"""What a run looks like to a person: read-only views for the command line and the screens (build step 10a).

`show` and `queue_rows` moved here from `cli_runs` unchanged (the command line imports them from here, so its output is
the same). `run_page`, `runs_list` and `confirmation_page` give the screens everything they show as ready-made words
and numbers: every number is formatted by `pipeline.display`, every statement line by `pipeline.statement`, and the
confirmation content by `pipeline.confirmation`. A template only places these strings; it computes nothing (owner,
step 10 brief).

Nothing here writes, claims a run, runs a pipeline stage or calls a model; it imports neither the queue, the worker,
the orchestrator nor recovery (tests/test_web_isolation.py).
"""
from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
from typing import Any, Iterator, Mapping

from sqlalchemy import Connection, Engine, text

from hypocurate.db.models import TEST_RUN_LABEL
from hypocurate.pipeline import display, failure_words, progress
from hypocurate.pipeline import statistics as st

# What a run's status is called on the screens (step 10a; the live-run record's open item 3: a waiting run is shown as
# waiting at the rules lock, never as stage "none").
STATUS_WORDS = {"queued": "queued", "waiting": "waiting at the rules lock", "running": "running",
                "completed": "completed", "failed": "failed"}
WAITING_STAGE = "waiting at the rules lock"
QUEUE_STAGE_WORDS = {"waiting": WAITING_STAGE, "queued": "queued (not started)"}  # the command line's `queue`
# The stage of a running run (`access.stage.actual_stage`, unchanged), in words.
STAGE_WORDS = {"before_lock": "before the rules lock (the Planner and code's narrowing decision)",
               "narrowed": "after code's narrowing decision (no plan is locked)",
               "curation": "curation (after the rules lock, before the dataset freeze)",
               "closed_without_freeze": "closing without a dataset freeze",
               "analysis": "analysis (after the dataset freeze)",
               "final": "finished", "final_without_freeze": "finished without a dataset freeze",
               "none": "not started"}
# The sensitivity sets as people read them (step 10a; register 'sensitivity_set_display_names'). The internal keys are
# never shown. The ninth set's name is the one eligibility already shows (`INFLUENCE_DISPLAY_NAME`).
SET_DISPLAY_NAMES = {
    "primary": "the locked plan's set (gives the verdict)",
    "no_exclusions": "with no exclusion rules",
    "tension_and_compression": "with tension and compression tests",
    "six_batches_as_groups": "with Texas A&M grouped by its six batches",
    "same_alloy_1_at_pct": "with alloys matched at 1 atomic percent (at.%)",
    "source_only_assignments": "with values assigned from the source only",
    "scope_not_confirmed_included": "with records of unconfirmed scope included",
    "possible_duplicates_separate": "with possible duplicates counted separately",
    "conflicts_survivor_value": "with conflicting values counted once (survivor rule)",
}
# The one change of each set, in words for people, and what the main result does instead (owner's review,
# 2026-10-11). The main result's rule is read from the run's locked plan ({…} filled by `_set_description`).
SET_DESCRIPTIONS = {
    "no_exclusions": "The plan's exclusion rules are dropped ({exclusions}); the main result applies them. The scope is "
                     "kept.",
    "tension_and_compression": "Tests in tension and in compression are both accepted, instead of {test_types} only, "
                               "as in the main result.",
    "six_batches_as_groups": "The Texas A&M records are grouped by their six batches, instead of as one group (the "
                             "whole dataset), as in the main result; the records are the same.",
    "same_alloy_1_at_pct": "Compositions are rounded to 1 at.% when deciding whether two records are the same alloy, "
                           "instead of to {main_rounding} at.%, as in the main result.",
    "source_only_assignments": "Only values converted or assigned from the source are accepted; the main result also "
                               "accepts values assigned by decision.",
    "scope_not_confirmed_included": "Records whose scope cannot be confirmed are treated as in scope; the main result "
                                    "leaves them out.",
    "possible_duplicates_separate": "Records in unresolved or possible duplicate groups count as separate "
                                    "measurements; in the main result a possible duplicate group counts once (by the "
                                    "survivor rule) and an unresolved one is left out.",
    # Owner's wording (2026-10-11): say that these values are normally left out.
    "conflicts_survivor_value": "Conflicting values, left out of the main result, are included once each, using the "
                                "survivor's value.",
}
STAGE_NAMES = {"planner": "Planner", "narrowing": "narrowing decision (code)", "curation": "curation (code)",
               "checks": "checks (code)", "critic": "Critic", "inclusion": "inclusion (code)",
               "dataset_freeze": "dataset freeze (code)", "statistics": "statistics (code)",
               "gap_facts": "gap facts (code)", "analyst": "Analyst"}
