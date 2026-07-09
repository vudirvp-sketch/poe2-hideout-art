# Examples

This directory contains sample inputs you can use to test the toolkit.

## `palette.json`

A colour-to-decoration mapping for `hideout-art img2hideout`. Each entry
maps an RGB triple to a known decoration hash. Edit this file to use
different decorations or to add caps (`max_count`) per decoration.

This is the **minimal 4-colour palette** observed in the Canal Hideout
reference composition: pink (Falling Sand), green (Long Grass),
light-green (Fringe Moss), dark-brown (Sand Tussock). Good for abstract
shapes; not enough for portraits.

### Usage

```bash
hideout-art img2hideout my_picture.png -o my_picture.hideout \
    --palette examples/palette.json \
    --scale 3 --width 100 --step 2 \
    --hideout-name "Canal Hideout" --hideout-hash 60415 \
    --preview
```

### How it works

1. The image is downscaled to `--width` pixels (aspect ratio preserved).
2. For each pixel:
   - if the PNG has an alpha channel and `alpha < --alpha-threshold`,
     skip;
   - otherwise, if the pixel is within `--bg-threshold` of `--bg R G B`
     (default black), skip;
   - otherwise, find the closest palette entry by `--color-metric`
     (default Euclidean RGB; `weighted` / `redmean` for better perceptual
     matching).
3. Pixel `(col, row)` is mapped to world coordinate
   `(origin_x + col*scale, origin_y + (h-1-row)*scale)` — note the row
   flip, because images store rows top-to-bottom but world y grows
   upward.
4. `--step N` places a decoration every Nth pixel (default 1).
5. `--bounds x_min,y_min,x_max,y_max` skips placements outside a
   world-coord rectangle — use to respect hideout boundaries.
6. `--dither` enables Floyd-Steinberg error diffusion for smoother
   gradients.
7. `--jitter` randomises `r` (15° steps) and `variant` per placement.

See `docs/img2hideout.md` for the full parameter reference.

### Tips

- **Keep `--width` ≤ 150.** A 150×150 image with 4 colours produces
  ~22,500 placements, which is near the practical limit the game can
  handle smoothly.
- **`--step 2` is usually the right starting point.** It halves the
  placement count and lets each decoration breathe — the game's tiles
  are larger than the default `--scale 2` implies.
- **Use a limited colour palette in the source image.** The closer your
  image's colours are to the palette entries, the cleaner the result.
  Pre-quantise the image (e.g. in GIMP: Image → Mode → Indexed) for
  best results.
- **`scale` controls how spread out the composition is.** Larger scale
  = fewer overlaps but bigger footprint.

## `palette_2b.json`

A **template** for a 10-colour palette suitable for portraits —
specifically, for a character like 2B from NieR: Automata. The default
4-colour palette cannot render a portrait: it has no white, black, gray,
silver, skin-tone, or red. This template defines the colour ROLES you
need; the actual decoration names are left as `TODO_*` placeholders.

### Filling in the template

1. In the game, place ONE of each missing decoration in your hideout.
2. Export the hideout to `.hideout`.
3. Run `hideout-art inspect path/to/export.hideout`.
4. The "Unknown hashes" section lists the hash for each unknown name.
5. Add the entry to `KNOWN_HASHES` in `src/hideout_art/constants.py`.
6. Add the decoration name to `ART_TYPES` in the same file (if it's
   purely artistic).
7. Replace the `TODO_*` entries in `palette_2b.json` with the actual
   decoration names.
8. Run `hideout-art img2hideout portrait.png --palette examples/palette_2b.json ...`.

Until the TODOs are filled in, `Palette.from_json_file()` raises a
`ValueError` listing the known decorations — by design.

## Producing a source image

The simplest pipeline:

1. Find or draw an image.
2. Crop to a roughly 1:1 or 4:3 aspect ratio.
3. Quantise to 4-8 colours using your image editor.
4. Match each colour to one of the palette entries above.
5. Save as PNG and run `hideout-art img2hideout`.

For pixel-art sources, add `--resample nearest` to preserve crisp edges
during downscaling. For photos, `--resample lanczos` is best.
