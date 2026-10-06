"""The analysis stage (PRD 5.7 to 5.10; build step 7): the statistics on the frozen sets, the
record of statistical significance, per-run calibration, the gap facts and the stored decision.

**Reads.** Statistics reads only through its access object (`dispatch.bind_code(…, "statistics")`),
which returns the frozen sets and, for their records only, what the model needs
(`frozen_analysis_data`), and only once the dataset is frozen. It never decides inclusion: every
set is used as frozen; the one rule it applies inside a fit is the model's own (alloys with two or
more distinct grain sizes among the analysis's records), reported as "not used in this fit". The
gap facts read through their own access object (`gap_facts`), which carries no outcome value.

**Computation** is a pure function of the frozen data and the locked plan (`analyse`): the same
inputs give the same numbers whatever the record ids or order. Every analysis (pooled, each source
within the primary set, each sensitivity set) goes through the same function. Per-source and
sensitivity results are descriptive and never change the verdict (register 'pooled_gives_verdict',
'sensitivity_one_change'); no adjustment is made for there being several.

**Writes.** One transaction under the run's lock (`writes.write`): the run must be at the
analysis stage (or closed without a freeze), with no result yet; the freeze fingerprint read must
be the run's. It writes `analysis_result` (pooled first), `calibration_result` (both methods per
analysis), and two code stage results: "statistics" (the record of statistical significance, PRD
5.9, and the decision) and "gap_facts" (data only; no report text). A marked run's rows and stage
results carry "test run: includes constructed data". The run itself is not completed here: the
decision is copied onto the run later by `completion.copy_decision`, unchanged.
"""
from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy import Connection, Engine, bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.access.dispatch import bind_code
from hypocurate.access.errors import AccessDenied
from hypocurate.access.inputs import role_input
from hypocurate.pipeline import calibration as cal
from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline import statistics as st
from hypocurate.pipeline.binding import record_identity
from hypocurate.pipeline.writes import TEST_RUN_LABEL, Refused, code_stage, log_refusal, marked, write
from hypocurate.sources.record import VALUE_STATUSES

ROLE = "statistics"


# --- Pure: from the frozen data and the locked plan ----------------------------------------------

class RecordsWithoutGroup(st.StatisticsError):
    """Records of a frozen set have no group (a paper not known): no group is invented (register
    'paper_grouping_by_doi'). The pooled analysis refuses; any other analysis is not analysed."""

    def __init__(self, n: int):
        self.n = n
        super().__init__("records_without_group")


def observations(records: list[Mapping], plan: Mapping, set_key: str) -> list[st.Observation]:
    """The records of one analysis as observations: alloy and group by the set's own settings
    (the same functions as Inclusion and the freeze counts), the stable identity as the sort key."""
    settings = el.settings(plan, set_key)
    without_group = sum(el.group(r, settings) is None for r in records)
    if without_group:
        raise RecordsWithoutGroup(without_group)
    out = []
    for r in records:
        group = el.group(r, settings)
        alloy = el.alloy(r, settings.decimals)
        if alloy is None or r["grain_size"] is None or r["outcome"] is None:
            raise st.StatisticsError("a record in a frozen set lacks its composition, grain size or outcome")
        out.append(st.Observation(record_identity(r["version_fingerprint"], r["origin"], r["item_index"]),
                                  alloy, group, r["grain_size"], r["outcome"]))
    return out


def _unavailable(reason: str) -> dict:
    return {"status": "unavailable", "reason": reason}


def _rates(c: Mapping) -> dict:
    """The detection rate beside the false-positive share, under one method's assumptions."""
    if c["status"] != "computed":
        return {"unavailable": c["reason"]}
    return {"detection": c["effect"]["share"], "detection_ci": [c["effect"]["ci_low"], c["effect"]["ci_high"]],
            "false_positive": c["null"]["share"], "false_positive_ci": [c["null"]["ci_low"], c["null"]["ci_high"]],
            "scatter": c["assumptions"]["scatter"], "shift": c["assumptions"]["shift"]}


