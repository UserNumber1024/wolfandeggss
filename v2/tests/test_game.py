import random

from wolfeggs import balance as B
from wolfeggs.logic.events import (
    CoopSilenced, Defeat, EggCaught, EggMissed, RottenDodged, RowOpened, Victory, WaveStarted,
)
from wolfeggs.logic.game import Game, Phase
from wolfeggs.logic.types import Egg, EggKind, Pos, Side


def make(seed=1, **kw):
    return Game(random.Random(seed), **kw)


def run(g, seconds):
    ev = []
    for _ in range(round(seconds * 60)):
        ev += g.update(1 / 60)
    return ev


def other_side(g):
    return Side.RIGHT if g.wolf.side is Side.LEFT else Side.LEFT


def test_starts_in_break_then_wave_one():
    g = make()
    ev = run(g, B.BREAK_DURATION + 0.05)
    assert g.phase is Phase.WAVE
    assert any(isinstance(e, WaveStarted) and e.number == 1 for e in ev)
    assert len(g.active_coops) == 3


def test_catch_scores_and_miss_hurts():
    g = make()
    run(g, B.BREAK_DURATION + 0.05)
    g.eggs.append(Egg(999, g.wolf, EggKind.NORMAL, g.world_time, 0.5))
    ev = run(g, 0.6)
    assert any(isinstance(e, EggCaught) and e.egg.id == 999 for e in ev) and g.score >= 1
    g.eggs.append(Egg(1000, Pos(other_side(g), 2), EggKind.NORMAL, g.world_time, 0.5))
    h = g.lives.halves
    run(g, 0.6)
    assert g.lives.halves <= h - 2


def test_hare_halves_damage():
    g = make()
    run(g, B.BREAK_DURATION + 0.05)
    g.hare_visible = True
    g.eggs.clear()
    g.eggs.append(Egg(1, Pos(other_side(g), 1), EggKind.NORMAL, g.world_time, 0.2))
    h = g.lives.halves
    ev = run(g, 0.25)
    assert [e.damage_halves for e in ev if isinstance(e, EggMissed)] == [1] and g.lives.halves == h - 1


def test_magnet_catches_adjacent_row_but_not_rotten():
    g = make(start_wave=11)
    run(g, B.BREAK_DURATION + 0.05)
    g.eggs.clear()
    g.effects.activate(EggKind.MAGNET)
    g.wolf = Pos(Side.LEFT, 1)
    g.eggs += [
        Egg(1, Pos(Side.LEFT, 0), EggKind.NORMAL, g.world_time, 0.2),
        Egg(2, Pos(Side.LEFT, 2), EggKind.ROTTEN, g.world_time, 0.2),
    ]
    ev = run(g, 0.25)
    assert any(isinstance(e, EggCaught) and e.via_magnet for e in ev)
    assert any(isinstance(e, RottenDodged) for e in ev)


def test_silence_respects_minimum():
    g = make()
    run(g, B.BREAK_DURATION + 0.05)  # 3 активных
    g.eggs.clear()
    g.eggs.append(Egg(1, g.wolf, EggKind.SILENCE, g.world_time, 0.1))
    ev = run(g, 0.15)
    assert not any(isinstance(e, CoopSilenced) for e in ev)


def test_clock_slows_world_time():
    g = make()
    run(g, B.BREAK_DURATION + 0.05)
    g.effects.activate(EggKind.CLOCK)
    w = g.world_time
    run(g, 1.0)
    assert abs((g.world_time - w) - 0.5) < 0.02


def test_update_clamps_large_dt():
    g = make()
    run(g, B.BREAK_DURATION + 0.05)
    w = g.world_time
    g.update(5.0)
    assert g.world_time - w <= 0.1 + 1e-9


def test_defeat_when_lives_run_out():
    g = make()
    g.lives.halves = 1
    run(g, B.BREAK_DURATION + 0.05)
    g.eggs.append(Egg(1, Pos(other_side(g), 1), EggKind.NORMAL, g.world_time, 0.1))
    ev = run(g, 0.2)
    assert g.phase is Phase.LOST and any(isinstance(e, Defeat) for e in ev)


def test_stage_three_opens_row_zero():
    g = make(start_wave=11)
    ev = run(g, B.BREAK_DURATION + 0.05)
    assert any(isinstance(e, RowOpened) and e.row == 0 for e in ev) and 0 in g.open_rows


def test_victory_after_wave_twenty():
    g = make(start_wave=20, invulnerable=True)
    run(g, B.BREAK_DURATION + 0.05)
    ev = g.skip_wave() + run(g, 0.1)
    assert g.phase is Phase.WON and any(isinstance(e, Victory) for e in ev)


def test_mid_stage_start_has_all_stage_rows_open():
    assert make(start_wave=20).open_rows == (0, 1, 2, 3)
    assert make(start_wave=13).open_rows == (0, 1, 2)


def test_silence_closes_a_coop_when_enough_active():
    g = make(start_wave=2)
    run(g, B.BREAK_DURATION + 0.05)  # 4 активных
    g.eggs.clear()
    g.eggs.append(Egg(1, g.wolf, EggKind.SILENCE, g.world_time, 0.1))
    ev = run(g, 0.15)
    silenced = [e for e in ev if isinstance(e, CoopSilenced)]
    assert len(silenced) == 1 and silenced[0].pos in g.silenced and len(g.active_coops - g.silenced) == 3


def test_natural_transition_from_wave_five_to_stage_two():
    from wolfeggs.logic.events import StageStarted

    g = make(start_wave=5, invulnerable=True)
    run(g, B.BREAK_DURATION + 0.05)
    ev = g.skip_wave() + run(g, B.BREAK_DURATION + 0.2)
    assert any(isinstance(e, StageStarted) and e.stage == 2 for e in ev)
    assert any(isinstance(e, WaveStarted) and e.number == 6 for e in ev)
    assert g.params.stage == 2 and g.open_rows == (1, 2)
