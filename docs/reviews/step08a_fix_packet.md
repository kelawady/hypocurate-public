# Build step 8a — fix packet (after ChatGPT's review)

Date: 2026-10-07. Branch `step-08a-curator`. The review was of `16261de`; the fixes are in `057732a` (code, tests, register, README and summary corrections). This packet was generated after them from the files on disk (script in section 10). **Not merged.**

ChatGPT's review (`step08a_review_chatgpt.md`): not safe to merge; six findings. The owner asked for each to be fixed with tests that fail on the reviewed code, plus the owner's term-check changes (a–h), the time zone fixed by setting the session to UTC (no guard change), the overclaims corrected, and a test of the request's headers.

## 1. What was fixed

| # | Finding | Fix | Tests (all fail on `16261de`, section 6) |
|---|---|---|---|
| 1 | An imported `curation.json` was not checked against the version it was attached to. | `sources/curated.check_curation`, called before a curation file is sealed into a version (`versions._register_in`, so registration and `seal-curation`) and before it is applied (`curated_values`). It checks the format, source and keys; the **base fingerprint**, computed from the version's own files without `curation.json` under its interpretation settings; for each entry, the target field, the value, the quote (found again in the named documentation file at word boundaries **on the stated line**) and the stated term, all under the current checks (`quotes.check`); and the acceptance fields (proposal and settings version are positive integers, the model is named, the acceptor's name is 1–200 characters and not blank, the acceptance time has a time zone, the note is absent or at most 2,000 characters). Anything else refuses the whole version. The register now says the **exact approved export replayed on the same base is the only trusted import**: no check can show that a person really accepted a value. | `test_curator.py`: `test_an_export_copied_onto_another_base_is_refused` (the reviewer's case), `test_an_export_that_does_not_check_out_is_refused` (23 cases: wrong fingerprint, blank label, other source, missing or non-documentation file, absent quote, quote starting inside a word, wrong line, wrong term, other value, value outside the vocabulary, blank, missing, untimed or unparsable acceptance, string, boolean or zero proposal, zero settings version, empty model, non-text note, malformed entry), `test_a_quote_that_fails_the_current_term_checks_is_refused_on_import`; control: `test_the_frozen_export_on_its_own_base_is_accepted` |
| 2 | The database did not check the term against the value; NULLs made the completeness CHECK UNKNOWN. | Migration 0005 (amended; never applied outside local and test databases). `ck_curator_proposal_proposed_complete` is now `status <> 'proposed' OR coalesce(<every part non-NULL> AND line >= 1 AND 30–600 characters AND hc_curator_term_ok(field, value, quote, term), false)`. `hc_curator_term_ok` checks the value's JSON type and vocabulary, that the term is a listed term **of that value** (of a part, for a microstructure, every part of which must have a term in the quote), the whole-word and case rules, the testing word, the excluded phrase, and for a temperature a complete number equal to the value with a Celsius unit. `hc_quote_occurs` (the trigger) finds the quote at word boundaries. A new `ck_curator_proposal_value_not_json_null` refuses JSON null as any proposal's value. The lists are copied into the migration and tested equal to the code's. | `test_migrations_step8a.py`: `test_a_value_that_does_not_match_its_term_is_refused` (12 cases, including the reviewer's: compression with the tensile quote and term "tensile"), `test_a_passed_proposal_with_a_missing_part_is_refused` (NULL line, term, quote, document, value; JSON null), `test_json_null_is_never_stored_as_a_value`, `test_a_quote_must_begin_and_end_at_a_word_boundary_in_the_document`, `test_the_databases_term_list_is_the_codes`, `test_the_database_and_the_code_agree_on_every_case` (32 cases; a quote the code passes is stored with the code's term; for one it refuses, every candidate term is refused) |
| 3 | A registration reservation read its total before the month-wide lock. | `spend.reserve` takes every lock first (the run's, then the month-wide one, in that order) and only then reads the run's or the invocation's total and the month's. | `test_agent_core.py`: `test_two_reservations_on_one_invocation_cannot_both_pass_the_curation_cap` ($1.70 + 2 × $0.20) and `…_a_lower_ceiling` ($0.30 + 2 × $0.15 under $0.50). Both are deterministic: a third connection holds the month-wide lock until `pg_locks` shows both reservations waiting. Before the fix both reservations passed. Regression guard (passes on both): `…_the_run_cap`. |
| 4 | A failed recording after a provider failure or a reply without usage escaped and was retried as malformed. | `RecordedEngine._record` finishes the call on every branch; any failure there ends the call with `recording_failed` (stop). The call stays `started`, counted at its maximum. A reservation that cannot be written now ends with a new code, `reservation_failed` (stop, nothing sent). Before the fix it too became "malformed" and was retried; the same class of defect, found while fixing 4. | `test_a_recording_failure_on_any_branch_stops_and_keeps_the_maximum` (provider failure, unreadable reply, the engine's own no-usage branch, success: one request, the call started, the month total at its maximum), `test_a_reservation_that_cannot_be_written_sends_nothing` |
| 5 | The number check matched other temperatures; term matching used raw whitespace. | `quotes.check` (one function for the Curator, the import check and, as a copy, the database): complete signed numbers (sign and decimals included) equal to the value, followed by a Celsius unit; terms matched after collapsing whitespace. | `test_quote_checks.py` (new file, 68 cases), including −25 °C, -25 °C, 25.5 °C, 125 °C, 2.25 °C, 20-25 °C for 25, and "room\ntemperature" |
| 6 | A run-scoped Curator invocation could be created. | `ck_agent_invocation_shape`: a run invocation's role is never the Curator's. | `test_a_run_invocation_of_the_curator_is_refused` |

**Overclaims corrected.**
- "Additive": the migration's docstring and the summary now say 0005 replaces two of 0001's functions, replaces the path rule under its name and makes two columns nullable. The nullable change is safe because the live database holds no model call.
- "No outcome values whatsoever": the README and the Curator access test's docstring now say the Curator gets no data row, claim or plan, and that the documentation itself may state outcome numbers.
- "Secrets are never logged" (the README, on the key): **redaction rather than a stated limit.** The agent request path now logs a failure's code, the exception's types and where it was raised, never its text. The stated limit that remains is what a library logs by itself; litellm's own debug logging is off unless a process turns it on. Tests: `test_provider_error_text_never_reaches_the_process_log` (a planted string in the provider's error message is absent from every log record at DEBUG), and the planted-text assertions in the recording and reservation tests.

**Headers** (review question 1): `test_the_request_headers_carry_nothing_of_the_input`. The header names are exactly host, accept-encoding, connection, user-agent, anthropic-version, accept, content-type, x-api-key and content-length. A value planted in the input appears in the body and in no header. This test passes on the reviewed code: it adds coverage, not a fix.

**Time zone** (owner): `db/engine.make_engine` sets `TimeZone=UTC` on every connection (`SESSION_TIME_ZONE`, new register entry `database_session_time_zone`). psycopg maps the name "UTC" to `timezone.utc` without reading a zone file. With the server's "Etc/UTC" it called `ZoneInfo`, which opened `/usr/share/zoneinfo/Etc/UTC`. The guard is unchanged. Test: `test_access_files.py::test_a_guarded_timestamp_read_needs_no_zone_file` (a guarded process reads `now()`: the session zone is UTC and no refusal is logged; before, "Etc/UTC" and one refusal). This adds one probe action, `timestamp`, in `access/guard_probe.py`.

## 2. The owner's term-check changes (a–h)

| | Change | Where |
|---|---|---|
| a | Whole words everywhere: B2 not in "Nb25", "tension" not in "extension", "tensile" not on "ultimate tensile strength" alone (that phrase is set aside before matching; another "tensile" in the same quote still counts). FCC, BCC and HCP case-insensitive; B2 and L12 case-sensitive (`CASE_SENSITIVE_TERMS`). All other terms case-insensitive. Word characters are ASCII letters, digits and "_", in code and database alike. | `quotes._occurs`, `EXCLUDED_PHRASES`; `hc_term_occurs` |
| b | Test type, temperature band and test temperature need a testing word as a whole word (`TESTING_WORDS`). "The plates were cold rolled at room temperature…" is refused (`testing_word_missing`, a new refusal code). | `quotes.check` step 5; `hc_curator_term_ok` |
| c | A test temperature's number must be followed by a Celsius unit, in the forms found in the frozen documents: plain "°C" (after spaces or LaTeX "~"; MPEA's paper) and LaTeX `\SI{875}{\degreeCelsius}` (Texas A&M main.tex line 188). No other form occurs in them. | `quotes._PLAIN`, `_LATEX` |
| d | Face and body centred or centered cubic, with or without hyphens (8 spellings each); "liquid helium" for cryogenic. | `quotes.TERMS` |
| e | Quote at most 600 characters (was 1500), beginning and ending at a word boundary in the document (a later occurrence at word boundaries is found if the first is inside a word). | `QUOTE_MAX_CHARS`; `quotes.locate`; `hc_quote_occurs` |
| f | The register records the safe refusals: statements under 30 characters; temperatures given in kelvin; Celsius forms not found in the documents (such as "$^\circ$C"); ranges such as "20-25 °C"; LaTeX forms of a term such as "L1$_2$"; a test sentence without a testing word. | register `curator_quote_checks`, notes; `test_the_recorded_safe_refusals` |
| g | **The two accepted proposals still pass**, in code and in the database (below). | `test_the_owners_two_accepted_proposals_still_pass`; `test_each_proposal_is_stored_as_code_decided_it` stores both through the real path as 'proposed'; `test_registering_the_frozen_curation_reproduces_the_sealed_curated_version` registers the frozen file under the new import check |
| h | The register's `quasistatic_tests` entry cites proposal 5's quote as the Texas A&M evidence. | register |

**g in detail.** Proposal 5 (test type tension; main.tex line 177, "Quasistatic tensile testing was used to determine 0.2\% offset YS, while Vickers indentation tests provided the HV.") is 115 characters. It starts after a space and ends before one, holds "tensile" as a whole word (not inside "ultimate tensile strength") and holds the testing words "testing" and "tests": it passes, term "tensile", line 177. Proposal 2 (phase class FCC; line 173, "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system.") is 89 characters, sits at word boundaries and holds "FCC" as a whole word; a phase class needs no testing word, so it passes, term "FCC", line 173. **The frozen `curation.json` is unchanged, byte for byte.**

## 3. Tests changed (not new)

- `test_migrations_step8a.py::test_one_proposal_per_field_per_invocation_for_its_own_version`: its last case made a proposal from a run-scoped **Curator** invocation, which finding 6 now refuses. It now uses a run invocation of the Planner. The intent (a proposal needs a registration invocation of the Curator) is unchanged.
- `test_data_model.py::test_totals_are_the_sum_of_the_calls_and_unreported_calls_count_at_their_bound` and `test_small_costs_are_stored_exactly`: their second stage was the Curator's, which can no longer have a run invocation. It is now the Critic's; the expected per-stage label changed from "curator" to "critic", and every number is unchanged.
- `tests/pipeline_world.py::registered_files` (helper): it attached the frozen curation file to a constructed Texas A&M version that held no documentation. That is exactly the copied-export case of finding 1, now refused, which made `test_mixed_groups.py::test_the_pipeline_never_admits_the_exact_duplicate_twice` lose its Texas A&M record. The helper now adds the frozen documentation and writes the file with the constructed version's own base fingerprint; the entries are unchanged.
- `test_migrations_step8a.py`: the existing case "term not in the quote" still holds. The existing 1600-character quote is still refused as `quote_too_long`.
- `test_access_curator.py`: docstring only (the overclaim).

## 4. Reference numbers

The five reference runs were dumped again after the fixes and compared leaf by leaf, both with the dump taken before the fixes and with `main`.
- **After the fixes vs before them: byte-identical.** Nothing in the reference numbers changed. The curation file, its fingerprint and every record are unchanged.
- **Branch vs `main`:** the same result as in the review packet. All 784 structural comparisons are identical (counts, checks, minimums, labels, reasons, degrees of freedom, significance, run rows, decisions except the freeze fingerprint). Estimates, standard errors, p and t differ by at most 8.7e-15 relative (record order follows the fingerprints). The freeze fingerprints and the calibration draws differ as before. Pooled: 97 records, 22 alloys, 20 groups, 74 residual degrees of freedom, k = 424.9 ± 64.4, p ≈ 1.3e-6.

## 5. Limits stated plainly

- The database does not check the line number. Code computes it, and the import check verifies it before a curation file is sealed or applied.
- The import check cannot show that a person accepted a value. Trust rests on the frozen, owner-approved export replayed on its own base.
- The code and the database each implement the checks. They are tested to agree on 32 cases and to hold the same lists, not proven equivalent. Whitespace other than ASCII (such as a no-break space) is collapsed by Python's `isspace` and may not be collapsed by PostgreSQL's `\s`. A disagreement there refuses the proposal, the safe direction.
- What a library logs by itself is not covered by the logging claim.
- The local development database was not rebuilt. It is still on the reviewed 0005, so it lacks the amended checks and functions. The live curation records there are kept, and so is the frozen file. Before using it again: back it up, then rebuild it at the amended 0005. That is an owner decision: rebuilding drops those rows.

## 6–10

Section 6: the new tests on the reviewed code. 7: mutation checks. 8: the suite. 9: the code and test diff since the review (`16261de`). 10: the register changes and the scripts.


## 6. The new tests on the reviewed code (`16261de`)

The new tests were run against a copy of the reviewed package (`git archive 16261de`) with this branch's tests and data. The only file added to the copy is `access/guard_probe.py`, the test probe with its new `timestamp` action, so that the time-zone test fails for its own reason. 117 failed and 12 passed. The 12 that pass are expected: the positive controls (the frozen export on its own base, a matching value and term, two word-boundary cases that hold, six database cases the old checks already refused), the run-cap race (already serialized by the run lock) and the headers test (coverage, not a fix).

```
PASSED tests/test_quote_checks.py::test_a_quote_begins_and_ends_at_a_word_boundary[The specimens were tested in tension throughout the study.-True]
PASSED tests/test_quote_checks.py::test_a_quote_begins_and_ends_at_a_word_boundary[specimens were tested in tension throughout the study-True]
PASSED tests/test_migrations_step8a.py::test_a_passed_proposal_with_a_missing_part_is_refused[change4]
PASSED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change1]
PASSED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change5]
PASSED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change9]
PASSED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change10]
PASSED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change11]
PASSED tests/test_migrations_step8a.py::test_the_matching_value_and_term_are_stored
PASSED tests/test_curator.py::test_the_frozen_export_on_its_own_base_is_accepted
PASSED tests/test_agent_core.py::test_two_reservations_on_one_run_cannot_both_pass_the_run_cap
PASSED tests/test_agent_core.py::test_the_request_headers_carry_nothing_of_the_input
FAILED tests/test_quote_checks.py::test_the_owners_two_accepted_proposals_still_pass[test_type-tension-Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation tests provided the HV.-177-tensile]
FAILED tests/test_quote_checks.py::test_the_owners_two_accepted_proposals_still_pass[phase_class-FCC-The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system.-173-FCC]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[microstructure-B2-The Nb25 alloys were examined by diffraction after annealing.-term_missing]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[microstructure-B2-Ordered B2 precipitates were found after annealing in every alloy.-None]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[microstructure-B2-Ordered b2 precipitates were found after annealing in every alloy.-term_missing]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[microstructure-L12-Coherent L12 precipitates were found after ageing in every alloy.-None]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[microstructure-L12-Coherent l12 precipitates were found after ageing in every alloy.-term_missing]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[microstructure-FCC-All alloys showed a single fcc phase after the final anneal.-None]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[microstructure-HCP-All alloys showed a single hcp phase after the final anneal.-None]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[microstructure-FCC+B2-Each alloy had an FCC matrix with B2 particles after annealing.-None]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[microstructure-FCC+B2-Each alloy had an FCC matrix with Nb2 particles after annealing.-term_missing]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[phase_class-FCC-All alloys were designed as fcc solid solutions in this study.-None]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[phase_class-BCC-All alloys were designed as BCCs and HCPs in this study, then.-term_missing]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[test_type-tension-Specimens were tested after extension of the gauge section by machining.-term_missing]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[test_type-tension-Specimens were tested in tension at a constant crosshead speed.-None]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[test_type-tension-The ultimate tensile strength was tested for each of the alloys.-term_missing]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[test_type-tension-The ultimate tensile strength and tensile ductility were tested for each.-None]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[test_type-compression-Cylinders were tested under compressive loading at room temperature.-None]
FAILED tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules[test_type-compression-Cylinders were tested under precompression before the main experiment.-term_missing]
FAILED tests/test_quote_checks.py::test_whitespace_is_collapsed_for_terms_as_for_locating_the_quote
FAILED tests/test_quote_checks.py::test_test_conditions_need_a_testing_word[test_temperature_band-room temperature-The plates were cold rolled at room temperature to a 60% reduction in thickness.-testing_word_missing]
FAILED tests/test_quote_checks.py::test_test_conditions_need_a_testing_word[test_temperature_band-room temperature-The plates were deformed at room temperature to a 60% reduction in thickness.-None]
FAILED tests/test_quote_checks.py::test_test_conditions_need_a_testing_word[test_type-tension-Dog-bone tensile specimens were cut from each plate by machining.-testing_word_missing]
FAILED tests/test_quote_checks.py::test_test_conditions_need_a_testing_word[test_type-tension-Dog-bone specimens were loaded in tension until they broke.-None]
FAILED tests/test_quote_checks.py::test_test_conditions_need_a_testing_word[test_type-tension-Dog-bone specimens were attested to be tensile by the supplier, sure.-testing_word_missing]
FAILED tests/test_quote_checks.py::test_test_conditions_need_a_testing_word[test_type-tension-Specimens were pulled in tension at a strain rate of 0.001 per second.-None]
FAILED tests/test_quote_checks.py::test_test_conditions_need_a_testing_word[test_temperature-25-Plates were annealed and then cooled to 25 \xb0C in still laboratory air.-testing_word_missing]
FAILED tests/test_quote_checks.py::test_test_conditions_need_a_testing_word[test_temperature-25-All the specimens were strained at 25 \xb0C in still laboratory air.-None]
FAILED tests/test_quote_checks.py::test_test_conditions_need_a_testing_word[phase_class-FCC-The dataset contains 94 FCC alloy conditions in one alloy system.-None]
FAILED tests/test_quote_checks.py::test_a_temperature_is_the_whole_number_with_its_unit[25-All the specimens were tested at 25 \xb0C in laboratory air.-25]
FAILED tests/test_quote_checks.py::test_a_temperature_is_the_whole_number_with_its_unit[25-All the specimens were tested at 25\xb0C in laboratory air.-25]
FAILED tests/test_quote_checks.py::test_a_temperature_is_the_whole_number_with_its_unit[25-All the specimens were tested at 25~\xb0C in laboratory air.-25]
FAILED tests/test_quote_checks.py::test_a_temperature_is_the_whole_number_with_its_unit[25-All the specimens were tested at \\SI{25}{\\degreeCelsius} in laboratory air.-25]
FAILED tests/test_quote_checks.py::test_a_temperature_is_the_whole_number_with_its_unit[25-All the specimens were tested at 25.0 \xb0C in laboratory air.-25.0]
FAILED tests/test_quote_checks.py::test_a_temperature_is_the_whole_number_with_its_unit[25.5-All the specimens were tested at 25.5 \xb0C in laboratory air.-25.5]
FAILED tests/test_quote_checks.py::test_a_temperature_is_the_whole_number_with_its_unit[-196-All the specimens were tested at \u2212196 \xb0C in liquid nitrogen.-\u2212196]
FAILED tests/test_quote_checks.py::test_a_temperature_is_the_whole_number_with_its_unit[-196-All the specimens were tested at -196 \xb0C in liquid nitrogen.--196]
FAILED tests/test_quote_checks.py::test_a_temperature_is_the_whole_number_with_its_unit[25-Tested at 300 \xb0C, and also tested at 25 \xb0C in laboratory air.-25]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[25-All the specimens were tested at \u221225 \xb0C in laboratory air.]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[25-All the specimens were tested at -25 \xb0C in laboratory air.]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[25-All the specimens were tested at 25.5 \xb0C in laboratory air.]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[25-All the specimens were tested at 125 \xb0C in laboratory air.]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[25-All the specimens were tested at 2.25 \xb0C in laboratory air.]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[25-All the specimens were tested between 20-25 \xb0C in laboratory air.]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[25-All the specimens were tested at 25 MPa in laboratory air and more.]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[25-All the specimens were tested at 25 and then held in laboratory air.]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[298-All the specimens were tested at 298 K in laboratory air, as usual.]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[25-All the specimens were tested at 25 $^\\circ$C in laboratory air.]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[25-All the specimens were tested at \\SI{125}{\\degreeCelsius} in laboratory air.]
FAILED tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused[-196-All the specimens were tested at 196 \xb0C in laboratory air, as usual.]
FAILED tests/test_quote_checks.py::test_spelling_variants_are_listed[phase_class-FCC-face-centred cubic]
FAILED tests/test_quote_checks.py::test_spelling_variants_are_listed[phase_class-FCC-face centered cubic]
FAILED tests/test_quote_checks.py::test_spelling_variants_are_listed[phase_class-FCC-face-centered-cubic]
FAILED tests/test_quote_checks.py::test_spelling_variants_are_listed[phase_class-FCC-face centred cubic]
FAILED tests/test_quote_checks.py::test_spelling_variants_are_listed[phase_class-BCC-body-centred cubic]
FAILED tests/test_quote_checks.py::test_spelling_variants_are_listed[phase_class-BCC-body centered cubic]
FAILED tests/test_quote_checks.py::test_spelling_variants_are_listed[phase_class-BCC-body-centered-cubic]
FAILED tests/test_quote_checks.py::test_spelling_variants_are_listed[test_temperature_band-cryogenic-liquid helium]
FAILED tests/test_quote_checks.py::test_a_quote_is_at_most_600_characters
FAILED tests/test_quote_checks.py::test_a_quote_begins_and_ends_at_a_word_boundary[he specimens were tested in tension throughout the study.-False]
FAILED tests/test_quote_checks.py::test_a_quote_begins_and_ends_at_a_word_boundary[The specimens were tested in tension throughout the stu-False]
FAILED tests/test_quote_checks.py::test_a_later_occurrence_at_word_boundaries_is_the_one_found
FAILED tests/test_quote_checks.py::test_the_recorded_safe_refusals[test_type-tension-Tested in tension.-quote_too_short]
FAILED tests/test_quote_checks.py::test_the_recorded_safe_refusals[test_temperature-25-All the specimens were tested at 298.15 K in laboratory air.-term_missing]
FAILED tests/test_quote_checks.py::test_the_recorded_safe_refusals[microstructure-L12-Coherent L1$_2$ precipitates were found after ageing in every alloy.-term_missing]
FAILED tests/test_quote_checks.py::test_the_value_is_checked_first_and_json_null_is_never_a_value
FAILED tests/test_migrations_step8a.py::test_a_run_invocation_of_the_curator_is_refused
FAILED tests/test_migrations_step8a.py::test_a_passed_proposal_with_a_missing_part_is_refused[change0]
FAILED tests/test_migrations_step8a.py::test_a_passed_proposal_with_a_missing_part_is_refused[change1]
FAILED tests/test_migrations_step8a.py::test_a_passed_proposal_with_a_missing_part_is_refused[change2]
FAILED tests/test_migrations_step8a.py::test_a_passed_proposal_with_a_missing_part_is_refused[change3]
FAILED tests/test_migrations_step8a.py::test_a_passed_proposal_with_a_missing_part_is_refused[change5]
FAILED tests/test_migrations_step8a.py::test_json_null_is_never_stored_as_a_value
FAILED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change0]
FAILED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change2]
FAILED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change3]
FAILED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change4]
FAILED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change6]
FAILED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change7]
FAILED tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused[change8]
FAILED tests/test_migrations_step8a.py::test_a_quote_must_begin_and_end_at_a_word_boundary_in_the_document
FAILED tests/test_migrations_step8a.py::test_the_databases_term_list_is_the_codes
FAILED tests/test_migrations_step8a.py::test_the_database_and_the_code_agree_on_every_case
FAILED tests/test_curator.py::test_an_export_copied_onto_another_base_is_refused
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change0]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change1]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change2]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change3]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change4]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change5]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change6]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change7]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change8]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change9]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change10]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change11]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change12]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change13]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change14]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change15]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change16]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change17]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change18]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change19]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change20]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change21]
FAILED tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused[change22]
FAILED tests/test_curator.py::test_a_quote_that_fails_the_current_term_checks_is_refused_on_import
FAILED tests/test_agent_core.py::test_two_reservations_on_one_invocation_cannot_both_pass_the_curation_cap
FAILED tests/test_agent_core.py::test_two_reservations_on_one_invocation_cannot_both_pass_a_lower_ceiling
FAILED tests/test_agent_core.py::test_a_recording_failure_on_any_branch_stops_and_keeps_the_maximum[provider_failure]
FAILED tests/test_agent_core.py::test_a_recording_failure_on_any_branch_stops_and_keeps_the_maximum[unreadable_reply]
FAILED tests/test_agent_core.py::test_a_recording_failure_on_any_branch_stops_and_keeps_the_maximum[no_usage]
FAILED tests/test_agent_core.py::test_a_recording_failure_on_any_branch_stops_and_keeps_the_maximum[success]
FAILED tests/test_agent_core.py::test_a_reservation_that_cannot_be_written_sends_nothing
FAILED tests/test_agent_core.py::test_provider_error_text_never_reaches_the_process_log
FAILED tests/test_access_files.py::test_a_guarded_timestamp_read_needs_no_zone_file

117 failed, 12 passed, 1 warning in 25.65s
```


## 7. Mutation checks on the fixes

Each mutation is applied to a scratch copy of the package (`data/` and `tests/` linked, `PYTHONPATH` to the copy, the import checked), and the named tests run (`~/hc-work/step08a/fix/run_mutations.sh`). **All 23 are caught.** The control (no change) has one failure: `test_access_files.py::test_the_python_installation_and_the_package_code_can_be_read`, which expects the repository's own package to be readable under the guard, while the scratch run uses a copy. It belongs only to f21's test file, whose run fails both that test and `test_a_guarded_timestamp_read_needs_no_zone_file` (checked by name).

```
23
control (no change): 1 failed, 246 passed, 1 warning in 89.33s (0:01:29)
f01: 2 failed, 37 passed, 1 warning in 36.63s
f02: 5 failed, 34 passed, 1 warning in 36.93s
f03: 1 failed, 38 passed, 1 warning in 36.73s
f04: 6 failed, 33 passed, 1 warning in 36.74s
f05: 2 failed, 112 passed in 26.81s
f06: 4 failed, 110 passed in 26.65s
f07: 4 failed, 110 passed in 26.44s
f08: 8 failed, 106 passed in 26.23s
f09: 4 failed, 110 passed in 26.59s
f10: 1 failed, 113 passed in 27.32s
f11: 1 failed, 113 passed in 27.18s
f12: 15 failed, 58 passed in 19.65s
f13: 3 failed, 70 passed in 19.36s
f14: 1 failed, 72 passed in 19.18s
f15: 1 failed, 72 passed in 19.28s
f16: 2 failed, 71 passed in 19.31s
f22: 1 failed, 72 passed in 19.49s
f23: 1 failed, 72 passed in 19.52s
f17: 2 failed, 44 passed in 33.57s
f18: 2 failed, 44 passed in 29.05s
f19: 2 failed, 44 passed in 27.01s
f20: 25 failed, 21 passed in 26.13s
f21: 2 failed, 19 passed in 16.51s

[exited with code 0]
```

The mutations: f01 the month lock after the totals (finding 3); f02 a recording failure re-raised; f03 a reservation failure not caught; f04 the exception text logged; f05 no case-sensitive terms; f06 no word boundaries for terms; f07 no testing word; f08 numbers without sign or decimal boundaries; f09 no word boundaries for quotes; f10 no excluded phrase; f11 the quote maximum back to 1500; f12 the database's term check removed; f13 the NULL-safe completeness check reverted; f14 a run invocation of the Curator allowed; f15 the database's quote boundaries removed; f16 the database's case-sensitive terms emptied; f17 the base fingerprint not checked; f18 the import's quote and term checks weakened; f19 any acceptor accepted; f20 no check at registration; f21 no session time zone; f22 JSON null allowed; f23 no testing word in the database. Specs:

- `f01`: `[["pipeline/agents/spend.py", "        conn.execute(text(\"SELECT pg_advisory_xact_lock(:k)\"), dict(k=MONTH_LOCK_KEY))\n        if inv.scope == \"run\":", "        if inv.scope == \"run\":"], ["pipeline/agents/spend.py", "        month = conn.execute(text(_MONTH_TOTAL)).scalar_one()", "        conn.execute(text(\"SELECT pg_advisory_xact_lock(:k)\"), dict(k=MONTH_LOCK_KEY))\n        month = conn.execute(text(_MONTH_TOTAL)).scalar_one()"]]`
- `f02`: `[["pipeline/agents/lm.py", "            _keep(\"recording_failed\", error)\n            raise self._fail(\"recording_failed\") from None", "            raise"]]`
- `f03`: `[["pipeline/agents/lm.py", "except Exception as error:  # noqa: BLE001 (nothing was reserved", "except ZeroDivisionError as error:  # noqa: BLE001 (nothing was reserved"]]`
- `f04`: `[["pipeline/agents/lm.py", "\"raised_at\": frames}))", "\"raised_at\": frames, \"text\": str(error)}))"]]`
- `f05`: `[["pipeline/agents/quotes.py", "CASE_SENSITIVE_TERMS = frozenset({\"B2\", \"L12\"})", "CASE_SENSITIVE_TERMS = frozenset()"]]`
- `f06`: `[["pipeline/agents/quotes.py", "return re.search(rf\"(?<![{_W}]){re.escape(term)}(?![{_W}])\", text, flags) is not None", "return re.search(re.escape(term), text, flags) is not None"]]`
- `f07`: `[["pipeline/agents/quotes.py", "TESTING_FIELDS = frozenset({\"test_type\", \"test_temperature_band\", \"test_temperature\"})", "TESTING_FIELDS = frozenset()"]]`
- `f08`: `[["pipeline/agents/quotes.py", "_PLAIN = re.compile(rf\"(?<![{_W}.{_SIGNS}])({_NUMBER})(?!\\.?[0-9])[ ~]*\\u00b0C\")", "_PLAIN = re.compile(rf\"([0-9]+)[ ~]*\\u00b0C\")"]]`
- `f09`: `[["pipeline/agents/quotes.py", "    return not inside_at_start and not inside_at_end", "    return True"]]`
- `f10`: `[["pipeline/agents/quotes.py", "EXCLUDED_PHRASES = (\"ultimate tensile strength\", \"ultimate tensile strengths\")", "EXCLUDED_PHRASES = ()"]]`
- `f11`: `[["pipeline/agents/quotes.py", "QUOTE_MIN_CHARS, QUOTE_MAX_CHARS = 30, 600", "QUOTE_MIN_CHARS, QUOTE_MAX_CHARS = 30, 1500"]]`
- `f12`: `[["db/migrations/versions/0005_agents_and_documentation.py", "f\"AND hc_curator_term_ok(field, value, quote, term), false)\",", "f\"AND true, false)\","]]`
- `f13`: `[["db/migrations/versions/0005_agents_and_documentation.py", "            f\"status <> 'proposed' OR coalesce(value IS NOT NULL AND quote IS NOT NULL AND document_path IS NOT NULL \"\n            f\"AND line IS NOT NULL AND term IS NOT NULL AND line >= 1 \"", "            f\"status <> 'proposed' OR (value IS NOT NULL AND document_path IS NOT NULL \"\n            f\"AND line >= 1 \""], ["db/migrations/versions/0005_agents_and_documentation.py", "f\"AND hc_curator_term_ok(field, value, quote, term), false)\",", "f\"AND (hc_curator_term_ok(field, value, quote, term) OR term IS NULL OR line IS NULL OR quote IS NULL))\","]]`
- `f14`: `[["db/migrations/versions/0005_agents_and_documentation.py", "            \"AND role <> 'curator') \"", "            \") \""]]`
- `f15`: `[["db/migrations/versions/0005_agents_and_documentation.py", "            IF NOT (s > 1 AND substr(t, s - 1, 1) ~ '[A-Za-z0-9_]'", "            IF true OR NOT (s > 1 AND substr(t, s - 1, 1) ~ '[A-Za-z0-9_]'"]]`
- `f16`: `[["db/migrations/versions/0005_agents_and_documentation.py", "CASE_SENSITIVE_TERMS = ('B2', 'L12')", "CASE_SENSITIVE_TERMS = ('B2x',)"]]`
- `f17`: `[["sources/curated.py", "    if base[\"fingerprint\"] != version_identity", "    if False and base[\"fingerprint\"] != version_identity"]]`
- `f18`: `[["sources/curated.py", "        if result.code is not None:\n            raise CurationInvalid(f\"entry {field!r}: {result.code}\")", "        if result.code not in (None, \"quote_not_found\", \"term_missing\", \"testing_word_missing\"):\n            raise CurationInvalid(f\"entry {field!r}: {result.code}\")"]]`
- `f19`: `[["sources/curated.py", "        if not (isinstance(by, str) and by.strip() and len(by) <= ACCEPTOR_MAX):", "        if not (by is None or isinstance(by, str)):"]]`
- `f20`: `[["sources/versions.py", "    if CURATION_PATH in files:  # checked", "    if False:  # checked"]]`
- `f21`: `[["db/engine.py", "connect_args={\"connect_timeout\": 3, \"options\": f\"-c TimeZone={SESSION_TIME_ZONE}\"})", "connect_args={\"connect_timeout\": 3})"]]`
- `f22`: `[["db/migrations/versions/0005_agents_and_documentation.py", "sa.CheckConstraint(\"value IS NULL OR jsonb_typeof(value) <> 'null'\",", "sa.CheckConstraint(\"true\","]]`
- `f23`: `[["db/migrations/versions/0005_agents_and_documentation.py", "        IF p_field IN ('test_type', 'test_temperature_band', 'test_temperature') AND NOT EXISTS (", "        IF p_field IN ('none') AND NOT EXISTS ("]]`


## 8. Suite

Locally:

```
1471 passed, 1 warning in 436.46s (0:07:16)
```

In the rebuilt test image:

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
1471 passed, 1 warning in 485.38s (0:08:05)
exit 0
```

### Reference comparison output (branch after the fixes vs `main`)

```
differing leaves by name: {'ci_high': 99, 'ci_low': 99, 'share': 99, 'significant': 99, 'seed': 66, 'detection': 34, 'detection_ci': 68, 'false_positive': 65, 'false_positive_ci': 130, 'estimated_power_estimated_noise': 32, 'estimated_power': 2, 'freeze_fingerprint': 5, 'rss_full': 6, 'scatter': 10, 'scatter_squared': 6, 'shift': 16, 'shift_squared_untruncated': 9, 'trace': 4, 'estimate': 3, 'p_value': 4, 'std_error': 4, 't': 4, 'rss_reduced': 1, 'records_found': 189}
max relative difference of estimate, standard error, p, t: 8.685492656737593e-15
   .reference.analyses[4].estimate 428.02404949610104 -> 428.024049496101
   .reference.analyses[4].p_value 7.398407506070927e-07 -> 7.398407506070913e-07
   .reference.analyses[4].std_error 63.51112235023561 -> 63.511122350235595
   .reference.analyses[4].t 6.739355779854411 -> 6.739355779854412
   .reference.analyses[5].p_value 7.511240461762386e-07 -> 7.511240461762399e-07
   .reference.analyses[5].std_error 64.22883580113376 -> 64.22883580113377
   .reference.analyses[5].t 6.615080354343604 -> 6.615080354343602
   .reference.analyses[8].estimate 432.3502268594971 -> 432.35022685949724
   .reference.analyses[8].p_value 6.72368893771935e-07 -> 6.723688937719363e-07
   .reference.analyses[8].std_error 64.86124831533819 -> 64.86124831533822
   .reference.analyses[8].t 6.665770981735118 -> 6.665770981735117
   .reference.analyses[11].estimate 393.50438134761123 -> 393.50438134761134
   .reference.analyses[11].p_value 0.00019348509448671378 -> 0.00019348509448671546
   .reference.analyses[11].std_error 90.487111236234 -> 90.48711123623411
   .reference.analyses[11].t 4.348734045894032 -> 4.3487340458940285
mpea_fixed | run row identical: True | decision keys differing: ['freeze_fingerprint']
mpea_use | run row identical: True | decision keys differing: ['freeze_fingerprint']
reference | run row identical: True | decision keys differing: ['freeze_fingerprint']
tamu_fixed | run row identical: True | decision keys differing: ['freeze_fingerprint']
tamu_use | run row identical: True | decision keys differing: ['freeze_fingerprint']
structural comparisons made (counts, checks, minimums, labels, reasons, df, significance per analysis): 784
pooled on the branch: 97 22 20 74 424.9 64.4 1.3e-06
```
Branch after the fixes vs the branch before them: the two dumps are byte-identical JSON.


## 9. Diffs since the review (`16261de..HEAD`)

### Package and README

````diff
diff --git a/README.md b/README.md
index c9667d1..3fd0810 100644
--- a/README.md
+++ b/README.md
@@ -14,7 +14,7 @@ Build step 8a of 12 (PRD Section 15; step 8 is built in two parts): the statisti
 cp .env.example .env     # then fill in every value; .env is never committed
 ```
 
-`HYPOCURATE_PASSWORD` is the login password: at least 24 characters in production (the site refuses to start otherwise), 12 locally. Generate it, e.g. with a password manager or `python3 -c "import secrets; print(secrets.token_urlsafe(24))"` (32 random characters). `SESSION_SECRET` signs the session cookie (at least 32 characters): `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. `POSTGRES_PASSWORD` is for the local database container only. `DATABASE_URL` is needed only to run the suite outside Docker: `postgresql://hypocurate:<POSTGRES_PASSWORD>@localhost:5432/hypocurate`. `ANTHROPIC_API_KEY` is the model provider's key (step 8a): the owner enters it; it is never printed or logged, and the suite never needs it (tests use a local stub of the provider).
+`HYPOCURATE_PASSWORD` is the login password: at least 24 characters in production (the site refuses to start otherwise), 12 locally. Generate it, e.g. with a password manager or `python3 -c "import secrets; print(secrets.token_urlsafe(24))"` (32 random characters). `SESSION_SECRET` signs the session cookie (at least 32 characters): `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. `POSTGRES_PASSWORD` is for the local database container only. `DATABASE_URL` is needed only to run the suite outside Docker: `postgresql://hypocurate:<POSTGRES_PASSWORD>@localhost:5432/hypocurate`. `ANTHROPIC_API_KEY` is the model provider's key (step 8a): the owner enters it; our code never prints it, the agent request path logs a failure only as its code, exception types and where it was raised (never an exception's text), and the suite never needs it (tests use a local stub of the provider). Not covered by that: what a library logs by itself (litellm's own debug logging is off unless a process turns it on).
 
 ## Start the system locally
 
@@ -142,7 +142,7 @@ hypocurate sources test tamu_fcc -n 3    # the first 3 records, in the common re
 
 ## The Curator and the agents' request path (step 8a)
 
-The Curator runs when a source version is registered, never in a run, and only for a source grouped by dataset. It reads that version's documentation and proposes, for the fields a table may lack, one value with the exact sentence it relied on. Code checks each proposal (the quote occurs in the sealed documentation, whitespace collapsed; it contains a listed term for the value); a person accepts or rejects it; the accepted values are sealed into a new source version and applied only where the table gives no value.
+The Curator runs when a source version is registered, never in a run, and only for a source grouped by dataset. It reads that version's documentation and proposes, for the fields a table may lack, one value with the exact sentence it relied on. Code checks each proposal (the value is allowed; the quote, 30 to 600 characters, occurs in the sealed documentation at word boundaries, whitespace collapsed; it holds a listed term for the value as a whole word and, for a test condition, a testing word; the database checks it all again except the line); a person accepts or rejects it; the accepted values are sealed into a new source version and applied only where the table gives no value. A curation file is checked against the version it is attached to before it is sealed or applied; the one trusted import is the exact approved export replayed on the same base. The documentation itself may state outcome numbers (a paper reports its results): the Curator receives no data row, claim or plan, not "no outcome value whatsoever".
 
 ```
 hypocurate sources curate tamu_fcc --ceiling 0.50   # one model call (costs money); needs ANTHROPIC_API_KEY
diff --git a/hypocurate/access/guard_probe.py b/hypocurate/access/guard_probe.py
index a5aa9ad..82a3b75 100644
--- a/hypocurate/access/guard_probe.py
+++ b/hypocurate/access/guard_probe.py
@@ -81,6 +81,17 @@ def _database(_: Any) -> str:
     return f"ok {value}"
 
 
+def _timestamp(_: Any) -> str:
+    """Reads a timestamp with time zone (step 8a review: no zone file is read for it)."""
+    from sqlalchemy import text
+    from hypocurate.db.engine import make_engine
+    engine = make_engine(os.environ["DATABASE_URL"])
+    with engine.connect() as conn:
+        zone, value = conn.execute(text("SELECT current_setting('TimeZone'), now()")).one()
+    engine.dispose()
+    return f"ok {zone} {value.isoformat()[-6:]}"
+
+
 def _certificates(_: Any) -> str:
     import urllib.request
     context = ssl.create_default_context()
@@ -165,7 +176,7 @@ ACTIONS: dict[str, Callable[[dict], str]] = {
     "read": lambda a: _read(a["path"], a.get("how", "open")),
     "list": lambda a: _list(a["path"], a.get("how", "listdir")),
     "write": lambda a: _write(a["path"]),
-    "write_scratch": _write_scratch, "scratch": _scratch, "render": _render, "database": _database, "certificates": _certificates,
+    "write_scratch": _write_scratch, "scratch": _scratch, "render": _render, "database": _database, "timestamp": _timestamp, "certificates": _certificates,
     "subprocess": _subprocess, "system": _system, "ctypes": _ctypes, "ctypes_string_at": _ctypes_string_at,
     "ctypes_from_address": _ctypes_from_address,
     "register": _register,
diff --git a/hypocurate/db/engine.py b/hypocurate/db/engine.py
index f3b7f66..47db92f 100644
--- a/hypocurate/db/engine.py
+++ b/hypocurate/db/engine.py
@@ -5,12 +5,19 @@ from __future__ import annotations
 
 from sqlalchemy import Engine, create_engine, text
 
+SESSION_TIME_ZONE = "UTC"  # register 'database_session_time_zone'
+
 
 def make_engine(database_url: str) -> Engine:
     # Render and Docker give "postgresql://"; SQLAlchemy needs the psycopg 3 driver named.
     if database_url.startswith("postgresql://"):
         database_url = "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
-    return create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
+    # The session's time zone is UTC by name (step 8a review; owner, 2026-10-07): the driver then
+    # interprets timestamps without reading a zone file, which the file guard would refuse (a server
+    # zone such as 'Etc/UTC' makes it open /usr/share/zoneinfo). Every query states its zone where it
+    # matters ('AT TIME ZONE ...'), and the servers used so far run in UTC already.
+    return create_engine(database_url, pool_pre_ping=True,
+                         connect_args={"connect_timeout": 3, "options": f"-c TimeZone={SESSION_TIME_ZONE}"})
 
 
 def database_reachable(engine: Engine) -> bool:
diff --git a/hypocurate/db/migrations/versions/0005_agents_and_documentation.py b/hypocurate/db/migrations/versions/0005_agents_and_documentation.py
index 12b9a3c..fa4b6c4 100644
--- a/hypocurate/db/migrations/versions/0005_agents_and_documentation.py
+++ b/hypocurate/db/migrations/versions/0005_agents_and_documentation.py
@@ -5,8 +5,12 @@ Revises: 0004
 Create Date: 2026-10-06
 
 Approved by the owner on 2026-10-06 (step 8a plan), subject to the second-model review before
-merging. Additive: 0001 to 0004 are untouched; the two trigger functions replaced here keep every
-check of 0001 unchanged and in the same order, and add new checks after them.
+merging; changed after that review (owner, 2026-10-07). Not purely additive: 0001 to 0004 are
+untouched as files, but this migration replaces two of 0001's trigger functions (each keeps every
+check of 0001 unchanged and in the same order, and adds new checks after them), replaces source_file's
+path rule under the same name, and makes model_call.run_id and stage_result_id nullable. That last
+change is safe because the live database holds no model call (step 8a summary); the downgrade
+refuses while any row uses what 0005 adds.
 
 source_file (owner, Q1: documentation frozen into the source version):
 - `role`: 'data' (default; what every earlier file is), 'documentation' or 'curation'. Each role
@@ -16,9 +20,10 @@ source_file (owner, Q1: documentation frozen into the source version):
 
 agent_invocation (one invocation record per agent call; step 5 re-check):
 - `scope` 'run' or 'registration'. A run invocation names its run and stage result, and its
-  (run, role, agent setting) must be one recorded at dispatch (`run_agent_setting`). A
-  registration invocation names a sealed source version, its role is the Curator's, and its agent
-  setting is a Curator setting. The dispatcher (`bind_invocation`) reads run or version, role,
+  (run, role, agent setting) must be one recorded at dispatch (`run_agent_setting`); its role is
+  never the Curator's (the Curator never runs within a run; review finding 6). A registration
+  invocation names a sealed source version, its role is the Curator's, and its agent setting is a
+  Curator setting. The dispatcher (`bind_invocation`) reads run or version, role,
   setting and source from this one row.
 
 model_call:
@@ -29,10 +34,16 @@ model_call:
   immutability rules. The month view already counts every call.
 
 curator_proposal, curator_decision (owner, Q2):
-- a proposal per field per invocation, either 'proposed' (it passed both checks: the quote occurs
-  in one of the version's documentation files, which the database verifies itself after
-  collapsing runs of whitespace, and the quote contains the listed term stored with it) or
-  'refused' with a code. Append-only.
+- a proposal per field per invocation, either 'proposed' (it passed the checks of
+  `pipeline.agents.quotes`, which the database applies again itself: the quote occurs in the
+  documentation file it names after collapsing runs of whitespace, beginning and ending at a word
+  boundary; it is 30 to 600 characters; the value has the field's type and is in its vocabulary;
+  the stored term is a listed term of that value (of every part of a microstructure, each of which
+  must occur) and occurs in the quote as a whole word; a test condition's quote holds a testing word;
+  a test temperature's term is a complete number equal to the value, followed by a Celsius unit;
+  nothing it needs is NULL, and no value is JSON null) or 'refused' with a code. Append-only. The
+  database does not check the line number (code computes it; a curation file is checked again,
+  line included, before it is sealed or applied).
 - one decision per proposal, 'accepted' or 'rejected', by a named person, at the database's time;
   only a 'proposed' proposal can be decided. Append-only.
 
@@ -46,6 +57,8 @@ functions and constraints exactly.
 Rules for every migration (README, "Database migrations"): it runs inside the one upgrade
 transaction; it keeps working with the previous release's code; and it has a downgrade.
 """
+import re
+
 from alembic import op
 import sqlalchemy as sa
 from sqlalchemy.dialects import postgresql
@@ -59,7 +72,153 @@ ROLES = "('planner', 'curator', 'critic', 'analyst', 'commentator')"
 # The fields the Curator may propose values for (owner, Q2): the conditions a table may lack.
 CURATION_FIELDS = ('test_type', 'phase_class', 'test_temperature', 'test_temperature_band', 'microstructure')
 # A proposal's quote, after collapsing runs of whitespace (the same normalization as the code's).
-QUOTE_MIN, QUOTE_MAX = 30, 1500
+QUOTE_MIN, QUOTE_MAX = 30, 600
+# The code's lists (pipeline.agents.quotes), copied here so the migration does not change when the
+# code does; tests/test_migrations_step8a.py checks that they are equal.
+CURATOR_TERMS = (
+    ('test_type', 'tension', 'tensile'),
+    ('test_type', 'tension', 'tension'),
+    ('test_type', 'compression', 'compressive'),
+    ('test_type', 'compression', 'compression'),
+    ('phase_class', 'FCC', 'FCC'),
+    ('phase_class', 'FCC', 'face-centred cubic'),
+    ('phase_class', 'FCC', 'face-centred-cubic'),
+    ('phase_class', 'FCC', 'face-centered cubic'),
+    ('phase_class', 'FCC', 'face-centered-cubic'),
+    ('phase_class', 'FCC', 'face centred cubic'),
+    ('phase_class', 'FCC', 'face centred-cubic'),
+    ('phase_class', 'FCC', 'face centered cubic'),
+    ('phase_class', 'FCC', 'face centered-cubic'),
+    ('phase_class', 'BCC', 'BCC'),
+    ('phase_class', 'BCC', 'body-centred cubic'),
+    ('phase_class', 'BCC', 'body-centred-cubic'),
+    ('phase_class', 'BCC', 'body-centered cubic'),
+    ('phase_class', 'BCC', 'body-centered-cubic'),
+    ('phase_class', 'BCC', 'body centred cubic'),
+    ('phase_class', 'BCC', 'body centred-cubic'),
+    ('phase_class', 'BCC', 'body centered cubic'),
+    ('phase_class', 'BCC', 'body centered-cubic'),
+    ('test_temperature_band', 'room temperature', 'room temperature'),
+    ('test_temperature_band', 'room temperature', 'room-temperature'),
+    ('test_temperature_band', 'room temperature', 'ambient temperature'),
+    ('test_temperature_band', 'elevated', 'elevated temperature'),
+    ('test_temperature_band', 'elevated', 'high temperature'),
+    ('test_temperature_band', 'elevated', 'high-temperature'),
+    ('test_temperature_band', 'cryogenic', 'cryogenic'),
+    ('test_temperature_band', 'cryogenic', 'liquid nitrogen'),
+    ('test_temperature_band', 'cryogenic', 'liquid helium'),
+    ('test_temperature_band', 'cryogenic', '77 K'),
+    ('microstructure', 'FCC', 'FCC'),
+    ('microstructure', 'BCC', 'BCC'),
+    ('microstructure', 'B2', 'B2'),
+    ('microstructure', 'HCP', 'HCP'),
+    ('microstructure', 'L12', 'L12'),
+    ('microstructure', 'Laves', 'Laves'),
+)
+CASE_SENSITIVE_TERMS = ('B2', 'L12')
+TESTING_WORDS = ('test', 'tests', 'tested', 'testing', 'loaded', 'loading', 'strained', 'deformed', 'strain rate')
+EXCLUDED_PHRASES = ('ultimate tensile strength', 'ultimate tensile strengths')
+# Every listed text is letters, digits, spaces and hyphens, so it is used in a regular expression as it is.
+assert all(re.fullmatch(r"[A-Za-z0-9 -]+", t) for t in
+           [t for _, _, t in CURATOR_TERMS] + list(TESTING_WORDS) + list(EXCLUDED_PHRASES))
+
+
+def _texts(items) -> str:
+    return "ARRAY[" + ", ".join(f"'{t}'" for t in items) + "]::text[]"
+
+
+_TERMS_SQL = "(VALUES " + ", ".join(f"('{f}', '{v}', '{t}')" for f, v, t in CURATOR_TERMS) + ") AS t(field, value, term)"
+_B = "(?<![A-Za-z0-9_])"  # a word boundary before and after (ASCII word characters, as the code's)
+_A = "(?![A-Za-z0-9_])"
+
+# Whether a quote occurs in a document, both with runs of whitespace collapsed, beginning and ending
+# at a word boundary (the code's `quotes.locate`, without the line).
+QUOTE_OCCURS = r"""
+    CREATE FUNCTION hc_quote_occurs(p_document text, p_quote text) RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $$
+    DECLARE t text := regexp_replace(p_document, '\s+', ' ', 'g');
+            q text := btrim(regexp_replace(p_quote, '\s+', ' ', 'g'));
+            off int := 0; pos int; s int; e int;
+    BEGIN
+        IF t IS NULL OR q IS NULL OR q = '' THEN
+            RETURN false;
+        END IF;
+        LOOP
+            pos := strpos(substr(t, off + 1), q);
+            EXIT WHEN pos = 0;
+            s := off + pos;
+            e := s + length(q) - 1;
+            IF NOT (s > 1 AND substr(t, s - 1, 1) ~ '[A-Za-z0-9_]' AND substr(t, s, 1) ~ '[A-Za-z0-9_]')
+               AND NOT (e < length(t) AND substr(t, e, 1) ~ '[A-Za-z0-9_]' AND substr(t, e + 1, 1) ~ '[A-Za-z0-9_]') THEN
+                RETURN true;
+            END IF;
+            off := s;
+        END LOOP;
+        RETURN false;
+    END $$
+    """
+
+# Whether a proposal's value has its field's type and vocabulary and its term is a listed term of that
+# value that occurs in the quote (the code's `quotes.check`, steps 1, 4 and 5).
+TERM_OK = r"""
+    CREATE FUNCTION hc_curator_term_ok(p_field text, p_value jsonb, p_quote text, p_term text)
+    RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $$
+    DECLARE q text; collapsed text; v text; n numeric; part text; phrase text; pattern text;
+    BEGIN
+        IF p_field IS NULL OR p_value IS NULL OR p_quote IS NULL OR p_term IS NULL THEN
+            RETURN false;
+        END IF;
+        collapsed := btrim(regexp_replace(p_quote, '\s+', ' ', 'g'));
+        q := collapsed;
+        FOREACH phrase IN ARRAY __EXCLUDED__ LOOP
+            q := regexp_replace(q, '__B__' || phrase || '__A__', ' ', 'gi');
+        END LOOP;
+        IF p_field IN ('test_type', 'test_temperature_band', 'test_temperature') AND NOT EXISTS (
+                SELECT 1 FROM unnest(__TESTING__) w WHERE collapsed ~* ('__B__' || w || '__A__')) THEN
+            RETURN false;
+        END IF;
+        IF p_field = 'test_temperature' THEN
+            IF jsonb_typeof(p_value) <> 'number' THEN
+                RETURN false;
+            END IF;
+            n := (p_value #>> '{}')::numeric;
+            IF n < -273.15 OR n > 3000 OR p_term !~ '^[-+−–]?[0-9]+([.][0-9]+)?$'
+               OR translate(p_term, '−–', '--')::numeric <> n THEN
+                RETURN false;
+            END IF;
+            pattern := replace(replace(p_term, '.', '[.]'), '+', '[+]');
+            RETURN q ~ ('(?<![A-Za-z0-9_.+−–-])' || pattern || '(?![.]?[0-9])[ ~]*°C')
+                OR q ~ ('\\SI[{]' || pattern || '[}][{]\\degreeCelsius[}]');
+        END IF;
+        IF jsonb_typeof(p_value) <> 'string' THEN
+            RETURN false;
+        END IF;
+        v := p_value #>> '{}';
+        IF p_field = 'microstructure' THEN
+            FOREACH part IN ARRAY string_to_array(v, '+') LOOP
+                IF NOT EXISTS (SELECT 1 FROM __TERMS__ WHERE t.field = 'microstructure' AND t.value = part
+                               AND hc_term_occurs(t.term, q)) THEN
+                    RETURN false;
+                END IF;
+            END LOOP;
+            RETURN EXISTS (SELECT 1 FROM __TERMS__ WHERE t.field = 'microstructure'
+                           AND t.value = ANY (string_to_array(v, '+')) AND t.term = p_term);
+        END IF;
+        RETURN EXISTS (SELECT 1 FROM __TERMS__ WHERE t.field = p_field AND t.value = v AND t.term = p_term
+                       AND hc_term_occurs(t.term, q));
+    END $$
+    """.replace("__EXCLUDED__", _texts(EXCLUDED_PHRASES)).replace("__TESTING__", _texts(TESTING_WORDS)) \
+       .replace("__TERMS__", _TERMS_SQL).replace("__B__", _B).replace("__A__", _A)
+
+# A listed term as a whole word of the (collapsed) quote; case-insensitive except CASE_SENSITIVE_TERMS.
+TERM_OCCURS = r"""
+    CREATE FUNCTION hc_term_occurs(p_term text, p_text text) RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
+        SELECT CASE WHEN p_term = ANY (__SENSITIVE__) THEN p_text ~ ('__B__' || p_term || '__A__')
+                    ELSE p_text ~* ('__B__' || p_term || '__A__') END
+    $$
+    """.replace("__SENSITIVE__", _texts(CASE_SENSITIVE_TERMS)).replace("__B__", _B).replace("__A__", _A)
+CHECK_FUNCTIONS = [QUOTE_OCCURS, TERM_OCCURS, TERM_OK]
+CHECK_FUNCTION_NAMES = ["hc_curator_term_ok(text, jsonb, text, text)", "hc_term_occurs(text, text)",
+                        "hc_quote_occurs(text, text)"]
 STORED_TEXT_MAX = 4000  # any status: what the model wrote is kept, bounded
 
 # 0001's path rule, and the rule by role that replaces it under the same name (so a path tells its
@@ -199,8 +358,8 @@ FUNCTIONS = [
     END $$
     """,
     # A proposal belongs to a registration invocation of the Curator and to that invocation's
-    # version. A proposal that passed the checks quotes a passage the database finds in one of the
-    # version's documentation files (runs of whitespace collapsed on both sides).
+    # version. A proposal that passed the checks quotes a passage the database finds in the
+    # documentation file it names (runs of whitespace collapsed on both sides, at word boundaries).
     """
     CREATE FUNCTION hc_curator_proposal_insert() RETURNS trigger LANGUAGE plpgsql AS $$
     DECLARE inv agent_invocation;
@@ -212,11 +371,11 @@ FUNCTIONS = [
         IF NEW.source_version_id IS DISTINCT FROM inv.source_version_id THEN
             PERFORM hc_reject('a proposal is for its invocation''s source version');
         END IF;
-        IF NEW.status = 'proposed' AND NOT EXISTS (
+        -- (A missing quote or document is refused by ck_curator_proposal_proposed_complete.)
+        IF NEW.status = 'proposed' AND NEW.quote IS NOT NULL AND NEW.document_path IS NOT NULL AND NOT EXISTS (
                 SELECT 1 FROM source_file f WHERE f.source_version_id = NEW.source_version_id
                   AND f.role = 'documentation' AND f.path = NEW.document_path
-                  AND strpos(regexp_replace(convert_from(f.content, 'UTF8'), '\\s+', ' ', 'g'),
-                             btrim(regexp_replace(NEW.quote, '\\s+', ' ', 'g'))) > 0) THEN
+                  AND hc_quote_occurs(convert_from(f.content, 'UTF8'), NEW.quote)) THEN
             PERFORM hc_reject('a proposal''s quote must occur in the documentation file it names');
         END IF;
         NEW.created_at := now();
@@ -277,7 +436,8 @@ def upgrade() -> None:
         sa.CheckConstraint("scope IN ('run', 'registration')", name=op.f('ck_agent_invocation_scope')),
         sa.CheckConstraint(f"role IN {ROLES}", name=op.f('ck_agent_invocation_role')),
         sa.CheckConstraint(
-            "(scope = 'run' AND run_id IS NOT NULL AND stage_result_id IS NOT NULL AND source_version_id IS NULL) "
+            "(scope = 'run' AND run_id IS NOT NULL AND stage_result_id IS NOT NULL AND source_version_id IS NULL "
+            "AND role <> 'curator') "
             "OR (scope = 'registration' AND run_id IS NULL AND stage_result_id IS NULL "
             "AND source_version_id IS NOT NULL AND role = 'curator')", name=op.f('ck_agent_invocation_shape')),
         sa.ForeignKeyConstraint(['run_id'], ['run.id'], name=op.f('fk_agent_invocation_run_id')),
@@ -306,6 +466,8 @@ def upgrade() -> None:
                                "(run_id IS NULL) = (stage_result_id IS NULL)")
     op.create_check_constraint(op.f('ck_model_call_with_invocation'), 'model_call', "invocation_id IS NOT NULL")
 
+    for f in CHECK_FUNCTIONS:  # used by curator_proposal's checks and trigger
+        op.execute(f)
     op.create_table(
         'curator_proposal',
         sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
@@ -323,11 +485,17 @@ def upgrade() -> None:
         sa.CheckConstraint("field IN (" + ", ".join(f"'{f}'" for f in CURATION_FIELDS) + ")",
                            name=op.f('ck_curator_proposal_field')),
         sa.CheckConstraint("status IN ('proposed', 'refused', 'not_stated')", name=op.f('ck_curator_proposal_status')),
+        # Every part a passed proposal needs, non-NULL (so the check can never be UNKNOWN, which a CHECK
+        # accepts), and its value and term as the code's checks require.
         sa.CheckConstraint(
-            f"status <> 'proposed' OR (value IS NOT NULL AND document_path IS NOT NULL AND line >= 1 "
+            f"status <> 'proposed' OR coalesce(value IS NOT NULL AND quote IS NOT NULL AND document_path IS NOT NULL "
+            f"AND line IS NOT NULL AND term IS NOT NULL AND line >= 1 "
             f"AND length(btrim(regexp_replace(quote, '\\s+', ' ', 'g'))) BETWEEN {QUOTE_MIN} AND {QUOTE_MAX} "
-            f"AND length(term) > 0 AND strpos(lower(quote), lower(term)) > 0)",
+            f"AND hc_curator_term_ok(field, value, quote, term), false)",
             name=op.f('ck_curator_proposal_proposed_complete')),
+        # No value is ever JSON null (named to sort after the check above).
+        sa.CheckConstraint("value IS NULL OR jsonb_typeof(value) <> 'null'",
+                           name=op.f('ck_curator_proposal_value_not_json_null')),
         sa.CheckConstraint("(status = 'refused') = (refusal_code IS NOT NULL) "
                            "AND (refusal_code IS NULL OR refusal_code ~ '^[a-z_]+$')",
                            name=op.f('ck_curator_proposal_refusal_code')),
@@ -396,7 +564,7 @@ def downgrade() -> None:
     op.drop_column('model_call', 'invocation_id')
     op.drop_index('ix_agent_invocation_run_id', table_name='agent_invocation')
     op.drop_table('agent_invocation')
-    for f in FUNCTION_NAMES:
+    for f in FUNCTION_NAMES + CHECK_FUNCTION_NAMES:
         op.execute(f"DROP FUNCTION {f}")
     op.drop_constraint(op.f('uq_run_agent_setting_run_id_role_agent_setting_id'), 'run_agent_setting', type_='unique')
     op.drop_constraint(op.f('ck_source_file_safe_data_file_path'), 'source_file', type_='check')
diff --git a/hypocurate/db/models.py b/hypocurate/db/models.py
index d2da17f..3e0e554 100644
--- a/hypocurate/db/models.py
+++ b/hypocurate/db/models.py
@@ -555,7 +555,7 @@ class ModelCall(Base):
 # --- Agent invocations and the Curator's proposals (step 8a, migration 0005) --------------
 
 CURATION_FIELDS = ("test_type", "phase_class", "test_temperature", "test_temperature_band", "microstructure")
-QUOTE_MIN, QUOTE_MAX = 30, 1500  # a proposal's quote, whitespace collapsed (register 'curator_quote_checks')
+QUOTE_MIN, QUOTE_MAX = 30, 600  # a proposal's quote, whitespace collapsed (register 'curator_quote_checks')
 STORED_TEXT_MAX = 4000
 
 
@@ -577,7 +577,8 @@ class AgentInvocation(Base):
         CheckConstraint("scope IN ('run', 'registration')", name="scope"),
         CheckConstraint(one_of("role", ROLES), name="role"),
         CheckConstraint(
-            "(scope = 'run' AND run_id IS NOT NULL AND stage_result_id IS NOT NULL AND source_version_id IS NULL) "
+            "(scope = 'run' AND run_id IS NOT NULL AND stage_result_id IS NOT NULL AND source_version_id IS NULL "
+            "AND role <> 'curator') "
             "OR (scope = 'registration' AND run_id IS NULL AND stage_result_id IS NULL "
             "AND source_version_id IS NOT NULL AND role = 'curator')", name="shape"),
         ForeignKeyConstraint(["agent_setting_id", "role"], ["agent_setting.id", "agent_setting.role"],
@@ -612,9 +613,11 @@ class CuratorProposal(Base):
         CheckConstraint(one_of("field", CURATION_FIELDS), name="field"),
         CheckConstraint("status IN ('proposed', 'refused', 'not_stated')", name="status"),
         CheckConstraint(
-            f"status <> 'proposed' OR (value IS NOT NULL AND document_path IS NOT NULL AND line >= 1 "
+            f"status <> 'proposed' OR coalesce(value IS NOT NULL AND quote IS NOT NULL AND document_path IS NOT NULL "
+            f"AND line IS NOT NULL AND term IS NOT NULL AND line >= 1 "
             f"AND length(btrim(regexp_replace(quote, '\\s+', ' ', 'g'))) BETWEEN {QUOTE_MIN} AND {QUOTE_MAX} "
-            f"AND length(term) > 0 AND strpos(lower(quote), lower(term)) > 0)", name="proposed_complete"),
+            f"AND hc_curator_term_ok(field, value, quote, term), false)", name="proposed_complete"),
+        CheckConstraint("value IS NULL OR jsonb_typeof(value) <> 'null'", name="value_not_json_null"),
         CheckConstraint("(status = 'refused') = (refusal_code IS NOT NULL) "
                         "AND (refusal_code IS NULL OR refusal_code ~ '^[a-z_]+$')", name="refusal_code"),
         CheckConstraint("status <> 'not_stated' OR (value IS NULL AND quote IS NULL AND document_path IS NULL "
diff --git a/hypocurate/pipeline/agents/curator.py b/hypocurate/pipeline/agents/curator.py
index e6b0d3e..a2b6438 100644
--- a/hypocurate/pipeline/agents/curator.py
+++ b/hypocurate/pipeline/agents/curator.py
@@ -6,7 +6,8 @@ measurements, with the exact sentence it relied on, or says "not stated". It is
 plan or data row (its access list holds only the documentation and the targets).
 
 Code decides what a proposal is: `proposals_from` checks each entry (the field is a target, the
-value is allowed, the quote is found in the documentation and contains a listed term; `quotes`) and
+value is allowed, the quote is found in the documentation at word boundaries, holds a listed term and, for a
+test condition, a testing word; `quotes.check`) and
 stores it as 'proposed', 'refused' with a code, or 'not_stated'. A proposal takes effect only when a
 person accepts it (`sources.curation`), and only where a table gives no value.
 
@@ -18,12 +19,11 @@ common interface).
 from __future__ import annotations
 
 import json
-import math
 import re
 from dataclasses import dataclass
 from typing import Any, Mapping
 
-from hypocurate.access.vocabulary import CURATION_TARGETS, MICROSTRUCTURE_TOKENS
+from hypocurate.access.vocabulary import CURATION_TARGETS
 from hypocurate.pipeline.agents import libraries, quotes
 
 OUTPUT_DESCRIPTION = ('One JSON object with one key per target field. The value of each key is either the string '
@@ -84,17 +84,6 @@ class Proposal:
     refusal_code: str | None = None
 
 
-def _value_problem(field: str, value: Any) -> str | None:
-    if field == "test_temperature":
-        ok = (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
-              and -273.15 <= value <= 3000)
-        return None if ok else "value_not_allowed"
-    if field == "microstructure":
-        ok = isinstance(value, str) and value != "" and all(t in MICROSTRUCTURE_TOKENS for t in value.split("+"))
-        return None if ok else "value_not_allowed"
-    return None if isinstance(value, str) and value in CURATION_TARGETS[field]["vocabulary"] else "value_not_allowed"
-
-
 def _stored(value: Any) -> Any:
     """What a refused entry keeps of the model's value: JSON within the bound, else nothing."""
     try:
@@ -110,23 +99,11 @@ def _entry(field: str, entry: Any, documents: Mapping[str, str]) -> Proposal:
     if not (isinstance(entry, dict) and set(entry) == {"value", "quote"} and isinstance(entry["quote"], str)):
         return Proposal(field, "refused", refusal_code="malformed_entry")
     value, quote = entry["value"], entry["quote"]
-    kept = dict(value=_stored(value), quote=quote[:STORED_MAX])
-    code = _value_problem(field, value)
-    collapsed = quotes.collapse(quote)
-    if code is None and len(collapsed) < quotes.QUOTE_MIN_CHARS:
-        code = "quote_too_short"
-    if code is None and len(collapsed) > quotes.QUOTE_MAX_CHARS:
-        code = "quote_too_long"
-    located = quotes.locate(quote, documents) if code is None else None
-    if code is None and located is None:
-        code = "quote_not_found"
-    term = quotes.term_for(field, value, quote) if code is None else None
-    if code is None and term is None:
-        code = "term_missing"
-    if code is not None:
-        return Proposal(field, "refused", refusal_code=code, **kept)
-    return Proposal(field, "proposed", value=value, quote=quote, document=located.document, line=located.line,
-                    term=term)
+    result = quotes.check(field, value, quote, documents)
+    if result.code is not None:
+        return Proposal(field, "refused", refusal_code=result.code, value=_stored(value), quote=quote[:STORED_MAX])
+    return Proposal(field, "proposed", value=value, quote=quote, document=result.located.document,
+                    line=result.located.line, term=result.term)
 
 
 def proposals_from(text: str, documents: Mapping[str, str]) -> tuple[list[Proposal], list[str]]:
diff --git a/hypocurate/pipeline/agents/lm.py b/hypocurate/pipeline/agents/lm.py
index 00e0da1..d6d5d81 100644
--- a/hypocurate/pipeline/agents/lm.py
+++ b/hypocurate/pipeline/agents/lm.py
@@ -8,20 +8,28 @@ each request it:
 2. sends the request through DSPy's own litellm engine, outside any database transaction, one HTTP
    attempt (litellm's retries are off, `libraries.load`);
 3. records the outcome (`spend.finish`): the reported usage and its cost (`prices.cost`), or a
-   failure with no usage and a fixed code;
+   failure with no usage and a fixed code. If that recording fails, on any branch (a provider
+   failure, a reply without usage, a usable reply), the call ends with `recording_failed`, which
+   stops it: no further request, and the call stays started, counted at its maximum cost (step 8a
+   review, finding 4). A reservation that cannot be written ends with `reservation_failed`; nothing
+   is sent;
 4. turns a reply that cannot be used into a fixed code after it is recorded: truncated (the output
    limit was reached), refused, a tool call (no tools are offered), empty or over-long text.
 
 Every failure is an `AgentFailure` with a fixed code (`FAILURES`); its message is the code's fixed
-text. The original exception, with its traceback, goes to the process log only: nothing a provider,
-a library or the database wrote ever travels with the error or into a later request. The last
-failure is also kept on the engine (`last_failure`), because DSPy may wrap exceptions raised inside
-it.
+text. The process log gets the code, the exception's type (and the types of its causes) and where it
+was raised (file, line, function), never the exception's text: a provider's or library's message can
+quote the request, and this path never writes it anywhere (step 8a review). Nothing a provider, a
+library or the database wrote ever travels with the error or into a later request. The last failure
+is also kept on the engine (`last_failure`), because DSPy may wrap exceptions raised inside it.
+Not covered: what a library logs by itself (litellm's own debug logging is off unless a process
+turns it on).
 """
 from __future__ import annotations
 
 import json
 import logging
+import traceback
 from decimal import Decimal
 from typing import Any, Mapping
 
@@ -37,6 +45,7 @@ FAILURES: Mapping[str, tuple[str, str]] = {
     "provider_rejected": ("the provider refused the request", "stop"),
     "cost_unknown": ("the provider reported no usage, so the cost is unknown", "stop"),
     "recording_failed": ("the call could not be recorded", "stop"),
+    "reservation_failed": ("the call could not be reserved", "stop"),
     "refused": ("the model declined to answer", "stop"),
     "truncated": ("the answer reached the output limit", "correct"),
     "tool_call": ("the answer asked for a tool; none is offered", "correct"),
@@ -69,7 +78,14 @@ def _classify(error: BaseException) -> str:
 
 
 def _keep(code: str, error: BaseException) -> None:
-    LOG.error(json.dumps({"agent_request_failure": code}), exc_info=(type(error), error, error.__traceback__))
+    """The failure in the process log: its code, types and places, never its text."""
+    chain, seen, current = [], set(), error
+    while current is not None and id(current) not in seen:
+        seen.add(id(current))
+        chain.append(type(current).__qualname__)
+        current = current.__cause__ or current.__context__
+    frames = [f"{f.filename}:{f.lineno} {f.name}" for f in traceback.extract_tb(error.__traceback__)]
+    LOG.error(json.dumps({"agent_request_failure": code, "exception_types": chain, "raised_at": frames}))
 
 
 def request_bytes(request: Any) -> int:
@@ -101,6 +117,9 @@ class RecordedEngine:
             call = spend.reserve(self._db, self._invocation, self._model, bound, self._ceiling)
         except spend.SpendingRefused as refused:
             raise self._fail(refused.code) from None
+        except Exception as error:  # noqa: BLE001 (nothing was reserved, so nothing is sent)
+            _keep("reservation_failed", error)
+            raise self._fail("reservation_failed") from None
         self.calls.append(call)
         failure = None
         try:
@@ -109,28 +128,34 @@ class RecordedEngine:
             failure = _classify(error)
             _keep(failure, error)
         if failure is not None:
-            spend.finish(self._db, call, "failed", code=failure)
+            self._record(call, "failed", code=failure)
             raise self._fail(failure)
         usage = response.usage
         if usage is None or usage.input_tokens is None or usage.output_tokens is None:
-            spend.finish(self._db, call, "failed", code="cost_unknown")
+            self._record(call, "failed", code="cost_unknown")
             raise self._fail("cost_unknown")
         read, write = usage.cache_read_tokens or 0, usage.cache_write_tokens or 0
-        recorded = None
-        try:
-            spend.finish(self._db, call, "succeeded", input_tokens=usage.input_tokens,
-                         output_tokens=usage.output_tokens, cached_tokens=read,
-                         cost=prices.cost(self._model, usage.input_tokens, usage.output_tokens, read, write))
-            recorded = True
-        except Exception as error:  # noqa: BLE001
-            _keep("recording_failed", error)
-        if not recorded:
-            raise self._fail("recording_failed")
+        self._record(call, "succeeded", usage=(usage.input_tokens, usage.output_tokens, read, write))
         code = _unusable(response, self._max_output_chars)
         if code:
             raise self._fail(code)
         return response
 
+    def _record(self, call: int, status: str, *, usage=None, code: str | None = None) -> None:
+        """Finishes the call; any failure to do so (on every branch) ends the agent call with
+        `recording_failed`, and the call stays started, counted at its maximum cost."""
+        try:
+            if usage is None:
+                spend.finish(self._db, call, status, code=code)
+            else:
+                input_tokens, output_tokens, read, write = usage
+                spend.finish(self._db, call, status, input_tokens=input_tokens, output_tokens=output_tokens,
+                             cached_tokens=read,
+                             cost=prices.cost(self._model, input_tokens, output_tokens, read, write))
+        except Exception as error:  # noqa: BLE001
+            _keep("recording_failed", error)
+            raise self._fail("recording_failed") from None
+
     def stream(self, request):
         raise NotImplementedError("the agents do not stream")
 
diff --git a/hypocurate/pipeline/agents/quotes.py b/hypocurate/pipeline/agents/quotes.py
index 14e6bf7..f708e67 100644
--- a/hypocurate/pipeline/agents/quotes.py
+++ b/hypocurate/pipeline/agents/quotes.py
@@ -1,39 +1,77 @@
-"""The two checks on a Curator proposal (owner, 2026-10-06, Q2; register 'curator_quote_checks').
-
-1. **The quote occurs in the source's sealed documentation.** Runs of whitespace (spaces, tabs,
-   line breaks) are collapsed to one space on both sides, and the quote is trimmed; nothing else is
-   changed (no case folding, no punctuation or LaTeX normalization). Code finds the document and the
-   line where the quote begins; the model's own claim about where it found the quote is not used.
-   The database checks the same occurrence again when the proposal is stored (migration 0005).
-2. **The quote contains a listed term for the proposed value** (`TERMS`, case-insensitive), a first
-   filter against a quote unrelated to the value. A paraphrase without a listed term is refused,
-   which leaves the field unassigned: the safe direction. For the test temperature (a number), the
-   term is the number as written in the quote. A microstructure joined by '+' needs every part.
-
-Neither check shows that the sentence supports the value: that is for the person who accepts or
-rejects the proposal, with the quote shown beside it.
+"""The checks on a Curator proposal (owner, 2026-10-06, Q2; changed after the step 8a review, owner
+2026-10-07; register 'curator_quote_checks').
+
+`check(field, value, quote, documents)` applies them in this order and returns the first refusal code:
+1. **The value** is allowed for the field (`value_problem`): a vocabulary value, a microstructure of
+   vocabulary tokens joined by '+', or for the test temperature a finite number of °C (never JSON
+   null, never a boolean or a string).
+2. **The quote's length**, after collapsing runs of whitespace: `QUOTE_MIN_CHARS` to `QUOTE_MAX_CHARS`.
+3. **The quote occurs in the source's sealed documentation** (`locate`): runs of whitespace are
+   collapsed to one space on both sides and the quote is trimmed; nothing else is changed (no case
+   folding, no punctuation or LaTeX normalization). The occurrence must begin and end at a word
+   boundary of the document (it does not start or stop inside a word). Code finds the document and
+   the line; the model's own claim about where it found the quote is not used.
+4. **The quote holds a listed term for the value** (`term_for`), as a whole word, after collapsing
+   whitespace and setting aside `EXCLUDED_PHRASES` ("tensile" in "ultimate tensile strength" alone is
+   not a test type). Terms are case-insensitive except `CASE_SENSITIVE_TERMS` (B2, L12). A
+   microstructure joined by '+' needs every part. A test temperature is a complete signed number
+   (sign and decimals included, so 25 never matches -25, 25.5 or 125) equal to the value and followed
+   by a Celsius unit in a form found in the frozen documents: "°C" (after spaces or LaTeX "~"), or
+   LaTeX "\\SI{<number>}{\\degreeCelsius}".
+5. **For a test condition** (test type, temperature band, test temperature) the quote also holds a
+   testing word (`TESTING_WORDS`, whole words): a processing sentence such as "cold rolled at room
+   temperature" is refused.
+
+Safe refusals, recorded in the register: a statement under 30 characters, a temperature given in
+kelvin or in a Celsius form not found in the documents (such as "$^\\circ$C"), a range such as
+"20-25 °C", and LaTeX forms of a term (such as "L1$_2$"). Each leaves the field unassigned.
+
+The database applies the same checks when a passed proposal is stored (migration 0005, with its own
+copy of the lists, tested equal to these). None of them shows that the sentence supports the value:
+that is for the person who accepts or rejects the proposal, with the quote shown beside it.
 """
 from __future__ import annotations
 
+import math
 import re
 from dataclasses import dataclass
+from decimal import Decimal
 from types import MappingProxyType
-from typing import Mapping
+from typing import Any, Mapping
+
+from hypocurate.access.vocabulary import CURATION_TARGETS, MICROSTRUCTURE_TOKENS
 
-QUOTE_MIN_CHARS, QUOTE_MAX_CHARS = 30, 1500  # after collapsing whitespace; the database's bounds (0005)
+QUOTE_MIN_CHARS, QUOTE_MAX_CHARS = 30, 600  # after collapsing whitespace; the database's bounds (0005)
 _SPACE = re.compile(r"\s+")
+WORD_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_")  # ASCII, as the database
+_W = "A-Za-z0-9_"
+
+
+def _spellings(first: str) -> tuple[str, ...]:
+    """'face' -> face-centred cubic, face centered cubic, face-centered-cubic, ... (with or without hyphens)."""
+    return tuple(f"{first}{a}cent{b}{c}cubic" for a in ("-", " ") for b in ("red", "ered") for c in (" ", "-"))
+
 
 # The listed terms per field and value (register 'curator_quote_checks'; changing it is a register change).
 TERMS: Mapping[str, Mapping[str, tuple[str, ...]]] = MappingProxyType({
     "test_type": MappingProxyType({"tension": ("tensile", "tension"), "compression": ("compressive", "compression")}),
-    "phase_class": MappingProxyType({"FCC": ("FCC", "face-centred cubic", "face-centered cubic"),
-                                     "BCC": ("BCC", "body-centred cubic", "body-centered cubic")}),
+    "phase_class": MappingProxyType({"FCC": ("FCC",) + _spellings("face"), "BCC": ("BCC",) + _spellings("body")}),
     "test_temperature_band": MappingProxyType({
         "room temperature": ("room temperature", "room-temperature", "ambient temperature"),
         "elevated": ("elevated temperature", "high temperature", "high-temperature"),
-        "cryogenic": ("cryogenic", "liquid nitrogen", "77 K")}),
+        "cryogenic": ("cryogenic", "liquid nitrogen", "liquid helium", "77 K")}),
     "microstructure": MappingProxyType({token: (token,) for token in ("FCC", "BCC", "B2", "HCP", "L12", "Laves")}),
 })
+CASE_SENSITIVE_TERMS = frozenset({"B2", "L12"})
+EXCLUDED_PHRASES = ("ultimate tensile strength", "ultimate tensile strengths")
+TESTING_WORDS = ("test", "tests", "tested", "testing", "loaded", "loading", "strained", "deformed", "strain rate")
+TESTING_FIELDS = frozenset({"test_type", "test_temperature_band", "test_temperature"})
+TEMPERATURE_RANGE = (-273.15, 3000.0)  # °C, the value check of a test temperature
+
+_SIGNS = "\\-+\u2212\u2013"  # hyphen-minus (escaped for a character class), plus, minus sign, en dash
+_NUMBER = rf"[{_SIGNS}]?[0-9]+(?:\.[0-9]+)?"
+_PLAIN = re.compile(rf"(?<![{_W}.{_SIGNS}])({_NUMBER})(?!\.?[0-9])[ ~]*\u00b0C")
+_LATEX = re.compile(rf"\\SI\{{({_NUMBER})\}}\{{\\degreeCelsius\}}")
 
 
 def collapse(text: str) -> str:
@@ -46,8 +84,22 @@ class Located:
     line: int  # 1-based, where the quote begins in the original document
 
 
+@dataclass(frozen=True)
+class Checked:
+    code: str | None              # None: passed
+    located: Located | None = None
+    term: str | None = None
+
+
+def _bounded(text: str, start: int, end: int) -> bool:
+    inside_at_start = start > 0 and text[start - 1] in WORD_CHARS and text[start] in WORD_CHARS
+    inside_at_end = end < len(text) and text[end - 1] in WORD_CHARS and text[end] in WORD_CHARS
+    return not inside_at_start and not inside_at_end
+
+
 def locate(quote: str, documents: Mapping[str, str]) -> Located | None:
-    """Where the collapsed quote first occurs, searching documents in path order; None if nowhere."""
+    """Where the collapsed quote first occurs at word boundaries, searching documents in path order;
+    None if nowhere."""
     wanted = collapse(quote)
     if not wanted:
         return None
@@ -65,29 +117,86 @@ def locate(quote: str, documents: Mapping[str, str]) -> Located | None:
                 collapsed.append(ch)
                 origin.append(i)
                 in_space = False
-        at = "".join(collapsed).find(wanted)
-        if at >= 0:
-            return Located(path, original.count("\n", 0, origin[at]) + 1)
+        text = "".join(collapsed)
+        at = text.find(wanted)
+        while at >= 0:
+            if _bounded(text, at, at + len(wanted)):
+                return Located(path, original.count("\n", 0, origin[at]) + 1)
+            at = text.find(wanted, at + 1)
     return None
 
 
+def _prepared(quote: str) -> str:
+    text = collapse(quote)
+    for phrase in EXCLUDED_PHRASES:
+        text = re.sub(rf"(?<![{_W}]){re.escape(phrase)}(?![{_W}])", " ", text, flags=re.IGNORECASE)
+    return text
+
+
+def _occurs(term: str, text: str) -> bool:
+    flags = 0 if term in CASE_SENSITIVE_TERMS else re.IGNORECASE
+    return re.search(rf"(?<![{_W}]){re.escape(term)}(?![{_W}])", text, flags) is not None
+
+
+def _as_decimal(written: str) -> Decimal:
+    return Decimal(written.translate(str.maketrans({"\u2212": "-", "\u2013": "-"})))
+
+
 def term_for(field: str, value, quote: str) -> str | None:
-    """The listed term the quote contains for this value, or None (see the module docstring)."""
-    lowered = quote.lower()
+    """The listed term the quote holds for this value, or None (see the module docstring)."""
+    text = _prepared(quote)
     if field == "test_temperature":
-        written = _number_text(value)
-        return written if written is not None and re.search(rf"(?<![\d.]){re.escape(written)}(?![\d])", quote) else None
+        if value_problem(field, value):
+            return None
+        wanted = Decimal(str(value))
+        for match in sorted([*_PLAIN.finditer(text), *_LATEX.finditer(text)], key=lambda m: m.start()):
+            if _as_decimal(match.group(1)) == wanted:
+                return match.group(1)
+        return None
     if field == "microstructure" and isinstance(value, str):
         parts = value.split("+")
-        terms = [next((t for t in TERMS["microstructure"].get(p, ()) if t.lower() in lowered), None) for p in parts]
+        terms = [next((t for t in TERMS["microstructure"].get(p, ()) if _occurs(t, text)), None) for p in parts]
         return terms[0] if parts and all(terms) else None  # every part checked; the first stored (it occurs)
-    for term in TERMS.get(field, {}).get(value, ()):
-        if term.lower() in lowered:
+    for term in TERMS.get(field, {}).get(value, ()) if isinstance(value, str) else ():
+        if _occurs(term, text):
             return term
     return None
 
 
-def _number_text(value) -> str | None:
-    if isinstance(value, bool) or not isinstance(value, (int, float)):
-        return None
-    return str(int(value)) if float(value).is_integer() else repr(float(value))
+def testing_word(quote: str) -> str | None:
+    text = collapse(quote)
+    return next((w for w in TESTING_WORDS if _occurs(w, text)), None)
+
+
+def value_problem(field: str, value: Any) -> str | None:
+    if field == "test_temperature":
+        ok = (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
+              and TEMPERATURE_RANGE[0] <= value <= TEMPERATURE_RANGE[1])
+        return None if ok else "value_not_allowed"
+    if field == "microstructure":
+        ok = isinstance(value, str) and value != "" and all(t in MICROSTRUCTURE_TOKENS for t in value.split("+"))
+        return None if ok else "value_not_allowed"
+    target = CURATION_TARGETS.get(field)
+    ok = target is not None and isinstance(value, str) and value in target["vocabulary"]
+    return None if ok else "value_not_allowed"
+
+
+def check(field: str, value: Any, quote: str, documents: Mapping[str, str]) -> Checked:
+    """Every check, in order (see the module docstring)."""
+    code = value_problem(field, value)
+    if code:
+        return Checked(code)
+    collapsed = collapse(quote) if isinstance(quote, str) else ""
+    if len(collapsed) < QUOTE_MIN_CHARS:
+        return Checked("quote_too_short")
+    if len(collapsed) > QUOTE_MAX_CHARS:
+        return Checked("quote_too_long")
+    located = locate(quote, documents)
+    if located is None:
+        return Checked("quote_not_found")
+    term = term_for(field, value, quote)
+    if term is None:
+        return Checked("term_missing", located)
+    if field in TESTING_FIELDS and testing_word(quote) is None:
+        return Checked("testing_word_missing", located, term)
+    return Checked(None, located, term)
diff --git a/hypocurate/pipeline/agents/spend.py b/hypocurate/pipeline/agents/spend.py
index 802fd80..b111ebf 100644
--- a/hypocurate/pipeline/agents/spend.py
+++ b/hypocurate/pipeline/agents/spend.py
@@ -3,8 +3,9 @@
 **Before every request** (`reserve`): one transaction checks the caps and records the call as
 started with its maximum cost; it is finished before the request is sent, so no model call ever
 happens inside a database transaction. A run call takes the run's lock first (the locking protocol);
-every reservation then takes one month-wide advisory lock, so two reservations can never both pass
-the monthly cap. The caps count every recorded call at its reported cost, or at its maximum cost
+every reservation then takes one month-wide advisory lock, and only then reads any total, so two
+reservations can never both pass the same cap or ceiling (the run's, the curation's or the month's)
+on a stale total. (Before the step 8a review fix a registration call read its total before the lock.) The caps count every recorded call at its reported cost, or at its maximum cost
 while no cost is known (`coalesce(cost, max_cost)`, as the totals views do):
 - a run: at most `RUN_CAP_USD` over all its calls;
 - a registration invocation (the Curator): at most `CURATION_CAP_USD` over its calls;
@@ -76,18 +77,22 @@ def reserve(engine: Engine, invocation_id: int, model: str, max_cost: Decimal, c
                            dict(i=invocation_id)).one_or_none()
         if inv is None:
             return ("refused", "invocation_unknown", None, None, None)
+        # Every lock before any total is read (step 8a review, finding 3): the run's lock first (the
+        # locking protocol), then the month-wide lock; read in the same order everywhere.
         if inv.scope == "run":
             status = conn.execute(text("SELECT hc_write_lock(p_run => :r)"), dict(r=inv.run_id)).scalar_one()
             stage = actual_stage(conn, inv.run_id, status)
+        else:
+            stage = "registration"
+        conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=MONTH_LOCK_KEY))
+        if inv.scope == "run":
             spent = conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
                                       "WHERE run_id = :r"), dict(r=inv.run_id)).scalar_one()
             cap, cap_code = RUN_CAP_USD, "spending_cap_run"
         else:
-            stage = "registration"
             spent = conn.execute(text("SELECT coalesce(sum(coalesce(cost, max_cost)), 0) FROM model_call "
                                       "WHERE invocation_id = :i"), dict(i=invocation_id)).scalar_one()
             cap, cap_code = CURATION_CAP_USD, "spending_cap_curation"
-        conn.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=MONTH_LOCK_KEY))
         month = conn.execute(text(_MONTH_TOTAL)).scalar_one()
         code = (cap_code if spent + max_cost > cap else
                 "ceiling_reached" if ceiling is not None and spent + max_cost > ceiling else
diff --git a/hypocurate/sources/curated.py b/hypocurate/sources/curated.py
index 7b69599..bb114a6 100644
--- a/hypocurate/sources/curated.py
+++ b/hypocurate/sources/curated.py
@@ -7,44 +7,126 @@ one); it never overrides a reported, converted or decided value. It is stored wi
 'assigned_from_source' and a citation: the documentation file, the line, the exact quote, and the
 proposal, model and settings version, who accepted it and when.
 
-A curation file that cannot be read exactly as written (wrong format, another source, a field that is
-not a target) refuses the whole version, like any malformed file (register 'malformed_files_refused').
+**The file is checked against the version it is attached to** (`check_curation`; step 8a review,
+finding 1), before it is sealed into a version (registration and seal-curation, `versions._register_in`)
+and again before it is applied (`curated_values`):
+- its format and source, and exactly the expected keys;
+- its base version: the fingerprint of the version's own files without `curation.json`, under the
+  version's interpretation settings, must be the one the file names (an export copied onto another
+  version of the same source, whose data or documentation differ, is refused);
+- every entry: a target field; the value, quote, document, line and term pass the current checks
+  (`quotes.check`) against that version's documentation, found on the stated line with the stated
+  term;
+- the acceptance fields: proposal and settings version positive integers, a model name, the
+  acceptor's name (1 to 200 characters, not blank), the acceptance time with its time zone, a note
+  or none (at most 2,000 characters).
+Anything else refuses the whole version, like any malformed file (register 'malformed_files_refused').
+
+What this cannot show: that a person really accepted the values. That is recorded in the database
+where the curation happened (`curator_decision`). **The one trusted import is the exact approved
+export replayed on the same base**: the file the owner approved and froze in `data/` (pinned by its
+manifest fingerprint), registered with the base version's own files (register 'curation_acceptance').
 """
 from __future__ import annotations
 
 import dataclasses
 import json
+from datetime import datetime
 from typing import Mapping
 
 from hypocurate.access.vocabulary import CURATION_TARGETS
 from hypocurate.sources.record import HARMONIZED_FIELDS, AdapterError, AdapterResult, Citation, Value
-from hypocurate.sources.versions import CURATION_PATH, SealedVersion
+from hypocurate.sources.versions import (CURATION_PATH, SealedVersion, file_role, files_digest,
+                                         version_identity)
 
 CURATION_FORMAT = 1
+DOCUMENT_KEYS = {"format", "source", "base_version", "values"}
 ENTRY_KEYS = {"value", "document", "line", "quote", "term", "proposal", "model", "agent_setting_version",
               "accepted_by", "accepted_at", "note"}
+ACCEPTOR_MAX, NOTE_MAX = 200, 2000  # the database's bounds on a decision (migration 0005)
+
+
+class CurationInvalid(ValueError):
+    """A curation file that does not check out against its version."""
+
+
+def _positive_int(value) -> bool:
+    return isinstance(value, int) and not isinstance(value, bool) and value >= 1
+
+
+def check_curation(files: Mapping[str, bytes], source_key: str, source_type: str, data_kind: str,
+                   grouping_unit: str) -> dict:
+    """The curation file in `files`, checked against the other files (see the module docstring);
+    CurationInvalid otherwise."""
+    from hypocurate.pipeline.agents import quotes
+    try:
+        doc = json.loads(files[CURATION_PATH].decode("utf-8"))
+    except (KeyError, UnicodeDecodeError, ValueError) as error:
+        raise CurationInvalid(f"not readable ({type(error).__name__})") from None
+    if not isinstance(doc, dict) or set(doc) != DOCUMENT_KEYS:
+        raise CurationInvalid("not the expected keys")
+    if doc["format"] != CURATION_FORMAT or doc["source"] != source_key:
+        raise CurationInvalid("format or source")
+    base_files = {p: c for p, c in files.items() if p != CURATION_PATH}
+    base = doc["base_version"]
+    if not (isinstance(base, dict) and set(base) == {"label", "fingerprint"} and isinstance(base["label"], str)
+            and base["label"].strip()):
+        raise CurationInvalid("base version")
+    if base["fingerprint"] != version_identity(files_digest(base_files), source_type, data_kind, grouping_unit):
+        raise CurationInvalid("the base version's fingerprint is not this version's")
+    documents = {}
+    for path, content in base_files.items():
+        if file_role(path) == "documentation":
+            try:
+                documents[path] = content.decode("utf-8")
+            except UnicodeDecodeError:
+                raise CurationInvalid(f"{path} is not UTF-8") from None
+    values = doc["values"]
+    if not isinstance(values, dict):
+        raise CurationInvalid("values")
+    for field, e in values.items():
+        if field not in CURATION_TARGETS or not isinstance(e, dict) or set(e) != ENTRY_KEYS:
+            raise CurationInvalid(f"entry {field!r}")
+        if not (isinstance(e["document"], str) and e["document"] in documents and isinstance(e["quote"], str)):
+            raise CurationInvalid(f"entry {field!r}: document")
+        result = quotes.check(field, e["value"], e["quote"], {e["document"]: documents[e["document"]]})
+        if result.code is not None:
+            raise CurationInvalid(f"entry {field!r}: {result.code}")
+        if not _positive_int(e["line"]) or result.located.line != e["line"] or result.term != e["term"]:
+            raise CurationInvalid(f"entry {field!r}: line or term")
+        if not (_positive_int(e["proposal"]) and _positive_int(e["agent_setting_version"])
+                and isinstance(e["model"], str) and e["model"].strip()):
+            raise CurationInvalid(f"entry {field!r}: proposal, model or settings version")
+        by = e["accepted_by"]
+        if not (isinstance(by, str) and by.strip() and len(by) <= ACCEPTOR_MAX):
+            raise CurationInvalid(f"entry {field!r}: acceptor")
+        try:
+            when = datetime.fromisoformat(e["accepted_at"]) if isinstance(e["accepted_at"], str) else None
+        except ValueError:
+            when = None
+        if when is None or when.tzinfo is None:
+            raise CurationInvalid(f"entry {field!r}: acceptance time")
+        if not (e["note"] is None or (isinstance(e["note"], str) and len(e["note"]) <= NOTE_MAX)):
+            raise CurationInvalid(f"entry {field!r}: note")
+    return doc
 
 
 def curated_values(version: SealedVersion) -> dict[str, Value]:
-    raw = version.files.get(CURATION_PATH)
-    if raw is None:
+    if CURATION_PATH not in version.files:
         return {}
     try:
-        doc = json.loads(raw.decode("utf-8"))
-        if doc.get("format") != CURATION_FORMAT or doc.get("source") != version.source_key:
-            raise ValueError("format or source")
-        out = {}
-        for field, e in doc["values"].items():
-            if field not in CURATION_TARGETS or set(e) != ENTRY_KEYS:
-                raise ValueError(f"entry {field!r}")
-            where = (f"line {int(e['line'])}; Curator proposal {int(e['proposal'])} ({e['model']}, settings version "
-                     f"{int(e['agent_setting_version'])}), accepted by {e['accepted_by']} on {e['accepted_at'][:10]}")
-            out[field] = Value(e["value"], HARMONIZED_FIELDS[field], "assigned_from_source",
-                               citation=Citation(f"{version.source_key}: {e['document']} (sealed with the source)",
-                                                 where, e["quote"]))
-        return out
-    except (ValueError, KeyError, TypeError, AttributeError) as error:
-        raise AdapterError(f"{CURATION_PATH}: cannot be read as a curation file ({error})") from None
+        doc = check_curation(version.files, version.source_key, version.source_type, version.data_kind,
+                             version.grouping_unit)
+    except CurationInvalid as error:
+        raise AdapterError(f"{CURATION_PATH}: cannot be read as a curation file for this version ({error})") from None
+    out = {}
+    for field, e in doc["values"].items():
+        where = (f"line {e['line']}; Curator proposal {e['proposal']} ({e['model']}, settings version "
+                 f"{e['agent_setting_version']}), accepted by {e['accepted_by']} on {e['accepted_at'][:10]}")
+        out[field] = Value(e["value"], HARMONIZED_FIELDS[field], "assigned_from_source",
+                           citation=Citation(f"{version.source_key}: {e['document']} (sealed with the source)",
+                                             where, e["quote"]))
+    return out
 
 
 def apply_curation(result: AdapterResult, version: SealedVersion) -> AdapterResult:
diff --git a/hypocurate/sources/versions.py b/hypocurate/sources/versions.py
index 06b01af..f72180b 100644
--- a/hypocurate/sources/versions.py
+++ b/hypocurate/sources/versions.py
@@ -225,6 +225,12 @@ def _register_in(conn: Connection, d: SourceDefinition, files: dict[str, bytes],
     """Registers and seals a version of `d` holding `files` (or finds the identical sealed one).
     `label`: the version's label (default: the definition's); a curated version names its own."""
     label = label or d.version_label
+    if CURATION_PATH in files:  # checked against the files it is sealed with (step 8a review, finding 1)
+        from hypocurate.sources.curated import CurationInvalid, check_curation
+        try:
+            check_curation(files, d.key, d.source_type, d.data_kind, d.grouping_unit)
+        except CurationInvalid as error:
+            raise RegistrationError(f"{CURATION_PATH}: not a curation of this version ({error})") from None
     digest = files_digest(files)
     identity = version_identity(digest, d.source_type, d.data_kind, d.grouping_unit)
     conn.execute(text(
````

### Tests (new and changed)

```diff
diff --git a/tests/pipeline_world.py b/tests/pipeline_world.py
index 7d29053..63da9f7 100644
--- a/tests/pipeline_world.py
+++ b/tests/pipeline_world.py
@@ -27,7 +27,10 @@ def registered_files(engine, files: dict[str, bytes]) -> dict[str, int]:
     """Registers each source key with one sealed version holding the given file (MPEA layout for
     'mpea' and 'controlled_duplicates'), with the settings of the code's source definition. Step 8a:
     a Texas A&M version also holds the frozen curation (the owner's accepted values: test type
-    tension, phase class FCC), as the real source does, since adapter version 3 no longer assigns them."""
+    tension, phase class FCC), as the real source does, since adapter version 3 no longer assigns them.
+    Step 8a review (finding 1): a curation file must belong to the version it is in, so the version
+    also holds the frozen documentation the quotes come from, and the file names this version's own
+    base fingerprint (the frozen file's entries otherwise unchanged)."""
     from hypocurate.sources.versions import DATA_DIR, SOURCES, file_role, files_digest, version_identity
     out = {}
     for key, content in files.items():
@@ -43,7 +46,14 @@ def registered_files(engine, files: dict[str, bytes]) -> dict[str, int]:
             import hashlib
             stored = {name: content}
             if d.curation_file:
-                stored[d.curation_file] = (DATA_DIR / d.directory / d.curation_file).read_bytes()
+                import json
+                for doc in d.documentation_files:
+                    stored[doc] = (DATA_DIR / d.directory / doc).read_bytes()
+                curation = json.loads((DATA_DIR / d.directory / d.curation_file).read_text(encoding="utf-8"))
+                curation["base_version"] = {"label": "test file", "fingerprint": version_identity(
+                    files_digest(stored), d.source_type, d.data_kind, d.grouping_unit)}
+                stored[d.curation_file] = (json.dumps(curation, indent=2, sort_keys=True, ensure_ascii=False)
+                                           + "\n").encode("utf-8")
             for path, data in stored.items():
                 conn.execute(text("INSERT INTO source_file (source_version_id, path, sha256, content, role) "
                                   "VALUES (:v, :p, :h, :c, :r)"),
diff --git a/tests/test_access_curator.py b/tests/test_access_curator.py
index 837a401..c57c50e 100644
--- a/tests/test_access_curator.py
+++ b/tests/test_access_curator.py
@@ -7,7 +7,8 @@ values), no claim (so not its direction), no plan, no other version. Every read
 run, naming the version and the invocation.
 
 What these tests do not cover: the model request built from this input (the agent-core tests,
-through the local stub provider), and anything the documentation itself says.
+through the local stub provider), and anything the documentation itself says: a paper may state
+outcome numbers, so the claim is "no data row", not "no outcome value whatsoever".
 """
 from __future__ import annotations
 
diff --git a/tests/test_access_files.py b/tests/test_access_files.py
index bc4fae6..c7dc1a4 100644
--- a/tests/test_access_files.py
+++ b/tests/test_access_files.py
@@ -189,3 +189,14 @@ def test_the_guarded_process_refuses_a_scratch_directory_that_would_open_anythin
                 f.unlink()
             made.rmdir()
     assert done.returncode != 0 and "unsuitable scratch directory" in done.stderr
+
+
+def test_a_guarded_timestamp_read_needs_no_zone_file(migrated_database, caplog):
+    """Step 8a review (owner, 2026-10-07): the database session's time zone is set to UTC when the engine
+    connects, so the driver reads no zone file to interpret a timestamp, and the guard refuses nothing.
+    Before, the server's 'Etc/UTC' made the driver open /usr/share/zoneinfo/Etc/UTC, which the guard
+    refused (the driver then fell back to UTC, with a warning)."""
+    import logging
+    caplog.set_level(logging.WARNING, logger="hypocurate.access")
+    assert probe([{"op": "timestamp"}], migrated_database) == ["ok UTC +00:00"]
+    assert [r.getMessage() for r in caplog.records if "file_guard" in r.getMessage()] == []
diff --git a/tests/test_agent_core.py b/tests/test_agent_core.py
index c3e576a..962f7cd 100644
--- a/tests/test_agent_core.py
+++ b/tests/test_agent_core.py
@@ -363,3 +363,158 @@ def test_a_reservation_waits_for_the_month_wide_lock(w, db):
     assert done.wait(10)
     thread.join()
     assert len(calls(w, inv)) == 1
+
+
+# --- review fixes (ChatGPT, 2026-10-07) -------------------------------------------------------------------------
+# Finding 3: the serialization lock is taken before the invocation's (or run's) total is read.
+
+def _waiting_for_advisory_locks(db, n, timeout=10.0):
+    import time
+    deadline = time.monotonic() + timeout
+    with db.connect() as conn:
+        while time.monotonic() < deadline:
+            waiting = conn.execute(text("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND NOT granted"))
+            if waiting.scalar_one() >= n:
+                return
+            conn.rollback()
+            time.sleep(0.05)
+    raise AssertionError(f"{n} reservations never waited for the month-wide lock")
+
+
+def _race(db, inv, amount, ceiling=None):
+    """Two reservations on the same invocation, released together: deterministic, not timing-dependent.
+    Both are made to wait for the month-wide lock first; if either read its total before taking the lock,
+    both would read the same stale total."""
+    outcomes = []
+
+    def go():
+        try:
+            outcomes.append(("ok", spend.reserve(db, inv, MODEL, Decimal(amount), ceiling)))
+        except spend.SpendingRefused as refused:
+            outcomes.append(("refused", refused.code))
+
+    with db.connect() as holder:
+        holder.execute(text("SELECT pg_advisory_xact_lock(:k)"), dict(k=spend.MONTH_LOCK_KEY))
+        threads = [threading.Thread(target=go) for _ in range(2)]
+        [t.start() for t in threads]
+        _waiting_for_advisory_locks(db, 2)
+        holder.rollback()
+    [t.join(30) for t in threads]
+    return sorted(outcomes)
+
+
+def test_two_reservations_on_one_invocation_cannot_both_pass_the_curation_cap(w, db):
+    inv = spent(w, registration(w), "1.70")
+    outcomes = _race(db, inv, "0.20")
+    assert [o[0] for o in outcomes] == ["ok", "refused"] and outcomes[1][1] == "spending_cap_curation"
+    assert w.val("SELECT sum(coalesce(cost, max_cost)) FROM model_call WHERE invocation_id = :i", i=inv) <= 2
+
+
+def test_two_reservations_on_one_invocation_cannot_both_pass_a_lower_ceiling(w, db):
+    inv = spent(w, registration(w), "0.30")
+    outcomes = _race(db, inv, "0.15", ceiling=Decimal("0.50"))
+    assert [o[0] for o in outcomes] == ["ok", "refused"] and outcomes[1][1] == "ceiling_reached"
+    assert w.val("SELECT sum(coalesce(cost, max_cost)) FROM model_call WHERE invocation_id = :i", i=inv) <= Decimal(
+        "0.50")
+
+
+def test_two_reservations_on_one_run_cannot_both_pass_the_run_cap(w, db):
+    rid = w.running(agents=True)
+    inv = spent(w, rid, "1.70", run=True)
+    outcomes, done = [], []
+
+    def go():
+        try:
+            outcomes.append(("ok", spend.reserve(db, inv, MODEL, Decimal("0.20"))))
+        except spend.SpendingRefused as refused:
+            outcomes.append(("refused", refused.code))
+
+    threads = [threading.Thread(target=go) for _ in range(2)]
+    [t.start() for t in threads]
+    [t.join(30) for t in threads]
+    assert sorted(o[0] for o in outcomes) == ["ok", "refused"]
+    assert [o[1] for o in outcomes if o[0] == "refused"] == ["spending_cap_run"]
+
+
+# Finding 4: a recording failure on any branch stops the call; the reservation stays at its maximum.
+
+class _NoUsage:
+    """An engine whose reply litellm could read but whose usage is empty (the engine's own branch)."""
+    requests = 0
+
+    def __init__(self, **_):
+        pass
+
+    def complete(self, request):
+        from types import SimpleNamespace
+        type(self).requests += 1
+        return SimpleNamespace(usage=None, finish_reason="stop", text="[[ ## answer ## ]]\nx", tool_calls=())
+
+    def close(self):
+        pass
+
+
+@pytest.mark.parametrize("branch", ["provider_failure", "unreadable_reply", "no_usage", "success"])
+def test_a_recording_failure_on_any_branch_stops_and_keeps_the_maximum(w, db, stub, monkeypatch, caplog, branch):
+    from hypocurate.pipeline.agents import libraries
+    inv = registration(w)
+
+    def broken(*a, **kw):
+        raise RuntimeError(f"database gone {PLANTED}")
+
+    monkeypatch.setattr(spend, "finish", broken)
+    if branch == "no_usage":
+        _NoUsage.requests = 0
+        monkeypatch.setattr(libraries, "litellm_engine", lambda **kw: _NoUsage(**kw))
+    stub.queue(*{"provider_failure": [sp.error(500, "api_error")] * 2,
+                 "unreadable_reply": [sp.no_usage(sp.fields(answer="x"))] * 2,
+                 "no_usage": [],
+                 "success": [sp.reply(sp.fields(answer="Kept?"))] * 2}[branch])
+    result = ask(db, inv, stub)
+    assert result.attempts == ["recording_failed"] and result.outputs is None
+    assert len(stub.requests) + _NoUsage.requests * (branch == "no_usage") == 1   # no further request
+    [row] = calls(w, inv)
+    assert row.status == "started"                                                 # counted at its maximum
+    assert w.val("SELECT sum(cap_cost) FROM model_call_totals_by_month") == row.max_cost
+    assert PLANTED not in caplog.text
+
+
+def test_a_reservation_that_cannot_be_written_sends_nothing(w, db, stub, monkeypatch, caplog):
+    inv = registration(w)
+
+    def broken(*a, **kw):
+        raise RuntimeError(f"database gone {PLANTED}")
+
+    monkeypatch.setattr(spend, "reserve", broken)
+    stub.queue(sp.reply(sp.fields(answer="x")))
+    result = ask(db, inv, stub)
+    assert result.attempts == ["reservation_failed"] and stub.requests == [] and calls(w, inv) == []
+    assert PLANTED not in caplog.text and "RuntimeError" in caplog.text
+
+
+# The overclaim on logs: the agent request path logs a failure's type and where it was raised, never its text.
+
+def test_provider_error_text_never_reaches_the_process_log(w, db, stub, caplog):
+    import logging
+    caplog.set_level(logging.DEBUG)
+    inv = registration(w)
+    stub.queue(sp.error(400, "invalid_request_error", f"bad request {PLANTED}"))
+    result = ask(db, inv, stub)
+    assert result.attempts == ["provider_rejected"]
+    assert "agent_request_failure" in caplog.text and PLANTED not in caplog.text
+
+
+# The request's headers (ChatGPT, question 1): exactly the transport's and the provider's own, no input in any.
+
+def test_the_request_headers_carry_nothing_of_the_input(w, db, stub):
+    inv = registration(w)
+    stub.queue(sp.reply(sp.fields(answer="Yes.")))
+    ask(db, inv, stub, question=f"Is it tension? {PLANTED}")
+    [request] = stub.requests
+    headers = {k.lower(): v for k, v in request["headers"].items()}
+    assert set(headers) == {"host", "accept-encoding", "connection", "user-agent", "anthropic-version", "accept",
+                            "content-type", "x-api-key", "content-length"}
+    assert headers["x-api-key"] == sp.DUMMY_KEY and headers["anthropic-version"] == "2023-06-01"
+    assert headers["user-agent"].startswith("litellm/") and headers["content-type"] == "application/json"
+    assert not any(PLANTED in v or "tension" in v for v in headers.values())
+    assert PLANTED in request["raw"].decode()  # the planted value is in the body, so the check above can fail
diff --git a/tests/test_curator.py b/tests/test_curator.py
index 1bb09e1..c493d96 100644
--- a/tests/test_curator.py
+++ b/tests/test_curator.py
@@ -328,3 +328,113 @@ def test_the_quote_checks_collapse_whitespace_only():
     assert quotes.term_for("microstructure", "FCC+BCC", "FCC only") is None
     assert quotes.term_for("test_temperature", 25, "tested at 25 °C") == "25"
     assert quotes.term_for("test_temperature", 25, "tested at 250 °C") is None
+
+
+# --- review finding 1 (ChatGPT, 2026-10-07): a curation file is checked against the version it is attached to ---
+# Before it is sealed into a version (registration, seal-curation) and again before it is applied (adapters.read):
+# the base version's fingerprint, every quote found again in that version's documentation on the stated line,
+# every value and term passing the current checks, and the acceptance fields present and valid. The one trusted
+# import is the exact approved export replayed on the same base (the frozen data/sources/tamu_fcc/curation.json).
+
+def frozen_curation() -> dict:
+    from hypocurate.sources.versions import DATA_DIR
+    return json.loads((DATA_DIR / "sources" / "tamu_fcc" / "curation.json").read_text(encoding="utf-8"))
+
+
+def encode(doc: dict) -> bytes:
+    return (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
+
+
+def sealed_as(base, files):
+    from hypocurate.sources.versions import SealedVersion
+    digest = files_digest(files)
+    return SealedVersion(base.id, base.source_key, base.label, base.source_type, base.data_kind, base.grouping_unit,
+                         base.sealed_at, digest, version_identity(digest, base.source_type, base.data_kind,
+                                                                  base.grouping_unit), files)
+
+
+def refused_everywhere(db, files) -> None:
+    """Registration refuses the files, and an adapter refuses a version holding them."""
+    from hypocurate.db.retry import run_transaction
+    from hypocurate.sources.record import AdapterError
+    from hypocurate.sources.versions import SOURCES, RegistrationError, _register_in
+    base = version_of(db, "tamu_fcc")
+    with pytest.raises(RegistrationError, match="curation.json"):
+        run_transaction(db, lambda conn: _register_in(conn, SOURCES["tamu_fcc"], files, base.sealed_at.date()))
+    with pytest.raises(AdapterError, match="curation.json"):
+        adapters.read(sealed_as(base, files))
+
+
+def test_the_frozen_export_on_its_own_base_is_accepted(db):
+    register_base(db)
+    base = version_of(db, "tamu_fcc")
+    files = {**dict(base.files), CURATION_PATH: encode(frozen_curation())}
+    records = adapters.read(sealed_as(base, files)).records
+    assert {records[0].harmonized[f].value for f in ("test_type", "phase_class")} == {"tension", "FCC"}
+
+
+def test_an_export_copied_onto_another_base_is_refused(db):
+    """The reviewer's case: the documentation (or data) changed, so the export's base fingerprint no longer
+    matches, even though every quote is still found."""
+    register_base(db)
+    base = version_of(db, "tamu_fcc")
+    changed = dict(base.files)
+    changed["documentation/main.tex"] = changed["documentation/main.tex"] + b"\n% a later revision\n"
+    refused_everywhere(db, {**changed, CURATION_PATH: encode(frozen_curation())})
+
+
+def _set(path, value):
+    def change(doc):
+        target = doc
+        for key in path[:-1]:
+            target = target[key]
+        if value is KeyError:
+            del target[path[-1]]
+        else:
+            target[path[-1]] = value
+    return change
+
+
+T = ("values", "test_type")
+@pytest.mark.parametrize("change", [
+    _set(("base_version", "fingerprint"), "0" * 64),
+    _set(("base_version", "label"), ""),
+    _set(("source",), "mpea"),
+    _set(T + ("document",), "documentation/absent.tex"),
+    _set(T + ("document",), "Grain_Size_Summary_v3.xlsx"),
+    _set(T + ("quote",), "Quasistatic tensile testing was used everywhere in this imaginary paper."),
+    _set(T + ("quote",), "uasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers"),
+    _set(T + ("line",), 178),
+    _set(T + ("term",), "tension"),
+    _set(T + ("value",), "compression"),
+    _set(T + ("value",), "shear"),
+    _set(T + ("accepted_by",), "  "),
+    _set(T + ("accepted_by",), None),
+    _set(T + ("accepted_at",), "yesterday"),
+    _set(T + ("accepted_at",), "2026-10-06T23:17:06"),        # no time zone
+    _set(T + ("proposal",), "5"),
+    _set(T + ("proposal",), True),
+    _set(T + ("proposal",), 0),
+    _set(T + ("agent_setting_version",), 0),
+    _set(T + ("model",), ""),
+    _set(T + ("note",), 5),
+    _set(T + ("accepted_at",), KeyError),
+    _set(("values", "microstructure"), {}),
+])
+def test_an_export_that_does_not_check_out_is_refused(db, change):
+    register_base(db)
+    base = version_of(db, "tamu_fcc")
+    doc = frozen_curation()
+    change(doc)
+    refused_everywhere(db, {**dict(base.files), CURATION_PATH: encode(doc)})
+
+
+def test_a_quote_that_fails_the_current_term_checks_is_refused_on_import(db):
+    """A quote that is found, on its line, but no longer passes the checks (here: no testing word for a
+    temperature band) is refused like any other."""
+    register_base(db)
+    base = version_of(db, "tamu_fcc")
+    doc = frozen_curation()
+    doc["values"]["test_temperature_band"] = {**doc["values"]["phase_class"], "value": "room temperature",
+                                              "term": "room temperature"}
+    refused_everywhere(db, {**dict(base.files), CURATION_PATH: encode(doc)})
diff --git a/tests/test_data_model.py b/tests/test_data_model.py
index 9ac1872..a7b4729 100644
--- a/tests/test_data_model.py
+++ b/tests/test_data_model.py
@@ -1077,14 +1077,15 @@ def test_model_call_usage_rules(w):
 
 def test_totals_are_the_sum_of_the_calls_and_unreported_calls_count_at_their_bound(w):
     rid = w.running(agents=True)
-    planner, curator = w.stage(rid), w.stage(rid, "curator", "curator")
+    # Step 8a review (finding 6): the Curator has no run invocation, so the second stage is the Critic's.
+    planner, critic = w.stage(rid), w.stage(rid, "critic", "critic")
     ok = w.call(rid, planner, max_cost=0.50)
     w.finish_call(ok, "succeeded", (1000, 200, 100, 0.0123))
     charged = w.call(rid, planner, max_cost=0.40)
     w.finish_call(charged, "failed", (500, 0, 0, 0.0040))         # failed, but the provider reported usage
-    lost = w.call(rid, curator, max_cost=0.30)
+    lost = w.call(rid, critic, max_cost=0.30)
     w.finish_call(lost, "failed", None)                           # failed without usage: may still be charged
-    w.call(rid, curator, max_cost=0.20)                           # still started (e.g. the worker died)
+    w.call(rid, critic, max_cost=0.20)                            # still started (e.g. the worker died)
     columns = "calls, input_tokens, output_tokens, cached_tokens, reported_cost, unconfirmed_calls, " \
               "unconfirmed_cost_bound, cap_cost"
     run_total = w.rows(f"SELECT {columns} FROM model_call_totals_by_run WHERE run_id = :r", r=rid)[0]
@@ -1092,7 +1093,7 @@ def test_totals_are_the_sum_of_the_calls_and_unreported_calls_count_at_their_bou
     by_stage = w.rows(f"SELECT stage, {columns} FROM model_call_totals_by_stage WHERE run_id = :r ORDER BY stage",
                       r=rid)
     assert [(s, float(rep), float(cap)) for s, _, _, _, _, rep, _, _, cap in by_stage] == [
-        ("curator", 0.0, 0.50), ("planner", 0.0163, 0.0163)]
+        ("critic", 0.0, 0.50), ("planner", 0.0163, 0.0163)]
     query = w.rows("SELECT h.id FROM hypothesis h JOIN hypothesis_version v ON v.hypothesis_id = h.id "
                    "JOIN run r ON r.hypothesis_version_id = v.id WHERE r.id = :r", r=rid)[0][0]
     assert float(w.val("SELECT cap_cost FROM model_call_totals_by_query WHERE hypothesis_id = :h", h=query)) == 0.5163
@@ -1107,7 +1108,7 @@ def test_small_costs_are_stored_exactly(w):
     rid = w.running(agents=True)
     call = w.call(rid, w.stage(rid), max_cost=Decimal("1E-12"))
     w.finish_call(call, "succeeded", (1, 1, 0, Decimal("3E-13")))
-    w.call(rid, w.stage(rid, "curator", "curator"), max_cost=Decimal("2E-12"))
+    w.call(rid, w.stage(rid, "critic", "critic"), max_cost=Decimal("2E-12"))  # step 8a review: not the Curator
     row = w.rows("SELECT reported_cost, unconfirmed_cost_bound, cap_cost FROM model_call_totals_by_run "
                  "WHERE run_id = :r", r=rid)[0]
     assert row == (Decimal("3E-13"), Decimal("2E-12"), Decimal("2.3E-12"))
diff --git a/tests/test_migrations_step8a.py b/tests/test_migrations_step8a.py
index 2de69fe..1ccc606 100644
--- a/tests/test_migrations_step8a.py
+++ b/tests/test_migrations_step8a.py
@@ -367,7 +367,7 @@ def test_one_proposal_per_field_per_invocation_for_its_own_version(w, curation):
     other = sealed_version_with_documentation(w, label="other")
     w.rejected(PROPOSAL, "its invocation's source version", i=inv, v=other, **proposal(f="phase_class"))
     rid = w.running(agents=True)
-    run_inv = w.invocation(rid, w.stage(rid, "curator", "curator"), role="curator")
+    run_inv = w.invocation(rid, w.stage(rid))  # a run invocation (the Curator never has one: review finding 6)
     w.rejected(PROPOSAL, "registration invocation of the curator", i=run_inv, v=v, **proposal(f="phase_class"))
 
 
@@ -396,3 +396,152 @@ def test_the_database_sets_the_decision_time(w, curation):
               "VALUES (:p, 'accepted', 'K', now() - interval '3 days')", p=passed)
     assert w.val("SELECT decided_at > now() - interval '1 minute' FROM curator_decision WHERE proposal_id = :p",
                  p=passed)
