# Extractor prompts, version 1 (Sprint 2 pilot)

Versioned files, not code (Design D17). The pilot's model-call Extractor reads `extract.md` (the extraction call's
instruction) and `verify.md` (the ChatExtract-style verification call's instruction) from here, and validates the
extraction answer against `output_schema.json`. A change to any file after its first use is a new version directory
(`v2/`); every stored output records the prompt version it used.

Version 1 carries the owner's decisions of 2026-10-22 and 2026-10-23: the specification's context fields are recorded,
never used as a filter; a value shown only in a figure is returned as "figure only" with an ambiguity note; a range is
kept as written; rows reporting cited papers' data are marked `reported_from`, never claimed as the paper's own.
