"""Весь текст интерфейса (spec 6)."""

from __future__ import annotations

TITLE = "ВОЛК И ЯЙЦА"
SUBTITLE = "НУ, ПОГОДИ!"
MENU = ("ИГРАТЬ", "НАСТРОЙКИ", "ВЫХОД")
PAUSE = "ПАУЗА"
PAUSE_MENU = ("ПРОДОЛЖИТЬ", "В МЕНЮ")
SETTINGS_TITLE = "НАСТРОЙКИ"
SETTINGS = ("МУЗЫКА", "ЗВУКИ", "ПОЛНЫЙ ЭКРАН", "НАЗАД")
WAVE = "ВОЛНА {n}"
HUD_WAVE = "ЭТАП {s} · ВОЛНА {n}"
STAGE = "ЭТАП {n} · {name}"
GOLD_RUSH = "ЗОЛОТАЯ ЛИХОРАДКА"
HURRICANE = "УРАГАН"
GAME_OVER = "ИГРА ОКОНЧЕНА"
VICTORY = "ПОБЕДА!"
NEW_RECORD = "НОВЫЙ РЕКОРД!"
RESULT_LINES = ("ОЧКИ: {score}", "ВОЛНА: {wave}", "ЛУЧШАЯ СЕРИЯ: {streak}")
HINT_END = "R — ЗАНОВО   ESC — МЕНЮ"
HINT_CONTROLS = "СТРЕЛКИ / WASD   ПРОБЕЛ — ПАУЗА"
BEST = "РЕКОРД: {score}"
SCORE = "{score}"
COMBO = "×{n}"
ON_OFF = ("ВКЛ", "ВЫКЛ")
PERCENT = "{n}%"
LEGEND = {
    "golden": "+{points} ОЧКОВ",
    "heart": "+ЖИЗНЬ",
    "clock": "ЗАМЕДЛЕНИЕ",
    "magnet": "МАГНИТ",
    "silence": "МИНУС КУРЯТНИК",
    "rotten": "НЕ ЛОВИ!",
}


def all_texts() -> list[str]:
    """Все строки с подставленными примерами — для проверки шрифта."""
    out = [TITLE, SUBTITLE, PAUSE, SETTINGS_TITLE, GOLD_RUSH, HURRICANE, GAME_OVER,
           VICTORY, NEW_RECORD, HINT_END, HINT_CONTROLS]
    out += [*MENU, *PAUSE_MENU, *SETTINGS, *ON_OFF]
    out += [WAVE.format(n=20), HUD_WAVE.format(s=4, n=20), BEST.format(score=1234567890), SCORE.format(score=90),
            COMBO.format(n=4), PERCENT.format(n=70)]
    out += [STAGE.format(n=i, name=name) for i, name in enumerate(("ВЕСНА", "ЛЕТО", "ОСЕНЬ", "ЗИМА"), 1)]
    out += [line.format(score=1, wave=2, streak=3) for line in RESULT_LINES]
    out += [label.format(points=5) for label in LEGEND.values()]
    return out