OPEN_STATUSES = ("queued", "waiting", "running")  # the screens update these by themselves (static/poll.js)
NOT_COMPLETED = "No evidence level yet (not completed)"
NOT_REACHED = "not searched (the run ended first)"
FAILED_NO_LEVEL = "failed: no evidence level"  # owner, 2026-10-11
# The stored label of a marked run (register 'constructed_test_runs'), shown as it is stored.
TEST_RUN_BADGE = TEST_RUN_LABEL


RUNS_PER_PAGE = 50  # fix rounds 1 and 2: the runs list has pages of 50, followed by an ID cursor


@contextmanager
def snapshot(engine: Engine) -> Iterator[Connection]:
    """One read-only REPEATABLE READ transaction (fix round 1, finding 2): every read of a page sees the database as it
    was at the page's first read, so its status, statement, verdict and evidence level always belong together."""
    with engine.connect() as conn:
        conn.execution_options(isolation_level="REPEATABLE READ")
        with conn.begin():
            conn.execute(text("SET TRANSACTION READ ONLY"))
            yield conn


def _set_description(key: str | None, plan: Mapping | None = None) -> str:
    """The set's one change and what the main result does instead, with the main result's rule from `plan` (the run's
    locked plan; the profile's defaults when none is given)."""
    from hypocurate.pipeline import plan as plans
    from hypocurate.pipeline import reading
    from hypocurate.pipeline.eligibility import INFLUENCE_KEY, SENSITIVITY_CHANGES
    if key == INFLUENCE_KEY:
        return (SENSITIVITY_CHANGES[INFLUENCE_KEY][:1].upper() + SENSITIVITY_CHANGES[INFLUENCE_KEY][1:]
                + "; the main result keeps them.")
    p = plan or plans.reference_plan(0)
    rules = p.get("exclusion_rules") or []
    values = {"exclusions": "; ".join(reading.exclusion_words(r) for r in rules) if rules else "none in this plan",
              "test_types": " and ".join(p["scope"]["test_type"]),
              "main_rounding": f"{10 ** -p['rules']['same_alloy_decimals']:g}"}
    return SET_DESCRIPTIONS.get(key or "", "").format(**values)


def _set_display_name(key: str | None) -> str:
    from hypocurate.pipeline.eligibility import INFLUENCE_DISPLAY_NAME, INFLUENCE_KEY
    if key == INFLUENCE_KEY:
        return INFLUENCE_DISPLAY_NAME
    return SET_DISPLAY_NAMES.get(key or "", "another sensitivity set")


def money(value) -> str:
    """US dollars to six decimals, as the run record holds them."""
    return f"${Decimal(value or 0):.6f}"


def tokens(value) -> str:
    return f"{int(value or 0):,}"


# --- moved from cli_runs (step 10a), unchanged ---------------------------------------------------------------------

def question_as_tested(engine: Engine, run_id: int) -> dict | None:
    from hypocurate.pipeline import reading
    with engine.connect() as conn:
        return reading.stored(conn, run_id)


def _question_as_tested(conn: Connection, run_id: int) -> dict | None:
    from hypocurate.pipeline import reading
    return reading.stored(conn, run_id)


def analyst_text(explained) -> dict:
    """The Analyst's stored explanation, always with its label; or that it is unavailable (code's own words)."""
    from hypocurate.pipeline.agents import analyst
    if isinstance(explained, dict) and explained.get("report"):
        return {"label": analyst.LABEL, "text": explained["report"]}
    if isinstance(explained, dict):
        return {"unavailable": explained.get("shown") or analyst.UNAVAILABLE}
    return {"unavailable": analyst.UNAVAILABLE}


