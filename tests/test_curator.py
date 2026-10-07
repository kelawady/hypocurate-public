"""Step 8a: the Curator and the curation workflow at registration (owner, 2026-10-06, Q2 and Q3).

Through the real path: the frozen sources registered with their documentation; `curate` binds one
registration invocation, reads the Curator's complete input through the access layer, sends the
request through DSPy and litellm to the local stub provider, and stores every proposal as code
decided it; a person accepts or rejects; `seal_curation` seals the accepted values into a new
version; the adapters apply them where the table gives no value.

What these tests do not cover: what a real model proposes (the one live curation call, run only
with the owner's go), and whether a sentence supports a value (that is the person's decision).
"""
from __future__ import annotations

import json
from decimal import Decimal

import pytest

import stub_provider as sp
from hypocurate.access.vocabulary import CURATION_TARGETS
from hypocurate.pipeline.agents import quotes
from hypocurate.pipeline.agents.settings import CURATOR_INSTRUCTION
from hypocurate.sources import adapters, curation
from hypocurate.sources.curation import CurationRefused
from hypocurate.sources.versions import (CURATION_PATH, files_digest, latest_sealed_version_id, load_sealed_version,
                                         register, version_identity)
from model_builder import World

TENSION_QUOTE = ("Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation "
                 "tests provided the HV.")
FCC_QUOTE = "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system."
PLANTED = "ZQPLANT-31337"


def answer(**entries) -> str:
    body = {f: "not stated" for f in CURATION_TARGETS}
    body.update(entries)
    return sp.fields(proposals=json.dumps(body))


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


def register_base(db):
    """The Texas A&M version a curation starts from: its data and documentation without the frozen
    curation (step 8a: registering the definition now gives the curated version)."""
    import dataclasses
    from hypocurate.db.retry import run_transaction
    from hypocurate.sources.versions import SOURCES, _register_in, read_definition_files
    d = dataclasses.replace(SOURCES["tamu_fcc"], curation_file=None)
    files, obtained = read_definition_files(d)
    return run_transaction(db, lambda conn: _register_in(conn, d, files, obtained))


def run_curate(db, key, stub, **kw):
    return curation.curate(db, key, client_options=sp.client_options(stub), **kw)


def version_of(db, key):
    with db.connect() as conn:
        return load_sealed_version(conn, latest_sealed_version_id(conn, key))


# --- refusals before any model call ------------------------------------------------------------------

def test_a_compilation_source_is_never_curated(db, stub):
    """Owner, Q3: a source grouped by paper is refused before any model call."""
    register(db, "mpea")
    with pytest.raises(CurationRefused) as refused:
        run_curate(db, "mpea", stub)
    assert refused.value.code == "compilation_source"
    with db.connect() as conn:
        assert conn.exec_driver_sql("SELECT count(*) FROM agent_invocation").scalar() == 0
    assert stub.requests == []


def test_a_version_without_documentation_is_not_curated(db, stub):
    w = World(db)  # the world's tamu_fcc version holds one data file and no documentation
    assert w
    with pytest.raises(CurationRefused) as refused:
        run_curate(db, "tamu_fcc", stub)
    assert refused.value.code == "no_documentation" and stub.requests == []


# --- the request and the proposals ------------------------------------------------------------------------

def test_the_curators_complete_request_is_the_instruction_the_documentation_and_the_targets(db, stub):
    register_base(db)
    version = version_of(db, "tamu_fcc")
    stub.queue(sp.reply(answer()))
    run_curate(db, "tamu_fcc", stub)
    [body] = stub.bodies()
    assert body["model"] == "claude-sonnet-5-5" and body["max_tokens"] == 8000
    assert body["output_config"] == {"effort": "medium"} and "tools" not in body
    system, user = json.dumps(body["system"]), body["messages"][0]["content"][0]["text"]
    assert len(body["messages"]) == 1
    assert json.dumps(CURATOR_INSTRUCTION)[1:-1] in system
    for path, content in version.documentation.items():
        assert f"=== {path} ===\n{content.decode()}" in user
    assert json.dumps({f: dict(s) for f, s in CURATION_TARGETS.items()}, sort_keys=True, ensure_ascii=False) in user
    assert "[[ ## note ## ]]\nnone" in user
    # No data row reaches the Curator: the spreadsheet's yield strengths and alloy names are absent.
    records = adapters.read(version).records
    documentation = "".join(c.decode() for c in version.documentation.values())
    checked = 0
    for r in records:
        for column in ("YS (MPa)", "Alloy Name", "Grain Size(µm)"):
            cell = r.reported.get(column)
            if cell is not None and len(cell.text) >= 4 and cell.text not in documentation:  # the paper names some
                assert cell.text not in user, (column, cell.text)
                checked += 1
    assert checked > 100


