"""The results statement (step 8b fix round 1; owner's decision A, with the owner's changes of 2026-10-07; register
'results_statement').

Code writes a short fixed statement for every completed run from what code stored: the question as asked (the
claim's words) and as tested (`pipeline.reading`), the outcome and verdict wording, the evidence level, the model
sentence, the pooled estimate with its unit, the p-value phrase and the four paper figures together, the spread of
the slope information, one sensitivity line, the calibration summary, and the main cautions chosen by fixed rules:

- with a verdict, always: the result is an association under the stated model in the sources searched; it does
  not show cause;
- either calibration finds the method over-confident on data like these (which describes the method, not the error
  of this particular p-value);
- with a p-value only: a source, or a sensitivity set, not in agreement with the pooled result;
- the result is exploratory.

Below the minimums, and when nothing was frozen, each count is shown against its minimum, with the records found
per source and how many lack the predictor or the outcome. A partly-sufficient original shows its candidate counts
per part of the question and the narrower question, which a person must dispatch.

The statement is rendered from the stored rows whenever it is shown (owner, 2026-10-07): `facts` reads them into a
plain dictionary with no record identity, and `render` is a pure function of that dictionary, ordering sources and
sensitivity sets itself, so the same stored rows always give the same text whatever the record ids or the order the
rows come in. Its numbers come only from stored results and cannot change. Its wording is always the current format's
(`FORMAT_VERSION`), never the format the run was completed under (owner's decision after the re-check): the statement
ends with "Statement format N." and, when the run was completed under another format (recorded on the run), "This
run was completed under format M." A change of wording is a new format (tests/test_statement.py pins the current
format's rendered text). It is present for every completed run,
whatever happened to the Analyst, and holds nothing a model wrote. The Analyst's explanation is stored and shown
separately, under its own label (`agents.analyst.LABEL`).
"""
from __future__ import annotations

from typing import Any, Mapping

import json

from sqlalchemy import Connection, Engine, text

from hypocurate.pipeline import analyst_names as an
from hypocurate.pipeline import display, queries, reading
from hypocurate.pipeline import statistics as st

# The statement's format: change it with any change of wording (owner, 2026-10-07; register 'results_statement').
# Every statement is rendered with the current format, whatever format its run was completed under (owner, after the
# re-check): the format is shown, with the run's own when it differs. 2: the not-fitted branch, the spread line
# whenever its figures exist, and the format lines (re-check, 2026-10-07).
FORMAT_VERSION = 2
ASSOCIATION = "The result is an association under the stated model in the sources searched; it does not show cause."
OVER_CONFIDENT = ("The simulation check found the method over-confident on data with this structure; that describes "
                  "the method on data like these, not the error of this particular p-value.")
EXPLORATORY = "Exploratory: the minimums were waived (use what is available); the validity checks were not."
NONE = "Main cautions: none beyond those above."
DISPATCH = "It is not run until a person dispatches it."
MINIMUM_WORDS = {"records": "records", "alloys": "alloys with at least 2 grain sizes", "groups": "informative groups",
                 "resid_df": "residual degrees of freedom"}
MINIMUM_ORDER = ("records", "alloys", "groups", "resid_df")
LACKING = ("grain_size", "yield_strength")  # the predictor and the outcome


def _source_name(key: str) -> str:
    from hypocurate.sources.versions import SOURCES
    d = SOURCES.get(key)
    return d.name if d is not None else key


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def _output(conn: Connection, run_id: int, stage: str) -> Any:
    return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = :s AND status = 'done' "
                             "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).scalar_one_or_none()


# --- reading the stored rows -----------------------------------------------------------------------------------

IDENTITY_KEYS = ("records_found",)  # stored lists of record ids: never part of the facts


def _without_identity(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _without_identity(v) for k, v in value.items() if k not in IDENTITY_KEYS}
    if isinstance(value, list):
        return [_without_identity(v) for v in value]
    return value


