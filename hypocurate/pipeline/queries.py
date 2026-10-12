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
- Step 9a (owner's approval of the step 9 plan, 2026-10-08; the reasons' wording approved with the go for 9a):
  - `dispatch` stores the run's spending ceiling (R5; read by `spend.reserve` on every request, so it holds after
    a crash or a restart) and refuses when this month's counted model calls have reached the monthly cap (R5; PRD
    8, 9.3), or when a chosen source is constructed test data and the run is not marked as a test (Q6; the
    storage guard stays as the backstop);
  - `dispatch_again`: a new queued run of a query whose earlier run ended (PRD 8, 14.4), recording what that run
    recorded (fixed plan, test mark; a ceiling only as given), refused while another run of the query is open;
  - `cancel`: a named person cancels a queued or a waiting run (R3); a started run cannot be cancelled in
    sprint 1.
- `create_narrower`: the narrower question of a run completed as partly sufficient (owner, Q10, A8): a
  separate query linked to that run, created as submitted, with its original's domain, sources and option,
  and a text built by code from `NARROWER_TEXT`.
- Step 10b, fix round 1 (ChatGPT's review; the owner, 2026-10-11):
  - who did it: every write records its action, the name given and where (`db/actions.record`, table
    `action_record`, migration 0009) in its own transaction; `via` is the website, the command line or code;
  - act only on the version shown: the website sends the version it displayed and its `version_fingerprint`; each
    write compares both with the stored version under the version lock, in its transaction, and refuses a
    difference as `stale` (`STALE`). On the website both are required. A page that submits passes `submit=True`,
    so the version written is the version submitted, in one transaction.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Mapping

from sqlalchemy import Connection, Engine, text

from hypocurate.db import actions
from hypocurate.db.actions import CODE, COMMAND_LINE, WEBSITE as VIA_WEBSITE
from hypocurate.db.retry import run_transaction
from hypocurate.pipeline.agents import settings as agent_settings

LOCK_TIMEOUT_MS = 5000
REVIEWER_MAX = 200
# The narrower question's text (owner, A8; register 'narrower_question_text'): code-built, never a model's.
NARROWER_TEXT = "{original} (narrower question: {scope})"
CONSTRUCTED_MARK = "constructed_test_data"
OPEN_STATUSES = ("queued", "waiting", "running")
# Step 9a: the fixed reasons (owner, 2026-10-08; the monthly cap's in the owner's own words).
REASONS = {
    "month_cap_reached": "this month's model calls have reached the monthly cap ($50); dispatch is refused until next "
                         "month, or until the owner raises the cap",
    "constructed_source_unmarked": "{source} is constructed test data; dispatch it only as a marked test run",
    "already_open": "another run of this query is queued, waiting or running",
}
CANCELLED = {"queued": "cancelled: cancelled by {by} before it started",
             "waiting": "cancelled: cancelled by {by} while waiting for confirmation of the question as tested"}


# Step 10b, fix round 1 (owner's words, 2026-10-11): a page acting on a version that changed since it was shown.
STALE = "This query has changed since you opened it; reload the page"
WHERE_WORDS = {COMMAND_LINE: "at the command line", VIA_WEBSITE: "on the website"}  # in the stored domain comment


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


def _fingerprint(conn: Connection, version_id: int) -> str | None:
    """SHA-256 of the canonical JSON of what a page shows of a version: its query, number, status, hypothesis,
    domains, option, note, sources and review comment."""
    import hashlib
    row = conn.execute(text(
        "SELECT hv.id, h.number, hv.version_number, hv.status, hv.text, d.key AS domain, cd.key AS confirmed_domain, "
        "hv.sufficiency_option, hv.note, hv.review_comment, ARRAY(SELECT s.key FROM hypothesis_version_source hvs "
        "JOIN source s ON s.id = hvs.source_id WHERE hvs.hypothesis_version_id = hv.id ORDER BY s.key) AS sources "
        "FROM hypothesis_version hv JOIN hypothesis h ON h.id = hv.hypothesis_id JOIN domain d ON d.id = hv.domain_id "
        "LEFT JOIN domain cd ON cd.id = hv.confirmed_domain_id WHERE hv.id = :v"), dict(v=version_id)).one_or_none()
    if row is None:
        return None
    content = dict(row._mapping)
    content["sources"] = list(content["sources"])
    return hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def version_fingerprint(bind: Engine | Connection, version_id: int) -> str | None:
    """The fingerprint of a version as stored now (a page sends it back with the version's id)."""
    if isinstance(bind, Connection):
        return _fingerprint(bind, version_id)
    with bind.connect() as conn:
        return _fingerprint(conn, version_id)


def _check_shown(conn: Connection, version_id: int, expected_version: int | None, expected_fingerprint: str | None,
                 via: str) -> None:
    """Under the version lock: the version acted on is the one the page showed, unchanged. The website always sends
    both; the command line acts on what it names."""
    if expected_version is None and expected_fingerprint is None and via != VIA_WEBSITE:
        return
    if (expected_version is not None and expected_version != version_id) or not expected_fingerprint \
            or _fingerprint(conn, version_id) != expected_fingerprint:
        raise QueryRefused("stale", STALE)


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
           sufficiency: str = "fixed_minimum", narrower_of_run: int | None = None, note: str | None = None, *,
           by: str | None = None, via: str = COMMAND_LINE, submit: bool = False) -> Query:
    """A new query with one draft version (step 10b: with the submitter's optional note); with `submit`, submitted
    in the same transaction."""
    actions.actor(by, via)
    claim, note = _claim_text(claim), _note_text(note)
    sources = list(dict.fromkeys(sources))
    if not sources:
        raise QueryRefused("no_source", "a query chooses at least one source")

    def body(conn: Connection):
        domain_id, source_ids = _domain_id(conn, domain), _source_ids(conn, sources)
        h = conn.execute(text("INSERT INTO hypothesis (narrower_of_run_id) VALUES (:r) RETURNING id, number"),
                         dict(r=narrower_of_run)).one()
        vid = conn.execute(text(
            "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id, sufficiency_option, note) "
            "VALUES (:h, 1, :t, :d, :o, :n) RETURNING id"),
            dict(h=h.id, t=claim, d=domain_id, o=sufficiency, n=note)).scalar_one()
        for sid in source_ids:
            conn.execute(text("INSERT INTO hypothesis_version_source VALUES (:v, :s)"), dict(v=vid, s=sid))
        actions.record(conn, "create", by, via, version=vid)
        if submit:
            _submit_in(conn, vid, by, via)
        return Query(h.id, h.number, vid)

    return run_transaction(engine, body)


