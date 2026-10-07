import math
import random

import pygame

from equipment_data import HERO_RECOMMENDED_ITEMS, ITEMS
from game_data import (
    BRUSH_ZONES,
    HEIGHT,
    HEROES,
    Hero,
    MODE_RULES,
    RIVER_POLYGON,
    SKILL_MAX_LEVELS,
    SKIN_STYLES,
    WIDTH,
    clamp,
    skin_accent,
    team_color,
)
import meta
import sprites

# tkinter font sizes are points (~1.33px at 96dpi); pygame sizes are pixels.
FONT_SCALE = 4 / 3

_color_cache = {}


def color(value):
    cached = _color_cache.get(value)
    if cached is None:
        cached = pygame.Color(value)
        _color_cache[value] = cached
    return cached


_fonts = {}


def get_font(size, bold):
    pixel_size = max(7, round(size * FONT_SCALE))
    key = (pixel_size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("microsoftyahei,segoeui", pixel_size, bold=bold)
    return _fonts[key]


def rect(c, x1, y1, x2, y2, fill=None, outline=None, width=1):
    box = pygame.Rect(round(x1), round(y1), round(x2 - x1), round(y2 - y1))
    if box.width <= 0 or box.height <= 0:
        return
    if fill is not None:
        pygame.draw.rect(c, color(fill), box)
    if outline is not None:
        pygame.draw.rect(c, color(outline), box, max(1, width))


def oval(c, x1, y1, x2, y2, fill=None, outline=None, width=1, dash=None):
    box = pygame.Rect(round(x1), round(y1), round(x2 - x1), round(y2 - y1))
    if box.width <= 0 or box.height <= 0:
        return
    if fill is not None:
        pygame.draw.ellipse(c, color(fill), box)
    if outline is not None:
        if dash:
            dashed_ellipse(c, color(outline), box, max(1, width), dash)
        else:
            pygame.draw.ellipse(c, color(outline), box, max(1, width))


def polygon(c, points, fill=None, outline=None, width=1):
    pts = [(round(points[i]), round(points[i + 1])) for i in range(0, len(points) - 1, 2)]
    if len(pts) < 3:
        return
    if fill is not None:
        pygame.draw.polygon(c, color(fill), pts)
    if outline is not None and width > 0:
        pygame.draw.polygon(c, color(outline), pts, max(1, width))


def dashed_line(c, clr, x1, y1, x2, y2, width=1, dash=(8, 6)):
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length <= 0:
        return
    ux, uy = dx / length, dy / length
    on, off = dash
    t = 0.0
    while t < length:
        end = min(t + on, length)
        pygame.draw.line(c, clr, (round(x1 + ux * t), round(y1 + uy * t)), (round(x1 + ux * end), round(y1 + uy * end)), width)
        t += on + off


def dashed_ellipse(c, clr, box, width=1, dash=(8, 6)):
    rx = box.width / 2
    ry = box.height / 2
    if rx <= 0 or ry <= 0:
        return
    circumference = math.pi * (3 * (rx + ry) - math.sqrt((3 * rx + ry) * (rx + 3 * ry)))
    on, off = dash
    step_deg = (on + off) / max(circumference, 1.0) * 360.0
    angle = 0.0
    while angle < 360:
        end = min(angle + step_deg * on / max(on + off, 1), 360)
        if end > angle:
            pygame.draw.arc(c, clr, box, math.radians(angle), math.radians(end), width)
        angle += step_deg


def line(c, points, fill, width=1, dash=None, rounded=True):
    pts = [(round(points[i]), round(points[i + 1])) for i in range(0, len(points) - 1, 2)]
    if len(pts) < 2:
        return
    clr = color(fill)
    width = max(1, round(width))
    if dash:
        for i in range(len(pts) - 1):
            dashed_line(c, clr, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], width, dash)
        return
    if len(pts) == 2:
        pygame.draw.line(c, clr, pts[0], pts[1], width)
    else:
        pygame.draw.lines(c, clr, False, pts, width)
    if rounded and width >= 2:
        joint_radius = width // 2
        for p in (pts[0], pts[-1]):
            pygame.draw.circle(c, clr, p, joint_radius)
        for p in pts[1:-1]:
            pygame.draw.circle(c, clr, p, joint_radius)


def pie(c, x, y, radius, pct, fill="#000000"):
    pct = clamp(pct, 0, 1)
    if pct <= 0:
        return
    pts = [(x, y)]
    steps = max(2, int(40 * pct))
    for i in range(steps + 1):
        angle = math.radians(90 - 360 * pct * i / steps)
        pts.append((round(x + math.cos(angle) * radius), round(y - math.sin(angle) * radius)))
    pygame.draw.polygon(c, color(fill), pts)


def wrap_text(font, value, max_width):
    lines = []
    for raw in str(value).split("\n"):
        if font.size(raw)[0] <= max_width:
            lines.append(raw)
            continue
        current = ""
        for ch in raw:
            if current and font.size(current + ch)[0] > max_width:
                lines.append(current)
                current = ch
            else:
                current += ch
        if current:
            lines.append(current)
    return lines


def blit_line(c, font, value, clr, x, y, anchor):
    surf = font.render(value, True, clr)
    box = surf.get_rect()
    if anchor == "w":
        box.midleft = (round(x), round(y))
    elif anchor == "e":
        box.midright = (round(x), round(y))
    else:
        box.center = (round(x), round(y))
    c.blit(surf, box)


