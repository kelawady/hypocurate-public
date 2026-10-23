"""Evidence states and the acceptance matrix (Sprint 2 pilot, PRD v1.2 R6, Section 4; owner, 2026-10-23).

Which S0 stands for a paper: the newest S0 under the prompt version, on the document named in STANDING_DOCUMENTS
when the paper has one (by the PDF's SHA-256, so the choice survives the bundle), else on any document of the paper
(register 'pilot_standing_s0').

The rules (each a state event by its named rule, never over a person's later event except where stated):
- R-ambiguous: a link the Extractor marked ambiguous, still 'proposed' by the extraction, becomes 'unresolved'.
- Findings by consequence (register 'pilot_findings_by_consequence'): a finding disputes its object when its
  consequence is re_extract or expert_review, or correction until a correction of a value of that observation is
  loaded; qualified_unresolved and search_target never change a state (they qualify it). A disputing finding stands
  against the object even when a person accepted it. When the correction is loaded, the rule returns the object to the
  state it had before the dispute (a person's acceptance included), and the other rules decide again.
- R-link-1: a same-table-row link, not ambiguous and still 'proposed', whose observation has a same-observation
  mapping accepted by a person to a compilation record of the same paper, is accepted by rule and marked as a
  re-report of that record.
- The derived rule (register 'pilot_observation_acceptance'): an extracted observation is accepted when it has a
  stated grain size and a stated yield strength (a number with a known unit, after any loaded correction; not
  figure-only, not a range), each with a provenance and not marked ambiguous; at least one accepted link between the
  two; every link and every mapping of it accepted, and at least one mapping; and no disputing finding on it, its
  links or its mappings. Otherwise it keeps its state, and `status` gives the first reason.

R-rereport and the survivor rule: an accepted observation with an accepted same-observation mapping is a re-report of
that compilation record and is counted once, the compilation record surviving; whether its values agree within 2 %
is reported with it (the person's acceptance resolved the identity; a disagreement is a qualifier). An accepted
observation with no such mapping is new. The primary set's extracted records are the new ones.

The freeze (S2) stores the event ids it relied on and re-checks, independently of `status`, that no record it puts in
the primary set has a non-accepted observation, mapping or link at those events (the freeze invariant)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

from hypocurate.db.retry import run_transaction
from hypocurate.scoring.score import TOLERANCE, quantity

PROMPT_VERSION = "v4"  # the owner's decision of 2026-10-23: the Reconciler, R6 and the H1 runs use v4 S0s only
# The S0 that stands for a paper with more than one document (owner, 2026-10-23): actamat.2014.08.026's reviewed
# manuscript (document fetched by program); the published version fetched as repair 1 gave identical evidence.
STANDING_DOCUMENTS = {
    "doi:10.1016/j.actamat.2014.08.026": "d4b1a23fd7d66a0d8f116aa7556fb2197264aafe19df3cd5bf2647d0a2d8d324",
}
R_AMBIGUOUS, R_FINDING, R_LINK_1, R_DERIVED = "r-ambiguous", "r6-finding", "r-link-1", "r6-derived"
DISPUTING = ("re_extract", "expert_review", "correction")  # 'correction' only until a correction is loaded
QUALIFYING = ("qualified_unresolved", "search_target")
MACHINE_RULES = ("extraction", "reconciler", "reconciler-check", R_AMBIGUOUS)  # S1: rules that read no person's event
CATEGORIES = ("accepted", "proposed", "unresolved", "disputed")


def standing_outputs(conn: Connection, prompt_version: str | None = None) -> list[tuple[str, int]]:
    rows = conn.execute(text(
        "SELECT d.doi_key, x.id, d.pdf_sha256 FROM extraction_output x "
        "JOIN document_parse p ON p.id = x.document_parse_id JOIN document d ON d.id = p.document_id "
        "JOIN evidence_snapshot s ON s.extraction_output_id = x.id AND s.name = 'S0' "
        "WHERE x.method->>'prompt_version' = :v ORDER BY d.doi_key, x.id DESC"), dict(v=prompt_version or PROMPT_VERSION)).all()
    out: dict[str, int] = {}
    for key, xid, sha in rows:
        if key not in out and STANDING_DOCUMENTS.get(key, sha) == sha:
            out[key] = xid
    return sorted(out.items())


@dataclass
class _World:
    """The objects of a set of outputs and their newest states (at a set of event ids, or now)."""
    observations: dict = field(default_factory=dict)   # obs id -> (output id, doi_key)
    values: dict = field(default_factory=dict)         # obs id -> {field: row}
    links: dict = field(default_factory=dict)          # obs id -> [row]
    mappings: dict = field(default_factory=dict)       # obs id -> [row]
    states: dict = field(default_factory=dict)         # (kind, id) -> (state, by_rule, by_person, event id)
    findings: list = field(default_factory=list)
    corrections: dict = field(default_factory=dict)    # value id -> newest correction row


def _load(conn: Connection, outputs: list[tuple[str, int]], event_ids: list[int] | None = None) -> _World:
    w = _World()
    xs = [x for _, x in outputs]
    key_of = {x: k for k, x in outputs}
    for o in conn.execute(text("SELECT id, extraction_output_id FROM candidate_observation "
                               "WHERE extraction_output_id = ANY(:x)"), dict(x=xs)).all():
        w.observations[o.id] = (o.extraction_output_id, key_of[o.extraction_output_id])
        w.values[o.id], w.links[o.id], w.mappings[o.id] = {}, [], []
    obs = list(w.observations)
    for v in conn.execute(text("SELECT id, observation_id, field, value_text, unit, provenance, ambiguous "
                               "FROM candidate_value WHERE observation_id = ANY(:o)"), dict(o=obs)).all():
        w.values[v.observation_id][v.field] = v
    for l in conn.execute(text("SELECT l.id, l.observation_id, l.kind, l.ambiguous, a.field AS af, b.field AS bf "
                               "FROM extraction_link l JOIN candidate_value a ON a.id = l.from_value_id "
                               "JOIN candidate_value b ON b.id = l.to_value_id WHERE l.observation_id = ANY(:o)"),
                          dict(o=obs)).all():
        w.links[l.observation_id].append(l)
    for m in conn.execute(text("SELECT id, observation_id, kind, compilation_key FROM reconciler_mapping "
                               "WHERE observation_id = ANY(:o)"), dict(o=obs)).all():
        w.mappings[m.observation_id].append(m)
    sql = ("SELECT DISTINCT ON (object_kind, object_id) object_kind, object_id, state, by_rule, by_person, id "
           "FROM evidence_state_event WHERE extraction_output_id = ANY(:x)"
           + (" AND id = ANY(:e)" if event_ids is not None else "") + " ORDER BY object_kind, object_id, id DESC")
    for s in conn.execute(text(sql), dict(x=xs, e=event_ids or [])).all():
        w.states[(s.object_kind, s.object_id)] = (s.state, s.by_rule, s.by_person, s.id)
    w.findings = conn.execute(text("SELECT id, object_kind, object_id, finding_kind, consequence, at FROM auditor_finding "
                                   "WHERE extraction_output_id = ANY(:x) ORDER BY id"), dict(x=xs)).all()
    for c in conn.execute(text("SELECT DISTINCT ON (value_id) id, value_id, corrected_text, unit, at FROM value_correction "
                               "WHERE value_id = ANY(:v) ORDER BY value_id, id DESC"),
                          dict(v=[v.id for vs in w.values.values() for v in vs.values()])).all():
        w.corrections[c.value_id] = c
    return w


def _state(w: _World, kind: str, oid: int) -> str:
    return w.states.get((kind, oid), ("proposed",))[0]


def _observation_of(w: _World, kind: str, oid: int) -> int | None:
    if kind == "observation":
        return oid
    pool = w.links if kind == "link" else w.mappings
    return next((o for o, rows in pool.items() if any(r.id == oid for r in rows)), None)


def disputing_findings(w: _World) -> dict[tuple[str, int], list]:
    """The findings that stand against an object, by object (findings by consequence)."""
    out: dict[tuple[str, int], list] = {}
    for f in w.findings:
        if f.consequence not in DISPUTING:
            continue
        if f.consequence == "correction":
            obs = _observation_of(w, f.object_kind, f.object_id)
            if obs is not None and any(v.id in w.corrections and w.corrections[v.id].at >= f.at
                                       for v in w.values[obs].values()):
                continue  # the correction it asks for is loaded
        out.setdefault((f.object_kind, f.object_id), []).append(f)
    return out


def _stated(w: _World, obs: int, f: str) -> tuple[bool, str]:
    v = w.values[obs].get(f)
    if v is None:
        return False, f"no {f.replace('_', ' ')}"
    c = w.corrections.get(v.id)
    q = quantity(f, c.corrected_text if c else v.value_text, (c.unit if c else v.unit))
    if q.kind == "figure":
        return False, f"figure-only {f.replace('_', ' ')}"
    if q.kind == "range":
        return False, f"{f.replace('_', ' ')} is a range"
    if q.kind != "number" or not q.unit_known:
        return False, f"{f.replace('_', ' ')} not a number with a known unit"
    if not v.provenance:
        return False, f"{f.replace('_', ' ')} without provenance"
    if v.ambiguous:  # an ambiguity note by the Extractor, or the verifier's answer other than 'yes'
        return False, f"{f.replace('_', ' ')} flagged ambiguous"
    return True, ""


def _accepted_same_observation(w: _World, obs: int):
    return next((m for m in w.mappings[obs] if m.kind == "same_observation" and _state(w, "mapping", m.id) == "accepted"
                 and w.states[("mapping", m.id)][2] is not None), None)


def derived_reason(w: _World, obs: int, disputes: dict) -> str | None:
    """None when the derived rule accepts the observation, else the first reason it does not."""
    for f in ("grain_size", "yield_strength"):
        ok, why = _stated(w, obs, f)
        if not ok:
            return why
    objects = [("observation", obs)] + [("link", l.id) for l in w.links[obs]] + [("mapping", m.id) for m in w.mappings[obs]]
    if any(o in disputes for o in objects):
        return "a finding disputes it"
    if any(_state(w, k, i) == "disputed" for k, i in objects[1:]):
        return "a link or mapping is disputed"
    if not any({l.af, l.bf} == {"grain_size", "yield_strength"} and _state(w, "link", l.id) == "accepted"
               for l in w.links[obs]):
        return "no accepted grain size - yield strength link"
    if any(_state(w, "link", l.id) != "accepted" for l in w.links[obs]):
        return "a link not accepted"
    if not w.mappings[obs]:
        return "no mapping"
    if any(_state(w, "mapping", m.id) != "accepted" for m in w.mappings[obs]):
        return "a mapping not accepted"
    return None


def _event(conn: Connection, kind: str, oid: int, out: int, state: str, rule: str, reason: str) -> None:
    conn.execute(text("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, by_rule, "
                      "reason) VALUES (:k, :o, :x, :s, :r, :why)"),
                 dict(k=kind, o=oid, x=out, s=state, r=rule, why=reason[:2000]))


def apply_rules(engine: Engine, outputs: list[tuple[str, int]]) -> dict:
    """Applies the rules in order, writing only events that change a state; returns counts per rule."""
    def run(conn: Connection) -> dict:
        n = {R_AMBIGUOUS: 0, R_FINDING: 0, R_LINK_1: 0, R_DERIVED: 0}
        w = _load(conn, outputs)
        out_of = {o: w.observations[o][0] for o in w.observations}
        for obs, links in w.links.items():
            for l in links:
                if l.ambiguous and w.states.get(("link", l.id), ("proposed", "extraction"))[:2] == ("proposed", "extraction"):
                    _event(conn, "link", l.id, out_of[obs], "unresolved", R_AMBIGUOUS, "the Extractor could not attribute "
                           "it to one specimen (R-ambiguous)")
                    n[R_AMBIGUOUS] += 1
        w = _load(conn, outputs)
        disputes = disputing_findings(w)
        for (kind, oid), st in list(w.states.items()):
            if st[0] == "disputed" and st[1] == R_FINDING and (kind, oid) not in disputes:
                obs = _observation_of(w, kind, oid)
                before = conn.execute(text("SELECT state FROM evidence_state_event WHERE object_kind = :k AND object_id = :o "
                                           "AND by_rule IS DISTINCT FROM :r ORDER BY id DESC LIMIT 1"),
                                      dict(k=kind, o=oid, r=R_FINDING)).scalar() or "proposed"
                _event(conn, kind, oid, out_of[obs], before, R_FINDING, "no finding disputes it any more (the correction "
                       f"it asked for is loaded): back to its state before the dispute, {before}")
                n[R_FINDING] += 1
        for (kind, oid), fs in disputes.items():
            obs = _observation_of(w, kind, oid)
            if obs is not None and _state(w, kind, oid) != "disputed":
                _event(conn, kind, oid, out_of[obs], "disputed", R_FINDING, "finding(s) " + ", ".join(
                    f"{f.id} ({f.finding_kind}, {f.consequence})" for f in fs) + " stand against it")
                n[R_FINDING] += 1
        w = _load(conn, outputs)
        for obs, links in w.links.items():
            m = _accepted_same_observation(w, obs)
            if m is None:
                continue
            for l in links:
                if l.kind == "same_table_row" and not l.ambiguous and _state(w, "link", l.id) == "proposed":
                    _event(conn, "link", l.id, out_of[obs], "accepted", R_LINK_1,
                           f"R-link-1: a table-row link in a paper the compilation used; re-report of {m.compilation_key}")
                    n[R_LINK_1] += 1
        w = _load(conn, outputs)
        disputes = disputing_findings(w)
        for obs in w.observations:
            if _state(w, "observation", obs) in ("proposed", "unresolved") and derived_reason(w, obs, disputes) is None:
                _event(conn, "observation", obs, out_of[obs], "accepted", R_DERIVED, "stated grain size and yield "
                       "strength with provenance; its links and mappings accepted; no finding disputes it")
                n[R_DERIVED] += 1
        return n
    return run_transaction(engine, run)


@dataclass(frozen=True)
class ObservationStatus:
    observation_id: int
    doi_key: str
    category: str                     # accepted / proposed / unresolved / disputed
    reason: str                       # why it is not accepted ('' when accepted)
    rereport_of: str | None = None    # the compilation record that survives, for an accepted re-report
    values_agree: bool | None = None  # grain size and yield strength within 2 % of that record (None: not compared)
    qualifiers: tuple = ()            # findings that qualify it without disputing it


def _agree(w: _World, obs: int, record) -> bool | None:
    if record is None:
        return None
    out = []
    for f, attr in (("grain_size", "grain_size"), ("yield_strength", "yield_strength")):
        v = w.values[obs].get(f)
        c = w.corrections.get(v.id) if v else None
        q = quantity(f, (c.corrected_text if c else v.value_text) if v else None, (c.unit if c else v.unit) if v else None)
        ref = record.harmonized[attr].value
        if q.kind != "number" or ref is None:
            return None
        ref = Decimal(str(ref))
        small = min(abs(q.low), abs(ref))
        out.append(abs(q.low - ref) <= TOLERANCE * small if small else q.low == ref)
    return all(out)


def status(conn: Connection, outputs: list[tuple[str, int]], compilation: dict | None = None,
           event_ids: list[int] | None = None) -> list[ObservationStatus]:
    """Every observation of the outputs with its category and reason, at the events given (default: now)."""
    w = _load(conn, outputs, event_ids)
    disputes = disputing_findings(w)
    qualifying: dict[int, list] = {}
    for f in w.findings:
        if f.consequence in QUALIFYING:
            obs = _observation_of(w, f.object_kind, f.object_id)
            if obs is not None:
                qualifying.setdefault(obs, []).append(f"finding {f.id}: {f.finding_kind}")
    result = []
    for obs, (_, key) in sorted(w.observations.items()):
        objects = [("observation", obs)] + [("link", l.id) for l in w.links[obs]] + [("mapping", m.id)
                                                                                    for m in w.mappings[obs]]
        states = {_state(w, k, i) for k, i in objects}
        own = _state(w, "observation", obs)
        if any(o in disputes for o in objects):
            cat, why = "disputed", "a finding disputes it"
        elif "disputed" in states:
            cat, why = "disputed", ("disputed" if own == "disputed" else "a link or mapping is disputed")
        elif own == "accepted" and states == {"accepted"}:
            cat, why = "accepted", ""
        else:
            cat = "unresolved" if "unresolved" in states else "proposed"
            why = derived_reason(w, obs, disputes) or "not yet evaluated by the rules"
        m = _accepted_same_observation(w, obs) if cat == "accepted" else None
        record = (compilation or {}).get(m.compilation_key) if m else None
        result.append(ObservationStatus(obs, key, cat, why, m.compilation_key if m else None,
                                        _agree(w, obs, record) if m else None, tuple(qualifying.get(obs, ()))))
    return result


def counts(statuses: list[ObservationStatus]) -> dict:
    """Observations by category and reason (the workbook's and the inventory's counts; owner, 2026-10-23)."""
    out: dict = {c: {} for c in CATEGORIES}
    for s in statuses:
        r = s.reason or ("re-report (compilation record survives)" if s.rereport_of else "new")
        out[s.category][r] = out[s.category].get(r, 0) + 1
    return out


def primary_extracted(statuses: list[ObservationStatus]) -> list[ObservationStatus]:
    """The extracted records the primary set adds: accepted and new (a re-report is counted once, as the compilation's
    record)."""
    return [s for s in statuses if s.category == "accepted" and s.rereport_of is None]


class FreezeRefused(RuntimeError):
    pass


def check_invariant(conn: Connection, event_ids: list[int], observation_ids: list[int]) -> list[str]:
    """The freeze invariant, read directly from the events (not from `status`): for every observation given, the
    observation, each of its links and each of its mappings has 'accepted' as its newest state among the events."""
    rows = conn.execute(text(
        "WITH objs AS (SELECT 'observation' AS k, o.id AS i, o.id AS obs FROM candidate_observation o "
        "WHERE o.id = ANY(:o) UNION ALL SELECT 'link', l.id, l.observation_id FROM extraction_link l "
        "WHERE l.observation_id = ANY(:o) UNION ALL SELECT 'mapping', m.id, m.observation_id FROM reconciler_mapping m "
        "WHERE m.observation_id = ANY(:o)) "
        "SELECT objs.k, objs.i, objs.obs, (SELECT e.state FROM evidence_state_event e WHERE e.object_kind = objs.k "
        "AND e.object_id = objs.i AND e.id = ANY(:e) ORDER BY e.id DESC LIMIT 1) AS state FROM objs"),
        dict(o=observation_ids, e=event_ids)).all()
    return [f"observation {r.obs}: {r.k} {r.i} is {r.state or 'without a state'}" for r in rows if r.state != "accepted"]


@dataclass
class Frozen:
    s1: int
    s2: int
    events_sha256: str
    event_ids: list[int]
    statuses: list[ObservationStatus]
    primary: list[ObservationStatus]
    accepted: list[ObservationStatus]


def _snapshot(conn: Connection, name: str, ids: list[int], by: str) -> tuple[int, str]:
    ids = sorted(set(ids))
    sha = hashlib.sha256(",".join(map(str, ids)).encode()).hexdigest()
    sid = conn.execute(text("INSERT INTO evidence_snapshot (name, event_ids, events_sha256, taken_by) VALUES "
                            "(:n, :e, :h, :b) RETURNING id"), dict(n=name, e=ids, h=sha, b=by)).scalar_one()
    return sid, sha


def freeze(engine: Engine, outputs: list[tuple[str, int]], by: str, compilation: dict | None = None,
           _status=None) -> Frozen:
    """S1 (the events by rules that read no person's event) and S2 (every event of the outputs now), in one
    transaction; refused when the invariant fails for any accepted record."""
    def run(conn: Connection) -> Frozen:
        xs = [x for _, x in outputs]
        conn.execute(text("SELECT id FROM extraction_output WHERE id = ANY(:x) ORDER BY id FOR UPDATE"), dict(x=xs))
        events = conn.execute(text("SELECT id, by_rule FROM evidence_state_event WHERE extraction_output_id = ANY(:x) "
                                   "ORDER BY id"), dict(x=xs)).all()
        s2_ids = [e.id for e in events]
        statuses = (_status or status)(conn, outputs, compilation, s2_ids)
        accepted = [s for s in statuses if s.category == "accepted"]
        problems = check_invariant(conn, s2_ids, [s.observation_id for s in accepted])
        if problems:
            raise FreezeRefused("the freeze invariant fails: " + "; ".join(problems[:20]))
        s1, _ = _snapshot(conn, "S1", [e.id for e in events if e.by_rule in MACHINE_RULES], by)
        s2, sha = _snapshot(conn, "S2", s2_ids, by)
        return Frozen(s1, s2, sha, s2_ids, statuses, primary_extracted(statuses), accepted)
    return run_transaction(engine, run)
