"""The tables of PRD Section 7 (build step 3), as decided with the owner on 2026-10-04/05.

The rules that protect the method are enforced in the database itself, by CHECK
constraints here and by triggers in the migration (`migrations/versions/0001_data_model.py`):
a locked plan cannot change; a frozen dataset cannot change; records are never
updated; stored is not analysed (`record` versus `run_record` and `analysis_set`);
a narrower question is a separate query linked to the run it narrows; every
model call has tokens and cost or counts at its upper bound.

Limitation, stated plainly: the triggers stop the application and ordinary edits.
The database owner can still drop a trigger; the fingerprints are the cross-check.

No table stores token or cost totals; the views `model_call_totals_by_*` sum
`model_call`. Search coverage and the kinds of "nothing found" are not stored per
run either; the view `run_search_coverage` reports them per source, from the run's
own dispatch-time `run_source` rows.

Locking protocol (review finding 1; re-check item 1). Lock order: version, then run,
then the run's child rows. Application code calls `SELECT hc_write_lock(p_run => ...)`
(or `p_version => ...` for chosen sources, submission and dispatch) first in every
transaction that writes to them; such paths cannot deadlock with each other. The
triggers lock the run (or version) before checking its state, which makes the checks
race-free but does not by itself fix the lock order: an UPDATE of a child row locks
that row before its trigger asks for the run lock. A path that skips the protocol may
deadlock; PostgreSQL then aborts one transaction (SQLSTATE 40P01) and the caller must
retry the whole transaction.

What the CHECKs on `analysis_result` establish (review finding 5): necessary
conditions on the stored counts only. The full validity rules of PRD 5.7 and the
agreement of the verdict with the pooled result are computed and tested in step 7
(`pipeline/statistics.py`). Migration 0004 (step 7) adds the withheld state, computed by the
insert trigger, the records a fit does not use, the test-run label, both calibration methods,
the fourth per-source label and the run's evidence level.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Double,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    LargeBinary,
    MetaData,
    Sequence,
    SmallInteger,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy import text as sql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s",
    "pk": "pk_%(table_name)s",
}

MAX_FILE_BYTES = 5 * 1024 * 1024  # owner decision, 2026-10-04: 5 MiB per stored file
ROLES = ("planner", "curator", "critic", "analyst", "commentator")
SHA256 = "~ '^[0-9a-f]{64}$'"


def one_of(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def now():
    return sql("now()")


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


def pk() -> Mapped[int]:
    return mapped_column(BigInteger, Identity(), primary_key=True)


def created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=now())


# --- Fixed lists ---------------------------------------------------------------

class Domain(Base):
    """PRD 5.5. Seeded by the migration; append-only."""
    __tablename__ = "domain"
    id: Mapped[int] = pk()
    key: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    supported: Mapped[bool] = mapped_column(Boolean)
    profile_name: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("NOT supported OR profile_name IS NOT NULL", name="supported_has_profile"),
    )


TAG_KINDS = ("property", "alloy_class", "test_condition")
TAG_STATUSES = ("proposed", "approved", "rejected")


class TagValue(Base):
    """PRD 5.5: fixed lists. A value proposed by the Planner is approved or rejected once by a person."""
    __tablename__ = "tag_value"
    id: Mapped[int] = pk()
    kind: Mapped[str] = mapped_column(Text)
    value: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    proposed_by_run_id: Mapped[int | None] = mapped_column(ForeignKey("run.id"))
    created_at: Mapped[datetime] = created()
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("kind", "value"),
        CheckConstraint(one_of("kind", TAG_KINDS), name="kind"),
        CheckConstraint(one_of("status", TAG_STATUSES), name="status"),
        CheckConstraint("length(value) > 0", name="value_not_empty"),
        CheckConstraint("(status = 'proposed') = (decided_at IS NULL)", name="decided_once"),
    )


# --- Sources -------------------------------------------------------------------

SOURCE_TYPES = ("uploaded_table", "web_interface", "paper_search", "model_recall")
DATA_KINDS = ("measured", "computed", "model_recalled")


class Source(Base):
    """A registered source (PRD 9.6). It is never deleted and its key never changes.
    `source_type`, `data_kind` and `grouping_unit` here are the settings for the next
    version: each version keeps its own copy (review finding 4). Operational settings
    (enabled, adapter status, address, licence, properties) may change."""
    __tablename__ = "source"
    id: Mapped[int] = pk()
    key: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    licence: Mapped[str] = mapped_column(Text)
    data_kind: Mapped[str] = mapped_column(Text)
    adapter_status: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean)
    # PRD 5.7: each source states its grouping unit (the paper, or the whole dataset).
    grouping_unit: Mapped[str] = mapped_column(Text)
    properties_covered: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=sql("'{}'"))
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        CheckConstraint("key ~ '^[a-z0-9_]+$'", name="key_format"),
        CheckConstraint(one_of("source_type", SOURCE_TYPES), name="source_type"),
        CheckConstraint(one_of("data_kind", DATA_KINDS), name="data_kind"),
        CheckConstraint(one_of("adapter_status", ("adapter_needed", "available")), name="adapter_status"),
        CheckConstraint(one_of("grouping_unit", ("paper", "dataset", "batch")), name="grouping_unit"),
    )


class SourceVersion(Base):
    """A snapshot of a source (review finding 4). It holds its own copy of the settings
    that change how records are read, copied from `source` at insert. Files are added,
    then the version is sealed once: the database sets `sealed_at` and checks that
    `fingerprint` is the SHA-256 of the sorted file list. Only a sealed version can be
    used by a run. Nothing changes after sealing; it is never deleted.
    At sealing (re-check item 2) the database sets `files_digest`, the SHA-256 of the
    sorted file list, and requires `fingerprint` to be the SHA-256 of that digest plus
    the interpretation settings. `fingerprint` is the version's identity (unique per
    source), so the same files under revised settings seal as a new version."""
    __tablename__ = "source_version"
    id: Mapped[int] = pk()
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"))
    label: Mapped[str] = mapped_column(Text)
    obtained_on: Mapped[date] = mapped_column(Date)
    source_type: Mapped[str] = mapped_column(Text)
    data_kind: Mapped[str] = mapped_column(Text)
    grouping_unit: Mapped[str] = mapped_column(Text)
    sealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    files_digest: Mapped[str | None] = mapped_column(Text)
    fingerprint: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        UniqueConstraint("source_id", "fingerprint"),
        UniqueConstraint("id", "source_id"),
        CheckConstraint(f"fingerprint {SHA256}", name="fingerprint_format"),
        CheckConstraint("(sealed_at IS NULL) = (fingerprint IS NULL)", name="sealed_with_fingerprint"),
        CheckConstraint(f"files_digest {SHA256}", name="files_digest_format"),
        CheckConstraint("(sealed_at IS NULL) = (files_digest IS NULL)", name="sealed_with_files_digest"),
        CheckConstraint(one_of("source_type", SOURCE_TYPES), name="source_type"),
        CheckConstraint(one_of("data_kind", DATA_KINDS), name="data_kind"),
        CheckConstraint(one_of("grouping_unit", ("paper", "dataset", "batch")), name="grouping_unit"),
    )


FILE_ROLES = ("data", "documentation", "curation")


class SourceFile(Base):
    """A file of a source version (at most 5 MiB), added only before its version is sealed.
    Append-only. Step 8a (migration 0005; owner, 2026-10-06): its role is 'data' (what an adapter
    reads; every file before 8a), 'documentation' (the source's own documentation, which the Curator
    reads) or 'curation' (the accepted Curator values sealed into a curated version)."""
    __tablename__ = "source_file"
    id: Mapped[int] = pk()
    source_version_id: Mapped[int] = mapped_column(ForeignKey("source_version.id"))
    path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(Text)
    content: Mapped[bytes] = mapped_column(LargeBinary)
    role: Mapped[str] = mapped_column(Text, server_default=sql("'data'"))
    __table_args__ = (
        UniqueConstraint("source_version_id", "path"),
        CheckConstraint(f"octet_length(content) <= {MAX_FILE_BYTES}", name="max_size"),
        # Re-check item 2: a safe character set, anchored at both ends, so a path holds no
        # line break and the sealed file list has one unambiguous line per file. Step 8a: the rule
        # by role (0001's name kept); a path tells its role, so the files digest stays unambiguous.
        CheckConstraint(
            "(role = 'data' AND path ~ '^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$' AND path !~ '^documentation/') "
            "OR (role = 'documentation' AND path ~ '^documentation/[A-Za-z0-9][A-Za-z0-9._-]*[.](tex|xml|md|txt)$') "
            "OR (role = 'curation' AND path = 'curation.json')", name="safe_data_file_path"),
        CheckConstraint("sha256 = encode(sha256(content), 'hex')", name="sha256_matches_content"),
    )


# --- Agent settings ------------------------------------------------------------

class AgentSetting(Base):
    """Versioned settings per role (PRD 9.5). Append-only: a change is a new version."""
    __tablename__ = "agent_setting"
    id: Mapped[int] = pk()
    role: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer)
    instruction: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    limits: Mapped[dict] = mapped_column(JSONB, server_default=sql("'{}'"))
    settings: Mapped[dict] = mapped_column(JSONB, server_default=sql("'{}'"))
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        UniqueConstraint("role", "version"),
        UniqueConstraint("id", "role"),
        CheckConstraint(one_of("role", ROLES), name="role"),
        CheckConstraint("version >= 1", name="version_positive"),
    )


# --- Queries -------------------------------------------------------------------

HYPOTHESIS_NUMBER_SEQ = Sequence("hypothesis_number_seq", metadata=Base.metadata)


class Hypothesis(Base):
    """One row per query number. A narrower question is its own query, linked to the
    run whose outcome was partly sufficient (owner decision, question 1)."""
    __tablename__ = "hypothesis"
    id: Mapped[int] = pk()
    number: Mapped[str] = mapped_column(
        Text, unique=True,
        server_default=sql("'Q-' || lpad(nextval('hypothesis_number_seq')::text, 4, '0')"))
    narrower_of_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("run.id", use_alter=True))
    created_at: Mapped[datetime] = created()
    # Step 9a (0007): at most one narrower question per original run.
    __table_args__ = (Index("uq_hypothesis_narrower_of_run_id", "narrower_of_run_id", unique=True,
                            postgresql_where=sql("narrower_of_run_id IS NOT NULL")),)


VERSION_STATUSES = ("draft", "submitted", "returned", "dispatched")


# The data-sufficiency options (PRD 5.8): of a query (step 8b, 0006) and of its locked plan (0001).
SUFFICIENCY_OPTIONS = ("fixed_minimum", "use_available")


class HypothesisVersion(Base):
    """Each edit is a new version. Frozen once it leaves draft, except the review
    fields; everything is frozen once returned or dispatched."""
    __tablename__ = "hypothesis_version"
    id: Mapped[int] = pk()
    hypothesis_id: Mapped[int] = mapped_column(ForeignKey("hypothesis.id"))
    version_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domain.id"))
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default=sql("'draft'"))
    confirmed_domain_id: Mapped[int | None] = mapped_column(ForeignKey("domain.id"))
    domain_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created()
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Step 8b (migration 0006; owner, A2): the query's data-sufficiency option, chosen before dispatch,
    # fixed once submitted; the locked plan's option must equal it.
    sufficiency_option: Mapped[str] = mapped_column(Text, server_default=sql("'fixed_minimum'"))
    __table_args__ = (
        UniqueConstraint("hypothesis_id", "version_number"),
        CheckConstraint(one_of("status", VERSION_STATUSES), name="status"),
        CheckConstraint("version_number >= 1", name="version_positive"),
        CheckConstraint("length(btrim(text)) > 0", name="text_not_empty"),
        CheckConstraint("(confirmed_domain_id IS NULL) = (domain_confirmed_at IS NULL)",
                        name="confirmed_domain_with_time"),
        CheckConstraint("status <> 'dispatched' OR (confirmed_domain_id IS NOT NULL AND dispatched_at IS NOT NULL)",
                        name="dispatch_needs_confirmed_domain"),
        CheckConstraint("status = 'draft' OR submitted_at IS NOT NULL", name="submitted_time"),
        CheckConstraint("status <> 'returned' OR returned_at IS NOT NULL", name="returned_time"),
        CheckConstraint(one_of("sufficiency_option", SUFFICIENCY_OPTIONS), name="sufficiency_option"),
    )


class HypothesisVersionSource(Base):
    """The sources chosen for a version. Changes only while the version is a draft."""
    __tablename__ = "hypothesis_version_source"
    hypothesis_version_id: Mapped[int] = mapped_column(ForeignKey("hypothesis_version.id"), primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), primary_key=True)


# --- Runs ----------------------------------------------------------------------

# Step 9a (0007): 'waiting' for a named person's confirmation of the question as tested, before the rules lock.
RUN_STATUSES = ("queued", "running", "waiting", "completed", "failed")
OUTCOMES = ("sufficient", "partly_sufficient", "insufficient")
VERDICTS = ("supported", "not_supported")


class Run(Base):
    """One row per dispatch. Completed and failed are final.
    Verdict (owner decision, question 4): present if and only if the run completed as
    sufficient. Exploratory: only for a sufficient run under "use what is available"
    whose pooled data were below the plan's minimums (checked by trigger)."""
    __tablename__ = "run"
    id: Mapped[int] = pk()
    hypothesis_version_id: Mapped[int] = mapped_column(ForeignKey("hypothesis_version.id"))
    status: Mapped[str] = mapped_column(Text, server_default=sql("'queued'"))
    current_stage: Mapped[str | None] = mapped_column(Text)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str | None] = mapped_column(Text)
    verdict: Mapped[str | None] = mapped_column(Text)
    exploratory: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))
    # Step 7 (migration 0004; register 'evidence_level_scale'): 1 to 6, written by the copy path;
    # required on every completed run.
    evidence_level: Mapped[int | None] = mapped_column(SmallInteger)
    # Step 8b fix round 1 (migration 0006): the results statement's format version, recorded when the run completes.
    statement_format_version: Mapped[int | None] = mapped_column(SmallInteger)
    # Step 9a (0007; register 'spending_caps'): a lower ceiling than the per-run cap, stored at dispatch, never changed.
    # Fix round 1 (owner, 2026-10-08): none given is the per-run cap, the column's default (runs before 0007: empty).
    spending_ceiling: Mapped[Decimal | None] = mapped_column(Numeric, server_default=sql("2"))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    agent_mode: Mapped[str] = mapped_column(Text, server_default=sql("'four_roles'"))
    fixed_plan: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))
    experiment_flags: Mapped[dict] = mapped_column(JSONB, server_default=sql("'{}'"))
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint(one_of("status", RUN_STATUSES), name="status"),
        CheckConstraint(f"outcome IS NULL OR {one_of('outcome', OUTCOMES)}", name="outcome"),
        CheckConstraint(f"verdict IS NULL OR {one_of('verdict', VERDICTS)}", name="verdict"),
        CheckConstraint("agent_mode = 'four_roles'", name="agent_mode"),
        CheckConstraint("(outcome IS NOT NULL) = (status = 'completed')", name="outcome_iff_completed"),
        CheckConstraint(
            "(verdict IS NOT NULL) = (status = 'completed' AND outcome IS NOT DISTINCT FROM 'sufficient')",
            name="verdict_iff_sufficient"),
        CheckConstraint("NOT exploratory OR verdict IS NOT NULL", name="exploratory_needs_verdict"),
        CheckConstraint("evidence_level IS NULL OR (evidence_level BETWEEN 1 AND 6 AND outcome IS NOT NULL "
                        "AND (evidence_level = 6) = (verdict IS NOT NULL AND NOT exploratory) "
                        "AND (evidence_level = 5) = (verdict IS NOT NULL AND exploratory))", name="evidence_level"),
        CheckConstraint("(evidence_level IS NOT NULL) = (status = 'completed')", name="evidence_level_iff_completed"),
        CheckConstraint("statement_format_version IS NULL OR statement_format_version >= 1",
                        name="statement_format_version"),
        CheckConstraint("spending_ceiling IS NULL OR (spending_ceiling > 0 AND spending_ceiling < 'Infinity')",
                        name="spending_ceiling"),
        CheckConstraint("status = 'queued' OR started_at IS NOT NULL OR status = 'failed'", name="started_time"),
        CheckConstraint("status <> 'completed' OR completed_at IS NOT NULL", name="completed_time"),
        CheckConstraint("(status = 'failed') = (failure_reason IS NOT NULL)", name="failed_has_reason"),
        CheckConstraint("status <> 'failed' OR failed_at IS NOT NULL", name="failed_time"),
    )




