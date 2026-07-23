import math
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
    "sentinel": {
        "name": "Iron Sentinel",
        "role": "Tank",
        "accent": "#8fd3ff",
        "hp": 720,
        "speed": 164,
        "attack_damage": 30,
        "attack_range": 205,
        "attack_cd": 0.52,
        "cooldowns": {"q": 4.0, "e": 7.0, "r": 15.0},
        "skills": {"q": "Anchor Wave", "e": "Fortify", "r": "Guardian Slam"},
    },
    "shade": {
        "name": "Night Shade",
        "role": "Assassin",
        "accent": "#ff7bd1",
        "hp": 430,
        "speed": 232,
        "attack_damage": 38,
        "attack_range": 190,
        "attack_cd": 0.36,
        "cooldowns": {"q": 2.6, "e": 5.0, "r": 12.0},
        "skills": {"q": "Shadow Cut", "e": "Blink Strike", "r": "Void Execution"},
    },
}


ITEMS = {
    "blade": {"cost": 120, "attack_damage": 8, "max_stacks": 3, "color": "#f7d765"},
    "boots": {"cost": 100, "speed": 18, "max_stacks": 3, "color": "#76b7ff"},
    "guard": {"cost": 150, "max_hp": 110, "max_stacks": 3, "color": "#48d06b"},
}


MODE_RULES = {
    "rank": {
        "spawn_interval": 7.0,
        "gold_mult": 1.0,
        "xp_mult": 1.0,
        "enemy_xp_rate": 10,
        "tower_hp_mult": 1.0,
        "core_hp_mult": 1.0,
        "enemy_stat_mult": 1.0,
        "start_level": 1,
        "start_gold": 0,
    },
    "train": {
        "spawn_interval": 8.0,
        "gold_mult": 1.35,
        "xp_mult": 1.25,
        "enemy_xp_rate": 6,
        "tower_hp_mult": 0.85,
        "core_hp_mult": 0.85,
        "enemy_stat_mult": 0.82,
        "start_level": 2,
        "start_gold": 220,
    },
    "quick": {
        "spawn_interval": 4.4,
        "gold_mult": 1.75,
        "xp_mult": 1.8,
        "enemy_xp_rate": 18,
        "tower_hp_mult": 0.72,
        "core_hp_mult": 0.72,
        "enemy_stat_mult": 1.08,
        "start_level": 3,
        "start_gold": 260,
    },
}


L10N = {
    "en": {
        "language_title": "CHOOSE LANGUAGE",
        "language_subtitle": "Python MOBA Prototype",
        "lobby_title": "AETHER ARENA",
        "lobby_subtitle": "Original MOBA Prototype",
        "start_match": "START MATCH",
        "mode_rank": "Crystal Valley",
        "mode_train": "Practice Grounds",
        "mode_quick": "Quick Duel",
        "mode_desc": {
            "rank": "Standard pace, balanced towers and AI.",
            "train": "Easier AI, starting gold and slower waves.",
            "quick": "Fast waves, faster growth and weaker structures.",
        },
        "mode_prompt": "Choose a mode before selecting a hero",
        "hero_unselected": "Hero not selected",
        "mode_unselected": "Mode not selected",
        "flash": "Flash",
        "heal": "Heal",
        "season": "Season Trial",
        "profile": "Commander",
        "loading": "LOADING",
        "versus": "VERSUS",
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
        "level_up": "{name} reached Lv.{level}: HP +48, ATK +4, skills stronger",
        "need_base": "Return to base to buy equipment",
        "recall_start": "Recalling...",
        "recall_cancel": "Recall interrupted",
        "recall_complete": "Returned to base",
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
            "sentinel": "Iron Sentinel",
            "shade": "Night Shade",
        },
        "hero_roles": {
            "vanguard": "Fighter",
            "ranger": "Marksman",
            "arcanist": "Mage",
            "sentinel": "Tank",
            "shade": "Assassin",
        },
        "skills": {
            "vanguard": {"q": "Spear Line", "e": "Shield Rush", "r": "Earth Break"},
            "ranger": {"q": "Triple Shot", "e": "Quick Step", "r": "Arrow Storm"},
            "arcanist": {"q": "Storm Orb", "e": "Arc Shield", "r": "Thunder Field"},
            "sentinel": {"q": "Anchor Wave", "e": "Fortify", "r": "Guardian Slam"},
            "shade": {"q": "Shadow Cut", "e": "Blink Strike", "r": "Void Execution"},
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
        "lobby_title": "星辉峡谷",
        "lobby_subtitle": "原创王者类 MOBA 原型",
        "start_match": "开始对战",
        "mode_rank": "水晶峡谷",
        "mode_train": "训练营",
        "mode_quick": "快速对决",
        "mode_desc": {
            "rank": "标准节奏，防御塔和 AI 强度均衡。",
            "train": "AI 更弱，开局金币更多，兵线更慢。",
            "quick": "兵线更快，成长更快，建筑更脆。",
        },
        "mode_prompt": "请先选择对战模式，再选择英雄",
        "hero_unselected": "英雄未选择",
        "mode_unselected": "模式未选择",
        "flash": "闪现",
        "heal": "治疗",
        "season": "赛季试炼",
        "profile": "召唤师",
        "loading": "加载中",
        "versus": "对战",
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
        "level_up": "{name} 升到 {level} 级：生命+48 攻击+4 技能更强",
        "need_base": "回到己方水晶附近才能购买",
        "recall_start": "正在回城...",
        "recall_cancel": "回城被打断",
        "recall_complete": "已回到基地",
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
            "sentinel": "玄甲",
            "shade": "影刃",
        },
        "hero_roles": {
            "vanguard": "战士",
            "ranger": "射手",
            "arcanist": "法师",
            "sentinel": "坦克",
            "shade": "刺客",
        },
        "skills": {
            "vanguard": {"q": "破阵矛", "e": "铁壁冲锋", "r": "裂地击"},
            "ranger": {"q": "三连矢", "e": "疾步", "r": "箭雨"},
            "arcanist": {"q": "雷光法球", "e": "奥术护盾", "r": "雷暴领域"},
            "sentinel": {"q": "巨锚波", "e": "玄甲守护", "r": "守护重砸"},
            "shade": {"q": "影切", "e": "瞬步斩", "r": "虚空处决"},
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


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: str
    ttl: float
    max_ttl: float
    radius: float = 3
    shrink: bool = True


@dataclass
class Beam:
    x1: float
    y1: float
    x2: float
    y2: float
    color: str
    ttl: float
    max_ttl: float
    width: float = 3


@dataclass
class FloatingText:
    x: float
    y: float
    text: str
    color: str
    ttl: float
    max_ttl: float
    vy: float = -34


@dataclass
class Banner:
    text: str
    color: str
    ttl: float
    max_ttl: float
