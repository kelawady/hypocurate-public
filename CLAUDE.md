# HypoCurate — instructions for Claude Code

Version: 2026-10-04 v1. Owner: Khalid El-Awady.

## What this is

HypoCurate takes a scientific hypothesis in words (first domain: grain-size strengthening in metal alloys), searches registered data sources, and ends in one of three outcomes stated for the sources searched: **sufficient** (a test and a verdict), **partly sufficient** (no verdict on the original question; a narrower question is a separate linked record), or **insufficient** (a gap report, never a forced verdict).

The full specification is `docs/PRD_sprint1.md`. Read the relevant section before you write code. If this file and the PRD disagree, stop and ask.

## How we work

1. **One build step at a time.** The build order is PRD Section 15. Do not start a step until the owner says so. Do not build ahead.
2. **Plan first.** For each step, propose a plan and wait for approval before changing files.
3. **Tests are the gate.** Every step adds tests to the regression suite. A step is finished only when the whole suite passes. Never weaken, skip or delete a test to make it pass; never widen a tolerance. If a test seems wrong, stop and ask.
4. **End of each step:** write a short summary in `docs/reviews/` (what was built, which tests were added, what is open) so a second model (ChatGPT) can review it. Its review is advice; the tests decide.
5. **Any change to a safeguard** (access layer, checkpoints, validity checks, eligibility rules) needs the owner's approval and a second-model review, even if small.
6. **Ask one question at a time**, in plain English, with options and a recommendation.
7. **Deferred ideas go in the backlog** (PRD Section 18). Do not build them.
8. Small commits with clear messages. Never commit to `main` anything that fails the suite.
9. **Any change to `.github/workflows/` needs the owner's explicit review**, even if the workflow tests pass. A workflow test cannot stop its own job from being skipped (for example by a job-level condition), and Render counts a skipped check as passed.

## Rules the code must never break

1. **Code decides; agents advise.** Inclusion of records, flags, the choice of test, data sufficiency and the verdict are computed by code. No language model output may set them.
2. **Access contract (PRD Section 4).** Every agent reads data only through the access layer, which holds an allow-list of fields per role and stage. Anything else raises `AccessDenied` and is written to the audit log. Tests check a role's *complete* input, including a planted-value test.
   - Planner: fills template parameters; sees counts only, never outcome values.
   - Curator: extraction only; is not told the direction of the claim; has no say over inclusion.
   - Critic: classifies flags from sources and metadata; is told the kind of flag, not the numbers; never sees outcomes.
   - Analyst: explains results that code has already computed.
   - Commentator: outside the decision path; a different model; optional. Its numbers are checked against the run record; label: "numbers checked against the run record".
3. **Two checkpoints (PRD 5.6).** *Rules lock* before curation: the model, scope, exclusion rules and data-sufficiency option are fixed. *Dataset freeze* before analysis: the record set is fixed and fingerprinted. Nothing changes after its checkpoint, by agent or by person. Later removals are sensitivity analyses only and never change the verdict.
4. **Stored is not analysed (PRD 5.3).** Every record found is kept. Eligibility for the test is a separate decision by code under the locked rules. Conflicting records are preserved, not automatically pooled.
5. **Two validity checks that can never be waived (PRD 5.7).** (1) Can a coefficient be fitted? (2) Is inference valid (at least 1 residual degree of freedom and at least 2 independent groups)? If 1 passes and 2 fails: report the coefficient only, with no uncertainty, no p-value and no verdict.
6. **One supported model in sprint 1.** Yield strength = baseline per alloy + k × (grain size in µm)^-1/2; ordinary least squares with alloy intercepts; cluster-robust standard errors grouped by paper with the small-sample correction; one-sided test of k > 0 at 0.05 against a t distribution with (groups − 1) degrees of freedom; only alloys with at least 2 distinct grain sizes. Do not add models.
7. **Data sufficiency is a query parameter fixed at rules lock (PRD 5.8).** Default: fixed minimum (30 records, 5 alloys with at least 2 grain sizes, 10 independent papers, 10 residual degrees of freedom). "Use what is available" waives the threshold only, never the validity checks, and labels the result exploratory.
8. **A narrower question is a separate record**, linked to the original. The original gets no verdict.
9. **Three kinds of "nothing found" stay distinct:** a reported negative result, missing evidence, and a failed search.
10. **Model-recalled data are never pooled** and never count toward a verdict.
11. **Per-run calibration (PRD 5.10) is a flag, not a gate.** When inference cannot run, show "calibration unavailable" with the reason. Software correctness (pass/fail against an independent reference) is separate from calibration (a reported finding).
12. **Every model call is recorded** with tokens and actual cost (`model_call`). Spending caps: $2 per run, $50 per month.
13. **Wording:** outcomes are always stated "in the sources searched". Never write that data "do not exist".

## Environment

- Development happens in a GitHub Codespace. Nothing lives on the owner's laptop. The site runs on Render: pushing to `main` on GitHub deploys it.
- Stack: Python, FastAPI + Jinja + HTMX, one background worker (same code as the command line), PostgreSQL + Alembic, DSPy + litellm, statsmodels/scipy, Docker from day one (`Dockerfile`, `docker-compose.yml`, `render.yaml`).
- Repository layout: PRD Section 6.1.
- **Secrets** (API keys, database URL, login password) live in `.env` locally and in Render environment variables. Never commit them, print them, or put them in tests. Keep `.env.example` with names only.
- Do not create Render services or anything else that costs money without asking first.

## Reference material in `docs/`

- `PRD_sprint1.md` — the specification (PDF copy alongside).
- `HypoCurate_Combined_Overview_2026-10-04_v3.13.pdf` — background and research questions.
- `glossary.json` — the 41 explanation texts for popups and the Help page. One source; do not duplicate the texts in templates.
- `mockup_screens/` — the nine target screens.
- `reference/worked_example.py`, `reference/calibration_example.py` — the scripts that produced the reference numbers. They contain file paths from another machine; treat them as a statement of method, not as code to import.

## Reference numbers (fixed-plan test, PRD 14.1a)

Pooled: 98 records, 22 alloys, 21 groups, 75 residual degrees of freedom, k = 428 ± 64, p ≈ 8e-7. First source alone (MPEA): 77 records, 20 papers, k = 427 ± 61, p ≈ 6e-7. Second source alone (Texas A&M): coefficient ≈ 1173, one group, no uncertainty, no verdict.
