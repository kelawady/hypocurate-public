# Build step 10a — fix packet (fix round 1)

Branch `step-10a-run-pages`, head `8e55c81`. The reviewed head was `9fc3d9a` (the owner's register approval followed as `431f880`). Generated from the files on disk by a script (quoted at the end).

## 1. The owner's decision

> ChatGPT reviewed 10a: not safe to merge. I accept all four findings. Fix them on step-10a-run-pages, each with a failing test first, then write a fix packet for a short re-check. Do not merge.

> Also: in register entry 8, say that every test has its own database except the shared read-only world fixture; my approval of the 8 register entries from my earlier message stands, with your entry 4 correction and "Wording approved by the owner, 2026-10-11".

## 1a. A workflow change for the reviewer: the CI job limit, 40 to 60 minutes

The owner's decision (2026-10-11), verbatim: "Yes, raise the job limit from 40 to 60 minutes. This is my decision. Make it a single-line commit on step-10a-run-pages, changing nothing else in .github/workflows/, and note it in the fix packet so ChatGPT sees it."

Why: run 38149431419 on `9fc3d9a` (the serial suite) was green, but its suite step took 34 min 59 s and the job 36 min 27 s of the 40-minute limit; this round adds slower tests (205 runs for the list's pages; a web process started twice). The commit changes only `timeout-minutes` (one line); nothing else in `.github/workflows/`. It changes no check: Render still deploys `main` only after the checks pass. It only lets a run take longer before GitHub cancels it.

```diff
commit 8e55c81c57a2b40dd638dc3b2780178bac68c915
Author: kelawady <47933563+kelawady@users.noreply.github.com>
Date:   Sun Oct 11 15:42:52 2026 +0000

    CI: job limit 40 -> 60 minutes (owner's decision, 2026-10-11)
    
    The owner's words: "Yes, raise the job limit from 40 to 60 minutes. This is my decision." The serial suite step took
    34 min 59 s (job 36 min 27 s) on run 38149431419; fix round 1 adds slower tests. One line; nothing else in
    .github/workflows/ changes.
    
    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

diff --git a/.github/workflows/tests.yml b/.github/workflows/tests.yml
index 9334854..80d95b1 100644
--- a/.github/workflows/tests.yml
+++ b/.github/workflows/tests.yml
@@ -15,7 +15,7 @@ permissions:
 jobs:
   tests:
     runs-on: ubuntu-24.04
-    timeout-minutes: 40
+    timeout-minutes: 60
     steps:
       - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
 

```

## 2. The review (verbatim)

```
I found three code problems and one acceptance-test gap.
1. Confirmation can record wording the person never saw.
   File: hypocurate/pipeline/confirmation.py — content_fingerprint() and confirm().
   The fingerprint covers the content dictionary, while confirmation regenerates the displayed text. If a deployment changes render() between viewing and submitting, unchanged content passes the fingerprint check, but different text is stored as what the person confirmed.
   Reproduced: changing “independent groups” to “informative groups” between those operations leaves the fingerprint valid and stores the new wording.
   Smallest fix: include the rendered confirmation text in the checked fingerprint. Add a regression test changing only the renderer between display and submission. The existing tests compare against the current renderer, so they miss this.
2. Completion during a page read can produce a permanently incomplete results screen.
   Files: hypocurate/pipeline/run_view.py — run_page(); hypocurate/web/templates/run.html.
   show() reads the run first; run_page() subsequently reads its status through another connection. If the worker completes between those reads, the page combines completed status with the earlier missing statement, verdict and evidence level. The template then omits polling, leaving the page incomplete until manually refreshed.
   Reproduced: status="completed", open=False, empty statement, no outcome, and “No evidence level yet (not completed).”
   Smallest fix: obtain the displayed state from one consistent database snapshot across the helpers, or detect the status transition and rebuild the entire view. Merely sharing a connection under ordinary read-committed isolation is insufficient. Add a controlled completion-between-reads test.
3. The runs list silently hides older runs.
   Files: hypocurate/pipeline/run_view.py — runs_list(); hypocurate/web/templates/runs.html.
   The page promises “Every dispatched run,” but the query limits results to 200 and provides no pagination.
   Failing case: after 201 dispatches, the oldest run disappears from the list—even if it remains queued or waiting for confirmation.
   Smallest fix: provide pagination, or remove the limit for this sprint. Test that an older waiting run remains reachable through the list.
4. Criterion 14.4’s test does not actually restart the web service.
   File: tests/test_web_state.py — test_14_4_a_run_goes_on_to_its_end_with_the_page_closed_and_across_a_web_restart.
   The worker is a real subprocess, but del first followed by another TestClient only recreates app objects inside the test process. It neither terminates a web process nor ensures the run is still executing when the supposed restart occurs. A regression tied to web-process shutdown could pass.
   Smallest fix: hold the worker at a stub-request barrier, stop a separately launched web process, restart it, and release the worker. Check completion with one claim and no duplicate request.
I found no additional bypass in session-name handling, CSRF, cancel or web isolation by inspection. The isolation probe genuinely checks imports in a fresh process. Keeping statement format 2 for the provenance correction is defensible. No existing assertion appears weakened; SERIAL_FILES is inert. One small register correction: “every test has its own database” overlooks the intentionally shared, read-only world fixture.
Verification: reproduced findings 1–2 with isolated function probes and mocked database reads; directly ran all four extracted text-formatting tests successfully. Database integration, browser behavior and process-restart coverage were read only. The local pytest invocation crashed before producing results; I did not reproduce the full suite.
not safe to merge

```

## 3. What changed (the summary's fix-round section)


> **Update, 2026-10-11: fix round 1.** ChatGPT's review (`step10a_review_chatgpt.md`) found 10a **not safe to merge**: three code problems and one gap in a test. The owner accepted all four. Each fix came with tests written first, and those tests failed on the reviewed code where the code was at fault. The evidence is in `step10a_fix_packet.md`.
>
> | Finding | What was wrong | What changed |
> |---|---|---|
> | 1 | The confirmation fingerprint covered the content only, so a renderer changed between showing and confirming stored wording the person never saw. | `confirmation.shown_fingerprint(content, text)`: the page (field `shown_fingerprint`) and the command line send the fingerprint of the content and the exact text shown. `confirm` renders the text in its own transaction and refuses any difference, so the stored text is what was shown. |
> | 2 | The run page read the run in several transactions, so a run completing mid-read showed "completed" with no statement and stopped polling. | `run_view.snapshot`: one read-only REPEATABLE READ transaction per page. `show`, the run page, the confirmation page and the runs list read everything in it. `show`'s output is unchanged. |
> | 3 | The runs list showed at most 200 runs, with no pages. | Pages of 50 (`RUNS_PER_PAGE`), "Runs a to b of n", links to newer and older pages; a page outside the list is not found. |
> | 4 | The 14.4 test recreated app objects in the test process; it never stopped a web process. | The test now starts uvicorn as its own process, holds a worker process at its Analyst request, stops the web process, starts a new one, and releases the worker. It checks completion with one claim and one model request. |
> | Owner | — | Register entry `parallel_suite` names the one exception to a database per test: the shared read-only world fixture of `tests/test_web_runs.py`. |
>
> **Tests that failed first:** 8 failed on `431f880` (findings 1–3); a ninth, the command line's text check, was added after them. The new 14.4 test passes on the reviewed code too, as expected: finding 4 was a gap in the test, not in the code.
>
> **Reference runs:** byte-identical to `main` in all six dumps, `show`'s output included.
>
> **Register (157 entries):**
> - `confirmation_shown_fingerprint` reworded, its earlier value kept in its history;
> - `live_run_state` and `parallel_suite` corrected;
> - new: `runs_list_pages` (50 a page; Claude Code's proposal, for the owner's review).
>
> **A workflow change (owner's decision, 2026-10-11):** the CI job limit goes from 40 to 60 minutes, in a single-line commit (`8e55c81`); nothing else in `.github/workflows/` changes. Why: run 38149431419 on `9fc3d9a` (serial) was green, with the suite step at 34 min 59 s and the job at 36 min 27 s of 40.
>
> **Mutation checks:** 8 faults, all caught, each by the test written for it; the control run is clean.
>
> **The whole suite:** 2,301 tests, all passing locally on `c157f51`. It took 44 min 38 s because a stale earlier suite ran beside it for its first 13 minutes; that suite was stopped. The tests that read the workflow file pass on the job-limit commit.
>
> **The GitHub run:** see the fix packet and the owner's report.
>

## 4. Commits

```
8e55c81 CI: job limit 40 -> 60 minutes (owner's decision, 2026-10-11)
c157f51 Step 10a fix round 1, finding 1: a test of the command line's check of the text it printed
36d98ba Step 10a fix round 1: register
c163337 Step 10a fix round 1, finding 4: criterion 14.4 with a real web process stopped and restarted mid-run
d812fa3 Step 10a fix round 1, findings 1-3: fingerprint of the text shown; one snapshot per page; runs list pages

```

### d812fa3

```diff
commit d812fa349020dd485c08def3e3d529aaaad87fc9
Author: kelawady <47933563+kelawady@users.noreply.github.com>
Date:   Sun Oct 11 15:24:21 2026 +0000

    Step 10a fix round 1, findings 1-3: fingerprint of the text shown; one snapshot per page; runs list pages
    
    ChatGPT's review of 10a (all accepted by the owner, 2026-10-11). One commit: the three fixes share run_view.py and
    app.py, which cannot be split without interactive staging.
    
    1. confirmation.shown_fingerprint(content, text) replaces content_fingerprint: the page (form field
       shown_fingerprint) and the command line send the fingerprint of the content and the exact text shown; confirm
       renders the text inside its transaction and refuses any difference, so the stored text is what the person saw.
    2. run_view.snapshot: one read-only REPEATABLE READ transaction per page; show, run_page, the confirmation page and
       the runs list read everything in it (statement.build_in, critic.flag_display_in, reading.stored on the same
       connection). `show`'s output is unchanged.
    3. The runs list has pages of RUNS_PER_PAGE (50), "Runs a to b of n", newer/older links; a page outside is 404.
    
    Failing tests first (~/hc-work/step10a/fix1_before.log): 8 failed on 431f880 - the renderer-change tests (web and
    function), the fingerprint-of-text tests, completion between reads (page and fragment), the 205-runs list and the
    page words. Changed tests: the earlier fingerprint tests use shown_fingerprint(content, text) and the field name
    shown_fingerprint; the content-only fingerprint test now pins content and text together.
    
    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
---
 hypocurate/cli_runs.py                |   4 +-
 hypocurate/pipeline/agents/critic.py  |  13 ++-
 hypocurate/pipeline/confirmation.py   |  24 +++--
 hypocurate/pipeline/run_view.py       | 196 +++++++++++++++++++++-------------
 hypocurate/pipeline/statement.py      |   8 +-
 hypocurate/web/app.py                 |  16 +--
 hypocurate/web/static/style.css       |   1 +
 hypocurate/web/templates/confirm.html |   4 +-
 hypocurate/web/templates/runs.html    |  11 +-
 tests/test_confirmation_step10.py     |  60 +++++++++--
 tests/test_web_fix1.py                | 145 +++++++++++++++++++++++++
 tests/test_web_runs.py                |  16 +--
 12 files changed, 382 insertions(+), 116 deletions(-)

diff --git a/hypocurate/cli_runs.py b/hypocurate/cli_runs.py
index 2e31d42..7e9a484 100644
--- a/hypocurate/cli_runs.py
+++ b/hypocurate/cli_runs.py
@@ -172,7 +172,9 @@ def _confirm(engine: Engine, run_id: int, by: str, to_queue: bool = False) -> in
         raise queries.QueryRefused("not_waiting", f"run {run_id} is not waiting for confirmation (it is {status})")
     content, words = confirmation.show(engine, run_id)
     print(words, flush=True)
-    confirmation.confirm(engine, run_id, by, shown=content)
+    # Fix round 1, finding 1: the text printed is checked too, so what is stored is exactly what was printed.
+    confirmation.confirm(engine, run_id, by, shown=content,
+                         shown_fingerprint=confirmation.shown_fingerprint(content, words))
     if to_queue:  # step 9b (R2): confirmed; a worker takes it up
         print(json.dumps({"run": run_id, "status": "waiting", "confirmed": True, "queued": True}), flush=True)
         return 0
diff --git a/hypocurate/pipeline/agents/critic.py b/hypocurate/pipeline/agents/critic.py
index da4c853..d117afe 100644
--- a/hypocurate/pipeline/agents/critic.py
+++ b/hypocurate/pipeline/agents/critic.py
@@ -221,10 +221,15 @@ def flag_display(engine: Engine, run_id: int) -> list[dict]:
     Critic's class and reason with ADVICE_LABEL beside them, or NOT_SENT for a single-record flag, or 'not classified'
     (shown, never decided on)."""
     with engine.connect() as conn:
-        rows = conn.execute(text(
-            "SELECT f.id, f.kind, f.category, f.critic_class, f.critic_reason, "
-            "(SELECT count(*) FROM flag_record fr WHERE fr.flag_id = f.id) AS n FROM flag f WHERE f.run_id = :r "
-            "ORDER BY f.id"), dict(r=run_id)).all()
+        return flag_display_in(conn, run_id)
+
+
+def flag_display_in(conn: Connection, run_id: int) -> list[dict]:
+    """`flag_display` on a given connection (step 10a, fix round 1, finding 2: the run page reads one snapshot)."""
+    rows = conn.execute(text(
+        "SELECT f.id, f.kind, f.category, f.critic_class, f.critic_reason, "
+        "(SELECT count(*) FROM flag_record fr WHERE fr.flag_id = f.id) AS n FROM flag f WHERE f.run_id = :r "
+        "ORDER BY f.id"), dict(r=run_id)).all()
     out = []
     for r in rows:
         if r.n < MIN_RECORDS:
diff --git a/hypocurate/pipeline/confirmation.py b/hypocurate/pipeline/confirmation.py
index ba3e0ac..0e4ced4 100644
--- a/hypocurate/pipeline/confirmation.py
+++ b/hypocurate/pipeline/confirmation.py
@@ -269,13 +269,18 @@ def render(c: Mapping[str, Any]) -> str:
     return "\n".join(lines)
 
 
-def content_fingerprint(c: Mapping[str, Any]) -> str:
-    """SHA-256 of the content's canonical JSON (keys sorted, no spaces, UTF-8): what a confirmation page sends back so
-    that `confirm` can check it is still the content shown (owner's addition 2 of 2026-10-11)."""
-    canonical = json.dumps(c, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
+def shown_fingerprint(c: Mapping[str, Any], words: str) -> str:
+    """SHA-256 of the canonical JSON (keys sorted, no spaces, UTF-8) of the content and the exact text shown together:
+    what a confirmation page (or the command line) sends back, so that `confirm` records only what the person saw
+    (owner's addition 2 of 2026-10-11; fix round 1, finding 1: the text too, so a renderer changed between showing and
+    confirming is refused)."""
+    canonical = json.dumps({"content": c, "text": words}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
     return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
 
 
+_fingerprint = shown_fingerprint  # `confirm`'s own parameter has the same name
+
+
 def show(engine: Engine, run_id: int) -> tuple[dict, str]:
     """The content and its text, for a waiting run (what `confirm` prints before recording anything)."""
     with engine.connect() as conn:
@@ -286,9 +291,10 @@ def show(engine: Engine, run_id: int) -> tuple[dict, str]:
 def confirm(engine: Engine, run_id: int, by: str, shown: Mapping[str, Any] | None = None,
             shown_fingerprint: str | None = None) -> dict:
     """Records one named person's confirmation of one waiting run. `shown`: the content that was printed; or
-    `shown_fingerprint`: the `content_fingerprint` of the content a page displayed (step 10a, owner's addition 2). The
-    confirmation is refused as `content_changed` if either differs from the current content, read in the same
-    transaction as the insert. Returns the stored content and text."""
+    `shown_fingerprint`: the `shown_fingerprint` of the content and the text displayed (step 10a, owner's addition 2;
+    fix round 1, finding 1). The content is read and the text rendered in the same transaction as the insert; the
+    confirmation is refused as `content_changed` if either differs from what was shown, so the text stored is exactly
+    the text the fingerprint covered. Returns the stored content and text."""
     name = (by or "").strip()
     if not name or len(name) > CONFIRMED_BY_MAX:
         raise QueryRefused("name_required", f"a confirmation names the person (1 to {CONFIRMED_BY_MAX} characters)")
@@ -309,11 +315,11 @@ def confirm(engine: Engine, run_id: int, by: str, shown: Mapping[str, Any] | Non
             c = content(conn, run_id)
         except NotLockable as error:
             raise QueryRefused(error.code, "the stored rows give no plan to lock") from None
+        words = render(c)
         if (shown is not None and dict(shown) != c) or \
-                (shown_fingerprint is not None and shown_fingerprint != content_fingerprint(c)):
+                (shown_fingerprint is not None and shown_fingerprint != _fingerprint(c, words)):
             raise QueryRefused("content_changed", "what was shown is no longer the run's current content; show it "
                                                   "again before confirming")
-        words = render(c)
         conn.execute(text(
             "INSERT INTO rules_confirmation (run_id, confirmed_by, plan_fingerprint, planner_stage_result_id, "
             "narrowing_stage_result_id, content, shown) VALUES (:r, :b, :fp, :p, :n, :c, :s)").bindparams(
diff --git a/hypocurate/pipeline/run_view.py b/hypocurate/pipeline/run_view.py
index 8f29b6f..3df091f 100644
--- a/hypocurate/pipeline/run_view.py
+++ b/hypocurate/pipeline/run_view.py
@@ -11,8 +11,9 @@ the orchestrator nor recovery (tests/test_web_isolation.py).
 """
 from __future__ import annotations
 
+from contextlib import contextmanager
 from decimal import Decimal
-from typing import Any, Mapping
+from typing import Any, Iterator, Mapping
 
 from sqlalchemy import Connection, Engine, text
 
@@ -75,6 +76,20 @@ FAILED_NO_LEVEL = "failed: no evidence level"  # owner, 2026-10-11
 TEST_RUN_BADGE = TEST_RUN_LABEL
 
 
+RUNS_PER_PAGE = 50  # fix round 1, finding 3: the runs list has pages, so every run stays reachable
+
+
+@contextmanager
+def snapshot(engine: Engine) -> Iterator[Connection]:
+    """One read-only REPEATABLE READ transaction (fix round 1, finding 2): every read of a page sees the database as it
+    was at the page's first read, so its status, statement, verdict and evidence level always belong together."""
+    with engine.connect() as conn:
+        conn.execution_options(isolation_level="REPEATABLE READ")
+        with conn.begin():
+            conn.execute(text("SET TRANSACTION READ ONLY"))
+            yield conn
+
+
 def _set_description(key: str | None) -> str:
     from hypocurate.pipeline.eligibility import INFLUENCE_KEY, SENSITIVITY_CHANGES
     if key == INFLUENCE_KEY:
@@ -106,6 +121,11 @@ def question_as_tested(engine: Engine, run_id: int) -> dict | None:
         return reading.stored(conn, run_id)
 
 
+def _question_as_tested(conn: Connection, run_id: int) -> dict | None:
+    from hypocurate.pipeline import reading
+    return reading.stored(conn, run_id)
+
+
 def analyst_text(explained) -> dict:
     """The Analyst's stored explanation, always with its label; or that it is unavailable (code's own words)."""
     from hypocurate.pipeline.agents import analyst
@@ -122,6 +142,11 @@ def critic_flags(engine: Engine, run_id: int) -> list[dict]:
     return critic.flag_display(engine, run_id)
 
 
+def _critic_flags(conn: Connection, run_id: int) -> list[dict]:
+    from hypocurate.pipeline.agents import critic
+    return critic.flag_display_in(conn, run_id)
+
+
 def queue_rows(engine: Engine) -> list[dict]:
     """`queue` (R2): every queued, waiting or running run, with its stage, its claim's worker and heartbeat age, the
     time since the run last wrote anything (A4), and how often it was taken up again."""
@@ -153,41 +178,46 @@ def queue_rows(engine: Engine) -> list[dict]:
 
 
 def show(engine: Engine, run_id: int) -> dict | None:
+    with snapshot(engine) as conn:
+        return show_in(conn, run_id)
+
+
+def show_in(conn: Connection, run_id: int) -> dict | None:
+    """`show` on a given connection: one snapshot for the whole output (fix round 1, finding 2)."""
     from hypocurate.pipeline import statement
-    with engine.connect() as conn:
-        run = conn.execute(text(
-            "SELECT r.id, r.status, r.outcome, r.verdict, r.exploratory, r.evidence_level, r.failure_reason, "
-            "r.fixed_plan, h.number, hv.text, hv.sufficiency_option, h.narrower_of_run_id FROM run r "
-            "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
-            "WHERE r.id = :r"), dict(r=run_id)).one_or_none()
-        if run is None:
-            return None
+    run = conn.execute(text(
+        "SELECT r.id, r.status, r.outcome, r.verdict, r.exploratory, r.evidence_level, r.failure_reason, "
+        "r.fixed_plan, h.number, hv.text, hv.sufficiency_option, h.narrower_of_run_id FROM run r "
+        "JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id "
+        "WHERE r.id = :r"), dict(r=run_id)).one_or_none()
+    if run is None:
+        return None
 
-        def output(stage):
-            return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = :s "
-                                     "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).scalar_one_or_none()
-
-        stats, gap, narrowing, explained = output("statistics"), output("gap_facts"), output("narrowing"), output("analyst")
-        results = [dict(r._mapping) for r in conn.execute(text(
-            "SELECT ar.scope, s.key AS source, a.key AS analysis_set, ar.n_records, ar.n_alloys, ar.n_groups, "
-            "ar.resid_df, ar.check1_passed, ar.check2_passed, ar.minimums_met, ar.withheld, ar.estimate, ar.std_error, "
-            "ar.p_value, ar.label FROM analysis_result ar JOIN analysis_set a ON a.id = ar.analysis_set_id "
-            "LEFT JOIN source s ON s.id = ar.source_id WHERE ar.run_id = :r ORDER BY ar.id"), dict(r=run_id)).all()]
-        narrower = conn.execute(text("SELECT number FROM hypothesis WHERE narrower_of_run_id = :r"),
-                                dict(r=run_id)).scalar_one_or_none()
-        original = conn.execute(text("SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = "
-                                     "r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"),
-                                dict(r=run.narrower_of_run_id)).scalar_one_or_none() if run.narrower_of_run_id else None
-        cost = conn.execute(text("SELECT * FROM model_call_totals_by_run WHERE run_id = :r"), dict(r=run_id)).one_or_none()
+    def output(stage):
+        return conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = :s "
+                                 "ORDER BY id DESC LIMIT 1"), dict(r=run_id, s=stage)).scalar_one_or_none()
+
+    stats, gap, narrowing, explained = output("statistics"), output("gap_facts"), output("narrowing"), output("analyst")
+    results = [dict(r._mapping) for r in conn.execute(text(
+        "SELECT ar.scope, s.key AS source, a.key AS analysis_set, ar.n_records, ar.n_alloys, ar.n_groups, "
+        "ar.resid_df, ar.check1_passed, ar.check2_passed, ar.minimums_met, ar.withheld, ar.estimate, ar.std_error, "
+        "ar.p_value, ar.label FROM analysis_result ar JOIN analysis_set a ON a.id = ar.analysis_set_id "
+        "LEFT JOIN source s ON s.id = ar.source_id WHERE ar.run_id = :r ORDER BY ar.id"), dict(r=run_id)).all()]
+    narrower = conn.execute(text("SELECT number FROM hypothesis WHERE narrower_of_run_id = :r"),
+                            dict(r=run_id)).scalar_one_or_none()
+    original = conn.execute(text("SELECT h.number FROM run r JOIN hypothesis_version hv ON hv.id = "
+                                 "r.hypothesis_version_id JOIN hypothesis h ON h.id = hv.hypothesis_id WHERE r.id = :r"),
+                            dict(r=run.narrower_of_run_id)).scalar_one_or_none() if run.narrower_of_run_id else None
+    cost = conn.execute(text("SELECT * FROM model_call_totals_by_run WHERE run_id = :r"), dict(r=run_id)).one_or_none()
     decision = (stats or {}).get("decision") or (narrowing or {}).get("decision") or {}
-    built = statement.build(engine, run_id)  # decision A: code's statement, for every completed run
+    built = statement.build_in(conn, run_id)  # decision A: code's statement, for every completed run
     return {
         # One presentation everywhere (owner, after the re-check): code's statement first, then the Analyst's text,
         # only with the statement and only under its label; `run` and `dispatch` print this same output.
         "statement": built["lines"] if built else None,
         "analyst_text": analyst_text(explained) if built else None,
         "run": run.id, "query": run.number, "claim": run.text, "outcome_code": run.outcome,
-        "question_as_tested": question_as_tested(engine, run.id), "status": run.status,
+        "question_as_tested": _question_as_tested(conn, run.id), "status": run.status,
         "narrower_question_of": original, "narrower_question": narrower,
         # A8: a narrower question's plan is shown as coming from its original's narrowing decision.
         "plan": ("from the narrowing decision" if original is not None else "fixed") if run.fixed_plan
@@ -205,7 +235,7 @@ def show(engine: Engine, run_id: int) -> dict | None:
         "sources": (gap or {}).get("sources"),
         "statement_format": ({"current": built["format_version"], "recorded": built["recorded_format_version"]}
                              if built else None),
-        "flags": critic_flags(engine, run_id),
+        "flags": _critic_flags(conn, run_id),
         "tokens_and_cost": {k: v for k, v in cost._mapping.items() if k != "run_id"} if cost else None,
         "p_value_description": st.P_VALUE_DESCRIPTION if any(r["p_value"] is not None for r in results) else None,
         # Step 9a: only for a waiting run, so every other run's output is as before.
@@ -322,40 +352,44 @@ def _time(conn: Connection, column: str, table: str, run_id: int, key: str = "ru
 
 
 def run_page(engine: Engine, run_id: int) -> dict | None:
-    """Everything the run viewer shows, as ready-made words and numbers."""
+    """Everything the run viewer shows, as ready-made words and numbers, from one snapshot."""
+    with snapshot(engine) as conn:
+        return run_page_in(conn, run_id)
+
+
+def run_page_in(conn: Connection, run_id: int) -> dict | None:
     from hypocurate.access.stage import actual_stage
-    shown = show(engine, run_id)
+    shown = show_in(conn, run_id)
     if shown is None:
         return None
-    with engine.connect() as conn:
-        head = conn.execute(text(
-            "SELECT r.status, r.experiment_flags, r.spending_ceiling, r.agent_mode, hv.version_number, d.name AS domain, "
-            "to_char(r.queued_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS queued, "
-            "to_char(coalesce(r.completed_at, r.failed_at) AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS ended, "
-            "EXISTS (SELECT 1 FROM rules_confirmation rc WHERE rc.run_id = r.id) AS confirmed "
-            "FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
-            "JOIN domain d ON d.id = coalesce(hv.confirmed_domain_id, hv.domain_id) WHERE r.id = :r"),
-            dict(r=run_id)).one()
-        tags = conn.execute(text(
-            "SELECT tv.kind, tv.value FROM run_tag rt JOIN tag_value tv ON tv.id = rt.tag_value_id WHERE rt.run_id = :r "
-            "ORDER BY tv.kind, tv.value"), dict(r=run_id)).all()
-        plan = conn.execute(text("SELECT fingerprint FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar_one_or_none()
-        freeze = conn.execute(text("SELECT fingerprint, n_records FROM run_snapshot WHERE run_id = :r"),
-                              dict(r=run_id)).one_or_none()
-        locked_at, frozen_at = _time(conn, "locked_at", "plan", run_id), _time(conn, "frozen_at", "run_snapshot", run_id)
-        stats = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' AND "
-                                  "status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
-        kinds = dict(conn.execute(text("SELECT s.key, s.data_kind FROM run_source rs JOIN source s ON s.id = "
-                                       "rs.source_id WHERE rs.run_id = :r"), dict(r=run_id)).all())
-        sources = conn.execute(text(
-            "SELECT s.key, s.name, rs.search_status, rs.nothing_found FROM run_source rs JOIN source s ON s.id = "
-            "rs.source_id WHERE rs.run_id = :r ORDER BY s.key"), dict(r=run_id)).all()
-        stages = conn.execute(text(
-            "SELECT sr.stage, sr.attempt, sr.status, sr.model, t.calls, t.input_tokens, t.output_tokens, t.reported_cost "
-            "FROM stage_result sr LEFT JOIN model_call_totals_by_stage t ON t.stage_result_id = sr.id "
-            "WHERE sr.run_id = :r ORDER BY sr.id"), dict(r=run_id)).all()
-        stage = actual_stage(conn, run_id, head.status) if head.status == "running" else None
-        facts = _claim_facts(conn, run_id) if head.status in ("queued", "waiting", "running") else None
+    head = conn.execute(text(
+        "SELECT r.status, r.experiment_flags, r.spending_ceiling, r.agent_mode, hv.version_number, d.name AS domain, "
+        "to_char(r.queued_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS queued, "
+        "to_char(coalesce(r.completed_at, r.failed_at) AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS \"UTC\"') AS ended, "
+        "EXISTS (SELECT 1 FROM rules_confirmation rc WHERE rc.run_id = r.id) AS confirmed "
+        "FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
+        "JOIN domain d ON d.id = coalesce(hv.confirmed_domain_id, hv.domain_id) WHERE r.id = :r"),
+        dict(r=run_id)).one()
+    tags = conn.execute(text(
+        "SELECT tv.kind, tv.value FROM run_tag rt JOIN tag_value tv ON tv.id = rt.tag_value_id WHERE rt.run_id = :r "
+        "ORDER BY tv.kind, tv.value"), dict(r=run_id)).all()
+    plan = conn.execute(text("SELECT fingerprint FROM plan WHERE run_id = :r"), dict(r=run_id)).scalar_one_or_none()
+    freeze = conn.execute(text("SELECT fingerprint, n_records FROM run_snapshot WHERE run_id = :r"),
+                          dict(r=run_id)).one_or_none()
+    locked_at, frozen_at = _time(conn, "locked_at", "plan", run_id), _time(conn, "frozen_at", "run_snapshot", run_id)
+    stats = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'statistics' AND "
+                              "status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
+    kinds = dict(conn.execute(text("SELECT s.key, s.data_kind FROM run_source rs JOIN source s ON s.id = "
+                                   "rs.source_id WHERE rs.run_id = :r"), dict(r=run_id)).all())
+    sources = conn.execute(text(
+        "SELECT s.key, s.name, rs.search_status, rs.nothing_found FROM run_source rs JOIN source s ON s.id = "
+        "rs.source_id WHERE rs.run_id = :r ORDER BY s.key"), dict(r=run_id)).all()
+    stages = conn.execute(text(
+        "SELECT sr.stage, sr.attempt, sr.status, sr.model, t.calls, t.input_tokens, t.output_tokens, t.reported_cost "
+        "FROM stage_result sr LEFT JOIN model_call_totals_by_stage t ON t.stage_result_id = sr.id "
+        "WHERE sr.run_id = :r ORDER BY sr.id"), dict(r=run_id)).all()
+    stage = actual_stage(conn, run_id, head.status) if head.status == "running" else None
+    facts = _claim_facts(conn, run_id) if head.status in ("queued", "waiting", "running") else None
     test_run = bool((head.experiment_flags or {}).get("constructed_test_data"))
     cost = shown["tokens_and_cost"] or {}
     tables = _tables(stats or {}, kinds)
@@ -397,15 +431,24 @@ def run_page(engine: Engine, run_id: int) -> dict | None:
     }
 
 
-def runs_list(engine: Engine, limit: int = 200) -> list[dict]:
-    """Every run, newest first: query, claim, status, outcome, evidence level and cost."""
-    with engine.connect() as conn:
+class NoSuchPage(LookupError):
+    pass
+
+
+def runs_list(engine: Engine, page: int = 1, per_page: int = RUNS_PER_PAGE) -> dict:
+    """One page of every run, newest first (query, claim, status, outcome, evidence level and cost), with the page's
+    place in the whole (fix round 1, finding 3: every run stays reachable). One snapshot for the count and the rows."""
+    with snapshot(engine) as conn:
+        total = conn.execute(text("SELECT count(*) FROM run")).scalar_one()
+        pages = max(1, -(-total // per_page))
+        if not 1 <= page <= pages:
+            raise NoSuchPage(f"no page {page} of the runs list (pages 1 to {pages})")
         rows = conn.execute(text(
             "SELECT r.id, r.status, r.evidence_level, r.verdict, r.experiment_flags, h.number, hv.text, "
             "r.outcome, to_char(r.queued_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI \"UTC\"') AS queued, "
             "coalesce(t.cap_cost, 0) AS cost FROM run r JOIN hypothesis_version hv ON hv.id = r.hypothesis_version_id "
             "JOIN hypothesis h ON h.id = hv.hypothesis_id LEFT JOIN model_call_totals_by_run t ON t.run_id = r.id "
-            "ORDER BY r.id DESC LIMIT :n"), dict(n=limit)).all()
+            "ORDER BY r.id DESC LIMIT :n OFFSET :o"), dict(n=per_page, o=(page - 1) * per_page)).all()
     out = []
     for r in rows:
         test_run = bool((r.experiment_flags or {}).get("constructed_test_data"))
@@ -414,7 +457,10 @@ def runs_list(engine: Engine, limit: int = 200) -> list[dict]:
                     "outcome": r.outcome.replace("_", " ") + " in the sources searched" if r.outcome else None,
                     "evidence": evidence(r.evidence_level, None, None, test_run, failed=r.status == "failed"),
                     "cost": money(r.cost)})
-    return out
+    first = (page - 1) * per_page + 1
+    return {"runs": out, "page": page, "pages": pages, "total": total,
+            "words": (f"Runs {first} to {first + len(out) - 1} of {total}, newest first." if out else "No run yet."),
+            "previous": page - 1 if page > 1 else None, "next": page + 1 if page < pages else None}
 
 
 def _text_rows(words: str) -> list[dict]:
@@ -433,20 +479,22 @@ def _text_rows(words: str) -> list[dict]:
 
 
 def confirmation_page(engine: Engine, run_id: int, name: str | None) -> dict | None:
-    """A waiting run's confirmation: the content and its text exactly as `confirm` shows them, the content's
-    fingerprint, which the page sends back (owner's addition 2), and the label the question as tested will carry once
-    `name` confirms it."""
+    """A waiting run's confirmation, from one snapshot: the content and its text exactly as `confirm` shows them, the
+    fingerprint of both (owner's addition 2; fix round 1, finding 1), which the page sends back, and the label the
+    question as tested will carry once `name` confirms it."""
     from hypocurate.pipeline import confirmation
-    page = run_page(engine, run_id)
-    if page is None:
-        return None
-    if not page["can_confirm"]:
-        return {**page, "content": None}
-    content, words = confirmation.show(engine, run_id)
+    with snapshot(engine) as conn:
+        page = run_page_in(conn, run_id)
+        if page is None:
+            return None
+        if not page["can_confirm"]:
+            return {**page, "content": None}
+        content = confirmation.content(conn, run_id)
+    words = confirmation.render(content)
     after = confirmation.label_once_confirmed(content["question_as_tested"]["label"], by=name or "you",
                                               at="the time you confirm (UTC)")
     return {**page, "content": content, "text": words, "rows": _text_rows(words),
-            "content_fingerprint": confirmation.content_fingerprint(content), "label_after": after}
+            "shown_fingerprint": confirmation.shown_fingerprint(content, words), "label_after": after}
 
 
 def spending(engine: Engine) -> dict:
diff --git a/hypocurate/pipeline/statement.py b/hypocurate/pipeline/statement.py
index b3d6c34..7ae706f 100644
--- a/hypocurate/pipeline/statement.py
+++ b/hypocurate/pipeline/statement.py
@@ -297,7 +297,13 @@ def build(engine: Engine, run_id: int) -> dict | None:
     """The statement of a completed run, or None for a run that is not completed: its lines and text, the format
     version it is rendered in, and the version recorded on the run when it completed (None if not recorded)."""
     with engine.connect() as conn:
-        f = facts(conn, run_id)
+        return build_in(conn, run_id)
+
+
+def build_in(conn: Connection, run_id: int) -> dict | None:
+    """`build` on a given connection (step 10a, fix round 1, finding 2: the run page reads everything in one
+    snapshot)."""
+    f = facts(conn, run_id)
     if f is None:
         return None
     lines = render(f)
diff --git a/hypocurate/web/app.py b/hypocurate/web/app.py
index ab99d20..e682e08 100644
--- a/hypocurate/web/app.py
+++ b/hypocurate/web/app.py
@@ -17,7 +17,7 @@ from __future__ import annotations
 
 from pathlib import Path
 
-from fastapi import FastAPI, Form, HTTPException, Request
+from fastapi import FastAPI, Form, HTTPException, Query, Request
 from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
 from fastapi.staticfiles import StaticFiles
 from fastapi.templating import Jinja2Templates
@@ -163,9 +163,13 @@ def create_app(
     # --- the run pages (step 10a) ---------------------------------------------------------------------------------
 
     @app.get("/runs", response_class=HTMLResponse)
-    def runs(request: Request):
+    def runs(request: Request, page_number: int = Query(1, alias="page")):
         from hypocurate.pipeline import run_view
-        return page(request, "runs.html", {"runs": run_view.runs_list(engine)})
+        try:
+            listed = run_view.runs_list(engine, page_number)
+        except run_view.NoSuchPage as error:
+            raise HTTPException(status_code=404, detail=str(error)) from None
+        return page(request, "runs.html", {"listed": listed, "runs": listed["runs"]})
 
     @app.get("/runs/{run_id}", response_class=HTMLResponse)
     def run(request: Request, run_id: int):
@@ -195,17 +199,17 @@ def create_app(
         return page(request, "confirm.html", {"r": shown, "error": None})
 
     @app.post("/runs/{run_id}/confirm")
-    def confirm(request: Request, run_id: int, csrf_token: str = Form(""), content_fingerprint: str = Form("")):
+    def confirm(request: Request, run_id: int, csrf_token: str = Form(""), shown_fingerprint: str = Form("")):
         from hypocurate.pipeline import confirmation, queries, run_view
         security.check_csrf(request, csrf_token)
         name = security.signed_in_name(request)
         if run_view.run_page(engine, run_id) is None:
             raise HTTPException(status_code=404, detail=f"no run {run_id}")
         try:
-            if not content_fingerprint:
+            if not shown_fingerprint:
                 raise queries.QueryRefused("content_changed", "the page sent no fingerprint of what it showed; show "
                                                               "it again before confirming")
-            confirmation.confirm(engine, run_id, name, shown_fingerprint=content_fingerprint)
+            confirmation.confirm(engine, run_id, name, shown_fingerprint=shown_fingerprint)
         except queries.QueryRefused as refused:
             shown = run_view.confirmation_page(engine, run_id, request.session.get("name"))
             if shown is None:
diff --git a/hypocurate/web/static/style.css b/hypocurate/web/static/style.css
index cc9d28f..364be14 100644
--- a/hypocurate/web/static/style.css
+++ b/hypocurate/web/static/style.css
@@ -112,3 +112,4 @@ dd ul { margin: 0; padding-left: 1.2em; }
 @media (max-width: 60rem) { .statement-row { grid-template-columns: 1fr; } }
 .info.flip .info-text { left: auto; right: 0; }
 table.runs td:nth-child(2) { white-space: nowrap; }
+.pages { display: flex; gap: 16px; align-items: baseline; margin: 1rem 0; }
diff --git a/hypocurate/web/templates/confirm.html b/hypocurate/web/templates/confirm.html
index 81ce897..1837a0d 100644
--- a/hypocurate/web/templates/confirm.html
+++ b/hypocurate/web/templates/confirm.html
@@ -20,7 +20,7 @@
 </section>
 <form method="post" action="/runs/{{ r.run }}/confirm" class="confirm-form">
   <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
-  <input type="hidden" name="content_fingerprint" value="{{ r.content_fingerprint }}">
+  <input type="hidden" name="shown_fingerprint" value="{{ r.shown_fingerprint }}">
   <p>Confirming as <strong>{{ signed_in_as }}</strong>. Once you confirm, the question as tested is labelled: {{ r.label_after }}.</p>
   <button type="submit">Confirm the question as tested</button>
   <a class="button secondary" href="/runs/{{ r.run }}">Back without confirming</a>
@@ -29,6 +29,6 @@
   <input type="hidden" name="{{ csrf_field }}" value="{{ csrf_token }}">
   <button type="submit" class="secondary">Cancel this run instead</button>
 </form>
-<p class="muted small">Content fingerprint {{ r.content_fingerprint }}</p>
+<p class="muted small">Fingerprint of what is shown {{ r.shown_fingerprint }}</p>
 {% endif %}
 {% endblock %}
diff --git a/hypocurate/web/templates/runs.html b/hypocurate/web/templates/runs.html
index bff9b37..c120936 100644
--- a/hypocurate/web/templates/runs.html
+++ b/hypocurate/web/templates/runs.html
@@ -4,8 +4,8 @@
 {% block main_attrs %} class="wide"{% endblock %}
 {% block content %}
 <h1>Runs</h1>
-<p class="muted">Every dispatched run, newest first. {{ info("queue") }}</p>
-{% if not runs %}<p>No run yet.</p>{% else %}
+<p class="muted">{{ listed.words }} {{ info("queue") }}</p>
+{% if runs %}
 <table class="data runs">
   <thead><tr><th>Evidence {{ info("evidence_level") }}</th><th>Run</th><th>Claim</th><th>Status {{ info("status") }}</th><th>Outcome {{ info("outcome") }}</th><th>Cost {{ info("cost") }}</th></tr></thead>
   <tbody>{% for x in runs %}
@@ -20,4 +20,11 @@
   {% endfor %}</tbody>
 </table>
 {% endif %}
+{% if listed.previous or listed.next %}
+<nav class="pages" aria-label="Pages of the runs list">
+  {% if listed.previous %}<a rel="prev" href="/runs?page={{ listed.previous }}">Newer runs</a>{% endif %}
+  <span>Page {{ listed.page }} of {{ listed.pages }}</span>
+  {% if listed.next %}<a rel="next" href="/runs?page={{ listed.next }}">Older runs</a>{% endif %}
+</nav>
+{% endif %}
 {% endblock %}
diff --git a/tests/test_confirmation_step10.py b/tests/test_confirmation_step10.py
index 6cf6286..8c0d1ec 100644
--- a/tests/test_confirmation_step10.py
+++ b/tests/test_confirmation_step10.py
@@ -41,21 +41,25 @@ def confirmations(engine, rid):
 
 
 def test_the_fingerprint_is_the_sha256_of_the_contents_canonical_json_and_changes_with_any_item():
+    """Fix round 1, finding 1: the fingerprint covers the content and the text shown together (it covered the content
+    alone before); key order does not count, list order and any item do."""
     import hashlib
     import json
     c = {"run": 1, "query": "Q-0001", "cost_so_far": {"counted_usd": "0.017640", "calls": 1}, "names": ["ä", "b"]}
-    expected = hashlib.sha256(json.dumps(c, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
-                              .encode("utf-8")).hexdigest()
-    assert confirmation.content_fingerprint(c) == expected
-    assert confirmation.content_fingerprint(dict(reversed(list(c.items())))) == expected  # key order does not count
-    assert confirmation.content_fingerprint({**c, "cost_so_far": {"counted_usd": "0.017641", "calls": 1}}) != expected
-    assert confirmation.content_fingerprint({**c, "names": ["b", "ä"]}) != expected  # list order does
+    words = "Run 1 of Q-0001 waits."
+    expected = hashlib.sha256(json.dumps({"content": c, "text": words}, sort_keys=True, separators=(",", ":"),
+                                         ensure_ascii=False).encode("utf-8")).hexdigest()
+    assert confirmation.shown_fingerprint(c, words) == expected
+    assert confirmation.shown_fingerprint(dict(reversed(list(c.items()))), words) == expected  # key order does not count
+    assert confirmation.shown_fingerprint({**c, "cost_so_far": {"counted_usd": "0.017641", "calls": 1}}, words) != expected
+    assert confirmation.shown_fingerprint({**c, "names": ["b", "ä"]}, words) != expected  # list order does
 
 
 def test_a_matching_fingerprint_confirms(engine, stub):
     rid = waiting(engine, stub)
     content, words = confirmation.show(engine, rid)
-    stored = confirmation.confirm(engine, rid, "Grace Reviewer", shown_fingerprint=confirmation.content_fingerprint(content))
+    stored = confirmation.confirm(engine, rid, "Grace Reviewer",
+                                  shown_fingerprint=confirmation.shown_fingerprint(content, words))
     assert stored["shown"] == words and confirmations(engine, rid) == 1
 
 
@@ -72,7 +76,7 @@ def test_content_that_changed_after_it_was_shown_is_refused(engine, stub, monkey
     """What `confirm` compares is the content as it reads inside its own transaction: content that differs from what
     the page showed (here one item more) is refused."""
     rid = waiting(engine, stub)
-    shown = confirmation.content_fingerprint(confirmation.show(engine, rid)[0])
+    shown = confirmation.shown_fingerprint(*confirmation.show(engine, rid))
     original = confirmation.content
     monkeypatch.setattr(confirmation, "content", lambda conn, run_id: {**original(conn, run_id), "changed": True})
     with pytest.raises(queries.QueryRefused) as refused:
@@ -92,7 +96,8 @@ def test_the_text_shown_says_informative_groups_the_label_now_and_once_confirmed
     assert "  Once confirmed, labelled: the Planner's reading of the claim; not verified by code; confirmed by the " \
            "person who confirms on the time of confirming (UTC)" in words.split("\n")
     assert content["cost_so_far"]["calls"] == 1 and "(reported $" in words and "; 1 model call, 0 without" in words
-    stored = confirmation.confirm(engine, rid, "Grace Reviewer", shown_fingerprint=confirmation.content_fingerprint(content))
+    stored = confirmation.confirm(engine, rid, "Grace Reviewer",
+                                  shown_fingerprint=confirmation.shown_fingerprint(content, words))
     assert stored["shown"] == words  # what is stored is exactly what was shown
 
 
@@ -102,3 +107,40 @@ def test_the_label_once_confirmed_follows_the_readings_own_wording():
         reading.CONFIRMED_LABEL.format(by="Ada", at="2026-10-11 10:00:00 UTC")
     assert confirmation.label_once_confirmed(reading.LABELS["narrower"], "Ada", "then") == \
         reading.LABELS["narrower"] + "; confirmed by Ada on then"
+
+
+# --- Fix round 1, finding 1 (ChatGPT, accepted by the owner, 2026-10-11): the fingerprint covers the text shown ------
+
+def test_a_renderer_changed_between_display_and_submission_is_refused(engine, stub, monkeypatch):
+    """The page showed one wording; the code that renders it changed before the person confirmed (a deploy). The
+    content is the same, but the text that would be stored is not what the person saw: refused, nothing recorded."""
+    rid = waiting(engine, stub)
+    content, words = confirmation.show(engine, rid)
+    shown = confirmation.shown_fingerprint(content, words)
+    original = confirmation.render
+    monkeypatch.setattr(confirmation, "render",
+                        lambda c: original(c).replace("informative groups", "independent groups"))
+    assert confirmation.render(content) != words  # only the renderer changed
+    with pytest.raises(queries.QueryRefused) as refused:
+        confirmation.confirm(engine, rid, "Grace Reviewer", shown_fingerprint=shown)
+    assert refused.value.code == "content_changed" and confirmations(engine, rid) == 0
+
+
+def test_the_fingerprint_covers_the_content_and_the_text_together():
+    c = {"run": 1, "query": "Q-0001"}
+    assert confirmation.shown_fingerprint(c, "a") != confirmation.shown_fingerprint(c, "b")
+    assert confirmation.shown_fingerprint(c, "a") != confirmation.shown_fingerprint({**c, "run": 2}, "a")
+    import hashlib
+    import json
+    assert confirmation.shown_fingerprint(c, "a") == hashlib.sha256(json.dumps(
+        {"content": c, "text": "a"}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
+
+
+def test_what_is_stored_is_exactly_the_text_the_fingerprint_covered(engine, stub):
+    rid = waiting(engine, stub)
+    content, words = confirmation.show(engine, rid)
+    stored = confirmation.confirm(engine, rid, "Grace Reviewer",
+                                  shown_fingerprint=confirmation.shown_fingerprint(content, words))
+    with engine.connect() as conn:
+        assert conn.execute(text("SELECT shown FROM rules_confirmation WHERE run_id = :r"), dict(r=rid)).scalar() \
+            == words == stored["shown"]
diff --git a/tests/test_web_fix1.py b/tests/test_web_fix1.py
new file mode 100644
index 0000000..7773673
--- /dev/null
+++ b/tests/test_web_fix1.py
@@ -0,0 +1,145 @@
+"""Step 10a, fix round 1 (ChatGPT's review of 2026-10-11, findings 1 to 3, accepted by the owner).
+
+1. The confirmation page's fingerprint covers the text it showed, not only the content: a renderer changed between
+   display and submission is refused.
+2. The run page is built from one database snapshot: a run that completes while the page is being read is shown
+   whole in one state, never as completed with the earlier missing statement.
+3. The runs list has pages, so every run stays reachable however many newer runs there are.
+"""
+from __future__ import annotations
+
+import re
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+import stub_provider as sp
+import test_orchestrator as to
+from hypocurate.db.engine import make_engine
+from hypocurate.pipeline import confirmation, orchestrator, queries, reading, run_view
+from test_web_runs import plain, signed_in, token
+
+
+@pytest.fixture
+def stub():
+    s = sp.StubProvider()
+    yield s
+    s.close()
+
+
+@pytest.fixture
+def own(migrated_database):
+    e = make_engine(migrated_database)
+    pw.registered(e, ("mpea", "tamu_fcc"))
+    yield e, migrated_database
+    e.dispose()
+
+
+def one(engine, sql, **params):
+    with engine.connect() as conn:
+        return conn.execute(text(sql), params).scalar()
+
+
+def waiting(engine, stub):
+    stub.respond(to.responder(to.planner_body()))
+    rid = to.dispatched(engine)
+    assert orchestrator.run(engine, rid, client_options=sp.client_options(stub)).status == "waiting"
+    return rid
+
+
+# --- finding 1 ----------------------------------------------------------------------------------------------------
+
+def test_finding_1_a_page_confirmed_after_the_renderer_changed_is_refused(own, stub, monkeypatch):
+    engine, url = own
+    rid = waiting(engine, stub)
+    c = signed_in(engine, url)
+    page = c.get(f"/runs/{rid}/confirm").text
+    fp = re.search(r'name="shown_fingerprint" value="([0-9a-f]{64})"', page).group(1)
+    assert "10 informative groups" in plain(page)
+    original = confirmation.render  # a deploy between showing and confirming changes only the wording
+    monkeypatch.setattr(confirmation, "render",
+                        lambda content: original(content).replace("informative groups", "independent groups"))
+    r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "shown_fingerprint": fp})
+    assert r.status_code == 409 and "show it again before confirming" in plain(r.text)
+    assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 0
+
+
+# --- finding 2 ----------------------------------------------------------------------------------------------------
+
+def test_finding_2_a_run_that_completes_while_its_page_is_read_is_shown_in_one_state(own, stub, monkeypatch):
+    """The run is queued when the page starts reading; the worker completes it in the middle of the reads (here,
+    during the question-as-tested read). The page shows one state throughout: the queued run, still polling."""
+    engine, url = own
+    stub.respond(to.responder())
+    rid = to.dispatched(engine, fixed_plan=True)
+    original, done = reading.stored, []
+
+    def completing(conn, run_id):
+        if not done:
+            done.append(True)
+            assert to.run(engine, rid, stub).status == "completed"  # committed by other connections
+        return original(conn, run_id)
+
+    monkeypatch.setattr(reading, "stored", completing)
+    page = run_view.run_page(engine, rid)
+    assert done, "the run did not complete during the page's reads"
+    assert page["status"] == "queued" and page["open"] is True
+    assert page["statement"]["body"] == [] and page["evidence"]["level"] is None and page["outcome"] is None
+    after = run_view.run_page(engine, rid)  # the next read: completed, whole
+    assert after["status"] == "completed" and after["open"] is False and after["statement"]["body"]
+    assert after["evidence"]["level"] == 6 and after["outcome"] == "sufficient in the sources searched"
+
+
+def test_finding_2_the_state_fragment_of_such_a_run_keeps_polling(own, stub, monkeypatch):
+    engine, url = own
+    stub.respond(to.responder())
+    rid = to.dispatched(engine, fixed_plan=True)
+    c = signed_in(engine, url)
+    original, done = reading.stored, []
+
+    def completing(conn, run_id):
+        if not done:
+            done.append(True)
+            assert to.run(engine, rid, stub).status == "completed"
+        return original(conn, run_id)
+
+    monkeypatch.setattr(reading, "stored", completing)
+    fragment = c.get(f"/runs/{rid}/state").text
+    assert done and f'data-poll="/runs/{rid}/state"' in fragment  # the next poll sees it ended
+    monkeypatch.setattr(reading, "stored", original)
+    assert 'data-ended="true"' in c.get(f"/runs/{rid}/state").text
+
+
+# --- finding 3 ----------------------------------------------------------------------------------------------------
+
+def test_finding_3_an_old_waiting_run_stays_reachable_through_the_runs_list(own, stub):
+    """Over 200 newer runs (the old list's limit): the oldest run, waiting for a confirmation, is found by following
+    the list's pages and opens."""
+    engine, url = own
+    old = waiting(engine, stub)
+    newer = [to.dispatched(engine, fixed_plan=True) for _ in range(205)]
+    c = signed_in(engine, url)
+    seen, address, pages = set(), "/runs", 0
+    while address and pages < 50:
+        page = c.get(address)
+        assert page.status_code == 200
+        seen |= {int(x) for x in re.findall(r'href="/runs/(\d+)"', page.text)}
+        nxt = re.search(r'<a [^>]*rel="next"[^>]*href="([^"]+)"|<a [^>]*href="([^"]+)"[^>]*rel="next"', page.text)
+        address = (nxt.group(1) or nxt.group(2)).replace("&amp;", "&") if nxt else None
+        pages += 1
+    assert seen == {old, *newer}, f"unreachable: {sorted({old, *newer} - seen)[:5]}"
+    assert pages > 1
+    opened = plain(c.get(f"/runs/{old}").text)
+    assert "waiting at the rules lock" in opened and "Review and confirm the question as tested" in opened
+
+
+def test_finding_3_the_list_says_which_runs_a_page_shows(own):
+    engine, url = own
+    for _ in range(run_view.RUNS_PER_PAGE + 3):
+        to.dispatched(engine, fixed_plan=True)
+    c = signed_in(engine, url)
+    total = run_view.RUNS_PER_PAGE + 3
+    assert f"Runs 1 to {run_view.RUNS_PER_PAGE} of {total}, newest first." in plain(c.get("/runs").text)
+    assert f"Runs {run_view.RUNS_PER_PAGE + 1} to {total} of {total}, newest first." in plain(c.get("/runs?page=2").text)
+    assert c.get("/runs?page=0").status_code == 404 and c.get("/runs?page=99").status_code == 404
diff --git a/tests/test_web_runs.py b/tests/test_web_runs.py
index 2484342..743340c 100644
--- a/tests/test_web_runs.py
+++ b/tests/test_web_runs.py
@@ -261,7 +261,7 @@ def test_the_confirmation_page_shows_exactly_what_the_command_line_shows(world):
     content, words = confirmation.show(engine, runs["waiting"])
     for line in words.split("\n"):
         assert " ".join(line.split()) in plain(page), line
-    assert f'name="content_fingerprint" value="{confirmation.content_fingerprint(content)}"' in page
+    assert f'name="shown_fingerprint" value="{confirmation.shown_fingerprint(content, words)}"' in page
     assert f"Confirming as {NAME}" in plain(page)
 
 
@@ -283,10 +283,10 @@ def test_confirming_records_the_signed_in_name_and_exactly_the_text_shown_and_ru
     rid = waiting(engine, stub)
     c = signed_in(engine, url)
     page = c.get(f"/runs/{rid}/confirm").text
-    fp = re.search(r'name="content_fingerprint" value="([0-9a-f]{64})"', page).group(1)
+    fp = re.search(r'name="shown_fingerprint" value="([0-9a-f]{64})"', page).group(1)
     stages = one(engine, "SELECT count(*) FROM stage_result WHERE run_id = :r", r=rid)
     calls = len(stub.requests)
-    r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "content_fingerprint": fp})
+    r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "shown_fingerprint": fp})
     assert r.status_code == 303 and r.headers["location"] == f"/runs/{rid}?done=confirmed"
     with engine.connect() as conn:
         row = conn.execute(text("SELECT confirmed_by, shown FROM rules_confirmation WHERE run_id = :r"),
@@ -305,8 +305,8 @@ def test_a_confirmation_of_content_other_than_what_was_shown_is_refused(own, stu
     engine, url = own
     rid = waiting(engine, stub)
     c = signed_in(engine, url)
-    for fp in ("0" * 64, confirmation.content_fingerprint({"run": rid})):
-        r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "content_fingerprint": fp})
+    for fp in ("0" * 64, confirmation.shown_fingerprint({"run": rid}, "another text")):
+        r = c.post(f"/runs/{rid}/confirm", data={"csrf_token": token(c), "shown_fingerprint": fp})
         assert r.status_code == 409 and "show it again before confirming" in plain(r.text)
     assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 0
 
@@ -326,9 +326,9 @@ def test_a_write_without_the_sessions_token_is_refused_and_writes_nothing(own, s
     engine, url = own
     rid = waiting(engine, stub)
     c = signed_in(engine, url)
-    fp = confirmation.content_fingerprint(confirmation.show(engine, rid)[0])
+    fp = confirmation.shown_fingerprint(*confirmation.show(engine, rid))
     extra = {} if sent is None else {"csrf_token": sent}
-    assert c.post(f"/runs/{rid}/confirm", data={"content_fingerprint": fp, **extra}).status_code == 403
+    assert c.post(f"/runs/{rid}/confirm", data={"shown_fingerprint": fp, **extra}).status_code == 403
     assert c.post(f"/runs/{rid}/cancel", data=extra).status_code == 403
     assert one(engine, "SELECT count(*) FROM rules_confirmation WHERE run_id = :r", r=rid) == 0
     assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "waiting"
@@ -365,7 +365,7 @@ def test_a_completed_run_has_no_confirmation_to_give(world):
     engine, url, runs = world
     c = signed_in(engine, url)
     assert "is not waiting for a confirmation" in plain(c.get(f"/runs/{runs['sufficient']}/confirm").text)
-    r = c.post(f"/runs/{runs['sufficient']}/confirm", data={"csrf_token": token(c), "content_fingerprint": "0" * 64})
+    r = c.post(f"/runs/{runs['sufficient']}/confirm", data={"csrf_token": token(c), "shown_fingerprint": "0" * 64})
     assert r.status_code == 409
 
 

```

### c163337

```diff
commit c163337c5a2ebd74129d19ada2af2db0999f6cfb
Author: kelawady <47933563+kelawady@users.noreply.github.com>
Date:   Sun Oct 11 15:24:21 2026 +0000

    Step 10a fix round 1, finding 4: criterion 14.4 with a real web process stopped and restarted mid-run
    
    The test now starts the web service as its own process (uvicorn), holds a worker process at its Analyst request (a
    stub barrier), stops the web process, starts a new one, releases the worker, and checks: completed with the reference
    result, one claim, one model request, and the restarted web process shows the run's end. It replaces
    test_14_4_a_run_goes_on_to_its_end_with_the_page_closed_and_across_a_web_restart, which recreated app objects in the
    test process only. Finding 4 is a gap in the test, not the code: the new test passes on 431f880 too.
    
    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
---
 tests/test_web_state.py | 119 +++++++++++++++++++++++++++++++++++++++---------
 1 file changed, 98 insertions(+), 21 deletions(-)

diff --git a/tests/test_web_state.py b/tests/test_web_state.py
index 7d69ecd..9def8dd 100644
--- a/tests/test_web_state.py
+++ b/tests/test_web_state.py
@@ -117,35 +117,112 @@ def test_the_script_asks_again_only_when_the_state_it_received_carries_an_addres
     assert js.index('getAttribute("data-ended")') < again  # an ended fragment never reaches the next schedule
 
 
-def test_14_4_a_run_goes_on_to_its_end_with_the_page_closed_and_across_a_web_restart(own, stub):
-    """Criterion 14.4, bullets 1 and 3: a worker works the run; one web app reads its state and is then dropped (the
-    browser closed); a new app on the same database (the web service restarted) reads on until the run ends. The run
-    completes with the reference result, worked by the worker alone; the web service wrote nothing."""
+def free_port() -> int:
+    import socket
+    with socket.socket() as sock:
+        sock.bind(("127.0.0.1", 0))
+        return sock.getsockname()[1]
+
+
+class WebProcess:
+    """The web service as its own process (uvicorn, the image's command), on a database of its own."""
+
+    PASSWORD = "test-password-not-a-secret"
+
+    def __init__(self, database_url: str):
+        import secrets
+        self.port = free_port()
+        self.base = f"http://127.0.0.1:{self.port}"
+        env = {**os.environ, "HYPOCURATE_ENV": "development", "HYPOCURATE_PASSWORD": self.PASSWORD,
+               "SESSION_SECRET": secrets.token_hex(32), "DATABASE_URL": database_url}
+        self.proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "hypocurate.web.main:app", "--host",
+                                      "127.0.0.1", "--port", str(self.port), "--workers", "1"],
+                                     stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, env=env)
+        import httpx
+        deadline = time.time() + 60
+        while time.time() < deadline:
+            try:
+                if httpx.get(self.base + "/health", timeout=2).status_code == 200:
+                    break
+            except httpx.HTTPError:
+                time.sleep(0.2)
+        else:
+            self.stop()
+            raise AssertionError("the web process did not start")
+        self.client = httpx.Client(base_url=self.base, follow_redirects=False, timeout=30)
+        assert self.client.post("/login", data={"password": self.PASSWORD, "name": "Ada Reviewer"}).status_code == 303
+
+    def state(self, rid: int) -> str:
+        r = self.client.get(f"/runs/{rid}/state")
+        assert r.status_code == 200
+        return r.text
+
+    def stop(self) -> int:
+        if self.proc.poll() is None:
+            self.proc.terminate()
+            try:
+                self.proc.wait(timeout=30)
+            except subprocess.TimeoutExpired:
+                self.proc.kill()
+                self.proc.wait(timeout=30)
+        if getattr(self, "client", None) is not None:
+            self.client.close()
+        return self.proc.returncode
+
+
+def test_14_4_a_run_goes_on_to_its_end_across_a_restart_of_the_web_process(own, stub):
+    """Criterion 14.4, bullets 1 and 3 (fix round 1, finding 4): the web service runs as its own process. A worker
+    process works a fixed-plan run and is held at its model request (the Analyst's) by the stub. While it is held,
+    the web process is stopped (its browser gone with it) and a new one is started. Then the worker is released.
+    The run completes with the reference result, under one claim, with one model request: nothing was repeated."""
+    import threading
     engine, url = own
+    arrived, release = threading.Event(), threading.Event()
+
+    def hold():
+        arrived.set()
+        release.wait(180)
+
     stub.respond(to.responder())
+    stub.on_request(hold)
     rid = to.dispatched(engine, fixed_plan=True)
-    proc = subprocess.Popen([sys.executable, "-m", "hypocurate.worker", "--once"], stdout=subprocess.PIPE,
-                            stderr=subprocess.PIPE, text=True, env=dict(os.environ))
+    first = WebProcess(url)
+    worker = second = None
     try:
-        first = signed_in(engine, url)
-        seen = {first.get(f"/runs/{rid}/state").status_code for _ in range(3)}
-        assert seen == {200}
-        del first  # the browser is closed
-        second = signed_in(engine, url)  # the web service restarted: a new app, nothing carried over
-        deadline = time.time() + 300
-        while time.time() < deadline and "data-ended" not in second.get(f"/runs/{rid}/state").text:
+        assert "queued" in plain(first.state(rid))
+        worker = subprocess.Popen([sys.executable, "-m", "hypocurate.worker", "--once"], stdout=subprocess.PIPE,
+                                  stderr=subprocess.PIPE, text=True, env=dict(os.environ))
+        assert arrived.wait(300), "the worker never reached its model request"
+        held = plain(first.state(rid))
+        assert "running" in held and run_view.STAGE_WORDS["analysis"] in held
+        assert first.stop() is not None  # the web process is gone, while the run is mid-request
+        with pytest.raises(Exception):
+            import httpx
+            httpx.get(first.base + "/health", timeout=2)
+        second = WebProcess(url)  # the web service restarted: a new process, nothing carried over
+        assert "running" in plain(second.state(rid))
+        assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "running"
+        release.set()
+        out, err = worker.communicate(timeout=300)
+        assert worker.returncode == 0, err[-3000:]
+        deadline = time.time() + 60
+        while time.time() < deadline and 'data-ended="true"' not in second.state(rid):
             time.sleep(0.5)
-        out, err = proc.communicate(timeout=300)
-        assert proc.returncode == 0, err[-3000:]
+        page = plain(second.client.get(f"/runs/{rid}").text)
     finally:
-        if proc.poll() is None:
-            proc.kill()
+        release.set()
+        for web in (first, second):
+            if web is not None:
+                web.stop()
+        if worker is not None and worker.poll() is None:
+            worker.kill()
     assert one(engine, "SELECT status FROM run WHERE id = :r", r=rid) == "completed"
     pooled = run_view.show(engine, rid)["results"][0]
     assert (pooled["n_records"], pooled["n_alloys"], pooled["n_groups"], pooled["resid_df"]) == (97, 22, 20, 74)
     assert round(pooled["estimate"], 1) == 424.9 and round(pooled["std_error"], 1) == 64.4
     with engine.connect() as conn:
-        claims = conn.execute(text("SELECT worker, release_reason FROM run_claim WHERE run_id = :r"), dict(r=rid)).all()
-    assert len(claims) == 1 and claims[0].release_reason == "finished"
-    page = plain(signed_in(engine, url).get(f"/runs/{rid}").text)
-    assert "Level 6 of 6: tested answer" in page and "completed" in page
+        claims = conn.execute(text("SELECT release_reason FROM run_claim WHERE run_id = :r"), dict(r=rid)).all()
+    assert [c.release_reason for c in claims] == ["finished"]  # one claim
+    assert len(stub.requests) == 1  # one model request: the Analyst's, never repeated
+    assert one(engine, "SELECT count(*) FROM model_call WHERE run_id = :r", r=rid) == 1
+    assert "Level 6 of 6: tested answer" in page

```

### c157f51

```diff
commit c157f51726742e7b4b3d269dd3b6cb2acf3f4032
Author: kelawady <47933563+kelawady@users.noreply.github.com>
Date:   Sun Oct 11 15:25:17 2026 +0000

    Step 10a fix round 1, finding 1: a test of the command line's check of the text it printed
    
    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
---
 tests/test_confirmation_step10.py | 19 +++++++++++++++++++
 1 file changed, 19 insertions(+)

diff --git a/tests/test_confirmation_step10.py b/tests/test_confirmation_step10.py
index 8c0d1ec..e49a508 100644
--- a/tests/test_confirmation_step10.py
+++ b/tests/test_confirmation_step10.py
@@ -144,3 +144,22 @@ def test_what_is_stored_is_exactly_the_text_the_fingerprint_covered(engine, stub
     with engine.connect() as conn:
         assert conn.execute(text("SELECT shown FROM rules_confirmation WHERE run_id = :r"), dict(r=rid)).scalar() \
             == words == stored["shown"]
+
+
+def test_the_command_line_refuses_a_text_that_changed_after_it_was_printed(engine, stub, monkeypatch, capsys):
+    """Fix round 1, finding 1, on the command line: `confirm` prints the text, then records; if the renderer gives
+    another text by then, nothing is recorded."""
+    from hypocurate import cli_runs
+    rid = waiting(engine, stub)
+    original, calls = confirmation.render, []
+
+    def changing(c):
+        calls.append(1)
+        words = original(c)
+        return words if len(calls) == 1 else words.replace("informative groups", "independent groups")
+
+    monkeypatch.setattr(confirmation, "render", changing)
+    with pytest.raises(queries.QueryRefused) as refused:
+        cli_runs._confirm(engine, rid, "Grace Reviewer")
+    assert refused.value.code == "content_changed" and confirmations(engine, rid) == 0
+    assert "10 informative groups" in capsys.readouterr().out  # what was printed

```

### 36d98ba

```diff
commit 36d98ba22b6f7d42c3e68fc7c72347f07a5a7e2c
Author: kelawady <47933563+kelawady@users.noreply.github.com>
Date:   Sun Oct 11 15:24:22 2026 +0000

    Step 10a fix round 1: register
    
    confirmation_shown_fingerprint: the fingerprint covers the content and the text shown (earlier value in history);
    live_run_state: one snapshot per page, the new 14.4 test; parallel_suite: the shared read-only world fixture is the
    one exception to a database per test (owner); new runs_list_pages (50 a page; wording and size drafted for the
    owner's review). 157 entries.
    
    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
---
 hypocurate/assumptions.json | 79 +++++++++++++++++++++++++++++++++++++++------
 1 file changed, 69 insertions(+), 10 deletions(-)

diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 683953f..6ca0c7b 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -8936,9 +8936,9 @@
     "key": "confirmation_shown_fingerprint",
     "name": "A confirmation is of the content the page showed",
     "state": "in_force",
-    "statement": "The confirmation page sends back the SHA-256 of the canonical JSON (keys sorted, no spaces, UTF-8) of the content it displayed. confirmation.confirm compares it, inside the transaction that records the confirmation, with the run's current content, and refuses any difference as content_changed (as it refuses other content given whole by the command line). A page that sends no fingerprint is refused the same way. The website is the second caller of confirm, after the command line; confirm still takes one run and one name.",
+    "statement": "The confirmation page sends back the SHA-256 of the canonical JSON (keys sorted, no spaces, UTF-8) of the content it displayed and the exact text it displayed, together. confirmation.confirm reads the content and renders the text inside the transaction that records the confirmation, and refuses any difference from what was shown as content_changed, so the text stored is exactly the text the person saw (a renderer changed between showing and confirming is refused). A page that sends no fingerprint is refused the same way; the command line's confirm checks the text it printed the same way. The website is the second caller of confirm, after the command line; confirm still takes one run and one name.",
     "value": {
-      "text": "SHA-256 of the canonical content",
+      "text": "SHA-256 of the content and the text shown",
       "unit": null
     },
     "category": "operational",
@@ -8961,22 +8961,34 @@
       "status": "yes",
       "settings": [
         {
-          "ref": "python:hypocurate.pipeline.confirmation:content_fingerprint"
+          "ref": "python:hypocurate.pipeline.confirmation:shown_fingerprint"
         }
       ],
       "note": null
     },
     "tests": [
       "tests/test_confirmation_step10.py::test_the_fingerprint_is_the_sha256_of_the_contents_canonical_json_and_changes_with_any_item",
+      "tests/test_confirmation_step10.py::test_the_fingerprint_covers_the_content_and_the_text_together",
+      "tests/test_confirmation_step10.py::test_a_renderer_changed_between_display_and_submission_is_refused",
+      "tests/test_confirmation_step10.py::test_what_is_stored_is_exactly_the_text_the_fingerprint_covered",
       "tests/test_confirmation_step10.py::test_another_fingerprint_is_refused_as_content_changed_and_nothing_is_recorded",
       "tests/test_confirmation_step10.py::test_content_that_changed_after_it_was_shown_is_refused",
+      "tests/test_web_fix1.py::test_finding_1_a_page_confirmed_after_the_renderer_changed_is_refused",
       "tests/test_web_runs.py::test_a_confirmation_of_content_other_than_what_was_shown_is_refused",
       "tests/test_web_runs.py::test_a_confirmation_without_the_shown_contents_fingerprint_is_refused",
       "tests/test_confirmation.py::test_no_code_confirms_in_bulk_or_by_itself"
     ],
-    "history": [],
+    "history": [
+      {
+        "from": "2026-10-11",
+        "to": "2026-10-11",
+        "value": "SHA-256 of the canonical content",
+        "note": "the fingerprint covered the content only; ChatGPT's review of step 10a (finding 1) showed a renderer changed between showing and confirming passed it; the owner accepted the fix (2026-10-11)"
+      }
+    ],
     "notes": [
-      "Wording approved by the owner, 2026-10-11."
+      "Wording approved by the owner, 2026-10-11.",
+      "Fix round 1 (2026-10-11): the fingerprint covers the text shown as well (ChatGPT finding 1, accepted by the owner)."
     ]
   },
   {
@@ -9093,7 +9105,7 @@
     "key": "live_run_state",
     "name": "An open run's page updates itself and stops when the run ends",
     "state": "in_force",
-    "statement": "While a run is queued, waiting or running, its page asks for the run's state every 5 seconds (static/poll.js, a script of our own, not HTMX). The server decides when this ends: an open run's state carries its own address, an ended run's (completed or failed) carries none; the script asks again only when the state it received carries an address, and on an ended state reloads the page once to show the results. Every state read is read-only; the web service never claims a run or runs a stage, so closing the browser or restarting the web service never affects a run (criterion 14.4).",
+    "statement": "While a run is queued, waiting or running, its page asks for the run's state every 5 seconds (static/poll.js, a script of our own, not HTMX). The server decides when this ends: an open run's state carries its own address, an ended run's (completed or failed) carries none; the script asks again only when the state it received carries an address, and on an ended state reloads the page once to show the results. Every state read is read-only and comes from one database snapshot (a read-only REPEATABLE READ transaction for the whole page; fix round 1, finding 2); the web service never claims a run or runs a stage, so closing the browser or restarting the web service never affects a run (criterion 14.4).",
     "value": {
       "text": "every 5 s while the run is open",
       "unit": "seconds"
@@ -9135,8 +9147,10 @@
       "tests/test_web_state.py::test_an_open_runs_page_polls_its_own_state_and_an_ended_runs_page_does_not",
       "tests/test_web_state.py::test_the_state_fragment_carries_the_address_while_open_and_says_ended_once_ended",
       "tests/test_web_state.py::test_the_script_asks_again_only_when_the_state_it_received_carries_an_address",
-      "tests/test_web_state.py::test_14_4_a_run_goes_on_to_its_end_with_the_page_closed_and_across_a_web_restart",
-      "tests/test_web_isolation.py::test_opening_every_run_page_loads_no_model_library_and_no_pipeline_runner"
+      "tests/test_web_state.py::test_14_4_a_run_goes_on_to_its_end_across_a_restart_of_the_web_process",
+      "tests/test_web_isolation.py::test_opening_every_run_page_loads_no_model_library_and_no_pipeline_runner",
+      "tests/test_web_fix1.py::test_finding_2_a_run_that_completes_while_its_page_is_read_is_shown_in_one_state",
+      "tests/test_web_fix1.py::test_finding_2_the_state_fragment_of_such_a_run_keeps_polling"
     ],
     "history": [],
     "notes": [
@@ -9195,7 +9209,7 @@
     "key": "parallel_suite",
     "name": "The regression suite runs serially; a parallel run is for step 11",
     "state": "in_force",
-    "statement": "The suite runs serially (plain `pytest -q`). A parallel run with pytest-xdist was tried in step 10a and taken out: on 4 workers locally (2-core machine) it took 34 min 10 s against 36 min 06 s serially, and a test with a 6 s stall allowance (test_worker_fix1.py::test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance) failed under the load although it ran in a group on one worker; on 2 workers it took 31 min 37 s locally against 35 min 58 s serially (the same 2,292 tests and outcomes), and on GitHub the suite step took 26 min 20 s (green) and 26 min 45 s (that test failed again), against about 32 minutes serially. Every test still has a database of its own with a random name; the files that would need keeping apart from other load are listed in tests/conftest.py SERIAL_FILES. The suite's speed is revisited in step 11 as its own reviewed change.",
+    "statement": "The suite runs serially (plain `pytest -q`). A parallel run with pytest-xdist was tried in step 10a and taken out: on 4 workers locally (2-core machine) it took 34 min 10 s against 36 min 06 s serially, and a test with a 6 s stall allowance (test_worker_fix1.py::test_downtime_before_an_attempt_does_not_count_against_its_stall_allowance) failed under the load although it ran in a group on one worker; on 2 workers it took 31 min 37 s locally against 35 min 58 s serially (the same 2,292 tests and outcomes), and on GitHub the suite step took 26 min 20 s (green) and 26 min 45 s (that test failed again), against about 32 minutes serially. Every test has a database of its own with a random name, except the shared read-only world fixture of tests/test_web_runs.py (one database for that module's tests that only read); the files that would need keeping apart from other load are listed in tests/conftest.py SERIAL_FILES. The suite's speed is revisited in step 11 as its own reviewed change.",
     "value": {
       "text": "serial; revisit in step 11",
       "unit": null
@@ -9229,7 +9243,52 @@
     ],
     "history": [],
     "notes": [
-      "Wording approved by the owner, 2026-10-11."
+      "Wording approved by the owner, 2026-10-11.",
+      "2026-10-11: corrected after ChatGPT's review of step 10a: the shared read-only world fixture is the one exception to a database per test (owner)."
+    ]
+  },
+  {
+    "key": "runs_list_pages",
+    "name": "The runs list has pages of 50",
+    "state": "in_force",
+    "statement": "The runs list shows every run, newest first, in pages of 50, with \"Runs a to b of n\" and links to the newer and older pages, so every run stays reachable however many newer runs there are. Each page is read from one database snapshot (the count and the rows together). A page outside the list is not found.",
+    "value": {
+      "text": "50 runs a page",
+      "unit": "runs"
+    },
+    "category": "operational",
+    "affects": "The runs list.",
+    "reason": "ChatGPT's review of step 10a, finding 3: the list showed at most 200 runs with no pagination, so older runs, even waiting ones, could not be reached. The owner accepted the fix (2026-10-11); the page size is Claude Code's proposal.",
+    "evidence": [
+      "docs/reviews/step10a_review_chatgpt.md, finding 3; docs/reviews/step10a_fix_packet.md."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-11"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.run_view:RUNS_PER_PAGE",
+          "equals": 50
+        }
+      ],
+      "note": null
+    },
+    "tests": [
+      "tests/test_web_fix1.py::test_finding_3_an_old_waiting_run_stays_reachable_through_the_runs_list",
+      "tests/test_web_fix1.py::test_finding_3_the_list_says_which_runs_a_page_shows"
+    ],
+    "history": [],
+    "notes": [
+      "Wording and page size drafted by Claude Code for the owner's review (2026-10-11)."
     ]
   }
 ]

```

### 8e55c81

```diff
commit 8e55c81c57a2b40dd638dc3b2780178bac68c915
Author: kelawady <47933563+kelawady@users.noreply.github.com>
Date:   Sun Oct 11 15:42:52 2026 +0000

    CI: job limit 40 -> 60 minutes (owner's decision, 2026-10-11)
    
    The owner's words: "Yes, raise the job limit from 40 to 60 minutes. This is my decision." The serial suite step took
    34 min 59 s (job 36 min 27 s) on run 38149431419; fix round 1 adds slower tests. One line; nothing else in
    .github/workflows/ changes.
    
    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
---
 .github/workflows/tests.yml | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/.github/workflows/tests.yml b/.github/workflows/tests.yml
index 9334854..80d95b1 100644
--- a/.github/workflows/tests.yml
+++ b/.github/workflows/tests.yml
@@ -15,7 +15,7 @@ permissions:
 jobs:
   tests:
     runs-on: ubuntu-24.04
-    timeout-minutes: 40
+    timeout-minutes: 60
     steps:
       - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1
 

```

## 5. The new tests on the reviewed code (failed before)

Run on `431f880` before any fix (the command line's test was written after these and is checked by mutation m2):

```
                                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: module 'hypocurate.pipeline.confirmation' has no attribute 'shown_fingerprint'. Did you mean: 'plan_fingerprint'?

tests/test_confirmation_step10.py:138: AttributeError
=========================== short test summary info ============================
FAILED tests/test_web_fix1.py::test_finding_1_a_page_confirmed_after_the_renderer_changed_is_refused
FAILED tests/test_web_fix1.py::test_finding_2_a_run_that_completes_while_its_page_is_read_is_shown_in_one_state
FAILED tests/test_web_fix1.py::test_finding_2_the_state_fragment_of_such_a_run_keeps_polling
FAILED tests/test_web_fix1.py::test_finding_3_an_old_waiting_run_stays_reachable_through_the_runs_list
FAILED tests/test_web_fix1.py::test_finding_3_the_list_says_which_runs_a_page_shows
FAILED tests/test_confirmation_step10.py::test_a_renderer_changed_between_display_and_submission_is_refused
FAILED tests/test_confirmation_step10.py::test_the_fingerprint_covers_the_content_and_the_text_together
FAILED tests/test_confirmation_step10.py::test_what_is_stored_is_exactly_the_text_the_fingerprint_covered
8 failed, 1 passed in 80.66s (0:01:20)
```

## 6. The new and affected tests after the fixes

```
.............                                                            [100%]
157 passed in 543.22s (0:09:03)
```

## 7. Mutation checks

Each fault on a fresh copy of the package (PYTHONPATH from a folder without one); the named tests must fail. ERROR or HUNG would not count as caught.

```
== run 1 (control and m1-m4; the run stopped at m5, whose pattern did not match the code: no result, not counted)
control: clean: 61 passed in 164.40s (0:02:44)
m1_fingerprint_ignores_text: caught: 1 failed in 14.87s
m2_cli_checks_content_only: caught: 1 failed, 11 passed in 35.24s
m3_confirm_skips_fingerprint: caught: 1 failed in 14.80s
m4_snapshot_read_committed: caught: 1 failed, 1 passed in 23.89s
Traceback (most recent call last):
  File "/home/codespace/hc-work/step10a/mut/mutate.py", line 28, in <module>
    assert s.count(old) == 1, (name, s.count(old)); f.write_text(s.replace(old, new), encoding="utf-8")
           ^^^^^^^^^^^^^^^^^
AssertionError: ('m5_page_reads_show_apart', 0)
done

== run 2 (m5 with the corrected pattern, m6-m8)
m5_page_reads_show_apart: caught: 1 failed, 1 passed in 24.02s
m6_list_ignores_offset: caught: 1 failed, 3 passed in 43.05s
m7_list_no_next_page: caught: 1 failed, 3 passed in 42.46s
m8_list_limit_200_one_page: caught: 1 failed, 3 passed in 41.82s

```

## 8. Reference runs against main

```
fixed_plan.json identical
narrower.json identical
partly_original.json identical
planner_bcc.json identical
planner_fcc.json identical
reference.json identical

```

## 9. The whole suite

```
2301 passed, 1 warning in 2678.93s (0:44:38)
exit 0
```

## 10. Scripts

### packet/fixpacket.py
```python
"""Scratch: builds docs/reviews/step10a_fix_packet.md (fix round 1) from the files on disk."""
import pathlib, subprocess
R = pathlib.Path("/workspaces/hypocurate"); W = pathlib.Path.home() / "hc-work/step10a"
def sh(*a): return subprocess.run(a, cwd=R, capture_output=True, text=True, check=True).stdout
def tail(p, n=6): return "\n".join(pathlib.Path(p).read_text(encoding="utf-8").splitlines()[-n:])
commits = ["d812fa3", "c163337", "c157f51", "36d98ba", "8e55c81"]
out = ["# Build step 10a — fix packet (fix round 1)", "",
  f"Branch `step-10a-run-pages`, head `{sh('git','rev-parse','--short','HEAD').strip()}`. The reviewed head was `9fc3d9a` "
  "(the owner's register approval followed as `431f880`). Generated from the files on disk by a script (quoted at the "
  "end).", "",
  "## 1. The owner's decision", "",
  "> ChatGPT reviewed 10a: not safe to merge. I accept all four findings. Fix them on step-10a-run-pages, each with a "
  "failing test first, then write a fix packet for a short re-check. Do not merge.", "",
  "> Also: in register entry 8, say that every test has its own database except the shared read-only world fixture; "
  "my approval of the 8 register entries from my earlier message stands, with your entry 4 correction and \"Wording "
  "approved by the owner, 2026-10-11\".", "",
  "## 1a. A workflow change for the reviewer: the CI job limit, 40 to 60 minutes", "",
  "The owner's decision (2026-10-11), verbatim: \"Yes, raise the job limit from 40 to 60 minutes. This is my "
  "decision. Make it a single-line commit on step-10a-run-pages, changing nothing else in .github/workflows/, and note "
  "it in the fix packet so ChatGPT sees it.\"", "",
  "Why: run 38149431419 on `9fc3d9a` (the serial suite) was green, but its suite step took 34 min 59 s and the job "
  "36 min 27 s of the 40-minute limit; this round adds slower tests (205 runs for the list's pages; a web process "
  "started twice). The commit changes only `timeout-minutes` (one line); nothing else in `.github/workflows/`. It "
  "changes no check: Render still deploys `main` only after the checks pass. It only lets a run take longer before "
  "GitHub cancels it.", "",
  "```diff", sh("git", "show", "8e55c81", "--", ".github/workflows/tests.yml"), "```", "",
  "## 2. The review (verbatim)", "", "```", (R / "docs/reviews/step10a_review_chatgpt.md").read_text(encoding="utf-8"), "```", "",
  "## 3. What changed (the summary's fix-round section)", "",
  (R / "docs/reviews/step10a_summary.md").read_text(encoding="utf-8").split("\n> The sections below")[0].split("\n", 1)[1], "",
  "## 4. Commits", "", "```", sh("git", "log", "--oneline", "431f880..HEAD"), "```", ""]
for c in commits:
    out += [f"### {c}", "", "```diff", sh("git", "show", "--stat", "--patch", c), "```", ""]
out += ["## 5. The new tests on the reviewed code (failed before)", "",
  "Run on `431f880` before any fix (the command line's test was written after these and is checked by mutation m2):", "",
  "```", tail(W / "fix1_before.log", 14), "```", "",
  "## 6. The new and affected tests after the fixes", "", "```", tail(W / "fix1_after.log", 2), "```", "",
  "## 7. Mutation checks", "", "Each fault on a fresh copy of the package (PYTHONPATH from a folder without one); the "
  "named tests must fail. ERROR or HUNG would not count as caught.", "", "```", (W / "mut/mutations.log").read_text(encoding="utf-8"), "```", "",
  "## 8. Reference runs against main", "", "```", (W / "refdump/fix1_compare.txt").read_text(encoding="utf-8"), "```", "",
  "## 9. The whole suite", "", "```", tail(W / "fix1_full.log", 2), "```", "",
  "## 10. Scripts", ""]
for name in ("packet/fixpacket.py", "mut/mutate.py"):
    out += [f"### {name}", "```python", (W / name).read_text(encoding="utf-8"), "```", ""]
(R / "docs/reviews/step10a_fix_packet.md").write_text("\n".join(out), encoding="utf-8")
print("written")

```

### mut/mutate.py
```python
"""Scratch: fix round 1 mutation checks. Each fault is applied to a fresh copy of the package (with data/ beside
it), the named tests run with PYTHONPATH on the copy from a folder without a package, and the run must fail."""
import json, os, pathlib, shutil, subprocess, sys
R = pathlib.Path("/workspaces/hypocurate"); W = pathlib.Path.home() / "hc-work/step10a/mut"
FIX = ["tests/test_web_fix1.py", "tests/test_confirmation_step10.py"]
FAULTS = {
 "m1_fingerprint_ignores_text": ("hypocurate/pipeline/confirmation.py", '{"content": c, "text": words}', '{"content": c, "text": ""}', FIX),
 "m2_cli_checks_content_only": ("hypocurate/cli_runs.py", "shown_fingerprint=confirmation.shown_fingerprint(content, words))", "shown_fingerprint=None)", ["tests/test_confirmation_step10.py"]),
 "m3_confirm_skips_fingerprint": ("hypocurate/pipeline/confirmation.py", "(shown_fingerprint is not None and shown_fingerprint != _fingerprint(c, words))", "False", FIX + ["tests/test_web_runs.py"]),
 "m4_snapshot_read_committed": ("hypocurate/pipeline/run_view.py", 'conn.execution_options(isolation_level="REPEATABLE READ")', "pass", FIX),
 "m5_page_reads_show_apart": ("hypocurate/pipeline/run_view.py", "    shown = show_in(conn, run_id)\n    if shown is None:\n        return None\n    head = conn", "    shown = show(conn.engine, run_id)\n    if shown is None:\n        return None\n    head = conn", FIX),
 "m6_list_ignores_offset": ("hypocurate/pipeline/run_view.py", "o=(page - 1) * per_page", "o=0", FIX),
 "m7_list_no_next_page": ("hypocurate/pipeline/run_view.py", '"next": page + 1 if page < pages else None', '"next": None', FIX),
 "m8_list_limit_200_one_page": ("hypocurate/pipeline/run_view.py", "pages = max(1, -(-total // per_page))", "pages = 1; per_page = 200", FIX),
}
env = {**os.environ, "DATABASE_URL": [l.split("=", 1)[1].strip() for l in (R / ".env").read_text().splitlines() if l.startswith("DATABASE_URL=")][0]}
results = {}
names = sys.argv[1:] or ["control", *FAULTS]
for name in names:
    copy = W / "copy"
    shutil.rmtree(copy, ignore_errors=True); copy.mkdir()
    shutil.copytree(R / "hypocurate", copy / "hypocurate", ignore=shutil.ignore_patterns("__pycache__"))
    (copy / "data").symlink_to(R / "data")
    files = FIX + ["tests/test_web_runs.py"]
    if name != "control":
        path, old, new, files = FAULTS[name]
        f = copy / path; s = f.read_text(encoding="utf-8")
        assert s.count(old) == 1, (name, s.count(old)); f.write_text(s.replace(old, new), encoding="utf-8")
    run_dir = W / "run"; run_dir.mkdir(exist_ok=True)
    try:
        out = subprocess.run([str(R / ".venv/bin/pytest"), "-q", "-p", "no:cacheprovider", "-x", "--rootdir", str(R),
                              *[str(R / f) for f in files]], cwd=run_dir, capture_output=True, text=True,
                             env={**env, "PYTHONPATH": str(copy)}, timeout=1800)
        tail = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "NO OUTPUT"
        verdict = ("clean" if out.returncode == 0 else "ERROR") if name == "control" else (
            "caught" if out.returncode == 1 and "failed" in tail else "SURVIVED" if out.returncode == 0 else "ERROR")
    except subprocess.TimeoutExpired:
        tail, verdict = "timeout", "HUNG"
    results[name] = (verdict, tail)
    (W / f"out_{name}.txt").write_text(out.stdout if verdict != "HUNG" else "timeout", encoding="utf-8")
    print(f"{name}: {verdict}: {tail}", flush=True)

```
