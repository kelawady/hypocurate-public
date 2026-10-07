"""Step 8a: migration 0005 (approved by the owner on 2026-10-06, subject to the second-model review).

Additive; 0001 to 0004 untouched; the two replaced model-call functions keep every check of 0001;
up, down, up gives the same schema; the downgrade refuses while anything 0005 added is in use and
restores 0001's functions and path rule exactly; a failed upgrade changes nothing. Then the rules
0005 adds, each with an allowed and a refused case: source files by role, one invocation record per
agent call (run or registration), model calls owned by an invocation, the Curator's proposals and a
person's decisions."""
from __future__ import annotations

import re

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from model_builder import World, sha
from test_migrations import assert_schema_is_empty, snapshot
from test_migrations_step6 import body

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
M0001 = SCRIPTS.get_revision("0001").module
M0005 = SCRIPTS.get_revision("0005").module

DOC = ("Quasistatic tensile testing was used to determine 0.2% offset YS, while Vickers indentation\n"
       "tests provided the HV. The dataset contains 94 FCC alloy conditions in the system.\n").encode()
QUOTE = "Quasistatic tensile testing was used to determine 0.2% offset YS"


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


@pytest.fixture
def w(db):
    return World(db)


def function_source(engine, name) -> str:
    with engine.connect() as conn:
        return conn.execute(text("SELECT prosrc FROM pg_proc WHERE proname = :n"), dict(n=name)).scalar_one()


def checks_of(function_sql: str) -> list[str]:
    return re.findall(r"IF .*? END IF;", body(function_sql))


# --- the migration -------------------------------------------------------------------------------

def test_0005_is_the_head_and_follows_0004():
    assert migrate.head_revision() == "0005" and M0005.down_revision == "0004"


@pytest.mark.parametrize("name, kept", [("hc_model_call_insert", "MODEL_CALL_INSERT_0001"),
                                        ("hc_model_call_update", "MODEL_CALL_UPDATE_0001")])
def test_the_downgrade_keeps_0001s_model_call_functions_verbatim(name, kept):
    original = next(f for f in M0001.FUNCTIONS if f"CREATE FUNCTION {name}()" in f)
    assert body(getattr(M0005, kept)) == body(original)


@pytest.mark.parametrize("old, new", [("MODEL_CALL_INSERT_0001", "MODEL_CALL_INSERT_0005"),
                                      ("MODEL_CALL_UPDATE_0001", "MODEL_CALL_UPDATE_0005")])
def test_the_new_model_call_functions_keep_every_check_of_0001(old, new):
    new_body = body(getattr(M0005, new))
    for check in checks_of(getattr(M0005, old)):
        assert check in new_body, check


def test_up_down_up_restores_0001s_functions_and_path_rule(engine):
    migrate.upgrade(engine)
    first = snapshot(engine)
    migrate.downgrade(engine, "0004")
    for name in ("hc_model_call_insert", "hc_model_call_update"):
        original = next(f for f in M0001.FUNCTIONS if f"CREATE FUNCTION {name}()" in f)
        assert " ".join(function_source(engine, name).split()) == body(original)
    with engine.connect() as conn:
        rule = conn.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                                 "WHERE conname = 'ck_source_file_safe_data_file_path'")).scalar_one()
        nullable = conn.execute(text("SELECT is_nullable FROM information_schema.columns "
                                     "WHERE table_name = 'model_call' AND column_name = 'run_id'")).scalar_one()
        tables = set(conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")).scalars())
    assert "csv|xlsx" in rule and "role" not in rule and nullable == "NO"
    assert not {"agent_invocation", "curator_proposal", "curator_decision"} & tables
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0004")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE curator_decision (id int)"))  # 0005 creates it last
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before
    assert migrate.current_revision(engine) == "0004"


def test_the_downgrade_refuses_while_0005_is_in_use(db):
    w = World(db)
    v = w.new_version("mpea", "v2")
    w.add_file(v, "documentation/paper.tex", DOC, role="documentation")
    before = snapshot(db)
    with pytest.raises(Exception, match="0005 is in use"):
        migrate.downgrade(db, "0004")
    assert snapshot(db) == before and migrate.current_revision(db) == "0005"


