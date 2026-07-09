"""Tolerant parser for PoE2 ``.hideout`` files.

Why tolerant? The ``doodads`` object inside a real export contains one
JSON object per placement, all sharing the SAME key (the decoration
name). ``json.load`` collapses duplicate keys and keeps only the last
one, which would silently drop ~99% of the data. We use a regex scanner
instead so every placement is preserved in source order.

The parser is also resilient to:

* BOM at the start of the file (UTF-8 / UTF-8-SIG)
* Unknown decoration names (kept verbatim, with their hash)
* Future additional fields inside a placement object (regex is strict
  about field order, but the writer never invents extra fields)
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .constants import (
    ART_TYPES,
    FV_FLIP_X_BIT,
    FV_VARIANT_MASK,
    HASH_TO_NAME,
    ROTATION_MODULUS,
)

# Matches a single placement entry, tolerant to whitespace.
_ENTRY_RE = re.compile(
    r'"(?P<name>[^"]+)"\s*:\s*\{\s*'
    r'"hash"\s*:\s*(?P<hash>\d+)\s*,\s*'
    r'"x"\s*:\s*(?P<x>-?\d+)\s*,\s*'
    r'"y"\s*:\s*(?P<y>-?\d+)\s*,\s*'
    r'"r"\s*:\s*(?P<r>-?\d+)\s*,\s*'
    r'"fv"\s*:\s*(?P<fv>-?\d+)\s*'
    r'\}'
)

# Header fields, scanned once before the doodads block.
_HEADER_PATTERNS = {
    "version":       r'"version"\s*:\s*(\d+)',
    "language":      r'"language"\s*:\s*"([^"]+)"',
    "hideout_name":  r'"hideout_name"\s*:\s*"([^"]+)"',
    "hideout_hash":  r'"hideout_hash"\s*:\s*(\d+)',
}


@dataclass
class Placement:
    """A single decoration placement in a hideout."""

    name: str
    hash: int
    x: int
    y: int
    r: int = 0       # rotation, 0..65535 (see ROTATION_MODULUS)
    fv: int = 0      # flip_x bit | variant index

    @property
    def rotation_degrees(self) -> float:
        """Rotation in degrees, 0..360."""
        return (self.r / ROTATION_MODULUS) * 360.0

    @property
    def flip_x(self) -> bool:
        """Whether this placement is mirrored horizontally."""
        return bool(self.fv & FV_FLIP_X_BIT)

    @property
    def variant(self) -> int:
        """Variant index (0..127)."""
        return self.fv & FV_VARIANT_MASK

    @property
    def is_art(self) -> bool:
        """Whether this decoration is in the artistic layer (see ART_TYPES)."""
        return self.name in ART_TYPES

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Hideout:
    """An entire hideout: header + ordered list of placements."""

    version: int = 1
    language: str = "English"
    hideout_name: str = ""
    hideout_hash: int = 0
    placements: list[Placement] = field(default_factory=list)

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    @classmethod
    def from_file(cls, path: str | Path) -> Hideout:
        p = Path(path)
        text = p.read_text(encoding="utf-8-sig")
        return cls._from_text(text)

    @classmethod
    def from_string(cls, text: str) -> Hideout:
        return cls._from_text(text)

    @classmethod
    def _from_text(cls, text: str) -> Hideout:
        header = {}
        for key, pat in _HEADER_PATTERNS.items():
            m = re.search(pat, text)
            if m is None:
                continue
            val = m.group(1)
            header[key] = int(val) if key in ("version", "hideout_hash") else val

        placements = [
            Placement(
                name=m["name"],
                hash=int(m["hash"]),
                x=int(m["x"]),
                y=int(m["y"]),
                r=int(m["r"]),
                fv=int(m["fv"]),
            )
            for m in _ENTRY_RE.finditer(text)
        ]
        return cls(
            version=header.get("version", 1),
            language=header.get("language", "English"),
            hideout_name=header.get("hideout_name", ""),
            hideout_hash=header.get("hideout_hash", 0),
            placements=placements,
        )

    # ------------------------------------------------------------------ #
    # Inspection
    # ------------------------------------------------------------------ #
    def __len__(self) -> int:
        return len(self.placements)

    def __iter__(self) -> Iterator[Placement]:
        return iter(self.placements)

    def bbox(self, art_only: bool = False) -> tuple[int, int, int, int] | None:
        """Return (x_min, y_min, x_max, y_max) or None if empty."""
        items = [p for p in self.placements if not art_only or p.is_art]
        if not items:
            return None
        xs = [p.x for p in items]
        ys = [p.y for p in items]
        return (min(xs), min(ys), max(xs), max(ys))

    def counts_by_name(self) -> Counter:
        return Counter(p.name for p in self.placements)

    def counts_by_hash(self) -> Counter:
        return Counter(p.hash for p in self.placements)

    def layers(self) -> dict[str, list[Placement]]:
        """Group placements by decoration name."""
        out: dict[str, list[Placement]] = defaultdict(list)
        for p in self.placements:
            out[p.name].append(p)
        return dict(out)

    def find_unknown_hashes(self) -> dict[int, list[Placement]]:
        """Return placements whose hash is not in the known catalogue.

        Useful when you want to extend KNOWN_HASHES — unknown hashes
        will be flagged here without raising.
        """
        out: dict[int, list[Placement]] = defaultdict(list)
        for p in self.placements:
            if p.hash not in HASH_TO_NAME:
                out[p.hash].append(p)
        return dict(out)

    # ------------------------------------------------------------------ #
    # Mutation helpers — return self for chaining
    # ------------------------------------------------------------------ #
    def shift(self, dx: int = 0, dy: int = 0, art_only: bool = False) -> Hideout:
        for p in self.placements:
            if art_only and not p.is_art:
                continue
            p.x += dx
            p.y += dy
        return self

    def filter(self, predicate) -> Hideout:
        """Keep only placements matching ``predicate(Placement) -> bool``.

        Returns a NEW Hideout (does not mutate ``self``).
        """
        new = Hideout(
            version=self.version,
            language=self.language,
            hideout_name=self.hideout_name,
            hideout_hash=self.hideout_hash,
            placements=[p for p in self.placements if predicate(p)],
        )
        return new

    def rename_header(self, name: str, hideout_hash: int) -> Hideout:
        """Re-target this composition to another hideout map.

        WARNING: This does NOT validate that decorations exist in the
        target hideout. Use ``Hideout.find_unknown_hashes`` after loading
        a sample export of the target hideout to verify availability.
        """
        self.hideout_name = name
        self.hideout_hash = hideout_hash
        return self
