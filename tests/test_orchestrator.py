"""Step 8b, milestone 7: whole runs through the orchestrator, every model call to the local stub provider
(criteria 14.1 and 14.3 from code; the command line's own tests are in test_cli_runs.py)."""
from __future__ import annotations

import json
import re

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import orchestrator, queries
from hypocurate.pipeline import plan as plans
from hypocurate.sources.versions import files_digest, version_identity

MPEA_CLASS = "multi-principal-element (high-entropy) alloy"
FCC_CLAIM = "In FCC multi-principal-element alloys, yield strength rises as grain size falls"
BCC_CLAIM = "Grain refinement still strengthens BCC multi-principal-element alloys at 1000 °C"
PARTLY_CLAIM = ("In FCC multi-principal-element alloys tested in tension, yield strength rises as grain size falls, "
                "both at room temperature and at cryogenic temperatures (-196 °C)")
RT = {"band": "room temperature"}
CRYO = {"band": "cryogenic", "min": -200.0, "max": -150.0}
HOT = {"band": "elevated", "min": 950.0, "max": 1050.0}


def planner_body(**over):
    b = {"domain_matches": True,
         "claim_scope": {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                         "temperature_band": [RT]},
         # Step 8b (owner, 2026-10-07): each scope part marked stated by the claim or defaulted by the Planner.
         "stated": {"alloy_class": True, "phase_class": True, "test_type": False, "temperature_band": False},
         "outcome": "yield_strength", "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1}], "narrower": None}
    b.update(over)
    # Fix round 1 (owner's decision B): a part marked defaulted must hold the default, so a scope part that differs
    # from the default is marked as stated by the claim (unless a test gives the marks).
    if "stated" not in over:
        from hypocurate.pipeline.agents.planner import DEFAULT_SCOPE
        b["stated"] = {k: v or sorted(map(str, b["claim_scope"][k])) != sorted(map(str, DEFAULT_SCOPE[k]))
                       for k, v in b["stated"].items()}
    return b


BCC = planner_body(claim_scope={"alloy_class": [MPEA_CLASS], "phase_class": ["BCC"], "test_type": ["compression"],
                                "temperature_band": [HOT]})
PARTLY = planner_body(claim_scope={"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                                   "temperature_band": [RT, CRYO]},
                      narrower={"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [RT]})


def analyst_text(raw: str) -> str:
    """A text that passes the Analyst's checks (step 8b, owner 2026-10-07): placeholders only, no digit; the outcome
    and, when there is one, the verdict by name."""
    if '\\"verdict_wording\\": ' in raw:  # a key of the facts (the instruction itself names the placeholder)
        # With a verdict the pooled phrases are required too (owner, 2026-10-07).
        return ("The data are {outcome_wording}, and the claim is {verdict_wording}, with {pooled_p_phrase}, from "
                "{pooled_figures_phrase}.")
    return "The outcome is {outcome_wording}."


def responder(planner_answer=None, critic_answer=None, analyst=analyst_text):
    def respond(raw: str):
        if "[[ ## plan ## ]]" in raw:
            return sp.reply(sp.fields(plan=json.dumps(planner_answer)))
        if "[[ ## classification ## ]]" in raw:
            return sp.reply(sp.fields(classification=json.dumps(critic_answer or {})))
        if "[[ ## report ## ]]" in raw:
            return sp.reply(sp.fields(report=analyst(raw)))
        return sp.error(500, "api_error", "unexpected request")
    return respond


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    e.test_url = migrated_database
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e
    e.dispose()


def dispatched(engine, claim=FCC_CLAIM, fixed_plan=False, sufficiency="fixed_minimum"):
    q = queries.create(engine, claim, ("mpea", "tamu_fcc"), sufficiency=sufficiency)
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    return queries.dispatch(engine, q.version_id, fixed_plan=fixed_plan)


def run(engine, rid, stub, **kw):
    return orchestrator.run(engine, rid, client_options=sp.client_options(stub), **kw)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def rows(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def pooled(engine, rid):
    return rows(engine, "SELECT n_records, n_alloys, n_groups, resid_df, estimate, std_error, p_value FROM analysis_result "
                        "WHERE run_id = :r AND scope = 'pooled'", r=rid)[0]


# --- 14.1 -----------------------------------------------------------------------------------------------

def test_14_1a_the_fixed_plan_run_reproduces_the_reference_and_repeats_identically(engine, stub):
    stub.respond(responder())
    rid = dispatched(engine, fixed_plan=True)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome, report.failure) == ("completed", "sufficient", None)
    assert "planner" not in report.stages and report.stages[0] == "fixed plan"
    assert rows(engine, "SELECT outcome, verdict, exploratory, evidence_level FROM run WHERE id = :r", r=rid) == [
        ("sufficient", "supported", False, 6)]
    n, a, g, df, k, se, p = pooled(engine, rid)
    assert (n, a, g, df) == (97, 22, 20, 74)
    assert abs(k - 424.9) <= 0.05 and abs(se - 64.4) <= 0.05 and 1.25e-6 <= p <= 1.35e-6
    labels = dict(rows(engine, "SELECT s.key, ar.label FROM analysis_result ar JOIN source s ON s.id = ar.source_id "
                               "WHERE ar.run_id = :r AND ar.scope = 'per_source'", r=rid))
    assert labels["mpea"] == "agrees"
    tamu = rows(engine, "SELECT ar.check1_passed, ar.check2_passed, ar.p_value FROM analysis_result ar JOIN source s "
                        "ON s.id = ar.source_id WHERE ar.run_id = :r AND s.key = 'tamu_fcc'", r=rid)[0]
    assert tamu == (True, False, None)  # a coefficient, no uncertainty, no verdict
    assert one(engine, "SELECT minimums_met FROM analysis_result WHERE run_id = :r AND scope = 'pooled'", r=rid)
    assert one(engine, "SELECT output->>'report' FROM stage_result WHERE run_id = :r AND stage = 'analyst'", r=rid) \
        == report.explanation
    # Running the frozen run again: a second fixed-plan run of the same version.
    vid = one(engine, "SELECT hypothesis_version_id FROM run WHERE id = :r", r=rid)
    again = pw.run_of_version(engine, vid, ("mpea", "tamu_fcc"), agents=("planner", "critic", "analyst"))
    assert run(engine, again, stub).outcome == "sufficient"
    assert pooled(engine, again) == pooled(engine, rid)
    assert one(engine, "SELECT fingerprint FROM run_snapshot WHERE run_id = :r", r=again) == \
        one(engine, "SELECT fingerprint FROM run_snapshot WHERE run_id = :r", r=rid)


def test_14_1b_the_planners_plan_is_locked_and_the_run_completes(engine, stub):
    stub.respond(responder(planner_body()))
    rid = dispatched(engine)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "sufficient")
    vid = one(engine, "SELECT hypothesis_version_id FROM run WHERE id = :r", r=rid)
    assert one(engine, "SELECT content FROM plan WHERE run_id = :r", r=rid) == plans.reference_plan(vid)
    tags = {r[0] for r in rows(engine, "SELECT tv.value FROM run_tag rt JOIN tag_value tv ON tv.id = rt.tag_value_id "
                                       "WHERE rt.run_id = :r", r=rid)}
    assert tags == {"yield strength", MPEA_CLASS, "room-temperature tension"}
    assert one(engine, "SELECT fixed_plan FROM run WHERE id = :r", r=rid) is False


# --- 14.3 -----------------------------------------------------------------------------------------------

def test_14_3_the_bcc_claim_ends_insufficient_as_missing_evidence_with_no_verdict(engine, stub):
    stub.respond(responder(BCC))
    rid = dispatched(engine, claim=BCC_CLAIM)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "insufficient")
    assert rows(engine, "SELECT verdict, evidence_level FROM run WHERE id = :r", r=rid) == [(None, 1)]
    assert one(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid) == 0  # no dataset frozen
    assert one(engine, "SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0  # no p-value, no plot
    facts = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid)
    assert facts["kind"] == "missing_evidence"
    assert {s["source"]: s["kind"] for s in facts["sources"]} == {"mpea": "missing_evidence",
                                                                  "tamu_fcc": "missing_evidence"}
    assert facts["records_lacking_fields"]["mpea"]["grain_size"] > 0  # names the missing field
    assert set(facts["minimums_missed"]) == {"records", "alloys", "groups", "resid_df"}  # what would be enough
    coverage = rows(engine, "SELECT searched_sources, not_searched_sources FROM run_search_coverage WHERE run_id = :r",
                    r=rid)[0]
    assert sorted(coverage[0]) == ["mpea", "tamu_fcc"]


def test_14_3_a_partly_sufficient_original_and_its_narrower_question(engine, stub):
    stub.respond(responder(PARTLY))
    rid = dispatched(engine, claim=PARTLY_CLAIM)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "partly_sufficient") and report.narrower_question
    assert rows(engine, "SELECT verdict, evidence_level FROM run WHERE id = :r", r=rid) == [(None, 1)]
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
    assert one(engine, "SELECT status FROM stage_result WHERE run_id = :r AND stage = 'analyst'", r=rid) == "done"
    # The narrower question: separate, linked, labelled, dispatched by its number; it locks the stored plan (A8).
    vid = queries.submitted_version(engine, report.narrower_question)
    assert "narrower question" in one(engine, "SELECT text FROM hypothesis_version WHERE id = :v", v=vid)
    queries.confirm_domain(engine, vid, by="Ada Reviewer")
    narrower = queries.dispatch(engine, vid, fixed_plan=True)
    out = run(engine, narrower, stub)
    assert (out.status, out.outcome) == ("completed", "sufficient")
    stored = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'narrowing'", r=rid)
    locked = one(engine, "SELECT content FROM plan WHERE run_id = :r", r=narrower)
    assert locked == {"hypothesis_version": vid, **stored["narrower_plan"]}
    assert pooled(engine, narrower)[:4] == (97, 22, 20, 74)


def seal_new_version(engine, key):
    """A newer sealed version of `key`: the same data and one more documentation file."""
    with engine.begin() as conn:
        old = conn.execute(text("SELECT sv.id, sv.source_id, sv.source_type, sv.data_kind, sv.grouping_unit FROM "
                                "source_version sv JOIN source s ON s.id = sv.source_id WHERE s.key = :k "
                                "ORDER BY sv.id DESC LIMIT 1"), dict(k=key)).one()
        files = {p: bytes(c) for p, c in conn.execute(text("SELECT path, content FROM source_file WHERE "
                                                           "source_version_id = :v"), dict(v=old.id)).all()}
        roles = dict(conn.execute(text("SELECT path, role FROM source_file WHERE source_version_id = :v"),
                                  dict(v=old.id)).all())
        files["documentation/note.txt"], roles["documentation/note.txt"] = b"a later note\n", "documentation"
        new = conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on, source_type, data_kind, "
                                "grouping_unit) VALUES (:s, 'later', '2026-10-07', :t, :d, :u) RETURNING id"),
                           dict(s=old.source_id, t=old.source_type, d=old.data_kind, u=old.grouping_unit)).scalar()
        import hashlib
        for path, content in files.items():
            conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content, role) VALUES "
                              "(:v, :p, :h, :c, :o)"), dict(v=new, p=path, h=hashlib.sha256(content).hexdigest(),
                                                             c=content, o=roles[path]))
        digest = files_digest(files)
        conn.execute(text("UPDATE source_version SET sealed_at = now(), files_digest = :d, fingerprint = :f WHERE id = :v"),
                     dict(d=digest, f=version_identity(digest, old.source_type, old.data_kind, old.grouping_unit), v=new))


