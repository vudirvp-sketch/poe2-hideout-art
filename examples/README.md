# Examples

This directory contains sample inputs you can use to test the toolkit.

## `palette.json`

A colour-to-decoration mapping for `hideout-art img2hideout`. Each entry
maps an RGB triple to a known decoration hash. Edit this file to use
different decorations or to add caps (`max_count`) per decoration.

### Usage

```bash
hideout-art img2hideout my_picture.png -o my_picture.hideout \
    --palette examples/palette.json \
    --scale 3 --width 100 \
    --hideout-name "Canal Hideout" --hideout-hash 60415
```

### How it works

1. The image is downscaled to `--width` pixels (aspect ratio preserved).
2. For each pixel, the closest palette entry is found by Euclidean RGB
   distance.
3. Pixel `(col, row)` is mapped to world coordinate
   `(origin_x + col*scale, origin_y + (h-1-row)*scale)` — note the row
   flip, because images store rows top-to-bottom but world y grows
   upward.
4. Pure-black pixels (`(0,0,0)`, within `--background-threshold`) are
   treated as transparent and skipped.

### Tips

- **Keep `--width` ≤ 150.** A 150×150 image with 4 colours produces
  ~22,500 placements, which is near the practical limit the game can
  handle smoothly.
- **Use a limited colour palette in the source image.** The closer your
  image's colours are to the palette entries, the cleaner the result.
  Pre-quantise the image (e.g. in GIMP: Image → Mode → Indexed) for
  best results.
- **`scale` controls how spread out the composition is.** Larger scale
  = fewer overlaps but bigger footprint.

## Producing a source image

The simplest pipeline:

1. Find or draw an image.
2. Crop to a roughly 1:1 or 4:3 aspect ratio.
3. Quantise to 4-8 colours using your image editor.
4. Match each colour to one of the palette entries above.
5. Save as PNG and run `hideout-art img2hideout`.
