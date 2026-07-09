# Scripts

One-off dev and exploration scripts. **Do not** add scripts here that
users need — those belong in `src/hideout_art/` as proper modules with
tests. This directory is for things like:

- bulk-rebuilding previews
- scraping hashes from a folder of `.hideout` exports
- ad-hoc analysis of an unusual file
- pixel-sampling screenshots to get ground-truth RGB

Scripts here may depend on `matplotlib`, `pillow`, etc. without being
declared in `pyproject.toml`.

## Available scripts

| File | Purpose |
|---|---|
| `bulk_preview.py` | Render PNGs for every `.hideout` in a folder |
| `scrape_hashes.py` | Walk a folder of exports and print unknown hashes |
| `measure_decorations.py` | Measure decoration placement footprints from `исходники/*.hideout` (re-run when new decorations are added; output goes to `decoration_footprints.json`, gitignored) |
| `sample_pixels.py` | **(0.2.6)** Sample real pixel RGB under each art placement — closes KI-11. Auto or manual world→pixel calibration, diagnostic overlay PNG, JSON report. See usage below. |
| `sample_all.py` | **(0.2.6)** Convenience wrapper: runs `sample_pixels.py` on all 7 `исходники/` screenshot+hideout pairs and consolidates into `sampled_all.json`. |
| `draw_primitives.py` | **(0.2.7, defaults updated 0.2.8)** Inject the curated 5-shape drawing-primitives composition (vertical lines + hollow circle + filled circle + S-snake + thick line with contours) into the centre of an existing `.hideout` file. Strictly additive. See usage below. |
| `render_primitives_preview.py` | **(0.2.7)** Render a colour-coded PNG preview of a hideout with per-decoration legend, Canal Hideout canvas outline, and centre marker. |

## `sample_pixels.py` — pixel sampling for ground-truth RGB

The core tool for replacing noisy VLM-estimated RGB (KI-11) with
pixel-exact measurements. Takes a `.hideout` file (with placement
coordinates) + a matching `.jpg` screenshot and:

1. Calibrates world-coordinates → pixel-coordinates (auto or manual).
2. Samples a circular window (default radius 4 wu ≈ 1/6 tile) around
   each placement's centre.
3. Computes median / mean / p25 / p75 RGB per placement and per
   decoration type.
4. Writes a JSON report and (optionally) a diagnostic overlay PNG.

### Quick start (auto-calibration)

```bash
python scripts/sample_pixels.py \
    "исходники/камни и кустарники.hideout" \
    "исходники/камни и кустарники.jpg" \
    --world-bbox functional \
    --include-functional \
    --output scripts/sampled_камни.json \
    --diagnostic scripts/diagnostic_камни.png
```

### Calibration modes

The world-coordinate → pixel-coordinate transform is the hard part.
Each screenshot has a different crop / zoom, so we cannot just linearly
map world coords to image coords.

**Auto (`--world-bbox canal`)** — default. Maps `CANAL_HIDEOUT_BOUNDS =
(700, 540, 860, 775)` onto the screenshot with UI-aware margins
(5% sides, 5% top, 20% bottom for skill bar). Works well when all art
placements fall inside the Canal canvas, but **misses anchors at x<700**
(Ange, Reforging Bench, Salvage Bench, Well).

**Auto (`--world-bbox functional`)** — recommended. Auto-derives the
world bbox from all non-art placements in the .hideout file. Captures
all 18 functional anchors (Stash, Waypoint, NPCs) so you can sanity-check
calibration by verifying Stash gives a believable brown wood colour
(R > G > B, brightness 64-182).

**Manual (`--calibration anchors.json`)** — most accurate. Provide ≥2
anchor correspondences; the script solves a least-squares affine fit.
Required for resolving KI-12 (Marble-серия pixel-sampling issue).

```json
{
  "anchors": [
    {"world": [811, 519], "pixel": [1218, 899], "name": "Stash"},
    {"world": [697, 660], "pixel": [387, 463],  "name": "Waypoint"},
    {"world": [683, 694], "pixel": [350, 580],  "name": "Well"}
  ]
}
```

### Diagnostic overlay

Always pass `--diagnostic path/to/overlay.png`. The overlay draws:

- White rings + labels on functional placements (Stash, Waypoint, NPCs)
  — verify these line up with the visible in-game objects.
- Coloured filled circles on art placements — verify these line up with
  the visible decorations.
- Thin coloured circles showing the sampling window radius.

If the rings/dots don't match the visible objects, calibration is off.
Adjust margins (auto mode) or fix anchor pixel coords (manual mode).

### Sampling window

The default `--sample-radius-wu 4.0` corresponds to ~1/6 of a tile
(23 wu) — a small window around the placement centre. Increase to 8-12
for larger decorations (Beech Tree, Marble Table) but beware of
capturing neighbouring decorations.

### Output JSON

Per-decoration: `median_rgb`, `mean_rgb`, `p25_rgb`, `p75_rgb`,
`n_placements`, `per_placement` (with pixel coords + per-placement
RGB). Plus `_meta` with calibration info for reproducibility.

### All 7 screenshots at once

```bash
python scripts/sample_all.py
```

Consolidates results to `scripts/sampled_all.json` — the source for
the `_pixel_sampling_summary_0_2_6` block in `examples/palette_2b.json`.

## `draw_primitives.py` — drawing primitives in world coords (0.2.7, defaults 0.2.8)

