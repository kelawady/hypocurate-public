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
# A fixed marker shape for each source (owner's screenshot review, 2026-10-11: never by order of appearance);
# a source not named here is drawn as a diamond.
SOURCE_SHAPES = {"mpea": "circle", "tamu_fcc": "triangle", "controlled_duplicates": "square"}
OTHER_SHAPE = "diamond"
USED, SENSITIVITY_ONLY, NOT_USED = "used in the test", "used only in a sensitivity set", "not used"
# The legend's words for "used" when the fit gave a coefficient only (owner's review, 2026-10-11).
USED_COEFFICIENT_ONLY = "used in the fit (coefficient only: no valid uncertainty, not a test)"
# Two drawings of the same plot (owner's review: it scales to the screen, axis words included): a wide one and a
# narrow one for a phone, each with its font chosen so that text is never below 12 px where it is shown (style.css:
# the wide one from 56rem, never narrower than 540 px; the narrow one below, on screens at least 360 px wide).
LAYOUTS = {"wide": {"w": 720, "h": 460, "left": 84, "right": 20, "top": 20, "bottom": 64, "font": 16, "r": 5,
                    "ticks": 5},
           "narrow": {"w": 320, "h": 300, "left": 72, "right": 10, "top": 12, "bottom": 52, "font": 14, "r": 4,
                      "ticks": 4}}
W, FONT = LAYOUTS["wide"]["w"], LAYOUTS["wide"]["font"]


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
    coefficient_only = k is not None and pooled.get("p_value") is None
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
            "coefficient_only": coefficient_only,
            "sources": [{"key": s, "name": names[s], "shape": SOURCE_SHAPES.get(s, OTHER_SHAPE)} for s in sources],
            "counts": {u: sum(1 for p in points if p["use"] == u) for u in (USED, SENSITIVITY_ONLY, NOT_USED)},
            "k_words": display.coefficient(k) if k is not None else None,
            "version": version_line("Plot", PLOT_FORMAT)}


def _marker(shape: str, x: float, y: float, use: str, r: float, source: str) -> str:
    """One record's marker, with its source and use as attributes (the tests read them)."""
    tag = f' class="pt" data-source="{source}" data-use="{use}"'
    if use == SENSITIVITY_ONLY:
        return (f'<path{tag} data-shape="cross" d="M{x - r:.1f},{y - r:.1f} L{x + r:.1f},{y + r:.1f} M{x - r:.1f},'
                f'{y + r:.1f} L{x + r:.1f},{y - r:.1f}" stroke="#b45309" stroke-width="2" fill="none"/>')
    fill = "#2457c5" if use == USED else "none"
    stroke = "#2457c5" if use == USED else "#7b8494"
    common = f'{tag} data-shape="{shape}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"'
    if shape == "circle":
        return f'<circle{common} cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>'
    if shape == "triangle":
        return (f'<path{common} d="M{x:.1f},{y - r - 1:.1f} L{x + r + 1:.1f},{y + r:.1f} '
                f'L{x - r - 1:.1f},{y + r:.1f} Z"/>')
    if shape == "square":
        return f'<rect{common} x="{x - r:.1f}" y="{y - r:.1f}" width="{2 * r}" height="{2 * r}"/>'
    return (f'<path{common} d="M{x:.1f},{y - r - 1:.1f} L{x + r + 1:.1f},{y:.1f} L{x:.1f},{y + r + 1:.1f} '
            f'L{x - r - 1:.1f},{y:.1f} Z"/>')


def view(d: Mapping) -> dict:
    """The axes' range (owner's review: limited to the records used and the sensitivity-only ones, and the lines) and
    how many records not used lie outside it."""
    shown = [p for p in d["points"] if p["use"] != NOT_USED]
    basis = shown or d["points"]
    xs = [p["x"] for p in basis] + [s["x0"] for s in d["segments"]] + [s["x1"] for s in d["segments"]]
    ys = [p["y"] for p in basis] + [s["y0"] for s in d["segments"]] + [s["y1"] for s in d["segments"]]
    x1, y1 = max(xs) * 1.05, max(ys) * 1.08
    y0 = min(0.0, min(ys))
    outside = sum(1 for p in d["points"] if p["use"] == NOT_USED and not (0 <= p["x"] <= x1 and y0 <= p["y"] <= y1))
    return {"x0": 0.0, "x1": x1, "y0": y0, "y1": y1, "outside": outside}


