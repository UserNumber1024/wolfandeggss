"""Мелкие персонажи и иконки: цыплёнок, заяц, птицы, скорлупа, сердца."""

from __future__ import annotations

from .canvas import Canvas


def chick_frame(step: int) -> list[str]:
    c = Canvas(8, 8)
    c.ellipse(3.5, 4, 3.2, 3, "j")
    c.ellipse(5, 2.5, 2, 2, "j")
    c.put(5, 2, "q")
    c.put(7, 3, "J")
    c.put(2, 4, "J")
    if step == 0:
        c.put(2, 7, "J")
        c.put(5, 7, "J")
    else:
        c.put(3, 7, "J")
        c.put(4, 7, "J")
    return c.rows()


def hare_frame(hop: bool, twitch: int = 0) -> list[str]:
    """Заяц целиком, 26×34, смотрит вправо."""
    c = Canvas(26, 34)
    lift = 2 if hop else 0
    c.ellipse(4, 25 - lift, 2.5, 2.5, "x")  # хвост
    c.ellipse(11, 24 - lift, 7.5, 6.5, lambda x, y: "A" if y > 26 - lift else "a")  # тело
    if hop:
        c.ellipse(6, 30, 5, 1.8, "a")
        c.ellipse(19, 29, 3, 1.6, "a")
    else:
        c.ellipse(9, 31, 5, 2, "a")
        c.ellipse(16, 31, 2.4, 2, "x")
    c.ellipse(17, 14 - lift, 5, 4.6, "a")  # голова
    c.ellipse(19.5, 16 - lift, 3, 2.2, "x")  # мордочка
    c.ellipse(13 + twitch, 5 - lift, 1.8, 6.5, "a")  # уши
    c.ellipse(16, 4 - lift, 1.8, 6.5, "a")
    c.ellipse(13 + twitch, 5 - lift, 0.8, 4.8, "r")
    c.ellipse(16, 4 - lift, 0.8, 4.8, "r")
    c.put(18, 12 - lift, "q")
    c.put(22, 15 - lift, "r")
    c.put(21, 18 - lift, "x")
    return c.rows()


BIRD = [
    ["q.....q", ".q...q.", "..qqq..", "...q...", "......."],
    [".......", "..qqq..", ".q.q.q.", "q.....q", "......."],
]
BUTTERFLY = [
    ["M.M.M", "MMqMM", "MMqMM", ".M.M."],
    ["..M..", ".MqM.", ".MqM.", "..M.."],
]
CROW = [
    ["..qq....", ".qqqq.qJ", "qqqqqqq.", "...qqq..", "....q...", "........"],
    ["........", ".qqqq.qJ", "qqqqqqq.", "..qq.q..", ".q..q...", "........"],
]


def shell_frame(i: int) -> list[str]:
    c = Canvas(16, 7)
    spread = 2 + i * 2
    c.ellipse(8, 5.5, 3 + i * 1.5, 1.6, "x")
    c.ellipse(8, 5, 1.6, 1.3, "j")
    for dx, dy in ((-spread, -1 - i), (spread, -i), (-spread // 2, -2 - i)):
        c.put(8 + dx, 4 + dy, "h")
        c.put(9 + dx, 4 + dy, "H")
    return c.rows()


HEART_FULL = [".cc.cc.", "cxcccCc", "cccccCc", ".cccCc.", "..cCc..", "...c..."]
HEART_HALF = [".cc.qq.", "cxcq.qq", "cccq.qq", ".ccq.q.", "..cqq..", "...q..."]
HEART_EMPTY = [".qq.qq.", "q..q..q", "q.....q", ".q...q.", "..q.q..", "...q..."]
ICON_CLOCK = [".qqqqq.", "qxxqxxq", "qxxqxxq", "qxxqqxq", "qxxxxxq", "qxxxxxq", ".qqqqq."]
ICON_MAGNET = ["cc...cc", "cc...cc", "cc...cc", "cc...cc", "ccc.ccc", ".ccccc.", "..ccc.."]

CHICK = [chick_frame(0), chick_frame(1)]
HARE = [hare_frame(False), hare_frame(False, 1), hare_frame(True)]
SHELL = [shell_frame(i) for i in range(3)]
