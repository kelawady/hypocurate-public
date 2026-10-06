"""Step 4: registering the three sources as sealed versions (step 3 requirements).

- The files digest and identity computed in Python equal the database's.
- Every version is sealed before use; an unsealed or altered version is refused.
- Registration locks the source row first (owner, step 4 question 1) and is retried
  on deadlock; registering twice, or at the same time, leaves one version.
- Every manifest path read stays inside its directory (step 3, open item 4)."""
import dataclasses
import json
import shutil
import threading
import time
from pathlib import Path

import pytest
from sqlalchemy import text

from hypocurate.sources import adapters
from hypocurate.sources.manifest import load_manifest
from hypocurate.sources.versions import (SOURCES, RegistrationError, UnsealedVersion, _register_in, files_digest,
                                         latest_sealed_version_id, load_sealed_version, read_definition_files,
                                         register, safe_path_within, sha256_hex, version_identity)

REPO = Path(__file__).resolve().parents[1]


def rows(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def val(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def add_unsealed(engine, key, files, unit="paper"):
    with engine.begin() as conn:
        sid = conn.execute(text(
            "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
            "VALUES (:k, :k, 'uploaded_table', 'test', 'measured', 'available', true, :u) RETURNING id"),
            dict(k=key, u=unit)).scalar_one()
        vid = conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on) "
                                "VALUES (:s, 'v', '2026-10-05') RETURNING id"), dict(s=sid)).scalar_one()
        for path, content in files.items():
            conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content) "
                              "VALUES (:v, :p, :h, :c)"), dict(v=vid, p=path, h=sha256_hex(content), c=content))
    return vid


# --- The database's definitions ------------------------------------------------------

FILE_SETS = [
    {"a.csv": b"1"},
    {"b.csv": b"x", "B.csv": b"y", "a.csv": b"z"},             # bytewise: upper case first
    {"a-b.csv": b"1", "a.b.csv": b"2", "a/b.csv": b"3", "a_b.csv": b"4", "aB.xlsx": b"5"},
    {"dir/z.csv": b"", "dir/A.xlsx": b"\x00\xff"},
]


@pytest.mark.parametrize("files", FILE_SETS)
def test_files_digest_equals_the_databases(db, files):
    vid = add_unsealed(db, "digest_test", files)
    assert val(db, "SELECT hc_files_digest(:v)", v=vid) == files_digest(files)


def test_version_identity_equals_the_databases(db):
    digest = files_digest({"a.csv": b"1"})
    for source_type in ("uploaded_table", "web_interface", "paper_search", "model_recall"):
        for kind in ("measured", "computed", "model_recalled"):
            for unit in ("paper", "dataset", "batch"):
                assert val(db, "SELECT hc_version_identity(:d, :t, :k, :u)", d=digest, t=source_type, k=kind,
                           u=unit) == version_identity(digest, source_type, kind, unit)


def test_an_unsafe_stored_path_is_refused_before_the_database():
    for path in ("a\n.csv", "../a.csv", "/a.csv", "a.txt", ".a.csv", "a b.csv"):
        with pytest.raises(RegistrationError, match="unsafe"):
            files_digest({path: b"1"})


# --- Registration --------------------------------------------------------------------

def test_registering_seals_every_source(db):
    for key, d in SOURCES.items():
        r = register(db, key)
        assert r.created
        files, obtained = read_definition_files(d)
        assert r.files_digest == files_digest(files)
        assert r.fingerprint == version_identity(r.files_digest, d.source_type, d.data_kind, d.grouping_unit)
        (sealed_at, digest, fp, label, on, stype, kind, unit), = rows(db, (
            "SELECT sealed_at, files_digest, fingerprint, label, obtained_on, source_type, data_kind, grouping_unit "
            "FROM source_version WHERE id = :v"), v=r.version_id)
        assert sealed_at is not None and (digest, fp, label) == (r.files_digest, r.fingerprint, d.version_label)
        assert (on, stype, kind, unit) == (obtained, d.source_type, d.data_kind, d.grouping_unit)
        stored = {p: bytes(c) for p, c in rows(db, "SELECT path, content FROM source_file WHERE source_version_id = :v",
                                                v=r.version_id)}
        assert stored == files
        (enabled, status), = rows(db, "SELECT enabled, adapter_status FROM source WHERE key = :k", k=key)
        assert (enabled, status) == (d.enabled, "available")
    # Step 8a (owner, 2026-10-06, Q1): each source's documentation is stored with its data, by role.
    stored = {(p, r) for p, r in rows(db, "SELECT path, role FROM source_file")}
    assert stored == {("MPEA_dataset.csv", "data"), ("Grain_Size_Summary_v3.xlsx", "data"), ("extract.csv", "data"),
                      ("documentation/Borg2020_PMC7722748.xml", "documentation"),
                      ("documentation/main.tex", "documentation"), ("documentation/supplementary.tex", "documentation"),
                      ("curation.json", "curation")}  # step 8a: the owner's accepted Curator values
    assert val(db, "SELECT enabled FROM source WHERE key = 'controlled_duplicates'") is False


