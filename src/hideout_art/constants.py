"""Known decoration hashes and metadata for PoE2 hideouts.

This catalogue grows as more hideout files are observed. Each entry maps
a human-readable name to its stable ``hash`` (the in-game asset id).

If you encounter an unknown hash while parsing, the parser will keep it
verbatim — the writer never drops data. Submit a PR with new entries
discovered in the wild.

Naming convention: English canonical names. Russian (or other localised)
in-game names are NOT stored here — the parser keeps the original name
verbatim, and ``Placement.is_art`` resolves via hash. This is the KI-9 fix:
a Russian-named ``"Береговая галька"`` resolves via hash to ``"Coastal Pebble"``
and is correctly classified as art.
"""

from __future__ import annotations

from typing import NamedTuple

# (name) -> hash
# Values extracted from real .hideout exports of "Canal Hideout"
# (hideout_hash=60415). The catalogue grows in three layers:
#   * 0.1.0 — 23 original Canal Hideout hashes (functional + 4 art).
#   * 0.2.1 — 5 warm-tone Maraket/Coastal Pebble hashes from user exports.
#   * 0.2.2 — 18 new hashes from user-provided "исходники/" folder
#             (coastal stones, marble furniture, cave fossils, trees, etc.).
KNOWN_HASHES: dict[str, int] = {
    # ------------------------------------------------------------------ #
    # Functional objects (1 per hideout, typically)
    # ------------------------------------------------------------------ #
    "Stash":               3230065491,
    "Guild Stash":          139228481,
    "Waypoint":            1224707366,
    "Ziggurat Map Device":     76459657,
    "Relic Locker":           12969733,
    "Reforging Bench":      3263423625,
    "Salvage Bench":        3734046884,
    "Well":                 2057229261,
    "Wardrobe Decoration":  2914603195,
    "Verisium Anvil":       2920892519,
    "Atziri Statue":        3375587104,

    # NPCs
    "Alva":                 2115859440,
    "Zelina":               1023253651,
    "Zolin":                2204408127,
    "Doryani":              3673653565,
    "Ange":                 2297799330,
    "Hilda":                1986775202,
    "Jado":                  204349116,
    "Farrow":                434172762,

    # ------------------------------------------------------------------ #
    # Decorations used for floor art (original Canal Hideout palette, 0.1.0)
    # RGB values: PIXEL = pixel-sampled (0.2.6, scripts/sample_pixels.py),
    # VLM = glm-4.6v estimate (0.2.4/0.2.5, noisy — see KI-11).
    # ------------------------------------------------------------------ #
    "Long Grass":           2219637749,  # PIXEL 0.2.6 (136,119,93) brown-tan. VLM was (46,125,50) green — wrong.
    "Falling Sand":         3853073345,  # PIXEL 0.2.6 (145,125,101) brown-tan (sampling hit gap between particles). VLM 0.2.5 (255,192,203) pink (sampled actual particle). Particle effect — colour depends on sampling point.
    "Fringe Moss":          1459723677,  # Not pixel-sampled (0 placements in исходники). VLM 0.2.1 (139,195,74) bright green — unverified.
    "Sand Tussock":          146816198,  # PIXEL 0.2.6 (112,99,79) dark olive-tan. RESOLVES KI-11: between VLM 0.2.1 (78,52,46) and VLM 0.2.5 (180,160,120). NOT skin tone — too dark and too olive.

    # ------------------------------------------------------------------ #
    # Warm-tone earth decorations (added in 0.2.1 from user-provided exports).
    # Sampled median in-game RGB values are kept in the comment for reference;
    # use them when building palettes (see examples/palette_warm.json).
    # NOTE (0.2.6): pixel sampling (scripts/sample_pixels.py) gave ground-truth
    # RGB that differs from VLM estimates by 30-100+ points — see KI-11 (closed)
    # and _pixel_sampling_summary_0_2_6 in examples/palette_2b.json.
    # Maraket Rubble pixel-sampled (125,112,87) is NEUTRAL BROWN, not reddish
    # as VLM 0.2.5 (153,78,68) claimed.
    # ------------------------------------------------------------------ #
    "Maraket Rubble":       3012657298,  # PIXEL 0.2.6 (125,112,87) neutral brown. VLM 0.2.5 (153,78,68) was wrong — NOT reddish.
    "Maraket Treasures":    1078696835,  # PIXEL 0.2.6 (116,102,85) brown. VLM 0.2.5 (191,154,111) too bright.
    "Maraket Samovar":       57228444,   # PIXEL 0.2.6 (194,157,118) copper. VLM 0.2.5 (184,134,77) close.
    "Maraket Ornament":     2125171205,  # PIXEL 0.2.6 (113,104,82) brown. VLM 0.2.5 (197,153,102) too bright.
    "Coastal Pebble":       2365064644,  # PIXEL 0.2.6 (127,111,86) tan. VLM 0.2.1 (134,115,94) close.

    # ------------------------------------------------------------------ #
    # New Canal Hideout decorations (added in 0.2.2 from "исходники/" folder).
    # Source: 5 user-provided .hideout exports, each placing a handful of
    # new decorations inside Canal Hideout (hideout_hash=60415). RGB values
    # below are ESTIMATES from the corresponding screenshots; refine by
    # sampling the in-game pixel under each placement.
    # ------------------------------------------------------------------ #
    # Boundary / marker decorations (used by user to outline the playable canvas)
    "Cordilina":            1082688452,  # green decorative plant, ~1 tile
    "Petrified Cave Figure": 2014424642, # large statue (estimate 2-3 tiles)

    # Coastal stones (warm tan/gray, three sizes)
    "Coastal Bush":         2984478824,  # PIXEL 0.2.6 (114,98,70) brown. VLM 0.2.5 (80,120,80) green — wrong, bush is brown.
    "Small Coastal Stone":  1122244925,  # PIXEL 0.2.6 (81,80,60) dark warm-gray. CONFIRMS VLM 0.2.5 (85,75,70). Fills 2B 'black' role.
    "Medium Coastal Stone":  369950199,  # PIXEL 0.2.6 (71,67,50) darker than Small Coastal Stone.

    # Plants / foliage
    "Slender Seedling":     532751457,   # PIXEL 0.2.6 (105,93,67) dark olive-tan. Russian "Тонкосемянник"; bushy shrub.
    "Log":                  2780985165,  # PIXEL 0.2.6 (162,138,107) warm brown bark.
    "Beech Tree":           2796444611,  # PIXEL 0.2.6 (88,81,66) dark gray-brown. Large tree (~2 tiles).
    "Pile of Leaves":       4294658310,  # PIXEL 0.2.6 (122,109,91) autumn warm brown.

    # Cave / mountain decorations
    "Cave Fossil":          2206403756,  # PIXEL 0.2.6 (159,136,109) warm brown. VLM 0.2.4 (140,110,80) close.
    "Cave Coral":           2359120247,  # PIXEL 0.2.6 (170,144,114) light brown. VLM 0.2.4 (150,130,110) close.
    "Summit Brazier":       2623109233,  # PIXEL 0.2.6 (156,133,106) golden-brown metal. VLM 0.2.4 (180,140,80) close.

    # Marble furniture — KI-12: pixel-sampled RGB (76-110 brown range) is much
    # darker than VLM 0.2.4 estimates (210-230 light gray). Sampling window
    # likely hits the dark base/shadow of the marble object, not its bright
    # top surface. Only Marble Table placement 1 gave bright cream (237,208,169).
    # VLM values retained in palette_2b.json until manual calibration resolves KI-12.
    "Marble Bench":          534959854,  # PIXEL 0.2.6 (79,64,45) brown. VLM 0.2.4 (210,210,205) light gray — KI-12 conflict.
    "Marble Table":         4056218057,  # PIXEL 0.2.6 (196,170,136) cream. VLM 0.2.4 (200,200,195) close on R, browner on G/B.
    "Marble Walls":         1380152311,  # PIXEL 0.2.6 (76,68,52) brown. VLM 0.2.4 (210,210,205) — KI-12 conflict.
    "Marble Fountain":       525963527,  # PIXEL 0.2.6 (110,103,76) brown. VLM 0.2.4 (230,230,220) near-white — KI-12 conflict.

    # Camp props (warm brown wood + canvas)
    "Camp Crate":           2156404357,  # PIXEL 0.2.6 (138,122,94) warm brown wood.
    "Camp Gear":             412387213,  # PIXEL 0.2.6 (70,66,56) dark brown.

    # ------------------------------------------------------------------ #
    # Aquatic decoration (added in 0.2.5 from "исходники/водоросли и летающий
    # песок.hideout"). Russian in-game name "Морская водоросль". 7 placements
    # in source file (variants 0..11). PIXEL 0.2.6 (126,111,87) warm brown —
    # confirms VLM 0.2.5 (128,96,64) within noise. NOT a cool-palette candidate.
    # ------------------------------------------------------------------ #
    "Seaweed":             1015947674,  # PIXEL 0.2.6 (126,111,87) warm brown. Confirms VLM 0.2.5 (128,96,64).
}

