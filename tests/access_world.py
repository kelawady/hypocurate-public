"""Test data for the access layer (step 5): runs at every stage, with distinctive outcome
values planted everywhere they are stored, and a second planted value in other runs.

PLANTED: the main run's outcome values. They are in its sealed source file (yield
strength, tensile strength, hardness, and a cell the adapter cannot read, so the value
also sits in a 'not a number' reason), in its stored records (harmonized, as reported,
nested), in a flag's compared numbers, in a Curator stage's output, reasoning and tool
calls, in a model setting's instruction, in a proposed (not approved) tag value, in the
source's free-text address and version label, and in an unnamed key of the plan.

OTHER: a different value in other runs: the original run of the narrower question (its
records, coefficient, stage outputs and commentary) and an earlier, failed run of the same
hypothesis version (its records and stage outputs).

Inside allowed fields (step 5 review, finding 3), PLANTED is also in: category cells
(microstructure, processing method, phase class), the paper title, the DOI, every kind of
plan leaf and the power assumptions, an eligibility rule, a failed source's failure text, a
flag's kind and category, and the source registry's licence and properties edited after
dispatch.

GAP_REPORT: the text of the Analyst's gap report, on runs that end with no dataset frozen.

DIRECTION: a token in the claim and in the plan's hypotheses and field list, for the
Curator test (the Curator is not told the direction of the claim).
"""
from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB

from hypocurate.sources import adapters
from hypocurate.sources.versions import load_sealed_version
from model_builder import FP, World

REPO = Path(__file__).resolve().parent.parent
MPEA_CSV = REPO / "data" / "sources" / "mpea" / "MPEA_dataset.csv"

PLANTED = {"yield_strength": 48213.579, "ultimate_tensile_strength": 57104.263, "hardness": 36912.847}
OTHER = 59324.681
DIRECTION = "ZQXDIR rises as grain size falls"
GAP_REPORT = "Insufficient in the sources searched: grain size is missing for most alloys (GAPTOKEN)."

YS, UTS, HV = "PROPERTY: YS (MPa)", "PROPERTY: UTS (MPa)", "PROPERTY: HV"
GS, TT, TYPE = "PROPERTY: grain size ($\\mu$m)", "PROPERTY: Test temperature ($^\\circ$C)", "PROPERTY: Type of test"
MICRO, PROCESS, PHASE = "PROPERTY: Microstructure", "PROPERTY: Processing method", "PROPERTY: BCC/FCC/other"
TITLE, DOI = "REFERENCE: title", "REFERENCE: doi"
ROLES = ("planner", "curator", "critic", "analyst", "commentator")


def mpea_rows(n: int) -> tuple[list[str], list[dict]]:
    """The MPEA header and the first n real rows that have a grain size and a yield strength."""
    with MPEA_CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r[GS].strip() and r[YS].strip()][:n]
        return list(reader.fieldnames), rows


def planted_csv(value_ys=PLANTED["yield_strength"], value_uts=PLANTED["ultimate_tensile_strength"],
                value_hv=PLANTED["hardness"]) -> bytes:
    """An MPEA-layout file: four real rows, then rows carrying the planted values."""
    header, rows = mpea_rows(4)
    planted = []
    for i, base in enumerate(rows[:3]):
        r = dict(base)
        r[YS], r[UTS], r[HV] = repr(value_ys), repr(value_uts), repr(value_hv)
        r[TYPE], r[TT] = "T", "25.0"
        r[GS] = f"{12.5 + i}"
        planted.append(r)
    # Planted inside fields the blinded views do show: category cells, the title, the DOI.
    planted[0][MICRO] = f"FCC; yield strength {value_ys} MPa"
    planted[0][PROCESS] = f"CAST {value_ys}"
    planted[0][PHASE] = f"FCC {value_ys}"
    planted[0][TITLE] = f"Yield strength of {value_ys} MPa in CoCrNi"
    planted[0][DOI] = f"doi {value_ys}"
    unreadable = dict(rows[0])
    unreadable[YS] = f"{value_ys} MPa"  # the adapter keeps it as 'not a number: ...'
    planted.append(unreadable)
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=header, lineterminator="\n")
    w.writeheader()
    w.writerows(rows + planted)
    return out.getvalue().encode("utf-8")