def test_registering_again_adds_nothing(db):
    first = {k: register(db, k) for k in SOURCES}
    counts = [val(db, f"SELECT count(*) FROM {t}") for t in ("source", "source_version", "source_file")]
    again = {k: register(db, k) for k in SOURCES}
    assert counts == [3, 3, 7]  # step 8a: three data files, three documentation files, one curation file
    assert [val(db, f"SELECT count(*) FROM {t}") for t in ("source", "source_version", "source_file")] == counts
    assert all(not r.created and r.version_id == first[k].version_id and r.fingerprint == first[k].fingerprint
               for k, r in again.items())


def waiting_on_a_lock(engine) -> int:
    return val(engine, "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() "
                       "AND wait_event_type = 'Lock' AND state = 'active'")


def test_concurrent_registration_waits_on_the_source_lock_and_leaves_one_version(db):
    d = SOURCES["mpea"]
    files, obtained = read_definition_files(d)
    outcome = {}

    def second():
        try:
            outcome["result"] = register(db, "mpea")
        except Exception as error:  # reported below
            outcome["result"] = error

    with db.connect() as a:
        tx = a.begin()
        first = _register_in(a, d, files, obtained)  # holds the source row lock, uncommitted
        thread = threading.Thread(target=second)
        thread.start()
        deadline = time.monotonic() + 10
        while waiting_on_a_lock(db) == 0 and time.monotonic() < deadline:
            time.sleep(0.05)
        assert thread.is_alive() and waiting_on_a_lock(db) == 1, "the second registration should wait"
        tx.commit()
    thread.join(30)
    result = outcome["result"]
    assert not isinstance(result, Exception), result
    assert first.created and not result.created and result.version_id == first.version_id
    assert val(db, "SELECT count(*) FROM source_version") == 1


def test_the_source_lock_serializes_a_new_version_of_an_existing_source(db):
    """The source row exists, but its version does not (a second version later, or a
    registration that failed before sealing). Without the source-row lock both writers
    would insert a version and the second would fail at sealing on the unique identity."""
    d = SOURCES["mpea"]
    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
            "VALUES ('mpea', 'x', :t, 'x', :k, 'available', true, :u)"),
            dict(t=d.source_type, k=d.data_kind, u=d.grouping_unit))
    test_concurrent_registration_waits_on_the_source_lock_and_leaves_one_version(db)


def test_two_registrations_at_once_leave_one_version(db):
    barrier = threading.Barrier(2)
    results = []

    def go():
        barrier.wait()
        results.append(register(db, "tamu_fcc"))

    threads = [threading.Thread(target=go) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert sorted(r.created for r in results) == [False, True]
    assert len({r.version_id for r in results}) == 1
    assert val(db, "SELECT count(*) FROM source_version") == 1


@pytest.fixture
def data_copy(tmp_path):
    """A copy of data/ to alter, with the original manifest."""
    copy = tmp_path / "data"
    shutil.copytree(REPO / "data", copy)
    return copy


def test_a_changed_file_is_refused_and_nothing_is_written(db, data_copy):
    path = data_copy / "sources/mpea/MPEA_dataset.csv"
    content = bytearray(path.read_bytes())
    content[-2] ^= 1
    path.write_bytes(bytes(content))
    with pytest.raises(RegistrationError, match="does not match its manifest fingerprint"):
        register(db, "mpea", data_dir=data_copy)
    assert val(db, "SELECT count(*) FROM source") == 0


def test_changed_interpretation_settings_are_refused(db):
    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO source (key, name, source_type, licence, data_kind, adapter_status, enabled, grouping_unit) "
            "VALUES ('tamu_fcc', 'x', 'uploaded_table', 'MIT', 'measured', 'available', true, 'batch')"))
    with pytest.raises(RegistrationError, match="not made silently"):
        register(db, "tamu_fcc")
    assert val(db, "SELECT count(*) FROM source_version") == 0
    assert val(db, "SELECT grouping_unit FROM source WHERE key = 'tamu_fcc'") == "batch"


