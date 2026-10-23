# HypoCurate — Sprint 1: what was built (summary for review)

Date: 2026-10-21. Repository: `kelawady/hypocurate`, branch `main` at merge `eb78ec0` (step 10b, live since 2026-10-12).
Owner: Khalid El-Awady. Built by Claude Code (Anthropic) with ChatGPT as the second-model reviewer.

## 0. What this document is for, and how to use it

This is the one place that describes everything Sprint 1 built, in enough detail that a reader with no access to the
earlier conversations can:

1. understand what the system does today, end to end;
2. compare it, section by section, with the Sprint 1 PRD (`docs/PRD_sprint1.md`, v1.6) and the proposal overview
   (`docs/HypoCurate_Combined_Overview_2026-10-04_v3.13.pdf`, draft v3.13);
3. prepare a detailed flow chart of how the code actually runs;
4. help the owner decide the next steps and the changes to make.

**Sources of truth, in order of authority.** The code and its tests decide. Then the assumptions register
(`hypocurate/assumptions.json`, 169 entries, also shown on the site at `/assumptions`), which records every default
and decision with its reason, who decided it and when, and its earlier values. Then the per-step summaries in
`docs/reviews/stepNN_summary.md`, and the second-model reviews saved verbatim beside them. This document summarises
those; where it and they disagree, they win. The step summaries also list, step by step, every "PRD correction or
clarification" agreed with the owner, collected in Section 10 below.

**A companion document**, `docs/sprint1/HypoCurate_Sprint1_Code_Flowchart.docx`, holds flow charts of the code as
built (drawn by Claude Code from the source). The diagram sources are in `docs/sprint1/flowchart_src/`. A reviewer
preparing a new flow chart can check it against both.

**What is asked of a reviewer (Claude or ChatGPT).**
- Check this summary against the PRD and the overview. Say where the build departs from them, whether each departure
  is recorded as a decision (Section 10), and whether any is unrecorded.
- Prepare a detailed flow chart that shows exactly how the current code operates (Section 16 lists what it should
  cover and where in the code each part lives).
- List the questions the owner should answer to plan the next sprint (Section 15 is a starting list).
- Do not trust this summary's claims about behaviour without checking the code they name; say which you checked.

---

## 1. Status at a glance

| Item | State |
|---|---|
| PRD Section 15 build steps | **Steps 1–10 merged and live** (with small inserted steps 4b, 7b and a fix branch). **Step 11** (deployment polish, the domain, the 14.7 demonstration) **not started. Step 12** (the optional Commentator) **not started.** |
| Live site | https://hypocurate-web.onrender.com (Render: web service, background worker, PostgreSQL 17). One shared password plus a name at sign-in. The `hypocurate.ai` domain is not yet attached. |
| Live database | Schema at migration **0009** (head). Sources `mpea` and `tamu_fcc` registered (2026-10-10). Three runs made by the owner from Render's shell (2026-10-10): run 1 fixed plan (reproduced the reference numbers), run 2 Planner (failed on a contract bug, since fixed), run 3 Planner, confirmed, completed sufficient/supported. |
| Regression suite | **2,422 tests**, all passing locally (42 min 51 s), in the test image (46 min 19 s) and on GitHub Actions (main run 38204411015, suite step 38 min 00 s; job limit 60 min). Grew from 93 tests at step 1. |
| Assumptions register | **169 entries**: 168 in force, 1 "direction approved" (calibration noise levels); 168 applied in code, 1 "not yet" (`parallel_suite`); **none reviewed by a domain expert yet**. |
| Database migrations | 0001–0009, each with a tested downgrade; 34 tables. |
| Model spending | Live (Render): $0.18 over 6 calls. Local development database: 14 runs, 23 calls, $1.09. Plus one curation call ($0.13) and two Critic test calls ($0.02) on scratch databases. All within the caps ($2 per run, $50 per month). |
| Second-model review | Every step reviewed by ChatGPT, usually two to four rounds; each accepted finding fixed with tests that failed on the code before the fix. Reviews saved verbatim in `docs/reviews/`. |

---

## 2. What the system does today, end to end

A person (signed in with the shared password and a name) or the command line:

1. **Writes a query.** A hypothesis in words, a domain from a fixed list (only "grain-size strengthening" is
   supported), one or more registered sources, a data-sufficiency option ("fixed minimum" by default, or "use what
   is available"), and an optional note. It is saved as a draft or submitted. Editing a draft changes it in place;
   editing a returned query creates its next version; earlier versions never change.
2. **Reviews and dispatches it.** A reviewer confirms or changes the domain (recorded under their name) and
   dispatches it, with an optional spending ceiling, or returns it with a comment. Dispatch creates a run in the
   queue and records, for every registered source, its newest sealed version (or "not selected"), and the settings
   version of each agent role. Dispatch is refused at the monthly cap, for an unsupported domain, and for
   constructed test data in a run not marked as a test. Every write is recorded in `action_record` with the
   person's name.
3. **A background worker claims the run** (one at a time; claims are advisory-locked and heartbeated), and runs the
   pipeline in a separate "guarded" child process (a file-access tripwire, not a sandbox).
4. **The Planner** (a language model, Claude Opus 5.5) reads only the claim, the domain, the sources' descriptions,
   the approved tag values and record counts. It answers a fixed JSON form: the claim's scope (alloy class, phase
   class, test type, temperature band), which parts the claim states and which it assumes, the outcome, and
   exclusion rules from a menu. **Code** checks the answer and builds the plan from the domain profile's defaults
   plus only those parameters. The model, the eligibility rules, the calibration and the sufficiency option never
   come from the Planner.
5. **The narrowing decision (code)** counts candidate records per part of the claim (structure only, no outcome
   value). If every part has records and the claim is one plan, the run goes on. If some part has none, code builds
   a narrower question; the original ends "partly sufficient" with no verdict, and the narrower question is created
   as a separate, linked query that a person must dispatch. A claim spanning several bands, test types or alloy
   classes with no empty part fails ("not one plan").
6. **The run waits at the rules lock** for a named person to confirm "the question as tested" (what will actually
   be tested, each part marked stated or assumed). The confirmation page sends back a fingerprint of exactly the
   content and text it showed; anything else is refused. Fixed-plan runs (the reference test) do not wait.
7. **Checkpoint 1, the rules lock:** the plan is stored with its fingerprint and the database's time, plus three
   tags (property, alloy class, test condition). Nothing in the plan can change afterwards (database triggers).
8. **Records are stored** by code adapters (not by an agent) from each chosen source's sealed version, every record
   kept, each with how it was extracted.
9. **Checks (code)** raise flags: physically impossible values, and, between different sources only, exact
   duplicates, possible duplicates, conflicts and ambiguous groups.
