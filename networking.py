import json
import socket
import threading
from collections import deque
from dataclasses import asdict

from equipment_data import ITEMS
from game_data import (
    Banner,
    Beam,
    Core,
    Effect,
    FloatingText,
    HEIGHT,
    Hero,
    Minion,
    NeutralMonster,
    Particle,
    Projectile,
    Tower,
    WIDTH,
    clamp,
    norm,
)


def send_json(sock, payload):
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
    sock.sendall(data)


def recv_json_lines(sock, on_message, on_close):
    buffer = b""
    try:
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                if line:
                    on_message(json.loads(line.decode("utf-8")))
    except OSError:
        pass
    finally:
        on_close()


def unit_dict(unit):
    return asdict(unit)


def projectile_dict(projectile):
    data = asdict(projectile)
    data["target"] = None
    return data


def timed_unit(data, offset):
    for key in ("next_attack", "stunned_until", "slowed_until"):
        data[key] = data.get(key, 0) + offset
    return data


def timed_hero(data, offset):
    timed_unit(data, offset)
    data["respawn_at"] = data.get("respawn_at", 0) + offset
    data["cooldowns"] = {key: value + offset for key, value in data.get("cooldowns", {}).items()}
    return data


class NetworkMixin:
    def setup_network(self, role=None, address="127.0.0.1", port=8765):
        self.network_role = role
        self.network_address = address
        self.network_port = port
        self.network_socket = None
        self.network_peer = None
        self.network_running = False
        self.network_connected = False
        self.network_events = deque()
        self.network_latest_snapshot = None
        self.network_lock = threading.Lock()
        self.network_snapshot_interval = 1 / 30
        self.network_last_snapshot_at = 0
        self.remote_keys = set()
        self.remote_mouse_x = WIDTH // 2
        self.remote_mouse_y = HEIGHT // 2
        self.remote_aiming_skill = None
        self.enemy_summoner_cooldowns = {"f": 0, "g": 0}

    def start_network(self):
        if self.network_role == "host":
            self.network_running = True
            threading.Thread(target=self._host_thread, daemon=True).start()
            self.show_message(f"LAN host: 0.0.0.0:{self.network_port}")
        elif self.network_role == "client":
            self.network_running = True
            threading.Thread(target=self._client_thread, daemon=True).start()
            self.show_message(f"Connecting {self.network_address}:{self.network_port}")

    def stop_network(self):
        self.network_running = False
        for sock in (self.network_peer, self.network_socket):
            if sock:
                try:
                    sock.close()
                except OSError:
                    pass

    def _host_thread(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("", self.network_port))
        server.listen(1)
        self.network_socket = server
        try:
            peer, _addr = server.accept()
        except OSError:
            return
        with self.network_lock:
            self.network_peer = peer
            self.network_connected = True
        send_json(peer, {"type": "hello", "team": "red"})
        recv_json_lines(peer, self._queue_network_message, self._close_peer)

    def _client_thread(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.network_address, self.network_port))
        except OSError as exc:
            self.network_events.append({"type": "error", "message": str(exc)})
            return
        with self.network_lock:
            self.network_peer = sock
            self.network_connected = True
        recv_json_lines(sock, self._queue_network_message, self._close_peer)

    def _queue_network_message(self, message):
        if message.get("type") == "snapshot":
            self.network_latest_snapshot = message
        else:
            self.network_events.append(message)

    def _close_peer(self):
        with self.network_lock:
            self.network_connected = False
            self.network_peer = None

    def send_network_input(self, event):
        if self.network_role != "client":
            return
        with self.network_lock:
            peer = self.network_peer
        if not peer:
            return
        payload = {"type": "input", **event}
        try:
            send_json(peer, payload)
        except OSError:
            self._close_peer()

    def process_network_events(self):
        while self.network_events:
            event = self.network_events.popleft()
            if event.get("type") == "input" and self.network_role == "host":
                self.handle_remote_input(event)
            elif event.get("type") == "error":
                self.show_message(event.get("message", "Network error"))

    def network_after_update(self):
        if self.network_role == "host" and self.network_connected:
            current = self.now()
            if current - self.network_last_snapshot_at < self.network_snapshot_interval:
                return
            self.network_last_snapshot_at = current
            self.broadcast_snapshot()

    def network_client_tick(self):
        if self.network_role != "client":
            return
        snapshot = self.network_latest_snapshot
        if snapshot:
            self.network_latest_snapshot = None
            self.apply_snapshot(snapshot)

    def handle_remote_input(self, event):
        kind = event.get("kind")
        key = event.get("key", "")
        self.remote_mouse_x = event.get("mouse_x", self.remote_mouse_x)
        self.remote_mouse_y = event.get("mouse_y", self.remote_mouse_y)
        if kind == "mouse":
            return
        if kind == "key_press":
            self.remote_keys.add(key)
            if key == "b":
                self.start_enemy_recall()
            elif key in {"q", "e", "r"}:
                self.start_remote_aiming_skill(key)
            elif key == "space":
                self.hero_attack(self.enemy_hero)
            elif key == "f":
                self.cast_remote_flash()
            elif key == "g":
                self.cast_remote_heal()
            elif key in {"z", "x", "c"}:
                skill_key = {"z": "q", "x": "e", "c": "r"}[key]
                self.upgrade_skill(self.enemy_hero, skill_key, silent=True)
            elif key in {"1", "2", "3", "4", "5", "6", "7", "8", "9"}:
                item_keys = list(self.enemy_hero.equipment.keys())
                index = int(key) - 1
                if 0 <= index < len(item_keys):
                    self.buy_item_for_hero(self.enemy_hero, item_keys[index], self.red_core)
        elif kind == "key_release":
            self.remote_keys.discard(key)
            if key == self.remote_aiming_skill:
                self.cast_remote_aiming_skill()
        elif kind == "left_click":
            if self.remote_aiming_skill:
                self.cast_remote_aiming_skill()
            else:
                self.hero_attack(self.enemy_hero)
        elif kind == "right_click":
            if self.remote_aiming_skill:
                self.remote_aiming_skill = None
            else:
                self.cast_remote_skill("e")

    def start_remote_aiming_skill(self, skill_key):
        hero = self.enemy_hero
        if not hero.alive or not self.skill_unlocked(hero, skill_key) or not self.skill_available(hero, skill_key):
            return
        self.remote_aiming_skill = skill_key

    def cast_remote_aiming_skill(self):
        skill_key = self.remote_aiming_skill
        self.remote_aiming_skill = None
        if skill_key:
            self.cast_remote_skill(skill_key)

    def cast_remote_skill(self, skill_key):
        old_mouse = self.mouse_x, self.mouse_y
        self.mouse_x, self.mouse_y = self.remote_mouse_x, self.remote_mouse_y
        try:
            if skill_key == "q":
                self.cast_q(self.enemy_hero)
            elif skill_key == "e":
                self.cast_e(self.enemy_hero)
            elif skill_key == "r":
                self.cast_r(self.enemy_hero)
        finally:
            self.mouse_x, self.mouse_y = old_mouse

    def cast_remote_flash(self):
        if self.now() < self.enemy_summoner_cooldowns["f"] or not self.enemy_hero.alive:
            return
        self.enemy_summoner_cooldowns["f"] = self.now() + self.summoner_cd_durations["f"]
        old_mouse = self.mouse_x, self.mouse_y
        self.mouse_x, self.mouse_y = self.remote_mouse_x, self.remote_mouse_y
        try:
            vx, vy = self.aim_vector(self.enemy_hero)
        finally:
            self.mouse_x, self.mouse_y = old_mouse
        old_x, old_y = self.enemy_hero.x, self.enemy_hero.y
        self.enemy_hero.x = clamp(self.enemy_hero.x + vx * 170, 35, WIDTH - 35)
        self.enemy_hero.y = clamp(self.enemy_hero.y + vy * 170, 35, HEIGHT - 35)
        self.spawn_beam(old_x, old_y, self.enemy_hero.x, self.enemy_hero.y, "#f5f1d7", width=7, ttl=0.18)
        self.spawn_ring(self.enemy_hero.x, self.enemy_hero.y, "#f5f1d7", base_radius=54, ttl=0.24)

    def cast_remote_heal(self):
        if self.now() < self.enemy_summoner_cooldowns["g"] or not self.enemy_hero.alive:
            return
        self.enemy_summoner_cooldowns["g"] = self.now() + self.summoner_cd_durations["g"]
        amount = min(self.enemy_hero.max_hp - self.enemy_hero.hp, self.enemy_hero.max_hp * 0.32)
        self.enemy_hero.hp = min(self.enemy_hero.max_hp, self.enemy_hero.hp + amount)
        self.add_match_stat(self.enemy_hero.team, "healing", amount)
        self.spawn_floating_text(self.enemy_hero.x, self.enemy_hero.y - 24, f"+{int(amount)}", "#48d06b", ttl=0.75)
        self.spawn_ring(self.enemy_hero.x, self.enemy_hero.y, "#48d06b", base_radius=76, ttl=0.34)

    def update_remote_hero(self, dt):
        hero = self.enemy_hero
        if not hero.alive:
            if self.now() >= hero.respawn_at:
                self.respawn(hero)
            return
        if self.enemy_recalling:
            if any(k in self.remote_keys for k in {"w", "a", "s", "d", "up", "down", "left", "right"}):
                self.cancel_enemy_recall()
                return
            self.enemy_recall_elapsed += dt
            if self.enemy_recall_elapsed >= self.recall_duration:
                self.complete_enemy_recall()
            return
        if self.is_stunned(hero):
            self.regen_hero(hero, dt)
            return

        dx = 0
        dy = 0
        if "w" in self.remote_keys or "up" in self.remote_keys:
            dy -= 1
        if "s" in self.remote_keys or "down" in self.remote_keys:
            dy += 1
        if "a" in self.remote_keys or "left" in self.remote_keys:
            dx -= 1
        if "d" in self.remote_keys or "right" in self.remote_keys:
            dx += 1
        nx, ny = norm(dx, dy)
        speed = self.effective_speed(hero)
        hero.x = clamp(hero.x + nx * speed * dt, 35, WIDTH - 35)
        hero.y = clamp(hero.y + ny * speed * dt, 35, HEIGHT - 35)
        self.regen_hero(hero, dt)

    def make_snapshot(self):
        return {
            "type": "snapshot",
            "server_now": self.now(),
            "match_time": self.match_time,
            "match_over": self.match_over,
            "winner": self.winner,
            "match_stats": self.match_stats,
            "message": self.message,
            "message_remaining": max(0, self.message_until - self.now()),
            "recalling": self.recalling,
            "recall_elapsed": self.recall_elapsed,
            "enemy_recalling": self.enemy_recalling,
            "enemy_recall_elapsed": self.enemy_recall_elapsed,
            "summoner_cooldowns": self.summoner_cooldowns,
            "enemy_summoner_cooldowns": self.enemy_summoner_cooldowns,
            "player": unit_dict(self.player),
            "enemy_hero": unit_dict(self.enemy_hero),
            "blue_core": unit_dict(self.blue_core),
            "red_core": unit_dict(self.red_core),
            "towers": [unit_dict(tower) for tower in self.towers],
            "minions": [unit_dict(minion) for minion in self.minions],
            "neutral_monsters": [unit_dict(monster) for monster in self.neutral_monsters],
            "projectiles": [projectile_dict(projectile) for projectile in self.projectiles],
            "effects": [asdict(effect) for effect in self.effects],
            "particles": [asdict(particle) for particle in self.particles],
            "beams": [asdict(beam) for beam in self.beams],
            "float_texts": [asdict(text) for text in self.float_texts],
            "banners": [asdict(banner) for banner in self.banners],
        }

    def broadcast_snapshot(self):
        with self.network_lock:
            peer = self.network_peer
        if not peer:
            return
        try:
            send_json(peer, self.make_snapshot())
        except OSError:
            self._close_peer()

    def apply_snapshot(self, snapshot):
        offset = self.now() - snapshot.get("server_now", self.now())
        blue_hero = Hero(**timed_hero(snapshot["player"], offset))
        red_hero = Hero(**timed_hero(snapshot["enemy_hero"], offset))
        self.player = red_hero
        self.enemy_hero = blue_hero
        self.blue_core = Core(**timed_unit(snapshot["blue_core"], offset))
        self.red_core = Core(**timed_unit(snapshot["red_core"], offset))
        self.towers = [Tower(**timed_unit(data, offset)) for data in snapshot.get("towers", [])]
        self.minions = [Minion(**timed_unit(data, offset)) for data in snapshot.get("minions", [])]
        self.neutral_monsters = [NeutralMonster(**timed_unit(data, offset)) for data in snapshot.get("neutral_monsters", [])]
        self.projectiles = [Projectile(**data) for data in snapshot.get("projectiles", [])]
        self.effects = [Effect(**data) for data in snapshot.get("effects", [])]
        self.particles = [Particle(**data) for data in snapshot.get("particles", [])]
        self.beams = [Beam(**data) for data in snapshot.get("beams", [])]
        self.float_texts = [FloatingText(**data) for data in snapshot.get("float_texts", [])]
        self.banners = [Banner(**data) for data in snapshot.get("banners", [])]
        self.match_time = snapshot.get("match_time", self.match_time)
        self.match_over = snapshot.get("match_over", False)
        self.winner = snapshot.get("winner")
        stats = snapshot.get("match_stats")
        if stats:
            merged_stats = self.blank_match_stats()
            for team in ("blue", "red"):
                merged_stats[team].update(stats.get(team, {}))
            self.match_stats = merged_stats
        self.message = snapshot.get("message", "")
        self.message_until = self.now() + snapshot.get("message_remaining", 0)
        self.recalling = snapshot.get("enemy_recalling", False)
        self.recall_elapsed = snapshot.get("enemy_recall_elapsed", 0)
        self.enemy_recalling = snapshot.get("recalling", False)
        self.enemy_recall_elapsed = snapshot.get("recall_elapsed", 0)
        self.summoner_cooldowns = {key: value + offset for key, value in snapshot.get("enemy_summoner_cooldowns", {}).items()}
        self.enemy_summoner_cooldowns = {key: value + offset for key, value in snapshot.get("summoner_cooldowns", {}).items()}

    def buy_item_for_hero(self, hero, item_key, home_core):
        if not hero.alive:
            return False
        if abs(hero.x - home_core.x) > 155 or abs(hero.y - home_core.y) > 155:
            return False
        item = ITEMS[item_key]
        current_level = hero.equipment[item_key]
        if current_level >= item["max_stacks"]:
            return False
        missing_item = self.missing_item_requirement(hero, item)
        if missing_item:
            return False
        cost = item["cost"] + current_level * 70
        if hero.gold < cost:
            return False
        hero.gold -= cost
        hero.equipment[item_key] += 1
        self.add_match_stat(hero.team, "items_spent", cost)
        if "attack_damage" in item:
            hero.attack_damage += item["attack_damage"]
        if "skill_power" in item:
            hero.skill_power += item["skill_power"]
        if "speed" in item:
            hero.speed += item["speed"]
        if "attack_range" in item:
            hero.attack_range += item["attack_range"]
        if "attack_cd_reduce" in item:
            hero.attack_cd = max(0.2, hero.attack_cd - item["attack_cd_reduce"])
        if "max_hp" in item:
            hero.max_hp += item["max_hp"]
            hero.hp += item["max_hp"]
        return True
