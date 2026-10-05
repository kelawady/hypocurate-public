"""Data model (build step 3): the tables of PRD Section 7 and the rules the database enforces.

Revision ID: 0001
Revises:
Create Date: 2026-10-05

The CREATE TABLE statements were rendered by Alembic autogenerate from
`hypocurate/db/models.py` and then reviewed and edited by hand (sequence and the
hypothesis -> run foreign key moved; long names shortened). The trigger
functions, triggers, views and the seed rows below are hand-written. The models
are not imported here, so this migration stays as it was when it was written.

Every trigger rejection raises SQLSTATE 23514 (check_violation) with a message
starting "hypocurate: ".

Rules for every migration (README, "Database migrations"): it runs inside the one
upgrade transaction (no CONCURRENTLY, no autocommit_block); it keeps working with
the previous release's code; and it has a downgrade.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('agent_setting',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('instruction', sa.Text(), nullable=False),
    sa.Column('model', sa.Text(), nullable=False),
    sa.Column('limits', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("role IN ('planner', 'curator', 'critic', 'analyst', 'commentator')", name=op.f('ck_agent_setting_role')),
    sa.CheckConstraint('version >= 1', name=op.f('ck_agent_setting_version_positive')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_agent_setting')),
    sa.UniqueConstraint('id', 'role', name=op.f('uq_agent_setting_id_role')),
    sa.UniqueConstraint('role', 'version', name=op.f('uq_agent_setting_role_version'))
    )
    op.create_table('domain',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('key', sa.Text(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('supported', sa.Boolean(), nullable=False),
    sa.Column('profile_name', sa.Text(), nullable=True),
    sa.CheckConstraint('NOT supported OR profile_name IS NOT NULL', name=op.f('ck_domain_supported_has_profile')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_domain')),
    sa.UniqueConstraint('key', name=op.f('uq_domain_key'))
    )
    op.execute("CREATE SEQUENCE hypothesis_number_seq")
    op.create_table('hypothesis',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('number', sa.Text(), server_default=sa.text("'Q-' || lpad(nextval('hypothesis_number_seq')::text, 4, '0')"), nullable=False),
    sa.Column('narrower_of_run_id', sa.BigInteger(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_hypothesis')),
    sa.UniqueConstraint('number', name=op.f('uq_hypothesis_number'))
    )
    op.create_table('source',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('key', sa.Text(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('source_type', sa.Text(), nullable=False),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('licence', sa.Text(), nullable=False),
    sa.Column('data_kind', sa.Text(), nullable=False),
    sa.Column('adapter_status', sa.Text(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=False),
    sa.Column('grouping_unit', sa.Text(), nullable=False),
    sa.Column('properties_covered', sa.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("adapter_status IN ('adapter_needed', 'available')", name=op.f('ck_source_adapter_status')),
    sa.CheckConstraint("data_kind IN ('measured', 'computed', 'model_recalled')", name=op.f('ck_source_data_kind')),
    sa.CheckConstraint("grouping_unit IN ('paper', 'dataset', 'batch')", name=op.f('ck_source_grouping_unit')),
    sa.CheckConstraint("key ~ '^[a-z0-9_]+$'", name=op.f('ck_source_key_format')),
    sa.CheckConstraint("source_type IN ('uploaded_table', 'web_interface', 'paper_search', 'model_recall')", name=op.f('ck_source_source_type')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_source')),
    sa.UniqueConstraint('key', name=op.f('uq_source_key'))
    )
    op.create_table('hypothesis_version',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('hypothesis_id', sa.BigInteger(), nullable=False),
    sa.Column('version_number', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('domain_id', sa.BigInteger(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), server_default=sa.text("'draft'"), nullable=False),
    sa.Column('confirmed_domain_id', sa.BigInteger(), nullable=True),
    sa.Column('domain_confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('review_comment', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('returned_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("status <> 'dispatched' OR (confirmed_domain_id IS NOT NULL AND dispatched_at IS NOT NULL)", name=op.f('ck_hypothesis_version_dispatch_needs_confirmed_domain')),
    sa.CheckConstraint("status <> 'returned' OR returned_at IS NOT NULL", name=op.f('ck_hypothesis_version_returned_time')),
    sa.CheckConstraint("status = 'draft' OR submitted_at IS NOT NULL", name=op.f('ck_hypothesis_version_submitted_time')),
    sa.CheckConstraint("status IN ('draft', 'submitted', 'returned', 'dispatched')", name=op.f('ck_hypothesis_version_status')),
    sa.CheckConstraint('(confirmed_domain_id IS NULL) = (domain_confirmed_at IS NULL)', name=op.f('ck_hypothesis_version_confirmed_domain_with_time')),
    sa.CheckConstraint('length(btrim(text)) > 0', name=op.f('ck_hypothesis_version_text_not_empty')),
    sa.CheckConstraint('version_number >= 1', name=op.f('ck_hypothesis_version_version_positive')),
    sa.ForeignKeyConstraint(['confirmed_domain_id'], ['domain.id'], name=op.f('fk_hypothesis_version_confirmed_domain_id')),
    sa.ForeignKeyConstraint(['domain_id'], ['domain.id'], name=op.f('fk_hypothesis_version_domain_id')),
    sa.ForeignKeyConstraint(['hypothesis_id'], ['hypothesis.id'], name=op.f('fk_hypothesis_version_hypothesis_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_hypothesis_version')),
    sa.UniqueConstraint('hypothesis_id', 'version_number', name=op.f('uq_hypothesis_version_hypothesis_id_version_number'))
    )
    op.create_table('source_version',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('source_id', sa.BigInteger(), nullable=False),
    sa.Column('label', sa.Text(), nullable=False),
    sa.Column('obtained_on', sa.Date(), nullable=False),
    sa.Column('source_type', sa.Text(), nullable=False),
    sa.Column('data_kind', sa.Text(), nullable=False),
    sa.Column('grouping_unit', sa.Text(), nullable=False),
    sa.Column('sealed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('files_digest', sa.Text(), nullable=True),
    sa.Column('fingerprint', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_source_version_fingerprint_format')),
    sa.CheckConstraint('(sealed_at IS NULL) = (fingerprint IS NULL)', name=op.f('ck_source_version_sealed_with_fingerprint')),
    sa.CheckConstraint("files_digest ~ '^[0-9a-f]{64}$'", name=op.f('ck_source_version_files_digest_format')),
    sa.CheckConstraint('(sealed_at IS NULL) = (files_digest IS NULL)', name=op.f('ck_source_version_sealed_with_files_digest')),
    sa.CheckConstraint("source_type IN ('uploaded_table', 'web_interface', 'paper_search', 'model_recall')", name=op.f('ck_source_version_source_type')),
    sa.CheckConstraint("data_kind IN ('measured', 'computed', 'model_recalled')", name=op.f('ck_source_version_data_kind')),
    sa.CheckConstraint("grouping_unit IN ('paper', 'dataset', 'batch')", name=op.f('ck_source_version_grouping_unit')),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], name=op.f('fk_source_version_source_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_source_version')),
    sa.UniqueConstraint('id', 'source_id', name=op.f('uq_source_version_id_source_id')),
    sa.UniqueConstraint('source_id', 'fingerprint', name=op.f('uq_source_version_source_id_fingerprint'))
    )
    op.create_table('hypothesis_version_source',
    sa.Column('hypothesis_version_id', sa.BigInteger(), nullable=False),
    sa.Column('source_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['hypothesis_version_id'], ['hypothesis_version.id'], name=op.f('fk_hypothesis_version_source_hypothesis_version_id')),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], name=op.f('fk_hypothesis_version_source_source_id')),
    sa.PrimaryKeyConstraint('hypothesis_version_id', 'source_id', name=op.f('pk_hypothesis_version_source'))
    )
    op.create_table('run',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('hypothesis_version_id', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.Text(), server_default=sa.text("'queued'"), nullable=False),
    sa.Column('current_stage', sa.Text(), nullable=True),
    sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('outcome', sa.Text(), nullable=True),
    sa.Column('verdict', sa.Text(), nullable=True),
    sa.Column('exploratory', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('failure_reason', sa.Text(), nullable=True),
    sa.Column('agent_mode', sa.Text(), server_default=sa.text("'four_roles'"), nullable=False),
    sa.Column('fixed_plan', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('experiment_flags', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('queued_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("(outcome IS NOT NULL) = (status = 'completed')", name=op.f('ck_run_outcome_iff_completed')),
    sa.CheckConstraint("(status = 'failed') = (failure_reason IS NOT NULL)", name=op.f('ck_run_failed_has_reason')),
    sa.CheckConstraint("(verdict IS NOT NULL) = (status = 'completed' AND outcome IS NOT DISTINCT FROM 'sufficient')", name=op.f('ck_run_verdict_iff_sufficient')),
    sa.CheckConstraint("agent_mode = 'four_roles'", name=op.f('ck_run_agent_mode')),
    sa.CheckConstraint("outcome IS NULL OR outcome IN ('sufficient', 'partly_sufficient', 'insufficient')", name=op.f('ck_run_outcome')),
    sa.CheckConstraint("status <> 'completed' OR completed_at IS NOT NULL", name=op.f('ck_run_completed_time')),
    sa.CheckConstraint("status <> 'failed' OR failed_at IS NOT NULL", name=op.f('ck_run_failed_time')),
    sa.CheckConstraint("status = 'queued' OR started_at IS NOT NULL OR status = 'failed'", name=op.f('ck_run_started_time')),
    sa.CheckConstraint("status IN ('queued', 'running', 'completed', 'failed')", name=op.f('ck_run_status')),
    sa.CheckConstraint("verdict IS NULL OR verdict IN ('supported', 'not_supported')", name=op.f('ck_run_verdict')),
    sa.CheckConstraint('NOT exploratory OR verdict IS NOT NULL', name=op.f('ck_run_exploratory_needs_verdict')),
    sa.ForeignKeyConstraint(['hypothesis_version_id'], ['hypothesis_version.id'], name=op.f('fk_run_hypothesis_version_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_run'))
    )
    op.create_foreign_key(op.f('fk_hypothesis_narrower_of_run_id'), 'hypothesis', 'run', ['narrower_of_run_id'], ['id'])
    op.create_table('source_file',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('source_version_id', sa.BigInteger(), nullable=False),
    sa.Column('path', sa.Text(), nullable=False),
    sa.Column('sha256', sa.Text(), nullable=False),
    sa.Column('content', sa.LargeBinary(), nullable=False),
    sa.CheckConstraint("path ~ '^[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)$'", name=op.f('ck_source_file_safe_data_file_path')),
    sa.CheckConstraint("sha256 = encode(sha256(content), 'hex')", name=op.f('ck_source_file_sha256_matches_content')),
    sa.CheckConstraint('octet_length(content) <= 5242880', name=op.f('ck_source_file_max_size')),
    sa.ForeignKeyConstraint(['source_version_id'], ['source_version.id'], name=op.f('fk_source_file_source_version_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_source_file')),
    sa.UniqueConstraint('source_version_id', 'path', name=op.f('uq_source_file_source_version_id_path'))
    )
    op.create_table('analysis_set',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('key', sa.Text(), nullable=False),
    sa.CheckConstraint("key ~ '^[a-z0-9_]+$'", name=op.f('ck_analysis_set_key_format')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_analysis_set_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_analysis_set')),
    sa.UniqueConstraint('id', 'run_id', name=op.f('uq_analysis_set_id_run_id')),
    sa.UniqueConstraint('run_id', 'key', name=op.f('uq_analysis_set_run_id_key'))
    )
    op.create_table('artifact',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('kind', sa.Text(), nullable=False),
    sa.Column('filename', sa.Text(), nullable=False),
    sa.Column('media_type', sa.Text(), nullable=False),
    sa.Column('sha256', sa.Text(), nullable=False),
    sa.Column('content', sa.LargeBinary(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("kind IN ('plot', 'workbook', 'csv')", name=op.f('ck_artifact_kind')),
    sa.CheckConstraint("sha256 = encode(sha256(content), 'hex')", name=op.f('ck_artifact_sha256_matches_content')),
    sa.CheckConstraint('octet_length(content) <= 5242880', name=op.f('ck_artifact_max_size')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_artifact_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_artifact'))
    )
    op.create_table('audit_log',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=True),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('stage', sa.Text(), nullable=False),
    sa.Column('function', sa.Text(), nullable=False),
    sa.Column('allowed', sa.Boolean(), nullable=False),
    sa.Column('detail', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_audit_log_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_log'))
    )
    op.create_index('ix_audit_log_run_id', 'audit_log', ['run_id'], unique=False)
    op.create_table('flag',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('kind', sa.Text(), nullable=False),
    sa.Column('category', sa.Text(), nullable=False),
    sa.Column('compared_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('raised_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('critic_class', sa.Text(), nullable=True),
    sa.Column('critic_reason', sa.Text(), nullable=True),
    sa.Column('classified_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('(critic_class IS NULL) = (classified_at IS NULL)', name=op.f('ck_flag_classified_time')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_flag_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_flag'))
    )
    op.create_table('plan',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('fingerprint', sa.Text(), nullable=False),
    sa.Column('locked_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('sufficiency_option', sa.Text(), nullable=False),
    sa.Column('min_records', sa.Integer(), nullable=False),
    sa.Column('min_alloys', sa.Integer(), nullable=False),
    sa.Column('min_groups', sa.Integer(), nullable=False),
    sa.Column('min_resid_df', sa.Integer(), nullable=False),
    sa.Column('sensitivity_analysis_keys', sa.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('power_assumptions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.CheckConstraint("NOT ('primary' = ANY (sensitivity_analysis_keys))", name=op.f('ck_plan_primary_not_sensitivity')),
    sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_plan_fingerprint_format')),
    sa.CheckConstraint("sufficiency_option IN ('fixed_minimum', 'use_available')", name=op.f('ck_plan_sufficiency_option')),
    sa.CheckConstraint('min_records >= 1 AND min_alloys >= 1 AND min_groups >= 1 AND min_resid_df >= 1', name=op.f('ck_plan_minimums_positive')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_plan_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_plan')),
    sa.UniqueConstraint('run_id', name=op.f('uq_plan_run_id'))
    )
    op.create_table('record',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('extraction_run_id', sa.BigInteger(), nullable=False),
    sa.Column('source_version_id', sa.BigInteger(), nullable=False),
    sa.Column('source_item_key', sa.Text(), nullable=False),
    sa.Column('item_index', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('kind', sa.Text(), nullable=False),
    sa.Column('alloy', sa.Text(), nullable=True),
    sa.Column('harmonized', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('reported', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('paper_reference', sa.Text(), nullable=True),
    sa.Column('paper_doi', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("kind IN ('measured', 'computed', 'model_recalled')", name=op.f('ck_record_kind')),
    sa.CheckConstraint('item_index >= 0', name=op.f('ck_record_item_index_not_negative')),
    sa.CheckConstraint('length(source_item_key) > 0', name=op.f('ck_record_item_key_not_empty')),
    sa.ForeignKeyConstraint(['extraction_run_id'], ['run.id'], name=op.f('fk_record_extraction_run_id')),
    sa.ForeignKeyConstraint(['source_version_id'], ['source_version.id'], name=op.f('fk_record_source_version_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_record')),
    sa.UniqueConstraint('extraction_run_id', 'source_version_id', 'source_item_key', 'item_index', name='uq_record_origin_per_run')
    )
    op.create_index('ix_record_source_version_id_source_item_key', 'record', ['source_version_id', 'source_item_key'], unique=False)
    op.create_table('run_agent_setting',
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('agent_setting_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['agent_setting_id', 'role'], ['agent_setting.id', 'agent_setting.role'], name='fk_run_agent_setting_agent_setting'),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_agent_setting_run_id')),
    sa.PrimaryKeyConstraint('run_id', 'role', name=op.f('pk_run_agent_setting'))
    )
    op.create_table('run_snapshot',
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('fingerprint', sa.Text(), nullable=False),
    sa.Column('frozen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('n_records', sa.Integer(), nullable=False),
    sa.CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name=op.f('ck_run_snapshot_fingerprint_format')),
    sa.CheckConstraint('n_records >= 1', name=op.f('ck_run_snapshot_not_empty')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_snapshot_run_id')),
    sa.PrimaryKeyConstraint('run_id', name=op.f('pk_run_snapshot'))
    )
    op.create_table('run_source',
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('source_id', sa.BigInteger(), nullable=False),
    sa.Column('source_version_id', sa.BigInteger(), nullable=True),
    sa.Column('search_status', sa.Text(), nullable=False),
    sa.Column('nothing_found', sa.Text(), nullable=True),
    sa.Column('failure_reason', sa.Text(), nullable=True),
    sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("(search_status = 'failed') = (nothing_found IS NOT DISTINCT FROM 'failed_search')", name=op.f('ck_run_source_failed_iff_failed_search')),
    sa.CheckConstraint("(search_status IN ('searched', 'failed')) = (decided_at IS NOT NULL)", name=op.f('ck_run_source_decided_time')),
    sa.CheckConstraint("nothing_found IS NULL OR nothing_found IN ('reported_negative', 'missing_evidence', 'failed_search')", name=op.f('ck_run_source_nothing_found')),
    sa.CheckConstraint("search_status <> 'failed' OR failure_reason IS NOT NULL", name=op.f('ck_run_source_failed_has_reason')),
    sa.CheckConstraint("search_status <> 'not_selected' OR source_version_id IS NULL", name=op.f('ck_run_source_not_selected_no_version')),
    sa.CheckConstraint("search_status <> 'searched' OR source_version_id IS NOT NULL", name=op.f('ck_run_source_searched_has_version')),
    sa.CheckConstraint("search_status IN ('not_selected', 'pending', 'searched', 'failed')", name=op.f('ck_run_source_search_status')),
    sa.CheckConstraint("search_status NOT IN ('not_selected', 'pending') OR nothing_found IS NULL", name=op.f('ck_run_source_undecided_has_no_kind')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_source_run_id')),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], name=op.f('fk_run_source_source_id')),
    sa.ForeignKeyConstraint(['source_version_id', 'source_id'], ['source_version.id', 'source_version.source_id'], name='fk_run_source_source_version'),
    sa.PrimaryKeyConstraint('run_id', 'source_id', name=op.f('pk_run_source'))
    )
    op.create_table('stage_result',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('stage', sa.Text(), nullable=False),
    sa.Column('attempt', sa.Integer(), server_default=sa.text('1'), nullable=False),
    sa.Column('role', sa.Text(), nullable=True),
    sa.Column('status', sa.Text(), server_default=sa.text("'running'"), nullable=False),
    sa.Column('input', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('output', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('reasoning', sa.Text(), nullable=True),
    sa.Column('tool_calls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('agent_setting_id', sa.BigInteger(), nullable=True),
    sa.Column('model', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("(status = 'running') = (finished_at IS NULL)", name=op.f('ck_stage_result_finished_time')),
    sa.CheckConstraint("role IS NULL OR role IN ('planner', 'curator', 'critic', 'analyst', 'commentator')", name=op.f('ck_stage_result_role')),
    sa.CheckConstraint("stage ~ '^[a-z_]+$'", name=op.f('ck_stage_result_stage_format')),
    sa.CheckConstraint("status IN ('running', 'done', 'failed', 'skipped')", name=op.f('ck_stage_result_status')),
    sa.CheckConstraint('attempt >= 1', name=op.f('ck_stage_result_attempt_positive')),
    sa.ForeignKeyConstraint(['agent_setting_id'], ['agent_setting.id'], name=op.f('fk_stage_result_agent_setting_id')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_stage_result_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_stage_result')),
    sa.UniqueConstraint('id', 'run_id', name=op.f('uq_stage_result_id_run_id')),
    sa.UniqueConstraint('run_id', 'stage', 'attempt', name=op.f('uq_stage_result_run_id_stage_attempt'))
    )
    op.create_table('tag_value',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('kind', sa.Text(), nullable=False),
    sa.Column('value', sa.Text(), nullable=False),
    sa.Column('status', sa.Text(), nullable=False),
    sa.Column('proposed_by_run_id', sa.BigInteger(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("(status = 'proposed') = (decided_at IS NULL)", name=op.f('ck_tag_value_decided_once')),
    sa.CheckConstraint("kind IN ('property', 'alloy_class', 'test_condition')", name=op.f('ck_tag_value_kind')),
    sa.CheckConstraint("status IN ('proposed', 'approved', 'rejected')", name=op.f('ck_tag_value_status')),
    sa.CheckConstraint('length(value) > 0', name=op.f('ck_tag_value_value_not_empty')),
    sa.ForeignKeyConstraint(['proposed_by_run_id'], ['run.id'], name=op.f('fk_tag_value_proposed_by_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tag_value')),
    sa.UniqueConstraint('kind', 'value', name=op.f('uq_tag_value_kind_value'))
    )
    op.create_table('analysis_result',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('scope', sa.Text(), nullable=False),
    sa.Column('analysis_set_id', sa.BigInteger(), nullable=False),
    sa.Column('source_id', sa.BigInteger(), nullable=True),
    sa.Column('n_records', sa.Integer(), nullable=False),
    sa.Column('n_alloys', sa.Integer(), nullable=False),
    sa.Column('n_groups', sa.Integer(), nullable=False),
    sa.Column('resid_df', sa.Integer(), nullable=False),
    sa.Column('check1_passed', sa.Boolean(), nullable=False),
    sa.Column('check2_passed', sa.Boolean(), nullable=False),
    sa.Column('minimums_met', sa.Boolean(), nullable=False),
    sa.Column('estimate', sa.Double(), nullable=True),
    sa.Column('std_error', sa.Double(), nullable=True),
    sa.Column('p_value', sa.Double(), nullable=True),
    sa.Column('estimated_power', sa.Double(), nullable=True),
    sa.Column('label', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("(scope = 'per_source') = (source_id IS NOT NULL)", name=op.f('ck_analysis_result_source_iff_per_source')),
    sa.CheckConstraint("label IS NULL OR label IN ('agrees', 'conflicts', 'not_enough_data')", name=op.f('ck_analysis_result_label')),
    sa.CheckConstraint("scope IN ('pooled', 'per_source', 'sensitivity')", name=op.f('ck_analysis_result_scope')),
    sa.CheckConstraint('check1_passed = (estimate IS NOT NULL)', name=op.f('ck_analysis_result_estimate_iff_check1')),
    sa.CheckConstraint('check1_passed = (n_alloys >= 1)', name=op.f('ck_analysis_result_check1_consistent')),
    sa.CheckConstraint('check2_passed = (check1_passed AND resid_df >= 1 AND n_groups >= 2)', name=op.f('ck_analysis_result_check2_consistent')),
    sa.CheckConstraint('n_records >= 2 * n_alloys', name=op.f('ck_analysis_result_two_records_per_alloy')),
    sa.CheckConstraint('n_groups <= n_records', name=op.f('ck_analysis_result_groups_within_records')),
    sa.CheckConstraint('n_records = 0 OR n_groups >= 1', name=op.f('ck_analysis_result_records_have_a_group')),
    sa.CheckConstraint('check2_passed = (p_value IS NOT NULL)', name=op.f('ck_analysis_result_p_value_iff_check2')),
    sa.CheckConstraint('check2_passed = (std_error IS NOT NULL)', name=op.f('ck_analysis_result_std_error_iff_check2')),
    sa.CheckConstraint('estimated_power IS NULL OR estimated_power BETWEEN 0 AND 1', name=op.f('ck_analysis_result_power_range')),
    sa.CheckConstraint('n_records >= 0 AND n_alloys >= 0 AND n_groups >= 0', name=op.f('ck_analysis_result_counts_not_negative')),
    sa.CheckConstraint('p_value IS NULL OR p_value BETWEEN 0 AND 1', name=op.f('ck_analysis_result_p_value_range')),
    sa.CheckConstraint('resid_df = n_records - n_alloys - 1', name=op.f('ck_analysis_result_resid_df_definition')),
    sa.CheckConstraint('std_error IS NULL OR std_error >= 0', name=op.f('ck_analysis_result_std_error_not_negative')),
    sa.ForeignKeyConstraint(['analysis_set_id', 'run_id'], ['analysis_set.id', 'analysis_set.run_id'], name='fk_analysis_result_analysis_set'),
    sa.ForeignKeyConstraint(['source_id'], ['source.id'], name=op.f('fk_analysis_result_source_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_analysis_result')),
    sa.UniqueConstraint('id', 'run_id', name=op.f('uq_analysis_result_id_run_id'))
    )
    op.create_index('uq_analysis_result_scope', 'analysis_result', ['run_id', 'scope', 'analysis_set_id', 'source_id'], unique=True, postgresql_nulls_not_distinct=True)
    op.create_table('analysis_set_record',
    sa.Column('analysis_set_id', sa.BigInteger(), nullable=False),
    sa.Column('record_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['analysis_set_id'], ['analysis_set.id'], name=op.f('fk_analysis_set_record_analysis_set_id')),
    sa.ForeignKeyConstraint(['record_id'], ['record.id'], name=op.f('fk_analysis_set_record_record_id')),
    sa.PrimaryKeyConstraint('analysis_set_id', 'record_id', name=op.f('pk_analysis_set_record'))
    )
    op.create_table('commentary',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('stage_result_id', sa.BigInteger(), nullable=False),
    sa.Column('status', sa.Text(), nullable=False),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('model', sa.Text(), nullable=False),
    sa.Column('number_check', sa.Text(), nullable=True),
    sa.Column('mismatches', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("(number_check IS NOT DISTINCT FROM 'mismatches') = (mismatches IS NOT NULL)", name=op.f('ck_commentary_mismatches_listed')),
    sa.CheckConstraint("(status = 'written') = (text IS NOT NULL AND number_check IS NOT NULL)", name=op.f('ck_commentary_written_has_text_and_check')),
    sa.CheckConstraint("number_check IS NULL OR number_check IN ('all_match', 'mismatches')", name=op.f('ck_commentary_number_check')),
    sa.CheckConstraint("status IN ('written', 'unavailable')", name=op.f('ck_commentary_status')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_commentary_run_id')),
    sa.ForeignKeyConstraint(['stage_result_id', 'run_id'], ['stage_result.id', 'stage_result.run_id'], name='fk_commentary_stage_result'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_commentary')),
    sa.UniqueConstraint('run_id', name=op.f('uq_commentary_run_id'))
    )
    op.create_table('flag_record',
    sa.Column('flag_id', sa.BigInteger(), nullable=False),
    sa.Column('record_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['flag_id'], ['flag.id'], name=op.f('fk_flag_record_flag_id')),
    sa.ForeignKeyConstraint(['record_id'], ['record.id'], name=op.f('fk_flag_record_record_id')),
    sa.PrimaryKeyConstraint('flag_id', 'record_id', name=op.f('pk_flag_record'))
    )
    op.create_table('model_call',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('stage_result_id', sa.BigInteger(), nullable=False),
    sa.Column('role', sa.Text(), nullable=False),
    sa.Column('model', sa.Text(), nullable=False),
    sa.Column('price_table_version', sa.Text(), nullable=False),
    sa.Column('max_cost', sa.Numeric(), nullable=False),
    sa.Column('status', sa.Text(), server_default=sa.text("'started'"), nullable=False),
    sa.Column('input_tokens', sa.BigInteger(), nullable=True),
    sa.Column('output_tokens', sa.BigInteger(), nullable=True),
    sa.Column('cached_tokens', sa.BigInteger(), nullable=True),
    sa.Column('cost', sa.Numeric(), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("role IN ('planner', 'curator', 'critic', 'analyst', 'commentator')", name=op.f('ck_model_call_role')),
    sa.CheckConstraint("status <> 'failed' OR (finished_at IS NOT NULL AND ((input_tokens IS NULL AND output_tokens IS NULL AND cached_tokens IS NULL AND cost IS NULL) OR (input_tokens IS NOT NULL AND output_tokens IS NOT NULL AND cached_tokens IS NOT NULL AND cost IS NOT NULL)))", name=op.f('ck_model_call_failed_usage_all_or_none')),
    sa.CheckConstraint("status <> 'interrupted' OR (input_tokens IS NULL AND output_tokens IS NULL AND cached_tokens IS NULL AND cost IS NULL AND finished_at IS NOT NULL)", name=op.f('ck_model_call_interrupted_has_no_usage')),
    sa.CheckConstraint("status <> 'started' OR (input_tokens IS NULL AND output_tokens IS NULL AND cached_tokens IS NULL AND cost IS NULL AND finished_at IS NULL)", name=op.f('ck_model_call_started_has_no_usage')),
    sa.CheckConstraint("status <> 'succeeded' OR (input_tokens IS NOT NULL AND output_tokens IS NOT NULL AND cached_tokens IS NOT NULL AND cost IS NOT NULL AND finished_at IS NOT NULL)", name=op.f('ck_model_call_succeeded_has_usage')),
    sa.CheckConstraint("status IN ('started', 'succeeded', 'failed', 'interrupted')", name=op.f('ck_model_call_status')),
    sa.CheckConstraint('coalesce(input_tokens, 0) >= 0 AND coalesce(output_tokens, 0) >= 0 AND coalesce(cached_tokens, 0) >= 0 AND coalesce(cost, 0) >= 0', name=op.f('ck_model_call_usage_not_negative')),
    sa.CheckConstraint('length(model) > 0 AND length(price_table_version) > 0', name=op.f('ck_model_call_model_and_prices_named')),
    sa.CheckConstraint('max_cost > 0', name=op.f('ck_model_call_max_cost_positive')),
    sa.ForeignKeyConstraint(['stage_result_id', 'run_id'], ['stage_result.id', 'stage_result.run_id'], name='fk_model_call_stage_result'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_model_call'))
    )
    op.create_index('ix_model_call_run_id', 'model_call', ['run_id'], unique=False)
    op.create_table('run_record',
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('record_id', sa.BigInteger(), nullable=False),
    sa.Column('eligible', sa.Boolean(), nullable=False),
    sa.Column('rule', sa.Text(), nullable=False),
    sa.Column('decided_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('length(rule) > 0', name=op.f('ck_run_record_rule_named')),
    sa.ForeignKeyConstraint(['record_id'], ['record.id'], name=op.f('fk_run_record_record_id')),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_record_run_id')),
    sa.PrimaryKeyConstraint('run_id', 'record_id', name=op.f('pk_run_record'))
    )
    op.create_table('run_tag',
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('tag_value_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_run_tag_run_id')),
    sa.ForeignKeyConstraint(['tag_value_id'], ['tag_value.id'], name=op.f('fk_run_tag_tag_value_id')),
    sa.PrimaryKeyConstraint('run_id', 'tag_value_id', name=op.f('pk_run_tag'))
    )
    op.create_table('calibration_result',
    sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
    sa.Column('run_id', sa.BigInteger(), nullable=False),
    sa.Column('analysis_result_id', sa.BigInteger(), nullable=True),
    sa.Column('status', sa.Text(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('assumptions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('n_simulations', sa.Integer(), nullable=True),
    sa.Column('seed', sa.BigInteger(), nullable=True),
    sa.Column('null_share', sa.Double(), nullable=True),
    sa.Column('null_ci_low', sa.Double(), nullable=True),
    sa.Column('null_ci_high', sa.Double(), nullable=True),
    sa.Column('effect_share', sa.Double(), nullable=True),
    sa.Column('effect_ci_low', sa.Double(), nullable=True),
    sa.Column('effect_ci_high', sa.Double(), nullable=True),
    sa.Column('confidence_flag', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("confidence_flag IS NULL OR confidence_flag IN ('none', 'over_confident', 'under_confident')", name=op.f('ck_calibration_result_confidence_flag')),
    sa.CheckConstraint("reason IS NULL OR reason IN ('no_dataset_frozen', 'coefficient_not_fitted', 'insufficient_groups')", name=op.f('ck_calibration_result_reason')),
    sa.CheckConstraint("status <> 'computed' OR (reason IS NULL AND assumptions IS NOT NULL AND n_simulations IS NOT NULL AND seed IS NOT NULL AND null_share IS NOT NULL AND null_ci_low IS NOT NULL AND null_ci_high IS NOT NULL AND effect_share IS NOT NULL AND effect_ci_low IS NOT NULL AND effect_ci_high IS NOT NULL AND confidence_flag IS NOT NULL)", name=op.f('ck_calibration_result_computed_is_complete')),
    sa.CheckConstraint("status <> 'unavailable' OR (reason IS NOT NULL AND assumptions IS NULL AND n_simulations IS NULL AND seed IS NULL AND null_share IS NULL AND null_ci_low IS NULL AND null_ci_high IS NULL AND effect_share IS NULL AND effect_ci_low IS NULL AND effect_ci_high IS NULL AND confidence_flag IS NULL)", name=op.f('ck_calibration_result_unavailable_has_reason_only')),
    sa.CheckConstraint("status IN ('computed', 'unavailable')", name=op.f('ck_calibration_result_status')),
    sa.CheckConstraint('effect_share IS NULL OR (0 <= effect_ci_low AND effect_ci_low <= effect_share AND effect_share <= effect_ci_high AND effect_ci_high <= 1)', name=op.f('ck_calibration_result_effect_interval')),
    sa.CheckConstraint("(analysis_result_id IS NULL) = (reason IS NOT DISTINCT FROM 'no_dataset_frozen')", name=op.f('ck_calibration_result_run_level_only_without_freeze')),
    sa.CheckConstraint('n_simulations IS NULL OR n_simulations >= 1', name=op.f('ck_calibration_result_simulations_positive')),
    sa.CheckConstraint('null_share IS NULL OR (0 <= null_ci_low AND null_ci_low <= null_share AND null_share <= null_ci_high AND null_ci_high <= 1)', name=op.f('ck_calibration_result_null_interval')),
    sa.ForeignKeyConstraint(['analysis_result_id', 'run_id'], ['analysis_result.id', 'analysis_result.run_id'], name='fk_calibration_result_analysis_result'),
    sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_calibration_result_run_id')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_calibration_result'))
    )
    op.create_index('uq_calibration_result_scope', 'calibration_result', ['run_id', 'analysis_result_id'], unique=True, postgresql_nulls_not_distinct=True)
    for statement in FUNCTIONS + TRIGGERS + VIEWS + SEED:
        op.execute(statement)


def downgrade() -> None:
    for view in reversed(VIEW_NAMES):
        op.execute(f"DROP VIEW {view}")
    op.drop_constraint(op.f('fk_hypothesis_narrower_of_run_id'), 'hypothesis', type_='foreignkey')
    op.drop_index('uq_calibration_result_scope', table_name='calibration_result', postgresql_nulls_not_distinct=True)
    op.drop_table('calibration_result')
    op.drop_table('run_tag')
    op.drop_table('run_record')
    op.drop_index('ix_model_call_run_id', table_name='model_call')
    op.drop_table('model_call')
    op.drop_table('flag_record')
    op.drop_table('commentary')
    op.drop_table('analysis_set_record')
    op.drop_index('uq_analysis_result_scope', table_name='analysis_result', postgresql_nulls_not_distinct=True)
    op.drop_table('analysis_result')
    op.drop_table('tag_value')
    op.drop_table('stage_result')
    op.drop_table('run_source')
    op.drop_table('run_snapshot')
    op.drop_table('run_agent_setting')
    op.drop_index('ix_record_source_version_id_source_item_key', table_name='record')
    op.drop_table('record')
    op.drop_table('plan')
    op.drop_table('flag')
    op.drop_index('ix_audit_log_run_id', table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_table('artifact')
    op.drop_table('analysis_set')
    op.drop_table('source_file')
    op.drop_table('run')
    op.drop_table('hypothesis_version_source')
    op.drop_table('source_version')
    op.drop_table('hypothesis_version')
    op.drop_table('source')
    op.drop_table('hypothesis')
    op.drop_table('domain')
    op.drop_table('agent_setting')
    op.execute("DROP SEQUENCE hypothesis_number_seq")
    for function in reversed(FUNCTION_NAMES):
        op.execute(f"DROP FUNCTION {function}")


# ---------------------------------------------------------------------------
# Hand-written: trigger functions, triggers, views, seed rows.
# No '%' anywhere: messages are built with ||.
#
# Locking protocol (review finding 1; re-check item 1). The lock order is version,
# then run, then the run's child rows. Two parts:
#  - The protocol, for application code: every transaction that will write to a run
#    or its child rows first calls hc_write_lock(p_run => ...); every transaction that
#    will change a hypothesis version's chosen sources, submit it or dispatch it first
#    calls hc_write_lock(p_version => ...). Paths that follow it acquire locks in the
#    order above, so they cannot deadlock with each other.
#  - The triggers: every trigger that checks or changes a run's state locks the run
#    (hc_lock_run) and reads its status in the same statement; chosen-source and
#    dispatch triggers lock the version (hc_lock_version). This makes the checks
#    race-free. It does NOT by itself establish the lock order: an UPDATE of a child
#    row locks that row before its trigger asks for the run lock. A path that skips
#    the protocol can therefore deadlock; PostgreSQL then aborts one transaction
#    (SQLSTATE 40P01), and callers must retry the whole transaction.
#
# What may be written to a run in each state (review finding 3; owner, 2026-10-05):
#   queued:    run_source and run_agent_setting (dispatch); the run becomes running.
#   running:   everything of the pipeline, each in its checkpoint order:
#              plan (+ tags) -> records -> eligibility -> sets -> freeze -> results.
#   completed: only the commentary, the Commentator's stage and model calls, and
#              artifacts. None of them can change the outcome, verdict, analysis
#              results or record sets, which are all final.
#   failed:    nothing (audit_log is written in every state).
# A run can complete or fail only when none of its stages is running and none of its
# model calls is still started.
# ---------------------------------------------------------------------------

FUNCTION_NAMES = [
    "hc_reject(text)",
    "hc_append_only()",
    "hc_no_delete()",
    "hc_is_frozen(bigint)",
    "hc_lock_run(bigint)",
    "hc_lock_version(bigint)",
    "hc_write_lock(bigint, bigint)",
    "hc_files_digest(bigint)",
    "hc_version_identity(text, text, text, text)",
    "hc_original_domain(bigint)",
    "hc_hypothesis_insert()",
    "hc_version_insert()",
    "hc_version_update()",
    "hc_version_source_change()",
    "hc_run_insert()",
    "hc_run_update()",
    "hc_plan_insert()",
    "hc_run_tag_insert()",
    "hc_tag_value_update()",
    "hc_source_update()",
    "hc_source_version_insert()",
    "hc_source_version_update()",
    "hc_source_file_insert()",
    "hc_run_agent_setting_insert()",
    "hc_run_source_insert()",
    "hc_run_source_update()",
    "hc_record_insert()",
    "hc_run_record_insert()",
    "hc_analysis_set_insert()",
    "hc_analysis_set_record_insert()",
    "hc_run_snapshot_insert()",
    "hc_flag_insert()",
    "hc_flag_update()",
    "hc_flag_record_insert()",
    "hc_analysis_result_insert()",
    "hc_calibration_insert()",
    "hc_commentary_insert()",
    "hc_artifact_insert()",
    "hc_stage_result_insert()",
    "hc_stage_result_update()",
    "hc_model_call_insert()",
    "hc_model_call_update()",
]

FUNCTIONS = [
    # Every rejection goes through here.
    """
    CREATE FUNCTION hc_reject(message text) RETURNS void LANGUAGE plpgsql AS $$
    BEGIN
        RAISE EXCEPTION USING MESSAGE = 'hypocurate: ' || message, ERRCODE = 'check_violation';
    END $$
    """,
    """
    CREATE FUNCTION hc_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        PERFORM hc_reject(TG_TABLE_NAME || ' is append-only: ' || lower(TG_OP) || ' is not allowed');
        RETURN NULL;
    END $$
    """,
    """
    CREATE FUNCTION hc_no_delete() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        PERFORM hc_reject(TG_TABLE_NAME || ' rows are never deleted: ' || lower(TG_OP) || ' is not allowed');
        RETURN NULL;
    END $$
    """,
    """
    CREATE FUNCTION hc_is_frozen(p_run bigint) RETURNS boolean LANGUAGE sql STABLE AS $$
        SELECT EXISTS (SELECT 1 FROM run_snapshot WHERE run_id = p_run)
    $$
    """,
    # The locking protocol: lock the row and read its current status in one statement.
    """
    CREATE FUNCTION hc_lock_run(p_run bigint) RETURNS text LANGUAGE plpgsql AS $$
    DECLARE s text;
    BEGIN
        SELECT status INTO s FROM run WHERE id = p_run FOR NO KEY UPDATE;
        RETURN s;
    END $$
    """,
    """
    CREATE FUNCTION hc_lock_version(p_version bigint) RETURNS text LANGUAGE plpgsql AS $$
    DECLARE s text;
    BEGIN
        SELECT status INTO s FROM hypothesis_version WHERE id = p_version FOR NO KEY UPDATE;
        RETURN s;
    END $$
    """,
    # The protocol's entry point for application code (re-check item 1): call it first,
    # before any write to the run's or the version's rows. Locks the version, then the
    # run; returns the run's status (or the version's, when no run is given).
    """
    CREATE FUNCTION hc_write_lock(p_run bigint DEFAULT NULL, p_version bigint DEFAULT NULL)
    RETURNS text LANGUAGE plpgsql AS $$
    DECLARE s text;
    BEGIN
        IF p_run IS NULL AND p_version IS NULL THEN
            PERFORM hc_reject('hc_write_lock needs a run or a hypothesis version');
        END IF;
        IF p_version IS NOT NULL THEN
            s := hc_lock_version(p_version);
            IF s IS NULL THEN
                PERFORM hc_reject('no hypothesis version ' || p_version);
            END IF;
        END IF;
        IF p_run IS NOT NULL THEN
            IF p_version IS NOT NULL AND p_version IS DISTINCT FROM
               (SELECT hypothesis_version_id FROM run WHERE id = p_run) THEN
                PERFORM hc_reject('run ' || p_run || ' does not belong to hypothesis version ' || p_version);
            END IF;
            s := hc_lock_run(p_run);
            IF s IS NULL THEN
                PERFORM hc_reject('no run ' || p_run);
            END IF;
        END IF;
        RETURN s;
    END $$
    """,
    # A source version's files digest (owner, 2026-10-05; re-check item 2): SHA-256 of its
    # file list, one line "<sha256>  <path>\n" per file (the sha256sum format), sorted by
    # path bytewise. Paths cannot hold a line break (CHECK), so the list is unambiguous.
    # Step 4 computes the same in Python.
    """
    CREATE FUNCTION hc_files_digest(p_version bigint) RETURNS text LANGUAGE sql STABLE AS $$
        SELECT encode(sha256(convert_to(
                   string_agg(sha256 || '  ' || path || chr(10), '' ORDER BY path COLLATE "C"), 'UTF8')), 'hex')
        FROM source_file WHERE source_version_id = p_version
    $$
    """,
    # A source version's identity (re-check item 2): SHA-256 of four lines, the files digest
    # and the three interpretation settings, each "<name> <value>\n". The settings come
    # from fixed lists (CHECK), so they hold no line break.
    """
    CREATE FUNCTION hc_version_identity(p_digest text, p_type text, p_kind text, p_unit text)
    RETURNS text LANGUAGE sql IMMUTABLE AS $$
        SELECT encode(sha256(convert_to(
                   'files ' || p_digest || chr(10) || 'source_type ' || p_type || chr(10)
                   || 'data_kind ' || p_kind || chr(10) || 'grouping_unit ' || p_unit || chr(10), 'UTF8')), 'hex')
    $$
    """,
    # The confirmed domain of the original question, for a narrower query; NULL otherwise.
    """
    CREATE FUNCTION hc_original_domain(p_hypothesis bigint) RETURNS bigint LANGUAGE sql STABLE AS $$
        SELECT hv.confirmed_domain_id
        FROM hypothesis h
        JOIN run r ON r.id = h.narrower_of_run_id
        JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
        WHERE h.id = p_hypothesis
    $$
    """,
    # A narrower question links only to a run whose outcome is partly sufficient (owner, question 1).
    # A completed run never changes, so no lock is needed here.
    """
    CREATE FUNCTION hc_hypothesis_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.narrower_of_run_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM run WHERE id = NEW.narrower_of_run_id
              AND status = 'completed' AND outcome = 'partly_sufficient') THEN
            PERFORM hc_reject('a narrower question can link only to a run whose outcome is partly_sufficient');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_version_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE original bigint := hc_original_domain(NEW.hypothesis_id);
    BEGIN
        IF NEW.status <> 'draft' OR NEW.confirmed_domain_id IS NOT NULL THEN
            PERFORM hc_reject('a new hypothesis version starts as an unreviewed draft');
        END IF;
        IF original IS NOT NULL AND NEW.domain_id <> original THEN
            PERFORM hc_reject('a narrower question has the domain of its original');
        END IF;
        RETURN NEW;
    END $$
    """,
    # The UPDATE itself holds the version row's lock.
    """
    CREATE FUNCTION hc_version_update() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE original bigint := hc_original_domain(NEW.hypothesis_id);
    BEGIN
        IF OLD.status IN ('returned', 'dispatched') THEN
            PERFORM hc_reject('a ' || OLD.status || ' hypothesis version cannot change; an edit is a new version');
        END IF;
        IF NEW.hypothesis_id <> OLD.hypothesis_id OR NEW.version_number <> OLD.version_number
           OR NEW.created_at <> OLD.created_at THEN
            PERFORM hc_reject('the identity of a hypothesis version cannot change');
        END IF;
        IF OLD.status <> 'draft' AND (NEW.text IS DISTINCT FROM OLD.text OR NEW.domain_id IS DISTINCT FROM OLD.domain_id
                                      OR NEW.note IS DISTINCT FROM OLD.note) THEN
            PERFORM hc_reject('a submitted hypothesis version cannot be edited; an edit is a new version');
        END IF;
        IF NOT ((OLD.status, NEW.status) IN (('draft', 'draft'), ('draft', 'submitted'), ('submitted', 'submitted'),
                                             ('submitted', 'returned'), ('submitted', 'dispatched'))) THEN
            PERFORM hc_reject('hypothesis version status cannot go from ' || OLD.status || ' to ' || NEW.status);
        END IF;
        IF OLD.status <> 'submitted' AND (NEW.confirmed_domain_id IS DISTINCT FROM OLD.confirmed_domain_id
                                          OR NEW.domain_confirmed_at IS DISTINCT FROM OLD.domain_confirmed_at
                                          OR NEW.review_comment IS DISTINCT FROM OLD.review_comment) THEN
            PERFORM hc_reject('review fields can be set only while the version is submitted');
        END IF;
        IF original IS NOT NULL AND (NEW.domain_id <> original OR NEW.confirmed_domain_id <> original) THEN
            PERFORM hc_reject('a narrower question has the domain of its original');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_version_source_change() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE row_version bigint;
    BEGIN
        IF TG_OP = 'UPDATE' THEN
            PERFORM hc_reject('hypothesis_version_source rows are added or removed, not updated');
        END IF;
        row_version := CASE WHEN TG_OP = 'INSERT' THEN NEW.hypothesis_version_id ELSE OLD.hypothesis_version_id END;
        IF hc_lock_version(row_version) IS DISTINCT FROM 'draft' THEN
            PERFORM hc_reject('the chosen sources can change only while the version is a draft');
        END IF;
        RETURN CASE WHEN TG_OP = 'INSERT' THEN NEW ELSE OLD END;
    END $$
    """,
    # Dispatch: the version is dispatched and its confirmed domain is supported (PRD 5.5).
    """
    CREATE FUNCTION hc_run_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.status <> 'queued' OR NEW.exploratory THEN
            PERFORM hc_reject('a run starts as queued');
        END IF;
        IF hc_lock_version(NEW.hypothesis_version_id) IS DISTINCT FROM 'dispatched' THEN
            PERFORM hc_reject('a run needs a dispatched hypothesis version');
        END IF;
        IF (SELECT d.supported FROM hypothesis_version hv JOIN domain d ON d.id = hv.confirmed_domain_id
            WHERE hv.id = NEW.hypothesis_version_id) IS NOT TRUE THEN
            PERFORM hc_reject('dispatch blocked: the confirmed domain is not supported yet');
        END IF;
        RETURN NEW;
    END $$
    """,
    # The UPDATE itself holds the run row's lock, so writers to the run's children wait.
    # Start: the dispatch-time source inventory is complete (review finding 6).
    # Completion and failure: no stage running, no model call open.
    # Completion as sufficient (owner, question 4 and addition 2): exactly one pooled
    # result that passed both validity checks; exploratory = use_available AND minimums not met.
    """
    CREATE FUNCTION hc_run_update() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE p plan; pooled analysis_result; n_pooled int;
    BEGIN
        IF OLD.status IN ('completed', 'failed') THEN
            PERFORM hc_reject('a ' || OLD.status || ' run is final');
        END IF;
        IF NEW.hypothesis_version_id <> OLD.hypothesis_version_id OR NEW.agent_mode <> OLD.agent_mode
           OR NEW.fixed_plan <> OLD.fixed_plan OR NEW.experiment_flags <> OLD.experiment_flags
           OR NEW.queued_at <> OLD.queued_at THEN
            PERFORM hc_reject('what a run records at dispatch cannot change');
        END IF;
        IF NOT ((OLD.status, NEW.status) IN (('queued', 'queued'), ('queued', 'running'), ('queued', 'failed'),
                                             ('running', 'running'), ('running', 'completed'), ('running', 'failed'))) THEN
            PERFORM hc_reject('run status cannot go from ' || OLD.status || ' to ' || NEW.status);
        END IF;
        IF OLD.status = 'queued' AND NEW.status = 'running' AND EXISTS (
            SELECT 1 FROM source s WHERE s.created_at <= NEW.queued_at
              AND NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.id AND rs.source_id = s.id)) THEN
            PERFORM hc_reject('a run starts only with a run_source row for every source registered at dispatch');
        END IF;
        IF NEW.status IN ('completed', 'failed') THEN
            IF EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND status = 'running')
               OR EXISTS (SELECT 1 FROM model_call WHERE run_id = NEW.id AND status = 'started') THEN
                PERFORM hc_reject('a run ends only when no stage is running and no model call is open');
            END IF;
        END IF;
        IF NEW.status = 'completed' AND NEW.outcome = 'sufficient' THEN
            SELECT * INTO p FROM plan WHERE run_id = NEW.id;
            IF NOT FOUND THEN
                PERFORM hc_reject('a sufficient outcome needs a locked plan');
            END IF;
            SELECT count(*) INTO n_pooled FROM analysis_result WHERE run_id = NEW.id AND scope = 'pooled';
            SELECT * INTO pooled FROM analysis_result WHERE run_id = NEW.id AND scope = 'pooled';
            IF n_pooled <> 1 OR pooled.check2_passed IS NOT TRUE THEN
                PERFORM hc_reject('a sufficient outcome needs exactly one pooled result that passed both validity checks');
            END IF;
            IF p.sufficiency_option = 'fixed_minimum' AND NOT pooled.minimums_met THEN
                PERFORM hc_reject('under fixed_minimum, a sufficient outcome needs the minimums met');
            END IF;
            IF NEW.exploratory <> (p.sufficiency_option = 'use_available' AND NOT pooled.minimums_met) THEN
                PERFORM hc_reject('exploratory must equal: use_available and the minimums not met');
            END IF;
        END IF;
        RETURN NEW;
    END $$
    """,
    # Rules lock (PRD 5.6): inserted once, during the run, with the database's own time.
    """
    CREATE FUNCTION hc_plan_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('a plan is locked only while its run is running');
        END IF;
        IF NEW.locked_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('locked_at is set by the database at the lock');
        END IF;
        IF EXISTS (SELECT 1 FROM unnest(NEW.sensitivity_analysis_keys) k WHERE k IS NULL OR k !~ '^[a-z0-9_]+$') THEN
            PERFORM hc_reject('sensitivity analysis keys are lowercase names');
        END IF;
        IF cardinality(NEW.sensitivity_analysis_keys)
           <> (SELECT count(DISTINCT k) FROM unnest(NEW.sensitivity_analysis_keys) k) THEN
            PERFORM hc_reject('sensitivity analysis keys must be unique');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Tags are written in the transaction that locks the plan, and never after.
    """
    CREATE FUNCTION hc_run_tag_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('run tags are written only while the run is running');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.run_id AND locked_at = now()) THEN
            PERFORM hc_reject('run tags are written in the rules-lock transaction only');
        END IF;
        IF (SELECT status FROM tag_value WHERE id = NEW.tag_value_id) IS NOT DISTINCT FROM 'rejected' THEN
            PERFORM hc_reject('a rejected tag value cannot be attached');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_tag_value_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF OLD.status <> 'proposed' OR NEW.status = 'proposed' THEN
            PERFORM hc_reject('a proposed tag value is approved or rejected once');
        END IF;
        IF NEW.kind <> OLD.kind OR NEW.value <> OLD.value OR NEW.created_at <> OLD.created_at
           OR NEW.proposed_by_run_id IS DISTINCT FROM OLD.proposed_by_run_id THEN
            PERFORM hc_reject('only the decision on a tag value can change');
        END IF;
        RETURN NEW;
    END $$
    """,
    # A source's key names it in every run's coverage, so it never changes (review finding 6).
    """
    CREATE FUNCTION hc_source_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.key <> OLD.key OR NEW.created_at <> OLD.created_at THEN
            PERFORM hc_reject('a source''s key and registration time cannot change');
        END IF;
        RETURN NEW;
    END $$
    """,
    # A version copies the settings that change how records are read (review finding 4).
    """
    CREATE FUNCTION hc_source_version_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s source;
    BEGIN
        SELECT * INTO s FROM source WHERE id = NEW.source_id;
        IF NEW.sealed_at IS NOT NULL OR NEW.fingerprint IS NOT NULL OR NEW.files_digest IS NOT NULL THEN
            PERFORM hc_reject('a source version is sealed after its files are added');
        END IF;
        IF NEW.source_type IS DISTINCT FROM s.source_type AND NEW.source_type IS NOT NULL
           OR NEW.data_kind IS DISTINCT FROM s.data_kind AND NEW.data_kind IS NOT NULL
           OR NEW.grouping_unit IS DISTINCT FROM s.grouping_unit AND NEW.grouping_unit IS NOT NULL THEN
            PERFORM hc_reject('a source version copies its settings from the source');
        END IF;
        NEW.source_type := s.source_type;
        NEW.data_kind := s.data_kind;
        NEW.grouping_unit := s.grouping_unit;
        RETURN NEW;
    END $$
    """,
    # The only change to a version is sealing it, once (owner, 2026-10-05).
    """
    CREATE FUNCTION hc_source_version_update() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE digest text;
    BEGIN
        IF OLD.sealed_at IS NOT NULL THEN
            PERFORM hc_reject('a sealed source version cannot change');
        END IF;
        IF NEW.sealed_at IS NULL OR NEW.source_id <> OLD.source_id OR NEW.label <> OLD.label
           OR NEW.obtained_on <> OLD.obtained_on OR NEW.source_type <> OLD.source_type
           OR NEW.data_kind <> OLD.data_kind OR NEW.grouping_unit <> OLD.grouping_unit
           OR NEW.created_at <> OLD.created_at THEN
            PERFORM hc_reject('the only change to a source version is sealing it');
        END IF;
        IF NEW.sealed_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('sealed_at is set by the database at sealing');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM source_file WHERE source_version_id = NEW.id) THEN
            PERFORM hc_reject('a source version needs at least one file before sealing');
        END IF;
        digest := hc_files_digest(NEW.id);
        IF NEW.files_digest IS NOT NULL AND NEW.files_digest <> digest THEN
            PERFORM hc_reject('files_digest must be the SHA-256 of the sorted file list');
        END IF;
        NEW.files_digest := digest;
        IF NEW.fingerprint IS DISTINCT FROM hc_version_identity(digest, NEW.source_type, NEW.data_kind,
                                                                NEW.grouping_unit) THEN
            PERFORM hc_reject('the fingerprint must be the SHA-256 of the files digest and the interpretation settings');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_source_file_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE sealed timestamptz;
    BEGIN
        SELECT sealed_at INTO sealed FROM source_version WHERE id = NEW.source_version_id FOR NO KEY UPDATE;
        IF sealed IS NOT NULL THEN
            PERFORM hc_reject('files cannot be added to a sealed source version');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_run_agent_setting_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'queued' THEN
            PERFORM hc_reject('agent settings versions are recorded at dispatch');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_run_source_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'queued' THEN
            PERFORM hc_reject('run sources are recorded at dispatch');
        END IF;
        IF NEW.search_status NOT IN ('not_selected', 'pending') THEN
            PERFORM hc_reject('a run source starts as not_selected or pending');
        END IF;
        IF NEW.source_version_id IS NOT NULL AND NOT EXISTS (
            SELECT 1 FROM source_version WHERE id = NEW.source_version_id AND sealed_at IS NOT NULL) THEN
            PERFORM hc_reject('a run can use only a sealed source version');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_run_source_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(OLD.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('a search result is recorded only while the run is running');
        END IF;
        IF OLD.search_status <> 'pending' THEN
            PERFORM hc_reject('a run source that is ' || OLD.search_status || ' is final');
        END IF;
        IF NEW.run_id <> OLD.run_id OR NEW.source_id <> OLD.source_id
           OR NEW.source_version_id IS DISTINCT FROM OLD.source_version_id THEN
            PERFORM hc_reject('the source and source version of a run cannot change');
        END IF;
        IF NEW.search_status = 'not_selected' THEN
            PERFORM hc_reject('a pending source becomes searched or failed');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Records: after the rules lock, while running, before the freeze, from a version the
    # run recorded, and of the kind that version holds (review findings 3 and 4).
    """
    CREATE FUNCTION hc_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.extraction_run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('records are extracted while their run is running');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.extraction_run_id) THEN
            PERFORM hc_reject('records are extracted only after the rules lock');
        END IF;
        IF hc_is_frozen(NEW.extraction_run_id) THEN
            PERFORM hc_reject('records cannot be added after the dataset freeze');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM run_source rs WHERE rs.run_id = NEW.extraction_run_id
                         AND rs.source_version_id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record must come from a source version recorded for its run');
        END IF;
        IF NEW.kind IS DISTINCT FROM (SELECT data_kind FROM source_version WHERE id = NEW.source_version_id) THEN
            PERFORM hc_reject('a record has the kind of data of its source version');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Stored is not analysed (PRD 5.3): eligibility is written once, after the lock, before the freeze.
    """
    CREATE FUNCTION hc_run_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE rec record;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('eligibility is decided only while the run is running');
        END IF;
        SELECT * INTO rec FROM record WHERE id = NEW.record_id;
        IF rec.extraction_run_id IS DISTINCT FROM NEW.run_id THEN
            PERFORM hc_reject('a run decides only on records extracted in that run');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.run_id) THEN
            PERFORM hc_reject('eligibility is decided only under a locked plan');
        END IF;
        IF hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('eligibility cannot change after the dataset freeze');
        END IF;
        IF NEW.eligible AND rec.kind = 'model_recalled' THEN
            PERFORM hc_reject('a model-recalled record is never eligible');
        END IF;
        RETURN NEW;
    END $$
    """,
    # A set exists only for 'primary' or an analysis the locked plan names (owner, question 2).
    """
    CREATE FUNCTION hc_analysis_set_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE keys text[];
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('analysis sets are written only while the run is running');
        END IF;
        SELECT sensitivity_analysis_keys INTO keys FROM plan WHERE run_id = NEW.run_id;
        IF NOT FOUND THEN
            PERFORM hc_reject('an analysis set needs a locked plan');
        END IF;
        IF NEW.key <> 'primary' AND NOT (NEW.key = ANY (keys)) THEN
            PERFORM hc_reject('the locked plan names no analysis ' || NEW.key);
        END IF;
        IF hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('analysis sets cannot change after the dataset freeze');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_analysis_set_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s analysis_set; rr run_record;
    BEGIN
        SELECT * INTO s FROM analysis_set WHERE id = NEW.analysis_set_id;
        IF hc_lock_run(s.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('analysis sets are written only while the run is running');
        END IF;
        IF hc_is_frozen(s.run_id) THEN
            PERFORM hc_reject('analysis sets cannot change after the dataset freeze');
        END IF;
        SELECT * INTO rr FROM run_record WHERE run_id = s.run_id AND record_id = NEW.record_id;
        IF NOT FOUND THEN
            PERFORM hc_reject('a set holds only records the run has decided on');
        END IF;
        IF (SELECT kind FROM record WHERE id = NEW.record_id) = 'model_recalled' THEN
            PERFORM hc_reject('a model-recalled record is never in an analysis set');
        END IF;
        IF s.key = 'primary' AND rr.eligible IS NOT TRUE THEN
            PERFORM hc_reject('the primary set holds only eligible records');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Dataset freeze (PRD 5.6; review findings 2 and 3): every record of the run has a
    # decision; the primary set is exactly the records decided eligible; every named
    # sensitivity set exists; no "no dataset frozen" calibration was recorded.
    """
    CREATE FUNCTION hc_run_snapshot_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE keys text[]; primary_id bigint; primary_count int;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('a dataset is frozen only while its run is running');
        END IF;
        IF NEW.frozen_at IS DISTINCT FROM now() THEN
            PERFORM hc_reject('frozen_at is set by the database at the freeze');
        END IF;
        SELECT sensitivity_analysis_keys INTO keys FROM plan WHERE run_id = NEW.run_id;
        IF NOT FOUND THEN
            PERFORM hc_reject('a dataset freeze needs a locked plan');
        END IF;
        IF EXISTS (SELECT 1 FROM calibration_result WHERE run_id = NEW.run_id AND analysis_result_id IS NULL) THEN
            PERFORM hc_reject('this run already recorded that no dataset was frozen');
        END IF;
        IF EXISTS (SELECT 1 FROM record r WHERE r.extraction_run_id = NEW.run_id
                     AND NOT EXISTS (SELECT 1 FROM run_record rr WHERE rr.run_id = NEW.run_id AND rr.record_id = r.id)) THEN
            PERFORM hc_reject('every record of the run needs an eligibility decision before the freeze');
        END IF;
        SELECT id INTO primary_id FROM analysis_set WHERE run_id = NEW.run_id AND key = 'primary';
        SELECT count(*) INTO primary_count FROM analysis_set_record WHERE analysis_set_id = primary_id;
        IF primary_count = 0 THEN
            PERFORM hc_reject('no eligible records: no dataset is frozen');
        END IF;
        IF EXISTS (SELECT 1 FROM run_record rr WHERE rr.run_id = NEW.run_id AND rr.eligible
                     AND NOT EXISTS (SELECT 1 FROM analysis_set_record sr
                                     WHERE sr.analysis_set_id = primary_id AND sr.record_id = rr.record_id)) THEN
            PERFORM hc_reject('the primary set must hold every record decided eligible');
        END IF;
        IF NEW.n_records <> primary_count THEN
            PERFORM hc_reject('n_records must equal the size of the primary set');
        END IF;
        IF EXISTS (SELECT 1 FROM unnest(keys) k WHERE NOT EXISTS (
                     SELECT 1 FROM analysis_set WHERE run_id = NEW.run_id AND key = k)) THEN
            PERFORM hc_reject('every sensitivity analysis named by the plan needs its set before the freeze');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_flag_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('flags are raised only while the run is running');
        END IF;
        IF hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('flags cannot be added after the dataset freeze');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_flag_update() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(OLD.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('flags are classified only while the run is running');
        END IF;
        IF OLD.critic_class IS NOT NULL THEN
            PERFORM hc_reject('a flag is classified once');
        END IF;
        IF hc_is_frozen(OLD.run_id) THEN
            PERFORM hc_reject('flags cannot change after the dataset freeze');
        END IF;
        IF NEW.run_id <> OLD.run_id OR NEW.kind <> OLD.kind OR NEW.category <> OLD.category
           OR NEW.compared_values IS DISTINCT FROM OLD.compared_values OR NEW.raised_at <> OLD.raised_at THEN
            PERFORM hc_reject('only the Critic''s classification of a flag can be added');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_flag_record_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE flag_run bigint;
    BEGIN
        SELECT run_id INTO flag_run FROM flag WHERE id = NEW.flag_id;
        IF hc_lock_run(flag_run) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('flags are raised only while the run is running');
        END IF;
        IF (SELECT extraction_run_id FROM record WHERE id = NEW.record_id) IS DISTINCT FROM flag_run THEN
            PERFORM hc_reject('a flag names only records of its own run');
        END IF;
        IF hc_is_frozen(flag_run) THEN
            PERFORM hc_reject('flags cannot change after the dataset freeze');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Results (owner, addition 3; review finding 5): after the freeze, while running, on
    # the right set, with counts consistent with it. These are necessary conditions only.
    """
    CREATE FUNCTION hc_analysis_result_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s analysis_set; p plan; set_count int; set_alloys int;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('analysis results are written only while the run is running');
        END IF;
        IF NOT hc_is_frozen(NEW.run_id) THEN
            PERFORM hc_reject('analysis results come after the dataset freeze');
        END IF;
        SELECT * INTO s FROM analysis_set WHERE id = NEW.analysis_set_id;
        IF NEW.scope IN ('pooled', 'per_source') AND s.key IS DISTINCT FROM 'primary' THEN
            PERFORM hc_reject('pooled and per-source results use the primary set');
        END IF;
        IF NEW.scope = 'sensitivity' AND s.key = 'primary' THEN
            PERFORM hc_reject('a sensitivity result uses a sensitivity set');
        END IF;
        SELECT count(*), count(DISTINCT r.alloy) INTO set_count, set_alloys FROM analysis_set_record sr
            JOIN record r ON r.id = sr.record_id
            JOIN source_version sv ON sv.id = r.source_version_id
            WHERE sr.analysis_set_id = NEW.analysis_set_id
              AND (NEW.source_id IS NULL OR sv.source_id = NEW.source_id);
        IF NEW.n_records <> set_count THEN
            PERFORM hc_reject('n_records must equal the records of the set used');
        END IF;
        IF NEW.n_alloys > set_alloys THEN
            PERFORM hc_reject('n_alloys cannot exceed the distinct alloys of the set used');
        END IF;
        SELECT * INTO p FROM plan WHERE run_id = NEW.run_id;
        IF NEW.minimums_met <> (NEW.n_records >= p.min_records AND NEW.n_alloys >= p.min_alloys
                                AND NEW.n_groups >= p.min_groups AND NEW.resid_df >= p.min_resid_df) THEN
            PERFORM hc_reject('minimums_met must agree with the counts and the plan''s minimums');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Calibration (PRD 5.10): computed exactly when inference is valid; otherwise the reason
    # matches. A run-level "no dataset frozen" row and a freeze exclude each other (finding 3).
    """
    CREATE FUNCTION hc_calibration_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE a analysis_result;
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'running' THEN
            PERFORM hc_reject('calibration is recorded only while the run is running');
        END IF;
        IF NEW.analysis_result_id IS NULL THEN
            IF hc_is_frozen(NEW.run_id) THEN
                PERFORM hc_reject('a dataset was frozen: calibration is reported per analysis');
            END IF;
            RETURN NEW;
        END IF;
        SELECT * INTO a FROM analysis_result WHERE id = NEW.analysis_result_id;
        IF (NEW.status = 'computed') <> a.check2_passed THEN
            PERFORM hc_reject('calibration is computed exactly when inference is valid');
        END IF;
        IF NEW.reason = 'coefficient_not_fitted' AND a.check1_passed
           OR NEW.reason = 'insufficient_groups' AND NOT (a.check1_passed AND NOT a.check2_passed) THEN
            PERFORM hc_reject('the reason calibration is unavailable must match the validity checks');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_commentary_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF hc_lock_run(NEW.run_id) IS DISTINCT FROM 'completed' THEN
            PERFORM hc_reject('commentary is written after the run is completed');
        END IF;
        IF (SELECT stage FROM stage_result WHERE id = NEW.stage_result_id) IS DISTINCT FROM 'commentator' THEN
            PERFORM hc_reject('commentary comes from the commentator stage');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_artifact_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF coalesce(hc_lock_run(NEW.run_id), '') NOT IN ('running', 'completed') THEN
            PERFORM hc_reject('artifacts are stored only for a running or completed run');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Stages: while running; after completion only the Commentator's stage.
    """
    CREATE FUNCTION hc_stage_result_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(NEW.run_id), '');
    BEGIN
        IF NOT (s = 'running' OR s = 'completed' AND NEW.stage = 'commentator'
                                              AND NEW.role IS NOT DISTINCT FROM 'commentator') THEN
            PERFORM hc_reject('a stage runs while the run is running; after completion only the commentator');
        END IF;
        IF NEW.status <> 'running' THEN
            PERFORM hc_reject('a stage result starts as running');
        END IF;
        RETURN NEW;
    END $$
    """,
    """
    CREATE FUNCTION hc_stage_result_update() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s text := coalesce(hc_lock_run(OLD.run_id), '');
    BEGIN
        IF NOT (s = 'running' OR s = 'completed' AND OLD.stage = 'commentator') THEN
            PERFORM hc_reject('a stage result changes only while its run is running');
        END IF;
        IF OLD.status <> 'running' THEN
            PERFORM hc_reject('a finished stage result is final');
        END IF;
        IF NEW.run_id <> OLD.run_id OR NEW.stage <> OLD.stage OR NEW.attempt <> OLD.attempt
           OR NEW.started_at <> OLD.started_at THEN
            PERFORM hc_reject('the identity of a stage result cannot change');
        END IF;
        RETURN NEW;
    END $$
    """,
    # Model calls (owner, question 5; review finding 7): written before the request with
    # the database's time, finished exactly once with the database's time. After
    # completion only the Commentator's calls, which count in the run's totals.
    """
    CREATE FUNCTION hc_model_call_insert() RETURNS trigger LANGUAGE plpgsql AS $$
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
    """,
    """
    CREATE FUNCTION hc_model_call_update() RETURNS trigger LANGUAGE plpgsql AS $$
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
    """,
]