# --- source files by role ------------------------------------------------------------------------

def test_a_file_without_a_role_is_a_data_file_as_before(w):
    """The previous release's code inserts files without a role."""
    v = w.new_version("mpea", "v2")
    w.add_file(v, "table.csv", b"a,b\n")
    assert w.val("SELECT role FROM source_file WHERE source_version_id = :v", v=v) == "data"


@pytest.mark.parametrize("path, role, ok", [
    ("documentation/main.tex", "documentation", True),
    ("documentation/paper.xml", "documentation", True),
    ("documentation/notes.md", "documentation", True),
    ("curation.json", "curation", True),
    ("table.xlsx", "data", True),
    ("documentation/main.tex", "data", False),        # a data file is a table
    ("documentation/table.csv", "data", False),       # the documentation folder holds documentation only
    ("main.tex", "documentation", False),             # documentation lives in its folder
    ("documentation/sub/main.tex", "documentation", False),
    ("documentation/main.pdf", "documentation", False),
    ("documentation/.hidden.tex", "documentation", False),
    ("other.json", "curation", False),
    ("curation.json", "data", False),
    ("table.csv", "curation", False),
    ("table.csv", "unknown", False),
])
def test_each_role_has_its_own_path_rule(w, path, role, ok):
    v = w.new_version("mpea", "v2")
    sql = ("INSERT INTO source_file (source_version_id, path, sha256, content, role) VALUES (:v, :p, :h, :c, :o)")
    params = dict(v=v, p=path, h=sha(b"x"), c=b"x", o=role)
    if ok:
        w.run_sql(sql, **params)
    else:
        w.rejected(sql, "ck_source_file_safe_data_file_path", **params)


def test_a_version_with_documentation_seals_over_all_its_files(w):
    v = w.new_version("mpea", "v2")
    w.add_file(v, "table.csv", b"a,b\n")
    w.add_file(v, "documentation/main.tex", DOC, role="documentation")
    w.seal(v)
    assert w.val("SELECT count(*) FROM source_file WHERE source_version_id = :v", v=v) == 2
    assert w.val("SELECT fingerprint FROM source_version WHERE id = :v", v=v) == w.fingerprint(v)


# --- invocations ---------------------------------------------------------------------------------

def run_invocation(w, rid, stage, role="planner", setting=None):
    setting = setting or w.val("SELECT agent_setting_id FROM run_agent_setting WHERE run_id = :r AND role = :o",
                               r=rid, o=role)
    return ("INSERT INTO agent_invocation (scope, run_id, stage_result_id, role, agent_setting_id) "
            "VALUES ('run', :r, :s, :o, :a) RETURNING id", dict(r=rid, s=stage, o=role, a=setting))


def test_a_run_invocation_uses_the_setting_recorded_for_that_run(w):
    """Two valid runs whose recorded settings differ: an invocation of run A with run B's setting is
    refused, so a wrong but valid combination cannot be assembled."""
    a = w.running(agents=True)
    b_setting = w.val("INSERT INTO agent_setting (role, version, instruction, model) VALUES ('planner', 7, 'i', 'm') "
                      "RETURNING id")
    b = w.run()
    w.run_sql("INSERT INTO run_agent_setting VALUES (:r, 'planner', :s)", r=b, s=b_setting)
    w.start(b)
    sa = w.stage(a)
    sql, params = run_invocation(w, a, sa)
    assert w.val(sql, **params)
    sql, params = run_invocation(w, a, sa, setting=b_setting)
    w.rejected(sql, "fk_agent_invocation_run_agent_setting", **params)


