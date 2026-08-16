import math
from dataclasses import dataclass, field


WIDTH = 1100
HEIGHT = 700
FPS_MS = 16
SKILL_MAX_LEVELS = {"q": 6, "e": 6, "r": 3}
SKILL_UPGRADE_KEYS = {"z": "q", "x": "e", "c": "r"}


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
    "weaver": {
        "name": "Aether Weaver",
        "role": "Assassin",
        "accent": "#ff9f6e",
        "hp": 455,
        "speed": 236,
        "attack_damage": 32,
        "attack_range": 205,
        "attack_cd": 0.34,
        "cooldowns": {"q": 2.9, "e": 5.4, "r": 12.8},
        "skills": {"q": "Thread Lance", "e": "Grapple Vault", "r": "Snare Bloom"},
    },
    "warden": {
        "name": "Dawn Warden",
        "role": "Support",
        "accent": "#ffd166",
        "hp": 560,
        "speed": 184,
        "attack_damage": 26,
        "attack_range": 238,
        "attack_cd": 0.48,
        "cooldowns": {"q": 3.4, "e": 6.0, "r": 14.5},
        "skills": {"q": "Radiant Bolt", "e": "Sanctuary Step", "r": "Dawnfall"},
    },
    "reaver": {
        "name": "Crimson Reaver",
        "role": "Fighter",
        "accent": "#ff5a6a",
        "hp": 585,
        "speed": 206,
        "attack_damage": 36,
        "attack_range": 198,
        "attack_cd": 0.40,
        "cooldowns": {"q": 3.0, "e": 5.2, "r": 13.0},
        "skills": {"q": "Blood Crescent", "e": "Rift Lunge", "r": "Crimson Harvest"},
    },
    "geomancer": {
        "name": "Stone Geomancer",
        "role": "Mage",
        "accent": "#b7d56a",
        "hp": 520,
        "speed": 168,
        "attack_damage": 24,
        "attack_range": 255,
        "attack_cd": 0.52,
        "cooldowns": {"q": 3.8, "e": 6.4, "r": 15.0},
        "skills": {"q": "Shard Volley", "e": "Stone Wall", "r": "Quake Ring"},
    },
    "tempest": {
        "name": "Tempest Duelist",
        "role": "Marksman",
        "accent": "#66d9ff",
        "hp": 455,
        "speed": 226,
        "attack_damage": 28,
        "attack_range": 275,
        "attack_cd": 0.32,
        "cooldowns": {"q": 2.7, "e": 4.9, "r": 12.2},
        "skills": {"q": "Gale Shot", "e": "Slipstream", "r": "Cyclone Barrage"},
    },
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


JUNGLE_CAMPS = {
    "blue_grove": {
        "x": 324,
        "y": 500,
        "hp": 360,
        "attack_damage": 20,
        "gold": 62,
        "xp": 72,
        "respawn": 24.0,
        "radius": 18,
        "color": "#76f4d1",
    },
    "blue_stone": {
        "x": 414,
        "y": 248,
        "hp": 420,
        "attack_damage": 24,
        "gold": 72,
        "xp": 82,
        "respawn": 28.0,
        "radius": 20,
        "color": "#8fd3ff",
    },
    "red_grove": {
        "x": 776,
        "y": 200,
        "hp": 360,
        "attack_damage": 20,
        "gold": 62,
        "xp": 72,
        "respawn": 24.0,
        "radius": 18,
        "color": "#76f4d1",
    },
    "red_stone": {
        "x": 686,
        "y": 452,
        "hp": 420,
        "attack_damage": 24,
        "gold": 72,
        "xp": 82,
        "respawn": 28.0,
        "radius": 20,
        "color": "#8fd3ff",
    },
    "ancient_guard": {
        "x": 550,
        "y": 350,
        "hp": 820,
        "attack_damage": 36,
        "gold": 150,
        "xp": 180,
        "respawn": 45.0,
        "radius": 26,
        "color": "#f7d765",
    },
}


