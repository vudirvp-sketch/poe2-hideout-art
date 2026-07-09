#!/usr/bin/env python3
"""Inject drawing primitives into the centre of an existing .hideout file.

Usage::

    python scripts/draw_primitives.py \
        /home/z/my-project/upload/чистый холст.hideout \
        -o /home/z/my-project/download/чистый холст с примитивами.hideout \
        --center 780 657 \
        --preview preview.png

The script:
  1. Loads the source .hideout with the tolerant parser (preserves all
     existing placements, including duplicate keys).
  2. Appends a curated composition of five primitives (vertical lines,
     hollow circle, filled circle, S-snake, thick line with contours) at
     the requested centre.
  3. Writes the result back to a new .hideout file (byte-compatible with
     the format the game expects — duplicate keys preserved).
  4. Optionally renders a PNG preview so you can sanity-check the layout
     before importing in-game.

The script NEVER removes existing placements — it is strictly additive.
This is the "не ломая файл с убежищем" rule from the user's brief.
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
from hideout_art.primitives import center_composition  # noqa: E402


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
        "--s-snake-decoration", default="Sand Tussock",
        help="Decoration for S-snake (default: %(default)s).",
    )
    p.add_argument(
        "--thick-outline-decoration", default="Small Coastal Stone",
        help="Decoration for thick line outline (default: %(default)s).",
    )
    p.add_argument(
        "--thick-fill-decoration", default="Coastal Pebble",
        help="Decoration for thick line fill (default: %(default)s).",
    )
    p.add_argument(
        "--spacing-override", type=float, default=None,
        help="Override the auto-derived placement spacing (in wu). "
             "Default: use min_spacing_wu from DECORATION_FOOTPRINT_CATALOG.",
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

    # Validate all decoration names BEFORE loading the file (fail fast).
    _validate_decoration(args.line_decoration, "line")
    _validate_decoration(args.hollow_circle_decoration, "hollow-circle")
    _validate_decoration(args.filled_circle_decoration, "filled-circle")
    _validate_decoration(args.s_snake_decoration, "s-snake")
    _validate_decoration(args.thick_outline_decoration, "thick-outline")
    _validate_decoration(args.thick_fill_decoration, "thick-fill")

    # 1. Load source.
    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")
    h = Hideout.from_file(args.input)
    original_count = len(h)
    print(f"[load] {args.input.name}: {original_count} placements, "
          f"hideout_hash={h.hideout_hash} ({h.hideout_name!r})")

    # 2. Build the composition.
    new_placements = center_composition(
        center_x=args.center[0],
        center_y=args.center[1],
        line_decoration=args.line_decoration,
        hollow_circle_decoration=args.hollow_circle_decoration,
        filled_circle_decoration=args.filled_circle_decoration,
        s_snake_decoration=args.s_snake_decoration,
        thick_outline_decoration=args.thick_outline_decoration,
        thick_fill_decoration=args.thick_fill_decoration,
        spacing_override=args.spacing_override,
    )
    print(f"[draw] generated {len(new_placements)} new placements")

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
