# Build step 6 — fourth fix packet (the second confirmation's problem)

Date: 2026-10-06. Branch: `step-06-eligibility`. Covers only the problem the second confirmation (`docs/reviews/step06_confirm2_chatgpt.md`) found: commits after `8c9b062` (the third fix packet) up to `1ca5cc0`. Generated from the files and commits on disk by a script. The full step is in `docs/reviews/step06_review_packet.md`, the earlier rounds in `docs/reviews/step06_fix_packet.md`, `step06_fix2_packet.md` and `step06_fix3_packet.md`, and the step summary (updated) in `docs/reviews/step06_summary.md`.

## How to use this packet

The owner asked: records linked by a chain of exact pairs are one measurement with one survivor by the survivor rule (last tie-break the source's stable identity, never an id or an order); a chain touching a definite conflict enters with none of its records and none of the conflicting ones; the freeze check verifies at most one record per chain; a permutation test (ids and insertion order) over the reviewer's case and the real reference data; and a search for other id- or order-dependent places. Section 1 has all of it. Please return a dated confirmation: for the problem, closed, partly closed or open, and any new finding.

## Contents

1. What was fixed (from the summary)
2. The second confirmation
3. The fixes, commit by commit (message and full diff)
4. Mutation checks of this round
5. Reference numbers recomputed after the fixes
6. Suite results

## Commits

```
ec61879 Step 6: second confirmation review saved verbatim
4efc69d Step 6 confirmation-2 fix: identity decisions never depend on ids or order
1ca5cc0 Step 6 summary: the second confirmation and its fix
```

## 1. What was fixed

## Second confirmation (ChatGPT, 2026-10-06) and fix

The text is in `docs/reviews/step06_confirm2_chatgpt.md`; the commits and diffs in `docs/reviews/step06_fix4_packet.md`. Confirmed fixed: mixed groups, paper identity, non-unique exact matches, the "definite first" equivalence (for that change), the two label-over-pair fixes. **New problem:** overlapping exact pairs were resolved pair by pair in flag-id order, so the primary set depended on database ids. The reviewer's case: A (MPEA, DOI D), B (DOI D, reference Y), C (no DOI, reference Y); A-B exact, B-C exact, A-C possible; possible duplicates counted both. In one id order A and C survived, in another only A. Both passed the freeze check.

| Item | Fix | New tests (failed before the fix) |
|---|---|---|
| Overlapping exact pairs | Rule 7 decides whole groups, never flag by flag. **(1)** Every pending record of an ambiguous group: `identity_unresolved`. **(2)** Records linked by a chain of exact pairs are one measurement, and a definite conflict links its records too. A connected group that touches a conflict follows the plan's conflict rule: neither (none of the chain and none of the conflicting records enters), or the survivor's value (one survivor). A group of exact duplicates only keeps exactly one survivor. **(3)** The plan's possible-duplicate choice on what remains, per connected possible group. Survivors come from the survivor rule, whose last tie-break is the source's stable identity (source, origin key, item index), never an id or an order. | `test_the_reviewers_chain_gives_the_same_result_for_every_id_and_order` (all 6 id assignments × 3 orders; identical decisions in every set, fingerprint and freeze-check result; A survives, B and C counted once); `test_a_chain_touching_a_conflict_enters_with_none_of_its_records` |
| The freeze check | `primary_set_problems` forms the chains itself from Checks' exact flags and allows at most one record per chain, and per group linked by a definite conflict. | `test_the_freeze_check_allows_at_most_one_record_per_chain` (A and C in, B out: no single pair is wholly inside) |
| Permutation over the pipeline | — | `test_permuted_ids_and_insertion_order_give_the_same_frozen_result`, on the controlled extract (marked) and on the **real reference data**. Each source's records are stored shuffled, the sources in shuffled order, and unrelated records inserted first. Required: identical decisions for every record, identical membership of the primary set and every sensitivity set, identical per-set rules, identical fingerprint. Passes before and after the fix: these data have no overlapping exact pairs. |

**The reviewer's case cannot arise through the sprint 1 adapters:** an exact pair needs known, equal test conditions on both sides, and Texas A&M reports no test temperature. So with only two MPEA-layout sources, no record can be exactly linked to two others. The case is tested on the same functions Checks, Inclusion and the freeze use (`raise_flags`, `set_flags`, `all_sets`, `primary_set_problems`, and `freeze_fingerprint`, factored out of the freeze unchanged for this). The pipeline permutation test covers what the adapters can produce.

**Other places where an outcome could depend on ids or ordering** (looked for, as asked):
- **The one real case:** rule 7's flag-by-flag loop, sorted by flag id. Fixed above.
- **Order only, no effect on any decision:**
  - the order of the rows Inclusion reads (`ORDER BY id`);
  - the order Checks creates flags (and so their ids);
  - the per-set flags' internal ids;
  - union-find's internal roots (the components are the same);
  - the order of `compared_values` numbers (audit only; not in the binding or the fingerprint).
- **Already stable:**
  - eligibility-rule lookup follows the plan's own order (content, not the database);
  - survivors use the survivor rule;
  - pairwise comparisons are symmetric;
  - the Checks binding and the freeze fingerprint use sorted stable identities;
  - the grain-size count is a set;
  - sources are stored in key order.
- **Informational, not a decision:** the Inclusion stage's stored "differences from primary" are keyed by record id (they differ between runs, as ids do). They are not in the fingerprint or the binding; the decisions themselves are compared by identity in the permutation test.

**Reference numbers and fingerprint after this fix: none changed, and the freeze fingerprint is identical (`93c44b22…`).** The reference run raises no flag at all, so rule 7 never acts on it.


## 2. The second confirmation

````markdown
# Step 6 — second-model confirmation, round 2 (ChatGPT, 2026-10-06)

Confirmation review of `docs/reviews/step06_fix3_packet.md` (branch `step-06-eligibility`). Saved verbatim as the owner gave it. The owner asked for the new problem to be fixed, with tests that fail on the code before it (see `docs/reviews/step06_summary.md`).

---

1. Mixed groups — fixed for the A, B, C case. The exact A–B relationship survives as its own flag. Pipeline tests check counted-once handling, and the freeze test bypasses eligibility to demonstrate that the retained pair independently causes refusal. The freeze checker no longer relies solely on the group label.
2. Paper identity — fixed. Unequal reference text now means unknown. Unequal normalized DOIs still establish different papers. Matching uses the shared function, including sensitivity sets.
3. Non-unique exact matches — fixed for primary. Those records remain in an unresolved-identity group, which primary excludes regardless of the possible-duplicate choice. Counting possible duplicates separately cannot override that exclusion. They may enter the explicitly named sensitivity set, as intended.
4. “Definite first” mutation — the equivalence claim is correct for that specific change. With one survivor ordering, resolving a subgroup before its enclosing counted-once group cannot remove the enclosing group’s highest-priority survivor. If possible duplicates are counted separately, their group rule removes nothing anyway.
   That does not establish that ordering among definite pairs is harmless. The new issue below demonstrates otherwise.
5. The two additional label-over-pair fixes — fixed. Retaining the exact pair inside a conflict-labelled group gives the freeze checker that relationship. Keeping a conflict confined to its definite pair correctly avoids excluding a third record whose links are only possible.
New issue: overlapping retained exact pairs make primary depend on database IDs.
I reproduced this with identical conditions and values:
- A: MPEA, DOI D, reference text X.
- B: Texas A&M, DOI D, reference text Y.
- C: extract, no DOI, reference text Y.
Checks finds A–B exact through DOI, B–C exact through reference text, and A–C possible. Choose the permitted “possible duplicates counted separately” plan and supply another grain size.
The result changes with pair-processing order:
- A–B first: B is excluded; processing B–C then leaves C. A and C survive.
- B–C first: C is excluded; A–B then excludes B. Only A survives.
Swapping record IDs produced these two results. Both passed the freeze invariant checker. This can change counts and statistical results without changing the plan or source evidence.
Resolve overlapping definite pairs using a stable, explicitly defined procedure based on the survivor priority—not generated flag or record IDs. Add a regression that permutes IDs and insertion order and compares the frozen memberships.
These conclusions use the packet and targeted reconstructed-code probes; I did not rerun the reported 896-test database suite.
Not safe to merge.
````

## 3. The fixes, commit by commit

### `ec61879 Step 6: second confirmation review saved verbatim`

````diff
ec618797d54b15e5c6a1c43aded975d7ca4b9c35

Step 6: second confirmation review saved verbatim

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

### `4efc69d Step 6 confirmation-2 fix: identity decisions never depend on ids or order`

````diff
4efc69d72163a36989970d9816e15fee66b6c0cd

Step 6 confirmation-2 fix: identity decisions never depend on ids or order

Overlapping exact pairs were resolved pair by pair, in flag-id order, so the
primary set depended on database ids (the reviewer's A-B-C case gave two
results). Rule 7 now decides whole groups: records linked by a chain of
exact pairs are one measurement with one survivor by the survivor rule
(last tie-break: source, origin key, item index); a chain touching a
definite conflict follows the conflict rule as one group (neither: none of
the chain and none of the conflicting records); then the possible-duplicate
choice per connected possible group. The freeze check forms the chains
itself and allows at most one record per chain. The fingerprint
calculation is factored out (no change) so the pure tests can use it.

New tests failed on the code before this change (the A-B-C case with ids
and order permuted; a chain touching a conflict; the chain-aware freeze
check); the permutation test over the controlled extract and the real
reference data passes before and after (no overlapping chains there).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index a090a94..df4c851 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -2321,7 +2321,8 @@
       "The step 1 answer file, its builder and README carry this wording since step 6 (owner's approval, 2026-10-05).",
       "Rule 1 can only decide a possible duplicate: paired records otherwise cite the same paper.",
       "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants').",
-      "Step 6 review, finding 3 (2026-10-06): the lock refuses a survivor order or a grouping that leaves out a chosen source, and the final tie-breaker is the record's stable identity (source, origin key, item index), never a database id."
+      "Step 6 review, finding 3 (2026-10-06): the lock refuses a survivor order or a grouping that leaves out a chosen source, and the final tie-breaker is the record's stable identity (source, origin key, item index), never a database id.",
+      "Confirmation round 2 (2026-10-06): a chain of exact pairs keeps exactly one survivor by this rule; its last tie-break is the record's stable identity (source, origin key, item index)."
     ],
     "tests": [
       "tests/test_checkpoints.py::test_the_lock_refuses_settings_that_leave_out_a_chosen_source",
@@ -2330,7 +2331,8 @@
       "tests/test_eligibility.py::test_survivor_rule_one_a_source_other_than_mpea_survives_when_it_alone_carries_the_doi",
       "tests/test_eligibility.py::test_survivor_rule_three_the_lowest_row_within_one_source",
       "tests/test_eligibility.py::test_survivor_rule_two_texas_am_survives_over_the_extract_by_source_order",
-      "tests/test_eligibility.py::test_the_survivor_does_not_depend_on_database_ids_or_insertion_order"
+      "tests/test_eligibility.py::test_the_survivor_does_not_depend_on_database_ids_or_insertion_order",
+      "tests/test_order_independence.py::test_the_reviewers_chain_gives_the_same_result_for_every_id_and_order"
     ]
   },
   {
@@ -4218,7 +4220,8 @@
     },
     "history": [],
     "notes": [
-      "Confirmation (2026-10-06): within the identity rule, definite relationships (exact duplicates, conflicts) are applied before the plan's possible-duplicate choice, which then applies to what remains."
+      "Confirmation (2026-10-06): within the identity rule, definite relationships (exact duplicates, conflicts) are applied before the plan's possible-duplicate choice, which then applies to what remains.",
+      "Confirmation round 2 (2026-10-06): the identity rule decides whole groups, never flag by flag: records linked by a chain of exact pairs are one measurement (one survivor); a chain touching a definite conflict follows the plan's conflict rule as one group; then the possible-duplicate choice per connected possible group. No decision depends on record ids, flag ids or insertion order."
     ],
     "tests": [
       "tests/test_eligibility.py::test_a_conflict_inside_a_mixed_group_stays_out_and_the_others_follow_the_plan",
@@ -4227,6 +4230,9 @@
       "tests/test_eligibility.py::test_each_rule_on_its_own",
       "tests/test_eligibility.py::test_excluded_and_identity_come_before_the_grain_size_count",
       "tests/test_eligibility.py::test_rule_order",
+      "tests/test_order_independence.py::test_a_chain_touching_a_conflict_enters_with_none_of_its_records",
+      "tests/test_order_independence.py::test_permuted_ids_and_insertion_order_give_the_same_frozen_result",
+      "tests/test_order_independence.py::test_the_reviewers_chain_gives_the_same_result_for_every_id_and_order",
       "tests/test_reference_sets.py::test_every_record_has_one_decision_with_its_rule"
     ]
   },