CONFIRMED_BY_MAX = 200


class RulesConfirmation(Base):
    """Step 9a (0007; owner, Q1, A1, A2): a named person's confirmation of the question as tested, for a run waiting
    at its rules lock: the fingerprint of the plan that will be locked, the stages it rests on, the content shown
    and the exact text shown. One per run, at the database's time. Append-only."""
    __tablename__ = "rules_confirmation"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), unique=True)
    confirmed_by: Mapped[str] = mapped_column(Text)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    plan_fingerprint: Mapped[str] = mapped_column(Text)
    planner_stage_result_id: Mapped[int | None] = mapped_column(ForeignKey("stage_result.id"))
    narrowing_stage_result_id: Mapped[int | None] = mapped_column(ForeignKey("stage_result.id"))
    content: Mapped[dict] = mapped_column(JSONB)
    shown: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint(f"length(btrim(confirmed_by)) BETWEEN 1 AND {CONFIRMED_BY_MAX}", name="named"),
        CheckConstraint(f"plan_fingerprint {SHA256}", name="fingerprint_format"),
        CheckConstraint("jsonb_typeof(content) = 'object' AND length(shown) > 0", name="content_and_text"),
    )


# Step 9b (0008): how a claim ends; the same list as pipeline/queue.RELEASE_REASONS (tests check both).
RELEASE_REASONS = ("finished", "waiting", "stopped_for_recovery", "child_failed", "child_stuck", "shutdown", "lost")


