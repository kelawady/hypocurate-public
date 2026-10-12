The three original fixes are addressed. Two issues remain:
1. The downgrade can delete newly committed audit history.
   File: db/migrations/versions/0009_action_record.py, downgrade().
   Failing case: A transaction inserts the first action but has not committed. The downgrade’s IN_USE query sees an empty table. DROP TABLE then waits for that transaction; once it commits, the drop proceeds and deletes its audit record. The current migration tests do not exercise this interleaving.
   Smallest fix: Acquire LOCK TABLE action_record IN ACCESS EXCLUSIVE MODE before checking whether it contains rows, in the same transaction. Add a two-connection test with an uncommitted insert.
2. The isolation probe still does not cover every write path.
   File: tests/test_web_isolation.py, PROBE_10B.
   It edits a draft and returns it, but never edits that returned query to exercise new_version(). Neither fresh-process probe exercises confirmation or cancellation POSTs.
   Smallest fix: Add those successful actions to the fresh-process probe before checking loaded modules. I found no actual forbidden model or worker call; this is a remaining coverage gap.
The other requested checks look sound:
- Version IDs and fingerprints now bind actions to the displayed content, with checks under the pipeline’s version lock. The two-session tests genuinely interleave viewing, another session’s change, and stale submission; they are not simultaneous transaction tests.
- Audit rows use the write’s own transaction. Website names are required, and update, delete and truncate are blocked.
- Adding via preserves one run, one name and the two permitted confirmation callers.
- The revised stall test retains its purpose: downtime exceeds the allowance, the first insert is delayed, and completion remains required. Production stays at 900 seconds. I found no weakened existing assertion.
Reproduced: The actual export helpers preserve formula-like strings as XLSX string cells, neutralize all six specified CSV prefixes, and preserve numbers. Read only: Database enforcement, migration tests, session tests, isolation and worker timing; I could not rerun PostgreSQL or the full suite.
Additional constructed-source commit: Sound as described, but not independently verified because it is absent from the packet. One wording qualification: website “dispatch again” can inherit an existing CLI-created test mark; it does not create that mark itself.
not safe to merge
