"""Command-line interface for hideout_art.

Usage examples
--------------
    hideout-art inspect path/to/file.hideout
    hideout-art layers  path/to/file.hideout
    hideout-art stats   path/to/file.hideout
    hideout-art preview path/to/file.hideout -o preview.png
    hideout-art shift   path/to/file.hideout -o moved.hideout -x 50 -y -20
    hideout-art shift   path/to/file.hideout -o art_only.hideout -x 50 --art-only
    hideout-art transfer path/to/file.hideout -o other.hideout \
        --name "Kurast Hideout" --hash 12345
    hideout-art img2hideout picture.png -o art.hideout --palette palette.json \
        --scale 3 --width 100
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .constants import NAMED_BOUNDS
from .img2hideout import image_to_hideout
from .palette import Palette, default_palette
from .parser import Hideout
from .preview import render_png
from .writer import write_hideout


def _resolve_bounds(spec: str) -> tuple[int, int, int, int] | None:
    """Resolve a --bounds spec to a (x_min, y_min, x_max, y_max) tuple.

    Accepted forms:
      * "<name>"                 — named bounds, see NAMED_BOUNDS (e.g. "canal")
      * "x_min,y_min,x_max,y_max" — explicit numeric rectangle
    """
    spec = spec.strip()
    # Named bounds (single token, no commas).
    if "," not in spec:
        if spec.lower() in NAMED_BOUNDS:
            return NAMED_BOUNDS[spec.lower()]
        print(f"ERROR: unknown --bounds name '{spec}'. "
              f"Known names: {sorted(NAMED_BOUNDS)}", file=sys.stderr)
        return None
    parts = [p.strip() for p in spec.split(",")]
    if len(parts) != 4:
        print("ERROR: --bounds must be 'x_min,y_min,x_max,y_max' "
              f"or a named shortcut {sorted(NAMED_BOUNDS)}", file=sys.stderr)
        return None
    try:
        return tuple(int(p) for p in parts)  # type: ignore[return-value]
    except ValueError:
        print(f"ERROR: --bounds values must be integers, got {parts!r}",
              file=sys.stderr)
        return None


def _cmd_inspect(args: argparse.Namespace) -> int:
    h = Hideout.from_file(args.file)
    print(f"Hideout: {h.hideout_name}  (hash {h.hideout_hash})")
    print(f"Language: {h.language}  Version: {h.version}")
    print(f"Total placements: {len(h)}")
    bb = h.bbox()
    if bb:
        print(f"BBox: ({bb[0]},{bb[1]}) -> ({bb[2]},{bb[3]})  "
              f"size {bb[2]-bb[0]} x {bb[3]-bb[1]}")
    print("\nPlacements per name:")
    for n, c in h.counts_by_name().most_common():
        tag = " [art]" if any(p.name == n and p.is_art for p in h.placements) else ""
        print(f"  {c:5d}  {n}{tag}")
    unknown = h.find_unknown_hashes()
    if unknown:
        print(f"\nWARNING: {len(unknown)} unknown hashes (not in catalogue):")
        for hv, lst in unknown.items():
            print(f"  hash={hv}  count={len(lst)}  name='{lst[0].name}'")
    return 0


def _cmd_layers(args: argparse.Namespace) -> int:
    h = Hideout.from_file(args.file)
    print(f"{'name':24s} {'n':>5s}  bbox                                centroid")
    by = h.layers()
    for n in sorted(by, key=lambda k: -len(by[k])):
        lst = by[n]
        xs = [p.x for p in lst]
        ys = [p.y for p in lst]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        print(f"{n:24s} {len(lst):5d}  ({min(xs)},{min(ys)})-({max(xs)},{max(ys)})  ({cx:.1f},{cy:.1f})")
    return 0


def _cmd_stats(args: argparse.Namespace) -> int:
    h = Hideout.from_file(args.file)
    from collections import Counter
    rs = Counter(p.r for p in h.placements)
    print("Top rotations (raw r -> degrees):")
    for r, c in rs.most_common(15):
        print(f"  r={r:>6d}  deg={r/65536*360:6.1f}°  count={c}")
    fvs = Counter(p.fv for p in h.placements)
    print("\nfv distribution (variant | flip_x):")
    for fv, c in sorted(fvs.items()):
        flip = "Y" if fv & 0x80 else "N"
        var = fv & 0x7F
        print(f"  fv={fv:>3d}  flip_x={flip}  variant={var:>2d}  count={c}")
    return 0


def _cmd_preview(args: argparse.Namespace) -> int:
    h = Hideout.from_file(args.file)
    render_png(h, args.output, art_only=args.art_only, show_labels=not args.no_labels)
    print(f"Wrote {args.output}")
    return 0


def _cmd_shift(args: argparse.Namespace) -> int:
    h = Hideout.from_file(args.file)
    h.shift(dx=args.x, dy=args.y, art_only=args.art_only)
    write_hideout(h, args.output)
    print(f"Wrote {args.output}  ({len(h)} placements)")
    return 0


def _cmd_transfer(args: argparse.Namespace) -> int:
    h = Hideout.from_file(args.file)
    h.rename_header(args.name, args.hash)
    write_hideout(h, args.output)
    print(f"Wrote {args.output}  (header now: name='{args.name}', hash={args.hash})")
    return 0


def _cmd_img2hideout(args: argparse.Namespace) -> int:
    palette = default_palette()
    if args.palette:
        palette = Palette.from_json_file(args.palette)

    bounds = None
    if args.bounds:
        bounds = _resolve_bounds(args.bounds)
        if bounds is None:
            return 2

    h = image_to_hideout(
        args.image,
        palette=palette,
        target_width=args.width,
        scale=args.scale,
        step=args.step,
        tile_size=args.tile_size,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        alpha_threshold=args.alpha_threshold,
        use_alpha=not args.no_alpha,
        background=None if args.no_bg else tuple(args.bg),
        background_threshold=args.bg_threshold,
        color_metric=args.color_metric,
        dither=args.dither,
        jitter=args.jitter,
        jitter_seed=args.jitter_seed,
        jitter_variants=args.jitter_variants,
        bounds=bounds,
        resample=args.resample,
        hideout_name=args.hideout_name or "Imported",
        hideout_hash=args.hideout_hash or 0,
        language=args.language,
    )
    write_hideout(h, args.output)
    print(f"Wrote {args.output}  ({len(h)} placements, {len(h.layers())} decoration types)")

    if args.preview:
        from pathlib import Path
        out_png = Path(args.output).with_suffix(".preview.png")
        render_png(h, out_png, art_only=True, show_labels=False)
        print(f"Wrote preview: {out_png}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="hideout-art",
        description="Read, transform and emit Path of Exile 2 .hideout files.",
    )
    ap.add_argument("--version", action="version", version=f"hideout-art {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inspect", help="List placements, bboxes, per-layer stats")
    p.add_argument("file")
    p.set_defaults(fn=_cmd_inspect)

    p = sub.add_parser("layers", help="Per-layer bounding boxes + centroids")
    p.add_argument("file")
    p.set_defaults(fn=_cmd_layers)

    p = sub.add_parser("stats", help="Rotation and fv distribution")
    p.add_argument("file")
    p.set_defaults(fn=_cmd_stats)

    p = sub.add_parser("preview", help="Render a PNG preview")
    p.add_argument("file")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--art-only", action="store_true")
    p.add_argument("--no-labels", action="store_true")
    p.set_defaults(fn=_cmd_preview)

    p = sub.add_parser("shift", help="Translate placements")
    p.add_argument("file")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("-x", type=int, default=0)
    p.add_argument("-y", type=int, default=0)
    p.add_argument("--art-only", action="store_true")
    p.set_defaults(fn=_cmd_shift)

    p = sub.add_parser("transfer", help="Re-target to a different hideout map")
    p.add_argument("file")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--hash", type=int, required=True)
    p.set_defaults(fn=_cmd_transfer)

    p = sub.add_parser("img2hideout", help="Convert an image into a .hideout file")
    p.add_argument("image")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--palette", help="JSON palette file (see examples/)")
    p.add_argument("--width", type=int, default=120,
                   help="Downscale image to this width (px). Default 120.")
    p.add_argument("--scale", type=int, default=2,
                   help="World units per pixel. Default 2.")
    p.add_argument("--step", type=int, default=None,
                   help="Place a decoration every Nth pixel in both x and y. "
                        "step=2 halves placement count and lets each decoration "
                        "breathe. Default 1. Mutually exclusive with --tile-size.")
    p.add_argument("--tile-size", type=int, default=None,
                   help="Decoration footprint in world units. When set, "
                        "auto-computes step = round(tile_size / scale) so that "
                        "one decoration is placed per game tile (no overlap, "
                        "no gaps). Typical value: 23 (1 tile). Mutually "
                        "exclusive with --step. Closes KI-1.")
    p.add_argument("--origin-x", type=int, default=700)
    p.add_argument("--origin-y", type=int, default=550)
    # Background / alpha
    p.add_argument("--bg", type=int, nargs=3, default=[0, 0, 0],
                   metavar=("R", "G", "B"),
                   help="Background colour to skip (RGB). Default 0 0 0. "
                        "Use --no-bg to disable.")
    p.add_argument("--no-bg", action="store_true",
                   help="Disable background-colour skipping.")
    p.add_argument("--bg-threshold", type=int, default=30,
                   help="Euclidean RGB distance under which a pixel is "
                        "treated as background. Default 30.")
    p.add_argument("--alpha-threshold", type=int, default=32,
                   help="For RGBA images: skip pixels with alpha < this. "
                        "Default 32.")
    p.add_argument("--no-alpha", action="store_true",
                   help="Ignore alpha channel even when present (legacy mode).")
    # Colour matching
    p.add_argument("--color-metric", default="rgb",
                   choices=["rgb", "weighted", "redmean"],
                   help="Distance metric for palette matching. "
                        "'rgb' (default, Euclidean), 'weighted' (luminance), "
                        "'redmean' (perceptual, good for warm colours).")
    p.add_argument("--dither", action="store_true",
                   help="Enable Floyd-Steinberg dithering (smoother gradients).")
    # Jitter
    p.add_argument("--jitter", action="store_true",
                   help="Randomise rotation (15° steps) and variant per "
                        "placement for visual variety.")
    p.add_argument("--jitter-seed", type=int, default=0,
                   help="RNG seed for reproducible jitter. 0 = unpredictable.")
    p.add_argument("--jitter-variants", type=int, default=8,
                   help="Max variant index when jittering (0..N-1). Default 8.")
    # Bounds
    p.add_argument("--bounds", default=None,
                   help="Clip placements to a world-coord rectangle. Two forms: "
                        "named shortcut (e.g. 'canal' for Canal Hideout's "
                        "playable canvas, see NAMED_BOUNDS in constants.py), "
                        "or explicit 'x_min,y_min,x_max,y_max'. Placements "
                        "outside the rectangle are skipped. Use to respect "
                        "hideout boundaries.")
    # Resample
    p.add_argument("--resample", default="bicubic",
                   choices=["nearest", "bilinear", "bicubic", "lanczos"],
                   help="PIL downscaling filter. 'nearest' preserves pixel-art "
                        "edges. Default 'bicubic'.")
    # Output extras
    p.add_argument("--preview", action="store_true",
                   help="Also write a PNG preview next to the .hideout file "
                        "(<output>.preview.png). Lets you iterate without "
                        "importing into the game.")
    p.add_argument("--hideout-name")
    p.add_argument("--hideout-hash", type=int)
    p.add_argument("--language", default="English",
                   help="Language for the .hideout file header and decoration "
                        "names. Default 'English'. Pass 'Russian' to emit "
                        "Russian decoration names (matches what real user "
                        "exports look like when exported from a Russian PoE2 "
                        "client). Hashes are language-independent.")
    p.set_defaults(fn=_cmd_img2hideout)

    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
