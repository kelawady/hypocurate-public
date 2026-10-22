"""Sprint 2 pilot, R1: migration 0010 (PRD v1.2; the owner's decisions of 2026-10-22).

The migration: additive; it follows 0009; it replaces only the two named 0005 functions, and its copies of their 0005
text (restored by the downgrade) equal 0005's; up, down, up gives the same schema; a failed upgrade changes nothing;
the downgrade refuses while anything 0010 added holds data.

The approved safeguard change (document scope, extractor and reconciler roles): every Sprint 1 combination is accepted
or refused as before; a document invocation is the Extractor's on a parsed document, in no run; its calls belong to no
run; the Extractor is refused in a run, the Reconciler outside one.

The tables: PDFs and parses carry hashes the database checks; values and links carry a provenance naming their own
document and parse, or an explicit 'ambiguous' marker; S0 holds exactly the extraction's own proposed events, taken
before any other event on its objects, and nothing is added to an output after its S0; a stop reason is written once
the run has ended; every new table is append-only."""
from __future__ import annotations

import hashlib
import json

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.db import migrate, models
from hypocurate.db.engine import make_engine
from model_builder import World
from test_migrations import assert_schema_is_empty, snapshot

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
PDF = b"%PDF-1.7\n% a test document\n"


def m(rev):
    return SCRIPTS.get_revision(rev).module


def sha(data: str | bytes) -> str:
    return hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


@pytest.fixture
def w(db):
    return World(db)


# --- builders --------------------------------------------------------------------------------------------------------

def document(w, doi="10.1000/abc.1", pdf=PDF, kind="article", parent=None, source="unpaywall", by="code"):
    return w.val("INSERT INTO document (kind, parent_document_id, doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by, "
                 "by_hand) VALUES (:k, :p, :d, :key, :s, :pdf, :h, :by, :bh) RETURNING id",
                 k=kind, p=parent, d=doi, key="doi:" + doi.lower(), s=source, pdf=pdf, h=sha(pdf), by=by,
                 bh=source == "by_hand")


def parse(w, doc, parsed='{"pages": []}'):
    return w.val("INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, parsed, "
                 "parsed_sha256, pages, tables_found) VALUES (:d, 'docling', '2.141.0', false, 'parsed', :p, :h, 3, 1) "
                 "RETURNING id", d=doc, p=parsed, h=sha(parsed))


def output(w, parse_id, raw='{"records": []}', invocation=None):
    h = w.val("SELECT parsed_sha256 FROM document_parse WHERE id = :p", p=parse_id)
    method = json.dumps({"method": "fixture", "name": "fixture_extractor", "version": "1", "prompt_version": "none"})
    return w.val("INSERT INTO extraction_output (document_parse_id, parse_sha256, method, status, raw_output, raw_sha256, "
                 "invocation_id) VALUES (:p, :h, CAST(:m AS jsonb), 'returned', :r, :rh, :i) RETURNING id",
                 p=parse_id, h=h, m=method, r=raw, rh=sha(raw), i=invocation)


def provenance(w, out, **kw):
    doc, h = w.rows("SELECT d.document_id, x.parse_sha256 FROM extraction_output x JOIN document_parse d "
                    "ON d.id = x.document_parse_id WHERE x.id = :x", x=out)[0]
    return json.dumps({"document_id": doc, "parse_sha256": h, "page": 2, "table_index": 0, "row_index": 1,
                       "snippet": "CoCrFeMnNi 4.4 360", **kw})


def observation(w, out, index=0):
    return w.val("INSERT INTO candidate_observation (extraction_output_id, item_index, identity, identity_key) "
                 "VALUES (:x, :i, '{}'::jsonb, :k) RETURNING id", x=out, i=index, k=sha(f"{out}-{index}"))


def value(w, obs, field="grain_size", prov=None, ambiguous=False):
    return w.val("INSERT INTO candidate_value (observation_id, field, value_text, provenance, ambiguous, ambiguity_note) "
                 "VALUES (:o, :f, '4.4', CAST(:p AS jsonb), :a, :n) RETURNING id",
                 o=obs, f=field, p=prov, a=ambiguous, n="cannot tell which specimen" if ambiguous else None)


