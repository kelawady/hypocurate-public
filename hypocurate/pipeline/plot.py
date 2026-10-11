"""The plot of a run (PRD 9.4; build step 10b; owner's answer of 2026-10-11): built on request from stored rows, never
stored (the artifact table stays unused in sprint 1).

**What it shows.** Every record the run found that has a grain size and the outcome: its own outcome value (MPa)
against grain size^-1/2 (µm^-1/2). Marker shape by source; a filled marker for a record in the test (the primary set),
a cross for a record used only in a sensitivity set, a hollow marker for a record not used. When the test fitted a
coefficient that is shown (not withheld below the minimums), each alloy in the test gets a line segment over its own
grain-size range, all with the stored slope k: the alloy's baseline is its mean outcome minus k times its mean
grain size^-1/2, the arithmetic of the fit with one baseline per alloy. With no coefficient, or below the minimums,
there are no lines and the reason is stated; with no dataset frozen there is no plot.

**What it is built from.** The run's stored records, its analysis sets and its stored statistics output, read in one
snapshot; alloys are grouped by `eligibility.alloy` with the primary set's own rounding (as the statistics stage
groups them), and the records' values are projected as the access layer projects them for the statistics stage.
Nothing is fitted here: k is the stored estimate. The plot states its format and the code version that built it.
"""
from __future__ import annotations

import math
import os
from collections import defaultdict
from typing import Mapping

from markupsafe import Markup
from sqlalchemy import Engine, text

from hypocurate.pipeline import display
from hypocurate.pipeline.run_view import snapshot

PLOT_FORMAT = 1
# Marker shapes by source (in the order of the run's sources), and how a record was used.
SHAPES = ("circle", "triangle", "square", "diamond")
USED, SENSITIVITY_ONLY, NOT_USED = "used in the test", "used only in a sensitivity set", "not used"
W, H = 720, 460
LEFT, RIGHT, TOP, BOTTOM = 84, 20, 20, 64
FONT = 16  # SVG units; the plot is never drawn narrower than 540 px (style.css), so text stays at least 12 px


def code_version() -> str:
    """The code version that built the plot, as /health reports it (Render's commit), else "unknown"."""
    return os.environ.get("RENDER_GIT_COMMIT", "") or "unknown"


def version_line(kind: str, fmt: int) -> str:
    return f"{kind} format {fmt}; built by code version {code_version()}."


def _ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    span = hi - lo or 1.0
    raw = span / n
    mag = 10 ** math.floor(math.log10(raw))
    step = min((s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= raw), default=raw)
    start = math.ceil(lo / step) * step
    out, v = [], start
    while v <= hi + 1e-9:
        out.append(round(v, 10))
        v += step
    return out


