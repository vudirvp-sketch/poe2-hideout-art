"""Tests for the new (0.2.1) hashes and palette entries."""

from __future__ import annotations

from pathlib import Path

import pytest

from hideout_art.constants import (
    ART_TYPES,
    DEFAULT_TILE_SIZE_WORLD_UNITS,
    HASH_TO_NAME,
    KNOWN_HASHES,
)
from hideout_art.palette import Palette
from hideout_art.parser import Hideout, Placement

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


# ---------------------------------------------------------------------------
# KNOWN_HASHES — new entries from user-provided exports
# ---------------------------------------------------------------------------

NEW_ENTRIES = {
    "Maraket Rubble":     3012657298,
    "Maraket Treasures":  1078696835,
    "Maraket Samovar":     57228444,
    "Maraket Ornament":   2125171205,
    "Coastal Pebble":     2365064644,
}


@pytest.mark.parametrize("name,hv", sorted(NEW_ENTRIES.items()))
def test_new_hash_registered(name: str, hv: int):
    assert KNOWN_HASHES.get(name) == hv
    assert HASH_TO_NAME.get(hv) == name


@pytest.mark.parametrize("name", sorted(NEW_ENTRIES.keys()))
def test_new_hashes_are_art(name: str):
    """All 5 new decorations are decorative — must be in ART_TYPES."""
    assert name in ART_TYPES


def test_no_collisions_with_existing_hashes():
    """Each new hash must be unique across the whole catalogue."""
    all_hashes = list(KNOWN_HASHES.values())
    for hv in NEW_ENTRIES.values():
        assert all_hashes.count(hv) == 1


# ---------------------------------------------------------------------------
# Parsing the user-provided exports (uploaded as uploads/)
# ---------------------------------------------------------------------------

UPLOAD_DIR = Path("/home/z/my-project/upload")
HAS_UPLOADS = UPLOAD_DIR.is_dir()


@pytest.mark.skipif(not HAS_UPLOADS, reason="no upload/ directory present")
def test_parse_user_export_ukrasheniya():
    """First user export: 36 placements, 4 unknown hashes (now known)."""
    h = Hideout.from_file(UPLOAD_DIR / "укрошения, хорошие подложки будто и обломки.hideout")
    assert len(h) == 36
    unknown = h.find_unknown_hashes()
    # After adding the 5 new hashes, none should be unknown anymore.
    assert not unknown, f"unexpected unknown hashes: {list(unknown.keys())}"


@pytest.mark.skipif(not HAS_UPLOADS, reason="no upload/ directory present")
def test_parse_user_export_galka():
    """Second user export: 27 placements, 1 unknown hash (now known)."""
    h = Hideout.from_file(UPLOAD_DIR / "галька.hideout")
    assert len(h) == 27
    unknown = h.find_unknown_hashes()
    assert not unknown, f"unexpected unknown hashes: {list(unknown.keys())}"


@pytest.mark.skipif(not HAS_UPLOADS, reason="no upload/ directory present")
def test_user_export_art_classification():
    """Placements with the new hashes must be classified as art.

    The .hideout file stores Russian names ("Береговая галька"), but
    ``is_art`` resolves via hash to the canonical English name
    ("Coastal Pebble") which IS in ART_TYPES — so is_art must be True.
    """
    h = Hideout.from_file(UPLOAD_DIR / "галька.hideout")
    pebble_placements = [p for p in h if p.hash == KNOWN_HASHES["Coastal Pebble"]]
    assert len(pebble_placements) == 9
    # Original Russian name preserved verbatim by the parser
    assert all(p.name == "Береговая галька" for p in pebble_placements)
    # But is_art correctly resolves via hash → Coastal Pebble ∈ ART_TYPES
    assert all(p.is_art for p in pebble_placements)


# ---------------------------------------------------------------------------
# palette_warm.json — new working palette
# ---------------------------------------------------------------------------

def test_palette_warm_loads():
    """palette_warm.json is a fully working palette — must load cleanly."""
    p = Palette.from_json_file(EXAMPLES / "palette_warm.json")
    assert len(p.entries) == 9
    # Every entry's decoration must exist in KNOWN_HASHES (the Palette
    # constructor itself enforces this, so just reaching this assertion
    # means the palette is valid).
    for e in p.entries:
        assert e.decoration in KNOWN_HASHES


def test_palette_warm_uses_new_decorations():
    """palette_warm.json must use all 5 new warm-tone decorations."""
    p = Palette.from_json_file(EXAMPLES / "palette_warm.json")
    names = {e.decoration for e in p.entries}
    assert "Maraket Rubble" in names
    assert "Maraket Treasures" in names
    assert "Maraket Samovar" in names
    assert "Maraket Ornament" in names
    assert "Coastal Pebble" in names


def test_palette_2b_still_has_todos():
    """palette_2b.json is still a template — TODOs must remain (no white/black/gray yet)."""
    import json
    data = json.loads((EXAMPLES / "palette_2b.json").read_text(encoding="utf-8"))
    names = [e["decoration"] for e in data["entries"]]
    todo_count = sum(1 for n in names if n.startswith("TODO_"))
    # We expect 6 remaining TODOs: white, black, gray, silver, skin, red.
    assert todo_count == 6


# ---------------------------------------------------------------------------
# DEFAULT_TILE_SIZE_WORLD_UNITS — calibration constant
# ---------------------------------------------------------------------------

def test_default_tile_size_is_reasonable():
    """Tile size should be in the 15-30 range based on observed deltas."""
    assert 15 <= DEFAULT_TILE_SIZE_WORLD_UNITS <= 30
    assert DEFAULT_TILE_SIZE_WORLD_UNITS == 23


# ---------------------------------------------------------------------------
# KI-9 fix: is_art resolves via hash (not name) so Russian-named placements
# are still classified as art.
# ---------------------------------------------------------------------------

def test_is_art_resolves_via_hash_not_name():
    """A placement with a Russian name but a known hash must be is_art=True
    when the canonical English name is in ART_TYPES.
    """
    p = Placement(
        name="Береговая галька",  # Russian name
        hash=KNOWN_HASHES["Coastal Pebble"],
        x=0, y=0, r=0, fv=0,
    )
    assert p.is_art is True


def test_is_art_false_for_unknown_hash():
    """Unknown hash + unknown name → not art (preserves legacy behaviour)."""
    p = Placement(
        name="Some Unknown Decoration",
        hash=9999999999,
        x=0, y=0, r=0, fv=0,
    )
    assert p.is_art is False


def test_is_art_false_for_known_functional_object():
    """Stash is a known hash but NOT in ART_TYPES → is_art=False."""
    p = Placement(
        name="Tайник",  # Russian for "Stash"
        hash=KNOWN_HASHES["Stash"],
        x=0, y=0, r=0, fv=0,
    )
    assert p.is_art is False
