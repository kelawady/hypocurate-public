# Build step 8b — summary for review

Date: 2026-10-07. Branch: `step-08b-agents` (from `main` at `d76c86a`). **Status: second-model review "not safe to merge"; fix round 1 built (next section); whole suite 1,829 locally and in the rebuilt test image; pushed; not merged** (owner's instruction: "When built: full suite, summary, review packet, push, and stop. Do not merge."). Plan, every owner answer and the progress checklist: the step 8b plan file (quoted in the packet, section 11).

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

## Fix round 1 (2026-10-07)

**Update.** ChatGPT reviewed the packet at `859e019` and found the step **not safe to merge**, with five findings (`docs/reviews/step08b_review_chatgpt.md`). This round fixes all five and applies the owner's two decisions (A: a results statement written by code; B: the Planner's reading). It also makes the owner's wording corrections and additions. Every change came with tests that failed on the code before it. The step is still **not merged**.

### What changed, by finding and decision

| Item | What was wrong | What changed | Commit |
|---|---|---|---|
| Finding 1 (high) | A narrower question dispatched with default arguments went through the Planner. It skipped the stored plan and the source-version check. | `dispatch` and the orchestrator take the narrower path from the question's link to its original (`narrower_of_run_id`), never from a flag. **Database backstop in 0006** (owner's answer F-Q1: amend 0006, which is unmerged): a narrower question's run must have `fixed_plan`, and its plan must equal the stored narrower plan on the source versions the counts were taken on. | `e266234` |
| Finding 2 (high) | Requests used the current settings, while the audit record named the settings recorded at dispatch. | `settings.recorded(engine, invocation)`. The Planner, the Critic (per batch), the Analyst and the Curator build their requests from the invocation's recorded version. | `e266234` |
| Finding 3 (high) | After a recording or reservation failure, the Critic sent its next batch and the orchestrator went on to the Analyst. | `lm.RUN_STOPS`. Either failure at any agent stops the run: no further request, nothing more written, no narrower question. The run stays running for step 9's recovery. | `423fd46` |
| "Tests" point | The Critic-failure test used data with no flags, so it never reached the Critic. | Replaced by a test on constructed data that raises flags (`tests/test_orchestrator_flagged.py`). | `423fd46` |
| Finding 5 (medium) | A list or object as the Critic's class (or as the Planner's rule name) raised `TypeError`. | Type is checked before membership. Wrong-type shapes at every position are tested for the Critic, Planner, Curator and Analyst (`tests/answer_shapes.py`). | `740f044` |
| Decision B | Claim interpretation was unchecked (review, "Claim interpretation"). | A part marked as defaulted must hold the profile's default (`DEFAULT_SCOPE`). Code writes "the question as tested", labelled "the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person", and stores it with the Planner's stage. `run`/`dispatch` print it beside the claim before the rules lock (prepare, then proceed). `show` prints it. | `54d6aa1` |
| Finding 4 (medium) and decision A | The Analyst's numerical guarantees were stronger than its checks: numbers written in words passed, and the informative-group count was exposed on its own. | **A results statement written by code** for every completed run (`pipeline/statement.py`, wording approved by the owner with changes, F-Q2). The Analyst's text is labelled "written by a language model; values inserted from the run record; narrative not verified". No rules about number words. `count_groups`/`met_groups` removed. | `395d948`, `e7f7c8b` |
| Owner's wording fixes | — | The p-value phrase reads "an approximate, nominal, one-sided p ≈ X" (no double brackets). "Not testable alone (too few groups)". The simulation interval is described once. "Alloys". The unused unitless `display.display()` is deleted. | `395d948` |
| Corrections | — | The Planner's temperature bounds do enter a rule. The narrowing counts are candidate records. Calibration describes the method, not this p-value's error. All three are corrected in this summary and the register. | `54d6aa1`, `395d948`, `e7f7c8b` |

### A design choice for the reviewer: the statement is rendered at display

The statement is **not stored as text**. It is rendered from the stored results whenever it is shown.

