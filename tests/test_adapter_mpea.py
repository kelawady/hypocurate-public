"""Step 4: the MPEA-layout adapter on the frozen MPEA dataset, and on planted rows.

An adapter converts and reports: one record per row, nothing dropped, every value as
reported kept with its unit, anything unconvertible kept and marked with the reason."""
import csv
import dataclasses
import io
import re
from collections import Counter
from pathlib import Path

import pytest

from hypocurate.sources import adapters
from hypocurate.sources.adapters import mpea_layout
from hypocurate.sources.record import HARMONIZED_FIELDS, AdapterError, CommonRecord
from hypocurate.sources.versions import UnsealedVersion
from source_helpers import sealed, sealed_from_disk

REPO = Path(__file__).resolve().parents[1]
MPEA_CSV = REPO / "data/sources/mpea/MPEA_dataset.csv"
GS = "PROPERTY: grain size ($\\mu$m)"


@pytest.fixture(scope="module")
def version():
    return sealed_from_disk("mpea")


@pytest.fixture(scope="module")
def result(version):
    return adapters.read(version)


@pytest.fixture(scope="module")
def rows():
    with open(MPEA_CSV, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))[1:]


def test_one_record_per_row_none_dropped(result, rows):
    assert len(rows) == 1545
    assert len(result.records) == 1545
    assert result.blank_rows == ()
    assert [r.source_item_key for r in result.records] == [f"MPEA_dataset.csv:row:{i}" for i in range(1545)]
    assert all(r.item_index == 0 for r in result.records)


def test_every_value_is_kept_as_reported_with_its_unit(result, rows):
    for record, row in zip(result.records, rows):
        assert list(record.reported) == list(mpea_layout.HEADER)
        assert [r.text for r in record.reported.values()] == row
        assert all(r.column == name for name, r in record.reported.items())
    first = result.records[0].reported
    assert first[GS].unit == "µm"
    assert first["PROPERTY: YS (MPa)"].unit == "MPa"
    assert first["PROPERTY: Test temperature ($^\\circ$C)"].unit == "°C"
    assert first["FORMULA"].unit is None


def test_every_record_has_the_common_fields_with_their_units(result):
    for r in result.records:
        assert set(r.harmonized) == set(HARMONIZED_FIELDS)
        assert all(v.unit == HARMONIZED_FIELDS[k] for k, v in r.harmonized.items())
        assert r.kind == "measured"
        assert r.source_key == "mpea"


def test_numbers_are_converted_unchanged(result, rows):
    for record, row in zip(result.records, rows):
        for field, col in (("grain_size", 5), ("hardness", 8), ("test_temperature", 10),
                           ("yield_strength", 11), ("ultimate_tensile_strength", 12)):
            v = record.harmonized[field]
            if row[col] == "":
                assert (v.status, v.reason) == ("not_reported", "blank in the source")
            else:
                assert (v.status, v.value) == ("converted", float(row[col]))


def test_grain_size_counts(result):
    statuses = Counter(r.harmonized["grain_size"].status for r in result.records)
    assert statuses == {"converted": 237, "not_reported": 1308}


def test_nothing_in_the_frozen_file_is_unconvertible(result):
    assert not [(r.source_item_key, k) for r in result.records for k, v in r.harmonized.items()
                if v.status == "not_convertible"]


def test_test_type_codes(result):
    assert Counter(r.harmonized["test_type"].value or r.harmonized["test_type"].status
                   for r in result.records) == {"compression": 792, "tension": 358, "not_reported": 395}


def test_no_value_is_assigned(result):
    assert not [r for r in result.records for v in r.harmonized.values()
                if v.status == "assigned" or v.citation is not None]


def _reference_norm(f):
    """The reference script's alloy naming (docs/reference/worked_example.py), copied."""
    comp = {}
    for e, n in re.findall(r'([A-Z][a-z]?)([0-9.]*)', f):
        comp[e] = comp.get(e, 0) + (float(n) if n else 1.0)
    s = sum(comp.values())
    return ''.join(f"{e}{round(100 * v / s, 1):g}" for e, v in sorted(comp.items()))


def test_display_labels_follow_the_reference_naming(result, rows):
    for record, row in zip(result.records, rows):
        assert record.alloy == _reference_norm(row[1])
        assert sum(record.harmonized["composition"].value.values()) == pytest.approx(100)


