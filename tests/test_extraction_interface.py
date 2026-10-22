"""Sprint 2 pilot, R4 (first part, 2026-10-22): the Extractor interface, the observation identity, the provenance
check and the S0 freeze.

Acceptance (PRD v1.2 Table 4, R4), the parts shown today: a second, trivial implementation (the fixture extractor)
runs behind the same interface; every stored record has provenance for every value and every link or an 'ambiguous'
marker; the raw output is retrievable per document; method and prompt version are on every record. And S0: frozen with
its hash in the same transaction, stable, never changed, and holding only the extraction's own proposed events.
R-identity: defined once; a composition, not a spelling, is the alloy; °C and K agree; a specimen label, else the
location, separates observations under identical conditions; no paper, or neither label nor location, is refused."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest
from sqlalchemy import text

from hypocurate.documents.parse_worker import canonical
from hypocurate.pipeline.extraction import identity as idm
from hypocurate.pipeline.extraction import provenance, s0
from hypocurate.pipeline.extraction.fixture_extractor import METHOD, FixtureExtractor
from hypocurate.pipeline.extraction.interface import (CandidateRecord, EvidenceSpec, ExtractionResult, Extractor, Link,
                                                      Method, ParsedDocument, Provenance, Value)
from model_builder import World

PDF = b"%PDF-1.7\n% fixture\n"
PARSED = {"format": "hypocurate-parse-1", "parser": "docling", "parser_version": "2.141.0", "fallback_used": False,
          "pages": 3, "attempts": [],
          "texts": [{"index": 0, "page": 2, "text": "The CoCrFeMnNi alloy annealed at 800 °C had a yield strength of "
                                                     "360 MPa at a grain size of 4.4 µm."}],
          "tables": [{"index": 0, "page": 2, "caption": "Table 1",
                      "rows": [["Alloy", "State", "Grain size (µm)", "Yield strength (MPa)"],
                               ["CoCrFeMnNi", "annealed 800 °C 1 h", "4.4", "360"],
                               ["CoCrFeMnNi", "annealed 1000 °C 1 h", "21", "265"],
                               ["Al0.3CoCrFeNi", "annealed 900 °C", "n/a", "250"]]}]}


def stored_parse(w, doi="10.1000/fixture.1", parsed=PARSED):
    body = canonical(parsed)
    doc = w.val("INSERT INTO document (doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by) VALUES (:d, :k, 'unpaywall', "
                ":p, :h, 'code') RETURNING id", d=doi, k="doi:" + doi, p=PDF, h=hashlib.sha256(PDF).hexdigest())
    return w.val("INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, parsed, "
                 "parsed_sha256, pages, tables_found) VALUES (:d, 'docling', '2.141.0', false, 'parsed', :b, :h, 3, 1) "
                 "RETURNING id", d=doc, b=body, h=hashlib.sha256(body.encode()).hexdigest())


@pytest.fixture
def w(db):
    return World(db)


@pytest.fixture
def document(w, db):
    with db.connect() as conn:
        return ParsedDocument.load(conn, stored_parse(w))


# --- the interface -------------------------------------------------------------------------------------------------

def test_the_fixture_extractor_runs_behind_the_interface_and_its_records_are_stored_proposed(db, document):
    extractor: Extractor = FixtureExtractor()
    result = extractor.extract(document, EvidenceSpec.load("H1_v1"))
    assert len(result.records) == 3
    frozen = s0.store_and_freeze(db, document, result)
    with db.connect() as conn:
        out = conn.execute(text("SELECT method, raw_output, raw_sha256, status FROM extraction_output WHERE id = :x"),
                           dict(x=frozen.output_id)).one()
        states = conn.execute(text("SELECT object_kind, state, by_rule FROM evidence_state_event "
                                   "WHERE extraction_output_id = :x"), dict(x=frozen.output_id)).all()
        values = conn.execute(text("SELECT v.field, v.provenance, v.ambiguous FROM candidate_value v JOIN "
                                   "candidate_observation o ON o.id = v.observation_id WHERE o.extraction_output_id = :x"),
                              dict(x=frozen.output_id)).all()
    assert out.method == METHOD.to_json() and out.method["prompt_version"] == "none" and out.status == "returned"
    assert out.raw_output == result.raw_output and out.raw_sha256 == hashlib.sha256(result.raw_output.encode()).hexdigest()
    assert {(k, s, r) for k, s, r in states} == {("observation", "proposed", "extraction"), ("link", "proposed", "extraction")}
    assert len(states) == 6 and all(p is not None and not a for _, p, a in values)


def test_the_third_row_without_a_numeric_grain_size_is_still_read_as_written():
    """The fixture keeps what is written ('n/a' is a value as written); it has no say over inclusion."""
    doc = ParsedDocument(1, 1, "a" * 64, "doi:10.1000/x", PARSED)
    records = FixtureExtractor().extract(doc, EvidenceSpec.load("H1_v1")).records
    third = records[2].value("grain_size")
    assert (third.text, third.number, third.provenance.row_index) == ("n/a", None, 3)


def test_every_value_and_link_has_provenance_or_an_explicit_marker(db, document):
    gs = Value("grain_size", "4.4", unit="µm", provenance=Provenance(2, "4.4", 0, 1))
    ys = Value("yield_strength", "360", unit="MPa")  # no provenance and no note
    alloy = Value("alloy", "CoCrFeMnNi", ambiguity_note="two alloys share the row")
    record = CandidateRecord((gs, ys, alloy), (Link("grain_size", "yield_strength"),))
    result = ExtractionResult(Method("model_call", "pilot", "1", "v1", "claude-sonnet-5-5"), '{"raw": 1}', (record,))
    frozen = s0.store_and_freeze(db, document, result)
    with db.connect() as conn:
        rows = dict(conn.execute(text("SELECT v.field, v.ambiguity_note FROM candidate_value v JOIN candidate_observation o "
                                      "ON o.id = v.observation_id WHERE o.extraction_output_id = :x"),
                                 dict(x=frozen.output_id)).all())
        link_note = conn.execute(text("SELECT ambiguity_note FROM extraction_link l JOIN candidate_observation o ON "
                                      "o.id = l.observation_id WHERE o.extraction_output_id = :x"),
                                 dict(x=frozen.output_id)).scalar_one()
    assert rows == {"grain_size": None, "yield_strength": s0.NO_PROVENANCE, "alloy": "two alloys share the row"}
    assert link_note == s0.NO_PROVENANCE


def test_a_link_to_a_value_the_record_lacks_is_refused_whole(db, document):
    record = CandidateRecord((Value("grain_size", "4.4", provenance=Provenance(2, "4.4", 0, 1)),),
                             (Link("grain_size", "yield_strength", "same_table_row", Provenance(2, "4.4", 0, 1)),))
    with pytest.raises(ValueError, match="a link names a value the record does not have"):
        s0.store_and_freeze(db, document, ExtractionResult(METHOD, "{}", (record,)))
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM extraction_output")).scalar() == 0  # nothing half-stored


def test_provenance_and_values_are_checked_at_construction():
    with pytest.raises(ValueError, match="both the table and the row"):
        Provenance(1, "x", table_index=0)
    with pytest.raises(ValueError, match="a table row or a sentence"):
        Provenance(1, "x")
    with pytest.raises(ValueError, match="snippet"):
        Provenance(1, " ", sentence="s")
    with pytest.raises(ValueError, match="unknown field"):
        Value("hardness", "200")
    with pytest.raises(ValueError, match="unknown link kind"):
        Link("grain_size", "yield_strength", "same_figure")


# --- the provenance check --------------------------------------------------------------------------------------------

def test_a_table_provenance_resolves_only_at_the_cited_row_with_the_snippet():
    doc = ParsedDocument(1, 1, "a" * 64, "doi:10.1000/x", PARSED)
    assert provenance.problem(doc, Provenance(2, "4.4 360", 0, 1)) is None
    assert "no row 9" in provenance.problem(doc, Provenance(2, "4.4", 0, 9))
    assert "no table 3" in provenance.problem(doc, Provenance(2, "4.4", 3, 1))
    assert "on page 2, not 1" in provenance.problem(doc, Provenance(1, "4.4", 0, 1))
    assert "not in the row" in provenance.problem(doc, Provenance(2, "4.4 265", 0, 1))  # 265 is in row 2
    assert "not in the document" in provenance.problem(doc, Provenance(7, "4.4", 0, 1))


def test_a_sentence_provenance_resolves_only_on_its_page_with_the_snippet_inside():
    doc = ParsedDocument(1, 1, "a" * 64, "doi:10.1000/x", PARSED)
    sentence = "yield strength of 360 MPa at a grain size of 4.4 µm"
    assert provenance.problem(doc, Provenance(2, "360 MPa", sentence=sentence)) is None
    assert "not on page 3" in provenance.problem(doc, Provenance(3, "360 MPa", sentence=sentence))
    assert "not in the sentence" in provenance.problem(doc, Provenance(2, "400 MPa", sentence=sentence))
    record = CandidateRecord((Value("yield_strength", "360", provenance=Provenance(2, "999", 0, 1)),))
    assert provenance.problems(doc, record) == ["yield_strength: snippet words not in the row: ['999']"]


# --- S0 --------------------------------------------------------------------------------------------------------------

def test_s0_is_frozen_with_its_hash_in_the_same_transaction_and_never_changes(w, db, document):
    result = FixtureExtractor().extract(document, EvidenceSpec.load("H1_v1"))
    frozen = s0.store_and_freeze(db, document, result)
    with db.connect() as conn:
        snap = conn.execute(text("SELECT name, raw_sha256, event_ids, events_sha256 FROM evidence_snapshot WHERE id = :s"),
                            dict(s=frozen.snapshot_id)).one()
        events = conn.execute(text("SELECT id FROM evidence_state_event WHERE extraction_output_id = :x ORDER BY id"),
                              dict(x=frozen.output_id)).scalars().all()
    assert snap.name == "S0" and snap.raw_sha256 == frozen.raw_sha256 and list(snap.event_ids) == events
    assert snap.events_sha256 == hashlib.sha256(",".join(map(str, events)).encode()).hexdigest() == frozen.events_sha256
    for table in ("extraction_output", "evidence_snapshot", "candidate_observation", "candidate_value",
                  "extraction_link", "evidence_state_event"):
        w.rejected(f"DELETE FROM {table}", "append-only")
    w.rejected("UPDATE extraction_output SET raw_output = 'x'", "append-only")
    w.rejected("INSERT INTO candidate_observation (extraction_output_id, item_index, identity, identity_key) VALUES "
               "(:x, 99, '{}', :k)", "before its S0 is taken", x=frozen.output_id, k="b" * 64)


def test_the_same_output_frozen_twice_gives_the_same_hashes_of_content(w, db):
    with db.connect() as conn:
        a = ParsedDocument.load(conn, stored_parse(w, "10.1000/fixture.1"))
        b = ParsedDocument.load(conn, stored_parse(w, "10.1000/fixture.2"))
    ra, rb = (FixtureExtractor().extract(d, EvidenceSpec.load("H1_v1")) for d in (a, b))
    fa, fb = s0.store_and_freeze(db, a, ra), s0.store_and_freeze(db, b, rb)
    assert fa.raw_sha256 == fb.raw_sha256 and fa.observations == fb.observations == 3


def test_nothing_that_uses_the_compilation_imports_s0():
    """Only the extraction package writes S0 (PRD 4: nothing that uses the compilation touches S0). Today no module
    outside `pipeline/extraction` imports it; the re-report and link rules (Saturday) must keep it so."""
    package = Path(__file__).resolve().parents[1] / "hypocurate"
    importers = []
    for path in package.rglob("*.py"):
        if "pipeline/extraction" in path.as_posix():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                     else [f"{node.module}.{a.name}" for a in node.names] if isinstance(node, ast.ImportFrom) and node.module
                     else [])
            if any("extraction.s0" in n or n.endswith("extraction.s0") for n in names):
                importers.append(path.relative_to(package).as_posix())
    assert importers == []


def test_method_and_prompt_version_are_on_every_output():
    assert set(METHOD.to_json()) == {"method", "name", "version", "prompt_version"}
    m = Method("model_call", "pilot_extractor", "1", "v1", "claude-sonnet-5-5")
    assert m.to_json()["model"] == "claude-sonnet-5-5" and m.to_json()["prompt_version"] == "v1"


def test_the_evidence_specifications_are_locked_files_with_hashes():
    h1, h2 = EvidenceSpec.load("H1_v1"), EvidenceSpec.load("H2_v1")
    assert (h1.key, h1.version, h2.key, h2.version) == ("H1", "1", "H2", "1")
    assert "either (a) the as-processed grain size" in h2.content["required_measurements"]["grain_size"].casefold()
    assert "Compression is not excluded" in h2.content["exclusion_rules"]
    raw = (Path(__file__).resolve().parents[1] / "hypocurate/pipeline/extraction/specs/H1_v1.json").read_bytes()
    assert h1.sha256 == hashlib.sha256(raw).hexdigest()


# --- R-identity ------------------------------------------------------------------------------------------------------

def ident(**kw):
    base = dict(paper_doi="10.1016/J.ACTAMAT.2013.06.018", alloy="CrMnFeCoNi", processing_state="annealed 800 °C 1 h",
                test_type="tension", test_temperature="293", specimen_label=None, observation_location="p. 5, table 2, row 1",
                test_temperature_unit="K")
    return idm.identity(**(base | kw))


def test_a_composition_not_a_spelling_is_the_alloy():
    a = ident()
    assert ident(alloy="CoCrFeMnNi").key == a.key
    assert ident(alloy="Co20Cr20Fe20Mn20Ni20").key == a.key
    assert ident(alloy="x", composition="Co20 Cr20 Fe20 Mn20 Ni20").key == a.key
    assert ident(alloy="Al0.3CoCrFeNi").key != a.key
    assert ident(alloy="Cantor alloy").alloy == "name:cantoralloy"


def test_kelvin_is_converted_before_rounding_and_room_temperature_is_the_band():
    """Owner, 2026-10-23: K to °C, then rounded; a stated 'room temperature' with no number keys to the band, so it
    matches a record stated as 20 °C or 25 °C (Sprint 1's room-temperature range)."""
    band = ident(test_temperature="room temperature", test_temperature_unit=None)
    assert band.test_temperature == "room temperature"
    assert ident().test_temperature == "room temperature"  # 293 K = 19.85 °C, rounded 20 °C
    for t, u in (("20", "°C"), ("25 °C", None), ("RT", None), ("298", "K"), ("ambient", None)):
        assert ident(test_temperature=t, test_temperature_unit=u).key == band.key, (t, u)
    assert ident(test_temperature="26", test_temperature_unit="°C").test_temperature == "26 °c"
    assert ident(test_temperature="19", test_temperature_unit="°C").test_temperature == "19 °c"
    assert ident(test_temperature="1073", test_temperature_unit="K").test_temperature == "800 °c"
    from hypocurate.pipeline import profile
    assert profile.ROOM_TEMPERATURE_C == (20.0, 25.0)


def test_the_match_key_leaves_out_the_processing_state_only():
    """Owner, 2026-10-23: the scorer and the re-report rule match without the processing state; its text is reported
    per pair and adjudicated."""
    a = ident(processing_state="annealed 1 h at 800 °C")
    b = ident(processing_state="annealed at 800 °C for 1 h")
    assert a.key != b.key and a.match_key == b.match_key == idm.match_key(a.to_json())
    for change in (dict(alloy="Al0.3CoCrFeNi"), dict(test_type="compression"), dict(specimen_label="A2"),
                   dict(test_temperature="800", test_temperature_unit="°C"), dict(paper_doi="10.1000/other")):
        assert ident(**change).match_key != a.match_key, change
    assert idm.MATCH_FIELDS == ("paper", "alloy", "test_type", "test_temperature", "specimen", "version")


def test_the_test_type_is_tension_or_compression_when_the_text_says_so():
    assert ident(test_type="Tensile").test_type == "tension" == ident(test_type="T").test_type
    assert ident(test_type="compressive").test_type == "compression"


def test_a_label_else_the_location_separates_observations_under_identical_conditions():
    a, b = ident(observation_location="p. 5, table 2, row 1"), ident(observation_location="p. 5, table 2, row 2")
    assert a.key != b.key
    la, lb = ident(specimen_label="A"), ident(specimen_label="A2")
    assert la.key != lb.key and la.specimen == "label:a"
    assert ident(specimen_label="A", observation_location="elsewhere").key == la.key  # the label decides when given


def test_an_observation_without_a_paper_or_without_label_and_location_is_refused():
    with pytest.raises(idm.IdentityError, match="paper"):
        ident(paper_doi="")
    with pytest.raises(idm.IdentityError, match="specimen label or its location"):
        ident(specimen_label=" ", observation_location=None)


def test_processing_state_text_is_normalized_but_not_interpreted():
    assert ident(processing_state="Annealed  800 ℃ 1 h").key == ident().key
    assert ident(processing_state="annealed 800 °C 2 h").key != ident().key
