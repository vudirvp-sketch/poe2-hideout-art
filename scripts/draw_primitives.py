#!/usr/bin/env python3
"""Inject drawing primitives into the centre of an existing .hideout file.

Usage::

    python scripts/draw_primitives.py \\
        /home/z/my-project/upload/чистый холст.hideout \\
        -o /home/z/my-project/download/чистый холст с примитивами.hideout \\
        --center 780 657 \\
        --preview preview.png

The script:
  1. Loads the source .hideout with the tolerant parser (preserves all
     existing placements, including duplicate keys).
  2. Appends a curated composition of primitives at the requested centre.
  3. Writes the result back to a new .hideout file (byte-compatible with
     the format the game expects — duplicate keys preserved).
  4. Optionally renders a PNG preview so you can sanity-check the layout
     before importing in-game.

The script NEVER removes existing placements — it is strictly additive.

Composition modes (mutually exclusive):
  * default: ``center_composition`` (5 core primitives, 0.2.7+0.2.8).
  * ``--with-mosaic``: also append ``mosaic_composition`` (4 mosaic v2
    primitives, 0.2.9). NOTE (KI-17): mosaic v2 produces noisy output
    in-game; prefer ``--clean`` for visual verification.
  * ``--clean``: ONLY ``clean_composition`` (7 simplest single-decoration
    contours + fills, 0.3.0). Skips center_composition entirely — this
    is the recommended mode for visual verification (KI-17 response).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the package importable when run from a repo checkout without install.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from hideout_art import Hideout  # noqa: E402
from hideout_art.constants import (  # noqa: E402
    ART_TYPES,
    CANAL_HIDEOUT_BOUNDS,
    KNOWN_HASHES,
)
from hideout_art.primitives import (  # noqa: E402
    center_composition,
    clean_composition,
    mosaic_composition,
)


def _validate_decoration(name: str, role: str) -> str:
    if name not in KNOWN_HASHES:
        raise SystemExit(
            f"{role} decoration {name!r} is not in KNOWN_HASHES. Pick one "
            f"of: {', '.join(sorted(ART_TYPES))}"
        )
    if name not in ART_TYPES:
        raise SystemExit(
            f"{role} decoration {name!r} is not in ART_TYPES (it is a "
            "functional object). Pick an art decoration."
        )
    return name


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("input", type=Path,
                   help="Source .hideout file (kept untouched).")
    p.add_argument("-o", "--output", type=Path, required=True,
                   help="Destination .hideout file (created/overwritten).")
    p.add_argument(
        "--center", nargs=2, type=float, metavar=("X", "Y"),
        default=(780.0, 657.0),
        help="Centre of the composition in world coordinates "
             "(default: %(default)s — Canal Hideout centre).",
    )

    # ---- composition mode selectors ----
    p.add_argument(
        "--clean", action="store_true",
        help="ONLY inject the 0.3.0 clean_composition (7 simplest "
             "single-decoration contours + fills). Skips "
             "center_composition entirely. Recommended for visual "
             "verification (KI-17 response).",
    )
    p.add_argument(
        "--with-mosaic", action="store_true",
        help="Also inject the 0.2.9 mosaic v2 composition (bezier_curve + "
             "thick_ring + thick_arc + crosshatch) in the free zone below "
             "the core composition. Strictly additive. "
             "NOTE (KI-17): produces noisy output in-game — prefer --clean. "
             "See docs/mosaic_recipe.md for the concept.",
    )

    # ---- center_composition decoration overrides ----
    p.add_argument(
        "--line-decoration", default="Long Grass",
        help="Decoration for vertical lines (default: %(default)s).",
    )
    p.add_argument(
        "--hollow-circle-decoration", default="Maraket Rubble",
        help="Decoration for hollow circle (default: %(default)s).",
    )
    p.add_argument(
        "--filled-circle-decoration", default="Coastal Pebble",
        help="Decoration for filled circle (default: %(default)s).",
    )
    p.add_argument(
        "--s-snake-decoration", default="Maraket Rubble",
        help="Decoration for S-snake (default: %(default)s). KI-14 fix (0.2.8): "
             "was 'Sand Tussock' (too sparse).",
    )
    p.add_argument(
        "--thick-outline-decoration", default="Small Coastal Stone",
        help="Decoration for thick line outline (default: %(default)s).",
    )
    p.add_argument(
        "--thick-fill-decoration", default="Long Grass",
        help="Decoration for thick line fill (default: %(default)s). KI-15 fix "
             "(0.2.8): was 'Coastal Pebble' (invisible at thickness=14).",
    )

    # ---- clean_composition decoration overrides (0.3.0) ----
    p.add_argument(
        "--contour-decoration", default="Long Grass",
        help="Decoration for the 4 contour shapes in clean_composition "
             "(hollow_circle, rectangle, triangle, arc). "
             "Default: %(default)s (densest in catalog, sp=13.3 wu).",
    )
    p.add_argument(
        "--fill-decoration", default="Maraket Rubble",
        help="Decoration for the 3 fill shapes in clean_composition "
             "(filled_circle, hexagon, 3x3 grid). "
             "Default: %(default)s (sp=13.6 wu, contrasting brown).",
    )

    # ---- mosaic_composition decoration overrides (0.2.9) ----
    p.add_argument(
        "--spacing-override", type=float, default=None,
        help="Override the auto-derived placement spacing (in wu). "
             "Default: use min_spacing_wu from DECORATION_FOOTPRINT_CATALOG.",
    )
    p.add_argument(
        "--bezier-decoration", default="Small Coastal Stone",
        help="Decoration for the mosaic-zone bezier smile (default: %(default)s).",
    )
    p.add_argument(
        "--ring-outline-decoration", default="Small Coastal Stone",
        help="Decoration for the mosaic-zone thick_ring outline (default: %(default)s).",
    )
    p.add_argument(
        "--ring-fill-decoration", default="Cave Coral",
        help="Decoration for the mosaic-zone thick_ring fill (default: %(default)s).",
    )
    p.add_argument(
        "--arc-outline-decoration", default="Small Coastal Stone",
        help="Decoration for the mosaic-zone thick_arc outline (default: %(default)s).",
    )
    p.add_argument(
        "--arc-fill-decoration", default="Long Grass",
        help="Decoration for the mosaic-zone thick_arc fill (default: %(default)s).",
    )
    p.add_argument(
        "--hatch-decoration", default="Seaweed",
        help="Decoration for the mosaic-zone crosshatch (default: %(default)s).",
    )
    p.add_argument(
        "--preview", type=Path, default=None,
        help="Optional path to render a PNG preview of the result.",
    )
    p.add_argument(
        "--bounds-check", action="store_true",
        help="Fail if any new placement falls outside Canal Hideout bounds "
             f"{CANAL_HIDEOUT_BOUNDS}.",
    )
    args = p.parse_args(argv)

    if args.clean and args.with_mosaic:
        raise SystemExit(
            "--clean and --with-mosaic are mutually exclusive. --clean "
            "produces the simplest test bed (KI-17 response); "
            "--with-mosaic adds the noisy 0.2.9 mosaic v2 layer."
        )

    # Validate all decoration names BEFORE loading the file (fail fast).
    if not args.clean:
        _validate_decoration(args.line_decoration, "line")
        _validate_decoration(args.hollow_circle_decoration, "hollow-circle")
        _validate_decoration(args.filled_circle_decoration, "filled-circle")
        _validate_decoration(args.s_snake_decoration, "s-snake")
        _validate_decoration(args.thick_outline_decoration, "thick-outline")
        _validate_decoration(args.thick_fill_decoration, "thick-fill")
    else:
        _validate_decoration(args.contour_decoration, "contour")
        _validate_decoration(args.fill_decoration, "fill")
    if args.with_mosaic:
        _validate_decoration(args.bezier_decoration, "bezier")
        _validate_decoration(args.ring_outline_decoration, "ring-outline")
        _validate_decoration(args.ring_fill_decoration, "ring-fill")
        _validate_decoration(args.arc_outline_decoration, "arc-outline")
        _validate_decoration(args.arc_fill_decoration, "arc-fill")
        _validate_decoration(args.hatch_decoration, "hatch")

    # 1. Load source.
    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")
    h = Hideout.from_file(args.input)
    original_count = len(h)
    print(f"[load] {args.input.name}: {original_count} placements, "
          f"hideout_hash={h.hideout_hash} ({h.hideout_name!r})")

    # 2. Build the composition.
    new_placements: list = []

    if args.clean:
        # 0.3.0 clean_composition ONLY — KI-17 response.
        new_placements.extend(clean_composition(
            center_x=args.center[0],
            center_y=args.center[1],
            contour_decoration=args.contour_decoration,
            fill_decoration=args.fill_decoration,
            spacing_override=args.spacing_override,
        ))
        print(f"[draw] generated {len(new_placements)} clean placements "
              f"(0.3.0 clean_composition only)")
    else:
        # Default: 0.2.7+0.2.8 center_composition.
        new_placements.extend(center_composition(
            center_x=args.center[0],
            center_y=args.center[1],
            line_decoration=args.line_decoration,
            hollow_circle_decoration=args.hollow_circle_decoration,
            filled_circle_decoration=args.filled_circle_decoration,
            s_snake_decoration=args.s_snake_decoration,
            thick_outline_decoration=args.thick_outline_decoration,
            thick_fill_decoration=args.thick_fill_decoration,
            spacing_override=args.spacing_override,
        ))
        print(f"[draw] generated {len(new_placements)} core placements")

        # Optional: mosaic v2 composition (0.2.9) — bezier + ring + arc + hatch.
        # NOTE (KI-17): known to produce noisy output in-game.
        if args.with_mosaic:
            mosaic_placements = mosaic_composition(
                center_x=args.center[0],
                center_y=args.center[1],
                bezier_decoration=args.bezier_decoration,
                ring_outline_decoration=args.ring_outline_decoration,
                ring_fill_decoration=args.ring_fill_decoration,
                arc_outline_decoration=args.arc_outline_decoration,
                arc_fill_decoration=args.arc_fill_decoration,
                hatch_decoration=args.hatch_decoration,
                spacing_override=args.spacing_override,
            )
            print(f"[draw] generated {len(mosaic_placements)} mosaic v2 placements "
                  "(WARNING: KI-17 — produces noisy output in-game)")
            new_placements.extend(mosaic_placements)

    # 3. Optional bounds check.
    if args.bounds_check:
        x_min, y_min, x_max, y_max = CANAL_HIDEOUT_BOUNDS
        out_of_bounds = [
            p for p in new_placements
            if not (x_min <= p.x <= x_max and y_min <= p.y <= y_max)
        ]
        if out_of_bounds:
            print("[error] bounds check failed — out-of-canvas placements:",
                  file=sys.stderr)
            for p in out_of_bounds[:10]:
                print(f"  {p.name} @ ({p.x},{p.y})", file=sys.stderr)
            if len(out_of_bounds) > 10:
                print(f"  ... and {len(out_of_bounds) - 10} more",
                      file=sys.stderr)
            return 2
        print(f"[check] all {len(new_placements)} placements within "
              f"Canal Hideout bounds {CANAL_HIDEOUT_BOUNDS}")

    # 4. Append. Sort is NOT applied — source order is preserved (existing
    #    doodads first, then new art placements in composition order). This
    #    keeps the writer output stable.
    h.placements.extend(new_placements)
    print(f"[append] hideout now has {len(h)} placements "
          f"({original_count} original + {len(new_placements)} new)")

    # 5. Write output.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    h.to_file(args.output)
    print(f"[write] {args.output} "
          f"({args.output.stat().st_size} bytes)")

    # 6. Optional preview.
    if args.preview is not None:
        try:
            from hideout_art import render_png
        except ImportError:
            print("[warn] matplotlib not available — skipping preview",
                  file=sys.stderr)
        else:
            args.preview.parent.mkdir(parents=True, exist_ok=True)
            render_png(h, args.preview)
            print(f"[preview] {args.preview}")

    # 7. Sanity: re-parse the output and confirm round-trip count.
    h_check = Hideout.from_file(args.output)
    if len(h_check) != len(h):
        raise SystemExit(
            f"Round-trip mismatch: wrote {len(h)} placements but re-parsed "
            f"{len(h_check)}. Output is corrupt — do not import in-game."
        )
    print(f"[verify] round-trip OK: {len(h_check)} placements re-parsed "
          f"from output file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
