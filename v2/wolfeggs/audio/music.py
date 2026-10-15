"""Адаптивная чиптюн-музыка: своя мелодия на каждую волну (spec 7.1).

Песня волны — 16 тактов в тональности и темпе этапа. Форма (A/B/A′/C),
гармония, ритм мотивов, рисунок баса, ударных и арпеджио выбираются по
зерну партии и номеру волны, поэтому волны звучат по-разному, а каждая
партия — по-своему. Слои играют одновременно на своих каналах; интенсивность
и эффекты управляют только их громкостью. Музыку следующей волны собирает
фоновый поток.
"""

from __future__ import annotations

import random
from concurrent.futures import Future, ThreadPoolExecutor
from functools import lru_cache

import numpy as np

from .synth import SAMPLE_RATE, envelope, mix, mixer_available, noise, sweep, to_sound

LAYERS = ("bass", "drums", "lead", "harmony", "sparkle", "wind")
CHANNEL_NAMES = LAYERS + ("slow",)
# этап -> (тоника, лад, bpm); 0 — меню
STAGE_THEMES = {
    0: ("C", "major", 96),
    1: ("C", "major", 112),
    2: ("G", "major", 120),
    3: ("A", "minor", 128),
    4: ("D", "minor", 136),
}
_ROOTS = {"C": 261.63, "D": 293.66, "G": 196.0, "A": 220.0}
_MODES = {"major": (0, 2, 4, 5, 7, 9, 11), "minor": (0, 2, 3, 5, 7, 8, 10)}
# ступени аккордов, по одному на такт
PROGRESSIONS = {
    "major": [(0, 4, 5, 3), (0, 5, 3, 4), (0, 3, 4, 3), (5, 3, 0, 4), (0, 2, 3, 4), (3, 0, 4, 5)],
    "minor": [(0, 5, 2, 6), (0, 3, 6, 2), (0, 6, 5, 6), (0, 3, 4, 0), (5, 6, 0, 0), (0, 5, 3, 4)],
}
FORMS = [("A", "B", "A2", "C"), ("A", "A2", "B", "C"), ("A", "B", "C", "A2")]
# ритмические ячейки на такт в восьмых: x — нота, . — пауза/продление
RHYTHMS = ["x.x.xx.x", "x..x..x.", "xxx.x.x.", "x.xxx...", "x...x.xx", "x.x.x.x.", "xx.x.xx.", "x..xx.x.",
           "x.x..xx.", ".xx.x.x."]
ACCENTS = [(0, 6, 12), (4, 10), (0, 3, 8, 11), (2, 8, 14), (0, 10), (6, 12)]  # в шестнадцатых
BASS_STYLES = ("root", "rootfifth", "octave", "walk")
DRUM_STYLES = ("basic", "half", "four", "synco")
ARP_STYLES = ("up", "down", "updown", "broken", "pad")
BARS = 16
STEPS_PER_BAR = 16  # шестнадцатые
STEPS = BARS * STEPS_PER_BAR
FADE_TIME = 0.6


def samples_per_step(stage: int) -> int:
    return int(SAMPLE_RATE * 60 / STAGE_THEMES[stage][2] / 4)


