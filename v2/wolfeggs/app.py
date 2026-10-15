"""Приложение: окно, целочисленное масштабирование, цикл, смена экранов."""

from __future__ import annotations

import pygame

from . import save
from .audio.music import Music
from .audio.sfx import Sfx
from .gfx.background import prebuild_scenes
from .gfx.font import PixelFont
from .gfx.layout import H, W
from .gfx.sprites import Sprites
from .screens.base import Screen

MAX_DT = 0.1
CAPTION = "Волк и яйца"


def window_flags(fullscreen: bool) -> int:
    """SCALED — целочисленное масштабирование холста на видеокарте (быстро даже в 4K)."""
    return pygame.SCALED | (pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE)


class App:
    def __init__(self, debug: bool = False, start_stage: int | None = None, seed: int | None = None,
                 headless: bool = False):
        pygame.init()
        self.debug = debug
        self.seed = seed
        self.headless = headless
        self.save = save.SaveData() if headless else save.load()
        self.fullscreen = self.save.fullscreen and not headless
        self.window = self._make_window()
        self.canvas = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.sprites = Sprites()
        self.font = PixelFont(1)
        self.font2 = PixelFont(2)
        self.font3 = PixelFont(3)
        self.font5 = PixelFont(5)
        self.sfx = Sfx(self.save.sfx_volume, enabled=not headless)
        self.music = Music(self.save.music_volume, enabled=not headless)
        if not headless:  # всё тяжёлое — при запуске, а не на смене этапа
            prebuild_scenes(self.sprites)
            self.music.preload()
        self.running = True
        self.screen: Screen | None = None

        from .screens.play import PlayScreen
        from .screens.title import TitleScreen

        if start_stage is not None:
            self.switch(PlayScreen(self, start_wave=(start_stage - 1) * 5 + 1))
        else:
            self.switch(TitleScreen(self))

    # --- окно ---------------------------------------------------------------
    def _make_window(self) -> pygame.Surface:
        pygame.display.set_caption(CAPTION)
        if self.headless:
            return pygame.display.set_mode((W, H))
        return pygame.display.set_mode((W, H), window_flags(self.fullscreen))

    def toggle_fullscreen(self) -> None:
        if self.headless:
            self.save.fullscreen = not self.save.fullscreen
            return
        self.fullscreen = not self.fullscreen
        self.save.fullscreen = self.fullscreen
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            self.window = self._make_window()
        self.store_save()

    def present(self) -> None:
        self.window.blit(self.canvas, (0, 0))
        pygame.display.flip()

    # --- экраны и цикл ------------------------------------------------------
    def switch(self, screen: Screen) -> None:
        self.screen = screen
        screen.on_enter()

    def store_save(self) -> None:
        if not self.headless:
            save.store(self.save)

    def quit(self) -> None:
        self.running = False

    def step(self, real_dt: float, events: list[pygame.event.Event]) -> None:
        real_dt = min(real_dt, MAX_DT)
        for e in events:
            if e.type == pygame.QUIT:
                self.quit()
            elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                self.toggle_fullscreen()
            else:
                self.screen.handle(e)
        self.screen.update(real_dt)
        self.screen.draw(self.canvas)
        self.music.update(real_dt)
        if not self.headless:
            self.present()

    def run(self) -> None:
        try:
            while self.running:
                real_dt = self.clock.tick(60) / 1000
                self.step(real_dt, pygame.event.get())
        finally:
            self.store_save()
            pygame.quit()
