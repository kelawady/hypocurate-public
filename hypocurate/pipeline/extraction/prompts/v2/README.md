# Extractor prompts, version 2 (Sprint 2 pilot, 2026-10-23)

Version 1 was sent once (ijplas.2018.10.005, 2026-10-23) and both attempts were refused as malformed: its instruction
named an output schema that the request did not contain. Version 2 keeps version 1's instructions, says that every
record has "values", "links" and "reported_from", and the request appends this directory's `output_schema.json` to the
extraction instruction (`settings.extractor_variant`). `verify.md` and `output_schema.json` are unchanged from v1.
Version 1 is kept as it was used.
