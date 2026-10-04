# Controlled duplicate extract

**Constructed test data.** `extract.csv` holds 16 records derived from the frozen MPEA dataset (`data/sources/mpea/MPEA_dataset.csv`). Some overlap MPEA records and some do not. It exists only to test duplicate handling (PRD Sections 5.3, 10 and 14.1). It is never pooled into a real analysis or a reference run.

The two sprint sources share no measurements, so this extract is the only overlap available for testing.

## Format

The same columns as the MPEA dataset, with the header copied verbatim. Records whose paper is not a real publication carry a DOI beginning `10.5555/hypocurate-test-` and say so in their title.

## Fingerprint

The SHA-256 of `extract.csv` is recorded in `data/manifest.json`. A test fails if the file changes.
