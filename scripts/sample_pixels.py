#!/usr/bin/env python3
"""Pixel sampling for PoE2 hideout decorations — closes KI-11.

For each art placement in a ``.hideout`` file, sample the corresponding
pixels in a screenshot and compute median / mean / quartile RGB. This
provides ground-truth colour measurement to replace the noisy VLM
estimates documented in KI-11 (STATUS.md).

The core challenge is calibrating the world-coordinate → pixel-coordinate
transform, because every screenshot has a different crop / zoom. We solve
this in two ways:

1. **Auto-calibration** (default). The Canal Hideout playable canvas
   ``CANAL_HIDEOUT_BOUNDS = (700, 540, 860, 775)`` is mapped onto the
   screenshot with UI-aware margins: the game UI occupies the bottom
   ~20% of the screen (skill bar, buffs) and thin strips on the sides,
   so by default we map the canvas to ``x ∈ [0.05W, 0.95W]`` and
   ``y ∈ [0.05H, 0.80H]`` (Y axis flipped — world y grows upward,
   image y grows downward). Override with ``--margin-left/right/top/bottom``.

2. **Manual calibration** via ``--calibration <json>``. The JSON lists
   anchor points — known ``(world_x, world_y) → (pixel_x, pixel_y)``
   correspondences for in-game objects visible on the screenshot
   (Stash at (811, 519), Waypoint at (697, 660), etc.). With ≥2 anchors
   the script solves a least-squares affine transform. With ≥3 anchors
   it also reports the residual so you can verify accuracy.

ALWAYS inspect the ``--diagnostic`` PNG after running: it overlays every
placement as a coloured dot on the screenshot. If the dots line up with
the visible decorations, the calibration is good. If they don't, adjust
margins or supply a manual calibration JSON.

Usage:
    # Auto-calibration + diagnostic + JSON report:
    python scripts/sample_pixels.py \\
        "исходники/камни и кустарники.hideout" \\
        "исходники/камни и кустарники.jpg" \\
        --output scripts/sampled_pixels.json \\
        --diagnostic scripts/diagnostic_камни.png

    # Manual calibration (recommended for production use):
    python scripts/sample_pixels.py ... \\
        --calibration scripts/calibrations/камни.json

    # Larger sampling window (noisier but covers more of the sprite):
    python scripts/sample_pixels.py ... --sample-radius-wu 6

Calibration JSON format::

    {
      "anchors": [
        {"world": [811, 519], "pixel": [1200, 100], "name": "Stash"},
        {"world": [697, 660], "pixel": [400, 500], "name": "Waypoint"},
        {"world": [683, 694], "pixel": [350, 700], "name": "Well"}
      ]
    }

Output JSON format::

    {
      "_meta": {
        "hideout_file": "...",
        "screenshot_file": "...",
        "image_size": [W, H],
        "calibration": {"method": "auto"|"manual", "residual_px": float|null, ...},
        "sample_radius_wu": 4,
        "sample_radius_px": 31.2,
        "n_placements_sampled": 16
      },
      "decorations": {
        "Sand Tussock": {
          "hash": 146816198,
          "n_placements": 7,
          "median_rgb": [180, 162, 121],
          "mean_rgb":   [178, 159, 117],
          "p25_rgb":    [150, 132, 95],
          "p75_rgb":    [205, 188, 150],
          "per_placement": [
            {"x": 740, "y": 683, "r": 0, "fv": 0,
             "pixel_xy": [412, 705],
             "median_rgb": [182, 165, 124], "n_pixels_sampled": 1840},
            ...
          ]
        },
        ...
      }
    }
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

# Allow running without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from hideout_art.constants import (  # noqa: E402
    CANAL_HIDEOUT_BOUNDS,
    DECORATION_FOOTPRINT_CATALOG,
    HASH_TO_NAME,
)
from hideout_art.parser import Hideout  # noqa: E402


# --------------------------------------------------------------------------- #
# Calibration
# --------------------------------------------------------------------------- #
@dataclass
class WorldToPixel:
    """Affine transform: (wx, wy) -> (px, py).

    px = a * wx + b
    py = c * wy + d   (c < 0 because Y axis is flipped)

    For least-squares manual calibration with N anchors (N >= 2):
        minimise  sum_i  (a*wx_i + b - px_i)^2  +  (c*wy_i + d - py_i)^2
    Closed-form solution (separate 1D linear regressions for x and y).
    """

    a: float  # scale_x (world unit -> pixel)
    b: float  # offset_x (pixel)
    c: float  # scale_y (world unit -> pixel) — NEGATIVE (y flip)
    d: float  # offset_y (pixel)
    method: str  # "auto" | "manual"
    residual_px: float | None = None  # RMS residual in pixels (manual only)
    n_anchors: int = 0

    def world_to_pixel(self, wx: float, wy: float) -> tuple[float, float]:
        return (self.a * wx + self.b, self.c * wy + self.d)

    def world_dist_to_pixel(self, wu: float) -> float:
        """Convert a world-unit distance to a pixel distance (uses scale_x)."""
        return abs(self.a) * wu

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "a_scale_x": round(self.a, 4),
            "b_offset_x": round(self.b, 2),
            "c_scale_y": round(self.c, 4),
            "d_offset_y": round(self.d, 2),
            "residual_px": (round(self.residual_px, 2)
                            if self.residual_px is not None else None),
            "n_anchors": self.n_anchors,
        }


def calibrate_auto(
    image_size: tuple[int, int],
    world_bbox: tuple[int, int, int, int] = CANAL_HIDEOUT_BOUNDS,
    margin_left: float = 0.05,
    margin_right: float = 0.05,
    margin_top: float = 0.05,
    margin_bottom: float = 0.20,
) -> WorldToPixel:
    """Map the Canal Hideout playable canvas onto the screenshot with UI margins.

    The PoE2 UI puts the skill bar, buffs and chat in the bottom ~20% of
    the screen and thin strips on the sides, so by default the playable
    canvas occupies x ∈ [5%, 95%] of the screenshot width and
    y ∈ [5%, 80%] of the height (top of screen → top of world bbox
    because world y grows upward).
    """
    w, h = image_size
    wx_min, wy_min, wx_max, wy_max = world_bbox

    px_min = margin_left * w
    px_max = (1.0 - margin_right) * w
    # World y grows upward; image y grows downward. So world y_max maps
    # to image top (py_min) and world y_min maps to image bottom (py_max).
    py_min = margin_top * h
    py_max = (1.0 - margin_bottom) * h

    a = (px_max - px_min) / (wx_max - wx_min)
    b = px_min - a * wx_min
    c = (py_max - py_min) / (wy_min - wy_max)  # negative (flip)
    d = py_min - c * wy_max  # anchor at top of world

    return WorldToPixel(a=a, b=b, c=c, d=d, method="auto", n_anchors=0)


def calibrate_manual(anchors: list[dict]) -> WorldToPixel:
    """Least-squares affine fit from anchor points.

    Each anchor: ``{"world": [wx, wy], "pixel": [px, py], "name": str}``.
    Need >= 2 anchors; with >= 3 we can compute a residual.

    We solve two independent 1D linear regressions:
        px = a * wx + b   (minimise sum (a*wx_i + b - px_i)^2)
        py = c * wy + d   (minimise sum (c*wy_i + d - py_i)^2)
    """
    if len(anchors) < 2:
        raise ValueError(
            f"Manual calibration needs >= 2 anchors, got {len(anchors)}."
        )

    wxs = [float(a["world"][0]) for a in anchors]
    wys = [float(a["world"][1]) for a in anchors]
    pxs = [float(a["pixel"][0]) for a in anchors]
    pys = [float(a["pixel"][1]) for a in anchors]

    n = len(anchors)

    def linfit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
        """Return (slope, intercept, rms_residual) for y = slope*x + intercept."""
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
        den = sum((x - mean_x) ** 2 for x in xs)
        if den == 0:
            # All x equal — degenerate; fall back to mean
            slope = 0.0
            intercept = mean_y
        else:
            slope = num / den
            intercept = mean_y - slope * mean_x
        # RMS residual
        if n >= 3:
            sse = sum((slope * x + intercept - y) ** 2
                     for x, y in zip(xs, ys, strict=True))
            rms = math.sqrt(sse / n)
        else:
            rms = 0.0
        return slope, intercept, rms

    a, b, res_x = linfit(wxs, pxs)
    c, d, res_y = linfit(wys, pys)

    # Combined RMS residual
    if n >= 3:
        residual = math.sqrt((res_x ** 2 + res_y ** 2) / 2)
    else:
        residual = None

    return WorldToPixel(
        a=a, b=b, c=c, d=d,
        method="manual",
        residual_px=residual,
        n_anchors=n,
    )


# --------------------------------------------------------------------------- #
# Pixel sampling
# --------------------------------------------------------------------------- #
def sample_placement_pixels(
    img: Image.Image,
    px: float,
    py: float,
    radius_px: float,
) -> tuple[list[tuple[int, int, int]], int]:
    """Return list of (R, G, B) tuples inside a circle of radius_px around (px, py).

    Pixels are clamped to image bounds. Returns the list of sampled pixels
    and the count of pixels that fell inside the image (some may be clipped
    if the placement is near the edge).
    """
    w, h = img.size
    x0 = max(0, int(math.floor(px - radius_px)))
    x1 = min(w, int(math.ceil(px + radius_px)) + 1)
    y0 = max(0, int(math.floor(py - radius_px)))
    y1 = min(h, int(math.ceil(py + radius_px)) + 1)
    if x1 <= x0 or y1 <= y0:
        return [], 0

    crop = img.crop((x0, y0, x1, y1))
    pixels = list(crop.getdata())
    r2 = radius_px * radius_px
    cx = px - x0
    cy = py - y0
    out: list[tuple[int, int, int]] = []
    for dy in range(crop.height):
        for dx in range(crop.width):
            if (dx - cx) ** 2 + (dy - cy) ** 2 <= r2:
                out.append(pixels[dy * crop.width + dx])
    return out, len(out)


def rgb_stats(pixels: list[tuple[int, int, int]]) -> dict:
    """Compute median / mean / p25 / p75 RGB statistics."""
    if not pixels:
        return {
            "median_rgb": None, "mean_rgb": None,
            "p25_rgb": None, "p75_rgb": None, "n_pixels_sampled": 0,
        }
    rs = sorted(p[0] for p in pixels)
    gs = sorted(p[1] for p in pixels)
    bs = sorted(p[2] for p in pixels)
    n = len(pixels)

    def quantile(sorted_list: list[int], q: float) -> int:
        if not sorted_list:
            return 0
        # Nearest-rank method
        idx = max(0, min(n - 1, int(round(q * (n - 1)))))
        return sorted_list[idx]

    return {
        "median_rgb": [quantile(rs, 0.50), quantile(gs, 0.50), quantile(bs, 0.50)],
        "mean_rgb":   [round(sum(rs) / n), round(sum(gs) / n), round(sum(bs) / n)],
        "p25_rgb":    [quantile(rs, 0.25), quantile(gs, 0.25), quantile(bs, 0.25)],
        "p75_rgb":    [quantile(rs, 0.75), quantile(gs, 0.75), quantile(bs, 0.75)],
        "n_pixels_sampled": n,
    }


def aggregate_medians(per_placement_rgb: list[list[int]]) -> list[int]:
    """Per-channel median across multiple placements of the same decoration.

    For n == 1 returns the single value. For n == 2 returns the mean of the
    two (the standard "median of an even-length list" definition). For
    n >= 3 returns the middle element of the sorted list (nearest-rank).
    """
    if not per_placement_rgb:
        return [0, 0, 0]
    n = len(per_placement_rgb)
    rs = sorted(rgb[0] for rgb in per_placement_rgb)
    gs = sorted(rgb[1] for rgb in per_placement_rgb)
    bs = sorted(rgb[2] for rgb in per_placement_rgb)
    if n == 2:
        return [
            round((rs[0] + rs[1]) / 2),
            round((gs[0] + gs[1]) / 2),
            round((bs[0] + bs[1]) / 2),
        ]
    mid = n // 2
    return [rs[mid], gs[mid], bs[mid]]


# --------------------------------------------------------------------------- #
# Diagnostic overlay
# --------------------------------------------------------------------------- #
# Stable colour per decoration name (hash → hue).
def decoration_color(name: str) -> tuple[int, int, int]:
    h = abs(hash(name)) % 360
    # Convert HSV to RGB (matplotlib-free, simple formula)
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(h / 360.0, 0.85, 0.95)
    return (int(r * 255), int(g * 255), int(b * 255))


def render_diagnostic(
    img: Image.Image,
    placements: list[dict],
    transform: WorldToPixel,
    output_path: Path,
    sample_radius_px: float,
) -> None:
    """Overlay every placement as a coloured dot on the screenshot.

    Art placements get filled circles (one colour per decoration name);
    functional placements (anchors) get white rings with text labels so
    you can verify the calibration by eye.
    """
    overlay = img.copy().convert("RGB")
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14
        )
    except Exception:
        font = ImageFont.load_default()

    # Functional anchors first (drawn under art dots)
    for pl in placements:
        if pl["is_art"]:
            continue
        px, py = transform.world_to_pixel(pl["x"], pl["y"])
        if not (0 <= px < img.size[0] and 0 <= py < img.size[1]):
            continue
        r = 12
        draw.ellipse(
            [(px - r, py - r), (px + r, py + r)],
            outline=(255, 255, 255), width=2,
        )
        draw.text((px + 14, py - 7), pl["canonical_name"],
                  fill=(255, 255, 255), font=font)

    # Art placements
    for pl in placements:
        if not pl["is_art"]:
            continue
        px, py = transform.world_to_pixel(pl["x"], pl["y"])
        if not (0 <= px < img.size[0] and 0 <= py < img.size[1]):
            continue
        col = decoration_color(pl["canonical_name"])
        r = 8
        # Sample window outline (thin)
        draw.ellipse(
            [(px - sample_radius_px, py - sample_radius_px),
             (px + sample_radius_px, py + sample_radius_px)],
            outline=col, width=1,
        )
        # Placement centre (filled)
        draw.ellipse(
            [(px - r, py - r), (px + r, py + r)],
            fill=col, outline=(0, 0, 0), width=1,
        )

    # Header text with calibration summary
    header = (
        f"calibration: {transform.method}  "
        f"scale_x={transform.a:.2f}px/wu  scale_y={transform.c:.2f}px/wu  "
        f"residual={transform.residual_px}"
    )
    draw.rectangle([(0, 0), (img.size[0], 26)], fill=(0, 0, 0))
    draw.text((6, 4), header, fill=(255, 255, 0), font=font)

    overlay.save(output_path)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def find_hideout_sibling_screenshot(hideout_path: Path) -> Path | None:
    """Given ``foo.hideout``, look for ``foo.jpg`` / ``foo.png`` alongside."""
    for ext in (".jpg", ".jpeg", ".png"):
        candidate = hideout_path.with_suffix(ext)
        if candidate.exists():
            return candidate
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Sample real pixel RGB under each art placement in a .hideout "
            "file using the matching screenshot. Closes KI-11."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("hideout", type=Path, help="Path to the .hideout file")
    p.add_argument(
        "screenshot", type=Path, nargs="?",
        help="Path to the .jpg screenshot. If omitted, looks for a sibling "
             "with the same stem.",
    )
    p.add_argument(
        "--calibration", type=Path,
        help="JSON file with manual anchor correspondences. Overrides auto.",
    )
    p.add_argument(
        "--world-bbox", type=str, default="canal",
        help="World bbox for auto-calibration. One of: 'canal' "
             "(CANAL_HIDEOUT_BOUNDS), 'functional' (auto-derived from all "
             "non-art placements in this .hideout — recommended when "
             "anchors fall outside Canal canvas), or "
             "'x_min,y_min,x_max,y_max' (comma-separated). Default: canal.",
    )
    p.add_argument("--margin-left", type=float, default=0.05)
    p.add_argument("--margin-right", type=float, default=0.05)
    p.add_argument("--margin-top", type=float, default=0.05)
    p.add_argument("--margin-bottom", type=float, default=0.20,
                   help="Bottom margin (UI skill bar). Default 0.20.")
    p.add_argument(
        "--sample-radius-wu", type=float, default=4.0,
        help="Sampling window radius in world units (1 tile ≈ 23 wu). "
             "Default 4.0 (≈ 1/6 tile).",
    )
    p.add_argument(
        "--output", "-o", type=Path, default=None,
        help="Output JSON report path. Default: scripts/sampled_pixels.json.",
    )
    p.add_argument(
        "--diagnostic", type=Path, default=None,
        help="Optional path to save a diagnostic overlay PNG.",
    )
    p.add_argument(
        "--only-art", action="store_true", default=True,
        help="Only sample art-layer placements (default).",
    )
    p.add_argument(
        "--include-functional", action="store_true",
        help="Also sample functional placements (Stash, Waypoint, etc.). "
             "Useful for calibration verification.",
    )
    args = p.parse_args(argv)

    # Resolve paths
    if not args.hideout.exists():
        print(f"ERROR: hideout file not found: {args.hideout}", file=sys.stderr)
        return 2
    screenshot = args.screenshot or find_hideout_sibling_screenshot(args.hideout)
    if screenshot is None or not screenshot.exists():
        print(
            f"ERROR: screenshot not found for {args.hideout.name}. "
            f"Pass --screenshot explicitly.",
            file=sys.stderr,
        )
        return 2

    output_path = args.output or (
        Path(__file__).resolve().parent / "sampled_pixels.json"
    )

    # Load hideout
    h = Hideout.from_file(args.hideout)
    print(f"Loaded hideout: {h.hideout_name} (hash={h.hideout_hash})")
    print(f"  placements: {len(h)} ({sum(1 for p in h if p.is_art)} art)")

    # Load screenshot
    img = Image.open(screenshot).convert("RGB")
    print(f"  screenshot: {screenshot.name}  size={img.size}")

    # Calibrate
    if args.calibration:
        cal_data = json.loads(args.calibration.read_text(encoding="utf-8"))
        anchors = cal_data.get("anchors", [])
        transform = calibrate_manual(anchors)
        print(f"  calibration: MANUAL  anchors={transform.n_anchors}  "
              f"residual={transform.residual_px}px")
    else:
        if args.world_bbox == "canal":
            world_bbox = CANAL_HIDEOUT_BOUNDS
        elif args.world_bbox == "functional":
            # Auto-derive from all non-art placements in this hideout.
            # Captures anchors outside Canal canvas (Ange, Reforging Bench,
            # Salvage Bench, Well — all at x<700).
            non_art = [p for p in h.placements if not p.is_art]
            if not non_art:
                print("ERROR: --world-bbox functional requires non-art "
                      "placements, found none.", file=sys.stderr)
                return 2
            xs = [p.x for p in non_art]
            ys = [p.y for p in non_art]
            # 5 wu padding so anchors aren't on the image edge
            world_bbox = (min(xs) - 5, min(ys) - 5,
                          max(xs) + 5, max(ys) + 5)
        else:
            parts = [float(x) for x in args.world_bbox.split(",")]
            if len(parts) != 4:
                print("ERROR: --world-bbox must be 'canal', 'functional', "
                      "or 'x_min,y_min,x_max,y_max'", file=sys.stderr)
                return 2
            world_bbox = tuple(parts)  # type: ignore
        transform = calibrate_auto(
            image_size=img.size,
            world_bbox=world_bbox,
            margin_left=args.margin_left,
            margin_right=args.margin_right,
            margin_top=args.margin_top,
            margin_bottom=args.margin_bottom,
        )
        print(f"  calibration: AUTO  bbox={world_bbox}  "
              f"scale_x={transform.a:.2f}px/wu  scale_y={transform.c:.2f}px/wu")

    sample_radius_px = transform.world_dist_to_pixel(args.sample_radius_wu)
    print(f"  sample radius: {args.sample_radius_wu} wu = "
          f"{sample_radius_px:.1f} px")

    # Decide which placements to sample
    include_func = args.include_functional or not args.only_art
    to_sample = [
        pl for pl in h.placements
        if pl.is_art or include_func
    ]

    # Sample each placement
    by_deco: dict[str, list[dict]] = {}
    all_sampled: list[dict] = []
    for pl in to_sample:
        canonical = HASH_TO_NAME.get(pl.hash, pl.name)
        px, py = transform.world_to_pixel(pl.x, pl.y)
        pixels, n = sample_placement_pixels(img, px, py, sample_radius_px)
        stats = rgb_stats(pixels)
        entry = {
            "name_in_file": pl.name,
            "canonical_name": canonical,
            "hash": pl.hash,
            "x": pl.x, "y": pl.y, "r": pl.r, "fv": pl.fv,
            "is_art": pl.is_art,
            "pixel_xy": [round(px, 1), round(py, 1)],
            "in_image": (0 <= px < img.size[0] and 0 <= py < img.size[1]),
            **stats,
        }
        all_sampled.append(entry)
        by_deco.setdefault(canonical, []).append(entry)

    # Aggregate per decoration
    deco_summary: dict[str, dict] = {}
    for name, entries in by_deco.items():
        medians = [e["median_rgb"] for e in entries if e["median_rgb"] is not None]
        means = [e["mean_rgb"] for e in entries if e["mean_rgb"] is not None]
        p25s = [e["p25_rgb"] for e in entries if e["p25_rgb"] is not None]
        p75s = [e["p75_rgb"] for e in entries if e["p75_rgb"] is not None]
        hash_val = entries[0]["hash"]
        deco_summary[name] = {
            "hash": hash_val,
            "n_placements": len(entries),
            "median_rgb": aggregate_medians(medians) if medians else None,
            "mean_rgb": aggregate_medians(means) if means else None,
            "p25_rgb": aggregate_medians(p25s) if p25s else None,
            "p75_rgb": aggregate_medians(p75s) if p75s else None,
            "per_placement": entries,
        }

    # Footprint info (placement tile estimate from DECORATION_FOOTPRINT_CATALOG)
    for name, summary in deco_summary.items():
        fp = DECORATION_FOOTPRINT_CATALOG.get(name)
        if fp:
            summary["footprint_estimate_wu"] = fp.min_spacing_wu
            summary["footprint_confidence"] = fp.confidence

    # Console table
    print()
    print(f"{'Decoration':<25} {'hash':>11} {'n':>3}  "
          f"{'median RGB':>17}  {'mean RGB':>17}  {'p25 - p75':>25}")
    print("-" * 110)
    for name in sorted(deco_summary):
        s = deco_summary[name]
        med = s["median_rgb"]
        mean = s["mean_rgb"]
        p25 = s["p25_rgb"]
        p75 = s["p75_rgb"]
        med_str = f"({med[0]:3d},{med[1]:3d},{med[2]:3d})" if med else "—"
        mean_str = f"({mean[0]:3d},{mean[1]:3d},{mean[2]:3d})" if mean else "—"
        if p25 and p75:
            q_str = f"({p25[0]:3d}..{p75[0]:3d},{p25[1]:3d}..{p75[1]:3d},{p25[2]:3d}..{p75[2]:3d})"
        else:
            q_str = "—"
        print(f"{name:<25} {s['hash']:>11} {s['n_placements']:>3}  "
              f"{med_str:>17}  {mean_str:>17}  {q_str:>25}")

    # Write JSON report
    report = {
        "_meta": {
            "hideout_file": str(args.hideout),
            "screenshot_file": str(screenshot),
            "image_size": list(img.size),
            "calibration": transform.to_dict(),
            "sample_radius_wu": args.sample_radius_wu,
            "sample_radius_px": round(sample_radius_px, 2),
            "n_placements_sampled": len(all_sampled),
            "n_decorations": len(deco_summary),
            "tool_version": "0.2.6",
        },
        "decorations": deco_summary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\nJSON report written to: {output_path}")

    # Diagnostic overlay
    if args.diagnostic:
        render_diagnostic(
            img=img,
            placements=all_sampled,
            transform=transform,
            output_path=args.diagnostic,
            sample_radius_px=sample_radius_px,
        )
        print(f"Diagnostic overlay written to: {args.diagnostic}")

    # Sanity check warnings
    n_off_image = sum(1 for e in all_sampled if not e["in_image"])
    if n_off_image:
        print(
            f"\nWARNING: {n_off_image} placements fell outside the screenshot. "
            f"Check the diagnostic overlay — calibration may be off."
        )
    n_empty = sum(1 for e in all_sampled
                  if e["in_image"] and e["n_pixels_sampled"] == 0)
    if n_empty:
        print(
            f"WARNING: {n_empty} placements produced 0 pixels. "
            f"Increase --sample-radius-wu or fix calibration."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
