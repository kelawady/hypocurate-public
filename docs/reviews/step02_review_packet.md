# Build step 2 — review packet for the second model

Date: 2026-10-04. Branch: `step-02-skeleton`. Code reviewed: commit `1249081` (this packet is added in the next commit and changes no code). GitHub Actions on commit `f937baa`, the last code change: success, https://github.com/kelawady/hypocurate/actions/runs/37237773121.

Generated from the files on disk by a script, so every file below is quoted exactly. The lock files are shown without their hash lines, which are long; the full files are in the repository.

## How to use this packet

You are reviewing build step 2 of HypoCurate (PRD Section 15): the skeleton. It includes:
- the repository layout;
- one Docker image for the web service and the worker;
- Docker Compose;
- a health page;
- the single shared login with a failed-login limit;
- the regression suite on GitHub Actions;
- locked dependencies;
- `render.yaml`.

Your review is advice; the test suite is the gate. Please return a dated findings file. Each finding will be accepted (and fixed with a regression test) or rejected with a one-line reason.

Use the fixed checklist in section 2, answering each item yes, no or not applicable to this change, with a reason for every "no". For this step the most relevant items are **Secrets** and **Data and tests**, and the "access" item about which files pipeline code can read. Beyond the checklist, please look at:
- the login and session handling (cookie flags, signing, the lockout, redirects for unauthenticated paths);
- whether `/health`, the logs, the image or committed files can expose a secret;
- whether `render.yaml` really deploys only after the GitHub checks pass;
- whether the deployed image keeps `tests/` and `docs/reviews/` out;
- whether anything was built ahead of step 2.

## Contents

1. Step summary
2. Reviewer checklist
3. Application code (full text)
4. Tests (full text)
5. Containers, deployment and CI (full text)
6. Dependencies
7. README
8. Test output

## 1. Step summary

### `docs/reviews/step02_summary.md`

SHA-256 `7fbdf38ee9c179b7d3cc3d85149551a3df130da36eabcb40ba8912043c8926b4`, 12944 bytes.

````markdown
# Build step 2 — summary for review

Date: 2026-10-04. Branch: `step-02-skeleton`. **Status: built and green on GitHub; awaiting the second-model review and the owner's sign-off.** PRD Section 15, step 2: "Skeleton. Repository, Docker image, Docker Compose with web, worker and database, a health page, login, and the regression suite running automatically on GitHub."

The suite is the gate. This summary is for the second-model review (PRD 13.2), which uses `docs/reviews/checklist.md`; this is the checklist's first use.

## What was built