def critic_flags(engine: Engine, run_id: int) -> list[dict]:
    """Each flag as shown: code's kind and category, its records, and the Critic's class or why there is none."""
    from hypocurate.pipeline.agents import critic
    return critic.flag_display(engine, run_id)


def _critic_flags(conn: Connection, run_id: int) -> list[dict]:
    from hypocurate.pipeline.agents import critic
    return critic.flag_display_in(conn, run_id)


def queue_rows(engine: Engine) -> list[dict]:
    """`queue` (R2): every queued, waiting or running run, with its stage, its claim's worker and heartbeat age, the
    time since the run last wrote anything (A4), and how often it was taken up again."""
    from hypocurate.access.stage import actual_stage
    from hypocurate.pipeline import confirmation
    out = []
    with engine.connect() as conn:
        runs = conn.execute(text(
            "SELECT r.id, r.status, h.number, r.experiment_flags, EXISTS (SELECT 1 FROM rules_confirmation rc WHERE "
            "rc.run_id = r.id) AS confirmed, c.worker, extract(epoch FROM clock_timestamp() - c.heartbeat_at) AS heartbeat_age, "
            "(SELECT count(*) FROM run_claim x WHERE x.run_id = r.id AND x.released_at IS NOT NULL AND "
            "x.release_reason NOT IN ('waiting', 'finished')) AS recoveries FROM run r "
            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
            "LEFT JOIN run_claim c ON c.run_id = r.id AND c.released_at IS NULL "
            "WHERE r.status IN ('queued', 'waiting', 'running') ORDER BY r.queued_at, r.id")).all()
        for r in runs:
            out.append({
                # Step 10a (the live-run record's open item 3): a waiting or queued run says where it is, never
                # "none" (the access layer's `actual_stage` is unchanged).
                "run": r.id, "query": r.number, "status": r.status,
                "stage": QUEUE_STAGE_WORDS.get(r.status) or actual_stage(conn, r.id, r.status),
                "waiting_for": (confirmation.WAITING_FOR if r.status == "waiting" and not r.confirmed else
                                "a worker (confirmed)" if r.status == "waiting" else None),
                "worker": r.worker, "heartbeat_age_seconds": round(float(r.heartbeat_age), 1)
                if r.heartbeat_age is not None else None,
                "seconds_since_last_write": round(progress.seconds_since_last_write(conn, r.id), 1),
                "recoveries": int(r.recoveries),
                # Step 10b (register 'constructed_test_runs'): the label on every list.
                "test_run": bool((r.experiment_flags or {}).get("constructed_test_data"))})
    return out


def show(engine: Engine, run_id: int) -> dict | None:
    with snapshot(engine) as conn:
        return show_in(conn, run_id)