def sql(world: World, statement: str, **params):
    """Runs one statement in its own transaction; parameters named j_* are JSON."""
    stmt = text(statement).bindparams(*[bindparam(k, type_=JSONB) for k in params if k.startswith("j_")])
    with world.e.begin() as conn:
        return conn.execute(stmt, params)


def val(world: World, statement: str, **params):
    return sql(world, statement, **params).scalar()


@dataclass
class AccessWorld:
    w: World
    run: int  # the main run (a narrower question)
    original_run: int  # the run the narrower question came from
    earlier_run: int  # an earlier run of the same hypothesis version
    records: list[int] = field(default_factory=list)
    flags: list[int] = field(default_factory=list)
    settings: dict = field(default_factory=dict)  # role -> agent setting id recorded for the run
    original_tested_run: int = 0  # step 8b: an earlier run of the original query, with records and a coefficient


def add_planted_version(w: World, key="mpea", content: bytes | None = None, label="v-planted") -> int:
    v = w.new_version(key, label=label)
    w.add_file(v, f"{key}_planted.csv", content or planted_csv())
    w.seal(v)
    w.version[key] = v
    return v


def store_records(w: World, run: int, key="mpea") -> list[int]:
    """The adapter's records of the run's version, stored as step 6 will store them."""
    with w.e.begin() as conn:
        version = load_sealed_version(conn, w.version[key])
    ids = []
    for r in adapters.read(version).records:
        j = r.to_json()
        ids.append(val(w, "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, "
                          "kind, alloy, harmonized, reported, paper_reference, paper_doi, extraction) "
                          "VALUES (:r, :sv, :k, :ix, :kind, :a, :j_h, :j_rep, :pr, :pd, :j_x) RETURNING id",
                       r=run, sv=w.version[key], k=j["source_item_key"], ix=j["item_index"], kind=j["kind"],
                       a=j["alloy"], j_h=j["harmonized"], j_rep=j["reported"], pr=j["paper_reference"],
                       pd=j["paper_doi"], j_x=adapters.extraction(key)))
    return ids


def store_value_records(w: World, run: int, value: float, n=3, key="mpea") -> list[int]:
    """Records whose outcome value is `value` (for runs other than the main one)."""
    ids = []
    for i in range(n):
        h = {"yield_strength": {"value": value, "unit": "MPa", "status": "converted"},
             "grain_size": {"value": 10.0 + i, "unit": "µm", "status": "converted"},
             "composition": {"value": {"Co": 50.0, "Ni": 50.0}, "unit": "at.%", "status": "converted"}}
        rep = {YS: {"column": YS, "text": f"{value}", "unit": "MPa"}}
        ids.append(val(w, "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, "
                          "kind, alloy, harmonized, reported, extraction) "
                          "VALUES (:r, :sv, :k, 0, 'measured', 'Co50Ni50', :j_h, :j_rep, :j_x) "
                          "RETURNING id", r=run, sv=w.version[key], k=f"other-{run}-{i}", j_h=h, j_rep=rep,
                       j_x=adapters.extraction(key)))
    return ids


def stage(w: World, run: int, name: str, role: str, payload: str, attempt=1) -> int:
    sid = w.stage(run, stage=name, role=role, attempt=attempt)
    sql(w, "UPDATE stage_result SET status = 'done', finished_at = now(), input = :j_i, output = :j_o, "
           "reasoning = :rs, tool_calls = :j_t WHERE id = :s",
        j_i={"text": payload}, j_o={"note": payload, "nested": {"values": [payload]}}, rs=payload,
        j_t={"calls": [{"result": payload}]}, s=sid)
    return sid


