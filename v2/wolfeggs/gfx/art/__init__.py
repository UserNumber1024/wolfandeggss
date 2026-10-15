"""Кадры персонажей как пиксельные сетки."""

from __future__ import annotations

from typing import Iterator


def iter_all_grids() -> Iterator[tuple[str, list[list[str]]]]:
    from . import critters, eggs, hen, wolf

    for name, frames in wolf.WOLF_FRAMES.items():
        yield f"wolf.{name}", frames
    for name, frames in hen.HEN_FRAMES.items():
        yield f"hen.{name}", frames
    for kind, grid in eggs.EGG_GRIDS.items():
        yield f"egg.{kind.value}", [grid]
    yield "chick", critters.CHICK
    yield "hare", critters.HARE
    yield "bird", critters.BIRD
    yield "butterfly", critters.BUTTERFLY
    yield "crow", critters.CROW
    yield "shell", critters.SHELL
    yield "hearts", [critters.HEART_FULL, critters.HEART_HALF, critters.HEART_EMPTY]
    yield "icons", [critters.ICON_CLOCK, critters.ICON_MAGNET]
