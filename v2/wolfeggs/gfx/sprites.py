"""Сборка и кеш всех спрайтов персонажей (строятся один раз при запуске)."""

from __future__ import annotations

import pygame

from ..logic.types import EggKind
from .art import critters, eggs, hen, wolf
from .palettes import CHARACTER_PALETTE, OUTLINE
from .pixel import flip_h, grid_to_surface, outline

ROTATION_STEPS = 16


def _mk(rows, palette=CHARACTER_PALETTE, with_outline: bool = True) -> pygame.Surface:
    surf = grid_to_surface(rows, palette)
    if with_outline:
        surf = outline(surf, OUTLINE)
    return surf.convert_alpha()


def _egg_palette(kind: EggKind) -> dict:
    base, shade, hi = eggs.EGG_TONES[kind]
    return {**CHARACTER_PALETTE, "1": base, "2": shade, "3": hi}


class Sprites:
    def __init__(self) -> None:
        self.wolf = {k: [_mk(f) for f in frames] for k, frames in wolf.WOLF_FRAMES.items()}
        self.wolf_left = {k: [flip_h(s) for s in v] for k, v in self.wolf.items()}
        self.hen = {k: [_mk(f) for f in frames] for k, frames in hen.HEN_FRAMES.items()}
        self.hen_left = {k: [flip_h(s) for s in v] for k, v in self.hen.items()}
        self.egg = {kind: _mk(eggs.EGG_GRIDS[kind], _egg_palette(kind)) for kind in EggKind}
        self.chick = [_mk(f) for f in critters.CHICK]
        self.hare = [_mk(f) for f in critters.HARE]
        self.bird = [_mk(f, with_outline=False) for f in critters.BIRD]
        self.butterfly = [_mk(f, with_outline=False) for f in critters.BUTTERFLY]
        self.crow = [_mk(f, with_outline=False) for f in critters.CROW]
        self.shell = [_mk(f) for f in critters.SHELL]
        self.hearts = {
            "full": _mk(critters.HEART_FULL),
            "half": _mk(critters.HEART_HALF),
            "empty": _mk(critters.HEART_EMPTY),
        }
        self.icons = {
            EggKind.CLOCK: _mk(critters.ICON_CLOCK),
            EggKind.MAGNET: _mk(critters.ICON_MAGNET),
        }
        self.hearts_x2 = {k: pygame.transform.scale_by(v, 2) for k, v in self.hearts.items()}
        self.icons_x2 = {k: pygame.transform.scale_by(v, 2) for k, v in self.icons.items()}
        self._rot: dict[tuple[EggKind, int], pygame.Surface] = {}

    def egg_rotated(self, kind: EggKind, angle_step: int) -> pygame.Surface:
        key = (kind, angle_step % ROTATION_STEPS)
        surf = self._rot.get(key)
        if surf is None:
            surf = pygame.transform.rotate(self.egg[kind], -key[1] * 360 / ROTATION_STEPS)
            self._rot[key] = surf
        return surf

