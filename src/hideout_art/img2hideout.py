"""Convert a PNG/JPG image into a Hideout composition.

Algorithm
---------
1. Load the image with Pillow and downscale to a target width
   (default: ~120 px to keep placement count manageable).
2. For each pixel, decide whether to skip it:

   * if the image has an **alpha channel**, pixels with ``alpha < alpha_threshold``
     are skipped (transparent);
   * otherwise, pixels within ``background_threshold`` of ``background``
     colour are skipped (legacy behaviour).

3. Map the surviving pixel to a palette entry. Two strategies:

   * **nearest** (default): Euclidean (or weighted / redmean) RGB distance
     to each palette colour, pick the smallest;
   * **dither** (Floyd-Steinberg): same distance metric, but the residual
     error is propagated to neighbours → much smoother gradients.

4. Map pixel (col, row) to world (x, y):

   * ``y`` grows upward (top row of image → highest ``y``);
   * ``scale`` = world units per pixel;
   * ``step`` = place a decoration every Nth pixel (default 1 = every pixel).
     ``step > 1`` reduces placement count and lets each decoration breathe.

5. Optionally skip placements outside ``bounds`` (world-coord rectangle).
   Useful when the user has «outlined» the hideout's playable area.

6. Optionally jitter ``r`` (multiples of 15°) and ``variant`` per placement
   for visual variety. Default OFF — preserves the original rigid look.

7. Optionally write a PNG preview of the resulting hideout alongside.

All new options are opt-in; defaults reproduce the pre-1.1 behaviour
byte-for-byte on a non-alpha, non-dithered input.

This module is **not** imported by ``hideout_art/__init__.py`` because
Pillow is a heavier optional dependency.
"""

from __future__ import annotations

import random
from pathlib import Path

from .constants import KNOWN_HASHES, ROTATION_MODULUS, localize_name
from .palette import ColorEntry, Palette, default_palette
from .parser import Hideout, Placement

# ---------------------------------------------------------------------------
# Color distance metrics
# ---------------------------------------------------------------------------

# Weights for the "weighted" metric — standard ITU-R BT.601 luma weights.
_LUMA_R, _LUMA_G, _LUMA_B = 0.299, 0.587, 0.114