def planted_plan() -> dict:
    """The plan the main run locks. Step 8b fix round 1 (finding 1): the main run is a narrower question's, so its
    plan must be the narrower plan its original's narrowing decision stored (0006); the original stores this one."""
    ys = PLANTED["yield_strength"]
    # Planted in every kind of plan leaf; the projection keeps only named keys, vocabulary
    # values (else the marker), numbers and field names.
    return {"claim": DIRECTION,
               "variables": {"outcome": {"field": "yield_strength", "unit": f"{ys} MPa", "note": f"{ys}"},
                             "predictor": {"field": "grain_size", "unit": "µm", "transformation": f"x^{ys}"}},
               "model": {"name": "hall_petch_alloy_intercepts", "null": "k <= 0",
                         "alternative": f"k > 0 ({DIRECTION}, {ys})", "alpha": 0.05, "comment": f"{ys}"},
               "scope": {"phase_class": ["FCC", f"FCC {ys}"], "alloy_class": [f"{ys}"], "free": f"{ys}"},
               "fields_to_extract": ["grain_size", "yield_strength", "composition", DIRECTION, repr(ys), ys],
               "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1, "note": f"{ys}"},
                                   {"rule": f"ys above {ys}", "values": ["tension", f"{ys}"]}],
               "eligibility_rules": [{"flag_kind": "values_disagree", "rule": f"keep {ys}"}],
               "verdict_statement": f"supported if {ys}",
               "sensitivity_analyses": ["tension_and_compression", f"drop {ys}"],
               "unnamed_key": {"planted": ys}}


def lock(w: World, run: int) -> None:
    ys = PLANTED["yield_strength"]
    content = planted_plan()
    sql(w, "INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
           "min_groups, min_resid_df, power_assumptions) VALUES (:r, :j_c, :fp, 'fixed_minimum', 4, 1, 2, 1, :j_p)",
        r=run, j_c=content, fp=FP, j_p={"method": "information_only", "scatter": 60.0, "note": f"{ys}",
                                         "smallest_effect": f"{ys}"})


def original_run(w: World) -> tuple[int, int]:
    """The run a narrower question comes from, completed as 'partly sufficient', and an earlier run of
    the same original query. Step 8b (0006; owner, A5): a partly-sufficient run has no plan and no
    record, only code's narrowing decision, so OTHER is planted in its stage outputs and commentary, and
    in the earlier run's records and coefficient. Returns (original run, earlier tested run)."""
    # Step 7 (owner's decision 1): under the fixed option a run below the minimums stores no
    # coefficient, so the earlier run, which holds OTHER as its coefficient, has minimums it meets.
    # (The query keeps the default option: its narrower question, the main run, must have the same.)
    vid = w.dispatched(sources=("mpea",))
    tested = w.running(vid=vid, sources=("mpea",))
    w.lock(tested, mins=(1, 1, 1, 1))
    w.search(tested, "mpea")
    recs = store_value_records(w, tested, OTHER)
    primary = w.analysis_set(tested)
    for rec in recs:
        w.decide(tested, rec)
        w.add(primary, rec)
    w.freeze(tested, len(recs))
    sql(w, "INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, "
           "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met, estimate) "
           "VALUES (:r, 'pooled', :s, 3, 1, 1, 1, 1, true, false, true, :e)", r=tested, s=primary, e=OTHER)
    w.complete(tested, "insufficient", level=4)
    rid = w.running(vid=vid, sources=("mpea",))
    stage(w, rid, "analyst", "analyst", f"k = {OTHER}")
    w.partly(rid, narrower_plan=planted_plan())
    cid = stage(w, rid, "commentator", "commentator", f"the coefficient {OTHER}")
    sql(w, "INSERT INTO commentary (run_id, stage_result_id, status, text, model, number_check) "
           "VALUES (:r, :s, 'written', :t2, 'model-b', 'all_match')", r=rid, s=cid, t2=f"k was {OTHER}")
    return rid, tested


def code_output(w: World, run: int, name: str, output: dict, attempt: int = 1) -> int:
    """A done code stage result (role NULL) with `output`, as `writes.code_stage` writes it."""
    sid = w.stage(run, stage=name, role=None, attempt=attempt)
    sql(w, "UPDATE stage_result SET status = 'done', finished_at = now(), output = :j_o WHERE id = :s",
        j_o=output, s=sid)
    return sid