def _semi(mode: tuple[int, ...], degree: int) -> int:
    return mode[degree % 7] + 12 * (degree // 7)


def _freq(root: float, semi: float) -> float:
    return root * 2 ** (semi / 12)


# --- план песни ----------------------------------------------------------------
def _plan(stage: int, wave: int, seed: int) -> dict:
    rng = random.Random(f"song-{seed}-{stage}-{wave}")
    mode_name = STAGE_THEMES[stage][1]
    form = rng.choice(FORMS)
    progs = rng.sample(PROGRESSIONS[mode_name], 3)
    sec_prog = {"A": progs[0], "A2": progs[0], "B": progs[1], "C": progs[2][:3] + (4,)}  # C кончается на V
    chords, sections = [], []
    for sec in form:
        chords += list(sec_prog[sec])
        sections += [sec] * 4
    styles = {sec: {"bass": rng.choice(BASS_STYLES), "drums": rng.choice(DRUM_STYLES), "arp": rng.choice(ARP_STYLES),
                    "duty": rng.choice((0.5, 0.25, 0.125)), "accent": rng.choice(ACCENTS)}
              for sec in ("A", "B", "C")}
    styles["A2"] = dict(styles["A"], arp=rng.choice(ARP_STYLES), duty=rng.choice((0.5, 0.25, 0.125)))
    cells = rng.sample(RHYTHMS, 6)
    motifs = {"A": (cells[0], cells[1], cells[2]), "B": (cells[3], cells[4], cells[3]), "C": (cells[5], cells[2], cells[5])}
    contours = {sec: rng.choice(("arch", "rise", "fall", "wave")) for sec in ("A", "B", "C")}
    return {"rng_seed": f"{seed}-{stage}-{wave}", "form": form, "chords": chords, "sections": sections,
            "styles": styles, "motifs": motifs, "contours": contours, "mode": _MODES[mode_name]}


def _contour(kind: str, p: float) -> float:
    if kind == "arch":
        return 4 * p * (1 - p) * 5
    if kind == "rise":
        return p * 5
    if kind == "fall":
        return (1 - p) * 5
    return 2.5 + 2.5 * np.sin(p * 2 * np.pi)


def melody_notes(stage: int, wave: int, seed: int) -> list[tuple[int, int, int, float]]:
    """Ноты мелодии: (шаг в шестнадцатых, полутон от тоники, длительность в шагах, громкость)."""
    plan = _plan(stage, wave, seed)
    rng = random.Random("mel-" + plan["rng_seed"])
    mode = plan["mode"]
    notes: list[tuple[int, int, int, float]] = []
    base_section: dict[str, list] = {}
    for si, sec in enumerate(plan["form"]):
        key = "A" if sec == "A2" else sec
        lift = {"A": 0, "A2": 0, "B": 1, "C": 3}[sec]
        if sec == "A2" and "A" in base_section:  # реприза: тот же мотив, вторая фраза выше, другое окончание
            src = base_section["A"]
            out = []
            for s, deg, dur, vel in src:
                bar = s // STEPS_PER_BAR
                if bar >= 2:
                    deg += 2
                if bar == 3 and s % STEPS_PER_BAR >= 8:
                    continue
                out.append((s, deg, dur, vel * rng.uniform(0.92, 1.08)))
            end = 3 * STEPS_PER_BAR + 8
            out.append((end, plan["chords"][si * 4 + 3] + rng.choice((0, 2, 4)) + lift, 8, 0.8))
            sec_notes = out
        else:
            r1, r2, r3 = plan["motifs"][key]
            bars = (r1, r2, r1, r3)
            onsets = [b * STEPS_PER_BAR + i * 2 for b, cell in enumerate(bars) for i, ch in enumerate(cell) if ch == "x"]
            sec_notes, prev, prev2 = [], rng.choice((0, 2, 4)), None
            for j, s in enumerate(onsets):
                bar = s // STEPS_PER_BAR
                chord = plan["chords"][si * 4 + bar]
                target = _contour(plan["contours"][key], s / (4 * STEPS_PER_BAR)) + lift
                if s % 8 == 0:  # сильная доля — тон аккорда, ближайший к контуру
                    cands = [chord + k + 7 * o for k in (0, 2, 4) for o in (-1, 0, 1)]
                    recent = [n[1] for n in sec_notes[-5:]]
                    deg = min(cands, key=lambda c: abs(c - target) + rng.random() * 1.5 + 1.4 * recent.count(c))
                else:
                    step = rng.choice((-2, -1, -1, 1, 1, 2)) if abs(prev - target) < 2 else (1 if target > prev else -1)
                    deg = prev + step
                if deg == prev == prev2:
                    deg += rng.choice((-1, 1))
                nxt = onsets[j + 1] if j + 1 < len(onsets) else 4 * STEPS_PER_BAR
                dur = max(1, min(nxt - s, 6))
                sec_notes.append((s, deg, dur, 0.0))
                prev2, prev = prev, deg
            base_section.setdefault(key, sec_notes)
        # динамика: дуга фразы, сменяющиеся акценты, случайные отклонения
        acc = plan["styles"][sec]["accent"]
        shifts = [rng.choice((0, 2, 4, 6, 10)) for _ in range(2)]  # рисунок акцентов сдвигается от фразы к фразе
        peaks = {}
        for s, deg, dur, vel in sec_notes:  # самая высокая нота каждой фразы — тоже акцент
            ph = s // (2 * STEPS_PER_BAR)
            if ph not in peaks or deg > peaks[ph][1]:
                peaks[ph] = (s, deg)
        peak_steps = {v[0] for v in peaks.values()}
        shaped = []
        for s, deg, dur, vel in sec_notes:
            ph = s // (2 * STEPS_PER_BAR)
            phrase_p = (s % (2 * STEPS_PER_BAR)) / (2 * STEPS_PER_BAR)
            accented = (s - shifts[ph % 2]) % STEPS_PER_BAR in acc or s in peak_steps
            v = 0.55 + 0.22 * np.sin(phrase_p * np.pi) + (0.18 if accented else 0) + rng.uniform(-0.08, 0.08)
            if vel:
                v = 0.5 * v + 0.5 * vel
            shaped.append((s + si * 4 * STEPS_PER_BAR, _semi(mode, deg), dur, float(np.clip(v, 0.3, 1.0))))
        notes += shaped
    # форшлаги: короткая соседняя нота перед частью нот
    graced = []
    taken = {n[0] for n in notes}
    for s, semi, dur, v in notes:
        if s > 0 and (s - 1) not in taken and rng.random() < 0.12:
            graced.append((s - 1, semi + rng.choice((1, 2, -1)), 1, v * 0.55))
        graced.append((s, semi, dur, v))
    return sorted(graced)


# --- синтез --------------------------------------------------------------------
def _pulse(freq: np.ndarray, duty: float) -> np.ndarray:
    phase = np.cumsum(freq) / SAMPLE_RATE
    return np.where(phase % 1.0 < duty, 1.0, -1.0)


def _tri(freq: np.ndarray) -> np.ndarray:
    phase = np.cumsum(freq) / SAMPLE_RATE
    return 4.0 * np.abs(phase % 1.0 - 0.5) - 1.0


def _note(f: float, dur: float, wave: str, vol: float, duty: float = 0.5, vibrato: bool = False,
          slide: bool = False, attack: float = 0.008) -> np.ndarray:
    n = max(1, int(dur * SAMPLE_RATE))
    t = np.arange(n) / SAMPLE_RATE
    freq = np.full(n, f, dtype=np.float64)
    if vibrato:
        freq *= 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.08) / 0.1, 0, 1)
    if slide:
        k = min(n, int(0.035 * SAMPLE_RATE))
        freq[:k] *= 2 ** (np.linspace(-1, 0, k) / 12)
    sig = _pulse(freq, duty) if wave == "pulse" else _tri(freq)
    rel = min(0.07, dur * 0.4)
    return envelope((sig * vol).astype(np.float32), attack, dur * 0.3, 0.62, rel)


