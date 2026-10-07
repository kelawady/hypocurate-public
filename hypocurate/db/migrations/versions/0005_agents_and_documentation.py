"""The agents' records and the source documentation (build step 8a).

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-06

Approved by the owner on 2026-10-06 (step 8a plan), subject to the second-model review before
merging; changed after that review (owner, 2026-10-07). Not purely additive: 0001 to 0004 are
untouched as files, but this migration replaces two of 0001's trigger functions (each keeps every
check of 0001 unchanged and in the same order, and adds new checks after them), replaces source_file's
path rule under the same name, and makes model_call.run_id and stage_result_id nullable. That last
change is safe because the live database holds no model call (step 8a summary); the downgrade
refuses while any row uses what 0005 adds.

source_file (owner, Q1: documentation frozen into the source version):
- `role`: 'data' (default; what every earlier file is), 'documentation' or 'curation'. Each role
  has its own path rule, so a path tells its role and the files digest (sorted paths and hashes,
  unchanged) stays unambiguous: data `<name>.csv|.xlsx` (0001's rule), documentation
  `docs/<name>.tex|.xml|.md|.txt`, curation exactly `curation.json`.

agent_invocation (one invocation record per agent call; step 5 re-check):
- `scope` 'run' or 'registration'. A run invocation names its run and stage result, and its
  (run, role, agent setting) must be one recorded at dispatch (`run_agent_setting`); its role is
  never the Curator's (the Curator never runs within a run; review finding 6). A registration
  invocation names a sealed source version, its role is the Curator's, and its agent setting is a
  Curator setting. The dispatcher (`bind_invocation`) reads run or version, role,
  setting and source from this one row.

model_call:
- `invocation_id`: required on every new call (by the insert trigger; the live database has no
  model call). `run_id` and `stage_result_id` may be NULL, exactly for a registration
  invocation's calls. The run rules of 0001 are unchanged for run calls; a registration call is
  recorded while its source version is sealed and finished exactly once, with the same
  immutability rules. The month view already counts every call.

curator_proposal, curator_decision (owner, Q2):
- a proposal per field per invocation, either 'proposed' (it passed the checks of
  `pipeline.agents.quotes`, which the database applies again itself: the quote occurs in the
  documentation file it names after collapsing runs of whitespace, beginning and ending at a word
  boundary; it is 30 to 600 characters; the value has the field's type and is in its vocabulary;
  the stored term is a listed term of that value (of every part of a microstructure, each of which
  must occur) and occurs in the quote as a whole word; a test condition's quote holds a testing word;
  a test temperature's term is a complete number equal to the value, followed by a Celsius unit,
  never part of a larger number or an end of a range;
  nothing it needs is NULL, and no value is JSON null) or 'refused' with a code. Append-only. The
  database does not check the line number (code computes it; a curation file is checked again,
  line included, before it is sealed or applied).
- one decision per proposal, 'accepted' or 'rejected', by a named person, at the database's time;
  only a 'proposed' proposal can be decided. Append-only.

Works with the previous release's code: that code inserts source files without a role (they are
data files and get the default), writes no model call, invocation, proposal or decision.

Downgrade refuses while any row uses what 0005 adds (a documentation or curation file, an
invocation, a model call with an invocation, a proposal, a decision), then restores 0001's
functions and constraints exactly.

Rules for every migration (README, "Database migrations"): it runs inside the one upgrade
transaction; it keeps working with the previous release's code; and it has a downgrade.
"""
import re

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None

