"""Sprint 2 pilot, R6: evidence states and the acceptance matrix (PRD v1.2 Section 4; owner, 2026-10-23).

The rules are state events by named rules: R-ambiguous, findings by consequence, R-link-1 and the derived rule for
observations. R-rereport counts a re-extracted copy of a compilation record once (the compilation record survives);
a disputed link removes exactly its record from the primary set and keeps it in the gap count; figure-only and range
values stay 'proposed' with their reason; the freeze stores S1 and S2 and refuses when its independent invariant
fails. The standing S0 of a paper with two documents is the one named by its PDF's hash."""
from __future__ import annotations

import dataclasses
import hashlib
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from hypocurate.documents.parse_worker import canonical
from hypocurate.pipeline import evidence as ev
from hypocurate.pipeline.extraction import s0
from hypocurate.pipeline.extraction.fixture_extractor import FixtureExtractor
from hypocurate.pipeline.extraction.interface import EvidenceSpec, Link, ParsedDocument

DOI = "10.1016/j.ijplas.2018.10.005"
KEY = "doi:" + DOI
OWNER = "K. El-Awady"
HEADER = ["Alloy", "State", "Grain size (µm)", "Yield strength (MPa)"]
ROWS = [["A1", "700 °C", "0.8", "1100"],     # 0: a re-report, values agree
        ["A2", "800 °C", "2.0", "700"],      # 1: a re-report, the compilation's strength 10 % off
        ["A3", "900 °C", "5.0", "500"],      # 2: new (no compilation record)
        ["A4", "1000 °C", "9.0", "figure only"],  # 3: figure-only yield strength
        ["A5", "1100 °C", "0.2–20", "300"],  # 4: a grain-size range
        ["A6", "1200 °C", "12", "250"]]      # 5: its link is ambiguous
COMPILATION = {k: SimpleNamespace(harmonized={"grain_size": SimpleNamespace(value=gs),
                                              "yield_strength": SimpleNamespace(value=ys)})
               for k, gs, ys in (("rec:0", 0.8, 1100.0), ("rec:1", 2.0, 770.0))}


def _document(db, pdf: bytes, rows=ROWS) -> int:
    parsed = {"format": "hypocurate-parse-1", "parser": "docling", "parser_version": "2.141.0", "fallback_used": False,
              "pages": 3, "attempts": [], "texts": [{"index": 0, "page": 2, "text": "Tensile tests at room temperature."}],
              "tables": [{"index": 0, "page": 2, "caption": "Table 1", "rows": [HEADER] + rows}]}
    body = canonical(parsed)
    with db.begin() as conn:
        doc = conn.execute(text("INSERT INTO document (doi, doi_key, oa_source, pdf, pdf_sha256, fetched_by, by_hand, "
                                "access_method) VALUES (:d, :k, 'by_hand', :p, :h, :b, true, 'institutional_credential') "
                                "RETURNING id"), dict(d=DOI, k=KEY, p=pdf, h=hashlib.sha256(pdf).hexdigest(), b=OWNER)
                           ).scalar_one()
        return conn.execute(text(
            "INSERT INTO document_parse (document_id, parser, parser_version, fallback_used, status, parsed, "
            "parsed_sha256, pages, tables_found) VALUES (:d, 'docling', '2.141.0', false, 'parsed', :b, :h, 3, 1) "
            "RETURNING id"), dict(d=doc, b=body, h=hashlib.sha256(body.encode()).hexdigest())).scalar_one()


def _freeze_s0(db, parse_id: int, ambiguous_row: int | None = None) -> int:
    with db.connect() as conn:
        document = ParsedDocument.load(conn, parse_id)
    result = FixtureExtractor().extract(document, EvidenceSpec.load("H1_v1"))
    if ambiguous_row is not None:
        records = list(result.records)
        records[ambiguous_row] = dataclasses.replace(records[ambiguous_row], links=(Link(
            "grain_size", "yield_strength", ambiguity_note="two specimens share this row"),))
        result = dataclasses.replace(result, records=tuple(records))
    return s0.store_and_freeze(db, document, result).output_id


