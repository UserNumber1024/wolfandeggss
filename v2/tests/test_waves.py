import pytest

from wolfeggs.logic.types import SpecialWave
from wolfeggs.logic.waves import interval_at, stage_of, wave_params


def test_stage_of():
    assert [stage_of(n) for n in (1, 5, 6, 11, 16, 20)] == [1, 1, 2, 3, 4, 4]


def test_open_rows_grow():
    assert wave_params(1).open_rows == (1, 2)
    assert wave_params(11).open_rows == (0, 1, 2)
    assert wave_params(16).open_rows == (0, 1, 2, 3)


def test_first_wave_has_three_coops():
    assert wave_params(1).active_coops == 3 and wave_params(2).active_coops == 4


def test_specials():
    assert wave_params(5).special is SpecialWave.GOLD_RUSH
    assert wave_params(10).special is SpecialWave.HURRICANE
    assert wave_params(4).special is None


def test_rotten_from_stage_two():
    assert not wave_params(5).rotten_allowed and wave_params(6).rotten_allowed


def test_interval_shrinks_within_wave():
    p = wave_params(1)
    assert interval_at(p, 0) == pytest.approx(1.6)
    assert interval_at(p, p.duration) == pytest.approx(1.2)
    assert interval_at(p, 10 * p.duration) == pytest.approx(1.2)
