# Build step 6 — third fix packet (the confirmation's two problems)

Date: 2026-10-06. Branch: `step-06-eligibility`. Covers only the two problems the confirmation review (`docs/reviews/step06_confirm_chatgpt.md`) found: commits after `0122d45` (the second fix packet) up to `82146e4`. Generated from the files and commits on disk by a script. The full step is in `docs/reviews/step06_review_packet.md`, the earlier rounds in `docs/reviews/step06_fix_packet.md` and `docs/reviews/step06_fix2_packet.md`, and the step summary (updated) in `docs/reviews/step06_summary.md`.

## How to use this packet

The owner asked for both problems to be fixed, each with tests that fail on the code before it: mixed groups keep every definite pairwise result, applied before the plan's possible-duplicate choice and seen by the freeze check (with the eligibility safeguards bypassed); and only unequal DOIs prove different papers. Section 1 also lists the other places where a group label discarded a pairwise fact. Please return a dated confirmation: for each problem, closed, partly closed or open, and any new finding.

## Contents

1. What was fixed (from the summary)
2. The confirmation review
3. The fixes, commit by commit (message and full diff)
4. Mutation checks of this round
5. Reference numbers recomputed after the fixes
6. Suite results

## Commits

```
d6f8fb8 Step 6: confirmation review saved verbatim
1482192 Step 6 confirmation fix: mixed groups keep definite pairs; DOI-only proof
82146e4 Step 6 summary: the confirmation review and its fixes
```

## 1. What was fixed

## Confirmation review (ChatGPT, 2026-10-06) and fixes

The text is in `docs/reviews/step06_confirm_chatgpt.md`; the commits and diffs in `docs/reviews/step06_fix3_packet.md`. Confirmed fixed: the concurrency item and duplicate rule entries. Partly fixed: the fixed rules and the freeze check (a mixed group lost a definite exact pair). New: unequal reference text was treated as proof of different papers, and the summary said otherwise. **Not safe to merge** until both are fixed; the owner asked for both, each with tests that fail on the code before it.

| Item | Fix | New tests (failed before the fix) |
|---|---|---|
| Mixed groups lose definite relationships (A, B exact with the same DOI; C, a third source, possible): a plan counting possible duplicates both admitted the exact duplicate twice | Checks keeps every definite pairwise result inside a group as its own two-record flag (`exact_duplicate` or `values_disagree`) whenever the group's label does not state it. An exact pair is kept only when neither record has another exact match in the other's source; otherwise the two matches are themselves the ambiguity, and counting each pair once would merge on a guess. A conflict pair is always kept (it only excludes). A group with any possible link is now labelled possible, so a conflict is no longer imposed on records whose only links are possible. Inclusion applies definite relationships first, then the plan's possible-duplicate choice to what remains. | `test_a_mixed_group_keeps_its_definite_pairs`; `test_a_mixed_group_never_admits_an_exact_duplicate_twice` (default plan, the "both counted" choice and `possible_duplicates_separate`); `test_the_pipeline_never_admits_the_exact_duplicate_twice` (the reviewer's case through the real pipeline: MPEA, the extract and a Texas A&M workbook) |
| The same loss for a conflict pair | The retained conflict pair stays out wherever conflicts are excluded; the third record follows the plan's possible-duplicate choice. | `test_a_mixed_group_keeps_its_definite_conflict_without_imposing_it_on_the_others`; `test_a_conflict_inside_a_mixed_group_stays_out_and_the_others_follow_the_plan`; `test_an_ambiguous_group_keeps_its_definite_exact_pair` |
| The freeze check trusted group labels | `primary_set_problems` checks exact and conflict relationships pair by pair from the retained flags, so it can catch this case on its own. | `test_the_freeze_check_catches_the_exact_pair_with_eligibility_bypassed` (the eligibility safeguard switched off in the test: an exact pair treated as "counted separately"; the freeze refuses) |
| Unequal reference text proved different papers | Only unequal DOIs prove different papers; equal DOIs or equal reference texts are the same paper; anything else is unknown. The summary's description (section above) now matches the code. | `test_unequal_reference_text_is_unknown_not_a_different_paper` (incl. a punctuation-only difference) |

**Other places where a group-level label discarded a pairwise fact** (looked for, as asked):
1. **A conflict-labelled group with an exact pair inside** (A and B exact, C conflicting with both): the exact pair was only implicit. Now kept as its own flag; it changes nothing in the primary set (all three are conflicts) and makes the freeze check see it.
2. **A conflict label imposed on a record with only possible links** (C within the tolerance of two conflicting records): C was excluded as a conflict. Fixed by the labelling order (a possible link makes the group possible; the conflict pair is kept as its own flag).
3. **Per-set flags** (`set_flags`) are built by the same function, so the fix applies to every sensitivity set.
4. **Not changed, and why:**
   - possible links inside an ambiguous group are not kept pairwise: the group never enters primary, and `possible_duplicates_separate` counts it separately by definition;
   - non-unique exact pairs inside an ambiguous group are not kept (see the fix above);
   - the unresolved-identity check uses the group label, which is the right level (it is a property of the group);
   - the numbers compared were already kept per pair (`compared_values`, for audit).
5. **The Critic (step 8)** will see the group flag and the retained pair flags. Whether it should be told which flags are group-level is for step 8.

