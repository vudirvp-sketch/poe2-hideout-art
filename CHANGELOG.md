# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.2] - 2026-07-09

### Added
- **18 new decoration hashes** from user-provided `исходники/` folder
  (5 `.hideout` exports, all targeting Canal Hideout, hash 60415):
  - Boundary / marker: `Cordilina` (1082688452), `Petrified Cave Figure`
    (2014424642).
  - Coastal stones: `Coastal Bush` (2984478824), `Small Coastal Stone`
    (1122244925), `Medium Coastal Stone` (369950199).
  - Plants / foliage: `Slender Seedling` (532751457, ru: «Тонкосемянник»),
    `Log` (2780985165), `Beech Tree` (2796444611), `Pile of Leaves`
    (4294658310).
  - Cave / mountain: `Cave Fossil` (2206403756), `Cave Coral` (2359120247),
    `Summit Brazier` (2623109233).
  - Marble furniture (light gray — closest existing match for 2B "white"):
    `Marble Bench` (534959854), `Marble Table` (4056218057),
    `Marble Walls` (1380152311), `Marble Fountain` (525963527).
  - Camp props: `Camp Crate` (2156404357), `Camp Gear` (412387213).
  - All 18 added to `ART_TYPES` (none are gameplay-functional).
- **`CANAL_HIDEOUT_HASH`** constant (60415) — the Canal Hideout map hash,
  extracted from the header for programmatic use.
- **`CANAL_HIDEOUT_BOUNDS`** constant `(700, 540, 860, 775)` — the
  playable-canvas bounding box of Canal Hideout, calibrated from a
  user-provided boundary outline (11 Cordilina placements around the
  perimeter + 1 Petrified Cave Figure as centre marker).
- **`NAMED_BOUNDS`** registry + **`--bounds <name>`** CLI shortcut.
  `--bounds canal` now resolves to `CANAL_HIDEOUT_BOUNDS`; explicit
  `--bounds x_min,y_min,x_max,y_max` still works. Case-insensitive.
  Add new hideouts to `NAMED_BOUNDS` as their canvases get measured.
- 70 new pytest cases (parametrised) in `tests/test_new_hashes.py`:
  18 hash-registration tests, 18 ART_TYPES tests, 1 collision test,
  1 catalogue-size sanity test (`len(KNOWN_HASHES) == 46`), 18
  source-file presence tests (one per new hash), 5 whole-file no-unknowns
  tests for each `исходники/*.hideout`, 1 Canal-hash header test,
  3 Russian→English cross-validation tests, 7 bounds tests, 1
  `is_art`-via-hash test for all new decorations in real exports.
  Total test count: 140 collected (139 pass, 1 skipped — `Береговая
  галька` Russian name not present in `исходники/`).

### Changed
- `src/hideout_art/constants.py` — `KNOWN_HASHES` grew from 28 → 46
  entries; comments note estimated RGB where available and Russian
  in-game names where they differ from canonical English (e.g.
  `Long Grass` ← ru `Высокая трава`, `Sand Tussock` ← ru `Песчаный
  кустарник`). Added `CANAL_HIDEOUT_HASH`, `CANAL_HIDEOUT_BOUNDS`,
  `NAMED_BOUNDS` constants.
- `src/hideout_art/cli.py` — extracted `_resolve_bounds()` helper that
  accepts either a named shortcut (`canal`) or an explicit
  `x_min,y_min,x_max,y_max` string. `--bounds` help text updated.
- `src/hideout_art/img2hideout.py` — docstring of `image_to_hideout()`
  now mentions `CANAL_HIDEOUT_BOUNDS` for the `bounds` parameter.
- `STATUS.md` — rewritten: KI table at the top, test count updated to
  140, hash count updated to 46, "Что улучшать дальше" trimmed to 5 items.
- `docs/img2hideout.md` — added `--bounds canal` documentation and a
  "Canal Hideout canvas" calibration section.
- `examples/README.md` — added note about `--bounds canal` and the 18
  new Canal decorations available for palette construction.
- Version bumped to `0.2.2` in `pyproject.toml` and `__init__.py`.

### Fixed
- None (no new bugs). All previously known issues (KI-1..KI-9) remain
  fixed; KI-2 partially improved (marble candidates added but not yet
  RGB-calibrated).

## [0.2.1] - 2026-07-09

### Added
- 5 new decoration hashes from user-provided exports (closes KI-2 partially):
  - `Maraket Rubble` (hash 3012657298) — warm tan/khaki ~(138,120,94)
  - `Maraket Treasures` (hash 1078696835) — dark warm gray ~(108,91,83)
  - `Maraket Samovar` (hash 57228444) — light warm gray ~(148,133,115)
  - `Maraket Ornament` (hash 2125171205) — warm tan/khaki ~(136,120,97)
  - `Coastal Pebble` (hash 2365064644) — warm tan/khaki ~(134,115,94)
  - All 5 added to `ART_TYPES` (purely decorative).
- `examples/palette_warm.json` — fully working 9-colour warm-tone palette
  (4 original Canal colours + 5 new warm decorations). Loads cleanly
  today; use it for desert/wood/stone/autumn scenes.