When `img2hideout` rasterises a PNG, geometric shapes (circles, lines,
S-curves) become noisy dot clouds after palette quantisation. This
script draws them *directly* in world coordinates using art decorations,
so each shape is clean and recognisable in-game.

The script uses `src/hideout_art/primitives.py` — see that module for
the per-shape API. Core (0.2.7): `line`, `polyline`, `hollow_circle`,
`filled_circle`, `s_snake`, `thick_line_with_contours`,
`center_composition`. Mosaic/bas-relief (0.2.8 NEW): `arc`, `rectangle`,
`polygon`, `grid` (only `center_composition` is wired into the CLI; the
mosaic primitives are Python-API only for now).

### Quick start

```bash
python scripts/draw_primitives.py \
    "чистый холст.hideout" \
    -o "чистый холст с примитивами.hideout" \
    --center 780 657 \
    --bounds-check \
    --preview preview.png
```

This loads the source hideout (30 placements — Canal Hideout functional
objects + NPCs + 11 Cordilina boundary + 1 Petrified Cave Figure),
appends 63 art placements for the 5 core primitives, and writes a
93-placement output file. All new placements are inside
`CANAL_HIDEOUT_BOUNDS = (700, 540, 860, 775)` — `--bounds-check` fails
otherwise.

### The 5 core primitives (curated `center_composition`)

| Shape | Default decoration | Position (relative to centre) |
|---|---|---|
| 3 vertical parallel lines (length 80 wu) | Long Grass | top-left, x = cx−60..−45 |
| Hollow circle (radius 18 wu) | Maraket Rubble | top-centre, (cx, cy−50) |
| Filled circle (radius 14 wu) | Coastal Pebble | top-right, (cx+45, cy−50) |
| S-snake (height 60, width 25 wu) | Maraket Rubble *(0.2.8: was Sand Tussock)* | bottom-left, (cx−45, cy+35) |
| Thick line with contours (length 50, **thickness 28** wu) | Small Coastal Stone (outline) + Long Grass (fill) *(0.2.8: was thickness 14 + Coastal Pebble fill)* | bottom-right, (cx+5..+55, cy+35) |

### 4 mosaic / bas-relief primitives (0.2.8, Python API only)

These are NOT wired into `draw_primitives.py` CLI yet — call them
directly from Python:

| Shape | Use case | Example |
|---|---|---|
| `arc(cx, cy, radius, start_deg, end_deg, opts)` | Arches, semicircle caps, bas-relief curved corners | `arc(780, 657, 30, 0, 180, opts)` — upper half-ring |
| `rectangle(x0, y0, x1, y1, opts)` | Hollow borders, picture frames | `rectangle(720, 580, 840, 720, opts)` |
| `polygon(cx, cy, radius, n_sides, opts, rotation_deg=0)` | Triangles, squares, hexagons, octagons — mosaic tiles | `polygon(780, 657, 30, 6, opts)` — hexagon |
| `grid(x0, y0, x1, y1, opts, cols, rows, include_border=True)` | Mosaic tile fields, pointillism fills, bas-relief textures | `grid(720, 580, 840, 720, opts, cols=5, rows=5)` — 5×5 lattice |

### Options (CLI)

- `--center X Y` (default: 780 657) — centre of the composition.
- `--bounds-check` — fail if any new placement falls outside Canal
  Hideout bounds.
- `--preview PATH` — render a default PNG preview.
- `--<shape>-decoration NAME` — override the decoration for any shape
  (e.g. `--line-decoration Maraket Rubble`). Defaults: KI-14/15 fix
  baked in (S-snake=Maraket Rubble, thick fill=Long Grass).
- `--spacing-override N` — override the auto-derived placement spacing
  (in wu) for ALL primitives. Default: per-decoration `min_spacing_wu`
  from `DECORATION_FOOTPRINT_CATALOG`.

### Spacing

Each decoration has a measured `min_spacing_wu` in
`DECORATION_FOOTPRINT_CATALOG` — the closest observed pair distance in
`исходники/*.hideout`. The primitives use this as the placement spacing
so neighbouring decorations sit at the same density the user observed
in real exports. Decorations without observed samples fall back to 15 wu.

Override per-call with `--spacing-override N` if you need tighter or
looser placement. Beware: tighter than `min_spacing_wu` may cause
visible sprite overlap in-game (KI-10).

### Статус проверки в игре

Визуальная проверка (0.2.7, 2 скриншота): 3/5 фигур узнаваемы (vertical
lines, hollow circle, filled circle), 2/5 нужно доработать (S-snake,
thick_line) → заведены KI-14/15. В 0.2.8 оба фикса применены (см.
таблицу выше). **Ожидает повторной визуальной проверки пользователем**
(цель: 5/5 узнаваемых фигур). См. `STATUS.md` → KI-13/14/15.

## `render_primitives_preview.py` — colour-coded preview (0.2.7)

A thicker PNG preview than the default `hideout-art preview` command.
Renders:

- Each art decoration as a distinct colour dot (one colour per hash).
- Each functional object as a blue square with a name label.
- The Canal Hideout canvas outline as a grey rectangle.
- The composition centre as a red crosshair.

Useful for visually checking primitive layouts before importing in-game.

```bash
python scripts/render_primitives_preview.py \
    "чистый холст с примитивами.hideout" \
    preview.png
```

## What's gitignored

`*.json` outputs in this directory (e.g. `sampled_*.json`,
`diagnostic_*.png`, `decoration_footprints.json`) are kept locally for
debugging but not committed. The scripts themselves and this README
are tracked.
