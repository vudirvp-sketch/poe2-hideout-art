"""Run img2hideout on the two test images (TODO-1, v0.6.1).

For each input PNG:
  1. Convert to .hideout using examples/palette_canal_warm.json
  2. Skip white background (--bg 255 255 255 --no-alpha)
  3. Clip to Canal Hideout playable canvas (--bounds canal)
  4. Use redmean metric (good for warm browns/tans)
  5. Auto-place one decor per tile (--tile-size 12) for density
  6. Render a PNG preview alongside the .hideout

Outputs go to:
  <repo>/download/
  heart.hideout           + heart.preview.png
  portrait.hideout        + portrait.preview.png
  img2hideout_report.txt  — quick sanity summary

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

PALETTE = Palette.from_json_file(REPO / "examples/palette_canal_warm.json")

# Common kwargs: white background skip, redmean metric, 1 tile per decor,
# clip to Canal Hideout bounds.
COMMON = dict(
    palette=PALETTE,
    bounds=CANAL_HIDEOUT_BOUNDS,
    background=(255, 255, 255),
    background_threshold=30,
    use_alpha=False,             # images are RGB, force bg-skip path
    color_metric="redmean",
    tile_size=12,                # half-tile: more density for recognizability
    scale=2,
    origin_x=707,                # snapped to canal bounds left
    origin_y=542,                # snapped to canal bounds bottom
    hideout_name="Imported",
    hideout_hash=60415,          # Canal Hideout
    language="Russian",
    resample="lanczos",
)


def run_one(image_path: Path, output_name: str, target_width: int) -> dict:
    """Convert one image to .hideout + preview. Return a small report dict."""
    out_hideout = OUT_DIR / f"{output_name}.hideout"
    out_preview = OUT_DIR / f"{output_name}.preview.png"

    h = image_to_hideout(
        image_path,
        target_width=target_width,
        **COMMON,
    )
    write_hideout(h, out_hideout)
    render_png(h, out_preview, art_only=True, show_labels=False)

    # Sanity: bbox within Canal Hideout bounds?
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
        "hideout": str(out_hideout),
        "preview": str(out_preview),
        "total_placements": len(h),
        "layers": counts,
        "bbox": bb,
        "bbox_in_canal_bounds": in_bounds,
    }


def main() -> None:
    reports = []

    heart = REPO / "examples/test_icon_heart.png"
    if heart.exists():
        # 200×250 heart → downscale to width 60 (small, ~30 placements expected)
        reports.append(run_one(heart, "heart", target_width=60))
    else:
        print(f"WARN: {heart} missing")

    portrait = REPO / "examples/test_portrait.png"
    if portrait.exists():
        # 400×281 portrait → downscale to width 80 (per STATUS.md TODO-1)
        reports.append(run_one(portrait, "portrait", target_width=80))
    else:
        print(f"WARN: {portrait} missing")

    # Write report
    report_path = OUT_DIR / "img2hideout_report.txt"
    lines = ["img2hideout v1 sanity report (v0.6.1)", "=" * 60, ""]
    for r in reports:
        lines.append(f"Image:        {r['image']}")
        lines.append(f"target_width: {r['target_width']} px")
        lines.append(f"Output:       {r['hideout']}")
        lines.append(f"Preview:      {r['preview']}")
        lines.append(f"Placements:   {r['total_placements']}")
        lines.append(f"BBox:         {r['bbox']}  (in canal bounds: {r['bbox_in_canal_bounds']})")
        lines.append("Per-decor counts:")
        for n, c in sorted(r["layers"].items(), key=lambda kv: -kv[1]):
            lines.append(f"  {c:5d}  {n}")
        lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nReport: {report_path}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