@pytest.fixture
def paper(db):
    out = _freeze_s0(db, _document(db, b"%PDF-1.7\n% evidence test\n"), ambiguous_row=5)
    with db.begin() as conn:
        obs = conn.execute(text("SELECT id FROM candidate_observation WHERE extraction_output_id = :x ORDER BY item_index"),
                           dict(x=out)).scalars().all()
        links = {o: conn.execute(text("SELECT id FROM extraction_link WHERE observation_id = :o"), dict(o=o)).scalar()
                 for o in obs}
        maps = {}
        for i, o in enumerate(obs):
            maps[o] = [_mapping(conn, out, o, "alias_to_composition", f"A{i + 1}", None)]
            if i < 2:
                maps[o].append(_mapping(conn, out, o, "same_observation", f"row {i + 1}", f"rec:{i}"))
            for m in maps[o]:
                _person(conn, "mapping", m, out, "accepted")
    return SimpleNamespace(out=out, obs=obs, links=links, maps=maps, outputs=[(KEY, out)])


def _mapping(conn, out, obs, kind, subject, key):
    m = conn.execute(text("INSERT INTO reconciler_mapping (extraction_output_id, observation_id, kind, subject, proposed, "
                          "applied, compilation_key, mapping_version) VALUES (:x, :o, :k, :s, '{}', '{\"ok\": true}', "
                          ":c, 'reconcile-v2') RETURNING id"), dict(x=out, o=obs, k=kind, s=subject, c=key)).scalar_one()
    conn.execute(text("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, by_rule) "
                      "VALUES ('mapping', :m, :x, 'proposed', 'reconciler')"), dict(m=m, x=out))
    return m


def _person(conn, kind, oid, out, state, reason=None):
    conn.execute(text("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, by_person, "
                      "reason) VALUES (:k, :o, :x, :s, :p, :r)"), dict(k=kind, o=oid, x=out, s=state, p=OWNER, r=reason))


def _finding(db, kind, oid, out, finding, consequence):
    with db.begin() as conn:
        return conn.execute(text("INSERT INTO auditor_finding (object_kind, object_id, extraction_output_id, finding_kind, "
                                 "consequence, detail, by_person) VALUES (:k, :o, :x, :f, :c, 'a sentence', :p) "
                                 "RETURNING id"), dict(k=kind, o=oid, x=out, f=finding, c=consequence, p=OWNER)).scalar_one()


def _status(db, p):
    with db.connect() as conn:
        return {s.observation_id: s for s in ev.status(conn, p.outputs, COMPILATION)}


def test_r_link_1_and_the_derived_rule_accept_re_reports_and_rereport_counts_them_once(db, paper):
    p = paper
    n = ev.apply_rules(db, p.outputs)
    assert n == {ev.R_AMBIGUOUS: 1, ev.R_FINDING: 0, ev.R_LINK_1: 2, ev.R_DERIVED: 2}
    st = _status(db, p)
    a, b, new, fig, rng, amb = (st[o] for o in p.obs)
    assert (a.category, a.rereport_of, a.values_agree) == ("accepted", "rec:0", True)
    assert (b.category, b.rereport_of, b.values_agree) == ("accepted", "rec:1", False)  # resolved identity; qualifier
    assert (new.category, new.reason) == ("proposed", "no accepted grain size - yield strength link")  # owner only
    assert (fig.category, fig.reason) == ("proposed", "figure-only yield strength")
    assert (rng.category, rng.reason) == ("proposed", "grain size is a range")
    assert amb.category == "unresolved"
    assert ev.primary_extracted(list(st.values())) == []  # both accepted records are re-reports: counted once
    with db.connect() as conn:
        rules = conn.execute(text("SELECT object_kind, by_rule, reason FROM evidence_state_event WHERE by_rule LIKE 'r%-%' "
                                  "AND by_rule <> 'reconciler-check' ORDER BY id")).all()
    assert [r.by_rule for r in rules] == [ev.R_AMBIGUOUS, ev.R_LINK_1, ev.R_LINK_1, ev.R_DERIVED, ev.R_DERIVED]
    assert "re-report of rec:0" in rules[1].reason
    assert ev.apply_rules(db, p.outputs) == dict.fromkeys(n, 0)  # nothing changes on a second pass


def test_a_new_observation_enters_only_when_the_owner_accepts_its_link(db, paper):
    p = paper
    with db.begin() as conn:
        _person(conn, "link", p.links[p.obs[2]], p.out, "accepted")
    ev.apply_rules(db, p.outputs)
    st = _status(db, p)
    assert (st[p.obs[2]].category, st[p.obs[2]].rereport_of) == ("accepted", None)
    assert [s.observation_id for s in ev.primary_extracted(list(st.values()))] == [p.obs[2]]


