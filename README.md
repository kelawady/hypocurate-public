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
