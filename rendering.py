import math
import random
import tkinter as tk

from equipment_data import HERO_RECOMMENDED_ITEMS, ITEMS
from game_data import (
    BRUSH_ZONES,
    HEIGHT,
    HEROES,
    Hero,
    MODE_RULES,
    RIVER_POLYGON,
    SKILL_MAX_LEVELS,
    WIDTH,
    clamp,
    team_color,
)


class RenderingMixin:
    def draw_skill_preview(self, c):
        if not self.aiming_skill or not self.player or not self.player.alive:
            return
        hero = self.player
        vx, vy = self.aim_vector(hero)
        if self.aiming_skill == "q":
            if hero.hero_key == "ranger":
                angle = math.atan2(vy, vx)
                for offset in (-0.18, 0, 0.18):
                    ax = math.cos(angle + offset)
                    ay = math.sin(angle + offset)
                    c.create_line(hero.x, hero.y, hero.x + ax * 260, hero.y + ay * 260, fill=hero.accent, width=3, dash=(8, 6))
            elif hero.hero_key == "sentinel":
                c.create_oval(hero.x - 72, hero.y - 72, hero.x + 72, hero.y + 72, outline=hero.accent, width=2, dash=(8, 4))
                c.create_line(hero.x, hero.y, hero.x + vx * 150, hero.y + vy * 150, fill=hero.accent, width=3, dash=(8, 6))
            elif hero.hero_key == "arcanist":
                c.create_line(hero.x, hero.y, hero.x + vx * 180, hero.y + vy * 180, fill=hero.accent, width=5, dash=(10, 6))
            elif hero.hero_key == "shade":
                c.create_line(hero.x, hero.y, hero.x + vx * 165, hero.y + vy * 165, fill=hero.accent, width=4, dash=(8, 6))
            elif hero.hero_key == "weaver":
                c.create_line(hero.x, hero.y, hero.x + vx * 240, hero.y + vy * 240, fill=hero.accent, width=3, dash=(7, 5))
                c.create_line(hero.x - vy * 10, hero.y + vx * 10, hero.x + vx * 220 - vy * 10, hero.y + vy * 220 + vx * 10, fill=hero.accent, width=1, dash=(7, 5))
                c.create_line(hero.x + vy * 10, hero.y - vx * 10, hero.x + vx * 220 + vy * 10, hero.y + vy * 220 - vx * 10, fill=hero.accent, width=1, dash=(7, 5))
            else:
                c.create_line(hero.x, hero.y, hero.x + vx * 260, hero.y + vy * 260, fill=hero.accent, width=3, dash=(8, 6))
            end_x = hero.x + vx * 260
            end_y = hero.y + vy * 260
            c.create_oval(end_x - 14, end_y - 14, end_x + 14, end_y + 14, outline=hero.accent, width=2)
        elif self.aiming_skill == "e":
            if hero.hero_key in {"sentinel", "arcanist"}:
                radius = 82 if hero.hero_key == "arcanist" else 94
                c.create_oval(hero.x - radius, hero.y - radius, hero.x + radius, hero.y + radius, outline=hero.accent, width=2, dash=(8, 4))
                c.create_oval(hero.x - 16, hero.y - 16, hero.x + 16, hero.y + 16, outline=hero.accent, width=2)
            else:
                distance = 168 if hero.hero_key == "ranger" else 205 if hero.hero_key == "shade" else 236 if hero.hero_key == "weaver" else 120
                end_x = clamp(hero.x + vx * distance, 35, WIDTH - 35)
                end_y = clamp(hero.y + vy * distance, 35, HEIGHT - 35)
                c.create_line(hero.x, hero.y, end_x, end_y, fill=hero.accent, width=4, dash=(10, 6))
                if hero.hero_key == "weaver":
                    c.create_oval(end_x - 62, end_y - 62, end_x + 62, end_y + 62, outline=hero.accent, width=2, dash=(8, 4))
                else:
                    c.create_oval(end_x - 16, end_y - 16, end_x + 16, end_y + 16, outline=hero.accent, width=2)
        elif self.aiming_skill == "r":
            if hero.hero_key == "ranger":
                angle = math.atan2(vy, vx)
                for offset in (-0.52, -0.39, -0.26, -0.13, 0, 0.13, 0.26, 0.39, 0.52):
                    ax = math.cos(angle + offset)
                    ay = math.sin(angle + offset)
                    c.create_line(hero.x, hero.y, hero.x + ax * 260, hero.y + ay * 260, fill=hero.accent, width=2, dash=(10, 6))
            elif hero.hero_key == "shade":
                c.create_line(hero.x, hero.y, self.mouse_x, self.mouse_y, fill=hero.accent, width=5, dash=(12, 8))
                c.create_oval(self.mouse_x - 34, self.mouse_y - 34, self.mouse_x + 34, self.mouse_y + 34, outline=hero.accent, width=2)
            elif hero.hero_key == "weaver":
                c.create_line(hero.x, hero.y, self.mouse_x, self.mouse_y, fill=hero.accent, width=4, dash=(10, 7))
                c.create_oval(self.mouse_x - 108, self.mouse_y - 108, self.mouse_x + 108, self.mouse_y + 108, outline=hero.accent, width=2, dash=(8, 4))
                c.create_oval(self.mouse_x - 54, self.mouse_y - 54, self.mouse_x + 54, self.mouse_y + 54, outline=hero.accent, width=1, dash=(6, 5))
            else:
                radius = 96 if hero.hero_key == "vanguard" else 120 if hero.hero_key == "arcanist" else 136
                c.create_oval(self.mouse_x - radius, self.mouse_y - radius, self.mouse_x + radius, self.mouse_y + radius, outline=hero.accent, width=2, dash=(8, 4))
                c.create_oval(self.mouse_x - 12, self.mouse_y - 12, self.mouse_x + 12, self.mouse_y + 12, outline=hero.accent, width=2)


    def draw(self):
        c = self.canvas
        c.delete("all")
        if self.state == "language":
            self.draw_language(c)
            return
        if self.state == "lobby":
            self.draw_lobby(c)
            return
        if self.state == "select":
            self.draw_select(c)
            return
        if self.state == "loading":
            self.draw_loading(c)
            return

        self.draw_map(c)
        self.draw_structure_threats(c)
        for core in [self.blue_core, self.red_core]:
            self.draw_core(c, core)
        for tower in self.towers:
            if tower.alive:
                self.draw_tower(c, tower)
        for minion in self.minions:
            self.draw_minion(c, minion)
        for monster in self.neutral_monsters:
            self.draw_neutral_monster(c, monster)
        self.draw_hero(c, self.player)
        if self.hero_visible_to_player(self.enemy_hero):
            self.draw_hero(c, self.enemy_hero)
        for p in self.projectiles:
            c.create_oval(
                p.x - p.radius,
                p.y - p.radius,
                p.x + p.radius,
                p.y + p.radius,
                fill=p.color,
                outline="",
            )
        for e in self.effects:
            alpha_width = max(1, int(5 * e.ttl / e.max_ttl))
            c.create_oval(
                e.x - e.radius,
                e.y - e.radius,
                e.x + e.radius,
                e.y + e.radius,
                outline=e.color,
                width=alpha_width,
            )
        for beam in self.beams:
            width = max(1, int(beam.width * beam.ttl / beam.max_ttl))
            c.create_line(beam.x1, beam.y1, beam.x2, beam.y2, fill=beam.color, width=width, capstyle=tk.ROUND)
        for p in self.particles:
            size = p.radius * (0.7 if p.shrink else 1)
            c.create_oval(
                p.x - size,
                p.y - size,
                p.x + size,
                p.y + size,
                fill=p.color,
                outline="",
            )
        for text in self.float_texts:
            c.create_text(text.x, text.y, text=text.text, fill=text.color, font=("Segoe UI", 11, "bold"))
        self.draw_locked_target(c)
        for index, banner in enumerate(self.banners[-3:]):
            alpha = banner.ttl / banner.max_ttl
            left = WIDTH // 2 - 220
            right = WIDTH // 2 + 220
            top = 120 + index * 58
            bottom = 172
            bottom += index * 58
            fill = "#101416" if alpha > 0.3 else "#0f1416"
            c.create_rectangle(left, top, right, bottom, fill=fill, outline=banner.color, width=2)
            c.create_text(WIDTH // 2, top + 27, text=banner.text, fill=banner.color, font=("Segoe UI", 18, "bold"))
        self.draw_ui(c)

    def draw_language(self, c):
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#14191c", outline="")
        self.draw_menu_backdrop(c)
        c.create_rectangle(0, 0, WIDTH, 118, fill="#0f1416", outline="")
        c.create_text(WIDTH // 2, 42, text="LANGUAGE / 语言", fill="#f5f1d7", font=("Segoe UI", 30, "bold"))
        c.create_text(WIDTH // 2, 78, text="Python MOBA Prototype", fill="#9ea898", font=("Segoe UI", 13))

        self.language_buttons = []
        buttons = [("zh", "中文", "进入中文界面"), ("en", "English", "Use English UI")]
        left = 294
        top = 252
        for index, (language, title, subtitle) in enumerate(buttons):
            x1 = left + index * 272
            x2 = x1 + 218
            y1 = top
            y2 = top + 154
            self.language_buttons.append((language, x1, y1, x2, y2))
            active = x1 <= self.mouse_x <= x2 and y1 <= self.mouse_y <= y2
            outline = "#d8cf9b" if active else "#394043"
            c.create_rectangle(x1, y1, x2, y2, fill="#20282b", outline=outline, width=3)
            c.create_text((x1 + x2) // 2, y1 + 60, text=title, fill="#f5f1d7", font=("Segoe UI", 25, "bold"))
            c.create_text((x1 + x2) // 2, y1 + 102, text=subtitle, fill="#aeb8ad", font=("Segoe UI", 12))

        c.create_rectangle(384, 518, 716, 562, fill="#101416", outline="#394043")
        c.create_text(WIDTH // 2, 540, text="MOBA READY", fill="#d8cf9b", font=("Segoe UI", 13, "bold"))

    def draw_select(self, c):
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#151b1d", outline="")
        self.draw_menu_backdrop(c)
        c.create_rectangle(0, 0, WIDTH, 95, fill="#101416", outline="")
        c.create_text(
            WIDTH // 2,
            38,
            text=self.text("hero_title"),
            fill="#f5f1d7",
            font=("Segoe UI", 28, "bold"),
        )
        c.create_text(
            WIDTH // 2,
            72,
            text=self.text("language_subtitle"),
            fill="#9ea898",
            font=("Segoe UI", 13),
        )

        self.hero_cards = []
        hovered_hero_key = None
        card_w = 198
        card_h = 214
        gap_x = 16
        gap_y = 18
        columns = 5
        start_x = (WIDTH - card_w * columns - gap_x * (columns - 1)) // 2
        start_y = 122
        for index, (hero_key, config) in enumerate(HEROES.items()):
            row = index // columns
            col = index % columns
            left = start_x + col * (card_w + gap_x)
            top = start_y + row * (card_h + gap_y)
            right = left + card_w
            bottom = top + card_h
            self.hero_cards.append((hero_key, left, top, right, bottom))
            active = left <= self.mouse_x <= right and top <= self.mouse_y <= bottom
            if active:
                hovered_hero_key = hero_key
            outline = config["accent"] if active else "#394043"
            c.create_rectangle(left, top, right, bottom, fill="#20282b", outline=outline, width=3)
            c.create_rectangle(left, top, right, top + 52, fill="#161c1f", outline="")
            c.create_text(left + 16, top + 19, text=f"{index + 1}. {self.hero_name(hero_key)}", fill="#f5f1d7", anchor="w", font=("Segoe UI", 12, "bold"), width=150)
            c.create_text(left + 16, top + 40, text=self.hero_role(hero_key), fill=config["accent"], anchor="w", font=("Segoe UI", 9, "bold"))
            self.draw_hero_icon(c, left + 161, top + 88, config)

            stat_y = top + 76
            self.draw_stat(c, left + 16, stat_y, "HP", config["hp"], 760, "#48d06b")
            self.draw_stat(c, left + 16, stat_y + 26, "SPD", config["speed"], 250, "#76b7ff")
            self.draw_stat(c, left + 16, stat_y + 52, "ATK", config["attack_damage"], 45, "#f7d765")
            c.create_text(left + 16, top + 154, text=f"Q {self.hero_skill(hero_key, 'q')}", fill="#cfd6cd", anchor="w", font=("Segoe UI", 8, "bold"), width=164)
            c.create_text(left + 16, top + 172, text=f"E {self.hero_skill(hero_key, 'e')}", fill="#cfd6cd", anchor="w", font=("Segoe UI", 8, "bold"), width=164)
            c.create_text(left + 16, top + 190, text=f"R {self.hero_skill(hero_key, 'r')}", fill="#f5d28a", anchor="w", font=("Segoe UI", 8, "bold"), width=164)
            trait = self.hero_skill_traits(hero_key)
            trait_size = 8 if len(trait) > 24 else 9
            c.create_text(left + 16, top + 208, text=trait, fill=config["accent"], anchor="w", font=("Segoe UI", trait_size, "bold"), width=168)

        if hovered_hero_key:
            accent = HEROES[hovered_hero_key]["accent"]
            c.create_rectangle(182, 568, 918, 692, fill="#101416", outline=accent, width=2)
            c.create_text(
                206,
                588,
                text=f"{self.hero_name(hovered_hero_key)} / {self.hero_role(hovered_hero_key)}",
                fill="#f5f1d7",
                anchor="w",
                font=("Segoe UI", 12, "bold"),
            )
            passive = f"P {self.hero_passive_name(hovered_hero_key)}: {self.hero_passive_detail(hovered_hero_key)}"
            c.create_text(206, 610, text=passive, fill=accent, anchor="w", font=("Segoe UI", 8, "bold"), width=690)
            for index, key in enumerate(("q", "e", "r")):
                detail = f"{key.upper()} {self.hero_skill(hovered_hero_key, key)}: {self.hero_skill_detail(hovered_hero_key, key)}"
                c.create_text(206, 634 + index * 18, text=detail, fill="#cfd6cd", anchor="w", font=("Segoe UI", 8), width=690)
        else:
            c.create_rectangle(358, 610, 742, 656, fill="#101416", outline="#394043")
            c.create_text(WIDTH // 2, 633, text=self.text("choose_hero"), fill="#d8cf9b", font=("Segoe UI", 13, "bold"))

    def draw_lobby(self, c):
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#12181b", outline="")
        self.draw_menu_backdrop(c)
        c.create_rectangle(0, 0, WIDTH, 82, fill="#0d1215", outline="")
        c.create_text(34, 30, text=self.text("lobby_title"), fill="#f5f1d7", anchor="w", font=("Segoe UI", 25, "bold"))
        c.create_text(36, 58, text=self.text("lobby_subtitle"), fill="#aeb8ad", anchor="w", font=("Segoe UI", 11))
        c.create_text(WIDTH - 34, 30, text=self.text("profile"), fill="#f7d765", anchor="e", font=("Segoe UI", 13, "bold"))
        c.create_text(WIDTH - 34, 58, text=self.text("season"), fill="#cfd6cd", anchor="e", font=("Segoe UI", 12))

        c.create_rectangle(44, 122, 342, 254, fill="#20282b", outline="#d8cf9b", width=2)
        c.create_text(72, 154, text=self.text("profile"), fill="#f5f1d7", anchor="w", font=("Segoe UI", 15, "bold"))
        mode_name = self.mode_configs()[self.selected_mode_key][0] if self.selected_mode_key else self.text("mode_unselected")
        c.create_text(72, 188, text=mode_name, fill="#78a3ff", anchor="w", font=("Segoe UI", 18, "bold"))
        c.create_text(72, 222, text=self.text("hero_unselected"), fill="#aeb8ad", anchor="w", font=("Segoe UI", 12))

        self.mode_cards = []
        mode_layout = [
            ("rank", 404, 132, 666, 284),
            ("train", 696, 132, 958, 284),
            ("quick", 404, 318, 666, 470),
        ]
        mode_configs = self.mode_configs()
        for mode_key, left, top, right, bottom in mode_layout:
            title, color, desc = mode_configs[mode_key]
            selected = self.selected_mode_key == mode_key
            hovered = left <= self.mouse_x <= right and top <= self.mouse_y <= bottom
            outline = "#f5f1d7" if selected else color if hovered else "#394043"
            fill = "#27343a" if selected else "#20282b"
            self.mode_cards.append((mode_key, left, top, right, bottom))
            c.create_rectangle(left, top, right, bottom, fill=fill, outline=outline, width=3 if selected else 2)
            c.create_rectangle(left, top, right, top + 38, fill="#151b1e", outline="")
            c.create_text(left + 22, top + 20, text=title, fill="#f5f1d7", anchor="w", font=("Segoe UI", 15, "bold"))
            c.create_text(left + 22, top + 62, text=desc, fill="#cfd6cd", anchor="w", font=("Segoe UI", 9), width=right - left - 42)
            c.create_text(left + 22, top + 102, text=self.mode_rule_summary(mode_key), fill="#d8cf9b", anchor="w", font=("Segoe UI", 8, "bold"), width=right - left - 42)
            c.create_line(left + 24, bottom - 22, right - 24, top + 118, fill=color, width=5)
            c.create_oval(right - 74, bottom - 78, right - 24, bottom - 28, fill=color, outline="")

        self.lobby_buttons = [("start", 408, 548, 692, 616)]
        button_fill = "#d8cf9b" if self.selected_mode_key else "#4b4f4b"
        text_fill = "#101416" if self.selected_mode_key else "#aeb8ad"
        c.create_rectangle(408, 548, 692, 616, fill=button_fill, outline="#f5f1d7", width=3)
        c.create_text(WIDTH // 2, 582, text=self.text("start_match"), fill=text_fill, font=("Segoe UI", 21, "bold"))
        c.create_text(WIDTH // 2, 642, text=self.text("mode_prompt"), fill="#aeb8ad", font=("Segoe UI", 12))

    def draw_loading(self, c):
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#101416", outline="")
        self.draw_menu_backdrop(c)
        progress = clamp((self.now() - self.loading_started_at) / 1.15, 0, 1)
        enemy_key = self.enemy_hero.hero_key if self.enemy_hero else "vanguard"
        c.create_text(WIDTH // 2, 86, text=self.text("loading"), fill="#f5f1d7", font=("Segoe UI", 26, "bold"))
        c.create_rectangle(184, 154, 456, 514, fill="#20282b", outline=self.player.accent, width=3)
        c.create_rectangle(644, 154, 916, 514, fill="#20282b", outline="#e84d4f", width=3)
        self.draw_hero_portrait(c, 320, 300, HEROES[self.player.hero_key])
        self.draw_hero_portrait(c, 780, 300, HEROES[enemy_key])
        c.create_text(320, 430, text=self.hero_name(self.player.hero_key), fill="#f5f1d7", font=("Segoe UI", 20, "bold"))
        c.create_text(780, 430, text=self.text("enemy_prefix", name=self.hero_name(enemy_key)), fill="#f5f1d7", font=("Segoe UI", 20, "bold"))
        c.create_text(WIDTH // 2, 320, text=self.text("versus"), fill="#d8cf9b", font=("Segoe UI", 28, "bold"))
        c.create_rectangle(260, 590, 840, 606, fill="#252a2a", outline="")
        c.create_rectangle(260, 590, 260 + 580 * progress, 606, fill="#d8cf9b", outline="")

    def mode_rule_summary(self, mode_key):
        rule = MODE_RULES[mode_key]
        structure_mult = min(rule["tower_hp_mult"], rule["core_hp_mult"])
        return self.text(
            "mode_rule_summary",
            wave=f"{rule['spawn_interval']:.1f}",
            gold=f"{rule['gold_mult']:.2g}",
            xp=f"{rule['xp_mult']:.2g}",
            structure=f"{structure_mult:.2g}",
        )

    def draw_menu_backdrop(self, c):
        for path in self.paths.values():
            points = []
            for x, y in path:
                points.extend([x, y])
            c.create_line(*points, fill="#263139", width=62, capstyle=tk.ROUND, joinstyle=tk.ROUND)
            c.create_line(*points, fill="#3f4b4e", width=28, capstyle=tk.ROUND, joinstyle=tk.ROUND)
        c.create_oval(-90, HEIGHT - 160, 230, HEIGHT + 160, fill="#203f5f", outline="")
        c.create_oval(WIDTH - 230, -160, WIDTH + 90, 160, fill="#5b2428", outline="")
        for i in range(18):
            rng = random.Random(100 + i)
            x = rng.randint(80, WIDTH - 80)
            y = rng.randint(130, HEIGHT - 80)
            c.create_rectangle(x - 18, y - 2, x + 18, y + 2, fill="#2d3939", outline="")

    def draw_hero_portrait(self, c, x, y, config):
        accent = config["accent"]
        c.create_oval(x - 54, y - 54, x + 54, y + 54, fill="#14191c", outline=accent, width=4)
        c.create_polygon(x, y - 48, x - 45, y + 38, x + 45, y + 38, fill=accent, outline="#f5f1d7", width=2)
        c.create_oval(x - 24, y - 20, x + 24, y + 28, fill="#1f282c", outline="")
        c.create_line(x - 62, y + 68, x + 62, y + 68, fill=accent, width=3)

    def draw_hero_icon(self, c, x, y, config):
        accent = config["accent"]
        c.create_oval(x - 36, y - 36, x + 36, y + 36, fill="#14191c", outline=accent, width=3)
        c.create_polygon(x, y - 30, x - 28, y + 24, x + 28, y + 24, fill=accent, outline="#f5f1d7", width=1)
        c.create_oval(x - 14, y - 10, x + 14, y + 18, fill="#1f282c", outline="")

    def draw_stat(self, c, x, y, label, value, max_value, color):
        c.create_text(x, y, text=label, fill="#f5f1d7", anchor="w", font=("Segoe UI", 10, "bold"))
        c.create_rectangle(x + 48, y - 6, x + 224, y + 6, fill="#151b1d", outline="")
        pct = clamp(value / max_value, 0, 1)
        c.create_rectangle(x + 48, y - 6, x + 48 + 176 * pct, y + 6, fill=color, outline="")
        c.create_text(x + 234, y, text=str(int(value)), fill="#cfd6cd", anchor="w", font=("Segoe UI", 10))

    def draw_map(self, c):
        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#17291f", outline="")
        river_points = []
        for x, y in RIVER_POLYGON:
            river_points.extend([x, y])
        c.create_polygon(*river_points, fill="#234a55", outline="#3f737c", width=2)
        jungle_zones = [
            (250, 430, 410, 588, "#1e3c2b"),
            (350, 174, 510, 328, "#1f3f34"),
            (690, 112, 850, 270, "#1e3c2b"),
            (590, 374, 750, 530, "#1f3f34"),
        ]
        for x1, y1, x2, y2, color in jungle_zones:
            c.create_oval(x1, y1, x2, y2, fill=color, outline="#365640", width=2)
        c.create_oval(486, 288, 614, 412, fill="#2d3a2a", outline="#d8cf9b", width=2)
        for left, top, right, bottom in BRUSH_ZONES:
            c.create_rectangle(left, top, right, bottom, fill="#123722", outline="#3f6b42", width=2)
            for i in range(6):
                x = left + 12 + i * ((right - left - 24) / 5)
                c.create_line(x, bottom - 4, x + 8, top + 8, fill="#5a8b53", width=2)
        for lane, path in self.paths.items():
            points = []
            for x, y in path:
                points.extend([x, y])
            c.create_line(*points, fill="#56624d", width=54, capstyle=tk.ROUND, joinstyle=tk.ROUND)
            c.create_line(*points, fill="#8d8b73", width=34, capstyle=tk.ROUND, joinstyle=tk.ROUND)
            c.create_line(*points, fill="#c0b988", width=3, dash=(12, 14))

        for _ in range(28):
            rng = random.Random(_)
            x = rng.randint(40, WIDTH - 40)
            y = rng.randint(45, HEIGHT - 45)
            c.create_oval(x - 8, y - 5, x + 8, y + 5, fill="#203c2d", outline="")

        c.create_polygon(0, HEIGHT, 0, 505, 188, HEIGHT, fill="#203f5f", outline="")
        c.create_polygon(WIDTH, 0, WIDTH, 195, 912, 0, fill="#5b2428", outline="")

    def draw_bar(self, c, x, y, width, hp, max_hp, color):
        pct = 0 if max_hp <= 0 else clamp(hp / max_hp, 0, 1)
        c.create_rectangle(x, y, x + width, y + 6, fill="#252a2a", outline="")
        c.create_rectangle(x, y, x + width * pct, y + 6, fill=color, outline="")

    def draw_structure_threats(self, c):
        structures = [structure for structure in self.towers + [self.blue_core, self.red_core] if structure.alive]
        for structure in structures:
            target = self.nearest_enemy(structure, structure.attack_range, include_cores=False)
            if not target or isinstance(target, Hero) and not self.hero_visible_to_player(target):
                target = None
            is_player_target = target is self.player
            is_visible_enemy_target = target is self.enemy_hero and self.hero_visible_to_player(self.enemy_hero)
            player_in_enemy_range = (
                self.player.alive
                and structure.team != self.player.team
                and math.hypot(structure.x - self.player.x, structure.y - self.player.y) <= structure.attack_range
            )
            if not player_in_enemy_range and not is_player_target and not is_visible_enemy_target:
                continue
            color = "#ffb0aa" if structure.team == "red" else "#8fd3ff"
            r = structure.attack_range
            width = 2 if is_player_target or is_visible_enemy_target else 1
            c.create_oval(structure.x - r, structure.y - r, structure.x + r, structure.y + r, outline=color, width=width, dash=(12, 8))
            if not target:
                continue
            c.create_line(structure.x, structure.y, target.x, target.y, fill=color, width=2, dash=(8, 5))
            lock_r = target.radius + 22
            c.create_oval(target.x - lock_r, target.y - lock_r, target.x + lock_r, target.y + lock_r, outline=color, width=2)
            if is_player_target:
                c.create_text(target.x, target.y - 104, text=self.text("structure_targeted"), fill=color, font=("Segoe UI", 8, "bold"))

    def draw_core(self, c, core):
        color = team_color(core.team)
        c.create_oval(
            core.x - core.radius,
            core.y - core.radius,
            core.x + core.radius,
            core.y + core.radius,
            fill=color,
            outline="#f5f1d7",
            width=3,
        )
        c.create_oval(core.x - 14, core.y - 14, core.x + 14, core.y + 14, fill="#f5f1d7", outline="")
        self.draw_bar(c, core.x - 42, core.y - 50, 84, core.hp, core.max_hp, "#48d06b")

    def draw_tower(self, c, tower):
        color = team_color(tower.team)
        x, y, r = tower.x, tower.y, tower.radius
        c.create_rectangle(x - r, y - r, x + r, y + r, fill="#2e3335", outline=color, width=3)
        if tower.tier == "base":
            c.create_rectangle(x - r + 5, y - r + 5, x + r - 5, y + r - 5, outline="#f7d765", width=2)
        c.create_polygon(x, y - r - 16, x - 18, y, x + 18, y, fill=color, outline="#f5f1d7")
        self.draw_bar(c, x - 30, y - 38, 60, tower.hp, tower.max_hp, "#48d06b")

    def draw_minion(self, c, minion):
        color = team_color(minion.team)
        outline = "#f7d765" if minion.empowered else "#15191b"
        width = 3 if minion.empowered else 2
        if minion.kind == "ranged":
            c.create_polygon(
                minion.x,
                minion.y - minion.radius - 2,
                minion.x - minion.radius - 1,
                minion.y + minion.radius,
                minion.x + minion.radius + 1,
                minion.y + minion.radius,
                fill=color,
                outline=outline,
                width=width,
            )
        elif minion.kind == "siege":
            r = minion.radius
            c.create_rectangle(minion.x - r - 4, minion.y - r, minion.x + r + 4, minion.y + r, fill=color, outline=outline, width=width)
            c.create_oval(minion.x - r - 8, minion.y + r - 5, minion.x - r + 2, minion.y + r + 5, fill="#101416", outline="")
            c.create_oval(minion.x + r - 2, minion.y + r - 5, minion.x + r + 8, minion.y + r + 5, fill="#101416", outline="")
        else:
            c.create_oval(
                minion.x - minion.radius,
                minion.y - minion.radius,
                minion.x + minion.radius,
                minion.y + minion.radius,
                fill=color,
                outline=outline,
                width=width,
            )
        if minion.empowered:
            c.create_oval(minion.x - minion.radius - 8, minion.y - minion.radius - 8, minion.x + minion.radius + 8, minion.y + minion.radius + 8, outline="#f7d765", width=1, dash=(4, 4))
        self.draw_bar(c, minion.x - 18, minion.y - minion.radius - 12, 36, minion.hp, minion.max_hp, "#48d06b")

    def draw_neutral_monster(self, c, monster):
        if not monster.alive:
            if monster.respawn_at:
                left = max(0, int(monster.respawn_at - self.now() + 1))
                c.create_oval(monster.x - 20, monster.y - 20, monster.x + 20, monster.y + 20, fill="#12181b", outline="#394043", width=2)
                c.create_text(monster.x, monster.y, text=str(left), fill="#d8cf9b", font=("Segoe UI", 10, "bold"))
            return
        r = monster.radius
        c.create_oval(monster.x - r - 8, monster.y - r - 8, monster.x + r + 8, monster.y + r + 8, fill="#101416", outline=monster.color, width=2)
        c.create_oval(monster.x - r, monster.y - r, monster.x + r, monster.y + r, fill=monster.color, outline="#f5f1d7", width=2)
        c.create_oval(monster.x - 8, monster.y - 8, monster.x + 8, monster.y + 8, fill="#20282b", outline="")
        self.draw_bar(c, monster.x - 34, monster.y - r - 18, 68, monster.hp, monster.max_hp, "#48d06b")

    def draw_hero(self, c, hero):
        if not hero.alive:
            x, y = (130, 580) if hero.team == "blue" else (965, 120)
            left = max(0, int(hero.respawn_at - self.now() + 1))
            c.create_text(x, y - 38, text=str(left), fill="#ffffff", font=("Segoe UI", 18, "bold"))
            return
        color = team_color(hero.team)
        angle = math.atan2(self.mouse_y - hero.y, self.mouse_x - hero.x) if hero.team == "blue" else 0
        pts = []
        for i, spread in enumerate([0, 2.35, -2.35]):
            length = 25 if i == 0 else 18
            pts.extend([hero.x + math.cos(angle + spread) * length, hero.y + math.sin(angle + spread) * length])
        c.create_polygon(*pts, fill=color, outline=hero.accent, width=3)
        c.create_oval(hero.x - 10, hero.y - 10, hero.x + 10, hero.y + 10, fill="#1a2024", outline="")
        if self.hero_in_brush(hero):
            c.create_oval(hero.x - 30, hero.y - 30, hero.x + 30, hero.y + 30, outline="#76f4a0", width=2, dash=(6, 5))
        if hero.shield > 0:
            c.create_oval(hero.x - 34, hero.y - 34, hero.x + 34, hero.y + 34, outline="#8fd3ff", width=2)
        if self.is_stunned(hero):
            c.create_text(hero.x, hero.y - 82, text="STUN", fill="#f7d765", font=("Segoe UI", 8, "bold"))
        elif self.now() < hero.slowed_until:
            c.create_text(hero.x, hero.y - 82, text="SLOW", fill="#9ad7ff", font=("Segoe UI", 8, "bold"))
        if hero is self.enemy_hero and self.enemy_recalling:
            pct = clamp(self.enemy_recall_elapsed / self.recall_duration, 0, 1)
            c.create_rectangle(hero.x - 42, hero.y - 96, hero.x + 42, hero.y - 84, fill="#0d1215", outline="#ffb0aa")
            c.create_rectangle(hero.x - 38, hero.y - 92, hero.x - 38 + 76 * pct, hero.y - 88, fill="#ffb0aa", outline="")
            c.create_text(hero.x, hero.y - 106, text=self.text("recall_start"), fill="#ffb0aa", font=("Segoe UI", 8, "bold"))
        self.draw_hero_plate(c, hero)

    def draw_hero_plate(self, c, hero):
        display_name = self.hero_name(hero.hero_key)
        if hero.team == "red":
            display_name = self.text("enemy_prefix", name=display_name)
        x = hero.x
        y = hero.y - 58
        c.create_rectangle(x - 54, y - 12, x + 54, y + 23, fill="#101416", outline="#2f383b")
        c.create_oval(x - 61, y - 14, x - 31, y + 16, outline=hero.accent, width=2)
        c.create_oval(x - 58, y - 11, x - 34, y + 13, fill=hero.accent, outline="#f5f1d7", width=1)
        c.create_text(x - 46, y + 1, text=str(hero.level), fill="#111719", font=("Segoe UI", 10, "bold"))
        name_size = 8 if len(display_name) > 10 else 9
        c.create_text(x - 28, y - 1, text=display_name, fill="#f5f1d7", anchor="w", font=("Segoe UI", name_size, "bold"))
        self.draw_bar(c, x - 32, y + 14, 74, hero.hp, hero.max_hp, "#48d06b")

    def draw_ui(self, c):
        self.skill_upgrade_buttons = []
        self.utility_buttons = []
        self.skill_detail_buttons = []
        c.create_rectangle(0, 0, WIDTH, 50, fill="#0d1215", outline="")
        c.create_rectangle(398, 7, 702, 43, fill="#151b1e", outline="#394043", width=2)
        c.create_text(438, 25, text=str(self.player.kills), fill="#78a3ff", font=("Segoe UI", 16, "bold"))
        c.create_text(WIDTH // 2, 25, text=self.format_time(self.match_time), fill="#f5f1d7", font=("Segoe UI", 14, "bold"))
        c.create_text(662, 25, text=str(self.enemy_hero.kills), fill="#ff7b7c", font=("Segoe UI", 16, "bold"))
        c.create_text(24, 25, text=self.hero_name(self.player.hero_key), fill="#78a3ff", anchor="w", font=("Segoe UI", 13, "bold"))
        c.create_text(164, 25, text=f"{self.text('level')} {self.player.level}", fill="#f5f1d7", anchor="w", font=("Segoe UI", 13))
        c.create_text(260, 25, text=f"G {self.player.gold}", fill="#f7d765", anchor="w", font=("Segoe UI", 13))
        xp_pct = clamp(self.player.xp / self.player.next_xp, 0, 1)
        c.create_rectangle(24, 43, 300, 47, fill="#252a2a", outline="")
        c.create_rectangle(24, 43, 24 + 276 * xp_pct, 47, fill="#b38cff", outline="")
        if self.player.skill_points > 0:
            c.create_text(720, 25, text=f"{self.text('skill_points')} {self.player.skill_points}", fill="#f7d765", anchor="w", font=("Segoe UI", 12, "bold"))
        enemy_text = f"{self.hero_name(self.enemy_hero.hero_key)}  {self.text('level')} {self.enemy_hero.level}  G {self.enemy_hero.gold}"
        c.create_text(WIDTH - 24, 23, text=enemy_text, fill="#ff7b7c", anchor="e", font=("Segoe UI", 12, "bold"))

        self.draw_minimap(c)
        self.draw_virtual_stick(c)
        self.draw_skill_preview(c)
        self.draw_utility_row(c)
        self.draw_skill(c, WIDTH - 112, HEIGHT - 92, "Q", self.player.cooldowns["q"], self.skill_cooldown(self.player, "q"), 46, "q")
        self.draw_skill(c, WIDTH - 58, HEIGHT - 154, "E", self.player.cooldowns["e"], self.skill_cooldown(self.player, "e"), 46, "e")
        self.draw_skill(c, WIDTH - 172, HEIGHT - 154, "R", self.player.cooldowns["r"], self.skill_cooldown(self.player, "r"), 52, "r")
        self.draw_skill(c, WIDTH - 58, HEIGHT - 70, "A", self.player.next_attack, self.player.attack_cd, 42)
        self.draw_skill_tooltip(c)

        if self.now() < self.message_until:
            c.create_rectangle(386, 54, 714, 80, fill="#101416", outline="#394043")
            c.create_text(WIDTH // 2, 67, text=self.message, fill="#f5f1d7", font=("Segoe UI", 11, "bold"))

        if self.recalling:
            self.draw_recall_indicator(c)

        if self.near_shop():
            self.draw_shop(c)

        if self.show_scoreboard:
            self.draw_scoreboard(c)

        if self.tutorial_visible and not self.match_over:
            self.draw_tutorial(c)

        if self.match_over:
            self.draw_settlement(c)

    def format_time(self, seconds):
        total = int(seconds)
        return f"{total // 60:02d}:{total % 60:02d}"

    def draw_virtual_stick(self, c):
        x, y = 92, HEIGHT - 92
        c.create_oval(x - 62, y - 62, x + 62, y + 62, fill="#0d1215", outline="#394043", width=2)
        c.create_oval(x - 28, y - 28, x + 28, y + 28, fill="#1f2a2e", outline="#d8cf9b", width=2)
        c.create_line(x - 50, y, x + 50, y, fill="#394043", width=2)
        c.create_line(x, y - 50, x, y + 50, fill="#394043", width=2)

    def draw_utility_row(self, c):
        y = HEIGHT - 38
        items = [
            ("f", WIDTH // 2 - 58, "F", self.summoner_cooldowns["f"], self.summoner_cd_durations["f"]),
            ("g", WIDTH // 2, "G", self.summoner_cooldowns["g"], self.summoner_cd_durations["g"]),
            ("b", WIDTH // 2 + 58, "B", 0, 1),
        ]
        for action, x, label, ready_at, full_cd in items:
            size = 34
            self.utility_buttons.append((action, x - size // 2 - 4, y - size // 2 - 4, x + size // 2 + 4, y + size // 2 + 4))
            self.draw_skill(c, x, y, label, ready_at, full_cd, size)
            if action == "b" and self.recalling:
                c.create_oval(x - 23, y - 23, x + 23, y + 23, outline="#d8cf9b", width=2, dash=(5, 4))

    def draw_recall_indicator(self, c):
        pct = clamp(self.recall_elapsed / self.recall_duration, 0, 1)
        c.create_rectangle(372, 60, 728, 96, fill="#0d1215", outline="#d8cf9b", width=2)
        c.create_text(WIDTH // 2, 71, text=self.text("recall_start"), fill="#d8cf9b", font=("Segoe UI", 13, "bold"))
        c.create_rectangle(432, 78, 668, 88, fill="#252a2a", outline="")
        c.create_rectangle(432, 78, 432 + 236 * pct, 88, fill="#d8cf9b", outline="")
        c.create_text(WIDTH // 2, 103, text=f"{int((1 - pct) * self.recall_duration) + 1}", fill="#ffffff", font=("Segoe UI", 8, "bold"))
        if self.player.alive:
            x, y = self.player.x, self.player.y - 84
            c.create_rectangle(x - 46, y - 10, x + 46, y + 8, fill="#0d1215", outline="#d8cf9b")
            c.create_rectangle(x - 42, y - 6, x - 42 + 84 * pct, y + 4, fill="#d8cf9b", outline="")

    def draw_minimap(self, c):
        left, top = 18, 64
        w, h = 178, 122
        c.create_rectangle(left, top, left + w, top + h, fill="#0d1215", outline="#d8cf9b", width=2)
        for path in self.paths.values():
            points = []
            for x, y in path:
                points.extend([left + x / WIDTH * w, top + y / HEIGHT * h])
            c.create_line(*points, fill="#8d8b73", width=4, capstyle=tk.ROUND, joinstyle=tk.ROUND)
        for tower in self.towers:
            if tower.alive:
                self.draw_minimap_dot(c, left, top, w, h, tower.x, tower.y, team_color(tower.team), 3)
        for minion in self.minions[::2]:
            self.draw_minimap_dot(c, left, top, w, h, minion.x, minion.y, team_color(minion.team), 2)
        for monster in self.neutral_monsters:
            color = monster.color if monster.alive else "#4a4f4d"
            radius = 5 if monster.camp_key == "ancient_guard" else 3
            self.draw_minimap_dot(c, left, top, w, h, monster.x, monster.y, color, radius)
            if not monster.alive and monster.respawn_at:
                mx = left + monster.x / WIDTH * w
                my = top + monster.y / HEIGHT * h
                remaining = max(0, int(monster.respawn_at - self.now() + 1))
                c.create_text(mx, my - 8, text=str(remaining), fill="#d8cf9b", font=("Segoe UI", 6, "bold"))
        self.draw_minimap_dot(c, left, top, w, h, self.blue_core.x, self.blue_core.y, "#78a3ff", 5)
        self.draw_minimap_dot(c, left, top, w, h, self.red_core.x, self.red_core.y, "#ff7b7c", 5)
        if self.player.alive:
            self.draw_minimap_dot(c, left, top, w, h, self.player.x, self.player.y, "#ffffff", 4)
        if self.enemy_hero.alive and self.hero_visible_to_player(self.enemy_hero):
            self.draw_minimap_dot(c, left, top, w, h, self.enemy_hero.x, self.enemy_hero.y, "#ffb0aa", 4)

    def draw_minimap_dot(self, c, left, top, w, h, x, y, color, r):
        mx = left + x / WIDTH * w
        my = top + y / HEIGHT * h
        c.create_oval(mx - r, my - r, mx + r, my + r, fill=color, outline="")

    def draw_locked_target(self, c):
        target = self.valid_locked_target(self.player)
        if not target:
            return
        if isinstance(target, Hero) and not self.hero_visible_to_player(target):
            return
        r = target.radius + 16
        c.create_oval(target.x - r, target.y - r, target.x + r, target.y + r, outline="#f7d765", width=2, dash=(7, 5))
        c.create_line(target.x - r - 8, target.y, target.x - r + 6, target.y, fill="#f7d765", width=2)
        c.create_line(target.x + r - 6, target.y, target.x + r + 8, target.y, fill="#f7d765", width=2)
        c.create_line(target.x, target.y - r - 8, target.x, target.y - r + 6, fill="#f7d765", width=2)
        c.create_line(target.x, target.y + r - 6, target.x, target.y + r + 8, fill="#f7d765", width=2)

    def draw_shop(self, c):
        self.shop_cards = []
        self.recommended_buy_button = None
        left = WIDTH - 404
        top = HEIGHT - 356
        c.create_rectangle(left, top, WIDTH - 24, HEIGHT - 84, fill="#111719", outline="#d8cf9b", width=2)
        c.create_text(left + 18, top + 20, text=self.text("shop"), fill="#f5f1d7", anchor="w", font=("Segoe UI", 13, "bold"))
        bx1, by1, bx2, by2 = WIDTH - 158, top + 9, WIDTH - 38, top + 33
        self.recommended_buy_button = (bx1, by1, bx2, by2)
        c.create_rectangle(bx1, by1, bx2, by2, fill="#20282b", outline="#f7d765", width=2)
        c.create_text((bx1 + bx2) / 2, (by1 + by2) / 2, text=self.text("buy_recommended"), fill="#f5f1d7", font=("Segoe UI", 9, "bold"))
        recommended = set(HERO_RECOMMENDED_ITEMS.get(self.player.hero_key, []))
        for index, (item_key, item) in enumerate(ITEMS.items()):
            col = index % 3
            row = index // 3
            x1 = left + 14 + col * 122
            y1 = top + 42 + row * 52
            x2 = x1 + 112
            y2 = y1 + 44
            self.shop_cards.append((item_key, x1, y1, x2, y2))
            current_level = self.player.equipment[item_key]
            cost = item["cost"] + current_level * 70
            maxed = current_level >= item["max_stacks"]
            missing_item = self.missing_item_requirement(self.player, item)
            locked = missing_item is not None
            fill = "#20282b" if not maxed and not locked else "#181d1f"
            outline = "#f7d765" if item_key in recommended and not maxed else item["color"]
            c.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, width=2)
            c.create_rectangle(x1 + 8, y1 + 10, x1 + 24, y1 + 26, fill=item["color"], outline="")
            c.create_text(x1 + 30, y1 + 13, text=self.item_name(item_key), fill="#f5f1d7", anchor="w", font=("Segoe UI", 8, "bold"))
            c.create_text(x1 + 30, y1 + 28, text=self.item_stat_text(item), fill="#cfd6cd", anchor="w", font=("Segoe UI", 7))
            price = "MAX" if maxed else self.item_name(missing_item) if locked else f"G {cost}"
            c.create_text(x1 + 8, y2 - 6, text=f"Lv {current_level}/{item['max_stacks']}", fill="#9ea898", anchor="w", font=("Segoe UI", 7))
            c.create_text(x2 - 6, y2 - 6, text=price, fill="#f7d765", anchor="e", font=("Segoe UI", 8, "bold"))
        self.draw_shop_detail(c)

    def item_stat_text(self, item):
        parts = []
        if item.get("attack_damage"):
            parts.append(f"+{item['attack_damage']} {self.text('stat_attack')}")
        if item.get("skill_power"):
            parts.append(f"+{item['skill_power']} {self.text('stat_skill')}")
        if item.get("max_hp"):
            parts.append(f"+{item['max_hp']} {self.text('stat_hp')}")
        if item.get("speed"):
            parts.append(f"+{item['speed']} {self.text('stat_speed')}")
        if item.get("attack_range"):
            parts.append(f"+{item['attack_range']} {self.text('stat_range')}")
        if item.get("attack_cd_reduce"):
            parts.append(f"+{int(item['attack_cd_reduce'] * 100)} {self.text('stat_haste')}")
        passive_key = item.get("passive")
        if passive_key:
            parts.append(self.text(f"passive_{passive_key}"))
        return " / ".join(parts[:2]) if parts else "-"

    def draw_shop_detail(self, c):
        hovered = None
        for item_key, left, top, right, bottom in self.shop_cards:
            if left <= self.mouse_x <= right and top <= self.mouse_y <= bottom:
                hovered = item_key
                break
        if not hovered:
            return
        item = ITEMS[hovered]
        left = WIDTH - 644
        top = HEIGHT - 356
        right = left + 216
        bottom = top + 134
        c.create_rectangle(left, top, right, bottom, fill="#101416", outline=item["color"], width=2)
        c.create_text(left + 14, top + 18, text=self.item_name(hovered), fill="#f5f1d7", anchor="w", font=("Segoe UI", 12, "bold"))
        c.create_text(left + 14, top + 44, text=f"{self.text('equipment_stats')}: {self.full_item_stat_text(item)}", fill="#cfd6cd", anchor="w", font=("Segoe UI", 9), width=188)
        y = top + 78
        missing_item = self.missing_item_requirement(self.player, item)
        if missing_item:
            c.create_text(left + 14, y, text=self.text("equipment_requires", item=self.item_name(missing_item)), fill="#ffb0aa", anchor="w", font=("Segoe UI", 9, "bold"))
            y += 22
        passive_key = item.get("passive")
        if passive_key:
            c.create_text(left + 14, y, text=f"{self.text('equipment_passive')}: {self.text(f'passive_{passive_key}')}", fill="#f7d765", anchor="w", font=("Segoe UI", 9, "bold"), width=188)

    def full_item_stat_text(self, item):
        parts = []
        if item.get("attack_damage"):
            parts.append(f"+{item['attack_damage']} {self.text('stat_attack')}")
        if item.get("skill_power"):
            parts.append(f"+{item['skill_power']} {self.text('stat_skill')}")
        if item.get("max_hp"):
            parts.append(f"+{item['max_hp']} {self.text('stat_hp')}")
        if item.get("speed"):
            parts.append(f"+{item['speed']} {self.text('stat_speed')}")
        if item.get("attack_range"):
            parts.append(f"+{item['attack_range']} {self.text('stat_range')}")
        if item.get("attack_cd_reduce"):
            parts.append(f"+{int(item['attack_cd_reduce'] * 100)} {self.text('stat_haste')}")
        return " / ".join(parts) if parts else "-"

    def draw_scoreboard(self, c):
        left = 218
        top = 112
        right = WIDTH - 218
        bottom = 402
        c.create_rectangle(left, top, right, bottom, fill="#0d1215", outline="#d8cf9b", width=2)
        c.create_rectangle(left, top, right, top + 48, fill="#151b1e", outline="")
        c.create_text(WIDTH // 2, top + 24, text=self.text("scoreboard"), fill="#f5f1d7", font=("Segoe UI", 18, "bold"))
        self.draw_scoreboard_row(c, self.player, left + 28, top + 78, right - left - 56, "#78a3ff")
        self.draw_scoreboard_row(c, self.enemy_hero, left + 28, top + 188, right - left - 56, "#ff7b7c")

    def draw_scoreboard_row(self, c, hero, left, top, width, color):
        c.create_rectangle(left, top, left + width, top + 82, fill="#111719", outline=color, width=2)
        c.create_oval(left + 18, top + 18, left + 58, top + 58, fill=hero.accent, outline="#f5f1d7", width=2)
        c.create_text(left + 38, top + 38, text=str(hero.level), fill="#101416", font=("Segoe UI", 14, "bold"))
        name = self.hero_name(hero.hero_key)
        if hero.team == "red":
            name = self.text("enemy_prefix", name=name)
        c.create_text(left + 74, top + 20, text=f"{name} / {self.hero_role(hero.hero_key)}", fill="#f5f1d7", anchor="w", font=("Segoe UI", 13, "bold"))
        stat_text = f"{self.text('kills')} {hero.kills}   {self.text('deaths')} {hero.deaths}   {self.text('gold')} {hero.gold}"
        c.create_text(left + 74, top + 48, text=stat_text, fill="#cfd6cd", anchor="w", font=("Segoe UI", 11))

        equipment_text = self.equipment_summary(hero)
        skill_text = " / ".join(f"{key.upper()} Lv{hero.skill_levels.get(key, 0)}" for key in ("q", "e", "r"))
        c.create_text(left + width - 22, top + 24, text=f"{self.text('equipment')}: {equipment_text}", fill="#d8cf9b", anchor="e", font=("Segoe UI", 10))
        c.create_text(left + width - 22, top + 54, text=skill_text, fill="#f7d765", anchor="e", font=("Segoe UI", 11, "bold"))

    def equipment_summary(self, hero):
        purchased = [f"{self.item_name(key)} {level}" for key, level in hero.equipment.items() if level > 0]
        if not purchased:
            return "-"
        if len(purchased) > 4:
            return " / ".join(purchased[:4]) + f" +{len(purchased) - 4}"
        return " / ".join(purchased)

    def draw_settlement(self, c):
        self.settlement_buttons = []
        blue_won = self.winner == "blue"
        overlay = "#17291f" if blue_won else "#35191d"
        left = 260
        top = 116
        right = WIDTH - 260
        bottom = 586
        c.create_rectangle(left, top, right, bottom, fill=overlay, outline="#f5f1d7", width=2)
        c.create_text(WIDTH // 2, top + 34, text=self.text("settlement"), fill="#d8cf9b", font=("Segoe UI", 15, "bold"))
        result_text = self.text("result_win") if blue_won else self.text("result_loss")
        result_color = "#78a3ff" if blue_won else "#ff7b7c"
        c.create_text(WIDTH // 2, top + 84, text=result_text, fill=result_color, font=("Segoe UI", 36, "bold"))
        c.create_text(WIDTH // 2, top + 124, text=f"{self.text('duration')} {self.format_time(self.match_time)}", fill="#cfd6cd", font=("Segoe UI", 12))

        self.draw_settlement_stats(c, self.player, left + 42, top + 162, "#78a3ff")
        self.draw_settlement_stats(c, self.enemy_hero, WIDTH // 2 + 16, top + 162, "#ff7b7c")

        self.draw_settlement_button(c, "rematch", WIDTH // 2 - 172, bottom - 72, 150, 44, "#d8cf9b")
        self.draw_settlement_button(c, "lobby", WIDTH // 2 + 22, bottom - 72, 150, 44, "#78a3ff")

    def draw_settlement_stats(self, c, hero, left, top, color):
        width = 238
        height = 206
        enemy_towers_destroyed = sum(1 for tower in self.towers if tower.team != hero.team and not tower.alive)
        c.create_rectangle(left, top, left + width, top + height, fill="#101416", outline=color, width=2)
        name = self.hero_name(hero.hero_key)
        if hero.team == "red":
            name = self.text("enemy_prefix", name=name)
        c.create_text(left + 18, top + 24, text=name, fill="#f5f1d7", anchor="w", font=("Segoe UI", 13, "bold"))
        stats = self.match_stats[hero.team]
        left_lines = [
            f"{self.text('level')} {hero.level}",
            f"{self.text('kills')} {hero.kills} / {self.text('deaths')} {hero.deaths}",
            f"{self.text('gold_earned')} {int(stats['gold_earned'])}",
            f"{self.text('items_spent')} {int(stats['items_spent'])}",
            f"{self.text('minions_last_hit')} {int(stats['minions_last_hit'])}",
            f"{self.text('monsters_slain')} {int(stats['monsters_slain'])}",
        ]
        right_lines = [
            f"{self.text('destroyed_towers')} {enemy_towers_destroyed}",
            f"{self.text('hero_damage')} {int(stats['hero_damage'])}",
            f"{self.text('structure_damage')} {int(stats['structure_damage'])}",
            f"{self.text('damage_taken')} {int(stats['damage_taken'])}",
            f"{self.text('healing')} {int(stats['healing'])}",
            f"{self.text('shielding')} {int(stats['shielding'])}",
        ]
        for index, line in enumerate(left_lines):
            c.create_text(left + 18, top + 52 + index * 22, text=line, fill="#cfd6cd", anchor="w", font=("Segoe UI", 9))
        for index, line in enumerate(right_lines):
            c.create_text(left + 124, top + 52 + index * 22, text=line, fill="#cfd6cd", anchor="w", font=("Segoe UI", 9))
        c.create_text(
            left + 18,
            top + 188,
            text=" / ".join(f"{key.upper()} Lv{hero.skill_levels.get(key, 0)}" for key in ("q", "e", "r")),
            fill="#f7d765",
            anchor="w",
            font=("Segoe UI", 9, "bold"),
        )

    def draw_settlement_button(self, c, action, x, y, width, height, color):
        self.settlement_buttons.append((action, x, y, x + width, y + height))
        label = self.text("rematch") if action == "rematch" else self.text("back_lobby")
        c.create_rectangle(x, y, x + width, y + height, fill="#111719", outline=color, width=2)
        c.create_text(x + width / 2, y + height / 2, text=label, fill="#f5f1d7", font=("Segoe UI", 12, "bold"))

    def draw_skill(self, c, x, y, label, ready_at, full_cd, size, skill_key=None):
        current = self.now()
        locked = skill_key is not None and not self.skill_unlocked(self.player, skill_key)
        ready = current >= ready_at and not locked
        fill = "#26313a" if ready else "#171b20"
        r = size // 2
        c.create_oval(x - r - 4, y - r - 4, x + r + 4, y + r + 4, fill="#0d1215", outline="#394043", width=2)
        c.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline="#d8cf9b", width=2)
        if not ready and not locked:
            left = ready_at - current
            pct = clamp(left / full_cd, 0, 1)
            c.create_arc(
                x - r,
                y - r,
                x + r,
                y + r,
                start=90,
                extent=-360 * pct,
                fill="#000000",
                outline="",
            )
        c.create_text(x, y, text=label, fill="#f5f1d7", font=("Segoe UI", 15, "bold"))
        if locked:
            c.create_text(x, y + 25, text=self.text("locked"), fill="#ffb0aa", font=("Segoe UI", 8, "bold"))
        elif not ready:
            c.create_text(x, y + 25, text=f"{left:.1f}", fill="#ffffff", font=("Segoe UI", 8, "bold"))
        if skill_key is not None:
            self.skill_detail_buttons.append((skill_key, x - r - 8, y - r - 8, x + r + 8, y + r + 28))
            level = self.player.skill_levels.get(skill_key, 0)
            max_level = SKILL_MAX_LEVELS[skill_key]
            c.create_text(x, y + r + 18, text=f"Lv {level}/{max_level}", fill="#cfd6cd", font=("Segoe UI", 8, "bold"))
            if self.can_upgrade_skill(self.player, skill_key):
                px = x + r - 5
                py = y - r - 17
                self.skill_upgrade_buttons.append((skill_key, px - 10, py - 10, px + 10, py + 10))
                c.create_oval(px - 10, py - 10, px + 10, py + 10, fill="#f7d765", outline="#101416", width=2)
                c.create_text(px, py - 1, text="+", fill="#101416", font=("Segoe UI", 13, "bold"))

    def draw_skill_tooltip(self, c):
        hovered = None
        for skill_key, left, top, right, bottom in self.skill_detail_buttons:
            if left <= self.mouse_x <= right and top <= self.mouse_y <= bottom:
                hovered = skill_key
                break
        if not hovered:
            return
        level = self.player.skill_levels.get(hovered, 0)
        title = self.text(
            "skill_tooltip_title",
            key=hovered.upper(),
            name=self.hero_skill(self.player.hero_key, hovered),
            level=level,
            max_level=SKILL_MAX_LEVELS[hovered],
        )
        body = self.text("skill_tooltip_body", detail=self.hero_skill_detail(self.player.hero_key, hovered))
        passive = f"P {self.hero_passive_name(self.player.hero_key)}: {self.hero_passive_detail(self.player.hero_key)}"
        left = WIDTH - 392
        top = HEIGHT - 316
        c.create_rectangle(left, top, left + 344, top + 116, fill="#101416", outline=self.player.accent, width=2)
        c.create_text(left + 14, top + 20, text=title, fill="#f5f1d7", anchor="w", font=("Segoe UI", 11, "bold"))
        c.create_text(left + 14, top + 52, text=body, fill="#cfd6cd", anchor="w", font=("Segoe UI", 9), width=314)
        c.create_text(left + 14, top + 92, text=passive, fill=self.player.accent, anchor="w", font=("Segoe UI", 8, "bold"), width=314)

    def draw_tutorial(self, c):
        left, top, right, bottom = 214, 88, 592, 244
        c.create_rectangle(left, top, right, bottom, fill="#101416", outline="#d8cf9b", width=2)
        c.create_text(left + 18, top + 22, text=self.text("tutorial_title"), fill="#f5f1d7", anchor="w", font=("Segoe UI", 13, "bold"))
        for index, line in enumerate(self.text("tutorial_lines")):
            c.create_text(left + 20, top + 52 + index * 22, text=line, fill="#cfd6cd", anchor="w", font=("Segoe UI", 9), width=338)
        bx1, by1, bx2, by2 = left + 18, bottom - 30, right - 18, bottom - 8
        self.tutorial_close_button = (bx1, by1, bx2, by2)
        hovered = bx1 <= self.mouse_x <= bx2 and by1 <= self.mouse_y <= by2
        c.create_rectangle(bx1, by1, bx2, by2, fill="#27343a" if hovered else "#1b2326", outline="#394043")
        c.create_text((bx1 + bx2) / 2, (by1 + by2) / 2, text=self.text("tutorial_close"), fill="#d8cf9b", font=("Segoe UI", 9, "bold"))

