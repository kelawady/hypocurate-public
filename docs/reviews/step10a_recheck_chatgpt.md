One problem remains: pagination is not stable while runs are added.
Files: hypocurate/pipeline/run_view.py — runs_list(); hypocurate/web/templates/runs.html.
The query uses ORDER BY r.id DESC LIMIT 50 OFFSET …. Each page has a consistent snapshot, but successive pages see different snapshots.
Reproduced case: with runs 1–101, page 1 shows 101–52. Insert run 102, then open page 2: it shows 52–3, repeating run 52. If 50 new runs arrive between each page request, advancing pages repeatedly returns the same block instead of progressing toward the old waiting run.
Smallest fix: use an ID cursor for navigation—“older than the last run displayed”—rather than an offset. Add a test inserting runs between page requests and verifying traversal without repeats. The current 205-run test keeps the list static, so it misses this. The register’s guaranteed-reachability wording is premature.
The other three findings are closed on inspection:
- The fingerprint includes content and rendered text; confirmation checks and stores the same rendered string. The renderer-only tests genuinely change the wording between display and submission.
- The run view and its helpers share one read-only REPEATABLE READ transaction. The regression tests actually commit completion through other connections between reads.
- Criterion 14.4 now stops and restarts a separate web process while the worker is held at its Analyst request, then checks completion, one claim and one request.
The supplied workflow diff changes only 40→60 minutes. The register corrections match the stated decisions, and I found no weakened protection in the changed tests.
Verification: reproduced the pagination defect using the reconstructed runs_list() function with mocked database results, and directly checked the new fingerprint function. PostgreSQL snapshot tests, web-process restart tests and the full suite were inspected, not rerun.
not safe to merge
