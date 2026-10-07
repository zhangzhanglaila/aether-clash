"""Account-level meta progression: persistent profile, XP awards, daily quests, and level curve."""
import datetime
import json
import os
import random

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
PROFILE_PATH = os.path.join(SAVE_DIR, "profile.json")

DEFAULT_PROFILE = {
    "xp": 0,
    "level": 1,
    "matches": 0,
    "wins": 0,
    "kills": 0,
    "damage": 0,
    "quests": {},
}

QUEST_POOL = [
    {"id": "win", "metric": "win", "goal": 1, "reward": 60, "text_key": "quest_win"},
    {"id": "kills5", "metric": "kills", "goal": 5, "reward": 55, "text_key": "quest_kills"},
    {"id": "minions30", "metric": "minions", "goal": 30, "reward": 45, "text_key": "quest_minions"},
    {"id": "matches2", "metric": "matches", "goal": 2, "reward": 40, "text_key": "quest_matches"},
    {"id": "damage8000", "metric": "damage", "goal": 8000, "reward": 50, "text_key": "quest_damage"},
]


def today_key():
    return datetime.date.today().isoformat()


def daily_quests(date_str=None):
    date_str = date_str or today_key()
    return random.Random("quests:" + date_str).sample(QUEST_POOL, 3)


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


def grant_xp(profile, amount):
    """Add XP, applying level-ups in place; returns number of levels gained."""
    profile["xp"] += amount
    leveled = 0
    while profile["xp"] >= xp_for_level(profile["level"]):
        profile["xp"] -= xp_for_level(profile["level"])
        profile["level"] += 1
        leveled += 1
    return leveled


def apply_match_result(profile, match_stats, hero_stats, won):
    profile["matches"] += 1
    profile["wins"] += 1 if won else 0
    profile["kills"] += hero_stats.get("kills", 0)
    profile["damage"] += int(hero_stats.get("damage_dealt", 0))
    xp_gain = match_xp_reward(match_stats, hero_stats, won)
    leveled = grant_xp(profile, xp_gain)
    return xp_gain, leveled


def record_match_progress(profile, hero_stats, won):
    """Advance today's daily quests with this match's deltas; returns (completed quests, xp rewarded)."""
    today = today_key()
    state = profile.get("quests") or {}
    if state.get("date") != today:
        state = {"date": today, "done": [], "progress": {}}
    deltas = {
        "win": 1 if won else 0,
        "matches": 1,
        "kills": hero_stats.get("kills", 0),
        "minions": int(hero_stats.get("minions_last_hit", 0)),
        "damage": int(hero_stats.get("hero_damage", 0)),
    }
    completed = []
    reward = 0
    for quest in daily_quests(today):
        if quest["id"] in state["done"]:
            continue
        progress = state["progress"].get(quest["id"], 0) + deltas[quest["metric"]]
        state["progress"][quest["id"]] = progress
        if progress >= quest["goal"]:
            state["done"].append(quest["id"])
            reward += quest["reward"]
            completed.append(quest)
    profile["quests"] = state
    if reward:
        grant_xp(profile, reward)
    return completed, reward
