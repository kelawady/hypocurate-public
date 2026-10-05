# Build step 6 — second fix packet (the re-check's three items)

Date: 2026-10-06. Branch: `step-06-eligibility`. Covers only the items the re-check (`docs/reviews/step06_recheck_chatgpt.md`) left open, and the owner's addition: commits after `21d828c` (the state the re-check reviewed, plus its summary) up to `b2470bc`. Generated from the files and commits on disk by a script. The full step is in `docs/reviews/step06_review_packet.md`, the first round's fixes in `docs/reviews/step06_fix_packet.md`, and the step summary (updated) in `docs/reviews/step06_summary.md`.

## How to use this packet

The owner asked for the three remaining items to be fixed, each with a test that fails on the code before it, and added a check on the result: at the freeze, the primary set itself is verified against every item of `primary_set_invariants`, with plans deliberately built to slip past settings validation (including the reviewer's two cases). Please return a dated re-check: for each item, closed, partly closed or open, and any new finding.

## Contents

1. What was fixed (from the summary)
2. The re-check
3. The fixes, commit by commit (message and full diff)
4. Mutation checks of this round
5. Reference numbers recomputed after the fixes
6. Suite results

## Commits

```
b28e92d Step 6: re-check saved verbatim; a shadowed test runs again
3d4f37d Step 6 re-check fix: the rule guard resolves entries as the lookup does
dc85887 Step 6 re-check fix: paper identity apart from grouping; one outcome
9d964e2 Step 6 re-check fix: Inclusion and the freeze verify Checks as they read
8ec5c63 Step 6 re-check fix: the freeze checks the primary set against the invariants
b2470bc Step 6 re-check fix: test that Inclusion's read itself verifies Checks
```

## 1. What was fixed

## Re-check (ChatGPT, 2026-10-06) and fixes

The text is in `docs/reviews/step06_recheck_chatgpt.md`; the commits and diffs in `docs/reviews/step06_fix2_packet.md`. Closed: findings 2 (subject to 1), 3, 4, 5 and 6. Left: three items, fixed as the owner asked (each with a test that failed on the code before it), plus the owner's addition:

| Item | Fix | New tests (failed before the fix) |
|---|---|---|
| 1. Inclusion or the freeze could read before Checks completed (empty per-set flags) and still pass the coverage check | The `set_flags` reader, in the same transaction under the run's lock that reads Inclusion's inputs, verifies that a completed Checks result exists and covers exactly the records and flags read; otherwise the read is refused (`checks_not_done`, `checks_not_current`) and Inclusion and the freeze log the refusal. A sensitivity set whose own flags are required (its same-alloy step or value statuses differ) and missing from the result is refused (`set_flags_missing`), never read as "no flags". The binding helpers moved to `pipeline/binding.py`, shared by the access layer and the write paths. | `test_the_reviewers_interleaving_is_refused` (Checks committed between Inclusion's read and write; the reviewer's controlled interleaving); `test_a_missing_required_per_set_flag_result_is_a_refusal`; `test_the_read_itself_refuses_a_checks_result_that_does_not_cover_the_records` (added after the mutation checks: the read, not only the later write, refuses) |
| 2a. Grouping changed paper identity (MPEA grouped by dataset stopped matching) | Paper identity for matching comes only from the records' own normalized paper references: both DOIs (derived key), else both reference texts (spaces collapsed, case-folded), else unknown. Grouping is used only for clustering. | `test_paper_identity_does_not_depend_on_the_grouping_setting` (the reviewer's case); `test_without_a_doi_the_normalized_paper_reference_identifies_the_paper` |
| 2b. Another outcome disabled the tensile-below-yield check | Physical validity is checked on every record whatever the plan's outcome; Checks compares yield strength (`flags.COMPARED_OUTCOME`); validation refuses any outcome but yield strength (`eligibility.SUPPORTED_OUTCOMES`; new register entry `supported_outcomes`). | `test_physical_validity_does_not_depend_on_the_outcome_setting` (the reviewer's case); two new cases in `test_invalid_plans_are_refused` |
| 3. The application-time guard kept the last of duplicate entries while the lookup uses the first | One shared lookup (`ordered_rules`, `lookup`) serves both the rules and the guard; duplicate entries are refused; every flag kind and category is checked as the lookup resolves it. | `test_the_application_time_guard_refuses_duplicate_or_shadowing_entries` (4 cases; 3 failed, the narrower-category case was already refused) |
| **Owner's addition:** a check on the result, not only on the settings | At the freeze, `eligibility.primary_set_problems` checks the primary set itself against every item of `primary_set_invariants`, using the Checks flags (independent of the plan's grouping and outcome) and each record's kind and source; a failure refuses the freeze (`invariant_broken`) and is logged. Its constructed-source test reads the source definition itself, so that switching off the earlier guard does not switch it off. Register: the invariants are stated as enforced on the frozen set itself. | `tests/test_freeze_invariants.py` (15): each of the six invariants on the checker; what it allows; end to end, plans built to slip past settings validation (the guards switched off in the test): an exact duplicate twice, both records of a conflict, an invalid value, an unresolved-identity group, a constructed record in an unmarked run, and **the reviewer's two cases** (grouping by dataset; tensile strength as the outcome), each refused at the freeze and logged; a valid plan freezes |

**Also in this round:** two parallel sessions had each added `test_no_record_is_stored_after_checks`; the second definition hid the first. The first is renamed `test_no_record_is_stored_even_when_checks_ran_early`, so both run; a scan of every test file finds no other duplicate name.

**Reference numbers after these fixes:** recomputed; **none changed**, and the freeze fingerprint is unchanged too (`93c44b22…`). As the re-check expected: the reference sources have no shared measurement and no invalid value.

