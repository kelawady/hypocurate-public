# Extractor prompts, version 3 (Sprint 2 pilot, 2026-10-23)

The owner's decisions of 2026-10-23 (evening), on version 2's first live results:
- extract: every record carries the specification's context fields; a condition stated once (for example in the methods)
  that applies to all specimens is copied into each record, with the methods sentence as provenance and the definition
  "from methods, applies to all specimens". Whether the Extractor does this is one of the things the pilot measures.
- verify: every item is answered (yes / no / cannot tell), context fields included; a skipped item is still recorded as
  "not answered" by code and counted.
`output_schema.json` is unchanged from version 2. Versions 1 and 2 are kept as they were used.