def test_one_disputed_link_removes_exactly_that_record_from_the_primary_set_and_keeps_it_in_the_gap_count(db, paper):
    """PRD v1.2 R6's acceptance condition."""
    p = paper
    with db.begin() as conn:
        _person(conn, "link", p.links[p.obs[2]], p.out, "accepted")
    ev.apply_rules(db, p.outputs)
    before = _status(db, p)
    with db.begin() as conn:
        _person(conn, "link", p.links[p.obs[2]], p.out, "disputed", "the row mixes two specimens")
    after = _status(db, p)
    changed = {o for o in p.obs if before[o].category != after[o].category}
    assert changed == {p.obs[2]} and after[p.obs[2]].category == "disputed"
    assert ev.primary_extracted(list(after.values())) == []
    c = ev.counts(list(after.values()))
    assert c["disputed"] == {"a link or mapping is disputed": 1}
    assert sum(sum(r.values()) for r in c.values()) == len(p.obs)  # every observation is counted somewhere


def test_findings_dispute_by_consequence_and_a_loaded_correction_lifts_a_correction_finding(db, paper):
    p = paper
    q = _finding(db, "mapping", p.maps[p.obs[0]][1], p.out, "not_comparable", "qualified_unresolved")
    _finding(db, "observation", p.obs[1], p.out, "mapping_doubtful", "expert_review")
    _finding(db, "observation", p.obs[2], p.out, "implausible_value", "correction")
    with db.begin() as conn:
        _person(conn, "link", p.links[p.obs[2]], p.out, "accepted")
    n = ev.apply_rules(db, p.outputs)
    assert n[ev.R_FINDING] == 2
    st = _status(db, p)
    assert st[p.obs[0]].category == "accepted" and st[p.obs[0]].qualifiers == (f"finding {q}: not_comparable",)
    assert (st[p.obs[1]].category, st[p.obs[1]].reason) == ("disputed", "a finding disputes it")
    assert st[p.obs[2]].category == "disputed"
    with db.begin() as conn:
        vid = conn.execute(text("SELECT id FROM candidate_value WHERE observation_id = :o AND field = 'yield_strength'"),
                           dict(o=p.obs[2])).scalar()
        conn.execute(text("INSERT INTO value_correction (value_id, corrected_text, unit, reason, by_person) VALUES "
                          "(:v, '510', 'MPa', 'Table 1 reads 510', :p)"), dict(v=vid, p=OWNER))
    ev.apply_rules(db, p.outputs)
    st = _status(db, p)
    assert st[p.obs[2]].category == "accepted"  # the correction it asked for is loaded; the corrected value is read
    assert st[p.obs[1]].category == "disputed"  # an expert-review finding still stands


def test_the_freeze_takes_s1_and_s2_and_refuses_when_the_invariant_fails(db, paper):
    p = paper
    ev.apply_rules(db, p.outputs)
    with db.begin() as conn:
        _person(conn, "link", p.links[p.obs[2]], p.out, "accepted")
    ev.apply_rules(db, p.outputs)
    real = ev.status

    def lying(conn, outputs, compilation=None, event_ids=None):  # status claims a figure-only record is accepted
        out = real(conn, outputs, compilation, event_ids)
        return [dataclasses.replace(s, category="accepted", reason="") if s.observation_id == p.obs[3] else s
                for s in out]
    with pytest.raises(ev.FreezeRefused, match=f"observation {p.obs[3]}: observation {p.obs[3]} is proposed"):
        ev.freeze(db, p.outputs, OWNER, COMPILATION, _status=lying)
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM evidence_snapshot WHERE name IN ('S1', 'S2')")).scalar() == 0
    f = ev.freeze(db, p.outputs, OWNER, COMPILATION)
    assert [s.observation_id for s in f.primary] == [p.obs[2]] and len(f.accepted) == 3
    with db.connect() as conn:
        snaps = {r.name: r for r in conn.execute(text("SELECT id, name, event_ids, events_sha256 FROM evidence_snapshot "
                                                      "WHERE name IN ('S1', 'S2')")).all()}
        rules = dict(conn.execute(text("SELECT id, coalesce(by_rule, 'person') FROM evidence_state_event")).all())
    assert snaps["S2"].events_sha256 == f.events_sha256 and list(snaps["S2"].event_ids) == f.event_ids
    assert {rules[i] for i in snaps["S1"].event_ids} == {"extraction", "reconciler", ev.R_AMBIGUOUS}
    assert set(snaps["S1"].event_ids) < set(snaps["S2"].event_ids)


