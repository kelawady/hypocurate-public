Three problems need fixing before merge.
1. A stale page can act on a different query version.
   Files: web/app.py, web/templates/review.html, web/templates/query_form.html, pipeline/queries.py.
   Failing case: Alice opens version 1 for review. Someone returns it, edits it and submits version 2. Alice presses Dispatch in her old tab: review_action() retrieves the latest version and dispatches version 2, which Alice never reviewed. Return has the same problem. An old edit form can also overwrite a newer draft.
   Smallest fix: Submit the displayed version ID and a content fingerprint; check them inside the pipeline’s write transaction, under the version lock. Refuse stale submissions. Add two-session tests for review and editing.
2. Exports can turn stored text into spreadsheet formulas.
   File: pipeline/workbook.py, functions build() and records_csv().
   Failing case: A hypothesis or paper-reference string of =1+1 becomes an Excel formula. I reproduced this using the packet’s actual export functions: the reloaded workbook cells had formula type f. The CSV also emitted =1+1 unchanged.
   The Analyst’s label prefix protects that particular cell, but other text fields remain exposed.
   Smallest fix: Explicitly write text as string cells in XLSX; neutralize formula-leading text in the spreadsheet-facing CSV while preserving genuine numeric values. Test exported cell types, not just their displayed contents.
3. Several writes do not record the signed-in person.
   Files: web/app.py, pipeline/queries.py, sources/versions.py, tests/test_web_catalog.py.
   Failing case: Create, submit, edit and dispatch-again validate signed_in_name() but discard its return value. Registration uses the name only in its success message; it is not passed to register(). Consequently, these actions have no durable attribution to the person who performed them.
   The registration test passes because it checks the name in the response—not in a stored audit record.
   Smallest fix: Pass the session name into these pipeline functions and persist the actor and action within the write transaction. Test attribution after reopening the stored record.
Verification: I reproduced the formula issue and the stale review handler’s selection of version 2 using extracted functions with mocked database inputs. The remaining findings are from code inspection; I did not run PostgreSQL, Docker or the full suite.
I found no weakened assertion in the listed existing-test changes. However, the fresh-process isolation test still visits only the older run pages, so it does not establish isolation for the new screens. The packet’s failing image-suite stall test also remains unresolved; its cause was not independently verified here.
not safe to merge
