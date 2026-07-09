"""Tests for the DECORATION_FOOTPRINT_CATALOG (0.2.3).

Verifies:
  * Catalog covers every entry in ART_TYPES (no missing footprints).
  * Every catalog entry references a known art decoration.
  * Confidence levels are valid.
  * estimated_tile_footprint is consistent with min_spacing_wu.
  * Low-confidence Marble Table entry is flagged (KI-10).
  * Samples count matches what's actually in исходники/*.hideout
    (when the folder is present).
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from hideout_art.constants import (
    ART_TYPES,
    DECORATION_FOOTPRINT_CATALOG,
    DEFAULT_TILE_SIZE_WORLD_UNITS,
    FOOTPRINT_CONFIDENCE_LEVELS,
    KNOWN_HASHES,
    DecorationFootprint,
)
from hideout_art.parser import Hideout

REPO_ROOT = Path(__file__).resolve().parent.parent
ISXODNIKI = REPO_ROOT / "исходники"
HAS_ISXODNIKI = ISXODNIKI.is_dir()


# ---------------------------------------------------------------------------
# Structural integrity
# ---------------------------------------------------------------------------

def test_catalog_covers_all_art_types():
    """Every name in ART_TYPES must have a catalog entry."""
    missing = ART_TYPES - set(DECORATION_FOOTPRINT_CATALOG.keys())
    assert not missing, f"ART_TYPES missing from catalog: {sorted(missing)}"


def test_catalog_does_not_contain_non_art():
    """Every catalog entry must be in ART_TYPES (no functional objects)."""
    extra = set(DECORATION_FOOTPRINT_CATALOG.keys()) - ART_TYPES
    assert not extra, f"Non-art entries in catalog: {sorted(extra)}"


def test_catalog_entries_are_namedtuples():
    """Each entry must be a DecorationFootprint NamedTuple."""
    for name, fp in DECORATION_FOOTPRINT_CATALOG.items():
        assert isinstance(fp, DecorationFootprint), (
            f"{name}: expected DecorationFootprint, got {type(fp).__name__}"
        )


def test_confidence_levels_are_valid():
    """Every confidence value must be in FOOTPRINT_CONFIDENCE_LEVELS."""
    for name, fp in DECORATION_FOOTPRINT_CATALOG.items():
        assert fp.confidence in FOOTPRINT_CONFIDENCE_LEVELS, (
            f"{name}: invalid confidence '{fp.confidence}'"
        )


# ---------------------------------------------------------------------------
# Confidence ↔ samples consistency
# ---------------------------------------------------------------------------

def _expected_confidence(samples: int) -> str:
    if samples >= 5:
        return "high"
    if samples >= 3:
        return "medium"
    if samples == 2:
        return "low"
    if samples == 1:
        return "single"
    return "none"


@pytest.mark.parametrize("name", sorted(DECORATION_FOOTPRINT_CATALOG.keys()))
def test_confidence_matches_samples(name: str):
    """confidence must match the samples count per the documented thresholds."""
    fp = DECORATION_FOOTPRINT_CATALOG[name]
    expected = _expected_confidence(fp.samples)
    assert fp.confidence == expected, (
        f"{name}: samples={fp.samples} should give confidence='{expected}', "
        f"got '{fp.confidence}'"
    )


# ---------------------------------------------------------------------------
# Spacing ↔ footprint consistency
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(DECORATION_FOOTPRINT_CATALOG.keys()))
def test_footprint_consistent_with_min_spacing(name: str):
    """When min_spacing_wu is not None, estimated_tile_footprint must equal
    ceil(min_spacing_wu / DEFAULT_TILE_SIZE_WORLD_UNITS * 2) / 2.
    """
    fp = DECORATION_FOOTPRINT_CATALOG[name]
    if fp.min_spacing_wu is None:
        assert fp.estimated_tile_footprint is None, (
            f"{name}: min_spacing_wu is None but tile footprint is "
            f"{fp.estimated_tile_footprint}"
        )
        assert fp.median_spacing_wu is None, (
            f"{name}: min_spacing_wu is None but median_spacing_wu is "
            f"{fp.median_spacing_wu}"
        )
        return

    # min_spacing_wu is set — footprint must be set too.
    assert fp.estimated_tile_footprint is not None, (
        f"{name}: min_spacing_wu={fp.min_spacing_wu} but tile footprint is None"
    )
    expected = math.ceil(fp.min_spacing_wu / DEFAULT_TILE_SIZE_WORLD_UNITS * 2) / 2
    assert fp.estimated_tile_footprint == expected, (
        f"{name}: min_spacing={fp.min_spacing_wu}, "
        f"expected tile footprint {expected}, got {fp.estimated_tile_footprint}"
    )


@pytest.mark.parametrize("name", sorted(DECORATION_FOOTPRINT_CATALOG.keys()))
def test_min_le_median_when_both_set(name: str):
    """When both min and median are set, min must be <= median."""
    fp = DECORATION_FOOTPRINT_CATALOG[name]
    if fp.min_spacing_wu is None or fp.median_spacing_wu is None:
        return
    assert fp.min_spacing_wu <= fp.median_spacing_wu, (
        f"{name}: min={fp.min_spacing_wu} > median={fp.median_spacing_wu}"
    )


# ---------------------------------------------------------------------------
# Specific known values (regression protection)
# ---------------------------------------------------------------------------

def test_beech_tree_is_low_confidence_one_tile():
    """Beech Tree has only 2 placements — must be low confidence, ~1 tile."""
    fp = DECORATION_FOOTPRINT_CATALOG["Beech Tree"]
    assert fp.samples == 2
    assert fp.confidence == "low"
    assert fp.min_spacing_wu == 22.0
    assert fp.estimated_tile_footprint == 1.0


def test_cordilina_has_high_sample_count():
    """Cordilina was placed 11 times around the Canal Hideout perimeter."""
    fp = DECORATION_FOOTPRINT_CATALOG["Cordilina"]
    assert fp.samples == 11
    assert fp.confidence == "high"


def test_marble_table_low_confidence_two_tiles_ki10():
    """Marble Table has only 2 placements — flagged low-confidence (KI-10).

    The 45.6 wu minimum observed spacing is likely a coincidence of where
    the user placed the two tables, NOT evidence that Marble Table is
    actually 2 tiles wide. See KI-10 in STATUS.md.
    """
    fp = DECORATION_FOOTPRINT_CATALOG["Marble Table"]
    assert fp.samples == 2
    assert fp.confidence == "low"
    assert fp.estimated_tile_footprint == 2.0


def test_single_sample_decorations_have_no_footprint():
    """Decorations with only 1 placement cannot be measured."""
    for _name, fp in DECORATION_FOOTPRINT_CATALOG.items():
        if fp.samples == 1:
            assert fp.min_spacing_wu is None
            assert fp.estimated_tile_footprint is None
            assert fp.confidence == "single"


def test_zero_sample_decorations_are_marked_none():
    """Decorations not present in исходники/ have samples=0, confidence=none."""
    for _name, fp in DECORATION_FOOTPRINT_CATALOG.items():
        if fp.samples == 0:
            assert fp.confidence == "none"
            assert fp.min_spacing_wu is None
            assert fp.estimated_tile_footprint is None


def test_atziri_statue_excluded_from_catalog():
    """Atziri Statue is functional (huge, not for art) — must NOT be in catalog.

    Per user instruction, large functional objects are excluded from the
    footprint catalog. Only ART_TYPES entries belong here.
    """
    assert "Atziri Statue" not in DECORATION_FOOTPRINT_CATALOG
    assert "Atziri Statue" not in ART_TYPES
    assert "Atziri Statue" in KNOWN_HASHES  # still a known hash


# ---------------------------------------------------------------------------
# Sanity: at least some entries have measurable footprints
# ---------------------------------------------------------------------------

def test_catalog_has_measurable_entries():
    """At least 10 decorations must have a non-None estimated_tile_footprint."""
    measurable = [
        name for name, fp in DECORATION_FOOTPRINT_CATALOG.items()
        if fp.estimated_tile_footprint is not None
    ]
    assert len(measurable) >= 10, (
        f"Only {len(measurable)} measurable entries: {sorted(measurable)}"
    )


def test_catalog_has_high_confidence_entries():
    """At least 8 decorations must have 'high' confidence (>=5 samples)."""
    high = [
        name for name, fp in DECORATION_FOOTPRINT_CATALOG.items()
        if fp.confidence == "high"
    ]
    assert len(high) >= 8, (
        f"Only {len(high)} high-confidence entries: {sorted(high)}"
    )


# ---------------------------------------------------------------------------
# Cross-check against real исходники/*.hideout (when present)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not HAS_ISXODNIKI, reason="no исходники/ folder present")
def test_sample_counts_match_real_exports():
    """The `samples` field in the catalog must equal the number of placements
    of that hash across all исходники/*.hideout files.

    This is the ground-truth check: if we add/remove placements in source
    files, the catalog must be regenerated (re-run scripts/measure_decorations.py).
    """
    # Collect placements per hash across all source files.
    counts_by_hash: dict[int, int] = {}
    for p in sorted(ISXODNIKI.glob("*.hideout")):
        h = Hideout.from_file(p)
        for pl in h.placements:
            counts_by_hash[pl.hash] = counts_by_hash.get(pl.hash, 0) + 1

    # For every catalog entry, samples must match the observed count.
    for name, fp in DECORATION_FOOTPRINT_CATALOG.items():
        hv = KNOWN_HASHES[name]
        observed = counts_by_hash.get(hv, 0)
        assert fp.samples == observed, (
            f"{name} (hash {hv}): catalog says samples={fp.samples}, "
            f"but исходники/ contains {observed} placements. "
            f"Re-run scripts/measure_decorations.py and update the catalog."
        )