**What these fixes do not do:** the result check covers the six invariants of `primary_set_invariants`; it does not re-derive every eligibility rule (that is the freeze's existing comparison of the stored decisions with what the locked rules produce). Paper identity from reference text is exact after normalizing spaces and case; two spellings of one reference that differ otherwise are "unknown", which can give a possible duplicate, never a pair.


## 2. The re-check

````markdown
# Step 6 — second-model re-check (ChatGPT, 2026-10-06)

Re-check of `docs/reviews/step06_fix_packet.md` (branch `step-06-eligibility`). Saved verbatim as the owner gave it. The owner asked for the three remaining items to be fixed, each with a test that fails on the code before it (see `docs/reviews/step06_summary.md`).

---

Not ready to merge yet. The original matching and migration fixes are substantially addressed, but a concurrency gap remains, and other valid plan settings can bypass the new fixed rules.
Finding	Status	Assessment
1. Checks coverage	Partly closed	Sequential skipping, unfinished extraction and records added after Checks are now rejected. A race involving per-set flags remains below.
2. Sensitivity matching	Closed, subject to #1	Checks now recomputes matching flags under each set’s effective settings. The coarser-alloy example correctly retains two records rather than four. Inclusion receives categories and IDs, not compared outcomes. These are consequences of the single changed setting.
3. Source coverage and survivor order	Closed	The lock requires every chosen source in both settings; the final tie-breaker uses stable origin information. I found no remaining database-ID dependence in survivor selection.
4. Conflicts inside ambiguous groups	Closed	The three-source example now excludes A and C in possible_duplicates_separate, while permitting B if otherwise eligible. Primary still excludes the unresolved group.
5. Freeze fingerprint	Closed	Record IDs have been replaced with stable identities. The new same-database test addresses the previous test weakness. Different hypothesis-version IDs intentionally produce different plan fingerprints; that limitation is now stated.
6. Extraction constraint	Closed	Present string-valued fields and explicit false-on-NULL handling close the loophole. The original trigger checks remain intact.


The remaining issues, in seriousness order:
1. Concurrent operations can freeze a sensitivity set computed before its Checks flags existed.
set_flags() returns {} when Checks has not completed. Later, require_checks_cover() compares record identities and primary flags only.
An allowed interleaving is:
1. Freeze and Inclusion each read before Checks completes, obtaining empty per-set flags.
2. Checks commits: no primary flags, but duplicate flags for the coarser-alloy sensitivity.
3. Inclusion writes its stale decisions; the coverage check passes.
4. Freeze compares against those same stale decisions; it also passes.
Using the patched functions, the stale input retained four records, the completed Checks input retained two, and the coverage check accepted the stale view after Checks completed.
Fix: require completed Checks within the same transaction that reads Inclusion/freeze inputs. Missing required per-set flags should fail closed, rather than silently reuse primary flags. Add a controlled interleaving test.
2. The fixed rules can still be bypassed through other valid plan settings.
I reproduced two cases without changing the required eligibility-rule entries:
- Grouping changes duplicate identity. Set MPEA’s grouping to dataset while the other source remains paper. paper() then substitutes dataset:mpea for MPEA’s actual DOI. Identical cross-source records citing the same paper stop matching, and both enter primary. Statistical clustering should not erase known paper identity. Separate these concepts or reject inappropriate grouping overrides.
- Changing the outcome disables a physical-validity check. With ultimate_tensile_strength as the outcome, the UTS-below-YS check does not run. Records with UTS 399 and YS 400 receive no invalid flag and enter primary. That physical check must run independently of the selected outcome—or unsupported outcome choices must be rejected.
The new rule-map restrictions therefore do not yet establish the owner’s invariant.
3. Application-time validation misses duplicate rule entries.
fixed_rule_problems() converts entries into a dictionary, retaining the last duplicate. Actual rule lookup uses the first matching entry.
Prepending exact_duplicate → in_scope before the required correct entry passes the application-time check and admits both copies. Plan validation does reject this, so the normal lock path is protected; the claimed second enforcement point is not. Reject duplicate entries there too.
The unchanged reference numbers are expected: the reference sources have no shared measurements or invalid-value flags, the relevant coarse-alloy grouping is unchanged, and the default plan remains the same. These fixes principally affect constructed edge cases, sequencing and fingerprints.
I found no separate live-database safety blocker in migrations 0002/0003. Nevertheless, hold the step-6 merge until the concurrency and fixed-rule gaps are closed.
I reconstructed the patched modules and ran targeted reproductions; I did not independently rerun the reported 860-test PostgreSQL suite.
````

## 3. The fixes, commit by commit

### `b28e92d Step 6: re-check saved verbatim; a shadowed test runs again`

````diff
b28e92dfaf3637c3537a0efe523446dec052ce7b

Step 6: re-check saved verbatim; a shadowed test runs again

Two parallel sessions each added test_no_record_is_stored_after_checks; the
second definition hid the first. The first is renamed
test_no_record_is_stored_even_when_checks_ran_early so both run. A scan of
every test file finds no other duplicate name.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/tests/test_checkpoints.py b/tests/test_checkpoints.py
index 70ee894..52e3a04 100644
--- a/tests/test_checkpoints.py
+++ b/tests/test_checkpoints.py
@@ -244,7 +244,7 @@ def test_checks_wait_until_every_chosen_source_is_stored(engine):
     assert (sets["primary"][mpea], sets["primary"][copy]) == ("conflict_unresolved", "conflict_unresolved")
 
 
-def test_no_record_is_stored_after_checks(engine, monkeypatch):
+def test_no_record_is_stored_even_when_checks_ran_early(engine, monkeypatch):
     """A second guard: storage refuses once Checks have run. Through the normal order this cannot
     arise (Checks refuse while a source is pending, and a decided source is final), so the test
     lets Checks run with the extract pending, then stores it."""
````

### `3d4f37d Step 6 re-check fix: the rule guard resolves entries as the lookup does`

````diff
3d4f37d4a7bbd86bcc5d01725b3b6c36380490fb

Step 6 re-check fix: the rule guard resolves entries as the lookup does

Re-check finding 3: fixed_rule_problems kept the last of duplicate entries
while the rule lookup uses the first, so a prepended exact_duplicate ->
in_scope passed the guard applied with the rules. One shared lookup now
serves both; duplicate entries are refused, and every flag kind and
category is checked as the lookup resolves it. 3 of the 4 new cases failed
on the code before this change (the narrower-category case was already
refused).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index 3216972..68de0e3 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -68,18 +68,40 @@ FLAG_RULE_CHOICES = {
 }
 
 
+def ordered_rules(eligibility_rules) -> tuple:
+    """A plan's eligibility rules in lookup order: entries naming a category first, then the
+    others, each group in the plan's order. `lookup` takes the first that matches."""
+    entries = [(e.get("flag_kind"), e.get("category"), e.get("rule")) for e in eligibility_rules]
+    return tuple(sorted(entries, key=lambda t: t[1] is None))
+
+
+def lookup(rules: tuple, kind: str, category: str | None) -> str | None:
+    """The rule a flag of this kind and category gets: the first matching entry."""
+    for k, c, rule in rules:
+        if k == kind and (c is None or c == category):
+            return rule
+    return None
+
+
 def fixed_rule_problems(eligibility_rules) -> list[str]:
-    """What breaks the fixed rules in a plan's eligibility rules (empty if nothing)."""
-    got = {(e.get("flag_kind"), e.get("category")): e.get("rule") for e in eligibility_rules}
-    problems = [f"{kind}{'/' + cat if cat else ''}: missing" for kind, cat in FLAG_RULE_CHOICES
-                if (kind, cat) not in got]
-    for key, rule in got.items():
-        allowed = FLAG_RULE_CHOICES.get(key)
-        if allowed is None:
-            problems.append(f"{key[0]}{'/' + key[1] if key[1] else ''}: not a flag the plan sets a rule for")
-        elif rule not in allowed:
-            problems.append(f"{key[0]}{'/' + key[1] if key[1] else ''}: {rule} (allowed: {', '.join(allowed)})")
-    return problems
+    """What breaks the fixed rules in a plan's eligibility rules (empty if nothing). Duplicate
+    entries are refused, and each flag kind and category is resolved exactly as `lookup` resolves
+    it when the rules are applied (re-check finding 3)."""
+    from hypocurate.access.vocabulary import FLAG_CATEGORIES
+    keys = [(e.get("flag_kind"), e.get("category")) for e in eligibility_rules]
+    name = lambda k: f"{k[0]}{'/' + k[1] if k[1] else ''}"
+    problems = [f"{name(k)}: more than one entry" for k in sorted(set(keys), key=str) if keys.count(k) > 1]
+    problems += [f"{name(k)}: missing" for k in FLAG_RULE_CHOICES if k not in keys]
+    problems += [f"{name(k)}: not a flag the plan sets a rule for" for k in sorted(set(keys), key=str)
+                 if k not in FLAG_RULE_CHOICES]
+    rules = ordered_rules(eligibility_rules)
+    for kind in sorted({k for k, _ in FLAG_RULE_CHOICES}):
+        for category in sorted(FLAG_CATEGORIES):
+            allowed = FLAG_RULE_CHOICES.get((kind, category), FLAG_RULE_CHOICES.get((kind, None), ()))
+            got = lookup(rules, kind, category)
+            if got not in allowed:
+                problems.append(f"{kind} ({category}): resolves to {got} (allowed: {', '.join(allowed)})")
+    return sorted(set(problems))
 
 # The one change of each sensitivity set (owner, 2026-10-05).
 SENSITIVITY_CHANGES = {
@@ -122,8 +144,7 @@ def settings(plan: Mapping[str, Any], key: str = PRIMARY) -> Settings:
     problems = fixed_rule_problems(plan["eligibility_rules"])
     if problems:
         raise ValueError("the plan breaks a fixed rule for the primary set: " + "; ".join(problems))
-    flag_rules = tuple(sorted(((e["flag_kind"], e.get("category"), e["rule"]) for e in plan["eligibility_rules"]),
-                              key=lambda t: t[1] is None))
+    flag_rules = ordered_rules(plan["eligibility_rules"])
     base = Settings(
         outcome=v["outcome"]["field"], predictor=v["predictor"]["field"], test_types=frozenset(s["test_type"]),
         bands=frozenset(s["temperature_band"]), phase_classes=frozenset(s["phase_class"]),
@@ -224,10 +245,7 @@ def alloy(rec: Mapping, decimals: int) -> str | None:
 
 
 def flag_rule(flag: Mapping, st: Settings) -> str | None:
-    for kind, category, rule in st.flag_rules:
-        if kind == flag["kind"] and (category is None or category == flag["category"]):
-            return rule
-    return None
+    return lookup(st.flag_rules, flag["kind"], flag["category"])
 
 
 def survivor_key(rec: Mapping, st: Settings) -> tuple:
diff --git a/tests/test_eligibility.py b/tests/test_eligibility.py
index 844c22e..692b77e 100644
--- a/tests/test_eligibility.py
+++ b/tests/test_eligibility.py
@@ -296,6 +296,25 @@ def test_no_plan_can_put_these_records_in_the_primary_set(kind, category, rule):
         el.settings(plan)
 
 
+@pytest.mark.parametrize("extra", [
+    {"flag_kind": "exact_duplicate", "rule": "in_scope"},  # the re-check's case: prepended, first match wins
+    {"flag_kind": "values_disagree", "rule": "in_scope"},
+    {"flag_kind": "possible_duplicate", "category": "several candidates", "rule": "in_scope"},
+    {"flag_kind": "exact_duplicate", "category": "identical values", "rule": "in_scope"},  # a narrower entry
+])
+def test_the_application_time_guard_refuses_duplicate_or_shadowing_entries(extra):
+    """Re-check finding 3: the guard applied with the rules resolves entries exactly as the rule
+    lookup does (first match, category entries first), and refuses duplicate entries, so a plan
+    that bypassed validation cannot admit both copies of an exact duplicate."""
+    plan = copy.deepcopy(PLAN)
+    plan["eligibility_rules"].insert(0, extra)
+    with pytest.raises(ValueError, match="fixed rule"):
+        el.settings(plan)
+    records = [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0)]
+    with pytest.raises(ValueError, match="fixed rule"):
+        decide(records, [flag("exact_duplicate", "identical values", 1, 3)], plan)
+
+
 def test_the_fixed_rules_hold_in_every_set_the_plan_names():
     """Sensitivity sets change only what their key names: conflicts keep 'neither' or the survivor's
     value; exact duplicates stay counted once; invalid values and ambiguous groups stay out except
````

### `dc85887 Step 6 re-check fix: paper identity apart from grouping; one outcome`

````diff
dc85887d5452e14a1cf00caa41be94fcfcb6ce77

Step 6 re-check fix: paper identity apart from grouping; one outcome

Re-check finding 2. (a) Grouping set MPEA's paper to "dataset:mpea", so
identical records citing the same paper stopped matching. Paper identity
now comes only from the records' own normalized paper references (both
DOIs, else both reference texts, else unknown); grouping is for clustering
only. (b) With another outcome the tensile-below-yield check did not run.
Physical validity is now checked on every record whatever the outcome,
Checks compares yield strength, and validation refuses any outcome but
yield strength (register supported_outcomes). The 5 new tests failed on the
code before this change; three tests whose premise changed are listed in
the summary.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 38dd9b5..408d1e6 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -399,13 +399,15 @@
     "tests": [
       "tests/test_controlled_duplicates_handling.py::test_the_flag_is_the_answer_files",
       "tests/test_eligibility.py::test_an_ambiguous_group_keeps_its_conflict_in_every_set",
-      "tests/test_flags.py::test_a_dataset_source_is_its_own_paper",
+      "tests/test_flags.py::test_a_source_without_per_record_papers_is_compared_by_its_reference",
       "tests/test_flags.py::test_a_group_whose_records_are_not_all_linked_is_ambiguous",
       "tests/test_flags.py::test_a_group_with_one_conflicting_pair_is_a_conflict",
       "tests/test_flags.py::test_a_known_difference_in_paper_or_conditions_means_no_pair",
       "tests/test_flags.py::test_an_unknown_paper_or_condition_gives_a_possible_duplicate_only_if_the_values_match",
+      "tests/test_flags.py::test_paper_identity_does_not_depend_on_the_grouping_setting",
       "tests/test_flags.py::test_rows_within_one_source_are_never_compared",
-      "tests/test_flags.py::test_several_candidates_from_one_source_pair_nothing"
+      "tests/test_flags.py::test_several_candidates_from_one_source_pair_nothing",
+      "tests/test_flags.py::test_without_a_doi_the_normalized_paper_reference_identifies_the_paper"
     ],
     "history": [
       {
@@ -426,8 +428,8 @@
       "Not reviewed by an expert.",
       "Related: entry 'observation_unit' (what one source row represents) and entry 'values_disagree_tolerance' (the 2% tolerance).",
       "A record with a missing test condition is also 'scope not confirmed': Checks still raises the possible-duplicate flag, and Inclusion applies the scope rule before the duplicate rule (owner, 2026-10-05).",
-      "A paper is identified by its DOI (derived key); a source grouped by dataset (Texas A&M) cites itself.",
-      "Step 6 review, finding 4 (2026-10-06): an ambiguous group that contains a definite conflict keeps it as its own conflict flag; the conflicting records stay out wherever conflicts are excluded, including 'possible_duplicates_separate'."
+      "Step 6 review, finding 4 (2026-10-06): an ambiguous group that contains a definite conflict keeps it as its own conflict flag; the conflicting records stay out wherever conflicts are excluded, including 'possible_duplicates_separate'.",
+      "A paper is identified from the records' own normalized paper references: both DOIs (derived key), else both reference texts (spaces collapsed, case-folded), else unknown. The plan's grouping is for clustering only and never changes paper identity (re-check finding 2a, 2026-10-06). Texas A&M records carry the dataset's reference and no DOI."
     ]
   },
   {
@@ -1300,12 +1302,14 @@
       }
     ],
     "notes": [
-      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants')."
+      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants').",
+      "Checked on every record whatever the plan's outcome (re-check finding 2b, 2026-10-06)."
     ],
     "tests": [
       "tests/test_eligibility.py::test_each_rule_on_its_own",
       "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set",
       "tests/test_flags.py::test_flags_come_from_pairwise_comparisons_and_group_classification",
+      "tests/test_flags.py::test_physical_validity_does_not_depend_on_the_outcome_setting",
       "tests/test_flags.py::test_physically_impossible_values_are_flagged_per_record"
     ]
   },
@@ -4747,7 +4751,7 @@
     "key": "fixed_policies_in_code",
     "name": "Policies fixed in code for every plan",
     "state": "in_force",
-    "statement": "Plan settings (scope, exclusion rules, eligibility rules within the fixed choices, the plan's rules, sufficiency) are read from the locked plan only, never from the domain profile. These policies are fixed in code and the same for every plan: which statuses carry a value; what counts as physically invalid (tensile strength below yield strength, grain size of zero or less); which test conditions are compared (test type and temperature); how a paper is identified (the DOI's derived key; a source grouped by dataset cites itself); the room-temperature band's name; the order of the eligibility rules; the ambiguity rule; the fixed rules for the primary set ('primary_set_invariants'); the structure of the survivor rule and its stable tie-breaker; the change each sensitivity key applies; and the code roles' field lists. Changing one is a code change with this entry, needing the owner's approval.",
+    "statement": "Plan settings (scope, exclusion rules, eligibility rules within the fixed choices, the plan's rules, sufficiency) are read from the locked plan only, never from the domain profile. These policies are fixed in code and the same for every plan: which statuses carry a value; what counts as physically invalid (tensile strength below yield strength, grain size of zero or less); which test conditions are compared (test type and temperature); how a paper is identified (from the records' own normalized paper references: both DOIs, else both reference texts, else unknown; never from the plan's grouping, which is for clustering only); that physical validity is checked on every record whatever the plan's outcome; the supported outcome ('supported_outcomes'); the room-temperature band's name; the order of the eligibility rules; the ambiguity rule; the fixed rules for the primary set ('primary_set_invariants'); the structure of the survivor rule and its stable tie-breaker; the change each sensitivity key applies; and the code roles' field lists. Changing one is a code change with this entry, needing the owner's approval.",
     "value": {
       "text": "eleven fixed policies",
       "unit": null
@@ -4786,12 +4790,68 @@
       ],
       "note": "The meaning of each sensitivity key must stay stable, or be versioned with the domain profile."
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Plan settings (scope, exclusion rules, eligibility rules within the fixed choices, the plan's rules, sufficiency) are read from the locked plan only, never from the domain profile. These policies are fixed in code and the same for every plan: which statuses carry a value; what counts as physically invalid (tensile strength below yield strength, grain size of zero or less); which test conditions are compared (test type and temperature); how a paper is identified (the DOI's derived key; a source grouped by dataset cites itself); the room-temperature band's name; the order of the eligibility rules; the ambiguity rule; the fixed rules for the primary set ('primary_set_invariants'); the structure of the survivor rule and its stable tie-breaker; the change each sensitivity key applies; and the code roles' field lists. Changing one is a code change with this entry, needing the owner's approval.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Before the re-check (finding 2a)."
+      }
+    ],
     "notes": [],
     "tests": [
-      "tests/test_eligibility.py::test_each_setting_is_read_from_the_locked_plan",
       "tests/test_eligibility.py::test_decisions_ignore_the_domain_profile",
-      "tests/test_flags.py::test_flags_come_from_pairwise_comparisons_and_group_classification"
+      "tests/test_eligibility.py::test_each_setting_is_read_from_the_locked_plan",
+      "tests/test_flags.py::test_flags_come_from_pairwise_comparisons_and_group_classification",
+      "tests/test_flags.py::test_paper_identity_does_not_depend_on_the_grouping_setting",
+      "tests/test_flags.py::test_physical_validity_does_not_depend_on_the_outcome_setting"
+    ]
+  },
+  {
+    "key": "supported_outcomes",
+    "name": "Supported outcomes",
+    "state": "in_force",
+    "statement": "Sprint 1 supports one model, whose outcome is yield strength. Plan validation refuses a plan with any other outcome.",
+    "value": {
+      "text": "yield_strength",
+      "unit": null
+    },
+    "category": "statistical",
+    "affects": "Which plans can be locked; the outcome Checks compares for duplicates and conflicts.",
+    "reason": "Re-check finding 2b: choosing another outcome disabled a physical-validity check; CLAUDE.md rule 6 allows one model.",
+    "evidence": [
+      "docs/reviews/step06_recheck_chatgpt.md, finding 2; the owner's instruction of 2026-10-06."
+    ],
+    "decided": {
+      "by": "owner (Khalid El-Awady)",
+      "date": "2026-10-06"
+    },
+    "expert_review": {
+      "status": "not_reviewed",
+      "name": null,
+      "date": null
+    },
+    "sensitivity": null,
+    "applied": {
+      "status": "yes",
+      "settings": [
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:SUPPORTED_OUTCOMES",
+          "equals": [
+            "yield_strength"
+          ]
+        },
+        {
+          "ref": "python:hypocurate.pipeline.flags:COMPARED_OUTCOME",
+          "equals": "yield_strength"
+        }
+      ],
+      "note": null
+    },
+    "history": [],
+    "notes": [],
+    "tests": [
+      "tests/test_plan.py::test_invalid_plans_are_refused"
     ]
   }
 ]
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index 68de0e3..182b79e 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -49,6 +49,9 @@ from typing import Any, Iterable, Mapping
 from hypocurate.sources.normalize import same_alloy_key
 
 PRIMARY = "primary"
+# Sprint 1 supports one model (CLAUDE.md rule 6): its outcome is yield strength. Plan validation
+# refuses any other (re-check finding 2b; register 'supported_outcomes').
+SUPPORTED_OUTCOMES = ("yield_strength",)
 FLAG_STAGE_RULES = ("identity_unresolved", "conflict_unresolved", "duplicate_counted_once")
 
 # Fixed rules, not plan defaults (owner, 2026-10-06; register 'primary_set_invariants'): what each
diff --git a/hypocurate/pipeline/flags.py b/hypocurate/pipeline/flags.py
index 85f8dbe..80cbcd2 100644
--- a/hypocurate/pipeline/flags.py
+++ b/hypocurate/pipeline/flags.py
@@ -72,21 +72,43 @@ def _number(rec: Mapping, f: str, statuses=VALUE_STATUSES) -> float | None:
     return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) else None
 
 
-def paper(rec: Mapping, grouping: Mapping[str, str]) -> str | None:
-    """The paper a record cites: from its DOI for a source grouped by paper; the dataset
-    itself for a source that is its own paper (grouped by dataset)."""
-    if grouping.get(rec["source"]) in ("dataset", "batch"):
-        return f"dataset:{rec['source']}"
+# The outcome Checks compares: the one supported model's (re-check finding 2b; plans with
+# another outcome are refused at validation, `eligibility.SUPPORTED_OUTCOMES`).
+COMPARED_OUTCOME = "yield_strength"
+
+
+def _doi(rec: Mapping) -> str | None:
     doi = rec.get("paper_doi")
-    return identity_hash(doi_group_key(doi)) if isinstance(doi, str) and doi.strip() else None
+    return doi_group_key(doi) if isinstance(doi, str) and doi.strip() else None
+
+
+def _reference(rec: Mapping) -> str | None:
+    """The paper reference as reported, normalized: spaces collapsed, case-folded."""
+    ref = rec.get("paper_reference")
+    return " ".join(ref.split()).casefold() if isinstance(ref, str) and ref.strip() else None
+
+
+def same_paper(a: Mapping, b: Mapping) -> bool | None:
+    """Whether two records cite the same paper, from their own normalized paper references only
+    (re-check finding 2a: never from the plan's grouping, which is for clustering): both DOIs
+    known, compare them; else both references known, compare them; else unknown (None)."""
+    da, db = _doi(a), _doi(b)
+    if da and db:
+        return da == db
+    ra, rb = _reference(a), _reference(b)
+    if ra and rb:
+        return ra == rb
+    return None
 
 
-def invalid_values(records: Iterable[Mapping], outcome: str) -> list[Flag]:
+def invalid_values(records: Iterable[Mapping], outcome: str | None = None) -> list[Flag]:
+    """Physically impossible values, on every record whatever the plan's outcome (re-check
+    finding 2b): tensile strength below yield strength; a grain size of zero or less."""
     out = []
     for r in records:
-        ys, uts, gs = _number(r, outcome), _number(r, "ultimate_tensile_strength"), _number(r, "grain_size")
+        ys, uts, gs = _number(r, "yield_strength"), _number(r, "ultimate_tensile_strength"), _number(r, "grain_size")
         reasons = {}
-        if outcome == "yield_strength" and ys is not None and uts is not None and uts < ys:
+        if ys is not None and uts is not None and uts < ys:
             reasons["ultimate_tensile_strength_below_yield_strength"] = [uts, ys]
         if gs is not None and gs <= 0:
             reasons["grain_size_not_positive"] = [gs]
@@ -98,11 +120,10 @@ def invalid_values(records: Iterable[Mapping], outcome: str) -> list[Flag]:
 @dataclass(frozen=True)
 class Matching:
     """The settings that decide which records are compared (step 6 review, finding 2): the
-    same-alloy step, the tolerance, the grouping (a dataset cites itself) and the value statuses
-    that count as known."""
+    same-alloy step, the tolerance and the value statuses that count as known. Not the grouping,
+    which is for clustering only (re-check finding 2a)."""
     decimals: int
     tolerance: float
-    grouping: tuple
     statuses: tuple
 
 
@@ -110,8 +131,7 @@ def matching(plan: Mapping[str, Any], key: str = "primary") -> Matching:
     """The matching settings of set `key` under the locked plan (its own change applied)."""
     from hypocurate.pipeline.eligibility import settings
     st = settings(plan, key)
-    return Matching(st.decimals, plan["rules"]["duplicate_tolerance"], tuple(sorted(st.grouping.items())),
-                    tuple(sorted(st.statuses)))
+    return Matching(st.decimals, plan["rules"]["duplicate_tolerance"], tuple(sorted(st.statuses)))
 
 
 def _condition(a: Mapping, b: Mapping, statuses=VALUE_STATUSES) -> str:
@@ -128,20 +148,20 @@ def _condition(a: Mapping, b: Mapping, statuses=VALUE_STATUSES) -> str:
 
 def _link(a: Mapping, b: Mapping, plan: Mapping, m: Matching) -> tuple[str, dict] | None:
     """The candidate link between two records of different sources, or None."""
-    tol, outcome, st, grouping = m.tolerance, plan["variables"]["outcome"]["field"], m.statuses, dict(m.grouping)
+    tol, outcome, st = m.tolerance, COMPARED_OUTCOME, m.statuses
     ga, gb, ya, yb = (_number(a, "grain_size", st), _number(b, "grain_size", st), _number(a, outcome, st),
                       _number(b, outcome, st))
     if None in (ga, gb, ya, yb) or relative_difference(ga, gb) > tol:
         return None
-    pa, pb = paper(a, grouping), paper(b, grouping)
-    if pa is not None and pb is not None and pa != pb:
+    paper = same_paper(a, b)
+    if paper is False:
         return None
     cond = _condition(a, b, st)
     if cond == "differs":
         return None
     numbers = {"grain_size": [ga, gb], outcome: [ya, yb], "relative_difference": relative_difference(ya, yb)}
     within = numbers["relative_difference"] <= tol
-    if pa is not None and pb is not None and cond == "same":
+    if paper is True and cond == "same":
         return ("exact" if within else "conflict"), numbers
     return ("possible", numbers) if within else None
 
@@ -200,7 +220,7 @@ def duplicate_groups(records: list[Mapping], plan: Mapping[str, Any], m: Matchin
 
 def raise_flags(plan: Mapping[str, Any], records: list[Mapping]) -> list[Flag]:
     """Every flag for the run's records under the locked plan, in a fixed order."""
-    return invalid_values(records, plan["variables"]["outcome"]["field"]) + duplicate_groups(records, plan)
+    return invalid_values(records) + duplicate_groups(records, plan)
 
 
 def set_flags(plan: Mapping[str, Any], records: list[Mapping]) -> dict[str, list[Flag]]:
diff --git a/hypocurate/pipeline/plan.py b/hypocurate/pipeline/plan.py
index 13dc593..f301d87 100644
--- a/hypocurate/pipeline/plan.py
+++ b/hypocurate/pipeline/plan.py
@@ -29,7 +29,7 @@ from hypocurate.access.allowlist import PLAN_SCHEMA
 from hypocurate.access.fields import project
 from hypocurate.access.vocabulary import SENSITIVITY_KEYS
 from hypocurate.pipeline import profile as p
-from hypocurate.pipeline.eligibility import fixed_rule_problems
+from hypocurate.pipeline.eligibility import SUPPORTED_OUTCOMES, fixed_rule_problems
 
 PARTS = ("hypothesis_version", "variables", "scope", "model", "sufficiency", "fields_to_extract", "exclusion_rules",
          "eligibility_rules", "verdict_statement", "sensitivity_analyses", "profile", "rules")
@@ -119,6 +119,8 @@ def _check_template(c: dict) -> None:
         raise PlanError("variables need an outcome (field, unit) and a predictor (field, unit, transformation)")
     if (v["predictor"]["field"], v["predictor"]["unit"]) != ("grain_size", "µm"):
         raise PlanError("the supported model's predictor is grain size in µm")
+    if v["outcome"]["field"] not in SUPPORTED_OUTCOMES:
+        raise PlanError(f"the supported outcome is {', '.join(SUPPORTED_OUTCOMES)} (one model in sprint 1)")
     if v["outcome"]["field"] == v["predictor"]["field"]:
         raise PlanError("the outcome and the predictor are different fields")
     if set(m) != {"name", "null", "alternative", "alpha"} or not 0 < m["alpha"] < 1:
diff --git a/tests/test_flags.py b/tests/test_flags.py
index a45b7a0..c0c9d4d 100644
--- a/tests/test_flags.py
+++ b/tests/test_flags.py
@@ -24,12 +24,13 @@ PLAN = default_plan(1)
 DOI = "10.1016/j.test.2020.001"
 
 
-def rec(i, source="mpea", comp=None, gs=10.0, ys=400.0, uts=None, doi=DOI, test_type="tension", temp=25.0):
+def rec(i, source="mpea", comp=None, gs=10.0, ys=400.0, uts=None, doi=DOI, test_type="tension", temp=25.0,
+        reference=None):
     def v(value, unit=None):
         return {"value": value, "unit": unit, "status": "converted"} if value is not None else \
             {"value": None, "unit": unit, "status": "not_reported", "reason": "blank in the source"}
     return {"id": i, "source": source, "origin": f"{source}.csv:row:{i}", "item_index": 0, "kind": "measured",
-            "alloy": "x", "paper_reference": None, "paper_doi": doi, "version_fingerprint": "f" * 64, "reported": {},
+            "alloy": "x", "paper_reference": reference, "paper_doi": doi, "version_fingerprint": "f" * 64, "reported": {},
             "harmonized": {"composition": v(comp or {"Co": 50.0, "Ni": 50.0}, "at.%"), "grain_size": v(gs, "µm"),
                            "yield_strength": v(ys, "MPa"), "ultimate_tensile_strength": v(uts, "MPa"),
                            "test_type": v(test_type), "test_temperature": v(temp, "°C")}}
@@ -141,9 +142,46 @@ def test_a_group_with_one_conflicting_pair_is_a_conflict():
                    ("values_disagree", "differ beyond tolerance", [1, 3])]
 
 
-def test_a_dataset_source_is_its_own_paper():
-    """Texas A&M (grouped by dataset) cites itself: never paired with a record citing another paper."""
-    assert kinds([rec(1), rec(2, "tamu_fcc", doi=None)]) == []
+def test_paper_identity_does_not_depend_on_the_grouping_setting():
+    """Re-check finding 2a, the reviewer's case: MPEA grouped by dataset, the extract by paper.
+    Identical records citing the same DOI are still the same paper, so an exact duplicate.
+    Grouping is used only for clustering in the analysis."""
+    plan = copy.deepcopy(PLAN)
+    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "dataset"}, {"source": "tamu_fcc", "unit": "dataset"},
+                                 {"source": "controlled_duplicates", "unit": "paper"}]
+    assert kinds([rec(1), rec(2, "controlled_duplicates")], plan) == [("exact_duplicate", "identical values", [1, 2])]
+    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
+                                 {"source": "controlled_duplicates", "unit": "paper"}]
+    assert kinds([rec(1, reference="Effect of annealing on CoCrFeMnNi"),
+                  rec(2, "tamu_fcc", doi=None, reference="Mulukutla et al. 2026")], plan) == []
+
+
+def test_without_a_doi_the_normalized_paper_reference_identifies_the_paper():
+    """Both records without a DOI: the same reference (spaces and case aside) is the same paper,
+    another reference is another paper; a reference against a DOI or nothing is unknown."""
+    a = rec(1, "tamu_fcc", doi=None, reference="Mulukutla, M. et al. (2026).  Dataset v1.1.0")
+    same = rec(2, "controlled_duplicates", doi=None, reference="mulukutla, m. et al. (2026). dataset v1.1.0")
+    other = rec(3, "controlled_duplicates", doi=None, reference="Another paper (2019)")
+    assert kinds([a, same]) == [("exact_duplicate", "identical values", [1, 2])]
+    assert kinds([a, other]) == []
+    assert kinds([a, rec(4, "controlled_duplicates", doi=None)])[0][0] == "possible_duplicate"
+
+
+def test_physical_validity_does_not_depend_on_the_outcome_setting():
+    """Re-check finding 2b, the reviewer's case: with tensile strength as the outcome (a plan that
+    bypassed validation), tensile strength 399 below yield strength 400 is still invalid."""
+    plan = copy.deepcopy(PLAN)
+    plan["variables"]["outcome"]["field"] = "ultimate_tensile_strength"
+    assert kinds([rec(1, uts=399.0)], plan) == [("invalid_value", "physically impossible", [1])]
+
+
+def test_a_source_without_per_record_papers_is_compared_by_its_reference():
+    """Texas A&M has no per-record paper: its records carry the dataset's reference and no DOI.
+    Against a record with a DOI and a title, the references differ, so they are never paired.
+    (Replaces 'a dataset source is its own paper', which came from the grouping setting until the
+    re-check, finding 2a.)"""
+    tamu = rec(2, "tamu_fcc", doi=None, reference="Mulukutla, M. et al. (2026). Revisiting Hall-Petch")
+    assert kinds([rec(1, reference="Effect of annealing on CoCrFeMnNi"), tamu]) == []
 
 
 def _world(seed):
