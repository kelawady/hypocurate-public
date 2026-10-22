# Reconciler prompt, version 1 (Sprint 2 pilot, 2026-10-23)

The Reconciler runs per document, before the H1 runs (owner, 2026-10-23; register 'pilot_reconciler_placement'), on
the newest S0 of a parsed document, with the compilation's records for that paper. It proposes mappings with quotes;
code applies them with Sprint 1's normalizers and checks them; the owner accepts, rejects or corrects them on the
review sheet. Its outputs are S1 events, never S0.