def test_a_run_invocation_names_a_running_stage_of_its_run_with_its_role(w):
    a, b = w.running(agents=True), w.running(agents=True)
    sa, sb = w.stage(a), w.stage(b)
    critic = w.stage(a, "critic", "critic")
    for sql, params in (run_invocation(w, a, sb),):                       # another run's stage
        w.rejected(sql, "running stage of its run with the same role", **params)
    sql, params = run_invocation(w, a, critic)                            # the stage is the critic's
    w.rejected(sql, "running stage of its run with the same role", **params)
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now() WHERE id = :s", s=sa)
    sql, params = run_invocation(w, a, sa)                                # the stage is finished
    w.rejected(sql, "running stage of its run with the same role", **params)


def test_a_run_invocation_only_while_the_run_is_running(w):
    queued = w.run(agents=True)
    st = w.stage(w.running(agents=True))
    sql, params = run_invocation(w, queued, st)
    w.rejected(sql, "only while the run is running", **params)


def test_after_completion_only_the_commentator_is_invoked(w):
    rid, sets, _ = w.frozen(agents=True)
    w.result(rid, sets["primary"])
    w.complete(rid, "sufficient", "supported")
    commentator = w.stage(rid, "commentator", "commentator")
    sql, params = run_invocation(w, rid, commentator, role="commentator")
    assert w.val(sql, **params)
    sql, params = run_invocation(w, rid, commentator, role="analyst")
    w.rejected(sql, "after completion only the commentator", **params)


def curator_setting(w):
    return w.agent_setting("curator")


def sealed_version_with_documentation(w, key="tamu_fcc", label="docs"):
    v = w.new_version(key, label)
    w.add_file(v, "table.csv", f"a,b,{label}\n".encode())  # each label its own files, so its own fingerprint
    w.add_file(v, "documentation/main.tex", DOC, role="documentation")
    w.seal(v)
    return v


REGISTRATION = ("INSERT INTO agent_invocation (scope, source_version_id, role, agent_setting_id) "
                "VALUES ('registration', :v, :o, :a) RETURNING id")


def test_a_registration_invocation_is_the_curators_on_a_sealed_version(w):
    v = sealed_version_with_documentation(w)
    assert w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    unsealed = w.new_version("tamu_fcc", "open")
    w.rejected(REGISTRATION, "reads a sealed source version", v=unsealed, o="curator", a=curator_setting(w))
    w.rejected(REGISTRATION, "ck_agent_invocation_shape", v=v, o="planner", a=w.agent_setting("planner"))
    w.rejected(REGISTRATION, "fk_agent_invocation_agent_setting", v=v, o="curator", a=w.agent_setting("planner"))
    rid = w.running(agents=True)
    w.rejected("INSERT INTO agent_invocation (scope, run_id, source_version_id, role, agent_setting_id) "
               "VALUES ('registration', :r, :v, 'curator', :a)", "ck_agent_invocation_shape",
               r=rid, v=v, a=curator_setting(w))


def test_invocations_are_append_only(w):
    v = sealed_version_with_documentation(w)
    w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    w.rejected("UPDATE agent_invocation SET source_version_id = source_version_id", "append-only")
    w.rejected("DELETE FROM agent_invocation", "append-only")


# --- model calls owned by an invocation -------------------------------------------------------------

CALL = ("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, price_table_version, max_cost) "
        "VALUES (:r, :s, :i, :o, 'm', 'p', 0.5) RETURNING id")


def test_every_call_names_its_invocation(w):
    rid = w.running(agents=True)
    st = w.stage(rid)
    w.rejected("INSERT INTO model_call (run_id, stage_result_id, role, model, price_table_version, max_cost) "
               "VALUES (:r, :s, 'planner', 'm', 'p', 0.5)", "ck_model_call_with_invocation", r=rid, s=st)
    assert w.call(rid, st)


def test_a_registration_call_belongs_to_no_run_and_is_finished_once(w):
    v = sealed_version_with_documentation(w)
    inv = w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    call = w.val(CALL, r=None, s=None, i=inv, o="curator")
    w.finish_call(call, "succeeded", (2000, 300, 0, 0.007))
    with pytest.raises(IntegrityError, match="finished exactly once"):
        w.finish_call(call, "failed", None)
    rid = w.running(agents=True)
    st = w.stage(rid, "curator", "curator")
    w.rejected(CALL, "belongs to no run", r=rid, s=st, i=inv, o="curator")            # a run on a registration call
    w.rejected(CALL, "belongs to no run", r=None, s=None, i=inv, o="planner")         # another role
    w.rejected(CALL, "ck_model_call_run_with_stage", r=rid, s=None, i=None, o="curator")
    month = w.val("SELECT sum(reported_cost) FROM model_call_totals_by_month")
    assert float(month) == 0.007  # the month counts registration calls; no run's total does
    assert float(w.val("SELECT sum(cap_cost) FROM model_call_totals_by_run")) == 0


