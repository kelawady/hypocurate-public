"""Step 3: the rules the database enforces (PRD 7, with the owner's decisions of
2026-10-04/05). Every rule has an allowed case and a rejected case, on a freshly
migrated scratch database. Rejections by a trigger read "hypocurate: ..."; rejections
by a CHECK name the constraint."""
import pytest
from sqlalchemy.exc import IntegrityError

from hypocurate.db.models import MAX_FILE_BYTES
from model_builder import FP, World, sha


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
               "verdict = 'supported' WHERE id = :r", "ck_run_verdict_iff_sufficient", r=rid)


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
    "UPDATE run SET status = 'completed', completed_at = now(), outcome = 'insufficient' WHERE id = :r",
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
    """Check 1 passes, check 2 fails (2 records, 1 alloy: no residual degree of freedom)."""
    rid, sets, _ = w.frozen(n=2, mins=(1, 1, 1, 1))
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
    rid = w.run(sources=())
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
    other = w.val("INSERT INTO source_version (source_id, label, fingerprint, obtained_on) "
                  "VALUES (:s, 'v2', :fp, '2026-10-05') RETURNING id", s=w.source["mpea"], fp="c" * 64)
    w.rejected("UPDATE run_source SET source_version_id = :sv WHERE run_id = :r AND source_id = :s",
               "cannot change", sv=other, r=rid, s=w.source["mpea"])


def nothing_found(w, rid):
    return w.rows("SELECT nothing_found, searched_sources, failed_sources, not_searched_sources "
                  "FROM run_nothing_found WHERE run_id = :r", r=rid)[0]


def test_a_failed_source_is_never_missing_evidence(w):
    """One source failed, the other has missing evidence: the run is missing evidence
    in the sources searched, and the failed source is named as failed and not searched."""
    rid = w.running()
    w.search(rid, "mpea", "searched", "missing_evidence")
    w.search(rid, "tamu_fcc", "failed", "failed_search", "unreachable")
    w.complete(rid, "insufficient")
    assert nothing_found(w, rid) == ("missing_evidence", ["mpea"], ["tamu_fcc"], ["tamu_fcc"])


def test_no_source_searched_is_failed_search(w):
    rid = w.running(sources=("mpea",))
    w.search(rid, "mpea", "failed", "failed_search", "unreachable")
    w.complete(rid, "insufficient")
    assert nothing_found(w, rid) == ("failed_search", [], ["mpea"], ["mpea", "tamu_fcc"])


def test_a_reported_negative_result_is_kept_distinct(w):
    rid = w.running()
    w.search(rid, "mpea", "searched", "reported_negative")
    w.search(rid, "tamu_fcc", "searched", "missing_evidence")
    w.complete(rid, "insufficient")
    assert nothing_found(w, rid) == ("reported_negative", ["mpea", "tamu_fcc"], [], [])


def test_records_found_but_insufficient_is_missing_evidence(w):
    rid = w.running(sources=("mpea",))
    w.search(rid, "mpea", "searched")
    w.complete(rid, "insufficient")
    assert nothing_found(w, rid) == ("missing_evidence", ["mpea"], [], ["tamu_fcc"])


def test_nothing_found_applies_only_to_insufficient_runs(w):
    rid = w.running()
    w.search(rid, "mpea", "searched")
    assert nothing_found(w, rid)[0] is None
    w.complete(rid, "partly_sufficient")
    assert nothing_found(w, rid)[0] is None


def test_run_has_no_stored_nothing_found_column(w):
    assert w.val("SELECT count(*) FROM information_schema.columns WHERE table_name = 'run' "
                 "AND column_name LIKE '%nothing%'") == 0


# --- records: stored is not analysed ---------------------------------------------------------

def test_records_are_never_updated_or_deleted(w):
    rid = w.running()
    rec = w.record(rid)
    for sql in ("UPDATE record SET alloy = 'other' WHERE id = :c", "UPDATE record SET harmonized = '{}' WHERE id = :c",
                "DELETE FROM record WHERE id = :c"):
        w.rejected(sql, "record is append-only", c=rec)
    w.rejected("TRUNCATE record CASCADE", "append-only")


def test_a_record_comes_from_a_source_version_its_run_recorded(w):
    rid = w.running(sources=("mpea",))
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
    rid = w.running()
    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, source_item_key, kind, harmonized, reported) "
               "VALUES (:r, :sv, '', 'measured', '{}', '{}')", "ck_record_item_key_not_empty",
               r=rid, sv=w.version["mpea"])
    w.rejected("INSERT INTO record (extraction_run_id, source_version_id, kind, harmonized, reported) "
               "VALUES (:r, :sv, 'measured', '{}', '{}')", "source_item_key", r=rid, sv=w.version["mpea"])
    w.record(rid, key="row-7")
    with pytest.raises(IntegrityError, match="uq_record_origin_per_run"):
        w.record(rid, key="row-7")
    w.record(rid, key="row-7", index=1)  # a second observation from the same row
    other_run = w.running()
    w.record(other_run, key="row-7")
    matched = w.rows("SELECT extraction_run_id FROM record WHERE source_version_id = :sv AND source_item_key = 'row-7' "
                     "AND item_index = 0 ORDER BY extraction_run_id", sv=w.version["mpea"])
    assert [r[0] for r in matched] == [rid, other_run]
    index = w.val("SELECT indexdef FROM pg_indexes WHERE indexname = 'ix_record_source_version_id_source_item_key'")
    assert index.endswith("(source_version_id, source_item_key)")


