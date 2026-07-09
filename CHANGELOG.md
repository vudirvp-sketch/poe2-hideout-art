# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.6] - 2026-07-09

### Added
- **Pixel sampling script** (`scripts/sample_pixels.py`) — closes KI-11.
  Takes a `.hideout` file + matching `.jpg` screenshot and samples real
  pixel RGB under each art placement. Auto or manual world→pixel
  calibration (affine transform), diagnostic overlay PNG, JSON report
  with median / mean / p25 / p75 RGB per placement and per decoration.
- **`scripts/sample_all.py`** — convenience wrapper that runs
  `sample_pixels.py` on all 7 `исходники/` screenshot+hideout pairs and
  consolidates into `scripts/sampled_all.json`.
- **Pixel-sampled RGB** for 25 of 28 art decorations (Cordilina, Fringe
  Moss, Petrified Cave Figure have no sampled placements). All 7
  screenshots sanity-checked: Stash gives believable brown wood
  (R>G>B, brightness 64-182) → calibration valid.
- **`_pixel_sampling_summary_0_2_6`** block in `palette_2b.json` — full
  comparison table of pixel-sampled vs VLM-estimated RGB with drift
  analysis.
- **`_0_2_6_pixel_vs_vlm_drift`** block in `palette_2b.json` — per-channel
  drift measurements documenting where VLM was wrong.

### Changed
- **`constants.py` RGB comments** — every art decoration now carries
  both `PIXEL 0.2.6 (R,G,B)` ground-truth and `VLM 0.2.x (R,G,B)`
  estimate (where available). When they conflict, PIXEL is trusted.
- **`palette_2b.json` entries** — RGB values updated to pixel-sampled
  where pixel confirms VLM (Small Coastal Stone); kept VLM values
  where pixel sampling is unreliable (Marble-серия — KI-12).
- **`STATUS.md`** — KI-11 marked closed; new KI-12 (Marble-серия
  pixel-sampling shadow issue) added; "Что улучшать дальше" updated
  with manual-calibration TODO for KI-12.
- **`AGENTS.md`** — added navigation hint for `sample_pixels.py`;
  updated RGB-values-in-comments section to document both sources.
- **`scripts/README.md`** — full `sample_pixels.py` usage guide added.
- **`README.md`** — repository layout updated with new scripts;
  reference to `scripts/README.md` for pixel-sampling tool.

### Resolved
- **KI-11 (VLM-noise)** — closed. Pixel sampling provides ground-truth
  RGB. Confirmed: Sand Tussock real RGB is (112,99,79) — between the
  two conflicting VLM estimates (78,52,46) and (180,160,120). Maraket
  Rubble is NEUTRAL brown (125,112,87), NOT reddish (153,78,68) as VLM
  claimed. Coastal Bush is brown (114,98,70), NOT green (80,120,80).

### Known Issues
- **KI-12 (new)** — Marble-серия pixel-sampled RGB (76-196 brown range)
  is much darker than VLM 0.2.4 estimates (210-230 light gray). The
  sampling window (4 wu radius) likely hits the dark base/shadow of
  the marble object, not its bright top surface. Only Marble Table
  placement 1 gave bright cream (237,208,169). To resolve: manual
  calibration + larger `--sample-radius-wu` on a screen with good
  Marble visibility.
- **KI-2 (updated)** — `skin` TODO remains open. Pixel-sampled Sand
  Tussock (112,99,79) confirms it's too dark olive-tan for skin tone.
  Need a new peach/tan decoration from another hideout.
- **KI-10** — unchanged (placement vs sprite bounds).

## [0.2.5] - 2026-07-09

### Added
- **New decoration: Seaweed** (Морская водоросль, hash=1015947674). Found in
  new user-provided `исходники/водоросли и летающий песок.hideout` (7
  placements with variants 0..11). Added to `KNOWN_HASHES`, `ART_TYPES`,
  and `DECORATION_FOOTPRINT_CATALOG` (7 samples, min=26.1 wu, 1.5 tile,
  confidence=high). VLM-measured mid-tone RGB (128,96,64) — warm brown,
  NOT a 2B cool-palette candidate.
