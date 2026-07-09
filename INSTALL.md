# poe2-hideout-art — patch 0.2.8

Версия: **0.2.8** (supersedes 0.2.7)
Дата: 2026-07-10
Тема: KI-14/15 fix + 4 new mosaic/bas-relief primitives

## Что в архиве

Архив содержит **только изменённые/новые файлы**. Структура папок повторяет
репозиторий — распакуйте поверх локальной копии репозитория, затем
`git add -A && git commit && git push`.

```
poe2-hideout-art-0.2.8/
├── AGENTS.md                              # обновлён (file map + test count 311→333)
├── CHANGELOG.md                           # добавлена запись 0.2.8
├── README.md                              # раздел primitives обновлён (5→9 фигур)
├── STATUS.md                              # KI-13/14/15 закрыты, добавлены fix-секции
├── pyproject.toml                         # version 0.2.7 → 0.2.8
├── scripts/
│   ├── README.md                          # обновлён под 0.2.8 (defaults + mosaic table)
│   └── draw_primitives.py                 # CLI defaults синхронизированы (KI-14/15)
├── src/hideout_art/
│   ├── __init__.py                        # re-exports arc/rectangle/polygon/grid, v0.2.8
│   └── primitives.py                      # +4 новых примитива, KI-14/15 fix в center_composition
├── tests/
│   └── test_primitives.py                 # +22 новых pytest cases (arc/rect/poly/grid + KI-14/15 regression)
└── download/                              # НЕ для репозитория — артефакты для импорта в игру
    ├── чистый холст с примитивами.hideout  # 93 placements (30 canvas + 63 art)
    ├── чистый холст с примитивами.preview.png
    └── чистый холст с примитивами.colored.png
```

## Кратко об изменениях

### Фиксы KI-14, KI-15 (high priority)

| What | Before (0.2.7) | After (0.2.8) |
|------|----------------|---------------|
| S-snake decorator | `Sand Tussock` (sp=17.1, sparse) | `Maraket Rubble` (sp=13.6, denser + contrast) |
| Thick line thickness | `14` (1 fill row, invisible) | `28` (2 fill rows) |
| Thick line fill | `Coastal Pebble` (sp=29.7) | `Long Grass` (sp=13.3, visible per KI-13) |

### Новые примитивы (0.2.8) — Python API only

- `arc(cx, cy, radius, start_angle_deg, end_angle_deg, opts)` — дуга окружности
- `rectangle(x0, y0, x1, y1, opts)` — полый прямоугольник
- `polygon(cx, cy, radius, n_sides, opts, rotation_deg=0)` — n-угольник (3+, по умолчанию rotation_deg=0)
- `grid(x0, y0, x1, y1, opts, cols, rows, include_border=True)` — сетка cols×rows

CLI `draw_primitives.py` пока использует только core 5 фигур (S-snake, thick_line
с новыми defaults). Мозаичные примитивы вызываются из Python напрямую.

### Тесты

- Before: 310 pass, 1 skipped
- After:  **332 pass, 1 skipped** (+22 new)
- Lint: ruff clean
- Все regression-тесты (KI-14, KI-15) зелёные

## Как применить

1. Распакуйте архив поверх локальной копии репозитория:
   ```bash
   unzip poe2-hideout-art-0.2.8.zip -d /path/to/poe2-hideout-art/
   ```
2. Файлы из `download/` — это артефакты для импорта в игру, не для репозитория.
   Они уже лежат в правильной папке, если у вас есть `download/` в проекте.
3. Проверьте, что тесты проходят:
   ```bash
   pip install -e ".[dev]"
   pytest -q
   ```
   Ожидаемый результат: `332 passed, 1 skipped`.
4. Закоммитьте и запушьте:
   ```bash
   git add -A
   git commit -m "0.2.8: KI-14/15 fix + 4 mosaic/bas-relief primitives"
   git push origin main
   ```

## Точка остановки

См. `STATUS.md` → «Что улучшать дальше» в корне репозитория после применения
патча. Кратко:

1. **Повторная визуальная проверка 0.2.8** — пользователь импортирует
   `download/чистый холст с примитивами.hideout` в PoE2, делает скриншоты.
   Цель: 5/5 узнаваемых фигур.
2. Multi-pass img2hideout (outline + fill) — не начат.
3. Расширить `center_composition` демонстрацией новых mosaic-примитивов
   (hexagon + arc + 3×3 grid) — не начат.
4. Sprite bounds (KI-10) — не начат.