def stored_facts(w: World, run: int, frozen: bool) -> None:
    """Step 8b: the statistics and gap-facts outputs code stores (step 7), with a planted value in keys
    the Analyst's facts do not name (and, without a freeze, nowhere it may see)."""
    hidden = {"yield_strength": PLANTED["yield_strength"]}
    decision = {"state": "sufficient" if frozen else "no_dataset_frozen", "outcome": "insufficient",
                "outcome_wording": "insufficient in the sources searched", "verdict": None, "verdict_wording": None,
                "exploratory": False, "evidence_level": 1, "evidence_level_wording": "no dataset frozen",
                "label": None, "freeze_fingerprint": None, "hidden": hidden}
    analyses = [{"analysis": "pooled", "scope": "pooled", "set": "primary", "source": None, "withheld": False,
                 "counts": {"n_records": 3, "n_alloys": 1, "hidden": hidden}, "estimate": 424.9, "std_error": 64.4,
                 "records_found": [f"{PLANTED['yield_strength']}"], "hidden": hidden}] if frozen else []
    code_output(w, run, "statistics", {"decision": decision, "analyses": analyses, "not_analysed": [],
                                       "withheld": False, "hidden": hidden})
    code_output(w, run, "gap_facts", {"minimums": None, "minimums_missed": [], "records_lacking_fields": {},
                                      "eligibility_rules": {}, "sources": [], "hidden": hidden})