def test_no_planted_value_and_no_claim_reaches_the_curator(db, stub):
    """A constructed source version grouped by dataset: a planted outcome value in its data file, a
    run whose claim states a direction. Neither is in the request's bytes."""
    w = World(db)
    w.running()  # claim: "Yield strength rises as grain size falls"
    v = w.new_version("tamu_fcc", "planted")
    w.add_file(v, "table.csv", f"alloy,grain_size,yield_strength\nZQX1,4.0,{PLANTED}\n".encode())
    w.add_file(v, "documentation/notes.md", b"Every specimen was tested in tension at room temperature.\n",
               role="documentation")
    w.seal(v)
    stub.queue(sp.reply(answer()))
    run_curate(db, "tamu_fcc", stub)
    raw = stub.requests[0]["raw"].decode()
    assert "Every specimen was tested in tension" in raw
    for absent in (PLANTED, "ZQX1", "table.csv", "rises as grain size falls", "yield_strength\\n"):
        assert absent not in raw, absent


def test_each_proposal_is_stored_as_code_decided_it(db, stub):
    register_base(db)
    stub.queue(sp.reply(answer(
        test_type={"value": "tension", "quote": TENSION_QUOTE},
        phase_class={"value": "FCC", "quote": FCC_QUOTE},
        microstructure={"value": "FCC", "quote": "This sentence is not anywhere in the documentation, FCC."},
        test_temperature={"value": "warm", "quote": FCC_QUOTE},
        test_temperature_band={"value": "room temperature", "quote": FCC_QUOTE},
        made_up_field={"value": 1, "quote": "x"})))
    out = run_curate(db, "tamu_fcc", stub)
    assert out["status"] == "done" and out["ignored_keys"] == ["made_up_field"]
    got = {p["field"]: (p["status"], p["refusal_code"], p["document"], p["line"], p["term"]) for p in out["proposals"]}
    assert got == {
        "test_type": ("proposed", None, "documentation/main.tex", 177, "tensile"),
        "phase_class": ("proposed", None, "documentation/main.tex", 173, "FCC"),
        "microstructure": ("refused", "quote_not_found", None, None, None),
        "test_temperature": ("refused", "value_not_allowed", None, None, None),
        "test_temperature_band": ("refused", "term_missing", None, None, None),  # the quote names no temperature
    }
    assert {p["field"] for p in curation.proposals(db, "tamu_fcc")} == set(CURATION_TARGETS)


@pytest.mark.parametrize("entry, code", [
    ({"value": "tension", "quote": "tensile"}, "quote_too_short"),
    ({"value": "tension", "quote": "x" * 1600}, "quote_too_long"),
    ({"value": "shear", "quote": TENSION_QUOTE}, "value_not_allowed"),
    ({"value": "tension"}, "malformed_entry"),
    ("tension", "malformed_entry"),
    ({"value": "compression", "quote": TENSION_QUOTE}, "term_missing"),
])
def test_an_entry_that_fails_a_check_is_refused_with_its_code(db, stub, entry, code):
    register_base(db)
    stub.queue(sp.reply(answer(test_type=entry)))
    out = run_curate(db, "tamu_fcc", stub)
    [p] = [p for p in out["proposals"] if p["field"] == "test_type"]
    assert (p["status"], p["refusal_code"]) == ("refused", code)


def test_a_malformed_answer_is_corrected_once_and_then_nothing_is_stored(db, stub):
    register_base(db)
    stub.queue(sp.reply(sp.fields(proposals=f"I think tension {PLANTED}")),
               sp.reply(sp.fields(proposals="still not JSON")))
    out = run_curate(db, "tamu_fcc", stub)
    assert (out["status"], out["code"], out["attempts"]) == ("failed", "malformed", ["malformed", "malformed"])
    assert out["proposals"] == [] and curation.proposals(db, "tamu_fcc") == []
    retry = stub.requests[1]["raw"].decode()
    assert "(malformed:" in retry and PLANTED not in retry


