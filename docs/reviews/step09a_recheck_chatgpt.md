The original five findings are closed. One gap remains in the new requirement that every new run stores its effective ceiling.
- File: db/migrations/versions/0007_rules_confirmation.py
- Failing case: a direct SQL insert explicitly supplying spending_ceiling = NULL still succeeds. The column remains nullable, the check explicitly permits NULL, and a default applies only when the value is omitted. The update trigger then prevents correcting it.
- Smallest fix: add an insert trigger that replaces NULL with the default cap. This preserves historical empty values while ensuring new runs have a ceiling. Add a direct-SQL test for explicit NULL.
This does not bypass the existing spending caps, but it contradicts the owner’s new requirement and the packet’s “never empty for a new run” claim.
The other fixes check out:
- Stored Planner failures prevent another request; Critic spending/accounting failures prevent the Analyst; Analyst accounting failures prevent completion.
- Confirmed Planner and narrower runs resume without waiting again.
- Confirmation, source insertion and sealing take the same advisory lock. The direct-SQL tests and two-connection sealing tests genuinely exercise refusal and blocking in both orders.
- confirm --ceiling is removed.
- The database rejects cancellation-labelled failures from running while retaining ordinary failures.
- I found no weakened existing test. The changed ceiling expectation correctly follows the owner decision. The register otherwise matches the fixes.
Reproduced: the corrected resume branches using the packet’s function bodies with mocked database dependencies, including the failure stops and confirmed-run routing.
Read only: PostgreSQL triggers, concurrency tests, migration behavior and reported suite output. I did not rerun PostgreSQL or make model calls.
not safe to merge