- **2 of 3 remaining 2B TODOs filled** in `palette_2b.json`:
  - `black` role → **Small Coastal Stone** (85,75,70) — VLM-confirmed
    `is_dark=true` on `камни и кустарники.jpg`. User intuition
    («камни разные чем не черный?») was correct.
  - `red` role → **Maraket Rubble** (153,78,68) — VLM-confirmed
    `is_reddish=true` on `укрошения.jpg`. User intuition
    («маракетские обломки вон 'красноватый/розовый' оттенок имеют»)
    was correct; the 0.2.1 estimate (138,120,94) was too neutral.
  - `skin` role remains TODO — see KI-11 below.
- **VLM re-analysis of 3 screenshots** (glm-4.6v):
  - `исходники/водоросли и летающий песок.jpg` → Seaweed (128,96,64) +
    Falling Sand re-confirmed as PINK (255,192,203) — matches 0.2.4
    (248,187,208) within noise. NOT skin/red.
  - `исходники/камни и кустарники.jpg` → Small Coastal Stone (85,75,70),
    Coastal Bush (80,120,80), Sand Tussock (180,160,120) — note Sand
    Tussock's 0.2.1 RGB was (78,52,46), a 100+ point conflict (KI-11).
  - `исходники/укрошения.jpg` → Maraket Rubble (153,78,68 reddish),
    Treasures (191,154,111 gold), Samovar (184,134,77 copper),
    Ornament (197,153,102 bronze).
- **New metadata block** in `palette_2b.json`: `_0_2_5_measured_rgb_summary`
  with new measurements + `todo_status_after_0_2_5` table.
- **New tests** in `tests/test_new_hashes.py`:
  - `test_seaweed_hash_registered` — hash registered + reversible.
  - `test_seaweed_is_art` — Seaweed in ART_TYPES.
  - `test_seaweed_hash_no_collision` — hash not duplicated.
  - `test_seaweed_present_in_source_export` — 7 placements in source file.
  - `test_seaweed_is_art_in_source_export` — KI-9 invariant for new hash.
  - `test_palette_2b_uses_small_coastal_stone_for_black` — regression
    protection for the new black-role fill.
  - `test_palette_2b_uses_maraket_rubble_for_red` — regression protection
    for the new red-role fill.
  - `test_palette_2b_black_red_rgb_values` — exact RGB regression test.
  - `test_palette_2b_only_skin_todo_remains` — proves only skin TODO left.
  - `test_maraket_rubble_present_in_ukroshenia_export` — source file check.
  - `test_small_coastal_stone_present_in_stones_export` — source file check.
  - `test_total_known_hash_count` updated 46 → 47.
  - `test_parse_isxodnik_file_no_unknowns` extended with `водоросли и
    летающий песок` substring (file must parse with no unknowns after
    Seaweed is registered).
  - `test_isxodnik_files_use_canal_hideout_hash` extended with new file.
  - `test_is_art_true_for_all_new_022_decorations_in_exports` extended
    with new file.
  - `RUSSIAN_NAME_TO_CANONICAL` extended with `Летающий песок` →
    `Falling Sand` and `Морская водоросль` → `Seaweed` mappings.
  - `test_palette_2b_still_has_todos` updated — now expects 1 TODO
    (skin only), down from 3 in 0.2.4 and 6 in 0.2.3.
  - `test_palette_2b_marble_only_section_loads_via_palette_class` updated
    — now expects 10 working entries (4 original + 4 marble + 2 new
    role-fills), up from 8 in 0.2.4.
- Total test count: **255** (254 pass, 1 skipped).

