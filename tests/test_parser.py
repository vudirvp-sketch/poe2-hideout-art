"""Tests for the tolerant parser."""

from pathlib import Path

import pytest

from hideout_art import Hideout
from hideout_art.parser import _ENTRY_RE

DATA = Path(__file__).parent / "data" / "sample.hideout"


def test_parse_basic_fields():
    h = Hideout.from_file(DATA)
    assert h.version == 1
    assert h.language == "English"
    assert h.hideout_name == "Test Hideout"
    assert h.hideout_hash == 99999


def test_parse_preserves_duplicate_keys():
    """The single most important property of the parser."""
    h = Hideout.from_file(DATA)
    # sample.hideout has 4 placements total: 1 Stash + 2 Long Grass + 1 Unknown
    assert len(h) == 4
    grass = [p for p in h if p.name == "Long Grass"]
    assert len(grass) == 2
    assert grass[0].x == 110
    assert grass[1].x == 112


def test_placement_decoders():
    h = Hideout.from_file(DATA)
    grass_with_rotation = next(p for p in h if p.name == "Long Grass" and p.r == 10922)
    # 10922 / 65536 * 360 ≈ 60°
    assert grass_with_rotation.rotation_degrees == pytest.approx(60.0, abs=0.01)
    assert grass_with_rotation.flip_x is False
    assert grass_with_rotation.variant == 7

    grass_flipped = next(p for p in h if p.name == "Long Grass" and p.fv == 135)
    # 135 = 0x80 | 7
    assert grass_flipped.flip_x is True
    assert grass_flipped.variant == 7


def test_is_art_classification():
    h = Hideout.from_file(DATA)
    art = [p for p in h if p.is_art]
    # Only Long Grass placements are in ART_TYPES
    assert len(art) == 2
    assert all(p.name == "Long Grass" for p in art)


def test_unknown_hash_preserved():
    h = Hideout.from_file(DATA)
    unknown = h.find_unknown_hashes()
    assert 9999999999 in unknown
    assert len(unknown[9999999999]) == 1
    assert unknown[9999999999][0].name == "Unknown Decoration"


def test_bbox():
    h = Hideout.from_file(DATA)
    bb = h.bbox()
    assert bb == (100, 100, 150, 150)
    bb_art = h.bbox(art_only=True)
    assert bb_art == (110, 110, 112, 112)


def test_counts_by_name():
    h = Hideout.from_file(DATA)
    counts = h.counts_by_name()
    assert counts["Long Grass"] == 2
    assert counts["Stash"] == 1
    assert counts["Unknown Decoration"] == 1


def test_layers_grouping():
    h = Hideout.from_file(DATA)
    layers = h.layers()
    assert set(layers.keys()) == {"Stash", "Long Grass", "Unknown Decoration"}
    assert len(layers["Long Grass"]) == 2


def test_from_string_matches_from_file():
    text = DATA.read_text(encoding="utf-8-sig")
    h1 = Hideout.from_file(DATA)
    h2 = Hideout.from_string(text)
    assert len(h1) == len(h2)
    assert [p.as_dict() for p in h1] == [p.as_dict() for p in h2]


def test_entry_regex_does_not_match_garbage():
    assert _ENTRY_RE.search('not even close') is None
    # Missing fields
    assert _ENTRY_RE.search('{"name": {"x": 1}}') is None


def test_filter_returns_new_instance():
    h = Hideout.from_file(DATA)
    h2 = h.filter(lambda p: p.is_art)
    assert h2 is not h
    assert len(h2) == 2
    # Original is unmodified
    assert len(h) == 4


def test_shift_art_only():
    h = Hideout.from_file(DATA)
    h.shift(dx=100, dy=50, art_only=True)
    art = [p for p in h if p.is_art]
    func = [p for p in h if not p.is_art]
    # Art shifted
    assert all(p.x >= 200 for p in art)
    # Functional untouched
    assert all(p.x < 200 for p in func)
