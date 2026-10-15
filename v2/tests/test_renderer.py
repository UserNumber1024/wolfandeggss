import random

import pygame

from wolfeggs.gfx.font import PixelFont
from wolfeggs.gfx.juice import HitStop, Shake
from wolfeggs.gfx.layout import H, W
from wolfeggs.gfx.renderer import GameRenderer
from wolfeggs.gfx.sprites import Sprites
from wolfeggs.logic.events import EggCaught
from wolfeggs.logic.game import Game
from wolfeggs.logic.types import Dir, Egg, EggKind


def test_render_full_game_smoke(display):
    g = Game(random.Random(1), start_wave=16)
    r = GameRenderer(Sprites(), PixelFont(), 4, g.open_rows)
    surf = pygame.Surface((W, H))
    for i in range(600):
        ev = g.update(1 / 60)
        if i % 20 == 0:
            ev += g.move([Dir.UP, Dir.LEFT, Dir.DOWN, Dir.RIGHT][i // 20 % 4])
        r.handle(ev, g)
        r.update(1 / 60, g)
        r.draw(surf, g)


def test_sound_commands_for_catch(display):
    g = Game(random.Random(1))
    r = GameRenderer(Sprites(), PixelFont(), 1, g.open_rows)
    e = Egg(1, g.wolf, EggKind.GOLDEN, 0, 1)
    assert ("catch_golden", 0) in r.handle([EggCaught(e, 5, 1, False)], g)


def test_hitstop_capped():
    h = HitStop()
    h.trigger(0.06)
    h.trigger(0.06)
    h.update(0.081)
    assert not h.active


def test_shake_capped():
    s = Shake()
    for _ in range(10):
        s.add(3, 0.2)
    assert max(abs(v) for v in s.offset) <= 4


def test_hud_label_shows_stage_and_wave():
    from wolfeggs.gfx.hud import hud_wave_label

    assert hud_wave_label(Game(random.Random(1), start_wave=16)) == "ЭТАП 4 · ВОЛНА 16"


def _renderer(start_wave=1):
    g = Game(random.Random(1), start_wave=start_wave)
    return g, GameRenderer(Sprites(), PixelFont(), 1, g.open_rows)


def test_splat_sound_plays_when_egg_hits_ground(display):
    from wolfeggs.logic.events import EggMissed
    from wolfeggs.logic.types import Pos, Side

    g, r = _renderer()
    egg = Egg(1, Pos(Side.RIGHT, 1), EggKind.NORMAL, 0, 1)
    immediate = r.handle([EggMissed(egg, 2)], g)
    assert ("splat", 0) not in immediate and ("life_lost", 0) in immediate
    assert r.drain_sounds() == []
    for _ in range(60):
        r.update(1 / 60, g)
    assert ("splat", 0) in r.drain_sounds()


def test_caught_egg_drops_into_basket(display):
    g, r = _renderer()
    r.handle([EggCaught(Egg(1, g.wolf, EggKind.NORMAL, 0, 1), 1, 1, False)], g)
    assert len(r.dropping) == 1


def test_hare_comes_out_whole(display):
    from wolfeggs.gfx.layout import GROUND_Y

    g, r = _renderer()
    shown, hidden = r.hare_rect(1.0), r.hare_rect(0.0)
    assert shown.left >= 0 and shown.bottom <= GROUND_Y + 2 and shown.height >= 30
    assert hidden.right <= 0


def test_bonus_legend_lists_every_special_egg(display):
    from wolfeggs.gfx.hud import legend_items, legend_width

    kinds = [k for k, _ in legend_items()]
    assert set(kinds) == set(EggKind) - {EggKind.NORMAL}
    assert legend_width(PixelFont()) <= W - 16


def test_last_hearts_juice(display):
    from wolfeggs.logic.events import LifeChanged

    g, r = _renderer()
    r.handle([LifeChanged(2, -2)], g)
    assert r.hitstop.active and r.flash > 0


def test_banner_does_not_cover_coops(display):
    from wolfeggs.gfx.layout import coop_rect
    from wolfeggs.logic.types import Pos, Side

    g, r = _renderer()
    r.banner.show("ЭТАП 4 · ЗИМА", "ЗОЛОТАЯ ЛИХОРАДКА")
    rect = r.banner.rect(r.font3, r.font2)
    for side in Side:
        for row in range(4):
            assert not rect.colliderect(coop_rect(Pos(side, row)))


def test_shake_duration_resets_on_new_shake():
    s = Shake()
    s.add(4, 1.0)
    s.update(0.95)
    s.add(4, 0.2)
    assert abs(s.time - 0.2) < 1e-9 and abs(s.duration - 0.2) < 1e-9
