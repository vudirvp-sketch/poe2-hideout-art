#!/usr/bin/env python3
"""Measure decoration placement footprints from source .hideout files.

For each decoration type (hash), this script collects ALL (x, y) placements
across all ``исходники/*.hideout`` files and computes pairwise Euclidean
distances between placements of the SAME decoration type.

The MINIMUM observed distance is an UPPER BOUND on the placement
footprint: if the user placed two Beech Trees 22 wu apart vertically,
the placement tile is at most 22 wu tall (otherwise they would visibly
overlap in-game and the user would not have placed them that close).

This is NOT the sprite bounds — the visible canopy of a tree can extend
well beyond its placement tile. For ``img2hideout`` step calculation, the
placement footprint is what matters. See KI-10 in STATUS.md.

Usage:
    python scripts/measure_decorations.py

Output:
    - Console table with statistics per decoration
    - JSON dump to scripts/decoration_footprints.json

When new decorations are added to ``исходники/``, re-run this script and
copy the resulting numbers into ``DECORATION_FOOTPRINT_CATALOG`` in
``src/hideout_art/constants.py``. The test
``test_sample_counts_match_real_exports`` in ``tests/test_footprints.py``
will fail if the catalog drifts out of sync with the source files.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from pathlib import Path

# Allow running without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hideout_art.constants import (
    ART_TYPES,
    DEFAULT_TILE_SIZE_WORLD_UNITS,
    KNOWN_HASHES,
)
from hideout_art.parser import Hideout

REPO_ROOT = Path(__file__).resolve().parent.parent
ISXODNIKI = REPO_ROOT / "исходники"
OUTPUT_JSON = Path(__file__).resolve().parent / "decoration_footprints.json"


def collect_placements_by_hash() -> dict[int, list[tuple[int, int, str]]]:
    """Return {hash: [(x, y, source_filename), ...]} across all исходники files."""
    out: dict[int, list[tuple[int, int, str]]] = {}
    for p in sorted(ISXODNIKI.glob("*.hideout")):
        h = Hideout.from_file(p)
        for pl in h.placements:
            out.setdefault(pl.hash, []).append((pl.x, pl.y, p.name))
    return out


def pairwise_distances(points: list[tuple[int, int]]) -> list[float]:
    """All pairwise Euclidean distances among (x, y) points."""
    out: list[float] = []
    n = len(points)
    for i in range(n):
        xi, yi = points[i]
        for j in range(i + 1, n):
            xj, yj = points[j]
            out.append(math.hypot(xi - xj, yi - yj))
    return out


def confidence(samples: int) -> str:
    if samples >= 5:
        return "high"
    if samples >= 3:
        return "medium"
    if samples == 2:
        return "low"
    return "single"


def estimated_tile_footprint(min_spacing: float | None) -> float | None:
    if min_spacing is None:
        return None
    tiles = min_spacing / DEFAULT_TILE_SIZE_WORLD_UNITS
    return math.ceil(tiles * 2) / 2


def main() -> int:
    if not ISXODNIKI.is_dir():
        print(f"ERROR: {ISXODNIKI} not found.", file=sys.stderr)
        return 2

    by_hash = collect_placements_by_hash()

    rows: list[dict] = []
    for name in sorted(ART_TYPES):
        hv = KNOWN_HASHES[name]
        placements = by_hash.get(hv, [])
        if not placements:
            rows.append({
                "name": name, "hash": hv, "samples": 0,
                "min_spacing_wu": None, "median_spacing_wu": None,
                "mean_spacing_wu": None, "max_spacing_wu": None,
                "estimated_tile_footprint": None,
                "confidence": "none", "sources": [],
            })
            continue

        pts = [(x, y) for (x, y, _src) in placements]
        sources = sorted({src for (_x, _y, src) in placements})
        dists = pairwise_distances(pts)
        if not dists:
            rows.append({
                "name": name, "hash": hv, "samples": len(placements),
                "min_spacing_wu": None, "median_spacing_wu": None,
                "mean_spacing_wu": None, "max_spacing_wu": None,
                "estimated_tile_footprint": None,
                "confidence": confidence(len(placements)),
                "sources": sources,
            })
            continue

        rows.append({
            "name": name, "hash": hv, "samples": len(placements),
            "pairwise_count": len(dists),
            "min_spacing_wu": round(min(dists), 2),
            "median_spacing_wu": round(statistics.median(dists), 2),
            "mean_spacing_wu": round(statistics.mean(dists), 2),
            "max_spacing_wu": round(max(dists), 2),
            "estimated_tile_footprint": estimated_tile_footprint(min(dists)),
            "confidence": confidence(len(placements)),
            "sources": sources,
        })

    print(f"{'Name':<28} {'samples':>7} {'min':>8} {'median':>8} "
          f"{'max':>8} {'tiles':>6} {'conf':>8}")
    print("-" * 90)
    for r in rows:
        min_s = f"{r['min_spacing_wu']:.1f}" if r["min_spacing_wu"] is not None else "—"
        med_s = f"{r['median_spacing_wu']:.1f}" if r["median_spacing_wu"] is not None else "—"
        max_s = f"{r['max_spacing_wu']:.1f}" if r["max_spacing_wu"] is not None else "—"
        tiles = (f"{r['estimated_tile_footprint']:.1f}"
                 if r["estimated_tile_footprint"] is not None else "—")
        print(f"{r['name']:<28} {r['samples']:>7} {min_s:>8} {med_s:>8} "
              f"{max_s:>8} {tiles:>6} {r['confidence']:>8}")

    OUTPUT_JSON.write_text(
        json.dumps(
            {
                "_note": (
                    "Placement footprint estimates derived from min pairwise "
                    "Euclidean distance between same-hash placements in "
                    "исходники/*.hideout. MIN spacing = UPPER BOUND on placement "
                    "tile footprint (NOT sprite bounds). confidence: high (>=5), "
                    "medium (3-4), low (2), single (1, no measurement)."
                ),
                "default_tile_size_world_units": DEFAULT_TILE_SIZE_WORLD_UNITS,
                "decorations": rows,
            },
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nJSON dumped to: {OUTPUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
