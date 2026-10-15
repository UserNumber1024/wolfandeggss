"""Базовые типы игровой логики."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Side(Enum):
    LEFT = -1
    RIGHT = 1


@dataclass(frozen=True)
class Pos:
    """Позиция волка или жёлоба: сторона и ярус (0 — верхний, 3 — нижний)."""

    side: Side
    row: int


class Dir(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class EggKind(Enum):
    NORMAL = "normal"
    GOLDEN = "golden"
    ROTTEN = "rotten"
    HEART = "heart"
    CLOCK = "clock"
    MAGNET = "magnet"
    SILENCE = "silence"


MANDATORY = frozenset({EggKind.NORMAL, EggKind.GOLDEN})
BONUS = frozenset({EggKind.HEART, EggKind.CLOCK, EggKind.MAGNET, EggKind.SILENCE})


class SpecialWave(Enum):
    GOLD_RUSH = "gold_rush"
    HURRICANE = "hurricane"


@dataclass
class Egg:
    id: int
    chute: Pos
    kind: EggKind
    lay_time: float  # мировое время, когда яйцо начинает катиться
    roll_time: float

    @property
    def arrival(self) -> float:
        return self.lay_time + self.roll_time

    def progress(self, now: float) -> float:
        if now <= self.lay_time:
            return 0.0
        return min(1.0, (now - self.lay_time) / self.roll_time)