def test_an_unknown_source_is_refused(db):
    with pytest.raises(RegistrationError, match="unknown source"):
        register(db, "nope")


# --- Paths ---------------------------------------------------------------------------

def test_paths_must_stay_inside_their_directory(tmp_path):
    base = tmp_path / "base"
    (base / "a").mkdir(parents=True)
    (tmp_path / "outside.csv").write_text("x")
    assert safe_path_within(base, "a/../b.csv") == (base / "b.csv").resolve()
    for bad in ("a/../../outside.csv", "../outside.csv", "/etc/passwd", str(tmp_path / "outside.csv"), ""):
        with pytest.raises(RegistrationError):
            safe_path_within(base, bad)
    (base / "link.csv").symlink_to(tmp_path / "outside.csv")
    with pytest.raises(RegistrationError, match="leaves"):
        safe_path_within(base, "link.csv")


def test_a_definition_pointing_outside_data_is_refused(data_copy):
    escaping = dataclasses.replace(SOURCES["mpea"], directory="../../tests")
    with pytest.raises(RegistrationError, match="leaves"):
        read_definition_files(escaping, data_dir=data_copy)
    via_name = dataclasses.replace(SOURCES["mpea"], data_files=("../tamu_fcc/inputs.csv",))
    with pytest.raises(RegistrationError):
        read_definition_files(via_name, data_dir=data_copy)


def test_a_file_missing_from_the_manifest_is_refused(data_copy):
    manifest = load_manifest(data_copy / "manifest.json")
    manifest["sources"]["mpea"]["files"] = []
    with pytest.raises(RegistrationError, match="not in the manifest"):
        read_definition_files(SOURCES["mpea"], data_dir=data_copy, manifest=manifest)


# --- Sealed before use ---------------------------------------------------------------

def test_an_unsealed_version_is_refused(db):
    vid = add_unsealed(db, "unsealed", {"a.csv": b"1"})
    with db.connect() as conn:
        with pytest.raises(UnsealedVersion, match="not sealed"):
            load_sealed_version(conn, vid)
        with pytest.raises(UnsealedVersion, match="no sealed version"):
            latest_sealed_version_id(conn, "unsealed")
        with pytest.raises(UnsealedVersion, match="no source version"):
            load_sealed_version(conn, vid + 1000)


def test_a_loaded_version_reads_like_the_files_on_disk(db):
    from source_helpers import sealed_from_disk
    for key in SOURCES:
        r = register(db, key)
        with db.connect() as conn:
            assert latest_sealed_version_id(conn, key) == r.version_id
            version = load_sealed_version(conn, r.version_id)
        assert (version.files_digest, version.fingerprint) == (r.files_digest, r.fingerprint)
        from_db = [x.to_json() for x in adapters.read(version).records]
        from_disk = [x.to_json() for x in adapters.read(sealed_from_disk(key)).records]
        assert json.dumps(from_db) == json.dumps(from_disk)


def test_changed_settings_on_a_loaded_version_are_refused(db):
    r = register(db, "tamu_fcc")
    with db.connect() as conn:
        version = load_sealed_version(conn, r.version_id)
    with pytest.raises(UnsealedVersion, match="sealed identity"):
        adapters.read(dataclasses.replace(version, grouping_unit="batch"))


# The curated Texas A&M version sealed from the owner's decisions (step 8a, local development database,
# 2026-10-06): registering the frozen files must give exactly this version, with no model call.
CURATED_TAMU_FINGERPRINT = "2fad3ccb3dbc32c1ec51e6efcb70a9d17d755bfdfa606cb044f458bd2b37b982"


def test_registering_the_frozen_curation_reproduces_the_sealed_curated_version(db):
    r = register(db, "tamu_fcc")
    assert r.fingerprint == CURATED_TAMU_FINGERPRINT
