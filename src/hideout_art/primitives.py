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

Shapes (core, 0.2.7)
--------------------
* :func:`line` — straight line between two points.
* :func:`polyline` — chain of segments (used by S-snake).
* :func:`hollow_circle` — points on a circle perimeter.
* :func:`filled_circle` — points in a disk.
* :func:`s_snake` — sinusoidal vertical S-shape.
* :func:`thick_line_with_contours` — outline + fill thick band.

Shapes (mosaic / bas-relief, 0.2.8)
-----------------------------------
* :func:`arc` — partial circle (arches, frames, half-circles).
* :func:`rectangle` — hollow rectangle outline (borders, frames).
* :func:`polygon` — regular n-gon (triangle, square, pentagon, hexagon…).
* :func:`grid` — regular cols×rows grid (mosaic tiles, pointillism).

Shapes (mosaic v2 / portrait-grade, 0.2.9)
------------------------------------------
* :func:`bezier_curve` — quadratic Bézier curve (smiles, eyebrows, fingers).
* :func:`thick_ring` — annular ring with outline + fill (glasses lenses, eyes).
* :func:`thick_arc` — thick arc band with outline + fill (glasses temples,
  brackets, smile with thickness).
* :func:`crosshatch` — diagonal cross-hatch pattern (beard, hair, texture).

