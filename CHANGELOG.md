# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-07-10

### Added
- **`clean_composition(center_x, center_y, *, contour_decoration="Long Grass",
  fill_decoration="Maraket Rubble", spacing_override=None)`** в
  `src/hideout_art/primitives.py` — KI-17 response. 7 простейших
  single-decoration контуров и заливок:
  - Row 1 (контуры, Long Grass, sp≈13.3 wu): `hollow_circle` r=14,
    `rectangle` 24×24, `polygon` (triangle) r=14, `arc` (полукруг) r=12.
  - Row 2 (заливки, Maraket Rubble, sp≈13.6 wu): `filled_circle` r=10,
    `polygon` (hexagon) r=12, `grid` 3×3 в окне 30×30.
  - Каждая фигура использует РОВНО ОДНУ декорацию — без смешивания
    outline+fill внутри одной формы (в отличие от 0.2.9 `thick_ring` /
    `thick_arc`).
  - 35 placements всего (19 contour + 16 fill). Помещается в Canal
    Hideout bounds (700, 540, 860, 775) при center (780, 657).
- **CLI флаг `--clean`** в `scripts/draw_primitives.py` — генерирует
  ТОЛЬКО `clean_composition` (без `center_composition`, без
  `mosaic_composition`). Per-shape decoration overrides:
  `--contour-decoration`, `--fill-decoration`. `--clean` и
  `--with-mosaic` взаимоисключающие.
- **9 новых pytest cases** в `tests/test_primitives.py`:
  `TestCleanComposition` —
  `test_uses_only_known_art_decorations`,
  `test_uses_exactly_two_decorations_by_default`,
  `test_all_placements_within_canal_hideout_bounds`,
  `test_no_duplicate_placements_per_decoration`,
  `test_default_produces_35_placements`,
  `test_row1_and_row2_do_not_overlap`,
  `test_no_exotic_primitives_used`,
  `test_round_trip_through_hideout`,
  `test_respects_custom_decorations`.
- **Артефакт**: `download/чистый холст clean.hideout` (65 placements =
  30 functional/boundary + 35 clean). Превью:
  `download/чистый холст clean.{preview,colored}.png`.
- **Исходник**: `download/чистый холст.hideout` (30 placements — только
  functional + NPC + 11 Cordilina boundary + Petrified Cave Figure).
  Получен вычиткой v0.2.9 файла и удалением всех art placements.

### Changed
- `__init__.py` — re-exports `clean_composition`. Version 0.2.9 → 0.3.0.
- `pyproject.toml` — version 0.2.9 → 0.3.0.

### Known Issues
- **KI-17 (open 0.3.0)** — v0.2.9 mosaic v2 (bezier/thick_ring/thick_arc/
  crosshatch) дают визуальный «мусор» на холсте. Смесь outline_opts +
  fill_opts, плотный crosshatch и bezier_curve сливаются в шумное пятно.
  Решение 0.3.0: откат к single-decoration контурам и заливкам
  (`clean_composition`). Код 0.2.9 остаётся в `primitives.py`
  (тесты проходят), но в канонический `.hideout` не добавляется.
- **KI-18 (open 0.3.0)** — `clean_composition` не проверена в игре.
  `download/чистый холст clean.hideout` ждёт visual-verify от
  пользователя. Ожидаем 7/7 узнаваемых простых контуров и заливок.
- **KI-16 (superseded 0.3.0)** — Mosaic v2 не проверены в игре.
  Перекрыт KI-17: проверка состоялась (негативный результат).

## [0.2.9] - 2026-07-10

### Added
- **4 mosaic v2 / portrait-grade primitives** в
  `src/hideout_art/primitives.py`:
  - `bezier_curve(p0, p1, p2, opts, *, spacing=None)` — квадратичная
    кривая Безье (органические кривые: улыбки, брови, контур пальца,
    плечи). Сэмплирование по approximate arc length (32 fine sub-segments).
  - `thick_ring(cx, cy, inner_r, outer_r, outline_opts, fill_opts, *,
    spacing=None)` — кольцо с outline + fill (очки-линзы, глаза,
    декоративные рамки, нимбы). inner_r=0 деградирует в filled_circle
    с outline.
  - `thick_arc(cx, cy, radius, thickness, start_angle_deg, end_angle_deg,
    outline_opts, fill_opts, *, spacing=None)` — толстая дуга с outline
    + fill (дужки очков, скобки, улыбка с толщиной, арки). Две arc
    outlines + две radial caps + fill spokes.
  - `crosshatch(x0, y0, x1, y1, opts, *, spacing=None, angle_deg=45,
    bidirectional=True)` — диагональная крестовая штриховка (борода,
    волосы, тени, текстуры). Liang-Barsky clipping к прямоугольнику.
