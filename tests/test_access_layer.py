"""Step 5: the access layer (PRD 4; criterion 14.2).

Every role at every stage gets exactly the fields on its list; every other request raises
AccessDenied and leaves a denied row in the audit log that survives the rejection; what a
role may see changes at the rules lock and at the dataset freeze, tested on both sides;
every access call follows the locking protocol and runs in `run_transaction`.
"""
from __future__ import annotations

import ast
import json
import threading
import time
from pathlib import Path

import pytest
from sqlalchemy import text
import access_world as aw
from access_testing import access_for
from hypocurate.access import Access, AccessDenied, AccessFailed, allowlist, bind, layer, role_input
from hypocurate.access import vocabulary
from hypocurate.access.allowlist import ALLOWED, FIELDS, ROLES, SOURCE_META_FIELDS, STAGES, allowed
from hypocurate.access.fields import READERS
from hypocurate.db.engine import make_engine
from hypocurate.pipeline.profile import TAG_STARTING_LISTS
from hypocurate.sources.record import HARMONIZED_FIELDS

REPO = Path(__file__).resolve().parent.parent

# World stage -> the access stage it is at.
WORLD_STAGES = {"queued": "none", "failed": "none", "before_lock": "before_lock", "curation": "curation",
                "analysis": "analysis", "closed_without_freeze": "closed_without_freeze", "final": "final",
                "final_without_freeze": "final_without_freeze", "narrowed": "narrowed"}


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    e.test_url = migrated_database
    yield e
    e.dispose()


def access(engine, world, role, stage, **kw):
    return access_for(engine, world.run, role, stage, **kw)


def audit(engine, run=None):
    with engine.connect() as conn:
        return conn.execute(text("SELECT role, stage, function, allowed, detail FROM audit_log "
                                 + ("WHERE run_id = :r " if run else "") + "ORDER BY id"), dict(r=run)).all()


# --- The allow-list itself --------------------------------------------------------------

def test_the_allow_list_matches_the_owners_table():
    """The table approved by the owner on 2026-10-05 (step 5 plan), field for field."""
    # Sprint 2 pilot (owner, 2026-10-22, an approved safeguard change): the Extractor and the Reconciler.
    assert ROLES == ("planner", "curator", "critic", "analyst", "commentator", "extractor", "reconciler")
    assert set(ALLOWED) == set(ROLES)
    # Step 8b (owner, 2026-10-07): the Analyst also at 'narrowed' (A4); the Commentator reads nothing (A6).
    assert {r: set(s) for r, s in ALLOWED.items()} == {
        "planner": {"before_lock"}, "curator": {"registration"}, "critic": {"curation"},
        "analyst": {"analysis", "closed_without_freeze", "narrowed"}, "commentator": set(),
        "extractor": {"document"}, "reconciler": set()}
    assert allowed("planner", "before_lock") == {"claim", "domain", "sources_meta", "tag_values", "record_counts"}
    # Owner, 2026-10-06 (step 8a, Q2): the Curator reads a source version's documentation at
    # registration, never in a run.
    assert allowed("curator", "registration") == {"source_documentation", "curation_targets"}
    assert all(allowed("curator", stage) == frozenset() for stage in STAGES if stage != "registration")
    assert all(allowed(role, "registration") == frozenset() for role in ROLES if role != "curator")
    assert allowed("critic", "curation") == {"sources_meta", "record_metadata", "flags_kind"}
    # Step 8b (owner, Q6): the Analyst receives stored facts only, the same five fields at each stage.
    analyst = {"claim", "domain", "sources_meta", "coverage", "analyst_facts"}
    for stage in ("analysis", "closed_without_freeze", "narrowed"):
        assert allowed("analyst", stage) == analyst, stage
    # Owner, 2026-10-07 (A6): the Commentator reads nothing at any stage until step 12.
    assert all(allowed("commentator", stage) == frozenset() for stage in STAGES)
    assert all(allowed(role, "narrowed") == frozenset() for role in ROLES if role != "analyst")
    for stage in STAGES:
        if stage != "before_lock":
            assert allowed("planner", stage) == frozenset()
    assert all(allowed(role, "none") == frozenset() for role in ROLES)
    # Sprint 2 pilot: the Extractor reads one parsed document, its specification's reading sections and its own
    # draft, at 'document' only; no other role reads anything there; the Reconciler reads nothing until R5.
    assert allowed("extractor", "document") == {"parsed_document", "extraction_spec", "extraction_draft"}
    assert all(allowed("extractor", stage) == frozenset() for stage in STAGES if stage != "document")
    assert all(allowed(role, "document") == frozenset() for role in ROLES if role != "extractor")
    assert all(allowed("reconciler", stage) == frozenset() for stage in STAGES)