def test_the_ceiling_refuses_the_call_before_it_is_sent(db, stub):
    register_base(db)
    out = run_curate(db, "tamu_fcc", stub, ceiling=Decimal("0.01"))
    assert (out["status"], out["code"]) == ("failed", "ceiling_reached") and stub.requests == []


# --- decisions, sealing and applying -------------------------------------------------------------------------

def proposed(db, stub, **entries):
    stub.queue(sp.reply(answer(**entries)))
    out = run_curate(db, "tamu_fcc", stub)
    return {p["field"]: p["id"] for p in out["proposals"]}


def test_a_person_decides_once_and_only_on_a_proposal_that_passed(db, stub):
    register_base(db)
    ids = proposed(db, stub, test_type={"value": "tension", "quote": TENSION_QUOTE},
                   phase_class={"value": "FCC", "quote": "not in the documentation at all, FCC here"})
    assert curation.decide(db, ids["test_type"], "accepted", "Khalid El-Awady")["decision"] == "accepted"
    for proposal, code in ((ids["test_type"], "already_decided"), (ids["phase_class"], "not_decidable"),
                           (10 ** 9, "unknown_proposal")):
        with pytest.raises(CurationRefused) as refused:
            curation.decide(db, proposal, "rejected", "Khalid El-Awady")
        assert refused.value.code == code


def tamu_with_notes(db, note: bytes):
    """A Texas A&M version holding the real spreadsheet and a test note as its documentation."""
    register_base(db)
    base = version_of(db, "tamu_fcc")
    w = World.__new__(World)
    w.e = db
    v = w.val("INSERT INTO source_version (source_id, label, obtained_on) SELECT source_id, 'notes', obtained_on "
              "FROM source_version WHERE id = :b RETURNING id", b=base.id)
    for path, content in base.data_files.items():
        w.add_file(v, path, content)
    w.add_file(v, "documentation/notes.md", note, role="documentation")
    w.seal(v, w.fingerprint(v) if hasattr(w, "fingerprint") else None)
    return v


def test_sealing_applies_accepted_values_only_where_the_table_gives_none(db, stub):
    note = ("All tensile tests in this dataset were carried out at 25 \u00b0C in laboratory air on single-phase "
            "FCC specimens.\n").encode()
    base = tamu_with_notes(db, note)
    quote = note.decode().strip()
    ids = proposed(db, stub, test_temperature={"value": 25, "quote": quote},
                   test_type={"value": "tension", "quote": quote},
                   phase_class={"value": "FCC", "quote": quote},
                   microstructure={"value": "FCC", "quote": quote},
                   test_temperature_band={"value": "room temperature", "quote": quote})
    assert {k for k, v in ids.items()} == set(CURATION_TARGETS)
    curation.decide(db, ids["test_temperature"], "accepted", "Khalid El-Awady", "states 25 °C")
    curation.decide(db, ids["test_type"], "accepted", "Khalid El-Awady")
    curation.decide(db, ids["phase_class"], "rejected", "Khalid El-Awady", "the phase check is not a result")
    curation.decide(db, ids["microstructure"], "accepted", "Khalid El-Awady")  # the decision's field: never replaced
    # Rejected (phase class), refused (the band: no listed term in the quote) and not stated: never sealed.
    sealed = curation.seal_curation(db, "tamu_fcc")
    assert sealed.created and sealed.label.endswith("+ curation")
    curated = version_of(db, "tamu_fcc")
    assert curated.id == sealed.version_id and set(curated.files) == {*load_sealed_version_files(db, base), CURATION_PATH}
    doc = json.loads(curated.files[CURATION_PATH])
    assert set(doc["values"]) == {"test_temperature", "test_type", "microstructure"} and doc["source"] == "tamu_fcc"
    assert doc["values"]["test_temperature"]["value"] == 25 and doc["values"]["test_temperature"]["line"] == 1
    records = adapters.read(curated).records
    t = records[0].harmonized["test_temperature"]
    assert (t.value, t.status) == (25, "assigned_from_source") and "accepted by Khalid El-Awady" in t.citation.location
    assert t.citation.quote == quote
    # Where the table gives none, the accepted value applies (test type: adapter version 3 assigns none).
    assert records[0].harmonized["test_type"].citation.document == "tamu_fcc: documentation/notes.md (sealed with the source)"
    # Never over a value the record already has: the band and the microstructure are assigned by decision,
    # so the accepted microstructure leaves them as they are.
    assert records[0].harmonized["test_temperature_band"].status == "assigned_by_decision"
    assert all(r.harmonized["microstructure"].status == "assigned_by_decision" for r in records)
    assert all(r.harmonized["test_temperature"].value == 25 for r in records)


