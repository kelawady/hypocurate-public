"""Step 3: the rules the database enforces (PRD 7, with the owner's decisions of
2026-10-04/05). Every rule has an allowed case and a rejected case, on a freshly
migrated scratch database. Rejections by a trigger read "hypocurate: ..."; rejections
by a CHECK name the constraint."""
import pytest
from sqlalchemy.exc import IntegrityError

from hypocurate.db.models import MAX_FILE_BYTES
from model_builder import EXTRACTION, FP, World, files_digest, sha


@pytest.fixture
def w(db):
    return World(db)


# --- queries and versions ------------------------------------------------------------------

def test_query_numbers_come_from_a_sequence(w):
    numbers = [w.val("SELECT number FROM hypothesis WHERE id = :h", h=w.hypothesis()) for _ in range(2)]
    assert numbers == ["Q-0001", "Q-0002"]


def test_a_new_version_starts_as_an_unreviewed_draft(w):
    h = w.hypothesis()
    w.rejected("INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id, status, submitted_at) "
               "VALUES (:h, 1, 'x', :d, 'submitted', now())", "starts as an unreviewed draft",
               h=h, d=w.domain["grain_size_strengthening"])
    assert w.draft(hypothesis=h)


def test_a_submitted_version_cannot_be_edited(w):
    vid = w.draft()
    w.run_sql("UPDATE hypothesis_version SET text = 'edited in draft' WHERE id = :v", v=vid)
    w.submit(vid)
    for column, value in (("text", "'changed'"), ("note", "'changed'"),
                          ("domain_id", str(w.domain["other"]))):
        w.rejected(f"UPDATE hypothesis_version SET {column} = {value} WHERE id = :v",
                   "an edit is a new version", v=vid)


def test_an_edit_is_a_new_version_of_the_same_query(w):
    h = w.hypothesis()
    v1 = w.dispatched(hypothesis=h)
    v2 = w.draft(hypothesis=h, number=2)
    assert v2 != v1
    w.rejected("UPDATE hypothesis_version SET text = 'x' WHERE id = :v", "cannot change", v=v1)
    w.rejected("INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
               "VALUES (:h, 2, 'x', :d)", "uq_hypothesis_version_hypothesis_id_version_number",
               h=h, d=w.domain["other"])


@pytest.mark.parametrize("start, end", [("draft", "dispatched"), ("draft", "returned"),
                                        ("submitted", "draft"), ("returned", "submitted"),
                                        ("dispatched", "submitted")])
def test_version_status_moves_only_forward(w, start, end):
    vid = w.draft()
    if start != "draft":
        w.submit(vid)
    if start == "returned":
        w.run_sql("UPDATE hypothesis_version SET status = 'returned', returned_at = now() WHERE id = :v", v=vid)
    if start == "dispatched":
        w.confirm(vid)
        w.dispatch_version(vid)
    w.rejected(f"UPDATE hypothesis_version SET status = '{end}', submitted_at = now(), returned_at = now(), "
               "dispatched_at = now() WHERE id = :v", "cannot (go from|change)", v=vid)


def test_return_for_edits_with_a_comment(w):
    vid = w.draft()
    w.submit(vid)
    w.run_sql("UPDATE hypothesis_version SET status = 'returned', returned_at = now(), "
              "review_comment = 'narrow the scope' WHERE id = :v", v=vid)
    w.rejected("UPDATE hypothesis_version SET review_comment = 'other' WHERE id = :v", "returned", v=vid)


def test_chosen_sources_change_only_in_draft(w):
    vid = w.draft()
    w.run_sql("DELETE FROM hypothesis_version_source WHERE hypothesis_version_id = :v AND source_id = :s",
              v=vid, s=w.source["tamu_fcc"])
    w.submit(vid)
    w.rejected("INSERT INTO hypothesis_version_source VALUES (:v, :s)", "only while the version is a draft",
               v=vid, s=w.source["tamu_fcc"])
    w.rejected("DELETE FROM hypothesis_version_source WHERE hypothesis_version_id = :v", "only while", v=vid)
    w.rejected("UPDATE hypothesis_version_source SET source_id = :s", "not updated", s=w.source["tamu_fcc"])


def test_reviewer_confirms_the_domain_only_while_submitted(w):
    """Owner decision, question 6: the submitter's domain is kept; the reviewer's
    decision is a separate field with its time, fixed at dispatch."""
    vid = w.draft()
    w.rejected("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() WHERE id = :v",
               "only while the version is submitted", v=vid, d=w.domain["other"])
    w.submit(vid)
    w.rejected("UPDATE hypothesis_version SET confirmed_domain_id = :d WHERE id = :v",
               "ck_hypothesis_version_confirmed_domain_with_time", v=vid, d=w.domain["other"])
    w.rejected("UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v",
               "ck_hypothesis_version_dispatch_needs_confirmed_domain", v=vid)
    w.confirm(vid, "other")
    w.confirm(vid, "grain_size_strengthening")  # may be changed again before dispatch
    w.dispatch_version(vid)
    w.rejected("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() WHERE id = :v",
               "dispatched hypothesis version cannot change", v=vid, d=w.domain["other"])
    row = w.rows("SELECT domain_id, confirmed_domain_id, domain_confirmed_at IS NOT NULL "
                 "FROM hypothesis_version WHERE id = :v", v=vid)[0]
    assert row == (w.domain["grain_size_strengthening"], w.domain["grain_size_strengthening"], True)


def test_dispatch_is_blocked_for_an_unsupported_domain(w):
    vid = w.dispatched(domain="fatigue")
    w.rejected("INSERT INTO run (hypothesis_version_id) VALUES (:v)", "domain is not supported", v=vid)


def test_a_run_needs_a_dispatched_version(w):
    vid = w.draft()
    w.rejected("INSERT INTO run (hypothesis_version_id) VALUES (:v)", "needs a dispatched", v=vid)


@pytest.mark.parametrize("table", ["hypothesis", "hypothesis_version", "run"])
def test_queries_versions_and_runs_are_never_deleted(w, table):
    w.run()
    w.rejected(f"DELETE FROM {table}", "(append-only|never deleted)")
    w.rejected(f"TRUNCATE {table} CASCADE", "(append-only|never deleted)")


# --- a narrower question is a separate query (owner decision, question 1) --------------------------

def partly_sufficient_run(w):
    rid = w.running()
    w.complete(rid, "partly_sufficient")
    return rid


def test_narrower_question_links_only_to_a_partly_sufficient_run(w):
    running = w.running()
    w.rejected("INSERT INTO hypothesis (narrower_of_run_id) VALUES (:r)", "partly_sufficient", r=running)
    insufficient = w.running()
    w.complete(insufficient, "insufficient")
    w.rejected("INSERT INTO hypothesis (narrower_of_run_id) VALUES (:r)", "partly_sufficient", r=insufficient)
    original = partly_sufficient_run(w)
    narrower = w.hypothesis(narrower_of=original)
    original_query = w.val("SELECT h.number FROM run r JOIN hypothesis_version v ON v.id = r.hypothesis_version_id "
                           "JOIN hypothesis h ON h.id = v.hypothesis_id WHERE r.id = :r", r=original)
    narrower_query = w.val("SELECT number FROM hypothesis WHERE id = :h", h=narrower)
    assert narrower_query.startswith("Q-") and narrower_query != original_query  # its own query number
    w.rejected("UPDATE hypothesis SET narrower_of_run_id = NULL WHERE id = :h", "append-only", h=narrower)


def test_a_partly_sufficient_run_has_no_verdict(w):
    rid = w.running()
    w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
               "verdict = 'supported', evidence_level = 6 WHERE id = :r", "ck_run_verdict_iff_sufficient", r=rid)


def test_narrower_question_has_the_original_domain(w):
    narrower = w.hypothesis(narrower_of=partly_sufficient_run(w))
    w.rejected("INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
               "VALUES (:h, 1, 'narrower', :d)", "domain of its original", h=narrower, d=w.domain["other"])
    vid = w.draft(hypothesis=narrower)
    w.submit(vid)
    w.rejected("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() WHERE id = :v",
               "domain of its original", v=vid, d=w.domain["other"])


def test_narrower_question_goes_through_review_and_dispatch(w):
    """Nothing creates or runs it automatically: it starts as a draft like any query."""
    original = partly_sufficient_run(w)
    narrower = w.hypothesis(narrower_of=original)
    assert w.rows("SELECT count(*) FROM hypothesis_version WHERE hypothesis_id = :h", h=narrower)[0][0] == 0
    vid = w.draft(hypothesis=narrower)
    assert w.val("SELECT status FROM hypothesis_version WHERE id = :v", v=vid) == "draft"
    rid = w.run(vid=w.dispatched(hypothesis=narrower, number=2))
    assert w.val("SELECT status FROM run WHERE id = :r", r=rid) == "queued"
    assert w.val("SELECT outcome FROM run WHERE id = :r", r=original) == "partly_sufficient"
    assert w.val("SELECT verdict FROM run WHERE id = :r", r=original) is None


# --- runs ----------------------------------------------------------------------------------------

def test_a_run_starts_queued(w):
    vid = w.dispatched()
    w.rejected("INSERT INTO run (hypothesis_version_id, status, started_at) VALUES (:v, 'running', now())",
               "starts as queued", v=vid)