def test_every_listed_field_has_a_reader_and_a_description():
    listed = set().union(*(fs for stages in ALLOWED.values() for fs in stages.values()))
    assert listed <= set(READERS) == set(FIELDS)


def test_no_outcome_reaching_field_is_listed_for_the_planner_the_critic_or_the_gap_report():
    outcome_bearing = {"records_full", "flags_full", "results", "stage_outputs", "source_documentation", "plan"}
    for role, stage in (("planner", "before_lock"), ("critic", "curation")):
        assert not allowed(role, stage) & outcome_bearing, role
    # Step 8b: the Analyst gets none of these at any stage (its facts are named keys of stored results).
    for stage in ("analysis", "closed_without_freeze", "narrowed"):
        assert not allowed("analyst", stage) & outcome_bearing, stage
    assert all(not allowed("commentator", stage) for stage in STAGES)  # A6


# --- Every role, every stage, every field ------------------------------------------------

@pytest.mark.parametrize("world_stage", list(WORLD_STAGES))
def test_each_role_gets_exactly_its_fields_and_every_refusal_is_logged(engine, world_stage):
    world = aw.build(engine, world_stage)
    stage = WORLD_STAGES[world_stage]
    for role in ROLES:
        for field in sorted(FIELDS):
            before = len(audit(engine, world.run))
            a = access(engine, world, role, stage)
            if field in allowed(role, stage):
                a.get(field)
                rows = audit(engine, world.run)[before:]
                assert [(r.role, r.stage, r.function, r.allowed) for r in rows] == [(role, stage, field, True)]
                assert rows[0].detail == {"result": "allowed", "actual_stage": stage,
                                          **({"source": "mpea"} if role == "curator" else {})}
            else:
                with pytest.raises(AccessDenied):
                    a.get(field)
                rows = audit(engine, world.run)[before:]
                assert [(r.role, r.stage, r.function, r.allowed) for r in rows] == [(role, stage, field, False)]
                assert rows[0].detail["actual_stage"] == stage
                assert rows[0].detail["result"] == "denied" and rows[0].detail["code"] == "not_on_list"


@pytest.mark.parametrize("world_stage", ["queued", "failed"])
def test_queued_and_failed_runs_give_nothing_to_anyone(engine, world_stage):
    world = aw.build(engine, world_stage)
    for role in ROLES:
        for stage in STAGES:
            with pytest.raises(AccessDenied):
                access(engine, world, role, stage).get("claim")


def test_role_input_reads_every_listed_field_once_through_the_access_object(engine):
    world = aw.build(engine, "curation")
    before = len(audit(engine, world.run))
    got = role_input(access(engine, world, "critic", "curation"))
    assert set(got) == allowed("critic", "curation")
    rows = audit(engine, world.run)[before:]
    assert sorted(r.function for r in rows) == sorted(allowed("critic", "curation"))
    assert all(r.allowed for r in rows)


# --- The refusal is logged and survives ----------------------------------------------------

