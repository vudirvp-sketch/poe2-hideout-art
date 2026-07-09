"""
hideout_art — read, transform and emit Path of Exile 2 .hideout files.

A .hideout file is a JSON document whose ``doodads`` object contains
duplicate keys (one per placement). Standard ``json.load`` collapses
duplicates, so this package uses a tolerant regex scanner.

Public API:
    from hideout_art import Hideout, Placement
    h = Hideout.from_file("path/to/file.hideout")
    h.shift(dx=50, dy=-20)
    h.to_file("out.hideout")
"""

from .img2hideout import image_to_hideout
from .palette import Palette, default_palette
from .parser import Hideout, Placement
from .preview import render_png
from .primitives import (
    PrimitiveOptions,
    arc,
    bezier_curve,
    center_composition,
    crosshatch,
    filled_circle,
    grid,
    hollow_circle,
    line,
    mosaic_composition,
    polygon,
    polyline,
    rectangle,
    s_snake,
    safe_spacing,
    thick_arc,
    thick_line_with_contours,
    thick_ring,
)
from .transforms import mirror_x, mirror_y, rotate, shift
from .writer import write_hideout

__version__ = "0.2.9"
__all__ = [
    "Hideout",
    "Placement",
    "write_hideout",
    "shift",
    "rotate",
    "mirror_x",
    "mirror_y",
    "render_png",
    "Palette",
    "default_palette",
    "image_to_hideout",
    # Primitives (0.2.7) — core drawing shapes.
    "PrimitiveOptions",
    "safe_spacing",
    "line",
    "polyline",
    "hollow_circle",
    "filled_circle",
    "s_snake",
    "thick_line_with_contours",
    "center_composition",
    # Primitives (0.2.8) — mosaic / bas-relief shapes.
    "arc",
    "rectangle",
    "polygon",
    "grid",
    # Primitives (0.2.9) — mosaic v2 / portrait-grade shapes.
    "bezier_curve",
    "thick_ring",
    "thick_arc",
    "crosshatch",
    "mosaic_composition",
    "__version__",
]