- **`mosaic_composition(center_x, center_y, ...)`** — курируемая
  демонстрация 4 новых примитивов в отдельной зоне холста (снизу от
  `center_composition`, не перекрывает её — KI-14/15 re-verify остаётся
  чистым). Defaults: Small Coastal Stone (контур), Cave Coral (ring fill),
  Long Grass (arc fill), Seaweed (hatch).
- **`docs/mosaic_recipe.md`** — емкий рецепт портрета: концепция
  «Портрет из артефактов и природы», decoration-to-role mapping, рейтинг
  декораций по назначению (контур/точки vs заполнение/фон), псевдокод
  для 0.2.9 примитивов.
- **30 новых pytest cases** в `tests/test_primitives.py`: TestBezierCurve
  (6), TestThickRing (6), TestThickArc (5), TestCrosshatch (7),
  TestMosaicComposition (6).
- **CLI флаг `--with-mosaic`** в `scripts/draw_primitives.py` —
  опционально добавляет mosaic v2 композицию. Per-shape decoration
  overrides: `--bezier-decoration`, `--ring-outline-decoration`,
  `--ring-fill-decoration`, `--arc-outline-decoration`,
  `--arc-fill-decoration`, `--hatch-decoration`.
- **Артефакт**: `download/чистый холст с примитивами.hideout` (165
  placements = 30 functional/boundary + 63 core + 72 mosaic v2).
- **Превью**: `download/чистый холст с примитивами.{preview,colored}.png`.

### Changed
- `__init__.py` — re-exports bezier_curve/thick_ring/thick_arc/crosshatch/
  mosaic_composition. Version 0.2.8 → 0.2.9.
- `pyproject.toml` — version 0.2.8 → 0.2.9.

### Known Issues
- **KI-16 (open 0.2.9)** — Mosaic v2 примитивы (bezier/ring/arc/hatch)
  не проверены в игре. Ожидается visual-verify после импорта
  `download/чистый холст с примитивами.hideout`.

## [0.2.8] - 2026-07-10

### Added
- **4 mosaic / bas-relief primitives** в `src/hideout_art/primitives.py`:
  - `arc(cx, cy, radius, start_angle_deg, end_angle_deg, opts)` — дуга
    окружности (арки, рамки, полукруглые углы);
  - `rectangle(x0, y0, x1, y1, opts)` — полый прямоугольник (бордюры,
    рамки);
  - `polygon(cx, cy, radius, n_sides, opts, rotation_deg=0)` —
    правильный n-угольник (треугольник, квадрат, пятиугольник,
    шестиугольник… — базовые тайлы мозаики);
  - `grid(x0, y0, x1, y1, opts, cols, rows, include_border=True)` —
    регулярная сетка cols×rows (мозаичные тайлы, пуантилизм, bas-relief
    текстуры). Все 4 примитива — pure stdlib, используют `safe_spacing`
    и `_make_placement`, не вводят новых декораций.
- **22 новых pytest cases** в `tests/test_primitives.py`: TestArc (5),
  TestRectangle (4), TestPolygon (5), TestGrid (6), + 2 regression-теста
  для KI-14/KI-15 (`test_ki14_s_snake_uses_maraket_rubble`,
  `test_ki15_thick_line_fill_uses_long_grass`).

### Changed — KI-14 fix
- `center_composition` default `s_snake_decoration`: `"Sand Tussock"` →
  `"Maraket Rubble"`. Maraket Rubble имеет min_spacing=13.6 (на 21%
  плотнее, чем Sand Tussock 17.1) и нейтрально-коричневый RGB (125,112,87)
  против тёмной оливы Sand Tussock (112,99,79) — выше контраст на tan-полу.
- `scripts/draw_primitives.py` CLI default `--s-snake-decoration`
  синхронизирован.

### Changed — KI-15 fix
- `center_composition` default `thick_fill_decoration`: `"Coastal Pebble"`
  → `"Long Grass"`. Long Grass виден на полу (KI-13 vertical lines),
  min_spacing=13.3 (плотнее, чем Coastal Pebble 29.7).
- `thick_line_with_contours` в `center_composition`: `thickness=14` →
  `thickness=28`. При sp=13.3 теперь 2 ряда заливки (был ≤1).
