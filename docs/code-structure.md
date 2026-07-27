# Code Structure

Run the game from the project root:

```powershell
python main.py
```

`main.py` is the application shell. It creates the Tk window, owns match setup, and calls each subsystem during the game loop.

Subsystem files:

- `rendering.py`: all canvas drawing, HUD, menus, minimap, shop panel, scoreboard, settlement, and skill indicators.
- `input_handler.py`: keyboard and mouse routing, language selection, mode selection, hero selection, shop clicks, utility buttons, and settlement clicks.
- `combat.py`: attacks, target lock, skill leveling, skill casting, damage, control effects, rewards, XP, level-up, combat particles, and kill handling.
- `ai.py`: enemy hero decision making, defense behavior, last-hit targeting, retreat, jungle targeting, and enemy movement.
- `map_systems.py`: minion waves, minion movement, player movement, neutral monsters, towers, cores, death cleanup, respawn, brush visibility, and win checks.
- `economy.py`: base shop range, item purchasing, item requirements, and recommended buying.
- `player_actions.py`: recall, enemy recall, flash, heal, and summoner cooldown checks.
- `game_data.py`: shared data classes, constants, map data, heroes, modes, jungle camps, brush zones, and localization text.
- `equipment_data.py`: equipment definitions and recommended builds.

Keep future changes in the subsystem closest to the behavior. Add shared constants or dataclasses to `game_data.py` only when more than one subsystem needs them.
