"""Step 7b (owner, 2026-10-06): the sensitivity set "without the most influential paper"; register
'most_influential_paper_set'.

The set is the primary set minus every record of the paper (the group under the primary grouping)
that holds the largest share of slope information, I_g = the group's sum of squared within-alloy
deviations of the transformed grain size (register 'effective_papers'). The paper is chosen by code at
Inclusion, from grain sizes, alloys and groups only: Inclusion receives no outcome value. Ties (shares
within the numerical zero of the largest) are broken by each tied paper's earliest record under the
plan's survivor source order, then the lowest row in the source file, then the stable identity. The
set differs from primary in exactly this one respect; it is descriptive and never changes the verdict.
"""
from __future__ import annotations

import copy
import math
from collections import defaultdict

import numpy as np
import pytest

import generator as g
from hypocurate.pipeline import analysis
from hypocurate.pipeline import eligibility as el
from hypocurate.pipeline import statistics as st
from hypocurate.pipeline.plan import default_plan
from test_eligibility import cond, decide

PLAN = default_plan(1)
KEY = "without_most_influential_paper"
CO, CN = {"Co": 50.0, "Ni": 50.0}, {"Co": 40.0, "Ni": 60.0}


def information_test_side(rows):
    """I_g from (alloy, group, grain size), written independently of the package: alloys with two
    or more distinct grain sizes, x = d^-1/2, deviations from the alloy's mean x."""
    by_alloy = defaultdict(list)
    for alloy, group, d in rows:
        by_alloy[alloy].append((group, d ** -0.5))
    info = defaultdict(float)
    for members in by_alloy.values():
        xs = [x for _, x in members]
        if max(xs) - min(xs) <= 1e-10 * max(xs):
            continue
        mean = sum(xs) / len(xs)
        for group, x in members:
            info[group] += (x - mean) ** 2
    return dict(info)


def _records():
    """Three papers on two alloys: p1 has the widest grain-size range."""
    return [cond(1, comp=CO, gs=1.0, paper="p1"), cond(2, comp=CO, gs=100.0, paper="p1"),
            cond(3, comp=CO, gs=10.0, paper="p2"), cond(4, comp=CO, gs=12.0, paper="p2"),
            cond(5, comp=CN, gs=5.0, paper="p3"), cond(6, comp=CN, gs=6.0, paper="p3")]


def test_the_slope_information_is_the_owners_formula():
    """`statistics.slope_information` against the independent computation."""
    recs = _records()
    got = st.slope_information([(f"id{r['id']}", el.alloy(r, 1), f"paper:{r['paper']}", r["values"]["grain_size"])
                                for r in recs], "inverse_square_root")
    expected = information_test_side([(el.alloy(r, 1), f"paper:{r['paper']}", r["values"]["grain_size"]) for r in recs])
    assert got.keys() == expected.keys()
    for k in got:
        assert got[k] == pytest.approx(expected[k], rel=1e-12)


def test_the_design_uses_the_same_slope_information():
    """The effective number of papers and the largest share stored with every result come from the
    same function (one place), on generated data with several papers."""
    data = g.frozen_data(g.SPECS["effect_many_papers"])
    obs = analysis.observations(data["records"], g.plan(), "primary")
    d = st.design(obs, "inverse_square_root")
    info = st.slope_information([(o.identity, o.alloy, o.group, o.grain_size) for o in obs], "inverse_square_root")
    values = np.array(list(info.values()))
    assert d.effective_papers == pytest.approx(values.sum() ** 2 / (values @ values), rel=1e-12)
    assert d.largest_paper_share == pytest.approx(values.max() / values.sum(), rel=1e-12)


def test_the_set_is_primary_minus_the_paper_with_the_largest_share():
    records = _records()
    primary = decide(records)
    assert set(primary.values()) == {"in_scope"}
    rules = decide(records, key=KEY)
    assert rules == {1: "most_influential_paper", 2: "most_influential_paper", 3: "in_scope", 4: "in_scope",
                     5: "in_scope", 6: "in_scope"}
    info = information_test_side([(el.alloy(r, 1), r["paper"], r["values"]["grain_size"]) for r in records])
    assert max(info, key=info.get) == "p1"
    chosen = el.most_influential(PLAN, {r["id"]: r for r in records}, sorted(primary))
    assert chosen["group"] == "paper:" + "p1" and chosen["records"] == [1, 2]
    assert chosen["share"] == pytest.approx(info["p1"] / sum(info.values()), rel=1e-12)
    assert chosen["tied"] == ["paper:p1"]


def test_it_differs_from_primary_in_exactly_this_one_respect():
    """Every record keeps its primary rule except the chosen paper's records, which are not in the
    set (rule `most_influential_paper`); no other rule is applied again."""
    records = [*_records(), cond(7, comp=CO, gs=10.0, doi=False), cond(8, test_type="compression"),
               cond(9, comp={"Fe": 50.0, "Ni": 50.0}, gs=3.0, paper="p4")]
    primary, other = decide(records), decide(records, key=KEY)
    differing = {i for i in primary if primary[i] != other[i]}
    assert differing == {1, 2} and {other[i] for i in differing} == {"most_influential_paper"}
    assert primary[9] == "single_grain_size" and other[9] == "single_grain_size"