@pytest.mark.parametrize("sql", [
    "UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient', evidence_level = 1 "
    "WHERE id = :r",
    "UPDATE run SET status = 'queued' WHERE id = :r",
])
def test_run_status_moves_only_forward(w, sql):
    rid = w.run()
    if "queued" in sql:
        w.start(rid)
    w.rejected(sql, "run status cannot go from", r=rid)


@pytest.mark.parametrize("end", ["completed", "failed"])
def test_completed_and_failed_runs_are_final(w, end):
    rid = w.running()
    w.complete(rid, "insufficient") if end == "completed" else w.fail(rid)
    w.rejected("UPDATE run SET heartbeat_at = now() WHERE id = :r", "run is final", r=rid)


def test_what_a_run_records_at_dispatch_cannot_change(w):
    rid = w.run()
    for change in ("experiment_flags = '{\"relaxed\": true}'", "fixed_plan = true", "queued_at = now() - interval '1 day'"):
        w.rejected(f"UPDATE run SET {change} WHERE id = :r", "at dispatch cannot change", r=rid)


def test_a_failed_run_states_its_reason(w):
    rid = w.running()
    w.rejected("UPDATE run SET status = 'failed', failed_at = now() WHERE id = :r", "ck_run_failed_has_reason", r=rid)
    w.fail(rid, "spending cap reached")


@pytest.mark.parametrize("outcome, verdict", [("sufficient", None), ("insufficient", "supported"),
                                              ("partly_sufficient", "not_supported")])
def test_verdict_if_and_only_if_sufficient(w, outcome, verdict):
    rid, sets, _ = w.frozen()
    w.result(rid, sets["primary"])  # a valid pooled result, so only the verdict rule can fail
    with pytest.raises(IntegrityError, match="ck_run_verdict_iff_sufficient"):
        w.complete(rid, outcome, verdict)


def test_a_running_run_has_no_outcome_or_verdict(w):
    rid = w.running()
    w.rejected("UPDATE run SET verdict = 'supported' WHERE id = :r", "ck_run_verdict_iff_sufficient", r=rid)
    w.rejected("UPDATE run SET outcome = 'insufficient' WHERE id = :r", "ck_run_outcome_iff_completed", r=rid)


# --- completion (owner's addition 2): the pooled-result rule applies only to "sufficient" ----------

def test_sufficient_needs_a_pooled_result_that_passed_both_checks(w):
    rid, sets, _ = w.frozen()
    with pytest.raises(IntegrityError, match="exactly one pooled result"):
        w.complete(rid, "sufficient", "supported")
    w.result(rid, sets["primary"])
    w.complete(rid, "sufficient", "supported")


def test_coefficient_only_completes_as_insufficient_without_a_verdict(w):
    """Check 1 passes, check 2 fails (2 records, 1 alloy: no residual degree of freedom).
    Step 7: under "use what is available" (under the fixed option the run misses the residual
    minimum, so the coefficient is withheld: owner's decision 1, tested in test_statistics_results)."""
    rid, sets, _ = w.frozen(n=2, mins=(1, 1, 1, 1), option="use_available")
    w.result(rid, sets["primary"], n=2, alloys=1, groups=2)
    assert w.rows("SELECT check1_passed, check2_passed, estimate IS NOT NULL, std_error, p_value "
                  "FROM analysis_result WHERE run_id = :r", r=rid) == [(True, False, True, None, None)]
    with pytest.raises(IntegrityError, match="passed both validity checks"):
        w.complete(rid, "sufficient", "supported")
    w.complete(rid, "insufficient")
    assert w.val("SELECT verdict FROM run WHERE id = :r", r=rid) is None


