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
REQUIRED = ["hypocurate/web/main.py", "hypocurate/worker.py", "data/manifest.json", "requirements.lock",
            # Step 3: Render's pre-deploy command migrates from inside the deployed image.
            "hypocurate/db/migrate.py", "hypocurate/db/migrations/env.py",
            "hypocurate/db/migrations/versions/0001_data_model.py",
            # Step 4: the sources are registered and read from inside the deployed image.
            "hypocurate/sources/versions.py", "hypocurate/sources/adapters/__init__.py",
            "data/sources/mpea/MPEA_dataset.csv", "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx",
            "data/controlled_duplicates/extract.csv",
            # Step 4b: the assumptions register and its page.
            "hypocurate/assumptions.json", "hypocurate/assumptions.py",
            "hypocurate/web/templates/assumptions.html"]
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
