import math
import random
import time
import tkinter as tk
from game_data import (
    BRUSH_ZONES,
    Core,
    FPS_MS,
    HEROES,
    HEIGHT,
    Hero,
    JUNGLE_CAMPS,
    L10N,
    MODE_RULES,
    Minion,
    NeutralMonster,
    Tower,
    WIDTH,
    clamp,
    dist,
    norm,
)
from equipment_data import HERO_RECOMMENDED_ITEMS, ITEMS
from ai import AiMixin
from combat import CombatMixin
from input_handler import InputMixin
from rendering import RenderingMixin


class MobaGame(RenderingMixin, InputMixin, AiMixin, CombatMixin):
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
        self.wave_index = 0
        self.enemy_xp_timer = 0
        self.match_over = False
        self.winner = None
        self.message_until = 0
        self.message = ""
        self.recalling = False
        self.recall_elapsed = 0.0
        self.recall_duration = 3.0
        self.enemy_recalling = False
        self.enemy_recall_elapsed = 0.0
        self.summoner_cooldowns = {"f": 0, "g": 0}
        self.summoner_cd_durations = {"f": 12.0, "g": 18.0}
        self.aiming_skill = None
        self.show_scoreboard = False
        self.locked_target = None

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
        self.shop_cards = []
        self.utility_buttons = []
        self.recommended_buy_button = None
        self.skill_upgrade_buttons = []
        self.settlement_buttons = []
        self.loading_started_at = 0
        self.selected_mode_key = None
        self.selected_hero_key = None
        self.player = None
        self.enemy_hero = None
        self.blue_core = None
        self.red_core = None
        self.towers = []
        self.minions = []
        self.neutral_monsters = []
        self.projectiles = []
        self.effects = []
        self.damage_over_times = []
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

    def hero_skill_traits(self, hero_key):
        return L10N[self.language]["skill_traits"][hero_key]

    def item_name(self, item_key):
        return L10N[self.language]["items"][item_key]

    def lane_name(self, lane):
        return L10N[self.language]["lanes"][lane]

    def jungle_name(self, camp_key):
        return L10N[self.language]["jungle"][camp_key]

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
            equipment={key: 0 for key in ITEMS},
        )

    def reset_match(self, hero_key):
        self.selected_hero_key = hero_key
        rule = self.mode_rule()
        self.match_over = False
        self.winner = None
        self.spawn_timer = 0
        self.wave_index = 0
        self.match_time = 0
        self.message_until = 0
        self.message = ""
        self.recalling = False
        self.recall_elapsed = 0.0
        self.enemy_recalling = False
        self.enemy_recall_elapsed = 0.0
        self.summoner_cooldowns = {"f": 0, "g": 0}
        self.aiming_skill = None
        self.show_scoreboard = False
        self.locked_target = None
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
        self.neutral_monsters = self.make_neutral_monsters()
        self.projectiles = []
        self.effects = []
        self.damage_over_times = []
        self.particles = []
        self.beams = []
        self.float_texts = []
        self.banners = []
        self.shop_cards = []
        self.utility_buttons = []
        self.recommended_buy_button = None
        self.skill_upgrade_buttons = []
        self.settlement_buttons = []

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
            ("blue", "top", "base", 120, 330),
            ("blue", "top", "outer", 310, 148),
            ("red", "top", "outer", 810, 146),
            ("red", "top", "base", 970, 255),
            ("blue", "mid", "base", 280, 510),
            ("red", "mid", "base", 820, 190),
            ("blue", "bot", "base", 290, 565),
            ("blue", "bot", "outer", 540, 565),
            ("red", "bot", "outer", 885, 500),
            ("red", "bot", "base", 980, 335),
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
                tier=tier,
                name=f"{team.title()} {lane.title()} Tower",
            )
            for team, lane, tier, x, y in data
        ]

    def make_neutral_monsters(self):
        monsters = []
        for camp_key, config in JUNGLE_CAMPS.items():
            monsters.append(
                NeutralMonster(
                    x=config["x"],
                    y=config["y"],
                    team="neutral",
                    hp=config["hp"],
                    max_hp=config["hp"],
                    radius=config["radius"],
                    speed=0,
                    attack_damage=config["attack_damage"],
                    attack_range=128,
                    attack_cd=1.05,
                    camp_key=camp_key,
                    name=camp_key,
                    gold_reward=config["gold"],
                    xp_reward=config["xp"],
                    respawn_delay=config["respawn"],
                    color=config["color"],
                )
            )
        return monsters

    def start(self):
        self.loop()
        self.root.mainloop()

    def now(self):
        return time.perf_counter()

    def near_shop(self):
        return self.player.alive and dist(self.player, self.blue_core) <= 155

    def start_recall(self):
        if self.state != "playing" or not self.player.alive or self.recalling:
            return
        self.aiming_skill = None
        self.recalling = True
        self.recall_elapsed = 0.0
        text = self.text("recall_start")
        self.show_message(text)
        self.spawn_banner(text, "#d8cf9b", ttl=1.2)
        self.spawn_ring(self.player.x, self.player.y, "#d8cf9b", base_radius=72, ttl=0.36)
        self.spawn_particles(self.player.x, self.player.y, "#d8cf9b", count=14, speed=120, spread=1.0, radius=2.8, ttl=0.34)

    def cancel_recall(self, announce=True):
        if not self.recalling:
            return
        self.recalling = False
        self.recall_elapsed = 0.0
        if announce:
            text = self.text("recall_cancel")
            self.show_message(text)
            self.spawn_banner(text, "#ffb0aa", ttl=1.0)

    def complete_recall(self):
        if not self.recalling:
            return
        self.recalling = False
        self.recall_elapsed = 0.0
        self.player.x, self.player.y = 130, 580
        self.player.hp = self.player.max_hp
        text = self.text("recall_complete")
        self.show_message(text)
        self.spawn_banner(text, "#76f4d1", ttl=1.2)
        self.spawn_particles(self.player.x, self.player.y, "#76f4d1", count=18, speed=150, spread=1.0, radius=3.2, ttl=0.38)
        self.spawn_ring(self.player.x, self.player.y, "#76f4d1", base_radius=92, ttl=0.34)

    def start_enemy_recall(self):
        if not self.enemy_hero.alive or self.enemy_recalling:
            return
        self.enemy_recalling = True
        self.enemy_recall_elapsed = 0.0
        if self.hero_visible_to_player(self.enemy_hero):
            text = self.text("enemy_recall_start")
            self.show_message(text)
            self.spawn_banner(text, "#ffb0aa", ttl=1.0)
        self.spawn_ring(self.enemy_hero.x, self.enemy_hero.y, "#ffb0aa", base_radius=72, ttl=0.32)

    def cancel_enemy_recall(self, announce=True):
        if not self.enemy_recalling:
            return
        self.enemy_recalling = False
        self.enemy_recall_elapsed = 0.0
        if announce and self.hero_visible_to_player(self.enemy_hero):
            text = self.text("enemy_recall_cancel")
            self.show_message(text)

    def complete_enemy_recall(self):
        if not self.enemy_recalling:
            return
        self.enemy_recalling = False
        self.enemy_recall_elapsed = 0.0
        self.enemy_hero.x, self.enemy_hero.y = 965, 120
        self.enemy_hero.hp = self.enemy_hero.max_hp
        self.enemy_hero.shield = 0
        self.enemy_hero.stunned_until = 0
        self.enemy_hero.slowed_until = 0
        self.enemy_hero.slow_mult = 1.0
        if self.hero_visible_to_player(self.enemy_hero):
            text = self.text("enemy_recall_complete")
            self.show_message(text)
        self.spawn_particles(self.enemy_hero.x, self.enemy_hero.y, "#ffb0aa", count=18, speed=150, spread=1.0, radius=3.2, ttl=0.38)
        self.spawn_ring(self.enemy_hero.x, self.enemy_hero.y, "#ffb0aa", base_radius=92, ttl=0.34)

    def summoner_ready(self, key):
        return self.now() >= self.summoner_cooldowns[key]

    def cast_flash(self):
        if self.state != "playing" or not self.player.alive or not self.summoner_ready("f"):
            return
        self.summoner_cooldowns["f"] = self.now() + self.summoner_cd_durations["f"]
        old_x, old_y = self.player.x, self.player.y
        vx, vy = self.aim_vector(self.player)
        distance = 170
        self.player.x = clamp(self.player.x + vx * distance, 35, WIDTH - 35)
        self.player.y = clamp(self.player.y + vy * distance, 35, HEIGHT - 35)
        self.spawn_beam(old_x, old_y, self.player.x, self.player.y, "#f5f1d7", width=7, ttl=0.18)
        self.spawn_particles(old_x, old_y, "#f5f1d7", count=14, speed=130, spread=1.0, radius=2.8, ttl=0.32)
        self.spawn_particles(self.player.x, self.player.y, "#f5f1d7", count=18, speed=150, spread=1.15, radius=3.0, ttl=0.36)
        self.spawn_ring(self.player.x, self.player.y, "#f5f1d7", base_radius=54, ttl=0.24)
        self.show_message(self.text("flash"))

    def cast_heal(self):
        if self.state != "playing" or not self.player.alive or not self.summoner_ready("g"):
            return
        self.summoner_cooldowns["g"] = self.now() + self.summoner_cd_durations["g"]
        amount = self.player.max_hp * 0.32
        self.player.hp = min(self.player.max_hp, self.player.hp + amount)
        self.spawn_particles(self.player.x, self.player.y, "#48d06b", count=22, speed=135, spread=1.05, radius=3.0, ttl=0.42)
        self.spawn_ring(self.player.x, self.player.y, "#48d06b", base_radius=76, ttl=0.34)
        self.spawn_floating_text(self.player.x, self.player.y - 24, f"+{int(amount)}", "#48d06b", ttl=0.75)
        self.show_message(self.text("heal"))

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
        missing_item = self.missing_item_requirement(self.player, item)
        if missing_item:
            self.show_message(self.text("need_component", item=self.item_name(missing_item)))
            return False
        cost = item["cost"] + current_level * 70
        if self.player.gold < cost:
            self.show_message(self.text("not_enough_gold"))
            return False

        self.player.gold -= cost
        self.player.equipment[item_key] += 1
        if "attack_damage" in item:
            self.player.attack_damage += item["attack_damage"]
        if "skill_power" in item:
            self.player.skill_power += item["skill_power"]
        if "speed" in item:
            self.player.speed += item["speed"]
        if "attack_range" in item:
            self.player.attack_range += item["attack_range"]
        if "attack_cd_reduce" in item:
            self.player.attack_cd = max(0.2, self.player.attack_cd - item["attack_cd_reduce"])
        if "max_hp" in item:
            self.player.max_hp += item["max_hp"]
            self.player.hp += item["max_hp"]
        self.show_message(self.text("bought", item=self.item_name(item_key)))
        return True

    def missing_item_requirement(self, hero, item):
        for required_key, required_level in item.get("requires", {}).items():
            if hero.equipment.get(required_key, 0) < required_level:
                return required_key
        return None

    def buy_recommended_item(self):
        recommended = HERO_RECOMMENDED_ITEMS.get(self.player.hero_key, [])
        for item_key in recommended:
            item = ITEMS[item_key]
            if self.player.equipment.get(item_key, 0) >= item["max_stacks"]:
                continue
            missing_item = self.missing_item_requirement(self.player, item)
            candidate = missing_item or item_key
            if self.player.equipment.get(candidate, 0) >= ITEMS[candidate]["max_stacks"]:
                continue
            self.buy_item(candidate)
            return True
        self.show_message(self.text("no_recommended"))
        return True

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
        self.update_neutral_monsters()
        self.update_minions(dt)
        self.update_towers()
        self.update_cores()
        self.update_projectiles(dt)
        self.update_damage_over_time(dt)
        self.update_effects(dt)
        self.cleanup_dead()
        self.check_winner()

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

    def show_message(self, text):
        self.message = text
        self.message_until = self.now() + 2.2

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

if __name__ == "__main__":
    MobaGame().start()
