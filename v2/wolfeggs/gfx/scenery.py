"""Живописные объекты сцены: курятники, жёлоба, шест, деревья, облака, холмы.

Стиль: плотный пиксель-арт с текстурами, светом сверху-слева, упорядоченным
дизерингом и контуром из тёмного оттенка своего же цвета.
"""

from __future__ import annotations

import numpy as np
import pygame

from .paint import (
    bayer, blob_light, canvas, ellipse, grid, mix, multiply, put, ramp, shadow, soft_outline, tint, to_surface,
    value_noise,
)

WOOD = [(52, 32, 26), (78, 50, 34), (108, 70, 44), (140, 94, 58), (172, 122, 76), (204, 156, 102)]
THATCH = [(84, 56, 30), (120, 86, 42), (158, 120, 58), (194, 156, 82), (226, 194, 120)]
STONE = [(58, 56, 62), (84, 82, 86), (112, 110, 108), (144, 140, 132), (176, 170, 158)]
MOSS = [(66, 90, 44), (98, 124, 56), (134, 156, 70)]
SNOW = [(150, 166, 206), (196, 210, 238), (236, 242, 252)]
DARK = [(14, 10, 12), (26, 18, 18), (40, 28, 24)]
GLOW = (255, 214, 120)

from .layout import COOP_H, COOP_W  # noqa: E402


