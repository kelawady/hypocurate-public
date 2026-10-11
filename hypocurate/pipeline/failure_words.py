"""A failed run explained in plain English (build step 10b; owner's request of 2026-10-11).

The page says first, in plain sentences, what happened, what was and was not done, and what the person can do next;
then the codes, as "Technical detail: …". Every sentence is fixed text chosen by the stored failure code (and its
detail code), with the facts it names read from the stored rows: whether a plan was locked, the sources searched, a
dataset frozen; the number of Planner attempts; the name in a cancellation. Where the Planner's stage stored a
specific reason for refusing an answer, it is shown too, in code's own words. Nothing a model wrote is shown here.
"""
from __future__ import annotations

import re
from typing import Mapping

from sqlalchemy import Connection, text

# One plain explanation per failure code (failure_reason "<code>: <reason>[ (<detail>)]"). {done}: what was done
# before the stop, from the stored rows. {attempts}, {each}: the Planner's attempts. {by}: the person who cancelled.
EXPLAIN = {
    "planner_failed": ("The run stopped before anything was tested. The Planner proposed a plan {attempts}, and {each} "
                       "code's checks refused it, so nothing was locked or searched. You can dispatch the question "
                       "again as a new run."),
    "planner_unreadable": ("The run stopped before anything was tested. The Planner answered {attempts}, but {each} "
                           "the answer was not in the form code can read, so nothing was locked or searched. You can "
                           "dispatch the question again as a new run."),
    "planner_unreachable": ("The run stopped before anything was tested: the model provider could not be reached "
                            "when the Planner was asked, so nothing was locked or searched. You can dispatch the "
                            "question again as a new run once the provider answers."),
    "planner_declined": ("The run stopped before anything was tested: the Planner's model declined to answer, so "
                         "nothing was locked or searched. You can reword the hypothesis and dispatch it again."),
    "planner_provider_refused": ("The run stopped before anything was tested: the model provider refused the "
                                 "Planner's request ({words}), so nothing was locked or searched. The provider's "
                                 "settings need checking before the question is dispatched again."),
    "domain_mismatch": ("The run stopped before anything was tested: the Planner judged that the claim belongs to "
                        "another domain, so nothing was locked or searched. Check the query's domain, then dispatch "
                        "it again as a new run."),
    "claim_not_one_plan": ("The run stopped before anything was tested: the claim covers more than one temperature "
                           "band, test type or alloy class, and one run tests one of each, so nothing was locked or "
                           "searched. Edit the query into one question per band, test type and alloy class, and "
                           "dispatch each."),
    "narrowing_sources_changed": ("The run stopped before anything was tested: the sources changed after the original "
                                  "question's narrowing decision counted them, so the narrower plan no longer "
                                  "describes them, and nothing was locked or searched. Dispatch the original question "
                                  "again as a new run."),
    "narrower_plan_missing": ("The run stopped before anything was tested: the original question's narrowing decision "
                              "holds no narrower plan, so nothing was locked or searched. Dispatch the original "
                              "question again as a new run."),
    "spending_refused": ("The run stopped because its next model request would have gone over {cap}; the request was "
                         "not sent and nothing more was paid for. {done} {next_step}"),
    "refused": ("The run stopped because code refused one of its steps ({words}). {done} You can dispatch the question "
                "again as a new run; if it stops the same way, the step needs looking at."),
    "interrupted": ("The run stopped because the worker was interrupted twice while the Planner was being asked, and "
                    "it is not asked a third time; nothing was locked or searched. You can dispatch the question "
                    "again as a new run."),
    "attempts_exhausted": ("The run stopped after the worker was interrupted and took it up again too many times. "
                           "{done} You can dispatch the question again as a new run."),
    "cancelled_queued": ("The run was cancelled by {by} before it started: nothing was asked, locked, searched or paid "
                         "for. You can dispatch the question again as a new run."),
    "cancelled_waiting": ("The run was cancelled by {by} while it waited for a person to confirm the question as "
                          "tested: the Planner had been asked, but nothing was locked or searched. You can dispatch "
                          "the question again as a new run."),
    "other": ("The run stopped: {reason}. {done} You can dispatch the question again as a new run."),
}
CAPS = {"spending_cap_run": "the run's spending cap", "spending_cap_month": "this month's spending cap",
        "ceiling_reached": "the ceiling set for this run"}
NEXT_STEP = {"spending_cap_run": "You can dispatch it again as a new run; its cap is the per-run cap.",
             "spending_cap_month": "Dispatch it again next month, or once the owner raises the monthly cap.",
             "ceiling_reached": "You can dispatch it again as a new run with a higher ceiling."}
