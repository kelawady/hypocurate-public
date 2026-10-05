"""Step 6: the code checks that raise flags (PRD 5.3; `hypocurate.pipeline.flags`).

Records here are in the `records_full` format Checks receives through its access object. The
owner's rules (2026-10-05): duplicates and conflicts only between different sources; grain size
within the tolerance to pair (a matching tolerance), yield strength within it for a duplicate
and beyond it for a conflict; a group with several candidates from one source is ambiguous and
nothing is paired on a guess. Checks uses only per-record and pairwise rules: no model, slope,
residual or plan hypothesis.
"""
from __future__ import annotations

import ast
import copy
import random
from pathlib import Path

import pytest

from hypocurate.pipeline import flags as fl
from hypocurate.pipeline.plan import default_plan

PLAN = default_plan(1)
DOI = "10.1016/j.test.2020.001"


def rec(i, source="mpea", comp=None, gs=10.0, ys=400.0, uts=None, doi=DOI, test_type="tension", temp=25.0):
    def v(value, unit=None):
        return {"value": value, "unit": unit, "status": "converted"} if value is not None else \
            {"value": None, "unit": unit, "status": "not_reported", "reason": "blank in the source"}
    return {"id": i, "source": source, "origin": f"{source}.csv:row:{i}", "item_index": 0, "kind": "measured",
            "alloy": "x", "paper_reference": None, "paper_doi": doi, "version_fingerprint": "f" * 64, "reported": {},
            "harmonized": {"composition": v(comp or {"Co": 50.0, "Ni": 50.0}, "at.%"), "grain_size": v(gs, "µm"),
                           "yield_strength": v(ys, "MPa"), "ultimate_tensile_strength": v(uts, "MPa"),
                           "test_type": v(test_type), "test_temperature": v(temp, "°C")}}


def kinds(records, plan=PLAN):
    return [(f.kind, f.category, f.records) for f in fl.raise_flags(plan, records)]


def test_physically_impossible_values_are_flagged_per_record():
    got = kinds([rec(1, uts=399.0), rec(2, uts=400.0), rec(3, gs=0.0, doi="10.1/a"), rec(4, gs=-1.0, doi="10.1/b"),
                 rec(5, gs=0.05, doi="10.1/c")])
    assert got == [("invalid_value", "physically impossible", [1]), ("invalid_value", "physically impossible", [3]),
                   ("invalid_value", "physically impossible", [4])]
    f = fl.raise_flags(PLAN, [rec(1, uts=399.0)])[0]
    assert f.compared_values == {"ultimate_tensile_strength_below_yield_strength": [399.0, 400.0]}


def test_rows_within_one_source_are_never_compared():
    assert kinds([rec(1), rec(2), rec(3, ys=600.0)]) == []


def test_exact_duplicate_and_the_tolerance_on_yield_strength():
    assert kinds([rec(1), rec(2, "controlled_duplicates")]) == [("exact_duplicate", "identical values", [1, 2])]
    assert kinds([rec(1, ys=100.0), rec(2, "controlled_duplicates", ys=101.99)]) == [
        ("exact_duplicate", "within tolerance", [1, 2])]
    assert kinds([rec(1, ys=100.0), rec(2, "controlled_duplicates", ys=102.01)]) == [
        ("values_disagree", "differ beyond tolerance", [1, 2])]
    # Relative to the smaller value, in either order.
    assert kinds([rec(1, ys=102.01), rec(2, "controlled_duplicates", ys=100.0)])[0][0] == "values_disagree"


def test_grain_size_is_a_matching_tolerance_never_a_conflict():
    assert kinds([rec(1, gs=100.0), rec(2, "controlled_duplicates", gs=101.99)]) == [
        ("exact_duplicate", "within tolerance", [1, 2])]
    assert kinds([rec(1, gs=100.0), rec(2, "controlled_duplicates", gs=102.01)]) == []  # separate measurements
    assert kinds([rec(1, gs=1.79), rec(2, "controlled_duplicates", gs=1.8)]) == [
        ("exact_duplicate", "within tolerance", [1, 2])]