def text(c, x, y, value, fill, size=12, bold=False, anchor="center", width=None):
    font = get_font(size, bold)
    clr = color(fill)
    if width:
        lines = wrap_text(font, value, width)
        line_height = font.get_linesize()
        total = line_height * len(lines)
        top = y - total // 2
        for index, ln in enumerate(lines):
            blit_line(c, font, ln, clr, x, top + index * line_height + line_height // 2, anchor)
        return
    blit_line(c, font, str(value), clr, x, y, anchor)


_flash_overlay = None


def flash_overlay():
    global _flash_overlay
    if _flash_overlay is None:
        _flash_overlay = pygame.Surface((52, 52), pygame.SRCALPHA)
        pygame.draw.circle(_flash_overlay, (255, 255, 255, 150), (26, 26), 24)
    return _flash_overlay


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
                    line(c, [hero.x, hero.y, hero.x + ax * 260, hero.y + ay * 260], hero.accent, 3, dash=(8, 6))
            elif hero.hero_key == "sentinel":
                oval(c, hero.x - 72, hero.y - 72, hero.x + 72, hero.y + 72, outline=hero.accent, width=2, dash=(8, 4))
                line(c, [hero.x, hero.y, hero.x + vx * 150, hero.y + vy * 150], hero.accent, 3, dash=(8, 6))
            elif hero.hero_key == "arcanist":
                line(c, [hero.x, hero.y, hero.x + vx * 180, hero.y + vy * 180], hero.accent, 5, dash=(10, 6))
            elif hero.hero_key == "shade":
                line(c, [hero.x, hero.y, hero.x + vx * 165, hero.y + vy * 165], hero.accent, 4, dash=(8, 6))
            elif hero.hero_key == "weaver":
                line(c, [hero.x, hero.y, hero.x + vx * 240, hero.y + vy * 240], hero.accent, 3, dash=(7, 5))
                line(c, [hero.x - vy * 10, hero.y + vx * 10, hero.x + vx * 220 - vy * 10, hero.y + vy * 220 + vx * 10], hero.accent, 1, dash=(7, 5))
                line(c, [hero.x + vy * 10, hero.y - vx * 10, hero.x + vx * 220 + vy * 10, hero.y + vy * 220 - vx * 10], hero.accent, 1, dash=(7, 5))
            elif hero.hero_key == "geomancer":
                angle = math.atan2(vy, vx)
                for offset in (-0.18, 0, 0.18):
                    ax = math.cos(angle + offset)
                    ay = math.sin(angle + offset)
                    line(c, [hero.x, hero.y, hero.x + ax * 210, hero.y + ay * 210], hero.accent, 2, dash=(7, 5))
            elif hero.hero_key == "tempest":
                angle = math.atan2(vy, vx)
                for offset in (-0.08, 0, 0.08):
                    ax = math.cos(angle + offset)
                    ay = math.sin(angle + offset)
                    line(c, [hero.x, hero.y, hero.x + ax * 260, hero.y + ay * 260], hero.accent, 2, dash=(8, 6))
            else:
                line(c, [hero.x, hero.y, hero.x + vx * 260, hero.y + vy * 260], hero.accent, 3, dash=(8, 6))
            end_x = hero.x + vx * 260
            end_y = hero.y + vy * 260
            oval(c, end_x - 14, end_y - 14, end_x + 14, end_y + 14, outline=hero.accent, width=2)
        elif self.aiming_skill == "e":
            if hero.hero_key in {"sentinel", "arcanist", "geomancer"}:
                radius = 82 if hero.hero_key == "arcanist" else 78 if hero.hero_key == "geomancer" else 94
                oval(c, hero.x - radius, hero.y - radius, hero.x + radius, hero.y + radius, outline=hero.accent, width=2, dash=(8, 4))
                oval(c, hero.x - 16, hero.y - 16, hero.x + 16, hero.y + 16, outline=hero.accent, width=2)
            else:
                distance = 168 if hero.hero_key == "ranger" else 205 if hero.hero_key == "shade" else 236 if hero.hero_key == "weaver" else 178 if hero.hero_key == "tempest" else 176 if hero.hero_key == "reaver" else 142 if hero.hero_key == "warden" else 120
                end_x = clamp(hero.x + vx * distance, 35, WIDTH - 35)
                end_y = clamp(hero.y + vy * distance, 35, HEIGHT - 35)
                line(c, [hero.x, hero.y, end_x, end_y], hero.accent, 4, dash=(10, 6))
                if hero.hero_key == "weaver":
                    oval(c, end_x - 62, end_y - 62, end_x + 62, end_y + 62, outline=hero.accent, width=2, dash=(8, 4))
                else:
                    oval(c, end_x - 16, end_y - 16, end_x + 16, end_y + 16, outline=hero.accent, width=2)
        elif self.aiming_skill == "r":
            if hero.hero_key == "ranger":
                angle = math.atan2(vy, vx)
                for offset in (-0.52, -0.39, -0.26, -0.13, 0, 0.13, 0.26, 0.39, 0.52):
                    ax = math.cos(angle + offset)
                    ay = math.sin(angle + offset)
                    line(c, [hero.x, hero.y, hero.x + ax * 260, hero.y + ay * 260], hero.accent, 2, dash=(10, 6))
            elif hero.hero_key == "shade":
                line(c, [hero.x, hero.y, self.mouse_x, self.mouse_y], hero.accent, 5, dash=(12, 8))
                oval(c, self.mouse_x - 34, self.mouse_y - 34, self.mouse_x + 34, self.mouse_y + 34, outline=hero.accent, width=2)
            elif hero.hero_key == "weaver":
                line(c, [hero.x, hero.y, self.mouse_x, self.mouse_y], hero.accent, 4, dash=(10, 7))
                oval(c, self.mouse_x - 108, self.mouse_y - 108, self.mouse_x + 108, self.mouse_y + 108, outline=hero.accent, width=2, dash=(8, 4))
                oval(c, self.mouse_x - 54, self.mouse_y - 54, self.mouse_x + 54, self.mouse_y + 54, outline=hero.accent, width=1, dash=(6, 5))
            elif hero.hero_key == "tempest":
                angle = math.atan2(vy, vx)
                for offset in (-0.42, -0.24, -0.08, 0.08, 0.24, 0.42):
                    ax = math.cos(angle + offset)
                    ay = math.sin(angle + offset)
                    line(c, [hero.x, hero.y, hero.x + ax * 250, hero.y + ay * 250], hero.accent, 2, dash=(10, 6))
            else:
                radius = 96 if hero.hero_key == "vanguard" else 120 if hero.hero_key == "arcanist" else 118 if hero.hero_key == "warden" else 98 if hero.hero_key == "reaver" else 132 if hero.hero_key == "geomancer" else 136
                oval(c, self.mouse_x - radius, self.mouse_y - radius, self.mouse_x + radius, self.mouse_y + radius, outline=hero.accent, width=2, dash=(8, 4))
                oval(c, self.mouse_x - 12, self.mouse_y - 12, self.mouse_x + 12, self.mouse_y + 12, outline=hero.accent, width=2)


    def draw(self):
        if self.state in ("language", "lobby", "select", "loading"):
            c = self.screen
            c.fill("#18261d")
            if self.state == "language":
                self.draw_language(c)
            elif self.state == "lobby":
                self.draw_lobby(c)
            elif self.state == "select":
                self.draw_select(c)
            else:
                self.draw_loading(c)
            return

        # The battle renders onto a world layer so screen shake can offset it while the HUD stays stable.
        c = self.world_surface
        c.fill("#18261d")
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
        self.draw_projectile_trails(c)
        self.draw_hero(c, self.player)
        if self.hero_visible_to_player(self.enemy_hero):
            self.draw_hero(c, self.enemy_hero)
        for p in self.projectiles:
            oval(c, p.x - p.radius, p.y - p.radius, p.x + p.radius, p.y + p.radius, fill=p.color)
        for e in self.effects:
            alpha_width = max(1, int(5 * e.ttl / e.max_ttl))
            oval(c, e.x - e.radius, e.y - e.radius, e.x + e.radius, e.y + e.radius, outline=e.color, width=alpha_width)
        for beam in self.beams:
            width = max(1, int(beam.width * beam.ttl / beam.max_ttl))
            line(c, [beam.x1, beam.y1, beam.x2, beam.y2], beam.color, width)
        for p in self.particles:
            size = p.radius * (0.7 if p.shrink else 1)
            oval(c, p.x - size, p.y - size, p.x + size, p.y + size, fill=p.color)
        for item in self.float_texts:
            text(c, item.x, item.y, item.text, item.color, 11, True)
        self.draw_locked_target(c)
        offset_x, offset_y = self.shake_offset()
        self.screen.fill("#0b0f11")
        self.screen.blit(c, (round(offset_x), round(offset_y)))
        screen = self.screen
        for index, banner in enumerate(self.banners[-3:]):
            alpha = banner.ttl / banner.max_ttl
            left = WIDTH // 2 - 220
            right = WIDTH // 2 + 220
            top = 120 + index * 58
            bottom = 172
            bottom += index * 58
            fill = "#101416" if alpha > 0.3 else "#0f1416"
            rect(screen, left, top, right, bottom, fill=fill, outline=banner.color, width=2)
            text(screen, WIDTH // 2, top + 27, banner.text, banner.color, 18, True)
        self.draw_ui(screen)

    def draw_language(self, c):
        rect(c, 0, 0, WIDTH, HEIGHT, fill="#14191c")
        self.draw_menu_backdrop(c)
        rect(c, 0, 0, WIDTH, 118, fill="#0f1416")
        text(c, WIDTH // 2, 42, "LANGUAGE / 语言", "#f5f1d7", 30, True)
        text(c, WIDTH // 2, 78, "Python MOBA Prototype", "#9ea898", 13)

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
            rect(c, x1, y1, x2, y2, fill="#20282b", outline=outline, width=3)
            text(c, (x1 + x2) // 2, y1 + 60, title, "#f5f1d7", 25, True)
            text(c, (x1 + x2) // 2, y1 + 102, subtitle, "#aeb8ad", 12)

        rect(c, 384, 518, 716, 562, fill="#101416", outline="#394043")
        text(c, WIDTH // 2, 540, "MOBA READY", "#d8cf9b", 13, True)

    def draw_select(self, c):
        rect(c, 0, 0, WIDTH, HEIGHT, fill="#151b1d")
        self.draw_menu_backdrop(c)
        rect(c, 0, 0, WIDTH, 95, fill="#101416")
        text(c, WIDTH // 2, 38, self.text("hero_title"), "#f5f1d7", 28, True)
        text(c, WIDTH // 2, 72, self.text("language_subtitle"), "#9ea898", 13)

        self.hero_cards = []
        self.skin_buttons = []
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
                self.select_hover_hero = hero_key
            outline = config["accent"] if active else "#394043"
            rect(c, left, top, right, bottom, fill="#20282b", outline=outline, width=3)
            rect(c, left, top, right, top + 52, fill="#161c1f")
            hotkey = "0" if index == 9 else str(index + 1)
            text(c, left + 16, top + 19, f"{hotkey}. {self.hero_name(hero_key)}", "#f5f1d7", 12, True, anchor="w", width=150)
            text(c, left + 16, top + 40, self.hero_role(hero_key), config["accent"], 9, True, anchor="w")
            self.draw_hero_icon(c, left + 165, top + 26, hero_key, skin_accent(hero_key, meta.selected_skin_id(self.profile, hero_key)))

            stat_y = top + 76
            self.draw_stat(c, left + 16, stat_y, "HP", config["hp"], 760, "#48d06b")
            self.draw_stat(c, left + 16, stat_y + 26, "SPD", config["speed"], 250, "#76b7ff")
            self.draw_stat(c, left + 16, stat_y + 52, "ATK", config["attack_damage"], 45, "#f7d765")
            text(c, left + 16, top + 154, f"Q {self.hero_skill(hero_key, 'q')}", "#cfd6cd", 8, True, anchor="w", width=164)
            text(c, left + 16, top + 172, f"E {self.hero_skill(hero_key, 'e')}", "#cfd6cd", 8, True, anchor="w", width=164)
            text(c, left + 16, top + 190, f"R {self.hero_skill(hero_key, 'r')}", "#f5d28a", 8, True, anchor="w", width=164)
            trait = self.hero_skill_traits(hero_key)
            trait_size = 8 if len(trait) > 24 else 9
            text(c, left + 16, top + 208, trait, config["accent"], trait_size, True, anchor="w", width=168)

        panel_hero_key = self.select_hover_hero
        if panel_hero_key:
            accent = skin_accent(panel_hero_key, meta.selected_skin_id(self.profile, panel_hero_key))
            rect(c, 182, 568, 918, 692, fill="#101416", outline=accent, width=2)
            text(
                c,
                206,
                588,
                f"{self.hero_name(panel_hero_key)} / {self.hero_role(panel_hero_key)}",
                "#f5f1d7",
                12,
                True,
                anchor="w",
            )
            passive = f"P {self.hero_passive_name(panel_hero_key)}: {self.hero_passive_detail(panel_hero_key)}"
            text(c, 206, 610, passive, accent, 8, True, anchor="w", width=640)
            for index, key in enumerate(("q", "e", "r")):
                detail = f"{key.upper()} {self.hero_skill(panel_hero_key, key)}: {self.hero_skill_detail(panel_hero_key, key)}"
                text(c, 206, 634 + index * 18, detail, "#cfd6cd", 8, False, anchor="w", width=640)
            for index, style in enumerate(SKIN_STYLES):
                row_y = 592 + index * 32
                locked = self.profile["level"] < style["unlock_level"]
                swatch_accent = skin_accent(panel_hero_key, style["id"])
                selected = meta.selected_skin_id(self.profile, panel_hero_key) == style["id"]
                label = self.text(style["name_key"]) if not locked else self.text("skin_locked", level=style["unlock_level"])
                text(c, 850, row_y, label, "#f5f1d7" if selected else "#9ea898", 8, True, anchor="e")
                oval(c, 862, row_y - 12, 886, row_y + 12, fill="#14191c" if locked else swatch_accent, outline="#f5f1d7" if selected else "#394043", width=3 if selected else 2)
                self.skin_buttons.append((style["id"], 858, row_y - 16, 890, row_y + 16))
        else:
            rect(c, 358, 610, 742, 656, fill="#101416", outline="#394043")
            text(c, WIDTH // 2, 633, self.text("choose_hero"), "#d8cf9b", 13, True)

    def draw_lobby(self, c):
        rect(c, 0, 0, WIDTH, HEIGHT, fill="#12181b")
        self.draw_menu_backdrop(c)
        rect(c, 0, 0, WIDTH, 82, fill="#0d1215")
        text(c, 34, 30, self.text("lobby_title"), "#f5f1d7", 25, True, anchor="w")
        text(c, 36, 58, self.text("lobby_subtitle"), "#aeb8ad", 11, False, anchor="w")
        text(c, WIDTH - 34, 30, self.text("profile"), "#f7d765", 13, True, anchor="e")
        text(c, WIDTH - 34, 58, self.text("season"), "#cfd6cd", 12, False, anchor="e")

        rect(c, 44, 122, 342, 254, fill="#20282b", outline="#d8cf9b", width=2)
        text(c, 72, 154, self.text("profile"), "#f5f1d7", 15, True, anchor="w")
        mode_name = self.mode_configs()[self.selected_mode_key][0] if self.selected_mode_key else self.text("mode_unselected")
        text(c, 72, 184, mode_name, "#78a3ff", 18, True, anchor="w")
        text(c, 72, 212, self.text("hero_unselected"), "#aeb8ad", 12, False, anchor="w")
        account_line = self.text(
            "account_line",
            level=self.profile["level"],
            xp=self.profile["xp"],
            need=meta.xp_for_level(self.profile["level"]),
        )
        text(c, 72, 238, account_line, "#f7d765", 11, True, anchor="w")
        self.draw_quests_panel(c)

    def draw_quests_panel(self, c):
        quests = meta.daily_quests()
        state = self.profile.get("quests") or {}
        left, top, right, bottom = 700, 498, 958, 640
        rect(c, left, top, right, bottom, fill="#101416", outline="#394043", width=2)
        text(c, left + 14, top + 18, self.text("daily_quests"), "#d8cf9b", 12, True, anchor="w")
        for index, quest in enumerate(quests):
            y = top + 46 + index * 32
            done = quest["id"] in state.get("done", [])
            progress = min(state.get("progress", {}).get(quest["id"], 0), quest["goal"])
            mark = "✓ " if done else ""
            desc_color = "#5f6a5f" if done else "#cfd6cd"
            text(c, left + 14, y, f"{mark}{self.text(quest['text_key'], goal=quest['goal'])}", desc_color, 9, True, anchor="w")
            progress_color = "#76f4d1" if done else "#f7d765"
            text(c, right - 14, y, f"{progress}/{quest['goal']}  +{quest['reward']}", progress_color, 9, True, anchor="e")

        self.mode_cards = []
        mode_layout = [
            ("rank", 404, 132, 666, 284),
            ("train", 696, 132, 958, 284),
            ("quick", 404, 318, 666, 470),
        ]
        mode_configs = self.mode_configs()
        for mode_key, left, top, right, bottom in mode_layout:
            title, mcolor, desc = mode_configs[mode_key]
            selected = self.selected_mode_key == mode_key
            hovered = left <= self.mouse_x <= right and top <= self.mouse_y <= bottom
            outline = "#f5f1d7" if selected else mcolor if hovered else "#394043"
            fill = "#27343a" if selected else "#20282b"
            self.mode_cards.append((mode_key, left, top, right, bottom))
            rect(c, left, top, right, bottom, fill=fill, outline=outline, width=3 if selected else 2)
            rect(c, left, top, right, top + 38, fill="#151b1e")
            text(c, left + 22, top + 20, title, "#f5f1d7", 15, True, anchor="w")
            text(c, left + 22, top + 62, desc, "#cfd6cd", 9, False, anchor="w", width=right - left - 42)
            text(c, left + 22, top + 102, self.mode_rule_summary(mode_key), "#d8cf9b", 8, True, anchor="w", width=right - left - 42)
            line(c, [left + 24, bottom - 22, right - 24, top + 118], mcolor, 5)
            oval(c, right - 74, bottom - 78, right - 24, bottom - 28, fill=mcolor)

        self.lobby_buttons = [("start", 408, 548, 692, 616)]
        button_fill = "#d8cf9b" if self.selected_mode_key else "#4b4f4b"
        text_fill = "#101416" if self.selected_mode_key else "#aeb8ad"
        rect(c, 408, 548, 692, 616, fill=button_fill, outline="#f5f1d7", width=3)
        text(c, WIDTH // 2, 582, self.text("start_match"), text_fill, 21, True)
        text(c, WIDTH // 2, 642, self.text("mode_prompt"), "#aeb8ad", 12)

    def draw_loading(self, c):
        rect(c, 0, 0, WIDTH, HEIGHT, fill="#101416")
        self.draw_menu_backdrop(c)
        progress = clamp((self.now() - self.loading_started_at) / 1.15, 0, 1)
        enemy_key = self.enemy_hero.hero_key if self.enemy_hero else "vanguard"
        text(c, WIDTH // 2, 86, self.text("loading"), "#f5f1d7", 26, True)
        rect(c, 184, 154, 456, 514, fill="#20282b", outline=self.player.accent, width=3)
        rect(c, 644, 154, 916, 514, fill="#20282b", outline="#e84d4f", width=3)
        self.draw_hero_portrait(c, 320, 300, self.player.hero_key, self.player.accent)
        self.draw_hero_portrait(c, 780, 300, enemy_key, self.enemy_hero.accent)
        text(c, 320, 430, self.hero_name(self.player.hero_key), "#f5f1d7", 20, True)
        text(c, 780, 430, self.text("enemy_prefix", name=self.hero_name(enemy_key)), "#f5f1d7", 20, True)
        text(c, WIDTH // 2, 320, self.text("versus"), "#d8cf9b", 28, True)
        rect(c, 260, 590, 840, 606, fill="#252a2a")
        rect(c, 260, 590, 260 + 580 * progress, 606, fill="#d8cf9b")

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
        if self._menu_backdrop is None:
            surface = pygame.Surface((WIDTH, HEIGHT))
            surface.fill("#14191c")
            for path in self.paths.values():
                points = []
                for x, y in path:
                    points.extend([x, y])
                line(surface, points, "#263139", 62)
                line(surface, points, "#3f4b4e", 28)
            oval(surface, -90, HEIGHT - 160, 230, HEIGHT + 160, fill="#203f5f")
            oval(surface, WIDTH - 230, -160, WIDTH + 90, 160, fill="#5b2428")
            for i in range(18):
                rng = random.Random(100 + i)
                x = rng.randint(80, WIDTH - 80)
                y = rng.randint(130, HEIGHT - 80)
                rect(surface, x - 18, y - 2, x + 18, y + 2, fill="#2d3939")
            self._menu_backdrop = surface
        c.blit(self._menu_backdrop, (0, 0))

    def draw_hero_portrait(self, c, x, y, hero_key, accent):
        oval(c, x - 54, y - 54, x + 54, y + 54, fill="#14191c", outline=accent, width=4)
        portrait = sprites.portrait_scaled(hero_key, HEROES[hero_key]["role"], accent, 92)
        c.blit(portrait, portrait.get_rect(center=(round(x), round(y))))
        line(c, [x - 62, y + 68, x + 62, y + 68], accent, 3)

    def draw_hero_icon(self, c, x, y, hero_key, accent):
        icon = sprites.portrait_scaled(hero_key, HEROES[hero_key]["role"], accent, 42)
        c.blit(icon, icon.get_rect(center=(round(x), round(y))))

    def draw_stat(self, c, x, y, label, value, max_value, bar_color):
        text(c, x, y, label, "#f5f1d7", 10, True, anchor="w")
        rect(c, x + 44, y - 6, x + 164, y + 6, fill="#151b1d")
        pct = clamp(value / max_value, 0, 1)
        rect(c, x + 44, y - 6, x + 44 + 120 * pct, y + 6, fill=bar_color)
        text(c, x + 174, y, str(int(value)), "#cfd6cd", 10, False, anchor="e")

    def build_map_surface(self):
        surface = pygame.Surface((WIDTH, HEIGHT))
        rect(surface, 0, 0, WIDTH, HEIGHT, fill="#17291f")
        river_points = []
        for x, y in RIVER_POLYGON:
            river_points.extend([x, y])
        polygon(surface, river_points, fill="#234a55", outline="#3f737c", width=2)
        jungle_zones = [
            (250, 430, 410, 588, "#1e3c2b"),
            (350, 174, 510, 328, "#1f3f34"),
            (690, 112, 850, 270, "#1e3c2b"),
            (590, 374, 750, 530, "#1f3f34"),
        ]
        for x1, y1, x2, y2, zone_color in jungle_zones:
            oval(surface, x1, y1, x2, y2, fill=zone_color, outline="#365640", width=2)
        oval(surface, 486, 288, 614, 412, fill="#2d3a2a", outline="#d8cf9b", width=2)
        for left, top, right, bottom in BRUSH_ZONES:
            rect(surface, left, top, right, bottom, fill="#123722", outline="#3f6b42", width=2)
            for i in range(6):
                x = left + 12 + i * ((right - left - 24) / 5)
                line(surface, [x, bottom - 4, x + 8, top + 8], "#5a8b53", 2, rounded=False)
        for lane, path in self.paths.items():
            points = []
            for x, y in path:
                points.extend([x, y])
            line(surface, points, "#56624d", 54)
            line(surface, points, "#8d8b73", 34)
            line(surface, points, "#c0b988", 3, dash=(12, 14), rounded=False)

        for i in range(28):
            rng = random.Random(i)
            x = rng.randint(40, WIDTH - 40)
            y = rng.randint(45, HEIGHT - 45)
            oval(surface, x - 8, y - 5, x + 8, y + 5, fill="#203c2d")

        polygon(surface, [0, HEIGHT, 0, 505, 188, HEIGHT], fill="#203f5f")
        polygon(surface, [WIDTH, 0, WIDTH, 195, 912, 0], fill="#5b2428")
        return surface

    def draw_map(self, c):
        if self._map_surface is None:
            self._map_surface = self.build_map_surface()
        c.blit(self._map_surface, (0, 0))

    def draw_bar(self, c, x, y, width, hp, max_hp, bar_color):
        pct = 0 if max_hp <= 0 else clamp(hp / max_hp, 0, 1)
        rect(c, x, y, x + width, y + 6, fill="#252a2a")
        rect(c, x, y, x + width * pct, y + 6, fill=bar_color)

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
            threat_color = "#ffb0aa" if structure.team == "red" else "#8fd3ff"
            r = structure.attack_range
            width = 2 if is_player_target or is_visible_enemy_target else 1
            oval(c, structure.x - r, structure.y - r, structure.x + r, structure.y + r, outline=threat_color, width=width, dash=(12, 8))
            if not target:
                continue
            line(c, [structure.x, structure.y, target.x, target.y], threat_color, 2, dash=(8, 5), rounded=False)
            lock_r = target.radius + 22
            oval(c, target.x - lock_r, target.y - lock_r, target.x + lock_r, target.y + lock_r, outline=threat_color, width=2)
            if is_player_target:
                text(c, target.x, target.y - 104, self.text("structure_targeted"), threat_color, 8, True)

    def draw_core(self, c, core):
        crystal = sprites.core_sprite(core.team)
        c.blit(crystal, crystal.get_rect(center=(round(core.x), round(core.y))))
        self.draw_bar(c, core.x - 42, core.y - 50, 84, core.hp, core.max_hp, "#48d06b")

    def draw_tower(self, c, tower):
        turret = sprites.tower_sprite(tower.team, tower.tier)
        c.blit(turret, (round(tower.x - 32), round(tower.y - 30)))
        self.draw_bar(c, tower.x - 30, tower.y - 38, 60, tower.hp, tower.max_hp, "#48d06b")

    def draw_minion(self, c, minion):
        body = sprites.minion_sprite(minion.kind, minion.team, int(self.now() * 2.6) % 2)
        c.blit(body, body.get_rect(center=(round(minion.x), round(minion.y))))
        if minion.empowered:
            oval(c, minion.x - minion.radius - 8, minion.y - minion.radius - 8, minion.x + minion.radius + 8, minion.y + minion.radius + 8, outline="#f7d765", width=1, dash=(4, 4))
        self.draw_bar(c, minion.x - 18, minion.y - minion.radius - 12, 36, minion.hp, minion.max_hp, "#48d06b")

    def draw_neutral_monster(self, c, monster):
        if not monster.alive:
            if monster.respawn_at:
                left = max(0, int(monster.respawn_at - self.now() + 1))
                oval(c, monster.x - 20, monster.y - 20, monster.x + 20, monster.y + 20, fill="#12181b", outline="#394043", width=2)
                text(c, monster.x, monster.y, str(left), "#d8cf9b", 10, True)
            return
        r = monster.radius
        oval(c, monster.x - r - 8, monster.y - r - 8, monster.x + r + 8, monster.y + r + 8, fill="#101416", outline=monster.color, width=2)
        creature = sprites.monster_sprite(monster.color, r)
        c.blit(creature, creature.get_rect(center=(round(monster.x), round(monster.y))))
        self.draw_bar(c, monster.x - 34, monster.y - r - 18, 68, monster.hp, monster.max_hp, "#48d06b")

    def draw_hero(self, c, hero):
        if not hero.alive:
            x, y = (130, 580) if hero.team == "blue" else (965, 120)
            left = max(0, int(hero.respawn_at - self.now() + 1))
            text(c, x, y - 38, str(left), "#ffffff", 18, True)
            return
        angle = math.atan2(self.mouse_y - hero.y, self.mouse_x - hero.x) if hero.team == "blue" else 0
        if hero.team == "red":
            target = self.nearest_enemy(hero, 420)
            facing = target if target else self.blue_core
            angle = math.atan2(facing.y - hero.y, facing.x - hero.x)
        sprite = sprites.hero_sprite(hero.hero_key, hero.role, hero.accent, hero.team, int(self.now() * 2.6) % 2)
        rotated = sprites.rotate_for_blit(sprite, angle)
        c.blit(rotated, rotated.get_rect(center=(round(hero.x), round(hero.y))))
        if self.now() < hero.flash_until:
            overlay = flash_overlay()
            c.blit(overlay, overlay.get_rect(center=(round(hero.x), round(hero.y))))
        if self.hero_in_brush(hero):
            oval(c, hero.x - 30, hero.y - 30, hero.x + 30, hero.y + 30, outline="#76f4a0", width=2, dash=(6, 5))
        if hero.shield > 0:
            oval(c, hero.x - 34, hero.y - 34, hero.x + 34, hero.y + 34, outline="#8fd3ff", width=2)
        if self.is_stunned(hero):
            text(c, hero.x, hero.y - 82, "STUN", "#f7d765", 8, True)
        elif self.now() < hero.slowed_until:
            text(c, hero.x, hero.y - 82, "SLOW", "#9ad7ff", 8, True)
        if hero is self.enemy_hero and self.enemy_recalling:
            pct = clamp(self.enemy_recall_elapsed / self.recall_duration, 0, 1)
            rect(c, hero.x - 42, hero.y - 96, hero.x + 42, hero.y - 84, fill="#0d1215", outline="#ffb0aa")
            rect(c, hero.x - 38, hero.y - 92, hero.x - 38 + 76 * pct, hero.y - 88, fill="#ffb0aa")
            text(c, hero.x, hero.y - 106, self.text("recall_start"), "#ffb0aa", 8, True)
        self.draw_hero_plate(c, hero)

    def draw_hero_plate(self, c, hero):
        display_name = self.hero_name(hero.hero_key)
        if hero.team == "red":
            display_name = self.text("enemy_prefix", name=display_name)
        x = hero.x
        y = hero.y - 58
        rect(c, x - 54, y - 12, x + 54, y + 23, fill="#101416", outline="#2f383b")
        icon = sprites.portrait_scaled(hero.hero_key, hero.role, hero.accent, 30)
        c.blit(icon, icon.get_rect(center=(x - 46, y - 1)))
        text(c, x - 46, y + 17, str(hero.level), "#f5f1d7", 8, True)
        name_size = 8 if len(display_name) > 10 else 9
        text(c, x - 28, y - 1, display_name, "#f5f1d7", name_size, True, anchor="w")
        self.draw_bar(c, x - 32, y + 14, 74, hero.hp, hero.max_hp, "#48d06b")

    def draw_ui(self, c):
        self.skill_upgrade_buttons = []
        self.utility_buttons = []
        self.skill_detail_buttons = []
        rect(c, 0, 0, WIDTH, 50, fill="#0d1215")
        rect(c, 398, 7, 702, 43, fill="#151b1e", outline="#394043", width=2)
        text(c, 438, 25, str(self.player.kills), "#78a3ff", 16, True)
        text(c, WIDTH // 2, 25, self.format_time(self.match_time), "#f5f1d7", 14, True)
        text(c, 662, 25, str(self.enemy_hero.kills), "#ff7b7c", 16, True)
        text(c, 24, 25, self.hero_name(self.player.hero_key), "#78a3ff", 13, True, anchor="w")
        text(c, 164, 25, f"{self.text('level')} {self.player.level}", "#f5f1d7", 13, False, anchor="w")
        text(c, 260, 25, f"G {self.player.gold}", "#f7d765", 13, False, anchor="w")
        xp_pct = clamp(self.player.xp / self.player.next_xp, 0, 1)
        rect(c, 24, 43, 300, 47, fill="#252a2a")
        rect(c, 24, 43, 24 + 276 * xp_pct, 47, fill="#b38cff")
        if self.player.skill_points > 0:
            text(c, 720, 25, f"{self.text('skill_points')} {self.player.skill_points}", "#f7d765", 12, True, anchor="w")
        enemy_text = f"{self.hero_name(self.enemy_hero.hero_key)}  {self.text('level')} {self.enemy_hero.level}  G {self.enemy_hero.gold}"
        text(c, WIDTH - 24, 23, enemy_text, "#ff7b7c", 12, True, anchor="e")

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
            rect(c, 386, 54, 714, 80, fill="#101416", outline="#394043")
            text(c, WIDTH // 2, 67, self.message, "#f5f1d7", 11, True)

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
        oval(c, x - 62, y - 62, x + 62, y + 62, fill="#0d1215", outline="#394043", width=2)
        oval(c, x - 28, y - 28, x + 28, y + 28, fill="#1f2a2e", outline="#d8cf9b", width=2)
        line(c, [x - 50, y, x + 50, y], "#394043", 2, rounded=False)
        line(c, [x, y - 50, x, y + 50], "#394043", 2, rounded=False)

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
                oval(c, x - 23, y - 23, x + 23, y + 23, outline="#d8cf9b", width=2, dash=(5, 4))

    def draw_recall_indicator(self, c):
        pct = clamp(self.recall_elapsed / self.recall_duration, 0, 1)
        rect(c, 372, 60, 728, 96, fill="#0d1215", outline="#d8cf9b", width=2)
        text(c, WIDTH // 2, 71, self.text("recall_start"), "#d8cf9b", 13, True)
        rect(c, 432, 78, 668, 88, fill="#252a2a")
        rect(c, 432, 78, 432 + 236 * pct, 88, fill="#d8cf9b")
        text(c, WIDTH // 2, 103, f"{int((1 - pct) * self.recall_duration) + 1}", "#ffffff", 8, True)
        if self.player.alive:
            x, y = self.player.x, self.player.y - 84
            rect(c, x - 46, y - 10, x + 46, y + 8, fill="#0d1215", outline="#d8cf9b")
            rect(c, x - 42, y - 6, x - 42 + 84 * pct, y + 4, fill="#d8cf9b")

    def draw_minimap(self, c):
        left, top = 18, 64
        w, h = 178, 122
        rect(c, left, top, left + w, top + h, fill="#0d1215", outline="#d8cf9b", width=2)
        for path in self.paths.values():
            points = []
            for x, y in path:
                points.extend([left + x / WIDTH * w, top + y / HEIGHT * h])
            line(c, points, "#8d8b73", 4)
        for tower in self.towers:
            if tower.alive:
                self.draw_minimap_dot(c, left, top, w, h, tower.x, tower.y, team_color(tower.team), 3)
        for minion in self.minions[::2]:
            self.draw_minimap_dot(c, left, top, w, h, minion.x, minion.y, team_color(minion.team), 2)
        for monster in self.neutral_monsters:
            dot_color = monster.color if monster.alive else "#4a4f4d"
            radius = 5 if monster.camp_key == "ancient_guard" else 3
            self.draw_minimap_dot(c, left, top, w, h, monster.x, monster.y, dot_color, radius)
            if not monster.alive and monster.respawn_at:
                mx = left + monster.x / WIDTH * w
                my = top + monster.y / HEIGHT * h
                remaining = max(0, int(monster.respawn_at - self.now() + 1))
                text(c, mx, my - 8, str(remaining), "#d8cf9b", 6, True)
        self.draw_minimap_dot(c, left, top, w, h, self.blue_core.x, self.blue_core.y, "#78a3ff", 5)
        self.draw_minimap_dot(c, left, top, w, h, self.red_core.x, self.red_core.y, "#ff7b7c", 5)
        if self.player.alive:
            self.draw_minimap_dot(c, left, top, w, h, self.player.x, self.player.y, "#ffffff", 4)
        if self.enemy_hero.alive and self.hero_visible_to_player(self.enemy_hero):
            self.draw_minimap_dot(c, left, top, w, h, self.enemy_hero.x, self.enemy_hero.y, "#ffb0aa", 4)

    def draw_minimap_dot(self, c, left, top, w, h, x, y, dot_color, r):
        mx = left + x / WIDTH * w
        my = top + y / HEIGHT * h
        oval(c, mx - r, my - r, mx + r, my + r, fill=dot_color)

    def draw_projectile_trails(self, c):
        if not self.projectiles:
            return
        if self._trail_layer is None:
            self._trail_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        layer = self._trail_layer
        layer.fill((0, 0, 0, 0))
        drew = False
        for p in self.projectiles:
            count = len(p.trail)
            if not count:
                continue
            rgb = tuple(color(p.color))[:3]
            for index, (tx, ty) in enumerate(p.trail):
                fade = (index + 1) / count
                pygame.draw.circle(layer, (*rgb, int(80 * fade)), (round(tx), round(ty)), max(1, int(p.radius * 0.75 * fade)))
                drew = True
        if drew:
            c.blit(layer, (0, 0))

    def draw_locked_target(self, c):
        target = self.valid_locked_target(self.player)
        if not target:
            return
        if isinstance(target, Hero) and not self.hero_visible_to_player(target):
            return
        r = target.radius + 16
        oval(c, target.x - r, target.y - r, target.x + r, target.y + r, outline="#f7d765", width=2, dash=(7, 5))
        line(c, [target.x - r - 8, target.y, target.x - r + 6, target.y], "#f7d765", 2, rounded=False)
        line(c, [target.x + r - 6, target.y, target.x + r + 8, target.y], "#f7d765", 2, rounded=False)
        line(c, [target.x, target.y - r - 8, target.x, target.y - r + 6], "#f7d765", 2, rounded=False)
        line(c, [target.x, target.y + r - 6, target.x, target.y + r + 8], "#f7d765", 2, rounded=False)

    def draw_shop(self, c):
        self.shop_cards = []
        self.recommended_buy_button = None
        left = WIDTH - 404
        top = HEIGHT - 356
        rect(c, left, top, WIDTH - 24, HEIGHT - 84, fill="#111719", outline="#d8cf9b", width=2)
        text(c, left + 18, top + 20, self.text("shop"), "#f5f1d7", 13, True, anchor="w")
        bx1, by1, bx2, by2 = WIDTH - 158, top + 9, WIDTH - 38, top + 33
        self.recommended_buy_button = (bx1, by1, bx2, by2)
        rect(c, bx1, by1, bx2, by2, fill="#20282b", outline="#f7d765", width=2)
        text(c, (bx1 + bx2) / 2, (by1 + by2) / 2, self.text("buy_recommended"), "#f5f1d7", 9, True)
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
            rect(c, x1, y1, x2, y2, fill=fill, outline=outline, width=2)
            rect(c, x1 + 8, y1 + 10, x1 + 24, y1 + 26, fill=item["color"])
            text(c, x1 + 30, y1 + 13, self.item_name(item_key), "#f5f1d7", 8, True, anchor="w")
            text(c, x1 + 30, y1 + 28, self.item_stat_text(item), "#cfd6cd", 7, False, anchor="w")
            price = "MAX" if maxed else self.item_name(missing_item) if locked else f"G {cost}"
            text(c, x1 + 8, y2 - 6, f"Lv {current_level}/{item['max_stacks']}", "#9ea898", 7, False, anchor="w")
            text(c, x2 - 6, y2 - 6, price, "#f7d765", 8, True, anchor="e")
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
        if item.get("armor"):
            parts.append(f"+{item['armor']} {self.text('stat_armor')}")
        if item.get("magic_resist"):
            parts.append(f"+{item['magic_resist']} {self.text('stat_magic_resist')}")
        if item.get("armor_pen"):
            parts.append(f"+{item['armor_pen']} {self.text('stat_armor_pen')}")
        if item.get("magic_pen"):
            parts.append(f"+{item['magic_pen']} {self.text('stat_magic_pen')}")
        if item.get("crit_chance"):
            parts.append(f"+{int(item['crit_chance'] * 100)}% {self.text('stat_crit')}")
        if item.get("lifesteal"):
            parts.append(f"+{int(item['lifesteal'] * 100)}% {self.text('stat_lifesteal')}")
        if item.get("tenacity"):
            parts.append(f"+{int(item['tenacity'] * 100)}% {self.text('stat_tenacity')}")
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
        rect(c, left, top, right, bottom, fill="#101416", outline=item["color"], width=2)
        text(c, left + 14, top + 18, self.item_name(hovered), "#f5f1d7", 12, True, anchor="w")
        text(c, left + 14, top + 44, f"{self.text('equipment_stats')}: {self.full_item_stat_text(item)}", "#cfd6cd", 9, False, anchor="w", width=188)
        y = top + 78
        missing_item = self.missing_item_requirement(self.player, item)
        requirement_text = self.item_requirement_text(item)
        if requirement_text:
            req_color = "#ffb0aa" if missing_item else "#d8cf9b"
            text(c, left + 14, y, self.text("equipment_requires", item=requirement_text), req_color, 9, True, anchor="w", width=188)
            y += 22
        passive_key = item.get("passive")
        if passive_key:
            text(c, left + 14, y, f"{self.text('equipment_passive')}: {self.text(f'passive_{passive_key}')}", "#f7d765", 9, True, anchor="w", width=188)

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
        if item.get("armor"):
            parts.append(f"+{item['armor']} {self.text('stat_armor')}")
        if item.get("magic_resist"):
            parts.append(f"+{item['magic_resist']} {self.text('stat_magic_resist')}")
        if item.get("armor_pen"):
            parts.append(f"+{item['armor_pen']} {self.text('stat_armor_pen')}")
        if item.get("magic_pen"):
            parts.append(f"+{item['magic_pen']} {self.text('stat_magic_pen')}")
        if item.get("crit_chance"):
            parts.append(f"+{int(item['crit_chance'] * 100)}% {self.text('stat_crit')}")
        if item.get("lifesteal"):
            parts.append(f"+{int(item['lifesteal'] * 100)}% {self.text('stat_lifesteal')}")
        if item.get("tenacity"):
            parts.append(f"+{int(item['tenacity'] * 100)}% {self.text('stat_tenacity')}")
        return " / ".join(parts) if parts else "-"

    def item_requirement_text(self, item):
        parts = []
        for item_key, level in item.get("requires", {}).items():
            current = self.player.equipment.get(item_key, 0)
            parts.append(f"{self.item_name(item_key)} {current}/{level}")
        return " + ".join(parts)

    def draw_scoreboard(self, c):
        left = 218
        top = 112
        right = WIDTH - 218
        bottom = 402
        rect(c, left, top, right, bottom, fill="#0d1215", outline="#d8cf9b", width=2)
        rect(c, left, top, right, top + 48, fill="#151b1e")
        text(c, WIDTH // 2, top + 24, self.text("scoreboard"), "#f5f1d7", 18, True)
        self.draw_scoreboard_row(c, self.player, left + 28, top + 78, right - left - 56, "#78a3ff")
        self.draw_scoreboard_row(c, self.enemy_hero, left + 28, top + 188, right - left - 56, "#ff7b7c")

    def draw_scoreboard_row(self, c, hero, left, top, width, row_color):
        rect(c, left, top, left + width, top + 82, fill="#111719", outline=row_color, width=2)
        icon = sprites.portrait_scaled(hero.hero_key, hero.role, hero.accent, 40)
        c.blit(icon, icon.get_rect(center=(left + 38, top + 36)))
        oval(c, left + 42, top + 42, left + 58, top + 58, fill="#101416", outline="#f5f1d7", width=1)
        text(c, left + 50, top + 50, str(hero.level), "#f5f1d7", 8, True)
        name = self.hero_name(hero.hero_key)
        if hero.team == "red":
            name = self.text("enemy_prefix", name=name)
        text(c, left + 74, top + 20, f"{name} / {self.hero_role(hero.hero_key)}", "#f5f1d7", 13, True, anchor="w")
        stat_text = f"{self.text('kills')} {hero.kills}   {self.text('deaths')} {hero.deaths}   {self.text('gold')} {hero.gold}"
        text(c, left + 74, top + 48, stat_text, "#cfd6cd", 11, False, anchor="w")

        equipment_text = self.equipment_summary(hero)
        skill_text = " / ".join(f"{key.upper()} Lv{hero.skill_levels.get(key, 0)}" for key in ("q", "e", "r"))
        text(c, left + width - 22, top + 24, f"{self.text('equipment')}: {equipment_text}", "#d8cf9b", 10, False, anchor="e")
        text(c, left + width - 22, top + 54, skill_text, "#f7d765", 11, True, anchor="e")

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
        rect(c, left, top, right, bottom, fill=overlay, outline="#f5f1d7", width=2)
        text(c, WIDTH // 2, top + 34, self.text("settlement"), "#d8cf9b", 15, True)
        result_text = self.text("result_win") if blue_won else self.text("result_loss")
        result_color = "#78a3ff" if blue_won else "#ff7b7c"
        text(c, WIDTH // 2, top + 84, result_text, result_color, 36, True)
        text(c, WIDTH // 2, top + 124, f"{self.text('duration')} {self.format_time(self.match_time)}", "#cfd6cd", 12)
        account_color = "#f7d765" if self.match_levelups else "#d8cf9b"
        xp_prefix = self.text("level_up_account", level=self.profile["level"]) + "  " if self.match_levelups else ""
        xp_line = f"{xp_prefix}{self.text('xp_gain')} +{self.match_xp_gain}   " + self.text(
            "account_line",
            level=self.profile["level"],
            xp=self.profile["xp"],
            need=meta.xp_for_level(self.profile["level"]),
        )
        text(c, WIDTH // 2, top + 146, xp_line, account_color, 10, True)
        if self.quests_completed:
            quest_xp = sum(quest["reward"] for quest in self.quests_completed)
            text(
                c,
                WIDTH // 2,
                top + 376,
                self.text("quests_done", count=len(self.quests_completed), xp=quest_xp),
                "#76f4d1",
                10,
                True,
            )

        self.draw_settlement_stats(c, self.player, left + 42, top + 162, "#78a3ff")
        self.draw_settlement_stats(c, self.enemy_hero, WIDTH // 2 + 16, top + 162, "#ff7b7c")

        self.draw_settlement_button(c, "rematch", WIDTH // 2 - 172, bottom - 72, 150, 44, "#d8cf9b")
        self.draw_settlement_button(c, "lobby", WIDTH // 2 + 22, bottom - 72, 150, 44, "#78a3ff")

    def draw_settlement_stats(self, c, hero, left, top, panel_color):
        width = 238
        height = 206
        enemy_towers_destroyed = sum(1 for tower in self.towers if tower.team != hero.team and not tower.alive)
        rect(c, left, top, left + width, top + height, fill="#101416", outline=panel_color, width=2)
        name = self.hero_name(hero.hero_key)
        if hero.team == "red":
            name = self.text("enemy_prefix", name=name)
        text(c, left + 18, top + 24, name, "#f5f1d7", 13, True, anchor="w")
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
        for index, line_text in enumerate(left_lines):
            text(c, left + 18, top + 52 + index * 22, line_text, "#cfd6cd", 9, False, anchor="w")
        for index, line_text in enumerate(right_lines):
            text(c, left + 124, top + 52 + index * 22, line_text, "#cfd6cd", 9, False, anchor="w")
        text(
            c,
            left + 18,
            top + 188,
            " / ".join(f"{key.upper()} Lv{hero.skill_levels.get(key, 0)}" for key in ("q", "e", "r")),
            "#f7d765",
            9,
            True,
            anchor="w",
        )

    def draw_settlement_button(self, c, action, x, y, width, height, button_color):
        self.settlement_buttons.append((action, x, y, x + width, y + height))
        label = self.text("rematch") if action == "rematch" else self.text("back_lobby")
        rect(c, x, y, x + width, y + height, fill="#111719", outline=button_color, width=2)
        text(c, x + width / 2, y + height / 2, label, "#f5f1d7", 12, True)

    def draw_skill(self, c, x, y, label, ready_at, full_cd, size, skill_key=None):
        current = self.now()
        locked = skill_key is not None and not self.skill_unlocked(self.player, skill_key)
        ready = current >= ready_at and not locked
        fill = "#26313a" if ready else "#171b20"
        r = size // 2
        oval(c, x - r - 4, y - r - 4, x + r + 4, y + r + 4, fill="#0d1215", outline="#394043", width=2)
        oval(c, x - r, y - r, x + r, y + r, fill=fill, outline="#d8cf9b", width=2)
        left = 0
        if not ready and not locked:
            left = ready_at - current
            pct = clamp(left / full_cd, 0, 1)
            pie(c, x, y, r, pct)
        text(c, x, y, label, "#f5f1d7", 15, True)
        if locked:
            text(c, x, y + 25, self.text("locked"), "#ffb0aa", 8, True)
        elif not ready:
            text(c, x, y + 25, f"{left:.1f}", "#ffffff", 8, True)
        if skill_key is not None:
            self.skill_detail_buttons.append((skill_key, x - r - 8, y - r - 8, x + r + 8, y + r + 28))
            level = self.player.skill_levels.get(skill_key, 0)
            max_level = SKILL_MAX_LEVELS[skill_key]
            text(c, x, y + r + 18, f"Lv {level}/{max_level}", "#cfd6cd", 8, True)
            if self.can_upgrade_skill(self.player, skill_key):
                px = x + r - 5
                py = y - r - 17
                self.skill_upgrade_buttons.append((skill_key, px - 10, py - 10, px + 10, py + 10))
                oval(c, px - 10, py - 10, px + 10, py + 10, fill="#f7d765", outline="#101416", width=2)
                text(c, px, py - 1, "+", "#101416", 13, True)

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
        rect(c, left, top, left + 344, top + 116, fill="#101416", outline=self.player.accent, width=2)
        text(c, left + 14, top + 20, title, "#f5f1d7", 11, True, anchor="w")
        text(c, left + 14, top + 52, body, "#cfd6cd", 9, False, anchor="w", width=314)
        text(c, left + 14, top + 92, passive, self.player.accent, 8, True, anchor="w", width=314)

    def draw_tutorial(self, c):
        left, top, right, bottom = 214, 88, 592, 244
        rect(c, left, top, right, bottom, fill="#101416", outline="#d8cf9b", width=2)
        text(c, left + 18, top + 22, self.text("tutorial_title"), "#f5f1d7", 13, True, anchor="w")
        for index, tutorial_line in enumerate(self.text("tutorial_lines")):
            text(c, left + 20, top + 52 + index * 22, tutorial_line, "#cfd6cd", 9, False, anchor="w", width=338)
        bx1, by1, bx2, by2 = left + 18, bottom - 30, right - 18, bottom - 8
        self.tutorial_close_button = (bx1, by1, bx2, by2)
        hovered = bx1 <= self.mouse_x <= bx2 and by1 <= self.mouse_y <= by2
        rect(c, bx1, by1, bx2, by2, fill="#27343a" if hovered else "#1b2326", outline="#394043")
        text(c, (bx1 + bx2) / 2, (by1 + by2) / 2, self.text("tutorial_close"), "#d8cf9b", 9, True)
