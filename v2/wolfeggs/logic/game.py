"""Игровое состояние: волны, поимки, жизни, эффекты (spec 5)."""

from __future__ import annotations

import random
from enum import Enum

from .. import balance as B
from .effects import Effects
from .events import (
    CoopActivated, CoopSilenced, ComboReset, ComboUp, Defeat, EffectEnded, EffectStarted,
    EggCaught, EggLaid, EggMissed, EggTelegraphed, Event, HareHidden, HareShown,
    LifeChanged, RottenCaught, RottenDodged, RowOpened, StageStarted, Victory, WaveStarted,
    WolfMoved,
)
from .scoring import Combo, Lives
from .spawner import Spawner
from .types import BONUS, Dir, Egg, EggKind, Pos, Side, SpecialWave
from .waves import stage_of, wave_params
from .wolf import all_positions, step

MAX_DT = 0.1


class Phase(Enum):
    BREAK = "break"
    WAVE = "wave"
    DRAIN = "drain"
    WON = "won"
    LOST = "lost"


def _pos_key(p: Pos) -> tuple[int, int]:
    return (p.side.value, p.row)


class Game:
    def __init__(
        self,
        rng: random.Random | None = None,
        start_wave: int = 1,
        invulnerable: bool = False,
    ):
        self.rng = rng or random.Random()
        self.invulnerable = invulnerable
        self.spawner = Spawner(self.rng)
        self.wave_number = start_wave
        self.params = wave_params(start_wave)
        self.phase = Phase.BREAK
        self.world_time = 0.0
        self.real_time = 0.0
        self.wave_start = 0.0
        self.break_end = B.BREAK_DURATION
        self.eggs: list[Egg] = []
        self.combo = Combo()
        self.lives = Lives()
        self.effects = Effects()
        self.score = 0
        self.hare_visible = False
        self._hare_schedule: list[tuple[float, bool]] = []
        self.active_coops: set[Pos] = set()
        self.silenced: set[Pos] = set()
        self.max_wave_reached = 0
        self.wolf = Pos(Side.LEFT, 1)
        self._laid: set[int] = set()
        stage = stage_of(start_wave)
        # Перед первой волной этапа ярусы прошлого этапа: новые откроются анимацией.
        # Старт с середины этапа (отладка) сразу получает все ярусы этапа.
        first_of_stage = (start_wave - 1) % B.WAVES_PER_STAGE == 0
        self._open_rows = B.STAGE_OPEN_ROWS[max(1, stage - 1) if first_of_stage else stage]
        self._pending: list[Event] = self._prepare_break(start_wave)

    # --- состояние -----------------------------------------------------------
    @property
    def open_rows(self) -> tuple[int, ...]:
        return self._open_rows

    def positions(self) -> frozenset[Pos]:
        return all_positions(self._open_rows)

    @property
    def hurricane(self) -> bool:
        return self.params.special is SpecialWave.HURRICANE and self.phase in (Phase.WAVE, Phase.DRAIN)

    @property
    def wave_progress(self) -> float:
        if self.phase is Phase.WAVE:
            return min(1.0, (self.world_time - self.wave_start) / self.params.duration)
        return 1.0 if self.phase is Phase.DRAIN else 0.0

    # --- ввод ----------------------------------------------------------------
    def move(self, d: Dir) -> list[Event]:
        if self.phase not in (Phase.BREAK, Phase.WAVE, Phase.DRAIN):
            return []
        new = step(self.wolf, d, self._open_rows)
        if new == self.wolf:
            return []
        old, self.wolf = self.wolf, new
        return [WolfMoved(old, new)]

    def skip_wave(self) -> list[Event]:
        """Только для отладки: снять яйца без штрафа и завершить волну."""
        if self.phase is Phase.BREAK:
            self.break_end = self.world_time
        elif self.phase in (Phase.WAVE, Phase.DRAIN):
            self.eggs.clear()
            self.spawner.params = None
            self.phase = Phase.DRAIN
        return []

    # --- такт ----------------------------------------------------------------
    def update(self, dt: float) -> list[Event]:
        if self.phase in (Phase.WON, Phase.LOST):
            return []
        dt = min(dt, MAX_DT)
        ev, self._pending = self._pending, []
        self.real_time += dt
        for kind in self.effects.update(dt):
            ev.append(EffectEnded(kind))
        self.world_time += dt * self.effects.time_scale
        now = self.world_time

        if self.phase is Phase.BREAK and now >= self.break_end:
            ev += self._start_wave()
        if self.phase is Phase.WAVE:
            active = self.active_coops - self.silenced
            for egg in self.spawner.update(now, self.eggs, active, self.positions(), self.lives.is_full):
                self.eggs.append(egg)
                ev.append(EggTelegraphed(egg))
            if not self.spawner.spawning(now):
                self.phase = Phase.DRAIN
        if self.phase in (Phase.WAVE, Phase.DRAIN):
            ev += self._update_hare(now)

        for egg in self.eggs:
            if egg.id not in self._laid and now >= egg.lay_time:
                self._laid.add(egg.id)
                ev.append(EggLaid(egg))

        for egg in sorted((e for e in self.eggs if now >= e.arrival), key=lambda e: e.arrival):
            ev += self._resolve(egg)
            if self.lives.is_dead:
                self.phase = Phase.LOST
                ev.append(Defeat(self.score))
                return ev

        if self.phase is Phase.DRAIN and not self.eggs:
            ev += self._finish_wave()
        return ev

    # --- волны ---------------------------------------------------------------
    def _prepare_break(self, next_wave: int) -> list[Event]:
        ev: list[Event] = []
        if (next_wave - 1) % B.WAVES_PER_STAGE == 0:
            stage = stage_of(next_wave)
            ev.append(StageStarted(stage))
            new_rows = B.STAGE_OPEN_ROWS[stage]
            for row in new_rows:
                if row not in self._open_rows:
                    ev.append(RowOpened(row))
            self._open_rows = new_rows
        return ev

    def _start_wave(self) -> list[Event]:
        p = self.params = wave_params(self.wave_number)
        self.phase = Phase.WAVE
        self.wave_start = self.world_time
        self.max_wave_reached = max(self.max_wave_reached, p.number)
        self.silenced.clear()
        ev: list[Event] = []
        positions = self.positions()
        self.active_coops &= positions
        free = sorted(positions - self.active_coops, key=_pos_key)
        while len(self.active_coops) < p.active_coops and free:
            pos = free.pop(self.rng.randrange(len(free)))
            self.active_coops.add(pos)
            ev.append(CoopActivated(pos))
        self.spawner.start_wave(p, self.world_time)
        self._schedule_hare(p.duration)
        ev.insert(0, WaveStarted(p.number, p.stage, p.special))
        return ev

    def _finish_wave(self) -> list[Event]:
        ev = self._hide_hare()
        if self.wave_number >= B.TOTAL_WAVES:
            self.phase = Phase.WON
            ev.append(Victory(self.score))
            return ev
        self.wave_number += 1
        self.phase = Phase.BREAK
        self.break_end = self.world_time + B.BREAK_DURATION
        return ev + self._prepare_break(self.wave_number)

    # --- заяц ----------------------------------------------------------------
    def _schedule_hare(self, duration: float) -> None:
        shows = self.rng.randint(*B.HARE_SHOWS_PER_WAVE)
        slot = duration / shows
        schedule = []
        for i in range(shows):
            length = self.rng.uniform(*B.HARE_DURATION)
            start = self.wave_start + slot * i + self.rng.uniform(0, max(0.0, slot - length))
            schedule += [(start, True), (start + length, False)]
        self._hare_schedule = schedule

    def _update_hare(self, now: float) -> list[Event]:
        ev: list[Event] = []
        while self._hare_schedule and self._hare_schedule[0][0] <= now:
            _, visible = self._hare_schedule.pop(0)
            if visible != self.hare_visible:
                self.hare_visible = visible
                ev.append(HareShown() if visible else HareHidden())
        return ev

    def _hide_hare(self) -> list[Event]:
        self._hare_schedule = []
        if self.hare_visible:
            self.hare_visible = False
            return [HareHidden()]
        return []

    # --- разрешение яиц ------------------------------------------------------
    def _catches(self, egg: Egg) -> tuple[bool, bool]:
        if self.wolf == egg.chute:
            return True, False
        if (
            self.effects.active(EggKind.MAGNET)
            and egg.kind is not EggKind.ROTTEN
            and self.wolf.side is egg.chute.side
            and abs(self.wolf.row - egg.chute.row) == 1
        ):
            return True, True
        return False, False

    def _hurt(self, halves: int) -> list[Event]:
        if self.invulnerable or halves <= 0:
            return []
        before = self.lives.halves
        self.lives.damage(halves)
        return [LifeChanged(self.lives.halves, self.lives.halves - before)]

    def _reset_combo(self) -> list[Event]:
        lost = self.combo.streak
        return [ComboReset(lost)] if self.combo.reset() else []

    def _resolve(self, egg: Egg) -> list[Event]:
        self.eggs.remove(egg)
        self._laid.discard(egg.id)
        caught, via_magnet = self._catches(egg)
        ev: list[Event] = []

        if egg.kind is EggKind.ROTTEN:
            if caught:
                ev.append(RottenCaught(egg))
                ev += self._hurt(B.ROTTEN_DAMAGE_HALVES)
                ev += self._reset_combo()
            else:
                self.score += B.ROTTEN_DODGE_POINTS
                ev.append(RottenDodged(egg, B.ROTTEN_DODGE_POINTS))
            return ev

        if caught:
            mult = self.combo.multiplier
            points = B.POINTS[egg.kind.value] * mult
            self.score += points
            ev.append(EggCaught(egg, points, mult, via_magnet))
            if self.combo.hit():
                ev.append(ComboUp(self.combo.multiplier))
            ev += self._apply_bonus(egg.kind)
            return ev

        if egg.kind in BONUS:
            ev.append(EggMissed(egg, 0))
            return ev
        damage = B.MISS_DAMAGE_WITH_HARE_HALVES if self.hare_visible else B.MISS_DAMAGE_HALVES
        ev.append(EggMissed(egg, 0 if self.invulnerable else damage))
        ev += self._hurt(damage)
        ev += self._reset_combo()
        return ev

    def _apply_bonus(self, kind: EggKind) -> list[Event]:
        if kind is EggKind.HEART:
            added = self.lives.heal(B.HEART_HEAL_HALVES)
            return [LifeChanged(self.lives.halves, added)] if added else []
        if kind in (EggKind.CLOCK, EggKind.MAGNET):
            return [EffectStarted(kind, self.effects.activate(kind))]
        if kind is EggKind.SILENCE:
            candidates = sorted(self.active_coops - self.silenced, key=_pos_key)
            if len(candidates) > B.SILENCE_MIN_ACTIVE:
                pos = self.rng.choice(candidates)
                self.silenced.add(pos)
                return [CoopSilenced(pos)]
        return []
