"""Цвета эффектов и подписей, общие для HUD и отрисовки."""

from __future__ import annotations

from ..logic.types import EggKind

COMBO_COLORS = {1: (255, 255, 255), 2: (140, 230, 255), 3: (255, 220, 90), 4: (255, 120, 200)}

PARTICLE_COLORS = {
    EggKind.NORMAL: (255, 250, 230),
    EggKind.GOLDEN: (255, 214, 70),
    EggKind.ROTTEN: (130, 190, 60),
    EggKind.HEART: (255, 110, 150),
    EggKind.CLOCK: (150, 210, 255),
    EggKind.MAGNET: (230, 70, 70),
    EggKind.SILENCE: (190, 160, 255),
}
