"""Tests for geometric transforms."""

from pathlib import Path

import pytest

from hideout_art import Hideout
from hideout_art.transforms import (
    recombine,
)

DATA = Path(__file__).parent / "data" / "sample.hideout"


def test_shift_moves_all_placements():
    h = Hideout.from_file(DATA)
    original = [p.as_dict() for p in h]
    h.shift(dx=10, dy=-5)
    for p, o in zip(h.placements, original, strict=True):
        assert p.x == o["x"] + 10
        assert p.y == o["y"] - 5


def test_shift_art_only_leaves_functional_alone():
    h = Hideout.from_file(DATA)
    h.shift(dx=100, dy=100, art_only=True)
    stash = next(p for p in h if p.name == "Stash")
    assert stash.x == 100  # unchanged
    assert stash.y == 100
    grass = [p for p in h if p.name == "Long Grass"]
    assert all(p.x >= 200 for p in grass)


def test_shift_returns_self_for_chaining():
    h = Hideout.from_file(DATA)
    assert h.shift(dx=1) is h


def test_rotate_around_centroid():
    h = Hideout.from_file(DATA)
    # Snapshot placements
    before = [(p.x, p.y, p.r) for p in h]
    h.rotate(180)
    # 180° rotation: (x, y) -> (-x, -y) relative to centroid
    # Each placement's r should be incremented by 32768 (mod 65536)
    for p, (_, _, br) in zip(h.placements, before, strict=True):
        assert (p.r - br) % 65536 == 32768


def test_rotate_360_is_identity():
    h = Hideout.from_file(DATA)
    before = [(p.x, p.y, p.r) for p in h]
    h.rotate(360)
    for p, (bx, by, br) in zip(h.placements, before, strict=True):
        # 360° rotation adds 65536 to r, which mod 65536 == 0
        assert p.r == br
        # Coordinates may differ by 1 due to floating point - allow small drift
        assert abs(p.x - bx) <= 1
        assert abs(p.y - by) <= 1


def test_rotate_normalises_r_into_range():
    h = Hideout.from_file(DATA)
    h.rotate(720)  # two full turns
    for p in h.placements:
        assert 0 <= p.r < 65536


def test_mirror_x_flips_x_and_toggles_flip_bit():
    h = Hideout.from_file(DATA)
    before = [(p.x, p.fv) for p in h]
    h.mirror_x(axis=100)
    for p, (bx, bfv) in zip(h.placements, before, strict=True):
        # x -> 2*axis - x
        assert p.x == 2 * 100 - bx
        # flip bit toggled
        assert (p.fv & 0x80) != (bfv & 0x80)


def test_mirror_y_flips_y():
    h = Hideout.from_file(DATA)
    before = [p.y for p in h]
    h.mirror_y(axis=100)
    for p, by in zip(h.placements, before, strict=True):
        assert p.y == 2 * 100 - by


def test_mirror_on_empty_hideout_does_not_crash():
    h = Hideout(version=1, language="English", hideout_name="empty", hideout_hash=0, placements=[])
    h.mirror_x()
    h.mirror_y()
    assert len(h) == 0


def test_recombine_concatenates_placements():
    h1 = Hideout.from_file(DATA)
    h2 = Hideout.from_file(DATA)
    combined = recombine(h1, h2, offsets=[(0, 0), (1000, 1000)])
    assert len(combined) == len(h1) + len(h2)
    # First half unchanged
    first_half = combined.placements[: len(h1)]
    for a, b in zip(first_half, h1.placements, strict=True):
        assert a.as_dict() == b.as_dict()
    # Second half shifted
    second_half = combined.placements[len(h1):]
    for a, b in zip(second_half, h2.placements, strict=True):
        assert a.x == b.x + 1000
        assert a.y == b.y + 1000


def test_recombine_default_offsets():
    h1 = Hideout.from_file(DATA)
    h2 = Hideout.from_file(DATA)
    combined = recombine(h1, h2)
    assert len(combined) == len(h1) + len(h2)


def test_recombine_requires_matching_offset_count():
    h1 = Hideout.from_file(DATA)
    h2 = Hideout.from_file(DATA)
    with pytest.raises(ValueError):
        recombine(h1, h2, offsets=[(0, 0)])


def test_recombine_empty_raises():
    with pytest.raises(ValueError):
        recombine()