def _place(buf: np.ndarray, sig: np.ndarray, start: int) -> None:
    if start >= len(buf):
        return
    end = min(len(buf), start + len(sig))
    buf[start:end] += sig[: end - start]


@lru_cache(maxsize=None)
def _drum_kit(stage: int) -> dict[str, np.ndarray]:
    g = np.random.default_rng(stage + 3)
    hat_src = noise(0.05, 0.3, g)
    hat = hat_src - np.convolve(hat_src, np.ones(4) / 4, mode="same")
    open_src = noise(0.16, 0.25, g)
    return {
        "kick": envelope(sweep(140, 42, 0.13, "sine", 0.95), 0.0, 0.03, 0.5, 0.08),
        "snare": mix(envelope(noise(0.13, 0.5, g), 0.0, 0.03, 0.3, 0.07),
                     envelope(sweep(260, 180, 0.08, "triangle", 0.25), 0.0, 0.02, 0.4, 0.04)),
        "hat": envelope(hat.astype(np.float32), 0.0, 0.008, 0.25, 0.015),
        "ohat": envelope((open_src - np.convolve(open_src, np.ones(4) / 4, mode="same")).astype(np.float32), 0.0, 0.02, 0.4, 0.1),
        "tom_hi": envelope(sweep(240, 150, 0.12, "sine", 0.7), 0.0, 0.03, 0.5, 0.06),
        "tom_lo": envelope(sweep(160, 90, 0.15, "sine", 0.75), 0.0, 0.03, 0.5, 0.08),
        "crash": envelope(noise(0.9, 0.22, g), 0.0, 0.1, 0.35, 0.6),
    }


