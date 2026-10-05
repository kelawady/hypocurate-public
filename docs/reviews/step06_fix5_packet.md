# Build step 6 — fifth fix packet (the third confirmation's problem)

Date: 2026-10-06. Branch: `step-06-eligibility`. Covers only the problem the third confirmation (`docs/reviews/step06_confirm3_chatgpt.md`) found: commits after `b20d2d9` (the fourth fix packet) up to `4902175`. Generated from the files and commits on disk by a script. The full step is in `docs/reviews/step06_review_packet.md`, the earlier rounds in `docs/reviews/step06_fix_packet.md`, `step06_fix2_packet.md`, `step06_fix3_packet.md` and `step06_fix4_packet.md`, and the step summary (updated) in `docs/reviews/step06_summary.md`.

## How to use this packet

The owner's fixed rule: no record connected to a definite conflict enters the primary set under any plan; a survivor is allowed only in the sensitivity set `conflicts_survivor_value`. The owner asked for it to be enforced at validation, application and the freeze (which refused only more than one record); tests that fail on the code before, including the reviewer's case (exact chain A-B, conflict B-C, the conflict mapped to counted once) through the pipeline and at the freeze with the safeguards bypassed; confirmation that `conflicts_survivor_value` still works; the "by default" wording corrected; and a search for any other fixed rule enforced as "at most one" where the rule says "none". Section 1 has all of it. Please return a dated confirmation: for the problem, closed, partly closed or open, and any new finding.

## Contents

1. What was fixed (from the summary)
2. The third confirmation
3. The fixes, commit by commit (message and full diff)
4. Mutation checks of this round
5. Reference numbers recomputed after the fixes
6. Suite results

## Commits

```
2541871 Step 6: third confirmation review saved verbatim
b1e0080 Step 6 confirmation-3 fix: no record of a conflict-connected group enters primary
06d50de Step 6 summary: the third confirmation and its fix
4902175 Step 6 summary: mutation counts from the final run
```

## 1. What was fixed

## Third confirmation (ChatGPT, 2026-10-06) and fix

The text is in `docs/reviews/step06_confirm3_chatgpt.md`; the commits and diffs in `docs/reviews/step06_fix5_packet.md`. Confirmed fixed: A, B, C order dependence (144 id and order combinations, identical), the survivor choice, the freeze's verification of exact chains, the shared-function test of the chain. **Problem:** a plan could still map `values_disagree` to `duplicate_counted_once`. With an exact chain A-B touching a conflict B-C, A entered primary, B and C were counted-once copies, and neither the rule guard nor the freeze check objected (the freeze refused only more than one record of a conflict group). **The owner's rule is fixed: no record connected to a definite conflict enters the primary set under any plan. A survivor is allowed only in the sensitivity set `conflicts_survivor_value`.**

| Place | Fix | New or changed tests (failed before the fix) |
|---|---|---|
| Validation | `FLAG_RULE_CHOICES`: a conflict's only rule is `conflict_unresolved`. `plan.validate` refuses a plan mapping it to anything else at the lock, and `eligibility.settings` refuses it again. | `test_invalid_plans_are_refused` (new case: conflict → counted once); `test_no_plan_can_put_these_records_in_the_primary_set` (new case: conflict → counted once) |
| Application | Rule 7 no longer reads the plan's rule for conflicts. Every connected group (exact chains and conflict pairs) that touches a definite conflict is `conflict_unresolved` in every set. The one exception is `conflicts_survivor_value`, through the named setting `eligibility.conflict_survivor_allowed(key)`, which is true for that key only. That set's one change is now this setting, not a rewritten plan rule. | `tests/test_conflict_policy.py`: **the reviewer's chain**, with validation bypassed, in two shapes Checks can produce: "one paper" (the group A, B, C flagged as a conflict, with the exact pair A-B kept) and "only through B" (A-B exact, B-C conflict, A-C only possible; A reaches the conflict only through B). In primary none of A, B, C enters; in `conflicts_survivor_value` exactly one does; in every other set none does (2 cases). Through the pipeline on the controlled extract's real conflicting rows 7–8 (marked run, validation bypassed): both `conflict_unresolved` in primary, MPEA's survivor in `conflicts_survivor_value`, and the freeze succeeds. |
| Freeze check | `primary_set_problems` refuses **any** record of a group linked to a definite conflict, with the groups formed from Checks' flags (it refused only more than one). | `test_the_freeze_check_refuses_any_record_of_a_conflict_connected_group` (A alone, B alone, C alone, both shapes); `test_the_freeze_refuses_one_conflict_record_with_every_safeguard_bypassed` (the pipeline with validation **and** application bypassed: the MPEA record enters, the freeze refuses with `invariant_broken`, logged); `test_what_the_invariants_allow` (changed, below) |

**The reviewer's chain through the adapters:** as in the second confirmation, a three-source chain cannot arise through the sprint 1 adapters (Texas A&M reports no test temperature). It is tested on the shared functions (`raise_flags`, `set_flags`, `all_sets`, `primary_set_problems`). The pipeline tests use the real conflicting pair, rows 7–8. A chain whose middle record is not fully linked to the third is labelled "several candidates" by Checks and excluded already (`identity_unresolved`). That is why the "only through B" shape needs the A-C possible link.

**`conflicts_survivor_value` still works:** one survivor per conflict-connected group, by the survivor rule (`test_the_sensitivity_handling_is_the_answer_files` for rows 7–8, MPEA survives; the chain tests above). Every other rule is unchanged.

**Other fixed rules enforced as "at most one" where the rule says "none"** (looked for, as asked):
- **Conflicts:** the only case, in the freeze check and in the plan choice. Fixed above.
- **Exact duplicates:** "at most one per chain" is the rule itself ("counted once": one survivor enters). Correct as it is.
- **Already "none":**
  - invalid values: any member is refused;
  - unresolved-identity groups: any member;
  - model-recalled records: any member;
  - constructed records in an unmarked run: any member.
  The application of each is "none" too: rule 2, rule 7 `identity_unresolved`, rule 1, and the guard.
- **Possible duplicates:** a plan choice, not a fixed rule (counted once or both). Not affected.

