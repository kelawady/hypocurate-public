"""The data generator (PRD 13.3; build step 7), test side.

It produces datasets from the model the system tests, with every property set by us (number of
alloys and their grain sizes, records per grain size, groups and how records are spread over them,
true effect, scatter, per-group shift), so that results can be scored without materials
knowledge. Alloys have invented compositions of the invented elements "Qa" and "Qb", so that no
model could answer from what it knows about real alloys. Deterministic for a seed.

`frozen_data(spec)` gives the records in the shape the access layer's `frozen_analysis_data`
returns, so the package's pure `analysis.analyse` can run on them without a database; `rows(...)`
gives (alloy, group, grain size, outcome) for the reference implementation.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np

from hypocurate.pipeline.plan import default_plan
from hypocurate.sources.normalize import same_alloy_key


@dataclass(frozen=True)
class Spec:
    name: str
    seed: int
    n_alloys: int
    grain_sizes: tuple  # the distinct grain sizes (µm) of every alloy
    repeats: int  # records per alloy and grain size
    n_groups: int
    k: float
    scatter: float
    shift: float
    groups: str = "spread"  # "spread" (round robin), "one" (a single group), "per_alloy" (nested in alloys)
    single_size_alloys: int = 0  # extra alloys measured at one grain size only
    extra: dict = field(default_factory=dict)


def _group(spec: Spec, a: int, n: int) -> int:
    if spec.groups == "one":
        return 0
    if spec.groups == "per_alloy":
        return a % spec.n_groups
    return n % spec.n_groups


def frozen_data(spec: Spec) -> dict:
    rng = np.random.default_rng(spec.seed)
    shifts = rng.normal(0.0, spec.shift, spec.n_groups)
    records, n = [], 0
    layout = [(a, d) for a in range(spec.n_alloys) for d in spec.grain_sizes]
    layout += [(spec.n_alloys + j, spec.grain_sizes[0]) for j in range(spec.single_size_alloys)]
    for a, d in layout:
        for _ in range(spec.repeats):
            g = _group(spec, a, n)
            y = 250.0 + 40.0 * a + spec.k * d ** -0.5 + shifts[g] + rng.normal(0.0, spec.scatter)
            n += 1
            records.append({"id": n, "source": "mpea", "version_fingerprint": f"gen-{spec.name}",
                            "origin": f"generated:{spec.name}:row:{n}", "item_index": n - 1,
                            "composition": {"Qa": float(10 + a), "Qb": float(90 - a)},
                            "paper": f"paper-{g:03d}", "batch": None, "grain_size": float(d), "outcome": float(y)})
    fp = hashlib.sha256(f"{spec.name}|{spec.seed}".encode()).hexdigest()
    return {"freeze_fingerprint": fp, "outcome_field": "yield_strength", "sets": {"primary": [r["id"] for r in records]},
            "records": records}


def rows(data: dict, ids=None) -> list[tuple]:
    chosen = [r for r in data["records"] if ids is None or r["id"] in set(ids)]
    return [(same_alloy_key(r["composition"]), r["paper"], r["grain_size"], r["outcome"]) for r in chosen]


def plan(option: str = "fixed_minimum", minimums=(30, 5, 10, 10), n_simulations: int = 2000) -> dict:
    """The default plan without sensitivity analyses (generated data have only a primary set)."""
    p = default_plan(1)
    p["sensitivity_analyses"] = []
    p["sufficiency"] = {"option": option, "min_records": minimums[0], "min_alloys": minimums[1],
                        "min_groups": minimums[2], "min_resid_df": minimums[3]}
    p["calibration"]["n_simulations"] = n_simulations
    return p


# The fixed set (PRD 13.3): each dataset with its seed; the expected results are in
# tests/test_generated_fixed_set.py.
FIXED_SET = (
    Spec("effect_many_papers", 101, n_alloys=8, grain_sizes=(1.0, 4.0, 16.0, 64.0), repeats=2, n_groups=12,
         k=300.0, scatter=40.0, shift=20.0),
    Spec("no_effect_many_papers", 102, n_alloys=8, grain_sizes=(1.0, 4.0, 16.0, 64.0), repeats=2, n_groups=12,
         k=0.0, scatter=40.0, shift=20.0),
    Spec("negative_effect", 103, n_alloys=6, grain_sizes=(1.0, 4.0, 16.0, 64.0), repeats=2, n_groups=12,
         k=-200.0, scatter=40.0, shift=20.0),
    Spec("large_paper_shifts", 104, n_alloys=8, grain_sizes=(1.0, 4.0, 16.0, 64.0), repeats=2, n_groups=12,
         k=150.0, scatter=20.0, shift=120.0),
    Spec("small_but_valid", 105, n_alloys=3, grain_sizes=(1.0, 9.0), repeats=2, n_groups=4,
         k=300.0, scatter=30.0, shift=10.0),
    Spec("single_group", 106, n_alloys=6, grain_sizes=(1.0, 4.0, 16.0), repeats=2, n_groups=1,
         k=300.0, scatter=30.0, shift=0.0, groups="one"),
    Spec("one_alloy_two_sizes", 107, n_alloys=1, grain_sizes=(1.0, 9.0), repeats=1, n_groups=2,
         k=300.0, scatter=30.0, shift=0.0),
    Spec("no_alloy_with_two_sizes", 108, n_alloys=0, grain_sizes=(4.0,), repeats=1, n_groups=3,
         k=300.0, scatter=30.0, shift=0.0, single_size_alloys=6),
    Spec("papers_nested_in_alloys", 109, n_alloys=10, grain_sizes=(1.0, 4.0, 16.0), repeats=2, n_groups=10,
         k=300.0, scatter=30.0, shift=30.0, groups="per_alloy"),
    Spec("single_size_alloys_added", 110, n_alloys=8, grain_sizes=(1.0, 4.0, 16.0, 64.0), repeats=2, n_groups=12,
         k=300.0, scatter=40.0, shift=20.0, single_size_alloys=4),
)
SPECS = {s.name: s for s in FIXED_SET}
