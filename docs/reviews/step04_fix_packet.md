# Build step 4 — fix packet (first review)

Date: 2026-10-05. Branch: `step-04-adapters`. The first review (`docs/reviews/step04_review_chatgpt.md`) raised five findings and one test weakness; the owner accepted all six and approved the fix plan with one addition (finding 3: the error names the file, the line and the reason). One commit per item. GitHub Actions on the last code commit `4aad3a2`: success, 467 passed, https://github.com/kelawady/hypocurate/actions/runs/37257783194.

Generated from the repository by a script. Each item shows that commit's change as a unified diff with 12 lines of context. The updated `docs/reviews/step04_summary.md` (findings section, the tests replaced and why, the checks against the pre-fix code) is in the repository and is not repeated here.

## How to use this packet

Please check that each item is closed, and that nothing else changed. Your review is advice; the test suite is the gate.

| Item | Commit | Where |
|---|---|---|
| 1. Paper grouping key derived from the DOI | `30b95c0` | `normalize.doi_group_key`; `mpea_layout._record`; `test_adapter_mpea.py` (grouping tests replaced and added); `test_reference_counts_from_adapters.py` (20 papers by key and by DOI) |
| 2. The alloy label is for display only | `8a58a58` | docstrings in `normalize.py` and `record.py`; renamed tests; the new below-rounding test; a note in the reference-count test |
| 3. Strict CSV parsing; a malformed file is refused | `028617e` | `mpea_layout.read` and `_next`; the wrong-field-count branch in `_record` removed; new refusal tests |
| 4. A spreadsheet formula affects only its own field | `f0efe89` | `tamu_fcc._number`; the whole-row branch in `_record` removed; the corrected planted test |
| 5. Composition parsing never returns a non-finite value | `d2de2d8` | `normalize.formula_to_atomic_percent`, `percent_columns_to_atomic_percent`; `tests/test_normalize.py` |
| 6. Test weakness: hand-written expected strings | `f569d2b` | `test_reported_text_matches_independently_written_strings` in `test_adapter_tamu.py` |
| README | `4aad3a2` | README, Sources and adapters |

## 1. Paper grouping key derived from the DOI (`30b95c0`)

The group key is derived from the DOI as reported: whitespace trimmed, one URL or `doi:` wrapper removed (case-insensitive), ASCII A–Z case-folded, nothing else. `paper_doi` and the reported text are unchanged. Frozen data: 8 DOI strings change form; 265 groups stay 265; the 77 reference records keep 20 papers.

Commit message:

```
Step 4 fix 1: derive the paper grouping key from the DOI; keep the DOI as reported

Review finding 1: a raw-DOI group key split one paper written differently. The key is
now derived by doi_group_key (whitespace trimmed, a URL or doi: wrapper removed, ASCII
case-folded); paper_doi and the reported text are unchanged. The tests that required
the raw key are replaced. Frozen data: 8 DOI strings change form, 265 groups stay 265,
and the 77 reference records keep their 20 papers.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```diff
diff --git a/hypocurate/sources/adapters/mpea_layout.py b/hypocurate/sources/adapters/mpea_layout.py
index 33454c0..21919a4 100644
--- a/hypocurate/sources/adapters/mpea_layout.py
+++ b/hypocurate/sources/adapters/mpea_layout.py
@@ -1,24 +1,26 @@
 """Adapter for the MPEA column layout (Borg et al. 2020): the MPEA dataset itself and the
 controlled duplicate extract, which copies its header verbatim (step 1).
 
 - One record per data row, in file order; no row is dropped. An entirely blank line is
   listed in `blank_rows`, not turned into a record.
 - Origin key: `<file>:row:<n>`, n the 0-based data row (the row numbering used in
   step 1). One record per row, so `item_index` is 0.
 - Every column is kept as reported text, with the unit its header states.
 - **Paper identity (grouping): the DOI** (`REFERENCE: doi`), as in the reference script.
-  In the frozen MPEA file it is one-to-one with `IDENTIFIER: Reference ID`. A blank DOI
-  gives a record whose group is unknown, with the reason; the Reference ID is never used
-  in its place, and no group is invented.
+  `paper_doi` and the reported text keep the DOI exactly as in the file; the group key is
+  derived from it by `normalize.doi_group_key` (whitespace trimmed, a URL or `doi:`
+  wrapper removed, ASCII case-folded; step 4 review, finding 1), so formatting
+  differences do not split one paper. A blank DOI gives a record whose group is unknown,
+  with the reason; the Reference ID is never used in its place, and no group is invented.
 - Units are those of the headers (µm, MPa, HV, °C); values are converted unchanged.
 - Text values (DOI, title, categories) are kept exactly as reported, surrounding spaces
   included; only a whitespace-only cell counts as blank.
 """
 from __future__ import annotations
 
 import csv
 import io
 
 from hypocurate.sources import normalize as n
 from hypocurate.sources.record import (HARMONIZED_FIELDS, AdapterError, AdapterResult, CommonRecord,
                                        Group, Reported, Value)
@@ -124,15 +126,16 @@ def _record(version: SealedVersion, path: str, i: int, fields: list[str]) -> Com
         reported[f"(column {extra}, no header)"] = Reported(f"(column {extra}, no header)", value, None)
     if len(fields) != len(HEADER):
         reason = f"the row has {len(fields)} fields, the header {len(HEADER)}"
         harmonized = {name: Value(None, unit, "not_convertible", reason) for name, unit in HARMONIZED_FIELDS.items()}
         return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, None, None, None,
                             Group("paper", None, reason), harmonized, reported)
     cells = dict(zip(HEADER, fields))
     harmonized, alloy = _harmonize(cells)
     # Kept exactly as reported (one MPEA DOI has a leading space); only a whitespace-only
     # cell counts as blank.
     doi = cells["REFERENCE: doi"] if cells["REFERENCE: doi"].strip() else None
     title = cells["REFERENCE: title"] if cells["REFERENCE: title"].strip() else None
-    group = Group("paper", f"doi:{doi}") if doi else Group("paper", None, "no DOI in the source: paper unknown")
+    group_key = n.doi_group_key(doi) if doi else None
+    group = Group("paper", group_key) if group_key else Group("paper", None, "no DOI in the source: paper unknown")
     return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, alloy, title, doi,
                         group, harmonized, reported)
