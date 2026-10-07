"""The Critic (step 8b; PRD 3 step 6, 4; owner, A7; register 'critic_classes').

Between the rules lock and the dataset freeze, after Checks, the Critic classifies the flags code raised.
It reads its access list at 'curation' (sources_meta, record_metadata, flags_kind): each flag's kind,
category and record ids, never the numbers compared. The request carries only the metadata of the records
the flags name. Flags are sent in batches of at most `max_flags_per_call` (each batch its own stage result,
invocation and call).

The answer: one JSON object, one key per flag id (as text), each {"class": <code>, "reason": <text>}. Code
checks each entry: the flag is one of the batch's, the class is one of `CRITIC_CLASSES`, the reason is
1 to 300 characters (never truncated). An entry that fails is left unclassified with its refusal code, and
the others stand (no retry). An answer that is not a JSON object is malformed (corrected once).

**No code decision reads the class** (owner's standing requirement): Inclusion, the freeze, Statistics,
the narrowing and completion read flags only through `flags_kind` and `set_flags`, which carry no class;
`tests/test_critic.py` changes every class and finds every decision, set, fingerprint and result
unchanged. The class and reason are shown to people only (A7).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from sqlalchemy import Connection, Engine, text

from hypocurate.access.vocabulary import CRITIC_CLASSES, CRITIC_REASON_MAX
from hypocurate.pipeline.agents import libraries
from hypocurate.pipeline.agents.lm import RUN_STOPS
from hypocurate.pipeline.writes import Refused, write

_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.S)
OUTPUT_DESCRIPTION = ('One JSON object with one key per flag id (as text); each value {"class": <one of the allowed '
                      'classes>, "reason": "<at most 300 characters, from the metadata shown>"}. Nothing else.')


def signature(instruction: str):
    _, dspy = libraries.load()

    class CriticSignature(dspy.Signature):
        sources: str = dspy.InputField(desc="The chosen sources' descriptions, as JSON.")
        flags: str = dspy.InputField(desc="The flags to classify, each with the metadata of the records it names.")
        classes: str = dspy.InputField(desc="The allowed classes: code and meaning.")
        note: str = dspy.InputField(desc="'none', or a note about your previous answer.")
        classification: str = dspy.OutputField(desc=OUTPUT_DESCRIPTION)

    return CriticSignature.with_instructions(instruction)


def batches(critic_input: Mapping[str, Any], size: int) -> list[list[Mapping]]:
    flags = list(critic_input["flags_kind"])
    return [flags[i:i + size] for i in range(0, len(flags), size)]


def render_inputs(critic_input: Mapping[str, Any], batch: list[Mapping]) -> dict[str, str]:
    """The Critic's request inputs for one batch, built only from its access-layer input."""
    named = {r for f in batch for r in f["records"]}
    meta = {r["id"]: r for r in critic_input["record_metadata"] if r["id"] in named}
    flags = [{"id": str(f["id"]), "kind": f["kind"], "category": f["category"],
              "records": [meta[r] for r in f["records"] if r in meta]} for f in batch]
    return {"sources": json.dumps(critic_input["sources_meta"], sort_keys=True, ensure_ascii=False),
            "flags": json.dumps(flags, sort_keys=True, ensure_ascii=False),
            "classes": json.dumps(dict(CRITIC_CLASSES), sort_keys=True, ensure_ascii=False)}


def parse(text_: str) -> dict | None:
    body = text_.strip()
    fenced = _FENCE.match(body)
    if fenced:
        body = fenced.group(1)
    try:
        value = json.loads(body)
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def check(outputs: Mapping[str, str]) -> str | None:
    return None if parse(outputs["classification"]) is not None else "malformed"


@dataclass
class Classified:
    accepted: dict[int, tuple[str, str | None]] = field(default_factory=dict)
    refused: dict[str, str] = field(default_factory=dict)  # flag id (as given) -> code


