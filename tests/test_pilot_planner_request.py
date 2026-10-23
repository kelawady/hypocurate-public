"""Merge review A2 (2026-10-23): an ordinary Planner request (the complete outbound JSON body: instruction, inputs and
the response schema DSPy states) is byte-identical to main's. The reference file was captured by this same test body run
under main at eb78ec0 (a separate worktree, main's own test helpers) and stored as tests/golden/planner_request_main_eb78ec0.json;
the widened source vocabulary changes nothing a Planner call sends."""
import json, os
import pipeline_world as pw
import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queries
from hypocurate.pipeline.agents import planner

CLAIM = "In FCC multi-principal-element alloys, yield strength rises as grain size falls"
ANSWER = {"domain_matches": True, "claim_scope": {"alloy_class": ["multi-principal-element (high-entropy) alloy"],
          "phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [{"band": "room temperature"}]},
          "stated": {"alloy_class": True, "phase_class": True, "test_type": False, "temperature_band": False},
          "outcome": "yield_strength", "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1}], "narrower": None}


def test_an_ordinary_planner_request_is_byte_identical_to_mains(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    q = queries.create(e, CLAIM, ("mpea", "tamu_fcc"), sufficiency="fixed_minimum")
    queries.submit(e, q.version_id)
    queries.confirm_domain(e, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(e, q.version_id)
    queries.start(e, rid)
    s = sp.StubProvider()
    try:
        s.queue(sp.reply(sp.fields(plan=json.dumps(ANSWER))))
        result = planner.run_planner(e, rid, client_options=sp.client_options(s))
        assert result.failure is None
        [request] = s.requests
        got = json.dumps(json.loads(request["raw"]), indent=1, sort_keys=True, ensure_ascii=False)
        golden = open(os.path.join(os.path.dirname(__file__), "golden", "planner_request_main_eb78ec0.json"),
                      encoding="utf-8").read()
        assert got == golden and "extracted_pilot" not in got and "Your output fields are" in got
    finally:
        s.close()
    e.dispose()
