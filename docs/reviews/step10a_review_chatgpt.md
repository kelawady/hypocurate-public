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
