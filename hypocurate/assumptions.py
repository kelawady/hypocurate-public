"""The assumptions register (step 4b): one source file, `hypocurate/assumptions.json`.

One entry per assumption: what is assumed, its value, why, who decided it and when, the
expert review, the sensitivity analysis that covers it, whether code applies it yet, and
its earlier values. The /assumptions page is generated from it and nothing else.

Rules (CLAUDE.md, "How we work"): a new assumption or a changed default is entered here in
the same merge; code reads a default from one named place, and an entry that code applies
names that place in `applied.settings`. Each setting reference has one of these forms:

- `python:<module>:<name>[.<attribute or key>…]` — a module attribute, walked by attribute
  or mapping key;
- `python:<module>:<function>(<parameter>)` — the default of a function's parameter;
- `sql:<name>` — a constraint, function or message in the migrations;
- `file:<repository path>:<text>` — a fixed text in a repository file (for example the
  Dockerfile's process count).

An optional `equals` gives the value the code must hold. `resolve_setting` is used by the
tests (`tests/test_assumptions.py`), not by the page.
"""
from __future__ import annotations

import importlib
import inspect
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

PACKAGE = Path(__file__).resolve().parent
REGISTER_PATH = PACKAGE / "assumptions.json"
REPO_ROOT = PACKAGE.parent
MIGRATIONS = PACKAGE / "db" / "migrations" / "versions"

# Display order and labels.
CATEGORIES = {"scientific": "Scientific", "statistical": "Statistical",
              "data_handling": "Data handling", "operational": "Operational"}
REVIEW_STATUSES = {"not_reviewed": "Not reviewed", "accepted": "Reviewed and accepted", "disputed": "Disputed"}
STATES = ("in_force", "open")
BUILD_STEPS = range(5, 13)  # PRD 15, steps still to come

FIELDS = {"key", "name", "state", "statement", "value", "category", "affects", "reason", "evidence",
          "decided", "expert_review", "sensitivity", "applied", "history", "notes"}
OPEN_ONLY_FIELDS = {"pending"}
KEY = re.compile(r"[a-z][a-z0-9_]*")


class RegisterError(ValueError):
    """The register does not follow its schema. The message names the entry and the field."""


class SettingNotFound(LookupError):
    """A setting reference names nothing that exists in the code."""


def load_register(path: Path = REGISTER_PATH) -> list[dict]:
    """Read and validate the register. Raises RegisterError on any schema problem."""
    entries = json.loads(path.read_text(encoding="utf-8"))
    validate(entries)
    return entries


# --- Schema -------------------------------------------------------------------------

def _text(where: str, value: Any, *, optional: bool = False) -> None:
    if value is None and optional:
        return
    if not isinstance(value, str) or not value.strip():
        raise RegisterError(f"{where}: must be non-empty text")