**The ordering "definite first" is an equivalent mutation today:** with one survivor order, counting a pair once and then the group once picks the same record as counting the group once; and the "both counted" choice is applied last in any case. It is kept because it states the owner's rule; no test can distinguish it now (mutation checks below).

**Reference numbers and fingerprint after these fixes: none changed, and the freeze fingerprint is identical (`93c44b22…`).** The paper-identity change (item 3) could have changed them only through a new candidate pair between the two sources, since a Texas A&M record (no DOI) and an MPEA record would now be "unknown", not "different". It changed nothing because no Texas A&M alloy occurs in MPEA at all at 0.1 at.% (checked test-side: 0 records), so no pair between the sources reaches the paper test. On the reference run Checks still raises no flag.


## 2. The confirmation review

````markdown
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
````

## 3. The fixes, commit by commit

### `d6f8fb8 Step 6: confirmation review saved verbatim`

````diff
d6f8fb8d626f0f8509b0fd246287ce8619a190e7

Step 6: confirmation review saved verbatim

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
````

### `1482192 Step 6 confirmation fix: mixed groups keep definite pairs; DOI-only proof`

````diff
14821928ffe806946fd19bfa501ee7549d706433

Step 6 confirmation fix: mixed groups keep definite pairs; DOI-only proof

Finding 2 and the freeze check: a group labelled possible duplicate lost the
definite exact pair inside it, so a plan counting possible duplicates both
admitted the exact duplicate twice, and the freeze check (group labels only)
did not see it. Checks now keeps every definite pair (exact, conflict) whose
kind the group label does not state as its own two-record flag (an exact
pair only when neither record has another exact match in the other's
source); a group with a possible link is labelled possible, so a conflict is
no longer imposed on records with only possible links. Inclusion applies
definite relationships before the plan's possible-duplicate choice; the
freeze check sees the retained pairs.

New issue: unequal reference text no longer proves different papers; only
unequal DOIs do (equal DOIs or equal reference texts: same paper; anything
else: unknown).

The two changes share flags.py and its tests and are one commit. The 8 new
tests (pure, pipeline, freeze check with eligibility bypassed, conflict in a
mixed group, ambiguous group, paper identity) failed on the code before
this change; 5 tests whose premise changed are listed in the summary.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index e6ce1db..a090a94 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -399,14 +399,18 @@
     "tests": [
       "tests/test_controlled_duplicates_handling.py::test_the_flag_is_the_answer_files",
       "tests/test_eligibility.py::test_an_ambiguous_group_keeps_its_conflict_in_every_set",
-      "tests/test_flags.py::test_a_source_without_per_record_papers_is_compared_by_its_reference",
       "tests/test_flags.py::test_a_group_whose_records_are_not_all_linked_is_ambiguous",
       "tests/test_flags.py::test_a_group_with_one_conflicting_pair_is_a_conflict",
       "tests/test_flags.py::test_a_known_difference_in_paper_or_conditions_means_no_pair",
+      "tests/test_flags.py::test_a_mixed_group_keeps_its_definite_conflict_without_imposing_it_on_the_others",
+      "tests/test_flags.py::test_a_mixed_group_keeps_its_definite_pairs",
+      "tests/test_flags.py::test_a_source_without_dois_is_unknown_against_a_record_with_one",
+      "tests/test_flags.py::test_an_ambiguous_group_keeps_its_definite_exact_pair",
       "tests/test_flags.py::test_an_unknown_paper_or_condition_gives_a_possible_duplicate_only_if_the_values_match",
       "tests/test_flags.py::test_paper_identity_does_not_depend_on_the_grouping_setting",
       "tests/test_flags.py::test_rows_within_one_source_are_never_compared",
       "tests/test_flags.py::test_several_candidates_from_one_source_pair_nothing",
+      "tests/test_flags.py::test_unequal_reference_text_is_unknown_not_a_different_paper",
       "tests/test_flags.py::test_without_a_doi_the_normalized_paper_reference_identifies_the_paper"
     ],
     "history": [
@@ -429,7 +433,8 @@
       "Related: entry 'observation_unit' (what one source row represents) and entry 'values_disagree_tolerance' (the 2% tolerance).",
       "A record with a missing test condition is also 'scope not confirmed': Checks still raises the possible-duplicate flag, and Inclusion applies the scope rule before the duplicate rule (owner, 2026-10-05).",
       "Step 6 review, finding 4 (2026-10-06): an ambiguous group that contains a definite conflict keeps it as its own conflict flag; the conflicting records stay out wherever conflicts are excluded, including 'possible_duplicates_separate'.",
-      "A paper is identified from the records' own normalized paper references: both DOIs (derived key), else both reference texts (spaces collapsed, case-folded), else unknown. The plan's grouping is for clustering only and never changes paper identity (re-check finding 2a, 2026-10-06). Texas A&M records carry the dataset's reference and no DOI."
+      "A paper is identified from the records' own normalized paper references: both DOIs (derived key), else both reference texts (spaces collapsed, case-folded), else unknown. The plan's grouping is for clustering only and never changes paper identity (re-check finding 2a, 2026-10-06). Texas A&M records carry the dataset's reference and no DOI.",
+      "Confirmation (2026-10-06): only unequal DOIs prove different papers; unequal reference text alone is unknown. Inside a mixed group, every definite pair (exact, conflict) whose kind the group's label does not state is kept as its own flag; an exact pair only if neither record has another exact match in the other's source."
     ]
   },
   {
@@ -4212,12 +4217,16 @@
       "note": null
     },
     "history": [],
