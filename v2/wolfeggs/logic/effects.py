"""Таймеры эффектов спецяиц: часы и магнит (spec 5.5)."""

from __future__ import annotations

from .. import balance as B
from .types import EggKind

DURATIONS = {EggKind.CLOCK: B.CLOCK_DURATION, EggKind.MAGNET: B.MAGNET_DURATION}


class Effects:
    def __init__(self) -> None:
        self.timers: dict[EggKind, float] = {}

    def activate(self, kind: EggKind) -> float:
        duration = DURATIONS[kind]
        self.timers[kind] = duration  # повторная поимка продлевает до полного
        return duration

    def update(self, real_dt: float) -> list[EggKind]:
        ended = []
        for kind in list(self.timers):
            self.timers[kind] -= real_dt
            if self.timers[kind] <= 0:
                del self.timers[kind]
                ended.append(kind)
        return ended

    def active(self, kind: EggKind) -> bool:
        return kind in self.timers

    def remaining(self, kind: EggKind) -> float:
        return self.timers.get(kind, 0.0)

    @property
    def time_scale(self) -> float:
        return B.CLOCK_TIME_SCALE if self.active(EggKind.CLOCK) else 1.0
