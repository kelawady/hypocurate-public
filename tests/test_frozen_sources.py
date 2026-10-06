"""Step 1: the two sources are frozen, fingerprinted and as the PRD describes (Section 10)."""
import pandas as pd
import pytest

from hypocurate.sources.manifest import REPO_ROOT, file_entries, load_manifest, sha256_file, verify

MANIFEST = load_manifest()
MANIFEST_PATH = REPO_ROOT / "data/manifest.json"
# Pinned here, outside data/, so the data and the manifest cannot be changed
# together without changing a test (second-model review of step 1, finding 2).
MANIFEST_SHA256 = "ea06df04819736e2608a508c63f9fff8177a2543d954cdbd1f6e2191f9c45d14"  # step 8a: documentation, curation
# Every file the manifest must cover. Fixed here so that dropping an entry from
# the manifest cannot silently remove its fingerprint check.
REQUIRED_FILES = {
    "data/sources/mpea/MPEA_dataset.csv",
    "data/sources/mpea/LICENSE",
    "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx",
    "data/sources/tamu_fcc/inputs.csv",
    "data/sources/tamu_fcc/LICENSE",
    "data/controlled_duplicates/extract.csv",
    # Step 8a (owner, 2026-10-06): the sources' documentation, frozen into the source versions.
    "data/sources/tamu_fcc/documentation/main.tex",
    "data/sources/tamu_fcc/documentation/supplementary.tex",
    "data/sources/mpea/documentation/Borg2020_PMC7722748.xml",
    # Step 8a (owner, 2026-10-06): the Curator's proposals the owner accepted for Texas A&M.
    "data/sources/tamu_fcc/curation.json",
}
MPEA_CSV = REPO_ROOT / "data/sources/mpea/MPEA_dataset.csv"
TAMU_XLSX = REPO_ROOT / "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx"
TAMU_CSV = REPO_ROOT / "data/sources/tamu_fcc/inputs.csv"
ELEMENTS = ["Al", "Co", "Cr", "Cu", "Fe", "Mn", "Ni", "V"]


# --- fingerprints -------------------------------------------------------------

def test_manifest_itself_is_unchanged():
    assert sha256_file(MANIFEST_PATH) == MANIFEST_SHA256


def test_manifest_covers_exactly_the_required_files():
    assert {e.path for e in file_entries(MANIFEST)} == REQUIRED_FILES


@pytest.mark.parametrize("path", sorted(REQUIRED_FILES))
def test_required_file_is_present(path):
    assert (REPO_ROOT / path).is_file()


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


def test_documentation_records_its_origin_and_licence():
    """Step 8a (owner, 2026-10-06): each frozen document states where it came from and under
    which licence; the Texas A&M documents come from the pinned commit's archive."""
    tamu = MANIFEST["sources"]["tamu_fcc"]
    assert [d["path"] for d in tamu["documentation"]] == ["data/sources/tamu_fcc/documentation/main.tex",
                                                          "data/sources/tamu_fcc/documentation/supplementary.tex"]
    for d in tamu["documentation"]:
        assert d["origin_url"].startswith("https://") and tamu["commit"] in d["origin_url"]
        assert d["archive_member"] == "paper/" + d["path"].rsplit("/", 1)[1]
    mpea = MANIFEST["sources"]["mpea"]
    [paper] = mpea["documentation"]
    assert paper["path"] == "data/sources/mpea/documentation/Borg2020_PMC7722748.xml"
    assert paper["origin_url"] == "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7722748/fullTextXML"
    assert paper["licence"].startswith("CC-BY-4.0") and paper["retrieved"] == "2026-10-06"
    text = (REPO_ROOT / paper["path"]).read_text(encoding="utf-8")
    assert "Creative Commons Attribution 4.0 International License" in text
    assert "10.1038/s41597-020-00768-9" in text


def test_the_curation_file_records_the_owners_decisions():
    """Step 8a: the frozen curation holds exactly the two values the owner accepted (proposals 5 and 2;
    proposal 1, microstructure, rejected), each quoted from the frozen documentation."""
    import json
    [entry] = MANIFEST["sources"]["tamu_fcc"]["curation"]
    assert entry["path"] == "data/sources/tamu_fcc/curation.json" and entry["built"] == "2026-10-06"
    doc = json.loads((REPO_ROOT / entry["path"]).read_text(encoding="utf-8"))
    assert doc["source"] == "tamu_fcc" and set(doc["values"]) == {"test_type", "phase_class"}
    main = (REPO_ROOT / "data/sources/tamu_fcc/documentation/main.tex").read_text(encoding="utf-8").splitlines()
    for field, value, line in (("test_type", "tension", 177), ("phase_class", "FCC", 173)):
        v = doc["values"][field]
        assert (v["value"], v["line"], v["accepted_by"]) == (value, line, "Khalid El-Awady")
        assert v["quote"] in main[line - 1]


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