@@ -198,7 +236,7 @@ def test_flags_come_from_pairwise_comparisons_and_group_classification(seed):
     assert kinds(changed, blind) == before
 
 
-def test_checks_imports_no_statistics_and_reads_only_the_rules_and_the_outcome_field():
+def test_checks_imports_no_statistics_and_reads_only_the_rules_and_the_set_names():
     source = Path(fl.__file__).read_text()
     tree = ast.parse(source)
     imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
@@ -208,4 +246,5 @@ def test_checks_imports_no_statistics_and_reads_only_the_rules_and_the_outcome_f
     plan_keys = {n.slice.value for n in ast.walk(tree) if isinstance(n, ast.Subscript)
                  and isinstance(n.value, ast.Name) and n.value.id == "plan" and isinstance(n.slice, ast.Constant)}
     # Step 6 review, finding 2: the names of the sensitivity sets, to compute each set's own flags.
-    assert plan_keys == {"rules", "variables", "sensitivity_analyses"}
+    # Re-check finding 2b: not the plan's outcome (Checks compares yield strength, the one supported).
+    assert plan_keys == {"rules", "sensitivity_analyses"}
diff --git a/tests/test_plan.py b/tests/test_plan.py
index 7a520c6..d4bc621 100644
--- a/tests/test_plan.py
+++ b/tests/test_plan.py
@@ -125,6 +125,9 @@ def test_the_plan_choices_that_remain():
     (lambda c: c["sensitivity_analyses"].append("removal_after_lock"), "named once each"),
     (lambda c: c["model"].update(alpha=1.5), "threshold"),
     (lambda c: c["variables"]["predictor"].update(field="hardness"), "grain size"),
