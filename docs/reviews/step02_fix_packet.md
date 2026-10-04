# Build step 2 — fix packet for the second-model re-check

Date: 2026-10-04. Branch: `step-02-skeleton`. The first review covered commit `1249081` (see `docs/reviews/step02_review_packet.md`). The fixes are up to commit `ea44b6c`. This packet is added in the next commit and changes no code. GitHub Actions on the last code commit `f99027c`: success, https://github.com/kelawady/hypocurate/actions/runs/37239535436.

Generated from the files on disk by a script, so every file below is quoted exactly.

## How to use this packet

The owner accepted all six findings of your first review of step 2; your review text is filed verbatim as `docs/reviews/step02_review_chatgpt.md`. Please check that each fix closes its finding, and look for anything the fixes broke or left untested. Use the same checklist (`docs/reviews/checklist.md`, unchanged since the first packet). Return a dated findings file as before; your review is advice, and the test suite is the gate.

| # | Finding | Where the fix is |
|---|---|---|
| 1 | Render would build the test image | `Dockerfile` (runtime stage last); `scripts/check_runtime_image.py`; CI steps "Build the default image exactly as Render does", "Check the default image holds no tests, docs or answers", "Smoke-test the default image's default command"; `test_default_image_*` in `tests/test_skeleton.py`; `tests/test_check_runtime_image.py` |
| 2 | Global lockout allows denial of login | `hypocurate/web/login_throttle.py` replaces `login_limit.py`; `config.py` (24 characters in production); `tests/test_login_throttle.py`; throttling tests in `tests/test_login.py` |
| 3 | Prefix match exempts look-alike paths | `PUBLIC_PATHS` / `STATIC_PREFIX` in `hypocurate/web/app.py`; `test_lookalike_paths_are_protected` |
| 4 | Password change does not end sessions | README "Sessions and the login"; rotation, password-only, expiry and copied-cookie tests in `tests/test_login.py` |
| 5 | Local configuration exposes more than stated | `docker-compose.yml`, `.dockerignore`, `.gitignore`; Compose tests in `tests/test_skeleton.py`; CI step "Check no environment file reached an image" |
| 6 | Tests check appearances | decoded-cookie, docs-after-login and parsed-workflow tests; deploy-gate wording in the summary |

The summary (section 1) gives the details, what was shown against the old Dockerfile, the tests removed or replaced and why, and the open items.

## Contents

1. Step summary (updated)
2. Files changed since the first review
3. Changed files (full text)
4. Test output

## 1. Step summary (updated)

### `docs/reviews/step02_summary.md`

SHA-256 `aff235eca3b75b08431dca2e3d7fdb7e7d296caeb594a207676288e90c8cc7f6`, 19502 bytes.

````markdown
# Build step 2 — summary for review

Date: 2026-10-04. Branch: `step-02-skeleton`. **Status: the six findings of the second-model review are fixed and green on GitHub; awaiting the re-check and the owner's sign-off.** PRD Section 15, step 2: "Skeleton. Repository, Docker image, Docker Compose with web, worker and database, a health page, login, and the regression suite running automatically on GitHub."

The suite is the gate. This summary is for the second-model review (PRD 13.2), which uses `docs/reviews/checklist.md` (first used in this step). It describes the state **after** the fixes for the first review. The findings and their fixes are listed below; the review text is in `docs/reviews/step02_review_chatgpt.md`.

## What was built

