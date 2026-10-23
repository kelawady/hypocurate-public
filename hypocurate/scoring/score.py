"""The scoring script, first version (Sprint 2 pilot, PRD v1.2 R7; the owner's rules of 2026-10-22 and 2026-10-23,
register 'pilot_scoring_rules').

Every table names the snapshot it was computed on (S0: the Extractor's verified, reference-blind output; S2 from
Saturday). It reads only the database (S0, annotation rows) and the compilation's sealed version; nothing it computes
is written back to S0.

Matching (one-to-one, within one paper):
- observations are grouped by paper, alloy (Sprint 1's same-alloy key), test type and test temperature (R-identity's
  normalization, the room-temperature band included);
- where both sides give a specimen label, the label decides; otherwise values decide: a prediction and an annotation
  row (or compilation record) pair when both grain size and yield strength agree, after converting known units, within
  Sprint 1's tolerance (2 per cent relative to the smaller); when the annotation marks a value 'figure only', the pair
  is matched on the other value alone, and the prediction must mark that value figure-only or ambiguous (a number
  there is a precision error, 'value asserted where the paper states none');
- processing-state text and location are reported per pair and listed when they differ, never matched;
- a second prediction agreeing with an already matched row is a duplicate (one hit, one duplicate, never two hits); a
  prediction whose grain size agrees with one row and yield strength with another is 'values from different specimens'
  (a link error); any other unmatched prediction is 'unmatched, pending adjudication' (wrong under strict precision,
  set aside under pending precision);
- a prediction marked as reporting another paper ('reported_from') is correct handling, outside recall and precision.

Recovery against the compilation (MPEA, no locations): the compilation records of the paper with both a grain size
and a yield strength (the others are counted in a note, never scored); the same grouping and value agreement; a compilation record
whose values the annotation states only in a figure or as a range leaves the denominator ('figure-only or range,
deferred'); for a paper without annotation that cannot be determined and every record counts (so labelled).
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.engine import Engine

from hypocurate.pipeline import profile
from hypocurate.pipeline.extraction import provenance as pv
from hypocurate.pipeline.extraction.identity import (ROOM_TEMPERATURE, alloy_key, temperature_key, test_type_key)
from hypocurate.pipeline.extraction.interface import ParsedDocument, Provenance
from hypocurate.documents.select import phase_field
from hypocurate.sources.normalize import doi_group_key

TOLERANCE = Decimal(str(profile.DUPLICATE_TOLERANCE))  # Sprint 1's 2 per cent (register 'values_disagree_tolerance')
# Known unit conversions to the compared units (owner, Q-B): strength to MPa, grain size to µm.
UNITS = {"yield_strength": {"mpa": Decimal(1), "gpa": Decimal(1000), "n/mm2": Decimal(1), "n/mm^2": Decimal(1)},
         "grain_size": {"µm": Decimal(1), "μm": Decimal(1), "um": Decimal(1), "micron": Decimal(1),
                        "microns": Decimal(1), "nm": Decimal("0.001"), "mm": Decimal(1000)}}
CANONICAL = {"yield_strength": "mpa", "grain_size": "µm"}
FIGURE_ONLY = "figure only"
FROM_METHODS = "from methods"  # the definition prompt v3 asks for a condition copied from the methods (owner, 2026-10-23)
# Per paper, a label every scoring table for that paper carries (owner, 2026-10-23); register 'pilot_annotation_notes'.
ANNOTATION_NOTES = {"doi:10.1080/21663831.2018.1553803": "annotator informed that grain sizes match the compilation"}
_NUM = r"(\d+(?:\.\d+)?)"
_RANGE = re.compile(rf"^[~∼≈]?\s*{_NUM}\s*(?:-|–|—|to)\s*[~∼≈]?\s*{_NUM}\s*([a-zA-Zµμ/^0-9]*)\s*$")
_ONE = re.compile(rf"^[~∼≈<>]?\s*{_NUM}\s*([a-zA-Zµμ/^0-9]*)\s*$")
# A stated uncertainty ('1198 ± 27') is not part of the value compared: the central value is (2026-10-23).
_UNCERTAINTY = re.compile(r"\s*(?:±|\+/-|\+-)\s*\d+(?:\.\d+)?")
# A condition whose text says it is not stated counts as not stated (2026-10-23).
_NOT_STATED = re.compile(r"\bnot\s+(?:stated|given|reported|specified)\b", re.I)


@dataclass(frozen=True)
class Quantity:
    """A value as the scorer compares it: a number, a range, figure-only, missing or unreadable. A number with an
    ambiguity note is compared like any other and carries the flag and where it came from (owner, 2026-10-23)."""
    kind: str  # 'number', 'range', 'figure', 'missing', 'unreadable'
    low: Decimal | None = None
    high: Decimal | None = None
    unit_known: bool = True
    flag: str | None = None  # 'verifier', 'no provenance', 'extractor' (from the stored ambiguity note), or None


def flag_of(note: str | None, ambiguous: bool) -> str | None:
    if not ambiguous:
        return None
    n = (note or "").casefold()
    if "verification:" in n:
        return "verifier"
    if n.startswith("the extractor gave no provenance"):
        return "no provenance"
    return "extractor"


def quantity(field_: str, text_: str | None, unit: str | None, *, ambiguous: bool = False,
             stated_as: str | None = None, note: str | None = None) -> Quantity:
    t = (text_ or "").strip()
    if stated_as and stated_as.strip().casefold() == FIGURE_ONLY or t.casefold().startswith(FIGURE_ONLY):
        return Quantity("figure")
    if not t:
        return Quantity("missing")
    t = _UNCERTAINTY.sub("", t)
    m = _RANGE.match(t.replace(",", ""))
    one = None if m else _ONE.match(t.replace(",", ""))
    flag = flag_of(note, ambiguous)
    if not (m or one):
        return Quantity("unreadable", flag=flag)
    inline = (m.group(3) if m else one.group(2)) or ""
    u = (unit or inline or CANONICAL[field_]).strip().casefold().replace(" ", "")
    factor = UNITS[field_].get(u)
    known = factor is not None
    factor = factor or Decimal(1)
    if m:
        lo, hi = Decimal(m.group(1)) * factor, Decimal(m.group(2)) * factor
        return Quantity("range", min(lo, hi), max(lo, hi), known, flag)
    v = Decimal(one.group(1)) * factor
    return Quantity("number", v, v, known, flag)


def close(a: Decimal, b: Decimal) -> bool:
    small = min(abs(a), abs(b))
    return abs(a - b) <= TOLERANCE * small if small else a == b


def agree(p: Quantity, a: Quantity) -> bool:
    """Same stated form and values within the tolerance (both ends of a range)."""
    if p.low is None or a.low is None:
        return False
    if (p.kind == "range") != (a.kind == "range"):
        return False
    return close(p.low, a.low) and close(p.high, a.high)


@dataclass
class Obs:
    side: str  # 'prediction', 'annotation', 'compilation'
    ref: str
    paper: str
    alloy: str
    test_type: str
    temperature: str
    label: str | None
    gs: Quantity
    ys: Quantity
    location: str = ""
    state: str = ""
    reported_from: str = "this paper"
    link_asserted: bool = False
    provenance_ok: bool | None = None
    units_as_written: dict = field(default_factory=dict)

    @property
    def group(self) -> tuple:
        return (self.paper, self.alloy, self.test_type, self.temperature)

    @property
    def flagged(self) -> bool:
        return bool(self.gs.flag or self.ys.flag)

    methods_context: bool = False  # a test condition copied from the methods (prompt v3's definition)
    annotator: str | None = None  # for an annotation row: the annotator as the file names them

    @property
    def condition_not_stated(self) -> bool:
        return not self.test_type or not self.temperature


    @property
    def cited(self) -> bool:
        return self.reported_from.strip().casefold() != "this paper"


def same_group(p: "Obs", r: "Obs") -> bool:
    """Same paper and alloy; a test type or temperature the prediction leaves empty does not block pairing, a stated
    and different one does (owner, 2026-10-23)."""
    return (p.paper == r.paper and p.alloy == r.alloy and (not p.test_type or p.test_type == r.test_type)
            and (not p.temperature or p.temperature == r.temperature))


def pair_ok(p: Obs, a: Obs) -> tuple[bool, str | None]:
    """Do p and a pair? (and, if they pair, a precision error for a figure-only value predicted as a number)."""
    if p.label and a.label:
        return p.label == a.label, None
    figure_err = None
    checks = []
    for name in ("gs", "ys"):
        pv_, av = getattr(p, name), getattr(a, name)
        if av.kind == "figure":
            if pv_.kind in ("number", "range"):
                figure_err = f"{'grain size' if name == 'gs' else 'yield strength'}: value asserted where the paper " \
                             f"states none"
            continue
        checks.append(agree(pv_, av))
    return (bool(checks) and all(checks)), figure_err


@dataclass
class Pair:
    prediction: str
    reference: str
    state_differs: bool
    location_differs: bool
    gs_correct: bool
    ys_correct: bool
    units_correct: bool
    link_correct: bool
    provenance_ok: bool | None
    figure_error: str | None
    flags: str | None = None  # where a matched value's ambiguity note came from
    condition_not_stated: bool = False


@dataclass
class PaperScore:
    paper: str
    reference: str  # 'annotation' or 'compilation'
    references: int = 0
    deferred: int = 0  # reference rows/records figure-only or range (left out of the denominator), or 'not determined'
    matched: int = 0
    pairs: list = field(default_factory=list)
    duplicates: list = field(default_factory=list)
    wrong_specimen: list = field(default_factory=list)
    pending: list = field(default_factory=list)
    cited_marked: list = field(default_factory=list)
    predictions: int = 0
    figure_errors: int = 0
    note: str | None = None
    flagged_unmatched: int = 0
    annotators: tuple = ()
    conditions_not_stated: int = 0  # own predictions with no test type or temperature (a prompt-quality signal)
    conditions_from_methods: int = 0  # own predictions carrying a condition copied from the methods

    def metrics(self) -> dict:
        own = self.predictions
        denominator = self.references - self.deferred
        strict_wrong = len(self.duplicates) + len(self.wrong_specimen) + len(self.pending) + self.figure_errors
        correct = sum(1 for p in self.pairs if p.figure_error is None)
        return {"paper": self.paper, "against": self.reference, "annotator": ", ".join(self.annotators) or None,
                "reference_rows": self.references,
                "deferred": self.deferred, "denominator": denominator, "matched": self.matched,
                "recall_or_recovery": _ratio(self.matched, denominator),
                "predictions_own": own, "cited_rows_marked": len(self.cited_marked),
                "precision_strict": _ratio(correct, own),
                "precision_pending": _ratio(correct, own - len(self.pending)),
                "duplicates": len(self.duplicates), "values_from_different_specimens": len(self.wrong_specimen),
                "unmatched_pending_adjudication": len(self.pending), "figure_value_asserted": self.figure_errors,
                "gs_value_correct": sum(p.gs_correct for p in self.pairs),
                "ys_value_correct": sum(p.ys_correct for p in self.pairs),
                "units_as_written_correct": sum(p.units_correct for p in self.pairs),
                "links_correct": sum(p.link_correct for p in self.pairs),
                "provenance_resolves": sum(1 for p in self.pairs if p.provenance_ok),
                "state_text_differs": sum(p.state_differs for p in self.pairs),
                "location_differs": sum(p.location_differs for p in self.pairs),
                "correct_but_flagged": sum(1 for p in self.pairs if p.flags and p.figure_error is None),
                "wrong_and_flagged": self.flagged_unmatched,
                "condition_not_stated": self.conditions_not_stated,
                "condition_from_methods": self.conditions_from_methods,
                "strict_errors": strict_wrong, "note": self.note}


def _ratio(a: int, b: int) -> str | None:
    return None if b <= 0 else f"{Decimal(a) / Decimal(b):.3f}"


def score_paper(predictions: list[Obs], references: list[Obs], against: str) -> PaperScore:
    paper = (predictions or references or [None])[0].paper if (predictions or references) else ""
    s = PaperScore(paper, against)
    refs = [r for r in references]
    own = [p for p in predictions if not p.cited]
    s.cited_marked = [p.ref for p in predictions if p.cited]
    s.predictions = len(own)
    s.conditions_not_stated = sum(1 for p in own if p.condition_not_stated)
    s.conditions_from_methods = sum(1 for p in own if p.methods_context)
    s.note = ANNOTATION_NOTES.get(paper)
    s.annotators = tuple(sorted({r.annotator for r in refs if r.annotator}))
    s.references = len(refs)
    s.deferred = sum(1 for r in refs if _deferred(r, against))
    # candidate pairs within each group, closest first
    candidates = []
    for p in own:
        for r in refs:
            if not same_group(p, r):
                continue
            ok, ferr = pair_ok(p, r)
            if ok:
                candidates.append((_distance(p, r), p.ref, r.ref, ferr))
    candidates.sort()
    taken_p, taken_r = set(), set()
    by_p = {p.ref: p for p in own}
    by_r = {r.ref: r for r in refs}
    for _, pr, rr, ferr in candidates:
        if pr in taken_p or rr in taken_r:
            continue
        taken_p.add(pr)
        taken_r.add(rr)
        p, r = by_p[pr], by_r[rr]
        if ferr:
            s.figure_errors += 1
        s.pairs.append(Pair(pr, rr, _norm(p.state) != _norm(r.state) and bool(r.state),
                            _norm(p.location) != _norm(r.location) and bool(r.location),
                            r.gs.kind == "figure" or agree(p.gs, r.gs), r.ys.kind == "figure" or agree(p.ys, r.ys),
                            all(p.units_as_written.get(k) for k in p.units_as_written) and p.gs.unit_known
                            and p.ys.unit_known, p.link_asserted, p.provenance_ok, ferr,
                            ", ".join(sorted({f for f in (p.gs.flag, p.ys.flag) if f})) or None,
                            p.condition_not_stated))
    # a reference left out of the denominator (figure-only or range) is never counted as recovered
    s.matched = sum(1 for pr in s.pairs if not _deferred(by_r[pr.reference], against))
    for p in own:
        if p.ref in taken_p:
            continue
        s.flagged_unmatched += p.flagged
        same = [r for r in refs if same_group(p, r)]
        if any(pair_ok(p, r)[0] for r in same):
            s.duplicates.append(p.ref)
        elif any(agree(p.gs, r.gs) for r in same) and any(agree(p.ys, r.ys) for r in same):
            s.wrong_specimen.append(p.ref)
        else:
            s.pending.append(p.ref)
    return s


def _deferred(r: Obs, against: str) -> bool:
    """Left out of the denominator: a compilation record the annotation states only in a figure or as a range (owner,
    Q-C); an annotation row with neither value stated as a number (nothing to match on)."""
    if against == "compilation":
        return r.gs.kind in ("figure", "range") or r.ys.kind in ("figure", "range")
    return r.gs.kind == "figure" and r.ys.kind == "figure"


def _distance(p: Obs, r: Obs) -> Decimal:
    d = Decimal(0)
    for name in ("gs", "ys"):
        a, b = getattr(p, name), getattr(r, name)
        if a.low is not None and b.low is not None and min(a.low, b.low):
            d += abs(a.low - b.low) / min(a.low, b.low)
    return d


def _norm(s: str | None) -> str:
    return " ".join((s or "").split()).casefold()


# --- reading the three sides -----------------------------------------------------------------------------------------

def predictions_s0(engine: Engine, output_id: int) -> tuple[list[Obs], dict]:
    """The S0 candidates of one extraction output (the verified output), with whether each value's provenance
    resolves in its parse. Returns the observations and the snapshot's description."""
    with engine.connect() as conn:
        snap = conn.execute(text("SELECT id, taken_at, events_sha256, raw_sha256 FROM evidence_snapshot "
                                 "WHERE name = 'S0' AND extraction_output_id = :x"), dict(x=output_id)).one()
        out = conn.execute(text("SELECT document_parse_id, method FROM extraction_output WHERE id = :x"),
                           dict(x=output_id)).one()
        document = ParsedDocument.load(conn, out.document_parse_id)
        rows = conn.execute(text(
            "SELECT o.id, o.identity, v.field, v.value_text, v.unit, v.provenance, v.ambiguous, v.ambiguity_note, v.definition "
            "FROM candidate_observation o "
            "JOIN candidate_value v ON v.observation_id = o.id WHERE o.extraction_output_id = :x "
            "AND o.id IN (SELECT object_id FROM evidence_state_event e WHERE e.id = ANY(:ids) AND object_kind = 'observation') "
            "ORDER BY o.id, v.id"),
            dict(x=output_id, ids=list(conn.execute(text("SELECT event_ids FROM evidence_snapshot WHERE id = :s"),
                                                    dict(s=snap.id)).scalar_one()))).all()
        links = {r[0]: r[1] for r in conn.execute(text(
            "SELECT l.observation_id, bool_or(NOT l.ambiguous) FROM extraction_link l JOIN candidate_value a ON "
            "a.id = l.from_value_id JOIN candidate_value b ON b.id = l.to_value_id WHERE "
            "ARRAY[a.field, b.field] <@ ARRAY['grain_size', 'yield_strength'] AND a.field <> b.field "
            "AND l.observation_id IN (SELECT id FROM candidate_observation WHERE extraction_output_id = :x) "
            "GROUP BY l.observation_id"), dict(x=output_id)).all()}
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r.id, json.dumps(r.identity))].append(r)
    obs = []
    for (oid, ident_json), values in grouped.items():
        ident = json.loads(ident_json)
        v = {x.field: x for x in values}
        prov_ok = []
        for f in ("grain_size", "yield_strength"):
            x = v.get(f)
            if x is not None and x.provenance:
                p = x.provenance
                try:
                    prov_ok.append(pv.problem(document, Provenance(p["page"], p["snippet"], p.get("table_index"),
                                                                   p.get("row_index"), p.get("sentence"))) is None)
                except ValueError:
                    prov_ok.append(False)
        units = {f: (v[f].unit is not None or bool(re.search(r"[a-zA-Zµμ]", v[f].value_text)))
                 for f in ("grain_size", "yield_strength") if f in v and v[f].value_text.strip().casefold() != FIGURE_ONLY}
        label = ident["specimen"][len("label:"):] if ident["specimen"].startswith("label:") else None
        # the group fields are recomputed from the stored values with the current identity rules (S0 is never changed)
        temp = v.get("test_temperature")
        obs.append(Obs("prediction", f"obs:{oid}", ident["paper"],
                       ident["alloy"] if ident["paper"].startswith("cited:") else
                       alloy_key(_t(v, "alloy"), _t(v, "composition")),
                       _condition(test_type_key(_t(v, "test_type")), _t(v, "test_type")),
                       _condition(temperature_key(_t(v, "test_temperature"), temp.unit if temp else None),
                                  _t(v, "test_temperature")), label,
                       quantity("grain_size", _t(v, "grain_size"), _u(v, "grain_size"), ambiguous=_a(v, "grain_size"),
                                note=_n(v, "grain_size")),
                       quantity("yield_strength", _t(v, "yield_strength"), _u(v, "yield_strength"),
                                ambiguous=_a(v, "yield_strength"), note=_n(v, "yield_strength")),
                       location=ident["specimen"], state=ident["processing_state"],
                       reported_from=ident.get("reported_from", "this paper"), link_asserted=bool(links.get(oid)),
                       provenance_ok=(all(prov_ok) if prov_ok else None), units_as_written=units,
                       methods_context=any(FROM_METHODS in (v[f].definition or "").casefold()
                                           for f in ("test_type", "test_temperature", "strain_rate") if f in v)))
    described = {"snapshot": "S0", "snapshot_id": snap.id, "taken_at": str(snap.taken_at),
                 "events_sha256": snap.events_sha256, "raw_sha256": snap.raw_sha256, "output": output_id,
                 "method": {k: out.method.get(k) for k in ("name", "version", "model", "prompt_version", "step")},
                 "verification": out.method.get("verification"),
                 "not_answered": (out.method.get("verification") or {}).get("not answered", 0)}
    return obs, described


