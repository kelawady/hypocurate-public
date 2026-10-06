"""Real results only (build step 7; owner, 2026-10-05; register 'constructed_test_runs').

A run marked as a test with constructed data (`run.experiment_flags.constructed_test_data`) keeps
its results, each labelled "test run: includes constructed data", and is left out of every
aggregate, count or list of real results. Every such query goes through `REAL_RUN`, the one
named condition; the screens of step 10 must use it.
"""
from __future__ import annotations

from sqlalchemy import Connection, text

# The one named condition: a run that is not marked as a test (`r` is the run table's alias).
REAL_RUN = "NOT coalesce(r.experiment_flags->>'constructed_test_data' = 'true', false)"


def real_runs(conn: Connection) -> list:
    """Completed runs that are not marked as a test: id, outcome, verdict, exploratory, level."""
    return conn.execute(text(f"SELECT r.id, r.outcome, r.verdict, r.exploratory, r.evidence_level FROM run r "
                             f"WHERE r.status = 'completed' AND {REAL_RUN} ORDER BY r.id")).all()


def real_outcome_counts(conn: Connection) -> dict:
    """Completed real runs per outcome (an aggregate: marked runs never count)."""
    return dict(conn.execute(text(f"SELECT r.outcome, count(*) FROM run r WHERE r.status = 'completed' "
                                  f"AND {REAL_RUN} GROUP BY r.outcome")).all())


def real_analysis_results(conn: Connection) -> list:
    """Analysis results of runs that are not marked as a test."""
    return conn.execute(text(f"SELECT ar.* FROM analysis_result ar JOIN run r ON r.id = ar.run_id "
                             f"WHERE {REAL_RUN} ORDER BY ar.id")).all()
