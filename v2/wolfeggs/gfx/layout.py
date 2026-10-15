"""Геометрия сцены на логическом холсте (spec 4.3)."""

from __future__ import annotations

import pygame

from ..logic.types import Pos, Side

W, H = 640, 360
HUD_H = 20
GROUND_Y = 330

ROW_Y = (88, 152, 216, 280)  # высота конца жёлоба и линии корзины
COOP_X = 10  # левый край левого курятника
COOP_W, COOP_H = 60, 50
COOP_DOOR_CX = 42  # центр двери от внешнего края курятника
COOP_THRESHOLD_Y = 43  # порог двери от верха курятника = начало жёлоба
CHUTE_START_X = 70
CHUTE_END_X = 276
CHUTE_DROP = 26  # на сколько жёлоб опускается от курятника к краю
WOLF_X = 320  # ось шеста
WOLF_BODY_DX = 14  # центр тела волка от оси шеста
BASKET_DX = 24  # центр корзины от центра тела (см. art/wolf.py)
BASKET_ABOVE_FEET = 24  # центр корзины над ногами
BASKET_DROP = 14  # центр корзины ниже конца жёлоба: яйцо падает в корзину


def mirror_x(x: float, side: Side) -> float:
    return x if side is Side.LEFT else W - x


def chute_point(pos: Pos, progress: float) -> tuple[float, float]:
    x = CHUTE_START_X + (CHUTE_END_X - CHUTE_START_X) * progress
    y = ROW_Y[pos.row] - CHUTE_DROP + CHUTE_DROP * progress
    return mirror_x(x, pos.side), y


def wolf_anchor(pos: Pos) -> tuple[int, int]:
    """Точка ног волка (центр по x)."""
    x = WOLF_X + pos.side.value * WOLF_BODY_DX
    return x, ROW_Y[pos.row] + BASKET_DROP + BASKET_ABOVE_FEET


def basket_point(pos: Pos) -> tuple[int, int]:
    x, feet = wolf_anchor(pos)
    return x + pos.side.value * BASKET_DX, feet - BASKET_ABOVE_FEET


def coop_rect(pos: Pos) -> pygame.Rect:
    top = ROW_Y[pos.row] - CHUTE_DROP - COOP_THRESHOLD_Y
    left = COOP_X if pos.side is Side.LEFT else W - COOP_X - COOP_W
    return pygame.Rect(left, top, COOP_W, COOP_H)