diff --git a/hypocurate/sources/normalize.py b/hypocurate/sources/normalize.py
index 6eec1a8..fddb5d7 100644
--- a/hypocurate/sources/normalize.py
+++ b/hypocurate/sources/normalize.py
@@ -78,12 +78,32 @@ def percent_columns_to_atomic_percent(columns: dict[str, float | None]
         return None, f"negative percentage for {', '.join(negative)}"
     total = sum(columns.values())
     if abs(total - 100.0) > PERCENT_SUM_TOLERANCE:
         return None, f"percentages sum to {total:g}, not 100"
     return {e: float(v) for e, v in columns.items() if v > 0}, None
 
 
 def alloy_label(composition: dict[str, float]) -> str:
     """The canonical alloy name: elements in alphabetical order, each with its atomic
     percent rounded to 0.1 (the reference script's naming, `docs/reference/worked_example.py`).
     The full-precision composition is kept beside it in the record."""
     return "".join(f"{e}{round(v, 1):g}" for e, v in sorted(composition.items()))
+
+
+_DOI_WRAPPER = re.compile(r"(?:https?://(?:dx\.)?doi\.org/|doi:)\s*", re.IGNORECASE)
+_ASCII_UPPER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
+
+
+def doi_group_key(doi: str) -> str | None:
+    """The grouping key of a paper from its DOI as reported (step 4 review, finding 1).
+
+    Conservative normalization, so that formatting differences do not split one paper:
+    surrounding whitespace is trimmed; one `https://doi.org/`, `http://dx.doi.org/` or
+    `doi:` wrapper is removed (case-insensitive); ASCII letters A–Z are case-folded, as DOI
+    equivalence prescribes. Nothing else changes (no Unicode normalization). The DOI as
+    reported is kept unchanged in the record. Returns None if nothing is left."""
+    key = doi.strip()
+    match = _DOI_WRAPPER.match(key)
+    if match:
+        key = key[match.end():]
+    key = key.strip().translate(_ASCII_UPPER)
+    return f"doi:{key}" if key else None
diff --git a/tests/test_adapter_mpea.py b/tests/test_adapter_mpea.py
index d3cacb8..a0b4fe2 100644
--- a/tests/test_adapter_mpea.py
+++ b/tests/test_adapter_mpea.py
@@ -107,27 +107,30 @@ def _reference_norm(f):
 
 
 def test_alloy_names_follow_the_reference_naming(result, rows):
     for record, row in zip(result.records, rows):
         assert record.alloy == _reference_norm(row[1])
         assert sum(record.harmonized["composition"].value.values()) == pytest.approx(100)
 
 
 def test_paper_identity_is_the_doi(result, rows):
     for record, row in zip(result.records, rows):
         assert record.paper_doi == row[20]
         assert record.group.unit == "paper"
-        assert record.group.key == f"doi:{row[20]}"
+        # The group key is derived (finding 1); written out independently here.
+        assert record.group.key == "doi:" + row[20].strip().lower()
         assert record.paper_reference == (row[22] or None)
+    # Normalization changes the form of 8 DOI strings but merges and splits no group.
     assert len({r.group.key for r in result.records}) == 265
+    assert sum(r.group.key != f"doi:{r.paper_doi}" for r in {r.paper_doi: r for r in result.records}.values()) == 8
     # In the frozen file the DOI and the Reference ID are one-to-one.
     assert len({(row[0], row[20]) for row in rows}) == len({row[20] for row in rows}) == len({row[0] for row in rows})
 
 
 def test_the_record_format_has_no_decision_fields():
     names = {f.name for f in dataclasses.fields(CommonRecord)}
     assert names == {"source_key", "version_fingerprint", "source_item_key", "item_index", "kind", "alloy",
                      "paper_reference", "paper_doi", "group", "harmonized", "reported"}
 
 
 # --- Planted rows --------------------------------------------------------------------
 
@@ -205,13 +208,35 @@ def test_another_grouping_unit_is_refused():
 def test_altered_bytes_are_refused_before_parsing(version):
     tampered = dataclasses.replace(version, files={"MPEA_dataset.csv": planted([GOOD])})
     with pytest.raises(UnsealedVersion, match="files digest"):
         adapters.read(tampered)
     with pytest.raises(UnsealedVersion, match="not sealed"):
         adapters.read(dataclasses.replace(version, sealed_at=None))
 
 
 def test_text_is_kept_exactly_as_reported(result, rows):
     """One MPEA DOI has a leading space; the adapter keeps it (no silent correction)."""
     spaced = [r for r in result.records if r.paper_doi and r.paper_doi != r.paper_doi.strip()]
     assert [r.paper_doi for r in spaced] == [" 10.1038/ncomms10602"]
-    assert spaced[0].group.key == "doi: 10.1038/ncomms10602"
+    assert spaced[0].reported["REFERENCE: doi"].text == " 10.1038/ncomms10602"
+    assert spaced[0].group.key == "doi:10.1038/ncomms10602"
+
+
+@pytest.mark.parametrize("reported", [
+    "10.1016/J.ACTAMAT.2019.04.017", " 10.1016/j.actamat.2019.04.017 ", "doi:10.1016/j.actamat.2019.04.017",
+    "DOI: 10.1016/j.actamat.2019.04.017", "https://doi.org/10.1016/j.actamat.2019.04.017",
+    "http://dx.doi.org/10.1016/J.ActaMat.2019.04.017", "HTTPS://DOI.ORG/10.1016/j.actamat.2019.04.017",
+])
+def test_formatting_differences_do_not_split_a_paper(reported):
+    """Finding 1: one DOI written differently is one group; the DOI as reported is kept."""
+    result = mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted([_row(c20=reported)])}))
+    record, = result.records
+    assert record.group.key == "doi:10.1016/j.actamat.2019.04.017"
+    assert record.paper_doi == reported
+    assert record.reported["REFERENCE: doi"].text == reported
+
+
+def test_grouping_folds_ascii_case_only():
+    from hypocurate.sources.normalize import doi_group_key
+    assert doi_group_key("10.1/ÄB") == "doi:10.1/Äb"  # non-ASCII letters are left as they are
+    assert doi_group_key("10.1/ab") != doi_group_key("10.1/ac")
+    assert doi_group_key("   ") is None and doi_group_key("doi:") is None
diff --git a/tests/test_reference_counts_from_adapters.py b/tests/test_reference_counts_from_adapters.py
index 0399129..3fc477b 100644
--- a/tests/test_reference_counts_from_adapters.py
+++ b/tests/test_reference_counts_from_adapters.py
@@ -51,25 +51,26 @@ def tamu_reference_set(records):
 def mpea():
     return adapters.read(sealed_from_disk("mpea")).records
 
 
 @pytest.fixture(scope="module")
 def tamu():
     return adapters.read(sealed_from_disk("tamu_fcc")).records
 
 
 def test_mpea_77_records_from_20_papers(mpea):
     chosen = mpea_reference_set(mpea)
     assert len(chosen) == 77
-    assert len({r.group.key for r in chosen}) == 20
+    assert len({r.group.key for r in chosen}) == 20  # derived keys (finding 1)
+    assert len({r.paper_doi for r in chosen}) == 20  # DOIs as reported
 
 
 def test_mpea_rows_are_those_of_the_reference_script(mpea):
     """The same rows as the reference script run on the raw file with pandas."""
     d = pd.read_csv(REPO / "data/sources/mpea/MPEA_dataset.csv")
     d.columns = ['ref', 'formula', 'micro', 'proc', 'phase', 'gs', 'rho_exp', 'rho_calc', 'HV', 'test', 'T', 'YS',
                  'UTS', 'el', 'elp', 'E_exp', 'E_calc', 'O', 'N', 'Cwt', 'doi', 'year', 'title']
 
     def norm(f):
         comp = {}
         for e, n in re.findall(r'([A-Z][a-z]?)([0-9.]*)', f):
             comp[e] = comp.get(e, 0) + (float(n) if n else 1.0)
```

## 2. The alloy label is for display only (`8a58a58`)

No code path treated the label as identity; the claims did. They are removed. The rule for when two compositions are the same alloy is a step 6 plan setting with an owner-approved tolerance; the reference numbers used 0.1 at.% rounding, the current default pending approval.

Commit message:

```
Step 4 fix 2: the alloy label is for display only

Review finding 2: the 0.1 at.% label merges compositions that differ below the rounding
step. Docstrings now say the label is never an identity; the full-precision
composition is in every record, and the same-alloy rule is a step 6 plan setting with
an owner-approved tolerance. The reference numbers used 0.1 at.% rounding (current
default, pending approval). New test: Fe50.01Ni49.99 and Fe50.04Ni49.96 share a label
but not a composition. Naming tests renamed as display-label tests; the renamed-formula
test compares compositions.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```diff
diff --git a/hypocurate/sources/normalize.py b/hypocurate/sources/normalize.py
index fddb5d7..992f927 100644
--- a/hypocurate/sources/normalize.py
+++ b/hypocurate/sources/normalize.py
@@ -74,27 +74,32 @@ def percent_columns_to_atomic_percent(columns: dict[str, float | None]
     if blank:
         return None, f"blank percentage for {', '.join(blank)}"
     negative = [e for e, v in columns.items() if v < 0]
     if negative:
         return None, f"negative percentage for {', '.join(negative)}"
     total = sum(columns.values())
     if abs(total - 100.0) > PERCENT_SUM_TOLERANCE:
         return None, f"percentages sum to {total:g}, not 100"
     return {e: float(v) for e, v in columns.items() if v > 0}, None
 
 
 def alloy_label(composition: dict[str, float]) -> str:
-    """The canonical alloy name: elements in alphabetical order, each with its atomic
-    percent rounded to 0.1 (the reference script's naming, `docs/reference/worked_example.py`).
-    The full-precision composition is kept beside it in the record."""
+    """An alloy name **for display only**: elements in alphabetical order, each with its
+    atomic percent rounded to 0.1 (the reference script's naming,
+    `docs/reference/worked_example.py`).
+
+    Equal labels do not mean the same alloy: Fe50.01Ni49.99 and Fe50.04Ni49.96 both read
+    `Fe50Ni50` (step 4 review, finding 2). The record carries the full-precision
+    composition; when two compositions count as the same alloy is a plan and
+    domain-profile setting, defined in step 6 with a tolerance the owner approves."""
     return "".join(f"{e}{round(v, 1):g}" for e, v in sorted(composition.items()))
 
 
 _DOI_WRAPPER = re.compile(r"(?:https?://(?:dx\.)?doi\.org/|doi:)\s*", re.IGNORECASE)
 _ASCII_UPPER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
 
 
 def doi_group_key(doi: str) -> str | None:
     """The grouping key of a paper from its DOI as reported (step 4 review, finding 1).
 
     Conservative normalization, so that formatting differences do not split one paper:
     surrounding whitespace is trimmed; one `https://doi.org/`, `http://dx.doi.org/` or
