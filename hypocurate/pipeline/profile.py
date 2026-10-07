"""The domain profile for grain-size strengthening (PRD 5.5; build step 6).

One named place for each default of the domain (CLAUDE.md, "How we work" item 12): the
fields to extract, the units, the scope, the exclusion and eligibility rules, the
data-sufficiency minimums, the sensitivity analyses and the tag lists. The register
(`hypocurate/assumptions.json`) names these settings.

**The defaults are copied into each plan at the rules lock** (owner, 2026-10-05): every
setting that affects which records are eligible or how they are grouped is a value of the
locked plan (`PLAN_SCHEMA`), and the code that decides eligibility and grouping reads it from
the plan only, never from here. A plan records the profile name and version its defaults came
from. Raise `PROFILE_VERSION` whenever a default here changes.
"""
from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from hypocurate.sources.normalize import SAME_ALLOY_DECIMALS

PROFILE_NAME = "grain_size_strengthening"
PROFILE_VERSION = 2  # 2: the calibration defaults (step 7)

# --- Variables and the supported model (PRD 5.7) ---------------------------------------
OUTCOME = ("yield_strength", "MPa")
PREDICTOR = ("grain_size", "µm")
TRANSFORMATION = "inverse_square_root"
MODEL = "hall_petch_alloy_intercepts"
ALPHA = 0.05  # one-sided test of k > 0 (register 'significance_threshold'; p < alpha)
FIELDS_TO_EXTRACT = ("composition", "grain_size", "yield_strength", "ultimate_tensile_strength", "test_type",
                     "test_temperature", "test_temperature_band", "phase_class", "microstructure")

# --- Scope -------------------------------------------------------------------------------
ALLOY_CLASSES = ("multi-principal-element (high-entropy) alloy",)
PERMITTED_TEST_TYPES = ("tension",)  # register 'permitted_test_types' (owner, 2026-10-05)
TEMPERATURE_BANDS = ("room temperature",)
ROOM_TEMPERATURE_C = (20.0, 25.0)  # register 'room_temperature_scope': reported 20 to 25 °C
PHASE_CLASSES = ("FCC",)
# Single phase (register 'fcc_microstructure_scope'): the microstructure is exactly the phase
# class ("FCC"), not the phase column.
SINGLE_PHASE = "required"

# --- Exclusion rule from the menu (PRD 5.2) ----------------------------------------------
GRAIN_SIZE_FLOOR_UM = 0.1  # register 'grain_size_floor': exclude below 0.1 µm

# --- Eligibility and duplicates (PRD 5.3) ------------------------------------------------
MIN_GRAIN_SIZES_PER_ALLOY = 2  # register 'alloy_eligibility'
SAME_ALLOY_DECIMALS_DEFAULT = SAME_ALLOY_DECIMALS  # register 'same_alloy_rule': 0.1 at.%
# Register 'values_disagree_tolerance': |a - b| / min(|a|, |b|). A matching tolerance for
# grain size, a duplicate-or-conflict threshold for yield strength.
DUPLICATE_TOLERANCE = 0.02
# Register 'duplicate_survivor_rule', rule 2: the fixed source order.
SURVIVOR_SOURCE_ORDER = ("mpea", "tamu_fcc", "controlled_duplicates")
# Register 'assigned_value_statuses': the statuses whose values the default plan accepts.
ACCEPTED_VALUE_STATUSES = ("converted", "assigned_from_source", "assigned_by_decision")
# The grouping unit of each source for the grouped standard errors (register 'tamu_grouping_unit',
# 'paper_grouping_by_doi').
GROUPING = MappingProxyType({"mpea": "paper", "tamu_fcc": "dataset", "controlled_duplicates": "paper"})

# --- Data sufficiency (PRD 5.8; register 'fixed_minimums', 'sufficiency_options') ---------
SUFFICIENCY_OPTION = "fixed_minimum"
FIXED_MINIMUMS = MappingProxyType({"min_records": 30, "min_alloys": 5, "min_groups": 10, "min_resid_df": 10})

# --- Calibration on generated data (PRD 5.10; owner, 2026-10-05; step 7) ----------------
# Reported both ways, each method fixed at the rules lock (register 'calibration_both_ways'):
# 'fixed' uses the scatter and per-paper shift below (PRD 5.10's illustrative values, register
# 'calibration_simulation'); 'estimated' estimates them by code from the frozen residuals with
# Henderson's method III (register 'calibration_noise_levels'). A flag, never a gate.
CALIBRATION_METHODS = ("fixed", "estimated")
CALIBRATION_SIMULATIONS = 2000  # per simulated world
CALIBRATION_SCATTER_MPA = 60.0  # per record, fixed method
CALIBRATION_SHIFT_MPA = 40.0  # per group (paper), fixed method
CALIBRATION_ESTIMATION = "henderson_iii"
# The smallest effect that matters (register 'smallest_effect'): a query setting, in MPa·µm^0.5.
# The effect world of the calibration and the estimated power use it.
SMALLEST_EFFECT = 150.0

# --- Sensitivity analyses (owner, 2026-10-05; register 'sensitivity_one_change') ---------
# Each differs from the primary set in exactly one named respect; descriptive only, never
# changes the verdict, no adjustment for there being nine. The ninth, without the most influential
# paper, added by the owner on 2026-10-06 (step 7b; register 'most_influential_paper_set').
SENSITIVITY_ANALYSES = ("no_exclusions", "tension_and_compression", "six_batches_as_groups", "same_alloy_1_at_pct",
                        "source_only_assignments", "scope_not_confirmed_included",
                        "possible_duplicates_separate", "conflicts_survivor_value",
                        "without_most_influential_paper")

# --- Tags (PRD 5.5; register 'tag_starting_lists'; seeded by migration 0002) -------------
TAG_STARTING_LISTS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "property": ("yield strength", "ultimate tensile strength", "hardness", "elongation", "fatigue life"),
    "alloy_class": ("multi-principal-element (high-entropy) alloy", "steel", "aluminium alloy", "titanium alloy",
                    "nickel alloy", "copper alloy", "magnesium alloy", "other"),
    "test_condition": ("room-temperature tension", "room-temperature compression", "elevated temperature",
                       "cryogenic", "hardness test", "fatigue"),
})
# How a plan maps to its three tags (one per kind).
PROPERTY_TAGS = MappingProxyType({"yield_strength": "yield strength",
                                  "ultimate_tensile_strength": "ultimate tensile strength", "hardness": "hardness"})
TEST_CONDITION_TAGS = MappingProxyType({("room temperature", "tension"): "room-temperature tension",
                                        ("room temperature", "compression"): "room-temperature compression",
                                        # Step 8a (owner, 2026-10-06, Q4): values seeded by migration 0002.
                                        ("elevated", "tension"): "elevated temperature",
                                        ("elevated", "compression"): "elevated temperature",
                                        ("cryogenic", "tension"): "cryogenic",
                                        ("cryogenic", "compression"): "cryogenic"})
# The bands a plan may name, one per plan (step 8a, owner 2026-10-06, Q4).
SUPPORTED_BANDS = ("room temperature", "elevated", "cryogenic")
