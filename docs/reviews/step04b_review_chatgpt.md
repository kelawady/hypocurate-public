No serious security or database-damage issue found. The substantive problems are overclaiming what “applied” tests prove, several misleading entries, and missing scientific assumptions. I reviewed the packet and ran a targeted validation check; I did not rerun the reported 527-test suite.
1. “Applied: yes” can drift without the register tests failing.
   The checks establish that a named object exists and, sometimes, equals a separately recorded value. They do not establish that the entry accurately describes its behaviour.
   I changed grain_size_as_reported to say values are converted to nanometres, leaving its checked constant as µm. Both validation and check_settings passed.
   Other gaps:
   - A function’s behaviour can change while its name remains.
   - SQL references match names in migration text—even comments or superseded migrations.
   - A constant can remain unchanged while executable code stops using it.
   Fix the claim, not necessarily the architecture: describe these as reference/value checks. Link behavioural entries to relevant regression tests, and use structured values to generate displayed defaults where practical. Do not claim general protection against assumption drift.
2. Several “Yes” labels describe only partial implementation.
   - papers_independent: the source’s grouping metadata exists; independence is neither established nor yet used in inference.
   - sufficiency_options: database restrictions exist, but the stated default is deferred.
   - controlled_extract_disabled: registration defaults to disabled, but the promised exclusion from real analysis is not enforced yet.
   The expanded notes acknowledge these distinctions, but the main row still says “Yes.” Split the statements or display “Partly applied”. A reader should not need to expand a row to discover that its principal safeguard is pending.
3. The duplicate-survivor entry confuses citation with provenance.
   duplicate_survivor_rule says direct extraction from the original paper is “detected by the original paper’s DOI on the record.”
   A compilation and a copied extract can both carry that DOI. It identifies the cited paper, not where the record was extracted. The earlier step-1 decision said prefer the record carrying the original reference; the register strengthens that into an unsupported provenance claim.
   Restore the precise decision wording. If direct-source preference is intended later, it needs explicit extraction-origin metadata.
4. “0 open decisions” conceals a genuine unresolved decision.
   values_disagree_tolerance explicitly says record pairing is unfinished and needs owner approval. That determines whether legitimate repeat specimens become conflicts, so it deserves its own open entry.
   The calibration change is different: the owner has chosen a direction, but implementation awaits review. Keep that distinction visible—approved direction, pending technical review—rather than implying every aspect is settled.
The most important missing assumptions are below. These are register additions or clarifications, not requests to implement more models now.
Missing assumption	What should be stated
Confounding and interpretation of k	Within an alloy, processing, texture, dislocation density and other omitted strengthening mechanisms may vary with grain size. Clustered errors do not remove that bias. A positive fitted slope supports an association under the model, not isolated causal proof of grain-size strengthening. Extend baseline_per_alloy.
Measurement error is ignored	Grain size and composition are treated as known predictors. Their measurement uncertainty is not propagated. Also, transforming a reported mean grain size is not generally equivalent to averaging the transformed grain sizes. mean_grain_size_only does not fully capture this.
Weighting and influence	OLS gives each retained row equal weight in its objective—not each paper or alloy. Reported uncertainty and replicate counts do not determine weights. Larger studies and greater within-alloy predictor spread can dominate k. OLS documentation
Selection and missingness	Available, published, convertible and eligible records are not necessarily representative of all relevant alloys or experiments. State that the analysis does not correct publication bias or outcome-related missingness; its conclusions are conditional on the retained evidence.
Repeated testing	The significance threshold applies per locked test. Repeated queries, narrower questions and alternative plans do not collectively retain a 5% false-positive rate. State whether there is any multiplicity adjustment; do not leave that implicit.
Calibration’s complete error model	The reference simulation uses independent, zero-mean group shifts and record errors with common variance components, conditional on fixed grain sizes, groups and inclusion. “Normal distributions” alone omits these assumptions. It does not simulate source discovery, extraction mistakes or selection uncertainty.
Few-group inference is approximate	Passing the two-group computational floor does not establish reliable inference. The small-sample correction and t reference remain approximations, especially with few or highly unequal groups.
What one observation represents	A source row might be one specimen, a replicate mean or a summarized condition. State how these are treated, whether specimen counts matter, and what evidence distinguishes repeated specimens from duplicated reporting. This connects directly to the unresolved pairing decision.


A few smaller accuracy corrections:
- malformed_files_refused should explicitly refer to CSV; spreadsheet handling is different.
- p_threshold_comparison should display p < α, with 0.05 identified as the default, consistent with one_sided_test.
- normal_errors_in_calibration says heavier tails would make results optimistic. Use may change calibration; the direction is not guaranteed.
- “A login lasts 12 hours” suggests an absolute lifetime. The session middleware renews nonempty session cookies, so describe the expiry behaviour precisely.
Status honesty: source-based assignments and decision-based assignments are clearly distinguished in the register. Their future implementation is labelled accordingly. All 60 entries are marked not reviewed; I found no false expert endorsement.
Page and deployment: the route is behind the existing login, has no write handler, and only renders register contents. Failing startup on invalid JSON/schema also disables login and health for that instance. CI validates the bundled register, and a normal Render deployment retains the previous release when the new instance fails health checks. That is reasonable here, but it is not a guarantee for first startup or every restart, and it does not undo an already committed pre-deploy migration. Render deployment behaviour
The page needs no redesign. Correct the implementation claims and add the missing scientific assumptions before treating this as an authoritative register.