def test_a_registration_call_cannot_be_moved_to_a_run(w):
    v = sealed_version_with_documentation(w)
    inv = w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    call = w.val(CALL, r=None, s=None, i=inv, o="curator")
    rid = w.running(agents=True)
    st = w.stage(rid, "curator", "curator")
    w.rejected("UPDATE model_call SET run_id = :r, stage_result_id = :s, status = 'interrupted', finished_at = now() "
               "WHERE id = :c", "cannot change", r=rid, s=st, c=call)
    other = w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    w.rejected("UPDATE model_call SET invocation_id = :i, status = 'interrupted', finished_at = now() WHERE id = :c",
               "cannot change", i=other, c=call)


def test_a_run_call_has_its_invocations_run_stage_and_role(w):
    rid = w.running(agents=True)
    planner, critic = w.stage(rid), w.stage(rid, "critic", "critic")
    inv = w.invocation(rid, planner)
    w.rejected(CALL, "its invocation's run, stage and role", r=rid, s=critic, i=inv, o="critic")
    w.rejected(CALL, "its invocation's run, stage and role", r=rid, s=planner, i=inv, o="critic")
    assert w.val(CALL, r=rid, s=planner, i=inv, o="planner")


# --- the Curator's proposals and a person's decisions ----------------------------------------------

PROPOSAL = ("INSERT INTO curator_proposal (invocation_id, source_version_id, field, status, value, quote, "
            "document_path, line, term, refusal_code) VALUES (:i, :v, :f, :st, CAST(:val AS jsonb), :q, :d, :l, :t, :rc) "
            "RETURNING id")


def proposal(**kw):
    p = dict(f="test_type", st="proposed", val='"tension"', q=QUOTE, d="documentation/main.tex", l=1, t="tensile",
             rc=None)
    p.update(kw)
    return p


@pytest.fixture
def curation(w):
    v = sealed_version_with_documentation(w)
    return v, w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))


def test_a_proposal_that_passed_is_found_in_its_document_by_the_database(w, curation):
    v, inv = curation
    spaced = QUOTE.replace(" was ", "  was\n ")  # whitespace differs: runs are collapsed on both sides
    assert w.val(PROPOSAL, i=inv, v=v, **proposal(q=spaced))


@pytest.mark.parametrize("change, match", [
    (dict(q="Quasistatic tensile testing was used to measure everything in the world"), "must occur"),
    (dict(d="table.csv"), "must occur"),                                   # not a documentation file
    (dict(d="documentation/other.tex"), "must occur"),
    (dict(t="compression"), "ck_curator_proposal_proposed_complete"),     # the term is not in the quote
    (dict(q="tensile testing", t="tensile"), "ck_curator_proposal_proposed_complete"),  # too short
    (dict(l=0), "ck_curator_proposal_proposed_complete"),
    (dict(val=None), "ck_curator_proposal_proposed_complete"),
    (dict(f="yield_strength"), "ck_curator_proposal_field"),
    (dict(rc="quote_not_found"), "ck_curator_proposal_refusal_code"),
])
def test_a_proposal_that_did_not_pass_cannot_be_stored_as_passed(w, curation, change, match):
    v, inv = curation
    w.rejected(PROPOSAL, match, i=inv, v=v, **proposal(**change))


