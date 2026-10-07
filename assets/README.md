# assets / 素材目录

Game art lives here. Hero, portrait, and jungle-monster sprites are imported from
**Kenney Tiny Dungeon** (CC0, https://kenney.nl/assets/tiny-dungeon) via
`python tools/import_kenney.py` — rerun it any time to regenerate them from the pack.
Other art is generated procedurally by `sprites.py`, and any PNG you place at the
paths below replaces the art for that piece only.

英雄、头像和野怪素材来自 **Kenney Tiny Dungeon**（CC0 许可，可自由商用），由
`python tools/import_kenney.py` 从素材包导入，可随时重跑重新生成。其余素材由
`sprites.py` 程序化生成；按下面的路径放入 PNG 即可逐个替换对应素材。

## Override paths / 覆盖路径

| File | Purpose | Suggested size |
| --- | --- | --- |
| `sprites/heroes/<hero_key>.png` | Battle sprite, frame A, front-facing | 48×50 |
| `sprites/heroes/<hero_key>_b.png` | Battle sprite, frame B (walk bob) | 48×50 |
| `sprites/heroes/<hero_key>_blue.png` / `_red.png` | Team recolor (frame A; add `_b` for frame B) | 48×50 |
| `portraits/<hero_key>.png` | Menu / loading portrait | 96×96 or larger, square |
| `sprites/monsters/<camp_key>.png` | Jungle monster (camp: `blue_grove`, `blue_stone`, `red_grove`, `red_stone`, `ancient_guard`) | square, scaled to camp radius |

`<hero_key>` values: `vanguard`, `ranger`, `arcanist`, `sentinel`, `shade`, `weaver`,
`warden`, `reaver`, `geomancer`, `tempest`.

## Art direction notes / 美术方向说明

- Current characters are Kenney Tiny Dungeon (CC0) — no attribution required, but
  the source and license are documented here in good faith.
- 当前角色来自 Kenney Tiny Dungeon（CC0），无需署名，这里仍记录来源与许可以示规范。
