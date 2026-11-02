# HypoCurate

HypoCurate tests a scientific hypothesis against evidence collected from papers and databases. A scientist states a
hypothesis in words. A language-model agent drafts an evidence plan: which records count, under which test
conditions, and which statistical test decides the answer. The plan is fixed before any data are gathered. An agent
extracts candidate records from papers. Code then applies the plan to every record, keeps or excludes each one with a
reason, and runs the fixed test.

The proof of concept tests grain-size strengthening in high-entropy alloys, the well-established claim that yield
strength rises as grain size falls. It uses the MPEA database (Borg et al. 2020) and records the agent extracted from
10 papers cited by that database. Every run stores its plan, its model calls, its records and the reason each record
was kept or excluded, so any number in a result can be traced to its source.

This guide is for trying the system on the hosted site. Nothing needs to be installed and no API key is needed.

## Access

- Site: https://hypocurate-web.onrender.com
- Sign in with **Your name** (any name, recorded with what you do on the site) and the shared **Password**:
  `<PASSWORD — supplied separately>` (see the Assets section of the midway report). The password is not in this
  repository.
- Each run calls language models and costs a few cents (re-running the main result costs about $0.05). The site
  enforces spending caps of **$2 per run** and **$50 per month**. They are shown in the Spending panel on most pages.
  When the monthly cap is reached, new runs are refused until the next month.
- Everything you do is stored in the live database and is visible to the next visitor.

## Reproduce the main result

The main result of the midway report is run 11, query **Q-0010**. It tests the hypothesis against the augmented pool:
the MPEA database plus the records the agent extracted.

1. Sign in, then choose **Queries** in the menu and open **Q-0010**.
2. The page heading is the stored claim: "validation V5 (H1, augmented pool: MPEA + extracted): In single-phase FCC
   high-entropy alloys tested in tension at room temperature, yield strength increases with decreasing grain size."
   The part in front of the colon is a label we added during the pilot. The hypothesis itself is the sentence after
   the colon.
3. Press **Dispatch again (a new run)**. You are taken to the new run's page, which updates by itself. This query uses
   the fixed reference plan, so the run needs no confirmation and goes from queued to running to completed. Run 11 took
   about 2 minutes, plus any time waiting in the queue.
4. While another run of Q-0010 is still open (someone else may have just pressed the button), the button is not shown,
   or is refused if you press it at the same moment. Wait a few minutes and reload the page.

**What you should see** in the Results statement of the new run, as in run 11 (open **Runs** and choose run 11 to
compare):

| Item | Expected |
|---|---|
| Records, alloys, papers | 77 records on 13 alloys, from 20 informative groups (each group is a paper) |
| Slope k | 419.7 MPa·µm^0.5, standard error 62.3 MPa·µm^0.5 (one cluster-robust standard error, grouped by paper) |
| p-value | one-sided p ≈ 9.7e-7 |
| Outcome and verdict | sufficient in the sources searched, verdict supported, evidence level 6 |

The counts, the slope, the standard error, the p-value and the verdict must match exactly. The page rounds the slope
and standard error. Run 11's full-precision values (419.73474127880974 and 62.309086460668425, with 63 residual
degrees of freedom) are recorded in the [final report](docs/sprint2/final_report_2026-10-23.md). The run number, the
time, the cost and the Analyst's written explanation will differ.

The numbers are the same because nothing in the result depends on a model or on chance. The new run reads the same
sealed (fingerprinted) versions of the two sources, the plan is built by code from the same settings, and the
statistics are computed by code from the frozen records. The only model calls in this run are the Critic, which labels
flags but decides nothing, and the Analyst, which writes the explanation. The numbers would differ only if a new
version of a source were loaded or the statistics code were changed.

## What the run page shows

From top to bottom, a completed run's page shows:

- **Results statement (written by code)**: the outcome, the verdict, the estimate with its standard error and
  p-value, and the counts, with the evidence level dial beside it.
- **Plan (fixed at the rules lock)**: the evidence plan as stored before any record was gathered, in the same parts
  as Table 1 of the midway report. The hypothesis row shows the stored claim with the question as code tested it. The
  rules lock is the first of two checkpoints: after it, nobody can change the plan for this run.
- **Explanation by the Analyst**: written by a language model and labelled as such. It may misdescribe details. The
  numbers in the Results statement above it are the authoritative result.