def test_refused_and_not_stated_proposals_are_kept_with_their_shape(w, curation):
    v, inv = curation
    assert w.val(PROPOSAL, i=inv, v=v, **proposal(f="phase_class", st="refused", val='"FCC"', q="made up",
                                                  t=None, rc="quote_not_found"))
    w.rejected(PROPOSAL, "ck_curator_proposal_refusal_code", i=inv, v=v,
               **proposal(f="microstructure", st="refused", rc=None))
    w.rejected(PROPOSAL, "ck_curator_proposal_not_stated_empty", i=inv, v=v,
               **proposal(f="test_temperature", st="not_stated"))
    assert w.val(PROPOSAL, i=inv, v=v, **proposal(f="test_temperature", st="not_stated", val=None, q=None, d=None,
                                                  l=None, t=None))
    w.rejected(PROPOSAL, "ck_curator_proposal_bounded", i=inv, v=v,
               **proposal(f="test_temperature_band", st="refused", q="x" * 4001, t=None, rc="too_long"))


def test_one_proposal_per_field_per_invocation_for_its_own_version(w, curation):
    v, inv = curation
    w.val(PROPOSAL, i=inv, v=v, **proposal())
    w.rejected(PROPOSAL, "uq_curator_proposal_invocation_id_field", i=inv, v=v, **proposal())
    other = sealed_version_with_documentation(w, label="other")
    w.rejected(PROPOSAL, "its invocation's source version", i=inv, v=other, **proposal(f="phase_class"))
    rid = w.running(agents=True)
    run_inv = w.invocation(rid, w.stage(rid))  # a run invocation (the Curator never has one: review finding 6)
    w.rejected(PROPOSAL, "registration invocation of the curator", i=run_inv, v=v, **proposal(f="phase_class"))


DECISION = ("INSERT INTO curator_decision (proposal_id, decision, decided_by, note) VALUES (:p, :d, :b, :n) "
            "RETURNING id")


def test_a_person_decides_once_on_a_proposal_that_passed(w, curation):
    v, inv = curation
    passed = w.val(PROPOSAL, i=inv, v=v, **proposal())
    refused = w.val(PROPOSAL, i=inv, v=v, **proposal(f="phase_class", st="refused", t=None, rc="term_missing"))
    w.rejected(DECISION, "only a proposal that passed", p=refused, d="accepted", b="Khalid El-Awady", n=None)
    w.rejected(DECISION, "ck_curator_decision_named_and_bounded", p=passed, d="accepted", b="  ", n=None)
    w.rejected(DECISION, "ck_curator_decision_decision", p=passed, d="maybe", b="Khalid El-Awady", n=None)
    assert w.val(DECISION, p=passed, d="accepted", b="Khalid El-Awady", n="quote checked")
    w.rejected(DECISION, "uq_curator_decision_proposal_id", p=passed, d="rejected", b="Khalid El-Awady", n=None)
    w.rejected("UPDATE curator_decision SET decision = 'rejected'", "append-only")
    w.rejected("UPDATE curator_proposal SET value = '\"compression\"'", "append-only")
    w.rejected("DELETE FROM curator_proposal", "append-only")


def test_the_database_sets_the_decision_time(w, curation):
    v, inv = curation
    passed = w.val(PROPOSAL, i=inv, v=v, **proposal())
    w.run_sql("INSERT INTO curator_decision (proposal_id, decision, decided_by, decided_at) "
              "VALUES (:p, 'accepted', 'K', now() - interval '3 days')", p=passed)
    assert w.val("SELECT decided_at > now() - interval '1 minute' FROM curator_decision WHERE proposal_id = :p",
                 p=passed)


# --- review fixes (ChatGPT, 2026-10-07; owner's term-check changes) ------------------------------------
# Finding 6: the Curator never runs within a run, enforced when the invocation is created.

def test_a_run_invocation_of_the_curator_is_refused(w):
    rid = w.running(agents=True)
    stage = w.stage(rid, "curator", "curator")   # a running stage with that role, and its setting recorded
    sql, params = run_invocation(w, rid, stage, role="curator")
    w.rejected(sql, "ck_agent_invocation_shape", **params)


# Finding 2: the database checks the value, its type and vocabulary, and its term; nothing it needs is NULL.

