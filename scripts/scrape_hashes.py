#!/usr/bin/env python3
"""Walk a folder of .hideout exports, print every unknown hash.

Usage:
    python scripts/scrape_hashes.py /path/to/folder/of/exports

Useful when extending KNOWN_HASHES: run this over your collection and
submit a PR with any new (hash, name) pairs you find.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

# Allow running without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hideout_art import Hideout
from hideout_art.constants import HASH_TO_NAME


def main(folder: str) -> int:
    root = Path(folder)
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 2

    unknown_counts: Counter = Counter()
    unknown_names: dict[int, set[str]] = {}
    files_scanned = 0

    for path in sorted(root.rglob("*.hideout")):
        try:
            h = Hideout.from_file(path)
        except Exception as e:
            print(f"  SKIP {path}: {e}", file=sys.stderr)
            continue
        files_scanned += 1
        for h_, placements in h.find_unknown_hashes().items():
            unknown_counts[h_] += len(placements)
            unknown_names.setdefault(h_, set()).update(p.name for p in placements)

    print(f"Scanned {files_scanned} files in {root}")
    if not unknown_counts:
        print("All hashes are already in the catalogue. Nothing new.")
        return 0

    print(f"\n{len(unknown_counts)} unknown hashes found:\n")
    print(f"{'hash':>14s}  {'count':>6s}  names")
    print("-" * 60)
    for h_, cnt in unknown_counts.most_common():
        names = ", ".join(sorted(unknown_names[h_]))
        print(f"{h_:>14d}  {cnt:>6d}  {names}")

    print("\nAdd these to src/hideout_art/constants.py:KNOWN_HASHES.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <folder>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
