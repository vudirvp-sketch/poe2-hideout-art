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

## What's gitignored

`*.json` outputs in this directory (e.g. `sampled_*.json`,
`diagnostic_*.png`, `decoration_footprints.json`) are kept locally for
debugging but not committed. The scripts themselves and this README
are tracked.
