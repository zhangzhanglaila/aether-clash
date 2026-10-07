# assets / 素材目录

Game art lives here. Everything is **generated procedurally by `sprites.py`** by default,
so this directory can stay empty and the game still runs. Any PNG you place at the paths
below replaces the generated art for that piece only.

素材默认由 `sprites.py` 程序化生成，本目录可以为空。按下面的路径放入 PNG 即可逐个替换对应素材。

## Override paths / 覆盖路径

| File | Purpose | Suggested size |
| --- | --- | --- |
| `sprites/heroes/<hero_key>.png` | Battle sprite, frame A, facing **up** | 64×64 |
| `sprites/heroes/<hero_key>_b.png` | Battle sprite, frame B (walk/attack bob) | 64×64 |
| `sprites/heroes/<hero_key>_blue.png` / `_red.png` | Team recolor (frame A; add `_b` for frame B) | 64×64 |
| `portraits/<hero_key>.png` | Menu / loading portrait | 96×96 or larger, square |

`<hero_key>` values: `vanguard`, `ranger`, `arcanist`, `sentinel`, `shade`, `weaver`,
`warden`, `reaver`, `geomancer`, `tempest`.

## Art direction notes / 美术方向说明

- License check before committing any third-party art: CC0 / purchased pack license only.
  Do not commit art from known IP (game characters, anime, photos) — see
  `docs/appeal-and-retention-plan.md` for the reasoning.
- 提交任何第三方素材前先确认许可：只接受 CC0 或已购买授权的素材包。
  不要提交知名 IP 的图（游戏角色、动漫、真人照片），原因见 `docs/appeal-and-retention-plan.md`。
- Top-down style: sprites face up; the renderer rotates them toward the aim direction.
- 俯视角规范：精灵朝上，渲染层会按瞄准方向旋转。
