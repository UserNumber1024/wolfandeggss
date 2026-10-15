"""Отрисовка игры и визуальные реакции на события (spec 4.5, 5.9)."""

from __future__ import annotations

import math
import random
from typing import Sequence

import pygame

from .. import balance as B
from ..logic.events import (
    ComboReset, ComboUp, CoopSilenced, Defeat, EggCaught, EggMissed, EggTelegraphed, Event, HareHidden,
    HareShown, LifeChanged, RottenCaught, RottenDodged, RowOpened, StageStarted, Victory, WaveStarted,
)
from ..logic.game import Game
from ..logic.types import MANDATORY, Egg, EggKind, Pos, Side, SpecialWave
from . import texts
from .background import BackgroundDirector
from .effects_colors import COMBO_COLORS, PARTICLE_COLORS
from .font import PixelFont
from .hud import HEARTS_X, Banner, draw_hud, draw_legend
from .juice import FloatingTexts, HitStop, Particles, Shake
from .layout import (
    COOP_DOOR_CX, COOP_THRESHOLD_Y, GROUND_Y, H, HUD_H, ROW_Y, W, WOLF_X, basket_point, chute_point, coop_rect, wolf_anchor,
)
from . import scenery
from .sprites import Sprites
from .weather import Weather

WOLF_BODY_IN_FRAME = 15  # центр тела в кадре с контуром (смотрит вправо)
WOLF_FRAME_W = 50
MOVE_TIME = 0.09
EGG_LIFT = 8  # яйцо катится поверх жёлоба
FALL_GRAVITY = 900.0
HARE_STAND_X = 44  # заяц выбегает слева и садится в левом нижнем углу
HARE_SPEED = 4.0  # скорость выбегания (доля пути в секунду)
FLASH_TIME = 0.15


