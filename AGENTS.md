# AGENTS.md

Navigation hints for AI assistants (Claude, GPT, Cursor, Copilot, etc.)
working on this repository. Read this file first; it tells you where
everything lives and where the surprises are.

> If you are an AI agent browsing this repo for the first time, start at
> `README.md` for the user-facing overview, then come back here.

## TL;DR — where to look first

| If you need to... | Open this file |
|---|---|
| Understand the file format | `docs/format.md` |
| Understand the `img2hideout` pipeline + options | `docs/img2hideout.md` |
| See current state + known issues | `STATUS.md` |
| Find the parser entrypoint | `src/hideout_art/parser.py` → `Hideout.from_file()` |
| Find the writer | `src/hideout_art/writer.py` → `write_hideout()` |
| Add a new decoration hash | `src/hideout_art/constants.py` → `KNOWN_HASHES` |
| Look up a decoration's placement footprint | `src/hideout_art/constants.py` → `DECORATION_FOOTPRINT_CATALOG` |
| Re-measure footprints after adding placements to `исходники/` | `scripts/measure_decorations.py` |
| Pixel-sample real RGB under placements | `scripts/sample_pixels.py` (closes KI-11) |
| Draw geometric shapes directly in world coords | `src/hideout_art/primitives.py` + `scripts/draw_primitives.py` (0.2.7) |
| Add a new geometric transform | `src/hideout_art/transforms.py` |
| Extend `img2hideout` (dither, alpha, etc.) | `src/hideout_art/img2hideout.py` |
| Add a CLI subcommand | `src/hideout_art/cli.py` (register in `build_parser()`) |
| See what's tested | `tests/` |
| Find example inputs | `examples/` |

## The single most important thing

**The `.hideout` JSON has duplicate keys inside `doodads`.** Standard
`json.load` collapses them. Never use `json.load` to read a real
`.hideout` file — you will silently lose ~99% of placements. Use
`Hideout.from_file()` from `parser.py`, which uses a tolerant regex
scanner.

The writer (`writer.py`) intentionally emits duplicate keys. Do not
"refactor" it to merge placements into a list — that would produce a
file the game rejects.

## Field semantics (do not guess — verify)

| Field | Type | Verified meaning |
|---|---|---|
| `hash` | uint32 | Stable in-game asset id. Same for every instance of a decoration. Verified: 395 instances of "Long Grass" all share `2219637749`. |
| `x`, `y` | int | World coordinates. **y grows upward** — verified by Sand Tussock having the highest y values and being the hair at the top of the picture. |
| `r` | uint16 | Rotation. `deg = r / 65536 * 360`. Verified: values seen are exact multiples of 15° (0, 2730, 5461, 8192, ...). |
| `fv` | uint8 | Bitfield. Bit `0x80` = horizontal flip. Lower 7 bits = variant index. Verified: all observed values fall in `{0..8}` or `{128..136}` (= `0x80 + {0..8}`). |

If you encounter a value that doesn't fit this scheme, **do not invent
new semantics**. Open an issue instead.

## Things to never do

1. **Never call `json.load` on a real `.hideout` file** — see above.
2. **Never merge placements into a list when writing** — the game
   expects one object per placement under `doodads`.
3. **Never add `matplotlib` or `pillow` as a hard dependency** — they
   are optional extras. Import them inside the functions that need
   them, never at module top-level (except in `preview.py` and
   `img2hideout.py` which are themselves optional modules).
4. **Never invent hashes.** If a decoration is missing from
   `KNOWN_HASHES`, the parser keeps its hash verbatim. Do NOT generate
   a placeholder; flag it via `Hideout.find_unknown_hashes()` instead.
5. **Never "fix" the duplicate-key writer.** It is the format.

## How to extend the catalogue

1. Find a hideout export containing the new decoration.
2. `hideout-art inspect path/to/file.hideout` — unknown hashes are
   listed in the output.
3. Add the entry to `KNOWN_HASHES` in `constants.py` with the source
   hideout noted in the commit message.
4. If the decoration is purely artistic, also add it to `ART_TYPES`.
5. Add a round-trip test in `tests/test_parser.py`.

## How to add a CLI subcommand

1. Write a `_cmd_<name>(args)` function in `cli.py`.
2. Register it inside `build_parser()`:
   ```python
   p = sub.add_parser("your-cmd", help="...")
   p.add_argument("file")
   p.set_defaults(fn=_cmd_your_cmd)
   ```