+
+
+# --- review fixes (ChatGPT, 2026-10-07; owner's term-check changes) ------------------------------------
+# Finding 6: the Curator never runs within a run, enforced when the invocation is created.
+
+def test_a_run_invocation_of_the_curator_is_refused(w):
+    rid = w.running(agents=True)
+    stage = w.stage(rid, "curator", "curator")   # a running stage with that role, and its setting recorded
+    sql, params = run_invocation(w, rid, stage, role="curator")
+    w.rejected(sql, "ck_agent_invocation_shape", **params)
+
+
+# Finding 2: the database checks the value, its type and vocabulary, and its term; nothing it needs is NULL.
+
+@pytest.mark.parametrize("change", [
+    dict(l=None), dict(t=None), dict(q=None), dict(d=None), dict(val=None), dict(val="null"),
+])
+def test_a_passed_proposal_with_a_missing_part_is_refused(w, curation, change):
+    """A NULL must not turn the completeness check into UNKNOWN (which a CHECK accepts); JSON null is
+    not a value either."""
+    v, inv = curation
+    w.rejected(PROPOSAL, "ck_curator_proposal_proposed_complete", i=inv, v=v, **proposal(**change))
+
+
+def test_json_null_is_never_stored_as_a_value(w, curation):
+    v, inv = curation
+    w.rejected(PROPOSAL, "ck_curator_proposal_value_not_json_null", i=inv, v=v,
+               **proposal(f="phase_class", st="refused", val="null", t=None, rc="value_not_allowed"))
+    assert w.val(PROPOSAL, i=inv, v=v, **proposal(f="phase_class", st="refused", val=None, t=None,
+                                                  rc="value_not_allowed"))
+
+
+@pytest.mark.parametrize("change", [
+    dict(val='"compression"'),                          # the reviewer's case: the term belongs to another value
+    dict(val='"compression"', t="compression"),         # a term that is not in the quote
+    dict(val='"shear"'),                                # not in the vocabulary
+    dict(val='5'),                                      # not a string
+    dict(val='["tension"]'),
+    dict(t="tension"),                                  # a listed term, but not in the quote
+    dict(t="Quasistatic"),                              # in the quote, but not a listed term
+    dict(t="TENSILE"),                                  # not as listed
+    dict(f="phase_class", val='"FCC"', t="tensile"),    # a term of another field
+    dict(f="test_temperature", val='"25"', t="25"),     # a temperature is a number
+    dict(f="microstructure", val='"FCC+B2"', t="FCC"),  # every part needs its term in the quote
+    dict(f="microstructure", val='"FCC+"', t="FCC"),
+])
+def test_a_value_that_does_not_match_its_term_is_refused(w, curation, change):
+    v, inv = curation
+    w.rejected(PROPOSAL, "ck_curator_proposal_proposed_complete", i=inv, v=v, **proposal(**change))
+
+
+def test_the_matching_value_and_term_are_stored(w, curation):
+    v, inv = curation
+    assert w.val(PROPOSAL, i=inv, v=v, **proposal())
+    assert w.val(PROPOSAL, i=inv, v=v, **proposal(f="microstructure", val='"FCC"', t="FCC",
+                                                  q="The dataset contains 94 FCC alloy conditions in the system.",
+                                                  l=2))
+
+
+def test_a_quote_must_begin_and_end_at_a_word_boundary_in_the_document(w, curation):
+    v, inv = curation
+    w.rejected(PROPOSAL, "must occur", i=inv, v=v, **proposal(q=QUOTE[1:]))          # "uasistatic …"
+    w.rejected(PROPOSAL, "must occur", i=inv, v=v, **proposal(q=QUOTE[:-1]))         # "… offset Y"
+
+
+def test_the_databases_term_list_is_the_codes():
+    from hypocurate.pipeline.agents import quotes
+    listed = {(f, v, t) for f, by_value in quotes.TERMS.items() for v, terms in by_value.items() for t in terms}
+    assert {(f, v, t) for f, v, t in M0005.CURATOR_TERMS} == listed and len(M0005.CURATOR_TERMS) == len(listed)
+    assert set(M0005.CASE_SENSITIVE_TERMS) == set(quotes.CASE_SENSITIVE_TERMS)
+    assert tuple(M0005.TESTING_WORDS) == tuple(quotes.TESTING_WORDS)
+    assert tuple(M0005.EXCLUDED_PHRASES) == tuple(quotes.EXCLUDED_PHRASES)
+    assert (M0005.QUOTE_MIN, M0005.QUOTE_MAX) == (quotes.QUOTE_MIN_CHARS, quotes.QUOTE_MAX_CHARS) == (30, 600)
+
+
+# The database and the code agree on every case below: a quote the code passes is stored with the
+# code's term and line; for a quote the code refuses, the database refuses every term it could be given.
+AGREEMENT = [
+    ("test_type", "tension", "Specimens were tested in tension at a constant crosshead speed."),
+    ("test_type", "tension", "Specimens were tested after extension of the gauge section by machining."),
+    ("test_type", "tension", "The ultimate tensile strength was tested for each of the alloys."),
+    ("test_type", "tension", "The ultimate tensile strength and tensile ductility were tested for each."),
+    ("test_type", "tension", "Dog-bone tensile specimens were cut from each plate by machining."),
+    ("test_type", "tension", "Specimens were pulled in tension at a strain rate of 0.001 per second."),
+    ("test_type", "compression", "Cylinders were tested under compressive loading at room temperature."),
+    ("phase_class", "FCC", "All alloys were designed as fcc solid solutions in this study."),
+    ("phase_class", "FCC", "All alloys were designed as face centered cubic solid solutions."),
+    ("phase_class", "BCC", "All alloys were designed as BCCs and HCPs in this study, then."),
+    ("microstructure", "B2", "The Nb25 alloys were examined by diffraction after annealing."),
+    ("microstructure", "B2", "Ordered B2 precipitates were found after annealing in every alloy."),
+    ("microstructure", "B2", "Ordered b2 precipitates were found after annealing in every alloy."),
+    ("microstructure", "L12", "Coherent L1$_2$ precipitates were found after ageing in every alloy."),
+    ("microstructure", "FCC+B2", "Each alloy had an FCC matrix with B2 particles after annealing."),
+    ("microstructure", "FCC+B2", "Each alloy had an FCC matrix with Nb2 particles after annealing."),
+    ("test_temperature_band", "room temperature", "All specimens were tested at room temperature in air."),
+    ("test_temperature_band", "room temperature", "The plates were cold rolled at room temperature to 60%."),
+    ("test_temperature_band", "cryogenic", "Further specimens were tested in liquid helium baths."),
+    ("test_temperature", 25, "All the specimens were tested at 25 °C in laboratory air."),
+    ("test_temperature", 25, "All the specimens were tested at 25~°C in laboratory air."),
+    ("test_temperature", 25, "All the specimens were tested at \\SI{25}{\\degreeCelsius} in air."),
+    ("test_temperature", 25, "All the specimens were tested at 25.0 °C in laboratory air."),
+    ("test_temperature", 25, "All the specimens were tested at −25 °C in laboratory air."),
+    ("test_temperature", 25, "All the specimens were tested at -25 °C in laboratory air."),
+    ("test_temperature", 25, "All the specimens were tested at 25.5 °C in laboratory air."),
+    ("test_temperature", 25, "All the specimens were tested at 125 °C in laboratory air."),
+    ("test_temperature", 25, "All the specimens were tested between 20-25 °C in laboratory air."),
+    ("test_temperature", 25, "All the specimens were tested at 25 K in laboratory air, as usual."),
+    ("test_temperature", 25, "All the plates were annealed and cooled to 25 °C in still air."),
+    ("test_temperature", -196, "All the specimens were tested at −196 °C in liquid nitrogen."),
+    ("test_temperature", 25.5, "All the specimens were tested at 25.5 °C in laboratory air."),
+]
+
+
+def _stored(engine, params) -> bool:
+    with engine.connect() as conn:
+        trans = conn.begin()
+        try:
+            conn.execute(text(PROPOSAL), params)
+            return True
+        except IntegrityError:
+            return False
+        finally:
+            trans.rollback()
+
+
+def test_the_database_and_the_code_agree_on_every_case(w):
+    import json
+    from hypocurate.pipeline.agents import quotes
+    document = "\n".join(q for _, _, q in AGREEMENT) + "\n"
+    v = w.new_version("tamu_fcc", "agreement")
+    w.add_file(v, "table.csv", b"a,b,agreement\n")
+    w.add_file(v, "documentation/cases.md", document.encode(), role="documentation")
+    w.seal(v)
+    inv = w.val(REGISTRATION, v=v, o="curator", a=curator_setting(w))
+    docs = {"documentation/cases.md": document}
+    passed = 0
+    for field, value, quote in AGREEMENT:
+        result = quotes.check(field, value, quote, docs)
+        base = dict(i=inv, v=v, f=field, st="proposed", val=json.dumps(value), q=quote, d="documentation/cases.md",
+                    l=result.located.line if result.located else 1, rc=None)
+        if result.code is None:
+            passed += 1
+            assert _stored(w.e, {**base, "t": result.term}), (field, value, quote)
+            continue
+        listed = [t for p in str(value).split("+") for t in quotes.TERMS.get(field, {}).get(p, ())]
+        numbers = re.findall(r"[-+−–]?\d+(?:\.\d+)?", quote)
+        for term in listed + numbers + [str(value)]:
+            assert not _stored(w.e, {**base, "t": term}), (field, value, quote, term)
+    assert 0 < passed < len(AGREEMENT)
diff --git a/tests/test_quote_checks.py b/tests/test_quote_checks.py
new file mode 100644
index 0000000..e0988e9
--- /dev/null
+++ b/tests/test_quote_checks.py
@@ -0,0 +1,194 @@
+"""Step 8a review fixes (ChatGPT finding 5; owner's term-check changes a-g, 2026-10-07): the checks on
+a Curator proposal's quote, in code (`quotes.check`). The database's own copy of these checks is
+tested against this one in tests/test_migrations_step8a.py.
+
+The rules: the quote is found in one documentation file after collapsing runs of whitespace, and it
+begins and ends at a word boundary there; 30 to 600 characters; it holds a listed term for the value
+as a whole word (case-insensitive, except B2 and L12), after collapsing whitespace and setting aside
+"ultimate tensile strength"; for test type, temperature band and test temperature it also holds a
+testing word; a test temperature is a complete signed number equal to the value and followed by a
+Celsius unit in a form found in the frozen documents ("°C", or LaTeX \\SI{n}{\\degreeCelsius}).
+
+What these tests do not show: that a sentence that passes supports the value. A person decides that.
+"""
+from __future__ import annotations
+
+import pytest
+
+from hypocurate.pipeline.agents import quotes
+from hypocurate.sources.versions import DATA_DIR
+
+PROPOSAL_5 = ("Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation "
+              "tests provided the HV.")
+PROPOSAL_2 = "The dataset contains 94 FCC alloy conditions in the Al--Co--Cr--Cu--Fe--Mn--Ni--V system."
+
+
+def frozen_documents() -> dict[str, str]:
+    folder = DATA_DIR / "sources" / "tamu_fcc" / "documentation"
+    return {f"documentation/{p.name}": p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.tex"))}
+
+
+def checked(field, value, quote, document=None):
+    """The check's code for a quote that is itself the whole document (so it is always found)."""
+    return quotes.check(field, value, quote, {"documentation/notes.md": document if document is not None else quote})
+
+
+# --- g. the owner's two accepted proposals under the new rules ------------------------------------------
+
+@pytest.mark.parametrize("field, value, quote, line, term", [
+    ("test_type", "tension", PROPOSAL_5, 177, "tensile"),
+    ("phase_class", "FCC", PROPOSAL_2, 173, "FCC"),
+])
+def test_the_owners_two_accepted_proposals_still_pass(field, value, quote, line, term):
+    result = quotes.check(field, value, quote, frozen_documents())
+    assert (result.code, result.located, result.term) == (
+        None, quotes.Located("documentation/main.tex", line), term)
+
+
+# --- a. whole words; case ---------------------------------------------------------------------------------
+
+@pytest.mark.parametrize("field, value, quote, code", [
+    ("microstructure", "B2", "The Nb25 alloys were examined by diffraction after annealing.", "term_missing"),
+    ("microstructure", "B2", "Ordered B2 precipitates were found after annealing in every alloy.", None),
+    ("microstructure", "B2", "Ordered b2 precipitates were found after annealing in every alloy.", "term_missing"),
+    ("microstructure", "L12", "Coherent L12 precipitates were found after ageing in every alloy.", None),
+    ("microstructure", "L12", "Coherent l12 precipitates were found after ageing in every alloy.", "term_missing"),
+    ("microstructure", "FCC", "All alloys showed a single fcc phase after the final anneal.", None),
+    ("microstructure", "HCP", "All alloys showed a single hcp phase after the final anneal.", None),
+    ("microstructure", "FCC+B2", "Each alloy had an FCC matrix with B2 particles after annealing.", None),
+    ("microstructure", "FCC+B2", "Each alloy had an FCC matrix with Nb2 particles after annealing.", "term_missing"),
+    ("phase_class", "FCC", "All alloys were designed as fcc solid solutions in this study.", None),
+    ("phase_class", "BCC", "All alloys were designed as BCCs and HCPs in this study, then.", "term_missing"),
+    ("test_type", "tension", "Specimens were tested after extension of the gauge section by machining.", "term_missing"),
+    ("test_type", "tension", "Specimens were tested in tension at a constant crosshead speed.", None),
+    ("test_type", "tension", "The ultimate tensile strength was tested for each of the alloys.", "term_missing"),
+    ("test_type", "tension", "The ultimate tensile strength and tensile ductility were tested for each.", None),
+    ("test_type", "compression", "Cylinders were tested under compressive loading at room temperature.", None),
+    ("test_type", "compression", "Cylinders were tested under precompression before the main experiment.",
+     "term_missing"),
+])
+def test_terms_match_whole_words_with_the_stated_case_rules(field, value, quote, code):
+    assert checked(field, value, quote).code == code
+
+
+def test_whitespace_is_collapsed_for_terms_as_for_locating_the_quote():
+    quote = "All specimens were tested at room\ntemperature in laboratory air, every time."
+    result = checked("test_temperature_band", "room temperature", quote)
+    assert (result.code, result.term) == (None, "room temperature")
+
+
+# --- b. a testing word for test type, temperature band and test temperature -----------------------------
+
+@pytest.mark.parametrize("field, value, quote, code", [
+    ("test_temperature_band", "room temperature",
+     "The plates were cold rolled at room temperature to a 60% reduction in thickness.", "testing_word_missing"),
+    ("test_temperature_band", "room temperature",
+     "The plates were deformed at room temperature to a 60% reduction in thickness.", None),
+    ("test_type", "tension", "Dog-bone tensile specimens were cut from each plate by machining.", "testing_word_missing"),
+    ("test_type", "tension", "Dog-bone specimens were loaded in tension until they broke.", None),
+    ("test_type", "tension", "Dog-bone specimens were attested to be tensile by the supplier, sure.",
+     "testing_word_missing"),
+    ("test_type", "tension", "Specimens were pulled in tension at a strain rate of 0.001 per second.", None),
+    ("test_temperature", 25, "Plates were annealed and then cooled to 25 °C in still laboratory air.",
+     "testing_word_missing"),
+    ("test_temperature", 25, "All the specimens were strained at 25 °C in still laboratory air.", None),
+    ("phase_class", "FCC", "The dataset contains 94 FCC alloy conditions in one alloy system.", None),  # not needed
+])
+def test_test_conditions_need_a_testing_word(field, value, quote, code):
+    assert checked(field, value, quote).code == code
+
+
+# --- c. and finding 5: a test temperature is a complete number with a Celsius unit ------------------------
+
+@pytest.mark.parametrize("value, quote, term", [
+    (25, "All the specimens were tested at 25 °C in laboratory air.", "25"),
+    (25, "All the specimens were tested at 25°C in laboratory air.", "25"),
+    (25, "All the specimens were tested at 25~°C in laboratory air.", "25"),
+    (25, "All the specimens were tested at \\SI{25}{\\degreeCelsius} in laboratory air.", "25"),
+    (25, "All the specimens were tested at 25.0 °C in laboratory air.", "25.0"),
+    (25.5, "All the specimens were tested at 25.5 °C in laboratory air.", "25.5"),
+    (-196, "All the specimens were tested at −196 °C in liquid nitrogen.", "−196"),
+    (-196, "All the specimens were tested at -196 °C in liquid nitrogen.", "-196"),
+    (25, "Tested at 300 °C, and also tested at 25 °C in laboratory air.", "25"),
+])
+def test_a_temperature_is_the_whole_number_with_its_unit(value, quote, term):
+    result = checked("test_temperature", value, quote)
+    assert (result.code, result.term) == (None, term)
+
+
+@pytest.mark.parametrize("value, quote", [
+    (25, "All the specimens were tested at −25 °C in laboratory air."),   # another temperature
+    (25, "All the specimens were tested at -25 °C in laboratory air."),
+    (25, "All the specimens were tested at 25.5 °C in laboratory air."),
+    (25, "All the specimens were tested at 125 °C in laboratory air."),
+    (25, "All the specimens were tested at 2.25 °C in laboratory air."),
+    (25, "All the specimens were tested between 20-25 °C in laboratory air."),  # a range: refused (safe)
+    (25, "All the specimens were tested at 25 MPa in laboratory air and more."),  # no unit
+    (25, "All the specimens were tested at 25 and then held in laboratory air."),
+    (298, "All the specimens were tested at 298 K in laboratory air, as usual."),  # kelvin: refused (f)
+    (25, "All the specimens were tested at 25 $^\\circ$C in laboratory air."),  # a form not in the documents
+    (25, "All the specimens were tested at \\SI{125}{\\degreeCelsius} in laboratory air."),
+    (-196, "All the specimens were tested at 196 °C in laboratory air, as usual."),
+])
+def test_another_number_or_no_celsius_unit_is_refused(value, quote):
+    assert checked("test_temperature", value, quote).code == "term_missing"
+
+
+# --- d. spelling variants -------------------------------------------------------------------------------------
+
+@pytest.mark.parametrize("field, value, phrase", [
+    ("phase_class", "FCC", "face-centred cubic"), ("phase_class", "FCC", "face centered cubic"),
+    ("phase_class", "FCC", "face-centered-cubic"), ("phase_class", "FCC", "face centred cubic"),
+    ("phase_class", "BCC", "body-centred cubic"), ("phase_class", "BCC", "body centered cubic"),
+    ("phase_class", "BCC", "body-centered-cubic"),
+    ("test_temperature_band", "cryogenic", "liquid helium"),
+])
+def test_spelling_variants_are_listed(field, value, phrase):
+    quote = f"All the alloys tested here were {phrase} in the study, without exception."
+    assert checked(field, value, quote).code is None
+
+
+# --- e. at most 600 characters, beginning and ending at a word boundary --------------------------------------
+
+def test_a_quote_is_at_most_600_characters():
+    body = "Specimens were tested in tension " + "and again " * 60
+    at_600 = body[:599].rstrip() + "."
+    assert len(quotes.collapse(at_600)) <= quotes.QUOTE_MAX_CHARS == 600
+    assert checked("test_type", "tension", at_600).code is None
+    over = at_600[:-1] + " and again."
+    assert len(quotes.collapse(over)) > 600 and checked("test_type", "tension", over).code == "quote_too_long"
+
+
+@pytest.mark.parametrize("quote, found", [
+    ("The specimens were tested in tension throughout the study.", True),
+    ("he specimens were tested in tension throughout the study.", False),     # begins inside a word
+    ("The specimens were tested in tension throughout the stu", False),       # ends inside a word
+    ("specimens were tested in tension throughout the study", True),
+])
+def test_a_quote_begins_and_ends_at_a_word_boundary(quote, found):
+    docs = {"documentation/a.md": "Intro.\nThe specimens were tested in tension throughout the study.\n"}
+    assert (quotes.locate(quote, docs) is not None) is found
+
+
+def test_a_later_occurrence_at_word_boundaries_is_the_one_found():
+    docs = {"documentation/a.md": "Xspecimens were tested in tension at all times.\n"
+                                  "Then: specimens were tested in tension at all times.\n"}
+    assert quotes.locate("specimens were tested in tension at all times.", docs) == quotes.Located(
+        "documentation/a.md", 2)
+
+
+# --- f. the safe refusals the register records ------------------------------------------------------------------
+
+@pytest.mark.parametrize("field, value, quote, code", [
+    ("test_type", "tension", "Tested in tension.", "quote_too_short"),                    # under 30 characters
+    ("test_temperature", 25, "All the specimens were tested at 298.15 K in laboratory air.", "term_missing"),
+    ("microstructure", "L12", "Coherent L1$_2$ precipitates were found after ageing in every alloy.", "term_missing"),
+])
+def test_the_recorded_safe_refusals(field, value, quote, code):
+    assert checked(field, value, quote).code == code
+
+
+def test_the_value_is_checked_first_and_json_null_is_never_a_value():
+    for field, value in (("test_type", None), ("test_temperature", None), ("test_temperature", True),
+                         ("test_temperature", "25"), ("microstructure", "FCC+"), ("microstructure", "Sec.+FCC+x")):
+        assert quotes.value_problem(field, value) == "value_not_allowed", (field, value)
```


## 10. Register changes and scripts

7 entries new or changed (of 123): `quasistatic_tests`, `spending_caps`, `access_context_dispatcher`, `curator_quote_checks`, `curation_acceptance`, `request_failure_policy`, `database_session_time_zone`.

### `quasistatic_tests`

```json
{
 "key": "quasistatic_tests",
 "name": "Tests assumed quasistatic",
 "state": "in_force",
 "statement": "Tests are assumed to be quasistatic. Loading rate is not filtered.",
 "value": {
  "text": "quasistatic; no loading-rate rule",
  "unit": null
 },
 "category": "scientific",
 "affects": "Which records are pooled; a high-rate test would be pooled with quasistatic ones.",
 "reason": "Neither source has a loading-rate field.",
 "evidence": [
  "PRD 5.2 (exclusion menu has no rate rule); the MPEA and Texas A&M column lists.",
  "Texas A&M: data/sources/tamu_fcc/documentation/main.tex line 177 (accepted Curator proposal 5, owner, 2026-10-06): \"Quasistatic tensile testing was used to determine 0.2\\% offset YS, while Vickers indentation tests provided the HV.\""
 ],
 "decided": {
  "by": "implicit in PRD v1.6 and the reference script",
  "date": "2026-10-04"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.allowlist:PLAN_SCHEMA.scope"
   }
  ],
  "note": "The plan's scope has no loading-rate rule."
 },
 "history": [],
 "notes": [
  "For the Texas A&M source the assumption has the source's own statement (owner, 2026-10-07, item h): the quote of the accepted Curator proposal 5."
 ],
 "tests": [
  "tests/test_plan.py::test_the_reference_plan_is_the_default_plan_under_the_owners_decisions"
 ]
}
```
### `spending_caps`

```json
{
 "key": "spending_caps",
 "name": "Spending caps",
 "state": "in_force",
 "statement": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction that takes its locks before reading any total (the run's lock for a run call, then one month-wide advisory lock, in that order) and records the call as started; a request that would pass a cap, or a lower ceiling the caller names, is not sent, and the refusal is logged. So two concurrent reservations can never both pass the same cap or ceiling. The monthly cap counts the calls recorded in this database only.",
 "value": {
  "text": "$2 per run; $2 per curation; $50 per month",
  "unit": "USD"
 },
 "category": "operational",
 "affects": "Whether a run or a model call may proceed.",
 "reason": "CLAUDE.md, rule 12.",
 "evidence": [
  "CLAUDE.md, rule 12; step 3 summary, 'Step 9 requirements'."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.spend:RUN_CAP_USD",
    "equals": 2
   },
   {
    "ref": "python:hypocurate.pipeline.agents.spend:CURATION_CAP_USD",
    "equals": 2
   },
   {
    "ref": "python:hypocurate.pipeline.agents.spend:MONTH_CAP_USD",
    "equals": 50
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "Model calls may cost at most $2 per run and $50 per calendar month (UTC), counting calls without a reported cost at their upper bound.",
   "from": "2026-10-04",
   "to": "2026-10-06",
   "note": "Step 8a (owner, 2026-10-06): the per-curation cap and the enforcement before each request."
  },
  {
   "value": "Model calls may cost at most $2 per run, $2 per curation (one registration invocation of the Curator) and $50 per calendar month (UTC, by the database's start time), counting every call at its reported cost or, while none is known, at its maximum cost. The check is made before each request, in one transaction (the run's lock for a run call, then one month-wide advisory lock) that records the call as started; a request that would pass a cap, or a lower ceiling the caller names, is not sent, and the refusal is logged. The monthly cap counts the calls recorded in this database only.",
   "from": "2026-10-06",
   "to": "2026-10-07",
   "note": "Step 8a as built: a registration call read its curation total before taking the month-wide lock, so two concurrent reservations could both pass the curation cap or a lower ceiling (ChatGPT's review of step 8a, finding 3). Fixed 2026-10-07."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_agent_core.py::test_the_run_cap_refuses_a_request_before_it_is_sent",
  "tests/test_agent_core.py::test_the_curation_cap_and_a_ceiling_refuse_before_sending",
  "tests/test_agent_core.py::test_the_month_cap_counts_every_call_including_unconfirmed_ones",
  "tests/test_agent_core.py::test_two_reservations_cannot_both_pass_the_month_cap",
  "tests/test_agent_core.py::test_a_reservation_waits_for_the_month_wide_lock",
  "tests/test_agent_core.py::test_two_reservations_on_one_invocation_cannot_both_pass_the_curation_cap",
  "tests/test_agent_core.py::test_two_reservations_on_one_invocation_cannot_both_pass_a_lower_ceiling",
  "tests/test_agent_core.py::test_two_reservations_on_one_run_cannot_both_pass_the_run_cap"
 ]
}
```
### `access_context_dispatcher`

```json
{
 "key": "access_context_dispatcher",
 "name": "Access objects come only from the dispatcher",
 "state": "in_force",
 "statement": "An access object is created only by the trusted dispatcher, around an immutable context captured once: hypocurate.access.dispatch.bind(run, agent setting) reads the role from the run's recorded agent settings and the stage from the database, and binds no run role to a source; hypocurate.access.dispatch.bind_invocation(invocation) (step 8a) reads run or source version, role and agent setting from one invocation record (agent_invocation), so a call's run, setting and source are never assembled separately, and binds a registration invocation to the one sealed source version it names. The database refuses a run invocation of the Curator (the Curator never runs within a run). There is no public constructor taking a caller-chosen run, role, stage or source (the tests have their own helper). Every bind is logged.",
 "value": {
  "text": "dispatch.bind only",
  "unit": null
 },
 "category": "operational",
 "affects": "Every agent read (steps 8 and 9).",
 "reason": "Review finding 2: caller-chosen, mutable role, run, stage and source could be misused by our own code.",
 "evidence": [
  "Step 5 second-model review (ChatGPT, 2026-10-05), accepted by the owner: docs/reviews/step05_review_chatgpt.md."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.access.dispatch:bind"
   },
   {
    "ref": "python:hypocurate.access.dispatch:bind_invocation"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "An access object is created only by hypocurate.access.dispatch.bind(run, agent setting, source), around an immutable context captured once: the role is read from the run's recorded agent settings, the stage from the database, and a Curator's source must be one of the run's run_source rows. There is no public constructor taking a caller-chosen run, role, stage or source (the tests have their own helper). Every bind is logged.",
   "from": "2026-10-05",
   "to": "2026-10-06",
   "note": "Step 8a (owner, 2026-10-06): one invocation record per agent call (step 5 re-check); the Curator binds at registration, not to a run's source."
  },
  {
   "value": "An access object is created only by the trusted dispatcher, around an immutable context captured once: hypocurate.access.dispatch.bind(run, agent setting) reads the role from the run's recorded agent settings and the stage from the database, and binds no run role to a source; hypocurate.access.dispatch.bind_invocation(invocation) (step 8a) reads run or source version, role and agent setting from one invocation record (agent_invocation), so a call's run, setting and source are never assembled separately, and binds a registration invocation to the one sealed source version it names. There is no public constructor taking a caller-chosen run, role, stage or source (the tests have their own helper). Every bind is logged.",
   "from": "2026-10-06",
   "to": "2026-10-07",
   "note": "Step 8a as built: a run-scoped Curator invocation could be created; the access layer gave it no fields, but the common request interface could still send a request against it (ChatGPT's review of step 8a, finding 6). Refused by the database from 2026-10-07."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_access_dispatch.py::test_bind_refuses_a_setting_or_source_the_run_did_not_record",
  "tests/test_access_dispatch.py::test_an_access_object_has_no_public_constructor_and_cannot_be_changed",
  "tests/test_migrations_step8a.py::test_a_run_invocation_of_the_curator_is_refused"
 ]
}
```
### `curator_quote_checks`

```json
{
 "key": "curator_quote_checks",
 "name": "The two checks on a Curator proposal",
 "state": "in_force",
 "statement": "A Curator proposal passes only if, in this order (`quotes.check`): (1) the value is allowed: a vocabulary value, a microstructure of vocabulary tokens joined by '+', or for the test temperature a finite number of °C (never JSON null, a boolean or a string); (2) the quote is 30 to 600 characters after collapsing runs of whitespace; (3) it occurs in one of the sealed version's documentation files after collapsing runs of whitespace on both sides (nothing else normalized: no case folding, no markup changes), beginning and ending at a word boundary there, code finding the document and the line; (4) it holds a listed term for the value (TERMS) as a whole word, after collapsing whitespace and setting aside 'ultimate tensile strength' (so 'tensile' there alone is not a test type), case-insensitive except B2 and L12; a microstructure joined by '+' needs every part; a test temperature is a complete signed number (sign and decimals included) equal to the value and followed by a Celsius unit in a form found in the frozen documents ('°C', after spaces or LaTeX '~', or LaTeX '\\SI{n}{\\degreeCelsius}'); (5) for a test condition (test type, temperature band, test temperature) it also holds a testing word as a whole word (test, tests, tested, testing, loaded, loading, strained, deformed, strain rate), so a processing sentence such as 'cold rolled at room temperature' is refused. Otherwise the proposal is stored as refused with a code and leaves the field unassigned. The database applies the same checks again when a passed proposal is stored (its own copy of the lists, tested equal to the code's, and tested to agree with the code case by case), except the line number, which a curation file's check covers. None of the checks shows that the sentence supports the value: a person decides that.",
 "value": {
  "text": "value + quote found at word boundaries + whole-word listed term + testing word for test conditions; 30-600 characters",
  "unit": null
 },
 "category": "data_handling",
 "affects": "Which Curator proposals a person may accept.",
 "reason": "Owner's decision: a quote must exist in the sealed document and contain a listed term, a first filter; a refused paraphrase leaves the field unassigned, the safe direction.",
 "evidence": [
  "Owner, step 8a plan, Q2 (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.quotes:QUOTE_MIN_CHARS",
    "equals": 30
   },
   {
    "ref": "python:hypocurate.pipeline.agents.quotes:QUOTE_MAX_CHARS",
    "equals": 600
   },
   {
    "ref": "python:hypocurate.pipeline.agents.quotes:TERMS"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.quotes:CASE_SENSITIVE_TERMS"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.quotes:TESTING_WORDS"
   },
   {
    "ref": "python:hypocurate.pipeline.agents.quotes:EXCLUDED_PHRASES"
   },
   {
    "ref": "sql:ck_curator_proposal_proposed_complete"
   },
   {
    "ref": "sql:hc_curator_term_ok"
   },
   {
    "ref": "sql:hc_quote_occurs"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "A Curator proposal passes only if (1) its quote occurs in one of the sealed version's documentation files after collapsing runs of whitespace to one space on both sides (nothing else is normalized: no case folding, no markup changes), code finding the document and the line where it begins, and the database checking the occurrence again when it is stored; the quote is 30 to 1500 characters after collapsing; and (2) the quote contains a listed term for the proposed value (TERMS, case-insensitive; for the test temperature the number as written; for a microstructure joined by '+', every part). Otherwise it is stored as refused with a code and leaves the field unassigned. Neither check shows that the sentence supports the value: a person decides that.",
   "from": "2026-10-06",
   "to": "2026-10-07",
   "note": "Step 8a as built (draft lists by Claude Code). Changed after ChatGPT's review of step 8a (finding 5) and by the owner's term-check changes a-f, 2026-10-07."
  }
 ],
 "notes": [
  "The term list itself (TERMS) was drafted by Claude Code in step 8a; the owner approved the check, and the list is for the owner's review with step 8a. Changing it is a register change.",
  "The 30-1500 character bounds are Claude Code's defaults in step 8a, for the owner's review.",
  "Safe refusals (owner, 2026-10-07, item f; each leaves the field unassigned, and the person can still assign a value by decision): a statement under 30 characters; a temperature given in kelvin (no conversion is made); a Celsius form not found in the frozen documents (such as '$^\\circ$C'); a range such as '20-25 °C'; LaTeX forms of a term (such as 'L1$_2$'); a sentence whose testing word is missing although it does describe the test.",
  "Owner's changes of 2026-10-07: whole words everywhere (B2 not in 'Nb25', 'tension' not in 'extension', 'tensile' not on 'ultimate tensile strength' alone); FCC, BCC, HCP case-insensitive, B2 and L12 case-sensitive; testing word for test conditions; a temperature number followed by a Celsius unit; spelling variants (face and body centred or centered cubic, with or without hyphens; 'liquid helium' for cryogenic); at most 600 characters, beginning and ending at a word boundary.",
  "The owner's two accepted proposals (5, test type tension, main.tex line 177; 2, phase class FCC, line 173) were re-checked under these rules and the database's checks on 2026-10-07 and still pass (tests/test_quote_checks.py::test_the_owners_two_accepted_proposals_still_pass)."
 ],
 "tests": [
  "tests/test_curator.py::test_each_proposal_is_stored_as_code_decided_it",
  "tests/test_curator.py::test_an_entry_that_fails_a_check_is_refused_with_its_code",
  "tests/test_curator.py::test_the_quote_checks_collapse_whitespace_only",
  "tests/test_migrations_step8a.py::test_a_proposal_that_did_not_pass_cannot_be_stored_as_passed",
  "tests/test_quote_checks.py::test_the_owners_two_accepted_proposals_still_pass",
  "tests/test_quote_checks.py::test_terms_match_whole_words_with_the_stated_case_rules",
  "tests/test_quote_checks.py::test_whitespace_is_collapsed_for_terms_as_for_locating_the_quote",
  "tests/test_quote_checks.py::test_test_conditions_need_a_testing_word",
  "tests/test_quote_checks.py::test_a_temperature_is_the_whole_number_with_its_unit",
  "tests/test_quote_checks.py::test_another_number_or_no_celsius_unit_is_refused",
  "tests/test_quote_checks.py::test_spelling_variants_are_listed",
  "tests/test_quote_checks.py::test_a_quote_is_at_most_600_characters",
  "tests/test_quote_checks.py::test_a_quote_begins_and_ends_at_a_word_boundary",
  "tests/test_quote_checks.py::test_the_recorded_safe_refusals",
  "tests/test_migrations_step8a.py::test_a_value_that_does_not_match_its_term_is_refused",
  "tests/test_migrations_step8a.py::test_a_passed_proposal_with_a_missing_part_is_refused",
  "tests/test_migrations_step8a.py::test_the_databases_term_list_is_the_codes",
  "tests/test_migrations_step8a.py::test_the_database_and_the_code_agree_on_every_case"
 ]
}
```
### `curation_acceptance`

```json
{
 "key": "curation_acceptance",
 "name": "A Curator value takes effect only when a person accepts it",
 "state": "in_force",
 "statement": "A proposal that passed the checks takes effect only when a person accepts it (`hypocurate sources accept <proposal> --by <name>`; one decision per proposal, with the database's time; the command line takes the name as given and has no login). `seal-curation` seals the accepted values only, with quote, document, line, proposal, model and settings version, acceptor and time, as curation.json in a new sealed source version; rejected, refused, unanswered and not-stated proposals are left out (the field stays unassigned). Two accepted proposals for one field are not sealed. A curation file is checked against the version it is attached to before it is sealed (registration, seal-curation) and before it is applied: the base version's fingerprint must be that of the version's own files without the curation file; every quote must be found again in that version's documentation on the stated line with the stated term, and every value and term must pass the current checks; the acceptance fields must be present and valid. Anything else refuses the whole version. These checks cannot show that a person really accepted the values: the exact approved export replayed on the same base (the file the owner froze in data/, pinned by its manifest fingerprint) is the only trusted import. Adapters apply a curated value to every record of the version only where the record's field is not reported (never over a reported, converted or decided value), as 'assigned from source' with that citation. Runs use the newest sealed version; a run never calls the Curator. Values 'assigned by decision' stay owner decisions.",
 "value": {
  "text": "accepted by a person; sealed into the version; applied only to gaps",
  "unit": null
 },
 "category": "data_handling",
 "affects": "Which values reach records from the Curator; record content and fingerprints of curated versions.",
 "reason": "Owner's decision: no run depends on live model output for any record value; a proposal is only a proposal until a person accepts it.",
 "evidence": [
  "Owner, step 8a plan, Q2 (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.sources.curation:seal_curation"
   },
   {
    "ref": "python:hypocurate.sources.curated:apply_curation"
   },
   {
    "ref": "python:hypocurate.sources.curated:check_curation"
   },
   {
    "ref": "sql:uq_curator_decision_proposal_id"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "A proposal that passed the checks takes effect only when a person accepts it (`hypocurate sources accept <proposal> --by <name>`; one decision per proposal, with the database's time; the command line takes the name as given and has no login). `seal-curation` seals the accepted values only, with quote, document, line, proposal, model and settings version, acceptor and time, as curation.json in a new sealed source version; rejected, refused, unanswered and not-stated proposals are left out (the field stays unassigned). Two accepted proposals for one field are not sealed. Adapters apply a curated value to every record of the version only where the record's field is not reported (never over a reported, converted or decided value), as 'assigned from source' with that citation. Runs use the newest sealed version; a run never calls the Curator. Values 'assigned by decision' stay owner decisions.",
   "from": "2026-10-06",
   "to": "2026-10-07",
   "note": "Step 8a as built; the curation file's check added after ChatGPT's review of step 8a (finding 1), 2026-10-07."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_curator.py::test_a_person_decides_once_and_only_on_a_proposal_that_passed",
  "tests/test_curator.py::test_sealing_applies_accepted_values_only_where_the_table_gives_none",
  "tests/test_curator.py::test_a_curated_version_is_reproducible_from_its_files_and_cannot_be_curated_again",
  "tests/test_curator.py::test_two_accepted_proposals_for_one_field_are_not_sealed",
  "tests/test_curator.py::test_a_curation_file_that_cannot_be_read_refuses_the_version",
  "tests/test_curator.py::test_the_frozen_export_on_its_own_base_is_accepted",
  "tests/test_curator.py::test_an_export_copied_onto_another_base_is_refused",
  "tests/test_curator.py::test_an_export_that_does_not_check_out_is_refused",
  "tests/test_curator.py::test_a_quote_that_fails_the_current_term_checks_is_refused_on_import"
 ]
}
```
### `request_failure_policy`

```json
{
 "key": "request_failure_policy",
 "name": "What happens when an agent request fails",
 "state": "in_force",
 "statement": "Every agent request is reserved, sent once (litellm's retries off) outside any database transaction, and recorded. At most two requests per agent call: an unavailable provider (connection error, timeout, 429, 5xx, or a reply litellm cannot read) is tried once more with the same request; an unusable answer (empty, malformed, a tool call, truncated at the output limit, longer than the role allows) once more with a fixed corrective note naming only the failure code; refused credentials (401, 403), another refused request (4xx), a refusal, a cost the provider did not report, a reservation that cannot be written (nothing is sent), a failed recording on any branch (after a provider failure, a reply without usage or a usable reply) and every spending refusal stop at once. A failed call is recorded with no usage and counts at its maximum cost; a call whose recording fails stays 'started' and counts at its maximum cost. No provider, library or database text is kept with a call or sent in a later request; the process log gets the failure code, the exception's types and where it was raised, never its text. Not covered: what a library logs by itself (litellm's own debug logging is off unless a process turns it on). DSPy's JSON fallback is off.",
 "value": {
  "text": "2 requests at most; retry / correct / stop by code",
  "unit": null
 },
 "category": "operational",
 "affects": "Every agent call's cost and outcome.",
 "reason": "The step 8a failure table (owner, 2026-10-06): every failure mode has a defined, tested outcome.",
 "evidence": [
  "Owner, step 8a plan: the request-path failure table (2026-10-06)."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.pipeline.agents.interface:MAX_ATTEMPTS",
    "equals": 2
   },
   {
    "ref": "python:hypocurate.pipeline.agents.lm:FAILURES"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "Every agent request is reserved, sent once (litellm's retries off) outside any database transaction, and recorded. At most two requests per agent call: an unavailable provider (connection error, timeout, 429, 5xx, or a reply litellm cannot read) is tried once more with the same request; an unusable answer (empty, malformed, a tool call, truncated at the output limit, longer than the role allows) once more with a fixed corrective note naming only the failure code; refused credentials (401, 403), another refused request (4xx), a refusal, a cost the provider did not report, a failed recording and every spending refusal stop at once. A failed call is recorded with no usage and counts at its maximum cost; a call whose recording fails stays 'started' and counts at its maximum cost. No provider, library or database text is kept with a call or sent in a later request: it goes to the process log only. DSPy's JSON fallback is off.",
   "from": "2026-10-06",
   "to": "2026-10-07",
   "note": "Step 8a as built: a failed recording after a provider failure or a reply without usage escaped unclassified and was retried as malformed (ChatGPT's review of step 8a, finding 4); the process log held the exception's full text. Fixed 2026-10-07."
  }
 ],
 "notes": [
  "litellm cannot read a reply with no usage block and raises a connection error, so such a reply is treated as an unavailable provider (failed, counted at its maximum, tried once more); the code 'cost_unknown' is for a readable reply whose usage is empty."
 ],
 "tests": [
  "tests/test_agent_core.py::test_an_unavailable_provider_is_tried_once_more_with_the_same_request",
  "tests/test_agent_core.py::test_refused_credentials_or_requests_are_not_retried_and_no_provider_text_is_kept",
  "tests/test_agent_core.py::test_an_unusable_answer_is_corrected_once_with_a_fixed_note_and_never_the_answer",
  "tests/test_agent_core.py::test_a_refusal_is_not_retried",
  "tests/test_agent_core.py::test_a_reply_without_usage_is_unreadable_failed_and_counted_at_its_maximum",
  "tests/test_agent_core.py::test_a_readable_reply_with_empty_usage_is_cost_unknown",
  "tests/test_agent_core.py::test_a_reply_whose_recording_fails_is_discarded_and_the_call_stays_open",
  "tests/test_agent_core.py::test_no_database_transaction_is_open_while_a_request_is_in_flight",
  "tests/test_agent_core.py::test_a_recording_failure_on_any_branch_stops_and_keeps_the_maximum",
  "tests/test_agent_core.py::test_a_reservation_that_cannot_be_written_sends_nothing",
  "tests/test_agent_core.py::test_provider_error_text_never_reaches_the_process_log",
  "tests/test_agent_core.py::test_the_request_headers_carry_nothing_of_the_input"
 ]
}
```
### `database_session_time_zone` (new)

```json
{
 "key": "database_session_time_zone",
 "name": "Database sessions run in UTC",
 "state": "in_force",
 "statement": "Every database connection sets its session time zone to 'UTC' by name when it connects. The driver then interprets timestamps without reading a time-zone file, which the file guard would refuse in a guarded process (with the server's 'Etc/UTC' it opened /usr/share/zoneinfo/Etc/UTC). The file guard is unchanged. Queries that depend on a zone state it ('AT TIME ZONE'), and the servers used so far run in UTC already, so no stored or computed value changes.",
 "value": {
  "text": "UTC",
  "unit": null
 },
 "category": "operational",
 "affects": "How timestamps are read; whether a guarded process logs a refused zone-file read.",
 "reason": "Owner's decision after ChatGPT's review of step 8a: set the session time zone rather than widen the guard or accept a warning on every guarded run. psycopg special-cases the name 'UTC' and reads no zone file for it.",
 "evidence": [
  "ChatGPT's review of step 8a, operational point on the file guard (docs/reviews/step08a_review_chatgpt.md).",
  "psycopg 3.3.6, psycopg/_tz.py: get_tzinfo maps b\"UTC\" to timezone.utc without ZoneInfo."
 ],
 "decided": {
  "by": "owner (Khalid El-Awady)",
  "date": "2026-10-07"
 },
 "expert_review": {
  "status": "not_reviewed",
  "name": null,
  "date": null
 },
 "sensitivity": null,
 "applied": {
  "status": "yes",
  "settings": [
   {
    "ref": "python:hypocurate.db.engine:SESSION_TIME_ZONE",
    "equals": "UTC"
   }
  ],
  "note": null
 },
 "history": [
  {
   "value": "The server's own time zone ('Etc/UTC' in the local and test databases); in a guarded process the driver's zone-file read was refused and it fell back to UTC with a warning.",
   "from": "2026-10-04",
   "to": "2026-10-07",
   "note": "Steps 1 to 8a as built."
  }
 ],
 "notes": [],
 "tests": [
  "tests/test_access_files.py::test_a_guarded_timestamp_read_needs_no_zone_file"
 ]
}
```
### Scripts

#### `mutate2.sh`

```
#!/bin/bash
# usage: mutate2.sh <name> <spec.json> -- <pytest args>; spec: [[file, old, new], ...] (files relative to the package)
set -e
NAME=$1; SPEC=$2; shift 3
W=~/hc-work/step08a/mut/$NAME; rm -rf $W; mkdir -p $W
cp -r /workspaces/hypocurate/hypocurate $W/hypocurate
ln -s /workspaces/hypocurate/data $W/data; ln -s /workspaces/hypocurate/tests $W/tests
/workspaces/hypocurate/.venv/bin/python - "$W/hypocurate" "$SPEC" <<'PY'
import json, sys
root, spec = sys.argv[1], json.load(open(sys.argv[2]))
for f, old, new in spec:
    p = f"{root}/{f}"; s = open(p).read()
    assert s.count(old) == 1, (f, old[:50], s.count(old)); open(p, "w").write(s.replace(old, new))