def _streaks(h: int, w: int, rng: np.random.Generator, stretch: int = 6) -> np.ndarray:
    """Вертикальные волокна дерева."""
    n = rng.random((h // stretch + 2, w)).astype(np.float32)
    n = np.repeat(n, stretch, axis=0)[:h]
    return (n + np.roll(n, 1, axis=1) * 0.5) / 1.5


# --- курятник -----------------------------------------------------------------
def paint_coop(stage: int, seed: int = 3) -> pygame.Surface:
    rng = np.random.default_rng(seed)
    H, W = COOP_H, COOP_W
    arr = canvas(W, H)
    xs, ys = grid(H, W)
    d = bayer(H, W)

    # стены из вертикальных досок
    walls = (xs >= 7) & (xs < 53) & (ys >= 18) & (ys < 43)
    col = ((xs - 7) // 5).astype(int).clip(0, 11)
    tone = rng.uniform(0.82, 1.08, size=12).astype(np.float32)[col]
    t = 0.52 * tone * (1.0 - 0.28 * (xs - 7) / 46) + 0.22 * _streaks(H, W, rng) - 0.04
    pos = (xs - 7).astype(int) % 5
    t = np.where(pos == 4, t * 0.45, t)
    t = np.where(pos == 0, t + 0.07, t)
    t = np.where(ys < 23, t * (0.62 + 0.08 * (ys - 18)), t)  # тень под стрехой
    for by in (27, 37):  # поперечные брусья с гвоздями
        t = np.where((ys >= by) & (ys < by + 1), 0.78, t)
        t = np.where((ys >= by + 1) & (ys < by + 2), 0.42, t)
        t = np.where((ys >= by) & (ys < by + 1) & (pos == 2), 0.2, t)
    put(arr, walls, ramp(WOOD, t, d))

    # окошко со ставнями
    win = (xs >= 14) & (xs < 23) & (ys >= 26) & (ys < 34)
    glass_lit = stage >= 3
    glass = np.where(ys < 30, 0.75, 0.45) if glass_lit else np.where((xs - ys) % 7 < 1, 0.7, 0.25)
    put(arr, win, ramp([(30, 34, 52), (52, 62, 86), (90, 104, 130)] if not glass_lit
                       else [(150, 90, 40), (220, 160, 70), (255, 220, 130)], glass, d))
    put(arr, win & ((xs.astype(int) == 18) | (ys.astype(int) == 29)), WOOD[2])
    for sx in (11, 23):
        sh = (xs >= sx) & (xs < sx + 3) & (ys >= 25) & (ys < 35)
        put(arr, sh, ramp(WOOD, 0.62 - 0.12 * (xs - sx) + 0.1 * _streaks(H, W, rng, 3), d))
    put(arr, (xs >= 12) & (xs < 25) & (ys >= 34) & (ys < 35), WOOD[4])

    # дверной проём аркой, глубина темнее кверху
    arch = (((xs >= 36) & (xs < 49) & (ys >= 30) & (ys < 43)) | (ellipse(H, W, 42.5, 30.5, 6.5, 6) & (ys < 31)))
    frame = (((xs >= 35) & (xs < 50) & (ys >= 29) & (ys < 43)) | (ellipse(H, W, 42.5, 30.5, 7.6, 7.1) & (ys < 31))) & ~arch
    put(arr, frame, ramp(WOOD, np.where(xs < 42.5, 0.86, 0.6), d))
    put(arr, arch, ramp(DARK, 0.2 + 0.7 * (ys - 24) / 19, d))
    straw = arch & (ys >= 40)
    put(arr, straw, ramp(THATCH, 0.4 + 0.5 * value_noise(H, W, 2, rng), d))

    # порожек к жёлобу
    put(arr, (xs >= 48) & (xs < 60) & (ys >= 43) & (ys < 44), WOOD[4])
    put(arr, (xs >= 48) & (xs < 60) & (ys >= 44) & (ys < 45), WOOD[1])

    # фундамент из камней
    x = 5.0
    while x < 55:
        w = rng.uniform(5, 8.5)
        for cy, ry in ((45.5, 2.6), (48.3, 2.2)):
            off = 2.5 if cy > 46 else 0
            m = ellipse(H, W, x + w / 2 + off, cy, w / 2, ry) & (arr[:, :, 3] == 0)
            put(arr, m, ramp(STONE, blob_light(H, W, x + w / 2 + off, cy, w / 2, ry) * 0.8 + 0.1, d))
            moss = m & (ys < cy - ry + 1.3) & (value_noise(H, W, 2, rng) > 0.55)
            put(arr, moss, MOSS[1])
        x += w + 0.5

    # соломенная крыша слоями
    roof = np.zeros((H, W), bool)
    for yy in range(0, 21):
        half = 15 + (30 - 15) * yy / 20
        roof[yy, max(0, int(30 - half)):min(W, int(30 + half))] = True
    jag = rng.integers(0, 3, size=W)
    band = ys.astype(int) // 4
    p = (ys % 4) / 4
    straws = (rng.random(W) < 0.35).astype(np.float32)[None, :] * 0.12
    rt = 0.78 - 0.4 * p + 0.18 * (1 - xs / W) + straws + 0.12 * value_noise(H, W, 2, rng) - 0.1
    rt = np.where((ys.astype(int) % 4 == 3) & (jag[xs.astype(int)] == 0), rt - 0.25, rt)
    eave = (ys >= 18) & (ys < 21)
    rt = np.where(eave, rt - 0.15 - 0.15 * ((xs.astype(int) + band) % 2), rt)
    put(arr, roof, ramp(THATCH, rt, d))
    fringe = (ys >= 20) & (ys < 22) & (jag[xs.astype(int)] > 0) & (xs >= 1) & (xs < 59)
    put(arr, fringe & (arr[:, :, 3] == 0) | fringe & ~walls, THATCH[1])
    put(arr, (ys >= 0) & (ys < 2) & (xs >= 14) & (xs < 46), WOOD[1])  # конёк
    for _ in range(3):  # мох на крыше
        mx, my = rng.uniform(10, 50), rng.uniform(6, 16)
        m = ellipse(H, W, mx, my, rng.uniform(2, 3.5), 1.6) & roof
        put(arr, m, ramp(MOSS, blob_light(H, W, mx, my, 3, 1.6), d))

    # сезонные детали
    if stage == 4:
        snow = roof & (ys < 7 + 2 * value_noise(H, W, 3, rng))
        put(arr, snow, ramp(SNOW, 0.35 + 0.6 * (1 - xs / W), d))
        put(arr, (xs >= 12) & (xs < 25) & (ys >= 33) & (ys < 34), SNOW[2])
    if stage == 3:
        for _ in range(9):
            put(arr, (xs.astype(int) == rng.integers(4, 56)) & (ys.astype(int) == rng.integers(3, 19)) & roof,
                [(214, 110, 40), (180, 70, 36), (230, 160, 60)][rng.integers(0, 3)])

    # фонарь у двери
    put(arr, (xs >= 52) & (xs < 53) & (ys >= 21) & (ys < 25), DARK[2])
    lamp = (xs >= 51) & (xs < 55) & (ys >= 25) & (ys < 30)
    put(arr, lamp, DARK[1])
    put(arr, (xs >= 52) & (xs < 54) & (ys >= 26) & (ys < 29), GLOW if stage >= 3 else (120, 110, 90))

    # трава и цветы у основания
    for _ in range(14):
        gx = int(rng.integers(3, 57))
        gh = int(rng.integers(2, 5))
        put(arr, (xs.astype(int) == gx) & (ys >= H - gh) & (ys < H), MOSS[int(rng.integers(0, 3))])
    if stage == 1:
        for _ in range(5):
            put(arr, (xs.astype(int) == rng.integers(3, 57)) & (ys.astype(int) == H - 3),
                [(250, 240, 250), (250, 210, 90), (240, 150, 190)][rng.integers(0, 3)])
    soft_outline(arr, 0.5)
    return to_surface(arr)


# --- жёлоб, шест, площадка ------------------------------------------------------
def paint_chute(length: int, drop: int, seed: int = 5) -> pygame.Surface:
    """Деревянный жёлоб слева направо, опускается на drop. Верх лотка — линия жёлоба."""
    rng = np.random.default_rng(seed)
    H, W = drop + 12, length + 1
    arr = canvas(W, H)
    knots = rng.random(W) < 0.04
    for x in range(W):
        y = int(round(drop * x / length))
        seam = x % 23 == 0
        tones = [0.92, 0.66, 0.5, 0.38, 0.2]
        for i, t in enumerate(tones):
            tt = t * (0.6 if seam and i > 0 else 1.0) - (0.12 if knots[x] and i == 2 else 0)
            arr[y + i, x, :3] = ramp(WOOD, np.array([tt]))[0]
            arr[y + i, x, 3] = 255
        arr[y + 5, x] = (20, 16, 24, 60)  # тень под лотком
        if x % 46 == 20:  # скоба-подпорка
            for k in range(1, 6):
                if y + 4 + k < H:
                    arr[y + 4 + k, min(W - 1, x + k // 2)] = (*WOOD[1], 255)
    return to_surface(arr)


def paint_pole(height: int, seed: int = 7) -> pygame.Surface:
    rng = np.random.default_rng(seed)
    W = 10
    arr = canvas(W, height)
    xs, ys = grid(height, W)
    light = 1 - np.abs((xs - 3.5) / 5.5)
    t = 0.25 + 0.55 * light + 0.18 * _streaks(height, W, rng, 9) - 0.1
    rings = (rng.random(height) < 0.03)[:, None]
    t = np.where(rings, t * 0.6, t)
    put(arr, (xs >= 1) & (xs < 9), ramp(WOOD, t, bayer(height, W)))
    soft_outline(arr, 0.55)
    return to_surface(arr)


def paint_platform(seed: int = 9) -> pygame.Surface:
    rng = np.random.default_rng(seed)
    H, W = 7, 36
    arr = canvas(W, H)
    xs, ys = grid(H, W)
    t = np.select([ys < 1, ys < 4, ys < 5], [0.92, 0.62, 0.42], 0.25) + 0.15 * _streaks(H, W, rng, 1) - 0.07
    t = np.where((xs.astype(int) % 12 == 0) & (ys < 5), t * 0.55, t)
    put(arr, ys < 5, ramp(WOOD, t, bayer(H, W)))
    rope = (xs >= 15) & (xs < 21) & (ys >= 1) & (ys < 7)
    put(arr, rope, np.where(((xs + ys).astype(int) % 2 == 0)[..., None], np.array((196, 170, 120), np.uint8),
                            np.array((150, 124, 84), np.uint8)))
    soft_outline(arr, 0.55)
    return to_surface(arr)


# --- природа ------------------------------------------------------------------
def leaf_palette(pal: dict, stage: int) -> list[tuple[int, int, int]]:
    base = pal["trees"]
    return [tint(base, 0.45), tint(base, 0.68), tint(base, 0.9), mix(tint(base, 1.15), pal["light"], 0.25),
            mix(tint(base, 1.3), pal["light"], 0.45)]


def paint_tree(pal: dict, stage: int, rng: np.random.Generator, scale: float = 1.0) -> tuple[pygame.Surface, pygame.Surface, int]:
    """Ствол и крона отдельно (крона качается). Возвращает и смещение кроны по y."""
    leaves = leaf_palette(pal, stage)
    cw, ch = int(40 * scale), int(36 * scale)
    th = int(46 * scale)
    trunk = canvas(cw, th)
    xs, ys = grid(th, cw)
    tx = cw / 2
    tw = 2.2 * scale + (ys / th) * 1.6 * scale
    m = np.abs(xs - tx) < tw
    bark = [tint(pal["trunk"], 0.55), tint(pal["trunk"], 0.8), pal["trunk"], tint(pal["trunk"], 1.25)]
    put(trunk, m & (ys > th * 0.25), ramp(bark, 0.55 - 0.35 * (xs - tx) / (tw + 0.1) + 0.2 * _streaks(th, cw, rng, 4) - 0.1,
                                          bayer(th, cw)))
    for side in (-1, 1):  # ветви
        y0 = th * rng.uniform(0.3, 0.45)
        for k in range(int(8 * scale)):
            bx, by = int(tx + side * k), int(y0 - k * 0.7)
            if 0 <= bx < cw and 0 <= by < th:
                trunk[by, bx] = (*bark[1], 255)
    shadow(trunk, tx, th - 2, 9 * scale, 2.2 * scale, 80)
    soft_outline(trunk, 0.6)

    crown = canvas(cw, ch)
    d = bayer(ch, cw)
    if stage == 4:  # ель под снегом
        for i, (half, y) in enumerate(((5, 4), (8, 10), (11, 16), (14, 23), (16, 30))):
            hw, yy = half * scale, y * scale
            xs2, ys2 = grid(ch, cw)
            tri = (ys2 >= yy - 6 * scale) & (ys2 < yy + 2) & (np.abs(xs2 - cw / 2) < (ys2 - (yy - 6 * scale)) / (8 * scale) * hw)
            put(crown, tri, ramp(leaves, 0.25 + 0.4 * (1 - (xs2 - cw / 2 + hw) / (2 * hw)), d))
            cap = tri & (ys2 < yy - 6 * scale + 2.5) | tri & (value_noise(ch, cw, 2, rng) > 0.8)
            put(crown, cap, ramp(SNOW, 0.5 + 0.4 * (1 - xs2 / cw), d))
    else:
        clusters = [(cw / 2 + rng.uniform(-9, 9) * scale, ch * rng.uniform(0.35, 0.7), rng.uniform(6, 10) * scale)
                    for _ in range(int(7 * scale) + 2)]
        clusters.sort(key=lambda c: c[1])
        for cx, cy, r in clusters:
            m2 = ellipse(ch, cw, cx, cy, r, r * 0.86)
            lt = blob_light(ch, cw, cx, cy, r, r * 0.86)
            put(crown, m2, ramp(leaves, 0.15 + 0.75 * lt + 0.12 * value_noise(ch, cw, 2, rng) - 0.06, d))
        accent = {1: [(250, 236, 244), (244, 180, 206)], 3: [(232, 120, 40), (190, 70, 40)]}.get(stage)
        if accent:
            spots = (crown[:, :, 3] > 0) & (rng.random((ch, cw)) < (0.07 if stage == 1 else 0.12))
            put(crown, spots, accent[0])
            put(crown, spots & (rng.random((ch, cw)) < 0.5), accent[1])
    soft_outline(crown, 0.6)
    return to_surface(trunk), to_surface(crown), int(th * 0.55)


def paint_cloud(pal: dict, rng: np.random.Generator, scale: float = 1.0) -> pygame.Surface:
    w, h = int(64 * scale), int(28 * scale)
    arr = canvas(w, h)
    d = bayer(h, w)
    tones = [pal["cloud_shade"], mix(pal["cloud_shade"], pal["cloud"], 0.5), pal["cloud"], mix(pal["cloud"], (255, 255, 255), 0.6)]
    puffs = [(rng.uniform(w * 0.22, w * 0.78), h * rng.uniform(0.42, 0.62), rng.uniform(w * 0.13, w * 0.22)) for _ in range(6)]
    for cx, cy, r in sorted(puffs, key=lambda p: -p[1]):
        m = ellipse(h, w, cx, cy, r, r * 0.75) & (grid(h, w)[1] < h * 0.8)
        put(arr, m, ramp(tones, blob_light(h, w, cx, cy, r, r * 0.75) * 0.9 + 0.05, d))
    base = (grid(h, w)[1] >= h * 0.62) & (arr[:, :, 3] > 0)
    put(arr, base, ramp(tones, np.full((h, w), 0.2), d))
    return to_surface(arr)


def paint_sky(pal: dict, w: int, h: int, horizon: int, sun: tuple[int, int] | None) -> pygame.Surface:
    arr = canvas(w, h)
    xs, ys = grid(h, w)
    t = np.clip(ys / horizon, 0, 1)
    top, bot = np.array(pal["sky_top"], np.float32), np.array(pal["sky_bottom"], np.float32)
    # 12 тонов между верхом и горизонтом, переходы — упорядоченный дизеринг
    levels = 12
    v = t * (levels - 1)
    idx = v.astype(int) + ((v - v.astype(int)) > bayer(h, w)).astype(int)
    col = top + (bot - top) * (idx / (levels - 1))[..., None]
    if sun is not None:
        dist = np.sqrt((xs - sun[0]) ** 2 + ((ys - sun[1]) * 1.3) ** 2)
        glow = np.clip(1 - dist / 170, 0, 1) ** 2
        glow = np.round(glow * 4 + bayer(h, w) - 0.5) / 4
        col = col + (np.array(pal["light"], np.float32) - col) * (glow[..., None] * 0.45)
    arr[:, :, :3] = np.clip(col, 0, 255).astype(np.uint8)
    arr[:, :, 3] = 255
    return to_surface(arr)


def paint_hills(color, haze, w: int, h: int, seed: int, base: int, amp: float, freq: float,
                treeline: bool = False, texture: float = 0.12) -> pygame.Surface:
    rng = np.random.default_rng(seed)
    arr = canvas(w, h)
    xs, ys = grid(h, w)
    ph = rng.uniform(0, 6.28, 3)
    x1 = np.arange(w, dtype=np.float32)
    top = base - (np.sin(x1 * freq + ph[0]) * amp + np.sin(x1 * freq * 2.7 + ph[1]) * amp * 0.35
                  + np.sin(x1 * freq * 6.1 + ph[2]) * amp * 0.12)
    if treeline:
        bumps = value_noise(1, w, 3, rng)[0] * 7 + (rng.random(w) < 0.08) * 3
        top = top - bumps
    m = ys >= top[None, :]
    depth = np.clip((ys - top[None, :]) / 60, 0, 1)
    tones = [tint(color, 0.72), tint(color, 0.86), color, mix(color, haze, 0.25), mix(color, haze, 0.5)]
    n = value_noise(h, w, 4, rng)
    t = 0.75 - 0.45 * depth + texture * (n - 0.5) * 2
    t = np.where(ys < top[None, :] + 1.5, t + 0.2, t)  # освещённый гребень
    put(arr, m, ramp(tones, t, bayer(h, w)))
    return to_surface(arr)


def paint_house(pal: dict, lit: bool, rng: np.random.Generator, snow: bool = False) -> pygame.Surface:
    H, W = 30, 34
    arr = canvas(W, H)
    xs, ys = grid(H, W)
    d = bayer(H, W)
    walls = (xs >= 4) & (xs < 30) & (ys >= 13) & (ys < 30)
    plaster = [tint(pal["wood"], 0.7), tint(pal["wood"], 0.9), pal["wood"], tint(pal["wood"], 1.2)]
    put(arr, walls, ramp(plaster, 0.75 - 0.35 * (xs - 4) / 26 + 0.1 * _streaks(H, W, rng, 3), d))
    roof = np.zeros((H, W), bool)
    for yy in range(0, 15):
        half = 3 + 14 * yy / 14
        roof[yy, int(17 - half):int(17 + half)] = True
    put(arr, roof, ramp(THATCH, 0.8 - 0.4 * (ys % 3) / 3 + 0.15 * (1 - xs / W) - 0.1, d))
    if snow:
        cap = roof & (ys < 5 + 2 * value_noise(H, W, 2, rng))
        put(arr, cap, ramp(SNOW, 0.4 + 0.5 * (1 - xs / W), d))
    winc = (238, 190, 100) if lit else (46, 50, 66)
    put(arr, (xs >= 8) & (xs < 13) & (ys >= 17) & (ys < 22), winc)
    put(arr, (xs >= 19) & (xs < 25) & (ys >= 20) & (ys < 30), DARK[1])
    put(arr, (xs >= 23) & (xs < 26) & (ys >= 2) & (ys < 8), STONE[1])
    soft_outline(arr, 0.55)
    return to_surface(arr)


def paint_windmill(pal: dict, rng: np.random.Generator) -> pygame.Surface:
    """Башня мельницы (крылья рисуются поверх и вращаются)."""
    H, W = 70, 26
    arr = canvas(W, H)
    xs, ys = grid(H, W)
    d = bayer(H, W)
    half = 5 + 7 * ys / H
    body = (np.abs(xs - W / 2) < half) & (ys >= 8)
    put(arr, body, ramp(WOOD, 0.75 - 0.45 * (xs - W / 2 + half) / (2 * half) + 0.12 * _streaks(H, W, rng, 3) - 0.06, d))
    cap = ellipse(H, W, W / 2, 9, 8, 6) & (ys < 11)
    put(arr, cap, ramp(THATCH, blob_light(H, W, W / 2, 9, 8, 6), d))
    put(arr, (xs >= 10) & (xs < 16) & (ys >= 54) & (ys < 70), DARK[1])
    put(arr, (xs >= 11) & (xs < 15) & (ys >= 28) & (ys < 33), DARK[2])
    soft_outline(arr, 0.55)
    return to_surface(arr)


def paint_ground(pal: dict, w: int, h: int, rng: np.random.Generator, stage: int) -> pygame.Surface:
    arr = canvas(w, h)
    xs, ys = grid(h, w)
    g = pal["ground"]
    tones = [tint(g, 0.7), tint(g, 0.85), g, tint(g, 1.1), mix(tint(g, 1.2), pal["light"], 0.3)]
    t = 0.6 - 0.25 * ys / h + 0.3 * (value_noise(h, w, 5, rng) - 0.5) + 0.15 * (rng.random((h, w)) - 0.5)
    t = np.where(ys < 2, 0.95, t)
    put(arr, np.ones((h, w), bool), ramp(tones, t, bayer(h, w)))
    flowers = {1: [(250, 246, 250), (250, 214, 90), (238, 150, 196)], 2: [(250, 214, 90), (230, 90, 70)],
               3: [(214, 110, 40), (160, 70, 40)], 4: []}[stage]
    for _ in range(60 if flowers else 0):
        fx, fy = int(rng.integers(0, w)), int(rng.integers(3, h - 1))
        arr[fy, fx, :3] = flowers[int(rng.integers(0, len(flowers)))]
    for _ in range(18):  # камушки
        sx, sy = rng.uniform(4, w - 4), rng.uniform(5, h - 3)
        m = ellipse(h, w, sx, sy, rng.uniform(1.5, 3), 1.4)
        put(arr, m, ramp(STONE, blob_light(h, w, sx, sy, 3, 1.4) * 0.7 + 0.2, bayer(h, w)))
    return to_surface(arr)


def paint_front(pal: dict, w: int, h: int, rng: np.random.Generator, stage: int) -> pygame.Surface:
    arr = canvas(w, h)
    base = pal["grass"]
    tones = [tint(base, 0.6), tint(base, 0.8), base, mix(base, pal["light"], 0.35)]
    for x in range(0, w, 2):
        hgt = int(rng.integers(3, 11))
        lean = rng.uniform(-0.35, 0.35)
        for k in range(hgt):
            px = int(round(x + lean * k))
            if 0 <= px < w:
                arr[h - 1 - k, px, :3] = tones[min(3, int(k / hgt * 4 + rng.random() * 0.8))]
                arr[h - 1 - k, px, 3] = 255
    return to_surface(arr)


def paint_bush(pal: dict, rng: np.random.Generator, w: int = 40, h: int = 26, berries: bool = True) -> pygame.Surface:
    arr = canvas(w, h)
    leaves = leaf_palette(pal, 1)
    d = bayer(h, w)
    for _ in range(6):
        cx, cy, r = rng.uniform(w * 0.25, w * 0.75), rng.uniform(h * 0.45, h * 0.7), rng.uniform(7, 10)
        m = ellipse(h, w, cx, cy, r, r * 0.8) & (grid(h, w)[1] < h - 1)
        put(arr, m, ramp(leaves, 0.1 + 0.8 * blob_light(h, w, cx, cy, r, r * 0.8) + 0.1 * value_noise(h, w, 2, rng), d))
    if berries:
        spots = (arr[:, :, 3] > 0) & (rng.random((h, w)) < 0.025)
        put(arr, spots, pal["accent"])
    soft_outline(arr, 0.6)
    return to_surface(arr)


def paint_fence(pal: dict, w: int, rng: np.random.Generator) -> pygame.Surface:
    H = 40
    arr = canvas(w, H)
    xs, ys = grid(H, w)
    d = bayer(H, w)
    for x0 in range(0, w - 4, 14):
        post = (xs >= x0) & (xs < x0 + 5) & (ys >= 6 + (x0 // 14) % 2) & (ys < 40)
        tip = (ys < 9 + (x0 // 14) % 2) & (np.abs(xs - x0 - 2.5) > (ys - 4 - (x0 // 14) % 2) * 0.9)
        post &= ~tip
        put(arr, post, ramp(WOOD, 0.75 - 0.4 * (xs - x0) / 5 + 0.15 * _streaks(H, w, rng, 3) - 0.1, d))
    for ry in (13, 27):
        rail = (ys >= ry) & (ys < ry + 4) & (arr[:, :, 3] == 0)
        put(arr, rail, ramp(WOOD, np.select([ys < ry + 1, ys < ry + 3], [0.85, 0.6], 0.35)
                            + 0.12 * _streaks(H, w, rng, 1) - 0.06, d))
    soft_outline(arr, 0.55)
    return to_surface(arr)


def light_rays(w: int, h: int, origin: tuple[int, int], color) -> pygame.Surface:
    """Полупрозрачные солнечные лучи (статичный слой, альфа меняется в игре)."""
    arr = canvas(w, h)
    xs, ys = grid(h, w)
    ang = np.arctan2(ys - origin[1], xs - origin[0])
    rays = (np.sin(ang * 23) > 0.86) & (ys > origin[1])
    dist = np.sqrt((xs - origin[0]) ** 2 + (ys - origin[1]) ** 2)
    fade = np.clip(1 - dist / (w * 0.8), 0, 1)
    m = rays & (bayer(h, w) < fade * 0.6)
    arr[m] = (*color, 34)
    return to_surface(arr)


def sun_disc(pal: dict, r: int, moon: bool) -> pygame.Surface:
    size = r * 2 + 12
    arr = canvas(size, size)
    c = size / 2
    d = bayer(size, size)
    halo = ellipse(size, size, c, c, r + 5, r + 5) & ~ellipse(size, size, c, c, r, r) & (d < 0.35)
    arr[halo] = (*pal["light"], 110)
    m = ellipse(size, size, c, c, r, r)
    tones = [tint(pal["sun"], 0.85), pal["sun"], mix(pal["sun"], (255, 255, 255), 0.5)]
    put(arr, m, ramp(tones, blob_light(size, size, c, c, r, r), d))
    if moon:
        for cx, cy, rr in ((c + r * 0.3, c - r * 0.2, r * 0.25), (c - r * 0.35, c + r * 0.3, r * 0.18)):
            multiply(arr, ellipse(size, size, cx, cy, rr, rr) & m, 0.85)
    return to_surface(arr)


_RIG: dict[int, dict] = {}


def rig_for(stage: int) -> dict:
    """Курятники, жёлоба, шест и площадка сезона (рисуются один раз)."""
    rig = _RIG.get(stage)
    if rig is None:
        from ..logic.types import Side
        from .layout import CHUTE_DROP, CHUTE_END_X, CHUTE_START_X, GROUND_Y, ROW_Y

        coop = paint_coop(stage)
        chute = paint_chute(CHUTE_END_X - CHUTE_START_X, CHUTE_DROP)
        rig = _RIG[stage] = {
            "coop": {Side.LEFT: coop, Side.RIGHT: pygame.transform.flip(coop, True, False)},
            "chute": {Side.LEFT: chute, Side.RIGHT: pygame.transform.flip(chute, True, False)},
            "pole": paint_pole(GROUND_Y - ROW_Y[0]),
            "platform": paint_platform(),
        }
    return rig