def test_b1_a_narrower_question_on_other_source_versions_is_refused_with_a_reason(engine, stub):
    stub.respond(responder(PARTLY))
    rid = dispatched(engine, claim=PARTLY_CLAIM)
    report = run(engine, rid, stub)
    seal_new_version(engine, "mpea")
    vid = queries.submitted_version(engine, report.narrower_question)
    queries.confirm_domain(engine, vid, by="Ada Reviewer")
    narrower = queries.dispatch(engine, vid, fixed_plan=True)
    out = run(engine, narrower, stub)
    assert out.status == "failed" and out.failure.startswith("narrowing_sources_changed:")
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=narrower).startswith("narrowing_sources_changed")
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=narrower) == 0


def narrower_version(engine, stub):
    """A partly-sufficient original run through the orchestrator, and its narrower question's version (confirmed)."""
    stub.respond(responder(PARTLY))
    report = run(engine, dispatched(engine, claim=PARTLY_CLAIM), stub)
    vid = queries.submitted_version(engine, report.narrower_question)
    queries.confirm_domain(engine, vid, by="Ada Reviewer")
    return report.run_id, vid


def test_finding_1_a_narrower_question_dispatched_with_default_arguments_locks_its_stored_plan(engine, stub):
    original, vid = narrower_version(engine, stub)
    narrower = queries.dispatch(engine, vid)
    out = run(engine, narrower, stub)
    assert (out.status, out.outcome) == ("completed", "sufficient")
    stored = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'narrowing'", r=original)
    assert one(engine, "SELECT content FROM plan WHERE run_id = :r", r=narrower) == {"hypothesis_version": vid,
                                                                                   **stored["narrower_plan"]}
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=narrower) == 0


