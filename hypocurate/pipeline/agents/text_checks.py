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

**Wording check** (CLAUDE.md, rule 13; register 'analyst_text_checks'): the text must contain code's outcome
wording verbatim (it always says "in the sources searched"), and code's verdict wording verbatim when
there is a verdict; it must not contain any phrase of `FORBIDDEN` or `ALWAYS_FORBIDDEN` (no causal language,
never "confirms the claim"), and with no verdict it must not state one (`NO_VERDICT_FORBIDDEN`). Owner's
additions (2026-10-07): a sentence giving a p-value must say "approximate"; a sentence naming the effective
number must not call it "independent"; if the text gives the informative-paper count, it must also give the
effective number, the largest share and the degrees of freedom of the same analysis.
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
# Owner's additions (2026-10-07, before the live set): always forbidden, with or without a verdict.
ALWAYS_FORBIDDEN = re.compile(r"\bconfirms\s+the\s+(claim|hypothesis)\b|\bcauses\b|\bcaused\s+by\b|\bcausal\b",
                              re.IGNORECASE)
_P_VALUE = re.compile(r"\bp[- ]?values?\b|(?<![\w])p\s*[=<>≈≤≥]", re.IGNORECASE)
_EFFECTIVE = re.compile(r"\beffective\s+(number|papers)\b", re.IGNORECASE)
_INDEPENDENT = re.compile(r"\bindependent\b", re.IGNORECASE)
_INFORMATIVE = re.compile(r"\binformative\b", re.IGNORECASE)
_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")
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


def _shown(value: float, text: str) -> bool:
    """Does `value` appear among the numbers of `text`, at the precision shown (plain or as a percentage)?"""
    body = _SCI.sub(" ", _EXPONENT.sub(" ", text))
    for m in _NUMBER.finditer(body):
        token, percent = m.group(1), m.group(2)
        x, d = _num(token), _decimals(token.replace(",", ""))
        if (_matches_percent if percent else _matches_plain)(x, d, [value]):
            return True
    return False


def _paper_figures(facts: Mapping | None) -> list[list[float]]:
    """Per analysis, the figures that go with the informative-paper count: effective number, largest share,
    degrees of freedom (those the facts hold)."""
    out = []
    for e in (facts or {}).get("analyses") or []:
        counts = e.get("counts") or {}
        figures = [v for v in (counts.get("effective_papers"), counts.get("largest_paper_share"), e.get("df"))
                   if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if figures:
            out.append(figures)
    return out


def wording_problems(text: str, decision: Mapping, facts: Mapping | None = None) -> list[str]:
    """The wording rules the text breaks (empty when none). `facts`: the Analyst's facts, for the rules on the
    effective number and the paper figures."""
    lower = " ".join(text.lower().split())
    problems = [f"forbidden: {p}" for p in FORBIDDEN if p in lower]
    problems += [f"forbidden: {m.group(0).lower()}" for m in ALWAYS_FORBIDDEN.finditer(text)]
    effective_values = [f[0] for f in _paper_figures(facts)] if facts else []
    for sentence in filter(None, (x.strip() for x in _SENTENCE.split(text))):
        if _P_VALUE.search(sentence) and "approximate" not in sentence.lower():
            problems.append("a p-value without 'approximate' in its sentence")
        names_effective = _EFFECTIVE.search(sentence) or any(_shown(v, sentence) for v in effective_values
                                                               if v not in (1.0, 2.0))
        if names_effective and _INDEPENDENT.search(sentence):
            problems.append("the effective number described as independent")
    if _INFORMATIVE.search(text):
        figures = _paper_figures(facts)
        if not any(all(_shown(v, text) for v in f) for f in figures):
            problems.append("the informative-paper count without the effective number, largest share and degrees "
                            "of freedom")
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