APPEND_ONLY = [
    "domain", "agent_setting", "source_file", "hypothesis", "plan", "run_tag",
    "run_agent_setting", "run_snapshot", "record", "run_record", "analysis_set", "analysis_set_record",
    "flag_record", "analysis_result", "calibration_result", "commentary", "artifact", "audit_log",
]
NO_DELETE = [
    "hypothesis_version", "run", "tag_value", "source", "source_version", "run_source", "stage_result",
    "model_call", "flag",
]
# (table, event, function)
CHECKED = [
    ("hypothesis", "INSERT", "hc_hypothesis_insert"),
    ("hypothesis_version", "INSERT", "hc_version_insert"),
    ("hypothesis_version", "UPDATE", "hc_version_update"),
    ("hypothesis_version_source", "INSERT OR UPDATE OR DELETE", "hc_version_source_change"),
    ("run", "INSERT", "hc_run_insert"),
    ("run", "UPDATE", "hc_run_update"),
    ("plan", "INSERT", "hc_plan_insert"),
    ("run_tag", "INSERT", "hc_run_tag_insert"),
    ("tag_value", "UPDATE", "hc_tag_value_update"),
    ("source", "UPDATE", "hc_source_update"),
    ("source_version", "INSERT", "hc_source_version_insert"),
    ("source_version", "UPDATE", "hc_source_version_update"),
    ("source_file", "INSERT", "hc_source_file_insert"),
    ("run_agent_setting", "INSERT", "hc_run_agent_setting_insert"),
    ("run_source", "INSERT", "hc_run_source_insert"),
    ("run_source", "UPDATE", "hc_run_source_update"),
    ("record", "INSERT", "hc_record_insert"),
    ("run_record", "INSERT", "hc_run_record_insert"),
    ("analysis_set", "INSERT", "hc_analysis_set_insert"),
    ("analysis_set_record", "INSERT", "hc_analysis_set_record_insert"),
    ("run_snapshot", "INSERT", "hc_run_snapshot_insert"),
    ("flag", "INSERT", "hc_flag_insert"),
    ("flag", "UPDATE", "hc_flag_update"),
    ("flag_record", "INSERT", "hc_flag_record_insert"),
    ("analysis_result", "INSERT", "hc_analysis_result_insert"),
    ("calibration_result", "INSERT", "hc_calibration_insert"),
    ("commentary", "INSERT", "hc_commentary_insert"),
    ("artifact", "INSERT", "hc_artifact_insert"),
    ("stage_result", "INSERT", "hc_stage_result_insert"),
    ("stage_result", "UPDATE", "hc_stage_result_update"),
    ("model_call", "INSERT", "hc_model_call_insert"),
    ("model_call", "UPDATE", "hc_model_call_update"),
]

