# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.7] - 2026-07-09

### Added
- **Drawing primitives module** (`src/hideout_art/primitives.py`) — пять
  генераторов фигур, размещающих art-декорации прямо в world-координатах:
  - `line(x0, y0, x1, y1, opts)` — прямая линия;
  - `polyline(points, opts)` — цепочка сегментов (используется S-snake);
  - `hollow_circle(cx, cy, r, opts)` — контур круга;
  - `filled_circle(cx, cy, r, opts)` — круг с заливкой (концентрические
    кольца);
  - `s_snake(cx, cy, height, width, opts)` — вертикальная синусоида;
  - `thick_line_with_contours(x0..y1, thickness, outline_opts, fill_opts)`
    — «стадион» с контуром + заливкой;
  - `center_composition(cx, cy, ...)` — курируемая композиция из всех 5
    фигур, центрированная на (780, 657) в Canal Hideout.
  Все примитивы используют только `ART_TYPES`, соблюдают
  `DECORATION_FOOTPRINT_CATALOG.min_spacing_wu` через `safe_spacing()`,
  возвращают свежий `list[Placement]` (без мутации входного Hideout).
- **`scripts/draw_primitives.py`** — CLI, добавляющий композицию в
  существующий `.hideout`. Строго аддитивный. Опции: `--center X Y`,
  `--bounds-check`, `--preview PATH`, per-primitive `--<shape>-decoration`,
  `--spacing-override`.
- **`scripts/render_primitives_preview.py`** — color-coded PNG preview с
  Canal Hideout canvas outline + легендой по декорациям.
- **37 новых pytest cases** в `tests/test_primitives.py` (geometry,
  spacing validation, center_composition end-to-end, round-trip).
- **Артефакт**: `download/чистый холст с примитивами.hideout` (70
  placements = 18 functional + 52 art).

### Changed
- `__init__.py` — re-exports primitives API. Version 0.2.6 → 0.2.7.
- `pyproject.toml` — version 0.2.6 → 0.2.7.
- `STATUS.md` — KI-13 partial (3/5 узнаваемы в игре), новые KI-14
  (S-snake плохо видна) и KI-15 (thick_line плохо видна). KI-2 и KI-12
  отмечены как wontfix (не критично). Длинная история KI сжата.
- `AGENTS.md` — добавлен `primitives.py` в file map, обновлён test count
  274 → 311, добавлен TL;DR entry для drawing primitives.
- `README.md` — добавлен раздел "Drawing primitives (0.2.7)".
- `CHANGELOG.md` — длинная история 0.2.0-0.2.6 сжата до кратких сводок.

### Known Issues
- **KI-13 (partial 0.2.7)** — Drawing primitives проверены в игре: 3/5
  фигур узнаваемы (vertical lines, hollow circle, filled circle), 2/5
  плохо видны (S-snake, thick_line). См. STATUS.md.
- **KI-14 (new 0.2.7)** — S-snake из Sand Tussock плохо различима.
- **KI-15 (new 0.2.7)** — Thick_line при thickness=14 не видна.
- KI-2, KI-12 — wontfix (low priority, не блокируют).
- KI-10 — open (low priority).

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

[Unreleased]: https://github.com/vudirvp-sketch/poe2-hideout-art/compare/v0.2.7...HEAD
[0.2.7]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.7
[0.2.6]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.6
[0.2.5]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.5
[0.2.4]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.4
[0.2.3]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.3
[0.2.2]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.2
[0.2.1]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.1
[0.2.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.0
[0.1.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.1.0