def show_in(conn: Connection, run_id: int) -> dict | None:
    """`show` on a given connection: one snapshot for the whole output (fix round 1, finding 2)."""
    from hypocurate.pipeline import statement
    run = conn.execute(text(
        "SELECT r.id, r.status, r.outcome, r.verdict, r.exploratory, r.evidence_level, r.failure_reason, "
        "r.fixed_plan, h.number, hv.text, hv.sufficiency_option, h.narrower_of_run_id FROM run r "
        "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
        "WHERE r.id = :r"), dict(r=run_id)).one_or_none()
    if run is None:
        return None

    def output(stage):
        return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = :s "
                                 "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).scalar_one_or_none()

    stats, gap, narrowing, explained = output("statistics"), output("gap_facts"), output("narrowing"), output("analyst")
    results = [dict(r._mapping) for r in conn.execute(text(
        "SELECT ar.scope, s.key AS source, a.key AS analysis_set, ar.n_records, ar.n_alloys, ar.n_groups, "
        "ar.resid_df, ar.check1_passed, ar.check2_passed, ar.minimums_met, ar.withheld, ar.estimate, ar.std_error, "
        "ar.p_value, ar.label FROM analysis_result ar JOIN analysis_set a ON a.id = ar.analysis_set_id "
        "LEFT JOIN source s ON s.id = ar.source_id WHERE ar.run_id = :r ORDER BY ar.id"), dict(r=run_id)).all()]
    narrower = conn.execute(text("SELECT number FROM hypothesis WHERE narrower_of_run_id = :r"),
                            dict(r=run_id)).scalar_one_or_none()
    original = conn.execute(text("SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = "
                                 "r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"),
                            dict(r=run.narrower_of_run_id)).scalar_one_or_none() if run.narrower_of_run_id else None
    cost = conn.execute(text("SELECT * FROM model_call_totals_by_run WHERE run_id = :r"), dict(r=run_id)).one_or_none()
    decision = (stats or {}).get("decision") or (narrowing or {}).get("decision") or {}
    built = statement.build_in(conn, run_id)  # decision A: code's statement, for every completed run
    return {
        # One presentation everywhere (owner, after the re-check): code's statement first, then the Analyst's text,
        # only with the statement and only under its label; `run` and `dispatch` print this same output.
        "statement": built["lines"] if built else None,
        "analyst_text": analyst_text(explained) if built else None,
        "run": run.id, "query": run.number, "claim": run.text, "outcome_code": run.outcome,
        "question_as_tested": _question_as_tested(conn, run.id), "status": run.status,
        "narrower_question_of": original, "narrower_question": narrower,
        # A8: a narrower question's plan is shown as coming from its original's narrowing decision.
        "plan": ("from the narrowing decision" if original is not None else "fixed") if run.fixed_plan
                else "the Planner's",
        "sufficiency_option": run.sufficiency_option,
        "outcome": decision.get("outcome_wording") if run.status == "completed" else None,
        "verdict": decision.get("verdict_wording") if run.verdict else None,
        "exploratory": run.exploratory, "evidence_level": run.evidence_level,
        "evidence_level_wording": decision.get("evidence_level_wording") if run.status == "completed" else None,
        "label": decision.get("label"), "failure": run.failure_reason,
        "results": [r for r in results if not r["withheld"]] if results else [],
        "withheld": [{k: r[k] for k in ("scope", "source", "analysis_set", "n_records", "n_alloys", "n_groups",
                                         "resid_df", "minimums_met")} for r in results if r["withheld"]],
        "minimums_missed": (gap or {}).get("minimums_missed"), "nothing_found": (gap or {}).get("kind"),
        "sources": (gap or {}).get("sources"),
        "statement_format": ({"current": built["format_version"], "recorded": built["recorded_format_version"]}
                             if built else None),
        "flags": _critic_flags(conn, run_id),
        "tokens_and_cost": {k: v for k, v in cost._mapping.items() if k != "run_id"} if cost else None,
        "p_value_description": st.P_VALUE_DESCRIPTION if any(r["p_value"] is not None for r in results) else None,
        # Step 9a: only for a waiting run, so every other run's output is as before.
        **({"waiting_for": _waiting_for()} if run.status == "waiting" else {}),
    }


def _waiting_for() -> str:
    from hypocurate.pipeline.confirmation import WAITING_FOR
    return WAITING_FOR


# --- the screens (step 10a) ----------------------------------------------------------------------------------------

def evidence(level: int | None, verdict_wording: str | None, wording: str | None, test_run: bool,
             failed: bool = False) -> dict:
    """The evidence level as the dial shows it: the level, its short label (`statistics.EVIDENCE_SHORT`), the long
    wording code stored, the verdict shown beside the dial, and whether the run is a marked test run."""
    if level is None:
        return {"level": None, "words": FAILED_NO_LEVEL if failed else NOT_COMPLETED, "wording": None,
                "verdict": None, "test_run": test_run}
    return {"level": level, "words": f"Level {level} of {len(st.EVIDENCE_SHORT)}: {st.EVIDENCE_SHORT[level]}",
            "wording": wording, "verdict": verdict_wording, "test_run": test_run}


