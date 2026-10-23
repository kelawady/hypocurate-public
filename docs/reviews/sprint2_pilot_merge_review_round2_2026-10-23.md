# Sprint 2 merge review — round 2, 23 October 2026

Assessment of the revised packet's reported evidence; tests were not independently rerun. References are to sprint2_pilot_merge_packet.md.

## 1. Previous A items

- **A1 — Partly (§9, lines 269–290):** the scope now includes the shared safeguard files, tests and startup behavior, but the requested implementation diffs and corresponding test changes are still absent.
- **A2 — Partly (§10, lines 292–300):** the new lock refusal has mutation coverage, but the packet still does not show a captured ordinary Planner request establishing whether the widened vocabulary changes its prompt or response schema.
- **A3 — Resolved (§7, lines 206–222):** the retained 0010 checkout performs the downgrade before the code revert, and the rehearsal demonstrates both the wrong-order failure and restoration of the 0009 catalog and row counts.
- **A4 — Partly (§11, lines 302–318):** reservation, retry, Reconciler and monthly-cap coverage is now described, but verification lacks an explicit document-cap exhaustion test and the $2 budget resets per invocation, requiring either cumulative per-document enforcement or explicit owner approval of that changed guarantee.
- **A5 — Partly (§7a, lines 224–267):** the stand-in restore, production-image checks and before/after-load reference runs are reported, but restoration and validation of the actual live backup remain pending the owner's file.

## 2. Tests for the three defects

- **Fixed-plan refusal — Yes (§7a, lines 241–242):** `test_a_sprint1_run_on_a_database_holding_the_pilot_source_locks_a_plan_without_it` is explicitly reported to fail without the chosen-source filter fix.
- **Document-cap crash — Yes, as reported (§9, line 282; §11, line 314):** `test_every_refusal_code_of_the_spending_module_is_a_known_failure_that_stops` is identified as finding the missing `spending_cap_document` failure entry.
- **Bundle invariant bypass — Partly (§12, line 324):** the consistent-hashes/invalid-freeze rejection test is named, but the packet does not explicitly report its failure with the bundle invariant check removed or on the pre-fix code.

## 3. Newly blocking issue

- **Clarify the worker/write-pause sequence (§7, line 222; §7a, lines 258–267):** the worker is suspended and site use prohibited through checks, yet the sequence requests live runs without an explicit worker resume, so distinguish controlled validation writes from ordinary traffic and state when the worker resumes.
