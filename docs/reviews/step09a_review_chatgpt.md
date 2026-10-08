Not ready to merge. I found five concrete problems.
1. Resuming can bypass an earlier accounting failure or repeat the Planner.
   File: pipeline/orchestrator.py — prepare() and proceed().
   Failing cases:
   - A Planner reservation fails, leaving a failed stage and a running run. prepare() searches only for a done Planner stage, finds none and invokes the Planner again.
   - A Critic reservation fails. On resume, proceed() sees an existing Critic stage and skips it without reading its failure code, allowing the Analyst’s paid request.
   - An existing Analyst accounting failure is similarly skipped, allowing completion—including the partly-sufficient path.
   Smallest fix: inspect the latest stored stage regardless of status before deciding what comes next. Preserve RUN_STOPS and spending-failure behavior across resumes. Leave interrupted-stage recovery and the permitted Planner retry to 9b.
   I reproduced the first two control-flow failures with the packet’s function bodies and mocked dependencies. The register’s resumable_run and run_order_and_failures claims currently overstate this protection.
2. The database does not enforce source freshness, and Python’s check can race registration.
   Files: pipeline/confirmation.py; db/migrations/versions/0007_rules_confirmation.py.
   Failing case: a run waits on version V1; V2 is sealed. A direct SQL confirmation still passes because the trigger compares the narrowing’s V1 with the run’s V1—not with the latest sealed version. A newly registered source is likewise unchecked by the trigger.
   The ordinary confirmation path also has a window between source_changes() and insertion: registration can commit during that window without invalidating either historical comparison.
   Smallest fix: enforce the freshness check in the database and serialize it with source registration/sealing using a shared locking protocol. Add direct-SQL and two-connection tests. The existing database test checks mismatched historical versions, which is a different condition.
3. The normal run() entry point cannot reliably resume confirmed Planner or narrower runs.
   File: pipeline/orchestrator.py — prepare().
   Failing case: confirmation succeeds, the run returns to running, then execution stops before or after the rules lock. Calling run() again enters prepare(), which attempts _wait() again. The database correctly rejects this; the exception path can mark the recoverable run failed. A confirmed run still in waiting instead returns without becoming ready.
   Smallest fix: recognize an existing confirmation or locked plan in prepare() and route to proceed() without another wait.
   I reproduced the repeated-wait branch. The resume tests largely avoid it by using fixed-plan runs and calling proceed() directly. Add Planner and narrower-run tests through run().
4. A lower ceiling supplied at confirmation disappears after a restart.
   File: cli_runs.py — _confirm().
   Failing case: dispatch with a $1 ceiling, then use confirm --ceiling 0.10. That lower limit exists only in the child’s payload. After interruption, a resume without that argument reads the stored $1 ceiling and can exceed the requested ten cents.
   Smallest fix: remove the confirmation-time override and require the durable ceiling at dispatch, or persist any accepted tightening separately and apply it on every reservation.
5. “Cancel only queued or waiting” is not a database rule.
   Files: pipeline/queries.py; migration 0007.
   Failing case: direct SQL can change a running run with no open stage/call to failed, supplying failed_at and a cancelled: … reason. The ordinary running-to-failed transition permits it; the new trigger adds no cancellation-specific restriction.
   Smallest fix: add a database guard restricting cancellation-labelled failures to queued/waiting runs, with a direct-SQL regression test. Keep ordinary operational failures permitted.
The “empty” spending_ceiling is not limited to old runs. New dispatches without --ceiling intentionally store NULL; that means no additional ceiling, while the run and monthly caps still apply. Supplied ceilings are checked and immutable.
The two highlighted assertion changes are correct; I found no weakened existing protection. The missing coverage is the adverse resume and database cases above. The migration’s exact-restoration and transactional round-trip tests look appropriate on inspection, but I did not rerun PostgreSQL, the full suite or image checks. No model calls were made.
not safe to merge
