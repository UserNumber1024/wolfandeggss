"""Проверка справедливости набора яиц (spec 5.7).

Набор справедлив, если существует маршрут волка, который ловит все
обязательные яйца и при этом не стоит под тухлым в момент его прибытия.
Бонусные яйца необязательны и не учитываются.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .types import BONUS, EggKind, Pos
from .wolf import distance


@dataclass(frozen=True)
class Arrival:
    time: float
    pos: Pos
    kind: EggKind


def is_feasible(
    arrivals: Iterable[Arrival],
    start: frozenset[Pos],
    start_time: float,
    positions: frozenset[Pos],
    step_time: float,
) -> bool:
    # при равном времени сначала обязательное, потом тухлое
    events = sorted(
        (a for a in arrivals if a.kind not in BONUS),
        key=lambda a: (a.time, a.kind is EggKind.ROTTEN),
    )
    reach = set(start)
    t = start_time
    for a in events:
        k = int((a.time - t + 1e-9) // step_time)
        reach = {p for p in positions if any(distance(r, p) <= k for r in reach)}
        if a.kind is EggKind.ROTTEN:
            reach.discard(a.pos)
        else:
            reach = {a.pos} if a.pos in reach else set()
        if not reach:
            return False
        t = a.time
    return True
