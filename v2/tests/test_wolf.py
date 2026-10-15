from wolfeggs.logic.types import Pos, Side, Dir, Egg, EggKind
from wolfeggs.logic.wolf import distance, step, all_positions

L, R = Side.LEFT, Side.RIGHT


def test_distance_counts_rows_and_side():
    assert distance(Pos(L, 1), Pos(R, 3)) == 3
    assert distance(Pos(L, 2), Pos(L, 2)) == 0


def test_step_clamps_to_open_rows():
    assert step(Pos(L, 1), Dir.UP, (1, 2)) == Pos(L, 1)
    assert step(Pos(L, 1), Dir.UP, (0, 1, 2)) == Pos(L, 0)
    assert step(Pos(L, 2), Dir.DOWN, (1, 2)) == Pos(L, 2)


def test_step_switches_side():
    assert step(Pos(L, 2), Dir.RIGHT, (1, 2)) == Pos(R, 2)
    assert step(Pos(R, 2), Dir.RIGHT, (1, 2)) == Pos(R, 2)


def test_all_positions_size():
    assert len(all_positions((0, 1, 2, 3))) == 8


def test_egg_progress():
    e = Egg(1, Pos(L, 1), EggKind.NORMAL, lay_time=10.0, roll_time=2.0)
    assert e.arrival == 12.0
    assert e.progress(9.0) == 0.0 and e.progress(11.0) == 0.5 and e.progress(20.0) == 1.0