# Reverse lookup: hash -> name
HASH_TO_NAME: dict[int, str] = {v: k for k, v in KNOWN_HASHES.items()}

# Decorations whose primary use is artistic (not gameplay-blocking).
# Used by ``Hideout.shift(art_only=True)`` and similar filters.
ART_TYPES: frozenset[str] = frozenset({
    # Original Canal Hideout art (0.1.0)
    "Long Grass",
    "Falling Sand",
    "Fringe Moss",
    "Sand Tussock",
    # Warm-tone earth (0.2.1)
    "Maraket Rubble",
    "Maraket Treasures",
    "Maraket Samovar",
    "Maraket Ornament",
    "Coastal Pebble",
    # New Canal Hideout art (0.2.2) — all 18 new entries are decorative
    "Cordilina",
    "Petrified Cave Figure",
    "Coastal Bush",
    "Small Coastal Stone",
    "Medium Coastal Stone",
    "Slender Seedling",
    "Log",
    "Beech Tree",
    "Pile of Leaves",
    "Cave Fossil",
    "Cave Coral",
    "Summit Brazier",
    "Marble Bench",
    "Marble Table",
    "Marble Walls",
    "Marble Fountain",
    "Camp Crate",
    "Camp Gear",
    # Aquatic (0.2.5)
    "Seaweed",
    # Add more as the catalogue grows — keep functional objects OUT.
})