- `scripts/draw_primitives.py` CLI default `--thick-fill-decoration`
  синхронизирован.

### Closed
- **KI-13 (closed 0.2.8)** — Drawing primitives: 3/5 узнаваемы в 0.2.7.
  Корневые причины (S-snake sparse, thick_line thin) устранены в 0.2.8.
  Ожидает повторной визуальной проверки пользователем.
- **KI-14 (fixed 0.2.8)** — S-snake плохо различима.
- **KI-15 (fixed 0.2.8)** — Thick_line stadium не видна.

## [0.2.7] - 2026-07-09 — кратко

Drawing primitives module (`src/hideout_art/primitives.py`) — 5 базовых
фигур (`line`, `polyline`, `hollow_circle`, `filled_circle`, `s_snake`,
`thick_line_with_contours`) + `center_composition`. `scripts/draw_primitives.py`
CLI. 37 новых pytest cases. Визуальная проверка в игре: 3/5 узнаваемы →
KI-13 (partial), KI-14 (S-snake), KI-15 (thick_line) заведены. KI-2/KI-12
помечены wontfix. Фикс KI-14/15 — в 0.2.8.

## [0.2.6] - 2026-07-09 — кратко

Pixel-sampling tool (`scripts/sample_pixels.py` + `sample_all.py`) для
ground-truth RGB. Закрыт KI-11 (VLM-noise): Sand Tussock реальный RGB
(112,99,79), Maraket Rubble — neutral brown (125,112,87), не reddish.
Новый KI-12 (Marble-серия: pixel sampling даёт brown вместо gray — sampling
window попадает на тень). 19 новых тестов в `test_sample_pixels.py`.

## [0.2.5] - 2026-07-09 — кратко

Добавлена Seaweed (hash=1015947674) из `водоросли и лентающий песок.hideout`.
2 из 3 TODO в `palette_2b.json` закрыты: `black` → Small Coastal Stone,
`red` → Maraket Rubble. VLM re-analysis 3 скриншотов. 12 новых тестов.
Новый KI-11 (VLM RGB шумит — Sand Tussock 100+ point swing между 0.2.1 и
0.2.5).

## [0.2.4] - 2026-07-09 — кратко

VLM-measured RGB для Marble-серии (`palette_2b.json` частично заполнен:
white/silver/gray/gray-alt). Cave Fossil исправлен с "light gray" на
BROWN (140,110,80). 5 новых тестов.

## [0.2.3] - 2026-07-09 — кратко

`DECORATION_FOOTPRINT_CATALOG` в `constants.py` — placement footprint
для всех 27 art-декораций с confidence levels. `scripts/measure_decorations.py`
для re-derivation. 94 новых теста в `test_footprints.py`. Новый KI-10
(placement vs sprite bounds).

## [0.2.2] - 2026-07-09 — кратко

18 новых хешей из `исходники/*.hideout` (Cordilina, Marble-серия, Cave
Fossil/Coral, Summit Brazier и др.). `CANAL_HIDEOUT_BOUNDS` + `--bounds
canal` CLI shortcut. 70 новых тестов.

## [0.2.1] - 2026-07-09 — кратко

5 warm-tone Maraket/Coastal Pebble хешей. `examples/palette_warm.json`
(9-color palette). `tile_size` параметр (closes KI-1). KI-9 fix:
`Placement.is_art` resolves via hash, not name. 26 новых тестов.

## [0.2.0] - 2026-07-09 — кратко

`img2hideout` overhaul: alpha-channel, 3 colour-distance metrics,
Floyd-Steinberg dithering, jitter, `step`, `bounds`, `resample`, `--preview`.
`examples/palette_2b.json` template. `docs/img2hideout.md`. 11 новых тестов.

## [0.1.0] - 2026-07-09

Initial release: tolerant regex parser, `Hideout`/`Placement` dataclasses,
geometric transforms, header rewriter, PNG preview, `img2hideout`, CLI
(`inspect`/`layers`/`stats`/`preview`/`shift`/`transfer`/`img2hideout`),
23 known hashes, docs, 33 pytest tests.

[Unreleased]: https://github.com/vudirvp-sketch/poe2-hideout-art/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.3.0
[0.2.9]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.9
[0.2.8]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.8
[0.2.7]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.7
[0.2.6]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.6
[0.2.5]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.5
[0.2.4]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.4
[0.2.3]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.3
[0.2.2]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.2
[0.2.1]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.1
[0.2.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.0
[0.1.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.1.0
