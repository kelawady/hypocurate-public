"""Step 1: the two sources are frozen, fingerprinted and as the PRD describes (Section 10)."""
import pandas as pd
import pytest

from hypocurate.sources.manifest import REPO_ROOT, file_entries, load_manifest, sha256_file, verify

MANIFEST = load_manifest()
MPEA_CSV = REPO_ROOT / "data/sources/mpea/MPEA_dataset.csv"
TAMU_XLSX = REPO_ROOT / "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx"
TAMU_CSV = REPO_ROOT / "data/sources/tamu_fcc/inputs.csv"
ELEMENTS = ["Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V"]


# --- fingerprints -------------------------------------------------------------

@pytest.mark.parametrize("entry", file_entries(MANIFEST), ids=lambda e: e.path)
def test_frozen_file_matches_its_fingerprint(entry):
    path = REPO_ROOT / entry.path
    assert path.is_file(), f"{entry.path} is missing"
    assert path.stat().st_size == entry.bytes
    assert sha256_file(path) == entry.sha256


def test_verify_reports_no_problems():
    assert verify(MANIFEST) == []


def test_verify_detects_a_changed_byte(tmp_path):
    """The check itself works: one altered byte in a copy is reported."""
    entry = next(e for e in file_entries(MANIFEST) if e.path.endswith("MPEA_dataset.csv"))
    copy = tmp_path / entry.path
    copy.parent.mkdir(parents=True)
    data = bytearray((REPO_ROOT / entry.path).read_bytes())
    data[1000] ^= 0x01
    copy.write_bytes(bytes(data))
    manifest = {"sources": {"mpea": {"files": [{"path": entry.path, "sha256": entry.sha256, "bytes": entry.bytes}]}},
                "controlled_duplicates": {"files": []}}
    problems = verify(manifest, root=tmp_path)
    assert len(problems) == 1 and "sha256" in problems[0]


def test_both_sources_are_in_the_manifest():
    assert set(MANIFEST["sources"]) == {"mpea", "tamu_fcc"}


@pytest.mark.parametrize("source_id", ["mpea", "tamu_fcc"])
def test_manifest_records_origin_date_and_licence(source_id):
    s = MANIFEST["sources"][source_id]
    for key in ("name", "citation", "licence", "licence_file", "repository", "commit", "retrieved"):
        assert s.get(key), f"{source_id}: {key} missing"
    assert s["retrieved"] == "2026-10-04"
    assert len(s["commit"]) == 40
    for f in s["files"]:
        assert f["origin_url"].startswith("https://")
        assert s["commit"] in f["origin_url"], "origin must be pinned to the recorded commit"
    assert s["licence_file"] in {f["path"] for f in s["files"]}, "licence text must be frozen too"


def test_licence_texts_match_the_manifest():
    mpea = (REPO_ROOT / MANIFEST["sources"]["mpea"]["licence_file"]).read_text(encoding="utf-8")
    tamu = (REPO_ROOT / MANIFEST["sources"]["tamu_fcc"]["licence_file"]).read_text(encoding="utf-8")
    assert MANIFEST["sources"]["mpea"]["licence"] == "Apache-2.0"
    assert "Apache License" in mpea and "Version 2.0" in mpea
    assert MANIFEST["sources"]["tamu_fcc"]["licence"] == "MIT"
    assert tamu.startswith("MIT License")


def test_tamu_origin_is_the_zenodo_record():
    s = MANIFEST["sources"]["tamu_fcc"]
    assert s["doi"] == "10.5281/zenodo.22798856"
    assert s["tag"] == "v1.1.0"
    assert s["repository"] == "https://github.com/ArroyaveLab/2026-mulukutla-hall-petch"
    assert s["zenodo_archive"]["md5"] == "dad706f3a6db0b96166f43c82a721bc8"


# --- record counts stated in the PRD -------------------------------------------

def test_mpea_counts():
    d = pd.read_csv(MPEA_CSV)
    assert len(d) == 1545
    assert d["PROPERTY: grain size ($\\mu$m)"].notna().sum() == 237


def tamu_xlsx():
    return pd.read_excel(TAMU_XLSX)


def test_tamu_counts():
    x = tamu_xlsx()
    assert len(x) == 94  # samples
    assert len(x[ELEMENTS].drop_duplicates()) == 82  # compositions
    assert x["YS (MPa)"].isna().sum() == 1  # one sample has no yield strength
    assert x.loc[x["YS (MPa)"].isna(), "Alloy Name"].tolist() == ["BBA09"]
    assert x["Grain Size(µm)"].notna().all()


def test_tamu_csv_view_agrees_with_the_spreadsheet():
    x, c = tamu_xlsx(), pd.read_csv(TAMU_CSV)
    assert len(c) == len(x)
    assert c["Alloy"].tolist() == x["Alloy Name"].tolist()
    assert c["Iteration"].tolist() == x["Iteration"].tolist()
    pairs = {el: el for el in ELEMENTS} | {
        "GrainSize": "Grain Size(µm)", "SD_GS": "SD, Grain Size(µm)",
        "YS": "YS (MPa)", "SD_YS": "SD, YS", "HV": "Hardness, HV", "SD_HV": "SD, HV",
        "ColdWork": "Cold Work (%Reduction)", "RecrystT": "Recrystallization Temp(℃)",
        "HoldTime": "Holding time (h)",
    }
    for csv_col, xlsx_col in pairs.items():
        pd.testing.assert_series_equal(
            c[csv_col].astype(float), x[xlsx_col].astype(float), check_names=False, obj=csv_col
        )