def build(engine, stage_name: str) -> AccessWorld:
    """A main run at `stage_name` (one of the access stages, or 'queued' / 'failed')."""
    w = World(engine)
    # B: planted values in the source's free text: the version label and the address.
    add_planted_version(w, label=f"label {PLANTED['yield_strength']}")
    sql(w, "UPDATE source SET address = :a WHERE key = 'mpea'", a=f"https://example.org/{PLANTED['yield_strength']}")
    settings = {"planner": val(w, "INSERT INTO agent_setting (role, version, instruction, model) "
                                  "VALUES ('planner', 1, :i, 'model-a') RETURNING id",
                               i=f"remember {PLANTED['yield_strength']}")}
    sql(w, "INSERT INTO tag_value (kind, value, status, decided_at) "
           "VALUES ('property', 'yield strength', 'approved', now()) "
           "ON CONFLICT (kind, value) DO NOTHING")  # seeded by migration 0002 (step 6)
    sql(w, "INSERT INTO tag_value (kind, value, status) VALUES ('property', :v, 'proposed')",
        v=f"strength {PLANTED['yield_strength']}")
    original, tested = original_run(w)
    h = w.hypothesis(narrower_of=original)
    vid = val(w, "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
                 "VALUES (:h, 1, :t, :d) RETURNING id", h=h, t=DIRECTION, d=w.domain["grain_size_strengthening"])
    for key in ("mpea", "tamu_fcc"):
        w.run_sql("INSERT INTO hypothesis_version_source VALUES (:v, :s)", v=vid, s=w.source[key])
    w.submit(vid)
    w.confirm(vid)
    w.dispatch_version(vid)
    earlier = w.running(vid=vid, sources=("mpea", "tamu_fcc"))
    w.lock(earlier, content=planted_plan())
    store_value_records(w, earlier, OTHER)
    stage(w, earlier, "curator", "curator", f"saw {OTHER}")
    w.fail(earlier)
    rid = w.run(vid=vid, sources=("mpea", "tamu_fcc"))
    world = AccessWorld(w, rid, original, earlier)
    world.original_tested_run = tested
    # Dispatch records the agent setting of each role (the dispatcher reads roles from here).
    for role in ROLES:
        sid = settings.get(role) or val(w, "INSERT INTO agent_setting (role, version, instruction, model) "
                                           "VALUES (:o, 1, 'instruction', 'model-a') RETURNING id", o=role)
        settings[role] = sid
        sql(w, "INSERT INTO run_agent_setting (run_id, role, agent_setting_id) VALUES (:r, :o, :a)",
            r=rid, o=role, a=sid)
    world.settings = settings
    # Edits to the source registry after dispatch must change nothing for this run.
    sql(w, "UPDATE source SET licence = :l, properties_covered = :p WHERE key = 'mpea'",
        l=f"licence {PLANTED['yield_strength']}", p=["yield_strength", f"{PLANTED['yield_strength']}"])
    if stage_name == "queued":
        return world
    w.start(rid)
    if stage_name == "failed":
        w.fail(rid)
        return world
    if stage_name == "before_lock":
        return world
    if stage_name == "narrowed":
        # Step 8b (A4): code's narrowing decision of partly sufficient, stored with named keys; a planted
        # value in a key that is not named must never reach a role.
        code_output(w, rid, "narrowing", {
            "result": "partly_sufficient", "reason": "zero_parts_and_narrower_plan",
            "claim_scope": {"phase_class": ["FCC"], "temperature_band": [{"band": "room temperature"},
                                                                         {"band": "cryogenic", "min": -200.0,
                                                                          "max": -150.0}],
                            "test_type": ["tension"]},
            "part_counts": [{"part": "phase_class", "value": "FCC", "n": 3}],
            "zero_parts": [{"part": "temperature_band", "value": "cryogenic"}],
            "narrower_scope": {"phase_class": ["FCC"], "temperature_band": ["room temperature"],
                               "test_type": ["tension"]},
            "hidden": {"yield_strength": PLANTED["yield_strength"]}})
        return world
    lock(w, rid)
    w.search(rid, "mpea")
    w.search(rid, "tamu_fcc", status="failed", nothing_found="failed_search",
             reason=f"timed out after reading {PLANTED['yield_strength']}")
    world.records = store_records(w, rid)
    planted = [r for r in world.records
               if val(w, "SELECT harmonized->'yield_strength'->>'value' FROM record WHERE id = :r", r=r)
               == repr(PLANTED["yield_strength"])]
    fid = val(w, "INSERT INTO flag (run_id, kind, category, compared_values) "
                 "VALUES (:r, 'values_disagree', 'differ beyond tolerance', :j_cv) RETURNING id",
              r=rid, j_cv={"yield_strength": [PLANTED["yield_strength"], 47000.25], "text": f"{PLANTED['yield_strength']}"})
    for rec in planted[:2]:
        sql(w, "INSERT INTO flag_record VALUES (:f, :r)", f=fid, r=rec)
    world.flags.append(fid)
    world.flags.append(val(w, "INSERT INTO flag (run_id, kind, category) VALUES (:r, :k, :c) RETURNING id", r=rid,
                           k=f"kind {PLANTED['yield_strength']}", c=f"differ by {PLANTED['yield_strength']}"))
    stage(w, rid, "curator", "curator", f"extracted yield strength {PLANTED['yield_strength']} MPa")
    if stage_name == "curation":
        return world
    for i, rec in enumerate(world.records):
        w.decide(rid, rec, rule=f"kept at {PLANTED['yield_strength']}" if i == 0 else "in_scope")
    if stage_name in ("closed_without_freeze", "final_without_freeze"):
        sql(w, "INSERT INTO calibration_result (run_id, status, reason) VALUES (:r, 'unavailable', 'no_dataset_frozen')",
            r=rid)
        stored_facts(w, rid, frozen=False)
        # The Analyst's gap report (it never saw an outcome value, so it holds none).
        stage(w, rid, "analyst", "analyst", GAP_REPORT)
        if stage_name == "final_without_freeze":
            w.complete(rid, "insufficient")
        return world
    if stage_name in ("analysis", "final"):
        primary = w.analysis_set(rid)
        for rec in world.records:
            w.add(primary, rec)
        w.freeze(rid, len(world.records))
        stored_facts(w, rid, frozen=True)
        if stage_name == "final":
            # Step 8b (0006; owner, A5): a run with a plan never completes as partly sufficient.
            w.complete(rid, "insufficient", level=4)
        return world
    raise ValueError(stage_name)
