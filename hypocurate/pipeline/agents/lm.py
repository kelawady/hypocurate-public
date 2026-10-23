"""The request path of every agent call (step 8a): reserve, request, record (register
'model_call_recording', 'request_failure_policy').

`RecordedEngine` is a DSPy engine (`complete(Request) -> Response`, DSPy's supported interface). For
each request it:
1. reserves the call's maximum cost (`spend.reserve`, one transaction that checks the caps and
   records the call as started); a refusal sends nothing;
2. sends the request through DSPy's own litellm engine, outside any database transaction, one HTTP
   attempt (litellm's retries are off, `libraries.load`);
3. records the outcome (`spend.finish`): the reported usage and its cost (`prices.cost`), or a
   failure with no usage and a fixed code. If that recording fails, on any branch (a provider
   failure, a reply without usage, a usable reply), the call ends with `recording_failed`, which
   stops it: no further request, and the call stays started, counted at its maximum cost (step 8a
   review, finding 4). A reservation that cannot be written ends with `reservation_failed`; nothing
   is sent;
4. turns a reply that cannot be used into a fixed code after it is recorded: truncated (the output
   limit was reached), refused, a tool call (no tools are offered), empty or over-long text.

Every failure is an `AgentFailure` with a fixed code (`FAILURES`); its message is the code's fixed
text. The process log gets the code, the exception's type (and the types of its causes) and where it
was raised (file, line, function), never the exception's text: a provider's or library's message can
quote the request, and this path never writes it anywhere (step 8a review). Nothing a provider, a
library or the database wrote ever travels with the error or into a later request. The last failure
is also kept on the engine (`last_failure`), because DSPy may wrap exceptions raised inside it.
Not covered: what a library logs by itself (litellm's own debug logging is off unless a process
turns it on).
"""
from __future__ import annotations

import json
import logging
import traceback
from decimal import Decimal
from typing import Any, Mapping

from hypocurate.pipeline.agents import libraries, prices, spend

LOG = logging.getLogger("hypocurate.pipeline")
DEFAULT_TIMEOUT_SECONDS = 300
# code -> (fixed text, what the runner does: "retry" (the same request again), "correct" (again, with
# the fixed corrective note), or "stop").
# The accounting failures that stop the whole run, not only the call (step 8b fix round, finding 3): after either,
# no further model request is made for the run (no further Critic batch, no Analyst), and the run is left running,
# with a call whose recording failed still started, for step 9's recovery.
RUN_STOPS = ("recording_failed", "reservation_failed")
FAILURES: Mapping[str, tuple[str, str]] = {
    "provider_unavailable": ("the provider could not be reached or did not answer in time", "retry"),
    "model_auth": ("the provider refused the credentials", "stop"),
    "provider_rejected": ("the provider refused the request", "stop"),
    "cost_unknown": ("the provider reported no usage, so the cost is unknown", "stop"),
    "recording_failed": ("the call could not be recorded", "stop"),
    "reservation_failed": ("the call could not be reserved", "stop"),
    "refused": ("the model declined to answer", "stop"),
    "truncated": ("the answer reached the output limit", "correct"),
    "tool_call": ("the answer asked for a tool; none is offered", "correct"),
    "empty": ("the answer was empty", "correct"),
    "over_long": ("the answer was longer than the role allows", "correct"),
    "malformed": ("the answer could not be read in the requested form", "correct"),
    "spending_cap_run": ("the run's spending cap would be exceeded", "stop"),
    "spending_cap_curation": ("the curation's spending cap would be exceeded", "stop"),
    "spending_cap_document": ("the document invocation's spending cap would be exceeded", "stop"),  # Sprint 2 pilot
    "spending_cap_month": ("the monthly spending cap would be exceeded", "stop"),
    "ceiling_reached": ("the ceiling set for this call would be exceeded", "stop"),
    "invocation_unknown": ("no such invocation", "stop"),
    # Step 8b: the roles' own checks of an answer that could be read (each corrected once).
    "invalid_plan": ("the plan is not valid for the supported template or does not match the claim's scope", "correct"),
    "numbers_unmatched": ("a number in the text is not one of the facts given, as given", "correct"),
    "wording_refused": ("the text uses wording that is not allowed", "correct"),
    # Owner, 2026-10-07: the Analyst's placeholders.
    "unknown_name": ("a placeholder names no fact given", "correct"),
    "digit_outside_placeholder": ("a digit was written outside a placeholder; every number is a placeholder", "correct"),
    "result_phrases_missing": ("with a verdict, the pooled p-value phrase and paper-figures phrase must be used", "correct"),
}


