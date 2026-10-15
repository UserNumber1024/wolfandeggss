"""Сохранение рекордов и настроек в v2/save.json (spec 8)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

SAVE_PATH = Path(__file__).resolve().parent.parent / "save.json"


@dataclass
class SaveData:
    best_score: int = 0
    best_wave: int = 0
    best_streak: int = 0
    music_volume: float = 0.7
    sfx_volume: float = 0.8
    fullscreen: bool = False


def _coerce(name: str, default, value):
    if isinstance(default, bool):
        return value if isinstance(value, bool) else default
    if isinstance(default, int):
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else default
    if isinstance(default, float):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return min(1.0, max(0.0, float(value)))
        return default
    return default


def load(path: Path = SAVE_PATH) -> SaveData:
    data = SaveData()
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return data
    if not isinstance(raw, dict):
        return data
    for f in fields(SaveData):
        if f.name in raw:
            setattr(data, f.name, _coerce(f.name, getattr(data, f.name), raw[f.name]))
    return data


def store(data: SaveData, path: Path = SAVE_PATH) -> None:
    path = Path(path)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(asdict(data), indent=2), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass


def record_result(data: SaveData, score: int, wave: int, streak: int) -> bool:
    new_record = score > data.best_score
    data.best_score = max(data.best_score, score)
    data.best_wave = max(data.best_wave, wave)
    data.best_streak = max(data.best_streak, streak)
    return new_record