# Magic numbers for the ``r`` (rotation) field. PoE2 stores rotation as
# an unsigned 16-bit fraction of a full turn (0..65535 = 0°..360°).
ROTATION_MODULUS: int = 1 << 16  # 65536

# Magic numbers for the ``fv`` (flags + variant) field.
# Bit 0x80 = horizontal flip. Lower 7 bits = variant index (0..127).
FV_FLIP_X_BIT: int = 0x80
FV_VARIANT_MASK: int = 0x7F

# Calibrated typical decoration footprint in world units. Derived from
# observed placement deltas in user-provided exports: adjacent manually-
# placed Maraket Rubble / Coastal Pebble / Coastal Bush / Slender Seedling
# placements sit ~15-30 world units apart, with median ~23. Corresponds
# to roughly one game tile. Used by ``img2hideout.image_to_hideout`` when
# the user passes ``tile_size`` to auto-compute ``step`` so that one
# decoration is placed per tile (no overlap, no gaps).
DEFAULT_TILE_SIZE_WORLD_UNITS: int = 23

# --------------------------------------------------------------------------- #
# Canal Hideout — known geometry
# --------------------------------------------------------------------------- #
# Hash of the Canal Hideout map itself (the value stored in the
# ``hideout_hash`` header field of every Canal Hideout .hideout file).
CANAL_HIDEOUT_HASH: int = 60415

# Approximate playable-canvas bounding box for Canal Hideout, in world
# coordinates. Derived from a user-provided "boundary outline" export
# (исходники/Кордилой обозначил условные границы полотна...hideout):
# the user placed 11 "Cordilina" decorations around the playable perimeter
# plus one "Petrified Cave Figure" near the centre. Bounding box of those
# 11 Cordilina placements: x ∈ [707, 854], y ∈ [542, 772]. We round to
# (700, 540, 860, 775) for CLI ergonomics — the deltas are <7 wu, well
# inside the user's "условный центр плюс-минус" tolerance.
#
# Use with:  hideout-art img2hideout img.png -o out.hideout --bounds canal
# Or in Python:
#   from hideout_art.constants import CANAL_HIDEOUT_BOUNDS
#   image_to_hideout("img.png", bounds=CANAL_HIDEOUT_BOUNDS, ...)
CANAL_HIDEOUT_BOUNDS: tuple[int, int, int, int] = (700, 540, 860, 775)

# Named bounds registry — CLI ``--bounds <name>`` looks up here.
# Add new hideouts as their canvases get measured.
NAMED_BOUNDS: dict[str, tuple[int, int, int, int]] = {
    "canal": CANAL_HIDEOUT_BOUNDS,
}


# --------------------------------------------------------------------------- #
# Decoration footprint catalogue (0.2.3)
# --------------------------------------------------------------------------- #
# Estimated PLACEMENT footprint for each decoration in ART_TYPES. Derived
# from MIN pairwise Euclidean distance between same-hash placements across
# all исходники/*.hideout exports (see scripts/measure_decorations.py).
#
# What this measures:
#   * The MIN spacing observed is an UPPER BOUND on the placement tile
#     footprint — if the user placed two Beech Trees 22 wu apart vertically
#     without visible overlap in-game, the placement tile is at most 22 wu.
#
# What this does NOT measure (KI-10):
#   * Sprite bounds. The visible canopy of a tree extends well beyond its
#     placement tile. For img2hideout step calibration, the placement
#     footprint is what matters; for visual overlap detection you would
#     need in-game sprite measurement (not derivable from .hideout files).
#   * Rotation-dependent footprint. All observations are at r=0; rotated
#     placements may have different effective bounds.
#
# Confidence levels (by sample size):
#   high    — >=5 placements (min distance is reliable)
#   medium  — 3-4 placements
#   low     — 2 placements (min distance is a noisy estimate — the only
#             pair observed may have been placed far apart by coincidence)
#   single  — 1 placement (cannot measure; footprint unknown)
#   none    — decoration not present in исходники/ (no measurement possible)
#
# estimated_tile_footprint = ceil(min_spacing_wu / DEFAULT_TILE_SIZE_WORLD_UNITS * 2) / 2
# (rounded UP to nearest 0.5 tile — err on the side of sparser placement.)
#
# Atziri Statue and other functional objects are deliberately excluded:
# per user instruction, they are huge and will not participate in art
# compositions. Only ART_TYPES entries are catalogued.