TRIGGERS = (
    [f"CREATE TRIGGER hc_{t}_append_only BEFORE UPDATE OR DELETE ON {t} "
     f"FOR EACH ROW EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} "
       f"FOR EACH STATEMENT EXECUTE FUNCTION hc_append_only()" for t in APPEND_ONLY]
    + [f"CREATE TRIGGER hc_{t}_no_delete BEFORE DELETE ON {t} "
       f"FOR EACH ROW EXECUTE FUNCTION hc_no_delete()" for t in NO_DELETE]
    + [f"CREATE TRIGGER hc_{t}_no_truncate BEFORE TRUNCATE ON {t} "
       f"FOR EACH STATEMENT EXECUTE FUNCTION hc_no_delete()" for t in NO_DELETE + ["hypothesis_version_source"]]
    + [f"CREATE TRIGGER {f} BEFORE {event} ON {t} FOR EACH ROW EXECUTE FUNCTION {f}()"
       for t, event, f in CHECKED]
)

# Totals are derived from model_call, never stored (owner, question 5). A call without
# reported cost counts at its upper bound max_cost toward cap_cost.
_TOTALS = """
    count(mc.id) AS calls,
    coalesce(sum(mc.input_tokens), 0) AS input_tokens,
    coalesce(sum(mc.output_tokens), 0) AS output_tokens,
    coalesce(sum(mc.cached_tokens), 0) AS cached_tokens,
    coalesce(sum(mc.cost), 0) AS reported_cost,
    count(mc.id) FILTER (WHERE mc.cost IS NULL) AS unconfirmed_calls,
    coalesce(sum(mc.max_cost) FILTER (WHERE mc.cost IS NULL), 0) AS unconfirmed_cost_bound,
    coalesce(sum(coalesce(mc.cost, mc.max_cost)), 0) AS cap_cost
"""


