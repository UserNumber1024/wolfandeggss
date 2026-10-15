"""HUD и баннеры волн/этапов."""

from __future__ import annotations

import math

import pygame

from .. import balance as B
from ..logic.game import Game
from ..logic.types import EggKind
from . import texts
from .effects_colors import COMBO_COLORS
from .font import PixelFont
from .layout import H, HUD_H, W
from .sprites import Sprites

TEXT = (255, 240, 200)
SHADOW = (20, 16, 28)
HEARTS_X = 120
def hud_wave_label(game: Game) -> str:
    return texts.HUD_WAVE.format(s=game.params.stage, n=game.params.number)


def draw_hud(surf: pygame.Surface, game: Game, font: PixelFont, sprites: Sprites, heart_flash: float,
             t: float = 0.0) -> None:
    bar = pygame.Surface((W, HUD_H), pygame.SRCALPHA)
    bar.fill((16, 14, 30, 150))
    surf.blit(bar, (0, 0))
    big = font
    surf.blit(big.render(texts.SCORE.format(score=game.score), TEXT, SHADOW), (8, 3))

    # сердца
    slots = max(B.LIVES_START_HALVES, game.lives.halves + game.lives.halves % 2) // 2
    x0 = HEARTS_X
    blink = heart_flash > 0 and math.sin(heart_flash * 40) > 0
    for i in range(slots):
        h = game.lives.halves - i * 2
        key = "full" if h >= 2 else ("half" if h == 1 else "empty")
        if blink and key != "full" and h >= -1:
            continue
        surf.blit(sprites.hearts_x2[key], (x0 + i * 19, 2))

    ws = big.render(hud_wave_label(game), TEXT, SHADOW)
    surf.blit(ws, (W // 2 - ws.get_width() // 2 + 40, 3))

    mult = game.combo.multiplier
    if mult > 1:
        pulse = 1 if math.sin(t * 10) > 0.6 else 0
        cs = big.render(texts.COMBO.format(n=mult), COMBO_COLORS[mult], SHADOW)
        surf.blit(cs, (W - cs.get_width() - 8, 3 - pulse))

    # действующие эффекты: иконка и полоска таймера
    x = W - 120
    for kind, total in ((EggKind.CLOCK, B.CLOCK_DURATION), (EggKind.MAGNET, B.MAGNET_DURATION)):
        rem = game.effects.remaining(kind)
        if rem <= 0:
            continue
        icon = sprites.icons_x2[kind]
        surf.blit(icon, (x - 6, HUD_H + 2))
        w = int(26 * rem / total)
        pygame.draw.rect(surf, SHADOW, (x + 11, HUD_H + 7, 28, 4))
        pygame.draw.rect(surf, (255, 220, 120), (x + 12, HUD_H + 8, w, 2))
        x -= 46


LEGEND_ORDER = (EggKind.GOLDEN, EggKind.HEART, EggKind.CLOCK, EggKind.MAGNET, EggKind.SILENCE, EggKind.ROTTEN)
LEGEND_GAP = 12
LEGEND_COLORS = {EggKind.ROTTEN: (255, 150, 140)}


def legend_items() -> list[tuple[EggKind, str]]:
    """Подсказка по спецяйцам: яйцо и что оно даёт."""
    return [(k, texts.LEGEND[k.value].format(points=B.POINTS["golden"])) for k in LEGEND_ORDER]


def legend_width(font: PixelFont) -> int:
    items = legend_items()
    egg_w = 14 + 3
    return sum(egg_w + font.size(label)[0] for _, label in items) + LEGEND_GAP * (len(items) - 1)


def draw_legend(surf: pygame.Surface, sprites: Sprites, font: PixelFont) -> None:
    strip = pygame.Surface((W, 19), pygame.SRCALPHA)
    strip.fill((16, 14, 30, 150))
    surf.blit(strip, (0, H - 19))
    x = (W - legend_width(font)) // 2
    for kind, label in legend_items():
        egg = sprites.egg[kind]
        surf.blit(egg, (x, H - 18))
        x += egg.get_width() + 3
        surf.blit(font.render(label, LEGEND_COLORS.get(kind, TEXT), SHADOW), (x, H - 13))
        x += font.size(label)[0] + LEGEND_GAP


class Banner:
    IN, HOLD, OUT = 0.25, 0.7, 0.25

    def __init__(self) -> None:
        self.title: str | None = None
        self.subtitle: str | None = None
        self.t = 0.0
        self.queue: list[tuple[str, str | None]] = []

    @property
    def total(self) -> float:
        return self.IN + self.HOLD + self.OUT

    def show(self, title: str, subtitle: str | None = None) -> None:
        self.title, self.subtitle, self.t = title, subtitle, 0.0

    def update(self, dt: float) -> None:
        if self.title is None:
            return
        self.t += dt
        if self.t >= self.total:
            self.title = None

    Y = 110

    def rect(self, title_font: PixelFont, sub_font: PixelFont) -> pygame.Rect:
        """Лента по ширине текста, по центру — не закрывает курятники по краям."""
        tw, th = title_font.size(self.title or "")
        sw = sub_font.size(self.subtitle)[0] if self.subtitle else 0
        h = th + 16 + (sub_font.size("A")[1] + 6 if self.subtitle else 0)
        w = max(tw, sw) + 48
        return pygame.Rect(W // 2 - w // 2, self.Y, w, h)

    def draw(self, surf: pygame.Surface, title_font: PixelFont, sub_font: PixelFont) -> None:
        if self.title is None:
            return
        t = self.t
        if t < self.IN:
            k = 1 - (1 - t / self.IN) ** 3
            dx = int((1 - k) * -W)
        elif t < self.IN + self.HOLD:
            dx = 0
        else:
            k = (t - self.IN - self.HOLD) / self.OUT
            dx = int(k * k * W)
        ts = title_font.render(self.title, (255, 236, 150), SHADOW)
        r = self.rect(title_font, sub_font)
        y = r.y
        ribbon = pygame.Surface(r.size, pygame.SRCALPHA)
        ribbon.fill((16, 14, 30, 160))
        surf.blit(ribbon, (r.x + dx, y))
        surf.blit(ts, (W // 2 - ts.get_width() // 2 + dx, y + 8))
        if self.subtitle:
            ss = sub_font.render(self.subtitle, (150, 220, 255), SHADOW)
            surf.blit(ss, (W // 2 - ss.get_width() // 2 + dx, y + 14 + ts.get_height()))
