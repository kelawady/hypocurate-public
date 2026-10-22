"""The evidence-assembly pilot (Sprint 2, PRD v1.2 R1): documents, parses, the search log, the Extractor's output and
candidates with provenance, evidence states, snapshots, run stop reasons and annotations.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-22

Approved by the owner on 2026-10-22 (PRD v1.2 R1; the questions of that day):
- States and stop reasons live in append-only side tables, not as columns on `record` or `run` ("Side tables,
  append-only"): `record` stays append-only, a final run is never updated, and the Sprint 1 reference dumps (which
  read `SELECT *` from record and run) stay byte-identical. The current state of an object is its newest event.
- S0, S1 and S2 are each "the state events up to time T", with T and the event ids stored; no copies of records.
- The Extractor's calls are recorded under a third invocation scope, 'document', with two new roles, 'extractor'
  (document scope only) and 'reconciler' (run scope only): "New scope + roles, approved as a safeguard change".

Additive. New tables only, plus, on existing tables (no column is added to any existing table):
- the role lists of agent_setting, stage_result, model_call and agent_invocation gain 'extractor' and 'reconciler',
  and agent_invocation's scope list and shape gain 'document'; Sprint 1's combinations are accepted and refused
  exactly as before (the shape's first two branches are 0005's, the run branch also excluding the new 'extractor');
  the parsed document a document invocation reads is a row of the new `document_invocation`, required when the transaction ends by a
  deferred constraint trigger on agent_invocation (a new trigger, no earlier one changed);
- two of 0005's functions are replaced, each with one branch added for the document scope and its other branches
  verbatim: `hc_agent_invocation_insert` and `hc_model_call_insert`. The downgrade restores 0005's text, copied
  below (a test checks the copies equal 0005's). No other earlier function is replaced.

What the database enforces for S0 (the reference-blind snapshot): every candidate is recorded 'proposed' by the rule
'extraction' before its output's S0 is taken, and no other event on that output's objects is accepted until S0
exists; S0 lists exactly the output's events at that time and the output's raw hash. So nothing that uses the
compilation can act on a candidate before its S0 is frozen, and S0 never contains such an event.

Works with the previous release's code: it never reads or writes the new tables, the new column or the new values.

Downgrade locks every table it changes (ACCESS EXCLUSIVE) and refuses while anything 0010 added holds data (a row in
a new table, or a row using the new scope, roles or column), then restores 0009's schema exactly.

Rules for every migration (README, "Database migrations"): it runs inside the one upgrade transaction; it keeps
working with the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None

# Copied here so the migration does not change when the code does (tests check they equal the code's lists).
SPRINT1_ROLES = ("planner", "curator", "critic", "analyst", "commentator")
PILOT_ROLES = ("extractor", "reconciler")
ROLES = SPRINT1_ROLES + PILOT_ROLES
INVOCATION_SCOPES = ("run", "registration", "document")
DOCUMENT_MAX_BYTES = 50 * 1024 * 1024
MAX_FILE_BYTES = 5 * 1024 * 1024
DOCUMENT_KINDS = ("article", "supplement", "methods")
OA_SOURCES = ("unpaywall", "openalex", "by_hand")
PARSERS = ("docling", "pymupdf")
PARSE_STATUSES = ("parsed", "failed")
SEARCH_ACTIONS = ("select", "openalex_lookup", "unpaywall_lookup", "supplement_check", "download", "parse",
                  "fetch_by_hand")
SEARCH_OUTCOMES = ("ok", "found", "not_found", "refused", "error", "failed")
EXTRACTION_STATUSES = ("returned", "failed")
VALUE_FIELDS = ("alloy", "composition", "processing_state", "specimen_label", "grain_size", "grain_size_type",
                "yield_strength", "test_type", "test_temperature", "strain_rate", "phase")
LINK_KINDS = ("same_table_row", "specimen_label", "explicit_sentence", "methods_statement")
EVIDENCE_STATES = ("proposed", "supported", "accepted", "disputed", "unresolved")
STATE_OBJECTS = ("observation", "link")
SNAPSHOT_NAMES = ("S0", "S1", "S2")
EXTRACTION_RULE = "extraction"
STOP_REASONS = ("corpus_processed", "full_text_inaccessible", "fetched_not_parsed", "specimen_metadata_missing",
                "no_eligible_evidence", "budget_exhausted", "inventory_analysis_deferred")
NAME_MAX = 200
DETAIL_MAX = 2000
SHA256 = "~ '^[0-9a-f]{64}$'"
DOI_KEY = "~ '^doi:10[.][0-9]{4,9}/\\S+$'"
PROVENANCE_SHAPE = ("jsonb_typeof(provenance) = 'object' "
                    "AND provenance ?& array['document_id', 'parse_sha256', 'page', 'snippet'] "
                    "AND (provenance ?& array['table_index', 'row_index'] OR provenance ? 'sentence')")

# The four role lists 0001 and 0005 created, and agent_invocation's scope and shape (0005), before and after.
ROLE_CHECKS = [("agent_setting", "ck_agent_setting_role", "role IN {}"),
               ("stage_result", "ck_stage_result_role", "role IS NULL OR role IN {}"),
               ("model_call", "ck_model_call_role", "role IN {}"),
               ("agent_invocation", "ck_agent_invocation_role", "role IN {}")]
SCOPE_0005 = "scope IN ('run', 'registration')"
SHAPE_0005 = ("(scope = 'run' AND run_id IS NOT NULL AND stage_result_id IS NOT NULL AND source_version_id IS NULL "
              "AND role <> 'curator') "
              "OR (scope = 'registration' AND run_id IS NULL AND stage_result_id IS NULL "
              "AND source_version_id IS NOT NULL AND role = 'curator')")
SHAPE_0010 = (
    "(scope = 'run' AND run_id IS NOT NULL AND stage_result_id IS NOT NULL AND source_version_id IS NULL "
    "AND role <> 'curator' AND role <> 'extractor') "
    "OR (scope = 'registration' AND run_id IS NULL AND stage_result_id IS NULL "
    "AND source_version_id IS NOT NULL AND role = 'curator') "
    "OR (scope = 'document' AND run_id IS NULL AND stage_result_id IS NULL "
    "AND source_version_id IS NULL AND role = 'extractor')")


def _in(column: str, values) -> str:
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


def _list(values) -> str:
    return "(" + ", ".join(f"'{v}'" for v in values) + ")"


def _named(column: str, nullable: bool = False) -> str:
    rule = f"({column} = btrim({column}) AND length({column}) BETWEEN 1 AND {NAME_MAX})"
    return f"{column} IS NULL OR {rule}" if nullable else rule


def ck(name: str) -> str:
    return op.f(name)


# --- 0005's two functions, verbatim (restored by the downgrade) ------------------------------------------------------

AGENT_INVOCATION_INSERT_0005 = """
    CREATE OR REPLACE FUNCTION hc_agent_invocation_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
    BEGIN
        IF NEW.scope = 'run' THEN
            -- The same rule as a model call (0001): while the run is running, and after completion
            -- only the Commentator's, for its own stage.
            IF NOT (s = 'running' OR s = 'completed' AND NEW.role = 'commentator'
                    AND (SELECT stage FROM stage_result WHERE id = NEW.stage_result_id) = 'commentator') THEN
                PERFORM hc_reject('an agent is invoked only while the run is running; after completion only the commentator''s');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM stage_result WHERE id = NEW.stage_result_id AND run_id = NEW.run_id
                             AND role = NEW.role AND status = 'running') THEN
                PERFORM hc_reject('an invocation belongs to a running stage of its run with the same role');
            END IF;
        ELSIF NOT EXISTS (SELECT 1 FROM source_version WHERE id = NEW.source_version_id AND sealed_at IS NOT NULL) THEN
            PERFORM hc_reject('a registration invocation reads a sealed source version');
        END IF;
        NEW.created_at := now();
        RETURN NEW;
    END $$
    """

MODEL_CALL_INSERT_0005 = """
    CREATE OR REPLACE FUNCTION hc_model_call_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
            inv agent_invocation;
    BEGIN
        IF NEW.invocation_id IS NOT NULL THEN
            SELECT * INTO inv FROM agent_invocation WHERE id = NEW.invocation_id;
        END IF;
        IF inv.scope = 'registration' THEN
            IF NEW.run_id IS NOT NULL OR NEW.stage_result_id IS NOT NULL OR NEW.role IS DISTINCT FROM inv.role THEN
                PERFORM hc_reject('a call of a registration invocation belongs to no run and has the invocation''s role');
            END IF;
        ELSE
            IF NOT (s = 'running' OR s = 'completed' AND NEW.role = 'commentator'
                    AND (SELECT stage FROM stage_result WHERE id = NEW.stage_result_id) = 'commentator') THEN
                PERFORM hc_reject('a model call is made while the run is running; after completion only the commentator''s');
            END IF;
            IF inv.id IS NOT NULL AND (NEW.run_id IS DISTINCT FROM inv.run_id
                    OR NEW.stage_result_id IS DISTINCT FROM inv.stage_result_id OR NEW.role IS DISTINCT FROM inv.role) THEN
                PERFORM hc_reject('a model call has its invocation''s run, stage and role');
            END IF;
        END IF;
        IF NEW.status <> 'started' THEN
            PERFORM hc_reject('a model call is recorded before the request, as started');
        END IF;
        IF NEW.started_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('started_at is set by the database');
        END IF;
        RETURN NEW;
    END $$
    """

# --- 0010's versions: one branch added for the document scope; the other branches as in 0005 -------------------------

AGENT_INVOCATION_INSERT_0010 = """
    CREATE OR REPLACE FUNCTION hc_agent_invocation_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
    BEGIN
        IF NEW.scope = 'run' THEN
            -- The same rule as a model call (0001): while the run is running, and after completion
            -- only the Commentator's, for its own stage.
            IF NOT (s = 'running' OR s = 'completed' AND NEW.role = 'commentator'
                    AND (SELECT stage FROM stage_result WHERE id = NEW.stage_result_id) = 'commentator') THEN
                PERFORM hc_reject('an agent is invoked only while the run is running; after completion only the commentator''s');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM stage_result WHERE id = NEW.stage_result_id AND run_id = NEW.run_id
                             AND role = NEW.role AND status = 'running') THEN
                PERFORM hc_reject('an invocation belongs to a running stage of its run with the same role');
            END IF;
        ELSIF NEW.scope = 'document' THEN
            -- 0010: the Extractor, in no run; the parsed document it reads is its document_invocation row, required
            -- when the transaction ends (hc_document_invocation_required).
            NULL;
        ELSIF NOT EXISTS (SELECT 1 FROM source_version WHERE id = NEW.source_version_id AND sealed_at IS NOT NULL) THEN
            PERFORM hc_reject('a registration invocation reads a sealed source version');
        END IF;
        NEW.created_at := now();
        RETURN NEW;
    END $$
    """

MODEL_CALL_INSERT_0010 = """
    CREATE OR REPLACE FUNCTION hc_model_call_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
            inv agent_invocation;
    BEGIN
        IF NEW.invocation_id IS NOT NULL THEN
            SELECT * INTO inv FROM agent_invocation WHERE id = NEW.invocation_id;
        END IF;
        IF inv.scope = 'registration' OR inv.scope = 'document' THEN
            -- 0010: a document invocation's call, like a registration invocation's, belongs to no run.
            IF NEW.run_id IS NOT NULL OR NEW.stage_result_id IS NOT NULL OR NEW.role IS DISTINCT FROM inv.role THEN
                PERFORM hc_reject('a call of a registration invocation belongs to no run and has the invocation''s role');
            END IF;
        ELSE
            IF NOT (s = 'running' OR s = 'completed' AND NEW.role = 'commentator'
                    AND (SELECT stage FROM stage_result WHERE id = NEW.stage_result_id) = 'commentator') THEN
                PERFORM hc_reject('a model call is made while the run is running; after completion only the commentator''s');
            END IF;
            IF inv.id IS NOT NULL AND (NEW.run_id IS DISTINCT FROM inv.run_id
                    OR NEW.stage_result_id IS DISTINCT FROM inv.stage_result_id OR NEW.role IS DISTINCT FROM inv.role) THEN
                PERFORM hc_reject('a model call has its invocation''s run, stage and role');
            END IF;
        END IF;
        IF NEW.status <> 'started' THEN
            PERFORM hc_reject('a model call is recorded before the request, as started');
        END IF;
        IF NEW.started_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('started_at is set by the database');
        END IF;
        RETURN NEW;
    END $$
    """

REPLACED = [(AGENT_INVOCATION_INSERT_0005, AGENT_INVOCATION_INSERT_0010),
            (MODEL_CALL_INSERT_0005, MODEL_CALL_INSERT_0010)]
REPLACED_NAMES = ["hc_agent_invocation_insert", "hc_model_call_insert"]

# --- 0010's own functions ------------------------------------------------------------------------------------------

FUNCTIONS = [
    # The database's time on every new row, whatever the insert says.
    """
    CREATE FUNCTION hc_document_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.parent_document_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM document WHERE id = NEW.parent_document_id AND kind = 'article') THEN
            PERFORM hc_reject('a supplement or methods file belongs to an article');
        END IF;
        NEW.fetched_at := now();
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_document_parse_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        NEW.created_at := now();
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_search_log_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        NEW.at := now();
        RETURN NEW;
    END $$
    """,
    # A document invocation's row names a parsed document and belongs to an Extractor's document invocation.
    """
    CREATE FUNCTION hc_document_invocation_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM agent_invocation WHERE id = NEW.invocation_id AND scope = 'document'
                         AND role = 'extractor') THEN
            PERFORM hc_reject('a document invocation row belongs to an extractor invocation in the document scope');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM document_parse WHERE id = NEW.document_parse_id AND status = 'parsed') THEN
            PERFORM hc_reject('a document invocation reads a parsed document');
        END IF;
        NEW.created_at := now();
        RETURN NEW;
    END $$
    """,
    # When the transaction ends: every document invocation names its parsed document (a deferred constraint trigger, new in 0010).
    """
    CREATE FUNCTION hc_document_invocation_required() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM document_invocation WHERE invocation_id = NEW.id) THEN
            PERFORM hc_reject('a document invocation names the parsed document it reads');
        END IF;
        RETURN NULL;
    END $$
    """,
    # An output reads a parsed document (the foreign key on (parse, hash) requires a parse with a hash); when it came
    # from a model call, its invocation is the Extractor's on that same parse.
    """
    CREATE FUNCTION hc_extraction_output_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.invocation_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM document_invocation WHERE invocation_id = NEW.invocation_id
                  AND document_parse_id = NEW.document_parse_id) THEN
            PERFORM hc_reject('an extraction output comes from an extractor invocation on the same parsed document');
        END IF;
        NEW.created_at := now();
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_candidate_observation_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF EXISTS (SELECT 1 FROM evidence_snapshot WHERE name = 'S0'
                     AND extraction_output_id = NEW.extraction_output_id) THEN
            PERFORM hc_reject('an extraction output''s candidates are stored before its S0 is taken');
        END IF;
        NEW.created_at := now();
        RETURN NEW;
    END $$
    """,
    # A value's or link's provenance names the document and the parse its output was read from.
    """
    CREATE FUNCTION hc_provenance_matches(p_observation bigint, p_provenance jsonb) RETURNS boolean
    LANGUAGE sql STABLE AS $$
        SELECT p_provenance IS NULL OR EXISTS (
            SELECT 1 FROM candidate_observation o
            JOIN extraction_output x ON x.id = o.extraction_output_id
            JOIN document_parse d ON d.id = x.document_parse_id
            WHERE o.id = p_observation
              AND p_provenance->>'parse_sha256' = x.parse_sha256
              AND p_provenance->>'document_id' = d.document_id::text)
    $$
    """,
    """
    CREATE FUNCTION hc_candidate_value_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NOT hc_provenance_matches(NEW.observation_id, NEW.provenance) THEN
            PERFORM hc_reject('a provenance names the document and parse its extraction output was read from');
        END IF;
        IF EXISTS (SELECT 1 FROM candidate_observation o JOIN evidence_snapshot s
                     ON s.name = 'S0' AND s.extraction_output_id = o.extraction_output_id
                   WHERE o.id = NEW.observation_id) THEN
            PERFORM hc_reject('an extraction output''s candidates are stored before its S0 is taken');
        END IF;
        NEW.created_at := now();
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_extraction_link_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NOT hc_provenance_matches(NEW.observation_id, NEW.provenance) THEN
            PERFORM hc_reject('a provenance names the document and parse its extraction output was read from');
        END IF;
        IF EXISTS (SELECT 1 FROM candidate_observation o JOIN evidence_snapshot s
                     ON s.name = 'S0' AND s.extraction_output_id = o.extraction_output_id
                   WHERE o.id = NEW.observation_id) THEN
            PERFORM hc_reject('an extraction output''s candidates are stored before its S0 is taken');
        END IF;
        NEW.created_at := now();
        RETURN NEW;
    END $$
    """,
    # An event names an existing object of its output. The extraction's own 'proposed' events come before the output's
    # S0; every other event comes after it (the S0 rule in the docstring).
    """
    CREATE FUNCTION hc_evidence_state_event_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE output_id bigint;
            has_s0 boolean;
    BEGIN
        IF NEW.object_kind = 'observation' THEN
            SELECT extraction_output_id INTO output_id FROM candidate_observation WHERE id = NEW.object_id;
        ELSE
            SELECT o.extraction_output_id INTO output_id FROM extraction_link l
              JOIN candidate_observation o ON o.id = l.observation_id WHERE l.id = NEW.object_id;
        END IF;
        IF output_id IS NULL OR output_id <> NEW.extraction_output_id THEN
            PERFORM hc_reject('a state event names an existing observation or link of its extraction output');
        END IF;
        PERFORM 1 FROM extraction_output WHERE id = output_id FOR UPDATE;
        has_s0 := EXISTS (SELECT 1 FROM evidence_snapshot WHERE name = 'S0' AND extraction_output_id = output_id);
        IF NEW.state = 'proposed' AND NEW.by_rule = 'extraction' THEN
            IF has_s0 THEN
                PERFORM hc_reject('the extraction records its candidates before the output''s S0 is taken');
            END IF;
        ELSIF NOT has_s0 THEN
            PERFORM hc_reject('no other state event before the extraction output''s S0 is taken');
        END IF;
        NEW.at := now();
        RETURN NEW;
    END $$
    """,
    # A snapshot lists its event ids in ascending order with their hash (checked here). S0: exactly its output's events
    # at this time, every one the extraction's own 'proposed', every observation and link of the output among them, and
    # the output's raw hash. S1 and S2: events that exist.
    """
    CREATE FUNCTION hc_evidence_snapshot_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE ids bigint[];
    BEGIN
        IF NEW.event_ids IS NULL OR NEW.event_ids IS DISTINCT FROM
               (SELECT coalesce(array_agg(DISTINCT e ORDER BY e), '{}') FROM unnest(NEW.event_ids) e) THEN
            PERFORM hc_reject('a snapshot lists distinct event ids in ascending order');
        END IF;
        IF NEW.events_sha256 IS DISTINCT FROM
               encode(sha256(convert_to(array_to_string(NEW.event_ids, ','), 'UTF8')), 'hex') THEN
            PERFORM hc_reject('a snapshot''s events hash is the hash of its event ids');
        END IF;
        IF (SELECT count(*) FROM evidence_state_event WHERE id = ANY(NEW.event_ids))
               <> coalesce(array_length(NEW.event_ids, 1), 0) THEN
            PERFORM hc_reject('a snapshot lists existing state events');
        END IF;
        IF NEW.name = 'S0' THEN
            PERFORM 1 FROM extraction_output WHERE id = NEW.extraction_output_id FOR UPDATE;
            IF NEW.raw_sha256 IS DISTINCT FROM (SELECT raw_sha256 FROM extraction_output WHERE id = NEW.extraction_output_id) THEN
                PERFORM hc_reject('S0 carries its extraction output''s raw hash');
            END IF;
            SELECT coalesce(array_agg(id ORDER BY id), '{}') INTO ids FROM evidence_state_event
             WHERE extraction_output_id = NEW.extraction_output_id;
            IF ids IS DISTINCT FROM NEW.event_ids THEN
                PERFORM hc_reject('S0 lists exactly its extraction output''s state events');
            END IF;
            IF EXISTS (SELECT 1 FROM evidence_state_event WHERE id = ANY(ids)
                         AND NOT (state = 'proposed' AND by_rule = 'extraction')) THEN
                PERFORM hc_reject('S0 holds only the extraction''s own proposed events');
            END IF;
            IF EXISTS (SELECT 1 FROM candidate_observation o WHERE o.extraction_output_id = NEW.extraction_output_id
                         AND NOT EXISTS (SELECT 1 FROM evidence_state_event e WHERE e.id = ANY(ids)
                                           AND e.object_kind = 'observation' AND e.object_id = o.id))
               OR EXISTS (SELECT 1 FROM extraction_link l JOIN candidate_observation o ON o.id = l.observation_id
                          WHERE o.extraction_output_id = NEW.extraction_output_id
                            AND NOT EXISTS (SELECT 1 FROM evidence_state_event e WHERE e.id = ANY(ids)
                                              AND e.object_kind = 'link' AND e.object_id = l.id)) THEN
                PERFORM hc_reject('S0 holds a proposed event for every observation and link of its output');
            END IF;
        END IF;
        NEW.taken_at := now();
        RETURN NEW;
    END $$
    """,
    # Written in the transaction that ends the run, after the run's final update.
    """
    CREATE FUNCTION hc_run_stop_reason_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
    BEGIN
        IF s NOT IN ('completed', 'failed') THEN
            PERFORM hc_reject('a stop reason is written when the run ends');
        END IF;
        NEW.at := now();
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_annotation_file_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        NEW.loaded_at := now();
        RETURN NEW;
    END $$
    """,
]
FUNCTION_NAMES = ["hc_document_insert()", "hc_document_parse_insert()", "hc_search_log_insert()",
                  "hc_document_invocation_insert()", "hc_document_invocation_required()", "hc_extraction_output_insert()", "hc_candidate_observation_insert()",
                  "hc_provenance_matches(bigint, jsonb)", "hc_candidate_value_insert()", "hc_extraction_link_insert()",
                  "hc_evidence_state_event_insert()", "hc_evidence_snapshot_insert()", "hc_run_stop_reason_insert()",
                  "hc_annotation_file_insert()"]

NEW_TABLES = ["document", "document_parse", "search_log", "document_invocation", "extraction_output", "candidate_observation",
              "candidate_value", "extraction_link", "evidence_state_event", "evidence_snapshot", "run_stop_reason",
              "annotation_file", "annotation_row"]
APPEND_ONLY = NEW_TABLES
CHECKED = [(t, "INSERT", f"hc_{t}_insert", f"hc_{t}_insert") for t in
           ["document", "document_parse", "search_log", "document_invocation", "extraction_output", "candidate_observation",
            "candidate_value", "extraction_link", "evidence_state_event", "evidence_snapshot", "run_stop_reason",
            "annotation_file"]]
TRIGGERS = (
    [f"CREATE TRIGGER hc_{t}_append_only BEFORE UPDATE OR DELETE ON {t} "
     f"FOR EACH ROW EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} "
       f"FOR EACH STATEMENT EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER {t} BEFORE {event} ON {table} FOR EACH ROW EXECUTE FUNCTION {f}()"
       for table, event, t, f in CHECKED]
    + ["CREATE CONSTRAINT TRIGGER hc_agent_invocation_document_required AFTER INSERT ON agent_invocation "
       "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW WHEN (NEW.scope = 'document') "
       "EXECUTE FUNCTION hc_document_invocation_required()"]
)
CONSTRAINT_TRIGGERS = [("agent_invocation", "hc_agent_invocation_document_required")]


def _tables() -> None:
    op.create_table(
        'document',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('kind', sa.Text(), server_default=sa.text("'article'"), nullable=False),
        sa.Column('parent_document_id', sa.BigInteger(), nullable=True),
        sa.Column('doi', sa.Text(), nullable=False),
        sa.Column('doi_key', sa.Text(), nullable=False),
        sa.Column('oa_status', sa.Text(), nullable=True),
        sa.Column('oa_source', sa.Text(), nullable=False),
        sa.Column('oa_url', sa.Text(), nullable=True),
        sa.Column('license', sa.Text(), nullable=True),
        sa.Column('pdf', sa.LargeBinary(), nullable=False),
        sa.Column('pdf_sha256', sa.Text(), nullable=False),
        sa.Column('fetched_by', sa.Text(), nullable=False),
        sa.Column('by_hand', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(_in('kind', DOCUMENT_KINDS), name=ck('ck_document_kind')),
        sa.CheckConstraint("(kind = 'article') = (parent_document_id IS NULL)",
                           name=ck('ck_document_parent_unless_article')),
        sa.CheckConstraint(f"doi_key {DOI_KEY}", name=ck('ck_document_doi_key_format')),
        sa.CheckConstraint(_in('oa_source', OA_SOURCES), name=ck('ck_document_oa_source')),
        sa.CheckConstraint("by_hand = (oa_source = 'by_hand')", name=ck('ck_document_by_hand_source')),
        sa.CheckConstraint(f"octet_length(pdf) BETWEEN 5 AND {DOCUMENT_MAX_BYTES}", name=ck('ck_document_max_size')),
        sa.CheckConstraint("substring(pdf from 1 for 5) = '\\x255044462d'::bytea", name=ck('ck_document_is_pdf')),
        sa.CheckConstraint("pdf_sha256 = encode(sha256(pdf), 'hex')", name=ck('ck_document_sha256_matches_pdf')),
        sa.CheckConstraint(_named('fetched_by'), name=ck('ck_document_fetched_by_named')),
        sa.ForeignKeyConstraint(['parent_document_id'], ['document.id'], name=ck('fk_document_parent_document_id')),
        sa.PrimaryKeyConstraint('id', name=ck('pk_document')),
    )
    op.create_index('ix_document_doi_key', 'document', ['doi_key'])

    op.create_table(
        'document_parse',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('parser', sa.Text(), nullable=False),
        sa.Column('parser_version', sa.Text(), nullable=False),
        sa.Column('fallback_used', sa.Boolean(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('parsed', sa.Text(), nullable=True),
        sa.Column('parsed_sha256', sa.Text(), nullable=True),
        sa.Column('pages', sa.Integer(), nullable=True),
        sa.Column('tables_found', sa.Integer(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(_in('parser', PARSERS), name=ck('ck_document_parse_parser')),
        sa.CheckConstraint("length(parser_version) BETWEEN 1 AND 100", name=ck('ck_document_parse_parser_version')),
        sa.CheckConstraint(_in('status', PARSE_STATUSES), name=ck('ck_document_parse_status')),
        sa.CheckConstraint("status <> 'parsed' OR (parsed IS NOT NULL AND pages >= 1 AND tables_found >= 0 "
                           "AND failure_reason IS NULL)", name=ck('ck_document_parse_parsed_complete')),
        sa.CheckConstraint("status <> 'failed' OR (parsed IS NULL AND parsed_sha256 IS NULL AND failure_reason IS NOT NULL "
                           f"AND length(failure_reason) BETWEEN 1 AND {DETAIL_MAX})",
                           name=ck('ck_document_parse_failed_has_reason')),
        sa.CheckConstraint("parsed_sha256 IS NOT DISTINCT FROM encode(sha256(convert_to(parsed, 'UTF8')), 'hex')",
                           name=ck('ck_document_parse_sha256_matches_parsed')),
        sa.ForeignKeyConstraint(['document_id'], ['document.id'], name=ck('fk_document_parse_document_id')),
        sa.PrimaryKeyConstraint('id', name=ck('pk_document_parse')),
        sa.UniqueConstraint('id', 'parsed_sha256', name=ck('uq_document_parse_id_parsed_sha256')),
    )
    op.create_index('ix_document_parse_document_id', 'document_parse', ['document_id'])

    op.create_table(
        'search_log',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('doi_key', sa.Text(), nullable=True),
        sa.Column('document_id', sa.BigInteger(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('outcome', sa.Text(), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('actor', sa.Text(), nullable=False),
        sa.Column('by_hand', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.CheckConstraint(_in('action', SEARCH_ACTIONS), name=ck('ck_search_log_action')),
        sa.CheckConstraint(_in('outcome', SEARCH_OUTCOMES), name=ck('ck_search_log_outcome')),
        sa.CheckConstraint("by_hand = (action = 'fetch_by_hand')", name=ck('ck_search_log_by_hand_action')),
        sa.CheckConstraint(_named('actor'), name=ck('ck_search_log_actor_named')),
        sa.CheckConstraint(f"length(coalesce(detail, '')) <= {DETAIL_MAX} AND length(coalesce(url, '')) <= {DETAIL_MAX}",
                           name=ck('ck_search_log_bounded')),
        sa.CheckConstraint("http_status IS NULL OR http_status BETWEEN 100 AND 599",
                           name=ck('ck_search_log_http_status')),
        sa.ForeignKeyConstraint(['document_id'], ['document.id'], name=ck('fk_search_log_document_id')),
        sa.PrimaryKeyConstraint('id', name=ck('pk_search_log')),
    )
    op.create_index('ix_search_log_doi_key', 'search_log', ['doi_key'])

    op.create_table(
        'document_invocation',
        sa.Column('invocation_id', sa.BigInteger(), nullable=False),
        sa.Column('document_parse_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['invocation_id'], ['agent_invocation.id'], name=ck('fk_document_invocation_invocation_id')),
        sa.ForeignKeyConstraint(['document_parse_id'], ['document_parse.id'],
                                name=ck('fk_document_invocation_document_parse_id')),
        sa.PrimaryKeyConstraint('invocation_id', name=ck('pk_document_invocation')),
    )
    op.create_index('ix_document_invocation_document_parse_id', 'document_invocation', ['document_parse_id'])

    op.create_table(
        'extraction_output',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('document_parse_id', sa.BigInteger(), nullable=False),
        sa.Column('parse_sha256', sa.Text(), nullable=False),
        sa.Column('method', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('raw_output', sa.Text(), nullable=False),
        sa.Column('raw_sha256', sa.Text(), nullable=False),
        sa.Column('invocation_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("jsonb_typeof(method) = 'object' "
                           "AND method ?& array['method', 'name', 'version', 'prompt_version']",
                           name=ck('ck_extraction_output_method_shape')),
        sa.CheckConstraint(_in('status', EXTRACTION_STATUSES), name=ck('ck_extraction_output_status')),
        sa.CheckConstraint("raw_sha256 = encode(sha256(convert_to(raw_output, 'UTF8')), 'hex')",
                           name=ck('ck_extraction_output_sha256_matches_raw')),
        sa.ForeignKeyConstraint(['document_parse_id', 'parse_sha256'],
                                ['document_parse.id', 'document_parse.parsed_sha256'],
                                name='fk_extraction_output_document_parse'),
        sa.ForeignKeyConstraint(['invocation_id'], ['agent_invocation.id'],
                                name=ck('fk_extraction_output_invocation_id')),
        sa.PrimaryKeyConstraint('id', name=ck('pk_extraction_output')),
    )
    op.create_index('ix_extraction_output_document_parse_id', 'extraction_output', ['document_parse_id'])

    op.create_table(
        'candidate_observation',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('extraction_output_id', sa.BigInteger(), nullable=False),
        sa.Column('item_index', sa.Integer(), nullable=False),
        sa.Column('identity', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('identity_key', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("item_index >= 0", name=ck('ck_candidate_observation_item_index')),
        sa.CheckConstraint("jsonb_typeof(identity) = 'object'", name=ck('ck_candidate_observation_identity_object')),
        sa.CheckConstraint(f"identity_key {SHA256}", name=ck('ck_candidate_observation_identity_key_format')),
        sa.ForeignKeyConstraint(['extraction_output_id'], ['extraction_output.id'],
                                name=ck('fk_candidate_observation_extraction_output_id')),
        sa.PrimaryKeyConstraint('id', name=ck('pk_candidate_observation')),
        sa.UniqueConstraint('extraction_output_id', 'item_index',
                            name=ck('uq_candidate_observation_extraction_output_id_item_index')),
    )

    op.create_table(
        'candidate_value',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('observation_id', sa.BigInteger(), nullable=False),
        sa.Column('field', sa.Text(), nullable=False),
        sa.Column('value_text', sa.Text(), nullable=False),
        sa.Column('value_number', sa.Numeric(), nullable=True),
        sa.Column('unit', sa.Text(), nullable=True),
        sa.Column('definition', sa.Text(), nullable=True),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ambiguous', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('ambiguity_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(_in('field', VALUE_FIELDS), name=ck('ck_candidate_value_field')),
        sa.CheckConstraint(f"length(value_text) BETWEEN 1 AND {DETAIL_MAX}", name=ck('ck_candidate_value_value_text')),
        sa.CheckConstraint("value_number IS NULL OR (value_number < 'Infinity' AND value_number > '-Infinity')",
                           name=ck('ck_candidate_value_number_finite')),
        sa.CheckConstraint("provenance IS NOT NULL OR ambiguous", name=ck('ck_candidate_value_provenance_or_ambiguous')),
        sa.CheckConstraint(f"provenance IS NULL OR ({PROVENANCE_SHAPE})", name=ck('ck_candidate_value_provenance_shape')),
        sa.CheckConstraint(f"ambiguous = (ambiguity_note IS NOT NULL) AND length(coalesce(ambiguity_note, '')) <= "
                           f"{DETAIL_MAX}", name=ck('ck_candidate_value_ambiguity_noted')),
        sa.ForeignKeyConstraint(['observation_id'], ['candidate_observation.id'],
                                name=ck('fk_candidate_value_observation_id')),
        sa.PrimaryKeyConstraint('id', name=ck('pk_candidate_value')),
        sa.UniqueConstraint('observation_id', 'field', name=ck('uq_candidate_value_observation_id_field')),
        sa.UniqueConstraint('id', 'observation_id', name=ck('uq_candidate_value_id_observation_id')),
    )
    op.create_index('ix_candidate_value_observation_id', 'candidate_value', ['observation_id'])

    op.create_table(
        'extraction_link',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('observation_id', sa.BigInteger(), nullable=False),
        sa.Column('from_value_id', sa.BigInteger(), nullable=False),
        sa.Column('to_value_id', sa.BigInteger(), nullable=False),
        sa.Column('kind', sa.Text(), nullable=True),
        sa.Column('provenance', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ambiguous', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('ambiguity_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("from_value_id <> to_value_id", name=ck('ck_extraction_link_two_values')),
        sa.CheckConstraint(f"kind IS NULL OR {_in('kind', LINK_KINDS)}", name=ck('ck_extraction_link_kind')),
        sa.CheckConstraint("(provenance IS NOT NULL AND kind IS NOT NULL) OR ambiguous",
                           name=ck('ck_extraction_link_provenance_or_ambiguous')),
        sa.CheckConstraint(f"provenance IS NULL OR ({PROVENANCE_SHAPE})", name=ck('ck_extraction_link_provenance_shape')),
        sa.CheckConstraint(f"ambiguous = (ambiguity_note IS NOT NULL) AND length(coalesce(ambiguity_note, '')) <= "
                           f"{DETAIL_MAX}", name=ck('ck_extraction_link_ambiguity_noted')),
        sa.ForeignKeyConstraint(['observation_id'], ['candidate_observation.id'],
                                name=ck('fk_extraction_link_observation_id')),
        sa.ForeignKeyConstraint(['from_value_id', 'observation_id'],
                                ['candidate_value.id', 'candidate_value.observation_id'],
                                name='fk_extraction_link_from_value'),
        sa.ForeignKeyConstraint(['to_value_id', 'observation_id'],
                                ['candidate_value.id', 'candidate_value.observation_id'],
                                name='fk_extraction_link_to_value'),
        sa.PrimaryKeyConstraint('id', name=ck('pk_extraction_link')),
        sa.UniqueConstraint('from_value_id', 'to_value_id', name=ck('uq_extraction_link_from_value_id_to_value_id')),
    )
    op.create_index('ix_extraction_link_observation_id', 'extraction_link', ['observation_id'])

    op.create_table(
        'evidence_state_event',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('object_kind', sa.Text(), nullable=False),
        sa.Column('object_id', sa.BigInteger(), nullable=False),
        sa.Column('extraction_output_id', sa.BigInteger(), nullable=False),
        sa.Column('state', sa.Text(), nullable=False),
        sa.Column('by_rule', sa.Text(), nullable=True),
        sa.Column('by_person', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.CheckConstraint(_in('object_kind', STATE_OBJECTS), name=ck('ck_evidence_state_event_object_kind')),
        sa.CheckConstraint(_in('state', EVIDENCE_STATES), name=ck('ck_evidence_state_event_state')),
        sa.CheckConstraint("(by_rule IS NULL) <> (by_person IS NULL)", name=ck('ck_evidence_state_event_rule_or_person')),
        sa.CheckConstraint("by_rule IS NULL OR by_rule ~ '^[A-Za-z0-9_-]{1,40}$'",
                           name=ck('ck_evidence_state_event_rule_format')),
        sa.CheckConstraint(_named('by_person', nullable=True), name=ck('ck_evidence_state_event_person_named')),
        sa.CheckConstraint(f"length(coalesce(reason, '')) <= {DETAIL_MAX}", name=ck('ck_evidence_state_event_bounded')),
        sa.ForeignKeyConstraint(['extraction_output_id'], ['extraction_output.id'],
                                name=ck('fk_evidence_state_event_extraction_output_id')),
        sa.PrimaryKeyConstraint('id', name=ck('pk_evidence_state_event')),
    )
    op.create_index('ix_evidence_state_event_object', 'evidence_state_event', ['object_kind', 'object_id'])

    op.create_table(
        'evidence_snapshot',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('extraction_output_id', sa.BigInteger(), nullable=True),
        sa.Column('raw_sha256', sa.Text(), nullable=True),
        sa.Column('taken_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('event_ids', postgresql.ARRAY(sa.BigInteger()), nullable=False),
        sa.Column('events_sha256', sa.Text(), nullable=False),
        sa.Column('taken_by', sa.Text(), nullable=False),
        sa.CheckConstraint(_in('name', SNAPSHOT_NAMES), name=ck('ck_evidence_snapshot_name')),
        sa.CheckConstraint("(name = 'S0') = (extraction_output_id IS NOT NULL AND raw_sha256 IS NOT NULL)",
                           name=ck('ck_evidence_snapshot_s0_per_output')),
        sa.CheckConstraint(f"raw_sha256 IS NULL OR raw_sha256 {SHA256}", name=ck('ck_evidence_snapshot_raw_sha256_format')),
        sa.CheckConstraint(f"events_sha256 {SHA256}", name=ck('ck_evidence_snapshot_events_sha256_format')),
        sa.CheckConstraint(_named('taken_by'), name=ck('ck_evidence_snapshot_taken_by_named')),
        sa.ForeignKeyConstraint(['extraction_output_id'], ['extraction_output.id'],
                                name=ck('fk_evidence_snapshot_extraction_output_id')),
        sa.PrimaryKeyConstraint('id', name=ck('pk_evidence_snapshot')),
    )
    op.create_index('uq_evidence_snapshot_s0', 'evidence_snapshot', ['extraction_output_id'], unique=True,
                    postgresql_where=sa.text("name = 'S0'"))

    op.create_table(
        'run_stop_reason',
        sa.Column('run_id', sa.BigInteger(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(_in('reason', STOP_REASONS), name=ck('ck_run_stop_reason_reason')),
        sa.CheckConstraint(f"length(coalesce(detail, '')) <= {DETAIL_MAX}", name=ck('ck_run_stop_reason_bounded')),
        sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=ck('fk_run_stop_reason_run_id')),
        sa.PrimaryKeyConstraint('run_id', name=ck('pk_run_stop_reason')),
    )

    op.create_table(
        'annotation_file',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('filename', sa.Text(), nullable=False),
        sa.Column('content', sa.LargeBinary(), nullable=False),
        sa.Column('sha256', sa.Text(), nullable=False),
        sa.Column('template_version', sa.Text(), nullable=False),
        sa.Column('loaded_by', sa.Text(), nullable=False),
        sa.Column('loaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(f"octet_length(content) BETWEEN 1 AND {MAX_FILE_BYTES}", name=ck('ck_annotation_file_max_size')),
        sa.CheckConstraint("sha256 = encode(sha256(content), 'hex')", name=ck('ck_annotation_file_sha256_matches_content')),
        sa.CheckConstraint("filename ~ '^[A-Za-z0-9][A-Za-z0-9._ -]{0,199}[.](xlsx|csv)$'",
                           name=ck('ck_annotation_file_filename')),
        sa.CheckConstraint("length(template_version) BETWEEN 1 AND 40", name=ck('ck_annotation_file_template_version')),
        sa.CheckConstraint(_named('loaded_by'), name=ck('ck_annotation_file_loaded_by_named')),
        sa.PrimaryKeyConstraint('id', name=ck('pk_annotation_file')),
        sa.UniqueConstraint('sha256', name=ck('uq_annotation_file_sha256')),
    )

    op.create_table(
        'annotation_row',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('annotation_file_id', sa.BigInteger(), nullable=False),
        sa.Column('row_number', sa.Integer(), nullable=False),
        sa.Column('doi_key', sa.Text(), nullable=False),
        sa.Column('identity', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('identity_key', sa.Text(), nullable=False),
        sa.Column('cells', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('annotator', sa.Text(), nullable=False),
        sa.Column('minutes', sa.Integer(), nullable=True),
        sa.CheckConstraint("row_number >= 1", name=ck('ck_annotation_row_row_number')),
        sa.CheckConstraint(f"doi_key {DOI_KEY}", name=ck('ck_annotation_row_doi_key_format')),
        sa.CheckConstraint("jsonb_typeof(identity) = 'object' AND jsonb_typeof(cells) = 'object'",
                           name=ck('ck_annotation_row_objects')),
        sa.CheckConstraint(f"identity_key {SHA256}", name=ck('ck_annotation_row_identity_key_format')),
        sa.CheckConstraint(_named('annotator'), name=ck('ck_annotation_row_annotator_named')),
        sa.CheckConstraint("minutes IS NULL OR minutes >= 0", name=ck('ck_annotation_row_minutes')),
        sa.ForeignKeyConstraint(['annotation_file_id'], ['annotation_file.id'],
                                name=ck('fk_annotation_row_annotation_file_id')),
        sa.PrimaryKeyConstraint('id', name=ck('pk_annotation_row')),
        sa.UniqueConstraint('annotation_file_id', 'row_number',
                            name=ck('uq_annotation_row_annotation_file_id_row_number')),
    )


def _replace_check(table: str, name: str, condition: str) -> None:
    op.drop_constraint(op.f(name), table, type_='check')
    op.create_check_constraint(op.f(name), table, condition)


def upgrade() -> None:
    _tables()
    for table, name, template in ROLE_CHECKS:
        _replace_check(table, name, template.format(_list(ROLES)))
    _replace_check('agent_invocation', 'ck_agent_invocation_scope', _in('scope', INVOCATION_SCOPES))
    _replace_check('agent_invocation', 'ck_agent_invocation_shape', SHAPE_0010)
    for f in FUNCTIONS:
        op.execute(f)
    for t in TRIGGERS:
        op.execute(t)
    for _, new in REPLACED:
        op.execute(new)


# Locked before anything is looked at, in the downgrade's own transaction, so a row inserted but not yet committed is
# waited for and seen, never dropped unseen (as 0009).
LOCKED = NEW_TABLES + ["agent_invocation", "agent_setting", "stage_result", "model_call"]
LOCK = "LOCK TABLE " + ", ".join(LOCKED) + " IN ACCESS EXCLUSIVE MODE"
IN_USE = (
    "DO $$\nBEGIN\n    IF "
    + "\n       OR ".join(f"EXISTS (SELECT 1 FROM {t})" for t in NEW_TABLES)
    + f"\n       OR EXISTS (SELECT 1 FROM agent_invocation WHERE scope = 'document' OR role IN {_list(PILOT_ROLES)})"
    + "".join(f"\n       OR EXISTS (SELECT 1 FROM {t} WHERE role IN {_list(PILOT_ROLES)})"
              for t in ("agent_setting", "stage_result", "model_call"))
    + " THEN\n        RAISE EXCEPTION 'hypocurate: migration 0010 is in use (documents, extraction, states, snapshots, "
      "annotations, or the document scope or pilot roles); not downgraded';\n    END IF;\nEND $$"
)


def downgrade() -> None:
    op.execute(LOCK)
    op.execute(IN_USE)
    for old, _ in REPLACED:
        op.execute(old)
    _replace_check('agent_invocation', 'ck_agent_invocation_shape', SHAPE_0005)
    _replace_check('agent_invocation', 'ck_agent_invocation_scope', SCOPE_0005)
    for table, name, template in ROLE_CHECKS:
        _replace_check(table, name, template.format(_list(SPRINT1_ROLES)))
    for table, trigger in CONSTRAINT_TRIGGERS:
        op.execute(f"DROP TRIGGER {trigger} ON {table}")
    for t in reversed(NEW_TABLES):
        op.drop_table(t)
    for f in FUNCTION_NAMES:
        op.execute(f"DROP FUNCTION {f}")