@pytest.mark.parametrize("outcome", ["insufficient", "partly_sufficient", "failed"])
def test_other_endings_need_no_pooled_result(w, outcome):
    rid = w.running()
    w.fail(rid) if outcome == "failed" else w.complete(rid, outcome)
    assert w.val("SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0


def test_fixed_minimum_sufficient_needs_the_minimums_met(w):
    rid, sets, _ = w.frozen(mins=(5, 1, 2, 1))  # 4 records < 5
    w.result(rid, sets["primary"], mins=(5, 1, 2, 1))
    with pytest.raises(IntegrityError, match="minimums met"):
        w.complete(rid, "sufficient", "supported")
    w.complete(rid, "insufficient")


@pytest.mark.parametrize("met, exploratory_ok", [(False, True), (True, False)])
def test_exploratory_means_use_available_and_minimums_not_met(w, met, exploratory_ok):
    """Owner decision, question 4: under "use what is available", data that meet the
    minimums are not exploratory."""
    mins = (4, 1, 2, 1) if met else (5, 1, 2, 1)
    rid, sets, _ = w.frozen(option="use_available", mins=mins)
    w.result(rid, sets["primary"], mins=mins)
    with pytest.raises(IntegrityError, match="exploratory must equal"):
        w.complete(rid, "sufficient", "supported", exploratory=not exploratory_ok)
    w.complete(rid, "sufficient", "supported", exploratory=exploratory_ok)


def test_exploratory_only_with_a_verdict(w):
    rid = w.running()
    with pytest.raises(IntegrityError, match="ck_run_exploratory_needs_verdict"):
        w.complete(rid, "insufficient", exploratory=True)


# --- the rules lock -------------------------------------------------------------------------

def test_a_locked_plan_cannot_change(w):
    rid = w.running()
    pid = w.lock(rid, keys=["no_exclusions"])
    for change in ("content = '{\"exclude\": []}'", "sufficiency_option = 'use_available'", "min_records = 1",
                   "sensitivity_analysis_keys = '{}'", "power_assumptions = '{}'", "fingerprint = repeat('1', 64)"):
        w.rejected(f"UPDATE plan SET {change} WHERE id = :p", "plan is append-only", p=pid)
    w.rejected("DELETE FROM plan WHERE id = :p", "plan is append-only", p=pid)
    w.rejected("TRUNCATE plan CASCADE", "plan is append-only")
    w.rejected("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
               "min_groups, min_resid_df) VALUES (:r, '{}', :fp, 'fixed_minimum', 1, 1, 1, 1)",
               "uq_plan_run_id", r=rid, fp=FP)


def test_a_plan_is_locked_only_while_the_run_is_running(w):
    with pytest.raises(IntegrityError, match="only while its run is running"):
        w.lock(w.run())


def test_the_lock_time_is_the_database_time(w):
    w.rejected("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
               "min_groups, min_resid_df, locked_at) VALUES (:r, '{}', :fp, 'fixed_minimum', 1, 1, 1, 1, "
               "now() - interval '1 hour')", "set by the database", r=w.running(), fp=FP)


@pytest.mark.parametrize("keys, match", [(["primary"], "ck_plan_primary_not_sensitivity"),
                                         (["a", "a"], "must be unique"),
                                         (["Bad Key"], "lowercase names")])
def test_sensitivity_analysis_keys(w, keys, match):
    with pytest.raises(IntegrityError, match=match):
        w.lock(w.running(), keys=keys)


@pytest.mark.parametrize("option, mins, match", [
    ("power_based", (30, 5, 10, 10), "ck_plan_sufficiency_option"),
    ("fixed_minimum", (0, 5, 10, 10), "ck_plan_minimums_positive"),
    ("use_available", (30, 5, 10, 0), "ck_plan_minimums_positive"),
])
def test_sufficiency_option_and_minimums(w, option, mins, match):
    """Power-based is not a gate in sprint 1 (owner's addition 1); minimums are kept under both options."""
    with pytest.raises(IntegrityError, match=match):
        w.lock(w.running(), option=option, mins=mins)


def test_power_assumptions_are_an_information_field(w):
    rid = w.running()
    w.run_sql("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
              "min_groups, min_resid_df, power_assumptions) VALUES (:r, '{}', :fp, 'fixed_minimum', 30, 5, 10, 10, "
              "'{\"power\": 0.8}')", r=rid, fp=FP)


def test_plan_fingerprint_format(w):
    w.rejected("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
               "min_groups, min_resid_df) VALUES (:r, '{}', 'ABC', 'fixed_minimum', 1, 1, 1, 1)",
               "ck_plan_fingerprint_format", r=w.running())


# --- tags --------------------------------------------------------------------------------------

def tag(w, value="FCC", status="approved"):
    return w.val("INSERT INTO tag_value (kind, value, status, decided_at) VALUES ('alloy_class', :v, :s, "
                 "CASE WHEN :s = 'proposed' THEN NULL ELSE now() END) RETURNING id", v=value, s=status)


def test_tags_are_written_in_the_lock_transaction_only(w):
    fcc, bcc = tag(w, "FCC"), tag(w, "BCC")
    rid = w.running()
    w.lock(rid, tags=[fcc])
    w.rejected("INSERT INTO run_tag VALUES (:r, :t)", "rules-lock transaction only", r=rid, t=bcc)
    w.rejected("DELETE FROM run_tag", "append-only")
    w.rejected("INSERT INTO run_tag VALUES (:r, :t)", "rules-lock transaction only", r=w.running(), t=bcc)


def test_a_proposed_tag_value_is_decided_once(w):
    proposed = tag(w, "HEA", "proposed")
    rid = w.running()
    w.lock(rid, tags=[proposed])  # the lock does not wait for a person
    w.run_sql("UPDATE tag_value SET status = 'approved', decided_at = now() WHERE id = :t", t=proposed)
    w.rejected("UPDATE tag_value SET status = 'rejected' WHERE id = :t", "approved or rejected once", t=proposed)
    w.rejected("DELETE FROM tag_value", "never deleted")


def test_a_rejected_tag_value_cannot_be_attached(w):
    rejected = tag(w, "nonsense", "rejected")
    with pytest.raises(IntegrityError, match="rejected tag value"):
        w.lock(w.running(), tags=[rejected])


def test_tag_kinds_are_a_fixed_list(w):
    w.rejected("INSERT INTO tag_value (kind, value, status) VALUES ('colour', 'blue', 'proposed')",
               "ck_tag_value_kind")


# --- agent settings ---------------------------------------------------------------------------

def setting(w, role="planner", version=1):
    return w.val("INSERT INTO agent_setting (role, version, instruction, model) VALUES (:r, :v, 'i', 'm') "
                 "RETURNING id", r=role, v=version)


def test_agent_settings_are_versioned_and_append_only(w):
    s1 = setting(w)
    setting(w, version=2)
    w.rejected("INSERT INTO agent_setting (role, version, instruction, model) VALUES ('planner', 1, 'i', 'm')",
               "uq_agent_setting_role_version")
    w.rejected("UPDATE agent_setting SET instruction = 'new' WHERE id = :s", "append-only", s=s1)


def test_agent_settings_versions_are_recorded_at_dispatch(w):
    planner = setting(w)
    rid = w.run()
    w.rejected("INSERT INTO run_agent_setting VALUES (:r, 'critic', :s)", "fk_run_agent_setting_agent_setting",
               r=rid, s=planner)
    w.run_sql("INSERT INTO run_agent_setting VALUES (:r, 'planner', :s)", r=rid, s=planner)
    w.rejected("UPDATE run_agent_setting SET agent_setting_id = :s", "append-only", s=planner)
    running = w.running()
    w.rejected("INSERT INTO run_agent_setting VALUES (:r, 'planner', :s)", "recorded at dispatch",
               r=running, s=planner)


# --- run sources and "nothing found" (owner decision, question 3) ----------------------------------------

def test_a_run_source_starts_undecided(w):
    rid = w.running(sources=())
    w.rejected("UPDATE run_source SET search_status = 'searched' WHERE run_id = :r", "is final", r=rid)
    vid = w.dispatched()
    rid2 = w.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
    w.rejected("INSERT INTO run_source (run_id, source_id, source_version_id, search_status, decided_at) "
               "VALUES (:r, :s, :sv, 'searched', now())", "starts as not_selected or pending",
               r=rid2, s=w.source["mpea"], sv=w.version["mpea"])


@pytest.mark.parametrize("status, kind, reason, match", [
    ("failed", None, "timeout", "ck_run_source_failed_iff_failed_search"),
    ("failed", "missing_evidence", "timeout", "ck_run_source_failed_iff_failed_search"),
    ("searched", "failed_search", None, "ck_run_source_failed_iff_failed_search"),
    ("failed", "failed_search", None, "ck_run_source_failed_has_reason"),
])
def test_a_failed_source_is_always_failed_search(w, status, kind, reason, match):
    rid = w.running()
    with pytest.raises(IntegrityError, match=match):
        w.search(rid, status=status, nothing_found=kind, reason=reason)


def test_a_decided_run_source_is_final(w):
    rid = w.running()
    w.search(rid, "mpea", "failed", "failed_search", "unreachable")
    w.rejected("UPDATE run_source SET search_status = 'searched', nothing_found = NULL, failure_reason = NULL "
               "WHERE run_id = :r AND source_id = :s", "is final", r=rid, s=w.source["mpea"])
    w.rejected("DELETE FROM run_source", "never deleted")


def test_the_source_version_of_a_run_cannot_change(w):
    rid = w.running()
    other = w.new_version("mpea", "v2")
    w.add_file(other, "mpea_v2.csv", b"v2")
    w.seal(other)
    w.rejected("UPDATE run_source SET source_version_id = :sv WHERE run_id = :r AND source_id = :s",
               "cannot change", sv=other, r=rid, s=w.source["mpea"])


COVERAGE = ("searched_sources, not_searched_sources, not_selected_sources, failed_search_sources, "
            "records_found_sources, missing_evidence_sources, reported_negative_sources")


def coverage(w, rid):
    names = [c.strip() for c in COVERAGE.split(",")]
    return dict(zip(names, w.rows(f"SELECT {COVERAGE} FROM run_search_coverage WHERE run_id = :r", r=rid)[0]))


def test_a_failed_source_is_never_missing_evidence(w):
    """One source failed, the other has missing evidence: each is reported in its own
    category; the failed source is named as failed and not searched."""
    rid = w.running()
    w.search(rid, "mpea", "searched", "missing_evidence")
    w.search(rid, "tamu_fcc", "failed", "failed_search", "unreachable")
    w.complete(rid, "insufficient")
    c = coverage(w, rid)
    assert c["missing_evidence_sources"] == ["mpea"] and c["failed_search_sources"] == ["tamu_fcc"]
    assert c["searched_sources"] == ["mpea"] and c["not_searched_sources"] == ["tamu_fcc"]


def test_mixed_results_are_reported_per_category(w):
    """Review finding 6: a negative report in one source and missing evidence in another
    are both reported, each with its source; nothing collapses them into one label."""
    rid = w.running()
    w.search(rid, "mpea", "searched", "reported_negative")
    w.search(rid, "tamu_fcc", "searched", "missing_evidence")
    w.complete(rid, "insufficient")
    c = coverage(w, rid)
    assert c["reported_negative_sources"] == ["mpea"] and c["missing_evidence_sources"] == ["tamu_fcc"]
    assert c["searched_sources"] == ["mpea", "tamu_fcc"] and c["not_searched_sources"] == []


def test_every_selected_source_failing_shows_no_source_searched(w):
    rid = w.running(sources=("mpea",))
    w.search(rid, "mpea", "failed", "failed_search", "unreachable")
    w.complete(rid, "insufficient")
    c = coverage(w, rid)
    assert c["searched_sources"] == [] and c["failed_search_sources"] == ["mpea"]
    assert c["not_searched_sources"] == ["mpea", "tamu_fcc"] and c["not_selected_sources"] == ["tamu_fcc"]


def test_records_found_is_its_own_category(w):
    rid = w.running(sources=("mpea",))
    w.search(rid, "mpea", "searched")
    c = coverage(w, rid)
    assert c["records_found_sources"] == ["mpea"] and c["missing_evidence_sources"] == []


def test_coverage_comes_from_the_runs_own_dispatch_rows(w):
    """Review finding 6: registering a source later does not change an earlier run's coverage."""
    rid = w.running()
    w.search(rid, "mpea", "searched")
    w.complete(rid, "insufficient")
    before = coverage(w, rid)
    w.add_source("later_source")
    assert coverage(w, rid) == before
    w.rejected("UPDATE source SET key = 'renamed' WHERE key = 'mpea'", "key and registration time cannot change")


def test_a_run_starts_only_with_its_full_source_inventory(w):
    """Every source registered at dispatch has a run_source row before the run starts."""
    vid = w.dispatched()
    rid = w.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
    w.run_sql("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
              "VALUES (:r, :s, :sv, 'pending')", r=rid, s=w.source["mpea"], sv=w.version["mpea"])
    with pytest.raises(IntegrityError, match="every source registered at dispatch"):
        w.start(rid)
    w.run_sql("INSERT INTO run_source (run_id, source_id, search_status) VALUES (:r, :s, 'not_selected')",
              r=rid, s=w.source["tamu_fcc"])
    w.start(rid)


def test_no_table_stores_a_run_level_nothing_found(w):
    assert w.val("SELECT count(*) FROM information_schema.columns WHERE table_name = 'run' "
                 "AND column_name LIKE '%nothing%'") == 0


# --- records: stored is not analysed ---------------------------------------------------------

def test_records_are_never_updated_or_deleted(w):
    rid = w.locked()
    rec = w.record(rid)
    for sql in ("UPDATE record SET alloy = 'other' WHERE id = :c", "UPDATE record SET harmonized = '{}' WHERE id = :c",
                "DELETE FROM record WHERE id = :c"):
        w.rejected(sql, "record is append-only", c=rec)
    w.rejected("TRUNCATE record CASCADE", "append-only")


def test_a_record_comes_from_a_source_version_its_run_recorded(w):
    rid = w.locked(sources=("mpea",))
    with pytest.raises(IntegrityError, match="source version recorded for its run"):
        w.record(rid, source="tamu_fcc")
    w.record(rid, source="mpea")


def test_records_are_extracted_while_running_and_before_the_freeze(w):
    with pytest.raises(IntegrityError, match="while their run is running"):
        w.record(w.run())
    rid, _, _ = w.frozen()
    with pytest.raises(IntegrityError, match="after the dataset freeze"):
        w.record(rid, key="late")


def test_every_record_names_its_origin(w):
    """Owner decision, question 7: source version plus the row it came from, so the
    same source row can be matched across runs."""
    rid = w.locked()
    # Each insert states its extraction (step 6), so that it reaches the check it is about.
    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, reported, "
               "extraction) VALUES (:r, :sv, '', 'measured', '{}', '{}', CAST(:x AS jsonb))", "ck_record_item_key_not_empty",
               r=rid, sv=w.version["mpea"], x=EXTRACTION)
    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, kind, harmonized, reported, extraction) "
               "VALUES (:r, :sv, 'measured', '{}', '{}', CAST(:x AS jsonb))", "source_item_key", r=rid, sv=w.version["mpea"],
               x=EXTRACTION)
    w.record(rid, key="row-7")
    with pytest.raises(IntegrityError, match="uq_record_origin_per_run"):
        w.record(rid, key="row-7")
    w.record(rid, key="row-7", index=1)  # a second observation from the same row
    other_run = w.locked()
    w.record(other_run, key="row-7")
    matched = w.rows("SELECT extraction_run_id FROM record WHERE source_version_id = :sv AND source_item_key = 'row-7' "
                     "AND item_index = 0 ORDER BY extraction_run_id", sv=w.version["mpea"])
    assert [r[0] for r in matched] == [rid, other_run]
    index = w.val("SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_record_source_version_id_source_item_key'")
    assert index.endswith("(source_version_id, source_item_key)")