PY
export DATABASE_URL="$(grep '^DATABASE_URL=' /workspaces/hypocurate/.env | cut -d= -f2-)"
cd $W && PYTHONPATH=$W /workspaces/hypocurate/.venv/bin/python -c "import hypocurate; assert hypocurate.__file__.startswith('$W')"
cd $W && PYTHONPATH=$W /workspaces/hypocurate/.venv/bin/pytest -q -p no:cacheprovider --rootdir=$W -c /dev/null "$@" 2>&1 | tail -1
```
#### `fix/run_mutations.sh`

```
#!/bin/bash
# The step 8a review-fix mutations; one line per mutation (spec files in mspec_fix/).
D=~/hc-work/step08a/mspec_fix; M=~/hc-work/step08a/mutate2.sh; cd ~
T_C="tests/test_agent_core.py"
T_Q="tests/test_quote_checks.py tests/test_curator.py"
T_M="tests/test_migrations_step8a.py"
T_I="tests/test_curator.py"
T_Z="tests/test_access_files.py"
echo "control (no change): $($M control <(echo '[]') -- $T_C $T_Q $T_M $T_Z)"
for m in f01 f02 f03 f04; do echo "$m: $($M $m $D/$m.json -- $T_C)"; done
for m in f05 f06 f07 f08 f09 f10 f11; do echo "$m: $($M $m $D/$m.json -- $T_Q)"; done
for m in f12 f13 f14 f15 f16 f22 f23; do echo "$m: $($M $m $D/$m.json -- $T_M)"; done
for m in f17 f18 f19 f20; do echo "$m: $($M $m $D/$m.json -- $T_I)"; done
for m in f21; do echo "$m: $($M $m $D/$m.json -- $T_Z)"; done
```
#### `refdump/test_zz_refdump.py`

```
"""Scratch (not committed): dumps the reference runs' full statistics output to REFDUMP_OUT."""
import json, os
from test_reference_numbers import runs  # noqa: F401 (the module fixture)


