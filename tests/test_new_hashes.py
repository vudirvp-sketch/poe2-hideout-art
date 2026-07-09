"""Tests for hashes, palette entries, and bounds discovered across iterations.

Covers:
  * 0.2.1 — 5 warm-tone Maraket/Coastal Pebble hashes + tile_size + KI-9 fix.
  * 0.2.2 — 18 new hashes from "исходники/" folder + CANAL_HIDEOUT_BOUNDS +
    ``--bounds canal`` CLI shortcut.
  * 0.2.4 — VLM-measured RGB for Marble-серия + Cave Fossil/Coral/Brazier;
    palette_2b.json fills 3 of 6 TODOs (white/silver/gray).
  * 0.2.5 — Seaweed hash + Small Coastal Stone (black role) + Maraket Rubble
    (red role); palette_2b.json fills 5 of 6 TODOs (only skin remains).
    New KI-11 documents VLM-noise on Sand Tussock/Maraket-серия RGB.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hideout_art.constants import (
    ART_TYPES,
    CANAL_HIDEOUT_BOUNDS,
    CANAL_HIDEOUT_HASH,
    DEFAULT_TILE_SIZE_WORLD_UNITS,
    HASH_TO_NAME,
    KNOWN_HASHES,
    NAMED_BOUNDS,
)
from hideout_art.palette import Palette
from hideout_art.parser import Hideout, Placement

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
ISXODNIKI = Path(__file__).resolve().parent.parent / "исходники"


# ---------------------------------------------------------------------------
# 0.2.1 — warm-tone Maraket/Coastal Pebble hashes
# ---------------------------------------------------------------------------

WARM_ENTRIES = {
    "Maraket Rubble":     3012657298,
    "Maraket Treasures":  1078696835,
    "Maraket Samovar":     57228444,
    "Maraket Ornament":   2125171205,
    "Coastal Pebble":     2365064644,
}


@pytest.mark.parametrize("name,hv", sorted(WARM_ENTRIES.items()))
def test_warm_hash_registered(name: str, hv: int):
    assert KNOWN_HASHES.get(name) == hv
    assert HASH_TO_NAME.get(hv) == name


@pytest.mark.parametrize("name", sorted(WARM_ENTRIES.keys()))
def test_warm_hashes_are_art(name: str):
    assert name in ART_TYPES


# ---------------------------------------------------------------------------
# 0.2.2 — 18 new Canal Hideout hashes from "исходники/" folder
# ---------------------------------------------------------------------------

NEW_022_ENTRIES = {
    # Boundary / marker
    "Cordilina":              1082688452,
    "Petrified Cave Figure":  2014424642,
    # Coastal stones
    "Coastal Bush":           2984478824,
    "Small Coastal Stone":    1122244925,
    "Medium Coastal Stone":    369950199,
    # Plants / foliage
    "Slender Seedling":       532751457,
    "Log":                    2780985165,
    "Beech Tree":             2796444611,
    "Pile of Leaves":         4294658310,
    # Cave / mountain
    "Cave Fossil":            2206403756,
    "Cave Coral":             2359120247,
    "Summit Brazier":         2623109233,
    # Marble furniture
    "Marble Bench":            534959854,
    "Marble Table":           4056218057,
    "Marble Walls":           1380152311,
    "Marble Fountain":         525963527,
    # Camp props
    "Camp Crate":             2156404357,
    "Camp Gear":               412387213,
}

# Expected source .hideout file in исходники/ for each new hash.
# (decoration_name -> filename substring). Used by the parsing tests below.
NEW_022_SOURCES = {
    "Cordilina":              "Кордилой обозначил",
    "Petrified Cave Figure":  "Кордилой обозначил",
    "Coastal Bush":           "камни и кустарники",
    "Small Coastal Stone":    "камни и кустарники",
    "Medium Coastal Stone":   "еще камни и растения",
    "Slender Seedling":       "еще камни и растения",
    "Log":                    "всякое",
    "Beech Tree":             "всякое",
    "Pile of Leaves":         "всякое",
    "Camp Crate":             "всякое",
    "Camp Gear":              "всякое",
    "Cave Fossil":            "еще элементы",
    "Cave Coral":             "еще элементы",
    "Summit Brazier":         "еще элементы",
    "Marble Bench":           "еще элементы",
    "Marble Table":           "еще элементы",
    "Marble Walls":           "еще элементы",
    "Marble Fountain":        "еще элементы",
}


@pytest.mark.parametrize("name,hv", sorted(NEW_022_ENTRIES.items()))
def test_new_022_hash_registered(name: str, hv: int):
    """Each new 0.2.2 hash must be in KNOWN_HASHES and reversible."""
    assert KNOWN_HASHES.get(name) == hv
    assert HASH_TO_NAME.get(hv) == name


@pytest.mark.parametrize("name", sorted(NEW_022_ENTRIES.keys()))
def test_new_022_hashes_are_art(name: str):
    """All 18 new decorations are decorative — must be in ART_TYPES."""
    assert name in ART_TYPES


def test_new_022_hashes_no_collisions_with_warm():
    """0.2.2 hashes must not collide with 0.2.1 warm hashes or original Canal hashes."""
    all_hashes = list(KNOWN_HASHES.values())
    for hv in NEW_022_ENTRIES.values():
        assert all_hashes.count(hv) == 1, f"hash {hv} appears more than once"


def test_total_known_hash_count():
    """Sanity check: catalogue grew from 28 (0.2.1) to 46 (0.2.2) to 47 (0.2.5)."""
    assert len(KNOWN_HASHES) == 47


# ---------------------------------------------------------------------------
# Parsing the "исходники/" .hideout files
# ---------------------------------------------------------------------------

HAS_ISXODNIKI = ISXODNIKI.is_dir()


def _find_isxodnik(substr: str) -> Path | None:
    """Find a file in исходники/ whose name contains the substring."""
    if not HAS_ISXODNIKI:
        return None
    matches = list(ISXODNIKI.glob("*.hideout"))
    for p in matches:
        if substr in p.name:
            return p
    return None


@pytest.mark.skipif(not HAS_ISXODNIKI, reason="no исходники/ folder present")
@pytest.mark.parametrize("name", sorted(NEW_022_ENTRIES.keys()))
def test_new_022_hash_present_in_source_export(name: str):
    """Each new 0.2.2 hash must actually appear in its claimed source .hideout file."""
    hv = NEW_022_ENTRIES[name]
    src_substr = NEW_022_SOURCES[name]
    p = _find_isxodnik(src_substr)
    assert p is not None, f"source file with substring '{src_substr}' not found"
    h = Hideout.from_file(p)
    hashes_seen = {pl.hash for pl in h.placements}
    assert hv in hashes_seen, (
        f"hash {hv} ({name}) not found in {p.name}; "
        f"hashes present: {sorted(hashes_seen)}"
    )


@pytest.mark.skipif(not HAS_ISXODNIKI, reason="no исходники/ folder present")
def test_parse_isxodnik_boundary_file_no_unknowns():
    """The boundary-outline file must parse cleanly with NO unknown hashes.

    This file places 11 Cordilina + 1 Petrified Cave Figure around the
    Canal Hideout playable perimeter. After 0.2.2, both hashes are known,
    so ``find_unknown_hashes()`` must return an empty dict.
    """
    p = _find_isxodnik("Кордилой обозначил")
    assert p is not None
    h = Hideout.from_file(p)
    unknown = h.find_unknown_hashes()
    assert not unknown, f"unexpected unknown hashes: {list(unknown.keys())}"
    # Sanity: 11 Cordilinas + 1 Petrified Cave Figure + 18 base items (functional + NPCs)
    cordilina = [pl for pl in h if pl.hash == KNOWN_HASHES["Cordilina"]]
    petrified = [pl for pl in h if pl.hash == KNOWN_HASHES["Petrified Cave Figure"]]
    assert len(cordilina) == 11
    assert len(petrified) == 1


@pytest.mark.skipif(not HAS_ISXODNIKI, reason="no исходники/ folder present")
@pytest.mark.parametrize("substr", [
    "камни и кустарники",
    "еще камни и растения",
    "еще элементы",
    "всякое",
    "Кордилой обозначил",
    "водоросли и летающий песок",
])
def test_parse_isxodnik_file_no_unknowns(substr: str):
    """Every исходники .hideout must parse with no unknown hashes (post-0.2.5).

    The 'водоросли и летающий песок' file was added in 0.2.5 alongside
    the Seaweed hash registration — without Seaweed in KNOWN_HASHES this
    test would fail with one unknown hash.
    """
    p = _find_isxodnik(substr)
    assert p is not None
    h = Hideout.from_file(p)
    unknown = h.find_unknown_hashes()
    assert not unknown, (
        f"{p.name}: unexpected unknown hashes: {list(unknown.keys())}"
    )


@pytest.mark.skipif(not HAS_ISXODNIKI, reason="no исходники/ folder present")
def test_isxodnik_files_use_canal_hideout_hash():
    """All исходники .hideout files target Canal Hideout (hash 60415)."""
    for substr in [
        "камни и кустарники",
        "еще камни и растения",
        "еще элементы",
        "всякое",
        "Кордилой обозначил",
        "водоросли и летающий песок",
    ]:
        p = _find_isxodnik(substr)
        assert p is not None
        h = Hideout.from_file(p)
        assert h.hideout_hash == CANAL_HIDEOUT_HASH, (
            f"{p.name}: hideout_hash={h.hideout_hash}, expected {CANAL_HIDEOUT_HASH}"
        )


# ---------------------------------------------------------------------------
# Cross-validation: Russian in-game names resolve to canonical English via hash
# ---------------------------------------------------------------------------

# Russian names observed in исходники .hideout files, mapped to the canonical
# English name they SHOULD resolve to via HASH_TO_NAME. This is the KI-9
# guarantee: language-independent art classification.
RUSSIAN_NAME_TO_CANONICAL = {
    "Высокая трава":      "Long Grass",       # hash 2219637749
    "Песчаный кустарник": "Sand Tussock",     # hash 146816198
    "Береговая галька":   "Coastal Pebble",   # hash 2365064644 (from earlier export)
    "Летающий песок":     "Falling Sand",     # hash 3853073345 — confirmed in 0.2.5 водоросли файл
    "Морская водоросль":  "Seaweed",          # hash 1015947674 — NEW in 0.2.5
}


@pytest.mark.skipif(not HAS_ISXODNIKI, reason="no исходники/ folder present")
@pytest.mark.parametrize("ru_name,en_name", sorted(RUSSIAN_NAME_TO_CANONICAL.items()))
def test_russian_name_resolves_to_english_via_hash(ru_name: str, en_name: str):
    """A Russian-named placement must resolve to its canonical English name
    via hash lookup. This is the core KI-9 invariant.
    """
    # Find a placement with this Russian name in any исходники file
    found = False
    for substr in ["всякое", "камни и кустарники", "еще камни и растения",
                   "еще элементы", "Кордилой обозначил",
                   "водоросли и летающий песок"]:
        p = _find_isxodnik(substr)
        if p is None:
            continue
        h = Hideout.from_file(p)
        for pl in h.placements:
            if pl.name == ru_name:
                canonical = HASH_TO_NAME.get(pl.hash)
                assert canonical == en_name, (
                    f"Russian '{ru_name}' has hash {pl.hash} which resolves "
                    f"to '{canonical}', expected '{en_name}'"
                )
                found = True
                break
        if found:
            break
    if not found:
        pytest.skip(f"Russian name '{ru_name}' not present in any исходники file")


# ---------------------------------------------------------------------------
# CANAL_HIDEOUT_BOUNDS — geometry from the user's boundary outline
# ---------------------------------------------------------------------------

def test_canal_hideout_bounds_is_4_tuple():
    """CANAL_HIDEOUT_BOUNDS must be a 4-tuple of ints."""
    assert isinstance(CANAL_HIDEOUT_BOUNDS, tuple)
    assert len(CANAL_HIDEOUT_BOUNDS) == 4
    for v in CANAL_HIDEOUT_BOUNDS:
        assert isinstance(v, int)


def test_canal_hideout_bounds_is_well_formed():
    """x_min < x_max, y_min < y_max; canvas is at least 50 wu wide/tall."""
    x_min, y_min, x_max, y_max = CANAL_HIDEOUT_BOUNDS
    assert x_min < x_max
    assert y_min < y_max
    assert (x_max - x_min) >= 50
    assert (y_max - y_min) >= 50


def test_canal_hideout_bounds_wraps_user_outline():
    """CANAL_HIDEOUT_BOUNDS must contain all 11 Cordilina placements from
    the user's boundary outline file (the source of the calibration).
    """
    if not HAS_ISXODNIKI:
        pytest.skip("no исходники/ folder present")
    p = _find_isxodnik("Кордилой обозначил")
    assert p is not None
    h = Hideout.from_file(p)
    cordilina = [pl for pl in h if pl.hash == KNOWN_HASHES["Cordilina"]]
    assert len(cordilina) == 11
    x_min, y_min, x_max, y_max = CANAL_HIDEOUT_BOUNDS
    for pl in cordilina:
        assert x_min <= pl.x <= x_max, f"x={pl.x} outside [{x_min},{x_max}]"
        assert y_min <= pl.y <= y_max, f"y={pl.y} outside [{y_min},{y_max}]"


def test_named_bounds_registry_contains_canal():
    """NAMED_BOUNDS must include 'canal' → CANAL_HIDEOUT_BOUNDS."""
    assert "canal" in NAMED_BOUNDS
    assert NAMED_BOUNDS["canal"] == CANAL_HIDEOUT_BOUNDS


def test_named_bounds_lookup_is_case_insensitive_via_cli_resolver():
    """The CLI resolver (mirrored here) must accept 'canal' / 'CANAL' / 'Canal'."""
    # We test the resolver function directly by importing it from cli.
    from hideout_art.cli import _resolve_bounds
    assert _resolve_bounds("canal") == CANAL_HIDEOUT_BOUNDS
    assert _resolve_bounds("CANAL") == CANAL_HIDEOUT_BOUNDS
    assert _resolve_bounds("Canal") == CANAL_HIDEOUT_BOUNDS


def test_named_bounds_resolver_rejects_unknown_name():
    """Unknown --bounds name must return None (CLI prints an error and exits 2)."""
    from hideout_art.cli import _resolve_bounds
    assert _resolve_bounds("unknown_name") is None


def test_named_bounds_resolver_accepts_explicit_coords():
    """Explicit 'x_min,y_min,x_max,y_max' must still work alongside named bounds."""
    from hideout_art.cli import _resolve_bounds
    assert _resolve_bounds("100,200,300,400") == (100, 200, 300, 400)


# ---------------------------------------------------------------------------
# palette_warm.json — working palette (0.2.1)
# ---------------------------------------------------------------------------

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


@pytest.mark.skipif(not HAS_ISXODNIKI, reason="no исходники/ folder present")
def test_is_art_true_for_all_new_022_decorations_in_exports():
    """Every placement of a 0.2.2 decoration in исходники files must be
    classified as art (via hash, regardless of Russian name).
    """
    seen = set()
    for substr in ["всякое", "камни и кустарники", "еще камни и растения",
                   "еще элементы", "Кордилой обозначил",
                   "водоросли и летающий песок"]:
        p = _find_isxodnik(substr)
        if p is None:
            continue
        h = Hideout.from_file(p)
        for pl in h.placements:
            if pl.hash in NEW_022_ENTRIES.values():
                assert pl.is_art is True, (
                    f"placement of {HASH_TO_NAME.get(pl.hash)} (name='{pl.name}') "
                    f"should be art but is_art={pl.is_art}"
                )
                seen.add(pl.hash)
    # Sanity: we must have seen at least one placement for each new hash
    assert seen == set(NEW_022_ENTRIES.values()), (
        f"missing hashes: {set(NEW_022_ENTRIES.values()) - seen}"
    )


# ---------------------------------------------------------------------------
# 0.2.5 — Seaweed hash + Small Coastal Stone/Maraket Rubble fill black/red
# ---------------------------------------------------------------------------

NEW_025_ENTRIES = {
    "Seaweed": 1015947674,  # Russian "Морская водоросль"
}


@pytest.mark.parametrize("name,hv", sorted(NEW_025_ENTRIES.items()))
def test_seaweed_hash_registered(name: str, hv: int):
    """Seaweed (0.2.5) must be registered in KNOWN_HASHES and reversible."""
    assert KNOWN_HASHES.get(name) == hv
    assert HASH_TO_NAME.get(hv) == name


@pytest.mark.parametrize("name", sorted(NEW_025_ENTRIES.keys()))
def test_seaweed_is_art(name: str):
    """Seaweed is decorative — must be in ART_TYPES."""
    assert name in ART_TYPES


@pytest.mark.parametrize("name,hv", sorted(NEW_025_ENTRIES.items()))
def test_seaweed_hash_no_collision(name: str, hv: int):
    """Seaweed hash must not collide with any existing hash."""
    all_hashes = list(KNOWN_HASHES.values())
    assert all_hashes.count(hv) == 1


@pytest.mark.skipif(not HAS_ISXODNIKI, reason="no исходники/ folder present")
def test_seaweed_present_in_source_export():
    """The 'водоросли и летающий песок' file must contain 7 Seaweed placements."""
    p = _find_isxodnik("водоросли и летающий песок")
    assert p is not None
    h = Hideout.from_file(p)
    seaweed = [pl for pl in h if pl.hash == KNOWN_HASHES["Seaweed"]]
    assert len(seaweed) == 7, (
        f"expected 7 Seaweed placements, found {len(seaweed)} in {p.name}"
    )


@pytest.mark.skipif(not HAS_ISXODNIKI, reason="no исходники/ folder present")
def test_seaweed_is_art_in_source_export():
    """Every Seaweed placement in the source file must classify as art (KI-9)."""
    p = _find_isxodnik("водоросли и летающий песок")
    assert p is not None
    h = Hideout.from_file(p)
    for pl in h:
        if pl.hash == KNOWN_HASHES["Seaweed"]:
            assert pl.is_art is True, (
                f"Seaweed placement (name='{pl.name}') should be art "
                f"but is_art={pl.is_art}"
            )


@pytest.mark.skipif(not HAS_ISXODNIKI, reason="no исходники/ folder present")
def test_maraket_rubble_present_in_ukroshenia_export():
    """The 'укрошения' file must contain Maraket Rubble (used for 'red' role)."""
    p = _find_isxodnik("укрошения")
    assert p is not None
    h = Hideout.from_file(p)
    rubble = [pl for pl in h if pl.hash == KNOWN_HASHES["Maraket Rubble"]]
    assert len(rubble) >= 1


@pytest.mark.skipif(not HAS_ISXODNIKI, reason="no исходники/ folder present")
def test_small_coastal_stone_present_in_stones_export():
    """The 'камни и кустарники' file must contain Small Coastal Stone (used for 'black')."""
    p = _find_isxodnik("камни и кустарники")
    assert p is not None
    h = Hideout.from_file(p)
    stone = [pl for pl in h if pl.hash == KNOWN_HASHES["Small Coastal Stone"]]
    assert len(stone) >= 1
