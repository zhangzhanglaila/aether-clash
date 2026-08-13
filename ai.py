import math

from equipment_data import HERO_RECOMMENDED_ITEMS, ITEMS
from game_data import HEIGHT, WIDTH, Hero, Minion, clamp, dist, norm


class AiMixin:
    def update_enemy_hero(self, dt):
        hero = self.enemy_hero
        if getattr(self, "network_role", None) == "host" and self.network_connected:
            self.update_remote_hero(dt)
            return
        if not hero.alive:
            if self.now() >= hero.respawn_at:
                self.respawn(hero)
            return
        if self.enemy_recalling:
            if self.player.alive and dist(hero, self.player) < 230:
                self.cancel_enemy_recall()
                return
            self.enemy_recall_elapsed += dt
            if self.enemy_recall_elapsed >= self.recall_duration:
                self.complete_enemy_recall()
            return
        if self.is_stunned(hero):
            self.regen_hero(hero, dt)
            return

        self.maybe_enemy_buy_items(hero)
        self.regen_hero(hero, dt)
        hp_ratio = hero.hp / hero.max_hp
        player_pressure = self.player.alive and dist(hero, self.player) < 300
        if self.enemy_has_affordable_recommended_item(hero) and dist(hero, self.red_core) > 260 and not player_pressure:
            self.start_enemy_recall()
            return
        if hp_ratio < 0.18 and dist(hero, self.red_core) > 260 and (not self.player.alive or dist(hero, self.player) > 260):
            self.start_enemy_recall()
            return
        ai_state, target, tx, ty = self.enemy_ai_decision(hero, hp_ratio)
        if target:
            if dist(hero, target) <= hero.attack_range:
                self.hero_attack(hero, target)
            self.cast_enemy_skills(hero, target, ai_state, hp_ratio)

        dx, dy = tx - hero.x, ty - hero.y
        stop_distance = 180 if ai_state in {"fight", "jungle"} else 90
        if ai_state != "retreat" and math.hypot(dx, dy) < stop_distance:
            return
        nx, ny = norm(dx, dy)
        speed = self.effective_speed(hero)
        hero.x = clamp(hero.x + nx * speed * dt, 35, WIDTH - 35)
        hero.y = clamp(hero.y + ny * speed * dt, 35, HEIGHT - 35)


    def enemy_ai_decision(self, hero, hp_ratio):
        if hp_ratio < 0.28:
            return "retreat", None, self.red_core.x, self.red_core.y

        player_target = self.player if self.player.alive and not self.hero_hidden_from(self.player, hero) and dist(hero, self.player) < 360 else None
        if player_target and hp_ratio > 0.42:
            return "fight", player_target, player_target.x, player_target.y

        defense_target = self.defense_target(hero)
        if defense_target and hp_ratio > 0.34:
            return "defend", defense_target, defense_target.x, defense_target.y

        low_minion = self.low_health_enemy_minion(hero)
        if low_minion:
            return "lane", low_minion, low_minion.x, low_minion.y

        jungle_target = self.priority_jungle_target(hero)
        if jungle_target and hp_ratio > 0.55:
            return "jungle", jungle_target, jungle_target.x, jungle_target.y

        lane_target = self.nearest_enemy(hero, 310, include_cores=False)
        if lane_target:
            return "lane", lane_target, lane_target.x, lane_target.y
        return "lane", None, 560, 350


    def priority_jungle_target(self, hero):
        ancient = next(
            (
                monster
                for monster in self.neutral_monsters
                if monster.camp_key == "ancient_guard" and monster.alive
            ),
            None,
        )
        if ancient and hero.level >= 4 and dist(hero, ancient) <= 520:
            return ancient
        return self.nearest_neutral(hero, 260)


    def low_health_enemy_minion(self, hero):
        candidates = [
            minion for minion in self.minions
            if minion.team != hero.team and minion.alive and minion.hp <= hero.attack_damage * 1.25 and dist(hero, minion) <= 330
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda minion: (dist(hero, minion), minion.hp))
        return candidates[0]


    def defense_target(self, hero):
        red_structures = [tower for tower in self.towers if tower.team == "red" and tower.alive]
        red_structures.append(self.red_core)
        threats = []
        for structure in red_structures:
            if not structure.alive:
                continue
            nearby_enemies = [
                unit for unit in [self.player] + self.minions
                if unit.alive and unit.team == "blue" and dist(unit, structure) <= structure.attack_range + 70 and not self.hero_hidden_from(unit, hero)
            ]
            for unit in nearby_enemies:
                pressure = 0 if isinstance(unit, Minion) else -1
                damaged = structure.hp / structure.max_hp
                threats.append((damaged, pressure, dist(hero, structure), unit))
        if not threats:
            return None
        threats.sort(key=lambda item: (item[0], item[1], item[2]))
        return threats[0][3]


    def maybe_enemy_buy_items(self, hero):
        if hero.team != "red" or dist(hero, self.red_core) > 155:
            return
        for _ in range(3):
            candidate = self.next_affordable_enemy_item(hero)
            if not candidate:
                break
            candidate_item = ITEMS[candidate]
            if self.buy_item_for_hero(hero, candidate, self.red_core):
                if self.hero_visible_to_player(hero):
                    self.spawn_floating_text(hero.x, hero.y - 72, f"+{self.item_name(candidate)}", candidate_item["color"], ttl=0.85)
            else:
                break


    def enemy_has_affordable_recommended_item(self, hero):
        return self.next_affordable_enemy_item(hero) is not None


    def next_affordable_enemy_item(self, hero):
        for item_key in HERO_RECOMMENDED_ITEMS.get(hero.hero_key, []):
            item = ITEMS[item_key]
            if hero.equipment.get(item_key, 0) >= item["max_stacks"]:
                continue
            missing_item = self.missing_item_requirement(hero, item)
            candidate = missing_item or item_key
            candidate_item = ITEMS[candidate]
            if hero.equipment.get(candidate, 0) >= candidate_item["max_stacks"]:
                continue
            cost = candidate_item["cost"] + hero.equipment.get(candidate, 0) * 70
            if hero.gold >= cost:
                return candidate
        return None


    def cast_enemy_skills(self, hero, target, ai_state, hp_ratio):
        distance = dist(hero, target)
        if isinstance(target, Hero):
            target_ratio = target.hp / target.max_hp
            if self.skill_available(hero, "r") and distance <= 340 and (target_ratio <= 0.58 or hp_ratio >= 0.68):
                self.cast_enemy_skill_at(hero, "r", target.x, target.y)
                return
            if self.skill_available(hero, "e"):
                if hero.hero_key == "warden" and hp_ratio <= 0.74:
                    self.cast_enemy_skill_at(hero, "e", hero.x + 24, hero.y + 18)
                    return
                if hero.hero_key == "reaver" and 80 <= distance <= 250:
                    self.cast_enemy_skill_at(hero, "e", target.x, target.y)
                    return
                if hero.hero_key == "geomancer" and distance <= 260:
                    self.cast_enemy_skill_at(hero, "e", hero.x, hero.y)
                    return
                if hero.hero_key == "tempest" and distance <= 240:
                    self.cast_enemy_skill_at(hero, "e", hero.x + (hero.x - target.x), hero.y + (hero.y - target.y))
                    return
                if hero.hero_key in {"sentinel", "arcanist"} and hp_ratio <= 0.72:
                    self.cast_enemy_skill_at(hero, "e", target.x, target.y)
                    return
                if hero.hero_key in {"vanguard", "shade", "weaver"} and 105 <= distance <= 270:
                    self.cast_enemy_skill_at(hero, "e", target.x, target.y)
                    return
                if hero.hero_key == "ranger" and distance <= 170:
                    away_x = hero.x + (hero.x - target.x)
                    away_y = hero.y + (hero.y - target.y)
                    self.cast_enemy_skill_at(hero, "e", away_x, away_y)
                    return
                if hero.hero_key == "reaver" and hp_ratio <= 0.55:
                    self.cast_enemy_skill_at(hero, "e", target.x, target.y)
                    return
            if self.skill_available(hero, "q") and distance <= 390:
                if hero.hero_key == "tempest" and distance <= 420:
                    self.cast_enemy_skill_at(hero, "q", target.x, target.y)
                    return
                if hero.hero_key == "warden" and distance <= 360:
                    self.cast_enemy_skill_at(hero, "q", target.x, target.y)
                    return
                if hero.hero_key == "geomancer" and distance <= 360:
                    self.cast_enemy_skill_at(hero, "q", target.x, target.y)
                    return
                self.cast_enemy_skill_at(hero, "q", target.x, target.y)
            return
        if self.skill_available(hero, "q") and distance <= 310 and ai_state in {"jungle", "lane"}:
            if hero.hero_key == "geomancer" or hero.hero_key == "tempest" or hero.hero_key == "warden":
                self.cast_enemy_skill_at(hero, "q", target.x, target.y)
                return
            self.cast_enemy_skill_at(hero, "q", target.x, target.y)


    def cast_enemy_skill_at(self, hero, skill_key, x, y):
        old_mouse = self.mouse_x, self.mouse_y
        self.mouse_x, self.mouse_y = x, y
        try:
            if skill_key == "q":
                self.cast_q(hero)
            elif skill_key == "e":
                self.cast_e(hero)
            elif skill_key == "r":
                self.cast_r(hero)
        finally:
            self.mouse_x, self.mouse_y = old_mouse