def test_a_known_difference_in_paper_or_conditions_means_no_pair():
    other = "controlled_duplicates"
    assert kinds([rec(1), rec(2, other, doi="10.5555/other")]) == []
    assert kinds([rec(1), rec(2, other, test_type="compression")]) == []
    assert kinds([rec(1), rec(2, other, temp=-196.0)]) == []
    assert kinds([rec(1), rec(2, other, comp={"Co": 60.0, "Ni": 40.0})]) == []
    # DOI formatting does not split one paper (step 4's derived key).
    assert kinds([rec(1), rec(2, other, doi=f"https://doi.org/{DOI.upper()}")])[0][0] == "exact_duplicate"


def test_an_unknown_paper_or_condition_gives_a_possible_duplicate_only_if_the_values_match():
    other = "controlled_duplicates"
    assert kinds([rec(1), rec(2, other, doi=None)]) == [("possible_duplicate", "identical values", [1, 2])]
    assert kinds([rec(1), rec(2, other, temp=None)]) == [("possible_duplicate", "identical values", [1, 2])]
    assert kinds([rec(1), rec(2, other, test_type=None)]) == [("possible_duplicate", "identical values", [1, 2])]
    assert kinds([rec(1), rec(2, other, doi=None, ys=500.0)]) == []


def test_the_same_alloy_rule_of_the_plan_decides_which_records_are_compared():
    other = "controlled_duplicates"
    a, b = {"Co": 50.04, "Ni": 49.96}, {"Co": 49.96, "Ni": 50.04}  # both 50.0 / 50.0 at 0.1 at.%
    assert kinds([rec(1, comp=a), rec(2, other, comp=b)])[0][0] == "exact_duplicate"
    c, d = {"Co": 50.06, "Ni": 49.94}, {"Co": 50.04, "Ni": 49.96}  # 50.1 vs 50.0: a known boundary weakness
    assert kinds([rec(1, comp=c), rec(2, other, comp=d)]) == []
    coarse = copy.deepcopy(PLAN)
    coarse["rules"]["same_alloy_decimals"] = 0
    assert kinds([rec(1, comp=c), rec(2, other, comp=d)], coarse)[0][0] == "exact_duplicate"


def test_the_tolerance_is_read_from_the_plan():
    loose = copy.deepcopy(PLAN)
    loose["rules"]["duplicate_tolerance"] = 0.05
    records = [rec(1, ys=100.0), rec(2, "controlled_duplicates", ys=103.0)]
    assert kinds(records)[0][0] == "values_disagree"
    assert kinds(records, loose)[0][0] == "exact_duplicate"


def test_several_candidates_from_one_source_pair_nothing():
    """Owner, 2026-10-05: if a record has more than one candidate in another source, nothing is
    paired automatically and all of them are flagged as possible duplicates."""
    other = "controlled_duplicates"
    one_to_two = kinds([rec(1), rec(2, other), rec(3, other, gs=10.1)])
    assert one_to_two == [("possible_duplicate", "several candidates", [1, 2, 3])]
    two_to_two = kinds([rec(1), rec(2, gs=10.1), rec(3, other), rec(4, other, gs=10.05)])
    assert two_to_two == [("possible_duplicate", "several candidates", [1, 2, 3, 4])]


def test_a_group_whose_records_are_not_all_linked_is_ambiguous():
    """A–B and B–C are candidates, A–C are not (known different papers): nothing is paired."""
    plan = copy.deepcopy(PLAN)
    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
                                 {"source": "controlled_duplicates", "unit": "paper"}]
    got = kinds([rec(1), rec(2, "controlled_duplicates", doi=None), rec(3, "tamu_fcc", doi="10.5555/other")], plan)
    assert got == [("possible_duplicate", "several candidates", [1, 2, 3])]


