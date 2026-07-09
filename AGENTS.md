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
| Find the parser entrypoint | `src/hideout_art/parser.py` → `Hideout.from_file()` |
| Find the writer | `src/hideout_art/writer.py` → `write_hideout()` |
| Add a new decoration hash | `src/hideout_art/constants.py` → `KNOWN_HASHES` |
| Add a new geometric transform | `src/hideout_art/transforms.py` |
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
- **`cli.py`** — argparse-based CLI. One file per command, registered
  in `build_parser()`.
- **`constants.py`** — `KNOWN_HASHES`, `HASH_TO_NAME`, `ART_TYPES`,
  and the magic-number constants (`ROTATION_MODULUS`, `FV_FLIP_X_BIT`,
  `FV_VARIANT_MASK`). This is the file most PRs touch.

### `tests/`

- **`test_parser.py`** — round-trip parse → write → parse equality;
  field decoder tests; unknown-hash handling.
- **`test_writer.py`** — output is byte-stable; duplicate keys are
  preserved.
- **`test_transforms.py`** — `shift`/`rotate`/`mirror` correctness on
  the sample fixture.
- **`data/sample.hideout`** — tiny synthetic fixture (< 1 KB).
  Contains one of each: a functional object, an art-layer decoration
  with rotation, an art-layer decoration with `flip_x`, an unknown
  decoration (to test resilience).

### `docs/`

- **`format.md`** — the canonical file format spec. Update this if you
  discover new field semantics.
- **`screenshots/`** — PNGs used by `README.md`.

### `examples/`

- **`palette.json`** — example palette file for `img2hideout`.
- **`README.md`** — how to use the examples.

### `scripts/`

One-off dev scripts. Anything experimental goes here, not in
`src/hideout_art/`.

## When in doubt

Open an issue and ask. Don't guess semantics — this format was
reverse-engineered from observation, and wrong assumptions compound.
