# Extractor prompts, version 1 (Sprint 2 pilot)

Versioned files, not code (Design D17). The pilot's model-call Extractor (written Friday, R4) reads `extract.md` and
`verify.md` from here and validates the answer against `output_schema.json`. A change to any file is a new version
directory (`v2/`), and every stored output records the prompt version it used. Nothing here is sent to a model until
the Extractor's access allow-list and its planted-value test exist (owner, 2026-10-22, D-b).