**Wording corrected:**
- This summary: the first review's table, the second confirmation's description, the PRD correction 17.
- The register: `primary_set_invariants` point (2) and its "plan choices"; `conflicts_not_pooled`, which said "by default". Both now state the rule as fixed, with the earlier wording in their history.
- The code comments of `FLAG_RULE_CHOICES` and rule 7.

**Reference numbers and fingerprint after this fix: none changed; the freeze fingerprint is identical (`93c44b22…`).** The reference run raises no flags.


## 2. The third confirmation

````markdown
# Step 6 — second-model confirmation, round 3 (ChatGPT, 2026-10-06)

Confirmation review of `docs/reviews/step06_fix4_packet.md` (branch `step-06-eligibility`). Saved verbatim as the owner gave it. The owner's rule: no record connected to a definite conflict enters the primary set under any plan; a survivor is allowed only in the sensitivity set `conflicts_survivor_value` (see `docs/reviews/step06_summary.md`).

---

1. A, B, C order dependence — fixed. I tested all six ID assignments × all 24 input orders: 144 combinations, with identical decisions and memberships across every set, counts and freeze fingerprints. Resolving whole connected components removes the previous pair-order dependency.
2. Survivor choice — fixed. Selection uses DOI presence, the locked source priority, row number and stable source/origin/item identity. Database IDs affect internal component representation, but no longer determine the survivor. The outcome is deterministic for the same evidence and locked plan.
3. Conflict exclusion — not fixed to your stated requirement. A plan can still map values_disagree to duplicate_counted_once. For an exact chain A–B touching conflict B–C, I reproduced:
   - A admitted to primary;
   - B and C excluded as counted-once copies;
   - no objection from either the rule guard or freeze checker.
   Required correction: primary must always exclude the entire conflict-connected component. Permit a survivor only in conflicts_survivor_value. Enforce that at validation, application and freeze. The freeze currently rejects more than one member of a conflict component; your rule requires rejecting any member.
4. Freeze verification of exact chains — fixed. It reconstructs chains from Checks’ flags rather than trusting Inclusion’s survivor decisions. It retains the middle record when establishing connectivity even if that record is outside primary. Selecting A and C from A–B–C correctly fails. It shares the component-building helper with Inclusion, but independently checks membership. The separate conflict-policy defect is item 3.
5. Shared-function rather than full-pipeline chain test — fixed adequately for this scope. Exercising the actual matching, selection and fingerprint functions covers this algorithmic defect. The pipeline permutation tests separately cover storage and integration. Given the current adapters’ limitations, another end-to-end chain fixture is not a merge blocker.
New issues: none beyond the conflict-policy mismatch above.
I ran targeted reconstructed-code tests, not the reported 901-test database suite.
Not safe to merge.
````

## 3. The fixes, commit by commit

### `b1e0080 Step 6 confirmation-3 fix: no record of a conflict-connected group enters primary`

````diff
b1e0080f23a38217fcec3ac7185b75b28b701e0b

Step 6 confirmation-3 fix: no record of a conflict-connected group enters primary

The owner's fixed rule, enforced in three places:
- validation: a conflict's only rule is conflict_unresolved (FLAG_RULE_CHOICES);
- application: rule 7 excludes every group linked to a definite conflict in
  every set except conflicts_survivor_value (conflict_survivor_allowed);
- freeze: primary_set_problems refuses any record of such a group, not only
  more than one.
Register primary_set_invariants and conflicts_not_pooled state the rule as
fixed (earlier wording in their history). New tests/test_conflict_policy.py
(the reviewer's chain in two shapes; the real rows 7-8 through the pipeline
and at the freeze with every safeguard bypassed); changed tests listed in the
summary.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>


diff --git a/hypocurate/assumptions.json b/hypocurate/assumptions.json
index df4c851..0021e09 100644
--- a/hypocurate/assumptions.json
+++ b/hypocurate/assumptions.json
@@ -4240,7 +4240,7 @@
     "key": "conflicts_not_pooled",
     "name": "Conflicting reports are not pooled",
     "state": "in_force",
-    "statement": "When two sources report the same measurement with values beyond the tolerance, both records are kept and flagged, and both never enter the primary analysis together: this is a fixed rule, not a plan default. By default neither enters the primary analysis; the only other choice a plan has is the survivor's value counted once. The sensitivity analysis 'conflicts_survivor_value' counts the group once by the survivor rule.",
+    "statement": "When two sources report the same measurement with values beyond the tolerance, both records are kept and flagged, and neither enters the primary analysis: this is a fixed rule under every plan, not a default. No record connected to the conflict enters either, including one linked to it by exact duplicates. The survivor's value is counted only in the sensitivity analysis 'conflicts_survivor_value', which counts the group once by the survivor rule.",
     "value": {
       "text": "neither in primary; survivor value in a sensitivity analysis",
       "unit": null
@@ -4266,6 +4266,9 @@
       "settings": [
         {
           "ref": "python:hypocurate.pipeline.eligibility:decide"
+        },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:conflict_survivor_allowed"
         }
       ],
       "note": null
@@ -4276,12 +4279,21 @@
         "from": "2026-10-05",
         "to": "2026-10-06",
         "note": "Step 6 wording (decision C); made a fixed rule by the owner on 2026-10-06 (the override to 'both enter' removed)."