def test_eligibility_is_decided_only_under_a_locked_plan(w):
    rid = w.running()
    rec = w.record(rid)
    with pytest.raises(IntegrityError, match="under a locked plan"):
        w.decide(rid, rec)
    w.lock(rid)
    w.decide(rid, rec, eligible=False, rule="grain size below 0.1 um")
    w.rejected("UPDATE run_record SET eligible = true", "append-only")
    w.rejected("DELETE FROM run_record", "append-only")


def test_a_run_decides_only_on_its_own_records(w):
    other = w.running()
    rec = w.record(other)
    rid = w.running()
    w.lock(rid)
    with pytest.raises(IntegrityError, match="records extracted in that run"):
        w.decide(rid, rec)


def test_a_model_recalled_record_is_stored_but_never_eligible(w):
    rid = w.running()
    w.lock(rid)
    rec = w.record(rid, kind="model_recalled")
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
    """PRD 5.3, the reason for named sets: one survivor in primary, both in the sensitivity set."""
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
    rid, other = w.running(), w.running()
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
    ("check2_passed", "true", "ck_analysis_result_check2_definition"),  # 1 group
    ("std_error", "1.0", "ck_analysis_result_std_error_iff_check2"),
    ("p_value", "0.01", "ck_analysis_result_p_value_iff_check2"),
    ("resid_df", "5", "ck_analysis_result_resid_df_definition"),
])
def test_the_validity_checks_cannot_be_waived(w, column, value, match):
    """One group: check 2 fails, so no uncertainty and no p-value can be stored."""
    rid, sets, _ = w.frozen()
    rid_value = w.result(rid, sets["primary"], groups=1)
    assert w.rows("SELECT check2_passed, std_error, p_value FROM analysis_result WHERE id = :a", a=rid_value) == [
        (False, None, None)]
    rid2, sets2, _ = w.frozen()
    columns = {"run_id": rid2, "scope": "'pooled'", "analysis_set_id": sets2["primary"], "n_records": 4,
               "n_alloys": 1, "n_groups": 1, "resid_df": 2, "check1_passed": "true", "check2_passed": "false",
               "minimums_met": "false", "estimate": 1.0}
    columns[column] = value
    w.rejected(f"INSERT INTO analysis_result ({', '.join(columns)}) VALUES ({', '.join(map(str, columns.values()))})",
               match)


def test_check_one_failing_means_no_estimate(w):
    rid, sets, _ = w.frozen(n=1, mins=(1, 1, 1, 1))
    w.rejected("INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, resid_df, "
               "check1_passed, check2_passed, minimums_met, estimate) VALUES (:r, 'pooled', :s, 1, 0, 1, 0, false, "
               "false, false, 5.0)", "ck_analysis_result_estimate_iff_check1", r=rid, s=sets["primary"])
    w.result(rid, sets["primary"], n=1, alloys=0, groups=1, mins=(1, 1, 1, 1))


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
               "resid_df, check1_passed, check2_passed, minimums_met) "
               "VALUES (:r, 'per_source', :s, 4, 0, 0, 3, false, false, false)",
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

CALIBRATION = ("INSERT INTO calibration_result (run_id, analysis_result_id, status, reason, assumptions, "
               "n_simulations, seed, null_share, null_ci_low, null_ci_high, effect_share, effect_ci_low, "
               "effect_ci_high, confidence_flag) VALUES (:r, :a, :st, :re, {numbers})")
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
    rid = w.running()
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
    rid = w.running()
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
    other = w.running()
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
               "VALUES (:r, :s, 'planner', 'm', 'p', 1)", "fk_model_call_stage_result", r=other, s=st)


