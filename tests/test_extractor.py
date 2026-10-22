"""Sprint 2 pilot, R4: the Extractor's access path, its model calls and its S0 (owner, 2026-10-22 and 2026-10-23).

Access (an approved safeguard change): the Extractor's complete input is the one parsed document its invocation
names and the reading sections of its evidence specification, and, for the verification call, its own draft on that
document. A planted compilation value, a planted compilation record id and the claim text reach neither its access
input nor the complete outbound request bytes (the extractor's allow-list is the only place S0's reference-blindness
is enforced). It cannot read another document; a Reconciler context reads nothing at the document stage; a document
read is audited with no run and the parsed document named.

Calls: two document invocations per document (extract, verify), each reserved under the per-document cap. Both raw
outputs are stored with their hashes; S0 is the verified result, frozen on the verification output. A value or link
answered 'no' or 'cannot tell', or not answered, keeps its value with a note quoting the verifier; nothing is
dropped; anything code cannot convert is listed in the stored method. A figure-only value is stored ambiguous with
no provenance; a row reporting another paper is stored as cited, never as this paper's observation."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal

import pytest
from sqlalchemy import text

import stub_provider as sp
from access_testing import document_access_for
from hypocurate.access.dispatch import bind_invocation
from hypocurate.access.errors import AccessDenied
from hypocurate.documents.parse_worker import canonical
from hypocurate.pipeline.agents import spend
from hypocurate.pipeline.agents.settings import ensure_setting, extractor_variant
from hypocurate.pipeline.extraction import model_extractor as mx
from hypocurate.pipeline.extraction.interface import EvidenceSpec
from model_builder import World

PDF = b"%PDF-1.7\n% extractor test\n"
PLANTED_VALUE = "987.6543"
PLANTED_RECORD = "ZQREC-4711"
CLAIM = "Yield strength rises as grain size falls"  # the test world's claim text (model_builder.World.draft)
PARSED = {"format": "hypocurate-parse-1", "parser": "docling", "parser_version": "2.141.0", "fallback_used": False,
          "pages": 3, "attempts": [],
          "texts": [{"index": 0, "page": 2, "text": "After annealing at 900 °C for 1 h the grain size was 25 µm and "
                                                     "the yield strength 210 MPa."},
                    {"index": 1, "page": 3, "text": "Fig. 5. Engineering stress-strain curves of the annealed samples."}],
          "tables": [{"index": 0, "page": 2, "caption": "Table 1 Grain sizes",
                      "rows": [["Alloy", "State", "Grain size (µm)", "Yield strength (MPa)"],
                               ["CoCrFeNiMo0.2", "700 °C 1 h", "0.8", "1100"],
                               ["CrMnFeCoNi [12]", "800 °C 1 h", "4.4", "360"]]}]}


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def w(db):
    return World(db)


def stored_parse(w, doi="10.1000/ext.1", parsed=PARSED):
    body = canonical(parsed)
    doc = w.val("INSERT INTO document (doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by) VALUES (:d, :k, "
                "'unpaywall', :p, :h, 'code') RETURNING id", d=doi, k="doi:" + doi, p=PDF, h=hashlib.sha256(PDF).hexdigest())
    return w.val("INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, parsed, "
                 "parsed_sha256, pages, tables_found) VALUES (:d, 'docling', '2.141.0', false, 'parsed', :b, :h, 3, 1) "
                 "RETURNING id", d=doc, b=body, h=hashlib.sha256(body.encode()).hexdigest())


def plant_compilation(w):
    """A compilation version holding a planted value and record id, and a running run with the planted claim."""
    v = w.new_version("mpea", "planted")
    w.add_file(v, "table.csv", f"id,yield\n{PLANTED_RECORD},{PLANTED_VALUE}\n".encode())
    w.seal(v)
    rid = w.locked()
    w.record(rid, key=PLANTED_RECORD)
    assert w.val("SELECT hv.text FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
                 "WHERE r.id = :r", r=rid) == CLAIM
    return rid


def draft(records):
    return json.dumps({"records": records})


def gs_ys_record(reported_from="this paper", ys_text="1100", ys_prov=None, extra_values=(), links=None):
    prov = {"page": 2, "snippet": "0.8 1100", "table_index": 0, "row_index": 1}
    values = [{"field": "alloy", "text": "CoCrFeNiMo0.2", "provenance": prov},
              {"field": "grain_size", "text": "0.8", "unit": "µm", "provenance": prov},
              {"field": "yield_strength", "text": ys_text, "unit": "MPa", "provenance": ys_prov or prov},
              *extra_values]
    return {"reported_from": reported_from, "values": values,
            "links": links if links is not None else [{"from_field": "grain_size", "to_field": "yield_strength",
                                                       "kind": "same_table_row", "provenance": prov}]}


def checks(*entries):
    return sp.fields(checks=json.dumps({"checks": [dict(record=r, item=i, answer=a, quote=q) for r, i, a, q in entries]}))


def run(db, stub, records, verify_entries, w=None):
    stub.queue(sp.reply(sp.fields(records=draft(records)), input_tokens=4000, output_tokens=900),
               sp.reply(checks(*verify_entries), input_tokens=5000, output_tokens=400))
    parse_id = stored_parse(w or World(db))
    return mx.extract_document(db, parse_id, "H1_v1", client_options=sp.client_options(stub)), parse_id


ALL_YES = [(0, "alloy", "yes", "CoCrFeNiMo0.2"), (0, "grain_size", "yes", "0.8"), (0, "yield_strength", "yes", "1100"),
           (0, "link:grain_size-yield_strength", "yes", "same row")]


# --- access --------------------------------------------------------------------------------------------------------

def doc_invocation(db, parse_id, step="extract", spec="H1_v1"):
    setting = ensure_setting(db, "extractor", extractor_variant(step, spec))
    return mx._invocation(db, parse_id, setting)


def test_the_extractors_complete_input_is_its_document_and_the_specs_reading_sections(w, db):
    plant_compilation(w)
    parse_id = stored_parse(w)
    access = bind_invocation(db, doc_invocation(db, parse_id))
    got = {f: access.get(f) for f in mx.EXTRACT_FIELDS}
    spec = EvidenceSpec.load("H1_v1")
    assert set(got["extraction_spec"]["sections"]) == set(spec.content["extractor_sections"]) == {
        "unit_of_observation", "required_measurements", "required_context", "linkage_evidence", "ambiguity_handling"}
    dumped = json.dumps(got, ensure_ascii=False)
    for absent in (PLANTED_VALUE, PLANTED_RECORD, CLAIM, spec.content["claim"], spec.content["analysis"],
                   spec.content["identity_and_rereports"], spec.content["exclusion_rules"], "10.1000/ext.1"):
        assert absent not in dumped
    assert got["parsed_document"]["tables"] == PARSED["tables"] and got["parsed_document"]["pages"] == 3
    with pytest.raises(AccessDenied) as e:  # no draft yet
        access.get("extraction_draft")
    assert e.value.code == "no_draft"
    with db.connect() as conn:
        rows = conn.execute(text("SELECT run_id, role, stage, function, allowed, detail FROM audit_log "
                                 "WHERE role = 'extractor' ORDER BY id")).all()
    assert all(r.run_id is None and r.stage == "document" for r in rows)
    assert {r.function for r in rows if r.allowed} >= {"bind", "parsed_document", "extraction_spec"}
    assert all(r.detail["document_parse"] == parse_id for r in rows)


def test_an_extractor_reads_only_its_own_document_and_a_reconciler_reads_nothing_there(w, db):
    mine, other = stored_parse(w), stored_parse(w, "10.1000/ext.2", PARSED | {"pages": 2})
    inv = doc_invocation(db, mine)
    with pytest.raises(AccessDenied) as e:
        document_access_for(db, inv, other).get("parsed_document")
    assert e.value.code == "stage_mismatch"
    for field in ("parsed_document", "extraction_spec", "extraction_draft"):
        with pytest.raises(AccessDenied) as e:
            document_access_for(db, inv, mine, role="reconciler").get(field)
        assert e.value.code in ("stage_mismatch", "not_on_list")
    bound = bind_invocation(db, inv)
    assert bound.context.role == "extractor" and bound.context.stage == "document"


def test_a_setting_without_a_specification_reads_none(w, db):
    parse_id = stored_parse(w)
    setting = w.val("INSERT INTO agent_setting (role, version, instruction, model) VALUES ('extractor', 77, 'x', "
                    "'claude-sonnet-5-5') RETURNING id")
    inv = mx._invocation(db, parse_id, setting)
    with pytest.raises(AccessDenied) as e:
        bind_invocation(db, inv).get("extraction_spec")
    assert e.value.code == "spec_not_named"


def test_no_planted_value_record_id_or_claim_reaches_the_outbound_requests(w, db, stub):
    plant_compilation(w)
    result, _ = run(db, stub, [gs_ys_record()], ALL_YES, w)
    assert result.failure is None and len(stub.requests) == 2
    for request in stub.requests:
        raw = request["raw"].decode("utf-8")
        for absent in (PLANTED_VALUE, PLANTED_RECORD, CLAIM, "increases with decreasing grain size", "k > 0",
                       "re-report", "10.1000/ext.1"):
            assert absent not in raw, absent
    first, second = stub.bodies()
    assert first["model"] == "claude-sonnet-5-5" and first["max_tokens"] == 32000
    assert first["output_config"] == {"effort": "medium"} and "tools" not in first
    content = first["messages"][0]["content"]
    user = content if isinstance(content, str) else "".join(part.get("text", "") for part in content)
    assert "[page 2, table 0, row 1] CoCrFeNiMo0.2 | 700 °C 1 h | 0.8 | 1100" in user
    system = json.dumps(first["system"], ensure_ascii=False)
    assert "Never present cited data as this paper's own" in system
    assert "Output schema:" in system and '\\"reported_from\\"' in system
    assert "0.8" in json.dumps(second) and second["max_tokens"] == 16000


# --- both raw outputs, S0 on the verified result --------------------------------------------------------------------

def test_both_raw_outputs_are_stored_and_s0_is_the_verified_result(db, stub):
    result, parse_id = run(db, stub, [gs_ys_record()], ALL_YES)
    with db.connect() as conn:
        outs = conn.execute(text("SELECT id, method, raw_output, raw_sha256, status FROM extraction_output "
                                 "WHERE document_parse_id = :p ORDER BY id"), dict(p=parse_id)).all()
        snap = conn.execute(text("SELECT extraction_output_id, raw_sha256 FROM evidence_snapshot WHERE name = 'S0'")).all()
        cands = conn.execute(text("SELECT extraction_output_id FROM candidate_observation")).scalars().all()
    draft_row, verify_row = outs
    assert draft_row.method["step"] == "extract" and verify_row.method["step"] == "verify"
    assert verify_row.method["draft_output_id"] == draft_row.id == result.draft_output_id
    assert verify_row.method["draft_raw_sha256"] == draft_row.raw_sha256
    assert verify_row.method["model"] == "claude-sonnet-5-5" and verify_row.method["prompt_version"] == "v3"
    assert verify_row.method["evidence_spec"] == "H1 v1"
    assert snap == [(verify_row.id, verify_row.raw_sha256)] and set(cands) == {verify_row.id}
    assert json.loads(draft_row.raw_output)["records"][0]["values"][1]["text"] == "0.8"
    # Sonnet 5.5 at $2 / $10 per million tokens: 4000 + 5000 in, 900 + 400 out
    assert result.calls == 2 and result.cost == Decimal("0.031")


def test_a_value_answered_no_or_cannot_tell_or_not_answered_keeps_its_value_with_a_note(db, stub):
    entries = [(0, "alloy", "yes", "x"), (0, "grain_size", "no", "the row says 0.9"),
               (0, "yield_strength", "cannot tell", "none")]  # the link is not answered
    result, _ = run(db, stub, [gs_ys_record()], entries)
    with db.connect() as conn:
        notes = dict(conn.execute(text("SELECT field, ambiguity_note FROM candidate_value")).all())
        link = conn.execute(text("SELECT ambiguous, ambiguity_note FROM extraction_link")).one()
    assert notes == {"alloy": None, "grain_size": 'verification: no: "the row says 0.9"',
                     "yield_strength": 'verification: cannot tell: "none"'}
    assert link == (True, "verification: not answered")
    assert result.verified.answers == {"yes": 1, "no": 1, "cannot tell": 1, "not answered": 1}
    assert result.cannot_tell_share == Decimal(1) / Decimal(3)


def test_what_code_cannot_convert_is_listed_never_dropped_silently(db, stub):
    record = gs_ys_record(extra_values=[{"field": "yield_strength", "text": "950", "unit": "MPa"}],
                          links=[{"from_field": "grain_size", "to_field": "strain_rate", "kind": "same_table_row"}])
    result, _ = run(db, stub, [record], ALL_YES)
    with db.connect() as conn:
        method = conn.execute(text("SELECT method FROM extraction_output WHERE method->>'step' = 'verify'")).scalar()
        ys = conn.execute(text("SELECT value_text, ambiguity_note FROM candidate_value WHERE field = 'yield_strength'")).one()
    assert method["conversion"] == ["record 0: a second 'yield_strength' ('950') was not stored",
                                    "record 0, link 0: names a value the record lacks (grain_size - strain_rate); "
                                    "not stored"]
    assert ys == ("1100", "the extractor gave more than one yield_strength")


def test_a_figure_only_value_is_stored_ambiguous_and_a_cited_row_is_never_this_papers(db, stub):
    figure = {"field": "yield_strength", "text": "figure only", "ambiguity_note": "figure only; no number stated (Fig. 5)"}
    own = gs_ys_record()
    own["values"][2] = figure
    cited = gs_ys_record(reported_from="[12] Otto et al. 2013")
    result, _ = run(db, stub, [own, cited], ALL_YES + [(0, "yield_strength", "yes", "Fig. 5")])
    with db.connect() as conn:
        ys = conn.execute(text("SELECT v.value_text, v.provenance, v.ambiguous, v.ambiguity_note, o.item_index "
                               "FROM candidate_value v JOIN candidate_observation o ON o.id = v.observation_id "
                               "WHERE v.field = 'yield_strength' ORDER BY o.item_index")).all()
        identities = conn.execute(text("SELECT identity FROM candidate_observation ORDER BY item_index")).scalars().all()
    assert ys[0][:4] == ("figure only", None, True, "figure only; no number stated (Fig. 5)")
    assert identities[0]["paper"] == "doi:10.1000/ext.1" and identities[0]["reported_from"] == "this paper"
    assert identities[1]["paper"] == "cited:[12] otto et al. 2013"


def test_a_malformed_answer_is_corrected_once_then_stored_as_a_failed_draft(db, stub):
    stub.queue(sp.reply(sp.fields(records="not json")), sp.reply(sp.fields(records='{"records": "x"}')))
    parse_id = stored_parse(World(db))
    result = mx.extract_document(db, parse_id, client_options=sp.client_options(stub))
    assert result.failure == "extract: malformed" and result.frozen is None and len(stub.requests) == 2
    with db.connect() as conn:
        assert conn.execute(text("SELECT status, method->>'failure' FROM extraction_output")).one() == ("failed", "malformed")
        method = conn.execute(text("SELECT method FROM extraction_output")).scalar_one()
        assert conn.execute(text("SELECT count(*) FROM evidence_snapshot")).scalar() == 0
    assert method["attempts"] == ["malformed", "malformed"]
    assert method["reasons"] == ["the answer is not one JSON object with a 'records' list"] * 2
    assert "not json" not in json.dumps(method)  # the model's text is never stored for a failed call


# --- the per-document cap ------------------------------------------------------------------------------------------

def test_a_document_invocation_is_reserved_under_the_per_document_cap(w, db):
    inv = doc_invocation(db, stored_parse(w))
    assert spend.DOCUMENT_CAP_USD == Decimal("2")
    spend.reserve(db, inv, "claude-sonnet-5-5", Decimal("1.5"))
    with pytest.raises(spend.SpendingRefused) as e:
        spend.reserve(db, inv, "claude-sonnet-5-5", Decimal("0.6"))
    assert e.value.code == "spending_cap_document"
    with db.connect() as conn:
        row = conn.execute(text("SELECT stage, detail FROM audit_log WHERE detail->>'code' = 'spending_cap_document'")).one()
    assert row.stage == "document"


def test_the_extractor_settings_come_from_the_versioned_prompt_files():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1] / "hypocurate/pipeline/extraction/prompts/v3"
    schema = (root / "output_schema.json").read_text(encoding="utf-8").strip()
    for step in ("extract", "verify"):
        v = extractor_variant(step, "H1_v1")
        expected = (root / f"{step}.md").read_text(encoding="utf-8").strip()
        if step == "extract":  # from v2 the output schema is part of the extraction instruction
            expected += "\n\nOutput schema:\n" + schema
        assert v["instruction"] == expected
        assert dict(v["settings"]) == {"reasoning_effort": "medium", "step": step, "prompt_version": "v3",
                                       "evidence_spec": "H1_v1"}
    v1 = extractor_variant("extract", "H1_v1", "v1")  # kept as it was used: no schema in its instruction
    assert "Output schema:" not in v1["instruction"]
    assert "never a filter" in extractor_variant("extract", "H1_v1")["instruction"]
    assert 'text "figure only"' in extractor_variant("extract", "H1_v1")["instruction"]


def test_the_owners_stop_rules():
    """Owner, 2026-10-23: stop and ask if a document costs more than $1, or if verification answers 'cannot tell' for
    more than half of the values (on the first paper, that would mean the prompt is the problem)."""
    assert mx.DOCUMENT_STOP_USD == Decimal("1") and mx.CANNOT_TELL_STOP == Decimal("0.5")
    ok = mx.DocumentRun(1, cost=Decimal("1.00"), verified=mx.Verified([], [], {}, values=10, cannot_tell=5))
    assert mx.stop_reasons(ok) == []
    dear = mx.DocumentRun(1, cost=Decimal("1.01"), verified=mx.Verified([], [], {}, values=10, cannot_tell=6))
    assert mx.stop_reasons(dear) == ["the document cost $1.01 (more than $1)",
                                     "verification answered 'cannot tell' for 6 of 10 values"]


# --- passage provenance and re-conversion (owner, 2026-10-23 evening) ------------------------------------------

PASSAGE = {"page": 2, "snippet": "the yield strength 210 MPa"}


def passage_record():
    r = gs_ys_record()
    r["values"].append({"field": "test_type", "text": "tension", "provenance": PASSAGE,
                        "definition": "from methods, applies to all specimens"})
    return r


def test_a_page_and_snippet_provenance_is_accepted_as_a_passage_that_resolves_on_its_page(db, stub):
    result, parse_id = run(db, stub, [passage_record()], ALL_YES + [(0, "test_type", "yes", "tension")])
    with db.connect() as conn:
        prov, amb = conn.execute(text("SELECT provenance, ambiguous FROM candidate_value WHERE field = 'test_type'")).one()
        method = conn.execute(text("SELECT method FROM extraction_output WHERE method->>'step' = 'verify'")).scalar()
    assert prov["passage"] is True and prov["sentence"] == PASSAGE["snippet"] and amb is False
    assert method["conversion_rule"] == "passage-1" and method["passages"] == 1 and method["conversion"] == []
    from hypocurate.pipeline.extraction import provenance as pv
    from hypocurate.pipeline.extraction.interface import ParsedDocument, Provenance
    with db.connect() as conn:
        doc = ParsedDocument.load(conn, parse_id)
    assert pv.problem(doc, Provenance.passage_of(2, PASSAGE["snippet"])) is None
    assert "not on page 3" in pv.problem(doc, Provenance.passage_of(3, PASSAGE["snippet"]))
    assert Provenance.passage_of(2, "x").location == "p. 2, passage: x"


def test_a_stored_output_is_converted_again_into_a_new_s0_and_the_old_one_is_kept(db, stub, monkeypatch):
    monkeypatch.setattr(mx, "CONVERSION_RULE", "none")  # as before 2026-10-23: a passage was not usable
    result, _ = run(db, stub, [passage_record()], ALL_YES + [(0, "test_type", "yes", "tension")])
    old = result.frozen
    with db.connect() as conn:
        note = conn.execute(text("SELECT ambiguity_note FROM candidate_value WHERE field = 'test_type'")).scalar()
    assert note.startswith("the extractor gave no provenance")
    monkeypatch.setattr(mx, "CONVERSION_RULE", "passage-1")
    new = mx.reconvert(db, old.output_id)
    assert new.output_id != old.output_id and new.raw_sha256 == old.raw_sha256 and new.snapshot_id != old.snapshot_id
    with db.connect() as conn:
        m = conn.execute(text("SELECT method FROM extraction_output WHERE id = :x"), dict(x=new.output_id)).scalar()
        rows = conn.execute(text("SELECT o.extraction_output_id, v.ambiguous FROM candidate_value v JOIN "
                                 "candidate_observation o ON o.id = v.observation_id WHERE v.field = 'test_type' "
                                 "ORDER BY o.extraction_output_id")).all()
        snaps = conn.execute(text("SELECT extraction_output_id FROM evidence_snapshot ORDER BY id")).scalars().all()
    assert m["reconverted_from"] == old.output_id and m["conversion_rule"] == "passage-1" and m["passages"] == 1
    assert rows == [(old.output_id, True), (new.output_id, False)] and snaps == [old.output_id, new.output_id]
    import pytest as _pytest
    with _pytest.raises(ValueError, match="only a verification output"):
        mx.reconvert(db, result.draft_output_id)
