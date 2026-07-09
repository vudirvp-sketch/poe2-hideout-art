# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/vudirvp-sketch/poe2-hideout-art/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.0
[0.1.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.1.0