diff --git a/hypocurate/sources/record.py b/hypocurate/sources/record.py
index 44860d9..1f81dbc 100644
--- a/hypocurate/sources/record.py
+++ b/hypocurate/sources/record.py
@@ -1,18 +1,20 @@
 """The common record format every source adapter returns (PRD Section 10; step 4).
 
 One `CommonRecord` per observation, mirroring the `record` table (step 3) so that a
 later step can store it unchanged: its origin (`source_item_key`, `item_index`), the
-kind of data, the alloy, the paper and its grouping identity, the harmonized values
-and the values as reported.
+kind of data, a display label for the alloy, the paper and its grouping identity, the
+harmonized values (the full-precision composition among them) and the values as
+reported. The adapter states no alloy identity: when two compositions are the same
+alloy is decided under the plan (step 6).
 
 An adapter converts and reports. The format therefore has no field for eligibility,
 flags, duplicates or survivors: those are decided by code under the locked plan
 (steps 6 and 7). Every harmonized value carries its status:
 
 - `converted`: read from the source and converted (possibly unchanged) to the unit shown;
 - `not_reported`: blank in the source, or the source has no such column (the reason says which);
 - `not_convertible`: present in the source but could not be converted; the reason says why,
   and the text as reported is kept in `reported`;
 - `assigned`: not in the data file, set by the adapter from the source's own documentation.
   It always carries a `Citation` (file, location and the exact passage), so an assigned
   value can never be mistaken for a reported one.
@@ -127,25 +129,25 @@ class Group:
 
     def to_json(self) -> dict:
         return {"unit": self.unit, "key": self.key, "reason": self.reason}
 
 
 @dataclass(frozen=True)
 class CommonRecord:
     source_key: str
     version_fingerprint: str
     source_item_key: str  # stable origin key within the source version
     item_index: int
     kind: str  # the version's kind of data
-    alloy: str | None  # canonical label from the composition; None if not convertible
+    alloy: str | None  # display label only, never an identity (see normalize.alloy_label); None if not convertible
     paper_reference: str | None
     paper_doi: str | None
     group: Group
     harmonized: Mapping[str, Value] = field(default_factory=dict)
     reported: Mapping[str, Reported] = field(default_factory=dict)
 
     def __post_init__(self):
         if not self.source_item_key:
             raise ValueError("a record needs its origin key")
         if set(self.harmonized) != set(HARMONIZED_FIELDS):
             raise ValueError(f"harmonized fields differ from the common set: "
                              f"{sorted(set(self.harmonized) ^ set(HARMONIZED_FIELDS))}")
diff --git a/tests/test_adapter_extract.py b/tests/test_adapter_extract.py
index c56443e..0248ca9 100644
--- a/tests/test_adapter_extract.py
+++ b/tests/test_adapter_extract.py
@@ -62,31 +62,30 @@ def test_each_record_equals_its_mpea_row_except_the_changed_columns(extract, mpe
         for attr in ("paper_doi", "paper_reference", "group"):
             if attr not in changed_fields:
                 assert getattr(record, attr) == getattr(source, attr), (t["extract_row"], attr)
         if "FORMULA" not in changed:
             assert record.alloy == source.alloy
         for column, rep in record.reported.items():
             if column not in changed:
                 assert rep == source.reported[column], (t["extract_row"], column)
             else:
                 assert rep.text != source.reported[column].text
 
 
-def test_a_renamed_formula_gives_the_same_alloy(extract, mpea, truth):
+def test_a_renamed_formula_gives_the_same_composition(extract, mpea, truth):
     renamed = [(t, r) for t, r in zip(truth, extract) if t["changed_columns"] == "FORMULA"]
     assert len(renamed) == 2
     for t, record in renamed:
         source = mpea[int(t["mpea_row"])]
         assert record.reported["FORMULA"].text != source.reported["FORMULA"].text
-        assert record.alloy == source.alloy
         a, b = record.harmonized["composition"].value, source.harmonized["composition"].value
         assert a.keys() == b.keys() and all(a[e] == pytest.approx(b[e], abs=1e-9) for e in a)
 
 
 def test_paper_unknown_is_marked_never_invented(extract, truth):
     blank = [r for t, r in zip(truth, extract) if "REFERENCE: doi" in t["changed_columns"]
              and r.reported["REFERENCE: doi"].text == ""]
     assert len(blank) == 2
     for r in blank:
         assert r.paper_doi is None and r.group.key is None
         assert r.group.reason == "no DOI in the source: paper unknown"
 
diff --git a/tests/test_adapter_mpea.py b/tests/test_adapter_mpea.py
index a0b4fe2..5cccd95 100644
--- a/tests/test_adapter_mpea.py
+++ b/tests/test_adapter_mpea.py
@@ -97,25 +97,25 @@ def test_no_value_is_assigned(result):
                 if v.status == "assigned" or v.citation is not None]
 
 
 def _reference_norm(f):
     """The reference script's alloy naming (docs/reference/worked_example.py), copied."""
     comp = {}
     for e, n in re.findall(r'([A-Z][a-z]?)([0-9.]*)', f):
         comp[e] = comp.get(e, 0) + (float(n) if n else 1.0)
     s = sum(comp.values())
     return ''.join(f"{e}{round(100 * v / s, 1):g}" for e, v in sorted(comp.items()))
 
 
-def test_alloy_names_follow_the_reference_naming(result, rows):
+def test_display_labels_follow_the_reference_naming(result, rows):
     for record, row in zip(result.records, rows):
         assert record.alloy == _reference_norm(row[1])
         assert sum(record.harmonized["composition"].value.values()) == pytest.approx(100)
 
 
 def test_paper_identity_is_the_doi(result, rows):
     for record, row in zip(result.records, rows):
         assert record.paper_doi == row[20]
         assert record.group.unit == "paper"
         # The group key is derived (finding 1); written out independently here.
         assert record.group.key == "doi:" + row[20].strip().lower()
         assert record.paper_reference == (row[22] or None)
@@ -231,12 +231,23 @@ def test_formatting_differences_do_not_split_a_paper(reported):
     result = mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted([_row(c20=reported)])}))
     record, = result.records
     assert record.group.key == "doi:10.1016/j.actamat.2019.04.017"
     assert record.paper_doi == reported
     assert record.reported["REFERENCE: doi"].text == reported
 
 
 def test_grouping_folds_ascii_case_only():
     from hypocurate.sources.normalize import doi_group_key
     assert doi_group_key("10.1/ÄB") == "doi:10.1/Äb"  # non-ASCII letters are left as they are
     assert doi_group_key("10.1/ab") != doi_group_key("10.1/ac")
     assert doi_group_key("   ") is None and doi_group_key("doi:") is None
+
+
+def test_compositions_differing_below_the_rounding_step_are_not_identical():
+    """Finding 2: the display label rounds to 0.1 at.%; the adapter's compositions do not."""
+    result = mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted(
+        [_row(c1="Fe50.01 Ni49.99"), _row(c1="Fe50.04 Ni49.96")])}))
+    a, b = result.records
+    assert a.alloy == b.alloy == "Fe50Ni50"  # the same display label …
+    ca, cb = a.harmonized["composition"].value, b.harmonized["composition"].value
+    assert ca != cb  # … but not the same composition
+    assert ca["Fe"] == pytest.approx(50.01) and cb["Fe"] == pytest.approx(50.04)
diff --git a/tests/test_adapter_tamu.py b/tests/test_adapter_tamu.py
index 2a450fd..81290c5 100644
--- a/tests/test_adapter_tamu.py
+++ b/tests/test_adapter_tamu.py
@@ -98,25 +98,25 @@ def test_temperature_is_not_reported(records):
             v = r.harmonized[name]
             assert (v.status, v.value) == ("not_reported", None)
             assert "states no test temperature" in v.reason
 
 
 def test_composition_in_atomic_percent(records):
     for r in records:
         c = r.harmonized["composition"]
         assert c.status == "converted" and c.citation == tamu_fcc.COMPOSITION_UNIT_CITATION
         assert sum(c.value.values()) == pytest.approx(100, abs=1e-9)
         for e in tamu_fcc.ELEMENT_COLUMNS:
             assert c.value.get(e, 0.0) == float(r.reported[e].text)
-    # 82 distinct compositions (PRD 10), and the naming keeps them distinct.
+    # 82 distinct compositions (PRD 10); their display labels happen to be distinct too.
     assert len({tuple(sorted(r.harmonized["composition"].value.items())) for r in records}) == 82
     assert len({r.alloy for r in records}) == 82
 
 
 def test_agrees_with_the_authors_csv_view(records):
     with open(INPUTS, encoding="utf-8", newline="") as f:
         view = {row["Alloy"]: row for row in csv.DictReader(f)}
     assert len(view) == 94
     for r in records:
         row = view[r.reported["Alloy Name"].text]
         h = r.harmonized
         assert h["grain_size"].value == pytest.approx(float(row["GrainSize"]))