def test_records_and_eligibility_come_after_the_rules_lock(w):
    """Review finding 3: no extraction before the rules lock, so no record can be
    decided on outside a locked plan."""
    rid = w.running()
    with pytest.raises(IntegrityError, match="only after the rules lock"):
        w.record(rid)
    w.lock(rid)
    rec = w.record(rid)
    w.decide(rid, rec, eligible=False, rule="grain size below 0.1 um")
    w.rejected("UPDATE run_record SET eligible = true", "append-only")
    w.rejected("DELETE FROM run_record", "append-only")


def test_a_run_decides_only_on_its_own_records(w):
    other = w.locked()
    rec = w.record(other)
    rid = w.running()
    w.lock(rid)
    with pytest.raises(IntegrityError, match="records extracted in that run"):
        w.decide(rid, rec)


def test_a_model_recalled_record_is_stored_but_never_eligible(w):
    w.add_source("recall", data_kind="model_recalled", source_type="model_recall")
    rid = w.locked(sources=("mpea", "recall"))
    rec = w.record(rid, source="recall")
    assert w.val("SELECT kind FROM record WHERE id = :c", c=rec) == "model_recalled"
    with pytest.raises(IntegrityError, match="never eligible"):
        w.decide(rid, rec, eligible=True)
    w.decide(rid, rec, eligible=False, rule="model-recalled: comparison only")
    sensitivity = w.analysis_set(rid, "primary")
    with pytest.raises(IntegrityError, match="never in an analysis set"):
        w.add(sensitivity, rec)


# --- analysis sets and the dataset freeze (owner decision, question 2) ---------------------------------

def test_a_set_exists_only_for_an_analysis_the_locked_plan_names(w):
    rid = w.running()
    with pytest.raises(IntegrityError, match="needs a locked plan"):
        w.analysis_set(rid)
    w.lock(rid, keys=["no_exclusions"])
    w.analysis_set(rid, "primary")
    w.analysis_set(rid, "no_exclusions")
    with pytest.raises(IntegrityError, match="names no analysis drop_four"):
        w.analysis_set(rid, "drop_four")


def test_primary_holds_only_eligible_records_and_sensitivity_sets_may_hold_others(w):
    rid = w.running()
    w.lock(rid, keys=["scope_not_confirmed"])
    eligible, excluded, undecided = w.record(rid, key="a"), w.record(rid, key="b"), w.record(rid, key="c")
    w.decide(rid, eligible)
    w.decide(rid, excluded, eligible=False, rule="scope not confirmed")
    primary, sensitivity = w.analysis_set(rid), w.analysis_set(rid, "scope_not_confirmed")
    with pytest.raises(IntegrityError, match="only eligible records"):
        w.add(primary, excluded)
    w.add(primary, eligible)
    w.add(sensitivity, eligible)
    w.add(sensitivity, excluded)
    with pytest.raises(IntegrityError, match="decided on"):
        w.add(sensitivity, undecided)


def test_a_possible_duplicate_counts_once_in_primary_and_twice_in_its_sensitivity_set(w):
    """PRD 5.3, the reason for named sets: one survivor in primary, both in the sensitivity set.
    This shows the storage can hold the result; it does not test duplicate handling,
    which is built in step 6 (second-model review of step 3). The non-surviving copy
    carries its own decision (not eligible), which keeps it out of the primary set."""
    rid = w.running()
    w.lock(rid, keys=["duplicates_separate"])
    survivor, twin = w.record(rid, key="a"), w.record(rid, key="b")
    w.decide(rid, survivor)
    w.decide(rid, twin, eligible=False, rule="possible duplicate of a; counted once")
    primary, both = w.analysis_set(rid), w.analysis_set(rid, "duplicates_separate")
    w.add(primary, survivor)
    w.add(both, survivor)
    w.add(both, twin)
    w.freeze(rid, 1)
    counts = w.rows("SELECT s.key, count(*) FROM analysis_set s JOIN analysis_set_record r ON r.analysis_set_id = s.id "
                    "WHERE s.run_id = :r GROUP BY s.key ORDER BY s.key", r=rid)
    assert counts == [("duplicates_separate", 2), ("primary", 1)]


def test_nothing_changes_after_the_freeze(w):
    rid, sets, recs = w.frozen(keys=["no_exclusions"])
    late = recs[0]
    for sql, match in [
        ("INSERT INTO analysis_set (run_id, key) VALUES (:r, 'no_exclusions_2')", "names no analysis|after the dataset freeze"),
        ("DELETE FROM analysis_set_record WHERE analysis_set_id = :s", "append-only"),
        ("UPDATE analysis_set SET key = 'other' WHERE run_id = :r", "append-only"),
        ("UPDATE run_snapshot SET fingerprint = repeat('1', 64) WHERE run_id = :r", "append-only"),
        ("DELETE FROM run_snapshot WHERE run_id = :r", "append-only"),
    ]:
        w.rejected(sql, match, r=rid, s=sets["primary"])
    with pytest.raises(IntegrityError, match="after the dataset freeze"):
        w.add(sets["no_exclusions"], late)
    with pytest.raises(IntegrityError, match="after the dataset freeze"):
        w.decide(rid, late)


def eligible_records(w, rid, n):
    recs = [w.record(rid, key=f"row-{i}") for i in range(n)]
    for rec in recs:
        w.decide(rid, rec)
    return recs


def test_the_freeze_rejects_a_primary_set_that_omits_eligible_records(w):
    """Review finding 2: ten records decided eligible, three put in primary."""
    rid = w.locked()
    recs = eligible_records(w, rid, 10)
    primary = w.analysis_set(rid)
    for rec in recs[:3]:
        w.add(primary, rec)
    with pytest.raises(IntegrityError, match="must hold every record decided eligible"):
        w.freeze(rid, 3)
    for rec in recs[3:]:
        w.add(primary, rec)
    w.freeze(rid, 10)


def test_the_freeze_rejects_an_undecided_record(w):
    rid = w.locked()
    rec = eligible_records(w, rid, 1)[0]
    w.add(w.analysis_set(rid), rec)
    w.record(rid, key="undecided")
    with pytest.raises(IntegrityError, match="needs an eligibility decision"):
        w.freeze(rid, 1)


def test_no_eligible_records_means_no_freeze(w):
    rid = w.running()
    w.lock(rid)
    w.analysis_set(rid)
    with pytest.raises(IntegrityError, match="no dataset is frozen"):
        w.freeze(rid, 1)
    with pytest.raises(IntegrityError, match="no dataset is frozen"):
        w.freeze(rid, 0)


def test_the_freeze_matches_the_primary_set_and_needs_every_named_set(w):
    rid = w.running()
    w.lock(rid, keys=["no_exclusions"])
    rec = w.record(rid)
    w.decide(rid, rec)
    w.add(w.analysis_set(rid), rec)
    with pytest.raises(IntegrityError, match="every sensitivity analysis named by the plan"):
        w.freeze(rid, 1)
    w.analysis_set(rid, "no_exclusions")
    with pytest.raises(IntegrityError, match="size of the primary set"):
        w.freeze(rid, 2)
    w.rejected("INSERT INTO run_snapshot (run_id, fingerprint, n_records, frozen_at) "
               "VALUES (:r, :fp, 1, now() - interval '1 hour')", "set by the database", r=rid, fp=FP)
    w.freeze(rid, 1)


# --- lifecycle on both sides (review finding 3; owner, 2026-10-05) ---------------------------------

def curation_in_progress(w):
    """A locked run with a record, a decision, a primary set, a pending source and an
    unclassified flag: everything curation could still touch."""
    rid = w.locked()
    w.search(rid, "mpea", "searched")  # tamu_fcc stays pending
    rec = eligible_records(w, rid, 1)[0]
    w.record(rid, key="undecided")
    primary = w.analysis_set(rid)
    f = flag(w, rid)
    return rid, rec, primary, f