**Why:** a partly-sufficient statement names its narrower question. The database lets that question be created only after the original run is completed, and it accepts no new stage result on a completed run.

**The owner's conditions, all built and tested:**
- **Pure function:** `statement.facts` reads the stored rows into plain values. It strips the stored lists of record ids. `statement.render` is a pure function of those values and orders sources and sensitivity sets itself. Two runs of one version, with other records and other ids, give the same text, and shuffled stored lists give the same text.
- **Format version:** the format has a version, `statement.FORMAT_VERSION` (1), in one named place. The completing code records it on the run (`run.statement_format_version`, 0006). It can be set only in the update that completes the run, and never changed after. `show` gives the rendered and recorded versions.
- **Wording pinned:** a fixture of stored facts for each outcome kind (`tests/fixtures/statement_facts.json`) has its rendered text pinned per version. A wording change fails until the version is raised.

**What follows:**
- The numbers cannot change, because they come only from stored results.
- The wording follows the format version.
- A run completed by code that did not record a version (the previous release's, or the 12 live runs in the development database) shows "not recorded".

### Safeguard changes in this round (second-model review before any merge)

- Migration 0006, amended in place (unmerged; never applied to the live database):
  - `hc_run_narrower` and `hc_plan_narrower` (finding 1);
  - `run.statement_format_version` with `hc_run_statement_version`.
- **Narrower path:** `queries.dispatch` and the orchestrator recognise a narrower question by its link.
- **Recorded settings:** requests are built from the recorded settings version (all four roles).
- **Accounting failures:** recording or reservation failures stop the run (`RUN_STOPS`).
- **Answer checks:** the Critic and Planner check types before membership; the Planner's defaulted parts must hold the default.
- **Analyst's facts:** the informative-group count is no longer a name of its own.
- **Statement:** the results statement and the Analyst's label. The statement is outside the agents' path; it reads stored rows only.

### Tests whose expectation changed in this round, and why

No test was weakened, skipped or deleted except the one replaced, as listed. Fixture data changes are listed too.

| Test or helper | Change | Reason |
|---|---|---|
| `test_orchestrator.py::test_a_critic_failure_leaves_flags_unclassified_and_the_run_goes_on` | **Removed, replaced** by `test_orchestrator_flagged.py::test_a_critic_failure_on_flagged_data_leaves_every_flag_unclassified_and_the_run_completes` | On the reference data (no flags) it could pass without any Critic request (review, "Tests"). The replacement checks the Critic was asked, its stage failed, no flag is classified, and the run froze and completed. |
| `test_access_projected.py::test_the_planted_values_are_stored_everywhere_they_should_be` | The planted plan is now counted 2 times, plus exactly once for the main run (was 1) | The fixture's earlier run of the same narrower question must lock the same stored narrower plan (finding 1's backstop). |
| `test_access_layer.py::test_experiment_flags_relax_nothing` | Its extra run is inserted with `fixed_plan = true` | It is a narrower question's run; the database requires the flag (finding 1). No assertion changed. |
| `test_access_dispatch.py::test_a_rules_lock_committed_while_a_read_waits_closes_the_planner` | Its lock inserts the stored narrower plan (was `{}`). Parametrized with an ordinary run. | The new rule refused `{}`. This failed on GitHub for `423fd46` and `54d6aa1` because it was not in the files run before those pushes; the owner's rule 13 (whole suite before every push) followed. The ordinary-run case keeps the common path covered. |
| `test_cli_runs.py::test_14_3_partly_sufficient_and_the_narrower_question_from_the_command_line` | Plan label "from the narrowing decision" (was "fixed") | The wording of the owner's answer A8. |
| `test_cli_runs.py::report_of` (helper) | Reads the new line with the claim and the question as tested | Decision B prints it before the run goes on. |
| `test_cli_runs.py::test_14_1a_run_with_the_fixed_plan_and_show_it` | Explanation label is the new one | Decision A. |
| `test_analyst.py::test_the_facts_carry_display_strings_and_phrases` | **Renamed** `test_the_named_formatting_functions_give_the_display_strings_and_phrases`. Same values, built by the named functions. New p-value phrase. | The function it tested (`display.display`) is deleted by the owner's instruction. |
| `test_analyst.py::test_numbers_exactly_as_given_match`, `::test_the_sensitivity_sets_are_labelled_with_the_per_source_function` | New p-value phrase | Owner's wording fix (no double brackets). |
| `test_analyst.py::test_the_plain_label_for_a_single_group_source` | "not testable alone (too few groups)" | Owner's wording fix. |
| `test_analyst.py::test_no_fact_name_exposes_a_bare_p_value_or_an_individual_paper_figure` | Also asserts no name carries the informative-group count | It missed `count_groups` (finding 4). |
| `test_assumptions.py` `PARTLY` | Adds `question_as_tested` | Its confirmation by a person is step 10. |
| `test_migrations_step8b.py` trigger order | Adds the run-insert trigger | The new trigger must fire after 0001's. |
| `test_planner_narrowing.py::body`, `test_orchestrator.py::planner_body` (fixtures) | A scope part that differs from the default is marked as stated unless a test gives the marks | Decision B: a part marked defaulted must hold the default. |
| `model_builder.World` (`run`, `lock`, `partly`), `access_world` (`planted_plan`) | `fixed_plan` derived for a narrower question; plan content as given; the original stores a narrower plan and its counted sources | Finding 1's backstop. |
| `test_reading.py` (new this round) | Labels, "alloys" | The owner's F-Q2 changes after decision B. |