-    "notes": [],
+    "notes": [
+      "Confirmation (2026-10-06): within the identity rule, definite relationships (exact duplicates, conflicts) are applied before the plan's possible-duplicate choice, which then applies to what remains."
+    ],
     "tests": [
+      "tests/test_eligibility.py::test_a_conflict_inside_a_mixed_group_stays_out_and_the_others_follow_the_plan",
+      "tests/test_eligibility.py::test_a_mixed_group_never_admits_an_exact_duplicate_twice",
+      "tests/test_eligibility.py::test_duplicates_are_resolved_before_grain_sizes_are_counted",
       "tests/test_eligibility.py::test_each_rule_on_its_own",
-      "tests/test_eligibility.py::test_rule_order",
       "tests/test_eligibility.py::test_excluded_and_identity_come_before_the_grain_size_count",
-      "tests/test_eligibility.py::test_duplicates_are_resolved_before_grain_sizes_are_counted",
+      "tests/test_eligibility.py::test_rule_order",
       "tests/test_reference_sets.py::test_every_record_has_one_decision_with_its_rule"
     ]
   },
@@ -4694,7 +4703,8 @@
       }
     ],
     "notes": [
-      "Shown on the assumptions page like every entry."
+      "Shown on the assumptions page like every entry.",
+      "Confirmation (2026-10-06): the freeze check sees every retained pairwise exact or conflict result (two-record flags inside mixed groups), not only group labels."
     ],
     "tests": [
       "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
@@ -4713,6 +4723,8 @@
       "tests/test_freeze_invariants.py::test_each_invariant_is_checked_on_the_primary_set",
       "tests/test_freeze_invariants.py::test_the_reviewers_grouping_case_is_refused_at_the_freeze",
       "tests/test_freeze_invariants.py::test_the_reviewers_outcome_case_is_refused_at_the_freeze",
+      "tests/test_mixed_groups.py::test_the_freeze_check_catches_the_exact_pair_with_eligibility_bypassed",
+      "tests/test_mixed_groups.py::test_the_pipeline_never_admits_the_exact_duplicate_twice",
       "tests/test_plan.py::test_invalid_plans_are_refused",
       "tests/test_plan.py::test_the_plan_choices_that_remain"
     ]
@@ -4786,7 +4798,7 @@
     "key": "fixed_policies_in_code",
     "name": "Policies fixed in code for every plan",
     "state": "in_force",