def _date(where: str, value: Any) -> date:
    if not isinstance(value, str):
        raise RegisterError(f"{where}: must be a date YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        raise RegisterError(f"{where}: must be a date YYYY-MM-DD") from None
    if parsed.isoformat() != value:
        raise RegisterError(f"{where}: must be a date YYYY-MM-DD")
    return parsed


def _keys(where: str, obj: Any, required: set[str], optional: frozenset[str] = frozenset()) -> None:
    if not isinstance(obj, dict):
        raise RegisterError(f"{where}: must be an object")
    missing, extra = required - obj.keys(), obj.keys() - required - optional
    if missing:
        raise RegisterError(f"{where}: missing {sorted(missing)}")
    if extra:
        raise RegisterError(f"{where}: unknown {sorted(extra)}")


def validate(entries: Any) -> None:
    if not isinstance(entries, list) or not entries:
        raise RegisterError("the register must be a non-empty list")
    seen: set[str] = set()
    for i, e in enumerate(entries):
        where = f"entry {i}"
        if isinstance(e, dict) and isinstance(e.get("key"), str):
            where = f"entry {e['key']!r}"
        _validate_entry(where, e)
        if e["key"] in seen:
            raise RegisterError(f"{where}: duplicate key")
        seen.add(e["key"])


def _validate_entry(where: str, e: Any) -> None:
    is_open = isinstance(e, dict) and e.get("state") == "open"
    _keys(where, e, FIELDS | (OPEN_ONLY_FIELDS if is_open else set()))
    if not isinstance(e["key"], str) or not KEY.fullmatch(e["key"]):
        raise RegisterError(f"{where}.key: lower-case letters, digits and _ only")
    for f in ("name", "statement", "affects", "reason"):
        _text(f"{where}.{f}", e[f])
    if e["state"] not in STATES:
        raise RegisterError(f"{where}.state: one of {list(STATES)}")
    if e["category"] not in CATEGORIES:
        raise RegisterError(f"{where}.category: one of {list(CATEGORIES)}")
    if not isinstance(e["evidence"], list) or not e["evidence"]:
        raise RegisterError(f"{where}.evidence: a non-empty list")
    for j, ev in enumerate(e["evidence"]):
        _text(f"{where}.evidence[{j}]", ev)
    _text(f"{where}.sensitivity", e["sensitivity"], optional=True)
    if not isinstance(e["notes"], list):
        raise RegisterError(f"{where}.notes: a list")
    for j, note in enumerate(e["notes"]):
        _text(f"{where}.notes[{j}]", note)

    decided_on = None
    if is_open:
        # An open decision has no value in force and no decision yet; it says who decides, by when.
        if e["value"] is not None or e["decided"] is not None:
            raise RegisterError(f"{where}: an open decision has value null and decided null")
        _keys(f"{where}.pending", e["pending"], {"by", "before_step"})
        _text(f"{where}.pending.by", e["pending"]["by"])
        if e["pending"]["before_step"] not in BUILD_STEPS:
            raise RegisterError(f"{where}.pending.before_step: a build step from 5 to 12")
    else:
        _keys(f"{where}.value", e["value"], {"text", "unit"})
        _text(f"{where}.value.text", e["value"]["text"])
        _text(f"{where}.value.unit", e["value"]["unit"], optional=True)
        _keys(f"{where}.decided", e["decided"], {"by", "date"})
        _text(f"{where}.decided.by", e["decided"]["by"])
        decided_on = _date(f"{where}.decided.date", e["decided"]["date"])

    review = e["expert_review"]
    _keys(f"{where}.expert_review", review, {"status", "name", "date"})
    if review["status"] not in REVIEW_STATUSES:
        raise RegisterError(f"{where}.expert_review.status: one of {list(REVIEW_STATUSES)}")
    if review["status"] == "not_reviewed":
        if review["name"] is not None or review["date"] is not None:
            raise RegisterError(f"{where}.expert_review: not reviewed has no name or date")
    else:
        _text(f"{where}.expert_review.name", review["name"])
        _date(f"{where}.expert_review.date", review["date"])

    _validate_applied(f"{where}.applied", e["applied"])

    if not isinstance(e["history"], list):
        raise RegisterError(f"{where}.history: a list")
    previous_to = None
    for j, h in enumerate(e["history"]):
        hw = f"{where}.history[{j}]"
        _keys(hw, h, {"value", "from", "to", "note"})
        _text(f"{hw}.value", h["value"])
        _text(f"{hw}.note", h["note"], optional=True)
        start, end = _date(f"{hw}.from", h["from"]), _date(f"{hw}.to", h["to"])
        if start > end:
            raise RegisterError(f"{hw}: 'from' is after 'to'")
        if previous_to is not None and start < previous_to:
            raise RegisterError(f"{hw}: earlier values must be in date order")
        if decided_on is not None and end > decided_on:
            raise RegisterError(f"{hw}: ends after the current value was decided")
        previous_to = end


def _validate_applied(where: str, applied: Any) -> None:
    if not isinstance(applied, dict) or applied.get("status") not in ("yes", "not_yet"):
        raise RegisterError(f"{where}.status: 'yes' or 'not_yet'")
    if applied["status"] == "yes":
        _keys(where, applied, {"status", "settings", "note"})
        if not isinstance(applied["settings"], list) or not applied["settings"]:
            raise RegisterError(f"{where}.settings: applied in code needs at least one named setting")
        for j, s in enumerate(applied["settings"]):
            _keys(f"{where}.settings[{j}]", s, {"ref"}, frozenset({"equals"}))
            _text(f"{where}.settings[{j}].ref", s["ref"])
    else:
        _keys(where, applied, {"status", "step", "note"})
        if applied["step"] not in BUILD_STEPS:
            raise RegisterError(f"{where}.step: a build step from 5 to 12")
    _text(f"{where}.note", applied["note"], optional=True)


# --- Settings in code ----------------------------------------------------------------

_PYTHON = re.compile(r"python:([A-Za-z_][\w.]*):([A-Za-z_]\w*(?:\.\w+)*)(?:\((\w+)\))?")


def _plain(value: Any) -> Any:
    """A code value in the register's JSON terms: sets sorted, tuples as lists."""
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(v) for v in value)
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def resolve_setting(ref: str) -> Any:
    """The value a setting reference names in the code. Raises SettingNotFound if it names
    nothing. For `sql:` and `file:` references the value is the matched text."""
    if ref.startswith("python:"):
        m = _PYTHON.fullmatch(ref)
        if not m:
            raise SettingNotFound(f"{ref}: not a python:<module>:<name> reference")
        module_name, path, parameter = m.groups()
        try:
            obj: Any = importlib.import_module(module_name)
        except ImportError as error:
            raise SettingNotFound(f"{ref}: module not found ({error})") from None
        for part in path.split("."):
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                try:
                    obj = obj[part]
                except (KeyError, TypeError, IndexError):
                    raise SettingNotFound(f"{ref}: {part!r} not found") from None
        if parameter is None:
            return _plain(obj)
        try:
            param = inspect.signature(obj).parameters[parameter]
        except (KeyError, TypeError, ValueError):
            raise SettingNotFound(f"{ref}: no parameter {parameter!r}") from None
        if param.default is inspect.Parameter.empty:
            raise SettingNotFound(f"{ref}: parameter {parameter!r} has no default")
        return _plain(param.default)
    if ref.startswith("sql:"):
        name = ref[len("sql:"):]
        pattern = re.compile(rf"(?<![\w]){re.escape(name)}(?![\w])")
        for migration in sorted(MIGRATIONS.glob("*.py")):
            if pattern.search(migration.read_text(encoding="utf-8")):
                return name
        raise SettingNotFound(f"{ref}: not found in the migrations")
    if ref.startswith("file:"):
        relative, sep, needle = ref[len("file:"):].partition(":")
        target = (REPO_ROOT / relative).resolve()
        if not sep or not needle or not target.is_relative_to(REPO_ROOT) or not target.is_file():
            raise SettingNotFound(f"{ref}: not a file:<path>:<text> reference to a repository file")
        if needle not in target.read_text(encoding="utf-8"):
            raise SettingNotFound(f"{ref}: text not found")
        return needle
    raise SettingNotFound(f"{ref}: unknown kind of reference")


