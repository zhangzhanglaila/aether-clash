import argparse
import random
import time

import pygame

from game_data import (
    Core,
    HEROES,
    HEIGHT,
    Hero,
    JUNGLE_CAMPS,
    L10N,
    MODE_RULES,
    NeutralMonster,
    Tower,
    WIDTH,
)
from equipment_data import ITEMS
from ai import AiMixin
from audio import SoundBank
from combat import CombatMixin
from economy import EconomyMixin
from input_handler import InputMixin
from map_systems import MapSystemsMixin
from networking import NetworkMixin
from player_actions import PlayerActionsMixin
from rendering import RenderingMixin


class MobaGame(RenderingMixin, InputMixin, AiMixin, CombatMixin, MapSystemsMixin, EconomyMixin, PlayerActionsMixin, NetworkMixin):
    def __init__(
        self,
        network_role=None,
        network_address="127.0.0.1",
        network_port=8765,
        mode_key="rank",
        hero_key="vanguard",
        remote_hero_key="ranger",
        language="zh",
    ):
        pygame.init()
        pygame.display.set_caption("Aether Clash")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.world_surface = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.sfx = SoundBank()
        self._sound_last_played = {}
        self.shake_until = 0.0
        self.shake_strength = 0.0
        self.shake_duration = 1.0
        self.freeze_until = 0.0
        self.keys = set()
        self.mouse_x = WIDTH // 2
        self.mouse_y = HEIGHT // 2
        self.last_time = time.perf_counter()
        self.spawn_timer = 0
        self.wave_index = 0
        self.enemy_xp_timer = 0
        self.match_over = False
        self.winner = None
        self.message_until = 0
        self.message = ""
        self.recalling = False
        self.recall_elapsed = 0.0
        self.recall_duration = 3.0
        self.enemy_recalling = False
        self.enemy_recall_elapsed = 0.0
        self.summoner_cooldowns = {"f": 0, "g": 0}
        self.summoner_cd_durations = {"f": 12.0, "g": 18.0}
        self.aiming_skill = None
        self.show_scoreboard = False
        self.locked_target = None
        self.tutorial_visible = True
        self.tutorial_close_button = None
        self.skill_detail_buttons = []
        self.match_stats = self.blank_match_stats()

        self._map_surface = None
        self._menu_backdrop = None

        self.paths = {
            "top": [(92, 608), (96, 150), (910, 146), (1002, 112)],
            "mid": [(92, 608), (550, 350), (1002, 112)],
            "bot": [(92, 608), (250, 565), (920, 565), (1002, 112)],
        }

        self.language = language
        self.state = "language"
        self.language_buttons = []
        self.lobby_buttons = []
        self.mode_cards = []
        self.hero_cards = []
        self.shop_cards = []
        self.utility_buttons = []
        self.recommended_buy_button = None
        self.skill_upgrade_buttons = []
        self.settlement_buttons = []
        self.loading_started_at = 0
        self.selected_mode_key = None
        self.selected_hero_key = None
        self.player = None
        self.enemy_hero = None
        self.blue_core = None
        self.red_core = None
        self.towers = []
        self.minions = []
        self.neutral_monsters = []
        self.projectiles = []
        self.effects = []
        self.damage_over_times = []
        self.particles = []
        self.beams = []
        self.float_texts = []
        self.banners = []
        self.setup_network(network_role, network_address, network_port)

        if self.network_role == "host":
            self.selected_mode_key = mode_key
            self.reset_match(hero_key, enemy_hero_key=remote_hero_key)
            self.state = "playing"
            self.start_network()
        elif self.network_role == "client":
            self.selected_mode_key = mode_key
            self.reset_match(remote_hero_key, enemy_hero_key=hero_key)
            self.player, self.enemy_hero = self.enemy_hero, self.player
            self.state = "playing"
            self.start_network()

    def text(self, key, /, **kwargs):
        value = L10N[self.language][key]
        if kwargs:
            return value.format(**kwargs)
        return value

    def blank_match_stats(self):
        return {
            "blue": {
                "damage_dealt": 0,
                "hero_damage": 0,
                "structure_damage": 0,
                "damage_taken": 0,
                "healing": 0,
                "shielding": 0,
                "gold_earned": 0,
                "xp_earned": 0,
                "towers_destroyed": 0,
                "monsters_slain": 0,
                "minions_last_hit": 0,
                "items_spent": 0,
            },
            "red": {
                "damage_dealt": 0,
                "hero_damage": 0,
                "structure_damage": 0,
                "damage_taken": 0,
                "healing": 0,
                "shielding": 0,
                "gold_earned": 0,
                "xp_earned": 0,
                "towers_destroyed": 0,
                "monsters_slain": 0,
                "minions_last_hit": 0,
                "items_spent": 0,
            },
        }

    def add_match_stat(self, team, key, amount):
        if team not in {"blue", "red"} or key not in self.match_stats[team]:
            return
        self.match_stats[team][key] += max(0, amount)

    def hero_name(self, hero_key):
        return L10N[self.language]["hero_names"][hero_key]

    def hero_role(self, hero_key):
        return L10N[self.language]["hero_roles"][hero_key]

    def hero_skill(self, hero_key, skill_key):
        return L10N[self.language]["skills"][hero_key][skill_key]

    def hero_skill_detail(self, hero_key, skill_key):
        return L10N[self.language]["skill_details"][hero_key][skill_key]

    def hero_passive_name(self, hero_key):
        return L10N[self.language]["passives"][hero_key]["name"]

    def hero_passive_detail(self, hero_key):
        return L10N[self.language]["passives"][hero_key]["detail"]

    def hero_skill_traits(self, hero_key):
        return L10N[self.language]["skill_traits"][hero_key]

    def item_name(self, item_key):
        return L10N[self.language]["items"][item_key]

    def lane_name(self, lane):
        return L10N[self.language]["lanes"][lane]

    def jungle_name(self, camp_key):
        return L10N[self.language]["jungle"][camp_key]

    def mode_rule(self):
        return MODE_RULES.get(self.selected_mode_key or "rank", MODE_RULES["rank"])

    def make_hero(self, hero_key, team, x, y):
        config = HEROES[hero_key]
        role_armor = {"Tank": 32, "Fighter": 27, "Support": 24, "Assassin": 22, "Marksman": 20, "Mage": 18}
        role_magic_resist = {"Tank": 24, "Fighter": 22, "Support": 24, "Assassin": 18, "Marksman": 18, "Mage": 20}
        return Hero(
            x=x,
            y=y,
            team=team,
            hp=config["hp"],
            max_hp=config["hp"],
            radius=18,
            speed=config["speed"],
            attack_damage=config["attack_damage"],
            attack_range=config["attack_range"],
            attack_cd=config["attack_cd"],
            name=config["name"],
            hero_key=hero_key,
            role=config["role"],
            accent=config["accent"],
            skill_cds=dict(config["cooldowns"]),
            skill_names=dict(config["skills"]),
            armor=config.get("armor", role_armor.get(config["role"], 20)),
            magic_resist=config.get("magic_resist", role_magic_resist.get(config["role"], 18)),
            equipment={key: 0 for key in ITEMS},
        )

    def reset_match(self, hero_key, enemy_hero_key="vanguard"):
        self.selected_hero_key = hero_key
        rule = self.mode_rule()
        self.match_over = False
        self.winner = None
        self.shake_until = 0.0
        self.freeze_until = 0.0
        self.spawn_timer = 0
        self.wave_index = 0
        self.match_time = 0
        self.message_until = 0
        self.message = ""
        self.recalling = False
        self.recall_elapsed = 0.0
        self.enemy_recalling = False
        self.enemy_recall_elapsed = 0.0
        self.summoner_cooldowns = {"f": 0, "g": 0}
        self.enemy_summoner_cooldowns = {"f": 0, "g": 0}
        self.aiming_skill = None
        self.show_scoreboard = False
        self.locked_target = None
        self.tutorial_visible = True
        self.tutorial_close_button = None
        self.skill_detail_buttons = []
        self.match_stats = self.blank_match_stats()
        self.player = self.make_hero(hero_key, "blue", 130, 580)
        self.enemy_hero = self.make_hero(enemy_hero_key, "red", 965, 120)
        self.enemy_hero.name = f"Red {HEROES[enemy_hero_key]['name']}"
        self.apply_starting_level(self.player, rule["start_level"])
        self.player.gold = rule["start_gold"]
        self.match_stats["blue"]["gold_earned"] = self.player.gold
        self.scale_hero_stats(self.enemy_hero, rule["enemy_stat_mult"])
        self.blue_core = Core(
            74,
            626,
            "blue",
            1000 * rule["core_hp_mult"],
            1000 * rule["core_hp_mult"],
            35,
            attack_damage=70,
            attack_range=210,
            attack_cd=0.85,
            name="Blue Core",
        )
        self.red_core = Core(
            1008,
            112,
            "red",
            1000 * rule["core_hp_mult"],
            1000 * rule["core_hp_mult"],
            35,
            attack_damage=70,
            attack_range=210,
            attack_cd=0.85,
            name="Red Core",
        )
        self.towers = self.make_towers()
        self.scale_structures(rule)
        self.minions = []
        self.neutral_monsters = self.make_neutral_monsters()
        self.projectiles = []
        self.effects = []
        self.damage_over_times = []
        self.particles = []
        self.beams = []
        self.float_texts = []
        self.banners = []
        self.shop_cards = []
        self.utility_buttons = []
        self.recommended_buy_button = None
        self.skill_upgrade_buttons = []
        self.settlement_buttons = []

    def apply_starting_level(self, hero, level):
        for _ in range(max(0, level - 1)):
            self.level_up(hero, silent=True)

    def scale_hero_stats(self, hero, multiplier):
        hero.max_hp *= multiplier
        hero.hp = hero.max_hp
        hero.attack_damage *= multiplier

    def scale_structures(self, rule):
        for tower in self.towers:
            tower.max_hp *= rule["tower_hp_mult"]
            tower.hp = tower.max_hp

    def make_towers(self):
        data = [
            ("blue", "top", "base", 120, 330),
            ("blue", "top", "outer", 310, 148),
            ("red", "top", "outer", 810, 146),
            ("red", "top", "base", 970, 255),
            ("blue", "mid", "base", 280, 510),
            ("red", "mid", "base", 820, 190),
            ("blue", "bot", "base", 290, 565),
            ("blue", "bot", "outer", 540, 565),
            ("red", "bot", "outer", 885, 500),
            ("red", "bot", "base", 980, 335),
        ]
        return [
            Tower(
                x=x,
                y=y,
                team=team,
                hp=360,
                max_hp=360,
                radius=24,
                attack_damage=52,
                attack_range=180,
                attack_cd=0.85,
                lane=lane,
                tier=tier,
                name=f"{team.title()} {lane.title()} Tower",
            )
            for team, lane, tier, x, y in data
        ]

    def make_neutral_monsters(self):
        monsters = []
        for camp_key, config in JUNGLE_CAMPS.items():
            monsters.append(
                NeutralMonster(
                    x=config["x"],
                    y=config["y"],
                    team="neutral",
                    hp=config["hp"],
                    max_hp=config["hp"],
                    radius=config["radius"],
                    speed=0,
                    attack_damage=config["attack_damage"],
                    attack_range=128,
                    attack_cd=1.05,
                    camp_key=camp_key,
                    name=camp_key,
                    gold_reward=config["gold"],
                    xp_reward=config["xp"],
                    respawn_delay=config["respawn"],
                    color=config["color"],
                )
            )
        return monsters

    def start(self):
        while self.running:
            self.loop()
        pygame.quit()

    def now(self):
        return time.perf_counter()

    def play_sound(self, name, volume=1.0, min_interval=0.0):
        if not self.sfx.enabled:
            return
        last = self._sound_last_played.get(name, -1.0)
        current = self.now()
        if current - last < min_interval:
            return
        self._sound_last_played[name] = current
        self.sfx.play(name, volume)

    def trigger_shake(self, strength, duration):
        current = self.now()
        if current < self.shake_until and self.shake_strength >= strength:
            return
        self.shake_until = current + duration
        self.shake_duration = duration
        self.shake_strength = strength

    def shake_offset(self):
        current = self.now()
        if current >= self.shake_until:
            return 0, 0
        remaining = (self.shake_until - current) / max(self.shake_duration, 1e-6)
        strength = self.shake_strength * remaining
        return random.uniform(-strength, strength), random.uniform(-strength, strength)

    def trigger_freeze(self, duration):
        self.freeze_until = max(self.freeze_until, self.now() + duration)

    def loop(self):
        current = time.perf_counter()
        dt = min(0.05, current - self.last_time)
        self.last_time = current
        self.handle_events()
        if not self.running:
            return
        if self.state == "loading" and current - self.loading_started_at >= 1.15:
            self.state = "playing"
            self.last_time = time.perf_counter()
        if self.state == "playing":
            self.process_network_events()
            if self.network_role == "client":
                self.network_client_tick()
            elif not self.match_over and self.now() >= self.freeze_until:
                self.update(dt)
                self.network_after_update()
        self.draw()
        pygame.display.flip()
        self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                key = key_name(event.key)
                if key:
                    self.on_key_down(key)
            elif event.type == pygame.KEYUP:
                key = key_name(event.key)
                if key:
                    self.on_key_up(key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.on_left_click(event.pos[0], event.pos[1])
                elif event.button == 3:
                    self.on_right_click(event.pos[0], event.pos[1])
            elif event.type == pygame.WINDOWFOCUSLOST:
                self.keys.clear()
        self.mouse_x, self.mouse_y = pygame.mouse.get_pos()

    def update(self, dt):
        self.match_time += dt
        self.enemy_xp_timer += dt
        if self.enemy_xp_timer >= 5:
            self.enemy_xp_timer = 0
            self.gain_xp(self.enemy_hero, self.mode_rule()["enemy_xp_rate"])
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_wave()
            self.spawn_timer = self.mode_rule()["spawn_interval"]

        self.update_player(dt)
        self.update_enemy_hero(dt)
        self.update_neutral_monsters()
        self.update_minions(dt)
        self.update_towers()
        self.update_cores()
        self.update_projectiles(dt)
        self.update_damage_over_time(dt)
        self.update_effects(dt)
        self.cleanup_dead()
        self.check_winner()

    def show_message(self, message):
        self.message = message
        self.message_until = self.now() + 2.2


SPECIAL_KEYS = {
    pygame.K_ESCAPE: "escape",
    pygame.K_RETURN: "return",
    pygame.K_SPACE: "space",
    pygame.K_TAB: "tab",
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
}


def key_name(key_code):
    if pygame.K_a <= key_code <= pygame.K_z:
        return chr(key_code)
    if pygame.K_0 <= key_code <= pygame.K_9:
        return chr(key_code)
    return SPECIAL_KEYS.get(key_code)


def parse_args():
    parser = argparse.ArgumentParser(description="Run Aether Clash.")
    role = parser.add_mutually_exclusive_group()
    role.add_argument("--lan-host", action="store_true", help="Host a LAN 1v1 match as blue side.")
    role.add_argument("--lan-join", metavar="HOST", help="Join a LAN 1v1 match as red side.")
    parser.add_argument("--port", type=int, default=8765, help="LAN TCP port.")
    parser.add_argument("--mode", choices=sorted(MODE_RULES), default="rank", help="Match mode.")
    parser.add_argument("--hero", choices=sorted(HEROES), default="vanguard", help="Your hero.")
    parser.add_argument("--remote-hero", choices=sorted(HEROES), default="ranger", help="Expected remote hero.")
    parser.add_argument("--language", choices=("zh", "en"), default="zh", help="Initial UI language.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    role = "host" if args.lan_host else "client" if args.lan_join else None
    MobaGame(
        network_role=role,
        network_address=args.lan_join or "127.0.0.1",
        network_port=args.port,
        mode_key=args.mode,
        hero_key=args.hero,
        remote_hero_key=args.remote_hero,
        language=args.language,
    ).start()
