# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/vudirvp-sketch/poe2-hideout-art/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.1
[0.2.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.0
[0.1.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.1.0