def load_sealed_version_files(db, version_id):
    with db.connect() as conn:
        return set(load_sealed_version(conn, version_id).files)


def test_a_curated_version_is_reproducible_from_its_files_and_cannot_be_curated_again(db, stub):
    register_base(db)
    ids = proposed(db, stub, test_type={"value": "tension", "quote": TENSION_QUOTE})
    curation.decide(db, ids["test_type"], "accepted", "K")
    sealed = curation.seal_curation(db, "tamu_fcc")
    curated = version_of(db, "tamu_fcc")
    assert curation.curation_file(db, "tamu_fcc") == curated.files[CURATION_PATH]
    assert version_identity(files_digest(curated.files), "uploaded_table", "measured", "dataset") == sealed.fingerprint
    for call in (lambda: run_curate(db, "tamu_fcc", stub), lambda: curation.seal_curation(db, "tamu_fcc")):
        with pytest.raises(CurationRefused) as refused:
            call()
        assert refused.value.code == "already_curated"


def test_two_accepted_proposals_for_one_field_are_not_sealed(db, stub):
    register_base(db)
    first = proposed(db, stub, test_type={"value": "tension", "quote": TENSION_QUOTE})
    second = proposed(db, stub, test_type={"value": "tension", "quote": TENSION_QUOTE})
    curation.decide(db, first["test_type"], "accepted", "K")
    curation.decide(db, second["test_type"], "accepted", "K")
    with pytest.raises(CurationRefused) as refused:
        curation.seal_curation(db, "tamu_fcc")
    assert refused.value.code == "conflicting_acceptances"


def test_a_curation_file_that_cannot_be_read_refuses_the_version(db):
    from hypocurate.sources.record import AdapterError
    register_base(db)
    base = version_of(db, "tamu_fcc")
    bad = {**dict(base.files), CURATION_PATH: b'{"format": 1, "source": "mpea", "values": {}}\n'}
    from hypocurate.sources.versions import SealedVersion
    digest = files_digest(bad)
    v = SealedVersion(base.id, base.source_key, base.label, base.source_type, base.data_kind, base.grouping_unit,
                      base.sealed_at, digest, version_identity(digest, base.source_type, base.data_kind,
                                                               base.grouping_unit), bad)
    with pytest.raises(AdapterError, match="curation.json"):
        adapters.read(v)


# --- the command line ------------------------------------------------------------------------------------------

def test_the_command_line_never_prints_the_guarded_childs_error_text(monkeypatch, capsys, migrated_database):
    from hypocurate import cli
    from hypocurate.access import guarded
    monkeypatch.setenv("DATABASE_URL", migrated_database)

    def failing(*a, **kw):
        raise guarded.GuardedRunError(f"RuntimeError: provider said {PLANTED}")

    monkeypatch.setattr(guarded, "run_guarded", failing)
    assert cli.main(["sources", "curate", "tamu_fcc"]) == 1
    captured = capsys.readouterr()
    assert PLANTED not in captured.out + captured.err and "did not finish" in captured.err


def test_the_quote_checks_collapse_whitespace_only():
    docs = {"documentation/a.tex": "line one\nThe  dataset\n  contains 94 FCC alloy conditions.\n"}
    assert quotes.locate("The dataset contains 94 FCC alloy conditions.", docs) == quotes.Located("documentation/a.tex", 2)
    assert quotes.locate("the dataset contains 94 FCC alloy conditions.", docs) is None  # no case folding
    assert quotes.term_for("microstructure", "FCC+BCC", "FCC and BCC phases") == "FCC"
    assert quotes.term_for("microstructure", "FCC+BCC", "FCC only") is None
    assert quotes.term_for("test_temperature", 25, "tested at 25 °C") == "25"
    assert quotes.term_for("test_temperature", 25, "tested at 250 °C") is None


# --- review finding 1 (ChatGPT, 2026-10-07): a curation file is checked against the version it is attached to ---
# Before it is sealed into a version (registration, seal-curation) and again before it is applied (adapters.read):
# the base version's fingerprint, every quote found again in that version's documentation on the stated line,
# every value and term passing the current checks, and the acceptance fields present and valid. The one trusted
# import is the exact approved export replayed on the same base (the frozen data/sources/tamu_fcc/curation.json).