### Changed
- `src/hideout_art/constants.py`:
  - Added Seaweed to KNOWN_HASHES, ART_TYPES, DECORATION_FOOTPRINT_CATALOG
    (7 samples, min=26.1 wu, 1.5 tile, confidence=high).
  - `Falling Sand` catalog entry updated: 0 samples/none → 1 sample/single
    (a placement was added in the new `водоросли и летающий песок.hideout`).
  - Small Coastal Stone comment updated: `small DARK warm-gray stone
    (85,75,70) — VLM 0.2.5, is_dark=true → candidate for 2B 'black' role`.
  - Coastal Bush comment updated with VLM 0.2.5 RGB (80,120,80).
  - Maraket Rubble/Treasures/Samovar/Ornament comments updated with 0.2.5
    VLM-measured RGB (replacing 0.2.1 estimates which were too neutral).
  - Falling Sand comment updated with 0.2.5 re-measurement (255,192,203).
  - Sand Tussock comment now documents the 0.2.1 vs 0.2.5 RGB conflict
    (78,52,46) vs (180,160,120) — see KI-11.
- `examples/palette_2b.json` — see Added section above.
- `STATUS.md` — rewritten: KI-2 partial 0.2.5 (5/6 TODOs filled), new
  KI-11 (VLM noise), new future-task "Drawing primitives из декораций"
  (per user request — lines/curves/circles/S-shapes/filled circles from
  layered decorations).
- `AGENTS.md` — hash count 46→47, ART_TYPES 27→28, new 0.2.5 notes.
- `docs/img2hideout.md` — palette_2b section updated: 5 of 6 TODOs filled.
- `pyproject.toml` and `src/hideout_art/__init__.py` — version 0.2.4 → 0.2.5.

### Fixed
- None (no new bugs in code). The 0.2.1 RGB estimates for Maraket-серия
  were qualitatively corrected by 0.2.5 re-measurement — see KI-11 for
  why this is a documentation issue, not a code bug.

### Known Issues
- **KI-11 (new 0.2.5):** VLM-измерения RGB шумят — Sand Tussock varies
  from (78,52,46) in 0.2.1 to (180,160,120) in 0.2.5 (100+ RGB point
  swing, likely sampling different parts of the plant). Maraket-серия
  also drifted substantially. All VLM RGB values are first-pass estimates
  pending pixel sampling. Closes part of KI-2 but blocks `skin` role.
- KI-2 is now **partial 0.2.5** (was partial 0.2.4): 5/6 TODOs filled,
  only `skin` remains.
- KI-10 is unchanged.

## [0.2.4] - 2026-07-09

### Added
- **VLM-measured RGB for cold-tone decorations.** Used the `VLM` skill
  (glm-4.6v) to analyze the `исходники/еще элементы.jpg` screenshot
  (which contains Marble Bench/Table/Walls/Fountain + Cave Fossil +
  Cave Coral + Summit Brazier placements). Identified each decoration
  visually and reported mid-tone RGB values.
- **`palette_2b.json` partial fill.** Replaced 3 of 6 TODO placeholders
  with VLM-measured Marble-серия entries:
  - `white`  role → Marble Fountain (230, 230, 220) — brightest marble
  - `silver` role → Marble Table    (200, 200, 195) — mid light gray
  - `gray`   role → Marble Bench    (210, 210, 205) — light cool gray
  - `gray` alt → Marble Walls       (210, 210, 205) — near-twin of Bench
- **New metadata block** in `palette_2b.json`: `_rgb_sources` (method
  description + per-decoration RGB attribution), `_0_2_4_measured_rgb_summary`
  (compact table of measured values and qualitative findings).