def test_finding_1_default_dispatch_after_a_newer_source_version_is_refused_with_a_reason(engine, stub):
    _, vid = narrower_version(engine, stub)
    seal_new_version(engine, "mpea")
    narrower = queries.dispatch(engine, vid)
    out = run(engine, narrower, stub)
    assert out.status == "failed" and out.failure.startswith("narrowing_sources_changed:")
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=narrower) == 0
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=narrower) == 0


def test_finding_1_the_orchestrator_reads_the_narrower_link_not_the_runs_flag(engine, stub):
    """Code alone, with the database's rule switched off for this test: a narrower question's run recorded
    without the flag still never reaches the Planner, and still gets the source-version check (B1)."""
    _, vid = narrower_version(engine, stub)
    seal_new_version(engine, "mpea")
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE run DISABLE TRIGGER hc_run_insert_narrower"))
    try:
        narrower = queries.dispatch(engine, vid)
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL session_replication_role = replica"))
            conn.execute(text("UPDATE run SET fixed_plan = false WHERE id = :r"), dict(r=narrower))
    finally:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE run ENABLE TRIGGER hc_run_insert_narrower"))
    assert one(engine, "SELECT fixed_plan FROM run WHERE id = :r", r=narrower) is False
    out = run(engine, narrower, stub)
    assert out.status == "failed" and out.failure.startswith("narrowing_sources_changed:")
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=narrower) == 0


