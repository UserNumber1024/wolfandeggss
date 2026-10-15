"""«Сочность»: тряска, hit-stop, частицы, всплывающий текст (spec 5.9)."""

from __future__ import annotations

import random

import pygame

from .font import PixelFont

SHAKE_MAX_PX = 4
HITSTOP_MAX = 0.08


class Shake:
    def __init__(self) -> None:
        self.strength = 0.0
        self.time = 0.0
        self.duration = 0.0

    def add(self, px: float, dur: float) -> None:
        active = self.time > 0
        self.strength = min(SHAKE_MAX_PX, max(self.strength if active else 0.0, px))
        self.time = max(self.time if active else 0.0, dur)
        self.duration = self.time  # затухание отсчитывается от свежего толчка

    def update(self, dt: float) -> None:
        self.time = max(0.0, self.time - dt)

    @property
    def offset(self) -> tuple[int, int]:
        if self.time <= 0 or self.duration <= 0:
            return (0, 0)
        k = self.strength * min(1.0, self.time / self.duration)
        r = int(round(k))
        if r == 0:
            return (0, 0)
        return (random.randint(-r, r), random.randint(-r, r))


class HitStop:
    def __init__(self) -> None:
        self.time = 0.0

    def trigger(self, sec: float) -> None:
        self.time = max(self.time, min(sec, HITSTOP_MAX))

    def update(self, real_dt: float) -> None:
        self.time = max(0.0, self.time - real_dt)

    @property
    def active(self) -> bool:
        return self.time > 0


class Particles:
    MAX = 300

    def __init__(self) -> None:
        self.parts: list[list] = []  # x, y, vx, vy, life, max_life, color, size, gravity

    def burst(self, x: float, y: float, color, n: int, speed: float, life: float,
              gravity: float = 260.0, size: int = 1, up: float = 0.0) -> None:
        for _ in range(n):
            if len(self.parts) >= self.MAX:
                self.parts.pop(0)
            vx = random.uniform(-speed, speed)
            vy = random.uniform(-speed, speed * 0.4) - up
            lf = life * random.uniform(0.6, 1.1)
            self.parts.append([x, y, vx, vy, lf, lf, color, size, gravity])

    def update(self, dt: float) -> None:
        alive = []
        for p in self.parts:
            p[4] -= dt
            if p[4] <= 0:
                continue
            p[3] += p[8] * dt
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            alive.append(p)
        self.parts = alive

    def draw(self, surf: pygame.Surface) -> None:
        for x, y, _, _, life, max_life, color, size, _ in self.parts:
            s = size if life > max_life * 0.4 else max(1, size - 1)
            surf.fill(color, (int(x), int(y), s, s))

    def count(self) -> int:
        return len(self.parts)


class FloatingTexts:
    LIFE = 0.8

    def __init__(self, font: PixelFont) -> None:
        self.font = font
        self.items: list[list] = []  # surf, x, y, t

    def spawn(self, text: str, x: float, y: float, color) -> None:
        surf = self.font.render(text, color, (20, 16, 28)).copy()
        self.items.append([surf, x - surf.get_width() / 2, y, 0.0])
        if len(self.items) > 24:
            self.items.pop(0)

    def update(self, dt: float) -> None:
        for it in self.items:
            it[3] += dt
            it[2] -= 26 * dt
        self.items = [it for it in self.items if it[3] < self.LIFE]

    def draw(self, surf: pygame.Surface) -> None:
        for img, x, y, t in self.items:
            img.set_alpha(int(255 * min(1.0, 2 * (1 - t / self.LIFE))))
            surf.blit(img, (int(x), int(y)))
