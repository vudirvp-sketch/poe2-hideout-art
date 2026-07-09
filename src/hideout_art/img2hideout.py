"""Convert a PNG/JPG image into a Hideout composition.

Algorithm
---------
1. Load the image with Pillow and downscale to a target width
   (default: ~120 px to keep placement count manageable).
2. For each pixel, find the closest palette entry by Euclidean RGB
   distance.
3. Map the pixel's (col, row) to world (x, y) using a configurable
   scale and origin. By default y grows upward (top row of the image
   becomes the highest y).
4. Emit one ``Placement`` per non-background pixel.

Optional: ``max_count`` per palette entry is respected — once a
decoration hits its cap, subsequent pixels that would map to it are
skipped.

This module is **not** imported by ``hideout_art/__init__.py`` because
Pillow is a heavier optional dependency.
"""

from __future__ import annotations

from pathlib import Path

from .constants import KNOWN_HASHES
from .palette import ColorEntry, Palette, default_palette
from .parser import Hideout, Placement


def _closest_entry(rgb: tuple[int, int, int], palette: Palette) -> ColorEntry | None:
    best: ColorEntry | None = None
    best_d2 = float("inf")
    for e in palette.entries:
        dr = rgb[0] - e.color[0]
        dg = rgb[1] - e.color[1]
        db = rgb[2] - e.color[2]
        d2 = dr * dr + dg * dg + db * db
        if d2 < best_d2:
            best_d2 = d2
            best = e
    return best


def image_to_hideout(
    image_path: str | Path,
    *,
    palette: Palette | None = None,
    target_width: int = 120,
    scale: int = 2,           # world units per pixel
    origin_x: int = 700,
    origin_y: int = 550,
    background: tuple[int, int, int] | None = (0, 0, 0),
    background_threshold: int = 30,
    hideout_name: str = "Imported",
    hideout_hash: int = 0,
    language: str = "English",
) -> Hideout:
    """Convert an image file into a Hideout.

    Parameters
    ----------
    image_path : path-like
        PNG/JPG/etc. Pillow-readable image.
    palette : Palette, optional
        Colour-to-decoration mapping. Defaults to ``default_palette()``.
    target_width : int
        Downscale the image so its width is this many pixels. Aspect
        ratio is preserved.
    scale : int
        World units per pixel. Larger = spread-out composition.
    origin_x, origin_y : int
        World coordinate of the BOTTOM-LEFT pixel of the image (y grows
        upward, so the bottom row corresponds to ``origin_y``).
    background : (r,g,b) or None
        If set, pixels within ``background_threshold`` of this colour
        are skipped (treated as transparent).
    hideout_name, hideout_hash, language : str / int
        Header fields for the resulting .hideout file.

    Returns
    -------
    Hideout
    """
    try:
        from PIL import Image
    except ImportError as e:
        raise ImportError(
            "Pillow is required for image_to_hideout. "
            "Install with: pip install hideout-art[image]"
        ) from e

    palette = palette or default_palette()

    img = Image.open(image_path).convert("RGB")
    if img.width > target_width:
        new_h = max(1, int(img.height * target_width / img.width))
        img = img.resize((target_width, new_h))

    w, h = img.size
    pixels = img.load()

    # Track per-entry counts to honour max_count.
    counts: dict[int, int] = {id(e): 0 for e in palette.entries}

    placements: list[Placement] = []
    for row in range(h):
        # row=0 is the TOP of the image; we want the top of the image
        # to be the highest y, so y = origin_y + (h - 1 - row) * scale
        y = origin_y + (h - 1 - row) * scale
        for col in range(w):
            x = origin_x + col * scale
            rgb = pixels[col, row]

            if background is not None:
                dr = rgb[0] - background[0]
                dg = rgb[1] - background[1]
                db = rgb[2] - background[2]
                if dr * dr + dg * dg + db * db <= background_threshold * background_threshold:
                    continue

            entry = _closest_entry(rgb, palette)
            if entry is None:
                continue
            if entry.max_count is not None and counts[id(entry)] >= entry.max_count:
                continue
            counts[id(entry)] += 1

            placements.append(Placement(
                name=entry.decoration,
                hash=KNOWN_HASHES[entry.decoration],
                x=x,
                y=y,
                r=0,
                fv=0,
            ))

    return Hideout(
        version=1,
        language=language,
        hideout_name=hideout_name,
        hideout_hash=hideout_hash,
        placements=placements,
    )