@pytest.mark.parametrize("ending", ["completed", "failed"])
def test_no_curation_once_the_run_has_ended(w, ending):
    rid, rec, primary, f = curation_in_progress(w)
    w.complete(rid, "insufficient") if ending == "completed" else w.fail(rid)
    with pytest.raises(IntegrityError, match="while their run is running"):
        w.record(rid, key="late")
    for sql in [
        "INSERT INTO run_record (run_id, record_id, eligible, rule) SELECT :r, id, true, 'x' FROM record "
        "WHERE extraction_run_id = :r AND source_item_key = 'undecided'",
        "INSERT INTO analysis_set_record VALUES (:s, :c)",
        "INSERT INTO flag (run_id, kind, category) VALUES (:r, 'k', 'c')",
        "UPDATE flag SET critic_class = 'comparable', classified_at = now() WHERE id = :f",
        "INSERT INTO flag_record VALUES (:f, :c)",
        "UPDATE run_source SET search_status = 'searched', decided_at = now() WHERE run_id = :r AND search_status = 'pending'",
    ]:
        w.rejected(sql, "only while the run is running|while the run is running", r=rid, c=rec, s=primary, f=f)
    w.rejected("INSERT INTO run_snapshot (run_id, fingerprint, n_records) VALUES (:r, :fp, 1)",
               "only while its run is running", r=rid, fp=FP)
    w.rejected(CALIBRATION.format(numbers=NONE), "only while the run is running",
               r=rid, a=None, st="unavailable", re="no_dataset_frozen")


def test_a_record_extracted_after_the_freeze_cannot_slip_in_after_the_run_ends(w):
    rid, sets, _ = w.frozen()
    w.result(rid, sets["primary"])
    w.complete(rid, "sufficient", "supported")
    for sql in ["INSERT INTO analysis_set (run_id, key) VALUES (:r, 'extra')",
                "INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, "
                "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met) "
                "VALUES (:r, 'sensitivity', :s, 0, 0, 0, 0, -1, false, false, false)"]:
        w.rejected(sql, "only while the run is running", r=rid, s=sets["primary"])


def test_no_dataset_frozen_and_a_freeze_exclude_each_other(w):
    """Review finding 3: whichever comes second is rejected (the other order is in the
    calibration tests below)."""
    rid = w.locked()
    rec = eligible_records(w, rid, 1)[0]
    w.add(w.analysis_set(rid), rec)
    w.run_sql(CALIBRATION.format(numbers=NONE), r=rid, a=None, st="unavailable", re="no_dataset_frozen")
    with pytest.raises(IntegrityError, match="already recorded that no dataset was frozen"):
        w.freeze(rid, 1)


def test_what_may_be_written_after_completion(w):
    """Owner, 2026-10-05: the commentary, the Commentator's stage and model calls, and
    artifacts. The Commentator's calls count in the run's totals and cap. Nothing else."""
    rid, sets, _ = w.frozen(agents=True)
    w.result(rid, sets["primary"])
    w.complete(rid, "sufficient", "supported")
    commentator = w.stage(rid, "commentator", "commentator")
    call = w.call(rid, commentator, max_cost=0.25, role="commentator")
    assert float(w.val("SELECT cap_cost FROM model_call_totals_by_run WHERE run_id = :r", r=rid)) == 0.25
    w.finish_call(call, "succeeded", (100, 50, 0, 0.002))
    assert float(w.val("SELECT reported_cost FROM model_call_totals_by_run WHERE run_id = :r", r=rid)) == 0.002
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now() WHERE id = :s", s=commentator)
    w.run_sql("INSERT INTO commentary (run_id, stage_result_id, status, text, model, number_check) "
              "VALUES (:r, :s, 'written', 'k = 428', 'other-model', 'all_match')", r=rid, s=commentator)
    w.run_sql(ARTIFACT, r=rid, h=sha(b"plot"), c=b"plot")
    with pytest.raises(IntegrityError, match="after completion only the commentator"):
        w.stage(rid, "analyst", "analyst")
    with pytest.raises(IntegrityError, match="after completion only the commentator"):
        w.call(rid, commentator, role="analyst")
    for sql in ["UPDATE run SET verdict = 'not_supported' WHERE id = :r",
                "UPDATE run SET outcome = 'insufficient', verdict = NULL WHERE id = :r"]:
        w.rejected(sql, "run is final", r=rid)
    w.rejected("UPDATE analysis_result SET estimate = 1", "append-only")
    w.rejected("INSERT INTO analysis_set_record VALUES (:s, :c)", "only while the run is running",
               s=sets["primary"], c=w.val("SELECT min(id) FROM record"))
    assert w.rows("SELECT outcome, verdict FROM run WHERE id = :r", r=rid) == [("sufficient", "supported")]


def test_nothing_but_the_audit_log_after_failure(w):
    rid = w.running(agents=True)
    st = w.stage(rid, "planner", "planner")
    w.run_sql("UPDATE stage_result SET status = 'failed', finished_at = now() WHERE id = :s", s=st)
    w.fail(rid, "worker stopped")
    with pytest.raises(IntegrityError, match="while the run is running"):
        w.stage(rid, "commentator", "commentator")
    with pytest.raises(IntegrityError, match="while the run is running"):
        w.call(rid, st)
    w.rejected("INSERT INTO commentary (run_id, stage_result_id, status, model) VALUES (:r, :s, 'unavailable', 'm')",
               "after the run is completed", r=rid, s=st)
    w.rejected(ARTIFACT, "running or completed run", r=rid, h=sha(b"x"), c=b"x")
    w.run_sql("INSERT INTO audit_log (run_id, role, stage, function, allowed) VALUES (:r, 'planner', 'plan', 'x', false)",
              r=rid)


@pytest.mark.parametrize("ending", ["completed", "failed"])
def test_a_run_ends_only_with_no_stage_running_and_no_call_open(w, ending):
    rid = w.running(agents=True)
    st = w.stage(rid)
    end = (lambda: w.complete(rid, "insufficient")) if ending == "completed" else (lambda: w.fail(rid))
    with pytest.raises(IntegrityError, match="no stage is running and no model call is open"):
        end()
    call = w.call(rid, st)
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now() WHERE id = :s", s=st)
    with pytest.raises(IntegrityError, match="no stage is running and no model call is open"):
        end()
    w.finish_call(call, "interrupted", None)
    end()


# --- flags ---------------------------------------------------------------------------------------

def flag(w, rid):
    return w.val("INSERT INTO flag (run_id, kind, category, compared_values) "
                 "VALUES (:r, 'values_differ', 'differ beyond tolerance', '{\"a\": 1.0}') RETURNING id", r=rid)


def test_a_flag_is_classified_once_before_the_freeze(w):
    rid = w.running()
    f = flag(w, rid)
    w.rejected("UPDATE flag SET compared_values = '{}' WHERE id = :f", "classification", f=f)
    w.run_sql("UPDATE flag SET critic_class = 'comparable', critic_reason = 'same test', classified_at = now() "
              "WHERE id = :f", f=f)
    w.rejected("UPDATE flag SET critic_class = 'other', classified_at = now() WHERE id = :f", "classified once", f=f)
    w.rejected("DELETE FROM flag", "never deleted")


def test_flags_stop_at_the_freeze(w):
    rid, _, recs = w.frozen()
    w.rejected("INSERT INTO flag (run_id, kind, category) VALUES (:r, 'k', 'c')", "after the dataset freeze", r=rid)


def test_a_flag_names_records_of_its_own_run(w):
    rid, other = w.locked(), w.locked()
    f = flag(w, rid)
    w.run_sql("INSERT INTO flag_record VALUES (:f, :c)", f=f, c=w.record(rid))
    w.rejected("INSERT INTO flag_record VALUES (:f, :c)", "its own run", f=f, c=w.record(other))


# --- analysis results (owner's addition 3) ------------------------------------------------------------

def test_results_come_after_the_freeze(w):
    rid = w.running()
    w.lock(rid)
    primary = w.analysis_set(rid)
    with pytest.raises(IntegrityError, match="after the dataset freeze"):
        w.result(rid, primary, n=0)


@pytest.mark.parametrize("column, value, match", [
    ("check2_passed", "true", "ck_analysis_result_check2_consistent"),  # 1 group
    ("std_error", "1.0", "ck_analysis_result_std_error_iff_check2"),
    ("p_value", "0.01", "ck_analysis_result_p_value_iff_check2"),
    ("resid_df", "5", "ck_analysis_result_resid_df_definition"),
])
def test_the_validity_checks_cannot_be_waived(w, column, value, match):
    """One group: check 2 fails, so no uncertainty and no p-value can be stored. Step 7: under "use
    what is available", so that the result is not withheld (owner's decision 1) and each constraint
    is the one that refuses."""
    rid, sets, _ = w.frozen(option="use_available")
    rid_value = w.result(rid, sets["primary"], groups=1)
    assert w.rows("SELECT check2_passed, std_error, p_value FROM analysis_result WHERE id = :a", a=rid_value) == [
        (False, None, None)]
    rid2, sets2, _ = w.frozen(option="use_available")
    columns = {"run_id": rid2, "scope": "'pooled'", "analysis_set_id": sets2["primary"], "n_records": 4,
               "n_alloys": 1, "n_groups": 1, "n_groups_informative": 1, "resid_df": 2, "check1_passed": "true",
               "check2_passed": "false",
               "minimums_met": "false", "estimate": 1.0}
    columns[column] = value
    w.rejected(f"INSERT INTO analysis_result ({', '.join(columns)}) VALUES ({', '.join(map(str, columns.values()))})",
               match)