+    # Re-check finding 2b: sprint 1 supports one model, whose outcome is yield strength.
+    (lambda c: c["variables"]["outcome"].update(field="ultimate_tensile_strength"), "supported outcome"),
+    (lambda c: c["variables"]["outcome"].update(field="hardness", unit="HV"), "supported outcome"),
 ])
 def test_invalid_plans_are_refused(change, message):
     content = default_plan(1)
````

### `9d964e2 Step 6 re-check fix: Inclusion and the freeze verify Checks as they read`

````diff
9d964e2474e3ee6898056cbcb25504acd9b20f50

Step 6 re-check fix: Inclusion and the freeze verify Checks as they read

Re-check finding 1: Inclusion could read before Checks completed (empty
per-set flags), Checks then commit, and the stale decisions pass the
coverage check. The set_flags reader now verifies, in the same transaction
under the run's lock that reads Inclusion's inputs, that a completed Checks
result covers exactly the records and flags read, and refuses otherwise; a
sensitivity set whose required own flags are missing is refused, never
read as "no flags". The binding helpers move to pipeline/binding.py. The
reviewer's interleaving and the missing-flags case failed on the code
before this change; the projected-data test now first completes Checks.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/access/fields.py b/hypocurate/access/fields.py
index 103a3ad..b148d6d 100644
--- a/hypocurate/access/fields.py
+++ b/hypocurate/access/fields.py
@@ -33,6 +33,7 @@ from hypocurate.access.allowlist import (BATCH_COLUMNS, CATEGORY_FIELDS, CONDITI
                                          CONDITION_RANGE_FIELDS, OUTCOME_FIELDS, PLAN_SCHEMA, POWER_SCHEMA,
                                          SOURCE_META_FIELDS)
 from hypocurate.access.context import AccessContext as Context
+from hypocurate.pipeline.binding import binding, record_identity
 from hypocurate.sources import adapters
 from hypocurate.sources.normalize import alloy_label, doi_group_key, identity_hash, same_alloy_key
 from hypocurate.sources.record import HARMONIZED_FIELDS, STATUSES, VALUE_STATUSES, AdapterError