class RunClaim(Base):
    """Step 9b (0008; R6): a worker's hold on one open run, with the guarded child's pid (once), its heartbeat (on
    this row, never the run row) and how it was released (once). One open claim per run. Never deleted."""
    __tablename__ = "run_claim"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    worker: Mapped[str] = mapped_column(Text)
    child_pid: Mapped[int | None] = mapped_column(Integer)
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    release_reason: Mapped[str | None] = mapped_column(Text)
    found: Mapped[dict | None] = mapped_column(JSONB)
    recovery: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))  # fix round 1, finding 7
    __table_args__ = (
        Index("uq_run_claim_open", "run_id", unique=True, postgresql_where=sql("released_at IS NULL")),
        CheckConstraint("length(btrim(worker)) BETWEEN 1 AND 200", name="worker_named"),
        CheckConstraint(f"release_reason IS NULL OR {one_of('release_reason', RELEASE_REASONS)}", name="release"),
        CheckConstraint("(released_at IS NULL) = (release_reason IS NULL)", name="released_with_reason"),
        CheckConstraint("found IS NULL OR jsonb_typeof(found) = 'object'", name="found_object"),
        CheckConstraint("child_pid IS NULL OR child_pid > 0", name="child_pid"),
    )



# Step 10b, fix round 1 (0009; owner, 2026-10-11): who did what. The same lists as migration 0009 (tests check both).
ACTIONS = ("create", "edit", "new_version", "submit", "return", "confirm_domain", "dispatch", "dispatch_again",
           "cancel", "confirm_rules", "register_source")
CHANNELS = ("website", "command line", "code")
# What each action names: v = the query version, r = the run, s = the source version.
ACTION_TARGETS = {"create": "v", "edit": "v", "new_version": "v", "submit": "v", "return": "v", "confirm_domain": "v",
                  "dispatch": "vr", "dispatch_again": "vr", "cancel": "r", "confirm_rules": "r", "register_source": "s"}
_TARGET_COLUMNS = {"v": "hypothesis_version_id", "r": "run_id", "s": "source_version_id"}


def _targets_check() -> str:
    return " OR ".join(
        f"(action = '{action}' AND " + " AND ".join(
            f"{col} IS {'NOT ' if k in kinds else ''}NULL" for k, col in _TARGET_COLUMNS.items()) + ")"
        for action, kinds in ACTION_TARGETS.items())


class ActionRecord(Base):
    """Step 10b, fix round 1 (0009): one row per person's action, written in the same transaction as the write it
    records: the action, where (website, command line, code), the name given (required on the website), what it acted
    on, and the database's time. Append-only. A record, not a gate."""
    __tablename__ = "action_record"
    id: Mapped[int] = pk()
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    action: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(Text)
    actor: Mapped[str | None] = mapped_column(Text)
    hypothesis_version_id: Mapped[int | None] = mapped_column(ForeignKey("hypothesis_version.id"), index=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("run.id"), index=True)
    source_version_id: Mapped[int | None] = mapped_column(ForeignKey("source_version.id"))
    __table_args__ = (
        CheckConstraint(one_of("action", ACTIONS), name="action"),
        CheckConstraint(one_of("channel", CHANNELS), name="channel"),
        CheckConstraint("actor IS NULL OR (actor = btrim(actor) AND length(actor) BETWEEN 1 AND 200)", name="actor"),
        CheckConstraint("channel <> 'website' OR actor IS NOT NULL", name="website_named"),
        CheckConstraint("channel <> 'code' OR actor IS NULL", name="code_unnamed"),
        CheckConstraint(_targets_check(), name="targets"),
    )