def check_settings(entry: dict) -> list[str]:
    """Problems with an applied entry's named settings: each must resolve, and each value
    given with `equals` must equal the code's. Empty when all is well."""
    problems = []
    for s in entry["applied"].get("settings", []):
        try:
            actual = resolve_setting(s["ref"])
        except SettingNotFound as error:
            problems.append(f"{entry['key']}: {error}")
            continue
        if "equals" in s and actual != s["equals"]:
            problems.append(f"{entry['key']}: {s['ref']} is {actual!r} in the code, the register says {s['equals']!r}")
    return problems


# --- The page ------------------------------------------------------------------------

def page_sections(entries: list[dict], *, not_reviewed_only: bool = False) -> list[tuple[str, list[dict]]]:
    """Sections for the page: open decisions first, then the entries in force by category."""
    shown = [e for e in entries if not not_reviewed_only or e["expert_review"]["status"] == "not_reviewed"]
    sections = [("Open decisions", [e for e in shown if e["state"] == "open"])]
    sections += [(label, [e for e in shown if e["state"] == "in_force" and e["category"] == c])
                 for c, label in CATEGORIES.items()]
    return [(label, group) for label, group in sections if group]


def summary_counts(entries: list[dict]) -> dict[str, int]:
    return {
        "total": len(entries),
        "open": sum(e["state"] == "open" for e in entries),
        "scientific_not_reviewed": sum(e["category"] == "scientific"
                                       and e["expert_review"]["status"] == "not_reviewed" for e in entries),
    }
