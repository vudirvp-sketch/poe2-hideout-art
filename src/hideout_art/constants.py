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
    # ------------------------------------------------------------------ #
    "Long Grass":           2219637749,  # Russian in-game: "Высокая трава"
    "Falling Sand":         3853073345,
    "Fringe Moss":          1459723677,
    "Sand Tussock":          146816198,  # Russian in-game: "Песчаный кустарник"

    # ------------------------------------------------------------------ #
    # Warm-tone earth decorations (added in 0.2.1 from user-provided exports).
    # Sampled median in-game RGB values are kept in the comment for reference;
    # use them when building palettes (see examples/palette_warm.json).
    # ------------------------------------------------------------------ #
    "Maraket Rubble":       3012657298,  # warm tan/khaki  ~ (138,120, 94)
    "Maraket Treasures":    1078696835,  # dark warm gray  ~ (108, 91, 83)
    "Maraket Samovar":       57228444,   # light warm gray ~ (148,133,115)
    "Maraket Ornament":     2125171205,  # warm tan/khaki  ~ (136,120, 97)
    "Coastal Pebble":       2365064644,  # warm tan/khaki  ~ (134,115, 94)

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
    "Coastal Bush":         2984478824,  # coastal bush, warm green-tan
    "Small Coastal Stone":  1122244925,  # small stone ~0.5 tile
    "Medium Coastal Stone":  369950199,  # medium stone ~1 tile

    # Plants / foliage
    "Slender Seedling":     532751457,   # Russian "Тонкосемянник"; bushy shrub
    "Log":                  2780985165,  # fallen log, brown bark
    "Beech Tree":           2796444611,  # large tree (estimate 2-3 tiles)
    "Pile of Leaves":       4294658310,  # leaf pile, autumn warm tones

    # Cave / mountain decorations
    "Cave Fossil":          2206403756,  # light gray/white ammonite-like
    "Cave Coral":           2359120247,  # pale gray/pink coral
    "Summit Brazier":       2623109233,  # stone brazier (fire = warm orange)

    # Marble furniture (light gray/white — closest existing match for 2B "white")
    "Marble Bench":          534959854,  # light gray marble
    "Marble Table":         4056218057,  # light gray marble
    "Marble Walls":         1380152311,  # light gray marble
    "Marble Fountain":       525963527,  # light gray marble + water

    # Camp props (warm brown wood + canvas)
    "Camp Crate":           2156404357,  # wooden crate, warm brown
    "Camp Gear":             412387213,  # bedroll/sack, warm tan
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