def test_dump(runs):
    out = {}
    for key, r in runs.items():
        records = [{"identity": [rec["stable_identity"] if "stable_identity" in rec else None], **{k: rec[k] for k in sorted(rec) if k not in ("id",)}}
                   for rec in r["data"]["records"]]
        out[key] = {"run": [str(x) for x in r["run"]], "decision": r["out"]["decision"],
                    "analyses": r["out"]["analyses"], "not_analysed": r["out"].get("not_analysed"),
                    "n_records": len(records)}
    with open(os.environ["REFDUMP_OUT"], "w") as f:
        json.dump(out, f, indent=1, sort_keys=True, default=str)
```
#### `refdump/compare_fix.py`

```
"""Compares main.json with branch_fix.json leaf by leaf (the reference runs' full statistics output)."""
import collections, json
a = json.load(open("main.json")); b = json.load(open("branch_fix.json"))
out = []
def walk(x, y, p):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)):
            walk(x.get(k, "<absent>"), y.get(k, "<absent>"), f"{p}.{k}")
    elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
        for i, (u, v) in enumerate(zip(x, y)):
            walk(u, v, f"{p}[{i}]")
    elif x != y:
        out.append((p, x, y))
walk(a, b, "")
print("differing leaves by name:", dict(collections.Counter(p.split(".")[-1].split("[")[0] for p, _, _ in out)))
stat = [(p, x, y) for p, x, y in out if p.split(".")[-1] in ("estimate", "p_value", "std_error", "t")]
print("max relative difference of estimate, standard error, p, t:", max((abs(x - y) / abs(x) for _, x, y in stat), default=0))
for p, x, y in stat:
    print("  ", p, x, "->", y)
