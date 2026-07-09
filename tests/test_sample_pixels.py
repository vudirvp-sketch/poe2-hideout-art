"""Tests for scripts/sample_pixels.py (0.2.6) — pixel-sampling calibration.

Covers the pure-Python parts of the script (calibration math, RGB
statistics, aggregate median) without invoking PIL/Pillow. The full
pipeline is exercised by running scripts/sample_all.py manually —
those integration results live in scripts/sampled_all.json (gitignored).

Tests here:
- WorldToPixel affine transform — auto and manual modes.
- calibrate_manual least-squares fit residual.
- rgb_stats median / quartile math.
- aggregate_medians n==2 mean vs n>=3 nearest-rank behaviour.
- sample_placement_pixels clamps to image bounds.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow importing the script without installing the package
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# sample_pixels.py imports from hideout_art, which is fine because the
# src/ path is added by conftest.py or already on sys.path.
import sample_pixels  # noqa: E402
from sample_pixels import (  # noqa: E402
    WorldToPixel,
    aggregate_medians,
    calibrate_auto,
    calibrate_manual,
    rgb_stats,
    sample_placement_pixels,
)


# --------------------------------------------------------------------------- #
# Auto-calibration
# --------------------------------------------------------------------------- #
def test_calibrate_auto_canal_bbox():
    """Auto-calibration maps CANAL_HIDEOUT_BOUNDS onto screenshot with margins."""
    # Image 1000x800, default margins 5%/5%/5%/20%
    t = calibrate_auto(image_size=(1000, 800),
                       world_bbox=(700, 540, 860, 775))
    assert t.method == "auto"
    # scale_x = (0.95 - 0.05) * 1000 / (860 - 700) = 900 / 160 = 5.625
    assert abs(t.a - 5.625) < 0.01
    # Y axis flipped: scale_y is negative
    assert t.c < 0
    # World (700, 775) → pixel (50, 40) (top-left corner of canvas)
    px, py = t.world_to_pixel(700, 775)
    assert abs(px - 50) < 0.5
    assert abs(py - 40) < 0.5


def test_calibrate_auto_functional_bbox_captures_anchors_outside_canal():
    """The 'functional' world bbox option in main() must include anchors
    at x<700 (Ange, Reforging Bench, etc.). We verify via calibrate_auto
    with an explicit bbox that includes those anchors."""
    # Functional bbox = (655, 514, 860, 791) per our run
    t = calibrate_auto(image_size=(1597, 1069),
                       world_bbox=(655, 514, 860, 791))
    # Stash (811, 519) must map inside the image
    px, py = t.world_to_pixel(811, 519)
    assert 0 <= px < 1597
    assert 0 <= py < 1069
    # Ange (660, 666) must also map inside the image (would be outside
    # with the canal bbox because Ange.x < 700)
    px2, py2 = t.world_to_pixel(660, 666)
    assert 0 <= px2 < 1597
    assert 0 <= py2 < 1069


# --------------------------------------------------------------------------- #
# Manual calibration
# --------------------------------------------------------------------------- #
def test_calibrate_manual_two_anchors_exact_fit():
    """With 2 anchors and no noise, the affine fit must be exact (residual=0)."""
    # Build a known transform: px = 2 * wx + 100, py = -3 * wy + 200
    anchors = [
        {"world": [10, 20], "pixel": [120, 140], "name": "a"},
        {"world": [30, 40], "pixel": [160, 80],  "name": "b"},
    ]
    t = calibrate_manual(anchors)
    assert t.method == "manual"
    assert t.n_anchors == 2
    # Residual is None for n<3 (not enough points to compute meaningful RMS)
    assert t.residual_px is None
    assert abs(t.a - 2.0) < 1e-6
    assert abs(t.b - 100.0) < 1e-6
    assert abs(t.c - (-3.0)) < 1e-6
    assert abs(t.d - 200.0) < 1e-6


def test_calibrate_manual_three_anchors_reports_residual():
    """With >=3 anchors, residual is computed (RMS of fit error)."""
    # Three points with a small perturbation on the third
    anchors = [
        {"world": [0, 0],   "pixel": [0, 0],   "name": "a"},
        {"world": [10, 10], "pixel": [20, 30], "name": "b"},
        {"world": [20, 20], "pixel": [40, 62], "name": "c"},  # 2 px off on Y
    ]
    t = calibrate_manual(anchors)
    assert t.n_anchors == 3
    assert t.residual_px is not None
    assert t.residual_px > 0  # non-zero due to perturbation
    assert t.residual_px < 5  # but small


def test_calibrate_manual_rejects_too_few_anchors():
    """Less than 2 anchors must raise."""
    with pytest.raises(ValueError, match=">= 2 anchors"):
        calibrate_manual([{"world": [1, 2], "pixel": [3, 4], "name": "a"}])


# --------------------------------------------------------------------------- #
# RGB statistics
# --------------------------------------------------------------------------- #
def test_rgb_stats_empty():
    """Empty pixel list yields None for all stats."""
    s = rgb_stats([])
    assert s["median_rgb"] is None
    assert s["n_pixels_sampled"] == 0


def test_rgb_stats_single_pixel():
    """Single pixel: median = mean = p25 = p75 = that pixel."""
    s = rgb_stats([(100, 150, 200)])
    assert s["median_rgb"] == [100, 150, 200]
    assert s["mean_rgb"] == [100, 150, 200]
    assert s["p25_rgb"] == [100, 150, 200]
    assert s["p75_rgb"] == [100, 150, 200]
    assert s["n_pixels_sampled"] == 1


def test_rgb_stats_quartiles():
    """Quartiles computed via nearest-rank on a 4-pixel list."""
    # R sorted: 10, 20, 30, 40
    # n=4, p25 idx = round(0.25 * 3) = 1 → 20
    # p50 idx = round(0.5 * 3) = 2 → 30 (rounded 1.5 = 2)
    # p75 idx = round(0.75 * 3) = 2 → 30 (rounded 2.25 = 2)
    pixels = [(10, 0, 0), (20, 0, 0), (30, 0, 0), (40, 0, 0)]
    s = rgb_stats(pixels)
    assert s["median_rgb"][0] == 30
    assert s["mean_rgb"][0] == 25  # (10+20+30+40)/4


# --------------------------------------------------------------------------- #
# Aggregate medians
# --------------------------------------------------------------------------- #
def test_aggregate_medians_n1():
    """n==1 returns the single value."""
    assert aggregate_medians([[10, 20, 30]]) == [10, 20, 30]


def test_aggregate_medians_n2_returns_mean():
    """n==2 returns the MEAN of the two values (not the larger)."""
    result = aggregate_medians([[10, 100, 200], [30, 60, 80]])
    assert result == [20, 80, 140]  # mean of each channel


def test_aggregate_medians_n3_returns_middle():
    """n==3 returns the middle element of the sorted list (nearest-rank)."""
    # R sorted: 10, 20, 30 → mid=1 → 20
    # G sorted: 60, 100, 200 → mid=1 → 100
    # B sorted: 80, 80, 200 → mid=1 → 80
    result = aggregate_medians([[30, 200, 200], [10, 60, 80], [20, 100, 80]])
    assert result == [20, 100, 80]


def test_aggregate_medians_empty():
    """Empty input returns [0,0,0]."""
    assert aggregate_medians([]) == [0, 0, 0]


# --------------------------------------------------------------------------- #
# sample_placement_pixels — bounds clamping
# --------------------------------------------------------------------------- #
def test_sample_placement_pixels_clamps_to_image():
    """Sampling window centered outside image bounds returns empty or
    partial pixel list (no IndexError)."""
    from PIL import Image
    img = Image.new("RGB", (100, 100), (50, 100, 150))
    # Centered at (-10, -10) with radius 5 → entirely outside, should
    # return [] without raising.
    pixels, n = sample_placement_pixels(img, -10, -10, 5)
    assert n == 0
    assert pixels == []


def test_sample_placement_pixels_full_window_inside():
    """Sampling window fully inside the image returns all pixels in circle."""
    from PIL import Image
    img = Image.new("RGB", (100, 100), (50, 100, 150))
    # Center at (50, 50) with radius 5 → ~81 pixels (circle area)
    pixels, n = sample_placement_pixels(img, 50, 50, 5)
    assert n > 50  # close to π * 5² ≈ 78
    assert n < 121  # less than (2*5+1)² = 121 (bounding box)
    # All pixels are the constant fill colour
    assert all(p == (50, 100, 150) for p in pixels)


def test_sample_placement_pixels_partial_window_at_edge():
    """Sampling window half outside image returns partial pixels."""
    from PIL import Image
    img = Image.new("RGB", (100, 100), (50, 100, 150))
    # Center at (0, 50) with radius 5 → only right half of circle inside
    pixels, n = sample_placement_pixels(img, 0, 50, 5)
    assert n > 0
    assert n < 50  # less than half of full circle


# --------------------------------------------------------------------------- #
# WorldToPixel transform
# --------------------------------------------------------------------------- #
def test_world_to_pixel_transform_round_trip():
    """world_to_pixel is deterministic for fixed a, b, c, d."""
    t = WorldToPixel(a=2.0, b=100.0, c=-3.0, d=200.0, method="manual")
    # wx=50, wy=10 → px = 2*50 + 100 = 200; py = -3*10 + 200 = 170
    px, py = t.world_to_pixel(50, 10)
    assert px == 200
    assert py == 170


def test_world_dist_to_pixel_uses_scale_x():
    """Distance conversion uses |a| (scale_x), not scale_y (which may differ)."""
    t = WorldToPixel(a=2.0, b=0, c=-3.0, d=0, method="manual")
    # 10 wu * 2 px/wu = 20 px
    assert t.world_dist_to_pixel(10) == 20


def test_to_dict_includes_all_fields():
    """WorldToPixel.to_dict() returns all calibration metadata."""
    t = WorldToPixel(a=2.0, b=100.0, c=-3.0, d=200.0, method="manual",
                     residual_px=1.5, n_anchors=3)
    d = t.to_dict()
    assert d["method"] == "manual"
    assert d["a_scale_x"] == 2.0
    assert d["b_offset_x"] == 100.0
    assert d["c_scale_y"] == -3.0
    assert d["d_offset_y"] == 200.0
    assert d["residual_px"] == 1.5
    assert d["n_anchors"] == 3


# --------------------------------------------------------------------------- #
# Module-level sanity
# --------------------------------------------------------------------------- #
def test_sample_pixels_module_imports():
    """sample_pixels module can be imported — verifies all top-level
    dependencies (PIL, hideout_art) are available."""
    assert hasattr(sample_pixels, "main")
    assert hasattr(sample_pixels, "calibrate_auto")
    assert hasattr(sample_pixels, "calibrate_manual")
    assert hasattr(sample_pixels, "sample_placement_pixels")
    assert hasattr(sample_pixels, "rgb_stats")
    assert hasattr(sample_pixels, "aggregate_medians")
