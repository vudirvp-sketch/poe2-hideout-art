"""Geometric transforms on Hideout compositions.

All transforms mutate the Hideout in place and return it for chaining.
Rotation maths are kept simple — PoE2's ``r`` is an unsigned 16-bit
angle, so we modulo after every arithmetic op to stay in range.
"""

from __future__ import annotations

import math

from .constants import ROTATION_MODULUS
from .parser import Hideout, Placement


def _normalise_r(r: int) -> int:
    """Bring an ``r`` value back into [0, ROTATION_MODULUS)."""
    return int(r) % ROTATION_MODULUS


def shift(
    h: Hideout, dx: int = 0, dy: int = 0, art_only: bool = False
) -> Hideout:
    """Translate every placement by (dx, dy)."""
    for p in h.placements:
        if art_only and not p.is_art:
            continue
        p.x += dx
        p.y += dy
    return h


def rotate(
    h: Hideout,
    degrees: float,
    cx: int | None = None,
    cy: int | None = None,
    art_only: bool = False,
) -> Hideout:
    """Rotate the composition by ``degrees`` around (cx, cy).

    If ``cx``/``cy`` are not given, the centroid of the (filtered)
    placements is used as the pivot. Each placement's own ``r`` field
    is updated to reflect the rotated orientation.
    """
    items = [p for p in h.placements if not art_only or p.is_art]
    if not items:
        return h

    if cx is None or cy is None:
        cx = sum(p.x for p in items) // len(items) if cx is None else cx
        cy = sum(p.y for p in items) // len(items) if cy is None else cy

    theta = math.radians(degrees)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    delta_r = int((degrees / 360.0) * ROTATION_MODULUS)

    for p in items:
        dx = p.x - cx
        dy = p.y - cy
        # Standard rotation. Note: PoE2's y grows upward, so positive
        # angles are counter-clockwise when viewed top-down.
        p.x = int(round(cx + dx * cos_t - dy * sin_t))
        p.y = int(round(cy + dx * sin_t + dy * cos_t))
        p.r = _normalise_r(p.r + delta_r)

    return h


def mirror_x(
    h: Hideout, axis: int | None = None, art_only: bool = False
) -> Hideout:
    """Flip horizontally around x = ``axis`` (defaults to centroid x)."""
    items = [p for p in h.placements if not art_only or p.is_art]
    if not items:
        return h

    if axis is None:
        axis = sum(p.x for p in items) // len(items)

    for p in items:
        p.x = 2 * axis - p.x
        # Toggle the flip_x bit of fv
        p.fv ^= 0x80
        # A horizontal mirror also rotates by 180° to keep the
        # decoration oriented consistently — empirically this matches
        # how the in-game mirror behaves on tested decorations.
        p.r = _normalise_r(ROTATION_MODULUS - p.r)

    return h


def mirror_y(
    h: Hideout, axis: int | None = None, art_only: bool = False
) -> Hideout:
    """Flip vertically around y = ``axis`` (defaults to centroid y)."""
    items = [p for p in h.placements if not art_only or p.is_art]
    if not items:
        return h

    if axis is None:
        axis = sum(p.y for p in items) // len(items)

    for p in items:
        p.y = 2 * axis - p.y
        # Vertical mirror = horizontal mirror + 180° rotation
        p.fv ^= 0x80
        p.r = _normalise_r(ROTATION_MODULUS - p.r)
        p.r = _normalise_r(p.r + ROTATION_MODULUS // 2)

    return h


# ---------------------------------------------------------------------- #
# Attach as Hideout methods, so the API is symmetric with `shift`.
# ---------------------------------------------------------------------- #
from .parser import Hideout as _H  # noqa: E402


def _shift(self, dx=0, dy=0, art_only=False):
    return shift(self, dx, dy, art_only=art_only)


def _rotate(self, degrees, cx=None, cy=None, art_only=False):
    return rotate(self, degrees, cx=cx, cy=cy, art_only=art_only)


def _mirror_x(self, axis=None, art_only=False):
    return mirror_x(self, axis=axis, art_only=art_only)


def _mirror_y(self, axis=None, art_only=False):
    return mirror_y(self, axis=axis, art_only=art_only)


def _recombine(self, *others, offsets=None):
    return recombine(self, *others, offsets=offsets)


_H.shift = _shift            # type: ignore[attr-defined]
_H.rotate = _rotate          # type: ignore[attr-defined]
_H.mirror_x = _mirror_x      # type: ignore[attr-defined]
_H.mirror_y = _mirror_y      # type: ignore[attr-defined]
_H.recombine = _recombine    # type: ignore[attr-defined]


def recombine(
    *hideouts: Hideout,
    offsets: list[tuple[int, int]] | None = None,
) -> Hideout:
    """Combine multiple hideouts into one.

    Each hideout's placements are appended, optionally translated by an
    (dx, dy) offset. The first hideout's header is used for the result.
    """
    if not hideouts:
        raise ValueError("recombine() requires at least one hideout")

    base = hideouts[0]
    result = Hideout(
        version=base.version,
        language=base.language,
        hideout_name=base.hideout_name,
        hideout_hash=base.hideout_hash,
        placements=[],
    )

    if offsets is None:
        offsets = [(0, 0)] * len(hideouts)
    if len(offsets) != len(hideouts):
        raise ValueError("offsets length must match hideouts length")

    for h, (dx, dy) in zip(hideouts, offsets, strict=True):
        for p in h.placements:
            result.placements.append(
                Placement(
                    name=p.name,
                    hash=p.hash,
                    x=p.x + dx,
                    y=p.y + dy,
                    r=p.r,
                    fv=p.fv,
                )
            )
    return result