class Plan(Base):
    """The locked plan (PRD 5.1, 5.6). Inserted at the rules lock, never changed.
    The columns the database checks against are explicit; the rest is `content`."""
    __tablename__ = "plan"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), unique=True)
    content: Mapped[dict] = mapped_column(JSONB)
    fingerprint: Mapped[str] = mapped_column(Text)
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    sufficiency_option: Mapped[str] = mapped_column(Text)
    min_records: Mapped[int] = mapped_column(Integer)
    min_alloys: Mapped[int] = mapped_column(Integer)
    min_groups: Mapped[int] = mapped_column(Integer)
    min_resid_df: Mapped[int] = mapped_column(Integer)
    sensitivity_analysis_keys: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=sql("'{}'"))
    # Owner's addition 1: an information-only power report; never a gate, read by no constraint.
    power_assumptions: Mapped[dict | None] = mapped_column(JSONB)
    __table_args__ = (
        CheckConstraint(f"fingerprint {SHA256}", name="fingerprint_format"),
        CheckConstraint(one_of("sufficiency_option", SUFFICIENCY_OPTIONS), name="sufficiency_option"),
        CheckConstraint("min_records >= 1 AND min_alloys >= 1 AND min_groups >= 1 AND min_resid_df >= 1",
                        name="minimums_positive"),
        CheckConstraint("NOT ('primary' = ANY (sensitivity_analysis_keys))", name="primary_not_sensitivity"),
    )


class RunTag(Base):
    """Tags attached at the lock (PRD 5.5); written in the lock's transaction only."""
    __tablename__ = "run_tag"
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), primary_key=True)
    tag_value_id: Mapped[int] = mapped_column(ForeignKey("tag_value.id"), primary_key=True)


class RunAgentSetting(Base):
    """The agent settings version each role uses, recorded at dispatch (PRD 8)."""
    __tablename__ = "run_agent_setting"
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), primary_key=True)
    role: Mapped[str] = mapped_column(Text, primary_key=True)
    agent_setting_id: Mapped[int] = mapped_column(BigInteger)
    __table_args__ = (
        ForeignKeyConstraint(["agent_setting_id", "role"], ["agent_setting.id", "agent_setting.role"],
                             name="fk_run_agent_setting_agent_setting"),
        # Step 8a (0005): the target of an invocation's (run, role, setting).
        UniqueConstraint("run_id", "role", "agent_setting_id"),
    )


SEARCH_STATUSES = ("not_selected", "pending", "searched", "failed")
NOTHING_FOUND = ("reported_negative", "missing_evidence", "failed_search")


class RunSource(Base):
    """Per run and source: what was searched, and the kind of "nothing found"
    (owner decision, question 3). Coverage and the kinds of "nothing found" are reported
    per source by the view run_search_coverage, from these dispatch-time rows only
    (review finding 6). A run starts only when every source registered at dispatch has a row."""
    __tablename__ = "run_source"
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("source.id"), primary_key=True)
    source_version_id: Mapped[int | None] = mapped_column(BigInteger)
    search_status: Mapped[str] = mapped_column(Text)
    nothing_found: Mapped[str | None] = mapped_column(Text)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(["source_version_id", "source_id"], ["source_version.id", "source_version.source_id"],
                             name="fk_run_source_source_version"),
        CheckConstraint(one_of("search_status", SEARCH_STATUSES), name="search_status"),
        CheckConstraint(f"nothing_found IS NULL OR {one_of('nothing_found', NOTHING_FOUND)}", name="nothing_found"),
        CheckConstraint("(search_status = 'failed') = (nothing_found IS NOT DISTINCT FROM 'failed_search')",
                        name="failed_iff_failed_search"),
        CheckConstraint("search_status NOT IN ('not_selected', 'pending') OR nothing_found IS NULL",
                        name="undecided_has_no_kind"),
        CheckConstraint("search_status <> 'failed' OR failure_reason IS NOT NULL", name="failed_has_reason"),
        CheckConstraint("search_status <> 'not_selected' OR source_version_id IS NULL", name="not_selected_no_version"),
        CheckConstraint("search_status <> 'searched' OR source_version_id IS NOT NULL", name="searched_has_version"),
        CheckConstraint("(search_status IN ('searched', 'failed')) = (decided_at IS NOT NULL)", name="decided_time"),
    )


class RunSnapshot(Base):
    """The dataset freeze (PRD 5.6): fingerprint and time. Append-only."""
    __tablename__ = "run_snapshot"
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(Text)
    frozen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    n_records: Mapped[int] = mapped_column(Integer)
    __table_args__ = (
        CheckConstraint(f"fingerprint {SHA256}", name="fingerprint_format"),
        CheckConstraint("n_records >= 1", name="not_empty"),
    )


STAGE_STATUSES = ("running", "done", "failed", "skipped")


class StageResult(Base):
    """Per stage and attempt: input, output, reasoning, tool calls, model, times.
    Token and cost totals come from the view model_call_totals_by_stage."""
    __tablename__ = "stage_result"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    stage: Mapped[str] = mapped_column(Text)
    attempt: Mapped[int] = mapped_column(Integer, server_default=sql("1"))
    role: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default=sql("'running'"))
    input: Mapped[dict | None] = mapped_column(JSONB)
    output: Mapped[dict | None] = mapped_column(JSONB)
    reasoning: Mapped[str | None] = mapped_column(Text)
    tool_calls: Mapped[dict | None] = mapped_column(JSONB)
    agent_setting_id: Mapped[int | None] = mapped_column(ForeignKey("agent_setting.id"))
    model: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("run_id", "stage", "attempt"),
        UniqueConstraint("id", "run_id"),
        CheckConstraint("stage ~ '^[a-z_]+$'", name="stage_format"),
        CheckConstraint("attempt >= 1", name="attempt_positive"),
        CheckConstraint(f"role IS NULL OR {one_of('role', ROLES)}", name="role"),
        CheckConstraint(one_of("status", STAGE_STATUSES), name="status"),
        CheckConstraint("(status = 'running') = (finished_at IS NULL)", name="finished_time"),
    )


CALL_STATUSES = ("started", "succeeded", "failed", "interrupted")
USAGE = ("input_tokens", "output_tokens", "cached_tokens", "cost")


def _all(cond: str) -> str:
    return " AND ".join(f"{c} {cond}" for c in USAGE)


