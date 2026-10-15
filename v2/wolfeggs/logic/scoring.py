"""Комбо-множитель и жизни (spec 5.3, 5.4)."""

from __future__ import annotations

from dataclasses import dataclass

from .. import balance as B


def multiplier_for(streak: int) -> int:
    for min_streak, mult in B.COMBO_TIERS:
        if streak >= min_streak:
            return mult
    return 1


@dataclass
class Combo:
    streak: int = 0
    best: int = 0

    @property
    def multiplier(self) -> int:
        return multiplier_for(self.streak)

    def hit(self) -> bool:
        before = self.multiplier
        self.streak += 1
        self.best = max(self.best, self.streak)
        return self.multiplier > before

    def reset(self) -> bool:
        had = self.streak > 0
        self.streak = 0
        return had


@dataclass
class Lives:
    halves: int = B.LIVES_START_HALVES

    def damage(self, h: int) -> None:
        self.halves = max(0, self.halves - h)

    def heal(self, h: int) -> int:
        added = min(h, B.LIVES_MAX_HALVES - self.halves)
        self.halves += added
        return added

    @property
    def is_dead(self) -> bool:
        return self.halves <= 0

    @property
    def is_full(self) -> bool:
        return self.halves >= B.LIVES_MAX_HALVES
