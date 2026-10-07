"""Step 8b, milestone 3: creating, submitting, confirming and dispatching queries (pipeline/queries.py), and the
narrower question (owner, Q10, A2, A8, A9)."""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import pipeline_world as pw
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queries
from hypocurate.pipeline.agents.settings import RUN_ROLES, SETTINGS

CLAIM = "In FCC multi-principal-element alloys, yield strength rises as grain size falls"


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e
    e.dispose()


def rows(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def dispatched(engine, sources=("mpea", "tamu_fcc"), **kw):
    q = queries.create(engine, CLAIM, sources, sufficiency=kw.pop("sufficiency", "fixed_minimum"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    return q, queries.dispatch(engine, q.version_id, **kw)


def test_a_query_goes_from_draft_to_a_running_run(engine):
    q, rid = dispatched(engine, sources=("mpea",))
    assert q.number.startswith("Q-")
    assert rows(engine, "SELECT status, review_comment, sufficiency_option FROM hypothesis_version WHERE id = :v",
                v=q.version_id) == [("dispatched", "domain confirmed at the command line by Ada Reviewer",
                                     "fixed_minimum")]
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued"
    queries.start(engine, rid)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    sources = rows(engine, "SELECT s.key, rs.search_status, rs.source_version_id IS NOT NULL FROM run_source rs "
                           "JOIN source s ON s.id = rs.source_id WHERE rs.run_id = :r ORDER BY s.key", r=rid)
    assert sources == [("mpea", "pending", True), ("tamu_fcc", "not_selected", False)]
    newest = one(engine, "SELECT max(sv.id) FROM source_version sv JOIN source s ON s.id = sv.source_id "
                         "WHERE s.key = 'mpea' AND sv.sealed_at IS NOT NULL")
    assert one(engine, "SELECT source_version_id FROM run_source rs JOIN source s ON s.id = rs.source_id "
                       "WHERE rs.run_id = :r AND s.key = 'mpea'", r=rid) == newest


def test_dispatch_records_the_settings_version_of_each_run_role(engine):
    _, rid = dispatched(engine)
    got = rows(engine, "SELECT ras.role, a.model FROM run_agent_setting ras JOIN agent_setting a "
                       "ON a.id = ras.agent_setting_id WHERE ras.run_id = :r ORDER BY ras.role", r=rid)
    assert got == sorted((role, SETTINGS[role]["model"]) for role in RUN_ROLES)
    assert "curator" not in {r for r, _ in got}  # the Curator never runs in a run (step 8a)


def test_the_querys_option_is_chosen_before_dispatch(engine):
    q, rid = dispatched(engine, sufficiency="use_available")
    assert one(engine, "SELECT sufficiency_option FROM hypothesis_version WHERE id = :v", v=q.version_id) == \
        "use_available"


def test_a_fixed_plan_and_a_test_run_are_recorded_at_dispatch(engine):
    _, rid = dispatched(engine, fixed_plan=True, constructed_test_data=True)
    assert rows(engine, "SELECT fixed_plan, experiment_flags FROM run WHERE id = :r", r=rid) == [
        (True, {"constructed_test_data": True})]


@pytest.mark.parametrize("by", ["", "   ", None, "x" * 201])
def test_the_domain_is_confirmed_only_by_a_named_person(engine, by):
    q = queries.create(engine, CLAIM, ("mpea",))
    queries.submit(engine, q.version_id)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.confirm_domain(engine, q.version_id, by=by)
    assert refused.value.code == "reviewer_missing"


def test_an_unsupported_domain_cannot_be_dispatched_and_the_message_says_why(engine):
    """PRD 14.3: a query in a domain that is not yet supported cannot be dispatched."""
    q = queries.create(engine, "Fatigue life falls with porosity", ("mpea",), domain="fatigue")
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    with pytest.raises(IntegrityError, match="dispatch blocked: the confirmed domain is not supported yet"):
        queries.dispatch(engine, q.version_id)
    assert one(engine, "SELECT count(*) FROM run") == 0
    assert one(engine, "SELECT status FROM hypothesis_version WHERE id = :v", v=q.version_id) == "submitted"


@pytest.mark.parametrize("sources, code", [(("nosuch",), "unknown_source"), ((), "no_source")])
def test_a_query_names_registered_sources(engine, sources, code):
    with pytest.raises(queries.QueryRefused) as refused:
        queries.create(engine, CLAIM, sources)
    assert refused.value.code == code


def test_dispatch_needs_a_confirmed_domain(engine):
    q = queries.create(engine, CLAIM, ("mpea",))
    queries.submit(engine, q.version_id)
    with pytest.raises(IntegrityError, match="dispatch_needs_confirmed_domain"):
        queries.dispatch(engine, q.version_id)


def partly(engine, sufficiency="use_available"):
    _, rid = dispatched(engine, sufficiency=sufficiency)
    queries.start(engine, rid)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO stage_result (run_id, stage) VALUES (:r, 'narrowing')"), dict(r=rid))
        conn.execute(text("UPDATE stage_result SET status = 'done', finished_at = now(), "
                          "output = '{\"result\": \"partly_sufficient\"}' WHERE run_id = :r"), dict(r=rid))
        conn.execute(text("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
                          "evidence_level = 1 WHERE id = :r"), dict(r=rid))
    return rid


NARROWER = {"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [{"band": "room temperature"}]}


def test_the_narrower_question_is_a_separate_linked_submitted_query(engine):
    original = partly(engine)
    q = queries.create_narrower(engine, original, NARROWER)
    assert rows(engine, "SELECT narrower_of_run_id FROM hypothesis WHERE id = :h", h=q.hypothesis_id) == [(original,)]
    version = rows(engine, "SELECT hv.status, hv.text, d.key, hv.sufficiency_option FROM hypothesis_version hv "
                           "JOIN domain d ON d.id = hv.domain_id WHERE hv.id = :v", v=q.version_id)[0]
    assert version == ("submitted", f"{CLAIM} (narrower question: phase class FCC; test type tension; room temperature)",
                       "grain_size_strengthening", "use_available")
    assert sorted(r[0] for r in rows(engine, "SELECT s.key FROM hypothesis_version_source hvs JOIN source s "
                                             "ON s.id = hvs.source_id WHERE hypothesis_version_id = :v",
                                     v=q.version_id)) == ["mpea", "tamu_fcc"]
    original_number = one(engine, "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = "
                                  "r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
                                  "WHERE r.id = :r", r=original)
    assert q.number != original_number
    # Dispatched by its number (`hypocurate dispatch Q-...`), after a named person confirms the domain.
    vid = queries.submitted_version(engine, q.number)
    assert vid == q.version_id
    queries.confirm_domain(engine, vid, by="Ada Reviewer")
    rid = queries.dispatch(engine, vid, fixed_plan=True)
    assert one(engine, "SELECT fixed_plan FROM run WHERE id = :r", r=rid) is True


def test_a_narrower_question_needs_a_partly_sufficient_original(engine):
    _, rid = dispatched(engine)
    with pytest.raises(IntegrityError, match="partly_sufficient"):
        queries.create_narrower(engine, rid, NARROWER)


def test_only_a_submitted_version_is_dispatched_by_number(engine):
    q = queries.create(engine, CLAIM, ("mpea",))
    with pytest.raises(queries.QueryRefused) as refused:
        queries.submitted_version(engine, q.number)
    assert refused.value.code == "not_submitted"


@pytest.mark.parametrize("scope, words", [
    ({"phase_class": ["FCC", "BCC"]}, "phase class FCC, BCC"),
    ({"temperature_band": [{"band": "cryogenic", "min": -200.0, "max": -150.0}]}, "cryogenic (-200 to -150 °C)"),
])
def test_the_narrower_scope_in_words_is_built_from_vocabulary_values(scope, words):
    assert queries.scope_in_words(scope) == words
