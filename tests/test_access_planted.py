"""Step 5: the planted-value test (PRD 4 testing requirement; criterion 14.2, second point).

Distinctive outcome values are planted everywhere the main run stores them
(`access_world`). None may appear, in any encoding we can reasonably anticipate, anywhere
in the complete input of the Planner (before the rules lock), the Critic (between the lock
and the freeze) or the Analyst writing a gap report (a run that ended with no dataset
frozen; owner, 2026-10-05). A positive control shows the detector finds the values where
they are allowed (the Analyst after the freeze).

Single-run scope (owner's addition A): a different value, planted in the original run of
the narrower question and in an earlier run of the same hypothesis, appears in no role's
complete input at any stage.

What "any encoding" covers: the value's decimal text at full precision and rounded to 2, 1
and 0 decimals; its integer part; thousands separators (comma, space, thin space) and a
decimal comma; scientific notation at several precisions; `g` formats; the value in GPa,
ksi and psi; `float.hex`; the IEEE-754 bytes (both byte orders) in hex and base64; the
decimal text in base64, hex and URL encoding. Only encodings of at least five characters
are searched, so that short fragments (for example "48.2") cannot match unrelated text by
chance. The input is searched as JSON (keys and values, with and without ASCII escapes),
as its Python repr, and case-insensitively.
"""
from __future__ import annotations

import base64
import json
import struct
import urllib.parse

import pytest
from sqlalchemy import text

import access_world as aw
from hypocurate.access import Access, role_input
from hypocurate.access.allowlist import ROLES, allowed
from hypocurate.db.engine import make_engine

MPA_PER_KSI = 6.894757293168361
PSI_PER_MPA = 145.03773773020923


def encodings(v: float) -> set[str]:
    s = repr(v)
    whole, _, frac = s.partition(".")
    out = {
        s, f"{v:.2f}", f"{v:.1f}", f"{v:.0f}", str(int(v)),
        f"{v:,}", f"{v:,.2f}", f"{v:,.1f}", f"{v:,.0f}",
        f"{v:,}".replace(",", " "), f"{v:,}".replace(",", " "), f"{v:,}".replace(",", " "),
        f"{whole},{frac}", f"{v:.2f}".replace(".", ","),
        f"{v:e}", f"{v:E}", f"{v:.3e}", f"{v:.4e}", f"{v:.2e}", f"{v:g}", f"{v:.8g}", f"{v:.10g}",
        repr(v / 1000), f"{v / 1000:.4f}", f"{v / 1000:.3f}",
        repr(v / MPA_PER_KSI), f"{v / MPA_PER_KSI:.2f}", f"{v / MPA_PER_KSI:.1f}",
        f"{v * PSI_PER_MPA:.0f}", f"{v * PSI_PER_MPA:.2e}",
        v.hex(),
        struct.pack("<d", v).hex(), struct.pack(">d", v).hex(),
        base64.b64encode(struct.pack("<d", v)).decode(), base64.b64encode(struct.pack(">d", v)).decode(),
        base64.b64encode(s.encode()).decode(), s.encode().hex(), urllib.parse.quote(f"{s} MPa"),
        json.dumps(s), json.dumps(v),
    }
    return {e for e in out if len(e) >= 5}


def leaks(payload, values) -> list[str]:
    """Every (value, encoding) found anywhere in the serialized input."""
    texts = [json.dumps(payload, sort_keys=True, default=str), json.dumps(payload, ensure_ascii=False, default=str),
             repr(payload)]
    haystack = "\n".join(texts)
    folded = haystack.lower()
    found = []
    for v in values:
        for e in sorted(encodings(v)):
            if e in haystack or e.lower() in folded:
                found.append(f"{v}: {e!r}")
    return found


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def inputs_of(engine, world, role, stage):
    return role_input(Access(engine, world.run, role, stage, source_key="mpea" if role == "curator" else None))


def test_the_encodings_catch_the_value_where_it_is_allowed(engine):
    """Positive control: after the freeze the Analyst does receive the outcome values, and the
    detector finds them in its input."""
    world = aw.build(engine, "analysis")
    got = inputs_of(engine, world, "analyst", "analysis")
    found = leaks(got, aw.PLANTED.values())
    for v in aw.PLANTED.values():
        assert any(f.startswith(f"{v}:") for f in found), v
    assert repr(aw.PLANTED["yield_strength"]) in json.dumps(got["flags_full"])
    assert repr(aw.PLANTED["yield_strength"]) in json.dumps(got["stage_outputs"])


