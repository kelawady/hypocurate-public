# Build step 4b — review packet for the second model

Date: 2026-10-05. Branch: `step-04b-assumptions`. Code reviewed: commit `b8837ee` (this packet and the summary are added in the next commit and change no code). GitHub Actions on that commit: success, 527 passed, runtime image OK, https://github.com/kelawady/hypocurate/actions/runs/37263110672.

Generated from the files on disk by a script, so every file below is quoted exactly.

## How to use this packet

You are reviewing step 4b of HypoCurate, a small step before PRD 15 step 5: an **assumptions register** (`hypocurate/assumptions.json`, one entry per assumption made so far, validated by a schema test), a **read-only page** for it (GET /assumptions, behind the login), and two new working rules in CLAUDE.md (items 11 and 12): every new assumption or changed default enters the register in the same merge, and code reads each default from one named place, which an "applied: yes" entry names and a test checks.

Not in this step: applying any of the owner's eight decisions of 2026-10-05 in code, recomputing the reference numbers, any other screen, any migration. No change to `render.yaml`, workflows, the Dockerfile, Compose or dependencies.

Your review is advice; the test suite is the gate. Please return a dated findings file. Each finding will be accepted (and fixed with a regression test) or rejected with a one-line reason.

Use the fixed checklist in section 2, answering each item yes, no or not applicable, with a reason for every "no". For this step the most relevant questions are:
- **Completeness and accuracy of the register**: is any assumption in the code, the PRD or the summaries missing, or is any entry stated more strongly than the code or the sources support (for example "applied: yes" where the code does less)?
- **The settings test**: does it fail when a named default changes without the register? What would it miss?
- **Read-only and login**: can the page change anything, and is it public anywhere?
- **The owner's decisions g and a**: both are recorded, not applied. g conflicts with PRD 5.10 and is flagged as a safeguard change for review in step 7; a uses a new status "assigned by decision". Are they stated so that step 6/7 cannot apply them silently?
- **The owner's microstructure decision** (after the first build): the Texas A&M microstructure is "single-phase FCC", assigned by decision, with its basis and caveats in the entry (summary section "The owner's decision on the Texas A&M microstructure"). Is the entry's evidence quoted accurately, and are the caveats visible?
- The "Questions for the reviewer" at the end of the summary.

## Contents

1. Step summary
2. Reviewer checklist
3. CLAUDE.md (with the new items 11 and 12)
4. The register: `hypocurate/assumptions.json`
5. Code: `hypocurate/assumptions.py`, `hypocurate/web/app.py`, templates, stylesheet, image check
6. Tests: `tests/test_assumptions.py`
7. Suite output

## Files added, modified or deleted since `main` (step 4 live record, `355e2c3`)

```
M	CLAUDE.md
A	docs/reviews/step04b_review_packet.md
A	docs/reviews/step04b_summary.md
A	hypocurate/assumptions.json
A	hypocurate/assumptions.py
M	hypocurate/web/app.py
M	hypocurate/web/static/style.css
A	hypocurate/web/templates/assumptions.html
M	hypocurate/web/templates/base.html
M	hypocurate/web/templates/home.html
M	scripts/check_runtime_image.py
A	tests/test_assumptions.py
```

Diff of the modified files other than new ones:

```diff
diff --git a/CLAUDE.md b/CLAUDE.md
index c178d6f..2e18544 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -21,6 +21,9 @@ The full specification is `docs/PRD_sprint1.md`. Read the relevant section befor
 9. **Any change to `.github/workflows/` needs the owner's explicit review**, even if the workflow tests pass. A workflow test cannot stop its own job from being skipped (for example by a job-level condition), and Render counts a skipped check as passed.
 10. **A change to `render.yaml` takes effect at push, before the checks pass**, and redeploys the code already running (Render's Blueprint sync; seen on the step 3 merge, 2026-10-05). So any setting that depends on new code goes in a later merge than that code, and every `render.yaml` change needs the owner's explicit review, like workflow changes.
 
+11. **Assumptions register.** Any new assumption or changed default is entered in `hypocurate/assumptions.json` in the same merge, with its reason, who decided it and when, and its earlier value in the history. The page /assumptions is generated from that file only.
+12. **One named place per default.** Code reads a default from one named setting (a module constant, a source definition, a plan default or a database constraint), never from a literal scattered through the code. A register entry marked "applied: yes" names that setting; `tests/test_assumptions.py` fails if it does not exist or holds a different value.
+
 ## Rules the code must never break
 
 1. **Code decides; agents advise.** Inclusion of records, flags, the choice of test, data sufficiency and the verdict are computed by code. No language model output may set them.
diff --git a/hypocurate/web/app.py b/hypocurate/web/app.py
index b995da4..15e6504 100644
--- a/hypocurate/web/app.py
+++ b/hypocurate/web/app.py
@@ -1,4 +1,5 @@
-"""The web service (PRD Section 6): login, health page, and a placeholder home page.
+"""The web service (PRD Section 6): login, health page, a placeholder home page, and the
+read-only assumptions register (step 4b, /assumptions).
 
 Every page needs the shared login except exactly /login and /health, and the
 files under /static/. The session is a signed cookie (Starlette
@@ -17,6 +18,7 @@ from fastapi.templating import Jinja2Templates
 from sqlalchemy import Engine
 from starlette.middleware.sessions import SessionMiddleware
 
+from hypocurate import assumptions
 from hypocurate.config import Settings, load_settings
 from hypocurate.db.engine import database_reachable, make_engine
 from hypocurate.db.migrate import schema_status
@@ -35,10 +37,16 @@ def create_app(
     settings: Settings | None = None,
     engine: Engine | None = None,
     login_throttle: LoginThrottle | None = None,
+    register: list[dict] | None = None,
 ) -> FastAPI:
     settings = settings or load_settings()
     engine = engine or make_engine(settings.database_url)
     throttle = login_throttle or LoginThrottle()
+    # Read and validated once at start: an invalid register stops the service starting.
+    if register is None:
+        register = assumptions.load_register()
+    else:
+        assumptions.validate(register)
 
     app = FastAPI(title="HypoCurate", docs_url=None, redoc_url=None, openapi_url=None)
 
@@ -91,6 +99,18 @@ def create_app(
         request.session.clear()
         return RedirectResponse("/login", status_code=303)
 
+    @app.get("/assumptions", response_class=HTMLResponse)
+    def assumptions_page(request: Request, review: str | None = None):
+        """Read-only: generated from hypocurate/assumptions.json; nothing is edited here."""
+        not_reviewed_only = review == "not_reviewed"
+        return templates.TemplateResponse(request, "assumptions.html", {
+            "sections": assumptions.page_sections(register, not_reviewed_only=not_reviewed_only),
+            "counts": assumptions.summary_counts(register),
+            "not_reviewed_only": not_reviewed_only,
+            "categories": assumptions.CATEGORIES,
+            "review_labels": assumptions.REVIEW_STATUSES,
+        })
+
     @app.get("/health")
     def health(request: Request) -> Response:
         db_ok = database_reachable(engine)
diff --git a/hypocurate/web/static/style.css b/hypocurate/web/static/style.css
index acebaaf..7002065 100644
--- a/hypocurate/web/static/style.css
+++ b/hypocurate/web/static/style.css
@@ -11,3 +11,22 @@ button { margin-top: 12px; padding: 8px 16px; border: 0; border-radius: 4px; bac
 .error { color: var(--bad); }
 .ok { color: var(--good); }
 th { text-align: left; padding-right: 16px; color: var(--muted); font-weight: 500; }
+/* Assumptions register (step 4b): plain table; full styling comes with the step 10 screens. */
+main.wide { max-width: 72rem; }
+.nav { display: flex; align-items: center; gap: 16px; }
+.muted { color: var(--muted); }
+a { color: var(--accent); }
+code { font-size: 0.9em; overflow-wrap: anywhere; }
+.register { width: 100%; border-collapse: collapse; margin-bottom: 2rem; }
+.register th, .register td { text-align: left; vertical-align: top; padding: 8px 12px 8px 0; }
+.register thead th { border-bottom: 2px solid var(--line); }
+.register tbody { border-bottom: 1px solid var(--line); }
+.register tr.more td { padding-top: 0; }
+.register .unreviewed-scientific td:first-child { border-left: 4px solid var(--bad); padding-left: 8px; }
+.badge { display: inline-block; margin-left: 6px; padding: 0 6px; border-radius: 4px; font-size: 0.85em; }
+.badge.unreviewed { background: #fdecea; color: var(--bad); }
+.badge.open-badge { background: #fff4e5; color: #8a4b00; }
+details summary { cursor: pointer; color: var(--muted); }
+dl { margin: 8px 0; } dt { font-weight: 600; margin-top: 6px; } dd { margin-left: 0; }
+dd ul { margin: 0; padding-left: 1.2em; }
+@media (max-width: 48rem) { .register thead { display: none; } .register td { display: block; padding-right: 0; } }
diff --git a/hypocurate/web/templates/base.html b/hypocurate/web/templates/base.html
index 612d9ba..a83a0a1 100644
--- a/hypocurate/web/templates/base.html
+++ b/hypocurate/web/templates/base.html
@@ -8,6 +8,6 @@
 </head>
 <body>
   <header><span class="brand">HypoCurate</span>{% block nav %}{% endblock %}</header>
-  <main>{% block content %}{% endblock %}</main>
+  <main{% block main_attrs %}{% endblock %}>{% block content %}{% endblock %}</main>
 </body>
 </html>
diff --git a/hypocurate/web/templates/home.html b/hypocurate/web/templates/home.html
index 49a8587..8bde491 100644
--- a/hypocurate/web/templates/home.html
+++ b/hypocurate/web/templates/home.html
@@ -3,5 +3,5 @@
 {% block content %}
 <h1>Signed in</h1>
 <p>The skeleton is running. The screens arrive in build step 10.</p>
-<p><a href="/health">Health</a></p>
+<p><a href="/assumptions">Assumptions</a> · <a href="/health">Health</a></p>
 {% endblock %}
diff --git a/scripts/check_runtime_image.py b/scripts/check_runtime_image.py
index b5958c8..f4f02a5 100644
--- a/scripts/check_runtime_image.py
+++ b/scripts/check_runtime_image.py
@@ -25,7 +25,10 @@ REQUIRED = ["hypocurate/web/main.py", "hypocurate/worker.py", "data/manifest.jso
             # Step 4: the sources are registered and read from inside the deployed image.
             "hypocurate/sources/versions.py", "hypocurate/sources/adapters/__init__.py",
             "data/sources/mpea/MPEA_dataset.csv", "data/sources/tamu_fcc/Grain_Size_Summary_v3.xlsx",
-            "data/controlled_duplicates/extract.csv"]
+            "data/controlled_duplicates/extract.csv",
+            # Step 4b: the assumptions register and its page.
+            "hypocurate/assumptions.json", "hypocurate/assumptions.py",
+            "hypocurate/web/templates/assumptions.html"]
 FORBIDDEN_DIRS = {"tests", "docs", "reviews", "fixtures", "scripts"}
 FORBIDDEN_NAMES = re.compile(r"(truth.*|build.*\.py|step\d\d_.*|checklist\.md|conftest\.py|test_.*\.py)$")
```

## 1. Step summary

### `docs/reviews/step04b_summary.md`

````markdown
# Build step 4b — summary for review

Date: 2026-10-05. Branch: `step-04b-assumptions`. **Status: built, suite green; awaiting the second-model review.** A small step before step 5, on the owner's instruction: an assumptions register and a read-only page for it. It is not a PRD Section 15 step.

The suite is the gate. This summary is for the second-model review (PRD 13.2), which uses `docs/reviews/checklist.md`.

The owner approved the plan on 2026-10-05, after six questions (below), with additions: nine more entries and a summary line on the page. After the first build, the owner decided the one open entry, the Texas A&M microstructure (section "The owner's decision on the Texas A&M microstructure"); the register and this summary were updated, with no code that applies it.

**Not built, as instructed:**
- applying any of the eight decisions in code;
- recomputing the reference numbers;
- any other screen;
- any migration.

There is no change to `render.yaml`, `.github/workflows/`, the Dockerfile, Compose, dependencies or the migration.

## What was built

| Path | What it is |
|---|---|
| `hypocurate/assumptions.json` | **The register: one source file**, a JSON list with one object per assumption (the same pattern as `docs/glossary.json`). 60 entries, all in force; no open decision since the owner's decision on the Texas A&M microstructure. |
| `hypocurate/assumptions.py` | It provides:<br>• `load_register()` and `validate()`: the schema, in plain Python with no new dependency;<br>• `resolve_setting()` and `check_settings()`: the named settings in code;<br>• `page_sections()` and `summary_counts()`: what the page shows. |
| `hypocurate/web/app.py` | `GET /assumptions`:<br>• behind the existing login middleware (nothing new is public);<br>• no other method: POST, PUT, PATCH and DELETE give 405;<br>• the register is read and validated once when the service starts, so **an invalid register stops the service starting**;<br>• `create_app` takes an optional `register` for tests, and validates it too. |
| `hypocurate/web/templates/assumptions.html` | The page:<br>• a summary line (entries, open decisions, scientific assumptions not reviewed by an expert);<br>• open decisions first, then one table per category (scientific, statistical, data handling, operational);<br>• columns: assumption and statement, value, what it affects, expert review, applied in code;<br>• each unreviewed scientific entry has a red left border and the badge "Not reviewed by an expert";<br>• each row expands (`<details>`, no JavaScript) to the reason, evidence, who decided and when, sensitivity analysis, the named settings or the step, earlier values, notes and the key;<br>• a filter `?review=not_reviewed` ("Show only: not reviewed by an expert" / "Show all");<br>• the only form is "Sign out". |
| `hypocurate/web/templates/base.html` | A `main_attrs` block, so this page can widen `<main>`. The other pages render as before. |
| `hypocurate/web/templates/home.html` | A link to Assumptions. |
| `hypocurate/web/static/style.css` | Plain table and badge styles in the login page's colours, with a narrow-screen layout. Full styling and the per-run "assumptions in force" panel come at step 10. |
| `scripts/check_runtime_image.py` | `REQUIRED` gains the register, its module and the template, so the deployed image must contain the page. |
| `CLAUDE.md` | "How we work":<br>• **item 11**: any new assumption or changed default enters the register in the same merge;<br>• **item 12**: code reads a default from one named place, never a scattered literal; an "applied: yes" entry names it, and `tests/test_assumptions.py` fails if it does not exist or holds a different value. |
| `tests/test_assumptions.py` | 58 tests (below). |

## The register's schema

Every entry has these fields. Unknown fields are refused, and so are missing ones.

| Field | Content |
|---|---|
| `key` | Lower-case identifier, unique. |
| `name`, `statement` | A short name and a plain-English statement. |
| `state` | `in_force` or `open` (an open decision has `value: null`, `decided: null` and `pending: {by, before_step}`). |
| `value` | `{text, unit}`; unit may be null. |
| `category` | `scientific`, `statistical`, `data_handling` or `operational`. |
| `affects` | What it affects. |
| `reason`, `evidence` | The reason, and a non-empty list of evidence or citations. |
| `decided` | `{by, date}`. |
| `expert_review` | `{status, name, date}`, where status is `not_reviewed` (no name or date), `accepted` or `disputed` (both need a name and a date). |
| `sensitivity` | The sensitivity analysis that covers it, or null. |
| `applied` | Either `{status: "yes", settings: [{ref, equals?}…], note}`, with at least one named setting, or `{status: "not_yet", step: 5–12, note}`. |
| `history` | Earlier values `{value, from, to, note}`, in date order, ending no later than the current decision. |
| `notes` | PRD conflicts and open points. |

**Named settings** (`ref`) have one of four forms:

| Form | Example |
|---|---|
| `python:<module>:<name>[.<attribute or key>…]` | `python:hypocurate.sources.versions:SOURCES.tamu_fcc.grouping_unit` |
| `python:<module>:<function>(<parameter>)` | `python:hypocurate.db.retry:run_transaction(attempts)`, the parameter's default |
| `sql:<name>` | `sql:ck_source_file_max_size`, a whole word in the migrations |
| `file:<repository path>:<text>` | `file:Dockerfile:--workers 1` |

An optional `equals` gives the value the code must hold. Sets are compared sorted and tuples as lists.

## The entries (60)