3. Add a usage example to `README.md` and the CLI docstring in `cli.py`.
4. Add a smoke test in `tests/test_cli.py` (create if it doesn't exist).

## Running tests

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
```

Tests use a tiny synthetic fixture at `tests/data/sample.hideout`.
Do NOT add real-world hideout exports to the repo — keep the fixture
minimal.

## File-by-file map

### `src/hideout_art/`

- **`__init__.py`** — public API surface. Re-exports the things users
  actually need. Keep this short.
- **`parser.py`** — `Hideout` and `Placement` dataclasses. The regex
  `_ENTRY_RE` is the heart of the package. Do not change it without
  adding a regression test.
- **`writer.py`** — serialises a `Hideout` back to the duplicate-key
  JSON format. Also monkey-patches `Hideout.to_file()` and
  `Hideout.to_string()` so the API is symmetric.
- **`transforms.py`** — `shift`, `rotate`, `mirror_x`, `mirror_y`,
  `recombine`. All operate in-place and return the `Hideout` for
  chaining.
- **`preview.py`** — PNG renderer. Optional dependency on matplotlib.
- **`palette.py`** — colour-to-decoration mapping for `img2hideout`.
  Pure stdlib.
- **`img2hideout.py`** — image → `Hideout`. Optional dependency on
  pillow.
- **`primitives.py`** (0.2.7) — drawing primitives that place art
  decorations along geometric shapes (line, hollow_circle, filled_circle,
  s_snake, thick_line_with_contours). Pure stdlib. Uses
  `DECORATION_FOOTPRINT_CATALOG.min_spacing_wu` via `safe_spacing()` to
  respect per-decoration placement density. Never mutates the input
  Hideout — returns fresh `list[Placement]`. See `center_composition`
  for a curated 5-shape layout, and `scripts/draw_primitives.py` for the
  CLI that injects it into an existing `.hideout` file. See KI-13 in
  `STATUS.md` for the "needs in-game verification" caveat.
- **`cli.py`** — argparse-based CLI. One file per command, registered
  in `build_parser()`. `_resolve_bounds()` handles `--bounds` named
  shortcuts (e.g. `canal`) and explicit `x_min,y_min,x_max,y_max`.
- **`constants.py`** — `KNOWN_HASHES` (47 entries), `HASH_TO_NAME`,
  `ART_TYPES` (28 entries), the magic-number constants
  (`ROTATION_MODULUS`, `FV_FLIP_X_BIT`, `FV_VARIANT_MASK`),
  `DEFAULT_TILE_SIZE_WORLD_UNITS = 23`, Canal Hideout geometry
  (`CANAL_HIDEOUT_HASH = 60415`, `CANAL_HIDEOUT_BOUNDS = (700, 540, 860, 775)`,
  `NAMED_BOUNDS`), and **`DECORATION_FOOTPRINT_CATALOG`** (0.2.3) —
  placement footprint estimates for all 28 art decorations, with
  confidence levels. See KI-10 in `STATUS.md` for the placement-vs-
  sprite-bounds limitation. This is the file most PRs touch.

  **RGB values in comments** (0.2.4 + 0.2.5 + 0.2.6): Two RGB sources
  now coexist:
  - **VLM** (glm-4.6v, 0.2.4/0.2.5) — first-pass estimates, NOISY (KI-11).
  - **PIXEL** (0.2.6, `scripts/sample_pixels.py`) — ground truth from
    screenshot pixel sampling under each placement.
  When they conflict, trust PIXEL. See `_pixel_sampling_summary_0_2_6`
  in `examples/palette_2b.json` for the full comparison table. Notable:
  - Sand Tussock PIXEL (112,99,79) resolves VLM 0.2.1 (78,52,46) vs
    VLM 0.2.5 (180,160,120) conflict — both VLM passes were wrong.
  - Maraket Rubble PIXEL (125,112,87) is NEUTRAL brown, not reddish
    as VLM 0.2.5 (153,78,68) claimed.
  - Marble-серия PIXEL (76-196) is much darker than VLM (210-230) —
    KI-12, sampling likely hit shadow. VLM values retained in
    palette_2b.json until manual calibration resolves KI-12.

### `tests/`

- **`test_parser.py`** — round-trip parse → write → parse equality;
  field decoder tests; unknown-hash handling.
- **`test_writer.py`** — output is byte-stable; duplicate keys are
  preserved.
- **`test_transforms.py`** — `shift`/`rotate`/`mirror` correctness on
  the sample fixture.
- **`test_img2hideout.py`** — smoke tests for every `img2hideout` option
  (alpha, dither, jitter, bounds, resample, color_metric, tile_size).
- **`test_new_hashes.py`** — 0.2.1 warm hashes + 0.2.2 new Canal hashes
  + `CANAL_HIDEOUT_BOUNDS` + `--bounds canal` CLI resolver + KI-9 fix
  (Russian-name → English-canonical via hash) + 0.2.4 VLM-measured
  Marble-серия RGB + 0.2.5 Seaweed + Small Coastal Stone (black role) +
  Maraket Rubble (red role) + 0.2.6 pixel-sampled RGB regression tests
  (Small Coastal Stone, Maraket Rubble, Sand Tussock, Marble Table) +
  palette_2b.json progress (5 of 6 TODOs filled, only `skin` remains).
- **`test_sample_pixels.py`** (0.2.6) — 19 cases for the
  `scripts/sample_pixels.py` calibration math: auto-calibration,
  manual least-squares fit + residual, RGB statistics, aggregate
  medians (n==1, n==2 mean, n>=3 nearest-rank), sampling window
  bounds clamping. Pure-Python — no PIL/Pillow needed.
- **`test_footprints.py`** (0.2.3) — 94 cases for
  `DECORATION_FOOTPRINT_CATALOG`: structural integrity, confidence↔
  samples consistency, spacing↔footprint math, regression tests for
  specific entries (Beech Tree, Cordilina, Marble Table), and a
  ground-truth check that `samples` matches real placement counts in
  `исходники/*.hideout`.
- **`test_primitives.py`** (0.2.7) — 37 cases for the drawing-primitives
  module: `safe_spacing` validation, `line`/`polyline` geometry,
  `hollow_circle`/`filled_circle` point counts and radii, `s_snake`
  shape bounds, `thick_line_with_contours` perimeter + fill separation
  + dedup, `center_composition` end-to-end (uses only ART_TYPES, fits
  Canal Hideout bounds, no duplicates, all 5 shapes present,
  relocatable), and a round-trip parse → write → parse test.
- **Total test count: 311** (310 pass, 1 skipped — see `STATUS.md`).
- **`data/sample.hideout`** — tiny synthetic fixture (< 1 KB).
  Contains one of each: a functional object, an art-layer decoration
  with rotation, an art-layer decoration with `flip_x`, an unknown
  decoration (to test resilience).

### `исходники/` (0.2.2)

User-provided reference exports. **Not test fixtures** — these are real
.hideout files with real Russian-named placements. Used as a data source
for catalogue growth (test cases in `test_new_hashes.py` reference them
by filename substring). Contents:

- `Кордилой обозначил...hideout` — 11 Cordilina + 1 Petrified Cave Figure
  outlining the Canal Hideout playable canvas. Source of
  `CANAL_HIDEOUT_BOUNDS`.
- `камни и кустарники.hideout` — Coastal Bush + Small Coastal Stone.
- `еще камни и растения.hideout` — Medium Coastal Stone + Slender Seedling.
- `еще элементы.hideout` — Cave Fossil, Cave Coral, Summit Brazier,
  Marble Bench/Table/Walls/Fountain.
- `всякое.hideout` — Log, Beech Tree, Pile of Leaves, Camp Crate, Camp Gear.
- `водоросли и летающий песок.hideout` (0.2.5) — 7 Seaweed (Морская
  водоросль, new in 0.2.5) + 1 Falling Sand. Source file for the Seaweed
  hash measurement.
- Matching `.jpg` screenshots alongside each `.hideout` for RGB calibration.

### `docs/`

- **`format.md`** — the canonical file format spec. Update this if you
  discover new field semantics.
- **`img2hideout.md`** — full parameter reference for the
  `img2hideout` pipeline (alpha, dither, jitter, bounds, resample,
  colour metrics). Update when adding a new option.
- **`screenshots/`** — PNGs used by `README.md`.

### Top-level

- **`STATUS.md`** — short live state-of-the-project doc. **Read this
  first** when picking up the project: what works, what's broken, what
  to improve next. Keep it under ~200 lines; move long history to
  `CHANGELOG.md`.

### `examples/`

- **`palette.json`** — example palette file for `img2hideout` (4-colour,
  Canal Hideout). Fine for abstract shapes; insufficient for portraits.
- **`palette_2b.json`** — template palette for portraits (2B-like
  characters) with `TODO_*` placeholders. Filling the template requires
  finding new decorations in-game and adding their hashes to
  `KNOWN_HASHES`. See the file's `_how_to_fill` block.
- **`README.md`** — how to use the examples.

### `scripts/`

One-off dev scripts. Anything experimental goes here, not in
`src/hideout_art/`. Notable:

- **`measure_decorations.py`** (0.2.3) — re-derives
  `DECORATION_FOOTPRINT_CATALOG` from `исходники/*.hideout`. Re-run
  whenever new placements are added, then update `constants.py`
  (`test_sample_counts_match_real_exports` will fail if you forget).
- **`sample_pixels.py`** (0.2.6) — pixel-samples real RGB under each
  art placement in a `.hideout` file using the matching `.jpg`
  screenshot. Auto or manual world→pixel calibration, diagnostic
  overlay PNG, JSON report. Closes KI-11. See `scripts/README.md`
  for full usage.
- **`sample_all.py`** (0.2.6) — convenience wrapper that runs
  `sample_pixels.py` on all 7 `исходники/` screenshot+hideout pairs
  and consolidates into `scripts/sampled_all.json`.
- **`draw_primitives.py`** (0.2.7) — injects the curated 5-shape
  composition (`center_composition` from `primitives.py`) into the
  centre of an existing `.hideout` file. Strictly additive — never
  removes placements. Optional `--bounds-check` fails if any new
  placement falls outside Canal Hideout bounds. Optional `--preview`
  renders a PNG. See KI-13 for the in-game verification caveat.
- **`render_primitives_preview.py`** (0.2.7) — thicker preview PNG
  renderer with per-decoration colour coding, Canal Hideout canvas
  outline, centre marker, and legend. Used for visual sanity check
  of primitive layouts before importing in-game.

## When in doubt

Open an issue and ask. Don't guess semantics — this format was
reverse-engineered from observation, and wrong assumptions compound.
