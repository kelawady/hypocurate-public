One item remains open: the temperature matcher still accepts parts of other numeric expressions. The other fixes close the identified defects, subject to the stated import and logging trust boundaries.
1. Imported curation — fixed within the trusted-export boundary.
   check_curation() now validates the base fingerprint, interpretation settings, each quote against the version’s own document, its line, value, term and acceptance metadata. It runs before registration/sealing and before application. My probes rejected the earlier wrong-base, absent-quote and blank-acceptor cases.
   It does not authenticate approval by itself: changing an acceptor to another nonblank name still passes validation. Exact approved bytes are protected by the normal manifest-pinned import; newly generated exports rely on the database’s accepted decisions. That is consistent with the packet’s explicit trust boundary, but “the validator accepts only approved exports” would be incorrect.
2. Database enforcement — fixed for the mismatched-term and NULL findings.
   The value-to-term mapping, explicit non-NULL requirements and coalesce(..., false) close those cases. JSON null is also rejected.
   The list-equality test adequately detects vocabulary drift. Together with the SQL/code agreement tests, it provides useful behavioral coverage—not proof of equivalence. Both implementations still share the numeric defect in item 5.
3. Spending — fixed.
   All totals are now read after acquiring the required locks, in consistent run → month order. This closes the stale-total race for curation, lower ceilings and monthly spending. The new same-invocation tests target the actual failing interleaving, rather than relying only on simultaneous thread starts.
4. Recording and reservation failures — fixed.
   All recording branches now use _record(). Failures become recording_failed, with no further request; reservation failures become reservation_failed, before sending anything. I reproduced both stop classifications. Existing reservations remain counted at their maximum while cost is unknown.
5. Matching — partly fixed.
   The original negative-number, decimal and whitespace cases are closed. However, I reproduced these accepted proposals for 25°C:
   - “All specimens were tested at 1,025 °C in laboratory air.”
   - “All specimens were tested between 20 - 25 °C in laboratory air.”
   In the first, quotes._PLAIN accepts the suffix of 1,025. In the second, it accepts a range endpoint despite the documented refusal of ranges. Migration 0005’s corresponding pattern has the same gaps.
   Fix: refuse these unsupported numeric forms in both implementations, and add them to the Python tests and SQL agreement cases. No general-purpose scientific-number parser is needed.
   Otherwise, the whole-word rules, spelling variants and quote bounds implement the owner decisions. They remain keyword filters: for example, the accepted testing word “deformed” can describe processing rather than testing. Human review still has to establish support and source-wide applicability. The documented safe refusals are acceptable.
6. Run-scoped Curator — fixed.
   The invocation constraint now explicitly excludes the Curator from run scope. The replacement test verifies refusal even with otherwise valid run, stage and setting references.
7. Logging — fixed for the reviewed request path.
   Exception messages and chained messages are no longer logged or included in corrective requests. My planted exception text was absent; only codes, types and locations appeared. The header test adds meaningful coverage.
   This is not a blanket guarantee about third-party logging, which the packet now correctly states as a limitation.
8. Changed tests/helpers — fixed; no material protection lost identified.
   Switching cost-test stages to the Critic preserves the numeric assertions. Using a Planner invocation preserves the non-registration proposal rejection. Adding documentation and rebinding the constructed fixture’s base fingerprint preserves its duplicate-handling purpose. That fixture operation must remain test-only; it is not evidence of approval for a different production source.
New findings: only the two remaining numeric-matching cases above. They are the remaining merge blocker.
I ran 66 quote regression cases plus focused curation-validation and failure-handling probes. I did not rerun PostgreSQL, the complete provider path or the full suite; the two tests requiring the actual frozen paper files were not executed locally.
Not safe to merge.
