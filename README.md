# hypocurate

[![tests](https://github.com/kelawady/hypocurate/actions/workflows/tests.yml/badge.svg)](https://github.com/kelawady/hypocurate/actions/workflows/tests.yml)

HypoCurate takes a scientific hypothesis in words, searches registered data sources, and reports whether the data in the sources searched are sufficient, partly sufficient or insufficient to test it. The specification is [docs/PRD_sprint1.md](docs/PRD_sprint1.md); the rules for working on the code are in [CLAUDE.md](CLAUDE.md).

## Status

Build step 5 of 12 (PRD Section 15): the access layer. The skeleton of step 2 (one Docker image for the web service and the worker, Docker Compose, a health page, the shared login, the suite on GitHub at every push, locked dependencies, `render.yaml`), the tables of PRD Section 7 with the rules the database enforces and Alembic migrations applied before every deploy (step 3), the three sources registered as sealed versions, one adapter per source and "test connection" (step 4), the assumptions register and its page (step 4b), plus the access layer with its audit log and the file guard for pipeline processes (step 5). The pipeline, the agents and the screens come in later steps.

## Set up secrets (once)

```
cp .env.example .env     # then fill in every value; .env is never committed
```

`HYPOCURATE_PASSWORD` is the login password: at least 24 characters in production (the site refuses to start otherwise), 12 locally. Generate it, e.g. with a password manager or `python3 -c "import secrets; print(secrets.token_urlsafe(24))"` (32 random characters). `SESSION_SECRET` signs the session cookie (at least 32 characters): `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. `POSTGRES_PASSWORD` is for the local database container only. `DATABASE_URL` is needed only to run the suite outside Docker: `postgresql://hypocurate:<POSTGRES_PASSWORD>@localhost:5432/hypocurate`.

## Start the system locally

```
docker compose up --build         # database, web (http://localhost:8000) and worker
```

`/health` needs no login; every other page asks for the shared password. Compose publishes the web service on 127.0.0.1 only, because locally it is plain HTTP. Each service gets only the variables it needs; the worker never sees the login password or the session secret.

In this Codespace, Docker has a leftover firewall rule that blocks traffic between containers. After every Codespace restart, run once:

```
sudo iptables-legacy -I DOCKER-USER -j ACCEPT
```

## Sessions and the login

- A session is a signed cookie holding only `{"signed_in": true}`. It lasts 12 hours. There is no server-side session record.
- **To revoke access, rotate `SESSION_SECRET` together with the password.** Changing the password alone does not end existing sessions. On Render: set a new `HYPOCURATE_PASSWORD` and a new `SESSION_SECRET` on the web service, then redeploy. Every existing session ends.
- Logout clears the cookie in that browser only. A copied cookie keeps working until it expires or the secret is rotated. This is a known limitation of cookie-only sessions, stated in `tests/test_login.py`.
- Failed logins are counted. Every attempt is still checked against the password, and the correct password is never refused by the count, so nobody can lock the owner out. After 5 wrong attempts within 15 minutes, further wrong attempts receive 429 instead of 401 until the window passes. That is all the count does.
- The protection against guessing is a random password of at least 24 characters, generated as above. The configuration enforces the length, not the randomness.

## Run the test suite

The suite needs PostgreSQL; the database tests fail (they never skip) when it is not reachable.

In the same image as the deployed services (this is what GitHub runs at every push):

```
docker compose run --rm test
```

Or in the Codespace's virtual environment:

```
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements-dev.lock
.venv/bin/pip install --no-deps -e .
docker compose up -d db
set -a; . ./.env; set +a
.venv/bin/pytest
```

## Dependencies

Direct dependencies are listed in `pyproject.toml`. The exact versions, with hashes, are in `requirements.lock` (runtime) and `requirements-dev.lock` (runtime plus test tools). To change a dependency: edit `pyproject.toml`, then regenerate both locks with pip-tools:

```
.venv/bin/pip install pip-tools
.venv/bin/pip-compile --strip-extras --generate-hashes --allow-unsafe -o requirements.lock pyproject.toml
.venv/bin/pip-compile --strip-extras --generate-hashes --allow-unsafe --extra dev -o requirements-dev.lock pyproject.toml
```

## Deployment

`render.yaml` describes the Render web service, worker and PostgreSQL database. Render deploys a commit on `main` only after its GitHub checks pass (`autoDeployTrigger: checksPass`).

## Database migrations

The tables are created and changed only by Alembic migrations in `hypocurate/db/migrations/`. The tables and the rules the database enforces are described in `hypocurate/db/models.py`.

```
python -m hypocurate.db.migrate upgrade              # to the latest revision
python -m hypocurate.db.migrate current              # the database's revision
python -m hypocurate.db.migrate downgrade <revision> # drops tables and their data
```

- **On deploy.** Both Render services run `python -m hypocurate.db.migrate upgrade` as their pre-deploy command. It runs after the image is built and before the new version starts. An advisory lock makes the second service wait, after which it finds the schema at the latest revision. `/health` shows the database's revision and whether it is the latest. Locally, `docker compose up` runs the same command in a one-off `migrate` service before web and worker start.
- **If a migration fails.** The whole upgrade is one transaction, so PostgreSQL undoes all of it: no table and no revision change. The command exits non-zero, Render fails the deploy, and the previous version keeps running. Every migration must therefore stay inside that transaction (no `CREATE INDEX CONCURRENTLY`, no `autocommit_block`); a test checks this.
- **Every migration keeps working with the previous release's code** (add first, remove in a later release). Reverting a merge on `main` then deploys the old code safely on the newer schema.
- **Rolling back:**
  1. Preferred: a new migration that undoes the change, deployed the normal way.
  2. Code only: revert the merge on `main`.
  3. Schema: the owner runs `python -m hypocurate.db.migrate downgrade <revision> --confirm-data-loss` in the Render Shell of a service. **This drops tables and their data**; in production it refuses without the flag. Before it, check the backups: Render's point-in-time recovery reaches back 3 days on the Hobby workspace and restores into a *new* database, which costs money.
- **What the database enforces, and its limits.**
  - Triggers and CHECK constraints refuse, among others: editing a locked plan; changing a frozen dataset; freezing a primary set that leaves out an eligible record; updating or deleting a record; extracting before the rules lock; any curation once a run has ended; adding files to a sealed source version; and a verdict on a run that is not sufficient. A refusal raises an error starting `hypocurate:`.
  - **Locking protocol (all write paths, from step 4 on).** The lock order is version, then run, then the run's child rows.
    - Every transaction that will write to a run or its child rows first calls `SELECT hc_write_lock(p_run => <run id>)`.
    - Every transaction that will change a hypothesis version's chosen sources, submit it or dispatch it first calls `SELECT hc_write_lock(p_version => <version id>)`.
    - Paths that follow the protocol cannot deadlock with each other.
    - The triggers also lock the run (or version) before checking its state, which makes the checks race-free. They do not by themselves establish the lock order: an UPDATE of a child row locks that row before its trigger asks for the run lock. A path that skips the protocol can deadlock.
    - **On a reported deadlock (SQLSTATE `40P01`) or serialization failure (`40001`), retry the whole transaction.** PostgreSQL aborts one transaction and writes nothing from it.
    - A transaction holding a run's lock makes every other writer to that run wait, so keep such transactions short.
  - **After a run ends.** On a completed run only the commentary, the Commentator's stage and model calls, and artifacts may still be written; on a failed run only the audit log.
  - **Validity checks.** The CHECKs on `analysis_result` are necessary conditions on the stored counts, not the full validity rules of PRD 5.7. Those, and the agreement of the verdict with the pooled result, are computed and tested in step 7.
  - The triggers stop the application and ordinary edits. The database owner can still drop a trigger, so they are not tamper-proof; the fingerprints are the cross-check.
- **Tests never touch the database at `DATABASE_URL`.** They create scratch databases (`hypocurate_t_…`, from a template migrated once per session) and drop them afterwards. The database user must be allowed to create databases (the local and CI containers' user is).

## Data

| Path | What it is |
|---|---|
| `data/manifest.json` | Fingerprint (SHA-256), size, licence, origin and retrieval date of every frozen file |
| `data/sources/mpea/` | MPEA dataset (Borg et al. 2020), Apache-2.0 |
| `data/sources/tamu_fcc/` | Texas A&M FCC dataset (Mulukutla et al. 2026, Zenodo 10.5281/zenodo.22798856), MIT |
| `data/controlled_duplicates/` | Constructed extract for testing duplicate detection; see its README |

To check that the origins still serve the same bytes (needs network; never overwrites the frozen copies):

```
.venv/bin/python scripts/fetch_sources.py            # pinned GitHub files
.venv/bin/python scripts/fetch_sources.py --zenodo   # also the Zenodo archive (about 49 MB)
```

## Sources and adapters

The three sources (`mpea`, `tamu_fcc`, `controlled_duplicates`) are defined in `hypocurate/sources/versions.py`. Registering one stores the data files its adapter reads as a `source_version` and seals it. The files digest and identity are computed as the database computes them, and the database checks them again.

```
hypocurate sources register              # all three; registering again changes nothing
hypocurate sources test tamu_fcc -n 3    # the first 3 records, in the common record format, as JSON
```

- Registration reads only paths inside `data/` (checked after resolving `..` and links), and refuses a file whose SHA-256 differs from `data/manifest.json`, or a source already registered with different interpretation settings.
- Registration writes no run or hypothesis version, so `hc_write_lock` does not apply. It locks the source row first (`SELECT … FOR UPDATE`) and runs in `run_transaction` (`hypocurate/db/retry.py`), which retries the whole transaction on `40P01` and `40001`.
- An adapter reads a **sealed** version (`load_sealed_version` re-checks every file's bytes against the seal) and returns one record per data row in the format of `hypocurate/sources/record.py`. Every value is kept as reported, with its unit. Every harmonized value has a status: `converted`, `not_reported`, `not_convertible` (with the reason) or `assigned` (with the passage of the source's documentation that states it). Adapters never decide eligibility and never drop or correct a record.
- A paper's group key is derived from its DOI (whitespace trimmed, a URL or `doi:` wrapper removed, ASCII case-folded); the DOI itself is kept as reported.
- The alloy label (0.1 at.% rounding) is for display only. Records carry the full-precision composition; when two compositions count as the same alloy is a plan setting (step 6).
- A CSV file with a quoting error or a row of the wrong length is refused as a whole, with the file, line and reason; no partial extraction is returned.
- "Test connection" runs in a read-only transaction.
- The controlled duplicate extract is registered with `enabled = false`: it is constructed test data.
- Not yet run on the live database: registering there is a later step and needs the owner.

## Access layer

Every agent reads data only through an access object built for its role, its stage and one run (`hypocurate/access/`; PRD 4). There is no agent yet (step 8).

```python
from hypocurate.access import Access, AccessDenied, role_input
critic = Access(engine, run_id, "critic", "curation")
critic.get("flags_kind")        # kind, category and record ids; never the numbers compared
role_input(critic)              # everything the Critic may receive at this stage
```

- **Allowed fields, not blocked fields.** `hypocurate/access/allowlist.py` lists the fields each role may receive at each stage; anything else raises `AccessDenied`. Each field is built from named keys only (`fields.py`). Every field reads only the run's own rows.
- **Stages come from the database**, on every call: before the rules lock, curation, analysis (after the freeze), closed without a freeze (gap report), final (completed after a freeze) and final without a freeze (completed with none; the Commentator then gets only the gap-report input, the Analyst's gap report and the run's outcome). Queued and failed runs give nothing.
- **Every read and every refusal is logged** in `audit_log` (role, stage, field, allowed or denied, and the reason; never a value). Each call is one `run_transaction` that calls `hc_write_lock(p_run => …)` first. A refusal is committed before `AccessDenied` is raised, so the row survives it. Never call the access layer while holding the same run's lock: the call would wait, and fails after 5 seconds.
- **Pipeline runs execute in a guarded process.** `run_guarded("hypocurate.<module>:<function>", payload)` starts `python -m hypocurate.access.guarded`, which installs an irreversible audit hook: it may read only the Python installation and the package's code, and write only in a private scratch directory (`TMPDIR`, `MPLCONFIGDIR` and `XDG_CACHE_HOME` point at it). `tests/`, `docs/`, `data/` and the repository root cannot be read or listed; other programs and `ctypes` are refused. Source data reach pipeline code only as the sealed bytes of the run's source versions, through the access layer. Source registration refuses to run in that process. The web service, the migrations, the `sources` commands and the tests are not guarded. The hook sees what Python code opens, not what C libraries open themselves; it is not an operating-system sandbox.
