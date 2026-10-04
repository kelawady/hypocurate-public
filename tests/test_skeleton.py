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
    # 1 GB disk (owner decision, 2026-10-04); Render's default would be 15 GB, which cannot be reduced.
    assert r["databases"][0]["diskSizeGB"] == 1


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