def test_decision_b_prepare_stops_before_the_lock_with_the_question_as_tested(engine, stub):
    """What the command line prints between its two calls: the run is prepared and nothing is locked yet."""
    stub.respond(responder(planner_body()))
    rid = dispatched(engine)
    prepared = orchestrator.prepare(engine, rid, client_options=sp.client_options(stub))
    assert prepared.ready and prepared.status == "running"
    assert prepared.question_as_tested["source"] == "planner"
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
    rest = orchestrator.proceed(engine, rid, client_options=sp.client_options(stub))
    assert (rest.status, rest.outcome) == ("completed", "sufficient") and rest.stages[0] == "rules lock"


@pytest.mark.parametrize("planner_done", [False, True])
def test_proceed_builds_the_plan_only_after_a_narrowing_decision_to_proceed(engine, stub, planner_done):
    """Without a stored Planner answer, or with one but no narrowing decision to proceed, `proceed` locks nothing."""
    from hypocurate.pipeline.agents import planner
    stub.respond(responder(planner_body()))
    rid = dispatched(engine)
    queries.start(engine, rid)
    if planner_done:
        assert planner.run_planner(engine, rid, client_options=sp.client_options(stub)).failure is None
    out = orchestrator.proceed(engine, rid, client_options=sp.client_options(stub))
    assert out.status == "failed" and out.failure.startswith("refused: ")
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0


