"""Мини-холст символов для рисования пиксельных сеток кодом."""

from __future__ import annotations

from typing import Callable, Sequence


class Canvas:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.px = [["."] * w for _ in range(h)]

    def put(self, x: int, y: int, c: str) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def get(self, x: int, y: int) -> str:
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return "."

    def rect(self, x: int, y: int, w: int, h: int, c: str) -> None:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, c)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float, c: str | Callable[[int, int], str]) -> None:
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0:
                    self.put(x, y, c(x, y) if callable(c) else c)

    def poly(self, pts: Sequence[tuple[float, float]], c: str | Callable[[int, int], str]) -> None:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            for x in range(int(min(xs)), int(max(xs)) + 1):
                if _inside(x + 0.5, y + 0.5, pts):
                    self.put(x, y, c(x, y) if callable(c) else c)

    def line(self, x0: float, y0: float, x1: float, y1: float, c: str, thick: int = 1) -> None:
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            t = i / n
            x = round(x0 + (x1 - x0) * t)
            y = round(y0 + (y1 - y0) * t)
            for dx in range(thick):
                for dy in range(thick):
                    self.put(x + dx, y + dy, c)

    def rows(self) -> list[str]:
        return ["".join(r) for r in self.px]


def _inside(x: float, y: float, pts: Sequence[tuple[float, float]]) -> bool:
    inside = False
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            inside = not inside
    return inside