def test_paper_identity_is_the_doi(result, rows):
    for record, row in zip(result.records, rows):
        assert record.paper_doi == row[20]
        assert record.group.unit == "paper"
        # The group key is derived (finding 1); written out independently here.
        assert record.group.key == "doi:" + row[20].strip().lower()
        assert record.paper_reference == (row[22] or None)
    # Normalization changes the form of 8 DOI strings but merges and splits no group.
    assert len({r.group.key for r in result.records}) == 265
    assert sum(r.group.key != f"doi:{r.paper_doi}" for r in {r.paper_doi: r for r in result.records}.values()) == 8
    # In the frozen file the DOI and the Reference ID are one-to-one.
    assert len({(row[0], row[20]) for row in rows}) == len({row[20] for row in rows}) == len({row[0] for row in rows})


def test_the_record_format_has_no_decision_fields():
    names = {f.name for f in dataclasses.fields(CommonRecord)}
    assert names == {"source_key", "version_fingerprint", "source_item_key", "item_index", "kind", "alloy",
                     "paper_reference", "paper_doi", "group", "harmonized", "reported"}


# --- Planted rows --------------------------------------------------------------------

def planted(lines: list[str]) -> bytes:
    header = MPEA_CSV.read_bytes().split(b"\n", 1)[0].decode("utf-8")
    return ("\n".join([header] + lines) + "\n").encode("utf-8")


GOOD = "1,Co1 Cr1 Ni1,FCC,CAST,FCC,50.0,,8.0,,T,25.0,300.0,,,,,,,,,10.1/x,2020,A paper"


def _row(**changes):
    fields = next(csv.reader([GOOD]))
    for col, value in changes.items():
        fields[int(col[1:])] = value
    buf = io.StringIO()
    csv.writer(buf, lineterminator="").writerow(fields)
    return buf.getvalue()


def test_planted_values_are_kept_and_marked():
    lines = [
        GOOD,
        _row(c5="abc"),              # 1: grain size not a number
        _row(c1="Xx1 Co1"),          # 2: unknown element
        _row(c1=""),                 # 3: no formula
        _row(c5="-5"),               # 4: negative grain size: converted as reported, not judged here
        _row(c10="25 C"),            # 5: temperature with text
        _row(c9="X"),                # 6: unknown test type
        _row(c20=""),                # 7: no DOI
        "",                          # 8: blank line
        _row(c2="FCC+BCC"),          # 9: an ordinary row (a wrong field count now refuses the file: finding 3)
        _row(c11="nan"),             # 10: not finite
        _row(c1="Co1 Cr0 Ni1"),      # 11: zero amount
    ]
    result = mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted(lines)}))
    by_row = {int(r.source_item_key.rsplit(":", 1)[1]): r for r in result.records}
    assert result.blank_rows == (8,)
    assert sorted(by_row) == [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11]

    def h(i, field):
        return by_row[i].harmonized[field]

    assert h(0, "grain_size").value == 50.0 and by_row[0].alloy == "Co33.3Cr33.3Ni33.3"
    assert (h(1, "grain_size").status, h(1, "grain_size").reason) == ("not_convertible", "not a number: 'abc'")
    assert by_row[1].reported[GS].text == "abc"
    assert h(2, "composition").status == "not_convertible" and "unknown element symbol 'Xx'" in h(2, "composition").reason
    assert by_row[2].alloy is None and by_row[2].reported["FORMULA"].text == "Xx1 Co1"
    assert h(3, "composition").status == "not_reported" and by_row[3].alloy is None
    assert (h(4, "grain_size").status, h(4, "grain_size").value) == ("converted", -5.0)
    assert h(5, "test_temperature").status == "not_convertible"
    assert by_row[5].reported["PROPERTY: Test temperature ($^\\circ$C)"].text == "25 C"
    assert h(6, "test_type").status == "not_convertible" and "'X'" in h(6, "test_type").reason
    assert by_row[7].group.key is None and by_row[7].group.reason == "no DOI in the source: paper unknown"
    assert by_row[7].paper_doi is None
    assert h(9, "microstructure").value == "FCC+BCC"
    assert h(10, "yield_strength").status == "not_convertible"
    assert h(11, "composition").status == "not_convertible" and "not positive" in h(11, "composition").reason


def test_a_file_in_another_layout_is_refused():
    with pytest.raises(AdapterError, match="line 1: the header"):
        mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": b"a,b\n1,2\n"}))
    with pytest.raises(AdapterError, match="UTF-8"):
        mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": b"\xff\xfe\x00"}))


def test_another_grouping_unit_is_refused():
    with pytest.raises(AdapterError, match="groups by paper"):
        mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted([GOOD])}, grouping_unit="dataset"))


def test_altered_bytes_are_refused_before_parsing(version):
    tampered = dataclasses.replace(version, files={"MPEA_dataset.csv": planted([GOOD])})
    with pytest.raises(UnsealedVersion, match="files digest"):
        adapters.read(tampered)
    with pytest.raises(UnsealedVersion, match="not sealed"):
        adapters.read(dataclasses.replace(version, sealed_at=None))