- `tile_size` parameter in `image_to_hideout()` and `--tile-size` in CLI
  (closes KI-1). Auto-computes `step = max(1, round(tile_size / scale))`
  so that one decoration is placed per game tile — no overlap, no gaps.
  Mutually exclusive with `step`.
- `DEFAULT_TILE_SIZE_WORLD_UNITS = 23` constant in `constants.py`,
  calibrated from observed placement deltas in user exports.
- 26 new pytest tests (`tests/test_new_hashes.py` + 5 new tests in
  `tests/test_img2hideout.py` for `tile_size`); total test count: 70.

### Fixed
- **KI-9** (new): `Placement.is_art` was checking `self.name in ART_TYPES`,
  which failed for non-English `.hideout` exports (e.g. Russian
  "Береговая галька" never matched English "Coastal Pebble"). Now
  resolves via `HASH_TO_NAME.get(self.hash, self.name)` first, falling
  back to the raw name for unknown hashes (legacy behaviour preserved).

### Changed
- `examples/palette_2b.json` — clarified that the 5 new warm-tone
  decorations do NOT fill the cool-tone TODOs (white/black/silver/skin/red
  still missing); added `_available_warm_alternatives_in_0_2_1` section
  listing the new decorations and why they don't fit 2B's cool palette.
- `STATUS.md` — rewritten: KI-1 and KI-9 marked fixed, KI-2 marked
  partially fixed, "Что улучшать дальше" trimmed to 5 concrete items.
- `docs/img2hideout.md` — added `--tile-size` documentation and a
  "calibration" section explaining how `DEFAULT_TILE_SIZE_WORLD_UNITS`
  was derived.

## [0.2.0] - 2026-07-09

### Added
- `img2hideout` overhaul — new opt-in features, all defaults preserve 0.1.0
  behaviour byte-for-byte:
  - **alpha-channel support** — RGBA PNGs skip transparent pixels
    automatically (`--alpha-threshold`, `--no-alpha`);
  - **3 colour-distance metrics** — `rgb` (default), `weighted` (luminance),
    `redmean` (perceptual, good for warm colours);
  - **Floyd-Steinberg dithering** — `--dither` for smoother gradients;
  - **jitter** — `--jitter` randomises `r` (multiples of 15°) and `variant`
    per placement, with optional seed for reproducibility;
  - **`step`** — place a decoration every Nth pixel to spread out density
    (`--step 2` is the recommended starting point for Canal Hideout);
  - **`bounds`** — clip placements to a world-coord rectangle
    (`--bounds x_min,y_min,x_max,y_max`) to respect hideout boundaries;
  - **`resample`** — `nearest`/`bilinear`/`bicubic`/`lanczos` downscaling
    (NEAREST preserves pixel-art edges);
  - **`--preview`** CLI flag — writes a PNG preview next to the `.hideout`
    so you can iterate without importing into the game.
- `examples/palette_2b.json` — template palette for portraits (2B-like
  characters) with TODO placeholders and instructions for finding the
  missing decorations in-game.
- `docs/img2hideout.md` — full parameter reference, tips, and troubleshooting.
- `STATUS.md` — short live state-of-the-project doc (what works, known
  issues, what to improve next).
- 11 new pytest tests in `tests/test_img2hideout.py` (smoke tests for
  every new option; total test count: 44).

### Changed
- `examples/README.md` — refreshed to document the new options and the
  `palette_2b.json` template.
- `AGENTS.md` — added pointers to `STATUS.md` and `docs/img2hideout.md`.

## [0.1.0] - 2026-07-09

### Added
- Initial release.
- Tolerant regex parser for `.hideout` files (preserves duplicate keys in
  `doodads`, which standard `json.load` would collapse).
- `Hideout` and `Placement` dataclasses with convenience properties:
  `rotation_degrees`, `flip_x`, `variant`, `is_art`.
- Inspection helpers: `bbox()`, `counts_by_name()`, `counts_by_hash()`,
  `layers()`, `find_unknown_hashes()`.
- Geometric transforms: `shift`, `rotate`, `mirror_x`, `mirror_y`,
  `recombine` (all support `art_only=True`).
- Header rewriter for transferring a composition to a different hideout map.
- PNG preview renderer (matplotlib, optional extra).
- `img2hideout` — convert any image into a `.hideout` composition via a
  configurable colour-to-decoration palette (pillow, optional extra).
- CLI `hideout-art` with `inspect`, `layers`, `stats`, `preview`, `shift`,
  `transfer`, `img2hideout` subcommands.
- Initial catalogue of 23 known hashes (Canal Hideout sample).
- Documentation: `docs/format.md` (file format spec), `README.md`,
  `CONTRIBUTING.md`, `AGENTS.md`.
- Test suite: `test_parser.py`, `test_writer.py`, `test_transforms.py`
  with a small synthetic fixture.
- Example palette file at `examples/palette.json`.

[Unreleased]: https://github.com/vudirvp-sketch/poe2-hideout-art/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.2
[0.2.1]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.1
[0.2.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.0
[0.1.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.1.0
