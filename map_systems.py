import math
import random

from game_data import BRUSH_ZONES, HEIGHT, Hero, Minion, WIDTH, clamp, dist, norm


class MapSystemsMixin:
    def spawn_wave(self):
        self.wave_index += 1
        for lane in self.paths:
            blue_path = self.paths[lane]
            red_path = list(reversed(blue_path))
            formation = [("melee", -22), ("melee", 0), ("ranged", 22)]
            if self.wave_index % 3 == 0:
                formation.append(("siege", 46))
            for kind, offset in formation:
                bx, by = blue_path[0]
                rx, ry = red_path[0]
                self.minions.append(self.make_minion("blue", lane, bx + random.uniform(-6, 6), by + offset, kind, self.lane_empowered("blue", lane)))
                self.minions.append(self.make_minion("red", lane, rx + random.uniform(-6, 6), ry - offset, kind, self.lane_empowered("red", lane)))


    def lane_empowered(self, team, lane):
        enemy_team = "red" if team == "blue" else "blue"
        return any(tower.team == enemy_team and tower.lane == lane and tower.tier == "base" and not tower.alive for tower in self.towers)


    def make_minion(self, team, lane, x, y, kind, empowered=False):
        stats = {
            "melee": {"hp": 142, "radius": 10, "speed": 68, "attack_damage": 15, "attack_range": 60, "attack_cd": 1.08, "gold": 8, "xp": 28},
            "ranged": {"hp": 98, "radius": 9, "speed": 66, "attack_damage": 14, "attack_range": 145, "attack_cd": 1.24, "gold": 10, "xp": 32},
            "siege": {"hp": 240, "radius": 13, "speed": 54, "attack_damage": 31, "attack_range": 190, "attack_cd": 1.55, "gold": 22, "xp": 54},
        }[kind]
        hp_mult = 1.38 if empowered else 1.0
        damage_mult = 1.28 if empowered else 1.0
        reward_mult = 1.18 if empowered else 1.0
        return Minion(
            x,
            y,
            team,
            stats["hp"] * hp_mult,
            stats["hp"] * hp_mult,
            stats["radius"] + (2 if empowered else 0),
            stats["speed"],
            stats["attack_damage"] * damage_mult,
            stats["attack_range"],
            stats["attack_cd"],
            lane=lane,
            kind=kind,
            empowered=empowered,
            gold_reward=int(stats["gold"] * reward_mult),
            xp_reward=int(stats["xp"] * reward_mult),
        )


    def update_player(self, dt):
        if not self.player.alive:
            if self.now() >= self.player.respawn_at:
                self.respawn(self.player)
            return
        if self.is_stunned(self.player):
            self.regen_hero(self.player, dt)
            return

        if self.recalling:
            if any(k in self.keys for k in {"w", "a", "s", "d", "up", "down", "left", "right"}):
                self.cancel_recall()
                return
            self.recall_elapsed += dt
            if self.recall_elapsed >= self.recall_duration:
                self.complete_recall()
            return

        dx = 0
        dy = 0
        if "w" in self.keys or "up" in self.keys:
            dy -= 1
        if "s" in self.keys or "down" in self.keys:
            dy += 1
        if "a" in self.keys or "left" in self.keys:
            dx -= 1
        if "d" in self.keys or "right" in self.keys:
            dx += 1
        nx, ny = norm(dx, dy)
        speed = self.effective_speed(self.player)
        self.player.x = clamp(self.player.x + nx * speed * dt, 35, WIDTH - 35)
        self.player.y = clamp(self.player.y + ny * speed * dt, 35, HEIGHT - 35)
        self.regen_hero(self.player, dt)


    def update_neutral_monsters(self):
        for monster in self.neutral_monsters:
            if not monster.alive:
                if monster.respawn_at and self.now() >= monster.respawn_at:
                    monster.alive = True
                    monster.hp = monster.max_hp
                    monster.respawn_at = 0
                    self.spawn_ring(monster.x, monster.y, monster.color, base_radius=52, ttl=0.28)
                continue
            if self.is_stunned(monster):
                continue

            hero_targets = [
                hero for hero in (self.player, self.enemy_hero)
                if hero.alive and dist(monster, hero) <= monster.attack_range
            ]
            if hero_targets:
                hero_targets.sort(key=lambda hero: dist(monster, hero))
                self.unit_attack(monster, hero_targets[0])


    def update_minions(self, dt):
        for minion in self.minions:
            if not minion.alive:
                continue
            if self.is_stunned(minion):
                continue
            target = self.nearest_enemy(minion, minion.attack_range, include_cores=True)
            if target:
                self.unit_attack(minion, target)
                continue

            path = self.paths[minion.lane]
            if minion.team == "red":
                path = list(reversed(path))
            if minion.waypoint >= len(path):
                continue
            tx, ty = path[minion.waypoint]
            dx, dy = tx - minion.x, ty - minion.y
            if math.hypot(dx, dy) < 12:
                minion.waypoint += 1
                continue
            nx, ny = norm(dx, dy)
            speed = self.effective_speed(minion)
            minion.x += nx * speed * dt
            minion.y += ny * speed * dt


    def update_towers(self):
        for tower in self.towers:
            if not tower.alive:
                continue
            target = self.nearest_enemy(tower, tower.attack_range, include_cores=False)
            if target:
                self.unit_attack(tower, target)


    def update_cores(self):
        for core in [self.blue_core, self.red_core]:
            if not core.alive:
                continue
            target = self.nearest_enemy(core, core.attack_range, include_cores=False)
            if target:
                self.unit_attack(core, target)


    def update_effects(self, dt):
        kept = []
        for e in self.effects:
            e.ttl -= dt
            progress = 1 - max(0, e.ttl / e.max_ttl)
            e.radius = e.max_radius * progress
            if e.ttl > 0:
                kept.append(e)
        self.effects = kept

        next_particles = []
        for p in self.particles:
            p.ttl -= dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= 0.94
            p.vy *= 0.94
            if p.ttl > 0:
                next_particles.append(p)
        self.particles = next_particles

        next_beams = []
        for beam in self.beams:
            beam.ttl -= dt
            if beam.ttl > 0:
                next_beams.append(beam)
        self.beams = next_beams

        next_texts = []
        for text in self.float_texts:
            text.ttl -= dt
            text.y += text.vy * dt
            if text.ttl > 0:
                next_texts.append(text)
        self.float_texts = next_texts

        next_banners = []
        for banner in self.banners:
            banner.ttl -= dt
            if banner.ttl > 0:
                next_banners.append(banner)
        self.banners = next_banners
        if self.locked_target and not getattr(self.locked_target, "alive", False):
            self.locked_target = None


    def cleanup_dead(self):
        self.minions = [m for m in self.minions if m.alive]

        for hero in [self.player, self.enemy_hero]:
            if not hero.alive and hero.respawn_at == 0:
                hero.respawn_at = self.now() + 5
                hero.deaths += 1
                if hero.last_attacker_team == "neutral":
                    hero.kill_streak = 0
                    defeat_text = self.text("defeated_by_neutral", victim=self.hero_name(hero.hero_key))
                else:
                    killer = self.enemy_hero if hero.team == "blue" else self.player
                    killer.kills += 1
                    killer.kill_streak += 1
                    shutdown_streak = hero.kill_streak
                    hero.kill_streak = 0
                    killer.gold += 80
                    self.spawn_reward_text(hero.x, hero.y, 80, 0)
                    if killer.team == "red":
                        self.gain_xp(killer, 120)
                        self.spawn_reward_text(hero.x, hero.y - 18, 0, 120)
                    defeat_text = self.text(
                        "defeated",
                        killer=self.hero_name(killer.hero_key),
                        victim=self.hero_name(hero.hero_key),
                    )
                self.show_message(defeat_text)
                self.spawn_banner(defeat_text, "#ffb0aa", ttl=1.6)
                if hero.last_attacker_team != "neutral":
                    if shutdown_streak >= 3:
                        shutdown_text = self.text("shutdown", name=self.hero_name(killer.hero_key), target=self.hero_name(hero.hero_key))
                        self.spawn_banner(shutdown_text, "#f7d765", ttl=1.45)
                    elif killer.kill_streak >= 3:
                        streak_text = self.text("killing_spree", name=self.hero_name(killer.hero_key), count=killer.kill_streak)
                        self.spawn_banner(streak_text, "#f7d765", ttl=1.45)


    def check_winner(self):
        if not self.blue_core.alive:
            self.match_over = True
            self.winner = "red"
        elif not self.red_core.alive:
            self.match_over = True
            self.winner = "blue"


    def respawn(self, hero):
        hero.alive = True
        hero.hp = hero.max_hp
        hero.respawn_at = 0
        hero.last_attacker_team = ""
        hero.shield = 0
        hero.stunned_until = 0
        hero.slowed_until = 0
        hero.slow_mult = 1.0
        if hero.team == "blue":
            hero.x, hero.y = 130, 580
        else:
            hero.x, hero.y = 965, 120


    def hero_in_brush(self, hero):
        return any(left <= hero.x <= right and top <= hero.y <= bottom for left, top, right, bottom in BRUSH_ZONES)


    def hero_hidden_from(self, hero, observer):
        if not isinstance(hero, Hero) or hero.team == observer.team or not self.hero_in_brush(hero):
            return False
        return dist(hero, observer) > 145


    def hero_visible_to_player(self, hero):
        if hero.team == "blue":
            return True
        return self.player.alive and not self.hero_hidden_from(hero, self.player)

