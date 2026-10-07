"""Queries: create, submit, confirm the domain, dispatch, start (PRD 3 steps 1-2; build step 8b).

The command line (and later the website) creates and dispatches queries through these functions only.
Every write follows the locking protocol (README, "Database migrations"): `run_transaction`, then
`hc_write_lock(p_version => …)` before a version's rows change, version before run.

- `create`: a new query (hypothesis) and its first version, a draft, with its domain, its chosen sources and
  its data-sufficiency option (owner, A2: a parameter of the query, chosen before dispatch).
- `submit`: draft -> submitted.
- `confirm_domain`: a named person confirms (or changes) the domain while submitted (owner, A9: at the
  command line `--by "<name>"` is required; the name goes into `review_comment` with the database's time).
- `dispatch`: submitted and confirmed -> dispatched; a queued run that records, for every registered
  source, its newest sealed version if chosen (else 'not_selected'), and the settings version of each run
  role (`settings.RUN_ROLES`). A fixed-plan run (criterion 14.1a, or a narrower question's run, A8) records
  `fixed_plan`. The database refuses an unsupported domain with its own message (PRD 5.5, 14.3).
- `start`: queued -> running.
- `create_narrower`: the narrower question of a run completed as partly sufficient (owner, Q10, A8): a
  separate query linked to that run, created as submitted, with its original's domain, sources and option,
  and a text built by code from `NARROWER_TEXT`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Mapping

from sqlalchemy import Connection, Engine, text

from hypocurate.db.retry import run_transaction
from hypocurate.pipeline.agents import settings as agent_settings

LOCK_TIMEOUT_MS = 5000
REVIEWER_MAX = 200
# The narrower question's text (owner, A8; register 'narrower_question_text'): code-built, never a model's.
NARROWER_TEXT = "{original} (narrower question: {scope})"
CONSTRUCTED_MARK = "constructed_test_data"


class QueryRefused(Exception):
    """A query operation refused with a fixed code and a stated reason."""

    def __init__(self, code: str, reason: str):
        self.code, self.reason = code, reason
        super().__init__(f"{code}: {reason}")


@dataclass(frozen=True)
class Query:
    hypothesis_id: int
    number: str
    version_id: int


def _lock_version(conn: Connection, version_id: int) -> str:
    conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
    return conn.execute(text("SELECT hc_write_lock(p_version => :v)"), dict(v=version_id)).scalar_one()


def _domain_id(conn: Connection, key: str) -> int:
    found = conn.execute(text("SELECT id FROM domain WHERE key = :k"), dict(k=key)).scalar_one_or_none()
    if found is None:
        raise QueryRefused("unknown_domain", f"no domain {key!r}")
    return found


def _source_ids(conn: Connection, keys: Iterable[str]) -> list[int]:
    ids = []
    for key in keys:
        found = conn.execute(text("SELECT id FROM source WHERE key = :k"), dict(k=key)).scalar_one_or_none()
        if found is None:
            raise QueryRefused("unknown_source", f"no registered source {key!r}")
        ids.append(found)
    return ids


def create(engine: Engine, claim: str, sources: Iterable[str], domain: str = "grain_size_strengthening",
           sufficiency: str = "fixed_minimum", narrower_of_run: int | None = None) -> Query:
    """A new query with one draft version."""
    sources = list(dict.fromkeys(sources))
    if not sources:
        raise QueryRefused("no_source", "a query chooses at least one source")

    def body(conn: Connection):
        domain_id, source_ids = _domain_id(conn, domain), _source_ids(conn, sources)
        h = conn.execute(text("INSERT INTO hypothesis (narrower_of_run_id) VALUES (:r) RETURNING id, number"),
                         dict(r=narrower_of_run)).one()
        vid = conn.execute(text(
            "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id, sufficiency_option) "
            "VALUES (:h, 1, :t, :d, :o) RETURNING id"), dict(h=h.id, t=claim, d=domain_id, o=sufficiency)).scalar_one()
        for sid in source_ids:
            conn.execute(text("INSERT INTO hypothesis_version_source VALUES (:v, :s)"), dict(v=vid, s=sid))
        return Query(h.id, h.number, vid)

    return run_transaction(engine, body)


def submit(engine: Engine, version_id: int) -> None:
    def body(conn: Connection):
        _lock_version(conn, version_id)
        conn.execute(text("UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v"),
                     dict(v=version_id))

    run_transaction(engine, body)


def confirm_domain(engine: Engine, version_id: int, by: str, domain: str | None = None) -> None:
    """A named person confirms the domain (or changes it to `domain`) while the version is submitted."""
    if not isinstance(by, str) or not by.strip() or len(by.strip()) > REVIEWER_MAX:
        raise QueryRefused("reviewer_missing", f"the reviewer's name is required (at most {REVIEWER_MAX} characters)")

    def body(conn: Connection):
        _lock_version(conn, version_id)
        chosen = conn.execute(text("SELECT domain_id FROM hypothesis_version WHERE id = :v"),
                              dict(v=version_id)).scalar_one()
        domain_id = _domain_id(conn, domain) if domain else chosen
        conn.execute(text("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now(), "
                          "review_comment = :c WHERE id = :v"),
                     dict(d=domain_id, c=f"domain confirmed at the command line by {by.strip()}", v=version_id))

    run_transaction(engine, body)


def dispatch(engine: Engine, version_id: int, *, fixed_plan: bool = False, constructed_test_data: bool = False) -> int:
    """Dispatches the version; returns the queued run's id. `fixed_plan` asks for the reference plan (14.1a). A
    narrower question's run always uses the plan its original's narrowing decision stored: that comes from the
    question's link to its original, never from the caller's flag (step 8b fix round, finding 1; the database
    refuses such a run without the flag, migration 0006)."""
    setting_ids = {role: agent_settings.ensure_setting(engine, role) for role in agent_settings.RUN_ROLES}

    def body(conn: Connection):
        _lock_version(conn, version_id)
        narrower = conn.execute(text("SELECT h.narrower_of_run_id IS NOT NULL FROM hypothesis_version hv JOIN "
                                     "hypothesis h ON h.id = hv.hypothesis_id WHERE hv.id = :v"),
                                dict(v=version_id)).scalar_one()
        conn.execute(text("UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v"),
                     dict(v=version_id))
        flags = json.dumps({CONSTRUCTED_MARK: True} if constructed_test_data else {})
        rid = conn.execute(text("INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags) "
                                "VALUES (:v, :f, CAST(:x AS jsonb)) RETURNING id"),
                           dict(v=version_id, f=fixed_plan or narrower, x=flags)).scalar_one()
        chosen = set(conn.execute(text("SELECT source_id FROM hypothesis_version_source WHERE hypothesis_version_id = :v"),
                                  dict(v=version_id)).scalars())
        for sid, key, latest in conn.execute(text(
                "SELECT s.id, s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id "
                "AND sv.sealed_at IS NOT NULL ORDER BY sv.id DESC LIMIT 1) FROM source s ORDER BY s.id")).all():
            if sid in chosen:
                if latest is None:
                    raise QueryRefused("source_not_sealed", f"the chosen source {key!r} has no sealed version")
                conn.execute(text("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
                                  "VALUES (:r, :s, :sv, 'pending')"), dict(r=rid, s=sid, sv=latest))
            else:
                conn.execute(text("INSERT INTO run_source (run_id, source_id, search_status) "
                                  "VALUES (:r, :s, 'not_selected')"), dict(r=rid, s=sid))
        for role, setting in setting_ids.items():
            conn.execute(text("INSERT INTO run_agent_setting (run_id, role, agent_setting_id) VALUES (:r, :o, :s)"),
                         dict(r=rid, o=role, s=setting))
        return rid

    return run_transaction(engine, body)


def start(engine: Engine, run_id: int) -> None:
    def body(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id))
        conn.execute(text("UPDATE run SET status = 'running', started_at = now() WHERE id = :r"), dict(r=run_id))

    run_transaction(engine, body)


def scope_in_words(scope: Mapping) -> str:
    """A narrower scope in words, from its vocabulary values only."""
    parts = []
    for key, label in (("phase_class", "phase class"), ("test_type", "test type")):
        if scope.get(key):
            parts.append(f"{label} {', '.join(scope[key])}")
    for band in scope.get("temperature_band") or []:
        if isinstance(band, Mapping):
            rng = f" ({band['min']:g} to {band['max']:g} °C)" if "min" in band else ""
            parts.append(f"{band['band']}{rng}")
        else:
            parts.append(str(band))
    return "; ".join(parts)


def create_narrower(engine: Engine, original_run: int, narrower_scope: Mapping) -> Query:
    """The narrower question of a run completed as partly sufficient, created as submitted (Q10)."""
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT hv.text, d.key AS domain, hv.sufficiency_option, hv.id AS vid FROM run r "
            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
            "JOIN domain d ON d.id = hv.confirmed_domain_id WHERE r.id = :r"), dict(r=original_run)).one()
        sources = list(conn.execute(text(
            "SELECT s.key FROM hypothesis_version_source hvs JOIN source s ON s.id = hvs.source_id "
            "WHERE hvs.hypothesis_version_id = :v ORDER BY s.key"), dict(v=row.vid)).scalars())
    q = create(engine, NARROWER_TEXT.format(original=row.text, scope=scope_in_words(narrower_scope)), sources,
               domain=row.domain, sufficiency=row.sufficiency_option, narrower_of_run=original_run)
    submit(engine, q.version_id)
    return q


def submitted_version(engine: Engine, number: str) -> int:
    """The submitted version of query `number` (for `hypocurate dispatch Q-…`)."""
    with engine.connect() as conn:
        vid = conn.execute(text(
            "SELECT hv.id FROM hypothesis h JOIN hypothesis_version hv ON hv.hypothesis_id = h.id "
            "WHERE h.number = :n AND hv.status = 'submitted' ORDER BY hv.version_number DESC LIMIT 1"),
            dict(n=number)).scalar_one_or_none()
    if vid is None:
        raise QueryRefused("not_submitted", f"query {number} has no submitted version to dispatch")
    return vid
