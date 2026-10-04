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
