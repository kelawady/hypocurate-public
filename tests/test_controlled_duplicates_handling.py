"""Step 6: duplicate, conflict and near-miss handling on the controlled duplicate extract,
checked against its answer file (PRD 5.3, 14.1 "Duplicates"; step 1).

One run, marked as a test (it holds constructed data), chooses the MPEA dataset and the extract,
and goes through the freeze under the reference plan. For each of the 16 extract rows the
answer file states the flag, the handling in the primary analysis, the survivor and the
sensitivity handling; every record is kept in the store.

The reference plan accepts tension tests only (owner, 2026-10-05); since 2026-10-06 the answer
file's rows 15–16 describe that plan in their own columns. For rows 13–14 the answer
file's "included" in the sensitivity analysis is read as decided by the owner (2026-10-05): in
`scope_not_confirmed_included` the scope no longer excludes the record, and the duplicate rule
still counts the measurement once.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from pipeline_fixtures import decisions, frozen_run

REPO = Path(__file__).resolve().parents[1]
TRUTH = list(csv.DictReader((REPO / "tests/fixtures/controlled_duplicates/truth.csv").open(encoding="utf-8")))
FLAG_OF = {"exact_duplicate": "exact_duplicate", "possible_duplicate": "possible_duplicate",
           "conflict": "values_disagree", "not_duplicate": None}


@pytest.fixture(scope="module")
def run(admin, database_url, template_database):
    with frozen_run(admin, database_url, template_database, sources=("mpea", "controlled_duplicates"),
                    marked=True) as (engine, rid):
        yield decisions(engine, rid)


def expected_removed(run):
    """The records the set without the group with the largest share of slope information must leave out,
    derived here independently of the result being checked (second model's review, point 3; owner,
    2026-10-06): from the primary members' conditions (no outcome), with the reference plan's grouping
    (MPEA and the extract by the paper's DOI hash, Texas A&M by dataset) and its same-alloy rule (0.1
    at.%): x = d^-1/2, each alloy with two or more grain sizes, I_g = Σ (x - alloy mean)², the largest I_g.
    No package code is used; a tie would make the check ambiguous, so a clear maximum is required."""
    from collections import defaultdict
    from hypocurate.sources.normalize import same_alloy_key
    members = [run["conditions"][i] for i in run["sets"]["primary"]]
    group = lambda c: "dataset" if c["source"] == "tamu_fcc" else c["paper"]  # noqa: E731
    by_alloy = defaultdict(list)
    for c in members:
        by_alloy[same_alloy_key(c["composition"], 1)].append(c)
    info = defaultdict(float)
    for cs in by_alloy.values():
        xs = [c["values"]["grain_size"] ** -0.5 for c in cs]
        if len(set(xs)) < 2:
            continue
        mean = sum(xs) / len(xs)
        for c, x in zip(cs, xs):
            info[group(c)] += (x - mean) ** 2
    ranked = sorted(info.values(), reverse=True)
    assert ranked[0] > ranked[1] * (1 + 1e-6)
    top = max(info, key=info.get)
    return {c["id"] for c in members if group(c) == top}


def ids(run, t):
    """The extract record of answer row t and its MPEA source record."""
    by_origin = {o: i for i, o in run["origin"].items()}
    return (by_origin[f"extract.csv:row:{int(t['extract_row']) - 1}"],
            by_origin[f"MPEA_dataset.csv:row:{t['mpea_row']}"])


def test_every_extract_row_is_kept_in_the_store(run):
    assert sum(s == "controlled_duplicates" for s in run["source"].values()) == 16
    assert sum(s == "mpea" for s in run["source"].values()) == 1545
    assert all(t["kept_in_store"] == "yes" and t["removed_from_store"] == "no" for t in TRUTH)


@pytest.mark.parametrize("t", TRUTH, ids=lambda t: f"row{t['extract_row']}-{t['case']}")
def test_the_flag_is_the_answer_files(run, t):
    extract_id, mpea_id = ids(run, t)
    mine = [f for f in run["flags"] if extract_id in f["records"]]
    expected = FLAG_OF[t["duplicate_status"]]
    if expected is None:  # near misses: matching alloy and grain size alone is not enough
        assert mine == []
    else:
        assert [(f["kind"], f["records"]) for f in mine] == [(expected, sorted([extract_id, mpea_id]))]
        assert mine[0]["category"] != "several candidates"


@pytest.mark.parametrize("t", TRUTH, ids=lambda t: f"row{t['extract_row']}-{t['case']}")
def test_the_primary_handling_and_the_survivor_are_the_answer_files(run, t):
    extract_id, mpea_id = ids(run, t)
    rules = run["rules"]["primary"]
    primary = t["primary_analysis"]
    expected = {
        "counted once": ("in_scope", "duplicate_counted_once"),
        "neither enters: conflict unresolved": ("conflict_unresolved", "conflict_unresolved"),
        "both enter": ("in_scope", "in_scope"),
        "not eligible under a room-temperature plan": ("in_scope", "out_of_scope"),
        "not eligible: scope not confirmed": ("in_scope", "scope_not_confirmed"),
        "not eligible: excluded by the test-type rule (tension only)": ("in_scope", "out_of_scope"),
        "not eligible: no group (paper reference missing)": ("in_scope", "group_unknown"),  # step 7b
    }[primary]
    assert (rules[mpea_id], rules[extract_id]) == expected
    if t["survivor_in_primary"].startswith("MPEA row"):
        assert t["survivor_in_primary"] == f"MPEA row {t['mpea_row']}"
        assert mpea_id in run["sets"]["primary"]
    for record in (extract_id, mpea_id):
        assert (record in run["sets"]["primary"]) == (rules[record] == "in_scope")


@pytest.mark.parametrize("t", TRUTH, ids=lambda t: f"row{t['extract_row']}-{t['case']}")
def test_the_sensitivity_handling_is_the_answer_files(run, t):
    extract_id, mpea_id = ids(run, t)
    sensitivity = t["sensitivity_analysis"]
    if sensitivity == "both counted separately":
        rules = run["rules"]["possible_duplicates_separate"]
        assert (rules[mpea_id], rules[extract_id]) == ("in_scope", "in_scope")
        assert {mpea_id, extract_id} <= run["sets"]["possible_duplicates_separate"]
    elif sensitivity == "counted once in conflicts_survivor_value":
        rules = run["rules"]["conflicts_survivor_value"]
        assert (rules[mpea_id], rules[extract_id]) == ("in_scope", "duplicate_counted_once")
    elif sensitivity == "included":  # rows 13-14, as the owner decided (module docstring)
        rules = run["rules"]["scope_not_confirmed_included"]
        assert (rules[mpea_id], rules[extract_id]) == ("in_scope", "duplicate_counted_once")
    else:
        assert sensitivity == "none"
        for key, rules in run["rules"].items():  # no set treats this pair differently from primary
            if key not in ("tension_and_compression", "source_only_assignments"):
                expected = [run["rules"]["primary"][mpea_id], run["rules"]["primary"][extract_id]]
                if key == "without_most_influential_paper":
                    # Step 7b: that set removes the primary members of one group, whatever their duplicate
                    # handling, and changes nothing else; the removed records are derived independently.
                    removed = expected_removed(run)
                    expected = ["most_influential_paper" if i in removed else r
                                for i, r in zip((mpea_id, extract_id), expected)]
                assert [rules[mpea_id], rules[extract_id]] == expected, key


def test_rows_15_and_16_enter_together_when_compression_is_permitted(run):
    """The compression copies are distinct measurements, not duplicates: with tension and
    compression together, both records of each pair enter."""
    for t in (t for t in TRUTH if t["case"] == "not_duplicate_other_test_type"):
        extract_id, mpea_id = ids(run, t)
        rules = run["rules"]["tension_and_compression"]
        assert (rules[mpea_id], rules[extract_id]) == ("in_scope", "in_scope")


def test_the_set_without_the_largest_share_removes_the_independently_derived_records(run):
    """The whole set, not only the answer rows: exactly the independently derived group leaves."""
    removed = expected_removed(run)
    assert removed and run["sets"]["without_most_influential_paper"] == run["sets"]["primary"] - removed