def _condition(key: str, written: str | None) -> str:
    """'' (not stated) when the written condition says it is not stated; else its normalized key."""
    return "" if written and _NOT_STATED.search(written) else key


def _t(v, f):
    return v[f].value_text if f in v else None


def _u(v, f):
    return v[f].unit if f in v else None


def _a(v, f):
    return bool(v[f].ambiguous) if f in v else False


def _n(v, f):
    return v[f].ambiguity_note if f in v else None


def annotation_obs(engine: Engine, doi_key: str, annotator: str | None = None) -> list[Obs]:
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, identity, cells, annotator FROM annotation_row WHERE doi_key = :k "
                                 "ORDER BY annotation_file_id, row_number"), dict(k=doi_key)).all()
    out = []
    for r in rows:
        if annotator and r.annotator != annotator:
            continue
        ident, c = r.identity, r.cells
        label = ident["specimen"][len("label:"):] if ident["specimen"].startswith("label:") else None
        out.append(Obs("annotation", f"ann:{r.id}", ident["paper"], ident["alloy"], ident["test_type"],
                       ident["test_temperature"], label,
                       quantity("grain_size", c["grain_size_value"], c["grain_size_unit"],
                                stated_as=c.get("grain_size_stated_as")),
                       quantity("yield_strength", c["yield_strength_value"], c["yield_strength_unit"],
                                stated_as=c.get("yield_strength_stated_as")),
                       location=c.get("observation_location", ""), state=c.get("processing_state", ""),
                       annotator=r.annotator))
    return out


