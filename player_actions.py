from game_data import HEIGHT, WIDTH, clamp


class PlayerActionsMixin:
    def start_recall(self):
        if self.state != "playing" or not self.player.alive or self.recalling:
            return
        self.aiming_skill = None
        self.recalling = True
        self.recall_elapsed = 0.0
        text = self.text("recall_start")
        self.show_message(text)
        self.spawn_banner(text, "#d8cf9b", ttl=1.2)
        self.spawn_ring(self.player.x, self.player.y, "#d8cf9b", base_radius=72, ttl=0.36)
        self.spawn_particles(self.player.x, self.player.y, "#d8cf9b", count=14, speed=120, spread=1.0, radius=2.8, ttl=0.34)


    def cancel_recall(self, announce=True):
        if not self.recalling:
            return
        self.recalling = False
        self.recall_elapsed = 0.0
        if announce:
            text = self.text("recall_cancel")
            self.show_message(text)
            self.spawn_banner(text, "#ffb0aa", ttl=1.0)


    def complete_recall(self):
        if not self.recalling:
            return
        self.recalling = False
        self.recall_elapsed = 0.0
        self.player.x, self.player.y = 130, 580
        self.player.hp = self.player.max_hp
        text = self.text("recall_complete")
        self.show_message(text)
        self.spawn_banner(text, "#76f4d1", ttl=1.2)
        self.spawn_particles(self.player.x, self.player.y, "#76f4d1", count=18, speed=150, spread=1.0, radius=3.2, ttl=0.38)
        self.spawn_ring(self.player.x, self.player.y, "#76f4d1", base_radius=92, ttl=0.34)


    def start_enemy_recall(self):
        if not self.enemy_hero.alive or self.enemy_recalling:
            return
        self.enemy_recalling = True
        self.enemy_recall_elapsed = 0.0
        if self.hero_visible_to_player(self.enemy_hero):
            text = self.text("enemy_recall_start")
            self.show_message(text)
            self.spawn_banner(text, "#ffb0aa", ttl=1.0)
        self.spawn_ring(self.enemy_hero.x, self.enemy_hero.y, "#ffb0aa", base_radius=72, ttl=0.32)


    def cancel_enemy_recall(self, announce=True):
        if not self.enemy_recalling:
            return
        self.enemy_recalling = False
        self.enemy_recall_elapsed = 0.0
        if announce and self.hero_visible_to_player(self.enemy_hero):
            text = self.text("enemy_recall_cancel")
            self.show_message(text)


    def complete_enemy_recall(self):
        if not self.enemy_recalling:
            return
        self.enemy_recalling = False
        self.enemy_recall_elapsed = 0.0
        self.enemy_hero.x, self.enemy_hero.y = 965, 120
        self.enemy_hero.hp = self.enemy_hero.max_hp
        self.enemy_hero.shield = 0
        self.enemy_hero.stunned_until = 0
        self.enemy_hero.slowed_until = 0
        self.enemy_hero.slow_mult = 1.0
        if self.hero_visible_to_player(self.enemy_hero):
            text = self.text("enemy_recall_complete")
            self.show_message(text)
        self.spawn_particles(self.enemy_hero.x, self.enemy_hero.y, "#ffb0aa", count=18, speed=150, spread=1.0, radius=3.2, ttl=0.38)
        self.spawn_ring(self.enemy_hero.x, self.enemy_hero.y, "#ffb0aa", base_radius=92, ttl=0.34)


    def summoner_ready(self, key):
        return self.now() >= self.summoner_cooldowns[key]


    def cast_flash(self):
        if self.state != "playing" or not self.player.alive or not self.summoner_ready("f"):
            return
        self.summoner_cooldowns["f"] = self.now() + self.summoner_cd_durations["f"]
        old_x, old_y = self.player.x, self.player.y
        vx, vy = self.aim_vector(self.player)
        distance = 170
        self.player.x = clamp(self.player.x + vx * distance, 35, WIDTH - 35)
        self.player.y = clamp(self.player.y + vy * distance, 35, HEIGHT - 35)
        self.spawn_beam(old_x, old_y, self.player.x, self.player.y, "#f5f1d7", width=7, ttl=0.18)
        self.spawn_particles(old_x, old_y, "#f5f1d7", count=14, speed=130, spread=1.0, radius=2.8, ttl=0.32)
        self.spawn_particles(self.player.x, self.player.y, "#f5f1d7", count=18, speed=150, spread=1.15, radius=3.0, ttl=0.36)
        self.spawn_ring(self.player.x, self.player.y, "#f5f1d7", base_radius=54, ttl=0.24)
        self.show_message(self.text("flash"))


    def cast_heal(self):
        if self.state != "playing" or not self.player.alive or not self.summoner_ready("g"):
            return
        self.summoner_cooldowns["g"] = self.now() + self.summoner_cd_durations["g"]
        amount = min(self.player.max_hp - self.player.hp, self.player.max_hp * 0.32)
        self.player.hp = min(self.player.max_hp, self.player.hp + amount)
        self.add_match_stat(self.player.team, "healing", amount)
        self.spawn_particles(self.player.x, self.player.y, "#48d06b", count=22, speed=135, spread=1.05, radius=3.0, ttl=0.42)
        self.spawn_ring(self.player.x, self.player.y, "#48d06b", base_radius=76, ttl=0.34)
        self.spawn_floating_text(self.player.x, self.player.y - 24, f"+{int(amount)}", "#48d06b", ttl=0.75)
        self.show_message(self.text("heal"))