diff --git a/tests/test_reference_counts_from_adapters.py b/tests/test_reference_counts_from_adapters.py
index 3fc477b..88708f7 100644
--- a/tests/test_reference_counts_from_adapters.py
+++ b/tests/test_reference_counts_from_adapters.py
@@ -1,19 +1,23 @@
 """Step 4: the adapters' output reproduces the reference counts (PRD 10, 14.1a).
 
 The filter below is a copy of the reference script's scope and rules
 (`docs/reference/worked_example.py`), written here on the test side to check the
 harmonization. It is not package code: eligibility is decided by code under the locked
 plan in step 6, and these counts are not a rule.
 
+Alloys are grouped here by the 0.1 at.% display label, which is how the reference numbers
+were computed. That rounding is the current default pending the owner's approval; the
+rule for when two compositions are the same alloy is set in step 6 (review, finding 2).
+
 The Texas A&M count ignores temperature: the source states no test temperature for its
 own measurements (step 4 question 3), and how a room-temperature scope treats it is the
 owner's step 6 decision."""
 import re
 from collections import defaultdict
 from pathlib import Path
 
 import pandas as pd
 import pytest
 
 from hypocurate.sources import adapters
 from source_helpers import sealed_from_disk
```

## 3. Strict CSV parsing; a malformed file is refused (`028617e`)

Owner's addition: the error names the file, the line(s) and the reason. The frozen MPEA file and the extract parse under strict mode. Limitation: a stray quote that leaves exactly 23 fields in every row is valid CSV and cannot be detected by syntax.

Commit message:

```
Step 4 fix 3: strict CSV parsing; a malformed file is refused, never partly read

Review finding 3: the permissive reader let an unterminated quote swallow later rows.
The MPEA-layout adapter now parses with strict=True; a parsing error or a row with the
wrong number of fields raises AdapterError naming the file, the line(s) and the reason
(owner's addition), e.g. 'MPEA_dataset.csv: line 4: expected 23 fields, found 21; the
file is refused'. The frozen MPEA file and the extract parse under strict mode.
Tests: unterminated quote at the end and swallowing later rows, malformed quote, wrong
field counts (24 and 21) with the line, a legitimate quoted multi-line field, and a
multi-line record's line range. The planted row with an extra field (formerly kept and
marked) is replaced by an ordinary row; refusal is tested separately.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```diff
diff --git a/hypocurate/sources/adapters/mpea_layout.py b/hypocurate/sources/adapters/mpea_layout.py
index 21919a4..7b4974a 100644
--- a/hypocurate/sources/adapters/mpea_layout.py
+++ b/hypocurate/sources/adapters/mpea_layout.py
@@ -1,17 +1,21 @@
 """Adapter for the MPEA column layout (Borg et al. 2020): the MPEA dataset itself and the
 controlled duplicate extract, which copies its header verbatim (step 1).
 
 - One record per data row, in file order; no row is dropped. An entirely blank line is
   listed in `blank_rows`, not turned into a record.
+- Strict CSV parsing: a quoting error or a row with the wrong number of fields refuses
+  the whole file with an `AdapterError` naming the file, the line and the reason. No
+  partial extraction is returned. A legitimate quoted field may span lines; the row
+  number in the origin key counts records, not physical lines.
 - Origin key: `<file>:row:<n>`, n the 0-based data row (the row numbering used in
   step 1). One record per row, so `item_index` is 0.
 - Every column is kept as reported text, with the unit its header states.
 - **Paper identity (grouping): the DOI** (`REFERENCE: doi`), as in the reference script.
   `paper_doi` and the reported text keep the DOI exactly as in the file; the group key is
   derived from it by `normalize.doi_group_key` (whitespace trimmed, a URL or `doi:`
   wrapper removed, ASCII case-folded; step 4 review, finding 1), so formatting
   differences do not split one paper. A blank DOI gives a record whose group is unknown,
   with the reason; the Reference ID is never used in its place, and no group is invented.
 - Units are those of the headers (µm, MPa, HV, °C); values are converted unchanged.
 - Text values (DOI, title, categories) are kept exactly as reported, surrounding spaces
   included; only a whitespace-only cell counts as blank.
@@ -95,47 +99,60 @@ def _harmonize(cells: dict[str, str]) -> tuple[dict[str, Value], str | None]:
 def read(version: SealedVersion) -> AdapterResult:
     version.verify()
     if version.grouping_unit != "paper":
         raise AdapterError(f"the MPEA-layout adapter groups by paper; version {version.id} "
                            f"has grouping unit {version.grouping_unit!r}")
     if len(version.files) != 1:
         raise AdapterError(f"expected one CSV file, found {sorted(version.files)}")
     (path, content), = version.files.items()
     try:
         decoded = content.decode("utf-8")
     except UnicodeDecodeError as error:
         raise AdapterError(f"{path} is not UTF-8: {error}") from None
-    rows = csv.reader(io.StringIO(decoded, newline=""))
-    header = tuple(next(rows, ()))
+    # Strict parsing (step 4 review, finding 3): a quoting error, or a row with the wrong
+    # number of fields, refuses the whole file. A partial extraction is never returned,
+    # because a stray quote can swallow the rows after it. The message names the file, the
+    # line and the reason, so whoever supplied the file can correct it.
+    rows = csv.reader(io.StringIO(decoded, newline=""), strict=True)
+    header = tuple(_next(rows, path, 1) or ())
     if header != HEADER:
-        raise AdapterError(f"{path}: the header is not the MPEA layout")
+        raise AdapterError(f"{path}: line 1: the header is not the MPEA layout; the file is refused")
     records, blank = [], []
-    for i, fields in enumerate(rows):
+    i, start = 0, rows.line_num + 1
+    while (fields := _next(rows, path, start)) is not None:
+        end = rows.line_num
+        lines = f"line {start}" if end == start else f"lines {start}-{end}"
         if not fields or all(f.strip() == "" for f in fields):
             blank.append(i)
-            continue
-        records.append(_record(version, path, i, fields))
+        elif len(fields) != len(HEADER):
+            raise AdapterError(f"{path}: {lines}: expected {len(HEADER)} fields, found {len(fields)}; "
+                               "the file is refused")
+        else:
+            records.append(_record(version, path, i, fields))
+        i, start = i + 1, end + 1
     return AdapterResult(tuple(records), tuple(blank))
 
 
+def _next(rows, path: str, start: int) -> list[str] | None:
+    """The next row, or None at the end of the file. A parsing error refuses the file."""
+    try:
+        return next(rows)
+    except StopIteration:
+        return None
+    except csv.Error as error:
+        raise AdapterError(f"{path}: line {start}: the record starting on this line cannot be parsed "
+                           f"({error}, detected at line {rows.line_num}); the file is refused") from None
+
+
 def _record(version: SealedVersion, path: str, i: int, fields: list[str]) -> CommonRecord:
     key = f"{path}:row:{i}"
-    reported = {}
-    for name, value in zip(HEADER, fields):
-        reported[name] = Reported(name, value, UNITS.get(name))
-    for extra, value in enumerate(fields[len(HEADER):], start=len(HEADER) + 1):
-        reported[f"(column {extra}, no header)"] = Reported(f"(column {extra}, no header)", value, None)
-    if len(fields) != len(HEADER):
-        reason = f"the row has {len(fields)} fields, the header {len(HEADER)}"
-        harmonized = {name: Value(None, unit, "not_convertible", reason) for name, unit in HARMONIZED_FIELDS.items()}
-        return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, None, None, None,
-                            Group("paper", None, reason), harmonized, reported)
+    reported = {name: Reported(name, value, UNITS.get(name)) for name, value in zip(HEADER, fields)}
     cells = dict(zip(HEADER, fields))
     harmonized, alloy = _harmonize(cells)
     # Kept exactly as reported (one MPEA DOI has a leading space); only a whitespace-only
     # cell counts as blank.
     doi = cells["REFERENCE: doi"] if cells["REFERENCE: doi"].strip() else None
     title = cells["REFERENCE: title"] if cells["REFERENCE: title"].strip() else None
     group_key = n.doi_group_key(doi) if doi else None
     group = Group("paper", group_key) if group_key else Group("paper", None, "no DOI in the source: paper unknown")
     return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, alloy, title, doi,
                         group, harmonized, reported)
diff --git a/tests/test_adapter_mpea.py b/tests/test_adapter_mpea.py
index 5cccd95..9147f78 100644
--- a/tests/test_adapter_mpea.py
+++ b/tests/test_adapter_mpea.py
@@ -153,57 +153,55 @@ def _row(**changes):
 
 def test_planted_values_are_kept_and_marked():
     lines = [
         GOOD,
         _row(c5="abc"),              # 1: grain size not a number
         _row(c1="Xx1 Co1"),          # 2: unknown element
         _row(c1=""),                 # 3: no formula
         _row(c5="-5"),               # 4: negative grain size: converted as reported, not judged here
         _row(c10="25 C"),            # 5: temperature with text
         _row(c9="X"),                # 6: unknown test type
         _row(c20=""),                # 7: no DOI
         "",                          # 8: blank line
-        GOOD + ",extra",             # 9: an extra field
+        _row(c2="FCC+BCC"),          # 9: an ordinary row (a wrong field count now refuses the file: finding 3)
         _row(c11="nan"),             # 10: not finite
         _row(c1="Co1 Cr0 Ni1"),      # 11: zero amount
     ]
     result = mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted(lines)}))
     by_row = {int(r.source_item_key.rsplit(":", 1)[1]): r for r in result.records}
     assert result.blank_rows == (8,)
     assert sorted(by_row) == [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11]
 
     def h(i, field):
         return by_row[i].harmonized[field]
 
     assert h(0, "grain_size").value == 50.0 and by_row[0].alloy == "Co33.3Cr33.3Ni33.3"
     assert (h(1, "grain_size").status, h(1, "grain_size").reason) == ("not_convertible", "not a number: 'abc'")
     assert by_row[1].reported[GS].text == "abc"
     assert h(2, "composition").status == "not_convertible" and "unknown element symbol 'Xx'" in h(2, "composition").reason
     assert by_row[2].alloy is None and by_row[2].reported["FORMULA"].text == "Xx1 Co1"
     assert h(3, "composition").status == "not_reported" and by_row[3].alloy is None
     assert (h(4, "grain_size").status, h(4, "grain_size").value) == ("converted", -5.0)
     assert h(5, "test_temperature").status == "not_convertible"
     assert by_row[5].reported["PROPERTY: Test temperature ($^\\circ$C)"].text == "25 C"
     assert h(6, "test_type").status == "not_convertible" and "'X'" in h(6, "test_type").reason
     assert by_row[7].group.key is None and by_row[7].group.reason == "no DOI in the source: paper unknown"
     assert by_row[7].paper_doi is None
-    assert all(v.status == "not_convertible" for v in by_row[9].harmonized.values())
-    assert by_row[9].reported["(column 24, no header)"].text == "extra"
-    assert by_row[9].group.key is None
+    assert h(9, "microstructure").value == "FCC+BCC"
     assert h(10, "yield_strength").status == "not_convertible"
     assert h(11, "composition").status == "not_convertible" and "not positive" in h(11, "composition").reason
 
 
 def test_a_file_in_another_layout_is_refused():
-    with pytest.raises(AdapterError, match="header"):
+    with pytest.raises(AdapterError, match="line 1: the header"):
         mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": b"a,b\n1,2\n"}))
     with pytest.raises(AdapterError, match="UTF-8"):
         mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": b"\xff\xfe\x00"}))
 
 
 def test_another_grouping_unit_is_refused():
     with pytest.raises(AdapterError, match="groups by paper"):
         mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted([GOOD])}, grouping_unit="dataset"))
 
 
 def test_altered_bytes_are_refused_before_parsing(version):
     tampered = dataclasses.replace(version, files={"MPEA_dataset.csv": planted([GOOD])})
@@ -242,12 +240,55 @@ def test_grouping_folds_ascii_case_only():
     assert doi_group_key("   ") is None and doi_group_key("doi:") is None
 
 
 def test_compositions_differing_below_the_rounding_step_are_not_identical():
     """Finding 2: the display label rounds to 0.1 at.%; the adapter's compositions do not."""
     result = mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted(
         [_row(c1="Fe50.01 Ni49.99"), _row(c1="Fe50.04 Ni49.96")])}))
     a, b = result.records
     assert a.alloy == b.alloy == "Fe50Ni50"  # the same display label …
     ca, cb = a.harmonized["composition"].value, b.harmonized["composition"].value
     assert ca != cb  # … but not the same composition
     assert ca["Fe"] == pytest.approx(50.01) and cb["Fe"] == pytest.approx(50.04)
+
+
+# --- Strict parsing (finding 3): a malformed file is refused, never partly read --------
+
+def refused(lines, match):
+    with pytest.raises(AdapterError, match=match) as error:
+        mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted(lines)}))
+    assert str(error.value).startswith("MPEA_dataset.csv: line")
+    assert str(error.value).endswith("the file is refused")
+    return str(error.value)
+
+
+def test_an_unterminated_quote_at_the_end_refuses_the_file():
+    # header is line 1; GOOD is line 2; the broken record starts on line 3
+    refused([GOOD, '2,"Co1 Cr1 Ni1,FCC'], r"line 3: the record starting on this line cannot be parsed")
+
+
+def test_an_unterminated_quote_that_swallows_later_rows_refuses_the_file():
+    message = refused([GOOD, GOOD.replace(",A paper", ',"unterminated title'), GOOD, GOOD],
+                      r"line 3: the record starting on this line cannot be parsed")
+    assert "detected at line 5" in message
+
+
+def test_a_malformed_quote_refuses_the_file():
+    refused([GOOD, GOOD.replace("A paper", '"A" paper')], r"^MPEA_dataset.csv: line 3: .*',' expected after")
+
+
+@pytest.mark.parametrize("change,found", [(GOOD + ",extra", 24), (GOOD.rsplit(",", 2)[0], 21)])
+def test_a_wrong_field_count_refuses_the_file_and_names_the_line(change, found):
+    refused([GOOD, GOOD, change, GOOD], rf"^MPEA_dataset.csv: line 4: expected 23 fields, found {found}; ")
+
+
+def test_a_legitimate_quoted_multi_line_field_is_read():
+    multi = GOOD.replace(",A paper", ',"A paper\nwith a second line"')
+    result = mpea_layout.read(sealed("mpea", {"MPEA_dataset.csv": planted([GOOD, multi, GOOD])}))
+    assert [r.source_item_key for r in result.records] == [f"MPEA_dataset.csv:row:{i}" for i in range(3)]
+    assert result.records[1].reported["REFERENCE: title"].text == "A paper\nwith a second line"
+    assert result.records[1].paper_reference == "A paper\nwith a second line"
+
+
+def test_a_wrong_field_count_after_a_multi_line_field_names_both_lines():
+    multi = GOOD.replace(",A paper", ',"A paper\nwith a second line"')
+    refused([multi, multi.rsplit(",", 2)[0] + ',"x\ny"'], r"lines 4-5: expected 23 fields, found 22")
```