@@ -4704,7 +4710,8 @@
     ],
     "notes": [
       "Shown on the assumptions page like every entry.",
-      "Confirmation (2026-10-06): the freeze check sees every retained pairwise exact or conflict result (two-record flags inside mixed groups), not only group labels."
+      "Confirmation (2026-10-06): the freeze check sees every retained pairwise exact or conflict result (two-record flags inside mixed groups), not only group labels.",
+      "Confirmation round 2 (2026-10-06): the freeze check allows at most one record per chain of exact pairs, and per group linked by a definite conflict, forming the chains itself from Checks' flags."
     ],
     "tests": [
       "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
@@ -4725,6 +4732,7 @@
       "tests/test_freeze_invariants.py::test_the_reviewers_outcome_case_is_refused_at_the_freeze",
       "tests/test_mixed_groups.py::test_the_freeze_check_catches_the_exact_pair_with_eligibility_bypassed",
       "tests/test_mixed_groups.py::test_the_pipeline_never_admits_the_exact_duplicate_twice",
+      "tests/test_order_independence.py::test_the_freeze_check_allows_at_most_one_record_per_chain",
       "tests/test_plan.py::test_invalid_plans_are_refused",
       "tests/test_plan.py::test_the_plan_choices_that_remain"
     ]
diff --git a/hypocurate/pipeline/checkpoints.py b/hypocurate/pipeline/checkpoints.py
index e5f53fa..98c0f57 100644
--- a/hypocurate/pipeline/checkpoints.py
+++ b/hypocurate/pipeline/checkpoints.py
@@ -98,6 +98,21 @@ def _set_records(conn: Connection, run_id: int) -> dict[str, list[int]]:
     return {k: sorted(v) for k, v in out.items()}
 
 