def link(w, obs, a, b, prov):
    return w.val("INSERT INTO extraction_link (observation_id, from_value_id, to_value_id, kind, provenance) "
                 "VALUES (:o, :a, :b, 'same_table_row', CAST(:p AS jsonb)) RETURNING id", o=obs, a=a, b=b, p=prov)


def event(w, kind, obj, out, state="proposed", rule="extraction", person=None):
    return w.val("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, by_rule, "
                 "by_person) VALUES (:k, :o, :x, :s, :r, :p) RETURNING id", k=kind, o=obj, x=out, s=state, r=rule,
                 p=person)


def s0(w, out, ids=None, raw_sha=None):
    return w.val(S0_SQL, **s0_params(w, out, ids, raw_sha))


def extracted(w):
    """One document, parsed, with an output holding one observation, two values and their link, each recorded
    'proposed' by the extraction."""
    out = output(w, parse(w, document(w)))
    obs = observation(w, out)
    gs = value(w, obs, "grain_size", provenance(w, out))
    ys = value(w, obs, "yield_strength", provenance(w, out))
    lk = link(w, obs, gs, ys, provenance(w, out))
    event(w, "observation", obs, out)
    event(w, "link", lk, out)
    return out, obs, lk


# --- the migration ---------------------------------------------------------------------------------------------------

def test_0010_is_the_head_and_follows_0009():
    assert migrate.head_revision() == "0010" and m("0010").down_revision == "0009"


def test_0010_replaces_only_the_two_named_functions_and_keeps_0005s_text_for_the_downgrade():
    earlier = {f.split("(")[0] for r in ("0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009")
               for f in getattr(m(r), "FUNCTION_NAMES", [])}
    assert not {f.split("(")[0] for f in m("0010").FUNCTION_NAMES} & earlier
    assert "CREATE OR REPLACE" not in " ".join(m("0010").FUNCTIONS)
    assert m("0010").REPLACED_NAMES == ["hc_agent_invocation_insert", "hc_model_call_insert"]
    m5 = m("0005")
    assert m("0010").MODEL_CALL_INSERT_0005 == m5.MODEL_CALL_INSERT_0005
    assert m("0010").AGENT_INVOCATION_INSERT_0005 == m5.FUNCTIONS[0].replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1)


def test_0010s_copy_of_0005s_shape_and_scope_is_0005s(engine):
    migrate.upgrade(engine, "0009")
    with engine.connect() as conn:
        shape, scope = [conn.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = :n"),
                                     dict(n=n)).scalar() for n in ("ck_agent_invocation_shape", "ck_agent_invocation_scope")]
    migrate.upgrade(engine)
    migrate.downgrade(engine, "0009")
    with engine.connect() as conn:
        assert [conn.execute(text("SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = :n"),
                             dict(n=n)).scalar() for n in ("ck_agent_invocation_shape", "ck_agent_invocation_scope")] \
            == [shape, scope]


def test_the_lists_are_the_codes():
    m10 = m("0010")
    assert m10.SPRINT1_ROLES == models.SPRINT1_ROLES == ("planner", "curator", "critic", "analyst", "commentator")
    assert m10.ROLES == models.ROLES and m10.PILOT_ROLES == models.PILOT_ROLES == ("extractor", "reconciler")
    assert m10.INVOCATION_SCOPES == models.INVOCATION_SCOPES and m10.SHAPE_0010 == models.INVOCATION_SHAPE
    for name in ("DOCUMENT_KINDS", "OA_SOURCES", "PARSERS", "PARSE_STATUSES", "SEARCH_ACTIONS", "SEARCH_OUTCOMES",
                 "EXTRACTION_STATUSES", "VALUE_FIELDS", "LINK_KINDS", "EVIDENCE_STATES", "STATE_OBJECTS",
                 "SNAPSHOT_NAMES", "STOP_REASONS", "DOCUMENT_MAX_BYTES", "EXTRACTION_RULE", "PROVENANCE_SHAPE"):
        assert getattr(m10, name) == getattr(models, name), name
    assert m10.MAX_FILE_BYTES == models.MAX_FILE_BYTES


