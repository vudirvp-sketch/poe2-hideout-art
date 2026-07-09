"""Render a top-down PNG preview of a Hideout.

Each decoration type gets a distinct colour; functional objects (NPCs,
benches, stash) are rendered as grey squares. The Y axis grows upward
to match world coordinates.

Optional dependency: matplotlib. The rest of the package works without
matplotlib installed — only this module requires it.
"""

from __future__ import annotations

from pathlib import Path

from .constants import HASH_TO_NAME
from .parser import Hideout

# Default colour palette per decoration type.
# Hex values approximate the in-game pixel-sampled RGB from DECO_CATALOG.md
# so that the preview roughly matches what the user will see in PoE2.
DEFAULT_COLORS: dict[str, str] = {
    # Original Canal Hideout art (0.1.0)
    "Long Grass":    "#88775d",  # (136,119,93) brown-tan
    "Falling Sand":  "#917d65",  # (145,125,101) tan
    "Fringe Moss":   "#8bc34a",  # bright green (RGB unverified — see KI in DECO_CATALOG)
    "Sand Tussock":  "#70634f",  # (112,99,79) dark olive-tan
    # Warm-tone earth (0.2.1)
    "Maraket Rubble":     "#7d7057",  # (125,112,87) neutral brown
    "Maraket Treasures":  "#746655",  # (116,102,85)
    "Maraket Samovar":    "#c29d76",  # (194,157,118) copper
    "Maraket Ornament":   "#716852",  # (113,104,82)
    "Coastal Pebble":     "#7f6f56",  # (127,111,86) tan
    # New Canal Hideout art (0.2.2)
    "Cordilina":           "#3a7d3a",  # green decorative plant
    "Petrified Cave Figure": "#9c8a6e",  # warm brown
    "Coastal Bush":        "#726246",  # (114,98,70)
    "Small Coastal Stone": "#51503c",  # (81,80,60) dark warm-gray
    "Medium Coastal Stone":"#474332",  # (71,67,50) darker
    "Slender Seedling":    "#695d43",  # (105,93,67) dark olive-tan
    "Log":                 "#a28a6b",  # (162,138,107) warm brown
    "Beech Tree":          "#585142",  # (88,81,66) dark gray-brown
    "Pile of Leaves":      "#7a6d5b",  # (122,109,91)
    "Cave Fossil":         "#9f886d",  # (159,136,109)
    "Cave Coral":          "#aa9072",  # (170,144,114)
    "Summit Brazier":      "#9c856a",  # (156,133,106)
    # Marble furniture — KI-12 conflict (pixel-sampled dark / VLM light)
    # Preview uses VLM light values because they match visual expectation;
    # img2hideout palette uses pixel-sampled dark values.
    "Marble Bench":   "#d2d2cd",  # VLM (210,210,205)
    "Marble Table":   "#c4aa88",  # (196,170,136) cream — pixel-sampled
    "Marble Walls":   "#d2d2cd",  # VLM (210,210,205)
    "Marble Fountain":"#e6e6dc",  # VLM (230,230,220)
    # Camp props
    "Camp Crate":     "#8a7a5e",  # (138,122,94)
    "Camp Gear":      "#464238",  # (70,66,56)
    # Aquatic
    "Seaweed":        "#7e6f57",  # (126,111,87)
    # Functional / large (not art, but rendered for context)
    "Atziri Statue":  "#b71c1c",  # dark red
}

DEFAULT_SIZES: dict[str, int] = {
    "Long Grass":    18,
    "Falling Sand":  20,
    "Fringe Moss":   18,
    "Sand Tussock":  22,
    "Maraket Rubble":     20,
    "Maraket Treasures":  22,
    "Maraket Samovar":    24,
    "Maraket Ornament":   20,
    "Coastal Pebble":     26,
    "Cordilina":           20,
    "Petrified Cave Figure": 40,
    "Coastal Bush":        26,
    "Small Coastal Stone": 20,
    "Medium Coastal Stone":24,
    "Slender Seedling":    20,
    "Log":                 28,
    "Beech Tree":          36,
    "Pile of Leaves":      22,
    "Cave Fossil":         20,
    "Cave Coral":          22,
    "Summit Brazier":      24,
    "Marble Bench":        30,
    "Marble Table":        40,
    "Marble Walls":        30,
    "Marble Fountain":     36,
    "Camp Crate":          22,
    "Camp Gear":           20,
    "Seaweed":             26,
    "Atziri Statue":       60,
}

FUNC_COLOR = "#90a4ae"


def render_png(
    h: Hideout,
    out_path: str | Path,
    *,
    art_only: bool = False,
    show_labels: bool = True,
    figsize: tuple[float, float] = (15, 9),
    dpi: int = 140,
    colors: dict[str, str] | None = None,
    sizes: dict[str, int] | None = None,
) -> Path:
    """Render the hideout to a PNG file.

    Parameters
    ----------
    h : Hideout
        The hideout to render.
    out_path : path-like
        Where to save the PNG.
    art_only : bool
        If True, only render decorative placements (skip NPCs/benches).
    show_labels : bool
        Annotate functional objects with their name.
    figsize, dpi : matplotlib options.
    colors, sizes : optional override dicts keyed by decoration name.

    Returns
    -------
    Path
        The resolved output path.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        raise ImportError(
            "matplotlib is required for render_png. "
            "Install it with: pip install hideout-art[preview]"
        ) from e

    colors = colors or DEFAULT_COLORS
    sizes = sizes or DEFAULT_SIZES

    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    seen: set[str] = set()

    for p in h.placements:
        # Resolve decoration name via hash so that localised names (e.g.
        # Russian "Береговая галька") still find the right colour/size entry
        # in DEFAULT_COLORS (which is keyed by English canonical names).
        canonical = HASH_TO_NAME.get(p.hash, p.name)
        is_art = canonical in colors
        if art_only and not (p.is_art or is_art):
            continue

        if is_art:
            color = colors[canonical]
            size = sizes.get(canonical, 20)
            label = canonical if canonical not in seen else None
            ax.scatter(p.x, p.y, c=color, s=size, alpha=0.85,
                       edgecolors="none", label=label, zorder=3)
            seen.add(canonical)
        else:
            label = "Functional" if "Functional" not in seen else None
            ax.scatter(p.x, p.y, c=FUNC_COLOR, s=45, marker="s",
                       edgecolors="black", linewidths=0.4, zorder=2,
                       label=label)
            seen.add("Functional")
            if show_labels:
                ax.annotate(p.name, (p.x, p.y), fontsize=6, ha="center",
                            va="bottom", xytext=(0, 3),
                            textcoords="offset points", color="#37474f")

    ax.set_aspect("equal")
    ax.set_title(
        f"{h.hideout_name}  (hash {h.hideout_hash})  —  {len(h)} placements"
    )
    ax.set_xlabel("x (world units)")
    ax.set_ylabel("y (world units, grows upward)")
    ax.grid(True, alpha=0.25, linestyle=":")
    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=dpi)
    plt.close(fig)
    return out