class ModelCall(Base):
    """One row per model call (owner decision, question 5), written BEFORE the request
    with its upper bound `max_cost`, then finished exactly once. A call without
    reported cost counts at `max_cost` toward totals and caps. `started_at` and
    `finished_at` are the database's transaction times (review finding 7)."""
    __tablename__ = "model_call"
    id: Mapped[int] = pk()
    # Step 8a (0005): NULL exactly for the calls of a registration invocation (the Curator).
    run_id: Mapped[int | None] = mapped_column(BigInteger)
    stage_result_id: Mapped[int | None] = mapped_column(BigInteger)
    invocation_id: Mapped[int | None] = mapped_column(ForeignKey("agent_invocation.id"))
    role: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    price_table_version: Mapped[str] = mapped_column(Text)
    # numeric with no fixed scale: stored exactly, so no amount rounds (review finding 7)
    max_cost: Mapped[Decimal] = mapped_column(Numeric())
    status: Mapped[str] = mapped_column(Text, server_default=sql("'started'"))
    input_tokens: Mapped[int | None] = mapped_column(BigInteger)
    output_tokens: Mapped[int | None] = mapped_column(BigInteger)
    cached_tokens: Mapped[int | None] = mapped_column(BigInteger)
    cost: Mapped[Decimal | None] = mapped_column(Numeric())
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        ForeignKeyConstraint(["stage_result_id", "run_id"], ["stage_result.id", "stage_result.run_id"],
                             name="fk_model_call_stage_result"),
        Index("ix_model_call_run_id", "run_id"),
        Index("ix_model_call_invocation_id", "invocation_id"),
        CheckConstraint(one_of("role", ROLES), name="role"),
        CheckConstraint("(run_id IS NULL) = (stage_result_id IS NULL)", name="run_with_stage"),
        # Named to sort after every check of 0001, so their refusals keep their own messages.
        CheckConstraint("invocation_id IS NOT NULL", name="with_invocation"),
        CheckConstraint(one_of("status", CALL_STATUSES), name="status"),
        CheckConstraint("length(model) > 0 AND length(price_table_version) > 0", name="model_and_prices_named"),
        CheckConstraint("max_cost > 0", name="max_cost_positive"),
        # Re-check item 3: unbounded numeric also holds NaN and Infinity; PostgreSQL orders
        # NaN above Infinity, so "< 'Infinity'" excludes both. -Infinity fails "> 0"/">= 0".
        CheckConstraint("max_cost < 'Infinity' AND (cost IS NULL OR cost < 'Infinity')", name="money_finite"),
        CheckConstraint(" AND ".join(f"coalesce({c}, 0) >= 0" for c in USAGE), name="usage_not_negative"),
        CheckConstraint(f"status <> 'started' OR ({_all('IS NULL')} AND finished_at IS NULL)",
                        name="started_has_no_usage"),
        CheckConstraint(f"status <> 'succeeded' OR ({_all('IS NOT NULL')} AND finished_at IS NOT NULL)",
                        name="succeeded_has_usage"),
        CheckConstraint(f"status <> 'failed' OR (finished_at IS NOT NULL AND (({_all('IS NULL')}) "
                        f"OR ({_all('IS NOT NULL')})))", name="failed_usage_all_or_none"),
        CheckConstraint(f"status <> 'interrupted' OR ({_all('IS NULL')} AND finished_at IS NOT NULL)",
                        name="interrupted_has_no_usage"),
    )


# --- Agent invocations and the Curator's proposals (step 8a, migration 0005) --------------

CURATION_FIELDS = ("test_type", "phase_class", "test_temperature", "test_temperature_band", "microstructure")
QUOTE_MIN, QUOTE_MAX = 30, 600  # a proposal's quote, whitespace collapsed (register 'curator_quote_checks')
STORED_TEXT_MAX = 4000


class AgentInvocation(Base):
    """One record per agent call (step 5 re-check): the dispatcher reads run or version, role,
    setting and source from it alone. A run invocation's (run, role, setting) is one recorded at
    dispatch; a registration invocation is the Curator's, on a sealed source version. Append-only."""
    __tablename__ = "agent_invocation"
    id: Mapped[int] = pk()
    scope: Mapped[str] = mapped_column(Text)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("run.id"))
    stage_result_id: Mapped[int | None] = mapped_column(BigInteger)
    source_version_id: Mapped[int | None] = mapped_column(ForeignKey("source_version.id"))
    role: Mapped[str] = mapped_column(Text)
    agent_setting_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        Index("ix_agent_invocation_run_id", "run_id"),
        CheckConstraint("scope IN ('run', 'registration')", name="scope"),
        CheckConstraint(one_of("role", ROLES), name="role"),
        CheckConstraint(
            "(scope = 'run' AND run_id IS NOT NULL AND stage_result_id IS NOT NULL AND source_version_id IS NULL "
            "AND role <> 'curator') "
            "OR (scope = 'registration' AND run_id IS NULL AND stage_result_id IS NULL "
            "AND source_version_id IS NOT NULL AND role = 'curator')", name="shape"),
        ForeignKeyConstraint(["agent_setting_id", "role"], ["agent_setting.id", "agent_setting.role"],
                             name="fk_agent_invocation_agent_setting"),
        ForeignKeyConstraint(["stage_result_id", "run_id"], ["stage_result.id", "stage_result.run_id"],
                             name="fk_agent_invocation_stage_result"),
        ForeignKeyConstraint(["run_id", "role", "agent_setting_id"],
                             ["run_agent_setting.run_id", "run_agent_setting.role",
                              "run_agent_setting.agent_setting_id"], name="fk_agent_invocation_run_agent_setting"),
    )


class CuratorProposal(Base):
    """What the Curator proposed for one field, as stored by code after its two checks (owner, Q2):
    'proposed' (passed: the quote occurs in the named documentation file, which the database checks
    again, and contains the listed term), 'refused' (with a code) or 'not_stated'. Append-only."""
    __tablename__ = "curator_proposal"
    id: Mapped[int] = pk()
    invocation_id: Mapped[int] = mapped_column(ForeignKey("agent_invocation.id"))
    source_version_id: Mapped[int] = mapped_column(ForeignKey("source_version.id"))
    field: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    value: Mapped[dict | None] = mapped_column(JSONB)
    quote: Mapped[str | None] = mapped_column(Text)
    document_path: Mapped[str | None] = mapped_column(Text)
    line: Mapped[int | None] = mapped_column(Integer)
    term: Mapped[str | None] = mapped_column(Text)
    refusal_code: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        UniqueConstraint("invocation_id", "field"),
        CheckConstraint(one_of("field", CURATION_FIELDS), name="field"),
        CheckConstraint("status IN ('proposed', 'refused', 'not_stated')", name="status"),
        CheckConstraint(
            f"status <> 'proposed' OR coalesce(value IS NOT NULL AND quote IS NOT NULL AND document_path IS NOT NULL "
            f"AND line IS NOT NULL AND term IS NOT NULL AND line >= 1 "
            f"AND length(btrim(regexp_replace(quote, '\\s+', ' ', 'g'))) BETWEEN {QUOTE_MIN} AND {QUOTE_MAX} "
            f"AND hc_curator_term_ok(field, value, quote, term), false)", name="proposed_complete"),
        CheckConstraint("value IS NULL OR jsonb_typeof(value) <> 'null'", name="value_not_json_null"),
        CheckConstraint("(status = 'refused') = (refusal_code IS NOT NULL) "
                        "AND (refusal_code IS NULL OR refusal_code ~ '^[a-z_]+$')", name="refusal_code"),
        CheckConstraint("status <> 'not_stated' OR (value IS NULL AND quote IS NULL AND document_path IS NULL "
                        "AND line IS NULL AND term IS NULL)", name="not_stated_empty"),
        CheckConstraint(f"length(coalesce(quote, '')) <= {STORED_TEXT_MAX} "
                        f"AND length(coalesce(value::text, '')) <= {STORED_TEXT_MAX}", name="bounded"),
    )


