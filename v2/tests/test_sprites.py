from wolfeggs.gfx.art import iter_all_grids
from wolfeggs.gfx.sprites import Sprites
from wolfeggs.logic.types import EggKind


def test_all_frames_have_declared_sizes(display):
    s = Sprites()
    assert all(f.get_size() == (48 + 2, 56 + 2) for f in sum(s.wolf.values(), []))  # +2 из-за контура
    assert set(s.wolf) == {"idle", "move", "catch", "sad"} and len(s.wolf["idle"]) == 2
    assert set(s.egg) == set(EggKind)


def test_rotation_cache(display):
    s = Sprites()
    a = s.egg_rotated(EggKind.NORMAL, 3)
    assert a is s.egg_rotated(EggKind.NORMAL, 19)  # 19 % 16 == 3


def test_grids_are_rectangular():
    for name, frames in iter_all_grids():
        for g in frames:
            assert len({len(r) for r in g}) == 1, name


def test_eggs_are_one_and_half_bigger(display):
    s = Sprites()
    assert all(img.get_size() == (12 + 2, 15 + 2) for img in s.egg.values())


def test_hud_icons_prescaled(display):
    s = Sprites()
    assert s.hearts_x2["full"].get_width() == 2 * s.hearts["full"].get_width()
    assert set(s.icons_x2) == set(s.icons)


def test_hare_has_whole_body(display):
    s = Sprites()
    assert all(f.get_height() >= 32 for f in s.hare)
