import time

import numpy as np

from wolfeggs.audio.sfx import CATCH_VARIANTS, SFX_NAMES, Sfx, build_sfx
from wolfeggs.audio.synth import SAMPLE_RATE


def test_all_sfx_render():
    bank = build_sfx()
    assert set(bank) == set(SFX_NAMES) and len(bank["catch"]) == CATCH_VARIANTS
    for name, variants in bank.items():
        for s in variants:
            assert 0 < len(s) <= 2 * SAMPLE_RATE, name
            assert np.max(np.abs(s)) <= 1.0, name


def test_catch_variants_rise_in_pitch():
    v = build_sfx()["catch"]
    zc = [np.count_nonzero(np.diff(np.sign(s[:4000]))) for s in v]
    assert zc == sorted(zc)


def test_build_is_fast():
    t = time.perf_counter()
    build_sfx()
    assert time.perf_counter() - t < 2.0


def test_sfx_disabled_when_mixer_unavailable(monkeypatch):
    monkeypatch.setattr("wolfeggs.audio.sfx.mixer_available", lambda: False)
    s = Sfx()
    assert s.enabled is False
    s.play("catch")  # не падает
