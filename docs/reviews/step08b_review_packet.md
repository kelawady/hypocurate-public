# Build step 8b — review packet

Date: 2026-10-07. Branch: `step-08b-agents`, from `main` at `d76c86a`. Head when generated: `4661ce2`. Generated from the
files on disk by a script (`~/hc-work/step08b/packet.py`, quoted in section 11), so every diff and output below is
quoted exactly.

## How to use this packet

Step 8b builds the Planner, the narrowing decision and the partly-sufficient path, the Critic, the Analyst, the
orchestrator and the command line's `run`, `dispatch` and `show`. It holds safeguard changes (listed at the top of the
summary), so please review against `docs/reviews/checklist.md` and answer the questions at the end of the summary.
Sections: 1 the summary; 2 the code diff; 3 the new test files; 4 the changed tests; 5 the register; 6 the reference
comparison with `main`; 7 the live calls; 8 the mutation checks; 9 new tests on `main`'s code; 10 the suite and the
images; 11 the plan file and the scripts.

## 1. The summary

# Build step 8b — summary for review

Date: 2026-10-07. Branch: `step-08b-agents` (from `main` at `d76c86a`). **Status: built; the whole suite passes (1,728 locally); pushed; not merged** (owner's instruction: "When built: full suite, summary, review packet, push, and stop. Do not merge."). Plan, every owner answer and the progress checklist: the step 8b plan file (quoted in the packet, section 11).

PRD Section 15, step 8 ("Agents"), second part: the Planner, the narrowing decision and the partly-sufficient path, the Critic, the Analyst, the orchestrator, and the command line's `run`, `dispatch` and `show`, with criteria 14.1 and 14.3 passing from the command line. Part 8a (merged and live, schema 0005) built the agent core, the Curator, the spending caps and the temperature bands.

**Safeguard changes in 8b (second-model review before any merge; CLAUDE.md "How we work" item 5):**

1. Migration 0006 (the query's sufficiency option; partly-sufficient rules; the Critic's class and reason).
2. The access layer: stage `narrowed`; the Analyst's lists (claim, domain, sources, coverage, `analyst_facts`) at three stages; the Commentator's lists emptied until step 12; the code role `narrowing` (`candidate_counts`); the accepted-disclosures list shortened by two items.
3. The narrowing decision (code; counts of structure only, before any lock) and the partly-sufficient copy path.
4. The Planner's answer form, its stated/defaulted marks, and plan building by code.
5. The Critic's classes (read by no code decision).
6. The Analyst's facts (named facts built by code; nothing computed from outcomes below the minimums), its placeholders (it writes no digits) and its text checks.
7. The guarded runner: `PRELOADED = ("psycopg", "scipy")`.
8. The gap facts: the kind of "nothing found" classified by code.

**Not changed:** `render.yaml`, `.github/workflows/`, the Dockerfile, Compose, and the dependency locks (checked with `git diff --name-only d76c86a..HEAD`). No PRD document is changed; corrections are listed at the end.

## What the checks cover, and what they do not

The Analyst's checks cover **numbers and wording, not interpretation**. Every number in an explanation is written by code: the Analyst writes `{name}` placeholders and code renders them. Code also checks the wording rules (for example "in the sources searched", no causal language, no verdict where there is none). No check shows that the Analyst's sentences draw the right conclusions from the facts. The label stored with an explanation is "numbers written by code from the run record". It is not a statement that the explanation is verified.

**The Critic has not been exercised by a live call.** The real data (MPEA and Texas A&M) raise no flags, so every live run sent nothing to the Critic. The Critic is tested only with recorded responses through the local stub, including its complete outbound request and the test that no decision reads its class.

### Interpretation findings from the live explanations (owner's request)

From the first accepted live explanation (run 9), before the owner's last round of code-built sentences:

1. **A conclusion from one flag applied to both calibrations.** "In both cases the conclusion was that the method is over-confident" used only `{estimated_flag}`; the fixed-noise flag was never referenced. *Addressed:* code now gives one calibration summary covering both flags.
2. **A direction read by the Analyst.** "which points in the direction the claim describes" was the Analyst's own reading of a positive estimate. *Addressed:* code now gives a direction note built from the estimate's sign and the claim's direction (the plan's alternative).
3. **An inference about the scope.** "parts of the scope … were not stated by the claim itself" was inferred from the note that a fixed plan's scope was not read from the claim. *Addressed:* code now gives one complete sentence for a fixed-plan run.

The last live explanation (run 12, after those changes, passed on its first attempt) still contains two conclusions of its own, which the checks do not catch:

- "So the nominal p-value should be read as more favourable than it really is" is drawn from the calibration flag.
- "the information then becomes even more concentrated in one remaining group" is drawn from the 52.1% largest share.

Neither changes a number or a decision.

## The owner's decisions (2026-10-07)

All the decisions of the step 8 plan (Q1–Q10 and the owner's additions of 2026-10-06) stand. Answers in 8b planning, one question at a time:

- **A1, run order (partly sufficient):** narrowing decision → Analyst (narrowing facts only, the run still running) → `copy_partly_sufficient` → the narrower question created as submitted. This corrects the plan file's order: the database refuses an agent stage on a completed run except the Commentator's.
- **A2, the query's sufficiency option:** stored on the hypothesis version (migration 0006), fixed once submitted, the original's on a narrower question; the plan's option must equal it.
- **A3, a spending cap reached at the Analyst:** code's decision stands. The run completes with "explanation unavailable (spending cap)". Before the freeze (Planner, Critic) a cap still fails the run. This departs from PRD 14.4 for this case (PRD corrections below).
- **A4:** a new stage `narrowed`.
- **A5:** database guards for partly sufficient.
- **A6, the Commentator:** reads nothing at any stage until step 12. Its earlier lists are kept in the register's history.
- **A7, the Critic's answer:** four classes, plus a reason of at most 300 characters, shown to people only.
- **A8, the narrower question's run:** locks the stored narrower plan (the Planner is bypassed). Its text is built by code.
- **A9:** a named reviewer at the command line (`--by`).
- **A10:** live set A–D, at most $2.
- **During the build:**
  - The two accepted-disclosure items that no longer occur were removed until step 12.
  - **A11:** a claim of more than one temperature band (extended by Claude Code, and stated to the owner, to more than one test type or alloy class) is not one plan and fails before the lock, unless the partly-sufficient path applies.
  - **A12:** scipy preloaded in the guarded process.
  - **A13:** checked that no production module imports statsmodels or pandas; pandas is in the runtime lock only as a dependency of dspy. The guard checks were also run in the runtime image.
  - Code classifies the kind of "nothing found".
- **Approval additions B1–B4:**
  - **B1:** a narrower question on other source versions is refused.
  - **B2:** an Analyst failure on the partly-sufficient path still completes the run and creates the narrower question.
  - **B3:** the drafts were shown before the live set.
  - **B4:** run A's plan was compared field by field with the reference plan.
- **After the live set:**
  - Code builds the narrower scope (the Planner cannot see which part has no usable record).
  - Failure facts are stored as counts or rule names, never text, also for attempts later corrected.
  - **Rounding and phrasing by code:** display precision is defined in one place (approved). The Analyst writes `{name}` placeholders and no digits. It receives fewer facts, built by code, including a summary of the sensitivity sets classified with the per-source labels and function.
  - The Planner marks each scope part as stated by the claim or defaulted.
  - The two word-based rules on p-values and paper figures were removed. With a verdict, the pooled p-value and paper-figures phrases are required placeholders.
  - **Code-built sentences:**
    - the model sentence;
    - the fixed-plan sentence;
    - the direction note;
    - one calibration summary;
    - the definition of a group.
  - Units on every estimate, standard error, scatter, shift and temperature.
  - The nominal level is shown as a percentage, and each simulation interval says what it is.
  - Plain wording for the labels, and "groups" throughout.

## What was built (each commit on the branch)

| Milestone | Commit | What |
|---|---|---|
| 1 | `27bd22b` | Migration 0006 (below). |
| 2 | `7c9e5be`, `17bfe7b` | Access layer: `narrowed`, the Analyst's lists, the Commentator emptied, `narrowing` with `candidate_counts`, `analyst_facts`; `lock_rules` refuses at `narrowed`; two accepted-disclosure items removed. |
| 3 | `b80e10c` | `pipeline/queries.py`: create, submit, confirm with a named reviewer, dispatch (each registered source's newest sealed version; the settings of the three run roles), start, the narrower question. Draft settings of the Planner, Critic and Analyst. |
| 4 | `82aab3c` | The Planner (fixed answer form; plan built by code; one correction then fail); `pipeline/narrowing.py`; `completion.copy_partly_sufficient`; `agents/runstage.py`; the roles' failure codes. |
| 5 | `628f7a6` | The Critic (batches; per-entry checks; written once before the freeze; nothing sent without flags). |
| 6 | `8754b82` | The Analyst and its text checks (later replaced by placeholders). |
| 7 | `0336041` | The orchestrator; `run`, `dispatch`, `show` in the guarded process; scipy preloaded; the kind of "nothing found"; the suite-wide no-live-call setting. |
| 8 | `9bbd70f` | Register entries; the no-live-call test; full suite, test image, runtime-image guard checks, reference comparison, mutation checks. |
| 9 | `4a49511` … `c72b15b` | The live set and the owner's changes after it (above). |

## Migration 0006

0001–0005 untouched; no earlier function replaced. Each new rule is its own function with its own trigger, named so that it fires after the earlier trigger on the same table (PostgreSQL fires BEFORE triggers in name order), so earlier messages keep priority.

| Rule | Where |
|---|---|
| `hypothesis_version.sufficiency_option` (default `fixed_minimum`); fixed once submitted; a narrower question has its original's | column, CHECK, `hc_version_option` |
| The plan's option equals the query's; no plan after a narrowing decision of partly sufficient | `hc_plan_query` |
| `partly_sufficient` only with no plan, no record and a done narrowing decision of partly sufficient | `hc_run_partly_sufficient` |
| `flag.critic_class` from the four codes; `critic_reason` 1–300 characters, only with a class | CHECKs |

Completing a run with no plan needed no trigger change: 0001 requires a plan only for "sufficient". The downgrade refuses while a query uses another option. Tested up, down and up; a failed upgrade changes nothing.

## A run (the orchestrator)

Planner → narrowing decision (code) → either [partly sufficient: Analyst (narrowing facts) → copy → narrower question; stop], or [not one plan: fail before the lock], or → rules lock → records → Checks → Critic → Inclusion → dataset freeze → statistics → Analyst → `copy_decision`. A fixed-plan run bypasses the Planner (criterion 14.1a, or a narrower question's stored plan, after the B1 check). No model call runs inside a database transaction: an agent stage is opened and closed in short locked transactions, and the request is sent with none open. This is tested with `pg_stat_activity` for every role.

| Failure | Outcome |
|---|---|
| Planner: invalid plan (shape, template, scope, tag), or an attempt to set a fixed rule or the option (no such key in its form) | Corrected once, naming only the code; then the run fails (`planner_failed`) |
| Planner: another domain | Run fails (`domain_mismatch`) |
| Claim not one plan, with no part lacking records | Run fails (`claim_not_one_plan`, with the reason) |
| Spending cap at the Planner or the Critic | Nothing sent; run fails (`spending_refused`) |
| Spending cap or any other failure at the Analyst | Run completes with code's decision; "explanation unavailable (<code>)"; on the partly path the narrower question is still created (B2) |
| Critic answer off-form for a flag / whole call failed | That flag, or the batch's flags, left unclassified; run goes on |
| Narrower question on other source versions (B1) | Refused before the lock (`narrowing_sources_changed`) |
| A refused checkpoint or write | Run fails with the code |
| A call whose recording failed | Stays open; the database refuses to end the run; recovery is step 9 |

## The agents

**Planner** (Opus 5.5):
- **Receives** the claim, domain, sources, approved tag values and record counts. Never an outcome value: the planted-value test runs on the raw request.
- **Answers** in a fixed form: domain match, claim scope, a stated/defaulted mark per scope part, outcome, exclusion rules from the menu, and a narrower scope that should be null.
- **Code** builds the plan from the profile's defaults and these parameters only. Live run A's plan equals the reference plan in every field (B4).

**Narrowing** (code):
- Counts records per claim part with a grain size and the outcome at an accepted status. The counts come from the sealed versions, structure only.
- Decides proceed, partly sufficient (code builds the narrower scope) or not one plan.
- Stores the decision, the counts' fingerprint, the source versions' fingerprints and the stated marks.

**Critic** (Haiku 4.5):
- **Receives** each flag's kind and category, plus the named records' metadata. Never the compared numbers.
- **Answers** with one of four classes and a reason of at most 300 characters.
- **No code decision reads the class.** Two runs of one version, one with every class set at random, give identical decisions, sets, freeze record and fingerprint, statistics and gap facts. A source scan of the imported package confirms it.

**Analyst** (Opus 5.5):
- **Receives** the claim's text, the domain, the sources' names, and named facts built by code (`pipeline/analyst_names.py`). Below the minimums no estimate, standard error, p-value or paper-figures name exists.
- **Answers** with plain text using `{name}` placeholders and no digits.
- **Code checks the template:** unknown names, digits outside placeholders, the required placeholders. It then renders the finished text and applies the wording rules.
- **Tested** that no rule fires on any code-built value or fixed wording, and that no name exposes a bare p-value or paper figure.
- **Request size:** about 3,400 input tokens, against 14,200 before.

## The live set and checks (local development database; prices checked against Anthropic's page on 2026-10-07: all match)

All records are in `docs/reviews/step08b_live_record.json`: 12 runs, 21 model calls, **$1.0278 actual** in total. The reserved maxima summed to $1.39.

| Run | What | Result | Actual cost |
|---|---|---|---|
| A (1) | 14.1b, FCC claim, live Planner | Sufficient, supported; **plan equals the reference plan in every field (B4)**; Analyst refused (old checks) | $0.1839 |
| B (2) | 14.3, BCC at 1000 °C | Insufficient in the sources searched, missing evidence, no freeze, no verdict; Analyst passed | $0.0504 |
| C (3) | Partly-sufficient claim | Failed `claim_not_one_plan (narrower_missing)`: the Planner proposed no narrower scope; led to "code builds it" | $0.0213 |
| C2 (4) | Same, after the change | Partly sufficient, level 1; narrower question Q-0005 | $0.0670 |
| D (5) | `dispatch Q-0005` | Sufficient on the stored narrower plan | $0.1738 |
| 6 | Diagnostic call (one attempt, raw answer to a local scratch file only) | Refused (p-value rule) | $0.0816 |
| 7 | Check with display strings and phrases | Refused twice (`wording_refused`, `numbers_unmatched`) | $0.1779 |
| 8 | Check with placeholders | Refused twice by the two word-based rules (since removed) | $0.0784 |
| 9, 10, 11 | Three checks after the rules were removed | Passed, passed after its one correction, passed | $0.1500 |
| 12 | Check with the code-built sentences and units | Passed on the first attempt | $0.0434 |

## Tests

- **The whole suite passes:** 1,728 locally. The test image (rebuilt at M8) ran 1,679, all passing.
- **New test files:**
  - `test_migrations_step8b.py`
  - `test_access_step8b.py`
  - `test_queries.py`
  - `test_planner_narrowing.py`
  - `test_critic.py`
  - `test_analyst.py`
  - `test_orchestrator.py`
  - `test_cli_runs.py`
  - `test_no_live_calls.py`
- **No live calls in the suite:** the test process and its guarded children have no provider credential and a closed local provider address. Every agent test answers through the stub, which records the raw request bytes.
- **Failed before the code:** the new tests were run against `main`'s package with scaffolding where needed. For example, 37 of 38 migration tests failed there; the up/down/up test passes there because nothing above 0005 exists to round-trip. Module-level tests of new modules fail on `main` by import.
- **Mutation checks** (scratch copy, `PYTHONPATH`): 26 mutations, all re-run on the final tests and caught; a control run is clean. The packet, section 8, has the full output.
  - **Migration:** d01–d05.
  - **Planner and narrowing:** p01–p04, n02–n03. **p01 first survived:** no case had a valid shape with an invalid plan; one was added.
  - **Copy path:** c01.
  - **Critic:** k01–k02. **k01 was first caught only by the behavioural test:** the source scan read the repository instead of the imported package; changed.
  - **Analyst:** x01–x04, x06 and y01–y03. **x04 and x06 first survived:** the withheld guard was hidden by the statistics layer, and the sensitivity labels were untested; tests added. **y03 first survived:** an extra fact carrying the raw statistics output went unnoticed. The two access tests now check that the facts hold no record identity and no full-precision number.
  - **Stage `narrowed`:** a01.
  - **Orchestrator:** o01, o03.
  - **Guard:** g01.
- **Reference results:** byte-compared with `main` on the five reference runs: decisions, every analysis, freeze fingerprints and calibrations are identical.
- **Runtime image:** the guard tests' checks run with the image's own package. Scipy loads with no refusal; a later ctypes call, a new native library and a planted `.env` read are still refused. The image has no tests, docs, pytest or statsmodels.
- **Changed tests:** none removed or weakened; each was re-pointed because a decision changed its premise. The packet, section 4, has the full diff.
  - **Fixture changes:**
    - the query's option is chosen before dispatch (A2);
    - a partly-sufficient run needs a narrowing decision and no plan (A5); the access world's original run was reshaped accordingly;
    - code stage outputs are stored in the access world.
  - **Access tests:**
    - the Analyst's lists, and the named facts in place of the step 5 fields;
    - the Commentator reads nothing (tests renamed and replaced, listed in commit `7c9e5be`);
    - code role lists.
  - **Register pins:** `code_role_access` date, `PARTLY`.
  - **Migration head tests.**
  - **Critic codes in old flag tests.**
  - **Analyst text tests**, rewritten for placeholders.
  - **The orchestrator stub's Analyst text.**
  - **Narrowing tests** after "code builds the narrower scope".
  - **One `claim_not_one_plan` case** (now two test types).

## Assumptions register

**135 entries**, all in force; one partly applied (`constructed_test_runs`, screens in step 10).

- **New:**
  - `query_sufficiency_option`
  - `partly_sufficient_rules`
  - `narrowing_decision`
  - `narrower_question`
  - `planner_answer`
  - `critic_classes`
  - `analyst_facts_only`
  - `analyst_text_checks`
  - `run_order_and_failures`
  - `nothing_found_kinds`
  - `no_live_calls_in_suite`
  - `display_precision`
- **Reworded** (earlier wording in history): `access_allow_lists` (with the Commentator's step 5 lists as the starting point for step 12), `code_role_access`, `accepted_disclosures`, `pipeline_file_guard`, `agent_models` (now applied: yes), `request_failure_policy`, `evidence_level_scale`, `copy_decision_only_copies`.
- **Drafts for the owner's review** (noted in the entries): the three agents' instruction texts and limits.

## Open items

1. **Interpretation.** The Analyst can still draw conclusions of its own (see above). The checks do not cover them.
2. **The Critic** has not run live.
3. **Calibration draws differ between runs of different query versions:** the plan fingerprint includes the hypothesis version. The approved numbers are unaffected. A backlog item already exists (an analysis-specific seed).
4. **When the command line is started from outside the repository folder**, the guard logs refusals for reading that folder. They are harmless; no guard change was made.
5. **The Commentator's lists, and the two removed disclosure items,** are decided in step 12.
6. **Live registration on Render** stays the owner's decision. The live database is at schema 0005 until this merges.

## PRD corrections and clarifications (for the next PRD update)

1. **PRD 3 / 5.4:** the narrowing decision is taken by code, before any lock, on counts of structure, and code builds the narrower scope. The partly-sufficient original's Analyst runs before it is completed. The narrower question locks the stored narrower plan.
2. **PRD 5.8:** the sufficiency option is stored on the query version.
3. **PRD 14.4:** a spending cap reached at the Analyst leaves code's decision standing; the run completes with "explanation unavailable" (owner, A3).
4. **PRD 4:** the Analyst receives named facts built by code, not results tables. The Commentator receives nothing until step 12.
5. **PRD 3.1 / 14.3:** the kind of "nothing found" is classified by code from stored facts; "reported negative" is never set by code in sprint 1.
6. **PRD 5.9 (for the Commentator):** placeholders, rather than a number check alone, make every number come from code.

## Questions for the reviewer

1. **Access.** Can the Planner, the Critic or the Analyst receive anything beyond their lists: through the request code builds, a retry, a failure note, the named facts, or the narrowing output? In particular, anything computed from outcomes below the minimums?
2. **Code decides.** Can any model output set a plan value beyond the allowed parameters, a narrowing result, a flag's effect, an outcome, a verdict, a label or a level?
3. **Migration 0006.** Do the new triggers hold against direct SQL? Is the downgrade exact?
4. **Partly sufficient.** Can a run be completed as partly sufficient, or a narrower question run, other than by the rules stated?
5. **Placeholders.** Can the Analyst's finished text contain a number not written by code, a p-value without its description, or the paper figures apart?
6. **Failures.** Does every row of the failure table behave as stated? Can a model call ever run inside a database transaction?
7. Is any claim in this summary, the code or the register stronger than the code supports?

## 2. Code diff (`d76c86a..HEAD`, the package; the register is in section 5)

````diff
diff --git a/hypocurate/access/allowlist.py b/hypocurate/access/allowlist.py
index e8f4cd4..15b6c19 100644
--- a/hypocurate/access/allowlist.py
+++ b/hypocurate/access/allowlist.py
@@ -13,8 +13,8 @@ isolation as a precondition.
 Allowed fields, not blocked fields: a role receives exactly the fields listed for it at
 the run's stage, and nothing else. Each field is built from named keys only
 (`hypocurate.access.fields`), never by copying a row and removing what is forbidden. Text
-in the blinded views (the Planner, the Critic, the gap report and the Commentator without
-a freeze) comes from fixed vocabularies (`vocabulary.py`) or is replaced by a marker; the
+in the blinded views (the Planner, the Critic, and the Analyst's facts without a freeze;
+step 8b) comes from fixed vocabularies (`vocabulary.py`) or is replaced by a marker; the
 plan is projected recursively by `PLAN_SCHEMA`. What these views still disclose by design
 is listed in `ACCEPTED_DISCLOSURES`; timing is not protected.
 
@@ -46,7 +46,8 @@ ROLES = ("planner", "curator", "critic", "analyst", "commentator")
 # agents. They read through access objects too, bound by `dispatch.bind_code`, so their reads
 # are logged. No agent setting can bind as one of them. Step 7 (owner, 2026-10-05; a safeguard
 # change, reviewed by a second model): Statistics and the gap facts.
-CODE_ROLES = ("inclusion", "checks", "statistics", "gap_facts")
+# Step 8b (owner, 2026-10-07): the narrowing decision, before any lock, on counts of structure only.
+CODE_ROLES = ("inclusion", "checks", "statistics", "gap_facts", "narrowing")
 ALL_ROLES = ROLES + CODE_ROLES
 
 # none: queued or failed. before_lock: running, no plan. curation: plan locked, no dataset
@@ -55,8 +56,10 @@ ALL_ROLES = ROLES + CODE_ROLES
 # final: completed after a dataset freeze. final_without_freeze: completed with no dataset frozen.
 # registration (step 8a, owner 2026-10-06): not a run stage; the Curator reads one sealed source
 # version, bound by a registration invocation (`dispatch.bind_invocation`), with no run.
+# narrowed (step 8b, owner 2026-10-07, A4): running, no plan, and code's narrowing decision of partly
+# sufficient stored; no plan can be locked from here (lock_rules needs before_lock; migration 0006).
 STAGES = ("none", "before_lock", "curation", "analysis", "closed_without_freeze", "final", "final_without_freeze",
-          "registration")
+          "registration", "narrowed")
 
 FIELDS = MappingProxyType({
     "claim": "The claim in words: query number, version number, text, and whether it is a narrower question.",
@@ -109,6 +112,20 @@ FIELDS = MappingProxyType({
                          "field's status, grain size and test temperature, and the category values from their "
                          "vocabularies. No outcome value, no value as reported, no free text.",
     "outcome": "The run's status, outcome, verdict and exploratory label.",
+    "candidate_counts": "For the narrowing decision (code; step 8b), before the lock, per chosen source from its "
+                        "sealed version (its key and fingerprint): counts of records per combination of phase class, "
+                        "test type and temperature band (from their vocabularies), reported test temperature, the "
+                        "status of each of those fields, of grain size and of each outcome field, and whether a grain "
+                        "size is present. Counts and statuses only: no outcome value, no composition, no free text.",
+    "analyst_facts": "For the Analyst (step 8b, owner Q6 and 2026-10-07): named facts built by code from what it "
+                     "stored (pipeline.analyst_names), each a finished display string or ready-made phrase the "
+                     "Analyst refers to as {name}: the decision and its wordings; the plan's threshold, option and "
+                     "minimums, and per scope part whether the claim stated it or the Planner assumed it; the pooled "
+                     "result and its counts against each minimum; per source its result and label; both "
+                     "calibrations; a summary of the sensitivity sets built by code; the gap facts; at 'narrowed' "
+                     "the claim's parts, their counts and the narrower scope. Below the minimums no estimate, "
+                     "standard error, p-value or paper figures. Never a record-level value or identity, a Critic's "
+                     "class or reason, or a stage's text.",
     "frozen_analysis_data": "For Statistics (code; step 7), once the dataset is frozen: the freeze's "
                             "fingerprint; the frozen sets (keys from the vocabulary, record ids); and per "
                             "record in any frozen set, and only those: id, source, stable identity "
@@ -117,10 +134,9 @@ FIELDS = MappingProxyType({
                             "No record outside the frozen sets, no value as reported, no free text.",
 })
 
-_ANALYSIS = frozenset({"claim", "domain", "sources_meta", "plan", "records_full", "decisions", "flags_full",
-                       "results", "coverage", "stage_outputs", "run_cost"})
-_GAP_REPORT = frozenset({"claim", "domain", "sources_meta", "plan", "coverage", "stored_record_counts",
-                         "decisions", "flags_kind", "condition_summaries"})
+# Step 8b (owner, 2026-10-07, Q6): the Analyst receives stored facts only, the same list at each of its
+# stages; what `analyst_facts` holds depends on the stage (see FIELDS).
+_ANALYST = frozenset({"claim", "domain", "sources_meta", "coverage", "analyst_facts"})
 
 ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
     "planner": MappingProxyType({
@@ -135,17 +151,15 @@ ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
         "curation": frozenset({"sources_meta", "record_metadata", "flags_kind"}),
     }),
     "analyst": MappingProxyType({
-        "analysis": _ANALYSIS,
-        # Owner, 2026-10-05: the gap report gets everything except outcomes, plus condition summaries.
-        "closed_without_freeze": _GAP_REPORT,
-    }),
-    "commentator": MappingProxyType({
-        "final": _ANALYSIS,
-        # Owner, 2026-10-05: with no dataset frozen, only what the Analyst received for the gap
-        # report, plus the Analyst's gap report and the run's outcome. No outcome values, no
-        # row-level records.
-        "final_without_freeze": _GAP_REPORT | {"gap_report", "outcome"},
+        "analysis": _ANALYST,
+        "closed_without_freeze": _ANALYST,
+        # A4: the partly-sufficient original, before any lock; `analyst_facts` holds the narrowing facts only.
+        "narrowed": _ANALYST,
     }),
+    # Owner, 2026-10-07 (A6): the Commentator reads nothing at any stage until step 12, when the role is
+    # built and its lists are decided and reviewed. Its step 5 lists are kept in the register entry
+    # 'access_allow_lists' as the starting point.
+    "commentator": MappingProxyType({}),
 })
 
 
@@ -163,6 +177,8 @@ CODE_ALLOWED: Mapping[str, Mapping[str, frozenset[str]]] = MappingProxyType({
         "analysis": frozenset({"plan", "decisions", "stored_record_counts", "coverage"}),
         "closed_without_freeze": frozenset({"plan", "decisions", "stored_record_counts", "coverage"}),
     }),
+    # Step 8b (owner, 2026-10-07, Q5): before any lock, counts of structure only.
+    "narrowing": MappingProxyType({"before_lock": frozenset({"candidate_counts"})}),
 })
 
 
@@ -258,11 +274,9 @@ POWER_SCHEMA = MappingProxyType({"method": POWER_METHODS, "within_paper_similari
 ACCEPTED_DISCLOSURES = (
     "counts by field status (for example how many yield strengths a source reports or cannot read)",
     "flag kinds and categories (for example that two values differ beyond the tolerance)",
-    "condition summaries, which reveal an exact grain size or temperature when a group has one record",
     "compositions and alloy labels derived from them",
     "DOIs with DOI syntax, which may contain digits",
     "text written or approved by people: the claim, the approved tag values, source names and licences in code",
     "numbers in the locked plan (thresholds, minimums), written before any record exists",
-    "the Analyst's gap report, passed to the Commentator on a run with no dataset frozen",
     "timing of calls and the existence of refusals",
 )
diff --git a/hypocurate/access/fields.py b/hypocurate/access/fields.py
index 639f133..34dce18 100644
--- a/hypocurate/access/fields.py
+++ b/hypocurate/access/fields.py
@@ -393,9 +393,13 @@ def decisions(conn: Connection, ctx: Context) -> dict:
         sets.setdefault(key, [])
         if record_id is not None:
             sets[key].append(record_id)
-    return {"records": [{"record": rec, "eligible": eligible, "rule": vocab.code(rule, vocab.ELIGIBILITY_RULES)}
-                        for rec, eligible, rule in _rows(
-                conn, "SELECT record_id, eligible, rule FROM run_record WHERE run_id = :r ORDER BY record_id",
+    # Step 8b (owner, 2026-10-07): each record's source key, so code can tell which sources contributed.
+    return {"records": [{"record": rec, "source": vocab.code(source, vocab.SOURCE_KEYS), "eligible": eligible,
+                         "rule": vocab.code(rule, vocab.ELIGIBILITY_RULES)}
+                        for rec, source, eligible, rule in _rows(
+                conn, "SELECT rr.record_id, s.key, rr.eligible, rr.rule FROM run_record rr "
+                      "JOIN record rec ON rec.id = rr.record_id JOIN source_version sv ON sv.id = rec.source_version_id "
+                      "JOIN source s ON s.id = sv.source_id WHERE rr.run_id = :r ORDER BY rr.record_id",
                 r=ctx.run_id)],
             "sets": sets}
 
@@ -533,6 +537,88 @@ def frozen_analysis_data(conn: Connection, ctx: Context) -> dict:
             else None, "sets": sets, "records": records}
 
 
+# --- Step 8b: the narrowing decision's counts and the Analyst's facts ---------------------------
+
+# The fields a candidate-count cell names (owner, Q5): the claim's countable parts and what makes a
+# record usable (grain size and the outcome at an accepted status). Alloy class is not countable.
+CANDIDATE_CATEGORIES = ("phase_class", "test_type", "test_temperature_band")
+CANDIDATE_STATUS_FIELDS = CANDIDATE_CATEGORIES + ("test_temperature", "grain_size") + tuple(sorted(OUTCOME_FIELDS))
+
+
+def candidate_counts(conn: Connection, ctx: Context) -> list[dict]:
+    """For the narrowing decision (code; step 8b), before the lock: per chosen source, read through its
+    adapter from the sealed version recorded at dispatch (records are stored only after the lock),
+    counts of records per cell. A cell is the categories (through their vocabularies), the reported
+    test temperature, the status of each field in CANDIDATE_STATUS_FIELDS, and whether a grain size is
+    present. Counts and statuses only: no outcome value, no composition, no free text."""
+    out = []
+    for row in _chosen_sources(conn, ctx):
+        version = load_sealed_version(conn, row.source_version_id)
+        try:
+            result = adapters.read(version)
+        except (AdapterError, UnsealedVersion):
+            out.append({"source": row.key, "version_fingerprint": version.fingerprint, "readable": False})
+            continue
+        cells: Counter = Counter()
+        for r in result.records:
+            h = {f: v.to_json() for f, v in r.harmonized.items()}
+            cells[json.dumps({
+                "categories": {f: _category(f, h.get(f)) for f in CANDIDATE_CATEGORIES},
+                "test_temperature": _number(h.get("test_temperature")),
+                "status": {f: _status(h.get(f)) for f in CANDIDATE_STATUS_FIELDS},
+                "grain_size_present": _number(h.get("grain_size")) is not None,
+            }, sort_keys=True)] += 1
+        out.append({"source": row.key, "version_fingerprint": version.fingerprint, "readable": True,
+                    "n_records": len(result.records),
+                    "cells": [{**json.loads(cell), "n": n} for cell, n in sorted(cells.items())]})
+    return out
+
+
+def _done_output(conn: Connection, run_id: int, stage: str) -> Mapping | None:
+    out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = :s AND status = 'done' "
+                            "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).scalar_one_or_none()
+    return out if isinstance(out, Mapping) else None
+
+
+def analyst_facts(conn: Connection, ctx: Context) -> dict:
+    """The Analyst's facts (step 8b; owner, Q6 and 2026-10-07): named facts built by code from what it stored
+    (`pipeline.analyst_names`), each a finished display string or phrase the Analyst refers to as {name}. Refused
+    when the stored facts its stage needs are missing."""
+    from hypocurate.pipeline import analyst_names as an
+    number = conn.execute(text("SELECT h.number, r.fixed_plan, h.narrower_of_run_id FROM run r JOIN hypothesis_version hv "
+                               "ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
+                               "WHERE r.id = :r"), dict(r=ctx.run_id)).one()
+    if ctx.stage == "narrowed":
+        n = _done_output(conn, ctx.run_id, "narrowing")
+        if n is None or n.get("result") != "partly_sufficient":
+            raise Refused("facts_missing")
+        names = an.narrowing_names(n)
+        kind = "narrowing"
+    else:
+        stats, gap = _done_output(conn, ctx.run_id, "statistics"), _done_output(conn, ctx.run_id, "gap_facts")
+        if stats is None or gap is None:
+            raise Refused("facts_missing")
+        p = _rows(conn, "SELECT content, sufficiency_option, min_records, min_alloys, min_groups, min_resid_df "
+                        "FROM plan WHERE run_id = :r", r=ctx.run_id)[0]
+        content = project(p.content, PLAN_SCHEMA) or {}
+        plan_facts = {"alpha": (content.get("model") or {}).get("alpha"),
+                      "alternative": (content.get("model") or {}).get("alternative"),
+                      "sufficiency_option": p.sufficiency_option,
+                      "minimums": {"records": p.min_records, "alloys": p.min_alloys, "groups": p.min_groups,
+                                   "resid_df": p.min_resid_df}}
+        if number.fixed_plan:
+            note = {"scope_source": an.NARROWER_PLAN_SENTENCE if number.narrower_of_run_id else an.FIXED_PLAN_SENTENCE}
+        else:
+            planner = _done_output(conn, ctx.run_id, "planner") or {}
+            answer = planner.get("answer") or {}
+            note = an.scope_notes(answer.get("claim_scope"), answer.get("stated"))
+        names = an.analysis_names(stats, gap, plan_facts, note)
+        kind = "analysis" if ctx.stage == "analysis" else "no_dataset_frozen"
+    names["query_number"] = str(number.number)
+    an.check_names(names)
+    return {"kind": kind, "names": dict(sorted(names.items()))}
+
+
 READERS: Mapping[str, Callable[[Connection, Context], Any]] = {
     "claim": claim, "domain": domain, "sources_meta": sources_meta, "tag_values": tag_values,
     "record_counts": record_counts, "source_documentation": source_documentation,
@@ -541,5 +627,6 @@ READERS: Mapping[str, Callable[[Connection, Context], Any]] = {
     "results": results, "coverage": coverage, "stage_outputs": stage_outputs, "run_cost": run_cost,
     "stored_record_counts": stored_record_counts, "condition_summaries": condition_summaries,
     "gap_report": gap_report, "outcome": outcome, "record_conditions": record_conditions, "set_flags": set_flags,
-    "frozen_analysis_data": frozen_analysis_data,
+    "frozen_analysis_data": frozen_analysis_data, "candidate_counts": candidate_counts,
+    "analyst_facts": analyst_facts,
 }
diff --git a/hypocurate/access/guard_probe.py b/hypocurate/access/guard_probe.py
index 82a3b75..a3b65ea 100644
--- a/hypocurate/access/guard_probe.py
+++ b/hypocurate/access/guard_probe.py
@@ -165,6 +165,21 @@ def _agent_libraries(_: Any) -> str:
     return "ok"
 
 
+def _statistics_libraries(_: Any) -> str:
+    """Loads what a guarded run imports (step 8b): the pipeline's statistics, analysis and orchestrator modules
+    and the agent libraries; reports which of the test-only or indirect libraries got loaded (none may be:
+    statsmodels is test-only, pandas only a dependency of dspy in the runtime lock)."""
+    import importlib
+    import sys
+    for name in ("hypocurate.pipeline.statistics", "hypocurate.pipeline.calibration", "hypocurate.pipeline.analysis",
+                 "hypocurate.pipeline.orchestrator"):
+        importlib.import_module(name)
+    from hypocurate.pipeline.agents import libraries
+    libraries.load()
+    loaded = sorted(m for m in ("statsmodels", "pandas", "patsy") if m in sys.modules)
+    return "ok" if not loaded else "loaded " + ", ".join(loaded)
+
+
 def _dotenv(action: dict) -> str:
     """A library reading a `.env` file (step 8a): what the tripwire must still catch."""
     import dotenv
@@ -181,7 +196,7 @@ ACTIONS: dict[str, Callable[[dict], str]] = {
     "ctypes_from_address": _ctypes_from_address,
     "register": _register,
     "role_input": _role_input, "sleep": _sleep,
-    "agent_libraries": _agent_libraries, "dotenv": _dotenv,
+    "agent_libraries": _agent_libraries, "dotenv": _dotenv, "statistics_libraries": _statistics_libraries,
 }
 
 
diff --git a/hypocurate/access/guarded.py b/hypocurate/access/guarded.py
index ad369dc..fc1dc19 100644
--- a/hypocurate/access/guarded.py
+++ b/hypocurate/access/guarded.py
@@ -48,7 +48,10 @@ SCRATCH_ENV = ("TMPDIR", "MPLCONFIGDIR", "XDG_CACHE_HOME")
 # installation the guard refuses the ctypes audit events it intercepts (a new library load, a
 # symbol lookup, a foreign call); it does not stop preloaded ctypes from reading process memory
 # directly, which raises no such event (a documented limit; see file_guard).
-PRELOADED = ("psycopg",)
+# Step 8b (owner, 2026-10-07): scipy too, for the same reason: importing it makes a ctypes foreign call at
+# load time (scipy/_lib/_ccallback_c.pyx), which the guard refuses; the run's statistics import scipy.stats.
+# After installation every ctypes event is still refused. (statsmodels is test-only and never imported here.)
+PRELOADED = ("psycopg", "scipy")
 
 
 class GuardedRunError(Exception):
diff --git a/hypocurate/access/layer.py b/hypocurate/access/layer.py
index ef48263..ab2b4b3 100644
--- a/hypocurate/access/layer.py
+++ b/hypocurate/access/layer.py
@@ -78,7 +78,8 @@ LOG = logging.getLogger("hypocurate.access")
 # Fixed codes and their fixed reasons: nothing a caller passes is copied into a reason.
 DENIALS = {
     "unknown_role": "the role is not one of the five agent roles or the code roles",
-    "not_a_code_role": "only the code roles (Inclusion, Checks, Statistics, gap facts) are bound without an agent setting",
+    "not_a_code_role": "only the code roles (Inclusion, Checks, Statistics, gap facts, narrowing) are bound without "
+                       "an agent setting",
     "unknown_stage": "the stage is not one of the access stages",
     "stage_mismatch": "the run is no longer at the stage this access was bound to",
     "not_on_list": "the field is not on the role's list at the run's stage",
@@ -90,6 +91,7 @@ DENIALS = {
     "checks_not_done": "no completed Checks result for this run",
     "checks_not_current": "the completed Checks result does not cover exactly the run's records and flags",
     "not_frozen": "no dataset is frozen for this run",
+    "facts_missing": "the stored facts the Analyst's stage needs are not there (step 8b)",
 }
 FAILURES = ("unknown_run", "unknown_invocation", "lock_timeout", "reader_error", "database_error", "file_guard")
 FUNCTIONS = frozenset(FIELDS) | {"role_input", "bind", "guarded_run"}
diff --git a/hypocurate/access/stage.py b/hypocurate/access/stage.py
index 3bd01aa..c8ba0f5 100644
--- a/hypocurate/access/stage.py
+++ b/hypocurate/access/stage.py
@@ -17,12 +17,15 @@ def actual_stage(conn: Connection, run_id: int, status: str) -> str:
     if status != "running":  # queued, failed
         return "none"
     row = conn.execute(text(
-        "SELECT EXISTS (SELECT 1 FROM plan WHERE run_id = :r) AS locked, "
+        "SELECT EXISTS (SELECT 1 FROM stage_result WHERE run_id = :r AND stage = 'narrowing' AND status = 'done' "
+        "AND output->>'result' = 'partly_sufficient') AS narrowed, "
+        "EXISTS (SELECT 1 FROM plan WHERE run_id = :r) AS locked, "
         "EXISTS (SELECT 1 FROM run_snapshot WHERE run_id = :r) AS frozen, "
         "EXISTS (SELECT 1 FROM calibration_result WHERE run_id = :r AND analysis_result_id IS NULL "
         "AND reason = 'no_dataset_frozen') AS closed"), dict(r=run_id)).one()
     if not row.locked:
-        return "before_lock"
+        # Step 8b (A4): after code's narrowing decision of partly sufficient, no plan is ever locked.
+        return "narrowed" if row.narrowed else "before_lock"
     if row.frozen:
         return "analysis"
     if row.closed:
diff --git a/hypocurate/access/vocabulary.py b/hypocurate/access/vocabulary.py
index 3b70c57..b342286 100644
--- a/hypocurate/access/vocabulary.py
+++ b/hypocurate/access/vocabulary.py
@@ -88,6 +88,16 @@ SENSITIVITY_KEYS = frozenset({"tension_and_compression", "six_batches_as_groups"
                               "conflicts_survivor_value", "without_most_influential_paper"})
 ANALYSIS_SET_KEYS = frozenset({"primary"}) | SENSITIVITY_KEYS
 
+# The Critic's classes of a flag (step 8b; owner, 2026-10-07, A7): code -> the wording shown to people.
+# The database holds the same codes (migration 0006, ck_flag_critic_class). No code decision reads them.
+CRITIC_CLASSES: Mapping[str, str] = {
+    "same_measurement": "same measurement reported twice",
+    "different_specimens_or_conditions": "different specimens or conditions",
+    "possible_transcription_or_unit_error": "possible transcription or unit error",
+    "cannot_tell": "cannot tell from the metadata",
+}
+CRITIC_REASON_MAX = 300  # characters; shown to people only (A7)
+
 
 # Codes in the locked plan's rules (step 6): the registered sources, grouping units, value
 # statuses, domain profiles, and whether single phase is required.
diff --git a/hypocurate/cli.py b/hypocurate/cli.py
index 321a3f7..879f1c6 100644
--- a/hypocurate/cli.py
+++ b/hypocurate/cli.py
@@ -1,6 +1,8 @@
 """The command-line entry point (PRD Section 12). Step 2: `version` and `check-db`.
 Step 4: `sources register` and `sources test`. Step 8a: the curation workflow at registration
-(`sources curate | proposals | accept | reject | seal-curation | export-curation`)."""
+(`sources curate | proposals | accept | reject | seal-curation | export-curation`). Step 8b: `run`, `dispatch`
+and `show` (owner, A9, Q10): a query is created, submitted, confirmed by a named person and dispatched here,
+and the run itself executes in the guarded process (`access.guarded`); the child's error text is never printed."""
 from __future__ import annotations
 
 import argparse
@@ -38,6 +40,21 @@ def main(argv: list[str] | None = None) -> int:
     export = sources_sub.add_parser("export-curation", help="write the curated version's curation.json")
     export.add_argument("key")
     export.add_argument("--out", help="the file to write (default: print it)")
+    run = sub.add_parser("run", help="create, dispatch and run a query to its end (may cost money: model calls)")
+    run.add_argument("claim", help="the hypothesis in words")
+    run.add_argument("--sources", required=True, help="comma-separated source keys, e.g. mpea,tamu_fcc")
+    run.add_argument("--by", required=True, help="the name of the person confirming the domain")
+    run.add_argument("--domain", default="grain_size_strengthening")
+    run.add_argument("--sufficiency", default="fixed_minimum", choices=("fixed_minimum", "use_available"))
+    run.add_argument("--fixed-plan", action="store_true", help="the reference plan, Planner bypassed (14.1a)")
+    run.add_argument("--test-data", action="store_true", help="mark the run as a test with constructed data")
+    run.add_argument("--ceiling", help="the most this run's model calls may cost, in USD (refused above it)")
+    dispatch = sub.add_parser("dispatch", help="dispatch a submitted query by its number and run it (may cost money)")
+    dispatch.add_argument("number", help="the query number, e.g. Q-0002")
+    dispatch.add_argument("--by", required=True, help="the name of the person confirming the domain")
+    dispatch.add_argument("--ceiling", help="the most this run's model calls may cost, in USD")
+    show = sub.add_parser("show", help="print a run's outcome and summary")
+    show.add_argument("run", type=int)
     args = parser.parse_args(argv)
 
     settings = load_settings(web=False)
@@ -49,6 +66,9 @@ def main(argv: list[str] | None = None) -> int:
         reachable = database_reachable(engine)
         print("database reachable" if reachable else "database NOT reachable")
         return 0 if reachable else 1
+    if args.command in ("run", "dispatch", "show"):
+        from hypocurate.cli_runs import command
+        return command(args, engine)
     return _sources(args, engine)
 
 
diff --git a/hypocurate/cli_runs.py b/hypocurate/cli_runs.py
new file mode 100644
index 0000000..adcfd8e
--- /dev/null
+++ b/hypocurate/cli_runs.py
@@ -0,0 +1,143 @@
+"""The command line's `run`, `dispatch` and `show` (PRD Section 12; build step 8b).
+
+`run` creates the query, submits it, records the named person's domain confirmation (A9), dispatches it and
+runs it in the guarded process (`access.guarded.run_guarded`, with the run's audit log for the guard's
+refusals). `dispatch Q-…` does the same for an already submitted query, such as a narrower question (Q10);
+a narrower question's run locks the plan its original's narrowing decision stored (A8). `show` prints what the
+database holds for a run: status, outcome and wordings, the pooled result unless withheld, the per-source
+results, the minimums, the kind of nothing found, the Analyst's explanation (or that it is unavailable),
+the narrower question and the run's tokens and cost. Errors print fixed codes and reasons; the guarded
+child's error text is never printed (it may quote anything).
+"""
+from __future__ import annotations
+
+import json
+import sys
+from decimal import Decimal, InvalidOperation
+
+from sqlalchemy import Engine, text
+from sqlalchemy.exc import IntegrityError
+
+from hypocurate.pipeline import queries
+
+
+def command(args, engine: Engine) -> int:
+    try:
+        if args.command == "show":
+            out = show(engine, args.run)
+            if out is None:
+                print(f"error: no run {args.run}", file=sys.stderr)
+                return 1
+            print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
+            return 0
+        ceiling = _ceiling(args.ceiling)
+        if args.command == "run":
+            q = queries.create(engine, args.claim, [k.strip() for k in args.sources.split(",") if k.strip()],
+                               domain=args.domain, sufficiency=args.sufficiency)
+            queries.submit(engine, q.version_id)
+            queries.confirm_domain(engine, q.version_id, by=args.by)
+            run_id = queries.dispatch(engine, q.version_id, fixed_plan=args.fixed_plan,
+                                      constructed_test_data=args.test_data)
+            number = q.number
+        else:
+            vid = queries.submitted_version(engine, args.number)
+            queries.confirm_domain(engine, vid, by=args.by)
+            with engine.connect() as conn:
+                narrower = conn.execute(text("SELECT h.narrower_of_run_id IS NOT NULL FROM hypothesis h "
+                                             "JOIN hypothesis_version hv ON hv.hypothesis_id = h.id WHERE hv.id = :v"),
+                                        dict(v=vid)).scalar_one()
+            run_id = queries.dispatch(engine, vid, fixed_plan=narrower)
+            number = args.number
+    except queries.QueryRefused as refused:
+        print(f"error: {refused.code}: {refused.reason}", file=sys.stderr)
+        return 1
+    except IntegrityError as error:  # the database's own fixed refusal (for example an unsupported domain)
+        from hypocurate.pipeline.writes import database_message
+        print(f"error: {database_message(error)}", file=sys.stderr)
+        return 1
+    except ValueError as error:
+        print(f"error: {error}", file=sys.stderr)
+        return 1
+    print(json.dumps({"query": number, "run": run_id, "status": "dispatched"}), flush=True)
+    return _run(engine, run_id, ceiling)
+
+
+def _ceiling(value: str | None) -> Decimal | None:
+    if value is None:
+        return None
+    try:
+        ceiling = Decimal(value)
+    except InvalidOperation:
+        raise ValueError("the ceiling is a number of US dollars") from None
+    if not ceiling > 0:
+        raise ValueError("the ceiling is a positive number of US dollars")
+    return ceiling
+
+
+def _run(engine: Engine, run_id: int, ceiling: Decimal | None) -> int:
+    from hypocurate.access.guarded import GuardedRunError, run_guarded
+    try:
+        report = run_guarded("hypocurate.pipeline.orchestrator:run_guarded",
+                             {"run_id": run_id, "ceiling": str(ceiling) if ceiling is not None else None},
+                             timeout=3600, audit=(engine, run_id))
+    except GuardedRunError:
+        print(f"error: run {run_id} did not finish in the guarded process (see the process log); "
+              f"`hypocurate show {run_id}` shows what was stored", file=sys.stderr)
+        return 1
+    print(json.dumps(report, indent=2, ensure_ascii=False))
+    return 0 if report.get("status") in ("completed", "failed") else 1
+
+
+def show(engine: Engine, run_id: int) -> dict | None:
+    from hypocurate.pipeline import statistics as st
+    with engine.connect() as conn:
+        run = conn.execute(text(
+            "SELECT r.id, r.status, r.outcome, r.verdict, r.exploratory, r.evidence_level, r.failure_reason, "
+            "r.fixed_plan, h.number, hv.text, hv.sufficiency_option, h.narrower_of_run_id FROM run r "
+            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
+            "WHERE r.id = :r"), dict(r=run_id)).one_or_none()
+        if run is None:
+            return None
+
+        def output(stage):
+            return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = :s "
+                                     "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).scalar_one_or_none()
+
+        stats, gap, narrowing, explained = output("statistics"), output("gap_facts"), output("narrowing"), output("analyst")
+        results = [dict(r._mapping) for r in conn.execute(text(
+            "SELECT ar.scope, s.key AS source, a.key AS analysis_set, ar.n_records, ar.n_alloys, ar.n_groups, "
+            "ar.resid_df, ar.check1_passed, ar.check2_passed, ar.minimums_met, ar.withheld, ar.estimate, ar.std_error, "
+            "ar.p_value, ar.label FROM analysis_result ar JOIN analysis_set a ON a.id = ar.analysis_set_id "
+            "LEFT JOIN source s ON s.id = ar.source_id WHERE ar.run_id = :r ORDER BY ar.id"), dict(r=run_id)).all()]
+        narrower = conn.execute(text("SELECT number FROM hypothesis WHERE narrower_of_run_id = :r"),
+                                dict(r=run_id)).scalar_one_or_none()
+        original = conn.execute(text("SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = "
+                                     "r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"),
+                                dict(r=run.narrower_of_run_id)).scalar_one_or_none() if run.narrower_of_run_id else None
+        cost = conn.execute(text("SELECT * FROM model_call_totals_by_run WHERE run_id = :r"), dict(r=run_id)).one_or_none()
+    decision = (stats or {}).get("decision") or (narrowing or {}).get("decision") or {}
+    if isinstance(explained, dict) and explained.get("report"):
+        explanation = explained["report"]
+    elif isinstance(explained, dict):
+        explanation = explained.get("shown") or "explanation unavailable"
+    else:
+        explanation = None
+    return {
+        "run": run.id, "query": run.number, "claim": run.text, "status": run.status,
+        "narrower_question_of": original, "narrower_question": narrower,
+        "plan": "fixed" if run.fixed_plan else "the Planner's", "sufficiency_option": run.sufficiency_option,
+        "outcome": decision.get("outcome_wording") if run.status == "completed" else None,
+        "verdict": decision.get("verdict_wording") if run.verdict else None,
+        "exploratory": run.exploratory, "evidence_level": run.evidence_level,
+        "evidence_level_wording": decision.get("evidence_level_wording") if run.status == "completed" else None,
+        "label": decision.get("label"), "failure": run.failure_reason,
+        "results": [r for r in results if not r["withheld"]] if results else [],
+        "withheld": [{k: r[k] for k in ("scope", "source", "analysis_set", "n_records", "n_alloys", "n_groups",
+                                         "resid_df", "minimums_met")} for r in results if r["withheld"]],
+        "minimums_missed": (gap or {}).get("minimums_missed"), "nothing_found": (gap or {}).get("kind"),
+        "sources": (gap or {}).get("sources"),
+        "explanation": explanation, "explanation_label": "model explanation; numbers checked against the run record"
+        if isinstance(explained, dict) and explained.get("report") else None,
+        "tokens_and_cost": {k: v for k, v in cost._mapping.items() if k != "run_id"} if cost else None,
+        "p_value_description": st.P_VALUE_DESCRIPTION if any(r["p_value"] is not None for r in results) else None,
+    }
diff --git a/hypocurate/db/migrations/versions/0006_query_option_and_partly_sufficient.py b/hypocurate/db/migrations/versions/0006_query_option_and_partly_sufficient.py
new file mode 100644
index 0000000..8547c0b
--- /dev/null
+++ b/hypocurate/db/migrations/versions/0006_query_option_and_partly_sufficient.py
@@ -0,0 +1,161 @@
+"""The query's sufficiency option, the partly-sufficient rules and the Critic's class (build step 8b).
+
+Revision ID: 0006
+Revises: 0005
+Create Date: 2026-10-07
+
+Approved by the owner on 2026-10-07 (step 8b plan, answers A2, A5 and A7), subject to the second-model
+review before merging. 0001 to 0005 are untouched: no earlier function is replaced. Each new rule is its
+own function with its own trigger, named so that it fires after the earlier trigger on the same table
+and event (PostgreSQL fires BEFORE triggers in name order), so the earlier rules' messages keep their
+priority.
+
+hypothesis_version (A2: the data-sufficiency option is a parameter of the query, chosen before dispatch):
+- `sufficiency_option`, 'fixed_minimum' (default) or 'use_available'. It can change only while the
+  version is a draft; a narrower question has its original's option.
+plan:
+- the locked plan's `sufficiency_option` must equal its run's query's option;
+- no plan is inserted for a run with a done narrowing decision of partly sufficient (A5).
+run (A5):
+- a run completes as 'partly_sufficient' only with no plan, no stored record, and a done 'narrowing'
+  stage result whose output's result is 'partly_sufficient'. (0001 already requires no verdict, and 0004
+  an evidence level consistent with it.)
+flag (A7):
+- `critic_class` is one of the Critic's fixed codes; `critic_reason` is at most 300 characters, not
+  blank, and only with a class.
+
+Works with the previous release's code: it inserts versions without the option (they get the
+default, which is the only option that code's plans use), never completes a run as partly
+sufficient, and writes no Critic class. The live database holds no run.
+
+Downgrade refuses while a query uses another option than the default (its option would be lost),
+then drops what 0006 added.
+
+Rules for every migration (README, "Database migrations"): it runs inside the one upgrade
+transaction; it keeps working with the previous release's code; and it has a downgrade.
+"""
+from alembic import op
+import sqlalchemy as sa
+
+revision = '0006'
+down_revision = '0005'
+branch_labels = None
+depends_on = None
+
+OPTIONS = ('fixed_minimum', 'use_available')
+# The Critic's codes, copied here so the migration does not change when the code does
+# (tests/test_migrations_step8b.py checks that they equal access.vocabulary.CRITIC_CLASSES).
+CRITIC_CLASSES = ('cannot_tell', 'different_specimens_or_conditions', 'possible_transcription_or_unit_error',
+                  'same_measurement')
+CRITIC_REASON_MAX = 300
+
+
+def _in(column: str, values) -> str:
+    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"
+
+
+FUNCTIONS = [
+    # The query's option: fixed once the version leaves draft; a narrower question has its original's.
+    """
+    CREATE FUNCTION hc_version_option() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE original text;
+    BEGIN
+        IF TG_OP = 'UPDATE' AND OLD.status <> 'draft' AND NEW.sufficiency_option IS DISTINCT FROM OLD.sufficiency_option THEN
+            PERFORM hc_reject('the sufficiency option is fixed once the version is submitted; an edit is a new version');
+        END IF;
+        SELECT hv.sufficiency_option INTO original
+        FROM hypothesis h
+        JOIN run r ON r.id = h.narrower_of_run_id
+        JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
+        WHERE h.id = NEW.hypothesis_id;
+        IF original IS NOT NULL AND NEW.sufficiency_option IS DISTINCT FROM original THEN
+            PERFORM hc_reject('a narrower question has the sufficiency option of its original');
+        END IF;
+        RETURN NEW;
+    END $$
+    """,
+    # The locked plan's option is the query's; no plan after a narrowing decision of partly sufficient.
+    # (0001's hc_plan_insert, which fires first, has locked the run.)
+    """
+    CREATE FUNCTION hc_plan_query() RETURNS trigger LANGUAGE plpgsql AS $$
+    BEGIN
+        IF NEW.sufficiency_option IS DISTINCT FROM (
+                SELECT hv.sufficiency_option FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
+                WHERE r.id = NEW.run_id) THEN
+            PERFORM hc_reject('the plan''s sufficiency option is the query''s (chosen before dispatch)');
+        END IF;
+        IF EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.run_id AND stage = 'narrowing' AND status = 'done'
+                     AND output->>'result' = 'partly_sufficient') THEN
+            PERFORM hc_reject('no plan is locked after a narrowing decision of partly sufficient');
+        END IF;
+        RETURN NEW;
+    END $$
+    """,
+    # Partly sufficient: the original question is never tested (no plan, no record) and code's narrowing
+    # decision is stored. (0001's hc_run_update, which fires first, holds the run's row.)
+    """
+    CREATE FUNCTION hc_run_partly_sufficient() RETURNS trigger LANGUAGE plpgsql AS $$
+    BEGIN
+        IF NEW.status = 'completed' AND NEW.outcome = 'partly_sufficient' THEN
+            IF EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.id)
+               OR EXISTS (SELECT 1 FROM record WHERE extraction_run_id = NEW.id) THEN
+                PERFORM hc_reject('partly sufficient is only for a run with no plan and no record');
+            END IF;
+            IF NOT EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND stage = 'narrowing'
+                             AND status = 'done' AND output->>'result' = 'partly_sufficient') THEN
+                PERFORM hc_reject('partly sufficient needs a narrowing decision of partly sufficient');
+            END IF;
+        END IF;
+        RETURN NEW;
+    END $$
+    """,
+]
+FUNCTION_NAMES = ["hc_version_option()", "hc_plan_query()", "hc_run_partly_sufficient()"]
+
+# (table, event, trigger, function). Each trigger's name sorts after the earlier trigger it follows.
+CHECKED = [
+    ("hypothesis_version", "INSERT", "hc_version_insert_option", "hc_version_option"),
+    ("hypothesis_version", "UPDATE", "hc_version_update_option", "hc_version_option"),
+    ("plan", "INSERT", "hc_plan_insert_query", "hc_plan_query"),
+    ("run", "UPDATE", "hc_run_update_partly_sufficient", "hc_run_partly_sufficient"),
+]
+TRIGGERS = [f"CREATE TRIGGER {t} BEFORE {event} ON {table} FOR EACH ROW EXECUTE FUNCTION {f}()"
+            for table, event, t, f in CHECKED]
+
+
+def upgrade() -> None:
+    op.add_column('hypothesis_version', sa.Column('sufficiency_option', sa.Text(),
+                                                  server_default=sa.text("'fixed_minimum'"), nullable=False))
+    op.create_check_constraint(op.f('ck_hypothesis_version_sufficiency_option'), 'hypothesis_version',
+                               _in('sufficiency_option', OPTIONS))
+    op.create_check_constraint(op.f('ck_flag_critic_class'), 'flag',
+                               f"critic_class IS NULL OR {_in('critic_class', CRITIC_CLASSES)}")
+    op.create_check_constraint(op.f('ck_flag_critic_reason'), 'flag',
+                               f"critic_reason IS NULL OR (critic_class IS NOT NULL "
+                               f"AND length(btrim(critic_reason)) BETWEEN 1 AND {CRITIC_REASON_MAX})")
+    for f in FUNCTIONS:
+        op.execute(f)
+    for t in TRIGGERS:
+        op.execute(t)
+
+
+IN_USE = """
+    DO $$
+    BEGIN
+        IF EXISTS (SELECT 1 FROM hypothesis_version WHERE sufficiency_option <> 'fixed_minimum') THEN
+            RAISE EXCEPTION 'hypocurate: migration 0006 is in use (a query uses another sufficiency option); not downgraded';
+        END IF;
+    END $$
+"""
+
+
+def downgrade() -> None:
+    op.execute(IN_USE)
+    for table, _, t, _ in CHECKED:
+        op.execute(f"DROP TRIGGER {t} ON {table}")
+    for f in FUNCTION_NAMES:
+        op.execute(f"DROP FUNCTION {f}")
+    op.drop_constraint(op.f('ck_flag_critic_reason'), 'flag', type_='check')
+    op.drop_constraint(op.f('ck_flag_critic_class'), 'flag', type_='check')
+    op.drop_constraint(op.f('ck_hypothesis_version_sufficiency_option'), 'hypothesis_version', type_='check')
+    op.drop_column('hypothesis_version', 'sufficiency_option')
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index 3e0e554..615dab7 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -273,6 +273,10 @@ class Hypothesis(Base):
 VERSION_STATUSES = ("draft", "submitted", "returned", "dispatched")
 
 
+# The data-sufficiency options (PRD 5.8): of a query (step 8b, 0006) and of its locked plan (0001).
+SUFFICIENCY_OPTIONS = ("fixed_minimum", "use_available")
+
+
 class HypothesisVersion(Base):
     """Each edit is a new version. Frozen once it leaves draft, except the review
     fields; everything is frozen once returned or dispatched."""
@@ -291,6 +295,9 @@ class HypothesisVersion(Base):
     submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
     returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
     dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
+    # Step 8b (migration 0006; owner, A2): the query's data-sufficiency option, chosen before dispatch,
+    # fixed once submitted; the locked plan's option must equal it.
+    sufficiency_option: Mapped[str] = mapped_column(Text, server_default=sql("'fixed_minimum'"))
     __table_args__ = (
         UniqueConstraint("hypothesis_id", "version_number"),
         CheckConstraint(one_of("status", VERSION_STATUSES), name="status"),
@@ -302,6 +309,7 @@ class HypothesisVersion(Base):
                         name="dispatch_needs_confirmed_domain"),
         CheckConstraint("status = 'draft' OR submitted_at IS NOT NULL", name="submitted_time"),
         CheckConstraint("status <> 'returned' OR returned_at IS NOT NULL", name="returned_time"),
+        CheckConstraint(one_of("sufficiency_option", SUFFICIENCY_OPTIONS), name="sufficiency_option"),
     )
 
 
@@ -365,7 +373,6 @@ class Run(Base):
     )
 
 
-SUFFICIENCY_OPTIONS = ("fixed_minimum", "use_available")
 
 
 class Plan(Base):
@@ -718,6 +725,13 @@ class AnalysisSetRecord(Base):
     record_id: Mapped[int] = mapped_column(ForeignKey("record.id"), primary_key=True)
 
 
+# The Critic's classes and the bound on its reason (step 8b, migration 0006; owner, A7). The same codes as
+# `access.vocabulary.CRITIC_CLASSES` (tests/test_migrations_step8b.py checks that they are equal).
+CRITIC_CLASSES = ("cannot_tell", "different_specimens_or_conditions", "possible_transcription_or_unit_error",
+                  "same_measurement")
+CRITIC_REASON_MAX = 300
+
+
 class Flag(Base):
     """A flag raised by code. `compared_values` is kept for audit; the access layer
     (step 5) never returns it to the Critic. The Critic's class is set once, before the freeze."""
@@ -733,6 +747,11 @@ class Flag(Base):
     classified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
     __table_args__ = (
         CheckConstraint("(critic_class IS NULL) = (classified_at IS NULL)", name="classified_time"),
+        # Step 8b (migration 0006; owner, A7): the class from the Critic's fixed list; the reason, shown to
+        # people only, bounded and only with a class.
+        CheckConstraint(f"critic_class IS NULL OR {one_of('critic_class', CRITIC_CLASSES)}", name="critic_class"),
+        CheckConstraint(f"critic_reason IS NULL OR (critic_class IS NOT NULL "
+                        f"AND length(btrim(critic_reason)) BETWEEN 1 AND {CRITIC_REASON_MAX})", name="critic_reason"),
     )
 
 
diff --git a/hypocurate/pipeline/agents/analyst.py b/hypocurate/pipeline/agents/analyst.py
new file mode 100644
index 0000000..7e9738b
--- /dev/null
+++ b/hypocurate/pipeline/agents/analyst.py
@@ -0,0 +1,134 @@
+"""The Analyst (step 8b; PRD 3 step 8, 5.7; owner, Q6, A3, B2; register 'analyst_facts').
+
+The Analyst explains a result code has already computed. It reads its access list (claim, domain,
+sources_meta, coverage, analyst_facts) at 'analysis', 'closed_without_freeze' or 'narrowed': code's stored
+facts only, and below the minimums nothing computed from outcome values. It answers plain text, at most
+the role's character limit.
+
+The Analyst writes no digits (owner, 2026-10-07): every number, p-value, set of paper figures, the outcome and the
+verdict are {name} placeholders of its named facts (`pipeline.analyst_names`), and code renders the finished text
+(`text_checks.render`). Code checks the template (every name given, no digit outside a placeholder, the outcome and
+verdict wordings used) and then the finished text (the wording rules; every number is one of the facts); each
+failure is corrected once with a note naming only the code. A text that fails twice is discarded (never stored as
+the report); the stage keeps counts or rule names, never text. The finished text and its template are stored. The
+Analyst never sets the outcome, the verdict, the label or the level: the copy paths copy code's stored
+decision. If the Analyst fails for any reason (its checks, the provider, a spending refusal), the run still
+completes with code's decision and shows "explanation unavailable" (A3, B2).
+"""
+from __future__ import annotations
+
+import json
+from dataclasses import dataclass
+from typing import Any, Mapping
+
+from hypocurate.pipeline.agents import libraries, text_checks
+
+UNAVAILABLE = "explanation unavailable"
+OUTPUT_DESCRIPTION = ("The explanation, in plain text, a few short paragraphs. No digits: every number, p-value, set of "
+                      "paper figures, the outcome and the verdict are written as {name} placeholders from 'facts'.")
+
+
+def signature(instruction: str):
+    _, dspy = libraries.load()
+
+    class AnalystSignature(dspy.Signature):
+        claim: str = dspy.InputField(desc="The claim in words (its numbers are given as facts too, by name).")
+        facts: str = dspy.InputField(desc="The named facts, as JSON {name: value}: refer to each as {name}.")
+        context: str = dspy.InputField(desc="The domain and the chosen sources, as JSON.")
+        note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
+        report: str = dspy.OutputField(desc=OUTPUT_DESCRIPTION)
+
+    return AnalystSignature.with_instructions(instruction)
+
+
+def render_inputs(analyst_input: Mapping[str, Any]) -> dict[str, str]:
+    """The Analyst's request inputs, built only from its complete access-layer input: the claim, the named facts,
+    and the domain and sources (the coverage's numbers reach it as named facts only)."""
+    claim = {k: v for k, v in analyst_input["claim"].items() if k in ("text", "narrower_question")}
+    return {"claim": json.dumps(claim, sort_keys=True, ensure_ascii=False),
+            "facts": json.dumps(analyst_input["analyst_facts"]["names"], sort_keys=True, ensure_ascii=False),
+            "context": json.dumps({"domain": analyst_input["domain"],
+                                   "sources": [{k: s.get(k) for k in ("key", "name", "grouping_unit")}
+                                               for s in analyst_input["sources_meta"]]},
+                                  sort_keys=True, ensure_ascii=False)}
+
+
+def make_check(analyst_input: Mapping[str, Any]):
+    """The common interface's check: None, 'empty', 'unknown_name', 'digit_outside_placeholder', 'wording_refused'
+    or 'numbers_unmatched'. `check.last_problems` holds counts or rule names, never text; `check.rendered` the
+    finished text of an accepted answer."""
+    names = analyst_input["analyst_facts"]["names"]
+    decision = {"outcome_wording": names.get("outcome_wording"), "verdict": "verdict_wording" in names,
+                "verdict_wording": names.get("verdict_wording")}
+
+    def check(outputs: Mapping[str, str]) -> str | None:
+        check.last_problems, check.rendered = [], None
+        template = outputs["report"].strip()
+        if not template:
+            return "empty"
+        counts = text_checks.placeholder_problems(template, names)
+        if counts["unknown_names"]:
+            check.last_problems = [counts]
+            return "unknown_name"
+        if counts["digits_outside_placeholders"]:
+            check.last_problems = [counts]
+            return "digit_outside_placeholder"
+        if counts["required_missing"]:
+            check.last_problems = [counts]
+            return "wording_refused"
+        if counts["result_phrases_missing"]:
+            check.last_problems = [counts]
+            return "result_phrases_missing"
+        report = text_checks.render(template, names)
+        problems = text_checks.wording_problems(report, decision, names)
+        if problems:
+            check.last_problems = problems  # the names of the rules (fixed wording, or a listed phrase)
+            return "wording_refused"
+        if text_checks.unmatched_numbers(report, names):  # a safeguard: every number came from a name
+            check.last_problems = ["numbers_unmatched"]
+            return "numbers_unmatched"
+        check.rendered = report
+        return None
+
+    check.last_problems, check.rendered = [], None
+    return check
+
+
+@dataclass(frozen=True)
+class AnalystResult:
+    report: str | None
+    failure: str | None
+    stage_id: int
+    calls: list
+
+
+def run_analyst(engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> AnalystResult:
+    """The Analyst's stage. On any failure the stage is closed 'failed' with the code and no text."""
+    from hypocurate.access.dispatch import bind_invocation
+    from hypocurate.access.inputs import role_input
+    from hypocurate.pipeline.agents.interface import call_agent
+    from hypocurate.pipeline.agents.runstage import close_stage, open_stage
+    from hypocurate.pipeline.agents.settings import SETTINGS
+
+    stage_id, invocation = open_stage(engine, run_id, "analyst", "analyst")
+    data = role_input(bind_invocation(engine, invocation))
+    s = SETTINGS["analyst"]
+    inputs = render_inputs(data)
+    check = make_check(data)
+    result = call_agent(engine, invocation, signature(s["instruction"]), inputs, model=s["model"],
+                        max_tokens=s["limits"]["max_tokens"], max_output_chars=s["limits"]["max_output_chars"],
+                        ceiling=ceiling, lm_options=dict(s["settings"]), client_options=client_options,
+                        check=check)
+    if result.failure is not None:
+        close_stage(engine, run_id, stage_id, "failed", {"code": result.failure, "attempts": result.attempts,
+                                                         "failure_details": result.details,
+                                                         "shown": f"{UNAVAILABLE} ({result.failure})"}, input_=inputs)
+        return AnalystResult(None, result.failure, stage_id, result.calls)
+    report = check.rendered
+    close_stage(engine, run_id, stage_id, "done", {"report": report, "template": result.outputs["report"].strip(),
+                                                   "attempts": result.attempts,
+                                                   # owner, 2026-10-07: also for an attempt later corrected
+                                                   "failure_details": result.details,
+                                                   "check": "numbers written by code from the run record"},
+                input_=inputs)
+    return AnalystResult(report, None, stage_id, result.calls)
diff --git a/hypocurate/pipeline/agents/critic.py b/hypocurate/pipeline/agents/critic.py
new file mode 100644
index 0000000..41bc805
--- /dev/null
+++ b/hypocurate/pipeline/agents/critic.py
@@ -0,0 +1,180 @@
+"""The Critic (step 8b; PRD 3 step 6, 4; owner, A7; register 'critic_classes').
+
+Between the rules lock and the dataset freeze, after Checks, the Critic classifies the flags code raised.
+It reads its access list at 'curation' (sources_meta, record_metadata, flags_kind): each flag's kind,
+category and record ids, never the numbers compared. The request carries only the metadata of the records
+the flags name. Flags are sent in batches of at most `max_flags_per_call` (each batch its own stage result,
+invocation and call).
+
+The answer: one JSON object, one key per flag id (as text), each {"class": <code>, "reason": <text>}. Code
+checks each entry: the flag is one of the batch's, the class is one of `CRITIC_CLASSES`, the reason is
+1 to 300 characters (never truncated). An entry that fails is left unclassified with its refusal code, and
+the others stand (no retry). An answer that is not a JSON object is malformed (corrected once).
+
+**No code decision reads the class** (owner's standing requirement): Inclusion, the freeze, Statistics,
+the narrowing and completion read flags only through `flags_kind` and `set_flags`, which carry no class;
+`tests/test_critic.py` changes every class and finds every decision, set, fingerprint and result
+unchanged. The class and reason are shown to people only (A7).
+"""
+from __future__ import annotations
+
+import json
+import re
+from dataclasses import dataclass, field
+from typing import Any, Mapping
+
+from sqlalchemy import Connection, Engine, text
+
+from hypocurate.access.vocabulary import CRITIC_CLASSES, CRITIC_REASON_MAX
+from hypocurate.pipeline.agents import libraries
+from hypocurate.pipeline.writes import Refused, write
+
+_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.S)
+OUTPUT_DESCRIPTION = ('One JSON object with one key per flag id (as text); each value {"class": <one of the allowed '
+                      'classes>, "reason": "<at most 300 characters, from the metadata shown>"}. Nothing else.')
+
+
+def signature(instruction: str):
+    _, dspy = libraries.load()
+
+    class CriticSignature(dspy.Signature):
+        sources: str = dspy.InputField(desc="The chosen sources' descriptions, as JSON.")
+        flags: str = dspy.InputField(desc="The flags to classify, each with the metadata of the records it names.")
+        classes: str = dspy.InputField(desc="The allowed classes: code and meaning.")
+        note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
+        classification: str = dspy.OutputField(desc=OUTPUT_DESCRIPTION)
+
+    return CriticSignature.with_instructions(instruction)
+
+
+def batches(critic_input: Mapping[str, Any], size: int) -> list[list[Mapping]]:
+    flags = list(critic_input["flags_kind"])
+    return [flags[i:i + size] for i in range(0, len(flags), size)]
+
+
+def render_inputs(critic_input: Mapping[str, Any], batch: list[Mapping]) -> dict[str, str]:
+    """The Critic's request inputs for one batch, built only from its access-layer input."""
+    named = {r for f in batch for r in f["records"]}
+    meta = {r["id"]: r for r in critic_input["record_metadata"] if r["id"] in named}
+    flags = [{"id": str(f["id"]), "kind": f["kind"], "category": f["category"],
+              "records": [meta[r] for r in f["records"] if r in meta]} for f in batch]
+    return {"sources": json.dumps(critic_input["sources_meta"], sort_keys=True, ensure_ascii=False),
+            "flags": json.dumps(flags, sort_keys=True, ensure_ascii=False),
+            "classes": json.dumps(dict(CRITIC_CLASSES), sort_keys=True, ensure_ascii=False)}
+
+
+def parse(text_: str) -> dict | None:
+    body = text_.strip()
+    fenced = _FENCE.match(body)
+    if fenced:
+        body = fenced.group(1)
+    try:
+        value = json.loads(body)
+    except ValueError:
+        return None
+    return value if isinstance(value, dict) else None
+
+
+def check(outputs: Mapping[str, str]) -> str | None:
+    return None if parse(outputs["classification"]) is not None else "malformed"
+
+
+@dataclass
+class Classified:
+    accepted: dict[int, tuple[str, str | None]] = field(default_factory=dict)
+    refused: dict[str, str] = field(default_factory=dict)  # flag id (as given) -> code
+
+
+def classify(data: Mapping, batch: list[Mapping]) -> Classified:
+    """Code's check of each entry (see the module docstring)."""
+    ids = {str(f["id"]): f["id"] for f in batch}
+    out = Classified()
+    for key, entry in data.items():
+        if key not in ids:
+            out.refused[str(key)[:40]] = "unknown_flag"
+            continue
+        if not isinstance(entry, dict) or set(entry) - {"class", "reason"} or "class" not in entry:
+            out.refused[key] = "malformed_entry"
+        elif entry["class"] not in CRITIC_CLASSES:
+            out.refused[key] = "class_not_allowed"
+        elif entry.get("reason") is not None and not (isinstance(entry["reason"], str)
+                                                       and 1 <= len(entry["reason"].strip()) <= CRITIC_REASON_MAX):
+            out.refused[key] = "reason_not_allowed"
+        else:
+            reason = entry.get("reason")
+            out.accepted[ids[key]] = (entry["class"], reason.strip() if isinstance(reason, str) else None)
+    for key in ids:
+        if key not in data:
+            out.refused.setdefault(key, "not_answered")
+    return out
+
+
+def write_classes(engine: Engine, run_id: int, accepted: Mapping[int, tuple[str, str | None]]) -> int:
+    """Writes each accepted class once, before the freeze (0001: classified once, only before the freeze)."""
+
+    def body(conn: Connection, stage: str):
+        if stage != "curation":
+            raise Refused("write_classes", "stage_mismatch")
+        n = 0
+        for flag_id, (cls, reason) in sorted(accepted.items()):
+            n += conn.execute(text("UPDATE flag SET critic_class = :c, critic_reason = :r, classified_at = now() "
+                                   "WHERE id = :f AND run_id = :run AND critic_class IS NULL"),
+                              dict(c=cls, r=reason, f=flag_id, run=run_id)).rowcount
+        return n
+
+    return write(engine, run_id, "critic", "write_classes", body)
+
+
+@dataclass(frozen=True)
+class CriticResult:
+    classified: int
+    refused: dict
+    failures: list  # the failure code of each batch that failed
+    stages: list
+
+
+def run_critic(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> CriticResult:
+    """The Critic's stage(s). A failed batch leaves its flags unclassified; a spending refusal stops the
+    remaining batches (the orchestrator then fails the run, PRD 8)."""
+    from hypocurate.access.dispatch import bind_invocation
+    from hypocurate.access.inputs import role_input
+    from hypocurate.pipeline.agents.interface import call_agent
+    from hypocurate.pipeline.agents.runstage import close_stage, open_stage
+    from hypocurate.pipeline.agents.settings import SETTINGS
+
+    s = SETTINGS["critic"]
+    classified, refused, failures, stages = 0, {}, [], []
+    data = None
+    plan_batches = None
+    while True:
+        stage_id, invocation = open_stage(engine, run_id, "critic", "critic")
+        stages.append(stage_id)
+        current = role_input(bind_invocation(engine, invocation))
+        if plan_batches is None:
+            data, plan_batches = current, batches(current, s["limits"]["max_flags_per_call"])
+        batch = plan_batches.pop(0) if plan_batches else []
+        if not batch:
+            close_stage(engine, run_id, stage_id, "skipped", {"reason": "no_flags"})
+            break
+        inputs = render_inputs(current, batch)
+        result = call_agent(engine, invocation, signature(s["instruction"]), inputs, model=s["model"],
+                            max_tokens=s["limits"]["max_tokens"], max_output_chars=s["limits"]["max_output_chars"],
+                            ceiling=ceiling, lm_options=dict(s["settings"]), client_options=client_options,
+                            check=check)
+        if result.failure is not None:
+            failures.append(result.failure)
+            refused.update({str(f["id"]): result.failure for f in batch})
+            close_stage(engine, run_id, stage_id, "failed", {"code": result.failure, "attempts": result.attempts,
+                                                             "flags": [f["id"] for f in batch]}, input_=inputs)
+            if result.failure.startswith("spending_cap") or result.failure == "ceiling_reached":
+                break
+        else:
+            got = classify(parse(result.outputs["classification"]), batch)
+            classified += write_classes(engine, run_id, got.accepted)
+            refused.update(got.refused)
+            close_stage(engine, run_id, stage_id, "done", {
+                "classified": {str(k): {"class": c, "reason": r} for k, (c, r) in sorted(got.accepted.items())},
+                "refused": got.refused, "attempts": result.attempts}, input_=inputs)
+        if not plan_batches:
+            break
+    return CriticResult(classified, refused, failures, stages)
diff --git a/hypocurate/pipeline/agents/interface.py b/hypocurate/pipeline/agents/interface.py
index ada7a49..014e217 100644
--- a/hypocurate/pipeline/agents/interface.py
+++ b/hypocurate/pipeline/agents/interface.py
@@ -14,6 +14,7 @@
 """
 from __future__ import annotations
 
+import re
 from dataclasses import dataclass, field
 from decimal import Decimal
 from typing import Any, Mapping
@@ -37,6 +38,20 @@ class AgentResult:
     failure: str | None
     attempts: list[str] = field(default_factory=list)  # one entry per request: "ok" or a failure code
     calls: list[int] = field(default_factory=list)       # the recorded model calls
+    # Step 8b (owner, 2026-10-07): per failed attempt, fixed facts about the answer's form, never its text.
+    details: list[dict] = field(default_factory=list)
+
+
+def parse_failure_facts(error: BaseException, signature) -> dict | None:
+    """For an answer DSPy could not parse: whether each output field's header and the closing marker were present,
+    and how many field headers there were. Booleans and a count only: none of the answer's text."""
+    response = getattr(error, "lm_response", None)
+    if not isinstance(response, str):
+        return None
+    headers = re.findall(r"\[\[ ## (\w+) ## \]\]", response)
+    return {"output_headers_present": {name: name in headers for name in signature.output_fields},
+            "completed_marker": "completed" in headers, "header_count": len(headers),
+            "answer_empty": not response.strip()}
 
 
 def call_agent(db, invocation_id: int, signature, inputs: Mapping[str, str], *, model: str, max_tokens: int,
@@ -59,11 +74,16 @@ def call_agent(db, invocation_id: int, signature, inputs: Mapping[str, str], *,
             try:
                 with dspy.context(lm=lm, adapter=adapter):
                     prediction = dspy.Predict(signature)(**inputs, note=note)
-            except Exception:  # noqa: BLE001 (classified by code; nothing of it is kept here)
+            except Exception as error:  # noqa: BLE001 (classified by code; nothing of its text is kept here)
                 code = engine.last_failure or "malformed"
+                facts = parse_failure_facts(error, signature) if code == "malformed" else None
+                if facts is not None:
+                    result.details.append({"attempt": len(result.attempts) + 1, "parse": facts})
             else:
                 outputs = {name: str(getattr(prediction, name)) for name in signature.output_fields}
                 code = check(outputs) if check is not None else None
+                if code is not None and getattr(check, "last_problems", None):
+                    result.details.append({"attempt": len(result.attempts) + 1, "problems": list(check.last_problems)})
                 if code is None:
                     result.attempts.append("ok")
                     result.outputs, result.failure = outputs, None
diff --git a/hypocurate/pipeline/agents/lm.py b/hypocurate/pipeline/agents/lm.py
index d6d5d81..00a1241 100644
--- a/hypocurate/pipeline/agents/lm.py
+++ b/hypocurate/pipeline/agents/lm.py
@@ -57,6 +57,14 @@ FAILURES: Mapping[str, tuple[str, str]] = {
     "spending_cap_month": ("the monthly spending cap would be exceeded", "stop"),
     "ceiling_reached": ("the ceiling set for this call would be exceeded", "stop"),
     "invocation_unknown": ("no such invocation", "stop"),
+    # Step 8b: the roles' own checks of an answer that could be read (each corrected once).
+    "invalid_plan": ("the plan is not valid for the supported template or does not match the claim's scope", "correct"),
+    "numbers_unmatched": ("a number in the text is not one of the facts given, as given", "correct"),
+    "wording_refused": ("the text uses wording that is not allowed", "correct"),
+    # Owner, 2026-10-07: the Analyst's placeholders.
+    "unknown_name": ("a placeholder names no fact given", "correct"),
+    "digit_outside_placeholder": ("a digit was written outside a placeholder; every number is a placeholder", "correct"),
+    "result_phrases_missing": ("with a verdict, the pooled p-value phrase and paper-figures phrase must be used", "correct"),
 }
 
 
diff --git a/hypocurate/pipeline/agents/planner.py b/hypocurate/pipeline/agents/planner.py
new file mode 100644
index 0000000..ec062d6
--- /dev/null
+++ b/hypocurate/pipeline/agents/planner.py
@@ -0,0 +1,306 @@
+"""The Planner (step 8b; PRD 3 step 3, 5.1, 5.4; owner's answers Q5, A11; register 'planner_answer').
+
+The Planner reads the claim, the domain, the chosen sources' descriptions, the approved tag values and the
+record counts (its access list at 'before_lock'; never an outcome value). It answers one JSON object:
+
+    {"domain_matches": true | false,
+     "claim_scope": {"alloy_class": [...], "phase_class": [...], "test_type": [...],
+                     "temperature_band": [{"band": "room temperature"} | {"band": "elevated" | "cryogenic",
+                                                                          "min": <°C>, "max": <°C>}, ...]},
+     "stated": {"alloy_class": true | false, "phase_class": ..., "test_type": ..., "temperature_band": ...},
+     "outcome": "yield_strength",
+     "exclusion_rules": [{"rule": <menu>, "min": <n>, "max": <n>, "values": [...]}, ...],
+     "narrower": null | {"phase_class": [...], "test_type": [...], "temperature_band": [...]}}
+
+Every value comes from a fixed list; there is no free text and no other key. **Code decides** (CLAUDE.md,
+rule 1): `check` refuses an answer whose shape, values or plan are not valid (`invalid_plan`, corrected once
+by the common interface); `build_plan` makes the plan from the profile's defaults and only these
+parameters: the model, the rules, the eligibility rules, the calibration and the data-sufficiency option
+never come from the model (the option is the query's, A2). The plan's scope is the claim's scope; a claim
+that is not one plan (more than one alloy class, temperature band or test type, A11) gets no plan here,
+and the narrowing decision (`pipeline.narrowing`) decides what happens. Code builds any narrower scope from its
+own counts (owner, 2026-10-07, after live run C); a narrower scope the Planner gives anyway is checked for its
+shape, stored, and never used.
+"""
+from __future__ import annotations
+
+import json
+import math
+import re
+from dataclasses import dataclass
+from typing import Any, Mapping
+
+from hypocurate.access.allowlist import ALLOY_CLASSES, EXCLUSION_RULES
+from hypocurate.access.vocabulary import PHASE_CLASSES, TEST_TYPES
+from hypocurate.pipeline import plan as plans
+from hypocurate.pipeline import profile as p
+from hypocurate.pipeline.agents import libraries
+from hypocurate.pipeline.eligibility import SUPPORTED_OUTCOMES
+
+KEYS = {"domain_matches", "claim_scope", "stated", "outcome", "exclusion_rules", "narrower"}
+SCOPE_KEYS = {"alloy_class", "phase_class", "test_type", "temperature_band"}
+NARROWER_KEYS = {"phase_class", "test_type", "temperature_band"}  # alloy class is not countable (Q5)
+BANDS = tuple(p.SUPPORTED_BANDS)
+CATEGORY_RULE_VALUES = {"phase": sorted(PHASE_CLASSES), "test_type": sorted(TEST_TYPES)}
+_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.S)
+
+OUTPUT_DESCRIPTION = ("One JSON object with exactly the keys domain_matches, claim_scope, outcome, exclusion_rules "
+                      "and narrower, in the form and with the values given in 'allowed'. Nothing else.")
+
+
+def signature(instruction: str):
+    _, dspy = libraries.load()
+
+    class PlannerSignature(dspy.Signature):
+        claim: str = dspy.InputField(desc="The claim in words, with its query number.")
+        domain: str = dspy.InputField(desc="The query's confirmed domain.")
+        sources: str = dspy.InputField(desc="The chosen sources' descriptions, as JSON.")
+        counts: str = dspy.InputField(desc="Counts of each source's records by field status and category value.")
+        allowed: str = dspy.InputField(desc="The answer's form, the allowed values and the defaults, as JSON.")
+        note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
+        plan: str = dspy.OutputField(desc=OUTPUT_DESCRIPTION)
+
+    return PlannerSignature.with_instructions(instruction)
+
+
+def allowed_values(tag_values: list[Mapping]) -> dict:
+    """The answer's form and allowed values, built by code from the vocabularies, the approved tag values
+    and the profile's defaults (no run data)."""
+    approved = sorted(t["value"] for t in tag_values if t.get("kind") == "alloy_class")
+    return {
+        "form": {"domain_matches": "true or false",
+                 "claim_scope": {"alloy_class": "list", "phase_class": "list", "test_type": "list",
+                                 "temperature_band": "list of {band} or {band, min, max} in °C"},
+                 "stated": {"alloy_class": "true if the claim states it, false if you used the default",
+                            "phase_class": "true or false", "test_type": "true or false",
+                            "temperature_band": "true or false"},
+                 "outcome": "one value", "exclusion_rules": "list of {rule, min?, max?, values?}",
+                 "narrower": "null (code decides any narrower scope from its own counts)"},
+        "alloy_class": [a for a in approved if a in ALLOY_CLASSES],
+        "phase_class": sorted(PHASE_CLASSES - {"other"}),
+        "test_type": sorted(TEST_TYPES),
+        "temperature_band": list(BANDS),
+        "room_temperature_c": list(p.ROOM_TEMPERATURE_C),
+        "outcome": list(SUPPORTED_OUTCOMES),
+        "exclusion_rule_menu": {"grain_size_range": "min and/or max in µm", "temperature_range": "min and/or max in °C",
+                                "phase": CATEGORY_RULE_VALUES["phase"], "test_type": CATEGORY_RULE_VALUES["test_type"]},
+        "defaults": {"alloy_class": list(p.ALLOY_CLASSES), "phase_class": list(p.PHASE_CLASSES),
+                     "test_type": list(p.PERMITTED_TEST_TYPES), "temperature_band": [{"band": "room temperature"}],
+                     "outcome": p.OUTCOME[0],
+                     "exclusion_rules": [{"rule": "grain_size_range", "min": float(p.GRAIN_SIZE_FLOOR_UM)}]},
+    }
+
+
+def render_inputs(planner_input: Mapping[str, Any]) -> dict[str, str]:
+    """The Planner's request inputs, built only from its complete access-layer input and code's lists."""
+    c = planner_input["claim"]
+    return {"claim": json.dumps(c, sort_keys=True, ensure_ascii=False),
+            "domain": json.dumps(planner_input["domain"], sort_keys=True, ensure_ascii=False),
+            "sources": json.dumps(planner_input["sources_meta"], sort_keys=True, ensure_ascii=False),
+            "counts": json.dumps(planner_input["record_counts"], sort_keys=True, ensure_ascii=False),
+            "allowed": json.dumps(allowed_values(planner_input["tag_values"]), sort_keys=True, ensure_ascii=False)}
+
+
+def parse(text: str) -> dict | None:
+    body = text.strip()
+    fenced = _FENCE.match(body)
+    if fenced:
+        body = fenced.group(1)
+    try:
+        value = json.loads(body)
+    except ValueError:
+        return None
+    return value if isinstance(value, dict) else None
+
+
+# --- The answer's shape ------------------------------------------------------------------------------
+
+class AnswerInvalid(ValueError):
+    pass
+
+
+def _number(v) -> bool:
+    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
+
+
+def _values(v, allowed, what) -> list:
+    if not isinstance(v, list) or not v or not all(isinstance(x, str) for x in v) or len(set(v)) != len(v) \
+            or not all(x in allowed for x in v):
+        raise AnswerInvalid(f"{what}: a non-empty list of distinct allowed values")
+    return list(v)
+
+
+def _bands(v) -> list[dict]:
+    if not isinstance(v, list) or not v:
+        raise AnswerInvalid("temperature_band: a non-empty list")
+    out, seen = [], set()
+    for b in v:
+        if not isinstance(b, dict) or b.get("band") not in BANDS:
+            raise AnswerInvalid("temperature_band: each {band} from the list")
+        if b["band"] == plans.ROOM_TEMPERATURE:
+            if set(b) != {"band"}:
+                raise AnswerInvalid("room temperature takes no range")
+            band = {"band": b["band"]}
+        else:
+            if set(b) != {"band", "min", "max"} or not (_number(b["min"]) and _number(b["max"])) or b["min"] > b["max"]:
+                raise AnswerInvalid("an elevated or cryogenic band names its range, min not above max")
+            band = {"band": b["band"], "min": float(b["min"]), "max": float(b["max"])}
+        if band["band"] in seen:
+            raise AnswerInvalid("each band once")
+        seen.add(band["band"])
+        out.append(band)
+    return out
+
+
+def _exclusions(v) -> list[dict]:
+    if not isinstance(v, list):
+        raise AnswerInvalid("exclusion_rules: a list")
+    out = []
+    for e in v:
+        if not isinstance(e, dict) or e.get("rule") not in EXCLUSION_RULES:
+            raise AnswerInvalid("an exclusion rule comes from the menu")
+        if e["rule"] in ("grain_size_range", "temperature_range"):
+            if not set(e) - {"rule"} or set(e) - {"rule", "min", "max"} or not all(_number(e[k]) for k in e if k != "rule"):
+                raise AnswerInvalid("a range rule names a minimum and/or maximum")
+            out.append({k: (float(x) if k != "rule" else x) for k, x in e.items()})
+        else:
+            if set(e) != {"rule", "values"}:
+                raise AnswerInvalid("a phase or test-type rule names its values")
+            out.append({"rule": e["rule"], "values": _values(e["values"], CATEGORY_RULE_VALUES[e["rule"]], e["rule"])})
+    return out
+
+
+def _scope(v, keys) -> dict:
+    if not isinstance(v, dict) or set(v) != keys:
+        raise AnswerInvalid(f"a scope has exactly {', '.join(sorted(keys))}")
+    out = {"phase_class": _values(v["phase_class"], PHASE_CLASSES - {"other"}, "phase_class"),
+           "test_type": _values(v["test_type"], TEST_TYPES, "test_type"),
+           "temperature_band": _bands(v["temperature_band"])}
+    if "alloy_class" in keys:
+        out["alloy_class"] = _values(v["alloy_class"], ALLOY_CLASSES, "alloy_class")
+    return out
+
+
+@dataclass(frozen=True)
+class Answer:
+    domain_matches: bool
+    claim_scope: dict
+    outcome: str
+    exclusion_rules: list
+    narrower: dict | None
+    stated: dict  # owner, 2026-10-07: per scope part, stated by the claim (True) or the Planner's default (False)
+
+
+def read_answer(data: Mapping) -> Answer:
+    if set(data) != KEYS:
+        raise AnswerInvalid("the answer has exactly the keys " + ", ".join(sorted(KEYS)))
+    if not isinstance(data["domain_matches"], bool):
+        raise AnswerInvalid("domain_matches is true or false")
+    if data["outcome"] not in SUPPORTED_OUTCOMES:
+        raise AnswerInvalid("the outcome comes from the list")
+    narrower = None if data["narrower"] is None else _scope(data["narrower"], NARROWER_KEYS)
+    stated = data["stated"]
+    if not isinstance(stated, dict) or set(stated) != SCOPE_KEYS or not all(isinstance(v, bool) for v in stated.values()):
+        raise AnswerInvalid("'stated' marks each scope part true (stated by the claim) or false (defaulted)")
+    return Answer(data["domain_matches"], _scope(data["claim_scope"], SCOPE_KEYS), data["outcome"],
+                  _exclusions(data["exclusion_rules"]), narrower, dict(sorted(stated.items())))
+
+
+# --- The plan, built by code -------------------------------------------------------------------------
+
+def one_plan(scope: Mapping) -> bool:
+    """Owner, A11: one alloy class, one temperature band and one test type make one plan (its three tags)."""
+    return len(scope.get("alloy_class", [None])) == 1 and len(scope["temperature_band"]) == 1 \
+        and len(scope["test_type"]) == 1
+
+
+def build_plan(hypothesis_version_id: int, scope: Mapping, outcome: str, exclusion_rules: list,
+               sufficiency_option: str, alloy_class: list | None = None) -> dict:
+    """The plan for a one-plan scope: the profile's default plan with only these parameters set. Raises
+    PlanError if the result is not valid."""
+    plan = plans.default_plan(hypothesis_version_id)
+    band = scope["temperature_band"][0]
+    plan["scope"] = {"alloy_class": list(alloy_class or scope["alloy_class"]), "temperature_band": [band["band"]],
+                     "test_type": list(scope["test_type"]), "phase_class": list(scope["phase_class"])}
+    plan["variables"]["outcome"] = {"field": outcome, "unit": "MPa"}
+    plan["exclusion_rules"] = [dict(e) for e in exclusion_rules]
+    plan["sufficiency"]["option"] = sufficiency_option
+    if band["band"] != plans.ROOM_TEMPERATURE:
+        plan["rules"][plans.RANGE_RULE] = {"min": band["min"], "max": band["max"]}
+    plans.validate(plan)
+    plans.tags_for(plan)
+    return plan
+
+
+def plan_without_version(plan: Mapping) -> dict:
+    """A plan less its hypothesis version (A8: the narrower question's run adds its own)."""
+    return {k: v for k, v in plan.items() if k != "hypothesis_version"}
+
+
+def make_check(hypothesis_version_id: int, sufficiency_option: str, approved_alloy_classes: set[str]):
+    """The common interface's check of a Planner answer: None, 'malformed' or 'invalid_plan'."""
+
+    def check(outputs: Mapping[str, str]) -> str | None:
+        data = parse(outputs["plan"])
+        if data is None:
+            return "malformed"
+        try:
+            answer = read_answer(data)
+            if not answer.domain_matches:
+                return None  # a valid answer: the run stops before the lock (PRD 5.5)
+            if not set(answer.claim_scope["alloy_class"]) <= approved_alloy_classes:
+                raise AnswerInvalid("an alloy class is not an approved tag value")
+            if one_plan(answer.claim_scope):
+                build_plan(hypothesis_version_id, answer.claim_scope, answer.outcome, answer.exclusion_rules,
+                           sufficiency_option)
+        except (AnswerInvalid, plans.PlanError):
+            return "invalid_plan"
+        return None
+
+    return check
+
+
+# --- One Planner call within a run --------------------------------------------------------------------
+
+@dataclass(frozen=True)
+class PlannerResult:
+    answer: Answer | None
+    failure: str | None
+    stage_id: int
+    invocation_id: int
+    calls: list
+
+
+def run_planner(engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> PlannerResult:
+    """The Planner's stage: opened (stage result and invocation) before the request, its input read through the
+    access layer, one agent call through the common interface, the answer checked by code, the stage closed
+    with the checked answer or the failure code. No model call runs inside a database transaction."""
+    from sqlalchemy import text
+    from hypocurate.access.dispatch import bind_invocation
+    from hypocurate.access.inputs import role_input
+    from hypocurate.pipeline.agents.interface import call_agent
+    from hypocurate.pipeline.agents.runstage import close_stage, open_stage
+    from hypocurate.pipeline.agents.settings import SETTINGS
+
+    stage_id, invocation = open_stage(engine, run_id, "planner", "planner")
+    data = role_input(bind_invocation(engine, invocation))
+    with engine.connect() as conn:
+        row = conn.execute(text("SELECT r.hypothesis_version_id, hv.sufficiency_option FROM run r JOIN "
+                                "hypothesis_version hv ON hv.id = r.hypothesis_version_id WHERE r.id = :r"),
+                           dict(r=run_id)).one()
+    approved = {t["value"] for t in data["tag_values"] if t.get("kind") == "alloy_class"}
+    s = SETTINGS["planner"]
+    inputs = render_inputs(data)
+    result = call_agent(engine, invocation, signature(s["instruction"]), inputs, model=s["model"],
+                        max_tokens=s["limits"]["max_tokens"], max_output_chars=s["limits"]["max_output_chars"],
+                        ceiling=ceiling, lm_options=dict(s["settings"]), client_options=client_options,
+                        check=make_check(row.hypothesis_version_id, row.sufficiency_option, approved))
+    if result.failure is not None:
+        close_stage(engine, run_id, stage_id, "failed", {"code": result.failure, "attempts": result.attempts},
+                    input_=inputs)
+        return PlannerResult(None, result.failure, stage_id, invocation, result.calls)
+    answer = read_answer(parse(result.outputs["plan"]))
+    close_stage(engine, run_id, stage_id, "done", {"answer": answer.__dict__, "attempts": result.attempts},
+                input_=inputs)
+    return PlannerResult(answer, None, stage_id, invocation, result.calls)
+
diff --git a/hypocurate/pipeline/agents/runstage.py b/hypocurate/pipeline/agents/runstage.py
new file mode 100644
index 0000000..4da393a
--- /dev/null
+++ b/hypocurate/pipeline/agents/runstage.py
@@ -0,0 +1,53 @@
+"""An agent's stage within a run (step 8b): opened before any request, closed after the answer is checked.
+
+`open_stage` writes, in one short transaction under the run's lock (the locking protocol), a running
+stage result for the role and the one invocation record of the agent call (0005: the invocation names
+the run, the stage and the role, and its setting is the one the run recorded at dispatch). It commits
+before the access read and before any request, so no model call ever runs inside a database
+transaction (the request path's own transactions are in `spend`). `close_stage` writes the stage's
+output and its status ('done' or 'failed') in another locked transaction. Neither ever holds a
+transaction open across a request.
+"""
+from __future__ import annotations
+
+from typing import Any, Mapping
+
+from sqlalchemy import Connection, Engine, bindparam, text
+from sqlalchemy.dialects.postgresql import JSONB
+
+from hypocurate.pipeline.writes import Refused, write
+
+
+def open_stage(engine: Engine, run_id: int, role: str, stage: str) -> tuple[int, int]:
+    """(stage result id, invocation id) for one agent call of `role` at `stage` of the run."""
+
+    def body(conn: Connection, _actual: str):
+        row = conn.execute(text("SELECT ras.agent_setting_id, a.model FROM run_agent_setting ras JOIN agent_setting a "
+                                "ON a.id = ras.agent_setting_id WHERE ras.run_id = :r AND ras.role = :o"),
+                           dict(r=run_id, o=role)).one_or_none()
+        if row is None:
+            raise Refused(f"open_{role}", "stage_mismatch", "the role's settings were not recorded at dispatch")
+        sid = conn.execute(text(
+            "INSERT INTO stage_result (run_id, stage, attempt, role, agent_setting_id, model) VALUES (:r, :s, "
+            "(SELECT coalesce(max(attempt), 0) + 1 FROM stage_result WHERE run_id = :r AND stage = :s), :o, :a, :m) "
+            "RETURNING id"), dict(r=run_id, s=stage, o=role, a=row.agent_setting_id, m=row.model)).scalar_one()
+        inv = conn.execute(text("INSERT INTO agent_invocation (scope, run_id, stage_result_id, role, agent_setting_id) "
+                                "VALUES ('run', :r, :s, :o, :a) RETURNING id"),
+                           dict(r=run_id, s=sid, o=role, a=row.agent_setting_id)).scalar_one()
+        return sid, inv
+
+    return write(engine, run_id, role, f"open_{role}", body)
+
+
+def close_stage(engine: Engine, run_id: int, stage_id: int, status: str, output: Mapping[str, Any],
+                input_: Mapping[str, Any] | None = None) -> None:
+    """Writes the stage's output (and the input it was given, as stored facts) and its final status."""
+
+    def body(conn: Connection, _actual: str):
+        conn.execute(text("UPDATE stage_result SET status = :st, finished_at = now(), output = :o, input = :i "
+                          "WHERE id = :s AND run_id = :r").bindparams(bindparam("o", type_=JSONB),
+                                                                       bindparam("i", type_=JSONB)),
+                     dict(st=status, o=dict(output), i=dict(input_) if input_ is not None else None, s=stage_id,
+                          r=run_id))
+
+    write(engine, run_id, "agent", "close_stage", body)
diff --git a/hypocurate/pipeline/agents/settings.py b/hypocurate/pipeline/agents/settings.py
index 08c064a..c92f989 100644
--- a/hypocurate/pipeline/agents/settings.py
+++ b/hypocurate/pipeline/agents/settings.py
@@ -5,7 +5,8 @@ instruction, model, limits and role-specific settings) is stored as an `agent_se
 `ensure_setting` returns the version whose stored values equal these, or adds the next version. A run
 records the versions it uses at dispatch; a registration invocation names the Curator's.
 
-The Curator's settings are here (step 8a); the other roles' instructions come with them in step 8b.
+The Curator's settings are here (step 8a); the Planner's, the Critic's and the Analyst's from step 8b (drafts
+for the owner's review). `RUN_ROLES`: the roles a run records at dispatch (the Curator never runs in a run).
 """
 from __future__ import annotations
 
@@ -23,6 +24,8 @@ MODELS = MappingProxyType({
     "analyst": "claude-opus-5-5",
 })
 
+RUN_ROLES = ("planner", "critic", "analyst")
+
 CURATOR_INSTRUCTION = (
     "You read the documentation of one scientific data source. For each field named in the targets, decide "
     "whether the documentation explicitly states one value of that field that holds for all of the source's "
@@ -32,7 +35,57 @@ CURATOR_INSTRUCTION = (
     "explicitly, answer \"not stated\" for that field. Do not infer, estimate or generalize, and do not use "
     "anything you know from outside the documentation.")
 
+# Step 8b drafts (Claude Code, 2026-10-07; for the owner's review before the live set, B3). Each role
+# answers in text only; code checks every answer and decides everything (CLAUDE.md, rule 1).
+PLANNER_INSTRUCTION = (
+    "You read a scientific claim about grain-size strengthening in metal alloys and fill the parameters of the one "
+    "supported test: yield strength = a baseline per alloy + k x (grain size)^-1/2. You see the claim, its domain, "
+    "the chosen sources' descriptions and counts of their records by field status and category value; you never "
+    "see measured values. Say whether the claim belongs to the domain. Give the claim's scope exactly as the claim "
+    "states it, using only the allowed values: its alloy classes, phase classes, test types and temperature bands "
+    "(room temperature, elevated or cryogenic; for elevated or cryogenic, the range in degrees Celsius that the "
+    "claim names). Where the claim does not state a part of the scope, use the default given, and in 'stated' "
+    "mark each part true if the claim states it and false if you used the default. Choose the outcome "
+    "field from the allowed list and exclusion rules only from the menu. Give null for 'narrower': code decides "
+    "any narrower scope from its own counts. Do not judge whether the claim is true.")
+CRITIC_INSTRUCTION = (
+    "You classify flags that code raised on records of a scientific data set. For each flag you are told its kind "
+    "and category and the metadata of the records it names (source, alloy and composition, paper DOI, field "
+    "statuses and conditions such as test type and phase); you are never told the numbers that were compared. "
+    "Classify each flag with exactly one of the allowed classes and give a short reason based only on the "
+    "metadata shown. If the metadata do not allow a judgment, use 'cannot_tell'. You do not decide which record "
+    "is used, and you never choose between values.")
+ANALYST_INSTRUCTION = (
+    "You explain a result that code has already computed. Write no digits at all. Wherever you want a number, a "
+    "p-value, the paper figures, the outcome or the verdict, write the name of the fact in braces exactly as it is "
+    "listed in 'facts', for example {pooled_estimate} or {pooled_p_phrase}; code replaces each name with its value. "
+    "Open by restating the claim in words, then give the outcome ({outcome_wording}) and, when it is listed, the "
+    "verdict ({verdict_wording}), then the main cautions, in two or three sentences, before any detail; do not open "
+    "with the query number. When there is a verdict, also use {pooled_p_phrase} and {pooled_figures_phrase}. Use the "
+    "ready-made sentences and notes whole where they apply: {model_sentence}, {scope_source} or the scope notes, "
+    "{direction_note}, {calibration_summary}, and {group_definition} once. Say 'groups', not 'papers'. Use only the "
+    "facts and notes given, compute nothing, and do not draw conclusions beyond the facts and notes given. Never "
+    "describe the effective number as a number of independent groups. Never write that data do not exist; say what "
+    "was not found in the sources searched. If there is no verdict, do not suggest one. Do not use causal language, "
+    "and do not say a result proves or confirms the claim, even when there is a verdict. Explain the checks and the "
+    "minimums, and what would be needed for a test, in plain words, in at most a few short paragraphs.")
+
 SETTINGS = MappingProxyType({
+    "planner": MappingProxyType({
+        "instruction": PLANNER_INSTRUCTION, "model": MODELS["planner"],
+        "limits": MappingProxyType({"max_tokens": 8000, "max_output_chars": 6000}),
+        "settings": MappingProxyType({"reasoning_effort": "medium"}),
+    }),
+    "critic": MappingProxyType({
+        "instruction": CRITIC_INSTRUCTION, "model": MODELS["critic"],
+        "limits": MappingProxyType({"max_tokens": 8000, "max_output_chars": 30000, "max_flags_per_call": 100}),
+        "settings": MappingProxyType({"reasoning_effort": "low"}),
+    }),
+    "analyst": MappingProxyType({
+        "instruction": ANALYST_INSTRUCTION, "model": MODELS["analyst"],
+        "limits": MappingProxyType({"max_tokens": 8000, "max_output_chars": 6000}),
+        "settings": MappingProxyType({"reasoning_effort": "medium"}),
+    }),
     "curator": MappingProxyType({
         "instruction": CURATOR_INSTRUCTION,
         "model": MODELS["curator"],
diff --git a/hypocurate/pipeline/agents/text_checks.py b/hypocurate/pipeline/agents/text_checks.py
new file mode 100644
index 0000000..5b980cb
--- /dev/null
+++ b/hypocurate/pipeline/agents/text_checks.py
@@ -0,0 +1,128 @@
+"""Checks of an agent's prose against the run record (step 8b; owner, Q8; register 'analyst_text_checks').
+
+Owner, 2026-10-07 (after the live set): rounding and phrasing are done by code. The Analyst's facts carry every
+number as its display string (`pipeline.display`) and a ready-made phrase for each p-value and for each set of
+paper figures; the Analyst quotes numbers exactly as given and never rounds.
+
+**Placeholders** (owner, 2026-10-07, after the live checks): the Analyst writes no digits; it refers to each
+number, phrase and wording by its fact's name in braces, and code renders the finished text (`render`). Before
+rendering: every name must be one of the facts given, no digit may appear outside a placeholder, and
+{outcome_wording} (and {verdict_wording} when there is a verdict) must be used (`placeholder_problems`, counts
+only). The rules below then run on the finished text.
+
+**Number check** (written for reuse by the Commentator, step 12; PRD 5.9): every number in the text must be, as a
+token, one of the numbers the facts give (their display strings, counts and the numbers in the given text such as
+the claim), apart from a few numbers of the method's own wording (`FIXED_NUMBERS`: validity checks 1 and 2, the 95%
+interval, the model's exponent -1/2). Thousands separators are ignored. It checks numerical consistency only: it
+does not check what the text says about the numbers.
+
+**Wording check** (CLAUDE.md, rule 13): the text must contain code's outcome wording verbatim (so it always says
+"in the sources searched"), and code's verdict wording verbatim when there is a verdict; it must not contain any
+phrase of `FORBIDDEN` or `ALWAYS_FORBIDDEN` (no causal language, never "confirms the claim", even with a verdict),
+and with no verdict it must not state one (`NO_VERDICT_FORBIDDEN`); a sentence naming the effective number must not
+call it "independent". (Owner, 2026-10-07: the two word-based rules on p-values and paper figures were removed. With
+placeholders, a p-value and the paper figures exist only inside their phrase names, which no other name exposes
+(tested); with a verdict, the pooled result's two phrases are required placeholders.)
+"""
+from __future__ import annotations
+
+import re
+from typing import Any, Iterable, Mapping
+
+FIXED_NUMBERS = ("1", "2", "95", "95%", "0.5", "-0.5")
+# The model's exponent, written in any of its usual forms, is removed before numbers are read.
+_EXPONENT = re.compile(r"\^\s*\(?\s*[-−]\s*1\s*/\s*2\s*\)?|\^\s*[-−]?\s*0\.5|[-−]½|⁻¹ᐟ²|\^\{-1/2\}")
+# A number token: scientific notation (2.5e-7), or a plain number with an optional percent sign.
+_TOKEN = re.compile(r"(?<![\w.])[-−]?\d+(?:\.\d+)?[eE][-+−]?\d+(?!\w)(?!\.\d)|"
+                    r"(?<![\w.])[-−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:\s*%)?(?![\w])")
+
+FORBIDDEN = ("do not exist", "does not exist", "don't exist", "doesn't exist", "no data exist", "data are absent",
+             "proves", "proven", "prove that", "proof that")
+# Owner's additions (2026-10-07, before the live set): always forbidden, with or without a verdict.
+ALWAYS_FORBIDDEN = re.compile(r"\bconfirms\s+the\s+(claim|hypothesis)\b|\bcauses\b|\bcaused\s+by\b|\bcausal\b",
+                              re.IGNORECASE)
+_EFFECTIVE = re.compile(r"\beffective\s+(number|papers)\b", re.IGNORECASE)
+_INDEPENDENT = re.compile(r"\bindependent\b", re.IGNORECASE)
+_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")
+NO_VERDICT_FORBIDDEN = re.compile(r"\b(is|was|are|were|be)\s+(not\s+)?supported\b|\bsupports?\s+the\s+(claim|hypothesis)\b|"
+                                  r"\bverdict\s*(is|:)\s*(not\s+)?supported\b|\bconfirm(s|ed)?\s+the\s+(claim|hypothesis)\b",
+                                  re.IGNORECASE)
+
+
+def tokens(text: str) -> list[str]:
+    """The number tokens of `text`, normalized: the model's exponent removed, the minus sign and thousands
+    separators unified, no space before a percent sign."""
+    body = _EXPONENT.sub(" ", text)
+    return [re.sub(r"\s+%", "%", m.group(0)).replace("−", "-").replace(",", "") for m in _TOKEN.finditer(body)]
+
+
+def fact_tokens(value: Any) -> set[str]:
+    """Every number the facts give, as a token: integers as written, display strings and given text by their tokens."""
+    out: set[str] = set()
+    if isinstance(value, bool) or value is None:
+        return out
+    if isinstance(value, int):
+        out.add(str(value))
+    elif isinstance(value, float):
+        out.add(repr(value))  # display strings are expected; a float is matched only as written
+    elif isinstance(value, str):
+        out.update(tokens(value))
+    elif isinstance(value, Mapping):
+        for v in value.values():
+            out |= fact_tokens(v)
+    elif isinstance(value, (list, tuple)):
+        for v in value:
+            out |= fact_tokens(v)
+    return out
+
+
+def unmatched_numbers(text: str, facts: Any) -> list[str]:
+    """The number tokens of `text` that the facts do not give (empty when all are given)."""
+    known = fact_tokens(facts) | set(FIXED_NUMBERS)
+    return [t for t in tokens(text) if t not in known]
+
+
+def wording_problems(text: str, decision: Mapping, facts: Mapping | None = None) -> list[str]:
+    """The wording rules the text breaks (empty when none). `facts`: the Analyst's facts, for its phrases."""
+    lower = " ".join(text.lower().split())
+    problems = [f"forbidden: {p}" for p in FORBIDDEN if p in lower]
+    problems += [f"forbidden: {m.group(0).lower()}" for m in ALWAYS_FORBIDDEN.finditer(text)]
+    outcome = (decision.get("outcome_wording") or "").lower()
+    if not outcome or outcome not in lower:
+        problems.append("outcome wording missing")
+    verdict = (decision.get("verdict_wording") or "").lower()
+    if decision.get("verdict"):
+        if verdict not in lower:
+            problems.append("verdict wording missing")
+    elif NO_VERDICT_FORBIDDEN.search(text):
+        problems.append("a verdict is stated where there is none")
+    for sentence in filter(None, (x.strip() for x in _SENTENCE.split(text))):
+        if _EFFECTIVE.search(sentence) and _INDEPENDENT.search(sentence):
+            problems.append("the effective number described as independent")
+    return problems
+
+
+# --- Placeholders (owner, 2026-10-07): the Analyst writes {name}; code writes the numbers -----------------------
+
+PLACEHOLDER = re.compile(r"\{([^{}\n]{1,80})\}")
+REQUIRED = ("outcome_wording",)  # and 'verdict_wording' whenever the facts give one
+# Owner, 2026-10-07: with a verdict, the pooled result's p-value phrase and paper-figures phrase must be used too.
+REQUIRED_WITH_VERDICT = ("pooled_p_phrase", "pooled_figures_phrase")
+
+
+def placeholder_problems(template: str, names: Mapping[str, str]) -> dict[str, int]:
+    """Counts only, never text: names not among the facts, digits outside a placeholder, required placeholders
+    missing."""
+    used = PLACEHOLDER.findall(template)
+    rest = PLACEHOLDER.sub(" ", template)
+    required = list(REQUIRED) + (["verdict_wording"] if "verdict_wording" in names else [])
+    phrases_required = [r for r in REQUIRED_WITH_VERDICT if "verdict_wording" in names and r in names]
+    return {"unknown_names": sum(1 for u in used if u not in names),
+            "digits_outside_placeholders": len(re.findall(r"\d", rest)),
+            "required_missing": sum(1 for r in required if r not in used),
+            "result_phrases_missing": sum(1 for r in phrases_required if r not in used)}
+
+
+def render(template: str, names: Mapping[str, str]) -> str:
+    """The finished text: each {name} replaced by its display string or ready-made phrase."""
+    return PLACEHOLDER.sub(lambda m: names[m.group(1)], template)
diff --git a/hypocurate/pipeline/analysis.py b/hypocurate/pipeline/analysis.py
index d5372db..a3def2f 100644
--- a/hypocurate/pipeline/analysis.py
+++ b/hypocurate/pipeline/analysis.py
@@ -163,10 +163,34 @@ def gap_facts(gap: Mapping, minimums: Mapping | None) -> dict:
     rules: dict[str, int] = {}
     for d in gap["decisions"]["records"]:
         rules[d["rule"]] = rules.get(d["rule"], 0) + 1
+    sources = [{"source": s["source"], "search_status": s["search_status"], "nothing_found": s["nothing_found"],
+                "kind": nothing_found_kind(s, gap["decisions"])} for s in gap["coverage"]["sources"]]
     return {"minimums": minimums, "minimums_missed": sorted(k for k, v in (minimums or {}).items() if not v["met"]),
             "records_lacking_fields": lacking, "eligibility_rules": dict(sorted(rules.items())),
-            "sources": [{"source": s["source"], "search_status": s["search_status"], "nothing_found": s["nothing_found"]}
-                        for s in gap["coverage"]["sources"]]}
+            "sources": sources, "kind": run_nothing_found_kind(sources)}
+
+
+# The kind of "nothing found" (PRD 3.1, 14.3; owner, 2026-10-07; register 'nothing_found_kinds'), decided by
+# code from stored facts: a failed search; missing evidence (searched, but no record of the source entered the
+# primary set); never 'reported_negative' in sprint 1 (no source states a negative result).
+def nothing_found_kind(source: Mapping, decisions: Mapping) -> str | None:
+    if source["search_status"] == "not_selected":
+        return None
+    if source["search_status"] == "failed":
+        return "failed_search"
+    primary = set(decisions["sets"].get("primary") or [])
+    if any(d["source"] == source["source"] and d["record"] in primary for d in decisions["records"]):
+        return None  # records of this source are in the primary set
+    return "missing_evidence"
+
+
+def run_nothing_found_kind(sources: list[Mapping]) -> str | None:
+    """For the run: None when some source contributed records; 'failed_search' when every chosen source failed;
+    otherwise 'missing_evidence'."""
+    chosen = [s for s in sources if s["search_status"] != "not_selected"]
+    if any(s["kind"] is None for s in chosen):
+        return None
+    return "failed_search" if chosen and all(s["kind"] == "failed_search" for s in chosen) else "missing_evidence"
 
 
 def empty_minimums(plan: Mapping) -> dict:
diff --git a/hypocurate/pipeline/analyst_names.py b/hypocurate/pipeline/analyst_names.py
new file mode 100644
index 0000000..1ec8bc5
--- /dev/null
+++ b/hypocurate/pipeline/analyst_names.py
@@ -0,0 +1,292 @@
+"""The Analyst's named facts (step 8b; owner, 2026-10-07: placeholders and fewer facts; register 'analyst_names').
+
+The Analyst writes no digits: wherever it wants a number, a p-value, the paper figures, the outcome or the verdict,
+it writes the name of a fact in braces, for example {pooled_estimate}; code replaces each name with its display
+string or ready-made phrase (`agents.text_checks.render`). This module builds those names from what code stored:
+
+- the decision: {outcome_wording} (always to be used), {verdict_wording} (to be used when there is a verdict),
+  {evidence_level}, {evidence_level_wording}, {result_label};
+- the plan: {alpha}, {sufficiency_option}, each minimum ({minimum_records}, ...), and where the scope came from:
+  per scope part a note {scope_alloy_class}, {scope_phase_class}, {scope_test_type}, {scope_temperature_band}
+  ("the claim did not state a test type; tension was assumed"), or {scope_source} for a fixed plan;
+- the pooled result: counts, each count against its minimum ({count_records}, {met_records}, ...), and unless
+  withheld the estimate, its standard error, {pooled_p_phrase} and {pooled_figures_phrase};
+- per source (its key in the name): counts, label and, unless withheld, estimate, standard error and phrases;
+- both calibrations of the pooled result (fixed and estimated noise): shares with intervals and the flag; below the
+  minimums only the fixed-noise detection and false-positive shares, which use no outcome value;
+- a summary of the sensitivity sets, built by code (owner, 2026-10-07): how many sets; how many under each of the
+  four per-source labels, classified against the pooled result by the same function (`statistics.label`); the
+  names of the sets not labelled "agrees"; the smallest and largest estimate with their sets; and the result
+  without the group holding the largest share of slope information. The full per-set numbers are not given;
+- for a run with no dataset frozen: the gap facts (records lacking each field per source, the kind of nothing
+  found, the minimums missed);
+- at 'narrowed': the claim's parts with their counts, the parts with none, the narrower scope.
+
+Every value is a string (display strings and phrases from `pipeline.display`; counts as written). Names hold
+lower-case letters and underscores only, so a digit can never be part of a name. Below the minimums no name gives an
+estimate, a standard error, a p-value or the paper figures (owner's standing requirement).
+"""
+from __future__ import annotations
+
+import re
+from typing import Any, Mapping
+
+from hypocurate.pipeline import display
+from hypocurate.pipeline import statistics as st
+from hypocurate.pipeline.eligibility import INFLUENCE_DISPLAY_NAME, INFLUENCE_KEY
+
+NAME = re.compile(r"[a-z_]+")
+# Plain wording for the four per-source labels when shown in text (owner, 2026-10-07). 'not_enough_data' is worded by
+# its reason (`label_words`): too few groups, or otherwise no valid test alone.
+LABEL_WORDS = {"agrees": "in agreement with the pooled result",
+               "conflicts": "in conflict with the pooled result (the opposite sign)",
+               "same_direction_different_decision": "in the same direction as the pooled result, with a different test "
+                                                    "result",
+               "not_enough_data": "not testable alone"}
+TOO_FEW_GROUPS = "too few groups to test alone"
+# Code-built sentences the Analyst uses whole (owner, 2026-10-07).
+GROUP_DEFINITION = "A group is a paper, or, for a source that is a single dataset, the whole dataset."
+MODEL_SENTENCE = ("The test fitted yield strength (MPa) as a baseline for each alloy plus one coefficient, shared by all "
+                  "alloys, times the inverse square root of grain size (µm); the estimate is that coefficient, in "
+                  "MPa·µm^0.5.")
+FIXED_PLAN_SENTENCE = "The scope was set by the fixed reference plan and was not read from the claim."
+NARROWER_PLAN_SENTENCE = ("The scope was set by the narrower plan that the original question's narrowing decision stored, "
+                          "and was not read from this question's text.")
+CALIBRATION_NAMES = {"estimated": "noise levels estimated from the data", "fixed": "fixed illustrative noise levels"}
+NO_FLAG = "the share is consistent with the nominal level under the stated assumptions"
+SCOPE_WORDS = {"alloy_class": "an alloy class", "phase_class": "a phase class", "test_type": "a test type",
+               "temperature_band": "a temperature"}
+SCOPE_LABELS = {"alloy_class": "alloy class", "phase_class": "phase class", "test_type": "test type",
+                "temperature_band": "temperature"}
+LETTERS = "abcdefghijklmnopqrstuvwxyz"
+
+
+def _s(v: Any) -> str:
+    """A value as text: integers as written, floats through the display rules' fallback, words as they are."""
+    if isinstance(v, bool):
+        return "yes" if v else "no"
+    if isinstance(v, int):
+        return str(v)
+    if isinstance(v, float):
+        return display.fallback(v)
+    return str(v)
+
+
+def _key(source: str) -> str:
+    return re.sub(r"[^a-z_]", "_", source.lower())
+
+
+def band_words(band: Mapping | str) -> str:
+    if not isinstance(band, Mapping):
+        return str(band)
+    if band.get("band") == "room temperature" or "min" not in band:
+        return str(band.get("band"))
+    return f"{band['band']} ({display.temperature(band['min'])} to {display.temperature(band['max'])})"
+
+
+def scope_value_words(part: str, values: list) -> str:
+    return ", ".join(band_words(v) if part == "temperature_band" else str(v) for v in values)
+
+
+def scope_notes(scope: Mapping | None, stated: Mapping | None) -> dict[str, str]:
+    """Per scope part: stated by the claim, or the Planner's default (owner, 2026-10-07)."""
+    if not scope or not stated:
+        return {}
+    out = {}
+    for part, label in SCOPE_LABELS.items():
+        if part not in scope:
+            continue
+        values = scope_value_words(part, scope[part])
+        out[f"scope_{part}"] = (f"{label} {values}, as the claim states" if stated.get(part)
+                                else f"the claim did not state {SCOPE_WORDS[part]}; {values} was assumed")
+    return out
+
+
+def _set_name(key: str) -> str:
+    return INFLUENCE_DISPLAY_NAME if key == INFLUENCE_KEY else key.replace("_", " ")
+
+
+def _calibration(prefix: str, c: Mapping | None) -> dict[str, str]:
+    out = {f"{prefix}_calibration_name": CALIBRATION_NAMES[prefix]}
+    if not isinstance(c, Mapping) or c.get("status") != "computed":
+        reason = (c or {}).get("reason") if isinstance(c, Mapping) else None
+        return {**out, f"{prefix}_unavailable": str(reason or "not computed").replace("_", " ")}
+    a = c.get("assumptions") or {}
+    return {**out, f"{prefix}_false_positive": display.percent(c["null"]["share"]),
+            f"{prefix}_false_positive_interval": display.interval_phrase(c["null"]["ci_low"], c["null"]["ci_high"]),
+            f"{prefix}_detection": display.percent(c["effect"]["share"]),
+            f"{prefix}_detection_interval": display.interval_phrase(c["effect"]["ci_low"], c["effect"]["ci_high"]),
+            f"{prefix}_flag": str(c.get("flag_wording") or NO_FLAG),
+            f"{prefix}_scatter": display.stress(a["scatter"]) if "scatter" in a else "not given",
+            f"{prefix}_shift": display.stress(a["shift"]) if "shift" in a else "not given"}
+
+
+def calibration_summary(cal: Mapping, alpha: float) -> str:
+    """One sentence covering both calibrations and their flags (owner, 2026-10-07)."""
+    parts, flags = [], {}
+    for method in ("estimated", "fixed"):
+        c = cal.get(method)
+        if isinstance(c, Mapping) and c.get("status") == "computed":
+            parts.append(f"with {CALIBRATION_NAMES[method]}, the test was significant in "
+                         f"{display.percent(c['null']['share'])} of simulations with no effect "
+                         f"({display.interval_phrase(c['null']['ci_low'], c['null']['ci_high'])})")
+            flags[method] = c.get("flag_wording") or NO_FLAG
+        else:
+            reason = str((c or {}).get("reason") or "not computed") if isinstance(c, Mapping) else "not computed"
+            parts.append(f"with {CALIBRATION_NAMES[method]}, no calibration ({reason.replace('_', ' ')})")
+    head = "In the simulation check, " + "; ".join(parts) + f", against a nominal level of {display.nominal_level(alpha)}."
+    if len(flags) == 2 and len(set(flags.values())) == 1:
+        return f"{head} Under both, {next(iter(flags.values()))}."
+    tails = [f"under {CALIBRATION_NAMES[m]}, {f}" for m, f in flags.items()]
+    return f"{head} " + ("; ".join(tails)[0].upper() + "; ".join(tails)[1:] + "." if tails else "")
+
+
+def direction_note(estimate: float | None, alternative: str | None) -> str | None:
+    """The estimate's sign against the direction the claim describes (the plan's alternative, k > 0)."""
+    if estimate is None or alternative != "k > 0":
+        return None
+    if estimate > 0:
+        return "the estimate is positive, the direction the claim describes"
+    if estimate < 0:
+        return "the estimate is negative, opposite to the direction the claim describes"
+    return "the estimate is zero"
+
+
+def label_words(e: Mapping) -> str:
+    if e.get("label") == "not_enough_data" and e.get("inference_reason") == "insufficient_groups":
+        return TOO_FEW_GROUPS
+    return LABEL_WORDS.get(e.get("label"), str(e.get("label")))
+
+
+def _result(prefix: str, e: Mapping, withheld: bool) -> dict[str, str]:
+    c = e.get("counts") or {}
+    out = {f"{prefix}_records": _s(c.get("n_records")), f"{prefix}_alloys": _s(c.get("n_alloys")),
+           f"{prefix}_groups": _s(c.get("n_groups")),
+           f"{prefix}_inference": "valid" if (e.get("checks") or {}).get("inference_valid") else "not valid"}
+    if e.get("inference_reason"):
+        out[f"{prefix}_inference_reason"] = str(e["inference_reason"]).replace("_", " ")
+    if withheld:
+        return out
+    if e.get("estimate") is not None:
+        out[f"{prefix}_estimate"] = display.coefficient(e["estimate"])
+    if e.get("std_error") is not None:
+        out[f"{prefix}_std_error"] = display.coefficient(e["std_error"])
+    if e.get("p_value") is not None:
+        out[f"{prefix}_p_phrase"] = display.p_phrase(e["p_value"])
+    if all(x is not None for x in (c.get("n_groups_informative"), c.get("effective_papers"),
+                                   c.get("largest_paper_share"), e.get("df"))):
+        out[f"{prefix}_figures_phrase"] = display.figures_phrase(c["n_groups_informative"], c["effective_papers"],
+                                                                 c["largest_paper_share"], e["df"])
+    return out
+
+
+def sensitivity_summary(analyses: list[Mapping], pooled: Mapping, alpha: float, withheld: bool) -> dict[str, str]:
+    """The sensitivity sets classified against the pooled result with the per-source labels and function."""
+    sets = [e for e in analyses if e.get("scope") == "sensitivity"]
+    out = {"sensitivity_sets": str(len(sets))}
+    labels = {e["set"]: st.label(e, pooled, alpha) for e in sets}
+    for code, words in LABEL_WORDS.items():
+        out[f"sensitivity_{code}"] = str(sum(1 for v in labels.values() if v == code))
+    by_set = {e["set"]: e for e in sets}
+    others = [f"{_set_name(k)} ({label_words({**by_set[k], 'label': v})})" for k, v in labels.items() if v != "agrees"]
+    out["sensitivity_not_agreeing"] = "; ".join(others) if others else "none"
+    estimated = [e for e in sets if e.get("estimate") is not None]
+    if estimated and not withheld:
+        low = min(estimated, key=lambda e: e["estimate"])
+        high = max(estimated, key=lambda e: e["estimate"])
+        out.update(sensitivity_smallest_estimate=display.coefficient(low["estimate"]),
+                   sensitivity_smallest_set=_set_name(low["set"]),
+                   sensitivity_largest_estimate=display.coefficient(high["estimate"]),
+                   sensitivity_largest_set=_set_name(high["set"]))
+    influential = next((e for e in sets if e["set"] == INFLUENCE_KEY), None)
+    if influential is not None:
+        out.update(_result("without_largest_share", influential, withheld))
+        out["without_largest_share_label"] = label_words({**influential, "label": labels[INFLUENCE_KEY]})
+    return out
+
+
+def analysis_names(stats: Mapping, gap: Mapping, plan: Mapping, scope_note: Mapping[str, str]) -> dict[str, str]:
+    """The names of a run after the analysis stage (with or without a dataset frozen)."""
+    d = stats.get("decision") or {}
+    names: dict[str, str] = {"outcome_wording": str(d.get("outcome_wording")),
+                             "evidence_level": _s(d.get("evidence_level")),
+                             "evidence_level_wording": str(d.get("evidence_level_wording"))}
+    if d.get("verdict"):
+        names["verdict_wording"] = str(d.get("verdict_wording"))
+    if d.get("label"):
+        names["result_label"] = str(d["label"])
+    names["nominal_level"] = display.nominal_level(plan["alpha"])
+    names["model_sentence"] = MODEL_SENTENCE
+    names["group_definition"] = GROUP_DEFINITION
+    names["sufficiency_option"] = str(plan["sufficiency_option"]).replace("_", " ")
+    for k, v in plan["minimums"].items():
+        names[f"minimum_{k}"] = _s(v)
+    names.update(scope_note)
+    withheld = bool(stats.get("withheld"))
+    analyses = [e for e in stats.get("analyses") or [] if isinstance(e, Mapping)]
+    if analyses:
+        pooled = analyses[0]
+        names.update(_result("pooled", pooled, withheld))
+        for k, m in (pooled.get("minimums") or {}).items():
+            names[f"count_{k}"] = _s(m.get("count"))
+            names[f"met_{k}"] = "met" if m.get("met") else "not met"
+        cal = pooled.get("calibration") or {}
+        note = direction_note(pooled.get("estimate"), plan.get("alternative")) if not withheld else None
+        if note:
+            names["direction_note"] = note
+        if withheld:  # the fixed-noise shares use no outcome value (owner, 2026-10-07)
+            fixed = (pooled.get("detection") or {}).get("fixed") or {}
+            if "detection" in fixed:
+                names.update(fixed_detection=display.percent(fixed["detection"]),
+                             fixed_false_positive=display.percent(fixed["false_positive"]))
+        else:
+            names.update(_calibration("fixed", cal.get("fixed")))
+            names.update(_calibration("estimated", cal.get("estimated")))
+            names["calibration_summary"] = calibration_summary(cal, plan["alpha"])
+        for e in analyses:
+            if e.get("scope") == "per_source":
+                prefix = _key(e["source"])
+                names.update(_result(prefix, e, withheld))
+                if e.get("label"):
+                    names[f"{prefix}_label"] = label_words(e)
+        names.update(sensitivity_summary(analyses, pooled, plan["alpha"], withheld))
+    missed = gap.get("minimums_missed") or []
+    names["minimums_missed"] = ", ".join(str(m).replace("_", " ") for m in missed) if missed else "none"
+    if gap.get("kind"):
+        names["nothing_found"] = str(gap["kind"]).replace("_", " ")
+    for s in gap.get("sources") or []:
+        prefix = _key(s["source"])
+        if s.get("kind"):
+            names[f"{prefix}_nothing_found"] = str(s["kind"]).replace("_", " ")
+        names[f"{prefix}_search"] = str(s.get("search_status"))
+    for source, fields in (gap.get("records_lacking_fields") or {}).items():
+        for field, n in fields.items():
+            if n:
+                names[f"{_key(source)}_lacking_{_key(field)}"] = _s(n)
+    return names
+
+
+def narrowing_names(n: Mapping) -> dict[str, str]:
+    """The names of a partly-sufficient original at 'narrowed'."""
+    d = n.get("decision") or {}
+    names = {"outcome_wording": str(d.get("outcome_wording")), "evidence_level": _s(d.get("evidence_level")),
+             "evidence_level_wording": str(d.get("evidence_level_wording"))}
+    names.update(scope_notes(n.get("claim_scope"), n.get("scope_stated")))
+    for letter, part in zip(LETTERS, n.get("part_counts") or []):
+        value = band_words(part["value"]) if part["part"] == "temperature_band" else str(part["value"])
+        names[f"part_{letter}"] = f"{SCOPE_LABELS.get(part['part'], part['part'])} {value}"
+        names[f"part_{letter}_records"] = _s(part["n"])
+    zero = n.get("zero_parts") or []
+    names["parts_without_records"] = "; ".join(
+        f"{SCOPE_LABELS.get(z['part'], z['part'])} {band_words(z['value']) if z['part'] == 'temperature_band' else z['value']}"
+        for z in zero) or "none"
+    narrower = n.get("narrower_scope") or {}
+    names["narrower_scope"] = "; ".join(f"{SCOPE_LABELS[p]} {scope_value_words(p, v)}" for p, v in narrower.items()
+                                        if p in SCOPE_LABELS)
+    return names
+
+
+def check_names(names: Mapping[str, str]) -> None:
+    bad = [k for k in names if not NAME.fullmatch(k)]
+    if bad:
+        raise ValueError(f"fact names hold lower-case letters and underscores only: {bad}")
diff --git a/hypocurate/pipeline/checkpoints.py b/hypocurate/pipeline/checkpoints.py
index 0134528..b9ae161 100644
--- a/hypocurate/pipeline/checkpoints.py
+++ b/hypocurate/pipeline/checkpoints.py
@@ -52,6 +52,8 @@ def lock_rules(engine: Engine, run_id: int, content: Mapping[str, Any]) -> str:
     fp = fingerprint(plan)
 
     def body(conn: Connection, stage: str):
+        if stage == "narrowed":  # step 8b (A4): the partly-sufficient original never locks a plan
+            raise Refused("lock_rules", "narrowed")
         if stage != "before_lock":
             raise Refused("lock_rules", "already_done" if stage != "none" else "stage_mismatch")
         version = conn.execute(text("SELECT hypothesis_version_id FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
diff --git a/hypocurate/pipeline/completion.py b/hypocurate/pipeline/completion.py
index e8a5e37..05404ed 100644
--- a/hypocurate/pipeline/completion.py
+++ b/hypocurate/pipeline/completion.py
@@ -45,3 +45,32 @@ def copy_decision(engine: Engine, run_id: int) -> dict:
         return decision
 
     return write(engine, run_id, ROLE, "copy_decision", body)
+
+
+def copy_partly_sufficient(engine: Engine, run_id: int) -> dict:
+    """Completes a partly-sufficient original question (step 8b; owner, Q5, A1): only copies the decision
+    stored by code's narrowing decision (outcome 'partly_sufficient', no verdict, level 1), after checking
+    that the run is at 'narrowed' and that the source versions the counts were taken on are the run's
+    (sealed versions never change, so the same versions give the same counts). The database checks again
+    (migration 0006: no plan, no record, a done narrowing decision of partly sufficient)."""
+
+    def body(conn: Connection, stage: str):
+        if stage != "narrowed":
+            raise Refused("copy_partly_sufficient", "stage_mismatch")
+        output = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'narrowing' "
+                                   "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
+        decision = output.get("decision") if isinstance(output, dict) else None
+        if not isinstance(decision, dict) or decision.get("outcome") != "partly_sufficient":
+            raise Refused("copy_partly_sufficient", "decision_missing")
+        stored = sorted((s["source"], s["version_fingerprint"]) for s in output.get("sources") or [])
+        current = sorted(conn.execute(text(
+            "SELECT s.key, sv.fingerprint FROM run_source rs JOIN source s ON s.id = rs.source_id "
+            "JOIN source_version sv ON sv.id = rs.source_version_id WHERE rs.run_id = :r"), dict(r=run_id)).all())
+        if stored != [tuple(c) for c in current]:
+            raise Refused("copy_partly_sufficient", "decision_not_current")
+        conn.execute(text("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
+                          "verdict = NULL, exploratory = false, evidence_level = :e WHERE id = :r"),
+                     dict(e=decision["evidence_level"], r=run_id))
+        return decision
+
+    return write(engine, run_id, ROLE, "copy_partly_sufficient", body)
diff --git a/hypocurate/pipeline/display.py b/hypocurate/pipeline/display.py
new file mode 100644
index 0000000..2d9aba3
--- /dev/null
+++ b/hypocurate/pipeline/display.py
@@ -0,0 +1,135 @@
+"""How numbers are shown (step 8b; owner, 2026-10-07: rounding and phrasing are done by code, never by the Analyst;
+register 'display_precision'). The one named place for display precision.
+
+From the register: k, its standard error and t to 0.1, and a p-value to two significant figures
+('reference_test_tolerance', 'reference_numbers'); counts exact. From the approved sensitivity numbers
+('reference_numbers'): the effective number of papers to two decimals and the largest share as a percentage to one
+decimal. Drafted by Claude Code for the owner's review: every other share or rate (calibration, detection, power,
+their intervals) as a percentage to one decimal; temperatures, scatter and shift to at most one decimal; the
+threshold α as given; any other number to three significant figures.
+
+`display(facts)` turns every float of the Analyst's facts into its display string; integers (counts) stay as they
+are. `p_phrase`, `figures_phrase` and `interval_phrase` are ready-made phrases; `coefficient`, `stress` and
+`temperature` carry their units (owner, 2026-10-07); `nominal_level` gives the threshold as a percentage.
+"""
+from __future__ import annotations
+
+import math
+from typing import Any, Callable, Mapping
+
+P_DESCRIPTION = "approximate, nominal, one-sided"
+
+
+def one_decimal(v: float) -> str:
+    return f"{v:.1f}"
+
+
+def two_decimals(v: float) -> str:
+    return f"{v:.2f}"
+
+
+def significant(v: float, n: int) -> str:
+    """`n` significant figures; scientific notation below 0.001 without exponent padding (2.5e-7)."""
+    if v == 0:
+        return "0"
+    if abs(v) < 1e-3:
+        mantissa, exponent = f"{v:.{n - 1}e}".split("e")
+        return f"{mantissa}e{int(exponent)}"
+    digits = max(n - 1 - math.floor(math.log10(abs(v))), 0)
+    return f"{v:.{digits}f}"
+
+
+def p_value(v: float) -> str:
+    return significant(v, 2)
+
+
+def percent(v: float) -> str:
+    return f"{v * 100:.1f}%"
+
+
+def at_most_one_decimal(v: float) -> str:
+    return f"{v:.1f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))
+
+
+def as_given(v: float) -> str:
+    return f"{v:g}"
+
+
+def fallback(v: float) -> str:
+    return significant(v, 3)
+
+
+# Key -> how its value is shown. A list value (an interval) is shown element by element.
+RULES: Mapping[str, Callable[[float], str]] = {
+    "estimate": one_decimal, "std_error": one_decimal, "t": one_decimal,
+    "p_value": p_value,
+    "effective_papers": two_decimals,
+    "largest_paper_share": percent, "share": percent, "ci_low": percent, "ci_high": percent,
+    "detection": percent, "detection_ci": percent, "false_positive": percent, "false_positive_ci": percent,
+    "estimated_power": percent, "estimated_power_estimated_noise": percent,
+    "scatter": at_most_one_decimal, "shift": at_most_one_decimal, "min": at_most_one_decimal,
+    "max": at_most_one_decimal,
+    "alpha": as_given,
+}
+
+
+def _show(key: str | None, value: Any) -> Any:
+    if isinstance(value, bool) or value is None:
+        return value
+    if isinstance(value, float):
+        if not math.isfinite(value):
+            return None
+        if value.is_integer() and key not in RULES:
+            return int(value)
+        return RULES.get(key, fallback)(value)
+    if isinstance(value, int):
+        return value
+    if isinstance(value, Mapping):
+        return {k: _show(k, v) for k, v in value.items()}
+    if isinstance(value, list):
+        return [_show(key, v) for v in value]
+    return value
+
+
+def display(facts: Mapping) -> dict:
+    """The facts with every float as its display string (integers unchanged)."""
+    return _show(None, facts)
+
+
+# Owner, 2026-10-07 (after reading a live explanation): units on every estimate, standard error, scatter, shift and
+# temperature; one form for rates and the threshold (percentages); each simulation interval says what it is.
+COEFFICIENT_UNIT = "MPa·µm^0.5"
+INTERVAL_NOTE = "a 95% simulation interval covering simulation uncertainty only"
+
+
+def coefficient(v: float) -> str:
+    """An estimate or standard error of k, with its unit."""
+    return f"{one_decimal(v)} {COEFFICIENT_UNIT}"
+
+
+def stress(v: float) -> str:
+    return f"{at_most_one_decimal(v)} MPa"
+
+
+def temperature(v: float) -> str:
+    return f"{at_most_one_decimal(v)} °C"
+
+
+def nominal_level(alpha: float) -> str:
+    """The threshold in the same form as the shares it is compared with."""
+    return percent(alpha)
+
+
+def interval_phrase(low: float, high: float) -> str:
+    return f"{percent(low)} to {percent(high)}, {INTERVAL_NOTE}"
+
+
+def p_phrase(p: float) -> str:
+    """The ready-made phrase for a p-value: the value and its fixed description."""
+    return f"p ≈ {p_value(p)} ({P_DESCRIPTION})"
+
+
+def figures_phrase(informative: int, effective: float, largest_share: float, df: int) -> str:
+    """The ready-made phrase for the four paper figures, always together (register 'p_value_reporting')."""
+    return (f"{informative} informative groups, an effective number of groups of {two_decimals(effective)}, "
+            f"a largest share of {percent(largest_share)} and {df} degrees of freedom")
diff --git a/hypocurate/pipeline/narrowing.py b/hypocurate/pipeline/narrowing.py
new file mode 100644
index 0000000..92253d9
--- /dev/null
+++ b/hypocurate/pipeline/narrowing.py
@@ -0,0 +1,151 @@
+"""The narrowing decision (step 8b; PRD 5.4; owner, Q5, A1, A8, A11, B1; register 'narrowing_decision').
+
+Taken by code, right after the Planner and before any lock, on counts of structure only: the code role
+'narrowing' reads `candidate_counts` (per chosen source, from the sealed version recorded at dispatch:
+counts per combination of categories, reported temperature and field statuses; never an outcome value).
+
+**Claim parts** are each phase class, each temperature band (with its range) and each test type of the
+claim's scope as the Planner stated it (code checked its shape); alloy class is not countable (Q5). A part's
+count is the number of records that have a grain size and the plan's outcome at an accepted status, fall in
+that part, and fall in the claim's values on the other two dimensions. Temperature is judged as eligibility
+rule 3 judges it: a reported temperature decides (room temperature by the profile's range, another band by
+the claim's range); otherwise the band; otherwise the record is not counted. Statuses are the profile's
+accepted value statuses.
+
+**The decision** (`decide`, pure):
+- no part has zero records: `proceed` if the claim is one plan, else `claim_not_one_plan` (A11);
+- some part has zero records: the narrower scope is the claim's scope less exactly those parts, built by code
+  (owner, 2026-10-07, after live run C: the Planner cannot see which part has no usable record; a proposal of
+  its, if any, is stored as `proposed_narrower` and never used). If a dimension is left empty, nothing is
+  testable: `proceed` (the original then ends insufficient) or `claim_not_one_plan`. If the narrower scope
+  makes a valid plan: `partly_sufficient`, with the narrower plan (less its hypothesis version) and its
+  fingerprint; if not (`narrower_invalid`), the original goes on (`proceed`) or stops (`claim_not_one_plan`).
+
+`run_narrowing` stores the decision as the code stage 'narrowing' (with the counts' fingerprint and each
+source's version fingerprint, B1) in one locked transaction at 'before_lock'. A decision of partly
+sufficient moves the run to 'narrowed' (A4): no plan can be locked after it (code and database).
+"""
+from __future__ import annotations
+
+import hashlib
+from typing import Any, Mapping
+
+from sqlalchemy import Connection, Engine, text
+
+from hypocurate.access.dispatch import bind_code
+from hypocurate.access.errors import AccessDenied
+from hypocurate.access.inputs import role_input
+from hypocurate.pipeline import plan as plans
+from hypocurate.pipeline import profile as p
+from hypocurate.pipeline import statistics as st
+from hypocurate.pipeline.agents.planner import Answer, build_plan, one_plan, plan_without_version
+from hypocurate.pipeline.writes import Refused, code_stage, log_refusal, write
+
+ROLE = "narrowing"
+DIMENSIONS = ("phase_class", "test_type", "temperature_band")
+STATUSES = frozenset(p.ACCEPTED_VALUE_STATUSES)
+RT_MIN, RT_MAX = p.ROOM_TEMPERATURE_C
+# Owner's addition 1 (2026-10-06): how a partly-sufficient original's level 1 is shown.
+PARTLY_DECISION = {"state": "partly_sufficient", "outcome": "partly_sufficient",
+                   "outcome_wording": "partly sufficient in the sources searched", "verdict": None,
+                   "verdict_wording": None, "exploratory": False, "evidence_level": 1,
+                   "evidence_level_wording": st.PARTLY_SUFFICIENT_WORDING, "label": None}
+
+
+def _known(cell: Mapping, field: str) -> bool:
+    return cell["status"].get(field) in STATUSES
+
+
+def usable(cell: Mapping, outcome: str) -> bool:
+    """A grain size and the outcome, each at an accepted status."""
+    return cell["grain_size_present"] and _known(cell, "grain_size") and _known(cell, outcome)
+
+
+def matches(cell: Mapping, dimension: str, value: Any) -> bool:
+    if dimension in ("phase_class", "test_type"):
+        return _known(cell, dimension) and cell["categories"][dimension] == value
+    t = cell["test_temperature"]
+    if _known(cell, "test_temperature") and t is not None:
+        low, high = (RT_MIN, RT_MAX) if value["band"] == plans.ROOM_TEMPERATURE else (value["min"], value["max"])
+        return low <= t <= high
+    if _known(cell, "test_temperature_band"):
+        return cell["categories"]["test_temperature_band"] == value["band"]
+    return False
+
+
+def part_counts(counts: list[Mapping], scope: Mapping, outcome: str) -> list[dict]:
+    """Per claim part, the records that count for it (see the module docstring)."""
+    cells = [c for source in counts if source.get("readable") for c in source["cells"] if usable(c, outcome)]
+    out = []
+    for dimension in DIMENSIONS:
+        others = [d for d in DIMENSIONS if d != dimension]
+        for value in scope[dimension]:
+            n = sum(c["n"] for c in cells if matches(c, dimension, value)
+                    and all(any(matches(c, d, v) for v in scope[d]) for d in others))
+            out.append({"part": dimension, "value": value, "n": n})
+    return out
+
+
+def _same(a: list, b: list) -> bool:
+    key = lambda v: plans.canonical(v) if isinstance(v, Mapping) else v  # noqa: E731
+    return sorted(map(key, a)) == sorted(map(key, b))
+
+
+def decide(answer: Answer, counts: list[Mapping], hypothesis_version_id: int, sufficiency_option: str) -> dict:
+    """The narrowing decision from the checked answer and the structure counts (pure)."""
+    scope = answer.claim_scope
+    is_one = one_plan(scope)
+    parts = part_counts(counts, scope, answer.outcome)
+    zero = [{"part": x["part"], "value": x["value"]} for x in parts if x["n"] == 0]
+    fallback = "proceed" if is_one else "claim_not_one_plan"
+    out = {"claim_scope": scope, "scope_stated": dict(answer.stated), "part_counts": parts, "zero_parts": zero,
+           "narrower_scope": None, "proposed_narrower": answer.narrower}
+    if not zero:
+        return {**out, "result": fallback, "reason": "no_part_without_records"}
+    narrower = {d: [v for v in scope[d] if not any(z["part"] == d and z["value"] == v for z in zero)] for d in DIMENSIONS}
+    if not all(narrower.values()):
+        return {**out, "result": fallback, "reason": "no_part_with_records"}
+    out["narrower_scope"] = narrower
+    # Owner, 2026-10-07 (after live run C): code builds the narrower scope from its own counts; the Planner
+    # cannot see which part has no usable record, so a proposal of its, if any, is stored and never used.
+    if len(scope["alloy_class"]) != 1 or not one_plan(narrower):
+        return {**out, "result": fallback, "reason": "narrower_invalid"}
+    try:
+        plan = build_plan(hypothesis_version_id, narrower, answer.outcome, answer.exclusion_rules,
+                          sufficiency_option, alloy_class=scope["alloy_class"])
+    except plans.PlanError:
+        return {**out, "result": fallback, "reason": "narrower_invalid"}
+    body = plan_without_version(plan)
+    return {**out, "result": "partly_sufficient", "reason": "zero_parts_and_narrower_plan",
+            "narrower_plan": body, "narrower_plan_fingerprint": plans.fingerprint(body),
+            "decision": dict(PARTLY_DECISION)}
+
+
+def counts_fingerprint(counts: list[Mapping]) -> str:
+    return hashlib.sha256(plans.canonical({"candidate_counts": counts}).encode("utf-8")).hexdigest()
+
+
+def run_narrowing(engine: Engine, run_id: int, answer: Answer) -> dict:
+    """Reads the structure counts (code role 'narrowing'), decides and stores the decision."""
+    try:
+        counts = role_input(bind_code(engine, run_id, ROLE))["candidate_counts"]
+    except AccessDenied as denied:
+        log_refusal(engine, run_id, ROLE, "run_narrowing", "stage_mismatch", denied.code)
+        raise Refused("run_narrowing", "stage_mismatch", denied.code) from None
+
+    def body(conn: Connection, stage: str):
+        if stage != "before_lock":
+            raise Refused("run_narrowing", "stage_mismatch")
+        row = conn.execute(_VERSION, dict(r=run_id)).one()
+        decision = decide(answer, counts, row.hypothesis_version_id, row.sufficiency_option)
+        output = {**decision, "counts_fingerprint": counts_fingerprint(counts),
+                  "sources": [{"source": c["source"], "version_fingerprint": c["version_fingerprint"],
+                               "readable": c["readable"]} for c in counts]}
+        code_stage(conn, run_id, "narrowing", {"claim_scope": answer.claim_scope}, output)
+        return output
+
+    return write(engine, run_id, ROLE, "run_narrowing", body)
+
+
+_VERSION = text("SELECT r.hypothesis_version_id, hv.sufficiency_option FROM run r JOIN hypothesis_version hv "
+                "ON hv.id = r.hypothesis_version_id WHERE r.id = :r")
diff --git a/hypocurate/pipeline/orchestrator.py b/hypocurate/pipeline/orchestrator.py
new file mode 100644
index 0000000..f5f5a10
--- /dev/null
+++ b/hypocurate/pipeline/orchestrator.py
@@ -0,0 +1,198 @@
+"""The orchestrator: one run, stage by stage (step 8b; PRD 3; the run order of the step 8 plan, corrected by the
+owner's answer A1; register 'run_order').
+
+    Planner -> narrowing decision (code, before any lock)
+      partly sufficient: Analyst (narrowing facts) -> copy_partly_sufficient -> narrower question; stop
+      claim not one plan: the run fails before the lock (A11)
+    -> rules lock -> store records -> Checks -> Critic -> Inclusion -> dataset freeze -> statistics
+    -> Analyst -> completion (copy_decision)
+
+A fixed-plan run bypasses the Planner (and the narrowing): the reference plan of criterion 14.1a, or, for a
+narrower question, exactly the narrower plan its original's narrowing decision stored (A8), after checking
+that the run's source versions are those the counts were taken on (B1).
+
+**Code decides everything** (CLAUDE.md, rule 1); each agent's answer is checked by code before it is used.
+**No model call runs inside a database transaction**: every step below uses its own short transactions, and
+the agents' stages are opened and closed around the request (`agents.runstage`).
+
+**Failures** (the step 8b failure table): a Planner failure, a domain mismatch, a claim that is not one plan,
+a refused checkpoint or write, a spending refusal at the Planner or the Critic, or changed source versions
+for a narrower question fail the run with a stated reason (`fail_run`). A Critic failure leaves flags
+unclassified and the run goes on (no decision reads the class). Any Analyst failure, a spending refusal
+included, leaves code's decision standing: the run completes with "explanation unavailable" (A3, B2). A call
+whose recording failed stays open; the database then refuses to end the run, which stays running for
+step 9's recovery, and `run` reports it.
+"""
+from __future__ import annotations
+
+import json
+from dataclasses import dataclass, field
+from typing import Any, Mapping
+
+from sqlalchemy import Connection, Engine, text
+
+from hypocurate.pipeline import analysis, checkpoints, checks, completion, extract, inclusion, narrowing, queries
+from hypocurate.pipeline import plan as plans
+from hypocurate.pipeline.agents import analyst, critic, planner
+from hypocurate.pipeline.writes import Refused, write
+
+SPENDING = ("spending_cap_run", "spending_cap_month", "ceiling_reached")
+# Fixed reasons of a failed run (failure_reason: "<code>: <reason>").
+REASONS = {
+    "planner_failed": "the Planner gave no usable plan",
+    "domain_mismatch": "the Planner judged that the claim belongs to another domain (PRD 5.5)",
+    "claim_not_one_plan": "the claim covers more than one temperature band, test type or alloy class; "
+                          "submit one question per band, test type and alloy class",
+    "narrowing_sources_changed": "the narrower question's source versions are not those its original's counts "
+                                 "were taken on",
+    "narrower_plan_missing": "the original's narrowing decision holds no narrower plan",
+    "spending_refused": "a spending cap or ceiling was reached before the request was sent",
+    "refused": "a checkpoint or write refused",
+}
+
+
+@dataclass
+class RunReport:
+    run_id: int
+    status: str = "running"
+    outcome: str | None = None
+    failure: str | None = None
+    stages: list = field(default_factory=list)
+    narrower_question: str | None = None
+    explanation: str | None = None
+
+
+def fail_run(engine: Engine, run_id: int, code: str, detail: str | None = None) -> str:
+    """Marks the run failed with "<code>: <reason>" (and the detail code, if any)."""
+    reason = f"{code}: {REASONS[code]}" + (f" ({detail})" if detail else "")
+
+    def body(conn: Connection, _stage: str):
+        conn.execute(text("UPDATE stage_result SET status = 'failed', finished_at = now() "
+                          "WHERE run_id = :r AND status = 'running'"), dict(r=run_id))
+        conn.execute(text("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r"),
+                     dict(f=reason[:500], r=run_id))
+
+    write(engine, run_id, "orchestrator", "fail_run", body)
+    return reason
+
+
+def _row(engine: Engine, run_id: int):
+    with engine.connect() as conn:
+        return conn.execute(text(
+            "SELECT r.status, r.fixed_plan, r.hypothesis_version_id, hv.sufficiency_option, h.narrower_of_run_id "
+            "FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
+            "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"), dict(r=run_id)).one()
+
+
+def _narrower_plan(engine: Engine, run_id: int, original: int, version_id: int) -> tuple[dict | None, str | None]:
+    """The narrower plan stored by the original's narrowing decision, for this run (A8), or a failure code."""
+    with engine.connect() as conn:
+        out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :o AND stage = 'narrowing' "
+                                "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(o=original)).scalar_one_or_none()
+        current = sorted(tuple(r) for r in conn.execute(text(
+            "SELECT s.key, sv.fingerprint FROM run_source rs JOIN source s ON s.id = rs.source_id "
+            "JOIN source_version sv ON sv.id = rs.source_version_id WHERE rs.run_id = :r"), dict(r=run_id)).all())
+    if not isinstance(out, dict) or not isinstance(out.get("narrower_plan"), dict):
+        return None, "narrower_plan_missing"
+    stored = sorted((s["source"], s["version_fingerprint"]) for s in out.get("sources") or [])
+    if stored != current:  # B1
+        return None, "narrowing_sources_changed"
+    body = out["narrower_plan"]
+    if plans.fingerprint(body) != out.get("narrower_plan_fingerprint"):
+        return None, "narrower_plan_missing"
+    return {"hypothesis_version": version_id, **body}, None
+
+
+def run(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> RunReport:
+    """Runs the run to its end (completed or failed), or leaves it running if a call stayed open."""
+    report = RunReport(run_id)
+    agent_kw = dict(ceiling=ceiling, client_options=client_options)
+    row = _row(engine, run_id)
+    if row.status == "queued":
+        queries.start(engine, run_id)
+    try:
+        if row.fixed_plan:
+            if row.narrower_of_run_id is not None:
+                plan, code = _narrower_plan(engine, run_id, row.narrower_of_run_id, row.hypothesis_version_id)
+                if code:
+                    return _failed(engine, report, code)
+            else:
+                plan = plans.reference_plan(row.hypothesis_version_id)
+                plan["sufficiency"]["option"] = row.sufficiency_option
+            report.stages.append("fixed plan")
+        else:
+            result = planner.run_planner(engine, run_id, **agent_kw)
+            report.stages.append("planner")
+            if result.failure is not None:
+                return _failed(engine, report, "spending_refused" if result.failure in SPENDING else "planner_failed",
+                               result.failure)
+            answer = result.answer
+            if not answer.domain_matches:
+                return _failed(engine, report, "domain_mismatch")
+            decision = narrowing.run_narrowing(engine, run_id, answer)
+            report.stages.append(f"narrowing: {decision['result']}")
+            if decision["result"] == "claim_not_one_plan":
+                return _failed(engine, report, "claim_not_one_plan", decision["reason"])
+            if decision["result"] == "partly_sufficient":
+                _explain(engine, report, agent_kw)
+                completion.copy_partly_sufficient(engine, run_id)
+                q = queries.create_narrower(engine, run_id, decision["narrower_scope"])
+                report.narrower_question = q.number
+                return _done(engine, report)
+            plan = planner.build_plan(row.hypothesis_version_id, answer.claim_scope, answer.outcome,
+                                      answer.exclusion_rules, row.sufficiency_option)
+        checkpoints.lock_rules(engine, run_id, plan)
+        report.stages.append("rules lock")
+        extract.store_records(engine, run_id)
+        checks.run_checks(engine, run_id)
+        report.stages += ["records stored", "checks"]
+        c = critic.run_critic(engine, run_id, **agent_kw)
+        report.stages.append("critic")
+        spent = [f for f in c.failures if f in SPENDING]
+        if spent:
+            return _failed(engine, report, "spending_refused", spent[0])
+        inclusion.decide_run(engine, run_id)
+        checkpoints.freeze_dataset(engine, run_id)
+        analysis.run_statistics(engine, run_id)
+        report.stages += ["inclusion", "dataset freeze", "statistics"]
+        _explain(engine, report, agent_kw)
+        completion.copy_decision(engine, run_id)
+        return _done(engine, report)
+    except Refused as refused:
+        return _failed(engine, report, "refused", refused.code)
+
+
+def _explain(engine: Engine, report: RunReport, agent_kw: Mapping) -> None:
+    """The Analyst: any failure leaves code's decision standing (A3, B2)."""
+    result = analyst.run_analyst(engine, report.run_id, **agent_kw)
+    report.stages.append("analyst")
+    report.explanation = result.report if result.failure is None else f"{analyst.UNAVAILABLE} ({result.failure})"
+
+
+def _done(engine: Engine, report: RunReport) -> RunReport:
+    with engine.connect() as conn:
+        row = conn.execute(text("SELECT status, outcome FROM run WHERE id = :r"), dict(r=report.run_id)).one()
+    report.status, report.outcome = row.status, row.outcome
+    return report
+
+
+def _failed(engine: Engine, report: RunReport, code: str, detail: str | None = None) -> RunReport:
+    try:
+        report.failure = fail_run(engine, report.run_id, code, detail)
+    except Refused as refused:  # a call still open (its recording failed): step 9 recovers the run
+        report.failure = f"{code} ({detail}); the run could not be ended: {refused.code}"
+    return _done(engine, report)
+
+
+def run_guarded(payload: dict) -> dict:
+    """The command line's run, in the guarded process. Only JSON-safe values cross back."""
+    from decimal import Decimal
+    from hypocurate.config import load_settings
+    from hypocurate.db.engine import make_engine
+    engine = make_engine(load_settings(web=False).database_url)
+    try:
+        ceiling = Decimal(payload["ceiling"]) if payload.get("ceiling") is not None else None
+        r = run(engine, int(payload["run_id"]), ceiling=ceiling, client_options=payload.get("client_options"))
+        return json.loads(json.dumps(r.__dict__, default=str))
+    finally:
+        engine.dispose()
diff --git a/hypocurate/pipeline/queries.py b/hypocurate/pipeline/queries.py
new file mode 100644
index 0000000..4683fc8
--- /dev/null
+++ b/hypocurate/pipeline/queries.py
@@ -0,0 +1,205 @@
+"""Queries: create, submit, confirm the domain, dispatch, start (PRD 3 steps 1-2; build step 8b).
+
+The command line (and later the website) creates and dispatches queries through these functions only.
+Every write follows the locking protocol (README, "Database migrations"): `run_transaction`, then
+`hc_write_lock(p_version => …)` before a version's rows change, version before run.
+
+- `create`: a new query (hypothesis) and its first version, a draft, with its domain, its chosen sources and
+  its data-sufficiency option (owner, A2: a parameter of the query, chosen before dispatch).
+- `submit`: draft -> submitted.
+- `confirm_domain`: a named person confirms (or changes) the domain while submitted (owner, A9: at the
+  command line `--by "<name>"` is required; the name goes into `review_comment` with the database's time).
+- `dispatch`: submitted and confirmed -> dispatched; a queued run that records, for every registered
+  source, its newest sealed version if chosen (else 'not_selected'), and the settings version of each run
+  role (`settings.RUN_ROLES`). A fixed-plan run (criterion 14.1a, or a narrower question's run, A8) records
+  `fixed_plan`. The database refuses an unsupported domain with its own message (PRD 5.5, 14.3).
+- `start`: queued -> running.
+- `create_narrower`: the narrower question of a run completed as partly sufficient (owner, Q10, A8): a
+  separate query linked to that run, created as submitted, with its original's domain, sources and option,
+  and a text built by code from `NARROWER_TEXT`.
+"""
+from __future__ import annotations
+
+import json
+from dataclasses import dataclass
+from typing import Iterable, Mapping
+
+from sqlalchemy import Connection, Engine, text
+
+from hypocurate.db.retry import run_transaction
+from hypocurate.pipeline.agents import settings as agent_settings
+
+LOCK_TIMEOUT_MS = 5000
+REVIEWER_MAX = 200
+# The narrower question's text (owner, A8; register 'narrower_question_text'): code-built, never a model's.
+NARROWER_TEXT = "{original} (narrower question: {scope})"
+CONSTRUCTED_MARK = "constructed_test_data"
+
+
+class QueryRefused(Exception):
+    """A query operation refused with a fixed code and a stated reason."""
+
+    def __init__(self, code: str, reason: str):
+        self.code, self.reason = code, reason
+        super().__init__(f"{code}: {reason}")
+
+
+@dataclass(frozen=True)
+class Query:
+    hypothesis_id: int
+    number: str
+    version_id: int
+
+
+def _lock_version(conn: Connection, version_id: int) -> str:
+    conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
+    return conn.execute(text("SELECT hc_write_lock(p_version => :v)"), dict(v=version_id)).scalar_one()
+
+
+def _domain_id(conn: Connection, key: str) -> int:
+    found = conn.execute(text("SELECT id FROM domain WHERE key = :k"), dict(k=key)).scalar_one_or_none()
+    if found is None:
+        raise QueryRefused("unknown_domain", f"no domain {key!r}")
+    return found
+
+
+def _source_ids(conn: Connection, keys: Iterable[str]) -> list[int]:
+    ids = []
+    for key in keys:
+        found = conn.execute(text("SELECT id FROM source WHERE key = :k"), dict(k=key)).scalar_one_or_none()
+        if found is None:
+            raise QueryRefused("unknown_source", f"no registered source {key!r}")
+        ids.append(found)
+    return ids
+
+
+def create(engine: Engine, claim: str, sources: Iterable[str], domain: str = "grain_size_strengthening",
+           sufficiency: str = "fixed_minimum", narrower_of_run: int | None = None) -> Query:
+    """A new query with one draft version."""
+    sources = list(dict.fromkeys(sources))
+    if not sources:
+        raise QueryRefused("no_source", "a query chooses at least one source")
+
+    def body(conn: Connection):
+        domain_id, source_ids = _domain_id(conn, domain), _source_ids(conn, sources)
+        h = conn.execute(text("INSERT INTO hypothesis (narrower_of_run_id) VALUES (:r) RETURNING id, number"),
+                         dict(r=narrower_of_run)).one()
+        vid = conn.execute(text(
+            "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id, sufficiency_option) "
+            "VALUES (:h, 1, :t, :d, :o) RETURNING id"), dict(h=h.id, t=claim, d=domain_id, o=sufficiency)).scalar_one()
+        for sid in source_ids:
+            conn.execute(text("INSERT INTO hypothesis_version_source VALUES (:v, :s)"), dict(v=vid, s=sid))
+        return Query(h.id, h.number, vid)
+
+    return run_transaction(engine, body)
+
+
+def submit(engine: Engine, version_id: int) -> None:
+    def body(conn: Connection):
+        _lock_version(conn, version_id)
+        conn.execute(text("UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v"),
+                     dict(v=version_id))
+
+    run_transaction(engine, body)
+
+
+def confirm_domain(engine: Engine, version_id: int, by: str, domain: str | None = None) -> None:
+    """A named person confirms the domain (or changes it to `domain`) while the version is submitted."""
+    if not isinstance(by, str) or not by.strip() or len(by.strip()) > REVIEWER_MAX:
+        raise QueryRefused("reviewer_missing", f"the reviewer's name is required (at most {REVIEWER_MAX} characters)")
+
+    def body(conn: Connection):
+        _lock_version(conn, version_id)
+        chosen = conn.execute(text("SELECT domain_id FROM hypothesis_version WHERE id = :v"),
+                              dict(v=version_id)).scalar_one()
+        domain_id = _domain_id(conn, domain) if domain else chosen
+        conn.execute(text("UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now(), "
+                          "review_comment = :c WHERE id = :v"),
+                     dict(d=domain_id, c=f"domain confirmed at the command line by {by.strip()}", v=version_id))
+
+    run_transaction(engine, body)
+
+
+def dispatch(engine: Engine, version_id: int, *, fixed_plan: bool = False, constructed_test_data: bool = False) -> int:
+    """Dispatches the version; returns the queued run's id."""
+    setting_ids = {role: agent_settings.ensure_setting(engine, role) for role in agent_settings.RUN_ROLES}
+
+    def body(conn: Connection):
+        _lock_version(conn, version_id)
+        conn.execute(text("UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v"),
+                     dict(v=version_id))
+        flags = json.dumps({CONSTRUCTED_MARK: True} if constructed_test_data else {})
+        rid = conn.execute(text("INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags) "
+                                "VALUES (:v, :f, CAST(:x AS jsonb)) RETURNING id"),
+                           dict(v=version_id, f=fixed_plan, x=flags)).scalar_one()
+        chosen = set(conn.execute(text("SELECT source_id FROM hypothesis_version_source WHERE hypothesis_version_id = :v"),
+                                  dict(v=version_id)).scalars())
+        for sid, key, latest in conn.execute(text(
+                "SELECT s.id, s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id "
+                "AND sv.sealed_at IS NOT NULL ORDER BY sv.id DESC LIMIT 1) FROM source s ORDER BY s.id")).all():
+            if sid in chosen:
+                if latest is None:
+                    raise QueryRefused("source_not_sealed", f"the chosen source {key!r} has no sealed version")
+                conn.execute(text("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
+                                  "VALUES (:r, :s, :sv, 'pending')"), dict(r=rid, s=sid, sv=latest))
+            else:
+                conn.execute(text("INSERT INTO run_source (run_id, source_id, search_status) "
+                                  "VALUES (:r, :s, 'not_selected')"), dict(r=rid, s=sid))
+        for role, setting in setting_ids.items():
+            conn.execute(text("INSERT INTO run_agent_setting (run_id, role, agent_setting_id) VALUES (:r, :o, :s)"),
+                         dict(r=rid, o=role, s=setting))
+        return rid
+
+    return run_transaction(engine, body)
+
+
+def start(engine: Engine, run_id: int) -> None:
+    def body(conn: Connection):
+        conn.execute(text(f"SET LOCAL lock_timeout = {LOCK_TIMEOUT_MS}"))
+        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id))
+        conn.execute(text("UPDATE run SET status = 'running', started_at = now() WHERE id = :r"), dict(r=run_id))
+
+    run_transaction(engine, body)
+
+
+def scope_in_words(scope: Mapping) -> str:
+    """A narrower scope in words, from its vocabulary values only."""
+    parts = []
+    for key, label in (("phase_class", "phase class"), ("test_type", "test type")):
+        if scope.get(key):
+            parts.append(f"{label} {', '.join(scope[key])}")
+    for band in scope.get("temperature_band") or []:
+        if isinstance(band, Mapping):
+            rng = f" ({band['min']:g} to {band['max']:g} °C)" if "min" in band else ""
+            parts.append(f"{band['band']}{rng}")
+        else:
+            parts.append(str(band))
+    return "; ".join(parts)
+
+
+def create_narrower(engine: Engine, original_run: int, narrower_scope: Mapping) -> Query:
+    """The narrower question of a run completed as partly sufficient, created as submitted (Q10)."""
+    with engine.connect() as conn:
+        row = conn.execute(text(
+            "SELECT hv.text, d.key AS domain, hv.sufficiency_option, hv.id AS vid FROM run r "
+            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
+            "JOIN domain d ON d.id = hv.confirmed_domain_id WHERE r.id = :r"), dict(r=original_run)).one()
+        sources = list(conn.execute(text(
+            "SELECT s.key FROM hypothesis_version_source hvs JOIN source s ON s.id = hvs.source_id "
+            "WHERE hvs.hypothesis_version_id = :v ORDER BY s.key"), dict(v=row.vid)).scalars())
+    q = create(engine, NARROWER_TEXT.format(original=row.text, scope=scope_in_words(narrower_scope)), sources,
+               domain=row.domain, sufficiency=row.sufficiency_option, narrower_of_run=original_run)
+    submit(engine, q.version_id)
+    return q
+
+
+def submitted_version(engine: Engine, number: str) -> int:
+    """The submitted version of query `number` (for `hypocurate dispatch Q-…`)."""
+    with engine.connect() as conn:
+        vid = conn.execute(text(
+            "SELECT hv.id FROM hypothesis h JOIN hypothesis_version hv ON hv.hypothesis_id = h.id "
+            "WHERE h.number = :n AND hv.status = 'submitted' ORDER BY hv.version_number DESC LIMIT 1"),
+            dict(n=number)).scalar_one_or_none()
+    if vid is None:
+        raise QueryRefused("not_submitted", f"query {number} has no submitted version to dispatch")
+    return vid
diff --git a/hypocurate/pipeline/statistics.py b/hypocurate/pipeline/statistics.py
index cf3d864..31d3c6f 100644
--- a/hypocurate/pipeline/statistics.py
+++ b/hypocurate/pipeline/statistics.py
@@ -118,6 +118,9 @@ EVIDENCE_LEVELS = MappingProxyType({
     2: "coefficient cannot be fitted",
     1: "no dataset frozen",
 })
+# Owner's addition 1 (2026-10-06; step 8b): a partly-sufficient original question is at level 1, shown as
+# this wording (it was never tested; code's narrowing decision proposed a narrower question).
+PARTLY_SUFFICIENT_WORDING = "original question not tested; a narrower question was proposed"
 STATE_LEVELS = MappingProxyType({"sufficient": 6, "exploratory": 5, "coefficient_only": 4, "below_minimums": 3,
                                  "not_fitted": 2, "no_dataset_frozen": 1})
 
diff --git a/hypocurate/pipeline/writes.py b/hypocurate/pipeline/writes.py
index eb15f99..da00ed5 100644
--- a/hypocurate/pipeline/writes.py
+++ b/hypocurate/pipeline/writes.py
@@ -65,6 +65,8 @@ CODES = {
     "statistics_failed": "the statistics could not be computed for this run (the error is in the refusal's message)",
     "decision_missing": "no stored decision for this run",
     "decision_not_current": "the stored decision belongs to a different freeze than the run's",
+    # Step 8b.
+    "narrowed": "code's narrowing decision is partly sufficient: the original question locks no plan",
 }
 CONSTRUCTED_MARK = "constructed_test_data"
 # Step 7 (owner, 2026-10-05; register 'constructed_test_runs'): TEST_RUN_LABEL, on every stored
````
## 3. New test files

### `tests/test_access_step8b.py`

```python
"""Step 8b, milestone 2: the access layer's changes (owner, 2026-10-07; safeguard changes, reviewed with 8b).

- the stage 'narrowed' (A4): a running run with no plan and code's narrowing decision of partly
  sufficient; the Analyst alone reads there; no plan can be locked there (code and database);
- the code role 'narrowing' (Q5): before the lock, `candidate_counts` only: counts of structure, no
  outcome value, no composition;
- the Analyst's facts (Q6): stored facts only, and below the minimums nothing computed from outcome
  values (the owner's standing requirement), shown on a real run through the pipeline.
The Analyst's lists, the Commentator's empty lists and the planted-value tests at each Analyst stage are
in test_access_layer.py and test_access_projected.py.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import access_world as aw
import pipeline_world as pw
from hypocurate.access import AccessDenied, bind, role_input
from hypocurate.access.dispatch import bind_code
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, checkpoints
from hypocurate.pipeline.plan import reference_plan
from hypocurate.pipeline.writes import Refused
from stats_world import run_on, small_rows


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def stage_of(engine, run_id):
    with engine.connect() as conn:
        from hypocurate.access.stage import actual_stage
        status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
        return actual_stage(conn, run_id, status)


# --- the stage 'narrowed' (A4) -----------------------------------------------------------------------

def test_a_narrowing_decision_of_partly_sufficient_moves_the_run_to_narrowed(engine):
    world = aw.build(engine, "before_lock")
    assert stage_of(engine, world.run) == "before_lock"
    aw.code_output(world.w, world.run, "narrowing", {"result": "proceed", "reason": "no_part_without_records"})
    assert stage_of(engine, world.run) == "before_lock"  # a decision to proceed leaves the lock open
    aw.code_output(world.w, world.run, "narrowing", {"result": "partly_sufficient"}, attempt=2)
    assert stage_of(engine, world.run) == "narrowed"


def test_at_narrowed_only_the_analyst_reads(engine):
    world = aw.build(engine, "narrowed")
    for role in ("planner", "critic", "commentator"):
        with pytest.raises(AccessDenied):
            role_input(bind(engine, world.run, world.settings[role]))
    assert set(role_input(bind(engine, world.run, world.settings["analyst"]))) == {
        "claim", "domain", "sources_meta", "coverage", "analyst_facts"}
    for role in ("narrowing", "inclusion", "checks", "statistics", "gap_facts"):
        with pytest.raises(AccessDenied):
            bind_code(engine, world.run, role)


def test_no_plan_is_locked_at_narrowed_by_code_or_by_the_database(engine):
    world = aw.build(engine, "narrowed")
    with engine.connect() as conn:
        vid = conn.execute(text("SELECT hypothesis_version_id FROM run WHERE id = :r"), dict(r=world.run)).scalar()
    with pytest.raises(Refused) as refused:
        checkpoints.lock_rules(engine, world.run, reference_plan(vid))
    assert refused.value.code == "narrowed"
    with pytest.raises(IntegrityError, match="no plan is locked after a narrowing decision"):
        aw.lock(world.w, world.run)


# --- the code role 'narrowing' (Q5) -------------------------------------------------------------------

def test_candidate_counts_are_counts_of_structure_only(engine):
    world = aw.build(engine, "before_lock")
    got = role_input(bind_code(engine, world.run, "narrowing"))
    assert set(got) == {"candidate_counts"}
    counts = got["candidate_counts"]
    assert [c["source"] for c in counts] == ["mpea", "tamu_fcc"]
    mpea, tamu = counts
    assert tamu["readable"] is False and len(tamu["version_fingerprint"]) == 64  # the world's placeholder file
    assert mpea["readable"] and mpea["n_records"] == 8 == sum(c["n"] for c in mpea["cells"])
    for cell in mpea["cells"]:
        assert set(cell) == {"categories", "test_temperature", "status", "grain_size_present", "n"}
        assert set(cell["categories"]) == {"phase_class", "test_type", "test_temperature_band"}
    text_of = json.dumps(got)
    for v in aw.PLANTED.values():
        assert str(v) not in text_of and repr(v) not in text_of
    assert "composition" not in text_of and "Co" not in text_of  # no composition, no alloy label


@pytest.mark.parametrize("world_stage", ["curation", "analysis", "closed_without_freeze", "narrowed"])
def test_the_narrowing_role_binds_only_before_the_lock(engine, world_stage):
    world = aw.build(engine, world_stage)
    with pytest.raises(AccessDenied) as denied:
        bind_code(engine, world.run, "narrowing")
    assert denied.value.code == "empty_list"


# --- the Analyst's facts on a real run (Q6; the owner's requirement below the minimums) ---------------

def analyst_input(engine, run_id):
    with engine.connect() as conn:
        setting = conn.execute(text("SELECT agent_setting_id FROM run_agent_setting WHERE run_id = :r "
                                    "AND role = 'analyst'"), dict(r=run_id)).scalar_one()
    return role_input(bind(engine, run_id, setting))


def stored_outcomes(engine, run_id) -> list[float]:
    with engine.connect() as conn:
        return [float(v) for v in conn.execute(text(
            "SELECT harmonized->'yield_strength'->>'value' FROM record WHERE extraction_run_id = :r"),
            dict(r=run_id)).scalars() if v is not None]


FROM_OUTCOMES = ("estimate", "std_error", "t", "df", "p_value", "p_value_description", "significant",
                 "estimated_power_estimated_noise")


def test_below_the_minimums_the_analysts_facts_hold_nothing_computed_from_outcomes(engine):
    rows = small_rows(3, papers=3, base=7311.0)  # distinctive outcome values
    rid = run_on(engine, rows, agents=("analyst",))
    out = analysis.run_statistics(engine, rid)
    assert out["withheld"] and out["decision"]["state"] == "below_minimums"
    got = analyst_input(engine, rid)
    facts = got["analyst_facts"]
    names = facts["names"]
    assert facts["kind"] == "analysis" and names["evidence_level"] == "3" and "verdict_wording" not in names
    # Owner, 2026-10-07: a run below the minimums offers no estimate names (no estimate, standard error, p-value or
    # paper figures under any name), and no calibration from estimated noise.
    assert not [k for k in names if k.endswith(("_estimate", "_std_error", "_p_phrase", "_figures_phrase"))]
    assert not [k for k in names if k.startswith("estimated_")]
    # The fixed-noise detection and false-positive shares use no outcome value: they stay (owner, 2026-10-07).
    assert names["fixed_detection"].endswith("%") and names["fixed_false_positive"].endswith("%")
    assert names["result_label"] == "data found; not enough to test"
    # Nothing beyond code's named display values: no record identity from the stored statistics output.
    found = [i for e in out["analyses"] for i in e.get("records_found") or []]
    assert found and not [i for i in found if i in json.dumps(facts)]
    text_of = json.dumps(got)
    values = stored_outcomes(engine, rid)
    assert len(values) == len(rows)
    for v in values:
        assert repr(v) not in text_of and f"{v:g}" not in text_of, v


def test_above_the_minimums_the_analysts_facts_carry_the_stored_estimate(engine):
    """Positive control for the test above: the same path, not withheld, carries the numbers."""
    rid = run_on(engine, small_rows(3, papers=3), option="use_available", agents=("analyst",))
    out = analysis.run_statistics(engine, rid)
    names = analyst_input(engine, rid)["analyst_facts"]["names"]
    stored = out["analyses"][0]
    # Step 8b (owner, 2026-10-07): named display strings and ready-made phrases, rounded by code.
    from hypocurate.pipeline import display
    assert names["pooled_estimate"] == display.coefficient(stored["estimate"])  # with its unit (owner, 2026-10-07)
    assert names["pooled_p_phrase"] == display.p_phrase(stored["p_value"])
    assert names["result_label"] == "exploratory" and names["verdict_wording"].endswith("in the sources searched")
    # Only display strings: no full-precision number from the stored statistics output.
    text_of = json.dumps(names)
    assert repr(stored["estimate"]) not in text_of and repr(stored["p_value"]) not in text_of
    assert names["fixed_false_positive"].endswith("%")
    assert names.get("estimated_false_positive", "%").endswith("%") and ("estimated_false_positive" in names
                                                                         or "estimated_unavailable" in names)


def test_the_analysts_facts_are_refused_until_code_has_stored_them(engine):
    rid = run_on(engine, small_rows(3, papers=3), agents=("analyst",))
    with pytest.raises(AccessDenied) as denied:
        analyst_input(engine, rid)
    assert denied.value.code == "facts_missing"
```
### `tests/test_analyst.py`

```python
"""Step 8b, milestone 6: the Analyst and its text checks (owner, Q6, Q8, A3, B2). Every model call goes to the
local stub provider."""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis
from hypocurate.pipeline.agents import analyst, text_checks
from hypocurate.pipeline.agents.settings import ANALYST_INSTRUCTION
from stats_world import run_on, small_rows

from hypocurate.pipeline import display

# Step 8b (owner, 2026-10-07, after the live set): the facts carry display strings and ready-made phrases; the
# number check compares tokens exactly (was: rounding to the shown precision accepted).
FACTS = display.display({"decision": {"outcome_wording": "sufficient in the sources searched", "verdict": "supported",
                                      "verdict_wording": "supported under the stated model, in the sources searched"},
                         "analyses": [{"estimate": 424.93, "std_error": 64.41, "n_records": 97, "detection": 0.0465,
                                       "largest_paper_share": 0.387,
                                       "p_value_phrase": display.p_phrase(1.287e-06),
                                       "paper_figures_phrase": display.figures_phrase(20, 3.9358, 0.38673, 19)}]})


def test_the_facts_carry_display_strings_and_phrases():
    a = FACTS["analyses"][0]
    assert (a["estimate"], a["std_error"], a["detection"], a["largest_paper_share"]) == ("424.9", "64.4", "4.7%", "38.7%")
    assert a["p_value_phrase"] == "p ≈ 1.3e-6 (approximate, nominal, one-sided)"
    assert a["paper_figures_phrase"] == ("20 informative groups, an effective number of groups of 3.94, a largest "
                                         "share of 38.7% and 19 degrees of freedom")  # 'groups' (owner, 2026-10-07)


@pytest.mark.parametrize("phrase", [
    "k = 424.9 ± 64.4", "97 records", "p ≈ 1.3e-6 (approximate, nominal, one-sided)", "4.7%",
    "38.7% of the slope information", "the model k × (grain size)^-1/2", "a 95% interval", "validity check 2",
    "an effective number of papers of 3.94",
])
def test_numbers_exactly_as_given_match(phrase):
    assert text_checks.unmatched_numbers(phrase, FACTS) == []


@pytest.mark.parametrize("phrase, bad", [
    ("p was 1.4e-6.", "1.4e-6"),  # scientific notation at the end of a sentence is one token
    ("k = 424.93", "424.93"), ("k is about 425", "425"), ("98 records", "98"), ("p = 1.4e-6", "1.4e-6"),
    ("4.65%", "4.65%"), ("0.387", "0.387"), ("1,000 records", "1000"), ("p = 1.3e-06", "1.3e-06"),
])
def test_a_number_not_given_as_shown_is_caught(phrase, bad):
    assert text_checks.unmatched_numbers(phrase, FACTS) == [bad]


# --- the wording check ------------------------------------------------------------------------------------

GOOD = "The result is sufficient in the sources searched, and k > 0 is supported under the stated model, in the " \
       "sources searched."
NONE = {"outcome_wording": "insufficient in the sources searched", "verdict": None}


@pytest.mark.parametrize("text_, decision, problems", [
    (GOOD, FACTS["decision"], []),
    ("The result is sufficient.", FACTS["decision"], ["outcome wording missing", "verdict wording missing"]),
    ("Insufficient in the sources searched: grain sizes do not exist for BCC alloys.", NONE,
     ["forbidden: do not exist"]),
    ("Insufficient in the sources searched, yet the claim is supported.", NONE,
     ["a verdict is stated where there is none"]),
    ("Insufficient in the sources searched; this proves nothing either way.", NONE, ["forbidden: proves"]),
    ("Insufficient in the sources searched. The supported model needs grain sizes.", NONE, []),
    (GOOD + " The pooled p ≈ 1.3e-6 (approximate, nominal, one-sided).", FACTS["decision"], []),
    # Owner, 2026-10-07: the word-based p-value and figures rules were removed (placeholders guarantee them).
    (GOOD + " The p-value is 1.3e-6.", FACTS["decision"], []),
    (GOOD + " The value 1.3e-6 is small.", FACTS["decision"], []),
    (GOOD + " It rests on 20 informative papers, an effective number of papers of 3.94, a largest share of 38.7% and "
            "19 degrees of freedom.", FACTS["decision"], []),
    (GOOD + " It rests on 20 informative papers.", FACTS["decision"], []),
    (GOOD + " The effective number is not a count of independent papers.", FACTS["decision"],
     ["the effective number described as independent"]),
])
def test_the_wording_rules(text_, decision, problems):
    assert text_checks.wording_problems(text_, decision, FACTS) == problems


# --- the Analyst's call -----------------------------------------------------------------------------------

@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def reply(report):
    return sp.reply(sp.fields(report=report))


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def names_of(engine, rid):
    """The named facts the Analyst is given for the run (through its access object)."""
    from hypocurate.access import bind, role_input
    setting = one(engine, "SELECT agent_setting_id FROM run_agent_setting WHERE run_id = :r AND role = 'analyst'",
                  r=rid)
    return role_input(bind(engine, rid, setting))["analyst_facts"]["names"]


def below_minimums(engine):
    rid = run_on(engine, small_rows(3, papers=3, base=7311.0), agents=("analyst",))
    analysis.run_statistics(engine, rid)
    return rid


# Step 8b (owner, 2026-10-07): the Analyst writes no digits; it refers to facts by name, and code renders the text.
BELOW = ("The outcome is {outcome_wording}: the pooled set has {pooled_records} records, below the minimum of "
         "{minimum_records}, so no test was run and no estimate is shown.")


def test_below_the_minimums_the_analysts_request_holds_no_outcome_value(engine, stub):
    rid = below_minimums(engine)
    stub.queue(reply(BELOW))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    names = names_of(engine, rid)
    expected = text_checks.render(BELOW, names)
    assert out.failure is None and out.report == expected
    assert expected.startswith("The outcome is insufficient in the sources searched: the pooled set has 6 records")
    raw = stub.requests[0]["raw"].decode()
    with engine.connect() as conn:
        values = [float(v) for v in conn.execute(text("SELECT harmonized->'yield_strength'->>'value' FROM record "
                                                      "WHERE extraction_run_id = :r"), dict(r=rid)).scalars()]
    for v in values:
        assert repr(v) not in raw and f"{v:g}" not in raw, v
    sent = json.loads(raw)
    assert "tools" not in sent and ANALYST_INSTRUCTION in json.dumps(sent, ensure_ascii=False)
    stored = one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id)
    assert stored["report"] == expected and stored["template"] == BELOW


def test_a_run_below_the_minimums_offers_no_estimate_names(engine):
    names = names_of(engine, below_minimums(engine))
    assert not [k for k in names if k.endswith(("_estimate", "_std_error", "_p_phrase", "_figures_phrase"))]
    assert "pooled_records" in names and "minimum_records" in names


@pytest.mark.parametrize("bad, code", [
    ("The outcome is {outcome_wording}: 31 records were found.", "digit_outside_placeholder"),
    ("The outcome is {outcome_wording}: the estimate is {pooled_estimate}.", "unknown_name"),  # withheld: no such name
    ("The outcome is {outcome_wording}, with {pooled_recordz} records.", "unknown_name"),
    ("The outcome is {outcome_wording}: grain sizes do not exist.", "wording_refused"),
    ("The outcome is {outcome_wording}, but the claim is supported.", "wording_refused"),
    ("The data were insufficient in the sources searched.", "wording_refused"),  # {outcome_wording} not used
])
def test_a_text_failing_a_check_twice_is_discarded(engine, stub, bad, code):
    rid = below_minimums(engine)
    stub.queue(reply(bad), reply(bad))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert (out.report, out.failure) == (None, code) and len(stub.requests) == 2
    retry = stub.requests[1]["raw"].decode()
    assert code in retry
    assert one(engine, "SELECT status FROM stage_result WHERE id = :s", s=out.stage_id) == "failed"
    assert one(engine, "SELECT output->>'shown' FROM stage_result WHERE id = :s", s=out.stage_id) == \
        f"explanation unavailable ({code})"
    assert one(engine, "SELECT output ? 'report' FROM stage_result WHERE id = :s", s=out.stage_id) is False


def test_a_corrected_text_is_stored(engine, stub):
    rid = below_minimums(engine)
    stub.queue(reply("The outcome is {outcome_wording}: 31 records."), reply(BELOW))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.report == text_checks.render(BELOW, names_of(engine, rid)) and len(stub.requests) == 2


def test_the_analyst_changes_no_stored_decision(engine, stub):
    rid = below_minimums(engine)
    before = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics'", r=rid)
    stub.queue(reply(BELOW))
    analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics'", r=rid) == before
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"


# --- above the minimums: the phrases, the owner's rules and the shape of the live diagnostic answer -------------

def exploratory(engine):
    """A run above the validity checks under 'use what is available': its facts hold the pooled estimate, its
    p-value phrase and its paper figures phrase."""
    rid = run_on(engine, small_rows(3, papers=3), option="use_available", agents=("analyst",))
    out = analysis.run_statistics(engine, rid)
    return rid, out["analyses"][0]


FOLLOWS_ALL = ("The data are {outcome_wording}, and the claim is {verdict_wording}. The pooled estimate is "
               "{pooled_estimate} ± {pooled_std_error}, with {pooled_p_phrase}. It rests on {pooled_figures_phrase}.")


def test_a_correct_text_is_accepted_and_rendered_with_the_exact_strings(engine, stub):
    rid, pooled = exploratory(engine)
    stub.queue(reply(FOLLOWS_ALL))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None and len(stub.requests) == 1
    c = pooled["counts"]
    assert f"The pooled estimate is {display.coefficient(pooled['estimate'])} ± {display.coefficient(pooled['std_error'])}, " \
           f"with {display.p_phrase(pooled['p_value'])}. It rests on " \
           f"{display.figures_phrase(c['n_groups_informative'], c['effective_papers'], c['largest_paper_share'], pooled['df'])}." \
           in out.report
    assert "{" not in out.report and "}" not in out.report


def diagnostic_shape(pooled):
    """The shape of the live diagnostic answer (2026-10-07): numbers written out at full precision."""
    c = pooled["counts"]
    return ("The data are {outcome_wording}, and the claim is {verdict_wording}. The estimated coefficient is "
            f"{pooled['estimate']!r}. The p-value is {pooled['p_value']!r}, an approximate, nominal, one-sided "
            f"cluster-robust p-value under the locked method. The support comes from {c['n_groups_informative']} "
            "informative papers.")


def test_the_diagnostic_answers_shape_is_refused_and_the_same_with_placeholders_is_stored(engine, stub):
    rid, pooled = exploratory(engine)
    old = diagnostic_shape(pooled)
    stub.queue(reply(old), reply(FOLLOWS_ALL))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert json.loads(stub.requests[1]["raw"])  # corrected once
    assert "digit_outside_placeholder" in stub.requests[1]["raw"].decode()
    assert out.failure is None and out.report == text_checks.render(FOLLOWS_ALL, names_of(engine, rid))


BREAKS = {
    "causes": (FOLLOWS_ALL + " Grain refinement causes the strengthening.", "wording_refused"),
    "caused by": (FOLLOWS_ALL + " The rise is caused by smaller grains.", "wording_refused"),
    "causal": (FOLLOWS_ALL + " The link is causal.", "wording_refused"),
    "confirms the claim": (FOLLOWS_ALL + " This confirms the claim.", "wording_refused"),
    "confirms the hypothesis": (FOLLOWS_ALL + " This confirms the hypothesis.", "wording_refused"),
    "effective number as independent": (FOLLOWS_ALL + " The effective number counts independent papers.",
                                        "wording_refused"),
    # Owner, 2026-10-07: with a verdict the pooled phrases are required (was: the word-based p-value and figures rules).
    "p-value phrase missing": (FOLLOWS_ALL.replace(", with {pooled_p_phrase}", ""), "result_phrases_missing"),
    "figures phrase missing": (FOLLOWS_ALL.replace(" It rests on {pooled_figures_phrase}.", ""), "result_phrases_missing"),
    "verdict not used": ("The data are {outcome_wording}.", "wording_refused"),
    "a digit": (FOLLOWS_ALL + " It used 97 records.", "digit_outside_placeholder"),
    "an unknown name": (FOLLOWS_ALL.replace("{pooled_estimate}", "{pooled_estimat}"), "unknown_name"),
}


@pytest.mark.parametrize("rule", sorted(BREAKS))
def test_a_text_breaking_each_rule_is_refused(engine, stub, rule):
    rid, _ = exploratory(engine)
    bad, code = BREAKS[rule]
    stub.queue(reply(bad), reply(bad))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert (out.report, out.failure) == (None, code) and len(stub.requests) == 2


# --- failure facts: counts or rule names only, never the answer's text ----------------------------------------

def details_of(engine, stage_id):
    return one(engine, "SELECT output->'failure_details' FROM stage_result WHERE id = :s", s=stage_id)


def test_an_unparsable_answer_stores_its_form_facts_and_no_text(engine, stub):
    rid = below_minimums(engine)
    prose = "ZQPROSE an explanation written without the field markers"
    stub.queue(sp.reply(prose), sp.reply(prose))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure == "malformed"
    details = details_of(engine, out.stage_id)
    assert details == [{"attempt": n, "parse": {"output_headers_present": {"report": False}, "completed_marker": False,
                                                "header_count": 0, "answer_empty": False}} for n in (1, 2)]
    assert "ZQPROSE" not in json.dumps(one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id))


def test_a_refused_text_stores_counts_or_rule_names_and_no_text(engine, stub):
    rid = below_minimums(engine)
    digits = "ZQDIG The outcome is {outcome_wording}; 12 and 34 records, {nosuch}."
    bad = "ZQBAD The outcome is {outcome_wording}; grain refinement causes strength."
    stub.queue(reply(digits), reply(bad))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure == "wording_refused"
    assert details_of(engine, out.stage_id) == [
        {"attempt": 1, "problems": [{"unknown_names": 1, "digits_outside_placeholders": 4, "required_missing": 0,
                                     "result_phrases_missing": 0}]},
        {"attempt": 2, "problems": ["forbidden: causes"]}]
    stored = json.dumps(one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id))
    assert "ZQDIG" not in stored and "ZQBAD" not in stored


# --- the named facts built by code (owner, 2026-10-07) ----------------------------------------------------------

from hypocurate.pipeline import analyst_names


def entry(key, estimate, p, scope="sensitivity", valid=True):
    return {"scope": scope, "set": key, "source": None, "estimate": estimate, "std_error": 10.0 if p else None,
            "p_value": p, "df": 9 if p else None, "checks": {"coefficient_fitted": estimate is not None,
                                                            "inference_valid": valid and p is not None},
            "counts": {"n_records": 30, "n_alloys": 5, "n_groups": 10, "n_groups_informative": 10,
                       "effective_papers": 6.5, "largest_paper_share": 0.2}, "withheld": False}


POOLED = entry("primary", 400.0, 1e-6, scope="pooled")


def test_the_sensitivity_sets_are_labelled_with_the_per_source_function():
    sets = [entry("no_exclusions", 410.0, 2e-6),                      # agrees
            entry("tension_and_compression", 120.0, 0.2),             # same direction, different decision
            entry("same_alloy_1_at_pct", -50.0, 0.9),                 # conflicts
            entry("six_batches_as_groups", 380.0, None, valid=False),  # not enough data
            entry("without_most_influential_paper", 390.0, 3e-5)]     # agrees
    out = analyst_names.sensitivity_summary([POOLED] + sets, POOLED, 0.05, withheld=False)
    assert (out["sensitivity_sets"], out["sensitivity_agrees"], out["sensitivity_same_direction_different_decision"],
            out["sensitivity_conflicts"], out["sensitivity_not_enough_data"]) == ("5", "2", "1", "1", "1")
    # Plain label wording and units (owner, 2026-10-07).
    assert out["sensitivity_not_agreeing"] == (
        "tension and compression (in the same direction as the pooled result, with a different test result); "
        "same alloy 1 at pct (in conflict with the pooled result (the opposite sign)); "
        "six batches as groups (not testable alone)")
    assert (out["sensitivity_smallest_estimate"], out["sensitivity_smallest_set"]) == ("-50.0 MPa·µm^0.5",
                                                                                      "same alloy 1 at pct")
    assert (out["sensitivity_largest_estimate"], out["sensitivity_largest_set"]) == ("410.0 MPa·µm^0.5", "no exclusions")
    assert out["without_largest_share_estimate"] == "390.0 MPa·µm^0.5"
    assert out["without_largest_share_label"] == "in agreement with the pooled result"
    assert out["without_largest_share_p_phrase"] == "p ≈ 3.0e-5 (approximate, nominal, one-sided)"


def test_a_withheld_result_gives_no_estimate_name_even_if_numbers_were_stored():
    """Behind the statistics (which store no number for a withheld result) the name builder refuses them too."""
    stats = {"decision": {"outcome_wording": "insufficient in the sources searched", "evidence_level": 3,
                          "evidence_level_wording": "below the minimums under the fixed option"},
             "withheld": True, "analyses": [POOLED, entry("per", 410.0, 2e-6, scope="per_source") | {"source": "mpea"},
                                            entry("no_exclusions", 410.0, 2e-6)]}
    plan = {"alpha": 0.05, "sufficiency_option": "fixed_minimum", "minimums": {"records": 30}}
    names = analyst_names.analysis_names(stats, {}, plan, {})
    assert not [k for k in names if k.endswith(("_estimate", "_std_error", "_p_phrase", "_figures_phrase"))]
    assert "pooled_records" in names and "mpea_records" in names



def test_the_words_p_value_and_paper_figures_are_allowed_now(engine, stub):
    """Owner, 2026-10-07: the two word-based rules are gone; the phrases carry the numbers."""
    rid, _ = exploratory(engine)
    text_ = FOLLOWS_ALL + " The p-value and the largest share above come from {pooled_groups} groups."
    stub.queue(reply(text_))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None and len(stub.requests) == 1


def test_without_a_verdict_the_pooled_phrases_are_not_required(engine, stub):
    rid = below_minimums(engine)
    stub.queue(reply(BELOW))
    assert analyst.run_analyst(engine, rid, client_options=sp.client_options(stub)).failure is None


def test_no_fact_name_exposes_a_bare_p_value_or_an_individual_paper_figure(engine):
    """Owner, 2026-10-07: a p-value and the paper figures (informative papers, effective number, largest share, degrees
    of freedom) exist only inside the phrase names."""
    rid, pooled = exploratory(engine)
    names = names_of(engine, rid)
    phrase_names = {k for k in names if k.endswith(("_p_phrase", "_figures_phrase"))}
    assert {"pooled_p_phrase", "pooled_figures_phrase"} <= phrase_names
    # No name for a figure on its own (the 'without_largest_share_' names are the set's own results, and resid_df the
    # residual degrees of freedom of the minimums, not the test's).
    assert not [k for k in names if k not in phrase_names and ("informative" in k or "effective" in k or "p_value" in k
                                                               or k.endswith(("_share", "_t_df")))]
    c = pooled["counts"]
    bare = {display.p_value(pooled["p_value"]), display.two_decimals(c["effective_papers"]),
            display.percent(c["largest_paper_share"])}
    for k, v in names.items():
        if k not in phrase_names:
            assert not set(text_checks.tokens(v)) & bare, (k, v)


@pytest.mark.parametrize("kind", ["exploratory", "withheld", "narrowed", "fixed wordings"])
def test_no_remaining_rule_fires_on_text_the_facts_supply(engine, kind):
    """Owner's review question, 2026-10-07: every code-built value, of each kind of run, and every fixed wording the
    facts can carry, passes the remaining wording rules when written into a text that uses the outcome (and verdict)."""
    from hypocurate.pipeline import calibration, narrowing
    from hypocurate.pipeline import statistics as st
    from hypocurate.pipeline.eligibility import INFLUENCE_DISPLAY_NAME
    from test_planner_narrowing import TWO_BANDS, NARROWER, answer_of, cell, counts
    if kind == "exploratory":
        names = names_of(engine, exploratory(engine)[0])
    elif kind == "withheld":
        names = names_of(engine, below_minimums(engine))
    elif kind == "narrowed":
        d = narrowing.decide(answer_of(claim_scope=TWO_BANDS, narrower=NARROWER),
                             counts(cell(n=5), cell(t=-196.0, gs=False)), 1, "fixed_minimum")
        names = analyst_names.narrowing_names(d)
    else:
        fixed = (list(calibration.FLAG_WORDING.values()) + list(st.EVIDENCE_LEVELS.values()) +
                 list(st.OUTCOME_WORDING.values()) + list(analyst_names.LABEL_WORDS.values()) +
                 [INFLUENCE_DISPLAY_NAME, st.BELOW_MINIMUMS_LABEL, st.EXPLORATORY_LABEL, st.PARTLY_SUFFICIENT_WORDING,
                  "missing evidence", "failed search", "insufficient groups", "evidence concentrated",
                  "uncertainty not estimable", "coefficient not fitted"])
        names = {"outcome_wording": "insufficient in the sources searched",
                 **{f"fixed_{LETTER}": w for LETTER, w in zip("abcdefghijklmnopqrstuvwxyz", [w for w in fixed if w])}}
    decision = {"outcome_wording": names["outcome_wording"], "verdict": "verdict_wording" in names,
                "verdict_wording": names.get("verdict_wording")}
    head = names["outcome_wording"] + (" " + names["verdict_wording"] if "verdict_wording" in names else "")
    for v in names.values():
        assert text_checks.wording_problems(f"{head}. {v}.", decision) == [], v


# --- owner's additions after reading a live explanation (2026-10-07): code-built sentences, units, plain names --

FW = "the method is over-confident on this data structure under the stated assumptions"


def cal(share, low, high, flag):
    return {"status": "computed", "null": {"share": share, "ci_low": low, "ci_high": high}, "flag_wording": flag}


@pytest.mark.parametrize("calibrations, ending", [
    ({"estimated": cal(0.082, 0.071, 0.095, FW), "fixed": cal(0.089, 0.077, 0.102, FW)}, f" Under both, {FW}."),
    ({"estimated": cal(0.082, 0.071, 0.095, FW), "fixed": cal(0.05, 0.04, 0.06, None)},
     f" Under noise levels estimated from the data, {FW}; under fixed illustrative noise levels, the share is consistent "
     "with the nominal level under the stated assumptions."),
])
def test_the_calibration_summary_covers_both_calibrations_and_their_flags(calibrations, ending):
    s = analyst_names.calibration_summary(calibrations, 0.05)
    assert s.startswith("In the simulation check, with noise levels estimated from the data, the test was significant "
                        "in 8.2% of simulations with no effect (7.1% to 9.5%, a 95% simulation interval covering "
                        "simulation uncertainty only); with fixed illustrative noise levels")
    assert "against a nominal level of 5.0%." in s and s.endswith(ending)


@pytest.mark.parametrize("estimate, note", [
    (424.9, "the estimate is positive, the direction the claim describes"),
    (-12.0, "the estimate is negative, opposite to the direction the claim describes"),
    (None, None),
])
def test_the_direction_note_is_built_from_the_sign_and_the_claims_direction(estimate, note):
    assert analyst_names.direction_note(estimate, "k > 0") == note


def test_the_plain_label_for_a_single_group_source():
    assert analyst_names.label_words({"label": "not_enough_data", "inference_reason": "insufficient_groups"}) == \
        "too few groups to test alone"
    assert analyst_names.label_words({"label": "agrees"}) == "in agreement with the pooled result"


def test_the_facts_carry_the_code_built_sentences_units_and_the_nominal_level(engine):
    rid, pooled = exploratory(engine)
    names = names_of(engine, rid)
    assert names["scope_source"] == analyst_names.FIXED_PLAN_SENTENCE  # the test world's runs use a fixed plan
    assert names["model_sentence"] == analyst_names.MODEL_SENTENCE
    assert names["group_definition"] == analyst_names.GROUP_DEFINITION
    assert names["direction_note"] == analyst_names.direction_note(pooled["estimate"], "k > 0")
    assert names["nominal_level"] == "5.0%" and "alpha" not in names
    assert names["pooled_estimate"].endswith(" MPa·µm^0.5") and names["pooled_std_error"].endswith(" MPa·µm^0.5")
    assert names["estimated_calibration_name"] == "noise levels estimated from the data"
    assert names["fixed_calibration_name"] == "fixed illustrative noise levels"
    assert names["fixed_scatter"].endswith(" MPa") and names["fixed_shift"].endswith(" MPa")
    assert names["fixed_false_positive_interval"].endswith(", a 95% simulation interval covering simulation "
                                                           "uncertainty only")
    assert names["calibration_summary"].startswith("In the simulation check, ")


SENTENCES = ("The claim is that yield strength rises as grain size falls. The outcome is {outcome_wording}, and the "
             "claim is {verdict_wording}, with {pooled_p_phrase}, from {pooled_figures_phrase}. {calibration_summary} "
             "{scope_source} {model_sentence} The pooled estimate is {pooled_estimate}; {direction_note}. "
             "{group_definition}")


def test_a_text_using_the_code_built_sentences_is_accepted(engine, stub):
    rid, _ = exploratory(engine)
    stub.queue(reply(SENTENCES))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None and out.report == text_checks.render(SENTENCES, names_of(engine, rid))


def test_the_failure_facts_of_a_corrected_attempt_are_stored(engine, stub):
    """Owner, 2026-10-07: also when a later attempt is accepted."""
    rid = below_minimums(engine)
    stub.queue(reply("ZQDIG The outcome is {outcome_wording}; 12 records."), reply(BELOW))
    out = analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
    assert out.failure is None
    stored = one(engine, "SELECT output FROM stage_result WHERE id = :s", s=out.stage_id)
    assert stored["attempts"] == ["digit_outside_placeholder", "ok"]
    assert stored["failure_details"] == [{"attempt": 1, "problems": [{"unknown_names": 0, "digits_outside_placeholders": 2,
                                                                      "required_missing": 0,
                                                                      "result_phrases_missing": 0}]}]
    assert "ZQDIG" not in json.dumps(stored)
```
### `tests/test_cli_runs.py`

```python
"""Step 8b, milestone 7: criteria 14.1 and 14.3 from the command line (`hypocurate run | dispatch | show`). Each
run executes in the guarded process; the model provider is the local stub, reached through the environment the
guarded child inherits (no live call)."""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate import cli
from hypocurate.db.engine import make_engine
from test_orchestrator import BCC, BCC_CLAIM, FCC_CLAIM, PARTLY, PARTLY_CLAIM, planner_body, responder


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database, monkeypatch, stub):
    monkeypatch.setenv("DATABASE_URL", migrated_database)
    monkeypatch.setenv("ANTHROPIC_API_BASE", stub.base_url)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", stub.base_url)
    monkeypatch.setenv("ANTHROPIC_API_KEY", sp.DUMMY_KEY)
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e
    e.dispose()


def hc(capsys, *argv):
    code = cli.main(list(argv))
    out, err = capsys.readouterr()
    return code, out, err


def report_of(out: str) -> dict:
    """The run's report: the JSON after the dispatch line."""
    first, rest = out.split("\n", 1)
    return {**json.loads(first), "report": json.loads(rest)}


def guard_refusals(engine, run_id):
    with engine.connect() as conn:
        return conn.execute(text("SELECT detail FROM audit_log WHERE run_id = :r AND NOT allowed "
                                 "AND detail->>'code' = 'file_guard'"), dict(r=run_id)).scalars().all()


def test_14_1a_run_with_the_fixed_plan_and_show_it(engine, stub, capsys):
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer")
    assert code == 0, err
    r = report_of(out)
    assert r["query"].startswith("Q-") and r["report"]["status"] == "completed" and r["report"]["outcome"] == "sufficient"
    assert guard_refusals(engine, r["run"]) == []
    code, out, err = hc(capsys, "show", str(r["run"]))
    shown = json.loads(out)
    assert shown["outcome"] == "sufficient in the sources searched"
    assert shown["verdict"] == "supported under the stated model, in the sources searched"
    pooled = next(x for x in shown["results"] if x["scope"] == "pooled")
    assert (pooled["n_records"], pooled["n_alloys"], pooled["n_groups"], pooled["resid_df"]) == (97, 22, 20, 74)
    assert round(pooled["estimate"], 1) == 424.9 and round(pooled["std_error"], 1) == 64.4
    assert shown["explanation_label"] == "model explanation; numbers checked against the run record"
    assert shown["tokens_and_cost"] is not None


def test_14_1b_run_with_the_planner(engine, stub, capsys):
    stub.respond(responder(planner_body()))
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    r = report_of(out)
    assert code == 0 and r["report"]["outcome"] == "sufficient" and "planner" in r["report"]["stages"]
    assert guard_refusals(engine, r["run"]) == []


def test_14_3_the_bcc_claim_from_the_command_line(engine, stub, capsys):
    stub.respond(responder(BCC))
    code, out, err = hc(capsys, "run", BCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    r = report_of(out)
    assert code == 0 and r["report"]["outcome"] == "insufficient"
    shown = json.loads(hc(capsys, "show", str(r["run"]))[1])
    assert shown["outcome"] == "insufficient in the sources searched" and shown["verdict"] is None
    assert shown["results"] == [] and shown["nothing_found"] == "missing_evidence"
    assert shown["evidence_level_wording"] == "no dataset frozen"


def test_14_3_partly_sufficient_and_the_narrower_question_from_the_command_line(engine, stub, capsys):
    stub.respond(responder(PARTLY))
    code, out, err = hc(capsys, "run", PARTLY_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
    r = report_of(out)
    assert code == 0 and r["report"]["outcome"] == "partly_sufficient"
    number = r["report"]["narrower_question"]
    shown = json.loads(hc(capsys, "show", str(r["run"]))[1])
    assert shown["outcome"] == "partly sufficient in the sources searched" and shown["narrower_question"] == number
    assert shown["evidence_level_wording"] == "original question not tested; a narrower question was proposed"
    code, out, err = hc(capsys, "dispatch", number, "--by", "Ada Reviewer")
    n = report_of(out)
    assert code == 0 and n["report"]["outcome"] == "sufficient" and n["report"]["stages"][0] == "fixed plan"
    narrower = json.loads(hc(capsys, "show", str(n["run"]))[1])
    assert narrower["narrower_question_of"] == r["query"] and narrower["plan"] == "fixed"


@pytest.fixture
def small(migrated_database, monkeypatch, stub):
    """A source below the fixed minimums: 3 alloys at two grain sizes, from 3 papers (or 1 paper)."""
    from stats_world import small_rows
    monkeypatch.setenv("DATABASE_URL", migrated_database)
    monkeypatch.setenv("ANTHROPIC_API_BASE", stub.base_url)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", stub.base_url)
    monkeypatch.setenv("ANTHROPIC_API_KEY", sp.DUMMY_KEY)
    e = make_engine(migrated_database)

    def register(papers):
        pw.registered_files(e, {"mpea": pw.mpea_csv(small_rows(3, papers=papers))})
    yield e, register
    e.dispose()


@pytest.mark.parametrize("papers, expected", [
    # Passes both validity checks, below the minimums: exploratory under 'use what is available', insufficient
    # (withheld) under the fixed minimum.
    (3, {"use_available": ("sufficient", True, 5), "fixed_minimum": ("insufficient", False, 3)}),
    # One paper: validity check 2 fails, so neither option gives a verdict.
    (1, {"use_available": ("insufficient", False, 4), "fixed_minimum": ("insufficient", False, 3)}),
])
def test_14_3_the_sufficiency_option_on_data_below_the_minimums(small, stub, capsys, papers, expected):
    engine, register = small
    register(papers)
    stub.respond(responder())
    got = {}
    for option in ("use_available", "fixed_minimum"):
        code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea", "--fixed-plan", "--sufficiency", option,
                            "--by", "Ada Reviewer")
        assert code == 0, err
        r = report_of(out)
        with engine.connect() as conn:
            got[option] = tuple(conn.execute(text("SELECT outcome, exploratory, evidence_level FROM run WHERE id = :r"),
                                             dict(r=r["run"])).one())
        shown = json.loads(hc(capsys, "show", str(r["run"]))[1])
        if got[option][1]:
            assert shown["label"] == "exploratory"
        if option == "fixed_minimum":
            assert shown["results"] == [] and shown["label"] == "data found; not enough to test"
    assert got == expected


def test_an_unsupported_domain_is_refused_and_the_message_says_why(engine, stub, capsys):
    code, out, err = hc(capsys, "run", "Fatigue life falls with porosity", "--sources", "mpea", "--domain", "fatigue",
                        "--by", "Ada Reviewer")
    assert code == 1 and "dispatch blocked: the confirmed domain is not supported yet" in err
    assert stub.requests == []


def test_a_run_needs_a_named_reviewer(engine, capsys):
    with pytest.raises(SystemExit) as exited:
        cli.main(["run", FCC_CLAIM, "--sources", "mpea"])
    assert exited.value.code == 2
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea", "--by", "  ")
    assert code == 1 and "reviewer_missing" in err


def test_show_an_unknown_run(engine, capsys):
    code, out, err = hc(capsys, "show", "999999")
    assert code == 1 and "no run 999999" in err


def test_14_3_a_source_that_cannot_be_read_is_a_failed_search_not_missing_evidence(small, stub, capsys):
    from stats_world import small_rows
    engine, _ = small
    pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3)), "tamu_fcc": b"not a workbook"})
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--sufficiency",
                        "use_available", "--by", "Ada Reviewer")
    r = report_of(out)
    shown = json.loads(hc(capsys, "show", str(r["run"]))[1])
    kinds = {s["source"]: (s["search_status"], s["kind"]) for s in shown["sources"]}
    assert kinds["tamu_fcc"] == ("failed", "failed_search")
    assert kinds["mpea"] == ("searched", None)  # its records are in the analysed set
    assert shown["outcome"] == "sufficient in the sources searched"


def test_14_1_the_controlled_duplicates_in_a_marked_test_run(engine, stub, capsys):
    """The constructed extract enters only a run marked as a test; its overlapping records are flagged, kept in
    the store and counted once; the run carries the test-run label."""
    pw.registered(engine, ("controlled_duplicates",))
    stub.respond(responder())
    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,controlled_duplicates", "--fixed-plan",
                        "--test-data", "--by", "Ada Reviewer")
    assert code == 0, err
    rid = report_of(out)["run"]
    with engine.connect() as conn:
        flags = conn.execute(text("SELECT kind, count(*) FROM flag WHERE run_id = :r GROUP BY kind"), dict(r=rid)).all()
        stored = conn.execute(text("SELECT count(*) FROM record WHERE extraction_run_id = :r"), dict(r=rid)).scalar()
        label = conn.execute(text("SELECT DISTINCT test_run_label FROM analysis_result WHERE run_id = :r"),
                             dict(r=rid)).scalars().all()
        once = conn.execute(text("SELECT count(*) FROM run_record WHERE run_id = :r AND rule = 'duplicate_counted_once'"),
                            dict(r=rid)).scalar()
    assert dict(flags).get("exact_duplicate", 0) + dict(flags).get("possible_duplicate", 0) > 0
    assert once > 0 and stored > once  # kept in the store, counted once
    assert label == ["test run: includes constructed data"]
    assert any("[[ ## classification ## ]]" in r["raw"].decode() for r in stub.requests)  # the Critic was asked
```
### `tests/test_critic.py`

```python
"""Step 8b, milestone 5: the Critic (owner, A7) and the owner's standing requirement that no code decision reads
the Critic's class. Every model call goes to the local stub provider."""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate.access.vocabulary import CRITIC_CLASSES
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, checkpoints, checks, extract, inclusion, queries
from hypocurate.pipeline.agents import critic
from hypocurate.pipeline.agents.settings import CRITIC_INSTRUCTION
from stats_world import plan_for, small_rows

import hypocurate

PACKAGE = Path(hypocurate.__file__).resolve().parent  # the code under test (a mutation copy too)
# Two records whose tensile strength is below their yield strength: Checks raises an invalid-value flag on
# each (flags between records are raised across sources only). Distinctive numbers, for the planted test.
CONFLICT = [{**pw.mpea_row("CoCrNi", 2.0, 7311.375, doi="10.1016/j.test.2026.001"), "PROPERTY: UTS (MPa)": "5511.25"},
            {**pw.mpea_row("CoCrNi", 4.0, 8911.625, doi="10.1016/j.test.2026.002"), "PROPERTY: UTS (MPa)": "4411.5"}]


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered_files(e, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT)})
    yield e
    e.dispose()


def version(engine):
    q = queries.create(engine, "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
                       ("mpea",))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    return q.version_id


def checked_run(engine, vid):
    """A run of version `vid` through Checks: its flags are raised, nothing decided yet."""
    if not one(engine, "SELECT count(*) FROM run WHERE hypothesis_version_id = :v", v=vid):
        rid = queries.dispatch(engine, vid)
    else:
        rid = pw.run_of_version(engine, vid, ("mpea",), agents=("planner", "critic", "analyst"))
    if one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued":
        queries.start(engine, rid)
    checkpoints.lock_rules(engine, rid, plan_for(vid))
    extract.store_records(engine, rid)
    checks.run_checks(engine, rid)
    return rid


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def rows(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def flag_ids(engine, rid):
    return [r[0] for r in rows(engine, "SELECT id FROM flag WHERE run_id = :r ORDER BY id", r=rid)]


def reply(entries):
    return sp.reply(sp.fields(classification=json.dumps(entries)))


def run_critic(engine, rid, stub):
    return critic.run_critic(engine, rid, client_options=sp.client_options(stub))


# --- the request and the answer --------------------------------------------------------------------------

def test_the_critics_complete_request_holds_no_compared_number_or_outcome(engine, stub):
    rid = checked_run(engine, version(engine))
    flags = flag_ids(engine, rid)
    assert flags  # the conflicting pair raised at least one flag
    stub.queue(reply({str(f): {"class": "cannot_tell", "reason": "the metadata are the same"} for f in flags}))
    run_critic(engine, rid, stub)
    raw = stub.requests[0]["raw"].decode()
    for v in ("7311.375", "8911.625", "7311.4", "8911.6", "5511.25", "4411.5"):
        assert v not in raw, v
    assert "compared_values" not in raw and "tools" not in json.loads(raw)
    assert CRITIC_INSTRUCTION in json.dumps(json.loads(raw), ensure_ascii=False)
    assert "physically impossible" in raw and "invalid_value" in raw  # the kind and category are told


def test_each_valid_entry_is_written_once_and_an_invalid_one_is_left_unclassified(engine, stub):
    rid = checked_run(engine, version(engine))
    flags = flag_ids(engine, rid)
    good, *rest = flags
    answer = {str(good): {"class": "same_measurement", "reason": "same DOI, alloy and grain size"},
              "999999": {"class": "cannot_tell"}}
    for f in rest:
        answer[str(f)] = {"class": "agrees"}  # not an allowed class
    stub.queue(reply(answer))
    out = run_critic(engine, rid, stub)
    assert len(stub.requests) == 1  # per-entry refusals are not retried
    assert rows(engine, "SELECT critic_class, critic_reason FROM flag WHERE id = :f", f=good) == [
        ("same_measurement", "same DOI, alloy and grain size")]
    assert out.refused["999999"] == "unknown_flag"
    for f in rest:
        assert out.refused[str(f)] == "class_not_allowed"
        assert one(engine, "SELECT critic_class FROM flag WHERE id = :f", f=f) is None


@pytest.mark.parametrize("entry, code", [({"class": "cannot_tell", "reason": "x" * 301}, "reason_not_allowed"),
                                         ({"class": "cannot_tell", "reason": "  "}, "reason_not_allowed"),
                                         ({"class": "cannot_tell", "extra": 1}, "malformed_entry"),
                                         ("cannot_tell", "malformed_entry")])
def test_a_reason_is_never_truncated_and_an_entry_has_a_fixed_form(entry, code):
    got = critic.classify({"7": entry}, [{"id": 7, "records": []}])
    assert got.refused == {"7": code} and not got.accepted


def test_a_malformed_answer_is_corrected_once_then_every_flag_stays_unclassified(engine, stub):
    rid = checked_run(engine, version(engine))
    stub.queue(sp.reply(sp.fields(classification="the first flag looks like a duplicate")),
               sp.reply(sp.fields(classification="still prose")))
    out = run_critic(engine, rid, stub)
    assert out.failures == ["malformed"] and len(stub.requests) == 2
    assert one(engine, "SELECT count(*) FROM flag WHERE run_id = :r AND critic_class IS NOT NULL", r=rid) == 0
    assert one(engine, "SELECT status FROM stage_result WHERE id = :s", s=out.stages[0]) == "failed"


def test_flags_are_sent_in_batches():
    data = {"flags_kind": [{"id": i, "records": []} for i in range(7)]}
    assert [len(b) for b in critic.batches(data, 3)] == [3, 3, 1]


def test_with_no_flag_nothing_is_sent(migrated_database, stub):
    engine = make_engine(migrated_database)
    pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3))})
    rid = checked_run(engine, version(engine))
    assert flag_ids(engine, rid) == []
    out = run_critic(engine, rid, stub)
    assert stub.requests == [] and out.classified == 0
    assert one(engine, "SELECT status FROM stage_result WHERE id = :s", s=out.stages[0]) == "skipped"


# --- no code decision reads the Critic's class (the owner's standing requirement) -----------------------

def decided(engine, rid):
    """Everything code decides after the Critic: the eligibility decisions and sets by stable identity, the
    freeze record and its fingerprint, and the stored statistics and gap facts."""
    inclusion.decide_run(engine, rid)
    freeze = checkpoints.freeze_dataset(engine, rid)
    # The freeze record names the most influential group's records by database id (not part of the
    # fingerprint), which differs between any two runs: compared here by stable identity.
    influential = freeze.get("most_influential") or {}
    if "records" in influential:
        influential["records"] = [one(engine, "SELECT source_item_key || ':' || item_index FROM record WHERE id = :i",
                                      i=i) for i in influential["records"]]
    analysis.run_statistics(engine, rid)
    identity = "rec.source_item_key || ':' || rec.item_index"
    return {
        "decisions": rows(engine, f"SELECT {identity}, rr.eligible, rr.rule FROM run_record rr JOIN record rec "
                                  f"ON rec.id = rr.record_id WHERE rr.run_id = :r ORDER BY 1", r=rid),
        "sets": rows(engine, f"SELECT a.key, {identity} FROM analysis_set a JOIN analysis_set_record asr ON "
                             f"asr.analysis_set_id = a.id JOIN record rec ON rec.id = asr.record_id "
                             f"WHERE a.run_id = :r ORDER BY 1, 2", r=rid),
        "freeze": freeze,
        "statistics": one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics'", r=rid),
        "gap_facts": one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid),
    }


def test_changing_every_class_changes_no_decision_set_fingerprint_or_result(engine):
    vid = version(engine)
    plain = checked_run(engine, vid)
    classified = checked_run(engine, vid)
    flags = flag_ids(engine, classified)
    assert flags
    rng = random.Random(8)
    with engine.begin() as conn:
        for f in flags:
            conn.execute(text("UPDATE flag SET critic_class = :c, critic_reason = 'random', classified_at = now() "
                              "WHERE id = :f"), dict(c=rng.choice(sorted(CRITIC_CLASSES)), f=f))
    a, b = decided(engine, plain), decided(engine, classified)
    assert a["freeze"]["fingerprint"] == b["freeze"]["fingerprint"]
    assert a == b


def test_no_decision_path_reads_the_critics_class():
    """A source scan behind the test above: outside the Critic's own module, only `flags_full` (a field on no
    role's list until step 12) reads the class; no pipeline module does."""
    readers = []
    for path in PACKAGE.rglob("*.py"):
        rel = "hypocurate/" + path.relative_to(PACKAGE).as_posix()
        if "/migrations/" in rel or rel in ("hypocurate/db/models.py", "hypocurate/access/vocabulary.py"):
            continue
        if re.search(r"critic_class|critic_reason", path.read_text()):
            readers.append(rel)
    assert sorted(readers) == ["hypocurate/access/fields.py", "hypocurate/pipeline/agents/critic.py"]
    fields = (PACKAGE / "access/fields.py").read_text()
    uses = [m.start() for m in re.finditer(r"critic_class", fields)]
    start = fields.index("def flags_full(")
    end = fields.index("\ndef ", start + 1)
    assert uses and all(start <= u < end for u in uses)
```
### `tests/test_migrations_step8b.py`

```python
"""Step 8b: migration 0006 (approved by the owner on 2026-10-07, subject to the second-model review).

0001 to 0005 untouched; no earlier function is replaced (each new rule is its own function and
trigger, named to fire after the earlier one on the same table and event); up, down, up gives the
same schema; the downgrade refuses while a query uses another option than the default; a failed
upgrade changes nothing. Then the rules 0006 adds, each with an allowed and a refused case:
- the query's sufficiency option (owner, A2): on the version, fixed once submitted, the original's on a
  narrower question, and the plan's must equal it;
- partly sufficient (owner, A5): only with no plan, no stored record and a done narrowing decision of
  partly sufficient; and no plan after such a decision;
- the Critic's class from its fixed list and its reason bounded (owner, A7)."""
from __future__ import annotations

import pytest
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, ProgrammingError

from hypocurate.access.vocabulary import CRITIC_CLASSES, CRITIC_REASON_MAX
from hypocurate.db import models
from hypocurate.db import migrate
from hypocurate.db.engine import make_engine
from model_builder import FP, World
from test_migrations import assert_schema_is_empty, snapshot
from test_migrations_step6 import body

SCRIPTS = ScriptDirectory(str(migrate.MIGRATIONS))
M0001 = SCRIPTS.get_revision("0001").module


def m0006():
    """Migration 0006's module (looked up when a test runs, so each test fails alone where it is absent)."""
    return SCRIPTS.get_revision("0006").module


@pytest.fixture
def engine(empty_database):
    e = make_engine(empty_database)
    yield e
    e.dispose()


@pytest.fixture
def w(db):
    return World(db)


# --- the migration -------------------------------------------------------------------------------

def test_0006_is_the_head_and_follows_0005():
    assert migrate.head_revision() == "0006" and m0006().down_revision == "0005"


def test_0006_replaces_no_earlier_function():
    earlier = {f.split("(")[0] for m in ("0001", "0002", "0003", "0004", "0005")
               for f in getattr(SCRIPTS.get_revision(m).module, "FUNCTION_NAMES", [])}
    assert not {f.split("(")[0] for f in m0006().FUNCTION_NAMES} & earlier
    assert "CREATE OR REPLACE" not in " ".join(m0006().FUNCTIONS)


@pytest.mark.parametrize("table, earlier", [("hypothesis_version", "hc_version_insert"),
                                            ("hypothesis_version", "hc_version_update"),
                                            ("plan", "hc_plan_insert"), ("run", "hc_run_update")])
def test_each_new_trigger_fires_after_the_earlier_one_on_its_table(table, earlier):
    """PostgreSQL fires BEFORE triggers in name order: 0001's messages keep their priority."""
    names = [t for tb, _, t, _ in m0006().CHECKED if tb == table and t.startswith(earlier)]
    assert names and all(n > earlier for n in names)


def test_the_critic_classes_are_the_codes_of_the_vocabulary():
    assert m0006().CRITIC_CLASSES == models.CRITIC_CLASSES == tuple(sorted(CRITIC_CLASSES))
    assert m0006().CRITIC_REASON_MAX == models.CRITIC_REASON_MAX == CRITIC_REASON_MAX


def test_up_down_up_restores_0005(engine):
    migrate.upgrade(engine, "0005")
    at_0005 = snapshot(engine)
    migrate.upgrade(engine)
    first = snapshot(engine)
    migrate.downgrade(engine, "0005")
    assert snapshot(engine) == at_0005
    migrate.upgrade(engine)
    assert snapshot(engine) == first
    migrate.downgrade(engine, "base")
    assert_schema_is_empty(engine)


def test_a_failed_upgrade_changes_nothing(engine):
    migrate.upgrade(engine, "0005")
    with engine.begin() as conn:
        conn.execute(text("CREATE FUNCTION hc_run_partly_sufficient() RETURNS int LANGUAGE sql AS 'SELECT 1'"))
    before = snapshot(engine)
    with pytest.raises(ProgrammingError, match="already exists"):
        migrate.upgrade(engine)
    assert snapshot(engine) == before
    assert migrate.current_revision(engine) == "0005"


def test_the_downgrade_refuses_while_a_query_uses_another_option(db):
    w = World(db)
    w.draft(sufficiency="use_available")
    before = snapshot(db)
    with pytest.raises(Exception, match="0006 is in use"):
        migrate.downgrade(db, "0005")
    assert snapshot(db) == before and migrate.current_revision(db) == "0006"


# --- the query's sufficiency option (A2) ---------------------------------------------------------

def test_a_version_without_an_option_uses_the_default(w):
    """The previous release's code inserts versions without the option."""
    vid = w.val("INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
                "VALUES (:h, 1, 'claim', :d) RETURNING id", h=w.hypothesis(), d=w.domain["grain_size_strengthening"])
    assert w.val("SELECT sufficiency_option FROM hypothesis_version WHERE id = :v", v=vid) == "fixed_minimum"


def test_the_option_comes_from_the_fixed_list(w):
    with pytest.raises(IntegrityError, match="ck_hypothesis_version_sufficiency_option"):
        w.draft(sufficiency="power_based")


def test_the_option_can_change_while_a_draft_and_never_after(w):
    vid = w.draft()
    w.run_sql("UPDATE hypothesis_version SET sufficiency_option = 'use_available' WHERE id = :v", v=vid)
    w.submit(vid)
    w.rejected("UPDATE hypothesis_version SET sufficiency_option = 'fixed_minimum' WHERE id = :v",
               "sufficiency option is fixed once the version is submitted", v=vid)


def test_a_narrower_question_has_its_originals_option(w):
    original = partly_run(w, sufficiency="use_available")
    h = w.hypothesis(narrower_of=original)
    w.rejected("INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
               "VALUES (:h, 1, 'narrower', :d)", "the sufficiency option of its original",
               h=h, d=w.domain["grain_size_strengthening"])
    vid = w.draft(hypothesis=h, sufficiency="use_available")
    w.rejected("UPDATE hypothesis_version SET sufficiency_option = 'fixed_minimum' WHERE id = :v",
               "the sufficiency option of its original", v=vid)


@pytest.mark.parametrize("query, plan, refused", [("fixed_minimum", "fixed_minimum", False),
                                                  ("use_available", "use_available", False),
                                                  ("fixed_minimum", "use_available", True),
                                                  ("use_available", "fixed_minimum", True)])
def test_the_plans_option_is_the_querys(w, query, plan, refused):
    rid = w.running(sufficiency=query)
    if refused:
        with pytest.raises(IntegrityError, match="the plan's sufficiency option is the query's"):
            w.lock(rid, option=plan)
    else:
        w.lock(rid, option=plan)
        assert w.val("SELECT sufficiency_option FROM plan WHERE run_id = :r", r=rid) == plan


def test_the_plans_own_option_check_still_refuses_an_unknown_option(w):
    """Behind the new trigger (which fires first, before any CHECK), 0001's CHECK still holds:
    reached here with the new trigger disabled in this transaction only."""
    rid = w.running()
    with w.e.begin() as conn:
        conn.execute(text("ALTER TABLE plan DISABLE TRIGGER hc_plan_insert_query"))
        with pytest.raises(IntegrityError, match="ck_plan_sufficiency_option"):
            with conn.begin_nested():
                conn.execute(text("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, "
                                  "min_alloys, min_groups, min_resid_df) VALUES (:r, '{}', :fp, 'power_based', "
                                  "30, 5, 10, 10)"), dict(r=rid, fp=FP))
        conn.execute(text("ALTER TABLE plan ENABLE TRIGGER hc_plan_insert_query"))


# --- partly sufficient (A5) ---------------------------------------------------------------------

def narrowing(w, rid, result="partly_sufficient", status="done"):
    """A code stage result of the narrowing decision (role NULL), as `writes.code_stage` writes it."""
    sid = w.stage(rid, "narrowing", None)
    if status != "running":
        w.run_sql("UPDATE stage_result SET status = :st, finished_at = now(), output = CAST(:o AS jsonb) "
                  "WHERE id = :s", st=status, o=f'{{"result": "{result}"}}', s=sid)
    return sid


def complete_partly(w, rid):
    w.complete(rid, "partly_sufficient", level=1)


def partly_run(w, sufficiency="fixed_minimum"):
    rid = w.running(sufficiency=sufficiency)
    narrowing(w, rid)
    complete_partly(w, rid)
    return rid


def test_a_run_completes_as_partly_sufficient_with_its_narrowing_decision_and_no_plan(w):
    rid = partly_run(w)
    assert w.rows("SELECT status, outcome, verdict, evidence_level FROM run WHERE id = :r", r=rid) == [
        ("completed", "partly_sufficient", None, 1)]


@pytest.mark.parametrize("shape", ["none", "proceed", "running", "failed"])
def test_partly_sufficient_needs_a_done_narrowing_decision_of_partly_sufficient(w, shape):
    rid = w.running()
    if shape == "proceed":
        narrowing(w, rid, result="proceed")
    elif shape == "running":
        narrowing(w, rid, status="running")
    elif shape == "failed":
        narrowing(w, rid, status="failed")
    if shape == "running":  # a running stage blocks any end first (0001); finish it as failed instead
        w.run_sql("UPDATE stage_result SET status = 'failed', finished_at = now() WHERE run_id = :r", r=rid)
    w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
               "evidence_level = 1 WHERE id = :r", "partly sufficient needs a narrowing decision", r=rid)


def test_partly_sufficient_is_refused_for_a_run_with_a_plan(w):
    rid = w.running()
    w.lock(rid)
    narrowing(w, rid)  # written after the lock by direct SQL: the database still refuses the outcome
    w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
               "evidence_level = 1 WHERE id = :r", "partly sufficient is only for a run with no plan", r=rid)


def test_no_plan_is_locked_after_a_narrowing_decision_of_partly_sufficient(w):
    rid = w.running()
    narrowing(w, rid)
    with pytest.raises(IntegrityError, match="no plan is locked after a narrowing decision of partly sufficient"):
        w.lock(rid)


def test_a_narrowing_decision_to_proceed_allows_the_lock(w):
    rid = w.running()
    narrowing(w, rid, result="proceed")
    w.lock(rid)
    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1


@pytest.mark.parametrize("outcome", ["insufficient", "sufficient"])
def test_other_outcomes_are_unaffected_by_the_new_rule(w, outcome):
    """'insufficient' completes as before; 'sufficient' keeps 0001's own refusal."""
    rid, sets, _ = w.frozen()
    if outcome == "insufficient":
        w.complete(rid, "insufficient", level=1)
        assert w.val("SELECT outcome FROM run WHERE id = :r", r=rid) == "insufficient"
    else:
        w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'sufficient', "
                   "verdict = 'supported', evidence_level = 6 WHERE id = :r", "exactly one pooled result", r=rid)


# --- the Critic's class and reason (A7) -----------------------------------------------------------

def a_flag(w):
    rid = w.locked()
    return rid, w.val("INSERT INTO flag (run_id, kind, category) VALUES (:r, 'values_disagree', "
                      "'differ beyond tolerance') RETURNING id", r=rid)


@pytest.mark.parametrize("cls", sorted(CRITIC_CLASSES))
def test_each_critic_class_is_accepted(w, cls):
    _, fid = a_flag(w)
    w.run_sql("UPDATE flag SET critic_class = :c, critic_reason = 'same DOI and composition', "
              "classified_at = now() WHERE id = :f", c=cls, f=fid)


@pytest.mark.parametrize("cls, reason, match", [
    ("agrees", None, "ck_flag_critic_class"),
    ("same_measurement", "x" * 301, "ck_flag_critic_reason"),
    ("same_measurement", "   ", "ck_flag_critic_reason"),
])
def test_a_class_outside_the_list_or_an_unbounded_reason_is_refused(w, cls, reason, match):
    _, fid = a_flag(w)
    w.rejected("UPDATE flag SET critic_class = :c, critic_reason = :r, classified_at = now() WHERE id = :f",
               match, c=cls, r=reason, f=fid)


def test_a_reason_needs_a_class(w):
    _, fid = a_flag(w)
    w.rejected("UPDATE flag SET critic_reason = 'a reason' WHERE id = :f", "ck_flag_critic_reason", f=fid)


def test_a_class_without_a_reason_is_allowed(w):
    _, fid = a_flag(w)
    w.run_sql("UPDATE flag SET critic_class = 'cannot_tell', classified_at = now() WHERE id = :f", f=fid)
```
### `tests/test_no_live_calls.py`

```python
"""Step 8b: the regression suite makes no live model call (owner's standing requirement). The test process and every
guarded child it starts have no provider credential, and the provider's address is a closed local port
(tests/conftest.py); a call that does not name the stub can therefore never leave the machine."""
from __future__ import annotations

import os

import pytest

import pipeline_world as pw
from conftest import NO_PROVIDER
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queries
from hypocurate.pipeline.agents import planner


def test_the_test_process_has_no_provider_credential_and_a_closed_local_address():
    assert "ANTHROPIC_API_KEY" not in os.environ and "ANTHROPIC_AUTH_TOKEN" not in os.environ
    assert os.environ["ANTHROPIC_API_BASE"] == os.environ["ANTHROPIC_BASE_URL"] == NO_PROVIDER
    assert NO_PROVIDER.startswith("http://127.0.0.1:")


@pytest.mark.parametrize("key, expected", [(None, "model_auth"), ("a-key-that-is-not-real", "provider_unavailable")])
def test_an_agent_call_without_the_stub_never_reaches_a_provider(migrated_database, monkeypatch, key, expected):
    """With no key the library refuses before sending (model_auth); with a key the request goes to the closed
    local port (provider_unavailable). In neither case is any usage recorded."""
    if key:
        monkeypatch.setenv("ANTHROPIC_API_KEY", key)
    engine = make_engine(migrated_database)
    pw.registered(engine, ("mpea",))
    q = queries.create(engine, "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
                       ("mpea",))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id)
    queries.start(engine, rid)
    result = planner.run_planner(engine, rid)
    assert result.failure == expected
    from sqlalchemy import text
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM model_call WHERE run_id = :r AND input_tokens IS NOT NULL"),
                            dict(r=rid)).scalar() == 0
```
### `tests/test_orchestrator.py`

```python
"""Step 8b, milestone 7: whole runs through the orchestrator, every model call to the local stub provider
(criteria 14.1 and 14.3 from code; the command line's own tests are in test_cli_runs.py)."""
from __future__ import annotations

import json
import re

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import orchestrator, queries
from hypocurate.pipeline import plan as plans
from hypocurate.sources.versions import files_digest, version_identity

MPEA_CLASS = "multi-principal-element (high-entropy) alloy"
FCC_CLAIM = "In FCC multi-principal-element alloys, yield strength rises as grain size falls"
BCC_CLAIM = "Grain refinement still strengthens BCC multi-principal-element alloys at 1000 °C"
PARTLY_CLAIM = ("In FCC multi-principal-element alloys tested in tension, yield strength rises as grain size falls, "
                "both at room temperature and at cryogenic temperatures (-196 °C)")
RT = {"band": "room temperature"}
CRYO = {"band": "cryogenic", "min": -200.0, "max": -150.0}
HOT = {"band": "elevated", "min": 950.0, "max": 1050.0}


def planner_body(**over):
    b = {"domain_matches": True,
         "claim_scope": {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                         "temperature_band": [RT]},
         # Step 8b (owner, 2026-10-07): each scope part marked stated by the claim or defaulted by the Planner.
         "stated": {"alloy_class": True, "phase_class": True, "test_type": False, "temperature_band": False},
         "outcome": "yield_strength", "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1}], "narrower": None}
    b.update(over)
    return b


BCC = planner_body(claim_scope={"alloy_class": [MPEA_CLASS], "phase_class": ["BCC"], "test_type": ["compression"],
                                "temperature_band": [HOT]})
PARTLY = planner_body(claim_scope={"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                                   "temperature_band": [RT, CRYO]},
                      narrower={"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [RT]})


def analyst_text(raw: str) -> str:
    """A text that passes the Analyst's checks (step 8b, owner 2026-10-07): placeholders only, no digit; the outcome
    and, when there is one, the verdict by name."""
    if '\\"verdict_wording\\": ' in raw:  # a key of the facts (the instruction itself names the placeholder)
        # With a verdict the pooled phrases are required too (owner, 2026-10-07).
        return ("The data are {outcome_wording}, and the claim is {verdict_wording}, with {pooled_p_phrase}, from "
                "{pooled_figures_phrase}.")
    return "The outcome is {outcome_wording}."


def responder(planner_answer=None, critic_answer=None, analyst=analyst_text):
    def respond(raw: str):
        if "[[ ## plan ## ]]" in raw:
            return sp.reply(sp.fields(plan=json.dumps(planner_answer)))
        if "[[ ## classification ## ]]" in raw:
            return sp.reply(sp.fields(classification=json.dumps(critic_answer or {})))
        if "[[ ## report ## ]]" in raw:
            return sp.reply(sp.fields(report=analyst(raw)))
        return sp.error(500, "api_error", "unexpected request")
    return respond


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    e.test_url = migrated_database
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e
    e.dispose()


def dispatched(engine, claim=FCC_CLAIM, fixed_plan=False, sufficiency="fixed_minimum"):
    q = queries.create(engine, claim, ("mpea", "tamu_fcc"), sufficiency=sufficiency)
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    return queries.dispatch(engine, q.version_id, fixed_plan=fixed_plan)


def run(engine, rid, stub, **kw):
    return orchestrator.run(engine, rid, client_options=sp.client_options(stub), **kw)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def rows(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def pooled(engine, rid):
    return rows(engine, "SELECT n_records, n_alloys, n_groups, resid_df, estimate, std_error, p_value FROM analysis_result "
                        "WHERE run_id = :r AND scope = 'pooled'", r=rid)[0]


# --- 14.1 -----------------------------------------------------------------------------------------------

def test_14_1a_the_fixed_plan_run_reproduces_the_reference_and_repeats_identically(engine, stub):
    stub.respond(responder())
    rid = dispatched(engine, fixed_plan=True)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome, report.failure) == ("completed", "sufficient", None)
    assert "planner" not in report.stages and report.stages[0] == "fixed plan"
    assert rows(engine, "SELECT outcome, verdict, exploratory, evidence_level FROM run WHERE id = :r", r=rid) == [
        ("sufficient", "supported", False, 6)]
    n, a, g, df, k, se, p = pooled(engine, rid)
    assert (n, a, g, df) == (97, 22, 20, 74)
    assert abs(k - 424.9) <= 0.05 and abs(se - 64.4) <= 0.05 and 1.25e-6 <= p <= 1.35e-6
    labels = dict(rows(engine, "SELECT s.key, ar.label FROM analysis_result ar JOIN source s ON s.id = ar.source_id "
                               "WHERE ar.run_id = :r AND ar.scope = 'per_source'", r=rid))
    assert labels["mpea"] == "agrees"
    tamu = rows(engine, "SELECT ar.check1_passed, ar.check2_passed, ar.p_value FROM analysis_result ar JOIN source s "
                        "ON s.id = ar.source_id WHERE ar.run_id = :r AND s.key = 'tamu_fcc'", r=rid)[0]
    assert tamu == (True, False, None)  # a coefficient, no uncertainty, no verdict
    assert one(engine, "SELECT minimums_met FROM analysis_result WHERE run_id = :r AND scope = 'pooled'", r=rid)
    assert one(engine, "SELECT output->>'report' FROM stage_result WHERE run_id = :r AND stage = 'analyst'", r=rid) \
        == report.explanation
    # Running the frozen run again: a second fixed-plan run of the same version.
    vid = one(engine, "SELECT hypothesis_version_id FROM run WHERE id = :r", r=rid)
    again = pw.run_of_version(engine, vid, ("mpea", "tamu_fcc"), agents=("planner", "critic", "analyst"))
    assert run(engine, again, stub).outcome == "sufficient"
    assert pooled(engine, again) == pooled(engine, rid)
    assert one(engine, "SELECT fingerprint FROM run_snapshot WHERE run_id = :r", r=again) == \
        one(engine, "SELECT fingerprint FROM run_snapshot WHERE run_id = :r", r=rid)


def test_14_1b_the_planners_plan_is_locked_and_the_run_completes(engine, stub):
    stub.respond(responder(planner_body()))
    rid = dispatched(engine)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "sufficient")
    vid = one(engine, "SELECT hypothesis_version_id FROM run WHERE id = :r", r=rid)
    assert one(engine, "SELECT content FROM plan WHERE run_id = :r", r=rid) == plans.reference_plan(vid)
    tags = {r[0] for r in rows(engine, "SELECT tv.value FROM run_tag rt JOIN tag_value tv ON tv.id = rt.tag_value_id "
                                       "WHERE rt.run_id = :r", r=rid)}
    assert tags == {"yield strength", MPEA_CLASS, "room-temperature tension"}
    assert one(engine, "SELECT fixed_plan FROM run WHERE id = :r", r=rid) is False


# --- 14.3 -----------------------------------------------------------------------------------------------

def test_14_3_the_bcc_claim_ends_insufficient_as_missing_evidence_with_no_verdict(engine, stub):
    stub.respond(responder(BCC))
    rid = dispatched(engine, claim=BCC_CLAIM)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "insufficient")
    assert rows(engine, "SELECT verdict, evidence_level FROM run WHERE id = :r", r=rid) == [(None, 1)]
    assert one(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid) == 0  # no dataset frozen
    assert one(engine, "SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0  # no p-value, no plot
    facts = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid)
    assert facts["kind"] == "missing_evidence"
    assert {s["source"]: s["kind"] for s in facts["sources"]} == {"mpea": "missing_evidence",
                                                                  "tamu_fcc": "missing_evidence"}
    assert facts["records_lacking_fields"]["mpea"]["grain_size"] > 0  # names the missing field
    assert set(facts["minimums_missed"]) == {"records", "alloys", "groups", "resid_df"}  # what would be enough
    coverage = rows(engine, "SELECT searched_sources, not_searched_sources FROM run_search_coverage WHERE run_id = :r",
                    r=rid)[0]
    assert sorted(coverage[0]) == ["mpea", "tamu_fcc"]


def test_14_3_a_partly_sufficient_original_and_its_narrower_question(engine, stub):
    stub.respond(responder(PARTLY))
    rid = dispatched(engine, claim=PARTLY_CLAIM)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "partly_sufficient") and report.narrower_question
    assert rows(engine, "SELECT verdict, evidence_level FROM run WHERE id = :r", r=rid) == [(None, 1)]
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
    assert one(engine, "SELECT status FROM stage_result WHERE run_id = :r AND stage = 'analyst'", r=rid) == "done"
    # The narrower question: separate, linked, labelled, dispatched by its number; it locks the stored plan (A8).
    vid = queries.submitted_version(engine, report.narrower_question)
    assert "narrower question" in one(engine, "SELECT text FROM hypothesis_version WHERE id = :v", v=vid)
    queries.confirm_domain(engine, vid, by="Ada Reviewer")
    narrower = queries.dispatch(engine, vid, fixed_plan=True)
    out = run(engine, narrower, stub)
    assert (out.status, out.outcome) == ("completed", "sufficient")
    stored = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'narrowing'", r=rid)
    locked = one(engine, "SELECT content FROM plan WHERE run_id = :r", r=narrower)
    assert locked == {"hypothesis_version": vid, **stored["narrower_plan"]}
    assert pooled(engine, narrower)[:4] == (97, 22, 20, 74)


def seal_new_version(engine, key):
    """A newer sealed version of `key`: the same data and one more documentation file."""
    with engine.begin() as conn:
        old = conn.execute(text("SELECT sv.id, sv.source_id, sv.source_type, sv.data_kind, sv.grouping_unit FROM "
                                "source_version sv JOIN source s ON s.id = sv.source_id WHERE s.key = :k "
                                "ORDER BY sv.id DESC LIMIT 1"), dict(k=key)).one()
        files = {p: bytes(c) for p, c in conn.execute(text("SELECT path, content FROM source_file WHERE "
                                                           "source_version_id = :v"), dict(v=old.id)).all()}
        roles = dict(conn.execute(text("SELECT path, role FROM source_file WHERE source_version_id = :v"),
                                  dict(v=old.id)).all())
        files["documentation/note.txt"], roles["documentation/note.txt"] = b"a later note\n", "documentation"
        new = conn.execute(text("INSERT INTO source_version (source_id, label, obtained_on, source_type, data_kind, "
                                "grouping_unit) VALUES (:s, 'later', '2026-10-07', :t, :d, :u) RETURNING id"),
                           dict(s=old.source_id, t=old.source_type, d=old.data_kind, u=old.grouping_unit)).scalar()
        import hashlib
        for path, content in files.items():
            conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content, role) VALUES "
                              "(:v, :p, :h, :c, :o)"), dict(v=new, p=path, h=hashlib.sha256(content).hexdigest(),
                                                             c=content, o=roles[path]))
        digest = files_digest(files)
        conn.execute(text("UPDATE source_version SET sealed_at = now(), files_digest = :d, fingerprint = :f WHERE id = :v"),
                     dict(d=digest, f=version_identity(digest, old.source_type, old.data_kind, old.grouping_unit), v=new))


def test_b1_a_narrower_question_on_other_source_versions_is_refused_with_a_reason(engine, stub):
    stub.respond(responder(PARTLY))
    rid = dispatched(engine, claim=PARTLY_CLAIM)
    report = run(engine, rid, stub)
    seal_new_version(engine, "mpea")
    vid = queries.submitted_version(engine, report.narrower_question)
    queries.confirm_domain(engine, vid, by="Ada Reviewer")
    narrower = queries.dispatch(engine, vid, fixed_plan=True)
    out = run(engine, narrower, stub)
    assert out.status == "failed" and out.failure.startswith("narrowing_sources_changed:")
    assert one(engine, "SELECT failure_reason FROM run WHERE id = :r", r=narrower).startswith("narrowing_sources_changed")
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=narrower) == 0


# --- the failure table ----------------------------------------------------------------------------------

def test_b2_the_analyst_failing_on_the_partly_path_still_completes_and_creates_the_narrower_question(engine, stub):
    stub.respond(responder(PARTLY, analyst=lambda raw: "The data do not exist in the sources searched."))
    rid = dispatched(engine, claim=PARTLY_CLAIM)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "partly_sufficient") and report.narrower_question
    assert report.explanation == "explanation unavailable (wording_refused)"
    assert one(engine, "SELECT status FROM stage_result WHERE run_id = :r AND stage = 'analyst'", r=rid) == "failed"


def test_a3_a_spending_refusal_at_the_analyst_leaves_codes_decision_standing(engine, stub):
    from decimal import Decimal
    stub.respond(responder())
    rid = dispatched(engine, fixed_plan=True)
    # The Critic's calls fit; the ceiling is too low for the Analyst's reservation (Opus, larger request).
    report = run(engine, rid, stub, ceiling=Decimal("0.17"))
    assert (report.status, report.outcome) == ("completed", "sufficient"), report
    assert report.explanation.startswith("explanation unavailable (")


def test_a_spending_refusal_at_the_planner_fails_the_run(engine, stub):
    from decimal import Decimal
    stub.respond(responder(planner_body()))
    rid = dispatched(engine)
    report = run(engine, rid, stub, ceiling=Decimal("0.001"))
    assert report.status == "failed" and report.failure.startswith("spending_refused:") and "ceiling_reached" in \
        report.failure
    assert stub.requests == []


@pytest.mark.parametrize("answer, code", [(planner_body(domain_matches=False), "domain_mismatch"),
                                          (planner_body(outcome="hardness"), "planner_failed"),
                                          # Both test types have usable records (FCC at room temperature), so
                                          # there is no narrower question: the claim is not one plan (A11). (Was
                                          # two bands, RT and 950-1050 °C; the second has no usable record, so code
                                          # now narrows it, owner 2026-10-07.)
                                          (planner_body(claim_scope={**planner_body()["claim_scope"],
                                                                     "test_type": ["tension", "compression"]}),
                                           "claim_not_one_plan")])
def test_a_run_fails_before_the_lock_with_a_stated_reason(engine, stub, answer, code):
    stub.respond(responder(answer))
    rid = dispatched(engine)
    report = run(engine, rid, stub)
    assert report.status == "failed" and report.failure.startswith(f"{code}: ")
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND status = 'running'", r=rid) == 0


def test_a_critic_failure_leaves_flags_unclassified_and_the_run_goes_on(engine, stub):
    def respond(raw):
        if "[[ ## classification ## ]]" in raw:
            return sp.reply(sp.fields(classification="prose, not JSON"))
        return responder()(raw)
    stub.respond(respond)
    rid = dispatched(engine, fixed_plan=True)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "sufficient")
    assert one(engine, "SELECT count(*) FROM flag WHERE run_id = :r AND critic_class IS NOT NULL", r=rid) == 0


def test_no_model_call_is_made_while_a_database_transaction_is_open(migrated_database, stub):
    """For every role: while the stub serves a request, the run's connections hold no open transaction. (Small
    data with invalid values, so the Critic has flags to classify; the reference data raise none.)"""
    from stats_world import small_rows
    from test_critic import CONFLICT
    engine = make_engine(migrated_database)
    engine.test_url = migrated_database
    pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT)})
    seen = []

    def check():
        with make_engine(engine.test_url).connect() as conn:
            seen.append(conn.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid() "
                "AND state IN ('idle in transaction', 'active') AND backend_type = 'client backend'")).scalar())

    stub.on_request(check)
    stub.respond(responder(planner_body()))
    q = queries.create(engine, FCC_CLAIM, ("mpea",))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id)
    assert run(engine, rid, stub).status == "completed"
    asked = {field for r in stub.requests for field in ("plan", "classification", "report")
             if f"[[ ## {field} ## ]]" in r["raw"].decode()}
    assert asked == {"plan", "classification", "report"}  # the Planner, the Critic and the Analyst
    assert len(seen) == len(stub.requests) and seen == [0] * len(seen)


def test_a_spending_refusal_at_the_critic_fails_the_run(migrated_database, stub):
    """PRD 8, 14.4: before the freeze a cap or ceiling stops the run, marked failed with the reason."""
    from decimal import Decimal
    from stats_world import small_rows
    from test_critic import CONFLICT
    engine = make_engine(migrated_database)
    pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT)})
    stub.respond(responder())
    q = queries.create(engine, FCC_CLAIM, ("mpea",))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, fixed_plan=True)
    report = run(engine, rid, stub, ceiling=Decimal("0.001"))
    assert report.status == "failed" and report.failure.startswith("spending_refused:")
    assert stub.requests == []  # nothing was sent
    assert one(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND status = 'running'", r=rid) == 0


def test_live_run_c_the_planner_gives_no_narrower_scope_and_code_builds_it(engine, stub):
    """Owner, 2026-10-07 (after live run C failed 'narrower_missing'): the same answer now gives a
    partly-sufficient original and its narrower question."""
    stub.respond(responder(PARTLY | {"narrower": None}))
    rid = dispatched(engine, claim=PARTLY_CLAIM)
    report = run(engine, rid, stub)
    assert (report.status, report.outcome) == ("completed", "partly_sufficient") and report.narrower_question


def test_the_analyst_is_told_which_scope_parts_the_claim_stated_and_which_were_assumed(engine, stub):
    """Owner, 2026-10-07 (after live run B tested an unstated test type as 'tension'): the Planner marks each scope
    part; the Analyst's facts carry the notes, so an explanation can say what was assumed."""
    stub.respond(responder(planner_body()))  # test type and temperature band marked as defaulted
    rid = dispatched(engine)
    run(engine, rid, stub)
    facts = json.loads(one(engine, "SELECT input->>'facts' FROM stage_result WHERE run_id = :r AND stage = 'analyst'",
                           r=rid))
    assert facts["scope_test_type"] == "the claim did not state a test type; tension was assumed"
    assert facts["scope_temperature_band"] == "the claim did not state a temperature; room temperature was assumed"
    assert facts["scope_phase_class"] == "phase class FCC, as the claim states"
    narrowing = one(engine, "SELECT output->'scope_stated' FROM stage_result WHERE run_id = :r AND stage = 'narrowing'",
                    r=rid)
    assert narrowing == {"alloy_class": True, "phase_class": True, "temperature_band": False, "test_type": False}
```
### `tests/test_planner_narrowing.py`

```python
"""Step 8b, milestone 4: the Planner, the narrowing decision and the partly-sufficient copy (owner, Q5, A1, A8,
A11). Every model call goes to the local stub provider: no live call."""
from __future__ import annotations

import json

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import completion, narrowing, queries
from hypocurate.pipeline import plan as plans
from hypocurate.pipeline.agents import planner
from hypocurate.pipeline.agents.settings import PLANNER_INSTRUCTION
from hypocurate.pipeline.statistics import PARTLY_SUFFICIENT_WORDING
from hypocurate.pipeline.writes import Refused

MPEA_CLASS = "multi-principal-element (high-entropy) alloy"
FCC_CLAIM = "In FCC multi-principal-element alloys, yield strength rises as grain size falls"
PARTLY_CLAIM = ("In FCC multi-principal-element alloys tested in tension, yield strength rises as grain size falls, "
                "both at room temperature and at cryogenic temperatures (-196 °C)")
BCC_CLAIM = "Grain refinement still strengthens BCC multi-principal-element alloys at 1000 °C"
RT = {"band": "room temperature"}
CRYO = {"band": "cryogenic", "min": -200.0, "max": -150.0}
HOT = {"band": "elevated", "min": 950.0, "max": 1050.0}


def body(**over):
    b = {"domain_matches": True,
         "claim_scope": {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                         "temperature_band": [RT]},
         # Step 8b (owner, 2026-10-07): each scope part marked stated by the claim or defaulted by the Planner.
         "stated": {"alloy_class": True, "phase_class": True, "test_type": False, "temperature_band": False},
         "outcome": "yield_strength", "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1}], "narrower": None}
    b.update(over)
    return b


def answer(**over) -> str:
    return sp.fields(plan=json.dumps(body(**over)))


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def running(engine, claim=FCC_CLAIM, sources=("mpea", "tamu_fcc"), register=True, sufficiency="fixed_minimum"):
    if register:
        pw.registered(engine, sources)
    q = queries.create(engine, claim, sources, sufficiency=sufficiency)
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id)
    queries.start(engine, rid)
    return rid


def plan_run(engine, rid, stub, **kw):
    return planner.run_planner(engine, rid, client_options=sp.client_options(stub), **kw)


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def stage(engine, rid):
    from hypocurate.access.stage import actual_stage
    with engine.connect() as conn:
        status = conn.execute(text("SELECT status FROM run WHERE id = :r"), dict(r=rid)).scalar_one()
        return actual_stage(conn, rid, status)


# --- the Planner's request and answer ------------------------------------------------------------------

def test_the_planners_complete_request_holds_no_outcome_value(engine, stub):
    """The planted-value test on the raw outbound bytes (PRD 4, 14.2): distinctive outcome values in the
    sealed source never reach the Planner; no tool is offered."""
    rows = [pw.mpea_row("CoCrNi", d, ys, doi=f"10.1016/j.test.2026.00{i}") for i, (d, ys) in
            enumerate([(1.0, 7311.375), (9.0, 6922.125), (4.0, 7104.875)])]
    pw.registered_files(engine, {"mpea": pw.mpea_csv(rows)})
    rid = running(engine, sources=("mpea",), register=False)
    stub.queue(sp.reply(answer()))
    result = plan_run(engine, rid, stub)
    assert result.failure is None
    [request] = stub.requests
    raw = request["raw"].decode()
    for v in ("7311.375", "6922.125", "7104.875", "7311.4", "6922.1", "7104.9", "14622.75"):
        assert v not in raw, v
    sent = json.loads(raw)
    assert "tools" not in sent
    assert PLANNER_INSTRUCTION in json.dumps(sent, ensure_ascii=False)
    assert FCC_CLAIM in raw and "record" in raw.lower()


def test_a_valid_answer_is_stored_and_its_plan_is_the_reference_plan(engine, stub):
    rid = running(engine)
    stub.queue(sp.reply(answer()))
    result = plan_run(engine, rid, stub)
    assert result.failure is None and result.answer.domain_matches
    vid = one(engine, "SELECT hypothesis_version_id FROM run WHERE id = :r", r=rid)
    built = planner.build_plan(vid, result.answer.claim_scope, result.answer.outcome, result.answer.exclusion_rules,
                               "fixed_minimum")
    assert built == plans.reference_plan(vid)  # field by field: the defaults plus the claim's scope
    assert one(engine, "SELECT status FROM stage_result WHERE id = :s", s=result.stage_id) == "done"
    assert one(engine, "SELECT output->'answer'->>'outcome' FROM stage_result WHERE id = :s",
               s=result.stage_id) == "yield_strength"


@pytest.mark.parametrize("over", [
    {"rules": {"min_grain_sizes": 1}},  # tries to weaken a fixed rule: not a key of the answer
    {"sufficiency": {"option": "use_available"}},  # the option is the query's, never the model's
    {"claim_scope": {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                     "temperature_band": [RT], "eligibility_rules": []}},
    {"outcome": "hardness"},
    {"claim_scope": {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                     "temperature_band": [{"band": "elevated"}]}},  # no range
    {"claim_scope": {"alloy_class": ["superalloy"], "phase_class": ["FCC"], "test_type": ["tension"],
                     "temperature_band": [RT]}},
    {"exclusion_rules": [{"rule": "yield_strength_range", "min": 100}]},  # not on the menu
    {"exclusion_rules": [{"rule": "phase", "values": ["HCP"]}]},
    {"domain_matches": "yes"},
    # Owner, 2026-10-07: the stated/defaulted mark is required for every scope part, as true or false.
    {"stated": {"alloy_class": True, "phase_class": True, "test_type": False}},
    {"stated": {"alloy_class": True, "phase_class": True, "test_type": "no", "temperature_band": False}},
    # The shape is right but the plan is not valid (plan.validate): an elevated range inside room temperature.
    {"claim_scope": {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
                     "temperature_band": [{"band": "elevated", "min": 15.0, "max": 22.0}]}},
])
def test_an_invalid_plan_is_corrected_once_naming_only_the_code_then_the_stage_fails(engine, stub, over):
    rid = running(engine)
    bad = answer(**over)
    stub.queue(sp.reply(bad), sp.reply(bad))
    result = plan_run(engine, rid, stub)
    assert result.answer is None and result.failure == "invalid_plan"
    assert len(stub.requests) == 2
    retry = stub.requests[1]["raw"].decode()
    assert "invalid_plan" in retry and "hardness" not in retry.split("previous answer")[-1][:200]
    assert one(engine, "SELECT status FROM stage_result WHERE id = :s", s=result.stage_id) == "failed"
    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0


def test_a_corrected_answer_is_accepted(engine, stub):
    rid = running(engine)
    stub.queue(sp.reply(answer(outcome="hardness")), sp.reply(answer()))
    result = plan_run(engine, rid, stub)
    assert result.failure is None and len(stub.requests) == 2


def test_a_claim_of_another_domain_is_a_valid_answer(engine, stub):
    rid = running(engine)
    stub.queue(sp.reply(answer(domain_matches=False)))
    result = plan_run(engine, rid, stub)
    assert result.failure is None and result.answer.domain_matches is False


def test_a_claim_that_is_not_one_plan_is_not_an_invalid_answer(engine, stub):
    """A11: two bands are a valid answer; no plan is built from it here (the narrowing decides)."""
    rid = running(engine)
    two = body()["claim_scope"] | {"temperature_band": [RT, CRYO]}
    stub.queue(sp.reply(answer(claim_scope=two)))
    result = plan_run(engine, rid, stub)
    assert result.failure is None and not planner.one_plan(result.answer.claim_scope)


# --- the narrowing decision (pure) -----------------------------------------------------------------------

def cell(phase="FCC", test="tension", band=None, t=25.0, gs=True, ys="converted", n=1):
    status = {"phase_class": "converted", "test_type": "converted", "test_temperature": "converted" if t is not None
              else "not_reported", "test_temperature_band": "converted" if band else "not_reported",
              "grain_size": "converted" if gs else "not_reported", "yield_strength": ys,
              "ultimate_tensile_strength": "not_reported", "hardness": "not_reported", "hardness_sd": "not_reported",
              "yield_strength_sd": "not_reported"}
    return {"categories": {"phase_class": phase, "test_type": test, "test_temperature_band": band},
            "test_temperature": t, "status": status, "grain_size_present": gs, "n": n}


def counts(*cells):
    return [{"source": "mpea", "version_fingerprint": "f" * 64, "readable": True, "n_records": len(cells),
             "cells": list(cells)}]


def answer_of(**over):
    return planner.read_answer(body(**over))


TWO_BANDS = {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
             "temperature_band": [RT, CRYO]}
NARROWER = {"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [RT]}


def test_every_part_with_records_proceeds():
    d = narrowing.decide(answer_of(), counts(cell(n=5)), 1, "fixed_minimum")
    assert (d["result"], d["reason"], d["zero_parts"]) == ("proceed", "no_part_without_records", [])
    assert d["part_counts"] == [{"part": "phase_class", "value": "FCC", "n": 5},
                                {"part": "test_type", "value": "tension", "n": 5},
                                {"part": "temperature_band", "value": RT, "n": 5}]


def test_a_part_with_none_and_the_exact_narrower_scope_is_partly_sufficient():
    d = narrowing.decide(answer_of(claim_scope=TWO_BANDS, narrower=NARROWER),
                         counts(cell(n=5), cell(t=-196.0, gs=False, n=9)), 1, "fixed_minimum")
    assert (d["result"], d["zero_parts"]) == ("partly_sufficient", [{"part": "temperature_band", "value": CRYO}])
    assert d["narrower_scope"] == NARROWER and "hypothesis_version" not in d["narrower_plan"]
    assert d["narrower_plan_fingerprint"] == plans.fingerprint(d["narrower_plan"])
    assert d["decision"]["evidence_level"] == 1 and d["decision"]["verdict"] is None
    assert d["decision"]["evidence_level_wording"] == PARTLY_SUFFICIENT_WORDING


@pytest.mark.parametrize("proposed", [
    None,
    {"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [CRYO]},
    {"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [RT, CRYO]},
])
def test_code_builds_the_narrower_scope_and_never_uses_the_planners(proposed):
    """Owner, 2026-10-07 (after live run C; was ..._not_exactly_the_parts_with_records_is_declined): the Planner
    cannot see which part has no usable record, so code builds the narrower scope; a proposal is stored only."""
    d = narrowing.decide(answer_of(claim_scope=TWO_BANDS, narrower=proposed),
                         counts(cell(n=5), cell(t=-196.0, gs=False)), 1, "fixed_minimum")
    assert (d["result"], d["narrower_scope"]) == ("partly_sufficient", NARROWER)
    assert d["proposed_narrower"] == (planner.read_answer(body(claim_scope=TWO_BANDS, narrower=proposed)).narrower)


def test_a_one_plan_claim_with_a_part_without_records_is_narrowed_by_code():
    """(Was test_a_declined_narrowing_of_a_one_plan_claim_proceeds.)"""
    two_phases = body()["claim_scope"] | {"phase_class": ["FCC", "BCC"]}
    d = narrowing.decide(answer_of(claim_scope=two_phases, narrower=None), counts(cell(n=5)), 1, "fixed_minimum")
    assert (d["result"], d["zero_parts"]) == ("partly_sufficient", [{"part": "phase_class", "value": "BCC"}])
    assert d["narrower_scope"] == {"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [RT]}


def test_a_narrower_scope_that_is_not_one_plan_is_not_used():
    """Two alloy classes: no narrower scope is one plan, so the claim is not one plan."""
    two_classes = TWO_BANDS | {"alloy_class": [MPEA_CLASS, "steel"]}
    d = narrowing.decide(answer_of(claim_scope=two_classes), counts(cell(n=5), cell(t=-196.0, gs=False)), 1,
                         "fixed_minimum")
    assert (d["result"], d["reason"]) == ("claim_not_one_plan", "narrower_invalid")


def test_two_bands_each_with_records_are_not_one_plan():
    """A11: the run fails before the lock; no narrower question."""
    d = narrowing.decide(answer_of(claim_scope=TWO_BANDS), counts(cell(n=5), cell(t=-196.0, n=2)), 1, "fixed_minimum")
    assert (d["result"], d["reason"]) == ("claim_not_one_plan", "no_part_without_records")


def test_no_part_with_records_proceeds_to_an_insufficient_run():
    bcc_hot = body()["claim_scope"] | {"phase_class": ["BCC"], "temperature_band": [HOT]}
    d = narrowing.decide(answer_of(claim_scope=bcc_hot), counts(cell(phase="BCC", test="compression", t=1000.0,
                                                                      gs=False, n=90)), 1, "fixed_minimum")
    assert (d["result"], d["reason"]) == ("proceed", "no_part_with_records")


@pytest.mark.parametrize("c, counted", [
    (cell(ys="not_reported"), False), (cell(gs=False), False), (cell(t=None, band="room temperature"), True),
    (cell(t=None, band=None), False), (cell(t=30.0), False), (cell(test="compression"), False),
])
def test_a_record_counts_only_with_a_grain_size_the_outcome_and_a_known_condition(c, counted):
    parts = narrowing.part_counts(counts(c), planner.read_answer(body()).claim_scope, "yield_strength")
    assert all((x["n"] == 1) == counted for x in parts if x["part"] == "temperature_band")


# --- the narrowing decision on the frozen sources, and the partly-sufficient copy ----------------------

def partly_answer():
    return body(claim_scope=TWO_BANDS, narrower=NARROWER)


def test_the_frozen_sources_make_the_cryogenic_claim_partly_sufficient(engine):
    """Structure counts from the frozen files (no model): FCC tension at room temperature has records with a
    grain size and yield strength; at cryogenic temperature none."""
    rid = running(engine, claim=PARTLY_CLAIM)
    out = narrowing.run_narrowing(engine, rid, planner.read_answer(partly_answer()))
    assert out["result"] == "partly_sufficient"
    by = {(x["part"], json.dumps(x["value"], sort_keys=True)): x["n"] for x in out["part_counts"]}
    assert by[("temperature_band", json.dumps(CRYO, sort_keys=True))] == 0
    assert by[("temperature_band", json.dumps(RT, sort_keys=True))] >= 89 + 93
    assert {s["source"] for s in out["sources"]} == {"mpea", "tamu_fcc"}
    assert stage(engine, rid) == "narrowed"


def test_the_frozen_sources_give_the_bcc_claim_nothing_to_test(engine):
    rid = running(engine, claim=BCC_CLAIM)
    bcc = body(claim_scope=body()["claim_scope"] | {"phase_class": ["BCC"], "test_type": ["compression"],
                                                      "temperature_band": [HOT]})
    out = narrowing.run_narrowing(engine, rid, planner.read_answer(bcc))
    assert (out["result"], out["reason"]) == ("proceed", "no_part_with_records")
    assert stage(engine, rid) == "before_lock"


def test_the_partly_sufficient_original_is_completed_by_copying_and_its_narrower_question_created(engine):
    rid = running(engine, claim=PARTLY_CLAIM)
    out = narrowing.run_narrowing(engine, rid, planner.read_answer(partly_answer()))
    decision = completion.copy_partly_sufficient(engine, rid)
    assert decision == out["decision"]
    with engine.connect() as conn:
        assert conn.execute(text("SELECT status, outcome, verdict, exploratory, evidence_level FROM run WHERE id = :r"),
                            dict(r=rid)).one() == ("completed", "partly_sufficient", None, False, 1)
    q = queries.create_narrower(engine, rid, out["narrower_scope"])
    assert one(engine, "SELECT narrower_of_run_id FROM hypothesis WHERE id = :h", h=q.hypothesis_id) == rid


def test_the_copy_refuses_a_run_that_is_not_narrowed(engine):
    rid = running(engine)
    with pytest.raises(Refused) as refused:
        completion.copy_partly_sufficient(engine, rid)
    assert refused.value.code == "stage_mismatch"


def test_the_copy_refuses_a_decision_taken_on_other_source_versions(engine):
    rid = running(engine, claim=PARTLY_CLAIM)
    d = narrowing.decide(planner.read_answer(partly_answer()),
                         counts(cell(n=5), cell(t=-196.0, gs=False)), 1, "fixed_minimum")
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO stage_result (run_id, stage, status, finished_at, output) VALUES "
                          "(:r, 'narrowing', 'running', NULL, NULL)"), dict(r=rid))
        conn.execute(text("UPDATE stage_result SET status = 'done', finished_at = now(), output = CAST(:o AS jsonb) "
                          "WHERE run_id = :r AND stage = 'narrowing'"),
                     dict(r=rid, o=json.dumps({**d, "sources": [{"source": "mpea", "version_fingerprint": "f" * 64,
                                                                 "readable": True}]})))
    with pytest.raises(Refused) as refused:
        completion.copy_partly_sufficient(engine, rid)
    assert refused.value.code == "decision_not_current"


def test_the_stated_marks_are_kept_with_the_answer_and_the_narrowing_decision():
    d = narrowing.decide(answer_of(), counts(cell(n=5)), 1, "fixed_minimum")
    assert d["scope_stated"] == {"alloy_class": True, "phase_class": True, "temperature_band": False, "test_type": False}


def test_an_answer_without_the_stated_marks_is_invalid():
    b = body()
    del b["stated"]
    with pytest.raises(planner.AnswerInvalid):
        planner.read_answer(b)
```
### `tests/test_queries.py`

```python
"""Step 8b, milestone 3: creating, submitting, confirming and dispatching queries (pipeline/queries.py), and the
narrower question (owner, Q10, A2, A8, A9)."""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import pipeline_world as pw
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import queries
from hypocurate.pipeline.agents.settings import RUN_ROLES, SETTINGS

CLAIM = "In FCC multi-principal-element alloys, yield strength rises as grain size falls"


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e
    e.dispose()


def rows(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).all()


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def dispatched(engine, sources=("mpea", "tamu_fcc"), **kw):
    q = queries.create(engine, CLAIM, sources, sufficiency=kw.pop("sufficiency", "fixed_minimum"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    return q, queries.dispatch(engine, q.version_id, **kw)


def test_a_query_goes_from_draft_to_a_running_run(engine):
    q, rid = dispatched(engine, sources=("mpea",))
    assert q.number.startswith("Q-")
    assert rows(engine, "SELECT status, review_comment, sufficiency_option FROM hypothesis_version WHERE id = :v",
                v=q.version_id) == [("dispatched", "domain confirmed at the command line by Ada Reviewer",
                                     "fixed_minimum")]
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "queued"
    queries.start(engine, rid)
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    sources = rows(engine, "SELECT s.key, rs.search_status, rs.source_version_id IS NOT NULL FROM run_source rs "
                           "JOIN source s ON s.id = rs.source_id WHERE rs.run_id = :r ORDER BY s.key", r=rid)
    assert sources == [("mpea", "pending", True), ("tamu_fcc", "not_selected", False)]
    newest = one(engine, "SELECT max(sv.id) FROM source_version sv JOIN source s ON s.id = sv.source_id "
                         "WHERE s.key = 'mpea' AND sv.sealed_at IS NOT NULL")
    assert one(engine, "SELECT source_version_id FROM run_source rs JOIN source s ON s.id = rs.source_id "
                       "WHERE rs.run_id = :r AND s.key = 'mpea'", r=rid) == newest


def test_dispatch_records_the_settings_version_of_each_run_role(engine):
    _, rid = dispatched(engine)
    got = rows(engine, "SELECT ras.role, a.model FROM run_agent_setting ras JOIN agent_setting a "
                       "ON a.id = ras.agent_setting_id WHERE ras.run_id = :r ORDER BY ras.role", r=rid)
    assert got == sorted((role, SETTINGS[role]["model"]) for role in RUN_ROLES)
    assert "curator" not in {r for r, _ in got}  # the Curator never runs in a run (step 8a)


def test_the_querys_option_is_chosen_before_dispatch(engine):
    q, rid = dispatched(engine, sufficiency="use_available")
    assert one(engine, "SELECT sufficiency_option FROM hypothesis_version WHERE id = :v", v=q.version_id) == \
        "use_available"


def test_a_fixed_plan_and_a_test_run_are_recorded_at_dispatch(engine):
    _, rid = dispatched(engine, fixed_plan=True, constructed_test_data=True)
    assert rows(engine, "SELECT fixed_plan, experiment_flags FROM run WHERE id = :r", r=rid) == [
        (True, {"constructed_test_data": True})]


@pytest.mark.parametrize("by", ["", "   ", None, "x" * 201])
def test_the_domain_is_confirmed_only_by_a_named_person(engine, by):
    q = queries.create(engine, CLAIM, ("mpea",))
    queries.submit(engine, q.version_id)
    with pytest.raises(queries.QueryRefused) as refused:
        queries.confirm_domain(engine, q.version_id, by=by)
    assert refused.value.code == "reviewer_missing"


def test_an_unsupported_domain_cannot_be_dispatched_and_the_message_says_why(engine):
    """PRD 14.3: a query in a domain that is not yet supported cannot be dispatched."""
    q = queries.create(engine, "Fatigue life falls with porosity", ("mpea",), domain="fatigue")
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    with pytest.raises(IntegrityError, match="dispatch blocked: the confirmed domain is not supported yet"):
        queries.dispatch(engine, q.version_id)
    assert one(engine, "SELECT count(*) FROM run") == 0
    assert one(engine, "SELECT status FROM hypothesis_version WHERE id = :v", v=q.version_id) == "submitted"


@pytest.mark.parametrize("sources, code", [(("nosuch",), "unknown_source"), ((), "no_source")])
def test_a_query_names_registered_sources(engine, sources, code):
    with pytest.raises(queries.QueryRefused) as refused:
        queries.create(engine, CLAIM, sources)
    assert refused.value.code == code


def test_dispatch_needs_a_confirmed_domain(engine):
    q = queries.create(engine, CLAIM, ("mpea",))
    queries.submit(engine, q.version_id)
    with pytest.raises(IntegrityError, match="dispatch_needs_confirmed_domain"):
        queries.dispatch(engine, q.version_id)


def partly(engine, sufficiency="use_available"):
    _, rid = dispatched(engine, sufficiency=sufficiency)
    queries.start(engine, rid)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO stage_result (run_id, stage) VALUES (:r, 'narrowing')"), dict(r=rid))
        conn.execute(text("UPDATE stage_result SET status = 'done', finished_at = now(), "
                          "output = '{\"result\": \"partly_sufficient\"}' WHERE run_id = :r"), dict(r=rid))
        conn.execute(text("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
                          "evidence_level = 1 WHERE id = :r"), dict(r=rid))
    return rid


NARROWER = {"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [{"band": "room temperature"}]}


def test_the_narrower_question_is_a_separate_linked_submitted_query(engine):
    original = partly(engine)
    q = queries.create_narrower(engine, original, NARROWER)
    assert rows(engine, "SELECT narrower_of_run_id FROM hypothesis WHERE id = :h", h=q.hypothesis_id) == [(original,)]
    version = rows(engine, "SELECT hv.status, hv.text, d.key, hv.sufficiency_option FROM hypothesis_version hv "
                           "JOIN domain d ON d.id = hv.domain_id WHERE hv.id = :v", v=q.version_id)[0]
    assert version == ("submitted", f"{CLAIM} (narrower question: phase class FCC; test type tension; room temperature)",
                       "grain_size_strengthening", "use_available")
    assert sorted(r[0] for r in rows(engine, "SELECT s.key FROM hypothesis_version_source hvs JOIN source s "
                                             "ON s.id = hvs.source_id WHERE hypothesis_version_id = :v",
                                     v=q.version_id)) == ["mpea", "tamu_fcc"]
    original_number = one(engine, "SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = "
                                  "r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
                                  "WHERE r.id = :r", r=original)
    assert q.number != original_number
    # Dispatched by its number (`hypocurate dispatch Q-...`), after a named person confirms the domain.
    vid = queries.submitted_version(engine, q.number)
    assert vid == q.version_id
    queries.confirm_domain(engine, vid, by="Ada Reviewer")
    rid = queries.dispatch(engine, vid, fixed_plan=True)
    assert one(engine, "SELECT fixed_plan FROM run WHERE id = :r", r=rid) is True


def test_a_narrower_question_needs_a_partly_sufficient_original(engine):
    _, rid = dispatched(engine)
    with pytest.raises(IntegrityError, match="partly_sufficient"):
        queries.create_narrower(engine, rid, NARROWER)


def test_only_a_submitted_version_is_dispatched_by_number(engine):
    q = queries.create(engine, CLAIM, ("mpea",))
    with pytest.raises(queries.QueryRefused) as refused:
        queries.submitted_version(engine, q.number)
    assert refused.value.code == "not_submitted"


@pytest.mark.parametrize("scope, words", [
    ({"phase_class": ["FCC", "BCC"]}, "phase class FCC, BCC"),
    ({"temperature_band": [{"band": "cryogenic", "min": -200.0, "max": -150.0}]}, "cryogenic (-200 to -150 °C)"),
])
def test_the_narrower_scope_in_words_is_built_from_vocabulary_values(scope, words):
    assert queries.scope_in_words(scope) == words
```
## 4. Changed tests and test helpers (diff)

```diff
diff --git a/tests/access_world.py b/tests/access_world.py
index aacff11..6e62a2b 100644
--- a/tests/access_world.py
+++ b/tests/access_world.py
@@ -108,6 +108,7 @@ class AccessWorld:
     records: list[int] = field(default_factory=list)
     flags: list[int] = field(default_factory=list)
     settings: dict = field(default_factory=dict)  # role -> agent setting id recorded for the run
+    original_tested_run: int = 0  # step 8b: an earlier run of the original query, with records and a coefficient
 
 
 def add_planted_version(w: World, key="mpea", content: bytes | None = None, label="v-planted") -> int:
@@ -182,29 +183,60 @@ def lock(w: World, run: int) -> None:
                                          "smallest_effect": f"{ys}"})
 
 
-def original_run(w: World) -> int:
-    """A completed 'partly sufficient' run with OTHER in its records, coefficient, stage
-    outputs and commentary: the run a narrower question comes from."""
-    rid = w.running(sources=("mpea",))
+def original_run(w: World) -> tuple[int, int]:
+    """The run a narrower question comes from, completed as 'partly sufficient', and an earlier run of
+    the same original query. Step 8b (0006; owner, A5): a partly-sufficient run has no plan and no
+    record, only code's narrowing decision, so OTHER is planted in its stage outputs and commentary, and
+    in the earlier run's records and coefficient. Returns (original run, earlier tested run)."""
     # Step 7 (owner's decision 1): under the fixed option a run below the minimums stores no
-    # coefficient, so this run, which holds OTHER as its coefficient, uses what is available.
-    w.lock(rid, option="use_available")
-    w.search(rid, "mpea")
-    recs = store_value_records(w, rid, OTHER)
-    primary = w.analysis_set(rid)
+    # coefficient, so the earlier run, which holds OTHER as its coefficient, has minimums it meets.
+    # (The query keeps the default option: its narrower question, the main run, must have the same.)
+    vid = w.dispatched(sources=("mpea",))
+    tested = w.running(vid=vid, sources=("mpea",))
+    w.lock(tested, mins=(1, 1, 1, 1))
+    w.search(tested, "mpea")
+    recs = store_value_records(w, tested, OTHER)
+    primary = w.analysis_set(tested)
     for rec in recs:
-        w.decide(rid, rec)
+        w.decide(tested, rec)
         w.add(primary, rec)
-    w.freeze(rid, len(recs))
+    w.freeze(tested, len(recs))
     sql(w, "INSERT INTO analysis_result (run_id, scope, analysis_set_id, n_records, n_alloys, n_groups, "
            "n_groups_informative, resid_df, check1_passed, check2_passed, minimums_met, estimate) "
-           "VALUES (:r, 'pooled', :s, 3, 1, 1, 1, 1, true, false, false, :e)", r=rid, s=primary, e=OTHER)
+           "VALUES (:r, 'pooled', :s, 3, 1, 1, 1, 1, true, false, true, :e)", r=tested, s=primary, e=OTHER)
+    w.complete(tested, "insufficient", level=4)
+    rid = w.running(vid=vid, sources=("mpea",))
     stage(w, rid, "analyst", "analyst", f"k = {OTHER}")
-    w.complete(rid, "partly_sufficient")
+    w.partly(rid)
     cid = stage(w, rid, "commentator", "commentator", f"the coefficient {OTHER}")
     sql(w, "INSERT INTO commentary (run_id, stage_result_id, status, text, model, number_check) "
            "VALUES (:r, :s, 'written', :t2, 'model-b', 'all_match')", r=rid, s=cid, t2=f"k was {OTHER}")
-    return rid
+    return rid, tested
+
+
+def code_output(w: World, run: int, name: str, output: dict, attempt: int = 1) -> int:
+    """A done code stage result (role NULL) with `output`, as `writes.code_stage` writes it."""
+    sid = w.stage(run, stage=name, role=None, attempt=attempt)
+    sql(w, "UPDATE stage_result SET status = 'done', finished_at = now(), output = :j_o WHERE id = :s",
+        j_o=output, s=sid)
+    return sid
+
+
+def stored_facts(w: World, run: int, frozen: bool) -> None:
+    """Step 8b: the statistics and gap-facts outputs code stores (step 7), with a planted value in keys
+    the Analyst's facts do not name (and, without a freeze, nowhere it may see)."""
+    hidden = {"yield_strength": PLANTED["yield_strength"]}
+    decision = {"state": "sufficient" if frozen else "no_dataset_frozen", "outcome": "insufficient",
+                "outcome_wording": "insufficient in the sources searched", "verdict": None, "verdict_wording": None,
+                "exploratory": False, "evidence_level": 1, "evidence_level_wording": "no dataset frozen",
+                "label": None, "freeze_fingerprint": None, "hidden": hidden}
+    analyses = [{"analysis": "pooled", "scope": "pooled", "set": "primary", "source": None, "withheld": False,
+                 "counts": {"n_records": 3, "n_alloys": 1, "hidden": hidden}, "estimate": 424.9, "std_error": 64.4,
+                 "records_found": [f"{PLANTED['yield_strength']}"], "hidden": hidden}] if frozen else []
+    code_output(w, run, "statistics", {"decision": decision, "analyses": analyses, "not_analysed": [],
+                                       "withheld": False, "hidden": hidden})
+    code_output(w, run, "gap_facts", {"minimums": None, "minimums_missed": [], "records_lacking_fields": {},
+                                      "eligibility_rules": {}, "sources": [], "hidden": hidden})
 
 
 def build(engine, stage_name: str) -> AccessWorld:
@@ -221,7 +253,7 @@ def build(engine, stage_name: str) -> AccessWorld:
            "ON CONFLICT (kind, value) DO NOTHING")  # seeded by migration 0002 (step 6)
     sql(w, "INSERT INTO tag_value (kind, value, status) VALUES ('property', :v, 'proposed')",
         v=f"strength {PLANTED['yield_strength']}")
-    original = original_run(w)
+    original, tested = original_run(w)
     h = w.hypothesis(narrower_of=original)
     vid = val(w, "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
                  "VALUES (:h, 1, :t, :d) RETURNING id", h=h, t=DIRECTION, d=w.domain["grain_size_strengthening"])
@@ -237,6 +269,7 @@ def build(engine, stage_name: str) -> AccessWorld:
     w.fail(earlier)
     rid = w.run(vid=vid, sources=("mpea", "tamu_fcc"))
     world = AccessWorld(w, rid, original, earlier)
+    world.original_tested_run = tested
     # Dispatch records the agent setting of each role (the dispatcher reads roles from here).
     for role in ROLES:
         sid = settings.get(role) or val(w, "INSERT INTO agent_setting (role, version, instruction, model) "
@@ -256,6 +289,21 @@ def build(engine, stage_name: str) -> AccessWorld:
         return world
     if stage_name == "before_lock":
         return world
+    if stage_name == "narrowed":
+        # Step 8b (A4): code's narrowing decision of partly sufficient, stored with named keys; a planted
+        # value in a key that is not named must never reach a role.
+        code_output(w, rid, "narrowing", {
+            "result": "partly_sufficient", "reason": "zero_parts_and_narrower_plan",
+            "claim_scope": {"phase_class": ["FCC"], "temperature_band": [{"band": "room temperature"},
+                                                                         {"band": "cryogenic", "min": -200.0,
+                                                                          "max": -150.0}],
+                            "test_type": ["tension"]},
+            "part_counts": [{"part": "phase_class", "value": "FCC", "n": 3}],
+            "zero_parts": [{"part": "temperature_band", "value": "cryogenic"}],
+            "narrower_scope": {"phase_class": ["FCC"], "temperature_band": ["room temperature"],
+                               "test_type": ["tension"]},
+            "hidden": {"yield_strength": PLANTED["yield_strength"]}})
+        return world
     lock(w, rid)
     w.search(rid, "mpea")
     w.search(rid, "tamu_fcc", status="failed", nothing_found="failed_search",
@@ -280,6 +328,7 @@ def build(engine, stage_name: str) -> AccessWorld:
     if stage_name in ("closed_without_freeze", "final_without_freeze"):
         sql(w, "INSERT INTO calibration_result (run_id, status, reason) VALUES (:r, 'unavailable', 'no_dataset_frozen')",
             r=rid)
+        stored_facts(w, rid, frozen=False)
         # The Analyst's gap report (it never saw an outcome value, so it holds none).
         stage(w, rid, "analyst", "analyst", GAP_REPORT)
         if stage_name == "final_without_freeze":
@@ -290,7 +339,9 @@ def build(engine, stage_name: str) -> AccessWorld:
         for rec in world.records:
             w.add(primary, rec)
         w.freeze(rid, len(world.records))
+        stored_facts(w, rid, frozen=True)
         if stage_name == "final":
-            w.complete(rid, "partly_sufficient")
+            # Step 8b (0006; owner, A5): a run with a plan never completes as partly sufficient.
+            w.complete(rid, "insufficient", level=4)
         return world
     raise ValueError(stage_name)
diff --git a/tests/conftest.py b/tests/conftest.py
index e3fd4d8..2e22523 100644
--- a/tests/conftest.py
+++ b/tests/conftest.py
@@ -15,6 +15,16 @@ from sqlalchemy import make_url, text
 from hypocurate.db import migrate
 from hypocurate.db.engine import database_reachable, make_engine
 
+# Step 8b: the regression suite makes no live model call (owner's standing requirement). For the whole test
+# process, and every guarded child it starts (they copy this environment): no provider credential, and the
+# provider's address is a closed local port, so a request without the stub's own address and key can never
+# leave the machine. Tests that call an agent pass the stub's address (stub_provider.client_options).
+NO_PROVIDER = "http://127.0.0.1:9"
+for _name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
+    os.environ.pop(_name, None)
+os.environ["ANTHROPIC_API_BASE"] = NO_PROVIDER
+os.environ["ANTHROPIC_BASE_URL"] = NO_PROVIDER
+
 HOW_TO = (
     "This test needs PostgreSQL. Run the suite with `docker compose run --rm test`, "
     "or start the database with `docker compose up -d db` and set DATABASE_URL "
diff --git a/tests/model_builder.py b/tests/model_builder.py
index 3490fe1..e8693f1 100644
--- a/tests/model_builder.py
+++ b/tests/model_builder.py
@@ -103,12 +103,14 @@ class World:
     def hypothesis(self, narrower_of=None):
         return self.val("INSERT INTO hypothesis (narrower_of_run_id) VALUES (:r) RETURNING id", r=narrower_of)
 
-    def draft(self, hypothesis=None, number=1, domain="grain_size_strengthening", sources=("mpea", "tamu_fcc")):
+    def draft(self, hypothesis=None, number=1, domain="grain_size_strengthening", sources=("mpea", "tamu_fcc"),
+              sufficiency="fixed_minimum"):
+        """Step 8b (0006): the query's sufficiency option is chosen here, before dispatch."""
         hypothesis = hypothesis or self.hypothesis()
         vid = self.val(
-            "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) "
-            "VALUES (:h, :n, 'Yield strength rises as grain size falls', :d) RETURNING id",
-            h=hypothesis, n=number, d=self.domain[domain])
+            "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id, sufficiency_option) "
+            "VALUES (:h, :n, 'Yield strength rises as grain size falls', :d, :o) RETURNING id",
+            h=hypothesis, n=number, d=self.domain[domain], o=sufficiency)
         for s in sources:
             self.run_sql("INSERT INTO hypothesis_version_source VALUES (:v, :s)", v=vid, s=self.source[s])
         return vid
@@ -131,10 +133,11 @@ class World:
         return vid
 
     # --- runs -------------------------------------------------------------------------
-    def run(self, vid=None, sources=("mpea", "tamu_fcc"), agents=False):
+    def run(self, vid=None, sources=("mpea", "tamu_fcc"), agents=False, sufficiency="fixed_minimum"):
         """Dispatch: a queued run with a run_source row for every registered source; with `agents`,
-        the world's settings version of every role recorded too (needed for model calls, step 8a)."""
-        vid = vid or self.dispatched()
+        the world's settings version of every role recorded too (needed for model calls, step 8a).
+        `sufficiency`: the new query's option (step 8b), when no version is given."""
+        vid = vid or self.dispatched(sufficiency=sufficiency)
         rid = self.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
         if agents:
             for role in ("planner", "curator", "critic", "analyst", "commentator"):
@@ -163,8 +166,11 @@ class World:
         self.lock(rid)
         return rid
 
-    def lock(self, rid, option="fixed_minimum", keys=(), mins=(4, 1, 2, 1), tags=()):
-        """The rules lock, in one transaction with its tags."""
+    def lock(self, rid, option=None, keys=(), mins=(4, 1, 2, 1), tags=()):
+        """The rules lock, in one transaction with its tags. Step 8b (0006): the plan's option is the
+        query's unless a test gives another (which the database refuses)."""
+        option = option or self.val("SELECT hv.sufficiency_option FROM run r JOIN hypothesis_version hv "
+                                    "ON hv.id = r.hypothesis_version_id WHERE r.id = :r", r=rid)
         with self.e.begin() as conn:
             pid = conn.execute(text(
                 "INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
@@ -206,8 +212,8 @@ class World:
         """A running run, locked and frozen, with n eligible records in its primary set.
         per_source: {"mpea": 3, "tamu_fcc": 1}; default: all from MPEA."""
         per_source = per_source or {"mpea": n}
-        rid = self.running(agents=agents)
-        self.lock(rid, option=option, keys=keys, mins=mins)
+        rid = self.running(agents=agents, sufficiency=option)
+        self.lock(rid, keys=keys, mins=mins)
         primary = self.analysis_set(rid)
         recs = []
         for source, count in per_source.items():
@@ -262,6 +268,19 @@ class World:
                      "exploratory = :x, evidence_level = :e WHERE id = :r", o=outcome, v=verdict, x=exploratory,
                      e=level, r=rid)
 
+    def partly(self, rid):
+        """Step 8b (0006; owner, A5): a run completes as partly sufficient only with no plan, no record and
+        code's narrowing decision of partly sufficient stored (a done 'narrowing' stage result); level 1."""
+        self.narrowing(rid)
+        self.complete(rid, "partly_sufficient", level=1)
+
+    def narrowing(self, rid, result="partly_sufficient"):
+        """Code's narrowing decision (step 8b): a done 'narrowing' stage result with its result."""
+        sid = self.stage(rid, "narrowing", None)
+        self.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), "
+                     "output = CAST(:o AS jsonb) WHERE id = :s", o=f'{{"result": "{result}"}}', s=sid)
+        return sid
+
     def fail(self, rid, reason="worker stopped"):
         self.run_sql("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = :f WHERE id = :r",
                      f=reason, r=rid)
diff --git a/tests/pipeline_world.py b/tests/pipeline_world.py
index 63da9f7..2cb4e09 100644
--- a/tests/pipeline_world.py
+++ b/tests/pipeline_world.py
@@ -107,8 +107,10 @@ def _val(engine, sql, **params):
         return result.scalar() if result.returns_rows else None
 
 
-def dispatched_run(engine, sources=("mpea", "tamu_fcc"), marked=False) -> int:
-    """A running run of the reference claim that chose `sources`."""
+def dispatched_run(engine, sources=("mpea", "tamu_fcc"), marked=False, sufficiency="fixed_minimum",
+                   agents=()) -> int:
+    """A running run of the reference claim that chose `sources`. Step 8b (0006): `sufficiency` is the
+    query's option, chosen before dispatch; the plan locked for the run must have the same."""
     with engine.connect() as conn:
         registry = dict(conn.execute(text(
             "SELECT s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id AND sv.sealed_at IS NOT NULL "
@@ -116,20 +118,22 @@ def dispatched_run(engine, sources=("mpea", "tamu_fcc"), marked=False) -> int:
         ids = dict(conn.execute(text("SELECT key, id FROM source")).all())
         domain = conn.execute(text("SELECT id FROM domain WHERE key = 'grain_size_strengthening'")).scalar_one()
     h = _val(engine, "INSERT INTO hypothesis DEFAULT VALUES RETURNING id")
-    vid = _val(engine, "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id) VALUES "
+    vid = _val(engine, "INSERT INTO hypothesis_version (hypothesis_id, version_number, text, domain_id, "
+                       "sufficiency_option) VALUES "
                        "(:h, 1, 'In FCC multi-principal-element alloys, yield strength rises as grain size falls', "
-                       ":d) RETURNING id", h=h, d=domain)
+                       ":d, :o) RETURNING id", h=h, d=domain, o=sufficiency)
     for key in sources:
         _val(engine, "INSERT INTO hypothesis_version_source VALUES (:v, :s)", v=vid, s=ids[key])
     _val(engine, "UPDATE hypothesis_version SET status = 'submitted', submitted_at = now() WHERE id = :v", v=vid)
     _val(engine, "UPDATE hypothesis_version SET confirmed_domain_id = :d, domain_confirmed_at = now() WHERE id = :v",
          v=vid, d=domain)
     _val(engine, "UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v", v=vid)
-    return run_of_version(engine, vid, sources, marked)
+    return run_of_version(engine, vid, sources, marked, agents)
 
 
-def run_of_version(engine, vid, sources=("mpea", "tamu_fcc"), marked=False) -> int:
-    """Another running run of an already dispatched hypothesis version."""
+def run_of_version(engine, vid, sources=("mpea", "tamu_fcc"), marked=False, agents=()) -> int:
+    """Another running run of an already dispatched hypothesis version. Step 8b: `agents`, the roles whose
+    (test) settings versions are recorded at dispatch, as the database requires."""
     with engine.connect() as conn:
         registry = dict(conn.execute(text(
             "SELECT s.key, (SELECT sv.id FROM source_version sv WHERE sv.source_id = s.id AND sv.sealed_at IS NOT NULL "
@@ -145,6 +149,9 @@ def run_of_version(engine, vid, sources=("mpea", "tamu_fcc"), marked=False) -> i
         else:
             _val(engine, "INSERT INTO run_source (run_id, source_id, search_status) VALUES (:r, :s, 'not_selected')",
                  r=rid, s=ids[key])
+    from hypocurate.pipeline.agents.settings import ensure_setting
+    for role in agents:  # the code's settings versions (as `queries.dispatch` records them)
+        _val(engine, "INSERT INTO run_agent_setting VALUES (:r, :o, :s)", r=rid, o=role, s=ensure_setting(engine, role))
     _val(engine, "UPDATE run SET status = 'running', started_at = now() WHERE id = :r", r=rid)
     return rid
 
diff --git a/tests/stats_world.py b/tests/stats_world.py
index 7213caa..0f4733f 100644
--- a/tests/stats_world.py
+++ b/tests/stats_world.py
@@ -40,10 +40,11 @@ def plan_for(vid: int, option: str = "fixed_minimum", mins=(30, 5, 10, 10), rule
     return plan
 
 
-def run_on(engine, rows, option="fixed_minimum", mins=(30, 5, 10, 10), marked=False, register=True, rules=None) -> int:
+def run_on(engine, rows, option="fixed_minimum", mins=(30, 5, 10, 10), marked=False, register=True, rules=None,
+           agents=()) -> int:
     if register:
         pw.registered_files(engine, {"mpea": pw.mpea_csv(rows)})
-    rid = pw.dispatched_run(engine, sources=("mpea",), marked=marked)
+    rid = pw.dispatched_run(engine, sources=("mpea",), marked=marked, sufficiency=option, agents=agents)
     checkpoints.lock_rules(engine, rid, plan_for(pw.version_of(engine, rid), option, mins, rules))
     extract.store_records(engine, rid)
     checks.run_checks(engine, rid)
diff --git a/tests/stub_provider.py b/tests/stub_provider.py
index b796329..3308e14 100644
--- a/tests/stub_provider.py
+++ b/tests/stub_provider.py
@@ -65,6 +65,7 @@ class StubProvider:
         self.requests: list[dict] = []
         self.script: deque = deque()
         self._callback = None
+        self._responder = None
         stub = self
 
         class Handler(BaseHTTPRequestHandler):
@@ -73,7 +74,12 @@ class StubProvider:
                 stub.requests.append({"path": self.path, "headers": dict(self.headers), "raw": raw})
                 if stub._callback:
                     stub._callback()
-                step = stub.script.popleft() if stub.script else error(500, "api_error", "no scripted reply")
+                if stub.script:
+                    step = stub.script.popleft()
+                elif stub._responder:
+                    step = stub._responder(raw.decode("utf-8", "replace"))
+                else:
+                    step = error(500, "api_error", "no scripted reply")
                 if step["kind"] == "sleep":
                     time.sleep(step["seconds"])
                     step = reply("too late")
@@ -99,6 +105,12 @@ class StubProvider:
         self.script.extend(steps)
         return self
 
+    def respond(self, responder):
+        """Step 8b: when the script is empty, `responder(raw request text)` gives the reply (a whole run calls
+        several roles; a test can answer each by the output field its request asks for)."""
+        self._responder = responder
+        return self
+
     def on_request(self, callback):
         self._callback = callback
 
diff --git a/tests/test_access_code_roles.py b/tests/test_access_code_roles.py
index 904d56a..81e079d 100644
--- a/tests/test_access_code_roles.py
+++ b/tests/test_access_code_roles.py
@@ -50,11 +50,14 @@ STEP6_ROLES = ("inclusion", "checks")
 
 def test_the_code_lists_match_the_owners_decision():
     # Step 7 (owner, 2026-10-05): Statistics and the gap facts added (changed from step 6's two).
-    assert CODE_ROLES == ("inclusion", "checks", "statistics", "gap_facts") and ALL_ROLES == ROLES + CODE_ROLES
-    assert not set(CODE_ROLES) & set(ALLOWED)  # the agent table is unchanged
+    # Step 8b (owner, 2026-10-07, Q5): the narrowing decision, before the lock, on structure counts only.
+    assert CODE_ROLES == ("inclusion", "checks", "statistics", "gap_facts", "narrowing")
+    assert ALL_ROLES == ROLES + CODE_ROLES
+    assert not set(CODE_ROLES) & set(ALLOWED)  # no agent role is a code role
     assert {r: set(s) for r, s in CODE_ALLOWED.items()} == {
         "inclusion": {"curation"}, "checks": {"curation"}, "statistics": {"analysis"},
-        "gap_facts": {"analysis", "closed_without_freeze"}}
+        "gap_facts": {"analysis", "closed_without_freeze"}, "narrowing": {"before_lock"}}
+    assert allowed("narrowing", "before_lock") == {"candidate_counts"}
     # set_flags: step 6 review, finding 2 (each sensitivity set's matching flags, codes and ids only).
     assert allowed("inclusion", "curation") == {"plan", "record_conditions", "flags_kind", "set_flags"}
     assert allowed("checks", "curation") == {"plan", "records_full"}
diff --git a/tests/test_access_dispatch.py b/tests/test_access_dispatch.py
index bcf30c9..195fde3 100644
--- a/tests/test_access_dispatch.py
+++ b/tests/test_access_dispatch.py
@@ -246,8 +246,9 @@ def test_a_freeze_committed_while_reads_wait_closes_the_critic_and_opens_the_ana
 
     assert _race(engine, engine.test_url, lambda: critic.get("flags_kind"), freeze) == ("denied", "stage_mismatch")
     analyst = access_for(engine, world.run, "analyst", "analysis")
-    kind, got = _outcome(lambda: analyst.get("records_full"))
-    assert kind == "allowed" and len(got) == len(world.records)
+    # Step 8b (Q6): the Analyst's list no longer holds records_full; coverage is on it at every stage.
+    kind, got = _outcome(lambda: analyst.get("coverage"))
+    assert kind == "allowed" and [s["source"] for s in got["sources"]] == ["mpea", "tamu_fcc"]
 
 
 # --- Vocabularies and unrecognized counts -------------------------------------------------------
@@ -298,8 +299,11 @@ def test_the_gap_report_input_has_codes_not_failure_text(engine):
     got = role_input(bind(engine, world.run, world.settings["analyst"]))
     assert got["coverage"]["sources"][1]["search_status"] == "failed"
     assert set(got["coverage"]["sources"][1]) == {"source", "search_status", "nothing_found", "unrecognized"}
-    rules = {d["rule"] for d in got["decisions"]["records"]}
-    assert rules == {"in_scope", "unrecognized"}
+    # Step 8b (Q6): eligibility decisions no longer reach the Analyst directly; the rule codes reach it only
+    # as the gap facts code stored (counts per rule code, from the `decisions` field read by the code role
+    # gap_facts, whose codes are tested in test_access_statistics.py).
+    assert "decisions" not in got and set(got["analyst_facts"]) == {"kind", "names"}
+    assert got["analyst_facts"]["names"]["minimums_missed"] == "none"  # the world's stored gap facts
     assert set(allowed("analyst", "closed_without_freeze")) == set(got)
 
 
diff --git a/tests/test_access_layer.py b/tests/test_access_layer.py
index a05eaa1..285964b 100644
--- a/tests/test_access_layer.py
+++ b/tests/test_access_layer.py
@@ -30,7 +30,7 @@ REPO = Path(__file__).resolve().parent.parent
 # World stage -> the access stage it is at.
 WORLD_STAGES = {"queued": "none", "failed": "none", "before_lock": "before_lock", "curation": "curation",
                 "analysis": "analysis", "closed_without_freeze": "closed_without_freeze", "final": "final",
-                "final_without_freeze": "final_without_freeze"}
+                "final_without_freeze": "final_without_freeze", "narrowed": "narrowed"}
 
 
 @pytest.fixture
@@ -57,9 +57,10 @@ def test_the_allow_list_matches_the_owners_table():
     """The table approved by the owner on 2026-10-05 (step 5 plan), field for field."""
     assert ROLES == ("planner", "curator", "critic", "analyst", "commentator")
     assert set(ALLOWED) == set(ROLES)
+    # Step 8b (owner, 2026-10-07): the Analyst also at 'narrowed' (A4); the Commentator reads nothing (A6).
     assert {r: set(s) for r, s in ALLOWED.items()} == {
         "planner": {"before_lock"}, "curator": {"registration"}, "critic": {"curation"},
-        "analyst": {"analysis", "closed_without_freeze"}, "commentator": {"final", "final_without_freeze"}}
+        "analyst": {"analysis", "closed_without_freeze", "narrowed"}, "commentator": set()}
     assert allowed("planner", "before_lock") == {"claim", "domain", "sources_meta", "tag_values", "record_counts"}
     # Owner, 2026-10-06 (step 8a, Q2): the Curator reads a source version's documentation at
     # registration, never in a run.
@@ -67,16 +68,13 @@ def test_the_allow_list_matches_the_owners_table():
     assert all(allowed("curator", stage) == frozenset() for stage in STAGES if stage != "registration")
     assert all(allowed(role, "registration") == frozenset() for role in ROLES if role != "curator")
     assert allowed("critic", "curation") == {"sources_meta", "record_metadata", "flags_kind"}
-    analysis = {"claim", "domain", "sources_meta", "plan", "records_full", "decisions", "flags_full", "results",
-                "coverage", "stage_outputs", "run_cost"}
-    assert allowed("analyst", "analysis") == analysis
-    gap = {"claim", "domain", "sources_meta", "plan", "coverage", "stored_record_counts", "decisions", "flags_kind",
-           "condition_summaries"}
-    assert allowed("analyst", "closed_without_freeze") == gap
-    assert allowed("commentator", "final") == analysis
-    # Owner, 2026-10-05 (before the step 5 review): with no dataset frozen, the Commentator gets
-    # only the gap-report input, the Analyst's gap report and the run's outcome.
-    assert allowed("commentator", "final_without_freeze") == gap | {"gap_report", "outcome"}
+    # Step 8b (owner, Q6): the Analyst receives stored facts only, the same five fields at each stage.
+    analyst = {"claim", "domain", "sources_meta", "coverage", "analyst_facts"}
+    for stage in ("analysis", "closed_without_freeze", "narrowed"):
+        assert allowed("analyst", stage) == analyst, stage
+    # Owner, 2026-10-07 (A6): the Commentator reads nothing at any stage until step 12.
+    assert all(allowed("commentator", stage) == frozenset() for stage in STAGES)
+    assert all(allowed(role, "narrowed") == frozenset() for role in ROLES if role != "analyst")
     for stage in STAGES:
         if stage != "before_lock":
             assert allowed("planner", stage) == frozenset()
@@ -92,8 +90,10 @@ def test_no_outcome_reaching_field_is_listed_for_the_planner_the_critic_or_the_g
     outcome_bearing = {"records_full", "flags_full", "results", "stage_outputs", "source_documentation", "plan"}
     for role, stage in (("planner", "before_lock"), ("critic", "curation")):
         assert not allowed(role, stage) & outcome_bearing, role
-    assert not allowed("analyst", "closed_without_freeze") & (outcome_bearing - {"plan"})
-    assert not allowed("commentator", "final_without_freeze") & (outcome_bearing - {"plan"})
+    # Step 8b: the Analyst gets none of these at any stage (its facts are named keys of stored results).
+    for stage in ("analysis", "closed_without_freeze", "narrowed"):
+        assert not allowed("analyst", stage) & outcome_bearing, stage
+    assert all(not allowed("commentator", stage) for stage in STAGES)  # A6
 
 
 # --- Every role, every stage, every field ------------------------------------------------
@@ -229,35 +229,41 @@ def test_the_dataset_freeze_changes_what_each_role_may_see(engine):
     analyst = access(engine, world, "analyst", "analysis")
     assert critic.get("flags_kind")
     with pytest.raises(AccessDenied):
-        analyst.get("records_full")
+        analyst.get("analyst_facts")
     primary = w.analysis_set(world.run)
     for rec in world.records:
         w.decide(world.run, rec)
         w.add(primary, rec)
     w.freeze(world.run, len(world.records))
+    aw.stored_facts(w, world.run, frozen=True)  # step 8b: the Analyst reads code's stored facts
     with pytest.raises(AccessDenied, match="no longer at the stage"):
         critic.get("flags_kind")
-    assert len(analyst.get("records_full")) == len(world.records)
+    assert analyst.get("analyst_facts")["names"]["pooled_estimate"] == "424.9 MPa·µm^0.5"  # step 8b: a named display string
 
 
 def test_ending_without_a_freeze_opens_only_the_gap_report_input(engine):
     world = aw.build(engine, "curation")
     gap = access(engine, world, "analyst", "closed_without_freeze")
     with pytest.raises(AccessDenied):
-        gap.get("condition_summaries")
+        gap.get("analyst_facts")
     for rec in world.records:
         world.w.decide(world.run, rec)
     aw.sql(world.w, "INSERT INTO calibration_result (run_id, status, reason) "
                     "VALUES (:r, 'unavailable', 'no_dataset_frozen')", r=world.run)
-    assert gap.get("condition_summaries")["overall"]["n_records"] == len(world.records)
-    for field in ("records_full", "flags_full", "results", "stage_outputs"):
+    aw.stored_facts(world.w, world.run, frozen=False)  # step 8b: the Analyst reads code's stored facts
+    assert gap.get("analyst_facts")["kind"] == "no_dataset_frozen"
+    # Step 8b (Q6): the step-5 gap-report fields are no longer on the Analyst's list.
+    for field in ("records_full", "flags_full", "results", "stage_outputs", "condition_summaries", "plan",
+                  "decisions", "flags_kind", "stored_record_counts"):
         with pytest.raises(AccessDenied):
             gap.get(field)
     with pytest.raises(AccessDenied):
         access(engine, world, "critic", "curation").get("flags_kind")
 
 
-def test_completion_without_a_freeze_moves_access_to_the_commentator_only(engine):
+def test_completion_without_a_freeze_closes_the_analyst_and_gives_the_commentator_nothing(engine):
+    """Step 8b (A6; was ..._moves_access_to_the_commentator_only): completion still closes the Analyst's
+    access; the Commentator reads nothing until step 12, before or after completion."""
     world = aw.build(engine, "closed_without_freeze")
     gap = access(engine, world, "analyst", "closed_without_freeze")
     commentator = access(engine, world, "commentator", "final_without_freeze")
@@ -267,36 +273,49 @@ def test_completion_without_a_freeze_moves_access_to_the_commentator_only(engine
     world.w.complete(world.run, "insufficient")
     with pytest.raises(AccessDenied, match="no longer at the stage"):
         gap.get("claim")
-    assert commentator.get("outcome") == {"status": "completed", "outcome": "insufficient", "verdict": None,
-                                          "exploratory": False}
+    with pytest.raises(AccessDenied) as denied:
+        commentator.get("outcome")
+    assert denied.value.code == "not_on_list"
     with pytest.raises(AccessDenied, match="no longer at the stage"):
         access(engine, world, "commentator", "final").get("results")
 
 
-def test_completion_after_a_freeze_moves_access_to_the_commentator_only(engine):
+def test_completion_after_a_freeze_closes_the_analyst_and_gives_the_commentator_nothing(engine):
+    """Step 8b (A6; was ..._moves_access_to_the_commentator_only)."""
     world = aw.build(engine, "analysis")
     analyst = access(engine, world, "analyst", "analysis")
     commentator = access(engine, world, "commentator", "final")
     with pytest.raises(AccessDenied):
         commentator.get("results")
-    assert analyst.get("results")
-    world.w.complete(world.run, "partly_sufficient")
+    assert analyst.get("analyst_facts")
+    # Step 8b (0006; owner, A5): a run with a plan never completes as partly sufficient.
+    world.w.complete(world.run, "insufficient", level=4)
     with pytest.raises(AccessDenied, match="no longer at the stage"):
-        analyst.get("results")
-    assert commentator.get("results")["run"]["outcome"] == "partly_sufficient"
-
-
-def test_the_commentator_without_a_freeze_gets_the_gap_report_input_the_report_and_the_outcome(engine):
-    """Owner, 2026-10-05: no outcome values and no row-level records."""
-    world = aw.build(engine, "final_without_freeze")
-    got = role_input(access(engine, world, "commentator", "final_without_freeze"))
-    assert set(got) == allowed("analyst", "closed_without_freeze") | {"gap_report", "outcome"}
-    assert got["gap_report"] == [{"stage": "analyst", "attempt": 1, "status": "done",
-                                  "output": {"note": aw.GAP_REPORT, "nested": {"values": [aw.GAP_REPORT]}}}]
-    assert got["outcome"]["outcome"] == "insufficient" and got["outcome"]["verdict"] is None
-    for field in ("records_full", "flags_full", "results", "stage_outputs", "run_cost", "record_metadata"):
-        with pytest.raises(AccessDenied):
-            access(engine, world, "commentator", "final_without_freeze").get(field)
+        analyst.get("analyst_facts")
+    with pytest.raises(AccessDenied) as denied:
+        commentator.get("results")
+    assert denied.value.code == "not_on_list"
+
+
+@pytest.mark.parametrize("world_stage", ["final", "final_without_freeze", "analysis", "narrowed"])
+def test_a_commentator_binding_reads_nothing_at_any_stage(engine, world_stage):
+    """Owner, 2026-10-07 (A6; replaces test_the_commentator_without_a_freeze_gets_the_gap_report_input_the_
+    report_and_the_outcome): until step 12 the Commentator reads nothing, every field refused and logged,
+    and its complete input is refused (never empty)."""
+    world = aw.build(engine, world_stage)
+    stage = {"final": "final", "final_without_freeze": "final_without_freeze", "analysis": "analysis",
+             "narrowed": "narrowed"}[world_stage]
+    commentator = access(engine, world, "commentator", stage)
+    before = len(audit(engine, world.run))
+    for field in sorted(FIELDS):
+        with pytest.raises(AccessDenied) as denied:
+            commentator.get(field)
+        assert denied.value.code == "not_on_list"
+    rows = audit(engine, world.run)[before:]
+    assert len(rows) == len(FIELDS) and not any(r.allowed for r in rows)
+    with pytest.raises(AccessDenied) as denied:
+        role_input(commentator)
+    assert denied.value.code == "empty_list"
 
 
 def test_experiment_flags_relax_nothing(engine):
@@ -391,8 +410,9 @@ def test_flags_kind_has_no_numbers(engine):
 
 
 def test_the_plan_is_projected_by_its_named_parts(engine):
-    world = aw.build(engine, "analysis")
-    got = access(engine, world, "analyst", "analysis").get("plan")
+    """Step 8b: read as Inclusion (code), since no agent's list holds the plan any more (Q6, A6)."""
+    world = aw.build(engine, "curation")
+    got = access(engine, world, "inclusion", "curation").get("plan")
     u = "unrecognized"
     assert got["content"] == {
         "variables": {"outcome": {"field": "yield_strength"},
@@ -436,8 +456,12 @@ def test_record_counts_are_counts_from_the_sealed_source(engine):
 
 
 def test_condition_summaries_are_ranges_and_counts_of_conditions_only(engine):
+    """Step 8b: no role's list holds this field until step 12 (Q6, A6); its reader is tested directly."""
+    from hypocurate.access.context import AccessContext
+    from hypocurate.access.fields import condition_summaries
     world = aw.build(engine, "closed_without_freeze")
-    got = access(engine, world, "analyst", "closed_without_freeze").get("condition_summaries")
+    with engine.connect() as conn:
+        got = condition_summaries(conn, AccessContext(world.run, "analyst", "closed_without_freeze"))
     assert set(got) == {"overall", "per_alloy"}
     overall = got["overall"]
     assert set(overall) == {"n_records", "grain_size", "test_temperature", "test_type", "phase_class"}
diff --git a/tests/test_access_projected.py b/tests/test_access_projected.py
index af44030..e9ff643 100644
--- a/tests/test_access_projected.py
+++ b/tests/test_access_projected.py
@@ -48,7 +48,9 @@ import pytest
 from sqlalchemy import text
 
 import access_world as aw
-from hypocurate.access import bind, role_input
+from hypocurate.access import AccessDenied, bind, role_input
+from hypocurate.access.allowlist import CODE_ROLES
+from hypocurate.access.dispatch import bind_code
 from hypocurate.access.allowlist import ROLES, allowed
 from hypocurate.db.engine import make_engine
 
@@ -101,21 +103,33 @@ def engine(migrated_database):
 def inputs_of(engine, world, role, stage=None):
     """The role's projected input, through the real dispatcher (role from the run's agent
     settings, stage from the database). `stage` is only checked."""
-    access = bind(engine, world.run, world.settings[role])
+    access = bind_code(engine, world.run, role) if role in CODE_ROLES else bind(engine, world.run, world.settings[role])
     assert stage is None or access.context.stage == stage
     return role_input(access)
 
 
 def test_the_encodings_catch_the_value_where_it_is_allowed(engine):
-    """Positive control: after the freeze the Analyst does receive the outcome values, and the
-    detector finds them in its input."""
-    world = aw.build(engine, "analysis")
-    got = inputs_of(engine, world, "analyst", "analysis")
+    """Positive control: Checks (code), which compares all values, does receive the outcome values, and
+    the detector finds them in its input. (Step 8b, Q6: was the Analyst after the freeze, whose list now
+    holds only code's stored facts.)"""
+    world = aw.build(engine, "curation")
+    got = inputs_of(engine, world, "checks", "curation")
     found = leaks(got, aw.PLANTED.values())
     for v in aw.PLANTED.values():
         assert any(f.startswith(f"{v}:") for f in found), v
-    assert repr(aw.PLANTED["yield_strength"]) in json.dumps(got["flags_full"])
-    assert repr(aw.PLANTED["yield_strength"]) in json.dumps(got["stage_outputs"])
+    assert repr(aw.PLANTED["yield_strength"]) in json.dumps(got["records_full"])
+
+
+def test_the_analysts_facts_carry_the_stored_results_by_named_keys_only(engine):
+    """Step 8b (Q6): after the freeze the Analyst receives the stored estimate; keys the facts do not name
+    (a planted value in them, a record list) never pass."""
+    world = aw.build(engine, "analysis")
+    got = inputs_of(engine, world, "analyst", "analysis")
+    assert set(got) == allowed("analyst", "analysis")
+    names = got["analyst_facts"]["names"]
+    assert names["pooled_estimate"] == "424.9 MPa·µm^0.5" and names["pooled_std_error"] == "64.4 MPa·µm^0.5"  # step 8b: display strings
+    assert "records_found" not in json.dumps(got["analyst_facts"]) and "hidden" not in json.dumps(got)
+    assert leaks(got, aw.PLANTED.values()) == []
 
 
 def test_the_planted_values_are_stored_everywhere_they_should_be(engine):
@@ -171,20 +185,30 @@ def test_no_projected_planted_value_in_the_gap_report_input(engine):
     world = aw.build(engine, "closed_without_freeze")
     got = inputs_of(engine, world, "analyst", "closed_without_freeze")
     assert set(got) == allowed("analyst", "closed_without_freeze")
-    assert got["condition_summaries"]["overall"]["n_records"] == 8
+    # Step 8b (Q6): code's stored facts (the planted value sits in keys they do not name).
+    assert got["analyst_facts"]["kind"] == "no_dataset_frozen"
+    assert got["analyst_facts"]["names"]["outcome_wording"] == "insufficient in the sources searched"
     assert leaks(got, aw.PLANTED.values()) == []
 
 
-def test_no_projected_planted_value_in_the_commentators_input_without_a_freeze(engine):
-    """Owner, 2026-10-05: on a run that ended with no dataset frozen, the Commentator gets only the
-    gap-report input, the Analyst's gap report and the run's outcome."""
+def test_no_projected_planted_value_in_the_analysts_input_at_narrowed(engine):
+    """Step 8b (A4, Q6): the partly-sufficient original before any lock: the narrowing facts only."""
+    world = aw.build(engine, "narrowed")
+    got = inputs_of(engine, world, "analyst", "narrowed")
+    assert set(got) == allowed("analyst", "narrowed")
+    facts = got["analyst_facts"]
+    assert facts["kind"] == "narrowing" and facts["names"]["parts_without_records"] == "temperature cryogenic"
+    assert leaks(got, aw.PLANTED.values()) == [] and "hidden" not in json.dumps(got)
+
+
+def test_the_commentator_receives_no_input_without_a_freeze(engine):
+    """Owner, 2026-10-07 (A6; was test_no_projected_planted_value_in_the_commentators_input_without_a_freeze):
+    until step 12 the Commentator's complete input is refused, so no planted value can reach it."""
     world = aw.build(engine, "final_without_freeze")
-    got = inputs_of(engine, world, "commentator", "final_without_freeze")
-    assert set(got) == allowed("commentator", "final_without_freeze")
-    assert aw.GAP_REPORT in json.dumps(got["gap_report"]) and got["outcome"]["outcome"] == "insufficient"
-    assert got["condition_summaries"]["overall"]["n_records"] == 8
-    assert leaks(got, aw.PLANTED.values()) == []
-    assert "extracted yield strength" not in json.dumps(got)  # the Curator's stage output stays out
+    assert allowed("commentator", "final_without_freeze") == frozenset()
+    with pytest.raises(AccessDenied) as denied:
+        inputs_of(engine, world, "commentator", "final_without_freeze")
+    assert denied.value.code == "empty_list"
 
 
 def test_no_planted_value_in_the_source_free_text_reaches_planner_or_critic(engine):
@@ -198,14 +222,16 @@ def test_no_planted_value_in_the_source_free_text_reaches_planner_or_critic(engi
 
 
 @pytest.mark.parametrize("world_stage", ["before_lock", "curation", "analysis", "closed_without_freeze", "final",
-                                         "final_without_freeze"])
+                                         "final_without_freeze", "narrowed"])
 def test_nothing_from_another_run_reaches_any_role(engine, world_stage):
-    """Owner's addition A: the original run of the narrower question and an earlier run of the
-    same hypothesis hold OTHER in records, coefficient, stage outputs and commentary."""
+    """Owner's addition A: the original run of the narrower question, an earlier run of the original
+    query and an earlier run of the same hypothesis hold OTHER in records, coefficient, stage outputs
+    and commentary. (Step 8b, 0006: a partly-sufficient original has no plan, record or coefficient, so
+    the coefficient is planted in the original query's earlier run.)"""
     world = aw.build(engine, world_stage)
     with engine.connect() as conn:
         assert conn.execute(text("SELECT count(*) FROM analysis_result WHERE run_id = :r AND estimate = :v"),
-                            dict(r=world.original_run, v=aw.OTHER)).scalar() == 1
+                            dict(r=world.original_tested_run, v=aw.OTHER)).scalar() == 1
         assert conn.execute(text("SELECT count(*) FROM commentary WHERE run_id = :r"),
                             dict(r=world.original_run)).scalar() == 1
         assert conn.execute(text("SELECT count(*) FROM record WHERE extraction_run_id = :r"),
@@ -221,6 +247,8 @@ def test_nothing_from_another_run_reaches_any_role(engine, world_stage):
             got = inputs_of(engine, world, role, world_stage)
             assert leaks(got, [aw.OTHER]) == [], role
             checked += 1
-    assert checked >= 1
+    # Step 8b (A6): after completion no role reads anything until step 12 (the Commentator's lists are
+    # empty), so nothing can reach a role there; at every other stage at least one role is checked.
+    assert checked >= 1 if world_stage not in ("final", "final_without_freeze") else checked == 0
     if world_stage == "before_lock":
         assert inputs_of(engine, world, "planner", "before_lock")["claim"]["narrower_question"] is True
diff --git a/tests/test_agent_libraries.py b/tests/test_agent_libraries.py
index d6e0606..0b8750f 100644
--- a/tests/test_agent_libraries.py
+++ b/tests/test_agent_libraries.py
@@ -52,6 +52,28 @@ def test_a_planted_env_file_read_by_a_library_is_still_refused_under_the_guard(t
     assert any(str(planted) in line for line in _guard_lines(caplog))
 
 
+def test_the_statistics_libraries_import_under_the_guard_with_no_refusal(caplog):
+    """Step 8b (owner, 2026-10-07): scipy is preloaded (PRELOADED), since importing it makes a ctypes foreign
+    call at load time; then what a guarded run imports loads with no refusal, and loads no statsmodels (test-only),
+    pandas or patsy."""
+    caplog.set_level(logging.WARNING, logger="hypocurate.access")
+    assert run_guarded(PROBE, [{"op": "statistics_libraries"}], env=dict(os.environ), timeout=300) == ["ok"]
+    assert _guard_lines(caplog) == []
+
+
+def test_after_the_statistics_libraries_a_ctypes_call_and_a_planted_env_read_are_still_refused(tmp_path, caplog):
+    """Preloading scipy changes what the guard sees only for that import."""
+    caplog.set_level(logging.WARNING, logger="hypocurate.access")
+    planted = tmp_path / ".env"
+    planted.write_text("PLANTED_SECRET=do-not-read\n")
+    result = run_guarded(PROBE, [{"op": "statistics_libraries"}, {"op": "ctypes_string_at"}, {"op": "ctypes"},
+                                 {"op": "dotenv", "path": str(planted)}], env=dict(os.environ), timeout=300)
+    assert result[0] == "ok"
+    assert result[1] == "refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code"
+    assert result[2] == "refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code"
+    assert result[3].startswith("refused: file guard: reading"), result
+
+
 def test_missing_path_entries_are_dropped_and_the_others_kept(tmp_path):
     present = tmp_path / "present"
     present.mkdir()
diff --git a/tests/test_analysis_stage.py b/tests/test_analysis_stage.py
index 0b00430..951274a 100644
--- a/tests/test_analysis_stage.py
+++ b/tests/test_analysis_stage.py
@@ -226,7 +226,10 @@ def test_a_run_with_no_dataset_frozen_gets_level_one_and_its_gap_facts(engine):
     assert facts["minimums_missed"] == ["alloys", "groups", "records", "resid_df"]
     assert facts["minimums"]["records"] == {"count": 0, "minimum": 30, "met": False}
     assert facts["eligibility_rules"] == {"missing_value": 1, "out_of_scope": 2}
-    assert facts["sources"] == [{"source": "mpea", "search_status": "searched", "nothing_found": None}]
+    # Step 8b (owner, 2026-10-07): code classifies the kind of nothing found (PRD 14.3).
+    assert facts["sources"] == [{"source": "mpea", "search_status": "searched", "nothing_found": None,
+                                 "kind": "missing_evidence"}]
+    assert facts["kind"] == "missing_evidence"
     assert val(engine, "SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0
     completion.copy_decision(engine, rid)
     assert rows_of(engine, "SELECT status, outcome, verdict, evidence_level FROM run WHERE id = :r", r=rid) == [
@@ -238,7 +241,7 @@ def test_the_gap_facts_hold_no_text_and_no_outcome_value(engine):
     analysis.run_statistics(engine, rid)
     facts = rows_of(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'gap_facts'", r=rid)[0][0]
     assert set(facts) == {"minimums", "minimums_missed", "records_lacking_fields", "eligibility_rules", "sources",
-                          "test_run_label"}
+                          "kind", "test_run_label"}  # step 8b: the run's kind of nothing found
     yields = {r[0] for r in rows_of(engine, "SELECT (harmonized->'yield_strength'->>'value') FROM record "
                                             "WHERE extraction_run_id = :r", r=rid)}
     flat = repr(facts)
@@ -387,6 +390,11 @@ def test_the_evidence_level_must_agree_with_the_outcome(engine, outcome, verdict
     update = ("UPDATE run SET status = 'completed', completed_at = now(), outcome = :o, verdict = :v, "
               "exploratory = :x, evidence_level = :e WHERE id = :r")
     params = dict(o=outcome, v=verdict, x=exploratory, e=level, r=rid)
+    if outcome == "partly_sufficient":  # step 8b (0006; owner, A5): with code's narrowing decision stored
+        with engine.begin() as conn:
+            conn.execute(text("INSERT INTO stage_result (run_id, stage) VALUES (:r, 'narrowing')"), dict(r=rid))
+            conn.execute(text("UPDATE stage_result SET status = 'done', finished_at = now(), "
+                              "output = '{\"result\": \"partly_sufficient\"}' WHERE run_id = :r"), dict(r=rid))
     if ok:
         with engine.begin() as conn:
             conn.execute(text(update), params)
@@ -552,3 +560,34 @@ def test_the_statistics_backstop_is_not_reached_in_a_normal_run(engine):
     assert val(engine, "SELECT count(*) FROM audit_log WHERE run_id = :r AND detail->>'code' = "
                        "'records_without_group'", r=rid) == 0
     assert len(out["analyses"]) == 3 + len(reference_plan(1)["sensitivity_analyses"])
+
+
+# --- step 8b: the kind of "nothing found" (owner, 2026-10-07; PRD 3.1, 14.3) ------------------------------
+
+def _src(name, status):
+    return {"source": name, "search_status": status, "nothing_found": "failed_search" if status == "failed" else None}
+
+
+DECISIONS = {"records": [{"record": 1, "source": "mpea", "eligible": True, "rule": "in_scope"},
+                         {"record": 2, "source": "tamu_fcc", "eligible": False, "rule": "missing_value"}],
+             "sets": {"primary": [1]}}
+
+
+@pytest.mark.parametrize("source, kind", [
+    (_src("mpea", "searched"), None),                       # a record of it is in the primary set
+    (_src("tamu_fcc", "searched"), "missing_evidence"),     # searched, nothing of it in the primary set
+    (_src("tamu_fcc", "failed"), "failed_search"),          # never 'missing evidence' for a failed search
+    (_src("controlled_duplicates", "not_selected"), None),
+])
+def test_each_source_gets_its_kind_of_nothing_found_from_code(source, kind):
+    assert analysis.nothing_found_kind(source, DECISIONS) == kind
+
+
+@pytest.mark.parametrize("kinds, run_kind", [
+    ([None, "missing_evidence"], None), (["missing_evidence", "failed_search"], "missing_evidence"),
+    (["failed_search", "failed_search"], "failed_search"), (["missing_evidence"], "missing_evidence"),
+])
+def test_the_runs_kind_of_nothing_found(kinds, run_kind):
+    sources = [{"search_status": "failed" if k == "failed_search" else "searched", "kind": k} for k in kinds]
+    assert analysis.run_nothing_found_kind(sources) == run_kind
+    assert "reported_negative" not in {analysis.run_nothing_found_kind(sources)}
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index b118294..0d65b72 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -60,7 +60,7 @@ def test_every_category_has_entries_and_keys_are_unique():
 # Step 7 completed tamu_grouping_unit, papers_independent, validity_checks, fixed_minimums,
 # grain_size_transformation_at_analysis and reference_numbers; records_without_group was open, with
 # the code failing closed until the owner decided it in step 7b (2026-10-06): applied "yes".
-PARTLY = {"constructed_test_runs", "agent_models"}  # step 8a: the other roles' settings come in step 8b
+PARTLY = {"constructed_test_runs"}  # step 8b: agent_models fully applied (the Planner's, Critic's and Analyst's settings)
 
 
 def test_the_owners_eight_decisions_are_recorded_as_decided():
@@ -261,9 +261,10 @@ def test_the_step_6_decisions_carry_the_owners_wording():
         # conflicts_not_pooled was made a fixed rule by the owner on 2026-10-06; step 7b (owner, 2026-10-06)
         # reworded sensitivity_one_change and eligibility_rule_order, each with its 2026-10-05 wording in history.
         changed = ("conflicts_not_pooled", "sensitivity_one_change", "eligibility_rule_order")
-        date = "2026-10-06" if key in changed else "2026-10-05"
+        # Step 8b (owner, 2026-10-07): code_role_access reworded for the narrowing role, its 2026-10-05 wording in history.
+        date = "2026-10-07" if key == "code_role_access" else "2026-10-06" if key in changed else "2026-10-05"
         assert e["decided"] == {"by": OWNER, "date": date} and e["expert_review"]["status"] == "not_reviewed"
-        if key in changed[1:]:
+        if key in changed[1:] + ("code_role_access",):
             assert e["history"][-1]["from"] == "2026-10-05"
 
 
diff --git a/tests/test_data_model.py b/tests/test_data_model.py
index a7b4729..8d87ec9 100644
--- a/tests/test_data_model.py
+++ b/tests/test_data_model.py
@@ -5,7 +5,7 @@ by a CHECK name the constraint."""
 import pytest
 from sqlalchemy.exc import IntegrityError
 
-from hypocurate.db.models import MAX_FILE_BYTES
+from hypocurate.db.models import MAX_FILE_BYTES, SUFFICIENCY_OPTIONS
 from model_builder import EXTRACTION, FP, World, files_digest, sha
 
 
@@ -127,7 +127,7 @@ def test_queries_versions_and_runs_are_never_deleted(w, table):
 
 def partly_sufficient_run(w):
     rid = w.running()
-    w.complete(rid, "partly_sufficient")
+    w.partly(rid)  # step 8b (0006): with code's narrowing decision stored, no plan
     return rid
 
 
@@ -148,6 +148,7 @@ def test_narrower_question_links_only_to_a_partly_sufficient_run(w):
 
 def test_a_partly_sufficient_run_has_no_verdict(w):
     rid = w.running()
+    w.narrowing(rid)  # step 8b (0006): so that only the verdict rule can fail
     w.rejected("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
                "verdict = 'supported', evidence_level = 6 WHERE id = :r", "ck_run_verdict_iff_sufficient", r=rid)
 
@@ -217,8 +218,14 @@ def test_a_failed_run_states_its_reason(w):
 @pytest.mark.parametrize("outcome, verdict", [("sufficient", None), ("insufficient", "supported"),
                                               ("partly_sufficient", "not_supported")])
 def test_verdict_if_and_only_if_sufficient(w, outcome, verdict):
-    rid, sets, _ = w.frozen()
-    w.result(rid, sets["primary"])  # a valid pooled result, so only the verdict rule can fail
+    if outcome == "partly_sufficient":
+        # Step 8b (0006; owner, A5): partly sufficient only with no plan and code's narrowing decision,
+        # so only the verdict rule can fail.
+        rid = w.running()
+        w.narrowing(rid)
+    else:
+        rid, sets, _ = w.frozen()
+        w.result(rid, sets["primary"])  # a valid pooled result, so only the verdict rule can fail
     with pytest.raises(IntegrityError, match="ck_run_verdict_iff_sufficient"):
         w.complete(rid, outcome, verdict)
 
@@ -256,7 +263,12 @@ def test_coefficient_only_completes_as_insufficient_without_a_verdict(w):
 @pytest.mark.parametrize("outcome", ["insufficient", "partly_sufficient", "failed"])
 def test_other_endings_need_no_pooled_result(w, outcome):
     rid = w.running()
-    w.fail(rid) if outcome == "failed" else w.complete(rid, outcome)
+    if outcome == "failed":
+        w.fail(rid)
+    elif outcome == "partly_sufficient":
+        w.partly(rid)  # step 8b (0006): with code's narrowing decision stored, no plan
+    else:
+        w.complete(rid, outcome)
     assert w.val("SELECT count(*) FROM analysis_result WHERE run_id = :r", r=rid) == 0
 
 
@@ -321,14 +333,16 @@ def test_sensitivity_analysis_keys(w, keys, match):
 
 
 @pytest.mark.parametrize("option, mins, match", [
-    ("power_based", (30, 5, 10, 10), "ck_plan_sufficiency_option"),
+    # Step 8b (0006): a query cannot have this option, so the plan's differs from the query's and the new
+    # trigger refuses first; 0001's CHECK behind it is reached in test_migrations_step8b.py.
+    ("power_based", (30, 5, 10, 10), "the plan's sufficiency option is the query's"),
     ("fixed_minimum", (0, 5, 10, 10), "ck_plan_minimums_positive"),
     ("use_available", (30, 5, 10, 0), "ck_plan_minimums_positive"),
 ])
 def test_sufficiency_option_and_minimums(w, option, mins, match):
     """Power-based is not a gate in sprint 1 (owner's addition 1); minimums are kept under both options."""
     with pytest.raises(IntegrityError, match=match):
-        w.lock(w.running(), option=option, mins=mins)
+        w.lock(w.running(sufficiency=option if option in SUFFICIENCY_OPTIONS else "fixed_minimum"), option=option, mins=mins)
 
 
 def test_power_assumptions_are_an_information_field(w):
@@ -758,7 +772,7 @@ def test_no_curation_once_the_run_has_ended(w, ending):
         "WHERE extraction_run_id = :r AND source_item_key = 'undecided'",
         "INSERT INTO analysis_set_record VALUES (:s, :c)",
         "INSERT INTO flag (run_id, kind, category) VALUES (:r, 'k', 'c')",
-        "UPDATE flag SET critic_class = 'comparable', classified_at = now() WHERE id = :f",
+        "UPDATE flag SET critic_class = 'different_specimens_or_conditions', classified_at = now() WHERE id = :f",
         "INSERT INTO flag_record VALUES (:f, :c)",
         "UPDATE run_source SET search_status = 'searched', decided_at = now() WHERE run_id = :r AND search_status = 'pending'",
     ]:
@@ -861,9 +875,9 @@ def test_a_flag_is_classified_once_before_the_freeze(w):
     rid = w.running()
     f = flag(w, rid)
     w.rejected("UPDATE flag SET compared_values = '{}' WHERE id = :f", "classification", f=f)
-    w.run_sql("UPDATE flag SET critic_class = 'comparable', critic_reason = 'same test', classified_at = now() "
+    w.run_sql("UPDATE flag SET critic_class = 'different_specimens_or_conditions', critic_reason = 'same test', classified_at = now() "
               "WHERE id = :f", f=f)
-    w.rejected("UPDATE flag SET critic_class = 'other', classified_at = now() WHERE id = :f", "classified once", f=f)
+    w.rejected("UPDATE flag SET critic_class = 'cannot_tell', classified_at = now() WHERE id = :f", "classified once", f=f)
     w.rejected("DELETE FROM flag", "never deleted")
 
 
diff --git a/tests/test_migrations.py b/tests/test_migrations.py
index 587bec5..7e86c38 100644
--- a/tests/test_migrations.py
+++ b/tests/test_migrations.py
@@ -62,6 +62,8 @@ def expected_triggers() -> set[tuple[str, str]]:
     m5 = MIGRATION_0005
     names |= {(t, f"hc_{t}_append_only") for t in m5.APPEND_ONLY} | {(t, f"hc_{t}_no_truncate") for t in m5.APPEND_ONLY}
     names |= {(t, f) for t, _, f in m5.CHECKED}
+    m6 = ScriptDirectory(str(migrate.MIGRATIONS)).get_revision("0006").module  # step 8b
+    names |= {(t, trigger) for t, _, trigger, _ in m6.CHECKED}
     return names
 
 
diff --git a/tests/test_migrations_step8a.py b/tests/test_migrations_step8a.py
index f0266dd..cbb187e 100644
--- a/tests/test_migrations_step8a.py
+++ b/tests/test_migrations_step8a.py
@@ -53,8 +53,9 @@ def checks_of(function_sql: str) -> list[str]:
 
 # --- the migration -------------------------------------------------------------------------------
 
-def test_0005_is_the_head_and_follows_0004():
-    assert migrate.head_revision() == "0005" and M0005.down_revision == "0004"
+def test_0005_follows_0004():
+    """Step 8b: 0006 is the head now (test_migrations_step8b.py)."""
+    assert M0005.down_revision == "0004"
 
 
 @pytest.mark.parametrize("name, kept", [("hc_model_call_insert", "MODEL_CALL_INSERT_0001"),
@@ -111,7 +112,7 @@ def test_the_downgrade_refuses_while_0005_is_in_use(db):
     before = snapshot(db)
     with pytest.raises(Exception, match="0005 is in use"):
         migrate.downgrade(db, "0004")
-    assert snapshot(db) == before and migrate.current_revision(db) == "0005"
+    assert snapshot(db) == before and migrate.current_revision(db) == migrate.head_revision()
 
 
 # --- source files by role ------------------------------------------------------------------------
diff --git a/tests/test_reference_numbers.py b/tests/test_reference_numbers.py
index 9653d30..800af4a 100644
--- a/tests/test_reference_numbers.py
+++ b/tests/test_reference_numbers.py
@@ -80,7 +80,7 @@ def test_half_a_unit_in_the_last_digit():
 
 
 def _run(engine, sources, option="fixed_minimum"):
-    rid = pw.dispatched_run(engine, sources=sources)
+    rid = pw.dispatched_run(engine, sources=sources, sufficiency=option)  # step 8b (0006): the query's option
     plan = reference_plan(pw.version_of(engine, rid))
     plan["sufficiency"]["option"] = option
     checkpoints.lock_rules(engine, rid, plan)
```
## 5. Assumptions register (135 entries; 12 new, 9 changed)

### New: `query_sufficiency_option`

```json
{
 "key": "query_sufficiency_option",
 "name": "The data-sufficiency option is the query's",
 "state": "in_force",
 "statement": "The data-sufficiency option (fixed minimum or use what is available) is a parameter of the query, chosen before dispatch: it is stored on the hypothesis version (default 'fixed_minimum'), can change only while the version is a draft, a narrower question has its original's, and the locked plan's option must equal it (checked by code and by the database). No model sets it.",
 "value": {
  "text": "on the hypothesis version; the plan's must equal it",
  "unit": null
 },
 "category": "statistical",
 "affects": "Which sufficiency rule a run's plan locks (PRD 5.8).",
 "reason": "CLAUDE.md rule 7 calls it a query parameter; before step 8b it existed only in the plan, which the Planner fills.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answer A2."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.db.models:SUFFICIENCY_OPTIONS",
    "equals": [
     "fixed_minimum",
     "use_available"
    ]
   },
   {
    "ref": "sql:hc_plan_query"
   },
   {
    "ref": "sql:hc_version_option"
   },
   {
    "ref": "sql:ck_hypothesis_version_sufficiency_option"
   }
  ],
  "note": null
 },
 "notes": [],
 "tests": [
  "tests/test_migrations_step8b.py::test_a_version_without_an_option_uses_the_default",
  "tests/test_migrations_step8b.py::test_the_option_can_change_while_a_draft_and_never_after",
  "tests/test_migrations_step8b.py::test_a_narrower_question_has_its_originals_option",
  "tests/test_migrations_step8b.py::test_the_plans_option_is_the_querys",
  "tests/test_queries.py::test_the_querys_option_is_chosen_before_dispatch",
  "tests/test_planner_narrowing.py::test_an_invalid_plan_is_corrected_once_naming_only_the_code_then_the_stage_fails"
 ],
 "history": []
}
```
### New: `partly_sufficient_rules`

```json
{
 "key": "partly_sufficient_rules",
 "name": "Partly sufficient: before the lock, on counts, never tested",
 "state": "in_force",
 "statement": "A run is completed as partly sufficient only when code's narrowing decision, taken after the Planner and before any lock, finds a claim part with no record that has a grain size and the outcome at an accepted status, and the narrower scope of the parts that have such records, built by code from its counts, makes a valid plan (a narrower scope the Planner gives is stored and never used). The original then locks no plan and stores no record (the stage 'narrowed'; the database refuses a plan after such a decision and a partly-sufficient run with a plan, a record or no stored decision); the Analyst explains the narrowing facts; the decision is copied (outcome 'partly_sufficient', no verdict, level 1); the narrower question is created as a separate, linked, submitted query. If the Analyst fails for any reason, the run still completes as partly sufficient and the narrower question is still created.",
 "value": {
  "text": "no plan, no record, code's decision copied, level 1",
  "unit": null
 },
 "category": "statistical",
 "affects": "Which runs are partly sufficient (PRD 3.1, 5.4).",
 "reason": "PRD 5.4: the narrowing is decided on record counts, never on outcomes; the original receives no verdict.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answers Q5, A1, A4, A5, B2."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "sql:hc_run_partly_sufficient"
   },
   {
    "ref": "python:hypocurate.pipeline.completion:copy_partly_sufficient"
   },
   {
    "ref": "python:hypocurate.access.allowlist:STAGES"
   }
  ],
  "note": null
 },
 "notes": [],
 "tests": [
  "tests/test_migrations_step8b.py::test_a_run_completes_as_partly_sufficient_with_its_narrowing_decision_and_no_plan",
  "tests/test_migrations_step8b.py::test_partly_sufficient_needs_a_done_narrowing_decision_of_partly_sufficient",
  "tests/test_migrations_step8b.py::test_partly_sufficient_is_refused_for_a_run_with_a_plan",
  "tests/test_migrations_step8b.py::test_no_plan_is_locked_after_a_narrowing_decision_of_partly_sufficient",
  "tests/test_access_step8b.py::test_no_plan_is_locked_at_narrowed_by_code_or_by_the_database",
  "tests/test_orchestrator.py::test_14_3_a_partly_sufficient_original_and_its_narrower_question",
  "tests/test_orchestrator.py::test_b2_the_analyst_failing_on_the_partly_path_still_completes_and_creates_the_narrower_question",
  "tests/test_orchestrator.py::test_live_run_c_the_planner_gives_no_narrower_scope_and_code_builds_it"
 ],
 "history": [
  {
   "value": "A run is completed as partly sufficient only when code's narrowing decision, taken after the Planner and before any lock, finds a claim part with no record that has a grain size and the outcome at an accepted status, and the Planner proposed exactly the narrower scope of the parts that have such records, which makes a valid plan. The original then locks no plan and stores no record (the stage 'narrowed'; the database refuses a plan after such a decision and a partly-sufficient run with a plan, a record or no stored decision); the Analyst explains the narrowing facts; the decision is copied (outcome 'partly_sufficient', no verdict, level 1); the narrower question is created as a separate, linked, submitted query. If the Analyst fails for any reason, the run still completes as partly sufficient and the narrower question is still created.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after live run C failed 'narrower_missing': code builds the narrower scope from its own counts; the Planner cannot see which part has no usable record, so a proposal of its is stored and never used."
  }
 ]
}
```
### New: `narrowing_decision`

```json
{
 "key": "narrowing_decision",
 "name": "The narrowing decision counts structure only",
 "state": "in_force",
 "statement": "Code's narrowing decision reads, before the lock, only counts of structure per chosen source from the sealed version recorded at dispatch (never an outcome value). Claim parts are each phase class, temperature band (with its range) and test type of the claim's scope as the Planner stated it; alloy class is not countable. A part's count is the records that have a grain size and the outcome at an accepted status, fall in that part and in the claim's values on the other dimensions, with temperature judged as eligibility rule 3 judges it. A claim with more than one alloy class, temperature band or test type is not one plan: unless the partly-sufficient path applies, the run fails before the lock with a stated reason (submit one question per band, test type and alloy class). The decision stores the counts' fingerprint and each source version's fingerprint. The narrower scope is the claim's scope less exactly the parts with no usable record, built by code; a narrower scope the Planner gives is stored and never used (owner, 2026-10-07, after live run C). The decision also stores the Planner's mark of each scope part (stated by the claim or defaulted), which the Analyst's facts carry as notes.",
 "value": {
  "text": "counts per claim part; zero parts; exact narrower scope",
  "unit": null
 },
 "category": "statistical",
 "affects": "Partly sufficient and 'claim not one plan' (PRD 5.4).",
 "reason": "Owner's Q5; A11 for two bands; Claude Code extended A11 to test types and alloy classes, since a plan's tags allow one of each (stated to the owner).",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answers Q5, A11."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.narrowing:DIMENSIONS",
    "equals": [
     "phase_class",
     "test_type",
     "temperature_band"
    ]
   },
   {
    "ref": "python:hypocurate.pipeline.narrowing:decide"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.planner:one_plan"
   }
  ],
  "note": null
 },
 "notes": [],
 "tests": [
  "tests/test_planner_narrowing.py::test_every_part_with_records_proceeds",
  "tests/test_planner_narrowing.py::test_a_part_with_none_and_the_exact_narrower_scope_is_partly_sufficient",
  "tests/test_planner_narrowing.py::test_code_builds_the_narrower_scope_and_never_uses_the_planners",
  "tests/test_planner_narrowing.py::test_two_bands_each_with_records_are_not_one_plan",
  "tests/test_planner_narrowing.py::test_no_part_with_records_proceeds_to_an_insufficient_run",
  "tests/test_planner_narrowing.py::test_a_record_counts_only_with_a_grain_size_the_outcome_and_a_known_condition",
  "tests/test_planner_narrowing.py::test_the_frozen_sources_make_the_cryogenic_claim_partly_sufficient",
  "tests/test_access_step8b.py::test_candidate_counts_are_counts_of_structure_only",
  "tests/test_orchestrator.py::test_a_run_fails_before_the_lock_with_a_stated_reason",
  "tests/test_planner_narrowing.py::test_a_one_plan_claim_with_a_part_without_records_is_narrowed_by_code",
  "tests/test_planner_narrowing.py::test_a_narrower_scope_that_is_not_one_plan_is_not_used",
  "tests/test_planner_narrowing.py::test_the_stated_marks_are_kept_with_the_answer_and_the_narrowing_decision"
 ],
 "history": [
  {
   "value": "Code's narrowing decision reads, before the lock, only counts of structure per chosen source from the sealed version recorded at dispatch (never an outcome value). Claim parts are each phase class, temperature band (with its range) and test type of the claim's scope as the Planner stated it; alloy class is not countable. A part's count is the records that have a grain size and the outcome at an accepted status, fall in that part and in the claim's values on the other dimensions, with temperature judged as eligibility rule 3 judges it. A claim with more than one alloy class, temperature band or test type is not one plan: unless the partly-sufficient path applies, the run fails before the lock with a stated reason (submit one question per band, test type and alloy class). The decision stores the counts' fingerprint and each source version's fingerprint.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after live run C failed 'narrower_missing': code builds the narrower scope from its own counts; the Planner cannot see which part has no usable record, so a proposal of its is stored and never used."
  },
  {
   "value": "Code's narrowing decision reads, before the lock, only counts of structure per chosen source from the sealed version recorded at dispatch (never an outcome value). Claim parts are each phase class, temperature band (with its range) and test type of the claim's scope as the Planner stated it; alloy class is not countable. A part's count is the records that have a grain size and the outcome at an accepted status, fall in that part and in the claim's values on the other dimensions, with temperature judged as eligibility rule 3 judges it. A claim with more than one alloy class, temperature band or test type is not one plan: unless the partly-sufficient path applies, the run fails before the lock with a stated reason (submit one question per band, test type and alloy class). The decision stores the counts' fingerprint and each source version's fingerprint. The narrower scope is the claim's scope less exactly the parts with no usable record, built by code; a narrower scope the Planner gives is stored and never used (owner, 2026-10-07, after live run C).",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after the refused live Analyst check: placeholders (the Analyst writes no digits), fewer facts built by code, and the stated/defaulted marks, in one change."
  }
 ]
}
```
### New: `narrower_question`

```json
{
 "key": "narrower_question",
 "name": "The narrower question and its plan",
 "state": "in_force",
 "statement": "A narrower question is a separate query linked to its original run, created as submitted with the original's domain, sources and sufficiency option, and a text built by code (NARROWER_TEXT: the original claim and the narrower scope in words). It is dispatched by its number after a named person confirms its domain; its run locks exactly the narrower plan the original's narrowing decision stored (the Planner bypassed), and is refused before the lock, with a stated reason, if any of its source versions differs from those the counts were taken on.",
 "value": {
  "text": "code-built text; the stored plan; same source versions",
  "unit": null
 },
 "category": "operational",
 "affects": "How a narrower question is created and run (PRD 5.4).",
 "reason": "The narrower plan is the one the counts were taken on; a fresh Planner could widen it again.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answers Q10, A8, B1."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.queries:NARROWER_TEXT",
    "equals": "{original} (narrower question: {scope})"
   },
   {
    "ref": "python:hypocurate.pipeline.queries:create_narrower"
   }
  ],
  "note": null
 },
 "notes": [],
 "tests": [
  "tests/test_queries.py::test_the_narrower_question_is_a_separate_linked_submitted_query",
  "tests/test_orchestrator.py::test_14_3_a_partly_sufficient_original_and_its_narrower_question",
  "tests/test_orchestrator.py::test_b1_a_narrower_question_on_other_source_versions_is_refused_with_a_reason"
 ],
 "history": []
}
```
### New: `planner_answer`

```json
{
 "key": "planner_answer",
 "name": "What the Planner may answer and what code does with it",
 "state": "in_force",
 "statement": "The Planner answers one JSON object of fixed form: whether the claim belongs to the domain, the claim's scope (alloy classes, phase classes, test types, temperature bands with their ranges), and for each scope part whether the claim states it (true) or the Planner used the default (false), a mark code requires, the outcome field, exclusion rules from the menu, and a narrower scope that should be null (code decides any narrower scope; one given anyway is stored and never used); values from fixed lists only, no free text and no other key. Code builds the plan from the profile's defaults and only these parameters: the model, the rules, the eligibility rules, the calibration and the sufficiency option never come from the model. An answer whose shape, values or plan are not valid is corrected once, naming only the code, then the run fails before the lock. A claim judged to be of another domain fails the run before the lock (PRD 5.5).",
 "value": {
  "text": "fixed form; plan built by code",
  "unit": null
 },
 "category": "operational",
 "affects": "Every plan a live Planner contributes to.",
 "reason": "CLAUDE.md rule 1: code decides; agents advise. PRD 5.2: exclusion rules from a menu.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.planner:build_plan"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.planner:make_check"
   }
  ],
  "note": null
 },
 "notes": [
  "The Planner's instruction text and limits are drafts by Claude Code for the owner's review before the live set (B3)."
 ],
 "tests": [
  "tests/test_planner_narrowing.py::test_the_planners_complete_request_holds_no_outcome_value",
  "tests/test_planner_narrowing.py::test_a_valid_answer_is_stored_and_its_plan_is_the_reference_plan",
  "tests/test_planner_narrowing.py::test_an_invalid_plan_is_corrected_once_naming_only_the_code_then_the_stage_fails",
  "tests/test_planner_narrowing.py::test_a_claim_of_another_domain_is_a_valid_answer",
  "tests/test_planner_narrowing.py::test_an_answer_without_the_stated_marks_is_invalid"
 ],
 "history": [
  {
   "value": "The Planner answers one JSON object of fixed form: whether the claim belongs to the domain, the claim's scope (alloy classes, phase classes, test types, temperature bands with their ranges), the outcome field, exclusion rules from the menu, and optionally a narrower scope; values from fixed lists only, no free text and no other key. Code builds the plan from the profile's defaults and only these parameters: the model, the rules, the eligibility rules, the calibration and the sufficiency option never come from the model. An answer whose shape, values or plan are not valid is corrected once, naming only the code, then the run fails before the lock. A claim judged to be of another domain fails the run before the lock (PRD 5.5).",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after live run C failed 'narrower_missing': code builds the narrower scope from its own counts; the Planner cannot see which part has no usable record, so a proposal of its is stored and never used."
  },
  {
   "value": "The Planner answers one JSON object of fixed form: whether the claim belongs to the domain, the claim's scope (alloy classes, phase classes, test types, temperature bands with their ranges), the outcome field, exclusion rules from the menu, and a narrower scope that should be null (code decides any narrower scope; one given anyway is stored and never used); values from fixed lists only, no free text and no other key. Code builds the plan from the profile's defaults and only these parameters: the model, the rules, the eligibility rules, the calibration and the sufficiency option never come from the model. An answer whose shape, values or plan are not valid is corrected once, naming only the code, then the run fails before the lock. A claim judged to be of another domain fails the run before the lock (PRD 5.5).",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after the refused live Analyst check: placeholders (the Analyst writes no digits), fewer facts built by code, and the stated/defaulted marks, in one change."
  }
 ]
}
```
### New: `critic_classes`

```json
{
 "key": "critic_classes",
 "name": "The Critic's classes and reason",
 "state": "in_force",
 "statement": "The Critic classifies each flag code raised with one of four classes: same measurement reported twice, different specimens or conditions, possible transcription or unit error, cannot tell from the metadata; with a reason of at most 300 characters, shown to people only and never truncated. It receives each flag's kind, category and record ids and the named records' metadata, never the numbers compared. An entry that fails code's check stays unclassified; a failed call leaves every flag of its batch unclassified and the run goes on. No code decision reads the class or the reason: Inclusion, the freeze, Statistics, the narrowing and completion read flags only through fields that do not carry them.",
 "value": {
  "text": "four classes; reason for people only; read by no decision",
  "unit": null
 },
 "category": "data_handling",
 "affects": "Flags' classification shown to people (PRD 3 step 6).",
 "reason": "PRD 4: the Critic never chooses between values; owner's standing requirement that no code decision reads the class.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answer A7."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.vocabulary:CRITIC_CLASSES"
   },
   {
    "ref": "python:hypocurate.access.vocabulary:CRITIC_REASON_MAX",
    "equals": 300
   },
   {
    "ref": "sql:ck_flag_critic_class"
   },
   {
    "ref": "sql:ck_flag_critic_reason"
   }
  ],
  "note": null
 },
 "notes": [
  "The Critic's instruction text and limits are drafts by Claude Code for the owner's review before the live set (B3)."
 ],
 "tests": [
  "tests/test_critic.py::test_the_critics_complete_request_holds_no_compared_number_or_outcome",
  "tests/test_critic.py::test_each_valid_entry_is_written_once_and_an_invalid_one_is_left_unclassified",
  "tests/test_critic.py::test_changing_every_class_changes_no_decision_set_fingerprint_or_result",
  "tests/test_critic.py::test_no_decision_path_reads_the_critics_class",
  "tests/test_migrations_step8b.py::test_each_critic_class_is_accepted",
  "tests/test_migrations_step8b.py::test_a_class_outside_the_list_or_an_unbounded_reason_is_refused"
 ],
 "history": []
}
```
### New: `analyst_facts_only`

```json
{
 "key": "analyst_facts_only",
 "name": "The Analyst receives stored facts only",
 "state": "in_force",
 "statement": "The Analyst receives the claim's text, the domain, the chosen sources' names and grouping, and named facts built by code from what it stored, each a finished display string or ready-made phrase it refers to as {name}: the decision and its wordings; the plan's threshold, option and minimums; per scope part whether the claim stated it or the Planner assumed it (or that the plan was fixed); the pooled result and its counts against each minimum; per source its result and label; both calibrations of the pooled result; a summary of the sensitivity sets built by code (how many; how many under each per-source label, classified against the pooled result by the same function; the sets not labelled 'agrees'; the smallest and largest estimate with their sets; the result without the group holding the largest share of slope information); the gap facts; at 'narrowed' the claim's parts, their counts and the narrower scope. The full per-set numbers are not sent (step 10 shows them in a table drawn by code). Below the minimums no name gives an estimate, a standard error, a p-value or the paper figures; the fixed-noise detection and false-positive shares, which use no outcome value, stay. It never receives a record-level value or identity, a Critic's class or reason, or a stage's text, and never sets the outcome, verdict, label or level. Owner's additions (2026-10-07): code-built sentences the Analyst uses whole: a model sentence (what was fitted, and that the estimate is its coefficient), for a fixed-plan run a sentence that the scope was set by the fixed reference plan and not read from the claim, a direction note from the estimate's sign and the claim's direction (the plan's alternative), one calibration summary covering both calibrations and their flags, and one sentence saying what a group is; plain names for the two calibrations (noise levels estimated from the data; fixed illustrative noise levels); plain wording for the four labels ('in agreement with the pooled result', 'too few groups to test alone', ...); 'groups' throughout. The instruction asks the Analyst to open by restating the claim, then the outcome and verdict, then the main cautions, not with the query number, and not to draw conclusions beyond the facts and notes given.",
 "value": {
  "text": "named stored facts; nothing outcome-derived below the minimums",
  "unit": null
 },
 "category": "data_handling",
 "affects": "What the Analyst can say (PRD 3 step 8).",
 "reason": "Owner's Q6 and standing requirement.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answer Q6."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.fields:analyst_facts"
   },
   {
    "ref": "python:hypocurate.pipeline.analyst_names:analysis_names"
   },
   {
    "ref": "python:hypocurate.pipeline.analyst_names:sensitivity_summary"
   },
   {
    "ref": "python:hypocurate.pipeline.analyst_names:LABEL_WORDS"
   },
   {
    "ref": "python:hypocurate.pipeline.analyst_names:MODEL_SENTENCE"
   },
   {
    "ref": "python:hypocurate.pipeline.analyst_names:FIXED_PLAN_SENTENCE",
    "equals": "The scope was set by the fixed reference plan and was not read from the claim."
   },
   {
    "ref": "python:hypocurate.pipeline.analyst_names:calibration_summary"
   },
   {
    "ref": "python:hypocurate.pipeline.analyst_names:direction_note"
   }
  ],
  "note": null
 },
 "notes": [],
 "tests": [
  "tests/test_access_step8b.py::test_below_the_minimums_the_analysts_facts_hold_nothing_computed_from_outcomes",
  "tests/test_access_step8b.py::test_above_the_minimums_the_analysts_facts_carry_the_stored_estimate",
  "tests/test_analyst.py::test_below_the_minimums_the_analysts_request_holds_no_outcome_value",
  "tests/test_analyst.py::test_the_analyst_changes_no_stored_decision",
  "tests/test_analyst.py::test_a_run_below_the_minimums_offers_no_estimate_names",
  "tests/test_orchestrator.py::test_the_analyst_is_told_which_scope_parts_the_claim_stated_and_which_were_assumed",
  "tests/test_analyst.py::test_the_facts_carry_display_strings_and_phrases",
  "tests/test_analyst.py::test_the_facts_carry_the_code_built_sentences_units_and_the_nominal_level",
  "tests/test_analyst.py::test_the_calibration_summary_covers_both_calibrations_and_their_flags",
  "tests/test_analyst.py::test_the_direction_note_is_built_from_the_sign_and_the_claims_direction",
  "tests/test_analyst.py::test_the_plain_label_for_a_single_group_source",
  "tests/test_analyst.py::test_a_text_using_the_code_built_sentences_is_accepted"
 ],
 "history": [
  {
   "value": "The Analyst receives the claim, the domain, the sources' descriptions, the coverage and code's stored facts by named keys (the decision and its wordings; per analysis its counts, checks, minimums and, unless withheld, estimate, standard error, degrees of freedom, p-value, labels and calibration shares; the gap facts; the plan's scope, option, minimums and threshold; at 'narrowed' only the narrowing facts). Below the minimums it receives no estimate and nothing computed from outcome values; the fixed-noise detection rate, which uses none, stays. It never receives a record-level value or identity, a Critic's class or reason, or a stage's text. It never sets the outcome, verdict, label or level.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after the live set and the diagnostic call: rounding and phrasing are done by code; the Analyst quotes display strings and ready-made phrases."
  },
  {
   "value": "The Analyst receives the claim, the domain, the sources' descriptions, the coverage and code's stored facts by named keys (the decision and its wordings; per analysis its counts, checks, minimums and, unless withheld, estimate, standard error, degrees of freedom, p-value, labels and calibration shares; the gap facts; the plan's scope, option, minimums and threshold; at 'narrowed' only the narrowing facts). Below the minimums it receives no estimate and nothing computed from outcome values; the fixed-noise detection rate, which uses none, stays. It never receives a record-level value or identity, a Critic's class or reason, or a stage's text. It never sets the outcome, verdict, label or level. Every number reaches it as a display string rounded by code; a p-value only inside its ready-made phrase, with its fixed description; the paper figures only together, in their phrase.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after the refused live Analyst check: placeholders (the Analyst writes no digits), fewer facts built by code, and the stated/defaulted marks, in one change."
  },
  {
   "value": "The Analyst receives the claim's text, the domain, the chosen sources' names and grouping, and named facts built by code from what it stored, each a finished display string or ready-made phrase it refers to as {name}: the decision and its wordings; the plan's threshold, option and minimums; per scope part whether the claim stated it or the Planner assumed it (or that the plan was fixed); the pooled result and its counts against each minimum; per source its result and label; both calibrations of the pooled result; a summary of the sensitivity sets built by code (how many; how many under each per-source label, classified against the pooled result by the same function; the sets not labelled 'agrees'; the smallest and largest estimate with their sets; the result without the group holding the largest share of slope information); the gap facts; at 'narrowed' the claim's parts, their counts and the narrower scope. The full per-set numbers are not sent (step 10 shows them in a table drawn by code). Below the minimums no name gives an estimate, a standard error, a p-value or the paper figures; the fixed-noise detection and false-positive shares, which use no outcome value, stay. It never receives a record-level value or identity, a Critic's class or reason, or a stage's text, and never sets the outcome, verdict, label or level.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after reading the first accepted live explanation: code-built sentences so the Analyst need not interpret; units; one form for rates and the threshold; interval phrases; plain names and labels; 'groups' throughout."
  }
 ]
}
```
### New: `analyst_text_checks`

```json
{
 "key": "analyst_text_checks",
 "name": "The Analyst's number and wording checks",
 "state": "in_force",
 "statement": "The Analyst writes no digits: every number, p-value, set of paper figures, the outcome and the verdict are {name} placeholders of its named facts, and code renders the finished text. Before rendering, code refuses a name that is not among the facts given ('unknown_name'), any digit outside a placeholder ('digit_outside_placeholder'), a text that does not use {outcome_wording} (and {verdict_wording} when there is a verdict), and, when there is a verdict, a text that does not use {pooled_p_phrase} and {pooled_figures_phrase} ('result_phrases_missing'). A p-value and the paper figures exist only inside their phrase names: no other name exposes them (tested). On the finished text: no forbidden phrase ('do not exist', 'proves', ...), never 'confirms the claim' or 'confirms the hypothesis' and no causal language ('causes', 'caused by', 'causal') even with a verdict, no verdict where there is none, the effective number never called 'independent', and every number one of the facts' (a safeguard). Each failure is corrected once, naming only the code; failing twice the text is discarded and the run shows 'explanation unavailable'; the stage keeps counts or rule names, never text. The finished text and its template are stored. The failure facts (counts or rule names) are stored for every attempt that failed, also when a later attempt was accepted (owner, 2026-10-07).",
 "value": {
  "text": "numbers as given; wording rules",
  "unit": null
 },
 "category": "operational",
 "affects": "The Analyst's text (CLAUDE.md rule 13; PRD 5.9 for the Commentator later).",
 "reason": "Owner's Q8: the number check is written for reuse by the Commentator.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answer Q8."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.text_checks:FIXED_NUMBERS",
    "equals": [
     "1",
     "2",
     "95",
     "95%",
     "0.5",
     "-0.5"
    ]
   },
   {
    "ref": "python:hypocurate.pipeline.agents.text_checks:FORBIDDEN"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.text_checks:ALWAYS_FORBIDDEN"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.text_checks:REQUIRED",
    "equals": [
     "outcome_wording"
    ]
   },
   {
    "ref": "python:hypocurate.pipeline.agents.text_checks:REQUIRED_WITH_VERDICT",
    "equals": [
     "pooled_p_phrase",
     "pooled_figures_phrase"
    ]
   }
  ],
  "note": null
 },
 "notes": [
  "The wording lists, FIXED_NUMBERS and the phrases' wording are drafts by Claude Code, extended by the owner on 2026-10-07."
 ],
 "tests": [
  "tests/test_analyst.py::test_numbers_exactly_as_given_match",
  "tests/test_analyst.py::test_a_number_not_given_as_shown_is_caught",
  "tests/test_analyst.py::test_the_wording_rules",
  "tests/test_analyst.py::test_a_text_failing_a_check_twice_is_discarded",
  "tests/test_analyst.py::test_an_unparsable_answer_stores_its_form_facts_and_no_text",
  "tests/test_analyst.py::test_a_correct_text_is_accepted_and_rendered_with_the_exact_strings",
  "tests/test_analyst.py::test_the_diagnostic_answers_shape_is_refused_and_the_same_with_placeholders_is_stored",
  "tests/test_analyst.py::test_a_text_breaking_each_rule_is_refused",
  "tests/test_analyst.py::test_a_refused_text_stores_counts_or_rule_names_and_no_text",
  "tests/test_analyst.py::test_the_failure_facts_of_a_corrected_attempt_are_stored"
 ],
 "history": [
  {
   "value": "Every number in the Analyst's text must equal a number of the facts it was given, at the precision shown (plain, percentage, scientific notation), apart from the method's own numbers (the exponent -1/2, the 95% interval, validity checks 1 and 2); this checks numerical consistency only, not interpretation. The text must contain code's outcome wording verbatim (so always 'in the sources searched'), the verdict wording verbatim when there is a verdict, no forbidden phrase (for example 'do not exist', 'proves'), and no verdict where there is none. A text failing either check is corrected once, naming only the code; failing twice it is discarded and the run shows 'explanation unavailable'.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner's additions before the live set (2026-10-07): always-forbidden causal and 'confirms' phrases; p-value with 'approximate'; effective number never 'independent'; informative-paper count with its three figures; the Analyst's instruction extended to match."
  },
  {
   "value": "Every number in the Analyst's text must equal a number of the facts it was given, at the precision shown (plain, percentage, scientific notation), apart from the method's own numbers (the exponent -1/2, the 95% interval, validity checks 1 and 2); this checks numerical consistency only, not interpretation. The text must contain code's outcome wording verbatim (so always 'in the sources searched'), the verdict wording verbatim when there is a verdict, no forbidden phrase (for example 'do not exist', 'proves'), and no verdict where there is none. A text failing either check is corrected once, naming only the code; failing twice it is discarded and the run shows 'explanation unavailable'. Owner's additions (2026-10-07): always forbidden, even with a verdict: 'confirms the claim', 'confirms the hypothesis', 'causes', 'caused by', 'causal'; a sentence giving a p-value must contain 'approximate'; a sentence naming the effective number (by name or value) must not contain 'independent'; if the text gives the informative-paper count, it must also give the effective number, the largest share and the degrees of freedom of the same analysis.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after the live set and the diagnostic call: rounding and phrasing are done by code; the Analyst quotes display strings and ready-made phrases."
  },
  {
   "value": "The Analyst's facts carry every number as its display string, rounded by code (register 'display_precision'), and one ready-made phrase per p-value (the value and 'approximate, nominal, one-sided') and per set of paper figures (informative papers, effective number, largest share, degrees of freedom). Every number in the text must be, as a token, a number the facts give, apart from the method's own numbers (validity checks 1 and 2, the 95% interval, the exponent -1/2); thousands separators are ignored; this checks numerical consistency only, not interpretation. The text must contain code's outcome wording verbatim (so always 'in the sources searched'), the verdict wording verbatim when there is a verdict, no forbidden phrase ('do not exist', 'proves', ...), never 'confirms the claim' or 'confirms the hypothesis' and no causal language ('causes', 'caused by', 'causal') even with a verdict, and no verdict where there is none. A p-value may appear only inside its ready-made phrase, the paper figures only inside theirs, and a sentence naming the effective number must not call it 'independent'. A text failing a check is corrected once, naming only the code; failing twice it is discarded, the run shows 'explanation unavailable', and the stage keeps fixed facts about the failure (which rules failed; for an unparsable answer which headers were present), never the text.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after the refused live Analyst check: placeholders (the Analyst writes no digits), fewer facts built by code, and the stated/defaulted marks, in one change."
  },
  {
   "value": "The Analyst writes no digits: every number, p-value, set of paper figures, the outcome and the verdict are {name} placeholders of its named facts, and code renders the finished text. Before rendering, code refuses a name that is not among the facts given ('unknown_name'), any digit outside a placeholder ('digit_outside_placeholder'), and a text that does not use {outcome_wording} (and {verdict_wording} when there is a verdict). On the finished text: no forbidden phrase ('do not exist', 'proves', ...), never 'confirms the claim' or 'confirms the hypothesis' and no causal language ('causes', 'caused by', 'causal') even with a verdict, no verdict where there is none, the words 'p-value' and the paper figures only inside their ready-made phrases, the effective number never called 'independent', and every number one of the facts' (a safeguard). Each failure is corrected once, naming only the code; failing twice the text is discarded and the run shows 'explanation unavailable'; the stage keeps counts or rule names, never text. The finished text and its template are stored.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after the first of three live checks was refused by the two word-based rules: those rules removed (with placeholders a p-value and the paper figures exist only inside their phrase names, which no other name exposes, tested); with a verdict, the pooled p-value and paper-figures phrases are required placeholders, refused with 'result_phrases_missing'."
  },
  {
   "value": "The Analyst writes no digits: every number, p-value, set of paper figures, the outcome and the verdict are {name} placeholders of its named facts, and code renders the finished text. Before rendering, code refuses a name that is not among the facts given ('unknown_name'), any digit outside a placeholder ('digit_outside_placeholder'), a text that does not use {outcome_wording} (and {verdict_wording} when there is a verdict), and, when there is a verdict, a text that does not use {pooled_p_phrase} and {pooled_figures_phrase} ('result_phrases_missing'). A p-value and the paper figures exist only inside their phrase names: no other name exposes them (tested). On the finished text: no forbidden phrase ('do not exist', 'proves', ...), never 'confirms the claim' or 'confirms the hypothesis' and no causal language ('causes', 'caused by', 'causal') even with a verdict, no verdict where there is none, the effective number never called 'independent', and every number one of the facts' (a safeguard). Each failure is corrected once, naming only the code; failing twice the text is discarded and the run shows 'explanation unavailable'; the stage keeps counts or rule names, never text. The finished text and its template are stored.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after reading the first accepted live explanation: code-built sentences so the Analyst need not interpret; units; one form for rates and the threshold; interval phrases; plain names and labels; 'groups' throughout."
  }
 ]
}
```
### New: `run_order_and_failures`

```json
{
 "key": "run_order_and_failures",
 "name": "The run order and what a failure does to a run",
 "state": "in_force",
 "statement": "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or the rules lock, records, Checks, Critic, Inclusion, dataset freeze, statistics, Analyst and the copy of code's decision. A fixed-plan run bypasses the Planner (criterion 14.1a, or a narrower question's stored plan). A Planner failure, a domain mismatch, a claim that is not one plan, a refused checkpoint or write, changed source versions for a narrower question, and a spending refusal at the Planner or the Critic fail the run with a stated reason. A Critic failure leaves flags unclassified and the run goes on. Any Analyst failure, a spending refusal included, leaves code's decision standing: the run completes with 'explanation unavailable' (a departure from PRD 14.4's 'marked failed' for a cap reached at the Analyst, by the owner's decision). A call whose recording failed stays open, so the run stays running until step 9's recovery. No model call runs inside a database transaction.",
 "value": {
  "text": "the step 8b run order and failure table",
  "unit": null
 },
 "category": "operational",
 "affects": "Every run's stages and endings (PRD 3, 8, 14.4).",
 "reason": "The step 8 plan's run order, corrected by the owner (A1); the failure table approved with the plan.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answers A1, A3, A11, B1, B2."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.orchestrator:run"
   },
   {
    "ref": "python:hypocurate.pipeline.orchestrator:REASONS"
   }
  ],
  "note": null
 },
 "notes": [],
 "tests": [
  "tests/test_orchestrator.py::test_14_1a_the_fixed_plan_run_reproduces_the_reference_and_repeats_identically",
  "tests/test_orchestrator.py::test_14_1b_the_planners_plan_is_locked_and_the_run_completes",
  "tests/test_orchestrator.py::test_a3_a_spending_refusal_at_the_analyst_leaves_codes_decision_standing",
  "tests/test_orchestrator.py::test_a_spending_refusal_at_the_planner_fails_the_run",
  "tests/test_orchestrator.py::test_a_spending_refusal_at_the_critic_fails_the_run",
  "tests/test_orchestrator.py::test_a_critic_failure_leaves_flags_unclassified_and_the_run_goes_on",
  "tests/test_orchestrator.py::test_no_model_call_is_made_while_a_database_transaction_is_open"
 ],
 "history": []
}
```
### New: `nothing_found_kinds`

```json
{
 "key": "nothing_found_kinds",
 "name": "The kind of 'nothing found' is decided by code",
 "state": "in_force",
 "statement": "Code classifies, in the gap facts, each chosen source and the run: 'failed_search' when the search failed; 'missing_evidence' when the source was searched but none of its records entered the primary set; none when records entered it. The run is 'failed_search' only when every chosen source failed, otherwise 'missing_evidence' when no source contributed. Code never sets 'reported_negative' in sprint 1 (no source states a negative result).",
 "value": {
  "text": "failed search / missing evidence; never reported negative",
  "unit": null
 },
 "category": "data_handling",
 "affects": "The gap report (PRD 3.1, 14.3).",
 "reason": "A source's search result is final once it is searched, before eligibility is decided, so 'missing evidence' in 14.3's sense is classified later from stored facts.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.analysis:nothing_found_kind"
   },
   {
    "ref": "python:hypocurate.pipeline.analysis:run_nothing_found_kind"
   }
  ],
  "note": null
 },
 "notes": [],
 "tests": [
  "tests/test_analysis_stage.py::test_each_source_gets_its_kind_of_nothing_found_from_code",
  "tests/test_analysis_stage.py::test_the_runs_kind_of_nothing_found",
  "tests/test_orchestrator.py::test_14_3_the_bcc_claim_ends_insufficient_as_missing_evidence_with_no_verdict",
  "tests/test_cli_runs.py::test_14_3_a_source_that_cannot_be_read_is_a_failed_search_not_missing_evidence"
 ],
 "history": []
}
```
### New: `no_live_calls_in_suite`

```json
{
 "key": "no_live_calls_in_suite",
 "name": "The regression suite makes no live model call",
 "state": "in_force",
 "statement": "The test process and every guarded child it starts have no provider credential, and the provider's address is a closed local port, so a request that does not name the local stub cannot leave the machine; agent tests answer through the stub, which records the raw request bytes. Live tests are separate, marked, and run only with the owner's go.",
 "value": {
  "text": "no credential; provider address 127.0.0.1:9",
  "unit": null
 },
 "category": "operational",
 "affects": "Cost and reproducibility of the suite (PRD 13.1).",
 "reason": "Owner's standing requirement for step 8b.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.lm:FAILURES"
   }
  ],
  "note": null
 },
 "notes": [],
 "tests": [
  "tests/test_no_live_calls.py::test_the_test_process_has_no_provider_credential_and_a_closed_local_address",
  "tests/test_no_live_calls.py::test_an_agent_call_without_the_stub_never_reaches_a_provider"
 ],
 "history": []
}
```
### New: `display_precision`

```json
{
 "key": "display_precision",
 "name": "How numbers are shown",
 "state": "in_force",
 "statement": "Numbers shown to the Analyst (and, from step 10, to people) are rounded by code in one place: k, its standard error and t to 0.1; a p-value to two significant figures (scientific notation below 0.001, e.g. 1.3e-6); counts exact; the effective number of papers to two decimals; the largest share and every other share or rate (calibration, detection, power and their intervals) as a percentage to one decimal; temperatures, scatter and shift to at most one decimal; the threshold as given; any other number to three significant figures. A p-value is shown as 'p ≈ <value> (approximate, nominal, one-sided)'; the paper figures as '<n> informative papers, an effective number of papers of <e>, a largest share of <s> and <df> degrees of freedom'. Owner's additions (2026-10-07): estimates and standard errors of the coefficient carry the unit MPa·µm^0.5, scatter and shift MPa, temperatures °C; the nominal level is shown as a percentage beside the shares (5.0%), replacing the threshold shown as given; each simulation interval is shown as '<low> to <high>, a 95% simulation interval covering simulation uncertainty only'; the paper figures read 'informative groups' and 'an effective number of groups'.",
 "value": {
  "text": "0.1 for k and SE; 2 significant figures for p; percentages to 0.1",
  "unit": null
 },
 "category": "operational",
 "affects": "Every number the Analyst can quote.",
 "reason": "Owner, 2026-10-07: the Analyst never rounds; code does.",
 "evidence": [
  "Register 'reference_test_tolerance' and 'reference_numbers' (k, SE, p; the approved sensitivity numbers' effective number and share). Owner's decision after the live diagnostic call, 2026-10-07."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.display:RULES"
   },
   {
    "ref": "python:hypocurate.pipeline.display:P_DESCRIPTION",
    "equals": "approximate, nominal, one-sided"
   },
   {
    "ref": "python:hypocurate.pipeline.display:COEFFICIENT_UNIT",
    "equals": "MPa·µm^0.5"
   },
   {
    "ref": "python:hypocurate.pipeline.display:INTERVAL_NOTE",
    "equals": "a 95% simulation interval covering simulation uncertainty only"
   }
  ],
  "note": null
 },
 "notes": [
  "All the precisions, including those drafted by Claude Code where the register was silent (other shares and rates, temperatures, scatter, shift, the fallback), were approved by the owner on 2026-10-07."
 ],
 "tests": [
  "tests/test_analyst.py::test_the_facts_carry_display_strings_and_phrases",
  "tests/test_access_step8b.py::test_above_the_minimums_the_analysts_facts_carry_the_stored_estimate",
  "tests/test_analyst.py::test_the_facts_carry_the_code_built_sentences_units_and_the_nominal_level"
 ],
 "history": [
  {
   "value": "Numbers shown to the Analyst (and, from step 10, to people) are rounded by code in one place: k, its standard error and t to 0.1; a p-value to two significant figures (scientific notation below 0.001, e.g. 1.3e-6); counts exact; the effective number of papers to two decimals; the largest share and every other share or rate (calibration, detection, power and their intervals) as a percentage to one decimal; temperatures, scatter and shift to at most one decimal; the threshold as given; any other number to three significant figures. A p-value is shown as 'p ≈ <value> (approximate, nominal, one-sided)'; the paper figures as '<n> informative papers, an effective number of papers of <e>, a largest share of <s> and <df> degrees of freedom'.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after reading the first accepted live explanation: code-built sentences so the Analyst need not interpret; units; one form for rates and the threshold; interval phrases; plain names and labels; 'groups' throughout."
  }
 ]
}
```
### Changed: `access_allow_lists` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "access_allow_lists",
 "name": "Allowed fields per role and stage",
 "state": "in_force",
 "statement": "Each agent role receives exactly the fields listed for it at the run's stage, and nothing else: the Planner before the rules lock; the Critic between the lock and the freeze; the Analyst after the freeze, after a run ended without a freeze, and at 'narrowed' (a running run with no plan and code's narrowing decision of partly sufficient, where no plan can be locked), each time the same five fields: the claim, the domain, the source facts, the coverage and the Analyst's facts (code's stored results by named keys only; at 'narrowed', the narrowing facts only; below the minimums, nothing computed from outcome values). The Commentator receives nothing at any stage until step 12, when its lists are decided and reviewed (its earlier lists are in this entry's history). The Curator receives nothing at any run stage: it reads one sealed source version when that version is registered (stage 'registration', no run), and then only that version's documentation and the fields it may propose values for (step 8a). Queued and failed runs give nothing. Every field reads only the run's own rows (single-run scope), or for the Curator only its invocation's source version. Every read and every refusal is logged.",
 "value": {
  "text": "the table in hypocurate/access/allowlist.py (ALLOWED)",
  "unit": null
 },
 "category": "data_handling",
 "affects": "Everything an agent can receive (PRD 4), from step 8 on.",
 "reason": "PRD 4 lists what each role can see in general terms; the fields the PRD does not assign (the plan for the Critic, tag lists, coverage, handovers, cost, eligibility decisions, the domain for the Curator) were assigned in the step 5 plan.",
 "evidence": [
  "PRD 4; step 5 plan approved by the owner, 2026-10-05, with additions A (single-run scope) and B (named source fields).",
  "Owner's change before the step 5 review, 2026-10-05: the Commentator on a run with no dataset frozen."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.allowlist:ALLOWED"
   },
   {
    "ref": "python:hypocurate.access.allowlist:ROLES",
    "equals": [
     "planner",
     "curator",
     "critic",
     "analyst",
     "commentator"
    ]
   },
   {
    "ref": "python:hypocurate.access.allowlist:STAGES",
    "equals": [
     "none",
     "before_lock",
     "curation",
     "analysis",
     "closed_without_freeze",
     "final",
     "final_without_freeze",
     "registration",
     "narrowed"
    ]
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "On a completed run, the Commentator received the Analyst's post-freeze fields (including every stored record with its outcome values) whether or not a dataset was frozen, plus the gap-report summaries.",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Step 5 first build; changed by the owner before the review."
  },
  {
   "value": "Each agent role receives exactly the fields listed for it at the run's stage, and nothing else: the Planner before the rules lock; the Curator and the Critic between the lock and the freeze; the Analyst after the freeze, or after a run ended without a freeze (gap report); the Commentator after completion. On a run completed with no dataset frozen, the Commentator receives only what the Analyst received for the gap report, plus the Analyst's gap report and the run's outcome: no outcome values and no row-level records. Queued and failed runs give nothing. Every field reads only the run's own rows (single-run scope). Every read and every refusal is logged.",
   "from": "2026-10-05",
   "to": "2026-10-06",
   "note": "Step 8a (owner, 2026-10-06, Q2): the Curator moved from the curation stage (its own source's data files and the fields to extract) to registration."
  },
  {
   "value": "Each agent role receives exactly the fields listed for it at the run's stage, and nothing else: the Planner before the rules lock; the Critic between the lock and the freeze; the Analyst after the freeze, or after a run ended without a freeze (gap report); the Commentator after completion. The Curator receives nothing at any run stage: it reads one sealed source version when that version is registered (stage 'registration', no run), and then only that version's documentation and the fields it may propose values for (step 8a). On a run completed with no dataset frozen, the Commentator receives only what the Analyst received for the gap report, plus the Analyst's gap report and the run's outcome: no outcome values and no row-level records. Queued and failed runs give nothing. Every field reads only the run's own rows (single-run scope), or for the Curator only its invocation's source version. Every read and every refusal is logged.",
   "from": "2026-10-06",
   "to": "2026-10-07",
   "note": "Step 8b (owner, 2026-10-07): the Analyst's lists (Q6), the stage 'narrowed' (A4) and the Commentator's empty lists (A6). Starting point for step 12, the Commentator's lists before this change: at 'final', claim, domain, sources_meta, plan, records_full, decisions, flags_full, results, coverage, stage_outputs, run_cost; at 'final_without_freeze', claim, domain, sources_meta, plan, coverage, stored_record_counts, decisions, flags_kind, condition_summaries, gap_report, outcome. The Analyst's lists before this change: at 'analysis', the first of these; at 'closed_without_freeze', the second without gap_report and outcome."
  }
 ],
 "notes": [
  "Two fields are reference lists, not run data: the confirmed domain and the approved tag values (without the run that proposed them)."
 ],
 "tests": [
  "tests/test_access_layer.py::test_the_allow_list_matches_the_owners_table",
  "tests/test_access_layer.py::test_each_role_gets_exactly_its_fields_and_every_refusal_is_logged",
  "tests/test_access_projected.py::test_nothing_from_another_run_reaches_any_role",
  "tests/test_access_layer.py::test_a_commentator_binding_reads_nothing_at_any_stage",
  "tests/test_access_projected.py::test_the_commentator_receives_no_input_without_a_freeze",
  "tests/test_access_layer.py::test_the_curator_has_nothing_in_any_run",
  "tests/test_access_step8b.py::test_at_narrowed_only_the_analyst_reads",
  "tests/test_access_projected.py::test_no_projected_planted_value_in_the_analysts_input_at_narrowed",
  "tests/test_access_projected.py::test_the_analysts_facts_carry_the_stored_results_by_named_keys_only",
  "tests/test_access_step8b.py::test_below_the_minimums_the_analysts_facts_hold_nothing_computed_from_outcomes",
  "tests/test_access_step8b.py::test_no_plan_is_locked_at_narrowed_by_code_or_by_the_database"
 ]
}
```
### Changed: `access_stage_from_database` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "access_stage_from_database",
 "name": "A role's stage is the run's, read from the database",
 "state": "in_force",
 "statement": "Every access call reads the run's stage from the database inside its own transaction, after locking the run, and refuses when the role's declared stage differs. An access object built for one stage stops working when the run passes a checkpoint. A completed run is at stage 'final' if a dataset was frozen, otherwise at 'final_without_freeze'.",
 "value": {
  "text": "read on every call",
  "unit": null
 },
 "category": "operational",
 "affects": "When each role's access opens and closes (rules lock, freeze, end without freeze, completion).",
 "reason": "A stage taken from the caller could be wrong or stale.",
 "evidence": [
  "Step 5 plan (approved by the owner, 2026-10-05)."
 ],
 "decided": {
  "by": "step 5 (owner's approval of the plan)",
  "date": "2026-10-05"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.stage:actual_stage"
   }
  ],
  "note": null
 },
 "history": [],
 "notes": [],
 "tests": [
  "tests/test_access_layer.py::test_a_declared_stage_is_checked_against_the_database",
  "tests/test_access_layer.py::test_the_rules_lock_changes_what_each_role_may_see",
  "tests/test_access_layer.py::test_the_dataset_freeze_changes_what_each_role_may_see",
  "tests/test_access_layer.py::test_completion_without_a_freeze_closes_the_analyst_and_gives_the_commentator_nothing",
  "tests/test_access_layer.py::test_completion_after_a_freeze_closes_the_analyst_and_gives_the_commentator_nothing"
 ]
}
```
### Changed: `pipeline_file_guard` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "pipeline_file_guard",
 "name": "Approved input files of pipeline code",
 "state": "in_force",
 "statement": "A tripwire against accidental file access by trusted pipeline code, not a sandbox. Each pipeline run executes in a fresh process (python -m hypocurate.access.guarded) where a Python audit hook refuses reading or listing anything outside the Python installation and the package's code, writing outside a private scratch directory, relative paths, other programs and new native libraries; each refusal is logged (audit log as a failure, or the process log). It does not stop code that tries to get around it: Python warns that audit hooks are unsuitable for a sandbox, and open descriptors, the guard's own state, preloaded ctypes (direct memory access), sockets and the database are not restricted. The only construction-level guarantee is that the deployed image contains no tests/ or docs/. The modules imported before the guard is installed are psycopg and scipy (each makes a ctypes call when first imported); after installation every ctypes event is still refused.",
 "value": {
  "text": "tripwire: reads limited to the Python installation and package code; writes to a private scratch directory",
  "unit": null
 },
 "category": "operational",
 "affects": "Every pipeline run (the command line's run command, step 8; the worker, step 9).",
 "reason": "Answer material and review documents should not be reached by accident (step 1 open item 4). The owner's first instruction asked for 'unreachable by construction'; after the step 5 review the owner scoped this to a tripwire against our own mistakes, with the deployed image (no tests/, no docs/) as the only construction-level guarantee.",
 "evidence": [
  "Step 1 summary, open item 4; step 5 plan and owner's addition C, 2026-10-05.",
  "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.file_guard:GUARDED_MAIN",
    "equals": "hypocurate.access.guarded"
   },
   {
    "ref": "python:hypocurate.access.file_guard:SCRATCH_PREFIX",
    "equals": "hc-run-"
   },
   {
    "ref": "python:hypocurate.access.guarded:PRELOADED",
    "equals": [
     "psycopg",
     "scipy"
    ]
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "A pipeline run executes in a fresh process (python -m hypocurate.access.guarded) under an irreversible guard: it may read only the Python installation and the package's code, and write only in a private scratch directory (an empty, 0700 hc-run-* directory in the system temporary directory, removed afterwards). tests/, docs/, data/ and the repository root cannot be read or listed; other programs and native code through ctypes are refused. Source data reach pipeline code only as the sealed bytes of the run's source versions, through the access layer. The database driver is imported before the guard is installed.",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Step 5 first build; changed after the second-model review."
  },
  {
   "value": "A tripwire against accidental file access by trusted pipeline code, not a sandbox. Each pipeline run executes in a fresh process (python -m hypocurate.access.guarded) where a Python audit hook refuses reading or listing anything outside the Python installation and the package's code, writing outside a private scratch directory, relative paths, other programs and new native libraries; each refusal is logged (audit log as a failure, or the process log). It does not stop code that tries to get around it: Python warns that audit hooks are unsuitable for a sandbox, and open descriptors, the guard's own state, preloaded ctypes (direct memory access), sockets and the database are not restricted. The only construction-level guarantee is that the deployed image contains no tests/ or docs/.",
   "from": "2026-10-05",
   "to": "2026-10-07",
   "note": "Step 8b (owner, 2026-10-07): scipy preloaded with psycopg (importing it makes a ctypes foreign call at load time, which the guard refuses; the run's statistics import scipy.stats). Checked in the runtime image: refused without it, no refusal with it. No production module imports statsmodels (test-only) or pandas (in the runtime lock only as a dependency of dspy)."
  }
 ],
 "notes": [
  "Python documentation, sys.addaudithook and PEP 578: audit hooks are not suitable for implementing a sandbox.",
  "Sufficient under the threat model (entry 'threat_model'): only trusted code runs; agents return text only.",
  "A library that imports ctypes after the guard is installed is refused; such a library (for example the plotting library, step 7) must be added to PRELOADED with the owner's approval.",
  "Step 8a (owner, 2026-10-06): the guarded process drops import-path entries that do not exist before installing the guard, so importing the agent libraries logs no refusal; a planted .env read by a library is still refused (entry 'model_call_libraries')."
 ],
 "tests": [
  "tests/test_access_files.py::test_answers_reviews_data_and_the_repository_root_cannot_be_read",
  "tests/test_access_files.py::test_writes_outside_the_scratch_directory_are_refused",
  "tests/test_access_files.py::test_templates_database_and_certificates_work_under_the_guard",
  "tests/test_access_files.py::test_source_registration_cannot_run_under_the_guard",
  "tests/test_access_files.py::test_the_guarded_process_refuses_a_scratch_directory_that_would_open_anything_else",
  "tests/test_access_layer.py::test_the_guard_is_installed_in_one_place",
  "tests/test_access_files.py::test_preloaded_ctypes_still_works_a_documented_limit",
  "tests/test_access_dispatch.py::test_file_guard_refusals_are_logged_for_the_run_or_in_the_process_log",
  "tests/test_check_runtime_image.py::test_clean_image_passes",
  "tests/test_access_dispatch.py::test_a_refusal_followed_by_a_timeout_is_still_logged",
  "tests/test_agent_libraries.py::test_a_planted_env_file_read_by_a_library_is_still_refused_under_the_guard",
  "tests/test_agent_libraries.py::test_missing_path_entries_are_dropped_and_the_others_kept",
  "tests/test_agent_libraries.py::test_the_statistics_libraries_import_under_the_guard_with_no_refusal",
  "tests/test_agent_libraries.py::test_after_the_statistics_libraries_a_ctypes_call_and_a_planted_env_read_are_still_refused"
 ]
}
```
### Changed: `accepted_disclosures` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "accepted_disclosures",
 "name": "What the blinded views disclose by design",
 "state": "in_force",
 "statement": "The blinding of the Planner, the Critic and the Analyst's facts without a freeze is limited to: no outcome value is copied into their views from a stored outcome field, a value as reported, a flag's numbers, a stage's text, or text outside a vocabulary. They still disclose, by design: counts by field status; flag kinds and categories; compositions and alloy labels; DOIs with DOI syntax (which may contain digits); text written or approved by people (the claim, approved tag values, source names and licences in code); numbers in the locked plan; timing and the existence of refusals. Timing is not protected.",
 "value": {
  "text": "the seven disclosures in ACCEPTED_DISCLOSURES",
  "unit": null
 },
 "category": "data_handling",
 "affects": "The claim made for blinding (PRD 4) in every document.",
 "reason": "Review finding 3 and its note on counts and timing: these follow from the approved contract; 'no row-level value can be inferred' would be false.",
 "evidence": [
  "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.allowlist:ACCEPTED_DISCLOSURES"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "The blinding of the Planner, the Critic, the gap report and the Commentator without a freeze is limited to: no outcome value is copied into their views from a stored outcome field, a value as reported, a flag's numbers, a stage's text, or text outside a vocabulary. They still disclose, by design: counts by field status; flag kinds and categories; condition summaries, which reveal an exact grain size or temperature when a group has one record; compositions and alloy labels; DOIs with DOI syntax (which may contain digits); text written or approved by people (the claim, approved tag values, source names and licences in code); numbers in the locked plan; the Analyst's gap report passed to the Commentator; timing and the existence of refusals. Timing is not protected.",
   "from": "2026-10-05",
   "to": "2026-10-07",
   "note": "Step 8b (owner, 2026-10-07): the item 'the Analyst's gap report passed to the Commentator' removed, since the Commentator reads nothing until step 12 (A6); step 12 decides it with the Commentator's lists."
  },
  {
   "value": "The blinding of the Planner, the Critic and the Analyst's facts without a freeze is limited to: no outcome value is copied into their views from a stored outcome field, a value as reported, a flag's numbers, a stage's text, or text outside a vocabulary. They still disclose, by design: counts by field status; flag kinds and categories; condition summaries, which reveal an exact grain size or temperature when a group has one record; compositions and alloy labels; DOIs with DOI syntax (which may contain digits); text written or approved by people (the claim, approved tag values, source names and licences in code); numbers in the locked plan; timing and the existence of refusals. Timing is not protected.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b (owner, 2026-10-07): the item on condition summaries removed, since no agent reads that field now (the Analyst receives stored facts only; the Commentator nothing until step 12); step 12 decides it with the Commentator's lists."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_access_projected.py::test_no_projected_planted_value_in_the_critics_complete_input",
  "tests/test_access_dispatch.py::test_a_doi_with_doi_syntax_passes_even_with_digits_an_accepted_disclosure"
 ]
}
```
### Changed: `code_role_access` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "code_role_access",
 "name": "Inclusion and Checks read through access objects",
 "state": "in_force",
 "statement": "Inclusion and Checks are code and read through their own access objects, bound by the trusted dispatcher at the curation stage only, every bind and read logged. Checks sees every value. Inclusion receives no outcome value, so no eligibility decision can depend on a record's outcome directly or on its position relative to the tested relationship. Not claimed: that outcomes play no part at all, since Checks compares values (pairwise comparisons that feed a whole-group classification) to classify duplicates, conflicts and physically invalid records, and Inclusion acts on those flag kinds. Step 7 (owner, 2026-10-05; a safeguard change): Statistics binds only at the analysis stage and receives exactly the locked plan and the frozen data (the frozen sets and, for their records only, what the model needs, outcome included); the gap facts bind at the analysis stage and when a run closed without a freeze, and receive no outcome value. Step 8b (owner, 2026-10-07; a safeguard change): the narrowing decision binds only before the rules lock and receives only counts of structure per chosen source, read from its sealed version (records per combination of phase class, test type, temperature band and reported temperature, with field statuses and whether a grain size is present): no outcome value and no composition.",
 "value": {
  "text": "Inclusion: plan, record conditions, flag kinds; Checks: plan, all values",
  "unit": null
 },
 "category": "data_handling",
 "affects": "Eligibility decisions and flags.",
 "reason": "PRD 4 lists Inclusion and Checks; their reads are logged like the agents'. Blinding Inclusion keeps outcomes out of eligibility by construction of its input.",
 "evidence": [
  "Step 6 planning (owner, 2026-10-05); docs/reviews/step06_summary.md."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.allowlist:CODE_ALLOWED"
   },
   {
    "ref": "python:hypocurate.access.dispatch:bind_code"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "Inclusion and Checks are code and read through their own access objects, bound by the trusted dispatcher at the curation stage only, every bind and read logged. Checks sees every value. Inclusion receives no outcome value, so no eligibility decision can depend on a record's outcome directly or on its position relative to the tested relationship. Not claimed: that outcomes play no part at all, since Checks compares values (pairwise comparisons that feed a whole-group classification) to classify duplicates, conflicts and physically invalid records, and Inclusion acts on those flag kinds.",
   "from": "2026-10-05",
   "to": "2026-10-05",
   "note": "Step 7 (owner, 2026-10-05)."
  },
  {
   "value": "Inclusion and Checks are code and read through their own access objects, bound by the trusted dispatcher at the curation stage only, every bind and read logged. Checks sees every value. Inclusion receives no outcome value, so no eligibility decision can depend on a record's outcome directly or on its position relative to the tested relationship. Not claimed: that outcomes play no part at all, since Checks compares values (pairwise comparisons that feed a whole-group classification) to classify duplicates, conflicts and physically invalid records, and Inclusion acts on those flag kinds. Step 7 (owner, 2026-10-05; a safeguard change): Statistics binds only at the analysis stage and receives exactly the locked plan and the frozen data (the frozen sets and, for their records only, what the model needs, outcome included); the gap facts bind at the analysis stage and when a run closed without a freeze, and receive no outcome value.",
   "from": "2026-10-05",
   "to": "2026-10-07",
   "note": "Step 8b (owner, 2026-10-07, Q5): the code role 'narrowing' added."
  }
 ],
 "notes": [
  "Step 6 review, finding 2 (2026-10-06): Inclusion's list gains 'set_flags' (each sensitivity set's matching flags from the completed Checks result: codes and record ids, no numbers)."
 ],
 "tests": [
  "tests/test_access_code_roles.py::test_an_agent_setting_cannot_bind_as_a_code_role",
  "tests/test_access_code_roles.py::test_code_roles_do_not_bind_at_any_other_stage",
  "tests/test_access_code_roles.py::test_inclusion_receives_no_outcome_value",
  "tests/test_access_code_roles.py::test_only_code_roles_bind_without_an_agent_setting",
  "tests/test_access_code_roles.py::test_the_code_lists_match_the_owners_decision",
  "tests/test_access_statistics.py::test_records_outside_the_frozen_sets_never_reach_statistics",
  "tests/test_access_statistics.py::test_the_complete_input_of_statistics",
  "tests/test_access_statistics.py::test_the_gap_facts_receive_no_outcome_value",
  "tests/test_access_statistics.py::test_the_lists_are_the_owners_decision",
  "tests/test_flags.py::test_flags_come_from_pairwise_comparisons_and_group_classification",
  "tests/test_access_step8b.py::test_candidate_counts_are_counts_of_structure_only",
  "tests/test_access_step8b.py::test_the_narrowing_role_binds_only_before_the_lock"
 ]
}
```
### Changed: `evidence_level_scale` (the entry as it now stands; earlier wording in its history)

```json
{
 "sensitivity": null,
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "history": [
  {
   "value": "Every run's statistics result stores an evidence level from 1 to 6, derived by one tested function from the result state, never by an agent: 6 sufficient with a verdict; 5 use what is available with a minimum missed (exploratory); 4 inference invalid, coefficient only; 3 below the minimums under the fixed option; 2 coefficient cannot be fitted; 1 no dataset frozen. Precedence: no freeze; below the minimums (fixed option); not fitted; coefficient only; exploratory; sufficient. Descriptive only; it never affects the outcome or the verdict. A marked test run keeps its level beside its test label. A partly sufficient original question keeps the level of its own pooled result state.",
   "from": "2026-10-05",
   "to": "2026-10-07",
   "note": "Step 8b (owner's addition 1 of 2026-10-06, built 2026-10-07): the partly-sufficient original is at level 1 with its own wording."
  }
 ],
 "notes": [],
 "key": "evidence_level_scale",
 "name": "Evidence level",
 "state": "in_force",
 "statement": "Every run's statistics result stores an evidence level from 1 to 6, derived by one tested function from the result state, never by an agent: 6 sufficient with a verdict; 5 use what is available with a minimum missed (exploratory); 4 inference invalid, coefficient only; 3 below the minimums under the fixed option; 2 coefficient cannot be fitted; 1 no dataset frozen. Precedence: no freeze; below the minimums (fixed option); not fitted; coefficient only; exploratory; sufficient. Descriptive only; it never affects the outcome or the verdict. A marked test run keeps its level beside its test label. A partly sufficient original question, never tested, is at level 1, shown as 'original question not tested; a narrower question was proposed'.",
 "value": {
  "text": "1 to 6",
  "unit": null
 },
 "category": "statistical",
 "affects": "What is stored and shown with a run; filtering runs by level.",
 "reason": "A single descriptive scale of how far a run got, computed by code.",
 "evidence": [
  "Owner, step 7 (2026-10-05)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.statistics:EVIDENCE_LEVELS"
   },
   {
    "ref": "python:hypocurate.pipeline.statistics:evidence_level"
   },
   {
    "ref": "sql:ck_run_evidence_level"
   },
   {
    "ref": "sql:ck_run_evidence_level_iff_completed"
   },
   {
    "ref": "python:hypocurate.pipeline.statistics:PARTLY_SUFFICIENT_WORDING",
    "equals": "original question not tested; a narrower question was proposed"
   }
  ],
  "note": "Copied onto the run by the copy path; required on every completed run and only on one, and checked against the outcome, verdict and exploratory label by the database (review, smaller point, 2026-10-06)."
 },
 "tests": [
  "tests/test_analysis_stage.py::test_a_marked_run_carries_the_label_on_every_stored_result_and_stays_out_of_aggregates",
  "tests/test_analysis_stage.py::test_the_evidence_level_must_agree_with_the_outcome",
  "tests/test_completion.py::test_a_completed_run_needs_its_evidence_level",
  "tests/test_statistics.py::test_every_result_state_has_its_evidence_level",
  "tests/test_statistics.py::test_the_evidence_scale_is_the_owners",
  "tests/test_statistics.py::test_the_level_never_feeds_back_into_the_outcome_or_verdict",
  "tests/test_planner_narrowing.py::test_a_part_with_none_and_the_exact_narrower_scope_is_partly_sufficient",
  "tests/test_cli_runs.py::test_14_3_partly_sufficient_and_the_narrower_question_from_the_command_line"
 ]
}
```
### Changed: `copy_decision_only_copies` (the entry as it now stands; earlier wording in its history)

```json
{
 "sensitivity": null,
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "history": [
  {
   "value": "The analysis stage stores the run's decision (outcome, verdict, exploratory label, evidence level) with the freeze fingerprint it belongs to; it does not complete the run. A separate function copies the stored decision onto the run, unchanged, and completes it; it refuses, and logs the refusal, when the decision is missing or belongs to a different freeze. 'Partly sufficient' is not set by it (a step 8 decision).",
   "from": "2026-10-05",
   "to": "2026-10-07",
   "note": "Step 8b: how partly sufficient reaches the run."
  }
 ],
 "notes": [],
 "key": "copy_decision_only_copies",
 "name": "The decision is copied, not recomputed",
 "state": "in_force",
 "statement": "The analysis stage stores the run's decision (outcome, verdict, exploratory label, evidence level) with the freeze fingerprint it belongs to; it does not complete the run. A separate function copies the stored decision onto the run, unchanged, and completes it; it refuses, and logs the refusal, when the decision is missing or belongs to a different freeze. 'Partly sufficient' is copied by its own function from code's stored narrowing decision, after checking the source versions the counts were taken on (step 8b).",
 "value": {
  "text": "store, then copy unchanged",
  "unit": null
 },
 "category": "operational",
 "affects": "How a run's outcome reaches the run row (orchestration in steps 8 and 9).",
 "reason": "The Analyst runs after the statistics, and 'partly sufficient' needs the Planner's narrower question.",
 "evidence": [
  "Owner, step 7 planning decision 6 and addition 11 (2026-10-05)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.completion:copy_decision"
   },
   {
    "ref": "python:hypocurate.pipeline.completion:copy_partly_sufficient"
   }
  ],
  "note": null
 },
 "tests": [
  "tests/test_completion.py::test_the_decision_is_copied_unchanged",
  "tests/test_completion.py::test_it_refuses_a_missing_decision_and_logs_it",
  "tests/test_completion.py::test_it_refuses_a_decision_of_another_freeze_and_logs_it",
  "tests/test_completion.py::test_it_copies_what_is_stored_and_never_recomputes",
  "tests/test_completion.py::test_the_database_checks_the_copy_again",
  "tests/test_planner_narrowing.py::test_the_copy_refuses_a_run_that_is_not_narrowed",
  "tests/test_planner_narrowing.py::test_the_copy_refuses_a_decision_taken_on_other_source_versions"
 ]
}
```
### Changed: `agent_models` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "agent_models",
 "name": "The model of each agent role",
 "state": "in_force",
 "statement": "Planner Claude Opus 5.5, Curator Claude Sonnet 5.5, Critic Claude Haiku 4.5, Analyst Claude Opus 5.5, each with its effort and limits set explicitly in its settings version (agent_setting, append-only). The Curator: at most 8000 output tokens (thinking included), at most 20000 characters of answer, effort medium. The Planner and the Analyst: at most 8000 output tokens, 6000 characters, effort medium. The Critic: at most 8000 output tokens, 30000 characters, at most 100 flags per call, effort low.",
 "value": {
  "text": "Opus 5.5 / Sonnet 5.5 / Haiku 4.5 / Opus 5.5",
  "unit": null
 },
 "category": "operational",
 "affects": "Every model call's model, cost bound and quality.",
 "reason": "PRD 17, decision 2: a capable model for the Planner and the Analyst, a cheaper one for the Curator and the Critic.",
 "evidence": [
  "Owner, step 8a plan, Q7 (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.settings:MODELS",
    "equals": {
     "planner": "claude-opus-5-5",
     "curator": "claude-sonnet-5-5",
     "critic": "claude-haiku-4-5",
     "analyst": "claude-opus-5-5"
    }
   },
   {
    "ref": "python:hypocurate.pipeline.agents.settings:SETTINGS.curator.limits",
    "equals": {
     "max_tokens": 8000,
     "max_output_chars": 20000
    }
   },
   {
    "ref": "python:hypocurate.pipeline.agents.settings:SETTINGS.planner.limits",
    "equals": {
     "max_tokens": 8000,
     "max_output_chars": 6000
    }
   },
   {
    "ref": "python:hypocurate.pipeline.agents.settings:SETTINGS.critic.limits",
    "equals": {
     "max_tokens": 8000,
     "max_output_chars": 30000,
     "max_flags_per_call": 100
    }
   },
   {
    "ref": "python:hypocurate.pipeline.agents.settings:SETTINGS.analyst.limits",
    "equals": {
     "max_tokens": 8000,
     "max_output_chars": 6000
    }
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "Planner Claude Opus 5.5, Curator Claude Sonnet 5.5, Critic Claude Haiku 4.5, Analyst Claude Opus 5.5, each with its effort and limits set explicitly in its settings version (agent_setting, append-only). The Curator: at most 8000 output tokens (thinking included), at most 20000 characters of answer, effort medium.",
   "from": "2026-10-06",
   "to": "2026-10-07",
   "note": "Step 8b: the Planner's, the Critic's and the Analyst's settings added (drafts for the owner's review, B3)."
  }
 ],
 "notes": [
  "The Planner's, the Critic's and the Analyst's instruction texts and limits are drafts by Claude Code for the owner's review before the live set (B3)."
 ],
 "tests": [
  "tests/test_agent_core.py::test_the_price_table_names_the_owners_models",
  "tests/test_curator.py::test_the_curators_complete_request_is_the_instruction_the_documentation_and_the_targets",
  "tests/test_queries.py::test_dispatch_records_the_settings_version_of_each_run_role"
 ]
}
```
### Changed: `request_failure_policy` (the entry as it now stands; earlier wording in its history)

```json
{
 "key": "request_failure_policy",
 "name": "What happens when an agent request fails",
 "state": "in_force",
 "statement": "Every agent request is reserved, sent once (litellm's retries off) outside any database transaction, and recorded. At most two requests per agent call: an unavailable provider (connection error, timeout, 429, 5xx, or a reply litellm cannot read) is tried once more with the same request; an unusable answer (empty, malformed, a tool call, truncated at the output limit, longer than the role allows) once more with a fixed corrective note naming only the failure code; refused credentials (401, 403), another refused request (4xx), a refusal, a cost the provider did not report, a reservation that cannot be written (nothing is sent), a failed recording on any branch (after a provider failure, a reply without usage or a usable reply) and every spending refusal stop at once. A failed call is recorded with no usage and counts at its maximum cost; a call whose recording fails stays 'started' and counts at its maximum cost. No provider, library or database text is kept with a call or sent in a later request; the process log gets the failure code, the exception's types and where it was raised, never its text. Not covered: what a library logs by itself (litellm's own debug logging is off unless a process turns it on). DSPy's JSON fallback is off. Step 8b: a role's own check of an answer that could be read gives a code that is corrected once the same way: 'invalid_plan' (Planner), 'numbers_unmatched' and 'wording_refused' (Analyst). The Analyst's 'unknown_name' and 'digit_outside_placeholder' are corrected once the same way.",
 "value": {
  "text": "2 requests at most; retry / correct / stop by code",
  "unit": null
 },
 "category": "operational",
 "affects": "Every agent call's cost and outcome.",
 "reason": "The step 8a failure table (owner, 2026-10-06): every failure mode has a defined, tested outcome.",
 "evidence": [
  "Owner, step 8a plan: the request-path failure table (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.interface:MAX_ATTEMPTS",
    "equals": 2
   },
   {
    "ref": "python:hypocurate.pipeline.agents.lm:FAILURES"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "Every agent request is reserved, sent once (litellm's retries off) outside any database transaction, and recorded. At most two requests per agent call: an unavailable provider (connection error, timeout, 429, 5xx, or a reply litellm cannot read) is tried once more with the same request; an unusable answer (empty, malformed, a tool call, truncated at the output limit, longer than the role allows) once more with a fixed corrective note naming only the failure code; refused credentials (401, 403), another refused request (4xx), a refusal, a cost the provider did not report, a failed recording and every spending refusal stop at once. A failed call is recorded with no usage and counts at its maximum cost; a call whose recording fails stays 'started' and counts at its maximum cost. No provider, library or database text is kept with a call or sent in a later request: it goes to the process log only. DSPy's JSON fallback is off.",
   "from": "2026-10-06",
   "to": "2026-10-07",
   "note": "Step 8a as built: a failed recording after a provider failure or a reply without usage escaped unclassified and was retried as malformed (ChatGPT's review of step 8a, finding 4); the process log held the exception's full text. Fixed 2026-10-07."
  },
  {
   "value": "Every agent request is reserved, sent once (litellm's retries off) outside any database transaction, and recorded. At most two requests per agent call: an unavailable provider (connection error, timeout, 429, 5xx, or a reply litellm cannot read) is tried once more with the same request; an unusable answer (empty, malformed, a tool call, truncated at the output limit, longer than the role allows) once more with a fixed corrective note naming only the failure code; refused credentials (401, 403), another refused request (4xx), a refusal, a cost the provider did not report, a reservation that cannot be written (nothing is sent), a failed recording on any branch (after a provider failure, a reply without usage or a usable reply) and every spending refusal stop at once. A failed call is recorded with no usage and counts at its maximum cost; a call whose recording fails stays 'started' and counts at its maximum cost. No provider, library or database text is kept with a call or sent in a later request; the process log gets the failure code, the exception's types and where it was raised, never its text. Not covered: what a library logs by itself (litellm's own debug logging is off unless a process turns it on). DSPy's JSON fallback is off.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b: the roles' check codes added."
  },
  {
   "value": "Every agent request is reserved, sent once (litellm's retries off) outside any database transaction, and recorded. At most two requests per agent call: an unavailable provider (connection error, timeout, 429, 5xx, or a reply litellm cannot read) is tried once more with the same request; an unusable answer (empty, malformed, a tool call, truncated at the output limit, longer than the role allows) once more with a fixed corrective note naming only the failure code; refused credentials (401, 403), another refused request (4xx), a refusal, a cost the provider did not report, a reservation that cannot be written (nothing is sent), a failed recording on any branch (after a provider failure, a reply without usage or a usable reply) and every spending refusal stop at once. A failed call is recorded with no usage and counts at its maximum cost; a call whose recording fails stays 'started' and counts at its maximum cost. No provider, library or database text is kept with a call or sent in a later request; the process log gets the failure code, the exception's types and where it was raised, never its text. Not covered: what a library logs by itself (litellm's own debug logging is off unless a process turns it on). DSPy's JSON fallback is off. Step 8b: a role's own check of an answer that could be read gives a code that is corrected once the same way: 'invalid_plan' (Planner), 'numbers_unmatched' and 'wording_refused' (Analyst).",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after the refused live Analyst check: placeholders (the Analyst writes no digits), fewer facts built by code, and the stated/defaulted marks, in one change."
  }
 ],
 "notes": [
  "litellm cannot read a reply with no usage block and raises a connection error, so such a reply is treated as an unavailable provider (failed, counted at its maximum, tried once more); the code 'cost_unknown' is for a readable reply whose usage is empty."
 ],
 "tests": [
  "tests/test_agent_core.py::test_an_unavailable_provider_is_tried_once_more_with_the_same_request",
  "tests/test_agent_core.py::test_refused_credentials_or_requests_are_not_retried_and_no_provider_text_is_kept",
  "tests/test_agent_core.py::test_an_unusable_answer_is_corrected_once_with_a_fixed_note_and_never_the_answer",
  "tests/test_agent_core.py::test_a_refusal_is_not_retried",
  "tests/test_agent_core.py::test_a_reply_without_usage_is_unreadable_failed_and_counted_at_its_maximum",
  "tests/test_agent_core.py::test_a_readable_reply_with_empty_usage_is_cost_unknown",
  "tests/test_agent_core.py::test_a_reply_whose_recording_fails_is_discarded_and_the_call_stays_open",
  "tests/test_agent_core.py::test_no_database_transaction_is_open_while_a_request_is_in_flight",
  "tests/test_agent_core.py::test_a_recording_failure_on_any_branch_stops_and_keeps_the_maximum",
  "tests/test_agent_core.py::test_a_reservation_that_cannot_be_written_sends_nothing",
  "tests/test_agent_core.py::test_provider_error_text_never_reaches_the_process_log",
  "tests/test_agent_core.py::test_the_request_headers_carry_nothing_of_the_input",
  "tests/test_planner_narrowing.py::test_an_invalid_plan_is_corrected_once_naming_only_the_code_then_the_stage_fails",
  "tests/test_analyst.py::test_a_text_failing_a_check_twice_is_discarded"
 ]
}
```
## 6. Reference comparison with `main`

The five reference runs of `test_reference_numbers.py`, dumped on `main` (`d76c86a`, a separate worktree) and on this head; every decision (with its freeze fingerprint), every analysis (with its calibrations), the not-analysed list and the record counts compared:

```
mpea_fixed   decision      IDENTICAL
mpea_fixed   analyses      IDENTICAL
mpea_fixed   not_analysed  IDENTICAL
mpea_fixed   n_records     IDENTICAL
mpea_use     decision      IDENTICAL
mpea_use     analyses      IDENTICAL
mpea_use     not_analysed  IDENTICAL
mpea_use     n_records     IDENTICAL
reference    decision      IDENTICAL
reference    analyses      IDENTICAL
reference    not_analysed  IDENTICAL
reference    n_records     IDENTICAL
tamu_fixed   decision      IDENTICAL
tamu_fixed   analyses      IDENTICAL
tamu_fixed   not_analysed  IDENTICAL
tamu_fixed   n_records     IDENTICAL
tamu_use     decision      IDENTICAL
tamu_use     analyses      IDENTICAL
tamu_use     not_analysed  IDENTICAL
tamu_use     n_records     IDENTICAL
```

The comparison script:

```python
import json, sys
a = json.load(open(sys.argv[1])); b = json.load(open(sys.argv[2]))
for k in sorted(a):
    for part in ("decision", "analyses", "not_analysed", "n_records"):
        same = json.dumps(a[k][part], sort_keys=True) == json.dumps(b[k][part], sort_keys=True)
        print(f"{k:12} {part:13} {'IDENTICAL' if same else 'DIFFERS'}")
```

The dump test:

```python
"""Scratch (not committed): dumps the reference runs' full statistics output to REFDUMP_OUT."""
import json, os
from test_reference_numbers import runs  # noqa: F401 (the module fixture)


def test_dump(runs):
    out = {}
    for key, r in runs.items():
        records = [{"identity": [rec["stable_identity"] if "stable_identity" in rec else None], **{k: rec[k] for k in sorted(rec) if k not in ("id",)}}
                   for rec in r["data"]["records"]]
        out[key] = {"run": [str(x) for x in r["run"]], "decision": r["out"]["decision"],
                    "analyses": r["out"]["analyses"], "not_analysed": r["out"].get("not_analysed"),
                    "n_records": len(records)}
    with open(os.environ["REFDUMP_OUT"], "w") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=str)
```
## 7. The live calls (`docs/reviews/step08b_live_record.json`)

```json
{
 "note": "Step 8b live calls on the local development database (2026-10-07), exported for the review packet. Every model call with its tokens and cost; each run's outcome and the Analyst's stage. The diagnostic call's raw answer is not included (owner: local scratch file only).",
 "runs": [
  {
   "run": 1,
   "query": "Q-0001",
   "claim": "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
   "status": "completed",
   "outcome": "sufficient",
   "verdict": "supported",
   "evidence_level": 6,
   "fixed_plan": false,
   "failure": null,
   "calls": [
    {
     "role": "planner",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 3304,
     "output_tokens": 344,
     "cost": "0.020096",
     "max_cost": "0.195756"
    },
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 14371,
     "output_tokens": 1478,
     "cost": "0.087044",
     "max_cost": "0.307676"
    },
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 14417,
     "output_tokens": 956,
     "cost": "0.076788",
     "max_cost": "0.308348"
    }
   ],
   "analyst": {
    "status": "failed",
    "attempts": [
     "malformed",
     "wording_refused"
    ],
    "code": "wording_refused",
    "failure_details": null,
    "report": null,
    "template": null
   }
  },
  {
   "run": 2,
   "query": "Q-0002",
   "claim": "Grain refinement still strengthens BCC multi-principal-element alloys at 1000 °C",
   "status": "completed",
   "outcome": "insufficient",
   "verdict": null,
   "evidence_level": 1,
   "fixed_plan": false,
   "failure": null,
   "calls": [
    {
     "role": "planner",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 3308,
     "output_tokens": 450,
     "cost": "0.022232",
     "max_cost": "0.195764"
    },
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 2252,
     "output_tokens": 958,
     "cost": "0.028168",
     "max_cost": "0.188208"
    }
   ],
   "analyst": {
    "status": "done",
    "attempts": [
     "ok"
    ],
    "code": null,
    "failure_details": null,
    "report": "For query Q-0002, \"Grain refinement still strengthens BCC multi-principal-element alloys at 1000 °C,\" the outcome is **insufficient in the sources searched**. No dataset was frozen, so no analysis was run and there is no verdict. The evidence level is 1 (\"no dataset frozen\").\n\n**What was searched.** Two sources were searched, and both returned records:\n- the MPEA dataset (Borg et al. 2020)\n- the Texas A&M FCC dataset (Mulukutla et al. 2026)\n\nThe plan limited the scope to:\n- multi-principal-element (high-entropy) alloys\n- BCC phase class\n- the elevated temperature band\n- tension tests\n\nThe planned model was a Hall-Petch fit with alloy intercepts. Yield strength (MPa) was the outcome, and grain size (µm) was the predictor, transformed to its inverse square root.\n\n**Why records were not usable.** Under the eligibility rules, 1543 records were out of scope and 96 had a missing value. Many records lacked key fields:\n- **MPEA:** grain size was missing in 1308 records, test temperature band in 1545, test temperature in 181, test type in 395, yield strength in 478, ultimate tensile strength in 1006, and microstructure in 143.\n- **Texas A&M FCC:** test temperature and ultimate tensile strength were each missing in 94 records, and yield strength in 1.\n\n**Minimums not met.** A test needs all four fixed minimums to be met. None were:\n\n| Minimum | Required | Found |\n|---|---|---|\n| Records | 30 | 0 |\n| Groups | 10 | 0 |\n| Alloys | 5 | 0 |\n| Residual degrees of freedom | 10 | -1 |\n\n**What a test would need.** Records of BCC multi-principal-element alloys tested in tension in the elevated temperature band, each reporting both grain size and yield strength. These would need to come from enough groups and alloys to reach the minimums above. Such records were not found in the sources searched.",
    "template": null
   }
  },
  {
   "run": 3,
   "query": "Q-0003",
   "claim": "In FCC multi-principal-element alloys tested in tension, yield strength rises as grain size falls, both at room temperature and at cryogenic temperatures (-196 °C)",
   "status": "failed",
   "outcome": null,
   "verdict": null,
   "evidence_level": null,
   "fixed_plan": false,
   "failure": "claim_not_one_plan: the claim covers more than one temperature band, test type or alloy class; submit one question per band, test type and alloy class (narrower_missing)",
   "calls": [
    {
     "role": "planner",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 3334,
     "output_tokens": 398,
     "cost": "0.021296",
     "max_cost": "0.196096"
    }
   ],
   "analyst": null
  },
  {
   "run": 4,
   "query": "Q-0004",
   "claim": "In FCC multi-principal-element alloys tested in tension, yield strength rises as grain size falls, both at room temperature and at cryogenic temperatures (-196 °C)",
   "status": "completed",
   "outcome": "partly_sufficient",
   "verdict": null,
   "evidence_level": 1,
   "fixed_plan": false,
   "failure": null,
   "calls": [
    {
     "role": "planner",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 3299,
     "output_tokens": 306,
     "cost": "0.019316",
     "max_cost": "0.195672"
    },
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 1803,
     "output_tokens": 804,
     "cost": "0.023292",
     "max_cost": "0.18406"
    },
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 1851,
     "output_tokens": 847,
     "cost": "0.024344",
     "max_cost": "0.18472"
    }
   ],
   "analyst": {
    "status": "failed",
    "attempts": [
     "wording_refused",
     "malformed"
    ],
    "code": "malformed",
    "failure_details": null,
    "report": null,
    "template": null
   }
  },
  {
   "run": 5,
   "query": "Q-0005",
   "claim": "In FCC multi-principal-element alloys tested in tension, yield strength rises as grain size falls, both at room temperature and at cryogenic temperatures (-196 °C) (narrower question: phase class FCC; test type tension; room temperature)",
   "status": "completed",
   "outcome": "sufficient",
   "verdict": "supported",
   "evidence_level": 6,
   "fixed_plan": true,
   "failure": null,
   "calls": [
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 14445,
     "output_tokens": 1449,
     "cost": "0.08676",
     "max_cost": "0.30852"
    },
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 14493,
     "output_tokens": 1453,
     "cost": "0.087032",
     "max_cost": "0.30918"
    }
   ],
   "analyst": {
    "status": "failed",
    "attempts": [
     "wording_refused",
     "malformed"
    ],
    "code": "malformed",
    "failure_details": null,
    "report": null,
    "template": null
   }
  },
  {
   "run": 6,
   "query": "Q-0006",
   "claim": "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
   "status": "completed",
   "outcome": "sufficient",
   "verdict": "supported",
   "evidence_level": 6,
   "fixed_plan": true,
   "failure": null,
   "calls": [
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 14380,
     "output_tokens": 1206,
     "cost": "0.08164",
     "max_cost": "0.30782"
    }
   ],
   "analyst": {
    "status": "failed",
    "attempts": [
     "wording_refused"
    ],
    "code": "wording_refused",
    "failure_details": [
     {
      "attempt": 1,
      "problems": [
       "a p-value without 'approximate' in its sentence",
       "a p-value without 'approximate' in its sentence",
       "a p-value without 'approximate' in its sentence"
      ]
     }
    ],
    "report": null,
    "template": null
   }
  },
  {
   "run": 7,
   "query": "Q-0007",
   "claim": "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
   "status": "completed",
   "outcome": "sufficient",
   "verdict": "supported",
   "evidence_level": 6,
   "fixed_plan": true,
   "failure": null,
   "calls": [
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 14210,
     "output_tokens": 1445,
     "cost": "0.08574",
     "max_cost": "0.306496"
    },
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 14258,
     "output_tokens": 1756,
     "cost": "0.092152",
     "max_cost": "0.307156"
    }
   ],
   "analyst": {
    "status": "failed",
    "attempts": [
     "wording_refused",
     "numbers_unmatched"
    ],
    "code": "numbers_unmatched",
    "failure_details": [
     {
      "attempt": 1,
      "problems": [
       "a p-value outside its ready-made phrase"
      ]
     },
     {
      "attempt": 2,
      "problems": [
       "numbers_unmatched"
      ]
     }
    ],
    "report": null,
    "template": null
   }
  },
  {
   "run": 8,
   "query": "Q-0008",
   "claim": "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
   "status": "completed",
   "outcome": "sufficient",
   "verdict": "supported",
   "evidence_level": 6,
   "fixed_plan": true,
   "failure": null,
   "calls": [
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 2698,
     "output_tokens": 1505,
     "cost": "0.040892",
     "max_cost": "0.192464"
    },
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 2746,
     "output_tokens": 1326,
     "cost": "0.037504",
     "max_cost": "0.193124"
    }
   ],
   "analyst": {
    "status": "failed",
    "attempts": [
     "wording_refused",
     "wording_refused"
    ],
    "code": "wording_refused",
    "failure_details": [
     {
      "attempt": 1,
      "problems": [
       "paper figures outside their ready-made phrase",
       "a p-value outside its ready-made phrase"
      ]
     },
     {
      "attempt": 2,
      "problems": [
       "paper figures outside their ready-made phrase",
       "a p-value outside its ready-made phrase"
      ]
     }
    ],
    "report": null,
    "template": null
   }
  },
  {
   "run": 9,
   "query": "Q-0009",
   "claim": "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
   "status": "completed",
   "outcome": "sufficient",
   "verdict": "supported",
   "evidence_level": 6,
   "fixed_plan": true,
   "failure": null,
   "calls": [
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 2699,
     "output_tokens": 1469,
     "cost": "0.040176",
     "max_cost": "0.19246"
    }
   ],
   "analyst": {
    "status": "done",
    "attempts": [
     "ok"
    ],
    "code": null,
    "failure_details": null,
    "report": "For query Q-0009, the outcome is sufficient in the sources searched, and the verdict is supported under the stated model, in the sources searched. The scope came from the fixed reference plan; the scope was not read from the claim, so parts of the scope, such as test conditions and which records count as in scope, were not stated by the claim itself. The pooled analysis used 97 records on 22 alloys in 20 groups. It gave a pooled estimate of 424.9 with a standard error of 64.4, which points in the direction the claim describes. The pooled result has p ≈ 1.3e-6 (approximate, nominal, one-sided), based on 20 informative papers, an effective number of papers of 3.94, a largest share of 38.7% and 19 degrees of freedom. The effective number of papers is a measure of how evenly the slope information is spread across groups. It is not a count of independent papers, and here it is much smaller than the number of groups, which means a few groups carry most of the information.\n\nTwo sources were searched. In the searched MPEA dataset, 76 records on 13 alloys in 19 groups gave an estimate of 424.1 with a standard error of 62.2, labelled agrees, with p ≈ 1.1e-6 (approximate, nominal, one-sided) and 19 informative papers, an effective number of papers of 3.93, a largest share of 38.7% and 18 degrees of freedom. Many MPEA records could not be used. For example, 1308 lacked grain size and 478 lacked yield strength. The searched Texas A&M FCC dataset contributed 21 records on 9 alloys, but they all fall in 1 group. Its estimate of 1173.3 therefore could not be used for inference on its own: inference was not valid because of insufficient groups, and it is labelled not enough data.\n\nThe sufficiency rule was the fixed minimum. Each minimum was met:\n* Records: 97 against a minimum of 30 (met).\n* Alloys: 22 against 5 (met).\n* Groups: 20 against 10 (met).\n* Residual degrees of freedom: 74 against 10 (met).\n\nMinimums missed: none.\n\nIn the sensitivity checks, all 9 of 9 alternative sets agreed, with 0 conflicting and 0 short of data. Estimates ranged from 393.5 (without the group with the largest share of slope information) to 432.4 (scope not confirmed included). Dropping the group with the largest share left 89 records and gave an estimate of 393.5, with p ≈ 1.9e-4 (approximate, nominal, one-sided) and 19 informative papers, an effective number of papers of 3.24, a largest share of 52.1% and 18 degrees of freedom.\n\nA simulation check is an important caution. Under estimated settings, the method's false-positive rate was 8.2% (from 7.1% to 9.5%) against a nominal level of 0.05. Detection was 97.5%. Under fixed settings, the false-positive rate was 8.9%, with detection of 100.0%. In both cases the conclusion was that the method is over-confident on this data structure under the stated assumptions. For this reason the p-values are best read as nominal and somewhat optimistic. The association holds under the stated model in the sources searched, but it does not show that smaller grains produce the higher strength. Evidence level: 6 (sufficient with a verdict).",
    "template": "For query {query_number}, the outcome is {outcome_wording}, and the verdict is {verdict_wording}. The scope came from {scope_source}, so parts of the scope, such as test conditions and which records count as in scope, were not stated by the claim itself. The pooled analysis used {pooled_records} records on {pooled_alloys} alloys in {pooled_groups} groups. It gave a pooled estimate of {pooled_estimate} with a standard error of {pooled_std_error}, which points in the direction the claim describes. The pooled result has {pooled_p_phrase}, based on {pooled_figures_phrase}. The effective number of papers is a measure of how evenly the slope information is spread across groups. It is not a count of independent papers, and here it is much smaller than the number of groups, which means a few groups carry most of the information.\n\nTwo sources were searched. In the {mpea_search} MPEA dataset, {mpea_records} records on {mpea_alloys} alloys in {mpea_groups} groups gave an estimate of {mpea_estimate} with a standard error of {mpea_std_error}, labelled {mpea_label}, with {mpea_p_phrase} and {mpea_figures_phrase}. Many MPEA records could not be used. For example, {mpea_lacking_grain_size} lacked grain size and {mpea_lacking_yield_strength} lacked yield strength. The {tamu_fcc_search} Texas A&M FCC dataset contributed {tamu_fcc_records} records on {tamu_fcc_alloys} alloys, but they all fall in {tamu_fcc_groups} group. Its estimate of {tamu_fcc_estimate} therefore could not be used for inference on its own: inference was {tamu_fcc_inference} because of {tamu_fcc_inference_reason}, and it is labelled {tamu_fcc_label}.\n\nThe sufficiency rule was the {sufficiency_option}. Each minimum was met:\n* Records: {count_records} against a minimum of {minimum_records} ({met_records}).\n* Alloys: {count_alloys} against {minimum_alloys} ({met_alloys}).\n* Groups: {count_groups} against {minimum_groups} ({met_groups}).\n* Residual degrees of freedom: {count_resid_df} against {minimum_resid_df} ({met_resid_df}).\n\nMinimums missed: {minimums_missed}.\n\nIn the sensitivity checks, all {sensitivity_agrees} of {sensitivity_sets} alternative sets agreed, with {sensitivity_conflicts} conflicting and {sensitivity_not_enough_data} short of data. Estimates ranged from {sensitivity_smallest_estimate} ({sensitivity_smallest_set}) to {sensitivity_largest_estimate} ({sensitivity_largest_set}). Dropping the group with the largest share left {without_largest_share_records} records and gave an estimate of {without_largest_share_estimate}, with {without_largest_share_p_phrase} and {without_largest_share_figures_phrase}.\n\nA simulation check is an important caution. Under estimated settings, the method's false-positive rate was {estimated_false_positive} (from {estimated_false_positive_low} to {estimated_false_positive_high}) against a nominal level of {alpha}. Detection was {estimated_detection}. Under fixed settings, the false-positive rate was {fixed_false_positive}, with detection of {fixed_detection}. In both cases the conclusion was that {estimated_flag}. For this reason the p-values are best read as nominal and somewhat optimistic. The association holds under the stated model in the sources searched, but it does not show that smaller grains produce the higher strength. Evidence level: {evidence_level} ({evidence_level_wording})."
   }
  },
  {
   "run": 10,
   "query": "Q-0010",
   "claim": "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
   "status": "completed",
   "outcome": "sufficient",
   "verdict": "supported",
   "evidence_level": 6,
   "fixed_plan": true,
   "failure": null,
   "calls": [
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 2699,
     "output_tokens": 1424,
     "cost": "0.039276",
     "max_cost": "0.19246"
    },
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 2747,
     "output_tokens": 1083,
     "cost": "0.032648",
     "max_cost": "0.19312"
    }
   ],
   "analyst": {
    "status": "done",
    "attempts": [
     "wording_refused",
     "ok"
    ],
    "code": null,
    "failure_details": null,
    "report": "The outcome for this claim is sufficient in the sources searched, and the verdict is supported under the stated model, in the sources searched. Across both sources together, the pooled estimate of the slope linking yield strength to finer grain size is 424.9, with a standard error of 64.4, giving p ≈ 1.3e-6 (approximate, nominal, one-sided). This rests on 20 informative papers, an effective number of papers of 3.94, a largest share of 38.7% and 19 degrees of freedom. The effective number of papers describes how evenly the slope information is spread across groups. It is not a count of separate papers. The scope used here came from the fixed reference plan; the scope was not read from the claim, so the claim itself did not state the scope. The result is an association under the stated model, not a demonstration of the claim.\n\nBy source, the MPEA dataset gave an estimate of 424.1 (standard error 62.2, p ≈ 1.1e-6 (approximate, nominal, one-sided)). It used 76 records from 19 groups and 13 alloys, based on 19 informative papers, an effective number of papers of 3.93, a largest share of 38.7% and 18 degrees of freedom, and is labelled agrees. Many MPEA records could not be used: 1308 lacked grain size and 478 lacked yield strength. The Texas A&M FCC dataset gave an estimate of 1173.3, but it came from only 1 group, so inference was not valid (insufficient groups). That source is labelled not enough data.\n\nThe checks passed the fixed minimums. The analysis had 97 records against a minimum of 30, 20 groups against 10, 22 alloys against 5, and 74 residual degrees of freedom against 10. Minimums missed: none. Removing the group with the largest share of slope information gave 393.5 (p ≈ 1.9e-4 (approximate, nominal, one-sided), 19 informative papers, an effective number of papers of 3.24, a largest share of 52.1% and 18 degrees of freedom). Across 9 sensitivity sets, 9 agreed and 0 conflicted. The estimates ranged from 393.5 to 432.4.\n\nA simulation check found a false-positive rate of 8.0% under fixed settings and 8.6% under estimated settings, at an alpha of 0.05. Under both settings, the method is over-confident on this data structure under the stated assumptions. The p-values should therefore be read as approximate and somewhat optimistic. The evidence level is 6, which corresponds to sufficient with a verdict.",
    "template": "The outcome for this claim is {outcome_wording}, and the verdict is {verdict_wording}. Across both sources together, the pooled estimate of the slope linking yield strength to finer grain size is {pooled_estimate}, with a standard error of {pooled_std_error}, giving {pooled_p_phrase}. This rests on {pooled_figures_phrase}. The effective number of papers describes how evenly the slope information is spread across groups. It is not a count of separate papers. The scope used here came from {scope_source}, so the claim itself did not state the scope. The result is an association under the stated model, not a demonstration of the claim.\n\nBy source, the MPEA dataset gave an estimate of {mpea_estimate} (standard error {mpea_std_error}, {mpea_p_phrase}). It used {mpea_records} records from {mpea_groups} groups and {mpea_alloys} alloys, based on {mpea_figures_phrase}, and is labelled {mpea_label}. Many MPEA records could not be used: {mpea_lacking_grain_size} lacked grain size and {mpea_lacking_yield_strength} lacked yield strength. The Texas A&M FCC dataset gave an estimate of {tamu_fcc_estimate}, but it came from only {tamu_fcc_groups} group, so inference was {tamu_fcc_inference} ({tamu_fcc_inference_reason}). That source is labelled {tamu_fcc_label}.\n\nThe checks passed the fixed minimums. The analysis had {count_records} records against a minimum of {minimum_records}, {count_groups} groups against {minimum_groups}, {count_alloys} alloys against {minimum_alloys}, and {count_resid_df} residual degrees of freedom against {minimum_resid_df}. Minimums missed: {minimums_missed}. Removing the group with the largest share of slope information gave {without_largest_share_estimate} ({without_largest_share_p_phrase}, {without_largest_share_figures_phrase}). Across {sensitivity_sets} sensitivity sets, {sensitivity_agrees} agreed and {sensitivity_conflicts} conflicted. The estimates ranged from {sensitivity_smallest_estimate} to {sensitivity_largest_estimate}.\n\nA simulation check found a false-positive rate of {fixed_false_positive} under fixed settings and {estimated_false_positive} under estimated settings, at an alpha of {alpha}. Under both settings, {fixed_flag}. The p-values should therefore be read as approximate and somewhat optimistic. The evidence level is {evidence_level}, which corresponds to {evidence_level_wording}."
   }
  },
  {
   "run": 11,
   "query": "Q-0011",
   "claim": "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
   "status": "completed",
   "outcome": "sufficient",
   "verdict": "supported",
   "evidence_level": 6,
   "fixed_plan": true,
   "failure": null,
   "calls": [
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 2699,
     "output_tokens": 1356,
     "cost": "0.037916",
     "max_cost": "0.192456"
    }
   ],
   "analyst": {
    "status": "done",
    "attempts": [
     "ok"
    ],
    "code": null,
    "failure_details": null,
    "report": "For query Q-0011, the outcome is sufficient in the sources searched, and the verdict is supported under the stated model, in the sources searched. The evidence level is 6 (sufficient with a verdict). The scope came from the fixed reference plan; the scope was not read from the claim, so it was not taken from the wording of the claim. The pooled slope estimate, which relates yield strength to grain size, is 424.9 with a standard error of 64.4 and p ≈ 1.3e-6 (approximate, nominal, one-sided). It is based on 97 records from 22 alloys, with 20 informative papers, an effective number of papers of 3.94, a largest share of 38.7% and 19 degrees of freedom. The effective number of papers describes how the slope information is spread across groups. It is not a count of independent papers. This is an association under the stated model. It does not show that grain size drives strength, and it does not prove the claim.\n\nThe sufficiency rule used was the fixed minimum. Records were met (minimum 30, found 97). Alloys were met (minimum 5, found 22). Groups were met (minimum 10, found 20). Residual degrees of freedom were met (minimum 10, found 74). Minimums missed: none.\n\nAlmost all of the usable data came from the MPEA dataset. That source gave an estimate of 424.1 (standard error 62.2, p ≈ 1.1e-6 (approximate, nominal, one-sided), 19 informative papers, an effective number of papers of 3.93, a largest share of 38.7% and 18 degrees of freedom), and its label is agrees. Many MPEA entries could not be used. For example, 1308 entries lacked grain size and 478 lacked yield strength.\n\nThe Texas A&M FCC dataset was searched but was labelled not enough data. It gave 21 records but only 1 group, so inference was not valid (insufficient groups).\n\nSensitivity checks also supported the result. Of 9 alternative data sets, 9 agreed, 0 conflicted and 0 lacked enough data. Estimates ranged from 393.5 (\"without the group with the largest share of slope information\") to 432.4 (\"scope not confirmed included\"). Dropping the group with the largest share of slope information gave 393.5 with p ≈ 1.9e-4 (approximate, nominal, one-sided) and 19 informative papers, an effective number of papers of 3.24, a largest share of 52.1% and 18 degrees of freedom.\n\nSimulation checks raise a caution. With fixed assumptions, the false positive rate was 8.6% (range 7.4% to 9.9%). With estimated assumptions, it was 7.5% (range 6.4% to 8.8%). Both are above the nominal level of 0.05, and in each case the flag reads: the method is over-confident on this data structure under the stated assumptions. Detection rates were high, at 100.0% and 97.6%. For these reasons the p-values should be read as approximate.",
    "template": "For query {query_number}, the outcome is {outcome_wording}, and the verdict is {verdict_wording}. The evidence level is {evidence_level} ({evidence_level_wording}). The scope came from {scope_source}, so it was not taken from the wording of the claim. The pooled slope estimate, which relates yield strength to grain size, is {pooled_estimate} with a standard error of {pooled_std_error} and {pooled_p_phrase}. It is based on {pooled_records} records from {pooled_alloys} alloys, with {pooled_figures_phrase}. The effective number of papers describes how the slope information is spread across groups. It is not a count of independent papers. This is an association under the stated model. It does not show that grain size drives strength, and it does not prove the claim.\n\nThe sufficiency rule used was the {sufficiency_option}. Records were {met_records} (minimum {minimum_records}, found {count_records}). Alloys were {met_alloys} (minimum {minimum_alloys}, found {count_alloys}). Groups were {met_groups} (minimum {minimum_groups}, found {count_groups}). Residual degrees of freedom were {met_resid_df} (minimum {minimum_resid_df}, found {count_resid_df}). Minimums missed: {minimums_missed}.\n\nAlmost all of the usable data came from the MPEA dataset. That source gave an estimate of {mpea_estimate} (standard error {mpea_std_error}, {mpea_p_phrase}, {mpea_figures_phrase}), and its label is {mpea_label}. Many MPEA entries could not be used. For example, {mpea_lacking_grain_size} entries lacked grain size and {mpea_lacking_yield_strength} lacked yield strength.\n\nThe Texas A&M FCC dataset was searched but was labelled {tamu_fcc_label}. It gave {tamu_fcc_records} records but only {tamu_fcc_groups} group, so inference was {tamu_fcc_inference} ({tamu_fcc_inference_reason}).\n\nSensitivity checks also supported the result. Of {sensitivity_sets} alternative data sets, {sensitivity_agrees} agreed, {sensitivity_conflicts} conflicted and {sensitivity_not_enough_data} lacked enough data. Estimates ranged from {sensitivity_smallest_estimate} (\"{sensitivity_smallest_set}\") to {sensitivity_largest_estimate} (\"{sensitivity_largest_set}\"). Dropping the group with the largest share of slope information gave {without_largest_share_estimate} with {without_largest_share_p_phrase} and {without_largest_share_figures_phrase}.\n\nSimulation checks raise a caution. With fixed assumptions, the false positive rate was {fixed_false_positive} (range {fixed_false_positive_low} to {fixed_false_positive_high}). With estimated assumptions, it was {estimated_false_positive} (range {estimated_false_positive_low} to {estimated_false_positive_high}). Both are above the nominal level of {alpha}, and in each case the flag reads: {estimated_flag}. Detection rates were high, at {fixed_detection} and {estimated_detection}. For these reasons the p-values should be read as approximate."
   }
  },
  {
   "run": 12,
   "query": "Q-0012",
   "claim": "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
   "status": "completed",
   "outcome": "sufficient",
   "verdict": "supported",
   "evidence_level": 6,
   "fixed_plan": true,
   "failure": null,
   "calls": [
    {
     "role": "analyst",
     "model": "claude-opus-5-5",
     "status": "succeeded",
     "input_tokens": 3361,
     "output_tokens": 1500,
     "cost": "0.043444",
     "max_cost": "0.1995"
    }
   ],
   "analyst": {
    "status": "done",
    "attempts": [
     "ok"
    ],
    "code": null,
    "failure_details": [],
    "report": "The claim is that in FCC multi-principal-element alloys, yield strength is higher when grain size is smaller. The outcome is sufficient in the sources searched, and the verdict is supported under the stated model, in the sources searched. The main cautions are these. The simulation check found the method over-confident on this data structure. The effective number of groups is small. A single group carries a large share of the slope information. So the nominal p-value should be read as more favourable than it really is.\n\nThe test fitted yield strength (MPa) as a baseline for each alloy plus one coefficient, shared by all alloys, times the inverse square root of grain size (µm); the estimate is that coefficient, in MPa·µm^0.5. The pooled estimate is 424.9 MPa·µm^0.5, with a standard error of 64.4 MPa·µm^0.5, giving p ≈ 1.3e-6 (approximate, nominal, one-sided); the estimate is positive, the direction the claim describes. The pooled fit used 97 records on 22 alloys, with 20 informative groups, an effective number of groups of 3.94, a largest share of 38.7% and 19 degrees of freedom. A group is a paper, or, for a source that is a single dataset, the whole dataset. The effective number of groups shows how concentrated the slope information is across groups. It is not a count of independent groups. The scope was set by the fixed reference plan and was not read from the claim.\n\nTwo sources were searched.\n\n* **MPEA dataset:** This source supplied most of the data, with 76 records on 13 alloys from 19 groups. On its own it gave 424.1 MPa·µm^0.5 (p ≈ 1.1e-6 (approximate, nominal, one-sided)), which is in agreement with the pooled result. Many of its records could not be used because they lacked a needed field. For example, 1308 lacked grain size and 478 lacked yield strength.\n* **Texas A&M FCC dataset:** This source supplied 21 records on 9 alloys. Because it is a single dataset, it counts as 1 group. It is therefore too few groups to test alone, and its own estimate of 1173.3 MPa·µm^0.5 is not a valid separate test (insufficient groups).\n\nThe sensitivity checks re-ran the test on 9 alternative data sets. 9 agreed with the pooled result and 0 conflicted. The estimates ranged from 393.5 MPa·µm^0.5 (without the group with the largest share of slope information) to 432.4 MPa·µm^0.5 (scope not confirmed included). Dropping the group with the largest share gave 393.5 MPa·µm^0.5 (p ≈ 1.9e-4 (approximate, nominal, one-sided)), with 19 informative groups, an effective number of groups of 3.24, a largest share of 52.1% and 18 degrees of freedom. This is still in agreement with the pooled result, but the information then becomes even more concentrated in one remaining group.\n\nIn the simulation check, with noise levels estimated from the data, the test was significant in 7.7% of simulations with no effect (6.6% to 9.0%, a 95% simulation interval covering simulation uncertainty only); with fixed illustrative noise levels, the test was significant in 8.5% of simulations with no effect (7.3% to 9.8%, a 95% simulation interval covering simulation uncertainty only), against a nominal level of 5.0%. Under both, the method is over-confident on this data structure under the stated assumptions. This means that when there is truly no effect, the test flags one more often than its nominal level of 5.0%. The check also gives detection rates when a real effect is present:\n\n* With noise levels estimated from the data, the detection rate was 97.2%.\n* With fixed illustrative noise levels, the detection rate was 100.0%.\n\nA test requires fixed minimums: at least 30 records, 10 groups, 5 alloys and 10 residual degrees of freedom. The data provided 97 records, 20 groups, 22 alloys and 74 residual degrees of freedom, so every minimum was met and none was missed. Even so, the result describes an association under the stated model in the sources searched. It does not establish the claim. More independent groups with spread-out slope information would make the result less dependent on any one group.",
    "template": "The claim is that in FCC multi-principal-element alloys, yield strength is higher when grain size is smaller. The outcome is {outcome_wording}, and the verdict is {verdict_wording}. The main cautions are these. The simulation check found the method over-confident on this data structure. The effective number of groups is small. A single group carries a large share of the slope information. So the nominal p-value should be read as more favourable than it really is.\n\n{model_sentence} The pooled estimate is {pooled_estimate}, with a standard error of {pooled_std_error}, giving {pooled_p_phrase}; {direction_note}. The pooled fit used {pooled_records} records on {pooled_alloys} alloys, with {pooled_figures_phrase}. {group_definition} The effective number of groups shows how concentrated the slope information is across groups. It is not a count of independent groups. {scope_source}\n\nTwo sources were searched.\n\n* **MPEA dataset:** This source supplied most of the data, with {mpea_records} records on {mpea_alloys} alloys from {mpea_groups} groups. On its own it gave {mpea_estimate} ({mpea_p_phrase}), which is {mpea_label}. Many of its records could not be used because they lacked a needed field. For example, {mpea_lacking_grain_size} lacked grain size and {mpea_lacking_yield_strength} lacked yield strength.\n* **Texas A&M FCC dataset:** This source supplied {tamu_fcc_records} records on {tamu_fcc_alloys} alloys. Because it is a single dataset, it counts as {tamu_fcc_groups} group. It is therefore {tamu_fcc_label}, and its own estimate of {tamu_fcc_estimate} is not a valid separate test ({tamu_fcc_inference_reason}).\n\nThe sensitivity checks re-ran the test on {sensitivity_sets} alternative data sets. {sensitivity_agrees} agreed with the pooled result and {sensitivity_conflicts} conflicted. The estimates ranged from {sensitivity_smallest_estimate} ({sensitivity_smallest_set}) to {sensitivity_largest_estimate} ({sensitivity_largest_set}). Dropping the group with the largest share gave {without_largest_share_estimate} ({without_largest_share_p_phrase}), with {without_largest_share_figures_phrase}. This is still {without_largest_share_label}, but the information then becomes even more concentrated in one remaining group.\n\n{calibration_summary} This means that when there is truly no effect, the test flags one more often than its nominal level of {nominal_level}. The check also gives detection rates when a real effect is present:\n\n* With {estimated_calibration_name}, the detection rate was {estimated_detection}.\n* With {fixed_calibration_name}, the detection rate was {fixed_detection}.\n\nA test requires fixed minimums: at least {minimum_records} records, {minimum_groups} groups, {minimum_alloys} alloys and {minimum_resid_df} residual degrees of freedom. The data provided {count_records} records, {count_groups} groups, {count_alloys} alloys and {count_resid_df} residual degrees of freedom, so every minimum was met and none was missed. Even so, the result describes an association under the stated model in the sources searched. It does not establish the claim. More independent groups with spread-out slope information would make the result less dependent on any one group."
   }
  }
 ],
 "total_actual_cost": "1.027756",
 "total_reserved_maximum": "4.851056",
 "calls": 21
}
```
## 8. Mutation checks (all re-run on the final tests; a control run with no mutation last)

```
d01      CAUGHT  2 failed, 36 passed in 10.57s
d02      CAUGHT  4 failed, 34 passed in 10.90s
d03      CAUGHT  1 failed, 37 passed in 10.44s
d04      CAUGHT  1 failed, 37 passed in 10.54s
d05      CAUGHT  1 failed, 37 passed in 10.54s
p01      CAUGHT  1 failed, 38 passed in 30.39s
p02      CAUGHT  2 failed, 37 passed in 30.11s
p03      CAUGHT  1 failed, 38 passed in 30.40s
p04      CAUGHT  1 failed, 38 passed in 30.36s
n02      CAUGHT  1 failed, 38 passed in 30.33s
n03      CAUGHT  3 failed, 36 passed in 30.38s
c01      CAUGHT  1 failed, 38 passed in 30.36s
k01      CAUGHT  2 failed, 9 passed in 11.60s
k02      CAUGHT  1 failed, 10 passed in 11.73s
x01      CAUGHT  4 failed, 70 passed in 40.50s
x02      CAUGHT  3 failed, 71 passed in 41.17s
x03      CAUGHT  2 failed, 72 passed in 40.80s
x04      CAUGHT  1 failed, 73 passed in 41.22s
x06      CAUGHT  1 failed, 73 passed in 40.88s
y01      CAUGHT  2 failed, 72 passed in 41.04s
y02      CAUGHT  6 failed, 68 passed in 40.93s
y03      CAUGHT  2 failed, 9 passed in 8.97s
o01      CAUGHT  1 failed, 15 passed in 72.41s (0:01:12)
o03      CAUGHT  1 failed, 15 passed in 67.00s (0:01:07)
a01      CAUGHT  4 failed, 7 passed in 7.95s
g01      CAUGHT  3 failed, 4 passed in 19.09s
control  clean  85 passed in 44.79s
```

The specification and the runner:

```python
"""Every step 8b mutation, re-run on the final tests (scratch copy, PYTHONPATH). Each: (id, file under hypocurate/,
old, new, tests). A mutation is caught when at least one named test fails."""
T = "/workspaces/hypocurate/tests/"
M06 = "db/migrations/versions/0006_query_option_and_partly_sufficient.py"
MUTATIONS = [
 ("d01", M06, "        IF NEW.sufficiency_option IS DISTINCT FROM (", "        IF false AND NEW.sufficiency_option IS DISTINCT FROM (", ["test_migrations_step8b.py"]),
 ("d02", M06, "            IF NOT EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND stage = 'narrowing'", "            IF false AND NOT EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.id AND stage = 'narrowing'", ["test_migrations_step8b.py"]),
 ("d03", M06, "        IF EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.run_id AND stage = 'narrowing' AND status = 'done'", "        IF false AND EXISTS (SELECT 1 FROM stage_result WHERE run_id = NEW.run_id AND stage = 'narrowing' AND status = 'done'", ["test_migrations_step8b.py"]),
 ("d04", M06, "        IF TG_OP = 'UPDATE' AND OLD.status <> 'draft'", "        IF false AND TG_OP = 'UPDATE' AND OLD.status <> 'draft'", ["test_migrations_step8b.py"]),
 ("d05", M06, "            IF EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.id)\n               OR", "            IF false AND EXISTS (SELECT 1 FROM plan WHERE run_id = NEW.id)\n               OR", ["test_migrations_step8b.py"]),
 ("p01", "pipeline/agents/planner.py", "            if one_plan(answer.claim_scope):\n                build_plan(", "            if False:\n                build_plan(", ["test_planner_narrowing.py"]),
 ("p02", "pipeline/agents/planner.py", "    if set(data) != KEYS:", "    if not KEYS <= set(data):", ["test_planner_narrowing.py"]),
 ("p03", "pipeline/agents/planner.py", "            if set(b) != {\"band\", \"min\", \"max\"} or", "            if False and set(b) != {\"band\", \"min\", \"max\"} or", ["test_planner_narrowing.py"]),
 ("p04", "pipeline/agents/planner.py", "    if not isinstance(stated, dict) or set(stated) != SCOPE_KEYS", "    if False and set(stated) != SCOPE_KEYS", ["test_planner_narrowing.py"]),
 ("n02", "pipeline/narrowing.py", "and _known(cell, \"grain_size\") and _known(cell, outcome)", "and _known(cell, \"grain_size\")", ["test_planner_narrowing.py"]),
 ("n03", "pipeline/narrowing.py", "                    and all(any(matches(c, d, v) for v in scope[d]) for d in others))", "                    )", ["test_planner_narrowing.py"]),
 ("c01", "pipeline/completion.py", "        if stored != [tuple(c) for c in current]:", "        if False:", ["test_planner_narrowing.py"]),
 ("k01", "access/fields.py", "\"SELECT id, kind, category FROM flag WHERE run_id = :r ORDER BY id\"", "\"SELECT id, kind, category FROM flag WHERE run_id = :r AND critic_class IS NULL ORDER BY id\"", ["test_critic.py"]),
 ("k02", "pipeline/agents/critic.py", "        for flag_id, (cls, reason) in sorted(accepted.items()):", "        for flag_id, (cls, reason) in []:", ["test_critic.py"]),
 ("x01", "pipeline/agents/analyst.py", "        if counts[\"digits_outside_placeholders\"]:", "        if False:", ["test_analyst.py"]),
 ("x02", "pipeline/agents/analyst.py", "        if counts[\"unknown_names\"]:", "        if False:", ["test_analyst.py"]),
 ("x03", "pipeline/agents/analyst.py", "        if counts[\"required_missing\"]:", "        if False:", ["test_analyst.py"]),
 ("x04", "pipeline/analyst_names.py", "    if withheld:\n        return out", "    if False:\n        return out", ["test_analyst.py"]),
 ("x06", "pipeline/analyst_names.py", "    labels = {e[\"set\"]: st.label(e, pooled, alpha) for e in sets}", "    labels = {e[\"set\"]: (\"agrees\" if (e.get(\"estimate\") or 0) > 0 else \"conflicts\") for e in sets}", ["test_analyst.py"]),
 ("y01", "pipeline/agents/analyst.py", "        if counts[\"result_phrases_missing\"]:", "        if False:", ["test_analyst.py"]),
 ("y02", "pipeline/agents/text_checks.py", "    problems += [f\"forbidden: {m.group(0).lower()}\" for m in ALWAYS_FORBIDDEN.finditer(text)]", "", ["test_analyst.py"]),
 ("y03", "access/fields.py", "        names = an.analysis_names(stats, gap, plan_facts, note)", "        names = {**an.analysis_names(stats, gap, plan_facts, note), \"leak\": str(stats.get(\"analyses\"))}", ["test_access_step8b.py"]),
 ("o01", "pipeline/orchestrator.py", "    if stored != current:  # B1", "    if False:  # B1", ["test_orchestrator.py"]),
 ("o03", "pipeline/orchestrator.py", "        if spent:\n            return", "        if False:\n            return", ["test_orchestrator.py"]),
 ("a01", "access/stage.py", "        return \"narrowed\" if row.narrowed else \"before_lock\"", "        return \"before_lock\"", ["test_access_step8b.py"]),
 ("g01", "access/guarded.py", "PRELOADED = (\"psycopg\", \"scipy\")", "PRELOADED = (\"psycopg\",)", ["test_agent_libraries.py"]),
]
```
```python
import os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from mutations import MUTATIONS, T
M = os.path.expanduser("~/hc-work/step08b/mut")
env = dict(os.environ, PYTHONPATH=M)
env["DATABASE_URL"] = open("/workspaces/hypocurate/.env").read().split("DATABASE_URL=")[1].split("\n")[0]
results = []
for mid, f, old, new, tests in MUTATIONS + [("control", None, None, None, ["test_analyst.py", "test_critic.py"])]:
    shutil.rmtree(os.path.join(M, "hypocurate"), ignore_errors=True)
    shutil.copytree("/workspaces/hypocurate/hypocurate", os.path.join(M, "hypocurate"))
    if f:
        p = os.path.join(M, "hypocurate", f); s = open(p).read()
        assert s.count(old) >= 1, (mid, "pattern not found")
        open(p, "w").write(s.replace(old, new, 1))
    out = subprocess.run([sys.executable if False else "/workspaces/hypocurate/.venv/bin/pytest", "-q", "-p", "no:cacheprovider",
                          "--rootdir=/workspaces/hypocurate"] + [T + t for t in tests], cwd=os.path.expanduser("~/hc-work/step08b"),
                         env=env, capture_output=True, text=True).stdout.strip().splitlines()[-1]
    caught = "failed" in out or "error" in out
    line = f"{mid:8} {'CAUGHT' if caught else ('clean' if mid == 'control' else 'SURVIVED')}  {out}"
    print(line, flush=True); results.append(line)
```
## 9. New tests on `main`'s code

Milestone 1, `tests/test_migrations_step8b.py` on `main`'s package with the vocabulary and model constants as scaffolding (the up/down/up test passes there: nothing above 0005 to round-trip):

```
____________________ test_a_failed_upgrade_changes_nothing _____________________
    def test_a_failed_upgrade_changes_nothing(engine):
    @pytest.mark.parametrize("shape", ["none", "proceed", "running", "failed"])
    @pytest.mark.parametrize("shape", ["none", "proceed", "running", "failed"])
    @pytest.mark.parametrize("shape", ["none", "proceed", "running", "failed"])
_ test_partly_sufficient_needs_a_done_narrowing_decision_of_partly_sufficient[failed] _
w = <model_builder.World object at 0x7848cd3161a0>, shape = 'failed'
    @pytest.mark.parametrize("shape", ["none", "proceed", "running", "failed"])
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_0006_is_the_head_and_follows_0005
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_0006_replaces_no_earlier_function
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_each_new_trigger_fires_after_the_earlier_one_on_its_table[hypothesis_version-hc_version_insert]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_each_new_trigger_fires_after_the_earlier_one_on_its_table[hypothesis_version-hc_version_update]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_each_new_trigger_fires_after_the_earlier_one_on_its_table[plan-hc_plan_insert]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_each_new_trigger_fires_after_the_earlier_one_on_its_table[run-hc_run_update]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_the_critic_classes_are_the_codes_of_the_vocabulary
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_a_failed_upgrade_changes_nothing
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_the_downgrade_refuses_while_a_query_uses_another_option
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_a_version_without_an_option_uses_the_default
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_the_option_comes_from_the_fixed_list
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_the_option_can_change_while_a_draft_and_never_after
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_a_narrower_question_has_its_originals_option
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_the_plans_option_is_the_querys[fixed_minimum-fixed_minimum-False]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_the_plans_option_is_the_querys[use_available-use_available-False]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_the_plans_option_is_the_querys[fixed_minimum-use_available-True]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_the_plans_option_is_the_querys[use_available-fixed_minimum-True]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_the_plans_own_option_check_still_refuses_an_unknown_option
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_a_run_completes_as_partly_sufficient_with_its_narrowing_decision_and_no_plan
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_partly_sufficient_needs_a_done_narrowing_decision_of_partly_sufficient[none]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_partly_sufficient_needs_a_done_narrowing_decision_of_partly_sufficient[proceed]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_partly_sufficient_needs_a_done_narrowing_decision_of_partly_sufficient[running]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_partly_sufficient_needs_a_done_narrowing_decision_of_partly_sufficient[failed]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_partly_sufficient_is_refused_for_a_run_with_a_plan
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_no_plan_is_locked_after_a_narrowing_decision_of_partly_sufficient
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_a_narrowing_decision_to_proceed_allows_the_lock
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_other_outcomes_are_unaffected_by_the_new_rule[insufficient]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_other_outcomes_are_unaffected_by_the_new_rule[sufficient]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_each_critic_class_is_accepted[cannot_tell]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_each_critic_class_is_accepted[different_specimens_or_conditions]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_each_critic_class_is_accepted[possible_transcription_or_unit_error]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_each_critic_class_is_accepted[same_measurement]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_a_class_outside_the_list_or_an_unbounded_reason_is_refused[agrees-None-ck_flag_critic_class]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_a_class_outside_the_list_or_an_unbounded_reason_is_refused[same_measurement-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-ck_flag_critic_reason]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_a_class_outside_the_list_or_an_unbounded_reason_is_refused[same_measurement-   -ck_flag_critic_reason]
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_a_reason_needs_a_class
FAILED ../../../../workspaces/hypocurate/tests/test_migrations_step8b.py::test_a_class_without_a_reason_is_allowed
37 failed, 1 passed in 18.49s
```

Milestone 2: the 17 new access tests all failed on `main`'s package (which also lacks 0006). The tests of milestones 3 to 9 exercise modules that do not exist on `main` (`queries`, `narrowing`, `planner`, `critic`, `analyst`, `analyst_names`, `display`, `orchestrator`, `cli_runs`), so they fail there on import. Each change made after the live checks was tested against the code before it (the counts are in the commit messages).
## 10. The suite and the images

The whole suite on this head (locally):

```
1728 passed, 1 warning in 767.09s (0:12:47)
```

The test image at milestone 8 (rebuilt; the suite then had 1,679 tests):

```
1679 passed, 1 warning in 817.78s (0:13:37)
exit 0
```

The guard checks inside the runtime image (its own package; no pytest in the image):

```
ALL GUARD CHECKS PASSED IN THE RUNTIME IMAGE
{'statistics_libraries': ['ok'], 'refusals_after_clean_import': [], 'agent_libraries': ['ok'], 'after': ['ok', 'refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code', 'refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code', 'refused: file guard: reading /tmp/tmpfgyg098l/.env is outside the approved inputs of pipeline code']}
```
```python
"""The guard tests' checks (tests/test_agent_libraries.py, the step 8b ones), run in the runtime image with its
own package: the image has no pytest and no tests/."""
import io, logging, os, tempfile
stream = io.StringIO()
logging.basicConfig(level=logging.WARNING, stream=stream)
from hypocurate.access.guarded import PRELOADED, run_guarded
PROBE = "hypocurate.access.guard_probe:probe"
results = {}
assert PRELOADED == ("psycopg", "scipy"), PRELOADED
results["statistics_libraries"] = run_guarded(PROBE, [{"op": "statistics_libraries"}], env=dict(os.environ), timeout=300)
results["refusals_after_clean_import"] = [l for l in stream.getvalue().splitlines() if "file_guard" in l]
results["agent_libraries"] = run_guarded(PROBE, [{"op": "agent_libraries"}], env=dict(os.environ), timeout=300)
d = tempfile.mkdtemp(); planted = os.path.join(d, ".env"); open(planted, "w").write("PLANTED_SECRET=x\n")
results["after"] = run_guarded(PROBE, [{"op": "statistics_libraries"}, {"op": "ctypes_string_at"}, {"op": "ctypes"},
                                       {"op": "dotenv", "path": planted}], env=dict(os.environ), timeout=300)
assert results["statistics_libraries"] == ["ok"], results
assert results["refusals_after_clean_import"] == [], results
assert results["agent_libraries"] == ["ok"], results
a = results["after"]
assert a[0] == "ok"
assert a[1] == "refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code", a
assert a[2] == "refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code", a
assert a[3].startswith("refused: file guard: reading"), a
print("ALL GUARD CHECKS PASSED IN THE RUNTIME IMAGE"); print(results)
```
## 11. The plan file and the scripts

### The step 8b plan file (owner's answers and the checklist)

```markdown
# Step 8b — Planner, narrowing, Critic, Analyst, orchestrator, `run`/`show`/`dispatch` (APPROVED by the owner, 2026-10-07)

## Owner's approval (2026-10-07, verbatim)
"Yes, approved: create step-08b-agents and build part 8b. This is my decision. I approve migration 0006
and the safeguard changes listed, subject to the second-model review before merging."

Four additions:
- **B1 Narrower question and source versions.** "The narrowing decision stores the source versions its
  counts were taken on. When the narrower question is dispatched, check that the run's source versions
  are the same; if any differs, refuse with a stated reason. Add it to the failure table and the tests."
- **B2 Partly path, Analyst failure.** "On the partly-sufficient path, if the Analyst fails for any reason
  (checks, provider, cap), the run still completes as partly sufficient with 'explanation unavailable'
  and the narrower question is still created. Add the row and a test."
- **B3 Drafts before the live go.** "Before asking for the go on the live set, show me your drafts: the
  Analyst's wording list, and the instruction text and limits for the Planner, the Critic and the Analyst."
- **B4 Live run A vs the reference plan.** "For live run A, report field by field whether the Planner's
  plan equals the reference plan. If it differs, report the difference and stop. Do not adjust the
  instructions to make it match without telling me first."

Conditions: push at each milestone; stop and ask before the live set and anything else that costs money;
when built: full suite, summary, review packet, push, and stop. Do not merge.
Expected stops for the owner: the `ACCEPTED_DISCLOSURES` wording (M2); `PRELOADED` if the guarded run
needs it, a changed reference number, a test that seems wrong (any time); B3 drafts + price check + the
live-set go (M9); B4 report after run A.

## Context
PRD 15 step 8, second part. 8a (merged d76c86a, live, schema 0005) built the agent core, the
Curator, the caps and the temperature bands. 8b wires the remaining three agents and the code role
`narrowing` into one orchestrated run, adds the partly-sufficient path, and makes criteria 14.1 and
14.3 pass from the command line. Every owner decision in `radiant-hugging-trinket.md` (Q1–Q10,
additions 1–4) stands. Branch `step-08b-agents` from `main` — **not created until the owner approves**.

Standing requirements (owner, this session): no code decision ever reads the Critic's class; the
Analyst receives stored facts only, and nothing outcome-derived for a run below the minimums; the
narrowing decision uses counts of structure only and is taken before any lock; the regression suite
makes no live calls; ask before anything that costs money.

## Findings from reading main (for the owner)
1. **No production code creates or dispatches a hypothesis.** Only `tests/model_builder.py` does.
   8b needs `pipeline/queries.py` (create version, submit, confirm domain, dispatch, run_source rows
   for every registered source, run_agent_setting rows).
2. **The plan file's run order puts the Analyst after `copy_partly_sufficient`.** The database
   refuses that: a stage result and a model call are allowed on a completed run only for the
   Commentator (0001 `hc_stage_result_insert`, `hc_model_call_insert`, 0005 `hc_agent_invocation_insert`).
   And the narrower hypothesis can only be inserted once the original is completed as partly
   sufficient (0001 `hc_hypothesis_insert`). Correct order: narrowing decision → Analyst → copy → narrower question.
3. **The query's sufficiency option has no home before the lock.** `plan.sufficiency_option` exists;
   `hypothesis_version` has no such column. CLAUDE.md rule 7 calls it a query parameter.
4. **Completing a run with no plan needs no trigger change.** 0001 `hc_run_update` needs a plan only
   for outcome 'sufficient'; 0004 `ck_run_evidence_level` accepts level 1 with no verdict. But
   nothing in the database today stops a run with no narrowing decision from being completed as
   partly sufficient, or a plan being locked after one (proposed strengthening in 0006).
5. Real-data structure counts (records with grain size and yield strength at an accepted status,
   read from the frozen files, no model): BCC at ≥ 900 °C: 0 (of 90 compression records) → 14.3's
   claim ends insufficient, missing field grain size. FCC tension at room temperature 89 (MPEA) + 93
   (Texas A&M); FCC tension cryogenic 0 (of 9); FCC tension ≥ 900 °C 0 (of 2). So a real
   partly-sufficient claim exists: "FCC MPEAs in tension, at room temperature and at cryogenic
   temperature" → narrower question at room temperature only.

## Per-agent table (due before 8b)
| | Planner (Opus 5.5) | Critic (Haiku 4.5) | Analyst (Opus 5.5) |
|---|---|---|---|
| Stage | `before_lock` (running, no plan, no narrowing decision) | `curation` (plan locked, Checks done, no freeze) | `analysis`, `closed_without_freeze`, or new `narrowed` (running, no plan, partly-sufficient narrowing decision stored) |
| Receives (access list, unchanged from step 5) | `claim`, `domain`, `sources_meta`, `tag_values`, `record_counts` (counts per field status and per non-outcome category value, from the sealed versions) | `sources_meta`, `record_metadata`, `flags_kind` (kind, category, record ids; never the numbers). The request renders only the records the flags name. | Q6: `claim`, `domain`, `sources_meta`, `coverage`, `analyst_facts` (new field, below). At `narrowed`: the narrowing facts only. |
| May return | One JSON object: `domain_matches` (yes/no); `claim_scope` (phase classes, bands each with a °C range unless room temperature, test types, alloy class — vocabularies only); `parameters` (outcome field from `SUPPORTED_OUTCOMES`; scope; exclusion rules from the menu with numbers); optional `narrower` (same form as `parameters`). No other key; no free text. | Per flag id: a class from a fixed vocabulary (0006 CHECK) and a reason, text ≤ 300 characters, shown to people only (A7). | Plain text, at most N characters: the explanation, or the gap report's prose. |
| What code does | Builds the plan from `plan.default_plan` + the allowed parameters only (rules, eligibility rules, model, calibration, sufficiency never come from the model); `plan.validate`; checks plan scope = claim scope; tags available. Mismatch → run failed "domain mismatch" before the lock. Narrowing (code role) then decides; else `lock_rules`. | Writes `flag.critic_class`, `critic_reason`, `classified_at` (once, before the freeze; 0001 trigger). **No code decision reads them**: Inclusion, the freeze, Statistics, narrowing, completion get flags only through `flags_kind`/`set_flags`, which carry no class. | Stores the text as the Analyst stage's output only after both checks pass. It never sets outcome, verdict, label or level; `copy_decision` / `copy_partly_sufficient` copy code's stored decision. |
| What is checked | Schema (keys, vocabularies, types); `plan.validate` (template, fixed rules via `fixed_rule_problems`); scope = claim scope; tags approved; for `narrower`: strictly narrower, covers exactly the parts with records, valid. Complete-input and planted-value tests on the raw request bytes. | Class in vocabulary; flag id is in the input; one class per flag; planted outcome values and flag numbers absent from the raw request; a test that randomised classes leave every decision, set, fingerprint and result byte-identical. | Number check (every number in the text equals a number in `analyst_facts`/`coverage` at its shown precision; written for reuse by the Commentator); wording check (register list: "in the sources searched" with any outcome; never "do not exist"; no verdict word without a verdict; …). Below the minimums `analyst_facts` holds no estimate and nothing computed from outcomes (fixed-noise detection rate stays, structure only). Planted-value test at `narrowed`/`closed_without_freeze`. |

`analyst_facts` (code, from stored rows only): the stored decision (outcome, verdict, wordings, level,
label); per analysis: scope, source, counts, checks, inference reason, minimums, and — unless withheld —
estimate, SE, df, p, its description, per-source label, calibration shares; `gap_facts`; the plan's
scope, option, minimums, α. Never record-level values, record identities, Critic classes or reasons,
stage texts. At `narrowed`: claim scope, counts per part, the parts with zero, the narrower scope.

## Failure modes of a run (8a's request-path table applies to every call; this adds the run level)
| Failure | Outcome |
|---|---|
| Planner returns an invalid plan (schema, template, scope ≠ claim scope, tag not approved) | One corrective retry naming only the code (`invalid_plan`); second failure → stage failed, run **failed** `planner_invalid_plan`; no plan locked. |
| Planner tries to weaken a fixed rule | Impossible to take effect: its schema has no key for rules, eligibility rules, model, calibration or sufficiency; such a key is off-schema → as invalid plan. Second line: `validate` → `fixed_rule_problems`; third: `lock_rules` re-validates; the database never changes a locked plan. |
| Planner's narrower plan not strictly narrower, not exactly the parts with records, or invalid | Narrowing declined by code (reason code stored in the `narrowing` stage output, logged); no retry; the original goes on to the lock with its own plan. |
| No part has zero records, or a part has zero but the Planner proposed no narrower plan | Original goes on to the lock (likely ends insufficient with a gap report). |
| Planner says the claim is another domain | Run **failed** "domain mismatch" before the lock (PRD 5.5). |
| Planner call fails (provider, auth, refusal, unknown cost, malformed twice) | Run **failed** with the code; no plan. |
| Cap reached at the Planner or the Critic (run $2, month $50, live-set ceiling) | Nothing sent; stage failed; run **failed** with the cap's code (PRD 8, 14.4); stored rows stay; re-dispatch is a new run. |
| Cap reached at the Analyst (code's decision already stored) | Nothing sent; stage failed; run **completes** with code's decision, "explanation unavailable (spending cap)" (A3). |
| Critic answer off-schema for a flag | That flag stays unclassified with its refusal code; others stand; no retry. |
| Critic call fails (malformed twice, provider, refusal…) | Stage failed; every flag unclassified ("not classified: <code>"); run continues (no decision reads the class). |
| Analyst text fails the number or wording check twice | Text discarded (not stored as the report); stage failed `numbers_unmatched` / `wording_refused`; the run completes with code's decision and gap facts; shown as "explanation unavailable (<code>)". |
| A model call fails after the freeze (only the Analyst) | As above: run completes with code's decision; explanation unavailable. |
| A call's recording fails (`recording_failed`) | The call stays started; the database refuses to end the run while a call is open, so the run stays running; the command exits non-zero; recovery is step 9. |
| A checkpoint or write refuses (`changed_since_read`, `invariant_broken`, database refusal) | Logged (as today); run **failed** with the code. |
| Narrower question dispatched with a source version different from those the narrowing counts were taken on (B1) | Refused before the lock with a stated reason (code `narrowing_sources_changed`, naming the source); logged; run failed; no plan locked. Tested. |
| Analyst fails for any reason on the partly-sufficient path (checks twice, provider, refusal, cap) (B2) | Run still completes as partly sufficient (level 1) with "explanation unavailable (<code>)"; the narrower question is still created and linked. Tested. (`recording_failed` remains the exception: the open call blocks completion until step 9.) |
| Source unreadable | `failed_search` for that source (existing); run continues. |
| Unsupported domain | Dispatch refused by the database with its message; no run. |
| Process dies | Stages/calls left open; step 9. |

## The run's stages, in order
| # | Stage | Kind | Model call | Checkpoint |
|---|---|---|---|---|
| 1 | Dispatch (queries.py): version dispatched, run queued, run_source, run_agent_setting | code | – | |
| 2 | Start (run → running) | code | – | |
| 3 | Planner (skipped for a fixed-plan run, 14.1a) | agent | **yes** | |
| 4 | Narrowing decision (`narrowing`, `candidate_counts`, structure only) | code | – | before any lock |
| 4p | Partly: Analyst at `narrowed` → `copy_partly_sufficient` (completes, level 1) → narrower question created as submitted, linked; **stop** | agent, code | **yes** (Analyst) | no lock ever |
| 5 | **Rules lock** (`lock_rules`) | code | – | **checkpoint 1** |
| 6 | Store records (`store_records`) | code | – | |
| 7 | Checks (`run_checks`) | code | – | |
| 8 | Critic | agent | **yes** | |
| 9 | Inclusion (`decide_run`) | code | – | |
| 10 | **Dataset freeze** (`freeze_dataset`) | code | – | **checkpoint 2** |
| 11 | Statistics (`run_statistics`) | code | – | |
| 12 | Analyst (explanation or gap report) | agent | **yes** | |
| 13 | Completion (`copy_decision`) | code | – | |

No model call inside a database transaction: an agent stage is (a) one short transaction under the run
lock that writes the running stage result and its invocation, commit; (b) the access read (its own
transaction); (c) `spend.reserve` (own transaction, committed); (d) the HTTP request with no
transaction open (tested with `pg_stat_activity` as in 8a, now for each of the three roles);
(e) `spend.finish` (own transaction); (f) one locked transaction writing the output and closing the
stage. The whole run executes in a guarded child process (`run_guarded`), like the curation.

## Migration 0006 (0001–0005 untouched)
- `flag.critic_class` vocabulary CHECK (and `critic_reason` bound or vocabulary, per answer).
- Proposed (owner to decide): `hypothesis_version.sufficiency_option` (default 'fixed_minimum', fixed
  after submission by its own trigger; the plan's option must equal it at the lock).
- Proposed strengthening (owner to decide): a new trigger on `run` (not replacing 0001's function):
  outcome 'partly_sufficient' only with no plan, no record, and a done `narrowing` stage result; and a
  new trigger on `plan`: no plan after such a decision.
- Trigger change needed to complete with no plan: **none**.
Tested up/down/up, previous release's code unaffected, downgrade refuses while used.

## Live test set (owner's go first; ceiling $2 on reserved maximum; prices re-checked first)
| # | Run | Calls | Estimate (actual) |
|---|---|---|---|
| A | 14.1b: FCC claim, both sources, live Planner | Planner, Critic, Analyst | ~$0.30 |
| B | 14.3: BCC at 1000 °C, both sources | Planner, Critic, Analyst (gap report) | ~$0.25 |
| C | Partly: FCC tension at room and cryogenic temperature | Planner, Analyst (narrowing facts) | ~$0.12 |
| D | `dispatch` of C's narrower question (locks the stored plan, A8) | Critic, Analyst | ~$0.20 |
| | **Total** (owner A10: all four) | ~10 calls | **~$0.85 expected** |
Ceiling: each run gets `--ceiling` = $2 − actual cost of the set's earlier runs (read from `model_call`),
so reserved maximum + actual never passes $2; no change to `spend.py`. A call stuck at 'started'
counts at its maximum. Live tests live in `tests/live/`, marked `live`, skipped unless asked for.
Per-call basis: Opus $4/$20, Haiku $1/$5 per million tokens; Planner ~6k in / ≤4k out; Critic ~20–40k in
/ ~3k out; Analyst ~10–20k in / ~4k out.

## Files (8b)
`pipeline/queries.py` (new), `pipeline/narrowing.py` (new), `pipeline/orchestrator.py` (new),
`pipeline/completion.py` (`copy_partly_sufficient`), `pipeline/agents/{planner,critic,analyst,checks_text}.py`,
`pipeline/agents/settings.py` (three roles), `pipeline/agents/lm.py` (new codes), `access/allowlist.py`
(Analyst lists, `narrowed`, `narrowing`), `access/fields.py` (`analyst_facts`, `candidate_counts`),
`access/stage.py`, `pipeline/statistics.py` (named constant for the partly level wording),
`db/migrations/versions/0006_*.py`, `db/models.py`, `cli.py` (`run`, `show`, `dispatch`),
`assumptions.json`, tests (stub provider recordings per role; no live calls), `tests/live/` (marked, skipped by default),
`docs/reviews/step08b_summary.md`, packet.

## Owner's answers (8b planning, 2026-10-07)
- **A1 Run order (partly sufficient):** narrowing decision → Analyst (narrowing facts only, run still
  running) → `copy_partly_sufficient` completes the run at level 1 → narrower question created as
  submitted and linked. No 0001 trigger touched. (Corrects the order in radiant-hugging-trinket.md.)

- **A2 Sufficiency option:** migration 0006 adds `hypothesis_version.sufficiency_option` (default
  'fixed_minimum'), changeable only while a draft (own trigger); code fills the plan's option from it;
  a new plan trigger refuses a plan whose option differs. CLI `run --sufficiency use_available`. A
  narrower question copies its original's option. Register entry for the default.

- **A3 Cap reached at the Analyst:** after the freeze (and, by the same reasoning, at `narrowed` and
  `closed_without_freeze`, where code's decision is already stored), a cap refusal is treated like any
  other Analyst failure: the run completes with code's decision, "explanation unavailable (spending
  cap)". Before the freeze (Planner, Critic) a cap refusal still fails the run (PRD 8, 14.4). Departs
  from PRD 14.4's "marked failed" for this case → PRD corrections list in the 8b summary; register entry.

- **A4 New stage `narrowed`:** `actual_stage` returns 'narrowed' for a running run with no plan and a
  done narrowing decision of partly sufficient. The Analyst is allowed only there (narrowing facts
  only); the Planner gets nothing there; `lock_rules` needs 'before_lock', so no plan is locked after a
  narrowing. Safeguard change (STAGES, allow-lists; register `access_allow_lists` reworded, history kept).

- **A5 0006 guards:** two new trigger functions with their own triggers (0001's untouched): a run
  completes as 'partly_sufficient' only with no plan, no stored record and a done 'narrowing' stage
  result; no plan is inserted for a run with such a narrowing decision. Tested against direct SQL,
  mutation checks.

- **A6 Commentator's lists (owner's own answer, verbatim):** "Empty the Commentator's lists for now: it
  may read nothing at any stage until step 12, when the role is built and its lists are decided and
  reviewed. Record the current sets in the register entry as the starting point for step 12. Test that a
  Commentator binding reads nothing, and list any test that changes because of this."
  Tests expected to change (listed in the summary, none removed or weakened; each re-pointed to the new
  premise): `test_access_layer.py` (role/stage table line 62; lines 76, 79, 96;
  `test_completion_without_a_freeze_moves_access_to_the_commentator_only`,
  `test_completion_after_a_freeze_moves_access_to_the_commentator_only`,
  `test_the_commentator_without_a_freeze_gets_the_gap_report_input_the_report_and_the_outcome`),
  `test_access_projected.py::test_no_projected_planted_value_in_the_commentators_input_without_a_freeze`,
  and any register test pinning `access_allow_lists`. Also to check: `ACCEPTED_DISCLOSURES` item "the
  Analyst's gap report, passed to the Commentator" no longer occurs until step 12 (note in the register,
  tuple wording to be shown to the owner before changing).

- **A7 Critic's answer:** class from the fixed list (0006 CHECK; register vocabulary): 'same measurement
  reported twice', 'different specimens or conditions', 'possible transcription or unit error', 'cannot
  tell from the metadata'. Reason: short text ≤ 300 characters (0006 bound), stored in
  `flag.critic_reason`, shown to people only; given to no agent (left out of `analyst_facts`; the
  Commentator reads nothing until step 12) and read by no code decision.

- **A8 Narrower question's plan:** its run locks exactly the narrower plan stored by the narrowing
  decision (Planner bypassed; `run.fixed_plan` true, shown as "plan from the narrowing decision" because
  the hypothesis has `narrower_of_run_id`). Lock refused if the fingerprint differs. Since a plan names its
  hypothesis version, the decision stores the narrower plan without that key and its fingerprint is
  taken over the plan less `hypothesis_version`; the narrower run adds its own version id and checks the
  rest byte-for-byte. The orchestrator (trusted code, not an agent field) reads it; single-run scope of
  the access layer is unchanged. Question text built by code: original claim + "narrower question:
  <scope in words>" (template a named constant, register entry).

- **A9 Reviewer at the command line:** `run` and `dispatch` require `--by "<name>"`; the name and
  "confirmed at the command line" go into `review_comment` with the database's time. `--domain` defaults
  to grain-size strengthening; an unsupported domain is refused by the database with its message (14.3).

- **A10 Live set:** A, B, C, D (~$0.85 expected, $2 ceiling on reserved maximum), each only after the
  owner's separate go; prices re-checked against Anthropic's page first (stop if they differ).

## Design details (from the answers)
- **Narrowing (code role `narrowing`, field `candidate_counts`, stage `before_lock`).** Read from the
  sealed versions through the adapters (records are not stored before the lock), like `record_counts`.
  Claim parts: each phase class, each band (with its range), each test type of the Planner's claim
  scope (alloy class is not countable, Q5). A part's count = records with grain size and the plan's
  outcome at an accepted status that fall in that part **and** in the claim's values on the other
  dimensions, judged by the same scope functions as eligibility (rule 3 for temperature). Counts and
  statuses only; no outcome value is read beyond its status. Decision stored as a code stage
  `narrowing`: counts fingerprint, claim scope, zero parts, narrower plan (less `hypothesis_version`)
  and its fingerprint, the source version ids and fingerprints the counts were taken on (B1), result
  `partly_sufficient` or `proceed` with a reason code.
- **`copy_partly_sufficient`** (`completion.py`): only copies; checks the narrowing stage's fingerprints
  against what it re-reads; outcome 'partly_sufficient', no verdict, level 1, wording from a named
  constant "original question not tested; a narrower question was proposed" (owner's addition 1;
  `evidence_level_scale` reworded, history kept).
- **Narrower question** (`queries.create_narrower`): hypothesis with `narrower_of_run_id`, version
  submitted (domain and sufficiency option of the original, same sources), text from the code template.
- **Critic batching:** one call per run with every flag; the request renders only flagged records'
  metadata; above a named maximum of flags per call, split into several calls (each its own invocation).
- **Analyst checks** in `pipeline/agents/text_checks.py` (number check written for reuse by the
  Commentator; wording list in the register, drafted for the owner's review). New failure codes
  `numbers_unmatched`, `wording_refused` (action "correct") in `lm.FAILURES` (register
  `request_failure_policy` reworded).
- **Instructions and limits** for the Planner, Critic and Analyst: drafted by Claude Code, entered in the
  register as drafts for the owner's review (as the Curator's were in 8a).

## Safeguard changes in 8b (second-model review before any merge)
Allow-lists (Analyst's new lists, stage `narrowed`, Commentator emptied, code role `narrowing`); the new
field readers `analyst_facts` and `candidate_counts`; `access/stage.py`; migration 0006; the
partly-sufficient copy path; the Planner's parameter schema and plan building; the Analyst's text checks.

## Sequence of work (push the branch at each milestone; progress note at each)
1. Branch `step-08b-agents` from `main`; plan checklist; harness folder. Migration 0006 with failing
   tests first (sufficiency column and trigger, plan-option trigger, partly-sufficient triggers, Critic
   vocabulary and bound; up/down/up; previous release's code). *M1*
2. Access layer: `narrowed`, Analyst lists, Commentator emptied, `narrowing` role, `analyst_facts`,
   `candidate_counts`; planted-value tests for the Analyst at `narrowed` and `closed_without_freeze`,
   below-minimum test (no estimate, nothing from outcomes). *M2*
3. `queries.py` (create, submit, confirm with `--by`, dispatch, narrower question). *M3*
4. Planner (schema, plan building, checks, narrower proposal) + narrowing + `copy_partly_sufficient`. *M4*
5. Critic (vocabulary, batching, write once) + the "no decision reads the class" test (randomised
   classes → byte-identical sets, fingerprints, results). *M5*
6. Analyst (facts rendering, number and wording checks, fallback). *M6*
7. Orchestrator (stage order above, every failure-table row, no transaction during a request per role)
   and `run`/`show`/`dispatch` in the guarded process; 14.1a from the command line reproduces the
   approved reference numbers; 14.3 bullets from the command line with recorded responses. *M7*
8. Register (new and reworded entries, all with tests); full suite locally and in the image; mutation
   checks per safeguard; reference results byte-compared with `main`. *M8*
9. Show the drafts (B3: Analyst wording list; instruction text and limits of the Planner, Critic,
   Analyst); price check; then **stop and ask** for the go on the live set (A–D). After run A, report
   field by field whether the Planner's plan equals the reference plan; if it differs, report and
   **stop** (B4; never adjust instructions to match without telling the owner). Report actual costs. *M9*
10. Summary, review packet, push, stop. Do not merge.

## Verification
- Whole suite passes locally and in the rebuilt test image; no live call (the stub provider; a test
  that fails if any request leaves for a non-local host).
- Recorded-response tests for every row of the run failure table and every stage of the order.
- 14.1a: `hypocurate run "<claim>" --sources mpea,tamu_fcc --fixed-plan --by …` gives the approved
  reference numbers (CLAUDE.md) and the same freeze fingerprint on a repeat; `show` prints them.
- 14.3: BCC at 1000 °C → insufficient, no freeze, missing field grain size, missing evidence; fixed vs
  use-available on below-minimum data (exploratory vs insufficient); a validity failure gives no verdict
  under either; partly sufficient original + linked narrower question with its own plan and verdict;
  unreadable source → failed search; unsupported domain refused with the message.
- Mutation checks for each safeguard (scratch copy, `PYTHONPATH`), all reported.
- Live set A–D after the owner's go; costs reported against the estimate.

## Progress checklist (8b)
- [x] M1 Migration 0006 — commit 27bd22b, pushed; suite 1,530; new tests 38 (37 failed on main with
      scaffolding; up/down/up passes there). Harness ~/hc-work/step08b/ (pt.sh, main/ = main's package + scaffolding).
- [x] M3 queries.py — see git log (step 8b M3)
- [x] M4 Planner, narrowing, copy — 82aab3c
- [x] M5 Critic — 628f7a6
- [x] M6 Analyst — 8754b82
- [x] M7 Orchestrator, CLI, 14.1/14.3 — 0336041 (A12 scipy preloaded; A13; nothing-found kinds by code)
- [x] M8 — 9bbd70f; suite 1,679 local + test image; guard checks pass in runtime image; reference runs byte-identical to main; d01-d05 caught; prices match the page (read 2026-10-07)
- [x] M9 Drafts (B3), price check, live set A–D, B4 report, Analyst rework (A14, A15) and live checks; 12 live runs, $1.0278 actual
- [x] M10 Summary, packet, push; suite 1,728 passed locally; 26 mutations caught, control clean; reference runs identical to main. Stopped: not merged; awaiting the second-model review.

## Owner's answers during the build (2026-10-07)
- **M2 disclosures:** remove "the Analyst's gap report, passed to the Commentator" and "condition summaries ..."
  from ACCEPTED_DISCLOSURES until step 12 (history kept). Done.
- **A11 Claim that is not one plan:** a claim scope with more than one temperature band, where no part has
  zero records, fails the run before the lock: code `claim_not_one_plan`, reason "the claim covers more than
  one temperature band; submit one question per band". If a band has zero records, the partly-sufficient
  path applies as usual.
- [x] M2 Access layer — commit 7c9e5be, pushed; suite 1,547.
- **A12 PRELOADED (owner, 2026-10-07, M7 stop):** add scipy: PRELOADED = ("psycopg", "scipy"). Cause: importing
  scipy makes a ctypes foreign call at load (scipy/_lib/_ccallback_c.pyx:208), refused by the guard. Safeguard
  change, reviewed with 8b. Found on the probe: a run without the stub reached litellm's local missing-key
  refusal (no request left the machine); M7 adds a suite-wide safeguard against any non-local request.
- **A11 extended by Claude Code (to tell the owner):** a claim with more than one test type or alloy class is
  treated like two bands (claim_not_one_plan), since a plan's tags allow one of each.
- **A13 (owner, 2026-10-07):** after the check (no production module imports statsmodels or pandas; pandas only
  via dspy in the runtime lock; the zone read came from Claude Code's probe action listing statsmodels.api):
  scipy stays preloaded, no pandas change, probe action imports production modules only with a test that
  statsmodels/pandas/patsy are not loaded; **also run the guard tests inside the rebuilt runtime image at M8**.
- **Live Analyst check (2026-10-07):** refused (wording_refused, then numbers_unmatched); $0.1779; live total $0.756.
- **A14 (owner, 2026-10-07): placeholders + fewer facts + stated/defaulted in one change.** The Analyst writes no
  digits: {name} placeholders replaced by code (display strings, phrases); checks: unknown name, digit outside a
  placeholder (new codes, counts only), outcome/verdict wording placeholders required; other wording rules on the
  finished text. Facts: decision, pooled, per-source with labels, counts vs minimums, both calibrations, sensitivity
  summary by code (count per per-source label via the same function st.label; names of sets not 'agrees'; smallest and
  largest estimate with set names; the result without the largest-share group). Planner marks each scope part stated
  or defaulted; code checks; narrowing and Analyst facts carry it. Safeguard changes for the review. Full suite, then
  the estimated cost of one live check; no live call without the owner's go.
- **Live checks round 2 (2026-10-07):** 3/3 passed (2 first time, 1 after correction); $0.150; live total $0.984.
- **A15 (owner, 2026-10-07):** store failure facts for corrected attempts; code-built: calibration summary sentence
  (both flags), direction note (estimate's sign vs the claim's direction), fixed-plan sentence; instruction: no
  conclusions beyond the facts and notes. Plus: units on estimate/SE/scatter/shift/temperature (coefficient MPa·µm^0.5);
  a model sentence; instruction: open by restating the claim, then outcome and verdict, then main cautions (2–3
  sentences), not with the query number; nominal level as a percentage; simulation-interval phrase; plain calibration
  names (estimated from the data / fixed illustrative); plain label wording; "groups" consistently + one group
  definition. Recorded-response tests, full suite, one live check (~$0.04), then M10 (summary lists the three
  interpretation findings, says checks cover numbers and wording not interpretation, Critic not exercised live).
```
### `~/hc-work/step08b/live_set.py`

```python
"""The step 8b live test set (owner's answers A10, B3, B4): runs A, B, C, D through the command line on the local
development database, each with --ceiling = $2 minus the actual cost of the set's earlier runs. Stops after run A
if the Planner's locked plan differs from the reference plan in any field (B4), reporting each difference.

Run only after the owner's go, with ANTHROPIC_API_KEY exported from .env without printing it. Scratch harness, not
committed; quoted in the review packet."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from decimal import Decimal

from sqlalchemy import create_engine, text

REPO = "/workspaces/hypocurate"
SET_CEILING = Decimal("2")
CLAIMS = {
    "A": ("In FCC multi-principal-element alloys, yield strength rises as grain size falls", "mpea,tamu_fcc"),
    "B": ("Grain refinement still strengthens BCC multi-principal-element alloys at 1000 °C", "mpea,tamu_fcc"),
    "C": ("In FCC multi-principal-element alloys tested in tension, yield strength rises as grain size falls, both at "
          "room temperature and at cryogenic temperatures (-196 °C)", "mpea,tamu_fcc"),
}
BY = "Khalid El-Awady (live set, run by Claude Code on the owner's go)"
engine = create_engine(os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1))
runs: dict[str, int] = {}


def spent() -> Decimal:
    """Everything the set has cost: every model call in this (local development) database, which holds only the
    set's calls (reported cost, or the reserved maximum where none is known)."""
    with engine.connect() as conn:
        return Decimal(conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call")).scalar())


def hc(*args) -> tuple[int, str, str]:
    done = subprocess.run([sys.executable, "-m", "hypocurate.cli", *args], cwd=REPO, capture_output=True, text=True)
    return done.returncode, done.stdout, done.stderr


def ceiling() -> str:
    left = SET_CEILING - spent()
    if left <= Decimal("0.05"):
        sys.exit(f"STOP: the set's remaining ceiling is {left}")
    return str(left)


def run(label, *args):
    code, out, err = hc(*args, "--ceiling", ceiling())
    first = json.loads(out.split("\n", 1)[0]) if out.strip() else {}
    runs[label] = first.get("run")
    print(f"=== {label}: exit {code}; run {runs[label]}; query {first.get('query')}")
    if err.strip():
        print("stderr:", err.strip()[-500:])
    print(out.split("\n", 1)[1] if "\n" in out else out)
    return code, json.loads(out.split("\n", 1)[1]) if "\n" in out.strip() else {}


def costs(run_id):
    with engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(
            "SELECT role, model, status, input_tokens, output_tokens, cost, max_cost FROM model_call WHERE run_id = :r "
            "ORDER BY id"), dict(r=run_id)).all()]


def diff(a, b, path="plan"):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            out += diff(a.get(k, "<missing>"), b.get(k, "<missing>"), f"{path}.{k}")
        return out
    return [] if a == b else [f"{path}: Planner {json.dumps(a)} | reference {json.dumps(b)}"]


def rerun_c_and_d():
    """After the owner's decision (code builds the narrower scope): run C again, then D."""
    print(f"spent before: ${spent()}")
    _, report = run("C2", "run", CLAIMS["C"][0], "--sources", CLAIMS["C"][1], "--by", BY)
    print("costs C2:", json.dumps(costs(runs["C2"]), default=str))
    narrower = report.get("narrower_question")
    if not narrower:
        sys.exit("STOP: run C created no narrower question")
    run("D", "dispatch", narrower, "--by", BY)
    print("costs D:", json.dumps(costs(runs["D"]), default=str))
    print(f"TOTAL for the set (actual, or reserved where unknown): ${spent()}; runs {runs}")


def main():
    if sys.argv[1:] == ["c_and_d"]:
        return rerun_c_and_d()
    sys.path.insert(0, REPO)
    from hypocurate.pipeline.plan import reference_plan
    _, report = run("A", "run", CLAIMS["A"][0], "--sources", CLAIMS["A"][1], "--by", BY)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT p.content, r.hypothesis_version_id FROM plan p JOIN run r ON r.id = p.run_id "
                                "WHERE p.run_id = :r"), dict(r=runs["A"])).one_or_none()
    print("costs A:", json.dumps(costs(runs["A"]), default=str))
    if row is None:
        sys.exit("STOP (B4): run A locked no plan")
    ref = reference_plan(row.hypothesis_version_id)
    fields = sorted(set(ref) | set(row.content))
    differences = diff(row.content, ref)
    print("B4 field by field:")
    for f in fields:
        sub = [d for d in differences if d.startswith(f"plan.{f}")]
        print(f"  {f}: {'equal' if not sub else 'DIFFERS'}")
        for d in sub:
            print("     ", d)
    if differences:
        sys.exit("STOP (B4): the Planner's plan differs from the reference plan; reported above")
    for label in ("B", "C"):
        _, report = run(label, "run", CLAIMS[label][0], "--sources", CLAIMS[label][1], "--by", BY)
        print(f"costs {label}:", json.dumps(costs(runs[label]), default=str))
        if label == "C":
            narrower = report.get("narrower_question")
    if not narrower:
        sys.exit("STOP: run C created no narrower question")
    run("D", "dispatch", narrower, "--by", BY)
    print("costs D:", json.dumps(costs(runs["D"]), default=str))
    print(f"TOTAL actual (or reserved, for any call without a cost): ${spent()}; runs {runs}")


if __name__ == "__main__":
    main()
```
### `~/hc-work/step08b/diag/live_check.py`

```python
"""The one live Analyst check (owner's go, 2026-10-07): a fixed-plan run of the FCC claim on the local development
database, capped at $1.00, through the normal pipeline (two attempts at most). Scratch harness; not committed."""
import json, os, sys
from decimal import Decimal
sys.path.insert(0, "/workspaces/hypocurate")
from sqlalchemy import text
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import orchestrator, queries

engine = make_engine(os.environ["DATABASE_URL"])
q = queries.create(engine, "In FCC multi-principal-element alloys, yield strength rises as grain size falls", ("mpea", "tamu_fcc"))
queries.submit(engine, q.version_id)
queries.confirm_domain(engine, q.version_id, by="Khalid El-Awady (live Analyst check, run by Claude Code on the owner's go)")
rid = queries.dispatch(engine, q.version_id, fixed_plan=True)
report = orchestrator.run(engine, rid, ceiling=Decimal("0.20"))
with engine.connect() as conn:
    stage = conn.execute(text("SELECT status, output FROM stage_result WHERE run_id = :r AND stage = 'analyst'"), dict(r=rid)).one()
    calls = [dict(r._mapping) for r in conn.execute(text("SELECT role, model, status, input_tokens, output_tokens, cost, max_cost FROM model_call WHERE run_id = :r ORDER BY id"), dict(r=rid))]
print(json.dumps({"query": q.number, "run": rid, "status": report.status, "outcome": report.outcome,
                  "analyst_stage": stage.status, "attempts": stage.output.get("attempts"),
                  "failure_details": stage.output.get("failure_details"), "calls": calls}, default=str, indent=1))
print("=== EXPLANATION ===")
print(stage.output.get("report") or stage.output.get("shown"))
print("=== TEMPLATE ===")
print(stage.output.get("template"))
```
### `~/hc-work/step08b/diag/live_check3.py`

```python
"""Three live Analyst checks (owner's go, 2026-10-07): three fixed-plan runs of the FCC claim, one after another, on the
local development database; $0.50 in total (each run's ceiling = $0.50 minus what the earlier ones cost). Stops if a
run's Analyst is refused twice. Scratch harness; not committed."""
import json, os, sys
from decimal import Decimal
sys.path.insert(0, "/workspaces/hypocurate")
from sqlalchemy import text
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import orchestrator, queries

TOTAL = Decimal("0.50") - Decimal("0.078396")  # what is left of the $0.50 after check 1 of the first round
engine = make_engine(os.environ["DATABASE_URL"])
spent, shown = Decimal(0), False
for i in (1, 2, 3):
    q = queries.create(engine, "In FCC multi-principal-element alloys, yield strength rises as grain size falls",
                       ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Khalid El-Awady (live Analyst check, run by Claude Code on the owner's go)")
    rid = queries.dispatch(engine, q.version_id, fixed_plan=True)
    report = orchestrator.run(engine, rid, ceiling=TOTAL - spent)
    with engine.connect() as conn:
        st = conn.execute(text("SELECT status, output FROM stage_result WHERE run_id = :r AND stage = 'analyst'"), dict(r=rid)).one()
        calls = [dict(r._mapping) for r in conn.execute(text("SELECT input_tokens, output_tokens, cost, max_cost FROM model_call "
                                                              "WHERE run_id = :r ORDER BY id"), dict(r=rid))]
    run_cost = sum(Decimal(str(c["cost"] if c["cost"] is not None else c["max_cost"])) for c in calls)
    spent += run_cost
    print(json.dumps({"check": i, "query": q.number, "run": rid, "outcome": report.outcome, "analyst": st.status,
                      "attempts": st.output.get("attempts"), "failure_details": st.output.get("failure_details"),
                      "calls": calls, "run_cost": str(run_cost), "spent_so_far": str(spent)}, default=str, indent=1))
    if st.status == "done" and not shown:
        shown = True
        print("=== TEMPLATE ===\n" + st.output["template"] + "\n=== FINISHED TEXT ===\n" + st.output["report"] + "\n=== END ===")
    if st.status != "done":
        print(f"STOP: check {i} refused twice ({st.output.get('code')})")
        break
```
### `~/hc-work/step08b/diag/diagnose.py`

```python
"""One diagnostic Analyst call (owner's go, 2026-10-07): a fixed-plan run of the FCC claim on the local development
database, the Analyst limited to one attempt, the raw answer written to a local scratch file only. Every call is
reserved and recorded as usual (RecordedEngine). Scratch harness; not committed."""
import json, os, sys
from decimal import Decimal
sys.path.insert(0, "/workspaces/hypocurate")
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import orchestrator, queries
from hypocurate.pipeline.agents import interface
import dspy.adapters.chat_adapter as ca

RAW = os.path.expanduser("~/hc-work/step08b/diag/analyst_raw.txt")
original_parse = ca.ChatAdapter.parse
def capture(self, signature, completion):
    if "report" in signature.output_fields:
        with open(RAW, "a") as f:
            f.write("=== RAW ANSWER ===\n" + completion + "\n=== END ===\n")
    return original_parse(self, signature, completion)
ca.ChatAdapter.parse = capture
interface.MAX_ATTEMPTS = 1  # exactly one Analyst call

engine = make_engine(os.environ["DATABASE_URL"])
q = queries.create(engine, "In FCC multi-principal-element alloys, yield strength rises as grain size falls", ("mpea", "tamu_fcc"))
queries.submit(engine, q.version_id)
queries.confirm_domain(engine, q.version_id, by="Khalid El-Awady (diagnostic, run by Claude Code on the owner's go)")
rid = queries.dispatch(engine, q.version_id, fixed_plan=True)
report = orchestrator.run(engine, rid, ceiling=Decimal("0.40"))
print(json.dumps(report.__dict__, default=str, indent=1))
```
### `~/hc-work/step08b/packet.py`

````python
"""Builds docs/reviews/step08b_review_packet.md from the files on disk (run from the repository root). Every diff and
output is quoted exactly. Scratch harness; quoted in the packet's last section."""
import json
import subprocess
from pathlib import Path

HOME = Path.home() / "hc-work/step08b"
BASE = "d76c86a"
OUT = Path("docs/reviews/step08b_review_packet.md")
PLAN = Path.home() / ".claude/plans/pasted-content-id-74d4-read-claude-md-replicated-iverson.md"


def sh(*cmd) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def fence(text: str, lang: str = "") -> str:
    ticks = "````" if "```" in text else "```"
    return f"{ticks}{lang}\n{text.rstrip()}\n{ticks}\n"


def read(path) -> str:
    return Path(path).read_text(encoding="utf-8")


head = sh("git", "rev-parse", "--short", "HEAD").strip()
parts = [f"""# Build step 8b — review packet

Date: 2026-10-07. Branch: `step-08b-agents`, from `main` at `{BASE}`. Head when generated: `{head}`. Generated from the
files on disk by a script (`~/hc-work/step08b/packet.py`, quoted in section 11), so every diff and output below is
quoted exactly.

## How to use this packet

Step 8b builds the Planner, the narrowing decision and the partly-sufficient path, the Critic, the Analyst, the
orchestrator and the command line's `run`, `dispatch` and `show`. It holds safeguard changes (listed at the top of the
summary), so please review against `docs/reviews/checklist.md` and answer the questions at the end of the summary.
Sections: 1 the summary; 2 the code diff; 3 the new test files; 4 the changed tests; 5 the register; 6 the reference
comparison with `main`; 7 the live calls; 8 the mutation checks; 9 new tests on `main`'s code; 10 the suite and the
images; 11 the plan file and the scripts.

"""]
parts.append("## 1. The summary\n\n" + read("docs/reviews/step08b_summary.md") + "\n")
diff = sh("git", "diff", f"{BASE}..HEAD", "--", "hypocurate", ":(exclude)hypocurate/assumptions.json")
parts.append(f"## 2. Code diff (`{BASE}..HEAD`, the package; the register is in section 5)\n\n" + fence(diff, "diff"))
new_tests = sh("git", "diff", "--name-only", "--diff-filter=A", f"{BASE}..HEAD", "--", "tests").split()
parts.append("## 3. New test files\n\n" + "".join(f"### `{p}`\n\n" + fence(read(p), "python") for p in new_tests))
changed = sh("git", "diff", "--name-only", "--diff-filter=M", f"{BASE}..HEAD", "--", "tests").split()
parts.append("## 4. Changed tests and test helpers (diff)\n\n" + fence(sh("git", "diff", f"{BASE}..HEAD", "--", *changed), "diff"))
reg_old = {e["key"]: e for e in json.loads(sh("git", "show", f"{BASE}:hypocurate/assumptions.json"))}
reg_new = {e["key"]: e for e in json.loads(read("hypocurate/assumptions.json"))}
added = [k for k in reg_new if k not in reg_old]
modified = [k for k in reg_new if k in reg_old and reg_new[k] != reg_old[k]]
reg = "".join(f"### New: `{k}`\n\n" + fence(json.dumps(reg_new[k], indent=1, ensure_ascii=False), "json") for k in added)
reg += "".join(f"### Changed: `{k}` (the entry as it now stands; earlier wording in its history)\n\n"
               + fence(json.dumps(reg_new[k], indent=1, ensure_ascii=False), "json") for k in modified)
parts.append(f"## 5. Assumptions register ({len(reg_new)} entries; {len(added)} new, {len(modified)} changed)\n\n" + reg)
parts.append("## 6. Reference comparison with `main`\n\nThe five reference runs of `test_reference_numbers.py`, dumped on "
             f"`main` (`{BASE}`, a separate worktree) and on this head; every decision (with its freeze fingerprint), "
             "every analysis (with its calibrations), the not-analysed list and the record counts compared:\n\n"
             + fence(read(HOME / "refdump/compare_final_output.txt")) + "\nThe comparison script:\n\n"
             + fence(read(HOME / "refdump/compare.py"), "python") + "\nThe dump test:\n\n"
             + fence(read(HOME / "refdump/test_zz_refdump.py"), "python"))
parts.append("## 7. The live calls (`docs/reviews/step08b_live_record.json`)\n\n"
             + fence(read("docs/reviews/step08b_live_record.json"), "json"))
parts.append("## 8. Mutation checks (all re-run on the final tests; a control run with no mutation last)\n\n"
             + fence(read(HOME / "mspec/final_mutations.log")) + "\nThe specification and the runner:\n\n"
             + fence(read(HOME / "mspec/mutations.py"), "python") + fence(read(HOME / "mspec/run_all.py"), "python"))
parts.append("## 9. New tests on `main`'s code\n\nMilestone 1, `tests/test_migrations_step8b.py` on `main`'s package with "
             "the vocabulary and model constants as scaffolding (the up/down/up test passes there: nothing above 0005 "
             "to round-trip):\n\n" + fence(read(HOME / "m1_failed_before.log")) +
             "\nMilestone 2: the 17 new access tests all failed on `main`'s package (which also lacks 0006). The tests "
             "of milestones 3 to 9 exercise modules that do not exist on `main` (`queries`, `narrowing`, `planner`, "
             "`critic`, `analyst`, `analyst_names`, `display`, `orchestrator`, `cli_runs`), so they fail there on import. "
             "Each change made after the live checks was tested against the code before it (the counts are in the "
             "commit messages).\n")
parts.append("## 10. The suite and the images\n\nThe whole suite on this head (locally):\n\n" + fence(read(HOME / "final_full.log"))
             + "\nThe test image at milestone 8 (rebuilt; the suite then had 1,679 tests):\n\n"
             + fence("\n".join(l for l in read(HOME / "image_suite.log").splitlines() if "passed" in l or "failed" in l or l.startswith("exit")))
             + "\nThe guard checks inside the runtime image (its own package; no pytest in the image):\n\n"
             + fence(read(HOME / "image_guard.log")) + fence(read(HOME / "imgcheck/guard_in_image.py"), "python"))
scripts = ["live_set.py", "diag/live_check.py", "diag/live_check3.py", "diag/diagnose.py", "packet.py"]
parts.append("## 11. The plan file and the scripts\n\n### The step 8b plan file (owner's answers and the checklist)\n\n"
             + fence(read(PLAN), "markdown")
             + "".join(f"### `~/hc-work/step08b/{s}`\n\n" + fence(read(HOME / s), "python") for s in scripts))
OUT.write_text("".join(parts), encoding="utf-8")
print(f"{OUT}: {OUT.stat().st_size} bytes; head {head}")
````