def _submit_in(conn: Connection, version_id: int, by: str | None, via: str) -> None:
    _lock_version(conn, version_id)
    conn.execute(text("UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v"),
                 dict(v=version_id))
    actions.record(conn, "submit", by, via, version=version_id)


def submit(engine: Engine, version_id: int, *, by: str | None = None, via: str = COMMAND_LINE) -> None:
    actions.actor(by, via)
    run_transaction(engine, lambda conn: _submit_in(conn, version_id, by, via))


def confirm_domain(engine: Engine, version_id: int, by: str, domain: str | None = None, *, via: str = COMMAND_LINE,
                   expected_fingerprint: str | None = None) -> str:
    """A named person confirms the domain (or changes it to `domain`) while the version is submitted, on the command
    line or the website (`via`, step 10b; its words in the stored comment, `WHERE_WORDS`). Returns the version's
    fingerprint after the change, which the website's dispatch then sends (fix round 1)."""
    if not isinstance(by, str) or not by.strip() or len(by.strip()) > REVIEWER_MAX:
        raise QueryRefused("reviewer_missing", f"the reviewer's name is required (at most {REVIEWER_MAX} characters)")

    def body(conn: Connection):
        _lock_version(conn, version_id)
        _check_shown(conn, version_id, None, expected_fingerprint, via)
        chosen = conn.execute(text("SELECT domain_id FROM hypothesis_version WHERE id = :v"),
                              dict(v=version_id)).scalar_one()
        domain_id = _domain_id(conn, domain) if domain else chosen
        conn.execute(text("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now(), "
                          "review_comment = :c WHERE id = :v"),
                     dict(d=domain_id, c=f"domain confirmed {WHERE_WORDS[via]} by {by.strip()}", v=version_id))
        actions.record(conn, "confirm_domain", by, via, version=version_id)
        return _fingerprint(conn, version_id)

    return run_transaction(engine, body)