## 4. A spreadsheet formula affects only its own field (`f0efe89`)

The planted test is corrected (formula in the grain-size SD, as in the review) and compares every other field with the ordinary row; a formula in Cr affects the composition only.

Commit message:

```
Step 4 fix 4: a spreadsheet formula affects only the field it feeds

Review finding 4: a formula anywhere in a row made all 17 harmonized fields
unconvertible, dropping valid values, the cited assignments and the deliberately
not-reported temperature. A formula cell is now not_convertible for its own field only
(any element column: the composition). The planted test is corrected, not extended:
a formula in the grain-size SD leaves every other value, assignment and the
temperature status as in the ordinary row; a formula in Cr affects the composition only.
The frozen spreadsheet has no formulas.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```diff
diff --git a/hypocurate/sources/adapters/tamu_fcc.py b/hypocurate/sources/adapters/tamu_fcc.py
index 1c418e6..30b2f5b 100644
--- a/hypocurate/sources/adapters/tamu_fcc.py
+++ b/hypocurate/sources/adapters/tamu_fcc.py
@@ -77,24 +77,27 @@ def reported_text(value) -> str:
     if value is None:
         return ""
     if isinstance(value, bool):
         return str(value)
     if isinstance(value, float):
         return repr(value)
     return str(value)
 
 
 def _number(value, unit: str | None) -> Value:
     if value is None or (isinstance(value, str) and value.strip() == ""):
         return Value(None, unit, "not_reported", "blank in the source")
+    if isinstance(value, str) and value.startswith("="):
+        # Only the field this cell feeds is affected (step 4 review, finding 4).
+        return Value(None, unit, "not_convertible", f"the cell holds a formula, not a value: {value!r}")
     if isinstance(value, bool):
         return Value(None, unit, "not_convertible", f"not a number: {value!r}")
     if isinstance(value, (int, float)):
         if not math.isfinite(value):
             return Value(None, unit, "not_convertible", f"not a finite number: {value!r}")
         return Value(float(value), unit, "converted")
     return n.number(str(value), unit)
 
 
 def _composition(cells: dict) -> tuple[Value, str | None]:
     columns: dict[str, float | None] = {}
     for symbol in ELEMENT_COLUMNS:
@@ -162,21 +165,15 @@ def read(version: SealedVersion) -> AdapterResult:
         records.append(_record(version, path, i, values))
     workbook.close()
     return AdapterResult(tuple(records), tuple(blank))
 
 
 def _record(version: SealedVersion, path: str, i: int, values: tuple) -> CommonRecord:
     key = f"{path}:row:{i}"
     reported = {name: Reported(name, reported_text(v), UNITS.get(name)) for name, v in zip(HEADER, values)}
     for extra, v in enumerate(values[len(HEADER):], start=len(HEADER) + 1):
         if v is not None:
             reported[f"(column {extra}, no header)"] = Reported(f"(column {extra}, no header)", reported_text(v), None)
     group = Group("dataset", f"dataset:{DATASET_DOI}")
