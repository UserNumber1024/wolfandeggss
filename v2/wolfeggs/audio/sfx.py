"""Звуковые эффекты (spec 7.2). Всё синтезируется при запуске."""

from __future__ import annotations

import numpy as np

from .synth import (
    concat, envelope, lowpass, mix, mixer_available, noise, notes, silence, sweep, to_sound, tone, vibrato,
)

SFX_NAMES = (
    "catch", "catch_golden", "catch_heart", "catch_clock", "catch_magnet", "catch_silence",
    "rotten_caught", "rotten_dodged", "splat", "chick", "cluck", "life_lost", "combo_up",
    "combo_reset", "hare", "wave_start", "stage_start", "row_open", "pause", "defeat",
    "victory", "menu_move", "menu_select",
)
CATCH_VARIANTS = 8  # высота «catch» растёт с серией


def _semi(base: float, n: float) -> float:
    return base * 2 ** (n / 12)


def _catch(i: int) -> np.ndarray:
    f = _semi(523.25, 2 * i)
    pop = envelope(sweep(f, f * 1.5, 0.12, "square", 0.32), 0.002, 0.04, 0.45, 0.05)
    click = envelope(noise(0.02, 0.15), 0.0, 0.01, 0.2, 0.01)
    return mix(pop, click)


def build_sfx() -> dict[str, list[np.ndarray]]:
    C5, E5, G5, C6 = 523.25, 659.25, 783.99, 1046.5
    rng = np.random.default_rng(11)
    bank: dict[str, list[np.ndarray]] = {
        "catch": [_catch(i) for i in range(CATCH_VARIANTS)],
        "catch_golden": [mix(
            notes([(C5, 0.05), (E5, 0.05), (G5, 0.05), (C6, 0.16)], "square", 0.3, 0.25),
            concat(silence(0.12), envelope(tone(2093, 0.18, "triangle", vol=0.2), 0.001, 0.05, 0.3, 0.1)),
        )],
        "catch_heart": [notes([(E5, 0.1), (_semi(E5, 5), 0.22)], "triangle", 0.5)],
        "catch_clock": [concat(*(
            concat(envelope(tone(f, 0.03, "square", 0.3, 0.35), 0.0, 0.01, 0.3, 0.015), silence(0.09))
            for f in (2000, 1500, 2000, 1500)
        ))],
        "catch_magnet": [envelope(vibrato(440, 0.42, 0.08, 18, "square", 0.3), 0.01, 0.1, 0.7, 0.15)],
        "catch_silence": [envelope(sweep(880, 220, 0.5, "triangle", 0.45), 0.01, 0.1, 0.8, 0.25)],
        "rotten_caught": [mix(
            envelope(lowpass(noise(0.35, 0.6, rng), 12), 0.005, 0.1, 0.5, 0.15),
            envelope(sweep(220, 80, 0.35, "square", 0.3), 0.005, 0.1, 0.6, 0.15),
        )],
        "rotten_dodged": [notes([(330, 0.07), (392, 0.1)], "triangle", 0.35)],
        "splat": [mix(
            envelope(noise(0.18, 0.7, rng), 0.0, 0.05, 0.25, 0.1),
            envelope(sweep(300, 70, 0.18, "square", 0.25), 0.0, 0.05, 0.4, 0.1),
        )],
        "chick": [concat(*(
            concat(envelope(sweep(2000, 2700, 0.05, "square", 0.18), 0.002, 0.02, 0.5, 0.02), silence(0.04))
            for _ in range(3)
        ))],
        "cluck": [concat(
            envelope(sweep(340, 260, 0.06, "square", 0.22), 0.002, 0.02, 0.5, 0.02), silence(0.04),
            envelope(sweep(320, 240, 0.07, "square", 0.22), 0.002, 0.02, 0.5, 0.03),
        )],
        "life_lost": [envelope(sweep(440, 110, 0.38, "square", 0.35), 0.002, 0.1, 0.6, 0.15)],
        "combo_up": [notes([(_semi(C5, k), 0.045) for k in (0, 4, 7, 12, 16)], "square", 0.3, 0.25)],
        "combo_reset": [envelope(sweep(600, 180, 0.28, "saw", 0.3), 0.002, 0.1, 0.5, 0.1)],
        "hare": [concat(
            envelope(sweep(300, 900, 0.12, "sine", 0.45), 0.002, 0.03, 0.8, 0.02),
            envelope(sweep(900, 320, 0.18, "sine", 0.45), 0.0, 0.05, 0.7, 0.08),
        )],
        "wave_start": [notes([(G5, 0.08), (G5, 0.08), (C6, 0.22)], "square", 0.32, 0.25)],
        "stage_start": [mix(
            notes([(C5, 0.1), (E5, 0.1), (G5, 0.1), (C6, 0.1), (G5, 0.1), (C6, 0.45)], "square", 0.3, 0.25),
            concat(silence(0.5), envelope(tone(261.6, 0.45, "triangle", vol=0.4), 0.01, 0.1, 0.6, 0.2)),
        )],
        "row_open": [mix(
            envelope(lowpass(noise(0.6, 0.5, rng), 30), 0.05, 0.2, 0.6, 0.25),
            envelope(sweep(110, 440, 0.6, "triangle", 0.4), 0.05, 0.1, 0.8, 0.2),
        )],
        "pause": [notes([(880, 0.05), (660, 0.08)], "square", 0.25, 0.25)],
        "defeat": [notes([(_semi(440, k), d) for k, d in ((0, 0.2), (-2, 0.2), (-4, 0.2), (-9, 0.6))], "square", 0.32)],
        "victory": [mix(
            notes([(C5, 0.12), (E5, 0.12), (G5, 0.12), (C6, 0.24), (G5, 0.12), (C6, 0.6)], "square", 0.3, 0.25),
            notes([(261.6, 0.36), (392, 0.36), (523.25, 0.6)], "triangle", 0.35),
        )],
        "menu_move": [envelope(tone(880, 0.04, "square", 0.25, 0.22), 0.001, 0.01, 0.5, 0.015)],
        "menu_select": [envelope(sweep(660, 990, 0.08, "square", 0.25), 0.001, 0.02, 0.6, 0.03)],
    }
    return bank


class Sfx:
    def __init__(self, volume: float = 0.8, enabled: bool = True):
        self.enabled = enabled and mixer_available()
        self._volume = volume
        self.sounds: dict[str, list] = {}
        if self.enabled:
            self.sounds = {name: [to_sound(s) for s in variants] for name, variants in build_sfx().items()}
            self.volume = volume

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, value))
        for variants in self.sounds.values():
            for snd in variants:
                snd.set_volume(self._volume)

    def play(self, name: str, variant: int = 0) -> None:
        if not self.enabled:
            return
        variants = self.sounds[name]
        variants[max(0, min(variant, len(variants) - 1))].play()