# --- the failure table ----------------------------------------------------------------------------------

def test_b2_the_analyst_failing_on_the_partly_path_still_completes_and_creates_the_narrower_question(engine, stub):
    stub.respond(responder(PARTLY, analyst=lambda raw: "The data do not exist in the sources searched."))
    rid = dispatched(engine, claim=PARTLY_CLAIM)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "partly_sufficient") and report.narrower_question
    assert report.explanation == "explanation unavailable (wording_refused)"
    assert one(engine, "SELECT status FROM stage_result WHERE run_id = :r AND stage = 'analyst'", r=rid) == "failed"


@pytest.mark.parametrize("failure", ["recording_failed", "reservation_failed"])
def test_finding_3_an_accounting_failure_at_the_planner_stops_the_run_open(engine, stub, monkeypatch, failure):
    from hypocurate.pipeline.agents import spend

    def broken(*a, **kw):
        raise RuntimeError("database gone")

    stub.respond(responder(planner_body()))
    rid = dispatched(engine)
    monkeypatch.setattr(spend, "finish" if failure == "recording_failed" else "reserve", broken)
    report = run(engine, rid, stub)
    assert report.status == "running" and report.failure.startswith(f"{failure}: ")
    assert len(stub.requests) == (1 if failure == "recording_failed" else 0)
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'narrowing'", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0


@pytest.mark.parametrize("failure", ["recording_failed", "reservation_failed"])
def test_finding_3_an_accounting_failure_at_the_analyst_on_the_partly_path_creates_no_narrower_question(
        engine, stub, monkeypatch, failure):
    """B2's exception: the partly-sufficient run is not completed and no narrower question is created; the run
    stays running for recovery."""
    from hypocurate.pipeline.agents import spend
    name = "finish" if failure == "recording_failed" else "reserve"
    real = getattr(spend, name)

    def broken_for_the_analyst(db, *a, **kw):
        with db.connect() as conn:
            role = conn.execute(text("SELECT role FROM stage_result WHERE status = 'running' ORDER BY id DESC "
                                     "LIMIT 1")).scalar()
        if role == "analyst":
            raise RuntimeError("database gone")
        return real(db, *a, **kw)

    monkeypatch.setattr(spend, name, broken_for_the_analyst)
    stub.respond(responder(PARTLY))
    rid = dispatched(engine, claim=PARTLY_CLAIM)
    report = run(engine, rid, stub)
    assert report.status == "running" and report.failure.startswith(f"{failure}: ")
    assert report.narrower_question is None
    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 0
    assert one(engine, "SELECT outcome FROM run WHERE id = :r", r=rid) is None


def test_a3_a_spending_refusal_at_the_analyst_leaves_codes_decision_standing(engine, stub):
    from decimal import Decimal
    stub.respond(responder())
    rid = dispatched(engine, fixed_plan=True)
    # The Critic's calls fit; the ceiling is too low for the Analyst's reservation (Opus, larger request).
    report = run(engine, rid, stub, ceiling=Decimal("0.17"))
    assert (report.status, report.outcome) == ("completed", "sufficient"), report
    assert report.explanation.startswith("explanation unavailable (")


def test_a_spending_refusal_at_the_planner_fails_the_run(engine, stub):
    from decimal import Decimal
    stub.respond(responder(planner_body()))
    rid = dispatched(engine)
    report = run(engine, rid, stub, ceiling=Decimal("0.001"))
    assert report.status == "failed" and report.failure.startswith("spending_refused:") and "ceiling_reached" in \
        report.failure
    assert stub.requests == []


@pytest.mark.parametrize("answer, code", [(planner_body(domain_matches=False), "domain_mismatch"),
                                          (planner_body(outcome="hardness"), "planner_failed"),
                                          # Both test types have usable records (FCC at room temperature), so
                                          # there is no narrower question: the claim is not one plan (A11). (Was
                                          # two bands, RT and 950-1050 °C; the second has no usable record, so code
                                          # now narrows it, owner 2026-10-07.)
                                          (planner_body(claim_scope={**planner_body()["claim_scope"],
                                                                     "test_type": ["tension", "compression"]}),
                                           "claim_not_one_plan")])
