"""Step 8a: plans for other temperature bands (owner, 2026-10-06, Q4; a safeguard change: plan
validation and eligibility rule 3).

One band per plan: room temperature, elevated or cryogenic. A plan for elevated or cryogenic names
the claim's temperature range in its rules (`temperature_range`); a room-temperature plan does not
(its range is the room-temperature rule, unchanged). Rule 3 under a non-room-temperature plan: a
reported temperature inside the range is in scope, outside it out of scope; a band alone, with no
number, is "scope not confirmed" when it is the plan's band and out of scope otherwise. The
reference plan is unchanged, so its fingerprint and the reference numbers are too.
"""
from __future__ import annotations

import copy

import pytest

from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline import plan as pl
from test_eligibility import cond

# The reference plan's fingerprint on main before step 8a (cd2b3be), for hypothesis version 1,
# computed from a checkout of that commit.
REFERENCE_FINGERPRINT_ON_MAIN = "830b5343d0bf6db763c6cb2292189a29a0de11170e78d4202cd18669a5aa2c91"


def plan_for(band: str, low=None, high=None, test_type="tension") -> dict:
    p = pl.default_plan(1)
    p["scope"]["temperature_band"] = [band]
    p["scope"]["test_type"] = [test_type]
    if low is not None or high is not None:
        p["rules"]["temperature_range"] = {k: v for k, v in (("min", low), ("max", high)) if v is not None}
    return p


def test_the_reference_plan_is_unchanged():
    ref = pl.reference_plan(1)
    assert "temperature_range" not in ref["rules"] and ref["scope"]["temperature_band"] == ["room temperature"]
    assert pl.validate(ref) == ref
    assert pl.fingerprint(ref) == REFERENCE_FINGERPRINT_ON_MAIN


@pytest.mark.parametrize("band, low, high", [("elevated", 950.0, 1050.0), ("cryogenic", -200.0, -150.0)])
def test_a_plan_for_another_band_names_its_range(band, low, high):
    p = plan_for(band, low, high)
    assert pl.validate(p)["rules"]["temperature_range"] == {"min": low, "max": high}
    with pytest.raises(pl.PlanError, match="temperature range"):
        pl.validate(plan_for(band))


@pytest.mark.parametrize("plan, match", [
    (lambda: plan_for("room temperature", 20.0, 25.0), "temperature range"),     # room temperature names none
    (lambda: plan_for("elevated", 20.0, 1050.0), "above room temperature"),      # overlaps room temperature
    (lambda: plan_for("cryogenic", -200.0, 21.0), "below room temperature"),
    (lambda: plan_for("elevated", 1050.0, 950.0), "temperature range"),           # min above max
    (lambda: plan_for("elevated", 950.0), "temperature range"),                   # one end only
    (lambda: plan_for("warm", 950.0, 1050.0), "outside PLAN_SCHEMA"),           # not a band of the vocabulary
])
def test_invalid_temperature_plans_are_refused(plan, match):
    with pytest.raises(pl.PlanError, match=match):
        pl.validate(plan())


def test_one_band_per_plan():
    p = plan_for("elevated", 950.0, 1050.0)
    p["scope"]["temperature_band"] = ["room temperature", "elevated"]
    with pytest.raises(pl.PlanError, match="one band"):
        pl.validate(p)


@pytest.mark.parametrize("band, test_type, tag", [("elevated", "tension", "elevated temperature"),
                                                  ("elevated", "compression", "elevated temperature"),
                                                  ("cryogenic", "tension", "cryogenic"),
                                                  ("cryogenic", "compression", "cryogenic")])
def test_the_test_condition_tag_of_another_band(band, test_type, tag):
    low, high = (950.0, 1050.0) if band == "elevated" else (-200.0, -150.0)
    assert pl.tags_for(pl.validate(plan_for(band, low, high, test_type)))["test_condition"] == tag


@pytest.mark.parametrize("record, verdict", [
    (cond(1, temp=1000.0), "in"),
    (cond(1, temp=1100.0), "in"),                       # the range includes its ends
    (cond(1, temp=800.0), "out"),
    (cond(1, temp=25.0), "out"),
    (cond(1, temp=None, band="elevated"), "unconfirmed"),  # a band alone does not confirm the range
    (cond(1, temp=None, band="room temperature"), "out"),
    (cond(1, temp=None), "unconfirmed"),
])
def test_rule_3_under_an_elevated_plan(record, verdict):
    st = el.settings(plan_for("elevated", 900.0, 1100.0))
    assert el.scope(record, st) == verdict


@pytest.mark.parametrize("record, verdict", [
    (cond(1, temp=22.0), "in"),
    (cond(1, temp=1000.0), "out"),
    (cond(1, temp=None, band="room temperature"), "in"),   # unchanged: the band decides when accepted
    (cond(1, temp=None, band="elevated"), "out"),
])
def test_rule_3_under_a_room_temperature_plan_is_unchanged(record, verdict):
    assert el.scope(record, el.settings(pl.default_plan(1))) == verdict


def test_the_range_comes_from_the_plan():
    narrow = el.settings(plan_for("elevated", 990.0, 1010.0))
    wide = el.settings(plan_for("elevated", 900.0, 1100.0))
    record = cond(1, temp=950.0)
    assert (el.scope(record, narrow), el.scope(record, wide)) == ("out", "in")


def test_every_sensitivity_set_keeps_the_range():
    p = plan_for("elevated", 900.0, 1100.0)
    for key in p["sensitivity_analyses"]:
        assert el.settings(p, key).temperature_range == (900.0, 1100.0)
    assert copy.deepcopy(p) == p
