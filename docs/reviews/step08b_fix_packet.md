# Build step 8b — fix packet, round 1

Date: 2026-10-07. Branch: `step-08b-agents`. Reviewed head: `859e019` (ChatGPT: "not safe to merge",
`docs/reviews/step08b_review_chatgpt.md`). Head when generated: `b947828`. Generated from the files on disk by a script
(`~/hc-work/step08b/fix/fixpacket.py`, quoted in the last section), so every diff and output below is quoted exactly.

Sections: 1 the fix-round summary (the first section of `docs/reviews/step08b_summary.md`); 2 the code diff since the
reviewed head; 3 new test files; 4 changed tests (diff); 5 the register changes; 6 the mutation checks; 7 the suite,
the images and GitHub; 8 the reference comparison with `main`; 9 the review text; 10 the plan file and the scripts.

## 1. The fix round


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
- **No live call was made in this round.** Live spending stays at $1.0278.

### Open

- **One live Critic call** (≤ $0.25, constructed data with a small flagged batch). It waits for the owner's go. The local development database is still at the earlier 0006, so before that call it needs a backup and a migration back down and up to the amended 0006. Its run rows are kept.
- The confirmation of the question as tested by a person is step 10 (the website).
- The Analyst's narrative is unverified by design; it is labelled as such.

## 2. Code diff (`859e019..HEAD`, the package; the register is in section 5)

````diff
diff --git a/hypocurate/cli_runs.py b/hypocurate/cli_runs.py
index adcfd8e..ca681aa 100644
--- a/hypocurate/cli_runs.py
+++ b/hypocurate/cli_runs.py
@@ -42,11 +42,7 @@ def command(args, engine: Engine) -> int:
         else:
             vid = queries.submitted_version(engine, args.number)
             queries.confirm_domain(engine, vid, by=args.by)
-            with engine.connect() as conn:
-                narrower = conn.execute(text("SELECT h.narrower_of_run_id IS NOT NULL FROM hypothesis h "
-                                             "JOIN hypothesis_version hv ON hv.hypothesis_id = h.id WHERE hv.id = :v"),
-                                        dict(v=vid)).scalar_one()
-            run_id = queries.dispatch(engine, vid, fixed_plan=narrower)
+            run_id = queries.dispatch(engine, vid)  # a narrower question's plan follows from its link (finding 1)
             number = args.number
     except queries.QueryRefused as refused:
         print(f"error: {refused.code}: {refused.reason}", file=sys.stderr)
@@ -75,11 +71,20 @@ def _ceiling(value: str | None) -> Decimal | None:
 
 
 def _run(engine: Engine, run_id: int, ceiling: Decimal | None) -> int:
+    """Two guarded calls: up to the rules lock, then on to the end. Between them the original claim and the
+    question as tested are printed (owner's decision B), before the run goes on."""
     from hypocurate.access.guarded import GuardedRunError, run_guarded
+    payload = {"run_id": run_id, "ceiling": str(ceiling) if ceiling is not None else None}
     try:
-        report = run_guarded("hypocurate.pipeline.orchestrator:run_guarded",
-                             {"run_id": run_id, "ceiling": str(ceiling) if ceiling is not None else None},
+        report = run_guarded("hypocurate.pipeline.orchestrator:run_guarded", {**payload, "phase": "prepare"},
                              timeout=3600, audit=(engine, run_id))
+        print(json.dumps({"claim": _claim(engine, run_id), "question_as_tested": report.get("question_as_tested")},
+                         ensure_ascii=False), flush=True)
+        if report.get("ready"):
+            rest = run_guarded("hypocurate.pipeline.orchestrator:run_guarded", {**payload, "phase": "proceed"},
+                               timeout=3600, audit=(engine, run_id))
+            report = {**rest, "stages": report["stages"] + rest["stages"],
+                      "question_as_tested": report.get("question_as_tested")}
     except GuardedRunError:
         print(f"error: run {run_id} did not finish in the guarded process (see the process log); "
               f"`hypocurate show {run_id}` shows what was stored", file=sys.stderr)
@@ -88,8 +93,22 @@ def _run(engine: Engine, run_id: int, ceiling: Decimal | None) -> int:
     return 0 if report.get("status") in ("completed", "failed") else 1
 
 
+def _claim(engine: Engine, run_id: int) -> str:
+    with engine.connect() as conn:
+        return conn.execute(text("SELECT hv.text FROM run r JOIN hypothesis_version hv ON hv.id = "
+                                 "r.hypothesis_version_id WHERE r.id = :r"), dict(r=run_id)).scalar_one()
+
+
+def question_as_tested(engine: Engine, run_id: int) -> dict | None:
+    from hypocurate.pipeline import reading
+    with engine.connect() as conn:
+        return reading.stored(conn, run_id)
+
+
 def show(engine: Engine, run_id: int) -> dict | None:
+    from hypocurate.pipeline import statement
     from hypocurate.pipeline import statistics as st
+    from hypocurate.pipeline.agents import analyst
     with engine.connect() as conn:
         run = conn.execute(text(
             "SELECT r.id, r.status, r.outcome, r.verdict, r.exploratory, r.evidence_level, r.failure_reason, "
@@ -122,10 +141,15 @@ def show(engine: Engine, run_id: int) -> dict | None:
         explanation = explained.get("shown") or "explanation unavailable"
     else:
         explanation = None
+    built = statement.build(engine, run_id)  # decision A: code's statement, for every completed run
     return {
-        "run": run.id, "query": run.number, "claim": run.text, "status": run.status,
+        "run": run.id, "query": run.number, "claim": run.text,
+        "question_as_tested": question_as_tested(engine, run.id), "status": run.status,
         "narrower_question_of": original, "narrower_question": narrower,
-        "plan": "fixed" if run.fixed_plan else "the Planner's", "sufficiency_option": run.sufficiency_option,
+        # A8: a narrower question's plan is shown as coming from its original's narrowing decision.
+        "plan": ("from the narrowing decision" if original is not None else "fixed") if run.fixed_plan
+                else "the Planner's",
+        "sufficiency_option": run.sufficiency_option,
         "outcome": decision.get("outcome_wording") if run.status == "completed" else None,
         "verdict": decision.get("verdict_wording") if run.verdict else None,
         "exploratory": run.exploratory, "evidence_level": run.evidence_level,
@@ -136,7 +160,11 @@ def show(engine: Engine, run_id: int) -> dict | None:
                                          "resid_df", "minimums_met")} for r in results if r["withheld"]],
         "minimums_missed": (gap or {}).get("minimums_missed"), "nothing_found": (gap or {}).get("kind"),
         "sources": (gap or {}).get("sources"),
-        "explanation": explanation, "explanation_label": "model explanation; numbers checked against the run record"
+        "statement": built["lines"] if built else None,
+        # Owner, 2026-10-07: the statement is shown with its format version (rendered; recorded at completion).
+        "statement_format_version": ({"rendered": built["format_version"], "recorded": built["recorded_format_version"]}
+                                     if built else None),
+        "explanation": explanation, "explanation_label": analyst.LABEL
         if isinstance(explained, dict) and explained.get("report") else None,
         "tokens_and_cost": {k: v for k, v in cost._mapping.items() if k != "run_id"} if cost else None,
         "p_value_description": st.P_VALUE_DESCRIPTION if any(r["p_value"] is not None for r in results) else None,
diff --git a/hypocurate/db/migrations/versions/0006_query_option_and_partly_sufficient.py b/hypocurate/db/migrations/versions/0006_query_option_and_partly_sufficient.py
index 8547c0b..56cdfb5 100644
--- a/hypocurate/db/migrations/versions/0006_query_option_and_partly_sufficient.py
+++ b/hypocurate/db/migrations/versions/0006_query_option_and_partly_sufficient.py
@@ -15,11 +15,19 @@ hypothesis_version (A2: the data-sufficiency option is a parameter of the query,
   version is a draft; a narrower question has its original's option.
 plan:
 - the locked plan's `sufficiency_option` must equal its run's query's option;
-- no plan is inserted for a run with a done narrowing decision of partly sufficient (A5).
+- no plan is inserted for a run with a done narrowing decision of partly sufficient (A5);
+- a narrower question's plan is exactly the narrower plan its original's narrowing decision stored (its
+  content less `hypothesis_version`, compared as JSON), and its run's source versions are those the
+  narrowing counts were taken on (A8, B1; added in the step 8b fix round, finding 1, owner's answer F-Q1).
 run (A5):
 - a run completes as 'partly_sufficient' only with no plan, no stored record, and a done 'narrowing'
   stage result whose output's result is 'partly_sufficient'. (0001 already requires no verdict, and 0004
   an evidence level consistent with it.)
+- a narrower question's run has `fixed_plan` true (it never goes through the Planner; fix round,
+  finding 1). 0001 already keeps `fixed_plan` from changing.
+- `statement_format_version` (fix round 1, owner 2026-10-07): the format version of the results statement, set
+  only in the update that completes the run and never changed after; null when the completing code did not set
+  it (the previous release's code, and runs completed before it existed).
 flag (A7):
 - `critic_class` is one of the Critic's fixed codes; `critic_reason` is at most 300 characters, not
   blank, and only with a class.
@@ -109,8 +117,69 @@ FUNCTIONS = [
         RETURN NEW;
     END $$
     """,
+    # A narrower question's run uses the narrower plan stored by its original's narrowing decision (fix round 1).
+    """
+    CREATE FUNCTION hc_run_narrower() RETURNS trigger LANGUAGE plpgsql AS $$
+    BEGIN
+        IF NOT NEW.fixed_plan AND EXISTS (
+                SELECT 1 FROM hypothesis_version hv JOIN hypothesis h ON h.id = hv.hypothesis_id
+                WHERE hv.id = NEW.hypothesis_version_id AND h.narrower_of_run_id IS NOT NULL) THEN
+            PERFORM hc_reject('a narrower question''s run uses the plan stored by its original''s narrowing decision '
+                              '(fixed_plan)');
+        END IF;
+        RETURN NEW;
+    END $$
+    """,
+    # Its plan is that stored plan, on the source versions the counts were taken on (A8, B1; fix round 1).
+    """
+    CREATE FUNCTION hc_plan_narrower() RETURNS trigger LANGUAGE plpgsql AS $$
+    DECLARE original bigint; decision jsonb; stored text[]; current text[];
+    BEGIN
+        SELECT h.narrower_of_run_id INTO original
+        FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id
+        JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = NEW.run_id;
+        IF original IS NULL THEN
+            RETURN NEW;
+        END IF;
+        SELECT output INTO decision FROM stage_result
+        WHERE run_id = original AND stage = 'narrowing' AND status = 'done'
+          AND output->>'result' = 'partly_sufficient'
+        ORDER BY id DESC LIMIT 1;
+        IF decision IS NULL OR jsonb_typeof(decision->'narrower_plan') IS DISTINCT FROM 'object'
+           OR (NEW.content - 'hypothesis_version') IS DISTINCT FROM decision->'narrower_plan' THEN
+            PERFORM hc_reject('a narrower question''s plan is the narrower plan stored by its original''s '
+                              'narrowing decision');
+        END IF;
+        SELECT coalesce(array_agg((e->>'source') || ' ' || (e->>'version_fingerprint') ORDER BY (e->>'source') || ' ' || (e->>'version_fingerprint')), '{}')
+        INTO stored
+        FROM jsonb_array_elements(CASE WHEN jsonb_typeof(decision->'sources') = 'array'
+                                       THEN decision->'sources' ELSE '[]'::jsonb END) e;
+        SELECT coalesce(array_agg(s.key || ' ' || sv.fingerprint ORDER BY s.key || ' ' || sv.fingerprint), '{}') INTO current
+        FROM run_source rs JOIN source s ON s.id = rs.source_id
+        JOIN source_version sv ON sv.id = rs.source_version_id
+        WHERE rs.run_id = NEW.run_id;
+        IF stored IS DISTINCT FROM current THEN
+            PERFORM hc_reject('a narrower question runs on the source versions its original''s narrowing counts '
+                              'were taken on');
+        END IF;
+        RETURN NEW;
+    END $$
+    """,
+    # The results statement's format version: recorded by the update that completes the run, then fixed (fix round 1).
+    """
+    CREATE FUNCTION hc_run_statement_version() RETURNS trigger LANGUAGE plpgsql AS $$
+    BEGIN
+        IF NEW.statement_format_version IS DISTINCT FROM OLD.statement_format_version
+           AND NOT (OLD.status <> 'completed' AND NEW.status = 'completed'
+                    AND OLD.statement_format_version IS NULL) THEN
+            PERFORM hc_reject('the statement format version is recorded when the run completes, and never changed');
+        END IF;
+        RETURN NEW;
+    END $$
+    """,
 ]
-FUNCTION_NAMES = ["hc_version_option()", "hc_plan_query()", "hc_run_partly_sufficient()"]
+FUNCTION_NAMES = ["hc_version_option()", "hc_plan_query()", "hc_run_partly_sufficient()", "hc_run_narrower()",
+                  "hc_plan_narrower()", "hc_run_statement_version()"]
 
 # (table, event, trigger, function). Each trigger's name sorts after the earlier trigger it follows.
 CHECKED = [
@@ -118,6 +187,9 @@ CHECKED = [
     ("hypothesis_version", "UPDATE", "hc_version_update_option", "hc_version_option"),
     ("plan", "INSERT", "hc_plan_insert_query", "hc_plan_query"),
     ("run", "UPDATE", "hc_run_update_partly_sufficient", "hc_run_partly_sufficient"),
+    ("run", "INSERT", "hc_run_insert_narrower", "hc_run_narrower"),
+    ("plan", "INSERT", "hc_plan_insert_narrower", "hc_plan_narrower"),
+    ("run", "UPDATE", "hc_run_update_statement_version", "hc_run_statement_version"),
 ]
 TRIGGERS = [f"CREATE TRIGGER {t} BEFORE {event} ON {table} FOR EACH ROW EXECUTE FUNCTION {f}()"
             for table, event, t, f in CHECKED]
@@ -128,6 +200,9 @@ def upgrade() -> None:
                                                   server_default=sa.text("'fixed_minimum'"), nullable=False))
     op.create_check_constraint(op.f('ck_hypothesis_version_sufficiency_option'), 'hypothesis_version',
                                _in('sufficiency_option', OPTIONS))
+    op.add_column('run', sa.Column('statement_format_version', sa.SmallInteger(), nullable=True))
+    op.create_check_constraint(op.f('ck_run_statement_format_version'), 'run',
+                               'statement_format_version IS NULL OR statement_format_version >= 1')
     op.create_check_constraint(op.f('ck_flag_critic_class'), 'flag',
                                f"critic_class IS NULL OR {_in('critic_class', CRITIC_CLASSES)}")
     op.create_check_constraint(op.f('ck_flag_critic_reason'), 'flag',
@@ -155,6 +230,8 @@ def downgrade() -> None:
         op.execute(f"DROP TRIGGER {t} ON {table}")
     for f in FUNCTION_NAMES:
         op.execute(f"DROP FUNCTION {f}")
+    op.drop_constraint(op.f('ck_run_statement_format_version'), 'run', type_='check')
+    op.drop_column('run', 'statement_format_version')
     op.drop_constraint(op.f('ck_flag_critic_reason'), 'flag', type_='check')
     op.drop_constraint(op.f('ck_flag_critic_class'), 'flag', type_='check')
     op.drop_constraint(op.f('ck_hypothesis_version_sufficiency_option'), 'hypothesis_version', type_='check')
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index 615dab7..9d6a40d 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -344,6 +344,8 @@ class Run(Base):
     # Step 7 (migration 0004; register 'evidence_level_scale'): 1 to 6, written by the copy path;
     # required on every completed run.
     evidence_level: Mapped[int | None] = mapped_column(SmallInteger)
+    # Step 8b fix round 1 (migration 0006): the results statement's format version, recorded when the run completes.
+    statement_format_version: Mapped[int | None] = mapped_column(SmallInteger)
     failure_reason: Mapped[str | None] = mapped_column(Text)
     agent_mode: Mapped[str] = mapped_column(Text, server_default=sql("'four_roles'"))
     fixed_plan: Mapped[bool] = mapped_column(Boolean, server_default=sql("false"))
@@ -366,6 +368,8 @@ class Run(Base):
                         "AND (evidence_level = 6) = (verdict IS NOT NULL AND NOT exploratory) "
                         "AND (evidence_level = 5) = (verdict IS NOT NULL AND exploratory))", name="evidence_level"),
         CheckConstraint("(evidence_level IS NOT NULL) = (status = 'completed')", name="evidence_level_iff_completed"),
+        CheckConstraint("statement_format_version IS NULL OR statement_format_version >= 1",
+                        name="statement_format_version"),
         CheckConstraint("status = 'queued' OR started_at IS NOT NULL OR status = 'failed'", name="started_time"),
         CheckConstraint("status <> 'completed' OR completed_at IS NOT NULL", name="completed_time"),
         CheckConstraint("(status = 'failed') = (failure_reason IS NOT NULL)", name="failed_has_reason"),
diff --git a/hypocurate/pipeline/agents/analyst.py b/hypocurate/pipeline/agents/analyst.py
index 7e9738b..72ef895 100644
--- a/hypocurate/pipeline/agents/analyst.py
+++ b/hypocurate/pipeline/agents/analyst.py
@@ -24,6 +24,8 @@ from typing import Any, Mapping
 from hypocurate.pipeline.agents import libraries, text_checks
 
 UNAVAILABLE = "explanation unavailable"
+# Owner's decision A (fix round 1): what the stored explanation is; shown with it, separately from code's statement.
+LABEL = "written by a language model; values inserted from the run record; narrative not verified"
 OUTPUT_DESCRIPTION = ("The explanation, in plain text, a few short paragraphs. No digits: every number, p-value, set of "
                       "paper figures, the outcome and the verdict are written as {name} placeholders from 'facts'.")
 
@@ -108,11 +110,11 @@ def run_analyst(engine, run_id: int, *, ceiling=None, client_options: Mapping[st
     from hypocurate.access.inputs import role_input
     from hypocurate.pipeline.agents.interface import call_agent
     from hypocurate.pipeline.agents.runstage import close_stage, open_stage
-    from hypocurate.pipeline.agents.settings import SETTINGS
+    from hypocurate.pipeline.agents.settings import recorded
 
     stage_id, invocation = open_stage(engine, run_id, "analyst", "analyst")
     data = role_input(bind_invocation(engine, invocation))
-    s = SETTINGS["analyst"]
+    s = recorded(engine, invocation)  # finding 2: the recorded version, never the current one
     inputs = render_inputs(data)
     check = make_check(data)
     result = call_agent(engine, invocation, signature(s["instruction"]), inputs, model=s["model"],
@@ -129,6 +131,6 @@ def run_analyst(engine, run_id: int, *, ceiling=None, client_options: Mapping[st
                                                    "attempts": result.attempts,
                                                    # owner, 2026-10-07: also for an attempt later corrected
                                                    "failure_details": result.details,
-                                                   "check": "numbers written by code from the run record"},
+                                                   "check": LABEL},
                 input_=inputs)
     return AnalystResult(report, None, stage_id, result.calls)
diff --git a/hypocurate/pipeline/agents/critic.py b/hypocurate/pipeline/agents/critic.py
index 41bc805..3650ea6 100644
--- a/hypocurate/pipeline/agents/critic.py
+++ b/hypocurate/pipeline/agents/critic.py
@@ -27,6 +27,7 @@ from sqlalchemy import Connection, Engine, text
 
 from hypocurate.access.vocabulary import CRITIC_CLASSES, CRITIC_REASON_MAX
 from hypocurate.pipeline.agents import libraries
+from hypocurate.pipeline.agents.lm import RUN_STOPS
 from hypocurate.pipeline.writes import Refused, write
 
 _FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.S)
@@ -95,7 +96,7 @@ def classify(data: Mapping, batch: list[Mapping]) -> Classified:
             continue
         if not isinstance(entry, dict) or set(entry) - {"class", "reason"} or "class" not in entry:
             out.refused[key] = "malformed_entry"
-        elif entry["class"] not in CRITIC_CLASSES:
+        elif not isinstance(entry["class"], str) or entry["class"] not in CRITIC_CLASSES:  # type first (finding 5)
             out.refused[key] = "class_not_allowed"
         elif entry.get("reason") is not None and not (isinstance(entry["reason"], str)
                                                        and 1 <= len(entry["reason"].strip()) <= CRITIC_REASON_MAX):
@@ -135,20 +136,21 @@ class CriticResult:
 
 def run_critic(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> CriticResult:
     """The Critic's stage(s). A failed batch leaves its flags unclassified; a spending refusal stops the
-    remaining batches (the orchestrator then fails the run, PRD 8)."""
+    remaining batches (the orchestrator then fails the run, PRD 8), and so does a recording or reservation
+    failure (the orchestrator then stops the run and leaves it open for recovery; fix round, finding 3)."""
     from hypocurate.access.dispatch import bind_invocation
     from hypocurate.access.inputs import role_input
     from hypocurate.pipeline.agents.interface import call_agent
     from hypocurate.pipeline.agents.runstage import close_stage, open_stage
-    from hypocurate.pipeline.agents.settings import SETTINGS
+    from hypocurate.pipeline.agents.settings import recorded
 
-    s = SETTINGS["critic"]
     classified, refused, failures, stages = 0, {}, [], []
     data = None
     plan_batches = None
     while True:
         stage_id, invocation = open_stage(engine, run_id, "critic", "critic")
         stages.append(stage_id)
+        s = recorded(engine, invocation)  # finding 2: the recorded version, never the current one
         current = role_input(bind_invocation(engine, invocation))
         if plan_batches is None:
             data, plan_batches = current, batches(current, s["limits"]["max_flags_per_call"])
@@ -166,7 +168,8 @@ def run_critic(engine: Engine, run_id: int, *, ceiling=None, client_options: Map
             refused.update({str(f["id"]): result.failure for f in batch})
             close_stage(engine, run_id, stage_id, "failed", {"code": result.failure, "attempts": result.attempts,
                                                              "flags": [f["id"] for f in batch]}, input_=inputs)
-            if result.failure.startswith("spending_cap") or result.failure == "ceiling_reached":
+            if (result.failure.startswith("spending_cap") or result.failure == "ceiling_reached"
+                    or result.failure in RUN_STOPS):  # finding 3: no further batch after an accounting failure
                 break
         else:
             got = classify(parse(result.outputs["classification"]), batch)
diff --git a/hypocurate/pipeline/agents/lm.py b/hypocurate/pipeline/agents/lm.py
index 00a1241..043bc97 100644
--- a/hypocurate/pipeline/agents/lm.py
+++ b/hypocurate/pipeline/agents/lm.py
@@ -39,6 +39,10 @@ LOG = logging.getLogger("hypocurate.pipeline")
 DEFAULT_TIMEOUT_SECONDS = 300
 # code -> (fixed text, what the runner does: "retry" (the same request again), "correct" (again, with
 # the fixed corrective note), or "stop").
+# The accounting failures that stop the whole run, not only the call (step 8b fix round, finding 3): after either,
+# no further model request is made for the run (no further Critic batch, no Analyst), and the run is left running,
+# with a call whose recording failed still started, for step 9's recovery.
+RUN_STOPS = ("recording_failed", "reservation_failed")
 FAILURES: Mapping[str, tuple[str, str]] = {
     "provider_unavailable": ("the provider could not be reached or did not answer in time", "retry"),
     "model_auth": ("the provider refused the credentials", "stop"),
diff --git a/hypocurate/pipeline/agents/planner.py b/hypocurate/pipeline/agents/planner.py
index ec062d6..8252a5f 100644
--- a/hypocurate/pipeline/agents/planner.py
+++ b/hypocurate/pipeline/agents/planner.py
@@ -28,12 +28,14 @@ import json
 import math
 import re
 from dataclasses import dataclass
+from types import MappingProxyType
 from typing import Any, Mapping
 
 from hypocurate.access.allowlist import ALLOY_CLASSES, EXCLUSION_RULES
 from hypocurate.access.vocabulary import PHASE_CLASSES, TEST_TYPES
 from hypocurate.pipeline import plan as plans
 from hypocurate.pipeline import profile as p
+from hypocurate.pipeline import reading
 from hypocurate.pipeline.agents import libraries
 from hypocurate.pipeline.eligibility import SUPPORTED_OUTCOMES
 
@@ -63,6 +65,14 @@ def signature(instruction: str):
     return PlannerSignature.with_instructions(instruction)
 
 
+# The profile's default of each scope part: what the Planner must give for a part it marks as not stated by the
+# claim (owner's decision B, fix round 1; register 'question_as_tested'). One named place: also the defaults the
+# Planner is shown.
+DEFAULT_SCOPE: Mapping[str, list] = MappingProxyType({
+    "alloy_class": list(p.ALLOY_CLASSES), "phase_class": list(p.PHASE_CLASSES),
+    "test_type": list(p.PERMITTED_TEST_TYPES), "temperature_band": [{"band": plans.ROOM_TEMPERATURE}]})
+
+
 def allowed_values(tag_values: list[Mapping]) -> dict:
     """The answer's form and allowed values, built by code from the vocabularies, the approved tag values
     and the profile's defaults (no run data)."""
@@ -84,8 +94,7 @@ def allowed_values(tag_values: list[Mapping]) -> dict:
         "outcome": list(SUPPORTED_OUTCOMES),
         "exclusion_rule_menu": {"grain_size_range": "min and/or max in µm", "temperature_range": "min and/or max in °C",
                                 "phase": CATEGORY_RULE_VALUES["phase"], "test_type": CATEGORY_RULE_VALUES["test_type"]},
-        "defaults": {"alloy_class": list(p.ALLOY_CLASSES), "phase_class": list(p.PHASE_CLASSES),
-                     "test_type": list(p.PERMITTED_TEST_TYPES), "temperature_band": [{"band": "room temperature"}],
+        "defaults": {**{k: list(v) for k, v in DEFAULT_SCOPE.items()},
                      "outcome": p.OUTCOME[0],
                      "exclusion_rules": [{"rule": "grain_size_range", "min": float(p.GRAIN_SIZE_FLOOR_UM)}]},
     }
@@ -123,6 +132,12 @@ def _number(v) -> bool:
     return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
 
 
+def _word(v, allowed) -> bool:
+    """A vocabulary value: text first, then membership (a list or object never reaches a membership test;
+    fix round, finding 5)."""
+    return isinstance(v, str) and v in allowed
+
+
 def _values(v, allowed, what) -> list:
     if not isinstance(v, list) or not v or not all(isinstance(x, str) for x in v) or len(set(v)) != len(v) \
             or not all(x in allowed for x in v):
@@ -135,7 +150,7 @@ def _bands(v) -> list[dict]:
         raise AnswerInvalid("temperature_band: a non-empty list")
     out, seen = [], set()
     for b in v:
-        if not isinstance(b, dict) or b.get("band") not in BANDS:
+        if not isinstance(b, dict) or not _word(b.get("band"), BANDS):
             raise AnswerInvalid("temperature_band: each {band} from the list")
         if b["band"] == plans.ROOM_TEMPERATURE:
             if set(b) != {"band"}:
@@ -157,7 +172,7 @@ def _exclusions(v) -> list[dict]:
         raise AnswerInvalid("exclusion_rules: a list")
     out = []
     for e in v:
-        if not isinstance(e, dict) or e.get("rule") not in EXCLUSION_RULES:
+        if not isinstance(e, dict) or not _word(e.get("rule"), EXCLUSION_RULES):
             raise AnswerInvalid("an exclusion rule comes from the menu")
         if e["rule"] in ("grain_size_range", "temperature_range"):
             if not set(e) - {"rule"} or set(e) - {"rule", "min", "max"} or not all(_number(e[k]) for k in e if k != "rule"):
@@ -196,14 +211,22 @@ def read_answer(data: Mapping) -> Answer:
         raise AnswerInvalid("the answer has exactly the keys " + ", ".join(sorted(KEYS)))
     if not isinstance(data["domain_matches"], bool):
         raise AnswerInvalid("domain_matches is true or false")
-    if data["outcome"] not in SUPPORTED_OUTCOMES:
+    if not _word(data["outcome"], SUPPORTED_OUTCOMES):
         raise AnswerInvalid("the outcome comes from the list")
     narrower = None if data["narrower"] is None else _scope(data["narrower"], NARROWER_KEYS)
     stated = data["stated"]
     if not isinstance(stated, dict) or set(stated) != SCOPE_KEYS or not all(isinstance(v, bool) for v in stated.values()):
         raise AnswerInvalid("'stated' marks each scope part true (stated by the claim) or false (defaulted)")
-    return Answer(data["domain_matches"], _scope(data["claim_scope"], SCOPE_KEYS), data["outcome"],
-                  _exclusions(data["exclusion_rules"]), narrower, dict(sorted(stated.items())))
+    scope = _scope(data["claim_scope"], SCOPE_KEYS)
+    for part, is_stated in stated.items():
+        if not is_stated and _sorted(scope[part]) != _sorted(DEFAULT_SCOPE[part]):
+            raise AnswerInvalid(f"{part} is marked as not stated by the claim but is not the default")
+    return Answer(data["domain_matches"], scope, data["outcome"], _exclusions(data["exclusion_rules"]), narrower,
+                  dict(sorted(stated.items())))
+
+
+def _sorted(values: list) -> list:
+    return sorted(values, key=lambda v: json.dumps(v, sort_keys=True))
 
 
 # --- The plan, built by code -------------------------------------------------------------------------
@@ -280,7 +303,7 @@ def run_planner(engine, run_id: int, *, ceiling=None, client_options: Mapping[st
     from hypocurate.access.inputs import role_input
     from hypocurate.pipeline.agents.interface import call_agent
     from hypocurate.pipeline.agents.runstage import close_stage, open_stage
-    from hypocurate.pipeline.agents.settings import SETTINGS
+    from hypocurate.pipeline.agents.settings import recorded
 
     stage_id, invocation = open_stage(engine, run_id, "planner", "planner")
     data = role_input(bind_invocation(engine, invocation))
@@ -289,7 +312,7 @@ def run_planner(engine, run_id: int, *, ceiling=None, client_options: Mapping[st
                                 "hypothesis_version hv ON hv.id = r.hypothesis_version_id WHERE r.id = :r"),
                            dict(r=run_id)).one()
     approved = {t["value"] for t in data["tag_values"] if t.get("kind") == "alloy_class"}
-    s = SETTINGS["planner"]
+    s = recorded(engine, invocation)  # finding 2: the recorded version, never the current one
     inputs = render_inputs(data)
     result = call_agent(engine, invocation, signature(s["instruction"]), inputs, model=s["model"],
                         max_tokens=s["limits"]["max_tokens"], max_output_chars=s["limits"]["max_output_chars"],
@@ -300,7 +323,10 @@ def run_planner(engine, run_id: int, *, ceiling=None, client_options: Mapping[st
                     input_=inputs)
         return PlannerResult(None, result.failure, stage_id, invocation, result.calls)
     answer = read_answer(parse(result.outputs["plan"]))
-    close_stage(engine, run_id, stage_id, "done", {"answer": answer.__dict__, "attempts": result.attempts},
-                input_=inputs)
+    # Decision B: the question as tested, in code's words, labelled as the Planner's reading.
+    tested = reading.question_as_tested(answer.claim_scope, answer.outcome, answer.exclusion_rules, answer.stated,
+                                        "planner")
+    close_stage(engine, run_id, stage_id, "done", {"answer": answer.__dict__, "attempts": result.attempts,
+                                                   "question_as_tested": tested}, input_=inputs)
     return PlannerResult(answer, None, stage_id, invocation, result.calls)
 
diff --git a/hypocurate/pipeline/agents/settings.py b/hypocurate/pipeline/agents/settings.py
index c92f989..29237d2 100644
--- a/hypocurate/pipeline/agents/settings.py
+++ b/hypocurate/pipeline/agents/settings.py
@@ -12,6 +12,7 @@ from __future__ import annotations
 
 import json
 from types import MappingProxyType
+from typing import Any, Mapping
 
 from sqlalchemy import Engine, text
 
@@ -120,3 +121,16 @@ def ensure_setting(engine: Engine, role: str) -> int:
             dict(r=role, i=s["instruction"], m=s["model"], l=json.dumps(limits), s=json.dumps(extra))).scalar_one()
 
     return run_transaction(engine, transaction)
+
+
+def recorded(engine: Engine, invocation: int) -> Mapping[str, Any]:
+    """The settings version recorded for the invocation (its instruction, model, limits and options), from which
+    every role builds its request: never the settings current when the request is made (step 8b fix round,
+    finding 2), so the audit record and the request cannot differ."""
+    with engine.connect() as conn:
+        row = conn.execute(text("SELECT a.instruction, a.model, a.limits, a.settings FROM agent_invocation i "
+                                "JOIN agent_setting a ON a.id = i.agent_setting_id WHERE i.id = :i"),
+                           dict(i=invocation)).one()
+    return MappingProxyType({"instruction": row.instruction, "model": row.model,
+                             "limits": MappingProxyType(dict(row.limits)),
+                             "settings": MappingProxyType(dict(row.settings))})
diff --git a/hypocurate/pipeline/analyst_names.py b/hypocurate/pipeline/analyst_names.py
index 1ec8bc5..64397cf 100644
--- a/hypocurate/pipeline/analyst_names.py
+++ b/hypocurate/pipeline/analyst_names.py
@@ -43,7 +43,7 @@ LABEL_WORDS = {"agrees": "in agreement with the pooled result",
                "same_direction_different_decision": "in the same direction as the pooled result, with a different test "
                                                     "result",
                "not_enough_data": "not testable alone"}
-TOO_FEW_GROUPS = "too few groups to test alone"
+TOO_FEW_GROUPS = "not testable alone (too few groups)"  # fix round 1: reads after "is" and in a list
 # Code-built sentences the Analyst uses whole (owner, 2026-10-07).
 GROUP_DEFINITION = "A group is a paper, or, for a source that is a single dataset, the whole dataset."
 MODEL_SENTENCE = ("The test fitted yield strength (MPa) as a baseline for each alloy plus one coefficient, shared by all "
@@ -81,6 +81,8 @@ def band_words(band: Mapping | str) -> str:
         return str(band)
     if band.get("band") == "room temperature" or "min" not in band:
         return str(band.get("band"))
+    if float(band["min"]) == float(band["max"]):
+        return f"{band['band']} ({display.temperature(band['min'])})"
     return f"{band['band']} ({display.temperature(band['min'])} to {display.temperature(band['max'])})"
 
 
@@ -124,12 +126,15 @@ def _calibration(prefix: str, c: Mapping | None) -> dict[str, str]:
 def calibration_summary(cal: Mapping, alpha: float) -> str:
     """One sentence covering both calibrations and their flags (owner, 2026-10-07)."""
     parts, flags = [], {}
+    described = False  # the interval's description is given once (owner, F-Q2)
     for method in ("estimated", "fixed"):
         c = cal.get(method)
         if isinstance(c, Mapping) and c.get("status") == "computed":
+            interval = (f"{display.percent(c['null']['ci_low'])} to {display.percent(c['null']['ci_high'])}" if described
+                        else display.interval_phrase(c["null"]["ci_low"], c["null"]["ci_high"]))
+            described = True
             parts.append(f"with {CALIBRATION_NAMES[method]}, the test was significant in "
-                         f"{display.percent(c['null']['share'])} of simulations with no effect "
-                         f"({display.interval_phrase(c['null']['ci_low'], c['null']['ci_high'])})")
+                         f"{display.percent(c['null']['share'])} of simulations with no effect ({interval})")
             flags[method] = c.get("flag_wording") or NO_FLAG
         else:
             reason = str((c or {}).get("reason") or "not computed") if isinstance(c, Mapping) else "not computed"
@@ -227,7 +232,11 @@ def analysis_names(stats: Mapping, gap: Mapping, plan: Mapping, scope_note: Mapp
     if analyses:
         pooled = analyses[0]
         names.update(_result("pooled", pooled, withheld))
+        # The count against each minimum, except the groups': that count is of informative groups, a paper figure
+        # shown only with the other three (fix round 1, finding 4; the statement shows the minimums).
         for k, m in (pooled.get("minimums") or {}).items():
+            if k == "groups":
+                continue
             names[f"count_{k}"] = _s(m.get("count"))
             names[f"met_{k}"] = "met" if m.get("met") else "not met"
         cal = pooled.get("calibration") or {}
diff --git a/hypocurate/pipeline/completion.py b/hypocurate/pipeline/completion.py
index 05404ed..607278a 100644
--- a/hypocurate/pipeline/completion.py
+++ b/hypocurate/pipeline/completion.py
@@ -18,8 +18,11 @@ from __future__ import annotations
 
 from sqlalchemy import Connection, Engine, text
 
+from hypocurate.pipeline.statement import FORMAT_VERSION as STATEMENT_FORMAT
 from hypocurate.pipeline.writes import Refused, write
 
+# Each completion records the format version of the results statement it will be shown with (fix round 1).
+
 ROLE = "completion"
 
 
@@ -39,9 +42,9 @@ def copy_decision(engine: Engine, run_id: int) -> dict:
         if decision.get("freeze_fingerprint") != snapshot:
             raise Refused("copy_decision", "decision_not_current")
         conn.execute(text("UPDATE run SET status = 'completed', completed_at = now(), outcome = :o, verdict = :v, "
-                          "exploratory = :x, evidence_level = :e WHERE id = :r"),
+                          "exploratory = :x, evidence_level = :e, statement_format_version = :f WHERE id = :r"),
                      dict(o=decision["outcome"], v=decision["verdict"], x=decision["exploratory"],
-                          e=decision["evidence_level"], r=run_id))
+                          e=decision["evidence_level"], f=STATEMENT_FORMAT, r=run_id))
         return decision
 
     return write(engine, run_id, ROLE, "copy_decision", body)
@@ -69,8 +72,9 @@ def copy_partly_sufficient(engine: Engine, run_id: int) -> dict:
         if stored != [tuple(c) for c in current]:
             raise Refused("copy_partly_sufficient", "decision_not_current")
         conn.execute(text("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
-                          "verdict = NULL, exploratory = false, evidence_level = :e WHERE id = :r"),
-                     dict(e=decision["evidence_level"], r=run_id))
+                          "verdict = NULL, exploratory = false, evidence_level = :e, statement_format_version = :f "
+                          "WHERE id = :r"),
+                     dict(e=decision["evidence_level"], f=STATEMENT_FORMAT, r=run_id))
         return decision
 
     return write(engine, run_id, ROLE, "copy_partly_sufficient", body)
diff --git a/hypocurate/pipeline/display.py b/hypocurate/pipeline/display.py
index 2d9aba3..24c5c9e 100644
--- a/hypocurate/pipeline/display.py
+++ b/hypocurate/pipeline/display.py
@@ -8,14 +8,13 @@ decimal. Drafted by Claude Code for the owner's review: every other share or rat
 their intervals) as a percentage to one decimal; temperatures, scatter and shift to at most one decimal; the
 threshold α as given; any other number to three significant figures.
 
-`display(facts)` turns every float of the Analyst's facts into its display string; integers (counts) stay as they
-are. `p_phrase`, `figures_phrase` and `interval_phrase` are ready-made phrases; `coefficient`, `stress` and
+Every number shown is formatted here, with its unit where it has one (fix round 1: the earlier `display(facts)`, which
+gave numbers without units, is deleted). `p_phrase`, `figures_phrase` and `interval_phrase` are ready-made phrases; `coefficient`, `stress` and
 `temperature` carry their units (owner, 2026-10-07); `nominal_level` gives the threshold as a percentage.
 """
 from __future__ import annotations
 
 import math
-from typing import Any, Callable, Mapping
 
 P_DESCRIPTION = "approximate, nominal, one-sided"
 
@@ -59,43 +58,6 @@ def fallback(v: float) -> str:
     return significant(v, 3)
 
 
-# Key -> how its value is shown. A list value (an interval) is shown element by element.
-RULES: Mapping[str, Callable[[float], str]] = {
-    "estimate": one_decimal, "std_error": one_decimal, "t": one_decimal,
-    "p_value": p_value,
-    "effective_papers": two_decimals,
-    "largest_paper_share": percent, "share": percent, "ci_low": percent, "ci_high": percent,
-    "detection": percent, "detection_ci": percent, "false_positive": percent, "false_positive_ci": percent,
-    "estimated_power": percent, "estimated_power_estimated_noise": percent,
-    "scatter": at_most_one_decimal, "shift": at_most_one_decimal, "min": at_most_one_decimal,
-    "max": at_most_one_decimal,
-    "alpha": as_given,
-}
-
-
-def _show(key: str | None, value: Any) -> Any:
-    if isinstance(value, bool) or value is None:
-        return value
-    if isinstance(value, float):
-        if not math.isfinite(value):
-            return None
-        if value.is_integer() and key not in RULES:
-            return int(value)
-        return RULES.get(key, fallback)(value)
-    if isinstance(value, int):
-        return value
-    if isinstance(value, Mapping):
-        return {k: _show(k, v) for k, v in value.items()}
-    if isinstance(value, list):
-        return [_show(key, v) for v in value]
-    return value
-
-
-def display(facts: Mapping) -> dict:
-    """The facts with every float as its display string (integers unchanged)."""
-    return _show(None, facts)
-
-
 # Owner, 2026-10-07 (after reading a live explanation): units on every estimate, standard error, scatter, shift and
 # temperature; one form for rates and the threshold (percentages); each simulation interval says what it is.
 COEFFICIENT_UNIT = "MPa·µm^0.5"
@@ -125,8 +87,9 @@ def interval_phrase(low: float, high: float) -> str:
 
 
 def p_phrase(p: float) -> str:
-    """The ready-made phrase for a p-value: the value and its fixed description."""
-    return f"p ≈ {p_value(p)} ({P_DESCRIPTION})"
+    """The ready-made phrase for a p-value: its fixed description and the value, with no brackets, so that it reads
+    the same inside parentheses (fix round 1, owner's wording fix)."""
+    return f"an {P_DESCRIPTION} p ≈ {p_value(p)}"
 
 
 def figures_phrase(informative: int, effective: float, largest_share: float, df: int) -> str:
diff --git a/hypocurate/pipeline/narrowing.py b/hypocurate/pipeline/narrowing.py
index 92253d9..b2508ab 100644
--- a/hypocurate/pipeline/narrowing.py
+++ b/hypocurate/pipeline/narrowing.py
@@ -15,7 +15,7 @@ accepted value statuses.
 **The decision** (`decide`, pure):
 - no part has zero records: `proceed` if the claim is one plan, else `claim_not_one_plan` (A11);
 - some part has zero records: the narrower scope is the claim's scope less exactly those parts, built by code
-  (owner, 2026-10-07, after live run C: the Planner cannot see which part has no usable record; a proposal of
+  (owner, 2026-10-07, after live run C: the Planner cannot see which part has no candidate record; a proposal of
   its, if any, is stored as `proposed_narrower` and never used). If a dimension is left empty, nothing is
   testable: `proceed` (the original then ends insufficient) or `claim_not_one_plan`. If the narrower scope
   makes a valid plan: `partly_sufficient`, with the narrower plan (less its hypothesis version) and its
@@ -107,7 +107,7 @@ def decide(answer: Answer, counts: list[Mapping], hypothesis_version_id: int, su
         return {**out, "result": fallback, "reason": "no_part_with_records"}
     out["narrower_scope"] = narrower
     # Owner, 2026-10-07 (after live run C): code builds the narrower scope from its own counts; the Planner
-    # cannot see which part has no usable record, so a proposal of its, if any, is stored and never used.
+    # cannot see which part has no candidate record, so a proposal of its, if any, is stored and never used.
     if len(scope["alloy_class"]) != 1 or not one_plan(narrower):
         return {**out, "result": fallback, "reason": "narrower_invalid"}
     try:
diff --git a/hypocurate/pipeline/orchestrator.py b/hypocurate/pipeline/orchestrator.py
index f5f5a10..aab9ec5 100644
--- a/hypocurate/pipeline/orchestrator.py
+++ b/hypocurate/pipeline/orchestrator.py
@@ -7,9 +7,11 @@ owner's answer A1; register 'run_order').
     -> rules lock -> store records -> Checks -> Critic -> Inclusion -> dataset freeze -> statistics
     -> Analyst -> completion (copy_decision)
 
-A fixed-plan run bypasses the Planner (and the narrowing): the reference plan of criterion 14.1a, or, for a
-narrower question, exactly the narrower plan its original's narrowing decision stored (A8), after checking
-that the run's source versions are those the counts were taken on (B1).
+A narrower question's run bypasses the Planner (and the narrowing): it locks exactly the narrower plan its
+original's narrowing decision stored (A8), after checking that the run's source versions are those the counts
+were taken on (B1). It is recognised by the question's link to its original, never by a flag (fix round,
+finding 1); the database refuses its plan otherwise (0006). A fixed-plan run of an ordinary question uses the
+reference plan of criterion 14.1a.
 
 **Code decides everything** (CLAUDE.md, rule 1); each agent's answer is checked by code before it is used.
 **No model call runs inside a database transaction**: every step below uses its own short transactions, and
@@ -19,9 +21,10 @@ the agents' stages are opened and closed around the request (`agents.runstage`).
 a refused checkpoint or write, a spending refusal at the Planner or the Critic, or changed source versions
 for a narrower question fail the run with a stated reason (`fail_run`). A Critic failure leaves flags
 unclassified and the run goes on (no decision reads the class). Any Analyst failure, a spending refusal
-included, leaves code's decision standing: the run completes with "explanation unavailable" (A3, B2). A call
-whose recording failed stays open; the database then refuses to end the run, which stays running for
-step 9's recovery, and `run` reports it.
+included, leaves code's decision standing: the run completes with "explanation unavailable" (A3, B2). A
+recording or a reservation failure at any agent (`lm.RUN_STOPS`) stops the run at once: no further model request
+is made (no further Critic batch, no Analyst), nothing more is written, and the run stays running (a call whose
+recording failed stays started) for step 9's recovery; `run` reports it (fix round, finding 3).
 """
 from __future__ import annotations
 
@@ -32,11 +35,14 @@ from typing import Any, Mapping
 from sqlalchemy import Connection, Engine, text
 
 from hypocurate.pipeline import analysis, checkpoints, checks, completion, extract, inclusion, narrowing, queries
+from hypocurate.pipeline import reading
 from hypocurate.pipeline import plan as plans
 from hypocurate.pipeline.agents import analyst, critic, planner
+from hypocurate.pipeline.agents.lm import RUN_STOPS
 from hypocurate.pipeline.writes import Refused, write
 
 SPENDING = ("spending_cap_run", "spending_cap_month", "ceiling_reached")
+STOPPED = "the run stopped and stays open for recovery (step 9); no further model request was made"
 # Fixed reasons of a failed run (failure_reason: "<code>: <reason>").
 REASONS = {
     "planner_failed": "the Planner gave no usable plan",
@@ -60,6 +66,9 @@ class RunReport:
     stages: list = field(default_factory=list)
     narrower_question: str | None = None
     explanation: str | None = None
+    explanation_failure: str | None = None
+    question_as_tested: dict | None = None
+    ready: bool = False  # prepared: the run goes on to the rules lock (`proceed`)
 
 
 def fail_run(engine: Engine, run_id: int, code: str, detail: str | None = None) -> str:
@@ -104,28 +113,47 @@ def _narrower_plan(engine: Engine, run_id: int, original: int, version_id: int)
 
 
 def run(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> RunReport:
-    """Runs the run to its end (completed or failed), or leaves it running if a call stayed open."""
+    """Runs the run to its end (completed or failed), or leaves it running if a call stayed open: `prepare`, then,
+    unless the run ended there, `proceed`."""
+    report = prepare(engine, run_id, ceiling=ceiling, client_options=client_options)
+    if not report.ready:
+        return report
+    rest = proceed(engine, run_id, ceiling=ceiling, client_options=client_options)
+    rest.stages = report.stages + rest.stages
+    rest.question_as_tested = report.question_as_tested
+    return rest
+
+
+def prepare(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> RunReport:
+    """Up to the rules lock: start; the narrower question's or the fixed plan, or the Planner and the narrowing
+    decision (the partly-sufficient path ends here). `ready` when the run goes on to `proceed`; the question as
+    tested is in the report (owner's decision B: the command line prints it before the run goes on)."""
     report = RunReport(run_id)
     agent_kw = dict(ceiling=ceiling, client_options=client_options)
     row = _row(engine, run_id)
     if row.status == "queued":
         queries.start(engine, run_id)
     try:
-        if row.fixed_plan:
-            if row.narrower_of_run_id is not None:
-                plan, code = _narrower_plan(engine, run_id, row.narrower_of_run_id, row.hypothesis_version_id)
-                if code:
-                    return _failed(engine, report, code)
-            else:
-                plan = plans.reference_plan(row.hypothesis_version_id)
-                plan["sufficiency"]["option"] = row.sufficiency_option
+        # A narrower question is recognised by its link to its original, never by the run's flag (fix round,
+        # finding 1): it always locks the stored narrower plan, after the source-version check (A8, B1).
+        if row.narrower_of_run_id is not None:
+            plan, code = _narrower_plan(engine, run_id, row.narrower_of_run_id, row.hypothesis_version_id)
+            if code:
+                return _failed(engine, report, code)
+            report.stages.append("fixed plan")
+            report.question_as_tested = reading.from_plan(plan, "narrower")
+        elif row.fixed_plan:
             report.stages.append("fixed plan")
+            report.question_as_tested = reading.from_plan(_reference_plan(row), "fixed")
         else:
             result = planner.run_planner(engine, run_id, **agent_kw)
             report.stages.append("planner")
+            if result.failure in RUN_STOPS:
+                return _stopped(engine, report, result.failure)
             if result.failure is not None:
                 return _failed(engine, report, "spending_refused" if result.failure in SPENDING else "planner_failed",
                                result.failure)
+            report.question_as_tested = _stored_reading(engine, result.stage_id)
             answer = result.answer
             if not answer.domain_matches:
                 return _failed(engine, report, "domain_mismatch")
@@ -134,13 +162,36 @@ def run(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[st
             if decision["result"] == "claim_not_one_plan":
                 return _failed(engine, report, "claim_not_one_plan", decision["reason"])
             if decision["result"] == "partly_sufficient":
-                _explain(engine, report, agent_kw)
+                if _explain(engine, report, agent_kw) in RUN_STOPS:
+                    return _stopped(engine, report, report.explanation_failure)
                 completion.copy_partly_sufficient(engine, run_id)
                 q = queries.create_narrower(engine, run_id, decision["narrower_scope"])
                 report.narrower_question = q.number
                 return _done(engine, report)
-            plan = planner.build_plan(row.hypothesis_version_id, answer.claim_scope, answer.outcome,
-                                      answer.exclusion_rules, row.sufficiency_option)
+        report.ready = True
+        return _done(engine, report)
+    except Refused as refused:
+        return _failed(engine, report, "refused", refused.code)
+
+
+def proceed(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> RunReport:
+    """From the rules lock to the end, for a run `prepare` left ready. The plan is built again from what is stored
+    (the narrower question's stored plan with its checks, the reference plan, or the Planner's stored answer after
+    a narrowing decision to proceed), so nothing is carried between the two in memory."""
+    report = RunReport(run_id)
+    agent_kw = dict(ceiling=ceiling, client_options=client_options)
+    row = _row(engine, run_id)
+    try:
+        if row.status != "running":
+            raise Refused("proceed", "stage_mismatch", "the run is not running")
+        if row.narrower_of_run_id is not None:
+            plan, code = _narrower_plan(engine, run_id, row.narrower_of_run_id, row.hypothesis_version_id)
+            if code:
+                return _failed(engine, report, code)
+        elif row.fixed_plan:
+            plan = _reference_plan(row)
+        else:
+            plan = _planner_plan(engine, run_id, row)
         checkpoints.lock_rules(engine, run_id, plan)
         report.stages.append("rules lock")
         extract.store_records(engine, run_id)
@@ -148,6 +199,9 @@ def run(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[st
         report.stages += ["records stored", "checks"]
         c = critic.run_critic(engine, run_id, **agent_kw)
         report.stages.append("critic")
+        stops = [f for f in c.failures if f in RUN_STOPS]
+        if stops:
+            return _stopped(engine, report, stops[0])
         spent = [f for f in c.failures if f in SPENDING]
         if spent:
             return _failed(engine, report, "spending_refused", spent[0])
@@ -155,18 +209,55 @@ def run(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[st
         checkpoints.freeze_dataset(engine, run_id)
         analysis.run_statistics(engine, run_id)
         report.stages += ["inclusion", "dataset freeze", "statistics"]
-        _explain(engine, report, agent_kw)
+        if _explain(engine, report, agent_kw) in RUN_STOPS:
+            return _stopped(engine, report, report.explanation_failure)
         completion.copy_decision(engine, run_id)
         return _done(engine, report)
     except Refused as refused:
         return _failed(engine, report, "refused", refused.code)
 
 
-def _explain(engine: Engine, report: RunReport, agent_kw: Mapping) -> None:
-    """The Analyst: any failure leaves code's decision standing (A3, B2)."""
+def _reference_plan(row) -> dict:
+    plan = plans.reference_plan(row.hypothesis_version_id)
+    plan["sufficiency"]["option"] = row.sufficiency_option
+    return plan
+
+
+def _stored_reading(engine: Engine, stage_id: int) -> dict | None:
+    with engine.connect() as conn:
+        return conn.execute(text("SELECT output->'question_as_tested' FROM stage_result WHERE id = :s"),
+                            dict(s=stage_id)).scalar_one()
+
+
+def _planner_plan(engine: Engine, run_id: int, row) -> dict:
+    """The plan from the Planner's stored answer, only after a stored narrowing decision to proceed."""
+    with engine.connect() as conn:
+        stored = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'planner' AND "
+                                   "status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
+        decided = conn.execute(text("SELECT output->>'result' FROM stage_result WHERE run_id = :r AND stage = "
+                                    "'narrowing' AND status = 'done' ORDER BY id DESC LIMIT 1"),
+                               dict(r=run_id)).scalar_one_or_none()
+    if not isinstance(stored, dict) or decided != "proceed":
+        raise Refused("proceed", "stage_mismatch", "no Planner answer with a narrowing decision to proceed")
+    a = stored["answer"]
+    return planner.build_plan(row.hypothesis_version_id, a["claim_scope"], a["outcome"], a["exclusion_rules"],
+                              row.sufficiency_option)
+
+
+def _explain(engine: Engine, report: RunReport, agent_kw: Mapping) -> str | None:
+    """The Analyst: any failure but an accounting one leaves code's decision standing (A3, B2). Returns the
+    failure code, if any."""
     result = analyst.run_analyst(engine, report.run_id, **agent_kw)
     report.stages.append("analyst")
     report.explanation = result.report if result.failure is None else f"{analyst.UNAVAILABLE} ({result.failure})"
+    report.explanation_failure = result.failure
+    return result.failure
+
+
+def _stopped(engine: Engine, report: RunReport, code: str) -> RunReport:
+    """An accounting failure (finding 3): nothing more is written or requested; the run stays as it is."""
+    report.failure = f"{code}: {STOPPED}"
+    return _done(engine, report)
 
 
 def _done(engine: Engine, report: RunReport) -> RunReport:
@@ -192,7 +283,8 @@ def run_guarded(payload: dict) -> dict:
     engine = make_engine(load_settings(web=False).database_url)
     try:
         ceiling = Decimal(payload["ceiling"]) if payload.get("ceiling") is not None else None
-        r = run(engine, int(payload["run_id"]), ceiling=ceiling, client_options=payload.get("client_options"))
+        phase = {"prepare": prepare, "proceed": proceed}.get(payload.get("phase"), run)
+        r = phase(engine, int(payload["run_id"]), ceiling=ceiling, client_options=payload.get("client_options"))
         return json.loads(json.dumps(r.__dict__, default=str))
     finally:
         engine.dispose()
diff --git a/hypocurate/pipeline/queries.py b/hypocurate/pipeline/queries.py
index 4683fc8..de5c034 100644
--- a/hypocurate/pipeline/queries.py
+++ b/hypocurate/pipeline/queries.py
@@ -121,17 +121,23 @@ def confirm_domain(engine: Engine, version_id: int, by: str, domain: str | None
 
 
 def dispatch(engine: Engine, version_id: int, *, fixed_plan: bool = False, constructed_test_data: bool = False) -> int:
-    """Dispatches the version; returns the queued run's id."""
+    """Dispatches the version; returns the queued run's id. `fixed_plan` asks for the reference plan (14.1a). A
+    narrower question's run always uses the plan its original's narrowing decision stored: that comes from the
+    question's link to its original, never from the caller's flag (step 8b fix round, finding 1; the database
+    refuses such a run without the flag, migration 0006)."""
     setting_ids = {role: agent_settings.ensure_setting(engine, role) for role in agent_settings.RUN_ROLES}
 
     def body(conn: Connection):
         _lock_version(conn, version_id)
+        narrower = conn.execute(text("SELECT h.narrower_of_run_id IS NOT NULL FROM hypothesis_version hv JOIN "
+                                     "hypothesis h ON h.id = hv.hypothesis_id WHERE hv.id = :v"),
+                                dict(v=version_id)).scalar_one()
         conn.execute(text("UPDATE hypothesis_version SET status = 'dispatched', dispatched_at = now() WHERE id = :v"),
                      dict(v=version_id))
         flags = json.dumps({CONSTRUCTED_MARK: True} if constructed_test_data else {})
         rid = conn.execute(text("INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags) "
                                 "VALUES (:v, :f, CAST(:x AS jsonb)) RETURNING id"),
-                           dict(v=version_id, f=fixed_plan, x=flags)).scalar_one()
+                           dict(v=version_id, f=fixed_plan or narrower, x=flags)).scalar_one()
         chosen = set(conn.execute(text("SELECT source_id FROM hypothesis_version_source WHERE hypothesis_version_id = :v"),
                                   dict(v=version_id)).scalars())
         for sid, key, latest in conn.execute(text(
diff --git a/hypocurate/pipeline/reading.py b/hypocurate/pipeline/reading.py
new file mode 100644
index 0000000..869b3fe
--- /dev/null
+++ b/hypocurate/pipeline/reading.py
@@ -0,0 +1,113 @@
+"""The question as tested (step 8b fix round 1, owner's decision B; register 'question_as_tested').
+
+Code writes, from a scope and its exclusion rules, the question a run actually tests: the outcome against grain
+size, each scope part in words (a band other than room temperature with its range), and each exclusion rule. For a
+run with the Planner, these are the Planner's reading of the claim: each part is marked as the claim states it or
+as assumed (the Planner's own marks, checked only in that a part marked assumed must hold the profile's default),
+and the label says the reading is not verified by code and that a person confirms it at the rules lock on the
+website (step 10). For a fixed-plan run, or a narrower question's run, the reading comes from that plan.
+
+The text is stored with the Planner's stage output (the Planner's reading) and, for a fixed or narrower plan,
+follows from the locked plan; the command line prints it beside the original claim before the run goes on to the
+rules lock, and `show` prints it.
+"""
+from __future__ import annotations
+
+from typing import Any, Mapping
+
+from sqlalchemy import Connection, text
+
+from hypocurate.pipeline import display
+from hypocurate.pipeline import plan as plans
+from hypocurate.pipeline import profile as p
+
+# Owner, 2026-10-07 (F-Q2): the labels say what is true in this version.
+LABELS = {
+    "planner": "the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a "
+               "person",
+    "fixed": "the fixed reference plan; not read from the claim",
+    "narrower": "the narrower plan stored by the original question's narrowing decision",
+}
+PART_LABELS = {"phase_class": "phase class", "test_type": "test type"}
+STATED = "as the claim states"
+ASSUMED = "assumed: the claim does not state it"
+
+
+def _number(v: float) -> str:
+    return display.at_most_one_decimal(float(v))
+
+
+def plural(alloy_class: str) -> str:
+    """'multi-principal-element (high-entropy) alloys' (owner, F-Q2: 'alloys', not 'alloy')."""
+    return alloy_class if alloy_class.endswith("s") else alloy_class + "s"
+
+
+def band_words(band: Mapping) -> str:
+    if band["band"] == plans.ROOM_TEMPERATURE:
+        lo, hi = p.ROOM_TEMPERATURE_C
+    else:
+        lo, hi = band["min"], band["max"]
+    if float(lo) == float(hi):
+        return f"{band['band']}, {_number(lo)} °C"
+    return f"{band['band']}, {_number(lo)} to {_number(hi)} °C"
+
+
+def exclusion_words(rule: Mapping) -> str:
+    kind = rule["rule"]
+    if kind in ("grain_size_range", "temperature_range"):
+        unit = "µm" if kind == "grain_size_range" else "°C"
+        what = "with a grain size" if kind == "grain_size_range" else "tested"
+        lo, hi = rule.get("min"), rule.get("max")
+        if lo is not None and hi is not None:
+            return f"excluding records {what} outside {_number(lo)} to {_number(hi)} {unit}"
+        if lo is not None:
+            return f"excluding records {what} below {_number(lo)} {unit}"
+        return f"excluding records {what} above {_number(hi)} {unit}"
+    label = "phase class" if kind == "phase" else "test type"
+    return f"excluding records of a {label} other than {', '.join(rule['values'])}"
+
+
+def question_as_tested(scope: Mapping, outcome: str, exclusion_rules: list, stated: Mapping | None,
+                       source: str) -> dict[str, str]:
+    """`scope` in the Planner's answer form (bands as {band, min, max}); `stated` the Planner's marks, or None."""
+
+    def mark(part: str, words: str) -> str:
+        if stated is None:
+            return words
+        return f"{words} ({STATED if stated.get(part) else ASSUMED})"
+
+    parts = [mark("alloy_class", ", ".join(plural(a) for a in scope["alloy_class"]))]
+    for part in ("phase_class", "test_type"):
+        parts.append(mark(part, f"{PART_LABELS[part]} {', '.join(scope[part])}"))
+    parts.append(mark("temperature_band", " and ".join(band_words(b) for b in scope["temperature_band"])))
+    parts += [exclusion_words(r) for r in exclusion_rules]
+    head = f"{outcome.replace('_', ' ')} against grain size, in "
+    return {"text": head + "; ".join(parts), "label": LABELS[source], "source": source}
+
+
+def from_plan(plan: Mapping[str, Any], source: str) -> dict[str, str]:
+    """The reading of a locked (or reference) plan: its scope, its band's range and its exclusion rules."""
+    s = plan["scope"]
+    bands = []
+    for name in s["temperature_band"]:
+        r = plan.get("rules", {}).get(plans.RANGE_RULE) if name != plans.ROOM_TEMPERATURE else None
+        bands.append({"band": name, **({"min": r["min"], "max": r["max"]} if r else {})})
+    scope = {"alloy_class": s["alloy_class"], "phase_class": s["phase_class"], "test_type": s["test_type"],
+             "temperature_band": bands}
+    return question_as_tested(scope, plan["variables"]["outcome"]["field"], plan.get("exclusion_rules") or [], None,
+                              source)
+
+
+def stored(conn: Connection, run_id: int) -> dict | None:
+    """The question as tested of a run: the Planner's stored reading, else the reading of its locked plan (fixed
+    or narrower), else the Planner's reading of a partly-sufficient original (no plan), else none."""
+    out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'planner' AND status = "
+                            "'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
+    if isinstance(out, dict) and out.get("question_as_tested"):
+        return out["question_as_tested"]
+    row = conn.execute(text("SELECT p.content, h.narrower_of_run_id FROM plan p JOIN run r ON r.id = p.run_id JOIN "
+                            "hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = "
+                            "hv.hypothesis_id WHERE p.run_id = :r"), dict(r=run_id)).one_or_none()
+    if row is None:
+        return None
+    return from_plan(row.content, "narrower" if row.narrower_of_run_id is not None else "fixed")
diff --git a/hypocurate/pipeline/statement.py b/hypocurate/pipeline/statement.py
new file mode 100644
index 0000000..ca3dcef
--- /dev/null
+++ b/hypocurate/pipeline/statement.py
@@ -0,0 +1,266 @@
+"""The results statement (step 8b fix round 1; owner's decision A, with the owner's changes of 2026-10-07; register
+'results_statement').
+
+Code writes a short fixed statement for every completed run from what code stored: the question as asked (the
+claim's words) and as tested (`pipeline.reading`), the outcome and verdict wording, the evidence level, the model
+sentence, the pooled estimate with its unit, the p-value phrase and the four paper figures together, the spread of
+the slope information, one sensitivity line, the calibration summary, and the main cautions chosen by fixed rules:
+
+- with a verdict, always: the result is an association under the stated model in the sources searched; it does
+  not show cause;
+- either calibration finds the method over-confident on data like these (which describes the method, not the error
+  of this particular p-value);
+- with a p-value only: a source, or a sensitivity set, not in agreement with the pooled result;
+- the result is exploratory.
+
+Below the minimums, and when nothing was frozen, each count is shown against its minimum, with the records found
+per source and how many lack the predictor or the outcome. A partly-sufficient original shows its candidate counts
+per part of the question and the narrower question, which a person must dispatch.
+
+The statement is rendered from the stored rows whenever it is shown (owner, 2026-10-07): `facts` reads them into a
+plain dictionary with no record identity, and `render` is a pure function of that dictionary, ordering sources and
+sensitivity sets itself, so the same stored rows always give the same text whatever the record ids or the order the
+rows come in. Its numbers come only from stored results and cannot change; its wording follows `FORMAT_VERSION`,
+which the completing code records on the run and which is shown with the statement; a change of wording is a new
+version (tests/test_statement.py pins the rendered text of each version). It is present for every completed run,
+whatever happened to the Analyst, and holds nothing a model wrote. The Analyst's explanation is stored and shown
+separately, under its own label (`agents.analyst.LABEL`).
+"""
+from __future__ import annotations
+
+from typing import Any, Mapping
+
+import json
+
+from sqlalchemy import Connection, Engine, text
+
+from hypocurate.pipeline import analyst_names as an
+from hypocurate.pipeline import display, queries, reading
+from hypocurate.pipeline import statistics as st
+
+# The statement's format: change it with any change of wording (owner, 2026-10-07; register 'results_statement').
+FORMAT_VERSION = 1
+ASSOCIATION = "The result is an association under the stated model in the sources searched; it does not show cause."
+OVER_CONFIDENT = ("The simulation check found the method over-confident on data with this structure; that describes "
+                  "the method on data like these, not the error of this particular p-value.")
+EXPLORATORY = "Exploratory: the minimums were waived (use what is available); the validity checks were not."
+NONE = "Main cautions: none beyond those above."
+DISPATCH = "It is not run until a person dispatches it."
+MINIMUM_WORDS = {"records": "records", "alloys": "alloys with at least 2 grain sizes", "groups": "informative groups",
+                 "resid_df": "residual degrees of freedom"}
+MINIMUM_ORDER = ("records", "alloys", "groups", "resid_df")
+LACKING = ("grain_size", "yield_strength")  # the predictor and the outcome
+
+
+def _source_name(key: str) -> str:
+    from hypocurate.sources.versions import SOURCES
+    d = SOURCES.get(key)
+    return d.name if d is not None else key
+
+
+def _cap(s: str) -> str:
+    return s[:1].upper() + s[1:]
+
+
+def _output(conn: Connection, run_id: int, stage: str) -> Any:
+    return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = :s AND status = 'done' "
+                             "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).scalar_one_or_none()
+
+
+# --- reading the stored rows -----------------------------------------------------------------------------------
+
+IDENTITY_KEYS = ("records_found",)  # stored lists of record ids: never part of the facts
+
+
+def _without_identity(value: Any) -> Any:
+    if isinstance(value, dict):
+        return {k: _without_identity(v) for k, v in value.items() if k not in IDENTITY_KEYS}
+    if isinstance(value, list):
+        return [_without_identity(v) for v in value]
+    return value
+
+
+def facts(conn: Connection, run_id: int) -> dict | None:
+    """What the statement is rendered from, as plain JSON values with no record identity; None unless completed."""
+    run = conn.execute(text(
+        "SELECT r.status, r.outcome, r.verdict, r.exploratory, r.evidence_level, r.statement_format_version, hv.text "
+        "FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id WHERE r.id = :r"),
+        dict(r=run_id)).one()
+    if run.status != "completed":
+        return None
+    out = {"claim": run.text, "tested": reading.stored(conn, run_id), "outcome": run.outcome,
+           "verdict": run.verdict, "exploratory": run.exploratory, "evidence_level": run.evidence_level,
+           "recorded_format_version": run.statement_format_version}
+    if run.outcome == "partly_sufficient":
+        out["narrowing"] = _output(conn, run_id, "narrowing") or {}
+        out["narrower_number"] = conn.execute(text("SELECT number FROM hypothesis WHERE narrower_of_run_id = :r "
+                                                   "ORDER BY id LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
+        return _without_identity(json.loads(json.dumps(out, default=str)))
+    plan = conn.execute(text("SELECT content FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar_one()
+    model = plan.get("model") or {}
+    out.update(statistics=_output(conn, run_id, "statistics") or {}, gap=_output(conn, run_id, "gap_facts") or {},
+               alpha=model.get("alpha"), alternative=model.get("alternative"),
+               found=dict(conn.execute(text(
+                   "SELECT s.key, count(*) FROM record r JOIN source_version sv ON sv.id = r.source_version_id "
+                   "JOIN source s ON s.id = sv.source_id WHERE r.extraction_run_id = :r GROUP BY s.key"),
+                   dict(r=run_id)).all()))
+    return _without_identity(json.loads(json.dumps(out, default=str)))
+
+
+# --- the pure rendering ------------------------------------------------------------------------------------------
+
+def counts_against_minimums(minimums: Mapping[str, Mapping]) -> str:
+    parts = []
+    for key in MINIMUM_ORDER:
+        m = minimums.get(key)
+        if m is None:
+            continue
+        if key == "resid_df" and (m.get("count") or 0) <= 0:
+            parts.append(f"no residual degrees of freedom (minimum {m['minimum']})")
+        else:
+            parts.append(f"{m['count']} of {m['minimum']} {MINIMUM_WORDS[key]}")
+    return "Counts against the minimums: " + "; ".join(parts) + "."
+
+
+def _found_lines(found: Mapping[str, int], gap: Mapping) -> list[str]:
+    lacking = gap.get("records_lacking_fields") or {}
+    lines = []
+    for s in sorted(gap.get("sources") or [], key=lambda s: s["source"]):
+        key = s["source"]
+        parts = [f"{found.get(key, 0):,} records found"]
+        for field in LACKING:
+            n = (lacking.get(key) or {}).get(field)
+            if n:
+                parts.append(f"{n:,} {'lacks' if n == 1 else 'lack'} a {field.replace('_', ' ')}")
+        lines.append(f"  {_source_name(key)}: " + "; ".join(parts) + ".")
+    return lines
+
+
+def _over_confident(calibration: Mapping) -> bool:
+    return any(isinstance(c, Mapping) and c.get("status") == "computed" and c.get("confidence_flag") == "over_confident"
+               for c in calibration.values())
+
+
+def _ordered(analyses: list) -> list[Mapping]:
+    """Pooled first, then the sources by key, then the sensitivity sets by key: never the stored order."""
+    rank = {"pooled": 0, "per_source": 1, "sensitivity": 2}
+    return sorted((e for e in analyses if isinstance(e, Mapping)),
+                  key=lambda e: (rank.get(e.get("scope"), 3), str(e.get("source") or ""), str(e.get("set") or "")))
+
+
+def _sensitivity_line(sets: list[Mapping], pooled: Mapping, alpha: float) -> str | None:
+    estimated = [e["estimate"] for e in sets if e.get("estimate") is not None]
+    if not sets or not estimated:
+        return None
+    agree = sum(1 for e in sets if st.label(e, pooled, alpha) == "agrees")
+    return (f"Sensitivity: {agree} of {len(sets)} sets in agreement with the pooled result; estimates from "
+            f"{display.coefficient(min(estimated))} to {display.coefficient(max(estimated))}.")
+
+
+def _analysis_lines(f: Mapping) -> list[str]:
+    stats, gap, alpha = f["statistics"], f["gap"], f["alpha"]
+    analyses = _ordered(stats.get("analyses") or [])
+    withheld = bool(stats.get("withheld"))
+    lines: list[str] = []
+    cautions: list[str] = []
+    if f["verdict"]:
+        cautions.append(ASSOCIATION)
+    if not analyses:
+        lines.append(f"Nothing was tested: no dataset was frozen ({str(gap.get('kind') or 'no record').replace('_', ' ')}).")
+        lines.append(counts_against_minimums(gap.get("minimums") or {}))
+        lines += _found_lines(f["found"], gap)
+    elif withheld:
+        lines.append("No estimate is shown: the minimums were not met.")
+        lines.append(counts_against_minimums(analyses[0].get("minimums") or {}))
+        lines += _found_lines(f["found"], gap)
+    else:
+        pooled = analyses[0]
+        sets = [e for e in analyses if e.get("scope") == "sensitivity"]
+        c = pooled.get("counts") or {}
+        inference = pooled.get("p_value") is not None
+        lines.append(an.MODEL_SENTENCE)
+        where = f"{c.get('n_records')} records on {c.get('n_alloys')} alloys"
+        if inference:
+            figures = display.figures_phrase(c["n_groups_informative"], c["effective_papers"], c["largest_paper_share"],
+                                             pooled["df"])
+            lines.append(f"Pooled estimate: {display.coefficient(pooled['estimate'])}, standard error "
+                         f"{display.coefficient(pooled['std_error'])}; {display.p_phrase(pooled['p_value'])}; {where}; "
+                         f"from {figures}.")
+        else:
+            reason = str(pooled.get("inference_reason") or "no valid inference").replace("_", " ")
+            lines.append(f"Pooled estimate: {display.coefficient(pooled['estimate'])}, the coefficient only ({reason}): "
+                         f"no uncertainty, no p-value and no verdict; {where}.")
+        note = an.direction_note(pooled.get("estimate"), f["alternative"])
+        if note:
+            lines.append(_cap(note) + ".")
+        if inference:
+            lines.append(f"Spread of the slope information: an effective number of groups of "
+                         f"{display.two_decimals(c['effective_papers'])} out of {c['n_groups_informative']} informative "
+                         f"groups; largest share {display.percent(c['largest_paper_share'])}.")
+        lines.append(an.GROUP_DEFINITION)
+        if inference:
+            sensitivity = _sensitivity_line(sets, pooled, alpha)
+            if sensitivity:
+                lines.append(sensitivity)
+        calibration = pooled.get("calibration") or {}
+        lines.append(an.calibration_summary(calibration, alpha).strip())
+        if _over_confident(calibration):
+            cautions.append(OVER_CONFIDENT)
+        if inference:
+            for e in analyses:
+                if e.get("scope") == "per_source" and e.get("label") and e["label"] != "agrees":
+                    cautions.append(f"{_source_name(e['source'])}: {an.label_words(e)}.")
+            others = an.sensitivity_summary(analyses, pooled, alpha, withheld)["sensitivity_not_agreeing"]
+            if others != "none":
+                cautions.append(f"Sensitivity sets not in agreement with the pooled result: {others}.")
+    if f["exploratory"]:
+        cautions.append(EXPLORATORY)
+    lines.append("Main cautions:" if cautions else NONE)
+    lines += [f"  - {x}" for x in cautions]
+    return lines
+
+
+def _partly_lines(f: Mapping) -> list[str]:
+    narrowing = f["narrowing"]
+    names = an.narrowing_names(narrowing)
+    counts = []
+    for letter in an.LETTERS:
+        if f"part_{letter}" not in names:
+            break
+        counts.append(f"{names[f'part_{letter}']}: {names[f'part_{letter}_records']}")
+    lines = ["Records with a grain size and the outcome, per part of the question (candidates before any "
+             "eligibility decision): " + "; ".join(counts) + "."]
+    if f.get("narrower_number") is not None:
+        lines.append(f"Narrower question {f['narrower_number']}: "
+                     f"{queries.scope_in_words(narrowing.get('narrower_scope') or {})}. {DISPATCH}")
+    return lines
+
+
+def render(f: Mapping) -> list[str]:
+    """The statement's lines: a pure function of `facts` (same facts, same text)."""
+    lines = [f"Question as asked: {f['claim']}"]
+    if f.get("tested"):
+        lines.append(f"Question as tested ({f['tested']['label']}): {f['tested']['text']}.")
+    if f["outcome"] == "partly_sufficient":
+        d = f["narrowing"].get("decision") or {}
+        lines.append(f"Outcome: {d.get('outcome_wording')}. The original question was not tested and has no verdict.")
+        lines.append(f"Evidence level: {f['evidence_level']} ({d.get('evidence_level_wording')}).")
+        return lines + _partly_lines(f)
+    d = f["statistics"].get("decision") or {}
+    label = f" ({d['label']})" if d.get("label") else ""
+    verdict = f"Verdict: {d['verdict_wording']}." if f["verdict"] else "No verdict."
+    lines.append(f"Outcome: {d.get('outcome_wording')}{label}. {verdict}")
+    lines.append(f"Evidence level: {f['evidence_level']} ({d.get('evidence_level_wording')}).")
+    return lines + _analysis_lines(f)
+
+
+def build(engine: Engine, run_id: int) -> dict | None:
+    """The statement of a completed run, or None for a run that is not completed: its lines and text, the format
+    version it is rendered in, and the version recorded on the run when it completed (None if not recorded)."""
+    with engine.connect() as conn:
+        f = facts(conn, run_id)
+    if f is None:
+        return None
+    lines = render(f)
+    return {"lines": lines, "text": "\n".join(lines), "format_version": FORMAT_VERSION,
+            "recorded_format_version": f["recorded_format_version"]}
diff --git a/hypocurate/sources/curation.py b/hypocurate/sources/curation.py
index b321cae..91d97ae 100644
--- a/hypocurate/sources/curation.py
+++ b/hypocurate/sources/curation.py
@@ -67,7 +67,7 @@ def curate(engine: Engine, key: str, *, ceiling: Decimal | None = None,
     from hypocurate.access.inputs import role_input
     from hypocurate.pipeline.agents import curator
     from hypocurate.pipeline.agents.interface import call_agent
-    from hypocurate.pipeline.agents.settings import SETTINGS, ensure_setting
+    from hypocurate.pipeline.agents.settings import ensure_setting, recorded
 
     version = _version(engine, key)
     if version.grouping_unit != "dataset":
@@ -81,7 +81,7 @@ def curate(engine: Engine, key: str, *, ceiling: Decimal | None = None,
         "INSERT INTO agent_invocation (scope, source_version_id, role, agent_setting_id) "
         "VALUES ('registration', :v, 'curator', :a) RETURNING id"), dict(v=version.id, a=setting)).scalar_one())
     data = role_input(bind_invocation(engine, invocation))
-    s = SETTINGS["curator"]
+    s = recorded(engine, invocation)  # finding 2: the recorded version, never the current one
     result = call_agent(engine, invocation, curator.signature(s["instruction"]), curator.render_inputs(data),
                         model=s["model"], max_tokens=s["limits"]["max_tokens"],
                         max_output_chars=s["limits"]["max_output_chars"], ceiling=ceiling,
````
## 3. New test files

### `tests/answer_shapes.py`

```python
"""Step 8b fix round 1, finding 5: wrong-type answer shapes for every role's validator tests.

`variants(answer)` yields the answer with each position (the whole answer, every value of every object and every
item of every list) replaced in turn by each value of `WRONG`: valid JSON of every type, including the nested
lists and objects that once raised TypeError at a membership test. A validator must refuse each with its own
code and never raise anything else.
"""
from __future__ import annotations

import json
from typing import Any, Iterator

WRONG = [None, True, 0, 1.5, "", "x", [], ["x"], [[]], {}, {"a": 1}, {"class": []}]


def _paths(o: Any, path: tuple = ()) -> Iterator[tuple]:
    yield path
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _paths(v, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _paths(v, path + (i,))


def _replaced(o: Any, path: tuple, value: Any) -> Any:
    if not path:
        return value
    copy = json.loads(json.dumps(o))
    cur = copy
    for k in path[:-1]:
        cur = cur[k]
    cur[path[-1]] = value
    return copy


def variants(answer: Any) -> Iterator[tuple[tuple, Any, Any]]:
    """(path, wrong value, the answer with that value at that path)."""
    for path in list(_paths(answer)):
        for value in WRONG:
            yield path, value, _replaced(answer, path, value)
```
### `tests/fixtures/statement_facts.json`

(data fixture, 223,498 bytes; not quoted)

### `tests/test_orchestrator_flagged.py`

```python
"""Step 8b fix round 1: the orchestrator on constructed data that raises flags, so the Critic is really called.

- Replaces the earlier Critic-failure test, which used the reference data (no flags) and so could pass without
  any Critic request (ChatGPT's review, "Tests").
- Finding 3: a recording or reservation failure stops the run: no further Critic batch and no Analyst call; the
  run stays running (and a call whose recording failed stays started) for step 9's recovery.

Every model call goes to the local stub provider.
"""
from __future__ import annotations

from types import MappingProxyType

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import orchestrator, queries
from hypocurate.pipeline.agents import settings as agent_settings
from hypocurate.pipeline.agents import spend
from stats_world import small_rows
from test_critic import CONFLICT
from test_orchestrator import responder

CLAIM = "In FCC multi-principal-element alloys, yield strength rises as grain size falls"


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


def one(engine, sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar()


def dispatched(engine, flags_per_call=None, monkeypatch=None):
    """A fixed-plan run on the constructed data; `flags_per_call` is recorded in the Critic's settings version."""
    if flags_per_call is not None:
        c = agent_settings.SETTINGS["critic"]
        changed = MappingProxyType({**c, "limits": MappingProxyType({**c["limits"], "max_flags_per_call": flags_per_call})})
        monkeypatch.setattr(agent_settings, "SETTINGS", MappingProxyType({**agent_settings.SETTINGS, "critic": changed}))
    q = queries.create(engine, CLAIM, ("mpea",))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    return queries.dispatch(engine, q.version_id, fixed_plan=True, constructed_test_data=True)


def run(engine, rid, stub):
    return orchestrator.run(engine, rid, client_options=sp.client_options(stub))


def kinds(stub) -> list[str]:
    """Which role each request was for, in order."""
    out = []
    for r in stub.requests:
        raw = r["raw"].decode()
        out.append("critic" if "[[ ## classification ## ]]" in raw else "analyst" if "[[ ## report ## ]]" in raw
                   else "other")
    return out


def test_a_critic_failure_on_flagged_data_leaves_every_flag_unclassified_and_the_run_completes(engine, stub):
    def respond(raw):
        if "[[ ## classification ## ]]" in raw:
            return sp.reply(sp.fields(classification="prose, not JSON"))
        return responder()(raw)
    stub.respond(respond)
    rid = dispatched(engine)
    report = run(engine, rid, stub)
    flags = one(engine, "SELECT count(*) FROM flag WHERE run_id = :r", r=rid)
    assert flags >= 2                                                     # the data raise flags
    assert kinds(stub)[:2] == ["critic", "critic"]                        # the Critic was asked, and corrected once
    assert one(engine, "SELECT status FROM stage_result WHERE run_id = :r AND stage = 'critic'", r=rid) == "failed"
    assert one(engine, "SELECT count(*) FROM flag WHERE run_id = :r AND critic_class IS NOT NULL", r=rid) == 0
    assert report.status == "completed" and "analyst" in kinds(stub)      # the run went on to the end
    assert one(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid) == 1


@pytest.mark.parametrize("failure", ["recording_failed", "reservation_failed"])
def test_an_accounting_failure_at_the_critic_stops_the_run_with_no_further_request(engine, stub, monkeypatch,
                                                                                    failure):
    attempts = []

    def broken(*a, **kw):
        attempts.append(1)
        raise RuntimeError("database gone")

    rid = dispatched(engine, flags_per_call=1, monkeypatch=monkeypatch)
    stub.respond(responder())
    monkeypatch.setattr(spend, "finish" if failure == "recording_failed" else "reserve", broken)
    report = run(engine, rid, stub)
    assert one(engine, "SELECT count(*) FROM flag WHERE run_id = :r", r=rid) >= 2  # two batches were due
    assert attempts == [1]                                                # one reservation or one recording only
    assert kinds(stub) == (["critic"] if failure == "recording_failed" else [])  # no second batch, no Analyst
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'critic'", r=rid) == 1
    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'analyst'", r=rid) == 0
    assert one(engine, "SELECT count(*) FROM run_snapshot WHERE run_id = :r", r=rid) == 0
    assert report.status == "running" and one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    assert failure in report.failure
    if failure == "recording_failed":
        assert one(engine, "SELECT count(*) FROM model_call mc JOIN agent_invocation i ON i.id = mc.invocation_id "
                           "WHERE i.run_id = :r AND mc.status = 'started'", r=rid) == 1


@pytest.mark.parametrize("failure", ["recording_failed", "reservation_failed"])
def test_an_accounting_failure_at_the_analyst_stops_the_run_before_completion(engine, stub, monkeypatch, failure):
    def critic_ok(raw):
        if "[[ ## classification ## ]]" in raw:
            return sp.reply(sp.fields(classification="{}"))
        return responder()(raw)

    stub.respond(critic_ok)
    rid = dispatched(engine)
    real = {"finish": spend.finish, "reserve": spend.reserve}
    name = "finish" if failure == "recording_failed" else "reserve"

    def broken_for_the_analyst(db, *a, **kw):
        with db.connect() as conn:
            role = conn.execute(text("SELECT role FROM stage_result WHERE run_id = :r AND status = 'running'"),
                                dict(r=rid)).scalar()
        if role == "analyst":
            raise RuntimeError("database gone")
        return real[name](db, *a, **kw)

    monkeypatch.setattr(spend, name, broken_for_the_analyst)
    report = run(engine, rid, stub)
    assert report.status == "running" and failure in report.failure
    assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
    assert one(engine, "SELECT outcome FROM run WHERE id = :r", r=rid) is None   # nothing copied
```
### `tests/test_reading.py`

```python
"""Step 8b fix round 1, owner's decision B: "the question as tested", built by code from the scope and exclusion
rules (the Planner's reading, or a fixed plan), with its label. No model call."""
from __future__ import annotations

import pytest

from hypocurate.pipeline import plan as plans
from hypocurate.pipeline import reading

MPEA = "multi-principal-element (high-entropy) alloy"


def test_the_label_says_whose_reading_it_is_and_that_a_person_confirms_it():
    """Owner, F-Q2 (2026-10-07): the labels say what is true in this version (no person confirms the reading yet)."""
    assert reading.LABELS["planner"] == ("the Planner's reading of the claim; not verified by code and, in this "
                                         "version, not confirmed by a person")
    assert reading.LABELS["fixed"] == "the fixed reference plan; not read from the claim"
    assert reading.LABELS["narrower"] == "the narrower plan stored by the original question's narrowing decision"


@pytest.mark.parametrize("rule, words", [
    ({"rule": "grain_size_range", "min": 0.1}, "excluding records with a grain size below 0.1 µm"),
    ({"rule": "grain_size_range", "max": 100.0}, "excluding records with a grain size above 100 µm"),
    ({"rule": "grain_size_range", "min": 0.5, "max": 50.0},
     "excluding records with a grain size outside 0.5 to 50 µm"),
    ({"rule": "temperature_range", "min": 10.0, "max": 30.0},
     "excluding records tested outside 10 to 30 °C"),
    ({"rule": "phase", "values": ["FCC"]}, "excluding records of a phase class other than FCC"),
    ({"rule": "test_type", "values": ["tension"]}, "excluding records of a test type other than tension")])
def test_each_exclusion_rule_in_words(rule, words):
    assert reading.exclusion_words(rule) == words


def test_an_elevated_band_names_its_range_and_no_marks_without_a_reading():
    scope = {"alloy_class": [MPEA], "phase_class": ["FCC"], "test_type": ["compression"],
             "temperature_band": [{"band": "elevated", "min": 900.0, "max": 1100.0}]}
    q = reading.question_as_tested(scope, "yield_strength", [], None, "fixed")
    assert q == {"text": f"yield strength against grain size, in {MPEA}s; phase class FCC; test type compression; "
                         "elevated, 900 to 1100 °C", "label": reading.LABELS["fixed"], "source": "fixed"}


def test_the_reference_plans_reading():
    q = reading.from_plan(plans.reference_plan(1), "fixed")
    assert q["text"] == (f"yield strength against grain size, in {MPEA}s; phase class FCC; test type tension; "
                         "room temperature, 20 to 25 °C; excluding records with a grain size below 0.1 µm")


def test_a_band_at_one_temperature_names_it_once():
    assert reading.band_words({"band": "elevated", "min": 1000.0, "max": 1000.0}) == "elevated, 1000 °C"


def test_two_bands_are_joined_so_that_one_mark_covers_both():
    scope = {"alloy_class": [MPEA], "phase_class": ["FCC"], "test_type": ["tension"],
             "temperature_band": [{"band": "room temperature"}, {"band": "cryogenic", "min": -200.0, "max": -150.0}]}
    stated = {"alloy_class": True, "phase_class": True, "test_type": False, "temperature_band": True}
    q = reading.question_as_tested(scope, "yield_strength", [], stated, "planner")
    assert "room temperature, 20 to 25 °C and cryogenic, -200 to -150 °C (as the claim states)" in q["text"]
```
### `tests/test_recorded_settings.py`

```python
"""Step 8b fix round 1, finding 2: each role builds its request from the settings version recorded for its
invocation (instruction, model, limits and options), never from the settings current when the request is made.

Each test records version A (the current settings) at dispatch, then makes the current settings version B (a
changed instruction, effort and limits, the same model) and stores B, as a later deployment would on its next
dispatch, and only then runs the role. The request must be A's. Every model call goes to the local stub provider.
"""
from __future__ import annotations

import json
from types import MappingProxyType

import pytest

import stub_provider as sp
from hypocurate.pipeline.agents import settings as agent_settings
from test_analyst import BELOW, below_minimums
from test_analyst import reply as analyst_reply
from test_critic import checked_run, flag_ids, version
from test_critic import reply as critic_reply
from test_curator import answer as curator_answer
from test_curator import register_base, run_curate
from test_planner_narrowing import answer as planner_answer
from test_planner_narrowing import plan_run, running

MARKER = "VERSION-B-MARKER"
OTHER_EFFORT = {"low": "high", "medium": "high", "high": "low"}
HAIKU_BUDGET = {"low": 1024, "medium": 2048, "high": 4096}


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


def version_b(role: str) -> dict:
    """The role's current settings changed in everything but the model."""
    a = agent_settings.SETTINGS[role]
    limits = {**a["limits"], "max_tokens": a["limits"]["max_tokens"] + 1000}
    if "max_flags_per_call" in limits:
        limits["max_flags_per_call"] = 1
    effort = OTHER_EFFORT[a["settings"]["reasoning_effort"]]
    return MappingProxyType({"instruction": f"{a['instruction']} {MARKER}", "model": a["model"],
                             "limits": MappingProxyType(limits),
                             "settings": MappingProxyType({**a["settings"], "reasoning_effort": effort})})


def make_current(monkeypatch, engine, role: str) -> dict:
    """Version B becomes the current settings and is stored; returns version A (what the run recorded)."""
    a = agent_settings.SETTINGS[role]
    monkeypatch.setattr(agent_settings, "SETTINGS", MappingProxyType({**agent_settings.SETTINGS, role: version_b(role)}))
    agent_settings.ensure_setting(engine, role)
    return a


def assert_request_is(body: dict, a) -> None:
    raw = json.dumps(body, ensure_ascii=False)
    assert MARKER not in raw
    assert body["model"].endswith(a["model"])
    assert body["max_tokens"] == a["limits"]["max_tokens"]
    effort = a["settings"]["reasoning_effort"]
    if "haiku" in a["model"]:  # litellm (locked version) sends Haiku's effort as a thinking budget
        assert body["thinking"] == {"type": "enabled", "budget_tokens": HAIKU_BUDGET[effort]}
    else:
        assert body["output_config"] == {"effort": effort}


def test_the_planner_uses_the_settings_recorded_at_dispatch(migrated_database, stub, monkeypatch):
    from hypocurate.db.engine import make_engine
    engine = make_engine(migrated_database)
    try:
        rid = running(engine)
        a = make_current(monkeypatch, engine, "planner")
        stub.queue(sp.reply(planner_answer()))
        plan_run(engine, rid, stub)
        assert_request_is(stub.bodies()[0], a)
    finally:
        engine.dispose()


def test_the_critic_uses_the_settings_recorded_at_dispatch(migrated_database, stub, monkeypatch):
    import pipeline_world as pw
    from hypocurate.db.engine import make_engine
    from stats_world import small_rows
    from test_critic import CONFLICT
    engine = make_engine(migrated_database)
    try:
        pw.registered_files(engine, {"mpea": pw.mpea_csv(small_rows(3, papers=3) + CONFLICT)})
        rid = checked_run(engine, version(engine))
        flags = flag_ids(engine, rid)
        assert len(flags) >= 2  # version B's limit of one flag per call would make one call per flag
        a = make_current(monkeypatch, engine, "critic")
        stub.respond(lambda raw: critic_reply({str(f): {"class": "cannot_tell", "reason": "same metadata"}
                                               for f in flags}))
        from hypocurate.pipeline.agents import critic
        critic.run_critic(engine, rid, client_options=sp.client_options(stub))
        assert len(stub.requests) == 1
        assert_request_is(stub.bodies()[0], a)
    finally:
        engine.dispose()


def test_the_analyst_uses_the_settings_recorded_at_dispatch(migrated_database, stub, monkeypatch):
    from hypocurate.db.engine import make_engine
    from hypocurate.pipeline.agents import analyst
    engine = make_engine(migrated_database)
    try:
        rid = below_minimums(engine)
        a = make_current(monkeypatch, engine, "analyst")
        stub.queue(analyst_reply(BELOW))
        analyst.run_analyst(engine, rid, client_options=sp.client_options(stub))
        assert_request_is(stub.bodies()[0], a)
    finally:
        engine.dispose()


def test_the_curators_request_follows_the_setting_its_invocation_records(db, stub, monkeypatch):
    """The Curator's invocation records the setting at the call (registration scope); the request is built from
    that recorded row, so the audit record and the request cannot differ."""
    register_base(db)
    a_id = agent_settings.ensure_setting(db, "curator")
    a = make_current(monkeypatch, db, "curator")
    monkeypatch.setattr(agent_settings, "ensure_setting", lambda engine, role: a_id)
    stub.queue(sp.reply(curator_answer()))
    run_curate(db, "tamu_fcc", stub)
    assert_request_is(stub.bodies()[0], a)
```
### `tests/test_statement.py`

```python
"""Step 8b fix round 1, owner's decision A (with the owner's changes of 2026-10-07, F-Q2): the results statement.

Code writes a short fixed statement from the stored facts of every completed run, whether or not the Analyst
succeeded: the question as asked and as tested, the outcome and verdict wording, the evidence level, the model
sentence, the estimate with its unit and the four figures together, the spread of the slope information, one
sensitivity line, the calibration summary and the main cautions chosen by fixed rules. It is built from stored rows
whenever it is shown (`statement.build`), so it is present for every completed run and holds nothing a model wrote.
Every model call goes to the local stub provider.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import pytest
from sqlalchemy import text

import pipeline_world as pw
import stub_provider as sp
from hypocurate.db.engine import make_engine
from hypocurate.pipeline import analysis, analyst_names, completion, orchestrator, queries, reading, statement
from stats_world import run_on, small_rows
from test_orchestrator import (BCC, BCC_CLAIM, FCC_CLAIM, PARTLY, PARTLY_CLAIM, planner_body, responder)

MPEA = "multi-principal-element (high-entropy) alloys"
TESTED_FIXED = (f"Question as tested ({reading.LABELS['fixed']}): yield strength against grain size, in {MPEA}; "
                "phase class FCC; test type tension; room temperature, 20 to 25 °C; excluding records with a grain size "
                "below 0.1 µm.")


@pytest.fixture
def stub():
    s = sp.StubProvider()
    yield s
    s.close()


@pytest.fixture
def engine(migrated_database):
    e = make_engine(migrated_database)
    pw.registered(e, ("mpea", "tamu_fcc"))
    yield e
    e.dispose()


@pytest.fixture
def bare(migrated_database):
    e = make_engine(migrated_database)
    yield e
    e.dispose()


def run_claim(engine, stub, claim=FCC_CLAIM, fixed_plan=False, analyst=None, planner_answer=None):
    kw = {"analyst": analyst} if analyst else {}
    stub.respond(responder(planner_answer, **kw))
    q = queries.create(engine, claim, ("mpea", "tamu_fcc"))
    queries.submit(engine, q.version_id)
    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
    rid = queries.dispatch(engine, q.version_id, fixed_plan=fixed_plan)
    return orchestrator.run(engine, rid, client_options=sp.client_options(stub))


def stored_stats(engine, rid):
    with engine.connect() as conn:
        return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics'"),
                            dict(r=rid)).scalar()


def test_the_reference_run_s_statement(engine, stub):
    report = run_claim(engine, stub, fixed_plan=True)
    lines = statement.build(engine, report.run_id)["lines"]
    calibration = analyst_names.calibration_summary(stored_stats(engine, report.run_id)["analyses"][0]["calibration"],
                                                    0.05)
    assert lines == [
        f"Question as asked: {FCC_CLAIM}",
        TESTED_FIXED,
        "Outcome: sufficient in the sources searched. Verdict: supported under the stated model, in the sources "
        "searched.",
        "Evidence level: 6 (sufficient with a verdict).",
        analyst_names.MODEL_SENTENCE,
        "Pooled estimate: 424.9 MPa·µm^0.5, standard error 64.4 MPa·µm^0.5; an approximate, nominal, one-sided "
        "p ≈ 1.3e-6; 97 records on 22 alloys; from 20 informative groups, an effective number of groups of 3.94, a "
        "largest share of 38.7% and 19 degrees of freedom.",
        "The estimate is positive, the direction the claim describes.",
        "Spread of the slope information: an effective number of groups of 3.94 out of 20 informative groups; "
        "largest share 38.7%.",
        analyst_names.GROUP_DEFINITION,
        "Sensitivity: 9 of 9 sets in agreement with the pooled result; estimates from 393.5 MPa·µm^0.5 to "
        "432.4 MPa·µm^0.5.",
        calibration,
        "Main cautions:",
        f"  - {statement.ASSOCIATION}",
        f"  - {statement.OVER_CONFIDENT}",
        "  - Texas A&M FCC dataset (Mulukutla et al. 2026): not testable alone (too few groups).",
    ]
    assert calibration.count(analyst_names.display.INTERVAL_NOTE) == 1  # the interval described once (owner)


def test_the_statement_is_present_when_the_analyst_fails_and_holds_nothing_it_wrote(engine, stub):
    report = run_claim(engine, stub, fixed_plan=True, analyst=lambda raw: "The data do not exist {outcome_wording}.")
    assert report.status == "completed" and report.explanation.startswith("explanation unavailable")
    built = statement.build(engine, report.run_id)
    assert built["lines"][0] == f"Question as asked: {FCC_CLAIM}" and "424.9 MPa·µm^0.5" in built["text"]
    assert "do not exist" not in built["text"]


def test_a_planner_run_s_statement_labels_the_planner_s_reading(engine, stub):
    report = run_claim(engine, stub, planner_answer=planner_body())
    lines = statement.build(engine, report.run_id)["lines"]
    assert lines[1].startswith(f"Question as tested ({reading.LABELS['planner']}): yield strength against grain size")
    assert reading.LABELS["planner"] == ("the Planner's reading of the claim; not verified by code and, in this "
                                         "version, not confirmed by a person")
    assert "test type tension (assumed: the claim does not state it)" in lines[1]


def test_nothing_frozen_shows_each_count_against_its_minimum_and_the_records_found_per_source(engine, stub):
    report = run_claim(engine, stub, claim=BCC_CLAIM, planner_answer=BCC)
    lines = statement.build(engine, report.run_id)["lines"]
    assert lines[2] == "Outcome: insufficient in the sources searched. No verdict."
    assert lines[3] == "Evidence level: 1 (no dataset frozen)."
    assert lines[4] == "Nothing was tested: no dataset was frozen (missing evidence)."
    assert lines[5] == ("Counts against the minimums: 0 of 30 records; 0 of 5 alloys with at least 2 grain sizes; "
                        "0 of 10 informative groups; no residual degrees of freedom (minimum 10).")
    with engine.connect() as conn:
        found = dict(conn.execute(text("SELECT s.key, count(*) FROM record r JOIN source_version sv ON sv.id = "
                                       "r.source_version_id JOIN source s ON s.id = sv.source_id WHERE "
                                       "r.extraction_run_id = :r GROUP BY s.key"), dict(r=report.run_id)).all())
    mpea = next(x for x in lines if x.startswith("  MPEA dataset"))
    assert mpea.startswith(f"  MPEA dataset (Borg et al. 2020): {found['mpea']:,} records found; ")
    assert "lack a grain size" in mpea and "lack a yield strength" in mpea
    assert lines[-1] == "Main cautions: none beyond those above."


def test_partly_sufficient_shows_the_counts_per_part_and_the_narrower_question_to_dispatch(engine, stub):
    report = run_claim(engine, stub, claim=PARTLY_CLAIM, planner_answer=PARTLY)
    lines = statement.build(engine, report.run_id)["lines"]
    assert lines[2] == ("Outcome: partly sufficient in the sources searched. The original question was not tested "
                        "and has no verdict.")
    assert lines[3] == "Evidence level: 1 (original question not tested; a narrower question was proposed)."
    parts = next(x for x in lines if x.startswith("Records with a grain size and the outcome"))
    assert "candidates before any eligibility decision" in parts and "cryogenic" in parts and ": 0" in parts
    assert lines[-1] == (f"Narrower question {report.narrower_question}: phase class FCC; test type tension; room "
                         "temperature. It is not run until a person dispatches it.")


@pytest.mark.parametrize("case", ["exploratory", "coefficient_only", "below_minimums"])
def test_the_other_kinds(bare, case):
    kw, option = {"exploratory": (dict(papers=3), "use_available"), "coefficient_only": (dict(papers=1), "use_available"),
                  "below_minimums": (dict(papers=3, base=7311.0), "fixed_minimum")}[case]
    rid = run_on(bare, small_rows(3, **kw), option=option, agents=("analyst",))
    analysis.run_statistics(bare, rid)
    completion.copy_decision(bare, rid)
    lines = statement.build(bare, rid)["lines"]
    text_ = "\n".join(lines)
    if case == "exploratory":
        assert lines[2].startswith("Outcome: sufficient in the sources searched (exploratory). Verdict: supported")
        assert lines[3] == "Evidence level: 5 (use what is available with a minimum missed (exploratory))."
        assert f"  - {statement.EXPLORATORY}" in lines and f"  - {statement.ASSOCIATION}" in lines
        assert any(x.startswith("Spread of the slope information: an effective number of groups of 3.00 out of 3 "
                                "informative groups; largest share 33.3%.") for x in lines)
    elif case == "coefficient_only":
        assert lines[2] == "Outcome: insufficient in the sources searched. No verdict."
        assert any(x.startswith("Pooled estimate: 298.5 MPa·µm^0.5, the coefficient only (insufficient groups): no "
                                "uncertainty, no p-value and no verdict; 6 records on 3 alloys") for x in lines)
        assert "Spread of the slope information" not in text_ and "p ≈" not in text_
        assert lines[-1] == "Main cautions: none beyond those above."
    else:
        assert lines[2] == ("Outcome: insufficient in the sources searched (data found; not enough to test). "
                            "No verdict.")
        assert "No estimate is shown: the minimums were not met." in lines
        assert ("Counts against the minimums: 6 of 30 records; 3 of 5 alloys with at least 2 grain sizes; 3 of 10 "
                "informative groups; 2 of 10 residual degrees of freedom.") in lines
        assert analyst_names.MODEL_SENTENCE not in lines and "MPa·µm^0.5" not in text_   # nothing estimated shown
        assert any(x.startswith("  MPEA dataset (Borg et al. 2020): 6 records found") for x in lines)


def test_a_failed_run_has_no_statement(engine, stub):
    report = run_claim(engine, stub, planner_answer=planner_body(domain_matches=False))
    assert report.status == "failed" and statement.build(engine, report.run_id) is None


# --- a pure function of the stored rows, with a format version (owner, 2026-10-07) ------------------------------

FIXTURE = Path(__file__).parent / "fixtures" / "statement_facts.json"
# The rendered text of every case in FIXTURE, per format version: a change of wording changes this fingerprint, so it
# must come with a new FORMAT_VERSION (and a new entry here; the old ones stay).
RENDERED = {1: "6b667638eb8a8db4d19476b0b40a09e87df994df080811dc69d6fbfbac2bf596"}


def facts_of(engine, rid):
    with engine.connect() as conn:
        return statement.facts(conn, rid)


def test_the_same_stored_rows_give_the_same_text_whatever_the_record_ids(engine, stub):
    report = run_claim(engine, stub, fixed_plan=True)
    vid = pw.version_of(engine, report.run_id)
    again = pw.run_of_version(engine, vid, ("mpea", "tamu_fcc"), agents=("planner", "critic", "analyst"))
    assert orchestrator.run(engine, again, client_options=sp.client_options(stub)).outcome == "sufficient"
    with engine.connect() as conn:
        ids = [set(conn.execute(text("SELECT id FROM record WHERE extraction_run_id = :r"), dict(r=r)).scalars())
               for r in (report.run_id, again)]
    assert ids[0] and not ids[0] & ids[1]                                   # other records, other ids
    assert statement.build(engine, again)["text"] == statement.build(engine, report.run_id)["text"]
    f = facts_of(engine, again)
    assert not [i for i in ids[1] if f'"id": {i}' in json.dumps(f)]          # no record identity in the facts
    assert not set(statement.IDENTITY_KEYS) & set(json.dumps(f).replace('"', " ").split())


def test_the_facts_never_hold_the_stored_lists_of_record_ids(bare):
    rid = run_on(bare, small_rows(3, papers=3, base=7311.0), agents=("analyst",))
    out = analysis.run_statistics(bare, rid)
    completion.copy_decision(bare, rid)
    assert [i for e in out["analyses"] for i in e.get("records_found") or []]   # stored with the statistics
    assert "records_found" not in json.dumps(facts_of(bare, rid))


def test_the_order_of_the_stored_results_does_not_change_the_text(engine, stub):
    report = run_claim(engine, stub, fixed_plan=True)
    f = facts_of(engine, report.run_id)
    expected = statement.render(f)
    rng = random.Random(3)
    for _ in range(5):
        shuffled = json.loads(json.dumps(f))
        rng.shuffle(shuffled["statistics"]["analyses"])
        rng.shuffle(shuffled["gap"]["sources"])
        shuffled["found"] = dict(reversed(list(shuffled["found"].items())))
        assert statement.render(shuffled) == expected


def test_each_completion_records_the_format_version_and_show_gives_it(engine, stub):
    from hypocurate import cli_runs
    for report in (run_claim(engine, stub, fixed_plan=True),
                   run_claim(engine, stub, claim=PARTLY_CLAIM, planner_answer=PARTLY)):
        with engine.connect() as conn:
            recorded = conn.execute(text("SELECT statement_format_version FROM run WHERE id = :r"),
                                    dict(r=report.run_id)).scalar()
        assert recorded == statement.FORMAT_VERSION
        shown = cli_runs.show(engine, report.run_id)
        assert shown["statement_format_version"] == {"rendered": statement.FORMAT_VERSION,
                                                     "recorded": statement.FORMAT_VERSION}
        assert shown["statement"] == statement.build(engine, report.run_id)["lines"]


def rendered_fingerprint() -> str:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))
    text_ = "\n\n".join(f"{name}\n" + "\n".join(statement.render(f)) for name, f in sorted(cases.items()))
    return hashlib.sha256(text_.encode("utf-8")).hexdigest()


def test_the_wording_of_each_format_version_is_pinned():
    """Every case of the fixture (each kind of outcome, from stored facts) rendered with the current code: its
    fingerprint is the one recorded for the current FORMAT_VERSION. Changing any wording fails this test until the
    version is raised and its fingerprint added."""
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert set(cases) >= {"sufficient", "planner", "exploratory", "coefficient_only", "below_minimums",
                          "nothing_frozen", "partly_sufficient"}
    assert "records_found" not in FIXTURE.read_text(encoding="utf-8")
    assert statement.FORMAT_VERSION in RENDERED and rendered_fingerprint() == RENDERED[statement.FORMAT_VERSION]


@pytest.mark.parametrize("case", ["sufficient", "planner", "exploratory", "coefficient_only", "below_minimums",
                                  "nothing_frozen", "partly_sufficient"])
def test_every_kind_renders_the_same_whatever_the_order_of_its_stored_lists(case):
    """Mutation f35 (fix round 1): the order test above uses a run with an estimate, which lists no sources' records;
    here every kind, the nothing-frozen one with two sources, has each stored list reversed."""
    f = json.loads(FIXTURE.read_text(encoding="utf-8"))[case]
    expected = statement.render(f)
    flipped = json.loads(json.dumps(f))
    for path in (("statistics", "analyses"), ("gap", "sources")):
        node = flipped
        for k in path[:-1]:
            node = node.get(k) or {}
        if isinstance(node.get(path[-1]), list):
            node[path[-1]] = list(reversed(node[path[-1]]))
    flipped["found"] = dict(reversed(list((flipped.get("found") or {}).items())))
    if case == "nothing_frozen":
        assert len(f["gap"]["sources"]) == 2 and flipped["gap"]["sources"] != f["gap"]["sources"]
    assert statement.render(flipped) == expected
```
## 4. Changed tests and test helpers (diff)

```diff
diff --git a/tests/access_world.py b/tests/access_world.py
index 6e62a2b..d480c23 100644
--- a/tests/access_world.py
+++ b/tests/access_world.py
@@ -160,11 +160,13 @@ def stage(w: World, run: int, name: str, role: str, payload: str, attempt=1) ->
     return sid
 
 
-def lock(w: World, run: int) -> None:
+def planted_plan() -> dict:
+    """The plan the main run locks. Step 8b fix round 1 (finding 1): the main run is a narrower question's, so its
+    plan must be the narrower plan its original's narrowing decision stored (0006); the original stores this one."""
     ys = PLANTED["yield_strength"]
     # Planted in every kind of plan leaf; the projection keeps only named keys, vocabulary
     # values (else the marker), numbers and field names.
-    content = {"claim": DIRECTION,
+    return {"claim": DIRECTION,
                "variables": {"outcome": {"field": "yield_strength", "unit": f"{ys} MPa", "note": f"{ys}"},
                              "predictor": {"field": "grain_size", "unit": "µm", "transformation": f"x^{ys}"}},
                "model": {"name": "hall_petch_alloy_intercepts", "null": "k <= 0",
@@ -177,6 +179,11 @@ def lock(w: World, run: int) -> None:
                "verdict_statement": f"supported if {ys}",
                "sensitivity_analyses": ["tension_and_compression", f"drop {ys}"],
                "unnamed_key": {"planted": ys}}
+
+
+def lock(w: World, run: int) -> None:
+    ys = PLANTED["yield_strength"]
+    content = planted_plan()
     sql(w, "INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
            "min_groups, min_resid_df, power_assumptions) VALUES (:r, :j_c, :fp, 'fixed_minimum', 4, 1, 2, 1, :j_p)",
         r=run, j_c=content, fp=FP, j_p={"method": "information_only", "scatter": 60.0, "note": f"{ys}",
@@ -207,7 +214,7 @@ def original_run(w: World) -> tuple[int, int]:
     w.complete(tested, "insufficient", level=4)
     rid = w.running(vid=vid, sources=("mpea",))
     stage(w, rid, "analyst", "analyst", f"k = {OTHER}")
-    w.partly(rid)
+    w.partly(rid, narrower_plan=planted_plan())
     cid = stage(w, rid, "commentator", "commentator", f"the coefficient {OTHER}")
     sql(w, "INSERT INTO commentary (run_id, stage_result_id, status, text, model, number_check) "
            "VALUES (:r, :s, 'written', :t2, 'model-b', 'all_match')", r=rid, s=cid, t2=f"k was {OTHER}")
@@ -263,7 +270,7 @@ def build(engine, stage_name: str) -> AccessWorld:
     w.confirm(vid)
     w.dispatch_version(vid)
     earlier = w.running(vid=vid, sources=("mpea", "tamu_fcc"))
-    w.lock(earlier)
+    w.lock(earlier, content=planted_plan())
     store_value_records(w, earlier, OTHER)
     stage(w, earlier, "curator", "curator", f"saw {OTHER}")
     w.fail(earlier)
diff --git a/tests/model_builder.py b/tests/model_builder.py
index e8693f1..06e594d 100644
--- a/tests/model_builder.py
+++ b/tests/model_builder.py
@@ -2,6 +2,8 @@
 so the step 3 tests exercise the database rules exactly as later code will meet them."""
 from __future__ import annotations
 
+import json
+
 import hashlib
 
 import pytest
@@ -133,12 +135,17 @@ class World:
         return vid
 
     # --- runs -------------------------------------------------------------------------
-    def run(self, vid=None, sources=("mpea", "tamu_fcc"), agents=False, sufficiency="fixed_minimum"):
+    def run(self, vid=None, sources=("mpea", "tamu_fcc"), agents=False, sufficiency="fixed_minimum", fixed_plan=None):
         """Dispatch: a queued run with a run_source row for every registered source; with `agents`,
         the world's settings version of every role recorded too (needed for model calls, step 8a).
-        `sufficiency`: the new query's option (step 8b), when no version is given."""
+        `sufficiency`: the new query's option (step 8b), when no version is given. `fixed_plan`: by default
+        true exactly for a narrower question, as `queries.dispatch` derives it (step 8b fix round 1)."""
         vid = vid or self.dispatched(sufficiency=sufficiency)
-        rid = self.val("INSERT INTO run (hypothesis_version_id) VALUES (:v) RETURNING id", v=vid)
+        if fixed_plan is None:
+            fixed_plan = self.val("SELECT h.narrower_of_run_id IS NOT NULL FROM hypothesis_version hv "
+                                  "JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE hv.id = :v", v=vid)
+        rid = self.val("INSERT INTO run (hypothesis_version_id, fixed_plan) VALUES (:v, :f) RETURNING id",
+                       v=vid, f=fixed_plan)
         if agents:
             for role in ("planner", "curator", "critic", "analyst", "commentator"):
                 self.run_sql("INSERT INTO run_agent_setting VALUES (:r, :o, :s)", r=rid, o=role,
@@ -166,17 +173,19 @@ class World:
         self.lock(rid)
         return rid
 
-    def lock(self, rid, option=None, keys=(), mins=(4, 1, 2, 1), tags=()):
+    def lock(self, rid, option=None, keys=(), mins=(4, 1, 2, 1), tags=(), content=None):
         """The rules lock, in one transaction with its tags. Step 8b (0006): the plan's option is the
-        query's unless a test gives another (which the database refuses)."""
+        query's unless a test gives another (which the database refuses). `content`: the plan's content
+        (default empty; a narrower question's must be its original's stored narrower plan, fix round 1)."""
         option = option or self.val("SELECT hv.sufficiency_option FROM run r JOIN hypothesis_version hv "
                                     "ON hv.id = r.hypothesis_version_id WHERE r.id = :r", r=rid)
         with self.e.begin() as conn:
             pid = conn.execute(text(
                 "INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, min_alloys, "
                 "min_groups, min_resid_df, sensitivity_analysis_keys) "
-                "VALUES (:r, '{}', :fp, :o, :a, :b, :c, :d, :k) RETURNING id"),
-                dict(r=rid, fp=FP, o=option, a=mins[0], b=mins[1], c=mins[2], d=mins[3], k=list(keys))).scalar()
+                "VALUES (:r, CAST(:j AS jsonb), :fp, :o, :a, :b, :c, :d, :k) RETURNING id"),
+                dict(r=rid, j=json.dumps(content or {}), fp=FP, o=option, a=mins[0], b=mins[1], c=mins[2], d=mins[3],
+                     k=list(keys))).scalar()
             for tag in tags:
                 conn.execute(text("INSERT INTO run_tag VALUES (:r, :t)"), dict(r=rid, t=tag))
         return pid
@@ -268,17 +277,25 @@ class World:
                      "exploratory = :x, evidence_level = :e WHERE id = :r", o=outcome, v=verdict, x=exploratory,
                      e=level, r=rid)
 
-    def partly(self, rid):
+    def partly(self, rid, narrower_plan=None, sources=("mpea", "tamu_fcc")):
         """Step 8b (0006; owner, A5): a run completes as partly sufficient only with no plan, no record and
-        code's narrowing decision of partly sufficient stored (a done 'narrowing' stage result); level 1."""
-        self.narrowing(rid)
+        code's narrowing decision of partly sufficient stored (a done 'narrowing' stage result); level 1.
+        The decision stores a narrower plan (default empty) and the source versions its counts were taken
+        on (default this world's of `sources`), which a narrower question's plan must match (fix round 1)."""
+        self.narrowing(rid, output={"narrower_plan": narrower_plan or {}, "sources": self.counted(sources)})
         self.complete(rid, "partly_sufficient", level=1)
 
-    def narrowing(self, rid, result="partly_sufficient"):
+    def counted(self, sources):
+        """The narrowing decision's 'sources': each source key with its version's fingerprint."""
+        return [{"source": k, "version_fingerprint": self.val("SELECT fingerprint FROM source_version WHERE id = :v",
+                                                              v=self.version[k])} for k in sources]
+
+    def narrowing(self, rid, result="partly_sufficient", output=None):
         """Code's narrowing decision (step 8b): a done 'narrowing' stage result with its result."""
         sid = self.stage(rid, "narrowing", None)
         self.run_sql("UPDATE stage_result SET status = 'done', finished_at = now(), "
-                     "output = CAST(:o AS jsonb) WHERE id = :s", o=f'{{"result": "{result}"}}', s=sid)
+                     "output = CAST(:o AS jsonb) WHERE id = :s", o=json.dumps({"result": result, **(output or {})}),
+                     s=sid)
         return sid
 
     def fail(self, rid, reason="worker stopped"):
diff --git a/tests/test_access_dispatch.py b/tests/test_access_dispatch.py
index 195fde3..5341011 100644
--- a/tests/test_access_dispatch.py
+++ b/tests/test_access_dispatch.py
@@ -217,17 +217,35 @@ def _outcome(read):
         return ("denied", denied.code)
 
 
-def test_a_rules_lock_committed_while_a_read_waits_closes_the_planner(engine):
-    world = aw.build(engine, "before_lock")
-    planner = bind(engine, world.run, world.settings["planner"])
+@pytest.mark.parametrize("run_kind", ["narrower_question", "ordinary"])
+def test_a_rules_lock_committed_while_a_read_waits_closes_the_planner(engine, run_kind):
+    """Step 8b fix round 1: the access fixture's main run is a narrower question's, whose plan must be the narrower
+    plan its original stored (0006); the lock inserts that plan. The same race on an ordinary run (any plan) keeps
+    the common path covered."""
+    if run_kind == "narrower_question":
+        world = aw.build(engine, "before_lock")
+        run_id, content = world.run, aw.planted_plan()
+        planner = bind(engine, run_id, world.settings["planner"])  # bound before the lock, as a running call is
+        read = lambda: role_input(planner)  # noqa: E731
+    else:
+        from model_builder import World
+        w = World(engine)
+        run_id = w.running(agents=True)
+        assert w.val("SELECT h.narrower_of_run_id FROM run r JOIN hypothesis_version hv ON hv.id = "
+                     "r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r",
+                     r=run_id) is None
+        planner, content = bind(engine, run_id, w.agent_setting("planner")), {}
+        read = lambda: planner.get("claim")  # noqa: E731
 
     def rules_lock(conn):
-        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=world.run))
+        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id))
         conn.execute(text("INSERT INTO plan (run_id, content, fingerprint, sufficiency_option, min_records, "
-                          "min_alloys, min_groups, min_resid_df) VALUES (:r, '{}', :fp, 'fixed_minimum', 4, 1, 2, 1)"),
-                     dict(r=world.run, fp=aw.FP))
+                          "min_alloys, min_groups, min_resid_df) VALUES (:r, CAST(:c AS jsonb), :fp, 'fixed_minimum', "
+                          "4, 1, 2, 1)"), dict(r=run_id, c=__import__("json").dumps(content), fp=aw.FP))
 
-    assert _race(engine, engine.test_url, lambda: role_input(planner), rules_lock) == ("denied", "stage_mismatch")
+    assert _race(engine, engine.test_url, read, rules_lock) == ("denied", "stage_mismatch")
+    with engine.connect() as conn:
+        assert conn.execute(text("SELECT count(*) FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar() == 1
 
 
 def test_a_freeze_committed_while_reads_wait_closes_the_critic_and_opens_the_analyst(engine):
diff --git a/tests/test_access_layer.py b/tests/test_access_layer.py
index 285964b..e1431b2 100644
--- a/tests/test_access_layer.py
+++ b/tests/test_access_layer.py
@@ -323,7 +323,8 @@ def test_experiment_flags_relax_nothing(engine):
     world = aw.build(engine, "queued")
     w = world.w
     vid = w.val("SELECT hypothesis_version_id FROM run WHERE id = :r", r=world.run)
-    flagged = aw.val(w, "INSERT INTO run (hypothesis_version_id, experiment_flags) VALUES (:v, :j_f) RETURNING id",
+    flagged = aw.val(w, "INSERT INTO run (hypothesis_version_id, fixed_plan, experiment_flags) "
+                              "VALUES (:v, true, :j_f) RETURNING id",  # a narrower question's run (0006)
                      v=vid, j_f={"relax_access": True, "access": "all", "unlock": ["planner", "critic"]})
     w.run_sql("INSERT INTO run_source (run_id, source_id, source_version_id, search_status) "
               "VALUES (:r, :s, :sv, 'pending')", r=flagged, s=w.source["mpea"], sv=w.version["mpea"])
diff --git a/tests/test_access_projected.py b/tests/test_access_projected.py
index e9ff643..528d220 100644
--- a/tests/test_access_projected.py
+++ b/tests/test_access_projected.py
@@ -162,7 +162,10 @@ def test_the_planted_values_are_stored_everywhere_they_should_be(engine):
         assert count("SELECT count(*) FROM tag_value WHERE value LIKE :v AND status = 'proposed'") == 1
         assert count("SELECT count(*) FROM source WHERE address LIKE :v") == 1
         assert count("SELECT count(*) FROM source_version WHERE label LIKE :v") == 1
-        assert count("SELECT count(*) FROM plan WHERE content::text LIKE :v") == 1
+        # Step 8b fix round 1 (0006): the earlier run of the same narrower question locks the same stored plan.
+        assert count("SELECT count(*) FROM plan WHERE content::text LIKE :v") == 2
+        assert conn.execute(text("SELECT count(*) FROM plan WHERE content::text LIKE :v AND run_id = :r"),
+                            dict(v=f"%{ys}%", r=world.run)).scalar() == 1
 
 
 def test_no_projected_planted_value_in_the_planners_complete_input(engine):
diff --git a/tests/test_analyst.py b/tests/test_analyst.py
index b08cef3..a1467a4 100644
--- a/tests/test_analyst.py
+++ b/tests/test_analyst.py
@@ -17,25 +17,30 @@ from stats_world import run_on, small_rows
 from hypocurate.pipeline import display
 
 # Step 8b (owner, 2026-10-07, after the live set): the facts carry display strings and ready-made phrases; the
-# number check compares tokens exactly (was: rounding to the shown precision accepted).
-FACTS = display.display({"decision": {"outcome_wording": "sufficient in the sources searched", "verdict": "supported",
-                                      "verdict_wording": "supported under the stated model, in the sources searched"},
-                         "analyses": [{"estimate": 424.93, "std_error": 64.41, "n_records": 97, "detection": 0.0465,
-                                       "largest_paper_share": 0.387,
-                                       "p_value_phrase": display.p_phrase(1.287e-06),
-                                       "paper_figures_phrase": display.figures_phrase(20, 3.9358, 0.38673, 19)}]})
-
-
-def test_the_facts_carry_display_strings_and_phrases():
+# number check compares tokens exactly (was: rounding to the shown precision accepted). Fix round 1: the function
+# that turned every float into its display string is deleted (owner); the same strings are written by the named
+# formatting functions.
+FACTS = {"decision": {"outcome_wording": "sufficient in the sources searched", "verdict": "supported",
+                      "verdict_wording": "supported under the stated model, in the sources searched"},
+         "analyses": [{"estimate": display.one_decimal(424.93), "std_error": display.one_decimal(64.41),
+                       "n_records": 97, "detection": display.percent(0.0465),
+                       "largest_paper_share": display.percent(0.387),
+                       "p_value_phrase": display.p_phrase(1.287e-06),
+                       "paper_figures_phrase": display.figures_phrase(20, 3.9358, 0.38673, 19)}]}
+
+
+def test_the_named_formatting_functions_give_the_display_strings_and_phrases():
     a = FACTS["analyses"][0]
     assert (a["estimate"], a["std_error"], a["detection"], a["largest_paper_share"]) == ("424.9", "64.4", "4.7%", "38.7%")
-    assert a["p_value_phrase"] == "p ≈ 1.3e-6 (approximate, nominal, one-sided)"
+    # Fix round 1 (owner's wording fix): no brackets, so the phrase reads the same inside parentheses.
+    assert a["p_value_phrase"] == "an approximate, nominal, one-sided p ≈ 1.3e-6"
     assert a["paper_figures_phrase"] == ("20 informative groups, an effective number of groups of 3.94, a largest "
                                          "share of 38.7% and 19 degrees of freedom")  # 'groups' (owner, 2026-10-07)
+    assert display.coefficient(424.93) == "424.9 MPa·µm^0.5" and not hasattr(display, "display")
 
 
 @pytest.mark.parametrize("phrase", [
-    "k = 424.9 ± 64.4", "97 records", "p ≈ 1.3e-6 (approximate, nominal, one-sided)", "4.7%",
+    "k = 424.9 ± 64.4", "97 records", "an approximate, nominal, one-sided p ≈ 1.3e-6", "4.7%",
     "38.7% of the slope information", "the model k × (grain size)^-1/2", "a 95% interval", "validity check 2",
     "an effective number of papers of 3.94",
 ])
@@ -329,7 +334,7 @@ def test_the_sensitivity_sets_are_labelled_with_the_per_source_function():
     assert (out["sensitivity_largest_estimate"], out["sensitivity_largest_set"]) == ("410.0 MPa·µm^0.5", "no exclusions")
     assert out["without_largest_share_estimate"] == "390.0 MPa·µm^0.5"
     assert out["without_largest_share_label"] == "in agreement with the pooled result"
-    assert out["without_largest_share_p_phrase"] == "p ≈ 3.0e-5 (approximate, nominal, one-sided)"
+    assert out["without_largest_share_p_phrase"] == "an approximate, nominal, one-sided p ≈ 3.0e-5"  # fix round 1: no brackets
 
 
 def test_a_withheld_result_gives_no_estimate_name_even_if_numbers_were_stored():
@@ -377,6 +382,13 @@ def test_no_fact_name_exposes_a_bare_p_value_or_an_individual_paper_figure(engin
     for k, v in names.items():
         if k not in phrase_names:
             assert not set(text_checks.tokens(v)) & bare, (k, v)
+    # Fix round 1 (ChatGPT's finding 4): the earlier version of this test missed the informative-group count, which
+    # the group minimum's count ('count_groups', with 'met_groups') exposed on its own. No name carries the count of
+    # informative groups (the minimum's count) any more; the statement written by code shows the minimums.
+    assert "count_groups" not in names and "met_groups" not in names
+    informative = pooled["minimums"]["groups"]["count"]
+    assert informative == c["n_groups_informative"]
+    assert not [k for k, v in names.items() if k.startswith(("count_", "met_")) and k.endswith("groups")]
 
 
 @pytest.mark.parametrize("kind", ["exploratory", "withheld", "narrowed", "fixed wordings"])
@@ -444,7 +456,7 @@ def test_the_direction_note_is_built_from_the_sign_and_the_claims_direction(esti
 
 def test_the_plain_label_for_a_single_group_source():
     assert analyst_names.label_words({"label": "not_enough_data", "inference_reason": "insufficient_groups"}) == \
-        "too few groups to test alone"
+        "not testable alone (too few groups)"  # fix round 1 wording
     assert analyst_names.label_words({"label": "agrees"}) == "in agreement with the pooled result"
 
 
@@ -490,3 +502,16 @@ def test_the_failure_facts_of_a_corrected_attempt_are_stored(engine, stub):
                                                                       "required_missing": 0,
                                                                       "result_phrases_missing": 0}]}]
     assert "ZQDIG" not in json.dumps(stored)
+
+
+# --- finding 5 (fix round 1): answer shapes ---------------------------------------------------------------------
+
+@pytest.mark.parametrize("raw", ["", "{}", "[]", "null", "{outcome_wording", "{{outcome_wording}}", "{Outcome_wording}",
+                                 "{a.b}", "{outcome_wording} {}", "{outcome_wording} {[]}", '{"report": []}'])
+def test_an_analyst_text_of_any_shape_gets_a_code_never_an_exception(raw):
+    """The Analyst's answer is text; whatever its shape, the check returns a failure code or accepts it."""
+    from hypocurate.pipeline.agents import analyst
+    check = analyst.make_check({"analyst_facts": {"kind": "analysis", "names": {
+        "outcome_wording": "insufficient in the sources searched"}}})
+    assert check({"report": raw}) in (None, "empty", "malformed", "unknown_name", "digit_outside_placeholder",
+                                      "wording_refused", "result_phrases_missing", "numbers_unmatched")
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index 0d65b72..60d4156 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -60,7 +60,7 @@ def test_every_category_has_entries_and_keys_are_unique():
 # Step 7 completed tamu_grouping_unit, papers_independent, validity_checks, fixed_minimums,
 # grain_size_transformation_at_analysis and reference_numbers; records_without_group was open, with
 # the code failing closed until the owner decided it in step 7b (2026-10-06): applied "yes".
-PARTLY = {"constructed_test_runs"}  # step 8b: agent_models fully applied (the Planner's, Critic's and Analyst's settings)
+PARTLY = {"constructed_test_runs", "question_as_tested"}  # step 8b: agent_models fully applied (the Planner's, Critic's and Analyst's settings); fix round 1: question_as_tested (its confirmation by a person is step 10)
 
 
 def test_the_owners_eight_decisions_are_recorded_as_decided():
diff --git a/tests/test_cli_runs.py b/tests/test_cli_runs.py
index 2378e41..364f1e7 100644
--- a/tests/test_cli_runs.py
+++ b/tests/test_cli_runs.py
@@ -41,9 +41,10 @@ def hc(capsys, *argv):
 
 
 def report_of(out: str) -> dict:
-    """The run's report: the JSON after the dispatch line."""
-    first, rest = out.split("\n", 1)
-    return {**json.loads(first), "report": json.loads(rest)}
+    """The run's report: the dispatch line, then (fix round 1, decision B) the claim and the question as tested,
+    printed before the run goes on to the rules lock, then the report."""
+    first, reading, rest = out.split("\n", 2)
+    return {**json.loads(first), "reading": json.loads(reading), "report": json.loads(rest)}
 
 
 def guard_refusals(engine, run_id):
@@ -66,7 +67,8 @@ def test_14_1a_run_with_the_fixed_plan_and_show_it(engine, stub, capsys):
     pooled = next(x for x in shown["results"] if x["scope"] == "pooled")
     assert (pooled["n_records"], pooled["n_alloys"], pooled["n_groups"], pooled["resid_df"]) == (97, 22, 20, 74)
     assert round(pooled["estimate"], 1) == 424.9 and round(pooled["std_error"], 1) == 64.4
-    assert shown["explanation_label"] == "model explanation; numbers checked against the run record"
+    assert shown["explanation_label"] == ("written by a language model; values inserted from the run record; "
+                                         "narrative not verified")  # decision A (fix round 1)
     assert shown["tokens_and_cost"] is not None
 
 
@@ -102,7 +104,7 @@ def test_14_3_partly_sufficient_and_the_narrower_question_from_the_command_line(
     n = report_of(out)
     assert code == 0 and n["report"]["outcome"] == "sufficient" and n["report"]["stages"][0] == "fixed plan"
     narrower = json.loads(hc(capsys, "show", str(n["run"]))[1])
-    assert narrower["narrower_question_of"] == r["query"] and narrower["plan"] == "fixed"
+    assert narrower["narrower_question_of"] == r["query"] and narrower["plan"] == "from the narrowing decision"
 
 
 @pytest.fixture
@@ -204,3 +206,29 @@ def test_14_1_the_controlled_duplicates_in_a_marked_test_run(engine, stub, capsy
     assert once > 0 and stored > once  # kept in the store, counted once
     assert label == ["test run: includes constructed data"]
     assert any("[[ ## classification ## ]]" in r["raw"].decode() for r in stub.requests)  # the Critic was asked
+
+
+# --- decision B (owner, fix round 1): the question as tested beside the claim -----------------------------------
+
+def test_run_prints_the_claim_and_the_planners_reading_before_the_report_and_show_keeps_it(engine, stub, capsys):
+    from hypocurate.pipeline import reading
+    stub.respond(responder(planner_body()))
+    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--by", "Ada Reviewer")
+    assert code == 0, err
+    r = report_of(out)
+    assert r["reading"]["claim"] == FCC_CLAIM
+    q = r["reading"]["question_as_tested"]
+    assert q["label"] == reading.LABELS["planner"] and "test type tension (assumed" in q["text"]
+    code, out, err = hc(capsys, "show", str(r["run"]))
+    shown = json.loads(out)
+    assert shown["claim"] == FCC_CLAIM and shown["question_as_tested"] == q
+
+
+def test_a_fixed_plan_runs_reading_is_the_reference_plans(engine, stub, capsys):
+    from hypocurate.pipeline import reading
+    stub.respond(responder())
+    code, out, err = hc(capsys, "run", FCC_CLAIM, "--sources", "mpea,tamu_fcc", "--fixed-plan", "--by", "Ada Reviewer")
+    r = report_of(out)
+    assert r["reading"]["question_as_tested"]["label"] == reading.LABELS["fixed"]
+    code, out, err = hc(capsys, "show", str(r["run"]))
+    assert json.loads(out)["question_as_tested"] == r["reading"]["question_as_tested"]
diff --git a/tests/test_critic.py b/tests/test_critic.py
index 6724901..872ad00 100644
--- a/tests/test_critic.py
+++ b/tests/test_critic.py
@@ -11,6 +11,7 @@ import pytest
 from sqlalchemy import text
 
 import pipeline_world as pw
+from answer_shapes import WRONG, variants
 import stub_provider as sp
 from hypocurate.access.vocabulary import CRITIC_CLASSES
 from hypocurate.db.engine import make_engine
@@ -215,3 +216,42 @@ def test_no_decision_path_reads_the_critics_class():
     start = fields.index("def flags_full(")
     end = fields.index("\ndef ", start + 1)
     assert uses and all(start <= u < end for u in uses)
+
+
+# --- finding 5 (fix round 1): wrong-type answer shapes ---------------------------------------------------------
+
+BATCH = [{"id": 7, "kind": "values_disagree", "category": "c", "records": []},
+         {"id": 8, "kind": "values_disagree", "category": "c", "records": []}]
+VALID = {"7": {"class": "cannot_tell", "reason": "the metadata are the same"},
+         "8": {"class": "same_measurement", "reason": "same paper and alloy"}}
+
+
+@pytest.mark.parametrize("shape", [{"7": {"class": []}}, {"7": {"class": {}}}, {"7": {"class": ["cannot_tell"]}},
+                                   {"7": {"class": {"cannot_tell": 1}}}, {"7": {"class": 1}}, {"7": {"class": None}}])
+def test_a_class_of_the_wrong_type_leaves_that_entry_unclassified(shape):
+    """The reviewer's reproduction: a list or object as the class raised TypeError at the membership test."""
+    out = critic.classify(shape, BATCH)
+    assert out.accepted == {} and out.refused["7"] in ("class_not_allowed", "malformed_entry")
+    assert out.refused["8"] == "not_answered"
+
+
+def test_every_wrong_type_at_every_position_is_refused_entry_by_entry():
+    for path, value, answer in variants(VALID):
+        if not isinstance(answer, dict):
+            continue  # not a JSON object: the interface's check makes it malformed (corrected once)
+        out = critic.classify(answer, BATCH)                    # never raises
+        if not path:                                            # the whole answer replaced by another object
+            assert set(out.refused) >= {"7", "8"} and not out.accepted, value
+            continue
+        touched = str(path[0])
+        for key in ("7", "8"):
+            if key != touched:
+                assert out.accepted.get(int(key)) == (VALID[key]["class"], VALID[key]["reason"]), (path, value)
+        if touched in ("7", "8") and int(touched) not in out.accepted:
+            assert out.refused[touched], (path, value)
+
+
+def test_a_non_object_answer_is_malformed():
+    for value in WRONG:
+        if not isinstance(value, dict):
+            assert critic.check({"classification": json.dumps(value)}) == "malformed"
diff --git a/tests/test_curator.py b/tests/test_curator.py
index c493d96..f039636 100644
--- a/tests/test_curator.py
+++ b/tests/test_curator.py
@@ -17,6 +17,7 @@ from decimal import Decimal
 import pytest
 
 import stub_provider as sp
+from answer_shapes import variants
 from hypocurate.access.vocabulary import CURATION_TARGETS
 from hypocurate.pipeline.agents import quotes
 from hypocurate.pipeline.agents.settings import CURATOR_INSTRUCTION
@@ -438,3 +439,21 @@ def test_a_quote_that_fails_the_current_term_checks_is_refused_on_import(db):
     doc["values"]["test_temperature_band"] = {**doc["values"]["phase_class"], "value": "room temperature",
                                               "term": "room temperature"}
     refused_everywhere(db, {**dict(base.files), CURATION_PATH: encode(doc)})
+
+
+# --- finding 5 (fix round 1): wrong-type answer shapes ---------------------------------------------------------
+
+def test_every_wrong_type_at_every_position_is_refused_entry_by_entry():
+    """Each target's entry of the wrong shape or type is refused with its code (never an exception); the
+    Curator's answer was already safe here, and stays so."""
+    from hypocurate.access.vocabulary import CURATION_TARGETS
+    from hypocurate.pipeline.agents import curator
+    docs = {"documentation/main.tex": "Quasistatic tensile testing was used.\nThe alloys are FCC.\n"}
+    valid = {f: "not stated" for f in CURATION_TARGETS}
+    valid["test_type"] = {"value": "tension", "quote": "Quasistatic tensile testing was used."}
+    for path, value, answer in variants(valid):
+        if not isinstance(answer, dict):
+            assert curator.check({"proposals": json.dumps(answer)}) == "malformed"
+            continue
+        proposals, _ = curator.proposals_from(json.dumps(answer), docs)
+        assert {p.status for p in proposals} <= {"not_stated", "refused", "proposed"}, (path, value)
diff --git a/tests/test_migrations_step8b.py b/tests/test_migrations_step8b.py
index 012b3c4..58fc1bf 100644
--- a/tests/test_migrations_step8b.py
+++ b/tests/test_migrations_step8b.py
@@ -60,7 +60,9 @@ def test_0006_replaces_no_earlier_function():
 
 @pytest.mark.parametrize("table, earlier", [("hypothesis_version", "hc_version_insert"),
                                             ("hypothesis_version", "hc_version_update"),
-                                            ("plan", "hc_plan_insert"), ("run", "hc_run_update")])
+                                            ("plan", "hc_plan_insert"), ("run", "hc_run_update"),
+                                            ("run", "hc_run_insert")])
+# (run UPDATE also covers hc_run_update_statement_version, fix round 1)
 def test_each_new_trigger_fires_after_the_earlier_one_on_its_table(table, earlier):
     """PostgreSQL fires BEFORE triggers in name order: 0001's messages keep their priority."""
     names = [t for tb, _, t, _ in m0006().CHECKED if tb == table and t.startswith(earlier)]
@@ -277,3 +279,123 @@ def test_a_reason_needs_a_class(w):
 def test_a_class_without_a_reason_is_allowed(w):
     _, fid = a_flag(w)
     w.run_sql("UPDATE flag SET critic_class = 'cannot_tell', classified_at = now() WHERE id = :f", f=fid)
+
+
+# --- a narrower question's run (fix round 1, finding 1; owner F-Q1: the backstop is in 0006) -------------------
+
+BODY = {"model": "hall_petch", "scope": {"phase_class": ["FCC"]}, "alpha": 0.05}
+
+
+def narrower_version(w, original):
+    """A dispatched version of a narrower question of `original` (same sources as the world's runs)."""
+    return w.dispatched(hypothesis=w.hypothesis(narrower_of=original), number=1)
+
+
+def partly_original(w, body=BODY, sources=("mpea", "tamu_fcc")):
+    rid = w.running()
+    w.partly(rid, narrower_plan=body, sources=sources)
+    return rid
+
+
+def test_a_narrower_questions_run_must_use_the_stored_plan(w):
+    vid = narrower_version(w, partly_original(w))
+    w.rejected("INSERT INTO run (hypothesis_version_id, fixed_plan) VALUES (:v, false)",
+               "a narrower question's run uses the plan stored by its original's narrowing decision", v=vid)
+    rid = w.run(vid=vid)
+    assert w.val("SELECT fixed_plan FROM run WHERE id = :r", r=rid) is True
+
+
+def test_a_narrower_questions_plan_equal_to_the_stored_narrower_plan_is_locked(w):
+    vid = narrower_version(w, partly_original(w))
+    rid = w.running(vid=vid)
+    w.lock(rid, content={"hypothesis_version": vid, **BODY})
+    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1
+
+
+@pytest.mark.parametrize("content", [{}, {"model": "hall_petch", "scope": {"phase_class": ["BCC"]}, "alpha": 0.05},
+                                     {"hypothesis_version": 0, **BODY, "alpha": 0.1}])
+def test_a_narrower_questions_plan_other_than_the_stored_one_is_refused(w, content):
+    vid = narrower_version(w, partly_original(w))
+    rid = w.running(vid=vid)
+    with pytest.raises(IntegrityError, match="is the narrower plan stored by its original's narrowing decision"):
+        w.lock(rid, content=content)
+
+
+def test_a_narrower_questions_plan_is_refused_when_the_original_stored_no_narrower_plan(w):
+    original = w.running()
+    w.narrowing(original, output={"sources": w.counted(("mpea", "tamu_fcc"))})
+    w.complete(original, "partly_sufficient", level=1)
+    vid = narrower_version(w, original)
+    rid = w.running(vid=vid)
+    with pytest.raises(IntegrityError, match="is the narrower plan stored by its original's narrowing decision"):
+        w.lock(rid, content={"hypothesis_version": vid, **BODY})
+
+
+@pytest.mark.parametrize("counted", ["other_fingerprint", "fewer_sources"])
+def test_a_narrower_questions_plan_is_refused_on_other_source_versions(w, counted):
+    """B1 at the database: the run's source versions are those the original's narrowing counts were taken on."""
+    original = w.running()
+    sources = w.counted(("mpea", "tamu_fcc"))
+    if counted == "other_fingerprint":
+        sources[0]["version_fingerprint"] = "f" * 64
+    else:
+        sources = sources[:1]
+    w.narrowing(original, output={"narrower_plan": BODY, "sources": sources})
+    w.complete(original, "partly_sufficient", level=1)
+    vid = narrower_version(w, original)
+    rid = w.running(vid=vid)
+    with pytest.raises(IntegrityError, match="the source versions its original's narrowing counts were taken on"):
+        w.lock(rid, content={"hypothesis_version": vid, **BODY})
+
+
+def test_the_source_versions_are_compared_whatever_their_stored_order(w):
+    original = w.running()
+    w.narrowing(original, output={"narrower_plan": BODY, "sources": w.counted(("tamu_fcc", "mpea"))})
+    w.complete(original, "partly_sufficient", level=1)
+    vid = narrower_version(w, original)
+    rid = w.running(vid=vid)
+    w.lock(rid, content={"hypothesis_version": vid, **BODY})
+    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1
+
+
+def test_an_ordinary_runs_plan_is_unaffected_by_the_narrower_rule(w):
+    rid = w.running()
+    assert w.val("SELECT fixed_plan FROM run WHERE id = :r", r=rid) is False
+    w.lock(rid, content={"anything": 1})
+    assert w.val("SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 1
+
+
+# --- the statement's format version on the run (fix round 1, owner 2026-10-07) -----------------------------------
+
+def test_the_format_version_is_recorded_only_in_the_update_that_completes_the_run(w):
+    rid = w.running()
+    w.rejected("UPDATE run SET statement_format_version = 1 WHERE id = :r",
+               "the statement format version is recorded when the run completes", r=rid)
+    w.narrowing(rid)
+    w.run_sql("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
+              "evidence_level = 1, statement_format_version = 1 WHERE id = :r", r=rid)
+    assert w.val("SELECT statement_format_version FROM run WHERE id = :r", r=rid) == 1
+    w.rejected("UPDATE run SET statement_format_version = 2 WHERE id = :r", "a completed run is final", r=rid)  # 0001
+
+
+def test_a_run_completed_without_a_format_version_keeps_none(w):
+    """The previous release's code completes runs without it (0006 keeps working with it): the statement then says
+    the version was not recorded."""
+    rid = w.running()
+    w.partly(rid)
+    assert w.val("SELECT statement_format_version FROM run WHERE id = :r", r=rid) is None
+    w.rejected("UPDATE run SET statement_format_version = 1 WHERE id = :r", "a completed run is final", r=rid)  # 0001
+
+
+def test_a_failed_run_never_gets_a_format_version(w):
+    rid = w.running()
+    w.rejected("UPDATE run SET status = 'failed', failed_at = now(), failure_reason = 'x', statement_format_version = 1 "
+               "WHERE id = :r", "the statement format version is recorded when the run completes", r=rid)
+
+
+def test_the_format_version_is_positive(w):
+    rid = w.running()
+    w.narrowing(rid)
+    with pytest.raises(IntegrityError, match="ck_run_statement_format_version"):
+        w.run_sql("UPDATE run SET status = 'completed', completed_at = now(), outcome = 'partly_sufficient', "
+                  "evidence_level = 1, statement_format_version = 0 WHERE id = :r", r=rid)
diff --git a/tests/test_orchestrator.py b/tests/test_orchestrator.py
index ada84e5..ddac5ee 100644
--- a/tests/test_orchestrator.py
+++ b/tests/test_orchestrator.py
@@ -33,6 +33,12 @@ def planner_body(**over):
          "stated": {"alloy_class": True, "phase_class": True, "test_type": False, "temperature_band": False},
          "outcome": "yield_strength", "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1}], "narrower": None}
     b.update(over)
+    # Fix round 1 (owner's decision B): a part marked defaulted must hold the default, so a scope part that differs
+    # from the default is marked as stated by the claim (unless a test gives the marks).
+    if "stated" not in over:
+        from hypocurate.pipeline.agents.planner import DEFAULT_SCOPE
+        b["stated"] = {k: v or sorted(map(str, b["claim_scope"][k])) != sorted(map(str, DEFAULT_SCOPE[k]))
+                       for k, v in b["stated"].items()}
     return b
 
 
@@ -231,6 +237,83 @@ def test_b1_a_narrower_question_on_other_source_versions_is_refused_with_a_reaso
     assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=narrower) == 0
 
 
+def narrower_version(engine, stub):
+    """A partly-sufficient original run through the orchestrator, and its narrower question's version (confirmed)."""
+    stub.respond(responder(PARTLY))
+    report = run(engine, dispatched(engine, claim=PARTLY_CLAIM), stub)
+    vid = queries.submitted_version(engine, report.narrower_question)
+    queries.confirm_domain(engine, vid, by="Ada Reviewer")
+    return report.run_id, vid
+
+
+def test_finding_1_a_narrower_question_dispatched_with_default_arguments_locks_its_stored_plan(engine, stub):
+    original, vid = narrower_version(engine, stub)
+    narrower = queries.dispatch(engine, vid)
+    out = run(engine, narrower, stub)
+    assert (out.status, out.outcome) == ("completed", "sufficient")
+    stored = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'narrowing'", r=original)
+    assert one(engine, "SELECT content FROM plan WHERE run_id = :r", r=narrower) == {"hypothesis_version": vid,
+                                                                                   **stored["narrower_plan"]}
+    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=narrower) == 0
+
+
+def test_finding_1_default_dispatch_after_a_newer_source_version_is_refused_with_a_reason(engine, stub):
+    _, vid = narrower_version(engine, stub)
+    seal_new_version(engine, "mpea")
+    narrower = queries.dispatch(engine, vid)
+    out = run(engine, narrower, stub)
+    assert out.status == "failed" and out.failure.startswith("narrowing_sources_changed:")
+    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=narrower) == 0
+    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=narrower) == 0
+
+
+def test_finding_1_the_orchestrator_reads_the_narrower_link_not_the_runs_flag(engine, stub):
+    """Code alone, with the database's rule switched off for this test: a narrower question's run recorded
+    without the flag still never reaches the Planner, and still gets the source-version check (B1)."""
+    _, vid = narrower_version(engine, stub)
+    seal_new_version(engine, "mpea")
+    with engine.begin() as conn:
+        conn.execute(text("ALTER TABLE run DISABLE TRIGGER hc_run_insert_narrower"))
+    try:
+        narrower = queries.dispatch(engine, vid)
+        with engine.begin() as conn:
+            conn.execute(text("SET LOCAL session_replication_role = replica"))
+            conn.execute(text("UPDATE run SET fixed_plan = false WHERE id = :r"), dict(r=narrower))
+    finally:
+        with engine.begin() as conn:
+            conn.execute(text("ALTER TABLE run ENABLE TRIGGER hc_run_insert_narrower"))
+    assert one(engine, "SELECT fixed_plan FROM run WHERE id = :r", r=narrower) is False
+    out = run(engine, narrower, stub)
+    assert out.status == "failed" and out.failure.startswith("narrowing_sources_changed:")
+    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=narrower) == 0
+
+
+def test_decision_b_prepare_stops_before_the_lock_with_the_question_as_tested(engine, stub):
+    """What the command line prints between its two calls: the run is prepared and nothing is locked yet."""
+    stub.respond(responder(planner_body()))
+    rid = dispatched(engine)
+    prepared = orchestrator.prepare(engine, rid, client_options=sp.client_options(stub))
+    assert prepared.ready and prepared.status == "running"
+    assert prepared.question_as_tested["source"] == "planner"
+    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
+    rest = orchestrator.proceed(engine, rid, client_options=sp.client_options(stub))
+    assert (rest.status, rest.outcome) == ("completed", "sufficient") and rest.stages[0] == "rules lock"
+
+
+@pytest.mark.parametrize("planner_done", [False, True])
+def test_proceed_builds_the_plan_only_after_a_narrowing_decision_to_proceed(engine, stub, planner_done):
+    """Without a stored Planner answer, or with one but no narrowing decision to proceed, `proceed` locks nothing."""
+    from hypocurate.pipeline.agents import planner
+    stub.respond(responder(planner_body()))
+    rid = dispatched(engine)
+    queries.start(engine, rid)
+    if planner_done:
+        assert planner.run_planner(engine, rid, client_options=sp.client_options(stub)).failure is None
+    out = orchestrator.proceed(engine, rid, client_options=sp.client_options(stub))
+    assert out.status == "failed" and out.failure.startswith("refused: ")
+    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
+
+
 # --- the failure table ----------------------------------------------------------------------------------
 
 def test_b2_the_analyst_failing_on_the_partly_path_still_completes_and_creates_the_narrower_question(engine, stub):
@@ -242,6 +325,50 @@ def test_b2_the_analyst_failing_on_the_partly_path_still_completes_and_creates_t
     assert one(engine, "SELECT status FROM stage_result WHERE run_id = :r AND stage = 'analyst'", r=rid) == "failed"
 
 
+@pytest.mark.parametrize("failure", ["recording_failed", "reservation_failed"])
+def test_finding_3_an_accounting_failure_at_the_planner_stops_the_run_open(engine, stub, monkeypatch, failure):
+    from hypocurate.pipeline.agents import spend
+
+    def broken(*a, **kw):
+        raise RuntimeError("database gone")
+
+    stub.respond(responder(planner_body()))
+    rid = dispatched(engine)
+    monkeypatch.setattr(spend, "finish" if failure == "recording_failed" else "reserve", broken)
+    report = run(engine, rid, stub)
+    assert report.status == "running" and report.failure.startswith(f"{failure}: ")
+    assert len(stub.requests) == (1 if failure == "recording_failed" else 0)
+    assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND stage = 'narrowing'", r=rid) == 0
+    assert one(engine, "SELECT count(*) FROM plan WHERE run_id = :r", r=rid) == 0
+
+
+@pytest.mark.parametrize("failure", ["recording_failed", "reservation_failed"])
+def test_finding_3_an_accounting_failure_at_the_analyst_on_the_partly_path_creates_no_narrower_question(
+        engine, stub, monkeypatch, failure):
+    """B2's exception: the partly-sufficient run is not completed and no narrower question is created; the run
+    stays running for recovery."""
+    from hypocurate.pipeline.agents import spend
+    name = "finish" if failure == "recording_failed" else "reserve"
+    real = getattr(spend, name)
+
+    def broken_for_the_analyst(db, *a, **kw):
+        with db.connect() as conn:
+            role = conn.execute(text("SELECT role FROM stage_result WHERE status = 'running' ORDER BY id DESC "
+                                     "LIMIT 1")).scalar()
+        if role == "analyst":
+            raise RuntimeError("database gone")
+        return real(db, *a, **kw)
+
+    monkeypatch.setattr(spend, name, broken_for_the_analyst)
+    stub.respond(responder(PARTLY))
+    rid = dispatched(engine, claim=PARTLY_CLAIM)
+    report = run(engine, rid, stub)
+    assert report.status == "running" and report.failure.startswith(f"{failure}: ")
+    assert report.narrower_question is None
+    assert one(engine, "SELECT count(*) FROM hypothesis WHERE narrower_of_run_id = :r", r=rid) == 0
+    assert one(engine, "SELECT outcome FROM run WHERE id = :r", r=rid) is None
+
+
 def test_a3_a_spending_refusal_at_the_analyst_leaves_codes_decision_standing(engine, stub):
     from decimal import Decimal
     stub.respond(responder())
@@ -280,18 +407,6 @@ def test_a_run_fails_before_the_lock_with_a_stated_reason(engine, stub, answer,
     assert one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r AND status = 'running'", r=rid) == 0
 
 
-def test_a_critic_failure_leaves_flags_unclassified_and_the_run_goes_on(engine, stub):
-    def respond(raw):
-        if "[[ ## classification ## ]]" in raw:
-            return sp.reply(sp.fields(classification="prose, not JSON"))
-        return responder()(raw)
-    stub.respond(respond)
-    rid = dispatched(engine, fixed_plan=True)
-    report = run(engine, rid, stub)
-    assert (report.status, report.outcome) == ("completed", "sufficient")
-    assert one(engine, "SELECT count(*) FROM flag WHERE run_id = :r AND critic_class IS NOT NULL", r=rid) == 0
-
-
 def test_no_model_call_is_made_while_a_database_transaction_is_open(migrated_database, stub):
     """For every role: while the stub serves a request, the run's connections hold no open transaction. (Small
     data with invalid values, so the Critic has flags to classify; the reference data raise none.)"""
diff --git a/tests/test_planner_narrowing.py b/tests/test_planner_narrowing.py
index 8e0891e..afccfce 100644
--- a/tests/test_planner_narrowing.py
+++ b/tests/test_planner_narrowing.py
@@ -8,6 +8,7 @@ import pytest
 from sqlalchemy import text
 
 import pipeline_world as pw
+from answer_shapes import variants
 import stub_provider as sp
 from hypocurate.db.engine import make_engine
 from hypocurate.pipeline import completion, narrowing, queries
@@ -35,6 +36,12 @@ def body(**over):
          "stated": {"alloy_class": True, "phase_class": True, "test_type": False, "temperature_band": False},
          "outcome": "yield_strength", "exclusion_rules": [{"rule": "grain_size_range", "min": 0.1}], "narrower": None}
     b.update(over)
+    # Fix round 1 (owner's decision B): a part marked defaulted must hold the default, so a scope part that differs
+    # from the default is marked as stated by the claim (unless a test gives the marks).
+    if "stated" not in over:
+        from hypocurate.pipeline.agents.planner import DEFAULT_SCOPE
+        b["stated"] = {k: v or sorted(map(str, b["claim_scope"][k])) != sorted(map(str, DEFAULT_SCOPE[k]))
+                       for k, v in b["stated"].items()}
     return b
 
 
@@ -344,3 +351,66 @@ def test_an_answer_without_the_stated_marks_is_invalid():
     del b["stated"]
     with pytest.raises(planner.AnswerInvalid):
         planner.read_answer(b)
+
+
+# --- finding 5 (fix round 1): wrong-type answer shapes ---------------------------------------------------------
+
+FULL = body(narrower={"phase_class": ["FCC"], "test_type": ["tension"], "temperature_band": [RT]},
+            exclusion_rules=[{"rule": "grain_size_range", "min": 0.1}, {"rule": "temperature_range", "min": 10.0,
+                                                                         "max": 30.0},
+                             {"rule": "phase", "values": ["FCC"]}, {"rule": "test_type", "values": ["tension"]}])
+
+
+def test_every_wrong_type_at_every_position_is_refused_by_the_planners_check():
+    """The reviewer's shape: a list or object where a rule name is expected raised TypeError at a membership
+    test. Every variant is now either still a valid answer or refused with the check's own code."""
+    check = planner.make_check(1, "fixed_minimum", {MPEA_CLASS})
+    assert check({"plan": json.dumps(FULL)}) is None
+    for path, value, answer in variants(FULL):
+        assert check({"plan": json.dumps(answer)}) in (None, "invalid_plan", "malformed"), (path, value)
+
+
+@pytest.mark.parametrize("value", [[], {}, ["grain_size_range"], {"grain_size_range": 1}])
+def test_an_exclusion_rule_name_of_the_wrong_type_is_an_invalid_plan(value):
+    check = planner.make_check(1, "fixed_minimum", {MPEA_CLASS})
+    answer = body(exclusion_rules=[{"rule": value, "min": 0.1}])
+    assert check({"plan": json.dumps(answer)}) == "invalid_plan"
+
+
+# --- decision B (owner, fix round 1): the Planner's reading ---------------------------------------------------
+
+@pytest.mark.parametrize("part, value", [("test_type", ["compression"]), ("phase_class", ["BCC"]),
+                                         ("temperature_band", [{"band": "cryogenic", "min": -200.0, "max": -150.0}])])
+def test_a_part_marked_defaulted_must_hold_the_default(part, value):
+    """A part the Planner marks as not stated by the claim must be the profile's default; else the answer is an
+    invalid plan (corrected once)."""
+    check = planner.make_check(1, "fixed_minimum", {MPEA_CLASS})
+    stated = {"alloy_class": True, "phase_class": True, "test_type": True, "temperature_band": True, part: False}
+    answer = body(claim_scope={**body()["claim_scope"], part: value}, stated=stated)
+    assert check({"plan": json.dumps(answer)}) == "invalid_plan"
+    marked_stated = body(claim_scope={**body()["claim_scope"], part: value}, stated={**stated, part: True})
+    assert check({"plan": json.dumps(marked_stated)}) in (None, "invalid_plan")  # judged on its other merits only
+    with pytest.raises(planner.AnswerInvalid, match="marked as not stated"):
+        planner.read_answer(json.loads(json.dumps(answer)))
+
+
+def test_parts_marked_defaulted_that_hold_the_defaults_are_accepted():
+    check = planner.make_check(1, "fixed_minimum", {MPEA_CLASS})
+    stated = {"alloy_class": False, "phase_class": False, "test_type": False, "temperature_band": False}
+    assert check({"plan": json.dumps(body(stated=stated))}) is None
+    assert planner.DEFAULT_SCOPE == {"alloy_class": [MPEA_CLASS], "phase_class": ["FCC"], "test_type": ["tension"],
+                                     "temperature_band": [RT]}
+
+
+def test_the_planners_stage_stores_the_question_as_tested_labelled_as_its_reading(engine, stub):
+    from hypocurate.pipeline import reading
+    rid = running(engine)
+    stub.queue(sp.reply(answer()))
+    plan_run(engine, rid, stub)
+    out = one(engine, "SELECT output FROM stage_result WHERE run_id = :r AND stage = 'planner'", r=rid)
+    q = out["question_as_tested"]
+    assert q["label"] == reading.LABELS["planner"]
+    assert q["text"] == ("yield strength against grain size, in multi-principal-element (high-entropy) alloys "
+                         "(as the claim states); phase class FCC (as the claim states); test type tension (assumed: "
+                         "the claim does not state it); room temperature, 20 to 25 °C (assumed: the claim does not "
+                         "state it); excluding records with a grain size below 0.1 µm")
diff --git a/tests/test_queries.py b/tests/test_queries.py
index 63a339b..06c0c71 100644
--- a/tests/test_queries.py
+++ b/tests/test_queries.py
@@ -149,6 +149,20 @@ def test_the_narrower_question_is_a_separate_linked_submitted_query(engine):
     assert one(engine, "SELECT fixed_plan FROM run WHERE id = :r", r=rid) is True
 
 
+@pytest.mark.parametrize("kw", [{}, {"fixed_plan": False}])
+def test_a_narrower_question_is_dispatched_to_its_stored_plan_whatever_the_callers_flag(engine, kw):
+    """Fix round 1, finding 1: dispatch derives it from the narrower link, never from a caller's flag."""
+    q = queries.create_narrower(engine, partly(engine), NARROWER)
+    queries.confirm_domain(engine, q.version_id, by="Ada Reviewer")
+    rid = queries.dispatch(engine, q.version_id, **kw)
+    assert one(engine, "SELECT fixed_plan FROM run WHERE id = :r", r=rid) is True
+
+
+def test_an_ordinary_query_is_dispatched_to_the_planner_by_default(engine):
+    _, rid = dispatched(engine)
+    assert one(engine, "SELECT fixed_plan FROM run WHERE id = :r", r=rid) is False
+
+
 def test_a_narrower_question_needs_a_partly_sufficient_original(engine):
     _, rid = dispatched(engine)
     with pytest.raises(IntegrityError, match="partly_sufficient"):
```
## 5. Assumptions register (137 entries; 2 new, 10 changed)

### New: `question_as_tested`

```json
{
 "key": "question_as_tested",
 "name": "The question as tested, beside the claim",
 "state": "in_force",
 "statement": "Code writes the question a run tests from its scope and exclusion rules: the outcome against grain size, the alloy class, phase class, test type and temperature band with its range, and each exclusion rule. For a run with the Planner it is the Planner's reading of the claim, each part marked as the claim states it or as assumed, and is labelled 'the Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person' (owner, F-Q2: the label says what is true now; the confirmation by a person comes in step 10). Code checks only that a part marked as assumed holds the profile's default; it does not check that the reading matches the claim's words. It is stored with the Planner's stage output; for a fixed-plan run ('the fixed reference plan; not read from the claim') or a narrower question's run it is the reading of that plan, labelled as such. The command line prints it beside the original claim after the Planner and the narrowing decision and before the rules lock (`run` and `dispatch` make two guarded calls, the second rebuilding the plan from what is stored), and `show` prints it. Until step 10 no person confirms it: the run goes on to the lock without a confirmation.",
 "value": {
  "text": "code-written; labelled the Planner's reading; confirmed by a person in step 10",
  "unit": null
 },
 "category": "operational",
 "affects": "What a reader is told the run tested; how a wrong reading of the claim can be noticed.",
 "reason": "The second-model review found that claim interpretation is unchecked: a valid plan and a verdict could be attached to the wrong scientific question. Showing the reading prominently, and checking the defaulted marks, is the owner's response for sprint 1; the confirmation by a person comes with the website's rules lock.",
 "evidence": [
  "Step 8b second-model review (docs/reviews/step08b_review_chatgpt.md, 'Claim interpretation'); owner's decision B (2026-10-07)."
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
  "status": "partly",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.reading:LABELS"
   },
   {
    "ref": "python:hypocurate.pipeline.reading:question_as_tested"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.planner:DEFAULT_SCOPE"
   },
   {
    "ref": "python:hypocurate.pipeline.orchestrator:prepare"
   }
  ],
  "done": "Step 8b fix round 1: the text and label written by code, stored with the Planner's stage output, the defaulted-mark check, printed by `run`/`dispatch` before the rules lock and by `show`.",
  "pending": "A person confirms the reading at the rules lock on the website (step 10).",
  "step": 10,
  "note": null
 },
 "history": [
  {
   "value": "Code writes the question a run tests from its scope and exclusion rules: the outcome against grain size, the alloy class, phase class, test type and temperature band with its range, and each exclusion rule. For a run with the Planner it is the Planner's reading of the claim, each part marked as the claim states it or as assumed, and is labelled 'the Planner's reading of the claim; not verified by code; a person confirms it at the rules lock on the website (step 10)'. Code checks only that a part marked as assumed holds the profile's default; it does not check that the reading matches the claim's words. It is stored with the Planner's stage output; for a fixed-plan run or a narrower question's run it is the reading of that plan, labelled as such. The command line prints it beside the original claim after the Planner and the narrowing decision and before the rules lock (`run` and `dispatch` make two guarded calls, the second rebuilding the plan from what is stored), and `show` prints it. Until step 10 no person confirms it: the run goes on to the lock without a confirmation.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, F-Q2: labels say what is true in this version; no step 10 or website in the label."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_reading.py::test_the_label_says_whose_reading_it_is_and_that_a_person_confirms_it",
  "tests/test_reading.py::test_each_exclusion_rule_in_words",
  "tests/test_planner_narrowing.py::test_the_planners_stage_stores_the_question_as_tested_labelled_as_its_reading",
  "tests/test_planner_narrowing.py::test_a_part_marked_defaulted_must_hold_the_default",
  "tests/test_orchestrator.py::test_decision_b_prepare_stops_before_the_lock_with_the_question_as_tested",
  "tests/test_cli_runs.py::test_run_prints_the_claim_and_the_planners_reading_before_the_report_and_show_keeps_it",
  "tests/test_cli_runs.py::test_a_fixed_plan_runs_reading_is_the_reference_plans"
 ]
}
```
### New: `results_statement`

```json
{
 "key": "results_statement",
 "name": "The results statement written by code",
 "state": "in_force",
 "statement": "Every completed run has a short statement written by code from what code stored. It is rendered at display from the stored results (owner, 2026-10-07): a pure function of the stored rows, which never hold a record identity for it, so the same rows always give the same text whatever the record ids or their order (tested); its numbers come only from stored results and cannot change; its wording follows the statement's format version (FORMAT_VERSION, one named place), which the completing code records on the run (run.statement_format_version, set only in the update that completes the run and never changed; null for a run completed by code that did not set it) and which is shown with the statement. A change of wording is a new format version: a test pins the rendered text of every outcome kind for each version. It is present whatever happened to the Analyst and holds nothing a model wrote. It gives: the question as asked (the claim's words) and as tested (register 'question_as_tested'); the outcome and verdict wording (with the label, exploratory or 'data found; not enough to test'); the evidence level with its wording; when an estimate is shown, the model sentence, the pooled estimate with its unit, its standard error, the p-value phrase, the record and alloy counts and the four paper figures together, the direction note, the spread of the slope information ('an effective number of groups of E out of N informative groups; largest share S', always with an inference, no threshold, never compared with a minimum), the group definition, one sensitivity line (sets in agreement, range of estimates with units) and the calibration summary; a coefficient without inference is shown as the coefficient only. Below the minimums and when nothing was frozen, each count against its minimum and, per source, the records found and how many lack a grain size or a yield strength. A partly-sufficient original shows its candidate counts per part (before any eligibility decision), the narrower question's number and that a person must dispatch it. Main cautions, by fixed rules: with a verdict, always that the result is an association under the stated model in the sources searched and does not show cause; a calibration finding the method over-confident (which describes the method on data like these, not the error of this particular p-value); with a p-value only, a source or a sensitivity set not in agreement with the pooled result; an exploratory result.",
 "value": {
  "text": "code-written from stored facts; always present on a completed run",
  "unit": null
 },
 "category": "operational",
 "affects": "What every completed run says, independently of the Analyst.",
 "reason": "The second-model review (finding 4) found the Analyst's numerical guarantees stronger than its checks: numbers written in words pass. The owner put every numerical assertion in a statement written by code and labelled the Analyst's text as unverified narrative.",
 "evidence": [
  "Step 8b second-model review (docs/reviews/step08b_review_chatgpt.md); owner's decision A and F-Q2 (2026-10-07)."
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
    "ref": "python:hypocurate.pipeline.statement:build"
   },
   {
    "ref": "python:hypocurate.pipeline.statement:ASSOCIATION",
    "equals": "The result is an association under the stated model in the sources searched; it does not show cause."
   },
   {
    "ref": "python:hypocurate.pipeline.statement:OVER_CONFIDENT"
   },
   {
    "ref": "python:hypocurate.pipeline.statement:EXPLORATORY"
   },
   {
    "ref": "python:hypocurate.pipeline.statement:FORMAT_VERSION",
    "equals": 1
   },
   {
    "ref": "python:hypocurate.pipeline.statement:render"
   },
   {
    "ref": "sql:hc_run_statement_version"
   },
   {
    "ref": "sql:ck_run_statement_format_version"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "Every completed run has a short statement written by code from what code stored, built whenever it is shown (`show`), so it is present whatever happened to the Analyst and holds nothing a model wrote. It gives: the question as asked (the claim's words) and as tested (register 'question_as_tested'); the outcome and verdict wording (with the label, exploratory or 'data found; not enough to test'); the evidence level with its wording; when an estimate is shown, the model sentence, the pooled estimate with its unit, its standard error, the p-value phrase, the record and alloy counts and the four paper figures together, the direction note, the spread of the slope information ('an effective number of groups of E out of N informative groups; largest share S', always with an inference, no threshold, never compared with a minimum), the group definition, one sensitivity line (sets in agreement, range of estimates with units) and the calibration summary; a coefficient without inference is shown as the coefficient only. Below the minimums and when nothing was frozen, each count against its minimum and, per source, the records found and how many lack a grain size or a yield strength. A partly-sufficient original shows its candidate counts per part (before any eligibility decision), the narrower question's number and that a person must dispatch it. Main cautions, by fixed rules: with a verdict, always that the result is an association under the stated model in the sources searched and does not show cause; a calibration finding the method over-confident (which describes the method on data like these, not the error of this particular p-value); with a p-value only, a source or a sensitivity set not in agreement with the pooled result; an exploratory result.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07: rendered at display from stored results as a pure function; format version recorded on the run and shown; wording follows the version."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_statement.py::test_the_reference_run_s_statement",
  "tests/test_statement.py::test_the_statement_is_present_when_the_analyst_fails_and_holds_nothing_it_wrote",
  "tests/test_statement.py::test_a_planner_run_s_statement_labels_the_planner_s_reading",
  "tests/test_statement.py::test_nothing_frozen_shows_each_count_against_its_minimum_and_the_records_found_per_source",
  "tests/test_statement.py::test_partly_sufficient_shows_the_counts_per_part_and_the_narrower_question_to_dispatch",
  "tests/test_statement.py::test_the_other_kinds",
  "tests/test_statement.py::test_a_failed_run_has_no_statement",
  "tests/test_statement.py::test_the_same_stored_rows_give_the_same_text_whatever_the_record_ids",
  "tests/test_statement.py::test_the_order_of_the_stored_results_does_not_change_the_text",
  "tests/test_statement.py::test_the_facts_never_hold_the_stored_lists_of_record_ids",
  "tests/test_statement.py::test_each_completion_records_the_format_version_and_show_gives_it",
  "tests/test_statement.py::test_the_wording_of_each_format_version_is_pinned",
  "tests/test_migrations_step8b.py::test_the_format_version_is_recorded_only_in_the_update_that_completes_the_run",
  "tests/test_migrations_step8b.py::test_a_run_completed_without_a_format_version_keeps_none",
  "tests/test_migrations_step8b.py::test_a_failed_run_never_gets_a_format_version",
  "tests/test_statement.py::test_every_kind_renders_the_same_whatever_the_order_of_its_stored_lists"
 ]
}
```
### Changed: `agent_models` (as it now stands; the earlier wording is in its history)

```json
{
 "key": "agent_models",
 "name": "The model of each agent role",
 "state": "in_force",
 "statement": "Planner Claude Opus 5.5, Curator Claude Sonnet 5.5, Critic Claude Haiku 4.5, Analyst Claude Opus 5.5, each with its effort and limits set explicitly in its settings version (agent_setting, append-only). The Curator: at most 8000 output tokens (thinking included), at most 20000 characters of answer, effort medium. The Planner and the Analyst: at most 8000 output tokens, 6000 characters, effort medium. The Critic: at most 8000 output tokens, 30000 characters, at most 100 flags per call, effort low. Each role builds its request from the settings version recorded for its invocation (instruction, model, limits and options), never from the settings current when the request is made.",
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
   },
   {
    "ref": "python:hypocurate.pipeline.agents.settings:recorded"
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
  },
  {
   "value": "Planner Claude Opus 5.5, Curator Claude Sonnet 5.5, Critic Claude Haiku 4.5, Analyst Claude Opus 5.5, each with its effort and limits set explicitly in its settings version (agent_setting, append-only). The Curator: at most 8000 output tokens (thinking included), at most 20000 characters of answer, effort medium. The Planner and the Analyst: at most 8000 output tokens, 6000 characters, effort medium. The Critic: at most 8000 output tokens, 30000 characters, at most 100 flags per call, effort low.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b fix round 1 (ChatGPT review, finding 2): requests are built from the recorded settings version."
  }
 ],
 "notes": [
  "The Planner's, the Critic's and the Analyst's instruction texts and limits are drafts by Claude Code for the owner's review before the live set (B3)."
 ],
 "tests": [
  "tests/test_agent_core.py::test_the_price_table_names_the_owners_models",
  "tests/test_curator.py::test_the_curators_complete_request_is_the_instruction_the_documentation_and_the_targets",
  "tests/test_queries.py::test_dispatch_records_the_settings_version_of_each_run_role",
  "tests/test_recorded_settings.py::test_the_planner_uses_the_settings_recorded_at_dispatch",
  "tests/test_recorded_settings.py::test_the_critic_uses_the_settings_recorded_at_dispatch",
  "tests/test_recorded_settings.py::test_the_analyst_uses_the_settings_recorded_at_dispatch",
  "tests/test_recorded_settings.py::test_the_curators_request_follows_the_setting_its_invocation_records"
 ]
}
```
### Changed: `partly_sufficient_rules` (as it now stands; the earlier wording is in its history)

```json
{
 "key": "partly_sufficient_rules",
 "name": "Partly sufficient: before the lock, on counts, never tested",
 "state": "in_force",
 "statement": "A run is completed as partly sufficient only when code's narrowing decision, taken after the Planner and before any lock, finds a claim part with no record that has a grain size and the outcome at an accepted status, and the narrower scope of the parts that have such records, built by code from its counts, makes a valid plan (a narrower scope the Planner gives is stored and never used). The original then locks no plan and stores no record (the stage 'narrowed'; the database refuses a plan after such a decision and a partly-sufficient run with a plan, a record or no stored decision); the Analyst explains the narrowing facts; the decision is copied (outcome 'partly_sufficient', no verdict, level 1); the narrower question is created as a separate, linked, submitted query. If the Analyst fails for any reason but a recording or reservation failure, the run still completes as partly sufficient and the narrower question is still created; after a recording or reservation failure the run stops, stays running for recovery, and no narrower question is created.",
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
  "tests/test_orchestrator.py::test_live_run_c_the_planner_gives_no_narrower_scope_and_code_builds_it",
  "tests/test_orchestrator.py::test_finding_3_an_accounting_failure_at_the_analyst_on_the_partly_path_creates_no_narrower_question"
 ],
 "history": [
  {
   "value": "A run is completed as partly sufficient only when code's narrowing decision, taken after the Planner and before any lock, finds a claim part with no record that has a grain size and the outcome at an accepted status, and the Planner proposed exactly the narrower scope of the parts that have such records, which makes a valid plan. The original then locks no plan and stores no record (the stage 'narrowed'; the database refuses a plan after such a decision and a partly-sufficient run with a plan, a record or no stored decision); the Analyst explains the narrowing facts; the decision is copied (outcome 'partly_sufficient', no verdict, level 1); the narrower question is created as a separate, linked, submitted query. If the Analyst fails for any reason, the run still completes as partly sufficient and the narrower question is still created.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after live run C failed 'narrower_missing': code builds the narrower scope from its own counts; the Planner cannot see which part has no usable record, so a proposal of its is stored and never used."
  },
  {
   "value": "A run is completed as partly sufficient only when code's narrowing decision, taken after the Planner and before any lock, finds a claim part with no record that has a grain size and the outcome at an accepted status, and the narrower scope of the parts that have such records, built by code from its counts, makes a valid plan (a narrower scope the Planner gives is stored and never used). The original then locks no plan and stores no record (the stage 'narrowed'; the database refuses a plan after such a decision and a partly-sufficient run with a plan, a record or no stored decision); the Analyst explains the narrowing facts; the decision is copied (outcome 'partly_sufficient', no verdict, level 1); the narrower question is created as a separate, linked, submitted query. If the Analyst fails for any reason, the run still completes as partly sufficient and the narrower question is still created.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b fix round 1 (finding 3): accounting failures stop the run (B2's exception)."
  }
 ]
}
```
### Changed: `narrowing_decision` (as it now stands; the earlier wording is in its history)

```json
{
 "key": "narrowing_decision",
 "name": "The narrowing decision counts structure only",
 "state": "in_force",
 "statement": "Code's narrowing decision reads, before the lock, only counts of structure per chosen source from the sealed version recorded at dispatch (never an outcome value). Claim parts are each phase class, temperature band (with its range) and test type of the claim's scope as the Planner stated it; alloy class is not countable. A part's count is the records that have a grain size and the outcome at an accepted status, fall in that part and in the claim's values on the other dimensions, with temperature judged as eligibility rule 3 judges it. A claim with more than one alloy class, temperature band or test type is not one plan: unless the partly-sufficient path applies, the run fails before the lock with a stated reason (submit one question per band, test type and alloy class). The decision stores the counts' fingerprint and each source version's fingerprint. The narrower scope is the claim's scope less exactly the parts with no candidate record, built by code; a narrower scope the Planner gives is stored and never used (owner, 2026-10-07, after live run C). The decision also stores the Planner's mark of each scope part (stated by the claim or defaulted), which the Analyst's facts carry as notes. The counts are candidate records only: they do not show that records will survive eligibility under the locked rules, nor that the narrower question will meet the minimums.",
 "value": {
  "text": "counts per claim part; zero parts; exact narrower scope",
  "unit": null
 },
 "category": "statistical",
 "affects": "Partly sufficient and 'claim not one plan' (PRD 5.4).",
 "reason": "Owner's Q5; A11 for two bands; Claude Code extended A11 to test types and alloy classes, since a plan's tags allow one of each (stated to the owner).",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answers Q5, A11.",
  "Step 8b second-model review (docs/reviews/step08b_review_chatgpt.md); owner's decision A and F-Q2 (2026-10-07)."
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
  },
  {
   "value": "Code's narrowing decision reads, before the lock, only counts of structure per chosen source from the sealed version recorded at dispatch (never an outcome value). Claim parts are each phase class, temperature band (with its range) and test type of the claim's scope as the Planner stated it; alloy class is not countable. A part's count is the records that have a grain size and the outcome at an accepted status, fall in that part and in the claim's values on the other dimensions, with temperature judged as eligibility rule 3 judges it. A claim with more than one alloy class, temperature band or test type is not one plan: unless the partly-sufficient path applies, the run fails before the lock with a stated reason (submit one question per band, test type and alloy class). The decision stores the counts' fingerprint and each source version's fingerprint. The narrower scope is the claim's scope less exactly the parts with no usable record, built by code; a narrower scope the Planner gives is stored and never used (owner, 2026-10-07, after live run C). The decision also stores the Planner's mark of each scope part (stated by the claim or defaulted), which the Analyst's facts carry as notes.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b fix round 1 (wording correction, second-model review): the counts are candidate availability."
  }
 ]
}
```
### Changed: `narrower_question` (as it now stands; the earlier wording is in its history)

```json
{
 "key": "narrower_question",
 "name": "The narrower question and its plan",
 "state": "in_force",
 "statement": "A narrower question is a separate query linked to its original run, created as submitted with the original's domain, sources and sufficiency option, and a text built by code (NARROWER_TEXT: the original claim and the narrower scope in words). It is dispatched by its number after a named person confirms its domain; its run locks exactly the narrower plan the original's narrowing decision stored (the Planner bypassed), and is refused before the lock, with a stated reason, if any of its source versions differs from those the counts were taken on. Dispatch and the orchestrator recognise a narrower question by its link to its original (narrower_of_run_id), never by a caller's flag; the database refuses a narrower question's run without the fixed-plan flag, and refuses its plan unless it equals the stored narrower plan (less its version key) on the source versions the counts were taken on (migration 0006).",
 "value": {
  "text": "code-built text; the stored plan; same source versions",
  "unit": null
 },
 "category": "operational",
 "affects": "How a narrower question is created and run (PRD 5.4).",
 "reason": "The narrower plan is the one the counts were taken on; a fresh Planner could widen it again.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answers Q10, A8, B1.",
  "Step 8b second-model review, finding 1 (docs/reviews/step08b_review_chatgpt.md); owner's answer F-Q1 (2026-10-07)."
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
   },
   {
    "ref": "sql:hc_run_narrower"
   },
   {
    "ref": "sql:hc_plan_narrower"
   },
   {
    "ref": "python:hypocurate.pipeline.queries:dispatch"
   }
  ],
  "note": null
 },
 "notes": [],
 "tests": [
  "tests/test_queries.py::test_the_narrower_question_is_a_separate_linked_submitted_query",
  "tests/test_orchestrator.py::test_14_3_a_partly_sufficient_original_and_its_narrower_question",
  "tests/test_orchestrator.py::test_b1_a_narrower_question_on_other_source_versions_is_refused_with_a_reason",
  "tests/test_migrations_step8b.py::test_a_narrower_questions_run_must_use_the_stored_plan",
  "tests/test_migrations_step8b.py::test_a_narrower_questions_plan_other_than_the_stored_one_is_refused",
  "tests/test_migrations_step8b.py::test_a_narrower_questions_plan_is_refused_on_other_source_versions",
  "tests/test_queries.py::test_a_narrower_question_is_dispatched_to_its_stored_plan_whatever_the_callers_flag",
  "tests/test_orchestrator.py::test_finding_1_default_dispatch_after_a_newer_source_version_is_refused_with_a_reason",
  "tests/test_orchestrator.py::test_finding_1_the_orchestrator_reads_the_narrower_link_not_the_runs_flag"
 ],
 "history": [
  {
   "value": "A narrower question is a separate query linked to its original run, created as submitted with the original's domain, sources and sufficiency option, and a text built by code (NARROWER_TEXT: the original claim and the narrower scope in words). It is dispatched by its number after a named person confirms its domain; its run locks exactly the narrower plan the original's narrowing decision stored (the Planner bypassed), and is refused before the lock, with a stated reason, if any of its source versions differs from those the counts were taken on.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b fix round 1 (ChatGPT review, finding 1): the narrower path is derived from the question's link, not a flag, with a database backstop (owner's answer F-Q1: in migration 0006)."
  }
 ]
}
```
### Changed: `planner_answer` (as it now stands; the earlier wording is in its history)

```json
{
 "key": "planner_answer",
 "name": "What the Planner may answer and what code does with it",
 "state": "in_force",
 "statement": "The Planner answers one JSON object of fixed form: whether the claim belongs to the domain, the claim's scope (alloy classes, phase classes, test types, temperature bands with their ranges), and for each scope part whether the claim states it (true) or the Planner used the default (false), a mark code requires (a part marked as the default must hold the profile's default, else the answer is an invalid plan; the marks are otherwise the Planner's reading, not verified by code), the outcome field, exclusion rules from the menu, and a narrower scope that should be null (code decides any narrower scope; one given anyway is stored and never used); values from fixed lists only, no free text and no other key. Code builds the plan from the profile's defaults and only these parameters: the model, the eligibility rules, the calibration and the sufficiency option never come from the model, and of the rules only one does: for a band other than room temperature, the Planner's temperature range becomes the plan's temperature-range rule. The Planner's scope and exclusion rules decide which records are eligible. An answer whose shape, values or plan are not valid is corrected once, naming only the code, then the run fails before the lock. A claim judged to be of another domain fails the run before the lock (PRD 5.5).",
 "value": {
  "text": "fixed form; plan built by code",
  "unit": null
 },
 "category": "operational",
 "affects": "Every plan a live Planner contributes to.",
 "reason": "CLAUDE.md rule 1: code decides; agents advise. PRD 5.2: exclusion rules from a menu.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md.",
  "Step 8b second-model review (docs/reviews/step08b_review_chatgpt.md, 'Code decides'); owner's decision B and wording corrections (2026-10-07)."
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
   },
   {
    "ref": "python:hypocurate.pipeline.agents.planner:DEFAULT_SCOPE"
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
  "tests/test_planner_narrowing.py::test_an_answer_without_the_stated_marks_is_invalid",
  "tests/test_planner_narrowing.py::test_every_wrong_type_at_every_position_is_refused_by_the_planners_check",
  "tests/test_planner_narrowing.py::test_an_exclusion_rule_name_of_the_wrong_type_is_an_invalid_plan",
  "tests/test_planner_narrowing.py::test_a_part_marked_defaulted_must_hold_the_default",
  "tests/test_planner_narrowing.py::test_parts_marked_defaulted_that_hold_the_defaults_are_accepted"
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
  },
  {
   "value": "The Planner answers one JSON object of fixed form: whether the claim belongs to the domain, the claim's scope (alloy classes, phase classes, test types, temperature bands with their ranges), and for each scope part whether the claim states it (true) or the Planner used the default (false), a mark code requires, the outcome field, exclusion rules from the menu, and a narrower scope that should be null (code decides any narrower scope; one given anyway is stored and never used); values from fixed lists only, no free text and no other key. Code builds the plan from the profile's defaults and only these parameters: the model, the rules, the eligibility rules, the calibration and the sufficiency option never come from the model. An answer whose shape, values or plan are not valid is corrected once, naming only the code, then the run fails before the lock. A claim judged to be of another domain fails the run before the lock (PRD 5.5).",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b fix round 1: a part marked as the default must hold it (owner's decision B); wording corrected (second-model review: the Planner's temperature bounds enter a rule)."
  }
 ]
}
```
### Changed: `critic_classes` (as it now stands; the earlier wording is in its history)

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
  "tests/test_migrations_step8b.py::test_a_class_outside_the_list_or_an_unbounded_reason_is_refused",
  "tests/test_critic.py::test_a_class_of_the_wrong_type_leaves_that_entry_unclassified",
  "tests/test_critic.py::test_every_wrong_type_at_every_position_is_refused_entry_by_entry"
 ],
 "history": []
}
```
### Changed: `analyst_facts_only` (as it now stands; the earlier wording is in its history)

```json
{
 "key": "analyst_facts_only",
 "name": "The Analyst receives stored facts only",
 "state": "in_force",
 "statement": "The Analyst receives the claim's text, the domain, the chosen sources' names and grouping, and named facts built by code from what it stored, each a finished display string or ready-made phrase it refers to as {name}: the decision and its wordings; the plan's threshold, option and minimums; per scope part whether the claim stated it or the Planner assumed it (or that the plan was fixed); the pooled result and its counts against each minimum except the groups' (that count is of informative groups, a paper figure shown only with the other three); per source its result and label; both calibrations of the pooled result; a summary of the sensitivity sets built by code (how many; how many under each per-source label, classified against the pooled result by the same function; the sets not labelled 'agrees'; the smallest and largest estimate with their sets; the result without the group holding the largest share of slope information); the gap facts; at 'narrowed' the claim's parts, their counts and the narrower scope. The full per-set numbers are not sent (step 10 shows them in a table drawn by code). Below the minimums no name gives an estimate, a standard error, a p-value or the paper figures; the fixed-noise detection and false-positive shares, which use no outcome value, stay. It never receives a record-level value or identity, a Critic's class or reason, or a stage's text, and never sets the outcome, verdict, label or level. Owner's additions (2026-10-07): code-built sentences the Analyst uses whole: a model sentence (what was fitted, and that the estimate is its coefficient), for a fixed-plan run a sentence that the scope was set by the fixed reference plan and not read from the claim, a direction note from the estimate's sign and the claim's direction (the plan's alternative), one calibration summary covering both calibrations and their flags, and one sentence saying what a group is; plain names for the two calibrations (noise levels estimated from the data; fixed illustrative noise levels); plain wording for the four labels ('in agreement with the pooled result', 'not testable alone (too few groups)', ...); 'groups' throughout. The instruction asks the Analyst to open by restating the claim, then the outcome and verdict, then the main cautions, not with the query number, and not to draw conclusions beyond the facts and notes given. Fix round 1 (owner, F-Q2): the calibration summary describes the simulation interval once.",
 "value": {
  "text": "named stored facts; nothing outcome-derived below the minimums",
  "unit": null
 },
 "category": "data_handling",
 "affects": "What the Analyst can say (PRD 3 step 8).",
 "reason": "Owner's Q6 and standing requirement.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answer Q6.",
  "Step 8b second-model review (docs/reviews/step08b_review_chatgpt.md); owner's decision A and F-Q2 (2026-10-07)."
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
  "tests/test_analyst.py::test_the_named_formatting_functions_give_the_display_strings_and_phrases",
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
  },
  {
   "value": "The Analyst receives the claim's text, the domain, the chosen sources' names and grouping, and named facts built by code from what it stored, each a finished display string or ready-made phrase it refers to as {name}: the decision and its wordings; the plan's threshold, option and minimums; per scope part whether the claim stated it or the Planner assumed it (or that the plan was fixed); the pooled result and its counts against each minimum; per source its result and label; both calibrations of the pooled result; a summary of the sensitivity sets built by code (how many; how many under each per-source label, classified against the pooled result by the same function; the sets not labelled 'agrees'; the smallest and largest estimate with their sets; the result without the group holding the largest share of slope information); the gap facts; at 'narrowed' the claim's parts, their counts and the narrower scope. The full per-set numbers are not sent (step 10 shows them in a table drawn by code). Below the minimums no name gives an estimate, a standard error, a p-value or the paper figures; the fixed-noise detection and false-positive shares, which use no outcome value, stay. It never receives a record-level value or identity, a Critic's class or reason, or a stage's text, and never sets the outcome, verdict, label or level. Owner's additions (2026-10-07): code-built sentences the Analyst uses whole: a model sentence (what was fitted, and that the estimate is its coefficient), for a fixed-plan run a sentence that the scope was set by the fixed reference plan and not read from the claim, a direction note from the estimate's sign and the claim's direction (the plan's alternative), one calibration summary covering both calibrations and their flags, and one sentence saying what a group is; plain names for the two calibrations (noise levels estimated from the data; fixed illustrative noise levels); plain wording for the four labels ('in agreement with the pooled result', 'too few groups to test alone', ...); 'groups' throughout. The instruction asks the Analyst to open by restating the claim, then the outcome and verdict, then the main cautions, not with the query number, and not to draw conclusions beyond the facts and notes given.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b fix round 1: no separate informative-group count (finding 4); label wording and the interval described once."
  }
 ]
}
```
### Changed: `analyst_text_checks` (as it now stands; the earlier wording is in its history)

```json
{
 "key": "analyst_text_checks",
 "name": "The Analyst's number and wording checks",
 "state": "in_force",
 "statement": "The Analyst writes no digits: every number, p-value, set of paper figures, the outcome and the verdict are {name} placeholders of its named facts, and code renders the finished text. Before rendering, code refuses a name that is not among the facts given ('unknown_name'), any digit outside a placeholder ('digit_outside_placeholder'), a text that does not use {outcome_wording} (and {verdict_wording} when there is a verdict), and, when there is a verdict, a text that does not use {pooled_p_phrase} and {pooled_figures_phrase} ('result_phrases_missing'). A p-value and the paper figures exist only inside their phrase names: no other name exposes them (tested; the group minimum's count, which is the informative-group count, is no longer a name of its own). On the finished text: no forbidden phrase ('do not exist', 'proves', ...), never 'confirms the claim' or 'confirms the hypothesis' and no causal language ('causes', 'caused by', 'causal') even with a verdict, no verdict where there is none, the effective number never called 'independent', and every number one of the facts' (a safeguard). Each failure is corrected once, naming only the code; failing twice the text is discarded and the run shows 'explanation unavailable'; the stage keeps counts or rule names, never text. The finished text and its template are stored. The failure facts (counts or rule names) are stored for every attempt that failed, also when a later attempt was accepted (owner, 2026-10-07). The checks cover digits and wording only: a number written in words, or a conclusion the facts do not support, is not caught (no list of number words is kept, by the owner's decision). The stored explanation is therefore labelled 'written by a language model; values inserted from the run record; narrative not verified' and is shown separately from the statement code writes for every completed run (register 'results_statement').",
 "value": {
  "text": "numbers as given; wording rules",
  "unit": null
 },
 "category": "operational",
 "affects": "The Analyst's text (CLAUDE.md rule 13; PRD 5.9 for the Commentator later).",
 "reason": "Owner's Q8: the number check is written for reuse by the Commentator.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answer Q8.",
  "Step 8b second-model review (docs/reviews/step08b_review_chatgpt.md); owner's decision A and F-Q2 (2026-10-07)."
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
   },
   {
    "ref": "python:hypocurate.pipeline.agents.analyst:LABEL",
    "equals": "written by a language model; values inserted from the run record; narrative not verified"
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
  "tests/test_analyst.py::test_the_failure_facts_of_a_corrected_attempt_are_stored",
  "tests/test_analyst.py::test_no_fact_name_exposes_a_bare_p_value_or_an_individual_paper_figure"
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
  },
  {
   "value": "The Analyst writes no digits: every number, p-value, set of paper figures, the outcome and the verdict are {name} placeholders of its named facts, and code renders the finished text. Before rendering, code refuses a name that is not among the facts given ('unknown_name'), any digit outside a placeholder ('digit_outside_placeholder'), a text that does not use {outcome_wording} (and {verdict_wording} when there is a verdict), and, when there is a verdict, a text that does not use {pooled_p_phrase} and {pooled_figures_phrase} ('result_phrases_missing'). A p-value and the paper figures exist only inside their phrase names: no other name exposes them (tested). On the finished text: no forbidden phrase ('do not exist', 'proves', ...), never 'confirms the claim' or 'confirms the hypothesis' and no causal language ('causes', 'caused by', 'causal') even with a verdict, no verdict where there is none, the effective number never called 'independent', and every number one of the facts' (a safeguard). Each failure is corrected once, naming only the code; failing twice the text is discarded and the run shows 'explanation unavailable'; the stage keeps counts or rule names, never text. The finished text and its template are stored. The failure facts (counts or rule names) are stored for every attempt that failed, also when a later attempt was accepted (owner, 2026-10-07).",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b fix round 1 (finding 4, decision A): the label and the limits of the checks stated; count_groups removed."
  }
 ]
}
```
### Changed: `run_order_and_failures` (as it now stands; the earlier wording is in its history)

```json
{
 "key": "run_order_and_failures",
 "name": "The run order and what a failure does to a run",
 "state": "in_force",
 "statement": "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or the rules lock, records, Checks, Critic, Inclusion, dataset freeze, statistics, Analyst and the copy of code's decision. A fixed-plan run bypasses the Planner (criterion 14.1a); so does a narrower question's run, recognised by its link to its original (its stored plan). A Planner failure, a domain mismatch, a claim that is not one plan, a refused checkpoint or write, changed source versions for a narrower question, and a spending refusal at the Planner or the Critic fail the run with a stated reason. A Critic failure leaves flags unclassified and the run goes on. Any Analyst failure, a spending refusal included, leaves code's decision standing: the run completes with 'explanation unavailable' (a departure from PRD 14.4's 'marked failed' for a cap reached at the Analyst, by the owner's decision). A recording or reservation failure at any agent stops the run at once: no further model request (no further Critic batch, no Analyst), nothing more written, no narrower question created; the run stays running (a call whose recording failed stays started) until step 9's recovery. No model call runs inside a database transaction.",
 "value": {
  "text": "the step 8b run order and failure table",
  "unit": null
 },
 "category": "operational",
 "affects": "Every run's stages and endings (PRD 3, 8, 14.4).",
 "reason": "The step 8 plan's run order, corrected by the owner (A1); the failure table approved with the plan.",
 "evidence": [
  "Owner's answers in the step 8b planning and build (2026-10-07); plan file and docs/reviews/step08b_summary.md. Answers A1, A3, A11, B1, B2.",
  "Step 8b second-model review, findings 1 and 3 (docs/reviews/step08b_review_chatgpt.md)."
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
   },
   {
    "ref": "python:hypocurate.pipeline.agents.lm:RUN_STOPS",
    "equals": [
     "recording_failed",
     "reservation_failed"
    ]
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
  "tests/test_orchestrator.py::test_no_model_call_is_made_while_a_database_transaction_is_open",
  "tests/test_orchestrator_flagged.py::test_a_critic_failure_on_flagged_data_leaves_every_flag_unclassified_and_the_run_completes",
  "tests/test_orchestrator_flagged.py::test_an_accounting_failure_at_the_critic_stops_the_run_with_no_further_request",
  "tests/test_orchestrator_flagged.py::test_an_accounting_failure_at_the_analyst_stops_the_run_before_completion",
  "tests/test_orchestrator.py::test_finding_3_an_accounting_failure_at_the_planner_stops_the_run_open",
  "tests/test_orchestrator.py::test_finding_3_an_accounting_failure_at_the_analyst_on_the_partly_path_creates_no_narrower_question"
 ],
 "history": [
  {
   "value": "A run goes: Planner, narrowing decision (code), then either the partly-sufficient path or the rules lock, records, Checks, Critic, Inclusion, dataset freeze, statistics, Analyst and the copy of code's decision. A fixed-plan run bypasses the Planner (criterion 14.1a, or a narrower question's stored plan). A Planner failure, a domain mismatch, a claim that is not one plan, a refused checkpoint or write, changed source versions for a narrower question, and a spending refusal at the Planner or the Critic fail the run with a stated reason. A Critic failure leaves flags unclassified and the run goes on. Any Analyst failure, a spending refusal included, leaves code's decision standing: the run completes with 'explanation unavailable' (a departure from PRD 14.4's 'marked failed' for a cap reached at the Analyst, by the owner's decision). A call whose recording failed stays open, so the run stays running until step 9's recovery. No model call runs inside a database transaction.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b fix round 1 (ChatGPT review, findings 1 and 3): a narrower question is recognised by its link; recording and reservation failures stop the run with no further request."
  }
 ]
}
```
### Changed: `display_precision` (as it now stands; the earlier wording is in its history)

```json
{
 "key": "display_precision",
 "name": "How numbers are shown",
 "state": "in_force",
 "statement": "Numbers shown to the Analyst (and, from step 10, to people) are rounded by code in one place: k, its standard error and t to 0.1; a p-value to two significant figures (scientific notation below 0.001, e.g. 1.3e-6); counts exact; the effective number of papers to two decimals; the largest share and every other share or rate (calibration, detection, power and their intervals) as a percentage to one decimal; temperatures, scatter and shift to at most one decimal; the threshold as given; any other number to three significant figures. A p-value is shown as 'an approximate, nominal, one-sided p ≈ <value>' (no brackets, so it reads the same inside parentheses; fix round 1); the paper figures as '<n> informative papers, an effective number of papers of <e>, a largest share of <s> and <df> degrees of freedom'. Owner's additions (2026-10-07): estimates and standard errors of the coefficient carry the unit MPa·µm^0.5, scatter and shift MPa, temperatures °C; the nominal level is shown as a percentage beside the shares (5.0%), replacing the threshold shown as given; each simulation interval is shown as '<low> to <high>, a 95% simulation interval covering simulation uncertainty only'; the paper figures read 'informative groups' and 'an effective number of groups'. Every number is formatted by the named functions of pipeline/display.py; the earlier function that turned every float of the facts into a display string without its unit is deleted (fix round 1).",
 "value": {
  "text": "0.1 for k and SE; 2 significant figures for p; percentages to 0.1",
  "unit": null
 },
 "category": "operational",
 "affects": "Every number the Analyst can quote.",
 "reason": "Owner, 2026-10-07: the Analyst never rounds; code does.",
 "evidence": [
  "Register 'reference_test_tolerance' and 'reference_numbers' (k, SE, p; the approved sensitivity numbers' effective number and share). Owner's decision after the live diagnostic call, 2026-10-07.",
  "Step 8b second-model review (docs/reviews/step08b_review_chatgpt.md); owner's decision A and F-Q2 (2026-10-07)."
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
   },
   {
    "ref": "python:hypocurate.pipeline.display:p_phrase"
   }
  ],
  "note": null
 },
 "notes": [
  "All the precisions, including those drafted by Claude Code where the register was silent (other shares and rates, temperatures, scatter, shift, the fallback), were approved by the owner on 2026-10-07."
 ],
 "tests": [
  "tests/test_analyst.py::test_the_named_formatting_functions_give_the_display_strings_and_phrases",
  "tests/test_access_step8b.py::test_above_the_minimums_the_analysts_facts_carry_the_stored_estimate",
  "tests/test_analyst.py::test_the_facts_carry_the_code_built_sentences_units_and_the_nominal_level"
 ],
 "history": [
  {
   "value": "Numbers shown to the Analyst (and, from step 10, to people) are rounded by code in one place: k, its standard error and t to 0.1; a p-value to two significant figures (scientific notation below 0.001, e.g. 1.3e-6); counts exact; the effective number of papers to two decimals; the largest share and every other share or rate (calibration, detection, power and their intervals) as a percentage to one decimal; temperatures, scatter and shift to at most one decimal; the threshold as given; any other number to three significant figures. A p-value is shown as 'p ≈ <value> (approximate, nominal, one-sided)'; the paper figures as '<n> informative papers, an effective number of papers of <e>, a largest share of <s> and <df> degrees of freedom'.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Owner, 2026-10-07, after reading the first accepted live explanation: code-built sentences so the Analyst need not interpret; units; one form for rates and the threshold; interval phrases; plain names and labels; 'groups' throughout."
  },
  {
   "value": "Numbers shown to the Analyst (and, from step 10, to people) are rounded by code in one place: k, its standard error and t to 0.1; a p-value to two significant figures (scientific notation below 0.001, e.g. 1.3e-6); counts exact; the effective number of papers to two decimals; the largest share and every other share or rate (calibration, detection, power and their intervals) as a percentage to one decimal; temperatures, scatter and shift to at most one decimal; the threshold as given; any other number to three significant figures. A p-value is shown as 'p ≈ <value> (approximate, nominal, one-sided)'; the paper figures as '<n> informative papers, an effective number of papers of <e>, a largest share of <s> and <df> degrees of freedom'. Owner's additions (2026-10-07): estimates and standard errors of the coefficient carry the unit MPa·µm^0.5, scatter and shift MPa, temperatures °C; the nominal level is shown as a percentage beside the shares (5.0%), replacing the threshold shown as given; each simulation interval is shown as '<low> to <high>, a 95% simulation interval covering simulation uncertainty only'; the paper figures read 'informative groups' and 'an effective number of groups'.",
   "from": "2026-10-07",
   "to": "2026-10-07",
   "note": "Step 8b fix round 1 (owner's wording fixes): the p-value phrase without brackets; display() deleted."
  }
 ]
}
```
## 6. Mutation checks (scratch copy, PYTHONPATH; a control run with no mutation last)

```
f01      CAUGHT  1 failed, 52 passed in 14.31s
f02      CAUGHT  3 failed, 50 passed in 13.69s
f03      CAUGHT  2 failed, 51 passed in 13.90s
f04      CAUGHT  1 failed, 52 passed in 13.80s
f05      CAUGHT  3 failed, 18 passed in 14.71s
f06      CAUGHT  1 failed in 9.71s
f07      CAUGHT  1 failed, 3 passed in 10.82s
f08      CAUGHT  1 failed, 3 passed in 10.99s
f09      CAUGHT  1 failed, 3 passed in 10.73s
f10      CAUGHT  1 failed, 3 passed in 10.64s
f11      CAUGHT  2 failed, 3 passed in 11.99s
f12      CAUGHT  2 failed, 3 passed in 12.42s
f13      CAUGHT  2 failed, 3 passed in 11.99s
f14      CAUGHT  2 failed in 10.42s
f15      CAUGHT  2 failed in 9.37s
f16      CAUGHT  5 failed, 14 passed in 11.13s
f17      CAUGHT  5 failed, 44 passed in 29.87s
f18      CAUGHT  3 failed, 46 passed in 29.52s
f19      CAUGHT  2 failed, 48 passed in 50.27s
f20      CAUGHT  1 failed in 14.18s
f21      CAUGHT  1 failed, 1 passed in 14.08s
f22      CAUGHT  3 failed, 11 passed in 57.39s
f23      CAUGHT  2 failed, 12 passed in 57.99s
f24      CAUGHT  2 failed, 12 passed in 57.35s
f25      CAUGHT  2 failed, 12 passed in 57.24s
f26      CAUGHT  3 failed, 11 passed in 57.06s
f27      CAUGHT  1 failed, 13 passed in 57.01s
f28      CAUGHT  1 failed, 84 passed in 38.71s
f29      CAUGHT  2 failed, 12 passed in 130.68s (0:02:10)
f30      CAUGHT  2 failed, 83 passed in 76.34s (0:01:16)
f31      CAUGHT  3 failed, 96 passed in 139.41s (0:02:19)
f32      CAUGHT  1 failed, 10 passed in 2.27s
f33      CAUGHT  1 failed in 30.04s
f34      CAUGHT  1 failed in 21.70s
f35      SURVIVED  1 passed in 22.27s
f36      CAUGHT  1 failed in 7.61s
f37      CAUGHT  1 failed in 17.61s
f37b     CAUGHT  1 failed in 17.69s
f38      CAUGHT  2 failed, 51 passed in 19.35s
f39      CAUGHT  1 failed in 3.03s
f40      CAUGHT  1 failed in 2.74s
control  clean  138 passed in 165.83s (0:02:45)
f35      CAUGHT (re-run after the all-kinds order test was added)  1 failed, 6 passed, 14 deselected in 2.30s
```

The specification and the runner:

```python
"""Step 8b fix round 1 mutations (scratch copy, PYTHONPATH). Each: (id, file under hypocurate/, old, new, tests).
A mutation is caught when at least one named test fails."""
T = "/workspaces/hypocurate/tests/"
M06 = "db/migrations/versions/0006_query_option_and_partly_sufficient.py"
O = "pipeline/orchestrator.py"
S = "pipeline/statement.py"
MUTATIONS = [
 # finding 1: the database backstop and the derivation from the link
 ("f01", M06, "        IF NOT NEW.fixed_plan AND EXISTS (", "        IF false AND NOT NEW.fixed_plan AND EXISTS (", ["test_migrations_step8b.py"]),
 ("f02", M06, "           OR (NEW.content - 'hypothesis_version') IS DISTINCT FROM decision->'narrower_plan' THEN", "           OR false THEN", ["test_migrations_step8b.py"]),
 ("f03", M06, "        IF stored IS DISTINCT FROM current THEN", "        IF false THEN", ["test_migrations_step8b.py"]),
 ("f04", M06, "ORDER BY (e->>'source') || ' ' || (e->>'version_fingerprint'))", "ORDER BY 1)", ["test_migrations_step8b.py"]),
 ("f05", "pipeline/queries.py", "f=fixed_plan or narrower", "f=fixed_plan", ["test_queries.py", "test_orchestrator.py::test_finding_1_a_narrower_question_dispatched_with_default_arguments_locks_its_stored_plan"]),
 ("f06", O, "        if row.narrower_of_run_id is not None:\n            plan, code = _narrower_plan(engine, run_id, row.narrower_of_run_id, row.hypothesis_version_id)\n            if code:\n                return _failed(engine, report, code)\n            report.stages.append", "        if row.fixed_plan and row.narrower_of_run_id is not None:\n            plan, code = _narrower_plan(engine, run_id, row.narrower_of_run_id, row.hypothesis_version_id)\n            if code:\n                return _failed(engine, report, code)\n            report.stages.append", ["test_orchestrator.py::test_finding_1_the_orchestrator_reads_the_narrower_link_not_the_runs_flag"]),
 # finding 2: requests from the recorded settings
 ("f07", "pipeline/agents/planner.py", "s = recorded(engine, invocation)", "s = __import__('hypocurate.pipeline.agents.settings', fromlist=['x']).SETTINGS['planner']", ["test_recorded_settings.py"]),
 ("f08", "pipeline/agents/critic.py", "s = recorded(engine, invocation)", "s = __import__('hypocurate.pipeline.agents.settings', fromlist=['x']).SETTINGS['critic']", ["test_recorded_settings.py"]),
 ("f09", "pipeline/agents/analyst.py", "s = recorded(engine, invocation)", "s = __import__('hypocurate.pipeline.agents.settings', fromlist=['x']).SETTINGS['analyst']", ["test_recorded_settings.py"]),
 ("f10", "sources/curation.py", "s = recorded(engine, invocation)", "s = __import__('hypocurate.pipeline.agents.settings', fromlist=['x']).SETTINGS['curator']", ["test_recorded_settings.py"]),
 # finding 3: accounting failures stop the run
 ("f11", "pipeline/agents/critic.py", "                    or result.failure in RUN_STOPS):", "                    ):", ["test_orchestrator_flagged.py"]),
 ("f12", O, "        if stops:\n            return _stopped", "        if False:\n            return _stopped", ["test_orchestrator_flagged.py"]),
 ("f13", O, "        if _explain(engine, report, agent_kw) in RUN_STOPS:\n            return _stopped(engine, report, report.explanation_failure)\n        completion.copy_decision", "        if _explain(engine, report, agent_kw) in ():\n            return _stopped(engine, report, report.explanation_failure)\n        completion.copy_decision", ["test_orchestrator_flagged.py"]),
 ("f14", O, "                if _explain(engine, report, agent_kw) in RUN_STOPS:", "                if _explain(engine, report, agent_kw) in ():", ["test_orchestrator.py::test_finding_3_an_accounting_failure_at_the_analyst_on_the_partly_path_creates_no_narrower_question"]),
 ("f15", O, "            if result.failure in RUN_STOPS:\n                return _stopped", "            if False:\n                return _stopped", ["test_orchestrator.py::test_finding_3_an_accounting_failure_at_the_planner_stops_the_run_open"]),
 # finding 5: type before membership
 ("f16", "pipeline/agents/critic.py", "not isinstance(entry[\"class\"], str) or ", "", ["test_critic.py"]),
 ("f17", "pipeline/agents/planner.py", "    return isinstance(v, str) and v in allowed", "    return v in allowed", ["test_planner_narrowing.py"]),
 # decision B
 ("f18", "pipeline/agents/planner.py", "        if not is_stated and _sorted(scope[part]) != _sorted(DEFAULT_SCOPE[part]):", "        if False:", ["test_planner_narrowing.py"]),
 ("f19", "pipeline/agents/planner.py", "\"question_as_tested\": tested}", "}", ["test_planner_narrowing.py", "test_cli_runs.py::test_run_prints_the_claim_and_the_planners_reading_before_the_report_and_show_keeps_it"]),
 ("f20", O, "        report.ready = True\n        return _done(engine, report)", "        report.ready = True\n        return proceed(engine, run_id, **agent_kw)", ["test_orchestrator.py::test_decision_b_prepare_stops_before_the_lock_with_the_question_as_tested"]),
 ("f21", O, "    if not isinstance(stored, dict) or decided != \"proceed\":", "    if not isinstance(stored, dict):", ["test_orchestrator.py::test_proceed_builds_the_plan_only_after_a_narrowing_decision_to_proceed"]),
 # decision A: the statement and the wording fixes
 ("f22", S, "    if f[\"verdict\"]:\n        cautions.append(ASSOCIATION)", "    if False:\n        cautions.append(ASSOCIATION)", ["test_statement.py"]),
 ("f23", S, "        if _over_confident(calibration):", "        if False:", ["test_statement.py"]),
 ("f24", S, "        if inference:\n            for e in analyses:", "        if True:\n            for e in analyses:", ["test_statement.py"]),
 ("f25", S, "    if f[\"exploratory\"]:", "    if False:", ["test_statement.py"]),
 ("f26", S, "        if inference:\n            lines.append(f\"Spread", "        if False:\n            lines.append(f\"Spread", ["test_statement.py"]),
 ("f27", S, "    if run.status != \"completed\":\n        return None", "    if False:\n        return None", ["test_statement.py"]),
 ("f28", "pipeline/analyst_names.py", "            if k == \"groups\":\n                continue", "            if False:\n                continue", ["test_analyst.py"]),
 ("f29", "pipeline/analyst_names.py", "            described = True", "            described = False", ["test_statement.py"]),
 ("f30", "pipeline/display.py", "    return f\"an {P_DESCRIPTION} p ≈ {p_value(p)}\"", "    return f\"p ≈ {p_value(p)} ({P_DESCRIPTION})\"", ["test_analyst.py"]),
 ("f31", "pipeline/analyst_names.py", "TOO_FEW_GROUPS = \"not testable alone (too few groups)\"", "TOO_FEW_GROUPS = \"too few groups to test alone\"", ["test_statement.py", "test_analyst.py"]),
 ("f32", "pipeline/reading.py", "    if float(lo) == float(hi):", "    if False:", ["test_reading.py"]),
 ("f33", "cli_runs.py", "\"explanation_label\": analyst.LABEL", "\"explanation_label\": \"model explanation\"", ["test_cli_runs.py::test_14_1a_run_with_the_fixed_plan_and_show_it"]),
 ("f34", S, "    return sorted((e for e in analyses if isinstance(e, Mapping)),\n                  key=lambda e: (rank.get(e.get(\"scope\"), 3), str(e.get(\"source\") or \"\"), str(e.get(\"set\") or \"\")))", "    return [e for e in analyses if isinstance(e, Mapping)]", ["test_statement.py::test_the_order_of_the_stored_results_does_not_change_the_text"]),
 ("f35", S, "    for s in sorted(gap.get(\"sources\") or [], key=lambda s: s[\"source\"]):", "    for s in gap.get(\"sources\") or []:", ["test_statement.py::test_every_kind_renders_the_same_whatever_the_order_of_its_stored_lists"]),
 ("f36", S, "IDENTITY_KEYS = (\"records_found\",)", "IDENTITY_KEYS = ()", ["test_statement.py::test_the_facts_never_hold_the_stored_lists_of_record_ids"]),
 ("f37", "pipeline/completion.py", "x=decision[\"exploratory\"],\n                          e=decision[\"evidence_level\"], f=STATEMENT_FORMAT, r=run_id))", "x=decision[\"exploratory\"],\n                          e=decision[\"evidence_level\"], f=None, r=run_id))", ["test_statement.py::test_each_completion_records_the_format_version_and_show_gives_it"]),
 ("f37b", "pipeline/completion.py", "                     dict(e=decision[\"evidence_level\"], f=STATEMENT_FORMAT, r=run_id))", "                     dict(e=decision[\"evidence_level\"], f=None, r=run_id))", ["test_statement.py::test_each_completion_records_the_format_version_and_show_gives_it"]),
 ("f38", M06, "        IF NEW.statement_format_version IS DISTINCT FROM OLD.statement_format_version\n           AND NOT", "        IF false AND NOT", ["test_migrations_step8b.py"]),
 ("f39", S, "FORMAT_VERSION = 1", "FORMAT_VERSION = 2", ["test_statement.py::test_the_wording_of_each_format_version_is_pinned"]),
 ("f40", S, "NONE = \"Main cautions: none beyond those above.\"", "NONE = \"Main cautions: none.\"", ["test_statement.py::test_the_wording_of_each_format_version_is_pinned"]),
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
for mid, f, old, new, tests in MUTATIONS + [("control", None, None, None, ["test_analyst.py", "test_critic.py", "test_statement.py", "test_orchestrator_flagged.py", "test_recorded_settings.py", "test_reading.py"])]:
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
## 7. The suite, the images and GitHub

The whole suite on this head (locally):

```
1829 passed, 1 warning in 865.52s (0:14:25)
```

The test image, rebuilt on this head:

```
1829 passed, 1 warning in 899.21s (0:14:59)
exit 0
overlay          32G   23G  7.2G  76% /
```

The guard checks in the runtime image, rebuilt on this head:

```
no tests/ or docs/ in the image
ALL GUARD CHECKS PASSED IN THE RUNTIME IMAGE
{'statistics_libraries': ['ok'], 'refusals_after_clean_import': [], 'agent_libraries': ['ok'], 'after': ['ok', 'refused: file guard: ctypes.call_function is outside the approved inputs of pipeline code', 'refused: file guard: ctypes.dlopen is outside the approved inputs of pipeline code', 'refused: file guard: reading /tmp/tmp1c0woc9x/.env is outside the approved inputs of pipeline code']}
```

Package files in the repository and both images:

```
repo:    2c6c2bbe662095e3dd15d9b7e9b776fbab6fad987b630ba46a6ee643c42e41dc  -
runtime: 2c6c2bbe662095e3dd15d9b7e9b776fbab6fad987b630ba46a6ee643c42e41dc  -
test:    2c6c2bbe662095e3dd15d9b7e9b776fbab6fad987b630ba46a6ee643c42e41dc  -
tests/ in the test image vs the repository: identical
```

GitHub Actions on this branch:

```
(Recorded before pushing b947828, the head this packet was generated on; its own run follows that push. The two failures are the race test, fixed in 395d948.)
completed	success	Step 8b fix round 1: the statement is a pure function of stored rows,…	tests	step-08b-agents	push	37687740256	12m43s	2026-10-07T21:12:29Z
completed	success	CLAUDE.md: run the whole suite locally before every push (owner, 2026…	tests	step-08b-agents	push	37682617080	12m32s	2026-10-07T20:31:15Z
completed	failure	Step 8b fix round 1: owner's decision B (the Planner's reading: defau…	tests	step-08b-agents	push	37677014529	14m13s	2026-10-07T19:46:27Z
completed	failure	Step 8b fix round 1: finding 3 (accounting failures stop the run); a …	tests	step-08b-agents	push	37675124058	11m37s	2026-10-07T19:31:25Z
completed	success	Step 8b M10: review packet; summary points to the packet's plan section	tests	step-08b-agents	push	37667347593	11m38s	2026-10-07T18:30:22Z
completed	success	Step 8b M9: code-built sentences, units and plain wording for the Ana…	tests	step-08b-agents	push	37660998690	12m5s	2026-10-07T17:41:17Z
completed	success	Step 8b M9: remove the two word-based rules; require the pooled phras…	tests	step-08b-agents	push	37656798667	11m30s	2026-10-07T17:08:49Z
completed	success	Step 8b M9: the Analyst writes placeholders; fewer facts built by cod…	tests	step-08b-agents	push	37650754427	9m17s	2026-10-07T16:16:38Z
```
## 8. Reference comparison with `main`

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
byte-identical
4797b3c17da38ae50d9954f38406c5639992ca1097e389faae363d6f5257345f  /home/codespace/hc-work/step08b/refdump/main.json
4797b3c17da38ae50d9954f38406c5639992ca1097e389faae363d6f5257345f  /home/codespace/hc-work/step08b/fix/branch_fix.json
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
## 9. The review being answered

# Step 8b — second-model review (ChatGPT), 2026-10-07

Verdict: **not safe to merge.** Text as received by the owner and passed to Claude Code (the packet link in the
original pointed to the owner's local copy of `docs/reviews/step08b_review_packet.md`).

---

I found five issues to fix before merging. These are ordinary implementation mistakes within your stated threat model.
References below are to files quoted in the review packet (`step08b_review_packet.md`).

1. High — A narrower question can bypass its stored plan and source-version check.
   Files: pipeline/queries.py, pipeline/orchestrator.py.
   queries.dispatch() defaults to fixed_plan=False. The orchestrator checks the original’s narrower plan and source fingerprints only inside the fixed_plan branch. The CLI supplies the right flag, but the shared dispatch function does not enforce it.
   Failing sequence: create a narrower question, register a newer source version, then call queries.dispatch(engine, vid) normally. The orchestrator follows the Planner path, bypassing narrowing_sources_changed and the requirement to use the stored narrower plan.
   Fix: derive this behavior from narrower_of_run_id in dispatch and the orchestrator; do not depend on a caller remembering a flag. Add a database backstop and a regression using the default dispatch arguments.
2. High — Recorded settings need not be the settings actually used.
   Files: pipeline/agents/runstage.py, planner.py, critic.py, analyst.py.
   open_stage() records the settings version bound at dispatch. Each role then builds its request from the current global SETTINGS, rather than that recorded version.
   Failing case: dispatch a run, change an instruction or reasoning setting in a deployment, then execute the queued run. The request uses the new settings while the audit record names the old version. Keeping the model name unchanged is enough to expose this discrepancy.
   Fix: load instruction, model, limits and options from the invocation’s recorded settings. Test dispatch under version A and execution after current settings become B.
3. High — A recording or reservation failure does not stop further paid requests.
   Files: pipeline/agents/critic.py, pipeline/orchestrator.py.
   The Critic stops batching only for spending caps and ceiling_reached. It continues after recording_failed and reservation_failed. The orchestrator also treats only spending failures as terminal, so it can subsequently call the Analyst.
   Reproduced: running the actual Critic loop with two batches and mocked boundaries, either failure on the first batch caused a second call attempt.
   Keeping an unresolved reservation counted, and eventually refusing completion, does not prevent those subsequent requests.
   Fix: propagate accounting failures as run-level stops. Leave unresolved calls/runs open for recovery, with no later agent request. Test both another Critic batch and the subsequent Analyst.
4. Medium — The Analyst’s numerical guarantees are stronger than its checks.
   Files: pipeline/agents/text_checks.py, analyst.py, pipeline/analyst_names.py.
   Reproduced with the actual checker: all these pass on an insufficient run:
   - “The outcome is {outcome_wording}. The p-value is zero.”
   - “… The estimate is forty MPa.”
   - “… The estimated effect is ½ MPa.”
   These contain no decimal digits, but they plainly introduce numerical claims.
   There is also a separate phrase-only loophole: count_groups exposes the informative-group count individually. I reproduced an accepted explanation using it separately. The test claiming no individual paper figure escapes misses this name.
   Fix: put numerical assertions in code-rendered sentences and explicitly distinguish unverified model commentary. Do not try to solve this with an expanding list of number-word regexes. Either remove the separate informative-count fact or explicitly revise the phrase-only requirement. The current blanket label is not justified; “placeholder values copied from the run record; narrative not verified” is more accurate.
5. Medium — Ordinary malformed Critic JSON crashes instead of leaving an entry unclassified.
   File: pipeline/agents/critic.py.
   Reproduced: {"7": {"class": []}} and the equivalent object-valued class raise TypeError at membership testing against CRITIC_CLASSES.
   This escapes the documented per-entry failure handling and leaves the stage unfinished.
   Fix: check that the class is a string before membership testing. Add nested wrong-type cases to the role validators; the existing Critic tests cover invalid strings, but not these valid-JSON shapes.

On the remaining questions:
- Code decides: I found no decision path reading the Critic’s class or reason, or taking a verdict/evidence level from Analyst prose. The Planner legitimately affects inclusion through scope and exclusions. Its temperature bounds also populate rules[RANGE_RULE], so “no rules come from the model” needs that qualification. The fixed eligibility policy, statistical model, calibration and query sufficiency option otherwise remain outside its answer form.
- Claim interpretation remains unchecked. make_check() does not receive the claim text. A valid FCC answer to a BCC claim can pass, as can an incorrect stated/defaulted mark. Worst case: a valid computation and “supported” verdict attached to the wrong scientific question. At minimum, enforce that values marked defaulted actually equal the defaults, show the interpreted scope and exclusions prominently, and describe stated/defaulted marks as the Planner’s reading. Domain confirmation alone does not verify scope.
- Narrowing itself: the decision receives structural counts, not outcome values, and removes exactly the zero-count parts of the parsed scope. Those counts are candidate availability, not proof that records survive eligibility or meet minimums. The original’s no-plan/no-record/no-verdict path is guarded; the narrower child has finding 1.
- Facts and summaries: the normal withheld path appears to exclude outcome-derived estimates and calibration, retaining fixed-noise simulations. The sensitivity labels and calibration summary follow stored results. The direction note follows the locked alternative, which is only as faithful to the claim as the Planner’s interpretation. The live prose about a p-value being “more favourable than it really is” overstates what calibration establishes; it does not estimate this particular p-value’s error.
- Access and safeguards: I found no additional source-data disclosure in the reviewed request builders. Retries use fixed failure notes, and tools are absent in the supplied request tests. Emptying the Commentator’s lists and removing its gap-report handoff are consistent. Preloading scipy is acceptable for the explicitly limited file-guard tripwire.
- Migration and spending: 0006 is additive, with sensible rollback tests and no earlier function replacement. Its guards do not close finding 1. The existing run/month reservation lock order appears preserved. The live-set ceiling works for the supplied sequential harness; it is not an independently enforced concurrent experiment-wide cap.
- Tests: the fixture/access-test replacements generally preserve the relevant protections. But the supposed orchestrator Critic-failure test uses reference data with no flags, so it can pass without exercising a Critic failure at all. The supplied suite also misses the five cases above. Mutation-test success does not cover those omissions.

Smallest live Critic test: one capped call on a marked constructed-data run with a small flagged batch. Inspect the actual request, accepted/refused classifications and recorded cost; confirm the resulting decisions remain unchanged. No large live evaluation is needed before this limited, advisory role is used.

I reproduced the pure-checker failures and the Critic batching behavior with mocked database/provider boundaries. I did not rerun PostgreSQL, migrations, Docker, the full suite or live provider calls.

Not safe to merge.

## 10. The plan file and the scripts

### The step 8b plan file (with the fix round's answers)

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

## Fix round 1 (ChatGPT review "not safe to merge", 2026-10-07; text in docs/reviews/step08b_review_chatgpt.md)
Owner's instructions: fix findings 1–5 (each with tests failing on the current code); decision A (code-written results
statement, always present; Analyst text labelled "written by a language model; values inserted from the run record;
narrative not verified"; no number-word rules; remove count_groups or justify; fix the phrase-only test); decision B
(defaulted parts must equal the defaults; "the question as tested" stored, printed in run and show; register entry);
wording corrections (temperature bounds enter a rule; narrowing counts = candidate records; calibration ≠ error of a
particular p-value). Additions: the statement is built from the existing sentences (model, scope, direction,
calibration summary, group definition, figures phrase, p phrase); fix double brackets and "It is therefore too few
groups to test alone"; delete display.display(); housekeeping (pip-tools cache deleted; summary/packet: image rebuilt
on the final code, 1,728 tests; Docker cache corruption cleared with `docker builder prune -af`). Then: test image +
suite, reference comparison with main, fix packet, push; do not merge. One live Critic call (≤ $0.25) only with go.
- **F-Q1 (owner):** database backstop for finding 1 goes into 0006, amended in place.
Stops: F-Q2 results-statement wording and cautions list (before building A); live Critic go.
- **F-Q2 (owner, 2026-10-07): results statement approved with changes.** Concentration is a line, not a caution:
  always when there is an estimate with inference, no threshold, never compared with the minimum: "Spread of the
  slope information: an effective number of groups of E out of N informative groups; largest share S." Every
  statement starts "Question as asked:" (the claim's words), then "Question as tested:". Labels: Planner "the
  Planner's reading of the claim; not verified by code and, in this version, not confirmed by a person" (no step 10 /
  website); fixed "the fixed reference plan; not read from the claim" (no "criterion 14.1a"); drop the later scope
  sentence. Evidence level line (with wording) on every statement. With a verdict, always the caution: an
  association under the stated model in the sources searched; it does not show cause. Pooled line adds record and
  alloy counts; one sensitivity line (sets in agreement, range of estimates with units). Below the minimums and
  nothing frozen: each count against its minimum ("6 of 30 records"), and total records found per source before the
  counts lacking a field. Partly: usable-record count per part, the narrower question's number, a person must
  dispatch it. "alloys" not "alloy"; the simulation-interval description once. The other four caution rules as
  drafted (calibration, sources and sensitivity sets only with a p-value, exploratory).
```
### `~/hc-work/step08b/fix/fixpacket.py`

````python
"""Builds docs/reviews/step08b_fix_packet.md from the files on disk (run from the repository root). Every diff and
output is quoted exactly. Scratch harness; quoted in the packet's last section."""
import json
import subprocess
from pathlib import Path

HOME = Path.home() / "hc-work/step08b"
BASE = "859e019"  # the head ChatGPT reviewed (the review packet's head was 4661ce2; 859e019 added only the packet)
OUT = Path("docs/reviews/step08b_fix_packet.md")
PLAN = Path.home() / ".claude/plans/pasted-content-id-74d4-read-claude-md-replicated-iverson.md"


def sh(*cmd) -> str:
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def fence(text: str, lang: str = "") -> str:
    ticks = "````" if "```" in text else "```"
    return f"{ticks}{lang}\n{text.rstrip()}\n{ticks}\n"


def read(path) -> str:
    return Path(path).read_text(encoding="utf-8")


head = sh("git", "rev-parse", "--short", "HEAD").strip()
parts = [f"""# Build step 8b — fix packet, round 1

Date: 2026-10-07. Branch: `step-08b-agents`. Reviewed head: `{BASE}` (ChatGPT: "not safe to merge",
`docs/reviews/step08b_review_chatgpt.md`). Head when generated: `{head}`. Generated from the files on disk by a script
(`~/hc-work/step08b/fix/fixpacket.py`, quoted in the last section), so every diff and output below is quoted exactly.

Sections: 1 the fix-round summary (the first section of `docs/reviews/step08b_summary.md`); 2 the code diff since the
reviewed head; 3 new test files; 4 changed tests (diff); 5 the register changes; 6 the mutation checks; 7 the suite,
the images and GitHub; 8 the reference comparison with `main`; 9 the review text; 10 the plan file and the scripts.

"""]
summary = read("docs/reviews/step08b_summary.md")
start = summary.index("## Fix round 1")
end = summary.index("\n## ", start + 5)
parts.append("## 1. The fix round\n\n" + summary[start:end].split("\n", 1)[1] + "\n")
diff = sh("git", "diff", f"{BASE}..HEAD", "--", "hypocurate", ":(exclude)hypocurate/assumptions.json")
parts.append(f"## 2. Code diff (`{BASE}..HEAD`, the package; the register is in section 5)\n\n" + fence(diff, "diff"))
new_tests = sh("git", "diff", "--name-only", "--diff-filter=A", f"{BASE}..HEAD", "--", "tests").split()
parts.append("## 3. New test files\n\n" + "".join(
    f"### `{p}`\n\n" + (fence(read(p), "python") if p.endswith(".py") else
                        f"(data fixture, {Path(p).stat().st_size:,} bytes; not quoted)\n\n") for p in new_tests))
changed = sh("git", "diff", "--name-only", "--diff-filter=M", f"{BASE}..HEAD", "--", "tests").split()
parts.append("## 4. Changed tests and test helpers (diff)\n\n" + fence(sh("git", "diff", f"{BASE}..HEAD", "--", *changed), "diff"))
old = {e["key"]: e for e in json.loads(sh("git", "show", f"{BASE}:hypocurate/assumptions.json"))}
new = {e["key"]: e for e in json.loads(read("hypocurate/assumptions.json"))}
added = [k for k in new if k not in old]
modified = [k for k in new if k in old and new[k] != old[k]]
reg = "".join(f"### New: `{k}`\n\n" + fence(json.dumps(new[k], indent=1, ensure_ascii=False), "json") for k in added)
reg += "".join(f"### Changed: `{k}` (as it now stands; the earlier wording is in its history)\n\n"
               + fence(json.dumps(new[k], indent=1, ensure_ascii=False), "json") for k in modified)
parts.append(f"## 5. Assumptions register ({len(new)} entries; {len(added)} new, {len(modified)} changed)\n\n" + reg)
parts.append("## 6. Mutation checks (scratch copy, PYTHONPATH; a control run with no mutation last)\n\n"
             + fence(read(HOME / "mspec_fix/fix_mutations.log")) + "\nThe specification and the runner:\n\n"
             + fence(read(HOME / "mspec_fix/mutations.py"), "python") + fence(read(HOME / "mspec_fix/run_all.py"), "python"))
parts.append("## 7. The suite, the images and GitHub\n\nThe whole suite on this head (locally):\n\n"
             + fence(read(HOME / "fix/final_full.log")) + "\nThe test image, rebuilt on this head:\n\n"
             + fence(read(HOME / "fix/image_suite.log")) + "\nThe guard checks in the runtime image, rebuilt on this head:\n\n"
             + fence(read(HOME / "fix/image_guard.log")) + "\nPackage files in the repository and both images:\n\n"
             + fence(read(HOME / "fix/image_hashes.txt")) + "\nGitHub Actions on this branch:\n\n"
             + fence(read(HOME / "fix/gh_runs.txt")))
parts.append("## 8. Reference comparison with `main`\n\n" + fence(read(HOME / "fix/compare_output.txt"))
             + "\nThe comparison script:\n\n" + fence(read(HOME / "refdump/compare.py"), "python"))
parts.append("## 9. The review being answered\n\n" + read("docs/reviews/step08b_review_chatgpt.md") + "\n")
parts.append("## 10. The plan file and the scripts\n\n### The step 8b plan file (with the fix round's answers)\n\n"
             + fence(read(PLAN), "markdown") + "### `~/hc-work/step08b/fix/fixpacket.py`\n\n"
             + fence(read(HOME / "fix/fixpacket.py"), "python"))
OUT.write_text("".join(parts), encoding="utf-8")
print(f"{OUT}: {OUT.stat().st_size} bytes; head {head}")
````
