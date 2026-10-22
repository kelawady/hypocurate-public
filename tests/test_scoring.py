"""Sprint 2 pilot, R7: the scoring script (first version) and its five self-checks (PRD v1.2 Table 4).

The five self-checks: a planted wrong value; correct numbers attached to the wrong specimen; a duplicate prediction
for one observation; a wrong unit or test condition; two legitimate observations that share paper, alloy, state, test
type and temperature and differ only in specimen label or source location, scored as two. And the owner's rules of
2026-10-23: units converted then compared within 2 per cent; a figure-only value matched on the other value, a number
predicted there is a precision error; processing state and location reported, never matched; cited rows marked are
correct handling outside recall and precision; compilation records stated only in a figure or as a range leave the
recovery denominator; precision strict and pending."""
from __future__ import annotations

from decimal import Decimal

from hypocurate.pipeline.extraction.identity import alloy_key
from hypocurate.scoring import score as sc
from hypocurate.scoring.score import Obs, quantity

PAPER = "doi:10.1000/score.1"
ALLOY = alloy_key("CoCrFeNiMo0.2")


def obs(side, ref, gs, ys, *, gs_unit="µm", ys_unit="MPa", label=None, state="annealed 700 °C 1 h",
        location="p. 6, Table 1, row 1", test_type="tension", temp="room temperature", cited=False, gs_stated=None,
        ys_stated=None, link=True):
    return Obs(side, ref, PAPER, ALLOY, test_type, temp, label,
               quantity("grain_size", gs, gs_unit, stated_as=gs_stated),
               quantity("yield_strength", ys, ys_unit, stated_as=ys_stated),
               location=location, state=state, reported_from="[12] Otto et al." if cited else "this paper",
               link_asserted=link, provenance_ok=True, units_as_written={"grain_size": True, "yield_strength": True})


def ann(ref, gs, ys, **kw):
    return obs("annotation", ref, gs, ys, **kw)


def pred(ref, gs, ys, **kw):
    return obs("prediction", ref, gs, ys, **kw)


TRUTH = [ann("a1", "0.8", "1100", location="p. 6, Table 1, row 1"), ann("a2", "1.2", "950", location="row 2"),
         ann("a3", "3.2", "649", location="row 3")]


def m(predictions, references=TRUTH, against="annotation"):
    return sc.score_paper(predictions, references, against).metrics()


def test_all_correct_values_decide_and_location_and_state_are_only_reported():
    preds = [pred("p1", "0.8", "1100", location="page 6, table 0, row 1", state="annealed at 700 °C for 1 h"),
             pred("p2", "1.2", "0.95", ys_unit="GPa", location="page 6, table 0, row 2"),  # unit converted
             pred("p3", "3.25", "650", location="page 6, table 0, row 3")]  # within 2 per cent
    r = m(preds)
    assert (r["matched"], r["recall_or_recovery"], r["precision_strict"], r["precision_pending"]) == (3, "1.000", "1.000", "1.000")
    assert r["location_differs"] == 3 and r["state_text_differs"] == 1 and r["units_as_written_correct"] == 3


# --- the five self-checks (R7) ---------------------------------------------------------------------------------

def test_self_check_1_a_planted_wrong_value():
    r = m([pred("p1", "0.8", "1100"), pred("p2", "1.2", "990"), pred("p3", "3.2", "649")])  # 990 vs 950: +4.2 %
    assert r["matched"] == 2 and r["unmatched_pending_adjudication"] == 1 and r["precision_strict"] == "0.667"
    assert r["recall_or_recovery"] == "0.667" and r["precision_pending"] == "1.000"


def test_self_check_2_correct_numbers_attached_to_the_wrong_specimen():
    r = m([pred("p1", "0.8", "950"), pred("p2", "1.2", "1100")])  # each number right, paired with the other's
    assert r["matched"] == 0 and r["values_from_different_specimens"] == 2 and r["precision_strict"] == "0.000"


def test_self_check_3_a_duplicate_prediction_for_one_observation_is_one_hit_and_one_duplicate():
    r = m([pred("p1", "0.8", "1100"), pred("p1b", "0.8", "1100", location="p. 2, sentence: abstract")])
    assert r["matched"] == 1 and r["duplicates"] == 1 and r["precision_strict"] == "0.500"


def test_self_check_4_a_wrong_unit_or_a_wrong_test_condition():
    wrong_unit = m([pred("p1", "0.8", "1.1", ys_unit="MPa")])  # the paper says GPa; 1.1 MPa is not 1100 MPa
    assert wrong_unit["matched"] == 0 and wrong_unit["unmatched_pending_adjudication"] == 1
    wrong_test = m([pred("p1", "0.8", "1100", test_type="compression")])
    assert wrong_test["matched"] == 0 and wrong_test["unmatched_pending_adjudication"] == 1
    hot = m([pred("p1", "0.8", "1100", temp="800 °c")])
    assert hot["matched"] == 0


