"""Многослойные сезонные фоны с параллаксом и декором закрытых ярусов (spec 4.4)."""

from __future__ import annotations

import math
import random
from typing import Sequence

import pygame

import numpy as np

from ..logic.types import Side
from . import scenery as sc
from .layout import GROUND_Y, H, ROW_Y, W
from .palettes import STAGE_PALETTES
from .sprites import Sprites

PAD = 6  # запас по ширине слоёв под параллакс
PARALLAX = {"sky": 0, "far": 1, "mid": 2, "near": 3, "front": 4}  # пикселей сдвига
CROSSFADE = 2.0
REVEAL_TIME = 1.2


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


SUN = {1: ((112, 74), 15), 2: ((500, 46), 13), 3: ((520, 168), 24), 4: ((520, 56), 12)}


class StageScene:
    """Слои одного сезона: статичные пререндерены, живые обновляются."""

    def __init__(self, sprites: Sprites, stage: int):
        self.sprites = sprites
        self.stage = stage
        self.pal = pal = STAGE_PALETTES[stage]
        rng = random.Random(stage * 97)
        self.t = 0.0
        nrng = np.random.default_rng(stage * 97)
        ww = W + 2 * PAD
        sun_pos, sun_r = SUN[stage]
        self.sky = sc.paint_sky(pal, ww, H, GROUND_Y - 40, (sun_pos[0] + PAD, sun_pos[1]))
        self.sun = sc.sun_disc(pal, sun_r, moon=stage == 4)
        self.rays = sc.light_rays(W, H, sun_pos, pal["light"]) if stage in (1, 3) else None
        haze = pal["sky_bottom"]
        self.far = sc.paint_hills(pal["far"], haze, ww, H, stage, 236, 16, 0.012, treeline=True, texture=0.06)
        self.mid = sc.paint_hills(_lerp(pal["far"], pal["near"], 0.55), haze, ww, H, stage + 5, 254, 12, 0.017,
                                  treeline=True, texture=0.1)
        self.near = sc.paint_hills(pal["near"], haze, ww, H, stage + 10, 274, 12, 0.021, texture=0.16)
        self.clouds = [[rng.uniform(0, W), rng.uniform(24, 118), rng.uniform(3, 7),
                        sc.paint_cloud(pal, nrng, rng.uniform(0.7, 1.3))] for _ in range(6)]
        self.trees = []
        for i in range(8):
            x = 30 + i * 80 + rng.randint(-22, 22)
            scale = rng.uniform(0.8, 1.15)
            trunk, crown, crown_y = sc.paint_tree(pal, stage, nrng, scale)
            self.trees.append((x, 256 + rng.randint(0, 16), trunk, crown, crown_y, rng.uniform(0, 6.28)))
        self.trees.sort(key=lambda t: t[1])
        self.small_trees = []
        for i in range(10):
            trunk, crown, crown_y = sc.paint_tree(pal, stage, nrng, 0.5)
            self.small_trees.append((rng.randint(0, W), 246 + rng.randint(0, 8), trunk, crown, crown_y))
        self.bushes = [(rng.randint(0, W), 276 + rng.randint(0, 8), sc.paint_bush(pal, nrng, berries=stage in (1, 2)))
                       for _ in range(5)] if stage != 4 else []
        self.houses = []
        if stage in (1, 4):
            for x in (180, 250, 380, 440):
                self.houses.append((x, 238 + rng.randint(-3, 3), sc.paint_house(pal, False, nrng, snow=stage == 4),
                                    sc.paint_house(pal, True, nrng, snow=stage == 4)))
        self.mill = sc.paint_windmill(pal, nrng) if stage == 2 else None
        self.stars = [(rng.randint(0, W), rng.randint(22, 160), rng.uniform(0, 6.28)) for _ in range(46 if stage == 4 else 0)]
        self.critters = []
        self.window_flicker = [rng.uniform(0, 6.28) for _ in self.houses]
        self.ground = sc.paint_ground(pal, ww, H - GROUND_Y, nrng, stage)
        self.front = sc.paint_front(pal, ww, 30, nrng, stage)
        self._spawn_timer = 0.0

    # --- живые объекты ---
    def update(self, dt: float, wind: float) -> None:
        self.t += dt
        for c in self.clouds:
            c[0] += c[2] * (1 + 4 * wind) * dt
            if c[0] > W + 30:
                c[0] = -c[3].get_width() - 10
        self._spawn_timer -= dt
        if self._spawn_timer <= 0:
            self._spawn_timer = random.uniform(3, 7)
            self._spawn_critter()
        for cr in self.critters:
            cr["x"] += cr["vx"] * dt
            cr["y"] += math.sin(self.t * cr["wob"]) * cr["amp"] * dt
        self.critters = [cr for cr in self.critters if -20 < cr["x"] < W + 20]

    def _spawn_critter(self) -> None:
        kind = {1: "bird", 2: "butterfly", 3: "crow", 4: None}[self.stage]
        if kind is None or len(self.critters) > 5:
            return
        left = random.random() < 0.5
        y = random.uniform(40, 140) if kind != "butterfly" else random.uniform(200, 300)
        speed = {"bird": 40, "butterfly": 18, "crow": 30}[kind]
        self.critters.append({"kind": kind, "x": -10 if left else W + 10, "y": y,
                              "vx": speed if left else -speed, "wob": random.uniform(2, 5),
                              "amp": 10 if kind == "butterfly" else 4})

    def draw_back(self, surf: pygame.Surface, par: float, wind: float) -> None:
        ox = lambda layer: -PAD - int(round(par * PARALLAX[layer]))  # noqa: E731
        surf.blit(self.sky, (ox("sky"), 0))
        for x, y, ph in self.stars:
            if math.sin(self.t * 2 + ph) > -0.3:
                surf.set_at((x, y), (230, 236, 255))
        (sx, sy), _ = SUN[self.stage]
        surf.blit(self.sun, (sx - self.sun.get_width() // 2, sy - self.sun.get_height() // 2))
        for x, y, _, img in self.clouds:
            surf.blit(img, (int(x), int(y)))
        if self.rays is not None:
            self.rays.set_alpha(int(150 + 90 * math.sin(self.t * 0.6)))
            surf.blit(self.rays, (0, 0))
        surf.blit(self.far, (ox("far"), 0))
        for i, (x, y, dark, lit) in enumerate(self.houses):
            on = self.stage == 4 and math.sin(self.t * 0.7 + self.window_flicker[i]) > -0.6
            surf.blit(lit if on else dark, (x + ox("far"), y - dark.get_height()))
        if self.mill is not None:
            self._draw_windmill(surf, 470 + ox("far"), 170)
        for cr in self.critters:
            frames = getattr(self.sprites, cr["kind"])
            img = frames[int(self.t * 8) % 2]
            if cr["vx"] < 0:
                img = pygame.transform.flip(img, True, False)
            surf.blit(img, (int(cr["x"]), int(cr["y"])))
        surf.blit(self.mid, (ox("mid"), 0))
        for x, y, trunk, crown, cy in self.small_trees:
            bx = x + ox("mid")
            surf.blit(trunk, (bx, y - trunk.get_height()))
            surf.blit(crown, (bx, y - trunk.get_height() - crown.get_height() + cy))
        surf.blit(self.near, (ox("near"), 0))
        sway_amp = 1 + 3 * wind
        for x, y, trunk, crown, cy, ph in self.trees:
            bx = x + ox("near")
            surf.blit(trunk, (bx, y - trunk.get_height()))
            sway = int(round(math.sin(self.t * (1.3 + 3 * wind) + ph) * sway_amp))
            surf.blit(crown, (bx + sway, y - trunk.get_height() - crown.get_height() + cy))
        for x, y, img in self.bushes:
            surf.blit(img, (x + ox("near"), y - img.get_height()))
        surf.blit(self.ground, (ox("near"), GROUND_Y))

    def draw_front(self, surf: pygame.Surface, par: float) -> None:
        surf.blit(self.front, (-PAD - int(round(par * PARALLAX["front"])), H - 30))

    def _draw_windmill(self, surf: pygame.Surface, x: int, y: int) -> None:
        surf.blit(self.mill, (x - self.mill.get_width() // 2, y - 6))
        a = self.t * 1.2
        sail, sail_dark, spar = (236, 226, 200), (190, 176, 150), self.pal["wood_dark"]
        for k in range(4):
            ang = a + k * math.pi / 2
            ca, sa = math.cos(ang), math.sin(ang)
            ex, ey = x + ca * 32, y + sa * 32
            px, py = -sa * 6, ca * 6
            mx, my = x + ca * 10, y + sa * 10
            pygame.draw.polygon(surf, sail, [(mx, my), (ex, ey), (ex + px, ey + py), (mx + px, my + py)])
            pygame.draw.polygon(surf, sail_dark, [(mx + px * 0.5, my + py * 0.5), (ex + px * 0.5, ey + py * 0.5),
                                                  (ex + px, ey + py), (mx + px, my + py)])
            for f in (0.45, 0.7, 0.95):
                pygame.draw.line(surf, spar, (x + ca * 32 * f, y + sa * 32 * f),
                                 (x + ca * 32 * f + px, y + sa * 32 * f + py))
            pygame.draw.line(surf, spar, (x, y), (ex, ey), 2)
        pygame.draw.circle(surf, spar, (x, y), 3)


def _build_decor(stage: int) -> dict[int, pygame.Surface]:
    pal = STAGE_PALETTES[stage]
    rng = random.Random(5)
    nrng = np.random.default_rng(5)
    top = pygame.Surface((W, 90), pygame.SRCALPHA)
    for side_x in (0, W - 290):
        for i in range(5):
            cloud = sc.paint_cloud(pal, nrng, rng.uniform(1.2, 1.6))
            top.blit(cloud, (side_x + i * 50 + rng.randint(-6, 6), rng.randint(8, 40)))
    bottom = pygame.Surface((W, 80), pygame.SRCALPHA)
    for x0, x1 in ((10, 270), (W - 270, W - 10)):
        bottom.blit(sc.paint_fence(pal, x1 - x0, nrng), (x0, 20))
        for _ in range(6):
            bush = sc.paint_bush(pal, nrng, rng.randint(34, 46), rng.randint(22, 28), berries=stage != 4)
            bottom.blit(bush, (rng.randint(x0, x1 - bush.get_width()), 80 - bush.get_height() - rng.randint(4, 12)))
    return {0: top, 3: bottom}


_SCENES: dict[tuple[int, int], StageScene] = {}
_DECOR: dict[int, dict[int, pygame.Surface]] = {}


def _scene(sprites: Sprites, stage: int) -> StageScene:
    key = (id(sprites), stage)
    if key not in _SCENES:
        _SCENES[key] = StageScene(sprites, stage)
    return _SCENES[key]


def _decor(stage: int) -> dict[int, pygame.Surface]:
    if stage not in _DECOR:
        _DECOR[stage] = _build_decor(stage)
    return _DECOR[stage]


def prebuild_scenes(sprites: Sprites) -> None:
    """Построить сцены и декор всех сезонов заранее (смена этапа без подвисания)."""
    for stage in STAGE_PALETTES:
        _scene(sprites, stage)
        _decor(stage)
        sc.rig_for(stage)


class BackgroundDirector:
    def __init__(self, sprites: Sprites, stage: int, open_rows: Sequence[int]):
        self.sprites = sprites
        self.stage = stage
        self.scene = _scene(sprites, stage)
        self.old: StageScene | None = None
        self.fade = 0.0
        self.wind = 0.0
        self.par = 0.0
        self.row_reveal = {r: (1.0 if r in open_rows else 0.0) for r in range(4)}
        self._opening: set[int] = set()
        self._tmp = pygame.Surface((W, H))
        self._decor = _decor(self.stage)

    def set_stage(self, stage: int) -> None:
        if stage == self.stage:
            return
        self.old = self.scene
        self.scene = _scene(self.sprites, stage)
        self.stage = stage
        self.fade = CROSSFADE
        self._decor = _decor(self.stage)

    def open_row(self, row: int) -> None:
        if self.row_reveal[row] < 1.0:
            self._opening.add(row)

    def set_wind(self, strength: float) -> None:
        self.wind = max(0.0, min(1.0, strength))

    def update(self, dt: float, wolf_side: Side) -> None:
        target = wolf_side.value
        self.par += (target - self.par) * min(1.0, dt / 0.3)
        self.scene.update(dt, self.wind)
        if self.old is not None:
            self.old.update(dt, self.wind)
            self.fade -= dt
            if self.fade <= 0:
                self.old = None
        for row in list(self._opening):
            self.row_reveal[row] = min(1.0, self.row_reveal[row] + dt / REVEAL_TIME)
            if self.row_reveal[row] >= 1.0:
                self._opening.discard(row)

    def draw_back(self, surf: pygame.Surface) -> None:
        self.scene.draw_back(surf, self.par, self.wind)
        if self.old is not None:
            self.old.draw_back(self._tmp, self.par, self.wind)
            self._tmp.set_alpha(int(255 * max(0.0, self.fade / CROSSFADE)))
            surf.blit(self._tmp, (0, 0))
        self._draw_decor(surf)

    def draw_front(self, surf: pygame.Surface) -> None:
        self.scene.draw_front(surf, self.par)

    # --- декор закрытых ярусов ---
    def _draw_decor(self, surf: pygame.Surface) -> None:
        r0 = self.row_reveal[0]
        if r0 < 1.0:
            img = self._decor[0]
            img.set_alpha(int(255 * (1 - r0)))
            surf.blit(img, (0, ROW_Y[0] - 70 - int(r0 * 50)))
        r3 = self.row_reveal[3]
        if r3 < 1.0:
            img = self._decor[3]
            img.set_alpha(int(255 * (1 - r3)))
            surf.blit(img, (0, ROW_Y[3] - 40 + int(r3 * 70)))