RIVER_POLYGON = [(410, 92), (504, 84), (708, 608), (604, 616)]


BRUSH_ZONES = [
    (188, 366, 300, 438),
    (426, 200, 532, 278),
    (568, 422, 674, 500),
    (800, 262, 912, 334),
]


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
        "defeated_by_neutral": "{victim} was defeated by jungle monsters",
        "killing_spree": "{name} is on a {count} kill streak",
        "shutdown": "{name} shut down {target}",
        "destroyed": "{name} destroyed",
        "neutral_slain": "{name} defeated: +{gold}G +{xp}XP",
        "empowered_minions": "{team} minions empowered on {lane}",
        "level_up": "Lv.{level} + Skill Point",
        "skill_point_gained": "Skill point gained",
        "skill_upgraded": "{skill} upgraded to Lv.{level}",
        "skill_locked": "{skill} unlocks at Lv.{level}",
        "skill_max": "{skill} is maxed",
        "skill_points": "Skill Points",
        "locked": "LOCK",
        "scoreboard": "Scoreboard",
        "kills": "Kills",
        "deaths": "Deaths",
        "gold": "Gold",
        "equipment": "Equipment",
        "settlement": "Match Result",
        "result_win": "Victory",
        "result_loss": "Defeat",
        "duration": "Duration",
        "destroyed_towers": "Towers",
        "rematch": "Rematch",
        "back_lobby": "Lobby",
        "need_base": "Return to base to buy equipment",
        "recall_start": "Recalling...",
        "recall_cancel": "Recall interrupted",
        "recall_complete": "Returned to base",
        "enemy_recall_start": "Enemy started recall",
        "enemy_recall_cancel": "Enemy recall interrupted",
        "enemy_recall_complete": "Enemy returned to base",
        "target_locked": "Target locked: {name}",
        "target_cleared": "Target lock cleared",
        "not_enough_gold": "Not enough gold",
        "need_component": "Need {item} first",
        "item_max": "Equipment is maxed",
        "bought": "Bought {item}",
        "last_stand": "{name}'s Revive Plate activated",
        "buy_recommended": "Recommended",
        "no_recommended": "Recommended build is complete",
        "shop": "SHOP",
        "level": "LV",
        "enemy_prefix": "Enemy {name}",
        "mode_rule_summary": "Wave {wave}s  Gold x{gold}  XP x{xp}  Structure x{structure}",
        "stat_attack": "ATK",
        "stat_skill": "SKILL",
        "stat_hp": "HP",
        "stat_speed": "SPD",
        "stat_range": "RANGE",
        "stat_haste": "HASTE",
        "stat_armor": "ARMOR",
        "stat_magic_resist": "M.RES",
        "stat_armor_pen": "PEN",
        "stat_magic_pen": "M.PEN",
        "stat_crit": "CRIT",
        "stat_lifesteal": "LIFESTEAL",
        "stat_tenacity": "TENACITY",
        "passive_damage_reduction": "Damage reduction",
        "passive_last_stand": "Revive once",
        "passive_neutral_hunter": "Jungle bonus",
        "tutorial_title": "FIRST MATCH GUIDE",
        "tutorial_lines": [
            "Move with WASD or arrow keys. Aim with the mouse.",
            "Left click or Space attacks. Hold Q/E/R to aim, release to cast.",
            "Defeat minions and jungle monsters for gold and XP.",
            "Return near your core to buy items, then destroy towers and the enemy core.",
        ],
        "tutorial_close": "Press H or click here to hide",
        "skill_tooltip_title": "{key} {name}  Lv.{level}/{max_level}",
        "skill_tooltip_body": "{detail}  Next: damage/heal up, cooldown down.",
        "equipment_stats": "Stats",
        "equipment_requires": "Requires {item}",
        "equipment_passive": "Passive",
        "damage_dealt": "Damage",
        "hero_damage": "Hero dmg",
        "structure_damage": "Structure dmg",
        "damage_taken": "Taken",
        "healing": "Healing",
        "shielding": "Shielding",
        "monsters_slain": "Jungle",
        "minions_last_hit": "Last hits",
        "items_spent": "Items spent",
        "gold_earned": "Gold earned",
        "structure_targeted": "STRUCTURE TARGET",
        "hero_names": {
            "vanguard": "Vanguard",
            "ranger": "Star Ranger",
            "arcanist": "Storm Arcanist",
            "sentinel": "Iron Sentinel",
            "shade": "Night Shade",
            "weaver": "Aether Weaver",
            "warden": "Dawn Warden",
            "reaver": "Crimson Reaver",
            "geomancer": "Stone Geomancer",
            "tempest": "Tempest Duelist",
        },
        "hero_roles": {
            "vanguard": "Fighter",
            "ranger": "Marksman",
            "arcanist": "Mage",
            "sentinel": "Tank",
            "shade": "Assassin",
            "weaver": "Assassin",
            "warden": "Support",
            "reaver": "Fighter",
            "geomancer": "Mage",
            "tempest": "Marksman",
        },
        "skills": {
            "vanguard": {"q": "Spear Line", "e": "Shield Rush", "r": "Earth Break"},
            "ranger": {"q": "Triple Shot", "e": "Quick Step", "r": "Arrow Storm"},
            "arcanist": {"q": "Storm Orb", "e": "Arc Shield", "r": "Thunder Field"},
            "sentinel": {"q": "Anchor Wave", "e": "Fortify", "r": "Guardian Slam"},
            "shade": {"q": "Shadow Cut", "e": "Blink Strike", "r": "Void Execution"},
            "weaver": {"q": "Thread Lance", "e": "Grapple Vault", "r": "Snare Bloom"},
            "warden": {"q": "Radiant Bolt", "e": "Sanctuary Step", "r": "Dawnfall"},
            "reaver": {"q": "Blood Crescent", "e": "Rift Lunge", "r": "Crimson Harvest"},
            "geomancer": {"q": "Shard Volley", "e": "Stone Wall", "r": "Quake Ring"},
            "tempest": {"q": "Gale Shot", "e": "Slipstream", "r": "Cyclone Barrage"},
        },
        "passives": {
            "vanguard": {"name": "Last Line", "detail": "Below 40% HP, incoming damage is reduced."},
            "ranger": {"name": "Rhythm Shot", "detail": "Every third basic attack deals bonus damage and slows."},
            "arcanist": {"name": "Arc Charge", "detail": "Casting a skill grants a small temporary shield."},
            "sentinel": {"name": "Plated Guard", "detail": "All incoming damage is slightly reduced."},
            "shade": {"name": "Cull", "detail": "Deals more damage to low-health enemy heroes."},
            "weaver": {"name": "Thread Mark", "detail": "Deals more damage to stunned or slowed targets."},
            "warden": {"name": "Dawn Grace", "detail": "Healing or shielding effects are stronger when low on health."},
            "reaver": {"name": "Blood Price", "detail": "Damaging enemy heroes restores a small amount of health."},
            "geomancer": {"name": "Stone Skin", "detail": "Standing near structures or jungle monsters reduces incoming damage."},
            "tempest": {"name": "Tailwind", "detail": "Casting a skill briefly speeds up the next basic attack."},
        },
        "skill_details": {
            "vanguard": {
                "q": "Piercing spear line damage.",
                "e": "Short engage dash with impact damage.",
                "r": "Targeted ground burst with stun and slow.",
            },
            "ranger": {
                "q": "Three slowing arrows in a narrow fan.",
                "e": "Quick dash and instant attack reset.",
                "r": "Wide arrow storm that pierces and slows.",
            },
            "arcanist": {
                "q": "Piercing storm orb with heavy slow.",
                "e": "Heal, shield, and close-range pulse.",
                "r": "Large thunder field with stun and damage over time.",
            },
            "sentinel": {
                "q": "Close shockwave plus anchor projectile.",
                "e": "Fortify with heal, shield, and attack reset.",
                "r": "Wide guardian slam with strong control.",
            },
            "shade": {
                "q": "Fast shadow slash projectile.",
                "e": "Blink strike toward a nearby target or aim direction.",
                "r": "Execute burst that scales with missing health.",
            },
            "weaver": {
                "q": "Piercing thread lance that slows enemies.",
                "e": "Long grapple vault with landing damage.",
                "r": "Snare bloom that bursts and briefly locks enemies down.",
            },
            "warden": {
                "q": "Radiant projectile that damages enemies and slows on hit.",
                "e": "Short step that heals and shields the caster.",
                "r": "Large dawn zone that damages enemies and restores health.",
            },
            "reaver": {
                "q": "Wide blood crescent with short-range burst.",
                "e": "Aggressive lunge that damages and slows on landing.",
                "r": "Heavy harvest strike that heals from enemies hit.",
            },
            "geomancer": {
                "q": "Three stone shards in a controlled spread.",
                "e": "Raises a defensive stone shell and nearby shockwave.",
                "r": "Earthquake ring with strong area control.",
            },
            "tempest": {
                "q": "Fast piercing wind shot.",
                "e": "Slipstream dash with attack reset and speed burst.",
                "r": "Cyclone barrage of crossing wind blades.",
            },
        },
        "skill_traits": {
            "vanguard": "Dash / area stun / durable engage",
            "ranger": "Long range / mobility / slowing arrow storm",
            "arcanist": "Burst mage / shield / storm damage over time",
            "sentinel": "Tank / shield / slows and short stun",
            "shade": "Assassin / blink / missing-health execution",
            "weaver": "Assassin / grapple dash / snare burst",
            "warden": "Support / heal-shield / area sustain",
            "reaver": "Fighter / lifesteal / dive finisher",
            "geomancer": "Mage / terrain control / durable zone",
            "tempest": "Marksman / attack reset / piercing wind",
        },
        "items": {
            "blade": "Blade",
            "longbow": "Longbow",
            "piercing_spear": "Piercing Spear",
            "storm_staff": "Storm Staff",
            "arcane_core": "Arcane Core",
            "frost_orb": "Frost Orb",
            "boots": "Boots",
            "guard": "Guard",
            "bulwark": "Bulwark",
            "revive_plate": "Revive Plate",
            "swift_boots": "Swift Boots",
            "hunter_charm": "Hunter Charm",
        },
        "lanes": {
            "top": "top lane",
            "mid": "mid lane",
            "bot": "bot lane",
        },
        "jungle": {
            "blue_grove": "Blue Grove Spirit",
            "blue_stone": "Blue Stonebeast",
            "red_grove": "Red Grove Spirit",
            "red_stone": "Red Stonebeast",
            "ancient_guard": "Ancient Guard",
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
        "defeated_by_neutral": "{victim} 被野怪击败",
        "killing_spree": "{name} 已连续击败 {count} 人",
        "shutdown": "{name} 终结了 {target}",
        "destroyed": "{name} 被摧毁",
        "neutral_slain": "击败{name}：+{gold}金币 +{xp}经验",
        "empowered_minions": "{team}{lane}路小兵已强化",
        "level_up": "{level}级 +技能点",
        "skill_point_gained": "获得技能点",
        "skill_upgraded": "{skill} 升到 {level} 级",
        "skill_locked": "{skill} 需要 {level} 级解锁",
        "skill_max": "{skill} 已满级",
        "skill_points": "技能点",
        "locked": "未解锁",
        "scoreboard": "战绩面板",
        "kills": "击杀",
        "deaths": "死亡",
        "gold": "金币",
        "equipment": "装备",
        "settlement": "对局结算",
        "result_win": "胜利",
        "result_loss": "失败",
        "duration": "时长",
        "destroyed_towers": "推塔",
        "rematch": "再来一局",
        "back_lobby": "返回大厅",
        "need_base": "回到己方水晶附近才能购买",
        "recall_start": "正在回城...",
        "recall_cancel": "回城被打断",
        "recall_complete": "已回到基地",
        "enemy_recall_start": "敌方开始回城",
        "enemy_recall_cancel": "敌方回城被打断",
        "enemy_recall_complete": "敌方已回到基地",
        "target_locked": "已锁定目标：{name}",
        "target_cleared": "已取消锁定",
        "not_enough_gold": "金币不足",
        "need_component": "需要先购买{item}",
        "item_max": "装备已满级",
        "bought": "已购买 {item}",
        "last_stand": "{name}触发复战甲",
        "buy_recommended": "推荐购买",
        "no_recommended": "推荐装备已完成",
        "shop": "商店",
        "level": "等级",
        "enemy_prefix": "敌方{name}",
        "mode_rule_summary": "兵线 {wave}秒  金币 x{gold}  经验 x{xp}  建筑 x{structure}",
        "stat_attack": "攻击",
        "stat_skill": "法强",
        "stat_hp": "生命",
        "stat_speed": "移速",
        "stat_range": "射程",
        "stat_haste": "急速",
        "stat_armor": "护甲",
        "stat_magic_resist": "法抗",
        "stat_armor_pen": "穿透",
        "stat_magic_pen": "法穿",
        "stat_crit": "暴击",
        "stat_lifesteal": "吸血",
        "stat_tenacity": "韧性",
        "passive_damage_reduction": "减伤被动",
        "passive_last_stand": "复活被动",
        "passive_neutral_hunter": "打野加成",
        "tutorial_title": "新手引导",
        "tutorial_lines": [
            "WASD 或方向键移动，鼠标控制瞄准方向。",
            "左键或 Space 普攻，按住 Q/E/R 显示范围，松开释放。",
            "击败小兵和野怪获得金币与经验。",
            "回到己方水晶附近购买装备，推塔并摧毁敌方水晶获胜。",
        ],
        "tutorial_close": "按 H 或点击这里隐藏",
        "skill_tooltip_title": "{key} {name}  {level}/{max_level}级",
        "skill_tooltip_body": "{detail}  升级：伤害/治疗提升，冷却缩短。",
        "equipment_stats": "属性",
        "equipment_requires": "需要 {item}",
        "equipment_passive": "被动",
        "damage_dealt": "输出",
        "hero_damage": "英雄伤害",
        "structure_damage": "建筑伤害",
        "damage_taken": "承伤",
        "healing": "治疗量",
        "shielding": "护盾量",
        "monsters_slain": "野怪",
        "minions_last_hit": "补刀",
        "items_spent": "装备花费",
        "gold_earned": "总经济",
        "structure_targeted": "防御塔锁定",
        "hero_names": {
            "vanguard": "铁卫",
            "ranger": "星弓",
            "arcanist": "雷法",
            "sentinel": "玄甲",
            "shade": "影刃",
            "weaver": "星索",
            "warden": "曙光守护",
            "reaver": "赤刃",
            "geomancer": "岩术师",
            "tempest": "风暴游侠",
        },
        "hero_roles": {
            "vanguard": "战士",
            "ranger": "射手",
            "arcanist": "法师",
            "sentinel": "坦克",
            "shade": "刺客",
            "weaver": "刺客",
            "warden": "辅助",
            "reaver": "战士",
            "geomancer": "法师",
            "tempest": "射手",
        },
        "skills": {
            "vanguard": {"q": "破阵矛", "e": "铁壁冲锋", "r": "裂地击"},
            "ranger": {"q": "三连矢", "e": "疾步", "r": "箭雨"},
            "arcanist": {"q": "雷光法球", "e": "奥术护盾", "r": "雷暴领域"},
            "sentinel": {"q": "巨锚波", "e": "玄甲守护", "r": "守护重砸"},
            "shade": {"q": "影切", "e": "瞬步斩", "r": "虚空处决"},
            "weaver": {"q": "索刃", "e": "钩索跃迁", "r": "星缚绽放"},
            "warden": {"q": "辉光弹", "e": "圣域步", "r": "曙光坠落"},
            "reaver": {"q": "血月斩", "e": "裂隙突刺", "r": "赤潮收割"},
            "geomancer": {"q": "岩片齐射", "e": "岩壁守护", "r": "地震环"},
            "tempest": {"q": "疾风矢", "e": "顺风步", "r": "旋风连击"},
        },
        "passives": {
            "vanguard": {"name": "背水阵线", "detail": "生命低于 40% 时，受到的伤害降低。"},
            "ranger": {"name": "节奏射击", "detail": "每第三次普攻造成额外伤害并减速。"},
            "arcanist": {"name": "奥术充能", "detail": "释放技能后获得少量临时护盾。"},
            "sentinel": {"name": "重甲守卫", "detail": "受到的所有伤害小幅降低。"},
            "shade": {"name": "残影收割", "detail": "攻击低血量敌方英雄时伤害提升。"},
            "weaver": {"name": "星索印记", "detail": "攻击被眩晕或减速的目标时伤害提升。"},
            "warden": {"name": "曙光恩泽", "detail": "低血量时治疗和护盾效果提升。"},
            "reaver": {"name": "血价", "detail": "伤害敌方英雄时回复少量生命。"},
            "geomancer": {"name": "岩肤", "detail": "靠近建筑或野怪时受到的伤害降低。"},
            "tempest": {"name": "顺风", "detail": "释放技能后短时间强化下一次普攻节奏。"},
        },
        "skill_details": {
            "vanguard": {
                "q": "直线穿透长矛伤害。",
                "e": "短距离冲锋并造成落点伤害。",
                "r": "指定区域爆发，造成眩晕和减速。",
            },
            "ranger": {
                "q": "窄扇形三连减速箭。",
                "e": "快速位移并立即刷新普攻。",
                "r": "大范围穿透箭雨，命中减速。",
            },
            "arcanist": {
                "q": "穿透雷光法球并大幅减速。",
                "e": "治疗、护盾和近身脉冲伤害。",
                "r": "大范围雷暴，眩晕并持续伤害。",
            },
            "sentinel": {
                "q": "近身震荡并发射巨锚波。",
                "e": "回血、护盾并刷新普攻。",
                "r": "大范围守护重砸，强控制。",
            },
            "shade": {
                "q": "高速影刃投射伤害。",
                "e": "向附近目标或瞄准方向瞬步斩。",
                "r": "目标血量越低，处决爆发越高。",
            },
            "weaver": {
                "q": "穿透索刃，命中后减速。",
                "e": "长距离钩索跃迁，落点伤害。",
                "r": "星索束缚范围爆发，短暂控制敌人。",
            },
            "warden": {
                "q": "发射辉光弹，命中敌人造成伤害和减速。",
                "e": "短距离位移，同时获得治疗和护盾。",
                "r": "召唤大范围曙光区域，伤害敌人并回复生命。",
            },
            "reaver": {
                "q": "挥出宽弧血刃，造成近中距离爆发。",
                "e": "向前突刺，落点造成伤害和减速。",
                "r": "重击收割区域敌人，并按命中回复生命。",
            },
            "geomancer": {
                "q": "向前方扇形射出三枚岩片。",
                "e": "凝聚岩壁护盾，并震荡周围敌人。",
                "r": "释放地震环，造成范围控制和伤害。",
            },
            "tempest": {
                "q": "高速穿透风矢。",
                "e": "顺风位移，刷新普攻并加速。",
                "r": "多道交叉风刃形成旋风压制。",
            },
        },
        "skill_traits": {
            "vanguard": "突进 / 范围眩晕 / 耐打开团",
            "ranger": "远程 / 位移 / 减速箭雨",
            "arcanist": "爆发法师 / 护盾 / 雷暴持续伤害",
            "sentinel": "坦克 / 护盾 / 减速短控",
            "shade": "刺客 / 瞬步 / 已损生命斩杀",
            "weaver": "刺客 / 钩索位移 / 束缚爆发",
            "warden": "辅助 / 治疗护盾 / 区域续航",
            "reaver": "战士 / 吸血 / 突进收割",
            "geomancer": "法师 / 地形压制 / 阵地控制",
            "tempest": "射手 / 刷新普攻 / 穿透风刃",
        },
        "items": {
            "blade": "破军刃",
            "longbow": "逐星弓",
            "piercing_spear": "破甲枪",
            "storm_staff": "雷霆杖",
            "arcane_core": "奥术核",
            "frost_orb": "霜华珠",
            "boots": "疾行靴",
            "guard": "守护甲",
            "bulwark": "壁垒盾",
            "revive_plate": "复战甲",
            "swift_boots": "迅捷靴",
            "hunter_charm": "猎野符",
        },
        "lanes": {
            "top": "上",
            "mid": "中",
            "bot": "下",
        },
        "jungle": {
            "blue_grove": "蓝野灵",
            "blue_stone": "蓝石兽",
            "red_grove": "红野灵",
            "red_stone": "红石兽",
            "ancient_guard": "远古守卫",
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
    shield: float = 0
    stunned_until: float = 0
    slowed_until: float = 0
    slow_mult: float = 1.0

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
    skill_power: float = 0
    skill_cds: dict = field(default_factory=lambda: {"q": 3.6, "e": 5.5, "r": 13.5})
    skill_names: dict = field(default_factory=lambda: {"q": "Spear Line", "e": "Shield Rush", "r": "Earth Break"})
    armor: float = 20
    magic_resist: float = 18
    armor_pen: float = 0
    magic_pen: float = 0
    crit_chance: float = 0
    crit_damage: float = 1.75
    lifesteal: float = 0
    tenacity: float = 0
    level: int = 1
    xp: int = 0
    next_xp: int = 120
    gold: int = 0
    kills: int = 0
    kill_streak: int = 0
    deaths: int = 0
    last_attacker_team: str = ""
    equipment: dict = field(default_factory=lambda: {"blade": 0, "boots": 0, "guard": 0})
    item_passives_used: dict = field(default_factory=dict)
    respawn_at: float = 0
    cooldowns: dict = field(default_factory=lambda: {"q": 0, "e": 0, "r": 0})
    skill_levels: dict = field(default_factory=lambda: {"q": 1, "e": 1, "r": 0})
    skill_points: int = 0
    passive_stacks: int = 0


@dataclass
class Minion(Unit):
    lane: str = "mid"
    waypoint: int = 1
    kind: str = "melee"
    empowered: bool = False
    gold_reward: int = 8
    xp_reward: int = 28


@dataclass
class Tower(Unit):
    lane: str = "mid"
    name: str = "Tower"
    tier: str = "outer"


@dataclass
class Core(Unit):
    name: str = "Core"


@dataclass
class NeutralMonster(Unit):
    camp_key: str = "blue_grove"
    name: str = "Neutral"
    gold_reward: int = 0
    xp_reward: int = 0
    respawn_delay: float = 24.0
    respawn_at: float = 0
    color: str = "#f7d765"


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
    slow: float = 0
    slow_duration: float = 0
    stun: float = 0
    damage_type: str = ""


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


@dataclass
class DamageOverTime:
    target: object
    attacker_team: str
    damage_per_second: float
    ttl: float
    tick_interval: float = 0.35
    tick_timer: float = 0
    color: str = "#b38cff"
