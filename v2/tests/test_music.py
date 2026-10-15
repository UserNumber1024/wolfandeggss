import time
from collections import Counter

import numpy as np
import pytest

from wolfeggs.audio.music import (
    BARS, LAYERS, STEPS_PER_BAR, Music, compose_stage, compose_wave, layer_volumes, melody_notes, samples_per_step,
)


def test_layers_equal_length_including_slow():
    for st in range(5):
        c = compose_stage(st)
        assert len({len(c[k]) for k in (*LAYERS, "slow")}) == 1


def test_wave_music_is_sixteen_bars():
    c = compose_wave(2, 7, seed=1)
    assert len(c["lead"]) == samples_per_step(2) * STEPS_PER_BAR * BARS and BARS == 16


def test_stages_differ():
    assert not np.array_equal(compose_stage(1)["lead"], compose_stage(3)["lead"])


def test_each_wave_has_its_own_melody():
    a = [n[1] for n in melody_notes(1, 1, seed=7)]
    b = [n[1] for n in melody_notes(1, 2, seed=7)]
    assert a != b


def test_same_seed_same_music_other_seed_differs():
    assert melody_notes(3, 12, seed=5) == melody_notes(3, 12, seed=5)
    assert melody_notes(3, 12, seed=5) != melody_notes(3, 12, seed=6)


def test_melody_is_not_monotonous():
    for seed in range(5):
        notes = melody_notes(2, 8, seed)
        pitches = [p for _, p, _, _ in notes]
        top_share = Counter(pitches).most_common(1)[0][1] / len(pitches)
        assert len(set(pitches)) >= 7 and top_share < 0.25, (seed, top_share)
        vel = np.array([v for *_, v in notes])
        assert vel.std() > 0.06
        loud = {s % 16 for s, _, _, v in notes if v >= np.percentile(vel, 80)}
        assert len(loud) >= 4  # акценты гуляют по тактам, а не бьют в одно место


def test_volumes_by_intensity():
    assert layer_volumes(0.1, False, False, False)["drums"] == 0
    v = layer_volumes(0.7, False, True, False)
    assert v["drums"] > 0 and v["harmony"] > 0 and v["sparkle"] > 0 and v["wind"] == 0


def test_clock_switches_to_slow():
    v = layer_volumes(0.9, True, False, False)
    assert v["slow"] == 1 and all(v[k] == 0 for k in LAYERS)


def test_compose_wave_is_fast():
    t = time.perf_counter()
    compose_wave(4, 18, seed=3)
    assert time.perf_counter() - t < 0.8


def test_music_disabled_is_silent_noop():
    m = Music(enabled=False)
    m.play_stage(1)
    m.play_wave(1, 1, seed=1)
    m.set_intensity(0.5)
    m.update(0.1)
    m.jingle("victory")


def _enabled_music():
    m = Music()
    if not m.enabled:
        pytest.skip("no mixer")
    return m


def _wait(m, key, timeout=10.0):
    t = time.perf_counter()
    while not m.ready(key):
        assert time.perf_counter() - t < timeout
        time.sleep(0.02)


def test_preloaded_menu_starts_instantly(display):
    m = _enabled_music()
    m.preload()
    t = time.perf_counter()
    m.play_stage(0)
    m.update(0.1)
    assert time.perf_counter() - t < 0.03 and m.stage == 0


def test_wave_music_builds_in_background_and_switches(display):
    m = _enabled_music()
    m.preload()
    m.play_stage(0)
    m.update(0.1)
    t = time.perf_counter()
    m.play_wave(2, 6, seed=1)  # не ждём сборку на главном потоке
    assert time.perf_counter() - t < 0.01
    _wait(m, ("wave", 2, 6, 1))
    for _ in range(80):
        m.update(1 / 60)
    assert m.key == ("wave", 2, 6, 1) and m.stage == 2


def test_quick_return_to_menu_keeps_menu_music(display):
    m = _enabled_music()
    m.preload()
    m.play_stage(0)
    m.update(0.1)
    m.play_wave(1, 1, seed=1)  # началась игра
    m.play_stage(0)  # тут же вышли в меню
    _wait(m, ("wave", 1, 1, 1))
    for _ in range(80):
        m.update(1 / 60)
    assert m.key == ("stage", 0)
