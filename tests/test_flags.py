"""Step 6: the code checks that raise flags (PRD 5.3; `hypocurate.pipeline.flags`).

Records here are in the `records_full` format Checks receives through its access object. The
owner's rules (2026-10-05): duplicates and conflicts only between different sources; grain size
within the tolerance to pair (a matching tolerance), yield strength within it for a duplicate
and beyond it for a conflict; a group with several candidates from one source is ambiguous and
nothing is paired on a guess. Checks uses per-record rules and pairwise comparisons that feed a
whole-group classification: no model, slope,
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


def rec(i, source="mpea", comp=None, gs=10.0, ys=400.0, uts=None, doi=DOI, test_type="tension", temp=25.0,
        reference=None):
    def v(value, unit=None):
        return {"value": value, "unit": unit, "status": "converted"} if value is not None else \
            {"value": None, "unit": unit, "status": "not_reported", "reason": "blank in the source"}
    return {"id": i, "source": source, "origin": f"{source}.csv:row:{i}", "item_index": 0, "kind": "measured",
            "alloy": "x", "paper_reference": reference, "paper_doi": doi, "version_fingerprint": "f" * 64, "reported": {},
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
    # 1 and 2 agree; 3 reports the same measurement 2.25% higher: the whole group is a conflict,
    # and the definite exact pair 1-2 is kept as its own flag (confirmation, 2026-10-06).
    got = kinds([rec(1, ys=400.0), rec(2, "controlled_duplicates", ys=400.0), rec(3, "tamu_fcc", ys=409.0)], plan)
    assert got == [("values_disagree", "differ beyond tolerance", [1, 2, 3]),
                   ("exact_duplicate", "identical values", [1, 2])]
    # A possible link (paper unknown on 2) and a conflicting pair (1, 3) in one group: a conflict.
    got = kinds([rec(1, ys=400.0), rec(2, "controlled_duplicates", ys=400.0, doi=None),
                 rec(3, "tamu_fcc", ys=440.0)], plan)
    # 2-3 not linked: ambiguous; the definite conflict 1-3 is kept as its own flag (review finding 4).
    assert got == [("possible_duplicate", "several candidates", [1, 2, 3]),
                   ("values_disagree", "differ beyond tolerance", [1, 3])]


def test_paper_identity_does_not_depend_on_the_grouping_setting():
    """Re-check finding 2a, the reviewer's case: MPEA grouped by dataset, the extract by paper.
    Identical records citing the same DOI are still the same paper, so an exact duplicate.
    Grouping is used only for clustering in the analysis."""
    plan = copy.deepcopy(PLAN)
    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "dataset"}, {"source": "tamu_fcc", "unit": "dataset"},
                                 {"source": "controlled_duplicates", "unit": "paper"}]
    assert kinds([rec(1), rec(2, "controlled_duplicates")], plan) == [("exact_duplicate", "identical values", [1, 2])]
    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
                                 {"source": "controlled_duplicates", "unit": "paper"}]
    # Whatever the grouping: unequal DOIs are different papers; a missing DOI is unknown.
    assert kinds([rec(1), rec(2, "tamu_fcc", doi="10.5555/other")], plan) == []
    assert kinds([rec(1), rec(2, "tamu_fcc", doi=None, reference="Mulukutla et al. 2026")], plan)[0][0] == \
        "possible_duplicate"


def test_without_a_doi_the_normalized_paper_reference_identifies_the_paper():
    """Both records without a DOI: the same reference (spaces and case aside) is the same paper,
    another reference is another paper; a reference against a DOI or nothing is unknown."""
    a = rec(1, "tamu_fcc", doi=None, reference="Mulukutla, M. et al. (2026).  Dataset v1.1.0")
    same = rec(2, "controlled_duplicates", doi=None, reference="mulukutla, m. et al. (2026). dataset v1.1.0")
    other = rec(3, "controlled_duplicates", doi=None, reference="Another paper (2019)")
    assert kinds([a, same]) == [("exact_duplicate", "identical values", [1, 2])]
    # Unequal reference text alone is unknown, not a different paper (confirmation, 2026-10-06).
    assert kinds([a, other])[0][0] == "possible_duplicate"
    assert kinds([a, rec(4, "controlled_duplicates", doi=None)])[0][0] == "possible_duplicate"


def test_physical_validity_does_not_depend_on_the_outcome_setting():
    """Re-check finding 2b, the reviewer's case: with tensile strength as the outcome (a plan that
    bypassed validation), tensile strength 399 below yield strength 400 is still invalid."""
    plan = copy.deepcopy(PLAN)
    plan["variables"]["outcome"]["field"] = "ultimate_tensile_strength"
    assert kinds([rec(1, uts=399.0)], plan) == [("invalid_value", "physically impossible", [1])]


def test_a_mixed_group_keeps_its_definite_pairs():
    """Confirmation, the reviewer's case: A and B cite the same DOI with identical values (exact);
    C, from a third source, matches both but has no paper identity (possible). The group is a
    possible duplicate, and the definite exact pair A-B is kept as its own flag."""
    got = kinds([rec(1), rec(2, "controlled_duplicates"), rec(3, "tamu_fcc", doi=None)])
    assert got == [("possible_duplicate", "identical values", [1, 2, 3]),
                   ("exact_duplicate", "identical values", [1, 2])]


def test_a_mixed_group_keeps_its_definite_conflict_without_imposing_it_on_the_others():
    """A and B cite the same DOI and disagree (2.5%: a conflict); C has no paper identity and is
    within the tolerance of both (possible). The conflict is kept for A-B only; C is a possible
    duplicate, not part of a conflict."""
    got = kinds([rec(1, ys=400.0), rec(2, "controlled_duplicates", ys=410.0), rec(3, "tamu_fcc", ys=405.0, doi=None)])
    assert got == [("possible_duplicate", "within tolerance", [1, 2, 3]),
                   ("values_disagree", "differ beyond tolerance", [1, 2])]


def test_an_ambiguous_group_keeps_its_definite_exact_pair():
    """A (MPEA) and B (extract) cite the same DOI with identical values; C (extract, no DOI) also
    matches A: two candidates from one source, so ambiguous. The exact pair A-B is kept."""
    got = kinds([rec(1), rec(2, "controlled_duplicates"), rec(3, "controlled_duplicates", doi=None, gs=10.1)])
    assert got == [("possible_duplicate", "several candidates", [1, 2, 3]),
                   ("exact_duplicate", "identical values", [1, 2])]


def test_unequal_reference_text_is_unknown_not_a_different_paper():
    """Confirmation, new issue: only unequal DOIs prove different papers. Unequal reference text
    (one or both DOIs missing) is unknown, so matching values give a possible duplicate."""
    a = rec(1, reference="Effect of annealing on CoCrFeMnNi")
    b = rec(2, "tamu_fcc", doi=None, reference="Mulukutla et al. 2026")
    assert kinds([a, b])[0][:2] == ("possible_duplicate", "identical values")
    c = rec(3, "tamu_fcc", doi=None, reference="Effect of annealing on CoCrFeMnNi.")
    d = rec(4, "controlled_duplicates", doi=None, reference="Effect of annealing on CoCrFeMnNi")
    assert kinds([c, d])[0][0] == "possible_duplicate"  # punctuation differs: unknown, not different
    assert kinds([rec(5), rec(6, "tamu_fcc", doi="10.5555/other")]) == []  # unequal DOIs: different papers


def test_a_source_without_dois_is_unknown_against_a_record_with_one():
    """Texas A&M has no per-record paper: its records carry the dataset's reference and no DOI.
    Against a record with a DOI and another reference, the paper is unknown, so matching values
    give a possible duplicate, never an exact one. (Replaces the round-2 test that treated the
    unequal reference text as a different paper; confirmation, 2026-10-06.)"""
    tamu = rec(2, "tamu_fcc", doi=None, reference="Mulukutla, M. et al. (2026). Revisiting Hall-Petch")
    got = kinds([rec(1, reference="Effect of annealing on CoCrFeMnNi"), tamu])
    assert got == [("possible_duplicate", "identical values", [1, 2])]


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
def test_flags_come_from_pairwise_comparisons_and_group_classification(seed):
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


def test_checks_imports_no_statistics_and_reads_only_the_rules_and_the_set_names():
    source = Path(fl.__file__).read_text()
    tree = ast.parse(source)
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
        {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not {m for m in imported if m and m.split(".")[0] in ("numpy", "scipy", "statsmodels", "pandas")}
    assert "hypocurate.pipeline.profile" not in imported
    plan_keys = {n.slice.value for n in ast.walk(tree) if isinstance(n, ast.Subscript)
                 and isinstance(n.value, ast.Name) and n.value.id == "plan" and isinstance(n.slice, ast.Constant)}
    # Step 6 review, finding 2: the names of the sensitivity sets, to compute each set's own flags.
    # Re-check finding 2b: not the plan's outcome (Checks compares yield strength, the one supported).
    assert plan_keys == {"rules", "sensitivity_analyses"}
