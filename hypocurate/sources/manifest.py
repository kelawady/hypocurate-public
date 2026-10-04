"""Fingerprints of the frozen files (PRD Sections 10 and 15, step 1).

`data/manifest.json` records, for every frozen file, its SHA-256, its size, its
licence and its exact origin. `verify` compares the files on disk against it.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "data" / "manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()


def load_manifest(path: Path = MANIFEST_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@dataclass(frozen=True)
class FileEntry:
    group: str  # "sources/<id>" or "controlled_duplicates"
    path: str  # relative to the repository root
    sha256: str
    bytes: int


def file_entries(manifest: dict) -> list[FileEntry]:
    entries = []
    for source_id, source in manifest["sources"].items():
        for f in source["files"]:
            entries.append(FileEntry(f"sources/{source_id}", f["path"], f["sha256"], f["bytes"]))
    for f in manifest["controlled_duplicates"]["files"]:
        entries.append(FileEntry("controlled_duplicates", f["path"], f["sha256"], f["bytes"]))
    return entries


def verify(manifest: dict, root: Path = REPO_ROOT) -> list[str]:
    """Return one message per mismatch; an empty list means every file matches."""
    problems = []
    for e in file_entries(manifest):
        p = root / e.path
        if not p.is_file():
            problems.append(f"{e.path}: missing")
            continue
        size = p.stat().st_size
        if size != e.bytes:
            problems.append(f"{e.path}: size {size} != {e.bytes}")
        digest = sha256_file(p)
        if digest != e.sha256:
            problems.append(f"{e.path}: sha256 {digest} != {e.sha256}")
    return problems
