# Step 5 — second-model review (ChatGPT, 2026-10-05)

Review of `docs/reviews/step05_review_packet.md` (branch `step-05-access`, code commit `81f5003`). Saved verbatim as the owner gave it. The owner accepted all six findings on 2026-10-05, with a threat-model decision that scopes the fixes (see `docs/reviews/step05_summary.md`).

---

There are serious gaps. I would not sign off step 5 as enforcing the isolation described in the packet. The database checkpoint checks are substantially better than the surrounding security boundary.
I reviewed the supplied code and ran isolated probes against the file guard. I did not rerun the reported 620-test suite.
1. The file guard is bypassable from the Python process it guards.
   I reproduced three behaviours using a temporary sentinel file:
   - Normal opening of the file was denied.
   - An already-open descriptor could still read it.
   - Changing file_guard._state["read_roots"] made the previously denied file readable.
   I also confirmed that preloaded ctypes.string_at still works after installation. The claim that every foreign call is refused is therefore incorrect. The test exercises CDLL(None)—a new library load—not the remaining capabilities of preloaded ctypes.
   An irreversible hook is not an immutable policy. Python explicitly warns that these hooks are unsuitable as a sandbox. Python documentation
   Other boundary limitations:
   - The child inherits the environment and starts without isolation flags. Startup hooks and unexpected import paths can execute before repository-path removal and guard installation.
   - Removing a path does not remove previously loaded modules or close their handles.
   - Sockets/network access are unrestricted.
   - Ordinary symlink targets are resolved, but path checking followed by opening is not an atomic containment guarantee.
   Required decision: either restrict execution to trusted application code and describe this as protection against accidental file access, or use an actual process/OS isolation boundary for untrusted Python. Extending the event blacklist will not establish the claimed guarantee.
2. Database access bypasses the entire role/run contract.
   The guarded process intentionally receives database credentials and can connect directly. The database probe demonstrates that. Nothing restricts its SQL to Access.get: it can read source_file, records from another run, outcomes or audit rows directly.
   Additionally, Access accepts caller-selected, mutable role, run_id, stage and source_key:
   - A caller can construct an Analyst access object for another frozen run.
   - A Curator can switch to another source selected for the run; there is no independent assignment check.
   - Concurrent mutation of run_id can make the locked run differ from the run passed to a field reader, because _call rereads mutable attributes.
   This is acceptable only when a trusted dispatcher exclusively controls these objects and credentials. That boundary is not implemented here. Bind role/run/source in trusted orchestration, capture an immutable context per request, and keep unrestricted SQL outside model-controlled tools or executable code.
3. The projectors allow outcome-bearing text through approved fields.
   Field names alone do not establish blinding. Concrete examples:
   - _category accepts any string. A microstructure value such as "FCC; yield strength 48213.579 MPa" reaches the Critic and becomes a dictionary key in the Planner’s category counts.
   - Paper titles, origin keys, alloy labels and flag categories pass through as text.
   - The no-freeze Analyst receives nested plan values, power_assumptions, eligibility-rule text and coverage failure messages without recursive projection.
   - The no-freeze Commentator receives arbitrary Analyst output through gap_report.
   The packet acknowledges that some source text is intentionally approved. That is a disclosure exception, not proof that outcome values cannot appear.
   Use controlled category values and structured reason codes where possible. For deliberately retained free text, explicitly narrow the blinding claim and test the accepted risk. Plant values inside these allowed locations—not just discarded fields.
4. sources_meta does not follow its stated provenance policy.
   The summary says name and licence come from code definitions. _chosen_sources actually reads them from the mutable source table. It also reads interpretation settings there rather than from the run’s sealed source version.
   Consequently, later source edits can change an old run’s metadata, and free text can enter supposedly controlled metadata fields.
   Use the sealed version’s interpretation settings and the intended trusted source-description fields. Test changing the source registry after dispatch.
5. Denied attempts are not always logged.
   The commit-before-AccessDenied design correctly preserves ordinary policy refusals despite a caller rollback. It does not cover:
   - File-guard refusals: no audit logging exists there.
   - Unknown runs and lock timeouts.
   - Reader exceptions other than Refused.
   - Invalid role/stage calls through role_input, which can return {} without calling get.
   The timeout test explicitly expects no audit row. Also, caller-supplied role, field and source strings are copied into messages/log details, so “never a value” is not enforced.
   Distinguish policy denial from access failure, log both through an appropriate bounded mechanism, and specify the fallback when the database itself is unavailable. Do not claim unconditional durable database logging.
6. The planted-value test does not yet cover complete model input.
   role_input is a bundle of field-reader outputs. It excludes agent instructions—even though the fixture plants a value there—plus future message history, tool errors, retry prompts, attachments and any extra content step 8 assembles.
   Test the actual outbound model request when that integration exists. Until then, call this a projected-data test.
   The encoding detector also misses split strings, spelled-out numbers, arbitrary transformations, compression and information conveyed through counts or timing. Expanding its encoding list cannot prove absence of leakage.
   Particularly weak tests are the static pipeline import scan, which can be vacuous before pipeline code exists and misses indirect/dynamic access, and the ctypes test discussed above.
Checkpoint enforcement: with a fixed access context and the established database locking protocol, locking the run before reading its stage correctly serializes rules-lock and dataset-freeze transitions. I found no ordinary SQL checkpoint bypass in that path. Add an actual concurrent checkpoint-transition test; the current concurrency test holds a lock without changing the stage. Separate get calls also do not constitute one atomic input snapshot.
Counts and timing: outcome-status counts and flag classifications intentionally reveal limited outcome-related information. Singleton condition summaries reveal exact grain size or temperature. Those are consequences of the approved contract, not new reasons to remove those fields—but “no row-level value can be inferred” would be false. Timing is not protected.
Scope: I found no substantial unnecessary later-step functionality. The issue is the opposite: nested projection and the trusted model-input boundary cannot remain future work while step 5 claims complete enforcement. Keep this implementation as an access API foundation, but close or accurately delimit these security guarantees before approval.