class DecorationFootprint(NamedTuple):
    """Placement footprint estimate for one decoration type."""

    samples: int                                # placements observed in исходники/
    min_spacing_wu: float | None                # closest pair observed (UPPER BOUND)
    median_spacing_wu: float | None             # typical spacing (skewed by scatter)
    estimated_tile_footprint: float | None      # min_spacing / DEFAULT_TILE_SIZE, rounded up to 0.5
    confidence: str                             # high|medium|low|single|none


DECORATION_FOOTPRINT_CATALOG: dict[str, DecorationFootprint] = {
    # ----- original Canal Hideout art (0.1.0) -----
    "Long Grass":            DecorationFootprint(5,  13.3, 17.3,  1.0, "high"),
    "Falling Sand":          DecorationFootprint(1,  None, None,  None, "single"),  # 1 placement in водоросли и летающий песок.hideout (0.2.5)
    "Fringe Moss":           DecorationFootprint(0,  None, None,  None, "none"),
    "Sand Tussock":          DecorationFootprint(7,  17.1, 38.9,  1.0, "high"),

    # ----- warm-tone earth (0.2.1) -----
    "Maraket Rubble":        DecorationFootprint(11, 13.6, 33.0,  1.0, "high"),
    "Maraket Treasures":     DecorationFootprint(1,  None, None,  None, "single"),
    "Maraket Samovar":       DecorationFootprint(2,  14.3, 14.3,  1.0, "low"),
    "Maraket Ornament":      DecorationFootprint(4,  18.2, 32.1,  1.0, "medium"),
    "Coastal Pebble":        DecorationFootprint(9,  29.7, 58.0,  1.5, "high"),

    # ----- new Canal Hideout art (0.2.2) -----
    # Boundary / marker
    "Cordilina":             DecorationFootprint(11, 17.2, 144.8, 1.0, "high"),
    "Petrified Cave Figure": DecorationFootprint(1,  None, None,  None, "single"),

    # Coastal stones
    "Coastal Bush":          DecorationFootprint(4,  24.2, 38.0,  1.5, "medium"),
    "Small Coastal Stone":   DecorationFootprint(5,  20.2, 42.4,  1.0, "high"),
    "Medium Coastal Stone":  DecorationFootprint(9,  25.1, 54.9,  1.5, "high"),

    # Plants / foliage
    "Slender Seedling":      DecorationFootprint(7,  18.9, 51.6,  1.0, "high"),
    "Log":                   DecorationFootprint(2,  18.0, 18.0,  1.0, "low"),
    "Beech Tree":            DecorationFootprint(2,  22.0, 22.0,  1.0, "low"),
    "Pile of Leaves":        DecorationFootprint(5,  15.5, 25.5,  1.0, "high"),

    # Cave / mountain
    "Cave Fossil":           DecorationFootprint(8,  17.0, 41.4,  1.0, "high"),
    "Cave Coral":            DecorationFootprint(1,  None, None,  None, "single"),
    "Summit Brazier":        DecorationFootprint(4,  17.5, 28.2,  1.0, "medium"),

    # Marble furniture (light gray/white — RGB still unmeasured, see KI-2)
    "Marble Bench":          DecorationFootprint(1,  None, None,  None, "single"),
    "Marble Table":          DecorationFootprint(2,  45.6, 45.6,  2.0, "low"),  # see KI-10: low-conf
    "Marble Walls":          DecorationFootprint(1,  None, None,  None, "single"),
    "Marble Fountain":       DecorationFootprint(1,  None, None,  None, "single"),

    # Camp props
    "Camp Crate":            DecorationFootprint(4,  15.7, 30.9,  1.0, "medium"),
    "Camp Gear":             DecorationFootprint(1,  None, None,  None, "single"),

    # Aquatic (0.2.5) — 7 placements in водоросли и летающий песок.hideout.
    # Re-run scripts/measure_decorations.py to refresh after adding more samples.
    "Seaweed":               DecorationFootprint(7,  26.1, 68.9,  1.5, "high"),
}


# Confidence level set — used by tests for validation.
FOOTPRINT_CONFIDENCE_LEVELS: frozenset[str] = frozenset({
    "high", "medium", "low", "single", "none",
})