def test_up_down_up_restores_0009(engine):
    migrate.upgrade(engine, "0009")
    at_0009 = snapshot(engine)
    migrate.upgrade(engine)
    first = snapshot(engine)
    migrate.downgrade(engine, "0009")
    assert snapshot(engine) == at_0009
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0009")
    with engine.begin() as conn:
        conn.execute(text("CREATE FUNCTION hc_annotation_file_insert() RETURNS int LANGUAGE sql AS 'SELECT 1'"))
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before and migrate.current_revision(engine) == "0009"


@pytest.mark.parametrize("what", ["document", "pilot_setting"])
def test_the_downgrade_refuses_while_0010_holds_data(db, what):
    w = World(db)
    if what == "document":
        document(w)
    else:
        w.agent_setting("extractor")
    before = snapshot(db)
    with pytest.raises(Exception, match="0010 is in use"):
        migrate.downgrade(db, "0009")
    assert snapshot(db) == before and migrate.current_revision(db) == "0010"


# --- the document scope and the pilot roles (the approved safeguard change) ------------------------------------------

DOC_INV = ("INSERT INTO agent_invocation (scope, run_id, stage_result_id, source_version_id, role, agent_setting_id) "
           "VALUES (:sc, :r, :s, :v, :o, :a) RETURNING id")
DOC_ROW = "INSERT INTO document_invocation (invocation_id, document_parse_id) VALUES (:i, :d)"
CALL = ("INSERT INTO model_call (run_id, stage_result_id, invocation_id, role, model, price_table_version, max_cost) "
        "VALUES (:r, :s, :i, :o, 'model-a', 'prices-2026-10', 0.5) RETURNING id")


def doc_invocation(w, parse_id, role="extractor", row=True):
    """A document invocation and, in the same transaction, the row naming its parsed document."""
    setting = w.agent_setting(role)
    with w.e.begin() as conn:
        inv = conn.execute(text(DOC_INV), dict(sc="document", r=None, s=None, v=None, o=role, a=setting)).scalar()
        if row:
            conn.execute(text(DOC_ROW), dict(i=inv, d=parse_id))
    return inv


def test_a_document_invocation_is_the_extractors_on_a_parsed_document_in_no_run(w):
    p = parse(w, document(w))
    inv = doc_invocation(w, p)
    assert w.val("SELECT scope FROM agent_invocation WHERE id = :i", i=inv) == "document"
    assert w.val("SELECT document_parse_id FROM document_invocation WHERE invocation_id = :i", i=inv) == p
    with pytest.raises(IntegrityError, match="names the parsed document it reads"):  # no row: refused at commit
        doc_invocation(w, p, row=False)
    failed = w.val("INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, "
                   "failure_reason) VALUES (:d, 'pymupdf', '2.0', true, 'failed', 'no text') RETURNING id",
                   d=document(w, doi="10.1000/abc.2"))
    with pytest.raises(IntegrityError, match="reads a parsed document"):
        doc_invocation(w, failed)
    for role in ("reconciler", "curator", "planner"):  # only the extractor reads a document
        with pytest.raises(IntegrityError, match="ck_agent_invocation_shape"):
            w.val(DOC_INV, sc="document", r=None, s=None, v=None, o=role, a=w.agent_setting(role))
    rid = w.running(agents=True)
    st = w.stage(rid, "extraction_test", "extractor")
    with pytest.raises(IntegrityError, match="ck_agent_invocation_shape"):  # a run as well
        w.val(DOC_INV, sc="document", r=rid, s=st, v=None, o="extractor", a=w.agent_setting("extractor"))
    run_inv = w.invocation(rid, w.stage(rid, "planner", "planner"), "planner")
    w.rejected(DOC_ROW, "belongs to an extractor invocation in the document scope", i=run_inv, d=p)


def test_the_extractor_is_refused_in_a_run_and_the_reconciler_outside_one(w):
    rid = w.running(agents=True)
    st = w.stage(rid, "extraction_test", "extractor")
    with pytest.raises(IntegrityError, match="ck_agent_invocation_shape"):
        w.val(DOC_INV, sc="run", r=rid, s=st, v=None, o="extractor", a=w.agent_setting("extractor"))
    sv = w.version["mpea"]
    with pytest.raises(IntegrityError, match="ck_agent_invocation_shape"):
        w.val(DOC_INV, sc="registration", r=None, s=None, v=sv, o="reconciler", a=w.agent_setting("reconciler"))