+      },
+      {
+        "value": "When two sources report the same measurement with values beyond the tolerance, both records are kept and flagged, and both never enter the primary analysis together: this is a fixed rule, not a plan default. By default neither enters the primary analysis; the only other choice a plan has is the survivor's value counted once. The sensitivity analysis 'conflicts_survivor_value' counts the group once by the survivor rule.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Wording after it was made a fixed rule (owner, 2026-10-06) and before the third confirmation: it still called the exclusion a default and left a plan the survivor's value."
       }
     ],
     "notes": [
-      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants')."
+      "A fixed rule, not a plan default (owner, 2026-10-06; entry 'primary_set_invariants').",
+      "Third confirmation (ChatGPT, 2026-10-06): a plan could still map conflicts to 'counted once' and admit one record of a conflict-connected group; the owner's rule is stricter (none, under any plan)."
     ],
     "tests": [
+      "tests/test_conflict_policy.py::test_a_plan_mapping_conflicts_to_counted_once_admits_neither_record",
+      "tests/test_conflict_policy.py::test_the_reviewers_chain_enters_primary_with_none_of_its_records",
       "tests/test_controlled_duplicates_handling.py::test_the_primary_handling_and_the_survivor_are_the_answer_files",
       "tests/test_controlled_duplicates_handling.py::test_the_sensitivity_handling_is_the_answer_files",
       "tests/test_eligibility.py::test_a_conflict_enters_with_neither_record",
@@ -4658,7 +4670,7 @@
     "key": "primary_set_invariants",
     "name": "What no plan can ever do to the primary set",
     "state": "in_force",
-    "statement": "These hold for every plan, including any plan written by a model; no plan setting can change them. (1) An exact duplicate is never counted twice: one record of the group, chosen by the survivor rule, enters. (2) Both records of a conflict never enter: neither enters (the default), or the plan may choose the survivor's value counted once. (3) A physically invalid value never enters. (4) A group whose identity cannot be resolved (several candidates) never enters; it is counted separately only in the sensitivity analysis 'possible_duplicates_separate'. (5) A model-recalled record never enters. (6) A constructed record (the controlled extract) never enters a run that is not marked as a test. A plan that tries (1) to (4) is refused at the rules lock and refused again when its rules are applied; (5) is refused by the database; (6) by code at record storage, inclusion and the freeze. The only plan choices that remain: conflicts as in (2), and possible duplicates counted once (the default) or both counted. They are also enforced on the frozen set itself: at the dataset freeze, code checks the primary set against each of (1) to (6), using the Checks flags (paper identity and physical validity computed independently of the plan's grouping and outcome) and each record's kind and source, and refuses the freeze, logging the refusal, if any fails.",
+    "statement": "These hold for every plan, including any plan written by a model; no plan setting can change them. (1) An exact duplicate is never counted twice: one record of the group, chosen by the survivor rule, enters. (2) No record connected to a definite conflict ever enters, under any plan: not both records, not one. That includes a record linked by exact duplicates to a record in conflict (the whole connected group stays out). A survivor's value is counted only in the sensitivity analysis 'conflicts_survivor_value'. (3) A physically invalid value never enters. (4) A group whose identity cannot be resolved (several candidates) never enters; it is counted separately only in the sensitivity analysis 'possible_duplicates_separate'. (5) A model-recalled record never enters. (6) A constructed record (the controlled extract) never enters a run that is not marked as a test. A plan that tries (1) to (4) is refused at the rules lock and refused again when its rules are applied; (5) is refused by the database; (6) by code at record storage, inclusion and the freeze. The one plan choice that remains: possible duplicates counted once (the default) or both counted. They are also enforced on the frozen set itself: at the dataset freeze, code checks the primary set against each of (1) to (6), using the Checks flags (paper identity and physical validity computed independently of the plan's grouping and outcome) and each record's kind and source, and refuses the freeze, logging the refusal, if any fails.",
     "value": {
       "text": "six things no plan can do",
       "unit": null
@@ -4688,6 +4700,9 @@
         {
           "ref": "python:hypocurate.pipeline.eligibility:fixed_rule_problems"
         },
+        {
+          "ref": "python:hypocurate.pipeline.eligibility:conflict_survivor_allowed"
+        },
         {
           "ref": "sql:a model-recalled record is never eligible"
         },
@@ -4698,7 +4713,7 @@
           "ref": "python:hypocurate.pipeline.eligibility:primary_set_problems"
         }
       ],