def test_a_denied_row_survives_the_rejection_and_the_callers_rollback(engine):
    """The row is committed in the access layer's own transaction before AccessDenied is
    raised, so neither the exception nor a caller's rollback removes it."""
    world = aw.build(engine, "before_lock")
    with engine.connect() as caller:
        tx = caller.begin()
        caller.execute(text("SELECT 1"))
        with pytest.raises(AccessDenied) as denied:
            access(engine, world, "planner", "before_lock").get("records_full")
        tx.rollback()
    assert denied.value.field == "records_full" and denied.value.role == "planner"
    with make_engine(engine.test_url).connect() as fresh:
        rows = fresh.execute(text("SELECT role, function, allowed FROM audit_log WHERE run_id = :r"),
                             dict(r=world.run)).all()
    assert ("planner", "records_full", False) in [tuple(r) for r in rows]


@pytest.mark.parametrize("world_stage,role", [("before_lock", "planner"), ("curation", "critic")])
def test_the_planner_and_the_critic_asking_for_outcomes_are_denied_and_logged(engine, world_stage, role):
    """Criterion 14.2, first point."""
    world = aw.build(engine, world_stage)
    for field in ("records_full", "flags_full", "results", "stage_outputs", "source_documentation"):
        with pytest.raises(AccessDenied):
            access(engine, world, role, world_stage).get(field)
    denied = [r for r in audit(engine, world.run) if r.role == role and not r.allowed]
    assert {r.function for r in denied} == {"records_full", "flags_full", "results", "stage_outputs",
                                            "source_documentation"}
    assert not [r for r in audit(engine, world.run) if r.role == role and r.allowed]


def test_audit_rows_never_hold_a_value(engine):
    world = aw.build(engine, "curation")
    role_input(access(engine, world, "critic", "curation"))
    for field in ("records_full", "flags_full"):
        with pytest.raises(AccessDenied):
            access(engine, world, "critic", "curation").get(field)
    text_of_rows = json.dumps([list(r) for r in audit(engine, world.run)], default=str)
    for value in aw.PLANTED.values():
        assert repr(value) not in text_of_rows and str(int(value)) not in text_of_rows


def test_unknown_roles_stages_and_fields_are_denied_and_logged(engine):
    world = aw.build(engine, "before_lock")
    for role, stage, field in (("judge", "before_lock", "claim"), ("planner", "anytime", "claim"),
                               ("planner", "before_lock", "everything")):
        with pytest.raises(AccessDenied):
            access_for(engine, world.run, role, stage).get(field)
    rows = [(r.role, r.stage, r.function, r.allowed, r.detail["code"]) for r in audit(engine, world.run)]
    # Only validated strings are logged: anything not ours is "invalid" (with its length).
    assert rows == [("invalid", "before_lock", "claim", False, "unknown_role"),
                    ("planner", "invalid", "claim", False, "unknown_stage"),
                    ("planner", "before_lock", "invalid", False, "not_on_list")]


# --- Stages are read from the database; both sides of each checkpoint ------------------------

def test_a_declared_stage_is_checked_against_the_database(engine):
    world = aw.build(engine, "before_lock")
    with pytest.raises(AccessDenied) as denied:
        access(engine, world, "critic", "curation").get("sources_meta")
    assert denied.value.code == "stage_mismatch"


def test_the_rules_lock_changes_what_each_role_may_see(engine):
    world = aw.build(engine, "before_lock")
    planner = access(engine, world, "planner", "before_lock")
    critic = access(engine, world, "critic", "curation")
    curator = access(engine, world, "curator", "curation")
    assert planner.get("claim")["text"] == aw.DIRECTION
    with pytest.raises(AccessDenied):
        critic.get("record_metadata")
    aw.lock(world.w, world.run)
    with pytest.raises(AccessDenied, match="no longer at the stage"):
        planner.get("claim")
    assert critic.get("record_metadata") == []
    # Step 8a: the Curator has nothing at the curation stage (it reads at registration).
    with pytest.raises(AccessDenied, match="not on the role's list"):
        curator.get("sources_meta")