def _dist_rgb(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    dr = a[0] - b[0]
    dg = a[1] - b[1]
    db = a[2] - b[2]
    return dr * dr + dg * dg + db * db


def _dist_weighted(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """Luminance-weighted Euclidean distance.

    Prevents dark-green from matching dark-brown just because their RGB
    magnitudes are similar — green channel counts more, so the green
    decoration wins for green-ish pixels.
    """
    dr = (a[0] - b[0]) * _LUMA_R
    dg = (a[1] - b[1]) * _LUMA_G
    db = (a[2] - b[2]) * _LUMA_B
    return dr * dr + dg * dg + db * db


def _dist_redmean(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """redmean — a cheap perceptual metric that works well for close colours.

    See https://www.compuphase.com/cmetric.htm. Computationally tiny but
    noticeably better than plain Euclidean for the red/orange/brown range.
    """
    r_mean = (a[0] + b[0]) / 2.0
    dr = a[0] - b[0]
    dg = a[1] - b[1]
    db = a[2] - b[2]
    return (
        (2.0 + r_mean / 256.0) * dr * dr
        + 4.0 * dg * dg
        + (2.0 + (255.0 - r_mean) / 256.0) * db * db
    )


_METRICS = {
    "rgb": _dist_rgb,
    "weighted": _dist_weighted,
    "redmean": _dist_redmean,
}


def _closest_entry(
    rgb: tuple[int, int, int],
    palette: Palette,
    metric: str = "rgb",
) -> ColorEntry | None:
    fn = _METRICS.get(metric, _dist_rgb)
    best: ColorEntry | None = None
    best_d = float("inf")
    for e in palette.entries:
        d = fn(rgb, e.color)
        if d < best_d:
            best_d = d
            best = e
    return best


# ---------------------------------------------------------------------------
# PIL resample filter lookup
# ---------------------------------------------------------------------------

def _resample_filter(name: str):
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        return None
    # Lazy lookup so we don't import PIL at module load time.
    table = {
        "nearest": Image.NEAREST,
        "bilinear": Image.BILINEAR,
        "bicubic": Image.BICUBIC,
        "lanczos": Image.LANCZOS,
    }
    return table.get(name.lower(), Image.BICUBIC)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def image_to_hideout(
    image_path: str | Path,
    *,
    palette: Palette | None = None,
    target_width: int = 120,
    scale: int = 2,
    step: int | None = None,
    tile_size: int | None = None,
    origin_x: int = 700,
    origin_y: int = 550,
    background: tuple[int, int, int] | None = (0, 0, 0),
    background_threshold: int = 30,
    alpha_threshold: int = 32,
    use_alpha: bool = True,
    color_metric: str = "rgb",
    dither: bool = False,
    jitter: bool = False,
    jitter_seed: int = 0,
    jitter_variants: int = 8,
    bounds: tuple[int, int, int, int] | None = None,
    resample: str = "bicubic",
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
    step : int or None
        Place a decoration every ``step``-th pixel in both x and y.
        ``step=2`` halves the placement count and lets each decoration
        breathe. If ``None`` and ``tile_size`` is given, ``step`` is
        auto-computed as ``max(1, round(tile_size / scale))`` so that
        one decoration is placed per tile (no overlap, no gaps).
    tile_size : int or None
        Decoration footprint in world units. When set, overrides
        ``step`` (see above). Use this when you know the decoration's
        physical size — typically ~23 world units for a 1-tile
        decoration (see ``DEFAULT_TILE_SIZE_WORLD_UNITS``). Lets the
        system calibrate density automatically; closes KI-1.
    origin_x, origin_y : int
        World coordinate of the BOTTOM-LEFT pixel of the image (y grows
        upward, so the bottom row corresponds to ``origin_y``).
    background : (r,g,b) or None
        If set, pixels within ``background_threshold`` of this colour
        are skipped (treated as transparent). Ignored when the image
        has an alpha channel and ``use_alpha=True``.
    background_threshold : int
        Euclidean RGB distance (not squared) under which a pixel is
        treated as background.
    alpha_threshold : int
        For images with alpha: pixels with ``alpha < alpha_threshold``
        are skipped.
    use_alpha : bool
        Whether to honour the alpha channel when present. Default True.
        Set to False to force background-colour matching even on RGBA
        images (legacy behaviour).
    color_metric : str
        One of ``"rgb"`` (default, Euclidean), ``"weighted"`` (luminance),
        ``"redmean"`` (perceptual, good for warm colours).
    dither : bool
        If True, use Floyd-Steinberg error diffusion. Default False.
    jitter : bool
        If True, randomise ``r`` (multiples of 15°) and ``variant`` per
        placement. Default False.
    jitter_seed : int
        RNG seed for reproducible jitter. 0 = unpredictable.
    jitter_variants : int
        Max variant index when jittering (typical observed range: 0..8).
    bounds : (x_min, y_min, x_max, y_max) or None
        If set, skip placements whose world (x, y) falls outside this
        rectangle. Useful when the user has «outlined» the hideout.
        For Canal Hideout, use the pre-calibrated ``CANAL_HIDEOUT_BOUNDS``
        constant from ``hideout_art.constants`` (derived from a user
        outline of 11 Cordilina placements around the playable perimeter).
    resample : str
        PIL downscaling filter: ``"nearest"``, ``"bilinear"``,
        ``"bicubic"`` (default), ``"lanczos"``. For pixel-art sources
        prefer ``"nearest"`` to preserve crisp edges.
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

    # ----- resolve step from tile_size (KI-1 calibration) -----------------
    # If tile_size is given, auto-compute step so that adjacent placements
    # are ~tile_size world units apart (i.e. one decoration per tile).
    # If both step and tile_size are None, default step=1 (legacy behaviour).
    if step is None:
        if tile_size is not None:
            if tile_size <= 0:
                raise ValueError(
                    f"tile_size must be > 0, got {tile_size}"
                )
            step = max(1, round(tile_size / scale))
        else:
            step = 1
    elif tile_size is not None:
        # Both explicitly set: prefer tile_size (it's the more physical
        # parameter) but warn via ValueError so the user notices.
        raise ValueError(
            "Pass either 'step' or 'tile_size', not both. "
            f"Got step={step}, tile_size={tile_size}."
        )

    palette = palette or default_palette()
    rng = random.Random(jitter_seed if jitter_seed else None)

    # ----- load + downscale ------------------------------------------------
    img = Image.open(image_path)
    has_alpha = use_alpha and "A" in img.getbands()
    if has_alpha:
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    if img.width > target_width:
        new_h = max(1, int(img.height * target_width / img.width))
        img = img.resize((target_width, new_h), _resample_filter(resample))

    w, h = img.size
    pixels = img.load()

    # Build a mutable RGB buffer (and a separate alpha mask if applicable).
    # We need mutability for Floyd-Steinberg; even without dither, working
    # from a flat list is faster than PIL's per-pixel access.
    rgb_buf: list[list[tuple[int, int, int]]] = []
    alpha_mask: list[list[int]] | None = None if not has_alpha else []
    for row in range(h):
        rgb_row: list[tuple[int, int, int]] = []
        a_row: list[int] = []
        for col in range(w):
            px = pixels[col, row]
            if has_alpha:
                r, g, b, a = px  # type: ignore[misc]
                rgb_row.append((r, g, b))
                a_row.append(a)
            else:
                r, g, b = px  # type: ignore[misc]
                rgb_row.append((r, g, b))
        rgb_buf.append(rgb_row)
        if has_alpha:
            assert alpha_mask is not None
            alpha_mask.append(a_row)

    # ----- per-pixel skip predicate ---------------------------------------
    def is_skipped(row: int, col: int, rgb: tuple[int, int, int]) -> bool:
        if has_alpha:
            assert alpha_mask is not None
            if alpha_mask[row][col] < alpha_threshold:
                return True
        elif background is not None:
            dr = rgb[0] - background[0]
            dg = rgb[1] - background[1]
            db = rgb[2] - background[2]
            if dr * dr + dg * dg + db * db <= background_threshold * background_threshold:
                return True
        return False

    # ----- sample loop -----------------------------------------------------
    counts: dict[int, int] = {id(e): 0 for e in palette.entries}
    placements: list[Placement] = []

    # Rotation step = 15° = 65536 / 24
    r_step = ROTATION_MODULUS // 24

    for row in range(0, h, step):
        y = origin_y + (h - 1 - row) * scale
        for col in range(0, w, step):
            x = origin_x + col * scale
            rgb = rgb_buf[row][col]

            if is_skipped(row, col, rgb):
                continue

            entry = _closest_entry(rgb, palette, metric=color_metric)
            if entry is None:
                continue
            if entry.max_count is not None and counts[id(entry)] >= entry.max_count:
                continue
            counts[id(entry)] += 1

            # Bounds check (world coords)
            if bounds is not None:
                x_min, y_min, x_max, y_max = bounds
                if x < x_min or x > x_max or y < y_min or y > y_max:
                    continue

            # Jitter (optional)
            r_val = 0
            fv_val = 0
            if jitter:
                r_val = rng.randint(0, 23) * r_step
                fv_val = rng.randint(0, max(0, jitter_variants - 1))

            placements.append(Placement(
                name=localize_name(entry.decoration, language),
                hash=KNOWN_HASHES[entry.decoration],
                x=x,
                y=y,
                r=r_val,
                fv=fv_val,
            ))

            # ----- Floyd-Steinberg error diffusion ----------------------
            if dither:
                target = entry.color
                err = (
                    rgb[0] - target[0],
                    rgb[1] - target[1],
                    rgb[2] - target[2],
                )
                _diffuse(rgb_buf, row, col + 1, err, 7 / 16)
                _diffuse(rgb_buf, row + 1, col - 1, err, 3 / 16)
                _diffuse(rgb_buf, row + 1, col, err, 5 / 16)
                _diffuse(rgb_buf, row + 1, col + 1, err, 1 / 16)

    return Hideout(
        version=1,
        language=language,
        hideout_name=hideout_name,
        hideout_hash=hideout_hash,
        placements=placements,
    )


def _diffuse(
    buf: list[list[tuple[int, int, int]]],
    row: int,
    col: int,
    err: tuple[int, int, int],
    coeff: float,
) -> None:
    """Propagate quantisation error to a neighbour pixel (in place)."""
    if row < 0 or row >= len(buf):
        return
    line = buf[row]
    if col < 0 or col >= len(line):
        return
    r, g, b = line[col]
    line[col] = (
        max(0, min(255, int(round(r + err[0] * coeff)))),
        max(0, min(255, int(round(g + err[1] * coeff)))),
        max(0, min(255, int(round(b + err[2] * coeff)))),
    )