def _ceiling(ceiling) -> Decimal | None:
    if ceiling is None:
        return None
    if not isinstance(ceiling, Decimal) or not ceiling.is_finite() or not ceiling > 0:
        raise QueryRefused("invalid_ceiling", "the ceiling is a positive amount of US dollars")
    return ceiling


def _dispatch_checks(conn: Connection, version_id: int, constructed_test_data: bool) -> None:
    """Step 9a: the monthly cap (R5) and constructed test data (Q6), in the dispatching transaction."""
    from hypocurate.pipeline.agents import spend
    from hypocurate.sources.versions import SOURCES
    if spend.month_total(conn) >= spend.MONTH_CAP_USD:
        raise QueryRefused("month_cap_reached", REASONS["month_cap_reached"])
    if not constructed_test_data:
        for key in conn.execute(text("SELECT s.key FROM hypothesis_version_source hvs JOIN source s ON s.id = "
                                     "hvs.source_id WHERE hvs.hypothesis_version_id = :v ORDER BY s.key"),
                                dict(v=version_id)).scalars():
            if key in SOURCES and SOURCES[key].constructed:
                raise QueryRefused("constructed_source_unmarked",
                                   REASONS["constructed_source_unmarked"].format(source=key))


def dispatch(engine: Engine, version_id: int, *, fixed_plan: bool = False, constructed_test_data: bool = False,
             ceiling: Decimal | None = None, by: str | None = None, via: str = COMMAND_LINE,
             expected_fingerprint: str | None = None) -> int:
    """Dispatches the version; returns the queued run's id. `fixed_plan` asks for the reference plan (14.1a). A
    narrower question's run always uses the plan its original's narrowing decision stored: that comes from the
    question's link to its original, never from the caller's flag (step 8b fix round, finding 1; the database
    refuses such a run without the flag, migration 0006). `ceiling`: stored on the run (step 9a, R5)."""
    ceiling = _ceiling(ceiling)
    actions.actor(by, via)
    setting_ids = {role: agent_settings.ensure_setting(engine, role) for role in agent_settings.RUN_ROLES}

    def body(conn: Connection):
        _lock_version(conn, version_id)
        _check_shown(conn, version_id, None, expected_fingerprint, via)
        _dispatch_checks(conn, version_id, constructed_test_data)
        conn.execute(text("UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v"),
                     dict(v=version_id))
        rid = _new_run(conn, version_id, fixed_plan, constructed_test_data, ceiling, setting_ids)
        actions.record(conn, "dispatch", by, via, version=version_id, run=rid)
        return rid

    return run_transaction(engine, body)


def spend_cap() -> Decimal:
    """The per-run cap, stored as the ceiling when none is given (owner, 2026-10-08: every run stores its ceiling)."""
    from hypocurate.pipeline.agents.spend import RUN_CAP_USD
    return RUN_CAP_USD


def _new_run(conn: Connection, version_id: int, fixed_plan: bool, constructed_test_data: bool,
             ceiling: Decimal | None, setting_ids: Mapping[str, int]) -> int:
    """The queued run of a dispatched version, with everything a run records at dispatch."""
    narrower = conn.execute(text("SELECT h.narrower_of_run_id IS NOT NULL FROM hypothesis_version hv JOIN "
                                 "hypothesis h ON h.id = hv.hypothesis_id WHERE hv.id = :v"),
                            dict(v=version_id)).scalar_one()
    flags = json.dumps({CONSTRUCTED_MARK: True} if constructed_test_data else {})
    rid = conn.execute(text("INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags, spending_ceiling) "
                            "VALUES (:v, :f, CAST(:x AS jsonb), :c) RETURNING id"),
                       dict(v=version_id, f=fixed_plan or narrower, x=flags,
                            c=ceiling if ceiling is not None else spend_cap())).scalar_one()
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