def _result_words(e: Mapping, withheld: bool) -> str:
    """One result in words, from stored numbers formatted by `display`."""
    if withheld or e.get("withheld"):
        return "withheld: the minimums were not met"
    if e.get("estimate") is None:
        reason = str(e.get("inference_reason") or "coefficient not fitted").replace("_", " ")
        return f"no coefficient fitted ({reason})"
    k = display.coefficient(e["estimate"])
    if e.get("p_value") is None:
        reason = str(e.get("inference_reason") or "no valid inference").replace("_", " ")
        return f"{k}; coefficient only ({reason}): no uncertainty, no p-value"
    return f"{k} ± {display.coefficient(e['std_error'])} (one standard error); {display.p_phrase(e['p_value'])}"


def _counts_words(e: Mapping) -> dict:
    c = e.get("counts") or {}
    return {"records": c.get("n_records"), "alloys": c.get("n_alloys"), "groups": c.get("n_groups"),
            "informative": c.get("n_groups_informative"), "resid_df": c.get("resid_df")}


def _tables(stats: Mapping, kinds: Mapping[str, str], plan: Mapping | None = None) -> dict:
    """Per-source and sensitivity rows from the stored statistics output (the order `statement` uses)."""
    from hypocurate.pipeline import analyst_names as an
    from hypocurate.pipeline.statement import _ordered, _source_name
    analyses = _ordered(stats.get("analyses") or [])
    withheld, alpha = bool(stats.get("withheld")), stats.get("alpha")
    if not analyses:
        return {"pooled": None, "per_source": [], "sensitivity": []}
    pooled = analyses[0]
    inference = pooled.get("p_value") is not None and not withheld
    per_source = [{"name": "All sources together", "kind": ", ".join(sorted(set(kinds.values()))) or "—",
                   **_counts_words(pooled), "result": _result_words(pooled, withheld),
                   "against": "gives the verdict" if inference else "no verdict"}]
    for e in analyses:
        if e.get("scope") == "per_source":
            per_source.append({"name": _source_name(e["source"]), "kind": kinds.get(e["source"], "—"),
                               **_counts_words(e), "result": _result_words(e, withheld),
                               "against": an.label_words(e) if e.get("label") else "—"})
    sensitivity = []
    for e in analyses:
        if e.get("scope") != "sensitivity":
            continue
        against = "—"
        if inference and e.get("estimate") is not None:
            against = an.label_words({**e, "label": st.label(e, pooled, alpha)})
        sensitivity.append({"name": _set_display_name(e.get("set")), "change": _set_description(e.get("set"), plan),
                            **_counts_words(e), "result": _result_words(e, withheld), "against": against})
    return {"pooled": pooled, "per_source": per_source, "sensitivity": sensitivity}


def _statement_parts(lines: list[str] | None) -> dict:
    """Code's statement split for the page into its body, its cautions and its format lines. The lines are
    `statement.build`'s, unchanged and in their order; nothing is reworded."""
    if not lines:
        return {"body": [], "cautions": [], "format": []}
    start = next((i for i, x in enumerate(lines) if x.startswith("Main cautions")), None)
    end = next((i for i, x in enumerate(lines) if x.startswith("Statement format ")), len(lines))
    if start is None:
        return {"body": lines[:end], "cautions": [], "format": lines[end:]}
    return {"body": lines[:start], "cautions": lines[start:end], "format": lines[end:]}


def _analyst(a: Mapping | None) -> dict | None:
    """The Analyst's stored text, always with its label, or why there is none."""
    if a is None:
        return None
    if a.get("text"):  # shown in a small safe subset of Markdown (web/textfmt.model_text)
        return {"label": a["label"], "text": a["text"]}
    return {"unavailable": a.get("unavailable")}


def _claim_facts(conn: Connection, run_id: int) -> dict:
    row = conn.execute(text(
        "SELECT c.worker, to_char(c.claimed_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS claimed, "
        "extract(epoch FROM clock_timestamp() - c.heartbeat_at) AS heartbeat_age FROM run_claim c "
        "WHERE c.run_id = :r AND c.released_at IS NULL"), dict(r=run_id)).one_or_none()
    claims = conn.execute(text(
        "SELECT count(*) AS claims, count(*) FILTER (WHERE recovery) AS recoveries FROM run_claim WHERE run_id = :r"),
        dict(r=run_id)).one()
    return {"worker": row.worker if row else None, "claimed": row.claimed if row else None,
            "heartbeat_age": f"{float(row.heartbeat_age):.1f} s" if row and row.heartbeat_age is not None else None,
            "since_last_write": f"{progress.seconds_since_last_write(conn, run_id):.1f} s",
            "claims": int(claims.claims), "recoveries": int(claims.recoveries)}


