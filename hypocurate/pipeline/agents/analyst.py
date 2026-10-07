"""The Analyst (step 8b; PRD 3 step 8, 5.7; owner, Q6, A3, B2; register 'analyst_facts').

The Analyst explains a result code has already computed. It reads its access list (claim, domain,
sources_meta, coverage, analyst_facts) at 'analysis', 'closed_without_freeze' or 'narrowed': code's stored
facts only, and below the minimums nothing computed from outcome values. It answers plain text, at most
the role's character limit.

The Analyst writes no digits (owner, 2026-10-07): every number, p-value, set of paper figures, the outcome and the
verdict are {name} placeholders of its named facts (`pipeline.analyst_names`), and code renders the finished text
(`text_checks.render`). Code checks the template (every name given, no digit outside a placeholder, the outcome and
verdict wordings used) and then the finished text (the wording rules; every number is one of the facts); each
failure is corrected once with a note naming only the code. A text that fails twice is discarded (never stored as
the report); the stage keeps counts or rule names, never text. The finished text and its template are stored. The
Analyst never sets the outcome, the verdict, the label or the level: the copy paths copy code's stored
decision. If the Analyst fails for any reason (its checks, the provider, a spending refusal), the run still
completes with code's decision and shows "explanation unavailable" (A3, B2).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from hypocurate.pipeline.agents import libraries, text_checks

UNAVAILABLE = "explanation unavailable"
OUTPUT_DESCRIPTION = ("The explanation, in plain text, a few short paragraphs. No digits: every number, p-value, set of "
                      "paper figures, the outcome and the verdict are written as {name} placeholders from 'facts'.")


def signature(instruction: str):
    _, dspy = libraries.load()

    class AnalystSignature(dspy.Signature):
        claim: str = dspy.InputField(desc="The claim in words (its numbers are given as facts too, by name).")
        facts: str = dspy.InputField(desc="The named facts, as JSON {name: value}: refer to each as {name}.")
        context: str = dspy.InputField(desc="The domain and the chosen sources, as JSON.")
        note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
        report: str = dspy.OutputField(desc=OUTPUT_DESCRIPTION)

    return AnalystSignature.with_instructions(instruction)


def render_inputs(analyst_input: Mapping[str, Any]) -> dict[str, str]:
    """The Analyst's request inputs, built only from its complete access-layer input: the claim, the named facts,
    and the domain and sources (the coverage's numbers reach it as named facts only)."""
    claim = {k: v for k, v in analyst_input["claim"].items() if k in ("text", "narrower_question")}
    return {"claim": json.dumps(claim, sort_keys=True, ensure_ascii=False),
            "facts": json.dumps(analyst_input["analyst_facts"]["names"], sort_keys=True, ensure_ascii=False),
            "context": json.dumps({"domain": analyst_input["domain"],
                                   "sources": [{k: s.get(k) for k in ("key", "name", "grouping_unit")}
                                               for s in analyst_input["sources_meta"]]},
                                  sort_keys=True, ensure_ascii=False)}


def make_check(analyst_input: Mapping[str, Any]):
    """The common interface's check: None, 'empty', 'unknown_name', 'digit_outside_placeholder', 'wording_refused'
    or 'numbers_unmatched'. `check.last_problems` holds counts or rule names, never text; `check.rendered` the
    finished text of an accepted answer."""
    names = analyst_input["analyst_facts"]["names"]
    decision = {"outcome_wording": names.get("outcome_wording"), "verdict": "verdict_wording" in names,
                "verdict_wording": names.get("verdict_wording")}

    def check(outputs: Mapping[str, str]) -> str | None:
        check.last_problems, check.rendered = [], None
        template = outputs["report"].strip()
        if not template:
            return "empty"
        counts = text_checks.placeholder_problems(template, names)
        if counts["unknown_names"]:
            check.last_problems = [counts]
            return "unknown_name"
        if counts["digits_outside_placeholders"]:
            check.last_problems = [counts]
            return "digit_outside_placeholder"
        if counts["required_missing"]:
            check.last_problems = [counts]
            return "wording_refused"
        if counts["result_phrases_missing"]:
            check.last_problems = [counts]
            return "result_phrases_missing"
        report = text_checks.render(template, names)
        problems = text_checks.wording_problems(report, decision, names)
        if problems:
            check.last_problems = problems  # the names of the rules (fixed wording, or a listed phrase)
            return "wording_refused"
        if text_checks.unmatched_numbers(report, names):  # a safeguard: every number came from a name
            check.last_problems = ["numbers_unmatched"]
            return "numbers_unmatched"
        check.rendered = report
        return None

    check.last_problems, check.rendered = [], None
    return check


@dataclass(frozen=True)
class AnalystResult:
    report: str | None
    failure: str | None
    stage_id: int
    calls: list


def run_analyst(engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> AnalystResult:
    """The Analyst's stage. On any failure the stage is closed 'failed' with the code and no text."""
    from hypocurate.access.dispatch import bind_invocation
    from hypocurate.access.inputs import role_input
    from hypocurate.pipeline.agents.interface import call_agent
    from hypocurate.pipeline.agents.runstage import close_stage, open_stage
    from hypocurate.pipeline.agents.settings import recorded

    stage_id, invocation = open_stage(engine, run_id, "analyst", "analyst")
    data = role_input(bind_invocation(engine, invocation))
    s = recorded(engine, invocation)  # finding 2: the recorded version, never the current one
    inputs = render_inputs(data)
    check = make_check(data)
    result = call_agent(engine, invocation, signature(s["instruction"]), inputs, model=s["model"],
                        max_tokens=s["limits"]["max_tokens"], max_output_chars=s["limits"]["max_output_chars"],
                        ceiling=ceiling, lm_options=dict(s["settings"]), client_options=client_options,
                        check=check)
    if result.failure is not None:
        close_stage(engine, run_id, stage_id, "failed", {"code": result.failure, "attempts": result.attempts,
                                                         "failure_details": result.details,
                                                         "shown": f"{UNAVAILABLE} ({result.failure})"}, input_=inputs)
        return AnalystResult(None, result.failure, stage_id, result.calls)
    report = check.rendered
    close_stage(engine, run_id, stage_id, "done", {"report": report, "template": result.outputs["report"].strip(),
                                                   "attempts": result.attempts,
                                                   # owner, 2026-10-07: also for an attempt later corrected
                                                   "failure_details": result.details,
                                                   "check": "numbers written by code from the run record"},
                input_=inputs)
    return AnalystResult(report, None, stage_id, result.calls)
