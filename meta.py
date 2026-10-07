"""Account-level meta progression: persistent profile, XP awards, and level curve."""
import json
import os

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
PROFILE_PATH = os.path.join(SAVE_DIR, "profile.json")

DEFAULT_PROFILE = {
    "xp": 0,
    "level": 1,
    "matches": 0,
    "wins": 0,
    "kills": 0,
    "damage": 0,
}


def load_profile():
    profile = dict(DEFAULT_PROFILE)
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            profile.update({key: value for key, value in data.items() if key in DEFAULT_PROFILE})
    except (OSError, ValueError):
        pass
    return profile


def save_profile(profile):
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(PROFILE_PATH, "w", encoding="utf-8") as handle:
        json.dump(profile, handle, ensure_ascii=False, indent=2)


def xp_for_level(level):
    return 120 + 60 * level


def match_xp_reward(match_stats, hero_stats, won):
    return int(
        40
        + (35 if won else 0)
        + hero_stats.get("kills", 0) * 3
        + min(40, hero_stats.get("hero_damage", 0) / 120)
        + min(25, hero_stats.get("damage_dealt", 0) / 400)
        + hero_stats.get("towers_destroyed", 0) * 8
        + hero_stats.get("minions_last_hit", 0) * 0.4
    )


def apply_match_result(profile, match_stats, hero_stats, won):
    profile["matches"] += 1
    profile["wins"] += 1 if won else 0
    profile["kills"] += hero_stats.get("kills", 0)
    profile["damage"] += int(hero_stats.get("damage_dealt", 0))
    xp_gain = match_xp_reward(match_stats, hero_stats, won)
    profile["xp"] += xp_gain
    leveled = 0
    while profile["xp"] >= xp_for_level(profile["level"]):
        profile["xp"] -= xp_for_level(profile["level"])
        profile["level"] += 1
        leveled += 1
    return xp_gain, leveled
