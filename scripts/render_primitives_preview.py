#!/usr/bin/env python3
"""Render a clear preview PNG of the primitives-injected hideout.

This is a thicker, more readable preview than the default ``render_png`` —
it colours each decoration type distinctly, draws a bounding box for the
Canal Hideout canvas, and adds a legend.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Font fallback for any non-Latin glyphs.
for f in (
    "/usr/share/fonts/truetype/chinese/NotoSansSC-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
):
    try:
        fm.fontManager.addfont(f)
    except Exception:
        pass
plt.rcParams["font.sans-serif"] = ["Noto Sans SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "src"))

from hideout_art import Hideout  # noqa: E402
from hideout_art.constants import (  # noqa: E402
    CANAL_HIDEOUT_BOUNDS,
    HASH_TO_NAME,
)

# Distinct colour per art decoration (one per hash). Functional objects
# get a single neutral colour.
ART_COLORS: dict[str, str] = {
    "Long Grass":          "#7fa05a",
    "Falling Sand":        "#e6c992",
    "Fringe Moss":         "#8cc24a",
    "Sand Tussock":        "#9a8466",
    "Maraket Rubble":      "#7d6457",
    "Maraket Treasures":   "#c79a5e",
    "Maraket Samovar":     "#c29669",
    "Maraket Ornament":    "#715f44",
    "Coastal Pebble":      "#b69b6f",
    "Cordilina":           "#5a8a3a",
    "Petrified Cave Figure": "#a89576",
    "Coastal Bush":        "#6f5a3e",
    "Small Coastal Stone": "#5e5740",
    "Medium Coastal Stone": "#4a4634",
    "Slender Seedling":    "#6f6244",
    "Log":                 "#a7866b",
    "Beech Tree":          "#5e5642",
    "Pile of Leaves":      "#7d6b54",
    "Cave Fossil":         "#a78e6f",
    "Cave Coral":          "#b69070",
    "Summit Brazier":      "#c9975a",
    "Marble Bench":        "#cfc6b8",
    "Marble Table":        "#e0d4be",
    "Marble Walls":        "#bdb29c",
    "Marble Fountain":     "#d8d0bd",
    "Camp Crate":          "#8a7558",
    "Camp Gear":           "#49443a",
    "Seaweed":             "#7e6f50",
}
FUNCTIONAL_COLOR = "#3b6ea5"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: render_primitives_preview.py <hideout> [out.png]",
              file=sys.stderr)
        return 2
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) >= 3 else \
        src.with_suffix(".preview.png")
    h = Hideout.from_file(src)
    art = [p for p in h if p.is_art]
    functional = [p for p in h if not p.is_art]

    fig, ax = plt.subplots(figsize=(12, 9), constrained_layout=True)

    # Canvas bounds.
    x_min, y_min, x_max, y_max = CANAL_HIDEOUT_BOUNDS
    rect = mpatches.Rectangle(
        (x_min, y_min), x_max - x_min, y_max - y_min,
        linewidth=1.5, edgecolor="#888", facecolor="#f5f1ea",
        zorder=0,
    )
    ax.add_patch(rect)
    ax.text(x_min, y_max + 4,
            f"Canal Hideout canvas {CANAL_HIDEOUT_BOUNDS}",
            fontsize=9, color="#555", va="bottom")

    # Functional objects: large blue circles with name labels.
    for p in functional:
        canonical = HASH_TO_NAME.get(p.hash, p.name)
        ax.scatter(p.x, p.y, s=140, c=FUNCTIONAL_COLOR,
                   marker="s", edgecolors="white", linewidths=0.8,
                   zorder=4, alpha=0.7)
        ax.annotate(canonical, (p.x, p.y),
                    xytext=(4, 4), textcoords="offset points",
                    fontsize=7, color="#2a4a6a", zorder=5)

    # Art placements: coloured dots, one per decoration type.
    legend_handles: dict[str, Line2D] = {}
    for p in art:
        canonical = HASH_TO_NAME.get(p.hash, p.name)
        color = ART_COLORS.get(canonical, "#888")
        ax.scatter(p.x, p.y, s=90, c=color, marker="o",
                   edgecolors="black", linewidths=0.4, zorder=3)
        if canonical not in legend_handles:
            legend_handles[canonical] = Line2D(
                [0], [0], marker="o", color="w", markerfacecolor=color,
                markeredgecolor="black", markersize=8, label=canonical,
            )

    # Centre marker.
    cx, cy = 780, 657
    ax.axvline(cx, color="#ccc", linestyle=":", linewidth=0.8, zorder=1)
    ax.axhline(cy, color="#ccc", linestyle=":", linewidth=0.8, zorder=1)
    ax.scatter([cx], [cy], s=60, c="red", marker="+",
               linewidths=1.2, zorder=2)
    ax.text(cx + 2, cy + 2, "centre (780, 657)", fontsize=7,
            color="red", zorder=2)

    # Legend.
    art_handles = [legend_handles[k] for k in sorted(legend_handles)]
    art_handles.append(Line2D(
        [0], [0], marker="s", color="w", markerfacecolor=FUNCTIONAL_COLOR,
        markeredgecolor="white", markersize=8,
        label=f"functional ({len(functional)})",
    ))
    ax.legend(handles=art_handles, loc="upper left",
              bbox_to_anchor=(1.02, 1.0), fontsize=8,
              title=f"art placements: {len(art)}",
              title_fontsize=9)

    ax.set_xlim(x_min - 20, x_max + 20)
    ax.set_ylim(y_min - 20, y_max + 20)
    ax.set_aspect("equal")
    ax.set_xlabel("x (world units)")
    ax.set_ylabel("y (world units)")
    ax.set_title(
        f"Drawing primitives — {src.name}\n"
        f"{len(art)} art + {len(functional)} functional = {len(h)} total placements",
        fontsize=11,
    )
    ax.grid(True, color="#ddd", linewidth=0.4, zorder=0)

    fig.savefig(out, dpi=140)
    print(f"[preview] {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