def test_sprint1_combinations_are_unchanged(w):
    rid = w.running(agents=True)
    st = w.stage(rid, "planner", "planner")
    w.invocation(rid, st, "planner")  # a run invocation, as before
    sv = w.version["mpea"]
    w.val(DOC_INV, sc="registration", r=None, s=None, v=sv, o="curator", a=w.agent_setting("curator"))
    curator_stage = w.stage(rid, "curator_test", "curator")  # so the trigger's stage check passes and the shape decides
    for kw in (dict(sc="registration", r=None, s=None, v=sv, o="planner"),
               dict(sc="run", r=rid, s=curator_stage, v=None, o="curator"),
               dict(sc="run", r=rid, s=st, v=sv, o="planner")):
        with pytest.raises(IntegrityError, match="ck_agent_invocation_shape"):
            w.val(DOC_INV, a=w.agent_setting(kw["o"]), **kw)
    with pytest.raises(IntegrityError, match="ck_agent_invocation_scope"):
        # (a sealed version named, so the trigger's fall-through branch passes and the scope list decides)
        w.val(DOC_INV, sc="paper", r=None, s=None, v=sv, o="curator", a=w.agent_setting("curator"))


def test_no_column_is_added_to_an_existing_table(engine):
    """The Sprint 1 reference dumps read every column of the tables they dump (owner, 2026-10-22: byte-identical)."""
    migrate.upgrade(engine, "0009")
    q = "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public'"
    with engine.connect() as conn:
        before = set(conn.execute(text(q)).all())
    migrate.upgrade(engine)
    with engine.connect() as conn:
        after = set(conn.execute(text(q)).all())
    assert {t for t, _ in after - before} == set(m("0010").NEW_TABLES)


def test_a_document_call_belongs_to_no_run_and_has_its_invocations_role(w):
    inv = doc_invocation(w, parse(w, document(w)))
    call = w.val(CALL, r=None, s=None, i=inv, o="extractor")
    w.finish_call(call)
    assert w.val("SELECT status FROM model_call WHERE id = :c", c=call) == "succeeded"
    rid = w.running(agents=True)
    st = w.stage(rid, "planner", "planner")
    w.rejected(CALL, "belongs to no run", r=rid, s=st, i=inv, o="extractor")
    with pytest.raises(IntegrityError, match="ck_model_call_role|belongs to no run"):
        w.val(CALL, r=None, s=None, i=inv, o="reconciler")
    assert float(w.val("SELECT coalesce(sum(cost), 0) FROM model_call WHERE run_id IS NULL")) == 0.01


def test_a_run_call_still_needs_a_running_run(w):
    rid = w.locked(agents=True)
    st = w.stage(rid, "planner", "planner")
    call = w.call(rid, st)
    w.finish_call(call)
    w.run_sql("UPDATE stage_result SET status = 'done', finished_at = now() WHERE id = :s", s=st)
    w.complete(rid, "insufficient")
    w.rejected(CALL, "while the run is running", r=rid, s=st, i=w.val("SELECT invocation_id FROM model_call WHERE id "
                                                                      "= :c", c=call), o="planner")


# --- documents, parses, the search log -------------------------------------------------------------------------------

def test_a_document_is_a_pdf_whose_hash_the_database_checks(w):
    with pytest.raises(IntegrityError, match="ck_document_is_pdf"):
        document(w, pdf=b"<html>not a pdf</html>")
    with pytest.raises(IntegrityError, match="ck_document_sha256_matches_pdf"):
        w.val("INSERT INTO document (doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by) VALUES "
              "('10.1/x', 'doi:10.1000/x', 'unpaywall', :p, :h, 'code') RETURNING id", p=PDF, h="0" * 64)
    with pytest.raises(IntegrityError, match="ck_document_doi_key_format"):
        w.val("INSERT INTO document (doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by) VALUES "
              "('x', 'x', 'unpaywall', :p, :h, 'code') RETURNING id", p=PDF, h=sha(PDF))


