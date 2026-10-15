"""Прогон партий ботом и отчёт по балансу.

Запуск из папки v2: python tools/simulate.py --runs 24 --step 0.20 --reaction 0.25 --errors 0.05
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from wolfeggs.logic.bot import PerfectBot  # noqa: E402
from wolfeggs.logic.events import LifeChanged  # noqa: E402
from wolfeggs.logic.game import Game, Phase  # noqa: E402

DT = 1 / 60
TIME_LIMIT = 3600.0


def simulate(seed: int, bot: PerfectBot) -> dict:
    game = Game(random.Random(seed))
    lost = 0
    while game.phase not in (Phase.WON, Phase.LOST) and game.real_time < TIME_LIMIT:
        for e in game.update(DT):
            if isinstance(e, LifeChanged) and e.delta < 0:
                lost -= e.delta
        d = bot.act(game, DT)
        if d is not None:
            game.move(d)
    return {
        "won": game.phase is Phase.WON,
        "wave": game.max_wave_reached,
        "real_seconds": game.real_time,
        "score": game.score,
        "lives_lost_halves": lost,
        "best_streak": game.combo.best,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=10)
    ap.add_argument("--reaction", type=float, default=0.0)
    ap.add_argument("--errors", type=float, default=0.0)
    ap.add_argument("--step", type=float, default=None, help="секунд на нажатие (по умолчанию HUMAN_STEP_TIME)")
    args = ap.parse_args()
    results = []
    for seed in range(1, args.runs + 1):
        kw = {"step_time": args.step} if args.step else {}
        bot = PerfectBot(reaction=args.reaction, error_rate=args.errors, rng=random.Random(seed), **kw)
        results.append(simulate(seed, bot))
    wins = [r for r in results if r["won"]]
    print(f"runs={len(results)} wins={len(wins)} ({100 * len(wins) / len(results):.0f}%)")
    if wins:
        print(f"median win time: {statistics.median(r['real_seconds'] for r in wins) / 60:.1f} min")
    print(f"median score: {statistics.median(r['score'] for r in results)}")
    stages = Counter((r["wave"] - 1) // 5 + 1 for r in results if not r["won"])
    print("losses by stage:", dict(sorted(stages.items())))
    print("final waves:", sorted(r["wave"] for r in results))


if __name__ == "__main__":
    main()
