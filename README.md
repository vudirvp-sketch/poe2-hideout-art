# hideout-art

Read, transform and emit **Path of Exile 2** `.hideout` files. Build floor-art
compositions from images. Pure Python, no external services, MIT-licensed.

> [!WARNING]
> This project is **not affiliated with** Grinding Gear Games. All trademarked
> names belong to their owners. Use at your own risk; tool-assisted hideout
> editing has historically been tolerated but is not officially endorsed.

---

## Why does this exist?

A PoE2 `.hideout` export looks like JSON — but it isn't quite standard JSON.
The `doodads` object contains **hundreds of duplicate keys**, one per
placement. Standard `json.load` collapses duplicates and silently keeps only
the last one, which would drop 99% of the data on a real hideout.

`hideout-art` ships a tolerant parser that preserves every placement in
source order, plus a small toolkit for inspecting, transforming, rendering
and re-emitting these files. The end goal: **turn any PNG into a floor-art
composition** you can import into the game.

## Features

- **Tolerant parser** — duplicate keys in `doodads` are preserved, not collapsed
- **Field decoder** — `r` is a 16-bit angle, `fv` is `flip_x | variant` (bitfield)
- **Geometric transforms** — shift / rotate / mirror, optionally on art-layer only
- **Header rewrite** — transfer a composition to a different hideout map
- **PNG preview** — top-down render, one colour per decoration type
- **Image → hideout** — sample a PNG, map each pixel to the closest palette
  entry, emit a `.hideout` file
- **CLI** + **Python API** — same operations, two interfaces
- **Pure stdlib core** — `matplotlib` / `pillow` are optional extras

## Quick start

```bash
pip install hideout-art
# Optional extras:
pip install "hideout-art[preview]"   # for PNG rendering
pip install "hideout-art[image]"     # for img2hideout
pip install "hideout-art[dev]"       # for contributors
```

### CLI

```bash
hideout-art inspect  path/to/file.hideout
hideout-art layers   path/to/file.hideout
hideout-art stats    path/to/file.hideout
hideout-art preview  path/to/file.hideout -o preview.png
hideout-art shift    path/to/file.hideout -o moved.hideout -x 50 -y -20
hideout-art shift    path/to/file.hideout -o art_only.hideout -x 50 --art-only
hideout-art transfer path/to/file.hideout -o other.hideout \
    --name "Kurast Hideout" --hash 12345
hideout-art img2hideout picture.png -o art.hideout \
    --palette examples/palette.json --scale 3 --width 100 --step 2 \
    --preview
```

See [`docs/img2hideout.md`](docs/img2hideout.md) for the full parameter
reference (alpha channel, dithering, jitter, bounds, resample, colour
metrics, etc.).

### Python API

```python
from hideout_art import Hideout, render_png

h = Hideout.from_file("my.hideout")

# Inspect
print(len(h), "placements")
print(h.counts_by_name().most_common(5))
print("bbox:", h.bbox(art_only=True))

# Shift the art layer only
h.shift(dx=50, dy=-20, art_only=True)

# Render a preview
render_png(h, "preview.png", art_only=True)

# Save back
h.to_file("moved.hideout")
```

```python
from hideout_art import image_to_hideout, default_palette

h = image_to_hideout(
    "portrait.png",
    palette=default_palette(),
    target_width=120,
    scale=2,
    origin_x=700,
    origin_y=550,
    hideout_name="Canal Hideout",
    hideout_hash=60415,
)
h.to_file("portrait.hideout")
```

## How a `.hideout` file is laid out

See [`docs/format.md`](docs/format.md) for the full spec. Short version:

```jsonc
{
  "version": 1,
  "language": "English",
  "hideout_name": "Canal Hideout",
  "hideout_hash": 60415,
  "doodads": {
    "Stash":     { "hash": 3230065491, "x": 811, "y": 519, "r": 32298, "fv": 0 },
    "Long Grass": { "hash": 2219637749, "x": 774, "y": 632, "r": 57344, "fv": 7 },
    "Long Grass": { "hash": 2219637749, "x": 721, "y": 557, "r": 10922, "fv": 135 },
    // ... hundreds more, all sharing keys
  }
}
```

