"""Примитивы чиптюн-синтеза на numpy. Сигналы — моно float32 в [-1, 1]."""

from __future__ import annotations

import numpy as np

SAMPLE_RATE = 44100

_mixer_state: bool | None = None


def _t(dur: float) -> np.ndarray:
    return np.arange(max(1, int(SAMPLE_RATE * dur)), dtype=np.float64) / SAMPLE_RATE


def _osc(phase: np.ndarray, wave: str, duty: float) -> np.ndarray:
    frac = phase % 1.0
    if wave == "square":
        return np.where(frac < duty, 1.0, -1.0)
    if wave == "triangle":
        return 4.0 * np.abs(frac - 0.5) - 1.0
    if wave == "saw":
        return 2.0 * frac - 1.0
    if wave == "sine":
        return np.sin(2 * np.pi * phase)
    raise ValueError(f"unknown wave: {wave}")


def tone(freq: float, dur: float, wave: str = "square", duty: float = 0.5, vol: float = 0.5) -> np.ndarray:
    return (_osc(freq * _t(dur), wave, duty) * vol).astype(np.float32)


def sweep(f0: float, f1: float, dur: float, wave: str = "square", vol: float = 0.5) -> np.ndarray:
    n = len(_t(dur))
    freq = np.linspace(f0, f1, n)
    phase = np.cumsum(freq) / SAMPLE_RATE
    return (_osc(phase, wave, 0.5) * vol).astype(np.float32)


def vibrato(freq: float, dur: float, depth: float, rate: float, wave: str = "sine", vol: float = 0.5) -> np.ndarray:
    t = _t(dur)
    f = freq * (1 + depth * np.sin(2 * np.pi * rate * t))
    phase = np.cumsum(f) / SAMPLE_RATE
    return (_osc(phase, wave, 0.5) * vol).astype(np.float32)


def noise(dur: float, vol: float = 0.5, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng(7)
    return (rng.uniform(-1, 1, len(_t(dur))) * vol).astype(np.float32)


def lowpass(sig: np.ndarray, width: int) -> np.ndarray:
    """Грубый фильтр: скользящее среднее."""
    if width <= 1:
        return sig
    return np.convolve(sig, np.ones(width) / width, mode="same").astype(np.float32)


def silence(dur: float) -> np.ndarray:
    return np.zeros(len(_t(dur)), dtype=np.float32)


def envelope(sig: np.ndarray, a: float, d: float, s: float, r: float) -> np.ndarray:
    n = len(sig)
    env = np.full(n, s, dtype=np.float64)
    na, nd, nr = int(a * SAMPLE_RATE), int(d * SAMPLE_RATE), int(r * SAMPLE_RATE)
    na = min(na, n)
    env[:na] = np.linspace(0, 1, na, endpoint=False)
    nd = min(nd, n - na)
    env[na:na + nd] = np.linspace(1, s, nd, endpoint=False)
    nr = min(nr, n)
    if nr:
        env[n - nr:] = env[n - nr:] * np.linspace(1, 0, nr)
    return (sig * env).astype(np.float32)


def mix(*sigs: np.ndarray) -> np.ndarray:
    n = max(len(s) for s in sigs)
    out = np.zeros(n, dtype=np.float64)
    for s in sigs:
        out[: len(s)] += s
    return np.tanh(out).astype(np.float32)


def concat(*sigs: np.ndarray) -> np.ndarray:
    return np.concatenate(sigs).astype(np.float32)


def notes(seq: list[tuple[float, float]], wave: str = "square", vol: float = 0.4, duty: float = 0.5) -> np.ndarray:
    """Последовательность (частота, длительность); частота 0 — пауза."""
    parts = []
    for freq, dur in seq:
        if freq <= 0:
            parts.append(silence(dur))
        else:
            parts.append(envelope(tone(freq, dur, wave, duty, vol), 0.004, dur * 0.3, 0.6, dur * 0.3))
    return concat(*parts)


def mixer_available() -> bool:
    global _mixer_state
    if _mixer_state is None:
        import pygame

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(SAMPLE_RATE, -16, 2, 512)
            _mixer_state = True
        except pygame.error:
            _mixer_state = False
    return _mixer_state


def to_sound(sig: np.ndarray):
    import pygame

    channels = pygame.mixer.get_init()[2]
    arr = (np.clip(sig, -1, 1) * 32767).astype(np.int16)
    if channels == 2:
        arr = np.column_stack([arr, arr])
    return pygame.sndarray.make_sound(np.ascontiguousarray(arr))
