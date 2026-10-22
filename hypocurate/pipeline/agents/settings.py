"""The agents' settings: one named place per role (PRD 9.5; register 'agent_models', 'agent_settings').

`MODELS` is the owner's choice for each role (2026-10-06, Q7). Each role's settings version (its
instruction, model, limits and role-specific settings) is stored as an `agent_setting` row, append-only:
`ensure_setting` returns the version whose stored values equal these, or adds the next version. A run
records the versions it uses at dispatch; a registration invocation names the Curator's.

The Curator's settings are here (step 8a); the Planner's, the Critic's and the Analyst's from step 8b (drafts
for the owner's review). `RUN_ROLES`: the roles a run records at dispatch (the Curator never runs in a run).
"""
from __future__ import annotations

import json
from types import MappingProxyType
from typing import Any, Mapping

from sqlalchemy import Engine, text

from hypocurate.db.retry import run_transaction
from hypocurate.pipeline.agents.text_checks import SENTENCE_NAMES

MODELS = MappingProxyType({
    "planner": "claude-opus-5-5",
    "curator": "claude-sonnet-5-5",
    "critic": "claude-haiku-4-5",
    "analyst": "claude-opus-5-5",
    # Sprint 2 pilot (owner, 2026-10-22, register 'pilot_extractor_models'): Sonnet for the first pass; Opus as a
    # second method on the annotated papers is a later setting, added only after S0 scoring works.
    "extractor": "claude-sonnet-5-5",
})

RUN_ROLES = ("planner", "critic", "analyst")

CURATOR_INSTRUCTION = (
    "You read the documentation of one scientific data source. For each field named in the targets, decide "
    "whether the documentation explicitly states one value of that field that holds for all of the source's "
    "measurements. If it does, give that value, using only the allowed values listed for the field (for the "
    "test temperature, a number in degrees Celsius), and copy the one sentence that states it, word for word "
    "as it appears in the documentation, including any markup. If the documentation does not state it "
    "explicitly, answer \"not stated\" for that field. Do not infer, estimate or generalize, and do not use "
    "anything you know from outside the documentation.")

# Step 8b drafts (Claude Code, 2026-10-07; for the owner's review before the live set, B3). Each role
# answers in text only; code checks every answer and decides everything (CLAUDE.md, rule 1).
PLANNER_INSTRUCTION = (
    "You read a scientific claim about grain-size strengthening in metal alloys and fill the parameters of the one "
    "supported test: yield strength = a baseline per alloy + k x (grain size)^-1/2. You see the claim, its domain, "
    "the chosen sources' descriptions and counts of their records by field status and category value; you never "
    "see measured values. Say whether the claim belongs to the domain. Give the claim's scope exactly as the claim "
    "states it, using only the allowed values: its alloy classes, phase classes, test types and temperature bands "
    "(room temperature, elevated or cryogenic; for elevated or cryogenic, the range in degrees Celsius that the "
    "claim names). Where the claim does not state a part of the scope, use the default given, and in 'stated' "
    "mark each part true if the claim states it and false if you used the default. Choose the outcome "
    "field from the allowed list and exclusion rules only from the menu. Give null for 'narrower': code decides "
    "any narrower scope from its own counts. Do not judge whether the claim is true.")
CRITIC_INSTRUCTION = (
    "You classify flags that code raised on records of a scientific data set. For each flag you are told its kind "
    "and category and the metadata of the records it names (source, alloy and composition, paper DOI, field "
    "statuses and conditions such as test type and phase); you are never told the numbers that were compared. "
    "Classify each flag with exactly one of the allowed classes and give a short reason based only on the "
    "metadata shown. Each flag stands alone: judge it only on the records it names, and never compare records "
    "across flags. If the metadata do not allow a judgment, use 'cannot_tell'. You do not decide which record "
    "is used, and you never choose between values.")
_SENTENCES = ", ".join("{" + n + "}" for n in SENTENCE_NAMES[:-1]) + " and {" + SENTENCE_NAMES[-1] + "}"
ANALYST_INSTRUCTION = (
    "You explain a result that code has already computed. Write no digits at all. Wherever you want a number, a "
    "p-value, the paper figures, the outcome or the verdict, write the name of the fact in braces exactly as it is "
    "listed in 'facts', for example {pooled_estimate} or {pooled_p_phrase}; code replaces each name with its value. "
    "Open by restating the claim in words, then give the outcome ({outcome_wording}) and, when it is listed, the "
    "verdict ({verdict_wording}), then the main cautions, in two or three sentences, before any detail; do not open "
    "with the query number. When there is a verdict, also use {pooled_p_phrase} and {pooled_figures_phrase}. "
    # Owner, 2026-10-10 (live run A): the code-built sentences stand alone; the list is the check's own.
    f"These ready-made facts are complete sentences: where they apply, place each whole as a sentence of its own, "
    f"never inside another sentence: {_SENTENCES}; use {{group_definition}} once. Give the minimums only through "
    "{minimums_sentence}, which states each with its status. Use the scope notes whole where they apply. "
    "Say 'groups', not 'papers'. Use only the "
    "facts and notes given, compute nothing, and do not draw conclusions beyond the facts and notes given. Never "
    "describe the effective number as a number of independent groups. Never write that data do not exist; say what "
    "was not found in the sources searched. If there is no verdict, do not suggest one. Do not use causal language, "
    "and do not say a result proves or confirms the claim, even when there is a verdict. Explain the checks and the "
    "minimums, and what would be needed for a test, in plain words, in at most a few short paragraphs.")