-    formulas = [name for name, v in zip(HEADER, values) if isinstance(v, str) and v.startswith("=")]
-    if formulas:
-        reason = f"cells hold formulas, not values: {', '.join(formulas)}"
-        harmonized = {name: Value(None, unit, "not_convertible", reason) for name, unit in HARMONIZED_FIELDS.items()}
-        return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, None,
-                            DATASET_REFERENCE, None, group, harmonized, reported)
     harmonized, alloy = _harmonize(dict(zip(HEADER, values)))
     return CommonRecord(version.source_key, version.fingerprint, key, 0, version.data_kind, alloy,
                         DATASET_REFERENCE, None, group, harmonized, reported)
diff --git a/tests/test_adapter_tamu.py b/tests/test_adapter_tamu.py
index 81290c5..30bdfea 100644
--- a/tests/test_adapter_tamu.py
+++ b/tests/test_adapter_tamu.py
@@ -150,45 +150,61 @@ def _row(**changes):
     row = list(GOOD)
     for col, value in changes.items():
         row[int(col[1:])] = value
     return row
 
 
 def test_planted_values_are_kept_and_marked():
     rows = [
         GOOD,
         _row(c4="abc"),           # 1: a percentage that is not a number
         _row(c8=47),              # 2: percentages sum to 99
         _row(c12=None),           # 3: blank yield strength
-        _row(c17="=1+1"),         # 4: a formula, not a value
+        _row(c18="=1+1"),         # 4: a formula in the grain-size SD, not a value
         [None] * 19,              # 5: blank row
         GOOD + ["extra"],         # 6: an extra column
         _row(c17=-5),             # 7: negative grain size: converted as reported, not judged here
         _row(c17="12.5"),         # 8: a number stored as text
+        _row(c4="=A1"),           # 9: a formula in an element column
     ]
     result = tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook(rows)}))
     by_row = {int(r.source_item_key.rsplit(":", 1)[1]): r for r in result.records}
     assert result.blank_rows == (5,)
-    assert sorted(by_row) == [0, 1, 2, 3, 4, 6, 7, 8]
+    assert sorted(by_row) == [0, 1, 2, 3, 4, 6, 7, 8, 9]
 
     def h(i, field):
         return by_row[i].harmonized[field]
 
     assert by_row[0].alloy == "Al4Co8Cr4Cu4Fe16Mn12Ni48V4"
     assert h(1, "composition").status == "not_convertible" and h(1, "composition").reason == "Cr: not a number: 'abc'"
     assert by_row[1].alloy is None and by_row[1].reported["Cr"].text == "abc"
     assert h(2, "composition").reason == "percentages sum to 99, not 100"
     assert h(3, "yield_strength").status == "not_reported"
-    assert all(v.status == "not_convertible" for v in by_row[4].harmonized.values())
-    assert by_row[4].reported["Grain Size(µm)"].text == "=1+1"
+    # Finding 4: only the field the formula cell feeds is affected; everything else is as
+    # in the ordinary row 0, assignments and the deliberately not-reported temperature too.
+    assert h(4, "grain_size_sd").status == "not_convertible"
+    assert h(4, "grain_size_sd").reason == "the cell holds a formula, not a value: '=1+1'"
+    assert by_row[4].reported["SD, Grain Size(µm)"].text == "=1+1"
+    assert {k: v for k, v in by_row[4].harmonized.items() if k != "grain_size_sd"} == \
+        {k: v for k, v in by_row[0].harmonized.items() if k != "grain_size_sd"}
+    assert (h(4, "grain_size").value, h(4, "yield_strength").value) == (23.0, 284.2)
+    assert (h(4, "test_type").status, h(4, "test_type").citation) == ("assigned", tamu_fcc.TEST_TYPE_CITATION)
+    assert h(4, "test_temperature").status == "not_reported"
+    assert h(4, "test_temperature").reason == tamu_fcc.TEMPERATURE_NOT_REPORTED
+    assert by_row[4].alloy == by_row[0].alloy
+    # A formula in an element column affects the composition only.
+    assert h(9, "composition").status == "not_convertible" and h(9, "composition").reason.startswith("Cr: ")
+    assert by_row[9].alloy is None
+    assert {k: v for k, v in by_row[9].harmonized.items() if k != "composition"} == \
+        {k: v for k, v in by_row[0].harmonized.items() if k != "composition"}
     assert by_row[6].reported["(column 20, no header)"].text == "extra"
     assert (h(7, "grain_size").status, h(7, "grain_size").value) == ("converted", -5.0)
     assert (h(8, "grain_size").status, h(8, "grain_size").value) == ("converted", 12.5)
 
 
 def test_another_layout_is_refused():
     with pytest.raises(AdapterError, match="no sheet"):
         tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook([GOOD], sheet="Other")}))
     with pytest.raises(AdapterError, match="header"):
         tamu_fcc.read(sealed("tamu_fcc", {FILE: workbook([GOOD], header=("a",) * 19)}))
     with pytest.raises(AdapterError, match="not a readable spreadsheet"):
         tamu_fcc.read(sealed("tamu_fcc", {FILE: b"not a spreadsheet"}))
```

## 5. Composition parsing never returns a non-finite value (`d2de2d8`)

Scaling by the largest amount before an `fsum` avoids overflow; unrepresentable amounts or ratios and non-finite results are `not_convertible` with the reason.

Commit message:

```
Step 4 fix 5: composition parsing never returns a non-finite value

Review finding 5: large coefficients gave NaN or infinity marked as converted. Amounts
must be finite; the calculation scales by the largest amount before an fsum, so large
finite amounts normalize without overflow; a ratio too extreme to represent, an amount
that underflows to zero, and any non-finite result are not_convertible with the reason.
Percentage columns must be finite too. Tests in tests/test_normalize.py.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```diff
diff --git a/hypocurate/sources/normalize.py b/hypocurate/sources/normalize.py
index 992f927..b3f3756 100644
--- a/hypocurate/sources/normalize.py
+++ b/hypocurate/sources/normalize.py
@@ -46,47 +46,65 @@ def number(text: str, unit: str | None, blank_reason: str = "blank in the source
 def formula_to_atomic_percent(formula: str) -> tuple[dict[str, float] | None, str | None]:
     """A formula string ("Al0.25 Co1 Fe1 Ni1", "CoCrFeMnNi") → atomic percent per element,
     full precision. A missing amount means 1. Returns (composition, None) or (None, reason)."""
     if formula.strip() == "":
         return None, "blank in the source"
     if not _FORMULA.fullmatch(formula):
         return None, f"formula does not parse: {formula!r}"
     amounts: dict[str, float] = {}
     for symbol, amount in _TERM.findall(formula):
         if symbol not in ELEMENTS:
             return None, f"unknown element symbol {symbol!r} in {formula!r}"
         a = float(amount) if amount else 1.0
+        if not math.isfinite(a):
+            return None, f"amount {amount!r} of {symbol} is too large to represent in {formula!r}"
         if a <= 0:
+            if any(c in "123456789" for c in amount):
+                return None, f"amount {amount!r} of {symbol} is too small to represent in {formula!r}"
             return None, f"amount {amount!r} of {symbol} is not positive in {formula!r}"
         amounts[symbol] = amounts.get(symbol, 0.0) + a
-    total = sum(amounts.values())
-    return {e: 100.0 * a / total for e, a in amounts.items()}, None
+    # Numerically safe (step 4 review, finding 5): scale by the largest amount first, so
+    # neither the sum nor 100 * a overflows; refuse a ratio too extreme to represent.
+    largest = max(amounts.values())
+    if not math.isfinite(largest):
+        return None, f"amounts in {formula!r} are too large to represent"
+    scaled = {e: a / largest for e, a in amounts.items()}
+    if any(s == 0.0 for s in scaled.values()):
+        return None, f"the ratio of amounts in {formula!r} is too extreme to represent"
+    total = math.fsum(scaled.values())
+    composition = {e: 100.0 * s / total for e, s in scaled.items()}
+    if not all(math.isfinite(v) and v > 0 for v in composition.values()):
+        return None, f"the composition of {formula!r} is not a finite positive number for every element"
+    return composition, None
 
 
 def percent_columns_to_atomic_percent(columns: dict[str, float | None]
                                       ) -> tuple[dict[str, float] | None, str | None]:
     """Columns of atomic percentages, one per element → atomic percent per element.
     Elements at 0 are absent from the alloy. A blank column, a negative value or a sum
     other than 100 is reported, never rescaled."""
     for symbol in columns:
         if symbol not in ELEMENTS:
             return None, f"unknown element symbol {symbol!r}"
     blank = [e for e, v in columns.items() if v is None]
     if blank:
         return None, f"blank percentage for {', '.join(blank)}"
+    infinite = [e for e, v in columns.items() if not math.isfinite(v)]
+    if infinite:
+        return None, f"percentage not a finite number for {', '.join(infinite)}"
     negative = [e for e, v in columns.items() if v < 0]
     if negative:
         return None, f"negative percentage for {', '.join(negative)}"
-    total = sum(columns.values())
-    if abs(total - 100.0) > PERCENT_SUM_TOLERANCE:
+    total = math.fsum(columns.values())
+    if not math.isfinite(total) or abs(total - 100.0) > PERCENT_SUM_TOLERANCE:
         return None, f"percentages sum to {total:g}, not 100"
     return {e: float(v) for e, v in columns.items() if v > 0}, None
 
 
 def alloy_label(composition: dict[str, float]) -> str:
     """An alloy name **for display only**: elements in alphabetical order, each with its
     atomic percent rounded to 0.1 (the reference script's naming,
     `docs/reference/worked_example.py`).
 
     Equal labels do not mean the same alloy: Fe50.01Ni49.99 and Fe50.04Ni49.96 both read
     `Fe50Ni50` (step 4 review, finding 2). The record carries the full-precision
     composition; when two compositions count as the same alloy is a plan and
diff --git a/tests/test_normalize.py b/tests/test_normalize.py
new file mode 100644
index 0000000..dfd1d3b
--- /dev/null
+++ b/tests/test_normalize.py
@@ -0,0 +1,46 @@
+"""Step 4 fix, review finding 5: composition parsing never returns a non-finite value.
+
+Before the fix, large coefficients gave NaN or infinity marked as converted (labels such
+as "FeinfNi0"). The calculation now scales by the largest amount first, and refuses
+amounts or ratios it cannot represent."""
+import math
+
+import pytest
+
+from hypocurate.sources.normalize import formula_to_atomic_percent, percent_columns_to_atomic_percent
+
+HUGE = "9" * 308  # about 1e308: finite, but two of them overflow a plain sum
+
+
+def test_a_coefficient_too_large_to_represent_is_refused():
+    composition, reason = formula_to_atomic_percent(f"Fe{'9' * 400} Ni1")
+    assert composition is None and "too large to represent" in reason
+
+
+def test_large_finite_coefficients_are_normalized_without_overflow():
+    composition, reason = formula_to_atomic_percent(f"Fe{HUGE} Ni{HUGE}")
+    assert reason is None
+    assert composition == {"Fe": pytest.approx(50.0), "Ni": pytest.approx(50.0)}
+    composition, reason = formula_to_atomic_percent(f"Fe{HUGE} Ni{HUGE} Co{HUGE} Cr{HUGE}")
+    assert reason is None and all(math.isfinite(v) for v in composition.values())
+
+
+def test_a_ratio_too_extreme_to_represent_is_refused():
+    composition, reason = formula_to_atomic_percent(f"Fe0.{'0' * 330}1 Ni{HUGE}")
+    assert composition is None and "too small to represent" in reason
+    composition, reason = formula_to_atomic_percent(f"Fe0.{'0' * 300}1 Ni{HUGE}")
+    assert composition is None and "too extreme to represent" in reason
+
+
+def test_every_converted_composition_is_finite_and_sums_to_100():
+    for formula in ("Fe1 Ni1", "Al0.25 Co1 Fe1 Ni1", f"Fe{HUGE} Ni1", "Fe1 Ni0.000001"):
+        composition, reason = formula_to_atomic_percent(formula)
+        assert reason is None, formula
+        assert all(math.isfinite(v) and v > 0 for v in composition.values())
+        assert math.fsum(composition.values()) == pytest.approx(100.0)
+
+
+def test_non_finite_percentages_are_refused():
+    for bad in (math.inf, -math.inf, math.nan):
+        composition, reason = percent_columns_to_atomic_percent({"Fe": 50.0, "Ni": bad})
+        assert composition is None and "not a finite number for Ni" in reason
```

