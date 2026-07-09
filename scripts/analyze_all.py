"""
Analyze all uploaded .hideout files.

For each file:
  - placement count, distinct doodad types
  - bounding box of placements (x, y ranges)
  - rotation (r) value distribution
  - variant (fv) value distribution
  - top doodad types by count
  - hash -> name mapping (since PoE2 uses PoE1 names but different hashes)

Cross-file analysis:
  - which doodad types appear in multiple files (the "image building blocks")
  - hash collisions across PoE1 vs PoE2 (same name, different hash)
"""
from __future__ import annotations
import sys
from pathlib import Path
from collections import Counter, defaultdict
import json

sys.path.insert(0, str(Path(__file__).parent))
from parse_hideout import load_hideout

UPLOAD_DIR = Path("/home/z/my-project/upload")
OUT = Path("/home/z/my-project/download/analysis_full.json")


def analyze_file(path: Path) -> dict:
    data = load_hideout(path)
    placements = data["placements"]
    if not placements:
        return {**data, "stats": None}

    xs = [p["x"] for p in placements]
    ys = [p["y"] for p in placements]
    rs = [p["r"] for p in placements]
    fvs = [p["fv"] for p in placements]

    name_counts = Counter(p["name"] for p in placements)
    hash_counts = Counter(p["hash"] for p in placements)
    r_counts = Counter(rs)
    fv_counts = Counter(fvs)

    # name -> set of hashes (collisions?) and hash -> set of names
    name_to_hashes = defaultdict(set)
    hash_to_names = defaultdict(set)
    for p in placements:
        name_to_hashes[p["name"]].add(p["hash"])
        hash_to_names[p["hash"]].add(p["name"])

    return {
        "file": path.name,
        "hideout_name": data["hideout_name"],
        "hideout_hash": data["hideout_hash"],
        "placement_count": len(placements),
        "distinct_types": len(name_counts),
        "bbox": {
            "x_min": min(xs), "x_max": max(xs),
            "y_min": min(ys), "y_max": max(ys),
            "x_span": max(xs) - min(xs),
            "y_span": max(ys) - min(ys),
        },
        "r_values": dict(r_counts.most_common()),
        "fv_values": dict(fv_counts.most_common()),
        "top_types": name_counts.most_common(20),
        "name_to_hash": {k: sorted(v) for k, v in name_to_hashes.items()},
    }


def main():
    files = sorted(UPLOAD_DIR.glob("*.hideout"))
    results = []
    for f in files:
        print(f"\n--- {f.name} ---")
        r = analyze_file(f)
        results.append(r)
        print(f"  Hideout: {r['hideout_name']} hash={r['hideout_hash']}")
        print(f"  Placements: {r['placement_count']}  distinct: {r['distinct_types']}")
        print(f"  bbox: x=[{r['bbox']['x_min']}..{r['bbox']['x_max']}] "
              f"y=[{r['bbox']['y_min']}..{r['bbox']['y_max']}] "
              f"span={r['bbox']['x_span']}x{r['bbox']['y_span']}")
        print(f"  top types:")
        for n, k in r["top_types"][:8]:
            print(f"    {n:>5}x  {k}")
        print(f"  r values (top 10): {dict(list(r['r_values'].items())[:10])}")
        print(f"  fv values (top 10): {dict(list(r['fv_values'].items())[:10])}")

    # cross-file: name frequency across all files
    name_in_files = defaultdict(lambda: defaultdict(int))  # name -> {file: count}
    name_to_hashes_global = defaultdict(set)
    for r in results:
        for n, c in r["top_types"] + [(k, v) for k, v in Counter(
            p["name"] for p in load_hideout(UPLOAD_DIR / r["file"])["placements"]
        ).items()]:
            name_in_files[n][r["file"]] += c
        for name, hashes in r["name_to_hash"].items():
            name_to_hashes_global[name].update(hashes)

    # write full json
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nFull analysis saved to {OUT}")


if __name__ == "__main__":
    main()