class AgentFailure(Exception):
    """A failed agent request, with a fixed code and only the code's fixed text."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(f"{code}: {FAILURES[code][0]}")


def _classify(error: BaseException) -> str:
    lm15 = libraries.lm15()
    if isinstance(error, lm15.AuthError):
        return "model_auth"
    if isinstance(error, (lm15.RateLimitError, lm15.ServerError, lm15.TimeoutError, lm15.TransportError)):
        return "provider_unavailable"
    return "provider_rejected"


def _keep(code: str, error: BaseException) -> None:
    """The failure in the process log: its code, types and places, never its text."""
    chain, seen, current = [], set(), error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(type(current).__qualname__)
        current = current.__cause__ or current.__context__
    frames = [f"{f.filename}:{f.lineno} {f.name}" for f in traceback.extract_tb(error.__traceback__)]
    LOG.error(json.dumps({"agent_request_failure": code, "exception_types": chain, "raised_at": frames}))


def request_bytes(request: Any) -> int:
    """The UTF-8 length of the request's messages and settings as JSON: at least its token count."""
    return len(json.dumps(libraries.request_kwargs(request), default=str, ensure_ascii=False).encode("utf-8"))


class RecordedEngine:
    def __init__(self, db, invocation_id: int, model: str, *, max_output_chars: int,
                 ceiling: Decimal | None = None, client_options: Mapping[str, Any] | None = None):
        prices.price(model)  # an unpriced model is refused before anything else
        self._db, self._invocation, self._model = db, invocation_id, model
        self._max_output_chars, self._ceiling = int(max_output_chars), ceiling
        options = {"timeout": DEFAULT_TIMEOUT_SECONDS, **(client_options or {})}
        self._inner = libraries.litellm_engine(**options)
        self.last_failure: str | None = None
        self.calls: list[int] = []

    def _fail(self, code: str):
        self.last_failure = code
        return AgentFailure(code)

    def complete(self, request):
        self.last_failure = None
        if not request.config.max_tokens:
            raise ValueError("every agent request names its output limit")
        bound = prices.max_cost(self._model, request_bytes(request), request.config.max_tokens)
        try:
            call = spend.reserve(self._db, self._invocation, self._model, bound, self._ceiling)
        except spend.SpendingRefused as refused:
            raise self._fail(refused.code) from None
        except Exception as error:  # noqa: BLE001 (nothing was reserved, so nothing is sent)
            _keep("reservation_failed", error)
            raise self._fail("reservation_failed") from None
        self.calls.append(call)
        failure = None
        try:
            response = self._inner.complete(request)
        except Exception as error:  # noqa: BLE001 (classified; the original goes to the process log only)
            failure = _classify(error)
            _keep(failure, error)
        if failure is not None:
            self._record(call, "failed", code=failure)
            raise self._fail(failure)
        usage = response.usage
        if usage is None or usage.input_tokens is None or usage.output_tokens is None:
            self._record(call, "failed", code="cost_unknown")
            raise self._fail("cost_unknown")
        read, write = usage.cache_read_tokens or 0, usage.cache_write_tokens or 0
        self._record(call, "succeeded", usage=(usage.input_tokens, usage.output_tokens, read, write))
        code = _unusable(response, self._max_output_chars)
        if code:
            raise self._fail(code)
        return response

    def _record(self, call: int, status: str, *, usage=None, code: str | None = None) -> None:
        """Finishes the call; any failure to do so (on every branch) ends the agent call with
        `recording_failed`, and the call stays started, counted at its maximum cost."""
        try:
            if usage is None:
                spend.finish(self._db, call, status, code=code)
            else:
                input_tokens, output_tokens, read, write = usage
                spend.finish(self._db, call, status, input_tokens=input_tokens, output_tokens=output_tokens,
                             cached_tokens=read,
                             cost=prices.cost(self._model, input_tokens, output_tokens, read, write))
        except Exception as error:  # noqa: BLE001
            _keep("recording_failed", error)
            raise self._fail("recording_failed") from None

    def stream(self, request):
        raise NotImplementedError("the agents do not stream")

    def close(self) -> None:
        self._inner.close()


def _unusable(response, max_output_chars: int) -> str | None:
    """A recorded reply that cannot be used, as a code; None if it can."""
    reason = response.finish_reason
    if reason == "length":
        return "truncated"
    if reason in ("content_filter", "refusal"):
        return "refused"
    if response.tool_calls or reason == "tool_calls":
        return "tool_call"
    text = response.text or ""
    if not text.strip():
        return "empty"
    if len(text) > max_output_chars:
        return "over_long"
    return None
