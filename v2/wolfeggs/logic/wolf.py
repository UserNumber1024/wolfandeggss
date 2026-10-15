"""Перемещение волка между позициями."""

from __future__ import annotations

from typing import Sequence

from .types import Dir, Pos, Side


def distance(a: Pos, b: Pos) -> int:
    """Число шагов волка от a до b: ярусы плюс смена стороны."""
    return abs(a.row - b.row) + (0 if a.side is b.side else 1)


def step(pos: Pos, d: Dir, open_rows: Sequence[int]) -> Pos:
    if d is Dir.UP:
        row = pos.row - 1
        return Pos(pos.side, row) if row in open_rows else pos
    if d is Dir.DOWN:
        row = pos.row + 1
        return Pos(pos.side, row) if row in open_rows else pos
    side = Side.LEFT if d is Dir.LEFT else Side.RIGHT
    return Pos(side, pos.row)


def all_positions(open_rows: Sequence[int]) -> frozenset[Pos]:
    return frozenset(Pos(side, row) for side in Side for row in open_rows)