-    "statement": "Plan settings (scope, exclusion rules, eligibility rules within the fixed choices, the plan's rules, sufficiency) are read from the locked plan only, never from the domain profile. These policies are fixed in code and the same for every plan: which statuses carry a value; what counts as physically invalid (tensile strength below yield strength, grain size of zero or less); which test conditions are compared (test type and temperature); how a paper is identified (from the records' own normalized paper references: both DOIs, else both reference texts, else unknown; never from the plan's grouping, which is for clustering only); that physical validity is checked on every record whatever the plan's outcome; the supported outcome ('supported_outcomes'); the room-temperature band's name; the order of the eligibility rules; the ambiguity rule; the fixed rules for the primary set ('primary_set_invariants'); the structure of the survivor rule and its stable tie-breaker; the change each sensitivity key applies; and the code roles' field lists. Changing one is a code change with this entry, needing the owner's approval.",
+    "statement": "Plan settings (scope, exclusion rules, eligibility rules within the fixed choices, the plan's rules, sufficiency) are read from the locked plan only, never from the domain profile. These policies are fixed in code and the same for every plan: which statuses carry a value; what counts as physically invalid (tensile strength below yield strength, grain size of zero or less); which test conditions are compared (test type and temperature); how a paper is identified (from the records' own normalized paper references: only unequal DOIs prove different papers; equal DOIs, or equal reference texts, are the same paper; anything else, unequal reference text included, is unknown; never from the plan's grouping, which is for clustering only); that physical validity is checked on every record whatever the plan's outcome; the supported outcome ('supported_outcomes'); the room-temperature band's name; the order of the eligibility rules; the ambiguity rule; the fixed rules for the primary set ('primary_set_invariants'); the structure of the survivor rule and its stable tie-breaker; the change each sensitivity key applies; and the code roles' field lists. Changing one is a code change with this entry, needing the owner's approval.",
     "value": {
       "text": "eleven fixed policies",
       "unit": null
@@ -4831,6 +4843,12 @@
         "from": "2026-10-06",
         "to": "2026-10-06",
         "note": "Before the re-check (finding 2a)."
+      },
+      {
+        "value": "Plan settings (scope, exclusion rules, eligibility rules within the fixed choices, the plan's rules, sufficiency) are read from the locked plan only, never from the domain profile. These policies are fixed in code and the same for every plan: which statuses carry a value; what counts as physically invalid (tensile strength below yield strength, grain size of zero or less); which test conditions are compared (test type and temperature); how a paper is identified (from the records' own normalized paper references: both DOIs, else both reference texts, else unknown; never from the plan's grouping, which is for clustering only); that physical validity is checked on every record whatever the plan's outcome; the supported outcome ('supported_outcomes'); the room-temperature band's name; the order of the eligibility rules; the ambiguity rule; the fixed rules for the primary set ('primary_set_invariants'); the structure of the survivor rule and its stable tie-breaker; the change each sensitivity key applies; and the code roles' field lists. Changing one is a code change with this entry, needing the owner's approval.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Before the confirmation review (paper identity)."
       }
     ],
     "notes": [],
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index 9fa3cbe..f80fe3f 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -291,8 +291,12 @@ def decide(plan: Mapping[str, Any], records: Iterable[Mapping], flags: Iterable[
             rules[r["id"]] = "excluded_by_rule"
     # 7, in a fixed order (review finding 4): unresolved identity, then conflicts, then counted once,
     # so that a record in an ambiguous group and in a conflict gets the first that applies.
+    # Within one rule, definite relationships (exact duplicates, conflicts) come before possible
+    # duplicates, so that the plan's possible-duplicate choice applies only to what remains
+    # (confirmation, 2026-10-06).
     order = {"identity_unresolved": 0, "conflict_unresolved": 1, "duplicate_counted_once": 2}
-    for f in sorted(flags, key=lambda f: (order.get(flag_rule(f, st), 3), f["id"])):
+    definite = ("exact_duplicate", "values_disagree")
+    for f in sorted(flags, key=lambda f: (order.get(flag_rule(f, st), 3), f["kind"] not in definite, f["id"])):
         rule = flag_rule(f, st)
         members = [rid for rid in f["records"] if rid in records and rid not in rules]
         if rule in ("identity_unresolved", "conflict_unresolved"):
@@ -345,7 +349,10 @@ def primary_set_problems(members: set, records: Mapping[int, Mapping], flags: It
                          marked: bool) -> list[str]:
     """The result check of the freeze (owner, 2026-10-06; register 'primary_set_invariants'): what
     in the primary set itself breaks an invariant, whatever the plan said. `flags` are the Checks
-    flags (identity and validity independent of the plan's grouping and outcome); `records` gives
+    flags, including every retained pairwise exact or conflict result (two-record flags inside
+    mixed groups), so exact and conflict pairs are checked pair by pair, never through a group's
+    label (confirmation, 2026-10-06); identity and validity are independent of the plan's grouping
+    and outcome. `records` gives
     each member's kind and source; `marked` is the run's test mark. Empty if nothing."""
     from hypocurate.sources.versions import SOURCES
     out = []
diff --git a/hypocurate/pipeline/flags.py b/hypocurate/pipeline/flags.py
index 5b442db..7fcb43a 100644
--- a/hypocurate/pipeline/flags.py
+++ b/hypocurate/pipeline/flags.py
@@ -24,10 +24,12 @@ Flags (owner, 2026-10-05):
     possible duplicate; beyond it → not a candidate (nothing says it is the same measurement).
   Candidate links form groups (connected components). A group with two or more records from
   one source, or one in which some pair is not linked, is ambiguous: `possible_duplicate`,
-  "several candidates" (nothing is paired on a guess); its definite conflicts, if any, get a
-  `values_disagree` flag of their own (review finding 4). Otherwise a group with any conflicting
-  pair is a conflict, else a possible duplicate if any link is possible, else an exact
-  duplicate. One flag per group, naming all its records (plus that conflict flag).
+  "several candidates" (nothing is paired on a guess). Otherwise a group with any possible link
+  is a possible duplicate, else a conflict if any pair conflicts, else an exact duplicate. One
+  flag per group, naming all its records. **Definite pairs are never lost to a group label**
+  (review finding 4; confirmation, 2026-10-06): every exact or conflicting pair whose kind the
+  group's label does not state gets its own two-record flag (an exact pair only when neither
+  record has another exact match in the other's source).
 - Relative difference: |a − b| / min(|a|, |b|) (register 'values_disagree_tolerance').
 - The numbers compared are stored with the flag for audit (`compared_values`) and never
   returned to the Critic (step 5).
@@ -90,14 +92,17 @@ def _reference(rec: Mapping) -> str | None:
 
 def same_paper(a: Mapping, b: Mapping) -> bool | None:
     """Whether two records cite the same paper, from their own normalized paper references only
-    (re-check finding 2a: never from the plan's grouping, which is for clustering): both DOIs
-    known, compare them; else both references known, compare them; else unknown (None)."""
+    (re-check finding 2a: never from the plan's grouping, which is for clustering). Only unequal
+    authoritative identifiers (DOIs, derived keys) prove different papers (confirmation, 2026-10-06):
+    - both DOIs known: equal is the same paper, unequal a different one;
+    - otherwise, equal reference texts (spaces collapsed, case-folded) are the same paper;
+    - anything else, unequal reference text included, is unknown (None)."""
     da, db = _doi(a), _doi(b)
     if da and db:
         return da == db
     ra, rb = _reference(a), _reference(b)
-    if ra and rb:
-        return ra == rb
+    if ra and rb and ra == rb:
+        return True
     return None
 
 
@@ -194,27 +199,44 @@ def duplicate_groups(records: list[Mapping], plan: Mapping[str, Any], m: Matchin
         components[find(x)].append(x)
     source = {r["id"]: r["source"] for r in records}
     flags = []
+    identical = lambda ps: all(n["relative_difference"] == 0 and n["grain_size"][0] == n["grain_size"][1]
+                               for _, n in ps)
     for ids in sorted(sorted(c) for c in components.values()):
         pairs = {(a, b): links[(a, b)] for a, b in combinations(ids, 2) if (a, b) in links}
         compared = {f"{a}-{b}": {"link": kind, **numbers} for (a, b), (kind, numbers) in pairs.items()}
         sources = [source[i] for i in ids]
         kinds = {kind for kind, _ in pairs.values()}
+        category = "identical values" if identical(pairs.values()) else "within tolerance"
         if len(set(sources)) < len(sources) or len(pairs) < len(ids) * (len(ids) - 1) // 2:
-            flags.append(Flag("possible_duplicate", "several candidates", ids, compared))
-            # Review finding 4: a definite conflict inside an ambiguous group is kept as its own
-            # flag, so that a set that counts the group separately still excludes it.
-            conflicting = sorted({i for (a, b), (kind, _) in pairs.items() if kind == "conflict" for i in (a, b)})
-            if conflicting:
-                flags.append(Flag("values_disagree", "differ beyond tolerance", conflicting,
-                                  {k: v for k, v in compared.items() if v["link"] == "conflict"}))
+            group = Flag("possible_duplicate", "several candidates", ids, compared)
+        elif "possible" in kinds:
+            group = Flag("possible_duplicate", category, ids, compared)
         elif "conflict" in kinds:
-            flags.append(Flag("values_disagree", "differ beyond tolerance", ids, compared))
+            group = Flag("values_disagree", "differ beyond tolerance", ids, compared)
         else:
-            identical = all(n["relative_difference"] == 0 and n["grain_size"][0] == n["grain_size"][1]
-                            for _, n in pairs.values())
-            category = "identical values" if identical else "within tolerance"
-            flags.append(Flag("possible_duplicate" if "possible" in kinds else "exact_duplicate", category, ids,
-                              compared))
+            group = Flag("exact_duplicate", category, ids, compared)
+        flags.append(group)
+        # Confirmation (2026-10-06): the group label must not discard a definite pairwise fact.
+        # Every exact or conflicting pair whose kind the group's own label does not already state
+        # is kept as its own two-record flag, so that the fixed rules apply to it before the plan's
+        # possible-duplicate choice, and the freeze check can see it.
+        # An exact pair is definite only if neither record has another exact match in the other's
+        # source (rows within one source are separate measurements: two exact matches there are
+        # themselves the ambiguity, and counting each pair once would merge on a guess). A
+        # conflicting pair is always kept: it only ever excludes.
+        own = {"exact": "exact_duplicate", "conflict": "values_disagree"}
+        exact_to = defaultdict(set)
+        for (a, b), (kind, _) in pairs.items():
+            if kind == "exact":
+                exact_to[(a, source[b])].add(b)
+                exact_to[(b, source[a])].add(a)
+        for (a, b), (kind, numbers) in sorted(pairs.items()):
+            if kind == "exact" and (len(exact_to[(a, source[b])]) > 1 or len(exact_to[(b, source[a])]) > 1):
+                continue
+            if kind in own and group.kind != own[kind]:
+                pair_category = ("differ beyond tolerance" if kind == "conflict"
+                                 else "identical values" if identical([(kind, numbers)]) else "within tolerance")
+                flags.append(Flag(own[kind], pair_category, [a, b], {f"{a}-{b}": {"link": kind, **numbers}}))
     return flags
 
 
diff --git a/tests/pipeline_world.py b/tests/pipeline_world.py
index ca11e75..6813d4f 100644
--- a/tests/pipeline_world.py
+++ b/tests/pipeline_world.py
@@ -67,6 +67,23 @@ def mpea_row(formula, gs, ys, doi="10.1016/j.test.2026.001", test="T", temperatu
             "PROPERTY: UTS (MPa)": str(ys * 2), "REFERENCE: doi": doi}
 
 
+def tamu_xlsx(rows: list[dict]) -> bytes:
+    """A Texas A&M-layout workbook: the frozen sheet name and header, then rows given as
+    {column: value} (element columns default to 0)."""
+    import io
+    import openpyxl
+    from hypocurate.sources.adapters.tamu_fcc import ELEMENT_COLUMNS, HEADER, SHEET
+    wb = openpyxl.Workbook()
+    ws = wb.active
+    ws.title = SHEET
+    ws.append(list(HEADER))
+    for r in rows:
+        ws.append([r.get(h, 0.0 if h in ELEMENT_COLUMNS else None) for h in HEADER])
+    out = io.BytesIO()
+    wb.save(out)
+    return out.getvalue()
+
+
 def _val(engine, sql, **params):
     with engine.begin() as conn:
         result = conn.execute(text(sql), params)
diff --git a/tests/test_eligibility.py b/tests/test_eligibility.py
index 692b77e..64282eb 100644
--- a/tests/test_eligibility.py
+++ b/tests/test_eligibility.py
@@ -223,6 +223,48 @@ def test_an_ambiguous_group_keeps_its_conflict_in_every_set():
     assert {i: survivor[i] for i in (1, 2, 3)} == {i: "identity_unresolved" for i in (1, 2, 3)}
 
 
+def _mixed(plan, full):
+    from hypocurate.pipeline.flags import raise_flags
+    return [{"id": n, "kind": f.kind, "category": f.category, "records": f.records}
+            for n, f in enumerate(raise_flags(plan, full), start=1)]
+
+
+def test_a_mixed_group_never_admits_an_exact_duplicate_twice():
+    """Confirmation finding 2, the reviewer's case: A and B exact, C possible (third source, no
+    paper identity), another grain size present. Definite relationships first (A-B counted once),
+    then the plan's possible-duplicate choice on what remains."""
+    from test_flags import rec
+    full = [rec(1, "mpea"), rec(2, "controlled_duplicates"), rec(3, "tamu_fcc", doi=None), rec(4, "mpea", gs=40.0)]
+    records = [cond(1, "mpea"), cond(2, "controlled_duplicates"), cond(3, "tamu_fcc", doi=False),
+               cond(4, "mpea", gs=40.0)]
+    flags = _mixed(PLAN, full)
+    both = copy.deepcopy(PLAN)  # the plan's choice: possible duplicates both counted
+    for e in both["eligibility_rules"]:
+        if e["flag_kind"] == "possible_duplicate" and e.get("category") is None:
+            e["rule"] = "in_scope"
+    got = decide(records, flags, both)
+    assert sorted(got[i] for i in (1, 2)) == ["duplicate_counted_once", "in_scope"]
+    assert got[3] == "in_scope"
+    default = decide(records, flags)  # possible counted once: one survivor of the three
+    assert sum(default[i] == "in_scope" for i in (1, 2, 3)) == 1
+    separate = decide(records, flags, key="possible_duplicates_separate")
+    assert sorted(separate[i] for i in (1, 2)) == ["duplicate_counted_once", "in_scope"] and separate[3] == "in_scope"
+
+
+def test_a_conflict_inside_a_mixed_group_stays_out_and_the_others_follow_the_plan():
+    from test_flags import rec
+    full = [rec(1, "mpea", ys=400.0), rec(2, "controlled_duplicates", ys=410.0), rec(3, "tamu_fcc", ys=405.0, doi=None),
+            rec(4, "mpea", gs=40.0)]
+    records = [cond(1, "mpea"), cond(2, "controlled_duplicates"), cond(3, "tamu_fcc", doi=False),
+               cond(4, "mpea", gs=40.0)]
+    flags = _mixed(PLAN, full)
+    for key in (el.PRIMARY, "possible_duplicates_separate"):
+        got = decide(records, flags, key=key)
+        assert (got[1], got[2], got[3]) == ("conflict_unresolved", "conflict_unresolved", "in_scope"), key
+    survivor = decide(records, flags, key="conflicts_survivor_value")
+    assert sum(survivor[i] == "in_scope" for i in (1, 2)) <= 1
+
+
 def test_identity_applies_only_among_records_that_passed_the_earlier_rules():
     """Extract rows 13–14 (owner, 2026-10-05): the extract record is 'scope not confirmed'
     (rule 5 before rule 7); its MPEA twin survives. With scope not confirmed included, the
diff --git a/tests/test_flags.py b/tests/test_flags.py
index c0c9d4d..1fe79b4 100644
--- a/tests/test_flags.py
+++ b/tests/test_flags.py
@@ -131,9 +131,11 @@ def test_a_group_with_one_conflicting_pair_is_a_conflict():
     plan = copy.deepcopy(PLAN)
     plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
                                  {"source": "controlled_duplicates", "unit": "paper"}]
-    # 1 and 2 agree; 3 reports the same measurement 2.25% higher: the whole group is a conflict.
+    # 1 and 2 agree; 3 reports the same measurement 2.25% higher: the whole group is a conflict,
+    # and the definite exact pair 1-2 is kept as its own flag (confirmation, 2026-10-06).
     got = kinds([rec(1, ys=400.0), rec(2, "controlled_duplicates", ys=400.0), rec(3, "tamu_fcc", ys=409.0)], plan)
-    assert got == [("values_disagree", "differ beyond tolerance", [1, 2, 3])]
+    assert got == [("values_disagree", "differ beyond tolerance", [1, 2, 3]),
+                   ("exact_duplicate", "identical values", [1, 2])]
     # A possible link (paper unknown on 2) and a conflicting pair (1, 3) in one group: a conflict.
     got = kinds([rec(1, ys=400.0), rec(2, "controlled_duplicates", ys=400.0, doi=None),
                  rec(3, "tamu_fcc", ys=440.0)], plan)
@@ -152,8 +154,10 @@ def test_paper_identity_does_not_depend_on_the_grouping_setting():
     assert kinds([rec(1), rec(2, "controlled_duplicates")], plan) == [("exact_duplicate", "identical values", [1, 2])]
     plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
                                  {"source": "controlled_duplicates", "unit": "paper"}]
-    assert kinds([rec(1, reference="Effect of annealing on CoCrFeMnNi"),
-                  rec(2, "tamu_fcc", doi=None, reference="Mulukutla et al. 2026")], plan) == []
+    # Whatever the grouping: unequal DOIs are different papers; a missing DOI is unknown.
+    assert kinds([rec(1), rec(2, "tamu_fcc", doi="10.5555/other")], plan) == []
+    assert kinds([rec(1), rec(2, "tamu_fcc", doi=None, reference="Mulukutla et al. 2026")], plan)[0][0] == \
+        "possible_duplicate"
 
 
 def test_without_a_doi_the_normalized_paper_reference_identifies_the_paper():
@@ -163,7 +167,8 @@ def test_without_a_doi_the_normalized_paper_reference_identifies_the_paper():
     same = rec(2, "controlled_duplicates", doi=None, reference="mulukutla, m. et al. (2026). dataset v1.1.0")
     other = rec(3, "controlled_duplicates", doi=None, reference="Another paper (2019)")
     assert kinds([a, same]) == [("exact_duplicate", "identical values", [1, 2])]
-    assert kinds([a, other]) == []
+    # Unequal reference text alone is unknown, not a different paper (confirmation, 2026-10-06).
+    assert kinds([a, other])[0][0] == "possible_duplicate"
     assert kinds([a, rec(4, "controlled_duplicates", doi=None)])[0][0] == "possible_duplicate"
 
 
@@ -175,13 +180,52 @@ def test_physical_validity_does_not_depend_on_the_outcome_setting():
     assert kinds([rec(1, uts=399.0)], plan) == [("invalid_value", "physically impossible", [1])]
 
 
-def test_a_source_without_per_record_papers_is_compared_by_its_reference():
+def test_a_mixed_group_keeps_its_definite_pairs():
+    """Confirmation, the reviewer's case: A and B cite the same DOI with identical values (exact);
+    C, from a third source, matches both but has no paper identity (possible). The group is a
+    possible duplicate, and the definite exact pair A-B is kept as its own flag."""
+    got = kinds([rec(1), rec(2, "controlled_duplicates"), rec(3, "tamu_fcc", doi=None)])
+    assert got == [("possible_duplicate", "identical values", [1, 2, 3]),
+                   ("exact_duplicate", "identical values", [1, 2])]
+
+
+def test_a_mixed_group_keeps_its_definite_conflict_without_imposing_it_on_the_others():
+    """A and B cite the same DOI and disagree (2.5%: a conflict); C has no paper identity and is
+    within the tolerance of both (possible). The conflict is kept for A-B only; C is a possible
+    duplicate, not part of a conflict."""
+    got = kinds([rec(1, ys=400.0), rec(2, "controlled_duplicates", ys=410.0), rec(3, "tamu_fcc", ys=405.0, doi=None)])
+    assert got == [("possible_duplicate", "within tolerance", [1, 2, 3]),
+                   ("values_disagree", "differ beyond tolerance", [1, 2])]
+
+
+def test_an_ambiguous_group_keeps_its_definite_exact_pair():
+    """A (MPEA) and B (extract) cite the same DOI with identical values; C (extract, no DOI) also
+    matches A: two candidates from one source, so ambiguous. The exact pair A-B is kept."""
+    got = kinds([rec(1), rec(2, "controlled_duplicates"), rec(3, "controlled_duplicates", doi=None, gs=10.1)])
+    assert got == [("possible_duplicate", "several candidates", [1, 2, 3]),
+                   ("exact_duplicate", "identical values", [1, 2])]
+
+
+def test_unequal_reference_text_is_unknown_not_a_different_paper():
+    """Confirmation, new issue: only unequal DOIs prove different papers. Unequal reference text
+    (one or both DOIs missing) is unknown, so matching values give a possible duplicate."""
+    a = rec(1, reference="Effect of annealing on CoCrFeMnNi")
+    b = rec(2, "tamu_fcc", doi=None, reference="Mulukutla et al. 2026")
+    assert kinds([a, b])[0][:2] == ("possible_duplicate", "identical values")
+    c = rec(3, "tamu_fcc", doi=None, reference="Effect of annealing on CoCrFeMnNi.")
+    d = rec(4, "controlled_duplicates", doi=None, reference="Effect of annealing on CoCrFeMnNi")
+    assert kinds([c, d])[0][0] == "possible_duplicate"  # punctuation differs: unknown, not different
+    assert kinds([rec(5), rec(6, "tamu_fcc", doi="10.5555/other")]) == []  # unequal DOIs: different papers
+
+
+def test_a_source_without_dois_is_unknown_against_a_record_with_one():
     """Texas A&M has no per-record paper: its records carry the dataset's reference and no DOI.
-    Against a record with a DOI and a title, the references differ, so they are never paired.
-    (Replaces 'a dataset source is its own paper', which came from the grouping setting until the
-    re-check, finding 2a.)"""
+    Against a record with a DOI and another reference, the paper is unknown, so matching values
+    give a possible duplicate, never an exact one. (Replaces the round-2 test that treated the
+    unequal reference text as a different paper; confirmation, 2026-10-06.)"""
     tamu = rec(2, "tamu_fcc", doi=None, reference="Mulukutla, M. et al. (2026). Revisiting Hall-Petch")
-    assert kinds([rec(1, reference="Effect of annealing on CoCrFeMnNi"), tamu]) == []
+    got = kinds([rec(1, reference="Effect of annealing on CoCrFeMnNi"), tamu])
+    assert got == [("possible_duplicate", "identical values", [1, 2])]
 
 
 def _world(seed):
diff --git a/tests/test_mixed_groups.py b/tests/test_mixed_groups.py
new file mode 100644
index 0000000..8d5d181
--- /dev/null
+++ b/tests/test_mixed_groups.py
@@ -0,0 +1,65 @@
+"""Confirmation (ChatGPT, 2026-10-06), finding 2 and the freeze check: a mixed group keeps its
+definite pairwise relationships, through the real pipeline and at the freeze.
+
+The reviewer's case: A (MPEA) and B (the extract) cite the same DOI with identical conditions and
+values; C (Texas A&M, a third source) matches both but has no paper identity. Another grain size
+is present. The plan chooses to count possible duplicates both (a permitted choice)."""
+from __future__ import annotations
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+from hypocurate.pipeline import checkpoints, checks, eligibility, extract, inclusion
+from hypocurate.pipeline.plan import reference_plan
+from hypocurate.pipeline.writes import Refused
+
+DOI = "10.1016/j.test.2026.001"
+
+
+@pytest.fixture
+def run(db):
+    pw.registered_files(db, {
+        "mpea": pw.mpea_csv([pw.mpea_row("Co50Ni50", 10.0, 300.0, doi=DOI), pw.mpea_row("Co50Ni50", 40.0, 250.0, doi=DOI)]),
+        "controlled_duplicates": pw.mpea_csv([pw.mpea_row("Co50Ni50", 10.0, 300.0, doi=DOI)]),
+        "tamu_fcc": pw.tamu_xlsx([{"Iteration": "CBA", "Alloy Name": "Co50Ni50", "Co": 50.0, "Ni": 50.0,
+                                   "YS (MPa)": 300.0, "Grain Size(µm)": 10.0}])})
+    content = reference_plan(0)
+    for e in content["eligibility_rules"]:
+        if e["flag_kind"] == "possible_duplicate" and e.get("category") is None:
+            e["rule"] = "in_scope"  # the plan's choice: possible duplicates both counted
+    rid = pw.dispatched_run(db, sources=("mpea", "controlled_duplicates", "tamu_fcc"), marked=True)
+    content["hypothesis_version"] = pw.version_of(db, rid)
+    checkpoints.lock_rules(db, rid, content)
+    extract.store_records(db, rid)
+    checks.run_checks(db, rid)
+    return rid
+
+
+def _origins(db, rid, rule=None):
+    with db.connect() as conn:
+        return {f"{s}:{k}": r for s, k, r in conn.execute(text(
+            "SELECT s.key, rec.source_item_key, rr.rule FROM run_record rr JOIN record rec ON rec.id = rr.record_id "
+            "JOIN source_version sv ON sv.id = rec.source_version_id JOIN source s ON s.id = sv.source_id "
+            "WHERE rr.run_id = :r"), dict(r=rid))}
+
+
+def test_the_pipeline_never_admits_the_exact_duplicate_twice(db, run):
+    inclusion.decide_run(db, run)
+    rules = _origins(db, run)
+    a, b = rules["mpea:MPEA_dataset.csv:row:0"], rules["controlled_duplicates:extract.csv:row:0"]
+    assert sorted([a, b]) == ["duplicate_counted_once", "in_scope"]
+    assert rules["tamu_fcc:Grain_Size_Summary_v3.xlsx:row:0"] == "in_scope"
+    assert checkpoints.freeze_dataset(db, run)["frozen"] is True
+
+
+def test_the_freeze_check_catches_the_exact_pair_with_eligibility_bypassed(db, run, monkeypatch):
+    """The eligibility safeguards bypassed (an exact pair treated as 'counted separately'): the
+    freeze check, using Checks' retained pairwise result, still refuses."""
+    original = eligibility.flag_rule
+    monkeypatch.setattr(eligibility, "flag_rule",
+                        lambda f, st: "in_scope" if f["kind"] == "exact_duplicate" else original(f, st))
+    inclusion.decide_run(db, run)
+    with pytest.raises(Refused) as refused:
+        checkpoints.freeze_dataset(db, run)
+    assert refused.value.code == "invariant_broken" and "exact duplicate" in refused.value.message
````

## 4. Mutation checks of this round

**The confirmation round (2026-10-06)**, five mutations:

| Removed or changed in the copy (confirmation fixes) | Failing tests |
|---|---|
| Definite pairs not kept in mixed groups | 9 |
| Non-unique exact pairs kept (merging on a guess) | 1 |
| Unequal reference text proves a different paper | 3 |
| A conflict label imposed on the whole group | 2 |
| Definite relationships not applied before the possible choice | 0: an equivalent mutation (see the confirmation section) |


Harness output (`mutate.py` of the first packet with this round's list):

````
definite pairs not kept in mixed groups: 9 failed, 69 passed in 2.26s  (imports the copy: True)
definite relationships not applied before the possible choice: 53 passed in 2.23s  (imports the copy: True)
non-unique exact pairs kept (merging on a guess): 1 failed, 24 passed in 0.37s  (imports the copy: True)
unequal reference text proves a different paper: 3 failed, 22 passed in 0.39s  (imports the copy: True)
a conflict label imposed on the whole group: 2 failed, 74 passed in 0.63s  (imports the copy: True)
````

## 5. Reference numbers recomputed after the fixes

The scripts of the first packet (section 13), run on the fixed code. Identical to the values before this round (`diff` of the full output empty), for every set; the freeze fingerprint is unchanged too. Why the paper-identity change could not change them: section 1. Each "±" is one standard error (cluster-robust, by group), not a confidence interval.

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
896 passed in 218.80s                          (after the confirmation fixes, 2026-10-06)
$ docker compose run --rm test                 (the test image, rebuilt)
896 passed in 224.33s
```

After the re-check fixes: 888 passed locally and in the image.

After the first review's fixes: 860 passed locally and in the image.

Before the review: 816 passed locally and in the image.

GitHub Actions, commit `b11e7c8` (the owner's decisions of 2026-10-06, last change to code, tests or data): success; "Run the suite in the test image": 816 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37354762927
Earlier: commit `8ccfd36` (first build), 815 passed, https://github.com/kelawady/hypocurate/actions/runs/37352154249