+def freeze_fingerprint(plan_fingerprint: str, by_id: Mapping[int, Mapping], members: Mapping[str, list],
+                       sets: Mapping[str, Mapping[int, str]], counts: Mapping[str, Any]) -> str:
+    """The dataset freeze's fingerprint. Review finding 5: records are identified by their stable
+    identity (source-version fingerprint, origin key, item index) and their content hash, never by
+    database id, so the same data in any id or insertion order gives the same fingerprint."""
+    identity = {i: f"{r['version_fingerprint']}|{r['origin']}|{r['item_index']}" for i, r in by_id.items()}
+    content = {
+        "plan": plan_fingerprint,
+        "sets": {key: sorted([identity[i], by_id[i]["fingerprint"]] for i in ids) for key, ids in members.items()},
+        "rules": {key: dict(sorted((identity[i], rule) for i, rule in rules.items())) for key, rules in sets.items()},
+        "counts": counts,
+    }
+    return hashlib.sha256(canonical(content).encode("utf-8")).hexdigest()
+
+
 def freeze_dataset(engine: Engine, run_id: int) -> dict:
     """Freezes the analysis dataset (or records that none is frozen); returns the freeze record."""
     data = inclusion_input(engine, run_id, "checkpoint", "freeze_dataset")
@@ -109,16 +124,7 @@ def freeze_dataset(engine: Engine, run_id: int) -> dict:
     counts["per_source"] = {source: el.counts(plan, by_id, [i for i in members[el.PRIMARY]
                                                             if by_id[i]["source"] == source])
                             for source in sorted({by_id[i]["source"] for i in members[el.PRIMARY]})}