## 6. Test weakness: hand-written expected strings (`f569d2b`)

Expected strings for cells of BBA01, BBA02 and BBA09, written out from the file's XML (`xl/worksheets/sheet1.xml`).

Commit message:

```
Step 4 review: reported spreadsheet text checked against hand-written strings

Review test weakness: the preserved-values test computed its expectations with the
adapter's own formatter. A new test compares cells of BBA01, BBA02 and BBA09 with
strings written out from the file's XML.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```diff
diff --git a/tests/test_adapter_tamu.py b/tests/test_adapter_tamu.py
index 30bdfea..051cbbc 100644
--- a/tests/test_adapter_tamu.py
+++ b/tests/test_adapter_tamu.py
@@ -45,24 +45,48 @@ def test_one_record_per_sample_none_dropped(records, sheet_rows):
     assert all(r.source_key == "tamu_fcc" and r.kind == "measured" and r.item_index == 0 for r in records)
 
 
 def test_every_value_is_kept_as_reported(records, sheet_rows):
     for record, row in zip(records, sheet_rows):
         assert list(record.reported) == list(tamu_fcc.HEADER)
         assert [r.text for r in record.reported.values()] == [tamu_fcc.reported_text(v) for v in row]
     units = records[0].reported
     assert (units["Grain Size(µm)"].unit, units["YS (MPa)"].unit, units["Hardness, HV"].unit) == ("µm", "MPa", "HV")
     assert units["Al"].unit is None  # the header states none; the paper does (citation on the value)
 
 
+# Review, test weakness: expected strings written out by hand, not computed with the
+# adapter's own formatter. Source: the cell values in the file's XML
+# (xl/worksheets/sheet1.xml, rows 2, 3 and 9). The XML stores some doubles at 17
+# significant digits (K2 "140.19999999999999", N2 "34.299999999999997"); the reported text
+# is the shortest decimal that reads back as the same double ("140.2", "34.3"). Integer
+# cells read as integers ("4", "301"), and an empty cell is "".
+EXPECTED_TEXT = {
+    "BBA01": {"Iteration": "BBA", "Alloy Name": "BBA01", "Al": "4", "Co": "8", "Cr": "4", "Ni": "48",
+              "Hardness, HV": "140.2", "SD, HV": "3.8", "YS (MPa)": "284.2", "SD, YS": "34.3",
+              "Cold Work (%Reduction)": "60", "Recrystallization Temp(℃)": "950", "Holding time (h)": "0.5",
+              "Grain Size(µm)": "23", "SD, Grain Size(µm)": "13"},
+    "BBA02": {"Cr": "0", "Ni": "52", "Hardness, HV": "151.5", "YS (MPa)": "301", "SD, YS": "6.6",
+              "Grain Size(µm)": "31.94", "SD, Grain Size(µm)": "18.45"},
+    "BBA09": {"Cu": "0", "V": "12", "Hardness, HV": "200.9", "SD, HV": "8", "YS (MPa)": "", "SD, YS": "",
+              "Grain Size(µm)": "30.79", "SD, Grain Size(µm)": "22.57"},
+}
+
+
+def test_reported_text_matches_independently_written_strings(records):
+    by_name = {r.reported["Alloy Name"].text: r for r in records}
+    for name, expected in EXPECTED_TEXT.items():
+        assert {col: by_name[name].reported[col].text for col in expected} == expected, name
+
+
 def test_the_sample_without_yield_strength_is_kept(records):
     missing = [r for r in records if r.harmonized["yield_strength"].status != "converted"]
     assert [r.reported["Alloy Name"].text for r in missing] == ["BBA09"]
     assert missing[0].harmonized["yield_strength"].reason == "blank in the source"
     assert missing[0].harmonized["grain_size"].status == "converted"
 
 
 def test_one_group_the_dataset(records):
     assert {r.group.key for r in records} == {"dataset:10.5281/zenodo.22798856"}
     assert {r.group.unit for r in records} == {"dataset"}
     assert {r.paper_reference for r in records} == {tamu_fcc.DATASET_REFERENCE}
     assert {r.paper_doi for r in records} == {None}