def frozen_curation() -> dict:
    from hypocurate.sources.versions import DATA_DIR
    return json.loads((DATA_DIR / "sources" / "tamu_fcc" / "curation.json").read_text(encoding="utf-8"))


def encode(doc: dict) -> bytes:
    return (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sealed_as(base, files):
    from hypocurate.sources.versions import SealedVersion
    digest = files_digest(files)
    return SealedVersion(base.id, base.source_key, base.label, base.source_type, base.data_kind, base.grouping_unit,
                         base.sealed_at, digest, version_identity(digest, base.source_type, base.data_kind,
                                                                  base.grouping_unit), files)


def refused_everywhere(db, files) -> None:
    """Registration refuses the files, and an adapter refuses a version holding them."""
    from hypocurate.db.retry import run_transaction
    from hypocurate.sources.record import AdapterError
    from hypocurate.sources.versions import SOURCES, RegistrationError, _register_in
    base = version_of(db, "tamu_fcc")
    with pytest.raises(RegistrationError, match="curation.json"):
        run_transaction(db, lambda conn: _register_in(conn, SOURCES["tamu_fcc"], files, base.sealed_at.date()))
    with pytest.raises(AdapterError, match="curation.json"):
        adapters.read(sealed_as(base, files))


def test_the_frozen_export_on_its_own_base_is_accepted(db):
    register_base(db)
    base = version_of(db, "tamu_fcc")
    files = {**dict(base.files), CURATION_PATH: encode(frozen_curation())}
    records = adapters.read(sealed_as(base, files)).records
    assert {records[0].harmonized[f].value for f in ("test_type", "phase_class")} == {"tension", "FCC"}


def test_an_export_copied_onto_another_base_is_refused(db):
    """The reviewer's case: the documentation (or data) changed, so the export's base fingerprint no longer
    matches, even though every quote is still found."""
    register_base(db)
    base = version_of(db, "tamu_fcc")
    changed = dict(base.files)
    changed["documentation/main.tex"] = changed["documentation/main.tex"] + b"\n% a later revision\n"
    refused_everywhere(db, {**changed, CURATION_PATH: encode(frozen_curation())})


def _set(path, value):
    def change(doc):
        target = doc
        for key in path[:-1]:
            target = target[key]
        if value is KeyError:
            del target[path[-1]]
        else:
            target[path[-1]] = value
    return change


T = ("values", "test_type")
@pytest.mark.parametrize("change", [
    _set(("base_version", "fingerprint"), "0" * 64),
    _set(("base_version", "label"), ""),
    _set(("source",), "mpea"),
    _set(T + ("document",), "documentation/absent.tex"),
    _set(T + ("document",), "Grain_Size_Summary_v3.xlsx"),
    _set(T + ("quote",), "Quasistatic tensile testing was used everywhere in this imaginary paper."),
    _set(T + ("quote",), "uasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers"),
    _set(T + ("line",), 178),
    _set(T + ("term",), "tension"),
    _set(T + ("value",), "compression"),
    _set(T + ("value",), "shear"),
    _set(T + ("accepted_by",), "  "),
    _set(T + ("accepted_by",), None),
    _set(T + ("accepted_at",), "yesterday"),
    _set(T + ("accepted_at",), "2026-10-06T23:17:06"),        # no time zone
    _set(T + ("proposal",), "5"),
    _set(T + ("proposal",), True),
    _set(T + ("proposal",), 0),
    _set(T + ("agent_setting_version",), 0),
    _set(T + ("model",), ""),
    _set(T + ("note",), 5),
    _set(T + ("accepted_at",), KeyError),
    _set(("values", "microstructure"), {}),
])
def test_an_export_that_does_not_check_out_is_refused(db, change):
    register_base(db)
    base = version_of(db, "tamu_fcc")
    doc = frozen_curation()
    change(doc)
    refused_everywhere(db, {**dict(base.files), CURATION_PATH: encode(doc)})


def test_a_quote_that_fails_the_current_term_checks_is_refused_on_import(db):
    """A quote that is found, on its line, but no longer passes the checks (here: no testing word for a
    temperature band) is refused like any other."""
    register_base(db)
    base = version_of(db, "tamu_fcc")
    doc = frozen_curation()
    doc["values"]["test_temperature_band"] = {**doc["values"]["phase_class"], "value": "room temperature",
                                              "term": "room temperature"}
    refused_everywhere(db, {**dict(base.files), CURATION_PATH: encode(doc)})