def dispatch_again(engine: Engine, number: str, *, ceiling: Decimal | None = None, by: str | None = None,
                   via: str = COMMAND_LINE, expected_version: int | None = None,
                   expected_fingerprint: str | None = None) -> int:
    """A new queued run of query `number`'s dispatched version, once no run of the query is open (PRD 8, 14.4). It
    records what the version's latest run recorded (fixed plan, test mark), and the ceiling only as given now."""
    ceiling = _ceiling(ceiling)
    actions.actor(by, via)
    with engine.connect() as conn:
        vid = conn.execute(text(
            "SELECT hv.id FROM hypothesis h JOIN hypothesis_version hv ON hv.hypothesis_id = h.id "
            "WHERE h.number = :n AND hv.status = 'dispatched' ORDER BY hv.version_number DESC LIMIT 1"),
            dict(n=number)).scalar_one_or_none()
    if vid is None:
        raise QueryRefused("not_dispatched", f"query {number} has no dispatched version to dispatch again")
    setting_ids = {role: agent_settings.ensure_setting(engine, role) for role in agent_settings.RUN_ROLES}

    def body(conn: Connection):
        _lock_version(conn, vid)
        _check_shown(conn, vid, expected_version, expected_fingerprint, via)
        if conn.execute(text("SELECT EXISTS (SELECT 1 FROM run r JOIN hypothesis_version hv ON hv.id = "
                             "r.hypothesis_version_id WHERE hv.hypothesis_id = (SELECT hypothesis_id FROM "
                             "hypothesis_version WHERE id = :v) AND r.status IN ('queued', 'waiting', 'running'))"),
                        dict(v=vid)).scalar_one():
            raise QueryRefused("already_open", REASONS["already_open"])
        last = conn.execute(text("SELECT fixed_plan, experiment_flags FROM run WHERE hypothesis_version_id = :v "
                                 "ORDER BY id DESC LIMIT 1"), dict(v=vid)).one()
        marked = isinstance(last.experiment_flags, dict) and last.experiment_flags.get(CONSTRUCTED_MARK) is True
        _dispatch_checks(conn, vid, marked)
        rid = _new_run(conn, vid, last.fixed_plan, marked, ceiling, setting_ids)
        actions.record(conn, "dispatch_again", by, via, version=vid, run=rid)
        return rid

    return run_transaction(engine, body)


