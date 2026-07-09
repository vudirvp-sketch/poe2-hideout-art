"""
Quantitative spatial statistics for hideout placements.

Confirms or refutes the qualitative VLM observations with hard numbers:
  - Nearest-neighbor distance distribution (median, percentiles)
  - Grid detection: if points are on a grid, NN distances cluster at fixed step
  - Local rotation correlation: do neighbors share rotation? (Moran's I proxy)
  - Point density per unit area
  - Aspect ratio / orientation of the bounding ellipse
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from collections import Counter
import math
import statistics

sys.path.insert(0, str(Path(__file__).parent))
from parse_hideout import load_hideout

UPLOAD = Path("/home/z/my-project/upload")
OUT = Path("/home/z/my-project/download/spatial_stats.json")


def angle_bins(r_values: list[int], bins: int = 8) -> dict:
    """Bin rotations (0..65535 -> 0..360 deg) into N equal bins."""
    counts = [0] * bins
    for r in r_values:
        deg = (r / 65536.0) * 360.0
        b = int(deg / (360.0 / bins)) % bins
        counts[b] += 1
    return {f"{i*(360//bins)}-{(i+1)*(360//bins)}deg": c for i, c in enumerate(counts)}


def nearest_neighbor_stats(placements: list[dict]) -> dict:
    """O(N^2) NN distance. Fine for N ~ 500-800."""
    pts = [(p["x"], p["y"]) for p in placements]
    n = len(pts)
    if n < 2:
        return {}
    nn_dists = []
    for i in range(n):
        xi, yi = pts[i]
        best = float("inf")
        for j in range(n):
            if i == j:
                continue
            dx = xi - pts[j][0]
            dy = yi - pts[j][1]
            d = dx * dx + dy * dy
            if d < best:
                best = d
        nn_dists.append(math.sqrt(best))

    sorted_d = sorted(nn_dists)
    def pct(p):
        idx = min(len(sorted_d) - 1, int(p * len(sorted_d)))
        return sorted_d[idx]

    return {
        "n": n,
        "min": round(min(nn_dists), 3),
        "p10": round(pct(0.10), 3),
        "p25": round(pct(0.25), 3),
        "median": round(statistics.median(nn_dists), 3),
        "mean": round(statistics.mean(nn_dists), 3),
        "p75": round(pct(0.75), 3),
        "p90": round(pct(0.90), 3),
        "max": round(max(nn_dists), 3),
        "stdev": round(statistics.stdev(nn_dists), 3),
    }


def grid_detection(placements: list[dict]) -> dict:
    """Detect if points sit on a regular grid.

    Method: round all x and y to nearest integer, look at unique values.
    If grid -> small set of distinct x and y values covering all points.
    Also check x-difference histogram for dominant step.
    """
    xs = sorted(set(p["x"] for p in placements))
    ys = sorted(set(p["y"] for p in placements))
    # If gridded, len(unique_x) << n
    # Compute consecutive gaps in unique x
    if len(xs) >= 2:
        x_gaps = [xs[i+1] - xs[i] for i in range(len(xs) - 1)]
        x_gap_counter = Counter(x_gaps)
        top_x_gap = x_gap_counter.most_common(1)[0]
    else:
        x_gaps, top_x_gap = [], (None, 0)
    if len(ys) >= 2:
        y_gaps = [ys[i+1] - ys[i] for i in range(len(ys) - 1)]
        y_gap_counter = Counter(y_gaps)
        top_y_gap = y_gap_counter.most_common(1)[0]
    else:
        y_gaps, top_y_gap = [], (None, 0)

    return {
        "n_distinct_x": len(xs),
        "n_distinct_y": len(ys),
        "x_span": (xs[0], xs[-1]) if xs else None,
        "y_span": (ys[0], ys[-1]) if ys else None,
        "top_x_gap": {"gap": top_x_gap[0], "count": top_x_gap[1]},
        "top_y_gap": {"gap": top_y_gap[0], "count": top_y_gap[1]},
        "x_gap_diversity": len(set(x_gaps)),
        "y_gap_diversity": len(set(y_gaps)),
    }


def rotation_correlation(placements: list[dict]) -> dict:
    """For each point, check if its k nearest neighbors share the same rotation bin.

    If rotation is spatially correlated (Moran's I > 0), neighbors share bins
    more often than chance. We use 4-nearest-neighbor same-bin rate vs random.
    """
    import random
    random.seed(42)
    pts = [(p["x"], p["y"]) for p in placements]
    rs = [p["r"] for p in placements]
    n = len(pts)
    if n < 10:
        return {}

    # Bin rotations to 8 bins (45deg each)
    bin_of = [(r // (65536 // 8)) % 8 for r in rs]

    # For each point, find 4 nearest neighbors and check same-bin rate
    same_count = 0
    total = 0
    for i in range(n):
        xi, yi = pts[i]
        dists = []
        for j in range(n):
            if i == j:
                continue
            dx = xi - pts[j][0]
            dy = yi - pts[j][1]
            dists.append((dx*dx + dy*dy, j))
        dists.sort()
        for _, j in dists[:4]:
            if bin_of[i] == bin_of[j]:
                same_count += 1
            total += 1
    observed_rate = same_count / total if total else 0

    # Expected by chance: 1/8 = 0.125
    expected = 1/8
    # Moran's I proxy: (obs - exp) / (1 - exp)
    moran_proxy = (observed_rate - expected) / (1 - expected) if expected < 1 else 0

    return {
        "observed_same_bin_rate": round(observed_rate, 4),
        "expected_random_rate": round(expected, 4),
        "moran_proxy": round(moran_proxy, 4),
        "interpretation": (
            "spatially_correlated" if moran_proxy > 0.2 else
            "weakly_correlated" if moran_proxy > 0.05 else
            "random_like"
        ),
    }


def analyze(path: Path) -> dict:
    data = load_hideout(path)
    placements = data["placements"]
    if not placements:
        return {"file": path.name, "error": "no placements"}

    return {
        "file": path.name,
        "hideout_name": data["hideout_name"],
        "hideout_hash": data["hideout_hash"],
        "n_placements": len(placements),
        "nn_stats": nearest_neighbor_stats(placements),
        "grid_detection": grid_detection(placements),
        "rotation": {
            "angle_bins_8": angle_bins([p["r"] for p in placements], 8),
            "spatial_correlation": rotation_correlation(placements),
            "top_5_angles_deg": [
                {"deg": round((r / 65536.0) * 360, 2), "count": c}
                for r, c in Counter(p["r"] for p in placements).most_common(5)
            ],
        },
    }


def main():
    results = []
    for f in sorted(UPLOAD.glob("*.hideout")):
        print(f"\n=== {f.name} ===")
        r = analyze(f)
        results.append(r)
        print(f"  N={r['n_placements']}")
        print(f"  NN dist: median={r['nn_stats']['median']}, p25={r['nn_stats']['p25']}, p75={r['nn_stats']['p75']}, max={r['nn_stats']['max']}")
        g = r['grid_detection']
        print(f"  distinct x={g['n_distinct_x']}, y={g['n_distinct_y']}; top x gap={g['top_x_gap']}; top y gap={g['top_y_gap']}")
        print(f"  rot bins 8: {r['rotation']['angle_bins_8']}")
        print(f"  rot spatial corr: observed={r['rotation']['spatial_correlation']['observed_same_bin_rate']} "
              f"-> {r['rotation']['spatial_correlation']['interpretation']} "
              f"(moran_proxy={r['rotation']['spatial_correlation']['moran_proxy']})")
        print(f"  top 5 angles: {r['rotation']['top_5_angles_deg']}")

    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nSaved to {OUT}")


if __name__ == "__main__":
    main()