def _sources(condition: str) -> str:
    return (f"ARRAY(SELECT s.key FROM run_source rs JOIN source s ON s.id = rs.source_id "
            f"WHERE rs.run_id = r.id AND {condition} ORDER BY s.key)")


VIEW_NAMES = [
    "run_search_coverage",
    "model_call_totals_by_stage",
    "model_call_totals_by_run",
    "model_call_totals_by_query",
    "model_call_totals_by_month",
]

VIEWS = [
    # Review finding 6: every category is reported with its sources, never collapsed into
    # one label; coverage comes only from the run's own dispatch-time run_source rows.
    # A failed source is listed as failed and not searched, never as missing evidence.
    f"""
    CREATE VIEW run_search_coverage AS
    SELECT r.id AS run_id,
        {_sources("rs.search_status = 'searched'")} AS searched_sources,
        {_sources("rs.search_status <> 'searched'")} AS not_searched_sources,
        {_sources("rs.search_status = 'not_selected'")} AS not_selected_sources,
        {_sources("rs.search_status = 'failed'")} AS failed_search_sources,
        {_sources("rs.search_status = 'searched' AND rs.nothing_found IS NULL")} AS records_found_sources,
        {_sources("rs.search_status = 'searched' AND rs.nothing_found = 'missing_evidence'")} AS missing_evidence_sources,
        {_sources("rs.search_status = 'searched' AND rs.nothing_found = 'reported_negative'")} AS reported_negative_sources
    FROM run r
    """,
    f"""
    CREATE VIEW model_call_totals_by_stage AS
    SELECT sr.id AS stage_result_id, sr.run_id, sr.stage, sr.attempt, {_TOTALS}
    FROM stage_result sr LEFT JOIN model_call mc ON mc.stage_result_id = sr.id
    GROUP BY sr.id
    """,
    f"""
    CREATE VIEW model_call_totals_by_run AS
    SELECT r.id AS run_id, {_TOTALS}
    FROM run r LEFT JOIN model_call mc ON mc.run_id = r.id
    GROUP BY r.id
    """,
    f"""
    CREATE VIEW model_call_totals_by_query AS
    SELECT h.id AS hypothesis_id, h.number, {_TOTALS}
    FROM hypothesis h
    LEFT JOIN hypothesis_version hv ON hv.hypothesis_id = h.id
    LEFT JOIN run r ON r.hypothesis_version_id = hv.id
    LEFT JOIN model_call mc ON mc.run_id = r.id
    GROUP BY h.id
    """,
    # A call counts in the UTC month of its started_at, which the database sets.
    f"""
    CREATE VIEW model_call_totals_by_month AS
    SELECT date_trunc('month', mc.started_at AT TIME ZONE 'UTC') AS month_utc, {_TOTALS}
    FROM model_call mc
    GROUP BY 1
    """,
]

# PRD 5.5: the fixed list of domains. Tag lists are seeded in step 6 (PRD 17 #7 unconfirmed).
SEED = [
    """
    INSERT INTO domain (key, name, supported, profile_name) VALUES
        ('grain_size_strengthening', 'Grain-size strengthening', true, 'grain_size_strengthening'),
        ('fatigue', 'Fatigue', false, NULL),
        ('other', 'Other', false, NULL)
    """,
]