-      "note": "Tests per point: (1) test_no_plan_can_put_these_records_in_the_primary_set[exact_duplicate…], test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule; (2) test_a_conflict_enters_with_neither_record, test_no_plan_can_put_these_records_in_the_primary_set[values_disagree…]; (3) test_each_rule_on_its_own, test_no_plan_can_put_these_records_in_the_primary_set[invalid_value…]; (4) test_an_ambiguous_group_enters_with_none_of_its_records, test_no_plan_can_put_these_records_in_the_primary_set[possible_duplicate…]; (5) test_a_model_recalled_record_is_stored_but_never_eligible, test_each_rule_on_its_own; (6) test_constructed_data_never_enters_a_run_not_marked_as_a_test. Plan refusals: test_invalid_plans_are_refused. The result check at the freeze: test_each_invariant_is_checked_on_the_primary_set (all six) and the end-to-end tests in tests/test_freeze_invariants.py."
+      "note": "Tests per point: (1) test_no_plan_can_put_these_records_in_the_primary_set[exact_duplicate…], test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule; (2) test_a_conflict_enters_with_neither_record, test_no_plan_can_put_these_records_in_the_primary_set[values_disagree…], tests/test_conflict_policy.py (the reviewer's chain, through the pipeline and at the freeze); (3) test_each_rule_on_its_own, test_no_plan_can_put_these_records_in_the_primary_set[invalid_value…]; (4) test_an_ambiguous_group_enters_with_none_of_its_records, test_no_plan_can_put_these_records_in_the_primary_set[possible_duplicate…]; (5) test_a_model_recalled_record_is_stored_but_never_eligible, test_each_rule_on_its_own; (6) test_constructed_data_never_enters_a_run_not_marked_as_a_test. Plan refusals: test_invalid_plans_are_refused. The result check at the freeze: test_each_invariant_is_checked_on_the_primary_set (all six) and the end-to-end tests in tests/test_freeze_invariants.py."
     },
     "history": [
       {
@@ -4706,15 +4721,26 @@
         "from": "2026-10-06",
         "to": "2026-10-06",
         "note": "Before the re-check: enforced on the settings only."
+      },
+      {
+        "value": "These hold for every plan, including any plan written by a model; no plan setting can change them. (1) An exact duplicate is never counted twice: one record of the group, chosen by the survivor rule, enters. (2) Both records of a conflict never enter: neither enters (the default), or the plan may choose the survivor's value counted once. (3) A physically invalid value never enters. (4) A group whose identity cannot be resolved (several candidates) never enters; it is counted separately only in the sensitivity analysis 'possible_duplicates_separate'. (5) A model-recalled record never enters. (6) A constructed record (the controlled extract) never enters a run that is not marked as a test. A plan that tries (1) to (4) is refused at the rules lock and refused again when its rules are applied; (5) is refused by the database; (6) by code at record storage, inclusion and the freeze. The only plan choices that remain: conflicts as in (2), and possible duplicates counted once (the default) or both counted. They are also enforced on the frozen set itself: at the dataset freeze, code checks the primary set against each of (1) to (6), using the Checks flags (paper identity and physical validity computed independently of the plan's grouping and outcome) and each record's kind and source, and refuses the freeze, logging the refusal, if any fails.",
+        "from": "2026-10-06",
+        "to": "2026-10-06",
+        "note": "Before the third confirmation: point (2) let a plan choose the survivor's value counted once, and the freeze check refused only more than one record of a conflict group."
       }
     ],
     "notes": [
       "Shown on the assumptions page like every entry.",
       "Confirmation (2026-10-06): the freeze check sees every retained pairwise exact or conflict result (two-record flags inside mixed groups), not only group labels.",
-      "Confirmation round 2 (2026-10-06): the freeze check allows at most one record per chain of exact pairs, and per group linked by a definite conflict, forming the chains itself from Checks' flags."
+      "Confirmation round 2 (2026-10-06): the freeze check allows at most one record per chain of exact pairs, and per group linked by a definite conflict, forming the chains itself from Checks' flags.",
+      "Third confirmation (ChatGPT, 2026-10-06): a plan could still map conflicts to 'counted once' and admit one record of a conflict-connected group; the owner's rule is stricter (none, under any plan). Fixed at validation (FLAG_RULE_CHOICES), application (conflict_survivor_allowed) and the freeze (any record refused)."
     ],
     "tests": [
       "tests/test_checkpoints.py::test_constructed_data_never_enters_a_run_not_marked_as_a_test",
+      "tests/test_conflict_policy.py::test_a_plan_mapping_conflicts_to_counted_once_admits_neither_record",
+      "tests/test_conflict_policy.py::test_the_freeze_check_refuses_any_record_of_a_conflict_connected_group",
+      "tests/test_conflict_policy.py::test_the_freeze_refuses_one_conflict_record_with_every_safeguard_bypassed",
+      "tests/test_conflict_policy.py::test_the_reviewers_chain_enters_primary_with_none_of_its_records",
       "tests/test_data_model.py::test_a_model_recalled_record_is_stored_but_never_eligible",
       "tests/test_eligibility.py::test_a_conflict_enters_with_neither_record",
       "tests/test_eligibility.py::test_an_ambiguous_group_enters_with_none_of_its_records",
@@ -4722,11 +4748,11 @@
       "tests/test_eligibility.py::test_exact_and_possible_duplicates_are_counted_once_by_the_survivor_rule",
       "tests/test_eligibility.py::test_no_plan_can_put_these_records_in_the_primary_set",
       "tests/test_eligibility.py::test_the_fixed_rules_hold_in_every_set_the_plan_names",
+      "tests/test_freeze_invariants.py::test_a_conflict_admitted_past_every_guard_is_refused_at_the_freeze",
       "tests/test_freeze_invariants.py::test_a_constructed_record_in_an_unmarked_run_is_refused_at_the_freeze",
       "tests/test_freeze_invariants.py::test_an_exact_duplicate_counted_twice_is_refused_at_the_freeze",
       "tests/test_freeze_invariants.py::test_an_invalid_value_is_refused_at_the_freeze",
       "tests/test_freeze_invariants.py::test_an_unresolved_identity_group_is_refused_at_the_freeze",
-      "tests/test_freeze_invariants.py::test_both_records_of_a_conflict_are_refused_at_the_freeze",
       "tests/test_freeze_invariants.py::test_each_invariant_is_checked_on_the_primary_set",
       "tests/test_freeze_invariants.py::test_the_reviewers_grouping_case_is_refused_at_the_freeze",
       "tests/test_freeze_invariants.py::test_the_reviewers_outcome_case_is_refused_at_the_freeze",
diff --git a/hypocurate/pipeline/eligibility.py b/hypocurate/pipeline/eligibility.py
index 7b6ec6f..146a321 100644
--- a/hypocurate/pipeline/eligibility.py
+++ b/hypocurate/pipeline/eligibility.py
@@ -58,14 +58,16 @@ FLAG_STAGE_RULES = ("identity_unresolved", "conflict_unresolved", "duplicate_cou
 # flag means for the primary set. Every plan has exactly these eligibility-rule entries (flag kind,
 # category), with a rule from the allowed choices; validation refuses anything else, and so does
 # `settings` for a plan that bypassed validation. No plan, including one a model writes, can count
-# an exact duplicate twice, admit both records of a conflict, an invalid value or an unresolved-
-# identity group. The only plan choices: a conflict enters with neither record (the default) or
-# with the survivor's value counted once; a possible duplicate is counted once (the default) or
-# both records are counted.
+# an exact duplicate twice, admit any record connected to a definite conflict, an invalid value or
+# an unresolved-identity group. Conflicts are not a plan choice (third confirmation, owner
+# 2026-10-06): no record of a conflict-connected group enters primary; a survivor's value is
+# counted only in the sensitivity set 'conflicts_survivor_value' (`conflict_survivor_allowed`).
+# The one plan choice: a possible duplicate is counted once (the default) or both records are
+# counted.
 FLAG_RULE_CHOICES = {
     ("invalid_value", None): ("invalid_value",),
     ("exact_duplicate", None): ("duplicate_counted_once",),
-    ("values_disagree", None): ("conflict_unresolved", "duplicate_counted_once"),
+    ("values_disagree", None): ("conflict_unresolved",),
     ("possible_duplicate", "several candidates"): ("identity_unresolved",),
     ("possible_duplicate", None): ("duplicate_counted_once", "in_scope"),
 }
@@ -139,6 +141,13 @@ class Settings:
     survivor_order: tuple
     grouping: Mapping[str, str]
     scope_unconfirmed_ok: bool = False
+    conflict_survivor: bool = False  # only in 'conflicts_survivor_value' (`conflict_survivor_allowed`)
+
+
+def conflict_survivor_allowed(key: str) -> bool:
+    """The one place a conflict-connected group may keep a survivor (third confirmation, owner
+    2026-10-06): the sensitivity set 'conflicts_survivor_value', never primary, whatever the plan."""
+    return key == "conflicts_survivor_value"
 
 
 def settings(plan: Mapping[str, Any], key: str = PRIMARY) -> Settings:
@@ -156,7 +165,8 @@ def settings(plan: Mapping[str, Any], key: str = PRIMARY) -> Settings:
         exclusions=tuple(tuple(sorted(e.items(), key=lambda kv: kv[0])) for e in plan["exclusion_rules"]),
         flag_rules=flag_rules, decimals=r["same_alloy_decimals"], min_grain_sizes=r["min_grain_sizes"],
         survivor_order=tuple(r["survivor_source_order"]),
-        grouping={g["source"]: g["unit"] for g in r["grouping"]})
+        grouping={g["source"]: g["unit"] for g in r["grouping"]},
+        conflict_survivor=conflict_survivor_allowed(key))
     if key == PRIMARY:
         return base
     if key not in plan["sensitivity_analyses"]:
