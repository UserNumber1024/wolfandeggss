"""События игровой логики. Графика и звук реагируют только на них."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from .types import Egg, EggKind, Pos, SpecialWave


@dataclass(frozen=True)
class WaveStarted:
    number: int
    stage: int
    special: SpecialWave | None


@dataclass(frozen=True)
class StageStarted:
    stage: int


@dataclass(frozen=True)
class RowOpened:
    row: int


@dataclass(frozen=True)
class CoopActivated:
    pos: Pos


@dataclass(frozen=True)
class CoopSilenced:
    pos: Pos


@dataclass(frozen=True)
class EggTelegraphed:
    egg: Egg


@dataclass(frozen=True)
class EggLaid:
    egg: Egg


@dataclass(frozen=True)
class EggCaught:
    egg: Egg
    points: int
    multiplier: int
    via_magnet: bool


@dataclass(frozen=True)
class EggMissed:
    egg: Egg
    damage_halves: int


@dataclass(frozen=True)
class RottenCaught:
    egg: Egg


@dataclass(frozen=True)
class RottenDodged:
    egg: Egg
    points: int


@dataclass(frozen=True)
class ComboUp:
    multiplier: int


@dataclass(frozen=True)
class ComboReset:
    lost_streak: int


@dataclass(frozen=True)
class EffectStarted:
    kind: EggKind
    duration: float


@dataclass(frozen=True)
class EffectEnded:
    kind: EggKind


@dataclass(frozen=True)
class LifeChanged:
    halves: int
    delta: int


@dataclass(frozen=True)
class HareShown:
    pass


@dataclass(frozen=True)
class HareHidden:
    pass


@dataclass(frozen=True)
class WolfMoved:
    old: Pos
    new: Pos


@dataclass(frozen=True)
class Victory:
    score: int


@dataclass(frozen=True)
class Defeat:
    score: int


Event = Union[
    WaveStarted, StageStarted, RowOpened, CoopActivated, CoopSilenced, EggTelegraphed,
    EggLaid, EggCaught, EggMissed, RottenCaught, RottenDodged, ComboUp, ComboReset,
    EffectStarted, EffectEnded, LifeChanged, HareShown, HareHidden, WolfMoved, Victory, Defeat,
]
