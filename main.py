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


HEROES = {
    "vanguard": {
        "name": "Vanguard",
        "role": "Fighter",
        "accent": "#ffe082",
        "hp": 620,
        "speed": 188,
        "attack_damage": 34,
        "attack_range": 225,
        "attack_cd": 0.44,
        "cooldowns": {"q": 3.6, "e": 5.5, "r": 13.5},
        "skills": {"q": "Spear Line", "e": "Shield Rush", "r": "Earth Break"},
    },
    "ranger": {
        "name": "Star Ranger",
        "role": "Marksman",
        "accent": "#76f4d1",
        "hp": 470,
        "speed": 218,
        "attack_damage": 25,
        "attack_range": 285,
        "attack_cd": 0.30,
        "cooldowns": {"q": 2.8, "e": 4.8, "r": 11.0},
        "skills": {"q": "Triple Shot", "e": "Quick Step", "r": "Arrow Storm"},
    },
    "arcanist": {
        "name": "Storm Arcanist",
        "role": "Mage",
        "accent": "#b38cff",
        "hp": 440,
        "speed": 174,
        "attack_damage": 23,
        "attack_range": 260,
        "attack_cd": 0.52,
        "cooldowns": {"q": 3.2, "e": 6.2, "r": 14.0},
        "skills": {"q": "Storm Orb", "e": "Arc Shield", "r": "Thunder Field"},
    },
}


ITEMS = {
    "blade": {"cost": 120, "attack_damage": 8, "max_stacks": 3, "color": "#f7d765"},
    "boots": {"cost": 100, "speed": 18, "max_stacks": 3, "color": "#76b7ff"},
    "guard": {"cost": 150, "max_hp": 110, "max_stacks": 3, "color": "#48d06b"},
}