@@ -177,8 +187,7 @@ def settings(plan: Mapping[str, Any], key: str = PRIMARY) -> Settings:
         return replace(base, flag_rules=tuple((k, c, "in_scope" if k == "possible_duplicate" else rule)
                                               for k, c, rule in base.flag_rules))
     if key == "conflicts_survivor_value":
-        return replace(base, flag_rules=tuple((k, c, "duplicate_counted_once" if rule == "conflict_unresolved"
-                                               else rule) for k, c, rule in base.flag_rules))
+        return base  # its one change is `conflict_survivor`, set above
     raise KeyError(f"no change is defined for the analysis {key!r}")
 
 
@@ -340,9 +349,9 @@ def primary_set_problems(members: set, records: Mapping[int, Mapping], flags: It
     from hypocurate.sources.versions import SOURCES
     out = []
     flags = list(flags)
-    # At most one record per chain of exact pairs, and per group linked by a definite conflict
-    # (confirmation round 2): the chains are formed here from Checks' flags, independently of how
-    # Inclusion resolved them.
+    # At most one record per chain of exact pairs (confirmation round 2), and no record at all of a
+    # group linked to a definite conflict (third confirmation, owner 2026-10-06): the groups are
+    # formed here from Checks' flags, independently of how Inclusion resolved them.
     exact = [f["records"] for f in flags if f["kind"] == "exact_duplicate"]
     conflicting = {i for f in flags if f["kind"] == "values_disagree" for i in f["records"]}
     for group in components(exact):
@@ -351,8 +360,8 @@ def primary_set_problems(members: set, records: Mapping[int, Mapping], flags: It
             out.append(f"an exact duplicate counted twice: records {inside}")
     for group in components(exact + [f["records"] for f in flags if f["kind"] == "values_disagree"]):
         inside = sorted(i for i in group if i in members)
-        if set(group) & conflicting and len(inside) > 1:
-            out.append(f"both records of a conflict: records {inside}")
+        if set(group) & conflicting and inside:
+            out.append(f"a record connected to a conflict: records {inside}")
     for f in flags:
         inside = sorted(i for i in f["records"] if i in members)
         if f["kind"] == "invalid_value" and inside:
@@ -400,10 +409,11 @@ def _identity(records: Mapping[int, Mapping], flags: list[Mapping], rules: dict[
     the order of flags. In this order, each step a whole-group decision:
     1. unresolved identity: every pending record of an ambiguous group;
     2. definite relationships: records linked by a chain of exact-duplicate pairs are one
-       measurement, and a definite conflict links its records as well. A connected group that
-       touches a conflict follows the plan's conflict rule (neither: all its pending records are
-       `conflict_unresolved`; the survivor's value: one survivor); a group of exact duplicates
-       only keeps one survivor;
+       measurement, and a definite conflict links its records as well. In a connected group that
+       touches a conflict every pending record is `conflict_unresolved`, whatever the plan says
+       (third confirmation, owner 2026-10-06); only in 'conflicts_survivor_value'
+       (`st.conflict_survivor`) does it keep one survivor. A group of exact duplicates only keeps
+       one survivor;
     3. the plan's possible-duplicate choice on what remains: counted once, one survivor per
        connected possible group, or both counted.
     A survivor is chosen by the plan's survivor rule (`survivor_key`), whose last tie-break is the
@@ -416,13 +426,11 @@ def _identity(records: Mapping[int, Mapping], flags: list[Mapping], rules: dict[
             for i in pending(f["records"]):
                 rules[i] = "identity_unresolved"
     exact = [f["records"] for f in flags if f["kind"] == "exact_duplicate" and flag_rule(f, st) == "duplicate_counted_once"]
-    conflict = [f for f in flags if f["kind"] == "values_disagree"
-                and flag_rule(f, st) in ("conflict_unresolved", "duplicate_counted_once")]
-    in_conflict = {i: flag_rule(f, st) for f in conflict for i in f["records"]}
-    for group in components(exact + [f["records"] for f in conflict]):  # 2
+    conflict = [f["records"] for f in flags if f["kind"] == "values_disagree"]  # every one: not a plan choice
+    in_conflict = {i for c in conflict for i in c}
+    for group in components(exact + conflict):  # 2
         live = pending(group)
-        touched = sorted({in_conflict[i] for i in group if i in in_conflict})
-        if "conflict_unresolved" in touched:
+        if in_conflict & set(group) and not st.conflict_survivor:
             for i in live:
                 rules[i] = "conflict_unresolved"
         elif live:
diff --git a/tests/test_assumptions.py b/tests/test_assumptions.py
index 221dc9c..7da064f 100644
--- a/tests/test_assumptions.py
+++ b/tests/test_assumptions.py
@@ -255,7 +255,8 @@ def test_what_no_plan_can_do_to_the_primary_set_is_listed_in_one_entry():
     e = BY_KEY["primary_set_invariants"]
     s = e["statement"]
     for words in ("including any plan written by a model", "exact duplicate is never counted twice",
-                  "Both records of a conflict never enter", "physically invalid value never enters",
+                  "No record connected to a definite conflict ever enters, under any plan",
+                  "physically invalid value never enters",
                   "several candidates) never enters", "model-recalled record never enters",
                   "constructed record (the controlled extract) never enters a run that is not marked as a test"):
         assert words in s, words
diff --git a/tests/test_conflict_policy.py b/tests/test_conflict_policy.py
new file mode 100644
index 0000000..466db55
--- /dev/null
+++ b/tests/test_conflict_policy.py
@@ -0,0 +1,129 @@
+"""Third confirmation (ChatGPT, 2026-10-06), the owner's fixed rule: no record connected to a
+definite conflict enters the primary set, under any plan. A survivor is allowed only in the
+sensitivity set 'conflicts_survivor_value'. Enforced at validation (test_plan), at application
+and at the freeze.
+
+The reviewer's case: an exact chain A-B touching a conflict B-C, and a plan mapping conflicts to
+"counted once". Two shapes Checks can produce:
+- "one paper": A, B and C cite the same DOI and C reports the measurement 10% higher; Checks flags
+  the group A, B, C as a conflict and keeps the exact pair A-B;
+- "only through B": A and B cite the same DOI (A 404, B 400 MPa: exact), C has no DOI and B's
+  reference text (408.5 MPa: a conflict with B, 2.1%), and A-C is only a possible duplicate
+  (1.1%). The group is labelled possible duplicate; the exact pair A-B and the conflict pair B-C
+  are kept as their own flags; A is linked to the conflict only through B. (Without the A-C link
+  the group is not fully linked and Checks labels it "several candidates", excluded anyway.) Through the
+sprint 1 adapters a three-source chain cannot arise (Texas A&M reports no test temperature), so
+it is tested on the shared functions; the pipeline tests use the controlled extract's real
+conflicting rows 7-8 (MPEA row 1278 and its copy with yield strength x 1.3)."""
+from __future__ import annotations
+
+import copy
+
+import pytest
+from sqlalchemy import text
+
+import pipeline_world as pw
+from hypocurate.pipeline import checkpoints, checks, eligibility as el, extract, inclusion, plan as plan_module
+from hypocurate.pipeline.flags import raise_flags, set_flags
+from hypocurate.pipeline.plan import reference_plan
+from hypocurate.pipeline.writes import Refused
+from test_eligibility import PLAN, cond
+from test_flags import rec
+
+
+def survivor_plan(base):
+    plan = copy.deepcopy(base)
+    for e in plan["eligibility_rules"]:
+        if e["flag_kind"] == "values_disagree":
+            e["rule"] = "duplicate_counted_once"
+    return plan
+
+
+@pytest.fixture
+def no_validation(monkeypatch):
+    """Switches off the rule guards (validation and the check when rules are built)."""
+    monkeypatch.setattr(el, "fixed_rule_problems", lambda rules: [])
+    monkeypatch.setattr(plan_module, "fixed_rule_problems", lambda rules: [])
+
+
+SHAPES = {
+    "one paper": ((400.0, "10.1/d", "Reference X"), (400.0, "10.1/d", "Reference X"), (440.0, "10.1/d", "Reference X"),
+                  [("values_disagree", [1, 2, 3]), ("exact_duplicate", [1, 2])]),
+    "only through B": ((404.0, "10.1/d", "Reference X"), (400.0, "10.1/d", "Reference Y"), (408.5, None, "Reference Y"),
+                       [("possible_duplicate", [1, 2, 3]), ("exact_duplicate", [1, 2]), ("values_disagree", [2, 3])]),
+}
+
+
+def _chain(shape="only through B"):
+    (ya, da, ra), (yb, db, rb), (yc, dc, rc), expected = SHAPES[shape]
+    plan = survivor_plan(PLAN)
+    plan["rules"]["grouping"] = [{"source": "mpea", "unit": "paper"}, {"source": "tamu_fcc", "unit": "paper"},
+                                 {"source": "controlled_duplicates", "unit": "paper"}]
+    full = [rec(1, "mpea", ys=ya, doi=da, reference=ra), rec(2, "tamu_fcc", ys=yb, doi=db, reference=rb),
+            rec(3, "controlled_duplicates", ys=yc, doi=dc, reference=rc),
+            rec(4, "mpea", gs=40.0, ys=300.0, doi=da, reference=ra)]
+    flags = [{"id": n, "kind": f.kind, "category": f.category, "records": f.records}
+             for n, f in enumerate(raise_flags(plan, full), start=1)]
+    per_set = {k: [{"kind": f.kind, "category": f.category, "records": f.records} for f in fs]
+               for k, fs in set_flags(plan, full).items()}
+    records = [cond(1, "mpea"), cond(2, "tamu_fcc"), cond(3, "controlled_duplicates", doi=dc is not None),
+               cond(4, "mpea", gs=40.0)]
+    assert [(f["kind"], f["records"]) for f in flags] == expected
+    return plan, records, flags, per_set
+
+
+@pytest.mark.parametrize("shape", SHAPES)
+def test_the_reviewers_chain_enters_primary_with_none_of_its_records(no_validation, shape):
+    plan, records, flags, per_set = _chain(shape)
+    sets = el.all_sets(plan, records, flags, per_set)
+    assert {i: sets["primary"][i] for i in (1, 2, 3)} == {i: "conflict_unresolved" for i in (1, 2, 3)}
+    # The survivor is allowed only in the sensitivity set that names it.
+    assert sum(sets["conflicts_survivor_value"][i] == "in_scope" for i in (1, 2, 3)) == 1
+    for key, rules in sets.items():
+        if key != "conflicts_survivor_value":
+            assert all(rules[i] != "in_scope" for i in (1, 2, 3)), key
+
+
+@pytest.mark.parametrize("shape", SHAPES)
+def test_the_freeze_check_refuses_any_record_of_a_conflict_connected_group(no_validation, shape):
+    plan, records, flags, _ = _chain(shape)
+    recs = {r["id"]: r for r in records}
+    for member in (1, 2, 3):  # A alone (only exact-linked to the conflict), B alone, C alone
+        problems = el.primary_set_problems({member, 4}, recs, flags, True)
+        assert any("conflict" in p for p in problems), member
+    assert el.primary_set_problems({4}, recs, flags, True) == []
+
+
+# --- through the real pipeline: the controlled extract's conflicting rows 7-8 --------------------------
+
+def _decided(db, monkeypatch, bypass_application=False):
+    pw.registered(db, ("mpea", "controlled_duplicates"))
+    if bypass_application:  # a simulated gap in the application rule as well
+        monkeypatch.setattr(el, "conflict_survivor_allowed", lambda key: True, raising=False)
+    rid = pw.dispatched_run(db, sources=("mpea", "controlled_duplicates"), marked=True)
+    content = survivor_plan(reference_plan(pw.version_of(db, rid)))
+    checkpoints.lock_rules(db, rid, content)
+    extract.store_records(db, rid)
+    checks.run_checks(db, rid)
+    sets = inclusion.decide_run(db, rid)
+    with db.connect() as conn:
+        ids = dict(conn.execute(text("SELECT source_item_key, id FROM record WHERE extraction_run_id = :r AND "
+                                     "source_item_key IN ('MPEA_dataset.csv:row:1278', 'extract.csv:row:6')"),
+                                dict(r=rid)).all())
+    return rid, sets, ids["MPEA_dataset.csv:row:1278"], ids["extract.csv:row:6"]
+
+
+def test_a_plan_mapping_conflicts_to_counted_once_admits_neither_record(db, monkeypatch, no_validation):
+    rid, sets, mpea, copy_ = _decided(db, monkeypatch)
+    assert (sets["primary"][mpea], sets["primary"][copy_]) == ("conflict_unresolved", "conflict_unresolved")
+    assert (sets["conflicts_survivor_value"][mpea], sets["conflicts_survivor_value"][copy_]) == \
+        ("in_scope", "duplicate_counted_once")
+    assert checkpoints.freeze_dataset(db, rid)["frozen"] is True
+
+
+def test_the_freeze_refuses_one_conflict_record_with_every_safeguard_bypassed(db, monkeypatch, no_validation):
+    rid, sets, mpea, copy_ = _decided(db, monkeypatch, bypass_application=True)
+    assert sets["primary"][mpea] == "in_scope"  # the bypass let the survivor in
+    with pytest.raises(Refused) as refused:
+        checkpoints.freeze_dataset(db, rid)
+    assert refused.value.code == "invariant_broken" and "conflict" in refused.value.message
diff --git a/tests/test_eligibility.py b/tests/test_eligibility.py
index 64282eb..e14af31 100644
--- a/tests/test_eligibility.py
+++ b/tests/test_eligibility.py
@@ -304,13 +304,13 @@ def _changed(path, value):
     (("scope", "phase_class"), ["BCC"], pair(1, 10.0), [], 1, "in_scope", "out_of_scope"),
     (("exclusion_rules",), [{"rule": "grain_size_range", "min": 20.0}], pair(1, 10.0), [], 1, "in_scope",
      "excluded_by_rule"),
-    # Owner, 2026-10-06: for conflicts a plan may choose only between neither record (the default)
-    # and the survivor's value counted once. (Replaces the step 6 case that mapped a conflict to
-    # in_scope, which the owner removed.)
-    (("eligibility_rules",), [{**e, "rule": "duplicate_counted_once"} if e["flag_kind"] == "values_disagree" else e
-                              for e in PLAN["eligibility_rules"]],
+    # The one plan choice left (third confirmation, owner 2026-10-06): possible duplicates counted
+    # once (default) or both. (Replaces the case that chose the survivor's value for a conflict,
+    # which is no longer a plan choice.)
+    (("eligibility_rules",), [{**e, "rule": "in_scope"} if e["flag_kind"] == "possible_duplicate"
+                              and e.get("category") is None else e for e in PLAN["eligibility_rules"]],
      [*pair(1, 10.0), cond(3, "controlled_duplicates"), cond(4, "controlled_duplicates", gs=40.0)],
-     [flag("values_disagree", "differ beyond tolerance", 1, 3)], 1, "conflict_unresolved", "in_scope"),
+     [flag("possible_duplicate", "identical values", 1, 3)], 3, "duplicate_counted_once", "in_scope"),
     (("variables", "outcome", "field"), "hardness", pair(1, 10.0), [], 1, "in_scope", "missing_value"),
 ])
 def test_each_setting_is_read_from_the_locked_plan(path, value, records, flags, record, before, after):
@@ -323,6 +323,7 @@ def test_each_setting_is_read_from_the_locked_plan(path, value, records, flags,
 @pytest.mark.parametrize("kind, category, rule", [
     ("exact_duplicate", None, "in_scope"),  # an exact duplicate counted twice
     ("values_disagree", None, "in_scope"),  # both records of a conflict
+    ("values_disagree", None, "duplicate_counted_once"),  # one record of a conflict (third confirmation)
     ("invalid_value", None, "in_scope"),  # an invalid value
     ("possible_duplicate", "several candidates", "in_scope"),  # an unresolved-identity group
     ("possible_duplicate", "several candidates", "duplicate_counted_once"),
diff --git a/tests/test_freeze_invariants.py b/tests/test_freeze_invariants.py
index 9c9bd63..41f9d4a 100644
--- a/tests/test_freeze_invariants.py
+++ b/tests/test_freeze_invariants.py
@@ -3,7 +3,8 @@ every item of register entry 'primary_set_invariants', using the Checks flags (i
 validity computed independently of the plan's grouping and outcome settings) and the records'
 kind and source:
 - no two members form an exact duplicate pair;
-- no two members form a conflict pair;
+- no member is connected to a definite conflict (third confirmation, owner 2026-10-06: none, not
+  "at most one");
 - no member carries an invalid-value flag;
 - no member belongs to an unresolved-identity group;
 - no member is model-recalled;
@@ -63,7 +64,8 @@ def test_what_the_invariants_allow():
     primary by default, but a plan may choose it; possible duplicates; a constructed record in a
     marked run."""
     assert problems({1, 3}, [flag("exact_duplicate", "identical values", 1, 2)]) == []
-    assert problems({1}, [flag("values_disagree", "differ beyond tolerance", 1, 2)]) == []
+    # Third confirmation (owner, 2026-10-06): no record of a conflict-connected group, not even one.
+    assert problems({1}, [flag("values_disagree", "differ beyond tolerance", 1, 2)]) != []
     assert problems({1, 2}, [flag("possible_duplicate", "identical values", 1, 2)]) == []
     assert problems({1}, [], {1: rec(1, source="controlled_duplicates")}, marked=True) == []
 
@@ -116,7 +118,11 @@ def test_an_exact_duplicate_counted_twice_is_refused_at_the_freeze(db, no_guard)
     _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "exact duplicate")
 
 
-def test_both_records_of_a_conflict_are_refused_at_the_freeze(db, no_guard):
+def test_a_conflict_admitted_past_every_guard_is_refused_at_the_freeze(db, no_guard, monkeypatch):
+    """Third confirmation (owner, 2026-10-06): conflicts are no longer a plan rule, so the
+    application's own rule is bypassed as well (a survivor allowed in primary); the one conflict
+    record that then enters is refused at the freeze."""
+    monkeypatch.setattr(eligibility, "conflict_survivor_allowed", lambda key: True)
     content = _rule(_extract_run(db), "values_disagree", None, "in_scope")
     _refused(db, _through_decisions(db, ("mpea", "controlled_duplicates"), content), "conflict")
 
diff --git a/tests/test_plan.py b/tests/test_plan.py
index d4bc621..5aac794 100644
--- a/tests/test_plan.py
+++ b/tests/test_plan.py
@@ -84,9 +84,10 @@ def _set_rule(content, kind, category, rule):
 
 
 def test_the_plan_choices_that_remain():
-    """Conflicts: neither (default) or the survivor's value counted once. Possible duplicates:
-    counted once (default) or counted separately."""
-    for kind, rule in (("values_disagree", "duplicate_counted_once"), ("possible_duplicate", "in_scope")):
+    """The one choice left (third confirmation, owner 2026-10-06): possible duplicates counted once
+    (the default) or counted separately. Conflicts are no longer a choice: neither record, always;
+    the survivor's value only in the sensitivity set 'conflicts_survivor_value'."""
+    for kind, rule in (("possible_duplicate", "in_scope"),):
         content = default_plan(1)
         _set_rule(content, kind, None, rule)
         validate(content)
@@ -110,6 +111,8 @@ def test_the_plan_choices_that_remain():
     (lambda c: c["eligibility_rules"].append({"flag_kind": "values_disagree", "rule": "in_scope"}), "one eligibility"),
     # Owner, 2026-10-06: fixed rules a plan can never change (register 'primary_set_invariants').
     (lambda c: _set_rule(c, "values_disagree", None, "in_scope"), "fixed rule"),
+    # Third confirmation (owner, 2026-10-06): no record of a conflict enters primary, under any plan.
+    (lambda c: _set_rule(c, "values_disagree", None, "duplicate_counted_once"), "fixed rule"),
     (lambda c: _set_rule(c, "exact_duplicate", None, "in_scope"), "fixed rule"),
     (lambda c: _set_rule(c, "invalid_value", None, "in_scope"), "fixed rule"),
     (lambda c: _set_rule(c, "possible_duplicate", "several candidates", "in_scope"), "fixed rule"),
````

## 4. Mutation checks of this round

**The third confirmation round (2026-10-06)**, five mutations (run on `test_conflict_policy.py`, `test_plan.py`, `test_eligibility.py`, `test_freeze_invariants.py`; the fourth on `test_conflict_policy.py` and `test_controlled_duplicates_handling.py`; the fifth on `test_conflict_policy.py`):

| Removed or changed in the copy | Failing tests |
|---|---|
| Validation allows conflicts counted once again | 2 |
| The application lets primary keep a conflict survivor | 6 |
| The freeze check refuses only more than one conflict record | 5 |
| `conflicts_survivor_value` loses its survivor | 5 |
| Only records named by a conflict flag are excluded, not the exact-linked rest | 1 |

The fifth first survived: the chain fixture gave A, B and C one DOI, so A was in the conflict flag itself. The "only through B" shape (A linked to the conflict only through B) was added and catches it. The counts are from a final run of all five on the final tests.


Harness output (`mutate.py` of the first packet with this round's list):

````
validation allows conflicts counted once again: 2 failed, 107 passed in 23.42s  (imports the copy: True)
application lets primary keep a conflict survivor: 6 failed, 103 passed in 23.24s  (imports the copy: True)
the freeze check refuses only more than one conflict record: 5 failed, 104 passed in 23.66s  (imports the copy: True)
conflicts_survivor_value loses its survivor: 5 failed, 51 passed in 10.33s  (imports the copy: True)
only records named by a conflict flag are excluded, not the exact-linked rest: 1 failed, 5 passed in 7.49s  (imports the copy: True)
````

## 5. Reference numbers recomputed after the fixes

The scripts of the first packet (section 13), run on the fixed code. Identical to the values before this round (`diff` of the full output empty), for every set; the freeze fingerprint is unchanged too. Why: the reference run raises no flag, so no conflict rule acts on it (section 1). Each "±" is one standard error (cluster-robust, by group), not a confidence interval.

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
909 passed in 259.67s                          (after the third confirmation's fix, 2026-10-06)
$ docker compose run --rm test                 (the test image, rebuilt)
909 passed in 268.61s
```

After the second confirmation's fix: 901 passed locally and in the image; GitHub Actions on `b20d2d9`: success.

After the confirmation fixes: 896 passed locally and in the image; GitHub Actions on `8c9b062`: success (run 37374525357).

After the re-check fixes: 888 passed locally and in the image.

After the first review's fixes: 860 passed locally and in the image.

Before the review: 816 passed locally and in the image.

GitHub Actions, commit `b11e7c8` (the owner's decisions of 2026-10-06, last change to code, tests or data): success; "Run the suite in the test image": 816 passed; "Check the default image holds no tests, docs or answers": runtime image OK.
https://github.com/kelawady/hypocurate/actions/runs/37354762927
Earlier: commit `8ccfd36` (first build), 815 passed, https://github.com/kelawady/hypocurate/actions/runs/37352154249