def compilation_obs(records: Iterable, doi_key: str, annotation: list[Obs] | None) -> tuple[list[Obs], str | None]:
    """The compilation's records of one paper, from an adapter's records (MPEA). Where the paper is annotated, a record
    whose values the annotation states only in a figure or as a range is marked so (left out of recovery's
    denominator); otherwise it cannot be determined, and the note says so."""
    out, without = [], 0
    for r in records:
        if not r.paper_doi or doi_group_key(r.paper_doi) != doi_key:
            continue
        h = r.harmonized
        if h[phase_field()].value not in profile.PHASE_CLASSES:
            continue  # the reach selection's rule (Sprint 1's FCC definition): only those records are scored
        if h["grain_size"].value is None or h["yield_strength"].value is None:
            without += 1  # not an H1 observation in the compilation: counted, never scored
            continue
        comp = h["composition"].value
        alloy = alloy_key(r.alloy) if not comp else alloy_key(None, "".join(f"{e}{v}" for e, v in sorted(comp.items())))
        gs = Quantity("number", Decimal(str(h["grain_size"].value)), Decimal(str(h["grain_size"].value))) \
            if h["grain_size"].value is not None else Quantity("missing")
        ys = Quantity("number", Decimal(str(h["yield_strength"].value)), Decimal(str(h["yield_strength"].value))) \
            if h["yield_strength"].value is not None else Quantity("missing")
        temp = h["test_temperature"].value
        out.append(Obs("compilation", f"cmp:{r.source_item_key}", doi_key, alloy, test_type_key(h["test_type"].value),
                       temperature_key(None if temp is None else str(temp), "°C"), None, gs, ys))
    notes = [f"{without} compilation record(s) of this paper lack a grain size or a yield strength: not scored"] \
        if without else []
    if annotation is None:
        notes.append("figure-only or range not determined (paper not annotated): every compilation record counts")
    else:
        stated = [a for a in annotation if a.gs.kind == "number" and a.ys.kind == "number"]
        for c in out:
            if not any(c.group == a.group and agree(c.gs, a.gs) and agree(c.ys, a.ys) for a in stated):
                c.ys = Quantity("figure") if c.ys.kind == "number" else c.ys  # stated only in a figure or as a range
    return out, "; ".join(notes) or None


