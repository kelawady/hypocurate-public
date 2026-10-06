"""The agents' settings: one named place per role (PRD 9.5; register 'agent_models', 'agent_settings').

`MODELS` is the owner's choice for each role (2026-10-06, Q7). Each role's settings version (its
instruction, model, limits and role-specific settings) is stored as an `agent_setting` row, append-only:
`ensure_setting` returns the version whose stored values equal these, or adds the next version. A run
records the versions it uses at dispatch; a registration invocation names the Curator's.

The Curator's settings are here (step 8a); the other roles' instructions come with them in step 8b.
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

CURATOR_INSTRUCTION = (
    "You read the documentation of one scientific data source. For each field named in the targets, decide "
    "whether the documentation explicitly states one value of that field that holds for all of the source's "
    "measurements. If it does, give that value, using only the allowed values listed for the field (for the "
    "test temperature, a number in degrees Celsius), and copy the one sentence that states it, word for word "
    "as it appears in the documentation, including any markup. If the documentation does not state it "
    "explicitly, answer \"not stated\" for that field. Do not infer, estimate or generalize, and do not use "
    "anything you know from outside the documentation.")

SETTINGS = MappingProxyType({
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