@@ -316,10 +317,24 @@ def record_conditions(conn: Connection, ctx: Context) -> list[dict]:
 
 def set_flags(conn: Connection, ctx: Context) -> dict:
     """The per-set matching flags of the run's completed Checks result (step 6 review, finding 2):
-    codes and record ids only."""
+    codes and record ids only.
+
+    Re-check finding 1: read in the same transaction as the role's other fields, under the run's
+    lock, and only after verifying that a completed Checks result exists and covers exactly the
+    records and flags of the run as they are now; otherwise the read is refused
+    (`checks_not_done`, `checks_not_current`), never answered with "no flags"."""
     output = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'checks' "
                                "AND status = 'done' ORDER BY id DESC LIMIT 1"), dict(r=ctx.run_id)).scalar_one_or_none()
-    stored = output.get("set_flags", {}) if isinstance(output, Mapping) else {}
+    if not isinstance(output, Mapping) or not isinstance(output.get("binding"), Mapping):
+        raise Refused("checks_not_done")
+    identity = {i: record_identity(fp, key, ix) for i, fp, key, ix in _rows(
+        conn, "SELECT r.id, sv.fingerprint, r.source_item_key, r.item_index FROM record r "
+              "JOIN source_version sv ON sv.id = r.source_version_id WHERE r.extraction_run_id = :r", r=ctx.run_id)}
+    flagged = [(f.kind, f.category, [identity[x] for x in _flag_records(conn, ctx).get(f.id, []) if x in identity])
+               for f in _rows(conn, "SELECT id, kind, category FROM flag WHERE run_id = :r", r=ctx.run_id)]
+    if binding(identity.values(), flagged) != dict(output["binding"]):
+        raise Refused("checks_not_current")
+    stored = output.get("set_flags", {})
     out = {}
     for key, flags in (stored.items() if isinstance(stored, Mapping) else ()):
         out[vocab.code(key, vocab.SENSITIVITY_KEYS)] = [
diff --git a/hypocurate/access/layer.py b/hypocurate/access/layer.py
index b43ac3c..6774f63 100644
--- a/hypocurate/access/layer.py
+++ b/hypocurate/access/layer.py
@@ -80,6 +80,8 @@ DENIALS = {
     "source_not_for_role": "only the Curator is bound to a source",
     "setting_not_recorded": "the agent setting is not recorded for this run",
     "empty_list": "the role has no field at this stage",
+    "checks_not_done": "no completed Checks result for this run",
+    "checks_not_current": "the completed Checks result does not cover exactly the run's records and flags",
 }
 FAILURES = ("unknown_run", "lock_timeout", "reader_error", "database_error", "file_guard")
 FUNCTIONS = frozenset(FIELDS) | {"role_input", "bind", "guarded_run"}
diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 408d1e6..5668454 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -4703,7 +4703,7 @@
     "key": "checks_bound_to_records",
     "name": "Checks cover exactly the records decided on",
     "state": "in_force",
-    "statement": "Checks run only when every chosen source has been stored (or has failed), and no record is stored after them. The completed Checks result records exactly which records (by stable identity) and flags it covered; Inclusion and the dataset freeze refuse, and log the refusal, without a completed Checks result or when it does not cover exactly the run's records and flags.",
+    "statement": "Checks run only when every chosen source has been stored (or has failed), and no record is stored after them. The completed Checks result records exactly which records (by stable identity) and flags it covered; Inclusion and the dataset freeze refuse, and log the refusal, without a completed Checks result or when it does not cover exactly the run's records and flags. Inclusion and the freeze read their inputs in the same transaction, under the run's lock, that verifies the completed Checks result covers exactly those records and flags; a sensitivity set whose own flags are missing from that result is refused, never treated as having no flags.",
     "value": {
       "text": "extraction, then Checks, then Inclusion and the freeze, bound by the record collection",
       "unit": null
@@ -4732,19 +4732,35 @@
         },
         {
           "ref": "python:hypocurate.pipeline.writes:binding"
+        },
+        {
+          "ref": "python:hypocurate.access.fields:set_flags"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:needs_own_flags"
         }
       ],
       "note": null
     },
-    "history": [],
+    "history": [
+      {
+        "value": "Checks run only when every chosen source has been stored (or has failed), and no record is stored after them. The completed Checks result records exactly which records (by stable identity) and flags it covered; Inclusion and the dataset freeze refuse, and log the refusal, without a completed Checks result or when it does not cover exactly the run's records and flags.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Before the re-check (finding 1)."
+      }
+    ],
     "notes": [
       "A source refused by the constructed-data guard stays pending, so Checks cannot run until it is marked failed: the run's orchestration (step 9) must do that."
     ],
     "tests": [
+      "tests/test_access_code_roles.py::test_inclusion_receives_no_outcome_value",
       "tests/test_checkpoints.py::test_a_record_added_after_checks_is_refused_at_inclusion_and_the_freeze",
       "tests/test_checkpoints.py::test_checks_wait_until_every_chosen_source_is_stored",
       "tests/test_checkpoints.py::test_no_record_is_stored_after_checks",
-      "tests/test_checkpoints.py::test_skipping_checks_is_refused_at_inclusion_and_the_freeze"
+      "tests/test_checkpoints.py::test_skipping_checks_is_refused_at_inclusion_and_the_freeze",
+      "tests/test_sensitivity_matching.py::test_a_missing_required_per_set_flag_result_is_a_refusal",
+      "tests/test_sensitivity_matching.py::test_the_reviewers_interleaving_is_refused"
     ]
   },
   {
diff --git a/hypocurate/pipeline/binding.py b/hypocurate/pipeline/binding.py
new file mode 100644
index 0000000..25d21cf
--- /dev/null
+++ b/hypocurate/pipeline/binding.py
@@ -0,0 +1,22 @@
+"""What a completed Checks result covered (step 6 review, finding 1; re-check finding 1).
+
+No database and no access-layer import, so that the access layer (Inclusion's `set_flags`
+reader) and the pipeline's write paths compute the binding the same way."""
+from __future__ import annotations
+
+import hashlib
+
+
+def record_identity(version_fingerprint: str, origin: str, item_index: int) -> str:
+    """A record's stable identity: never its database id."""
+    return f"{version_fingerprint}|{origin}|{item_index}"
+
+
+def binding(identities, flags) -> dict:
+    """The exact record collection (by stable identity) and the flags raised for it (kind,
+    category and the identities of their records)."""
+    ids = sorted(identities)
+    digest = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
+    flag_lines = sorted(f"{k}|{c}|{','.join(sorted(r))}" for k, c, r in flags)
+    return {"records": len(ids), "identities": digest,
+            "flags": hashlib.sha256("\n".join(flag_lines).encode("utf-8")).hexdigest()}
diff --git a/hypocurate/pipeline/checkpoints.py b/hypocurate/pipeline/checkpoints.py
index d18f274..926e07e 100644
--- a/hypocurate/pipeline/checkpoints.py
+++ b/hypocurate/pipeline/checkpoints.py
@@ -33,7 +33,8 @@ from hypocurate.access.dispatch import bind_code
 from hypocurate.access.inputs import role_input
 from hypocurate.pipeline import eligibility as el
 from hypocurate.pipeline.plan import PlanError, canonical, fingerprint, tags_for, validate
-from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, flag_index, log_refusal,
+from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, decide_sets, flag_index,
+                                        inclusion_input, log_refusal,
                                         record_identity, record_ids, require_checks_cover, run_record_sources,
                                         write)
 
@@ -98,10 +99,10 @@ def _set_records(conn: Connection, run_id: int) -> dict[str, list[int]]:
 
 def freeze_dataset(engine: Engine, run_id: int) -> dict:
     """Freezes the analysis dataset (or records that none is frozen); returns the freeze record."""
-    data = role_input(bind_code(engine, run_id, "inclusion"))
+    data = inclusion_input(engine, run_id, "checkpoint", "freeze_dataset")
     plan, records, flags = data["plan"]["content"], data["record_conditions"], data["flags_kind"]
     by_id = {r["id"]: r for r in records}
