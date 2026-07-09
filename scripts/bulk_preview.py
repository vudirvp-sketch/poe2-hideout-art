#!/usr/bin/env python3
"""Render a PNG preview for every .hideout in a folder.

Usage:
    python scripts/bulk_preview.py /path/to/exports -o /path/to/previews
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hideout_art import Hideout, render_png


def main(folder: str, out_dir: str) -> int:
    root = Path(folder)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    n = 0
    for path in sorted(root.rglob("*.hideout")):
        try:
            h = Hideout.from_file(path)
        except Exception as e:
            print(f"  SKIP {path}: {e}", file=sys.stderr)
            continue
        target = out / (path.stem + ".png")
        render_png(h, target, art_only=False)
        print(f"  {path.name} -> {target.name}  ({len(h)} placements)")
        n += 1

    print(f"\nRendered {n} previews into {out}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[2] != "-o":
        print(f"Usage: {sys.argv[0]} <input_folder> -o <output_folder>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[3]))