See ``scripts/draw_primitives.py`` for a CLI that injects the curated
composition into the centre of an existing ``.hideout`` file.
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
# Mosaic / bas-relief primitives (0.2.8)
# --------------------------------------------------------------------------- #
def arc(
    cx: float,
    cy: float,
    radius: float,
    start_angle_deg: float,
    end_angle_deg: float,
    opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw a circular arc from ``start_angle_deg`` to ``end_angle_deg``.

    Angles are in degrees, measured counter-clockwise from the +x axis
    (standard math convention; matches ``math.cos``/``math.sin``).
    The arc is sampled at uniform ``spacing`` along the arc length; both
    endpoints are always included.

    Use cases: arch tops, semicircle caps, quarter-circle corners in
    bas-relief frames, curved brackets.
    """
    sp = spacing if spacing is not None else _resolve_spacing(opts)
    # Normalise the sweep so we always travel counter-clockwise from start
    # to end (the visual "short" or "long" way is the caller's choice — we
    # just respect the sign of (end - start)).
    sweep_deg = end_angle_deg - start_angle_deg
    arc_len = abs(math.radians(sweep_deg)) * radius
    if arc_len == 0:
        return [_make_placement(
            cx + radius * math.cos(math.radians(start_angle_deg)),
            cy + radius * math.sin(math.radians(start_angle_deg)),
            opts,
        )]
    n = max(2, int(math.ceil(arc_len / sp)))
    out: list[Placement] = []
    for i in range(n + 1):
        t = i / n
        ang = math.radians(start_angle_deg + sweep_deg * t)
        out.append(_make_placement(
            cx + radius * math.cos(ang),
            cy + radius * math.sin(ang),
            opts,
        ))
    return out


def rectangle(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw a hollow rectangle outline with corners at (x0, y0) and (x1, y1).

    Each side is sampled at uniform ``spacing``; corners are included once
    (not duplicated). Use for borders, picture frames, mosaic cell outlines.
    """
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0
    # Walk the perimeter as a closed polyline — but skip the closing
    # duplicate vertex so the start corner is not duplicated.
    pts: list[tuple[float, float]] = [
        (x0, y0),
        (x1, y0),
        (x1, y1),
        (x0, y1),
    ]
    out: list[Placement] = []
    for i in range(4):
        a = pts[i]
        b = pts[(i + 1) % 4]
        seg = line(a[0], a[1], b[0], b[1], opts, spacing=spacing)
        if i > 0:
            seg = seg[1:]  # skip duplicated corner
        # On the last side, also drop the closing vertex (== pts[0]).
        if i == 3 and len(seg) >= 1:
            seg = seg[:-1]
        out.extend(seg)
    return out


def polygon(
    cx: float,
    cy: float,
    radius: float,
    n_sides: int,
    opts: PrimitiveOptions,
    *,
    rotation_deg: float = 0.0,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw a regular n-gon centred at (cx, cy) with circumradius ``radius``.

    The first vertex sits at ``rotation_deg`` (measured counter-clockwise
    from +x axis, in degrees). Vertices are connected by line segments
    sampled at uniform ``spacing``; each vertex appears exactly once.

    Use cases: triangles, squares, pentagons, hexagons, octagons — the
    basic tile shapes of geometric mosaics.

    Raises
    ------
    ValueError
        If ``n_sides < 3``.
    """
    if n_sides < 3:
        raise ValueError(f"polygon needs n_sides >= 3 (got {n_sides})")
    sp = spacing if spacing is not None else _resolve_spacing(opts)
    rot = math.radians(rotation_deg)
    # Vertices on the circumcircle.
    vertices: list[tuple[float, float]] = []
    for i in range(n_sides):
        ang = rot + 2.0 * math.pi * i / n_sides
        vertices.append((cx + radius * math.cos(ang),
                         cy + radius * math.sin(ang)))
    out: list[Placement] = []
    for i in range(n_sides):
        a = vertices[i]
        b = vertices[(i + 1) % n_sides]
        seg = line(a[0], a[1], b[0], b[1], opts, spacing=sp)
        if i > 0:
            seg = seg[1:]  # skip duplicated vertex
        # On the last side, drop the closing vertex (== vertices[0]).
        if i == n_sides - 1 and len(seg) >= 1:
            seg = seg[:-1]
        out.extend(seg)
    return out


def grid(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    opts: PrimitiveOptions,
    cols: int,
    rows: int,
    *,
    include_border: bool = True,
) -> list[Placement]:
    """Draw a regular ``cols`` × ``rows`` grid of points inside the rectangle
    (x0, y0)..(x1, y1).

    Points are laid out in a uniform lattice. With ``include_border=True``
    (default) the lattice includes the four rectangle sides (i.e. ``cols``
    points per row, ``rows`` points per column). With ``include_border=False``
    the points sit at cell centres (``cols-1`` interior x-positions, etc.) —
    useful when you want pure "tile centres" without edge bleed.

    Spacing is derived from the lattice geometry (NOT from
    :data:`DECORATION_FOOTPRINT_CATALOG`) — the caller picks the cell count
    and the function honours it. Use ``PrimitiveOptions.spacing_override``
    only if you want to resample the same grid at a different density.

    Use cases: mosaic tile grids, pointillism fills, regular dot fields
    for bas-relief textures.

    Raises
    ------
    ValueError
        If ``cols`` or ``rows`` < 1.
    """
    if cols < 1 or rows < 1:
        raise ValueError(
            f"grid needs cols>=1 and rows>=1 (got cols={cols}, rows={rows})"
        )
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0
    out: list[Placement] = []
    if include_border:
        # cols points uniformly spaced across [x0, x1] (inclusive both ends).
        x_steps = cols - 1 if cols > 1 else 0
        y_steps = rows - 1 if rows > 1 else 0
        for j in range(rows):
            ty = j / y_steps if y_steps > 0 else 0.0
            py = y0 + (y1 - y0) * ty
            for i in range(cols):
                tx = i / x_steps if x_steps > 0 else 0.0
                px = x0 + (x1 - x0) * tx
                out.append(_make_placement(px, py, opts))
    else:
        # cols-1 interior cells along x; place a point at the centre of each.
        x_cell = (x1 - x0) / cols
        y_cell = (y1 - y0) / rows
        for j in range(rows):
            py = y0 + y_cell * (j + 0.5)
            for i in range(cols):
                px = x0 + x_cell * (i + 0.5)
                out.append(_make_placement(px, py, opts))
    return out


# --------------------------------------------------------------------------- #
# Mosaic v2 / portrait-grade primitives (0.2.9)
# --------------------------------------------------------------------------- #
def bezier_curve(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw a quadratic Bézier curve from ``p0`` through control ``p1`` to ``p2``.

    The curve is sampled at a fixed ``spacing`` along an *approximate* arc
    length (chord length sum of subdivided segments). Endpoints are always
    included. Use for organic curves — smiles, eyebrows, finger outlines,
    shoulder lines, hair contours.

    The control point ``p1`` pulls the curve toward itself but the curve
    does NOT pass through ``p1`` (except in degenerate cases). For a curve
    that visibly bulges toward ``p1``, place ``p1`` well outside the
    ``p0``–``p2`` chord.

    Parameters
    ----------
    p0, p1, p2:
        Start, control, end points (in world units).
    opts:
        Decoration + rotation/variant.
    spacing:
        Override the catalog spacing (otherwise :func:`safe_spacing`).
    """
    sp = spacing if spacing is not None else _resolve_spacing(opts)
    # Approximate arc length by sampling 32 fine sub-segments. This is
    # cheap and accurate enough — error is well below placement spacing.
    n_fine = 32
    fine_pts: list[tuple[float, float]] = []
    for i in range(n_fine + 1):
        t = i / n_fine
        mt = 1.0 - t
        x = mt * mt * p0[0] + 2.0 * mt * t * p1[0] + t * t * p2[0]
        y = mt * mt * p0[1] + 2.0 * mt * t * p1[1] + t * t * p2[1]
        fine_pts.append((x, y))
    # Cumulative chord length.
    seg_lens = [
        math.hypot(fine_pts[i + 1][0] - fine_pts[i][0],
                   fine_pts[i + 1][1] - fine_pts[i][1])
        for i in range(n_fine)
    ]
    total = sum(seg_lens)
    if total == 0:
        return [_make_placement(p0[0], p0[1], opts)]
    n = max(2, int(math.ceil(total / sp)))
    out: list[Placement] = []
    for i in range(n + 1):
        t = i / n
        # Walk the fine polyline to find the point at arc-length t*total.
        target = t * total
        acc = 0.0
        for j, sl in enumerate(seg_lens):
            if acc + sl >= target or j == len(seg_lens) - 1:
                # interpolate within fine segment j
                local = (target - acc) / sl if sl > 0 else 0.0
                local = max(0.0, min(1.0, local))
                x = fine_pts[j][0] + (fine_pts[j + 1][0] - fine_pts[j][0]) * local
                y = fine_pts[j][1] + (fine_pts[j + 1][1] - fine_pts[j][1]) * local
                out.append(_make_placement(x, y, opts))
                break
            acc += sl
    return out


def thick_ring(
    cx: float,
    cy: float,
    inner_r: float,
    outer_r: float,
    outline_opts: PrimitiveOptions,
    fill_opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw an annular ring (donut) with a contrasting outline + fill.

    The outer and inner circles form the outline; the band between them is
    filled with a second decoration. Use for glasses lenses, eyes, decorative
    borders, halos, nimbus shapes.

    Parameters
    ----------
    cx, cy:
        Centre of the ring.
    inner_r, outer_r:
        Inner and outer radii. ``inner_r`` may be 0 (degenerates to a
        :func:`filled_circle` with an outline).
    outline_opts, fill_opts:
        Decorations for the two circle outlines and the annular fill. SHOULD
        be different (otherwise the outline is invisible).
    spacing:
        Override the catalog spacing (otherwise uses ``fill_opts`` spacing).

    Raises
    ------
    ValueError
        If ``inner_r < 0``, ``outer_r <= 0``, or ``inner_r >= outer_r``.
    """
    if inner_r < 0:
        raise ValueError(f"inner_r must be >= 0 (got {inner_r})")
    if outer_r <= 0:
        raise ValueError(f"outer_r must be > 0 (got {outer_r})")
    if inner_r >= outer_r:
        raise ValueError(
            f"inner_r ({inner_r}) must be < outer_r ({outer_r})"
        )
    sp = spacing if spacing is not None else _resolve_spacing(fill_opts)
    outline: list[Placement] = []
    fill: list[Placement] = []

    # Outer circle outline.
    outline.extend(hollow_circle(cx, cy, outer_r, outline_opts, spacing=sp))
    # Inner circle outline (skip if inner_r is 0 — degenerates to a point).
    if inner_r > 0:
        outline.extend(hollow_circle(cx, cy, inner_r, outline_opts, spacing=sp))
    else:
        outline.append(_make_placement(cx, cy, outline_opts))

    # Fill: concentric rings between inner_r and outer_r, spaced `sp` apart.
    # Start one ring inward from outer_r so fill does not collide with outline.
    outline_keys: set[tuple[int, int]] = {(p.x, p.y) for p in outline}
    ring_r = outer_r - sp
    while ring_r > inner_r + 1e-6:
        circ = 2.0 * math.pi * ring_r
        n_on_ring = max(6, int(round(circ / sp)))
        for i in range(n_on_ring):
            theta = 2.0 * math.pi * i / n_on_ring
            px = cx + ring_r * math.cos(theta)
            py = cy + ring_r * math.sin(theta)
            ix, iy = int(round(px)), int(round(py))
            if (ix, iy) in outline_keys:
                continue
            fill.append(_make_placement(px, py, fill_opts))
        ring_r -= sp

    return outline + fill


def thick_arc(
    cx: float,
    cy: float,
    radius: float,
    thickness: float,
    start_angle_deg: float,
    end_angle_deg: float,
    outline_opts: PrimitiveOptions,
    fill_opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
) -> list[Placement]:
    """Draw a thick arc band with outline + fill.

    The shape is a partial annulus swept from ``start_angle_deg`` to
    ``end_angle_deg`` at centre ``radius``, with band ``thickness``.
    Two arc outlines run along the inner and outer edges; two radial cap
    lines close the band at each end; the interior is filled.

    Use for glasses temples (partial circles), brackets, smile curves with
    thickness, decorative arch bands.

    Parameters
    ----------
    cx, cy:
        Centre of curvature.
    radius:
        Centreline radius (mid-band).
    thickness:
        Total band width (perpendicular to the centreline). Inner edge sits
        at ``radius - thickness/2``, outer edge at ``radius + thickness/2``.
    start_angle_deg, end_angle_deg:
        Sweep endpoints in degrees (counter-clockwise from +x axis).
    outline_opts, fill_opts:
        Decorations for the perimeter and interior. SHOULD differ.
    spacing:
        Override catalog spacing (otherwise uses ``fill_opts`` spacing).

    Raises
    ------
    ValueError
        If ``radius <= 0`` or ``thickness <= 0``.
    """
    if radius <= 0:
        raise ValueError(f"radius must be > 0 (got {radius})")
    if thickness <= 0:
        raise ValueError(f"thickness must be > 0 (got {thickness})")
    sp = spacing if spacing is not None else _resolve_spacing(fill_opts)
    inner_r = radius - thickness / 2.0
    outer_r = radius + thickness / 2.0
    if inner_r < 0:
        inner_r = 0.0

    sweep_deg = end_angle_deg - start_angle_deg
    outline: list[Placement] = []
    fill: list[Placement] = []

    # Outer arc (radius = outer_r).
    outline.extend(arc(cx, cy, outer_r, start_angle_deg, end_angle_deg,
                       outline_opts, spacing=sp))
    # Inner arc (radius = inner_r), walked in the same direction.
    if inner_r > 0:
        inner_arc = arc(cx, cy, inner_r, start_angle_deg, end_angle_deg,
                        outline_opts, spacing=sp)
        outline.extend(inner_arc)
    else:
        outline.append(_make_placement(
            cx + 0 * math.cos(math.radians(start_angle_deg)),
            cy + 0 * math.sin(math.radians(start_angle_deg)),
            outline_opts,
        ))

    # Two radial caps: a line from inner edge to outer edge at each endpoint.
    for ang_deg in (start_angle_deg, end_angle_deg):
        ang = math.radians(ang_deg)
        ix = cx + inner_r * math.cos(ang)
        iy = cy + inner_r * math.sin(ang)
        ox = cx + outer_r * math.cos(ang)
        oy = cy + outer_r * math.sin(ang)
        cap = line(ix, iy, ox, oy, outline_opts, spacing=sp)
        # Drop endpoints (already on the arc outlines) to avoid duplicates.
        if len(cap) >= 3:
            cap = cap[1:-1]
        outline.extend(cap)

    # Fill: radial spokes at uniform angular spacing, each spoke running from
    # inner_r+epsilon to outer_r-epsilon. Skip points that land on outline.
    outline_keys: set[tuple[int, int]] = {(p.x, p.y) for p in outline}
    arc_len_center = abs(math.radians(sweep_deg)) * radius
    n_spokes = max(2, int(math.ceil(arc_len_center / sp)))
    inner_pad = inner_r + sp * 0.1 if inner_r > 0 else 0.0
    outer_pad = outer_r - sp * 0.1
    for i in range(n_spokes + 1):
        t = i / n_spokes
        ang = math.radians(start_angle_deg + sweep_deg * t)
        spoke_len = outer_pad - inner_pad
        if spoke_len <= 0:
            continue
        n_on_spoke = max(1, int(math.floor(spoke_len / sp)))
        for j in range(n_on_spoke + 1):
            tt = j / n_on_spoke if n_on_spoke > 0 else 0.5
            r = inner_pad + spoke_len * tt
            px = cx + r * math.cos(ang)
            py = cy + r * math.sin(ang)
            ix, iy = int(round(px)), int(round(py))
            if (ix, iy) in outline_keys:
                continue
            fill.append(_make_placement(px, py, fill_opts))

    # Defensive dedup of outline at identical integer coordinates.
    seen: set[tuple[int, int]] = set()
    deduped: list[Placement] = []
    for p in outline:
        key = (p.x, p.y)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)
    return deduped + fill


def crosshatch(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    opts: PrimitiveOptions,
    *,
    spacing: float | None = None,
    angle_deg: float = 45.0,
    bidirectional: bool = True,
) -> list[Placement]:
    """Draw a diagonal cross-hatch pattern clipped to the rectangle (x0,y0)..(x1,y1).

    Two families of parallel diagonal lines (at ``angle_deg`` and
    ``angle_deg + 90°``) are sampled at uniform ``spacing``. Both families
    are clipped to the rectangle. With ``bidirectional=False`` only the
    first family is drawn (single-direction hatch).

    Use for textures — beards, hair, shadows, fabric, decorative shading.

    Parameters
    ----------
    x0, y0, x1, y1:
        Rectangle corners (any order — auto-normalised).
    opts:
        Decoration + rotation/variant.
    spacing:
        Override catalog spacing (otherwise :func:`safe_spacing`).
    angle_deg:
        Angle of the first hatch family, in degrees (0 = horizontal,
        90 = vertical). The second family is at ``angle_deg + 90``.
    bidirectional:
        If True (default), draw both families (cross-hatch). If False,
        draw only the first family (parallel hatch).
    """
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0
    sp = spacing if spacing is not None else _resolve_spacing(opts)
    rect_w = x1 - x0
    rect_h = y1 - y0
    if rect_w <= 0 or rect_h <= 0:
        return []

    out: list[Placement] = []
    seen: set[tuple[int, int]] = set()

    def _add_family(ang_deg: float) -> None:
        ang = math.radians(ang_deg)
        # Direction along the lines.
        dx = math.cos(ang)
        dy = math.sin(ang)
        # Perpendicular direction (for offsetting parallel lines).
        nx = -dy
        ny = dx
        # The rectangle's "diagonal" extent — lines are generated for
        # perpendicular offsets in [-diag/2, +diag/2] where diag is the
        # rectangle diagonal. This guarantees full coverage.
        diag = math.hypot(rect_w, rect_h)
        cx = (x0 + x1) / 2.0
        cy = (y0 + y1) / 2.0
        n_offsets = max(2, int(math.ceil(diag / sp)))
        for k in range(-n_offsets, n_offsets + 1):
            # Offset line passes through (px, py) with direction (dx, dy).
            px = cx + nx * k * sp
            py = cy + ny * k * sp
            # Liang-Barsky clipping: parametric line point(t) = (px+dx*t, py+dy*t).
            # Standard form: p_i*t <= q_i for the four edges.
            #   left  (x=x0): p=-dx, q=px-x0
            #   right (x=x1): p= dx, q=x1-px
            #   bot   (y=y0): p=-dy, q=py-y0
            #   top   (y=y1): p= dy, q=y1-py
            t_min = -math.inf
            t_max = math.inf
            reject = False
            for p_i, q_i in (
                (-dx, px - x0),
                ( dx, x1 - px),
                (-dy, py - y0),
                ( dy, y1 - py),
            ):
                if abs(p_i) < 1e-12:
                    # Line parallel to this edge.
                    if q_i < 0:
                        reject = True
                        break
                    continue
                r = q_i / p_i
                if p_i < 0:
                    if r > t_max:
                        reject = True
                        break
                    if r > t_min:
                        t_min = r
                else:  # p_i > 0
                    if r < t_min:
                        reject = True
                        break
                    if r < t_max:
                        t_max = r
            if reject or t_min > t_max:
                continue
            # Sample points along the clipped segment at uniform spacing.
            seg_len = (t_max - t_min) * math.hypot(dx, dy)
            if seg_len <= 0:
                continue
            n_pts = max(1, int(math.ceil(seg_len / sp)))
            for i in range(n_pts + 1):
                t = t_min + (t_max - t_min) * (i / n_pts)
                qx = px + dx * t
                qy = py + dy * t
                # Defensive: ensure inside rectangle (numerical safety).
                if qx < x0 - 1e-6 or qx > x1 + 1e-6 or \
                   qy < y0 - 1e-6 or qy > y1 + 1e-6:
                    continue
                ix, iy = int(round(qx)), int(round(qy))
                if (ix, iy) in seen:
                    continue
                seen.add((ix, iy))
                out.append(_make_placement(qx, qy, opts))

    _add_family(angle_deg)
    if bidirectional:
        _add_family(angle_deg + 90.0)
    return out


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
    s_snake_decoration: str = "Maraket Rubble",
    thick_outline_decoration: str = "Small Coastal Stone",
    thick_fill_decoration: str = "Long Grass",
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

    KI-14 / KI-15 fixes (0.2.8)
    ---------------------------
    Previous defaults produced 2/5 unrecognisable shapes in-game:
      * ``s_snake_decoration`` was ``"Sand Tussock"`` (too sparse at width=25).
        Now ``"Maraket Rubble"`` — denser (sp=13.6 vs 17.1) and higher contrast
        against the tan Canal Hideout floor.
      * ``thick_fill_decoration`` was ``"Coastal Pebble"`` at ``thickness=14``
        (fill band only 1 point wide — invisible). Now ``"Long Grass"`` at
        ``thickness=28`` — Long Grass visibility confirmed by KI-13 vertical
        lines, 28 wu band gives ≥2 fill rows.
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

    # (5) Thick line with contours: horizontal at y = bot_y, length 50, thickness 28
    #     KI-15 (0.2.8): was thickness=14 (1 fill row, invisible). Now 28 (2+
    #     fill rows) + Long Grass fill (visible per KI-13 vertical lines).
    out.extend(thick_line_with_contours(
        cx + 5.0, bot_y,
        cx + 55.0, bot_y,
        thickness=28.0,
        outline_opts=opts(thick_outline_decoration),
        fill_opts=opts(thick_fill_decoration),
    ))

    return out


# --------------------------------------------------------------------------- #
# Convenience: a curated composition of the 0.2.9 mosaic v2 primitives
# --------------------------------------------------------------------------- #
def mosaic_composition(
    center_x: float,
    center_y: float,
    *,
    bezier_decoration: str = "Small Coastal Stone",
    ring_outline_decoration: str = "Small Coastal Stone",
    ring_fill_decoration: str = "Cave Coral",
    arc_outline_decoration: str = "Small Coastal Stone",
    arc_fill_decoration: str = "Long Grass",
    hatch_decoration: str = "Seaweed",
    spacing_override: float | None = None,
) -> list[Placement]:
    """Build a composition of the four 0.2.9 mosaic v2 primitives.

    The composition is **strictly separated** from :func:`center_composition`:
    it lives in a different zone of the canvas (offset DOWN by ~95 wu from
    the centre, in the free space below the 0.2.7 core shapes) so the 0.2.7
    core shapes can be visually verified independently of the 0.2.9
    additions. This protects the KI-14/15 re-verification (which only
    covers ``center_composition``) from being confounded by new shapes
    landing on top of the old ones.

    Layout (relative to ``center_x, center_y``, zone centre = ``(cx, cy+95)``)::

        ┌───────────────────────────────┐
        │  [thick_ring]   [thick_arc]   │   y = zy - 12  (compact r=7)
        │                                │
        │  [bezier smile]                │   y = zy + 5..15
        │                                │
        │  [crosshatch beard patch]      │   y = zy + 10..22
        └───────────────────────────────┘

    Total zone height ~37 wu, width ~50 wu. Fits inside Canal Hideout
    bounds ``(700, 540, 860, 775)`` when ``center`` is ``(780, 657)`` —
    zone becomes x∈[755, 808], y∈[733, 774], strictly below the
    ``center_composition`` bottom (S-snake at cy+65 = 722).

    All defaults use only decorations with high/medium placement confidence
    and that match the roles laid out in ``docs/mosaic_recipe.md``:

      * ``bezier_decoration`` — Small Coastal Stone: контур/точки, узнаваемая форма.
      * ``ring_outline_decoration`` — Small Coastal Stone: та же роль для контура линзы.
      * ``ring_fill_decoration`` — Cave Coral: светло-коричневый fill, виден на tan-полу.
      * ``arc_outline_decoration`` — Small Coastal Stone.
      * ``arc_fill_decoration`` — Long Grass: виден на полу (KI-13).
      * ``hatch_decoration`` — Seaweed: бесформенная куча, роль «бороды».
    """
    cx = float(center_x)
    cy = float(center_y)

    # Zone centre — directly BELOW center_composition, in the free canvas
    # space between the S-snake bottom (cy+65) and the canvas floor (775).
    zx = cx
    zy = cy + 95.0

    def opts(name: str) -> PrimitiveOptions:
        return PrimitiveOptions(
            decoration=name,
            spacing_override=spacing_override,
        )

    out: list[Placement] = []

    # (1) thick_ring — glasses lens shape, top-left of zone.
    #     The ring band is narrow (outer_r - inner_r = 7 wu), but Cave Coral
    #     has 'single' confidence → fallback spacing 15 wu → no fill would be
    #     generated. Override the ring's spacing to 3.0 wu so the fill band
    #     gets 2+ concentric rings of Cave Coral placements.
    ring_fill_opts_dense = PrimitiveOptions(
        decoration=ring_fill_decoration,
        spacing_override=3.0 if spacing_override is None else spacing_override,
    )
    out.extend(thick_ring(
        zx - 18.0, zy - 12.0,
        inner_r=3.0, outer_r=10.0,
        outline_opts=opts(ring_outline_decoration),
        fill_opts=ring_fill_opts_dense,
        spacing=3.0 if spacing_override is None else spacing_override,
    ))

    # (2) thick_arc — half-circle bracket, top-right of zone.
    out.extend(thick_arc(
        zx + 18.0, zy - 12.0,
        radius=8.0, thickness=4.0,
        start_angle_deg=0.0, end_angle_deg=180.0,
        outline_opts=opts(arc_outline_decoration),
        fill_opts=opts(arc_fill_decoration),
    ))

    # (3) bezier_curve — smile arc below the two top shapes.
    out.extend(bezier_curve(
        p0=(zx - 15.0, zy + 5.0),
        p1=(zx,        zy + 15.0),
        p2=(zx + 15.0, zy + 5.0),
        opts=opts(bezier_decoration),
    ))

    # (4) crosshatch — beard/shadow patch at the bottom of the zone.
    out.extend(crosshatch(
        zx - 18.0, zy + 10.0,
        zx + 18.0, zy + 22.0,
        opts=opts(hatch_decoration),
        angle_deg=30.0,
    ))

    return out


# --------------------------------------------------------------------------- #
# Convenience: CLEAN composition (0.3.0) — simplest contours + fills
# --------------------------------------------------------------------------- #
def clean_composition(
    center_x: float,
    center_y: float,
    *,
    contour_decoration: str = "Long Grass",
    fill_decoration: str = "Maraket Rubble",
    spacing_override: float | None = None,
) -> list[Placement]:
    """Build a CLEAN composition of 7 simplest primitives around a centre.

    Each shape uses exactly ONE decoration (no mixed outline+fill inside
    one shape). All shapes are either pure contours (perimeter only) or
    pure fills (solid disk / lattice) — never both at once.

    This is the 0.3.0 response to KI-17: the 0.2.9 mosaic v2 output
    (bezier_curve + thick_ring + thick_arc + crosshatch in one canvas)
    produced a noisy "mush" that did not visually parse in-game. The
    clean composition is the simplest possible visual-verify test bed —
    one decoration per shape, plenty of empty canvas between shapes, no
    overlapping primitives.

    Layout (relative to ``center_x, center_y``)::

        Row 1 (y = cy - 42):  contour shapes
            [hollow_circle] [rectangle] [triangle] [arc-half]

        Row 2 (y = cy + 42):  fill shapes
            [filled_circle] [hexagon-contour] [3x3-grid-fill]

    All 7 shapes fit inside Canal Hideout bounds ``(700, 540, 860, 775)``
    when the centre is ``(780, 657)`` — composition bbox is roughly
    x∈[715, 845], y∈[595, 715].

    Parameters
    ----------
    center_x, center_y:
        Centre of the composition in world coordinates. For Canal
        Hideout use ``(780, 657)``.
    contour_decoration:
        Decoration for the 4 contour shapes in row 1 (hollow_circle,
        rectangle, triangle, arc). Default: ``"Long Grass"`` — densest
        in the catalog (min_spacing_wu=13.3) for the thinnest lines.
    fill_decoration:
        Decoration for the 3 fill/contour shapes in row 2 (filled_circle,
        hexagon, grid). Default: ``"Maraket Rubble"`` (min_spacing_wu=13.6,
        similar density, contrasting brown for visual distinction from
        row 1).
    spacing_override:
        Optional override for the auto-derived spacing. Leave ``None`` to
        use ``DECORATION_FOOTPRINT_CATALOG.min_spacing_wu`` — already the
        thinnest possible.

    Design rules
    ------------
    * ONE decoration per shape — never mix outline + fill inside one
      shape. Shapes that traditionally need both (e.g. thick_band) are
      deliberately excluded.
    * Pure contour shapes: ``hollow_circle``, ``rectangle``, ``polygon``,
      ``arc``. Pure fill shapes: ``filled_circle``, ``grid``.
    * Each row is horizontally separated by ~40 wu so shapes do not
      visually overlap (Long Grass spacing is 13.3, so 40 wu gap = 3+
      empty tiles between shape edges).
    * Rows are vertically separated by 84 wu (2× the row height + gap).
    * No shape uses ``bezier_curve``, ``thick_ring``, ``thick_arc``,
      ``crosshatch``, ``s_snake``, or ``thick_line_with_contours`` —
      these remain in the module for advanced use but are intentionally
      absent from the clean test bed.
    """
    cx = float(center_x)
    cy = float(center_y)

    def opts(name: str) -> PrimitiveOptions:
        return PrimitiveOptions(
            decoration=name,
            spacing_override=spacing_override,
        )

    out: list[Placement] = []

    # ---- Row 1: contours (y = cy - 42) ----
    row1_y = cy - 42.0

    # (1) hollow_circle — pure contour. r=14, Long Grass.
    out.extend(hollow_circle(cx - 60.0, row1_y, 14.0,
                             opts(contour_decoration)))

    # (2) rectangle — pure hollow outline. 24×24 square, Long Grass.
    out.extend(rectangle(cx - 20.0 - 12.0, row1_y - 12.0,
                         cx - 20.0 + 12.0, row1_y + 12.0,
                         opts(contour_decoration)))

    # (3) polygon — triangle (3 sides), circumradius 14, Long Grass.
    #     Rotated so the flat side is on the bottom (point up).
    out.extend(polygon(cx + 20.0, row1_y, 14.0, 3,
                       opts(contour_decoration),
                       rotation_deg=90.0))

    # (4) arc — half-circle (0..180°), radius 12, Long Grass.
    #     Sweeps the upper half plane → looks like a dome/bowl.
    out.extend(arc(cx + 60.0, row1_y, 12.0, 0.0, 180.0,
                   opts(contour_decoration)))

    # ---- Row 2: fills + one contour (y = cy + 42) ----
    row2_y = cy + 42.0

    # (5) filled_circle — pure fill. r=10, Maraket Rubble.
    #     Position: cx - 45. Spans x ∈ [cx-55, cx-35]. Rightmost point
    #     at (cx-35, row2_y) is 23 wu from the hexagon's leftmost vertex
    #     at (cx-12, row2_y) — safe clearance.
    out.extend(filled_circle(cx - 45.0, row2_y, 10.0,
                             opts(fill_decoration)))

    # (6) polygon — hexagon (6 sides), circumradius 12, Maraket Rubble.
    #     Pure contour (no fill) — demonstrates a second polygon shape
    #     in a contrasting decoration. Spans x ∈ [cx-12, cx+12].
    out.extend(polygon(cx, row2_y, 12.0, 6,
                       opts(fill_decoration)))

    # (7) grid — 3×3 pure fill lattice in a 30×30 box, Maraket Rubble.
    #     include_border=True → 9 points uniformly spaced at 15 wu
    #     intervals (safely above min_spacing_wu=13.6).
    #     Position: cx + 50. Grid spans x ∈ [cx+35, cx+65]. Leftmost
    #     point at (cx+35, row2_y) is 23 wu from the hexagon's rightmost
    #     vertex at (cx+12, row2_y) — safe clearance.
    out.extend(grid(cx + 50.0 - 15.0, row2_y - 15.0,
                    cx + 50.0 + 15.0, row2_y + 15.0,
                    opts(fill_decoration),
                    cols=3, rows=3, include_border=True))

    return out