def test_a_supplement_belongs_to_an_article_and_a_fetch_by_hand_says_so(w):
    art = document(w)
    document(w, kind="supplement", parent=art, source="by_hand", by="Khalid El-Awady")
    with pytest.raises(IntegrityError, match="ck_document_parent_unless_article"):
        document(w, kind="supplement")
    with pytest.raises(IntegrityError, match="ck_document_by_hand_source"):
        w.val("INSERT INTO document (doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by, by_hand) VALUES "
              "('10.1000/y', 'doi:10.1000/y', 'unpaywall', :p, :h, 'code', true)", p=PDF, h=sha(PDF))


def test_a_parse_carries_its_hash_or_a_failure_with_its_reason(w):
    doc = document(w)
    with pytest.raises(IntegrityError, match="ck_document_parse_sha256_matches_parsed"):
        w.val("INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, parsed, "
              "parsed_sha256, pages, tables_found) VALUES (:d, 'docling', '1', false, 'parsed', '{}', :h, 1, 0)",
              d=doc, h="0" * 64)
    with pytest.raises(IntegrityError, match="ck_document_parse_failed_has_reason"):
        w.val("INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status) "
              "VALUES (:d, 'pymupdf', '2.0', true, 'failed')", d=doc)


def test_the_search_log_names_its_actor_and_marks_steps_done_by_hand(w):
    w.val("INSERT INTO search_log (action, doi_key, url, http_status, outcome, actor) VALUES "
          "('unpaywall_lookup', 'doi:10.1000/abc.1', 'https://api.unpaywall.org/v2/10.1000/abc.1', 200, 'found', "
          "'code') RETURNING id")
    w.val("INSERT INTO search_log (action, doi_key, outcome, actor, by_hand) VALUES ('fetch_by_hand', "
          "'doi:10.1000/abc.1', 'ok', 'Khalid El-Awady', true) RETURNING id")
    with pytest.raises(IntegrityError, match="ck_search_log_by_hand_action"):
        w.val("INSERT INTO search_log (action, outcome, actor, by_hand) VALUES ('download', 'ok', 'code', true)")
    with pytest.raises(IntegrityError, match="ck_search_log_actor_named"):
        w.val("INSERT INTO search_log (action, outcome, actor) VALUES ('download', 'ok', ' ')")


# --- the Extractor's output and candidates ---------------------------------------------------------------------------

def test_an_outputs_raw_hash_is_checked_and_its_invocation_is_the_extractors_on_that_parse(w):
    p = parse(w, document(w))
    with pytest.raises(IntegrityError, match="ck_extraction_output_sha256_matches_raw"):
        w.val("INSERT INTO extraction_output (document_parse_id, parse_sha256, method, status, raw_output, raw_sha256) "
              "VALUES (:p, :h, '{\"method\":\"a\",\"name\":\"b\",\"version\":\"1\",\"prompt_version\":\"v1\"}', "
              "'returned', 'x', :z)", p=p, h=sha('{"pages": []}'), z="0" * 64)
    other = parse(w, document(w, doi="10.1000/abc.2"), parsed='{"pages": [1]}')
    inv = doc_invocation(w, other)
    w.rejected("INSERT INTO extraction_output (document_parse_id, parse_sha256, method, status, raw_output, raw_sha256, "
               "invocation_id) VALUES (:p, :h, '{\"method\":\"a\",\"name\":\"b\",\"version\":\"1\","
               "\"prompt_version\":\"v1\"}', 'returned', 'x', :rh, :i)", "same parsed document",
               p=p, h=sha('{"pages": []}'), rh=sha("x"), i=inv)
    output(w, other, invocation=inv)