-    sets = el.all_sets(plan, records, flags, data["set_flags"])
+    sets = decide_sets(engine, run_id, "checkpoint", "freeze_dataset", data)
     members = {key: el.members(rules) for key, rules in sets.items()}
     counts: dict[str, Any] = {key: el.counts(plan, by_id, ids, key) for key, ids in members.items()}
     counts["per_source"] = {source: el.counts(plan, by_id, [i for i in members[el.PRIMARY]
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index 182b79e..1408d42 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -314,10 +314,27 @@ def decide(plan: Mapping[str, Any], records: Iterable[Mapping], flags: Iterable[
     return rules
 
 
-def flags_for(key: str, flags: list[Mapping], set_flags: Mapping[str, list] | None) -> list[Mapping]:
+class MissingSetFlags(ValueError):
+    """A sensitivity set needs its own matching flags and the Checks result lacks them."""
+
+
+def needs_own_flags(plan: Mapping[str, Any], key: str) -> bool:
+    """Whether set `key` changes a matching setting (the same-alloy step or the value statuses), so
+    that it needs its own duplicate, conflict and ambiguity flags from Checks."""
+    if key == PRIMARY:
+        return False
+    a, b = settings(plan), settings(plan, key)
+    return (a.decimals, a.statuses) != (b.decimals, b.statuses)
+
+
+def flags_for(key: str, flags: list[Mapping], set_flags: Mapping[str, list] | None,
+              plan: Mapping[str, Any] | None = None) -> list[Mapping]:
     """The flags set `key` applies: its own matching flags from Checks where its matching settings
     differ (step 6 review, finding 2), with the primary set's invalid-value flags; else the primary
-    set's flags."""
+    set's flags. A required result that is missing is refused, never read as "no flags"
+    (re-check finding 1)."""
+    if plan is not None and needs_own_flags(plan, key) and (not set_flags or key not in set_flags):
+        raise MissingSetFlags(f"the Checks result has no flags for the set {key!r}")
     if not set_flags or key not in set_flags:
         return flags
     own = [{"id": 10 ** 12 + n, **f} for n, f in enumerate(set_flags[key])]
@@ -327,7 +344,7 @@ def flags_for(key: str, flags: list[Mapping], set_flags: Mapping[str, list] | No
 def all_sets(plan: Mapping[str, Any], records: list[Mapping], flags: list[Mapping],
              set_flags: Mapping[str, list] | None = None) -> dict[str, dict[int, str]]:
     """The primary set and every sensitivity set the plan names, each with its own flags."""
-    return {key: decide(plan, records, flags_for(key, flags, set_flags), key)
+    return {key: decide(plan, records, flags_for(key, flags, set_flags, plan), key)
             for key in (PRIMARY, *plan["sensitivity_analyses"])}
 
 
diff --git a/hypocurate/pipeline/flags.py b/hypocurate/pipeline/flags.py
index 80cbcd2..5b442db 100644
--- a/hypocurate/pipeline/flags.py
+++ b/hypocurate/pipeline/flags.py
@@ -227,10 +227,6 @@ def set_flags(plan: Mapping[str, Any], records: list[Mapping]) -> dict[str, list
     """For each sensitivity set whose matching settings differ from the primary set's, the
     duplicate, conflict and ambiguity flags under its own settings (step 6 review, finding 2).
     Invalid values do not depend on matching; the set uses the primary set's."""
-    primary = matching(plan)
-    out = {}
-    for key in plan["sensitivity_analyses"]:
-        m = matching(plan, key)
-        if m != primary:
-            out[key] = duplicate_groups(records, plan, m)
-    return out
+    from hypocurate.pipeline.eligibility import needs_own_flags
+    return {key: duplicate_groups(records, plan, matching(plan, key))
+            for key in plan["sensitivity_analyses"] if needs_own_flags(plan, key)}
diff --git a/hypocurate/pipeline/inclusion.py b/hypocurate/pipeline/inclusion.py
index 5ecf603..faab423 100644
--- a/hypocurate/pipeline/inclusion.py
+++ b/hypocurate/pipeline/inclusion.py
@@ -20,14 +20,15 @@ from sqlalchemy import Connection, Engine, text
 from hypocurate.access.dispatch import bind_code
 from hypocurate.access.inputs import role_input
 from hypocurate.pipeline import eligibility as el
-from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, flag_index, record_identity,
+from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, decide_sets, flag_index,
+                                        inclusion_input, record_identity,
                                         record_ids, require_checks_cover, run_record_sources, write)
 
 
 def decide_run(engine: Engine, run_id: int) -> dict[str, dict[int, str]]:
-    data = role_input(bind_code(engine, run_id, "inclusion"))
+    data = inclusion_input(engine, run_id, "inclusion", "decide")
     plan, records, flags = data["plan"]["content"], data["record_conditions"], data["flags_kind"]
-    sets = el.all_sets(plan, records, flags, data["set_flags"])
+    sets = decide_sets(engine, run_id, "inclusion", "decide", data)
     read_ids = sorted(r["id"] for r in records)
     read_flags = [(f["id"], f["kind"], f["category"], tuple(sorted(f["records"]))) for f in flags]
     identity_of = {r["id"]: record_identity(r["version_fingerprint"], r["origin"], r["item_index"]) for r in records}
diff --git a/hypocurate/pipeline/writes.py b/hypocurate/pipeline/writes.py
index fc51e2e..140127e 100644
--- a/hypocurate/pipeline/writes.py
+++ b/hypocurate/pipeline/writes.py
@@ -39,6 +39,7 @@ from sqlalchemy.exc import DBAPIError, IntegrityError
 from hypocurate.access.layer import ACCESS_LOCK_TIMEOUT_MS
 from hypocurate.access.stage import actual_stage
 from hypocurate.db.retry import run_transaction
+from hypocurate.pipeline.binding import binding, record_identity  # noqa: F401 (shared with the access layer)
 
 LOG = logging.getLogger("hypocurate.pipeline")
 LOCK_TIMEOUT_MS = ACCESS_LOCK_TIMEOUT_MS
@@ -56,6 +57,7 @@ CODES = {
     "checks_done": "Checks have run: no record is stored after them",
     "checks_not_done": "no completed Checks result for this run",
     "checks_not_current": "the completed Checks result does not cover exactly the run's records and flags",
+    "set_flags_missing": "the completed Checks result lacks the flags a sensitivity set needs",
 }
 CONSTRUCTED_MARK = "constructed_test_data"
 
@@ -147,19 +149,36 @@ def flag_index(conn: Connection, run_id: int) -> list[tuple[int, str, str, tuple
 
 # --- Checks bound to the records it covered (step 6 review, finding 1) -----------------------
 
-def record_identity(version_fingerprint: str, origin: str, item_index: int) -> str:
-    """A record's stable identity: never its database id."""
-    return f"{version_fingerprint}|{origin}|{item_index}"
+CHECKS_DENIALS = ("checks_not_done", "checks_not_current")
 
 
-def binding(identities, flags) -> dict:
-    """What a completed Checks result covered: the exact record collection (by stable identity)
-    and the flags it raised (kind, category and the identities of their records)."""
-    ids = sorted(identities)
-    digest = hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
-    flag_lines = sorted(f"{k}|{c}|{','.join(sorted(r))}" for k, c, r in flags)
-    return {"records": len(ids), "identities": digest,
-            "flags": hashlib.sha256("\n".join(flag_lines).encode("utf-8")).hexdigest()}
+def inclusion_input(engine: Engine, run_id: int, role: str, function: str) -> dict:
+    """Inclusion's input, read in one transaction under the run's lock that also verifies the
+    completed Checks result covers exactly the records and flags read (re-check finding 1; the
+    `set_flags` reader). A refusal there becomes a logged pipeline refusal."""
+    from hypocurate.access.dispatch import bind_code
+    from hypocurate.access.errors import AccessDenied
+    from hypocurate.access.inputs import role_input
+    try:
+        return role_input(bind_code(engine, run_id, "inclusion"))
+    except AccessDenied as denied:
+        if denied.code not in CHECKS_DENIALS:
+            raise
+        code = denied.code
+    log_refusal(engine, run_id, role, function, code)
+    raise Refused(function, code)
+
+
+def decide_sets(engine: Engine, run_id: int, role: str, function: str, data: dict) -> dict:
+    """Every set's rules from Inclusion's input; a sensitivity set whose required own flags are
+    missing from the Checks result is a logged refusal, never "no flags" (re-check finding 1)."""
+    from hypocurate.pipeline import eligibility as el
+    try:
+        return el.all_sets(data["plan"]["content"], data["record_conditions"], data["flags_kind"], data["set_flags"])
+    except el.MissingSetFlags as missing:
+        message = str(missing)
+    log_refusal(engine, run_id, role, function, "set_flags_missing", message)
+    raise Refused(function, "set_flags_missing", message)
 
 
 def checks_binding(conn: Connection, run_id: int) -> dict | None:
diff --git a/tests/test_access_code_roles.py b/tests/test_access_code_roles.py
index ca4d57a..a062940 100644
--- a/tests/test_access_code_roles.py
+++ b/tests/test_access_code_roles.py
@@ -108,10 +108,32 @@ def test_an_agent_setting_cannot_bind_as_a_code_role(engine):
                                   "VALUES (:r, :o, :a)"), dict(r=world.run, o=role, a=setting))
 
 
+def completed_checks(engine, run_id):
+    """A completed Checks result covering the run's records and flags as they are (the world's
+    flags are planted by hand), so that Inclusion may read (re-check finding 1)."""
+    from hypocurate.pipeline import writes
+    with engine.begin() as conn:
+        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=run_id))
+        identity = {i: writes.record_identity(fp, key, ix) for i, fp, key, ix in conn.execute(text(
+            "SELECT r.id, sv.fingerprint, r.source_item_key, r.item_index FROM record r "
+            "JOIN source_version sv ON sv.id = r.source_version_id WHERE r.extraction_run_id = :r"), dict(r=run_id))}
+        flags = [(k, c, [identity[x] for x in (ids or []) if x in identity]) for k, c, ids in conn.execute(text(
+            "SELECT f.kind, f.category, array_agg(fr.record_id) FILTER (WHERE fr.record_id IS NOT NULL) FROM flag f "
+            "LEFT JOIN flag_record fr ON fr.flag_id = f.id WHERE f.run_id = :r GROUP BY f.id"), dict(r=run_id))]
+        writes.code_stage(conn, run_id, "checks", {}, {"binding": writes.binding(identity.values(), flags),
+                                                      "set_flags": {}})
+
+
 def test_inclusion_receives_no_outcome_value(engine):
     """The projected-data search over Inclusion's complete input finds none of the planted
-    outcome values; Checks' input (all values, by design) is the positive control."""
+    outcome values; Checks' input (all values, by design) is the positive control. Inclusion
+    reads only after a completed Checks result (re-check finding 1): before it, the read is
+    refused."""
     world = aw.build(engine, "curation")
+    with pytest.raises(AccessDenied) as denied:
+        role_input(bind_code(engine, world.run, "inclusion"))
+    assert denied.value.code == "checks_not_done"
+    completed_checks(engine, world.run)
     inclusion = role_input(bind_code(engine, world.run, "inclusion"))
     assert set(inclusion) == {"plan", "record_conditions", "flags_kind", "set_flags"}
     assert leaks(inclusion, aw.PLANTED.values()) == []
@@ -121,7 +143,7 @@ def test_inclusion_receives_no_outcome_value(engine):
     rows = [r for r in audit(engine, world.run) if r.role in CODE_ROLES and r.function != "bind"]
     assert {(r.role, r.function, r.allowed) for r in rows} == {
         ("inclusion", "plan", True), ("inclusion", "record_conditions", True), ("inclusion", "flags_kind", True),
-        ("inclusion", "set_flags", True),
+        ("inclusion", "set_flags", True), ("inclusion", "set_flags", False),
         ("checks", "plan", True), ("checks", "records_full", True)}
 
 
diff --git a/tests/test_sensitivity_matching.py b/tests/test_sensitivity_matching.py
index f38ec5a..b80823f 100644
--- a/tests/test_sensitivity_matching.py
+++ b/tests/test_sensitivity_matching.py
@@ -56,3 +56,61 @@ def test_the_one_change_rule_holds_with_recomputed_matching_flags(run):
     from test_reference_sets import _check_one_change
     differing = _check_one_change(run[2])
     assert differing["same_alloy_1_at_pct"] == 2
+
+
+# --- Re-check finding 1: reading inputs and verifying Checks in one transaction -------------------
+
+def _coarse_run(db, through="store"):
+    pw.registered_files(db, {
+        "mpea": pw.mpea_csv([pw.mpea_row("Co50.06Ni49.94", 10.0, 300.0), pw.mpea_row("Co50.06Ni49.94", 40.0, 250.0)]),
+        "controlled_duplicates": pw.mpea_csv([pw.mpea_row("Co50.04Ni49.96", 10.0, 300.0),
+                                              pw.mpea_row("Co50.04Ni49.96", 40.0, 250.0)])})
+    rid = pw.locked_run(db, sources=("mpea", "controlled_duplicates"), marked=True)
+    from hypocurate.pipeline import extract
+    extract.store_records(db, rid)
+    return rid
+
+
+def test_the_reviewers_interleaving_is_refused(db, monkeypatch):
+    """Inclusion reads before Checks has completed; Checks then commits (no primary flags, but
+    duplicate flags for the coarser same-alloy set); Inclusion's write follows. Inclusion must not
+    write decisions computed without those flags."""
+    from hypocurate.pipeline import checks, inclusion
+    from hypocurate.pipeline.writes import Refused
+    rid = _coarse_run(db)
+    original = inclusion.write
+
+    def checks_commit_between_read_and_write(*args, **kwargs):
+        checks.run_checks(db, rid)
+        return original(*args, **kwargs)
+
+    monkeypatch.setattr(inclusion, "write", checks_commit_between_read_and_write)
+    with pytest.raises(Refused) as refused:
+        inclusion.decide_run(db, rid)
+    assert refused.value.code == "checks_not_done"
+    with db.connect() as conn:
+        assert conn.execute(text("SELECT count(*) FROM run_record WHERE run_id = :r"), dict(r=rid)).scalar() == 0
+    # After the refusal, the normal order: Checks, then Inclusion with the set's own flags.
+    monkeypatch.undo()
+    checks.run_checks(db, rid)
+    sets = inclusion.decide_run(db, rid)
+    assert sum(r == "in_scope" for r in sets["same_alloy_1_at_pct"].values()) == 2
+
+
+def test_a_missing_required_per_set_flag_result_is_a_refusal(db):
+    """A completed Checks result that covers the records but lacks the flags a set needs (here the
+    coarser same-alloy set) is refused, never read as 'no flags'."""
+    from hypocurate.pipeline import inclusion, writes
+    from hypocurate.pipeline.writes import Refused
+    rid = _coarse_run(db)
+    with db.begin() as conn:
+        conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=rid))
+        identities = [writes.record_identity(fp, key, ix) for fp, key, ix in conn.execute(text(
+            "SELECT sv.fingerprint, r.source_item_key, r.item_index FROM record r "
+            "JOIN source_version sv ON sv.id = r.source_version_id WHERE r.extraction_run_id = :r"), dict(r=rid))]
+        writes.code_stage(conn, rid, "checks", {}, {"binding": writes.binding(identities, []), "set_flags": {}})
+    with pytest.raises(Refused) as refused:
+        inclusion.decide_run(db, rid)
+    assert refused.value.code == "set_flags_missing"
+    with db.connect() as conn:
+        assert conn.execute(text("SELECT count(*) FROM run_record WHERE run_id = :r"), dict(r=rid)).scalar() == 0
````

### `8ec5c63 Step 6 re-check fix: the freeze checks the primary set against the invariants`

````diff
8ec5c63330bfb0ec6dcdf6449c27e769abd0ee17

Step 6 re-check fix: the freeze checks the primary set against the invariants

Owner, 2026-10-06: at the freeze, the primary set itself is verified against
every item of primary_set_invariants (no exact duplicate twice, no conflict
pair, no invalid value, no unresolved-identity group, no model-recalled
record, no constructed record in an unmarked run), using the Checks flags,
which no longer depend on the plan's grouping or outcome, and the records'
kind and source. A failure refuses the freeze and is logged. The new tests
(each invariant on the checker; end-to-end plans built to slip past
validation, including the reviewer's grouping and outcome cases) failed on
the code before this change.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 5668454..8d17c75 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -4643,7 +4643,7 @@
     "key": "primary_set_invariants",
     "name": "What no plan can ever do to the primary set",
     "state": "in_force",
-    "statement": "These hold for every plan, including any plan written by a model; no plan setting can change them. (1) An exact duplicate is never counted twice: one record of the group, chosen by the survivor rule, enters. (2) Both records of a conflict never enter: neither enters (the default), or the plan may choose the survivor's value counted once. (3) A physically invalid value never enters. (4) A group whose identity cannot be resolved (several candidates) never enters; it is counted separately only in the sensitivity analysis 'possible_duplicates_separate'. (5) A model-recalled record never enters. (6) A constructed record (the controlled extract) never enters a run that is not marked as a test. A plan that tries (1) to (4) is refused at the rules lock and refused again when its rules are applied; (5) is refused by the database; (6) by code at record storage, inclusion and the freeze. The only plan choices that remain: conflicts as in (2), and possible duplicates counted once (the default) or both counted.",
+    "statement": "These hold for every plan, including any plan written by a model; no plan setting can change them. (1) An exact duplicate is never counted twice: one record of the group, chosen by the survivor rule, enters. (2) Both records of a conflict never enter: neither enters (the default), or the plan may choose the survivor's value counted once. (3) A physically invalid value never enters. (4) A group whose identity cannot be resolved (several candidates) never enters; it is counted separately only in the sensitivity analysis 'possible_duplicates_separate'. (5) A model-recalled record never enters. (6) A constructed record (the controlled extract) never enters a run that is not marked as a test. A plan that tries (1) to (4) is refused at the rules lock and refused again when its rules are applied; (5) is refused by the database; (6) by code at record storage, inclusion and the freeze. The only plan choices that remain: conflicts as in (2), and possible duplicates counted once (the default) or both counted. They are also enforced on the frozen set itself: at the dataset freeze, code checks the primary set against each of (1) to (6), using the Checks flags (paper identity and physical validity computed independently of the plan's grouping and outcome) and each record's kind and source, and refuses the freeze, logging the refusal, if any fails.",
     "value": {
       "text": "six things no plan can do",
       "unit": null
@@ -4678,23 +4678,41 @@
         },
         {
           "ref": "python:hypocurate.pipeline.writes:constructed_unmarked"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:primary_set_problems"
         }
       ],
-      "note": "Tests per point: (1) test_no_plan_can_put_these_records_in_the_primary_set[exact_duplicate…], test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule; (2) test_a_conflict_enters_with_neither_record, test_no_plan_can_put_these_records_in_the_primary_set[values_disagree…]; (3) test_each_rule_on_its_own, test_no_plan_can_put_these_records_in_the_primary_set[invalid_value…]; (4) test_an_ambiguous_group_enters_with_none_of_its_records, test_no_plan_can_put_these_records_in_the_primary_set[possible_duplicate…]; (5) test_a_model_recalled_record_is_stored_but_never_eligible, test_each_rule_on_its_own; (6) test_constructed_data_never_enters_a_run_not_marked_as_a_test. Plan refusals: test_invalid_plans_are_refused."
+      "note": "Tests per point: (1) test_no_plan_can_put_these_records_in_the_primary_set[exact_duplicate…], test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule; (2) test_a_conflict_enters_with_neither_record, test_no_plan_can_put_these_records_in_the_primary_set[values_disagree…]; (3) test_each_rule_on_its_own, test_no_plan_can_put_these_records_in_the_primary_set[invalid_value…]; (4) test_an_ambiguous_group_enters_with_none_of_its_records, test_no_plan_can_put_these_records_in_the_primary_set[possible_duplicate…]; (5) test_a_model_recalled_record_is_stored_but_never_eligible, test_each_rule_on_its_own; (6) test_constructed_data_never_enters_a_run_not_marked_as_a_test. Plan refusals: test_invalid_plans_are_refused. The result check at the freeze: test_each_invariant_is_checked_on_the_primary_set (all six) and the end-to-end tests in tests/test_freeze_invariants.py."
     },
-    "history": [],
+    "history": [
+      {
+        "value": "These hold for every plan, including any plan written by a model; no plan setting can change them. (1) An exact duplicate is never counted twice: one record of the group, chosen by the survivor rule, enters. (2) Both records of a conflict never enter: neither enters (the default), or the plan may choose the survivor's value counted once. (3) A physically invalid value never enters. (4) A group whose identity cannot be resolved (several candidates) never enters; it is counted separately only in the sensitivity analysis 'possible_duplicates_separate'. (5) A model-recalled record never enters. (6) A constructed record (the controlled extract) never enters a run that is not marked as a test. A plan that tries (1) to (4) is refused at the rules lock and refused again when its rules are applied; (5) is refused by the database; (6) by code at record storage, inclusion and the freeze. The only plan choices that remain: conflicts as in (2), and possible duplicates counted once (the default) or both counted.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Before the re-check: enforced on the settings only."
+      }
+    ],
     "notes": [
       "Shown on the assumptions page like every entry."
     ],
     "tests": [
-      "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set",
-      "tests/test_eligibility.py::test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule",
+      "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
+      "tests/test_data_model.py::test_a_model_recalled_record_is_stored_but_never_eligible",
       "tests/test_eligibility.py::test_a_conflict_enters_with_neither_record",
-      "tests/test_eligibility.py::test_each_rule_on_its_own",
       "tests/test_eligibility.py::test_an_ambiguous_group_enters_with_none_of_its_records",
+      "tests/test_eligibility.py::test_each_rule_on_its_own",
+      "tests/test_eligibility.py::test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule",
+      "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set",
       "tests/test_eligibility.py::test_the_fixed_rules_hold_in_every_set_the_plan_names",
-      "tests/test_data_model.py::test_a_model_recalled_record_is_stored_but_never_eligible",
-      "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
+      "tests/test_freeze_invariants.py::test_a_constructed_record_in_an_unmarked_run_is_refused_at_the_freeze",
+      "tests/test_freeze_invariants.py::test_an_exact_duplicate_counted_twice_is_refused_at_the_freeze",
+      "tests/test_freeze_invariants.py::test_an_invalid_value_is_refused_at_the_freeze",
+      "tests/test_freeze_invariants.py::test_an_unresolved_identity_group_is_refused_at_the_freeze",
+      "tests/test_freeze_invariants.py::test_both_records_of_a_conflict_are_refused_at_the_freeze",
+      "tests/test_freeze_invariants.py::test_each_invariant_is_checked_on_the_primary_set",
+      "tests/test_freeze_invariants.py::test_the_reviewers_grouping_case_is_refused_at_the_freeze",
+      "tests/test_freeze_invariants.py::test_the_reviewers_outcome_case_is_refused_at_the_freeze",
       "tests/test_plan.py::test_invalid_plans_are_refused",
       "tests/test_plan.py::test_the_plan_choices_that_remain"
     ]
diff --git a/hypocurate/pipeline/checkpoints.py b/hypocurate/pipeline/checkpoints.py
index 926e07e..e5f53fa 100644
--- a/hypocurate/pipeline/checkpoints.py
+++ b/hypocurate/pipeline/checkpoints.py
@@ -33,7 +33,8 @@ from hypocurate.access.dispatch import bind_code
 from hypocurate.access.inputs import role_input
 from hypocurate.pipeline import eligibility as el
 from hypocurate.pipeline.plan import PlanError, canonical, fingerprint, tags_for, validate
-from hypocurate.pipeline.writes import (Refused, code_stage, constructed_unmarked, decide_sets, flag_index,
+from hypocurate.pipeline.writes import (CONSTRUCTED_MARK, Refused, code_stage, constructed_unmarked, decide_sets,
+                                        flag_index,
                                         inclusion_input, log_refusal,
                                         record_identity, record_ids, require_checks_cover, run_record_sources,
                                         write)
@@ -131,6 +132,12 @@ def freeze_dataset(engine: Engine, run_id: int) -> dict:
         if record_ids(conn, run_id) != read_ids or flag_index(conn, run_id) != read_flags:
             raise Refused("freeze_dataset", "changed_since_read")
         require_checks_cover(conn, run_id, "freeze_dataset", identity_of, [(k, c, r) for _, k, c, r in read_flags])
+        # The result check (owner, 2026-10-06): the primary set itself against every invariant.
+        run_flags = conn.execute(text("SELECT experiment_flags FROM run WHERE id = :r"), dict(r=run_id)).scalar_one()
+        broken = el.primary_set_problems(set(members[el.PRIMARY]), by_id, flags,
+                                         isinstance(run_flags, dict) and run_flags.get(CONSTRUCTED_MARK) is True)
+        if broken:
+            raise Refused("freeze_dataset", "invariant_broken", "; ".join(broken))
         stored = dict(conn.execute(text("SELECT record_id, rule FROM run_record WHERE run_id = :r"),
                                    dict(r=run_id)).all())
         if stored != sets[el.PRIMARY] or _set_records(conn, run_id) != members:
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index 1408d42..9fa3cbe 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -341,6 +341,35 @@ def flags_for(key: str, flags: list[Mapping], set_flags: Mapping[str, list] | No
     return [f for f in flags if f["kind"] == "invalid_value"] + own
 
 
+def primary_set_problems(members: set, records: Mapping[int, Mapping], flags: Iterable[Mapping],
+                         marked: bool) -> list[str]:
+    """The result check of the freeze (owner, 2026-10-06; register 'primary_set_invariants'): what
+    in the primary set itself breaks an invariant, whatever the plan said. `flags` are the Checks
+    flags (identity and validity independent of the plan's grouping and outcome); `records` gives
+    each member's kind and source; `marked` is the run's test mark. Empty if nothing."""
+    from hypocurate.sources.versions import SOURCES
+    out = []
+    for f in flags:
+        inside = sorted(i for i in f["records"] if i in members)
+        if f["kind"] == "exact_duplicate" and len(inside) > 1:
+            out.append(f"an exact duplicate counted twice: records {inside}")
+        elif f["kind"] == "values_disagree" and len(inside) > 1:
+            out.append(f"both records of a conflict: records {inside}")
+        elif f["kind"] == "invalid_value" and inside:
+            out.append(f"an invalid value: records {inside}")
+        elif f["kind"] == "possible_duplicate" and f["category"] == "several candidates" and inside:
+            out.append(f"a group of unresolved identity: records {inside}")
+    recalled = sorted(i for i in members if records[i]["kind"] == "model_recalled")
+    if recalled:
+        out.append(f"model-recalled records: {recalled}")
+    # Its own test of the source definition, so that switching off the earlier guard does not
+    # switch off this check.
+    constructed = sorted(i for i in members if getattr(SOURCES.get(records[i]["source"]), "constructed", False))
+    if constructed and not marked:
+        out.append(f"constructed records in a run not marked as a test: {constructed}")
+    return out
+
+
 def all_sets(plan: Mapping[str, Any], records: list[Mapping], flags: list[Mapping],
              set_flags: Mapping[str, list] | None = None) -> dict[str, dict[int, str]]:
     """The primary set and every sensitivity set the plan names, each with its own flags."""
diff --git a/hypocurate/pipeline/writes.py b/hypocurate/pipeline/writes.py
index 140127e..a00bfd4 100644
--- a/hypocurate/pipeline/writes.py
+++ b/hypocurate/pipeline/writes.py
@@ -58,6 +58,7 @@ CODES = {
     "checks_not_done": "no completed Checks result for this run",
     "checks_not_current": "the completed Checks result does not cover exactly the run's records and flags",
     "set_flags_missing": "the completed Checks result lacks the flags a sensitivity set needs",
+    "invariant_broken": "the primary set breaks a rule no plan can change (register 'primary_set_invariants')",
 }
 CONSTRUCTED_MARK = "constructed_test_data"
 
diff --git a/tests/test_freeze_invariants.py b/tests/test_freeze_invariants.py
new file mode 100644
index 0000000..9c9bd63
--- /dev/null
+++ b/tests/test_freeze_invariants.py
@@ -0,0 +1,179 @@
+"""Re-check, the owner's addition (2026-10-06): the freeze verifies the primary set itself against
+every item of register entry 'primary_set_invariants', using the Checks flags (identity and
+validity computed independently of the plan's grouping and outcome settings) and the records'
+kind and source:
+- no two members form an exact duplicate pair;
+- no two members form a conflict pair;
+- no member carries an invalid-value flag;
+- no member belongs to an unresolved-identity group;
+- no member is model-recalled;
+- no member comes from a constructed source in a run not marked as a test.
+A freeze that fails any of them is refused and logged.
+
+Each end-to-end case uses a plan deliberately built to slip past settings validation: the
+guards are switched off for the test (a simulated gap), so only the check on the result can
+stop it. That includes the reviewer's two cases (grouping by dataset; another outcome)."""
+from __future__ import annotations
+
+import copy
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+from hypocurate.pipeline import checkpoints, checks, eligibility, extract, inclusion, plan as plan_module, writes
+from hypocurate.pipeline.plan import reference_plan
+from hypocurate.pipeline.writes import Refused
+
+
+# --- the check itself, item by item ---------------------------------------------------------------
+
+def rec(i, source="mpea", kind="measured"):
+    return {"id": i, "source": source, "kind": kind}
+
+
+def problems(members, flags=(), records=None, marked=False):
+    records = records or {i: rec(i) for i in members}
+    return eligibility.primary_set_problems(set(members), records, list(flags), marked)
+
+
+def flag(kind, category, *ids):
+    return {"id": 1, "kind": kind, "category": category, "records": list(ids)}
+
+
+@pytest.mark.parametrize("case, members, flags, records, marked, expected", [
+    ("exact duplicate counted twice", {1, 2}, [flag("exact_duplicate", "identical values", 1, 2)], None, False,
+     "exact duplicate"),
+    ("both records of a conflict", {1, 2}, [flag("values_disagree", "differ beyond tolerance", 1, 2)], None, False,
+     "conflict"),
+    ("an invalid value", {1}, [flag("invalid_value", "physically impossible", 1)], None, False, "invalid value"),
+    ("an unresolved-identity group", {1}, [flag("possible_duplicate", "several candidates", 1, 2, 3)], None, False,
+     "unresolved identity"),
+    ("a model-recalled record", {1}, [], {1: rec(1, kind="model_recalled")}, False, "model-recalled"),
+    ("a constructed record in an unmarked run", {1}, [], {1: rec(1, source="controlled_duplicates")}, False,
+     "constructed"),
+])
+def test_each_invariant_is_checked_on_the_primary_set(case, members, flags, records, marked, expected):
+    got = problems(members, flags, records, marked)
+    assert len(got) == 1 and expected in got[0], (case, got)
+
+
+def test_what_the_invariants_allow():
+    """One survivor of a duplicate; one record of a conflict counted by the survivor rule is not in
+    primary by default, but a plan may choose it; possible duplicates; a constructed record in a
+    marked run."""
+    assert problems({1, 3}, [flag("exact_duplicate", "identical values", 1, 2)]) == []
+    assert problems({1}, [flag("values_disagree", "differ beyond tolerance", 1, 2)]) == []
+    assert problems({1, 2}, [flag("possible_duplicate", "identical values", 1, 2)]) == []
+    assert problems({1}, [], {1: rec(1, source="controlled_duplicates")}, marked=True) == []
+
+
+# --- end to end: plans that slip past settings validation ------------------------------------------
+
+@pytest.fixture
+def no_guard(monkeypatch):
+    """Switches off the settings guards (validation and application time), as a gap would."""
+    monkeypatch.setattr(eligibility, "fixed_rule_problems", lambda rules: [])
+    monkeypatch.setattr(plan_module, "fixed_rule_problems", lambda rules: [])
+    monkeypatch.setattr(plan_module, "SUPPORTED_OUTCOMES", ("yield_strength", "ultimate_tensile_strength"))
+
+
+def _rule(content, kind, category, rule):
+    for e in content["eligibility_rules"]:
+        if e["flag_kind"] == kind and e.get("category") == category:
+            e["rule"] = rule
+    return content
+
+
+def _through_decisions(db, sources, content, marked=True):
+    rid = pw.dispatched_run(db, sources=sources, marked=marked)
+    content["hypothesis_version"] = pw.version_of(db, rid)
+    checkpoints.lock_rules(db, rid, content)
+    extract.store_records(db, rid)
+    checks.run_checks(db, rid)
+    inclusion.decide_run(db, rid)
+    return rid
+
+
+def _refused(db, rid, expected):
+    with pytest.raises(Refused) as refused:
+        checkpoints.freeze_dataset(db, rid)
+    assert refused.value.code == "invariant_broken" and expected in refused.value.message
+    with db.connect() as conn:
+        assert conn.execute(text("SELECT count(*) FROM run_snapshot WHERE run_id = :r"), dict(r=rid)).scalar() == 0
+        row = conn.execute(text("SELECT role, function, detail FROM audit_log WHERE run_id = :r "
+                                "AND detail->>'result' = 'rejected' ORDER BY id DESC LIMIT 1"), dict(r=rid)).one()
+    assert (row.role, row.function, row.detail["code"]) == ("checkpoint", "freeze_dataset", "invariant_broken")
+
+
+def _extract_run(db):
+    pw.registered(db, ("mpea", "controlled_duplicates"))
+    return reference_plan(0)
+
+
+def test_an_exact_duplicate_counted_twice_is_refused_at_the_freeze(db, no_guard):
+    content = _rule(_extract_run(db), "exact_duplicate", None, "in_scope")
+    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "exact duplicate")
+
+
+def test_both_records_of_a_conflict_are_refused_at_the_freeze(db, no_guard):
+    content = _rule(_extract_run(db), "values_disagree", None, "in_scope")
+    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "conflict")
+
+
+def test_the_reviewers_grouping_case_is_refused_at_the_freeze(db, no_guard):
+    """MPEA grouped by dataset, the extract by paper, and the plan admitting exact duplicates: the
+    duplicates are still known (Checks' paper identity ignores grouping) and the freeze refuses."""
+    content = _extract_run(db)
+    content["rules"]["grouping"] = [{"source": "mpea", "unit": "dataset"}, {"source": "tamu_fcc", "unit": "dataset"},
+                                    {"source": "controlled_duplicates", "unit": "paper"}]
+    _rule(content, "exact_duplicate", None, "in_scope")
+    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "exact duplicate")
+
+
+def _invalid_sources(db):
+    pw.registered_files(db, {
+        "mpea": pw.mpea_csv([{**pw.mpea_row("Co50Ni50", 10.0, 400.0), "PROPERTY: UTS (MPa)": "399"},
+                             pw.mpea_row("Co50Ni50", 40.0, 300.0)]),
+        "controlled_duplicates": pw.mpea_csv([pw.mpea_row("Co60Ni40", 10.0, 300.0, doi="10.5555/other")])})
+
+
+def test_an_invalid_value_is_refused_at_the_freeze(db, no_guard):
+    _invalid_sources(db)
+    content = _rule(reference_plan(0), "invalid_value", None, "in_scope")
+    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "invalid value")
+
+
+def test_the_reviewers_outcome_case_is_refused_at_the_freeze(db, no_guard):
+    """Tensile strength as the outcome and invalid values admitted: Checks still flags tensile
+    strength 399 below yield strength 400 (independent of the outcome) and the freeze refuses."""
+    _invalid_sources(db)
+    content = _rule(reference_plan(0), "invalid_value", None, "in_scope")
+    content["variables"]["outcome"] = {"field": "ultimate_tensile_strength", "unit": "MPa"}
+    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "invalid value")
+
+
+def test_an_unresolved_identity_group_is_refused_at_the_freeze(db, no_guard):
+    """One MPEA record with two candidates in the extract: an ambiguous group admitted by the plan."""
+    pw.registered_files(db, {
+        "mpea": pw.mpea_csv([pw.mpea_row("Co50Ni50", 10.0, 300.0), pw.mpea_row("Co50Ni50", 40.0, 250.0)]),
+        "controlled_duplicates": pw.mpea_csv([pw.mpea_row("Co50Ni50", 10.0, 300.0),
+                                              pw.mpea_row("Co50Ni50", 10.1, 300.0)])})
+    content = _rule(reference_plan(0), "possible_duplicate", "several candidates", "in_scope")
+    _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "unresolved identity")
+
+
+def test_a_constructed_record_in_an_unmarked_run_is_refused_at_the_freeze(db, monkeypatch):
+    """The storage, inclusion and freeze guards switched off: the check on the result still finds
+    the constructed records in a run not marked as a test."""
+    for module in (extract, inclusion, checkpoints):
+        monkeypatch.setattr(module, "constructed_unmarked", lambda conn, run_id, keys: False)
+    rid = _through_decisions(db, ("mpea", "controlled_duplicates"), _extract_run(db), marked=False)
+    _refused(db, rid, "constructed")
+
+
+def test_a_valid_plan_freezes(db):
+    """The reference plan on MPEA and the extract (marked) passes the check."""
+    content = _extract_run(db)
+    rid = _through_decisions(db, ("mpea", "controlled_duplicates"), content)
+    assert checkpoints.freeze_dataset(db, rid)["frozen"] is True
````

