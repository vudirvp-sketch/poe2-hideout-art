"""Known decoration hashes and metadata for PoE2 hideouts.

This catalogue grows as more hideout files are observed. Each entry maps
a human-readable name to its stable ``hash`` (the in-game asset id).

If you encounter an unknown hash while parsing, the parser will keep it
verbatim — the writer never drops data. Submit a PR with new entries
discovered in the wild.
"""

# (name) -> hash
# All values below were extracted from a real .hideout export of
# "Canal Hideout" (hideout_hash=60415) containing 752 placements.
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

    # Decorations used for floor art
    "Long Grass":           2219637749,
    "Falling Sand":         3853073345,
    "Fringe Moss":          1459723677,
    "Sand Tussock":          146816198,
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
    # Add more as the catalogue grows — keep functional objects OUT.
})

# Magic numbers for the ``r`` (rotation) field. PoE2 stores rotation as
# an unsigned 16-bit fraction of a full turn (0..65535 = 0°..360°).
ROTATION_MODULUS: int = 1 << 16  # 65536

# Magic numbers for the ``fv`` (flags + variant) field.
# Bit 0x80 = horizontal flip. Lower 7 bits = variant index (0..127).
FV_FLIP_X_BIT: int = 0x80
FV_VARIANT_MASK: int = 0x7F
