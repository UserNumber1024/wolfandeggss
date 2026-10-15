"""Погода по сезонам: только визуал, полупрозрачная (spec 4.4)."""

from __future__ import annotations

import math
import random

import pygame

from .layout import H, W

MAX_PARTICLES = 250

# сезон -> список (вид, базовая частота в секунду)
STAGE_WEATHER = {
    1: [("petal", 6), ("drizzle", 10)],
    2: [("pollen", 10)],
    3: [("leaf", 10), ("rain", 22)],
    4: [("snow", 34)],
}
COLORS = {
    "petal": (250, 196, 214, 220), "drizzle": (200, 220, 255, 120), "pollen": (255, 240, 150, 170),
    "leaf": (220, 120, 40, 230), "rain": (180, 200, 240, 130), "snow": (255, 255, 255, 210),
    "debris": (120, 86, 50, 220),
}


class Weather:
    def __init__(self, stage: int):
        self.stage = stage
        self.intensity = 0.0
        self.wind = 0.0
        self.t = 0.0
        self.parts: list[list] = []  # [kind, x, y, vx, vy, phase]
        self._acc: dict[str, float] = {}
        self._layer = pygame.Surface((W, H), pygame.SRCALPHA)

    def set_stage(self, stage: int) -> None:
        self.stage = stage

    def set_intensity(self, level: float) -> None:
        self.intensity = max(0.0, min(1.0, level))

    def set_wind(self, strength: float) -> None:
        self.wind = max(0.0, min(1.0, strength))

    def count(self) -> int:
        return len(self.parts)

    def _rates(self) -> list[tuple[str, float]]:
        rates = []
        for kind, base in STAGE_WEATHER[self.stage]:
            k = 1 + self.intensity * (3 if kind == "snow" else 1)  # зимой метель усиливается
            rates.append((kind, base * k))
        if self.wind > 0.5:
            rates.append(("debris", 30 * self.wind))
        return rates

    def update(self, dt: float) -> None:
        self.t += dt
        for kind, rate in self._rates():
            self._acc[kind] = self._acc.get(kind, 0.0) + rate * dt
            while self._acc[kind] >= 1 and len(self.parts) < MAX_PARTICLES:
                self._acc[kind] -= 1
                self._spawn(kind)
            self._acc[kind] = min(self._acc[kind], 1.0)
        push = self.wind * 160
        alive = []
        for p in self.parts:
            kind = p[0]
            sway = math.sin(self.t * 2 + p[5]) * (20 if kind in ("petal", "leaf", "snow", "pollen") else 0)
            p[1] += (p[3] + push + sway) * dt
            p[2] += p[4] * dt
            if -20 < p[1] < W + 20 and p[2] < H + 5:
                alive.append(p)
        self.parts = alive

    def _spawn(self, kind: str) -> None:
        x = random.uniform(-40 if self.wind else 0, W)
        y = random.uniform(-10, 0)
        if kind == "debris":
            x, y = -10, random.uniform(40, H - 40)
        speeds = {"petal": (8, 30), "drizzle": (0, 220), "pollen": (6, 8), "leaf": (10, 40),
                  "rain": (-10, 300), "snow": (0, 26 + 30 * self.intensity), "debris": (260, 20)}
        vx, vy = speeds[kind]
        if kind == "pollen":
            y = random.uniform(80, H - 40)
            vy = random.uniform(-4, 4)
        self.parts.append([kind, x, y, vx * random.uniform(0.7, 1.3), vy * random.uniform(0.8, 1.2),
                           random.uniform(0, 6.28)])

    def draw(self, surf: pygame.Surface) -> None:
        if not self.parts:
            return
        layer = self._layer
        layer.fill((0, 0, 0, 0))
        for kind, x, y, _, _, ph in self.parts:
            col = COLORS[kind]
            ix, iy = int(x), int(y)
            if kind in ("drizzle", "rain"):
                layer.fill(col, (ix, iy, 1, 4 if kind == "rain" else 3))
            elif kind in ("petal", "leaf", "debris"):
                w = 2 if math.sin(self.t * 6 + ph) > 0 else 1
                layer.fill(col, (ix, iy, w, 2))
            elif kind == "snow":
                size = 2 if ph > 3.5 else 1
                layer.fill(col, (ix, iy, size, size))
            else:
                layer.fill(col, (ix, iy, 1, 1))
        surf.blit(layer, (0, 0))
