"""«Волк и яйца» v2 — точка входа.

Запуск: python main.py [--debug] [--stage N] [--seed N]
"""

from __future__ import annotations

import argparse
import os
import sys
import warnings
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _dpi_aware() -> None:
    """Без этого Windows с масштабом 125–150 % размывает пиксели."""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Волк и яйца v2")
    ap.add_argument("--debug", action="store_true", help="F2 — пропуск волны, F3 — неуязвимость, F4 — пропуск этапа, FPS")
    ap.add_argument("--stage", type=int, choices=(1, 2, 3, 4), help="сразу начать с этапа N")
    ap.add_argument("--seed", type=int, help="зерно случайности")
    args = ap.parse_args()
    _dpi_aware()

    from wolfeggs.app import App

    App(debug=args.debug, start_stage=args.stage, seed=args.seed).run()


if __name__ == "__main__":
    main()