```

## README (`4aad3a2`)

Three lines on the grouping key, the display-only label and strict parsing.

Commit message:

```
README: grouping key, display-only alloy label, strict CSV parsing (step 4 review fixes)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
```

```diff
diff --git a/README.md b/README.md
index 64ae32e..107172c 100644
--- a/README.md
+++ b/README.md
@@ -123,15 +123,18 @@ To check that the origins still serve the same bytes (needs network; never overw
 ## Sources and adapters
 
 The three sources (`mpea`, `tamu_fcc`, `controlled_duplicates`) are defined in `hypocurate/sources/versions.py`. Registering one stores the data files its adapter reads as a `source_version` and seals it. The files digest and identity are computed as the database computes them, and the database checks them again.
 
 ```
 hypocurate sources register              # all three; registering again changes nothing
 hypocurate sources test tamu_fcc -n 3    # the first 3 records, in the common record format, as JSON
 ```
 
 - Registration reads only paths inside `data/` (checked after resolving `..` and links), and refuses a file whose SHA-256 differs from `data/manifest.json`, or a source already registered with different interpretation settings.
 - Registration writes no run or hypothesis version, so `hc_write_lock` does not apply. It locks the source row first (`SELECT … FOR UPDATE`) and runs in `run_transaction` (`hypocurate/db/retry.py`), which retries the whole transaction on `40P01` and `40001`.
 - An adapter reads a **sealed** version (`load_sealed_version` re-checks every file's bytes against the seal) and returns one record per data row in the format of `hypocurate/sources/record.py`. Every value is kept as reported, with its unit. Every harmonized value has a status: `converted`, `not_reported`, `not_convertible` (with the reason) or `assigned` (with the passage of the source's documentation that states it). Adapters never decide eligibility and never drop or correct a record.
+- A paper's group key is derived from its DOI (whitespace trimmed, a URL or `doi:` wrapper removed, ASCII case-folded); the DOI itself is kept as reported.
+- The alloy label (0.1 at.% rounding) is for display only. Records carry the full-precision composition; when two compositions count as the same alloy is a plan setting (step 6).
+- A CSV file with a quoting error or a row of the wrong length is refused as a whole, with the file, line and reason; no partial extraction is returned.
 - "Test connection" runs in a read-only transaction.
 - The controlled duplicate extract is registered with `enabled = false`: it is constructed test data.
 - Not yet run on the live database: registering there is a later step and needs the owner.
```

## Test output

```
$ .venv/bin/pytest -v tests/test_adapter_mpea.py tests/test_adapter_extract.py tests/test_adapter_tamu.py tests/test_normalize.py tests/test_reference_counts_from_adapters.py
tests/test_adapter_mpea.py::test_one_record_per_row_none_dropped PASSED  [  1%]
tests/test_adapter_mpea.py::test_every_value_is_kept_as_reported_with_its_unit PASSED [  3%]
tests/test_adapter_mpea.py::test_every_record_has_the_common_fields_with_their_units PASSED [  5%]
tests/test_adapter_mpea.py::test_numbers_are_converted_unchanged PASSED  [  6%]
tests/test_adapter_mpea.py::test_grain_size_counts PASSED                [  8%]
tests/test_adapter_mpea.py::test_nothing_in_the_frozen_file_is_unconvertible PASSED [ 10%]
tests/test_adapter_mpea.py::test_test_type_codes PASSED                  [ 11%]
tests/test_adapter_mpea.py::test_no_value_is_assigned PASSED             [ 13%]
tests/test_adapter_mpea.py::test_display_labels_follow_the_reference_naming PASSED [ 15%]
tests/test_adapter_mpea.py::test_paper_identity_is_the_doi PASSED        [ 16%]
tests/test_adapter_mpea.py::test_the_record_format_has_no_decision_fields PASSED [ 18%]
tests/test_adapter_mpea.py::test_planted_values_are_kept_and_marked PASSED [ 20%]
tests/test_adapter_mpea.py::test_a_file_in_another_layout_is_refused PASSED [ 21%]
tests/test_adapter_mpea.py::test_another_grouping_unit_is_refused PASSED [ 23%]
tests/test_adapter_mpea.py::test_altered_bytes_are_refused_before_parsing PASSED [ 25%]
tests/test_adapter_mpea.py::test_text_is_kept_exactly_as_reported PASSED [ 26%]
tests/test_adapter_mpea.py::test_formatting_differences_do_not_split_a_paper[10.1016/J.ACTAMAT.2019.04.017] PASSED [ 28%]
tests/test_adapter_mpea.py::test_formatting_differences_do_not_split_a_paper[ 10.1016/j.actamat.2019.04.017 ] PASSED [ 30%]
tests/test_adapter_mpea.py::test_formatting_differences_do_not_split_a_paper[doi:10.1016/j.actamat.2019.04.017] PASSED [ 31%]
tests/test_adapter_mpea.py::test_formatting_differences_do_not_split_a_paper[DOI: 10.1016/j.actamat.2019.04.017] PASSED [ 33%]
tests/test_adapter_mpea.py::test_formatting_differences_do_not_split_a_paper[https://doi.org/10.1016/j.actamat.2019.04.017] PASSED [ 35%]
tests/test_adapter_mpea.py::test_formatting_differences_do_not_split_a_paper[http://dx.doi.org/10.1016/J.ActaMat.2019.04.017] PASSED [ 36%]
tests/test_adapter_mpea.py::test_formatting_differences_do_not_split_a_paper[HTTPS://DOI.ORG/10.1016/j.actamat.2019.04.017] PASSED [ 38%]
tests/test_adapter_mpea.py::test_grouping_folds_ascii_case_only PASSED   [ 40%]
tests/test_adapter_mpea.py::test_compositions_differing_below_the_rounding_step_are_not_identical PASSED [ 41%]
tests/test_adapter_mpea.py::test_an_unterminated_quote_at_the_end_refuses_the_file PASSED [ 43%]
tests/test_adapter_mpea.py::test_an_unterminated_quote_that_swallows_later_rows_refuses_the_file PASSED [ 45%]
tests/test_adapter_mpea.py::test_a_malformed_quote_refuses_the_file PASSED [ 46%]
tests/test_adapter_mpea.py::test_a_wrong_field_count_refuses_the_file_and_names_the_line[1,Co1 Cr1 Ni1,FCC,CAST,FCC,50.0,,8.0,,T,25.0,300.0,,,,,,,,,10.1/x,2020,A paper,extra-24] PASSED [ 48%]
tests/test_adapter_mpea.py::test_a_wrong_field_count_refuses_the_file_and_names_the_line[1,Co1 Cr1 Ni1,FCC,CAST,FCC,50.0,,8.0,,T,25.0,300.0,,,,,,,,,10.1/x-21] PASSED [ 50%]
tests/test_adapter_mpea.py::test_a_legitimate_quoted_multi_line_field_is_read PASSED [ 51%]
tests/test_adapter_mpea.py::test_a_wrong_field_count_after_a_multi_line_field_names_both_lines PASSED [ 53%]
tests/test_adapter_extract.py::test_sixteen_records_with_origin_keys PASSED [ 55%]
tests/test_adapter_extract.py::test_each_record_equals_its_mpea_row_except_the_changed_columns PASSED [ 56%]
tests/test_adapter_extract.py::test_a_renamed_formula_gives_the_same_composition PASSED [ 58%]
tests/test_adapter_extract.py::test_paper_unknown_is_marked_never_invented PASSED [ 60%]
tests/test_adapter_extract.py::test_a_constructed_doi_is_its_own_paper PASSED [ 61%]
tests/test_adapter_tamu.py::test_one_record_per_sample_none_dropped PASSED [ 63%]
tests/test_adapter_tamu.py::test_every_value_is_kept_as_reported PASSED  [ 65%]
tests/test_adapter_tamu.py::test_reported_text_matches_independently_written_strings PASSED [ 66%]
tests/test_adapter_tamu.py::test_the_sample_without_yield_strength_is_kept PASSED [ 68%]
tests/test_adapter_tamu.py::test_one_group_the_dataset PASSED            [ 70%]
tests/test_adapter_tamu.py::test_assigned_values_carry_their_passage PASSED [ 71%]
tests/test_adapter_tamu.py::test_assigned_and_reported_stay_distinguishable PASSED [ 73%]
tests/test_adapter_tamu.py::test_temperature_is_not_reported PASSED      [ 75%]
tests/test_adapter_tamu.py::test_composition_in_atomic_percent PASSED    [ 76%]
tests/test_adapter_tamu.py::test_agrees_with_the_authors_csv_view PASSED [ 78%]
tests/test_adapter_tamu.py::test_planted_values_are_kept_and_marked PASSED [ 80%]
tests/test_adapter_tamu.py::test_another_layout_is_refused PASSED        [ 81%]
tests/test_adapter_tamu.py::test_the_batch_grouping_unit_is_refused_until_the_owner_decides PASSED [ 83%]
tests/test_adapter_tamu.py::test_records_serialize_to_json PASSED        [ 85%]
tests/test_normalize.py::test_a_coefficient_too_large_to_represent_is_refused PASSED [ 86%]
tests/test_normalize.py::test_large_finite_coefficients_are_normalized_without_overflow PASSED [ 88%]
tests/test_normalize.py::test_a_ratio_too_extreme_to_represent_is_refused PASSED [ 90%]
tests/test_normalize.py::test_every_converted_composition_is_finite_and_sums_to_100 PASSED [ 91%]
tests/test_normalize.py::test_non_finite_percentages_are_refused PASSED  [ 93%]
tests/test_reference_counts_from_adapters.py::test_mpea_77_records_from_20_papers PASSED [ 95%]
tests/test_reference_counts_from_adapters.py::test_mpea_rows_are_those_of_the_reference_script PASSED [ 96%]
tests/test_reference_counts_from_adapters.py::test_tamu_21_records_from_9_alloys PASSED [ 98%]
tests/test_reference_counts_from_adapters.py::test_pooled_98_records_22_alloys PASSED [100%]
============================== 60 passed in 1.35s ==============================

$ .venv/bin/pytest -q   (whole suite)
467 passed in 60.79s (0:01:00)
```