def analyse(plan: Mapping, data: Mapping) -> dict:
    """Every analysis of the run, its calibrations, and the decision (the record of statistical
    significance). `data` is `frozen_analysis_data`."""
    by_id = {r["id"]: r for r in data["records"]}
    sources = {i: r["source"] for i, r in by_id.items()}
    transformation = plan["variables"]["predictor"]["transformation"]
    alpha = plan["model"]["alpha"]
    fp = data["freeze_fingerprint"]
    designs, entries, not_analysed = {}, [], []
    for key, scope, set_key, source in st.analyses_of(plan, data["sets"], sources):
        ids = [i for i in data["sets"][set_key] if source is None or sources[i] == source]
        try:
            designs[key] = st.design(observations([by_id[i] for i in ids], plan, set_key), transformation)
        except RecordsWithoutGroup as missing:
            if scope == "pooled":
                raise
            # A descriptive analysis only: it is reported as not analysed, with the count (owner's
            # decision open; step 7 summary). Fail closed: no group is invented, nothing stored for it.
            not_analysed.append({"analysis": key, "scope": scope, "set": set_key, "source": source,
                                 "reason": "records_without_group", "n_records_without_group": missing.n,
                                 "n_records_in_set": len(ids)})
            continue
        entries.append({"analysis": key, "scope": scope, "set": set_key, "source": source})
    withheld = st.pooled_withheld(designs["pooled"], plan)
    for entry in entries:
        d = designs[entry["analysis"]]
        entry.update(st.analysis_entry(d, plan, withheld))
        if withheld:
            ids = [i for i in data["sets"][entry["set"]] if entry["source"] is None or sources[i] == entry["source"]]
            entry["records_found"] = sorted(record_identity(by_id[i]["version_fingerprint"], by_id[i]["origin"],
                                                            by_id[i]["item_index"]) for i in ids)
            entry["label_text"] = st.BELOW_MINIMUMS_LABEL
    pooled = entries[0]
    for entry in entries:
        per_source = entry["scope"] == "per_source"
        entry["label"] = st.label(entry, pooled, alpha) if per_source else None
        entry["label_reason"] = st.label_reason(entry, pooled) if per_source else None
        d = designs[entry["analysis"]]
        entry["estimated_power"], entry["estimated_power_estimated_noise"], entry["power_label"] = None, None, None
        entry["detection"], entry["detection_note"] = None, None
        if not entry["checks"]["inference_valid"]:
            reason = entry["inference_reason"]
            entry["calibration"] = {"fixed": _unavailable(reason), "estimated": _unavailable(reason)}
            continue
        # The fixed method uses no outcome value: its effect world is the estimated power, shown
        # even below the minimums (owner, decision 5).
        fixed = cal.calibrate(d, plan["calibration"], alpha, fp, entry["analysis"], "fixed")
        entry["estimated_power"], entry["power_label"] = fixed["effect"]["share"], st.POWER_LABEL
        entry["detection_note"] = st.detection_note(alpha)
        if withheld:
            entry["calibration"] = {"fixed": _unavailable("below_minimums"),
                                    "estimated": _unavailable("below_minimums")}
            entry["detection"] = {"fixed": _rates(fixed), "estimated": {"withheld": True}}
        else:
            estimated = cal.calibrate(d, plan["calibration"], alpha, fp, entry["analysis"], "estimated")
            entry["calibration"] = {"fixed": fixed, "estimated": estimated}
            entry["detection"] = {"fixed": _rates(fixed), "estimated": _rates(estimated)}
            if estimated["status"] == "computed":
                entry["estimated_power_estimated_noise"] = estimated["effect"]["share"]
    return {"freeze_fingerprint": fp, "model": plan["model"]["name"],
            "test": "one-sided t test of k > 0 against t with (informative groups - 1) degrees of freedom; "
                    "cluster-robust standard error by group with the small-sample correction over informative groups",
            "alpha": alpha, "sufficiency_option": plan["sufficiency"]["option"], "withheld": withheld,
            "analyses": entries, "not_analysed": not_analysed, "decision": st.decision(pooled, plan, fp)}


