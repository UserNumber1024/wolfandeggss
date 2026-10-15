import random

from wolfeggs import balance as B
from wolfeggs.logic.fairness import Arrival, is_feasible
from wolfeggs.logic.spawner import Spawner
from wolfeggs.logic.types import MANDATORY, EggKind as K
from wolfeggs.logic.waves import wave_params
from wolfeggs.logic.wolf import all_positions


def run_wave(n, seed, lives_full=False, active=None):
    p = wave_params(n)
    pos = all_positions(p.open_rows)
    act = list(active or sorted(pos, key=lambda q: (q.side.value, q.row))[: p.active_coops])
    sp = Spawner(random.Random(seed))
    sp.start_wave(p, 0.0)
    eggs, t = [], 0.0
    while sp.spawning(t):
        pending = [e for e in eggs if e.arrival > t]
        eggs += sp.update(t, pending, act, pos, lives_full)
        t += 1 / 60
    return p, pos, act, eggs


def test_every_wave_is_feasible_fuzz():
    for n in range(1, 21):
        for seed in range(5):
            p, pos, _, eggs = run_wave(n, seed)
            arr = [Arrival(e.arrival, e.chute, e.kind) for e in eggs]
            assert is_feasible(arr, pos, 0.0, pos, B.HUMAN_STEP_TIME), (n, seed)


def test_eggs_only_from_active_coops():
    _, _, act, eggs = run_wave(1, 1)
    assert {e.chute for e in eggs} <= set(act)


def test_rate_roughly_matches_interval():
    p, _, _, eggs = run_wave(1, 2)
    expected = p.duration / ((p.interval_start + p.interval_end) / 2)
    assert 0.8 * expected <= len(eggs) <= 1.1 * expected


def test_no_rotten_in_stage_one():
    for seed in range(10):
        assert all(e.kind is not K.ROTTEN for e in run_wave(3, seed)[3])


def test_no_heart_when_lives_full():
    for seed in range(10):
        assert all(e.kind is not K.HEART for e in run_wave(7, seed, lives_full=True)[3])


def test_gold_rush_is_generous():
    eggs = run_wave(5, 3)[3]
    assert sum(e.kind is K.GOLDEN for e in eggs) >= 0.25 * len(eggs)


def test_min_gap_between_mandatory_arrivals_on_different_chutes():
    p, _, _, eggs = run_wave(19, 4)
    m = sorted((e for e in eggs if e.kind in MANDATORY), key=lambda e: e.arrival)
    for a, b in zip(m, m[1:]):
        if a.chute != b.chute:
            assert b.arrival - a.arrival >= p.min_arrival_gap - 1e-9


def test_same_seed_same_eggs_regardless_of_hash_seed():
    import os
    import subprocess
    import sys
    from pathlib import Path

    code = (
        "import random;from wolfeggs.logic.spawner import Spawner;from wolfeggs.logic.waves import wave_params;"
        "from wolfeggs.logic.wolf import all_positions;p=wave_params(17);pos=all_positions(p.open_rows);"
        "sp=Spawner(random.Random(1));sp.start_wave(p,0.0);eggs=[];t=0.0\n"
        "while t<10:\n eggs+=sp.update(t,[e for e in eggs if e.arrival>t],set(pos),pos,False);t+=1/60\n"
        "print([(e.chute.side.value,e.chute.row,e.kind.value) for e in eggs])"
    )
    root = Path(__file__).resolve().parent.parent
    outs = []
    for hs in ("1", "2", "3"):
        env = {**os.environ, "PYTHONHASHSEED": hs}
        outs.append(subprocess.run([sys.executable, "-c", code], cwd=root, env=env,
                                   capture_output=True, text=True, check=True).stdout)
    assert outs[0] == outs[1] == outs[2]
