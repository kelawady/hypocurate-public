"""The allowed fields per role and stage (PRD 4). The one named place for the access contract.

Allowed fields, not blocked fields: a role receives exactly the fields listed for it at
the run's stage, and nothing else. Each field is built from named keys only
(`hypocurate.access.fields`), never by copying a row and removing what is forbidden.

**Single-run scope** (owner, 2026-10-05). Every field reads only the rows of the access
object's own run, and the sealed source versions that run recorded at dispatch. No field
returns anything from another run: not from the run a narrower question came from (its
results, coefficient, stage outputs or commentary), and not from earlier runs of the same
hypothesis. Two fields are reference lists, not run data: `domain` (the run's confirmed
domain) and `tag_values` (the approved values of the fixed tag lists, without the run that
proposed them).

Stages are read from the database on every call (`hypocurate.access.stage`), never taken
from the caller. A role that is not listed for a stage receives nothing at that stage; a
queued or failed run gives nothing to anyone. There is no general unlock at a checkpoint,
and no experiment flag relaxes this contract (sprint 1; PRD 4's relaxation flag is in the
backlog).
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

ROLES = ("planner", "curator", "critic", "analyst", "commentator")

# none: queued or failed. before_lock: running, no plan. curation: plan locked, no dataset
# frozen and no 'no dataset frozen' record. analysis: dataset frozen, running.
# closed_without_freeze: curation ended with no dataset frozen (insufficient), running.
# final: completed after a dataset freeze. final_without_freeze: completed with no dataset frozen.
STAGES = ("none", "before_lock", "curation", "analysis", "closed_without_freeze", "final", "final_without_freeze")

FIELDS = MappingProxyType({
    "claim": "The claim in words: query number, version number, text, and whether it is a narrower question.",
    "domain": "The run's confirmed domain: key, name and profile.",
    "sources_meta": "The run's chosen sources, as fixed named plain fields only (SOURCE_META_FIELDS).",
    "tag_values": "The approved values of the fixed tag lists: kind and value.",
    "record_counts": "Per chosen source, computed by code from its sealed version: the number of records, "
                     "per field the count of each status, and per value of each non-outcome category field "
                     "the count of records.",
    "plan_fields_to_extract": "From the locked plan, the list of fields to extract, and nothing else.",
    "source_content": "The sealed files of the one source the Curator reads, as recorded for the run.",
    "record_metadata": "Per stored record: id, source, origin key, alloy label and composition, paper "
                       "reference and DOI, each field's status, and the non-outcome category values. "
                       "No measured number of any field.",
    "flags_kind": "Per flag: id, kind, category and record ids. Never the numbers compared.",
    "plan": "The locked plan: its named parts (PLAN_KEYS), fingerprint, lock time, data-sufficiency "
            "option and minimums, sensitivity analyses and power assumptions.",
    "records_full": "Per stored record: every stored field, including outcome values and values as reported.",
    "decisions": "Eligibility decisions (record, eligible, rule) and the named analysis sets.",
    "flags_full": "Per flag: kind, category, record ids, the numbers compared, the Critic's class and reason.",
    "results": "The run's status, outcome, verdict and exploratory label; the dataset freeze; analysis "
               "results; calibration results.",
    "coverage": "Per source: search status and kind of nothing found; the run's search coverage lists.",
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
    "outcome": "The run's status, outcome, verdict and exploratory label.",
})

_ANALYSIS = frozenset({"claim", "domain", "sources_meta", "plan", "records_full", "decisions", "flags_full",
                       "results", "coverage", "stage_outputs", "run_cost"})
_GAP_REPORT = frozenset({"claim", "domain", "sources_meta", "plan", "coverage", "stored_record_counts",
                         "decisions", "flags_kind", "condition_summaries"})

ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
    "planner": MappingProxyType({
        "before_lock": frozenset({"claim", "domain", "sources_meta", "tag_values", "record_counts"}),
    }),
    "curator": MappingProxyType({
        "curation": frozenset({"plan_fields_to_extract", "sources_meta", "source_content"}),
    }),
    "critic": MappingProxyType({
        "curation": frozenset({"sources_meta", "record_metadata", "flags_kind"}),
    }),
    "analyst": MappingProxyType({
        "analysis": _ANALYSIS,
        # Owner, 2026-10-05: the gap report gets everything except outcomes, plus condition summaries.
        "closed_without_freeze": _GAP_REPORT,
    }),
    "commentator": MappingProxyType({
        "final": _ANALYSIS,
        # Owner, 2026-10-05: with no dataset frozen, only what the Analyst received for the gap
        # report, plus the Analyst's gap report and the run's outcome. No outcome values, no
        # row-level records.
        "final_without_freeze": _GAP_REPORT | {"gap_report", "outcome"},
    }),
})


def allowed(role: str, stage: str) -> frozenset[str]:
    """The fields `role` may receive at `stage`; empty for any role or stage not listed."""
    return ALLOWED.get(role, {}).get(stage, frozenset())


# The fields that can be the outcome of a plan. The Planner does not know which one its
# plan will choose before the lock, so every one of them is treated as an outcome
# everywhere outcomes are withheld: their values never reach the Planner, the Critic or
# the gap report, and no count is ever broken down by their values.
OUTCOME_FIELDS = frozenset({"yield_strength", "yield_strength_sd", "ultimate_tensile_strength",
                            "hardness", "hardness_sd"})

# Fields whose values are categories (text from a fixed or source vocabulary), shown to the
# Critic and counted for the Planner and the gap report.
CATEGORY_FIELDS = ("test_type", "test_temperature_band", "phase_class", "microstructure", "processing_method")

# The non-outcome measured conditions summarized for the gap report (owner, 2026-10-05).
CONDITION_RANGE_FIELDS = ("grain_size", "test_temperature")
CONDITION_COUNT_FIELDS = ("test_type", "phase_class")

# sources_meta: a fixed set of named plain fields (owner, 2026-10-05). Free text such as
# the address or the version label never reaches a role through this field.
SOURCE_META_FIELDS = ("key", "name", "source_type", "data_kind", "licence", "grouping_unit",
                      "fields_available")

# The named parts of a plan (PRD 5.1). The plan model (step 6) stores its content under
# these keys; any other key in a plan's content is withheld from every role.
PLAN_KEYS = ("claim", "hypothesis_version", "variables", "scope", "model", "sufficiency",
             "fields_to_extract", "exclusion_rules", "eligibility_rules", "verdict_statement",
             "sensitivity_analyses")
