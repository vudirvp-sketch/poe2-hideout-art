"""
Per-doodad-type positional analysis.

For each .hideout, for each top doodad type, compute:
  - NN distance (median) within that type
  - NN distance to NEAREST point of ANY type (overlap/co-location)
  - density (points per unit area of bbox)
  - centroid (does this type live in a specific region?)

This reveals each doodad's role:
  - "fill pixel": low NN-to-any (~1), spread across image -> interior fill
  - "outline pixel": high NN-to-same, low NN-to-any -> traces borders only
  - "stroke pixel": medium NN-to-same, forms curved paths
  - "accent pixel": very high NN-to-same, isolated dots -> rare highlights
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from collections import Counter, defaultdict
import math
import statistics

sys.path.insert(0, str(Path(__file__).parent))
from parse_hideout import load_hideout

UPLOAD = Path("/home/z/my-project/upload")
OUT = Path("/home/z/my-project/download/per_type_stats.json")


def nn_stats(points: list[tuple[int, int]]) -> dict:
    if len(points) < 2:
        return {"n": len(points), "median": None, "mean": None}
    dists = []
    for i, (xi, yi) in enumerate(points):
        best = float("inf")
        for j, (xj, yj) in enumerate(points):
            if i == j:
                continue
            dx = xi - xj
            dy = yi - yj
            d2 = dx*dx + dy*dy
            if d2 < best:
                best = d2
        dists.append(math.sqrt(best))
    return {
        "n": len(points),
        "min": round(min(dists), 3),
        "median": round(statistics.median(dists), 3),
        "mean": round(statistics.mean(dists), 3),
        "p90": round(sorted(dists)[int(0.9 * len(dists))], 3),
        "max": round(max(dists), 3),
    }


def nn_to_any(points: list[tuple[int, int]], all_points: list[tuple[int, int]]) -> dict:
    """NN distance from each point in `points` to nearest point in `all_points`."""
    if not points or not all_points:
        return {}
    dists = []
    for (xi, yi) in points:
        best = float("inf")
        for (xj, yj) in all_points:
            dx = xi - xj
            dy = yi - yj
            d2 = dx*dx + dy*dy
            if d2 < best:
                best = d2
        dists.append(math.sqrt(best))
    return {
        "median": round(statistics.median(dists), 3),
        "mean": round(statistics.mean(dists), 3),
        "max": round(max(dists), 3),
    }


def classify_role(same: dict, any_d: dict, n: int, total: int) -> str:
    """Heuristic role classifier based on same-type NN vs any-type NN."""
    if same["median"] is None:
        return "singleton"  # only 1 placement
    ratio_same_to_any = same["median"] / max(any_d["median"], 0.001)
    share = n / total
    if same["median"] <= 2.0 and share > 0.20:
        return "fill"        # dense + abundant -> interior fill pixel
    if ratio_same_to_any > 3.0 and share < 0.10:
        return "outline"     # sparse same-type, dense any -> border trace
    if same["median"] > 5.0 and share < 0.05:
        return "accent"      # very sparse, isolated -> highlight
    if 2.0 < same["median"] <= 8.0 and share > 0.05:
        return "stroke"      # medium spacing, mid-abundance -> brush stroke
    return "mixed"


def analyze_file(path: Path) -> dict:
    data = load_hideout(path)
    placements = data["placements"]
    if not placements:
        return {"file": path.name, "error": "empty"}

    all_points = [(p["x"], p["y"]) for p in placements]
    by_name = defaultdict(list)
    for p in placements:
        by_name[p["name"]].append(p)

    name_counts = Counter(p["name"] for p in placements)
    types = []
    for name, count in name_counts.most_common():
        pts = [(p["x"], p["y"]) for p in by_name[name]]
        same_stats = nn_stats(pts)
        any_stats = nn_to_any(pts, all_points)
        role = classify_role(same_stats, any_stats, count, len(placements))
        types.append({
            "name": name,
            "count": count,
            "share_pct": round(100 * count / len(placements), 1),
            "nn_within_type": same_stats,
            "nn_to_any_type": any_stats,
            "role": role,
            "centroid": {
                "x": round(sum(p[0] for p in pts) / len(pts), 1),
                "y": round(sum(p[1] for p in pts) / len(pts), 1),
            },
        })

    return {
        "file": path.name,
        "hideout_name": data["hideout_name"],
        "n_placements": len(placements),
        "types": types,
    }


def main():
    results = []
    for f in sorted(UPLOAD.glob("*.hideout")):
        print(f"\n=== {f.name} ===")
        r = analyze_file(f)
        results.append(r)
        print(f"  Total: {r['n_placements']}")
        print(f"  {'Type':<35} {'N':>5} {'%':>5} {'NN-same':>10} {'NN-any':>8} {'role':<10}")
        for t in r["types"][:12]:
            same = t["nn_within_type"]["median"]
            anym = t["nn_to_any_type"].get("median", "-")
            print(f"  {t['name'][:33]:<35} {t['count']:>5} {t['share_pct']:>5.1f} "
                  f"{str(same):>10} {str(anym):>8} {t['role']:<10}")

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to {OUT}")


if __name__ == "__main__":
    main()