@pytest.mark.parametrize("change", [
    dict(l=None), dict(t=None), dict(q=None), dict(d=None), dict(val=None), dict(val="null"),
])
def test_a_passed_proposal_with_a_missing_part_is_refused(w, curation, change):
    """A NULL must not turn the completeness check into UNKNOWN (which a CHECK accepts); JSON null is
    not a value either."""
    v, inv = curation
    w.rejected(PROPOSAL, "ck_curator_proposal_proposed_complete", i=inv, v=v, **proposal(**change))


def test_json_null_is_never_stored_as_a_value(w, curation):
    v, inv = curation
    w.rejected(PROPOSAL, "ck_curator_proposal_value_not_json_null", i=inv, v=v,
               **proposal(f="phase_class", st="refused", val="null", t=None, rc="value_not_allowed"))
    assert w.val(PROPOSAL, i=inv, v=v, **proposal(f="phase_class", st="refused", val=None, t=None,
                                                  rc="value_not_allowed"))


@pytest.mark.parametrize("change", [
    dict(val='"compression"'),                          # the reviewer's case: the term belongs to another value
    dict(val='"compression"', t="compression"),         # a term that is not in the quote
    dict(val='"shear"'),                                # not in the vocabulary
    dict(val='5'),                                      # not a string
    dict(val='["tension"]'),
    dict(t="tension"),                                  # a listed term, but not in the quote
    dict(t="Quasistatic"),                              # in the quote, but not a listed term
    dict(t="TENSILE"),                                  # not as listed
    dict(f="phase_class", val='"FCC"', t="tensile"),    # a term of another field
    dict(f="test_temperature", val='"25"', t="25"),     # a temperature is a number
    dict(f="microstructure", val='"FCC+B2"', t="FCC"),  # every part needs its term in the quote
    dict(f="microstructure", val='"FCC+"', t="FCC"),
])
def test_a_value_that_does_not_match_its_term_is_refused(w, curation, change):
    v, inv = curation
    w.rejected(PROPOSAL, "ck_curator_proposal_proposed_complete", i=inv, v=v, **proposal(**change))


def test_the_matching_value_and_term_are_stored(w, curation):
    v, inv = curation
    assert w.val(PROPOSAL, i=inv, v=v, **proposal())
    assert w.val(PROPOSAL, i=inv, v=v, **proposal(f="microstructure", val='"FCC"', t="FCC",
                                                  q="The dataset contains 94 FCC alloy conditions in the system.",
                                                  l=2))


def test_a_quote_must_begin_and_end_at_a_word_boundary_in_the_document(w, curation):
    v, inv = curation
    w.rejected(PROPOSAL, "must occur", i=inv, v=v, **proposal(q=QUOTE[1:]))          # "uasistatic …"
    w.rejected(PROPOSAL, "must occur", i=inv, v=v, **proposal(q=QUOTE[:-1]))         # "… offset Y"


def test_the_databases_term_list_is_the_codes():
    from hypocurate.pipeline.agents import quotes
    listed = {(f, v, t) for f, by_value in quotes.TERMS.items() for v, terms in by_value.items() for t in terms}
    assert {(f, v, t) for f, v, t in M0005.CURATOR_TERMS} == listed and len(M0005.CURATOR_TERMS) == len(listed)
    assert set(M0005.CASE_SENSITIVE_TERMS) == set(quotes.CASE_SENSITIVE_TERMS)
    assert tuple(M0005.TESTING_WORDS) == tuple(quotes.TESTING_WORDS)
    assert tuple(M0005.EXCLUDED_PHRASES) == tuple(quotes.EXCLUDED_PHRASES)
    assert (M0005.QUOTE_MIN, M0005.QUOTE_MAX) == (quotes.QUOTE_MIN_CHARS, quotes.QUOTE_MAX_CHARS) == (30, 600)


