Not ready to merge. I found four blocking safeguard gaps, plus two smaller issues. These matter under the agreed “our own mistakes” threat model.
File names below refer to code quoted in the packet.
1. High — Imported curation bypasses the evidence and source-version checks.
   Files: sources/curated.py, curated_values(); sources/versions.py, _register_in().
   The live workflow selects accepted proposals correctly. The import path, however, checks mainly the JSON format, source name and entry keys. It ignores the claimed base-version fingerprint and does not recheck the document, quote, value vocabulary or acceptance metadata.
   Concrete case: copy an older curation.json into a new version of the same source. Its assignments apply even if the underlying data or documentation changed. My function-level probe also accepted an entry with a nonexistent document, absent quote, wrong base fingerprint and blank acceptor.
   Fix: validate the curation against the version’s data, documentation and interpretation settings before sealing or applying it. Recheck values and evidence, and require valid acceptance metadata. Replaying an approved export is a legitimate trusted-import path; make that boundary explicit rather than treating arbitrary well-shaped JSON as equivalent.
2. High — The database does not enforce the claimed proposal checks.
   Files: 0005_agents_and_documentation.py, hc_curator_proposal_insert() and ck_curator_proposal_proposed_complete; corresponding models.
   The database verifies quote occurrence, but trusts the supplied term. It does not establish that the term belongs to the proposed field/value.
   Concrete SQL case: test_type="compression", the genuine tensile-testing quote, and term="tensile" satisfy the shown checks. A person can subsequently accept that supposedly checked proposal. Also, line=NULL or term=NULL can make the completeness CHECK evaluate to UNKNOWN, which PostgreSQL accepts.
   Fix: require non-NULL mandatory fields and validate the value’s type, vocabulary and corresponding terms—including every microstructure component. Add direct-SQL tests for mismatched values/terms, NULLs and JSON null. I established this from the SQL; I could not execute PostgreSQL locally.
3. High — Concurrent reservations can exceed the curation cap or its lower ceiling.
   File: pipeline/agents/spend.py, reserve().
   Registration calls read their invocation’s spending before acquiring the month lock. Two callers can therefore retain the same stale total despite subsequently taking that lock.
   Reproduction: with $1.70 already recorded, two concurrent $0.20 reservations both succeed, reaching $2.10. I reproduced this by executing the reservation function with a deterministic, instrumented database interleaving.
   Fix: acquire the serialization lock before reading the curation total. Preserve the run-then-month lock order. Add a two-connection test using the same invocation, for both the curation cap and a lower ceiling. Existing tests cover the monthly total, not this race.
4. Medium — Recording failures can trigger another paid request instead of stopping.
   Files: pipeline/agents/lm.py, RecordedEngine.complete(); interface.py, call_agent().
   Recording a successful response is protected by the recording_failed handler. Recording a provider failure or missing-usage response is not.
   Reproduction: make spend.finish() fail after a response with no usage. The exception escapes with last_failure=None; the interface classifies it as malformed and permits another request. The existing recording-failure test exercises only the successful-response branch.
   Fix: handle recording failures consistently on every branch, setting recording_failed and stopping. The unfinished reservation should remain charged at its maximum.
5. Medium — The numeric keyword check matches different temperatures.
   File: pipeline/agents/quotes.py, term_for().
   I reproduced proposed 25°C matching quotes stating −25°C and 25.5°C. This is a token-matching defect, beyond the acknowledged limitation that keywords cannot establish scientific support.
   Keyword matching also uses raw whitespace: room\ntemperature passes quote-location normalization but fails the room-temperature keyword check.
   Fix: match complete signed numeric values with proper decimal boundaries, and collapse whitespace consistently for keyword matching. Keep human review for units, negation, scope and interpretation.
   The 30-character minimum can reject a valid short statement; Kelvin-to-Celsius proposals can also fail the literal-number requirement. These fail safely but should be documented. The instruction and output limits otherwise look reasonable for this task.
6. Medium — “The Curator never runs within a run” is not enforced by invocation creation.
   File: 0005_agents_and_documentation.py, invocation shape and insert trigger.
   Run-scoped Curator invocations remain valid; a migration test explicitly creates one. The access layer correctly gives them no fields, but the common request interface accepts separately supplied inputs and can still send a request against that invocation.
   Fix: reject scope='run', role='curator' when creating the invocation. The current production curation workflow does not take this route, but the foundation should prevent that straightforward wiring mistake.
The summary’s eight questions resolve as follows:
Question	Assessment
1. Access	The actual Curator workflow reads its invocation’s sealed documentation and targets. Binding is coherent, and retries omit previous answers and raw errors. Documentation itself may contain outcome numbers; “no outcome values whatsoever” would overclaim. Body tests are useful, but comprehensive header-leak coverage is not demonstrated.
2. Agents decide nothing	No direct live-output-to-record path in the normal workflow. The import gap in finding 1 prevents an unconditional sign-off. Applying curation only to not_reported fields preserves reported, converted and owner-assigned values across the target fields.
3. Migration	Transactional upgrade and guarded downgrade look sound, and the old run-call checks remain. Findings 2 and 6 need fixing. “Purely additive” is imprecise: it replaces checks/functions and changes nullability. Compatibility depends on the stated absence of existing model-call rows.
4. Spending	Requests follow committed reservation transactions; no request is intentionally held inside one. Unknown costs remain counted at the maximum. Finding 3 breaks the curation guarantee. The byte count plus 1,000 framing tokens is conservative, but the packet does not prove an unconditional provider-cost upper bound.
5. Failure handling	Fixed errors and corrective notes keep provider text out of later requests and stored failure codes. Finding 4 remains. Raw exception tracebacks are deliberately logged, so “secrets are never logged” needs stronger evidence or redaction.
6. Temperature bands	The shown validation and eligibility changes match the decision: explicit ranges for non-room-temperature plans; a matching band without a number remains unconfirmed. I found no unintended admission path. The reference plan’s room-temperature branch is unchanged.
7. Reproducibility	Reusing the exact approved export can reproduce the fingerprint across databases. That establishes byte reproducibility, not correctness of a curation attached to the wrong base version—finding 1.
8. Overclaims	The principal overclaims concern checked imported curation, database-enforced proposal validity, concurrent spending limits and universal failure handling.


Two remaining operational points:
- File guard: removing nonexistent import-path entries is safe here; it grants no additional access. For the timezone warning, set the database session timezone explicitly to UTC and test guarded timestamp reads. Psycopg special-cases that name without loading a zone file. This is preferable to widening filesystem access or accepting permanent warning noise. Psycopg implementation
- Dependencies and tests: I found no basis to remove particular transitive dependencies merely from their names. Disabling dotenv loading, caches and telemetry is appropriate. The changed tests generally preserve their previous intent; the important omissions are the cases above. I verified that the listed base and five-minute cache prices match the provider’s published table. Anthropic pricing
I ran focused function-level probes, including the deterministic reservation interleaving. I could not rerun PostgreSQL migrations, the full DSPy/LiteLLM HTTP tests, the container suite or a version-specific dependency vulnerability audit. The reported 1,342 passing tests remain packet evidence.
Not safe to merge.
