"""Generate test inputs for img2hideout first-run validation (TODO-1, v0.6.1).

Produces two PNG files in <repo>/examples/:

1. ``test_icon_heart.png`` — 200×250 simple black silhouette on white
   background. Sanity check: should produce ~40-50 placements.

2. ``test_portrait.png`` — downscaled (≈400×281) version of a portrait
   source. Real-world test: does img2hideout preserve a recognizable
   human figure on an 80-pixel-wide canvas?

Both PNGs are fully opaque (no alpha channel) so the caller must use
``--bg 255 255 255`` to skip the white background.

Set the PORTRAIT_SRC environment variable to override the default
portrait source path (defaults to /home/z/my-project/upload/...).

Run from repo root:
  python scripts/gen_test_images.py
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw

# Resolve repo root: this script lives in <repo>/scripts/
REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "examples"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def make_heart(width: int = 200, height: int = 250) -> Image.Image:
    """A two-tone heart on a white background. 200×250 px.

    Top half = pink (255,192,203) — matches Falling Sand decoration.
    Bottom half = green (46,125,50) — matches Long Grass decoration.
    This mirrors the user's reference screenshot (234156.jpg) where
    the heart is built from pink Falling Sand on top and green Long
    Grass on the bottom.
    """
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    cx, cy = width / 2, height / 2 + 20
    r = int(min(width, height) * 0.22)

    pink = (255, 192, 203)
    green = (46, 125, 50)

    # Top half of the heart (two lobes) — pink
    draw.ellipse((cx - 2.0 * r, cy - 1.6 * r, cx, cy + 0.4 * r), fill=pink)
    draw.ellipse((cx,           cy - 1.6 * r, cx + 2.0 * r, cy + 0.4 * r), fill=pink)
    draw.rectangle((cx - 2.0 * r + 4, cy - 0.9 * r, cx + 2.0 * r - 4, cy - 0.4 * r),
                   fill=pink)

    # Bottom triangle of the heart — green
    draw.polygon(
        [(cx - 2.0 * r + 4, cy - 0.4 * r),
         (cx + 2.0 * r - 4, cy - 0.4 * r),
         (cx,               cy + 1.8 * r)],
        fill=green,
    )

    # Overlap zone: blend pink → green via a thin olive band so the
    # palette matcher doesn't pick a wildly wrong decoration at the seam.
    draw.rectangle(
        (cx - 2.0 * r + 4, cy - 0.5 * r, cx + 2.0 * r - 4, cy - 0.2 * r),
        fill=(140, 100, 90),  # pinkish-brown transition
    )

    return img


def downscale_portrait(src: Path, target_width: int = 400) -> Image.Image:
    """Downscale the user's uploaded portrait to ~400 px wide."""
    img = Image.open(src).convert("RGB")
    h = max(1, int(img.height * target_width / img.width))
    return img.resize((target_width, h), Image.LANCZOS)


def main() -> None:
    heart = make_heart()
    heart_path = OUT_DIR / "test_icon_heart.png"
    heart.save(heart_path, optimize=True)
    print(f"Wrote {heart_path}  ({heart.size})")

    # Portrait source: env var override OR default upload location.
    src_env = os.environ.get("PORTRAIT_SRC")
    if src_env:
        src = Path(src_env)
    else:
        src = Path("/home/z/my-project/upload/Gemini_Generated_Image_6a5vf46a5vf46a5v.png")
    if not src.exists():
        print(f"WARN: source portrait not found at {src}, skipping. "
              f"Set PORTRAIT_SRC env var to point at your portrait file.")
    else:
        portrait = downscale_portrait(src, target_width=400)
        portrait_path = OUT_DIR / "test_portrait.png"
        portrait.save(portrait_path, optimize=True)
        print(f"Wrote {portrait_path}  ({portrait.size})")


if __name__ == "__main__":
    main()