def test_check_one_failing_means_no_estimate(w):
    rid, sets, _ = w.frozen(n=1, mins=(1, 1, 1, 1))
    w.rejected("INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, "
               "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met, estimate) "
               "VALUES (:r, 'pooled', :s, 1, 0, 1, 1, 0, false, false, false, 5.0)",
               "ck_analysis_result_estimate_iff_check1", r=rid, s=sets["primary"])
    w.result(rid, sets["primary"], n=1, alloys=0, groups=1, mins=(1, 1, 1, 1))


@pytest.mark.parametrize("n, alloys, groups, match", [
    (1, 1, 1, "ck_analysis_result_two_records_per_alloy"),  # one record cannot show two grain sizes
    (4, 1, 5, "ck_analysis_result_groups_within_records"),
    (4, 0, 0, "ck_analysis_result_records_have_a_group"),
])
def test_stored_counts_must_be_consistent(w, n, alloys, groups, match):
    """Review finding 5: necessary conditions on the stored counts. The full validity
    rules of PRD 5.7 are computed and tested in step 7."""
    rid, sets, _ = w.frozen(n=n, mins=(1, 1, 1, 1))
    with pytest.raises(IntegrityError, match=match):
        w.result(rid, sets["primary"], n=n, alloys=alloys, groups=groups, mins=(1, 1, 1, 1))


def test_the_display_label_no_longer_bounds_the_alloy_count(w):
    """Step 7 review, finding 2 (changed from the case "(4, 2, 2): cannot exceed the distinct alloys"
    of test_stored_counts_must_be_consistent): the trigger no longer bounds the alloy count by the
    display label, which is rounded to 0.1 at.% while the plan's same-alloy rule may be finer. Two
    alloys in a set whose records share one label are stored; two records per alloy remain required."""
    rid, sets, _ = w.frozen(n=4, mins=(1, 1, 1, 1))
    assert w.val("SELECT count(DISTINCT r.alloy) FROM analysis_set_record sr JOIN record r ON r.id = sr.record_id "
                 "WHERE sr.analysis_set_id = :s", s=sets["primary"]) == 1
    w.result(rid, sets["primary"], n=4, alloys=2, groups=2, mins=(1, 1, 1, 1))
    assert w.val("SELECT n_alloys FROM analysis_result WHERE run_id = :r", r=rid) == 2


def test_one_result_per_run_and_scope_on_the_right_set(w):
    rid, sets, _ = w.frozen(n=4, per_source={"mpea": 3, "tamu_fcc": 1}, keys=["no_exclusions"])
    w.result(rid, sets["primary"])
    with pytest.raises(IntegrityError, match="uq_analysis_result_scope"):
        w.result(rid, sets["primary"])
    with pytest.raises(IntegrityError, match="use the primary set"):
        w.result(rid, sets["no_exclusions"], scope="pooled", n=0)
    with pytest.raises(IntegrityError, match="uses a sensitivity set"):
        w.result(rid, sets["primary"], scope="sensitivity")
    w.rejected("INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, "
               "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met) "
               "VALUES (:r, 'per_source', :s, 4, 0, 1, 1, 3, false, false, false)",
               "ck_analysis_result_source_iff_per_source", r=rid, s=sets["primary"])
    w.result(rid, sets["primary"], scope="per_source", source="mpea", n=3, alloys=1, groups=2)
    w.result(rid, sets["primary"], scope="per_source", source="tamu_fcc", n=1, alloys=0, groups=1)
    with pytest.raises(IntegrityError, match="uq_analysis_result_scope"):
        w.result(rid, sets["primary"], scope="per_source", source="mpea", n=3, alloys=1, groups=2)
    w.result(rid, sets["no_exclusions"], scope="sensitivity", n=0, alloys=0, groups=0)
    w.rejected("UPDATE analysis_result SET estimate = 1", "append-only")


def test_counts_must_match_the_set_used(w):
    rid, sets, _ = w.frozen(n=4, per_source={"mpea": 3, "tamu_fcc": 1})
    with pytest.raises(IntegrityError, match="n_records must equal"):
        w.result(rid, sets["primary"], n=5)
    with pytest.raises(IntegrityError, match="n_records must equal"):
        w.result(rid, sets["primary"], scope="per_source", source="mpea", n=4)  # restricted to MPEA: 3


def test_minimums_met_must_agree_with_the_plan(w):
    rid, sets, _ = w.frozen(mins=(4, 1, 2, 1))
    with pytest.raises(IntegrityError, match="minimums_met must agree"):
        w.result(rid, sets["primary"], minimums_met=False)


# --- calibration --------------------------------------------------------------------------------------

# Step 7 (migration 0004): a row of an analysis names its method (here 'fixed'); the run-level row none.
CALIBRATION = ("INSERT INTO calibration_result (run_id, analysis_result_id, method, status, reason, assumptions, "
               "n_simulations, seed, null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, "
               "effect_ci_high, confidence_flag) VALUES (:r, :a, CASE WHEN CAST(:a AS bigint) IS NULL THEN NULL "
               "ELSE 'fixed' END, :st, :re, {numbers})")
NUMBERS = "'{\"scatter\": 60}', 2000, 7, 0.072, 0.061, 0.084, 1.0, 0.998, 1.0, 'over_confident'"
NONE = "NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL"


def test_calibration_is_computed_exactly_when_inference_is_valid(w):
    rid, sets, _ = w.frozen(keys=["one_group"])
    valid = w.result(rid, sets["primary"])
    w.run_sql(CALIBRATION.format(numbers=NUMBERS), r=rid, a=valid, st="computed", re=None)
    w.rejected(CALIBRATION.format(numbers=NONE), "computed exactly when", r=rid, a=valid, st="unavailable",
               re="insufficient_groups")
    w.rejected("DELETE FROM calibration_result", "append-only")


def test_calibration_unavailable_states_a_matching_reason(w):
    rid, sets, _ = w.frozen(n=2, per_source={"mpea": 1, "tamu_fcc": 1}, mins=(1, 1, 1, 1))
    w.result(rid, sets["primary"], n=2, alloys=0, groups=2, mins=(1, 1, 1, 1))  # step 7: the pooled row first
    one_group = w.result(rid, sets["primary"], scope="per_source", source="mpea", n=1, alloys=0, groups=1,
                         mins=(1, 1, 1, 1))
    w.rejected(CALIBRATION.format(numbers=NUMBERS), "computed exactly when", r=rid, a=one_group, st="computed",
               re=None)
    w.rejected(CALIBRATION.format(numbers=NONE), "must match the validity checks", r=rid, a=one_group,
               st="unavailable", re="insufficient_groups")
    w.rejected(CALIBRATION.format(numbers=NONE), "ck_calibration_result_unavailable_has_reason_only",
               r=rid, a=one_group, st="unavailable", re=None)
    w.run_sql(CALIBRATION.format(numbers=NONE), r=rid, a=one_group, st="unavailable", re="coefficient_not_fitted")


def test_run_level_calibration_only_when_no_dataset_was_frozen(w):
    rid = w.running()
    w.rejected(CALIBRATION.format(numbers=NONE), "ck_calibration_result_run_level_only_without_freeze",
               r=rid, a=None, st="unavailable", re="insufficient_groups")
    w.run_sql(CALIBRATION.format(numbers=NONE), r=rid, a=None, st="unavailable", re="no_dataset_frozen")
    frozen, _, _ = w.frozen()
    w.rejected(CALIBRATION.format(numbers=NONE), "calibration is reported per analysis",
               r=frozen, a=None, st="unavailable", re="no_dataset_frozen")


def test_calibration_intervals_contain_their_share(w):
    rid, sets, _ = w.frozen()
    valid = w.result(rid, sets["primary"])
    bad = NUMBERS.replace("0.072, 0.061, 0.084", "0.072, 0.080, 0.084")
    w.rejected(CALIBRATION.format(numbers=bad), "ck_calibration_result_null_interval",
               r=rid, a=valid, st="computed", re=None)


# --- model calls and totals (owner decision, question 5) ------------------------------------------------

def test_a_model_call_is_recorded_before_the_request_and_finished_once(w):
    rid = w.running(agents=True)
    st = w.stage(rid)
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost, status, "
               "input_tokens, output_tokens, cached_tokens, cost, finished_at) VALUES (:r, :s, 'planner', 'm', 'p', 1, "
               "'succeeded', 1, 1, 0, 0.1, now())", "before the request", r=rid, s=st)
    call = w.call(rid, st)
    with pytest.raises(IntegrityError, match="ck_model_call_succeeded_has_usage"):
        w.finish_call(call, "succeeded", usage=None)
    w.finish_call(call, "succeeded")
    with pytest.raises(IntegrityError, match="finished exactly once"):
        w.finish_call(call, "failed", usage=None)
    w.rejected("DELETE FROM model_call", "never deleted")