- **5 new pytest tests** in `tests/test_new_hashes.py`:
  - `test_palette_2b_still_has_todos` (updated) — now expects 3 TODOs
    (black/skin/red), down from 6.
  - `test_palette_2b_uses_marble_series` — verifies Marble Fountain/
    Table/Bench/Walls are in the palette.
  - `test_palette_2b_marble_rgb_values` — regression protection for
    the VLM-measured RGB values.
  - `test_palette_2b_marble_entries_resolve_to_known_hashes` —
    catches typos in decoration names.
  - `test_palette_2b_marble_only_section_loads_via_palette_class` —
    proves that the Marble-серия entries alone form a valid Palette
    (only the 3 remaining TODOs keep palette_2b.json from loading).
- Total test count: **237** (236 pass, 1 skipped).

### Changed
- `src/hideout_art/constants.py` — comments for Cave Fossil/Cave Coral/
  Summit Brazier/Marble Bench/Table/Walls/Fountain updated with VLM-
  measured RGB values. Cave Fossil comment corrected from "light
  gray/white ammonite-like" to "BROWN rock (140,110,80)" — the prior
  0.2.2 guess was wrong.
- `STATUS.md` — KI-2 status updated to "partial 0.2.4" with a full
  RGB-measurement table; "Что улучшать дальше" trimmed; new principle
  added: "RGB-значения — с указанием источника".
- `AGENTS.md` — note added about the VLM-measured RGB source for the
  Marble-серия and the corrected Cave Fossil colour.
- `docs/img2hideout.md` — palette_2b.json section updated: 3 of 6 TODOs
  filled, 3 remain (black/skin/red); new "VLM-измеренные RGB" subsection.
- `examples/palette_2b.json` — see Added section above.
- Version bumped to `0.2.4` in `pyproject.toml` and `__init__.py`.

### Fixed
- **Cave Fossil colour correction (qualitative).** Prior 0.2.2 comment
  in `constants.py` guessed Cave Fossil as "light gray/white ammonite-
  like" — VLM analysis of the screenshot revealed it is actually BROWN
  (140,110,80), a warm rock. This means Cave Fossil is NOT a candidate
  for the 2B cool palette (was listed as a candidate in 0.2.2). The
  `_0_2_2_candidates_needing_rgb_sampling` block in `palette_2b.json`
  was effectively superseded by the new `_0_2_4_measured_rgb_summary`
  block, which records the correction.

### Known Issues (no change in 0.2.4)
- KI-2 is now **partial 0.2.4** (was partial 0.2.2): 3 of 6 TODOs filled,
  3 remain (black/skin/red).
- KI-10 is unchanged: catalog measures placement footprint, not sprite
  bounds.

## [0.2.3] - 2026-07-09

### Added
- **`DECORATION_FOOTPRINT_CATALOG`** in `src/hideout_art/constants.py` —
  placement footprint estimates for all 27 art decorations. Each entry
  records: number of placements observed in `исходники/*.hideout`, min
  and median pairwise Euclidean distance between same-hash placements,
  estimated tile footprint (rounded up to nearest 0.5 tile), and a
  confidence level (`high` ≥5 samples, `medium` 3-4, `low` 2, `single` 1,
  `none` 0).
- **`DecorationFootprint`** NamedTuple + **`FOOTPRINT_CONFIDENCE_LEVELS`**
  frozenset in `constants.py` for type-safe access to the catalog.
- **`scripts/measure_decorations.py`** — dev script that re-derives the
  catalog from `исходники/*.hideout` and prints a table + JSON dump
  (`scripts/decoration_footprints.json`, gitignored as reproducible).
- **94 new pytest tests** in `tests/test_footprints.py`:
  - Catalog covers all `ART_TYPES` and only `ART_TYPES` (no functional
    objects).
  - Every `confidence` value is valid; confidence matches `samples` count.
  - `estimated_tile_footprint` is consistent with `min_spacing_wu`.
  - Specific regression tests for Beech Tree (low-conf, 1 tile),
    Cordilina (11 samples, high-conf), Marble Table (low-conf, 2 tiles —
    KI-10).
  - Atziri Statue explicitly excluded from catalog (per user request).
  - **Ground-truth check**: `samples` field matches actual placement
    count in `исходники/*.hideout` — fails loudly if catalog drifts out
    of sync with source files.
  - Total test count: 233 collected (232 pass, 1 skipped).

