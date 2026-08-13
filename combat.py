import math
import random

from game_data import (
    Banner,
    Beam,
    Core,
    DamageOverTime,
    Effect,
    FloatingText,
    HEIGHT,
    HEROES,
    Hero,
    Minion,
    NeutralMonster,
    Particle,
    Projectile,
    SKILL_MAX_LEVELS,
    Tower,
    WIDTH,
    clamp,
    dist,
    dist_xy,
    norm,
)


class CombatMixin:
    def regen_hero(self, hero, dt):
        if dist(hero, self.blue_core if hero.team == "blue" else self.red_core) < 120:
            hero.hp = min(hero.max_hp, hero.hp + 34 * dt)


    def update_projectiles(self, dt):
        kept = []
        for p in self.projectiles:
            p.ttl -= dt
            if p.ttl <= 0:
                continue

            if p.target and getattr(p.target, "alive", False):
                nx, ny = norm(p.target.x - p.x, p.target.y - p.y)
                p.x += nx * p.speed * dt
                p.y += ny * p.speed * dt
                if dist_xy(p.x, p.y, p.target.x, p.target.y) <= p.radius + p.target.radius:
                    self.apply_damage(p.target, p.damage, p.team)
                    self.apply_projectile_control(p, p.target)
                    self.spawn_hit_fx(p.x, p.y, p.color)
                    continue
            else:
                p.x += p.vx * p.speed * dt
                p.y += p.vy * p.speed * dt
                hit = False
                targets = self.enemies_of(p.team, include_cores=True)
                if p.team != "neutral":
                    targets = targets + [monster for monster in self.neutral_monsters if monster.alive]
                for target in targets:
                    if target.alive and dist_xy(p.x, p.y, target.x, target.y) <= p.radius + target.radius:
                        self.apply_damage(target, p.damage, p.team)
                        self.apply_projectile_control(p, target)
                        self.spawn_hit_fx(p.x, p.y, p.color)
                        hit = not p.pierce
                        if hit:
                            break
                if hit:
                    continue
            if -30 <= p.x <= WIDTH + 30 and -30 <= p.y <= HEIGHT + 30:
                kept.append(p)
        self.projectiles = kept


    def apply_projectile_control(self, projectile, target):
        if projectile.stun:
            self.apply_stun(target, projectile.stun)
        if projectile.slow:
            self.apply_slow(target, projectile.slow, projectile.slow_duration or 1.0)


    def add_damage_over_time(self, target, attacker_team, damage_per_second, duration, color="#b38cff"):
        if target.alive:
            self.damage_over_times.append(DamageOverTime(target, attacker_team, damage_per_second, duration, color=color))


    def update_damage_over_time(self, dt):
        kept = []
        for effect in self.damage_over_times:
            effect.ttl -= dt
            effect.tick_timer -= dt
            target = effect.target
            if effect.ttl <= 0 or not getattr(target, "alive", False):
                continue
            if effect.tick_timer <= 0:
                effect.tick_timer = effect.tick_interval
                self.apply_damage(target, effect.damage_per_second * effect.tick_interval, effect.attacker_team)
                self.spawn_particles(target.x, target.y, effect.color, count=4, speed=50, spread=0.5, radius=2.0, ttl=0.18)
            kept.append(effect)
        self.damage_over_times = kept


    def enemies_of(self, team, include_cores=True):
        enemies = []
        if self.player.team != team:
            enemies.append(self.player)
        if self.enemy_hero.team != team:
            enemies.append(self.enemy_hero)
        enemies.extend(m for m in self.minions if m.team != team)
        enemies.extend(t for t in self.towers if t.team != team)
        if include_cores:
            enemies.append(self.red_core if team == "blue" else self.blue_core)
        return enemies


    def nearest_enemy(self, unit, range_value, include_cores=True):
        candidates = [
            e for e in self.enemies_of(unit.team, include_cores)
            if e.alive and dist(unit, e) <= range_value and not self.hero_hidden_from(e, unit)
        ]
        if not candidates:
            return None
        priority = {Minion: 0, Hero: 1, Tower: 2, Core: 3}
        candidates.sort(key=lambda e: (priority.get(type(e), 9), dist(unit, e)))
        return candidates[0]


    def nearest_neutral(self, unit, range_value):
        candidates = [
            monster for monster in self.neutral_monsters
            if monster.alive and dist(unit, monster) <= range_value
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda monster: dist(unit, monster))
        return candidates[0]


    def effective_speed(self, unit):
        speed = unit.speed
        if self.now() < unit.slowed_until:
            speed *= unit.slow_mult
        return speed


    def is_stunned(self, unit):
        return self.now() < unit.stunned_until


    def apply_slow(self, target, multiplier=0.58, duration=1.2):
        if not target.alive:
            return
        if self.now() >= target.slowed_until:
            target.slow_mult = multiplier
        else:
            target.slow_mult = min(target.slow_mult, multiplier)
        target.slowed_until = max(target.slowed_until, self.now() + duration)
        self.spawn_ring(target.x, target.y, "#9ad7ff", base_radius=34, ttl=0.18)


    def apply_stun(self, target, duration=0.55):
        if not target.alive:
            return
        target.stunned_until = max(target.stunned_until, self.now() + duration)
        self.spawn_ring(target.x, target.y, "#f7d765", base_radius=42, ttl=0.24)


    def unit_attack(self, unit, target):
        if self.is_stunned(unit):
            return
        current = self.now()
        if current < unit.next_attack:
            return
        unit.next_attack = current + unit.attack_cd
        color = "#8fd3ff" if unit.team == "blue" else "#ff9a91" if unit.team == "red" else "#f7d765"
        damage = unit.attack_damage
        slow = 0
        slow_duration = 0
        radius = 7 if isinstance(unit, Core) else 6 if isinstance(unit, Tower) else 4
        if isinstance(unit, Hero) and unit.hero_key == "ranger":
            unit.passive_stacks += 1
            if unit.passive_stacks >= 3:
                unit.passive_stacks = 0
                damage *= 1.35
                slow = 0.68
                slow_duration = 0.75
                radius = 7
                self.spawn_ring(unit.x, unit.y, unit.accent, base_radius=38, ttl=0.22)
                self.spawn_floating_text(unit.x, unit.y - 62, self.hero_passive_name(unit.hero_key), unit.accent, ttl=0.65)
        if isinstance(unit, Hero) and unit.hero_key == "tempest" and unit.passive_stacks > 0:
            unit.passive_stacks -= 1
            unit.next_attack = current + unit.attack_cd * 0.52
            damage *= 1.22
            radius = 7
            self.spawn_ring(unit.x, unit.y, unit.accent, base_radius=34, ttl=0.2)
            self.spawn_floating_text(unit.x, unit.y - 62, self.hero_passive_name(unit.hero_key), unit.accent, ttl=0.62)
        self.spawn_particles(unit.x, unit.y, color, count=6, speed=70, spread=0.5, radius=2.1, ttl=0.18)
        self.projectiles.append(
            Projectile(
                unit.x,
                unit.y,
                unit.team,
                damage,
                330 if isinstance(unit, (Tower, Core)) else 250,
                target=target,
                radius=radius,
                ttl=2.2,
                color=color,
                slow=slow,
                slow_duration=slow_duration,
            )
        )


    def hero_attack(self, hero, forced_target=None):
        if not hero.alive:
            return
        locked_target = self.valid_locked_target(hero) if hero is self.player else None
        target = forced_target or locked_target or self.nearest_enemy(hero, hero.attack_range, include_cores=True) or self.nearest_neutral(hero, hero.attack_range)
        if not target:
            return
        self.unit_attack(hero, target)


    def target_display_name(self, target):
        if isinstance(target, Hero):
            return self.hero_name(target.hero_key)
        if isinstance(target, Minion):
            return "Minion" if self.language == "en" else "小兵"
        if isinstance(target, NeutralMonster):
            return self.jungle_name(target.camp_key)
        if isinstance(target, Tower):
            return target.name
        if isinstance(target, Core):
            return target.name
        return "Target"


    def valid_locked_target(self, hero):
        target = self.locked_target
        if not target or not getattr(target, "alive", False):
            self.locked_target = None
            return None
        if isinstance(target, Hero) and not self.hero_visible_to_player(target):
            self.locked_target = None
            return None
        if dist(hero, target) > max(hero.attack_range + 120, 360):
            return None
        return target


    def lock_target(self, target):
        self.locked_target = target
        self.show_message(self.text("target_locked", name=self.target_display_name(target)))
        self.spawn_ring(target.x, target.y, "#f7d765", base_radius=42, ttl=0.22)


    def lock_target_at(self, x, y):
        candidates = self.lockable_targets()
        clicked = [
            target for target in candidates
            if dist_xy(x, y, target.x, target.y) <= target.radius + 14
        ]
        if not clicked:
            return False
        clicked.sort(key=lambda target: dist_xy(x, y, target.x, target.y))
        self.lock_target(clicked[0])
        return True


    def cycle_locked_target(self):
        candidates = self.lockable_targets()
        if not candidates:
            self.locked_target = None
            self.show_message(self.text("target_cleared"))
            return
        candidates.sort(key=lambda target: dist(self.player, target))
        if self.locked_target not in candidates:
            self.lock_target(candidates[0])
            return
        index = candidates.index(self.locked_target)
        self.lock_target(candidates[(index + 1) % len(candidates)])


    def lockable_targets(self):
        candidates = []
        if self.enemy_hero.alive and self.hero_visible_to_player(self.enemy_hero):
            candidates.append(self.enemy_hero)
        candidates.extend(minion for minion in self.minions if minion.team == "red" and minion.alive)
        candidates.extend(monster for monster in self.neutral_monsters if monster.alive)
        candidates.extend(tower for tower in self.towers if tower.team == "red" and tower.alive)
        if self.red_core.alive:
            candidates.append(self.red_core)
        return [target for target in candidates if dist(self.player, target) <= 520]


    def skill_ready(self, hero, key):
        if not self.skill_unlocked(hero, key):
            return False
        current = self.now()
        if not hero.alive or current < hero.cooldowns[key]:
            return False
        cooldown = self.skill_cooldown(hero, key)
        hero.skill_cds[key] = cooldown
        hero.cooldowns[key] = current + cooldown
        return True


    def skill_available(self, hero, key):
        return hero.alive and self.skill_unlocked(hero, key) and self.now() >= hero.cooldowns[key]


    def skill_unlocked(self, hero, key):
        return hero.skill_levels.get(key, 0) > 0


    def max_skill_level_for_hero_level(self, hero, key):
        if key == "r":
            if hero.level >= 12:
                return 3
            if hero.level >= 8:
                return 2
            if hero.level >= 4:
                return 1
            return 0
        return min(SKILL_MAX_LEVELS[key], 1 + hero.level // 2)


    def next_skill_unlock_level(self, key, current_level):
        if key == "r":
            unlocks = [4, 8, 12]
            return unlocks[min(current_level, len(unlocks) - 1)]
        return max(2, current_level * 2)


    def can_upgrade_skill(self, hero, key):
        return (
            hero.alive
            and hero.skill_points > 0
            and hero.skill_levels.get(key, 0) < self.max_skill_level_for_hero_level(hero, key)
            and hero.skill_levels.get(key, 0) < SKILL_MAX_LEVELS[key]
        )


    def skill_cooldown(self, hero, key):
        base_cd = HEROES[hero.hero_key]["cooldowns"][key]
        level = max(1, hero.skill_levels.get(key, 0))
        return max(base_cd * 0.72, base_cd * (1 - 0.055 * (level - 1)))


    def skill_level_multiplier(self, hero, key):
        level = max(1, hero.skill_levels.get(key, 0))
        return 1 + 0.16 * (level - 1)


    def upgrade_skill(self, hero, key, silent=False):
        if hero.skill_points <= 0:
            return False
        current_level = hero.skill_levels.get(key, 0)
        allowed_level = self.max_skill_level_for_hero_level(hero, key)
        skill_name = self.hero_skill(hero.hero_key, key)
        if current_level >= SKILL_MAX_LEVELS[key]:
            if not silent and hero.team == "blue":
                self.show_message(self.text("skill_max", skill=skill_name))
            return False
        if current_level >= allowed_level:
            if not silent and hero.team == "blue":
                unlock_level = self.next_skill_unlock_level(key, current_level)
                self.show_message(self.text("skill_locked", skill=skill_name, level=unlock_level))
            return False
        hero.skill_points -= 1
        hero.skill_levels[key] = current_level + 1
        hero.skill_cds[key] = self.skill_cooldown(hero, key)
        if not silent and hero.team == "blue":
            text = self.text("skill_upgraded", skill=skill_name, level=hero.skill_levels[key])
            self.show_message(text)
            self.spawn_banner(text, hero.accent, ttl=1.15)
        return True


    def auto_upgrade_skills(self, hero):
        for key in ("r", "q", "e"):
            while self.can_upgrade_skill(hero, key):
                self.upgrade_skill(hero, key, silent=True)
                break


    def aim_vector(self, hero):
        vx, vy = norm(self.mouse_x - hero.x, self.mouse_y - hero.y)
        if vx == 0 and vy == 0:
            return 1, 0
        return vx, vy


    def damage_area(self, team, x, y, radius, amount, include_cores=False):
        targets = self.enemies_of(team, include_cores=include_cores)
        if team != "neutral":
            targets = targets + [monster for monster in self.neutral_monsters if monster.alive]
        for target in targets:
            if target.alive and dist_xy(x, y, target.x, target.y) <= radius + target.radius:
                self.apply_damage(target, amount, team)


    def control_area(self, team, x, y, radius, stun=0, slow=None, duration=1.0):
        targets = self.enemies_of(team, include_cores=False)
        if team != "neutral":
            targets = targets + [monster for monster in self.neutral_monsters if monster.alive]
        for target in targets:
            if target.alive and dist_xy(x, y, target.x, target.y) <= radius + target.radius:
                if stun:
                    self.apply_stun(target, stun)
                if slow:
                    self.apply_slow(target, slow, duration)


    def dot_area(self, team, x, y, radius, damage_per_second, duration, color="#b38cff"):
        targets = self.enemies_of(team, include_cores=False)
        if team != "neutral":
            targets = targets + [monster for monster in self.neutral_monsters if monster.alive]
        for target in targets:
            if target.alive and dist_xy(x, y, target.x, target.y) <= radius + target.radius:
                self.add_damage_over_time(target, team, damage_per_second, duration, color=color)


    def skill_damage(self, hero, base, multiplier=1.0, skill_key=None):
        base_attack = HEROES[hero.hero_key]["attack_damage"]
        attack_bonus = max(0, hero.attack_damage - base_attack)
        skill_power = getattr(hero, "skill_power", 0)
        skill_bonus = self.skill_level_multiplier(hero, skill_key) if skill_key else 1
        return (base * multiplier + (hero.level - 1) * 8 * multiplier + attack_bonus * 0.45 * multiplier + skill_power * 0.72 * multiplier) * skill_bonus


    def spawn_particles(self, x, y, color, count=10, speed=120, spread=1.0, radius=3, ttl=0.45):
        for _ in range(count):
            angle = random.random() * math.tau
            magnitude = speed * (0.35 + random.random() * 0.65) * spread
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * magnitude,
                    vy=math.sin(angle) * magnitude,
                    color=color,
                    ttl=ttl * (0.65 + random.random() * 0.7),
                    max_ttl=ttl,
                    radius=radius * (0.7 + random.random() * 0.8),
                )
            )


    def spawn_ring(self, x, y, color, base_radius=18, ttl=0.32):
        self.effects.append(Effect(x, y, 4, base_radius, color, ttl, ttl))


    def spawn_hit_fx(self, x, y, color, big=False):
        self.spawn_particles(x, y, color, count=18 if big else 9, speed=160 if big else 100, spread=1.2 if big else 0.8, radius=3.6 if big else 2.6, ttl=0.42 if big else 0.28)
        self.spawn_ring(x, y, color, base_radius=44 if big else 24, ttl=0.28 if big else 0.18)


    def spawn_beam(self, x1, y1, x2, y2, color, width=4, ttl=0.16):
        self.beams.append(Beam(x1, y1, x2, y2, color, ttl, ttl, width))


    def spawn_floating_text(self, x, y, text, color="#ffffff", ttl=0.8):
        self.float_texts.append(FloatingText(x, y, text, color, ttl, ttl))


    def grant_shield(self, hero, amount):
        before = hero.shield
        hero.shield = max(hero.shield, amount)
        self.add_match_stat(hero.team, "shielding", hero.shield - before)


    def spawn_cast_fx(self, hero, skill_key):
        if hero.hero_key == "arcanist":
            shield = 24 + hero.level * 4 + 10 * max(1, hero.skill_levels.get(skill_key, 1))
            self.grant_shield(hero, shield)
            self.spawn_floating_text(hero.x, hero.y - 62, self.hero_passive_name(hero.hero_key), hero.accent, ttl=0.65)
        if hero.hero_key == "tempest":
            hero.passive_stacks = min(2, hero.passive_stacks + 1)
        if skill_key == "q":
            self.spawn_particles(hero.x, hero.y, hero.accent, count=8, speed=80, spread=0.7, radius=2.4, ttl=0.22)
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=28, ttl=0.18)
        elif skill_key == "e":
            self.spawn_particles(hero.x, hero.y, hero.accent, count=14, speed=110, spread=1.0, radius=2.8, ttl=0.28)
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=36, ttl=0.22)
        else:
            self.spawn_particles(hero.x, hero.y, hero.accent, count=24, speed=170, spread=1.3, radius=3.2, ttl=0.38)
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=58, ttl=0.32)


    def spawn_damage_text(self, x, y, amount, color="#f5f1d7"):
        self.spawn_floating_text(x, y, f"-{int(amount)}", color, ttl=0.7)


    def spawn_banner(self, text, color="#d8cf9b", ttl=1.4):
        self.banners.append(Banner(text, color, ttl, ttl))


    def start_aiming_skill(self, skill_key):
        if self.state != "playing":
            return
        if not self.skill_unlocked(self.player, skill_key):
            unlock_level = 4 if skill_key == "r" else 1
            self.show_message(self.text("skill_locked", skill=self.hero_skill(self.player.hero_key, skill_key), level=unlock_level))
            return
        if not self.skill_available(self.player, skill_key):
            return
        self.aiming_skill = skill_key


    def cast_aiming_skill(self):
        skill_key = self.aiming_skill
        self.aiming_skill = None
        if skill_key == "q":
            self.cast_q(self.player)
        elif skill_key == "e":
            self.cast_e(self.player)
        elif skill_key == "r":
            self.cast_r(self.player)


    def cast_q(self, hero):
        if not self.skill_ready(hero, "q"):
            return
        vx, vy = self.aim_vector(hero)
        self.spawn_cast_fx(hero, "q")
        if hero.hero_key == "sentinel":
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=76, ttl=0.34)
            self.damage_area(hero.team, hero.x, hero.y, 72, self.skill_damage(hero, 68, skill_key="q"))
            self.control_area(hero.team, hero.x, hero.y, 72, slow=0.62, duration=1.0)
            self.projectiles.append(
                Projectile(hero.x, hero.y, hero.team, self.skill_damage(hero, 54, skill_key="q"), 310, vx=vx, vy=vy, radius=14, pierce=True, ttl=0.85, color=hero.accent, stun=0.25)
            )
            return

        if hero.hero_key == "shade":
            self.spawn_beam(hero.x, hero.y, hero.x + vx * 165, hero.y + vy * 165, hero.accent, width=6, ttl=0.13)
            self.projectiles.append(
                Projectile(hero.x, hero.y, hero.team, self.skill_damage(hero, 92, skill_key="q"), 560, vx=vx, vy=vy, radius=9, pierce=False, ttl=0.62, color=hero.accent)
            )
            return

        if hero.hero_key == "weaver":
            self.spawn_beam(hero.x, hero.y, hero.x + vx * 220, hero.y + vy * 220, hero.accent, width=3, ttl=0.18)
            self.spawn_beam(hero.x - vy * 9, hero.y + vx * 9, hero.x + vx * 205 - vy * 9, hero.y + vy * 205 + vx * 9, hero.accent, width=2, ttl=0.12)
            self.spawn_beam(hero.x + vy * 9, hero.y - vx * 9, hero.x + vx * 205 + vy * 9, hero.y + vy * 205 - vx * 9, hero.accent, width=2, ttl=0.12)
            self.projectiles.append(
                Projectile(
                    hero.x,
                    hero.y,
                    hero.team,
                    self.skill_damage(hero, 84, skill_key="q"),
                    610,
                    vx=vx,
                    vy=vy,
                    radius=8,
                    pierce=True,
                    ttl=0.72,
                    color=hero.accent,
                    slow=0.58,
                    slow_duration=0.9,
                )
            )
            return

        if hero.hero_key == "warden":
            angle = math.atan2(vy, vx)
            self.spawn_beam(hero.x, hero.y, hero.x + math.cos(angle) * 150, hero.y + math.sin(angle) * 150, hero.accent, width=5, ttl=0.16)
            self.projectiles.append(
                Projectile(
                    hero.x,
                    hero.y,
                    hero.team,
                    self.skill_damage(hero, 76, skill_key="q"),
                    470,
                    vx=vx,
                    vy=vy,
                    radius=9,
                    pierce=True,
                    ttl=0.8,
                    color=hero.accent,
                    slow=0.68,
                    slow_duration=0.85,
                )
            )
            return

        if hero.hero_key == "reaver":
            self.spawn_beam(hero.x, hero.y, hero.x + vx * 150, hero.y + vy * 150, hero.accent, width=6, ttl=0.16)
            self.projectiles.append(
                Projectile(
                    hero.x,
                    hero.y,
                    hero.team,
                    self.skill_damage(hero, 98, skill_key="q"),
                    420,
                    vx=vx,
                    vy=vy,
                    radius=10,
                    pierce=False,
                    ttl=0.76,
                    color=hero.accent,
                )
            )
            return

        if hero.hero_key == "geomancer":
            for offset in (-0.18, 0, 0.18):
                ax = math.cos(math.atan2(vy, vx) + offset)
                ay = math.sin(math.atan2(vy, vx) + offset)
                self.spawn_beam(hero.x, hero.y, hero.x + ax * 120, hero.y + ay * 120, hero.accent, width=3, ttl=0.16)
                self.projectiles.append(
                    Projectile(
                        hero.x,
                        hero.y,
                        hero.team,
                        self.skill_damage(hero, 42, skill_key="q"),
                        380,
                        vx=ax,
                        vy=ay,
                        radius=8,
                        pierce=True,
                        ttl=0.86,
                        color=hero.accent,
                    )
                )
            return

        if hero.hero_key == "tempest":
            angle = math.atan2(vy, vx)
            for offset in (-0.08, 0, 0.08):
                ax = math.cos(angle + offset)
                ay = math.sin(angle + offset)
                self.spawn_beam(hero.x, hero.y, hero.x + ax * 155, hero.y + ay * 155, hero.accent, width=2, ttl=0.12)
                self.projectiles.append(
                    Projectile(
                        hero.x,
                        hero.y,
                        hero.team,
                        self.skill_damage(hero, 54, skill_key="q"),
                        560,
                        vx=ax,
                        vy=ay,
                        radius=7,
                        pierce=True,
                        ttl=0.74,
                        color=hero.accent,
                        slow=0.7,
                        slow_duration=0.65,
                    )
                )
            return

        if hero.hero_key == "ranger":
            angle = math.atan2(vy, vx)
            for offset in (-0.18, 0, 0.18):
                ax = math.cos(angle + offset)
                ay = math.sin(angle + offset)
                self.spawn_beam(hero.x, hero.y, hero.x + ax * 120, hero.y + ay * 120, hero.accent, width=2, ttl=0.14)
                self.projectiles.append(
                    Projectile(
                        hero.x,
                        hero.y,
                        hero.team,
                        self.skill_damage(hero, 46, skill_key="q"),
                        520,
                        vx=ax,
                        vy=ay,
                        radius=7,
                        pierce=False,
                        ttl=0.9,
                        color=hero.accent,
                        slow=0.72,
                        slow_duration=0.75,
                    )
                )
            return

        if hero.hero_key == "arcanist":
            self.spawn_beam(hero.x, hero.y, hero.x + vx * 160, hero.y + vy * 160, hero.accent, width=5, ttl=0.18)
            self.projectiles.append(
                Projectile(
                    hero.x,
                    hero.y,
                    hero.team,
                    self.skill_damage(hero, 96, skill_key="q"),
                    360,
                    vx=vx,
                    vy=vy,
                    radius=15,
                    pierce=True,
                    ttl=1.05,
                    color=hero.accent,
                    slow=0.52,
                    slow_duration=1.2,
                )
            )
            return

        self.projectiles.append(
            Projectile(hero.x, hero.y, hero.team, self.skill_damage(hero, 82, skill_key="q"), 430, vx=vx, vy=vy, radius=11, pierce=True, ttl=0.95, color=hero.accent)
        )
        self.spawn_beam(hero.x, hero.y, hero.x + vx * 140, hero.y + vy * 140, hero.accent, width=4, ttl=0.14)


    def cast_e(self, hero):
        if not self.skill_ready(hero, "e"):
            return
        vx, vy = self.aim_vector(hero)
        self.spawn_cast_fx(hero, "e")
        if hero.hero_key == "sentinel":
            healed = min(hero.max_hp - hero.hp, 140 * self.skill_level_multiplier(hero, "e"))
            hero.hp += healed
            self.add_match_stat(hero.team, "healing", healed)
            self.grant_shield(hero, 130 * self.skill_level_multiplier(hero, "e"))
            hero.next_attack = 0
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=94, ttl=0.36)
            self.spawn_particles(hero.x, hero.y, hero.accent, count=18, speed=90, spread=0.9, radius=3.0, ttl=0.36)
            return

        if hero.hero_key == "arcanist":
            self.spawn_beam(hero.x, hero.y, hero.x, hero.y, hero.accent, width=8, ttl=0.2)
            healed = min(hero.max_hp - hero.hp, 95 * self.skill_level_multiplier(hero, "e"))
            hero.hp += healed
            self.add_match_stat(hero.team, "healing", healed)
            self.grant_shield(hero, 80 * self.skill_level_multiplier(hero, "e"))
            self.damage_area(hero.team, hero.x, hero.y, 82, self.skill_damage(hero, 54, skill_key="e"))
            self.control_area(hero.team, hero.x, hero.y, 82, slow=0.55, duration=1.2)
            self.spawn_hit_fx(hero.x, hero.y, hero.accent, big=True)
            return

        old_x, old_y = hero.x, hero.y
        if hero.hero_key == "shade":
            target = self.nearest_enemy(hero, 260, include_cores=False)
            if target:
                vx, vy = norm(target.x - hero.x, target.y - hero.y)
            distance = 205
            hero.x = clamp(hero.x + vx * distance, 35, WIDTH - 35)
            hero.y = clamp(hero.y + vy * distance, 35, HEIGHT - 35)
            self.spawn_beam(old_x, old_y, hero.x, hero.y, hero.accent, width=7, ttl=0.18)
            self.damage_area(hero.team, hero.x, hero.y, 54, self.skill_damage(hero, 72, skill_key="e"))
            self.control_area(hero.team, hero.x, hero.y, 54, slow=0.5, duration=0.9)
            self.spawn_hit_fx(hero.x, hero.y, hero.accent, big=True)
            return

        if hero.hero_key == "weaver":
            distance = 236
            hero.x = clamp(hero.x + vx * distance, 35, WIDTH - 35)
            hero.y = clamp(hero.y + vy * distance, 35, HEIGHT - 35)
            self.spawn_beam(old_x, old_y, hero.x, hero.y, hero.accent, width=5, ttl=0.22)
            self.spawn_beam(old_x - vy * 14, old_y + vx * 14, hero.x - vy * 14, hero.y + vx * 14, hero.accent, width=2, ttl=0.18)
            self.spawn_beam(old_x + vy * 14, old_y - vx * 14, hero.x + vy * 14, hero.y - vx * 14, hero.accent, width=2, ttl=0.18)
            self.damage_area(hero.team, hero.x, hero.y, 62, self.skill_damage(hero, 66, skill_key="e"))
            self.control_area(hero.team, hero.x, hero.y, 62, slow=0.52, duration=0.9)
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=64, ttl=0.28)
            self.spawn_hit_fx(hero.x, hero.y, hero.accent, big=True)
            hero.next_attack = 0
            return

        if hero.hero_key == "warden":
            distance = 142
            hero.x = clamp(hero.x + vx * distance, 35, WIDTH - 35)
            hero.y = clamp(hero.y + vy * distance, 35, HEIGHT - 35)
            heal_amount = min(hero.max_hp - hero.hp, 72 * self.skill_level_multiplier(hero, "e"))
            if hero.hp / hero.max_hp <= 0.45:
                heal_amount *= 1.35
            hero.hp += heal_amount
            self.add_match_stat(hero.team, "healing", heal_amount)
            shield_amount = 66 * self.skill_level_multiplier(hero, "e")
            if hero.hp / hero.max_hp <= 0.45:
                shield_amount *= 1.28
            self.grant_shield(hero, shield_amount)
            self.spawn_beam(old_x, old_y, hero.x, hero.y, hero.accent, width=5, ttl=0.2)
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=78, ttl=0.3)
            self.spawn_particles(hero.x, hero.y, hero.accent, count=18, speed=100, spread=1.0, radius=2.8, ttl=0.3)
            return

        if hero.hero_key == "reaver":
            distance = 176
            hero.x = clamp(hero.x + vx * distance, 35, WIDTH - 35)
            hero.y = clamp(hero.y + vy * distance, 35, HEIGHT - 35)
            self.spawn_beam(old_x, old_y, hero.x, hero.y, hero.accent, width=6, ttl=0.18)
            self.damage_area(hero.team, hero.x, hero.y, 58, self.skill_damage(hero, 84, skill_key="e"))
            self.control_area(hero.team, hero.x, hero.y, 58, slow=0.55, duration=0.95)
            self.spawn_hit_fx(hero.x, hero.y, hero.accent, big=True)
            return

        if hero.hero_key == "geomancer":
            self.spawn_beam(hero.x, hero.y, hero.x, hero.y, hero.accent, width=8, ttl=0.18)
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=90, ttl=0.34)
            self.spawn_particles(hero.x, hero.y, hero.accent, count=20, speed=120, spread=1.0, radius=2.9, ttl=0.34)
            self.damage_area(hero.team, hero.x, hero.y, 78, self.skill_damage(hero, 60, skill_key="e"))
            self.control_area(hero.team, hero.x, hero.y, 78, stun=0.3, slow=0.52, duration=1.0)
            self.grant_shield(hero, 70 * self.skill_level_multiplier(hero, "e"))
            return

        if hero.hero_key == "tempest":
            distance = 178
            hero.x = clamp(hero.x + vx * distance, 35, WIDTH - 35)
            hero.y = clamp(hero.y + vy * distance, 35, HEIGHT - 35)
            hero.next_attack = 0
            self.spawn_beam(old_x, old_y, hero.x, hero.y, hero.accent, width=5, ttl=0.16)
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=58, ttl=0.24)
            self.spawn_hit_fx(hero.x, hero.y, hero.accent)
            return

        distance = 168 if hero.hero_key == "ranger" else 120
        hero.x = clamp(hero.x + vx * distance, 35, WIDTH - 35)
        hero.y = clamp(hero.y + vy * distance, 35, HEIGHT - 35)
        self.spawn_beam(old_x, old_y, hero.x, hero.y, hero.accent, width=5 if hero.hero_key == "ranger" else 4, ttl=0.16)
        if hero.hero_key == "ranger":
            hero.next_attack = 0
            self.spawn_hit_fx(hero.x, hero.y, hero.accent)
        else:
            self.damage_area(hero.team, hero.x, hero.y, 52, self.skill_damage(hero, 42, skill_key="e"))
            self.spawn_hit_fx(hero.x, hero.y, hero.accent)


    def cast_r(self, hero):
        if not hero.alive:
            return
        if dist_xy(hero.x, hero.y, self.mouse_x, self.mouse_y) > 340:
            return
        if not self.skill_ready(hero, "r"):
            return
        self.spawn_cast_fx(hero, "r")

        if hero.hero_key == "sentinel":
            self.spawn_ring(self.mouse_x, self.mouse_y, hero.accent, base_radius=148, ttl=0.55)
            self.spawn_particles(self.mouse_x, self.mouse_y, hero.accent, count=30, speed=165, spread=1.35, radius=3.4, ttl=0.48)
            self.spawn_beam(hero.x, hero.y, self.mouse_x, self.mouse_y, hero.accent, width=8, ttl=0.2)
            self.damage_area(hero.team, self.mouse_x, self.mouse_y, 136, self.skill_damage(hero, 154, 1.35, skill_key="r"), include_cores=True)
            self.control_area(hero.team, self.mouse_x, self.mouse_y, 136, stun=0.65, slow=0.45, duration=1.4)
            return

        if hero.hero_key == "shade":
            target = self.nearest_enemy(hero, 360, include_cores=False)
            tx, ty = (target.x, target.y) if target else (self.mouse_x, self.mouse_y)
            if dist_xy(hero.x, hero.y, tx, ty) > 380:
                return
            self.spawn_beam(hero.x, hero.y, tx, ty, hero.accent, width=9, ttl=0.18)
            hero.x = clamp(tx - 18, 35, WIDTH - 35)
            hero.y = clamp(ty - 18, 35, HEIGHT - 35)
            self.spawn_ring(tx, ty, hero.accent, base_radius=88, ttl=0.32)
            self.spawn_particles(tx, ty, hero.accent, count=28, speed=220, spread=1.25, radius=3.2, ttl=0.38)
            execute_mult = 1.0
            if target and target.alive:
                missing_hp = 1 - target.hp / target.max_hp
                execute_mult += missing_hp * 0.85
            self.damage_area(hero.team, tx, ty, 78, self.skill_damage(hero, 188, 1.5 * execute_mult, skill_key="r"), include_cores=False)
            self.control_area(hero.team, tx, ty, 78, slow=0.45, duration=1.0)
            return

        if hero.hero_key == "weaver":
            tx, ty = self.mouse_x, self.mouse_y
            self.spawn_ring(tx, ty, hero.accent, base_radius=116, ttl=0.52)
            self.spawn_ring(tx, ty, hero.accent, base_radius=64, ttl=0.34)
            for angle in (0, math.pi / 3, math.pi * 2 / 3, math.pi, math.pi * 4 / 3, math.pi * 5 / 3):
                x1 = tx + math.cos(angle) * 18
                y1 = ty + math.sin(angle) * 18
                x2 = tx + math.cos(angle) * 112
                y2 = ty + math.sin(angle) * 112
                self.spawn_beam(x1, y1, x2, y2, hero.accent, width=3, ttl=0.28)
            self.spawn_beam(hero.x, hero.y, tx, ty, hero.accent, width=7, ttl=0.22)
            self.spawn_particles(tx, ty, hero.accent, count=34, speed=210, spread=1.45, radius=2.9, ttl=0.45)
            self.damage_area(hero.team, tx, ty, 108, self.skill_damage(hero, 164, 1.42, skill_key="r"), include_cores=True)
            self.control_area(hero.team, tx, ty, 108, stun=0.55, slow=0.45, duration=1.25)
            self.dot_area(hero.team, tx, ty, 108, self.skill_damage(hero, 20, 0.72, skill_key="r"), 1.8, color=hero.accent)
            return

        if hero.hero_key == "ranger":
            vx, vy = self.aim_vector(hero)
            angle = math.atan2(vy, vx)
            for offset in (-0.52, -0.39, -0.26, -0.13, 0, 0.13, 0.26, 0.39, 0.52):
                bx = math.cos(angle + offset)
                by = math.sin(angle + offset)
                self.spawn_beam(hero.x, hero.y, hero.x + bx * 110, hero.y + by * 110, hero.accent, width=2, ttl=0.12)
                self.projectiles.append(
                    Projectile(
                        hero.x,
                        hero.y,
                        hero.team,
                        self.skill_damage(hero, 42, 1.3, skill_key="r"),
                        500,
                        vx=math.cos(angle + offset),
                        vy=math.sin(angle + offset),
                        radius=8,
                        pierce=True,
                        ttl=1.05,
                        color=hero.accent,
                        slow=0.72,
                        slow_duration=0.75,
                    )
                )
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=84, ttl=0.28)
            return

        if hero.hero_key == "arcanist":
            self.spawn_beam(hero.x, hero.y, self.mouse_x, self.mouse_y, hero.accent, width=7, ttl=0.22)
            self.spawn_ring(self.mouse_x, self.mouse_y, hero.accent, base_radius=130, ttl=0.55)
            self.spawn_particles(self.mouse_x, self.mouse_y, hero.accent, count=28, speed=210, spread=1.4, radius=3.2, ttl=0.42)
            self.damage_area(hero.team, self.mouse_x, self.mouse_y, 120, self.skill_damage(hero, 176, 1.45, skill_key="r"), include_cores=True)
            self.control_area(hero.team, self.mouse_x, self.mouse_y, 120, stun=0.5, slow=0.5, duration=1.4)
            self.dot_area(hero.team, self.mouse_x, self.mouse_y, 120, self.skill_damage(hero, 28, 0.8, skill_key="r"), 2.1, color=hero.accent)
            return

        if hero.hero_key == "warden":
            self.spawn_ring(self.mouse_x, self.mouse_y, hero.accent, base_radius=138, ttl=0.5)
            self.spawn_particles(self.mouse_x, self.mouse_y, hero.accent, count=26, speed=175, spread=1.2, radius=3.0, ttl=0.38)
            self.damage_area(hero.team, self.mouse_x, self.mouse_y, 118, self.skill_damage(hero, 128, 1.3, skill_key="r"), include_cores=True)
            allies = [unit for unit in [self.player, self.enemy_hero] if unit.alive and unit.team == hero.team]
            for ally in allies:
                if dist_xy(self.mouse_x, self.mouse_y, ally.x, ally.y) <= 150:
                    heal_amount = min(ally.max_hp - ally.hp, 82 * self.skill_level_multiplier(hero, "r"))
                    ally.hp += heal_amount
                    self.add_match_stat(hero.team, "healing", heal_amount)
                    self.grant_shield(ally, 42 * self.skill_level_multiplier(hero, "r"))
            return

        if hero.hero_key == "reaver":
            self.spawn_beam(hero.x, hero.y, self.mouse_x, self.mouse_y, hero.accent, width=8, ttl=0.2)
            self.spawn_ring(self.mouse_x, self.mouse_y, hero.accent, base_radius=104, ttl=0.44)
            self.spawn_particles(self.mouse_x, self.mouse_y, hero.accent, count=28, speed=200, spread=1.3, radius=3.1, ttl=0.38)
            dealt = self.skill_damage(hero, 160, 1.35, skill_key="r")
            self.damage_area(hero.team, self.mouse_x, self.mouse_y, 98, dealt, include_cores=False)
            self.control_area(hero.team, self.mouse_x, self.mouse_y, 98, slow=0.45, duration=1.1)
            heal_amount = min(hero.max_hp - hero.hp, dealt * 0.22)
            hero.hp += heal_amount
            self.add_match_stat(hero.team, "healing", heal_amount)
            return

        if hero.hero_key == "geomancer":
            self.spawn_ring(self.mouse_x, self.mouse_y, hero.accent, base_radius=150, ttl=0.58)
            self.spawn_particles(self.mouse_x, self.mouse_y, hero.accent, count=32, speed=165, spread=1.25, radius=3.2, ttl=0.46)
            self.damage_area(hero.team, self.mouse_x, self.mouse_y, 132, self.skill_damage(hero, 152, 1.42, skill_key="r"), include_cores=True)
            self.control_area(hero.team, self.mouse_x, self.mouse_y, 132, stun=0.6, slow=0.6, duration=1.35)
            self.dot_area(hero.team, self.mouse_x, self.mouse_y, 132, self.skill_damage(hero, 24, 0.78, skill_key="r"), 1.9, color=hero.accent)
            self.grant_shield(hero, 96 * self.skill_level_multiplier(hero, "r"))
            return

        if hero.hero_key == "tempest":
            vx, vy = self.aim_vector(hero)
            angle = math.atan2(vy, vx)
            for offset in (-0.42, -0.24, -0.08, 0.08, 0.24, 0.42):
                ax = math.cos(angle + offset)
                ay = math.sin(angle + offset)
                self.spawn_beam(hero.x, hero.y, hero.x + ax * 120, hero.y + ay * 120, hero.accent, width=2, ttl=0.12)
                self.projectiles.append(
                    Projectile(
                        hero.x,
                        hero.y,
                        hero.team,
                        self.skill_damage(hero, 40, 1.08, skill_key="r"),
                        560,
                        vx=ax,
                        vy=ay,
                        radius=7,
                        pierce=True,
                        ttl=1.0,
                        color=hero.accent,
                        slow=0.76,
                        slow_duration=0.65,
                    )
                )
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=92, ttl=0.3)
            return

        self.spawn_beam(hero.x, hero.y, self.mouse_x, self.mouse_y, hero.accent, width=6, ttl=0.18)
        self.spawn_ring(self.mouse_x, self.mouse_y, hero.accent, base_radius=112, ttl=0.48)
        self.spawn_particles(self.mouse_x, self.mouse_y, hero.accent, count=20, speed=190, spread=1.25, radius=3.0, ttl=0.36)
        self.damage_area(hero.team, self.mouse_x, self.mouse_y, 96, self.skill_damage(hero, 148, 1.45, skill_key="r"), include_cores=True)
        self.control_area(hero.team, self.mouse_x, self.mouse_y, 96, stun=0.45, slow=0.55, duration=1.1)
        self.dot_area(hero.team, self.mouse_x, self.mouse_y, 96, self.skill_damage(hero, 18, 0.7, skill_key="r"), 1.6, color=hero.accent)


    def cast_ai_bolt(self, hero, target):
        if not self.skill_ready(hero, "q"):
            return
        vx, vy = norm(target.x - hero.x, target.y - hero.y)
        self.projectiles.append(
            Projectile(
                hero.x,
                hero.y,
                hero.team,
                self.skill_damage(hero, 64, skill_key="q"),
                385,
                vx=vx,
                vy=vy,
                radius=10,
                pierce=True,
                ttl=0.9,
                color="#ff6c7a",
                slow=0.7,
                slow_duration=0.7,
            )
        )


    def reward_player(self, target):
        rule = self.mode_rule()
        gold = 0
        xp = 0
        if isinstance(target, Minion):
            gold = int(target.gold_reward * rule["gold_mult"])
            xp = int(target.xp_reward * rule["xp_mult"])
        elif isinstance(target, Tower):
            gold = int(120 * rule["gold_mult"])
            xp = int(90 * rule["xp_mult"])
        elif isinstance(target, Hero):
            gold = int(120 * rule["gold_mult"])
            xp = int(120 * rule["xp_mult"])
        if gold or xp:
            self.player.gold += gold
            self.record_reward("blue", gold, xp)
            self.gain_xp(self.player, xp)
            self.spawn_reward_text(target.x, target.y, gold, xp)


    def spawn_reward_text(self, x, y, gold, xp):
        parts = []
        if gold:
            parts.append(f"+{gold}G")
        if xp:
            parts.append(f"+{xp}XP")
        if parts:
            self.spawn_floating_text(x, y - 36, " ".join(parts), "#f7d765", ttl=0.95)


    def gain_xp(self, hero, amount):
        hero.xp += amount
        while hero.xp >= hero.next_xp:
            hero.xp -= hero.next_xp
            self.level_up(hero)


    def level_up(self, hero, silent=False):
        hero.level += 1
        hero.skill_points += 1
        hero.next_xp = int(hero.next_xp * 1.32)
        hero.max_hp += 48
        hero.hp = min(hero.max_hp, hero.hp + 48)
        hero.attack_damage += 4
        hero.attack_range += 3
        if hero.team == "red":
            self.auto_upgrade_skills(hero)
        self.spawn_particles(hero.x, hero.y, hero.accent, count=22, speed=170, spread=1.1, radius=3.0, ttl=0.42)
        self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=62, ttl=0.32)
        if not silent and hero.team == "blue":
            text = self.text("level_up", level=hero.level)
            self.show_message(text)
            self.spawn_floating_text(hero.x, hero.y - 42, text, "#f7d765", ttl=0.85)


    def apply_damage(self, target, amount, attacker_team):
        if isinstance(target, (Tower, Core)):
            amount *= 1.35 if attacker_team == "blue" else 1.15
        amount = self.apply_item_damage_modifiers(target, amount, attacker_team)
        amount = self.apply_hero_passive_modifiers(target, amount, attacker_team)
        was_alive = target.alive
        if isinstance(target, Hero):
            target.last_attacker_team = attacker_team
        if target is self.player and self.recalling:
            self.cancel_recall()
        if target is self.enemy_hero and self.enemy_recalling and attacker_team == "blue":
            self.cancel_enemy_recall()
        if getattr(target, "shield", 0) > 0:
            absorbed = min(target.shield, amount)
            target.shield -= absorbed
            amount -= absorbed
            if absorbed > 0:
                self.spawn_floating_text(target.x, target.y - 34, f"-{int(absorbed)} SH", "#8fd3ff", ttl=0.65)
            if amount <= 0:
                return
        damage_color = "#ff9a91" if attacker_team == "blue" else "#8fd3ff" if attacker_team == "red" else "#f7d765"
        self.spawn_damage_text(target.x, target.y - 18, amount, damage_color)
        self.record_damage_stats(target, amount, attacker_team)
        if self.try_last_stand(target, amount):
            return
        target.take_damage(amount)
        if was_alive and not target.alive:
            if isinstance(target, NeutralMonster) and attacker_team in {"blue", "red"}:
                self.reward_neutral(target, attacker_team)
                target.respawn_at = self.now() + target.respawn_delay
            if attacker_team == "blue" and target.team == "red":
                self.reward_player(target)
            if isinstance(target, Minion) and attacker_team in {"blue", "red"}:
                self.add_match_stat(attacker_team, "minions_last_hit", 1)
            if isinstance(target, Tower) and attacker_team in {"blue", "red"}:
                self.match_stats[attacker_team]["towers_destroyed"] += 1
                text = self.text("destroyed", name=target.name)
                if target.tier == "base" and attacker_team in {"blue", "red"}:
                    empowered_text = self.text("empowered_minions", team=self.text(attacker_team), lane=self.lane_name(target.lane))
                    text = f"{text} / {empowered_text}"
                self.show_message(text)
                self.spawn_banner(text, "#f7d765", ttl=1.5)
                self.spawn_particles(target.x, target.y, "#f7d765", count=22, speed=150, spread=1.3, radius=3.4, ttl=0.42)
                self.spawn_ring(target.x, target.y, "#f7d765", base_radius=76, ttl=0.34)
            elif isinstance(target, Core):
                text = self.text("destroyed", name=target.name)
                self.show_message(text)
                self.spawn_banner(text, "#f7d765", ttl=1.7)
                self.spawn_particles(target.x, target.y, "#f7d765", count=32, speed=190, spread=1.6, radius=3.8, ttl=0.56)
                self.spawn_ring(target.x, target.y, "#f7d765", base_radius=120, ttl=0.48)
            elif isinstance(target, Hero):
                self.spawn_particles(target.x, target.y, target.accent, count=26, speed=180, spread=1.4, radius=3.2, ttl=0.38)
                self.spawn_ring(target.x, target.y, target.accent, base_radius=68, ttl=0.26)


    def reward_neutral(self, monster, attacker_team):
        hero = self.player if attacker_team == "blue" else self.enemy_hero
        rule = self.mode_rule()
        gold = int(monster.gold_reward * rule["gold_mult"])
        xp = int(monster.xp_reward * rule["xp_mult"])
        hero.gold += gold
        self.record_reward(attacker_team, gold, xp)
        self.match_stats[attacker_team]["monsters_slain"] += 1
        self.gain_xp(hero, xp)
        self.spawn_particles(monster.x, monster.y, monster.color, count=24, speed=150, spread=1.2, radius=3.1, ttl=0.4)
        self.spawn_ring(monster.x, monster.y, monster.color, base_radius=64, ttl=0.34)
        if attacker_team == "blue":
            text = self.text("neutral_slain", name=self.jungle_name(monster.camp_key), gold=gold, xp=xp)
            self.show_message(text)
            self.spawn_banner(text, monster.color, ttl=1.25)


    def record_damage_stats(self, target, amount, attacker_team):
        if target.team == attacker_team:
            return
        effective = min(amount, getattr(target, "hp", amount))
        if attacker_team in {"blue", "red"}:
            self.add_match_stat(attacker_team, "damage_dealt", effective)
            if isinstance(target, Hero):
                self.add_match_stat(attacker_team, "hero_damage", effective)
            elif isinstance(target, (Tower, Core)):
                self.add_match_stat(attacker_team, "structure_damage", effective)
        if target.team in {"blue", "red"}:
            self.add_match_stat(target.team, "damage_taken", effective)


    def record_reward(self, team, gold, xp):
        if team not in {"blue", "red"}:
            return
        self.match_stats[team]["gold_earned"] += max(0, gold)
        self.match_stats[team]["xp_earned"] += max(0, xp)


    def hero_for_team(self, team):
        if team == "blue":
            return self.player
        if team == "red":
            return self.enemy_hero
        return None


    def apply_item_damage_modifiers(self, target, amount, attacker_team):
        attacker = self.hero_for_team(attacker_team)
        if isinstance(target, NeutralMonster) and attacker:
            hunter_level = attacker.equipment.get("hunter_charm", 0)
            if hunter_level:
                amount *= 1 + 0.18 * hunter_level
        if isinstance(target, Hero):
            bulwark_level = target.equipment.get("bulwark", 0)
            if bulwark_level:
                amount *= 0.9
        return amount


    def apply_hero_passive_modifiers(self, target, amount, attacker_team):
        attacker = self.hero_for_team(attacker_team)
        if attacker and attacker.hero_key == "shade" and isinstance(target, Hero) and target.team != attacker_team and target.hp / target.max_hp <= 0.45:
            amount *= 1.14
        if attacker and attacker.hero_key == "weaver" and target.team != attacker_team and (self.is_stunned(target) or self.now() < target.slowed_until):
            amount *= 1.12
        if isinstance(target, Hero):
            if target.hero_key == "sentinel":
                amount *= 0.92
            if target.hero_key == "vanguard" and target.hp / target.max_hp <= 0.4:
                amount *= 0.9
        return amount


    def try_last_stand(self, target, amount):
        if not isinstance(target, Hero):
            return False
        if target.hp - amount > 0:
            return False
        if target.equipment.get("revive_plate", 0) <= 0 or target.item_passives_used.get("revive_plate"):
            return False
        target.item_passives_used["revive_plate"] = True
        target.hp = max(1, target.max_hp * 0.28)
        self.spawn_particles(target.x, target.y, "#f5f1d7", count=30, speed=180, spread=1.25, radius=3.2, ttl=0.46)
        self.spawn_ring(target.x, target.y, "#f5f1d7", base_radius=82, ttl=0.38)
        text = self.text("last_stand", name=self.hero_name(target.hero_key))
        self.show_message(text)
        self.spawn_banner(text, "#f5f1d7", ttl=1.35)
        return True


