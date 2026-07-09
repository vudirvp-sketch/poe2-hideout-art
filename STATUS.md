# STATUS.md

Текущее состояние проекта `poe2-hideout-art`. Короткая живая памятка для
агента/человека: что работает, что сломано, что делать дальше. Длинную
историю изменений не ведём — для этого есть `CHANGELOG.md`.

## Что работает (проверено 2026-07-10, версия 0.3.0)

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
- **Drawing primitives (0.3.0)** — модуль `src/hideout_art/primitives.py`
  + `scripts/draw_primitives.py`. Все примитивы доступны, но в
  `download/чистый холст clean.hideout` (0.3.0) лежит только
  `clean_composition` — 7 простейших контуров и заливок по одной
  декорации на фигуру.
  - **Core (0.2.7)**: `line`, `polyline`, `hollow_circle`, `filled_circle`,
    `s_snake`, `thick_line_with_contours`, + курируемая `center_composition`.
  - **Mosaic/bas-relief (0.2.8)**: `arc`, `rectangle`, `polygon`, `grid`.
  - **Mosaic v2 / portrait-grade (0.2.9, ЗАМОРОЖЕНО — см. KI-17)**:
    `bezier_curve`, `thick_ring`, `thick_arc`, `crosshatch`,
    + курируемая `mosaic_composition`. Код и тесты остаются, но в
    канонический `.hideout` больше НЕ добавляются.
  - **Clean composition (0.3.0, NEW)**: `clean_composition` — 7 фигур
    (`hollow_circle`, `filled_circle`, `rectangle`, `polygon` ×2,
    `arc`, `grid`), каждая использует ОДНУ декорацию (Long Grass или
    Maraket Rubble — самые плотные, sp≈13.3..13.6 wu), без смешивания
    outline+fill внутри одной фигуры. Лёгкий чистый тестовый стенд для
    визуальной проверки базовых примитивов в игре.
- **Визуальная проверка в игре (0.2.7)** — 3/5 фигур узнаваемы. KI-14/15
  зафиксены в 0.2.8 — ожидается повторная проверка (5/5) от пользователя.
  0.2.9 mosaic v2 примитивы — НЕ проверены в игре (см. KI-17).
  0.3.0 clean_composition — НЕ проверена в игре, ждёт visual-verify
  от пользователя (см. KI-18).
- Тесты: **369 pass, 1 skipped** (7 новых в `tests/test_primitives.py`
  для `clean_composition`).
- **Рецепт портрета** — `docs/mosaic_recipe.md`: фиксирует концепцию
  «Портрет из артефактов и природы» + рейтинг декораций по назначению.

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
| KI-16 | superseded 0.3.0 | —     | Mosaic v2 не проверены в игре. Перекрыт KI-17 — откат к чистым примитивам. |
| KI-17 | open 0.3.0   | high      | v0.2.9 mosaic v2 (bezier/thick_ring/thick_arc/crosshatch) дают визуальный «мусор» на холсте. |
| KI-18 | open 0.3.0   | high      | `clean_composition` (0.3.0) не проверена в игре — ждёт visual-verify. |

### KI-17 (open 0.3.0) — v0.2.9 mosaic v2 даёт визуальный мусор

Пользователь импортировал `download/чистый холст с примитивами.hideout`
(v0.2.9, 165 placements: 30 functional/boundary + 63 core + 72 mosaic v2)
в PoE2. Скриншот показал, что фигуры на полу не опознаются — смесь
`outline_opts` + `fill_opts` внутри `thick_ring` / `thick_arc`, плотный
`crosshatch` (Seaweed) и `bezier_curve` (Small Coastal Stone) сливаются
в шумное пятно. KI-16 «не проверены в игре» перекрыт этим KI-17 —
проверка состоялась, результат негативный.

**Решение (0.3.0):** откат к «самым тонким и простым» элементам.
Новый `clean_composition` использует ТОЛЬКО single-decoration контуры
и заливки (`hollow_circle`, `filled_circle`, `rectangle`, `polygon`,
`arc`, `grid`) с Long Grass / Maraket Rubble (sp≈13.3..13.6 — самые
плотные из каталога). Без `bezier_curve`, `thick_ring`, `thick_arc`,
`crosshatch`, `s_snake`, `thick_line_with_contours`. Код mosaic v2
остаётся в `primitives.py` (тесты проходят), но в канонический
`.hideout` не добавляется.

### KI-18 (open 0.3.0) — clean_composition не проверена в игре

`download/чистый холст clean.hideout` (0.3.0, 7 чистых фигур) ждёт
импорта в PoE2 и скриншота. Ожидаем: 7/7 узнаваемых простых контуров
и заливок. Если хотя бы 5/7 — закрываем KI-18 и переходим к портрету.
Если <5/7 — заводим KI-19 с конкретной фигурой.

### KI-16 (superseded 0.3.0) — Mosaic v2 не проверены в игре

Перекрыт KI-17: проверка состоялась (негативный результат). Код
сохранён для будущей доработки, но в поставку не входит.

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

1. **Visual-verify 0.3.0 clean_composition.** Пользователь импортирует
   `download/чистый холст clean.hideout` в PoE2, делает скриншот.
   Ожидаем: 7/7 узнаваемых простых контуров и заливок. Если ≥5/7 —
   KI-18 закрывается, переходим к портрету. Если <5/7 — KI-19 с
   конкретной фигурой.
2. **Композиция портрета** (после закрытия KI-18). Собрать портрет из
   чистых примитивов: `hollow_circle` (контур лица), `filled_circle`
   (глаза), `arc` (улыбка), `polygon` (нос), `grid` (борода/тень).
   Без `bezier_curve` / `thick_ring` / `crosshatch` до тех пор, пока
   они не будут визуально верифицированы отдельно. Новый скрипт
   `scripts/draw_portrait.py`.
3. **Multi-pass img2hideout: outline + fill.** Двухпроходной рендер
   фотографий: первый проход — контуры (Long Grass), второй — fill
   (Maraket Rubble). Реализуется в `img2hideout.py` через
   `outline_color` + `outline_step` параметры.
4. **Sprite bounds (KI-10).** Расширить `DECORATION_FOOTPRINT_CATALOG`
   полем `sprite_bounds_wu` отдельно от placement footprint.
5. **Drawing primitives v4.** `bezier_cubic` (кубическая Безье с 2
   control points), `text` (через bitmap font), `concentric_rings`.
   ТОЛЬКО после закрытия KI-18 — не плодить новые непроверенные фигуры.
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
9. **Чистые примитивы первичны (0.3.0+).** В канонический `.hideout`
   идут только single-decoration контуры и заливки. `bezier_curve` /
   `thick_ring` / `thick_arc` / `crosshatch` / `s_snake` /
   `thick_line_with_contours` остаются в коде, но НЕ в поставке, пока
   каждая фигура по отдельности не верифицирована в игре.