def cancel(engine: Engine, run_id: int, by: str, *, via: str = COMMAND_LINE) -> str:
    """A named person cancels a queued or a waiting run (R3); returns the reason recorded. Refused for any other
    status (a started run cannot be cancelled in sprint 1)."""
    name = by.strip() if isinstance(by, str) else ""
    if not name or len(name) > REVIEWER_MAX:
        raise QueryRefused("name_required", f"a cancel names the person (1 to {REVIEWER_MAX} characters)")

    def body(conn: Connection):
        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
        if conn.execute(text("SELECT count(*) FROM run WHERE id = :r"), dict(r=run_id)).scalar_one() == 0:
            raise QueryRefused("unknown_run", f"no run {run_id}")
        status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id)).scalar_one()
        if status not in CANCELLED:
            raise QueryRefused("not_cancellable", f"run {run_id} is {status}; only a queued or a waiting run can be "
                                                  "cancelled (a started run cannot be cancelled in sprint 1)")
        reason = CANCELLED[status].format(by=name)
        conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"),
                     dict(f=reason, r=run_id))
        actions.record(conn, "cancel", name, via, run=run_id)  # the failure reason above is unchanged (owner)
        return reason

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
    """The narrower question of a run completed as partly sufficient, created as submitted (Q10). Step 9a: taken up
    again after a stop, it finishes what was begun (a draft left by a stop is submitted) and never creates a second
    one (the database allows one per run, 0007)."""
    with engine.connect() as conn:
        existing = conn.execute(text(
            "SELECT h.id, h.number, hv.id AS vid, hv.status FROM hypothesis h JOIN hypothesis_version hv ON "
            "hv.hypothesis_id = h.id WHERE h.narrower_of_run_id = :r ORDER BY hv.version_number LIMIT 1"),
            dict(r=original_run)).one_or_none()
    if existing is not None:
        if existing.status == "draft":
            submit(engine, existing.vid, via=CODE)
        return Query(existing.id, existing.number, existing.vid)
    with engine.connect() as conn:
        row = conn.execute(text(
            "SELECT hv.text, d.key AS domain, hv.sufficiency_option, hv.id AS vid FROM run r "
            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
            "JOIN domain d ON d.id = hv.confirmed_domain_id WHERE r.id = :r"), dict(r=original_run)).one()
        sources = list(conn.execute(text(
            "SELECT s.key FROM hypothesis_version_source hvs JOIN source s ON s.id = hvs.source_id "
            "WHERE hvs.hypothesis_version_id = :v ORDER BY s.key"), dict(v=row.vid)).scalars())
    q = create(engine, NARROWER_TEXT.format(original=row.text, scope=scope_in_words(narrower_scope)), sources,
               domain=row.domain, sufficiency=row.sufficiency_option, narrower_of_run=original_run, via=CODE)
    submit(engine, q.version_id, via=CODE)
    return q


CLAIM_MAX = 2000      # step 10b: the hypothesis text, as typed on the new-query page
NOTE_MAX = 2000       # the submitter's note to the reviewer
COMMENT_MAX = 2000    # the reviewer's comment when returning a query
WEBSITE = VIA_WEBSITE  # step 10b: a write from the website (`via`); its words are in WHERE_WORDS


def _claim_text(claim: str) -> str:
    text_ = (claim or "").strip()  # trimmed only: the claim's words are kept as written
    if not 1 <= len(text_) <= CLAIM_MAX:
        raise QueryRefused("claim_required", f"state the hypothesis (1 to {CLAIM_MAX} characters)")
    return text_


def _note_text(note: str | None) -> str | None:
    note = (note or "").strip()
    if len(note) > NOTE_MAX:
        raise QueryRefused("note_too_long", f"the note is at most {NOTE_MAX} characters")
    return note or None


def _version(conn: Connection, number: str):
    """The latest version of query `number`, locked."""
    row = conn.execute(text(
        "SELECT hv.id, hv.status, hv.version_number, h.id AS hypothesis_id, h.narrower_of_run_id FROM hypothesis h "
        "JOIN hypothesis_version hv ON hv.hypothesis_id = h.id WHERE h.number = :n ORDER BY hv.version_number DESC "
        "LIMIT 1"), dict(n=number)).one_or_none()
    if row is None:
        raise QueryRefused("unknown_query", f"no query {number}")
    _lock_version(conn, row.id)
    return row