### `b2470bc Step 6 re-check fix: test that Inclusion's read itself verifies Checks`

````diff
b2470bc84c7fac7ba776115c29f348a1128269e5

Step 6 re-check fix: test that Inclusion's read itself verifies Checks

Found by the mutation checks: removing the coverage comparison from the
set_flags read passed every test, because the write transaction's check
refuses the same cases. The new test adds a record after Checks and expects
the read itself to be refused (checks_not_current).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index 8d17c75..e6ce1db 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -4778,6 +4778,7 @@
       "tests/test_checkpoints.py::test_no_record_is_stored_after_checks",
       "tests/test_checkpoints.py::test_skipping_checks_is_refused_at_inclusion_and_the_freeze",
       "tests/test_sensitivity_matching.py::test_a_missing_required_per_set_flag_result_is_a_refusal",
+      "tests/test_sensitivity_matching.py::test_the_read_itself_refuses_a_checks_result_that_does_not_cover_the_records",
       "tests/test_sensitivity_matching.py::test_the_reviewers_interleaving_is_refused"
     ]
   },
diff --git a/tests/test_sensitivity_matching.py b/tests/test_sensitivity_matching.py
index b80823f..4c4d6ff 100644
--- a/tests/test_sensitivity_matching.py
+++ b/tests/test_sensitivity_matching.py
@@ -114,3 +114,22 @@ def test_a_missing_required_per_set_flag_result_is_a_refusal(db):
     assert refused.value.code == "set_flags_missing"
     with db.connect() as conn:
         assert conn.execute(text("SELECT count(*) FROM run_record WHERE run_id = :r"), dict(r=rid)).scalar() == 0
