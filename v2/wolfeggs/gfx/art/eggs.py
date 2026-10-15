"""Яйца 12×15: обычное и спецяйца с метками."""

from __future__ import annotations

from ...logic.types import EggKind
from .canvas import Canvas

# цвета: 1 — основной, 2 — тень, 3 — блик
EGG_TONES = {
    EggKind.NORMAL: ((250, 244, 224), (214, 202, 176), (255, 255, 255)),
    EggKind.GOLDEN: ((255, 206, 60), (214, 150, 30), (255, 246, 180)),
    EggKind.ROTTEN: ((128, 164, 72), (88, 118, 48), (170, 200, 110)),
    EggKind.HEART: ((250, 170, 190), (214, 120, 150), (255, 226, 232)),
    EggKind.CLOCK: ((170, 214, 250), (110, 160, 214), (230, 244, 255)),
    EggKind.MAGNET: ((190, 196, 214), (140, 146, 170), (240, 240, 250)),
    EggKind.SILENCE: ((196, 176, 236), (150, 126, 200), (236, 226, 252)),
}


EW, EH = 12, 15

HEART_MARK = [".cc.cc.", "ccccccc", "ccccccc", ".ccccc.", "..ccc..", "...c..."]


def egg_grid(kind: EggKind) -> list[str]:
    c = Canvas(EW, EH)
    c.ellipse(6, 8, 5.4, 7.2, lambda x, y: "2" if (x >= 8 and y >= 7) or y >= 12 else "1")
    for x, y in ((3, 3), (3, 4), (4, 3), (3, 5), (4, 2)):
        c.put(x, y, "3")
    if kind is EggKind.ROTTEN:
        for x, y in ((7, 4), (4, 9), (8, 10), (3, 7), (6, 12), (9, 6)):
            c.put(x, y, "q")
    elif kind is EggKind.HEART:
        for dy, row in enumerate(HEART_MARK):
            for dx, ch in enumerate(row):
                if ch == "c":
                    c.put(2 + dx, 6 + dy, "c")
    elif kind is EggKind.CLOCK:
        c.ellipse(6, 8.5, 3.8, 3.8, "x")
        for x, y in ((6, 6), (6, 7), (6, 8), (7, 8), (8, 8)):
            c.put(x, y, "q")
    elif kind is EggKind.MAGNET:
        c.rect(3, 5, 2, 6, "c")
        c.rect(8, 5, 2, 6, "c")
        c.rect(3, 10, 7, 2, "c")
        c.rect(3, 5, 2, 1, "x")
        c.rect(8, 5, 2, 1, "x")
    elif kind is EggKind.SILENCE:
        c.rect(4, 6, 5, 1, "z")
        for x, y in ((7, 7), (6, 8), (5, 9)):
            c.put(x, y, "z")
        c.rect(4, 10, 5, 1, "z")
    elif kind is EggKind.GOLDEN:
        for x, y in ((8, 3), (9, 6), (7, 2)):
            c.put(x, y, "3")
    return c.rows()


EGG_GRIDS = {kind: egg_grid(kind) for kind in EggKind}