def test_the_planted_values_are_stored_everywhere_they_should_be(engine):
    """The test is not vacuous: the values are in the source file, the records (harmonized,
    as reported, in a reason), the flag's numbers, the stage outputs, a model instruction,
    a proposed tag value, and the source's free text."""
    world = aw.build(engine, "curation")
    ys = repr(aw.PLANTED["yield_strength"])
    with engine.connect() as conn:
        def count(sql):
            return conn.execute(text(sql), dict(v=f"%{ys}%")).scalar()
        assert count("SELECT count(*) FROM source_file WHERE convert_from(content, 'UTF8') LIKE :v") == 1
        assert count("SELECT count(*) FROM record WHERE harmonized->'yield_strength'->>'value' LIKE :v") == 3
        assert count("SELECT count(*) FROM record WHERE harmonized::text LIKE :v") == 4  # 3 values, 1 reason
        assert count("SELECT count(*) FROM record WHERE reported::text LIKE :v") == 4
        assert count("SELECT count(*) FROM record WHERE harmonized->'yield_strength'->>'reason' LIKE :v") == 1
        assert count("SELECT count(*) FROM flag WHERE compared_values::text LIKE :v") == 1
        assert count("SELECT count(*) FROM stage_result WHERE output::text LIKE :v AND reasoning LIKE :v "
                     "AND tool_calls::text LIKE :v AND input::text LIKE :v") == 1
        assert count("SELECT count(*) FROM agent_setting WHERE instruction LIKE :v") == 1
        assert count("SELECT count(*) FROM tag_value WHERE value LIKE :v AND status = 'proposed'") == 1
        assert count("SELECT count(*) FROM source WHERE address LIKE :v") == 1
        assert count("SELECT count(*) FROM source_version WHERE label LIKE :v") == 1
        assert count("SELECT count(*) FROM plan WHERE content::text LIKE :v") == 1


def test_no_planted_value_in_the_planners_complete_input(engine):
    world = aw.build(engine, "before_lock")
    got = inputs_of(engine, world, "planner", "before_lock")
    assert set(got) == allowed("planner", "before_lock")
    assert got["record_counts"][0]["n_records"] == 8  # it did read the planted source
    assert leaks(got, aw.PLANTED.values()) == []


def test_no_planted_value_in_the_critics_complete_input(engine):
    world = aw.build(engine, "curation")
    got = inputs_of(engine, world, "critic", "curation")
    assert set(got) == allowed("critic", "curation")
    assert len(got["record_metadata"]) == 8 and got["flags_kind"]
    assert leaks(got, aw.PLANTED.values()) == []


def test_no_planted_value_in_the_gap_report_input(engine):
    world = aw.build(engine, "closed_without_freeze")
    got = inputs_of(engine, world, "analyst", "closed_without_freeze")
    assert set(got) == allowed("analyst", "closed_without_freeze")
    assert got["condition_summaries"]["overall"]["n_records"] == 8
    assert leaks(got, aw.PLANTED.values()) == []


def test_no_planted_value_in_the_commentators_input_without_a_freeze(engine):
    """Owner, 2026-10-05: on a run that ended with no dataset frozen, the Commentator gets only the
    gap-report input, the Analyst's gap report and the run's outcome."""
    world = aw.build(engine, "final_without_freeze")
    got = inputs_of(engine, world, "commentator", "final_without_freeze")
    assert set(got) == allowed("commentator", "final_without_freeze")
    assert aw.GAP_REPORT in json.dumps(got["gap_report"]) and got["outcome"]["outcome"] == "insufficient"
    assert got["condition_summaries"]["overall"]["n_records"] == 8
    assert leaks(got, aw.PLANTED.values()) == []
    assert "extracted yield strength" not in json.dumps(got)  # the Curator's stage output stays out


def test_no_planted_value_in_the_source_free_text_reaches_planner_or_critic(engine):
    """Owner's addition B: the address and version label hold the planted value; sources_meta
    is a fixed set of named plain fields."""
    world = aw.build(engine, "before_lock")
    meta = Access(engine, world.run, "planner", "before_lock").get("sources_meta")
    assert leaks(meta, aw.PLANTED.values()) == []
    assert "example.org" not in json.dumps(meta) and "label" not in json.dumps(meta)


@pytest.mark.parametrize("world_stage", ["before_lock", "curation", "analysis", "closed_without_freeze", "final",
                                         "final_without_freeze"])
def test_nothing_from_another_run_reaches_any_role(engine, world_stage):
    """Owner's addition A: the original run of the narrower question and an earlier run of the
    same hypothesis hold OTHER in records, coefficient, stage outputs and commentary."""
    world = aw.build(engine, world_stage)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM analysis_result WHERE run_id = :r AND estimate = :v"),
                            dict(r=world.original_run, v=aw.OTHER)).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM commentary WHERE run_id = :r"),
                            dict(r=world.original_run)).scalar() == 1
        assert conn.execute(text("SELECT count(*) FROM record WHERE extraction_run_id = :r"),
                            dict(r=world.earlier_run)).scalar() == 3
        assert conn.execute(text("SELECT narrower_of_run_id FROM hypothesis h JOIN hypothesis_version hv "
                                 "ON hv.hypothesis_id = h.id JOIN run r ON r.hypothesis_version_id = hv.id "
                                 "WHERE r.id = :r"), dict(r=world.run)).scalar() == world.original_run
    checked = 0
    for role in ROLES:
        if allowed(role, world_stage):
            got = inputs_of(engine, world, role, world_stage)
            if role != "curator":  # the Curator's input is its own source's bytes
                assert leaks(got, [aw.OTHER]) == [], role
            else:
                assert str(aw.OTHER).encode() not in got["source_content"]["files"]["mpea_planted.csv"]
                assert leaks({k: v for k, v in got.items() if k != "source_content"}, [aw.OTHER]) == []
            checked += 1
    assert checked >= 1
    if world_stage == "before_lock":
        assert inputs_of(engine, world, "planner", "before_lock")["claim"]["narrower_question"] is True
