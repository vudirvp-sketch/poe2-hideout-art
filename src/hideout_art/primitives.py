"""Drawing primitives built from art-layer decorations.

This module is the foundation of the "drawing primitives из декораций" epic
flagged in ``STATUS.md``. Each primitive returns a list of
:class:`~hideout_art.parser.Placement` objects, which the caller can append
to an existing :class:`~hideout_art.parser.Hideout`.

Why this exists
---------------
``img2hideout`` rasterises a PNG — it is great for photographs but poor for
synthetic geometry: a hollow circle in the source PNG becomes a noisy dot
cloud after palette quantisation. This module draws geometric shapes
*directly* in world coordinates, so each shape is clean and recognisable
in-game.

Design rules (do not violate)
------------------------------
1. Every decoration used MUST be in :data:`~hideout_art.constants.ART_TYPES`
   and in :data:`~hideout_art.constants.KNOWN_HASHES`. Never invent hashes.
2. Spacing between same-hash placements MUST respect
   :data:`~hideout_art.constants.DECORATION_FOOTPRINT_CATALOG` (use
   ``min_spacing_wu`` as the lower bound). Use :func:`safe_spacing` to look
   it up.
3. All coordinates are integers (the writer emits them as-is).
4. ``r`` and ``fv`` default to 0; callers may override for rotation/variant.
5. Primitives NEVER mutate the input Hideout — they return fresh lists.
   The caller decides where to splice the result.

Shapes
------
* :func:`line` — straight line between two points.
* :func:`polyline` — chain of segments (used by S-snake).
* :func:`hollow_circle` — points on a circle perimeter.
* :func:`filled_circle` — points in a disk.
* :func:`s_snake` — sinusoidal vertical S-shape.
* :func:`thick_line_with_contours` — outline + fill thick band.

See ``scripts/draw_primitives.py`` for a CLI that injects all five into the
centre of an existing ``.hideout`` file.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .constants import (
    ART_TYPES,
    DECORATION_FOOTPRINT_CATALOG,
    KNOWN_HASHES,
)
from .parser import Placement

# When a decoration has no measured min_spacing_wu (single/none confidence),
# fall back to the default tile size as a safe lower bound.
_DEFAULT_FALLBACK_SPACING: int = 15


@dataclass(frozen=True)
class PrimitiveOptions:
    """Tunables shared by all primitives.

    Attributes
    ----------
    decoration:
        Name of the art decoration to use (must be in ``ART_TYPES``).
    r, fv:
        Rotation and flag/variant passed through to every Placement.
    spacing_override:
        If set, overrides the catalog's safe spacing. Useful when stacking
        multiple primitives of the same decoration type in a tight area.
    """

    decoration: str
    r: int = 0
    fv: int = 0
    spacing_override: float | None = None


def safe_spacing(decoration: str) -> float:
    """Return the safe placement spacing (in world units) for a decoration.

    Uses ``min_spacing_wu`` from :data:`DECORATION_FOOTPRINT_CATALOG` when
    available; otherwise falls back to ``_DEFAULT_FALLBACK_SPACING``.

    Raises
    ------
    ValueError
        If ``decoration`` is not in :data:`ART_TYPES` or not in
        :data:`KNOWN_HASHES`.
    """
    if decoration not in ART_TYPES:
        raise ValueError(
            f"{decoration!r} is not in ART_TYPES — only art decorations "
            "may be used by primitives."
        )
    if decoration not in KNOWN_HASHES:
        raise ValueError(
            f"{decoration!r} is in ART_TYPES but missing from KNOWN_HASHES "
            "— never invent hashes; register the decoration first."
        )
    catalog = DECORATION_FOOTPRINT_CATALOG.get(decoration)
    if catalog is None or catalog.min_spacing_wu is None:
        return float(_DEFAULT_FALLBACK_SPACING)
    return float(catalog.min_spacing_wu)


def _resolve_spacing(opts: PrimitiveOptions) -> float:
    if opts.spacing_override is not None:
        return float(opts.spacing_override)
    return safe_spacing(opts.decoration)


def _make_placement(x: float, y: float, opts: PrimitiveOptions) -> Placement:
    """Build a Placement, rounding coords to int and resolving the hash."""
    return Placement(
        name=opts.decoration,
        hash=KNOWN_HASHES[opts.decoration],
        x=int(round(x)),
        y=int(round(y)),
        r=opts.r,
        fv=opts.fv,
    )


# --------------------------------------------------------------------------- #
# Primitive shapes
# --------------------------------------------------------------------------- #
def line(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw a straight line from (x0, y0) to (x1, y1).

    The endpoints are always included; intermediate points are placed at
    uniform ``spacing`` along the segment.
    """
    sp = spacing if spacing is not None else _resolve_spacing(opts)
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length == 0:
        return [_make_placement(x0, y0, opts)]
    n = max(1, int(math.floor(length / sp + 1e-9)))
    out: list[Placement] = []
    for i in range(n + 1):
        t = i / n
        out.append(_make_placement(x0 + dx * t, y0 + dy * t, opts))
    return out


