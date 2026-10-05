"""Step 4: the controlled duplicate extract, read by the MPEA-layout adapter.

Each extract row is an MPEA row copied unchanged or with listed columns changed (step 1).
The adapter must give the same harmonized values for both, except where a listed column
changed. The answer file is read here, on the test side only; the adapter never sees it.
Duplicate handling itself is step 6."""
import csv
from pathlib import Path

import pytest

from hypocurate.sources import adapters
from source_helpers import sealed_from_disk

REPO = Path(__file__).resolve().parents[1]
TRUTH = REPO / "tests/fixtures/controlled_duplicates/truth.csv"

# Which harmonized fields (and record attributes) each changed column feeds.
FEEDS = {
    "FORMULA": {"composition"},
    "PROPERTY: YS (MPa)": {"yield_strength"},
    "PROPERTY: Test temperature ($^\\circ$C)": {"test_temperature"},
    "PROPERTY: Type of test": {"test_type"},
    "IDENTIFIER: Reference ID": set(),
    "REFERENCE: doi": {"paper_doi", "group"},
    "REFERENCE: year": set(),
    "REFERENCE: title": {"paper_reference"},
}


@pytest.fixture(scope="module")
def extract():
    return adapters.read(sealed_from_disk("controlled_duplicates")).records


@pytest.fixture(scope="module")
def mpea():
    return adapters.read(sealed_from_disk("mpea")).records


@pytest.fixture(scope="module")
def truth():
    with open(TRUTH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_sixteen_records_with_origin_keys(extract):
    assert [r.source_item_key for r in extract] == [f"extract.csv:row:{i}" for i in range(16)]
    assert all(r.source_key == "controlled_duplicates" and r.kind == "measured" for r in extract)


def test_each_record_equals_its_mpea_row_except_the_changed_columns(extract, mpea, truth):
    assert len(truth) == 16
    for t, record in zip(truth, extract):
        source = mpea[int(t["mpea_row"])]
        changed = [c for c in t["changed_columns"].split("; ") if c]
        changed_fields = set().union(*(FEEDS[c] for c in changed)) if changed else set()
        for name, value in record.harmonized.items():
            if name in changed_fields:
                continue
            assert value == source.harmonized[name], (t["extract_row"], name)
        for attr in ("paper_doi", "paper_reference", "group"):
            if attr not in changed_fields:
                assert getattr(record, attr) == getattr(source, attr), (t["extract_row"], attr)
        if "FORMULA" not in changed:
            assert record.alloy == source.alloy
        for column, rep in record.reported.items():
            if column not in changed:
                assert rep == source.reported[column], (t["extract_row"], column)
            else:
                assert rep.text != source.reported[column].text


def test_a_renamed_formula_gives_the_same_composition(extract, mpea, truth):
    renamed = [(t, r) for t, r in zip(truth, extract) if t["changed_columns"] == "FORMULA"]
    assert len(renamed) == 2
    for t, record in renamed:
        source = mpea[int(t["mpea_row"])]
        assert record.reported["FORMULA"].text != source.reported["FORMULA"].text
        a, b = record.harmonized["composition"].value, source.harmonized["composition"].value
        assert a.keys() == b.keys() and all(a[e] == pytest.approx(b[e], abs=1e-9) for e in a)


def test_paper_unknown_is_marked_never_invented(extract, truth):
    blank = [r for t, r in zip(truth, extract) if "REFERENCE: doi" in t["changed_columns"]
             and r.reported["REFERENCE: doi"].text == ""]
    assert len(blank) == 2
    for r in blank:
        assert r.paper_doi is None and r.group.key is None
        assert r.group.reason == "no DOI in the source: paper unknown"


def test_a_constructed_doi_is_its_own_paper(extract):
    constructed = [r for r in extract if (r.paper_doi or "").startswith("10.5555/hypocurate-test-")]
    assert [r.group.key for r in constructed] == ["doi:10.5555/hypocurate-test-0001",
                                                  "doi:10.5555/hypocurate-test-0002"]
    # Their Reference ID is blank; the DOI alone identifies the paper.
    assert all(r.reported["IDENTIFIER: Reference ID"].text == "" for r in constructed)
