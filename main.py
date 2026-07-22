import math
import random
import time
import tkinter as tk
from dataclasses import dataclass, field


WIDTH = 1100
HEIGHT = 700
FPS_MS = 16


def clamp(value, low, high):
    return max(low, min(high, value))


def dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def dist_xy(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def norm(dx, dy):
    length = math.hypot(dx, dy)
    if length <= 0.0001:
        return 0, 0
    return dx / length, dy / length


def team_color(team):
    return "#3f7cff" if team == "blue" else "#e84d4f"


@dataclass
class Unit:
    x: float
    y: float
    team: str
    hp: float
    max_hp: float
    radius: float
    speed: float = 0
    attack_damage: float = 0
    attack_range: float = 0
    attack_cd: float = 0
    next_attack: float = 0
    alive: bool = True

    def take_damage(self, amount):
        if not self.alive:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False


@dataclass
class Hero(Unit):
    name: str = "Hero"
    level: int = 1
    gold: int = 0
    kills: int = 0
    respawn_at: float = 0
    cooldowns: dict = field(default_factory=lambda: {"q": 0, "e": 0, "r": 0})


@dataclass
class Minion(Unit):
    lane: str = "mid"
    waypoint: int = 1


@dataclass
class Tower(Unit):
    lane: str = "mid"
    name: str = "Tower"


@dataclass
class Core(Unit):
    name: str = "Core"


@dataclass
class Projectile:
    x: float
    y: float
    team: str
    damage: float
    speed: float
    target: object | None = None
    vx: float = 0
    vy: float = 0
    radius: float = 5
    pierce: bool = False
    ttl: float = 2
    color: str = "#ffffff"


@dataclass
class Effect:
    x: float
    y: float
    radius: float
    max_radius: float
    color: str
    ttl: float
    max_ttl: float


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
        self.match_over = False
        self.winner = None
        self.message_until = 0
        self.message = ""

        self.paths = {
            "top": [(92, 608), (96, 150), (910, 146), (1010, 92)],
            "mid": [(92, 608), (550, 350), (1010, 92)],
            "bot": [(92, 608), (250, 565), (920, 565), (1010, 92)],
        }

        self.player = Hero(
            x=130,
            y=580,
            team="blue",
            hp=560,
            max_hp=560,
            radius=18,
            speed=190,
            attack_damage=32,
            attack_range=235,
            attack_cd=0.42,
            name="Vanguard",
        )
        self.enemy_hero = Hero(
            x=965,
            y=120,
            team="red",
            hp=520,
            max_hp=520,
            radius=18,
            speed=165,
            attack_damage=29,
            attack_range=225,
            attack_cd=0.55,
            name="Warlord",
        )

        self.blue_core = Core(74, 626, "blue", 1200, 1200, 35, name="Blue Core")
        self.red_core = Core(1026, 74, "red", 1200, 1200, 35, name="Red Core")
        self.towers = self.make_towers()
        self.minions = []
        self.projectiles = []
        self.effects = []

        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.root.bind("<Motion>", self.on_mouse_move)
        self.root.bind("<Button-1>", self.on_left_click)
        self.root.bind("<Button-3>", self.on_right_click)
        self.root.focus_force()

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
                hp=440,
                max_hp=440,
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
        self.keys.add(key)
        if key == "q":
            self.cast_q(self.player)
        elif key == "e":
            self.cast_e(self.player)
        elif key == "r":
            self.cast_r(self.player)
        elif key == "space":
            self.on_left_click(event)
        elif key == "escape":
            self.root.destroy()

    def on_key_release(self, event):
        self.keys.discard(event.keysym.lower())

    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def on_left_click(self, _event):
        self.hero_attack(self.player)

    def on_right_click(self, _event):
        self.cast_e(self.player)

    def loop(self):
        current = time.perf_counter()
        dt = min(0.05, current - self.last_time)
        self.last_time = current
        if not self.match_over:
            self.update(dt)
        self.draw()
        self.root.after(FPS_MS, self.loop)

    def update(self, dt):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_wave()
            self.spawn_timer = 7.0

        self.update_player(dt)
        self.update_enemy_hero(dt)
        self.update_minions(dt)
        self.update_towers()
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
                    self.effects.append(Effect(p.x, p.y, 4, 28, p.color, 0.22, 0.22))
                    continue
            else:
                p.x += p.vx * p.speed * dt
                p.y += p.vy * p.speed * dt
                hit = False
                for target in self.enemies_of(p.team, include_cores=False):
                    if target.alive and dist_xy(p.x, p.y, target.x, target.y) <= p.radius + target.radius:
                        self.apply_damage(target, p.damage, p.team)
                        self.effects.append(Effect(p.x, p.y, 6, 34, p.color, 0.24, 0.24))
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

    def cleanup_dead(self):
        before = len(self.minions)
        self.minions = [m for m in self.minions if m.alive]
        gained = before - len(self.minions)
        if gained:
            self.player.gold += gained * 4

        for hero in [self.player, self.enemy_hero]:
            if not hero.alive and hero.respawn_at == 0:
                hero.respawn_at = self.now() + 5
                killer = self.enemy_hero if hero.team == "blue" else self.player
                killer.kills += 1
                killer.gold += 80
                self.show_message(f"{killer.name} defeated {hero.name}")

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
        self.projectiles.append(
            Projectile(
                unit.x,
                unit.y,
                unit.team,
                unit.attack_damage,
                330 if isinstance(unit, Tower) else 250,
                target=target,
                radius=6 if isinstance(unit, Tower) else 4,
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

    def cast_q(self, hero):
        current = self.now()
        if not hero.alive or current < hero.cooldowns["q"]:
            return
        hero.cooldowns["q"] = current + 3.6
        vx, vy = norm(self.mouse_x - hero.x, self.mouse_y - hero.y)
        if vx == 0 and vy == 0:
            vx = 1
        self.projectiles.append(
            Projectile(
                hero.x,
                hero.y,
                hero.team,
                76,
                420,
                vx=vx,
                vy=vy,
                radius=11,
                pierce=True,
                ttl=0.95,
                color="#76f4d1",
            )
        )

    def cast_e(self, hero):
        current = self.now()
        if not hero.alive or current < hero.cooldowns["e"]:
            return
        hero.cooldowns["e"] = current + 5.5
        vx, vy = norm(self.mouse_x - hero.x, self.mouse_y - hero.y)
        hero.x = clamp(hero.x + vx * 115, 35, WIDTH - 35)
        hero.y = clamp(hero.y + vy * 115, 35, HEIGHT - 35)
        self.effects.append(Effect(hero.x, hero.y, 8, 45, "#ffe082", 0.28, 0.28))

    def cast_r(self, hero):
        current = self.now()
        if not hero.alive or current < hero.cooldowns["r"]:
            return
        if dist_xy(hero.x, hero.y, self.mouse_x, self.mouse_y) > 340:
            return
        hero.cooldowns["r"] = current + 13.5
        self.effects.append(Effect(self.mouse_x, self.mouse_y, 10, 105, "#b38cff", 0.45, 0.45))
        for target in self.enemies_of(hero.team, include_cores=False):
            if target.alive and dist_xy(self.mouse_x, self.mouse_y, target.x, target.y) < 95:
                self.apply_damage(target, 138, hero.team)

    def cast_ai_bolt(self, hero, target):
        hero.cooldowns["q"] = self.now() + 4.2
        vx, vy = norm(target.x - hero.x, target.y - hero.y)
        self.projectiles.append(
            Projectile(
                hero.x,
                hero.y,
                hero.team,
                64,
                385,
                vx=vx,
                vy=vy,
                radius=10,
                pierce=True,
                ttl=0.9,
                color="#ff6c7a",
            )
        )

    def apply_damage(self, target, amount, attacker_team):
        was_alive = target.alive
        target.take_damage(amount)
        if was_alive and not target.alive:
            if isinstance(target, Tower):
                self.show_message(f"{target.name} destroyed")
                if attacker_team == "blue":
                    self.player.gold += 90
            elif isinstance(target, Core):
                self.show_message(f"{target.name} destroyed")

    def draw(self):
        c = self.canvas
        c.delete("all")
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
        self.draw_ui(c)

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
            random.seed(_)
            x = random.randint(40, WIDTH - 40)
            y = random.randint(45, HEIGHT - 45)
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
        c.create_polygon(*pts, fill=color, outline="#f8f2da", width=2)
        c.create_oval(hero.x - 10, hero.y - 10, hero.x + 10, hero.y + 10, fill="#1a2024", outline="")
        self.draw_bar(c, hero.x - 32, hero.y - 36, 64, hero.hp, hero.max_hp, "#48d06b")

    def draw_ui(self, c):
        c.create_rectangle(0, 0, WIDTH, 46, fill="#111719", outline="")
        c.create_text(24, 23, text="BLUE", fill="#78a3ff", anchor="w", font=("Segoe UI", 13, "bold"))
        c.create_text(120, 23, text=f"K {self.player.kills}", fill="#f5f1d7", anchor="w", font=("Segoe UI", 13))
        c.create_text(190, 23, text=f"G {self.player.gold}", fill="#f7d765", anchor="w", font=("Segoe UI", 13))
        c.create_text(WIDTH - 24, 23, text="RED", fill="#ff7b7c", anchor="e", font=("Segoe UI", 13, "bold"))
        c.create_text(WIDTH - 120, 23, text=f"K {self.enemy_hero.kills}", fill="#f5f1d7", anchor="e", font=("Segoe UI", 13))

        self.draw_skill(c, WIDTH // 2 - 102, HEIGHT - 58, "Q", self.player.cooldowns["q"], 3.6)
        self.draw_skill(c, WIDTH // 2 - 34, HEIGHT - 58, "E", self.player.cooldowns["e"], 5.5)
        self.draw_skill(c, WIDTH // 2 + 34, HEIGHT - 58, "R", self.player.cooldowns["r"], 13.5)
        self.draw_skill(c, WIDTH // 2 + 102, HEIGHT - 58, "A", self.player.next_attack, self.player.attack_cd)

        if self.now() < self.message_until:
            c.create_text(WIDTH // 2, 78, text=self.message, fill="#f5f1d7", font=("Segoe UI", 18, "bold"))

        if self.match_over:
            overlay = "#17291f" if self.winner == "blue" else "#35191d"
            c.create_rectangle(300, 248, 800, 452, fill=overlay, outline="#f5f1d7", width=2)
            text = "BLUE VICTORY" if self.winner == "blue" else "RED VICTORY"
            c.create_text(WIDTH // 2, 326, text=text, fill="#f5f1d7", font=("Segoe UI", 34, "bold"))
            c.create_text(WIDTH // 2, 382, text="Close the window to exit", fill="#cfc8ac", font=("Segoe UI", 14))

    def draw_skill(self, c, x, y, label, ready_at, full_cd):
        size = 44
        current = self.now()
        ready = current >= ready_at
        fill = "#26313a" if ready else "#171b20"
        c.create_rectangle(x - size // 2, y - size // 2, x + size // 2, y + size // 2, fill=fill, outline="#d8cf9b", width=2)
        c.create_text(x, y, text=label, fill="#f5f1d7", font=("Segoe UI", 15, "bold"))
        if not ready:
            left = ready_at - current
            pct = clamp(left / full_cd, 0, 1)
            c.create_rectangle(
                x - size // 2,
                y + size // 2 - size * pct,
                x + size // 2,
                y + size // 2,
                fill="#000000",
                stipple="gray50",
                outline="",
            )
            c.create_text(x, y + 25, text=f"{left:.1f}", fill="#ffffff", font=("Segoe UI", 8, "bold"))


if __name__ == "__main__":
    MobaGame().start()
