"""Экран игры: ввод, пауза, итоги, музыка и звуки по событиям (spec 5, 6, 7)."""

from __future__ import annotations

import random

import pygame

from .. import balance as B
from ..gfx import texts
from ..gfx.layout import H, W
from ..gfx.renderer import GameRenderer
from ..logic.events import Defeat, Victory, WaveStarted
from ..logic.game import Game, Phase
from ..logic.types import Dir, EggKind, SpecialWave
from ..logic.waves import stage_of
from ..save import record_result
from .base import CONFIRM_KEYS, DIR_KEYS, Screen, dim, draw_menu

STEP = 1 / 60
DIRS = {"up": Dir.UP, "down": Dir.DOWN, "left": Dir.LEFT, "right": Dir.RIGHT}


class PlayScreen(Screen):
    def __init__(self, app, start_wave: int = 1):
        super().__init__(app)
        self.start_wave = start_wave
        rng = random.Random(app.seed) if app.seed is not None else random.Random()
        self.game = Game(rng, start_wave=start_wave)
        # отдельный генератор: зерно музыки не должно сдвигать случайность игры
        mrng = random.Random(f"music-{app.seed}") if app.seed is not None else random.Random()
        self.music_seed = mrng.randrange(1 << 30)
        self.renderer = GameRenderer(app.sprites, app.font, stage_of(start_wave), self.game.open_rows)
        self.paused = False
        self.pause_sel = 0
        self.acc = 0.0
        self.t = 0.0
        self.new_record = False

    @property
    def finished(self) -> bool:
        return self.game.phase in (Phase.WON, Phase.LOST)

    def on_enter(self) -> None:
        self._music_for_wave(self.start_wave)

    def _music_for_wave(self, wave: int) -> None:
        """Своя песня на каждую волну; следующая собирается в фоне заранее."""
        music = self.app.music
        music.play_wave(stage_of(wave), wave, self.music_seed)
        if wave < B.TOTAL_WAVES:
            music.prepare_wave(stage_of(wave + 1), wave + 1, self.music_seed)

    # --- ввод ---------------------------------------------------------------
    def handle(self, event: pygame.event.Event) -> None:
        if event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED):
            self._set_paused(True)
            return
        if event.type != pygame.KEYDOWN:
            return
        key = event.key
        if self.finished:
            if key == pygame.K_r:
                self.app.switch(PlayScreen(self.app, self.start_wave))
            elif key == pygame.K_ESCAPE:
                self._to_menu()
            return
        if self.paused:
            d = DIR_KEYS.get(key)
            if key == pygame.K_ESCAPE:
                self._to_menu()
            elif d in ("up", "down"):
                self.pause_sel = 1 - self.pause_sel
                self.app.sfx.play("menu_move")
            elif key in (pygame.K_SPACE, pygame.K_p) or (key in CONFIRM_KEYS and self.pause_sel == 0):
                self._set_paused(False)
            elif key in CONFIRM_KEYS:
                self._to_menu()
            return
        d = DIR_KEYS.get(key)
        if d:
            self._process(self.game.move(DIRS[d]))
        elif key in (pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_p):
            self._set_paused(True)
        elif self.app.debug:
            self._debug_key(key)

    def _debug_key(self, key: int) -> None:
        g = self.game
        if key == pygame.K_F2:
            g.skip_wave()
        elif key == pygame.K_F3:
            g.invulnerable = not g.invulnerable
        elif key == pygame.K_F4 and g.phase in (Phase.WAVE, Phase.DRAIN):
            target = min(B.TOTAL_WAVES, (stage_of(g.wave_number)) * B.WAVES_PER_STAGE + 1)
            g.skip_wave()
            g.wave_number = target - 1

    def _set_paused(self, paused: bool) -> None:
        if self.finished or paused == self.paused:
            return
        self.paused = paused
        self.pause_sel = 0
        self.app.music.set_paused(paused)
        self.app.sfx.play("pause")

    def _to_menu(self) -> None:
        from .title import TitleScreen

        self.app.music.set_paused(False)
        self.app.switch(TitleScreen(self.app))

    # --- такт ---------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t += dt
        if self.paused:
            return
        if self.renderer.hitstop.active or self.finished:
            self.acc = 0.0
        else:
            self.acc += dt
            while self.acc >= STEP:
                self.acc -= STEP
                self._process(self.game.update(STEP))
                if self.renderer.hitstop.active or self.finished:
                    self.acc = 0.0
                    break
        self.renderer.update(dt, self.game)
        for name, variant in self.renderer.drain_sounds():
            self.app.sfx.play(name, variant)
        g = self.game
        music = self.app.music
        music.set_intensity(((g.params.number - 1) % B.WAVES_PER_STAGE) / (B.WAVES_PER_STAGE - 1) * 0.7
                            + g.wave_progress * 0.3)
        golden = g.params.special is SpecialWave.GOLD_RUSH and g.phase in (Phase.WAVE, Phase.DRAIN)
        music.set_flags(g.effects.active(EggKind.CLOCK), g.effects.active(EggKind.MAGNET) or golden, g.hurricane)

    def _process(self, events) -> None:
        if not events:
            return
        for name, variant in self.renderer.handle(events, self.game):
            self.app.sfx.play(name, variant)
        for e in events:
            if isinstance(e, WaveStarted):
                self._music_for_wave(e.number)
            elif isinstance(e, (Victory, Defeat)):
                self._finish(isinstance(e, Victory))

    def _finish(self, won: bool) -> None:
        g = self.game
        self.new_record = record_result(self.app.save, g.score, g.max_wave_reached, g.combo.best)
        self.app.store_save()
        self.app.music.jingle("victory" if won else "defeat")

    # --- отрисовка ----------------------------------------------------------
    def draw(self, surf: pygame.Surface) -> None:
        app = self.app
        self.renderer.draw(surf, self.game)
        if self.paused:
            dim(surf)
            title = app.font3.render(texts.PAUSE, (255, 220, 100), (20, 16, 28))
            surf.blit(title, (W // 2 - title.get_width() // 2, 110))
            draw_menu(surf, app.font2, list(texts.PAUSE_MENU), self.pause_sel, W // 2, 160, self.t)
        elif self.finished:
            self._draw_result(surf)
        if app.debug:
            fps = app.font.render(f"FPS {app.clock.get_fps():.0f}  {'INV' if self.game.invulnerable else ''}",
                                  (255, 255, 255), (0, 0, 0))
            surf.blit(fps, (4, H - 10))

    def _draw_result(self, surf: pygame.Surface) -> None:
        app, g = self.app, self.game
        won = g.phase is Phase.WON
        dim(surf, 110 if won else 150)
        title = app.font3.render(texts.VICTORY if won else texts.GAME_OVER,
                                 (255, 220, 100) if won else (255, 120, 120), (20, 16, 28))
        surf.blit(title, (W // 2 - title.get_width() // 2, 80))
        y = 130
        values = {"score": g.score, "wave": g.max_wave_reached, "streak": g.combo.best}
        for line in texts.RESULT_LINES:
            img = app.font2.render(line.format(**values), (240, 240, 250), (20, 16, 28))
            surf.blit(img, (W // 2 - img.get_width() // 2, y))
            y += 22
        if self.new_record and int(self.t * 3) % 2 == 0:
            rec = app.font2.render(texts.NEW_RECORD, (255, 200, 90), (20, 16, 28))
            surf.blit(rec, (W // 2 - rec.get_width() // 2, y + 6))
        hint = app.font2.render(texts.HINT_END, (200, 230, 255), (20, 16, 28))
        surf.blit(hint, (W // 2 - hint.get_width() // 2, y + 40))
