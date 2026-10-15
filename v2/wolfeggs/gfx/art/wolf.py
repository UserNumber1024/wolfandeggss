"""Волк в тельняшке с корзиной. Кадр 48×56, смотрит вправо.

Центр тела — x=14, ноги — нижняя строка, центр корзины — (38, 32),
то есть корзина на 24 px выше ног (layout.BASKET_ABOVE_FEET).
"""

from __future__ import annotations

from .canvas import Canvas

FW, FH = 48, 56
BASKET_CENTER = (38, 32)


def _stripes(shade_x: int):
    def fn(x: int, y: int) -> str:
        stripe = y % 3 == 0
        if x < shade_x:
            return "B" if stripe else "l"
        return "b" if stripe else "w"

    return fn


def wolf_frame(legs: int = 0, blink: bool = False, basket: int = 0, sad: bool = False) -> list[str]:
    c = Canvas(FW, FH)

    # хвост
    c.poly([(7, 36), (10, 40), (5, 50), (1, 47)], lambda x, y: "G" if x < 4 else "g")
    c.ellipse(2.8, 48.5, 2.2, 2.2, "l")

    # ноги: брюки-клёш и ботинки
    lx, rx = 8 - legs, 15 + legs
    for x0, inner in ((lx, lx + 5), (rx, rx)):
        c.rect(x0, 40, 6, 9, "p")
        c.rect(inner, 40, 1, 9, "P")
        c.rect(x0 - 1, 48, 8, 3, "p")
        c.rect(x0 - 1, 50, 8, 1, "P")
    lift_l, lift_r = (1, 0) if legs > 0 else ((0, 1) if legs < 0 else (0, 0))
    for x0, lift in ((lx, lift_l), (rx, lift_r)):
        c.rect(x0 - 1, 51 - lift, 9, 4, "s")
        c.rect(x0 + 6, 52 - lift, 3, 3, "s")
        c.rect(x0 - 1, 54 - lift, 10, 1, "S")

    # туловище в тельняшке и ремень
    c.ellipse(14, 31.5, 8.5, 9.5, _stripes(9))
    c.rect(6, 39, 17, 2, "P")
    c.put(14, 39, "y")

    # шея и голова
    c.rect(11, 19, 7, 5, "g")
    c.rect(11, 19, 2, 5, "G")
    c.ellipse(15, 13, 7.5, 7.5, lambda x, y: "G" if x < 10 else "g")
    c.ellipse(25, 16, 7.2, 3.6, lambda x, y: "l" if y < 17 else "L")
    c.ellipse(31.6, 14.6, 1.9, 1.7, "n")
    c.poly([(13, 7), (16, 3), (19, 7)], "G")  # чёлка

    # уши
    if sad:
        c.poly([(10, 6), (1, 3), (10, 10)], "G")
        c.poly([(13, 5), (4, 1), (13, 9)], "g")
        c.line(6, 3, 11, 6, "r")
    else:
        c.poly([(7, 9), (8.5, -0.5), (12, 6)], "G")
        c.poly([(12, 6), (15, -0.5), (18, 6)], "g")
        c.line(15, 2, 15, 5, "r")
        c.line(9, 2, 10, 6, "r")

    # глаз
    if blink:
        c.line(17, 11, 22, 11, "G")
    elif sad:
        c.ellipse(19.5, 11.5, 2.2, 1.8, "e")
        c.put(20, 12, "i")
        c.line(17, 9, 22, 10, "G")
    else:
        c.ellipse(19.5, 10.5, 2.2, 3.0, "e")
        c.rect(20, 10, 1, 2, "i")

    # рот
    if sad:
        c.line(20, 20, 24, 19, "n")
        c.line(24, 19, 28, 20, "n")
    else:
        c.line(20, 18, 29, 19, "n")
        c.rect(22, 19, 5, 1, "m")
        c.put(27, 19, "e")

    # руки: дальняя темнее, ближняя с рукавом
    c.line(15, 29, 30, 33, "G", thick=3)
    c.line(18, 26, 29, 30, "g", thick=3)
    c.line(18, 26, 21, 27, "w", thick=3)
    c.line(18, 27, 21, 28, "b")

    # корзина: 0 — обычная, 1 — сжата, 2 — вытянута
    bw, bh = {0: (13, 8), 1: (15, 6), 2: (11, 10)}[basket]
    cx, cy = BASKET_CENTER
    x0 = cx - bw // 2
    y0 = cy - bh // 2 + (1 if basket == 1 else 0)
    c.poly(
        [(x0, y0), (x0 + bw, y0), (x0 + bw - 2, y0 + bh), (x0 + 2, y0 + bh)],
        lambda x, y: "Y" if (x + y) % 3 == 0 else "y",
    )
    c.rect(x0 - 1, y0, bw + 2, 1, "o")
    c.rect(x0 - 1, y0 + 1, bw + 2, 1, "Y")
    c.ellipse(31.5, 31, 2.3, 2.3, "g")  # ладонь на ободе
    return c.rows()


WOLF_FRAMES = {
    "idle": [wolf_frame(), wolf_frame(blink=True)],
    "move": [wolf_frame(legs=1), wolf_frame(legs=-1)],
    "catch": [wolf_frame(basket=1), wolf_frame(basket=2)],
    "sad": [wolf_frame(sad=True)],
}