def test_only_primary_members_count():
    """A record outside the primary set does not count toward its paper's share: here the widest
    range belongs to a compression test (out of scope), so its paper is not chosen."""
    records = [cond(1, comp=CO, gs=1.0, paper="p1", test_type="compression"), cond(2, comp=CO, gs=100.0, paper="p1"),
               cond(3, comp=CO, gs=10.0, paper="p2"), cond(4, comp=CO, gs=40.0, paper="p2")]
    assert decide(records, key=KEY) == {1: "out_of_scope", 2: "in_scope", 3: "most_influential_paper",
                                        4: "most_influential_paper"}


def _tie(ids, rows, sources=("mpea", "mpea")):
    """Two papers on two alloys with identical designs: equal shares."""
    (a1, a2), (b1, b2) = ids
    return [cond(a1, sources[0], comp=CO, gs=10.0, paper="pa", row=rows[0]),
            cond(a2, sources[0], comp=CO, gs=40.0, paper="pa", row=rows[0] + 1),
            cond(b1, sources[1], comp=CN, gs=10.0, paper="pb", row=rows[1]),
            cond(b2, sources[1], comp=CN, gs=40.0, paper="pb", row=rows[1] + 1)]


def _chosen(records):
    return el.most_influential(PLAN, {r["id"]: r for r in records}, sorted(r["id"] for r in records))


@pytest.mark.parametrize("ids", [((1, 2), (3, 4)), ((3, 4), (1, 2)), ((10, 2), (7, 1))])
def test_a_tie_is_broken_by_the_lowest_row_whatever_the_ids_or_order(ids):
    """Equal shares: the paper whose earliest record has the lowest row in the source file (here
    'pb', rows 3-4, before 'pa', rows 50-51), whatever the database ids or the order of records."""
    records = _tie(ids, rows=(50, 3))
    for order in (records, records[::-1], records[1::2] + records[::2]):
        chosen = _chosen(order)
        assert chosen["group"] == "paper:pb" and chosen["tied"] == ["paper:pa", "paper:pb"]
        assert chosen["share"] == pytest.approx(0.5)


def test_a_tie_follows_the_survivor_source_order_before_the_row():
    """The plan's survivor source order comes first: an MPEA paper at row 50 beats an extract paper
    at row 3 (MPEA is first in the order)."""
    chosen = _chosen(_tie(((1, 2), (3, 4)), rows=(50, 3), sources=("mpea", "controlled_duplicates")))
    assert chosen["group"] == "paper:pa"


def test_without_any_slope_information_nothing_is_removed():
    """Grain sizes equal after the transformation: the set equals primary, and the choice says why."""
    records = [cond(1, gs=9.0), cond(2, gs=9.000000000000002)]
    assert decide(records) == {1: "in_scope", 2: "in_scope"}
    assert decide(records, key=KEY) == decide(records)
    chosen = _chosen(records)
    assert chosen["group"] is None and chosen["records"] == [] and chosen["reason"] == "no_slope_information"
    # Transformed values that differ by a few units in the last place (not exactly equal) are still no
    # contrast: the alloy rule of `statistics.has_contrast` applies before any information is counted.
    near = [cond(1, gs=9.0), cond(2, gs=9.000000000000004)]
    assert 9.0 ** -0.5 != 9.000000000000004 ** -0.5
    assert st.slope_information([(f"id{r['id']}", el.alloy(r, 1), "paper:p1", r["values"]["grain_size"])
                                 for r in near], "inverse_square_root") == {}
    assert _chosen(near)["reason"] == "no_slope_information"


def test_the_choice_uses_no_outcome_value():
    """The records Inclusion receives carry no outcome value; the choice is the same when every
    outcome field is absent, and when made-up outcome values are added (they are not read)."""
    records = _records()
    assert all("yield_strength" not in r["values"] for r in records)
    planted = copy.deepcopy(records)
    for n, r in enumerate(planted):
        r["values"]["yield_strength"] = 1e6 * (-1) ** n
        r["outcome"] = -r["values"]["yield_strength"]
    assert _chosen(planted) == _chosen(records)
    assert decide(planted, key=KEY) == decide(records, key=KEY)


def test_the_change_is_named_and_in_the_default_plan():
    assert KEY in PLAN["sensitivity_analyses"] and KEY in el.SENSITIVITY_CHANGES
    assert "most influential" in el.SENSITIVITY_CHANGES[KEY]
    assert not el.needs_own_flags(PLAN, KEY)  # it changes no matching setting: primary's flags apply


def test_the_numerical_zero_decides_ties():
    """Shares within RELATIVE_ZERO of the largest are tied (the register's numerical zero)."""
    records = _tie(((1, 2), (3, 4)), rows=(50, 3))
    records[1]["values"]["grain_size"] = 40.0 * (1 + 1e-14)
    chosen = _chosen(records)
    assert chosen["tied"] == ["paper:pa", "paper:pb"] and chosen["group"] == "paper:pb"
    records[1]["values"]["grain_size"] = 41.0
    assert _chosen(records)["tied"] == ["paper:pa"]
    assert math.isclose(st.RELATIVE_ZERO, 1e-10)