def classify(data: Mapping, batch: list[Mapping]) -> Classified:
    """Code's check of each entry (see the module docstring)."""
    ids = {str(f["id"]): f["id"] for f in batch}
    out = Classified()
    for key, entry in data.items():
        if key not in ids:
            out.refused[str(key)[:40]] = "unknown_flag"
            continue
        if not isinstance(entry, dict) or set(entry) - {"class", "reason"} or "class" not in entry:
            out.refused[key] = "malformed_entry"
        elif not isinstance(entry["class"], str) or entry["class"] not in CRITIC_CLASSES:  # type first (finding 5)
            out.refused[key] = "class_not_allowed"
        elif entry.get("reason") is not None and not (isinstance(entry["reason"], str)
                                                       and 1 <= len(entry["reason"].strip()) <= CRITIC_REASON_MAX):
            out.refused[key] = "reason_not_allowed"
        else:
            reason = entry.get("reason")
            out.accepted[ids[key]] = (entry["class"], reason.strip() if isinstance(reason, str) else None)
    for key in ids:
        if key not in data:
            out.refused.setdefault(key, "not_answered")
    return out


def write_classes(engine: Engine, run_id: int, accepted: Mapping[int, tuple[str, str | None]]) -> int:
    """Writes each accepted class once, before the freeze (0001: classified once, only before the freeze)."""

    def body(conn: Connection, stage: str):
        if stage != "curation":
            raise Refused("write_classes", "stage_mismatch")
        n = 0
        for flag_id, (cls, reason) in sorted(accepted.items()):
            n += conn.execute(text("UPDATE flag SET critic_class = :c, critic_reason = :r, classified_at = now() "
                                   "WHERE id = :f AND run_id = :run AND critic_class IS NULL"),
                              dict(c=cls, r=reason, f=flag_id, run=run_id)).rowcount
        return n

    return write(engine, run_id, "critic", "write_classes", body)


@dataclass(frozen=True)
class CriticResult:
    classified: int
    refused: dict
    failures: list  # the failure code of each batch that failed
    stages: list


def run_critic(engine: Engine, run_id: int, *, ceiling=None, client_options: Mapping[str, Any] | None = None) -> CriticResult:
    """The Critic's stage(s). A failed batch leaves its flags unclassified; a spending refusal stops the
    remaining batches (the orchestrator then fails the run, PRD 8), and so does a recording or reservation
    failure (the orchestrator then stops the run and leaves it open for recovery; fix round, finding 3)."""
    from hypocurate.access.dispatch import bind_invocation
    from hypocurate.access.inputs import role_input
    from hypocurate.pipeline.agents.interface import call_agent
    from hypocurate.pipeline.agents.runstage import close_stage, open_stage
    from hypocurate.pipeline.agents.settings import recorded

    classified, refused, failures, stages = 0, {}, [], []
    data = None
    plan_batches = None
    while True:
        stage_id, invocation = open_stage(engine, run_id, "critic", "critic")
        stages.append(stage_id)
        s = recorded(engine, invocation)  # finding 2: the recorded version, never the current one
        current = role_input(bind_invocation(engine, invocation))
        if plan_batches is None:
            data, plan_batches = current, batches(current, s["limits"]["max_flags_per_call"])
        batch = plan_batches.pop(0) if plan_batches else []
        if not batch:
            close_stage(engine, run_id, stage_id, "skipped", {"reason": "no_flags"})
            break
        inputs = render_inputs(current, batch)
        result = call_agent(engine, invocation, signature(s["instruction"]), inputs, model=s["model"],
                            max_tokens=s["limits"]["max_tokens"], max_output_chars=s["limits"]["max_output_chars"],
                            ceiling=ceiling, lm_options=dict(s["settings"]), client_options=client_options,
                            check=check)
        if result.failure is not None:
            failures.append(result.failure)
            refused.update({str(f["id"]): result.failure for f in batch})
            close_stage(engine, run_id, stage_id, "failed", {"code": result.failure, "attempts": result.attempts,
                                                             "flags": [f["id"] for f in batch]}, input_=inputs)
            if (result.failure.startswith("spending_cap") or result.failure == "ceiling_reached"
                    or result.failure in RUN_STOPS):  # finding 3: no further batch after an accounting failure
                break
        else:
            got = classify(parse(result.outputs["classification"]), batch)
            classified += write_classes(engine, run_id, got.accepted)
            refused.update(got.refused)
            close_stage(engine, run_id, stage_id, "done", {
                "classified": {str(k): {"class": c, "reason": r} for k, (c, r) in sorted(got.accepted.items())},
                "refused": got.refused, "attempts": result.attempts}, input_=inputs)
        if not plan_batches:
            break
    return CriticResult(classified, refused, failures, stages)
