"""Sprint 2 pilot, R7/R8 (first part, 2026-10-22): the annotation template and its loader.

The template keeps every Appendix B column in order and adds three (owner, 2026-10-22): `observation_location` and
`specimen_label` right after `processing_state`, and `test_temperature_unit` after `test_temperature`; its 'Read me'
gives one example with specimen labels and one where the location stands in. The loader reads the template's columns
exactly, computes each row's identity with the one R-identity function, stores cells as written, skips wholly blank
rows, and refuses the whole file, listing every problem, on wrong columns or a row with no paper, no annotator, or
neither a label nor a location."""
from __future__ import annotations

import csv
import io

import pytest
from openpyxl import load_workbook
from sqlalchemy import text

from hypocurate.pipeline.extraction.identity import identity
from hypocurate.scoring import annotation, template

APPENDIX_B = ("paper_doi", "alloy_as_written", "composition_at_pct", "processing_state", "grain_size_value",
              "grain_size_unit", "grain_size_method", "grain_size_location", "yield_strength_value",
              "yield_strength_unit", "yield_strength_definition", "yield_strength_location", "test_type",
              "test_temperature", "strain_rate", "link_evidence", "link_location", "ambiguity_note", "in_compilation",
              "annotator", "minutes")


def test_every_appendix_b_column_is_kept_in_order_and_three_identity_columns_are_added_where_agreed():
    names = template.NAMES
    assert tuple(n for n in names if n in APPENDIX_B) == APPENDIX_B
    assert set(names) - set(APPENDIX_B) == {"observation_location", "specimen_label", "test_temperature_unit"}
    i = names.index("processing_state")
    assert names[i + 1:i + 3] == ("observation_location", "specimen_label")
    assert names[names.index("test_temperature") + 1] == "test_temperature_unit"


def test_the_workbook_has_the_read_me_with_both_examples_and_a_header_only_annotation_sheet():
    wb = load_workbook(io.BytesIO(template.workbook()))
    assert wb.sheetnames == ["Read me", "Annotation"]
    readme = " ".join(str(r[0]) for r in wb["Read me"].iter_rows(values_only=True) if r[0])
    assert "Example 1" in readme and "specimen_label 'A1'" in readme
    assert "Example 2" in readme and "The location stands in for the label" in readme
    rows = list(wb["Annotation"].iter_rows(values_only=True))
    assert rows == [template.NAMES]


def sheet(rows, header=template.NAMES) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for r in rows:
        w.writerow([r.get(n, "") for n in header])
    return buf.getvalue().encode("utf-8")


ROW = {"paper_doi": "10.1016/j.actamat.2013.06.018", "alloy_as_written": "CrMnFeCoNi",
       "processing_state": "annealed 1 h at 800 °C", "observation_location": "p. 5, Table 2, row 1",
       "grain_size_value": "4.4", "grain_size_unit": "µm", "yield_strength_value": "360", "yield_strength_unit": "MPa",
       "test_type": "tension", "test_temperature": "293", "test_temperature_unit": "K",
       "link_evidence": "same table row", "annotator": "K. El-Awady", "minutes": "25"}


def test_a_good_file_loads_with_the_identity_from_the_one_function(db):
    second = ROW | {"observation_location": "p. 5, Table 2, row 2", "yield_strength_value": "350", "minutes": ""}
    content = sheet([ROW, {}, second])
    fid, n, blank = annotation.load(db, "paper1.csv", content, "Khalid El-Awady")
    assert (n, blank) == (2, 1)
    expected = identity(ROW["paper_doi"], "CrMnFeCoNi", ROW["processing_state"], "tension", "293", None,
                        ROW["observation_location"], test_temperature_unit="K")
    with db.connect() as conn:
        rows = conn.execute(text("SELECT row_number, identity_key, cells, minutes FROM annotation_row WHERE "
                                 "annotation_file_id = :f ORDER BY row_number"), dict(f=fid)).all()
        sha = conn.execute(text("SELECT template_version FROM annotation_file WHERE id = :f"), dict(f=fid)).scalar()
    assert [r.row_number for r in rows] == [2, 4] and rows[0].identity_key == expected.key
    assert rows[0].identity_key != rows[1].identity_key  # two locations: two observations
    assert rows[0].cells["yield_strength_value"] == "360" and rows[0].minutes == 25 and rows[1].minutes is None
    assert sha == template.TEMPLATE_VERSION


def test_a_file_is_refused_whole_and_lists_every_problem():
    bad = [ROW, ROW | {"paper_doi": ""}, ROW | {"annotator": ""}, ROW | {"observation_location": "", "specimen_label": ""},
           ROW | {"minutes": "half an hour"}]
    with pytest.raises(annotation.AnnotationRefused) as e:
        annotation.parse("paper1.csv", sheet(bad))
    assert e.value.problems == ["row 3: no paper_doi", "row 3: an observation names its paper", "row 4: no annotator",
                                "row 5: an observation names its specimen label or its location in the source",
                                "row 6: minutes 'half an hour' is not a number"]


def test_wrong_columns_or_a_wrong_name_are_refused():
    with pytest.raises(annotation.AnnotationRefused, match="columns differ"):
        annotation.parse("a.csv", sheet([ROW], header=tuple(n for n in template.NAMES if n != "specimen_label")))
    reordered = list(template.NAMES)
    reordered[4], reordered[5] = reordered[5], reordered[4]
    with pytest.raises(annotation.AnnotationRefused, match="out of order"):
        annotation.parse("a.csv", sheet([ROW], header=tuple(reordered)))
    with pytest.raises(annotation.AnnotationRefused, match="file name"):
        annotation.parse("../a.csv", sheet([ROW]))


def test_the_xlsx_template_round_trips_through_the_loader():
    from openpyxl import load_workbook as lw
    wb = lw(io.BytesIO(template.workbook()))
    wb["Annotation"].append([ROW.get(n, "") for n in template.NAMES])
    buf = io.BytesIO()
    wb.save(buf)
    rows, blank = annotation.parse("filled.xlsx", buf.getvalue())
    assert len(rows) == 1 and rows[0].cells["specimen_label"] == "" and rows[0].identity["specimen"].startswith("location:")
