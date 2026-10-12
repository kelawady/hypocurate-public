"""Registered sources and their sealed versions (PRD Sections 7 and 10; step 4).

Three sources are registered from the frozen files of step 1: the MPEA dataset, the
Texas A&M FCC dataset and the controlled duplicate extract. Each becomes a
`source_version` holding the data files its adapter reads, sealed once (step 3).

The digest and identity are computed here exactly as the database computes them
(`hc_files_digest`, `hc_version_identity` in migration 0001), and the database checks
them again at sealing.

Locking (owner, 2026-10-05, step 4 question 1): `hc_write_lock` covers runs and
hypothesis versions only, and source registration writes neither. Registration
therefore locks the source row first (`SELECT … FOR UPDATE`, after an
`INSERT … ON CONFLICT DO NOTHING` for a new source), then writes the version, its files
and the seal in the same transaction, retried on 40P01 / 40001 (`run_transaction`).
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from sqlalchemy import Connection, Engine, text

from hypocurate.db.retry import run_transaction
from hypocurate.sources.manifest import REPO_ROOT, load_manifest

DATA_DIR = REPO_ROOT / "data"
MAX_FILE_BYTES = 5 * 1024 * 1024  # the source_file CHECK (owner decision, 2026-10-04)
# The source_file path CHECK, in Python, so an unsafe path is refused before the database sees it.
# A data file (0001's rule). Step 8a (migration 0005): the rule by role; a path tells its role.
SAFE_STORED_PATH = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]*[.](csv|xlsx)")
DOCUMENTATION_PATH = re.compile(r"documentation/[A-Za-z0-9][A-Za-z0-9._-]*[.](tex|xml|md|txt)")
CURATION_PATH = "curation.json"
DOCUMENTATION_DIR = "documentation"


def file_role(path: str) -> str:
    """'data', 'documentation' or 'curation', from the path alone (the database's rule by role);
    RegistrationError for a path no role allows."""
    if isinstance(path, str):
        if path == CURATION_PATH:
            return "curation"
        if DOCUMENTATION_PATH.fullmatch(path):
            return "documentation"
        if SAFE_STORED_PATH.fullmatch(path) and not path.startswith(DOCUMENTATION_DIR + "/"):
            return "data"
    raise RegistrationError(f"unsafe stored path {path!r}")


class RegistrationError(Exception):
    """A source cannot be registered as defined (changed file, changed settings, unsafe path)."""


class UnsealedVersion(Exception):
    """A source version that is not sealed, or whose stored bytes do not match its seal."""


# --- Digest and identity (the database's definitions, step 3 item 10) ---------------

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def files_digest(files: Mapping[str, bytes]) -> str:
    """SHA-256 of one line "<sha256>  <path>\\n" per file, sorted by path bytewise
    (the database sorts with COLLATE "C"). The same as `hc_files_digest`."""
    for path in files:
        file_role(path)
    listing = "".join(f"{sha256_hex(files[p])}  {p}\n" for p in sorted(files, key=lambda p: p.encode()))
    return sha256_hex(listing.encode("utf-8"))


def version_identity(digest: str, source_type: str, data_kind: str, grouping_unit: str) -> str:
    """SHA-256 of four lines, each "<name> <value>\\n". The same as `hc_version_identity`."""
    return sha256_hex((f"files {digest}\nsource_type {source_type}\n"
                       f"data_kind {data_kind}\ngrouping_unit {grouping_unit}\n").encode("utf-8"))


# --- Paths --------------------------------------------------------------------------

def safe_path_within(directory: Path, relative: str) -> Path:
    """The path `relative` inside `directory`, after resolving `..` and symbolic links.
    Raises RegistrationError if it is absolute, empty, or leaves the directory.
    Every path read from the manifest goes through this, and so must any stored path
    before it is written to disk (step 3, open item 4)."""
    if not relative or Path(relative).is_absolute() or relative.startswith(("/", "\\")):
        raise RegistrationError(f"path {relative!r} must be relative")
    base = directory.resolve()
    target = (base / relative).resolve()
    if not target.is_relative_to(base):
        raise RegistrationError(f"path {relative!r} leaves {directory}")
    return target


# --- The three sources --------------------------------------------------------------

@dataclass(frozen=True)
class SourceDefinition:
    key: str
    name: str
    source_type: str
    data_kind: str
    grouping_unit: str
    licence: str
    address: str | None
    properties_covered: tuple[str, ...]
    enabled: bool
    directory: str  # relative to data/
    data_files: tuple[str, ...]  # file names inside `directory`, as stored
    version_label: str
    manifest_section: tuple[str, ...]  # where its files are listed in data/manifest.json
    # Constructed test data (step 6): its records enter only a run marked as a test
    # (run.experiment_flags constructed_test_data; register 'constructed_test_runs').
    constructed: bool = False
    # Step 8a (owner, 2026-10-06, Q1): the source's frozen documentation, stored with its data in the
    # sealed version (paths inside `directory`, under documentation/), and, once the owner has
    # accepted the Curator's proposals and the file is frozen, its curation file (curation.json).
    documentation_files: tuple[str, ...] = ()
    curation_file: str | None = None


SOURCES: Mapping[str, SourceDefinition] = MappingProxyType({
    "mpea": SourceDefinition(
        key="mpea", name="MPEA dataset (Borg et al. 2020)", source_type="uploaded_table",
        data_kind="measured", grouping_unit="paper", licence="Apache-2.0",
        address="https://github.com/CitrineInformatics/MPEA_dataset",
        properties_covered=("yield_strength", "ultimate_tensile_strength", "hardness", "grain_size"),
        enabled=True, directory="sources/mpea", data_files=("MPEA_dataset.csv",),
        documentation_files=("documentation/Borg2020_PMC7722748.xml",),
        version_label="commit d31e2510cccc3fb9e79d43ad62652f64ef8c2c5e",
        manifest_section=("sources", "mpea")),
    "tamu_fcc": SourceDefinition(
        key="tamu_fcc", name="Texas A&M FCC dataset (Mulukutla et al. 2026)", source_type="uploaded_table",
        data_kind="measured",
        # PRD 17, open decision 9: one group in sprint 1; batches later if the owner agrees.
        grouping_unit="dataset", licence="MIT",
        address="https://doi.org/10.5281/zenodo.22798856",
        properties_covered=("yield_strength", "hardness", "grain_size"),
        enabled=True, directory="sources/tamu_fcc",
        # The spreadsheet is the source of record (step 1); only files the adapter reads are stored.
        data_files=("Grain_Size_Summary_v3.xlsx",),
        documentation_files=("documentation/main.tex", "documentation/supplementary.tex"),
        # Step 8a: the owner's accepted Curator values (test type, phase class), frozen.
        curation_file="curation.json",
        version_label="v1.1.0, commit 11390ee516c1a17cacdde318b40d5d6889d4007f",
        manifest_section=("sources", "tamu_fcc")),
    "controlled_duplicates": SourceDefinition(
        key="controlled_duplicates",
        name="Controlled duplicate extract (constructed test data; never pooled into a real analysis)",
        source_type="uploaded_table", data_kind="measured", grouping_unit="paper",
        licence="Apache-2.0 (derived from the MPEA dataset)", address=None,
        properties_covered=("yield_strength", "ultimate_tensile_strength", "hardness", "grain_size"),
        # Off by default: constructed data. Its records enter only a run marked as a test (step 6).
        enabled=False, directory="controlled_duplicates", data_files=("extract.csv",),
        version_label="built 2026-10-04 from the MPEA dataset",
        manifest_section=("controlled_duplicates",), constructed=True),
})


def _manifest_files(definition: SourceDefinition, manifest: dict) -> tuple[dict, str]:
    section = manifest
    for part in definition.manifest_section:
        section = section[part]
    obtained = section.get("retrieved") or section.get("built")
    return {f["path"]: f for f in section["files"] + section.get("documentation", []) + section.get("curation", [])}, obtained


def read_definition_files(definition: SourceDefinition, data_dir: Path = DATA_DIR,
                          manifest: dict | None = None) -> tuple[dict[str, bytes], date]:
    """Reads a source's files from disk (its data files, and from step 8a its documentation and any
    curation file), checks each against its manifest entry (SHA-256 and size) and returns
    {stored path: bytes} and the date obtained."""
    from hypocurate.access import file_guard  # here, not at the top: the access layer imports this module
    if file_guard.installed():
        raise RegistrationError("source registration reads data/ and cannot run in a guarded pipeline "
                                "process (step 5)")
    manifest = manifest if manifest is not None else load_manifest(data_dir / "manifest.json")
    listed, obtained = _manifest_files(definition, manifest)
    source_dir = safe_path_within(data_dir, definition.directory)
    files: dict[str, bytes] = {}
    names = definition.data_files + definition.documentation_files + (
        (definition.curation_file,) if definition.curation_file else ())
    for name in names:
        expected = ("data" if name in definition.data_files else
                    "documentation" if name in definition.documentation_files else "curation")
        if file_role(name) != expected:  # raises RegistrationError for a path no role allows
            raise RegistrationError(f"{name!r} is not a {expected} file path")
        path = safe_path_within(source_dir, name)
        manifest_path = f"data/{definition.directory}/{name}"
        entry = listed.get(manifest_path)
        if entry is None:
            raise RegistrationError(f"{manifest_path} is not in the manifest")
        content = path.read_bytes()
        if len(content) != entry["bytes"] or sha256_hex(content) != entry["sha256"]:
            raise RegistrationError(f"{manifest_path} does not match its manifest fingerprint")
        if len(content) > MAX_FILE_BYTES:
            raise RegistrationError(f"{manifest_path} is larger than 5 MiB")
        files[name] = content
    return files, date.fromisoformat(obtained)


# --- Registration -------------------------------------------------------------------

@dataclass(frozen=True)
class Registered:
    key: str
    source_id: int
    version_id: int
    label: str
    files_digest: str
    fingerprint: str
    created: bool  # False: an identical sealed version already existed


INTERPRETATION = ("source_type", "data_kind", "grouping_unit")


def _register_in(conn: Connection, d: SourceDefinition, files: dict[str, bytes], obtained: date,
                 label: str | None = None) -> Registered:
    """Registers and seals a version of `d` holding `files` (or finds the identical sealed one).
    `label`: the version's label (default: the definition's); a curated version names its own."""
    label = label or d.version_label
    if CURATION_PATH in files:  # checked against the files it is sealed with (step 8a review, finding 1)
        from hypocurate.sources.curated import CurationInvalid, check_curation
        try:
            check_curation(files, d.key, d.source_type, d.data_kind, d.grouping_unit)
        except CurationInvalid as error:
            raise RegistrationError(f"{CURATION_PATH}: not a curation of this version ({error})") from None
    digest = files_digest(files)
    identity = version_identity(digest, d.source_type, d.data_kind, d.grouping_unit)
    conn.execute(text(
        "INSERT INTO source (key, name, source_type, address, licence, data_kind, adapter_status, enabled, "
        "grouping_unit, properties_covered) VALUES (:key, :name, :type, :address, :licence, :kind, "
        "'available', :enabled, :unit, :props) ON CONFLICT (key) DO NOTHING"),
        dict(key=d.key, name=d.name, type=d.source_type, address=d.address, licence=d.licence,
             kind=d.data_kind, enabled=d.enabled, unit=d.grouping_unit, props=list(d.properties_covered)))
    # The lock: every registration of this source waits here until the other commits.
    row = conn.execute(text(
        "SELECT id, source_type, data_kind, grouping_unit FROM source WHERE key = :key FOR UPDATE"),
        dict(key=d.key)).one()
    stored = dict(zip(INTERPRETATION, row[1:]))
    expected = {k: getattr(d, k) for k in INTERPRETATION}
    if stored != expected:
        raise RegistrationError(
            f"source {d.key!r} is registered with {stored}, but the code defines {expected}; "
            "a change of interpretation settings is not made silently")
    source_id = row[0]
    existing = conn.execute(text(
        "SELECT id, label, files_digest FROM source_version "
        "WHERE source_id = :s AND fingerprint = :fp AND sealed_at IS NOT NULL"),
        dict(s=source_id, fp=identity)).one_or_none()
    if existing is not None:
        return Registered(d.key, source_id, existing[0], existing[1], existing[2], identity, created=False)
    version_id = conn.execute(text(
        "INSERT INTO source_version (source_id, label, obtained_on) VALUES (:s, :l, :o) RETURNING id"),
        dict(s=source_id, l=label, o=obtained)).scalar_one()
    for path in sorted(files):
        conn.execute(text(
            "INSERT INTO source_file (source_version_id, path, sha256, content, role) VALUES (:v, :p, :h, :c, :r)"),
            dict(v=version_id, p=path, h=sha256_hex(files[path]), c=files[path], r=file_role(path)))
    sealed = conn.execute(text(
        "UPDATE source_version SET sealed_at = now(), fingerprint = :fp WHERE id = :v "
        "RETURNING files_digest, fingerprint"), dict(v=version_id, fp=identity)).one()
    if sealed[0] != digest or sealed[1] != identity:
        raise RegistrationError("the database's files digest differs from the one computed here")
    return Registered(d.key, source_id, version_id, label, digest, identity, created=True)


def register(engine: Engine, key: str, data_dir: Path = DATA_DIR, manifest: dict | None = None, *,
             by: str | None = None, via: str = "command line") -> Registered:
    """Registers source `key` and seals its version, or returns the identical sealed
    version if it is already registered. One transaction, retried on 40P01 / 40001.
    Step 10b, fix round 1: a version sealed here is recorded in `action_record` with the name
    given (`by`; required on the website) in the same transaction; finding it already
    registered writes nothing."""
    from hypocurate.db import actions
    if key not in SOURCES:
        raise RegistrationError(f"unknown source {key!r}; known: {', '.join(SOURCES)}")
    actions.actor(by, via)
    d = SOURCES[key]
    files, obtained = read_definition_files(d, data_dir, manifest)

    def body(conn: Connection) -> Registered:
        done = _register_in(conn, d, files, obtained)
        if done.created:
            actions.record(conn, "register_source", by, via, source_version=done.version_id)
        return done

    return run_transaction(engine, body)


# --- Loading a sealed version for an adapter ----------------------------------------

@dataclass(frozen=True)
class SealedVersion:
    """A sealed source version with its file bytes, as an adapter receives it."""
    id: int
    source_key: str
    label: str
    source_type: str
    data_kind: str
    grouping_unit: str
    sealed_at: datetime | None
    files_digest: str
    fingerprint: str
    files: Mapping[str, bytes]

    def __post_init__(self):
        object.__setattr__(self, "files", MappingProxyType(dict(self.files)))

    @property
    def data_files(self) -> Mapping[str, bytes]:
        """The files an adapter reads (step 8a: a version may also hold documentation and curation)."""
        return MappingProxyType({p: c for p, c in self.files.items() if file_role(p) == "data"})

    @property
    def documentation(self) -> Mapping[str, bytes]:
        """The source's own documentation, which the Curator reads (step 8a)."""
        return MappingProxyType({p: c for p, c in self.files.items() if file_role(p) == "documentation"})

    def verify(self) -> None:
        """Raises UnsealedVersion unless the version is sealed and its bytes give exactly
        its stored files digest and identity. Every adapter calls this before parsing."""
        if self.sealed_at is None:
            raise UnsealedVersion(f"source version {self.id} is not sealed")
        if files_digest(self.files) != self.files_digest:
            raise UnsealedVersion(f"source version {self.id}: files do not match the sealed files digest")
        if version_identity(self.files_digest, self.source_type, self.data_kind,
                            self.grouping_unit) != self.fingerprint:
            raise UnsealedVersion(f"source version {self.id}: settings do not match the sealed identity")


