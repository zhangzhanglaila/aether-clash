"""Import Kenney Tiny Dungeon (CC0) sprites into the assets/ override pipeline.

Usage:
    python tools/import_kenney.py [path_to_extracted_pack]

The pack (https://kenney.nl/assets/tiny-dungeon, CC0) can be downloaded from
KENNEY_URL; pass a local extracted dir containing Tiles/tile_XXXX.png to skip
the download. Writes battle sprites (with a 2-frame bob), portraits, and
jungle-monster sprites under assets/.
"""
import os
import shutil
import sys
import tempfile
import zipfile
import urllib.request

import pygame

KENNEY_URL = "https://kenney.nl/media/pages/assets/tiny-dungeon/f8422efb44-1674742415/kenney_tiny-dungeon.zip"

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(REPO, "assets")

# hero_key -> 16px tile index in the pack (character picked by role silhouette)
HERO_TILES = {
    "vanguard": 87,   # lance knight      (Fighter)
    "ranger": 112,    # green-hood archer (Marksman)
    "arcanist": 84,   # purple wizard     (Mage)
    "sentinel": 96,   # heavy knight      (Tank)
    "shade": 121,     # ghost             (Assassin, night theme)
    "weaver": 120,    # spider            (Assassin, thread theme)
    "warden": 100,    # white-beard elder (Support)
    "reaver": 86,     # barbarian         (Fighter, blood theme)
    "geomancer": 109, # rock golem        (Mage, earth theme)
    "tempest": 98,    # wind ranger       (Marksman)
}
MONSTER_TILES = {
    "blue_grove": 108,     # slime
    "blue_stone": 123,     # rat
    "red_grove": 110,      # crab
    "red_stone": 122,      # red spider
    "ancient_guard": 124,  # skull
}
# environment tiles: sand ground (clean), blue-gray slat lanes, brick walls,
# cracked dark bricks for jungle zones, and stone patches for the ancient circle
MAP_TILES = {
    "floor_sand_0": 48, "floor_sand_1": 49, "floor_sand_2": 50, "floor_sand_3": 51, "floor_sand_4": 52, "floor_sand_5": 53,
    "floor_lane_0": 36, "floor_lane_1": 37, "floor_lane_2": 38, "floor_lane_3": 40,
    "floor_jungle_0": 12, "floor_jungle_1": 13, "floor_jungle_2": 15, "floor_jungle_3": 24, "floor_jungle_4": 25,
    "wall_0": 57, "wall_1": 58, "wall_2": 59,
    "decor_0": 42, "decor_1": 43,
}
# minion source tiles, tinted per team; melee soldier, ranged archer, siege golem
MINION_TILES = {"melee": 85, "ranged": 112, "siege": 109}
TEAM_TINTS = {"blue": (140, 170, 255), "red": (255, 150, 140)}
# skill slot icons: Q sword, E potion, R wand
SKILL_ICONS = {"q": 106, "e": 116, "r": 130}
TILE = 16
BATTLE_SCALE = 3   # 16 -> 48
PORTRAIT_SCALE = 6 # 16 -> 96


def ensure_pack(source_dir=None):
    if source_dir:
        return os.path.join(source_dir, "Tiles")
    tiles_dir = os.path.join(tempfile.gettempdir(), "kenney_tiny_dungeon", "Tiles")
    if os.path.isdir(tiles_dir) and os.path.isfile(os.path.join(tiles_dir, "tile_0000.png")):
        return tiles_dir
    print("downloading", KENNEY_URL)
    zip_path = os.path.join(tempfile.gettempdir(), "kenney_tiny_dungeon.zip")
    urllib.request.urlretrieve(KENNEY_URL, zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(os.path.dirname(tiles_dir))
    return tiles_dir


def load_tile(tiles_dir, index):
    path = os.path.join(tiles_dir, f"tile_{index:04d}.png")
    surface = pygame.image.load(path)
    if surface.get_size() != (TILE, TILE):
        raise SystemExit(f"unexpected tile size {surface.get_size()} for {path}")
    return surface


def save(surface, rel_path):
    path = os.path.join(ASSETS, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pygame.image.save(surface, path)
    print("wrote", os.path.relpath(path, REPO))


def main():
    source_dir = sys.argv[1] if len(sys.argv) > 1 else None
    pygame.init()
    tiles_dir = ensure_pack(source_dir)

    for hero_key, tile_index in HERO_TILES.items():
        tile = load_tile(tiles_dir, tile_index)
        art = pygame.transform.scale(tile, (TILE * BATTLE_SCALE, TILE * BATTLE_SCALE))
        # 48x50 canvas: frame A sits at y=0, frame B at y=2 for a walk bob
        for frame, offset in ((0, 0), (1, 2)):
            canvas = pygame.Surface((48, 50), pygame.SRCALPHA)
            canvas.blit(art, (0, offset))
            suffix = "_b" if frame else ""
            save(canvas, f"sprites/heroes/{hero_key}{suffix}.png")
        portrait = pygame.transform.scale(tile, (TILE * PORTRAIT_SCALE, TILE * PORTRAIT_SCALE))
        save(portrait, f"portraits/{hero_key}.png")

    for camp_key, tile_index in MONSTER_TILES.items():
        tile = load_tile(tiles_dir, tile_index)
        save(tile, f"sprites/monsters/{camp_key}.png")

    for name, tile_index in MAP_TILES.items():
        tile = load_tile(tiles_dir, tile_index)
        save(tile, f"sprites/map/{name}.png")

    for kind, tile_index in MINION_TILES.items():
        tile = load_tile(tiles_dir, tile_index)
        for team, tint in TEAM_TINTS.items():
            tinted = tile.copy()
            layer = pygame.Surface((TILE, TILE))
            layer.fill(tint)
            tinted.blit(layer, (0, 0), special_flags=pygame.BLEND_MULT)
            art = pygame.transform.scale(tinted, (32, 32))
            for frame, offset in ((0, 0), (1, 2)):
                canvas = pygame.Surface((32, 34), pygame.SRCALPHA)
                canvas.blit(art, (0, offset))
                suffix = "_b" if frame else ""
                save(canvas, f"sprites/minions/{kind}_{team}{suffix}.png")

    for slot, tile_index in SKILL_ICONS.items():
        tile = load_tile(tiles_dir, tile_index)
        icon = pygame.transform.scale(tile, (48, 48))
        save(icon, f"icons/skills/{slot}.png")

    print("done — art is CC0 from Kenney Tiny Dungeon (https://kenney.nl/assets/tiny-dungeon)")


if __name__ == "__main__":
    main()