def test_a_value_and_a_link_carry_a_provenance_of_their_own_parse_or_are_marked_ambiguous(w):
    out = output(w, parse(w, document(w)))
    obs = observation(w, out)
    with pytest.raises(IntegrityError, match="ck_candidate_value_provenance_or_ambiguous"):
        value(w, obs)
    value(w, obs, "grain_size", ambiguous=True)
    no_snippet = {k: v for k, v in json.loads(provenance(w, out)).items() if k != "snippet"}
    with pytest.raises(IntegrityError, match="ck_candidate_value_provenance_shape"):
        value(w, obs, "yield_strength", json.dumps(no_snippet))
    other = output(w, parse(w, document(w, doi="10.1000/abc.2"), parsed='{"other": 1}'))
    w.rejected("INSERT INTO candidate_value (observation_id, field, value_text, provenance) VALUES (:o, 'alloy', 'x', "
               "CAST(:p AS jsonb))", "names the document and parse", o=obs, p=provenance(w, other))
    ys = value(w, obs, "yield_strength", provenance(w, out, sentence="YS was 360 MPa", table_index=None))
    alloy = value(w, obs, "alloy", provenance(w, out))
    gs = w.val("SELECT id FROM candidate_value WHERE observation_id = :o AND field = 'grain_size'", o=obs)
    w.rejected("INSERT INTO extraction_link (observation_id, from_value_id, to_value_id, kind, provenance) VALUES "
               "(:o, :a, :b, 'same_table_row', CAST(:p AS jsonb))", "names the document and parse",
               o=obs, a=gs, b=ys, p=provenance(w, other))
    with pytest.raises(IntegrityError, match="ck_extraction_link_provenance_or_ambiguous"):
        w.val("INSERT INTO extraction_link (observation_id, from_value_id, to_value_id) VALUES (:o, :a, :b)",
              o=obs, a=gs, b=alloy)
    w.val("INSERT INTO extraction_link (observation_id, from_value_id, to_value_id, ambiguous, ambiguity_note) VALUES "
          "(:o, :a, :b, true, 'two specimens annealed at 800 C') RETURNING id", o=obs, a=gs, b=alloy)


def test_a_link_joins_two_values_of_its_own_observation(w):
    out = output(w, parse(w, document(w)))
    a, b = observation(w, out, 0), observation(w, out, 1)
    va, vb = value(w, a, prov=provenance(w, out)), value(w, b, prov=provenance(w, out))
    with pytest.raises(IntegrityError, match="fk_extraction_link_to_value"):
        link(w, a, va, vb, provenance(w, out))


# --- evidence states and S0 ------------------------------------------------------------------------------------------

def test_s0_holds_exactly_the_extractions_proposed_events_and_its_raw_hash(w):
    out, obs, lk = extracted(w)
    ids = [r[0] for r in w.rows("SELECT id FROM evidence_state_event WHERE extraction_output_id = :x ORDER BY id", x=out)]
    w.rejected(S0_SQL, "exactly its extraction output", **s0_params(w, out, ids[:1]))
    w.rejected(S0_SQL, "raw hash", **s0_params(w, out, ids, raw_sha="0" * 64))
    w.rejected(S0_SQL, "hash of its event ids", **{**s0_params(w, out, ids), "eh": "0" * 64})
    w.rejected(S0_SQL, "ascending order", **s0_params(w, out, list(reversed(ids)), sort=False))
    s0(w, out, ids)
    with pytest.raises(IntegrityError, match="uq_evidence_snapshot_s0"):
        s0(w, out, ids)


def test_s0_needs_a_proposed_event_for_every_observation_and_link(w):
    out = output(w, parse(w, document(w)))
    obs = observation(w, out)
    a, b = value(w, obs, "grain_size", provenance(w, out)), value(w, obs, "yield_strength", provenance(w, out))
    link(w, obs, a, b, provenance(w, out))
    event(w, "observation", obs, out)  # the link has no event
    w.rejected(S0_SQL, "every observation and link", **s0_params(w, out))