def report(paper_scores: list[tuple[str, PaperScore]], described: dict) -> dict:
    """The tables, each naming its snapshot and method."""
    return {"snapshot": described, "rows": [s.metrics() | {"table": t} for t, s in paper_scores],
            "pairs": {t + ":" + s.paper: [asdict(p) for p in s.pairs] for t, s in paper_scores},
            "unmatched": {t + ":" + s.paper: {"duplicates": s.duplicates, "values_from_different_specimens":
                                              s.wrong_specimen, "pending_adjudication": s.pending,
                                              "cited_rows_marked": s.cited_marked} for t, s in paper_scores}}


def predictions_s2(engine: Engine, output_id: int, s2_snapshot_id: int | None = None) -> tuple[list[Obs], dict]:
    """The S2 predictions of one standing output (corrected performance; owner, 2026-10-23, register
    'pilot_s2_scoring'): S0's observations, less those disputed at the S2 snapshot (by a person, a standing finding,
    or through a link or mapping: R6's status), with the grain size and yield strength read through any correction
    loaded before that snapshot. Corrections of other fields are not read here (the scorer compares those two
    values). `s2_snapshot_id`: default the newest S2 that holds this output's events."""
    from hypocurate.pipeline import evidence as ev
    preds, described = predictions_s0(engine, output_id)
    with engine.connect() as conn:
        key = conn.execute(text("SELECT d.doi_key FROM extraction_output x JOIN document_parse p ON p.id = "
                                "x.document_parse_id JOIN document d ON d.id = p.document_id WHERE x.id = :x"),
                           dict(x=output_id)).scalar_one()
        snap = conn.execute(text(
            "SELECT id, taken_at, events_sha256, event_ids FROM evidence_snapshot WHERE name = 'S2' AND (CAST(:s AS bigint) IS NULL OR "
            "id = :s) AND EXISTS (SELECT 1 FROM evidence_state_event e WHERE e.id = ANY(event_ids) AND "
            "e.extraction_output_id = :x) ORDER BY id DESC LIMIT 1"), dict(s=s2_snapshot_id, x=output_id)).one()
        statuses = {s.observation_id: s for s in ev.status(conn, [(key, output_id)], event_ids=list(snap.event_ids))}
        corrected = {(r.observation_id, r.field): r for r in conn.execute(text(
            "SELECT DISTINCT ON (v.id) v.observation_id, v.field, c.corrected_text, c.unit FROM value_correction c "
            "JOIN candidate_value v ON v.id = c.value_id JOIN candidate_observation o ON o.id = v.observation_id "
            "WHERE o.extraction_output_id = :x AND c.at <= :t AND v.field IN ('grain_size', 'yield_strength') "
            "ORDER BY v.id, c.id DESC"), dict(x=output_id, t=snap.taken_at)).all()}
    kept, dropped, applied = [], 0, 0
    for p in preds:
        oid = int(p.ref.removeprefix("obs:"))
        if statuses.get(oid) is not None and statuses[oid].category == "disputed":
            dropped += 1
            continue
        for f, attr in (("grain_size", "gs"), ("yield_strength", "ys")):
            c = corrected.get((oid, f))
            if c is not None:
                setattr(p, attr, quantity(f, c.corrected_text, c.unit))
                applied += 1
        kept.append(p)
    return kept, described | {"snapshot": "S2", "snapshot_id": snap.id, "taken_at": str(snap.taken_at),
                              "events_sha256": snap.events_sha256, "dropped_disputed": dropped,
                              "corrections_applied": applied}
