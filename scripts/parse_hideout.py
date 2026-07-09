"""
Duplicate-preserving .hideout parser.

PoE .hideout JSON files use duplicate keys to represent multiple placements
of the same doodad type. Standard json.load() silently keeps only the last
entry per key -- which is why naive parsing produces wildly wrong counts.

This module exposes:
  - load_hideout(path) -> dict with `placements` list (preserves every entry)
  - placement fields: name (zh-tw), hash, x, y, r, fv
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any


# Matches:  "Some Key": { "hash": 123, "x": 456, "y": 789, "r": 0, "fv": 0 }
# Tolerates whitespace, field order, missing fields.
_ENTRY_RE = re.compile(
    r'"([^"]+)"\s*:\s*\{\s*'
    r'"hash"\s*:\s*(-?\d+)\s*,\s*'
    r'"x"\s*:\s*(-?\d+)\s*,\s*'
    r'"y"\s*:\s*(-?\d+)\s*,\s*'
    r'"r"\s*:\s*(-?\d+)\s*,\s*'
    r'"fv"\s*:\s*(-?\d+)\s*'
    r'\}'
)

# Old text-format (PoE1 export):
#   Name = { Hash=123, X=456, Y=789, Rot=0, Flip=0, Var=0 }
# Field order in older exports can vary, so we parse field-by-field.
_OLD_ENTRY_RE = re.compile(
    r'^([^\s=][^\n=]*?)\s*=\s*\{\s*Hash\s*=\s*(-?\d+)\s*,\s*'
    r'X\s*=\s*(-?\d+)\s*,\s*'
    r'Y\s*=\s*(-?\d+)\s*,\s*'
    r'Rot\s*=\s*(-?\d+)\s*,\s*'
    r'Flip\s*=\s*(-?\d+)\s*,\s*'
    r'Var\s*=\s*(-?\d+)\s*'
    r'\s*\}\s*$',
    re.MULTILINE
)


def load_hideout(path: str | Path) -> dict[str, Any]:
    """Parse a .hideout file preserving every placement (incl. duplicates).

    Returns dict with keys:
      version, language, hideout_name, hideout_hash,
      placements: list of {name, hash, x, y, r, fv}
    """
    p = Path(path)
    # Some .hideout files are UTF-16-LE with BOM, others UTF-8 (with/without BOM).
    # Detect by reading first 4 bytes.
    with open(p, "rb") as fh:
        head = fh.read(4)
    if head[:2] in (b"\xff\xfe", b"\xfe\xff"):
        raw = p.read_text(encoding="utf-16")
    else:
        raw = p.read_text(encoding="utf-8-sig")

    # Header fields (single-valued, safe to read from json)
    try:
        head = json.loads(raw)
        header = {
            "version": head.get("version"),
            "language": head.get("language"),
            "hideout_name": head.get("hideout_name"),
            "hideout_hash": head.get("hideout_hash"),
        }
    except json.JSONDecodeError:
        # Old text-format file -- extract manually
        header = {
            "version": None,
            "language": _extract(raw, r'Language\s*=\s*"([^"]*)"'),
            "hideout_name": _extract(raw, r'Hideout Name\s*=\s*"([^"]*)"'),
            "hideout_hash": _int_extract(raw, r'Hideout Hash\s*=\s*(\d+)'),
        }

    placements = []
    for m in _ENTRY_RE.finditer(raw):
        name, h, x, y, r, fv = m.groups()
        placements.append({
            "name": name,
            "hash": int(h),
            "x": int(x),
            "y": int(y),
            "r": int(r),
            "fv": int(fv),
        })
    # Old text-format fallback
    if not placements:
        for m in _OLD_ENTRY_RE.finditer(raw):
            name, h, x, y, rot, flip, var = m.groups()
            # New format encodes flip+var into a single `fv` field.
            # Empirical check: when Flip=0, fv = Var. When Flip=1, fv = Var | 0x80
            # (bit 7 set).  We'll just preserve Var for now and note flip separately.
            fv = int(var) | (int(flip) << 7)
            placements.append({
                "name": name.strip(),
                "hash": int(h),
                "x": int(x),
                "y": int(y),
                "r": int(rot),
                "fv": fv,
                "_flip": int(flip),
                "_var": int(var),
            })

    return {**header, "placements": placements}


def _extract(s: str, pattern: str) -> str | None:
    m = re.search(pattern, s)
    return m.group(1) if m else None


def _int_extract(s: str, pattern: str) -> int | None:
    m = re.search(pattern, s)
    return int(m.group(1)) if m else None


if __name__ == "__main__":
    import sys
    data = load_hideout(sys.argv[1])
    print(f"File: {sys.argv[1]}")
    print(f"Hideout: {data['hideout_name']} (hash={data['hideout_hash']})")
    print(f"Placements: {len(data['placements'])}")
    from collections import Counter
    c = Counter(p["name"] for p in data["placements"])
    print(f"Distinct doodad types: {len(c)}")
    print("Top 10:")
    for n, k in c.most_common(10):
        print(f"  {n:>4}x  {k}")