def test_a_group_with_one_conflicting_pair_is_a_conflict():
    plan = copy.deepcopy(PLAN)
    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
                                 {"source": "controlled_duplicates", "unit": "paper"}]
    # 1 and 2 agree; 3 reports the same measurement 2.25% higher: the whole group is a conflict.
    got = kinds([rec(1, ys=400.0), rec(2, "controlled_duplicates", ys=400.0), rec(3, "tamu_fcc", ys=409.0)], plan)
    assert got == [("values_disagree", "differ beyond tolerance", [1, 2, 3])]
    # A possible link (paper unknown on 2) and a conflicting pair (1, 3) in one group: a conflict.
    got = kinds([rec(1, ys=400.0), rec(2, "controlled_duplicates", ys=400.0, doi=None),
                 rec(3, "tamu_fcc", ys=440.0)], plan)
    assert got[0][0] == "possible_duplicate" and got[0][1] == "several candidates"  # 2-3 not linked


def test_a_dataset_source_is_its_own_paper():
    """Texas A&M (grouped by dataset) cites itself: never paired with a record citing another paper."""
    assert kinds([rec(1), rec(2, "tamu_fcc", doi=None)]) == []


def _world(seed):
    """Records with cross-source copies (exact, within tolerance, conflicting, possible) and
    invalid values, and a Hall-Petch-like trend in the outcomes."""
    rnd = random.Random(seed)
    records, measurement, i = [], {}, 0
    for alloy in range(6):
        comp = {"Co": 30.0 + alloy, "Ni": 70.0 - alloy}
        for size in (1.0, 4.0, 16.0, 64.0):
            m = len(measurement)
            ys = 200.0 + 400.0 / size ** 0.5 + rnd.uniform(-5, 5)
            measurement[m] = ys
            doi = f"10.1/p{alloy}"
            i += 1
            records.append((m, 1.0, rec(i, "mpea", comp, size, ys, uts=ys * rnd.choice([1.2, 0.9]), doi=doi)))
            for source, factor, d in (("controlled_duplicates", (1.0, 1.01, 1.3)[m % 3], doi),
                                      ("tamu_fcc", 1.0, None)):
                # A conflicting copy has no third record, so its group stays a plain conflict.
                if (m < 6 or rnd.random() < 0.6) and not (source == "tamu_fcc" and m % 3 == 2):
                    i += 1
                    records.append((m, factor, rec(i, source, comp, size, ys * factor, uts=ys * factor * 1.2, doi=d)))
    return records


@pytest.mark.parametrize("seed", range(5))
def test_flags_use_only_pairwise_and_per_record_rules(seed):
    """Replacing every measurement's outcome by an arbitrary value (copies keep their ratio to it,
    tensile strength its ratio to yield strength) destroys any relation with grain size, but
    changes no pairwise or per-record relation: the flags are identical. So is removing the
    plan's model, hypotheses and predictor transformation: Checks does not read them."""
    items = _world(seed)
    plan = copy.deepcopy(PLAN)
    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
                                 {"source": "controlled_duplicates", "unit": "paper"}]
    before = kinds([r for _, _, r in items], plan)
    assert {k for k, _, _ in before} >= {"exact_duplicate", "values_disagree", "invalid_value", "possible_duplicate"}
    rnd = random.Random(1000 + seed)
    new = {m: rnd.uniform(50.0, 5000.0) for m in {m for m, _, _ in items}}
    changed = []
    for m, factor, r in items:
        r = copy.deepcopy(r)
        h = r["harmonized"]
        ratio = h["ultimate_tensile_strength"]["value"] / h["yield_strength"]["value"]
        h["yield_strength"]["value"] = new[m] * factor
        h["ultimate_tensile_strength"]["value"] = new[m] * factor * ratio
        changed.append(r)
    blind = copy.deepcopy(plan)
    for k in ("model", "verdict_statement"):
        del blind[k]
    del blind["variables"]["predictor"]["transformation"]
    assert kinds(changed, blind) == before


def test_checks_imports_no_statistics_and_reads_only_the_rules_and_the_outcome_field():
    source = Path(fl.__file__).read_text()
    tree = ast.parse(source)
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
        {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not {m for m in imported if m and m.split(".")[0] in ("numpy", "scipy", "statsmodels", "pandas")}
    assert "hypocurate.pipeline.profile" not in imported
    plan_keys = {n.slice.value for n in ast.walk(tree) if isinstance(n, ast.Subscript)
                 and isinstance(n.value, ast.Name) and n.value.id == "plan" and isinstance(n.slice, ast.Constant)}
    assert plan_keys == {"rules", "variables"}