UNREADABLE = ("malformed", "truncated", "empty", "over_long", "tool_call")
PROVIDER = ("model_auth", "provider_rejected", "cost_unknown")
SHORT = {"planner_failed": "the Planner's plan was refused", "planner_unreadable": "the Planner's answer was unreadable",
         "planner_unreachable": "the model provider could not be reached",
         "planner_declined": "the Planner's model declined to answer",
         "planner_provider_refused": "the model provider refused the request",
         "domain_mismatch": "the claim belongs to another domain",
         "claim_not_one_plan": "the claim covers more than one question",
         "narrowing_sources_changed": "the sources changed", "narrower_plan_missing": "no narrower plan",
         "spending_refused": "a spending cap was reached", "refused": "code refused a step",
         "interrupted": "interrupted twice at the Planner", "attempts_exhausted": "interrupted too many times",
         "cancelled_queued": "cancelled before it started", "cancelled_waiting": "cancelled while waiting",
         "other": "stopped"}


def parse(reason: str) -> tuple[str, str | None]:
    """The code and the detail code of a stored failure reason ("<code>: <words>[ (<detail>)]")."""
    code = reason.split(":", 1)[0].strip()
    detail = re.search(r"\(([a-z_]+)\)\s*$", reason)
    return code, detail.group(1) if detail else None


def _done(conn: Connection, run_id: int) -> str:
    """What was done before the stop, from the stored rows."""
    locked = conn.execute(text("SELECT EXISTS (SELECT 1 FROM plan WHERE run_id = :r)"), dict(r=run_id)).scalar()
    frozen = conn.execute(text("SELECT EXISTS (SELECT 1 FROM run_snapshot WHERE run_id = :r)"), dict(r=run_id)).scalar()
    searched = conn.execute(text("SELECT count(*) FROM run_source WHERE run_id = :r AND search_status = 'searched'"),
                            dict(r=run_id)).scalar()
    if frozen:
        return "The rules were locked and the dataset frozen, but no result was recorded."
    if locked and searched:
        return "The rules were locked and the sources searched, but no dataset was frozen and nothing was tested."
    if locked:
        return "The rules were locked, but no source was searched and nothing was tested."
    return "Nothing was locked or searched."


def _attempts(conn: Connection, run_id: int) -> tuple[list[str], list[str]]:
    out = conn.execute(text("SELECT output FROM stage_result WHERE run_id = :r AND stage = 'planner' "
                            "ORDER BY id DESC LIMIT 1"), dict(r=run_id)).scalar_one_or_none()
    out = out if isinstance(out, Mapping) else {}
    attempts = [a for a in out.get("attempts") or [] if isinstance(a, str)]
    reasons = [r for r in out.get("attempt_reasons") or [] if isinstance(r, str) and r]
    return attempts, reasons


def _times(n: int) -> tuple[str, str]:
    return {1: ("once", "the"), 2: ("twice", "both times")}.get(n, (f"{n} times", "each time"))


def explain(conn: Connection, run_id: int, reason: str | None) -> dict | None:
    """The plain explanation of a failed run: its sentences, the Planner's stored reasons in code's words (if any), a
    short form for lists, and the technical detail."""
    if not reason:
        return None
    from hypocurate.pipeline.agents.lm import FAILURES
    from hypocurate.pipeline.writes import CODES
    code, detail = parse(reason)
    key, values, reasons = code, {"done": _done(conn, run_id)}, []
    if code == "planner_failed":
        attempts, reasons = _attempts(conn, run_id)
        n = max(1, len([a for a in attempts if a != "ok"]))
        times, each = _times(n)
        each = "each time" if each == "the" else each
        values.update(attempts=times, each=each if n > 1 else "")
        if detail in UNREADABLE:
            key = "planner_unreadable"
        elif detail == "provider_unavailable":
            key = "planner_unreachable"
        elif detail == "refused":
            key = "planner_declined"
        elif detail in PROVIDER:
            key, values["words"] = "planner_provider_refused", FAILURES[detail][0]
    elif code == "spending_refused":
        values.update(cap=CAPS.get(detail, "a spending cap or ceiling"),
                      next_step=NEXT_STEP.get(detail, "You can dispatch it again as a new run."))
    elif code == "refused":
        words = CODES.get(detail, "a write was refused") if detail else "a write was refused"
        values["words"] = re.sub(r"\s*\(register '[^']*'\)", "", words)  # register keys belong to the detail
    elif code == "cancelled":
        m = re.match(r"cancelled: cancelled by (.+?) (before it started|while waiting.*)$", reason)
        key = "cancelled_waiting" if m and m.group(2).startswith("while") else "cancelled_queued"
        values["by"] = m.group(1) if m else "a person"
    elif code not in EXPLAIN:
        key, values["reason"] = "other", reason.split(":", 1)[-1].strip().rstrip(".")
    words = " ".join(EXPLAIN[key].format(**values).split())  # one space wherever a value was left empty
    return {"words": words, "short": f"failed: {SHORT[key]}", "reasons": reasons,
            "technical": "Technical detail: " + ", ".join(x for x in (code, detail) if x) + "."}