+
+
+def test_the_read_itself_refuses_a_checks_result_that_does_not_cover_the_records(db):
+    """Re-check finding 1: the verification is in the transaction that reads Inclusion's inputs,
+    not only in the later write. A record added after Checks makes the read itself refused."""
+    from hypocurate.access import AccessDenied, role_input
+    from hypocurate.access.dispatch import bind_code
+    from hypocurate.pipeline import checks
+    rid = _coarse_run(db)
+    checks.run_checks(db, rid)
+    role_input(bind_code(db, rid, "inclusion"))  # covered: the read succeeds
+    with db.begin() as conn:
+        conn.execute(text(
+            "INSERT INTO record (extraction_run_id, source_version_id, source_item_key, item_index, kind, alloy, harmonized, "
+            "reported, extraction) SELECT extraction_run_id, source_version_id, 'added-after-checks', 0, kind, alloy, "
+            "harmonized, reported, extraction FROM record WHERE extraction_run_id = :r LIMIT 1"), dict(r=rid))
+    with pytest.raises(AccessDenied) as denied:
+        role_input(bind_code(db, rid, "inclusion"))
+    assert denied.value.code == "checks_not_current"
````

## 4. Mutation checks of this round

**The re-check round (2026-10-06)**, nine mutations, each run alone (`PYTHONPATH`, the copy's import checked):

| Removed or changed in the copy (re-check fixes) | Failing tests |
|---|---|
| `set_flags` read without verifying the Checks coverage | 1 (after the new test; see below) |
| `set_flags` answers "no flags" without a Checks result | 2 |
| A missing per-set flag result read as "no flags" | 1 |
| The rule guard resolves the last entry, not the first | 35 |
| The guard as before the re-check (dict of entries, no duplicate refusal) | 3 |
| Paper identity ignores the reference text | 3 |
| Tensile-below-yield checked only for the yield-strength outcome | 7 |
| Validation accepts any outcome | 2 |
| The freeze skips the result check | 7 |

"`set_flags` read without verifying the Checks coverage" first survived: the write transaction's coverage check refused the same cases a moment later. `test_the_read_itself_refuses_a_checks_result_that_does_not_cover_the_records` now shows the read itself refusing.


Harness output (`mutate.py` of the first packet with this round's list):

````
set_flags read without verifying Checks: 5 passed in 11.50s  (imports the copy: True)
set_flags answers 'no flags' without a Checks result: 2 failed, 15 passed in 8.69s  (imports the copy: True)
a missing per-set flag result read as no flags: 1 failed, 4 passed in 3.49s  (imports the copy: True)
rule guard resolves the last entry, not the first: 35 failed, 14 passed in 1.41s  (imports the copy: True)
guard as before the re-check (dict of entries, no duplicate refusal): 3 failed, 46 passed in 0.50s  (imports the copy: True)
paper identity ignores the reference text: 3 failed, 18 passed in 0.36s  (imports the copy: True)
tensile-below-yield checked only for the yield-strength outcome: 7 failed, 14 passed in 0.42s  (imports the copy: True)
validation accepts any outcome: 2 failed, 33 passed in 0.37s  (imports the copy: True)
the freeze skips the result check: 7 failed, 8 passed in 16.24s  (imports the copy: True)
set_flags read without verifying Checks, after test_the_read_itself_refuses_a_checks_result_that_does_not_cover_the_records was added: 1 failed, 5 passed  (imports the copy: True)
````

## 5. Reference numbers recomputed after the fixes

The scripts of the first packet (section 13), run on the fixed code. Identical to the values before this round, for every set; the freeze fingerprint is unchanged too. Each "±" is one standard error (cluster-robust, by group), not a confidence interval.

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
888 passed in 226.25s                          (after the re-check fixes, 2026-10-06)
$ docker compose run --rm test                 (the test image, rebuilt)
888 passed in 234.14s
```

After the first review's fixes: 860 passed locally and in the image.

Before the review: 816 passed locally and in the image.

GitHub Actions, commit `b11e7c8` (the owner's decisions of 2026-10-06, last change to code, tests or data): success; "Run the suite in the test image": 816 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37354762927
Earlier: commit `8ccfd36` (first build), 815 passed, https://github.com/kelawady/hypocurate/actions/runs/37352154249

