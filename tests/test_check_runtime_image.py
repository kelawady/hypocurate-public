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


@pytest.mark.parametrize("missing", ["hypocurate/db/migrate.py", "hypocurate/db/migrations/env.py",
                                     "hypocurate/db/migrations/versions/0001_data_model.py"])
def test_missing_migrations_fail(image, missing):
    """Step 3: Render's pre-deploy command runs the migrations from inside the deployed image."""
    (image / missing).unlink()
    assert f"missing {missing}" in check.problems(image)