def test_the_dataset_freeze_changes_what_each_role_may_see(engine):
    world = aw.build(engine, "curation")
    w = world.w
    critic = access(engine, world, "critic", "curation")
    analyst = access(engine, world, "analyst", "analysis")
    assert critic.get("flags_kind")
    with pytest.raises(AccessDenied):
        analyst.get("analyst_facts")
    primary = w.analysis_set(world.run)
    for rec in world.records:
        w.decide(world.run, rec)
        w.add(primary, rec)
    w.freeze(world.run, len(world.records))
    aw.stored_facts(w, world.run, frozen=True)  # step 8b: the Analyst reads code's stored facts
    with pytest.raises(AccessDenied, match="no longer at the stage"):
        critic.get("flags_kind")
    assert analyst.get("analyst_facts")["names"]["pooled_estimate"] == "424.9 MPa·µm^0.5"  # step 8b: a named display string


def test_ending_without_a_freeze_opens_only_the_gap_report_input(engine):
    world = aw.build(engine, "curation")
    gap = access(engine, world, "analyst", "closed_without_freeze")
    with pytest.raises(AccessDenied):
        gap.get("analyst_facts")
    for rec in world.records:
        world.w.decide(world.run, rec)
    aw.sql(world.w, "INSERT INTO calibration_result (run_id, status, reason) "
                    "VALUES (:r, 'unavailable', 'no_dataset_frozen')", r=world.run)
    aw.stored_facts(world.w, world.run, frozen=False)  # step 8b: the Analyst reads code's stored facts
    assert gap.get("analyst_facts")["kind"] == "no_dataset_frozen"
    # Step 8b (Q6): the step-5 gap-report fields are no longer on the Analyst's list.
    for field in ("records_full", "flags_full", "results", "stage_outputs", "condition_summaries", "plan",
                  "decisions", "flags_kind", "stored_record_counts"):
        with pytest.raises(AccessDenied):
            gap.get(field)
    with pytest.raises(AccessDenied):
        access(engine, world, "critic", "curation").get("flags_kind")


def test_completion_without_a_freeze_closes_the_analyst_and_gives_the_commentator_nothing(engine):
    """Step 8b (A6; was ..._moves_access_to_the_commentator_only): completion still closes the Analyst's
    access; the Commentator reads nothing until step 12, before or after completion."""
    world = aw.build(engine, "closed_without_freeze")
    gap = access(engine, world, "analyst", "closed_without_freeze")
    commentator = access(engine, world, "commentator", "final_without_freeze")
    with pytest.raises(AccessDenied):
        commentator.get("outcome")
    assert gap.get("claim")
    world.w.complete(world.run, "insufficient")
    with pytest.raises(AccessDenied, match="no longer at the stage"):
        gap.get("claim")
    with pytest.raises(AccessDenied) as denied:
        commentator.get("outcome")
    assert denied.value.code == "not_on_list"
    with pytest.raises(AccessDenied, match="no longer at the stage"):
        access(engine, world, "commentator", "final").get("results")


def test_completion_after_a_freeze_closes_the_analyst_and_gives_the_commentator_nothing(engine):
    """Step 8b (A6; was ..._moves_access_to_the_commentator_only)."""
    world = aw.build(engine, "analysis")
    analyst = access(engine, world, "analyst", "analysis")
    commentator = access(engine, world, "commentator", "final")
    with pytest.raises(AccessDenied):
        commentator.get("results")
    assert analyst.get("analyst_facts")
    # Step 8b (0006; owner, A5): a run with a plan never completes as partly sufficient.
    world.w.complete(world.run, "insufficient", level=4)
    with pytest.raises(AccessDenied, match="no longer at the stage"):
        analyst.get("analyst_facts")
    with pytest.raises(AccessDenied) as denied:
        commentator.get("results")
    assert denied.value.code == "not_on_list"


