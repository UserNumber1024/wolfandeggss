"""Базовый экран."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from ..app import App

DIR_KEYS = {
    pygame.K_UP: "up", pygame.K_w: "up",
    pygame.K_DOWN: "down", pygame.K_s: "down",
    pygame.K_LEFT: "left", pygame.K_a: "left",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
}
CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


class Screen:
    def __init__(self, app: "App"):
        self.app = app

    def on_enter(self) -> None:
        pass

    def handle(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surf: pygame.Surface) -> None:
        pass


def draw_menu(surf: pygame.Surface, font, items: list[str], selected: int, cx: int, y: int, t: float,
              gap: int = 22) -> None:
    """Вертикальное меню: выбранный пункт подсвечен и помечен стрелками."""
    for i, label in enumerate(items):
        active = i == selected
        color = (255, 226, 120) if active else (230, 230, 240)
        text = f"> {label} <" if active else label
        img = font.render(text, color, (20, 16, 28))
        bob = 1 if active and int(t * 4) % 2 else 0
        surf.blit(img, (cx - img.get_width() // 2, y + i * gap - bob))


def dim(surf: pygame.Surface, alpha: int = 140) -> None:
    shade = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    shade.fill((10, 8, 20, alpha))
    surf.blit(shade, (0, 0))