ROLES = "('planner', 'curator', 'critic', 'analyst', 'commentator')"
# The fields the Curator may propose values for (owner, Q2): the conditions a table may lack.
CURATION_FIELDS = ('test_type', 'phase_class', 'test_temperature', 'test_temperature_band', 'microstructure')
# A proposal's quote, after collapsing runs of whitespace (the same normalization as the code's).
QUOTE_MIN, QUOTE_MAX = 30, 600
# The code's lists (pipeline.agents.quotes), copied here so the migration does not change when the
# code does; tests/test_migrations_step8a.py checks that they are equal.
CURATOR_TERMS = (
    ('test_type', 'tension', 'tensile'),
    ('test_type', 'tension', 'tension'),
    ('test_type', 'compression', 'compressive'),
    ('test_type', 'compression', 'compression'),
    ('phase_class', 'FCC', 'FCC'),
    ('phase_class', 'FCC', 'face-centred cubic'),
    ('phase_class', 'FCC', 'face-centred-cubic'),
    ('phase_class', 'FCC', 'face-centered cubic'),
    ('phase_class', 'FCC', 'face-centered-cubic'),
    ('phase_class', 'FCC', 'face centred cubic'),
    ('phase_class', 'FCC', 'face centred-cubic'),
    ('phase_class', 'FCC', 'face centered cubic'),
    ('phase_class', 'FCC', 'face centered-cubic'),
    ('phase_class', 'BCC', 'BCC'),
    ('phase_class', 'BCC', 'body-centred cubic'),
    ('phase_class', 'BCC', 'body-centred-cubic'),
    ('phase_class', 'BCC', 'body-centered cubic'),
    ('phase_class', 'BCC', 'body-centered-cubic'),
    ('phase_class', 'BCC', 'body centred cubic'),
    ('phase_class', 'BCC', 'body centred-cubic'),
    ('phase_class', 'BCC', 'body centered cubic'),
    ('phase_class', 'BCC', 'body centered-cubic'),
    ('test_temperature_band', 'room temperature', 'room temperature'),
    ('test_temperature_band', 'room temperature', 'room-temperature'),
    ('test_temperature_band', 'room temperature', 'ambient temperature'),
    ('test_temperature_band', 'elevated', 'elevated temperature'),
    ('test_temperature_band', 'elevated', 'high temperature'),
    ('test_temperature_band', 'elevated', 'high-temperature'),
    ('test_temperature_band', 'cryogenic', 'cryogenic'),
    ('test_temperature_band', 'cryogenic', 'liquid nitrogen'),
    ('test_temperature_band', 'cryogenic', 'liquid helium'),
    ('test_temperature_band', 'cryogenic', '77 K'),
    ('microstructure', 'FCC', 'FCC'),
    ('microstructure', 'BCC', 'BCC'),
    ('microstructure', 'B2', 'B2'),
    ('microstructure', 'HCP', 'HCP'),
    ('microstructure', 'L12', 'L12'),
    ('microstructure', 'Laves', 'Laves'),
)
CASE_SENSITIVE_TERMS = ('B2', 'L12')
TESTING_WORDS = ('test', 'tests', 'tested', 'testing', 'loaded', 'loading', 'strain rate')
EXCLUDED_PHRASES = ('ultimate tensile strength', 'ultimate tensile strengths')
# Every listed text is letters, digits, spaces and hyphens, so it is used in a regular expression as it is.
assert all(re.fullmatch(r"[A-Za-z0-9 -]+", t) for t in
           [t for _, _, t in CURATOR_TERMS] + list(TESTING_WORDS) + list(EXCLUDED_PHRASES))


def _texts(items) -> str:
    return "ARRAY[" + ", ".join(f"'{t}'" for t in items) + "]::text[]"


_TERMS_SQL = "(VALUES " + ", ".join(f"('{f}', '{v}', '{t}')" for f, v, t in CURATOR_TERMS) + ") AS t(field, value, term)"
_B = "(?<![A-Za-z0-9_])"  # a word boundary before and after (ASCII word characters, as the code's)
_A = "(?![A-Za-z0-9_])"

# Whether a quote occurs in a document, both with runs of whitespace collapsed, beginning and ending
# at a word boundary (the code's `quotes.locate`, without the line).
QUOTE_OCCURS = r"""
    CREATE FUNCTION hc_quote_occurs(p_document text, p_quote text) RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $$
    DECLARE t text := regexp_replace(p_document, '\s+', ' ', 'g');
            q text := btrim(regexp_replace(p_quote, '\s+', ' ', 'g'));
            off int := 0; pos int; s int; e int;
    BEGIN
        IF t IS NULL OR q IS NULL OR q = '' THEN
            RETURN false;
        END IF;
        LOOP
            pos := strpos(substr(t, off + 1), q);
            EXIT WHEN pos = 0;
            s := off + pos;
            e := s + length(q) - 1;
            IF NOT (s > 1 AND substr(t, s - 1, 1) ~ '[A-Za-z0-9_]' AND substr(t, s, 1) ~ '[A-Za-z0-9_]')
               AND NOT (e < length(t) AND substr(t, e, 1) ~ '[A-Za-z0-9_]' AND substr(t, e + 1, 1) ~ '[A-Za-z0-9_]') THEN
                RETURN true;
            END IF;
            off := s;
        END LOOP;
        RETURN false;
    END $$
    """

