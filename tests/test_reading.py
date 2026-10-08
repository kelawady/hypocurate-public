"""Step 8b fix round 1, owner's decision B: "the question as tested", built by code from the scope and exclusion
rules (the Planner's reading, or a fixed plan), with its label. No model call."""
from __future__ import annotations

import pytest

from hypocurate.pipeline import plan as plans
from hypocurate.pipeline import reading

MPEA = "multi-principal-element (high-entropy) alloy"


def test_the_label_says_whose_reading_it_is_and_that_a_person_confirms_it():
    """Owner, F-Q2 (2026-10-07): the labels say what is true in this version (no person confirms the reading yet)."""
    assert reading.LABELS["planner"] == ("the Planner's reading of the claim; not verified by code and, in this "
                                         "version, not confirmed by a person")
    assert reading.LABELS["fixed"] == "the fixed reference plan; not read from the claim"
    assert reading.LABELS["narrower"] == "the narrower plan stored by the original question's narrowing decision"


@pytest.mark.parametrize("rule, words", [
    ({"rule": "grain_size_range", "min": 0.1}, "excluding records with a grain size below 0.1 µm"),
    ({"rule": "grain_size_range", "max": 100.0}, "excluding records with a grain size above 100 µm"),
    ({"rule": "grain_size_range", "min": 0.5, "max": 50.0},
     "excluding records with a grain size outside 0.5 to 50 µm"),
    ({"rule": "temperature_range", "min": 10.0, "max": 30.0},
     "excluding records tested outside 10 to 30 °C"),
    ({"rule": "phase", "values": ["FCC"]}, "excluding records of a phase class other than FCC"),
    ({"rule": "test_type", "values": ["tension"]}, "excluding records of a test type other than tension")])
def test_each_exclusion_rule_in_words(rule, words):
    assert reading.exclusion_words(rule) == words


def test_an_elevated_band_names_its_range_and_no_marks_without_a_reading():
    scope = {"alloy_class": [MPEA], "phase_class": ["FCC"], "test_type": ["compression"],
             "temperature_band": [{"band": "elevated", "min": 900.0, "max": 1100.0}]}
    q = reading.question_as_tested(scope, "yield_strength", [], None, "fixed")
    assert q == {"text": f"yield strength against grain size, in {MPEA}s; phase class FCC; test type compression; "
                         "elevated, 900 to 1100 °C", "label": reading.LABELS["fixed"], "source": "fixed"}


def test_the_reference_plans_reading():
    q = reading.from_plan(plans.reference_plan(1), "fixed")
    assert q["text"] == (f"yield strength against grain size, in {MPEA}s; phase class FCC; test type tension; "
                         "room temperature, 20 to 25 °C; excluding records with a grain size below 0.1 µm")


def test_a_band_at_one_temperature_names_it_once():
    assert reading.band_words({"band": "elevated", "min": 1000.0, "max": 1000.0}) == "elevated, 1000 °C"


def test_two_bands_are_joined_so_that_one_mark_covers_both():
    scope = {"alloy_class": [MPEA], "phase_class": ["FCC"], "test_type": ["tension"],
             "temperature_band": [{"band": "room temperature"}, {"band": "cryogenic", "min": -200.0, "max": -150.0}]}
    stated = {"alloy_class": True, "phase_class": True, "test_type": False, "temperature_band": True}
    q = reading.question_as_tested(scope, "yield_strength", [], stated, "planner")
    assert "room temperature, 20 to 25 °C and cryogenic, -200 to -150 °C (as the claim states)" in q["text"]
