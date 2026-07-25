ITEMS = {
    "blade": {"cost": 120, "attack_damage": 8, "max_stacks": 3, "color": "#f7d765", "category": "attack"},
    "longbow": {"cost": 180, "attack_damage": 12, "attack_range": 12, "max_stacks": 2, "color": "#76f4d1", "category": "attack"},
    "piercing_spear": {"cost": 260, "attack_damage": 22, "max_stacks": 1, "color": "#ffb86c", "category": "attack", "requires": {"blade": 1}},
    "storm_staff": {"cost": 240, "skill_power": 30, "max_stacks": 1, "color": "#b38cff", "category": "magic", "requires": {"arcane_core": 1}},
    "arcane_core": {"cost": 170, "skill_power": 16, "max_stacks": 2, "color": "#8fd3ff", "category": "magic"},
    "frost_orb": {"cost": 220, "skill_power": 18, "max_hp": 80, "max_stacks": 1, "color": "#9ad7ff", "category": "magic", "requires": {"arcane_core": 1}},
    "guard": {"cost": 150, "max_hp": 110, "max_stacks": 3, "color": "#48d06b", "category": "defense"},
    "bulwark": {"cost": 240, "max_hp": 260, "max_stacks": 1, "color": "#aeb8ad", "category": "defense", "requires": {"guard": 1}, "passive": "damage_reduction"},
    "revive_plate": {"cost": 300, "max_hp": 180, "attack_damage": 8, "max_stacks": 1, "color": "#f5f1d7", "category": "defense", "requires": {"bulwark": 1}, "passive": "last_stand"},
    "boots": {"cost": 100, "speed": 18, "max_stacks": 3, "color": "#76b7ff", "category": "move"},
    "swift_boots": {"cost": 180, "speed": 34, "attack_cd_reduce": 0.04, "max_stacks": 1, "color": "#78a3ff", "category": "move", "requires": {"boots": 1}},
    "hunter_charm": {"cost": 160, "attack_damage": 6, "skill_power": 10, "max_hp": 60, "max_stacks": 2, "color": "#7ddc83", "category": "jungle", "passive": "neutral_hunter"},
}


HERO_RECOMMENDED_ITEMS = {
    "vanguard": ["blade", "guard", "piercing_spear", "revive_plate"],
    "ranger": ["longbow", "blade", "swift_boots", "piercing_spear"],
    "arcanist": ["arcane_core", "storm_staff", "frost_orb", "boots"],
    "sentinel": ["guard", "bulwark", "revive_plate", "hunter_charm"],
    "shade": ["piercing_spear", "swift_boots", "blade", "hunter_charm"],
}