10. **The Critic** (Claude Haiku 4.5) classifies multi-record flags from metadata only (never the numbers). Its class
    and reason are shown to people with a label saying they are unverified; **no code decision reads them**.
11. **Inclusion (code)** decides one eligibility rule per record, for the primary set and nine named sensitivity
    sets, without ever seeing an outcome value.
12. **Checkpoint 2, the dataset freeze:** code recomputes every set, checks the stored decisions equal what the
    locked rules produce and that seven primary-set invariants hold, then stores a fingerprint (by stable record
    identity, never database ids) and the counts. With no eligible record, no dataset is frozen.
13. **Statistics (code)** fits the one supported model on the pooled set, each source and each sensitivity set;
    applies the two validity checks and the data-sufficiency rule; decides the outcome, the verdict ("supported"
    when the one-sided p < 0.05) and an evidence level 1–6; runs a calibration on simulated outcomes two ways; and
    stores everything.
14. **The Analyst** (Claude Opus 5.5) writes an explanation from named facts code built; it writes no digits (every
    number is a `{placeholder}` code fills in), and code checks its wording. Any Analyst failure leaves code's
    decision standing ("explanation unavailable").
15. **Completion** copies code's stored decision onto the run, unchanged.
16. **The run page** shows code's results statement first, the Analyst's text under its "not verified" label, the
    plot, each source alone and pooled, the sensitivity sets, cautions, Critic flags, checkpoints, sources searched,
    and tokens and cost. A workbook (four sheets) and a records CSV can be downloaded for any outcome.

The command line runs the same pipeline (`hypocurate run …`, `dispatch`, `confirm`, `cancel`, `show`, `export`,
`queue`, `worker`, `sources …`).

---

## 3. Architecture as built