def facts(conn: Connection, run_id: int) -> dict | None:
    """What the statement is rendered from, as plain JSON values with no record identity; None unless completed."""
    run = conn.execute(text(
        "SELECT r.status, r.outcome, r.verdict, r.exploratory, r.evidence_level, r.statement_format_version, hv.text "
        "FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id WHERE r.id = :r"),
        dict(r=run_id)).one()
    if run.status != "completed":
        return None
    out = {"claim": run.text, "tested": reading.stored(conn, run_id), "outcome": run.outcome,
           "verdict": run.verdict, "exploratory": run.exploratory, "evidence_level": run.evidence_level,
           "recorded_format_version": run.statement_format_version}
    if run.outcome == "partly_sufficient":
        out["narrowing"] = _output(conn, run_id, "narrowing") or {}
        out["narrower_number"] = conn.execute(text("SELECT number FROM hypothesis WHERE narrower_of_run_id = :r "
                                                   "ORDER BY id LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
        return _without_identity(json.loads(json.dumps(out, default=str)))
    plan = conn.execute(text("SELECT content FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar_one()
    model = plan.get("model") or {}
    out.update(statistics=_output(conn, run_id, "statistics") or {}, gap=_output(conn, run_id, "gap_facts") or {},
               alpha=model.get("alpha"), alternative=model.get("alternative"),
               found=dict(conn.execute(text(
                   "SELECT s.key, count(*) FROM record r JOIN source_version sv ON sv.id = r.source_version_id "
                   "JOIN source s ON s.id = sv.source_id WHERE r.extraction_run_id = :r GROUP BY s.key"),
                   dict(r=run_id)).all()))
    return _without_identity(json.loads(json.dumps(out, default=str)))


# --- the pure rendering ------------------------------------------------------------------------------------------

def counts_against_minimums(minimums: Mapping[str, Mapping]) -> str:
    parts = []
    for key in MINIMUM_ORDER:
        m = minimums.get(key)
        if m is None:
            continue
        if key == "resid_df" and (m.get("count") or 0) <= 0:
            parts.append(f"no residual degrees of freedom (minimum {m['minimum']})")
        else:
            parts.append(f"{m['count']} of {m['minimum']} {MINIMUM_WORDS[key]}")
    return "Counts against the minimums: " + "; ".join(parts) + "."


def _found_lines(found: Mapping[str, int], gap: Mapping) -> list[str]:
    lacking = gap.get("records_lacking_fields") or {}
    lines = []
    for s in sorted(gap.get("sources") or [], key=lambda s: s["source"]):
        key = s["source"]
        parts = [f"{found.get(key, 0):,} records found"]
        for field in LACKING:
            n = (lacking.get(key) or {}).get(field)
            if n:
                parts.append(f"{n:,} {'lacks' if n == 1 else 'lack'} a {field.replace('_', ' ')}")
        lines.append(f"  {_source_name(key)}: " + "; ".join(parts) + ".")
    return lines


def _over_confident(calibration: Mapping) -> bool:
    return any(isinstance(c, Mapping) and c.get("status") == "computed" and c.get("confidence_flag") == "over_confident"
               for c in calibration.values())


def _ordered(analyses: list) -> list[Mapping]:
    """Pooled first, then the sources by key, then the sensitivity sets by key: never the stored order."""
    rank = {"pooled": 0, "per_source": 1, "sensitivity": 2}
    return sorted((e for e in analyses if isinstance(e, Mapping)),
                  key=lambda e: (rank.get(e.get("scope"), 3), str(e.get("source") or ""), str(e.get("set") or "")))


def _sensitivity_line(sets: list[Mapping], pooled: Mapping, alpha: float) -> str | None:
    estimated = [e["estimate"] for e in sets if e.get("estimate") is not None]
    if not sets or not estimated:
        return None
    agree = sum(1 for e in sets if st.label(e, pooled, alpha) == "agrees")
    return (f"Sensitivity: {agree} of {len(sets)} sets in agreement with the pooled result; estimates from "
            f"{display.coefficient(min(estimated))} to {display.coefficient(max(estimated))}.")


def pooled_not_fitted(pooled: Mapping) -> bool:
    """Validity check 1 failed: no coefficient was fitted, so no number of it exists to show (re-check)."""
    return pooled.get("estimate") is None


def _spread_line(c: Mapping) -> str | None:
    """The spread of the slope information, compared only with the run's own informative-group count."""
    if c.get("effective_papers") is None or c.get("largest_paper_share") is None or not c.get("n_groups_informative"):
        return None
    return (f"Spread of the slope information: an effective number of groups of "
            f"{display.two_decimals(c['effective_papers'])} out of {c['n_groups_informative']} informative groups; "
            f"largest share {display.percent(c['largest_paper_share'])}.")


def format_lines(recorded: int | None) -> list[str]:
    """The format the statement is rendered in, and the run's own when it differs (owner, after the re-check)."""
    lines = [f"Statement format {FORMAT_VERSION}."]
    if recorded is None:
        lines.append("The format this run was completed under was not recorded.")
    elif recorded != FORMAT_VERSION:
        lines.append(f"This run was completed under format {recorded}.")
    return lines


def _analysis_lines(f: Mapping) -> list[str]:
    stats, gap, alpha = f["statistics"], f["gap"], f["alpha"]
    analyses = _ordered(stats.get("analyses") or [])
    withheld = bool(stats.get("withheld"))
    lines: list[str] = []
    cautions: list[str] = []
    if f["verdict"]:
        cautions.append(ASSOCIATION)
    if not analyses:
        lines.append(f"Nothing was tested: no dataset was frozen ({str(gap.get('kind') or 'no record').replace('_', ' ')}).")
        lines.append(counts_against_minimums(gap.get("minimums") or {}))
        lines += _found_lines(f["found"], gap)
    elif withheld:
        lines.append("No estimate is shown: the minimums were not met.")
        lines.append(counts_against_minimums(analyses[0].get("minimums") or {}))
        lines += _found_lines(f["found"], gap)
    elif pooled_not_fitted(analyses[0]):
        pooled = analyses[0]
        c = pooled.get("counts") or {}
        reason = str(pooled.get("inference_reason") or "coefficient not fitted").replace("_", " ")
        lines.append(f"No coefficient could be fitted ({reason}): no estimate, no uncertainty, no p-value and no "
                     f"verdict; of the {c.get('n_records_in_set')} records in the set, {c.get('n_records_not_used')} "
                     f"could not be used ({c.get('n_alloys_not_used')} alloys).")
        spread = _spread_line(c)
        if spread:
            lines.append(spread)
        lines.append(an.GROUP_DEFINITION)
    else:
        pooled = analyses[0]
        sets = [e for e in analyses if e.get("scope") == "sensitivity"]
        c = pooled.get("counts") or {}
        inference = pooled.get("p_value") is not None
        lines.append(an.MODEL_SENTENCE)
        where = f"{c.get('n_records')} records on {c.get('n_alloys')} alloys"
        if inference:
            figures = display.figures_phrase(c["n_groups_informative"], c["effective_papers"], c["largest_paper_share"],
                                             pooled["df"])
            lines.append(f"Pooled estimate: {display.coefficient(pooled['estimate'])}, standard error "
                         f"{display.coefficient(pooled['std_error'])}; {display.p_phrase(pooled['p_value'])}; {where}; "
                         f"from {figures}.")
        else:
            reason = str(pooled.get("inference_reason") or "no valid inference").replace("_", " ")
            lines.append(f"Pooled estimate: {display.coefficient(pooled['estimate'])}, the coefficient only ({reason}): "
                         f"no uncertainty, no p-value and no verdict; {where}.")
        note = an.direction_note(pooled.get("estimate"), f["alternative"])
        if note:
            lines.append(_cap(note) + ".")
        spread = _spread_line(c)  # whenever its figures exist, with or without inference (re-check)
        if spread:
            lines.append(spread)
        lines.append(an.GROUP_DEFINITION)
        if inference:
            sensitivity = _sensitivity_line(sets, pooled, alpha)
            if sensitivity:
                lines.append(sensitivity)
        calibration = pooled.get("calibration") or {}
        lines.append(an.calibration_summary(calibration, alpha).strip())
        if _over_confident(calibration):
            cautions.append(OVER_CONFIDENT)
        if inference:
            for e in analyses:
                if e.get("scope") == "per_source" and e.get("label") and e["label"] != "agrees":
                    cautions.append(f"{_source_name(e['source'])}: {an.label_words(e)}.")
            others = an.sensitivity_summary(analyses, pooled, alpha, withheld)["sensitivity_not_agreeing"]
            if others != "none":
                cautions.append(f"Sensitivity sets not in agreement with the pooled result: {others}.")
    if f["exploratory"]:
        cautions.append(EXPLORATORY)
    lines.append("Main cautions:" if cautions else NONE)
    lines += [f"  - {x}" for x in cautions]
    return lines


def _partly_lines(f: Mapping) -> list[str]:
    narrowing = f["narrowing"]
    names = an.narrowing_names(narrowing)
    counts = []
    for letter in an.LETTERS:
        if f"part_{letter}" not in names:
            break
        counts.append(f"{names[f'part_{letter}']}: {names[f'part_{letter}_records']}")
    lines = ["Records with a grain size and the outcome, per part of the question (candidates before any "
             "eligibility decision): " + "; ".join(counts) + "."]
    if f.get("narrower_number") is not None:
        lines.append(f"Narrower question {f['narrower_number']}: "
                     f"{queries.scope_in_words(narrowing.get('narrower_scope') or {})}. {DISPATCH}")
    return lines


def render(f: Mapping) -> list[str]:
    """The statement's lines: a pure function of `facts` (same facts, same text)."""
    lines = [f"Question as asked: {f['claim']}"]
    if f.get("tested"):
        lines.append(f"Question as tested ({f['tested']['label']}): {f['tested']['text']}.")
    if f["outcome"] == "partly_sufficient":
        d = f["narrowing"].get("decision") or {}
        lines.append(f"Outcome: {d.get('outcome_wording')}. The original question was not tested and has no verdict.")
        lines.append(f"Evidence level: {f['evidence_level']} ({d.get('evidence_level_wording')}).")
        return lines + _partly_lines(f) + format_lines(f["recorded_format_version"])
    d = f["statistics"].get("decision") or {}
    label = f" ({d['label']})" if d.get("label") else ""
    verdict = f"Verdict: {d['verdict_wording']}." if f["verdict"] else "No verdict."
    lines.append(f"Outcome: {d.get('outcome_wording')}{label}. {verdict}")
    lines.append(f"Evidence level: {f['evidence_level']} ({d.get('evidence_level_wording')}).")
    return lines + _analysis_lines(f) + format_lines(f["recorded_format_version"])


def build(engine: Engine, run_id: int) -> dict | None:
    """The statement of a completed run, or None for a run that is not completed: its lines and text, the format
    version it is rendered in, and the version recorded on the run when it completed (None if not recorded)."""
    with engine.connect() as conn:
        f = facts(conn, run_id)
    if f is None:
        return None
    lines = render(f)
    return {"lines": lines, "text": "\n".join(lines), "format_version": FORMAT_VERSION,
            "recorded_format_version": f["recorded_format_version"]}
