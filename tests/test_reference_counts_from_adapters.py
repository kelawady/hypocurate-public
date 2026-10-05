"""Step 4: the adapters' output reproduces the reference counts (PRD 10, 14.1a).

The filter below is a copy of the reference script's scope and rules
(`docs/reference/worked_example.py`), written here on the test side to check the
harmonization. It is not package code: eligibility is decided by code under the locked
plan in step 6, and these counts are not a rule.

The Texas A&M count ignores temperature: the source states no test temperature for its
own measurements (step 4 question 3), and how a room-temperature scope treats it is the
owner's step 6 decision."""
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
import pytest

from hypocurate.sources import adapters
from source_helpers import sealed_from_disk

REPO = Path(__file__).resolve().parents[1]


def value(record, field):
    v = record.harmonized[field]
    return v.value if v.status in ("converted", "assigned") else None


def at_least_two_grain_sizes(records):
    sizes = defaultdict(set)
    for r in records:
        sizes[r.alloy].add(value(r, "grain_size"))
    return [r for r in records if len(sizes[r.alloy]) >= 2]


def mpea_reference_set(records):
    """Scope: microstructure FCC, test temperature 20–25 °C; grain size and yield strength
    present; alloys with at least two distinct grain sizes; grain size at least 0.1 µm."""
    scoped = [r for r in records if value(r, "microstructure") == "FCC"
              and value(r, "test_temperature") is not None and 20 <= value(r, "test_temperature") <= 25
              and value(r, "grain_size") is not None and value(r, "yield_strength") is not None]
    return [r for r in at_least_two_grain_sizes(scoped) if value(r, "grain_size") >= 0.1]


def tamu_reference_set(records):
    present = [r for r in records if value(r, "grain_size") is not None and value(r, "yield_strength") is not None]
    return at_least_two_grain_sizes(present)


@pytest.fixture(scope="module")
def mpea():
    return adapters.read(sealed_from_disk("mpea")).records


@pytest.fixture(scope="module")
def tamu():
    return adapters.read(sealed_from_disk("tamu_fcc")).records


def test_mpea_77_records_from_20_papers(mpea):
    chosen = mpea_reference_set(mpea)
    assert len(chosen) == 77
    assert len({r.group.key for r in chosen}) == 20  # derived keys (finding 1)
    assert len({r.paper_doi for r in chosen}) == 20  # DOIs as reported


def test_mpea_rows_are_those_of_the_reference_script(mpea):
    """The same rows as the reference script run on the raw file with pandas."""
    d = pd.read_csv(REPO / "data/sources/mpea/MPEA_dataset.csv")
    d.columns = ['ref', 'formula', 'micro', 'proc', 'phase', 'gs', 'rho_exp', 'rho_calc', 'HV', 'test', 'T', 'YS',
                 'UTS', 'el', 'elp', 'E_exp', 'E_calc', 'O', 'N', 'Cwt', 'doi', 'year', 'title']

    def norm(f):
        comp = {}
        for e, n in re.findall(r'([A-Z][a-z]?)([0-9.]*)', f):
            comp[e] = comp.get(e, 0) + (float(n) if n else 1.0)
        s = sum(comp.values())
        return ''.join(f"{e}{round(100 * v / s, 1):g}" for e, v in sorted(comp.items()))

    d['comp'] = d.formula.map(norm)
    scope = (d.micro == 'FCC') & d['T'].between(20, 25)
    s = d[scope & d.gs.notna() & d.YS.notna()].copy()
    g = s.groupby('comp').gs.nunique()
    s = s[s.comp.isin(g[g >= 2].index)]
    plan = s[s.gs >= 0.1]
    assert len(plan) == 77 and plan.doi.nunique() == 20
    assert [f"MPEA_dataset.csv:row:{i}" for i in plan.index] == [r.source_item_key for r in mpea_reference_set(mpea)]


def test_tamu_21_records_from_9_alloys(tamu):
    chosen = tamu_reference_set(tamu)
    assert len(chosen) == 21
    assert len({r.alloy for r in chosen}) == 9
    assert len({r.group.key for r in chosen}) == 1


def test_pooled_98_records_22_alloys(mpea, tamu):
    pooled = mpea_reference_set(mpea) + tamu_reference_set(tamu)
    assert len(pooled) == 98
    assert len({r.alloy for r in pooled}) == 22
    assert len({r.group.key for r in pooled}) == 21