# Whether a proposal's value has its field's type and vocabulary and its term is a listed term of that
# value that occurs in the quote (the code's `quotes.check`, steps 1, 4 and 5).
TERM_OK = r"""
    CREATE FUNCTION hc_curator_term_ok(p_field text, p_value jsonb, p_quote text, p_term text)
    RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $$
    DECLARE q text; collapsed text; v text; n numeric; part text; phrase text; pattern text;
            range_left constant text := '(?<![0-9](?:[ ~]*°C|[}][{]\\degreeCelsius[}])? ?(?:[Tt]o|[-−–]+) ?)';
            range_right constant text := '(?! ?(?:[-−–]|[Tt]o ) ?[-+−–]?(?:[0-9]|\\SI))';
    BEGIN
        IF p_field IS NULL OR p_value IS NULL OR p_quote IS NULL OR p_term IS NULL THEN
            RETURN false;
        END IF;
        collapsed := btrim(regexp_replace(p_quote, '\s+', ' ', 'g'));
        q := collapsed;
        FOREACH phrase IN ARRAY __EXCLUDED__ LOOP
            q := regexp_replace(q, '__B__' || phrase || '__A__', ' ', 'gi');
        END LOOP;
        IF p_field IN ('test_type', 'test_temperature_band', 'test_temperature') AND NOT EXISTS (
                SELECT 1 FROM unnest(__TESTING__) w WHERE collapsed ~* ('__B__' || w || '__A__')) THEN
            RETURN false;
        END IF;
        IF p_field = 'test_temperature' THEN
            IF jsonb_typeof(p_value) <> 'number' THEN
                RETURN false;
            END IF;
            n := (p_value #>> '{}')::numeric;
            IF n < -273.15 OR n > 3000 OR p_term !~ '^[-+−–]?(0|[1-9][0-9]*)([.][0-9]+)?$'
               OR translate(p_term, '−–', '--')::numeric <> n THEN
                RETURN false;
            END IF;
            pattern := replace(replace(p_term, '.', '[.]'), '+', '[+]');
            -- Never the tail of a larger number ('1,025', '1 025') or an end of a range ('20 - 25',
            -- '20–25', '20 to 25', '20 °C to 25 °C'), as the code's quotes._PLAIN, _LATEX and _RANGE_LEFT.
            RETURN q ~ ('(?<![A-Za-z0-9_.+−–-])(?<![0-9],)' || range_left || pattern
                        || '(?![.,]?[0-9])[ ~]*°C' || range_right)
                OR q ~ ('(?<![0-9],)' || range_left || '\\SI[{]' || pattern || '[}][{]\\degreeCelsius[}]'
                        || range_right);
        END IF;
        IF jsonb_typeof(p_value) <> 'string' THEN
            RETURN false;
        END IF;
        v := p_value #>> '{}';
        IF p_field = 'microstructure' THEN
            FOREACH part IN ARRAY string_to_array(v, '+') LOOP
                IF NOT EXISTS (SELECT 1 FROM __TERMS__ WHERE t.field = 'microstructure' AND t.value = part
                               AND hc_term_occurs(t.term, q)) THEN
                    RETURN false;
                END IF;
            END LOOP;
            RETURN EXISTS (SELECT 1 FROM __TERMS__ WHERE t.field = 'microstructure'
                           AND t.value = ANY (string_to_array(v, '+')) AND t.term = p_term);
        END IF;
        RETURN EXISTS (SELECT 1 FROM __TERMS__ WHERE t.field = p_field AND t.value = v AND t.term = p_term
                       AND hc_term_occurs(t.term, q));
    END $$
    """.replace("__EXCLUDED__", _texts(EXCLUDED_PHRASES)).replace("__TESTING__", _texts(TESTING_WORDS)) \
       .replace("__TERMS__", _TERMS_SQL).replace("__B__", _B).replace("__A__", _A)

# A listed term as a whole word of the (collapsed) quote; case-insensitive except CASE_SENSITIVE_TERMS.
TERM_OCCURS = r"""
    CREATE FUNCTION hc_term_occurs(p_term text, p_text text) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
        SELECT CASE WHEN p_term = ANY (__SENSITIVE__) THEN p_text ~ ('__B__' || p_term || '__A__')
                    ELSE p_text ~* ('__B__' || p_term || '__A__') END
    $$
    """.replace("__SENSITIVE__", _texts(CASE_SENSITIVE_TERMS)).replace("__B__", _B).replace("__A__", _A)
