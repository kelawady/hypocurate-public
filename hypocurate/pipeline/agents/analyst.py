"""The Analyst (step 8b; PRD 3 step 8, 5.7; owner, Q6, A3, B2; register 'analyst_facts').

The Analyst explains a result code has already computed. It reads its access list (claim, domain,
sources_meta, coverage, analyst_facts) at 'analysis', 'closed_without_freeze' or 'narrowed': code's stored
facts only, and below the minimums nothing computed from outcome values. It answers plain text, at most
the role's character limit.

Code checks the text (`text_checks`): every number must be one of the facts given, as given
(`numbers_unmatched`), and the wording must follow the rules (`wording_refused`); each is corrected once
with a note naming only the code. A text that fails twice is discarded (never stored as the report). The
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
OUTPUT_DESCRIPTION = "The explanation, in plain text: a few short paragraphs, every number exactly as in the facts."


def signature(instruction: str):
    _, dspy = libraries.load()

    class AnalystSignature(dspy.Signature):
        claim: str = dspy.InputField(desc="The claim in words, with its query number.")
        facts: str = dspy.InputField(desc="The facts code stored for the run, as JSON: the only source of numbers.")
        context: str = dspy.InputField(desc="The domain, the chosen sources and what was searched, as JSON.")
        note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
        report: str = dspy.OutputField(desc=OUTPUT_DESCRIPTION)

    return AnalystSignature.with_instructions(instruction)


def render_inputs(analyst_input: Mapping[str, Any]) -> dict[str, str]:
    """The Analyst's request inputs, built only from its complete access-layer input."""
    return {"claim": json.dumps(analyst_input["claim"], sort_keys=True, ensure_ascii=False),
            "facts": json.dumps(analyst_input["analyst_facts"], sort_keys=True, ensure_ascii=False),
            "context": json.dumps({"domain": analyst_input["domain"], "sources": analyst_input["sources_meta"],
                                   "coverage": analyst_input["coverage"]}, sort_keys=True, ensure_ascii=False)}


def make_check(analyst_input: Mapping[str, Any]):
    """The common interface's check: None, 'empty', 'numbers_unmatched' or 'wording_refused'."""
    decision = analyst_input["analyst_facts"].get("decision") or {}

    def check(outputs: Mapping[str, str]) -> str | None:
        report = outputs["report"].strip()
        if not report:
            return "empty"
        if text_checks.unmatched_numbers(report, analyst_input):
            return "numbers_unmatched"
        if text_checks.wording_problems(report, decision, analyst_input["analyst_facts"]):
            return "wording_refused"
        return None

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
    from hypocurate.pipeline.agents.settings import SETTINGS

    stage_id, invocation = open_stage(engine, run_id, "analyst", "analyst")
    data = role_input(bind_invocation(engine, invocation))
    s = SETTINGS["analyst"]
    inputs = render_inputs(data)
    result = call_agent(engine, invocation, signature(s["instruction"]), inputs, model=s["model"],
                        max_tokens=s["limits"]["max_tokens"], max_output_chars=s["limits"]["max_output_chars"],
                        ceiling=ceiling, lm_options=dict(s["settings"]), client_options=client_options,
                        check=make_check(data))
    if result.failure is not None:
        close_stage(engine, run_id, stage_id, "failed", {"code": result.failure, "attempts": result.attempts,
                                                         "shown": f"{UNAVAILABLE} ({result.failure})"}, input_=inputs)
        return AnalystResult(None, result.failure, stage_id, result.calls)
    report = result.outputs["report"].strip()
    close_stage(engine, run_id, stage_id, "done", {"report": report, "attempts": result.attempts,
                                                   "check": "numbers checked against the run record"}, input_=inputs)
    return AnalystResult(report, None, stage_id, result.calls)
