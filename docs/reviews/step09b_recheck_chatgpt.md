# Step 9b — ChatGPT's second review (re-check of the fix round 1 packet, head 60f5150)

Received 2026-10-09 from the owner; quoted verbatim.

Two problems remain.
1. Model-call completion bypasses the ownership check.
   File: hypocurate/pipeline/agents/spend.py, finish().
   This function updates model_call directly through run_transaction, without calling owner_holds() or writes.write().
   Failing case: a child loses its WORK-lock connection, then receives the provider’s response before it is killed. It can still finish an open call after losing ownership, provided recovery has not closed that call first. The new checks on ordinary writes and reservations do not protect this write.
   Smallest fix: check ownership inside the run-scoped finish() transaction, after acquiring the run lock and before updating the call, using the same claim-row locking protocol. Test that a stale child cannot finish an open call.
2. A committed refusal can still be mistaken for a recoverable save failure.
   Files: hypocurate/pipeline/recovery.py, refusal restoration; hypocurate/pipeline/agents/spend.py, reservation transaction.
   Failing case: PostgreSQL commits the refusal audit row, but the connection fails before the commit acknowledgement reaches Python. The caller sees a database failure and successfully saves the stage as failed with reservation_failed. Recovery searches for committed refusals only on stages still marked running, so it misses this refusal. The Planner can be repeated, or the Critic failure excused and the Analyst reached. Across a month change, the next reservation can pass.
   Rechecking caps prevents a fresh cap violation; it does not preserve the required stop following a committed refusal.
   Smallest fix: consult durable refusal evidence when classifying failed, recoverable stages too. Preserve the original stage history rather than rewriting an already-finished stage. Add a test that commits the refusal transaction and then raises a connection error before returning.
The remaining requested fixes look correct on inspection. FOR KEY SHARE blocks the explicit FOR UPDATE takeover while allowing heartbeat updates. The revised race and monitoring tests retain their substantive assertions. I found no additional problem in shutdown cleanup, fresh-Critic failure handling, stall allowance, recovery counting, two-batch coverage or connection settings. The supplied Render diff contains only the worker plan and comment changes. The register’s “every write” guarantee remains inaccurate because of finding 1.
Verification: I reproduced the missing ownership check using the actual finish() function with mocked database access. Focused worker probes also confirmed cleanup before release, shutdown before launch and the independent timeout path. Finding 2 is from code inspection. I did not rerun PostgreSQL concurrency tests, migrations or the Docker suite.
not safe to merge