def update_draft(engine: Engine, number: str, claim: str, sources: Iterable[str], domain: str, sufficiency: str,
                 note: str | None, *, by: str | None = None, via: str = COMMAND_LINE, submit: bool = False,
                 expected_version: int | None = None, expected_fingerprint: str | None = None) -> int:
    """Step 10b: a draft is edited in place (it was never submitted); its sources are replaced. Returns its id. Fix
    round 1: only the version shown, unchanged, is edited; with `submit`, it is submitted in the same transaction."""
    claim, note, sources = _claim_text(claim), _note_text(note), list(dict.fromkeys(sources))
    actions.actor(by, via)
    if not sources:
        raise QueryRefused("no_source", "a query chooses at least one source")

    def body(conn: Connection):
        v = _version(conn, number)
        _check_shown(conn, v.id, expected_version, expected_fingerprint, via)
        if v.status != "draft":
            raise QueryRefused("not_a_draft", f"query {number} is {v.status}; only a draft is edited in place")
        conn.execute(text("UPDATE hypothesis_version SET text = :t, domain_id = :d, sufficiency_option = :o, "
                          "note = :n WHERE id = :v"),
                     dict(t=claim, d=_domain_id(conn, domain), o=sufficiency, n=note, v=v.id))
        conn.execute(text("DELETE FROM hypothesis_version_source WHERE hypothesis_version_id = :v"), dict(v=v.id))
        for sid in _source_ids(conn, sources):
            conn.execute(text("INSERT INTO hypothesis_version_source VALUES (:v, :s)"), dict(v=v.id, s=sid))
        actions.record(conn, "edit", by, via, version=v.id)
        if submit:
            _submit_in(conn, v.id, by, via)
        return v.id

    return run_transaction(engine, body)


def new_version(engine: Engine, number: str, claim: str, sources: Iterable[str], domain: str, sufficiency: str,
                note: str | None, *, by: str | None = None, via: str = COMMAND_LINE, submit: bool = False,
                expected_version: int | None = None, expected_fingerprint: str | None = None) -> int:
    """Step 10b (PRD 9.2): editing a returned query creates its next version, a draft; earlier versions are kept
    unchanged. Returns the new version's id. Fix round 1: only from the returned version shown (so an old form
    never makes a second new version); with `submit`, submitted in the same transaction."""
    claim, note, sources = _claim_text(claim), _note_text(note), list(dict.fromkeys(sources))
    actions.actor(by, via)
    if not sources:
        raise QueryRefused("no_source", "a query chooses at least one source")

    def body(conn: Connection):
        v = _version(conn, number)
        _check_shown(conn, v.id, expected_version, expected_fingerprint, via)
        if v.status != "returned":
            raise QueryRefused("not_returned", f"query {number} is {v.status}; a new version follows a returned one")
        vid = conn.execute(text(
            "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id, sufficiency_option, note) "
            "VALUES (:h, :n, :t, :d, :o, :note) RETURNING id"),
            dict(h=v.hypothesis_id, n=v.version_number + 1, t=claim, d=_domain_id(conn, domain), o=sufficiency,
                 note=note)).scalar_one()
        for sid in _source_ids(conn, sources):
            conn.execute(text("INSERT INTO hypothesis_version_source VALUES (:v, :s)"), dict(v=vid, s=sid))
        actions.record(conn, "new_version", by, via, version=vid)
        if submit:
            _submit_in(conn, vid, by, via)
        return vid

    return run_transaction(engine, body)


def return_for_edits(engine: Engine, version_id: int, by: str, comment: str, *, via: str = COMMAND_LINE,
                     expected_fingerprint: str | None = None) -> None:
    """Step 10b (PRD 9.3): the reviewer returns a submitted version for edits, with a comment; it never changes again,
    and an edit is its next version."""
    if not isinstance(by, str) or not by.strip() or len(by.strip()) > REVIEWER_MAX:
        raise QueryRefused("reviewer_missing", f"the reviewer's name is required (at most {REVIEWER_MAX} characters)")
    comment = (comment or "").strip()
    if not 1 <= len(comment) <= COMMENT_MAX:
        raise QueryRefused("comment_required", f"say what to change (1 to {COMMENT_MAX} characters)")

    def body(conn: Connection):
        status = _lock_version(conn, version_id)
        _check_shown(conn, version_id, None, expected_fingerprint, via)
        if status != "submitted":
            raise QueryRefused("not_submitted", f"this version is {status}; only a submitted version is returned")
        conn.execute(text("UPDATE hypothesis_version SET status = 'returned', returned_at = now(), "
                          "review_comment = :c WHERE id = :v"),
                     dict(c=f"returned by {by.strip()}: {comment}", v=version_id))
        actions.record(conn, "return", by, via, version=version_id)

    run_transaction(engine, body)


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
