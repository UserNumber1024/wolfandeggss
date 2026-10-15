"""Курица, 24×22, смотрит вправо."""

from __future__ import annotations

from .canvas import Canvas

FW, FH = 24, 22


def hen_frame(cluck: bool = False, flap: bool = False) -> list[str]:
    c = Canvas(FW, FH)
    c.poly([(1, 5), (8, 9), (8, 16), (1, 12)], lambda x, y: "H" if (x + y) % 3 == 0 else "h")  # хвост
    c.ellipse(11, 14, 8, 6, lambda x, y: "H" if y > 16 else "h")
    wo = -2 if flap else 0
    c.ellipse(10, 13 + wo, 4.8, 3.2, lambda x, y: "A" if y > 13 + wo else "H")
    hx, hy = (18, 6) if cluck else (17, 7)
    c.ellipse(hx, hy, 3.8, 3.8, "h")
    c.rect(hx - 2, hy - 5, 2, 2, "c")
    c.rect(hx, hy - 6, 2, 3, "c")
    c.rect(hx + 2, hy - 5, 1, 2, "C")
    if cluck:
        c.poly([(hx + 3, hy - 2), (hx + 7, hy - 1.5), (hx + 3, hy)], "k")
        c.poly([(hx + 3, hy + 1), (hx + 6, hy + 2.5), (hx + 3, hy + 2)], "K")
    else:
        c.poly([(hx + 3, hy - 1), (hx + 7, hy + 0.5), (hx + 3, hy + 1.6)], "k")
    c.rect(hx + 2, hy + 2, 2, 2, "c")
    c.put(hx + 1, hy - 1, "i")
    c.rect(9, 19, 1, 2, "k")
    c.rect(13, 19, 1, 2, "k")
    c.rect(8, 21, 3, 1, "K")
    c.rect(12, 21, 3, 1, "K")
    return c.rows()


HEN_FRAMES = {
    "idle": [hen_frame(), hen_frame(flap=True)],
    "cluck": [hen_frame(cluck=True), hen_frame(cluck=True, flap=True)],
}
