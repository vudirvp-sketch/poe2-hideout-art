"""Run img2hideout on the two test images (v0.6.2 — high density).

For each input PNG:
  1. Convert to .hideout using examples/palette_canal_bright.json
  2. Skip white background (--bg 255 255 255 --no-alpha)
  3. Clip to Canal Hideout playable canvas (--bounds canal)
  4. Use redmean metric (good for warm + bright colours)
  5. HIGH DENSITY: step=1, scale=2 → placements every 2 wu
     (matches user reference screenshot 234156.jpg — dense, no gaps)
  6. Render a PNG preview alongside the .hideout

v0.6.2 changes vs v0.6.1:
  - Palette: palette_canal_bright.json (Falling Sand pink + Long Grass green
    + Fringe Moss light-green + Sand Tussock dark + Camp Gear very-dark)
    instead of palette_canal_warm.json (8 brown/tan decors).
  - Density: step=1, scale=2 (every 2 wu) instead of tile_size=12 (every 12 wu).
    4-6× more placements → dense, "sploche"-like look matching user reference.
  - Heart input: now pink+green (matches user reference 234156.jpg),
    not black silhouette.

Outputs go to:
  <repo>/download/
  heart_v062.hideout           + heart_v062.preview.png
  portrait_v062.hideout        + portrait_v062.preview.png
  img2hideout_report_v062.txt  — quick sanity summary

Run from repo root:
  python scripts/run_img2hideout_test.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Resolve repo root: this script lives in <repo>/scripts/
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from hideout_art.img2hideout import image_to_hideout
from hideout_art.palette import Palette
from hideout_art.constants import CANAL_HIDEOUT_BOUNDS
from hideout_art.writer import write_hideout
from hideout_art.preview import render_png

OUT_DIR = REPO / "download"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PALETTE = Palette.from_json_file(REPO / "examples/palette_canal_bright.json")

# Common kwargs: white background skip, redmean metric,
# HIGH DENSITY (step=1, scale=2 → placement every 2 wu),
# clip to Canal Hideout bounds.
# Origin is centered in Canal Hideout canvas (700,540,860,775):
#   canvas center = (780, 657). Each image is shifted so its center
#   lands on (780, 657) — see per-image origin override below.
COMMON = dict(
    palette=PALETTE,
    bounds=CANAL_HIDEOUT_BOUNDS,
    background=(255, 255, 255),
    background_threshold=30,
    use_alpha=False,             # images are RGB, force bg-skip path
    color_metric="redmean",
    step=1,                      # every pixel → maximum density
    scale=2,                     # 2 wu per pixel → 2 wu between placements
    hideout_name="Imported",
    hideout_hash=60415,          # Canal Hideout
    language="Russian",
    resample="lanczos",
)

# Canal Hideout canvas center (for centring each image)
_CANVAS_CX = (CANAL_HIDEOUT_BOUNDS[0] + CANAL_HIDEOUT_BOUNDS[2]) // 2  # 780
_CANVAS_CY = (CANAL_HIDEOUT_BOUNDS[1] + CANAL_HIDEOUT_BOUNDS[3]) // 2  # 657


def _centered_origin(target_width: int, target_height: int, scale: int) -> tuple[int, int]:
    """Compute (origin_x, origin_y) so the image centre lands on canvas centre.

    y grows upward: origin_y is the BOTTOM of the image, so
    origin_y = canvas_center_y - target_height * scale / 2.
    """
    origin_x = _CANVAS_CX - (target_width * scale) // 2
    origin_y = _CANVAS_CY - (target_height * scale) // 2
    return origin_x, origin_y


def _zoomed_preview(h, out_path: Path, padding: int = 5) -> Path:
    """Render a PNG preview zoomed to the placements' bbox (not the full canvas).

    The default ``render_png`` draws the full Canal Hideout canvas, so a
    small image looks tiny. This helper sets matplotlib axis limits to
    the placements' bbox + padding so the shape is actually visible.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from hideout_art.constants import HASH_TO_NAME
    from hideout_art.preview import DEFAULT_COLORS, DEFAULT_SIZES, FUNC_COLOR

    bb = h.bbox()
    if bb is None:
        # No placements — write a blank image
        fig, ax = plt.subplots(figsize=(6, 6), constrained_layout=True)
        ax.text(0.5, 0.5, "(no placements)", ha="center", va="center")
        ax.set_axis_off()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=120)
        plt.close(fig)
        return out_path

    x_min, y_min, x_max, y_max = bb
    x_min -= padding; x_max += padding
    y_min -= padding; y_max += padding

    fig, ax = plt.subplots(figsize=(10, 10), constrained_layout=True)
    seen: set[str] = set()
    for p in h.placements:
        canonical = HASH_TO_NAME.get(p.hash, p.name)
        is_art = canonical in DEFAULT_COLORS
        if is_art:
            color = DEFAULT_COLORS[canonical]
            size = DEFAULT_SIZES.get(canonical, 20)
            label = canonical if canonical not in seen else None
            ax.scatter(p.x, p.y, c=color, s=size, alpha=0.85,
                       edgecolors="none", label=label, zorder=3)
            seen.add(canonical)
        else:
            label = "Functional" if "Functional" not in seen else None
            ax.scatter(p.x, p.y, c=FUNC_COLOR, s=45, marker="s",
                       edgecolors="black", linewidths=0.4, zorder=2,
                       label=label)
            seen.add("Functional")

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect("equal")
    ax.set_title(f"{out_path.stem}  —  {len(h)} placements  —  bbox {bb}")
    ax.grid(True, alpha=0.25, linestyle=":")
    if seen:
        ax.legend(loc="lower right", fontsize=8, framealpha=0.9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def run_one(image_path: Path, output_name: str, target_width: int) -> dict:
    """Convert one image to .hideout + preview. Return a small report dict."""
    out_hideout = OUT_DIR / f"{output_name}.hideout"
    out_preview = OUT_DIR / f"{output_name}.preview.png"        # full canvas
    out_preview_zoom = OUT_DIR / f"{output_name}.preview_zoom.png"  # bbox only

    # Compute target_height from aspect ratio (after downscale)
    from PIL import Image
    src = Image.open(image_path)
    target_height = max(1, int(src.height * target_width / src.width))

    origin_x, origin_y = _centered_origin(target_width, target_height, COMMON["scale"])

    h = image_to_hideout(
        image_path,
        target_width=target_width,
        origin_x=origin_x,
        origin_y=origin_y,
        **COMMON,
    )
    write_hideout(h, out_hideout)
    render_png(h, out_preview, art_only=True, show_labels=False)
    _zoomed_preview(h, out_preview_zoom)

    bb = h.bbox()
    in_bounds = (
        bb is None or (
            bb[0] >= CANAL_HIDEOUT_BOUNDS[0] - 1
            and bb[1] >= CANAL_HIDEOUT_BOUNDS[1] - 1
            and bb[2] <= CANAL_HIDEOUT_BOUNDS[2] + 1
            and bb[3] <= CANAL_HIDEOUT_BOUNDS[3] + 1
        )
    )

    layers = h.layers()
    counts = {n: len(lst) for n, lst in layers.items()}

    return {
        "image": str(image_path),
        "target_width": target_width,
        "target_height": target_height,
        "origin": (origin_x, origin_y),
        "hideout": str(out_hideout),
        "preview": str(out_preview),
        "preview_zoom": str(out_preview_zoom),
        "total_placements": len(h),
        "layers": counts,
        "bbox": bb,
        "bbox_in_canal_bounds": in_bounds,
    }


def main() -> None:
    reports = []

    heart = REPO / "examples/test_icon_heart.png"
    if heart.exists():
        # 200×250 heart → downscale to width 40 (centred in canvas)
        # At step=1, scale=2: 40×50 = ~2000 placements before bounds clipping
        reports.append(run_one(heart, "heart_v062", target_width=40))
    else:
        print(f"WARN: {heart} missing")

    portrait = REPO / "examples/test_portrait.png"
    if portrait.exists():
        # 400×281 portrait → downscale to width 55 (centred in canvas)
        # At step=1, scale=2: 55×39 = ~2150 placements before bounds clipping
        reports.append(run_one(portrait, "portrait_v062", target_width=55))
    else:
        print(f"WARN: {portrait} missing")

    # Write report
    report_path = OUT_DIR / "img2hideout_report_v062.txt"
    lines = ["img2hideout v0.6.2 sanity report (high density + bright palette)", "=" * 70, ""]
    for r in reports:
        lines.append(f"Image:         {r['image']}")
        lines.append(f"target_size:   {r['target_width']}×{r['target_height']} px")
        lines.append(f"origin:        {r['origin']}")
        lines.append(f"Output:        {r['hideout']}")
        lines.append(f"Preview:       {r['preview']}")
        lines.append(f"Preview zoom:  {r['preview_zoom']}")
        lines.append(f"Placements:    {r['total_placements']}")
        lines.append(f"BBox:          {r['bbox']}  (in canal bounds: {r['bbox_in_canal_bounds']})")
        lines.append("Per-decor counts:")
        for n, c in sorted(r["layers"].items(), key=lambda kv: -kv[1]):
            lines.append(f"  {c:5d}  {n}")
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport: {report_path}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