def polyline(
    points: list[tuple[float, float]],
    opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw a chain of connected segments through ``points``.

    Each segment is sampled at ``spacing``; shared vertices are NOT
    duplicated (the endpoint of segment *i* equals the start of segment
    *i+1*, so the second is skipped).
    """
    if not points:
        return []
    if len(points) == 1:
        return [_make_placement(points[0][0], points[0][1], opts)]
    out: list[Placement] = []
    for i in range(len(points) - 1):
        seg = line(points[i][0], points[i][1],
                   points[i + 1][0], points[i + 1][1],
                   opts, spacing=spacing)
        if i > 0:
            seg = seg[1:]  # skip duplicated vertex
        out.extend(seg)
    return out


def hollow_circle(
    cx: float,
    cy: float,
    radius: float,
    opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw a hollow circle (perimeter only) centred at (cx, cy)."""
    sp = spacing if spacing is not None else _resolve_spacing(opts)
    circumference = 2.0 * math.pi * radius
    n = max(8, int(math.ceil(circumference / sp)))
    out: list[Placement] = []
    for i in range(n):
        theta = 2.0 * math.pi * i / n
        out.append(_make_placement(
            cx + radius * math.cos(theta),
            cy + radius * math.sin(theta),
            opts,
        ))
    return out


def filled_circle(
    cx: float,
    cy: float,
    radius: float,
    opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw a filled disk centred at (cx, cy) using a hex-ish grid.

    Points are placed on concentric rings; ring radius grows by ``spacing``
    so neighbouring points sit at the same spacing both within and across
    rings. The centre point is always included.
    """
    sp = spacing if spacing is not None else _resolve_spacing(opts)
    out: list[Placement] = [_make_placement(cx, cy, opts)]
    ring_radius = sp
    while ring_radius <= radius + 1e-6:
        # circumference at this ring
        circ = 2.0 * math.pi * ring_radius
        n_on_ring = max(6, int(round(circ / sp)))
        for i in range(n_on_ring):
            theta = 2.0 * math.pi * i / n_on_ring
            out.append(_make_placement(
                cx + ring_radius * math.cos(theta),
                cy + ring_radius * math.sin(theta),
                opts,
            ))
        ring_radius += sp
    return out


def s_snake(
    cx: float,
    cy: float,
    height: float,
    width: float,
    opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw a vertical S-shape (one full sine period).

    The snake spans ``height`` world units vertically (from ``cy - height/2``
    to ``cy + height/2``) and swings ``width`` units horizontally (peak
    amplitude = width/2).
    """
    sp = spacing if spacing is not None else _resolve_spacing(opts)
    n = max(4, int(math.ceil(height / sp)))
    pts: list[tuple[float, float]] = []
    for i in range(n + 1):
        t = i / n  # 0..1
        y = cy - height / 2.0 + height * t
        # one full period: sin(2*pi*t) → S-shape
        x = cx + (width / 2.0) * math.sin(2.0 * math.pi * t)
        pts.append((x, y))
    return polyline(pts, opts, spacing=spacing)


def thick_line_with_contours(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    thickness: float,
    outline_opts: PrimitiveOptions,
    fill_opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw a thick line with a contrasting outline.

    The shape is a "stadium" — a rectangle (long axis = the line) capped by
    two semicircles. The outline decorations run along the perimeter; the
    fill decorations fill the interior band.

    Parameters
    ----------
    x0, y0, x1, y1:
        Endpoints of the line's centreline.
    thickness:
        Total width of the band (perpendicular to the centreline). The
        outline radius equals ``thickness / 2``.
    outline_opts, fill_opts:
        Decorations for the perimeter and interior respectively. They
        SHOULD be different (otherwise the "outline" is invisible).
    """
    sp = spacing if spacing is not None else _resolve_spacing(fill_opts)
    dx = x1 - x0
    dy = y1 - y0
    length = math.hypot(dx, dy)
    if length == 0:
        # degenerate: just a filled circle
        return filled_circle(x0, y0, thickness / 2.0, fill_opts, spacing=sp)
    # Unit vector along the line and perpendicular.
    ux = dx / length
    uy = dy / length
    nx = -uy  # perpendicular (left-hand)
    ny = ux
    half_t = thickness / 2.0

    outline: list[Placement] = []
    fill: list[Placement] = []

    # Two long sides (offset by ±half_t along the normal).
    # Endpoints (first and last point of each side) are EXCLUDED here — the
    # semicircle caps cover them, and we don't want duplicate placements
    # at the corners.
    side_a = line(
        x0 + nx * half_t, y0 + ny * half_t,
        x1 + nx * half_t, y1 + ny * half_t,
        outline_opts, spacing=sp,
    )
    side_b = line(
        x0 - nx * half_t, y0 - ny * half_t,
        x1 - nx * half_t, y1 - ny * half_t,
        outline_opts, spacing=sp,
    )
    if len(side_a) >= 3:
        side_a = side_a[1:-1]
    if len(side_b) >= 3:
        side_b = side_b[1:-1]
    outline.extend(side_a)
    outline.extend(side_b)

    # Two semicircle caps at each endpoint. Each cap sweeps 180° from one
    # long-side endpoint to the other, going around the outside of the
    # stadium. Endpoints (theta = pi/2 and 3*pi/2) ARE included so the cap
    # meets the long sides seamlessly.
    cap_radius = half_t
    cap_steps = max(6, int(math.ceil(math.pi * cap_radius / sp)))
    # Cap at (x0, y0): semicircle on the -u side (away from x1).
    for i in range(cap_steps + 1):
        theta = math.pi / 2.0 + math.pi * i / cap_steps  # +pi/2 .. +3pi/2
        ox = math.cos(theta) * (-ux) + math.sin(theta) * (-nx)
        oy = math.cos(theta) * (-uy) + math.sin(theta) * (-ny)
        outline.append(_make_placement(
            x0 + ox * cap_radius,
            y0 + oy * cap_radius,
            outline_opts,
        ))
    # Cap at (x1, y1): mirror — sweep on +u side (away from x0).
    for i in range(cap_steps + 1):
        theta = math.pi / 2.0 + math.pi * i / cap_steps
        ox = math.cos(theta) * ux + math.sin(theta) * nx
        oy = math.cos(theta) * uy + math.sin(theta) * ny
        outline.append(_make_placement(
            x1 + ox * cap_radius,
            y1 + oy * cap_radius,
            outline_opts,
        ))

    # Fill: rows perpendicular to the centreline, spaced `sp` apart along u.
    # Fill points are INSET — they sit strictly between the two outline sides
    # so the outline is always visible around them. We use a cell-centred
    # layout: n cells of width thickness/n, with one fill point at the
    # centre of each cell. This guarantees the fill never lands on the
    # outline (which would be visually wasted).
    outline_coords: set[tuple[int, int]] = {(p.x, p.y) for p in outline}
    n_fill_rows = max(1, int(math.floor(length / sp)))
    n_fill_per_row = max(1, int(math.floor(thickness / sp)))
    cell_w = thickness / n_fill_per_row
    for i in range(n_fill_rows + 1):
        t = i / n_fill_rows
        cx_row = x0 + dx * t
        cy_row = y0 + dy * t
        for j in range(n_fill_per_row):
            # cell j covers offset range [-half_t + j*cell_w, -half_t + (j+1)*cell_w]
            # centre of cell j:
            offset = -half_t + (j + 0.5) * cell_w
            px = cx_row + nx * offset
            py = cy_row + ny * offset
            # Skip fill points that fall inside the cap semicircles — they
            # would be invisible under the cap decorations.
            along0 = (px - x0) * ux + (py - y0) * uy
            along1 = (px - x1) * ux + (py - y1) * uy
            if along0 < 0:
                d0 = math.hypot(px - x0, py - y0)
                if d0 < cap_radius - 1e-6:
                    continue
            if along1 > 0:
                d1 = math.hypot(px - x1, py - y1)
                if d1 < cap_radius - 1e-6:
                    continue
            # Defensive: skip if the integer-rounded coord lands on an
            # outline point (shouldn't happen with the inset layout, but
            # rounding can occasionally cause it).
            ix, iy = int(round(px)), int(round(py))
            if (ix, iy) in outline_coords:
                continue
            fill.append(_make_placement(px, py, fill_opts))

    # Defensive dedup of outline points at identical integer coordinates
    # (rounding can cause near-duplicates at the cap/side seam).
    seen: set[tuple[int, int]] = set()
    deduped_outline: list[Placement] = []
    for p in outline:
        key = (p.x, p.y)
        if key in seen:
            continue
        seen.add(key)
        deduped_outline.append(p)

    return deduped_outline + fill


# --------------------------------------------------------------------------- #
# Convenience: a curated composition of all five primitives
# --------------------------------------------------------------------------- #
def center_composition(
    center_x: float,
    center_y: float,
    *,
    line_decoration: str = "Long Grass",
    hollow_circle_decoration: str = "Maraket Rubble",
    filled_circle_decoration: str = "Coastal Pebble",
    s_snake_decoration: str = "Sand Tussock",
    thick_outline_decoration: str = "Small Coastal Stone",
    thick_fill_decoration: str = "Coastal Pebble",
    spacing_override: float | None = None,
) -> list[Placement]:
    """Build a composition of all five primitives around a centre point.

    The five shapes are arranged in a 3+2 grid:

    ::

        Top row (y = cy - 50):
            [ vertical-lines ] [ hollow-circle ] [ filled-circle ]
        Bottom row (y = cy + 35):
            [   S-snake    ] [     thick line with contours     ]

    All coordinates are derived from ``center_x``/``center_y`` so the whole
    composition can be moved by shifting the centre. The default layout fits
    inside the Canal Hideout playable canvas (700..860 × 540..775) when the
    centre is (780, 657).

    The decoration defaults use only decorations present in
    :data:`KNOWN_HASHES` with high/medium placement-confidence. Override
    them via the keyword arguments if a different palette is desired.
    """
    cx = float(center_x)
    cy = float(center_y)

    # Helper to build PrimitiveOptions with optional spacing override.
    def opts(name: str) -> PrimitiveOptions:
        return PrimitiveOptions(
            decoration=name,
            spacing_override=spacing_override,
        )

    out: list[Placement] = []

    # ---- Top row, y = cy - 50 ----
    top_y = cy - 50.0

    # (1) Vertical lines: 3 parallel vertical lines, height 80 wu, x = cx-60..-45
    vl_x_offsets = (-60.0, -52.5, -45.0)
    vl_y_top = top_y - 40.0
    vl_y_bot = top_y + 40.0
    for ox in vl_x_offsets:
        out.extend(line(cx + ox, vl_y_top, cx + ox, vl_y_bot,
                        opts(line_decoration)))

    # (2) Hollow circle: centre (cx, top_y), radius 18
    out.extend(hollow_circle(cx, top_y, 18.0, opts(hollow_circle_decoration)))

    # (3) Filled circle: centre (cx + 45, top_y), radius 14
    out.extend(filled_circle(cx + 45.0, top_y, 14.0,
                             opts(filled_circle_decoration)))

    # ---- Bottom row, y = cy + 35 ----
    bot_y = cy + 35.0

    # (4) S-snake: centre (cx - 45, bot_y), height 60, width 25
    out.extend(s_snake(cx - 45.0, bot_y, 60.0, 25.0,
                       opts(s_snake_decoration)))

    # (5) Thick line with contours: horizontal at y = bot_y, length 50, thickness 14
    out.extend(thick_line_with_contours(
        cx + 5.0, bot_y,
        cx + 55.0, bot_y,
        thickness=14.0,
        outline_opts=opts(thick_outline_decoration),
        fill_opts=opts(thick_fill_decoration),
    ))

    return out
