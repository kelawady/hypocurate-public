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
FLAG_CATEGORIES = frozenset({"identical values", "differ beyond tolerance", "within tolerance",
                             "outside scope", "scope not confirmed", "physically impossible"})
ELIGIBILITY_RULES = frozenset({"in_scope", "out_of_scope", "scope_not_confirmed", "invalid_value",
                               "duplicate_counted_once", "model_recalled", "single_grain_size",
                               "excluded_by_rule"})
SENSITIVITY_KEYS = frozenset({"tension_and_compression", "six_batches_as_groups", "same_alloy_1_at_pct",
                              "source_only_assignments", "possible_duplicates_separate",
                              "scope_not_confirmed_included", "removal_after_lock"})
ANALYSIS_SET_KEYS = frozenset({"primary"}) | SENSITIVITY_KEYS


def code(value: Any, vocabulary: frozenset[str]) -> str:
    return value if isinstance(value, str) and value in vocabulary else UNRECOGNIZED


DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]{1,200}")


def doi(value: Any) -> str | None:
    """A DOI if it has DOI syntax (surrounding spaces ignored), None if absent, else the marker.
    A DOI may contain digits: an accepted disclosure (register 'accepted_disclosures')."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return value.strip() if isinstance(value, str) and DOI.fullmatch(value.strip()) else UNRECOGNIZED