def test_model_call_usage_rules(w):
    rid = w.running(agents=True)
    st = w.stage(rid)
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
               "VALUES (:r, :s, 'planner', 'm', '', 1)", "ck_model_call_model_and_prices_named", r=rid, s=st)
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version) "
               "VALUES (:r, :s, 'planner', 'm', 'p')", "max_cost", r=rid, s=st)
    partial = w.call(rid, st)
    w.rejected("UPDATE model_call SET status = 'failed', input_tokens = 5, finished_at = now() WHERE id = :c",
               "ck_model_call_failed_usage_all_or_none", c=partial)
    w.rejected("UPDATE model_call SET status = 'succeeded', input_tokens = -1, output_tokens = 1, cached_tokens = 0, "
               "cost = 0, finished_at = now() WHERE id = :c", "ck_model_call_usage_not_negative", c=partial)
    w.rejected("UPDATE model_call SET status = 'failed', max_cost = 0, finished_at = now() WHERE id = :c",
               "before the request cannot change", c=partial)
    # A call whose stage belongs to another run. Step 8a (0005): every call names its invocation, and
    # the call must have the invocation's run, stage and role, which the insert trigger checks before
    # the foreign key on (stage, run) is reached; the foreign key still holds for the invocation.
    other = w.running()
    inv = w.invocation(rid, st)
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, price_table_version, "
               "max_cost) VALUES (:r, :s, :i, 'planner', 'm', 'p', 1)", "its invocation's run, stage and role",
               r=other, s=st, i=inv)


def test_totals_are_the_sum_of_the_calls_and_unreported_calls_count_at_their_bound(w):
    rid = w.running(agents=True)
    # Step 8a review (finding 6): the Curator has no run invocation, so the second stage is the Critic's.
    planner, critic = w.stage(rid), w.stage(rid, "critic", "critic")
    ok = w.call(rid, planner, max_cost=0.50)
    w.finish_call(ok, "succeeded", (1000, 200, 100, 0.0123))
    charged = w.call(rid, planner, max_cost=0.40)
    w.finish_call(charged, "failed", (500, 0, 0, 0.0040))         # failed, but the provider reported usage
    lost = w.call(rid, critic, max_cost=0.30)
    w.finish_call(lost, "failed", None)                           # failed without usage: may still be charged
    w.call(rid, critic, max_cost=0.20)                            # still started (e.g. the worker died)
    columns = "calls, input_tokens, output_tokens, cached_tokens, reported_cost, unconfirmed_calls, " \
              "unconfirmed_cost_bound, cap_cost"
    run_total = w.rows(f"SELECT {columns} FROM model_call_totals_by_run WHERE run_id = :r", r=rid)[0]
    assert tuple(map(float, run_total)) == (4, 1500, 200, 100, 0.0163, 2, 0.50, 0.5163)
    by_stage = w.rows(f"SELECT stage, {columns} FROM model_call_totals_by_stage WHERE run_id = :r ORDER BY stage",
                      r=rid)
    assert [(s, float(rep), float(cap)) for s, _, _, _, _, rep, _, _, cap in by_stage] == [
        ("critic", 0.0, 0.50), ("planner", 0.0163, 0.0163)]
    query = w.rows("SELECT h.id FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id "
                   "JOIN run r ON r.hypothesis_version_id = v.id WHERE r.id = :r", r=rid)[0][0]
    assert float(w.val("SELECT cap_cost FROM model_call_totals_by_query WHERE hypothesis_id = :h", h=query)) == 0.5163
    assert float(w.val("SELECT sum(cap_cost) FROM model_call_totals_by_month")) == 0.5163
    direct = w.rows("SELECT sum(cost), sum(coalesce(cost, max_cost)) FROM model_call")[0]
    assert tuple(map(float, direct)) == (0.0163, 0.5163)


def test_small_costs_are_stored_exactly(w):
    """Review finding 7: numeric without a fixed scale; nothing rounds to zero."""
    from decimal import Decimal
    rid = w.running(agents=True)
    call = w.call(rid, w.stage(rid), max_cost=Decimal("1E-12"))
    w.finish_call(call, "succeeded", (1, 1, 0, Decimal("3E-13")))
    w.call(rid, w.stage(rid, "critic", "critic"), max_cost=Decimal("2E-12"))  # step 8a review: not the Curator
    row = w.rows("SELECT reported_cost, unconfirmed_cost_bound, cap_cost FROM model_call_totals_by_run "
                 "WHERE run_id = :r", r=rid)[0]
    assert row == (Decimal("3E-13"), Decimal("2E-12"), Decimal("2.3E-12"))
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
               "VALUES (:r, :s, 'planner', 'm', 'p', 0)", "ck_model_call_max_cost_positive",
               r=rid, s=w.val("SELECT min(id) FROM stage_result"))


@pytest.mark.parametrize("value, match", [
    ("NaN", "ck_model_call_money_finite"), ("Infinity", "ck_model_call_money_finite"),
    ("-Infinity", "ck_model_call_max_cost_positive"),
])
def test_max_cost_must_be_finite(w, value, match):
    """Re-check item 3: NaN and infinity would contaminate totals and caps."""
    rid = w.running()
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
               "VALUES (:r, :s, 'planner', 'm', 'p', CAST(:v AS numeric))", match, r=rid, s=w.stage(rid), v=value)


@pytest.mark.parametrize("value, match", [
    ("NaN", "ck_model_call_money_finite"), ("Infinity", "ck_model_call_money_finite"),
    ("-Infinity", "ck_model_call_usage_not_negative"),
])
def test_reported_cost_must_be_finite(w, value, match):
    rid = w.running(agents=True)
    call = w.call(rid, w.stage(rid))
    w.rejected("UPDATE model_call SET status = 'succeeded', input_tokens = 1, output_tokens = 1, cached_tokens = 0, "
               "cost = CAST(:v AS numeric), finished_at = now() WHERE id = :c", match, c=call, v=value)
    assert w.val("SELECT status FROM model_call WHERE id = :c", c=call) == "started"


def test_call_times_are_set_by_the_database(w):
    rid = w.running(agents=True)
    st = w.stage(rid)
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost, started_at) "
               "VALUES (:r, :s, 'planner', 'm', 'p', 1, now() - interval '40 days')", "started_at is set by the database",
               r=rid, s=st)
    call = w.call(rid, st)
    w.rejected("UPDATE model_call SET status = 'interrupted', finished_at = now() - interval '1 day' WHERE id = :c",
               "finished_at is set by the database", c=call)


def test_a_run_without_calls_totals_zero(w):
    rid = w.running()
    assert tuple(map(float, w.rows("SELECT calls, reported_cost, cap_cost FROM model_call_totals_by_run "
                                   "WHERE run_id = :r", r=rid)[0])) == (0, 0, 0)


def test_no_table_stores_token_or_cost_totals(w):
    columns = w.rows("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public' "
                     "AND table_name IN (SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' "
                     "AND table_schema = 'public') AND (column_name LIKE '%token%' OR column_name LIKE '%cost%')")
    assert {t for t, _ in columns} == {"model_call"}


@pytest.mark.parametrize("finishing", [False, True])
def test_a_commentator_stage_cannot_be_relabelled(w, finishing):
    """Re-check item 4: the role is frozen with the stage name, also on a completed
    run and also in the update that finishes the stage."""
    rid = w.running()
    w.complete(rid, "insufficient")
    st = w.stage(rid, "commentator", "commentator")
    finish = ", status = 'done', finished_at = now()" if finishing else ""
    for role in ("'planner'", "NULL"):
        w.rejected(f"UPDATE stage_result SET role = {role}{finish} WHERE id = :s", "cannot change", s=st)
    assert w.rows("SELECT role, status FROM stage_result WHERE id = :s", s=st) == [("commentator", "running")]


def test_a_running_stage_cannot_be_relabelled(w):
    rid = w.running()
    st = w.stage(rid, "planner", "planner")
    w.rejected("UPDATE stage_result SET role = 'critic' WHERE id = :s", "cannot change", s=st)
    w.run_sql("UPDATE stage_result SET output = '{}' WHERE id = :s", s=st)  # other fields still update


def test_a_finished_stage_result_is_final(w):
    rid = w.running()
    st = w.stage(rid)
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=st)
    w.rejected("UPDATE stage_result SET output = '{\"changed\": true}' WHERE id = :s", "is final", s=st)
    w.rejected("DELETE FROM stage_result", "never deleted")


# --- commentary ---------------------------------------------------------------------------------------

def test_commentary_comes_after_completion_and_lists_mismatches(w):
    rid = w.running()
    early = w.stage(rid, "commentator", "commentator")
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now() WHERE id = :s", s=early)
    sql = ("INSERT INTO commentary (run_id, stage_result_id, status, text, model, number_check, mismatches) "
           "VALUES (:r, :s, :st, :t, 'other-model', :nc, CAST(:mm AS jsonb))")
    w.rejected(sql, "after the run is completed", r=rid, s=early, st="written", t="x", nc="all_match", mm=None)
    w.complete(rid, "insufficient")
    st = w.stage(rid, "commentator", "commentator", attempt=2)  # the Commentator's stage after completion
    w.rejected(sql, "ck_commentary_mismatches_listed", r=rid, s=st, st="written", t="x", nc="mismatches", mm=None)
    w.rejected(sql, "ck_commentary_written_has_text_and_check", r=rid, s=st, st="written", t=None, nc=None, mm=None)
    w.run_sql(sql, r=rid, s=st, st="written", t="k = 999", nc="mismatches", mm='["999"]')
    w.rejected("UPDATE commentary SET text = 'changed'", "append-only")


# --- files (owner decision: data files only, 5 MiB) ------------------------------------------------------

SOURCE_FILE = "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:sv, :p, :h, :c)"
ARTIFACT = ("INSERT INTO artifact (run_id, kind, filename, media_type, sha256, content) "
            "VALUES (:r, 'workbook', 'run.xlsx', 'application/octet-stream', :h, :c)")


