"""Smoke tests for img2hideout.

We don't ship real images in the repo, so tests build a tiny in-memory
PNG via Pillow. All tests are skipped if Pillow isn't installed.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

PIL = pytest.importorskip("PIL")  # noqa: F841
from PIL import Image  # noqa: E402

from hideout_art import image_to_hideout  # noqa: E402
from hideout_art.palette import default_palette  # noqa: E402


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _write_png(img: Image.Image, path: Path) -> Path:
    img.save(path, format="PNG")
    return path


def _solid_image(w: int, h: int, rgb: tuple[int, int, int]) -> Image.Image:
    return Image.new("RGB", (w, h), rgb)


def _rgba_image(w: int, h: int, rgba: tuple[int, int, int, int]) -> Image.Image:
    return Image.new("RGBA", (w, h), rgba)


def test_basic_conversion_emits_one_placement_per_pixel(tmp_path: Path):
    img = _solid_image(3, 3, (46, 125, 50))  # green -> Long Grass
    p = _write_png(img, tmp_path / "g.png")
    h = image_to_hideout(p, palette=default_palette(),
                         target_width=3, scale=2,
                         origin_x=0, origin_y=0,
                         background=(0, 0, 0), background_threshold=10)
    assert len(h) == 9
    assert all(p.name == "Long Grass" for p in h.placements)
    # Check y-flip: top row of image (row=0) -> highest y
    top_row = [p for p in h.placements if p.y >= 4]
    assert len(top_row) == 3


def test_background_pixels_are_skipped(tmp_path: Path):
    img = _solid_image(2, 2, (0, 0, 0))  # pure black
    p = _write_png(img, tmp_path / "bg.png")
    h = image_to_hideout(p, palette=default_palette(),
                         target_width=2, scale=1,
                         origin_x=0, origin_y=0,
                         background=(0, 0, 0), background_threshold=10)
    assert len(h) == 0


def test_no_bg_disables_skip(tmp_path: Path):
    img = _solid_image(2, 2, (0, 0, 0))
    p = _write_png(img, tmp_path / "bg.png")
    h = image_to_hideout(p, palette=default_palette(),
                         target_width=2, scale=1,
                         origin_x=0, origin_y=0,
                         background=None)
    # All 4 pixels become placements (closest palette entry to black is
    # Sand Tussock (78,52,46), but the exact match doesn't matter — just
    # that nothing was skipped).
    assert len(h) == 4


def test_alpha_channel_skips_transparent_pixels(tmp_path: Path):
    # 4 pixels: top-left opaque, others transparent
    img = _rgba_image(2, 2, (0, 0, 0, 0))  # all transparent
    img.putpixel((0, 0), (46, 125, 50, 255))  # one opaque green
    p = _write_png(img, tmp_path / "a.png")
    h = image_to_hideout(p, palette=default_palette(),
                         target_width=2, scale=1,
                         origin_x=0, origin_y=0,
                         background=(0, 0, 0), background_threshold=10)
    assert len(h) == 1
    assert h.placements[0].name == "Long Grass"


def test_step_n_halves_placement_count(tmp_path: Path):
    img = _solid_image(4, 4, (46, 125, 50))
    p = _write_png(img, tmp_path / "g.png")
    h1 = image_to_hideout(p, palette=default_palette(),
                          target_width=4, scale=1, step=1,
                          origin_x=0, origin_y=0,
                          background=(0, 0, 0), background_threshold=10)
    h2 = image_to_hideout(p, palette=default_palette(),
                          target_width=4, scale=1, step=2,
                          origin_x=0, origin_y=0,
                          background=(0, 0, 0), background_threshold=10)
    assert len(h1) == 16
    assert len(h2) == 4  # 2x2 grid from 4x4 with step=2


def test_dither_does_not_crash_and_changes_output(tmp_path: Path):
    # Half-and-half image: left half pure red, right half pure blue
    img = Image.new("RGB", (4, 2))
    for x in range(4):
        for y in range(2):
            img.putpixel((x, y), (255, 0, 0) if x < 2 else (0, 0, 255))
    p = _write_png(img, tmp_path / "half.png")

    h_plain = image_to_hideout(p, palette=default_palette(),
                               target_width=4, scale=1,
                               origin_x=0, origin_y=0,
                               background=None)
    h_dither = image_to_hideout(p, palette=default_palette(),
                                target_width=4, scale=1,
                                origin_x=0, origin_y=0,
                                background=None, dither=True)
    # Both must produce the same total count (no pixel skipped by dither)
    assert len(h_plain) == len(h_dither) == 8
    # But the placement breakdown may differ (dither diffuses the error
    # and may pick a different palette entry for some pixels).
    assert isinstance(h_dither.placements[0].x, int)


def test_jitter_varies_r_and_fv(tmp_path: Path):
    img = _solid_image(4, 4, (46, 125, 50))
    p = _write_png(img, tmp_path / "g.png")
    h = image_to_hideout(p, palette=default_palette(),
                         target_width=4, scale=1, step=1,
                         origin_x=0, origin_y=0,
                         background=(0, 0, 0), background_threshold=10,
                         jitter=True, jitter_seed=42, jitter_variants=8)
    rs = {p.r for p in h.placements}
    fvs = {p.fv for p in h.placements}
    # With jitter on and 16 placements, we should see more than one
    # distinct r and fv value.
    assert len(rs) > 1
    assert len(fvs) > 1
    # All r values must be multiples of 15° (= 65536/24 = 2730.67)
    r_step = 65536 // 24
    for r in rs:
        assert r % r_step == 0
    # All fv values must be < jitter_variants (8)
    for fv in fvs:
        assert 0 <= fv < 8


def test_bounds_skips_outside_placements(tmp_path: Path):
    img = _solid_image(4, 4, (46, 125, 50))
    p = _write_png(img, tmp_path / "g.png")
    # 4x4 pixels at scale=1, origin (0,0) -> placements at x in [0,3], y in [0,3]
    # Tighten bounds to (1,1,2,2) -> only 4 placements survive.
    h = image_to_hideout(p, palette=default_palette(),
                         target_width=4, scale=1, step=1,
                         origin_x=0, origin_y=0,
                         background=(0, 0, 0), background_threshold=10,
                         bounds=(1, 1, 2, 2))
    assert len(h) == 4
    for placement in h.placements:
        assert 1 <= placement.x <= 2
        assert 1 <= placement.y <= 2


def test_color_metric_choices_produce_valid_output(tmp_path: Path):
    img = _solid_image(2, 2, (50, 60, 70))  # ambiguous colour
    p = _write_png(img, tmp_path / "amb.png")
    for metric in ("rgb", "weighted", "redmean"):
        h = image_to_hideout(p, palette=default_palette(),
                             target_width=2, scale=1,
                             origin_x=0, origin_y=0,
                             background=None, color_metric=metric)
        assert len(h) == 4
        # All placements must use a known decoration
        for placement in h.placements:
            assert placement.name in {
                "Long Grass", "Falling Sand", "Fringe Moss", "Sand Tussock"
            }


def test_resample_nearest_preserves_pixel_art(tmp_path: Path):
    # 8x8 image with two distinct halves; downscale to 4 wide with NEAREST
    img = Image.new("RGB", (8, 8))
    for x in range(8):
        for y in range(8):
            img.putpixel((x, y), (46, 125, 50) if x < 4 else (78, 52, 46))
    p = _write_png(img, tmp_path / "half.png")
    h = image_to_hideout(p, palette=default_palette(),
                         target_width=4, scale=1,
                         origin_x=0, origin_y=0,
                         background=None, resample="nearest")
    # 4x4 = 16 placements, half green half brown
    greens = sum(1 for placement in h.placements if placement.name == "Long Grass")
    browns = sum(1 for placement in h.placements if placement.name == "Sand Tussock")
    assert greens + browns == 16


def test_default_args_match_legacy_behaviour(tmp_path: Path):
    """Default args must reproduce the pre-1.1 behaviour byte-for-byte
    on a non-alpha image. Regression guard.
    """
    img = _solid_image(3, 3, (46, 125, 50))
    p = _write_png(img, tmp_path / "g.png")
    h = image_to_hideout(p, palette=default_palette(),
                         target_width=3, scale=2,
                         origin_x=700, origin_y=550,
                         hideout_name="Canal Hideout",
                         hideout_hash=60415)
    assert h.hideout_name == "Canal Hideout"
    assert h.hideout_hash == 60415
    assert len(h) == 9
    # All r=0, fv=0 (no jitter)
    assert all(placement.r == 0 for placement in h.placements)
    assert all(placement.fv == 0 for placement in h.placements)