def _time(conn: Connection, column: str, table: str, run_id: int, key: str = "run_id") -> str | None:
    return conn.execute(text(f"SELECT to_char({column} AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') "
                             f"FROM {table} WHERE {key} = :r"), dict(r=run_id)).scalar_one_or_none()


def run_page(engine: Engine, run_id: int) -> dict | None:
    """Everything the run viewer shows, as ready-made words and numbers, from one snapshot."""
    with snapshot(engine) as conn:
        return run_page_in(conn, run_id)


def run_page_in(conn: Connection, run_id: int) -> dict | None:
    from hypocurate.access.stage import actual_stage
    shown = show_in(conn, run_id)
    if shown is None:
        return None
    head = conn.execute(text(
        "SELECT r.status, r.experiment_flags, r.spending_ceiling, r.agent_mode, hv.version_number, d.name AS domain, "
        "to_char(r.queued_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS queued, "
        "to_char(coalesce(r.completed_at, r.failed_at) AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS ended, "
        "EXISTS (SELECT 1 FROM rules_confirmation rc WHERE rc.run_id = r.id) AS confirmed "
        "FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
        "JOIN domain d ON d.id = coalesce(hv.confirmed_domain_id, hv.domain_id) WHERE r.id = :r"),
        dict(r=run_id)).one()
    tags = conn.execute(text(
        "SELECT tv.kind, tv.value FROM run_tag rt JOIN tag_value tv ON tv.id = rt.tag_value_id WHERE rt.run_id = :r "
        "ORDER BY tv.kind, tv.value"), dict(r=run_id)).all()
    locked = conn.execute(text("SELECT fingerprint, content FROM plan WHERE run_id = :r"), dict(r=run_id)).one_or_none()
    plan = locked.fingerprint if locked else None
    freeze = conn.execute(text("SELECT fingerprint, n_records FROM run_snapshot WHERE run_id = :r"),
                          dict(r=run_id)).one_or_none()
    locked_at, frozen_at = _time(conn, "locked_at", "plan", run_id), _time(conn, "frozen_at", "run_snapshot", run_id)
    stats = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' AND "
                              "status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
    kinds = dict(conn.execute(text("SELECT s.key, s.data_kind FROM run_source rs JOIN source s ON s.id = "
                                   "rs.source_id WHERE rs.run_id = :r"), dict(r=run_id)).all())
    sources = conn.execute(text(
        "SELECT s.key, s.name, rs.search_status, rs.nothing_found FROM run_source rs JOIN source s ON s.id = "
        "rs.source_id WHERE rs.run_id = :r ORDER BY s.key"), dict(r=run_id)).all()
    stages = conn.execute(text(
        "SELECT sr.stage, sr.attempt, sr.status, sr.model, t.calls, t.input_tokens, t.output_tokens, t.reported_cost "
        "FROM stage_result sr LEFT JOIN model_call_totals_by_stage t ON t.stage_result_id = sr.id "
        "WHERE sr.run_id = :r ORDER BY sr.id"), dict(r=run_id)).all()
    stage = actual_stage(conn, run_id, head.status) if head.status == "running" else None
    facts = _claim_facts(conn, run_id) if head.status in ("queued", "waiting", "running") else None
    test_run = bool((head.experiment_flags or {}).get("constructed_test_data"))
    cost = shown["tokens_and_cost"] or {}
    tables = _tables(stats or {}, kinds, locked.content if locked else None)
    return {
        "run": run_id, "query": shown["query"], "version": head.version_number, "claim": shown["claim"],
        "status": head.status, "status_words": STATUS_WORDS[head.status],
        "stage_words": STAGE_WORDS.get(stage) if stage else (WAITING_STAGE if head.status == "waiting" else None),
        "waiting_for": shown.get("waiting_for"), "confirmed": head.confirmed,
        "can_confirm": head.status == "waiting" and not head.confirmed,
        "can_cancel": head.status in ("queued", "waiting"),
        "open": head.status in OPEN_STATUSES,
        "failure": shown["failure"], "domain": head.domain, "queued": head.queued, "ended": head.ended,
        "tags": [f"{k.replace('_', ' ')}: {v}" for k, v in tags], "plan_kind": shown["plan"],
        "agent_mode": head.agent_mode.replace("_", " "), "ceiling": money(head.spending_ceiling) if head.spending_ceiling is not None else "not recorded",
        "test_run": test_run, "test_run_badge": TEST_RUN_BADGE if test_run else None,
        "question_as_tested": shown["question_as_tested"],
        "evidence": evidence(shown["evidence_level"], shown["verdict"], shown["evidence_level_wording"], test_run,
                             failed=head.status == "failed"),
        "outcome": shown["outcome"], "verdict": shown["verdict"], "exploratory": shown["exploratory"],
        "statement": _statement_parts(shown["statement"]),
        "analyst": _analyst(shown["analyst_text"]),
        "per_source": tables["per_source"], "sensitivity": tables["sensitivity"],
        "checkpoints": {"rules_lock": {"at": locked_at, "fingerprint": plan},
                        "dataset_freeze": {"at": frozen_at, "fingerprint": freeze.fingerprint if freeze else None,
                                           "records": freeze.n_records if freeze else None}},
        "failure_plain": failure_words.explain(conn, run_id, shown["failure"]) if head.status == "failed" else None,
        # Owner, 2026-10-11: a source a run never reached because it ended first is "not searched", never "pending".
        "sources": [{"name": s.name, "status": (NOT_REACHED if s.search_status == "pending" and head.status in
                                                ("completed", "failed") else s.search_status.replace("_", " ")),
                     "nothing_found": s.nothing_found.replace("_", " ") if s.nothing_found else None} for s in sources],
        "flags": [{**f, "kind_words": f["kind"].replace("_", " ")} for f in shown["flags"]],
        "stages": [{"name": STAGE_NAMES.get(s.stage, s.stage), "attempt": s.attempt, "status": s.status,
                    "model": s.model, "calls": int(s.calls or 0), "input_tokens": tokens(s.input_tokens),
                    "output_tokens": tokens(s.output_tokens), "cost": money(s.reported_cost)} for s in stages],
        "cost": {"calls": int(cost.get("calls") or 0),
                 "calls_words": f"{int(cost.get('calls') or 0)} model call{'' if int(cost.get('calls') or 0) == 1 else 's'}", "input_tokens": tokens(cost.get("input_tokens")),
                 "output_tokens": tokens(cost.get("output_tokens")), "reported": money(cost.get("reported_cost")),
                 "counted": money(cost.get("cap_cost")),
                 "unconfirmed_calls": int(cost.get("unconfirmed_calls") or 0)},
        "claim_facts": facts,
        "p_value_description": shown["p_value_description"],
    }


