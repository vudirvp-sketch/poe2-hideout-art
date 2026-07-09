"""
Per-type scatter grid for one example file.

Shows each top doodad type in its own subplot, so you can SEE which type
forms the fill, which forms the outline, which forms strokes.
"""
from __future__ import annotations
import sys
from pathlib import Path
from collections import Counter, defaultdict
import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

sys.path.insert(0, str(Path(__file__).parent))
from parse_hideout import load_hideout

UPLOAD = Path("/home/z/my-project/upload")
OUT = Path("/home/z/my-project/download")


def per_type_grid(path: Path, out_path: Path, top_n: int = 9):
    data = load_hideout(path)
    placements = data["placements"]
    name_counts = Counter(p["name"] for p in placements)
    top = name_counts.most_common(top_n)

    by_name = defaultdict(list)
    for p in placements:
        by_name[p["name"]].append(p)

    # All-points background for context
    all_x = [p["x"] for p in placements]
    all_y = [-p["y"] for p in placements]
    bbox = (min(all_x), max(all_x), min(all_y), max(all_y))

    n = len(top)
    cols = 3
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 5),
                              constrained_layout=True)
    axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]

    for i, (name, count) in enumerate(top):
        ax = axes[i]
        # background: all points in light grey
        ax.scatter(all_x, all_y, s=3, c='lightgrey', alpha=0.3, edgecolors='none')
        # foreground: this type
        ps = by_name[name]
        xs = [p["x"] for p in ps]
        ys = [-p["y"] for p in ps]
        ax.scatter(xs, ys, s=10, c='red', alpha=0.8, edgecolors='none')
        ax.set_title(f"{name}\n{count} ({100*count/len(placements):.1f}%)", fontsize=9)
        ax.set_aspect('equal')
        ax.set_xlim(bbox[0] - 5, bbox[1] + 5)
        ax.set_ylim(bbox[2] - 5, bbox[3] + 5)
        ax.grid(True, alpha=0.2)

    # Hide unused subplots
    for i in range(n, len(axes)):
        axes[i].set_visible(False)

    fig.suptitle(f"{path.name}\n{data['hideout_name']} — per-type breakdown (red = this type, grey = all others)",
                  fontsize=11)
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
    print(f"  saved {out_path.name}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted(UPLOAD.glob("*.hideout")):
        print(f"per-type grid for {f.name}...")
        per_type_grid(f, OUT / f"pertype_{f.stem}.png")


if __name__ == "__main__":
    main()
