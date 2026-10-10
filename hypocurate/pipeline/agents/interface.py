"""The common agent interface (PRD 6: the orchestrator calls every agent the same way; step 8a).

`call_agent` runs one agent call, bound to one invocation record:
- the input is the role's complete input from the access layer (`role_input` on the object
  `bind_invocation` returns), rendered as text by the role's module; nothing else enters the request;
- the request goes through a DSPy module (a `Signature` with declared inputs and outputs), with DSPy's
  ChatAdapter and its JSON fallback off (a fallback would be a second, unplanned request), and a
  `RecordedEngine` (every request reserved, sent, recorded);
- failures follow `lm.FAILURES`: "retry" sends the same request once more, "correct" sends it once
  more with the role's fixed corrective note naming the failure code and its specific reason (owner, 2026-10-10:
  a reason is code's own wording, naming only the role's own keys, parts, names and rules, never the failed answer
  and never any error text), "stop" ends the call. At most `MAX_ATTEMPTS` requests per agent call;
- the result is the raw text of the parsed output fields, for the role's module to check. A role
  never gets a result it can act on unless code has checked it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping

from hypocurate.pipeline.agents import libraries
from hypocurate.pipeline.agents.lm import FAILURES, AgentFailure, RecordedEngine

MAX_ATTEMPTS = 2  # register 'request_failure_policy'
NO_NOTE = "none"


def correction_note(code: str, reason: str | None = None) -> str:
    """The only text a retry adds: a fixed sentence naming the failure code and, when the check gave one, its specific
    reason (owner, 2026-10-10). A reason is code's own wording (see `call_agent`)."""
    because = f"; specifically: {reason}" if reason else ""
    return (f"The previous answer could not be used ({code}: {FAILURES[code][0]}{because}). "
            "Answer again, in exactly the requested form, within the length limit.")


def parse_reason(facts: dict | None) -> str | None:
    """The specific reason for an answer DSPy could not read, from its form facts only (never its text)."""
    if not facts:
        return None
    if facts.get("answer_empty"):
        return "the answer was empty"
    missing = sorted(name for name, present in facts.get("output_headers_present", {}).items() if not present)
    if missing:
        return "missing output field: " + ", ".join(missing)
    if not facts.get("completed_marker"):
        return "missing the closing completed marker"
    return None


@dataclass
class AgentResult:
    outputs: dict[str, str] | None
    failure: str | None
    attempts: list[str] = field(default_factory=list)  # one entry per request: "ok" or a failure code
    # Owner, 2026-10-10: one entry per request, the specific reason in code's words, or None (accepted, or no reason).
    reasons: list[str | None] = field(default_factory=list)
    calls: list[int] = field(default_factory=list)       # the recorded model calls
    # Step 8b (owner, 2026-10-07): per failed attempt, fixed facts about the answer's form, never its text.
    details: list[dict] = field(default_factory=list)


def parse_failure_facts(error: BaseException, signature) -> dict | None:
    """For an answer DSPy could not parse: whether each output field's header and the closing marker were present,
    and how many field headers there were. Booleans and a count only: none of the answer's text."""
    response = getattr(error, "lm_response", None)
    if not isinstance(response, str):
        return None
    headers = re.findall(r"\[\[ ## (\w+) ## \]\]", response)
    return {"output_headers_present": {name: name in headers for name in signature.output_fields},
            "completed_marker": "completed" in headers, "header_count": len(headers),
            "answer_empty": not response.strip()}


def call_agent(db, invocation_id: int, signature, inputs: Mapping[str, str], *, model: str, max_tokens: int,
               max_output_chars: int, ceiling: Decimal | None = None, lm_options: Mapping[str, Any] | None = None,
               client_options: Mapping[str, Any] | None = None, check=None) -> AgentResult:
    """One agent call (see the module docstring). `signature` has the role's input fields plus `note`.
    `lm_options`: the role's request settings (for example its effort). `check(outputs)`: the role's
    check that its answer can be read, returning None or a failure code (then corrected like a DSPy parse
    failure); after a refusal, `check.last_reason` may hold its specific reason in code's own words, which is stored
    with the attempt and named in the corrective note (owner, 2026-10-10)."""
    _, dspy = libraries.load()
    engine = RecordedEngine(db, invocation_id, model, max_output_chars=max_output_chars, ceiling=ceiling,
                            client_options=client_options)
    lm = dspy.LM(f"anthropic/{model}", engine=engine, cache=False, num_retries=0, max_tokens=max_tokens,
                 **dict(lm_options or {}))
    adapter = dspy.ChatAdapter(use_json_adapter_fallback=False)
    result = AgentResult(None, None)
    note = NO_NOTE
    try:
        for _ in range(MAX_ATTEMPTS):
            try:
                with dspy.context(lm=lm, adapter=adapter):
                    prediction = dspy.Predict(signature)(**inputs, note=note)
            except Exception as error:  # noqa: BLE001 (classified by code; nothing of its text is kept here)
                code = engine.last_failure or "malformed"
                facts = parse_failure_facts(error, signature) if code == "malformed" else None
                reason = parse_reason(facts)
                if facts is not None:
                    result.details.append({"attempt": len(result.attempts) + 1, "parse": facts})
            else:
                outputs = {name: str(getattr(prediction, name)) for name in signature.output_fields}
                if check is not None:
                    check.last_reason = None
                code = check(outputs) if check is not None else None
                reason = getattr(check, "last_reason", None) if code is not None else None
                if code is not None and getattr(check, "last_problems", None):
                    result.details.append({"attempt": len(result.attempts) + 1, "problems": list(check.last_problems)})
                if code is None:
                    result.attempts.append("ok")
                    result.reasons.append(None)
                    result.outputs, result.failure = outputs, None
                    return result
            result.attempts.append(code)
            result.reasons.append(reason)
            result.failure = code
            action = FAILURES[code][1]
            if action == "stop":
                break
            note = correction_note(code, reason) if action == "correct" else note
        return result
    finally:
        result.calls = list(engine.calls)
        engine.close()