@pytest.mark.parametrize("world_stage", ["final", "final_without_freeze", "analysis", "narrowed"])
def test_a_commentator_binding_reads_nothing_at_any_stage(engine, world_stage):
    """Owner, 2026-10-07 (A6; replaces test_the_commentator_without_a_freeze_gets_the_gap_report_input_the_
    report_and_the_outcome): until step 12 the Commentator reads nothing, every field refused and logged,
    and its complete input is refused (never empty)."""
    world = aw.build(engine, world_stage)
    stage = {"final": "final", "final_without_freeze": "final_without_freeze", "analysis": "analysis",
             "narrowed": "narrowed"}[world_stage]
    commentator = access(engine, world, "commentator", stage)
    before = len(audit(engine, world.run))
    for field in sorted(FIELDS):
        with pytest.raises(AccessDenied) as denied:
            commentator.get(field)
        assert denied.value.code == "not_on_list"
    rows = audit(engine, world.run)[before:]
    assert len(rows) == len(FIELDS) and not any(r.allowed for r in rows)
    with pytest.raises(AccessDenied) as denied:
        role_input(commentator)
    assert denied.value.code == "empty_list"


def test_experiment_flags_relax_nothing(engine):
    """PRD 4's relaxation flag is not built in sprint 1: flags on the run change no list."""
    world = aw.build(engine, "queued")
    w = world.w
    vid = w.val("SELECT hypothesis_version_id FROM run WHERE id = :r", r=world.run)
    flagged = aw.val(w, "INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags) "
                              "VALUES (:v, true, :j_f) RETURNING id",  # a narrower question's run (0006)
                     v=vid, j_f={"relax_access": True, "access": "all", "unlock": ["planner", "critic"]})
    w.run_sql("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
              "VALUES (:r, :s, :sv, 'pending')", r=flagged, s=w.source["mpea"], sv=w.version["mpea"])
    w.run_sql("INSERT INTO run_source (run_id, source_id, search_status) VALUES (:r, :s, 'not_selected')",
              r=flagged, s=w.source["tamu_fcc"])
    w.start(flagged)
    assert w.val("SELECT experiment_flags->>'access' FROM run WHERE id = :r", r=flagged) == "all"
    for field in sorted(set(FIELDS) - allowed("planner", "before_lock")):
        with pytest.raises(AccessDenied):
            access_for(engine, flagged, "planner", "before_lock").get(field)


# --- What each field contains -----------------------------------------------------------

def test_sources_meta_is_exactly_the_named_plain_fields(engine):
    world = aw.build(engine, "curation")
    got = access(engine, world, "critic", "curation").get("sources_meta")
    assert SOURCE_META_FIELDS == ("key", "name", "source_type", "data_kind", "licence", "grouping_unit",
                                  "fields_available")
    assert [list(s) for s in got] == [list(SOURCE_META_FIELDS)] * 2
    assert [s["key"] for s in got] == ["mpea", "tamu_fcc"]  # the chosen sources only


def test_sources_meta_comes_from_the_code_and_the_sealed_version_not_the_registry(engine):
    """Review finding 4: editing the source registry after dispatch changes nothing for the run
    (the world has already changed the licence and properties; here also the name and the
    interpretation settings)."""
    from hypocurate.sources.versions import SOURCES
    world = aw.build(engine, "curation")
    aw.sql(world.w, "UPDATE source SET name = 'renamed', grouping_unit = 'dataset', data_kind = 'computed' "
                    "WHERE key = 'mpea'")
    mpea = access(engine, world, "critic", "curation").get("sources_meta")[0]
    d = SOURCES["mpea"]
    assert mpea == {"key": "mpea", "name": d.name, "source_type": "uploaded_table", "data_kind": "measured",
                    "licence": d.licence, "grouping_unit": "paper", "fields_available": list(d.properties_covered)}