class GameRenderer:
    def __init__(self, sprites: Sprites, font: PixelFont, stage: int, open_rows: Sequence[int]):
        self.sprites = sprites
        self.font = font
        self.font2 = PixelFont(2)
        self.font3 = PixelFont(3)
        self.bg = BackgroundDirector(sprites, stage, open_rows)
        self.weather = Weather(stage)
        self.shake = Shake()
        self.hitstop = HitStop()
        self.particles = Particles()
        self.floats = FloatingTexts(self.font2)
        self.banner = Banner()
        self.world = pygame.Surface((W, H))
        self.t = 0.0
        self.heart_flash = 0.0
        self.low_pulse = 0.0
        # волк
        self.wolf_pos: Pos | None = None
        self.wolf_from: tuple[float, float] | None = None
        self.move_t = 1.0
        self.anim, self.anim_t = "idle", 0.0
        self.blink_t = 2.5
        # объекты сцены
        self.cluck: dict[Pos, float] = {}
        self.falling: list[dict] = []
        self.chicks: list[list] = []  # x, y, vx, t
        self.splats: list[list] = []  # x, t, kind
        self.dropping: list[dict] = []  # пойманные яйца падают в корзину
        self.sound_queue: list[tuple[str, int]] = []  # звуки, которые случаются позже события
        self.flash = 0.0
        self.hare_show = 0.0
        self.hare_target = 0.0
        self.fireworks = 0.0

    # --- события -> визуал и звуковые команды ------------------------------
    def handle(self, events: Sequence[Event], game: Game) -> list[tuple[str, int]]:
        sounds: list[tuple[str, int]] = []
        for e in events:
            if isinstance(e, EggCaught):
                sounds += self._on_catch(e, game)
            elif isinstance(e, EggMissed):
                self._drop(e.egg, game)
                if e.damage_halves > 0:  # шлепок и писк — при ударе о землю (_splat)
                    self.shake.add(3, 0.15)
                    self.heart_flash = 0.6
                    self._set_anim("sad", 0.4)
                    sounds.append(("life_lost", 0))
            elif isinstance(e, RottenCaught):
                self._drop_into_basket(e.egg, game)
                x, y = basket_point(e.egg.chute)
                self.particles.burst(x, y - 4, (120, 170, 60), 18, 50, 0.7, gravity=-30, size=2)
                self.shake.add(3, 0.15)
                self.heart_flash = 0.6
                self._set_anim("sad", 0.4)
                sounds += [("rotten_caught", 0), ("life_lost", 0)]
            elif isinstance(e, RottenDodged):
                self._drop(e.egg, game)
                x, y = chute_point(e.egg.chute, 1.0)
                self.floats.spawn(f"+{e.points}", x, y - 18, (170, 170, 180))
                sounds.append(("rotten_dodged", 0))
            elif isinstance(e, ComboUp):
                self.floats.spawn(texts.COMBO.format(n=e.multiplier), W - 40, HUD_H + 10, COMBO_COLORS[e.multiplier])
                self.hitstop.trigger(0.05)
                sounds.append(("combo_up", 0))
            elif isinstance(e, ComboReset):
                if e.lost_streak >= 5:
                    self.floats.spawn(texts.COMBO.format(n=1), W - 40, HUD_H + 10, (150, 150, 160))
                    sounds.append(("combo_reset", 0))
            elif isinstance(e, EggTelegraphed):
                self.cluck[e.egg.chute] = B.TELEGRAPH_TIME + 0.25
                sounds.append(("cluck", 0))
            elif isinstance(e, WaveStarted):
                sub = {SpecialWave.GOLD_RUSH: texts.GOLD_RUSH, SpecialWave.HURRICANE: texts.HURRICANE}.get(e.special)
                self.banner.show(texts.WAVE.format(n=e.number), sub)
                sounds.append(("wave_start", 0))
            elif isinstance(e, StageStarted):
                self.banner.show(texts.STAGE.format(n=e.stage, name=B.STAGE_NAMES[e.stage]))
                self.bg.set_stage(e.stage)
                self.weather.set_stage(e.stage)
                sounds.append(("stage_start", 0))
            elif isinstance(e, RowOpened):
                self.bg.open_row(e.row)
                self.hitstop.trigger(0.06)
                sounds.append(("row_open", 0))
            elif isinstance(e, CoopSilenced):
                r = coop_rect(e.pos)
                self.particles.burst(r.centerx, r.centery, (190, 160, 255), 14, 40, 0.8, gravity=-20, size=2)
            elif isinstance(e, HareShown):
                self.hare_target = 1.0
                sounds.append(("hare", 0))
            elif isinstance(e, HareHidden):
                self.hare_target = 0.0
            elif isinstance(e, LifeChanged):
                if e.delta < 0 and e.halves <= 2:  # последние сердца — крупный отклик
                    self.hitstop.trigger(0.07)
                    self.flash = FLASH_TIME
                if e.delta > 0:
                    self.floats.spawn("♥", HEARTS_X + 9 + ((e.halves - 1) // 2) * 19, HUD_H + 4, (255, 110, 150))
            elif isinstance(e, Victory):
                self.fireworks = 6.0
            elif isinstance(e, Defeat):
                self._set_anim("sad", 99.0)
        return sounds

    def _on_catch(self, e: EggCaught, game: Game) -> list[tuple[str, int]]:
        kind = e.egg.kind
        x, y = basket_point(game.wolf)
        color = PARTICLE_COLORS[kind]
        self._set_anim("catch", 0.16)
        self._drop_into_basket(e.egg, game)
        self.particles.burst(x, y - 4, color, 4 if kind is EggKind.NORMAL else 14, 45, 0.5, size=1 if kind is EggKind.NORMAL else 2)
        self.floats.spawn(f"+{e.points}", x, y - 22, COMBO_COLORS[e.multiplier])
        if kind is EggKind.NORMAL:
            return [("catch", min(game.combo.streak // 3, 7))]
        if kind is EggKind.GOLDEN:
            self.hitstop.trigger(0.06)
            self.particles.burst(x, y - 6, (255, 250, 200), 10, 80, 0.4, gravity=0)
        if kind is EggKind.HEART:
            self.hitstop.trigger(0.05)
        return [(f"catch_{kind.value}", 0)]

    def _drop(self, egg: Egg, game: Game) -> None:
        x, y = chute_point(egg.chute, 1.0)
        self.falling.append({"kind": egg.kind, "x": x + egg.chute.side.value * -4, "y": y - EGG_LIFT,
                             "vy": 0.0, "vx": egg.chute.side.value * -30.0, "rot": 0.0})

    def _drop_into_basket(self, egg: Egg, game: Game) -> None:
        x, y = chute_point(egg.chute, 1.0)
        _, by = basket_point(game.wolf)
        self.dropping.append({"kind": egg.kind, "x": x, "y": y - EGG_LIFT, "vy": 40.0, "target": by - 2})

    def drain_sounds(self) -> list[tuple[str, int]]:
        """Звуки, привязанные к анимации (удар яйца о землю), — забрать и проиграть."""
        out, self.sound_queue = self.sound_queue, []
        return out

    def hare_rect(self, show: float) -> pygame.Rect:
        """Заяц выбегает из-за левого края и садится целиком на землю."""
        img = self.sprites.hare[0]
        w, h = img.get_size()
        k = 1 - (1 - max(0.0, min(1.0, show))) ** 2
        x = int(-w + (HARE_STAND_X + w) * k)
        return pygame.Rect(x, GROUND_Y - h, w, h)

    def _set_anim(self, name: str, dur: float) -> None:
        if self.anim == "sad" and self.anim_t > 1.0 and name != "sad":
            return
        self.anim, self.anim_t = name, dur

    # --- обновление ---------------------------------------------------------
    def update(self, real_dt: float, game: Game) -> None:
        dt = real_dt
        self.t += dt
        self.hitstop.update(dt)
        self.shake.update(dt)
        self.particles.update(dt)
        self.floats.update(dt)
        self.banner.update(dt)
        self.heart_flash = max(0.0, self.heart_flash - dt)
        self.flash = max(0.0, self.flash - dt)
        for d in self.dropping:
            d["vy"] += FALL_GRAVITY * dt
            d["y"] += d["vy"] * dt
        self.dropping = [d for d in self.dropping if d["y"] < d["target"]]
        wind = 1.0 if game.hurricane else (0.15 if game.params.stage == 4 else 0.05)
        self.bg.set_wind(wind)
        self.weather.set_wind(1.0 if game.hurricane else 0.0)
        stage_level = ((game.params.number - 1) % B.WAVES_PER_STAGE) / (B.WAVES_PER_STAGE - 1)
        self.weather.set_intensity(stage_level * 0.7 + game.wave_progress * 0.3)
        self.bg.update(dt, game.wolf.side)
        self.weather.update(dt)

        # волк: догоняющая анимация перехода
        if self.wolf_pos != game.wolf:
            if self.wolf_pos is not None:
                self.wolf_from = self._wolf_xy()
                self.move_t = 0.0
                if self.anim not in ("catch", "sad"):
                    self._set_anim("move", MOVE_TIME + 0.05)
            self.wolf_pos = game.wolf
        self.move_t = min(1.0, self.move_t + dt / MOVE_TIME)
        self.anim_t -= dt
        if self.anim_t <= 0 and self.anim != "idle":
            self.anim = "idle"
        self.blink_t -= dt
        if self.blink_t < -0.12:
            self.blink_t = random.uniform(2.0, 4.5)

        for pos in list(self.cluck):
            self.cluck[pos] -= dt
            if self.cluck[pos] <= 0:
                del self.cluck[pos]

        for f in self.falling:
            f["vy"] += FALL_GRAVITY * dt
            f["y"] += f["vy"] * dt
            f["x"] += f["vx"] * dt
            f["rot"] += dt * 12
        landed = [f for f in self.falling if f["y"] >= GROUND_Y]
        self.falling = [f for f in self.falling if f["y"] < GROUND_Y]
        for f in landed:
            self._splat(f)

        for sp in self.splats:
            sp[1] += dt
        self.splats = [sp for sp in self.splats if sp[1] < 1.2]
        for c in self.chicks:
            c[0] += c[2] * dt
            c[3] += dt
        self.chicks = [c for c in self.chicks if -12 < c[0] < W + 12]

        step = HARE_SPEED * dt
        self.hare_show += max(-step, min(step, self.hare_target - self.hare_show))
        if self.fireworks > 0:
            self.fireworks -= dt
            if random.random() < dt * 6:
                col = random.choice([(255, 220, 90), (255, 120, 200), (140, 230, 255), (180, 255, 140)])
                self.particles.burst(random.uniform(80, W - 80), random.uniform(50, 160), col, 30, 120, 1.2, gravity=60, size=2)
        low = game.lives.halves <= 2 and game.lives.halves > 0
        self.low_pulse = (self.low_pulse + dt) if low else 0.0

    def _splat(self, f: dict) -> None:
        x = f["x"]
        kind = f["kind"]
        color = (130, 190, 60) if kind is EggKind.ROTTEN else (255, 214, 70)
        self.particles.burst(x, GROUND_Y - 2, color, 10, 60, 0.5, size=2, up=60)
        self.particles.burst(x, GROUND_Y - 2, (250, 248, 236), 8, 70, 0.5, up=80)
        self.splats.append([x, 0.0, kind])
        self.sound_queue.append(("splat", 0))
        if kind in MANDATORY:
            self.sound_queue.append(("chick", 0))
            direction = -1 if x < W / 2 else 1
            self.chicks.append([x, GROUND_Y - 9, direction * 55.0, 0.0])

    # --- отрисовка ----------------------------------------------------------
    def _wolf_xy(self) -> tuple[float, float]:
        tx, ty = wolf_anchor(self.wolf_pos)
        if self.wolf_from is None or self.move_t >= 1.0:
            return float(tx), float(ty)
        k = 1 - (1 - self.move_t) ** 2
        fx, fy = self.wolf_from
        return fx + (tx - fx) * k, fy + (ty - fy) * k

    def draw(self, surf: pygame.Surface, game: Game) -> None:
        world = self.world
        self.bg.draw_back(world)
        self._draw_rig(world, game)
        self._draw_eggs(world, game)
        self._draw_wolf(world, game)
        self._draw_ground_life(world)
        self.particles.draw(world)
        self.bg.draw_front(world)
        self.weather.draw(world)
        self.floats.draw(world)
        ox, oy = self.shake.offset
        if ox or oy:
            surf.fill((0, 0, 0))
        surf.blit(world, (ox, oy))
        draw_hud(surf, game, self.font2, self.sprites, self.heart_flash, self.t)
        draw_legend(surf, self.sprites, self.font)
        self.banner.draw(surf, self.font3, self.font2)
        if self.low_pulse > 0:
            a = int(60 + 50 * math.sin(self.low_pulse * 5))
            vign = pygame.Surface((W, H), pygame.SRCALPHA)
            pygame.draw.rect(vign, (200, 20, 40, a), (0, 0, W, H), 10)
            surf.blit(vign, (0, 0))
        if self.flash > 0:
            white = pygame.Surface((W, H), pygame.SRCALPHA)
            white.fill((255, 255, 255, int(120 * self.flash / FLASH_TIME)))
            surf.blit(white, (0, 0))

    def _rig(self) -> dict:
        return scenery.rig_for(self.bg.stage)

    def _draw_rig(self, s: pygame.Surface, game: Game) -> None:
        reveal = self.bg.row_reveal
        rows = [r for r in range(4) if reveal[r] > 0]
        if not rows:
            return
        rig = self._rig()
        top = ROW_Y[min(rows)] + 20
        pole = rig["pole"]
        s.blit(pole, (WOLF_X - pole.get_width() // 2, top), (0, 0, pole.get_width(), GROUND_Y - top))
        for r in rows:
            k = reveal[r]
            for side in Side:
                pos = Pos(side, r)
                # площадка волка
                fx, fy = wolf_anchor(pos)
                plat = rig["platform"]
                pw = max(1, int(plat.get_width() * k))
                img = plat if k >= 1 else pygame.transform.scale(plat, (pw, plat.get_height()))
                s.blit(img, (fx - pw // 2, fy - 1))
                # жёлоб выдвигается от курятника к центру
                chute = rig["chute"][side]
                cw = chute.get_width()
                vis = max(1, int(cw * k))
                x0, y0 = chute_point(pos, 0.0)
                if side is Side.LEFT:
                    s.blit(chute, (int(x0), int(y0)), (0, 0, vis, chute.get_height()))
                else:
                    s.blit(chute, (int(x0) - vis + 1, int(y0)), (cw - vis, 0, vis, chute.get_height()))
                # курятник «вырастает» от земли
                rect = coop_rect(pos)
                img = rig["coop"][side]
                if k < 1:
                    img = pygame.transform.scale(img, (img.get_width(), max(1, int(img.get_height() * k))))
                s.blit(img, (rect.x, rect.bottom - img.get_height()))
                if k >= 1:
                    self._draw_hen(s, game, pos, rect)

    def _draw_hen(self, s: pygame.Surface, game: Game, pos: Pos, rect: pygame.Rect) -> None:
        if pos not in game.active_coops:
            return
        frames = self.sprites.hen if pos.side is Side.LEFT else self.sprites.hen_left
        clucking = pos in self.cluck
        anim = frames["cluck" if clucking else "idle"]
        i = int(self.t * (10 if clucking else 1.5)) % 2
        img = anim[i]
        door_cx = rect.x + COOP_DOOR_CX if pos.side is Side.LEFT else rect.right - COOP_DOOR_CX
        hx = door_cx - img.get_width() // 2
        hy = rect.y + COOP_THRESHOLD_Y + 1 - img.get_height()
        if pos in game.silenced:
            img = img.copy()
            img.fill((90, 80, 120), special_flags=pygame.BLEND_RGB_MULT)
            z = self.font.render("Z", (200, 190, 255), (20, 16, 28))
            bob = int(math.sin(self.t * 3) * 2)
            s.blit(img, (hx, hy))
            s.blit(z, (hx + img.get_width() // 2, hy - 10 + bob))
            s.blit(z, (hx + img.get_width() // 2 + 6, hy - 16 - bob))
            return
        s.blit(img, (hx, hy))

    def _draw_eggs(self, s: pygame.Surface, game: Game) -> None:
        now = game.world_time
        for egg in game.eggs:
            if now < egg.lay_time:
                continue
            p = egg.progress(now)
            if game.hurricane:
                p = math.floor(p * B.HURRICANE_STEPS) / B.HURRICANE_STEPS
            x, y = chute_point(egg.chute, p)
            step = int(p * 24) * (1 if egg.chute.side is Side.LEFT else -1)
            img = self.sprites.egg_rotated(egg.kind, step)
            s.blit(img, (int(x - img.get_width() / 2), int(y - EGG_LIFT - img.get_height() / 2)))
            if egg.kind is EggKind.GOLDEN and int(self.t * 10) % 3 == 0:
                s.set_at((int(x) + random.randint(-5, 5), int(y - EGG_LIFT) + random.randint(-6, 4)), (255, 255, 220))
        for f in self.falling:
            img = self.sprites.egg_rotated(f["kind"], int(f["rot"]))
            s.blit(img, (int(f["x"] - img.get_width() / 2), int(f["y"] - img.get_height() / 2)))
        for d in self.dropping:
            img = self.sprites.egg[d["kind"]]
            s.blit(img, (int(d["x"] - img.get_width() / 2), int(d["y"] - img.get_height() / 2)))

    def _draw_wolf(self, s: pygame.Surface, game: Game) -> None:
        if self.wolf_pos is None:
            self.wolf_pos = game.wolf
        x, y = self._wolf_xy()
        side = self.wolf_pos.side
        frames = self.sprites.wolf if side is Side.RIGHT else self.sprites.wolf_left
        if self.anim == "idle":
            img = frames["idle"][1 if self.blink_t < 0 else 0]
            bob = 1 if math.sin(self.t * 2.6) > 0.3 else 0
        elif self.anim == "move":
            img = frames["move"][int(self.t * 20) % 2]
            bob = 0
        elif self.anim == "catch":
            img = frames["catch"][0 if self.anim_t > 0.08 else 1]
            bob = 0
        else:
            img = frames["sad"][0]
            bob = 0
        body = WOLF_BODY_IN_FRAME if side is Side.RIGHT else WOLF_FRAME_W - WOLF_BODY_IN_FRAME
        s.blit(img, (int(x) - body, int(y) - img.get_height() + 1 + bob))
        if game.effects.active(EggKind.MAGNET):
            bx, by = basket_point(self.wolf_pos)
            bx += x - wolf_anchor(self.wolf_pos)[0]
            r = 10 + int(math.sin(self.t * 12) * 2)
            pygame.draw.circle(s, (230, 80, 80), (int(bx), int(by)), r, 1)

    def _draw_ground_life(self, s: pygame.Surface) -> None:
        for x, t, kind in self.splats:
            frame = self.sprites.shell[min(2, int(t * 8))]
            if kind is EggKind.ROTTEN:
                frame = frame.copy()
                frame.fill((150, 210, 90), special_flags=pygame.BLEND_RGB_MULT)
            s.blit(frame, (int(x) - frame.get_width() // 2, GROUND_Y - frame.get_height() + 2))
        for x, y, vx, t in self.chicks:
            img = self.sprites.chick[int(t * 10) % 2]
            if vx < 0:
                img = pygame.transform.flip(img, True, False)
            s.blit(img, (int(x), int(y) - (1 if int(t * 10) % 2 else 0)))
        if self.hare_show > 0.0:
            running = abs(self.hare_target - self.hare_show) > 1e-3
            if running:
                img = self.sprites.hare[2 if int(self.t * 10) % 2 else 0]
            else:
                img = self.sprites.hare[1 if math.sin(self.t * 4) > 0.7 else 0]
            if running and self.hare_target < self.hare_show:
                img = pygame.transform.flip(img, True, False)  # убегает обратно влево
            r = self.hare_rect(self.hare_show)
            s.blit(img, (r.x, r.y + 1))