class NoSuchPage(LookupError):
    pass


def runs_list(engine: Engine, before: int | None = None, per_page: int = RUNS_PER_PAGE) -> dict:
    """One page of runs, newest first (query, claim, status, outcome, evidence level and cost): the newest, or with
    `before`, the runs older than that run. The next page's cursor is the last run shown (fix round 2, ChatGPT's
    re-check: an offset shifted when runs were added between pages, repeating some and never reaching others; a run's
    id never changes, so following "older runs" goes through every run that existed when the list was opened exactly
    once). One snapshot for the count and the rows."""
    from hypocurate.pipeline import reading
    if before is not None and before < 1:
        raise NoSuchPage(f"no runs before run {before}")
    with snapshot(engine) as conn:
        total = conn.execute(text("SELECT count(*) FROM run")).scalar_one()
        rows = conn.execute(text(
            "SELECT r.id, r.status, r.evidence_level, r.verdict, r.experiment_flags, h.number, hv.text, "
            "r.outcome, r.failure_reason, "
            "to_char(r.queued_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS queued, "
            "coalesce(t.cap_cost, 0) AS cost FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
            "JOIN hypothesis h ON h.id = hv.hypothesis_id LEFT JOIN model_call_totals_by_run t ON t.run_id = r.id "
            "WHERE CAST(:before AS bigint) IS NULL OR r.id < :before ORDER BY r.id DESC LIMIT :n"),
            dict(before=before, n=per_page + 1)).all()  # one more than shown: is there an older page?
        more, rows = len(rows) > per_page, rows[:per_page]
        plans = {r.id: reading.provenance(conn, r.id) for r in rows}  # step 10b: the "Plan" column, same snapshot
        failures = {r.id: failure_words.explain(conn, r.id, r.failure_reason) for r in rows if r.status == "failed"}
    out = []
    for r in rows:
        test_run = bool((r.experiment_flags or {}).get("constructed_test_data"))
        out.append({"run": r.id, "query": r.number, "claim": r.text, "status": r.status, "plan": plans[r.id],
                    "status_words": failures[r.id]["short"] if r.id in failures else STATUS_WORDS[r.status],
                    "queued": r.queued,
                    "outcome": r.outcome.replace("_", " ") + " in the sources searched" if r.outcome else None,
                    "evidence": evidence(r.evidence_level, None, None, test_run, failed=r.status == "failed"),
                    "cost": money(r.cost)})
    if before is None:
        words = f"{total} run{'' if total == 1 else 's'} in all; the newest first." if total else "No run yet."
    else:
        words = (f"{total} run{'' if total == 1 else 's'} in all; runs older than run {before}, newest first."
                 if out else f"No run older than run {before}.")
    return {"runs": out, "total": total, "words": words, "before": before, "newest": before is not None,
            "older": out[-1]["run"] if more else None}


