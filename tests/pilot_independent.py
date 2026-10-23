"""Sprint 2 pilot, R9: the independent test-side calculation on a run's frozen primary set (statsmodels,
`reference_stats`), compared with the package's pooled result to the Sprint 1 tolerance (relative 1e-9).

Usage (test side; the deployed image holds no tests/): DATABASE_URL=... python tests/pilot_independent.py RUN_ID
Prints the package's and the independent numbers and exits 1 if they differ beyond the tolerance."""
from __future__ import annotations

import json
import math
import os
import sys

from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(__file__))
import reference_stats as rs  # noqa: E402
from hypocurate.sources.normalize import doi_group_key, same_alloy_key  # noqa: E402

TOLERANCE = 1e-9  # register 'reference_test_tolerance', tier 2


def frozen_rows(conn, run_id: int) -> list:
    """(alloy key, group, grain size µm, yield strength MPa) of the frozen primary set, keyed test-side."""
    out = []
    for h, doi, key in conn.execute(text(
            "SELECT r.harmonized, r.paper_doi, s.key FROM analysis_set a JOIN analysis_set_record ar ON ar.analysis_set_id = a.id "
            "JOIN record r ON r.id = ar.record_id JOIN source_version v ON v.id = r.source_version_id "
            "JOIN source s ON s.id = v.source_id WHERE a.run_id = :r AND a.key = 'primary'"), dict(r=run_id)).all():
        group = "dataset:tamu_fcc" if key == "tamu_fcc" else f"paper:{doi_group_key(doi)}"
        out.append((same_alloy_key(h["composition"]["value"], 1), group, h["grain_size"]["value"],
                    h["yield_strength"]["value"]))
    return out


def compare(conn, run_id: int) -> dict:
    mine = conn.execute(text("SELECT n_records, n_alloys, n_groups, estimate, std_error, p_value FROM analysis_result "
                             "WHERE run_id = :r AND scope = 'pooled'"), dict(r=run_id)).one()
    ref = rs.fit(frozen_rows(conn, run_id))
    rel = lambda a, b: abs(a - b) / abs(b) if b else abs(a - b)  # noqa: E731
    ok = (mine.n_records, mine.n_alloys, mine.n_groups) == (ref["n"], ref["alloys"], ref["groups"]) and all(
        rel(float(a), float(b)) <= TOLERANCE for a, b in ((mine.estimate, ref["k"]), (mine.std_error, ref["se"]),
                                                          (mine.p_value, ref["p"])))
    return {"run": run_id, "package": [mine.n_records, mine.n_alloys, mine.n_groups, float(mine.estimate),
                                       float(mine.std_error), float(mine.p_value)],
            "independent": [ref["n"], ref["alloys"], ref["groups"], ref["k"], ref["se"], ref["p"]], "agree": ok}


if __name__ == "__main__":
    with create_engine(os.environ["DATABASE_URL"]).connect() as c:
        result = compare(c, int(sys.argv[1]))
    print(json.dumps(result))
    sys.exit(0 if result["agree"] else 1)