def gap_facts(gap: Mapping, minimums: Mapping | None) -> dict:
    """The facts a gap report needs, as data only (owner, 2026-10-05): counts against each minimum
    and which were missed, how many records lacked which fields, the eligibility rules applied, and
    the kind of "nothing found" per source. No report text; no outcome value."""
    fields = gap["plan"]["content"].get("fields_to_extract", [])
    lacking = {}
    for source in gap["stored_record_counts"]:
        by_status = source.get("by_status", {})
        lacking[source["source"]] = {f: sum(n for status, n in by_status.get(f, {}).items()
                                            if status not in VALUE_STATUSES) for f in fields}
    rules: dict[str, int] = {}
    for d in gap["decisions"]["records"]:
        rules[d["rule"]] = rules.get(d["rule"], 0) + 1
    return {"minimums": minimums, "minimums_missed": sorted(k for k, v in (minimums or {}).items() if not v["met"]),
            "records_lacking_fields": lacking, "eligibility_rules": dict(sorted(rules.items())),
            "sources": [{"source": s["source"], "search_status": s["search_status"], "nothing_found": s["nothing_found"]}
                        for s in gap["coverage"]["sources"]]}


def empty_minimums(plan: Mapping) -> dict:
    """The minimums against a run with no record to analyse (no dataset frozen)."""
    d = st.design([], plan["variables"]["predictor"]["transformation"])
    return st.minimums(d, plan["sufficiency"])


# --- Reads and the write ---------------------------------------------------------------------------

def _read(engine: Engine, run_id: int, role: str) -> tuple[dict, str]:
    try:
        access = bind_code(engine, run_id, role)
    except AccessDenied as denied:
        log_refusal(engine, run_id, ROLE, "run_statistics", "stage_mismatch", denied.code)
        raise Refused("run_statistics", "stage_mismatch", denied.code) from None
    return role_input(access), access.context.stage


_RESULT = text(
    "INSERT INTO analysis_result (run_id, scope, analysis_set_id, source_id, n_records, n_alloys, n_groups, resid_df, "
    "check1_passed, check2_passed, minimums_met, estimate, std_error, p_value, estimated_power, label, withheld, "
    "n_records_not_used, test_run_label, n_groups_informative, inference_reason, label_reason, "
    "estimated_power_estimated_noise, effective_papers, largest_paper_share) VALUES (:r, :scope, :set, :src, :n, :a, "
    ":g, :df, :c1, :c2, :mm, :est, :se, :p, :pw, :lab, :wh, :nu, :tl, :gi, :ir, :lr, :pe, :ep, :ls) RETURNING id")
_CALIBRATION = text(
    "INSERT INTO calibration_result (run_id, analysis_result_id, method, status, reason, assumptions, n_simulations, "
    "seed, null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, effect_ci_high, confidence_flag, "
    "test_run_label) VALUES (:r, :a, :m, :st, :re, :asm, :ns, :seed, :ns_sh, :ns_lo, :ns_hi, :ef_sh, :ef_lo, "
    ":ef_hi, :flag, :tl)").bindparams(bindparam("asm", type_=JSONB(none_as_null=True)))


def _calibration_row(run_id: int, result_id: int, method: str, c: Mapping, label: str | None) -> dict:
    computed = c["status"] == "computed"
    pick = lambda world, k: c[world][k] if computed else None  # noqa: E731
    return dict(r=run_id, a=result_id, m=method, st=c["status"], re=c.get("reason"),
                asm=c["assumptions"] if computed else None, ns=c["n_simulations"] if computed else None,
                seed=c["seed"] if computed else None, ns_sh=pick("null", "share"), ns_lo=pick("null", "ci_low"),
                ns_hi=pick("null", "ci_high"), ef_sh=pick("effect", "share"), ef_lo=pick("effect", "ci_low"),
                ef_hi=pick("effect", "ci_high"), flag=c["confidence_flag"] if computed else None, tl=label)