# The database and the code agree on every case below: a quote the code passes is stored with the
# code's term and line; for a quote the code refuses, the database refuses every term it could be given.
AGREEMENT = [
    ("test_type", "tension", "Specimens were tested in tension at a constant crosshead speed."),
    ("test_type", "tension", "Specimens were tested after extension of the gauge section by machining."),
    ("test_type", "tension", "The ultimate tensile strength was tested for each of the alloys."),
    ("test_type", "tension", "The ultimate tensile strength and tensile ductility were tested for each."),
    ("test_type", "tension", "Dog-bone tensile specimens were cut from each plate by machining."),
    ("test_type", "tension", "Specimens were pulled in tension at a strain rate of 0.001 per second."),
    ("test_type", "compression", "Cylinders were tested under compressive loading at room temperature."),
    ("phase_class", "FCC", "All alloys were designed as fcc solid solutions in this study."),
    ("phase_class", "FCC", "All alloys were designed as face centered cubic solid solutions."),
    ("phase_class", "BCC", "All alloys were designed as BCCs and HCPs in this study, then."),
    ("microstructure", "B2", "The Nb25 alloys were examined by diffraction after annealing."),
    ("microstructure", "B2", "Ordered B2 precipitates were found after annealing in every alloy."),
    ("microstructure", "B2", "Ordered b2 precipitates were found after annealing in every alloy."),
    ("microstructure", "L12", "Coherent L1$_2$ precipitates were found after ageing in every alloy."),
    ("microstructure", "FCC+B2", "Each alloy had an FCC matrix with B2 particles after annealing."),
    ("microstructure", "FCC+B2", "Each alloy had an FCC matrix with Nb2 particles after annealing."),
    ("test_temperature_band", "room temperature", "All specimens were tested at room temperature in air."),
    ("test_temperature_band", "room temperature", "The plates were cold rolled at room temperature to 60%."),
    ("test_temperature_band", "cryogenic", "Further specimens were tested in liquid helium baths."),
    ("test_temperature", 25, "All the specimens were tested at 25 °C in laboratory air."),
    ("test_temperature", 25, "All the specimens were tested at 25~°C in laboratory air."),
    ("test_temperature", 25, "All the specimens were tested at \\SI{25}{\\degreeCelsius} in air."),
    ("test_temperature", 25, "All the specimens were tested at 25.0 °C in laboratory air."),
    ("test_temperature", 25, "All the specimens were tested at −25 °C in laboratory air."),
    ("test_temperature", 25, "All the specimens were tested at -25 °C in laboratory air."),
    ("test_temperature", 25, "All the specimens were tested at 25.5 °C in laboratory air."),
    ("test_temperature", 25, "All the specimens were tested at 125 °C in laboratory air."),
    ("test_temperature", 25, "All the specimens were tested between 20-25 °C in laboratory air."),
    ("test_temperature", 25, "All the specimens were tested at 25 K in laboratory air, as usual."),
    ("test_temperature", 25, "All the plates were annealed and cooled to 25 °C in still air."),
    ("test_temperature", -196, "All the specimens were tested at −196 °C in liquid nitrogen."),
    ("test_temperature", 25.5, "All the specimens were tested at 25.5 °C in laboratory air."),
    # ChatGPT's re-check and the owner (2026-10-07): larger numbers, ranges, and two testing words removed.
    ("test_temperature", 25, "All specimens were tested at 1,025 °C in laboratory air."),
    ("test_temperature", 25, "All specimens were tested at 1 025 °C in laboratory air."),
    ("test_temperature", 25, "All specimens were tested between 20 - 25 °C in laboratory air."),
    ("test_temperature", 20, "All specimens were tested between 20 - 25 °C in laboratory air."),
    ("test_temperature", 25, "All specimens were tested between 20 – 25 °C in laboratory air."),
    ("test_temperature", 25, "All specimens were tested between 20–25 °C in laboratory air."),
    ("test_temperature", 25, "All specimens were tested from 20 to 25 °C in laboratory air."),
    ("test_temperature", 20, "All specimens were tested from 20 °C to 25 °C in laboratory air."),
    ("test_temperature", 25, "All specimens were tested from 20 °C to 25 °C in laboratory air."),
    ("test_temperature", 25, "Tested from \\SI{20}{\\degreeCelsius} to \\SI{25}{\\degreeCelsius} in air."),
    ("test_temperature", 20, "Tested from \\SI{20}{\\degreeCelsius} to \\SI{25}{\\degreeCelsius} in air."),
    ("test_temperature", 25, "All the specimens were tested at 25 °C after annealing at 1,025 °C."),
    ("test_temperature", 25, "All the specimens were tested at 25 °C, close to room temperature."),
    ("test_temperature", 25, "All the specimens were strained at 25 °C in still laboratory air."),
    ("test_temperature_band", "room temperature", "The plates were deformed by cold rolling at room temperature."),
]