@lru_cache(maxsize=8)
def _wind(n: int) -> np.ndarray:
    g = np.random.default_rng(99)
    coarse = g.uniform(-1, 1, n // 48 + 2)
    smooth = np.interp(np.arange(n) / 48, np.arange(len(coarse)), coarse)
    fine = g.uniform(-1, 1, n) * 0.25
    swell = 0.6 + 0.4 * np.sin(np.linspace(0, 6 * np.pi, n))
    return ((smooth * 0.75 + fine * smooth) * swell * 0.8).astype(np.float32)


def compose_wave(stage: int, wave: int, seed: int) -> dict[str, np.ndarray]:
    key, mode_name, _ = STAGE_THEMES[stage]
    root, mode = _ROOTS[key], _MODES[mode_name]
    plan = _plan(stage, wave, seed)
    rng = random.Random("arr-" + plan["rng_seed"])
    sps = samples_per_step(stage)
    sd = sps / SAMPLE_RATE  # секунд на шестнадцатую
    n = sps * STEPS
    L = {name: np.zeros(n, dtype=np.float32) for name in LAYERS}

    # мелодия: мягкий пульс с меняющейся скважностью, вибрато на долгих нотах, подтяжки
    for s, semi, dur, vel in melody_notes(stage, wave, seed):
        sec = plan["sections"][s // STEPS_PER_BAR]
        duty = plan["styles"][sec]["duty"]
        sig = _note(_freq(root, semi + 12), dur * sd * 0.95, "pulse", 0.26 * vel, duty,
                    vibrato=dur >= 4, slide=dur >= 3 and rng.random() < 0.18)
        _place(L["lead"], sig, s * sps)

    for bar in range(BARS):
        sec = plan["sections"][bar]
        st = plan["styles"][sec]
        chord = plan["chords"][bar]
        nxt = plan["chords"][(bar + 1) % BARS]
        b0 = bar * STEPS_PER_BAR
        last_of_section = bar % 4 == 3

        # бас
        style = st["bass"]
        r = _semi(mode, chord) - 24
        if style == "root":
            pattern = [(0, r, 3), (4, r, 3), (8, r, 3), (12, r, 3)]
        elif style == "rootfifth":
            pattern = [(0, r, 6), (8, _semi(mode, chord + 4) - 24, 6)]
        elif style == "octave":
            pattern = [(i, r + (12 if i % 4 == 2 else 0), 2) for i in range(0, 16, 2)]
        else:  # ходовой бас к следующему аккорду
            steps = [chord, chord + 2, chord + 4, nxt + (1 if nxt < chord else -1)]
            pattern = [(i * 4, _semi(mode, d) - 24, 3) for i, d in enumerate(steps)]
        if last_of_section and style != "walk":
            pattern[-1] = (pattern[-1][0], _semi(mode, nxt) - 24 - 1, pattern[-1][2])
        for s, semi, dur in pattern:
            vel = 0.75 + (0.15 if s == 0 else 0) + rng.uniform(-0.08, 0.08)
            _place(L["bass"], _note(_freq(root, semi), dur * sd, "tri", 0.5 * vel), (b0 + s) * sps)

        # ударные
        kit = _drum_kit(stage)
        ds = st["drums"]
        kicks = {"basic": (0, 8), "half": (0, 10), "four": (0, 4, 8, 12), "synco": (0, 6, 10)}[ds]
        snares = {"basic": (4, 12), "half": (8,), "four": (4, 12), "synco": (4, 12)}[ds]
        fill = last_of_section and bar != BARS - 1 or bar == BARS - 1
        for s in kicks:
            if not (fill and s >= 8):
                _place(L["drums"], kit["kick"] * rng.uniform(0.85, 1.0), (b0 + s) * sps)
        for s in snares:
            if not (fill and s >= 8):
                _place(L["drums"], kit["snare"] * rng.uniform(0.8, 1.0), (b0 + s) * sps)
        for s in range(0, 16, 2):
            if fill and s >= 8:
                break
            open_hat = ds == "four" and s % 4 == 2
            vel = (0.9 if s % 4 == 0 else 0.6) * rng.uniform(0.8, 1.1)
            _place(L["drums"], (kit["ohat"] if open_hat else kit["hat"]) * vel, (b0 + s) * sps)
            if ds == "synco" and rng.random() < 0.25:
                _place(L["drums"], kit["hat"] * 0.45, (b0 + s + 1) * sps)
        if fill:  # сбивка во второй половине последнего такта части
            kind = rng.choice(("snare_roll", "toms", "mixed"))
            for i, s in enumerate(range(8, 16)):
                v = 0.45 + 0.07 * i
                if kind == "snare_roll":
                    hit = kit["snare"]
                elif kind == "toms":
                    hit = kit["tom_hi"] if i < 4 else kit["tom_lo"]
                else:
                    hit = kit["snare"] if i % 2 == 0 else kit["tom_lo"]
                if kind != "snare_roll" or i % 2 == 0 or i >= 4:
                    _place(L["drums"], hit * v, (b0 + s) * sps)
        if bar % 4 == 0 and bar > 0:
            _place(L["drums"], kit["crash"], b0 * sps)

        # гармония: арпеджио или пэд
        tones = [_semi(mode, chord + k) for k in (0, 2, 4, 7)]
        arp = st["arp"]
        if arp == "pad":
            for semi in tones[:3]:
                _place(L["harmony"], _note(_freq(root, semi), 16 * sd, "pulse", 0.07, 0.5, attack=0.12), b0 * sps)
        else:
            order = {"up": [0, 1, 2, 3], "down": [3, 2, 1, 0], "updown": [0, 1, 2, 3, 2, 1],
                     "broken": [0, 2, 1, 3]}[arp]
            stride = 2 if rng.random() < 0.5 else 1
            for i, s in enumerate(range(0, 16, stride)):
                semi = tones[order[i % len(order)]]
                vel = 0.8 + (0.2 if s % 4 == 0 else 0) + rng.uniform(-0.1, 0.1)
                _place(L["harmony"], _note(_freq(root, semi), stride * sd * 0.9, "pulse", 0.11 * vel, 0.5), (b0 + s) * sps)

        # искры: редкие высокие ноты аккорда
        for s in range(0, 16, 2):
            if rng.random() < 0.35:
                semi = tones[rng.randrange(4)] + 24
                _place(L["sparkle"], _note(_freq(root, semi), sd * 1.5, "tri", 0.18 * rng.uniform(0.6, 1.0)), (b0 + s) * sps)

    L["wind"] = _wind(n).copy()
    out = {name: np.tanh(buf).astype(np.float32) for name, buf in L.items()}
    full = mix(out["bass"], out["drums"] * 0.8, out["lead"], out["harmony"])
    out["slow"] = np.repeat(full[: n // 2], 2)  # вдвое медленнее и на октаву ниже
    return out


def compose_stage(stage: int) -> dict[str, np.ndarray]:
    """Тема этапа (для меню — этап 0)."""
    return compose_wave(stage, 0, seed=0)


def layer_volumes(intensity: float, clock: bool, sparkle: bool, wind: bool) -> dict[str, float]:
    if clock:
        vols = {k: 0.0 for k in LAYERS}
        vols["slow"] = 1.0
        return vols
    return {
        "bass": 0.8,
        "lead": 0.6,
        "drums": 0.7 if intensity >= 0.25 else 0.0,
        "harmony": 0.45 if intensity >= 0.6 else 0.0,
        "sparkle": 0.5 if sparkle else 0.0,
        "wind": 0.6 if wind else 0.0,
        "slow": 0.0,
    }


def _jingle(name: str) -> np.ndarray:
    from .synth import notes

    if name == "victory":
        return mix(
            notes([(523.25, 0.15), (659.25, 0.15), (783.99, 0.15), (1046.5, 0.3), (783.99, 0.15), (1046.5, 0.9)], "square", 0.3, 0.25),
            notes([(261.63, 0.45), (392.0, 0.45), (523.25, 0.9)], "triangle", 0.4),
        )
    return mix(
        notes([(440, 0.25), (415.3, 0.25), (392, 0.25), (293.66, 0.9)], "square", 0.3),
        notes([(220, 0.75), (146.83, 0.9)], "triangle", 0.4),
    )


Key = tuple


class Music:
    MAX_CACHE = 3  # текущая, следующая и запасная песни

    def __init__(self, volume: float = 0.7, enabled: bool = True):
        self.enabled = enabled and mixer_available()
        self._volume = volume
        self.key: Key | None = None
        self._want: Key | None = None
        self._fade = 0.0
        self.intensity = 0.0
        self.flags = (False, False, False)
        self.paused = False
        self.current = {k: 0.0 for k in CHANNEL_NAMES}
        self.targets = layer_volumes(0.0, False, False, False)
        self._cache: dict[Key, dict] = {}
        self._futures: dict[Key, Future] = {}
        self._pool: ThreadPoolExecutor | None = None
        self.channels = {}
        if self.enabled:
            import pygame

            pygame.mixer.set_num_channels(32)
            pygame.mixer.set_reserved(len(CHANNEL_NAMES))
            self.channels = {name: pygame.mixer.Channel(i) for i, name in enumerate(CHANNEL_NAMES)}
            self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="music")

    @property
    def stage(self) -> int | None:
        return self.key[1] if self.key else None

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, value))

    # --- сборка песен ---
    @staticmethod
    def _build(key: Key) -> dict:
        layers = compose_stage(key[1]) if key[0] == "stage" else compose_wave(key[1], key[2], key[3])
        return {k: to_sound(v) for k, v in layers.items()}

    def _ensure(self, key: Key) -> None:
        if key in self._cache or key in self._futures:
            return
        self._futures[key] = self._pool.submit(self._build, key)

    def _collect(self) -> None:
        for key, fut in list(self._futures.items()):
            if fut.done():
                del self._futures[key]
                self._cache[key] = fut.result()
        while len(self._cache) > self.MAX_CACHE:
            old = next((k for k in self._cache if k not in (self.key, self._want)), None)
            if old is None:
                break
            del self._cache[old]

    def ready(self, key: Key) -> bool:
        if not self.enabled:
            return False
        self._collect()
        return key in self._cache

    def preload(self) -> None:
        """Музыка меню — сразу; песни волн собираются в фоне по ходу игры."""
        if self.enabled and ("stage", 0) not in self._cache:
            self._cache[("stage", 0)] = self._build(("stage", 0))

    def prepare_wave(self, stage: int, wave: int, seed: int) -> None:
        if self.enabled:
            self._ensure(("wave", stage, wave, seed))

    # --- что играть ---
    def play_stage(self, stage: int) -> None:
        self._request(("stage", stage))

    def play_wave(self, stage: int, wave: int, seed: int) -> None:
        self._request(("wave", stage, wave, seed))

    def _request(self, key: Key) -> None:
        if not self.enabled:
            return
        self._ensure(key)
        self._want = None if key == self.key else key

    def _start(self, key: Key) -> None:
        sounds = self._cache[key]
        for name, ch in self.channels.items():
            ch.set_volume(0.0)
            ch.play(sounds[name], loops=-1)
        self.current = {k: 0.0 for k in CHANNEL_NAMES}
        self.key, self._want, self._fade = key, None, 0.0

    def set_intensity(self, level: float) -> None:
        self.intensity = level
        self.targets = layer_volumes(level, *self.flags)

    def set_flags(self, clock: bool, sparkle: bool, wind: bool) -> None:
        self.flags = (clock, sparkle, wind)
        self.targets = layer_volumes(self.intensity, *self.flags)

    def set_paused(self, paused: bool) -> None:
        self.paused = paused

    def jingle(self, name: str) -> None:
        if not self.enabled:
            return
        for ch in self.channels.values():
            ch.fadeout(300)
        self.key, self._want, self._fade = None, None, 0.0
        snd = to_sound(_jingle(name))
        snd.set_volume(self._volume)
        snd.play()

    def update(self, dt: float) -> None:
        if not self.enabled:
            return
        self._collect()
        if self._want is not None and self._want in self._cache:
            if self.key is None:
                self._start(self._want)
            elif self._fade <= 0:
                for ch in self.channels.values():
                    ch.fadeout(int(FADE_TIME * 1000))
                self._fade = FADE_TIME
        if self._fade > 0:
            self._fade -= dt
            if self._fade <= 0:
                target = self._want or self.key  # запрос могли отменить во время затухания
                if target is not None and target in self._cache:
                    self._start(target)
                else:
                    self.key = None
        if self.key is None or self._fade > 0:
            return
        rate = dt / FADE_TIME
        duck = 0.3 if self.paused else 1.0
        for name, ch in self.channels.items():
            target = self.targets.get(name, 0.0)
            cur = self.current[name]
            cur += max(-rate, min(rate, target - cur))
            self.current[name] = cur
            ch.set_volume(cur * self._volume * duck)
