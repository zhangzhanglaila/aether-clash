"""Procedural sprite generation plus a file-override loader.

Drop PNG files into assets/ to replace the generated art file-by-file:
  assets/sprites/heroes/<hero_key>.png        battle sprite, facing up, ~64x64, frame A
  assets/sprites/heroes/<hero_key>_b.png      battle sprite, frame B (animation)
  assets/sprites/heroes/<hero_key>_red.png    red-team recolor (frame A; suffix _b_red for frame B)
  assets/portraits/<hero_key>.png             menu portrait, square (scaled as needed)
Missing files fall back to the procedural generator, so the game works with an empty assets/ dir.
"""
import math
import os

import pygame

from game_data import team_color

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

SKIN = (232, 195, 158)
DARK = (26, 32, 36)

_surfaces = {}
_rotated = {}
_file_cache = {}


def _load_override(rel_path):
    if rel_path in _file_cache:
        return _file_cache[rel_path]
    path = os.path.join(ASSETS_DIR, rel_path)
    surface = None
    if os.path.isfile(path):
        try:
            surface = pygame.image.load(path).convert_alpha()
        except pygame.error:
            surface = None
    _file_cache[rel_path] = surface
    return surface


def _color(hex_or_tuple):
    if isinstance(hex_or_tuple, str):
        return tuple(pygame.Color(hex_or_tuple))[:3]
    return hex_or_tuple


def _shade(rgb, factor):
    return tuple(max(0, min(255, int(channel * factor))) for channel in rgb)


def _circle(surface, color_value, pos, radius, width=0):
    pygame.draw.circle(surface, color_value, (round(pos[0]), round(pos[1])), round(radius), width)


def _line(surface, color_value, start, end, width=2):
    pygame.draw.line(surface, color_value, (round(start[0]), round(start[1])), (round(end[0]), round(end[1])), width)


def hero_sprite(hero_key, role, accent, team, frame=0):
    """Battle sprite for a hero, drawn facing up (north); rotate before blitting."""
    override_base = f"sprites/heroes/{hero_key}" + ("_b" if frame else "")
    override = _load_override(override_base + ".png") or _load_override(override_base + f"_{team}.png")
    if override:
        return override
    key = ("hero", hero_key, team, frame)
    if key in _surfaces:
        return _surfaces[key]
    size = 64
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    team_rgb = _color(team_color(team))
    accent = _color(accent)
    armor = _shade(team_rgb, 0.78)
    bob = 1 if frame else 0
    cx = size / 2
    cy = size / 2 + bob

    # shadow
    _circle(surface, (0, 0, 0, 70), (cx, size - 7), 11)

    # weapon behind body for melee reach roles
    if role == "Fighter":
        _line(surface, _shade(accent, 0.9), (cx + 16, cy + 14), (cx + 20, cy - 27), 5)
        pygame.draw.polygon(surface, accent, [(cx + 20, cy - 35), (cx + 15, cy - 22), (cx + 25, cy - 22)])
    elif role == "Marksman":
        pygame.draw.arc(surface, _shade(accent, 0.95), pygame.Rect(cx + 8, cy - 24, 26, 48), -70, 70, 4)
        _line(surface, (220, 220, 220), (cx + 17, cy - 20), (cx + 17, cy + 20), 1)
    elif role == "Mage" or role == "Support":
        staff_top = cy - 30 + (2 if frame else 0)
        _line(surface, (120, 90, 60), (cx + 15, cy + 16), (cx + 15, staff_top), 4)
        _circle(surface, accent, (cx + 15, staff_top - 4), 6)
        _circle(surface, _shade(accent, 1.5), (cx + 14, staff_top - 5), 2)
    elif role == "Assassin":
        for dx in (-12, 12):
            offset = 3 if (frame and dx > 0) else 0
            _line(surface, (200, 205, 215), (cx + dx, cy + 10 - offset), (cx + dx, cy - 19 - offset), 4)

    # torso
    pygame.draw.ellipse(surface, armor, pygame.Rect(cx - 15, cy - 11, 30, 26))
    pygame.draw.ellipse(surface, team_rgb, pygame.Rect(cx - 15, cy - 11, 30, 26), 2)
    _line(surface, accent, (cx - 11, cy + 6), (cx + 11, cy + 6), 4)

    # shoulder pads
    _circle(surface, team_rgb, (cx - 15, cy - 5), 7)
    _circle(surface, team_rgb, (cx + 15, cy - 5), 7)
    _circle(surface, _shade(team_rgb, 1.3), (cx - 15, cy - 6), 3)
    _circle(surface, _shade(team_rgb, 1.3), (cx + 15, cy - 6), 3)

    # head with helmet or hood
    _circle(surface, SKIN, (cx, cy - 16), 9)
    if role in ("Tank", "Fighter"):
        pygame.draw.arc(surface, _shade(team_rgb, 1.15), pygame.Rect(cx - 10, cy - 26, 20, 18), 0, 180, 6)
    elif role == "Assassin":
        pygame.draw.polygon(surface, _shade(team_rgb, 0.85), [(cx - 10, cy - 16), (cx + 10, cy - 16), (cx + 7, cy - 27), (cx - 7, cy - 27)])
        _line(surface, DARK, (cx - 7, cy - 14), (cx + 7, cy - 14), 4)
    else:
        pygame.draw.arc(surface, _shade(accent, 0.9), pygame.Rect(cx - 10, cy - 25, 20, 16), 10, 170, 5)

    # shield for Tank on left arm
    if role == "Tank":
        pygame.draw.rect(surface, team_rgb, pygame.Rect(cx - 27, cy - 13, 10, 26), border_radius=4)
        pygame.draw.rect(surface, accent, pygame.Rect(cx - 27, cy - 13, 10, 26), 2, border_radius=4)

    _surfaces[key] = surface
    return surface


