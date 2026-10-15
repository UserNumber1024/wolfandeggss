"""Параметры волн из таблицы баланса."""

from __future__ import annotations

from dataclasses import dataclass

from .. import balance as B
from .types import SpecialWave


@dataclass(frozen=True)
class WaveParams:
    number: int
    stage: int
    open_rows: tuple[int, ...]
    active_coops: int
    roll_time: float
    interval_start: float
    interval_end: float
    min_arrival_gap: float
    duration: float
    special: SpecialWave | None
    special_chance: float
    rotten_allowed: bool


def stage_of(n: int) -> int:
    return (n - 1) // B.WAVES_PER_STAGE + 1


def wave_params(n: int) -> WaveParams:
    roll, interval, gap, coops = B.WAVE_TABLE[n - 1]
    stage = stage_of(n)
    special = SpecialWave(B.SPECIAL_WAVES[n]) if n in B.SPECIAL_WAVES else None
    chance = (
        B.GOLD_RUSH_SPECIAL_CHANCE
        if special is SpecialWave.GOLD_RUSH
        else B.SPECIAL_CHANCE_BY_STAGE[stage]
    )
    return WaveParams(
        number=n,
        stage=stage,
        open_rows=B.STAGE_OPEN_ROWS[stage],
        active_coops=coops,
        roll_time=roll,
        interval_start=interval,
        interval_end=interval * B.WAVE_INTERVAL_SHRINK,
        min_arrival_gap=gap,
        duration=B.WAVE_DURATION,
        special=special,
        special_chance=chance,
        rotten_allowed=stage >= B.ROTTEN_FROM_STAGE,
    )


def interval_at(p: WaveParams, elapsed: float) -> float:
    f = min(1.0, max(0.0, elapsed / p.duration))
    return p.interval_start + (p.interval_end - p.interval_start) * f
