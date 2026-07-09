"""Tests for the drawing-primitives module.

Covers:
* Decoration validation (must be ART_TYPES + KNOWN_HASHES).
* Spacing derivation from the catalog.
* Geometry correctness for each core primitive (line, hollow_circle,
  filled_circle, s_snake, thick_line_with_contours).
* Geometry correctness for each mosaic primitive (arc, rectangle, polygon,
  grid) — added in 0.2.8.
* The curated ``center_composition`` end-to-end: fits inside Canal Hideout
  bounds when centred at (780, 657), uses only known art decorations, and
  has no duplicate placements per decoration.
* Round-trip: a Hideout with appended primitives survives parse → write →
  parse unchanged.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from hideout_art import Hideout
from hideout_art.constants import (
    ART_TYPES,
    CANAL_HIDEOUT_BOUNDS,
    KNOWN_HASHES,
)
from hideout_art.primitives import (
    PrimitiveOptions,
    arc,
    bezier_curve,
    center_composition,
    crosshatch,
    filled_circle,
    grid,
    hollow_circle,
    line,
    mosaic_composition,
    polygon,
    polyline,
    rectangle,
    s_snake,
    safe_spacing,
    thick_arc,
    thick_line_with_contours,
    thick_ring,
)


# --------------------------------------------------------------------------- #
# safe_spacing
# --------------------------------------------------------------------------- #
class TestSafeSpacing:
    def test_returns_catalog_min_spacing_for_known_art(self):
        # Long Grass has min_spacing_wu = 13.3 in the catalog.
        assert safe_spacing("Long Grass") == pytest.approx(13.3, abs=0.01)

    def test_falls_back_for_single_sample_decoration(self):
        # Marble Bench has only 1 sample → min_spacing_wu is None → fallback.
        sp = safe_spacing("Marble Bench")
        assert sp == 15.0  # _DEFAULT_FALLBACK_SPACING

    def test_falls_back_for_unsampled_decoration(self):
        # Fringe Moss has 0 samples → fallback.
        sp = safe_spacing("Fringe Moss")
        assert sp == 15.0

    def test_rejects_functional_decoration(self):
        with pytest.raises(ValueError, match="not in ART_TYPES"):
            safe_spacing("Stash")

    def test_rejects_unknown_name(self):
        with pytest.raises(ValueError, match="not in ART_TYPES"):
            safe_spacing("Nonexistent Decoration")


# --------------------------------------------------------------------------- #
# line
# --------------------------------------------------------------------------- #
class TestLine:
    def test_single_point_when_length_zero(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = line(100, 100, 100, 100, opts)
        assert len(out) == 1
        assert (out[0].x, out[0].y) == (100, 100)

    def test_endpoints_always_included(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = line(0, 0, 100, 0, opts, spacing=30.0)
        assert (out[0].x, out[0].y) == (0, 0)
        assert (out[-1].x, out[-1].y) == (100, 0)

    def test_intermediate_points_at_uniform_spacing(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = line(0, 0, 100, 0, opts, spacing=25.0)
        # length=100, spacing=25 → n=4 → 5 points
        assert len(out) == 5
        xs = [p.x for p in out]
        assert xs == [0, 25, 50, 75, 100]

    def test_respects_spacing_from_catalog(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = line(0, 0, 100, 0, opts)
        # Long Grass min spacing = 13.3 → floor(100/13.3)=7 → 8 points
        assert len(out) == 8

    def test_uses_decoration_hash(self):
        opts = PrimitiveOptions(decoration="Maraket Rubble")
        out = line(0, 0, 30, 0, opts, spacing=15.0)
        assert all(p.hash == KNOWN_HASHES["Maraket Rubble"] for p in out)
        assert all(p.name == "Maraket Rubble" for p in out)

    def test_diagonal_line(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = line(0, 0, 30, 40, opts, spacing=10.0)
        # length=50, spacing=10 → 6 points
        assert len(out) == 6
        # First and last are endpoints
        assert (out[0].x, out[0].y) == (0, 0)
        assert (out[-1].x, out[-1].y) == (30, 40)


# --------------------------------------------------------------------------- #
# polyline
# --------------------------------------------------------------------------- #
class TestPolyline:
    def test_empty_points(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        assert polyline([], opts) == []

    def test_single_point(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = polyline([(50, 50)], opts)
        assert len(out) == 1
        assert (out[0].x, out[0].y) == (50, 50)

    def test_two_points_one_segment(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = polyline([(0, 0), (30, 0)], opts, spacing=15.0)
        assert len(out) == 3  # 0, 15, 30

    def test_shared_vertex_not_duplicated(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = polyline([(0, 0), (30, 0), (60, 0)], opts, spacing=15.0)
        # First segment: 0, 15, 30 (3 pts)
        # Second segment: skip start (30), so 45, 60 (2 pts)
        # Total: 5 pts
        assert len(out) == 5
        xs = [p.x for p in out]
        assert xs == [0, 15, 30, 45, 60]


# --------------------------------------------------------------------------- #
# hollow_circle
# --------------------------------------------------------------------------- #
class TestHollowCircle:
    def test_minimum_8_points(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        # Very small radius → would compute n < 8, but we clamp at 8.
        out = hollow_circle(100, 100, 1.0, opts, spacing=100.0)
        assert len(out) >= 8

    def test_all_points_on_circle(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        cx, cy, r = 100, 100, 50
        out = hollow_circle(cx, cy, r, opts, spacing=10.0)
        for p in out:
            d = math.hypot(p.x - cx, p.y - cy)
            assert d == pytest.approx(r, abs=1.0)  # int rounding tolerance

    def test_point_count_matches_circumference_over_spacing(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        r = 30
        sp = 10.0
        expected_n = math.ceil(2 * math.pi * r / sp)
        out = hollow_circle(0, 0, r, opts, spacing=sp)
        assert len(out) == expected_n


# --------------------------------------------------------------------------- #
# filled_circle
# --------------------------------------------------------------------------- #
class TestFilledCircle:
    def test_includes_centre(self):
        opts = PrimitiveOptions(decoration="Coastal Pebble")
        out = filled_circle(100, 100, 20, opts, spacing=10.0)
        assert (100, 100) in [(p.x, p.y) for p in out]

    def test_no_points_outside_radius(self):
        opts = PrimitiveOptions(decoration="Coastal Pebble")
        cx, cy, r = 100, 100, 30
        out = filled_circle(cx, cy, r, opts, spacing=10.0)
        for p in out:
            d = math.hypot(p.x - cx, p.y - cy)
            assert d <= r + 1.0  # int rounding tolerance

    def test_more_points_than_hollow_circle(self):
        opts = PrimitiveOptions(decoration="Coastal Pebble")
        hollow = hollow_circle(0, 0, 30, opts, spacing=10.0)
        filled = filled_circle(0, 0, 30, opts, spacing=10.0)
        assert len(filled) > len(hollow)


# --------------------------------------------------------------------------- #
# s_snake
# --------------------------------------------------------------------------- #
class TestSSnake:
    def test_point_count_matches_height_over_spacing(self):
        opts = PrimitiveOptions(decoration="Sand Tussock")
        out = s_snake(0, 0, 60, 25, opts, spacing=15.0)
        # n = max(4, ceil(60/15)) = 4 → 5 points
        assert len(out) == 5

    def test_y_range_matches_height(self):
        opts = PrimitiveOptions(decoration="Sand Tussock")
        out = s_snake(0, 100, 60, 25, opts, spacing=15.0)
        ys = [p.y for p in out]
        assert min(ys) == pytest.approx(70, abs=1.0)  # 100 - 30
        assert max(ys) == pytest.approx(130, abs=1.0)  # 100 + 30

    def test_x_swings_within_amplitude(self):
        opts = PrimitiveOptions(decoration="Sand Tussock")
        out = s_snake(0, 100, 60, 25, opts, spacing=15.0)
        xs = [p.x for p in out]
        # amplitude = width/2 = 12.5
        assert min(xs) >= -13
        assert max(xs) <= 13

    def test_endpoints_at_centre_x(self):
        """S-shape ends at vertical centreline (sin(0)=sin(2π)=0)."""
        opts = PrimitiveOptions(decoration="Sand Tussock")
        out = s_snake(50, 100, 60, 25, opts, spacing=15.0)
        assert out[0].x == 50
        assert out[-1].x == 50


# --------------------------------------------------------------------------- #
# thick_line_with_contours
# --------------------------------------------------------------------------- #
class TestThickLineWithContours:
    def test_uses_both_decorations(self):
        out_opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill_opts = PrimitiveOptions(decoration="Coastal Pebble")
        out = thick_line_with_contours(
            0, 0, 50, 0, 14.0, out_opts, fill_opts, spacing=15.0,
        )
        names = {p.name for p in out}
        assert "Small Coastal Stone" in names
        assert "Coastal Pebble" in names

    def test_outline_points_form_perimeter(self):
        """Outline points should sit at distance ~half_t from either the
        centreline (long-side points) or the nearest endpoint (cap points).
        """
        out_opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill_opts = PrimitiveOptions(decoration="Coastal Pebble")
        x0, y0, x1, y1 = 100, 200, 150, 200
        thickness = 14.0
        out = thick_line_with_contours(
            x0, y0, x1, y1, thickness, out_opts, fill_opts, spacing=15.0,
        )
        outline = [p for p in out if p.name == "Small Coastal Stone"]
        half_t = thickness / 2.0
        for p in outline:
            # Distance from each endpoint.
            d_ep0 = math.hypot(p.x - x0, p.y - y0)
            d_ep1 = math.hypot(p.x - x1, p.y - y1)
            # If far from BOTH endpoints → long-side point → distance from
            # centreline (y=200) must equal half_t.
            if d_ep0 > half_t + 2 and d_ep1 > half_t + 2:
                d = abs(p.y - 200)
                assert d == pytest.approx(half_t, abs=1.5), \
                    f"Long-side point {p} not at half_t={half_t} from " \
                    f"centreline (got {d})"
            else:
                # Cap point → distance from nearest endpoint must equal half_t.
                d = min(d_ep0, d_ep1)
                assert d == pytest.approx(half_t, abs=1.5), \
                    f"Cap point {p} not at half_t={half_t} from endpoint " \
                    f"(got {d})"

    def test_no_duplicate_outline_placements(self):
        out_opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill_opts = PrimitiveOptions(decoration="Coastal Pebble")
        out = thick_line_with_contours(
            100, 200, 150, 200, 14.0, out_opts, fill_opts, spacing=15.0,
        )
        outline = [p for p in out if p.name == "Small Coastal Stone"]
        coords = [(p.x, p.y) for p in outline]
        assert len(coords) == len(set(coords)), \
            f"Duplicate outline coords: {coords}"

    def test_fill_points_strictly_inside_band(self):
        out_opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill_opts = PrimitiveOptions(decoration="Coastal Pebble")
        x0, y0, x1, y1 = 100, 200, 150, 200
        thickness = 30.0  # larger so we get interior fill points
        out = thick_line_with_contours(
            x0, y0, x1, y1, thickness, out_opts, fill_opts, spacing=10.0,
        )
        fill = [p for p in out if p.name == "Coastal Pebble"]
        half_t = thickness / 2.0
        for p in fill:
            # Y must be strictly between 200 - half_t and 200 + half_t
            assert abs(p.y - 200) < half_t - 1e-6, \
                f"Fill point {p} on outline boundary"
        assert len(fill) >= 1

    def test_degenerate_zero_length_returns_filled_circle(self):
        out_opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill_opts = PrimitiveOptions(decoration="Coastal Pebble")
        out = thick_line_with_contours(
            100, 200, 100, 200, 14.0, out_opts, fill_opts, spacing=15.0,
        )
        # Should not crash; produces at least one fill point at the centre.
        assert len(out) >= 1


# --------------------------------------------------------------------------- #
# center_composition
# --------------------------------------------------------------------------- #
class TestCenterComposition:
    def test_uses_only_known_art_decorations(self):
        out = center_composition(780, 657)
        for p in out:
            assert p.hash in KNOWN_HASHES.values()
            assert p.name in ART_TYPES

    def test_all_placements_within_canal_hideout_bounds(self):
        cx, cy = 780, 657
        out = center_composition(cx, cy)
        x_min, y_min, x_max, y_max = CANAL_HIDEOUT_BOUNDS
        for p in out:
            assert x_min <= p.x <= x_max, \
                f"{p.name} x={p.x} outside canvas"
            assert y_min <= p.y <= y_max, \
                f"{p.name} y={p.y} outside canvas"

    def test_no_duplicate_placements_per_decoration(self):
        from collections import Counter
        out = center_composition(780, 657)
        by_name: dict[str, list[tuple[int, int]]] = {}
        for p in out:
            by_name.setdefault(p.name, []).append((p.x, p.y))
        for name, coords in by_name.items():
            dupes = {k: v for k, v in Counter(coords).items() if v > 1}
            assert not dupes, f"{name} has duplicates: {dupes}"

    def test_contains_all_five_primitives(self):
        """The composition must include all five shape types."""
        out = center_composition(780, 657)
        names = {p.name for p in out}
        # Vertical lines = Long Grass (default)
        assert "Long Grass" in names
        # Hollow circle = Maraket Rubble (default)
        assert "Maraket Rubble" in names
        # Filled circle = Coastal Pebble (default)
        assert "Coastal Pebble" in names
        # S-snake = Maraket Rubble (default since 0.2.8, KI-14 fix)
        # — same decoration as hollow circle, distinguished by position.
        # Thick line outline = Small Coastal Stone (default)
        assert "Small Coastal Stone" in names
        # Thick line fill = Long Grass (default since 0.2.8, KI-15 fix)
        # — same decoration as vertical lines, distinguished by position.

    def test_ki14_s_snake_uses_maraket_rubble(self):
        """KI-14 (0.2.8): s_snake default must NOT be 'Sand Tussock'
        (too sparse) — must be 'Maraket Rubble' or another dense decoration."""
        out = center_composition(780, 657)
        # Sand Tussock must not appear anywhere in the default composition.
        names = {p.name for p in out}
        assert "Sand Tussock" not in names, (
            "KI-14 regression: Sand Tussock leaked back into the default "
            "composition. It is too sparse for S-snake at width=25."
        )

    def test_ki15_thick_line_fill_uses_long_grass(self):
        """KI-15 (0.2.8): thick_line fill must be 'Long Grass' (visible per
        KI-13 vertical lines), NOT 'Coastal Pebble' (invisible at thickness=14)."""
        out = center_composition(780, 657)
        # The thick line sits at the bottom row (y ≈ cy + 35 = 692),
        # spanning x ≈ cx + 5 .. cx + 55 = 785..835.
        # Find Long Grass placements in that band that are NOT vertical lines
        # (vertical lines sit at y in [cy-90, cy-10] = [670-90, 670-10]... wait
        # let me recompute: top_y = cy - 50 = 607, vl_y_top = top_y - 40 = 567,
        # vl_y_bot = top_y + 40 = 647. So vertical lines y in [567, 647].
        # Thick line at bot_y = cy + 35 = 692, thickness 28 → y in [678, 706].
        thick_band_long_grass = [
            p for p in out
            if p.name == "Long Grass" and 678 <= p.y <= 706
        ]
        assert len(thick_band_long_grass) >= 2, (
            f"KI-15 regression: expected ≥2 Long Grass fill points in the "
            f"thick line band (y∈[678, 706]), got {len(thick_band_long_grass)}. "
            f"Fill decoration may have reverted to Coastal Pebble."
        )

    def test_composition_is_relocatable(self):
        """Moving the centre moves all placements by the same delta (±1 wu
        tolerance for int rounding)."""
        out_a = center_composition(0, 0)
        out_b = center_composition(100, 50)
        assert len(out_a) == len(out_b)
        for a, b in zip(out_a, out_b, strict=True):
            assert abs((b.x - a.x) - 100) <= 1, \
                f"x delta mismatch: a={a}, b={b}"
            assert abs((b.y - a.y) - 50) <= 1, \
                f"y delta mismatch: a={a}, b={b}"

    def test_total_placement_count_in_expected_range(self):
        """Curated composition should produce 40-80 placements."""
        out = center_composition(780, 657)
        assert 40 <= len(out) <= 80, \
            f"Composition has {len(out)} placements — expected 40..80"


# --------------------------------------------------------------------------- #
# End-to-end: append to a Hideout, round-trip
# --------------------------------------------------------------------------- #
class TestEndToEnd:
    def test_primitives_can_be_appended_to_hideout(self):
        """A Hideout with appended primitives survives parse → write → parse."""
        import tempfile

        from hideout_art.writer import write_hideout
        h = Hideout(
            version=1,
            language="Russian",
            hideout_name="Test Canal",
            hideout_hash=60415,
            placements=[],
        )
        h.placements.extend(center_composition(780, 657))
        original_count = len(h)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".hideout", delete=False, encoding="utf-8",
        ) as f:
            tmp_path = Path(f.name)
        try:
            write_hideout(h, tmp_path)
            h2 = Hideout.from_file(tmp_path)
            assert len(h2) == original_count
            # Same set of (name, x, y) in source order.
            a = [(p.name, p.x, p.y) for p in h]
            b = [(p.name, p.x, p.y) for p in h2]
            assert a == b
        finally:
            tmp_path.unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# arc (0.2.8)
# --------------------------------------------------------------------------- #
class TestArc:
    def test_zero_sweep_returns_single_point(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = arc(100, 100, 30.0, 45.0, 45.0, opts, spacing=10.0)
        assert len(out) == 1
        # Point should sit at angle 45° from centre.
        px, py = out[0].x, out[0].y
        ang = math.degrees(math.atan2(py - 100, px - 100))
        assert abs(ang - 45.0) < 1.0

    def test_endpoints_always_included(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = arc(0, 0, 50.0, 0.0, 90.0, opts, spacing=100.0)
        # Even with huge spacing, n is clamped at >=2 → 3 points (0°, 45°, 90°).
        assert len(out) >= 3
        # First point ≈ (50, 0); last point ≈ (0, 50).
        assert abs(out[0].x - 50) <= 1 and abs(out[0].y - 0) <= 1
        assert abs(out[-1].x - 0) <= 1 and abs(out[-1].y - 50) <= 1

    def test_all_points_on_circle(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        cx, cy, r = 100, 100, 50
        out = arc(cx, cy, r, 0.0, 180.0, opts, spacing=10.0)
        for p in out:
            d = math.hypot(p.x - cx, p.y - cy)
            assert d == pytest.approx(r, abs=1.0)

    def test_negative_sweep_travels_clockwise(self):
        """end < start means clockwise (negative sweep)."""
        opts = PrimitiveOptions(decoration="Long Grass")
        out = arc(0, 0, 50.0, 90.0, 0.0, opts, spacing=10.0)
        # First point ≈ (0, 50) at 90°.
        assert abs(out[0].x - 0) <= 1 and abs(out[0].y - 50) <= 1
        # Last point ≈ (50, 0) at 0°.
        assert abs(out[-1].x - 50) <= 1 and abs(out[-1].y - 0) <= 1

    def test_full_circle_sweep(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = arc(0, 0, 30.0, 0.0, 360.0, opts, spacing=10.0)
        # Full circle ≈ 2π·30 ≈ 188 wu / 10 ≈ 19 segments → 20 points.
        assert len(out) >= 18
        # First and last point should be at the same place (start = end of full circle).
        assert abs(out[0].x - out[-1].x) <= 1
        assert abs(out[0].y - out[-1].y) <= 1


# --------------------------------------------------------------------------- #
# rectangle (0.2.8)
# --------------------------------------------------------------------------- #
class TestRectangle:
    def test_corners_included_once(self):
        opts = PrimitiveOptions(decoration="Maraket Rubble")
        out = rectangle(100, 200, 200, 240, opts, spacing=15.0)
        coords = [(p.x, p.y) for p in out]
        # Each corner appears exactly once.
        for corner in [(100, 200), (200, 200), (200, 240), (100, 240)]:
            assert coords.count(corner) == 1, \
                f"Corner {corner} appears {coords.count(corner)} times"

    def test_all_points_on_perimeter(self):
        opts = PrimitiveOptions(decoration="Maraket Rubble")
        x0, y0, x1, y1 = 100, 200, 200, 240
        out = rectangle(x0, y0, x1, y1, opts, spacing=15.0)
        for p in out:
            on_left = (p.x == x0 and y0 <= p.y <= y1)
            on_right = (p.x == x1 and y0 <= p.y <= y1)
            on_bottom = (p.y == y0 and x0 <= p.x <= x1)
            on_top = (p.y == y1 and x0 <= p.x <= x1)
            assert on_left or on_right or on_bottom or on_top, \
                f"Point {p} not on rectangle perimeter"

    def test_normalises_swapped_corners(self):
        opts = PrimitiveOptions(decoration="Maraket Rubble")
        a = rectangle(100, 200, 200, 240, opts, spacing=15.0)
        b = rectangle(200, 240, 100, 200, opts, spacing=15.0)
        assert {(p.x, p.y) for p in a} == {(p.x, p.y) for p in b}

    def test_no_duplicate_coords(self):
        opts = PrimitiveOptions(decoration="Maraket Rubble")
        out = rectangle(100, 200, 250, 240, opts, spacing=10.0)
        coords = [(p.x, p.y) for p in out]
        assert len(coords) == len(set(coords)), \
            f"Duplicate coords in rectangle: {coords}"


# --------------------------------------------------------------------------- #
# polygon (0.2.8)
# --------------------------------------------------------------------------- #
class TestPolygon:
    def test_rejects_fewer_than_three_sides(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        with pytest.raises(ValueError, match="n_sides >= 3"):
            polygon(0, 0, 30, 2, opts)
        with pytest.raises(ValueError, match="n_sides >= 3"):
            polygon(0, 0, 30, 1, opts)

    def test_vertices_on_circumcircle(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        cx, cy, r = 100, 100, 40
        out = polygon(cx, cy, r, 6, opts, spacing=100.0)  # huge spacing → only vertices
        # Hexagon with huge spacing: each side gets endpoints + 0 interior.
        # Polyline logic drops duplicate vertices, so we get exactly 6 unique vertices.
        unique = {(p.x, p.y) for p in out}
        assert len(unique) == 6
        for px, py in unique:
            d = math.hypot(px - cx, py - cy)
            assert d == pytest.approx(r, abs=1.0)

    def test_square_rotation_zero_has_vertex_on_x_axis(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = polygon(100, 100, 30, 4, opts, rotation_deg=0.0, spacing=100.0)
        unique = {(p.x, p.y) for p in out}
        # rotation_deg=0 → first vertex at (cx + r, cy) = (130, 100).
        assert (130, 100) in unique

    def test_triangle_vertex_count(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = polygon(0, 0, 30, 3, opts, spacing=100.0)
        unique = {(p.x, p.y) for p in out}
        assert len(unique) == 3

    def test_octagon_has_eight_vertices(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = polygon(0, 0, 30, 8, opts, spacing=100.0)
        unique = {(p.x, p.y) for p in out}
        assert len(unique) == 8


# --------------------------------------------------------------------------- #
# grid (0.2.8)
# --------------------------------------------------------------------------- #
class TestGrid:
    def test_total_count_matches_cols_times_rows(self):
        opts = PrimitiveOptions(decoration="Coastal Pebble")
        out = grid(100, 200, 200, 240, opts, cols=5, rows=3)
        assert len(out) == 5 * 3

    def test_border_grid_includes_corners(self):
        opts = PrimitiveOptions(decoration="Coastal Pebble")
        out = grid(100, 200, 200, 240, opts, cols=3, rows=2,
                   include_border=True)
        coords = {(p.x, p.y) for p in out}
        assert (100, 200) in coords
        assert (200, 200) in coords
        assert (100, 240) in coords
        assert (200, 240) in coords

    def test_centred_grid_excludes_border(self):
        """include_border=False → no point sits on the rectangle perimeter."""
        opts = PrimitiveOptions(decoration="Coastal Pebble")
        x0, y0, x1, y1 = 100, 200, 200, 240
        out = grid(x0, y0, x1, y1, opts, cols=3, rows=2,
                   include_border=False)
        for p in out:
            on_left = (p.x == x0)
            on_right = (p.x == x1)
            on_bottom = (p.y == y0)
            on_top = (p.y == y1)
            assert not (on_left or on_right or on_bottom or on_top), \
                f"Cell-centred point {p} on perimeter"

    def test_rejects_zero_cols_or_rows(self):
        opts = PrimitiveOptions(decoration="Coastal Pebble")
        with pytest.raises(ValueError, match="cols>=1 and rows>=1"):
            grid(100, 200, 200, 240, opts, cols=0, rows=3)
        with pytest.raises(ValueError, match="cols>=1 and rows>=1"):
            grid(100, 200, 200, 240, opts, cols=3, rows=0)

    def test_single_cell_grid_returns_one_point(self):
        opts = PrimitiveOptions(decoration="Coastal Pebble")
        out = grid(100, 200, 200, 240, opts, cols=1, rows=1)
        assert len(out) == 1
        # With cols=1, rows=1: x_steps=0, y_steps=0 → t=0/0 falls back to 0.0
        # → point at (x0, y0).
        assert (out[0].x, out[0].y) == (100, 200)

    def test_normalises_swapped_corners(self):
        opts = PrimitiveOptions(decoration="Coastal Pebble")
        a = grid(100, 200, 200, 240, opts, cols=3, rows=2)
        b = grid(200, 240, 100, 200, opts, cols=3, rows=2)
        assert {(p.x, p.y) for p in a} == {(p.x, p.y) for p in b}


# --------------------------------------------------------------------------- #
# Mosaic v2 / portrait-grade primitives (0.2.9)
# --------------------------------------------------------------------------- #
class TestBezierCurve:
    def test_endpoints_always_included(self):
        opts = PrimitiveOptions(decoration="Small Coastal Stone")
        out = bezier_curve((100, 200), (150, 250), (200, 200), opts)
        coords = [(p.x, p.y) for p in out]
        assert (100, 200) in coords
        assert (200, 200) in coords

    def test_curve_bulges_toward_control_point(self):
        """Quadratic Bezier with control above the chord must produce
        points whose max y is strictly above the chord y."""
        opts = PrimitiveOptions(decoration="Small Coastal Stone")
        # Chord from (0,0) to (100,0), control at (50, 80).
        out = bezier_curve((0, 0), (50, 80), (100, 0), opts,
                           spacing=10.0)
        ys = [p.y for p in out]
        # The curve should reach approximately y = 40 (half the control y)
        # at the midpoint — well above the chord y=0.
        assert max(ys) > 30, f"max y={max(ys)} — curve did not bulge upward"

    def test_degenerate_zero_length_returns_single_point(self):
        opts = PrimitiveOptions(decoration="Small Coastal Stone")
        out = bezier_curve((50, 50), (50, 50), (50, 50), opts)
        assert len(out) == 1
        assert (out[0].x, out[0].y) == (50, 50)

    def test_uses_only_known_art_decorations(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = bezier_curve((0, 0), (50, 30), (100, 0), opts)
        for p in out:
            assert p.name == "Long Grass"
            assert p.hash == KNOWN_HASHES["Long Grass"]
            assert p.name in ART_TYPES

    def test_no_duplicate_coords(self):
        opts = PrimitiveOptions(decoration="Small Coastal Stone")
        out = bezier_curve((0, 0), (40, 80), (80, 0), opts, spacing=8.0)
        coords = [(p.x, p.y) for p in out]
        assert len(coords) == len(set(coords)), \
            f"{len(coords) - len(set(coords))} duplicate coords"

    def test_spacing_override_controls_density(self):
        opts = PrimitiveOptions(decoration="Small Coastal Stone")
        sparse = bezier_curve((0, 0), (50, 80), (100, 0), opts, spacing=50.0)
        dense = bezier_curve((0, 0), (50, 80), (100, 0), opts, spacing=5.0)
        assert len(dense) > len(sparse) > 1


class TestThickRing:
    def test_rejects_negative_inner_r(self):
        opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill = PrimitiveOptions(decoration="Long Grass")
        with pytest.raises(ValueError, match="inner_r must be >= 0"):
            thick_ring(0, 0, -1, 10, opts, fill)

    def test_rejects_zero_outer_r(self):
        opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill = PrimitiveOptions(decoration="Long Grass")
        with pytest.raises(ValueError, match="outer_r must be > 0"):
            thick_ring(0, 0, 0, 0, opts, fill)

    def test_rejects_inner_r_greater_equal_outer_r(self):
        opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill = PrimitiveOptions(decoration="Long Grass")
        with pytest.raises(ValueError, match="inner_r .* must be < outer_r"):
            thick_ring(0, 0, 10, 10, opts, fill)
        with pytest.raises(ValueError, match="inner_r .* must be < outer_r"):
            thick_ring(0, 0, 15, 10, opts, fill)

    def test_produces_both_outline_and_fill(self):
        outline_opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill_opts = PrimitiveOptions(decoration="Long Grass")
        out = thick_ring(0, 0, 5, 15, outline_opts, fill_opts, spacing=5.0)
        names = {p.name for p in out}
        # Both decorations must appear.
        assert "Small Coastal Stone" in names
        assert "Long Grass" in names

    def test_inner_r_zero_degenerates_to_filled_circle_with_outline(self):
        """inner_r=0 → inner 'circle' collapses to a single centre point."""
        outline_opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill_opts = PrimitiveOptions(decoration="Long Grass")
        out = thick_ring(50, 50, 0, 10, outline_opts, fill_opts, spacing=5.0)
        # The centre (50, 50) must appear as an outline point.
        coords = [(p.x, p.y) for p in out]
        assert (50, 50) in coords

    def test_no_duplicate_coords(self):
        outline_opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill_opts = PrimitiveOptions(decoration="Long Grass")
        out = thick_ring(100, 100, 5, 15, outline_opts, fill_opts, spacing=5.0)
        coords = [(p.x, p.y) for p in out]
        assert len(coords) == len(set(coords))


class TestThickArc:
    def test_rejects_zero_or_negative_radius(self):
        opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill = PrimitiveOptions(decoration="Long Grass")
        with pytest.raises(ValueError, match="radius must be > 0"):
            thick_arc(0, 0, 0, 5, 0, 180, opts, fill)
        with pytest.raises(ValueError, match="radius must be > 0"):
            thick_arc(0, 0, -5, 5, 0, 180, opts, fill)

    def test_rejects_zero_or_negative_thickness(self):
        opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill = PrimitiveOptions(decoration="Long Grass")
        with pytest.raises(ValueError, match="thickness must be > 0"):
            thick_arc(0, 0, 10, 0, 0, 180, opts, fill)

    def test_produces_both_outline_and_fill(self):
        outline_opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill_opts = PrimitiveOptions(decoration="Long Grass")
        out = thick_arc(0, 0, 15, 6, 0, 180, outline_opts, fill_opts,
                        spacing=5.0)
        names = {p.name for p in out}
        assert "Small Coastal Stone" in names
        assert "Long Grass" in names

    def test_half_circle_arc_stays_in_upper_half_plane(self):
        """A 0..180° arc centred at origin sweeps the upper half plane:
        all produced points must have y >= 0 (within rounding tolerance)."""
        outline_opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill_opts = PrimitiveOptions(decoration="Long Grass")
        out = thick_arc(0, 0, 20, 6, 0, 180, outline_opts, fill_opts,
                        spacing=5.0)
        for p in out:
            # Allow tiny negative for numerical safety at the 0° and 180° endpoints.
            assert p.y >= -1, f"point {p} below x-axis (lower half plane)"

    def test_no_duplicate_coords(self):
        outline_opts = PrimitiveOptions(decoration="Small Coastal Stone")
        fill_opts = PrimitiveOptions(decoration="Long Grass")
        out = thick_arc(100, 100, 15, 6, 30, 150, outline_opts, fill_opts,
                        spacing=5.0)
        coords = [(p.x, p.y) for p in out]
        assert len(coords) == len(set(coords))


class TestCrosshatch:
    def test_returns_empty_for_zero_area_rectangle(self):
        opts = PrimitiveOptions(decoration="Seaweed")
        assert crosshatch(50, 50, 50, 50, opts) == []
        assert crosshatch(50, 50, 50, 100, opts) == []
        assert crosshatch(50, 50, 100, 50, opts) == []

    def test_all_points_inside_rectangle(self):
        opts = PrimitiveOptions(decoration="Seaweed")
        out = crosshatch(100, 200, 200, 240, opts, spacing=5.0)
        for p in out:
            assert 100 <= p.x <= 200, f"{p} x outside rect"
            assert 200 <= p.y <= 240, f"{p} y outside rect"

    def test_no_duplicate_coords(self):
        opts = PrimitiveOptions(decoration="Seaweed")
        out = crosshatch(0, 0, 50, 50, opts, spacing=5.0)
        coords = [(p.x, p.y) for p in out]
        assert len(coords) == len(set(coords)), \
            f"{len(coords) - len(set(coords))} duplicate coords"

    def test_bidirectional_has_more_points_than_unidirectional(self):
        opts = PrimitiveOptions(decoration="Seaweed")
        bi = crosshatch(0, 0, 50, 50, opts, spacing=5.0, bidirectional=True)
        uni = crosshatch(0, 0, 50, 50, opts, spacing=5.0, bidirectional=False)
        assert len(bi) > len(uni) > 0

    def test_normalises_swapped_corners(self):
        opts = PrimitiveOptions(decoration="Seaweed")
        a = crosshatch(0, 0, 50, 50, opts, spacing=5.0)
        b = crosshatch(50, 50, 0, 0, opts, spacing=5.0)
        assert {(p.x, p.y) for p in a} == {(p.x, p.y) for p in b}

    def test_angle_zero_produces_axis_aligned_grid(self):
        """angle_deg=0 + bidirectional → 0° + 90° = horizontal + vertical
        lines = an axis-aligned grid."""
        opts = PrimitiveOptions(decoration="Seaweed")
        out = crosshatch(0, 0, 50, 50, opts, spacing=10.0, angle_deg=0.0)
        # The intersection points (10, 10), (20, 20), etc. should all be present.
        # At least verify the structure: many points, all inside rect.
        assert len(out) > 10
        for p in out:
            assert 0 <= p.x <= 50 and 0 <= p.y <= 50

    def test_uses_only_known_art_decorations(self):
        opts = PrimitiveOptions(decoration="Long Grass")
        out = crosshatch(0, 0, 30, 30, opts)
        for p in out:
            assert p.name == "Long Grass"
            assert p.hash == KNOWN_HASHES["Long Grass"]


class TestMosaicComposition:
    def test_uses_only_known_art_decorations(self):
        out = mosaic_composition(780, 657)
        for p in out:
            assert p.hash in KNOWN_HASHES.values()
            assert p.name in ART_TYPES

    def test_all_placements_within_canal_hideout_bounds(self):
        cx, cy = 780, 657
        out = mosaic_composition(cx, cy)
        x_min, y_min, x_max, y_max = CANAL_HIDEOUT_BOUNDS
        for p in out:
            assert x_min <= p.x <= x_max, \
                f"{p.name} x={p.x} outside canvas"
            assert y_min <= p.y <= y_max, \
                f"{p.name} y={p.y} outside canvas"

    def test_no_duplicate_placements_per_decoration(self):
        from collections import Counter
        out = mosaic_composition(780, 657)
        by_name: dict[str, list[tuple[int, int]]] = {}
        for p in out:
            by_name.setdefault(p.name, []).append((p.x, p.y))
        for name, coords in by_name.items():
            dupes = {k: v for k, v in Counter(coords).items() if v > 1}
            assert not dupes, f"{name} has duplicates: {dupes}"

    def test_does_not_overlap_center_composition(self):
        """The mosaic zone MUST be strictly separated from
        center_composition so KI-14/15 re-verification is not confounded."""
        cc = center_composition(780, 657)
        mc = mosaic_composition(780, 657)
        cc_keys = {(p.x, p.y) for p in cc}
        overlap = [p for p in mc if (p.x, p.y) in cc_keys]
        assert not overlap, \
            f"mosaic_composition overlaps center_composition at {len(overlap)} points"

    def test_contains_all_four_new_primitives_decorations(self):
        """The composition must use decorations from all four new shapes:
        bezier (Small Coastal Stone), ring_fill (Cave Coral),
        arc_fill (Long Grass), hatch (Seaweed)."""
        out = mosaic_composition(780, 657)
        names = {p.name for p in out}
        # Bezier + ring_outline + arc_outline all use Small Coastal Stone.
        assert "Small Coastal Stone" in names
        # Ring fill uses Cave Coral.
        assert "Cave Coral" in names
        # Arc fill uses Long Grass.
        assert "Long Grass" in names
        # Hatch uses Seaweed.
        assert "Seaweed" in names

    def test_zone_is_below_center_composition(self):
        """All mosaic_composition placements must have y > max y of
        center_composition (zone is in the free space below)."""
        cc = center_composition(780, 657)
        mc = mosaic_composition(780, 657)
        cc_max_y = max(p.y for p in cc)
        for p in mc:
            assert p.y > cc_max_y, \
                f"mosaic point {p} not below center_composition (max_y={cc_max_y})"