def hero_portrait(hero_key, role, accent):
    """Square menu portrait with face, headgear, and weapon silhouette."""
    override = _load_override(f"portraits/{hero_key}.png")
    if override:
        return override
    key = ("portrait", hero_key)
    if key in _surfaces:
        return _surfaces[key]
    size = 96
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    accent = _color(accent)
    team = _color(team_color("blue"))
    pygame.draw.rect(surface, _shade(accent, 0.30), (0, 0, size, size))
    for i in range(3):
        pygame.draw.circle(surface, (*_shade(accent, 0.45), 40), (size // 2, size // 2 + 8), 44 - i * 7, 2)

    cx, cy = size / 2, size / 2 + 6
    # shoulders
    pygame.draw.ellipse(surface, team, pygame.Rect(cx - 26, cy + 12, 52, 26))
    pygame.draw.ellipse(surface, _shade(team, 1.25), pygame.Rect(cx - 26, cy + 12, 52, 26), 2)
    # weapon silhouette behind shoulder
    if role in ("Mage", "Support"):
        _line(surface, (120, 90, 60), (cx + 24, cy + 30), (cx + 30, cy - 26), 4)
        _circle(surface, accent, (cx + 30, cy - 30), 8)
    elif role == "Marksman":
        pygame.draw.arc(surface, accent, pygame.Rect(cx + 12, cy - 30, 26, 56), -60, 60, 4)
    elif role == "Assassin":
        _line(surface, (210, 215, 225), (cx + 18, cy + 20), (cx + 30, cy - 24), 4)
    elif role == "Fighter":
        pygame.draw.polygon(surface, accent, [(cx + 28, cy - 34), (cx + 20, cy - 8), (cx + 34, cy - 8)])
        _line(surface, (150, 110, 70), (cx + 27, cy - 8), (cx + 27, cy + 34), 4)
    # head
    _circle(surface, SKIN, (cx, cy - 6), 17)
    _circle(surface, (255, 255, 255), (cx - 6, cy - 8), 4)
    _circle(surface, (255, 255, 255), (cx + 6, cy - 8), 4)
    _circle(surface, DARK, (cx - 6, cy - 8), 2)
    _circle(surface, DARK, (cx + 6, cy - 8), 2)
    pygame.draw.arc(surface, DARK, pygame.Rect(cx - 6, cy + 1, 12, 8), 200, 340, 2)
    # headgear per role
    if role in ("Tank", "Fighter"):
        pygame.draw.arc(surface, team, pygame.Rect(cx - 19, cy - 24, 38, 26), 0, 180, 7)
        pygame.draw.line(surface, accent, (cx, cy - 26), (cx, cy - 18), 3)
    elif role == "Assassin":
        pygame.draw.polygon(surface, _shade(team, 0.85), [(cx - 19, cy - 8), (cx + 19, cy - 8), (cx + 12, cy - 30), (cx - 12, cy - 30)])
        _line(surface, DARK, (cx - 13, cy - 6), (cx + 13, cy - 6), 5)
    else:
        pygame.draw.arc(surface, accent, pygame.Rect(cx - 19, cy - 22, 38, 22), 10, 170, 6)
        pygame.draw.line(surface, accent, (cx - 22, cy - 14), (cx - 28, cy + 2), 3)
        pygame.draw.line(surface, accent, (cx + 22, cy - 14), (cx + 28, cy + 2), 3)
    _surfaces[key] = surface
    return surface


def minion_sprite(kind, team_name, frame=0):
    key = ("minion", kind, team_name, frame)
    if key in _surfaces:
        return _surfaces[key]
    size = 36
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    team = _color(team_color(team_name))
    cx, cy = size / 2, size / 2 + (1 if frame else 0)
    _circle(surface, (0, 0, 0, 60), (cx, size - 5), 7)
    if kind == "ranged":
        pygame.draw.polygon(surface, team, [(cx, cy - 11), (cx - 9, cy + 8), (cx + 9, cy + 8)])
        pygame.draw.polygon(surface, _shade(team, 1.3), [(cx, cy - 11), (cx - 9, cy + 8), (cx + 9, cy + 8)], 2)
        _circle(surface, SKIN, (cx, cy - 1), 4)
    elif kind == "siege":
        pygame.draw.rect(surface, team, pygame.Rect(cx - 12, cy - 8, 24, 16), border_radius=3)
        pygame.draw.rect(surface, _shade(team, 1.3), pygame.Rect(cx - 12, cy - 8, 24, 16), 2, border_radius=3)
        _circle(surface, DARK, (cx - 7, cy + 10), 4)
        _circle(surface, DARK, (cx + 7, cy + 10), 4)
        _circle(surface, (150, 150, 150), (cx - 7, cy + 10), 2)
        _circle(surface, (150, 150, 150), (cx + 7, cy + 10), 2)
    else:
        _circle(surface, team, (cx, cy), 9)
        _circle(surface, _shade(team, 1.3), (cx, cy), 9, 2)
        _circle(surface, _shade(team, 0.6), (cx, cy + 2), 5)
        _line(surface, (200, 205, 215), (cx + 7, cy + 6), (cx + 11, cy - 6), 2)
    _surfaces[key] = surface
    return surface


def monster_sprite(color_value, radius):
    key = ("monster", color_value, round(radius))
    if key in _surfaces:
        return _surfaces[key]
    size = int(radius * 2 + 20)
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    body = _color(color_value)
    cx = cy = size / 2
    _circle(surface, (0, 0, 0, 70), (cx, size - 6), radius * 0.8)
    _circle(surface, body, (cx, cy - 2), radius)
    _circle(surface, _shade(body, 1.35), (cx, cy - 2), radius, 2)
    # horns
    pygame.draw.polygon(surface, _shade(body, 0.7), [(cx - radius * 0.7, cy - radius * 0.5), (cx - radius * 1.0, cy - radius * 1.2), (cx - radius * 0.2, cy - radius * 0.9)])
    pygame.draw.polygon(surface, _shade(body, 0.7), [(cx + radius * 0.7, cy - radius * 0.5), (cx + radius * 1.0, cy - radius * 1.2), (cx + radius * 0.2, cy - radius * 0.9)])
    # eyes
    eye_offset = radius * 0.35
    _circle(surface, (255, 220, 120), (cx - eye_offset, cy - 4), 3)
    _circle(surface, (255, 220, 120), (cx + eye_offset, cy - 4), 3)
    _circle(surface, DARK, (cx - eye_offset, cy - 4), 1)
    _circle(surface, DARK, (cx + eye_offset, cy - 4), 1)
    _surfaces[key] = surface
    return surface


def tower_sprite(team_name, tier):
    key = ("tower", team_name, tier)
    if key in _surfaces:
        return _surfaces[key]
    surface = pygame.Surface((64, 76), pygame.SRCALPHA)
    team = _color(team_color(team_name))
    cx = 32
    # stone base
    pygame.draw.rect(surface, (56, 62, 66), pygame.Rect(cx - 22, 30, 44, 40), border_radius=4)
    pygame.draw.rect(surface, (28, 32, 34), pygame.Rect(cx - 22, 30, 44, 40), 2, border_radius=4)
    for row in range(3):
        for col in range(3):
            pygame.draw.line(surface, (40, 45, 48), (cx - 18 + col * 13, 38 + row * 11), (cx - 6 + col * 13, 38 + row * 11), 2)
    # turret
    pygame.draw.circle(surface, (72, 79, 84), (cx, 30), 16)
    pygame.draw.circle(surface, team, (cx, 30), 16, 3)
    pygame.draw.circle(surface, team, (cx, 30), 7)
    pygame.draw.circle(surface, _shade(team, 1.4), (cx, 30), 3)
    if tier == "base":
        pygame.draw.rect(surface, (247, 215, 101), pygame.Rect(cx - 26, 26, 52, 6), border_radius=3)
    _surfaces[key] = surface
    return surface


def core_sprite(team_name):
    key = ("core", team_name)
    if key in _surfaces:
        return _surfaces[key]
    surface = pygame.Surface((96, 96), pygame.SRCALPHA)
    team = _color(team_color(team_name))
    cx = cy = 48
    _circle(surface, _shade(team, 0.5), (cx, cy), 34)
    _circle(surface, team, (cx, cy), 30)
    _circle(surface, _shade(team, 1.45), (cx, cy), 30, 3)
    pygame.draw.polygon(surface, (245, 241, 215), [(cx, cy - 18), (cx - 14, cy), (cx, cy + 18), (cx + 14, cy)])
    pygame.draw.polygon(surface, _shade(team, 1.8), [(cx, cy - 10), (cx - 7, cy), (cx, cy + 10), (cx + 7, cy)])
    _surfaces[key] = surface
    return surface


def rotate_for_blit(surface, angle, bucket_deg=10):
    """Rotate a north-facing sprite to aim angle (radians); cached in coarse buckets."""
    bucket = int(math.degrees(angle) // bucket_deg)
    key = (id(surface), bucket)
    if key in _rotated:
        return _rotated[key]
    # sprite points north; pygame rotates counterclockwise in degrees
    rotated = pygame.transform.rotate(surface, -math.degrees(angle) - 90)
    _rotated[key] = rotated
    return rotated


def portrait_scaled(hero_key, role, accent, size):
    key = ("portrait_scaled", hero_key, size)
    if key in _rotated:
        return _rotated[key]
    scaled = pygame.transform.smoothscale(hero_portrait(hero_key, role, accent), (size, size))
    _rotated[key] = scaled
    return scaled
