"""Render every screen headlessly and save PNGs to tools/screenshots/.

Run:  python tools/headless_check.py
Uses SDL dummy drivers, so it works without a display (CI-friendly smoke test).
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

from main import MobaGame

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")


def save(game, name):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    pygame.image.save(game.screen, path)
    print("saved", name)


def main():
    game = MobaGame()

    game.draw()
    save(game, "1_language.png")

    game.choose_language("zh")
    game.draw()
    save(game, "2_lobby.png")

    game.state = "select"
    game.mouse_x, game.mouse_y = 300, 300
    game.draw()
    save(game, "3_select_hover.png")

    game.choose_mode("rank")
    game.choose_hero("ranger")
    game.state = "loading"
    game.draw()
    save(game, "4_loading.png")

    game.state = "playing"
    game.last_time = game.now()
    for _ in range(600):
        game.update(1 / 60)
    game.draw()
    save(game, "5_battle.png")

    game.buy_item(list(__import__("equipment_data").ITEMS.keys())[0])
    game.player.x, game.player.y = 130, 580
    game.mouse_x, game.mouse_y = 988, 608
    game.aiming_skill = "q"
    game.draw()
    save(game, "6_battle_aim_shop.png")
    game.aiming_skill = None

    game.show_scoreboard = True
    game.draw()
    save(game, "7_scoreboard.png")
    game.show_scoreboard = False

    for _ in range(7200):
        game.update(1 / 60)
        if game.match_over:
            break
    print("match_over:", game.match_over, "winner:", game.winner, "time:", round(game.match_time, 1))
    game.draw()
    save(game, "8_end_state.png")

    game.match_over = True
    game.winner = "blue"
    game.draw()
    save(game, "9_settlement.png")

    pygame.quit()
    print("OK")


if __name__ == "__main__":
    main()