def data(engine: Engine, run_id: int) -> dict | None:
    """The plot's points, segments and words, from one snapshot; None for an unknown run."""
    from hypocurate.access.fields import _composition, _number
    from hypocurate.pipeline import eligibility as el
    from hypocurate.sources.versions import SOURCES
    with snapshot(engine) as conn:
        run = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).one_or_none()
        if run is None:
            return None
        frozen = conn.execute(text("SELECT 1 FROM run_snapshot WHERE run_id = :r"), dict(r=run_id)).scalar()
        plan = conn.execute(text("SELECT content FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar_one_or_none()
        stats = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' AND "
                                  "status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
        if not frozen or plan is None:
            return {"plot": False, "reason": "No plot: no dataset was frozen, so nothing was tested."
                    if run.status in ("completed", "failed") else "No plot yet: the dataset is not frozen.",
                    "version": version_line("Plot", PLOT_FORMAT)}
        members: dict[str, set[int]] = defaultdict(set)
        for key, rid in conn.execute(text(
                "SELECT a.key, asr.record_id FROM analysis_set a JOIN analysis_set_record asr ON asr.analysis_set_id "
                "= a.id WHERE a.run_id = :r"), dict(r=run_id)).all():
            members[key].add(rid)
        rows = conn.execute(text(
            "SELECT r.id, s.key AS source, r.harmonized FROM record r JOIN source_version sv ON sv.id = "
            "r.source_version_id JOIN source s ON s.id = sv.source_id WHERE r.extraction_run_id = :r ORDER BY r.id"),
            dict(r=run_id)).all()
    outcome_field = (plan.get("variables") or {}).get("outcome", {}).get("field")
    decimals = el.settings(plan, el.PRIMARY).decimals
    primary = members.get(el.PRIMARY, set())
    others = set().union(*(v for k, v in members.items() if k != el.PRIMARY)) if members else set()
    sources = sorted({r.source for r in rows})
    points = []
    for r in rows:
        h = r.harmonized if isinstance(r.harmonized, Mapping) else {}
        gs, y = _number(h.get("grain_size")), _number(h.get(outcome_field))
        if gs is None or y is None or gs <= 0:
            continue
        composition = _composition(h.get("composition"))
        use = USED if r.id in primary else SENSITIVITY_ONLY if r.id in others else NOT_USED
        points.append({"x": gs ** -0.5, "y": y, "source": r.source, "use": use,
                       "alloy": el.alloy({"composition": composition}, decimals) if composition else None})
    pooled = next((a for a in (stats or {}).get("analyses") or [] if a.get("scope") == "pooled"), None)
    k, reason = None, None
    if pooled is None:
        reason = "No fitted lines: the statistics were not computed."
    elif (stats or {}).get("withheld") or pooled.get("withheld"):
        reason = "No fitted lines: the minimums were not met, so no estimate is shown."
    elif pooled.get("estimate") is None:
        reason = "No fitted lines: no coefficient could be fitted."
    else:
        k = pooled["estimate"]
    segments = []
    if k is not None:
        by_alloy: dict[str, list[dict]] = defaultdict(list)
        for p in points:
            if p["use"] == USED and p["alloy"]:
                by_alloy[p["alloy"]].append(p)
        for alloy, ps in sorted(by_alloy.items()):
            xs = [p["x"] for p in ps]
            if len(set(xs)) < 2:
                continue
            mx, my = sum(xs) / len(xs), sum(p["y"] for p in ps) / len(ps)
            base = my - k * mx
            segments.append({"x0": min(xs), "x1": max(xs), "y0": base + k * min(xs), "y1": base + k * max(xs)})
    names = {s: (SOURCES[s].name if s in SOURCES else s) for s in sources}
    return {"plot": True, "points": points, "segments": segments, "k": k, "reason": reason,
            "sources": [{"key": s, "name": names[s], "shape": SHAPES[i % len(SHAPES)]} for i, s in enumerate(sources)],
            "counts": {u: sum(1 for p in points if p["use"] == u) for u in (USED, SENSITIVITY_ONLY, NOT_USED)},
            "k_words": display.coefficient(k) if k is not None else None,
            "version": version_line("Plot", PLOT_FORMAT)}


def _marker(shape: str, x: float, y: float, use: str) -> str:
    r = 5
    if use == SENSITIVITY_ONLY:
        return (f'<path d="M{x - r},{y - r} L{x + r},{y + r} M{x - r},{y + r} L{x + r},{y - r}" stroke="#b45309" '
                f'stroke-width="2" fill="none"/>')
    fill = "#2457c5" if use == USED else "none"
    stroke = "#2457c5" if use == USED else "#7b8494"
    if shape == "circle":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
    if shape == "triangle":
        return (f'<path d="M{x:.1f},{y - r - 1:.1f} L{x + r + 1:.1f},{y + r:.1f} L{x - r - 1:.1f},{y + r:.1f} Z" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
    if shape == "square":
        return (f'<rect x="{x - r:.1f}" y="{y - r:.1f}" width="{2 * r}" height="{2 * r}" fill="{fill}" '
                f'stroke="{stroke}" stroke-width="1.5"/>')
    return (f'<path d="M{x:.1f},{y - r - 1:.1f} L{x + r + 1:.1f},{y:.1f} L{x:.1f},{y + r + 1:.1f} '
            f'L{x - r - 1:.1f},{y:.1f} Z" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')


def svg(d: Mapping) -> Markup:
    """The plot as inline SVG (axis words inside, at FONT units; the legend and the words are HTML beside it)."""
    pts = d["points"]
    if not pts:
        return Markup("")
    xs = [p["x"] for p in pts] + [s["x0"] for s in d["segments"]] + [s["x1"] for s in d["segments"]]
    ys = [p["y"] for p in pts] + [s["y0"] for s in d["segments"]] + [s["y1"] for s in d["segments"]]
    x0, x1 = 0.0, max(xs) * 1.05
    y0, y1 = min(0.0, min(ys)), max(ys) * 1.08
    px = lambda v: LEFT + (v - x0) / (x1 - x0 or 1) * (W - LEFT - RIGHT)  # noqa: E731
    py = lambda v: H - BOTTOM - (v - y0) / (y1 - y0 or 1) * (H - TOP - BOTTOM)  # noqa: E731
    shape = {s["key"]: s["shape"] for s in d["sources"]}
    out = [f'<svg class="plot" viewBox="0 0 {W} {H}" role="img" aria-label="Yield strength against grain size to the '
           f'power minus one half, one point per record" xmlns="http://www.w3.org/2000/svg" '
           f'font-family="system-ui, sans-serif" font-size="{FONT}">',
           f'<rect x="{LEFT}" y="{TOP}" width="{W - LEFT - RIGHT}" height="{H - TOP - BOTTOM}" fill="#ffffff" '
           f'stroke="#d8dde6"/>']
    for t in _ticks(x0, x1):
        out.append(f'<line x1="{px(t):.1f}" y1="{H - BOTTOM}" x2="{px(t):.1f}" y2="{H - BOTTOM + 6}" stroke="#5b6475"/>'
                   f'<text x="{px(t):.1f}" y="{H - BOTTOM + 24}" text-anchor="middle" fill="#5b6475">{t:g}</text>')
    for t in _ticks(y0, y1):
        out.append(f'<line x1="{LEFT - 6}" y1="{py(t):.1f}" x2="{LEFT}" y2="{py(t):.1f}" stroke="#5b6475"/>'
                   f'<text x="{LEFT - 10}" y="{py(t) + 5:.1f}" text-anchor="end" fill="#5b6475">{t:g}</text>')
    out.append(f'<text x="{(LEFT + W - RIGHT) / 2:.0f}" y="{H - 12}" text-anchor="middle" fill="#1d2330">grain size'
               f'<tspan baseline-shift="super" font-size="{FONT}">-1/2</tspan> (µm<tspan baseline-shift="super" '
               f'font-size="{FONT}">-1/2</tspan>)</text>')
    out.append(f'<text transform="translate(22,{(TOP + H - BOTTOM) / 2:.0f}) rotate(-90)" text-anchor="middle" '
               f'fill="#1d2330">yield strength (MPa)</text>')
    for s in d["segments"]:
        out.append(f'<line class="fit" x1="{px(s["x0"]):.1f}" y1="{py(s["y0"]):.1f}" x2="{px(s["x1"]):.1f}" '
                   f'y2="{py(s["y1"]):.1f}" stroke="#1d3f78" stroke-width="2"/>')
    for use in (NOT_USED, SENSITIVITY_ONLY, USED):  # used records drawn last, on top
        for p in pts:
            if p["use"] == use:
                out.append(_marker(shape[p["source"]], px(p["x"]), py(p["y"]), use))
    out.append("</svg>")
    return Markup("".join(out))


def legend(d: Mapping) -> list[str]:
    """The legend in words (HTML beside the plot)."""
    lines = [f"{s['name']}: {s['shape']}s" for s in d["sources"]]
    lines += [f"Filled: {USED} ({d['counts'][USED]}); crosses: {SENSITIVITY_ONLY} ({d['counts'][SENSITIVITY_ONLY]}); "
              f"hollow: {NOT_USED} ({d['counts'][NOT_USED]})."]
    if d["segments"]:
        lines.append(f"Lines: one per alloy in the test ({len(d['segments'])}), over its own grain sizes, each with the "
                     f"stored slope k = {d['k_words']}; an alloy's baseline is its own (one baseline per alloy).")
    elif d.get("reason"):
        lines.append(d["reason"])
    return lines