def _text_rows(words: str) -> list[dict]:
    """The confirmation text, line by line, for the page: each line's leading words before its first colon as a
    heading, the rest as its value; the words are `confirmation.render`'s, unchanged."""
    rows = []
    for line in words.split("\n"):
        indent = len(line) - len(line.lstrip(" "))
        body = line.strip()
        head, sep, rest = body.partition(": ")
        if sep and len(head) <= 60 and not head.endswith("."):
            rows.append({"indent": indent > 0, "head": head, "value": rest})
        else:
            rows.append({"indent": indent > 0, "head": None, "value": body})
    return rows


def confirmation_page(engine: Engine, run_id: int, name: str | None) -> dict | None:
    """A waiting run's confirmation, from one snapshot: the content and its text exactly as `confirm` shows them, the
    fingerprint of both (owner's addition 2; fix round 1, finding 1), which the page sends back, and the label the
    question as tested will carry once `name` confirms it."""
    from hypocurate.pipeline import confirmation
    with snapshot(engine) as conn:
        page = run_page_in(conn, run_id)
        if page is None:
            return None
        if not page["can_confirm"]:
            return {**page, "content": None}
        content = confirmation.content(conn, run_id)
    words = confirmation.render(content)
    after = confirmation.label_once_confirmed(content["question_as_tested"]["label"], by=name or "you",
                                              at="the time you confirm (UTC)")
    return {**page, "content": content, "text": words, "rows": _text_rows(words),
            "shown_fingerprint": confirmation.shown_fingerprint(content, words), "label_after": after}


def spending(engine: Engine) -> dict:
    """The menu's spending panel: the caps and this month's spend as the monthly cap counts it (`spend.month_total`),
    with the month's tokens (calendar month, UTC)."""
    from hypocurate.pipeline.agents import spend
    with engine.connect() as conn:
        counted = spend.month_total(conn)
        month_tokens = conn.execute(text(
            "SELECT coalesce(sum(input_tokens + output_tokens), 0) FROM model_call WHERE date_trunc('month', "
            "started_at AT TIME ZONE 'UTC') = date_trunc('month', now() AT TIME ZONE 'UTC')")).scalar_one()
    return {"per_run_cap": money(spend.RUN_CAP_USD), "monthly_cap": money(spend.MONTH_CAP_USD),
            "month_counted": money(counted), "month_tokens": tokens(month_tokens)}
