"""Sprint 2 pilot, R7 and acceptance criterion 1 (owner, 2026-10-23; register 'pilot_s2_scoring'): the S2 table
(corrected performance) beside the S0 table, with the same rows and columns, on each paper's standing S0; the score
command uses the standing S0."""
from __future__ import annotations

import hashlib
from decimal import Decimal

import pytest
from sqlalchemy import text

from hypocurate.pipeline import evidence as ev
from hypocurate.scoring import score as sc
from hypocurate.scoring import tables
from hypocurate.sources import versions
from test_evidence import COMPILATION, KEY, OWNER, _document, _freeze_s0, _person, paper  # noqa: F401 (fixture)


@pytest.fixture
def frozen(db, paper, monkeypatch):  # noqa: F811
    """The paper's rules applied, a correction loaded, one observation disputed by a person, then the freeze (S2);
    then a second correction after the freeze."""
    monkeypatch.setattr(ev, "PROMPT_VERSION", "none")
    versions.register(db, "mpea")
    p = paper
    with db.begin() as conn:
        _person(conn, "link", p.links[p.obs[2]], p.out, "accepted")
        _person(conn, "observation", p.obs[4], p.out, "disputed", "a range, not one specimen")
        v0 = conn.execute(text("SELECT id FROM candidate_value WHERE observation_id = :o AND field = 'yield_strength'"),
                          dict(o=p.obs[0])).scalar()
        conn.execute(text("INSERT INTO value_correction (value_id, corrected_text, unit, reason, by_person) VALUES "
                          "(:v, '1150', 'MPa', 'Table 1 reads 1150', :p)"), dict(v=v0, p=OWNER))
    ev.apply_rules(db, p.outputs)
    ev.freeze(db, p.outputs, OWNER, COMPILATION)
    with db.begin() as conn:
        v1 = conn.execute(text("SELECT id FROM candidate_value WHERE observation_id = :o AND field = 'yield_strength'"),
                          dict(o=p.obs[1])).scalar()
        conn.execute(text("INSERT INTO value_correction (value_id, corrected_text, unit, reason, by_person) VALUES "
                          "(:v, '999', 'MPa', 'after the freeze', :p)"), dict(v=v1, p=OWNER))
    return p


def test_s2_drops_disputed_observations_and_reads_corrections_loaded_before_the_freeze(db, frozen):
    p = frozen
    s0, d0 = sc.predictions_s0(db, p.out)
    s2, d2 = sc.predictions_s2(db, p.out)
    assert (d0["snapshot"], d2["snapshot"]) == ("S0", "S2")
    assert {x.ref for x in s0} - {x.ref for x in s2} == {f"obs:{p.obs[4]}"} and d2["dropped_disputed"] == 1
    by = {x.ref: x for x in s2}
    assert by[f"obs:{p.obs[0]}"].ys.low == Decimal("1150") and d2["corrections_applied"] == 1  # before the freeze
    assert by[f"obs:{p.obs[1]}"].ys.low == Decimal("700")  # the correction after the freeze is not read


def test_the_s0_and_s2_tables_have_the_same_rows_and_columns(db, frozen):
    rows = tables.build(db)
    s0 = [(r["paper"], r["table"]) for r in rows if r["snapshot"] == "S0"]
    s2 = [(r["paper"], r["table"]) for r in rows if r["snapshot"] == "S2"]
    assert s0 == s2 and ("POOLED", "vs compilation") in s0
    assert all(tuple(r) == tables.COLUMNS for r in rows)
    pooled = {r["snapshot"]: r for r in rows if r["paper"] == "POOLED" and r["table"] == "vs compilation"}
    assert pooled["S0"]["predictions_own"] - pooled["S2"]["predictions_own"] == 1  # the disputed one
    md = tables.to_markdown(rows)
    assert md.index(tables.LABEL["S0"]) < md.index(tables.LABEL["S2"])
    assert tables.to_csv(rows).splitlines()[0] == ",".join(tables.COLUMNS)


def test_the_score_command_uses_the_standing_s0(db, monkeypatch, capsys):
    import argparse
    import json
    from hypocurate.scoring import cli
    versions.register(db, "mpea")
    monkeypatch.setattr(ev, "PROMPT_VERSION", "none")
    first_pdf = b"%PDF-1.7\n% standing\n"
    first = _freeze_s0(db, _document(db, first_pdf))
    _freeze_s0(db, _document(db, b"%PDF-1.7\n% newer repair\n"))  # newer, not standing
    monkeypatch.setattr(ev, "STANDING_DOCUMENTS", {KEY: hashlib.sha256(first_pdf).hexdigest()})
    parser = argparse.ArgumentParser()
    cli.add_parser(parser.add_subparsers(dest="command"))
    assert cli.command(parser.parse_args(["scoring", "score", "--doi", KEY.removeprefix("doi:")]), db) == 0
    assert json.loads(capsys.readouterr().out)["snapshot"]["output"] == first
