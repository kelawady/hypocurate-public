"""The allowed fields per role and stage (PRD 4). The one named place for the access contract.

**Threat model** (owner, 2026-10-05; register entry 'threat_model'). The access layer and
its tests guard against *our own code* leaking data to a model. In sprint 1 agents are
language models that return text only: they never execute code and never receive SQL, a
database connection, a file path or any tool other than reads through an access object.
Only trusted, reviewed code runs, and a trusted dispatcher (`dispatch.bind`) binds each
agent call to a run, role, stage and source. The access layer is **not** a boundary
against hostile code running in the same process: such code could use the database
credentials directly. Agents that execute code are in the backlog, with operating-system
isolation as a precondition.

Allowed fields, not blocked fields: a role receives exactly the fields listed for it at
the run's stage, and nothing else. Each field is built from named keys only
(`hypocurate.access.fields`), never by copying a row and removing what is forbidden. Text
in the blinded views (the Planner, the Critic, and the Analyst's facts without a freeze;
step 8b) comes from fixed vocabularies (`vocabulary.py`) or is replaced by a marker; the
plan is projected recursively by `PLAN_SCHEMA`. What these views still disclose by design
is listed in `ACCEPTED_DISCLOSURES`; timing is not protected.

**Single-run scope** (owner, 2026-10-05). Every field reads only the rows of the access
object's own run, and the sealed source versions that run recorded at dispatch. No field
returns anything from another run: not from the run a narrower question came from (its
results, coefficient, stage outputs or commentary), and not from earlier runs of the same
hypothesis. Two fields are reference lists, not run data: `domain` (the run's confirmed
domain) and `tag_values` (the approved values of the fixed tag lists, without the run that
proposed them).

Stages are read from the database on every call (`hypocurate.access.stage`). A role that is
not listed for a stage receives nothing at that stage; a queued or failed run gives
nothing to anyone. There is no general unlock at a checkpoint, and no experiment flag
relaxes this contract (sprint 1; PRD 4's relaxation flag is in the backlog).
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from hypocurate.access.vocabulary import (CALIBRATION_METHODS, CATEGORY_FIELDS, ELIGIBILITY_RULES, ESTIMATION_METHODS, FLAG_CATEGORIES, FLAG_KINDS,
                                          GROUPING_UNITS, PHASE_CLASSES, PROCESSING_METHODS, PROFILE_NAMES,
                                          SENSITIVITY_KEYS, SINGLE_PHASE, SOURCE_KEYS, TEMPERATURE_BANDS, TEST_TYPES,
                                          VALUE_STATUSES)

# Sprint 2 pilot (owner, 2026-10-22, an approved safeguard change): the Extractor reads one parsed document in no
# run; the Reconciler reads nothing until its lists are built and reviewed with R5.
ROLES = ("planner", "curator", "critic", "analyst", "commentator", "extractor", "reconciler")
# The code roles of PRD 4 (step 6, owner 2026-10-05): Inclusion and Checks are code, not
# agents. They read through access objects too, bound by `dispatch.bind_code`, so their reads
# are logged. No agent setting can bind as one of them. Step 7 (owner, 2026-10-05; a safeguard
# change, reviewed by a second model): Statistics and the gap facts.
# Step 8b (owner, 2026-10-07): the narrowing decision, before any lock, on counts of structure only.
CODE_ROLES = ("inclusion", "checks", "statistics", "gap_facts", "narrowing")
ALL_ROLES = ROLES + CODE_ROLES

# none: queued or failed. before_lock: running, no plan. curation: plan locked, no dataset
# frozen and no 'no dataset frozen' record. analysis: dataset frozen, running.
# closed_without_freeze: curation ended with no dataset frozen (insufficient), running.
# final: completed after a dataset freeze. final_without_freeze: completed with no dataset frozen.
# registration (step 8a, owner 2026-10-06): not a run stage; the Curator reads one sealed source
# version, bound by a registration invocation (`dispatch.bind_invocation`), with no run.
# narrowed (step 8b, owner 2026-10-07, A4): running, no plan, and code's narrowing decision of partly
# sufficient stored; no plan can be locked from here (lock_rules needs before_lock; migration 0006).
# document (Sprint 2 pilot, owner 2026-10-22): not a run stage; the Extractor reads one parsed document, bound by a
# document invocation (`dispatch.bind_invocation`), with no run.
STAGES = ("none", "before_lock", "curation", "analysis", "closed_without_freeze", "final", "final_without_freeze",
          "registration", "narrowed", "document")

FIELDS = MappingProxyType({
    "claim": "The claim in words: query number, version number, text, and whether it is a narrower question.",
    "domain": "The run's confirmed domain: key, name and profile.",
    "sources_meta": "The run's chosen sources, as fixed named plain fields (SOURCE_META_FIELDS): name, licence "
                    "and fields available from the code's source definitions; type, kind of data and grouping "
                    "unit from the sealed version the run recorded.",
    "tag_values": "The approved values of the fixed tag lists: kind and value.",
    "record_counts": "Per chosen source, computed by code from its sealed version: the number of records, "
                     "per field the count of each status, and per value of each non-outcome category field "
                     "the count of records.",
    "source_documentation": "For the Curator at registration (step 8a): the documentation files of the one "
                            "sealed source version its invocation names, as text, with the source's key. "
                            "No data file, no claim, no plan, no other version.",
    "curation_targets": "For the Curator at registration (step 8a): the fields it may propose a value for, "
                        "with each field's vocabulary or unit (vocabulary.CURATION_TARGETS).",
    "parsed_document": "For the Extractor (Sprint 2 pilot): the one parsed document its invocation names, as stored "
                       "(pages, text blocks and tables with their page, table and row indexes), checked against its "
                       "hash. No DOI, no compilation record, no other document, no claim.",
    "extraction_spec": "For the Extractor (Sprint 2 pilot; owner, 2026-10-22): the reading sections of the evidence "
                       "specification its setting names (unit of observation, required measurements, required "
                       "context, linkage evidence, ambiguity handling), with the specification's key, version and "
                       "hash. Never the claim, the analysis, the exclusion rules or the re-report rule.",
    "extraction_draft": "For the Extractor's verification call (Sprint 2 pilot; owner, 2026-10-23): the raw output "
                        "of its own extraction call on the same parsed document, as stored with its hash.",
    "s0_records": "For the Reconciler (Sprint 2 pilot; owner, 2026-10-23): the candidate observations of the newest S0 "
                  "on the parsed document its invocation names, each with its values as written and their provenance.",
    "compilation_records": "For the Reconciler (Sprint 2 pilot; owner, 2026-10-22: its list may include compilation "
                           "records, so its outputs are S1, never S0): the compilation's (MPEA's) records for the same "
                           "paper, each with its key, alloy, composition, grain size, yield strength and conditions.",
    "record_metadata": "Per stored record: id, source, item index, kind, alloy label and composition, DOI "
                       "(DOI syntax only), each field's status, and the non-outcome category values from "
                       "their vocabularies. No measured number of any field, no paper title, no origin key.",
    "flags_kind": "Per flag: id, kind and category (from their vocabularies) and record ids. Never the numbers "
                  "compared.",
    "plan": "The locked plan, projected recursively by PLAN_SCHEMA; its fingerprint, lock time, "
            "data-sufficiency option and minimums, sensitivity analyses (vocabulary) and power assumptions "
            "(POWER_SCHEMA).",
    "records_full": "Per stored record: every stored field, including outcome values and values as reported.",
    "decisions": "Eligibility decisions (record, eligible, rule code) and the named analysis sets (keys from "
                 "the vocabulary).",
    "flags_full": "Per flag: kind, category, record ids, the numbers compared, the Critic's class and reason.",
    "results": "The run's status, outcome, verdict and exploratory label; the dataset freeze; analysis "
               "results; calibration results.",
    "coverage": "Per source: search status, kind of nothing found, and how many category values of each field "
                "were unrecognized in the run's records (counts only); the run's search coverage lists. "
                "No failure text.",
    "stage_outputs": "Every stage of the run: input, output, reasoning, tool calls and model.",
    "run_cost": "Tokens and cost of the run, in total and per stage.",
    "stored_record_counts": "Per source, computed by code from the run's stored records: the number of "
                            "records, per field the count of each status, and per value of each non-outcome "
                            "category field the count of records.",
    "condition_summaries": "Computed by code from the run's stored records, per alloy and overall: the "
                           "number of records; count, minimum and maximum of grain size and of test "
                           "temperature; counts by test type and by phase. Never a row-level value, an "
                           "outcome value or a statistic derived from outcomes.",
    "gap_report": "The Analyst's gap report: the output of each Analyst stage of the run.",
    "set_flags": "From the completed Checks result, for Inclusion (code): per sensitivity set whose matching "
                 "settings differ from the primary set's, its duplicate, conflict and ambiguity flags: kind and "
                 "category (from their vocabularies) and record ids. Never the numbers compared.",
    "record_conditions": "Per stored record, for Inclusion (code): id, source, row number, kind, its stable "
                         "identity (source-version fingerprint, origin key, item index), a hash of the stored record, whether it carries a DOI, identities as hashes (paper from the DOI, "
                         "batch), composition, each "
                         "field's status, grain size and test temperature, and the category values from their "
                         "vocabularies. No outcome value, no value as reported, no free text.",
    "outcome": "The run's status, outcome, verdict and exploratory label.",
    "candidate_counts": "For the narrowing decision (code; step 8b), before the lock, per chosen source from its "
                        "sealed version (its key and fingerprint): counts of records per combination of phase class, "
                        "test type and temperature band (from their vocabularies), reported test temperature, the "
                        "status of each of those fields, of grain size and of each outcome field, and whether a grain "
                        "size is present. Counts and statuses only: no outcome value, no composition, no free text.",
    "analyst_facts": "For the Analyst (step 8b, owner Q6 and 2026-10-07): named facts built by code from what it "
                     "stored (pipeline.analyst_names), each a finished display string or ready-made phrase the "
                     "Analyst refers to as {name}: the decision and its wordings; the plan's threshold, option and "
                     "minimums, and per scope part whether the claim stated it or the Planner assumed it; the pooled "
                     "result and its counts against each minimum; per source its result and label; both "
                     "calibrations; a summary of the sensitivity sets built by code; the gap facts; at 'narrowed' "
                     "the claim's parts, their counts and the narrower scope. Below the minimums no estimate, "
                     "standard error, p-value or paper figures. Never a record-level value or identity, a Critic's "
                     "class or reason, or a stage's text.",
    "frozen_analysis_data": "For Statistics (code; step 7), once the dataset is frozen: the freeze's "
                            "fingerprint; the frozen sets (keys from the vocabulary, record ids); and per "
                            "record in any frozen set, and only those: id, source, stable identity "
                            "(source-version fingerprint, origin key, item index), composition, the paper "
                            "(from the DOI) and the batch as hashes, grain size, and the plan's outcome value. "
                            "No record outside the frozen sets, no value as reported, no free text.",
})

# Step 8b (owner, 2026-10-07, Q6): the Analyst receives stored facts only, the same list at each of its
# stages; what `analyst_facts` holds depends on the stage (see FIELDS).
_ANALYST = frozenset({"claim", "domain", "sources_meta", "coverage", "analyst_facts"})

ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
    "planner": MappingProxyType({
        "before_lock": frozenset({"claim", "domain", "sources_meta", "tag_values", "record_counts"}),
    }),
    # Owner, 2026-10-06 (step 8a, Q2): the Curator runs when a source version is registered, never in a
    # run. It reads that version's documentation and the target fields, and nothing at any run stage.
    "curator": MappingProxyType({
        "registration": frozenset({"source_documentation", "curation_targets"}),
    }),
    "critic": MappingProxyType({
        "curation": frozenset({"sources_meta", "record_metadata", "flags_kind"}),
    }),
    "analyst": MappingProxyType({
        "analysis": _ANALYST,
        "closed_without_freeze": _ANALYST,
        # A4: the partly-sufficient original, before any lock; `analyst_facts` holds the narrowing facts only.
        "narrowed": _ANALYST,
    }),
    # Owner, 2026-10-07 (A6): the Commentator reads nothing at any stage until step 12, when the role is
    # built and its lists are decided and reviewed. Its step 5 lists are kept in the register entry
    # 'access_allow_lists' as the starting point.
    "commentator": MappingProxyType({}),
    # Sprint 2 pilot (owner, 2026-10-22): the Extractor reads one parsed document and the reading sections of its
    # evidence specification; its verification call also reads its own draft. Nothing that holds the compilation.
    "extractor": MappingProxyType({
        "document": frozenset({"parsed_document", "extraction_spec", "extraction_draft"}),
    }),
    # R5 (owner, 2026-10-23: per document, before the runs): the Reconciler reads one parsed document, its newest S0
    # and the compilation's records for that paper; its outputs are S1 events, never S0.
    "reconciler": MappingProxyType({
        "document": frozenset({"parsed_document", "s0_records", "compilation_records"}),
    }),
})


# The code roles' lists (owner, 2026-10-05). Checks sees all values (PRD 4: it compares them);
# Inclusion is blind: it receives no outcome value, so no eligibility decision can depend on a
# record's outcome directly or on its position relative to the tested relationship. It acts on
# the flags Checks raised, by kind and category.
CODE_ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
    "inclusion": MappingProxyType({"curation": frozenset({"plan", "record_conditions", "flags_kind", "set_flags"})}),
    "checks": MappingProxyType({"curation": frozenset({"plan", "records_full"})}),
    # Step 7 (owner, 2026-10-05): Statistics reads only the frozen set, after the freeze, and
    # never decides inclusion. The gap facts read no outcome value: counts, decisions, coverage.
    "statistics": MappingProxyType({"analysis": frozenset({"plan", "frozen_analysis_data"})}),
    "gap_facts": MappingProxyType({
        "analysis": frozenset({"plan", "decisions", "stored_record_counts", "coverage"}),
        "closed_without_freeze": frozenset({"plan", "decisions", "stored_record_counts", "coverage"}),
    }),
    # Step 8b (owner, 2026-10-07, Q5): before any lock, counts of structure only.
    "narrowing": MappingProxyType({"before_lock": frozenset({"candidate_counts"})}),
})


def allowed(role: str, stage: str) -> frozenset[str]:
    """The fields `role` may receive at `stage`; empty for any role or stage not listed."""
    lists = ALLOWED.get(role) or CODE_ALLOWED.get(role) or {}
    return lists.get(stage, frozenset())


# The fields that can be the outcome of a plan. The Planner does not know which one its
# plan will choose before the lock, so every one of them is treated as an outcome
# everywhere outcomes are withheld: their values never reach the Planner, the Critic or
# the gap report, and no count is ever broken down by their values.
OUTCOME_FIELDS = frozenset({"yield_strength", "yield_strength_sd", "ultimate_tensile_strength",
                            "hardness", "hardness_sd"})

# CATEGORY_FIELDS (from `vocabulary`): fields whose values are categories, shown to the Critic
# and counted for the Planner and the gap report, always through their vocabularies.

# The non-outcome measured conditions summarized for the gap report (owner, 2026-10-05).
CONDITION_RANGE_FIELDS = ("grain_size", "test_temperature")
CONDITION_COUNT_FIELDS = ("test_type", "phase_class")

# sources_meta: a fixed set of named plain fields (owner, 2026-10-05). Name, licence and
# fields available come from the code's definitions (`SOURCES`); interpretation settings
# from the run's sealed version. The source registry's text (address, labels, edits after
# dispatch) never reaches a role through this field.
SOURCE_META_FIELDS = ("key", "name", "source_type", "data_kind", "licence", "grouping_unit",
                      "fields_available")

# record_conditions: the one column as reported that Inclusion receives, per source, as a hash:
# the batch, for the sensitivity analysis that groups by batch (six batches for Texas A&M).
BATCH_COLUMNS = MappingProxyType({"tamu_fcc": "Iteration"})

# The plan, projected recursively (owner, 2026-10-05: defined in step 5; step 6's plan model
# must follow it). A schema is a dict of named keys; a leaf is "number", "integer",
# "field" (a common field name), "unit", or a vocabulary (a frozenset); ("list", schema) is
# a list. Unknown keys are dropped; a leaf that does not fit becomes the marker (vocabulary,
# field, unit) or is dropped (number, integer). There is no free-text leaf. PRD 5.1's
# "claim in words" is not part of the projection: roles that may see it get the `claim`
# field.
ALLOY_CLASSES = frozenset({"multi-principal-element (high-entropy) alloy", "steel", "aluminium alloy",
                           "titanium alloy", "nickel alloy", "copper alloy", "magnesium alloy", "other"})
EXCLUSION_RULES = frozenset({"grain_size_range", "temperature_range", "phase", "test_type"})
MODELS = frozenset({"hall_petch_alloy_intercepts"})
TRANSFORMATIONS = frozenset({"inverse_square_root"})
HYPOTHESES_NULL = frozenset({"k <= 0"})
HYPOTHESES_ALTERNATIVE = frozenset({"k > 0"})
VERDICT_STATEMENTS = frozenset({"pooled_test_gives_verdict"})
SUFFICIENCY_OPTIONS = frozenset({"fixed_minimum", "use_available"})
POWER_METHODS = frozenset({"information_only"})
CATEGORY_VALUES = TEST_TYPES | TEMPERATURE_BANDS | PHASE_CLASSES | PROCESSING_METHODS

PLAN_SCHEMA = MappingProxyType({
    "hypothesis_version": "integer",
    "variables": {"outcome": {"field": "field", "unit": "unit"},
                  "predictor": {"field": "field", "unit": "unit", "transformation": TRANSFORMATIONS}},
    "scope": {"alloy_class": ("list", ALLOY_CLASSES), "temperature_band": ("list", TEMPERATURE_BANDS),
              "test_type": ("list", TEST_TYPES), "phase_class": ("list", PHASE_CLASSES)},
    "model": {"name": MODELS, "null": HYPOTHESES_NULL, "alternative": HYPOTHESES_ALTERNATIVE, "alpha": "number"},
    "sufficiency": {"option": SUFFICIENCY_OPTIONS, "min_records": "integer", "min_alloys": "integer",
                    "min_groups": "integer", "min_resid_df": "integer"},
    "fields_to_extract": ("list", "field"),
    "exclusion_rules": ("list", {"rule": EXCLUSION_RULES, "min": "number", "max": "number",
                                 "values": ("list", CATEGORY_VALUES)}),
    # A flag category narrows an entry (step 6): an ambiguous group is a possible duplicate
    # with the category "several candidates".
    "eligibility_rules": ("list", {"flag_kind": FLAG_KINDS, "category": FLAG_CATEGORIES, "rule": ELIGIBILITY_RULES}),
    "verdict_statement": VERDICT_STATEMENTS,
    "sensitivity_analyses": ("list", SENSITIVITY_KEYS),
    # Step 6 (owner, 2026-10-05): every setting that affects which records are eligible or how
    # they are grouped is a value of the locked plan, and the domain profile it came from.
    "profile": {"name": PROFILE_NAMES, "version": "integer"},
    "rules": {"same_alloy_decimals": "integer", "duplicate_tolerance": "number",
              "survivor_source_order": ("list", SOURCE_KEYS), "min_grain_sizes": "integer",
              "room_temperature_min": "number", "room_temperature_max": "number", "single_phase": SINGLE_PHASE,
              "accepted_value_statuses": ("list", VALUE_STATUSES),
              "grouping": ("list", {"source": SOURCE_KEYS, "unit": GROUPING_UNITS}),
              # Step 8a (owner, 2026-10-06, Q4): the claim's temperature range, exactly when the plan's
              # band is not room temperature.
              "temperature_range": {"min": "number", "max": "number"}},
    # Step 7 (owner, 2026-10-05): the calibration is fixed at the rules lock, both methods.
    "calibration": {"methods": ("list", CALIBRATION_METHODS), "n_simulations": "integer", "scatter": "number",
                    "shift": "number", "estimation": ESTIMATION_METHODS, "smallest_effect": "number"},
})
POWER_SCHEMA = MappingProxyType({"method": POWER_METHODS, "within_paper_similarity": "number",
                                 "smallest_effect": "number", "scatter": "number"})

# What the blinded views still disclose, by design (owner, 2026-10-05; register entry
# 'accepted_disclosures'). The blinding claim is limited to: no outcome value is copied
# into these views from a stored outcome field, a value as reported, a flag's numbers, a
# stage's text, or text outside a vocabulary.
ACCEPTED_DISCLOSURES = (
    "counts by field status (for example how many yield strengths a source reports or cannot read)",
    "flag kinds and categories (for example that two values differ beyond the tolerance)",
    "compositions and alloy labels derived from them",
    "DOIs with DOI syntax, which may contain digits",
    "text written or approved by people: the claim, the approved tag values, source names and licences in code",
    "numbers in the locked plan (thresholds, minimums), written before any record exists",
    "timing of calls and the existence of refusals",
)
