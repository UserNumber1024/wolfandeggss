from tools.simulate import simulate
from wolfeggs.logic.bot import PerfectBot


def test_perfect_bot_wins_in_target_time():
    for seed in (1, 2, 3):
        r = simulate(seed, PerfectBot())
        assert r["won"], r
        assert 600 <= r["real_seconds"] <= 1020, r  # spec: 12–15 мин, с запасом