def test_no_other_event_before_s0_and_no_extraction_event_or_candidate_after_it(w):
    out, obs, lk = extracted(w)
    w.rejected(EVENT_SQL, "before the extraction output's S0", k="link", o=lk, x=out, s="accepted", r="R-link-1", p=None)
    w.rejected(EVENT_SQL, "before the extraction output's S0", k="observation", o=obs, x=out, s="disputed", r=None,
               p="Khalid El-Awady")
    s0(w, out)
    event(w, "link", lk, out, state="accepted", rule="R-link-1")
    event(w, "observation", obs, out, state="disputed", rule=None, person="Khalid El-Awady")
    w.rejected(EVENT_SQL, "before the output's S0 is taken", k="observation", o=obs, x=out, s="proposed",
               r="extraction", p=None)
    w.rejected("INSERT INTO candidate_observation (extraction_output_id, item_index, identity, identity_key) "
               "VALUES (:x, 9, '{}'::jsonb, :k)", "before its S0 is taken", x=out, k=sha("late"))
    w.rejected("INSERT INTO candidate_value (observation_id, field, value_text, ambiguous, ambiguity_note) VALUES "
               "(:o, 'phase', 'FCC', true, 'late')", "before its S0 is taken", o=obs)


def test_an_event_names_an_object_of_its_own_output_by_one_rule_or_one_person(w):
    out, obs, lk = extracted(w)
    other, _, _ = extracted_second(w)
    w.rejected(EVENT_SQL, "existing observation or link of its extraction output", k="observation", o=obs, x=other,
               s="proposed", r="extraction", p=None)
    w.rejected(EVENT_SQL, "existing observation or link", k="link", o=10 ** 9, x=out, s="proposed", r="extraction",
               p=None)
    with pytest.raises(IntegrityError, match="ck_evidence_state_event_rule_or_person"):
        w.val(EVENT_SQL, k="observation", o=obs, x=out, s="proposed", r="extraction", p="Ada")
    s0(w, out)  # after S0 the trigger accepts any other event, so the state list decides
    with pytest.raises(IntegrityError, match="ck_evidence_state_event_state"):
        w.val(EVENT_SQL, k="observation", o=obs, x=out, s="maybe", r="R-link-1", p=None)


def test_s1_and_s2_list_existing_events(w):
    out, obs, lk = extracted(w)
    s0(w, out)
    ids = [r[0] for r in w.rows("SELECT id FROM evidence_state_event ORDER BY id")]
    for name in ("S1", "S2"):
        w.val("INSERT INTO evidence_snapshot (name, event_ids, events_sha256, taken_by) VALUES (:n, CAST(:i AS bigint[]),"
              " :h, 'code') RETURNING id", n=name, i="{" + ",".join(map(str, ids)) + "}", h=sha(",".join(map(str, ids))))
    bad = ids + [10 ** 9]
    w.rejected("INSERT INTO evidence_snapshot (name, event_ids, events_sha256, taken_by) VALUES ('S1', "
               "CAST(:i AS bigint[]), :h, 'code')", "existing state events", i="{" + ",".join(map(str, bad)) + "}",
               h=sha(",".join(map(str, bad))))
    with pytest.raises(IntegrityError, match="ck_evidence_snapshot_s0_per_output"):
        w.val("INSERT INTO evidence_snapshot (name, extraction_output_id, raw_sha256, event_ids, events_sha256, "
              "taken_by) VALUES ('S1', :x, :h, '{}', :e, 'code')", x=out, h="0" * 64, e=sha(""))


# --- stop reasons, annotations, append-only --------------------------------------------------------------------------

def test_a_stop_reason_is_written_once_when_the_run_has_ended(w):
    rid = w.running()
    w.rejected("INSERT INTO run_stop_reason (run_id, reason) VALUES (:r, 'corpus_processed')", "when the run ends", r=rid)
    w.fail(rid)
    w.run_sql("INSERT INTO run_stop_reason (run_id, reason, detail) VALUES (:r, 'budget_exhausted', 'cap')", r=rid)
    with pytest.raises(IntegrityError, match="pk_run_stop_reason"):
        w.run_sql("INSERT INTO run_stop_reason (run_id, reason) VALUES (:r, 'corpus_processed')", r=rid)
    w.fail(other := w.running())
    with pytest.raises(IntegrityError, match="ck_run_stop_reason_reason"):
        w.run_sql("INSERT INTO run_stop_reason (run_id, reason) VALUES (:r, 'gave up')", r=other)


