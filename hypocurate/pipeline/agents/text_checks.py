"""Checks of an agent's prose against the run record (step 8b; owner, Q8; register 'analyst_text_checks').

**Number check** (written for reuse by the Commentator, step 12; PRD 5.9): every number in the text must
equal a number of the facts the agent was given, at the precision the text shows it:
- a plain number with d decimals matches a fact v when v rounded to d decimals equals it;
- a percentage "x%" matches when v x 100 (a share) or v itself, rounded to x's decimals, equals x;
- scientific notation ("1.3e-6", "1.3 x 10^-6", "1.3 × 10⁻⁶") matches when v at the same exponent,
  rounded to the mantissa's decimals, equals the mantissa;
- a few numbers that belong to the method's wording, not to any result, are always allowed
  (`FIXED_NUMBERS`: the model's exponent -1/2, the 95% interval, validity checks 1 and 2).
It checks numerical consistency only: it does not check what the text says about the numbers.

**Wording check** (CLAUDE.md, rule 13; register 'analyst_wording'): the text must contain code's outcome
wording verbatim (it always says "in the sources searched"), and code's verdict wording verbatim when
there is a verdict; it must not contain any phrase of `FORBIDDEN`, and with no verdict it must not state
one (`NO_VERDICT_FORBIDDEN`).
"""
from __future__ import annotations

import math
import re
from typing import Any, Iterable, Mapping

FIXED_NUMBERS = (1.0, 2.0, 95.0, 0.5, -0.5)
# The model's exponent, written in any of its usual forms, is removed before numbers are read.
_EXPONENT = re.compile(r"\^\s*\(?\s*[-−]\s*1\s*/\s*2\s*\)?|\^\s*[-−]?\s*0\.5|[-−]½|⁻¹ᐟ²|\^\{-1/2\}")
_SCI = re.compile(r"(?<![\w.])([-−]?\d+(?:\.\d+)?)\s*(?:[eE]\s*([-+−]?\d+)|[x×]\s*10\s*(?:\^\s*\(?\s*([-+−]?\d+)\s*\)?|"
                  r"([⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)))")
_NUMBER = re.compile(r"(?<![\w.])([-−]?\d{1,3}(?:,\d{3})+(?:\.\d+)?|[-−]?\d+(?:\.\d+)?)(\s*%)?(?![\w])")
_SUPER = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")

FORBIDDEN = ("do not exist", "does not exist", "don't exist", "doesn't exist", "no data exist", "data are absent",
             "proves", "proven", "prove that", "proof that")
NO_VERDICT_FORBIDDEN = re.compile(r"\b(is|was|are|were|be)\s+(not\s+)?supported\b|\bsupports?\s+the\s+(claim|hypothesis)\b|"
                                  r"\bverdict\s*(is|:)\s*(not\s+)?supported\b|\bconfirm(s|ed)?\s+the\s+(claim|hypothesis)\b",
                                  re.IGNORECASE)


def facts_numbers(value: Any) -> list[float]:
    """Every number in the facts (recursively; booleans are not numbers)."""
    out: list[float] = []
    if isinstance(value, bool) or value is None:
        return out
    if isinstance(value, (int, float)):
        if math.isfinite(value):
            out.append(float(value))
    elif isinstance(value, Mapping):
        for v in value.values():
            out.extend(facts_numbers(v))
    elif isinstance(value, (list, tuple)):
        for v in value:
            out.extend(facts_numbers(v))
    elif isinstance(value, str):
        out.extend(n for n, _ in _plain_numbers(value))
    return out


def _decimals(token: str) -> int:
    return len(token.split(".")[1]) if "." in token else 0


def _num(token: str) -> float:
    return float(token.replace("−", "-").replace(",", ""))


def _plain_numbers(text: str) -> list[tuple[float, str]]:
    return [(_num(m.group(1)), m.group(0)) for m in _NUMBER.finditer(text)]


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def _matches_plain(x: float, d: int, facts: Iterable[float]) -> bool:
    return any(_close(round(v, d), x) for v in facts)


def _matches_percent(x: float, d: int, facts: Iterable[float]) -> bool:
    return any(_close(round(v * 100, d), x) or _close(round(v, d), x) for v in facts)


def _matches_sci(mantissa: float, d: int, exponent: int, facts: Iterable[float]) -> bool:
    return any(v != 0 and _close(round(v / 10 ** exponent, d), mantissa) for v in facts)


def unmatched_numbers(text: str, facts: Any) -> list[str]:
    """The numbers in `text` that are not numbers of `facts` as shown (empty when all match)."""
    known = facts_numbers(facts) + list(FIXED_NUMBERS)
    body = _EXPONENT.sub(" ", text)
    bad = []
    for m in list(_SCI.finditer(body)):
        mantissa = m.group(1)
        exp = m.group(2) or m.group(3) or (m.group(4) or "").translate(_SUPER)
        if not _matches_sci(_num(mantissa), _decimals(mantissa), int(exp.replace("−", "-")), known):
            bad.append(m.group(0))
    body = _SCI.sub(" ", body)
    for m in _NUMBER.finditer(body):
        token, percent = m.group(1), m.group(2)
        x, d = _num(token), _decimals(token.replace(",", ""))
        ok = _matches_percent(x, d, known) if percent else _matches_plain(x, d, known)
        if not ok:
            bad.append(m.group(0).strip())
    return bad


def wording_problems(text: str, decision: Mapping) -> list[str]:
    """The wording rules the text breaks (empty when none)."""
    lower = " ".join(text.lower().split())
    problems = [f"forbidden: {p}" for p in FORBIDDEN if p in lower]
    outcome = (decision.get("outcome_wording") or "").lower()
    if not outcome or outcome not in lower:
        problems.append("outcome wording missing")
    verdict = (decision.get("verdict_wording") or "").lower()
    if decision.get("verdict"):
        if verdict not in lower:
            problems.append("verdict wording missing")
    elif NO_VERDICT_FORBIDDEN.search(text):
        problems.append("a verdict is stated where there is none")
    return problems