### Numbers

- **The whole suite** passes on the final code of this round: 1,829 tests (up from 1,728), locally and in the test image rebuilt on the same code (its package and `tests/` byte-identical to the repository's).
- **The runtime image**, rebuilt on the same code: every guard check passes; it holds no `tests/` or `docs/`. The build cache was cleared after the rebuild (owner's standing instruction).
- **Mutation checks:** 41 deliberate faults in the new safeguards and wording rules, plus a control run; results in the fix packet, section 6. Two faults survived the first run: f21 (`proceed` without the narrowing-decision condition) and f35 (the per-source lines in stored order: the order test used a run with an estimate, which lists no sources). A test case was added for each and both are caught; the control run is clean.
- **The reference runs** of `test_reference_numbers.py` are **byte-identical to `main`**: decisions with their freeze fingerprints, analyses with calibrations, the not-analysed list and record counts. Nothing changed.
- **One live Critic call** (owner's go; fresh scratch database; constructed data marked as such; ceiling $0.25): Haiku 4.5, 1,330 input and 833 output tokens, **$0.005495** (reserved maximum $0.045779). Two `invalid_value` flags were sent, each naming one record. The request held no compared value (code also checked it for each): only each flag's kind and category and its record's metadata (alloy, composition, paper DOI, categories, field statuses). Both entries were accepted (class 'different specimens or conditions'); none was refused; one attempt. A second run of the same version with no classes gave identical decisions, sets, freeze record and fingerprint, statistics and gap facts. Live spending is now $1.0333 (`docs/reviews/step08b_live_record.json`, `fix_round_1_critic_check`).

### Open

- The local development database is still at the earlier 0006 (the live Critic call ran on a fresh scratch database, by the owner's choice). Before it is used again it needs a backup and a migration back down and up to the amended 0006; its run rows are kept.
- The confirmation of the question as tested by a person is step 10 (the website).
- The Analyst's narrative is unverified by design; it is labelled as such.
- **The Critic's reasoning is not checked either.** In the live call each flag named one record (its own tensile strength below its yield strength), but the Critic compared the two flags with each other and chose 'different specimens or conditions'; for a single physically impossible record, 'possible transcription or unit error' fits. No decision reads the class (shown again by this call), and the class and reason are shown to people only, but code checks only the answer's form, not its reasoning.

## What the checks cover, and what they do not

The Analyst's checks cover **numbers and wording, not interpretation**. Every number in an explanation is written by code: the Analyst writes `{name}` placeholders and code renders them. Code also checks the wording rules (for example "in the sources searched", no causal language, no verdict where there is none). No check shows that the Analyst's sentences draw the right conclusions from the facts. The label stored with an explanation is "numbers written by code from the run record". It is not a statement that the explanation is verified.

**The Critic has not been exercised by a live call.** The real data (MPEA and Texas A&M) raise no flags, so every live run sent nothing to the Critic. The Critic is tested only with recorded responses through the local stub, including its complete outbound request and the test that no decision reads its class.

### Interpretation findings from the live explanations (owner's request)

From the first accepted live explanation (run 9), before the owner's last round of code-built sentences:

1. **A conclusion from one flag applied to both calibrations.** "In both cases the conclusion was that the method is over-confident" used only `{estimated_flag}`; the fixed-noise flag was never referenced. *Addressed:* code now gives one calibration summary covering both flags.
2. **A direction read by the Analyst.** "which points in the direction the claim describes" was the Analyst's own reading of a positive estimate. *Addressed:* code now gives a direction note built from the estimate's sign and the claim's direction (the plan's alternative).
3. **An inference about the scope.** "parts of the scope … were not stated by the claim itself" was inferred from the note that a fixed plan's scope was not read from the claim. *Addressed:* code now gives one complete sentence for a fixed-plan run.

The last live explanation (run 12, after those changes, passed on its first attempt) still contains two conclusions of its own, which the checks do not catch:

- "So the nominal p-value should be read as more favourable than it really is" is drawn from the calibration flag. *Correction (fix round 1):* the calibration describes how the method behaves on simulated data like these; it does not measure the error of this particular p-value. No fact or instruction says otherwise, and the statement code now writes says so explicitly.
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
  - Code builds the narrower scope (the Planner cannot see which part has no candidate record).
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
| Spending cap or any other failure at the Analyst, except a recording or reservation failure | Run completes with code's decision; "explanation unavailable (<code>)"; on the partly path the narrower question is still created (B2) |
| Critic answer off-form for a flag / whole call failed | That flag, or the batch's flags, left unclassified; run goes on |
| Narrower question on other source versions (B1) | Refused before the lock (`narrowing_sources_changed`) |
| A refused checkpoint or write | Run fails with the code |
| A recording or reservation failure at any agent (fix round 1, finding 3) | The run stops at once: no further model request (no further Critic batch, no Analyst), no copy of the decision, no narrower question; the run stays running (a call whose recording failed stays started) for step 9's recovery |

## The agents

**Planner** (Opus 5.5):
- **Receives** the claim, domain, sources, approved tag values and record counts. Never an outcome value: the planted-value test runs on the raw request.
- **Answers** in a fixed form: domain match, claim scope, a stated/defaulted mark per scope part, outcome, exclusion rules from the menu, and a narrower scope that should be null.
- **Code** builds the plan from the profile's defaults and these parameters only. *Correction (fix round 1):* the Planner's temperature bounds do enter a rule: for a band other than room temperature they become the plan's temperature-range rule. Its scope and exclusion rules decide which records are eligible. The model, the eligibility rules, the calibration and the sufficiency option never come from it. Live run A's plan equals the reference plan in every field (B4).

**Narrowing** (code):
- Counts records per claim part with a grain size and the outcome at an accepted status. The counts come from the sealed versions, structure only. *Correction (fix round 1):* these are candidate records; they do not show that records will survive eligibility under the locked rules, nor that a narrower question will meet the minimums.
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

- **The whole suite passes:** 1,728 locally at M10. The test image was then rebuilt on the final M10 code (859e019) and ran 1,728, all passing; the runtime image's guard checks passed on the same code. The first rebuild failed on a corrupted Docker build cache ("parent snapshot … does not exist"); `docker builder prune -af` cleared it before the rebuild. (Fix round 1's numbers are in its own section.)
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
