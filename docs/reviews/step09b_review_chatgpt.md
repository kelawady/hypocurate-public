Not ready to merge. The main gaps are failure handling and ownership during recovery, rather than the ordinary kill-and-restart path.
1. A spending refusal can become an “interruption” if saving the stage fails.
   Files: pipeline/recovery.py; the agent stage-saving path.
   Failing case: the Critic reaches a cap, but saving its failed stage fails—or the worker dies before that save. The stage remains running. Recovery overwrites its cause with interrupted, then permits the Analyst. The equivalent Planner case permits a repeat. A monthly refusal could subsequently disappear when the month changes.
   The tests manufacture an already-saved spending-failure stage, so they miss this boundary.
   Smallest fix: preserve the spending refusal durably against its invocation and consult that evidence before classifying a running stage as interrupted. Where the existing refusal audit row was saved, use it. Test an actual refusal followed by failure to save the stage, not just a preconstructed failed row.
2. An exception can release a claim while its child is still alive.
   Files: worker.py:work; access/guarded.py:GuardedChild.stop.
   Failing case: start_guarded() succeeds, then record_child() fails. The exception handler releases the claim without stopping the child. If the child has not acquired WORK yet, another worker can claim and begin recovery before the first child starts working.
   I reproduced the release occurring while the child remained alive. Shutdown also sends SIGTERM and waits 30 seconds without checking success or escalating before release.
   Smallest fix: retain the child reference and stop/reap it on every exit path before releasing ownership. Escalate an unsuccessful SIGTERM to SIGKILL. Also check the shutdown event before launching a child.
3. Loss of the advisory-lock connections does not stop their owners.
   Files: pipeline/queue.py:Lease, Heartbeat; pipeline/orchestrator.py:work_guarded.
   Failing case: a database restart or connection failure removes CLAIM and WORK while the processes remain alive. Neither dedicated lock connection is monitored. After a stale-claim takeover, the old heartbeat can update zero rows without noticing, while the old child continues using other connections.
   Smallest fix: fail closed when ownership is lost and bind child work to the current claim identity, rejecting stale owners before further requests or writes. Add a test that terminates the lock-holding database sessions while the processes survive. Killing the worker does not test this case.
4. recovered=True also excuses a new Critic accounting failure.
   File: pipeline/orchestrator.py:proceed.
   Failing case: recover a run stopped before the Critic. Its newly executed Critic then returns recording_failed. The filter ignores that failure because the whole run has recovered=True, and proceeds to the Analyst without first closing the newly lost call.
   I reproduced the Analyst path and completion attempt after this fresh failure.
   Smallest fix: apply the recovery exception only to previously stored stages that recovery processed. Failures returned by a newly executed Critic must stop normally.
5. A blocked monitoring query defeats both the watchdog and graceful shutdown.
   File: worker.py:_watch.
   Failing case: the last-write query blocks on the database or network. The main thread cannot revisit the 1,800-second deadline or the shutdown event until that query returns. Catching exceptions does not bound a call that never returns.
   I reproduced both checks remaining blocked beyond their deadline.
   Smallest fix: bound monitoring connection/query operations and keep the child’s wall-clock termination independent of their completion. Test a blocked monitoring connection, not only a blocked child.
6. Downtime counts against a newly resumed child’s stall allowance.
   Files: worker.py:_watch; pipeline/queue.py:seconds_since_last_write.
   Failing case: a run stops between stages, then remains idle for over 900 seconds. Recovery has no open stage or call to close. The resumed child begins statistics, but the first monitoring check sees the old timestamp and kills it immediately. Repeated attempts can exhaust recovery without receiving a useful execution window.
   I reproduced this with a fresh child and a last-write age of 901 seconds.
   Smallest fix: start the inactivity allowance at the current attempt’s launch, then reset it on subsequent progress. Historical downtime should not consume that allowance.
7. The recovery limit is off by one for worker-managed runs.
   File: pipeline/recovery.py:recover.
   Failing case: after the first worker loss, its released/lost claim is already counted in earlier. Adding one reports recovery 2. After the third loss, it reports 4 and fails before allowing the third recovery attempt.
   Smallest fix: count recovery attempts explicitly, excluding the initial execution. Test three recoveries followed by refusal of the fourth using actual claim histories.
The idle-loop test replacements preserve their original checks. The missing coverage includes the cases above, as well as the acknowledged two-batch Critic case. The register’s ownership, timeout and recovery guarantees therefore exceed what the code currently establishes.
client_connection_check_interval is worth adding. The worker tests already enable it at 100 ms, while production does not. A modest worker-session setting such as one second would help PostgreSQL abandon queries after a disconnected child. It does not replace bounded monitoring or ownership checks, and network-failure detection may also require keepalive settings. PostgreSQL documentation
I found no additional migration blocker on inspection. The stated Render resource increase is compatible with the old code, but the packet does not include the actual render.yaml diff, so I cannot independently confirm it is the only change.
Verification: I ran isolated probes of the packet’s worker and orchestrator function bodies with mocked dependencies. Database locking, migration behavior, spending-save failures and the supplied integration results were reviewed, not rerun. No model calls were made.
not safe to merge
