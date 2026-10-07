"""Loads assets/audio/*.wav and plays named sound effects; silently no-ops if audio is unavailable."""
import os

import pygame


class SoundBank:
    def __init__(self):
        self.sounds = {}
        self.enabled = False
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            self.enabled = True
        except pygame.error:
            return
        audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "audio")
        if not os.path.isdir(audio_dir):
            return
        for file_name in sorted(os.listdir(audio_dir)):
            if not file_name.lower().endswith(".wav"):
                continue
            key = os.path.splitext(file_name)[0]
            try:
                self.sounds[key] = pygame.mixer.Sound(os.path.join(audio_dir, file_name))
            except pygame.error:
                continue

    def play(self, name, volume=1.0):
        sound = self.sounds.get(name)
        if sound is None or not self.enabled:
            return
        sound.set_volume(max(0.0, min(1.0, volume)))
        sound.play()