| Path | What it is |
|---|---|
| `hypocurate/pipeline/`, `access/`, `db/`, `web/` (`__init__.py`) | PRD 6.1 layout. `pipeline` and `access` hold a docstring only. |
| `hypocurate/config.py` | Settings from environment variables. `DATABASE_URL` is always required. The web service also requires `HYPOCURATE_PASSWORD` (≥ 12 characters) and `SESSION_SECRET` (≥ 32 characters), in every environment, not only production; the worker and command line do not get them. Error messages name the setting, never its value. The secrets are hidden from `repr`. |
| `hypocurate/db/engine.py` | SQLAlchemy engine (psycopg 3) and `database_reachable` (`SELECT 1`, never raises). **No tables, no Alembic.** Login uses a signed cookie and health uses `SELECT 1`, so neither needs a table. |
| `hypocurate/web/app.py`, `main.py`, `templates/`, `static/style.css` | The web service: `GET/POST /login`, `POST /logout`, `GET /health`, and a placeholder `/` page ("signed in"). Every path except `/login`, `/health` and `/static/` redirects to `/login` without a session, including FastAPI's `/docs`, `/redoc` and `/openapi.json`, which are switched off. The password is compared with `hmac.compare_digest`. The session is Starlette's `SessionMiddleware`: an itsdangerous-signed cookie `hypocurate_session`, 12-hour max age, `SameSite=Lax`, `HttpOnly`, and `Secure` in production. |
| `hypocurate/web/login_limit.py` | Failed-login limit, in memory (owner's addition). After 5 failures within 15 minutes, every login is refused with 429 for 5 minutes, even with the right password. A success clears the count; a restart clears everything. The limit is global, not per IP, because behind Render's proxy the client address can be spoofed. The web service runs one process (`--workers 1`), so the count is shared. |
| `/health` | Public. Reports `web`, `database` (`ok` / `unreachable`) and `version` (Render's `RENDER_GIT_COMMIT`, else `unknown`). JSON by default, or an HTML page for a browser. Returns 503 when the database does not answer. No data and no secrets. |
| `hypocurate/worker.py` | Idle loop (owner's decision): it checks the database, logs "worker idle: no pipeline yet; database reachable", and sleeps 60 s. No queue, heartbeat or pipeline; those are step 9. |
| `hypocurate/cli.py` | `hypocurate version` and `hypocurate check-db` only. |
| `pyproject.toml`, `requirements.lock`, `requirements-dev.lock` | Direct dependencies in `pyproject.toml`. Exact versions with SHA-256 hashes, generated by pip-tools 7.6.1. The images install with `--require-hashes`. This closes step 1 open item 7. |
| `Dockerfile` | `python:3.14-slim`, pinned by digest. **`runtime` stage** (web and worker): it copies only `requirements.lock`, `hypocurate/` and `data/`. `tests/` and `docs/` (including `docs/reviews/`), which hold expected answers, are not in the deployed image; I checked this by listing `/app` in the built image. It runs as a non-root user `app`. **`test` stage**: runtime plus the dev lock and the whole repository context, minus `.dockerignore`; runs `pytest -q`. |
| `.dockerignore` | `.git`, `.venv`, `.env`, caches, egg-info. |
| `docker-compose.yml` | `db` (postgres:17, pinned by digest, health check, named volume, port bound to 127.0.0.1), `web` (port 8000), `worker`, and `test` (profile `test`, the test image). Secrets come from `.env`. `POSTGRES_PASSWORD` is required (`${POSTGRES_PASSWORD:?}`). |
| `.env.example` | Names only: `HYPOCURATE_ENV`, `HYPOCURATE_PASSWORD`, `SESSION_SECRET`, `POSTGRES_PASSWORD`, `DATABASE_URL`. |
| `render.yaml` | Blueprint: web service, background worker, PostgreSQL 17, all in `oregon`.<br>• Plans are the cheapest paid (owner's decision): web `0.5c-512mb`, worker `0.5c-512mb`, database `0.1c-256mb`, which are Render's current names for the old starter and basic-256mb.<br>• `autoDeployTrigger: checksPass` on both services (owner's request).<br>• `DATABASE_URL` comes from the database's private-network `connectionString`.<br>• `SESSION_SECRET` has `generateValue: true`; `HYPOCURATE_PASSWORD` has `sync: false` and is entered by the owner in Render.<br>• The worker gets no login secrets.<br>• Database `ipAllowList: []` blocks all outside connections.<br>• Checked against render.com/docs/blueprint-spec and render.com/docs/deploys on 2026-10-04. Render does not allow `sync: false` in an environment group, so the variables are listed per service. |
| `.github/workflows/tests.yml` | Check `tests`, on every push (all branches, including `main`, which Render's `checksPass` waits for) and every pull request.<br>• Writes throwaway random secrets to `.env`, builds the images, and runs `docker compose run --rm test`.<br>• Then starts web, worker and database, and checks that `/health` reports the database `ok`, that `/` redirects to login (303), and that the worker is running.<br>• `actions/checkout` is pinned by commit (v7.0.1). Permissions are `contents: read`. |
| `tests/conftest.py` | `database_url` fixture. When PostgreSQL is not reachable it **fails, it never skips**, with instructions. |
| `README.md` | CI badge; secrets set-up; `docker compose up`; the Codespace firewall note; running the suite both ways; regenerating the locks; deployment. |

Not built, as instructed: tables, migrations, the access layer, agents, pipeline code, screens other than login and health.

### Python version (owner's condition)
Python 3.14 was chosen after checking that the libraries of later steps publish releases for it. On a wheels-only dry-run resolve on 3.14 (2026-10-04), all of these install:
- dspy 3.4.0 (`requires_python <3.15,>=3.10`);
- litellm 1.104.0 (`<3.15,>=3.10`);
- statsmodels 0.15.0 and scipy 1.18.1 (both with cp314 wheels);
- their native dependencies: numpy 2.5.3, tiktoken 0.14.0, tokenizers 0.23.2.

They are not added to the lock now because nothing uses them yet. They will be added in steps 7–8. The Codespace also runs 3.14.2.

### Other choices made while building
- The web service requires its secrets in development too, not only in production as the plan said. This is stricter, so a missing `.env` can never start an unprotected site.
- The test client is `httpx2`, which Starlette recommends in place of `httpx` (it gave a deprecation warning).
- pyyaml is a dev dependency only, for reading `render.yaml`, Compose and the workflow in tests.

## Tests (151, all passing; 58 new, the 93 from step 1 unchanged)

`git diff main -- tests/test_frozen_sources.py tests/test_controlled_duplicates.py tests/fixtures data` is empty.

`tests/test_login.py` (21):
- without a session, `/` and any other path redirect to `/login`; the API docs are not exposed; `/login` and `/static` are public;
- a wrong or empty password gives 401 and no session; the right one gives a session; logout ends it;
- a tampered cookie, and a cookie signed with a different secret, are rejected;
- in production the cookie is `Secure`, `HttpOnly` and `SameSite=Lax`;
- the password appears in no cookie or page;
- after 5 failures even the right password gets 429 and no session;
- settings: the web service refuses to start without each secret (3 cases), or with short ones; error messages and `repr` never contain values; the worker needs no login secrets; an unknown `HYPOCURATE_ENV` is refused.

`tests/test_login_limit.py` (5):
- the approved defaults (5 / 15 min / 5 min);
- locked after 5 failures and not before;
- unlocked after the lockout;
- failures outside the window do not count;
- a success resets the count.

`tests/test_health.py` (7, against real PostgreSQL):
- `/health` works without login, with JSON and HTML, database `ok`;
- an unreachable database gives 503 and `unreachable`, without crashing;
- no secret and no database URL appear in the response;
- the worker idles, checks the database and logs each cycle;
- an unreachable database is logged without the URL's password;
- `check-db` returns 0 or 1 as appropriate.

`tests/test_skeleton.py` (25):
- PRD 6.1 paths exist;
- `.env.example` holds exactly the expected names, with no values;
- `.env` is in `.gitignore` and `.dockerignore`;
- no API key, token or database URL with a password appears in any text file;
- **planted-value style:** the secret values in the suite's own environment (random ones in CI and Docker) appear in no file;
- every lock line is pinned with hashes; direct dependencies are locked; the runtime and dev locks agree; test tools are not in the runtime lock;
- base images are pinned by digest; the runtime image copies only the lock, `hypocurate/` and `data/`; both installs use `--require-hashes`; both stages run as non-root; the web service runs one process;
- Compose has db, web, worker and test, and takes secrets from `.env` only;
- `render.yaml`: web, worker and database; the approved plans; `checksPass` on every service with branch `main`; one region and a private database; no secret values; the worker gets no login secrets;
- CI runs the whole suite on every push and pull request and checks `/health`; actions are pinned by commit; the test image runs plain `pytest -q` with no filter.

### Suite results
```
$ .venv/bin/pytest -q                    (Codespace, Python 3.14.2, with `docker compose up -d db`)
151 passed in 1.68s
$ docker compose run --rm test           (the test image)
151 passed in 2.49s
GitHub Actions, commit f937baa:          151 passed; health, login redirect and worker checks passed
https://github.com/kelawady/hypocurate/actions/runs/37237773121   (conclusion: success)
```

Local smoke test (`docker compose up`): `/health` → `{"web":"ok","database":"ok","version":"unknown"}`; `/` → 303 to `/login`; wrong password → 401; right password → 303 and then "Signed in"; worker log "no pipeline yet; database reachable".

## Deviations from the PRD and the approved plan
1. **Render is connected at the end of this step, not at step 11** (owner's decision, 2026-10-04), so that every later step is verified on the live site. Order: review and sign-off → branch green → merge `--no-ff` → `main` green → Render actions one at a time, with prices confirmed first, until `/health` and `/login` work on the Render address. The live check will be added to this summary.
2. **Dev container (PRD 16) is deferred** (owner's decision). Proposed backlog item. Running the suite in the deployed image (`docker compose run --rm test`, and on GitHub) gives the match with Render meanwhile. The PRD itself is not edited.
3. **Merge gate:** the repository is private on a free GitHub plan, so GitHub cannot require the check before a merge. By process, I confirm that the branch run is green and record its link before every merge (owner's decision). Render's `checksPass` keeps a failing `main` from deploying.

## Codespace finding (not a project change)
In this Codespace, Docker has a leftover `iptables-legacy` FORWARD chain with policy DROP, which blocks traffic between containers on Compose networks. With the owner's approval I ran `sudo iptables-legacy -I DOCKER-USER -j ACCEPT`. It is lost on restart; the README has the command. GitHub's runners and Render are not affected.

## Open items
1. **Region.** `render.yaml` uses `oregon` for all three resources; it cannot be changed after creation. Confirm, or choose another region, before connecting Render.
2. **Prices.** Confirm Render's current prices for the three plans on render.com before the first paid action.
3. **Login limit trade-off.** It is global, so anyone's failures can lock the owner out for 5 minutes. It is cleared on restart and does not survive a second web process; the image and test pin `--workers 1`.
4. **Pipeline code can still read `tests/` and `docs/reviews/` in development.** The deployed image does not contain them, but the step 5 access layer must still enforce the approved file list (step 1 open item 4).
5. Carried from step 1, unchanged: the pooled p-value 7.4e-7 against "≈ 8e-7" (before step 7); permitted test types and a non-MPEA survivor pair (step 6).
6. `docs/reviews/checklist.md` is used for the first time in this review and may be amended afterwards, with owner approval.

## Questions for the reviewer
- Is a global (not per-IP) failed-login limit acceptable for a single shared password behind Render's proxy?
- Is anything secret reachable from `/health`, the logs, the image or the committed files?
- Are there untested paths in the login and session handling?
````

## 2. Reviewer checklist

### `docs/reviews/checklist.md`

SHA-256 `93df5256230e9a3ed2089d0b0ed73c7af3d4bead77a4dbe084b72ffb91806ddb`, 6341 bytes.

```markdown
# Second-model review checklist

**Status: approved by the owner as a working draft, 2026-10-04.** Drafted from PRD Section 13.2 and the rules in `CLAUDE.md`. This is the fixed checklist given to the reviewer at every review. It may be amended after its first use in step 2; any amendment needs the owner's approval.

## When a review is required (PRD 13.2)
- At the end of each build step in PRD Section 15.
- Whenever a change touches a safeguard: the access rules, the plan lock, the inclusion and eligibility rules, or the statistics. Any change to a safeguard also needs the owner's approval, however small.

## What the reviewer is given
1. The changes since the last review: a review packet with the full text of every changed code, test and script file, and the test output.
2. The core rules:
   - the access contract (PRD 4);
   - the plan lock and dataset freeze (PRD 5.6);
   - "stored is not the same as analysed" (PRD 5.3);
   - "a narrower question is a separate record" (PRD 5.4).
3. This checklist.

## Minimum questions (PRD 13.2, verbatim)
1. Can any role reach outcome values it should not see?
2. Can anything change after the lock?
3. Are records ever dropped or overwritten in the store?
4. Do the eligibility rules match Section 5.3?
5. Are the statistics what the plan states?
6. Are there untested paths?
7. Are secrets or keys exposed?

## Rule-by-rule checks
Answer each with yes, no or not applicable to this change. Give a reason for every "no".

**Who decides**
- [ ] Code alone sets inclusion, flags, the choice of test, data sufficiency and the verdict. No language model output can set any of them. (CLAUDE.md rule 1)

**Access contract (PRD 4)**
- [ ] Every agent reads data only through the access layer, using a per-role, per-stage allow-list of fields. Is anything not on the list withheld?
- [ ] A disallowed call raises `AccessDenied` and writes an audit-log row.
- [ ] Outcome values cannot leak through any of these:
  - flag numbers;
  - values as originally reported;
  - nested fields;
  - text handed between stages.
- [ ] The tests cover a role's **complete** input: prompt, every tool response and handed-over text. Do they include the planted-value test for the Planner and the Critic?
- [ ] Pipeline code reads input files only from an explicit list of approved files. Are `tests/` and `docs/reviews/`, which hold expected answers, outside that list? Directory placement alone is a convention, not enforcement.
- [ ] The Curator is not told the direction of the claim.
- [ ] The Critic gets the kind of each flag, never the numbers.

**Checkpoints (PRD 5.6)**
- [ ] Rules lock before curation fixes all of these, with a fingerprint and a time:
  - the model;
  - scope;
  - exclusion rules;
  - eligibility rules;
  - the data-sufficiency option;
  - sensitivity analyses.
- [ ] Dataset freeze before analysis fixes the record sets, with a fingerprint and a time.
- [ ] After each checkpoint, nothing changes, by agent or by person. Is every attempt rejected and logged?
- [ ] A later removal appears only as a labelled sensitivity analysis and never changes the verdict.

**Stored is not analysed (PRD 5.3)**
- [ ] Every record found is kept. Nothing is deleted or overwritten in place.
- [ ] Eligibility is decided by code under the locked rules. Do the defaults match the PRD 5.3 table?
- [ ] Duplicates require all of these: the same original paper, alloy, grain size, value and test conditions. Is matching alloy and grain size alone kept from counting?
- [ ] The survivor of a duplicate pair follows the owner's rule:
  1. the record that comes directly from the original paper (detected by its DOI);
  2. then the fixed source order MPEA, Texas A&M, controlled extract;
  3. then the lowest row.
- [ ] Conflicting records are preserved, not automatically pooled.
- [ ] Physical checks never use the relationship under test.
- [ ] Model-recalled data are never pooled and never count toward a verdict.

**Statistics (PRD 5.7, 5.8, 5.10)**
- [ ] Only the one supported model is used:
  - OLS with alloy intercepts;
  - k × d^-1/2;
  - cluster-robust standard errors by paper, with the small-sample correction;
  - a one-sided test of k > 0 at 0.05, against t with (groups − 1) degrees of freedom;
  - only alloys with at least 2 distinct grain sizes.
- [ ] Both validity checks are applied to every analysis and can never be waived:
  1. Can a coefficient be fitted?
  2. Are there at least 1 residual degree of freedom and at least 2 groups?
  
  If check 2 fails, is only the coefficient reported?
- [ ] Data sufficiency is the option fixed at rules lock. Does "use what is available" waive only the threshold, and label the result exploratory?
- [ ] Calibration is a flag, not a gate. Is "calibration unavailable" shown with its reason when inference cannot run?
- [ ] Do the reference numbers still reproduce within the stated tolerances, with no tolerance widened?

**Outcomes and wording**
- [ ] A narrower question is a separate, linked record. Does the original get no verdict? (PRD 5.4)
- [ ] Are the three kinds of "nothing found" kept distinct: reported negative, missing evidence, failed search? (PRD 3.1)
- [ ] Are outcomes stated "in the sources searched"? Is it never claimed that data "do not exist"?

**Cost (PRD 8)**
- [ ] Is every model call recorded with tokens and actual cost (`model_call`)?
- [ ] Are the caps enforced: $2 per run, $50 per month?

**Data and tests**
- [ ] Do frozen files match their pinned fingerprints, with the manifest's own fingerprint and the list of required files pinned in the tests? (PRD 10, 15)
- [ ] Has no test been weakened, skipped or deleted, and no tolerance widened?
- [ ] Are new paths covered by tests?
- [ ] Has nothing been built ahead of the current step, and nothing from the backlog (PRD 18)?

**Secrets**
- [ ] Are there no keys, database URLs or passwords in code, tests, logs or committed files? Does `.env.example` hold names only?

## What comes back (PRD 13.2)
- A dated findings file in `docs/reviews/`.
- Each finding is either accepted, which means a fix plus a regression test, or rejected with a one-line reason in the same file.
- **Authority:** the reviewer advises; the test suite is the gate. A review cannot approve a change that fails the suite. A finding is acted on only after the owner accepts it.
```

## Files added or changed since `main` (step 1 merge)

| Status | Path |
|---|---|
| A | `.dockerignore` |
| A | `.env.example` |
| A | `.github/workflows/tests.yml` |
| A | `Dockerfile` |
| M | `README.md` |
| A | `docker-compose.yml` |
| A | `docs/reviews/step02_summary.md` |
| A | `hypocurate/access/__init__.py` |
| A | `hypocurate/cli.py` |
| A | `hypocurate/config.py` |
| A | `hypocurate/db/__init__.py` |
| A | `hypocurate/db/engine.py` |
| A | `hypocurate/pipeline/__init__.py` |
| A | `hypocurate/web/__init__.py` |
| A | `hypocurate/web/app.py` |
| A | `hypocurate/web/login_limit.py` |
| A | `hypocurate/web/main.py` |
| A | `hypocurate/web/static/style.css` |
| A | `hypocurate/web/templates/base.html` |
| A | `hypocurate/web/templates/health.html` |
| A | `hypocurate/web/templates/home.html` |
| A | `hypocurate/web/templates/login.html` |
| A | `hypocurate/worker.py` |
| M | `pyproject.toml` |
| A | `render.yaml` |
| A | `requirements-dev.lock` |
| A | `requirements.lock` |
| A | `tests/conftest.py` |
| A | `tests/test_health.py` |
| A | `tests/test_login.py` |
| A | `tests/test_login_limit.py` |
| A | `tests/test_skeleton.py` |

## 3. Application code

### `hypocurate/access/__init__.py`

SHA-256 `5e3404ed3f60d4fbc29628af658ac5216cce931e25bcc2bbdfe00009633e543d`, 91 bytes.

```python
"""The data-access layer: role and stage objects, the audit log, AccessDenied (step 5)."""
```

### `hypocurate/cli.py`

SHA-256 `ea3a5c3f65e5c49e9051ff06aa3946a48d2200c56211fabfcb50fbcf919d45d4`, 958 bytes.

```python
"""The command-line entry point (PRD Section 12). Step 2: `version` and `check-db` only."""
from __future__ import annotations

import argparse
import sys

from hypocurate.config import load_settings
from hypocurate.db.engine import database_reachable, make_engine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="hypocurate")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version", help="print the deployed version")
    sub.add_parser("check-db", help="check that the database answers")
    args = parser.parse_args(argv)

    settings = load_settings(web=False)
    if args.command == "version":
        print(settings.version)
        return 0
    reachable = database_reachable(make_engine(settings.database_url))
    print("database reachable" if reachable else "database NOT reachable")
    return 0 if reachable else 1


if __name__ == "__main__":
    sys.exit(main())
```

### `hypocurate/config.py`

SHA-256 `f4ffc24ea901dc12551e36c848c9ccab2b0c315043ba8ca1f34a78d95748a6db`, 2320 bytes.

```python
"""Settings from environment variables (PRD Section 6, "Login"; CLAUDE.md, "Secrets").

Secrets come only from the environment (`.env` locally, Render's environment
settings in production). Their values are never logged or shown; `Settings`
hides them from its repr.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

PRODUCTION = "production"
DEVELOPMENT = "development"
MIN_PASSWORD_LENGTH = 12
MIN_SESSION_SECRET_LENGTH = 32


class ConfigError(RuntimeError):
    """A required setting is missing or unsafe. The message names the setting, never its value."""


@dataclass(frozen=True)
class Settings:
    env: str
    database_url: str = field(repr=False)
    password: str = field(repr=False)
    session_secret: str = field(repr=False)
    version: str

    @property
    def production(self) -> bool:
        return self.env == PRODUCTION


def load_settings(environ: dict[str, str] | None = None, *, web: bool = True) -> Settings:
    """Read and check the settings.

    The database URL is always required. The login password and the session
    secret are required, and must be long enough, for the web service
    (`web=True`); the worker and the command line do not use them.
    """
    e = os.environ if environ is None else environ
    env = e.get("HYPOCURATE_ENV", DEVELOPMENT)
    if env not in (PRODUCTION, DEVELOPMENT):
        raise ConfigError(f"HYPOCURATE_ENV must be '{PRODUCTION}' or '{DEVELOPMENT}'")
    settings = Settings(
        env=env,
        database_url=e.get("DATABASE_URL", ""),
        password=e.get("HYPOCURATE_PASSWORD", ""),
        session_secret=e.get("SESSION_SECRET", ""),
        # Render sets RENDER_GIT_COMMIT; elsewhere the version is unknown.
        version=e.get("RENDER_GIT_COMMIT", "") or "unknown",
    )
    problems = []
    if not settings.database_url:
        problems.append("DATABASE_URL is not set")
    if web and len(settings.password) < MIN_PASSWORD_LENGTH:
        problems.append(f"HYPOCURATE_PASSWORD must be at least {MIN_PASSWORD_LENGTH} characters")
    if web and len(settings.session_secret) < MIN_SESSION_SECRET_LENGTH:
        problems.append(f"SESSION_SECRET must be at least {MIN_SESSION_SECRET_LENGTH} characters")
    if problems:
        raise ConfigError("; ".join(problems))
    return settings
```

### `hypocurate/db/__init__.py`

SHA-256 `92b6de6449152671e15518b9a31ad5aabf282a6229fc31135ead780859d0a48e`, 67 bytes.

```python
"""Database connection; models and migrations arrive in step 3."""
```

### `hypocurate/db/engine.py`

SHA-256 `3b7a2c30c4f76216aeec979fa2b7edabb63c4e48919915d66a4c346fc9ad5be2`, 872 bytes.

```python
"""The database engine. Step 2 creates no tables: login uses a signed cookie and
the health page only asks whether the database answers."""
from __future__ import annotations

from sqlalchemy import Engine, create_engine, text


def make_engine(database_url: str) -> Engine:
    # Render and Docker give "postgresql://"; SQLAlchemy needs the psycopg 3 driver named.
    if database_url.startswith("postgresql://"):
        database_url = "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    return create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})


def database_reachable(engine: Engine) -> bool:
    """True if the database answers `SELECT 1`. Never raises."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

### `hypocurate/pipeline/__init__.py`

SHA-256 `652d98a6813608cb0ce6d91e208f33cd526bce6a74d13a369b0d7350dcd0bd3c`, 107 bytes.

```python
"""The pipeline: orchestrator, agent roles, plan, inclusion, checks, statistics, reports (from step 6)."""
```

### `hypocurate/web/__init__.py`

SHA-256 `e8494ff984141ed29d35a18853f004cc747d39cb2a086a20495a2e801f9190d2`, 63 bytes.

```python
"""The website: FastAPI routes, templates and static files."""
```

### `hypocurate/web/app.py`

SHA-256 `462bf1595f2fb1e471b0d3bfe34993d419cf7b1368ddd996a87c87d3a21f42b0`, 3895 bytes.

```python
"""The web service (PRD Section 6): login, health page, and a placeholder home page.

Every page needs the shared login except /login, /health and /static. The
session is a signed cookie (Starlette SessionMiddleware, itsdangerous); in
production it is sent over HTTPS only.
"""
from __future__ import annotations

import hmac
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Engine
from starlette.middleware.sessions import SessionMiddleware

from hypocurate.config import Settings, load_settings
from hypocurate.db.engine import database_reachable, make_engine
from hypocurate.web.login_limit import LoginLimit

HERE = Path(__file__).resolve().parent
SESSION_COOKIE = "hypocurate_session"
SESSION_MAX_AGE = 12 * 60 * 60
PUBLIC_PREFIXES = ("/login", "/health", "/static/")

templates = Jinja2Templates(directory=HERE / "templates")


def create_app(
    settings: Settings | None = None,
    engine: Engine | None = None,
    login_limit: LoginLimit | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    engine = engine or make_engine(settings.database_url)
    limit = login_limit or LoginLimit()

    app = FastAPI(title="HypoCurate", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def require_login(request: Request, call_next):
        path = request.url.path
        if not path.startswith(PUBLIC_PREFIXES) and not request.session.get("signed_in"):
            return RedirectResponse("/login", status_code=303)
        return await call_next(request)

    # Added after require_login so that it runs first and the session is available.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie=SESSION_COOKIE,
        max_age=SESSION_MAX_AGE,
        same_site="lax",
        https_only=settings.production,
    )
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return templates.TemplateResponse(request, "home.html", {})

    @app.get("/login", response_class=HTMLResponse)
    def login_form(request: Request):
        return templates.TemplateResponse(request, "login.html", {"error": None})

    @app.post("/login")
    def login(request: Request, password: str = Form("")) -> Response:
        if limit.seconds_locked() > 0:
            return templates.TemplateResponse(
                request, "login.html",
                {"error": "Too many failed attempts. Try again in a few minutes."},
                status_code=429,
            )
        if hmac.compare_digest(password.encode(), settings.password.encode()):
            limit.record_success()
            request.session.clear()
            request.session["signed_in"] = True
            return RedirectResponse("/", status_code=303)
        limit.record_failure()
        return templates.TemplateResponse(
            request, "login.html", {"error": "Wrong password."}, status_code=401
        )

    @app.post("/logout")
    def logout(request: Request) -> Response:
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    @app.get("/health")
    def health(request: Request) -> Response:
        db_ok = database_reachable(engine)
        status = {"web": "ok", "database": "ok" if db_ok else "unreachable", "version": settings.version}
        code = 200 if db_ok else 503
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(request, "health.html", {"status": status}, status_code=code)
        return JSONResponse(status, status_code=code)

    return app
```

### `hypocurate/web/login_limit.py`

SHA-256 `4b13a659bde175cbc9bf1fa896a3c5bca8cd2d9c78ff3722af44d903cfcbd6b7`, 1968 bytes.

```python
"""A simple limit on failed login attempts, kept in memory (no table).

After MAX_FAILURES failed attempts within WINDOW_SECONDS, every login attempt,
even with the right password, is refused for LOCKOUT_SECONDS. A successful
login clears the count; a restart clears everything.

The limit is global, not per client address: behind Render's proxy the client
address can be spoofed through X-Forwarded-For, and there is one shared
password. The web service runs one process, so the count is shared.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60
LOCKOUT_SECONDS = 5 * 60


class LoginLimit:
    def __init__(
        self,
        max_failures: int = MAX_FAILURES,
        window_seconds: float = WINDOW_SECONDS,
        lockout_seconds: float = LOCKOUT_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._clock = clock
        self._failures: deque[float] = deque()
        self._locked_until = 0.0
        self._lock = threading.Lock()

    def seconds_locked(self) -> float:
        """Seconds until login is allowed again; 0 when it is allowed now."""
        with self._lock:
            return max(0.0, self._locked_until - self._clock())

    def record_failure(self) -> None:
        with self._lock:
            now = self._clock()
            self._failures.append(now)
            while self._failures and self._failures[0] <= now - self.window_seconds:
                self._failures.popleft()
            if len(self._failures) >= self.max_failures:
                self._locked_until = now + self.lockout_seconds
                self._failures.clear()

    def record_success(self) -> None:
        with self._lock:
            self._failures.clear()
```

### `hypocurate/web/main.py`

SHA-256 `d003a0712c45a8af6a798b053895423a030a0d6febf945efbd44b4dad8c7e50e`, 156 bytes.

```python
"""The ASGI entry point: `uvicorn hypocurate.web.main:app`. Settings are read at start-up."""
from hypocurate.web.app import create_app

app = create_app()
```

### `hypocurate/web/static/style.css`

SHA-256 `bdc4e5e6d3f1c364633fbde625c1850e651794de844c1e363f9e74fa491f2e6d`, 958 bytes.

```css
:root { --fg: #1d2330; --muted: #5b6475; --bg: #ffffff; --line: #d8dde6; --accent: #2457c5; --bad: #b3261e; --good: #1f7a3a; }
* { box-sizing: border-box; }
body { margin: 0; font: 16px/1.5 system-ui, sans-serif; color: var(--fg); background: var(--bg); }
header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid var(--line); }
.brand { font-weight: 600; }
main { max-width: 32rem; margin: 2rem auto; padding: 0 16px; }
label { display: block; margin-bottom: 4px; }
input { width: 100%; padding: 8px; border: 1px solid var(--line); border-radius: 4px; font: inherit; }
button { margin-top: 12px; padding: 8px 16px; border: 0; border-radius: 4px; background: var(--accent); color: #fff; font: inherit; cursor: pointer; }
.logout button { margin: 0; }
.error { color: var(--bad); }
.ok { color: var(--good); }
th { text-align: left; padding-right: 16px; color: var(--muted); font-weight: 500; }
```

### `hypocurate/web/templates/base.html`

SHA-256 `85adff0ba9e735b8aab6d096c0f466e05d2a90bff97efe035e4891fef37d32e0`, 412 bytes.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}HypoCurate{% endblock %}</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header><span class="brand">HypoCurate</span>{% block nav %}{% endblock %}</header>
  <main>{% block content %}{% endblock %}</main>
</body>
</html>
```

### `hypocurate/web/templates/health.html`

SHA-256 `b2cb0a27678777d4b054d61980848f5835d38d8e1ee5d82eba7fcd4b741476fe`, 391 bytes.

```html
{% extends "base.html" %}
{% block title %}Health · HypoCurate{% endblock %}
{% block content %}
<h1>Health</h1>
<table>
  <tr><th>Web service</th><td>{{ status.web }}</td></tr>
  <tr><th>Database</th><td class="{{ 'ok' if status.database == 'ok' else 'error' }}">{{ status.database }}</td></tr>
  <tr><th>Version</th><td><code>{{ status.version }}</code></td></tr>
</table>
{% endblock %}
```

### `hypocurate/web/templates/home.html`

SHA-256 `ee5f60d9d08c4f30b41d58462dd4619b512cbd335c1da8d09547efd309c0e152`, 313 bytes.

```html
{% extends "base.html" %}
{% block nav %}<form method="post" action="/logout" class="logout"><button type="submit">Sign out</button></form>{% endblock %}
{% block content %}
<h1>Signed in</h1>
<p>The skeleton is running. The screens arrive in build step 10.</p>
<p><a href="/health">Health</a></p>
{% endblock %}
```

### `hypocurate/web/templates/login.html`

SHA-256 `00a94789f0e09ea161dca2063792c547aa0e68ab5b97c7da724dfa6419da320b`, 436 bytes.

```html
{% extends "base.html" %}
{% block title %}Sign in · HypoCurate{% endblock %}
{% block content %}
<h1>Sign in</h1>
{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
<form method="post" action="/login">
  <label for="password">Password</label>
  <input id="password" name="password" type="password" autocomplete="current-password" required autofocus>
  <button type="submit">Sign in</button>
</form>
{% endblock %}
```

### `hypocurate/worker.py`

SHA-256 `2d568ef2dbcd6c118ca80d84055b5c27e988ba94f15009213b2afd4576ffa12a`, 1021 bytes.

```python
"""The background worker (PRD Section 6).

Step 2: an idle loop. It checks that the database answers, logs, and sleeps.
The queue, heartbeat and pipeline arrive in step 9. Run with
`python -m hypocurate.worker`.
"""
from __future__ import annotations

import logging
import time

from hypocurate.config import load_settings
from hypocurate.db.engine import database_reachable, make_engine

log = logging.getLogger("hypocurate.worker")
IDLE_SECONDS = 60


def run(max_cycles: int | None = None, sleep=time.sleep) -> None:
    settings = load_settings(web=False)
    engine = make_engine(settings.database_url)
    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        reachable = database_reachable(engine)
        log.info("worker idle: no pipeline yet; database %s", "reachable" if reachable else "NOT reachable")
        cycles += 1
        sleep(IDLE_SECONDS)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    run()
```


## 4. Tests

### `tests/conftest.py`

SHA-256 `b9224decba97c9c232598acfb6f9ec6a63d09ae1014898bfba0f00890818d539`, 710 bytes.

```python
"""Shared fixtures. Tests that need PostgreSQL fail, never skip, when it is not reachable."""
import os

import pytest

from hypocurate.db.engine import database_reachable, make_engine

HOW_TO = (
    "This test needs PostgreSQL. Run the suite with `docker compose run --rm test`, "
    "or start the database with `docker compose up -d db` and set DATABASE_URL "
    "(see README)."
)


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        pytest.fail("DATABASE_URL is not set. " + HOW_TO)
    if not database_reachable(make_engine(url)):
        pytest.fail("The database at DATABASE_URL does not answer. " + HOW_TO)
    return url
```

### `tests/test_health.py`

SHA-256 `b7b4af617f569475ccc2ee16729f2e496dd87e09aa3616c197a254124a88d2e4`, 2730 bytes.

```python
"""Step 2: the health page, the idle worker and the command line against a real PostgreSQL."""
import logging

from fastapi.testclient import TestClient

from hypocurate import cli, worker
from hypocurate.config import Settings
from hypocurate.db.engine import make_engine
from hypocurate.web.app import create_app

PASSWORD = "test-password-not-a-secret"
SECRET = "s" * 40
UNREACHABLE_DB = "postgresql://nobody:planted-pw-7319@127.0.0.1:1/none"


def client(database_url):
    s = Settings(env="development", database_url=database_url, password=PASSWORD,
                 session_secret=SECRET, version="abc123")
    return TestClient(create_app(s, engine=make_engine(database_url)), follow_redirects=False)


def test_health_without_login_database_up(database_url):
    r = client(database_url).get("/health")
    assert r.status_code == 200
    assert r.json() == {"web": "ok", "database": "ok", "version": "abc123"}


def test_health_page_in_a_browser(database_url):
    r = client(database_url).get("/health", headers={"accept": "text/html"})
    assert r.status_code == 200
    assert "Database" in r.text and ">ok<" in r.text


def test_health_reports_database_down_without_crashing():
    r = client(UNREACHABLE_DB).get("/health")
    assert r.status_code == 503
    assert r.json()["database"] == "unreachable"


def test_health_shows_no_secrets(database_url):
    c = client(database_url)
    for accept in ["application/json", "text/html"]:
        text = c.get("/health", headers={"accept": accept}).text
        assert PASSWORD not in text and SECRET not in text
        assert database_url not in text and "postgresql" not in text


def test_worker_idles_and_checks_the_database(database_url, monkeypatch, caplog):
    monkeypatch.setenv("DATABASE_URL", database_url)
    sleeps = []
    with caplog.at_level(logging.INFO, logger="hypocurate.worker"):
        worker.run(max_cycles=2, sleep=sleeps.append)
    assert sleeps == [worker.IDLE_SECONDS] * 2
    assert caplog.text.count("no pipeline yet; database reachable") == 2


def test_worker_logs_an_unreachable_database(monkeypatch, caplog):
    monkeypatch.setenv("DATABASE_URL", UNREACHABLE_DB)
    with caplog.at_level(logging.INFO, logger="hypocurate.worker"):
        worker.run(max_cycles=1, sleep=lambda s: None)
    assert "database NOT reachable" in caplog.text
    assert "planted-pw-7319" not in caplog.text  # the URL's password is never logged


def test_cli_check_db(database_url, monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", database_url)
    assert cli.main(["check-db"]) == 0
    monkeypatch.setenv("DATABASE_URL", UNREACHABLE_DB)
    assert cli.main(["check-db"]) == 1
    assert "planted-pw-7319" not in capsys.readouterr().out
```

### `tests/test_login.py`

SHA-256 `53f50599457c2c9551af04d600d1a73253c365dc2746864b7a0ac4b91df7440e`, 5540 bytes.

```python
"""Step 2: the single shared login (PRD Section 6, "Login")."""
import pytest
from fastapi.testclient import TestClient

from hypocurate.config import ConfigError, Settings, load_settings
from hypocurate.db.engine import make_engine
from hypocurate.web.app import SESSION_COOKIE, create_app
from hypocurate.web.login_limit import MAX_FAILURES, LoginLimit

PASSWORD = "test-password-not-a-secret"
SECRET = "s" * 40
UNREACHABLE_DB = "postgresql://nobody:planted-pw-7319@127.0.0.1:1/none"


def settings(env="development"):
    return Settings(env=env, database_url=UNREACHABLE_DB, password=PASSWORD,
                    session_secret=SECRET, version="test")


def client(env="development", limit=None):
    s = settings(env)
    app = create_app(s, engine=make_engine(s.database_url), login_limit=limit)
    base = "https://testserver" if env == "production" else "http://testserver"
    return TestClient(app, base_url=base, follow_redirects=False)


def sign_in(c, password=PASSWORD):
    return c.post("/login", data={"password": password})


def test_pages_redirect_to_login_when_signed_out():
    c = client()
    for path in ["/", "/anything", "/runs/1"]:
        r = c.get(path)
        assert r.status_code == 303 and r.headers["location"] == "/login"


def test_login_page_and_static_are_public():
    c = client()
    assert c.get("/login").status_code == 200
    assert c.get("/static/style.css").status_code == 200


def test_no_api_docs_exposed():
    c = client()
    for path in ["/docs", "/redoc", "/openapi.json"]:
        assert c.get(path).status_code == 303


def test_wrong_password_is_refused_and_gives_no_session():
    c = client()
    r = sign_in(c, "wrong-password")
    assert r.status_code == 401
    assert SESSION_COOKIE not in r.cookies
    assert c.get("/").status_code == 303


def test_empty_password_is_refused():
    c = client()
    assert c.post("/login", data={}).status_code == 401


def test_right_password_gives_a_session():
    c = client()
    r = sign_in(c)
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert c.get("/").status_code == 200


def test_logout_ends_the_session():
    c = client()
    sign_in(c)
    r = c.post("/logout")
    assert r.status_code == 303 and r.headers["location"] == "/login"
    assert c.get("/").status_code == 303


def test_tampered_cookie_is_rejected():
    c = client()
    sign_in(c)
    value = c.cookies[SESSION_COOKIE]
    c.cookies.clear()
    c.cookies.set(SESSION_COOKIE, value[:-2] + ("AA" if value[-2:] != "AA" else "BB"))
    assert c.get("/").status_code == 303


def test_cookie_signed_with_another_secret_is_rejected():
    other = Settings(env="development", database_url=UNREACHABLE_DB, password=PASSWORD,
                     session_secret="o" * 40, version="test")
    forger = TestClient(create_app(other, engine=make_engine(UNREACHABLE_DB)), follow_redirects=False)
    sign_in(forger)
    c = client()
    c.cookies.set(SESSION_COOKIE, forger.cookies[SESSION_COOKIE])
    assert c.get("/").status_code == 303


def test_production_cookie_is_secure_httponly_lax():
    c = client("production")
    header = sign_in(c).headers["set-cookie"].lower()
    assert "secure" in header
    assert "httponly" in header
    assert "samesite=lax" in header


def test_password_is_not_in_the_cookie_or_pages():
    c = client()
    r = sign_in(c)
    assert PASSWORD not in r.headers.get("set-cookie", "")
    assert PASSWORD not in c.get("/").text
    assert PASSWORD not in c.get("/login").text


def test_lockout_after_failures_refuses_even_the_right_password():
    c = client(limit=LoginLimit())
    for _ in range(MAX_FAILURES):
        assert sign_in(c, "wrong-password").status_code == 401
    r = sign_in(c)
    assert r.status_code == 429
    assert SESSION_COOKIE not in r.cookies
    assert c.get("/").status_code == 303


# --- settings -------------------------------------------------------------------

GOOD = {"HYPOCURATE_ENV": "production", "DATABASE_URL": "postgresql://u:planted-pw-7319@h/d",
        "HYPOCURATE_PASSWORD": PASSWORD, "SESSION_SECRET": SECRET}


def test_settings_load_when_complete():
    assert load_settings(GOOD).production


@pytest.mark.parametrize("missing", ["DATABASE_URL", "HYPOCURATE_PASSWORD", "SESSION_SECRET"])
def test_web_refuses_to_start_without_a_secret(missing):
    env = {k: v for k, v in GOOD.items() if k != missing}
    with pytest.raises(ConfigError, match=missing):
        load_settings(env)


def test_web_refuses_short_secrets():
    with pytest.raises(ConfigError, match="HYPOCURATE_PASSWORD"):
        load_settings({**GOOD, "HYPOCURATE_PASSWORD": "short"})
    with pytest.raises(ConfigError, match="SESSION_SECRET"):
        load_settings({**GOOD, "SESSION_SECRET": "short"})


def test_config_errors_never_contain_values():
    env = {**GOOD, "HYPOCURATE_PASSWORD": "tiny-pw", "SESSION_SECRET": "tiny-secret"}
    with pytest.raises(ConfigError) as e:
        load_settings(env)
    assert "tiny-pw" not in str(e.value) and "tiny-secret" not in str(e.value)


def test_worker_needs_no_login_secrets():
    env = {"HYPOCURATE_ENV": "production", "DATABASE_URL": "postgresql://u:planted-pw-7319@h/d"}
    assert load_settings(env, web=False).password == ""


def test_unknown_env_is_refused():
    with pytest.raises(ConfigError):
        load_settings({**GOOD, "HYPOCURATE_ENV": "staging"})


def test_settings_repr_hides_secrets():
    text = repr(load_settings(GOOD))
    assert PASSWORD not in text and SECRET not in text and "planted-pw-7319" not in text
```

### `tests/test_login_limit.py`

SHA-256 `8f39765a84741b01b186df0b9b9d86075badb1edc2c7dbaa4cae0f1d389a2250`, 1557 bytes.

```python
"""Step 2: the in-memory limit on failed login attempts."""
from hypocurate.web.login_limit import LOCKOUT_SECONDS, MAX_FAILURES, WINDOW_SECONDS, LoginLimit


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_defaults_are_as_approved():
    assert (MAX_FAILURES, WINDOW_SECONDS, LOCKOUT_SECONDS) == (5, 900, 300)


def test_locked_after_max_failures_and_not_before():
    clock = Clock()
    limit = LoginLimit(clock=clock)
    for _ in range(MAX_FAILURES - 1):
        limit.record_failure()
        assert limit.seconds_locked() == 0
    limit.record_failure()
    assert limit.seconds_locked() == LOCKOUT_SECONDS


def test_unlocked_after_lockout():
    clock = Clock()
    limit = LoginLimit(clock=clock)
    for _ in range(MAX_FAILURES):
        limit.record_failure()
    clock.now += LOCKOUT_SECONDS - 1
    assert limit.seconds_locked() > 0
    clock.now += 1
    assert limit.seconds_locked() == 0


def test_failures_outside_the_window_do_not_count():
    clock = Clock()
    limit = LoginLimit(clock=clock)
    for _ in range(MAX_FAILURES - 1):
        limit.record_failure()
    clock.now += WINDOW_SECONDS
    limit.record_failure()
    assert limit.seconds_locked() == 0


def test_success_resets_the_count():
    clock = Clock()
    limit = LoginLimit(clock=clock)
    for _ in range(MAX_FAILURES - 1):
        limit.record_failure()
    limit.record_success()
    for _ in range(MAX_FAILURES - 1):
        limit.record_failure()
    assert limit.seconds_locked() == 0
```

### `tests/test_skeleton.py`

SHA-256 `7b9fb523b34d681fb086c4714dff7378cb43cb1e40dbf67c048dd8cac2c83432`, 9528 bytes.

```python
"""Step 2: the skeleton's files: layout, locked dependencies, image, compose, Render and CI."""
import os
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]

# PRD 6.1
LAYOUT = [
    "hypocurate/pipeline/__init__.py",
    "hypocurate/access/__init__.py",
    "hypocurate/sources/__init__.py",
    "hypocurate/db/__init__.py",
    "hypocurate/web/__init__.py",
    "hypocurate/web/templates",
    "hypocurate/web/static",
    "hypocurate/worker.py",
    "hypocurate/cli.py",
    "tests",
    "Dockerfile",
    "docker-compose.yml",
    "render.yaml",
    "CLAUDE.md",
    "docs/reviews",
    ".github/workflows/tests.yml",
    ".env.example",
    "requirements.lock",
    "requirements-dev.lock",
]
SECRET_NAMES = {"HYPOCURATE_PASSWORD", "SESSION_SECRET", "POSTGRES_PASSWORD", "DATABASE_URL"}


def read(path):
    return (REPO / path).read_text(encoding="utf-8")


def test_layout_matches_prd_6_1():
    missing = [p for p in LAYOUT if not (REPO / p).exists()]
    assert missing == []


# --- secrets --------------------------------------------------------------------

def test_env_example_holds_names_only():
    names = set()
    for line in read(".env.example").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, sep, value = line.partition("=")
        assert sep and value == "", f"{name} has a value in .env.example"
        names.add(name)
    assert SECRET_NAMES | {"HYPOCURATE_ENV"} == names


def test_env_is_ignored_by_git_and_docker():
    assert ".env" in read(".gitignore").splitlines()
    assert ".env" in read(".dockerignore").splitlines()


def text_files():
    skip_dirs = {".git", ".venv", "__pycache__", ".pytest_cache", "sources", "hypocurate.egg-info"}
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for name in files:
            path = Path(root) / name
            if name == ".env" or path.suffix in {".pdf", ".png", ".xlsx"}:
                continue
            try:
                yield path, path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue


KEY_PATTERNS = [
    r"sk-ant-[A-Za-z0-9_-]{10,}",          # Anthropic
    r"sk-(proj-)?[A-Za-z0-9]{20,}",        # OpenAI
    r"gh[pousr]_[A-Za-z0-9]{20,}",         # GitHub
    r"AKIA[0-9A-Z]{16}",                   # AWS
    r"postgres(ql)?://[^:\s/]+:(?!planted-pw-7319@|\$\{|<)[^@\s]+@",  # URL with a password (planted test value allowed)
]


def test_no_keys_or_database_passwords_in_files():
    found = []
    for path, text in text_files():
        for pattern in KEY_PATTERNS:
            if re.search(pattern, text):
                found.append((str(path.relative_to(REPO)), pattern))
    assert found == []


def test_secret_values_from_the_environment_are_in_no_file():
    """When the suite runs with real secrets in its environment (Docker, CI), none appears in a file."""
    values = [os.environ.get(n, "") for n in SECRET_NAMES - {"DATABASE_URL"}]
    values = [v for v in values if len(v) >= 8]
    leaks = [str(p.relative_to(REPO)) for p, text in text_files() if any(v in text for v in values)]
    assert leaks == []


# --- locked dependencies -----------------------------------------------------------

def direct_dependencies(extra=None):
    import tomllib
    project = tomllib.loads(read("pyproject.toml"))["project"]
    deps = project["dependencies"] + (project["optional-dependencies"][extra] if extra else [])
    return {re.split(r"[\[<>=!~ ]", d, maxsplit=1)[0].lower().replace("_", "-") for d in deps}


def locked(path):
    pins = {}
    for m in re.finditer(r"^([A-Za-z0-9_.-]+)==(\S+) \\\n((?:\s+--hash=sha256:[0-9a-f]{64}(?: \\)?\n)+)", read(path), re.M):
        pins[m.group(1).lower().replace("_", "-")] = m.group(2)
    return pins


def test_every_lock_line_is_pinned_with_hashes():
    for path in ["requirements.lock", "requirements-dev.lock"]:
        names = re.findall(r"^([A-Za-z0-9_.-]+)", read(path), re.M)
        assert names and set(n.lower().replace("_", "-") for n in names) == set(locked(path)), path


def test_direct_dependencies_are_locked():
    assert direct_dependencies() <= set(locked("requirements.lock"))
    assert direct_dependencies("dev") <= set(locked("requirements-dev.lock"))


def test_runtime_and_dev_locks_agree():
    runtime, dev = locked("requirements.lock"), locked("requirements-dev.lock")
    assert {n: dev[n] for n in runtime} == runtime


def test_test_tools_are_not_in_the_runtime_lock():
    assert {"pytest", "httpx2", "pyyaml"}.isdisjoint(locked("requirements.lock"))


# --- Docker image ------------------------------------------------------------------

def stages():
    parts = re.split(r"^FROM ", read("Dockerfile"), flags=re.M)[1:]
    return {re.search(r" AS (\w+)", p.splitlines()[0]).group(1): p for p in parts}


def test_base_images_are_pinned_by_digest():
    froms = re.findall(r"^FROM (\S+)", read("Dockerfile"), re.M)
    assert froms[0].startswith("python:3.14-slim@sha256:")
    assert re.search(r"image: postgres:17@sha256:[0-9a-f]{64}", read("docker-compose.yml"))


def test_runtime_image_holds_only_package_data_and_lock():
    copies = re.findall(r"^COPY (\S+)", stages()["runtime"], re.M)
    assert copies == ["requirements.lock", "hypocurate/", "data/"]


def test_installs_require_hashes():
    installs = re.findall(r"pip install (.*)", read("Dockerfile"))
    assert len(installs) == 2 and all("--require-hashes" in i for i in installs)


def test_image_runs_as_non_root():
    for name, body in stages().items():
        users = re.findall(r"^USER (\S+)", body, re.M)
        assert users and users[-1] == "app", name


def test_web_runs_one_process():
    """The login limit is kept in memory, so it holds only with one web process."""
    assert "--workers 1" in stages()["runtime"]


# --- Docker Compose -----------------------------------------------------------------

def test_compose_has_web_worker_database_and_test():
    services = yaml.safe_load(read("docker-compose.yml"))["services"]
    assert {"db", "web", "worker", "test"} <= set(services)
    assert services["worker"]["command"] == ["python", "-m", "hypocurate.worker"]
    assert services["test"]["build"]["target"] == "test"


def test_compose_takes_secrets_from_env_only():
    compose = read("docker-compose.yml")
    assert "${POSTGRES_PASSWORD:?" in compose
    assert not re.search(r"(HYPOCURATE_PASSWORD|SESSION_SECRET)\s*:", compose)


# --- Render ---------------------------------------------------------------------------

def render():
    return yaml.safe_load(read("render.yaml"))


def test_render_describes_web_worker_and_database():
    r = render()
    kinds = {s["type"]: s for s in r["services"]}
    assert set(kinds) == {"web", "worker"}
    assert [d["name"] for d in r["databases"]] == ["hypocurate-db"]
    assert kinds["web"]["healthCheckPath"] == "/health"
    assert kinds["worker"]["dockerCommand"] == "python -m hypocurate.worker"


def test_render_plans_are_the_approved_ones():
    r = render()
    assert {s["type"]: s["plan"] for s in r["services"]} == {"web": "0.5c-512mb", "worker": "0.5c-512mb"}
    assert r["databases"][0]["plan"] == "0.1c-256mb"


def test_render_deploys_only_after_checks_pass():
    for s in render()["services"]:
        assert s["autoDeployTrigger"] == "checksPass", s["name"]
        assert "autoDeploy" not in s
        assert s["branch"] == "main"


def test_render_everything_in_one_region_and_database_private():
    r = render()
    regions = {s["region"] for s in r["services"]} | {r["databases"][0]["region"]}
    assert len(regions) == 1
    assert r["databases"][0]["ipAllowList"] == []


def test_render_holds_no_secret_values():
    env = {s["type"]: {v["key"]: v for v in s["envVars"]} for s in render()["services"]}
    web, wk = env["web"], env["worker"]
    assert web["HYPOCURATE_PASSWORD"] == {"key": "HYPOCURATE_PASSWORD", "sync": False}
    assert web["SESSION_SECRET"] == {"key": "SESSION_SECRET", "generateValue": True}
    for e in (web, wk):
        assert e["HYPOCURATE_ENV"]["value"] == "production"
        assert "value" not in e["DATABASE_URL"] and e["DATABASE_URL"]["fromDatabase"]["property"] == "connectionString"


def test_render_worker_gets_no_login_secrets():
    worker = next(s for s in render()["services"] if s["type"] == "worker")
    assert {v["key"] for v in worker["envVars"]} == {"HYPOCURATE_ENV", "DATABASE_URL"}


# --- GitHub Actions -------------------------------------------------------------------

def test_ci_runs_the_whole_suite_on_every_push_and_pull_request():
    wf = yaml.safe_load(read(".github/workflows/tests.yml"))
    triggers = wf[True]  # YAML 1.1 reads the key "on" as True
    assert set(triggers) == {"push", "pull_request"}
    assert triggers["push"] is None  # every branch, including main (Render waits for it)
    steps = " ".join(s.get("run", "") for s in wf["jobs"]["tests"]["steps"])
    assert "docker compose run --rm test" in steps
    assert "/health" in steps


def test_suite_command_runs_everything():
    """The test image runs plain pytest: no marker, -k or path filter can drop tests."""
    test_stage = stages()["test"]
    assert re.search(r'^CMD \["pytest", "-q"\]$', test_stage, re.M)


def test_ci_actions_are_pinned_to_a_commit():
    uses = re.findall(r"uses: (\S+)", read(".github/workflows/tests.yml"))
    assert uses and all(re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", u) for u in uses)
```


## 5. Containers, deployment and CI

### `.dockerignore`

SHA-256 `79dc1d999d23c23645fcaa3b72f120ca86131c9c14f4729eda5d02525d269ab5`, 56 bytes.

```
.git
.venv
.env
.pytest_cache
**/__pycache__
*.egg-info
```

### `.env.example`

SHA-256 `d156fdf423c48ce513706a0e385c749fadb572c9fcb1e136558f39d26bbe2fab`, 672 bytes.

```
# Copy to .env and fill in. .env is never committed. In production these are
# set in Render's environment settings (render.yaml).
# Names only here; no values.

# development or production (production: cookie sent over HTTPS only)
HYPOCURATE_ENV=
# The single shared login password, at least 12 characters
HYPOCURATE_PASSWORD=
# Signs the session cookie, at least 32 characters (e.g. python3 -c "import secrets; print(secrets.token_urlsafe(48))")
SESSION_SECRET=
# Password of the local Postgres container (docker compose only)
POSTGRES_PASSWORD=
# Only for running outside Docker, e.g. postgresql://hypocurate:<POSTGRES_PASSWORD>@localhost:5432/hypocurate
DATABASE_URL=
```

### `Dockerfile`

SHA-256 `23ed473286e90eb290c0d9b6d8dc68022dd736fcf3009d116b76d4330373f455`, 1223 bytes.

```dockerfile
# One image for the web service and the worker (PRD Section 6).
# Python 3.14: dspy, litellm, statsmodels and scipy all publish releases for it (checked 2026-10-04).
FROM python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock \
    && useradd --create-home --uid 10001 app

# Only the package and the frozen data. tests/ and docs/ hold expected answers
# and stay out of the deployed image (step 1 summary, open item 4).
COPY hypocurate/ hypocurate/
COPY data/ data/

USER app
EXPOSE 8000
# One process, so the in-memory login limit is shared. Render sets PORT.
CMD ["sh", "-c", "exec uvicorn hypocurate.web.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]


# The regression suite, run in the same image (docker compose run --rm test; GitHub Actions).
FROM runtime AS test
USER root
COPY requirements-dev.lock ./
RUN pip install --require-hashes -r requirements-dev.lock
COPY . .
RUN chown -R app /app
USER app
CMD ["pytest", "-q"]
```

### `docker-compose.yml`

SHA-256 `872da8c66333201642811767102b9a58e88e6741b0598ab3b798e6bec4d8392a`, 1245 bytes.

```yaml
# Local work: database, web service, worker; the suite with `docker compose run --rm test`.
# Secrets come from .env (see .env.example), never from this file.
x-app: &app
  build:
    context: .
    target: runtime
  image: hypocurate:runtime
  env_file:
    - path: .env
      required: false
  environment:
    DATABASE_URL: postgresql://hypocurate:${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}@db:5432/hypocurate
  depends_on:
    db:
      condition: service_healthy

services:
  db:
    image: postgres:17@sha256:d74eeac9a635390a49bc21bd49fccd973de707e2a53a76ac49b552b8712ec46f
    environment:
      POSTGRES_USER: hypocurate
      POSTGRES_DB: hypocurate
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hypocurate -d hypocurate"]
      interval: 2s
      timeout: 3s
      retries: 30

  web:
    <<: *app
    ports:
      - "8000:8000"

  worker:
    <<: *app
    command: ["python", "-m", "hypocurate.worker"]

  test:
    <<: *app
    build:
      context: .
      target: test
    image: hypocurate:test
    profiles: ["test"]

volumes:
  pgdata:
```

### `render.yaml`

SHA-256 `8877e6f2d0dd7e8f2c2c9720d1a8e3831c0bcf20195f9b183e3adde0828dfac3`, 1855 bytes.

```yaml
# Render Blueprint (PRD Section 6, "Hosting"). This file only describes the
# services; nothing exists on Render until the owner connects it as a Blueprint.
# Checked against render.com/docs/blueprint-spec on 2026-10-04.
#
# Plans: the cheapest paid plans (owner decision, 2026-10-04).
# autoDeployTrigger checksPass: Render deploys a commit on main only after its
# GitHub checks pass, and never when a check fails or no check is found.
# Region: all three in one region, so the services reach the database over
# Render's private network. It cannot be changed after creation.
services:
  - type: web
    name: hypocurate-web
    runtime: docker
    region: oregon
    plan: 0.5c-512mb
    branch: main
    autoDeployTrigger: checksPass
    dockerfilePath: ./Dockerfile
    dockerContext: .
    healthCheckPath: /health
    envVars:
      - key: HYPOCURATE_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: hypocurate-db
          property: connectionString
      - key: HYPOCURATE_PASSWORD
        sync: false
      - key: SESSION_SECRET
        generateValue: true

  # The worker does not serve pages, so it gets no login secrets.
  - type: worker
    name: hypocurate-worker
    runtime: docker
    region: oregon
    plan: 0.5c-512mb
    branch: main
    autoDeployTrigger: checksPass
    dockerfilePath: ./Dockerfile
    dockerContext: .
    dockerCommand: python -m hypocurate.worker
    envVars:
      - key: HYPOCURATE_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: hypocurate-db
          property: connectionString

databases:
  - name: hypocurate-db
    region: oregon
    plan: 0.1c-256mb
    postgresMajorVersion: "17"
    databaseName: hypocurate
    user: hypocurate
    # No connections from outside Render's private network.
    ipAllowList: []
```

### `.github/workflows/tests.yml`

SHA-256 `006a501f5eb982e5bee7ab37d52eef5cdd2ca66031129f5852f0deeb57d9a6b6`, 1514 bytes.

```yaml
# The regression suite on every push and pull request (PRD 13.1), in the same
# image as the deployed services. Render deploys main only after this passes
# (render.yaml, autoDeployTrigger: checksPass).
name: tests

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  tests:
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1

      - name: Throwaway secrets for this run only
        run: |
          {
            echo "HYPOCURATE_ENV=development"
            echo "HYPOCURATE_PASSWORD=$(openssl rand -hex 24)"
            echo "SESSION_SECRET=$(openssl rand -hex 32)"
            echo "POSTGRES_PASSWORD=$(openssl rand -hex 24)"
          } > .env

      - name: Build images
        run: docker compose --profile test build

      - name: Run the suite in the test image
        run: docker compose run --rm test

      - name: Start web, worker and database; check /health
        run: |
          docker compose up -d web worker
          for i in $(seq 1 30); do
            if curl -fsS http://127.0.0.1:8000/health; then echo; break; fi
            sleep 2
          done
          curl -fsS http://127.0.0.1:8000/health | grep -q '"database":"ok"'
          test "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/)" = 303
          docker compose ps worker --format '{{.State}}' | grep -q running

      - name: Logs
        if: always()
        run: docker compose logs --no-color
```


## 6. Dependencies

### `pyproject.toml`

SHA-256 `005826d23c4854f121844f36d99f9cb4a1eb9bb9933da020ebcce66dbb6e1247`, 889 bytes.

```toml
[build-system]
requires = ["setuptools>=69"]
build-backend = "setuptools.build_meta"

[project]
name = "hypocurate"
version = "0.1.0"
description = "Tests a scientific hypothesis in words against registered data sources."
requires-python = ">=3.12"
# Direct dependencies. The exact versions installed, with hashes, are in
# requirements.lock and requirements-dev.lock (pip-compile --generate-hashes).
dependencies = [
    "pandas>=2.2",
    "openpyxl>=3.1",
    "fastapi>=0.115",
    "uvicorn>=0.30",
    "jinja2>=3.1",
    "itsdangerous>=2.2",
    "python-multipart>=0.0.9",
    "sqlalchemy>=2.0",
    "psycopg[binary]>=3.2",
]

[project.optional-dependencies]
dev = ["pytest>=8", "httpx2>=2.13", "pyyaml>=6"]

[project.scripts]
hypocurate = "hypocurate.cli:main"

[tool.setuptools.packages.find]
include = ["hypocurate*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra"
```

### `requirements.lock`

SHA-256 `4b610ba775f947db59d0da2b16d1b0ef39a2f4f612127b47f747f429c48ab543`, 50418 bytes. Hash lines omitted here.

```
#
# This file is autogenerated by pip-compile with Python 3.14
# by the following command:
#
#    pip-compile --allow-unsafe --generate-hashes --no-index --output-file=requirements.lock --strip-extras pyproject.toml
#
annotated-doc==0.0.5
    # via fastapi
annotated-types==0.8.0
    # via pydantic
anyio==4.15.1
    # via starlette
click==8.5.0
    # via uvicorn
et-xmlfile==2.0.0
    # via openpyxl
fastapi==0.142.2
    # via hypocurate (pyproject.toml)
h11==0.16.0
    # via uvicorn
idna==3.20
    # via anyio
itsdangerous==2.2.0
    # via hypocurate (pyproject.toml)
jinja2==3.1.6
    # via hypocurate (pyproject.toml)
markupsafe==3.0.4
    # via jinja2
numpy==2.5.3
    # via pandas
openpyxl==3.1.5
    # via hypocurate (pyproject.toml)
opentelemetry-api==1.45.0
    # via fastapi
pandas==3.0.6
    # via hypocurate (pyproject.toml)
psycopg==3.3.6
    # via hypocurate (pyproject.toml)
psycopg-binary==3.3.6
    # via psycopg
pydantic==2.13.5
    # via fastapi
pydantic-core==2.46.5
    # via pydantic
python-dateutil==2.9.0.post0
    # via pandas
python-multipart==0.0.32
    # via hypocurate (pyproject.toml)
six==1.17.0
    # via python-dateutil
sqlalchemy==2.1.3
    # via hypocurate (pyproject.toml)
starlette==1.7.0
    # via fastapi
typing-extensions==4.16.0
    # via
    #   anyio
    #   fastapi
    #   opentelemetry-api
    #   pydantic
    #   pydantic-core
    #   sqlalchemy
    #   typing-inspection
typing-inspection==0.4.4
    # via
    #   fastapi
    #   pydantic
uvicorn==0.54.0
    # via hypocurate (pyproject.toml)
```

### `requirements-dev.lock`

SHA-256 `7eca7c4eeda0373a72e6f10308d6b86b36e4040aafdbe3d7b18cd983a74c925a`, 58457 bytes. Hash lines omitted here.

```
#
# This file is autogenerated by pip-compile with Python 3.14
# by the following command:
#
#    pip-compile --allow-unsafe --extra=dev --generate-hashes --no-index --output-file=requirements-dev.lock --strip-extras pyproject.toml
#
annotated-doc==0.0.5
    # via fastapi
annotated-types==0.8.0
    # via pydantic
anyio==4.15.1
    # via
    #   httpx2
    #   starlette
click==8.5.0
    # via uvicorn
et-xmlfile==2.0.0
    # via openpyxl
fastapi==0.142.2
    # via hypocurate (pyproject.toml)
h11==0.16.0
    # via
    #   httpcore2
    #   uvicorn
httpcore2==2.13.1
    # via httpx2
httpx2==2.13.1
    # via hypocurate (pyproject.toml)
idna==3.20
    # via
    #   anyio
    #   httpx2
iniconfig==2.3.0
    # via pytest
itsdangerous==2.2.0
    # via hypocurate (pyproject.toml)
jinja2==3.1.6
    # via hypocurate (pyproject.toml)
markupsafe==3.0.4
    # via jinja2
numpy==2.5.3
    # via pandas
openpyxl==3.1.5
    # via hypocurate (pyproject.toml)
opentelemetry-api==1.45.0
    # via fastapi
packaging==26.3
    # via pytest
pandas==3.0.6
    # via hypocurate (pyproject.toml)
pluggy==1.6.0
    # via pytest
psycopg==3.3.6
    # via hypocurate (pyproject.toml)
psycopg-binary==3.3.6
    # via psycopg
pydantic==2.13.5
    # via fastapi
pydantic-core==2.46.5
    # via pydantic
pygments==2.21.0
    # via pytest
pytest==9.1.1
    # via hypocurate (pyproject.toml)
python-dateutil==2.9.0.post0
    # via pandas
python-multipart==0.0.32
    # via hypocurate (pyproject.toml)
pyyaml==6.0.3
    # via hypocurate (pyproject.toml)
six==1.17.0
    # via python-dateutil
sqlalchemy==2.1.3
    # via hypocurate (pyproject.toml)
starlette==1.7.0
    # via fastapi
truststore==0.10.4
    # via
    #   httpcore2
    #   httpx2
typing-extensions==4.16.0
    # via
    #   anyio
    #   fastapi
    #   opentelemetry-api
    #   pydantic
    #   pydantic-core
    #   sqlalchemy
    #   typing-inspection
typing-inspection==0.4.4
    # via
    #   fastapi
    #   pydantic
uvicorn==0.54.0
    # via hypocurate (pyproject.toml)
```


## 7. README

### `README.md`

SHA-256 `9c6936c3bfcb79bb07471b7285c75fb53978647083845c0a6e081b3d66c73bc0`, 3728 bytes.

````markdown
# hypocurate

[![tests](https://github.com/kelawady/hypocurate/actions/workflows/tests.yml/badge.svg)](https://github.com/kelawady/hypocurate/actions/workflows/tests.yml)

HypoCurate takes a scientific hypothesis in words, searches registered data sources, and reports whether the data in the sources searched are sufficient, partly sufficient or insufficient to test it. The specification is [docs/PRD_sprint1.md](docs/PRD_sprint1.md); the rules for working on the code are in [CLAUDE.md](CLAUDE.md).

## Status

Build step 2 of 12 (PRD Section 15): the skeleton. One Docker image for the web service and the worker, Docker Compose for local work, a health page, the single shared login, the regression suite on GitHub at every push, locked dependencies, and `render.yaml`. The data model, the access layer, the pipeline and the screens come in later steps.

## Set up secrets (once)

```
cp .env.example .env     # then fill in every value; .env is never committed
```

`HYPOCURATE_PASSWORD` is the login password (at least 12 characters). `SESSION_SECRET` signs the session cookie (at least 32 characters): `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. `POSTGRES_PASSWORD` is for the local database container only. `DATABASE_URL` is needed only to run the suite outside Docker: `postgresql://hypocurate:<POSTGRES_PASSWORD>@localhost:5432/hypocurate`.

## Start the system locally

```
docker compose up --build         # database, web (http://localhost:8000) and worker
```

`/health` needs no login; every other page asks for the shared password.

In this Codespace, Docker has a leftover firewall rule that blocks traffic between containers. After every Codespace restart, run once:

```
sudo iptables-legacy -I DOCKER-USER -j ACCEPT
```

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
````


## 8. Test output

`.venv/bin/pytest -v` in the Codespace (Python 3.14.2) against the Compose database, on the reviewed commit:

```
============================= test session starts ==============================
platform linux -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0 -- ./.venv/bin/python3
cachedir: .pytest_cache
rootdir: .
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1
collecting ... collected 151 items

tests/test_controlled_duplicates.py::test_rebuild_gives_identical_bytes PASSED [  0%]
tests/test_controlled_duplicates.py::test_extract_fingerprint_is_in_the_manifest PASSED [  1%]
tests/test_controlled_duplicates.py::test_truth_fingerprint PASSED       [  1%]
tests/test_controlled_duplicates.py::test_answer_material_is_not_under_data_or_the_package PASSED [  2%]
tests/test_controlled_duplicates.py::test_no_expected_outcomes_under_data PASSED [  3%]
tests/test_controlled_duplicates.py::test_no_row_answers_under_package PASSED [  3%]
tests/test_controlled_duplicates.py::test_manifest_points_to_nothing_holding_answers PASSED [  4%]
tests/test_controlled_duplicates.py::test_extract_carries_no_answer_columns PASSED [  5%]
tests/test_controlled_duplicates.py::test_one_answer_per_extract_row PASSED [  5%]
tests/test_controlled_duplicates.py::test_every_case_is_present_twice PASSED [  6%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row1-exact_duplicate_verbatim] PASSED [  7%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row2-exact_duplicate_verbatim] PASSED [  7%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row3-exact_duplicate_renamed_alloy] PASSED [  8%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row4-exact_duplicate_renamed_alloy] PASSED [  9%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row5-possible_duplicate_unknown_paper] PASSED [  9%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row6-possible_duplicate_unknown_paper] PASSED [ 10%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row7-not_duplicate_value_differs] PASSED [ 11%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row8-not_duplicate_value_differs] PASSED [ 11%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row9-not_duplicate_other_paper] PASSED [ 12%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row10-not_duplicate_other_paper] PASSED [ 13%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row11-not_duplicate_other_temperature] PASSED [ 13%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row12-not_duplicate_other_temperature] PASSED [ 14%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row13-missing_test_condition] PASSED [ 15%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row14-missing_test_condition] PASSED [ 15%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row15-not_duplicate_other_test_type] PASSED [ 16%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row16-not_duplicate_other_test_type] PASSED [ 17%]
tests/test_controlled_duplicates.py::test_source_rows_are_in_reference_scope PASSED [ 17%]
tests/test_controlled_duplicates.py::test_verbatim_duplicates_are_byte_identical_lines PASSED [ 18%]
tests/test_controlled_duplicates.py::test_renamed_alloys_have_the_same_composition PASSED [ 19%]
tests/test_controlled_duplicates.py::test_unknown_paper_rows_have_no_reference PASSED [ 19%]
tests/test_controlled_duplicates.py::test_other_paper_rows_use_constructed_dois_not_found_in_mpea PASSED [ 20%]
tests/test_controlled_duplicates.py::test_changed_values_are_as_stated PASSED [ 21%]
tests/test_controlled_duplicates.py::test_missing_test_condition_rows_keep_their_paper PASSED [ 21%]
tests/test_controlled_duplicates.py::test_other_test_type_rows_are_compression_copies_of_tension_records PASSED [ 22%]
tests/test_controlled_duplicates.py::test_no_row_is_labelled_out_of_scope_while_entering_the_analysis PASSED [ 23%]
tests/test_controlled_duplicates.py::test_tension_only_handling_differs_only_for_compression_rows PASSED [ 23%]
tests/test_controlled_duplicates.py::test_expected_handling[row1-exact_duplicate_verbatim] PASSED [ 24%]
tests/test_controlled_duplicates.py::test_expected_handling[row2-exact_duplicate_verbatim] PASSED [ 25%]
tests/test_controlled_duplicates.py::test_expected_handling[row3-exact_duplicate_renamed_alloy] PASSED [ 25%]
tests/test_controlled_duplicates.py::test_expected_handling[row4-exact_duplicate_renamed_alloy] PASSED [ 26%]
tests/test_controlled_duplicates.py::test_expected_handling[row5-possible_duplicate_unknown_paper] PASSED [ 27%]
tests/test_controlled_duplicates.py::test_expected_handling[row6-possible_duplicate_unknown_paper] PASSED [ 27%]
tests/test_controlled_duplicates.py::test_expected_handling[row7-not_duplicate_value_differs] PASSED [ 28%]
tests/test_controlled_duplicates.py::test_expected_handling[row8-not_duplicate_value_differs] PASSED [ 29%]
tests/test_controlled_duplicates.py::test_expected_handling[row9-not_duplicate_other_paper] PASSED [ 29%]
tests/test_controlled_duplicates.py::test_expected_handling[row10-not_duplicate_other_paper] PASSED [ 30%]
tests/test_controlled_duplicates.py::test_expected_handling[row11-not_duplicate_other_temperature] PASSED [ 31%]
tests/test_controlled_duplicates.py::test_expected_handling[row12-not_duplicate_other_temperature] PASSED [ 31%]
tests/test_controlled_duplicates.py::test_expected_handling[row13-missing_test_condition] PASSED [ 32%]
tests/test_controlled_duplicates.py::test_expected_handling[row14-missing_test_condition] PASSED [ 33%]
tests/test_controlled_duplicates.py::test_expected_handling[row15-not_duplicate_other_test_type] PASSED [ 33%]
tests/test_controlled_duplicates.py::test_expected_handling[row16-not_duplicate_other_test_type] PASSED [ 34%]
tests/test_controlled_duplicates.py::test_unknown_paper_is_flagged_as_possible_duplicate_kept_not_removed PASSED [ 35%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row1-exact_duplicate_verbatim] PASSED [ 35%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row2-exact_duplicate_verbatim] PASSED [ 36%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row3-exact_duplicate_renamed_alloy] PASSED [ 37%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row4-exact_duplicate_renamed_alloy] PASSED [ 37%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row5-possible_duplicate_unknown_paper] PASSED [ 38%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row6-possible_duplicate_unknown_paper] PASSED [ 39%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row7-not_duplicate_value_differs] PASSED [ 39%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row8-not_duplicate_value_differs] PASSED [ 40%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row9-not_duplicate_other_paper] PASSED [ 41%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row10-not_duplicate_other_paper] PASSED [ 41%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row11-not_duplicate_other_temperature] PASSED [ 42%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row12-not_duplicate_other_temperature] PASSED [ 43%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row13-missing_test_condition] PASSED [ 43%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row14-missing_test_condition] PASSED [ 44%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row15-not_duplicate_other_test_type] PASSED [ 45%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row16-not_duplicate_other_test_type] PASSED [ 45%]
tests/test_frozen_sources.py::test_manifest_itself_is_unchanged PASSED   [ 46%]
tests/test_frozen_sources.py::test_manifest_covers_exactly_the_required_files PASSED [ 47%]
tests/test_frozen_sources.py::test_required_file_is_present[data/controlled_duplicates/extract.csv] PASSED [ 47%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/mpea/LICENSE] PASSED [ 48%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/mpea/MPEA_dataset.csv] PASSED [ 49%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx] PASSED [ 49%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/tamu_fcc/LICENSE] PASSED [ 50%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/tamu_fcc/inputs.csv] PASSED [ 50%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/mpea/MPEA_dataset.csv] PASSED [ 51%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/mpea/LICENSE] PASSED [ 52%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx] PASSED [ 52%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/inputs.csv] PASSED [ 53%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/LICENSE] PASSED [ 54%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/controlled_duplicates/extract.csv] PASSED [ 54%]
tests/test_frozen_sources.py::test_verify_reports_no_problems PASSED     [ 55%]
tests/test_frozen_sources.py::test_verify_detects_a_changed_byte PASSED  [ 56%]
tests/test_frozen_sources.py::test_both_sources_are_in_the_manifest PASSED [ 56%]
tests/test_frozen_sources.py::test_manifest_records_origin_date_and_licence[mpea] PASSED [ 57%]
tests/test_frozen_sources.py::test_manifest_records_origin_date_and_licence[tamu_fcc] PASSED [ 58%]
tests/test_frozen_sources.py::test_licence_texts_match_the_manifest PASSED [ 58%]
tests/test_frozen_sources.py::test_tamu_origin_is_the_zenodo_record PASSED [ 59%]
tests/test_frozen_sources.py::test_mpea_counts PASSED                    [ 60%]
tests/test_frozen_sources.py::test_tamu_counts PASSED                    [ 60%]
tests/test_frozen_sources.py::test_tamu_csv_view_agrees_with_the_spreadsheet PASSED [ 61%]
tests/test_health.py::test_health_without_login_database_up PASSED       [ 62%]
tests/test_health.py::test_health_page_in_a_browser PASSED               [ 62%]
tests/test_health.py::test_health_reports_database_down_without_crashing PASSED [ 63%]
tests/test_health.py::test_health_shows_no_secrets PASSED                [ 64%]
tests/test_health.py::test_worker_idles_and_checks_the_database PASSED   [ 64%]
tests/test_health.py::test_worker_logs_an_unreachable_database PASSED    [ 65%]
tests/test_health.py::test_cli_check_db PASSED                           [ 66%]
tests/test_login.py::test_pages_redirect_to_login_when_signed_out PASSED [ 66%]
tests/test_login.py::test_login_page_and_static_are_public PASSED        [ 67%]
tests/test_login.py::test_no_api_docs_exposed PASSED                     [ 68%]
tests/test_login.py::test_wrong_password_is_refused_and_gives_no_session PASSED [ 68%]
tests/test_login.py::test_empty_password_is_refused PASSED               [ 69%]
tests/test_login.py::test_right_password_gives_a_session PASSED          [ 70%]
tests/test_login.py::test_logout_ends_the_session PASSED                 [ 70%]
tests/test_login.py::test_tampered_cookie_is_rejected PASSED             [ 71%]
tests/test_login.py::test_cookie_signed_with_another_secret_is_rejected PASSED [ 72%]
tests/test_login.py::test_production_cookie_is_secure_httponly_lax PASSED [ 72%]
tests/test_login.py::test_password_is_not_in_the_cookie_or_pages PASSED  [ 73%]
tests/test_login.py::test_lockout_after_failures_refuses_even_the_right_password PASSED [ 74%]
tests/test_login.py::test_settings_load_when_complete PASSED             [ 74%]
tests/test_login.py::test_web_refuses_to_start_without_a_secret[DATABASE_URL] PASSED [ 75%]
tests/test_login.py::test_web_refuses_to_start_without_a_secret[HYPOCURATE_PASSWORD] PASSED [ 76%]
tests/test_login.py::test_web_refuses_to_start_without_a_secret[SESSION_SECRET] PASSED [ 76%]
tests/test_login.py::test_web_refuses_short_secrets PASSED               [ 77%]
tests/test_login.py::test_config_errors_never_contain_values PASSED      [ 78%]
tests/test_login.py::test_worker_needs_no_login_secrets PASSED           [ 78%]
tests/test_login.py::test_unknown_env_is_refused PASSED                  [ 79%]
tests/test_login.py::test_settings_repr_hides_secrets PASSED             [ 80%]
tests/test_login_limit.py::test_defaults_are_as_approved PASSED          [ 80%]
tests/test_login_limit.py::test_locked_after_max_failures_and_not_before PASSED [ 81%]
tests/test_login_limit.py::test_unlocked_after_lockout PASSED            [ 82%]
tests/test_login_limit.py::test_failures_outside_the_window_do_not_count PASSED [ 82%]
tests/test_login_limit.py::test_success_resets_the_count PASSED          [ 83%]
tests/test_skeleton.py::test_layout_matches_prd_6_1 PASSED               [ 84%]
tests/test_skeleton.py::test_env_example_holds_names_only PASSED         [ 84%]
tests/test_skeleton.py::test_env_is_ignored_by_git_and_docker PASSED     [ 85%]
tests/test_skeleton.py::test_no_keys_or_database_passwords_in_files PASSED [ 86%]
tests/test_skeleton.py::test_secret_values_from_the_environment_are_in_no_file PASSED [ 86%]
tests/test_skeleton.py::test_every_lock_line_is_pinned_with_hashes PASSED [ 87%]
tests/test_skeleton.py::test_direct_dependencies_are_locked PASSED       [ 88%]
tests/test_skeleton.py::test_runtime_and_dev_locks_agree PASSED          [ 88%]
tests/test_skeleton.py::test_test_tools_are_not_in_the_runtime_lock PASSED [ 89%]
tests/test_skeleton.py::test_base_images_are_pinned_by_digest PASSED     [ 90%]
tests/test_skeleton.py::test_runtime_image_holds_only_package_data_and_lock PASSED [ 90%]
tests/test_skeleton.py::test_installs_require_hashes PASSED              [ 91%]
tests/test_skeleton.py::test_image_runs_as_non_root PASSED               [ 92%]
tests/test_skeleton.py::test_web_runs_one_process PASSED                 [ 92%]
tests/test_skeleton.py::test_compose_has_web_worker_database_and_test PASSED [ 93%]
tests/test_skeleton.py::test_compose_takes_secrets_from_env_only PASSED  [ 94%]
tests/test_skeleton.py::test_render_describes_web_worker_and_database PASSED [ 94%]
tests/test_skeleton.py::test_render_plans_are_the_approved_ones PASSED   [ 95%]
tests/test_skeleton.py::test_render_deploys_only_after_checks_pass PASSED [ 96%]
tests/test_skeleton.py::test_render_everything_in_one_region_and_database_private PASSED [ 96%]
tests/test_skeleton.py::test_render_holds_no_secret_values PASSED        [ 97%]
tests/test_skeleton.py::test_render_worker_gets_no_login_secrets PASSED  [ 98%]
tests/test_skeleton.py::test_ci_runs_the_whole_suite_on_every_push_and_pull_request PASSED [ 98%]
tests/test_skeleton.py::test_suite_command_runs_everything PASSED        [ 99%]
tests/test_skeleton.py::test_ci_actions_are_pinned_to_a_commit PASSED    [100%]

============================= 151 passed in 1.78s ==============================
```
