"""Controlled vocabularies of the access layer (step 5 review, finding 3; owner, 2026-10-05).

Text that reaches a role through a blinded view (the Planner, the Critic, the gap report)
comes from a fixed vocabulary, or is replaced by the marker `UNRECOGNIZED`. The stored
value is never changed. Unrecognized values are counted per field (never shown), so that
a source with unfamiliar labels is noticed (owner's addition, 2026-10-05).

Adding a value to a vocabulary is a register change that needs the owner's approval
(entries 'category_vocabularies' and 'code_vocabularies').

This module imports nothing from the database or the sources, so any module may use it.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Iterable, Mapping

UNRECOGNIZED = "unrecognized"

# The record fields whose values are categories.
CATEGORY_FIELDS = ("test_type", "test_temperature_band", "phase_class", "microstructure", "processing_method")

# --- Category values of records (built from the frozen sources' actual values) ----------

TEST_TYPES = frozenset({"tension", "compression"})
TEMPERATURE_BANDS = frozenset({"room temperature", "cryogenic", "elevated"})
PHASE_CLASSES = frozenset({"FCC", "BCC", "other"})
# A microstructure is one or more of these tokens joined by "+" (covers all 40 MPEA values).
MICROSTRUCTURE_TOKENS = frozenset({"FCC", "BCC", "B2", "HCP", "L12", "Laves", "Sec.", "Other"})
PROCESSING_METHODS = frozenset({"CAST", "WROUGHT", "ANNEAL", "POWDER", "OTHER"})

CATEGORY_VOCABULARIES: Mapping[str, frozenset[str]] = {
    "test_type": TEST_TYPES, "test_temperature_band": TEMPERATURE_BANDS, "phase_class": PHASE_CLASSES,
    "processing_method": PROCESSING_METHODS,
}


# --- What the Curator may propose (step 8a; owner, Q2) -------------------------------------
# Per target field: its vocabulary (a value must be one of these) or, for the test temperature, a
# number in °C. The fields a table may lack; the Curator proposes a source-wide value for them only
# where the table gives none. The same list is the database's (models.CURATION_FIELDS).
CURATION_TARGETS: Mapping[str, Mapping[str, Any]] = {
    "test_type": {"vocabulary": sorted(TEST_TYPES)},
    "phase_class": {"vocabulary": sorted(PHASE_CLASSES)},
    "test_temperature": {"unit": "°C"},
    "test_temperature_band": {"vocabulary": sorted(TEMPERATURE_BANDS)},
    "microstructure": {"vocabulary": sorted(MICROSTRUCTURE_TOKENS),
                       "form": "one or more of the vocabulary joined by '+'"},
}


def category(field: str, value: Any) -> str:
    """A category value as a blinded view shows it: itself if it is in the field's
    vocabulary, otherwise `UNRECOGNIZED`."""
    if not isinstance(value, str):
        return UNRECOGNIZED
    if field == "microstructure":
        tokens = value.split("+")
        return value if tokens and all(t in MICROSTRUCTURE_TOKENS for t in tokens) else UNRECOGNIZED
    return value if value in CATEGORY_VOCABULARIES.get(field, frozenset()) else UNRECOGNIZED


def unrecognized_counts(values: Iterable[tuple[str, Any]]) -> dict[str, int]:
    """How many values of each field are unrecognized: counts only, never the values."""
    counts = Counter(f for f, v in values if category(f, v) == UNRECOGNIZED)
    return dict(sorted(counts.items()))


# --- Codes written by our own code (steps 6 and 7 must use these) ------------------------

FLAG_KINDS = frozenset({"exact_duplicate", "possible_duplicate", "values_disagree", "out_of_scope",
                        "scope_not_confirmed", "invalid_value", "model_recalled"})
# Step 6 additions (owner, 2026-10-05): the category "several candidates" (an ambiguous match
# group), the rules "missing_value", "identity_unresolved" and "conflict_unresolved", and the
# sensitivity keys "no_exclusions" and "conflicts_survivor_value". Step 7b (owner, 2026-10-06): the
# rules "group_unknown" and "most_influential_paper", the key "without_most_influential_paper".
FLAG_CATEGORIES = frozenset({"identical values", "differ beyond tolerance", "within tolerance",
                             "outside scope", "scope not confirmed", "physically impossible",
                             "several candidates"})
ELIGIBILITY_RULES = frozenset({"in_scope", "out_of_scope", "scope_not_confirmed", "invalid_value",
                               "duplicate_counted_once", "model_recalled", "single_grain_size",
                               "excluded_by_rule", "missing_value", "identity_unresolved",
                               "conflict_unresolved", "group_unknown", "most_influential_paper"})
SENSITIVITY_KEYS = frozenset({"tension_and_compression", "six_batches_as_groups", "same_alloy_1_at_pct",
                              "source_only_assignments", "possible_duplicates_separate",
                              "scope_not_confirmed_included", "removal_after_lock", "no_exclusions",
                              "conflicts_survivor_value", "without_most_influential_paper"})
ANALYSIS_SET_KEYS = frozenset({"primary"}) | SENSITIVITY_KEYS

# The Critic's classes of a flag (step 8b; owner, 2026-10-07, A7): code -> the wording shown to people.
# The database holds the same codes (migration 0006, ck_flag_critic_class). No code decision reads them.
CRITIC_CLASSES: Mapping[str, str] = {
    "same_measurement": "same measurement reported twice",
    "different_specimens_or_conditions": "different specimens or conditions",
    "possible_transcription_or_unit_error": "possible transcription or unit error",
    "cannot_tell": "cannot tell from the metadata",
}
CRITIC_REASON_MAX = 300  # characters; shown to people only (A7)


# Codes in the locked plan's rules (step 6): the registered sources, grouping units, value
# statuses, domain profiles, and whether single phase is required.
SOURCE_KEYS = frozenset({"mpea", "tamu_fcc", "controlled_duplicates",
                         "extracted_pilot"})  # Sprint 2 pilot (R9; register 'pilot_extracted_source')
GROUPING_UNITS = frozenset({"paper", "dataset", "batch"})
VALUE_STATUSES = frozenset({"converted", "assigned_from_source", "assigned_by_decision"})
PROFILE_NAMES = frozenset({"grain_size_strengthening"})
SINGLE_PHASE = frozenset({"required", "not_required"})
# Step 7 (owner, 2026-10-05): the calibration methods and the estimation method of the
# 'estimated' calibration (register 'calibration_both_ways', 'calibration_noise_levels').
CALIBRATION_METHODS = frozenset({"fixed", "estimated"})
ESTIMATION_METHODS = frozenset({"henderson_iii"})


def code(value: Any, vocabulary: frozenset[str]) -> str:
    return value if isinstance(value, str) and value in vocabulary else UNRECOGNIZED


DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]{1,200}")


def doi(value: Any) -> str | None:
    """A DOI if it has DOI syntax (surrounding spaces ignored), None if absent, else the marker.
    A DOI may contain digits: an accepted disclosure (register 'accepted_disclosures')."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return value.strip() if isinstance(value, str) and DOI.fullmatch(value.strip()) else UNRECOGNIZED
