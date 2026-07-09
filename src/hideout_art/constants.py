"""Known decoration hashes and metadata for PoE2 hideouts.

This catalogue grows as more hideout files are observed. Each entry maps
a human-readable name to its stable ``hash`` (the in-game asset id).

If you encounter an unknown hash while parsing, the parser will keep it
verbatim — the writer never drops data. Submit a PR with new entries
discovered in the wild.
"""

# (name) -> hash
# Values extracted from real .hideout exports of "Canal Hideout"
# (hideout_hash=60415). Maraket / Coastal Pebble hashes were added in 0.2.1
# from user-provided exports (see CHANGELOG.md).
KNOWN_HASHES: dict[str, int] = {
    # Functional objects (1 per hideout, typically)
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

    # Decorations used for floor art (original Canal Hideout palette)
    "Long Grass":           2219637749,
    "Falling Sand":         3853073345,
    "Fringe Moss":          1459723677,
    "Sand Tussock":          146816198,

    # Warm-tone earth decorations (added in 0.2.1 from user-provided exports).
    # Sampled median in-game RGB values are kept in the comment for reference;
    # use them when building palettes (see examples/palette_warm.json).
    "Maraket Rubble":       3012657298,  # warm tan/khaki  ~ (138,120, 94)
    "Maraket Treasures":    1078696835,  # dark warm gray  ~ (108, 91, 83)
    "Maraket Samovar":       57228444,   # light warm gray ~ (148,133,115)
    "Maraket Ornament":     2125171205,  # warm tan/khaki  ~ (136,120, 97)
    "Coastal Pebble":       2365064644,  # warm tan/khaki  ~ (134,115, 94)
}

# Reverse lookup: hash -> name
HASH_TO_NAME: dict[int, str] = {v: k for k, v in KNOWN_HASHES.items()}

# Decorations whose primary use is artistic (not gameplay-blocking).
# Used by ``Hideout.shift(art_only=True)`` and similar filters.
ART_TYPES: frozenset[str] = frozenset({
    "Long Grass",
    "Falling Sand",
    "Fringe Moss",
    "Sand Tussock",
    "Maraket Rubble",
    "Maraket Treasures",
    "Maraket Samovar",
    "Maraket Ornament",
    "Coastal Pebble",
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
# placed Maraket Rubble / Coastal Pebble placements sit ~15-23 world
# units apart, which corresponds to roughly one game tile (~23 wu).
# Used by ``img2hideout.image_to_hideout`` when the user passes
# ``tile_size`` to auto-compute ``step`` so that one decoration is placed
# per tile (no overlap, no gaps).
DEFAULT_TILE_SIZE_WORLD_UNITS: int = 23