compared = 0
for key in a:
    print(key, "| run row identical:", a[key]["run"] == b[key]["run"],
          "| decision keys differing:", sorted(k for k in a[key]["decision"] if a[key]["decision"][k] != b[key]["decision"][k]))
    for x, y in zip(a[key]["analyses"], b[key]["analyses"]):
        assert x["analysis"] == y["analysis"]
        for k in ("counts", "checks", "minimums", "label", "label_reason", "inference_reason", "minimums_met",
                  "withheld", "df", "significant", "uninformative_groups", "scope", "set", "source"):
            compared += 1
            if x[k] != y[k]:
                print("  DIFFERENT", x["analysis"], k, x[k], y[k])
print("structural comparisons made (counts, checks, minimums, labels, reasons, df, significance per analysis):", compared)
c = b["reference"]["analyses"][0]
print("pooled on the branch:", c["counts"]["n_records"], c["counts"]["n_alloys"], c["counts"]["n_groups"],
      c["counts"]["resid_df"], round(c["estimate"], 1), round(c["std_error"], 1), f"{c['p_value']:.1e}")
```
#### `fix/fixpacket.py`

````
"""Builds docs/reviews/step08a_fix_packet.md from the files on disk (run from the repository root)."""
import json, subprocess
from pathlib import Path

H = Path.home() / "hc-work/step08a"
F = H / "fix"
REVIEWED = "16261de"
OUT = Path("docs/reviews/step08a_fix_packet.md")


def sh(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def fence(text, lang=""):
    ticks = "````" if "```" in text else "```"
    return f"{ticks}{lang}\n{text.rstrip()}\n{ticks}\n"


fix_commit = sh("git", "log", "-1", "--format=%h", "--grep=Step 8a review fixes").strip()
parts = [(F / "fix_intro.md").read_text().replace("__FIXCOMMIT__", fix_commit)]
parts.append("\n## 6. The new tests on the reviewed code (`16261de`)\n\nThe new tests were run against a copy of the reviewed package (`git archive 16261de`) with this branch's tests and data. The only file added to the copy is `access/guard_probe.py`, the test probe with its new `timestamp` action, so that the time-zone test fails for its own reason. 117 failed and 12 passed. The 12 that pass are expected: the positive controls (the frozen export on its own base, a matching value and term, two word-boundary cases that hold, six database cases the old checks already refused), the run-cap race (already serialized by the run lock) and the headers test (coverage, not a fix).\n\n"
             + fence((F / "failed_before.txt").read_text() + "\n" + (F / "failed_before_raw.log").read_text().splitlines()[-1]))
parts.append("\n## 7. Mutation checks on the fixes\n\nEach mutation is applied to a scratch copy of the package (`data/` and `tests/` linked, `PYTHONPATH` to the copy, the import checked), and the named tests run (`~/hc-work/step08a/fix/run_mutations.sh`). **All 23 are caught.** The control (no change) has one failure: `test_access_files.py::test_the_python_installation_and_the_package_code_can_be_read`, which expects the repository's own package to be readable under the guard, while the scratch run uses a copy. It belongs only to f21's test file, whose run fails both that test and `test_a_guarded_timestamp_read_needs_no_zone_file` (checked by name).\n\n"
             + fence((F / "mutations_fix.log").read_text())
             + "\nThe mutations: f01 the month lock after the totals (finding 3); f02 a recording failure re-raised; f03 a reservation failure not caught; f04 the exception text logged; f05 no case-sensitive terms; f06 no word boundaries for terms; f07 no testing word; f08 numbers without sign or decimal boundaries; f09 no word boundaries for quotes; f10 no excluded phrase; f11 the quote maximum back to 1500; f12 the database's term check removed; f13 the NULL-safe completeness check reverted; f14 a run invocation of the Curator allowed; f15 the database's quote boundaries removed; f16 the database's case-sensitive terms emptied; f17 the base fingerprint not checked; f18 the import's quote and term checks weakened; f19 any acceptor accepted; f20 no check at registration; f21 no session time zone; f22 JSON null allowed; f23 no testing word in the database. Specs:\n\n"
             + "".join(f"- `{p.stem}`: `{p.read_text().strip()}`\n" for p in sorted((H / "mspec_fix").glob("*.json"))))
image = (F / "image_suite.log").read_text().splitlines()
parts.append("\n## 8. Suite\n\nLocally:\n\n" + fence((F / "suite_fix.log").read_text().strip().splitlines()[-1])
             + "\nIn the rebuilt test image:\n\n" + fence("\n".join(l for l in image[-3:] if l.strip()))
             + "\n### Reference comparison output (branch after the fixes vs `main`)\n\n" + fence((H / "refdump/compare_fix_output.txt").read_text())
             + "Branch after the fixes vs the branch before them: the two dumps are byte-identical JSON.\n")
code = sh("git", "diff", f"{REVIEWED}..HEAD", "--", "hypocurate", "README.md", ":(exclude)hypocurate/assumptions.json")
tests = sh("git", "diff", f"{REVIEWED}..HEAD", "--", "tests")
parts.append(f"\n## 9. Diffs since the review (`{REVIEWED}..HEAD`)\n\n### Package and README\n\n" + fence(code, "diff")
             + "\n### Tests (new and changed)\n\n" + fence(tests, "diff"))
old = {e["key"]: e for e in json.loads(sh("git", "show", f"{REVIEWED}:hypocurate/assumptions.json"))}
new = {e["key"]: e for e in json.loads(Path("hypocurate/assumptions.json").read_text())}
changed = [k for k in new if old.get(k) != new[k]]
parts.append("\n## 10. Register changes and scripts\n\n" + f"{len(changed)} entries new or changed (of {len(new)}): "
             + ", ".join(f"`{k}`" for k in changed) + ".\n\n"
             + "".join(f"### `{k}`{' (new)' if k not in old else ''}\n\n" + fence(json.dumps(new[k], indent=1, ensure_ascii=False), "json") for k in changed)
             + "### Scripts\n\n" + "".join(f"#### `{s}`\n\n" + fence((H / s).read_text()) for s in
                                           ("mutate2.sh", "fix/run_mutations.sh", "refdump/test_zz_refdump.py", "refdump/compare_fix.py", "fix/fixpacket.py")))
OUT.write_text("\n".join(parts), encoding="utf-8")
print(OUT, len(OUT.read_text()))
````
