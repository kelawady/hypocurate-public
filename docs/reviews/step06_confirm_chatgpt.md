# Step 6 — second-model confirmation (ChatGPT, 2026-10-06)

Confirmation review of `docs/reviews/step06_fix2_packet.md` (branch `step-06-eligibility`). Saved verbatim as the owner gave it. The owner asked for both remaining problems to be fixed, each with tests that fail on the code before it (see `docs/reviews/step06_summary.md`).

---

1. Concurrency — fixed. Completed Checks and coverage are now verified within the same locked transaction that reads Inclusion’s inputs. Required per-set flags cannot silently fall back to primary flags. The later write checks still catch intervening changes. I found no remaining interleaving bypass under the established locking and immutability rules.
2. Fixed rules — partly fixed. Paper identity no longer depends on clustering, and the outcome setting can no longer disable physical checks. However, a permitted combination still admits exact duplicates twice:
   - A and B cite the same DOI and have identical conditions and values.
   - C, from a third source, has matching conditions and values but no paper identity.
   - Checks labels the entire fully connected group possible duplicate, losing the definite A–B exact-duplicate relationship.
   - A plan choosing to count possible duplicates separately admits A, B and C.
   With another grain size present, I reproduced all three entering primary. Preserve exact-duplicate relationships inside mixed groups and enforce counted-once handling before applying the possible-duplicate choice.
3. Duplicate rule entries — fixed. Duplicate entries are rejected, and the guard now uses the same ordered lookup as rule application. The previous first-entry/last-entry discrepancy is closed.
4. Freeze check on primary — partly fixed. It checks membership independently of the eligibility-rule lookup, which is useful. But it trusts the same Checks classifications that built the set; it does not independently verify duplicate relationships. In the example above, primary_set_problems() returns no problems because it sees only a possible-duplicate flag.
   Add the mixed-group case both as a normal pipeline test and as a freeze-check test with eligibility safeguards bypassed. The checker needs the retained exact-pair information.
New issue introduced: unequal reference text is treated as proof of different papers. same_paper() returns False when normalized citation strings differ—even if the difference is merely punctuation or citation style and one DOI is missing. That suppresses matching entirely. The summary says such differences yield “unknown,” but the code does otherwise.
Use unequal authoritative identifiers to establish different papers; unequal citation text alone should remain unknown. I reproduced the current false-negative matching behavior.
I reconstructed the patched code and ran targeted reproductions; I did not rerun the reported 888-test database suite.
Not safe to merge.