def test_the_standing_s0_of_a_paper_with_two_documents_is_the_named_one(db, monkeypatch):
    first_pdf, second_pdf = b"%PDF-1.7\n% manuscript\n", b"%PDF-1.7\n% published\n"
    first = _freeze_s0(db, _document(db, first_pdf))
    second = _freeze_s0(db, _document(db, second_pdf))
    monkeypatch.setattr(ev, "STANDING_DOCUMENTS", {})
    with db.connect() as conn:
        assert ev.standing_outputs(conn, "none") == [(KEY, second)]  # without a name, the newest
        monkeypatch.setattr(ev, "STANDING_DOCUMENTS", {KEY: hashlib.sha256(first_pdf).hexdigest()})
        assert ev.standing_outputs(conn, "none") == [(KEY, first)]


def test_a_lifted_dispute_returns_the_owners_acceptance(db, paper):
    p = paper
    with db.begin() as conn:
        _person(conn, "link", p.links[p.obs[2]], p.out, "accepted")
    _finding(db, "link", p.links[p.obs[2]], p.out, "implausible_value", "correction")
    ev.apply_rules(db, p.outputs)
    with db.begin() as conn:
        vid = conn.execute(text("SELECT id FROM candidate_value WHERE observation_id = :o AND field = 'grain_size'"),
                           dict(o=p.obs[2])).scalar()
        conn.execute(text("INSERT INTO value_correction (value_id, corrected_text, unit, reason, by_person) VALUES "
                          "(:v, '5.1', 'µm', 'Table 1 reads 5.1', :p)"), dict(v=vid, p=OWNER))
    ev.apply_rules(db, p.outputs)
    with db.connect() as conn:
        states = conn.execute(text("SELECT state, coalesce(by_rule, 'person') FROM evidence_state_event WHERE "
                                   "object_kind = 'link' AND object_id = :l ORDER BY id"), dict(l=p.links[p.obs[2]])).all()
    assert [tuple(s) for s in states] == [("proposed", "extraction"), ("accepted", "person"),
                                          ("disputed", ev.R_FINDING), ("accepted", ev.R_FINDING)]
    assert _status(db, p)[p.obs[2]].category == "accepted"


def test_r_link_1_takes_only_table_row_links_and_every_link_must_be_accepted(db):
    from hypocurate.pipeline.extraction.interface import Provenance
    parse_id = _document(db, b"%PDF-1.7\n% two links\n", rows=ROWS[:1])
    with db.connect() as conn:
        document = ParsedDocument.load(conn, parse_id)
    result = FixtureExtractor().extract(document, EvidenceSpec.load("H1_v1"))
    record = result.records[0]
    second = Link("alloy", "grain_size", "explicit_sentence", Provenance(page=2, snippet="A1", table_index=0, row_index=1))
    result = dataclasses.replace(result, records=(dataclasses.replace(record, links=record.links + (second,)),))
    out = s0.store_and_freeze(db, document, result).output_id
    with db.begin() as conn:
        obs = conn.execute(text("SELECT id FROM candidate_observation WHERE extraction_output_id = :x"), dict(x=out)).scalar()
        for kind, key in (("alias_to_composition", None), ("same_observation", "rec:0")):
            _person(conn, "mapping", _mapping(conn, out, obs, kind, "A1", key), out, "accepted")
    outputs = [(KEY, out)]
    ev.apply_rules(db, outputs)
    with db.connect() as conn:
        links = dict(conn.execute(text("SELECT l.kind, (SELECT e.state FROM evidence_state_event e WHERE e.object_kind = "
                                       "'link' AND e.object_id = l.id ORDER BY e.id DESC LIMIT 1) FROM extraction_link l "
                                       "WHERE l.observation_id = :o"), dict(o=obs)).all())
        st = ev.status(conn, outputs, COMPILATION)[0]
    assert links == {"same_table_row": "accepted", "explicit_sentence": "proposed"}  # the other kind: owner only
    assert (st.category, st.reason) == ("proposed", "a link not accepted")


