"""Tests for the writer — byte-stability and duplicate-key preservation."""

from pathlib import Path

from hideout_art import Hideout
from hideout_art.writer import hideout_to_string, write_hideout

DATA = Path(__file__).parent / "data" / "sample.hideout"


def test_round_trip_preserves_placements():
    h1 = Hideout.from_file(DATA)
    s = hideout_to_string(h1)
    h2 = Hideout.from_string(s)
    assert len(h1) == len(h2)
    assert [p.as_dict() for p in h1] == [p.as_dict() for p in h2]


def test_output_has_duplicate_keys():
    """The writer MUST emit duplicate keys — this is the file format."""
    h = Hideout.from_file(DATA)
    s = hideout_to_string(h)
    # 'Long Grass' must appear twice as a key
    assert s.count('"Long Grass": {') == 2


def test_output_starts_and_ends_correctly():
    h = Hideout.from_file(DATA)
    s = hideout_to_string(h)
    assert s.startswith("{\n")
    assert s.endswith("}\n")
    assert '"version": 1' in s
    assert '"hideout_name": "Test Hideout"' in s
    assert '"doodads": {' in s


def test_no_bom_in_output():
    h = Hideout.from_file(DATA)
    s = hideout_to_string(h)
    # The writer never emits a BOM — cleanest for version control.
    assert not s.startswith("\ufeff")


def test_write_hideout_creates_file(tmp_path: Path):
    h = Hideout.from_file(DATA)
    out = tmp_path / "out.hideout"
    write_hideout(h, out)
    assert out.exists()
    # And we can read it back
    h2 = Hideout.from_file(out)
    assert len(h2) == len(h)


def test_write_hideout_creates_parent_dirs(tmp_path: Path):
    h = Hideout.from_file(DATA)
    out = tmp_path / "nested" / "deeper" / "out.hideout"
    write_hideout(h, out)
    assert out.exists()


def test_to_file_method_on_hideout(tmp_path: Path):
    h = Hideout.from_file(DATA)
    out = tmp_path / "via_method.hideout"
    h.to_file(out)
    assert out.exists()
    h2 = Hideout.from_file(out)
    assert [p.as_dict() for p in h] == [p.as_dict() for p in h2]


def test_header_round_trips():
    h = Hideout.from_file(DATA)
    s = hideout_to_string(h)
    h2 = Hideout.from_string(s)
    assert h2.version == h.version
    assert h2.language == h.language
    assert h2.hideout_name == h.hideout_name
    assert h2.hideout_hash == h.hideout_hash