-    # Review finding 5: records are identified by their stable identity (source-version
-    # fingerprint, origin key, item index) and their content hash, never by database id.
-    identity = {i: f"{r['version_fingerprint']}|{r['origin']}|{r['item_index']}" for i, r in by_id.items()}
-    content = {
-        "plan": data["plan"]["fingerprint"],
-        "sets": {key: sorted([identity[i], by_id[i]["fingerprint"]] for i in ids) for key, ids in members.items()},
-        "rules": {key: dict(sorted((identity[i], rule) for i, rule in rules.items())) for key, rules in sets.items()},
-        "counts": counts,
-    }
-    fp = hashlib.sha256(canonical(content).encode("utf-8")).hexdigest()
+    fp = freeze_fingerprint(data["plan"]["fingerprint"], by_id, members, sets, counts)
     read_ids = sorted(by_id)
     read_flags = [(f["id"], f["kind"], f["category"], tuple(sorted(f["records"]))) for f in flags]
     identity_of = {r["id"]: record_identity(r["version_fingerprint"], r["origin"], r["item_index"]) for r in records}
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index f80fe3f..7b6ec6f 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -289,24 +289,7 @@ def decide(plan: Mapping[str, Any], records: Iterable[Mapping], flags: Iterable[
             rules[r["id"]] = "scope_not_confirmed"
         elif _excluded(r, st):
             rules[r["id"]] = "excluded_by_rule"
-    # 7, in a fixed order (review finding 4): unresolved identity, then conflicts, then counted once,
-    # so that a record in an ambiguous group and in a conflict gets the first that applies.
-    # Within one rule, definite relationships (exact duplicates, conflicts) come before possible
-    # duplicates, so that the plan's possible-duplicate choice applies only to what remains
-    # (confirmation, 2026-10-06).
-    order = {"identity_unresolved": 0, "conflict_unresolved": 1, "duplicate_counted_once": 2}
-    definite = ("exact_duplicate", "values_disagree")
-    for f in sorted(flags, key=lambda f: (order.get(flag_rule(f, st), 3), f["kind"] not in definite, f["id"])):
-        rule = flag_rule(f, st)
-        members = [rid for rid in f["records"] if rid in records and rid not in rules]
-        if rule in ("identity_unresolved", "conflict_unresolved"):
-            for rid in members:
-                rules[rid] = rule
-        elif rule == "duplicate_counted_once" and members:
-            survivor = min(members, key=lambda rid: survivor_key(records[rid], st))
-            for rid in members:
-                if rid != survivor:
-                    rules[rid] = "duplicate_counted_once"
+    _identity(records, flags, rules, st)
     sizes: dict[str, set] = defaultdict(set)  # 8
     for r in records.values():
         if r["id"] not in rules:
@@ -356,13 +339,23 @@ def primary_set_problems(members: set, records: Mapping[int, Mapping], flags: It
     each member's kind and source; `marked` is the run's test mark. Empty if nothing."""
     from hypocurate.sources.versions import SOURCES
     out = []
-    for f in flags:
-        inside = sorted(i for i in f["records"] if i in members)
-        if f["kind"] == "exact_duplicate" and len(inside) > 1:
+    flags = list(flags)
+    # At most one record per chain of exact pairs, and per group linked by a definite conflict
+    # (confirmation round 2): the chains are formed here from Checks' flags, independently of how
+    # Inclusion resolved them.
+    exact = [f["records"] for f in flags if f["kind"] == "exact_duplicate"]
+    conflicting = {i for f in flags if f["kind"] == "values_disagree" for i in f["records"]}
+    for group in components(exact):
+        inside = sorted(i for i in group if i in members)
+        if len(inside) > 1:
             out.append(f"an exact duplicate counted twice: records {inside}")
-        elif f["kind"] == "values_disagree" and len(inside) > 1:
+    for group in components(exact + [f["records"] for f in flags if f["kind"] == "values_disagree"]):
+        inside = sorted(i for i in group if i in members)
+        if set(group) & conflicting and len(inside) > 1:
             out.append(f"both records of a conflict: records {inside}")
-        elif f["kind"] == "invalid_value" and inside:
+    for f in flags:
+        inside = sorted(i for i in f["records"] if i in members)
+        if f["kind"] == "invalid_value" and inside:
             out.append(f"an invalid value: records {inside}")
         elif f["kind"] == "possible_duplicate" and f["category"] == "several candidates" and inside:
             out.append(f"a group of unresolved identity: records {inside}")
@@ -377,6 +370,77 @@ def primary_set_problems(members: set, records: Mapping[int, Mapping], flags: It
     return out
 
 
+def components(groups: Iterable[Iterable[int]]) -> list[list[int]]:
+    """Connected components of records linked by the given groups (each group links all its
+    members): a pure function of the links, whatever their order or the ids' values."""
+    parent: dict[int, int] = {}
+
+    def find(x: int) -> int:
+        while parent.setdefault(x, x) != x:
+            parent[x] = parent[parent[x]]
+            x = parent[x]
+        return x
+
+    for group in groups:
+        group = list(group)
+        for x in group:
+            find(x)
+        for a, b in zip(group, group[1:]):
+            ra, rb = find(a), find(b)
+            if ra != rb:
+                parent[max(ra, rb)] = min(ra, rb)
+    out: dict[int, list[int]] = defaultdict(list)
+    for x in parent:
+        out[find(x)].append(x)
+    return [sorted(c) for c in out.values()]
+
+
+def _identity(records: Mapping[int, Mapping], flags: list[Mapping], rules: dict[int, str], st: Settings) -> None:
+    """Rule 7 (confirmation round 2, 2026-10-06): no decision depends on record ids, flag ids or
+    the order of flags. In this order, each step a whole-group decision:
+    1. unresolved identity: every pending record of an ambiguous group;
+    2. definite relationships: records linked by a chain of exact-duplicate pairs are one
+       measurement, and a definite conflict links its records as well. A connected group that
+       touches a conflict follows the plan's conflict rule (neither: all its pending records are
+       `conflict_unresolved`; the survivor's value: one survivor); a group of exact duplicates
+       only keeps one survivor;
+    3. the plan's possible-duplicate choice on what remains: counted once, one survivor per
+       connected possible group, or both counted.
+    A survivor is chosen by the plan's survivor rule (`survivor_key`), whose last tie-break is the
+    source's stable identity (source, origin key, item index)."""
+    def pending(ids):
+        return [i for i in ids if i in records and i not in rules]
+
+    for f in flags:  # 1
+        if flag_rule(f, st) == "identity_unresolved":
+            for i in pending(f["records"]):
+                rules[i] = "identity_unresolved"
+    exact = [f["records"] for f in flags if f["kind"] == "exact_duplicate" and flag_rule(f, st) == "duplicate_counted_once"]
+    conflict = [f for f in flags if f["kind"] == "values_disagree"
+                and flag_rule(f, st) in ("conflict_unresolved", "duplicate_counted_once")]
+    in_conflict = {i: flag_rule(f, st) for f in conflict for i in f["records"]}
+    for group in components(exact + [f["records"] for f in conflict]):  # 2
+        live = pending(group)
+        touched = sorted({in_conflict[i] for i in group if i in in_conflict})
+        if "conflict_unresolved" in touched:
+            for i in live:
+                rules[i] = "conflict_unresolved"
+        elif live:
+            survivor = min(live, key=lambda i: survivor_key(records[i], st))
+            for i in live:
+                if i != survivor:
+                    rules[i] = "duplicate_counted_once"
+    possible = [f["records"] for f in flags if f["kind"] == "possible_duplicate"
+                and flag_rule(f, st) == "duplicate_counted_once"]
+    for group in components(possible):  # 3
+        live = pending(group)
+        if live:
+            survivor = min(live, key=lambda i: survivor_key(records[i], st))
+            for i in live:
+                if i != survivor:
+                    rules[i] = "duplicate_counted_once"
+
+
 def all_sets(plan: Mapping[str, Any], records: list[Mapping], flags: list[Mapping],
              set_flags: Mapping[str, list] | None = None) -> dict[str, dict[int, str]]:
     """The primary set and every sensitivity set the plan names, each with its own flags."""
diff --git a/tests/test_order_independence.py b/tests/test_order_independence.py
new file mode 100644
index 0000000..0940f89
--- /dev/null
+++ b/tests/test_order_independence.py
@@ -0,0 +1,178 @@
+"""Confirmation round 2 (ChatGPT, 2026-10-06): no decision may depend on record ids, flag ids or
+insertion order. Records linked by a chain of exact-duplicate pairs are one measurement: one
+survivor by the plan's survivor rule (the last tie-break is the source's stable identity). A chain
+touching a definite conflict enters with none of its records and none of the conflicting ones. The
+freeze check verifies at most one record per chain.
+
+The reviewer's A, B, C case (A-B exact by DOI, B-C exact by reference text, A-C possible) needs
+three sources with known, equal test conditions; through the sprint 1 adapters Texas A&M reports no
+test temperature, so it cannot arise there. It is tested on the same functions Checks, Inclusion
+and the freeze use. The permutation test then runs through the real pipeline on the controlled
+extract and on the real reference data."""
+from __future__ import annotations
+
+import copy
+import itertools
+import random
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+from hypocurate.pipeline import checkpoints, checks, eligibility as el, extract, inclusion
+from hypocurate.pipeline.flags import raise_flags, set_flags
+from hypocurate.pipeline.plan import reference_plan
+from hypocurate.sources import adapters
+from hypocurate.sources.record import AdapterResult
+from test_eligibility import PLAN, cond
+from test_flags import rec
+
+GROUPING = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
+            {"source": "controlled_duplicates", "unit": "paper"}]
+D = "10.1016/j.test.2026.042"
+
+
+def plan_counting_possible_both():
+    plan = copy.deepcopy(PLAN)
+    plan["rules"]["grouping"] = GROUPING
+    for e in plan["eligibility_rules"]:
+        if e["flag_kind"] == "possible_duplicate" and e.get("category") is None:
+            e["rule"] = "in_scope"
+    return plan
+
+
+# The reviewer's records, by name: (source, DOI, reference text, grain size); E is another grain size.
+ABC = {"A": ("mpea", D, "Reference X", 10.0), "B": ("tamu_fcc", D, "Reference Y", 10.0),
+       "C": ("controlled_duplicates", None, "Reference Y", 10.0), "E": ("mpea", D, "Reference X", 40.0)}
+ROW = {"A": 3, "B": 5, "C": 7, "E": 4}
+
+
+def _decide_abc(plan, ids: dict, order: list):
+    full = [rec(ids[n], s, gs=g, doi=doi, reference=ref) for n, (s, doi, ref, g) in ABC.items()]
+    full = [full[list(ABC).index(n)] for n in order]
+    flags = [{"id": 900 - k, "kind": f.kind, "category": f.category, "records": f.records}
+             for k, f in enumerate(raise_flags(plan, full))]
+    conds = {}
+    for n, (s, doi, ref, g) in ABC.items():
+        c = cond(ids[n], s, gs=g, doi=doi is not None, row=ROW[n])
+        c["origin"] = f"{s}.csv:row:{ROW[n]}"
+        conds[n] = c
+    records = [conds[n] for n in order]
+    per_set = {k: [{"kind": f.kind, "category": f.category, "records": f.records} for f in fs]
+               for k, fs in set_flags(plan, full).items()}
+    sets = el.all_sets(plan, records, flags, per_set)
+    name = {ids[n]: n for n in ABC}
+    by_id = {c["id"]: c for c in records}
+    members = {k: el.members(r) for k, r in sets.items()}
+    fp = checkpoints.freeze_fingerprint("p" * 64, by_id, members, sets, {})
+    return ({k: {name[i]: r for i, r in rules.items()} for k, rules in sets.items()}, fp,
+            el.primary_set_problems(set(members["primary"]), by_id, flags, True))
+
+
+def test_the_reviewers_chain_gives_the_same_result_for_every_id_and_order():
+    plan = plan_counting_possible_both()
+    results = set()
+    for perm in itertools.permutations([11, 12, 13]):
+        for order in (["A", "B", "C", "E"], ["C", "B", "A", "E"], ["E", "B", "C", "A"]):
+            ids = {"A": perm[0], "B": perm[1], "C": perm[2], "E": 14}
+            decided, fp, problems = _decide_abc(plan, ids, order)
+            assert problems == [], (ids, order, problems)
+            results.add((repr(sorted((k, sorted(v.items())) for k, v in decided.items())), fp))
+    assert len(results) == 1
+    decided = eval(next(iter(results))[0])
+    primary = dict(dict(decided)["primary"])
+    # One measurement: A, B and C are linked by exact pairs; one survivor by the survivor rule
+    # (A: a DOI, and MPEA first in the source order).
+    assert (primary["A"], primary["B"], primary["C"]) == ("in_scope", "duplicate_counted_once", "duplicate_counted_once")
+
+
+def test_a_chain_touching_a_conflict_enters_with_none_of_its_records():
+    """A-B exact, B-X conflict (X another record): none of A, B, X enters the primary set."""
+    records = [cond(1, "mpea"), cond(2, "controlled_duplicates"), cond(3, "tamu_fcc"), cond(4, "mpea", gs=40.0),
+               cond(5, "tamu_fcc", gs=40.0)]
+    flags = [{"id": 2, "kind": "exact_duplicate", "category": "identical values", "records": [1, 2]},
+             {"id": 1, "kind": "values_disagree", "category": "differ beyond tolerance", "records": [2, 3]}]
+    for ids_order in (flags, list(reversed(flags))):
+        got = el.decide(PLAN, records, ids_order)
+        assert (got[1], got[2], got[3]) == ("conflict_unresolved",) * 3
+    survivor = el.decide(PLAN, records, flags, "conflicts_survivor_value")
+    assert sum(survivor[i] == "in_scope" for i in (1, 2, 3)) == 1
+
+
+def test_the_freeze_check_allows_at_most_one_record_per_chain():
+    """A and C in the primary set, B out: no single exact pair is wholly inside, but A and C are
+    the same measurement through B."""
+    recs = {i: {"id": i, "source": "mpea", "kind": "measured"} for i in (1, 2, 3)}
+    flags = [{"id": 1, "kind": "exact_duplicate", "category": "identical values", "records": [1, 2]},
+             {"id": 2, "kind": "exact_duplicate", "category": "identical values", "records": [2, 3]}]
+    problems = el.primary_set_problems({1, 3}, recs, flags, True)
+    assert len(problems) == 1 and "exact duplicate" in problems[0]
+    assert el.primary_set_problems({1}, recs, flags, True) == []
+    conflict = [{"id": 1, "kind": "exact_duplicate", "category": "identical values", "records": [1, 2]},
+                {"id": 2, "kind": "values_disagree", "category": "differ beyond tolerance", "records": [2, 3]}]
+    assert any("conflict" in p for p in el.primary_set_problems({1, 3}, recs, conflict, True))
+
+
+# --- through the real pipeline ------------------------------------------------------------------
+
+def _permuted_run(db, vid, sources, seed, monkeypatch, marked):
+    """One run of version `vid`, with each source's records stored in a shuffled order, the
+    sources stored in a shuffled order, and unrelated records inserted first (shifting every id)."""
+    rnd = random.Random(seed)
+    real_read = adapters.read
+
+    def shuffled(version):
+        result = real_read(version)
+        records = list(result.records)
+        rnd.shuffle(records)
+        return AdapterResult(tuple(records), result.blank_rows)
+
+    with monkeypatch.context() as m:
+        m.setattr(extract.adapters, "read", shuffled)
+        for _ in range(seed):  # unrelated records: another run's, before this run's
+            other = pw.run_of_version(db, vid, sources=("tamu_fcc",))
+            checkpoints.lock_rules(db, other, reference_plan(vid))
+            extract.store_records(db, other)
+        rid = pw.run_of_version(db, vid, sources=sources, marked=marked)
+        checkpoints.lock_rules(db, rid, reference_plan(vid))
+        order = list(sources)
+        rnd.shuffle(order)
+        for key in order:
+            extract.store_source(db, rid, key)
+    checks.run_checks(db, rid)
+    inclusion.decide_run(db, rid)
+    checkpoints.freeze_dataset(db, rid)
+    with db.connect() as conn:
+        identity = {i: f"{s}|{k}|{x}" for i, s, k, x in conn.execute(text(
+            "SELECT r.id, s.key, r.source_item_key, r.item_index FROM record r JOIN source_version sv "
+            "ON sv.id = r.source_version_id JOIN source s ON s.id = sv.source_id WHERE r.extraction_run_id = :r"),
+            dict(r=rid))}
+        decisions = {identity[i]: rule for i, rule in conn.execute(text(
+            "SELECT record_id, rule FROM run_record WHERE run_id = :r"), dict(r=rid))}
+        sets = {}
+        for key, i in conn.execute(text("SELECT a.key, asr.record_id FROM analysis_set a JOIN analysis_set_record asr "
+                                        "ON asr.analysis_set_id = a.id WHERE a.run_id = :r"), dict(r=rid)):
+            sets.setdefault(key, set()).add(identity[i])
+        stage = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'inclusion'"),
+                             dict(r=rid)).scalar_one()
+        diffs = {k: {identity[int(i)]: rule for i, rule in v.items()} for k, v in stage["differences_from_primary"].items()}
+        fp = conn.execute(text("SELECT fingerprint FROM run_snapshot WHERE run_id = :r"), dict(r=rid)).scalar_one()
+    return decisions, sets, diffs, fp
+
+
+@pytest.mark.parametrize("sources, marked", [(("mpea", "controlled_duplicates"), True), (("mpea", "tamu_fcc"), False)],
+                         ids=["controlled_extract", "reference_data"])
+def test_permuted_ids_and_insertion_order_give_the_same_frozen_result(db, monkeypatch, sources, marked):
+    """The same data, stored with ids and insertion order permuted three ways: identical decisions
+    for every record, identical membership of the primary set and every sensitivity set, and the
+    same freeze fingerprint."""
+    pw.registered(db, ("mpea", "tamu_fcc", "controlled_duplicates"))
+    vid = pw.version_of(db, pw.dispatched_run(db, sources=("tamu_fcc",)))
+    results = [_permuted_run(db, vid, sources, seed, monkeypatch, marked) for seed in (0, 1, 2)]
+    first = results[0]
+    assert len(first[0]) > 1000 and first[1]["primary"]
+    for other in results[1:]:
+        assert other[0] == first[0]  # every record's decision
+        assert other[1] == first[1]  # the primary set and every sensitivity set
+        assert other[2] == first[2]  # each sensitivity set's rules
+        assert other[3] == first[3]  # the freeze fingerprint
````

## 4. Mutation checks of this round

**The second confirmation round (2026-10-06)**, four mutations:

| Removed or changed in the copy | Failing tests |
|---|---|
| Exact pairs resolved one by one, not as chains | 2 |
| A chain touching a conflict keeps a survivor | 1 |
| The freeze check reads exact pairs flag by flag | 1 |
| The survivor's last tie-break is the record id | 1 |


Harness output (`mutate.py` of the first packet with this round's list):

````
exact pairs resolved one by one, not as chains: 2 failed, 3 passed in 18.17s  (imports the copy: True)
a chain touching a conflict keeps a survivor: 1 failed, 4 passed in 18.21s  (imports the copy: True)
the freeze check reads exact pairs flag by flag: 1 failed, 4 passed in 18.14s  (imports the copy: True)
the survivor's last tie-break is the record id: 1 failed, 55 passed in 18.30s  (imports the copy: True)
````

## 5. Reference numbers recomputed after the fixes

The scripts of the first packet (section 13), run on the fixed code. Identical to the values before this round (`diff` of the full output empty), for every set; the freeze fingerprint is unchanged too. Why: the reference run raises no flag, so the identity rule never acts on it (section 1). Each "±" is one standard error (cluster-robust, by group), not a confidence interval.

````
fingerprint 93c44b227285b1c33157364d6f780e614dccfb7e6638dcf63b62803624320934
| Set | Records | Alloys | Groups | Resid. df | Result |
|---|---|---|---|---|---|
| MPEA alone (primary) | 76 | 13 | 19 | 62 | k = 424.1 ± 62.2, p = 1.1e-06 |
| Texas A&M alone (primary) | 21 | 9 | 1 | 11 | k = 1173.3 (no uncertainty, no p-value) |
| Pooled (primary) | 97 | 22 | 20 | 74 | k = 424.9 ± 64.4, p = 1.3e-06 |
| conflicts_survivor_value | 97 | 22 | 20 | 74 | k = 424.9 ± 64.4, p = 1.3e-06 |
| no_exclusions | 97 | 22 | 20 | 74 | k = 424.9 ± 64.4, p = 1.3e-06 |
| possible_duplicates_separate | 97 | 22 | 20 | 74 | k = 424.9 ± 64.4, p = 1.3e-06 |
| same_alloy_1_at_pct | 97 | 22 | 20 | 74 | k = 424.9 ± 64.4, p = 1.3e-06 |
| scope_not_confirmed_included | 103 | 23 | 22 | 79 | k = 432.4 ± 64.9, p = 6.7e-07 |
| six_batches_as_groups | 97 | 22 | 22 | 74 | k = 424.9 ± 64.2, p = 7.5e-07 |
| source_only_assignments | 76 | 13 | 19 | 62 | k = 424.1 ± 62.2, p = 1.1e-06 |
| tension_and_compression | 98 | 22 | 21 | 75 | k = 428.0 ± 63.5, p = 7.4e-07 |
| tension_and_compression, MPEA alone | 77 | 13 | 20 | 63 | k = 427.2 ± 61.4, p = 6.2e-07 |
````

## 6. Suite results

### Suite results

```
$ pytest -q                                   (Codespace, Python 3.14.2, `docker compose up -d db`)
901 passed in 278.36s                          (after the second confirmation's fix, 2026-10-06)
$ docker compose run --rm test                 (the test image, rebuilt)
901 passed in 286.13s
```

After the confirmation fixes: 896 passed locally and in the image; GitHub Actions on `8c9b062`: success (run 37374525357).

After the re-check fixes: 888 passed locally and in the image.

After the first review's fixes: 860 passed locally and in the image.

Before the review: 816 passed locally and in the image.

GitHub Actions, commit `b11e7c8` (the owner's decisions of 2026-10-06, last change to code, tests or data): success; "Run the suite in the test image": 816 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37354762927
Earlier: commit `8ccfd36` (first build), 815 passed, https://github.com/kelawady/hypocurate/actions/runs/37352154249

