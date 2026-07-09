# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.4] - 2026-07-09

### Added
- **VLM-measured RGB for cold-tone decorations.** Used the `VLM` skill
  (glm-4.6v) to analyze the `исходники/еще элементы.jpg` screenshot
  (which contains Marble Bench/Table/Walls/Fountain + Cave Fossil +
  Cave Coral + Summit Brazier placements). Identified each decoration
  visually and reported mid-tone RGB values.
- **`palette_2b.json` partial fill.** Replaced 3 of 6 TODO placeholders
  with VLM-measured Marble-серия entries:
  - `white`  role → Marble Fountain (230, 230, 220) — brightest marble
  - `silver` role → Marble Table    (200, 200, 195) — mid light gray
  - `gray`   role → Marble Bench    (210, 210, 205) — light cool gray
  - `gray` alt → Marble Walls       (210, 210, 205) — near-twin of Bench
- **New metadata block** in `palette_2b.json`: `_rgb_sources` (method
  description + per-decoration RGB attribution), `_0_2_4_measured_rgb_summary`
  (compact table of measured values and qualitative findings).
- **5 new pytest tests** in `tests/test_new_hashes.py`:
  - `test_palette_2b_still_has_todos` (updated) — now expects 3 TODOs
    (black/skin/red), down from 6.
  - `test_palette_2b_uses_marble_series` — verifies Marble Fountain/
    Table/Bench/Walls are in the palette.
  - `test_palette_2b_marble_rgb_values` — regression protection for
    the VLM-measured RGB values.
  - `test_palette_2b_marble_entries_resolve_to_known_hashes` —
    catches typos in decoration names.
  - `test_palette_2b_marble_only_section_loads_via_palette_class` —
    proves that the Marble-серия entries alone form a valid Palette
    (only the 3 remaining TODOs keep palette_2b.json from loading).
- Total test count: **237** (236 pass, 1 skipped).

### Changed
- `src/hideout_art/constants.py` — comments for Cave Fossil/Cave Coral/
  Summit Brazier/Marble Bench/Table/Walls/Fountain updated with VLM-
  measured RGB values. Cave Fossil comment corrected from "light
  gray/white ammonite-like" to "BROWN rock (140,110,80)" — the prior
  0.2.2 guess was wrong.
- `STATUS.md` — KI-2 status updated to "partial 0.2.4" with a full
  RGB-measurement table; "Что улучшать дальше" trimmed; new principle
  added: "RGB-значения — с указанием источника".
- `AGENTS.md` — note added about the VLM-measured RGB source for the
  Marble-серия and the corrected Cave Fossil colour.
- `docs/img2hideout.md` — palette_2b.json section updated: 3 of 6 TODOs
  filled, 3 remain (black/skin/red); new "VLM-измеренные RGB" subsection.
- `examples/palette_2b.json` — see Added section above.
- Version bumped to `0.2.4` in `pyproject.toml` and `__init__.py`.

### Fixed
- **Cave Fossil colour correction (qualitative).** Prior 0.2.2 comment
  in `constants.py` guessed Cave Fossil as "light gray/white ammonite-
  like" — VLM analysis of the screenshot revealed it is actually BROWN
  (140,110,80), a warm rock. This means Cave Fossil is NOT a candidate
  for the 2B cool palette (was listed as a candidate in 0.2.2). The
  `_0_2_2_candidates_needing_rgb_sampling` block in `palette_2b.json`
  was effectively superseded by the new `_0_2_4_measured_rgb_summary`
  block, which records the correction.

### Known Issues (no change in 0.2.4)
- KI-2 is now **partial 0.2.4** (was partial 0.2.2): 3 of 6 TODOs filled,
  3 remain (black/skin/red).
- KI-10 is unchanged: catalog measures placement footprint, not sprite
  bounds.

## [0.2.3] - 2026-07-09

### Added
- **`DECORATION_FOOTPRINT_CATALOG`** in `src/hideout_art/constants.py` —
  placement footprint estimates for all 27 art decorations. Each entry
  records: number of placements observed in `исходники/*.hideout`, min
  and median pairwise Euclidean distance between same-hash placements,
  estimated tile footprint (rounded up to nearest 0.5 tile), and a
  confidence level (`high` ≥5 samples, `medium` 3-4, `low` 2, `single` 1,
  `none` 0).
- **`DecorationFootprint`** NamedTuple + **`FOOTPRINT_CONFIDENCE_LEVELS`**
  frozenset in `constants.py` for type-safe access to the catalog.
