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

from sqlalchemy import Engine, text

from hypocurate.db.retry import run_transaction

MODELS = MappingProxyType({
    "planner": "claude-opus-5-5",
    "curator": "claude-sonnet-5-5",
    "critic": "claude-haiku-4-5",
    "analyst": "claude-opus-5-5",
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
    "metadata shown. If the metadata do not allow a judgment, use 'cannot_tell'. You do not decide which record "
    "is used, and you never choose between values.")
ANALYST_INSTRUCTION = (
    "You explain a result that code has already computed. Write no digits at all. Wherever you want a number, a "
    "p-value, the paper figures, the outcome or the verdict, write the name of the fact in braces exactly as it is "
    "listed in 'facts', for example {pooled_estimate} or {pooled_p_phrase}; code replaces each name with its value. "
    "Open by restating the claim in words, then give the outcome ({outcome_wording}) and, when it is listed, the "
    "verdict ({verdict_wording}), then the main cautions, in two or three sentences, before any detail; do not open "
    "with the query number. When there is a verdict, also use {pooled_p_phrase} and {pooled_figures_phrase}. Use the "
    "ready-made sentences and notes whole where they apply: {model_sentence}, {scope_source} or the scope notes, "
    "{direction_note}, {calibration_summary}, and {group_definition} once. Say 'groups', not 'papers'. Use only the "
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


def _plain(value):
    return json.loads(json.dumps(value, default=dict))


def ensure_setting(engine: Engine, role: str) -> int:
    """The id of the stored settings version equal to `SETTINGS[role]`, adding the next version if none is."""
    s = SETTINGS[role]
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
