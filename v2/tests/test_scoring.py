from wolfeggs.logic.effects import Effects
from wolfeggs.logic.scoring import Combo, Lives
from wolfeggs.logic.types import EggKind as K


def test_combo_tiers():
    c = Combo()
    ups = [c.hit() for _ in range(30)]
    assert c.multiplier == 4
    assert [i + 1 for i, u in enumerate(ups) if u] == [5, 15, 30]


def test_combo_reset():
    c = Combo()
    c.hit()
    c.hit()
    assert c.reset() is True and c.multiplier == 1 and c.best == 2
    assert c.reset() is False


def test_lives_bounds():
    lv = Lives()
    assert lv.halves == 10
    assert lv.heal(10) == 4 and lv.is_full
    lv.damage(100)
    assert lv.halves == 0 and lv.is_dead


def test_clock_scales_time_and_expires():
    e = Effects()
    e.activate(K.CLOCK)
    assert e.time_scale == 0.5
    assert e.update(5.9) == [] and e.update(0.2) == [K.CLOCK]
    assert e.time_scale == 1.0


def test_recatch_extends_magnet():
    e = Effects()
    e.activate(K.MAGNET)
    e.update(7.0)
    e.activate(K.MAGNET)
    assert e.remaining(K.MAGNET) == 8.0
