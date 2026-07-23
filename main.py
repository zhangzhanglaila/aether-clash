import math
import random
import time
import tkinter as tk
from game_data import (
    Core,
    Beam,
    Effect,
    FPS_MS,
    HEROES,
    HEIGHT,
    Hero,
    ITEMS,
    L10N,
    MODE_RULES,
    Minion,
    FloatingText,
    Particle,
    Banner,
    Projectile,
    Tower,
    WIDTH,
    clamp,
    dist,
    dist_xy,
    norm,
    team_color,
)


class MobaGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Python MOBA Prototype")
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(
            self.root,
            width=WIDTH,
            height=HEIGHT,
            bg="#18261d",
            highlightthickness=0,
        )
        self.canvas.pack()
        self.keys = set()
        self.mouse_x = WIDTH // 2
        self.mouse_y = HEIGHT // 2
        self.last_time = time.perf_counter()
        self.spawn_timer = 0
        self.enemy_xp_timer = 0
        self.match_over = False
        self.winner = None
        self.message_until = 0
        self.message = ""

        self.paths = {
            "top": [(92, 608), (96, 150), (910, 146), (1002, 112)],
            "mid": [(92, 608), (550, 350), (1002, 112)],
            "bot": [(92, 608), (250, 565), (920, 565), (1002, 112)],
        }

        self.language = "zh"
        self.state = "language"
        self.language_buttons = []
        self.lobby_buttons = []
        self.mode_cards = []
        self.hero_cards = []
        self.loading_started_at = 0
        self.selected_mode_key = None
        self.selected_hero_key = None
        self.player = None
        self.enemy_hero = None
        self.blue_core = None
        self.red_core = None
        self.towers = []
        self.minions = []
        self.projectiles = []
        self.effects = []
        self.particles = []
        self.beams = []
        self.float_texts = []
        self.banners = []

        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.root.bind("<Motion>", self.on_mouse_move)
        self.root.bind("<Button-1>", self.on_left_click)
        self.root.bind("<Button-3>", self.on_right_click)
        self.root.focus_force()

    def text(self, key, **kwargs):
        value = L10N[self.language][key]
        if kwargs:
            return value.format(**kwargs)
        return value

    def hero_name(self, hero_key):
        return L10N[self.language]["hero_names"][hero_key]

    def hero_role(self, hero_key):
        return L10N[self.language]["hero_roles"][hero_key]

    def hero_skill(self, hero_key, skill_key):
        return L10N[self.language]["skills"][hero_key][skill_key]

    def item_name(self, item_key):
        return L10N[self.language]["items"][item_key]

    def mode_rule(self):
        return MODE_RULES.get(self.selected_mode_key or "rank", MODE_RULES["rank"])

    def make_hero(self, hero_key, team, x, y):
        config = HEROES[hero_key]
        return Hero(
            x=x,
            y=y,
            team=team,
            hp=config["hp"],
            max_hp=config["hp"],
            radius=18,
            speed=config["speed"],
            attack_damage=config["attack_damage"],
            attack_range=config["attack_range"],
            attack_cd=config["attack_cd"],
            name=config["name"],
            hero_key=hero_key,
            role=config["role"],
            accent=config["accent"],
            skill_cds=dict(config["cooldowns"]),
            skill_names=dict(config["skills"]),
        )

    def reset_match(self, hero_key):
        self.selected_hero_key = hero_key
        rule = self.mode_rule()
        self.match_over = False
        self.winner = None
        self.spawn_timer = 0
        self.match_time = 0
        self.message_until = 0
        self.message = ""
        self.player = self.make_hero(hero_key, "blue", 130, 580)
        self.enemy_hero = self.make_hero("vanguard", "red", 965, 120)
        self.enemy_hero.name = "Red Vanguard"
        self.apply_starting_level(self.player, rule["start_level"])
        self.player.gold = rule["start_gold"]
        self.scale_hero_stats(self.enemy_hero, rule["enemy_stat_mult"])
        self.blue_core = Core(
            74,
            626,
            "blue",
            1000 * rule["core_hp_mult"],
            1000 * rule["core_hp_mult"],
            35,
            attack_damage=70,
            attack_range=210,
            attack_cd=0.85,
            name="Blue Core",
        )
        self.red_core = Core(
            1008,
            112,
            "red",
            1000 * rule["core_hp_mult"],
            1000 * rule["core_hp_mult"],
            35,
            attack_damage=70,
            attack_range=210,
            attack_cd=0.85,
            name="Red Core",
        )
        self.towers = self.make_towers()
        self.scale_structures(rule)
        self.minions = []
        self.projectiles = []
        self.effects = []
        self.particles = []
        self.beams = []
        self.float_texts = []
        self.banners = []
        self.shop_cards = []

    def apply_starting_level(self, hero, level):
        for _ in range(max(0, level - 1)):
            self.level_up(hero, silent=True)

    def scale_hero_stats(self, hero, multiplier):
        hero.max_hp *= multiplier
        hero.hp = hero.max_hp
        hero.attack_damage *= multiplier

    def scale_structures(self, rule):
        for tower in self.towers:
            tower.max_hp *= rule["tower_hp_mult"]
            tower.hp = tower.max_hp

    def make_towers(self):
        data = [
            ("blue", "top", 120, 330),
            ("blue", "top", 310, 148),
            ("red", "top", 810, 146),
            ("red", "top", 970, 255),
            ("blue", "mid", 280, 510),
            ("red", "mid", 820, 190),
            ("blue", "bot", 290, 565),
            ("blue", "bot", 540, 565),
            ("red", "bot", 885, 500),
            ("red", "bot", 980, 335),
        ]
        return [
            Tower(
                x=x,
                y=y,
                team=team,
                hp=360,
                max_hp=360,
                radius=24,
                attack_damage=52,
                attack_range=180,
                attack_cd=0.85,
                lane=lane,
                name=f"{team.title()} {lane.title()} Tower",
            )
            for team, lane, x, y in data
        ]

    def start(self):
        self.loop()
        self.root.mainloop()

    def now(self):
        return time.perf_counter()

    def on_key_press(self, event):
        key = event.keysym.lower()
        if self.state == "language":
            if key in {"1", "c"}:
                self.choose_language("zh")
            elif key in {"2", "e"}:
                self.choose_language("en")
            elif key == "escape":
                self.root.destroy()
            return

        if self.state == "lobby":
            if key in {"1", "2", "3"}:
                self.choose_mode(list(self.mode_configs().keys())[int(key) - 1])
            elif key in {"return", "space"} and self.selected_mode_key:
                self.state = "select"
            elif key == "escape":
                self.root.destroy()
            return

        if self.state == "loading":
            return

        if self.state == "select":
            if key in {"1", "2", "3"}:
                hero_key = list(HEROES.keys())[int(key) - 1]
                self.choose_hero(hero_key)
            elif key == "escape":
                self.root.destroy()
            return

        self.keys.add(key)
        if key == "q":
            self.cast_q(self.player)
        elif key == "e":
            self.cast_e(self.player)
        elif key == "r":
            self.cast_r(self.player)
        elif key in {"1", "2", "3"}:
            item_key = list(ITEMS.keys())[int(key) - 1]
            self.buy_item(item_key)
        elif key == "space":
            self.hero_attack(self.player)
        elif key == "escape":
            self.root.destroy()

    def on_key_release(self, event):
        self.keys.discard(event.keysym.lower())

    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def on_left_click(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.state == "language":
            self.select_language_at(self.mouse_x, self.mouse_y)
            return
        if self.state == "lobby":
            self.select_lobby_at(self.mouse_x, self.mouse_y)
            return
        if self.state == "loading":
            return
        if self.state == "select":
            self.select_card_at(self.mouse_x, self.mouse_y)
            return
        if self.select_shop_at(self.mouse_x, self.mouse_y):
            return
        self.hero_attack(self.player)

    def on_right_click(self, _event):
        if self.state != "playing":
            return
        self.cast_e(self.player)

    def choose_language(self, language):
        self.language = language
        self.selected_mode_key = None
        self.selected_hero_key = None
        self.state = "lobby"

    def mode_configs(self):
        return {
            "rank": (self.text("mode_rank"), "#78a3ff", L10N[self.language]["mode_desc"]["rank"]),
            "train": (self.text("mode_train"), "#76f4d1", L10N[self.language]["mode_desc"]["train"]),
            "quick": (self.text("mode_quick"), "#b38cff", L10N[self.language]["mode_desc"]["quick"]),
        }

    def choose_mode(self, mode_key):
        self.selected_mode_key = mode_key

    def choose_hero(self, hero_key):
        self.reset_match(hero_key)
        self.state = "loading"
        self.loading_started_at = self.now()
        self.last_time = time.perf_counter()
        self.show_message(self.text("deployed", name=self.hero_name(hero_key)))

    def select_language_at(self, x, y):
        for language, left, top, right, bottom in self.language_buttons:
            if left <= x <= right and top <= y <= bottom:
                self.choose_language(language)
                return

    def select_lobby_at(self, x, y):
        for mode_key, left, top, right, bottom in self.mode_cards:
            if left <= x <= right and top <= y <= bottom:
                self.choose_mode(mode_key)
                return
        for action, left, top, right, bottom in self.lobby_buttons:
            if left <= x <= right and top <= y <= bottom:
                if action == "start" and self.selected_mode_key:
                    self.state = "select"
                return

    def select_card_at(self, x, y):
        for hero_key, left, top, right, bottom in self.hero_cards:
            if left <= x <= right and top <= y <= bottom:
                self.choose_hero(hero_key)
                return

    def near_shop(self):
        return self.player.alive and dist(self.player, self.blue_core) <= 155

    def buy_item(self, item_key):
        if self.state != "playing":
            return False
        if not self.near_shop():
            self.show_message(self.text("need_base"))
            return False
        item = ITEMS[item_key]
        current_level = self.player.equipment[item_key]
        if current_level >= item["max_stacks"]:
            self.show_message(self.text("item_max"))
            return False
        cost = item["cost"] + current_level * 70
        if self.player.gold < cost:
            self.show_message(self.text("not_enough_gold"))
            return False

        self.player.gold -= cost
        self.player.equipment[item_key] += 1
        if "attack_damage" in item:
            self.player.attack_damage += item["attack_damage"]
        if "speed" in item:
            self.player.speed += item["speed"]
        if "max_hp" in item:
            self.player.max_hp += item["max_hp"]
            self.player.hp += item["max_hp"]
        self.show_message(self.text("bought", item=self.item_name(item_key)))
        return True

    def select_shop_at(self, x, y):
        if not self.near_shop():
            return False
        for item_key, left, top, right, bottom in self.shop_cards:
            if left <= x <= right and top <= y <= bottom:
                return self.buy_item(item_key)
        return False

    def loop(self):
        current = time.perf_counter()
        dt = min(0.05, current - self.last_time)
        self.last_time = current
        if self.state == "loading" and current - self.loading_started_at >= 1.15:
            self.state = "playing"
            self.last_time = time.perf_counter()
        if self.state == "playing" and not self.match_over:
            self.update(dt)
        self.draw()
        self.root.after(FPS_MS, self.loop)

    def update(self, dt):
        self.match_time += dt
        self.enemy_xp_timer += dt
        if self.enemy_xp_timer >= 5:
            self.enemy_xp_timer = 0
            self.gain_xp(self.enemy_hero, self.mode_rule()["enemy_xp_rate"])
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_wave()
            self.spawn_timer = self.mode_rule()["spawn_interval"]

        self.update_player(dt)
        self.update_enemy_hero(dt)
        self.update_minions(dt)
        self.update_towers()
        self.update_cores()
        self.update_projectiles(dt)
        self.update_effects(dt)
        self.cleanup_dead()
        self.check_winner()

    def spawn_wave(self):
        for lane in self.paths:
            blue_path = self.paths[lane]
            red_path = list(reversed(blue_path))
            for i in range(3):
                bx, by = blue_path[0]
                rx, ry = red_path[0]
                offset = (i - 1) * 18
                self.minions.append(
                    Minion(
                        bx + random.uniform(-6, 6),
                        by + offset,
                        "blue",
                        120,
                        120,
                        10,
                        68,
                        14,
                        60,
                        1.15,
                        lane=lane,
                    )
                )
                self.minions.append(
                    Minion(
                        rx + random.uniform(-6, 6),
                        ry - offset,
                        "red",
                        120,
                        120,
                        10,
                        68,
                        14,
                        60,
                        1.15,
                        lane=lane,
                    )
                )

    def update_player(self, dt):
        if not self.player.alive:
            if self.now() >= self.player.respawn_at:
                self.respawn(self.player)
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
        self.player.x = clamp(self.player.x + nx * self.player.speed * dt, 35, WIDTH - 35)
        self.player.y = clamp(self.player.y + ny * self.player.speed * dt, 35, HEIGHT - 35)
        self.regen_hero(self.player, dt)

    def update_enemy_hero(self, dt):
        hero = self.enemy_hero
        if not hero.alive:
            if self.now() >= hero.respawn_at:
                self.respawn(hero)
            return

        self.regen_hero(hero, dt)
        hp_ratio = hero.hp / hero.max_hp
        if hp_ratio < 0.28:
            tx, ty = self.red_core.x, self.red_core.y
        else:
            target = self.nearest_enemy(hero, 270, include_cores=False)
            if target:
                if dist(hero, target) <= hero.attack_range:
                    self.hero_attack(hero, target)
                    if self.now() >= hero.cooldowns["q"]:
                        self.cast_ai_bolt(hero, target)
                tx, ty = target.x, target.y
            else:
                tx, ty = 560, 350

        dx, dy = tx - hero.x, ty - hero.y
        if hp_ratio >= 0.28 and math.hypot(dx, dy) < 150:
            return
        nx, ny = norm(dx, dy)
        hero.x = clamp(hero.x + nx * hero.speed * dt, 35, WIDTH - 35)
        hero.y = clamp(hero.y + ny * hero.speed * dt, 35, HEIGHT - 35)

    def regen_hero(self, hero, dt):
        if dist(hero, self.blue_core if hero.team == "blue" else self.red_core) < 120:
            hero.hp = min(hero.max_hp, hero.hp + 34 * dt)

    def update_minions(self, dt):
        for minion in self.minions:
            if not minion.alive:
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
            minion.x += nx * minion.speed * dt
            minion.y += ny * minion.speed * dt

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
                    self.spawn_hit_fx(p.x, p.y, p.color)
                    continue
            else:
                p.x += p.vx * p.speed * dt
                p.y += p.vy * p.speed * dt
                hit = False
                for target in self.enemies_of(p.team, include_cores=True):
                    if target.alive and dist_xy(p.x, p.y, target.x, target.y) <= p.radius + target.radius:
                        self.apply_damage(target, p.damage, p.team)
                        self.spawn_hit_fx(p.x, p.y, p.color)
                        hit = not p.pierce
                        if hit:
                            break
                if hit:
                    continue
            if -30 <= p.x <= WIDTH + 30 and -30 <= p.y <= HEIGHT + 30:
                kept.append(p)
        self.projectiles = kept

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

    def cleanup_dead(self):
        self.minions = [m for m in self.minions if m.alive]

        for hero in [self.player, self.enemy_hero]:
            if not hero.alive and hero.respawn_at == 0:
                hero.respawn_at = self.now() + 5
                killer = self.enemy_hero if hero.team == "blue" else self.player
                killer.kills += 1
                killer.gold += 80
                if killer.team == "red":
                    self.gain_xp(killer, 120)
                defeat_text = self.text(
                    "defeated",
                    killer=self.hero_name(killer.hero_key),
                    victim=self.hero_name(hero.hero_key),
                )
                self.show_message(defeat_text)
                self.spawn_banner(defeat_text, "#ffb0aa", ttl=1.6)

    def check_winner(self):
        if not self.blue_core.alive:
            self.match_over = True
            self.winner = "red"
        elif not self.red_core.alive:
            self.match_over = True
            self.winner = "blue"

    def show_message(self, text):
        self.message = text
        self.message_until = self.now() + 2.2

    def respawn(self, hero):
        hero.alive = True
        hero.hp = hero.max_hp
        hero.respawn_at = 0
        if hero.team == "blue":
            hero.x, hero.y = 130, 580
        else:
            hero.x, hero.y = 965, 120

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
            if e.alive and dist(unit, e) <= range_value
        ]
        if not candidates:
            return None
        priority = {Minion: 0, Hero: 1, Tower: 2, Core: 3}
        candidates.sort(key=lambda e: (priority.get(type(e), 9), dist(unit, e)))
        return candidates[0]

    def unit_attack(self, unit, target):
        current = self.now()
        if current < unit.next_attack:
            return
        unit.next_attack = current + unit.attack_cd
        color = "#8fd3ff" if unit.team == "blue" else "#ff9a91"
        self.spawn_particles(unit.x, unit.y, color, count=6, speed=70, spread=0.5, radius=2.1, ttl=0.18)
        self.projectiles.append(
            Projectile(
                unit.x,
                unit.y,
                unit.team,
                unit.attack_damage,
                330 if isinstance(unit, (Tower, Core)) else 250,
                target=target,
                radius=7 if isinstance(unit, Core) else 6 if isinstance(unit, Tower) else 4,
                ttl=2.2,
                color=color,
            )
        )

    def hero_attack(self, hero, forced_target=None):
        if not hero.alive:
            return
        target = forced_target or self.nearest_enemy(hero, hero.attack_range, include_cores=True)
        if not target:
            return
        self.unit_attack(hero, target)

    def skill_ready(self, hero, key):
        current = self.now()
        if not hero.alive or current < hero.cooldowns[key]:
            return False
        hero.cooldowns[key] = current + hero.skill_cds[key]
        return True

    def aim_vector(self, hero):
        vx, vy = norm(self.mouse_x - hero.x, self.mouse_y - hero.y)
        if vx == 0 and vy == 0:
            return 1, 0
        return vx, vy

    def damage_area(self, team, x, y, radius, amount, include_cores=False):
        for target in self.enemies_of(team, include_cores=include_cores):
            if target.alive and dist_xy(x, y, target.x, target.y) <= radius + target.radius:
                self.apply_damage(target, amount, team)

    def skill_damage(self, hero, base, multiplier=1.0):
        base_attack = HEROES[hero.hero_key]["attack_damage"]
        attack_bonus = max(0, hero.attack_damage - base_attack)
        return base * multiplier + (hero.level - 1) * 8 * multiplier + attack_bonus * 0.45 * multiplier

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

    def spawn_cast_fx(self, hero, skill_key):
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

    def cast_q(self, hero):
        if not self.skill_ready(hero, "q"):
            return
        vx, vy = self.aim_vector(hero)
        self.spawn_cast_fx(hero, "q")
        if hero.hero_key == "sentinel":
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=76, ttl=0.34)
            self.damage_area(hero.team, hero.x, hero.y, 72, self.skill_damage(hero, 68))
            self.projectiles.append(
                Projectile(hero.x, hero.y, hero.team, self.skill_damage(hero, 54), 310, vx=vx, vy=vy, radius=14, pierce=True, ttl=0.85, color=hero.accent)
            )
            return

        if hero.hero_key == "shade":
            self.spawn_beam(hero.x, hero.y, hero.x + vx * 165, hero.y + vy * 165, hero.accent, width=6, ttl=0.13)
            self.projectiles.append(
                Projectile(hero.x, hero.y, hero.team, self.skill_damage(hero, 92), 560, vx=vx, vy=vy, radius=9, pierce=False, ttl=0.62, color=hero.accent)
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
                        self.skill_damage(hero, 46),
                        520,
                        vx=ax,
                        vy=ay,
                        radius=7,
                        pierce=False,
                        ttl=0.9,
                        color=hero.accent,
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
                    self.skill_damage(hero, 96),
                    360,
                    vx=vx,
                    vy=vy,
                    radius=15,
                    pierce=True,
                    ttl=1.05,
                    color=hero.accent,
                )
            )
            return

        self.projectiles.append(
            Projectile(hero.x, hero.y, hero.team, self.skill_damage(hero, 82), 430, vx=vx, vy=vy, radius=11, pierce=True, ttl=0.95, color=hero.accent)
        )
        self.spawn_beam(hero.x, hero.y, hero.x + vx * 140, hero.y + vy * 140, hero.accent, width=4, ttl=0.14)

    def cast_e(self, hero):
        if not self.skill_ready(hero, "e"):
            return
        vx, vy = self.aim_vector(hero)
        self.spawn_cast_fx(hero, "e")
        if hero.hero_key == "sentinel":
            hero.hp = min(hero.max_hp, hero.hp + 140)
            hero.next_attack = 0
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=94, ttl=0.36)
            self.spawn_particles(hero.x, hero.y, hero.accent, count=18, speed=90, spread=0.9, radius=3.0, ttl=0.36)
            return

        if hero.hero_key == "arcanist":
            self.spawn_beam(hero.x, hero.y, hero.x, hero.y, hero.accent, width=8, ttl=0.2)
            hero.hp = min(hero.max_hp, hero.hp + 95)
            self.damage_area(hero.team, hero.x, hero.y, 82, self.skill_damage(hero, 54))
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
            self.damage_area(hero.team, hero.x, hero.y, 54, self.skill_damage(hero, 72))
            self.spawn_hit_fx(hero.x, hero.y, hero.accent, big=True)
            return

        distance = 168 if hero.hero_key == "ranger" else 120
        hero.x = clamp(hero.x + vx * distance, 35, WIDTH - 35)
        hero.y = clamp(hero.y + vy * distance, 35, HEIGHT - 35)
        self.spawn_beam(old_x, old_y, hero.x, hero.y, hero.accent, width=5 if hero.hero_key == "ranger" else 4, ttl=0.16)
        if hero.hero_key == "ranger":
            hero.next_attack = 0
            self.spawn_hit_fx(hero.x, hero.y, hero.accent)
        else:
            self.damage_area(hero.team, hero.x, hero.y, 52, self.skill_damage(hero, 42))
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
            self.damage_area(hero.team, self.mouse_x, self.mouse_y, 136, self.skill_damage(hero, 154, 1.35), include_cores=True)
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
            self.damage_area(hero.team, tx, ty, 78, self.skill_damage(hero, 188, 1.5), include_cores=False)
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
                        self.skill_damage(hero, 42, 1.3),
                        500,
                        vx=math.cos(angle + offset),
                        vy=math.sin(angle + offset),
                        radius=8,
                        pierce=True,
                        ttl=1.05,
                        color=hero.accent,
                    )
                )
            self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=84, ttl=0.28)
            return

        if hero.hero_key == "arcanist":
            self.spawn_beam(hero.x, hero.y, self.mouse_x, self.mouse_y, hero.accent, width=7, ttl=0.22)
            self.spawn_ring(self.mouse_x, self.mouse_y, hero.accent, base_radius=130, ttl=0.55)
            self.spawn_particles(self.mouse_x, self.mouse_y, hero.accent, count=28, speed=210, spread=1.4, radius=3.2, ttl=0.42)
            self.damage_area(hero.team, self.mouse_x, self.mouse_y, 120, self.skill_damage(hero, 176, 1.45), include_cores=True)
            return

        self.spawn_beam(hero.x, hero.y, self.mouse_x, self.mouse_y, hero.accent, width=6, ttl=0.18)
        self.spawn_ring(self.mouse_x, self.mouse_y, hero.accent, base_radius=112, ttl=0.48)
        self.spawn_particles(self.mouse_x, self.mouse_y, hero.accent, count=20, speed=190, spread=1.25, radius=3.0, ttl=0.36)
        self.damage_area(hero.team, self.mouse_x, self.mouse_y, 96, self.skill_damage(hero, 148, 1.45), include_cores=True)

    def cast_ai_bolt(self, hero, target):
        hero.cooldowns["q"] = self.now() + 4.2
        vx, vy = norm(target.x - hero.x, target.y - hero.y)
        self.projectiles.append(
            Projectile(
                hero.x,
                hero.y,
                hero.team,
                self.skill_damage(hero, 64),
                385,
                vx=vx,
                vy=vy,
                radius=10,
                pierce=True,
                ttl=0.9,
                color="#ff6c7a",
            )
        )

    def reward_player(self, target):
        rule = self.mode_rule()
        if isinstance(target, Minion):
            self.player.gold += int(8 * rule["gold_mult"])
            self.gain_xp(self.player, int(28 * rule["xp_mult"]))
        elif isinstance(target, Tower):
            self.player.gold += int(120 * rule["gold_mult"])
            self.gain_xp(self.player, int(90 * rule["xp_mult"]))
        elif isinstance(target, Hero):
            self.player.gold += int(120 * rule["gold_mult"])
            self.gain_xp(self.player, int(120 * rule["xp_mult"]))

    def gain_xp(self, hero, amount):
        hero.xp += amount
        while hero.xp >= hero.next_xp:
            hero.xp -= hero.next_xp
            self.level_up(hero)

    def level_up(self, hero, silent=False):
        hero.level += 1
        hero.next_xp = int(hero.next_xp * 1.32)
        hero.max_hp += 48
        hero.hp = min(hero.max_hp, hero.hp + 48)
        hero.attack_damage += 4
        hero.attack_range += 3
        self.spawn_particles(hero.x, hero.y, hero.accent, count=22, speed=170, spread=1.1, radius=3.0, ttl=0.42)
        self.spawn_ring(hero.x, hero.y, hero.accent, base_radius=62, ttl=0.32)
        if not silent and hero.team == "blue":
            text = self.text("level_up", name=self.hero_name(hero.hero_key), level=hero.level)
            self.show_message(text)
            self.spawn_banner(text, hero.accent, ttl=1.4)

    def apply_damage(self, target, amount, attacker_team):
        if isinstance(target, (Tower, Core)):
            amount *= 1.35 if attacker_team == "blue" else 1.15
        was_alive = target.alive
        self.spawn_damage_text(target.x, target.y - 18, amount, "#ff9a91" if attacker_team == "blue" else "#8fd3ff")
        target.take_damage(amount)
        if was_alive and not target.alive:
            if attacker_team == "blue" and target.team == "red":
                self.reward_player(target)
            if isinstance(target, Tower):
                text = self.text("destroyed", name=target.name)
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

    def draw(self):
        c = self.canvas
        c.delete("all")
        if self.state == "language":
            self.draw_language(c)
            return
        if self.state == "lobby":
            self.draw_lobby(c)
            return
        if self.state == "select":
            self.draw_select(c)
            return
        if self.state == "loading":
            self.draw_loading(c)
            return

        self.draw_map(c)
        for core in [self.blue_core, self.red_core]:
            self.draw_core(c, core)
        for tower in self.towers:
            if tower.alive:
                self.draw_tower(c, tower)
        for minion in self.minions:
            self.draw_minion(c, minion)
        self.draw_hero(c, self.player)
        self.draw_hero(c, self.enemy_hero)
        for p in self.projectiles:
            c.create_oval(
                p.x - p.radius,
                p.y - p.radius,
                p.x + p.radius,
                p.y + p.radius,
                fill=p.color,
                outline="",
            )
        for e in self.effects:
            alpha_width = max(1, int(5 * e.ttl / e.max_ttl))
            c.create_oval(
                e.x - e.radius,
                e.y - e.radius,
                e.x + e.radius,
                e.y + e.radius,
                outline=e.color,
                width=alpha_width,
            )
        for beam in self.beams:
            width = max(1, int(beam.width * beam.ttl / beam.max_ttl))
            c.create_line(beam.x1, beam.y1, beam.x2, beam.y2, fill=beam.color, width=width, capstyle=tk.ROUND)
        for p in self.particles:
            size = p.radius * (0.7 if p.shrink else 1)
            c.create_oval(
                p.x - size,
                p.y - size,
                p.x + size,
                p.y + size,
                fill=p.color,
                outline="",
            )
        for text in self.float_texts:
            c.create_text(text.x, text.y, text=text.text, fill=text.color, font=("Segoe UI", 11, "bold"))
        for banner in self.banners:
            alpha = banner.ttl / banner.max_ttl
            left = WIDTH // 2 - 220
            right = WIDTH // 2 + 220
            top = 120
            bottom = 172
            fill = "#101416" if alpha > 0.3 else "#0f1416"
            c.create_rectangle(left, top, right, bottom, fill=fill, outline=banner.color, width=2)
            c.create_text(WIDTH // 2, 147, text=banner.text, fill=banner.color, font=("Segoe UI", 18, "bold"))
        self.draw_ui(c)

    def draw_language(self, c):
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#14191c", outline="")
        self.draw_menu_backdrop(c)
        c.create_rectangle(0, 0, WIDTH, 118, fill="#0f1416", outline="")
        c.create_text(WIDTH // 2, 42, text="LANGUAGE / 语言", fill="#f5f1d7", font=("Segoe UI", 30, "bold"))
        c.create_text(WIDTH // 2, 78, text="Python MOBA Prototype", fill="#9ea898", font=("Segoe UI", 13))

        self.language_buttons = []
        buttons = [("zh", "中文", "进入中文界面"), ("en", "English", "Use English UI")]
        left = 294
        top = 252
        for index, (language, title, subtitle) in enumerate(buttons):
            x1 = left + index * 272
            x2 = x1 + 218
            y1 = top
            y2 = top + 154
            self.language_buttons.append((language, x1, y1, x2, y2))
            active = x1 <= self.mouse_x <= x2 and y1 <= self.mouse_y <= y2
            outline = "#d8cf9b" if active else "#394043"
            c.create_rectangle(x1, y1, x2, y2, fill="#20282b", outline=outline, width=3)
            c.create_text((x1 + x2) // 2, y1 + 60, text=title, fill="#f5f1d7", font=("Segoe UI", 25, "bold"))
            c.create_text((x1 + x2) // 2, y1 + 102, text=subtitle, fill="#aeb8ad", font=("Segoe UI", 12))

        c.create_rectangle(384, 518, 716, 562, fill="#101416", outline="#394043")
        c.create_text(WIDTH // 2, 540, text="MOBA READY", fill="#d8cf9b", font=("Segoe UI", 13, "bold"))

    def draw_select(self, c):
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#151b1d", outline="")
        self.draw_menu_backdrop(c)
        c.create_rectangle(0, 0, WIDTH, 95, fill="#101416", outline="")
        c.create_text(
            WIDTH // 2,
            38,
            text=self.text("hero_title"),
            fill="#f5f1d7",
            font=("Segoe UI", 28, "bold"),
        )
        c.create_text(
            WIDTH // 2,
            72,
            text=self.text("language_subtitle"),
            fill="#9ea898",
            font=("Segoe UI", 13),
        )

        self.hero_cards = []
        card_w = 300
        card_h = 206
        gap_x = 28
        gap_y = 24
        columns = 3
        start_x = (WIDTH - card_w * columns - gap_x * (columns - 1)) // 2
        start_y = 122
        for index, (hero_key, config) in enumerate(HEROES.items()):
            row = index // columns
            col = index % columns
            left = start_x + col * (card_w + gap_x)
            top = start_y + row * (card_h + gap_y)
            right = left + card_w
            bottom = top + card_h
            self.hero_cards.append((hero_key, left, top, right, bottom))
            active = left <= self.mouse_x <= right and top <= self.mouse_y <= bottom
            outline = config["accent"] if active else "#394043"
            c.create_rectangle(left, top, right, bottom, fill="#20282b", outline=outline, width=3)
            c.create_rectangle(left, top, right, top + 52, fill="#161c1f", outline="")
            c.create_text(left + 20, top + 19, text=self.hero_name(hero_key), fill="#f5f1d7", anchor="w", font=("Segoe UI", 15, "bold"))
            c.create_text(left + 20, top + 40, text=self.hero_role(hero_key), fill=config["accent"], anchor="w", font=("Segoe UI", 10, "bold"))
            self.draw_hero_icon(c, left + 244, top + 86, config)

            stat_y = top + 76
            self.draw_stat(c, left + 18, stat_y, "HP", config["hp"], 760, "#48d06b")
            self.draw_stat(c, left + 18, stat_y + 28, "SPD", config["speed"], 250, "#76b7ff")
            self.draw_stat(c, left + 18, stat_y + 56, "ATK", config["attack_damage"], 45, "#f7d765")
            c.create_text(left + 18, top + 158, text=f"Q {self.hero_skill(hero_key, 'q')}", fill="#cfd6cd", anchor="w", font=("Segoe UI", 9, "bold"))
            c.create_text(left + 18, top + 178, text=f"E {self.hero_skill(hero_key, 'e')}", fill="#cfd6cd", anchor="w", font=("Segoe UI", 9, "bold"))
            c.create_text(left + 156, top + 178, text=f"R {self.hero_skill(hero_key, 'r')}", fill="#f5d28a", anchor="w", font=("Segoe UI", 9, "bold"))

        c.create_rectangle(358, 610, 742, 656, fill="#101416", outline="#394043")
        c.create_text(WIDTH // 2, 633, text=self.text("choose_hero"), fill="#d8cf9b", font=("Segoe UI", 13, "bold"))

    def draw_lobby(self, c):
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#12181b", outline="")
        self.draw_menu_backdrop(c)
        c.create_rectangle(0, 0, WIDTH, 82, fill="#0d1215", outline="")
        c.create_text(34, 30, text=self.text("lobby_title"), fill="#f5f1d7", anchor="w", font=("Segoe UI", 25, "bold"))
        c.create_text(36, 58, text=self.text("lobby_subtitle"), fill="#aeb8ad", anchor="w", font=("Segoe UI", 11))
        c.create_text(WIDTH - 34, 30, text=self.text("profile"), fill="#f7d765", anchor="e", font=("Segoe UI", 13, "bold"))
        c.create_text(WIDTH - 34, 58, text=self.text("season"), fill="#cfd6cd", anchor="e", font=("Segoe UI", 12))

        c.create_rectangle(44, 122, 342, 254, fill="#20282b", outline="#d8cf9b", width=2)
        c.create_text(72, 154, text=self.text("profile"), fill="#f5f1d7", anchor="w", font=("Segoe UI", 15, "bold"))
        mode_name = self.mode_configs()[self.selected_mode_key][0] if self.selected_mode_key else self.text("mode_unselected")
        c.create_text(72, 188, text=mode_name, fill="#78a3ff", anchor="w", font=("Segoe UI", 18, "bold"))
        c.create_text(72, 222, text=self.text("hero_unselected"), fill="#aeb8ad", anchor="w", font=("Segoe UI", 12))

        self.mode_cards = []
        mode_layout = [
            ("rank", 404, 132, 666, 284),
            ("train", 696, 132, 958, 284),
            ("quick", 404, 318, 666, 470),
        ]
        mode_configs = self.mode_configs()
        for mode_key, left, top, right, bottom in mode_layout:
            title, color, desc = mode_configs[mode_key]
            selected = self.selected_mode_key == mode_key
            hovered = left <= self.mouse_x <= right and top <= self.mouse_y <= bottom
            outline = "#f5f1d7" if selected else color if hovered else "#394043"
            fill = "#27343a" if selected else "#20282b"
            self.mode_cards.append((mode_key, left, top, right, bottom))
            c.create_rectangle(left, top, right, bottom, fill=fill, outline=outline, width=3 if selected else 2)
            c.create_rectangle(left, top, right, top + 38, fill="#151b1e", outline="")
            c.create_text(left + 22, top + 20, text=title, fill="#f5f1d7", anchor="w", font=("Segoe UI", 15, "bold"))
            c.create_text(left + 22, top + 62, text=desc, fill="#cfd6cd", anchor="w", font=("Segoe UI", 9), width=right - left - 42)
            c.create_line(left + 24, bottom - 28, right - 24, top + 96, fill=color, width=5)
            c.create_oval(right - 74, bottom - 78, right - 24, bottom - 28, fill=color, outline="")

        self.lobby_buttons = [("start", 408, 548, 692, 616)]
        button_fill = "#d8cf9b" if self.selected_mode_key else "#4b4f4b"
        text_fill = "#101416" if self.selected_mode_key else "#aeb8ad"
        c.create_rectangle(408, 548, 692, 616, fill=button_fill, outline="#f5f1d7", width=3)
        c.create_text(WIDTH // 2, 582, text=self.text("start_match"), fill=text_fill, font=("Segoe UI", 21, "bold"))
        c.create_text(WIDTH // 2, 642, text=self.text("mode_prompt"), fill="#aeb8ad", font=("Segoe UI", 12))

    def draw_loading(self, c):
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#101416", outline="")
        self.draw_menu_backdrop(c)
        progress = clamp((self.now() - self.loading_started_at) / 1.15, 0, 1)
        c.create_text(WIDTH // 2, 86, text=self.text("loading"), fill="#f5f1d7", font=("Segoe UI", 26, "bold"))
        c.create_rectangle(184, 154, 456, 514, fill="#20282b", outline=self.player.accent, width=3)
        c.create_rectangle(644, 154, 916, 514, fill="#20282b", outline="#e84d4f", width=3)
        self.draw_hero_portrait(c, 320, 300, HEROES[self.player.hero_key])
        self.draw_hero_portrait(c, 780, 300, HEROES["vanguard"])
        c.create_text(320, 430, text=self.hero_name(self.player.hero_key), fill="#f5f1d7", font=("Segoe UI", 20, "bold"))
        c.create_text(780, 430, text=self.text("enemy_prefix", name=self.hero_name("vanguard")), fill="#f5f1d7", font=("Segoe UI", 20, "bold"))
        c.create_text(WIDTH // 2, 320, text=self.text("versus"), fill="#d8cf9b", font=("Segoe UI", 28, "bold"))
        c.create_rectangle(260, 590, 840, 606, fill="#252a2a", outline="")
        c.create_rectangle(260, 590, 260 + 580 * progress, 606, fill="#d8cf9b", outline="")

    def draw_menu_backdrop(self, c):
        for path in self.paths.values():
            points = []
            for x, y in path:
                points.extend([x, y])
            c.create_line(*points, fill="#263139", width=62, capstyle=tk.ROUND, joinstyle=tk.ROUND)
            c.create_line(*points, fill="#3f4b4e", width=28, capstyle=tk.ROUND, joinstyle=tk.ROUND)
        c.create_oval(-90, HEIGHT - 160, 230, HEIGHT + 160, fill="#203f5f", outline="")
        c.create_oval(WIDTH - 230, -160, WIDTH + 90, 160, fill="#5b2428", outline="")
        for i in range(18):
            rng = random.Random(100 + i)
            x = rng.randint(80, WIDTH - 80)
            y = rng.randint(130, HEIGHT - 80)
            c.create_rectangle(x - 18, y - 2, x + 18, y + 2, fill="#2d3939", outline="")

    def draw_hero_portrait(self, c, x, y, config):
        accent = config["accent"]
        c.create_oval(x - 54, y - 54, x + 54, y + 54, fill="#14191c", outline=accent, width=4)
        c.create_polygon(x, y - 48, x - 45, y + 38, x + 45, y + 38, fill=accent, outline="#f5f1d7", width=2)
        c.create_oval(x - 24, y - 20, x + 24, y + 28, fill="#1f282c", outline="")
        c.create_line(x - 62, y + 68, x + 62, y + 68, fill=accent, width=3)

    def draw_hero_icon(self, c, x, y, config):
        accent = config["accent"]
        c.create_oval(x - 36, y - 36, x + 36, y + 36, fill="#14191c", outline=accent, width=3)
        c.create_polygon(x, y - 30, x - 28, y + 24, x + 28, y + 24, fill=accent, outline="#f5f1d7", width=1)
        c.create_oval(x - 14, y - 10, x + 14, y + 18, fill="#1f282c", outline="")

    def draw_stat(self, c, x, y, label, value, max_value, color):
        c.create_text(x, y, text=label, fill="#f5f1d7", anchor="w", font=("Segoe UI", 10, "bold"))
        c.create_rectangle(x + 48, y - 6, x + 224, y + 6, fill="#151b1d", outline="")
        pct = clamp(value / max_value, 0, 1)
        c.create_rectangle(x + 48, y - 6, x + 48 + 176 * pct, y + 6, fill=color, outline="")
        c.create_text(x + 234, y, text=str(int(value)), fill="#cfd6cd", anchor="w", font=("Segoe UI", 10))

    def draw_map(self, c):
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#17291f", outline="")
        for lane, path in self.paths.items():
            points = []
            for x, y in path:
                points.extend([x, y])
            c.create_line(*points, fill="#56624d", width=54, capstyle=tk.ROUND, joinstyle=tk.ROUND)
            c.create_line(*points, fill="#8d8b73", width=34, capstyle=tk.ROUND, joinstyle=tk.ROUND)
            c.create_line(*points, fill="#c0b988", width=3, dash=(12, 14))

        for _ in range(28):
            rng = random.Random(_)
            x = rng.randint(40, WIDTH - 40)
            y = rng.randint(45, HEIGHT - 45)
            c.create_oval(x - 8, y - 5, x + 8, y + 5, fill="#203c2d", outline="")

        c.create_polygon(0, HEIGHT, 0, 505, 188, HEIGHT, fill="#203f5f", outline="")
        c.create_polygon(WIDTH, 0, WIDTH, 195, 912, 0, fill="#5b2428", outline="")

    def draw_bar(self, c, x, y, width, hp, max_hp, color):
        pct = 0 if max_hp <= 0 else clamp(hp / max_hp, 0, 1)
        c.create_rectangle(x, y, x + width, y + 6, fill="#252a2a", outline="")
        c.create_rectangle(x, y, x + width * pct, y + 6, fill=color, outline="")

    def draw_core(self, c, core):
        color = team_color(core.team)
        c.create_oval(
            core.x - core.radius,
            core.y - core.radius,
            core.x + core.radius,
            core.y + core.radius,
            fill=color,
            outline="#f5f1d7",
            width=3,
        )
        c.create_oval(core.x - 14, core.y - 14, core.x + 14, core.y + 14, fill="#f5f1d7", outline="")
        self.draw_bar(c, core.x - 42, core.y - 50, 84, core.hp, core.max_hp, "#48d06b")

    def draw_tower(self, c, tower):
        color = team_color(tower.team)
        x, y, r = tower.x, tower.y, tower.radius
        c.create_rectangle(x - r, y - r, x + r, y + r, fill="#2e3335", outline=color, width=3)
        c.create_polygon(x, y - r - 16, x - 18, y, x + 18, y, fill=color, outline="#f5f1d7")
        self.draw_bar(c, x - 30, y - 38, 60, tower.hp, tower.max_hp, "#48d06b")

    def draw_minion(self, c, minion):
        color = team_color(minion.team)
        c.create_oval(
            minion.x - minion.radius,
            minion.y - minion.radius,
            minion.x + minion.radius,
            minion.y + minion.radius,
            fill=color,
            outline="#15191b",
            width=2,
        )
        self.draw_bar(c, minion.x - 15, minion.y - 19, 30, minion.hp, minion.max_hp, "#48d06b")

    def draw_hero(self, c, hero):
        if not hero.alive:
            x, y = (130, 580) if hero.team == "blue" else (965, 120)
            left = max(0, int(hero.respawn_at - self.now() + 1))
            c.create_text(x, y - 38, text=str(left), fill="#ffffff", font=("Segoe UI", 18, "bold"))
            return
        color = team_color(hero.team)
        angle = math.atan2(self.mouse_y - hero.y, self.mouse_x - hero.x) if hero.team == "blue" else 0
        pts = []
        for i, spread in enumerate([0, 2.35, -2.35]):
            length = 25 if i == 0 else 18
            pts.extend([hero.x + math.cos(angle + spread) * length, hero.y + math.sin(angle + spread) * length])
        c.create_polygon(*pts, fill=color, outline=hero.accent, width=3)
        c.create_oval(hero.x - 10, hero.y - 10, hero.x + 10, hero.y + 10, fill="#1a2024", outline="")
        self.draw_hero_plate(c, hero)

    def draw_hero_plate(self, c, hero):
        display_name = self.hero_name(hero.hero_key)
        if hero.team == "red":
            display_name = self.text("enemy_prefix", name=display_name)
        x = hero.x
        y = hero.y - 58
        c.create_rectangle(x - 54, y - 12, x + 54, y + 23, fill="#101416", outline="#2f383b")
        c.create_oval(x - 61, y - 14, x - 31, y + 16, outline=hero.accent, width=2)
        c.create_oval(x - 58, y - 11, x - 34, y + 13, fill=hero.accent, outline="#f5f1d7", width=1)
        c.create_text(x - 46, y + 1, text=str(hero.level), fill="#111719", font=("Segoe UI", 10, "bold"))
        name_size = 8 if len(display_name) > 10 else 9
        c.create_text(x - 28, y - 1, text=display_name, fill="#f5f1d7", anchor="w", font=("Segoe UI", name_size, "bold"))
        self.draw_bar(c, x - 32, y + 14, 74, hero.hp, hero.max_hp, "#48d06b")

    def draw_ui(self, c):
        c.create_rectangle(0, 0, WIDTH, 50, fill="#0d1215", outline="")
        c.create_rectangle(398, 7, 702, 43, fill="#151b1e", outline="#394043", width=2)
        c.create_text(438, 25, text=str(self.player.kills), fill="#78a3ff", font=("Segoe UI", 16, "bold"))
        c.create_text(WIDTH // 2, 25, text=self.format_time(self.match_time), fill="#f5f1d7", font=("Segoe UI", 14, "bold"))
        c.create_text(662, 25, text=str(self.enemy_hero.kills), fill="#ff7b7c", font=("Segoe UI", 16, "bold"))
        c.create_text(24, 25, text=self.hero_name(self.player.hero_key), fill="#78a3ff", anchor="w", font=("Segoe UI", 13, "bold"))
        c.create_text(164, 25, text=f"{self.text('level')} {self.player.level}", fill="#f5f1d7", anchor="w", font=("Segoe UI", 13))
        c.create_text(260, 25, text=f"G {self.player.gold}", fill="#f7d765", anchor="w", font=("Segoe UI", 13))
        xp_pct = clamp(self.player.xp / self.player.next_xp, 0, 1)
        c.create_rectangle(24, 43, 300, 47, fill="#252a2a", outline="")
        c.create_rectangle(24, 43, 24 + 276 * xp_pct, 47, fill="#b38cff", outline="")
        c.create_text(WIDTH - 24, 23, text=self.text("red"), fill="#ff7b7c", anchor="e", font=("Segoe UI", 13, "bold"))

        self.draw_minimap(c)
        self.draw_virtual_stick(c)
        self.draw_skill(c, WIDTH - 112, HEIGHT - 92, "Q", self.player.cooldowns["q"], self.player.skill_cds["q"], 46)
        self.draw_skill(c, WIDTH - 58, HEIGHT - 154, "E", self.player.cooldowns["e"], self.player.skill_cds["e"], 46)
        self.draw_skill(c, WIDTH - 172, HEIGHT - 154, "R", self.player.cooldowns["r"], self.player.skill_cds["r"], 52)
        self.draw_skill(c, WIDTH - 58, HEIGHT - 70, "A", self.player.next_attack, self.player.attack_cd, 42)

        if self.now() < self.message_until:
            c.create_text(WIDTH // 2, 78, text=self.message, fill="#f5f1d7", font=("Segoe UI", 18, "bold"))

        if self.near_shop():
            self.draw_shop(c)

        if self.match_over:
            overlay = "#17291f" if self.winner == "blue" else "#35191d"
            c.create_rectangle(300, 248, 800, 452, fill=overlay, outline="#f5f1d7", width=2)
            text = self.text("victory_blue") if self.winner == "blue" else self.text("victory_red")
            c.create_text(WIDTH // 2, 326, text=text, fill="#f5f1d7", font=("Segoe UI", 34, "bold"))
            c.create_text(WIDTH // 2, 382, text=self.text("exit"), fill="#cfc8ac", font=("Segoe UI", 14))

    def format_time(self, seconds):
        total = int(seconds)
        return f"{total // 60:02d}:{total % 60:02d}"

    def draw_virtual_stick(self, c):
        x, y = 92, HEIGHT - 92
        c.create_oval(x - 62, y - 62, x + 62, y + 62, fill="#0d1215", outline="#394043", width=2)
        c.create_oval(x - 28, y - 28, x + 28, y + 28, fill="#1f2a2e", outline="#d8cf9b", width=2)
        c.create_line(x - 50, y, x + 50, y, fill="#394043", width=2)
        c.create_line(x, y - 50, x, y + 50, fill="#394043", width=2)

    def draw_minimap(self, c):
        left, top = 18, 64
        w, h = 178, 122
        c.create_rectangle(left, top, left + w, top + h, fill="#0d1215", outline="#d8cf9b", width=2)
        for path in self.paths.values():
            points = []
            for x, y in path:
                points.extend([left + x / WIDTH * w, top + y / HEIGHT * h])
            c.create_line(*points, fill="#8d8b73", width=4, capstyle=tk.ROUND, joinstyle=tk.ROUND)
        for tower in self.towers:
            if tower.alive:
                self.draw_minimap_dot(c, left, top, w, h, tower.x, tower.y, team_color(tower.team), 3)
        for minion in self.minions[::2]:
            self.draw_minimap_dot(c, left, top, w, h, minion.x, minion.y, team_color(minion.team), 2)
        self.draw_minimap_dot(c, left, top, w, h, self.blue_core.x, self.blue_core.y, "#78a3ff", 5)
        self.draw_minimap_dot(c, left, top, w, h, self.red_core.x, self.red_core.y, "#ff7b7c", 5)
        if self.player.alive:
            self.draw_minimap_dot(c, left, top, w, h, self.player.x, self.player.y, "#ffffff", 4)
        if self.enemy_hero.alive:
            self.draw_minimap_dot(c, left, top, w, h, self.enemy_hero.x, self.enemy_hero.y, "#ffb0aa", 4)

    def draw_minimap_dot(self, c, left, top, w, h, x, y, color, r):
        mx = left + x / WIDTH * w
        my = top + y / HEIGHT * h
        c.create_oval(mx - r, my - r, mx + r, my + r, fill=color, outline="")

    def draw_shop(self, c):
        self.shop_cards = []
        left = WIDTH - 328
        top = HEIGHT - 236
        c.create_rectangle(left, top, WIDTH - 24, HEIGHT - 84, fill="#111719", outline="#d8cf9b", width=2)
        c.create_text(left + 18, top + 20, text=self.text("shop"), fill="#f5f1d7", anchor="w", font=("Segoe UI", 13, "bold"))
        for index, (item_key, item) in enumerate(ITEMS.items()):
            y1 = top + 42 + index * 48
            y2 = y1 + 38
            self.shop_cards.append((item_key, left + 14, y1, WIDTH - 38, y2))
            current_level = self.player.equipment[item_key]
            cost = item["cost"] + current_level * 70
            maxed = current_level >= item["max_stacks"]
            fill = "#20282b" if not maxed else "#181d1f"
            c.create_rectangle(left + 14, y1, WIDTH - 38, y2, fill=fill, outline=item["color"], width=2)
            c.create_rectangle(left + 26, y1 + 9, left + 46, y1 + 29, fill=item["color"], outline="")
            c.create_text(left + 58, y1 + 19, text=f"{index + 1}. {self.item_name(item_key)}", fill="#f5f1d7", anchor="w", font=("Segoe UI", 11, "bold"))
            c.create_text(WIDTH - 118, y1 + 19, text=f"Lv {current_level}/{item['max_stacks']}", fill="#cfd6cd", anchor="e", font=("Segoe UI", 10))
            price = "MAX" if maxed else f"G {cost}"
            c.create_text(WIDTH - 50, y1 + 19, text=price, fill="#f7d765", anchor="e", font=("Segoe UI", 10, "bold"))

    def draw_skill(self, c, x, y, label, ready_at, full_cd, size):
        current = self.now()
        ready = current >= ready_at
        fill = "#26313a" if ready else "#171b20"
        r = size // 2
        c.create_oval(x - r - 4, y - r - 4, x + r + 4, y + r + 4, fill="#0d1215", outline="#394043", width=2)
        c.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline="#d8cf9b", width=2)
        if not ready:
            left = ready_at - current
            pct = clamp(left / full_cd, 0, 1)
            c.create_arc(
                x - r,
                y - r,
                x + r,
                y + r,
                start=90,
                extent=-360 * pct,
                fill="#000000",
                outline="",
            )
        c.create_text(x, y, text=label, fill="#f5f1d7", font=("Segoe UI", 15, "bold"))
        if not ready:
            c.create_text(x, y + 25, text=f"{left:.1f}", fill="#ffffff", font=("Segoe UI", 8, "bold"))


if __name__ == "__main__":
    MobaGame().start()
