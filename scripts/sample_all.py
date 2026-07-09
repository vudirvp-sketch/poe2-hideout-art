#!/usr/bin/env python3
"""Run sample_pixels.py on all 7 исходники screenshot/hideout pairs.

Re-runs sampling with --include-functional so we can sanity-check the
calibration on each screenshot (Stash / Waypoint / Well should give
believable brown wood-stone colours). Produces a single consolidated
report at scripts/sampled_all.json plus per-screenshot diagnostics.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ISXODNIKI = REPO_ROOT / "исходники"
SCRIPTS = REPO_ROOT / "scripts"

PAIRS = [
    "камни и кустарники",
    "укрошения, хорошие подложки будто и обломки",
    "еще элементы",
    "всякое",
    "галька",
    "еще камни и растения",
    "водоросли и летающий песок",
]


def safe_stem(name: str) -> str:
    return name.replace(" ", "_").replace(",", "").replace(".", "")


def main() -> int:
    results: list[dict] = []
    for stem in PAIRS:
        hideout = ISXODNIKI / f"{stem}.hideout"
        screenshot = ISXODNIKI / f"{stem}.jpg"
        if not hideout.exists() or not screenshot.exists():
            print(f"SKIP: {stem} (missing files)")
            continue
        safe = safe_stem(stem)
        out_json = SCRIPTS / f"sampled_{safe}.json"
        out_png = SCRIPTS / f"diagnostic_{safe}.png"
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "sample_pixels.py"),
            str(hideout),
            str(screenshot),
            "--world-bbox", "functional",
            "--include-functional",
            "--output", str(out_json),
            "--diagnostic", str(out_png),
        ]
        print(f"\n=== {stem} ===")
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
        print(r.stdout[-500:])
        if r.returncode != 0:
            print(f"FAILED: {r.stderr[-500:]}")
            continue
        data = json.loads(out_json.read_text(encoding="utf-8"))
        results.append({
            "stem": stem,
            "safe_stem": safe,
            "hideout_file": str(hideout),
            "screenshot_file": str(screenshot),
            "image_size": data["_meta"]["image_size"],
            "calibration": data["_meta"]["calibration"],
            "decorations": data["decorations"],
        })

    # Write consolidated report
    out_path = SCRIPTS / "sampled_all.json"
    out_path.write_text(
        json.dumps(
            {
                "_meta": {
                    "tool_version": "0.2.6",
                    "n_screenshots": len(results),
                    "note": (
                        "Pixel-sampled RGB measurements for all 7 исходники/"
                        "screenshot+hideout pairs. Auto-calibration with "
                        "functional bbox. Sanity-check each screenshot by "
                        "verifying that Stash/Waypoint give believable "
                        "brown wood/stone colours (not blue/green/black)."
                    ),
                },
                "screenshots": results,
            },
            indent=2, ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nConsolidated report: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
