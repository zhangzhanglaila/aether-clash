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

    print("done — art is CC0 from Kenney Tiny Dungeon (https://kenney.nl/assets/tiny-dungeon)")


if __name__ == "__main__":
    main()
