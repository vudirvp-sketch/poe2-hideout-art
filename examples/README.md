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

## `palette_warm.json` (new in 0.2.1)

A fully working 9-colour palette for warm-tone compositions — deserts,
wood/stone textures, autumn scenes. Built from the original 4 Canal
Hideout colours plus the 5 new Maraket/Coastal Pebble decorations
discovered from user-provided exports:

| Decoration          | RGB                | Role                       |
|---------------------|--------------------|----------------------------|
| Sand Tussock        | (78, 52, 46)       | deep shadow (darkest)      |
| Maraket Treasures   | (108, 91, 83)      | dark warm gray             |
| Maraket Rubble      | (138, 120, 94)     | warm tan/khaki (workhorse) |
| Maraket Ornament    | (136, 120, 97)     | warm tan (textural alt)    |
| Coastal Pebble      | (134, 115, 94)     | warm tan (noise alt)       |
| Maraket Samovar     | (148, 133, 115)    | light warm gray            |
| Long Grass          | (46, 125, 50)      | body green                 |
| Fringe Moss         | (139, 195, 74)     | light green                |
| Falling Sand        | (248, 187, 208)    | pink accent                |

### Usage

```bash
hideout-art img2hideout desert.png -o desert.hideout \
    --palette examples/palette_warm.json \
    --tile-size 23 --width 80 --dither \
    --hideout-name "Canal Hideout" --hideout-hash 60415 \
    --preview
```

## `palette_2b.json`

A **template** for a 10-colour palette suitable for cool-tone portraits —
specifically, for a character like 2B from NieR: Automata. The default
4-colour palette cannot render a portrait: it has no white, black, gray,
silver, skin-tone, or red. This template defines the colour ROLES you
need; the actual decoration names are left as `TODO_*` placeholders.

**Note (0.2.1):** the 5 new warm-tone decorations added in 0.2.1 do NOT
fill these cool-tone TODOs. They are warm tan/gray, not the neutral cool
gray that 2B's sword/dress shadows require. For warm-tone art, use
`palette_warm.json` (which loads cleanly today). To complete
`palette_2b.json`, the user must find in-game: white (dress), black
(blindfold), cool neutral gray (sword), silver (blade highlights),
skin tone, red (emblem).

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