def test_self_check_5_two_observations_differing_only_in_label_or_location_score_as_two():
    same_state = [ann("a1", "0.8", "1100", location="Table 1, row 1"), ann("a2", "0.9", "1080", location="Table 1, row 2")]
    r = m([pred("p1", "0.8", "1100", location="t0 r1"), pred("p2", "0.9", "1080", location="t0 r2")], same_state)
    assert r["matched"] == 2 and r["duplicates"] == 0
    labelled = [ann("a1", "0.8", "1100", label="a"), ann("a2", "0.8", "1100", label="a2")]
    r = m([pred("p1", "0.8", "1100", label="a"), pred("p2", "0.8", "1100", label="a2")], labelled)
    assert r["matched"] == 2 and r["duplicates"] == 0
    r = m([pred("p1", "0.8", "1100", label="a"), pred("p2", "0.8", "1100", label="a")], labelled)
    assert r["matched"] == 1 and r["duplicates"] == 1  # the same label twice: one hit, one duplicate


# --- the owner's further rules ----------------------------------------------------------------------------------

def test_a_figure_only_value_is_matched_on_the_other_value_and_a_number_there_is_an_error():
    figure = [ann("a1", "0.8", "", ys_stated="figure only")]
    good = m([pred("p1", "0.8", "figure only")], figure)
    assert good["matched"] == 1 and good["figure_value_asserted"] == 0 and good["precision_strict"] == "1.000"
    bad = m([pred("p1", "0.8", "1100")], figure)
    assert bad["matched"] == 1 and bad["figure_value_asserted"] == 1 and bad["precision_strict"] == "0.000"
    both = m([], [ann("a1", "", "", gs_stated="figure only", ys_stated="figure only")])
    assert both["deferred"] == 1 and both["denominator"] == 0 and both["recall_or_recovery"] is None


def test_a_range_matches_only_a_range():
    ranged = [ann("a1", "1", "0.95-1.1", ys_unit="GPa", ys_stated="range")]
    assert m([pred("p1", "1", "950-1100")], ranged)["matched"] == 1
    assert m([pred("p1", "1", "1100")], ranged)["matched"] == 0
    assert quantity("yield_strength", "∼1.1GPa", None) == sc.Quantity("number", Decimal("1100.0"), Decimal("1100.0"))


def test_a_marked_cited_row_is_outside_recall_and_precision():
    r = m([pred("p1", "0.8", "1100"), pred("c1", "4.4", "360", cited=True)])
    assert r["cited_rows_marked"] == 1 and r["predictions_own"] == 1 and r["precision_strict"] == "1.000"


def test_recovery_leaves_out_compilation_records_the_annotation_states_only_in_a_figure():
    from types import SimpleNamespace as NS
    def rec(key, gs, ys):
        v = lambda x: NS(value=x)  # noqa: E731
        return NS(paper_doi="10.1000/score.1", source_item_key=key, alloy="CoCrFeNiMo0.2",
                  harmonized={"composition": v(None), "grain_size": v(gs), "yield_strength": v(ys),
                              "test_type": v("tension"), "test_temperature": v(25.0)})
    records = [rec("r1", 0.8, 1100.0), rec("r2", 1.2, 950.0), rec("r3", 3.2, 649.0), rec("r0", 0.7, None)]
    annotation = [ann("a1", "0.8", "1100"), ann("a2", "1.2", "", ys_stated="figure only")]  # r3 not annotated
    comp, note = sc.compilation_obs(records, PAPER, annotation)
    assert note == "1 compilation record(s) of this paper lack a grain size or a yield strength: not scored"
    r = sc.score_paper([pred("p1", "0.8", "1100"), pred("p2", "1.2", "figure only")], comp, "compilation").metrics()
    assert (r["reference_rows"], r["deferred"], r["denominator"], r["matched"]) == (3, 2, 1, 1)
    comp_open, note = sc.compilation_obs(records, PAPER, None)
    assert note == ("1 compilation record(s) of this paper lack a grain size or a yield strength: not scored; "
                    "figure-only or range not determined (paper not annotated): every compilation record counts")
    r = sc.score_paper([pred("p1", "0.8", "1100")], comp_open, "compilation").metrics()
    assert (r["denominator"], r["matched"], r["recall_or_recovery"]) == (3, 1, "0.333")


def test_the_tolerance_and_units_are_read_from_their_named_places():
    from hypocurate.pipeline import profile
    assert sc.TOLERANCE == Decimal(str(profile.DUPLICATE_TOLERANCE)) == Decimal("0.02")
    assert sc.UNITS["yield_strength"]["gpa"] == 1000 and sc.UNITS["grain_size"]["nm"] == Decimal("0.001")