CHECK_FUNCTIONS = [QUOTE_OCCURS, TERM_OCCURS, TERM_OK]
CHECK_FUNCTION_NAMES = ["hc_curator_term_ok(text, jsonb, text, text)", "hc_term_occurs(text, text)",
                        "hc_quote_occurs(text, text)"]
STORED_TEXT_MAX = 4000  # any status: what the model wrote is kept, bounded

# 0001's path rule, and the rule by role that replaces it under the same name (so a path tells its
# role, and the files digest stays unambiguous).
PATH_RULE_0001 = "path ~ '^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$'"
PATH_RULE_0005 = (
    "(role = 'data' AND path ~ '^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$' AND path !~ '^documentation/') "
    "OR (role = 'documentation' AND path ~ '^documentation/[A-Za-z0-9][A-Za-z0-9._-]*[.](tex|xml|md|txt)$') "
    "OR (role = 'curation' AND path = 'curation.json')")

# 0001's functions, verbatim (restored by the downgrade).
MODEL_CALL_INSERT_0001 = """
    CREATE OR REPLACE FUNCTION hc_model_call_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
    BEGIN
        IF NOT (s = 'running' OR s = 'completed' AND NEW.role = 'commentator'
                AND (SELECT stage FROM stage_result WHERE id = NEW.stage_result_id) = 'commentator') THEN
            PERFORM hc_reject('a model call is made while the run is running; after completion only the commentator''s');
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
MODEL_CALL_UPDATE_0001 = """
    CREATE OR REPLACE FUNCTION hc_model_call_update() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(OLD.run_id), '');
    BEGIN
        IF NOT (s = 'running' OR s = 'completed' AND OLD.role = 'commentator') THEN
            PERFORM hc_reject('a model call is finished only while its run is running');
        END IF;
        IF OLD.status <> 'started' OR NEW.status = 'started' THEN
            PERFORM hc_reject('a model call is finished exactly once');
        END IF;
        IF NEW.run_id <> OLD.run_id OR NEW.stage_result_id <> OLD.stage_result_id OR NEW.role <> OLD.role
           OR NEW.model <> OLD.model OR NEW.price_table_version <> OLD.price_table_version
           OR NEW.max_cost <> OLD.max_cost OR NEW.started_at <> OLD.started_at THEN
            PERFORM hc_reject('what was recorded before the request cannot change');
        END IF;
        IF NEW.finished_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('finished_at is set by the database');
        END IF;
        RETURN NEW;
    END $$
    """

# A registration call (no run) is checked first; a run call goes through 0001's checks unchanged and
# then must agree with its invocation. That every call names an invocation is a CHECK
# (`ck_model_call_with_invocation`), named to sort after 0001's checks.
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
MODEL_CALL_UPDATE_0005 = """
    CREATE OR REPLACE FUNCTION hc_model_call_update() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(OLD.run_id), '');
    BEGIN
        IF OLD.run_id IS NOT NULL THEN
            IF NOT (s = 'running' OR s = 'completed' AND OLD.role = 'commentator') THEN
                PERFORM hc_reject('a model call is finished only while its run is running');
            END IF;
        END IF;
        IF OLD.status <> 'started' OR NEW.status = 'started' THEN
            PERFORM hc_reject('a model call is finished exactly once');
        END IF;
        IF NEW.run_id <> OLD.run_id OR NEW.stage_result_id <> OLD.stage_result_id OR NEW.role <> OLD.role
           OR NEW.model <> OLD.model OR NEW.price_table_version <> OLD.price_table_version
           OR NEW.max_cost <> OLD.max_cost OR NEW.started_at <> OLD.started_at THEN
            PERFORM hc_reject('what was recorded before the request cannot change');
        END IF;
        IF NEW.run_id IS DISTINCT FROM OLD.run_id OR NEW.stage_result_id IS DISTINCT FROM OLD.stage_result_id
           OR NEW.invocation_id IS DISTINCT FROM OLD.invocation_id THEN
            PERFORM hc_reject('what was recorded before the request cannot change');
        END IF;
        IF NEW.finished_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('finished_at is set by the database');
        END IF;
        RETURN NEW;
    END $$
    """

FUNCTIONS = [
    # An invocation is recorded once, before its calls: a run invocation under the run rule of a model
    # call, for a running stage of that run with the same role; a registration invocation for a sealed
    # version.
    """
    CREATE FUNCTION hc_agent_invocation_insert() RETURNS trigger LANGUAGE plpgsql AS $$
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
    """,
    # A proposal belongs to a registration invocation of the Curator and to that invocation's
    # version. A proposal that passed the checks quotes a passage the database finds in the
    # documentation file it names (runs of whitespace collapsed on both sides, at word boundaries).
    """
    CREATE FUNCTION hc_curator_proposal_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE inv agent_invocation;
    BEGIN
        SELECT * INTO inv FROM agent_invocation WHERE id = NEW.invocation_id;
        IF inv.scope IS DISTINCT FROM 'registration' OR inv.role IS DISTINCT FROM 'curator' THEN
            PERFORM hc_reject('a proposal comes from a registration invocation of the curator');
        END IF;
        IF NEW.source_version_id IS DISTINCT FROM inv.source_version_id THEN
            PERFORM hc_reject('a proposal is for its invocation''s source version');
        END IF;
        -- (A missing quote or document is refused by ck_curator_proposal_proposed_complete.)
        IF NEW.status = 'proposed' AND NEW.quote IS NOT NULL AND NEW.document_path IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM source_file f WHERE f.source_version_id = NEW.source_version_id
                  AND f.role = 'documentation' AND f.path = NEW.document_path
                  AND hc_quote_occurs(convert_from(f.content, 'UTF8'), NEW.quote)) THEN
            PERFORM hc_reject('a proposal''s quote must occur in the documentation file it names');
        END IF;
        NEW.created_at := now();
        RETURN NEW;
    END $$
    """,
    # One decision per proposal (unique), by a named person, at the database's time; only a
    # proposal that passed the checks can be decided.
    """
    CREATE FUNCTION hc_curator_decision_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF (SELECT status FROM curator_proposal WHERE id = NEW.proposal_id) IS DISTINCT FROM 'proposed' THEN
            PERFORM hc_reject('only a proposal that passed the checks can be accepted or rejected');
        END IF;
        NEW.decided_at := now();
        RETURN NEW;
    END $$
    """,
]
FUNCTION_NAMES = ["hc_agent_invocation_insert()", "hc_curator_proposal_insert()", "hc_curator_decision_insert()"]

APPEND_ONLY = ["agent_invocation", "curator_proposal", "curator_decision"]
# (table, event, function)
CHECKED = [
    ("agent_invocation", "INSERT", "hc_agent_invocation_insert"),
    ("curator_proposal", "INSERT", "hc_curator_proposal_insert"),
    ("curator_decision", "INSERT", "hc_curator_decision_insert"),
]
TRIGGERS = (
    [f"CREATE TRIGGER hc_{t}_append_only BEFORE UPDATE OR DELETE ON {t} "
     f"FOR EACH ROW EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} "
       f"FOR EACH STATEMENT EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER {f} BEFORE {event} ON {t} FOR EACH ROW EXECUTE FUNCTION {f}()" for t, event, f in CHECKED]
)


def upgrade() -> None:
    # source_file: a role per file, and the path rule by role (same name as 0001's rule).
    op.add_column('source_file', sa.Column('role', sa.Text(), server_default=sa.text("'data'"), nullable=False))
    op.drop_constraint(op.f('ck_source_file_safe_data_file_path'), 'source_file', type_='check')
    op.create_check_constraint(op.f('ck_source_file_safe_data_file_path'), 'source_file', PATH_RULE_0005)

    # The target of an invocation's (run, role, setting).
    op.create_unique_constraint(op.f('uq_run_agent_setting_run_id_role_agent_setting_id'), 'run_agent_setting',
                                ['run_id', 'role', 'agent_setting_id'])

    op.create_table(
        'agent_invocation',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('scope', sa.Text(), nullable=False),
        sa.Column('run_id', sa.BigInteger(), nullable=True),
        sa.Column('stage_result_id', sa.BigInteger(), nullable=True),
        sa.Column('source_version_id', sa.BigInteger(), nullable=True),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('agent_setting_id', sa.BigInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("scope IN ('run', 'registration')", name=op.f('ck_agent_invocation_scope')),
        sa.CheckConstraint(f"role IN {ROLES}", name=op.f('ck_agent_invocation_role')),
        sa.CheckConstraint(
            "(scope = 'run' AND run_id IS NOT NULL AND stage_result_id IS NOT NULL AND source_version_id IS NULL "
            "AND role <> 'curator') "
            "OR (scope = 'registration' AND run_id IS NULL AND stage_result_id IS NULL "
            "AND source_version_id IS NOT NULL AND role = 'curator')", name=op.f('ck_agent_invocation_shape')),
        sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_agent_invocation_run_id')),
        sa.ForeignKeyConstraint(['source_version_id'], ['source_version.id'],
                                name=op.f('fk_agent_invocation_source_version_id')),
        sa.ForeignKeyConstraint(['agent_setting_id', 'role'], ['agent_setting.id', 'agent_setting.role'],
                                name='fk_agent_invocation_agent_setting'),
        sa.ForeignKeyConstraint(['stage_result_id', 'run_id'], ['stage_result.id', 'stage_result.run_id'],
                                name='fk_agent_invocation_stage_result'),
        sa.ForeignKeyConstraint(['run_id', 'role', 'agent_setting_id'],
                                ['run_agent_setting.run_id', 'run_agent_setting.role',
                                 'run_agent_setting.agent_setting_id'],
                                name='fk_agent_invocation_run_agent_setting'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_agent_invocation')),
    )
    op.create_index('ix_agent_invocation_run_id', 'agent_invocation', ['run_id'], unique=False)

    # model_call: owned by an invocation; run and stage only for a run invocation's calls.
    op.add_column('model_call', sa.Column('invocation_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key(op.f('fk_model_call_invocation_id'), 'model_call', 'agent_invocation',
                          ['invocation_id'], ['id'])
    op.create_index('ix_model_call_invocation_id', 'model_call', ['invocation_id'], unique=False)
    op.alter_column('model_call', 'run_id', existing_type=sa.BigInteger(), nullable=True)
    op.alter_column('model_call', 'stage_result_id', existing_type=sa.BigInteger(), nullable=True)
    op.create_check_constraint(op.f('ck_model_call_run_with_stage'), 'model_call',
                               "(run_id IS NULL) = (stage_result_id IS NULL)")
    op.create_check_constraint(op.f('ck_model_call_with_invocation'), 'model_call', "invocation_id IS NOT NULL")

    for f in CHECK_FUNCTIONS:  # used by curator_proposal's checks and trigger
        op.execute(f)
    op.create_table(
        'curator_proposal',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('invocation_id', sa.BigInteger(), nullable=False),
        sa.Column('source_version_id', sa.BigInteger(), nullable=False),
        sa.Column('field', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quote', sa.Text(), nullable=True),
        sa.Column('document_path', sa.Text(), nullable=True),
        sa.Column('line', sa.Integer(), nullable=True),
        sa.Column('term', sa.Text(), nullable=True),
        sa.Column('refusal_code', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("field IN (" + ", ".join(f"'{f}'" for f in CURATION_FIELDS) + ")",
                           name=op.f('ck_curator_proposal_field')),
        sa.CheckConstraint("status IN ('proposed', 'refused', 'not_stated')", name=op.f('ck_curator_proposal_status')),
        # Every part a passed proposal needs, non-NULL (so the check can never be UNKNOWN, which a CHECK
        # accepts), and its value and term as the code's checks require.
        sa.CheckConstraint(
            f"status <> 'proposed' OR coalesce(value IS NOT NULL AND quote IS NOT NULL AND document_path IS NOT NULL "
            f"AND line IS NOT NULL AND term IS NOT NULL AND line >= 1 "
            f"AND length(btrim(regexp_replace(quote, '\\s+', ' ', 'g'))) BETWEEN {QUOTE_MIN} AND {QUOTE_MAX} "
            f"AND hc_curator_term_ok(field, value, quote, term), false)",
            name=op.f('ck_curator_proposal_proposed_complete')),
        # No value is ever JSON null (named to sort after the check above).
        sa.CheckConstraint("value IS NULL OR jsonb_typeof(value) <> 'null'",
                           name=op.f('ck_curator_proposal_value_not_json_null')),
        sa.CheckConstraint("(status = 'refused') = (refusal_code IS NOT NULL) "
                           "AND (refusal_code IS NULL OR refusal_code ~ '^[a-z_]+$')",
                           name=op.f('ck_curator_proposal_refusal_code')),
        sa.CheckConstraint("status <> 'not_stated' OR (value IS NULL AND quote IS NULL AND document_path IS NULL "
                           "AND line IS NULL AND term IS NULL)", name=op.f('ck_curator_proposal_not_stated_empty')),
        sa.CheckConstraint(f"length(coalesce(quote, '')) <= {STORED_TEXT_MAX} "
                           f"AND length(coalesce(value::text, '')) <= {STORED_TEXT_MAX}",
                           name=op.f('ck_curator_proposal_bounded')),
        sa.ForeignKeyConstraint(['invocation_id'], ['agent_invocation.id'],
                                name=op.f('fk_curator_proposal_invocation_id')),
        sa.ForeignKeyConstraint(['source_version_id'], ['source_version.id'],
                                name=op.f('fk_curator_proposal_source_version_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_curator_proposal')),
        sa.UniqueConstraint('invocation_id', 'field', name=op.f('uq_curator_proposal_invocation_id_field')),
    )
    op.create_table(
        'curator_decision',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('proposal_id', sa.BigInteger(), nullable=False),
        sa.Column('decision', sa.Text(), nullable=False),
        sa.Column('decided_by', sa.Text(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("decision IN ('accepted', 'rejected')", name=op.f('ck_curator_decision_decision')),
        sa.CheckConstraint("length(btrim(decided_by)) BETWEEN 1 AND 200 AND length(coalesce(note, '')) <= 2000",
                           name=op.f('ck_curator_decision_named_and_bounded')),
        sa.ForeignKeyConstraint(['proposal_id'], ['curator_proposal.id'],
                                name=op.f('fk_curator_decision_proposal_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_curator_decision')),
        sa.UniqueConstraint('proposal_id', name=op.f('uq_curator_decision_proposal_id')),
    )

    for f in FUNCTIONS:
        op.execute(f)
    for t in TRIGGERS:
        op.execute(t)
    op.execute(MODEL_CALL_INSERT_0005)
    op.execute(MODEL_CALL_UPDATE_0005)


# Anything 0005 added that holds data; the downgrade refuses while any exists.
IN_USE = """
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM source_file WHERE role <> 'data') OR EXISTS (SELECT 1 FROM agent_invocation)
           OR EXISTS (SELECT 1 FROM model_call WHERE invocation_id IS NOT NULL)
           OR EXISTS (SELECT 1 FROM curator_proposal) OR EXISTS (SELECT 1 FROM curator_decision) THEN
            RAISE EXCEPTION 'hypocurate: migration 0005 is in use (documentation, invocations, proposals or decisions); not downgraded';
        END IF;
    END $$
