from wolfeggs.logic.fairness import Arrival, is_feasible
from wolfeggs.logic.types import Pos, Side, EggKind as K
from wolfeggs.logic.wolf import all_positions

L, R = Side.LEFT, Side.RIGHT
P4 = all_positions((1, 2))
P8 = all_positions((0, 1, 2, 3))
ST = 0.14


def test_empty_is_feasible():
    assert is_feasible([], P4, 0.0, P4, ST)


def test_too_close_far_apart_is_infeasible():
    a = [Arrival(1.0, Pos(L, 0), K.NORMAL), Arrival(1.3, Pos(R, 3), K.NORMAL)]  # 4 шага = 0.56 с
    assert not is_feasible(a, P8, 0.0, P8, ST)


def test_enough_time_is_feasible():
    a = [Arrival(1.0, Pos(L, 0), K.NORMAL), Arrival(1.6, Pos(R, 3), K.GOLDEN)]
    assert is_feasible(a, P8, 0.0, P8, ST)


def test_rotten_at_same_spot_and_time_as_mandatory_is_infeasible():
    a = [Arrival(1.0, Pos(L, 1), K.NORMAL), Arrival(1.0, Pos(L, 1), K.ROTTEN)]
    assert not is_feasible(a, P4, 0.0, P4, ST)


def test_rotten_forced_when_no_time_to_leave():
    a = [Arrival(1.0, Pos(L, 1), K.NORMAL), Arrival(1.05, Pos(L, 1), K.ROTTEN)]
    assert not is_feasible(a, P4, 0.0, P4, ST)


def test_rotten_dodgeable_with_one_step():
    a = [Arrival(1.0, Pos(L, 1), K.NORMAL), Arrival(1.2, Pos(L, 1), K.ROTTEN)]
    assert is_feasible(a, P4, 0.0, P4, ST)


def test_bonus_eggs_are_ignored():
    a = [Arrival(1.0, Pos(L, 1), K.NORMAL), Arrival(1.01, Pos(R, 2), K.HEART)]
    assert is_feasible(a, P4, 0.0, P4, ST)


def test_start_set_limits_first_move():
    a = [Arrival(0.1, Pos(R, 2), K.NORMAL)]
    assert not is_feasible(a, frozenset({Pos(L, 1)}), 0.0, P4, ST)