def load_sealed_version(conn: Connection, version_id: int) -> SealedVersion:
    """Loads a version and its files. Refuses an unsealed version, and checks each file's
    bytes against its stored SHA-256 and the whole against the seal."""
    row = conn.execute(text(
        "SELECT sv.id, s.key, sv.label, sv.source_type, sv.data_kind, sv.grouping_unit, sv.sealed_at, "
        "sv.files_digest, sv.fingerprint FROM source_version sv JOIN source s ON s.id = sv.source_id "
        "WHERE sv.id = :v"), dict(v=version_id)).one_or_none()
    if row is None:
        raise UnsealedVersion(f"no source version {version_id}")
    if row.sealed_at is None:
        raise UnsealedVersion(f"source version {version_id} is not sealed")
    files = {}
    for path, sha, content in conn.execute(text(
            "SELECT path, sha256, content FROM source_file WHERE source_version_id = :v"), dict(v=version_id)):
        content = bytes(content)
        if sha256_hex(content) != sha:
            raise UnsealedVersion(f"source version {version_id}: {path} does not match its SHA-256")
        files[path] = content
    version = SealedVersion(row.id, row.key, row.label, row.source_type, row.data_kind, row.grouping_unit,
                            row.sealed_at, row.files_digest, row.fingerprint, files)
    version.verify()
    return version


def latest_sealed_version_id(conn: Connection, key: str) -> int:
    """The most recently sealed version of source `key`."""
    vid = conn.execute(text(
        "SELECT sv.id FROM source_version sv JOIN source s ON s.id = sv.source_id "
        "WHERE s.key = :k AND sv.sealed_at IS NOT NULL ORDER BY sv.sealed_at DESC, sv.id DESC LIMIT 1"),
        dict(k=key)).scalar_one_or_none()
    if vid is None:
        raise UnsealedVersion(f"source {key!r} has no sealed version")
    return vid
