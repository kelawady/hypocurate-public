"""Step 7 test helper: small runs through the real pipeline (adapters, Checks, Inclusion, the freeze)
from constructed MPEA-layout files, for the analysis stage and the copy path.

`small_rows(alloys, sizes, papers)` builds rows with invented-looking but parseable formulas (each
alloy a different equiatomic composition), every row in scope (FCC, tension, 25 °C).
`run_on(engine, rows, option, mins)` registers the file as source 'mpea', dispatches a run that
chose it, and takes it through the freeze under the reference plan with the given sufficiency
option and minimums.
"""
from __future__ import annotations

from sqlalchemy import text

import pipeline_world as pw
from hypocurate.pipeline import checkpoints, checks, extract, inclusion
from hypocurate.pipeline.plan import reference_plan

FORMULAS = ("CoCrFeMnNi", "CoCrFeNi", "CoCrNi", "CoFeNi", "CrFeNi", "CoCrMnNi", "CoFeMnNi", "CrFeMnNi",
            "FeMnNi", "CoMnNi", "CoCrFe", "CoNi")


def small_rows(n_alloys: int, sizes=(1.0, 9.0), papers: int = 3, k: float = 300.0, repeats: int = 1,
               base: float = 200.0) -> list[dict]:
    rows, i = [], 0
    for a in range(n_alloys):
        for d in sizes:
            for r in range(repeats):
                noise = ((i * 37) % 11 - 5) * 3.0  # small deterministic scatter
                ys = round(base + 30 * a + k * d ** -0.5 + noise, 1)
                rows.append(pw.mpea_row(FORMULAS[a], d, ys, doi=f"10.1016/j.test.2026.{(i % papers) + 1:03d}"))
                i += 1
    return rows


def plan_for(vid: int, option: str = "fixed_minimum", mins=(30, 5, 10, 10), rules=None) -> dict:
    plan = reference_plan(vid)
    plan["rules"].update(rules or {})
    plan["sufficiency"] = {"option": option, "min_records": mins[0], "min_alloys": mins[1], "min_groups": mins[2],
                           "min_resid_df": mins[3]}
    return plan


def run_on(engine, rows, option="fixed_minimum", mins=(30, 5, 10, 10), marked=False, register=True, rules=None,
           agents=()) -> int:
    if register:
        pw.registered_files(engine, {"mpea": pw.mpea_csv(rows)})
    rid = pw.dispatched_run(engine, sources=("mpea",), marked=marked, sufficiency=option, agents=agents)
    checkpoints.lock_rules(engine, rid, plan_for(pw.version_of(engine, rid), option, mins, rules))
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    inclusion.decide_run(engine, rid)
    checkpoints.freeze_dataset(engine, rid)
    return rid


def rows_of(engine, sql: str, **params) -> list:
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def val(engine, sql: str, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def audit_codes(engine, run_id: int, function: str) -> list:
    return [r[0] for r in rows_of(engine, "SELECT detail->>'code' FROM audit_log WHERE run_id = :r AND function = :f "
                                          "AND NOT allowed ORDER BY id", r=run_id, f=function)]
