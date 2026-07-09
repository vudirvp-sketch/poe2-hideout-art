"""
Render each .hideout file as a 2D scatter plot, colored by doodad hash.

Goal: visually see how images are composed -- grid? jittered points?
color blocks by hash? line strokes? Identifies the actual drawing patterns.

Output: /home/z/my-project/download/plot_<filename>.png
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


def plot_file(path: Path, out_path: Path):
    data = load_hideout(path)
    placements = data["placements"]
    if not placements:
        return

    # Group by hash, color by hash (top 8 types get distinct colors, rest grey)
    name_counts = Counter(p["name"] for p in placements)
    top_names = [n for n, _ in name_counts.most_common(8)]
    # tab10 has 10 distinct colors
    cmap = plt.get_cmap("tab10")
    name_to_color = {n: cmap(i) for i, n in enumerate(top_names)}

    fig, ax = plt.subplots(figsize=(10, 12), constrained_layout=True)

    # Plot each name-group separately so legend works
    by_name = defaultdict(list)
    for p in placements:
        by_name[p["name"]].append(p)

    # plot top names first, then "other" as grey dots
    for name in top_names:
        ps = by_name[name]
        xs = [p["x"] for p in ps]
        ys = [-p["y"] for p in ps]  # flip y because hideout y grows downward
        ax.scatter(xs, ys, s=8, c=[name_to_color[name]], label=f"{name} ({len(ps)})", alpha=0.7, edgecolors='none')
    # others
    other_ps = [p for n, ps in by_name.items() if n not in top_names for p in ps]
    if other_ps:
        xs = [p["x"] for p in other_ps]
        ys = [-p["y"] for p in other_ps]
        ax.scatter(xs, ys, s=4, c='lightgray', label=f"other ({len(other_ps)})", alpha=0.5, edgecolors='none')

    ax.set_aspect('equal')
    ax.set_title(f"{path.name}\n{data['hideout_name']} (hash={data['hideout_hash']}) — {len(placements)} placements", fontsize=11)
    ax.legend(loc='upper right', fontsize=8, framealpha=0.9)
    ax.set_xlabel("x")
    ax.set_ylabel("y (negated)")
    ax.grid(True, alpha=0.3)

    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    print(f"  saved {out_path.name}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted(UPLOAD.glob("*.hideout")):
        print(f"plotting {f.name}...")
        out = OUT / f"plot_{f.stem}.png"
        plot_file(f, out)

        # Also a "rotation heatmap" -- show rotation as color to see directional patterns
        data = load_hideout(f)
        placements = data["placements"]
        if not placements:
            continue
        fig, ax = plt.subplots(figsize=(10, 12), constrained_layout=True)
        # Normalize r to 0..1 (r is 0..65535)
        rs = [p["r"] / 65536.0 for p in placements]
        xs = [p["x"] for p in placements]
        ys = [-p["y"] for p in placements]
        sc = ax.scatter(xs, ys, s=8, c=rs, cmap='hsv', alpha=0.8, edgecolors='none', vmin=0, vmax=1)
        ax.set_aspect('equal')
        ax.set_title(f"{f.name} — rotation heatmap (hue = angle 0-360°)", fontsize=11)
        ax.set_xlabel("x"); ax.set_ylabel("y (negated)")
        ax.grid(True, alpha=0.3)
        plt.colorbar(sc, ax=ax, label='rotation (0=0°, 1=360°)')
        out2 = OUT / f"rot_{f.stem}.png"
        fig.savefig(out2, dpi=120)
        plt.close(fig)
        print(f"  saved {out2.name}")


if __name__ == "__main__":
    main()
