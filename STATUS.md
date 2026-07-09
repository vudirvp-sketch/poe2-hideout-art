# STATUS.md

Текущее состояние проекта `poe2-hideout-art`. Короткая живая памятка для
агента/человека: что работает, что сломано, что делать дальше. Длинную
историю изменений не ведём — для этого есть `CHANGELOG.md`.

## Что работает (проверено 2026-07-10, версия 0.2.9)

- Парсер `.hideout` (толерантный, регэксп, сохраняет дубликаты ключей).
- Врайтер (байт-совместимый, дубликаты ключей сохраняет).
- Геометрические трансформации: `shift`, `rotate`, `mirror_x`, `mirror_y`,
  `recombine`.
- Превью в PNG (matplotlib, по одной точке на размещение).
- Конвейер `img2hideout` (alpha-канал, 3 цветовых метрики, Floyd-Steinberg
  dithering, jitter, `step`/`tile_size`, `bounds`, `resample`, `--preview`).
- CLI: `inspect`, `layers`, `stats`, `preview`, `shift`, `transfer`,
  `img2hideout`.
- Каталог хешей: **47 известных декораций** (11 functional + 8 NPC +
  28 art). `DECORATION_FOOTPRINT_CATALOG` покрывает все 28 art-декораций.
- Pixel-sampling (`scripts/sample_pixels.py`) — ground-truth RGB для 25
  из 28 art-декораций.
- **Drawing primitives (0.2.9)** — модуль `src/hideout_art/primitives.py`
  + `scripts/draw_primitives.py`. **13 базовых фигур**:
  - **Core (0.2.7)**: `line`, `polyline`, `hollow_circle`, `filled_circle`,
    `s_snake`, `thick_line_with_contours`, + курируемая `center_composition`.
  - **Mosaic/bas-relief (0.2.8)**: `arc`, `rectangle`, `polygon`, `grid`.
  - **Mosaic v2 / portrait-grade (0.2.9, NEW)**: `bezier_curve`,
    `thick_ring`, `thick_arc`, `crosshatch`, + курируемая
    `mosaic_composition` (демонстрация в свободной зоне холста, НЕ
    трогает `center_composition` — KI-14/15 re-verify остаётся чистым).
- **Визуальная проверка в игре (0.2.7)** — 3/5 фигур узнаваемы. KI-14/15
  зафиксены в 0.2.8 — ожидается повторная проверка (5/5) от пользователя.
  0.2.9 mosaic v2 примитивы — НЕ проверены в игре, ждут отдельной
  визуальной проверки.
- Тесты: **362 pass, 1 skipped** (30 новых в `tests/test_primitives.py`
  для bezier/thick_ring/thick_arc/crosshatch/mosaic_composition).
- **Рецепт портрета** — `docs/mosaic_recipe.md`: емко фиксирует концепцию
  «Портрет из артефактов и природы» + рейтинг декораций по назначению
  (контур/точки vs заполнение/фон).

## Известные проблемы (Known Issues)

Все ранее задокументированные KI-1..KI-12 закрыты или low-priority.
Активные:

| KI  | Статус        | Приоритет | Что                                                                |
|-----|---------------|-----------|--------------------------------------------------------------------|
| KI-2 | wontfix 0.2.7 | low       | Skin-роль. Решено: точное попадание в RGB не нужно, главное — различимость. |
| KI-10 | open 0.2.3   | low       | Каталог измеряет placement footprint, не sprite bounds.            |
| KI-12 | wontfix 0.2.7 | low      | Marble-серия pixel-sampling даёт brown вместо gray.                |
| KI-13 | closed 0.2.8  | —        | Drawing primitives: 3/5 узнаваемы в 0.2.7. KI-14/15 фикс в 0.2.8 закрыл пробел. Ожидает повторной проверки. |
| KI-14 | fixed 0.2.8   | —        | S-snake: Sand Tussock → Maraket Rubble (плотнее + контрастнее). |
| KI-15 | fixed 0.2.8   | —        | Thick_line: thickness 14 → 28, fill Coastal Pebble → Long Grass. |
| KI-16 | open 0.2.9   | medium   | Mosaic v2 примитивы (bezier/ring/arc/hatch) не проверены в игре. Ожидается visual-verify после импорта `download/чистый холст с примитивами.hideout`. |

### KI-16 (open 0.2.9) — Mosaic v2 не проверены в игре

4 новых примитива 0.2.9 (`bezier_curve`, `thick_ring`, `thick_arc`,
`crosshatch`) и `mosaic_composition` добавлены в код и тесты (30 cases),
но НЕ прошли визуальную проверку в PoE2. Возможные проблемы:
- `crosshatch` использует Liang-Barsky clipping — может давать пустые
  зоны при очень острых углах + мелком прямоугольнике.
