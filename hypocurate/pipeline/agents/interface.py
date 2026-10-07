"""The common agent interface (PRD 6: the orchestrator calls every agent the same way; step 8a).

`call_agent` runs one agent call, bound to one invocation record:
- the input is the role's complete input from the access layer (`role_input` on the object
  `bind_invocation` returns), rendered as text by the role's module; nothing else enters the request;
- the request goes through a DSPy module (a `Signature` with declared inputs and outputs), with DSPy's
  ChatAdapter and its JSON fallback off (a fallback would be a second, unplanned request), and a
  `RecordedEngine` (every request reserved, sent, recorded);
- failures follow `lm.FAILURES`: "retry" sends the same request once more, "correct" sends it once
  more with the role's fixed corrective note naming the failure code (never the failed answer and
  never any error text), "stop" ends the call. At most `MAX_ATTEMPTS` requests per agent call;
- the result is the raw text of the parsed output fields, for the role's module to check. A role
  never gets a result it can act on unless code has checked it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping

from hypocurate.pipeline.agents import libraries
from hypocurate.pipeline.agents.lm import FAILURES, AgentFailure, RecordedEngine

MAX_ATTEMPTS = 2  # register 'request_failure_policy'
NO_NOTE = "none"


def correction_note(code: str) -> str:
    """The only text a retry adds: a fixed sentence naming the failure code."""
    return (f"The previous answer could not be used ({code}: {FAILURES[code][0]}). "
            "Answer again, in exactly the requested form, within the length limit.")


@dataclass
class AgentResult:
    outputs: dict[str, str] | None
    failure: str | None
    attempts: list[str] = field(default_factory=list)  # one entry per request: "ok" or a failure code
    calls: list[int] = field(default_factory=list)       # the recorded model calls


def call_agent(db, invocation_id: int, signature, inputs: Mapping[str, str], *, model: str, max_tokens: int,
               max_output_chars: int, ceiling: Decimal | None = None, lm_options: Mapping[str, Any] | None = None,
               client_options: Mapping[str, Any] | None = None, check=None) -> AgentResult:
    """One agent call (see the module docstring). `signature` has the role's input fields plus `note`.
    `lm_options`: the role's request settings (for example its effort). `check(outputs)`: the role's
    check that its answer can be read, returning None or "malformed" (then corrected like a DSPy parse
    failure)."""
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
            except Exception:  # noqa: BLE001 (classified by code; nothing of it is kept here)
                code = engine.last_failure or "malformed"
            else:
                outputs = {name: str(getattr(prediction, name)) for name in signature.output_fields}
                code = check(outputs) if check is not None else None
                if code is None:
                    result.attempts.append("ok")
                    result.outputs, result.failure = outputs, None
                    return result
            result.attempts.append(code)
            result.failure = code
            action = FAILURES[code][1]
            if action == "stop":
                break
            note = correction_note(code) if action == "correct" else note
        return result
    finally:
        result.calls = list(engine.calls)
        engine.close()
