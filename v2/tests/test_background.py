import time

import pygame

from wolfeggs.balance import STAGE_OPEN_ROWS
from wolfeggs.gfx.background import BackgroundDirector
from wolfeggs.gfx.layout import H, W
from wolfeggs.gfx.sprites import Sprites
from wolfeggs.gfx.weather import MAX_PARTICLES, Weather
from wolfeggs.logic.types import Side


def test_each_stage_renders(display):
    s = Sprites()
    surf = pygame.Surface((W, H))
    for st in (1, 2, 3, 4):
        bg = BackgroundDirector(s, st, STAGE_OPEN_ROWS[st])
        w = Weather(st)
        for _ in range(30):
            bg.update(1 / 60, Side.LEFT)
            w.update(1 / 60)
            bg.draw_back(surf)
            w.draw(surf)
            bg.draw_front(surf)


def test_stage_crossfade_renders(display):
    bg = BackgroundDirector(Sprites(), 2, (1, 2))
    surf = pygame.Surface((W, H))
    bg.set_stage(3)
    for _ in range(150):
        bg.update(1 / 60, Side.RIGHT)
        bg.draw_back(surf)
    assert bg.stage == 3


def test_row_reveal_animates(display):
    bg = BackgroundDirector(Sprites(), 3, (1, 2))
    bg.open_row(0)
    for _ in range(90):
        bg.update(1 / 60, Side.LEFT)
    assert bg.row_reveal[0] == 1.0 and bg.row_reveal[3] == 0.0


def test_weather_particle_cap(display):
    w = Weather(4)
    w.set_intensity(1.0)
    w.set_wind(1.0)
    for _ in range(600):
        w.update(1 / 60)
    assert w.count() <= MAX_PARTICLES


def test_frame_budget(display):
    s = Sprites()
    surf = pygame.Surface((W, H))
    bg = BackgroundDirector(s, 4, (0, 1, 2, 3))
    w = Weather(4)
    w.set_intensity(1)
    for _ in range(60):  # прогрев
        bg.update(1 / 60, Side.RIGHT)
        w.update(1 / 60)
    t = time.perf_counter()
    for _ in range(120):
        bg.update(1 / 60, Side.RIGHT)
        w.update(1 / 60)
        bg.draw_back(surf)
        w.draw(surf)
        bg.draw_front(surf)
    assert (time.perf_counter() - t) / 120 < 0.006  # ≤ 6 мс на фон, остаток кадра — игре


def test_set_stage_is_fast_after_prebuild(display):
    from wolfeggs.gfx.background import prebuild_scenes

    s = Sprites()
    prebuild_scenes(s)
    bg = BackgroundDirector(s, 1, (1, 2))
    t = time.perf_counter()
    for st in (2, 3, 4):
        bg.set_stage(st)
    assert (time.perf_counter() - t) / 3 < 0.005


def test_prebuild_also_paints_coops_and_chutes(display):
    import time as _t

    from wolfeggs.gfx import scenery
    from wolfeggs.gfx.background import prebuild_scenes

    prebuild_scenes(Sprites())
    t = _t.perf_counter()
    for st in (1, 2, 3, 4):
        rig = scenery.rig_for(st)
        assert {"coop", "chute", "pole", "platform"} <= set(rig)
    assert _t.perf_counter() - t < 0.002
