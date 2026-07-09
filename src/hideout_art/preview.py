"""Render a top-down PNG preview of a Hideout.

Each decoration type gets a distinct colour; functional objects (NPCs,
benches, stash) are rendered as grey squares. The Y axis grows upward
to match world coordinates.

Optional dependency: matplotlib. The rest of the package works without
matplotlib installed — only this module requires it.
"""

from __future__ import annotations

from pathlib import Path

from .parser import Hideout

# Default colour palette per decoration type. Extend as the catalogue grows.
DEFAULT_COLORS: dict[str, str] = {
    "Long Grass":   "#2e7d32",  # green
    "Falling Sand": "#f48fb1",  # pink
    "Fringe Moss":  "#8bc34a",  # light green
    "Sand Tussock": "#4e342e",  # dark brown (hair)
    "Atziri Statue": "#b71c1c", # dark red
}

DEFAULT_SIZES: dict[str, int] = {
    "Long Grass":   16,
    "Falling Sand": 22,
    "Fringe Moss":  20,
    "Sand Tussock": 40,
    "Atziri Statue": 60,
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
        is_art = p.name in colors
        if art_only and not is_art:
            continue

        if is_art:
            color = colors[p.name]
            size = sizes.get(p.name, 20)
            label = p.name if p.name not in seen else None
            ax.scatter(p.x, p.y, c=color, s=size, alpha=0.85,
                       edgecolors="none", label=label, zorder=3)
            seen.add(p.name)
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
