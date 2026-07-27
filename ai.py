import math

from game_data import HEIGHT, WIDTH, Hero, Minion, clamp, dist, norm


class AiMixin:
    def update_enemy_hero(self, dt):
        hero = self.enemy_hero
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

        self.regen_hero(hero, dt)
        hp_ratio = hero.hp / hero.max_hp
        if hp_ratio < 0.18 and dist(hero, self.red_core) > 260 and (not self.player.alive or dist(hero, self.player) > 260):
            self.start_enemy_recall()
            return
        ai_state, target, tx, ty = self.enemy_ai_decision(hero, hp_ratio)
        if target:
            if dist(hero, target) <= hero.attack_range:
                self.hero_attack(hero, target)
            if isinstance(target, Hero) and self.now() >= hero.cooldowns["q"]:
                self.cast_ai_bolt(hero, target)

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

        jungle_target = self.nearest_neutral(hero, 260)
        if jungle_target and hp_ratio > 0.55:
            return "jungle", jungle_target, jungle_target.x, jungle_target.y

        lane_target = self.nearest_enemy(hero, 310, include_cores=False)
        if lane_target:
            return "lane", lane_target, lane_target.x, lane_target.y
        return "lane", None, 560, 350


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

