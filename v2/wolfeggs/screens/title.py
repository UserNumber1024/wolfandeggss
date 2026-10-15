"""Титульный экран с живым весенним фоном (spec 6)."""

from __future__ import annotations

import math

import pygame

from ..gfx import texts
from ..gfx.background import BackgroundDirector
from ..gfx.hud import draw_legend
from ..gfx.layout import GROUND_Y, W
from ..gfx.weather import Weather
from ..logic.types import Side
from .base import CONFIRM_KEYS, DIR_KEYS, Screen, dim, draw_menu


class TitleScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.selected = 0
        self.t = 0.0
        self.bg = BackgroundDirector(app.sprites, 1, (1, 2))
        self.weather = Weather(1)
        self.weather.set_intensity(0.3)

    def on_enter(self) -> None:
        m = self.app.music
        m.play_stage(0)
        m.set_flags(False, False, False)
        m.set_intensity(0.3)

    def handle(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        d = DIR_KEYS.get(event.key)
        if d in ("up", "down"):
            self.selected = (self.selected + (1 if d == "down" else -1)) % len(texts.MENU)
            self.app.sfx.play("menu_move")
        elif event.key in CONFIRM_KEYS:
            self.app.sfx.play("menu_select")
            self._select()
        elif event.key == pygame.K_ESCAPE:
            self.app.quit()

    def _select(self) -> None:
        from .play import PlayScreen
        from .settings import SettingsScreen

        if self.selected == 0:
            self.app.switch(PlayScreen(self.app))
        elif self.selected == 1:
            self.app.switch(SettingsScreen(self.app, back=self))
        else:
            self.app.quit()

    def update(self, dt: float) -> None:
        self.t += dt
        self.bg.update(dt, Side.LEFT if math.sin(self.t * 0.4) < 0 else Side.RIGHT)
        self.weather.update(dt)

    def draw(self, surf: pygame.Surface) -> None:
        app = self.app
        self.bg.draw_back(surf)
        wolf = app.sprites.wolf["idle"][1 if (self.t % 3.2) > 3.05 else 0]
        surf.blit(wolf, (W // 2 - 15, GROUND_Y - wolf.get_height() + 2 + (1 if math.sin(self.t * 2.6) > 0.3 else 0)))
        self.bg.draw_front(surf)
        self.weather.draw(surf)
        dim(surf, 70)
        title = app.font5.render(texts.TITLE, (255, 220, 100), (60, 20, 30))
        bob = int(math.sin(self.t * 2) * 2)
        surf.blit(title, (W // 2 - title.get_width() // 2, 40 + bob))
        sub = app.font2.render(texts.SUBTITLE, (255, 255, 255), (20, 16, 28))
        surf.blit(sub, (W // 2 - sub.get_width() // 2, 88))
        draw_menu(surf, app.font2, list(texts.MENU), self.selected, W // 2, 140, self.t)
        if app.save.best_score:
            best = app.font2.render(texts.BEST.format(score=app.save.best_score), (200, 230, 255), (20, 16, 28))
            surf.blit(best, (W // 2 - best.get_width() // 2, 224))
        hint = app.font.render(texts.HINT_CONTROLS, (230, 230, 240), (20, 16, 28))
        surf.blit(hint, (W // 2 - hint.get_width() // 2, 250))
        draw_legend(surf, app.sprites, app.font)
