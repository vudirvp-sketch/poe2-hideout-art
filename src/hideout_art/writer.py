"""Emitter — serialise a Hideout back to a valid ``.hideout`` file.

The output is byte-compatible with the format PoE2 expects:

* UTF-8 (no BOM — PoE2 accepts both, but cleanest is no BOM)
* 2-space indentation
* Duplicate keys inside ``doodads`` are intentional and required:
  the game reads each entry as a separate placement.
"""

from __future__ import annotations

from pathlib import Path

from .parser import Hideout


def hideout_to_string(h: Hideout) -> str:
    """Serialise a Hideout to a string in ``.hideout`` format."""
    lines: list[str] = []
    lines.append("{")
    lines.append(f'  "version": {h.version},')
    lines.append(f'  "language": "{h.language}",')
    lines.append(f'  "hideout_name": "{h.hideout_name}",')
    lines.append(f'  "hideout_hash": {h.hideout_hash},')
    lines.append('  "doodads": {')
    for i, p in enumerate(h.placements):
        comma = "," if i < len(h.placements) - 1 else ""
        lines.append(f'    "{p.name}": {{')
        lines.append(f'      "hash": {p.hash},')
        lines.append(f'      "x": {p.x},')
        lines.append(f'      "y": {p.y},')
        lines.append(f'      "r": {p.r},')
        lines.append(f'      "fv": {p.fv}')
        lines.append(f"    }}{comma}")
    lines.append("  }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def write_hideout(h: Hideout, path: str | Path) -> Path:
    """Write a Hideout to ``path`` and return the resolved Path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(hideout_to_string(h), encoding="utf-8")
    return p


# Convenience: also expose on the Hideout class via monkey-patch.
def _to_file(self: Hideout, path: str | Path) -> Path:
    return write_hideout(self, path)


def _to_string(self: Hideout) -> str:
    return hideout_to_string(self)


Hideout.to_file = _to_file       # type: ignore[attr-defined]
Hideout.to_string = _to_string   # type: ignore[attr-defined]