| Field | Type | Meaning |
|---|---|---|
| `hash` | uint32 | Stable in-game asset id (same value for every instance of a decoration) |
| `x`, `y` | int | World coordinates. **y grows upward.** |
| `r` | uint16 | Rotation as a fraction of 360°: `deg = r / 65536 * 360` |
| `fv` | uint8 | Bit 0x80 = horizontal flip; lower 7 bits = variant index (0..127) |

## What you can build with this

| Goal | Tool |
|---|---|
| Inspect a hideout to see what's in it | `inspect`, `layers`, `stats` |
| Move a composition elsewhere in the same hideout | `shift` |
| Mirror a composition for symmetry | `mirror_x`, `mirror_y` (Python API) |
| Move a composition to a different hideout map | `transfer` (+ sample validation) |
| Combine several compositions side-by-side | `recombine` (Python API) |
| Visualise a hideout before re-importing | `preview` |
| Generate new art from a PNG | `img2hideout` |
| Catalogue new decorations from observed hashes | PR to `constants.py` |

## What you **can't** do

- Validate that a `hash` exists in a target hideout without a sample export.
  Use `Hideout.find_unknown_hashes()` after loading a target sample.
- Discover tile-grid boundaries — they are not in the file; placements
  outside the playable area are silently clipped by the game. You can
  work around this with `img2hideout --bounds x_min,y_min,x_max,y_max`
  if you have "outlined" the playable area.
- Know each decoration's tile footprint without observing it in-game.

See [`STATUS.md`](STATUS.md) for the current list of known issues and
planned improvements.

## Repository layout

```
poe2-hideout-art/
├── src/hideout_art/         # the Python package
│   ├── parser.py            # tolerant regex parser, Hideout/Placement dataclasses
│   ├── writer.py            # .hideout emitter (byte-compatible with the format)
│   ├── transforms.py        # shift / rotate / mirror / recombine
│   ├── preview.py           # PNG rendering (matplotlib, optional)
│   ├── palette.py           # colour -> decoration mapping
│   ├── img2hideout.py       # PNG -> Hideout (pillow, optional)
│   ├── cli.py               # `hideout-art` CLI entry point
│   └── constants.py         # known hashes, ART_TYPES, CANAL_HIDEOUT_BOUNDS
├── tests/                   # pytest test suite
│   ├── test_parser.py
│   ├── test_writer.py
│   ├── test_transforms.py
│   ├── test_img2hideout.py  # img2hideout smoke tests
│   ├── test_new_hashes.py   # 0.2.1/0.2.2 hashes + bounds + KI-9 fix
│   └── data/sample.hideout  # tiny synthetic test fixture
├── examples/                # example palette JSON + sample inputs
│   ├── palette.json         # 4-colour Canal Hideout base palette
│   ├── palette_warm.json    # 9-colour warm-tone palette (0.2.1, working)
│   ├── palette_2b.json      # template for cool-tone portraits (TODOs)
│   └── README.md
├── исходники/               # (0.2.2) user-provided reference exports:
│   │                          5 .hideout files + matching screenshots,
│   │                          source of the 18 new hashes and the
│   │                          Canal Hideout canvas bounds calibration
├── docs/
│   ├── format.md            # full .hideout format spec
│   └── screenshots/         # preview PNGs for the README
├── scripts/                 # one-off dev/exploration scripts
├── pyproject.toml           # PEP 621 packaging + ruff config
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── AGENTS.md                # navigation hints for AI assistants working on this repo
└── LICENSE
```

## Contributing

PRs welcome — especially new `KNOWN_HASHES` entries from observed hideouts.
See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the workflow, and
[`AGENTS.md`](AGENTS.md) if you are an AI assistant working on this repo.

## License

MIT. See [`LICENSE`](LICENSE).