@pytest.mark.parametrize("world_stage", ["before_lock", "curation", "analysis"])
def test_the_curator_has_nothing_in_any_run(engine, world_stage):
    """Step 8a (owner, 2026-10-06, Q2), replacing the run-stage Curator test of step 5: the Curator
    reads a source version at registration (tests/test_access_curator.py), never a run's data."""
    world = aw.build(engine, world_stage)
    a = access(engine, world, "curator", WORLD_STAGES[world_stage])
    with pytest.raises(AccessDenied, match="no field at this stage"):
        role_input(a)
    for field in ("sources_meta", "record_metadata", "claim", "source_documentation"):
        with pytest.raises(AccessDenied):
            a.get(field)


def test_inclusion_is_not_the_curators(engine):
    """The Curator's list has no eligibility, set or flag field (criterion 14.2, fourth point);
    eligibility is code's (step 6)."""
    assert not allowed("curator", "registration") & {"decisions", "flags_kind", "flags_full", "record_metadata",
                                                      "records_full", "claim", "plan"}


def test_record_metadata_carries_no_number_but_identity_and_composition(engine):
    world = aw.build(engine, "curation")
    got = access(engine, world, "critic", "curation").get("record_metadata")
    assert len(got) == len(world.records)
    for r in got:
        assert set(r) == {"id", "source", "item_index", "kind", "alloy", "composition", "paper_doi", "status",
                          "categories"}  # no origin key, no paper title (review finding 3)
        assert set(r["status"]) == set(HARMONIZED_FIELDS)
        assert set(r["status"].values()) <= {"converted", "not_reported", "not_convertible", "assigned_from_source",
                                             "assigned_by_decision", None}
        for f, v in r["categories"].items():
            assert v is None or v == "unrecognized" or vocabulary.category(f, v) == v, (f, v)
    planted = [r for r in got if r["status"]["yield_strength"] == "not_convertible"]
    assert len(planted) == 1  # the unreadable cell: its reason (which quotes it) is withheld
    marked = [r for r in got if r["categories"]["microstructure"] == "unrecognized"]
    assert len(marked) == 1 and marked[0]["categories"]["processing_method"] == "unrecognized"
    assert marked[0]["categories"]["phase_class"] == "unrecognized" and marked[0]["paper_doi"] == "unrecognized"


def test_flags_kind_has_no_numbers(engine):
    world = aw.build(engine, "curation")
    got = access(engine, world, "critic", "curation").get("flags_kind")
    assert got == [{"id": world.flags[0], "kind": "values_disagree", "category": "differ beyond tolerance",
                    "records": got[0]["records"]},
                   {"id": world.flags[1], "kind": "unrecognized", "category": "unrecognized", "records": []}]
    assert len(got[0]["records"]) == 2


def test_the_plan_is_projected_by_its_named_parts(engine):
    """Step 8b: read as Inclusion (code), since no agent's list holds the plan any more (Q6, A6)."""
    world = aw.build(engine, "curation")
    got = access(engine, world, "inclusion", "curation").get("plan")
    u = "unrecognized"
    assert got["content"] == {
        "variables": {"outcome": {"field": "yield_strength"},
                      "predictor": {"field": "grain_size", "unit": "µm", "transformation": u}},
        "model": {"name": "hall_petch_alloy_intercepts", "null": "k <= 0", "alternative": u, "alpha": 0.05},
        "scope": {"phase_class": ["FCC", u], "alloy_class": [u]},
        "fields_to_extract": ["grain_size", "yield_strength", "composition"],
        "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1}, {"rule": u, "values": ["tension", u]}],
        "eligibility_rules": [{"flag_kind": "values_disagree", "rule": u}],
        "verdict_statement": u,
        "sensitivity_analyses": ["tension_and_compression", u]}
    assert got["minimums"] == {"records": 4, "alloys": 1, "groups": 2, "resid_df": 1}
    assert got["power_assumptions"] == {"method": "information_only", "scatter": 60.0}