def test_s0_predictions_are_read_from_the_snapshot_with_provenance_checked(db):
    """End to end on one stored document: the fixture extractor's S0, read back as predictions, scored against an
    annotation file loaded through the loader."""
    import csv
    import io
    from model_builder import World
    from hypocurate.pipeline.extraction import s0
    from hypocurate.pipeline.extraction.fixture_extractor import FixtureExtractor
    from hypocurate.pipeline.extraction.interface import EvidenceSpec, ParsedDocument
    from hypocurate.scoring import annotation, template
    from test_extraction_interface import stored_parse
    w = World(db)
    with db.connect() as conn:
        doc = ParsedDocument.load(conn, stored_parse(w, "10.1000/score.1"))
    frozen = s0.store_and_freeze(db, doc, FixtureExtractor().extract(doc, EvidenceSpec.load("H1_v1")))
    preds, described = sc.predictions_s0(db, frozen.output_id)
    assert described["snapshot"] == "S0" and described["events_sha256"] == frozen.events_sha256 and len(preds) == 3
    assert all(p.provenance_ok for p in preds if p.gs.kind == "number")
    buf = io.StringIO()
    wr = csv.writer(buf)
    wr.writerow(template.NAMES)
    row = dict.fromkeys(template.NAMES, "") | {
        "paper_doi": "10.1000/score.1", "alloy_as_written": "CoCrFeMnNi", "processing_state": "annealed 800 °C 1 h",
        "observation_location": "p. 2, Table 1, row 1", "grain_size_value": "4.4", "grain_size_unit": "µm",
        "grain_size_stated_as": "number", "yield_strength_value": "360", "yield_strength_unit": "MPa",
        "yield_strength_stated_as": "number", "annotator": "K. El-Awady"}
    wr.writerow([row[n] for n in template.NAMES])
    annotation.load(db, "score.csv", buf.getvalue().encode(), "K. El-Awady")
    refs = sc.annotation_obs(db, "doi:10.1000/score.1")
    r = sc.score_paper(preds, refs, "annotation").metrics()
    # the fixture's rows have no test type or temperature, the annotation none either: one row matches by values
    assert r["matched"] == 1 and r["predictions_own"] == 3 and r["unmatched_pending_adjudication"] == 2
    out = sc.report([("vs annotation", sc.score_paper(preds, refs, "annotation"))], described)
    assert out["snapshot"]["snapshot"] == "S0" and out["rows"][0]["table"] == "vs annotation"


def test_the_extraction_workbook_shows_every_candidates_provenance_as_text(db):
    """R12 (first part): one row per S0 candidate with the source document, each value's provenance and whether it
    resolves, the link's provenance, the method and the snapshot, and the result against the compilation; every text
    cell a string cell, never a formula."""
    import io
    from openpyxl import load_workbook
    from model_builder import World
    from hypocurate.pipeline.extraction import s0
    from hypocurate.pipeline.extraction.fixture_extractor import FixtureExtractor
    from hypocurate.pipeline.extraction.interface import EvidenceSpec, ParsedDocument
    from hypocurate.scoring import extraction_workbook as xw
    from test_extraction_interface import PARSED, stored_parse
    parsed = PARSED | {"tables": [PARSED["tables"][0] | {"rows": PARSED["tables"][0]["rows"] + [["=1+1", "x", "2", "3"]]}]}
    w = World(db)
    with db.connect() as conn:
        doc = ParsedDocument.load(conn, stored_parse(w, "10.1000/wb.1", parsed))
    frozen = s0.store_and_freeze(db, doc, FixtureExtractor().extract(doc, EvidenceSpec.load("H1_v1")))
    data = xw.build(db, frozen.output_id, {"obs:0": "x"})
    ws = load_workbook(io.BytesIO(data))["Extracted (S0)"]
    rows = list(ws.iter_rows(values_only=True))
    assert rows[0] == xw.COLUMNS and len(rows) == 1 + 4
    first = dict(zip(xw.COLUMNS, rows[1]))
    assert first["source_document"] == "10.1000/wb.1" and first["grain_size"] == "4.4"
    assert first["grain_size_provenance"] == "p. 2, table 0, row 1; snippet: 4.4" and first["grain_size_resolves"] == "yes"
    assert first["link_kind"] == "same_table_row" and first["extraction_method"].startswith("fixture_extractor 1")
    assert first["snapshot"].startswith("S0 #") and first["against_compilation"] == "not scored"
    formula = [r for r in ws.iter_rows() if r[5].value == "=1+1"]
    assert formula and formula[0][5].data_type == "s"