| Part | As built | PRD 6 said |
|---|---|---|
| Web service | FastAPI + Jinja templates, one process (`--workers 1`). Live updates by a small polling script of our own (`static/poll.js`), **not HTMX** (owner's decision). It never runs the pipeline, claims a run or calls a model (tested in a fresh process that opens every page and makes every write). | FastAPI, Jinja, HTMX |
| Worker | One background worker (`hypocurate/worker.py`): claims a run, heartbeats on its claim row, starts a guarded child process for the orchestrator, watches it (900 s without a write or 1,800 s in all → stuck), releases the claim with a reason. Same code as the command line. On Render: 1 CPU / 2 GB (upgraded from 0.5/512 MB after a memory measurement). | One worker; same code as CLI |
| Agents | Planner, Curator, Critic, Analyst as DSPy modules behind one common interface (`call_agent`), through litellm. The **Commentator is not built** (its access lists are empty until step 12). Agent mode "four roles" recorded per run. | Four roles + optional Commentator |
| Models | Planner Claude Opus 5.5; Curator Claude Sonnet 5.5; Critic Claude Haiku 4.5; Analyst Claude Opus 5.5 (owner's decision Q7). | Configurable; decision 17.2 open |
| Database | PostgreSQL 17, Alembic migrations 0001–0009; most rules enforced by triggers and CHECK constraints as well as code. | PostgreSQL, Alembic |
| Files | Source files stored in the database (`source_file`, ≤ 5 MiB each, SHA-256 checked). Plots and workbooks are **built on request** from stored rows and never stored; the `artifact` table is unused (owner's decision). | Files in the DB as binary objects |
| Statistics | numpy/scipy in the runtime (statsmodels is test-side only, as an independent reference). POPPER is not used. | statsmodels and scipy; POPPER optional |
| Containers | One Dockerfile with `base`, `test` and `runtime` stages (runtime last, so Render's plain build gets it); Compose for local work (db, migrate, web, worker, test). The runtime image holds no `tests/` or `docs/` (checked in CI). | Docker from day one |
| Hosting | Render Blueprint (`render.yaml`): web $7, worker 1c-2g ~$25, Postgres $6 + disk, about $38/month. Auto-deploy only after the GitHub check passes. Pre-deploy runs the migrations. | Render |
| Login | One shared password (≥ 24 chars in production) plus a **name at sign-in**, fixed for the session; signed session cookie (12 h); CSRF token on every write; failed-login throttle. | Shared password, signed cookie |
| CI | GitHub Actions: builds the default image exactly as Render does, checks it holds no tests/docs/answers or env files, runs the whole suite in the test image, smoke-tests the image and the Compose stack. | Suite on every change |

**Layout:** `hypocurate/pipeline/` (orchestrator, agents, plan, eligibility, flags, checkpoints, statistics,
calibration, views, plot, workbook), `hypocurate/access/` (allow-lists, dispatcher, access layer, file guard,
guarded runner), `hypocurate/sources/` (adapters, normalizers, versions, curation), `hypocurate/db/` (models,
migrations, retry, actions), `hypocurate/web/` (routes, templates, static), `hypocurate/worker.py`,
`hypocurate/cli.py`, `cli_runs.py`. About 16,500 lines of package code; 113 test files.

---

## 4. What each build step built

Each step: plan approved by the owner (one question at a time), built on a branch with failing tests first, a
summary and a review packet, ChatGPT review rounds, fixes with tests, the owner's merge decision, merge, live check.

| Step | Built (main points) | Notable owner decisions | Reviews |
|---|---|---|---|
| **1 Sources frozen** | MPEA dataset (1,545 records, 237 with grain size; Apache-2.0) and Texas A&M FCC dataset (94 samples; MIT; spreadsheet + CSV view) frozen byte-for-byte with a manifest of SHA-256s pinned to commits; the controlled duplicate extract (16 constructed records, 8 cases) with its answer file kept under `tests/`. | Survivor rule for duplicates: the record carrying the original paper's DOI, then source order MPEA, Texas A&M, extract, then lowest row. | Review + re-check |
| **2 Skeleton** | Config, `/health`, login with throttle, Dockerfile (runtime stage last), Compose, `render.yaml`, CI workflow; **Render connected at this step** (not step 11), so every later step was verified live. | Deploy early; workflow changes need the owner's explicit review (CLAUDE.md 9). | Review + re-check |
| **3 Data model** | 28 tables, 5 views, ~40 trigger functions in migration 0001: checkpoint rules, append-only records, the locking protocol (`hc_write_lock`), per-source search coverage (three kinds of "nothing found" never collapsed), model-call accounting (reserved before the request, cost never stored as totals). | Narrower question = new query linked to a partly-sufficient run; named analysis sets; what may be written to a run in each state. | Review + 2 re-checks |
| **4 Adapters** | MPEA-layout and Texas A&M adapters into one common record format (17 harmonized fields with a status each; values as reported kept verbatim); strict parsing (a malformed file is refused whole); DOI-based paper grouping; source registration with sealed versions and fingerprints; "test connection". | Values "assigned" only on a quoted statement in the source; alloy label is display-only; Texas A&M one group (dataset). | Review + re-check |
| **4b Register** | `hypocurate/assumptions.json` with its validator, and the read-only `/assumptions` page; CLAUDE.md rules 11–12 (every default in the register, read from one named place). | Texas A&M temperature (room temperature) and microstructure (single-phase FCC) **assigned by decision**; tension only; 0.1 at.% same-alloy rule; minimums 30/5/10/10; 2% disagreement tolerance; p < α. | Review |
| **5 Access layer** | Per-role, per-stage allow-lists; immutable access objects only from a trusted dispatcher; every read one locked transaction with audit rows; denials and failures logged apart; vocabularies so blinded views carry no free text; the file-guard tripwire in a guarded process; planted-value tests. | **Threat model:** the layer guards against our own code leaking data to a text-only model; it is not a sandbox. Critic sees metadata, no numbers. | Review + re-check |
| **6 Plan, checkpoints, inclusion, checks** | Plan model (`PLAN_SCHEMA`), rules lock, dataset freeze with fingerprint; Checks (flags); Inclusion (9 ordered eligibility rules); 8 sensitivity sets; constructed-data guard; migrations 0002 (tag lists) and 0003 (record extraction). Reference numbers recomputed and approved (97 records pooled). | **Conflicts never enter the primary set** (corrects PRD 5.3); fixed rules no plan can override; one change per sensitivity set. | Review + re-check + 3 confirmations |
| **7 Statistics** | The model, validity checks, minimums, verdict, per-source labels, evidence level 1–6, result states (incl. "withheld" below the minimums), calibration both ways (fixed noise and Henderson method III), the generator's fixed set, decimal-precision reference check; migration 0004. | Calibration reported both ways (departs from PRD 5.10); informative papers only in the paper count, small-sample factor and df; effective-number-of-papers floor of 2. | Review + re-check + confirmation |
| **7b Groups and influence** | Eligibility rule 5 `group_unknown` (no group is invented); a 7th freeze invariant; a 9th sensitivity set "without the group with the largest share of slope information". | Paper minimum stays a count of informative papers (final for Sprint 1). | Review |
| **8a Curator and agent core** | dspy/litellm locked; the request path (reserve → send → record) with caps and a failure policy (at most two requests per call); the Curator at **source registration** (not in runs) proposing documentation-backed values a person accepts; Texas A&M curation sealed (tension, FCC accepted); temperature bands; migration 0005. | Curator runs only at registration, for dataset-grouped sources; models per role; live costs capped. | Review + re-check |
| **8b Planner, Critic, Analyst, orchestrator** | Planner answer form and plan building by code; narrowing decision and partly-sufficient path; Critic (multi-record flags only); Analyst with placeholders and wording checks; **results statement written by code**; orchestrator; CLI `run`/`dispatch`/`show`; live set of 12 local runs ($1.03); migration 0006. | Code builds the narrower scope; Analyst writes no digits; Critic advice label; spending cap at the Analyst leaves code's decision. | Review + re-check + confirmation |
| **9a Waiting and confirmation** | Status `waiting`; `rules_confirmation` (one named person, content and text stored); cancel; dispatch again; stored spending ceiling; dispatch refusals; orchestrator takes every step from stored rows; migration 0007. | The run waits at the rules lock for a named person; no bulk confirmation; CI job limit 20 → 40 min. | Review + re-check |
| **9b Worker and queue** | Claims (advisory locks + claim row), heartbeat, stuck-child limits, recovery bookkeeping, the per-role recovery rule, a kill matrix (SIGKILL at 11 points), migration 0008; worker plan 1c-2g. | Interrupted Planner repeated once; Critic/Analyst never repeated; spending refusal always a stop; max 3 recoveries. | Review + re-check |
| **fix-agent-contracts** | After the first live runs: the Planner's output description generated from the check's own key list (a drift had made every live Planner answer invalid); a specific reason stored per refused attempt and named in the retry; Analyst whole-sentence rules; contract tests per agent. | Merged on the local live check, without a review round. | — |
| **10a Run pages** | Runs list (cursor paging), run viewer, evidence-level dial, confirmation and cancel pages, live state polling, CSRF, sign-in name; parallel test suite tried and removed (a timing test failed under load); CI limit 40 → 60 min. | Polling script instead of HTMX; glossary moved into the package (`web/glossary.json`). | Review + re-check |
| **10b Other screens** | Queries list, new query/edit, review and dispatch, query page, dispatch again, data sources (register, test connection), read-only agent pages, plot (SVG), workbook + CSV (and CLI `export`), Help page, plain-English failure explanations; then the fixes: act only on the version shown (fingerprint), no formulas in exports, `action_record` (migration 0009). | Every write records who did it; confirm and cancel too. | Review + re-check |

---

## 5. Safeguards as built (CLAUDE.md "rules the code must never break")

| Rule | How it is enforced | Where it is tested |
|---|---|---|
| **1. Code decides; agents advise** | Plans built by code from validated parameters; eligibility, flags' effects, sufficiency, verdict, evidence level computed by code; the Critic's class is read by no decision (a test sets every class at random and finds every decision identical); the Analyst's text cannot set anything; completion only copies code's stored decision. | `test_critic.py`, `test_planner_narrowing.py`, `test_completion.py`, `test_analyst.py` |
| **2. Access contract** | `access/allowlist.py` (one place): allowed fields per role and stage; access objects only from `dispatch.bind`/`bind_invocation`/`bind_code`, bound to one invocation record; every read logged (allowed, denied, failed); blinded views built from vocabularies; the complete outbound model request is tested against planted outcome values (the request bytes captured by a local stub provider). | `test_access_*.py`, `test_critic.py`, `test_agent_contracts.py` |
| **3. Two checkpoints** | Rules lock and dataset freeze in `pipeline/checkpoints.py`, backed by triggers: a plan can be written once; records only after the lock and before the freeze; nothing about the record sets changes after the freeze; refusals logged. | `test_checkpoints.py`, `test_data_model.py`, `test_freeze_invariants.py` |
| **4. Stored is not analysed** | Every record found is stored; eligibility is a separate decision (`run_record`, `analysis_set`); conflicts are kept and never enter the primary set; duplicates counted once by the survivor rule. | `test_eligibility.py`, `test_controlled_duplicates_handling.py`, `test_conflict_policy.py` |
| **5. Two validity checks never waived** | Check 1: an alloy with two distinct (transformed) grain sizes. Check 2: residual df ≥ 1, ≥ 2 informative groups, effective number of papers ≥ 2, estimable uncertainty. Check 1 only → coefficient alone. Enforced in code, in every simulated fit, and by database constraints. | `test_statistics.py`, `test_statistics_boundaries.py`, `test_informative_inference.py` |
| **6. One supported model** | `pipeline/statistics.py`: OLS with alloy intercepts on d^-½, cluster-robust SE by group with the small-sample correction counting informative groups, one-sided t test with (informative groups − 1) df. Validation refuses any other outcome or predictor. | `test_reference_numbers.py`, `test_generated_fixed_set.py` |
| **7. Data sufficiency fixed at the lock** | Stored on the query version, copied into the plan, checked by the database; "use what is available" waives the minimums only and labels the result exploratory. Below the minimums under the fixed option, nothing computed from outcomes is stored or shown (run-wide). | `test_analysis_stage.py` |
| **8. Narrower question is a separate record** | `hypothesis.narrower_of_run_id`, one per original; the original completes "partly sufficient" with no verdict; the narrower run locks the stored narrower plan. | `test_cli_runs.py` (14.3), `test_migrations_step8b.py` |
| **9. Three kinds of "nothing found"** | Per source, per run (`run_source`, view `run_search_coverage`); classified by code; "reported negative" is never set by code in Sprint 1. | `test_data_model.py`, `test_analysis_stage.py` |
| **10. Model-recalled data never pooled** | A record kind; eligibility rule 1 refuses it; a freeze invariant. Model recall itself is **not built**. | `test_eligibility.py` |
| **11. Calibration is a flag, not a gate** | Calibration rows "computed" or "unavailable" with the reason; a test forces every flag and finds the decision unchanged. | `test_calibration.py` |
| **12. Every model call recorded; caps** | A `model_call` row is reserved (with a maximum cost) before each request, in a transaction that checks the per-run cap ($2), the stored ceiling and the month cap ($50), then finished with the reported usage. Unknown cost counts at its maximum. | `test_agent_core.py`, `test_recovery.py` |
| **13. Wording** | "In the sources searched" in every outcome wording; "does not exist" never written; verdict "supported under the stated model". Fixed in code (statement, outcome wordings, Analyst wording rules). | `test_statement.py`, `test_analyst.py` |
| **14. No SQL/connection/path to a model** | Agents get only text built from access-object reads; no tools are offered to any model. | `test_agent_core.py`, `test_access_dispatch.py` |

**What the safeguards do not claim** (stated in the threat model): the access layer and file guard protect against
our own code leaking data to a model; they are not a sandbox against hostile code in the same process. The only
construction-level guarantee about answer material is that the deployed image holds no `tests/` or `docs/`. The
sign-in name is not authenticated (one shared password). The Analyst's narrative and the Critic's reasoning are
unverified (labelled so).

---

## 6. Data, eligibility and statistics as built

### 6.1 Sources

| Source | Records | Notes |
|---|---|---|
| MPEA (Borg et al. 2020) | 1,545 (237 with grain size) | Grouped by paper (DOI-derived key; 265 papers). Apache-2.0. |
| Texas A&M FCC (Mulukutla et al. 2026) | 94 samples, 82 compositions | Grouped as one dataset (six batches kept; a sensitivity set treats them as groups). Test type tension and phase class FCC from an **accepted curation** of the paper (Curator proposal, owner accepted); test temperature (room temperature) and microstructure (single-phase FCC) **assigned by decision** of the owner, cited. MIT. |
| Controlled duplicate extract | 16 constructed records | Constructed test data: usable only in a run marked as a test; refused at dispatch otherwise. |

Harmonization: compositions to atomic percent at full precision (the alloy label is display only); units as stated
by the headers; values as reported kept verbatim; every harmonized value has a status (`converted`,
`not_reported`, `not_convertible`, `assigned_from_source`, `assigned_by_decision`).

### 6.2 Eligibility (one rule per record, first that applies)

1 model-recalled · 2 invalid value · 3 out of scope (tension only; 20–25 °C or band room temperature; FCC single
phase) · 4 missing value · 5 no group (`group_unknown`) · 6 scope not confirmed · 7 excluded by a menu rule (grain
size < 0.1 µm) · 8 identity (ambiguous group, conflict, duplicate counted once) · 9 single grain size · 10 in scope
(eligible). Duplicates are resolved before grain sizes are counted.

**Fixed rules no plan can change (primary-set invariants, checked again at the freeze):** no exact duplicate twice;
no record connected to a definite conflict; no physically invalid value; no unresolved-identity group; no
model-recalled record; no constructed record in an unmarked run; no record without a group.

### 6.3 Sensitivity sets (one change each, descriptive only, never change the verdict)

no exclusions · tension and compression · six batches as groups · same alloy at 1 at.% · source-only assignments ·
scope not confirmed included · possible duplicates separate · conflicts by the survivor's value · without the group
with the largest share of slope information.

### 6.4 The model and the decision

Yield strength = baseline per alloy + k × d^-½ (d in µm). OLS with alloy intercepts; cluster-robust SE by group with
G/(G−1) × (N−1)/(N−K), G = informative groups; one-sided test of k > 0 against t(G−1); supported when p < 0.05.
Fixed minimums: 30 records, 5 alloys with ≥ 2 grain sizes, 10 informative groups, 10 residual df.

**Result states and evidence levels:** 6 sufficient with a verdict · 5 exploratory · 4 coefficient only (check 2
failed) · 3 below the minimums under the fixed option (counts only, nothing from outcomes) · 2 no coefficient
fitted · 1 nothing tested (no dataset frozen; or a partly-sufficient original).

**Calibration** (a flag): 2,000 simulations per world (no effect; smallest effect 150 MPa·µm^½), two ways: fixed
noise (60/40 MPa) and noise estimated from the frozen residuals (Henderson's method III; departs from PRD 5.10, owner's
decision). Exact 95% intervals. The specified test is somewhat over-confident on these data (about 7–9%
significant with no effect against a nominal 5%); PRD 5.10's 7.2% is not reproduced exactly.

### 6.5 Reference numbers (approved by the owner, 2026-10-06; reproduced live)

| Set | Records | Alloys | Groups | Resid. df | k (MPa·µm^½) | ± 1 SE | p (one-sided) |
|---|---|---|---|---|---|---|---|
| Pooled | 97 | 22 | 20 | 74 | 424.9 | 64.4 | 1.3e-6 |
| MPEA alone | 76 | 13 | 19 | 62 | 424.1 | 62.2 | 1.1e-6 |
| Texas A&M alone | 21 | 9 | 1 | 11 | ≈ 1173 | none (one group) | none |
| Without the largest-share group | 89 | 22 | 19 | 66 | 393.5 | 90.5 | 1.9e-4 |

These differ from the PRD (98 records, 428 ± 64; 77 MPEA records, 427 ± 61) because the owner fixed the plan to
tension only, which removes one compression record (MPEA row 139) and its paper. The pooled result is reported with
its concentration diagnostics: 20 informative papers, an effective number of 3.94, largest paper share 38.7%, t df 19.

---

## 7. The agents as built

| Role | Model | Receives (allow-list) | Returns | Code's checks; on failure |
|---|---|---|---|---|
| **Planner** | Opus 5.5 | claim, domain, sources' descriptions, approved tags, record counts (stage `before_lock`) | fixed JSON form (scope, stated marks, outcome, menu exclusion rules) | shape and vocabulary; a part marked assumed must hold the default; plan valid for the template. Corrected once, then the run fails `planner_failed`. |
| **Curator** | Sonnet 5.5 | one sealed source version's documentation and the target fields, **at registration only** (no run) | per target: value + exact quote, or "not stated" | quote found in the documentation with a listed term (code and database); a person accepts or rejects each proposal; accepted values sealed into a new source version. |
| **Critic** | Haiku 4.5 | sources' descriptions, record metadata (no numbers), each flag's kind and category (stage `curation`); only flags naming ≥ 2 records | class (4 codes) + reason ≤ 300 chars per flag | per-entry form check; failures leave flags unclassified; no decision reads the class. |
| **Analyst** | Opus 5.5 | claim, domain, sources, coverage, named facts built by code (stages `analysis`, `closed_without_freeze`, `narrowed`) | plain text with `{placeholders}`, no digits | names, digits, required phrases, whole-sentence placement, wording rules; corrected once; any failure → "explanation unavailable", code's decision stands. |
| **Commentator** | — | nothing (lists empty until step 12) | — | not built |

**One agent call** (`pipeline/agents/interface.py`): open a stage and an invocation record (short transaction) →
bind an access object from the invocation → read the role's complete input → render it as text → DSPy request
through a recorded engine: reserve the maximum cost (caps checked) → send once (outside any transaction) → record
usage and cost → code's check → accept, or one corrected retry with a fixed note naming the code and reason, or
stop → close the stage. At most two requests per call. No provider text is stored or forwarded.

---

## 8. Website and command line as built

**Pages** (all behind the login except `/login` and `/health`): Queries (list, 50 per page, cursor), New query /
Edit, Query page (versions, runs, Dispatch again), Review and dispatch (picker, domain confirmation, ceiling,
return with comment, run queue), Runs list (with a small evidence dial), Run page (statement, dial, Analyst text,
plot, per-source, sensitivity, cautions, flags, checkpoints, sources, tokens and cost; live state while open),
Confirm (the question as tested), Data sources (list, register a code-defined source, test connection), Agents
(read-only, one page per role with "Fixed in code"), Help (every glossary entry, searchable), Assumptions (the
register). Downloads: workbook (`/runs/N/workbook`) and records CSV.

**Every write** goes through the pipeline's own functions, carries the session's CSRF token and the signed-in name
(stored in `action_record`), and, for query writes, the version shown and its fingerprint (a stale page is refused:
"This query has changed since you opened it; reload the page").

**Command line:** `hypocurate run "<claim>" --sources mpea,tamu_fcc --by NAME [--fixed-plan] [--ceiling] [--queue]`,
`dispatch Q-… [--again]`, `confirm N --by NAME`, `cancel N --by NAME`, `show N`, `export N --out F [--csv]`,
`queue`, `worker [--once]`, `sources register|test|curate|proposals|accept|reject|seal-curation|export-curation`,
`version`, `check-db`.

---

## 9. Database (migrations 0001–0009)

| Migration | Adds |
|---|---|
| 0001 (step 3) | The data model: 28 tables, views for coverage and cost totals, trigger functions for checkpoints, append-only rules, locking, accounting. |
| 0002 (step 6) | The approved tag lists (data only). |
| 0003 (step 6) | `record.extraction` (how each record was extracted). |
| 0004 (step 7) | Withheld results, unused-record counts, test-run labels, calibration methods, the fourth per-source label, `run.evidence_level`, p-value reporting fields. |
| 0005 (step 8a) | `agent_invocation`, `curator_proposal`, `curator_decision`, `source_file.role`, `model_call.invocation_id`. |
| 0006 (step 8b) | The query's sufficiency option; partly-sufficient rules; the Critic's class and reason; the narrower-plan backstop; `run.statement_format_version`. |
| 0007 (step 9a) | Status `waiting`; `rules_confirmation`; `run.spending_ceiling`; one narrower question per run; cancel rules; source-freshness check at confirmation. |
| 0008 (step 9b) | `run_claim` (claims, heartbeat, release reasons, recovery mark). |
| 0009 (step 10b) | `action_record` (who did what; append-only; downgrade locks the table before checking for rows). |

---

## 10. Comparison with the PRD (v1.6)

### 10.1 By PRD section

| PRD | As specified | As built | Status |
|---|---|---|---|
| 2.1 Scope | Four agents + optional Commentator; two checkpoints; one model; access contract; two sources; three outcomes; domain and tags; tokens and cost; regression suite and second-model review; info buttons and Help; generator and calibration; website; CLI; containers and Render | All built **except the Commentator** (optional, step 12). | Met, Commentator pending |
| 3 Query flow | Curator extracts each source's records | **Adapters (code) extract tabular records**; the Curator runs at source registration on documentation only (owner, step 8a). The run **waits for a person's confirmation** before the lock (step 9a; not in the PRD). | Changed by decision |
| 3.1 Outcomes | Three outcomes; gap report | Three outcomes; gap **facts** stored by code and explained by the Analyst; no experiment design (deferred, as the PRD says). | Met |
| 4 Access | Allow-lists; AccessDenied; audit log; experiment flag may relax the contract | Built as specified, plus a threat model, vocabularies, accepted disclosures. **The relaxation flag is not built** (backlog). Curator sees documentation at registration, not run data. | Met; flag deferred |
| 5.1–5.2 Plan, exclusions | Planner fills a template; exclusion menu | Built; plan schema fixed in code; one temperature band per plan; other bands need a range. | Met |
| 5.3 Stored ≠ analysed | Defaults "unless the Planner sets a different rule"; conflicts "both enter" | **Fixed rules no plan can change**; **conflicts never enter the primary set** (the PRD contradicted CLAUDE.md rule 4); duplicates only between different sources; possible duplicates counted once (the one plan choice); a record without a group is not eligible. | Changed by decision |
| 5.4 Narrower question | Planner proposes it | **Code builds the narrower scope** from its counts (the Planner cannot see which part is empty). | Changed by decision |
| 5.5 Domain and tags | Fixed lists; mismatch stops the run | Built; tags seeded by migration; one tag per kind at the lock. | Met |
| 5.6 Checkpoints | Rules lock, freeze | Built, with the freeze also checking the seven invariants; fingerprint by stable identity. | Met |
| 5.7 Model | As specified; ±1 tolerance; 427 ± 61 | Built; groups counted as **informative** papers in the paper minimum, factor and df; effective-papers floor; two-tier tolerances; reference numbers 424.9 ± 64.4 (tension only). | Changed by decision |
| 5.8 Sufficiency | Fixed minimum, power-based (not a gate), use what is available | Fixed minimum and use-available built; power-based **not offered as an option**: "estimated power" is reported for information. Below the minimums, nothing from outcomes is shown. | Met (power option deferred) |
| 5.9 Significance record, commentary | Code's record; Commentator | Code's results statement and record; no Commentator. | Partly (commentary pending) |
| 5.10 Calibration | Noise fixed in advance, never estimated from outcomes | **Both ways**: fixed and estimated from frozen residuals (method III). 7.2% not reproduced (≈ 7.8–8.6%). | Changed by decision |
| 6 Architecture | HTMX; files incl. plots in DB | Polling script; plots and workbooks built on request, not stored. | Changed by decision |
| 7 Data model | Suggested tables | Expanded (34 tables); several PRD fields replaced by views or join tables (listed in step 3). | Met, refined |
| 8 Lifecycle | Queue, heartbeat, resume or fail, caps | Built; heartbeat on a claim row; resume from stored rows; recovery rules per role; caps checked before each request; a spending cap at the Analyst leaves the decision standing. | Met, refined |
| 9.1 Queries | Search and filters by status and domain | List with paging (cursor); **no search or filters yet**. | Partly |
| 9.2 New query | Model recall source "comparison only" | No model recall source. | Partly (recall deferred) |
| 9.3 Review | Shared picker with search and filters | Picker of submitted queries; no search/filter. | Partly |
| 9.4 Run viewer | Header, banner, checkpoints, significance record, calibration, plot, per-source, commentary, **stages with inputs and outputs**, **records by group** | All except: **no per-stage panel with inputs, outputs, tool calls and reasoning** (tokens and cost per stage are shown); **records by group are in the workbook, not on the page**; commentary section says none. | Partly |
| 9.5 Agents | Read-only pages with "Fixed in code" | Built; "may call" / "may not do" are fixed sentences, not read from code. | Met |
| 9.6 Data sources | Register a source by form; generic CSV upload adapter | Lists and registers **code-defined sources only**; **no generic uploaded-table adapter**; test connection works. | Partly |
| 9.7 Info buttons, Help | One glossary; tests | Built (`web/glossary.json`); every entry used; every button names an entry. | Met |
| 10 Sources | As described; "82 single-phase FCC", "room-temperature tensile" | Corrected: the source says "94 FCC alloy conditions"; temperature and single-phase are owner decisions; tension and FCC from accepted curation. | Met, corrected |
| 11 Download | Workbook (4 sheets) + CSV | Built for every outcome; text cells are strings; CSV formula signs neutralised. | Met |
| 12 CLI | run, show, export, worker | Built, plus confirm, cancel, dispatch, queue, sources. | Met |
| 13 Testing and review | Suite on GitHub; recorded responses; reference run; access tests; generator; second-model review | Built. Agent tests use a local stub provider that records the real outbound request bytes. | Met |
| 14 Acceptance | Section 12 below | | |
| 15 Build order | Steps 1–12 | Steps 1–10 done; Render connected at step 2. | 11–12 pending |
| 16 Working practice | Dev container | Deferred (owner); Codespace used. | Changed |
| 17 Open decisions | 11 items | Decided: 1 (minimums, pending expert review), 2 (models), 4 (2% tolerance), 5 (files in DB), 7 (tag lists), 9 (one group), 11 (reported). Open: 3 (model recall), 6 (sprint length), 8 (power calculation), 10 (calibration values: direction approved, technical review pending). | Mostly decided |

### 10.2 PRD corrections and clarifications agreed with the owner (for the next PRD update)

Collected from the step summaries; each is recorded there with its reason.

1. **Narrower question** is a new query linked to its original run (not a version link).
2. **Named analysis sets** replace a single "sensitivity only" flag; at the freeze the primary set equals the
   records decided eligible.
3. **Search coverage per source** replaces a run-level "kind of nothing found"; mixed results are never collapsed.
4. `run` needs `verdict`, `exploratory`, `evidence_level`, `spending_ceiling`, statement format version.
5. **Exploratory** = "use what is available" and data below the minimums.
6. **Token and cost totals are views**, not stored columns; a call is recorded before the request; unknown cost
   counts at its maximum; the Commentator's calls would count in the run's totals.
7. What may be written to a run in each state (queued, running, completed, failed).
8. Files are `bytea` ≤ 5 MiB; a source version copies its interpretation settings and is sealed once.
9. Grain-size transformation applied at analysis; harmonization gives µm.
10. Texas A&M: tension stated in the source; temperature and single-phase FCC assigned by decision; 81 vs 82
    compositions noted.
11. Paper identity from a normalized DOI; malformed files refused whole; alloy label display only; same-alloy rule
    0.1 at.% rounding with a 1 at.% sensitivity set.
12. Values-disagree tolerance 2% relative to the smaller value (PRD recommended 15%); grain size within 2% to pair.
13. Verdict rule p < α (strict).
14. Calibration both ways (departs from 5.10); its first-result figures replaced.
15. **Conflicts never enter the primary set**; fixed rules no plan can override; duplicates only across sources.
16. Rule order (duplicates before grain sizes; missing condition is "scope not confirmed" first); a record with no
    group is not eligible.
17. Eight, then nine, named sensitivity sets; "438 ± 67 with four records removed" removed (chosen after seeing
    outcomes); "233 ± 97 no exclusions" came from one compression record.
18. Reference numbers as in Section 6.5; each "±" is one standard error, not a confidence interval.
19. Constructed test data: runs marked at dispatch, labelled everywhere, excluded from aggregates; a database rule
    for it is backlog.
20. Access: Critic sees descriptions, not content; Analyst's gap-report input; threat model; dispatcher; Inclusion
    and Checks read through access objects; the relaxation flag is backlog.
21. Curator: runs at registration on documentation, for dataset-grouped sources; adapters extract tables.
22. Agents: DSPy engine interface; one HTTP request = one recorded call; at most two requests per agent call; caps
    also per curation ($2).
23. One temperature band per plan; other bands name a range.
24. Narrowing decided by code on structure counts; code builds the narrower scope.
25. Sufficiency option stored on the query version.
26. A spending cap at the Analyst leaves code's decision; the run completes with "explanation unavailable".
27. The Analyst receives named facts and writes placeholders; the Commentator gets nothing until step 12.
28. The run waits at the rules lock for a named person's confirmation; new status `waiting`.
29. Dispatch refuses at the month cap and for unmarked constructed data; dispatch again; cancel only queued or
    waiting.
30. Live updates by a small script, not HTMX; plots and workbooks built on request; sign-in takes a name.
31. Queries list: short source names, cursor paging, a Plan column; plain-English failures with "Technical detail".
32. Registration from the website covers code-defined sources only.
33. Every write records who did it (`action_record`); forms act only on the version shown.

---

## 11. Comparison with the proposal overview (draft v3.13)

| Overview element | State after Sprint 1 |
|---|---|
| **Three outcomes**, stated for the sources searched | Built and demonstrated (sufficient, partly sufficient, insufficient). |
| **Four agents + Commentator; code decides** | Four agents built; Commentator not built. Code decides everything (Section 5). |
| **Access contract (Table 2), structural safeguard** | Built and tested, including the complete outbound request. This is the core of RQ1's condition (c). |
| **Two checkpoints** | Built. |
| **One model; validity checks; sufficiency options** | Built (power-based not offered as a gate). |
| **Calibration on generated data** | Built per run, both ways. |
| **Generated data with known answers** | A generator and a fixed set in the suite (statistics); **no batches of generated queries through the full pipeline** (the RQ1 instrument). |
| **Tier A structured datasets** | Two sources (MPEA, Texas A&M). Other compilations (Gorsse, Couzinié, Kumar et al.) not added. |
| **Tier B papers, Tier C figures** | Not built. The Curator reads documentation only at registration; no paper reading or extraction workers. |
| **Experiment design for insufficient cases** | Not built (gap facts only). |
| **Harmonized evidence base** | Exists per run (records with provenance, sealed source versions); not yet a shared, queryable resource across runs. |
| **Test registry** | Exists implicitly (locked plans, fingerprints and verdicts per run in the database); no registry view. |
| **Testability-gap map** | Not built (needs many runs and the grid of alloy class × property × condition). |
| **RQ1 (do agents p-hack; does structure stop them)** | The structural barrier (condition c) is built. Conditions (a) full visibility and (b) instruction only, the relaxation flag, the "show true / show false" runs and the null-case batches are **not built**. |
| **RQ2 (can agents tell data are missing)** | The outcome logic exists and is code-decided; the withheld-data benchmark (set W) and scoring are not built. |
| **RQ3 (four agents vs one)** | The common interface and the recorded agent mode exist; **no single-agent implementation**. |
| **Benchmark (40–60 claims, sets E/L/S/N/W; Tables 3–4)** | Not built. Only the sprint claims (FCC grain size; BCC at 1000 °C; a partly-sufficient claim) have been run. |
| **MCP servers** | Not built (plain Python access functions). |
| **Frameworks: DSPy, litellm, own orchestrator** | As proposed. POPPER, PyMARE, pymatgen, matminer not used. |
| **Website at hypocurate.ai** | Live on the Render address; the domain is not attached yet. |
| **Midpoint target (Nov 4): Tier A end to end, ~20 benchmark items, single-agent baseline, first RQ1 result** | Tier A end to end: done. Benchmark items, single-agent baseline, RQ1 result: **not started**. |
| **Cost target: under $1 per hypothesis** | Met so far: about $0.04–$0.19 per run on the sprint claims. |

The overview's figures quote the earlier numbers (77 records, 427 ± 61; pooled 98, 428 ± 64; "438 ± 64" with four
removals). The built system's approved numbers are in Section 6.5.

---

## 12. Acceptance criteria (PRD 14)

| Criterion | Status | Evidence |
|---|---|---|
| **14.1a** Reference test, fixed plan | **Met** (CLI and live on Render) | `test_reference_numbers.py`; live run 1 reproduced 97/22/20/74, 424.9 ± 64.4. Numbers differ from the PRD's by the approved tension-only decision. |
| **14.1b** Live test through the website | **Partly.** A live Planner run completed on Render (run 3), but **from the command line**; the website path (submit, review, dispatch, confirm in the browser on the live site) exists and is tested locally but has **not been run on the live site**. | live run record; `test_web_queries.py`, `test_web_runs.py` |
| **14.1 Duplicates** | **Met** in tests (controlled extract, marked test run) | `test_controlled_duplicates_handling.py` |
| **14.2** Blocked access and changes | **Mostly met.** AccessDenied, planted values, allow-lists, Curator blind to direction, refused changes after each checkpoint, logged. **Not built: viewing or exporting the audit log on the website** (step 11). | `test_access_*.py`, `test_checkpoints.py` |
| **14.3** Insufficient case | **Met from the command line** (BCC at 1000 °C insufficient, missing evidence; partly-sufficient with a narrower question; exploratory vs fixed; failed search; unsupported domain refused). Not yet shown on the live site. | `test_cli_runs.py`, local live runs B, C2, D |
| **14.4** Browser closed, worker or web restarted | **Met in tests** (kill matrix at 11 points; web restart while a worker runs; spending cap). Not yet demonstrated live. | `test_kill_matrix.py`, `test_web_isolation.py`, `test_web_state.py` |
| **14.5** Engineering conditions | **Met**: tokens and cost per stage in the viewer and workbook equal the recorded calls; suite green on GitHub; a findings file per step; agent mode recorded; significance record and calibration on every completed run; info buttons and Help; the fixed generated set. | per-step summaries |
| **14.6** Commentator | **Not built** (optional). | — |
| **14.7** Demonstration on the deployed site | **Not done** (step 11). | — |

---

## 13. Process and quality

- **Working method:** one build step at a time; plan approved before any code; one question at a time to the owner;
  failing tests first; whole suite before every push; one push per review round; second-model review of every step
  and every safeguard change; the owner decides each merge.
- **Mutation checks:** every new safeguard was switched off in a scratch copy and the tests that should catch it
  were run; every surviving mutation led to a new test (several hundred mutations over the sprint).
- **Reference dumps:** before and after each step, the reference runs and whole orchestrator runs were dumped and
  compared byte for byte with `main`.
- **Image proof:** the package's hash is the same in the repository, the runtime image and the test image; the
  runtime image holds no tests or docs.
- **CI time:** the GitHub suite step grew from about 15 min (step 7) to 38 min (step 10b). The job limit is 60 min,
  so about 20 min of headroom remain; a parallel suite was tried and removed (a timing test failed under load).
- **Register discipline:** every default and decision has an entry with its history; settings checks are
  reference-and-value checks only, behaviour is covered by the named regression tests.

---

## 14. Known limitations and open items

**Not built (in the PRD or overview):** the Commentator; the audit-log view; model recall; the generic CSV upload
adapter and the source form; search and filters on lists; the per-stage input/output panel and record groups on the
run page; the power-based sufficiency option as a gate; experiment designs; Tier B/C sources; the benchmark and
batch runs; the single-agent baseline; RQ1 conditions (a) and (b) and the relaxation flag; MCP servers; the
testability-gap map; the domain `hypocurate.ai`; the dev container.

**Open technical items:**
- Calibration's simulation seed comes from the whole-run fingerprint, so identical data in two runs give different
  draws (7.8% vs 8.6% live); backlog: an analysis-specific seed and about 10,000 simulations before the final
  evaluation.
- The calibration noise-level method (estimated from residuals) is "direction approved, pending technical review".
- The Analyst sometimes answers without its output form (corrected on the retry, at the cost of a second call), and
  its narrative can draw conclusions of its own (labelled "not verified").
- The Critic's reasons can misstate the metadata (seen in a live test); its class is advice only.
- The Texas A&M per-source coefficient (≈ 1173) is far from MPEA's (≈ 424); why is not established.
- The evidence for the slope is concentrated (one paper holds 38.7% of the slope information; effective number of
  papers 3.94).
- `ANTHROPIC_API_KEY` is set on the Render worker only through the dashboard, not declared in `render.yaml`; whether a
  Blueprint sync keeps it is unconfirmed.
- The sign-in name is not authenticated; the monthly cap counts only calls recorded in one database.
- Every scientific assumption (23 entries) awaits a domain expert's review (Prof. Jaafar El-Awady's group).
- The CI suite time is rising toward the limit.

**PRD Section 18 backlog items added during the sprint:** an analysis-specific seed and ~10,000 simulations; a
database rule for constructed data; agents that execute code (with operating-system isolation first); the
relaxation flag; a stricter small-sample correction or resampling (given the over-confidence).

---

## 15. Questions for the owner (to plan the next sprint)

A starting list for the reviewer to refine:

1. **Step 11 scope:** attach `hypocurate.ai`; run 14.1b, 14.3 and 14.4 on the live site through the website; build
   the audit-log view; rehearse the 14.7 walk-through. Anything else before the midpoint?
2. **Step 12:** build the Commentator now, or move straight to the research questions?
3. **Research priorities for the midpoint (Nov 4):** which first — the benchmark items, the single-agent baseline
   (RQ3), or RQ1's conditions (a) and (b) with the relaxation flag and null-case batches?
4. **Benchmark:** which claims from overview Tables 3–4 can the current single supported model test? Most need
   other models (two-group comparisons, "no difference" tests, correlations); is adding models the next step?
5. **Data:** add Tier A compilations (Gorsse, Couzinié, Kumar et al.) next, or start Tier B (papers)?
6. **Statistics:** resolve the calibration-noise technical review; adopt the analysis-specific seed and 10,000
   simulations; consider a stricter small-sample correction given the over-confidence?
7. **Expert review:** when can the 23 scientific register entries (minimums, tolerances, Texas A&M assignments,
   same-alloy rule) be reviewed by the Johns Hopkins group?
8. **Website gaps:** which matter for the demo — search and filters, the stage panel, record groups, the source
   form, model recall?
9. **CI time:** split the suite, a larger runner, or accept the trend?
10. **Cost and operations:** keep the worker at 1c-2g (~$38/month total)? Declare the API key in `render.yaml`?

---

## 16. What a flow chart of the code should cover (and where to look)

A complete flow chart of the current code should show at least these, each traceable to the files named:

1. **System context:** browser → web service (FastAPI) → PostgreSQL ← worker → guarded child → model provider;
   GitHub Actions → Render deploy (pre-deploy migrations). Files: `web/app.py`, `worker.py`, `access/guarded.py`,
   `render.yaml`, `.github/workflows/tests.yml`.
2. **Query lifecycle:** draft → submitted → returned (→ next version) / dispatched; domain confirmation; run created;
   `action_record` rows; version fingerprint checks. `pipeline/queries.py`, `web/app.py`.
3. **Run state machine:** queued → running → waiting → running → completed / failed; cancel from queued or waiting;
   dispatch again. Migrations 0001, 0007; `queries.py`, `orchestrator.py`.
4. **Worker loop and claim:** sweep → `finish_narrower_questions` → `claim_next` (lease locks, claim row) →
   recovery if it was running → start guarded child → heartbeat and monitor threads → watch (stall 900 s, total
   1,800 s, lost claim, shutdown) → release reason. `worker.py`, `pipeline/queue.py`, `pipeline/recovery.py`.
5. **`orchestrator.prepare`:** start; narrower question path; fixed plan path; Planner (stored or new); domain
   mismatch; narrowing decision (proceed / partly sufficient / not one plan); wait. `pipeline/orchestrator.py`,
   `narrowing.py`, `agents/planner.py`.
6. **`orchestrator.proceed`:** confirmed waiting → running; plan to lock and confirmation check; rules lock; store
   records; Checks; Critic; Inclusion; freeze; statistics; Analyst; copy decision. Each step only if its stored
   result is absent.
7. **One agent call:** `runstage.open_stage` → `dispatch.bind_invocation` → `role_input` → `call_agent` →
   `RecordedEngine` (reserve → send → finish) → check → correct / stop → `close_stage`. `agents/interface.py`,
   `agents/lm.py`, `agents/spend.py`.
8. **Access layer:** roles and stages, allow-list, the read transaction, audit rows, denial vs failure.
   `access/allowlist.py`, `dispatch.py`, `layer.py`, `fields.py`, `stage.py`.
9. **Data path:** source registration and sealing, curation (curate → proposals → accept/reject → seal → export),
   extraction, Checks (flags), Inclusion (rule order), freeze (invariants, fingerprint). `sources/versions.py`,
   `sources/curation.py`, `pipeline/extract.py`, `flags.py`, `checks.py`, `eligibility.py`, `inclusion.py`,
   `checkpoints.py`.
10. **Statistics:** per analysis: fit records, validity checks, minimums, result state, evidence level, calibration
    both ways, decision; completion copy. `pipeline/statistics.py`, `calibration.py`, `analysis.py`, `completion.py`.
11. **Failure and recovery outcomes:** the failure table (which failures fail the run, which complete it with
    "explanation unavailable", which stop it for recovery), and recovery's per-role rule.
12. **Read paths:** run page, workbook, plot, statement, all from one read-only snapshot. `pipeline/run_view.py`,
    `statement.py`, `plot.py`, `workbook.py`.

The companion Word document draws each of these.