- `thick_ring` с узкой полосой (outer_r - inner_r < spacing) требует
  `spacing_override` — иначе fill не генерируется (см. фикс в
  `mosaic_composition` где spacing=3.0 для ring band=7 wu).
- `thick_arc` fill может быть редким при большой толщине и малом радиусе.

**Действие:** пользователь импортирует `download/чистый холст с примитивами.hideout`
(165 placements = 30 functional/boundary + 63 core + 72 mosaic v2),
делает скриншот нижней зоны холста. Если 4 новых фигуры узнаваемы —
KI-16 закрывается. Если нет — заводим KI-17+ с конкретной фигурой.

### KI-10 (open 0.2.3, low) — placement vs sprite bounds

`DECORATION_FOOTPRINT_CATALOG` измеряет **placement footprint** (upper
bound на основе min pairwise distance), не реальные sprite bounds. Для
step-калибровки `img2hideout` достаточно; для визуального перекрытия
нужны внутриигровые замеры sprite. **Низкий приоритет.**

### KI-2 (wontfix 0.2.7) — skin-роль в палитре 2B

Решено: точное попадание в RGB (228,200,178) не нужно. Главное —
различимость фигур на полу. Если понадобится тёплый accent — использовать
`Maraket Treasures` (gold) или `Maraket Samovar` (copper).

### KI-12 (wontfix 0.2.7) — Marble-серия pixel-sampling

Pixel sampling показал brown (76-110) вместо ожидаемого light gray
(210-230) для Marble Bench/Walls/Fountain. Причина: sampling window
попадает на тень под объектом. **Не критично** — при переходе на другие
убежища проблема уйдёт.

## Что улучшать дальше (приоритеты следующей итерации)

1. **Повторная визуальная проверка 0.2.8 + 0.2.9.** Пользователь
   импортирует `download/чистый холст с примитивами.hideout` в PoE2,
   делает скриншоты. Ожидаем 5/5 узнаваемых core + 4/4 mosaic v2.
   Если нет — завести KI-17 с конкретной фигурой.
2. **Композиция портрета.** После visual-verify 0.2.9: использовать
   `bezier_curve` (улыбка), `thick_ring` (очки-линзы), `thick_arc`
   (дужка очков), `crosshatch` (борода) для сборки портрета по рецепту
   из `docs/mosaic_recipe.md`. Новый скрипт `scripts/draw_portrait.py`.
3. **Multi-pass img2hideout: outline + fill.** Реализуется в
   `img2hideout.py` через `outline_color` + двухпроходной рендер. Готовый
   паттерн — `thick_line_with_contours` в `primitives.py`.
4. **Sprite bounds (KI-10).** Расширить `DECORATION_FOOTPRINT_CATALOG`
   полем `sprite_bounds_wu` отдельно от placement footprint.
5. **Drawing primitives v4.** После визуальной проверки 0.2.9: добавить
   `bezier_cubic` (cubic Bezier с 2 control points), `text` (через
   bitmap font), `concentric_rings` (множество колец).
6. **Поддержка нескольких убежищ.** Сейчас `NAMED_BOUNDS` содержит только
   `canal`. Добавлять новые по мере появления экспортов.

## Базовые принципы при правках

1. **Сначала в STATUS.md, потом фикс.** Новый баг → новый KI-N → потом код.
2. **Никогда не ломать существующие тесты.** Все новые опции — opt-in.
3. **Никогда не выдумывать хеши.** Нет в `KNOWN_HASHES` → помечаем unknown.
4. **RGB-значения — с указанием источника и даты.** `VLM <version>, <date>`
   или `PIXEL <version>, <date>`. При конфликте доверять PIXEL.
5. **Документация короткая.** Этот файл — не больше 130 строк.
6. **Каталог размеров — sync с исходниками.** При добавлении размещений
   в `исходники/` перезапускать `scripts/measure_decorations.py` и
   обновлять `DECORATION_FOOTPRINT_CATALOG`.
7. **Drawing primitives — только ART_TYPES.** Никогда не использовать
   functional-объекты в примитивах (см. `safe_spacing` в `primitives.py`).
8. **Точное попадание в RGB — НЕ нужно.** Главное — различимость фигур
   на полу.
9. **Новые примитивы — в отдельных зонах холста.** Не смешивать с
   `center_composition` пока старые фигуры не прошли re-verify (см.
   `mosaic_composition` 0.2.9 — отдельная зона снизу).
