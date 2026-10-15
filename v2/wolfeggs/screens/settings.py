"""Настройки: громкость музыки и звуков, полный экран (spec 6)."""

from __future__ import annotations

import pygame

from ..gfx import texts
from ..gfx.layout import W
from .base import CONFIRM_KEYS, DIR_KEYS, Screen, dim, draw_menu

STEP = 0.1


class SettingsScreen(Screen):
    def __init__(self, app, back: Screen):
        super().__init__(app)
        self.back = back
        self.selected = 0
        self.t = 0.0

    def _labels(self) -> list[str]:
        s = self.app.save
        music, sfx, full, back = texts.SETTINGS
        pct = lambda v: texts.PERCENT.format(n=round(v * 100))  # noqa: E731
        return [
            f"{music}  {pct(s.music_volume)}",
            f"{sfx}  {pct(s.sfx_volume)}",
            f"{full}  {texts.ON_OFF[0] if s.fullscreen else texts.ON_OFF[1]}",
            back,
        ]

    def handle(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        d = DIR_KEYS.get(event.key)
        if event.key == pygame.K_ESCAPE:
            self._leave()
        elif d in ("up", "down"):
            self.selected = (self.selected + (1 if d == "down" else -1)) % len(texts.SETTINGS)
            self.app.sfx.play("menu_move")
        elif d in ("left", "right"):
            self._adjust(STEP if d == "right" else -STEP)
        elif event.key in CONFIRM_KEYS:
            if self.selected == 2:
                self.app.toggle_fullscreen()
            elif self.selected == 3:
                self._leave()
            self.app.sfx.play("menu_select")

    def _adjust(self, delta: float) -> None:
        s = self.app.save
        if self.selected == 0:
            s.music_volume = round(min(1.0, max(0.0, s.music_volume + delta)), 2)
            self.app.music.volume = s.music_volume
        elif self.selected == 1:
            s.sfx_volume = round(min(1.0, max(0.0, s.sfx_volume + delta)), 2)
            self.app.sfx.volume = s.sfx_volume
        elif self.selected == 2:
            self.app.toggle_fullscreen()
            return
        else:
            return
        self.app.sfx.play("menu_move")
        self.app.store_save()

    def _leave(self) -> None:
        self.app.store_save()
        self.app.switch(self.back)

    def update(self, dt: float) -> None:
        self.t += dt
        self.back.update(dt)  # живой фон титульного экрана

    def draw(self, surf: pygame.Surface) -> None:
        app = self.app
        if hasattr(self.back, "bg"):
            self.back.bg.draw_back(surf)
            self.back.bg.draw_front(surf)
        dim(surf, 150)
        title = app.font3.render(texts.SETTINGS_TITLE, (255, 220, 100), (20, 16, 28))
        surf.blit(title, (W // 2 - title.get_width() // 2, 60))
        draw_menu(surf, app.font2, self._labels(), self.selected, W // 2, 130, self.t, gap=26)