def test_text_is_kept_exactly_as_reported(result, rows):
    """One MPEA DOI has a leading space; the adapter keeps it (no silent correction)."""
    spaced = [r for r in result.records if r.paper_doi and r.paper_doi != r.paper_doi.strip()]
    assert [r.paper_doi for r in spaced] == [" 10.1038/ncomms10602"]
    assert spaced[0].reported["REFERENCE: doi"].text == " 10.1038/ncomms10602"
    assert spaced[0].group.key == "doi:10.1038/ncomms10602"


@pytest.mark.parametrize("reported", [
    "10.1016/J.ACTAMAT.2019.04.017", " 10.1016/j.actamat.2019.04.017 ", "doi:10.1016/j.actamat.2019.04.017",
    "DOI: 10.1016/j.actamat.2019.04.017", "https://doi.org/10.1016/j.actamat.2019.04.017",
    "http://dx.doi.org/10.1016/J.ActaMat.2019.04.017", "HTTPS://DOI.ORG/10.1016/j.actamat.2019.04.017",
])
def test_formatting_differences_do_not_split_a_paper(reported):
    """Finding 1: one DOI written differently is one group; the DOI as reported is kept."""
    result = mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted([_row(c20=reported)])}))
    record, = result.records
    assert record.group.key == "doi:10.1016/j.actamat.2019.04.017"
    assert record.paper_doi == reported
    assert record.reported["REFERENCE: doi"].text == reported


def test_grouping_folds_ascii_case_only():
    from hypocurate.sources.normalize import doi_group_key
    assert doi_group_key("10.1/ÄB") == "doi:10.1/Äb"  # non-ASCII letters are left as they are
    assert doi_group_key("10.1/ab") != doi_group_key("10.1/ac")
    assert doi_group_key("   ") is None and doi_group_key("doi:") is None


def test_compositions_differing_below_the_rounding_step_are_not_identical():
    """Finding 2: the display label rounds to 0.1 at.%; the adapter's compositions do not."""
    result = mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted(
        [_row(c1="Fe50.01 Ni49.99"), _row(c1="Fe50.04 Ni49.96")])}))
    a, b = result.records
    assert a.alloy == b.alloy == "Fe50Ni50"  # the same display label …
    ca, cb = a.harmonized["composition"].value, b.harmonized["composition"].value
    assert ca != cb  # … but not the same composition
    assert ca["Fe"] == pytest.approx(50.01) and cb["Fe"] == pytest.approx(50.04)


# --- Strict parsing (finding 3): a malformed file is refused, never partly read --------

def refused(lines, match):
    with pytest.raises(AdapterError, match=match) as error:
        mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted(lines)}))
    assert str(error.value).startswith("MPEA_dataset.csv: line")
    assert str(error.value).endswith("the file is refused")
    return str(error.value)


def test_an_unterminated_quote_at_the_end_refuses_the_file():
    # header is line 1; GOOD is line 2; the broken record starts on line 3
    refused([GOOD, '2,"Co1 Cr1 Ni1,FCC'], r"line 3: the record starting on this line cannot be parsed")


def test_an_unterminated_quote_that_swallows_later_rows_refuses_the_file():
    message = refused([GOOD, GOOD.replace(",A paper", ',"unterminated title'), GOOD, GOOD],
                      r"line 3: the record starting on this line cannot be parsed")
    assert "detected at line 5" in message


def test_a_malformed_quote_refuses_the_file():
    refused([GOOD, GOOD.replace("A paper", '"A" paper')], r"^MPEA_dataset.csv: line 3: .*',' expected after")


@pytest.mark.parametrize("change,found", [(GOOD + ",extra", 24), (GOOD.rsplit(",", 2)[0], 21)])
def test_a_wrong_field_count_refuses_the_file_and_names_the_line(change, found):
    refused([GOOD, GOOD, change, GOOD], rf"^MPEA_dataset.csv: line 4: expected 23 fields, found {found}; ")


def test_a_legitimate_quoted_multi_line_field_is_read():
    multi = GOOD.replace(",A paper", ',"A paper\nwith a second line"')
    result = mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted([GOOD, multi, GOOD])}))
    assert [r.source_item_key for r in result.records] == [f"MPEA_dataset.csv:row:{i}" for i in range(3)]
    assert result.records[1].reported["REFERENCE: title"].text == "A paper\nwith a second line"
    assert result.records[1].paper_reference == "A paper\nwith a second line"


def test_a_wrong_field_count_after_a_multi_line_field_names_both_lines():
    multi = GOOD.replace(",A paper", ',"A paper\nwith a second line"')
    refused([multi, multi.rsplit(",", 2)[0] + ',"x\ny"'], r"lines 4-5: expected 23 fields, found 22")
