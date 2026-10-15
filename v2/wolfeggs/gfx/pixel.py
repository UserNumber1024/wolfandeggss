"""Утилиты пиксель-арта: спрайты из текстовых сеток."""

from __future__ import annotations

from typing import Mapping, Sequence

import pygame

Color = tuple[int, int, int]


def grid_to_surface(rows: Sequence[str], palette: Mapping[str, Color]) -> pygame.Surface:
    """Сетка символов -> поверхность. '.' и ' ' прозрачные."""
    h, w = len(rows), max(len(r) for r in rows)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch not in ". ":
                surf.set_at((x, y), palette[ch])
    return surf


def outline(surf: pygame.Surface, color: Color) -> pygame.Surface:
    """Контур 1 px (4 соседа). Результат на 2 px шире и выше."""
    w, h = surf.get_size()
    out = pygame.Surface((w + 2, h + 2), pygame.SRCALPHA)
    sil = pygame.mask.from_surface(surf).to_surface(setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0))
    for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
        out.blit(sil, (dx, dy))
    out.blit(surf, (1, 1))
    return out


def flip_h(surf: pygame.Surface) -> pygame.Surface:
    return pygame.transform.flip(surf, True, False)

