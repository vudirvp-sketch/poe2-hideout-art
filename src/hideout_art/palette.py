"""Colour-to-decoration palette for image-driven hideout generation.

The ``img2hideout`` module uses a ``Palette`` to decide which decoration
to place for each pixel of an input image. A palette is just a list of
``ColorEntry`` records: a target colour, a decoration name (must exist
in ``KNOWN_HASHES``) and an optional max count.

Users can either:

* use ``default_palette()`` (built from observed Canal Hideout art), or
* load a JSON palette file via ``Palette.from_json_file()``, or
* build one programmatically with ``Palette(entries=[...])``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .constants import KNOWN_HASHES


@dataclass
class ColorEntry:
    """One (colour -> decoration) mapping."""

    color: tuple[int, int, int]  # RGB, 0..255
    decoration: str              # must exist in KNOWN_HASHES
    weight: float = 1.0          # relative sampling weight
    max_count: int | None = None  # if set, stop after this many

    def as_dict(self) -> dict:
        return {
            "color": list(self.color),
            "decoration": self.decoration,
            "weight": self.weight,
            "max_count": self.max_count,
        }


@dataclass
class Palette:
    """An ordered list of ColorEntry records."""

    entries: list[ColorEntry]

    def __post_init__(self) -> None:
        for e in self.entries:
            if e.decoration not in KNOWN_HASHES:
                raise ValueError(
                    f"Unknown decoration '{e.decoration}'. "
                    f"Known: {sorted(KNOWN_HASHES)}"
                )

    def as_dict(self) -> dict:
        return {"entries": [e.as_dict() for e in self.entries]}

    def to_json(self, path: str | Path) -> Path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.as_dict(), indent=2), encoding="utf-8")
        return p

    @classmethod
    def from_json_file(cls, path: str | Path) -> Palette:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> Palette:
        entries = [
            ColorEntry(
                color=tuple(e["color"]),
                decoration=e["decoration"],
                weight=e.get("weight", 1.0),
                max_count=e.get("max_count"),
            )
            for e in data["entries"]
        ]
        return cls(entries=entries)


def default_palette() -> Palette:
    """The palette observed in the reference Canal Hideout composition.

    Colour choices follow the in-game look:

    * pink   -> Falling Sand  (face glow)
    * green  -> Long Grass    (body silhouette)
    * light  -> Fringe Moss   (leg volume)
    * dark   -> Sand Tussock  (hair)
    """
    return Palette(entries=[
        ColorEntry(color=(248, 187, 208), decoration="Falling Sand"),  # pink
        ColorEntry(color=(46,  125, 50),  decoration="Long Grass"),    # green
        ColorEntry(color=(139, 195, 74),  decoration="Fringe Moss"),   # light green
        ColorEntry(color=(78,  52,  46),  decoration="Sand Tussock"),  # dark brown
    ])