def test_a_run_fails_before_the_lock_with_a_stated_reason(engine, stub, answer, code):
    stub.respond(responder(answer))
    rid = dispatched(engine)
    report = run(engine, rid, stub)
    assert report.status == "failed" and report.failure.startswith(f"{code}: ")
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND status = 'running'", r=rid) == 0


def test_no_model_call_is_made_while_a_database_transaction_is_open(migrated_database, stub):
    """For every role: while the stub serves a request, the run's connections hold no open transaction. (Small
    data with invalid values, so the Critic has flags to classify; the reference data raise none.)"""
    from stats_world import small_rows
    from test_critic import CONFLICT
    engine = make_engine(migrated_database)
    engine.test_url = migrated_database
    pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT)})
    seen = []

    def check():
        with make_engine(engine.test_url).connect() as conn:
            seen.append(conn.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid() "
                "AND state IN ('idle in transaction', 'active') AND backend_type = 'client backend'")).scalar())

    stub.on_request(check)
    stub.respond(responder(planner_body()))
    q = queries.create(engine, FCC_CLAIM, ("mpea",))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id)
    assert run(engine, rid, stub).status == "completed"
    asked = {field for r in stub.requests for field in ("plan", "classification", "report")
             if f"[[ ## {field} ## ]]" in r["raw"].decode()}
    assert asked == {"plan", "classification", "report"}  # the Planner, the Critic and the Analyst
    assert len(seen) == len(stub.requests) and seen == [0] * len(seen)


def test_a_spending_refusal_at_the_critic_fails_the_run(migrated_database, stub):
    """PRD 8, 14.4: before the freeze a cap or ceiling stops the run, marked failed with the reason."""
    from decimal import Decimal
    from stats_world import small_rows
    from test_critic import CONFLICT
    engine = make_engine(migrated_database)
    pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT)})
    stub.respond(responder())
    q = queries.create(engine, FCC_CLAIM, ("mpea",))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, fixed_plan=True)
    report = run(engine, rid, stub, ceiling=Decimal("0.001"))
    assert report.status == "failed" and report.failure.startswith("spending_refused:")
    assert stub.requests == []  # nothing was sent
    assert one(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND status = 'running'", r=rid) == 0


def test_live_run_c_the_planner_gives_no_narrower_scope_and_code_builds_it(engine, stub):
    """Owner, 2026-10-07 (after live run C failed 'narrower_missing'): the same answer now gives a
    partly-sufficient original and its narrower question."""
    stub.respond(responder(PARTLY | {"narrower": None}))
    rid = dispatched(engine, claim=PARTLY_CLAIM)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "partly_sufficient") and report.narrower_question


def test_the_analyst_is_told_which_scope_parts_the_claim_stated_and_which_were_assumed(engine, stub):
    """Owner, 2026-10-07 (after live run B tested an unstated test type as 'tension'): the Planner marks each scope
    part; the Analyst's facts carry the notes, so an explanation can say what was assumed."""
    stub.respond(responder(planner_body()))  # test type and temperature band marked as defaulted
    rid = dispatched(engine)
    run(engine, rid, stub)
    facts = json.loads(one(engine, "SELECT input->>'facts' FROM stage_result WHERE run_id = :r AND stage = 'analyst'",
                           r=rid))
    assert facts["scope_test_type"] == "the claim did not state a test type; tension was assumed"
    assert facts["scope_temperature_band"] == "the claim did not state a temperature; room temperature was assumed"
    assert facts["scope_phase_class"] == "phase class FCC, as the claim states"
    narrowing = one(engine, "SELECT output->'scope_stated' FROM stage_result WHERE run_id = :r AND stage = 'narrowing'",
                    r=rid)
    assert narrowing == {"alloy_class": True, "phase_class": True, "temperature_band": False, "test_type": False}
