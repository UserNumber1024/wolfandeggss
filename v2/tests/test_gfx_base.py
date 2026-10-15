from wolfeggs.gfx.font import PixelFont
from wolfeggs.gfx.layout import CHUTE_END_X, ROW_Y, W, basket_point, chute_point
from wolfeggs.gfx.pixel import grid_to_surface, outline
from wolfeggs.gfx.texts import all_texts
from wolfeggs.logic.types import Pos, Side


def test_font_covers_all_ui_text(display):
    f = PixelFont()
    for s in all_texts():
        for ch in s.upper():
            assert ch == " " or f.has_glyph(ch), (s, ch)


def test_font_size_scales(display):
    w1, h1 = PixelFont(1).size("ВОЛНА 7")
    w2, h2 = PixelFont(2).size("ВОЛНА 7")
    assert (w2, h2) == (2 * w1, 2 * h1) and h1 == 7


def test_grid_to_surface(display):
    s = grid_to_surface([".a", "a."], {"a": (255, 0, 0)})
    assert s.get_size() == (2, 2) and s.get_at((0, 0)).a == 0 and s.get_at((1, 0))[:3] == (255, 0, 0)


def test_outline_grows_by_two(display):
    s = outline(grid_to_surface(["a"], {"a": (255, 0, 0)}), (0, 0, 0))
    assert s.get_size() == (3, 3) and s.get_at((1, 0)).a == 255 and s.get_at((0, 0)).a == 0


def test_chute_endpoints_and_mirror():
    l0 = chute_point(Pos(Side.LEFT, 1), 1.0)
    r0 = chute_point(Pos(Side.RIGHT, 1), 1.0)
    assert l0 == (CHUTE_END_X, ROW_Y[1]) and r0 == (W - CHUTE_END_X, ROW_Y[1])


def test_basket_hangs_below_chute_end():
    # верх корзины ниже рейки примерно на размер яйца — яйцо падает в корзину
    for row in range(4):
        for side in Side:
            bx, by = basket_point(Pos(side, row))
            ex, ey = chute_point(Pos(side, row), 1.0)
            assert by - 4 >= ey + 8 and abs(bx - ex) <= 8