- **`scripts/measure_decorations.py`** — dev script that re-derives the
  catalog from `исходники/*.hideout` and prints a table + JSON dump
  (`scripts/decoration_footprints.json`, gitignored as reproducible).
- **94 new pytest tests** in `tests/test_footprints.py`:
  - Catalog covers all `ART_TYPES` and only `ART_TYPES` (no functional
    objects).
  - Every `confidence` value is valid; confidence matches `samples` count.
  - `estimated_tile_footprint` is consistent with `min_spacing_wu`.
  - Specific regression tests for Beech Tree (low-conf, 1 tile),
    Cordilina (11 samples, high-conf), Marble Table (low-conf, 2 tiles —
    KI-10).
  - Atziri Statue explicitly excluded from catalog (per user request).
  - **Ground-truth check**: `samples` field matches actual placement
    count in `исходники/*.hideout` — fails loudly if catalog drifts out
    of sync with source files.
  - Total test count: 233 collected (232 pass, 1 skipped).

### Changed
- `STATUS.md` — rewritten: KI-10 added, "Что улучшать дальше" trimmed to
  5 items, test count updated to 233, hash count still 46 (no new
  hashes — only metadata about existing decorations).
- `AGENTS.md` — added pointer to `DECORATION_FOOTPRINT_CATALOG` and
  `scripts/measure_decorations.py`.
- `docs/img2hideout.md` — added "Каталог размеров декораций" section
  explaining what the catalog measures, what it doesn't (KI-10), and
  how it will be used by the planned multi-pass renderer.
- `scripts/README.md` — added `measure_decorations.py` to the available
  scripts table.
- `.gitignore` — added `scripts/decoration_footprints.json` (auto-
  generated, reproducible).
- Version bumped to `0.2.3` in `pyproject.toml` and `__init__.py`.

### Fixed
- None (no new bugs). All previously known issues (KI-1..KI-9) remain
  fixed; KI-10 is a NEW known issue documenting the placement-vs-sprite-
  bounds limitation of the new catalog.

## [0.2.2] - 2026-07-09

### Added
- **18 new decoration hashes** from user-provided `исходники/` folder
  (5 `.hideout` exports, all targeting Canal Hideout, hash 60415):
  Cordilina, Petrified Cave Figure, Coastal Bush, Small/Medium Coastal
  Stone, Slender Seedling, Log, Beech Tree, Pile of Leaves, Cave Fossil,
  Cave Coral, Summit Brazier, Marble Bench/Table/Walls/Fountain, Camp
  Crate, Camp Gear. All added to `ART_TYPES`.
- `CANAL_HIDEOUT_HASH` (60415) + `CANAL_HIDEOUT_BOUNDS = (700, 540, 860, 775)`
  + `NAMED_BOUNDS` registry + `--bounds canal` CLI shortcut.
- 70 new pytest cases in `tests/test_new_hashes.py` (total: 140).

### Changed
- `constants.py` — `KNOWN_HASHES` 28 → 46 entries; Canal geometry added.
- `cli.py` — `_resolve_bounds()` helper for named/explicit bounds.
- Version bumped to `0.2.2`.

## [0.2.1] - 2026-07-09

### Added
- 5 warm-tone Maraket/Coastal Pebble hashes. `examples/palette_warm.json`
  (9-colour working palette). `tile_size` parameter (closes KI-1).
  `DEFAULT_TILE_SIZE_WORLD_UNITS = 23`. 26 new pytest tests (total: 70).

### Fixed
- **KI-9**: `Placement.is_art` now resolves via hash, not name — Russian-
  named placements correctly classified as art.

## [0.2.0] - 2026-07-09

### Added
- `img2hideout` overhaul: alpha-channel support, 3 colour-distance
  metrics, Floyd-Steinberg dithering, jitter, `step`, `bounds`,
  `resample`, `--preview`. `examples/palette_2b.json` template.
  `docs/img2hideout.md` reference. 11 new pytest tests (total: 44).

## [0.1.0] - 2026-07-09

### Added
- Initial release: tolerant regex parser, `Hideout`/`Placement`
  dataclasses, geometric transforms, header rewriter, PNG preview,
  `img2hideout`, CLI (`inspect`/`layers`/`stats`/`preview`/`shift`/
  `transfer`/`img2hideout`), 23 known hashes, docs, 33 pytest tests.

[Unreleased]: https://github.com/vudirvp-sketch/poe2-hideout-art/compare/v0.2.4...HEAD
[0.2.4]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.4
[0.2.3]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.3
[0.2.2]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.2
[0.2.1]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.1
[0.2.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.0
[0.1.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.1.0