def test_source_files_are_data_files_up_to_5_mib(w):
    sv = w.new_version("mpea", "v2")  # files are added before the version is sealed
    at_limit, over = b"x" * MAX_FILE_BYTES, b"x" * (MAX_FILE_BYTES + 1)
    w.run_sql(SOURCE_FILE, sv=sv, p="MPEA_dataset.csv", h=sha(at_limit), c=at_limit)
    w.rejected(SOURCE_FILE, "ck_source_file_max_size", sv=sv, p="big.csv", h=sha(over), c=over)
    w.rejected(SOURCE_FILE, "ck_source_file_safe_data_file_path", sv=sv, p="zenodo_archive.zip", h=sha(b"z"), c=b"z")
    w.rejected(SOURCE_FILE, "ck_source_file_sha256_matches_content", sv=sv, p="other.csv", h=sha(b"a"), c=b"b")
    w.run_sql(SOURCE_FILE, sv=sv, p="Grain_Size_Summary_v3.xlsx", h=sha(b"x"), c=b"x")
    w.rejected("UPDATE source_file SET content = 'y'", "append-only")
    w.rejected("UPDATE source_version SET label = 'v9' WHERE id = :v", "only change to a source version is sealing",
               v=sv)
    w.rejected("UPDATE source_version SET label = 'v9' WHERE id = :v", "sealed source version cannot change",
               v=w.version["mpea"])


# --- source versions: sealed files and their interpretation (review finding 4) ------------------------

def test_files_cannot_be_added_after_sealing(w):
    sv = w.new_version("mpea", "v2")
    w.add_file(sv, "a.csv", b"a")
    w.seal(sv)
    with pytest.raises(IntegrityError, match="sealed source version"):
        w.add_file(sv, "b.csv", b"b")


def test_sealing_needs_files_and_the_fingerprint_of_the_file_list(w):
    sv = w.new_version("mpea", "v2")
    with pytest.raises(IntegrityError, match="at least one file"):
        w.seal(sv, fingerprint="0" * 64)
    files = {"b.csv": b"second", "a.csv": b"first"}
    for path, content in files.items():
        w.add_file(sv, path, content)
    with pytest.raises(IntegrityError, match="files digest and the interpretation settings"):
        w.seal(sv, fingerprint="0" * 64)
    w.rejected("UPDATE source_version SET sealed_at = now() - interval '1 day', fingerprint = :fp WHERE id = :v",
               "set by the database", v=sv, fp=w.fingerprint(sv))
    w.rejected("UPDATE source_version SET sealed_at = now(), fingerprint = :fp, files_digest = :d WHERE id = :v",
               "files_digest must be the SHA-256", v=sv, fp=w.fingerprint(sv), d="0" * 64)
    w.seal(sv)
    assert w.rows("SELECT files_digest, fingerprint FROM source_version WHERE id = :v", v=sv) == [
        (files_digest(files), w.fingerprint(sv, files))]
    with pytest.raises(IntegrityError, match="sealed source version cannot change"):
        w.seal(sv)
    w.rejected("DELETE FROM source_version WHERE id = :v", "never deleted", v=sv)


@pytest.mark.parametrize("path", [
    "a.csv\n" + "0" * 64 + "  b.csv",   # the re-check's collision: a line break inside a path
    "a.csv\r", "a b.csv", "../outside.csv", "/abs.csv", "a.csv.zip", "café.csv", "",
])
def test_unsafe_file_paths_are_rejected(w, path):
    """Re-check item 2: a safe character set, anchored at both ends."""
    with pytest.raises(IntegrityError, match="ck_source_file_safe_data_file_path"):
        w.add_file(w.new_version("mpea", "v2"), path, b"x")


def test_the_same_files_under_revised_settings_seal_as_a_new_version(w):
    """Re-check item 2: the identity covers the interpretation settings, so a corrected
    grouping unit can be sealed with the same files; identical files and settings are
    still a duplicate."""
    files = {"tamu_fcc.csv": b"tamu_fcc,data\n"}
    first = w.version["tamu_fcc"]
    assert w.files(first) == files and w.settings(first)[2] == "dataset"
    w.run_sql("UPDATE source SET grouping_unit = 'batch' WHERE key = 'tamu_fcc'")
    revised = w.new_version("tamu_fcc", "v1-batches")
    w.add_file(revised, "tamu_fcc.csv", files["tamu_fcc.csv"])
    w.seal(revised)
    rows = w.rows("SELECT files_digest, fingerprint, grouping_unit FROM source_version WHERE id IN (:a, :b) "
                  "ORDER BY id", a=first, b=revised)
    assert rows[0][0] == rows[1][0] == files_digest(files)  # the same files
    assert rows[0][1] != rows[1][1]                          # a different identity
    assert [r[2] for r in rows] == ["dataset", "batch"]
    duplicate = w.new_version("tamu_fcc", "v1-batches-again")
    w.add_file(duplicate, "tamu_fcc.csv", files["tamu_fcc.csv"])
    with pytest.raises(IntegrityError, match="uq_source_version_source_id_fingerprint"):
        w.seal(duplicate)


def test_a_new_version_starts_unsealed(w):
    w.rejected("INSERT INTO source_version (source_id, label, obtained_on, sealed_at, fingerprint) "
               "VALUES (:s, 'v2', '2026-10-05', now(), :fp)", "sealed after its files are added",
               s=w.source["mpea"], fp=FP)


def test_only_a_sealed_version_can_be_used_by_a_run(w):
    unsealed = w.new_version("mpea", "v2")
    vid = w.dispatched()
    rid = w.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
    w.rejected("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
               "VALUES (:r, :s, :sv, 'pending')", "only a sealed source version", r=rid, s=w.source["mpea"],
               sv=unsealed)


def test_a_version_keeps_its_own_interpretation_settings(w):
    """Changing the source's settings affects only versions made afterwards."""
    sv = w.version["mpea"]
    assert w.rows("SELECT source_type, data_kind, grouping_unit FROM source_version WHERE id = :v", v=sv) == [
        ("uploaded_table", "measured", "paper")]
    w.run_sql("UPDATE source SET grouping_unit = 'dataset', data_kind = 'computed', enabled = false WHERE key = 'mpea'")
    assert w.rows("SELECT data_kind, grouping_unit FROM source_version WHERE id = :v", v=sv) == [("measured", "paper")]
    later = w.new_version("mpea", "v2")
    assert w.rows("SELECT data_kind, grouping_unit FROM source_version WHERE id = :v", v=later) == [
        ("computed", "dataset")]
    w.rejected("INSERT INTO source_version (source_id, label, obtained_on, grouping_unit) "
               "VALUES (:s, 'v3', '2026-10-05', 'paper')", "copies its settings from the source", s=w.source["mpea"])
    w.rejected("UPDATE source_version SET grouping_unit = 'dataset' WHERE id = :v", "sealed source version", v=sv)


def test_a_record_has_its_versions_kind_of_data(w):
    rid = w.locked()
    with pytest.raises(IntegrityError, match="kind of data of its source version"):
        w.record(rid, kind="computed")


def test_artifacts_up_to_5_mib(w):
    rid = w.running()
    at_limit, over = b"x" * MAX_FILE_BYTES, b"x" * (MAX_FILE_BYTES + 1)
    w.run_sql(ARTIFACT, r=rid, h=sha(at_limit), c=at_limit)
    w.rejected(ARTIFACT, "ck_artifact_max_size", r=rid, h=sha(over), c=over)
    w.rejected(ARTIFACT, "ck_artifact_sha256_matches_content", r=rid, h=sha(b"a"), c=b"b")
    w.rejected("DELETE FROM artifact", "append-only")


# --- fixed lists and the audit log ----------------------------------------------------------------------

def test_domains_are_seeded_and_fixed(w):
    rows = w.rows("SELECT key, supported, profile_name FROM domain ORDER BY id")
    assert rows == [("grain_size_strengthening", True, "grain_size_strengthening"),
                    ("fatigue", False, None), ("other", False, None)]
    w.rejected("UPDATE domain SET supported = true", "append-only")
    w.rejected("INSERT INTO domain (key, name, supported) VALUES ('x', 'X', true)", "ck_domain_supported_has_profile")


def test_the_audit_log_is_append_only(w):
    w.run_sql("INSERT INTO audit_log (role, stage, function, allowed) VALUES ('planner', 'plan', 'counts', true)")
    w.rejected("UPDATE audit_log SET allowed = false", "append-only")
    w.rejected("DELETE FROM audit_log", "append-only")
    w.rejected("TRUNCATE audit_log", "append-only")


# --- the protocol's entry point (re-check item 1) ---------------------------------------------------------

def test_write_lock_locks_a_run_or_a_version(w):
    rid = w.running()
    vid = w.val("SELECT hypothesis_version_id FROM run WHERE id = :r", r=rid)
    assert w.val("SELECT hc_write_lock(p_run => :r)", r=rid) == "running"
    assert w.val("SELECT hc_write_lock(p_version => :v)", v=vid) == "dispatched"
    assert w.val("SELECT hc_write_lock(p_run => :r, p_version => :v)", r=rid, v=vid) == "running"
    w.rejected("SELECT hc_write_lock(p_run => :r, p_version => :v)", "does not belong", r=rid, v=w.dispatched())
    w.rejected("SELECT hc_write_lock(p_run => 999999)", "no run 999999")
    w.rejected("SELECT hc_write_lock()", "needs a run or a hypothesis version")