| Path | What it is |
|---|---|
| `hypocurate/pipeline/`, `access/`, `db/`, `web/` (`__init__.py`) | PRD 6.1 layout. `pipeline` and `access` hold a docstring only. |
| `hypocurate/config.py` | Settings from environment variables. `DATABASE_URL` is always required. The web service also requires `HYPOCURATE_PASSWORD` and `SESSION_SECRET` (≥ 32 characters) in every environment. The password must be **≥ 24 characters in production** and ≥ 12 in development. The worker and command line do not get these two. Error messages name the setting, never its value. The secrets are hidden from `repr`. |
| `hypocurate/db/engine.py` | SQLAlchemy engine (psycopg 3) and `database_reachable` (`SELECT 1`, never raises). **No tables, no Alembic.** |
| `hypocurate/web/app.py`, `main.py`, `templates/`, `static/style.css` | The web service: `GET/POST /login`, `POST /logout`, `GET /health`, and a placeholder `/` page ("signed in").<br>• Public paths are **exactly** `/login` and `/health`, plus files under the `/static/` prefix. Everything else redirects to `/login` without a session.<br>• FastAPI's `/docs`, `/redoc` and `/openapi.json` are switched off (404 when signed in).<br>• The session is Starlette's `SessionMiddleware`: an itsdangerous-signed cookie `hypocurate_session` holding only `{"signed_in": true}`, 12-hour max age, `SameSite=Lax`, `HttpOnly`, and `Secure` in production. |
| `hypocurate/web/login_throttle.py` | Bounded throttling of failed logins, in memory.<br>• **The correct password is always accepted.**<br>• Wrong passwords are counted; after 5 within 15 minutes, further wrong attempts are refused at once (429) and not counted, until the oldest counted failure leaves the window.<br>• The comparison, the check and the count happen under one lock.<br>• **What it does not do:** slow guessing. A correct guess is accepted even while throttled. The protection against guessing is the password: ≥ 24 random characters in production. The throttle bounds work and log noise.<br>• The web service runs one process (`--workers 1`), so the count is shared; a restart clears it. |
| `/health` | Public. Reports `web`, `database` (`ok` / `unreachable`) and `version` (Render's `RENDER_GIT_COMMIT`, else `unknown`). JSON by default, or an HTML page for a browser. 503 when the database does not answer. No data and no secrets. |
| `hypocurate/worker.py` | Idle loop (owner's decision): it checks the database, logs, and sleeps 60 s. No queue, heartbeat or pipeline; those are step 9. |
| `hypocurate/cli.py` | `hypocurate version` and `hypocurate check-db` only. |
| `pyproject.toml`, `requirements.lock`, `requirements-dev.lock` | Direct dependencies in `pyproject.toml`. Exact versions with SHA-256 hashes, generated by pip-tools 7.6.1. The images install with `--require-hashes`. This closes step 1 open item 7. |
| `Dockerfile` | `python:3.14-slim`, pinned by digest. Three stages:<br>• `base`: runtime lock, non-root user `app`, `hypocurate/`, `data/`;<br>• `test`: base, plus the dev lock and the repository; runs `pytest -q`;<br>• **`runtime`, last**: base plus the uvicorn command.<br>A plain `docker build .`, which is what Render runs, gives the runtime image. It holds only `requirements.lock`, `hypocurate/` and `data/`. |
| `scripts/check_runtime_image.py` | Checks a copy of an image's `/app`:<br>• the top level is exactly `hypocurate`, `data` and `requirements.lock`;<br>• the server and worker files are present;<br>• there is no `tests/`, `docs/`, `scripts/` or `fixtures/` directory;<br>• there is no answer file, builder, review document, `conftest.py` or `test_*.py`;<br>• no file contains answer material. It uses the step 1 tests' own marker functions (row-specific answers everywhere, the outcome vocabulary under `data/`).<br>It runs in the test image, because the markers come from `tests/`, which is never in the deployed image. |
| `.dockerignore`, `.gitignore` | Both ignore `.env*` except `.env.example`, so `.env.production`, backups and similar files are excluded. |
| `docker-compose.yml` | `db` (postgres:17 pinned by digest), `web`, `worker`, and `test` (profile `test`). No `env_file`: each service gets only its own variables through `${VAR:?}` interpolation from `.env`.<br>• db: `POSTGRES_*`;<br>• web: `HYPOCURATE_ENV`, `DATABASE_URL`, `HYPOCURATE_PASSWORD`, `SESSION_SECRET`;<br>• worker: `HYPOCURATE_ENV`, `DATABASE_URL`;<br>• test: `DATABASE_URL` and the three secrets, which only the leak-scan test reads.<br>Ports are published on 127.0.0.1 only. |
| `.env.example` | Names only: `HYPOCURATE_ENV`, `HYPOCURATE_PASSWORD`, `SESSION_SECRET`, `POSTGRES_PASSWORD`, `DATABASE_URL`. |
| `render.yaml` | Blueprint: web service, background worker, PostgreSQL 17, all in `oregon`.<br>• Plans are the cheapest paid (owner's decision): web `0.5c-512mb`, worker `0.5c-512mb`, database `0.1c-256mb`.<br>• `autoDeployTrigger: checksPass` on both services.<br>• `DATABASE_URL` comes from the database's private-network `connectionString`.<br>• `SESSION_SECRET` has `generateValue: true`; `HYPOCURATE_PASSWORD` has `sync: false` and is entered by the owner in Render.<br>• The worker gets no login secrets.<br>• Database `ipAllowList: []` blocks all outside connections.<br>Checked against render.com/docs/blueprint-spec and render.com/docs/deploys on 2026-10-04. |
| `.github/workflows/tests.yml` | Check `tests`, on every push (all branches, including `main`) and every pull request, with no path or branch filters. Steps:<br>1. writes throwaway random secrets, and plants `.env.production.bak`;<br>2. **builds the default image exactly as Render does** (`docker build --file ./Dockerfile .`, no target);<br>3. checks that it runs as `app` with the uvicorn command, copies out its `/app`, and runs `check_runtime_image.py` on it;<br>4. checks that no `.env*` file other than `.env.example` reached either image;<br>5. runs the suite in the test image;<br>6. **smoke-tests the default image's default command**: `/health` reports the database `ok`, and `/` gives 303;<br>7. starts the Compose stack: `/health` ok, `/` gives 303, the worker is running.<br>`actions/checkout` is pinned by commit (v7.0.1). Permissions are `contents: read`. |
| `tests/conftest.py` | `database_url` fixture. When PostgreSQL is not reachable it **fails, it never skips**, with instructions. |
| `README.md` | CI badge; secrets (with the 24-character rule); `docker compose up`; **Sessions and the login**: rotating `SESSION_SECRET` with the password to revoke access, the copied-cookie limitation, the throttle; the Codespace firewall note; running the suite; regenerating the locks; deployment. |

Not built, as instructed: tables, migrations, the access layer, agents, pipeline code, screens other than login and health.

### Python version (owner's condition)
Python 3.14 was chosen after checking that the libraries of later steps publish releases for it. On a wheels-only dry-run resolve on 3.14 (2026-10-04), all of these install:
- dspy 3.4.0 (`requires_python <3.15,>=3.10`);
- litellm 1.104.0 (`<3.15,>=3.10`);
- statsmodels 0.15.0 and scipy 1.18.1 (both with cp314 wheels);
- their native dependencies: numpy 2.5.3, tiktoken 0.14.0, tokenizers 0.23.2.

They are not added to the lock now because nothing uses them yet. The Codespace also runs 3.14.2.

### Other choices made while building
- The web service requires its secrets in development too, not only in production, so a missing `.env` can never start an unprotected site.
- The test client is `httpx2`, which Starlette recommends in place of `httpx` (it gave a deprecation warning).
- pyyaml is a dev dependency only, for reading `render.yaml`, Compose and the workflow in tests.

### What the deploy gate does and does not cover
- `autoDeployTrigger: checksPass` gates Render's **automatic** deploys only. A manual deploy from Render's dashboard (or its API) is a separate path that this setting does not block.
- Render counts a check as passed if its conclusion is `success`, `neutral` **or `skipped`**. It does not deploy when a check fails or when no check is found for the commit. That is why the workflow test forbids `continue-on-error`, job or step conditions (except the final logs step), path or branch filters, and shell overrides.
- The live Render configuration is not shown yet: Render is connected only after sign-off. Checking that the live services carry `checksPass` will be part of that walkthrough.

## Review findings and fixes (first review, ChatGPT, 2026-10-04)

The owner accepted all six findings.

1. **High — Render would build the test image.** The Dockerfile ended with the test stage, so the default build ran `pytest` and contained `tests/`, the review documents and the answer file. The old image-content test read only the stage named `runtime`, so it passed.
   - **Fix:** the `runtime` stage is now last, and `base`/`test`/`runtime` share a clean base. CI builds the default image as Render does, inspects it with `check_runtime_image.py`, and smoke-tests its default command.
   - **Tests:**
     - `test_default_image_is_the_clean_runtime_stage` resolves the **last** stage and every stage it is built from, with all their `COPY` sources;
     - `test_default_image_check_catches_the_old_layout` feeds it the old layout;
     - `test_default_image_serves_the_web_by_default`;
     - `tests/test_check_runtime_image.py` (11): a clean copy passes; `tests/`, `docs/reviews/`, `truth.csv`, a builder, `scripts/`, `conftest.py`, a whole-repository copy, a row answer in the package, outcome vocabulary under `data/`, and a missing server file each fail.
   - **Shown:**
     - run against the old Dockerfile in a scratch copy, the two new Dockerfile tests fail; they pass on the new one;
     - built from the old Dockerfile, the default image has the command `["pytest","-q"]`, and `check_runtime_image.py` reports 46 problems (exit 1);
     - the new default image gives "runtime image OK".
2. **Medium — the global lockout let anyone keep the owner out.**
   - **Fix:** `login_limit.py` is replaced by `login_throttle.py` (above). The correct password is always accepted; the check and the count are atomic; the production password must be ≥ 24 characters.
   - **Tests:**
     - 64 threads of wrong attempts against the throttle give exactly 5 counted and 59 throttled;
     - 50 concurrent wrong attempts through the web app give exactly 5 × 401 and 45 × 429, while a correct login among them succeeds;
     - the correct password is accepted while throttled;
     - a success does not reset the count;
     - the throttle ends when the window passes;
     - throttled attempts are not counted;
     - production refuses 23 characters and accepts 24.
   - The concurrency tests passed 20 runs out of 20 locally.
3. **Medium — `startswith` exempted look-alike paths.**
   - **Fix:** exact matches for `/login` and `/health`; `/static/` stays a prefix.
   - **Test:** dummy protected routes `/loginx`, `/login-admin`, `/login/admin`, `/healthz`, `/health-private`, `/health/export`, `/staticx` and `/static` all redirect to `/login` when signed out, and reach their handler when signed in.
4. **Medium — a password change does not end sessions.**
   - **Fix:** the README says how to revoke access: rotate `SESSION_SECRET` together with the password. No session table.
   - **Tests, each docstring stating the limitation:**
     - a cookie is rejected after the secret and password are rotated, and the old password no longer works;
     - changing only the password does **not** end a session;
     - a session is accepted at 12 h − 1 min and rejected at 12 h + 1 s, with itsdangerous' clock patched;
     - a copied cookie keeps working after the original client logs out.
5. **Medium — local configuration exposed more than stated.**
   - **Fix:** the per-service variables, the 127.0.0.1 port bindings and the broader `.env*` ignore described above.
   - **Tests:**
     - each service's environment key set is exactly as listed, with no `env_file`;
     - secret values are `${VAR:?}` interpolations;
     - every published port is on 127.0.0.1;
     - both ignore files hold `.env*` before `!.env.example`;
     - CI plants `.env.production.bak` and checks that it reaches neither image.
   - Locally, `docker compose exec` shows the worker's variables as `DATABASE_URL HYPOCURATE_ENV` only.
6. **Medium — tests checked appearances.** Fixes:
   - the cookie payload is decoded and must equal `{"signed_in": true}`;
   - a forged payload with the old signature is rejected;
   - the API docs give 404 after login;
   - the workflow is parsed, and the test fails on `continue-on-error`, any job or step `if` other than `always()` on the logs step, trigger filters, `defaults`/`shell` overrides, other jobs, or a missing required step (default build, image check, env-file check, suite, default-command smoke, Compose smoke);
   - the deploy-gate wording is corrected (section above).

### Tests removed or replaced in the fix round
These tests checked the behaviour that finding 2 removed, or were replaced by stricter behavioural versions. None was weakened to make a change pass.
- `tests/test_login_limit.py` (5 tests of the lockout) is removed with `login_limit.py` and replaced by `tests/test_login_throttle.py` (7).
- `test_lockout_after_failures_refuses_even_the_right_password` asserted the behaviour the owner rejected. It is replaced by `test_correct_password_is_accepted_while_throttled`, which asserts the opposite, and by `test_wrong_attempts_beyond_the_bound_are_refused_quickly`.
- Replaced by stricter versions:
  - `test_password_is_not_in_the_cookie_or_pages` → `test_cookie_holds_only_the_signed_in_flag` (decoded) and `test_password_is_not_in_pages`;
  - `test_no_api_docs_exposed` → `test_no_api_docs_before_or_after_login`;
  - `test_runtime_image_holds_only_package_data_and_lock` → the three default-image tests;
  - `test_env_is_ignored_by_git_and_docker` → `test_every_env_file_is_ignored_by_git_and_docker`;
  - `test_compose_takes_secrets_from_env_only` → the per-service environment and interpolation tests;
  - `test_ci_runs_the_whole_suite_on_every_push_and_pull_request` → the three parsed-workflow tests.
- `test_web_refuses_short_secrets` is split into the production (24), development (12) and session-secret tests.

## Tests (188, all passing; 95 for step 2, the 93 from step 1 unchanged)

`git diff main -- tests/test_frozen_sources.py tests/test_controlled_duplicates.py tests/fixtures data` is empty.

| File | Tests | What |
|---|---|---|
| `tests/test_login.py` | 39 | Which paths need the login, including the look-alikes; password; decoded cookie, tampering, forged payload, foreign secret, production flags and max age; rotation, password-only change, expiry, copied cookie; throttling through the app, including concurrency; settings |
| `tests/test_login_throttle.py` | 7 | The throttle on its own, including 64 concurrent threads |
| `tests/test_health.py` | 7 | Health against real PostgreSQL, the database being down, no secrets; worker; CLI |
| `tests/test_check_runtime_image.py` | 11 | The image content check |
| `tests/test_skeleton.py` | 31 | Layout; env files; key and secret scans; locks; Dockerfile default image; Compose per-service variables and ports; render.yaml; parsed workflow |

### Suite results
```
$ .venv/bin/pytest -q                    (Codespace, Python 3.14.2, with `docker compose up -d db`)
188 passed in 3.26s
$ docker compose run --rm test           (the test image)
188 passed in 4.32s
GitHub Actions, commit f99027c:          success; every step passed, including the default image
                                         check ("runtime image OK") and the default-command smoke test
https://github.com/kelawady/hypocurate/actions/runs/37239535436
```

The same CI steps were run locally first:
- the default image runs as `app` with the uvicorn command, and the check reports "runtime image OK";
- `.env.production.bak` reached neither image;
- the default image's `/health` → database `ok`, and `/` → 303;
- in the Compose stack, web is on `127.0.0.1:8000`, `/health` is ok, and the worker has only `DATABASE_URL` and `HYPOCURATE_ENV`.

## Deviations from the PRD and the approved plan
1. **Render is connected at the end of this step, not at step 11** (owner's decision, 2026-10-04), so that every later step is verified on the live site. Order: re-check and sign-off → branch green → merge `--no-ff` → `main` green → Render actions one at a time, with prices confirmed first, until `/health` and `/login` work on the Render address. The live check will be added to this summary.
2. **Dev container (PRD 16) is deferred** (owner's decision). Proposed backlog item; the PRD itself is not edited.
3. **Merge gate:** the repository is private on a free GitHub plan, so GitHub cannot require the check before a merge. By process, I confirm that the branch run is green and record its link before every merge (owner's decision).
4. **Fix-round plan change:** the plan said the step 1 marker functions would move to a shared module. Instead `check_runtime_image.py` imports them from `tests/test_controlled_duplicates.py` as they are, so the step 1 test file stays byte-identical.

## Codespace finding (not a project change)
In this Codespace, Docker has a leftover `iptables-legacy` FORWARD chain with policy DROP, which blocks traffic between containers. With the owner's approval I ran `sudo iptables-legacy -I DOCKER-USER -j ACCEPT`. It is lost on restart; the README has the command. GitHub's runners and Render are not affected.

## Open items
1. **Region.** `render.yaml` uses `oregon` for all three resources; it cannot be changed after creation. Confirm before connecting Render.
2. **Prices.** Confirm Render's current prices for the three plans before the first paid action.
3. **Live deploy gate.** When Render is connected, check on the live services that the automatic deploy setting is "After CI Checks Pass", and agree not to deploy manually without a green run.
4. **Session revocation is all-or-nothing** (rotate `SESSION_SECRET`). Revoking a single session needs a session table; it is not proposed for sprint 1.
5. **Pipeline code can still read `tests/` and `docs/reviews/` in development.** The deployed image does not contain them and CI checks this, but the step 5 access layer must still enforce the approved file list (step 1 open item 4).
6. Carried from step 1, unchanged: the pooled p-value 7.4e-7 against "≈ 8e-7" (before step 7); permitted test types and a non-MPEA survivor pair (step 6).
7. `docs/reviews/checklist.md` was used for the first time in this review and may be amended afterwards, with owner approval.
````

## 2. Files changed since the first review

| Status | Path |
|---|---|
| M | `.dockerignore` |
| M | `.env.example` |
| M | `.github/workflows/tests.yml` |
| M | `.gitignore` |
| M | `Dockerfile` |
| M | `README.md` |
| M | `docker-compose.yml` |
| A | `docs/reviews/step02_review_chatgpt.md` |
| A | `docs/reviews/step02_review_packet.md` |
| M | `docs/reviews/step02_summary.md` |
| M | `hypocurate/config.py` |
| M | `hypocurate/web/app.py` |
| D | `hypocurate/web/login_limit.py` |
| A | `hypocurate/web/login_throttle.py` |
| A | `scripts/check_runtime_image.py` |
| A | `tests/test_check_runtime_image.py` |
| M | `tests/test_login.py` |
| D | `tests/test_login_limit.py` |
| A | `tests/test_login_throttle.py` |
| M | `tests/test_skeleton.py` |

`D` = deleted: `hypocurate/web/login_limit.py` and `tests/test_login_limit.py` were replaced (finding 2). Their text is in the first review packet.

## 3. Changed files (full text)

### `Dockerfile`

SHA-256 `cebc22130f25aaa6add50bdda9eec752285b2b1a4749bec47c1622752eba6173`, 1606 bytes.

```dockerfile
# One image for the web service and the worker (PRD Section 6).
# Python 3.14: dspy, litellm, statsmodels and scipy all publish releases for it (checked 2026-10-04).
#
# Stages: base -> test, and base -> runtime. The runtime stage is LAST, so a plain
# `docker build .` (what Render runs) gives the clean runtime image. The test
# stage is built only on request (`--target test`, docker compose's test service).
FROM python:3.14-slim@sha256:c3e521df8b2b498a7a682e7e18676771cb80c6b75b8699af886b2d554ce40151 AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore
WORKDIR /app

COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock \
    && useradd --create-home --uid 10001 app

# Only the package and the frozen data. tests/ and docs/ hold expected answers
# and stay out of the deployed image (step 1 summary, open item 4).
COPY hypocurate/ hypocurate/
COPY data/ data/
USER app


# The regression suite, in the same base (docker compose run --rm test; GitHub Actions).
FROM base AS test
USER root
COPY requirements-dev.lock ./
RUN pip install --require-hashes -r requirements-dev.lock
COPY . .
RUN chown -R app /app
USER app
CMD ["pytest", "-q"]


# The deployed image: web service by default; the worker overrides the command.
FROM base AS runtime
USER app
EXPOSE 8000
# One process, so the in-memory login throttle is shared. Render sets PORT.
CMD ["sh", "-c", "exec uvicorn hypocurate.web.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
```

### `.dockerignore`

SHA-256 `6c0ad1857e3206a560475c375b14d8ee891545e1ce21b66e6883294242392c69`, 213 bytes.

```
.git
.venv
# Every local environment file and backup (.env, .env.production, .env.bak, ...);
# only the names-only template goes into the build context.
.env*
!.env.example
.pytest_cache
**/__pycache__
*.egg-info
```

### `.gitignore`

SHA-256 `467d892db70b6bca44217f178be44c4d7991338ae7c0114b6083b8b83fdce6ea`, 4679 bytes.

```
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[codz]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#   Usually these files are written by a python script from a template
#   before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py.cover
*.lcov
.hypothesis/
.pytest_cache/
cover/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
#   For a library or package, you might want to ignore these files since the code is
#   intended to run in multiple environments; otherwise, check them in:
# .python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or not
#   install all needed dependencies.
# Pipfile.lock

# uv
#   Similar to Pipfile.lock, it is generally recommended to include uv.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
# uv.lock

# poetry
#   Similar to Pipfile.lock, it is generally recommended to include poetry.lock in version control.
#   This is especially recommended for binary packages to ensure reproducibility, and is more
#   commonly ignored for libraries.
#   https://python-poetry.org/docs/basic-usage/#commit-your-poetrylock-file-to-version-control
# poetry.lock
# poetry.toml

# pdm
#   Similar to Pipfile.lock, it is generally recommended to include pdm.lock in version control.
#   pdm recommends including project-wide configuration in pdm.toml, but excluding .pdm-python.
#   https://pdm-project.org/en/latest/usage/project/#working-with-version-control
# pdm.lock
# pdm.toml
.pdm-python
.pdm-build/

# pixi
#   Similar to Pipfile.lock, it is generally recommended to include pixi.lock in version control.
# pixi.lock
#   Pixi creates a virtual environment in the .pixi directory, just like venv module creates one
#   in the .venv directory. It is recommended not to include this directory in version control.
.pixi/*
!.pixi/config.toml

# PEP 582; used by e.g. github.com/David-OConnor/pyflow and github.com/pdm-project/pdm
__pypackages__/

# Celery stuff
celerybeat-schedule*
celerybeat.pid

# Redis
*.rdb
*.aof
*.pid

# RabbitMQ
mnesia/
rabbitmq/
rabbitmq-data/

# ActiveMQ
activemq-data/

# SageMath parsed files
*.sage.py

# Environments
.env*
!.env.example
.envrc
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs/Zensical documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static type analyzer
.pytype/

# Cython debug symbols
cython_debug/

# PyCharm
#   JetBrains specific template is maintained in a separate JetBrains.gitignore that can
#   be found at https://github.com/github/gitignore/blob/main/Global/JetBrains.gitignore
#   and can be added to the global gitignore or merged into this file.  For a more nuclear
#   option (not recommended) you can uncomment the following to ignore the entire idea folder.
# .idea/

# Abstra
#   Abstra is an AI-powered process automation framework.
#   Ignore directories containing user credentials, local state, and settings.
#   Learn more at https://abstra.io/docs
.abstra/

# Visual Studio Code
#   Visual Studio Code specific template is maintained in a separate VisualStudioCode.gitignore that
#   can be found at https://github.com/github/gitignore/blob/main/Global/VisualStudioCode.gitignore
#   and can be added to the global gitignore or merged into this file. However, if you prefer, you
#   could uncomment the following to ignore the entire vscode folder
# .vscode/
# Temporary file for partial code execution
tempCodeRunnerFile.py

# Ruff stuff:
.ruff_cache/

# PyPI configuration file
.pypirc

# Marimo
marimo/_static/
marimo/_lsp/
__marimo__/

# Streamlit
.streamlit/secrets.toml
```

### `docker-compose.yml`

SHA-256 `f71b7b2350e91e5f8226fefb5fbd392ebd6aa6254853ac90f9d634d6eba9b75f`, 2182 bytes.

```yaml
# Local work: database, web service, worker; the suite with `docker compose run --rm test`.
# Values come from .env (see .env.example), never from this file. Compose reads
# .env only to fill in the ${...} below; each service gets only the variables it
# needs (second-model review of step 2, finding 5).
x-database-url: &database-url postgresql://hypocurate:${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}@db:5432/hypocurate

x-app: &app
  build:
    context: .
    target: runtime
  image: hypocurate:runtime
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
    environment:
      HYPOCURATE_ENV: ${HYPOCURATE_ENV:-development}
      DATABASE_URL: *database-url
      HYPOCURATE_PASSWORD: ${HYPOCURATE_PASSWORD:?set HYPOCURATE_PASSWORD in .env}
      SESSION_SECRET: ${SESSION_SECRET:?set SESSION_SECRET in .env}
    # Plain HTTP locally: reachable from this machine only.
    ports:
      - "127.0.0.1:8000:8000"

  worker:
    <<: *app
    command: ["python", "-m", "hypocurate.worker"]
    environment:
      HYPOCURATE_ENV: ${HYPOCURATE_ENV:-development}
      DATABASE_URL: *database-url

  # The secrets are passed only so that the suite can check that none of their
  # values appears in any file (tests/test_skeleton.py).
  test:
    <<: *app
    build:
      context: .
      target: test
    image: hypocurate:test
    profiles: ["test"]
    environment:
      DATABASE_URL: *database-url
      HYPOCURATE_PASSWORD: ${HYPOCURATE_PASSWORD:?set HYPOCURATE_PASSWORD in .env}
      SESSION_SECRET: ${SESSION_SECRET:?set SESSION_SECRET in .env}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD in .env}

volumes:
  pgdata:
```

### `.env.example`

SHA-256 `e67a298fcd8dc5d69744eb02196e920ba7558c2fb4a8d8798a72cc9e079d766c`, 705 bytes.

```
# Copy to .env and fill in. .env is never committed. In production these are
# set in Render's environment settings (render.yaml).
# Names only here; no values.

# development or production (production: cookie sent over HTTPS only)
HYPOCURATE_ENV=
# The single shared login password: at least 24 random characters in production, 12 locally
HYPOCURATE_PASSWORD=
# Signs the session cookie, at least 32 characters (e.g. python3 -c "import secrets; print(secrets.token_urlsafe(48))")
SESSION_SECRET=
# Password of the local Postgres container (docker compose only)
POSTGRES_PASSWORD=
# Only for running outside Docker, e.g. postgresql://hypocurate:<POSTGRES_PASSWORD>@localhost:5432/hypocurate
DATABASE_URL=
```

### `.github/workflows/tests.yml`

SHA-256 `97cd44b56c0450784d3c912483c4054fc358a018ccb2d5533955626e3e780778`, 3841 bytes.

```yaml
# The regression suite on every push and pull request (PRD 13.1), and checks of
# the image Render builds. Render deploys main automatically only after this
# passes (render.yaml, autoDeployTrigger: checksPass).
# Nothing here may be skipped or allowed to fail: Render counts skipped and
# neutral checks as passed (tests/test_skeleton.py enforces this file's shape).
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
          # Planted: must never reach an image (.dockerignore).
          echo "PLANTED=planted-env-backup-4410" > .env.production.bak

      - name: Build the default image exactly as Render does
        run: docker build --file ./Dockerfile --tag hypocurate:default .

      - name: Build the test image
        run: docker compose --profile test build test

      - name: Check the default image holds no tests, docs or answers
        run: |
          test "$(docker inspect --format '{{.Config.User}}' hypocurate:default)" = app
          docker inspect --format '{{json .Config.Cmd}}' hypocurate:default | grep -q 'uvicorn hypocurate.web.main:app'
          docker create --name default-export hypocurate:default
          docker cp default-export:/app ./default-image-app
          docker rm default-export
          docker run --rm -v "$PWD/default-image-app:/image:ro" hypocurate:test \
            python scripts/check_runtime_image.py /image

      - name: Check no environment file reached an image
        run: |
          for image in hypocurate:default hypocurate:test; do
            found="$(docker run --rm --entrypoint sh "$image" -c 'cd /app && ls -A | grep "^\.env" || true')"
            test -z "$found" -o "$found" = ".env.example" || { echo "$image: $found"; exit 1; }
          done

      - name: Run the suite in the test image
        run: docker compose run --rm test

      - name: Smoke-test the default image's default command
        run: |
          docker compose up -d db
          network="$(docker inspect --format '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}{{end}}' "$(docker compose ps -q db)")"
          set -a; . ./.env; set +a
          docker run -d --name default-web --network "$network" -p 127.0.0.1:8001:8000 \
            -e HYPOCURATE_ENV=production \
            -e HYPOCURATE_PASSWORD="$(openssl rand -hex 16)" \
            -e SESSION_SECRET \
            -e DATABASE_URL="postgresql://hypocurate:${POSTGRES_PASSWORD}@db:5432/hypocurate" \
            hypocurate:default
          for i in $(seq 1 30); do curl -fsS http://127.0.0.1:8001/health && break; sleep 2; done
          echo
          curl -fsS http://127.0.0.1:8001/health | grep -q '"database":"ok"'
          test "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8001/)" = 303
          docker rm -f default-web

      - name: Start web, worker and database with Compose; check /health
        run: |
          docker compose up -d web worker
          for i in $(seq 1 30); do curl -fsS http://127.0.0.1:8000/health && break; sleep 2; done
          echo
          curl -fsS http://127.0.0.1:8000/health | grep -q '"database":"ok"'
          test "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/)" = 303
          docker compose ps worker --format '{{.State}}' | grep -q running

      - name: Logs
        if: always()
        run: docker compose logs --no-color
```

### `scripts/check_runtime_image.py`

SHA-256 `55f6884e411b83156576973eaf0aa784dcbf49cb1d0230c81183b926bc89e49d`, 3099 bytes.

```python
"""Check the contents of the deployed image (second-model review of step 2, finding 1).

Usage: python scripts/check_runtime_image.py <dir>
where <dir> is the image's /app copied out with `docker cp`. Run from the
repository (the test image in CI), because the answer markers come from the
step 1 tests, which are never in the deployed image.

The image must hold exactly the package, the frozen data and the runtime lock:
no tests/, no docs/, no answer file, no builder, no review document, and no
answer material in any file. Exit status 1 and one line per problem otherwise.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOP_LEVEL = {"hypocurate", "data", "requirements.lock"}
REQUIRED = ["hypocurate/web/main.py", "hypocurate/worker.py", "data/manifest.json", "requirements.lock"]
FORBIDDEN_DIRS = {"tests", "docs", "reviews", "fixtures", "scripts"}
FORBIDDEN_NAMES = re.compile(r"(truth.*|build.*\.py|step\d\d_.*|checklist\.md|conftest\.py|test_.*\.py)$")


def _answer_markers():
    spec = importlib.util.spec_from_file_location("step1_tests", REPO / "tests/test_controlled_duplicates.py")
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    row = {m.lower() for m in tests._row_specific_markers()}
    generic = {m.lower() for m in tests._generic_outcome_markers()}
    return row, generic, tests.FROZEN_SOURCE_FILES


def problems(root: Path) -> list[str]:
    root = Path(root)
    found = []
    top = {p.name for p in root.iterdir()}
    if top != TOP_LEVEL:
        found.append(f"top level is {sorted(top)}, expected {sorted(TOP_LEVEL)}")
    found += [f"missing {r}" for r in REQUIRED if not (root / r).is_file()]

    row, generic, frozen = _answer_markers()
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        parts = path.relative_to(root).parts
        if FORBIDDEN_DIRS & set(parts if path.is_dir() else parts[:-1]):
            found.append(f"forbidden directory: {rel}")
            continue
        if not path.is_file():
            continue
        if FORBIDDEN_NAMES.match(path.name):
            found.append(f"forbidden file: {rel}")
        if rel in frozen:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        # Row-specific answers are forbidden everywhere; the outcome vocabulary only
        # under data/ (the package uses it from step 6), as in the step 1 tests.
        markers = row | generic if rel.startswith("data/") else row
        hits = sorted(m for m in markers if m in text)
        if hits:
            found.append(f"answer material in {rel}: {hits[:3]}")
    return found


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    found = problems(Path(argv[1]))
    for line in found:
        print(line)
    print("runtime image OK" if not found else f"{len(found)} problem(s)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

### `hypocurate/web/login_throttle.py`

SHA-256 `18ac815cfa880b025e714f705180aca49454f1f8dd227d3d11dae359917dee84`, 2144 bytes.

```python
"""Bounded throttling of failed logins, kept in memory (no table).

Second-model review of step 2, finding 2: a lockout lets anyone keep the owner
out, so there is none. The correct password is always accepted. Wrong passwords
are counted; once MAX_FAILURES have been counted within WINDOW_SECONDS, further
wrong attempts are refused at once (and not counted) until the oldest counted
failure leaves the window.

The comparison, the check and the count happen under one lock, so concurrent
attempts cannot slip past the bound.

What this does and does not do: it bounds the work and the log noise caused by
wrong attempts. It does not slow guessing, because a correct guess is accepted
even while throttled. Protection against guessing is the password itself: in
production at least 24 random characters (hypocurate/config.py).

The web service runs one process, so the count is shared; a restart clears it.
"""
from __future__ import annotations

import hmac
import threading
import time
from collections import deque
from collections.abc import Callable
from enum import Enum

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60


class Attempt(Enum):
    OK = "ok"
    WRONG = "wrong"
    THROTTLED = "throttled"


class LoginThrottle:
    def __init__(
        self,
        max_failures: int = MAX_FAILURES,
        window_seconds: float = WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._clock = clock
        self._failures: deque[float] = deque()
        self._lock = threading.Lock()

    def attempt(self, password: str, expected: str) -> Attempt:
        with self._lock:
            if hmac.compare_digest(password.encode(), expected.encode()):
                return Attempt.OK
            now = self._clock()
            while self._failures and self._failures[0] <= now - self.window_seconds:
                self._failures.popleft()
            if len(self._failures) >= self.max_failures:
                return Attempt.THROTTLED
            self._failures.append(now)
            return Attempt.WRONG
```

### `hypocurate/web/app.py`

SHA-256 `664558be3891771bed0bb5deb2619b29f2f3b328787f2f592b6da2816cab0ac5`, 4123 bytes.

```python
"""The web service (PRD Section 6): login, health page, and a placeholder home page.

Every page needs the shared login except exactly /login and /health, and the
files under /static/. The session is a signed cookie (Starlette
SessionMiddleware, itsdangerous) holding only {"signed_in": true}; in
production it is sent over HTTPS only. There is no server-side session record:
rotating SESSION_SECRET ends every session (README, "Sessions").
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Engine
from starlette.middleware.sessions import SessionMiddleware

from hypocurate.config import Settings, load_settings
from hypocurate.db.engine import database_reachable, make_engine
from hypocurate.web.login_throttle import Attempt, LoginThrottle

HERE = Path(__file__).resolve().parent
SESSION_COOKIE = "hypocurate_session"
SESSION_MAX_AGE = 12 * 60 * 60
PUBLIC_PATHS = frozenset({"/login", "/health"})  # exact matches only
STATIC_PREFIX = "/static/"

templates = Jinja2Templates(directory=HERE / "templates")


def create_app(
    settings: Settings | None = None,
    engine: Engine | None = None,
    login_throttle: LoginThrottle | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    engine = engine or make_engine(settings.database_url)
    throttle = login_throttle or LoginThrottle()

    app = FastAPI(title="HypoCurate", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def require_login(request: Request, call_next):
        path = request.url.path
        public = path in PUBLIC_PATHS or path.startswith(STATIC_PREFIX)
        if not public and not request.session.get("signed_in"):
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
        result = throttle.attempt(password, settings.password)
        if result is Attempt.OK:
            request.session.clear()
            request.session["signed_in"] = True
            return RedirectResponse("/", status_code=303)
        if result is Attempt.THROTTLED:
            return templates.TemplateResponse(
                request, "login.html",
                {"error": "Too many failed attempts. Try again in a few minutes."},
                status_code=429,
            )
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

### `hypocurate/config.py`

SHA-256 `1938e736c86ae25a2f5ae13cb85fc879b8be8d0e1a6917083e68f5a89264ebe4`, 2599 bytes.

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
# Production: a generated password of at least 24 random characters is the
# protection against guessing (the login throttle does not slow guessing).
MIN_PRODUCTION_PASSWORD_LENGTH = 24
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
    min_password = MIN_PRODUCTION_PASSWORD_LENGTH if settings.production else MIN_PASSWORD_LENGTH
    if web and len(settings.password) < min_password:
        problems.append(f"HYPOCURATE_PASSWORD must be at least {min_password} characters in {env}")
    if web and len(settings.session_secret) < MIN_SESSION_SECRET_LENGTH:
        problems.append(f"SESSION_SECRET must be at least {MIN_SESSION_SECRET_LENGTH} characters")
    if problems:
        raise ConfigError("; ".join(problems))
    return settings
```

### `tests/test_check_runtime_image.py`

SHA-256 `1706034f1f73569cfc36d324549e8a22156142461fac7ab753897dc1abe7f8b3`, 2489 bytes.

```python
"""Step 2 fix (review finding 1): the deployed-image content check catches what it must."""
import importlib.util
import shutil

import pytest

from hypocurate.sources.manifest import REPO_ROOT

_spec = importlib.util.spec_from_file_location("check", REPO_ROOT / "scripts/check_runtime_image.py")
check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check)


@pytest.fixture
def image(tmp_path):
    """A copy of what the runtime stage puts in /app."""
    root = tmp_path / "app"
    root.mkdir()
    shutil.copytree(REPO_ROOT / "hypocurate", root / "hypocurate",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO_ROOT / "data", root / "data")
    shutil.copy(REPO_ROOT / "requirements.lock", root)
    return root


def test_clean_image_passes(image):
    assert check.problems(image) == []
    assert check.main(["check", str(image)]) == 0


@pytest.mark.parametrize("planted", [
    "tests/test_login.py",
    "docs/reviews/step02_summary.md",
    "data/controlled_duplicates/truth.csv",
    "hypocurate/fixtures/build.py",
    "scripts/check_runtime_image.py",
    "conftest.py",
])
def test_forbidden_paths_fail(image, planted):
    path = image / planted
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x\n")
    assert check.problems(image)
    assert check.main(["check", str(image)]) == 1


def test_whole_repository_copy_fails(image):
    """What the old default stage (`COPY . .`) produced."""
    shutil.copytree(REPO_ROOT / "tests", image / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(REPO_ROOT / "docs" / "reviews", image / "docs" / "reviews")
    found = check.problems(image)
    assert any("tests" in f for f in found) and any("docs" in f for f in found)


def test_row_answer_in_package_fails(image):
    row, _, _ = check._answer_markers()
    marker = sorted(m for m in row if len(m) > 30)[0]
    (image / "hypocurate" / "leak.py").write_text(f'"""{marker}"""\n')
    assert any("answer material in hypocurate/leak.py" in f for f in check.problems(image))


def test_outcome_vocabulary_under_data_fails(image):
    (image / "data" / "notes.txt").write_text("these two records are exact_duplicate\n")
    assert any("answer material in data/notes.txt" in f for f in check.problems(image))


def test_missing_server_fails(image):
    (image / "hypocurate" / "web" / "main.py").unlink()
    assert "missing hypocurate/web/main.py" in check.problems(image)
```

### `tests/test_login_throttle.py`

SHA-256 `f00c42ee8cadcf955dc816a0ef75866312e0a49b8ff436fbd61843bcfe9032c0`, 2534 bytes.

```python
"""Step 2 fix (review finding 2): bounded throttling of failed logins, no lockout."""
import threading
from collections import Counter

from hypocurate.web.login_throttle import MAX_FAILURES, WINDOW_SECONDS, Attempt, LoginThrottle

RIGHT = "the-right-password"


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_defaults_are_as_approved():
    assert (MAX_FAILURES, WINDOW_SECONDS) == (5, 900)


def test_wrong_attempts_counted_up_to_the_bound_then_throttled():
    t = LoginThrottle(clock=Clock())
    results = [t.attempt("wrong", RIGHT) for _ in range(MAX_FAILURES + 2)]
    assert results == [Attempt.WRONG] * MAX_FAILURES + [Attempt.THROTTLED] * 2


def test_correct_password_always_accepted():
    t = LoginThrottle(clock=Clock())
    assert t.attempt(RIGHT, RIGHT) is Attempt.OK
    for _ in range(MAX_FAILURES * 3):
        t.attempt("wrong", RIGHT)
    assert t.attempt(RIGHT, RIGHT) is Attempt.OK


def test_success_does_not_reset_the_count():
    t = LoginThrottle(clock=Clock())
    for _ in range(MAX_FAILURES):
        t.attempt("wrong", RIGHT)
    t.attempt(RIGHT, RIGHT)
    assert t.attempt("wrong", RIGHT) is Attempt.THROTTLED


def test_throttle_ends_when_failures_leave_the_window():
    clock = Clock()
    t = LoginThrottle(clock=clock)
    for _ in range(MAX_FAILURES):
        t.attempt("wrong", RIGHT)
    clock.now += WINDOW_SECONDS - 1
    assert t.attempt("wrong", RIGHT) is Attempt.THROTTLED
    clock.now += 1
    assert t.attempt("wrong", RIGHT) is Attempt.WRONG


def test_throttled_attempts_are_not_counted():
    """Otherwise a steady stream of refused attempts would extend the throttle forever."""
    clock = Clock()
    t = LoginThrottle(clock=clock)
    for _ in range(MAX_FAILURES):
        t.attempt("wrong", RIGHT)
    for _ in range(100):
        clock.now += 1
        t.attempt("wrong", RIGHT)
    clock.now = 1000.0 + WINDOW_SECONDS
    assert t.attempt("wrong", RIGHT) is Attempt.WRONG


def test_concurrent_failures_never_pass_the_bound():
    t = LoginThrottle()
    start = threading.Barrier(64)
    results = []
    lock = threading.Lock()

    def go():
        start.wait()
        r = t.attempt("wrong", RIGHT)
        with lock:
            results.append(r)

    threads = [threading.Thread(target=go) for _ in range(64)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    assert Counter(results) == {Attempt.WRONG: MAX_FAILURES, Attempt.THROTTLED: 64 - MAX_FAILURES}
```

### `tests/test_login.py`

SHA-256 `f6ce2fa96090546e7cc7bee9bb5c49da32e8f59f9a1d579898496dc060fd9b3e`, 11367 bytes.

```python
"""Step 2: the single shared login (PRD Section 6, "Login"), with the fixes for
the second-model review of step 2 (findings 2, 3, 4 and 6)."""
import base64
import json
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import itsdangerous.timed
import pytest
from fastapi.testclient import TestClient

from hypocurate.config import ConfigError, Settings, load_settings
from hypocurate.db.engine import make_engine
from hypocurate.web.app import SESSION_COOKIE, SESSION_MAX_AGE, create_app
from hypocurate.web.login_throttle import MAX_FAILURES, LoginThrottle

PASSWORD = "test-password-not-a-secret"
SECRET = "s" * 40
UNREACHABLE_DB = "postgresql://nobody:planted-pw-7319@127.0.0.1:1/none"
# Paths that only look like the public ones (review finding 3).
LOOKALIKES = ["/loginx", "/login-admin", "/login/admin", "/healthz", "/health-private",
              "/health/export", "/staticx", "/static"]


def settings(env="development", password=PASSWORD, secret=SECRET):
    return Settings(env=env, database_url=UNREACHABLE_DB, password=password,
                    session_secret=secret, version="test")


def make_app(env="development", throttle=None, password=PASSWORD, secret=SECRET):
    s = settings(env, password, secret)
    app = create_app(s, engine=make_engine(s.database_url), login_throttle=throttle)
    for path in LOOKALIKES:
        app.add_api_route(path, lambda: {"protected": True}, methods=["GET"])
    return app


def client(env="development", throttle=None, app=None):
    base = "https://testserver" if env == "production" else "http://testserver"
    return TestClient(app or make_app(env, throttle), base_url=base, follow_redirects=False)


def sign_in(c, password=PASSWORD):
    return c.post("/login", data={"password": password})


def cookie_payload(value):
    """The session cookie is base64(JSON) . timestamp . signature; return the JSON."""
    return json.loads(base64.b64decode(value.split(".")[0]))


# --- which paths need the login ----------------------------------------------------

def test_pages_redirect_to_login_when_signed_out():
    c = client()
    for path in ["/", "/anything", "/runs/1"]:
        r = c.get(path)
        assert r.status_code == 303 and r.headers["location"] == "/login"


def test_login_page_and_static_are_public():
    c = client()
    assert c.get("/login").status_code == 200
    assert c.get("/static/style.css").status_code == 200


@pytest.mark.parametrize("path", LOOKALIKES)
def test_lookalike_paths_are_protected(path):
    """Only /login and /health exactly, and files under /static/, are public."""
    c = client()
    r = c.get(path)
    assert r.status_code == 303 and r.headers["location"] == "/login"
    sign_in(c)
    if path == "/static":
        return  # the static mount answers here once signed in; the point is the redirect above
    assert c.get(path).json() == {"protected": True}


def test_no_api_docs_before_or_after_login():
    c = client()
    paths = ["/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"]
    for path in paths:
        assert c.get(path).status_code == 303
    sign_in(c)
    for path in paths:
        assert c.get(path).status_code == 404, path


# --- password -----------------------------------------------------------------------

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


# --- the cookie ---------------------------------------------------------------------

def test_cookie_holds_only_the_signed_in_flag():
    c = client()
    sign_in(c)
    assert cookie_payload(c.cookies[SESSION_COOKIE]) == {"signed_in": True}


def test_tampered_cookie_is_rejected():
    c = client()
    sign_in(c)
    value = c.cookies[SESSION_COOKIE]
    c.cookies.clear()
    c.cookies.set(SESSION_COOKIE, value[:-2] + ("AA" if value[-2:] != "AA" else "BB"))
    assert c.get("/").status_code == 303


def test_forged_payload_with_old_signature_is_rejected():
    c = client()
    sign_in(c)
    _, ts, sig = c.cookies[SESSION_COOKIE].split(".")
    forged = base64.b64encode(json.dumps({"signed_in": True, "role": "admin"}).encode()).decode()
    c.cookies.clear()
    c.cookies.set(SESSION_COOKIE, f"{forged}.{ts}.{sig}")
    assert c.get("/").status_code == 303


def test_cookie_signed_with_another_secret_is_rejected():
    forger = client(app=make_app(secret="o" * 40))
    sign_in(forger)
    c = client()
    c.cookies.set(SESSION_COOKIE, forger.cookies[SESSION_COOKIE])
    assert c.get("/").status_code == 303


def test_production_cookie_is_secure_httponly_lax_with_max_age():
    c = client("production")
    header = sign_in(c).headers["set-cookie"].lower()
    assert "secure" in header
    assert "httponly" in header
    assert "samesite=lax" in header
    assert f"max-age={SESSION_MAX_AGE}" in header


def test_password_is_not_in_pages():
    c = client()
    sign_in(c)
    assert PASSWORD not in c.get("/").text
    assert PASSWORD not in c.get("/login").text


# --- sessions: rotation, expiry, copied cookie (review finding 4) ----------------------

def test_rotating_the_secret_and_password_ends_existing_sessions():
    """How to revoke access (README, "Sessions"): change SESSION_SECRET with the password."""
    old = client()
    sign_in(old)
    cookie = old.cookies[SESSION_COOKIE]
    rotated = client(app=make_app(password="a-new-password-after-rotation", secret="n" * 40))
    rotated.cookies.set(SESSION_COOKIE, cookie)
    assert rotated.get("/").status_code == 303
    assert sign_in(rotated, PASSWORD).status_code == 401
    assert sign_in(rotated, "a-new-password-after-rotation").status_code == 303


def test_changing_only_the_password_does_not_end_sessions():
    """Stated limitation: the password alone is not in the cookie, so the secret must rotate too."""
    old = client()
    sign_in(old)
    new = client(app=make_app(password="a-new-password-after-rotation"))
    new.cookies.set(SESSION_COOKIE, old.cookies[SESSION_COOKIE])
    assert new.get("/").status_code == 200


def test_session_expires_after_max_age(monkeypatch):
    now = {"t": 1_800_000_000}
    monkeypatch.setattr(itsdangerous.timed.TimestampSigner, "get_timestamp", lambda self: now["t"])
    c = client()
    sign_in(c)
    now["t"] += SESSION_MAX_AGE - 60
    assert c.get("/").status_code == 200
    now["t"] += 61
    assert c.get("/").status_code == 303


def test_copied_cookie_still_works_after_logout():
    """Stated limitation of cookie-only sessions (no session table in sprint 1):
    logout clears this browser's cookie but cannot revoke a copy. A copy works
    until it expires (SESSION_MAX_AGE) or SESSION_SECRET is rotated."""
    original = client()
    sign_in(original)
    copy = client()
    copy.cookies.set(SESSION_COOKIE, original.cookies[SESSION_COOKIE])
    original.post("/logout")
    assert original.get("/").status_code == 303
    assert copy.get("/").status_code == 200


# --- throttling of failed logins (review finding 2) --------------------------------------

def test_wrong_attempts_beyond_the_bound_are_refused_quickly():
    c = client(throttle=LoginThrottle())
    codes = [sign_in(c, "wrong-password").status_code for _ in range(MAX_FAILURES + 3)]
    assert codes == [401] * MAX_FAILURES + [429] * 3


def test_correct_password_is_accepted_while_throttled():
    c = client(throttle=LoginThrottle())
    for _ in range(MAX_FAILURES + 3):
        sign_in(c, "wrong-password")
    r = sign_in(c)
    assert r.status_code == 303
    assert c.get("/").status_code == 200


def test_concurrent_wrong_attempts_respect_the_bound():
    """Fifty simultaneous wrong attempts through the web app: exactly MAX_FAILURES are
    counted, the rest refused; a correct login in the middle of them still succeeds."""
    app = make_app(throttle=LoginThrottle())
    start = threading.Barrier(10)  # 50 attempts = 5 full groups released together

    def wrong(_):
        c = client(app=app)
        try:
            start.wait(timeout=5)
        except threading.BrokenBarrierError:
            pass
        return sign_in(c, "wrong-password").status_code

    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(wrong, i) for i in range(50)]
        right = client(app=app)
        right_code = sign_in(right).status_code
        codes = Counter(f.result() for f in futures)
    assert codes == {401: MAX_FAILURES, 429: 50 - MAX_FAILURES}
    assert right_code == 303
    assert right.get("/").status_code == 200


# --- settings -----------------------------------------------------------------------

GOOD = {"HYPOCURATE_ENV": "production", "DATABASE_URL": "postgresql://u:planted-pw-7319@h/d",
        "HYPOCURATE_PASSWORD": "p" * 24, "SESSION_SECRET": SECRET}


def test_settings_load_when_complete():
    assert load_settings(GOOD).production


@pytest.mark.parametrize("missing", ["DATABASE_URL", "HYPOCURATE_PASSWORD", "SESSION_SECRET"])
def test_web_refuses_to_start_without_a_secret(missing):
    env = {k: v for k, v in GOOD.items() if k != missing}
    with pytest.raises(ConfigError, match=missing):
        load_settings(env)


def test_production_password_must_be_at_least_24_characters():
    with pytest.raises(ConfigError, match="HYPOCURATE_PASSWORD must be at least 24"):
        load_settings({**GOOD, "HYPOCURATE_PASSWORD": "p" * 23})
    assert load_settings({**GOOD, "HYPOCURATE_PASSWORD": "p" * 24}).production


def test_development_password_must_be_at_least_12_characters():
    dev = {**GOOD, "HYPOCURATE_ENV": "development"}
    with pytest.raises(ConfigError, match="HYPOCURATE_PASSWORD must be at least 12"):
        load_settings({**dev, "HYPOCURATE_PASSWORD": "p" * 11})
    assert not load_settings({**dev, "HYPOCURATE_PASSWORD": "p" * 12}).production


def test_web_refuses_a_short_session_secret():
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
    assert "p" * 24 not in text and SECRET not in text and "planted-pw-7319" not in text
```

### `tests/test_skeleton.py`

SHA-256 `da3a08bb6836ad28d6dab6d8450b6bc0fcdbc4074b4900150f499e00448b159d`, 14412 bytes.

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


def test_every_env_file_is_ignored_by_git_and_docker():
    """Review finding 5: .env.production, backups and the like too; only the template passes."""
    for ignore in (".gitignore", ".dockerignore"):
        lines = [l.strip() for l in read(ignore).splitlines()]
        assert ".env*" in lines and "!.env.example" in lines, ignore
        assert lines.index(".env*") < lines.index("!.env.example"), ignore


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

def dockerfile_stages(text=None):
    """The stages in order, as (name, parent, body)."""
    out = []
    for part in re.split(r"^FROM ", text or read("Dockerfile"), flags=re.M)[1:]:
        parent, name = re.match(r"(\S+) AS (\w+)", part.splitlines()[0]).groups()
        out.append((name, parent, part))
    return out


def stages():
    return {name: body for name, _, body in dockerfile_stages()}


def default_image(text=None):
    """What a plain `docker build .` (Render) produces: the LAST stage and every stage
    it is built FROM, with all the sources they COPY in, in build order."""
    found = dockerfile_stages(text)
    by_name = {name: (parent, body) for name, parent, body in found}
    chain, sources, name = [], [], found[-1][0]
    while name in by_name:
        parent, body = by_name[name]
        chain.append(name)
        stage_sources = []
        for args in re.findall(r"^COPY (.+)$", body, re.M):
            stage_sources += [a for a in args.split() if not a.startswith("--")][:-1]
        sources = stage_sources + sources
        name = parent
    return chain, sources


def default_image_problems(text=None):
    chain, sources = default_image(text)
    problems = []
    if chain[0] != "runtime":
        problems.append(f"the default (last) stage is {chain[0]!r}, not 'runtime'")
    if sources != ["requirements.lock", "hypocurate/", "data/"]:
        problems.append(f"the default image copies {sources}")
    return problems


def test_base_images_are_pinned_by_digest():
    froms = re.findall(r"^FROM (\S+)", read("Dockerfile"), re.M)
    assert froms[0].startswith("python:3.14-slim@sha256:")
    assert re.search(r"image: postgres:17@sha256:[0-9a-f]{64}", read("docker-compose.yml"))


def test_default_image_is_the_clean_runtime_stage():
    """Review finding 1: Render builds the last stage. It must be the runtime stage, and
    neither it nor any stage it is built from may copy tests/, docs/ or the whole repository."""
    assert default_image_problems() == []
    assert default_image()[0] == ["runtime", "base"]


def test_default_image_check_catches_the_old_layout():
    """The step 2 Dockerfile as first reviewed (test stage last) fails the check above."""
    old = """FROM python:3.14-slim AS runtime
COPY requirements.lock ./
COPY hypocurate/ hypocurate/
COPY data/ data/
CMD ["sh", "-c", "exec uvicorn hypocurate.web.main:app"]
FROM runtime AS test
COPY requirements-dev.lock ./
COPY . .
CMD ["pytest", "-q"]
"""
    problems = default_image_problems(old)
    assert any("not 'runtime'" in p for p in problems)
    assert any("'.'" in p for p in problems)


def test_default_image_serves_the_web_by_default():
    final_name, _, final_body = dockerfile_stages()[-1]
    cmds = re.findall(r"^CMD (.+)$", final_body, re.M)
    assert final_name == "runtime" and len(cmds) == 1
    assert "uvicorn hypocurate.web.main:app" in cmds[0]


def test_installs_require_hashes():
    installs = re.findall(r"pip install (.*)", read("Dockerfile"))
    assert len(installs) == 2 and all("--require-hashes" in i for i in installs)


def test_image_runs_as_non_root():
    for name, body in stages().items():
        users = re.findall(r"^USER (\S+)", body, re.M)
        assert users and users[-1] == "app", name


def test_web_runs_one_process():
    """The login throttle is kept in memory, so it holds only with one web process."""
    assert "--workers 1" in stages()["runtime"]


# --- Docker Compose (review finding 5) ------------------------------------------------

COMPOSE_ENV = {
    "db": {"POSTGRES_USER", "POSTGRES_DB", "POSTGRES_PASSWORD"},
    "web": {"HYPOCURATE_ENV", "DATABASE_URL", "HYPOCURATE_PASSWORD", "SESSION_SECRET"},
    "worker": {"HYPOCURATE_ENV", "DATABASE_URL"},
    "test": {"DATABASE_URL", "HYPOCURATE_PASSWORD", "SESSION_SECRET", "POSTGRES_PASSWORD"},
}


def compose():
    return yaml.safe_load(read("docker-compose.yml"))["services"]


def test_compose_has_web_worker_database_and_test():
    services = compose()
    assert set(services) == set(COMPOSE_ENV)
    assert services["worker"]["command"] == ["python", "-m", "hypocurate.worker"]
    assert services["web"]["build"]["target"] == services["worker"]["build"]["target"] == "runtime"
    assert services["test"]["build"]["target"] == "test"


def test_compose_gives_each_service_only_its_variables():
    for name, service in compose().items():
        assert "env_file" not in service, name
        assert set(service["environment"]) == COMPOSE_ENV[name], name


def test_compose_takes_secret_values_from_env_only():
    for name, service in compose().items():
        env = service["environment"]
        for key in {"HYPOCURATE_PASSWORD", "SESSION_SECRET", "POSTGRES_PASSWORD"} & set(env):
            assert env[key].startswith("${" + key + ":?"), (name, key)
        if "DATABASE_URL" in env:
            assert "${POSTGRES_PASSWORD:?" in env["DATABASE_URL"], name


def test_compose_ports_are_bound_to_localhost():
    ports = [p for s in compose().values() for p in s.get("ports", [])]
    assert ports and all(p.startswith("127.0.0.1:") for p in ports)


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


# --- GitHub Actions (review finding 6) -------------------------------------------------
# Render counts a skipped or neutral check as passed, so nothing may be skippable.

REQUIRED_STEPS = {
    "Build the default image exactly as Render does": "docker build --file ./Dockerfile --tag hypocurate:default .",
    "Check the default image holds no tests, docs or answers": "python scripts/check_runtime_image.py /image",
    "Check no environment file reached an image": "hypocurate:default hypocurate:test",
    "Run the suite in the test image": "docker compose run --rm test",
    "Smoke-test the default image's default command": "hypocurate:default",
    "Start web, worker and database with Compose; check /health": "/health",
}


def workflow():
    return yaml.safe_load(read(".github/workflows/tests.yml"))


def test_ci_runs_on_every_push_and_pull_request_without_filters():
    triggers = workflow()[True]  # YAML 1.1 reads the key "on" as True
    assert triggers == {"push": None, "pull_request": None}


def test_ci_has_every_required_step():
    steps = {s.get("name"): s.get("run", "") for s in workflow()["jobs"]["tests"]["steps"]}
    for name, command in REQUIRED_STEPS.items():
        assert name in steps, name
        assert command in steps[name], name


def test_ci_nothing_can_be_skipped_or_allowed_to_fail():
    wf = workflow()
    assert "continue-on-error" not in read(".github/workflows/tests.yml")
    assert list(wf["jobs"]) == ["tests"]
    job = wf["jobs"]["tests"]
    assert "if" not in job and "strategy" not in job
    assert "defaults" not in wf and "defaults" not in job  # keep GitHub's `bash -eo pipefail`
    for step in job["steps"]:
        assert "shell" not in step, step.get("name")
        if "if" in step:
            assert (step["name"], step["if"]) == ("Logs", "always()")


def test_suite_command_runs_everything():
    """The test image runs plain pytest: no marker, -k or path filter can drop tests."""
    assert re.search(r'^CMD \["pytest", "-q"\]$', stages()["test"], re.M)
    assert "command" not in compose()["test"]  # `docker compose run --rm test` uses that CMD


def test_ci_actions_are_pinned_to_a_commit():
    uses = re.findall(r"uses: (\S+)", read(".github/workflows/tests.yml"))
    assert uses and all(re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", u) for u in uses)
```

### `README.md`

SHA-256 `ebe6100a257805a1485af19eebf999ec843b69d7fc1d249045847fef9b1b100d`, 5091 bytes.

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
- Failed logins are throttled: after 5 wrong passwords within 15 minutes, further wrong attempts are refused at once (429) until the window passes. The correct password is always accepted, so nobody can lock the owner out. The throttle bounds load; it does not slow guessing. The protection against guessing is the long, random password.

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

## 4. Test output

`.venv/bin/pytest -v` in the Codespace (Python 3.14.2) against the Compose database:

```
============================= test session starts ==============================
platform linux -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0 -- ./.venv/bin/python3
cachedir: .pytest_cache
rootdir: .
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1
collecting ... collected 188 items

tests/test_check_runtime_image.py::test_clean_image_passes PASSED        [  0%]
tests/test_check_runtime_image.py::test_forbidden_paths_fail[tests/test_login.py] PASSED [  1%]
tests/test_check_runtime_image.py::test_forbidden_paths_fail[docs/reviews/step02_summary.md] PASSED [  1%]
tests/test_check_runtime_image.py::test_forbidden_paths_fail[data/controlled_duplicates/truth.csv] PASSED [  2%]
tests/test_check_runtime_image.py::test_forbidden_paths_fail[hypocurate/fixtures/build.py] PASSED [  2%]
tests/test_check_runtime_image.py::test_forbidden_paths_fail[scripts/check_runtime_image.py] PASSED [  3%]
tests/test_check_runtime_image.py::test_forbidden_paths_fail[conftest.py] PASSED [  3%]
tests/test_check_runtime_image.py::test_whole_repository_copy_fails PASSED [  4%]
tests/test_check_runtime_image.py::test_row_answer_in_package_fails PASSED [  4%]
tests/test_check_runtime_image.py::test_outcome_vocabulary_under_data_fails PASSED [  5%]
tests/test_check_runtime_image.py::test_missing_server_fails PASSED      [  5%]
tests/test_controlled_duplicates.py::test_rebuild_gives_identical_bytes PASSED [  6%]
tests/test_controlled_duplicates.py::test_extract_fingerprint_is_in_the_manifest PASSED [  6%]
tests/test_controlled_duplicates.py::test_truth_fingerprint PASSED       [  7%]
tests/test_controlled_duplicates.py::test_answer_material_is_not_under_data_or_the_package PASSED [  7%]
tests/test_controlled_duplicates.py::test_no_expected_outcomes_under_data PASSED [  8%]
tests/test_controlled_duplicates.py::test_no_row_answers_under_package PASSED [  9%]
tests/test_controlled_duplicates.py::test_manifest_points_to_nothing_holding_answers PASSED [  9%]
tests/test_controlled_duplicates.py::test_extract_carries_no_answer_columns PASSED [ 10%]
tests/test_controlled_duplicates.py::test_one_answer_per_extract_row PASSED [ 10%]
tests/test_controlled_duplicates.py::test_every_case_is_present_twice PASSED [ 11%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row1-exact_duplicate_verbatim] PASSED [ 11%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row2-exact_duplicate_verbatim] PASSED [ 12%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row3-exact_duplicate_renamed_alloy] PASSED [ 12%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row4-exact_duplicate_renamed_alloy] PASSED [ 13%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row5-possible_duplicate_unknown_paper] PASSED [ 13%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row6-possible_duplicate_unknown_paper] PASSED [ 14%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row7-not_duplicate_value_differs] PASSED [ 14%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row8-not_duplicate_value_differs] PASSED [ 15%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row9-not_duplicate_other_paper] PASSED [ 15%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row10-not_duplicate_other_paper] PASSED [ 16%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row11-not_duplicate_other_temperature] PASSED [ 17%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row12-not_duplicate_other_temperature] PASSED [ 17%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row13-missing_test_condition] PASSED [ 18%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row14-missing_test_condition] PASSED [ 18%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row15-not_duplicate_other_test_type] PASSED [ 19%]
tests/test_controlled_duplicates.py::test_row_differs_from_its_source_in_exactly_the_stated_columns[row16-not_duplicate_other_test_type] PASSED [ 19%]
tests/test_controlled_duplicates.py::test_source_rows_are_in_reference_scope PASSED [ 20%]
tests/test_controlled_duplicates.py::test_verbatim_duplicates_are_byte_identical_lines PASSED [ 20%]
tests/test_controlled_duplicates.py::test_renamed_alloys_have_the_same_composition PASSED [ 21%]
tests/test_controlled_duplicates.py::test_unknown_paper_rows_have_no_reference PASSED [ 21%]
tests/test_controlled_duplicates.py::test_other_paper_rows_use_constructed_dois_not_found_in_mpea PASSED [ 22%]
tests/test_controlled_duplicates.py::test_changed_values_are_as_stated PASSED [ 22%]
tests/test_controlled_duplicates.py::test_missing_test_condition_rows_keep_their_paper PASSED [ 23%]
tests/test_controlled_duplicates.py::test_other_test_type_rows_are_compression_copies_of_tension_records PASSED [ 23%]
tests/test_controlled_duplicates.py::test_no_row_is_labelled_out_of_scope_while_entering_the_analysis PASSED [ 24%]
tests/test_controlled_duplicates.py::test_tension_only_handling_differs_only_for_compression_rows PASSED [ 25%]
tests/test_controlled_duplicates.py::test_expected_handling[row1-exact_duplicate_verbatim] PASSED [ 25%]
tests/test_controlled_duplicates.py::test_expected_handling[row2-exact_duplicate_verbatim] PASSED [ 26%]
tests/test_controlled_duplicates.py::test_expected_handling[row3-exact_duplicate_renamed_alloy] PASSED [ 26%]
tests/test_controlled_duplicates.py::test_expected_handling[row4-exact_duplicate_renamed_alloy] PASSED [ 27%]
tests/test_controlled_duplicates.py::test_expected_handling[row5-possible_duplicate_unknown_paper] PASSED [ 27%]
tests/test_controlled_duplicates.py::test_expected_handling[row6-possible_duplicate_unknown_paper] PASSED [ 28%]
tests/test_controlled_duplicates.py::test_expected_handling[row7-not_duplicate_value_differs] PASSED [ 28%]
tests/test_controlled_duplicates.py::test_expected_handling[row8-not_duplicate_value_differs] PASSED [ 29%]
tests/test_controlled_duplicates.py::test_expected_handling[row9-not_duplicate_other_paper] PASSED [ 29%]
tests/test_controlled_duplicates.py::test_expected_handling[row10-not_duplicate_other_paper] PASSED [ 30%]
tests/test_controlled_duplicates.py::test_expected_handling[row11-not_duplicate_other_temperature] PASSED [ 30%]
tests/test_controlled_duplicates.py::test_expected_handling[row12-not_duplicate_other_temperature] PASSED [ 31%]
tests/test_controlled_duplicates.py::test_expected_handling[row13-missing_test_condition] PASSED [ 31%]
tests/test_controlled_duplicates.py::test_expected_handling[row14-missing_test_condition] PASSED [ 32%]
tests/test_controlled_duplicates.py::test_expected_handling[row15-not_duplicate_other_test_type] PASSED [ 32%]
tests/test_controlled_duplicates.py::test_expected_handling[row16-not_duplicate_other_test_type] PASSED [ 33%]
tests/test_controlled_duplicates.py::test_unknown_paper_is_flagged_as_possible_duplicate_kept_not_removed PASSED [ 34%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row1-exact_duplicate_verbatim] PASSED [ 34%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row2-exact_duplicate_verbatim] PASSED [ 35%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row3-exact_duplicate_renamed_alloy] PASSED [ 35%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row4-exact_duplicate_renamed_alloy] PASSED [ 36%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row5-possible_duplicate_unknown_paper] PASSED [ 36%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row6-possible_duplicate_unknown_paper] PASSED [ 37%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row7-not_duplicate_value_differs] PASSED [ 37%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row8-not_duplicate_value_differs] PASSED [ 38%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row9-not_duplicate_other_paper] PASSED [ 38%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row10-not_duplicate_other_paper] PASSED [ 39%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row11-not_duplicate_other_temperature] PASSED [ 39%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row12-not_duplicate_other_temperature] PASSED [ 40%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row13-missing_test_condition] PASSED [ 40%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row14-missing_test_condition] PASSED [ 41%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row15-not_duplicate_other_test_type] PASSED [ 42%]
tests/test_controlled_duplicates.py::test_survivor_is_stated[row16-not_duplicate_other_test_type] PASSED [ 42%]
tests/test_frozen_sources.py::test_manifest_itself_is_unchanged PASSED   [ 43%]
tests/test_frozen_sources.py::test_manifest_covers_exactly_the_required_files PASSED [ 43%]
tests/test_frozen_sources.py::test_required_file_is_present[data/controlled_duplicates/extract.csv] PASSED [ 44%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/mpea/LICENSE] PASSED [ 44%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/mpea/MPEA_dataset.csv] PASSED [ 45%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx] PASSED [ 45%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/tamu_fcc/LICENSE] PASSED [ 46%]
tests/test_frozen_sources.py::test_required_file_is_present[data/sources/tamu_fcc/inputs.csv] PASSED [ 46%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/mpea/MPEA_dataset.csv] PASSED [ 47%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/mpea/LICENSE] PASSED [ 47%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx] PASSED [ 48%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/inputs.csv] PASSED [ 48%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/sources/tamu_fcc/LICENSE] PASSED [ 49%]
tests/test_frozen_sources.py::test_frozen_file_matches_its_fingerprint[data/controlled_duplicates/extract.csv] PASSED [ 50%]
tests/test_frozen_sources.py::test_verify_reports_no_problems PASSED     [ 50%]
tests/test_frozen_sources.py::test_verify_detects_a_changed_byte PASSED  [ 51%]
tests/test_frozen_sources.py::test_both_sources_are_in_the_manifest PASSED [ 51%]
tests/test_frozen_sources.py::test_manifest_records_origin_date_and_licence[mpea] PASSED [ 52%]
tests/test_frozen_sources.py::test_manifest_records_origin_date_and_licence[tamu_fcc] PASSED [ 52%]
tests/test_frozen_sources.py::test_licence_texts_match_the_manifest PASSED [ 53%]
tests/test_frozen_sources.py::test_tamu_origin_is_the_zenodo_record PASSED [ 53%]
tests/test_frozen_sources.py::test_mpea_counts PASSED                    [ 54%]
tests/test_frozen_sources.py::test_tamu_counts PASSED                    [ 54%]
tests/test_frozen_sources.py::test_tamu_csv_view_agrees_with_the_spreadsheet PASSED [ 55%]
tests/test_health.py::test_health_without_login_database_up PASSED       [ 55%]
tests/test_health.py::test_health_page_in_a_browser PASSED               [ 56%]
tests/test_health.py::test_health_reports_database_down_without_crashing PASSED [ 56%]
tests/test_health.py::test_health_shows_no_secrets PASSED                [ 57%]
tests/test_health.py::test_worker_idles_and_checks_the_database PASSED   [ 57%]
tests/test_health.py::test_worker_logs_an_unreachable_database PASSED    [ 58%]
tests/test_health.py::test_cli_check_db PASSED                           [ 59%]
tests/test_login.py::test_pages_redirect_to_login_when_signed_out PASSED [ 59%]
tests/test_login.py::test_login_page_and_static_are_public PASSED        [ 60%]
tests/test_login.py::test_lookalike_paths_are_protected[/loginx] PASSED  [ 60%]
tests/test_login.py::test_lookalike_paths_are_protected[/login-admin] PASSED [ 61%]
tests/test_login.py::test_lookalike_paths_are_protected[/login/admin] PASSED [ 61%]
tests/test_login.py::test_lookalike_paths_are_protected[/healthz] PASSED [ 62%]
tests/test_login.py::test_lookalike_paths_are_protected[/health-private] PASSED [ 62%]
tests/test_login.py::test_lookalike_paths_are_protected[/health/export] PASSED [ 63%]
tests/test_login.py::test_lookalike_paths_are_protected[/staticx] PASSED [ 63%]
tests/test_login.py::test_lookalike_paths_are_protected[/static] PASSED  [ 64%]
tests/test_login.py::test_no_api_docs_before_or_after_login PASSED       [ 64%]
tests/test_login.py::test_wrong_password_is_refused_and_gives_no_session PASSED [ 65%]
tests/test_login.py::test_empty_password_is_refused PASSED               [ 65%]
tests/test_login.py::test_right_password_gives_a_session PASSED          [ 66%]
tests/test_login.py::test_logout_ends_the_session PASSED                 [ 67%]
tests/test_login.py::test_cookie_holds_only_the_signed_in_flag PASSED    [ 67%]
tests/test_login.py::test_tampered_cookie_is_rejected PASSED             [ 68%]
tests/test_login.py::test_forged_payload_with_old_signature_is_rejected PASSED [ 68%]
tests/test_login.py::test_cookie_signed_with_another_secret_is_rejected PASSED [ 69%]
tests/test_login.py::test_production_cookie_is_secure_httponly_lax_with_max_age PASSED [ 69%]
tests/test_login.py::test_password_is_not_in_pages PASSED                [ 70%]
tests/test_login.py::test_rotating_the_secret_and_password_ends_existing_sessions PASSED [ 70%]
tests/test_login.py::test_changing_only_the_password_does_not_end_sessions PASSED [ 71%]
tests/test_login.py::test_session_expires_after_max_age PASSED           [ 71%]
tests/test_login.py::test_copied_cookie_still_works_after_logout PASSED  [ 72%]
tests/test_login.py::test_wrong_attempts_beyond_the_bound_are_refused_quickly PASSED [ 72%]
tests/test_login.py::test_correct_password_is_accepted_while_throttled PASSED [ 73%]
tests/test_login.py::test_concurrent_wrong_attempts_respect_the_bound PASSED [ 73%]
tests/test_login.py::test_settings_load_when_complete PASSED             [ 74%]
tests/test_login.py::test_web_refuses_to_start_without_a_secret[DATABASE_URL] PASSED [ 75%]
tests/test_login.py::test_web_refuses_to_start_without_a_secret[HYPOCURATE_PASSWORD] PASSED [ 75%]
tests/test_login.py::test_web_refuses_to_start_without_a_secret[SESSION_SECRET] PASSED [ 76%]
tests/test_login.py::test_production_password_must_be_at_least_24_characters PASSED [ 76%]
tests/test_login.py::test_development_password_must_be_at_least_12_characters PASSED [ 77%]
tests/test_login.py::test_web_refuses_a_short_session_secret PASSED      [ 77%]
tests/test_login.py::test_config_errors_never_contain_values PASSED      [ 78%]
tests/test_login.py::test_worker_needs_no_login_secrets PASSED           [ 78%]
tests/test_login.py::test_unknown_env_is_refused PASSED                  [ 79%]
tests/test_login.py::test_settings_repr_hides_secrets PASSED             [ 79%]
tests/test_login_throttle.py::test_defaults_are_as_approved PASSED       [ 80%]
tests/test_login_throttle.py::test_wrong_attempts_counted_up_to_the_bound_then_throttled PASSED [ 80%]
tests/test_login_throttle.py::test_correct_password_always_accepted PASSED [ 81%]
tests/test_login_throttle.py::test_success_does_not_reset_the_count PASSED [ 81%]
tests/test_login_throttle.py::test_throttle_ends_when_failures_leave_the_window PASSED [ 82%]
tests/test_login_throttle.py::test_throttled_attempts_are_not_counted PASSED [ 82%]
tests/test_login_throttle.py::test_concurrent_failures_never_pass_the_bound PASSED [ 83%]
tests/test_skeleton.py::test_layout_matches_prd_6_1 PASSED               [ 84%]
tests/test_skeleton.py::test_env_example_holds_names_only PASSED         [ 84%]
tests/test_skeleton.py::test_every_env_file_is_ignored_by_git_and_docker PASSED [ 85%]
tests/test_skeleton.py::test_no_keys_or_database_passwords_in_files PASSED [ 85%]
tests/test_skeleton.py::test_secret_values_from_the_environment_are_in_no_file PASSED [ 86%]
tests/test_skeleton.py::test_every_lock_line_is_pinned_with_hashes PASSED [ 86%]
tests/test_skeleton.py::test_direct_dependencies_are_locked PASSED       [ 87%]
tests/test_skeleton.py::test_runtime_and_dev_locks_agree PASSED          [ 87%]
tests/test_skeleton.py::test_test_tools_are_not_in_the_runtime_lock PASSED [ 88%]
tests/test_skeleton.py::test_base_images_are_pinned_by_digest PASSED     [ 88%]
tests/test_skeleton.py::test_default_image_is_the_clean_runtime_stage PASSED [ 89%]
tests/test_skeleton.py::test_default_image_check_catches_the_old_layout PASSED [ 89%]
tests/test_skeleton.py::test_default_image_serves_the_web_by_default PASSED [ 90%]
tests/test_skeleton.py::test_installs_require_hashes PASSED              [ 90%]
tests/test_skeleton.py::test_image_runs_as_non_root PASSED               [ 91%]
tests/test_skeleton.py::test_web_runs_one_process PASSED                 [ 92%]
tests/test_skeleton.py::test_compose_has_web_worker_database_and_test PASSED [ 92%]
tests/test_skeleton.py::test_compose_gives_each_service_only_its_variables PASSED [ 93%]
tests/test_skeleton.py::test_compose_takes_secret_values_from_env_only PASSED [ 93%]
tests/test_skeleton.py::test_compose_ports_are_bound_to_localhost PASSED [ 94%]
tests/test_skeleton.py::test_render_describes_web_worker_and_database PASSED [ 94%]
tests/test_skeleton.py::test_render_plans_are_the_approved_ones PASSED   [ 95%]
tests/test_skeleton.py::test_render_deploys_only_after_checks_pass PASSED [ 95%]
tests/test_skeleton.py::test_render_everything_in_one_region_and_database_private PASSED [ 96%]
tests/test_skeleton.py::test_render_holds_no_secret_values PASSED        [ 96%]
tests/test_skeleton.py::test_render_worker_gets_no_login_secrets PASSED  [ 97%]
tests/test_skeleton.py::test_ci_runs_on_every_push_and_pull_request_without_filters PASSED [ 97%]
tests/test_skeleton.py::test_ci_has_every_required_step PASSED           [ 98%]
tests/test_skeleton.py::test_ci_nothing_can_be_skipped_or_allowed_to_fail PASSED [ 98%]
tests/test_skeleton.py::test_suite_command_runs_everything PASSED        [ 99%]
tests/test_skeleton.py::test_ci_actions_are_pinned_to_a_commit PASSED    [100%]

============================= 188 passed in 2.90s ==============================
```