### Changed
- `STATUS.md` — rewritten: KI-10 added, "Что улучшать дальше" trimmed to
  5 items, test count updated to 233, hash count still 46 (no new
  hashes — only metadata about existing decorations).
- `AGENTS.md` — added pointer to `DECORATION_FOOTPRINT_CATALOG` and
  `scripts/measure_decorations.py`.
- `docs/img2hideout.md` — added "Каталог размеров декораций" section
  explaining what the catalog measures, what it doesn't (KI-10), and
  how it will be used by the planned multi-pass renderer.
- `scripts/README.md` — added `measure_decorations.py` to the available
  scripts table.
- `.gitignore` — added `scripts/decoration_footprints.json` (auto-
  generated, reproducible).
- Version bumped to `0.2.3` in `pyproject.toml` and `__init__.py`.

### Fixed
- None (no new bugs). All previously known issues (KI-1..KI-9) remain
  fixed; KI-10 is a NEW known issue documenting the placement-vs-sprite-
  bounds limitation of the new catalog.

## [0.2.2] - 2026-07-09

### Added
- **18 new decoration hashes** from user-provided `исходники/` folder
  (5 `.hideout` exports, all targeting Canal Hideout, hash 60415):
  Cordilina, Petrified Cave Figure, Coastal Bush, Small/Medium Coastal
  Stone, Slender Seedling, Log, Beech Tree, Pile of Leaves, Cave Fossil,
  Cave Coral, Summit Brazier, Marble Bench/Table/Walls/Fountain, Camp
  Crate, Camp Gear. All added to `ART_TYPES`.
- `CANAL_HIDEOUT_HASH` (60415) + `CANAL_HIDEOUT_BOUNDS = (700, 540, 860, 775)`
  + `NAMED_BOUNDS` registry + `--bounds canal` CLI shortcut.
- 70 new pytest cases in `tests/test_new_hashes.py` (total: 140).

### Changed
- `constants.py` — `KNOWN_HASHES` 28 → 46 entries; Canal geometry added.
- `cli.py` — `_resolve_bounds()` helper for named/explicit bounds.
- Version bumped to `0.2.2`.

## [0.2.1] - 2026-07-09

### Added
- 5 warm-tone Maraket/Coastal Pebble hashes. `examples/palette_warm.json`
  (9-colour working palette). `tile_size` parameter (closes KI-1).
  `DEFAULT_TILE_SIZE_WORLD_UNITS = 23`. 26 new pytest tests (total: 70).

### Fixed
- **KI-9**: `Placement.is_art` now resolves via hash, not name — Russian-
  named placements correctly classified as art.

## [0.2.0] - 2026-07-09

### Added
- `img2hideout` overhaul: alpha-channel support, 3 colour-distance
  metrics, Floyd-Steinberg dithering, jitter, `step`, `bounds`,
  `resample`, `--preview`. `examples/palette_2b.json` template.
  `docs/img2hideout.md` reference. 11 new pytest tests (total: 44).

## [0.1.0] - 2026-07-09

### Added
- Initial release: tolerant regex parser, `Hideout`/`Placement`
  dataclasses, geometric transforms, header rewriter, PNG preview,
  `img2hideout`, CLI (`inspect`/`layers`/`stats`/`preview`/`shift`/
  `transfer`/`img2hideout`), 23 known hashes, docs, 33 pytest tests.

[Unreleased]: https://github.com/vudirvp-sketch/poe2-hideout-art/compare/v0.2.5...HEAD
[0.2.5]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.5
[0.2.4]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.4
[0.2.3]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.3
[0.2.2]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.2
[0.2.1]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.1
[0.2.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.2.0
[0.1.0]: https://github.com/vudirvp-sketch/poe2-hideout-art/releases/tag/v0.1.0