- **Plot of the data and the fitted relationship.**
- **Each source alone, and all together**: the pooled result, which gives the verdict, and each source's result on
  its own. In run 11 the extracted source appears as `extracted_pilot` here and in the plot legend, and as "Extracted
  records (Sprint 2 pilot)" in the Sources list. Both names are the same source. It shows 0 records alone because a
  fit uses only alloys measured at two or more grain sizes, and the alloy of its one usable record has its other grain
  sizes only in MPEA. In the pooled test that record counts, so 77 = 76 MPEA records + 1 extracted record.
- **Sensitivity sets**: the test repeated with one rule of the plan changed at a time. They are shown beside the
  verdict and never change it.
- **Cautions** and any **Flags raised by code** (for example possible duplicates between sources).
- **Checkpoints**: the rules lock and the dataset freeze (the second checkpoint, after which the record set is fixed
  and fingerprinted), each with its time and fingerprint.
- **Sources**, and **Tokens and cost** for every model call.
- **Download data (workbook)** and **Records as CSV** at the top give every record used and not used, with its reason.

## Try your own claim

You can enter your own claim with **New query**, then **Submit for review**, then **Review and dispatch** and
**Dispatch**. The Planner agent reads the claim and drafts the plan, and the run waits until you press **Review and
confirm the question as tested** and then **Confirm the question as tested** on its page. Choose MPEA and/or Texas A&M
as sources, not the extracted source, which only the fixed reference plan can use.

In this version a claim is tested only against the records already loaded, with the one supported model (yield
strength against grain size). There is no literature search and no live paper reading. A claim outside that scope
ends as insufficient, is narrowed to a smaller question linked to the original, or is stopped before testing, and the
page says why.

## Extraction results

The agent read the 10 papers we had access to among the 28 behind the database's FCC grain-size records. It found 48
candidate records. On four papers it matched 23 of 25 records (92%) in a reference extraction, which was prepared with
AI assistance (Codex) and reviewed by the author, not a blind human key. Only 5 candidate records were usable, mostly
because the other strengths appeared only in graphs. Details are in
[docs/sprint2/final_report_2026-10-23.md](docs/sprint2/final_report_2026-10-23.md) and
[docs/sprint2/p6_tables_2026-10-23.md](docs/sprint2/p6_tables_2026-10-23.md).

## Code map

| What | Where |
|---|---|
| Agents (Planner, Critic, Analyst, Curator) and the spending caps | [hypocurate/pipeline/agents/](hypocurate/pipeline/agents/) |
| Paper extraction (Extractor) and reconciliation | [hypocurate/pipeline/extraction/](hypocurate/pipeline/extraction/), [hypocurate/pipeline/reconcile.py](hypocurate/pipeline/reconcile.py), [hypocurate/documents/](hypocurate/documents/) |
| The plan, its defaults and the two checkpoints | [hypocurate/pipeline/plan.py](hypocurate/pipeline/plan.py), [profile.py](hypocurate/pipeline/profile.py), [checkpoints.py](hypocurate/pipeline/checkpoints.py) |
| Curation rules (flags, keep or exclude each record) | [flags.py](hypocurate/pipeline/flags.py), [checks.py](hypocurate/pipeline/checks.py), [eligibility.py](hypocurate/pipeline/eligibility.py) |
| Statistics and calibration | [statistics.py](hypocurate/pipeline/statistics.py), [calibration.py](hypocurate/pipeline/calibration.py) |
| A run from start to end, and the worker | [orchestrator.py](hypocurate/pipeline/orchestrator.py), [hypocurate/worker.py](hypocurate/worker.py) |
| What each agent may see | [hypocurate/access/](hypocurate/access/) |
| Sources and their adapters | [hypocurate/sources/](hypocurate/sources/) |
| Scoring the extraction | [hypocurate/scoring/](hypocurate/scoring/) |
| The website | [hypocurate/web/](hypocurate/web/) |
| Every assumption and default, with who decided it | [hypocurate/assumptions.json](hypocurate/assumptions.json) (shown on the site's Assumptions page) |
| Tests | [tests/](tests/) |

## Limits of this version

- One model only: yield strength against grain size.
- No live paper reading. New runs reuse the sources already loaded.
- No literature search.
- Strengths shown only in graphs are flagged but not read.

## For developers

Running the system and the tests locally, deployment, migrations and the internals are described in
[docs/DEVELOPING.md](docs/DEVELOPING.md). The specification is [docs/PRD_sprint1.md](docs/PRD_sprint1.md).

The MPEA dataset is Apache-2.0 and its paper (Borg et al. 2020, in `data/sources/mpea/documentation/`) is CC BY 4.0.
The Texas A&M dataset and its paper are MIT-licensed. Origins, licences and fingerprints are in
[data/manifest.json](data/manifest.json).
