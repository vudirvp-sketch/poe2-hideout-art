# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/vudirvp-sketch/poe2-hideout-art/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.1.0