class CuratorDecision(Base):
    """A person's decision on one proposal that passed the checks: accepted or rejected, by a
    named person, at the database's time. One per proposal. Append-only."""
    __tablename__ = "curator_decision"
    id: Mapped[int] = pk()
    proposal_id: Mapped[int] = mapped_column(ForeignKey("curator_proposal.id"), unique=True)
    decision: Mapped[str] = mapped_column(Text)
    decided_by: Mapped[str] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    __table_args__ = (
        CheckConstraint("decision IN ('accepted', 'rejected')", name="decision"),
        CheckConstraint("length(btrim(decided_by)) BETWEEN 1 AND 200 AND length(coalesce(note, '')) <= 2000",
                        name="named_and_bounded"),
    )


# --- Records: stored is not analysed ------------------------------------------------

class Record(Base):
    """One observation, extracted in one run (owner decision, question 7). Append-only.
    `source_item_key` identifies the row or item of the source version it came from,
    so the same source row can be matched across runs."""
    __tablename__ = "record"
    id: Mapped[int] = pk()
    extraction_run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    source_version_id: Mapped[int] = mapped_column(ForeignKey("source_version.id"))
    source_item_key: Mapped[str] = mapped_column(Text)
    item_index: Mapped[int] = mapped_column(Integer, server_default=sql("0"))
    kind: Mapped[str] = mapped_column(Text)
    alloy: Mapped[str | None] = mapped_column(Text)
    harmonized: Mapped[dict] = mapped_column(JSONB)
    reported: Mapped[dict] = mapped_column(JSONB)
    paper_reference: Mapped[str | None] = mapped_column(Text)
    paper_doi: Mapped[str | None] = mapped_column(Text)
    # How the record was extracted (migration 0003, step 6): {"method": "adapter" | "agent",
    # "name", "version"}. Required for every new record by the insert trigger.
    extraction: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        CheckConstraint("extraction IS NULL OR coalesce(jsonb_typeof(extraction) = 'object' "
                        "AND jsonb_typeof(extraction->'method') = 'string' "
                        "AND jsonb_typeof(extraction->'name') = 'string' "
                        "AND jsonb_typeof(extraction->'version') = 'string' "
                        "AND (extraction->>'method') IN ('adapter', 'agent') "
                        "AND length(extraction->>'name') > 0 AND length(extraction->>'version') > 0, false)",
                        name="extraction_shape"),
        UniqueConstraint("extraction_run_id", "source_version_id", "source_item_key", "item_index",
                         name="uq_record_origin_per_run"),
        Index("ix_record_source_version_id_source_item_key", "source_version_id", "source_item_key"),
        CheckConstraint(one_of("kind", DATA_KINDS), name="kind"),
        CheckConstraint("length(source_item_key) > 0", name="item_key_not_empty"),
        CheckConstraint("item_index >= 0", name="item_index_not_negative"),
    )


class RunRecord(Base):
    """For each run and record: eligible for the primary analysis or not, and the rule
    that decided it (PRD 5.3). Written by code under the locked plan, before the freeze.
    At the freeze every record of the run must have a decision, and the primary set must
    be exactly the records decided eligible (review finding 2). A duplicate's
    non-surviving copy carries its own decision (eligible = false, "counted once")."""
    __tablename__ = "run_record"
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("record.id"), primary_key=True)
    eligible: Mapped[bool] = mapped_column(Boolean)
    rule: Mapped[str] = mapped_column(Text)
    decided_at: Mapped[datetime] = created()
    __table_args__ = (CheckConstraint("length(rule) > 0", name="rule_named"),)


class AnalysisSet(Base):
    """A frozen record set: 'primary', or a sensitivity analysis named by the locked
    plan (owner decision, question 2)."""
    __tablename__ = "analysis_set"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    key: Mapped[str] = mapped_column(Text)
    __table_args__ = (
        UniqueConstraint("run_id", "key"),
        UniqueConstraint("id", "run_id"),
        CheckConstraint("key ~ '^[a-z0-9_]+$'", name="key_format"),
    )


class AnalysisSetRecord(Base):
    __tablename__ = "analysis_set_record"
    analysis_set_id: Mapped[int] = mapped_column(ForeignKey("analysis_set.id"), primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("record.id"), primary_key=True)


# The Critic's classes and the bound on its reason (step 8b, migration 0006; owner, A7). The same codes as
# `access.vocabulary.CRITIC_CLASSES` (tests/test_migrations_step8b.py checks that they are equal).
CRITIC_CLASSES = ("cannot_tell", "different_specimens_or_conditions", "possible_transcription_or_unit_error",
                  "same_measurement")
CRITIC_REASON_MAX = 300


class Flag(Base):
    """A flag raised by code. `compared_values` is kept for audit; the access layer
    (step 5) never returns it to the Critic. The Critic's class is set once, before the freeze."""
    __tablename__ = "flag"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    kind: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    compared_values: Mapped[dict | None] = mapped_column(JSONB)
    raised_at: Mapped[datetime] = created()
    critic_class: Mapped[str | None] = mapped_column(Text)
    critic_reason: Mapped[str | None] = mapped_column(Text)
    classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("(critic_class IS NULL) = (classified_at IS NULL)", name="classified_time"),
        # Step 8b (migration 0006; owner, A7): the class from the Critic's fixed list; the reason, shown to
        # people only, bounded and only with a class.
        CheckConstraint(f"critic_class IS NULL OR {one_of('critic_class', CRITIC_CLASSES)}", name="critic_class"),
        CheckConstraint(f"critic_reason IS NULL OR (critic_class IS NOT NULL "
                        f"AND length(btrim(critic_reason)) BETWEEN 1 AND {CRITIC_REASON_MAX})", name="critic_reason"),
    )


class FlagRecord(Base):
    __tablename__ = "flag_record"
    flag_id: Mapped[int] = mapped_column(ForeignKey("flag.id"), primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("record.id"), primary_key=True)


# --- Results -------------------------------------------------------------------

SCOPES = ("pooled", "per_source", "sensitivity")
LABELS = ("agrees", "conflicts", "not_enough_data", "same_direction_different_decision")  # 4th: step 7
TEST_RUN_LABEL = "test run: includes constructed data"
INFERENCE_REASONS = ("coefficient_not_fitted", "insufficient_groups", "evidence_concentrated", "uncertainty_not_estimable")
LABEL_REASONS = ("no_p_value", "pooled_without_decision", "zero_coefficient")
COUNTS_ALLOW = "(resid_df >= 1 AND n_groups_informative >= 2)"
SPREAD = "coalesce(effective_papers, 0) >= 2"
P_VALUE_DESCRIPTION = "approximate, nominal, one-sided cluster-robust p-value under the locked method"