def _stored(engine, params) -> bool:
    with engine.connect() as conn:
        trans = conn.begin()
        try:
            conn.execute(text(PROPOSAL), params)
            return True
        except IntegrityError:
            return False
        finally:
            trans.rollback()


def test_the_database_and_the_code_agree_on_every_case(w):
    import json
    from hypocurate.pipeline.agents import quotes
    document = "\n".join(q for _, _, q in AGREEMENT) + "\n"
    v = w.new_version("tamu_fcc", "agreement")
    w.add_file(v, "table.csv", b"a,b,agreement\n")
    w.add_file(v, "documentation/cases.md", document.encode(), role="documentation")
    w.seal(v)
    inv = w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    docs = {"documentation/cases.md": document}
    passed = 0
    for field, value, quote in AGREEMENT:
        result = quotes.check(field, value, quote, docs)
        base = dict(i=inv, v=v, f=field, st="proposed", val=json.dumps(value), q=quote, d="documentation/cases.md",
                    l=result.located.line if result.located else 1, rc=None)
        if result.code is None:
            passed += 1
            assert _stored(w.e, {**base, "t": result.term}), (field, value, quote)
            continue
        listed = [t for p in str(value).split("+") for t in quotes.TERMS.get(field, {}).get(p, ())]
        numbers = re.findall(r"[-+−–]?\d+(?:\.\d+)?", quote)
        for term in listed + numbers + [str(value)]:
            assert not _stored(w.e, {**base, "t": term}), (field, value, quote, term)
    assert 0 < passed < len(AGREEMENT)


# ChatGPT's re-check (2026-10-07): the database refuses a temperature that is part of a larger number or
# an end of a range, whichever number-shaped term it is given (the code's refusals are in test_quote_checks).
RANGES_AND_LARGER_NUMBERS = [
    (25, "All specimens were tested at 1,025 °C in laboratory air."),
    (25, "All specimens were tested at 1 025 °C in laboratory air."),
    (25, "All specimens were tested between 20 - 25 °C in laboratory air."),
    (25, "All specimens were tested between 20 – 25 °C in laboratory air."),
    (25, "All specimens were tested from 20 to 25 °C in laboratory air."),
    (20, "All specimens were tested from 20 °C to 25 °C in laboratory air."),
    (25, "All specimens were tested from 20 °C to 25 °C in laboratory air."),
    (25, "Tested from \\SI{20}{\\degreeCelsius} to \\SI{25}{\\degreeCelsius} in laboratory air."),
    (20, "Tested from \\SI{20}{\\degreeCelsius} to \\SI{25}{\\degreeCelsius} in laboratory air."),
]


def test_the_database_refuses_larger_numbers_and_ranges(w):
    import json
    document = "\n".join(q for _, q in RANGES_AND_LARGER_NUMBERS) + "\n"
    v = w.new_version("tamu_fcc", "ranges")
    w.add_file(v, "table.csv", b"a,b,ranges\n")
    w.add_file(v, "documentation/cases.md", document.encode(), role="documentation")
    w.seal(v)
    inv = w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
    for line, (value, quote) in enumerate(RANGES_AND_LARGER_NUMBERS, start=1):
        for term in (str(value), f"0{value}", "025", "25", "20"):
            assert not _stored(w.e, dict(i=inv, v=v, f="test_temperature", st="proposed", val=json.dumps(value),
                                         q=quote, d="documentation/cases.md", l=line, t=term, rc=None)), (quote, term)
