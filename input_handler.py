import time

from equipment_data import ITEMS
from game_data import HEROES, L10N, SKILL_UPGRADE_KEYS


class InputMixin:
    def on_key_press(self, event):
        key = event.keysym.lower()
        if self.state == "playing" and key == "tab":
            self.show_scoreboard = True
            return
        if self.state == "language":
            if key in {"1", "c"}:
                self.choose_language("zh")
            elif key in {"2", "e"}:
                self.choose_language("en")
            elif key == "escape":
                self.root.destroy()
            return

        if self.state == "lobby":
            if key in {"1", "2", "3"}:
                self.choose_mode(list(self.mode_configs().keys())[int(key) - 1])
            elif key in {"return", "space"} and self.selected_mode_key:
                self.state = "select"
            elif key == "escape":
                self.root.destroy()
            return

        if self.state == "loading":
            return

        if self.state == "playing" and self.match_over:
            if key == "escape":
                self.root.destroy()
            return

        if self.state == "select":
            if key.isdigit():
                hero_keys = list(HEROES.keys())
                index = int(key) - 1
                if 0 <= index < len(hero_keys):
                    self.choose_hero(hero_keys[index])
            elif key == "escape":
                self.root.destroy()
            return

        if self.state == "playing" and self.recalling:
            if key == "b" or key in {"w", "a", "s", "d", "up", "down", "left", "right", "q", "e", "r", "f", "g", "space", "1", "2", "3", "4", "5", "6", "7", "8", "9", "z", "x", "c", "t"}:
                self.cancel_recall()
            return

        if self.state == "playing" and key == "b":
            self.start_recall()
            return
        if self.state == "playing" and key in SKILL_UPGRADE_KEYS:
            self.upgrade_skill(self.player, SKILL_UPGRADE_KEYS[key])
            return
        if self.state == "playing" and key == "t":
            self.cycle_locked_target()
            return
        if self.state == "playing" and key in {"q", "e", "r"}:
            self.start_aiming_skill(key)
            return

        self.keys.add(key)
        if key == "f":
            self.cast_flash()
        elif key == "g":
            self.cast_heal()
        elif key in {"1", "2", "3", "4", "5", "6", "7", "8", "9"}:
            item_key = list(ITEMS.keys())[int(key) - 1]
            self.buy_item(item_key)
        elif key == "space":
            self.hero_attack(self.player)
        elif key == "escape":
            self.root.destroy()


    def on_key_release(self, event):
        key = event.keysym.lower()
        if key == "tab":
            self.show_scoreboard = False
            return
        if self.state == "playing" and key == self.aiming_skill:
            self.cast_aiming_skill()
        self.keys.discard(event.keysym.lower())


    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y


    def on_left_click(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y
        if self.state == "language":
            self.select_language_at(self.mouse_x, self.mouse_y)
            return
        if self.state == "lobby":
            self.select_lobby_at(self.mouse_x, self.mouse_y)
            return
        if self.state == "loading":
            return
        if self.state == "select":
            self.select_card_at(self.mouse_x, self.mouse_y)
            return
        if self.state == "playing" and self.match_over:
            self.select_settlement_at(self.mouse_x, self.mouse_y)
            return
        if self.state == "playing" and self.recalling:
            self.cancel_recall()
            return
        if self.state == "playing" and self.select_skill_upgrade_at(self.mouse_x, self.mouse_y):
            return
        if self.state == "playing" and self.aiming_skill:
            self.cast_aiming_skill()
            return
        if self.state == "playing" and self.select_utility_at(self.mouse_x, self.mouse_y):
            return
        if self.state == "playing" and self.lock_target_at(self.mouse_x, self.mouse_y):
            return
        if self.select_shop_at(self.mouse_x, self.mouse_y):
            return
        self.hero_attack(self.player)


    def on_right_click(self, _event):
        if self.state != "playing":
            return
        if self.match_over:
            return
        if self.recalling:
            self.cancel_recall()
            return
        if self.aiming_skill:
            self.aiming_skill = None
            return
        self.cast_e(self.player)


    def choose_language(self, language):
        self.language = language
        self.selected_mode_key = None
        self.selected_hero_key = None
        self.state = "lobby"


    def mode_configs(self):
        return {
            "rank": (self.text("mode_rank"), "#78a3ff", L10N[self.language]["mode_desc"]["rank"]),
            "train": (self.text("mode_train"), "#76f4d1", L10N[self.language]["mode_desc"]["train"]),
            "quick": (self.text("mode_quick"), "#b38cff", L10N[self.language]["mode_desc"]["quick"]),
        }


    def choose_mode(self, mode_key):
        self.selected_mode_key = mode_key


    def choose_hero(self, hero_key):
        self.reset_match(hero_key)
        self.state = "loading"
        self.loading_started_at = self.now()
        self.last_time = time.perf_counter()
        self.show_message(self.text("deployed", name=self.hero_name(hero_key)))


    def select_language_at(self, x, y):
        for language, left, top, right, bottom in self.language_buttons:
            if left <= x <= right and top <= y <= bottom:
                self.choose_language(language)
                return


    def select_lobby_at(self, x, y):
        for mode_key, left, top, right, bottom in self.mode_cards:
            if left <= x <= right and top <= y <= bottom:
                self.choose_mode(mode_key)
                return
        for action, left, top, right, bottom in self.lobby_buttons:
            if left <= x <= right and top <= y <= bottom:
                if action == "start" and self.selected_mode_key:
                    self.state = "select"
                return


    def select_card_at(self, x, y):
        for hero_key, left, top, right, bottom in self.hero_cards:
            if left <= x <= right and top <= y <= bottom:
                self.choose_hero(hero_key)
                return


    def select_shop_at(self, x, y):
        if not self.near_shop():
            return False
        if self.recommended_buy_button:
            left, top, right, bottom = self.recommended_buy_button
            if left <= x <= right and top <= y <= bottom:
                return self.buy_recommended_item()
        for item_key, left, top, right, bottom in self.shop_cards:
            if left <= x <= right and top <= y <= bottom:
                return self.buy_item(item_key)
        return False


    def select_utility_at(self, x, y):
        for action, left, top, right, bottom in self.utility_buttons:
            if left <= x <= right and top <= y <= bottom:
                if action == "f":
                    self.cast_flash()
                elif action == "g":
                    self.cast_heal()
                elif action == "b":
                    self.start_recall()
                return True
        return False


    def select_settlement_at(self, x, y):
        for action, left, top, right, bottom in self.settlement_buttons:
            if left <= x <= right and top <= y <= bottom:
                if action == "rematch":
                    self.reset_match(self.selected_hero_key or "vanguard")
                    self.state = "loading"
                    self.loading_started_at = self.now()
                elif action == "lobby":
                    self.state = "lobby"
                    self.selected_mode_key = None
                    self.selected_hero_key = None
                    self.match_over = False
                    self.winner = None
                    self.show_scoreboard = False
                    self.aiming_skill = None
                return True
        return False


    def select_skill_upgrade_at(self, x, y):
        for skill_key, left, top, right, bottom in self.skill_upgrade_buttons:
            if left <= x <= right and top <= y <= bottom:
                return self.upgrade_skill(self.player, skill_key)
        return False

