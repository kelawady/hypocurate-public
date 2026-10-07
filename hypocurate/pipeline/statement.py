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

The statement is built from the stored rows whenever it is shown (`build`): it is present for every completed run,
whatever happened to the Analyst, and it holds nothing a model wrote. The Analyst's explanation is stored and shown
separately, under its own label (`agents.analyst.LABEL`).
"""
from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy import Connection, Engine, text

from hypocurate.pipeline import analyst_names as an
from hypocurate.pipeline import display, queries, reading
from hypocurate.pipeline import statistics as st

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


def _found_lines(conn: Connection, run_id: int, gap: Mapping) -> list[str]:
    found = dict(conn.execute(text(
        "SELECT s.key, count(*) FROM record r JOIN source_version sv ON sv.id = r.source_version_id "
        "JOIN source s ON s.id = sv.source_id WHERE r.extraction_run_id = :r GROUP BY s.key"), dict(r=run_id)).all())
    lacking = gap.get("records_lacking_fields") or {}
    lines = []
    for s in gap.get("sources") or []:
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


def _sensitivity_line(analyses: list[Mapping], pooled: Mapping, alpha: float) -> str | None:
    sets = [e for e in analyses if e.get("scope") == "sensitivity"]
    estimated = [e["estimate"] for e in sets if e.get("estimate") is not None]
    if not sets or not estimated:
        return None
    agree = sum(1 for e in sets if st.label(e, pooled, alpha) == "agrees")
    return (f"Sensitivity: {agree} of {len(sets)} sets in agreement with the pooled result; estimates from "
            f"{display.coefficient(min(estimated))} to {display.coefficient(max(estimated))}.")


def _analysis_lines(conn: Connection, run_id: int, run, stats: Mapping, gap: Mapping, alpha: float,
                    alternative: str | None) -> list[str]:
    analyses = [e for e in stats.get("analyses") or [] if isinstance(e, Mapping)]
    withheld = bool(stats.get("withheld"))
    frozen = bool(analyses)
    lines: list[str] = []
    cautions: list[str] = []
    if run.verdict:
        cautions.append(ASSOCIATION)
    if not frozen:
        lines.append(f"Nothing was tested: no dataset was frozen ({str(gap.get('kind') or 'no record').replace('_', ' ')}).")
        lines.append(counts_against_minimums(gap.get("minimums") or {}))
        lines += _found_lines(conn, run_id, gap)
    elif withheld:
        pooled = analyses[0]
        lines.append("No estimate is shown: the minimums were not met.")
        lines.append(counts_against_minimums(pooled.get("minimums") or {}))
        lines += _found_lines(conn, run_id, gap)
    else:
        pooled = analyses[0]
        c = pooled.get("counts") or {}
        lines.append(an.MODEL_SENTENCE)
        where = f"{c.get('n_records')} records on {c.get('n_alloys')} alloys"
        if pooled.get("p_value") is not None:
            lines.append(f"Pooled estimate: {display.coefficient(pooled['estimate'])}, standard error "
                         f"{display.coefficient(pooled['std_error'])}; {display.p_phrase(pooled['p_value'])}; {where}; "
                         f"from {display.figures_phrase(c['n_groups_informative'], c['effective_papers'], c['largest_paper_share'], pooled['df'])}.")
        else:
            reason = str(pooled.get("inference_reason") or "no valid inference").replace("_", " ")
            lines.append(f"Pooled estimate: {display.coefficient(pooled['estimate'])}, the coefficient only ({reason}): "
                         f"no uncertainty, no p-value and no verdict; {where}.")
        note = an.direction_note(pooled.get("estimate"), alternative)
        if note:
            lines.append(_cap(note) + ".")
        if pooled.get("p_value") is not None:
            lines.append(f"Spread of the slope information: an effective number of groups of "
                         f"{display.two_decimals(c['effective_papers'])} out of {c['n_groups_informative']} informative "
                         f"groups; largest share {display.percent(c['largest_paper_share'])}.")
        lines.append(an.GROUP_DEFINITION)
        if pooled.get("p_value") is not None:
            sensitivity = _sensitivity_line(analyses, pooled, alpha)
            if sensitivity:
                lines.append(sensitivity)
        calibration = pooled.get("calibration") or {}
        lines.append(an.calibration_summary(calibration, alpha).strip())
        if _over_confident(calibration):
            cautions.append(OVER_CONFIDENT)
        if pooled.get("p_value") is not None:
            for e in analyses:
                if e.get("scope") == "per_source" and e.get("label") and e["label"] != "agrees":
                    cautions.append(f"{_source_name(e['source'])}: {an.label_words(e)}.")
            others = an.sensitivity_summary(analyses, pooled, alpha, withheld)["sensitivity_not_agreeing"]
            if others != "none":
                cautions.append(f"Sensitivity sets not in agreement with the pooled result: {others}.")
    if run.exploratory:
        cautions.append(EXPLORATORY)
    lines.append("Main cautions:" if cautions else NONE)
    lines += [f"  - {x}" for x in cautions]
    return lines


def _partly_lines(conn: Connection, run_id: int, narrowing: Mapping) -> list[str]:
    names = an.narrowing_names(narrowing)
    counts = []
    for letter in an.LETTERS:
        if f"part_{letter}" not in names:
            break
        counts.append(f"{names[f'part_{letter}']}: {names[f'part_{letter}_records']}")
    lines = ["Records with a grain size and the outcome, per part of the question (candidates before any "
             "eligibility decision): " + "; ".join(counts) + "."]
    number = conn.execute(text("SELECT h.number FROM hypothesis h WHERE h.narrower_of_run_id = :r ORDER BY h.id "
                               "LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
    scope = narrowing.get("narrower_scope") or {}
    if number is not None:
        lines.append(f"Narrower question {number}: {queries.scope_in_words(scope)}. {DISPATCH}")
    return lines


def build(engine: Engine, run_id: int) -> dict | None:
    """The statement of a completed run ({"lines", "text"}), or None for a run that is not completed."""
    with engine.connect() as conn:
        run = conn.execute(text(
            "SELECT r.status, r.outcome, r.verdict, r.exploratory, r.evidence_level, hv.text FROM run r "
            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id WHERE r.id = :r"), dict(r=run_id)).one()
        if run.status != "completed":
            return None
        tested = reading.stored(conn, run_id)
        lines = [f"Question as asked: {run.text}"]
        if tested:
            lines.append(f"Question as tested ({tested['label']}): {tested['text']}.")
        if run.outcome == "partly_sufficient":
            narrowing = _output(conn, run_id, "narrowing") or {}
            d = narrowing.get("decision") or {}
            lines.append(f"Outcome: {d.get('outcome_wording')}. The original question was not tested and has no "
                         "verdict.")
            lines.append(f"Evidence level: {run.evidence_level} ({d.get('evidence_level_wording')}).")
            lines += _partly_lines(conn, run_id, narrowing)
        else:
            stats = _output(conn, run_id, "statistics") or {}
            gap = _output(conn, run_id, "gap_facts") or {}
            d = stats.get("decision") or {}
            plan = conn.execute(text("SELECT content FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar_one()
            model = plan.get("model") or {}
            label = f" ({d['label']})" if d.get("label") else ""
            verdict = f"Verdict: {d['verdict_wording']}." if run.verdict else "No verdict."
            lines.append(f"Outcome: {d.get('outcome_wording')}{label}. {verdict}")
            lines.append(f"Evidence level: {run.evidence_level} ({d.get('evidence_level_wording')}).")
            lines += _analysis_lines(conn, run_id, run, stats, gap, model.get("alpha"), model.get("alternative"))
    return {"lines": lines, "text": "\n".join(lines)}
