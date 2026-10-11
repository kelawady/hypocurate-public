"""The evidence-level dial (step 10a; owner's brief and answer 2 of 2026-10-11).

A half circle of six separate segments, one per level, in one hue that darkens with the level (never red to green),
with a needle on the run's level. A marked test run's dial is hatched; its "test run" badge and every word are HTML
next to the drawing, never text inside it, so no text on the page is smaller than 12 px (owner's addition 6). The
verdict is shown beside the dial by the page, never in it. The level comes from the run (`run.evidence_level`, set by
code); this module only draws it.
"""
from __future__ import annotations

import math
from itertools import count

from markupsafe import Markup

LEVELS = 6
# One hue (blue, 215°), lightest at level 1, darkest at level 6 (register 'evidence_dial').
SHADES = ("#dde6f3", "#b9cbe7", "#8ea9d6", "#6286c2", "#3a63a6", "#1d3f78")
EMPTY = "#eceef2"
NEEDLE = "#1d2330"
SIZES = {"large": 220, "small": 64}
_ids = count(1)


def _point(cx: float, cy: float, r: float, degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    return cx + r * math.cos(a), cy - r * math.sin(a)


def _segment(i: int, cx: float, cy: float, outer: float, inner: float, gap: float) -> str:
    """Segment i (1..6) from the left (180°) to the right (0°), as an annulus path."""
    span = 180 / LEVELS
    start, end = 180 - (i - 1) * span - gap / 2, 180 - i * span + gap / 2
    x1, y1 = _point(cx, cy, outer, start)
    x2, y2 = _point(cx, cy, outer, end)
    x3, y3 = _point(cx, cy, inner, end)
    x4, y4 = _point(cx, cy, inner, start)
    return (f"M{x1:.2f},{y1:.2f} A{outer},{outer} 0 0 1 {x2:.2f},{y2:.2f} L{x3:.2f},{y3:.2f} "
            f"A{inner},{inner} 0 0 0 {x4:.2f},{y4:.2f} Z")


def svg(level: int | None, test_run: bool = False, size: str = "large", label: str = "") -> Markup:
    """The dial as inline SVG. `label` is its accessible name (the words shown beside it)."""
    width = SIZES[size]
    cx, cy, outer, inner = 100, 100, 92, 58
    uid = next(_ids)
    parts = [f'<svg class="dial dial-{size}" width="{width}" height="{width // 2 + 4}" viewBox="0 0 200 104" '
             f'role="img" aria-label="{Markup.escape(label)}" xmlns="http://www.w3.org/2000/svg">']
    if test_run:
        parts.append(f'<defs><pattern id="hatch{uid}" width="8" height="8" patternUnits="userSpaceOnUse" '
                     f'patternTransform="rotate(45)"><rect width="8" height="8" fill="none"/>'
                     f'<line x1="0" y1="0" x2="0" y2="8" stroke="#ffffff" stroke-width="3"/></pattern></defs>')
    for i in range(1, LEVELS + 1):
        d = _segment(i, cx, cy, outer, inner, 3)
        fill = SHADES[i - 1] if level is not None else EMPTY
        mark = f' stroke="{NEEDLE}" stroke-width="3"' if i == level else ""  # the run's level is outlined too
        parts.append(f'<path class="seg seg-{i}{" current" if i == level else ""}" d="{d}" fill="{fill}"{mark}/>')
        if test_run:
            parts.append(f'<path d="{d}" fill="url(#hatch{uid})"/>')
    if level is not None:
        if not 1 <= level <= LEVELS:
            raise ValueError(f"evidence level {level} is outside 1 to {LEVELS}")
        angle = 180 - (level - 0.5) * 180 / LEVELS
        x, y = _point(cx, cy, inner - 6, angle)  # ends inside the ring, so it shows on any shade
        parts.append(f'<line class="needle" x1="{cx}" y1="{cy}" x2="{x:.2f}" y2="{y:.2f}" stroke="{NEEDLE}" '
                     f'stroke-width="5" stroke-linecap="round"/>')
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="{NEEDLE}"/>')
    parts.append("</svg>")
    return Markup("".join(parts))
