"""Synthesize the game's sound effects into assets/audio/ using only the stdlib.

Run:  python tools/generate_sfx.py
"""
import math
import os
import random
import struct
import wave

RATE = 22050
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "audio")


def write_wav(name, samples):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{name}.wav")
    frames = b"".join(
        struct.pack("<h", max(-32767, min(32767, int(sample * 32767)))) for sample in samples
    )
    with wave.open(path, "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(frames)
    print("wrote", path)


def envelope(i, total, attack=0.006, decay=6.0):
    t = i / RATE
    attack_samples = max(1, int(RATE * attack))
    amp = min(1.0, i / attack_samples)
    amp *= math.exp(-decay * t / (total / RATE) * (total / RATE))
    return amp


def sweep(f0, f1, duration, amp=0.5, harmonics=((1, 1.0),), decay=5.0, noise=0.0):
    total = int(RATE * duration)
    out = []
    for i in range(total):
        t = i / RATE
        freq = f0 + (f1 - f0) * (i / total)
        phase = 2 * math.pi * (f0 * t + (f1 - f0) * t * t / (2 * duration))
        value = 0.0
        for mult, weight in harmonics:
            value += weight * math.sin(mult * phase)
        if noise:
            value = value * (1 - noise) + noise * (random.random() * 2 - 1)
        out.append(value * amp * envelope(i, total, decay=decay))
    return out


def note(freq, duration, amp=0.5, harmonics=((1, 1.0),), decay=4.0):
    return sweep(freq, freq, duration, amp, harmonics, decay)


def sequence(*parts):
    out = []
    for part in parts:
        out.extend(part)
    return out


def mix(*parts):
    length = max(len(part) for part in parts)
    return [sum(part[i] if i < len(part) else 0.0 for part in parts) for i in range(length)]


def scaled(part, factor):
    return [sample * factor for sample in part]


def main():
    random.seed(7)

    # Hero basic attack: short descending pluck.
    write_wav("attack", sweep(880, 460, 0.09, 0.5, harmonics=((1, 1.0), (2, 0.35)), decay=9.0))

    # Damage landing on a hero: noise thump plus low body.
    hit_noise = [ (random.random() * 2 - 1) * 0.5 for _ in range(int(RATE * 0.07))]
    write_wav("hit", mix(scaled(sweep(170, 90, 0.11, 0.7, decay=8.0), 1.0), scaled(hit_noise, 0.5)))

    # Regular skill cast: rising mid sweep.
    write_wav("cast", sweep(340, 720, 0.16, 0.5, harmonics=((1, 1.0), (2, 0.4)), decay=5.0))

    # Ultimate cast: heavy falling sweep with rumble.
    write_wav("cast_big", sweep(230, 85, 0.38, 0.7, harmonics=((1, 1.0), (2, 0.3)), decay=4.0, noise=0.18))

    # Hero kill: two-note rising chime.
    write_wav("kill", sequence(note(660, 0.09, 0.55, harmonics=((1, 1.0), (3, 0.2)), decay=6.0), note(990, 0.18, 0.55, harmonics=((1, 1.0), (3, 0.2)), decay=5.0)))

    # Structure destroyed: deep boom.
    write_wav("tower", mix(scaled(sweep(120, 45, 0.4, 0.8, decay=5.0), 1.0), scaled([(random.random() * 2 - 1) * 0.4 for _ in range(int(RATE * 0.1))], 0.6)))

    # Level up: three-note arpeggio.
    write_wav("levelup", sequence(note(523, 0.11, 0.5), note(659, 0.11, 0.5), note(784, 0.2, 0.55, decay=3.5)))

    # Item purchased: coin double ding.
    write_wav("buy", sequence(note(1250, 0.06, 0.45, decay=7.0), note(1650, 0.1, 0.45, decay=6.0)))

    # Recall channel: soft pulsing hum.
    hum = []
    for i in range(int(RATE * 0.5)):
        t = i / RATE
        tremolo = 0.7 + 0.3 * math.sin(2 * math.pi * 9 * t)
        hum.append(0.4 * tremolo * math.sin(2 * math.pi * 380 * t) * envelope(i, int(RATE * 0.5), decay=1.6))
    write_wav("recall", hum)

    # Flash: fast high zap.
    write_wav("flash", sweep(1500, 280, 0.12, 0.55, harmonics=((1, 1.0), (2, 0.3)), decay=7.0, noise=0.12))

    # Heal: gentle rising two-tone.
    write_wav("heal", sweep(520, 800, 0.22, 0.45, decay=4.5))

    # Match won: short fanfare.
    write_wav("victory", sequence(note(523, 0.18, 0.5), note(659, 0.18, 0.5), note(784, 0.18, 0.5), note(1046, 0.42, 0.55, decay=2.8)))

    # Match lost: descending tones.
    write_wav("defeat", sequence(note(392, 0.28, 0.5), note(311, 0.28, 0.5), note(262, 0.5, 0.5, decay=2.5)))


if __name__ == "__main__":
    main()