Who decided, abbreviated:
- **Owner**: owner (Khalid El-Awady);
- **PRD**: PRD v1.6 (owner);
- **Ref.**: reference script and PRD v1.6 (owner);
- **Implicit**: "implicit in PRD v1.6 and the reference script" (the owner's wording).

Every entry's expert review is **not reviewed**.

### The owner's decision on the Texas A&M microstructure (2026-10-05, after the first build)
| Key | Category | Value | Applied |
|---|---|---|---|
| `tamu_microstructure` | scientific | single-phase FCC, **assigned by decision** | not yet: step 6 |

It was the one open decision in the first build (`state: open`, pending the owner before step 6); its history records that.

### The owner's eight decisions of 2026-10-05
| Key | Category | Value | Applied |
|---|---|---|---|
| `tamu_test_temperature` (a) | scientific | room temperature, **assigned by decision** | not yet: step 6 |
| `permitted_test_types` (b) | scientific | tension only; sensitivity "tension and compression together" | not yet: step 6 |
| `tamu_grouping_unit` (c) | statistical | one group (the dataset); sensitivity "six batches as six groups" | **yes**: `SOURCES.tamu_fcc.grouping_unit == "dataset"` (the sensitivity analysis is step 7's) |
| `same_alloy_rule` (d) | scientific | round to 0.1 at.%, same alloy when the rounded compositions are identical; sensitivity at 1 at.% | not yet: step 6 |
| `fixed_minimums` (e) | statistical | 30 records; 5 alloys; 10 papers; 10 residual df | not yet: step 6 (plan default; check in step 7) |
| `values_disagree_tolerance` (f) | data handling | > 2%, relative to the smaller value | not yet: step 6 |
| `calibration_noise_levels` (g) | statistical | estimated from frozen residuals by a method fixed at the rules lock; smallest effect default 150 | not yet: step 7 |
| `tag_starting_lists` (h) | data handling | the three lists as given | not yet: step 6 |

**"Unless you find otherwise":** decision c is already applied. The Texas A&M source definition has grouping unit `dataset`, and the adapter refuses any other unit (step 4).

### All other entries
| Category | Key | Decided by | Applied |
|---|---|---|---|
| scientific | `shared_coefficient`, `exponent_fixed`, `baseline_per_alloy`, `quasistatic_tests` | Implicit | not yet: 7, 7, 7, 6 |
| scientific | `grain_size_as_reported`, `yield_strength_as_reported`, `composition_as_reported` | Implicit | yes (`HARMONIZED_FIELDS` units) |
| scientific | `mean_grain_size_only` | Implicit | not yet: 7 |
| scientific | `model_form`, `alloy_eligibility`, `physical_validity_checks` | PRD | not yet: 7, 6, 6 |
| scientific | `room_temperature_scope` (20–25 °C), `fcc_microstructure_scope`, `grain_size_floor` (< 0.1 µm excluded) | Ref. | not yet: 6 (test side only today) |
| scientific | `tamu_test_type`, `tamu_phase_class` | Owner (step 4 rule) | yes (`TEST_TYPE_CITATION`, `PHASE_CITATION`) |
| statistical | `ols_alloy_intercepts`, `cluster_robust_se`, `one_sided_test`, `validity_checks`, `pooled_gives_verdict`, `calibration_simulation`, `reference_test_tolerance` | PRD | not yet: 7 |
| statistical | `p_threshold_comparison` (p < 0.05) | Owner, 2026-10-05 | not yet: 7 |
| statistical | `papers_independent` | Implicit | yes (`SOURCES.mpea.grouping_unit == "paper"`) |
| statistical | `normal_errors_in_calibration` | Implicit | not yet: 7 |
| statistical | `sufficiency_options` | PRD | yes (`ck_plan_sufficiency_option`, `ck_run_exploratory_needs_verdict`, `hc_run_update`) |
| statistical | `power_information_only` | Owner, step 3 | yes (`ck_plan_sufficiency_option`) |
| data handling | `tamu_composition_unit` | Owner (step 4 rule) | yes (`COMPOSITION_UNIT_CITATION`) |
| data handling | `mpea_microstructure_label_trusted`, `curated_values_trusted` | Implicit | yes (`HARMONIZED_FIELDS.microstructure`; `mpea_layout.read`) |
| data handling | `paper_grouping_by_doi`, `values_kept_as_reported`, `malformed_files_refused`, `composition_normalization`, `alloy_label_display_only`, `controlled_extract_disabled` | Owner, step 4 | yes |
| data handling | `assigned_value_statuses` | Owner, 2026-10-05 | not yet: 6 |
| data handling | `grain_size_transformation_at_analysis` | Owner, step 4 | not yet: 6 |
| data handling | `duplicate_identity`, `unresolved_duplicates`, `scope_not_confirmed` | PRD | not yet: 6 |
| data handling | `duplicate_survivor_rule` | Owner, step 1 | not yet: 6 |
| operational | `stored_file_limits`, `login_throttle`, `session_length`, `secret_lengths`, `single_web_process`, `transaction_retries`, `worker_poll_interval` | Owner, steps 2–4 | yes |
| operational | `spending_caps` | PRD | not yet: 9 |

**Added while writing the owner's additional entries** (the owner asked for others of this kind):
- `mean_grain_size_only`: the grain-size distribution width is not used. The Texas A&M source studies it as a predictor.
- `composition_as_reported`: nominal and measured compositions are not distinguished.
- `mpea_microstructure_label_trusted`: the compilation's phase label is taken as the phase constitution.

**Left out on purpose:**
- the CLAUDE.md "never break" rules, which are invariants, not assumptions: model recall never pooled, code decides, the checkpoints, the wording;
- the model per agent (PRD 17 #2, undecided; step 8);
- the storage estimate;
- Render plans and region.

**Keys renamed from the plan while writing:**

| Plan | Register |
|---|---|
| `same_alloy_tolerance` | `same_alloy_rule` |
| `calibration_assumptions` | `calibration_noise_levels` |
| `assigned_values_need_citation` | `assigned_value_statuses` |
| `password_lengths` | `secret_lengths` |
| `paper_grouping_doi` | `paper_grouping_by_doi` |
| `tamu_phase_fcc` | `tamu_phase_class` |
| `tamu_test_type_tension` | `tamu_test_type` |
| `sufficiency_default_option` | `sufficiency_options` |
| `calibration_simulations` | `calibration_simulation` |

## The owner's answers (2026-10-05)

1. **Decision g and PRD 5.10.**
   - Recorded as "the estimation method is fixed at the rules lock and applied by code after the dataset freeze; no person or agent chooses the values".
   - The notes record:
     - the conflict with PRD 5.10, which says these values are fixed at the rules lock and never estimated from the real outcomes;
     - that this is a **safeguard change needing a second-model review in step 7 before it is applied**;
     - the alternative to compare in that review: report calibration both ways, with data-derived noise levels and with the fixed defaults.
2. **Decision a and the rule for assigned values: two statuses.**
   - **"Assigned from source"** rests on an explicit quoted statement in the source's documentation.
   - **"Assigned by decision"** rests on a recorded owner or expert decision, citing its basis.
   - Entry `assigned_value_statuses` states the rule. Today the code has one status, `assigned`, which requires a citation and is used only for source statements; the split arrives in step 6.
   - Decision a is "assigned by decision".
   - **For step 6:** the reference plan names a sensitivity analysis that accepts only reported values and values assigned from source, so the effect of every decision-based assignment is visible.
3. **Decision d.**
   - It is stated as the rule that produced the reference numbers: round each element to the nearest 0.1 at.%; same alloy when the rounded compositions are identical. This is transitive by construction.
   - Known weakness: compositions closer than the step can fall into different bins at a boundary.
   - Sensitivity analysis: the same rule at 1 at.%.
   - The earlier wording "each within 0.1 at.%" appeared nowhere in the repository or the memory files; the register uses the corrected wording.
   - **For step 6, a possible improvement, not a decision:** tolerance-based grouping, which needs a stated rule for chains and the owner's approval.
4. **Decision f.**
   - Relative difference = |a − b| / min(|a|, |b|).
   - **The pairing is not stated as final.** Open point for step 6, to be settled with the owner's approval:
     - repeat specimens in one source (same paper, alloy, grain size and conditions) are legitimate separate measurements;
     - a conflict is two records claiming to be the same measurement that disagree, mainly different sources reporting the same paper.
5. **FCC scope:** first recorded as an open decision entry, with the phase-constitution search reported below. The owner then decided it (next section).
6. **p-value against the threshold: p < α**, decided now. This closes step 3's "p < vs ≤" item.

**Additions at approval:**
- the nine "implicit" entries, each with a statement and what it affects:
  - (a) `shared_coefficient`, with its note on the ≈427 vs ≈1173 per-source estimates and per-source estimates as its sensitivity analysis;
  - (b) `grain_size_as_reported`;
  - (c) `yield_strength_as_reported`;
  - (d) `exponent_fixed`;
  - (e) `baseline_per_alloy`;
  - (f) `quasistatic_tests`;
  - (g) `papers_independent`;
  - (h) `curated_values_trusted`;
  - (i) `normal_errors_in_calibration`;
- a summary line with the count of open decisions and of unreviewed scientific assumptions;
- open decisions shown first.

## Texas A&M phase constitution: what the source states (owner's request)

**Searched:**
- `paper/main.tex` and `paper/supplementary.tex` of `ArroyaveLab/2026-mulukutla-hall-petch` at the pinned commit `11390ee516c1a17cacdde318b40d5d6889d4007f`, fetched 2026-10-05.
- Their SHA-256 equal the values recorded in step 4:
  - `main.tex`: `81fb864c…221836038e`;
  - `supplementary.tex`: `8dfe9731…d447461317`.
- Search terms (case-insensitive): single-phase, single phase, secondary/second phase, precipitate, XRD, X-ray, EBSD, recrystalli*, phase stability, design criteria, BCC, L1, sigma, intermetallic, homogeni*, and every mention of FCC.

**Passages about the lab's own alloys (verbatim):**

- `paper/main.tex` line 138 (introduction):
  > Hall-Petch parameters for FCC alloys are usually reported a few compositions at a time. Of the 630 alloys compiled by Borg et al., 27 single-phase FCC compositions carry grain size together with yield strength, drawn from 25 separate studies~\cite{Borg2020}. Six carry grain size, yield strength and hardness together. The 81 compositions measured here carry all three, under one processing route and one characterization protocol. This is the largest such set reported for single-phase FCC multi-principal element alloys, and it lets composition, processing and grain size be separated without correcting across studies.

- `paper/main.tex` line 173 (dataset), from its last three sentences:
  > The BB campaign contributes 35 candidates from batches BBA, BBB, and BBC, including 34 with YS. It explored composition under an FCC phase stability constraint while holding processing fixed. The complete BB-campaign synthesis and specimen preparation workflow is documented in Ref.~\cite{Mulukutla2026BRAVE}.

  The line opens with "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system." (step 4's citation for phase class FCC).

- `paper/main.tex` line 175:
  > Candidate alloys were iteratively selected from an FCC-constrained, manufacturable design space with the models updated after each iteration using the newly acquired data.

- `paper/main.tex` line 177:
  > Overall, both campaigns used the same high level production route: high-purity elemental feedstock was vacuum arc melted, homogenized, cold rolled, recrystallized, and quenched. Energy-dispersive X-ray spectroscopy (EDS) and X-ray diffraction were used to check realized chemistry and phase constitution, while electron microscopy and EBSD documented the microstructure.

- `paper/supplementary.tex` line 61:
  > It explored the Al--Co--Cr--Cu--Fe--Mn--Ni--V system under an FCC phase-stability constraint while holding processing fixed.

- `paper/supplementary.tex` line 65:
  > Both campaigns followed the same high-level route of vacuum-arc melting from high-purity elements, homogenization, cold rolling, recrystallization, and quenching. EDS and XRD checked realized chemistry and phase constitution; SEM and EBSD documented the microstructure; and quasistatic tensile and Vickers indentation measurements supplied YS and HV.

- `paper/supplementary.tex` line 367 (a limitation of a strength model, not a statement about the samples):
  > Approximated elastic properties, calibration transfer, phase or local-order effects, and the subtraction used to define experimental friction stress can all contribute.

Other hits concern the literature (Borg et al.'s single-phase FCC records, `supplementary.tex` lines 461 and 465; the Table S12 caption on the Al₀.₃ alloys, line 439) or acknowledgements (line 597). No hit for secondary phase, precipitate (in the lab's alloys), sigma, intermetallic or L1₂.

**Does any amount to an explicit statement that the 94 conditions are single-phase? My reading: no.** The decision is the owner's; nothing was assigned.
- The closest is `main.tex` line 138. It calls "the 81 compositions measured here" "the largest such set reported for single-phase FCC multi-principal element alloys", which implies that the authors regard their alloys as single-phase FCC. But:
  - it is a comparative sentence in the introduction, not a methods or results statement;
  - it says 81 compositions, while the spreadsheet has 82 distinct compositions (step 1).
- Lines 173/175 and supplementary line 61 state a design **constraint** (FCC phase stability), not an observed result.
- Line 177 and supplementary line 65 say XRD and EDS **checked** phase constitution, without stating the outcome.

The question was left open in the first build.

## The owner's decision on the Texas A&M microstructure (2026-10-05)

**Decision:** the Texas A&M microstructure is "single-phase FCC", status "assigned by decision" (owner). Entry `tamu_microstructure` changed from open to in force:
- **Evidence, each with file and line (verbatim, in the entry):**
  - `main.tex` line 138: the authors describe their measured compositions as single-phase FCC;
  - the FCC design constraint: `main.tex` line 173 and `supplementary.tex` line 61 (BB campaign), and `main.tex` line 175 (CB campaign);
  - the XRD phase check: `main.tex` line 177 and `supplementary.tex` line 65.
- **Notes in the entry:**
  - the paper says 81 compositions and the spreadsheet has 82;
  - no passage states the result of the XRD check;
  - not reviewed by an expert.
- **Applied:** not yet, step 6. Today the adapter still reports the microstructure as not reported.
- **Sensitivity analysis:** the source-only analysis (reported values and values assigned from source only) shows the result without these records.
- **History:** "not reported: the source does not state the phases present per record (open decision)", 2026-10-05.

Register and summary only; no code applies it. With this, the register has no open decision, and the page's summary line reads "0 open decisions".

**MPEA microstructure** (computed from the adapter output, scratchpad script; nothing committed):
- All **77** reference records have microstructure exactly `FCC`.
- Among the 237 rows with a grain size:

| Microstructure | Rows |
|---|---|
| `FCC` | 107 |
| `BCC` | 36 |
| `FCC+Sec.` | 23 |
| (blank) | 9 |
| `FCC+HCP` | 8 |
| `BCC+FCC` | 6 |
| `BCC+B2`, `BCC+Sec.`, `Other` | 5 each |
| `FCC+BCC`, `B2+BCC`, `FCC+B2`, `BCC+Laves+Sec.` | 4 each |
| `BCC+Laves`, `FCC+BCC+Sec.` | 3 each |
| `FCC+L12+Sec.`, `BCC+B2+Laves` | 2 each |
| `BCC+HCP`, `BCC+BCC+HCP`, `FCC+B2+Sec.`, `FCC+L12`, `FCC+L12+B2`, `FCC+FCC`, `B2` | 1 each |

## Tests (527, all passing; 58 new; no test from an earlier step changed)

`git diff main --stat -- tests/` shows only the new `tests/test_assumptions.py`.

| Group | Tests |
|---|---|
| Schema | The file validates. Every category has entries, and keys are unique. The eight decisions are present: decided by the owner on 2026-10-05, not reviewed, applied as stated (c applied, the others not yet, at their steps). The owner's wording is checked (assigned by decision; rounded compositions identical, with no "within"; min(\|a\|, \|b\|) and "not final"; g's statement and its three notes; p < 0.05). The Texas A&M microstructure decision is recorded as decided (in force, owner, 2026-10-05, not reviewed, step 6, the six citations, the three notes, the sensitivity analysis, the open-decision history), and no decision is open. An open decision (a fixture, since the register has none) validates, and is refused if it carries a value or a decision. |
| Validator | 25 malformed cases, each refused with its message: missing or unknown field, bad key, category, state, blank text, empty evidence, bad dates, review status, a name without a review, accepted or disputed without a name or date, "applied: yes" with no setting or without `settings`, bad status, step outside 5–12, history out of order or after the decision, open/in-force inconsistencies. Also duplicate keys, an empty register, and an open decision (fixture) without `pending` or with a past step. |
| **Settings in code** | **Every "applied: yes" entry's settings resolve, and every `equals` matches the code** (25 entries). The values compared are spot-checked. 11 references to nothing are refused (missing constant, module, mapping key or parameter; a parameter without a default; a missing or partial SQL name; a wrong Dockerfile text; a path outside the repository; a missing file; an unknown kind). A wrong value and a missing setting are reported with the key. JSON terms are used for sets and tuples. |
| Page | Login is required for `/assumptions`, the filter URL and `/assumptions/`. Headings are in category order, every entry appears in its section, in register order. With an open decision added (fixture register), "Open decisions" comes first, holds only that entry, shows "Not decided" and the badge, and the summary counts it. Summary counts on the real register: 0 open decisions, 20 unreviewed scientific entries. The unreviewed-scientific mark is on exactly the right entries (with a fixture register where one scientific entry is reviewed). The filter shows exactly the not-reviewed entries (fixture with one accepted and one disputed entry). A row expands to reason, evidence, history, notes and sensitivity, and shows named settings or the step. The only form is sign-out, there is no input, and POST/PUT/PATCH/DELETE give 405. The service refuses an invalid register. The home page links to the page. |

### Tests changed after the owner's microstructure decision (none weakened)

The register no longer has an open decision, so three tests that used the real open entry now use a fixture:
- `test_open_decisions_have_no_value_in_force` asserted that `tamu_microstructure` was the one open entry. It is replaced by `test_the_microstructure_decision_is_recorded_and_no_decision_is_open`, which checks the decision and that no entry is open. The open-entry rules it covered are kept by the new `test_an_open_decision_has_no_value_in_force`, on a fixture open entry; that test also checks the refusal of an open entry carrying a value or a decision.
- `test_an_open_decision_needs_who_decides_and_by_when` builds its entry with the same fixture; its assertions are unchanged.
- `test_the_page_shows_every_entry_grouped_with_open_decisions_first` is renamed `test_the_page_shows_every_entry_grouped_by_category`. It expects the four category headings, because the register has no open decision; the section-by-section checks are unchanged. "Open decisions first" is now tested by the new `test_open_decisions_are_shown_first_when_there_are_any` (fixture register).
- `test_the_summary_line_counts_open_decisions_and_unreviewed_scientific_entries` now asserts "0 open decisions" explicitly.

### The safeguard tests fail when the safeguard is removed

Each change was made in a scratch copy of the working tree, and only `tests/test_assumptions.py` was run. The copy was then discarded.

| Change in the copy | Result |
|---|---|
| `WINDOW_SECONDS` 15 → 10 minutes | the settings test fails (and the reporting test, which uses that entry) |
| `PERCENT_SUM_TOLERANCE` renamed | the settings test fails |
| Texas A&M `grouping_unit` → `batch` | the settings test fails |
| Dockerfile `--workers 1` → `--workers 2` | the settings test fails |
| The validator accepts "applied: yes" with an empty settings list | the validator test for that case fails |
| The "Not reviewed by an expert" badge removed from the template | the mark test fails |
| The filter ignored | the filter test fails |

### Suite results
After the owner's microstructure decision (commit `b8837ee`):
```
$ pytest -q                              (Codespace, Python 3.14.2, `docker compose up -d db`)
527 passed in 61.29s
```
GitHub Actions, commit `b8837ee` (the last change to the register and tests): success; "Run the suite in the test image": 527 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37263110672

First build (commit `8f7df59`), before that decision:
```
$ pytest -q                              525 passed in 73.41s
$ docker compose run --rm test           (the test image, rebuilt) 525 passed in 79.35s
```
The default (Render) image was built locally then: `scripts/check_runtime_image.py` on its `/app` said "runtime image OK", and inside the image `load_register()` read all 60 entries.
GitHub Actions, commit `8f7df59`: success, 525 passed, runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37262162090

The step 1 answer-isolation scan (`test_no_row_answers_under_package`) passes with the register in the package. The register names the compression record by its origin key `MPEA_dataset.csv:row:139`, not in the answer file's wording.

## Deviations from the approved plan

1. **`base.html` gained a `main_attrs` block**, because `<main>` is 32 rem wide. The login, home and health pages render as before (their tests are unchanged and pass).
2. **The service refuses to start with an invalid register.** The plan did not say what happens then. A broken register therefore fails CI (the schema test) before any merge, and on Render a failed start keeps the previous version running.
3. **`markupsafe.escape`** is used in one page test to compare escaped text. markupsafe is already in the runtime lock (Jinja2 depends on it). No dependency change.
4. **Nine entry keys were renamed** from the plan (table above), and three entries were added while writing (above).

## PRD corrections and clarifications for the next PRD update

1. **PRD 5.10 (calibration assumptions):**
   - The scatter and per-paper shift are estimated by code from the frozen dataset's residuals after the freeze, by a method fixed at the rules lock (owner's decision g).
   - This replaces "never estimated from the real outcomes".
   - It is a safeguard change, reviewed before it is applied in step 7, against the alternative of reporting both ways.
2. **PRD 5.3 and 17 #4 (values disagree):** 2%, relative to the smaller value, for yield strength and grain size. The PRD recommended 15% for yield strength only. Which records are compared is open (repeat specimens are not conflicts).
3. **PRD 5.5 and 17 #7 (tag lists):** the owner's lists replace the recommendation.
4. **PRD 5.7 and 17 #9 (Texas A&M grouping unit):** one group, confirmed; "six batches" is a sensitivity analysis.
5. **PRD 5.8 and 17 #1 (fixed minimums):** 30, 5, 10 and 10, confirmed by the owner. The expert review is still pending.
6. **PRD 5.7 (verdict rule):** supported when p < α (strictly below).
7. **PRD 5.3 and 10 (assigned values):** two statuses, "assigned from source" and "assigned by decision", kept distinguishable. The reference plan names a sensitivity analysis that excludes decision-based assignments.
8. **PRD 10 (Texas A&M):** "82 single-phase FCC compositions" now rests on the owner's decision (assigned by decision), not on a statement in the source; the source says 81 compositions, and no passage states the XRD result. Step 4's correction 3 is resolved this way.
9. **PRD 10 (same alloy):** the rule is 0.1 at.% rounding with identical rounded compositions, with a 1 at.% sensitivity analysis. Step 4's correction 6 is resolved.
10. **PRD 9 and 15:** a read-only Assumptions page (step 4b), with the per-run "assumptions in force" panel at step 10; and CLAUDE.md "How we work", items 11 and 12.

## Open items

1. **Step 6** (each is in the register with its step):
   - apply decisions a, b, d, e, f and h, and the two assigned-value statuses;
   - the source-only sensitivity analysis;
   - the pairing for decision f (owner's approval);
   - apply the Texas A&M microstructure decision ("single-phase FCC", assigned by decision);
   - the room-temperature scope must accept the assigned band, with a test that the 21 Texas A&M records stay eligible.
2. **Before step 7:** recompute the reference numbers. Tension only removes `MPEA_dataset.csv:row:139` from the 77. The same-alloy rule is unchanged, so the alloy count changes only through that record. Update CLAUDE.md's "Reference numbers" when recomputed.
3. **Step 7:** the second-model review of decision g (both ways) before it is applied.
4. **Expert review:** every entry is "not reviewed". The page lists 20 scientific entries for Prof. El-Awady. A review is recorded in the register (status, name, date) in a reviewed merge.
5. **Carried, unchanged:** the step 4 open items (live registration after the owner's decisions; step 5 approved inputs; step 6 guards), and the step 3 step 7/9 requirements. The step 3 "p < vs ≤" item is closed by decision O.

## Questions for the reviewer

1. Is any assumption already in the code, the PRD or the summaries missing from the register, or stated more strongly than the code does?
2. Does the settings test ("applied: yes" names a setting that exists and holds the stated value) catch a default changed in code without the register? Which defaults would it miss (for example a literal that no entry names)?
3. Is refusing to start on an invalid register the right behaviour for the web service?
4. Is the page read-only in every way that matters (no form, no method other than GET, nothing written)?
````

## 2. Reviewer checklist

### `docs/reviews/checklist.md`

```markdown
# Second-model review checklist

**Status: approved by the owner as a working draft, 2026-10-04.** Drafted from PRD Section 13.2 and the rules in `CLAUDE.md`. This is the fixed checklist given to the reviewer at every review. It may be amended after its first use in step 2; any amendment needs the owner's approval.

## When a review is required (PRD 13.2)
- At the end of each build step in PRD Section 15.
- Whenever a change touches a safeguard: the access rules, the plan lock, the inclusion and eligibility rules, or the statistics. Any change to a safeguard also needs the owner's approval, however small.

## What the reviewer is given
1. The changes since the last review: a review packet with the full text of every changed code, test and script file, and the test output.
2. The core rules:
   - the access contract (PRD 4);
   - the plan lock and dataset freeze (PRD 5.6);
   - "stored is not the same as analysed" (PRD 5.3);
   - "a narrower question is a separate record" (PRD 5.4).
3. This checklist.

## Minimum questions (PRD 13.2, verbatim)
1. Can any role reach outcome values it should not see?
2. Can anything change after the lock?
3. Are records ever dropped or overwritten in the store?
4. Do the eligibility rules match Section 5.3?
5. Are the statistics what the plan states?
6. Are there untested paths?
7. Are secrets or keys exposed?

## Rule-by-rule checks
Answer each with yes, no or not applicable to this change. Give a reason for every "no".

**Who decides**
- [ ] Code alone sets inclusion, flags, the choice of test, data sufficiency and the verdict. No language model output can set any of them. (CLAUDE.md rule 1)

**Access contract (PRD 4)**
- [ ] Every agent reads data only through the access layer, using a per-role, per-stage allow-list of fields. Is anything not on the list withheld?
- [ ] A disallowed call raises `AccessDenied` and writes an audit-log row.
- [ ] Outcome values cannot leak through any of these:
  - flag numbers;
  - values as originally reported;
  - nested fields;
  - text handed between stages.
- [ ] The tests cover a role's **complete** input: prompt, every tool response and handed-over text. Do they include the planted-value test for the Planner and the Critic?
- [ ] Pipeline code reads input files only from an explicit list of approved files. Are `tests/` and `docs/reviews/`, which hold expected answers, outside that list? Directory placement alone is a convention, not enforcement.
- [ ] The Curator is not told the direction of the claim.
- [ ] The Critic gets the kind of each flag, never the numbers.

**Checkpoints (PRD 5.6)**
- [ ] Rules lock before curation fixes all of these, with a fingerprint and a time:
  - the model;
  - scope;
  - exclusion rules;
  - eligibility rules;
  - the data-sufficiency option;
  - sensitivity analyses.
- [ ] Dataset freeze before analysis fixes the record sets, with a fingerprint and a time.
- [ ] After each checkpoint, nothing changes, by agent or by person. Is every attempt rejected and logged?
- [ ] A later removal appears only as a labelled sensitivity analysis and never changes the verdict.

**Stored is not analysed (PRD 5.3)**
- [ ] Every record found is kept. Nothing is deleted or overwritten in place.
- [ ] Eligibility is decided by code under the locked rules. Do the defaults match the PRD 5.3 table?
- [ ] Duplicates require all of these: the same original paper, alloy, grain size, value and test conditions. Is matching alloy and grain size alone kept from counting?
- [ ] The survivor of a duplicate pair follows the owner's rule:
  1. the record that comes directly from the original paper (detected by its DOI);
  2. then the fixed source order MPEA, Texas A&M, controlled extract;
  3. then the lowest row.
- [ ] Conflicting records are preserved, not automatically pooled.
- [ ] Physical checks never use the relationship under test.
- [ ] Model-recalled data are never pooled and never count toward a verdict.

**Statistics (PRD 5.7, 5.8, 5.10)**
- [ ] Only the one supported model is used:
  - OLS with alloy intercepts;
  - k × d^-1/2;
  - cluster-robust standard errors by paper, with the small-sample correction;
  - a one-sided test of k > 0 at 0.05, against t with (groups − 1) degrees of freedom;
  - only alloys with at least 2 distinct grain sizes.
- [ ] Both validity checks are applied to every analysis and can never be waived:
  1. Can a coefficient be fitted?
  2. Are there at least 1 residual degree of freedom and at least 2 groups?
  
  If check 2 fails, is only the coefficient reported?
- [ ] Data sufficiency is the option fixed at rules lock. Does "use what is available" waive only the threshold, and label the result exploratory?
- [ ] Calibration is a flag, not a gate. Is "calibration unavailable" shown with its reason when inference cannot run?
- [ ] Do the reference numbers still reproduce within the stated tolerances, with no tolerance widened?

**Outcomes and wording**
- [ ] A narrower question is a separate, linked record. Does the original get no verdict? (PRD 5.4)
- [ ] Are the three kinds of "nothing found" kept distinct: reported negative, missing evidence, failed search? (PRD 3.1)
- [ ] Are outcomes stated "in the sources searched"? Is it never claimed that data "do not exist"?

**Cost (PRD 8)**
- [ ] Is every model call recorded with tokens and actual cost (`model_call`)?
- [ ] Are the caps enforced: $2 per run, $50 per month?

**Data and tests**
- [ ] Do frozen files match their pinned fingerprints, with the manifest's own fingerprint and the list of required files pinned in the tests? (PRD 10, 15)
- [ ] Has no test been weakened, skipped or deleted, and no tolerance widened?
- [ ] Are new paths covered by tests?
- [ ] Has nothing been built ahead of the current step, and nothing from the backlog (PRD 18)?

**Secrets**
- [ ] Are there no keys, database URLs or passwords in code, tests, logs or committed files? Does `.env.example` hold names only?

## What comes back (PRD 13.2)
- A dated findings file in `docs/reviews/`.
- Each finding is either accepted, which means a fix plus a regression test, or rejected with a one-line reason in the same file.
- **Authority:** the reviewer advises; the test suite is the gate. A review cannot approve a change that fails the suite. A finding is acted on only after the owner accepts it.
```

## 3. CLAUDE.md

### `CLAUDE.md`

```markdown
# HypoCurate — instructions for Claude Code

Version: 2026-10-04 v1. Owner: Khalid El-Awady.

## What this is

HypoCurate takes a scientific hypothesis in words (first domain: grain-size strengthening in metal alloys), searches registered data sources, and ends in one of three outcomes stated for the sources searched: **sufficient** (a test and a verdict), **partly sufficient** (no verdict on the original question; a narrower question is a separate linked record), or **insufficient** (a gap report, never a forced verdict).

The full specification is `docs/PRD_sprint1.md`. Read the relevant section before you write code. If this file and the PRD disagree, stop and ask.

## How we work

1. **One build step at a time.** The build order is PRD Section 15. Do not start a step until the owner says so. Do not build ahead.
2. **Plan first.** For each step, propose a plan and wait for approval before changing files.
3. **Tests are the gate.** Every step adds tests to the regression suite. A step is finished only when the whole suite passes. Never weaken, skip or delete a test to make it pass; never widen a tolerance. If a test seems wrong, stop and ask.
4. **End of each step:** write a short summary in `docs/reviews/` (what was built, which tests were added, what is open) so a second model (ChatGPT) can review it. Its review is advice; the tests decide.
5. **Any change to a safeguard** (access layer, checkpoints, validity checks, eligibility rules) needs the owner's approval and a second-model review, even if small.
6. **Ask one question at a time**, in plain English, with options and a recommendation.
7. **Deferred ideas go in the backlog** (PRD Section 18). Do not build them.
8. Small commits with clear messages. Never commit to `main` anything that fails the suite.
9. **Any change to `.github/workflows/` needs the owner's explicit review**, even if the workflow tests pass. A workflow test cannot stop its own job from being skipped (for example by a job-level condition), and Render counts a skipped check as passed.
10. **A change to `render.yaml` takes effect at push, before the checks pass**, and redeploys the code already running (Render's Blueprint sync; seen on the step 3 merge, 2026-10-05). So any setting that depends on new code goes in a later merge than that code, and every `render.yaml` change needs the owner's explicit review, like workflow changes.

11. **Assumptions register.** Any new assumption or changed default is entered in `hypocurate/assumptions.json` in the same merge, with its reason, who decided it and when, and its earlier value in the history. The page /assumptions is generated from that file only.
12. **One named place per default.** Code reads a default from one named setting (a module constant, a source definition, a plan default or a database constraint), never from a literal scattered through the code. A register entry marked "applied: yes" names that setting; `tests/test_assumptions.py` fails if it does not exist or holds a different value.

## Rules the code must never break

1. **Code decides; agents advise.** Inclusion of records, flags, the choice of test, data sufficiency and the verdict are computed by code. No language model output may set them.
2. **Access contract (PRD Section 4).** Every agent reads data only through the access layer, which holds an allow-list of fields per role and stage. Anything else raises `AccessDenied` and is written to the audit log. Tests check a role's *complete* input, including a planted-value test.
   - Planner: fills template parameters; sees counts only, never outcome values.
   - Curator: extraction only; is not told the direction of the claim; has no say over inclusion.
   - Critic: classifies flags from sources and metadata; is told the kind of flag, not the numbers; never sees outcomes.
   - Analyst: explains results that code has already computed.
   - Commentator: outside the decision path; a different model; optional. Its numbers are checked against the run record; label: "numbers checked against the run record".
3. **Two checkpoints (PRD 5.6).** *Rules lock* before curation: the model, scope, exclusion rules and data-sufficiency option are fixed. *Dataset freeze* before analysis: the record set is fixed and fingerprinted. Nothing changes after its checkpoint, by agent or by person. Later removals are sensitivity analyses only and never change the verdict.
4. **Stored is not analysed (PRD 5.3).** Every record found is kept. Eligibility for the test is a separate decision by code under the locked rules. Conflicting records are preserved, not automatically pooled.
5. **Two validity checks that can never be waived (PRD 5.7).** (1) Can a coefficient be fitted? (2) Is inference valid (at least 1 residual degree of freedom and at least 2 independent groups)? If 1 passes and 2 fails: report the coefficient only, with no uncertainty, no p-value and no verdict.
6. **One supported model in sprint 1.** Yield strength = baseline per alloy + k × (grain size in µm)^-1/2; ordinary least squares with alloy intercepts; cluster-robust standard errors grouped by paper with the small-sample correction; one-sided test of k > 0 at 0.05 against a t distribution with (groups − 1) degrees of freedom; only alloys with at least 2 distinct grain sizes. Do not add models.
7. **Data sufficiency is a query parameter fixed at rules lock (PRD 5.8).** Default: fixed minimum (30 records, 5 alloys with at least 2 grain sizes, 10 independent papers, 10 residual degrees of freedom). "Use what is available" waives the threshold only, never the validity checks, and labels the result exploratory.
8. **A narrower question is a separate record**, linked to the original. The original gets no verdict.
9. **Three kinds of "nothing found" stay distinct:** a reported negative result, missing evidence, and a failed search.
10. **Model-recalled data are never pooled** and never count toward a verdict.
11. **Per-run calibration (PRD 5.10) is a flag, not a gate.** When inference cannot run, show "calibration unavailable" with the reason. Software correctness (pass/fail against an independent reference) is separate from calibration (a reported finding).
12. **Every model call is recorded** with tokens and actual cost (`model_call`). Spending caps: $2 per run, $50 per month.
13. **Wording:** outcomes are always stated "in the sources searched". Never write that data "do not exist".

## Environment

- Development happens in a GitHub Codespace. Nothing lives on the owner's laptop. The site runs on Render: pushing to `main` on GitHub deploys it.
- Stack: Python, FastAPI + Jinja + HTMX, one background worker (same code as the command line), PostgreSQL + Alembic, DSPy + litellm, statsmodels/scipy, Docker from day one (`Dockerfile`, `docker-compose.yml`, `render.yaml`).
- Repository layout: PRD Section 6.1.
- **Secrets** (API keys, database URL, login password) live in `.env` locally and in Render environment variables. Never commit them, print them, or put them in tests. Keep `.env.example` with names only.
- Do not create Render services or anything else that costs money without asking first.

## Reference material in `docs/`

- `PRD_sprint1.md` — the specification (PDF copy alongside).
- `HypoCurate_Combined_Overview_2026-10-04_v3.13.pdf` — background and research questions.
- `glossary.json` — the 41 explanation texts for popups and the Help page. One source; do not duplicate the texts in templates.
- `mockup_screens/` — the nine target screens.
- `reference/worked_example.py`, `reference/calibration_example.py` — the scripts that produced the reference numbers. They contain file paths from another machine; treat them as a statement of method, not as code to import.

## Reference numbers (fixed-plan test, PRD 14.1a)

Pooled: 98 records, 22 alloys, 21 groups, 75 residual degrees of freedom, k = 428 ± 64, p ≈ 8e-7. First source alone (MPEA): 77 records, 20 papers, k = 427 ± 61, p ≈ 6e-7. Second source alone (Texas A&M): coefficient ≈ 1173, one group, no uncertainty, no verdict.
```

## 4. The register

### `hypocurate/assumptions.json`

```json
[
{
  "key": "tamu_test_temperature",
  "name": "Texas A&M test temperature",
  "state": "in_force",
  "statement": "The Texas A&M records are treated as tested at room temperature. The value is 'assigned by decision': the source does not report it and does not state it explicitly.",
  "value": {"text": "room temperature (assigned by decision)", "unit": null},
  "category": "scientific",
  "affects": "Whether the 94 Texas A&M records fall inside a room-temperature scope; with them, the pooled reference result (PRD 14.1a).",
  "reason": "Quasistatic tensile tests reported without a temperature are, by convention, room-temperature tests. The paper's Table S12 caption says all values in that table are room temperature, and the table lists this dataset's own fitted slope.",
  "evidence": [
    "ArroyaveLab/2026-mulukutla-hall-petch@11390ee5 paper/supplementary.tex line 439 (caption of Table S12): \"All values are room temperature and, except where noted, are fitted to tensile yield strength.\"",
    "paper/supplementary.tex line 451 (row of Table S12): \"This work, Family~3 M3 & 766 & 14.7--212 & shared fitted slope \\\\\"",
    "Step 4 summary, 'Texas A&M: what the source states': no methods statement on test temperature."
  ],
  "decided": {"by": "owner (Khalid El-Awady)", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": "The source-only analysis (reported values and values assigned from source only) shows the effect of this and every other decision-based assignment.",
  "applied": {"status": "not_yet", "step": 6, "note": "Today the adapter reports the temperature as not reported (tamu_fcc.TEMPERATURE_NOT_REPORTED)."},
  "history": [
    {"value": "not reported: the source states no test temperature for its own measurements", "from": "2026-10-05", "to": "2026-10-05", "note": "Step 4 adapter, pending the owner's decision."}
  ],
  "notes": ["Uses the status 'assigned by decision' (see entry 'assigned_value_statuses')."]
},
{
  "key": "permitted_test_types",
  "name": "Permitted test types",
  "state": "in_force",
  "statement": "The default plan accepts tension tests only. Compression tests are kept in the store and enter only the sensitivity analysis 'tension and compression together'.",
  "value": {"text": "tension only", "unit": null},
  "category": "scientific",
  "affects": "Which records enter the primary analysis; the MPEA reference set (one compression record among the 77).",
  "reason": "Yield strength in compression can differ from yield strength in tension for the same material, so the two are not pooled by default.",
  "evidence": ["Step 1 summary, open item 2; step 4 summary, 'Owner's addition' (the 77 reference records: 76 tension, 1 compression)."],
  "decided": {"by": "owner (Khalid El-Awady)", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": "Tension and compression together.",
  "applied": {"status": "not_yet", "step": 6, "note": null},
  "history": [
    {"value": "no test-type rule: tension and compression both within scope", "from": "2026-10-04", "to": "2026-10-05", "note": "Reference script (docs/reference/worked_example.py)."}
  ],
  "notes": ["This removes MPEA_dataset.csv:row:139 (a compression test) from the primary analysis, so the reference numbers (77 / 98 records, k = 427 and 428) must be recomputed before step 7."]
},
{
  "key": "tamu_grouping_unit",
  "name": "Texas A&M grouping unit",
  "state": "in_force",
  "statement": "The Texas A&M dataset is one group (the dataset) for grouped standard errors. Its six batches are kept as reported.",
  "value": {"text": "one group: the dataset", "unit": null},
  "category": "statistical",
  "affects": "The number of independent groups: Texas A&M alone fails validity check 2 (one group), and it adds one group to the pooled test.",
  "reason": "The dataset has no per-record paper; whether its batches are independent enough to be separate groups is not established.",
  "evidence": ["PRD 5.7 (uncertainty row) and PRD 17, decision 9."],
  "decided": {"by": "owner (Khalid El-Awady)", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": "Six batches as six groups.",
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.versions:SOURCES.tamu_fcc.grouping_unit", "equals": "dataset"}
  ], "note": "The adapter refuses any other grouping unit. The sensitivity analysis comes in step 7."},
  "history": [
    {"value": "one group (recommended)", "from": "2026-10-04", "to": "2026-10-05", "note": "PRD 17, decision 9."}
  ],
  "notes": []
},
{
  "key": "same_alloy_rule",
  "name": "When two compositions are the same alloy",
  "state": "in_force",
  "statement": "Round each element's atomic percent to the nearest 0.1. Two compositions are the same alloy when their rounded compositions are identical: the same elements with the same rounded values. Computed on the full-precision composition, never on the display label.",
  "value": {"text": "rounding step 0.1", "unit": "at.%"},
  "category": "scientific",
  "affects": "The alloy intercepts of the model, the count of alloys with two or more grain sizes, and duplicate matching.",
  "reason": "This is the rule that produced the reference numbers (98 records, 22 alloys). It is transitive by construction, so there is no chain case.",
  "evidence": ["docs/reference/worked_example.py, norm(): round(100*v/s, 1).", "Step 4 summary, review finding 2."],
  "decided": {"by": "owner (Khalid El-Awady)", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": "The same rule with a rounding step of 1 at.%.",
  "applied": {"status": "not_yet", "step": 6, "note": "The adapters give the full-precision composition; the display label (normalize.alloy_label) is not this rule."},
  "history": [
    {"value": "0.1 at.% rounding, the current default pending approval", "from": "2026-10-05", "to": "2026-10-05", "note": "Step 4, review finding 2."}
  ],
  "notes": [
    "Known weakness: compositions closer than the step can fall into different bins at a boundary.",
    "Ties follow the reference script's rounding (Python round on the computed percentage) unless step 6 states otherwise.",
    "Possible improvement for step 6, not a decision: a tolerance-based grouping, which would need a stated rule for chains and the owner's approval."
  ]
},
{
  "key": "fixed_minimums",
  "name": "Fixed minimums for data sufficiency",
  "state": "in_force",
  "statement": "Under the default sufficiency option, a test needs at least 30 records, 5 alloys measured at two or more grain sizes, 10 independent papers and 10 residual degrees of freedom. All four must be met.",
  "value": {"text": "30 records; 5 alloys; 10 papers; 10 residual degrees of freedom", "unit": null},
  "category": "statistical",
  "affects": "Whether the outcome can be 'sufficient' under the fixed-minimum option; never the two validity checks.",
  "reason": "Simple counts are used until a power calculation is written down and reviewed (PRD 5.8).",
  "evidence": ["PRD 5.8; PRD 17, decision 1."],
  "decided": {"by": "owner (Khalid El-Awady)", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 6, "note": "Step 6 makes these the plan's default values; step 7 applies the check. The database already stores each plan's minimums and checks that 'minimums met' agrees with them."},
  "history": [
    {"value": "the same values, as starting values to be confirmed", "from": "2026-10-04", "to": "2026-10-05", "note": "PRD 5.8."}
  ],
  "notes": []
},
{
  "key": "values_disagree_tolerance",
  "name": "When values disagree",
  "state": "in_force",
  "statement": "Two values that should be the same measurement raise a conflict flag when their relative difference |a - b| / min(|a|, |b|) is above 2%. Applies to yield strength and grain size.",
  "value": {"text": "2% relative difference, relative to the smaller value", "unit": "%"},
  "category": "data_handling",
  "affects": "Conflict flags on records; flags never change the stored values.",
  "reason": "A strict symmetric tolerance makes transcription differences visible.",
  "evidence": ["PRD 5.3; PRD 17, decision 4."],
  "decided": {"by": "owner (Khalid El-Awady)", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 6, "note": null},
  "history": [
    {"value": "15% for yield strength at matched alloy and grain size (recommended)", "from": "2026-10-04", "to": "2026-10-05", "note": "PRD 17, decision 4."}
  ],
  "notes": ["Open point for step 6, to be settled with the owner's approval: which records are compared. Two records from the same paper with the same alloy, grain size and conditions in one source may be repeat specimens, which are separate measurements. A conflict is two records that claim to be the same measurement and disagree, which mainly arises between different sources reporting the same paper. The pairing is not final."]
},
{
  "key": "calibration_noise_levels",
  "name": "Calibration assumptions",
  "state": "in_force",
  "statement": "The scatter per record and the shift per paper used in the calibration simulation are estimated by code from the frozen dataset's residuals after the dataset freeze. The estimation method is fixed at the rules lock and applied by code; no person or agent chooses the values. The smallest effect that matters is a query setting.",
  "value": {"text": "scatter and per-paper shift estimated from the frozen residuals; smallest effect default 150", "unit": "MPa·µm^0.5"},
  "category": "statistical",
  "affects": "The calibration shares shown with the report (a flag, never a gate).",
  "reason": "Noise levels taken from the data's own structure describe the test's behaviour on data like this run's, instead of illustrative values.",
  "evidence": ["PRD 5.10; PRD 17, decision 10."],
  "decided": {"by": "owner (Khalid El-Awady)", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [
    {"value": "scatter 60 MPa, shift between groups 40 MPa, smallest effect 150 (illustrative), from the domain profile, fixed at the rules lock", "from": "2026-10-04", "to": "2026-10-05", "note": "PRD 5.10 and 17, decision 10."}
  ],
  "notes": [
    "Conflicts with PRD 5.10, which says these assumptions are fixed at the rules lock and never estimated from the real outcomes.",
    "This is a safeguard change: it needs a second-model review in step 7 before it is applied.",
    "Alternative to compare in that review: report calibration both ways, with data-derived noise levels and with the fixed defaults."
  ]
},
{
  "key": "tag_starting_lists",
  "name": "Starting lists of tag values",
  "state": "in_force",
  "statement": "Property: yield strength, ultimate tensile strength, hardness, elongation, fatigue life. Alloy class: multi-principal-element (high-entropy) alloy, steel, aluminium alloy, titanium alloy, nickel alloy, copper alloy, magnesium alloy, other. Test condition: room-temperature tension, room-temperature compression, elevated temperature, cryogenic, hardness test, fatigue.",
  "value": {"text": "5 property values; 8 alloy classes; 6 test conditions", "unit": null},
  "category": "data_handling",
  "affects": "The tags each run carries, and filtering and reporting by topic.",
  "reason": "Fixed lists keep the same thing named the same way; the Planner may propose a new value, which a person approves.",
  "evidence": ["PRD 5.5; PRD 17, decision 7."],
  "decided": {"by": "owner (Khalid El-Awady)", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 6, "note": null},
  "history": [
    {"value": "alloy class: FCC, BCC, FCC and BCC, other; test condition: room temperature, cryogenic, elevated; tension, compression, hardness (recommended)", "from": "2026-10-04", "to": "2026-10-05", "note": "PRD 17, decision 7."}
  ],
  "notes": []
},
{
  "key": "tamu_microstructure",
  "name": "Texas A&M microstructure",
  "state": "in_force",
  "statement": "The Texas A&M records are treated as single-phase FCC. The value is 'assigned by decision': the source does not state it explicitly as a result.",
  "value": {
    "text": "single-phase FCC (assigned by decision)",
    "unit": null
  },
  "category": "scientific",
  "affects": "Whether the 94 Texas A&M records fall inside a single-phase FCC scope; with them, the pooled reference result (PRD 14.1a).",
  "reason": "The authors describe their measured compositions as single-phase FCC, the alloys were selected under an FCC phase-stability constraint, and their phase constitution was checked by X-ray diffraction.",
  "evidence": [
    "ArroyaveLab/2026-mulukutla-hall-petch@11390ee5 paper/main.tex line 138: \"The 81 compositions measured here carry all three, under one processing route and one characterization protocol. This is the largest such set reported for single-phase FCC multi-principal element alloys, and it lets composition, processing and grain size be separated without correcting across studies.\"",
    "paper/main.tex line 173: \"It explored composition under an FCC phase stability constraint while holding processing fixed.\" (BB campaign); paper/supplementary.tex line 61: \"It explored the Al--Co--Cr--Cu--Fe--Mn--Ni--V system under an FCC phase-stability constraint while holding processing fixed.\"",
    "paper/main.tex line 175: \"Candidate alloys were iteratively selected from an FCC-constrained, manufacturable design space with the models updated after each iteration using the newly acquired data.\" (CB campaign)",
    "paper/main.tex line 177: \"Energy-dispersive X-ray spectroscopy (EDS) and X-ray diffraction were used to check realized chemistry and phase constitution, while electron microscopy and EBSD documented the microstructure.\"; paper/supplementary.tex line 65: \"EDS and XRD checked realized chemistry and phase constitution; SEM and EBSD documented the microstructure;\"",
    "Step 4b summary, 'Texas A&M phase constitution'."
  ],
  "decided": {
    "by": "owner (Khalid El-Awady)",
    "date": "2026-10-05"
  },
  "expert_review": {
    "status": "not_reviewed",
    "name": null,
    "date": null
  },
  "sensitivity": "The source-only analysis (reported values and values assigned from source only) shows the result without these records.",
  "applied": {
    "status": "not_yet",
    "step": 6,
    "note": "Today the adapter reports the microstructure as not reported and assigns phase class FCC from source."
  },
  "history": [
    {
      "value": "not reported: the source does not state the phases present per record (open decision)",
      "from": "2026-10-05",
      "to": "2026-10-05",
      "note": "Step 4 adapter; open decision in the first step 4b register."
    }
  ],
  "notes": [
    "The paper says 81 compositions; the spreadsheet has 82 distinct compositions.",
    "No passage states the result of the XRD phase check.",
    "Not reviewed by an expert.",
    "Uses the status 'assigned by decision' (see entry 'assigned_value_statuses')."
  ]
},
{
  "key": "shared_coefficient",
  "name": "One grain-size coefficient for all alloys",
  "state": "in_force",
  "statement": "All alloys share one grain-size coefficient k; only the baseline differs between alloys.",
  "value": {"text": "one shared k", "unit": null},
  "category": "scientific",
  "affects": "The tested quantity and the verdict.",
  "reason": "The claim under test is about grain-size strengthening across the alloys in scope, and one coefficient is what the supported model estimates.",
  "evidence": ["PRD 5.7 (formula row); docs/reference/worked_example.py."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": "Per-source estimates.",
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": ["The two sources' separate estimates differ: about 427 (MPEA) and about 1173 (Texas A&M)."]
},
{
  "key": "exponent_fixed",
  "name": "Exponent fixed at -1/2",
  "state": "in_force",
  "statement": "Yield strength depends on grain size through (grain size)^-1/2. The exponent is fixed, not fitted.",
  "value": {"text": "-1/2", "unit": null},
  "category": "scientific",
  "affects": "The predictor of the model and the meaning of k.",
  "reason": "The Hall-Petch relation as usually stated.",
  "evidence": ["PRD 5.7 (formula row)."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "model_form",
  "name": "The supported model",
  "state": "in_force",
  "statement": "Yield strength = a baseline for each alloy + k x (grain size in µm)^-1/2. This is the one supported model in sprint 1.",
  "value": {"text": "YS = baseline per alloy + k x d^-1/2, d in µm", "unit": "MPa"},
  "category": "scientific",
  "affects": "Every test, the verdict and the calibration.",
  "reason": "Sprint 1 supports one model so that the safeguards can be built and checked around it.",
  "evidence": ["PRD 5.7; CLAUDE.md, rule 6."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "baseline_per_alloy",
  "name": "One baseline per alloy",
  "state": "in_force",
  "statement": "Each alloy has one baseline strength. Differences in processing, texture and laboratory are not modelled, beyond grouping the errors by paper.",
  "value": {"text": "one intercept per alloy", "unit": null},
  "category": "scientific",
  "affects": "The estimate of k when processing or laboratory differ between grain sizes of the same alloy.",
  "reason": "The supported model has alloy intercepts only.",
  "evidence": ["PRD 5.7; docs/reference/worked_example.py (YS ~ x + C(comp))."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "grain_size_as_reported",
  "name": "Grain size used as reported",
  "state": "in_force",
  "statement": "Grain size is used as each source reports it, with no correction for how it was measured (for example linear intercept or equivalent circle diameter) or for whether twin boundaries were counted.",
  "value": {"text": "as reported, in µm", "unit": "µm"},
  "category": "scientific",
  "affects": "The predictor; differences in measurement method between papers enter the scatter or the estimate of k.",
  "reason": "The sources do not report the measurement method per record in a form code can harmonize.",
  "evidence": ["PRD 10; Texas A&M paper/main.tex line 177 (equivalent circle mean from EBSD)."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.record:HARMONIZED_FIELDS.grain_size", "equals": "µm"}
  ], "note": "The adapters convert the reported number unchanged."},
  "history": [],
  "notes": []
},
{
  "key": "mean_grain_size_only",
  "name": "Mean grain size only",
  "state": "in_force",
  "statement": "Only the mean grain size enters the model; the width of the grain-size distribution is not used.",
  "value": {"text": "mean only", "unit": null},
  "category": "scientific",
  "affects": "The predictor; any effect of the distribution width is left in the scatter.",
  "reason": "The supported model has one predictor. The Texas A&M source itself studies the distribution width as a separate predictor.",
  "evidence": ["Texas A&M paper/main.tex line 177 (mean d and SD_grain); PRD 5.7."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": "The adapters keep the reported grain-size SD where a source has one."},
  "history": [],
  "notes": ["Added in step 4b while writing the entries the owner listed."]
},
{
  "key": "yield_strength_as_reported",
  "name": "Yield strength used as reported",
  "state": "in_force",
  "statement": "Yield strength is used as each source reports it and treated as comparable across papers (for example the definition of yield, specimen geometry and strain rate are not harmonized).",
  "value": {"text": "as reported, in MPa", "unit": "MPa"},
  "category": "scientific",
  "affects": "The outcome variable; differences in definition between papers enter the scatter or the baselines.",
  "reason": "The sources do not report these details per record in a form code can harmonize.",
  "evidence": ["PRD 10; Texas A&M paper/main.tex line 177 (0.2% offset)."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.record:HARMONIZED_FIELDS.yield_strength", "equals": "MPa"}
  ], "note": "The adapters convert the reported number unchanged."},
  "history": [],
  "notes": []
},
{
  "key": "quasistatic_tests",
  "name": "Tests assumed quasistatic",
  "state": "in_force",
  "statement": "Tests are assumed to be quasistatic. Loading rate is not filtered.",
  "value": {"text": "quasistatic; no loading-rate rule", "unit": null},
  "category": "scientific",
  "affects": "Which records are pooled; a high-rate test would be pooled with quasistatic ones.",
  "reason": "Neither source has a loading-rate field.",
  "evidence": ["PRD 5.2 (exclusion menu has no rate rule); the MPEA and Texas A&M column lists."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 6, "note": "No code applies a rate rule; step 6 states the scope."},
  "history": [],
  "notes": []
},
{
  "key": "composition_as_reported",
  "name": "Composition used as reported",
  "state": "in_force",
  "statement": "An alloy's composition is the one its source reports. Nominal (target) and measured compositions are not distinguished.",
  "value": {"text": "as reported, in at.%", "unit": "at.%"},
  "category": "scientific",
  "affects": "Which records count as the same alloy.",
  "reason": "The MPEA dataset gives formula strings; the sources do not say per record whether a composition is nominal or measured.",
  "evidence": ["Texas A&M paper/main.tex line 182 (figure caption: measured and target composition); PRD 10."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.record:HARMONIZED_FIELDS.composition", "equals": "at.%"}
  ], "note": null},
  "history": [],
  "notes": ["Added in step 4b while writing the entries the owner listed."]
},
{
  "key": "room_temperature_scope",
  "name": "Room temperature",
  "state": "in_force",
  "statement": "A room-temperature scope accepts reported test temperatures from 20 to 25 °C.",
  "value": {"text": "20 to 25", "unit": "°C"},
  "category": "scientific",
  "affects": "Which records are in scope for a room-temperature claim.",
  "reason": "The reference script's scope.",
  "evidence": ["docs/reference/worked_example.py: d['T'].between(20, 25)."],
  "decided": {"by": "reference script and PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 6, "note": "Used on the test side only (tests/test_reference_counts_from_adapters.py)."},
  "history": [],
  "notes": ["How a record with an assigned room-temperature band (decision 'tamu_test_temperature') passes this scope is defined in step 6."]
},
{
  "key": "fcc_microstructure_scope",
  "name": "Single-phase FCC scope",
  "state": "in_force",
  "statement": "The reference plan's scope is single-phase FCC: in the MPEA dataset, microstructure exactly 'FCC'.",
  "value": {"text": "microstructure FCC", "unit": null},
  "category": "scientific",
  "affects": "Which records are in scope for the reference claim.",
  "reason": "The reference script's scope.",
  "evidence": ["docs/reference/worked_example.py: d.micro == 'FCC'."],
  "decided": {"by": "reference script and PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 6, "note": "Used on the test side only."},
  "history": [],
  "notes": ["The Texas A&M records meet it by decision (entry 'tamu_microstructure')."]
},
{
  "key": "mpea_microstructure_label_trusted",
  "name": "MPEA microstructure label trusted",
  "state": "in_force",
  "statement": "The MPEA dataset's microstructure label ('FCC', 'FCC+Sec.' and so on) is taken as the phase constitution, without checking the original papers.",
  "value": {"text": "as compiled", "unit": null},
  "category": "data_handling",
  "affects": "Which MPEA records are in a single-phase FCC scope.",
  "reason": "The compilation is the source; reading the original papers is a later sprint.",
  "evidence": ["PRD 10; PRD 18 (reading papers is backlog)."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.record:HARMONIZED_FIELDS.microstructure"}
  ], "note": "The MPEA adapter keeps the label verbatim."},
  "history": [],
  "notes": ["Added in step 4b while writing the entries the owner listed."]
},
{
  "key": "grain_size_floor",
  "name": "Grain-size floor",
  "state": "in_force",
  "statement": "Records with a grain size below 0.1 µm are excluded by a plan rule, fixed before any outcome is seen.",
  "value": {"text": "exclude below 0.1", "unit": "µm"},
  "category": "scientific",
  "affects": "Which records enter the primary analysis of the reference plan.",
  "reason": "Below about 0.1 µm the Hall-Petch relation is not expected to hold.",
  "evidence": ["PRD 5.2 (example rule); docs/reference/worked_example.py: s.gs >= 0.1."],
  "decided": {"by": "reference script and PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": "No exclusions (the reference script's sensitivity analysis).",
  "applied": {"status": "not_yet", "step": 6, "note": "Used on the test side only."},
  "history": [],
  "notes": []
},
{
  "key": "alloy_eligibility",
  "name": "Alloys with two or more grain sizes",
  "state": "in_force",
  "statement": "Only alloys measured at two or more distinct grain sizes within the plan's scope enter a test. Others are kept and marked not eligible.",
  "value": {"text": "at least 2 distinct grain sizes", "unit": null},
  "category": "scientific",
  "affects": "Which records enter the primary analysis.",
  "reason": "An alloy with one grain size has its own baseline and says nothing about k.",
  "evidence": ["PRD 5.7 ('Which alloys can be used'); CLAUDE.md, rule 6."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 6, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "physical_validity_checks",
  "name": "Physical validity checks",
  "state": "in_force",
  "statement": "A physically impossible value (for example tensile strength below yield strength, or a negative grain size) is flagged and kept out of the analysis. Agreement with the grain-size relationship under test is never used to judge a record.",
  "value": {"text": "UTS < YS or grain size < 0: invalid", "unit": null},
  "category": "scientific",
  "affects": "Which records are flagged invalid.",
  "reason": "Physical checks must not involve the relationship under test.",
  "evidence": ["PRD 5.3."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 6, "note": "The adapters convert such values unchanged; they do not judge them."},
  "history": [],
  "notes": []
},
{
  "key": "tamu_test_type",
  "name": "Texas A&M test type",
  "state": "in_force",
  "statement": "The Texas A&M yield strengths are from tensile tests, assigned from source.",
  "value": {"text": "tension (assigned from source)", "unit": null},
  "category": "scientific",
  "affects": "Whether the Texas A&M records pass a tension-only rule.",
  "reason": "The paper states it explicitly.",
  "evidence": ["paper/main.tex line 177: \"Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation tests provided the HV.\"", "paper/supplementary.tex line 65."],
  "decided": {"by": "owner (Khalid El-Awady), on the step 4 rule for assigned values", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.adapters.tamu_fcc:TEST_TYPE_CITATION"}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "tamu_phase_class",
  "name": "Texas A&M phase class",
  "state": "in_force",
  "statement": "The Texas A&M records are FCC, assigned from source. This is the phase class, not 'single-phase'.",
  "value": {"text": "FCC (assigned from source)", "unit": null},
  "category": "scientific",
  "affects": "The alloy-class description of the Texas A&M records.",
  "reason": "The paper states it explicitly.",
  "evidence": ["paper/main.tex line 173: \"The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system.\""],
  "decided": {"by": "owner (Khalid El-Awady), on the step 4 rule for assigned values", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.adapters.tamu_fcc:PHASE_CITATION"}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "tamu_composition_unit",
  "name": "Texas A&M composition unit",
  "state": "in_force",
  "statement": "The Texas A&M element columns are atomic percent. The column headers state no unit; the paper does.",
  "value": {"text": "at.%", "unit": "at.%"},
  "category": "data_handling",
  "affects": "The composition of every Texas A&M record.",
  "reason": "The paper states it explicitly, and the Al column's range (0 to 4) matches.",
  "evidence": ["paper/main.tex line 399: \"Al is not included in the 15\\% statement because it spans only 0--4~at.\\% and has a much wider interval.\""],
  "decided": {"by": "owner (Khalid El-Awady), on the step 4 rule for assigned values", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.adapters.tamu_fcc:COMPOSITION_UNIT_CITATION"}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "ols_alloy_intercepts",
  "name": "Fitting",
  "state": "in_force",
  "statement": "The model is fitted by ordinary least squares with one intercept per alloy.",
  "value": {"text": "ordinary least squares", "unit": null},
  "category": "statistical",
  "affects": "The estimate of k.",
  "reason": "The supported model (PRD 5.7).",
  "evidence": ["PRD 5.7 (fitting row); CLAUDE.md, rule 6."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "cluster_robust_se",
  "name": "Grouped standard error",
  "state": "in_force",
  "statement": "The standard error of k is cluster-robust, with records grouped by each source's grouping unit (the paper for literature data), with the small-sample correction.",
  "value": {"text": "cluster-robust by grouping unit, with small-sample correction", "unit": null},
  "category": "statistical",
  "affects": "The uncertainty, the p-value and the verdict.",
  "reason": "Records from one paper share conditions, so they are not independent.",
  "evidence": ["PRD 5.7 (uncertainty row); docs/reference/worked_example.py (statsmodels cov_type='cluster')."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": ["The reference numbers used statsmodels' default cluster correction; step 7 states the exact formula."]
},
{
  "key": "papers_independent",
  "name": "Papers are independent groups",
  "state": "in_force",
  "statement": "Each paper is an independent group, including papers from the same laboratory.",
  "value": {"text": "one group per paper", "unit": null},
  "category": "statistical",
  "affects": "The number of groups, the uncertainty and the degrees of freedom of the test.",
  "reason": "Papers are the grouping unit of the supported model; links between laboratories are not recorded.",
  "evidence": ["PRD 5.7 (uncertainty row)."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.versions:SOURCES.mpea.grouping_unit", "equals": "paper"}
  ], "note": "The grouping itself is used in step 7."},
  "history": [],
  "notes": []
},
{
  "key": "one_sided_test",
  "name": "The test",
  "state": "in_force",
  "statement": "Null hypothesis k <= 0, alternative k > 0. One-sided test at a threshold of 0.05 unless the plan sets another, against a t distribution with (number of groups - 1) degrees of freedom.",
  "value": {"text": "one-sided; threshold 0.05; t with groups - 1 degrees of freedom", "unit": null},
  "category": "statistical",
  "affects": "The p-value and the verdict.",
  "reason": "The claim is that grain refinement strengthens, a one-directional claim. The t reference with groups - 1 degrees of freedom suits few groups.",
  "evidence": ["PRD 5.7 (hypotheses row); CLAUDE.md, rule 6."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "p_threshold_comparison",
  "name": "p-value against the threshold",
  "state": "in_force",
  "statement": "The claim is supported when the one-sided p-value is strictly below the threshold.",
  "value": {"text": "p < 0.05", "unit": null},
  "category": "statistical",
  "affects": "The verdict when the p-value equals the threshold.",
  "reason": "The usual convention.",
  "evidence": ["Step 3 summary, 'Step 7 acceptance requirements', item 2."],
  "decided": {"by": "owner (Khalid El-Awady)", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "validity_checks",
  "name": "The two validity checks",
  "state": "in_force",
  "statement": "Check 1: at least one alloy measured at two distinct grain sizes, or nothing is fitted. Check 2: at least 1 residual degree of freedom and at least 2 independent groups, or the coefficient is reported alone with no uncertainty, no p-value and no verdict. Neither can be waived.",
  "value": {"text": "check 1: 1 alloy at 2 grain sizes; check 2: 1 residual df and 2 groups", "unit": null},
  "category": "statistical",
  "affects": "Whether a coefficient, an uncertainty and a verdict exist, for the pooled test, each source and each sensitivity analysis.",
  "reason": "Below these floors no coefficient, or no uncertainty, can be computed.",
  "evidence": ["PRD 5.7; CLAUDE.md, rule 5."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": "The database already checks necessary conditions on stored counts (ck_analysis_result_check1_consistent, ck_analysis_result_check2_consistent)."},
  "history": [],
  "notes": []
},
{
  "key": "sufficiency_options",
  "name": "Sufficiency options and 'exploratory'",
  "state": "in_force",
  "statement": "Two options: fixed minimum (the default) and use what is available. A result is 'exploratory' exactly when the query uses what is available and the fixed minimums are not met. Neither option waives the validity checks.",
  "value": {"text": "default: fixed minimum", "unit": null},
  "category": "statistical",
  "affects": "Whether a test runs on little data, and its label.",
  "reason": "PRD 5.8; step 3 decision on 'exploratory'.",
  "evidence": ["PRD 5.8; CLAUDE.md, rule 7; step 3 summary, PRD correction 5."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "sql:ck_plan_sufficiency_option"},
    {"ref": "sql:ck_run_exploratory_needs_verdict"},
    {"ref": "sql:hc_run_update"}
  ], "note": "The database enforces the two options and the 'exploratory' rule. The default option is set by the plan model in step 6."},
  "history": [],
  "notes": []
},
{
  "key": "power_information_only",
  "name": "Estimated power is information only",
  "state": "in_force",
  "statement": "Estimated power may be shown, labelled 'estimated power under the stated assumptions'. It never decides whether a test runs in sprint 1.",
  "value": {"text": "information only", "unit": null},
  "category": "statistical",
  "affects": "Nothing in the decision; only what is shown.",
  "reason": "The power calculation needs assumptions that have not been written down and reviewed.",
  "evidence": ["PRD 5.8; step 3 summary, decision 8 and PRD correction 13."],
  "decided": {"by": "owner (Khalid El-Awady), step 3", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "sql:ck_plan_sufficiency_option"}
  ], "note": "A power-based option cannot be stored."},
  "history": [],
  "notes": []
},
{
  "key": "pooled_gives_verdict",
  "name": "The pooled test gives the verdict",
  "state": "in_force",
  "statement": "The pooled test over all searched sources gives the verdict. Per-source results and sensitivity analyses are descriptive and never change it.",
  "value": {"text": "pooled", "unit": null},
  "category": "statistical",
  "affects": "Which result is the verdict.",
  "reason": "Stated in the plan before any outcome is seen.",
  "evidence": ["PRD 5.1, 5.2 and 5.7."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "calibration_simulation",
  "name": "Calibration simulation settings",
  "state": "in_force",
  "statement": "2,000 simulations in each of two worlds (no effect; smallest effect that matters), each share with an exact binomial 95% interval, deterministic for a stored seed. A flag, never a gate.",
  "value": {"text": "2,000 per world; 95% exact binomial interval", "unit": null},
  "category": "statistical",
  "affects": "The calibration shown with the report.",
  "reason": "PRD 5.10.",
  "evidence": ["PRD 5.10; CLAUDE.md, rule 11."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "normal_errors_in_calibration",
  "name": "Normal errors in the calibration",
  "state": "in_force",
  "statement": "The calibration simulation draws the per-record scatter and the per-paper shift from normal distributions.",
  "value": {"text": "normal", "unit": null},
  "category": "statistical",
  "affects": "The calibration shares; heavier-tailed real errors would make them optimistic.",
  "reason": "The simplest assumption; the reference calibration script uses it.",
  "evidence": ["docs/reference/calibration_example.py."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "reference_test_tolerance",
  "name": "Reference-test tolerance",
  "state": "in_force",
  "statement": "The fixed-plan reference test passes when k and its uncertainty are within ±1 of the reference values.",
  "value": {"text": "±1 on k and on its uncertainty", "unit": "MPa·µm^0.5"},
  "category": "statistical",
  "affects": "Whether the statistics code passes its software-correctness test.",
  "reason": "PRD 5.7 ('Reference test').",
  "evidence": ["PRD 5.7."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 7, "note": null},
  "history": [],
  "notes": ["The reference values are recomputed before step 7 (decision 'permitted_test_types')."]
},
{
  "key": "paper_grouping_by_doi",
  "name": "Paper identity from the DOI",
  "state": "in_force",
  "statement": "A literature record's paper (its group) is identified by a key derived from its DOI: surrounding whitespace trimmed, one URL or 'doi:' wrapper removed, ASCII letters case-folded. The DOI as reported is kept. A blank DOI means the paper is unknown; no group is invented.",
  "value": {"text": "normalized DOI", "unit": null},
  "category": "data_handling",
  "affects": "Grouping for the standard error, the paper count and duplicate matching.",
  "reason": "Formatting differences must not split one paper.",
  "evidence": ["Step 4 summary, review finding 1."],
  "decided": {"by": "owner (Khalid El-Awady), step 4", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.normalize:doi_group_key"}
  ], "note": null},
  "history": [
    {"value": "the DOI text exactly as in the file", "from": "2026-10-05", "to": "2026-10-05", "note": "First step 4 draft, before review finding 1."}
  ],
  "notes": []
},
{
  "key": "curated_values_trusted",
  "name": "Curated databases trusted as transcribed",
  "state": "in_force",
  "statement": "Values in curated source databases (the MPEA compilation) are trusted as transcribed from the original papers.",
  "value": {"text": "trusted as transcribed", "unit": null},
  "category": "data_handling",
  "affects": "Every MPEA value; a transcription error would enter the analysis.",
  "reason": "Reading the original papers is a later sprint.",
  "evidence": ["PRD 10; PRD 18 (reading papers)."],
  "decided": {"by": "implicit in PRD v1.6 and the reference script", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.adapters.mpea_layout:read"}
  ], "note": "The adapter converts the values unchanged."},
  "history": [],
  "notes": []
},
{
  "key": "duplicate_identity",
  "name": "When two records are the same measurement",
  "state": "in_force",
  "statement": "Two records are duplicates only if they come from the same original paper and match on alloy, grain size, value and test conditions. Matching alloy and grain size alone is not enough.",
  "value": {"text": "same paper, alloy, grain size, value and conditions", "unit": null},
  "category": "data_handling",
  "affects": "Which records are counted once.",
  "reason": "One measurement must not be counted twice, and distinct measurements must not be merged.",
  "evidence": ["PRD 5.3."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 6, "note": "Alloy under the rule 'same_alloy_rule'; paper under 'paper_grouping_by_doi'."},
  "history": [],
  "notes": []
},
{
  "key": "duplicate_survivor_rule",
  "name": "Which duplicate is kept in the primary analysis",
  "state": "in_force",
  "statement": "1) Prefer the record that comes directly from the original paper, detected by the original paper's DOI on the record. 2) If both or neither do, take the first source in the fixed order MPEA, Texas A&M, controlled extract. 3) Within one source, take the lowest row number.",
  "value": {"text": "original paper; then source order; then lowest row", "unit": null},
  "category": "data_handling",
  "affects": "Which copy of a duplicate enters the primary analysis; both stay in the store.",
  "reason": "A fixed rule, not a choice made after seeing values.",
  "evidence": ["PRD 5.3; step 1 summary, 'Survivor rule'."],
  "decided": {"by": "owner (Khalid El-Awady), step 1", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 6, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "unresolved_duplicates",
  "name": "Possible duplicates that cannot be resolved",
  "state": "in_force",
  "statement": "A possible duplicate that cannot be resolved is kept, counted once in the primary analysis by the survivor rule, and counted separately in a sensitivity analysis.",
  "value": {"text": "counted once", "unit": null},
  "category": "data_handling",
  "affects": "The primary record set and one sensitivity analysis.",
  "reason": "So that one measurement is not counted twice.",
  "evidence": ["PRD 5.3."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": "Both counted separately.",
  "applied": {"status": "not_yet", "step": 6, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "scope_not_confirmed",
  "name": "Scope not confirmed",
  "state": "in_force",
  "statement": "A record whose scope cannot be confirmed because metadata are missing is kept, left out of the primary analysis, and included in a sensitivity analysis.",
  "value": {"text": "out of primary; in sensitivity", "unit": null},
  "category": "data_handling",
  "affects": "The primary record set and one sensitivity analysis.",
  "reason": "A missing value is not evidence that the record is in scope.",
  "evidence": ["PRD 5.3."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": "Included.",
  "applied": {"status": "not_yet", "step": 6, "note": null},
  "history": [],
  "notes": []
},
{
  "key": "assigned_value_statuses",
  "name": "Values not in the data file",
  "state": "in_force",
  "statement": "A value not in the data file is set only with one of two statuses, each citing its basis: 'assigned from source' (an explicit statement in the source's documentation, quoted with file and line) or 'assigned by decision' (a recorded owner or expert decision). The two stay distinguishable wherever they are stored or shown. Otherwise the value is not reported.",
  "value": {"text": "assigned from source; assigned by decision", "unit": null},
  "category": "data_handling",
  "affects": "Every assigned value, and the source-only sensitivity analysis.",
  "reason": "The tool's credibility rests on code deciding from exactly what sources say, with every other basis visible.",
  "evidence": ["Step 4 summary, question 3."],
  "decided": {"by": "owner (Khalid El-Awady)", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": "The reference plan names a sensitivity analysis that accepts only reported values and values assigned from source, so the effect of every decision-based assignment is visible.",
  "applied": {"status": "not_yet", "step": 6, "note": "Today the code has one status, 'assigned', which requires a citation (hypocurate.sources.record.Value) and is used only for statements in the source, that is 'assigned from source'."},
  "history": [
    {"value": "one status 'assigned', only on an explicit quoted statement in the source", "from": "2026-10-05", "to": "2026-10-05", "note": "Step 4."}
  ],
  "notes": []
},
{
  "key": "values_kept_as_reported",
  "name": "Values kept as reported",
  "state": "in_force",
  "statement": "Nothing is corrected silently. Every cell is kept as reported text. A value that cannot be converted is marked 'not convertible' with the reason; the record and its other fields are kept. Entirely blank rows are listed, not made into records.",
  "value": {"text": "converted, not reported, not convertible, assigned", "unit": null},
  "category": "data_handling",
  "affects": "Every record.",
  "reason": "Silent fixes would bias results.",
  "evidence": ["Step 4 summary, 'The common record format'."],
  "decided": {"by": "owner (Khalid El-Awady), step 4", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.record:STATUSES", "equals": ["converted", "not_reported", "not_convertible", "assigned"]}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "malformed_files_refused",
  "name": "Malformed files refused",
  "state": "in_force",
  "statement": "A file that cannot be parsed strictly (a quoting error or a row with the wrong number of fields) is refused as a whole, naming the file, the line and the reason. No partial extraction is returned.",
  "value": {"text": "whole file refused", "unit": null},
  "category": "data_handling",
  "affects": "Whether a source version can be read at all.",
  "reason": "A malformed row can silently absorb later records.",
  "evidence": ["Step 4 summary, review finding 3."],
  "decided": {"by": "owner (Khalid El-Awady), step 4", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.adapters.mpea_layout:read"},
    {"ref": "python:hypocurate.sources.record:AdapterError"}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "composition_normalization",
  "name": "Composition in atomic percent",
  "state": "in_force",
  "statement": "Formula strings and percentage columns are both converted to atomic percent at full precision. A missing amount in a formula means 1. Percentages that do not sum to 100 are marked, never rescaled; the sum is accepted within 1e-6 (floating-point representation only).",
  "value": {"text": "sum tolerance 1e-6", "unit": "at.%"},
  "category": "data_handling",
  "affects": "The composition of every record.",
  "reason": "One unit for both sources; no silent rescaling.",
  "evidence": ["PRD 10; step 4 summary, review finding 5 and re-check item 5."],
  "decided": {"by": "owner (Khalid El-Awady), step 4", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.normalize:PERCENT_SUM_TOLERANCE", "equals": 1e-6},
    {"ref": "python:hypocurate.sources.normalize:formula_to_atomic_percent"}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "alloy_label_display_only",
  "name": "Alloy label for display only",
  "state": "in_force",
  "statement": "Each record carries a short alloy label (elements in alphabetical order, each rounded to 0.1 at.%). It is for display only; equal labels do not mean the same alloy.",
  "value": {"text": "display only", "unit": null},
  "category": "data_handling",
  "affects": "What is shown; never identity.",
  "reason": "Rounded labels are not scientific identity (step 4 review, finding 2).",
  "evidence": ["Step 4 summary, review finding 2."],
  "decided": {"by": "owner (Khalid El-Awady), step 4", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.normalize:alloy_label"}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "grain_size_transformation_at_analysis",
  "name": "Grain-size transformation at analysis",
  "state": "in_force",
  "statement": "Adapters give grain size in µm only. The transformation the locked plan names (grain size^-1/2) is applied by code when the analysis dataset is built.",
  "value": {"text": "µm in records; d^-1/2 at analysis", "unit": "µm"},
  "category": "data_handling",
  "affects": "Where the predictor is computed.",
  "reason": "No plan exists when records are read.",
  "evidence": ["Step 4 summary, question 2."],
  "decided": {"by": "owner (Khalid El-Awady), step 4", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 6, "note": "The µm part is applied (HARMONIZED_FIELDS); the transformation comes with the analysis dataset."},
  "history": [],
  "notes": []
},
{
  "key": "controlled_extract_disabled",
  "name": "Controlled extract off by default",
  "state": "in_force",
  "statement": "The controlled duplicate extract (constructed test data) is registered as a source that is switched off. It must never enter a real analysis.",
  "value": {"text": "enabled = false", "unit": null},
  "category": "data_handling",
  "affects": "Whether constructed data can reach a real analysis.",
  "reason": "It is test data built from the MPEA dataset.",
  "evidence": ["Step 4 summary, PRD correction 8 and open item 5."],
  "decided": {"by": "owner (Khalid El-Awady), step 4", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.versions:SOURCES.controlled_duplicates.enabled", "equals": false}
  ], "note": "A guard against choosing it is step 6's."},
  "history": [],
  "notes": []
},
{
  "key": "stored_file_limits",
  "name": "Stored files",
  "state": "in_force",
  "statement": "Files stored in the database are at most 5 MiB each. Source files must be CSV or XLSX with a safe relative path.",
  "value": {"text": "5 MiB per file; .csv or .xlsx", "unit": "bytes"},
  "category": "operational",
  "affects": "Which source files can be registered (the 49 MB Zenodo archive cannot).",
  "reason": "Files live in the database in sprint 1, which has a 1 GB disk.",
  "evidence": ["PRD 6 and 17, decision 5; step 3 summary, decision 10."],
  "decided": {"by": "owner (Khalid El-Awady), step 3", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.sources.versions:MAX_FILE_BYTES", "equals": 5242880},
    {"ref": "python:hypocurate.sources.versions:SAFE_STORED_PATH"},
    {"ref": "sql:ck_source_file_max_size"},
    {"ref": "sql:ck_source_file_safe_data_file_path"}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "login_throttle",
  "name": "Failed-login count",
  "state": "in_force",
  "statement": "After 5 wrong passwords within 15 minutes, further wrong attempts receive 429 instead of 401 until the oldest counted failure leaves the window. Every attempt is still checked; a correct password is never refused by the count.",
  "value": {"text": "5 wrong attempts in 15 minutes", "unit": null},
  "category": "operational",
  "affects": "Responses to wrong passwords.",
  "reason": "A lockout would let anyone keep the owner out (step 2 review, finding 2).",
  "evidence": ["Step 2 summary, finding 2."],
  "decided": {"by": "owner (Khalid El-Awady), step 2", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.web.login_throttle:MAX_FAILURES", "equals": 5},
    {"ref": "python:hypocurate.web.login_throttle:WINDOW_SECONDS", "equals": 900}
  ], "note": null},
  "history": [
    {"value": "a global lockout after failed attempts", "from": "2026-10-04", "to": "2026-10-04", "note": "First step 2 draft, before review finding 2."}
  ],
  "notes": []
},
{
  "key": "session_length",
  "name": "Session length",
  "state": "in_force",
  "statement": "A login lasts 12 hours (signed session cookie). Rotating SESSION_SECRET ends every session.",
  "value": {"text": "12", "unit": "hours"},
  "category": "operational",
  "affects": "How long a browser stays signed in.",
  "reason": "One working day; there is no session table in sprint 1.",
  "evidence": ["Step 2 summary."],
  "decided": {"by": "owner (Khalid El-Awady), step 2", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.web.app:SESSION_MAX_AGE", "equals": 43200}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "secret_lengths",
  "name": "Password and secret lengths",
  "state": "in_force",
  "statement": "The login password must be at least 24 characters in production and 12 in development; the session secret at least 32. The configuration enforces the length, not the randomness.",
  "value": {"text": "24 / 12 / 32", "unit": "characters"},
  "category": "operational",
  "affects": "Whether the web service starts.",
  "reason": "Protection against guessing is a random password of at least 24 characters.",
  "evidence": ["Step 2 summary, finding 2."],
  "decided": {"by": "owner (Khalid El-Awady), step 2", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.config:MIN_PRODUCTION_PASSWORD_LENGTH", "equals": 24},
    {"ref": "python:hypocurate.config:MIN_PASSWORD_LENGTH", "equals": 12},
    {"ref": "python:hypocurate.config:MIN_SESSION_SECRET_LENGTH", "equals": 32}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "single_web_process",
  "name": "One web process",
  "state": "in_force",
  "statement": "The web service runs one process, so the failed-login count is shared; a restart clears it.",
  "value": {"text": "1", "unit": "process"},
  "category": "operational",
  "affects": "The failed-login count.",
  "reason": "The count is kept in memory.",
  "evidence": ["Step 2 summary."],
  "decided": {"by": "owner (Khalid El-Awady), step 2", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "file:Dockerfile:--workers 1"}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "transaction_retries",
  "name": "Transaction retries",
  "state": "in_force",
  "statement": "A database transaction that fails with a deadlock (40P01) or a serialization failure (40001) is rerun as a whole, at most 5 attempts in all. Other errors are not retried.",
  "value": {"text": "5", "unit": "attempts"},
  "category": "operational",
  "affects": "Write paths under contention.",
  "reason": "PostgreSQL may abort one of two concurrent transactions; the caller must retry.",
  "evidence": ["Step 3 summary, 'The locking protocol'; step 4 summary."],
  "decided": {"by": "step 4 (owner's approval of the plan)", "date": "2026-10-05"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.db.retry:run_transaction(attempts)", "equals": 5},
    {"ref": "python:hypocurate.db.retry:RETRYABLE_SQLSTATES", "equals": ["40001", "40P01"]}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "worker_poll_interval",
  "name": "Worker idle interval",
  "state": "in_force",
  "statement": "The idle worker checks the database and sleeps 60 seconds between checks.",
  "value": {"text": "60", "unit": "seconds"},
  "category": "operational",
  "affects": "Worker logs only; it runs nothing yet.",
  "reason": "The queue comes in step 9.",
  "evidence": ["Step 2 summary."],
  "decided": {"by": "owner (Khalid El-Awady), step 2", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "yes", "settings": [
    {"ref": "python:hypocurate.worker:IDLE_SECONDS", "equals": 60}
  ], "note": null},
  "history": [],
  "notes": []
},
{
  "key": "spending_caps",
  "name": "Spending caps",
  "state": "in_force",
  "statement": "Model calls may cost at most $2 per run and $50 per calendar month (UTC), counting calls without a reported cost at their upper bound.",
  "value": {"text": "$2 per run; $50 per month", "unit": "USD"},
  "category": "operational",
  "affects": "Whether a run or a model call may proceed.",
  "reason": "CLAUDE.md, rule 12.",
  "evidence": ["CLAUDE.md, rule 12; step 3 summary, 'Step 9 requirements'."],
  "decided": {"by": "PRD v1.6 (owner)", "date": "2026-10-04"},
  "expert_review": {"status": "not_reviewed", "name": null, "date": null},
  "sensitivity": null,
  "applied": {"status": "not_yet", "step": 9, "note": null},
  "history": [],
  "notes": []
}
]
```

## 5. Code

### `hypocurate/assumptions.py`

```python
"""The assumptions register (step 4b): one source file, `hypocurate/assumptions.json`.

One entry per assumption: what is assumed, its value, why, who decided it and when, the
expert review, the sensitivity analysis that covers it, whether code applies it yet, and
its earlier values. The /assumptions page is generated from it and nothing else.

Rules (CLAUDE.md, "How we work"): a new assumption or a changed default is entered here in
the same merge; code reads a default from one named place, and an entry that code applies
names that place in `applied.settings`. Each setting reference has one of these forms:

- `python:<module>:<name>[.<attribute or key>…]` — a module attribute, walked by attribute
  or mapping key;
- `python:<module>:<function>(<parameter>)` — the default of a function's parameter;
- `sql:<name>` — a constraint, function or message in the migrations;
- `file:<repository path>:<text>` — a fixed text in a repository file (for example the
  Dockerfile's process count).

An optional `equals` gives the value the code must hold. `resolve_setting` is used by the
tests (`tests/test_assumptions.py`), not by the page.
"""
from __future__ import annotations

import importlib
import inspect
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parent
REGISTER_PATH = PACKAGE / "assumptions.json"
REPO_ROOT = PACKAGE.parent
MIGRATIONS = PACKAGE / "db" / "migrations" / "versions"

# Display order and labels.
CATEGORIES = {"scientific": "Scientific", "statistical": "Statistical",
              "data_handling": "Data handling", "operational": "Operational"}
REVIEW_STATUSES = {"not_reviewed": "Not reviewed", "accepted": "Reviewed and accepted", "disputed": "Disputed"}
STATES = ("in_force", "open")
BUILD_STEPS = range(5, 13)  # PRD 15, steps still to come

FIELDS = {"key", "name", "state", "statement", "value", "category", "affects", "reason", "evidence",
          "decided", "expert_review", "sensitivity", "applied", "history", "notes"}
OPEN_ONLY_FIELDS = {"pending"}
KEY = re.compile(r"[a-z][a-z0-9_]*")


class RegisterError(ValueError):
    """The register does not follow its schema. The message names the entry and the field."""


class SettingNotFound(LookupError):
    """A setting reference names nothing that exists in the code."""


def load_register(path: Path = REGISTER_PATH) -> list[dict]:
    """Read and validate the register. Raises RegisterError on any schema problem."""
    entries = json.loads(path.read_text(encoding="utf-8"))
    validate(entries)
    return entries


# --- Schema -------------------------------------------------------------------------

def _text(where: str, value: Any, *, optional: bool = False) -> None:
    if value is None and optional:
        return
    if not isinstance(value, str) or not value.strip():
        raise RegisterError(f"{where}: must be non-empty text")


def _date(where: str, value: Any) -> date:
    if not isinstance(value, str):
        raise RegisterError(f"{where}: must be a date YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise RegisterError(f"{where}: must be a date YYYY-MM-DD") from None
    if parsed.isoformat() != value:
        raise RegisterError(f"{where}: must be a date YYYY-MM-DD")
    return parsed


def _keys(where: str, obj: Any, required: set[str], optional: frozenset[str] = frozenset()) -> None:
    if not isinstance(obj, dict):
        raise RegisterError(f"{where}: must be an object")
    missing, extra = required - obj.keys(), obj.keys() - required - optional
    if missing:
        raise RegisterError(f"{where}: missing {sorted(missing)}")
    if extra:
        raise RegisterError(f"{where}: unknown {sorted(extra)}")


def validate(entries: Any) -> None:
    if not isinstance(entries, list) or not entries:
        raise RegisterError("the register must be a non-empty list")
    seen: set[str] = set()
    for i, e in enumerate(entries):
        where = f"entry {i}"
        if isinstance(e, dict) and isinstance(e.get("key"), str):
            where = f"entry {e['key']!r}"
        _validate_entry(where, e)
        if e["key"] in seen:
            raise RegisterError(f"{where}: duplicate key")
        seen.add(e["key"])


def _validate_entry(where: str, e: Any) -> None:
    is_open = isinstance(e, dict) and e.get("state") == "open"
    _keys(where, e, FIELDS | (OPEN_ONLY_FIELDS if is_open else set()))
    if not isinstance(e["key"], str) or not KEY.fullmatch(e["key"]):
        raise RegisterError(f"{where}.key: lower-case letters, digits and _ only")
    for f in ("name", "statement", "affects", "reason"):
        _text(f"{where}.{f}", e[f])
    if e["state"] not in STATES:
        raise RegisterError(f"{where}.state: one of {list(STATES)}")
    if e["category"] not in CATEGORIES:
        raise RegisterError(f"{where}.category: one of {list(CATEGORIES)}")
    if not isinstance(e["evidence"], list) or not e["evidence"]:
        raise RegisterError(f"{where}.evidence: a non-empty list")
    for j, ev in enumerate(e["evidence"]):
        _text(f"{where}.evidence[{j}]", ev)
    _text(f"{where}.sensitivity", e["sensitivity"], optional=True)
    if not isinstance(e["notes"], list):
        raise RegisterError(f"{where}.notes: a list")
    for j, note in enumerate(e["notes"]):
        _text(f"{where}.notes[{j}]", note)

    decided_on = None
    if is_open:
        # An open decision has no value in force and no decision yet; it says who decides, by when.
        if e["value"] is not None or e["decided"] is not None:
            raise RegisterError(f"{where}: an open decision has value null and decided null")
        _keys(f"{where}.pending", e["pending"], {"by", "before_step"})
        _text(f"{where}.pending.by", e["pending"]["by"])
        if e["pending"]["before_step"] not in BUILD_STEPS:
            raise RegisterError(f"{where}.pending.before_step: a build step from 5 to 12")
    else:
        _keys(f"{where}.value", e["value"], {"text", "unit"})
        _text(f"{where}.value.text", e["value"]["text"])
        _text(f"{where}.value.unit", e["value"]["unit"], optional=True)
        _keys(f"{where}.decided", e["decided"], {"by", "date"})
        _text(f"{where}.decided.by", e["decided"]["by"])
        decided_on = _date(f"{where}.decided.date", e["decided"]["date"])

    review = e["expert_review"]
    _keys(f"{where}.expert_review", review, {"status", "name", "date"})
    if review["status"] not in REVIEW_STATUSES:
        raise RegisterError(f"{where}.expert_review.status: one of {list(REVIEW_STATUSES)}")
    if review["status"] == "not_reviewed":
        if review["name"] is not None or review["date"] is not None:
            raise RegisterError(f"{where}.expert_review: not reviewed has no name or date")
    else:
        _text(f"{where}.expert_review.name", review["name"])
        _date(f"{where}.expert_review.date", review["date"])

    _validate_applied(f"{where}.applied", e["applied"])

    if not isinstance(e["history"], list):
        raise RegisterError(f"{where}.history: a list")
    previous_to = None
    for j, h in enumerate(e["history"]):
        hw = f"{where}.history[{j}]"
        _keys(hw, h, {"value", "from", "to", "note"})
        _text(f"{hw}.value", h["value"])
        _text(f"{hw}.note", h["note"], optional=True)
        start, end = _date(f"{hw}.from", h["from"]), _date(f"{hw}.to", h["to"])
        if start > end:
            raise RegisterError(f"{hw}: 'from' is after 'to'")
        if previous_to is not None and start < previous_to:
            raise RegisterError(f"{hw}: earlier values must be in date order")
        if decided_on is not None and end > decided_on:
            raise RegisterError(f"{hw}: ends after the current value was decided")
        previous_to = end


def _validate_applied(where: str, applied: Any) -> None:
    if not isinstance(applied, dict) or applied.get("status") not in ("yes", "not_yet"):
        raise RegisterError(f"{where}.status: 'yes' or 'not_yet'")
    if applied["status"] == "yes":
        _keys(where, applied, {"status", "settings", "note"})
        if not isinstance(applied["settings"], list) or not applied["settings"]:
            raise RegisterError(f"{where}.settings: applied in code needs at least one named setting")
        for j, s in enumerate(applied["settings"]):
            _keys(f"{where}.settings[{j}]", s, {"ref"}, frozenset({"equals"}))
            _text(f"{where}.settings[{j}].ref", s["ref"])
    else:
        _keys(where, applied, {"status", "step", "note"})
        if applied["step"] not in BUILD_STEPS:
            raise RegisterError(f"{where}.step: a build step from 5 to 12")
    _text(f"{where}.note", applied["note"], optional=True)


# --- Settings in code ----------------------------------------------------------------

_PYTHON = re.compile(r"python:([A-Za-z_][\w.]*):([A-Za-z_]\w*(?:\.\w+)*)(?:\((\w+)\))?")


def _plain(value: Any) -> Any:
    """A code value in the register's JSON terms: sets sorted, tuples as lists."""
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(v) for v in value)
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def resolve_setting(ref: str) -> Any:
    """The value a setting reference names in the code. Raises SettingNotFound if it names
    nothing. For `sql:` and `file:` references the value is the matched text."""
    if ref.startswith("python:"):
        m = _PYTHON.fullmatch(ref)
        if not m:
            raise SettingNotFound(f"{ref}: not a python:<module>:<name> reference")
        module_name, path, parameter = m.groups()
        try:
            obj: Any = importlib.import_module(module_name)
        except ImportError as error:
            raise SettingNotFound(f"{ref}: module not found ({error})") from None
        for part in path.split("."):
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                try:
                    obj = obj[part]
                except (KeyError, TypeError, IndexError):
                    raise SettingNotFound(f"{ref}: {part!r} not found") from None
        if parameter is None:
            return _plain(obj)
        try:
            param = inspect.signature(obj).parameters[parameter]
        except (KeyError, TypeError, ValueError):
            raise SettingNotFound(f"{ref}: no parameter {parameter!r}") from None
        if param.default is inspect.Parameter.empty:
            raise SettingNotFound(f"{ref}: parameter {parameter!r} has no default")
        return _plain(param.default)
    if ref.startswith("sql:"):
        name = ref[len("sql:"):]
        pattern = re.compile(rf"(?<![\w]){re.escape(name)}(?![\w])")
        for migration in sorted(MIGRATIONS.glob("*.py")):
            if pattern.search(migration.read_text(encoding="utf-8")):
                return name
        raise SettingNotFound(f"{ref}: not found in the migrations")
    if ref.startswith("file:"):
        relative, sep, needle = ref[len("file:"):].partition(":")
        target = (REPO_ROOT / relative).resolve()
        if not sep or not needle or not target.is_relative_to(REPO_ROOT) or not target.is_file():
            raise SettingNotFound(f"{ref}: not a file:<path>:<text> reference to a repository file")
        if needle not in target.read_text(encoding="utf-8"):
            raise SettingNotFound(f"{ref}: text not found")
        return needle
    raise SettingNotFound(f"{ref}: unknown kind of reference")


def check_settings(entry: dict) -> list[str]:
    """Problems with an applied entry's named settings: each must resolve, and each value
    given with `equals` must equal the code's. Empty when all is well."""
    problems = []
    for s in entry["applied"].get("settings", []):
        try:
            actual = resolve_setting(s["ref"])
        except SettingNotFound as error:
            problems.append(f"{entry['key']}: {error}")
            continue
        if "equals" in s and actual != s["equals"]:
            problems.append(f"{entry['key']}: {s['ref']} is {actual!r} in the code, the register says {s['equals']!r}")
    return problems


# --- The page ------------------------------------------------------------------------

def page_sections(entries: list[dict], *, not_reviewed_only: bool = False) -> list[tuple[str, list[dict]]]:
    """Sections for the page: open decisions first, then the entries in force by category."""
    shown = [e for e in entries if not not_reviewed_only or e["expert_review"]["status"] == "not_reviewed"]
    sections = [("Open decisions", [e for e in shown if e["state"] == "open"])]
    sections += [(label, [e for e in shown if e["state"] == "in_force" and e["category"] == c])
                 for c, label in CATEGORIES.items()]
    return [(label, group) for label, group in sections if group]


def summary_counts(entries: list[dict]) -> dict[str, int]:
    return {
        "total": len(entries),
        "open": sum(e["state"] == "open" for e in entries),
        "scientific_not_reviewed": sum(e["category"] == "scientific"
                                       and e["expert_review"]["status"] == "not_reviewed" for e in entries),
    }
```

### `hypocurate/web/app.py`

```python
"""The web service (PRD Section 6): login, health page, a placeholder home page, and the
read-only assumptions register (step 4b, /assumptions).

Every page needs the shared login except exactly /login and /health, and the
files under /static/. The session is a signed cookie (Starlette
SessionMiddleware, itsdangerous) holding only {"signed_in": true}; in
production it is sent over HTTPS only. There is no server-side session record:
rotating SESSION_SECRET ends every session (README, "Sessions").
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import Engine
from starlette.middleware.sessions import SessionMiddleware

from hypocurate import assumptions
from hypocurate.config import Settings, load_settings
from hypocurate.db.engine import database_reachable, make_engine
from hypocurate.db.migrate import schema_status
from hypocurate.web.login_throttle import Attempt, LoginThrottle

HERE = Path(__file__).resolve().parent
SESSION_COOKIE = "hypocurate_session"
SESSION_MAX_AGE = 12 * 60 * 60
PUBLIC_PATHS = frozenset({"/login", "/health"})  # exact matches only
STATIC_PREFIX = "/static/"

templates = Jinja2Templates(directory=HERE / "templates")


def create_app(
    settings: Settings | None = None,
    engine: Engine | None = None,
    login_throttle: LoginThrottle | None = None,
    register: list[dict] | None = None,
) -> FastAPI:
    settings = settings or load_settings()
    engine = engine or make_engine(settings.database_url)
    throttle = login_throttle or LoginThrottle()
    # Read and validated once at start: an invalid register stops the service starting.
    if register is None:
        register = assumptions.load_register()
    else:
        assumptions.validate(register)

    app = FastAPI(title="HypoCurate", docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def require_login(request: Request, call_next):
        path = request.url.path
        public = path in PUBLIC_PATHS or path.startswith(STATIC_PREFIX)
        if not public and not request.session.get("signed_in"):
            return RedirectResponse("/login", status_code=303)
        return await call_next(request)

    # Added after require_login so that it runs first and the session is available.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie=SESSION_COOKIE,
        max_age=SESSION_MAX_AGE,
        same_site="lax",
        https_only=settings.production,
    )
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return templates.TemplateResponse(request, "home.html", {})

    @app.get("/login", response_class=HTMLResponse)
    def login_form(request: Request):
        return templates.TemplateResponse(request, "login.html", {"error": None})

    @app.post("/login")
    def login(request: Request, password: str = Form("")) -> Response:
        result = throttle.attempt(password, settings.password)
        if result is Attempt.OK:
            request.session.clear()
            request.session["signed_in"] = True
            return RedirectResponse("/", status_code=303)
        if result is Attempt.THROTTLED:
            return templates.TemplateResponse(
                request, "login.html",
                {"error": "Too many failed attempts. Try again in a few minutes."},
                status_code=429,
            )
        return templates.TemplateResponse(
            request, "login.html", {"error": "Wrong password."}, status_code=401
        )

    @app.post("/logout")
    def logout(request: Request) -> Response:
        request.session.clear()
        return RedirectResponse("/login", status_code=303)

    @app.get("/assumptions", response_class=HTMLResponse)
    def assumptions_page(request: Request, review: str | None = None):
        """Read-only: generated from hypocurate/assumptions.json; nothing is edited here."""
        not_reviewed_only = review == "not_reviewed"
        return templates.TemplateResponse(request, "assumptions.html", {
            "sections": assumptions.page_sections(register, not_reviewed_only=not_reviewed_only),
            "counts": assumptions.summary_counts(register),
            "not_reviewed_only": not_reviewed_only,
            "categories": assumptions.CATEGORIES,
            "review_labels": assumptions.REVIEW_STATUSES,
        })

    @app.get("/health")
    def health(request: Request) -> Response:
        db_ok = database_reachable(engine)
        status = {"web": "ok", "database": "ok" if db_ok else "unreachable", "version": settings.version,
                  # Informational (step 3): confirms a deploy migrated; never changes the status code.
                  "schema": schema_status(engine) if db_ok else {"revision": None, "at_head": False}}
        code = 200 if db_ok else 503
        if "text/html" in request.headers.get("accept", ""):
            return templates.TemplateResponse(request, "health.html", {"status": status}, status_code=code)
        return JSONResponse(status, status_code=code)

    return app
```

### `hypocurate/web/templates/assumptions.html`

```html
{% extends "base.html" %}
{% block title %}Assumptions · HypoCurate{% endblock %}
{% block main_attrs %} class="wide"{% endblock %}
{% block nav %}<nav class="nav"><a href="/">Home</a><form method="post" action="/logout" class="logout"><button type="submit">Sign out</button></form></nav>{% endblock %}
{% block content %}

<h1>Assumptions</h1>
<p class="summary" id="summary">
  {{ counts.total }} entries ·
  <strong>{{ counts.open }} open decision{{ "" if counts.open == 1 else "s" }}</strong> ·
  <strong>{{ counts.scientific_not_reviewed }} scientific assumption{{ "" if counts.scientific_not_reviewed == 1 else "s" }} not reviewed by an expert</strong>
</p>
<p class="muted">Read-only. Generated from <code>hypocurate/assumptions.json</code>; changes are made there, in a reviewed merge.</p>
<p class="filter">
  {% if not_reviewed_only %}Showing: not reviewed by an expert. <a href="/assumptions">Show all</a>
  {% else %}Showing: all. <a href="/assumptions?review=not_reviewed">Show only: not reviewed by an expert</a>{% endif %}
</p>

{% for label, entries in sections %}
<h2>{{ label }}</h2>
<table class="register">
  <thead><tr><th>Assumption</th><th>Value</th><th>What it affects</th><th>Expert review</th><th>Applied in code</th></tr></thead>
  {% for e in entries %}
  {% set unreviewed_scientific = e.category == "scientific" and e.expert_review.status == "not_reviewed" %}
  <tbody id="{{ e.key }}" class="entry{% if unreviewed_scientific %} unreviewed-scientific{% endif %}{% if e.state == 'open' %} open{% endif %}">
    <tr>
      <td>
        <strong>{{ e.name }}</strong>
        {% if e.state == "open" %}<span class="badge open-badge">Open decision</span>{% endif %}
        {% if unreviewed_scientific %}<span class="badge unreviewed">Not reviewed by an expert</span>{% endif %}
        <div>{{ e.statement }}</div>
        {% if e.state == "open" %}<div class="muted">{{ categories[e.category] }}</div>{% endif %}
      </td>
      <td>{% if e.value %}{{ e.value.text }}{% if e.value.unit and e.value.unit not in e.value.text %} {{ e.value.unit }}{% endif %}
          {% else %}Not decided ({{ e.pending.by }}, before step {{ e.pending.before_step }}){% endif %}</td>
      <td>{{ e.affects }}</td>
      <td>{{ review_labels[e.expert_review.status] }}{% if e.expert_review.name %}: {{ e.expert_review.name }}, {{ e.expert_review.date }}{% endif %}</td>
      <td>{% if e.applied.status == "yes" %}Yes{% else %}Not yet: step {{ e.applied.step }}{% endif %}</td>
    </tr>
    <tr class="more">
      <td colspan="5">
        <details>
          <summary>Reason, evidence, history and sensitivity analysis</summary>
          <dl>
            <dt>Reason</dt><dd>{{ e.reason }}</dd>
            <dt>Evidence</dt><dd><ul>{% for ev in e.evidence %}<li>{{ ev }}</li>{% endfor %}</ul></dd>
            <dt>Decided</dt><dd>{% if e.decided %}{{ e.decided.by }}, {{ e.decided.date }}{% else %}Not yet decided{% endif %}</dd>
            <dt>Sensitivity analysis</dt><dd>{{ e.sensitivity or "None" }}</dd>
            <dt>Applied in code</dt><dd>
              {% if e.applied.status == "yes" %}Yes: {% for s in e.applied.settings %}<code>{{ s.ref }}</code>{% if not loop.last %}, {% endif %}{% endfor %}.
              {% else %}Not yet: step {{ e.applied.step }}.{% endif %}
              {% if e.applied.note %} {{ e.applied.note }}{% endif %}</dd>
            <dt>Earlier values</dt><dd>{% if e.history %}<ul>{% for h in e.history %}<li>{{ h.from }} to {{ h.to }}: {{ h.value }}{% if h.note %} ({{ h.note }}){% endif %}</li>{% endfor %}</ul>{% else %}None{% endif %}</dd>
            {% if e.notes %}<dt>Notes</dt><dd><ul>{% for n in e.notes %}<li>{{ n }}</li>{% endfor %}</ul></dd>{% endif %}
            <dt>Key</dt><dd><code>{{ e.key }}</code></dd>
          </dl>
        </details>
      </td>
    </tr>
  </tbody>
  {% endfor %}
</table>
{% endfor %}

{% endblock %}
```

### `hypocurate/web/templates/base.html`

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}HypoCurate{% endblock %}</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header><span class="brand">HypoCurate</span>{% block nav %}{% endblock %}</header>
  <main{% block main_attrs %}{% endblock %}>{% block content %}{% endblock %}</main>
</body>
</html>
```

### `hypocurate/web/templates/home.html`

```html
{% extends "base.html" %}
{% block nav %}<form method="post" action="/logout" class="logout"><button type="submit">Sign out</button></form>{% endblock %}
{% block content %}
<h1>Signed in</h1>
<p>The skeleton is running. The screens arrive in build step 10.</p>
<p><a href="/assumptions">Assumptions</a> · <a href="/health">Health</a></p>
{% endblock %}
```

### `hypocurate/web/static/style.css`

```css
:root { --fg: #1d2330; --muted: #5b6475; --bg: #ffffff; --line: #d8dde6; --accent: #2457c5; --bad: #b3261e; --good: #1f7a3a; }
* { box-sizing: border-box; }
body { margin: 0; font: 16px/1.5 system-ui, sans-serif; color: var(--fg); background: var(--bg); }
header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid var(--line); }
.brand { font-weight: 600; }
main { max-width: 32rem; margin: 2rem auto; padding: 0 16px; }
label { display: block; margin-bottom: 4px; }
input { width: 100%; padding: 8px; border: 1px solid var(--line); border-radius: 4px; font: inherit; }
button { margin-top: 12px; padding: 8px 16px; border: 0; border-radius: 4px; background: var(--accent); color: #fff; font: inherit; cursor: pointer; }
.logout button { margin: 0; }
.error { color: var(--bad); }
.ok { color: var(--good); }
th { text-align: left; padding-right: 16px; color: var(--muted); font-weight: 500; }
/* Assumptions register (step 4b): plain table; full styling comes with the step 10 screens. */
main.wide { max-width: 72rem; }
.nav { display: flex; align-items: center; gap: 16px; }
.muted { color: var(--muted); }
a { color: var(--accent); }
code { font-size: 0.9em; overflow-wrap: anywhere; }
.register { width: 100%; border-collapse: collapse; margin-bottom: 2rem; }
.register th, .register td { text-align: left; vertical-align: top; padding: 8px 12px 8px 0; }
.register thead th { border-bottom: 2px solid var(--line); }
.register tbody { border-bottom: 1px solid var(--line); }
.register tr.more td { padding-top: 0; }
.register .unreviewed-scientific td:first-child { border-left: 4px solid var(--bad); padding-left: 8px; }
.badge { display: inline-block; margin-left: 6px; padding: 0 6px; border-radius: 4px; font-size: 0.85em; }
.badge.unreviewed { background: #fdecea; color: var(--bad); }
.badge.open-badge { background: #fff4e5; color: #8a4b00; }
details summary { cursor: pointer; color: var(--muted); }
dl { margin: 8px 0; } dt { font-weight: 600; margin-top: 6px; } dd { margin-left: 0; }
dd ul { margin: 0; padding-left: 1.2em; }
@media (max-width: 48rem) { .register thead { display: none; } .register td { display: block; padding-right: 0; } }
```

### `scripts/check_runtime_image.py`

```python
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
```

## 6. Tests

### `tests/test_assumptions.py`

```python
"""Step 4b: the assumptions register (`hypocurate/assumptions.json`) and its read-only page.

- Every entry follows the schema; the validator refuses each kind of malformed entry.
- The owner's eight decisions of 2026-10-05 are present as decided.
- **Every entry marked "applied: yes" names at least one setting that exists in the code,
  and where the register gives a value, the code holds that value** (CLAUDE.md, "How we
  work", item 12). A setting renamed or changed in code without the register fails here.
- GET /assumptions needs the login, is generated from the register, and offers no editing.
"""
import copy
import json
import re

import pytest
from markupsafe import escape
from fastapi.testclient import TestClient

from hypocurate import assumptions as a
from hypocurate.db.engine import make_engine
from hypocurate.web.app import create_app
from test_login import PASSWORD, settings

REGISTER = a.load_register()
BY_KEY = {e["key"]: e for e in REGISTER}
OWNER = "owner (Khalid El-Awady)"

# The owner's eight decisions of 2026-10-05 (step 4b instructions, a to h).
OWNER_DECISIONS = {
    "tamu_test_temperature": ("scientific", 6),
    "permitted_test_types": ("scientific", 6),
    "tamu_grouping_unit": ("statistical", None),  # already applied: the adapter's grouping unit
    "same_alloy_rule": ("scientific", 6),
    "fixed_minimums": ("statistical", 6),
    "values_disagree_tolerance": ("data_handling", 6),
    "calibration_noise_levels": ("statistical", 7),
    "tag_starting_lists": ("data_handling", 6),
}


# --- Schema ---------------------------------------------------------------------------

def test_the_register_file_follows_the_schema():
    raw = json.loads(a.REGISTER_PATH.read_text(encoding="utf-8"))
    a.validate(raw)
    assert len(raw) == len(BY_KEY) >= 50


def test_every_category_has_entries_and_keys_are_unique():
    assert {e["category"] for e in REGISTER} == set(a.CATEGORIES)
    assert len({e["key"] for e in REGISTER}) == len(REGISTER)


def test_the_owners_eight_decisions_are_recorded_as_decided():
    for key, (category, step) in OWNER_DECISIONS.items():
        e = BY_KEY[key]
        assert e["state"] == "in_force", key
        assert e["category"] == category, key
        assert e["decided"] == {"by": OWNER, "date": "2026-10-05"}, key
        assert e["expert_review"] == {"status": "not_reviewed", "name": None, "date": None}, key
        if step is None:
            assert e["applied"]["status"] == "yes", key
        else:
            assert e["applied"] == {**e["applied"], "status": "not_yet", "step": step}, key


def test_decisions_carry_the_owners_wording():
    assert "assigned by decision" in BY_KEY["tamu_test_temperature"]["value"]["text"]
    assert BY_KEY["permitted_test_types"]["sensitivity"] == "Tension and compression together."
    assert "row:139" in " ".join(BY_KEY["permitted_test_types"]["notes"])
    assert BY_KEY["tamu_grouping_unit"]["sensitivity"] == "Six batches as six groups."
    same_alloy = BY_KEY["same_alloy_rule"]
    assert "rounded compositions are identical" in same_alloy["statement"]
    assert "within" not in same_alloy["statement"]  # the owner's corrected wording
    assert "1 at.%" in same_alloy["sensitivity"]
    assert "min(|a|, |b|)" in BY_KEY["values_disagree_tolerance"]["statement"]
    assert "not final" in " ".join(BY_KEY["values_disagree_tolerance"]["notes"])
    calibration = BY_KEY["calibration_noise_levels"]
    assert "fixed at the rules lock and applied by code" in calibration["statement"]
    assert "no person or agent chooses the values" in calibration["statement"]
    notes = " ".join(calibration["notes"])
    assert "PRD 5.10" in notes and "second-model review in step 7" in notes and "both ways" in notes
    assert BY_KEY["p_threshold_comparison"]["value"]["text"] == "p < 0.05"


def test_the_microstructure_decision_is_recorded_and_no_decision_is_open():
    """Owner, 2026-10-05: the open decision 'tamu_microstructure' became a decision."""
    assert [e["key"] for e in REGISTER if e["state"] == "open"] == []
    e = BY_KEY["tamu_microstructure"]
    assert e["state"] == "in_force" and e["category"] == "scientific"
    assert e["value"]["text"] == "single-phase FCC (assigned by decision)"
    assert e["decided"] == {"by": OWNER, "date": "2026-10-05"}
    assert e["expert_review"] == {"status": "not_reviewed", "name": None, "date": None}
    assert e["applied"]["status"] == "not_yet" and e["applied"]["step"] == 6
    evidence = " ".join(e["evidence"])
    for cited in ("main.tex line 138", "main.tex line 173", "supplementary.tex line 61", "main.tex line 175",
                  "main.tex line 177", "supplementary.tex line 65"):
        assert cited in evidence, cited
    notes = " ".join(e["notes"])
    assert "81 compositions" in notes and "82" in notes
    assert "No passage states the result of the XRD phase check." in notes
    assert "Not reviewed by an expert." in notes
    assert "without these records" in e["sensitivity"]
    assert e["history"][0]["value"].endswith("(open decision)")


def open_entry():
    """An open decision built for the tests (the register has none since 2026-10-05)."""
    e = copy.deepcopy(BY_KEY["tamu_microstructure"])
    e.update(key="an_open_question", state="open", value=None, decided=None, history=[],
             pending={"by": "owner", "before_step": 6})
    return e


def test_an_open_decision_has_no_value_in_force():
    a.validate([open_entry()])
    for field, value in (("value", {"text": "x", "unit": None}), ("decided", {"by": "owner", "date": "2026-10-05"})):
        e = open_entry()
        e[field] = value
        with pytest.raises(a.RegisterError, match="open decision has value null"):
            a.validate([e])


def entry(**changes):
    e = copy.deepcopy(BY_KEY["session_length"])
    e.update(changes)
    return e


@pytest.mark.parametrize("bad, message", [
    (lambda e: e.pop("affects"), "missing"),
    (lambda e: e.update(extra=1), "unknown"),
    (lambda e: e.update(key="Bad Key"), "key"),
    (lambda e: e.update(category="physics"), "category"),
    (lambda e: e.update(state="draft"), "state"),
    (lambda e: e.update(statement="  "), "statement"),
    (lambda e: e.update(evidence=[]), "evidence"),
    (lambda e: e["decided"].update(date="5 Oct 2026"), "date"),
    (lambda e: e["decided"].update(date="2026-13-01"), "date"),
    (lambda e: e["expert_review"].update(status="approved"), "expert_review.status"),
    (lambda e: e["expert_review"].update(name="Prof. X"), "not reviewed has no name"),
    (lambda e: e.update(expert_review={"status": "accepted", "name": None, "date": None}), "expert_review.name"),
    (lambda e: e.update(expert_review={"status": "disputed", "name": "Prof. X", "date": None}), "expert_review.date"),
    (lambda e: e.update(applied={"status": "yes", "settings": [], "note": None}), "at least one named setting"),
    (lambda e: e.update(applied={"status": "yes", "note": None}), "missing"),
    (lambda e: e.update(applied={"status": "maybe", "note": None}), "applied.status"),
    (lambda e: e.update(applied={"status": "not_yet", "step": 4, "note": None}), "build step"),
    (lambda e: e.update(applied={"status": "not_yet", "step": 13, "note": None}), "build step"),
    (lambda e: e.update(history=[{"value": "x", "from": "2026-10-05", "to": "2026-10-04", "note": None}]), "after"),
    (lambda e: e.update(history=[{"value": "x", "from": "2026-10-01", "to": "2026-10-03", "note": None},
                                 {"value": "y", "from": "2026-10-02", "to": "2026-10-04", "note": None}]), "date order"),
    (lambda e: e.update(history=[{"value": "x", "from": "2026-10-01", "to": "2026-10-09", "note": None}]),
     "after the current value was decided"),
    (lambda e: e.update(value=None), "value"),
    (lambda e: e.update(state="open"), "missing ['pending']"),
    (lambda e: e.update(state="open", pending={"by": "owner", "before_step": 6}), "open decision has value null"),
    (lambda e: e.update(pending={"by": "owner", "before_step": 6}), "unknown"),
])
def test_the_validator_refuses_malformed_entries(bad, message):
    e = entry()
    bad(e)
    with pytest.raises(a.RegisterError, match=re.escape(message)):
        a.validate([e])


def test_the_validator_refuses_duplicate_keys_and_an_empty_register():
    with pytest.raises(a.RegisterError, match="duplicate key"):
        a.validate([entry(), entry()])
    with pytest.raises(a.RegisterError, match="non-empty list"):
        a.validate([])


def test_an_open_decision_needs_who_decides_and_by_when():
    e = open_entry()
    del e["pending"]
    with pytest.raises(a.RegisterError, match="missing"):
        a.validate([e])
    e["pending"] = {"by": "owner", "before_step": 3}
    with pytest.raises(a.RegisterError, match="build step"):
        a.validate([e])


# --- Applied in code: a named setting ---------------------------------------------------

def test_every_applied_entry_names_settings_that_exist_and_match():
    applied = [e for e in REGISTER if e["applied"]["status"] == "yes"]
    assert len(applied) >= 20
    problems = [p for e in applied for p in a.check_settings(e)]
    assert not problems, "\n".join(problems)


def test_applied_values_are_compared_where_the_register_gives_them():
    """Spot-check that `equals` is used for the numeric and categorical defaults."""
    compared = {s["ref"]: s["equals"] for e in REGISTER if e["applied"]["status"] == "yes"
                for s in e["applied"]["settings"] if "equals" in s}
    assert compared["python:hypocurate.web.login_throttle:MAX_FAILURES"] == 5
    assert compared["python:hypocurate.web.login_throttle:WINDOW_SECONDS"] == 900
    assert compared["python:hypocurate.web.app:SESSION_MAX_AGE"] == 12 * 60 * 60
    assert compared["python:hypocurate.sources.versions:MAX_FILE_BYTES"] == 5 * 1024 * 1024
    assert compared["python:hypocurate.sources.versions:SOURCES.tamu_fcc.grouping_unit"] == "dataset"
    assert compared["python:hypocurate.db.retry:run_transaction(attempts)"] == 5


@pytest.mark.parametrize("ref", [
    "python:hypocurate.web.login_throttle:NO_SUCH_SETTING",
    "python:hypocurate.no_such_module:X",
    "python:hypocurate.sources.versions:SOURCES.no_such_source.grouping_unit",
    "python:hypocurate.db.retry:run_transaction(no_such_parameter)",
    "python:hypocurate.db.retry:run_transaction(fn)",  # no default
    "sql:ck_no_such_constraint",
    "sql:ck_source_file_max",  # part of a name is not the name
    "file:Dockerfile:--workers 4",
    "file:../outside:anything",
    "file:no/such/file:x",
    "env:HYPOCURATE_ENV",
])
def test_a_reference_to_nothing_is_refused(ref):
    with pytest.raises(a.SettingNotFound):
        a.resolve_setting(ref)


def test_a_wrong_value_or_a_missing_setting_is_reported():
    e = copy.deepcopy(BY_KEY["login_throttle"])
    e["applied"]["settings"][0]["equals"] = 6
    assert a.check_settings(e) == [
        "login_throttle: python:hypocurate.web.login_throttle:MAX_FAILURES is 5 in the code, the register says 6"]
    e["applied"]["settings"][0]["ref"] = "python:hypocurate.web.login_throttle:MAX_FAILED"
    assert len(a.check_settings(e)) == 1 and "not found" in a.check_settings(e)[0]


def test_resolved_values_use_json_terms():
    assert a.resolve_setting("python:hypocurate.db.retry:RETRYABLE_SQLSTATES") == ["40001", "40P01"]
    assert a.resolve_setting("python:hypocurate.sources.record:STATUSES") == [
        "converted", "not_reported", "not_convertible", "assigned"]


# --- The page ----------------------------------------------------------------------------

def page_client(register=None):
    s = settings()
    app = create_app(s, engine=make_engine(s.database_url), register=register)
    return TestClient(app, base_url="http://testserver", follow_redirects=False)


def signed_in(register=None):
    c = page_client(register)
    assert c.post("/login", data={"password": PASSWORD}).status_code == 303
    return c


def test_the_page_needs_the_login():
    c = page_client()
    for path in ["/assumptions", "/assumptions?review=not_reviewed", "/assumptions/"]:
        r = c.get(path)
        assert r.status_code == 303 and r.headers["location"] == "/login", path


def test_the_page_shows_every_entry_grouped_by_category():
    html = signed_in().get("/assumptions").text
    headings = re.findall(r"<h2>([^<]+)</h2>", html)
    assert headings == ["Scientific", "Statistical", "Data handling", "Operational"]  # no open decision now
    for e in REGISTER:
        assert f'id="{e["key"]}"' in html, e["key"]
    sections = re.split(r"<h2>", html)[1:]
    for (label, group), section in zip(a.page_sections(REGISTER), sections):
        assert section.startswith(label)
        assert re.findall(r'<tbody id="([a-z0-9_]+)"', section) == [e["key"] for e in group]


def test_open_decisions_are_shown_first_when_there_are_any():
    register = REGISTER + [open_entry()]
    html = signed_in(register).get("/assumptions").text
    headings = re.findall(r"<h2>([^<]+)</h2>", html)
    assert headings == ["Open decisions", "Scientific", "Statistical", "Data handling", "Operational"]
    first = re.split(r"<h2>", html)[1]
    assert re.findall(r'<tbody id="([a-z0-9_]+)"', first) == ["an_open_question"]
    assert "Not decided (owner, before step 6)" in first and "Open decision</span>" in first
    assert "1 open decision</strong>" in html


def test_the_summary_line_counts_open_decisions_and_unreviewed_scientific_entries():
    html = signed_in().get("/assumptions").text
    summary = re.search(r'<p class="summary" id="summary">(.*?)</p>', html, re.S).group(1)
    n_open = sum(e["state"] == "open" for e in REGISTER)
    n_sci = sum(e["category"] == "scientific" and e["expert_review"]["status"] == "not_reviewed" for e in REGISTER)
    assert n_open == 0 and "0 open decisions" in summary
    assert f"{n_sci} scientific assumptions not reviewed by an expert" in summary
    assert html.index('id="summary"') < html.index("<h2>")


def reviewed(key, status):
    e = copy.deepcopy(BY_KEY[key])
    e["expert_review"] = {"status": status, "name": "Prof. Test Reviewer", "date": "2026-10-06"}
    return e


def test_unreviewed_scientific_entries_are_marked_and_reviewed_ones_are_not():
    register = [reviewed("exponent_fixed", "accepted")] + [e for e in REGISTER if e["key"] != "exponent_fixed"]
    html = signed_in(register).get("/assumptions").text
    bodies = dict(re.findall(r'<tbody id="([a-z0-9_]+)"(.*?)</tbody>', html, re.S))
    for e in register:
        marked = "Not reviewed by an expert</span>" in bodies[e["key"]]
        should = e["category"] == "scientific" and e["expert_review"]["status"] == "not_reviewed"
        assert marked == should, e["key"]
    assert "Reviewed and accepted: Prof. Test Reviewer, 2026-10-06" in bodies["exponent_fixed"]
    assert "unreviewed-scientific" not in html.split('id="exponent_fixed"')[0].rsplit("<tbody", 1)[1]


def test_the_filter_shows_only_entries_not_reviewed_by_an_expert():
    register = ([reviewed("exponent_fixed", "accepted"), reviewed("session_length", "disputed")]
                + [e for e in REGISTER if e["key"] not in ("exponent_fixed", "session_length")])
    c = signed_in(register)
    everything = c.get("/assumptions").text
    filtered = c.get("/assumptions?review=not_reviewed").text
    assert 'id="exponent_fixed"' in everything and 'id="session_length"' in everything
    shown = re.findall(r'<tbody id="([a-z0-9_]+)"', filtered)
    assert set(shown) == {e["key"] for e in register if e["expert_review"]["status"] == "not_reviewed"}
    assert 'href="/assumptions">Show all' in filtered


def test_each_row_expands_to_reason_evidence_history_and_sensitivity():
    html = signed_in().get("/assumptions").text
    body = re.search(r'<tbody id="values_disagree_tolerance"(.*?)</tbody>', html, re.S).group(1)
    e = BY_KEY["values_disagree_tolerance"]
    assert "<details>" in body
    for text in [e["reason"], e["evidence"][0], e["history"][0]["value"], e["notes"][0], "Sensitivity analysis"]:
        assert str(escape(text)) in body, text
    applied = re.search(r'<tbody id="session_length"(.*?)</tbody>', html, re.S).group(1)
    assert "<code>python:hypocurate.web.app:SESSION_MAX_AGE</code>" in applied
    assert "Not yet: step 7" in re.search(r'<tbody id="exponent_fixed"(.*?)</tbody>', html, re.S).group(1)


def test_the_page_is_read_only():
    c = signed_in()
    html = c.get("/assumptions").text
    assert re.findall(r"<form[^>]*>", html) == ['<form method="post" action="/logout" class="logout">']
    assert "<input" not in html and "<textarea" not in html and "<select" not in html
    for method in ("post", "put", "patch", "delete"):
        assert getattr(c, method)("/assumptions").status_code == 405, method


def test_the_service_does_not_start_with_an_invalid_register():
    bad = [entry(category="physics")]
    with pytest.raises(a.RegisterError):
        page_client(bad)


def test_the_home_page_links_to_the_register():
    assert 'href="/assumptions"' in signed_in().get("/").text
```

## 7. Suite output

```
$ pytest -q tests/test_assumptions.py -v   (Codespace; per-test lines)
============================== 58 passed in 1.00s ==============================
$ pytest -q   (whole suite)
527 passed in 61.29s (0:01:01)
```