def test_tag_values_are_the_approved_lists_only(engine):
    """The approved values only: since step 6, the 19 starting values seeded by migration 0002
    (the world's own approved value is one of them). The planted proposed value never appears."""
    world = aw.build(engine, "before_lock")
    got = access(engine, world, "planner", "before_lock").get("tag_values")
    seeded = sorted(({"kind": k, "value": v} for k, values in TAG_STARTING_LISTS.items() for v in values),
                    key=lambda t: (t["kind"], t["value"]))
    assert got == seeded
    assert {"kind": "property", "value": "yield strength"} in got
    assert str(aw.PLANTED["yield_strength"]) not in json.dumps(got)


def test_record_counts_are_counts_from_the_sealed_source(engine):
    world = aw.build(engine, "before_lock")
    got = access(engine, world, "planner", "before_lock").get("record_counts")
    assert [c["source"] for c in got] == ["mpea", "tamu_fcc"] and got[0]["readable"]
    assert got[1] == {"source": "tamu_fcc", "readable": False}  # the world's placeholder file
    c = got[0]
    assert c["n_records"] == 8  # four real rows and four planted ones
    assert c["by_status"]["yield_strength"] == {"converted": 7, "not_convertible": 1}
    assert c["by_category"]["test_type"]["tension"] >= 3
    assert set(c["by_category"]) == set(allowlist.CATEGORY_FIELDS)
    assert c["unrecognized"] == {"microstructure": 1, "phase_class": 1, "processing_method": 1}
    assert c["by_category"]["microstructure"]["unrecognized"] == 1
    assert not set(c["by_category"]) & allowlist.OUTCOME_FIELDS


def test_condition_summaries_are_ranges_and_counts_of_conditions_only(engine):
    """Step 8b: no role's list holds this field until step 12 (Q6, A6); its reader is tested directly."""
    from hypocurate.access.context import AccessContext
    from hypocurate.access.fields import condition_summaries
    world = aw.build(engine, "closed_without_freeze")
    with engine.connect() as conn:
        got = condition_summaries(conn, AccessContext(world.run, "analyst", "closed_without_freeze"))
    assert set(got) == {"overall", "per_alloy"}
    overall = got["overall"]
    assert set(overall) == {"n_records", "grain_size", "test_temperature", "test_type", "phase_class"}
    assert overall["n_records"] == 8
    assert overall["grain_size"]["n"] == 8
    assert overall["grain_size"]["min"] <= 12.5 and overall["grain_size"]["max"] >= 14.5
    assert overall["test_temperature"]["min"] <= 25.0 <= overall["test_temperature"]["max"]
    assert sum(overall["test_type"].values()) <= 8
    assert sum(g["n_records"] for g in got["per_alloy"]) == 8
    for g in got["per_alloy"]:
        assert set(g) == {"alloy", "n_records", "grain_size", "test_temperature", "test_type", "phase_class"}


# --- The write protocol: hc_write_lock first, inside run_transaction ----------------------

def test_an_access_call_takes_the_run_lock_first_and_times_out_instead_of_hanging(engine):
    world = aw.build(engine, "curation")
    before = len(audit(engine, world.run))
    holder = make_engine(engine.test_url)
    with holder.connect() as conn:
        tx = conn.begin()
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=world.run))
        with pytest.raises(AccessFailed) as failed:
            access_for(engine, world.run, "critic", "curation", lock_timeout_ms=300).get("flags_kind")
        # The failure row is written while the lock is still held (named exception: no run lock).
        rows = audit(engine, world.run)[before:]
        tx.rollback()
    holder.dispose()
    assert failed.value.code == "lock_timeout"
    assert [(r.function, r.allowed, r.detail["result"], r.detail["code"]) for r in rows] == [
        ("flags_kind", False, "failed", "lock_timeout")]
    assert access_for(engine, world.run, "critic", "curation").get("flags_kind")
    assert layer.ACCESS_LOCK_TIMEOUT_MS == 5000


