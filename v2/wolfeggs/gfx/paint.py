"""Живописный пиксель-арт на numpy: текстуры, свет, дизеринг, мягкий контур.

Изображение — массив (h, w, 4) uint8 RGBA. Свет падает сверху-слева.
"""

from __future__ import annotations

import numpy as np
import pygame

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16 + 1 / 32
LIGHT = np.array([-0.62, -0.78])  # направление на источник света (x, y)


def canvas(w: int, h: int) -> np.ndarray:
    return np.zeros((h, w, 4), dtype=np.uint8)


def to_surface(arr: np.ndarray) -> pygame.Surface:
    h, w = arr.shape[:2]
    surf = pygame.image.frombuffer(np.ascontiguousarray(arr).tobytes(), (w, h), "RGBA")
    return surf.convert_alpha() if pygame.display.get_surface() else surf.copy()


def bayer(h: int, w: int, ox: int = 0, oy: int = 0) -> np.ndarray:
    ys = (np.arange(h) + oy) % 4
    xs = (np.arange(w) + ox) % 4
    return BAYER4[ys[:, None], xs[None, :]]


def grid(h: int, w: int) -> tuple[np.ndarray, np.ndarray]:
    ys, xs = np.mgrid[0:h, 0:w]
    return xs.astype(np.float32) + 0.5, ys.astype(np.float32) + 0.5


def ellipse(h: int, w: int, cx: float, cy: float, rx: float, ry: float) -> np.ndarray:
    xs, ys = grid(h, w)
    return ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1.0


def value_noise(h: int, w: int, cell: int, rng: np.random.Generator) -> np.ndarray:
    """Гладкий шум 0..1 (билинейная интерполяция случайной сетки)."""
    gh, gw = h // cell + 2, w // cell + 2
    g = rng.random((gh, gw)).astype(np.float32)
    ys = np.arange(h, dtype=np.float32) / cell
    xs = np.arange(w, dtype=np.float32) / cell
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = (ys - y0)[:, None], (xs - x0)[None, :]
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]
    b = g[y0][:, x0 + 1]
    c = g[y0 + 1][:, x0]
    d = g[y0 + 1][:, x0 + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def ramp(colors, t: np.ndarray, dither: np.ndarray | None = None) -> np.ndarray:
    """Значение 0..1 -> цвет из лесенки тонов (с упорядоченным дизерингом на стыках)."""
    cols = np.array(colors, dtype=np.uint8)
    n = len(cols)
    v = np.clip(t, 0, 0.9999) * n
    idx = v.astype(int)
    if dither is not None:
        frac = v - idx
        idx = np.where((frac > dither) & (idx < n - 1), idx + 1, idx)
    return cols[idx]


def put(arr: np.ndarray, mask: np.ndarray, rgb: np.ndarray | tuple, alpha: int = 255) -> None:
    arr[mask, :3] = rgb[mask] if isinstance(rgb, np.ndarray) and rgb.ndim == 3 else rgb
    arr[mask, 3] = alpha


def blob_light(h: int, w: int, cx: float, cy: float, rx: float, ry: float) -> np.ndarray:
    """Освещённость шарообразного объёма: 1 — к свету, 0 — в тени."""
    xs, ys = grid(h, w)
    nx, ny = (xs - cx) / rx, (ys - cy) / ry
    return np.clip(0.5 + 0.55 * (nx * LIGHT[0] + ny * LIGHT[1]), 0, 1)


def soft_outline(arr: np.ndarray, k: float = 0.55, only_bottom_right: bool = False) -> None:
    """Контур из затемнённого собственного цвета (без чёрной обводки)."""
    a = arr[:, :, 3] > 0
    pad = np.pad(a, 1)
    neigh = [pad[1:-1, 2:], pad[2:, 1:-1]] if only_bottom_right else \
        [pad[1:-1, :-2], pad[1:-1, 2:], pad[:-2, 1:-1], pad[2:, 1:-1]]
    edge = a & ~np.logical_and.reduce(neigh)
    arr[edge, :3] = (arr[edge, :3].astype(np.float32) * k).astype(np.uint8)


def shadow(arr: np.ndarray, cx: float, cy: float, rx: float, ry: float, alpha: int = 70) -> None:
    """Мягкая тень на земле (рисуется под объектом)."""
    h, w = arr.shape[:2]
    m = ellipse(h, w, cx, cy, rx, ry) & (arr[:, :, 3] == 0)
    inner = ellipse(h, w, cx, cy, rx * 0.7, ry * 0.7)
    d = bayer(h, w)
    m &= inner | (d < 0.5)
    arr[m] = (20, 16, 24, alpha)


def multiply(arr: np.ndarray, mask: np.ndarray, k: float | np.ndarray) -> None:
    kk = k[mask][:, None] if isinstance(k, np.ndarray) else k
    arr[mask, :3] = np.clip(arr[mask, :3].astype(np.float32) * kk, 0, 255).astype(np.uint8)


def tint(c, k: float) -> tuple[int, int, int]:
    return tuple(int(max(0, min(255, v * k))) for v in c)


def mix(a, b, t: float) -> tuple[int, int, int]:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
