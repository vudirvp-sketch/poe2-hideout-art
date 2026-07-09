# The `.hideout` file format

This document is the canonical spec for the `.hideout` file format used
by **Path of Exile 2** hideout exports. It was reverse-engineered from
observed files; if you find a value that contradicts what's written
here, please open an issue.

## TL;DR

A `.hideout` file is UTF-8 (often with BOM) JSON. The top-level object
has four header fields and a `doodads` object. **The `doodads` object
contains duplicate keys on purpose** — one entry per placement, all
sharing the decoration name as the key. Standard JSON parsers will
collapse these duplicates; you need a tolerant parser.

## Top-level structure

```jsonc
{
  "version": 1,
  "language": "English",
  "hideout_name": "Canal Hideout",
  "hideout_hash": 60415,
  "doodads": {
    /* ... many entries, with duplicate keys ... */
  }
}
```

| Field | Type | Meaning |
|---|---|---|
| `version` | int | Always `1` as of writing. |
| `language` | string | UI language the file was exported under. Affects decoration display names (which are localised). Hashes are stable across languages. |
| `hideout_name` | string | Localised name of the hideout map. |
| `hideout_hash` | int | Numeric id of the hideout map. Used by the game to find the right tile layout. |
| `doodads` | object | One JSON object per placement. Keys repeat. |

## Placement entry

Each entry inside `doodads` has exactly this shape (field order matters
for the regex parser, but the game itself is order-tolerant):

```jsonc
"Decoration Name": {
  "hash": 2219637749,
  "x":    774,
  "y":    632,
  "r":    57344,
  "fv":   7
}
```

### `hash` — uint32

Stable in-game asset id. **Same value for every instance of a given
decoration.** For example, all 395 instances of "Long Grass" in a
reference export share `hash = 2219637749`.

The full asset catalogue is not shipped with the file. To resolve a
hash to a decoration name you need either:

* a sample export from the same hideout where the name appears, OR
* `hideout-art`'s `KNOWN_HASHES` table (`src/hideout_art/constants.py`).

Unknown hashes are **kept verbatim** by the parser and writer. Never
invent a hash.

### `x`, `y` — int

World coordinates of the placement's origin (typically the centre of
the decoration's footprint).

**`y` grows upward.** This was verified against a reference composition
where "Sand Tussock" (the decoration used for hair at the top of the
picture) has the highest y values.

Coordinates are integers. The observed range in a Canal Hideout
composition is roughly `x ∈ [662, 867]`, `y ∈ [519, 786]` — i.e. a
~205×267 world-unit area.

### `r` — uint16

Rotation as an unsigned 16-bit fraction of a full turn:

```
degrees = r / 65536 * 360
```

So `r = 0` is 0°, `r = 16384` is 90°, `r = 32768` is 180°,
`r = 49152` is 270°, `r = 65535` is ~359.99°.

Empirically, PoE2's editor snaps to 15° increments. Observed values
(0, 2730, 5461, 8192, 10922, 13653, 16384, ...) all correspond to
multiples of 15°, but the field is unbounded — arbitrary rotations are
allowed.

`hideout-art` normalises `r` into `[0, 65536)` after every arithmetic
operation. See `src/hideout_art/transforms.py`.

### `fv` — uint8

Bitfield with two pieces of information packed into a single byte:

```
bit 7 (0x80) : flip_x  — mirror the decoration horizontally
bits 0..6    : variant — index into the decoration's variant list (0..127)
```

So:

| `fv` value | `flip_x` | `variant` |
|---|---|---|
| `0`   | No  | 0 |
| `1`   | No  | 1 |
| `7`   | No  | 7 |
| `128` | Yes | 0 |
| `135` | Yes | 7 |

Empirically, the variant index observed in art compositions stays in
`{0..8}`. The full 7-bit range (0..127) is theoretically available but
most decorations have only a handful of variants.

To toggle the flip bit without touching the variant:
```python
p.fv ^= 0x80
```

To set the variant without touching the flip:
```python
p.fv = (p.fv & 0x80) | (variant & 0x7F)
```

## Why duplicate keys?

The format predates a richer schema. The exporter walks every placed
decoration and serialises each one as `"name": { ... }` under
`doodads`, regardless of whether the same name has appeared before.

The game's importer reads `doodads` as an ordered list of pairs (it
doesn't deduplicate), so duplicate keys are required for valid round-trips.

### Practical consequences

1. **`json.load` is unsafe.** It collapses duplicate keys and keeps
   only the last one. A real hideout with 752 placements would
   collapse to ~23. Always use `Hideout.from_file()`.
2. **`json.dump` is unsafe.** It serialises a dict, which has unique
   keys — you'd lose placements on round-trip. Always use
   `write_hideout()` or `Hideout.to_file()`.
3. **`jq` is unsafe** for the same reason.

## Round-trip stability

`hideout-art` guarantees:

- Parse a `.hideout` → write it back → byte-identical output
  (modulo BOM, trailing whitespace, and indentation).
- No placement is dropped, renamed or reordered.
- Unknown hashes are preserved verbatim.

The writer always emits UTF-8 **without BOM**. PoE2 accepts both, but
no-BOM is cleaner for version control (no spurious diffs).

## Edge cases observed

1. **BOM.** Real exports ship with a UTF-8 BOM. `hideout-art` strips
   it on read and does not emit it on write.
2. **Negative coordinates.** Not observed in valid exports, but the
   parser accepts them. The game will clip placements outside the
   hideout's tile grid.
3. **`r` > 65535 or `r < 0`.** Not observed in valid exports. The
   parser accepts them; transforms normalise them.
4. **Unknown decoration names.** Some exports use localised names
   (e.g. Russian, Chinese). Hashes are stable; names are not. If you
   re-export from a different language client, names will change but
   hashes won't.

## What the file does NOT contain

- The hideout's tile-grid boundaries.
- The size (in tiles) of each decoration.
- The decoration's visual appearance (textures, models, etc.) — those
  are referenced by `hash` and resolved by the game client.
- Any player account info — exports are anonymous.

This means tooling cannot, without external data:

- Detect placements that fall outside the playable area.
- Compute whether two decorations overlap.
- Render a faithful preview (we approximate by colour-coding each
  decoration type).