"""


def downgrade() -> None:
    op.execute(IN_USE)
    op.execute(MODEL_CALL_INSERT_0001)
    op.execute(MODEL_CALL_UPDATE_0001)
    for t in ("curator_decision", "curator_proposal"):
        op.drop_table(t)
    op.drop_constraint(op.f('ck_model_call_with_invocation'), 'model_call', type_='check')
    op.drop_constraint(op.f('ck_model_call_run_with_stage'), 'model_call', type_='check')
    op.alter_column('model_call', 'stage_result_id', existing_type=sa.BigInteger(), nullable=False)
    op.alter_column('model_call', 'run_id', existing_type=sa.BigInteger(), nullable=False)
    op.drop_index('ix_model_call_invocation_id', table_name='model_call')
    op.drop_constraint(op.f('fk_model_call_invocation_id'), 'model_call', type_='foreignkey')
    op.drop_column('model_call', 'invocation_id')
    op.drop_index('ix_agent_invocation_run_id', table_name='agent_invocation')
    op.drop_table('agent_invocation')
    for f in FUNCTION_NAMES + CHECK_FUNCTION_NAMES:
        op.execute(f"DROP FUNCTION {f}")
    op.drop_constraint(op.f('uq_run_agent_setting_run_id_role_agent_setting_id'), 'run_agent_setting', type_='unique')
    op.drop_constraint(op.f('ck_source_file_safe_data_file_path'), 'source_file', type_='check')
    op.create_check_constraint(op.f('ck_source_file_safe_data_file_path'), 'source_file', PATH_RULE_0001)
    op.drop_column('source_file', 'role')