def test_r_link_1_needs_a_same_observation_mapping_accepted_by_a_person(db):
    parse_id = _document(db, b"%PDF-1.7\n% rule mapping\n", rows=ROWS[:1])
    out = _freeze_s0(db, parse_id)
    with db.begin() as conn:
        obs = conn.execute(text("SELECT id FROM candidate_observation WHERE extraction_output_id = :x"), dict(x=out)).scalar()
        m = _mapping(conn, out, obs, "same_observation", "A1", "rec:0")
        conn.execute(text("INSERT INTO evidence_state_event (object_kind, object_id, extraction_output_id, state, by_rule) "
                          "VALUES ('mapping', :m, :x, 'accepted', 'some-rule')"), dict(m=m, x=out))
    assert ev.apply_rules(db, [(KEY, out)])[ev.R_LINK_1] == 0


def test_the_evidence_command_applies_the_rules_and_prints_counts(db, paper, monkeypatch, capsys):
    import argparse
    import json
    from hypocurate.documents import cli
    from hypocurate.sources import versions
    versions.register(db, "mpea")
    monkeypatch.setattr(ev, "PROMPT_VERSION", "none")
    parser = argparse.ArgumentParser()
    cli.add_parser(parser.add_subparsers(dest="command"))
    assert cli.command(parser.parse_args(["documents", "evidence", "--status-only"]), db) == 0
    first = json.loads(capsys.readouterr().out)
    assert first["rules"] is None and first["all"]["accepted"] == {}
    assert cli.command(parser.parse_args(["documents", "evidence"]), db) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["rules"][ev.R_DERIVED] == 2 and out["outputs"] == {KEY: paper.out}
    assert out["all"]["proposed"]["figure-only yield strength"] == 1 and out["primary_extracted"] == 0


def test_a_value_flagged_ambiguous_keeps_its_observation_proposed_with_that_reason(db):
    parse_id = _document(db, b"%PDF-1.7\n% ambiguous value\n", rows=ROWS[:1])
    with db.connect() as conn:
        document = ParsedDocument.load(conn, parse_id)
    result = FixtureExtractor().extract(document, EvidenceSpec.load("H1_v1"))
    r = result.records[0]
    values = tuple(dataclasses.replace(v, ambiguity_note="verification: cannot tell") if v.field == "grain_size" else v
                   for v in r.values)
    result = dataclasses.replace(result, records=(dataclasses.replace(r, values=values),))
    out = s0.store_and_freeze(db, document, result).output_id
    with db.connect() as conn:
        st = ev.status(conn, [(KEY, out)], COMPILATION)[0]
    assert (st.category, st.reason) == ("proposed", "grain size flagged ambiguous")


@pytest.mark.parametrize("fault", ["link_proposed", "mapping_disputed", "observation_disputed"])
def test_the_freeze_invariant_refuses_any_non_accepted_part_even_when_status_says_accepted(db, paper, fault):
    """Merge review C1: negative cases for each part the invariant reads (a link still proposed; a mapping a person
    disputed after the rules ran; the observation itself disputed), with a faulty status computation that claims the
    record is accepted."""
    p = paper
    ev.apply_rules(db, p.outputs)  # obs 0 is accepted (a re-report); obs 2's link is still proposed
    target = p.obs[2] if fault == "link_proposed" else p.obs[0]
    with db.begin() as conn:
        if fault == "mapping_disputed":
            _person(conn, "mapping", p.maps[p.obs[0]][0], p.out, "disputed", "the alias is wrong")
        if fault == "observation_disputed":
            _person(conn, "observation", p.obs[0], p.out, "disputed", "not this specimen")
    real = ev.status

    def lying(conn, outputs, compilation=None, event_ids=None):
        return [dataclasses.replace(s, category="accepted", reason="") if s.observation_id == target else s
                for s in real(conn, outputs, compilation, event_ids)]
    with pytest.raises(ev.FreezeRefused, match=f"observation {target}: "):
        ev.freeze(db, p.outputs, OWNER, COMPILATION, _status=lying)
    with db.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM evidence_snapshot WHERE name IN ('S1', 'S2')")).scalar() == 0
