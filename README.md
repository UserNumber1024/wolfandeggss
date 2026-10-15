# Волк и яйца

Аркада по мотивам «Ну, погоди!» (Электроника ИМ-02) на Python и pygame:
волк с корзиной ловит яйца, которые скатываются из курятников.

![Волк и яйца v2 — зима](v2/docs/screenshots/winter.png)

## Что в репозитории

| Папка | Что это |
|---|---|
| [`v2/`](v2/README.md) | Основная версия: 20 волн в четырёх сезонах, спецяйца, комбо, заяц, нарисованный кодом пиксель-арт, своя музыка на каждую волну |
| [`v1/`](v1/README.md) | Исходная простая версия (один файл и три картинки) — сохранена как есть для сравнения |

## Быстрый старт (Windows)

1. Установите **Python 3.10 или новее** с [python.org](https://www.python.org/downloads/)
   (в установщике отметьте *Add python.exe to PATH*) или командой:
   ```powershell
   winget install Python.Python.3.13
   ```
2. Скачайте репозиторий (*Code → Download ZIP*) или клонируйте:
   ```powershell
   git clone https://github.com/UserNumber1024/wolfandeggss.git
   cd wolfandeggss
   ```
3. Установите зависимости и запустите v2:
   ```powershell
   py -m pip install -r v2\requirements.txt
   py v2\main.py
   ```

Подробности, управление и решение проблем — в [`v2/README.md`](v2/README.md).

На Linux и macOS игра тоже должна работать (pygame и numpy кроссплатформенные),
но проверялась только на Windows 11.
