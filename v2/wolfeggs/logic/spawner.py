"""Планировщик спавна яиц с гарантией справедливости (spec 5.5, 5.7)."""

from __future__ import annotations

import random
from typing import Collection, Sequence

from .. import balance as B
from .fairness import Arrival, is_feasible
from .types import MANDATORY, Egg, EggKind, Pos, SpecialWave
from .waves import WaveParams, interval_at


class Spawner:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.params: WaveParams | None = None
        self.wave_start = 0.0
        self.next_spawn = 0.0
        self._next_id = 1

    def start_wave(self, params: WaveParams, now: float) -> None:
        self.params = params
        self.wave_start = now
        self.next_spawn = now

    def spawning(self, now: float) -> bool:
        return self.params is not None and now - self.wave_start < self.params.duration

    def update(
        self,
        now: float,
        pending: Sequence[Egg],
        active: Collection[Pos],
        positions: frozenset[Pos],
        lives_full: bool,
    ) -> list[Egg]:
        if not self.spawning(now) or now < self.next_spawn or not active:
            return []
        p = self.params
        kind = self._pick_kind(len(active), lives_full)
        # сортировка: порядок множества зависит от PYTHONHASHSEED, а зерно должно воспроизводить партию
        chutes = sorted(active, key=lambda q: (q.side.value, q.row))
        self.rng.shuffle(chutes)
        for chute in chutes[: B.SPAWN_ATTEMPTS]:
            cand = Egg(self._next_id, chute, kind, now + B.TELEGRAPH_TIME, p.roll_time)
            if self._acceptable(cand, pending, positions, now):
                self._next_id += 1
                jitter = self.rng.uniform(*B.SPAWN_JITTER)
                self.next_spawn = now + interval_at(p, now - self.wave_start) * jitter
                return [cand]
        self.next_spawn = now + B.SPAWN_RETRY_DELAY
        return []

    def _pick_kind(self, active_count: int, lives_full: bool) -> EggKind:
        p = self.params
        if self.rng.random() >= p.special_chance:
            return EggKind.NORMAL
        if p.special is SpecialWave.GOLD_RUSH and self.rng.random() < B.GOLD_RUSH_GOLDEN_SHARE:
            return EggKind.GOLDEN
        weights = dict(B.SPECIAL_WEIGHTS)
        if not p.rotten_allowed:
            weights.pop("rotten")
        if lives_full:
            weights.pop("heart")
        if active_count <= B.SILENCE_MIN_ACTIVE:
            weights.pop("silence")
        names = list(weights)
        return EggKind(self.rng.choices(names, [weights[n] for n in names])[0])

    def _acceptable(
        self, cand: Egg, pending: Sequence[Egg], positions: frozenset[Pos], now: float
    ) -> bool:
        p = self.params
        for e in pending:
            if e.chute == cand.chute and abs(e.lay_time - cand.lay_time) < B.SAME_CHUTE_MIN_GAP:
                return False
            if (
                cand.kind in MANDATORY
                and e.kind in MANDATORY
                and e.chute != cand.chute
                and abs(e.arrival - cand.arrival) < p.min_arrival_gap
            ):
                return False
        # Старт — все позиции: новое яйцо прибывает позже, чем волк
        # успевает дойти из любой точки (инвариант из test_balance).
        arrivals = [Arrival(e.arrival, e.chute, e.kind) for e in (*pending, cand)]
        return is_feasible(arrivals, positions, now, positions, B.HUMAN_STEP_TIME)
