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
from .transforms import mirror_x, mirror_y, rotate, shift
from .writer import write_hideout

__version__ = "0.2.3"
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
    "__version__",
]