class AnalysisResult(Base):
    """One row per analysis and scope (owner's addition 3).
    The CHECKs below are necessary conditions on the stored counts, not the full
    validity rules of PRD 5.7 (review finding 5): the database cannot see whether an
    alloy was measured at two distinct grain sizes, nor recount alloys and groups.
    Those, and the agreement of the verdict with the pooled result, are computed and
    tested in step 7."""
    __tablename__ = "analysis_result"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(BigInteger)
    scope: Mapped[str] = mapped_column(Text)
    analysis_set_id: Mapped[int] = mapped_column(BigInteger)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("source.id"))
    n_records: Mapped[int] = mapped_column(Integer)
    n_alloys: Mapped[int] = mapped_column(Integer)
    n_groups: Mapped[int] = mapped_column(Integer)
    resid_df: Mapped[int] = mapped_column(Integer)
    check1_passed: Mapped[bool] = mapped_column(Boolean)
    check2_passed: Mapped[bool] = mapped_column(Boolean)
    minimums_met: Mapped[bool] = mapped_column(Boolean)
    estimate: Mapped[float | None] = mapped_column(Double)
    std_error: Mapped[float | None] = mapped_column(Double)
    p_value: Mapped[float | None] = mapped_column(Double)
    estimated_power: Mapped[float | None] = mapped_column(Double)
    label: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created()
    # Step 7 (migration 0004): withheld below the fixed minimums (computed by the insert trigger);
    # records of the set the fit does not use; the test-run label.
    withheld: Mapped[bool | None] = mapped_column(Boolean)
    n_records_not_used: Mapped[int] = mapped_column(Integer, server_default=sql("0"))
    test_run_label: Mapped[str | None] = mapped_column(Text)
    # Review fixes (2026-10-06): informative groups (the paper minimum and check 2 count these), why
    # check 2 failed, why a per-source label is "not enough data", the detection rate under the
    # estimated noise.
    n_groups_informative: Mapped[int] = mapped_column(Integer)
    inference_reason: Mapped[str | None] = mapped_column(Text)
    label_reason: Mapped[str | None] = mapped_column(Text)
    estimated_power_estimated_noise: Mapped[float | None] = mapped_column(Double)
    # Re-check (owner, 2026-10-06): concentrated evidence.
    effective_papers: Mapped[float | None] = mapped_column(Double)
    largest_paper_share: Mapped[float | None] = mapped_column(Double)
    # Merge decision (2026-10-06): stored with every p-value, to be shown together.
    t_df: Mapped[int | None] = mapped_column(Integer)
    p_value_description: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        ForeignKeyConstraint(["analysis_set_id", "run_id"], ["analysis_set.id", "analysis_set.run_id"],
                             name="fk_analysis_result_analysis_set"),
        UniqueConstraint("id", "run_id"),
        Index("uq_analysis_result_scope", "run_id", "scope", "analysis_set_id", "source_id",
              unique=True, postgresql_nulls_not_distinct=True),
        CheckConstraint(one_of("scope", SCOPES), name="scope"),
        CheckConstraint("(scope = 'per_source') = (source_id IS NOT NULL)", name="source_iff_per_source"),
        CheckConstraint(f"label IS NULL OR {one_of('label', LABELS)}", name="label"),
        CheckConstraint("n_records >= 0 AND n_alloys >= 0 AND n_groups >= 0", name="counts_not_negative"),
        # Each counted alloy has records at two or more grain sizes, so at least two records.
        CheckConstraint("n_records >= 2 * n_alloys", name="two_records_per_alloy"),
        CheckConstraint("n_groups <= n_records", name="groups_within_records"),
        CheckConstraint("n_records = 0 OR n_groups >= 1", name="records_have_a_group"),
        CheckConstraint("resid_df = n_records - n_alloys - 1", name="resid_df_definition"),
        CheckConstraint("check1_passed = (n_alloys >= 1)", name="check1_consistent"),
        CheckConstraint(f"NOT check2_passed OR (check1_passed AND {COUNTS_ALLOW} AND {SPREAD})",
                        name="check2_consistent"),
        CheckConstraint("effective_papers IS NULL OR effective_papers >= 0", name="effective_papers"),
        CheckConstraint(f"p_value_description IS NULL OR p_value_description = '{P_VALUE_DESCRIPTION}'",
                        name="p_value_description"),
        CheckConstraint("(t_df IS NULL) = (p_value IS NULL) AND (p_value_description IS NULL) = (p_value IS NULL) "
                        "AND (p_value IS NULL OR (t_df = n_groups_informative - 1 AND effective_papers IS NOT NULL "
                        "AND largest_paper_share IS NOT NULL))", name="reported_together"),
        CheckConstraint("largest_paper_share IS NULL OR (largest_paper_share > 0 AND largest_paper_share <= 1)",
                        name="largest_paper_share"),
        CheckConstraint("n_groups_informative BETWEEN 0 AND n_groups", name="informative_within_groups"),
        CheckConstraint("inference_reason IS NULL OR " + one_of("inference_reason", INFERENCE_REASONS),
                        name="inference_reason_value"),
        CheckConstraint("(inference_reason IS NULL) = check2_passed "
                        "AND (inference_reason IS NOT DISTINCT FROM 'coefficient_not_fitted') = NOT check1_passed "
                        f"AND (inference_reason IS DISTINCT FROM 'insufficient_groups' OR NOT {COUNTS_ALLOW}) "
                        f"AND (inference_reason IS DISTINCT FROM 'evidence_concentrated' OR ({COUNTS_ALLOW} AND NOT "
                        f"{SPREAD})) "
                        f"AND (inference_reason IS DISTINCT FROM 'uncertainty_not_estimable' OR ({COUNTS_ALLOW} AND "
                        f"{SPREAD}))",
                        name="inference_reason"),
        CheckConstraint("label_reason IS NULL OR " + one_of("label_reason", LABEL_REASONS), name="label_reason_value"),
        CheckConstraint("(label_reason IS NOT NULL) = (label IS NOT DISTINCT FROM 'not_enough_data')",
                        name="label_reason"),
        CheckConstraint("estimated_power_estimated_noise IS NULL OR (check2_passed AND NOT withheld "
                        "AND estimated_power_estimated_noise BETWEEN 0 AND 1)", name="power_estimated_noise"),
        CheckConstraint("(check1_passed AND NOT withheld) = (estimate IS NOT NULL)", name="estimate_iff_check1"),
        CheckConstraint("(check2_passed AND NOT withheld) = (std_error IS NOT NULL)", name="std_error_iff_check2"),
        CheckConstraint("(check2_passed AND NOT withheld) = (p_value IS NOT NULL)", name="p_value_iff_check2"),
        CheckConstraint("withheld IS NOT NULL", name="withheld_set"),
        CheckConstraint("n_records_not_used >= 0", name="not_used_not_negative"),
        CheckConstraint(f"test_run_label IS NULL OR test_run_label = '{TEST_RUN_LABEL}'", name="test_run_label"),
        CheckConstraint("label IS NULL OR scope = 'per_source'", name="label_per_source_only"),
        CheckConstraint("estimated_power IS NULL OR check2_passed", name="power_needs_check2"),
        CheckConstraint("std_error IS NULL OR std_error >= 0", name="std_error_not_negative"),
        CheckConstraint("p_value IS NULL OR p_value BETWEEN 0 AND 1", name="p_value_range"),
        CheckConstraint("estimated_power IS NULL OR estimated_power BETWEEN 0 AND 1", name="power_range"),
    )


