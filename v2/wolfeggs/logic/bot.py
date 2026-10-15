"""Бот для симуляции баланса: идеальный или «человеческий» игрок."""

from __future__ import annotations

import random

from .. import balance as B
from .game import Game
from .types import BONUS, MANDATORY, Dir, Egg, EggKind, Pos
from .wolf import distance, step


class PerfectBot:
    def __init__(
        self,
        step_time: float = B.HUMAN_STEP_TIME,
        reaction: float = 0.0,
        error_rate: float = 0.0,
        rng: random.Random | None = None,
    ):
        self.step_time = step_time
        self.reaction = reaction
        self.error_rate = error_rate
        self.rng = rng or random.Random(0)
        self.cooldown = 0.0

    def act(self, game: Game, dt: float) -> Dir | None:
        self.cooldown -= dt
        if self.cooldown > 0:
            return None
        now = game.world_time
        seen = [e for e in game.eggs if now >= e.lay_time - B.TELEGRAPH_TIME + self.reaction]
        target = self._target(game.wolf, seen, now)
        rotten_soon = {
            e.chute for e in seen
            if e.kind is EggKind.ROTTEN and 0 <= e.arrival - now <= self.step_time * 1.5
        }
        if target is None or target == game.wolf:
            if game.wolf not in rotten_soon:
                return None
            target = None  # уйти из-под тухлого на любую свободную соседнюю позицию

        options = [d for d in Dir if step(game.wolf, d, game.open_rows) != game.wolf]
        if self.error_rate and self.rng.random() < self.error_rate:
            choice = self.rng.choice(options)
        else:
            safe = [d for d in options if step(game.wolf, d, game.open_rows) not in rotten_soon]
            pool = safe or options
            if target is None:
                choice = pool[0]
            else:
                choice = min(pool, key=lambda d: distance(step(game.wolf, d, game.open_rows), target))
                if distance(step(game.wolf, choice, game.open_rows), target) >= distance(game.wolf, target):
                    return None
        self.cooldown = self.step_time
        return choice

    def _target(self, wolf: Pos, seen: list[Egg], now: float) -> Pos | None:
        mandatory = sorted((e for e in seen if e.kind in MANDATORY), key=lambda e: e.arrival)
        bonus = sorted((e for e in seen if e.kind in BONUS), key=lambda e: e.arrival)
        first = mandatory[0] if mandatory else None
        for b in bonus:
            reach_b = distance(wolf, b.chute) * self.step_time <= b.arrival - now
            if not reach_b:
                continue
            if first is None or (
                b.arrival <= first.arrival
                and distance(b.chute, first.chute) * self.step_time <= first.arrival - b.arrival
            ):
                return b.chute
        return first.chute if first else None