def svg(d: Mapping, layout: str = "wide") -> Markup:
    """The plot as inline SVG in one of `LAYOUTS` (axis words inside, at the layout's font; legend and words are HTML
    beside it). Records not used that lie outside the view are not drawn; `legend` says how many."""
    pts = d["points"]
    if not pts:
        return Markup("")
    L = LAYOUTS[layout]
    w, h, left, right, top, bottom, font, r = (L[k] for k in ("w", "h", "left", "right", "top", "bottom", "font", "r"))
    v = view(d)
    x0, x1, y0, y1 = v["x0"], v["x1"], v["y0"], v["y1"]
    px = lambda val: left + (val - x0) / (x1 - x0 or 1) * (w - left - right)  # noqa: E731
    py = lambda val: h - bottom - (val - y0) / (y1 - y0 or 1) * (h - top - bottom)  # noqa: E731
    out = [f'<svg class="plot plot-{layout}" viewBox="0 0 {w} {h}" role="img" aria-label="Yield strength against grain '
           f'size to the power minus one half, one point per record" xmlns="http://www.w3.org/2000/svg" '
           f'font-family="system-ui, sans-serif" font-size="{font}">',
           f'<rect x="{left}" y="{top}" width="{w - left - right}" height="{h - top - bottom}" fill="#ffffff" '
           f'stroke="#d8dde6"/>']
    for t in _ticks(x0, x1, L["ticks"]):
        out.append(f'<line x1="{px(t):.1f}" y1="{h - bottom}" x2="{px(t):.1f}" y2="{h - bottom + 5}" stroke="#5b6475"/>'
                   f'<text x="{px(t):.1f}" y="{h - bottom + font + 6}" text-anchor="middle" fill="#5b6475">{t:g}</text>')
    for t in _ticks(y0, y1, L["ticks"]):
        out.append(f'<line x1="{left - 5}" y1="{py(t):.1f}" x2="{left}" y2="{py(t):.1f}" stroke="#5b6475"/>'
                   f'<text x="{left - 8}" y="{py(t) + font / 3:.1f}" text-anchor="end" fill="#5b6475">{t:g}</text>')
    out.append(f'<text x="{(left + w - right) / 2:.0f}" y="{h - 8}" text-anchor="middle" fill="#1d2330">grain size'
               f'<tspan baseline-shift="super" font-size="{font}">-1/2</tspan> (µm<tspan baseline-shift="super" '
               f'font-size="{font}">-1/2</tspan>)</text>')
    out.append(f'<text transform="translate({font},{(top + h - bottom) / 2:.0f}) rotate(-90)" text-anchor="middle" '
               f'fill="#1d2330">yield strength (MPa)</text>')
    for seg in d["segments"]:
        out.append(f'<line class="fit" x1="{px(seg["x0"]):.1f}" y1="{py(seg["y0"]):.1f}" x2="{px(seg["x1"]):.1f}" '
                   f'y2="{py(seg["y1"]):.1f}" stroke="#1d3f78" stroke-width="2"/>')
    for use in (NOT_USED, SENSITIVITY_ONLY, USED):  # used records drawn last, on top
        for p in pts:
            if p["use"] != use or not (x0 <= p["x"] <= x1 and y0 <= p["y"] <= y1):
                continue
            out.append(_marker(SOURCE_SHAPES.get(p["source"], OTHER_SHAPE), px(p["x"]), py(p["y"]), use, r,
                               p["source"]))
    out.append("</svg>")
    return Markup("".join(out))


def legend(d: Mapping) -> list[str]:
    """The legend in words (HTML beside the plot)."""
    used = USED_COEFFICIENT_ONLY if d.get("coefficient_only") else USED
    lines = [f"{s['name']}: {s['shape']}s" for s in d["sources"]]
    lines += [f"Filled: {used} ({d['counts'][USED]}); crosses: {SENSITIVITY_ONLY} ({d['counts'][SENSITIVITY_ONLY]}); "
              f"hollow: {NOT_USED} ({d['counts'][NOT_USED]})."]
    outside = view(d)["outside"] if d["points"] else 0
    if outside:
        lines.append(f"The view shows the records used and the sensitivity-only ones; {outside} record"
                     f"{'' if outside == 1 else 's'} not used lie{'s' if outside == 1 else ''} outside it.")
    if d["segments"]:
        lines.append(f"Lines: one per alloy in the {'fit' if d.get('coefficient_only') else 'test'} "
                     f"({len(d['segments'])}), over its own grain sizes, each with the stored slope k = {d['k_words']}; "
                     f"an alloy's baseline is its own (one baseline per alloy).")
    elif d.get("reason"):
        lines.append(d["reason"])
    return lines