CALIBRATION_REASONS = ("no_dataset_frozen", "coefficient_not_fitted", "insufficient_groups",
                       "below_minimums", "scatter_not_estimable", "shift_not_estimable",  # step 7
                       "uncertainty_not_estimable", "evidence_concentrated")  # step 7 review fixes
CALIBRATION_METHODS = ("fixed", "estimated")
CALIBRATION_NUMBERS = ("assumptions", "n_simulations", "seed", "null_share", "null_ci_low", "null_ci_high",
                       "effect_share", "effect_ci_low", "effect_ci_high", "confidence_flag")


class CalibrationResult(Base):
    """PRD 5.10, for a run (analysis_result_id NULL) and for each analysis. A flag, not a gate."""
    __tablename__ = "calibration_result"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    analysis_result_id: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    assumptions: Mapped[dict | None] = mapped_column(JSONB)
    n_simulations: Mapped[int | None] = mapped_column(Integer)
    seed: Mapped[int | None] = mapped_column(BigInteger)
    null_share: Mapped[float | None] = mapped_column(Double)
    null_ci_low: Mapped[float | None] = mapped_column(Double)
    null_ci_high: Mapped[float | None] = mapped_column(Double)
    effect_share: Mapped[float | None] = mapped_column(Double)
    effect_ci_low: Mapped[float | None] = mapped_column(Double)
    effect_ci_high: Mapped[float | None] = mapped_column(Double)
    confidence_flag: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created()
    # Step 7 (migration 0004): both methods per analysis; the test-run label.
    method: Mapped[str | None] = mapped_column(Text)
    test_run_label: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        ForeignKeyConstraint(["analysis_result_id", "run_id"], ["analysis_result.id", "analysis_result.run_id"],
                             name="fk_calibration_result_analysis_result"),
        Index("uq_calibration_result_scope", "run_id", "analysis_result_id", "method",
              unique=True, postgresql_nulls_not_distinct=True),
        CheckConstraint("method IS NULL OR " + one_of("method", CALIBRATION_METHODS), name="method"),
        CheckConstraint("(method IS NULL) = (analysis_result_id IS NULL)", name="method_iff_analysis"),
        CheckConstraint(f"test_run_label IS NULL OR test_run_label = '{TEST_RUN_LABEL}'", name="test_run_label"),
        CheckConstraint(one_of("status", ("computed", "unavailable")), name="status"),
        CheckConstraint(f"reason IS NULL OR {one_of('reason', CALIBRATION_REASONS)}", name="reason"),
        CheckConstraint("confidence_flag IS NULL OR "
                        + one_of("confidence_flag", ("none", "over_confident", "under_confident")),
                        name="confidence_flag"),
        CheckConstraint("status <> 'computed' OR (reason IS NULL AND "
                        + " AND ".join(f"{c} IS NOT NULL" for c in CALIBRATION_NUMBERS) + ")",
                        name="computed_is_complete"),
        CheckConstraint("status <> 'unavailable' OR (reason IS NOT NULL AND "
                        + " AND ".join(f"{c} IS NULL" for c in CALIBRATION_NUMBERS) + ")",
                        name="unavailable_has_reason_only"),
        # Calibration attaches to an analysis; a run-level row exists only when no dataset was frozen.
        CheckConstraint("(analysis_result_id IS NULL) = (reason IS NOT DISTINCT FROM 'no_dataset_frozen')",
                        name="run_level_only_without_freeze"),
        CheckConstraint("n_simulations IS NULL OR n_simulations >= 1", name="simulations_positive"),
        CheckConstraint("null_share IS NULL OR (0 <= null_ci_low AND null_ci_low <= null_share "
                        "AND null_share <= null_ci_high AND null_ci_high <= 1)", name="null_interval"),
        CheckConstraint("effect_share IS NULL OR (0 <= effect_ci_low AND effect_ci_low <= effect_share "
                        "AND effect_share <= effect_ci_high AND effect_ci_high <= 1)", name="effect_interval"),
    )


class Commentary(Base):
    """The Commentator's text (PRD 5.9). Tokens and cost come from its stage's model calls."""
    __tablename__ = "commentary"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"), unique=True)
    stage_result_id: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(Text)
    text: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str] = mapped_column(Text)
    number_check: Mapped[str | None] = mapped_column(Text)
    mismatches: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        ForeignKeyConstraint(["stage_result_id", "run_id"], ["stage_result.id", "stage_result.run_id"],
                             name="fk_commentary_stage_result"),
        CheckConstraint(one_of("status", ("written", "unavailable")), name="status"),
        CheckConstraint("(status = 'written') = (text IS NOT NULL AND number_check IS NOT NULL)",
                        name="written_has_text_and_check"),
        CheckConstraint("number_check IS NULL OR " + one_of("number_check", ("all_match", "mismatches")),
                        name="number_check"),
        CheckConstraint("(number_check IS NOT DISTINCT FROM 'mismatches') = (mismatches IS NOT NULL)",
                        name="mismatches_listed"),
    )


class Artifact(Base):
    """Plots and workbooks for a run (at most 5 MiB each), written while the run is
    running or after it completed, never for a failed run. Append-only."""
    __tablename__ = "artifact"
    id: Mapped[int] = pk()
    run_id: Mapped[int] = mapped_column(ForeignKey("run.id"))
    kind: Mapped[str] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(Text)
    media_type: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(Text)
    content: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = created()
    __table_args__ = (
        CheckConstraint(one_of("kind", ("plot", "workbook", "csv")), name="kind"),
        CheckConstraint(f"octet_length(content) <= {MAX_FILE_BYTES}", name="max_size"),
        CheckConstraint("sha256 = encode(sha256(content), 'hex')", name="sha256_matches_content"),
    )


class AuditLog(Base):
    """Every data read and every denied call (PRD 4). Append-only. Written by the
    access layer (step 5)."""
    __tablename__ = "audit_log"
    id: Mapped[int] = pk()
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=now())
    run_id: Mapped[int | None] = mapped_column(ForeignKey("run.id"))
    role: Mapped[str] = mapped_column(Text)
    stage: Mapped[str] = mapped_column(Text)
    function: Mapped[str] = mapped_column(Text)
    allowed: Mapped[bool] = mapped_column(Boolean)
    detail: Mapped[dict | None] = mapped_column(JSONB)
    __table_args__ = (Index("ix_audit_log_run_id", "run_id"),)
