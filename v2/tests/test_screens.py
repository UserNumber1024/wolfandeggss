import pygame

from wolfeggs.app import App
from wolfeggs.logic.game import Phase
from wolfeggs.screens.play import PlayScreen
from wolfeggs.screens.settings import SettingsScreen
from wolfeggs.screens.title import TitleScreen


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="")


def test_title_to_play(display):
    app = App(headless=True)
    assert isinstance(app.screen, TitleScreen)
    app.step(1 / 60, [key(pygame.K_RETURN)])
    assert isinstance(app.screen, PlayScreen)


def test_title_to_settings_and_back(display):
    app = App(headless=True)
    app.step(1 / 60, [key(pygame.K_DOWN), key(pygame.K_RETURN)])
    assert isinstance(app.screen, SettingsScreen)
    app.step(1 / 60, [key(pygame.K_ESCAPE)])
    assert isinstance(app.screen, TitleScreen)


def test_pause_freezes_game_time(display):
    app = App(headless=True)
    app.switch(PlayScreen(app))
    for _ in range(200):
        app.step(1 / 60, [])
    g = app.screen.game
    app.step(1 / 60, [key(pygame.K_SPACE)])
    w, r = g.world_time, g.real_time
    for _ in range(120):
        app.step(1 / 60, [])
    assert (g.world_time, g.real_time) == (w, r) and app.screen.paused


def test_focus_loss_pauses(display):
    app = App(headless=True)
    app.switch(PlayScreen(app))
    app.step(1 / 60, [pygame.event.Event(pygame.WINDOWFOCUSLOST)])
    assert app.screen.paused


def test_move_applies_during_hitstop(display):
    app = App(headless=True)
    ps = PlayScreen(app)
    app.switch(ps)
    for _ in range(200):
        app.step(1 / 60, [])
    ps.renderer.hitstop.trigger(0.08)
    before = ps.game.wolf
    app.step(1 / 60, [key(pygame.K_d if before.side.name == "LEFT" else pygame.K_a)])
    assert ps.game.wolf.side != before.side


def test_restart_after_defeat(display):
    app = App(headless=True)
    ps = PlayScreen(app)
    app.switch(ps)
    ps.game.lives.halves = 0
    ps.game.phase = Phase.LOST
    app.step(1 / 60, [key(pygame.K_r)])
    assert app.screen is not ps and app.screen.game.phase is not Phase.LOST


def test_escape_from_pause_goes_to_menu(display):
    app = App(headless=True)
    app.switch(PlayScreen(app))
    app.step(1 / 60, [key(pygame.K_ESCAPE)])
    assert app.screen.paused
    app.step(1 / 60, [key(pygame.K_ESCAPE)])
    assert isinstance(app.screen, TitleScreen)


class _Recorder:
    def __init__(self):
        self.calls = []
        self.enabled = False
        self.volume = 0.0

    def __getattr__(self, name):
        return lambda *a, **k: self.calls.append((name, a))


def test_game_end_plays_one_tune_only(display):
    app = App(headless=True)
    ps = PlayScreen(app)
    app.switch(ps)
    app.sfx, app.music = _Recorder(), _Recorder()
    ps._finish(won=True)
    assert ("jingle", ("victory",)) in app.music.calls
    assert not any(name == "play" and args[:1] in (("victory",), ("defeat",)) for name, args in app.sfx.calls)


def test_window_uses_gpu_scaling():
    from wolfeggs.app import window_flags

    assert window_flags(fullscreen=True) & pygame.SCALED and window_flags(True) & pygame.FULLSCREEN
    assert window_flags(fullscreen=False) & pygame.SCALED and not window_flags(False) & pygame.FULLSCREEN


def test_p_toggles_pause(display):
    app = App(headless=True)
    app.switch(PlayScreen(app))
    app.step(1 / 60, [key(pygame.K_p)])
    assert app.screen.paused
    app.step(1 / 60, [key(pygame.K_p)])
    assert not app.screen.paused


def test_pause_freezes_effects_and_hare(display):
    from wolfeggs.logic.types import EggKind

    app = App(headless=True)
    ps = PlayScreen(app)
    app.switch(ps)
    for _ in range(200):
        app.step(1 / 60, [])
    ps.game.effects.activate(EggKind.MAGNET)
    schedule = list(ps.game._hare_schedule)
    app.step(1 / 60, [key(pygame.K_SPACE)])
    rem = ps.game.effects.remaining(EggKind.MAGNET)
    for _ in range(120):
        app.step(1 / 60, [])
    assert ps.game.effects.remaining(EggKind.MAGNET) == rem and ps.game._hare_schedule == schedule


def test_each_wave_requests_its_own_song_and_prepares_next(display):
    from wolfeggs.logic.events import WaveStarted

    app = App(headless=True, seed=4)
    ps = PlayScreen(app)
    app.switch(ps)
    app.music = _Recorder()
    ps._process([WaveStarted(7, 2, None)])
    assert ("play_wave", (2, 7, ps.music_seed)) in app.music.calls
    assert ("prepare_wave", (2, 8, ps.music_seed)) in app.music.calls
    other = PlayScreen(App(headless=True, seed=5))
    assert other.music_seed != ps.music_seed