SETTINGS = MappingProxyType({
    "planner": MappingProxyType({
        "instruction": PLANNER_INSTRUCTION, "model": MODELS["planner"],
        "limits": MappingProxyType({"max_tokens": 8000, "max_output_chars": 6000}),
        "settings": MappingProxyType({"reasoning_effort": "medium"}),
    }),
    "critic": MappingProxyType({
        "instruction": CRITIC_INSTRUCTION, "model": MODELS["critic"],
        "limits": MappingProxyType({"max_tokens": 8000, "max_output_chars": 30000, "max_flags_per_call": 100}),
        "settings": MappingProxyType({"reasoning_effort": "low"}),
    }),
    "analyst": MappingProxyType({
        "instruction": ANALYST_INSTRUCTION, "model": MODELS["analyst"],
        "limits": MappingProxyType({"max_tokens": 8000, "max_output_chars": 6000}),
        "settings": MappingProxyType({"reasoning_effort": "medium"}),
    }),
    "curator": MappingProxyType({
        "instruction": CURATOR_INSTRUCTION,
        "model": MODELS["curator"],
        # max_tokens covers thinking and answer; max_output_chars bounds the answer text.
        "limits": MappingProxyType({"max_tokens": 8000, "max_output_chars": 20000}),
        "settings": MappingProxyType({"reasoning_effort": "medium"}),
    }),
})


# Sprint 2 pilot: the Extractor's settings (register 'pilot_extractor_settings'). Its instructions are the versioned
# prompt files, never text in code (Design D17); each setting names its step, prompt version and evidence specification.
EXTRACTOR_PROMPT_VERSION = "v3"  # v1 sent once, refused as malformed (no schema in the request); v2 used on 2026-10-23
# for the nine open-access papers; v3 (owner, 2026-10-23 evening): context from the methods in every record, every
# item verified
EXTRACTOR_STEPS = ("extract", "verify")
EXTRACTOR_LIMITS = MappingProxyType({
    # max_tokens covers thinking and answer; max_output_chars bounds the answer text.
    "extract": MappingProxyType({"max_tokens": 32000, "max_output_chars": 200000}),
    "verify": MappingProxyType({"max_tokens": 16000, "max_output_chars": 100000}),
})
EXTRACTOR_EFFORT = "medium"


def extractor_variant(step: str, spec: str, prompt_version: str = EXTRACTOR_PROMPT_VERSION) -> Mapping[str, Any]:
    """The Extractor's settings for one step and one evidence specification."""
    from pathlib import Path
    if step not in EXTRACTOR_STEPS:
        raise ValueError(f"unknown extractor step {step!r}")
    prompts = Path(__file__).resolve().parents[1] / "extraction" / "prompts" / prompt_version
    instruction = (prompts / f"{step}.md").read_text(encoding="utf-8").strip()
    if step == "extract" and prompt_version != "v1":  # from v2: the output schema is part of the instruction
        instruction += "\n\nOutput schema:\n" + (prompts / "output_schema.json").read_text(encoding="utf-8").strip()
    return MappingProxyType({
        "instruction": instruction, "model": MODELS["extractor"], "limits": EXTRACTOR_LIMITS[step],
        "settings": MappingProxyType({"reasoning_effort": EXTRACTOR_EFFORT, "step": step,
                                      "prompt_version": prompt_version, "evidence_spec": spec}),
    })


def _plain(value):
    return json.loads(json.dumps(value, default=dict))


def ensure_setting(engine: Engine, role: str, variant: Mapping[str, Any] | None = None) -> int:
    """The id of the stored settings version equal to `SETTINGS[role]` (or to `variant`, the Extractor's settings
    for one step and specification), adding the next version if none is."""
    s = SETTINGS[role] if variant is None else variant
    limits, extra = _plain(dict(s["limits"])), _plain(dict(s["settings"]))

    def transaction(conn):
        conn.execute(text("SELECT pg_advisory_xact_lock(hashtext('agent_setting:' || :r))"), dict(r=role))
        found = conn.execute(text(
            "SELECT id FROM agent_setting WHERE role = :r AND instruction = :i AND model = :m "
            "AND limits = CAST(:l AS jsonb) AND settings = CAST(:s AS jsonb) ORDER BY version DESC LIMIT 1"),
            dict(r=role, i=s["instruction"], m=s["model"], l=json.dumps(limits), s=json.dumps(extra))).scalar()
        if found:
            return found
        return conn.execute(text(
            "INSERT INTO agent_setting (role, version, instruction, model, limits, settings) VALUES (:r, "
            "(SELECT coalesce(max(version), 0) + 1 FROM agent_setting WHERE role = :r), :i, :m, CAST(:l AS jsonb), "
            "CAST(:s AS jsonb)) RETURNING id"),
            dict(r=role, i=s["instruction"], m=s["model"], l=json.dumps(limits), s=json.dumps(extra))).scalar_one()

    return run_transaction(engine, transaction)


def recorded(engine: Engine, invocation: int) -> Mapping[str, Any]:
    """The settings version recorded for the invocation (its instruction, model, limits and options), from which
    every role builds its request: never the settings current when the request is made (step 8b fix round,
    finding 2), so the audit record and the request cannot differ."""
    with engine.connect() as conn:
        row = conn.execute(text("SELECT a.instruction, a.model, a.limits, a.settings FROM agent_invocation i "
                                "JOIN agent_setting a ON a.id = i.agent_setting_id WHERE i.id = :i"),
                           dict(i=invocation)).one()
    return MappingProxyType({"instruction": row.instruction, "model": row.model,
                             "limits": MappingProxyType(dict(row.limits)),
                             "settings": MappingProxyType(dict(row.settings))})