def test_totals_are_the_sum_of_the_calls_and_unreported_calls_count_at_their_bound(w):
    rid = w.running()
    planner, curator = w.stage(rid), w.stage(rid, "curator", "curator")
    ok = w.call(rid, planner, max_cost=0.50)
    w.finish_call(ok, "succeeded", (1000, 200, 100, 0.0123))
    charged = w.call(rid, planner, max_cost=0.40)
    w.finish_call(charged, "failed", (500, 0, 0, 0.0040))         # failed, but the provider reported usage
    lost = w.call(rid, curator, max_cost=0.30)
    w.finish_call(lost, "failed", None)                           # failed without usage: may still be charged
    w.call(rid, curator, max_cost=0.20)                           # still started (e.g. the worker died)
    columns = "calls, input_tokens, output_tokens, cached_tokens, reported_cost, unconfirmed_calls, " \
              "unconfirmed_cost_bound, cap_cost"
    run_total = w.rows(f"SELECT {columns} FROM model_call_totals_by_run WHERE run_id = :r", r=rid)[0]
    assert tuple(map(float, run_total)) == (4, 1500, 200, 100, 0.0163, 2, 0.50, 0.5163)
    by_stage = w.rows(f"SELECT stage, {columns} FROM model_call_totals_by_stage WHERE run_id = :r ORDER BY stage",
                      r=rid)
    assert [(s, float(rep), float(cap)) for s, _, _, _, _, rep, _, _, cap in by_stage] == [
        ("curator", 0.0, 0.50), ("planner", 0.0163, 0.0163)]
    query = w.rows("SELECT h.id FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id "
                   "JOIN run r ON r.hypothesis_version_id = v.id WHERE r.id = :r", r=rid)[0][0]
    assert float(w.val("SELECT cap_cost FROM model_call_totals_by_query WHERE hypothesis_id = :h", h=query)) == 0.5163
    assert float(w.val("SELECT sum(cap_cost) FROM model_call_totals_by_month")) == 0.5163
    direct = w.rows("SELECT sum(cost), sum(coalesce(cost, max_cost)) FROM model_call")[0]
    assert tuple(map(float, direct)) == (0.0163, 0.5163)


def test_a_run_without_calls_totals_zero(w):
    rid = w.running()
    assert tuple(map(float, w.rows("SELECT calls, reported_cost, cap_cost FROM model_call_totals_by_run "
                                   "WHERE run_id = :r", r=rid)[0])) == (0, 0, 0)


def test_no_table_stores_token_or_cost_totals(w):
    columns = w.rows("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public' "
                     "AND table_name IN (SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' "
                     "AND table_schema = 'public') AND (column_name LIKE '%token%' OR column_name LIKE '%cost%')")
    assert {t for t, _ in columns} == {"model_call"}


def test_a_finished_stage_result_is_final(w):
    rid = w.running()
    st = w.stage(rid)
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), output = '{}' WHERE id = :s", s=st)
    w.rejected("UPDATE stage_result SET output = '{\"changed\": true}' WHERE id = :s", "is final", s=st)
    w.rejected("DELETE FROM stage_result", "never deleted")


# --- commentary ---------------------------------------------------------------------------------------

def test_commentary_comes_after_completion_and_lists_mismatches(w):
    rid = w.running()
    st = w.stage(rid, "commentator", "commentator")
    sql = ("INSERT INTO commentary (run_id, stage_result_id, status, text, model, number_check, mismatches) "
           "VALUES (:r, :s, :st, :t, 'other-model', :nc, CAST(:mm AS jsonb))")
    w.rejected(sql, "after the run is completed", r=rid, s=st, st="written", t="x", nc="all_match", mm=None)
    w.complete(rid, "insufficient")
    w.rejected(sql, "ck_commentary_mismatches_listed", r=rid, s=st, st="written", t="x", nc="mismatches", mm=None)
    w.rejected(sql, "ck_commentary_written_has_text_and_check", r=rid, s=st, st="written", t=None, nc=None, mm=None)
    w.run_sql(sql, r=rid, s=st, st="written", t="k = 999", nc="mismatches", mm='["999"]')
    w.rejected("UPDATE commentary SET text = 'changed'", "append-only")


# --- files (owner decision: data files only, 5 MiB) ------------------------------------------------------

SOURCE_FILE = "INSERT INTO source_file (source_version_id, path, sha256, content) VALUES (:sv, :p, :h, :c)"
ARTIFACT = ("INSERT INTO artifact (run_id, kind, filename, media_type, sha256, content) "
            "VALUES (:r, 'workbook', 'run.xlsx', 'application/octet-stream', :h, :c)")


def test_source_files_are_data_files_up_to_5_mib(w):
    sv = w.version["mpea"]
    at_limit, over = b"x" * MAX_FILE_BYTES, b"x" * (MAX_FILE_BYTES + 1)
    w.run_sql(SOURCE_FILE, sv=sv, p="MPEA_dataset.csv", h=sha(at_limit), c=at_limit)
    w.rejected(SOURCE_FILE, "ck_source_file_max_size", sv=sv, p="big.csv", h=sha(over), c=over)
    w.rejected(SOURCE_FILE, "ck_source_file_data_file_type", sv=sv, p="zenodo_archive.zip", h=sha(b"z"), c=b"z")
    w.rejected(SOURCE_FILE, "ck_source_file_sha256_matches_content", sv=sv, p="other.csv", h=sha(b"a"), c=b"b")
    w.run_sql(SOURCE_FILE, sv=sv, p="Grain_Size_Summary_v3.xlsx", h=sha(b"x"), c=b"x")
    w.rejected("UPDATE source_file SET content = 'y'", "append-only")
    w.rejected("UPDATE source_version SET label = 'v9'", "append-only")


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