L10N = {
    "en": {
        "language_title": "CHOOSE LANGUAGE",
        "language_subtitle": "Python MOBA Prototype",
        "hero_title": "SELECT HERO",
        "choose_hero": "CHOOSE YOUR HERO",
        "blue": "BLUE",
        "red": "RED",
        "victory_blue": "BLUE VICTORY",
        "victory_red": "RED VICTORY",
        "exit": "Close the window to exit",
        "deployed": "{name} deployed",
        "defeated": "{killer} defeated {victim}",
        "destroyed": "{name} destroyed",
        "level_up": "{name} reached Lv.{level}",
        "need_base": "Return to base to buy equipment",
        "not_enough_gold": "Not enough gold",
        "item_max": "Equipment is maxed",
        "bought": "Bought {item}",
        "shop": "SHOP",
        "level": "LV",
        "enemy_prefix": "Enemy {name}",
        "hero_names": {
            "vanguard": "Vanguard",
            "ranger": "Star Ranger",
            "arcanist": "Storm Arcanist",
        },
        "hero_roles": {
            "vanguard": "Fighter",
            "ranger": "Marksman",
            "arcanist": "Mage",
        },
        "skills": {
            "vanguard": {"q": "Spear Line", "e": "Shield Rush", "r": "Earth Break"},
            "ranger": {"q": "Triple Shot", "e": "Quick Step", "r": "Arrow Storm"},
            "arcanist": {"q": "Storm Orb", "e": "Arc Shield", "r": "Thunder Field"},
        },
        "items": {
            "blade": "Blade",
            "boots": "Boots",
            "guard": "Guard",
        },
    },
    "zh": {
        "language_title": "选择语言",
        "language_subtitle": "Python 王者类 MOBA 原型",
        "hero_title": "选择英雄",
        "choose_hero": "选择你的英雄",
        "blue": "蓝方",
        "red": "红方",
        "victory_blue": "蓝方胜利",
        "victory_red": "红方胜利",
        "exit": "关闭窗口退出",
        "deployed": "{name} 已出战",
        "defeated": "{killer} 击败了 {victim}",
        "destroyed": "{name} 被摧毁",
        "level_up": "{name} 升到 {level} 级",
        "need_base": "回到己方水晶附近才能购买",
        "not_enough_gold": "金币不足",
        "item_max": "装备已满级",
        "bought": "已购买 {item}",
        "shop": "商店",
        "level": "等级",
        "enemy_prefix": "敌方{name}",
        "hero_names": {
            "vanguard": "铁卫",
            "ranger": "星弓",
            "arcanist": "雷法",
        },
        "hero_roles": {
            "vanguard": "战士",
            "ranger": "射手",
            "arcanist": "法师",
        },
        "skills": {
            "vanguard": {"q": "破阵矛", "e": "铁壁冲锋", "r": "裂地击"},
            "ranger": {"q": "三连矢", "e": "疾步", "r": "箭雨"},
            "arcanist": {"q": "雷光法球", "e": "奥术护盾", "r": "雷暴领域"},
        },
        "items": {
            "blade": "破军刃",
            "boots": "疾行靴",
            "guard": "守护甲",
        },
    },
}


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
    hero_key: str = "vanguard"
    role: str = "Fighter"
    accent: str = "#ffe082"
    skill_cds: dict = field(default_factory=lambda: {"q": 3.6, "e": 5.5, "r": 13.5})
    skill_names: dict = field(default_factory=lambda: {"q": "Spear Line", "e": "Shield Rush", "r": "Earth Break"})
    level: int = 1
    xp: int = 0
    next_xp: int = 120
    gold: int = 0
    kills: int = 0
    equipment: dict = field(default_factory=lambda: {"blade": 0, "boots": 0, "guard": 0})
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
            "top": [(92, 608), (96, 150), (910, 146), (1002, 112)],
            "mid": [(92, 608), (550, 350), (1002, 112)],
            "bot": [(92, 608), (250, 565), (920, 565), (1002, 112)],
        }

        self.language = "zh"
        self.state = "language"
        self.language_buttons = []
        self.hero_cards = []
        self.selected_hero_key = "vanguard"
        self.reset_match(self.selected_hero_key)

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
        self.match_over = False
        self.winner = None
        self.spawn_timer = 0
        self.match_time = 0
        self.message_until = 0
        self.message = ""
        self.player = self.make_hero(hero_key, "blue", 130, 580)
        self.enemy_hero = self.make_hero("vanguard", "red", 965, 120)
        self.enemy_hero.name = "Red Vanguard"
        self.blue_core = Core(
            74,
            626,
            "blue",
            1000,
            1000,
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
            1000,
            1000,
            35,
            attack_damage=70,
            attack_range=210,
            attack_cd=0.85,
            name="Red Core",
        )
        self.towers = self.make_towers()
        self.minions = []
        self.projectiles = []
        self.effects = []
        self.shop_cards = []

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
        self.state = "select"

    def choose_hero(self, hero_key):
        self.reset_match(hero_key)
        self.state = "playing"
        self.last_time = time.perf_counter()
        self.show_message(self.text("deployed", name=self.hero_name(hero_key)))

    def select_language_at(self, x, y):
        for language, left, top, right, bottom in self.language_buttons:
            if left <= x <= right and top <= y <= bottom:
                self.choose_language(language)
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
        if self.state == "playing" and not self.match_over:
            self.update(dt)
        self.draw()
        self.root.after(FPS_MS, self.loop)

    def update(self, dt):
        self.match_time += dt
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_wave()
            self.spawn_timer = 7.0

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
                    self.effects.append(Effect(p.x, p.y, 4, 28, p.color, 0.22, 0.22))
                    continue
            else:
                p.x += p.vx * p.speed * dt
                p.y += p.vy * p.speed * dt
                hit = False
                for target in self.enemies_of(p.team, include_cores=True):
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
        self.minions = [m for m in self.minions if m.alive]

        for hero in [self.player, self.enemy_hero]:
            if not hero.alive and hero.respawn_at == 0:
                hero.respawn_at = self.now() + 5
                killer = self.enemy_hero if hero.team == "blue" else self.player
                killer.kills += 1
                killer.gold += 80
                self.show_message(
                    self.text(
                        "defeated",
                        killer=self.hero_name(killer.hero_key),
                        victim=self.hero_name(hero.hero_key),
                    )
                )

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

    def cast_q(self, hero):
        if not self.skill_ready(hero, "q"):
            return
        vx, vy = self.aim_vector(hero)
        if hero.hero_key == "ranger":
            angle = math.atan2(vy, vx)
            for offset in (-0.18, 0, 0.18):
                ax = math.cos(angle + offset)
                ay = math.sin(angle + offset)
                self.projectiles.append(
                    Projectile(
                        hero.x,
                        hero.y,
                        hero.team,
                        46,
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
            self.projectiles.append(
                Projectile(
                    hero.x,
                    hero.y,
                    hero.team,
                    96,
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
            Projectile(hero.x, hero.y, hero.team, 82, 430, vx=vx, vy=vy, radius=11, pierce=True, ttl=0.95, color=hero.accent)
        )

    def cast_e(self, hero):
        if not self.skill_ready(hero, "e"):
            return
        vx, vy = self.aim_vector(hero)
        if hero.hero_key == "arcanist":
            hero.hp = min(hero.max_hp, hero.hp + 95)
            self.damage_area(hero.team, hero.x, hero.y, 82, 54)
            self.effects.append(Effect(hero.x, hero.y, 12, 88, hero.accent, 0.34, 0.34))
            return

        distance = 168 if hero.hero_key == "ranger" else 120
        hero.x = clamp(hero.x + vx * distance, 35, WIDTH - 35)
        hero.y = clamp(hero.y + vy * distance, 35, HEIGHT - 35)
        if hero.hero_key == "ranger":
            hero.next_attack = 0
            self.effects.append(Effect(hero.x, hero.y, 8, 42, hero.accent, 0.22, 0.22))
        else:
            self.damage_area(hero.team, hero.x, hero.y, 52, 42)
            self.effects.append(Effect(hero.x, hero.y, 8, 48, hero.accent, 0.28, 0.28))

    def cast_r(self, hero):
        if not hero.alive:
            return
        if dist_xy(hero.x, hero.y, self.mouse_x, self.mouse_y) > 340:
            return
        if not self.skill_ready(hero, "r"):
            return

        if hero.hero_key == "ranger":
            vx, vy = self.aim_vector(hero)
            angle = math.atan2(vy, vx)
            for offset in (-0.52, -0.39, -0.26, -0.13, 0, 0.13, 0.26, 0.39, 0.52):
                self.projectiles.append(
                    Projectile(
                        hero.x,
                        hero.y,
                        hero.team,
                        42,
                        500,
                        vx=math.cos(angle + offset),
                        vy=math.sin(angle + offset),
                        radius=8,
                        pierce=True,
                        ttl=1.05,
                        color=hero.accent,
                    )
                )
            self.effects.append(Effect(hero.x, hero.y, 10, 76, hero.accent, 0.28, 0.28))
            return

        if hero.hero_key == "arcanist":
            self.effects.append(Effect(self.mouse_x, self.mouse_y, 14, 130, hero.accent, 0.55, 0.55))
            self.damage_area(hero.team, self.mouse_x, self.mouse_y, 120, 176, include_cores=True)
            return

        self.effects.append(Effect(self.mouse_x, self.mouse_y, 10, 106, hero.accent, 0.45, 0.45))
        self.damage_area(hero.team, self.mouse_x, self.mouse_y, 96, 148, include_cores=True)

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

    def reward_player(self, target):
        if isinstance(target, Minion):
            self.player.gold += 8
            self.gain_xp(28)
        elif isinstance(target, Tower):
            self.player.gold += 120
            self.gain_xp(90)
        elif isinstance(target, Hero):
            self.player.gold += 120
            self.gain_xp(120)

    def gain_xp(self, amount):
        hero = self.player
        hero.xp += amount
        while hero.xp >= hero.next_xp:
            hero.xp -= hero.next_xp
            hero.level += 1
            hero.next_xp = int(hero.next_xp * 1.32)
            hero.max_hp += 48
            hero.hp = min(hero.max_hp, hero.hp + 48)
            hero.attack_damage += 4
            hero.attack_range += 3
            self.show_message(self.text("level_up", name=self.hero_name(hero.hero_key), level=hero.level))

    def apply_damage(self, target, amount, attacker_team):
        if isinstance(target, (Tower, Core)):
            amount *= 1.35 if attacker_team == "blue" else 1.15
        was_alive = target.alive
        target.take_damage(amount)
        if was_alive and not target.alive:
            if attacker_team == "blue" and target.team == "red":
                self.reward_player(target)
            if isinstance(target, Tower):
                self.show_message(self.text("destroyed", name=target.name))
            elif isinstance(target, Core):
                self.show_message(self.text("destroyed", name=target.name))

    def draw(self):
        c = self.canvas
        c.delete("all")
        if self.state == "language":
            self.draw_language(c)
            return
        if self.state == "select":
            self.draw_select(c)
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
        card_w = 286
        card_h = 390
        gap = 34
        start_x = (WIDTH - card_w * 3 - gap * 2) // 2
        top = 148
        for index, (hero_key, config) in enumerate(HEROES.items()):
            left = start_x + index * (card_w + gap)
            right = left + card_w
            bottom = top + card_h
            self.hero_cards.append((hero_key, left, top, right, bottom))
            active = left <= self.mouse_x <= right and top <= self.mouse_y <= bottom
            outline = config["accent"] if active else "#394043"
            c.create_rectangle(left, top, right, bottom, fill="#20282b", outline=outline, width=3)
            c.create_rectangle(left, top, right, top + 76, fill="#161c1f", outline="")
            c.create_text(left + 24, top + 26, text=self.hero_name(hero_key), fill="#f5f1d7", anchor="w", font=("Segoe UI", 18, "bold"))
            c.create_text(left + 24, top + 54, text=self.hero_role(hero_key), fill=config["accent"], anchor="w", font=("Segoe UI", 12, "bold"))
            self.draw_hero_portrait(c, left + card_w // 2, top + 137, config)

            stat_y = top + 215
            self.draw_stat(c, left + 26, stat_y, "HP", config["hp"], 700, "#48d06b")
            self.draw_stat(c, left + 26, stat_y + 38, "SPD", config["speed"], 240, "#76b7ff")
            self.draw_stat(c, left + 26, stat_y + 76, "ATK", config["attack_damage"], 42, "#f7d765")
            c.create_text(left + 26, top + 336, text="Q", fill="#f5f1d7", anchor="w", font=("Segoe UI", 11, "bold"))
            c.create_text(left + 54, top + 336, text=self.hero_skill(hero_key, "q"), fill="#cfd6cd", anchor="w", font=("Segoe UI", 11))
            c.create_text(left + 26, top + 362, text="E", fill="#f5f1d7", anchor="w", font=("Segoe UI", 11, "bold"))
            c.create_text(left + 54, top + 362, text=self.hero_skill(hero_key, "e"), fill="#cfd6cd", anchor="w", font=("Segoe UI", 11))
            c.create_text(left + 26, top + 388, text="R", fill="#f5f1d7", anchor="w", font=("Segoe UI", 11, "bold"))
            c.create_text(left + 54, top + 388, text=self.hero_skill(hero_key, "r"), fill="#cfd6cd", anchor="w", font=("Segoe UI", 11))

        c.create_rectangle(358, 590, 742, 636, fill="#101416", outline="#394043")
        c.create_text(WIDTH // 2, 613, text=self.text("choose_hero"), fill="#d8cf9b", font=("Segoe UI", 13, "bold"))

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
            random.seed(100 + i)
            x = random.randint(80, WIDTH - 80)
            y = random.randint(130, HEIGHT - 80)
            c.create_rectangle(x - 18, y - 2, x + 18, y + 2, fill="#2d3939", outline="")

    def draw_hero_portrait(self, c, x, y, config):
        accent = config["accent"]
        c.create_oval(x - 54, y - 54, x + 54, y + 54, fill="#14191c", outline=accent, width=4)
        c.create_polygon(x, y - 48, x - 45, y + 38, x + 45, y + 38, fill=accent, outline="#f5f1d7", width=2)
        c.create_oval(x - 24, y - 20, x + 24, y + 28, fill="#1f282c", outline="")
        c.create_line(x - 62, y + 68, x + 62, y + 68, fill=accent, width=3)

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