def run_statistics(engine: Engine, run_id: int) -> dict:
    """The analysis stage of a run whose dataset is frozen, or the closing record of a run with no
    dataset frozen. Returns the stored "statistics" output."""
    gap, stage = _read(engine, run_id, "gap_facts")
    plan = gap["plan"]["content"]
    if stage == "analysis":
        data, _ = _read(engine, run_id, ROLE)
        try:
            record = analyse(data["plan"]["content"], data["frozen_analysis_data"])
        except Exception as error:  # review finding 3: nothing bypasses the stage's error handling
            code = "records_without_group" if isinstance(error, RecordsWithoutGroup) else "statistics_failed"
            message = f"{type(error).__name__}: {error}"
            log_refusal(engine, run_id, ROLE, "run_statistics", code, message)
            raise Refused("run_statistics", code, message) from None
        pooled = record["analyses"][0]
        facts = gap_facts(gap, pooled["minimums"])
        plan_fp, fp = data["plan"]["fingerprint"], record["freeze_fingerprint"]
    else:
        record = {"freeze_fingerprint": None, "analyses": [], "not_analysed": [], "withheld": False,
                  "decision": st.decision(None, plan, None), "no_dataset_frozen": True}
        facts = gap_facts(gap, empty_minimums(plan))
        plan_fp, fp = gap["plan"]["fingerprint"], None

    def body(conn: Connection, now_stage: str):
        if now_stage != stage:
            raise Refused("run_statistics", "stage_mismatch")
        done = conn.execute(text("SELECT EXISTS (SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'statistics') "
                                 "OR EXISTS (SELECT 1 FROM analysis_result WHERE run_id = :r)"),
                            dict(r=run_id)).scalar_one()
        if done:
            raise Refused("run_statistics", "already_done")
        snapshot = conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"),
                                dict(r=run_id)).scalar_one_or_none()
        if snapshot != fp:
            raise Refused("run_statistics", "changed_since_read")
        label = TEST_RUN_LABEL if marked(conn, run_id) else None
        sets = dict(conn.execute(text("SELECT key, id FROM analysis_set WHERE run_id = :r"), dict(r=run_id)).all())
        source_ids = dict(conn.execute(text("SELECT key, id FROM source")).all())
        for e in record["analyses"]:
            c = e["counts"]
            rid = conn.execute(_RESULT, dict(
                r=run_id, scope=e["scope"], set=sets[e["set"]], src=source_ids[e["source"]] if e["source"] else None,
                n=c["n_records"], a=c["n_alloys"], g=c["n_groups"], df=c["resid_df"],
                c1=e["checks"]["coefficient_fitted"], c2=e["checks"]["inference_valid"], mm=e["minimums_met"],
                est=e["estimate"], se=e["std_error"], p=e["p_value"], pw=e["estimated_power"], lab=e["label"],
                wh=e["withheld"], nu=c["n_records_not_used"], tl=label, gi=c["n_groups_informative"],
                ir=e["inference_reason"], lr=e["label_reason"], pe=e["estimated_power_estimated_noise"],
                ep=c["effective_papers"] if c["n_alloys"] else None, ls=c["largest_paper_share"])).scalar_one()
            for method in ("fixed", "estimated"):
                conn.execute(_CALIBRATION, _calibration_row(run_id, rid, method, e["calibration"][method], label))
        output = {**record, "test_run_label": label}
        code_stage(conn, run_id, "statistics", {"plan": plan_fp, "freeze": fp}, output)
        code_stage(conn, run_id, "gap_facts", {"plan": plan_fp, "freeze": fp}, {**facts, "test_run_label": label})
        return output

    return write(engine, run_id, ROLE, "run_statistics", body)


def stored_record(engine: Engine, run_id: int) -> dict[str, Any] | None:
    """The stored "statistics" output of a run (tests and the copy path)."""
    with engine.connect() as conn:
        return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' "
                                 "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