def test_an_annotation_files_hash_is_checked(w):
    content = b"paper_doi,alloy_as_written\n"
    with pytest.raises(IntegrityError, match="ck_annotation_file_sha256_matches_content"):
        w.val("INSERT INTO annotation_file (filename, content, sha256, template_version, loaded_by) VALUES "
              "('a.csv', :c, :h, 'B1+identity-1', 'Khalid El-Awady')", c=content, h="0" * 64)
    fid = w.val("INSERT INTO annotation_file (filename, content, sha256, template_version, loaded_by) VALUES "
                "('a.csv', :c, :h, 'B1+identity-1', 'Khalid El-Awady') RETURNING id", c=content, h=sha(content))
    w.val("INSERT INTO annotation_row (annotation_file_id, row_number, doi_key, identity, identity_key, cells, annotator, "
          "minutes) VALUES (:f, 1, 'doi:10.1000/abc.1', '{}', :k, '{}', 'Khalid El-Awady', 25) RETURNING id",
          f=fid, k=sha("x"))


def test_every_new_table_is_append_only(w):
    out, obs, lk = extracted(w)
    s0(w, out)
    doc_invocation(w, w.val("SELECT document_parse_id FROM extraction_output WHERE id = :x", x=out))
    w.fail(rid := w.running())
    w.run_sql("INSERT INTO run_stop_reason (run_id, reason) VALUES (:r, 'corpus_processed')", r=rid)
    w.val("INSERT INTO search_log (action, outcome, actor) VALUES ('select', 'ok', 'code') RETURNING id")
    fid = w.val("INSERT INTO annotation_file (filename, content, sha256, template_version, loaded_by) VALUES "
                "('a.csv', 'x', :h, 'v1', 'K') RETURNING id", h=sha("x"))
    w.val("INSERT INTO annotation_row (annotation_file_id, row_number, doi_key, identity, identity_key, cells, "
          "annotator) VALUES (:f, 1, 'doi:10.1000/abc.1', '{}', :k, '{}', 'K') RETURNING id", f=fid, k=sha("y"))
    for table in m("0010").NEW_TABLES:
        assert w.val(f"SELECT count(*) FROM {table}") >= 1, table
        w.rejected(f"UPDATE {table} SET {first_column(w, table)} = {first_column(w, table)}", "append-only")
        w.rejected(f"DELETE FROM {table}", "append-only")
        w.rejected(f"TRUNCATE {table} CASCADE", "append-only")


def test_the_database_sets_the_times(w):
    out, obs, lk = extracted(w)
    assert w.val("SELECT bool_and(at > '2001-01-01') FROM evidence_state_event")
    doc = w.val("INSERT INTO document (doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by, fetched_at) VALUES "
                "('10.1000/t', 'doi:10.1000/t', 'openalex', :p, :h, 'code', '2000-01-01') RETURNING id",
                p=PDF, h=sha(PDF))
    assert w.val("SELECT fetched_at > '2001-01-01' FROM document WHERE id = :d", d=doc)


# --- helpers used above ----------------------------------------------------------------------------------------------

EVENT_SQL = ("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, by_rule, by_person) "
             "VALUES (:k, :o, :x, :s, :r, :p) RETURNING id")
S0_SQL = ("INSERT INTO evidence_snapshot (name, extraction_output_id, raw_sha256, event_ids, events_sha256, taken_by) "
          "VALUES ('S0', :x, :h, CAST(:ids AS bigint[]), :eh, 'code') RETURNING id")


def s0_params(w, out, ids=None, raw_sha=None, sort=True):
    if ids is None:
        ids = [r[0] for r in w.rows("SELECT id FROM evidence_state_event WHERE extraction_output_id = :x", x=out)]
    ids = sorted(ids) if sort else ids
    return dict(x=out, h=raw_sha or w.val("SELECT raw_sha256 FROM extraction_output WHERE id = :x", x=out),
                ids="{" + ",".join(map(str, ids)) + "}", eh=sha(",".join(map(str, ids))))


def extracted_second(w):
    out = output(w, parse(w, document(w, doi="10.1000/abc.9"), parsed='{"second": true}'))
    obs = observation(w, out)
    event(w, "observation", obs, out)
    return out, obs, None


def first_column(w, table):
    return w.val("SELECT column_name FROM information_schema.columns WHERE table_name = :t ORDER BY ordinal_position "
                 "LIMIT 1", t=table)