def test_an_access_call_waits_for_a_writer_holding_the_run_lock(engine):
    world = aw.build(engine, "curation")
    holder = make_engine(engine.test_url)
    result = {}
    with holder.connect() as conn:
        tx = conn.begin()
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=world.run))
        reader = threading.Thread(target=lambda: result.update(
            got=access_for(engine, world.run, "critic", "curation").get("flags_kind")))
        reader.start()
        waiting = False
        for _ in range(100):
            with engine.connect() as probe:
                waiting = probe.execute(text(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
                    "AND wait_event_type = 'Lock' AND query LIKE '%hc_write_lock%'")).scalar() > 0
            if waiting:
                break
            time.sleep(0.05)
        assert waiting and "got" not in result
        tx.commit()
        reader.join(10)
    holder.dispose()
    assert result["got"][0]["kind"] == "values_disagree"


def test_every_access_call_runs_in_run_transaction(engine, monkeypatch):
    world = aw.build(engine, "curation")
    calls = []
    real = layer.run_transaction

    def spy(e, fn, *args, **kwargs):
        calls.append(e)
        return real(e, fn, *args, **kwargs)

    monkeypatch.setattr(layer, "run_transaction", spy)
    a = access_for(engine, world.run, "critic", "curation")
    a.get("flags_kind")
    with pytest.raises(AccessDenied):
        a.get("records_full")
    assert calls == [engine, engine]


def test_the_access_transaction_calls_hc_write_lock_before_anything_else():
    src = Path(layer.__file__).read_text()
    body = src[src.index("def _transaction"):src.index("def _policy")]
    statements = [line.strip() for line in body.splitlines() if "conn.execute" in line or "actual_stage(" in line]
    assert "SET LOCAL lock_timeout" in statements[0]
    assert "FROM run WHERE id = :r" in statements[1]  # does the run exist (else a failure row)
    assert "hc_write_lock(p_run => :r)" in statements[2]
    assert "actual_stage(" in statements[3]


# --- Static checks: one way in -------------------------------------------------------------

def _calls(tree: ast.AST) -> list[str]:
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            out.append(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
    return out


def _imports(tree: ast.AST) -> set[str]:
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


def test_the_access_layer_has_no_function_that_takes_a_path():
    for name in ("allowlist", "context", "dispatch", "errors", "fields", "inputs", "layer", "stage", "vocabulary"):
        tree = ast.parse((REPO / "hypocurate" / "access" / f"{name}.py").read_text())
        assert not {"open", "read_bytes", "read_text", "Path", "listdir", "scandir"} & set(_calls(tree)), name
        assert not {"pathlib", "io", "glob", "shutil"} & _imports(tree), name
    assert list(Access.__init__.__code__.co_varnames[:5]) == ["self", "engine", "context", "lock_timeout_ms",
                                                              "_trusted"]


def test_the_guard_is_installed_in_one_place():
    installs, hooks = [], []
    for path in sorted((REPO / "hypocurate").rglob("*.py")):
        calls = _calls(ast.parse(path.read_text()))
        if "install" in calls:
            installs.append(path.relative_to(REPO).as_posix())
        if "addaudithook" in calls:
            hooks.append(path.relative_to(REPO).as_posix())
    assert installs == ["hypocurate/access/guarded.py"]
    assert hooks == ["hypocurate/access/file_guard.py"]


def test_condition_summaries_group_alloys_by_the_same_alloy_rule():
    """Register entry 'same_alloy_rule' (owner, 2026-10-05): rounded compositions identical."""
    from hypocurate.sources.normalize import SAME_ALLOY_DECIMALS, same_alloy_key
    assert SAME_ALLOY_DECIMALS == 1
    assert same_alloy_key({"Fe": 50.01, "Ni": 49.99}) == same_alloy_key({"Ni": 49.96, "Fe": 50.04}) == "Fe 50.0 Ni 50.0"
    assert same_alloy_key({"Fe": 50.06, "Ni": 49.94}) == "Fe 50.1 Ni 49.9"
