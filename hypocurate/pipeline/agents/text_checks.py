"""Checks of an agent's prose against the run record (step 8b; owner, Q8; register 'analyst_text_checks').

Owner, 2026-10-07 (after the live set): rounding and phrasing are done by code. The Analyst's facts carry every
number as its display string (`pipeline.display`) and a ready-made phrase for each p-value and for each set of
paper figures; the Analyst quotes numbers exactly as given and never rounds.

**Number check** (written for reuse by the Commentator, step 12; PRD 5.9): every number in the text must be, as a
token, one of the numbers the facts give (their display strings, counts and the numbers in the given text such as
the claim), apart from a few numbers of the method's own wording (`FIXED_NUMBERS`: validity checks 1 and 2, the 95%
interval, the model's exponent -1/2). Thousands separators are ignored. It checks numerical consistency only: it
does not check what the text says about the numbers.

**Wording check** (CLAUDE.md, rule 13): the text must contain code's outcome wording verbatim (so it always says
"in the sources searched"), and code's verdict wording verbatim when there is a verdict; it must not contain any
phrase of `FORBIDDEN` or `ALWAYS_FORBIDDEN` (no causal language, never "confirms the claim", even with a verdict),
and with no verdict it must not state one (`NO_VERDICT_FORBIDDEN`). Owner's rules of 2026-10-07: a p-value may
appear only inside its ready-made phrase; the paper figures (informative papers, effective number, largest share)
only inside theirs; and a sentence naming the effective number must not call it "independent".
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

FIXED_NUMBERS = ("1", "2", "95", "95%", "0.5", "-0.5")
PHRASE_KEYS = ("p_value_phrase", "paper_figures_phrase")
# The model's exponent, written in any of its usual forms, is removed before numbers are read.
_EXPONENT = re.compile(r"\^\s*\(?\s*[-−]\s*1\s*/\s*2\s*\)?|\^\s*[-−]?\s*0\.5|[-−]½|⁻¹ᐟ²|\^\{-1/2\}")
# A number token: scientific notation (2.5e-7), or a plain number with an optional percent sign.
_TOKEN = re.compile(r"(?<![\w.])[-−]?\d+(?:\.\d+)?[eE][-+−]?\d+(?!\w)(?!\.\d)|"
                    r"(?<![\w.])[-−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:\s*%)?(?![\w])")

FORBIDDEN = ("do not exist", "does not exist", "don't exist", "doesn't exist", "no data exist", "data are absent",
             "proves", "proven", "prove that", "proof that")
# Owner's additions (2026-10-07, before the live set): always forbidden, with or without a verdict.
ALWAYS_FORBIDDEN = re.compile(r"\bconfirms\s+the\s+(claim|hypothesis)\b|\bcauses\b|\bcaused\s+by\b|\bcausal\b",
                              re.IGNORECASE)
_P_VALUE = re.compile(r"\bp[- ]?values?\b|(?<![\w])p\s*[=<>≈≤≥]", re.IGNORECASE)
_FIGURE_WORDS = re.compile(r"\binformative\s+(papers?|groups?)\b|\beffective\s+number\b|\blargest\s+share\b",
                           re.IGNORECASE)
_EFFECTIVE = re.compile(r"\beffective\s+(number|papers)\b", re.IGNORECASE)
_INDEPENDENT = re.compile(r"\bindependent\b", re.IGNORECASE)
_SENTENCE = re.compile(r"(?<=[.!?])\s+|\n+")
NO_VERDICT_FORBIDDEN = re.compile(r"\b(is|was|are|were|be)\s+(not\s+)?supported\b|\bsupports?\s+the\s+(claim|hypothesis)\b|"
                                  r"\bverdict\s*(is|:)\s*(not\s+)?supported\b|\bconfirm(s|ed)?\s+the\s+(claim|hypothesis)\b",
                                  re.IGNORECASE)


def tokens(text: str) -> list[str]:
    """The number tokens of `text`, normalized: the model's exponent removed, the minus sign and thousands
    separators unified, no space before a percent sign."""
    body = _EXPONENT.sub(" ", text)
    return [re.sub(r"\s+%", "%", m.group(0)).replace("−", "-").replace(",", "") for m in _TOKEN.finditer(body)]


def fact_tokens(value: Any) -> set[str]:
    """Every number the facts give, as a token: integers as written, display strings and given text by their tokens."""
    out: set[str] = set()
    if isinstance(value, bool) or value is None:
        return out
    if isinstance(value, int):
        out.add(str(value))
    elif isinstance(value, float):
        out.add(repr(value))  # display strings are expected; a float is matched only as written
    elif isinstance(value, str):
        out.update(tokens(value))
    elif isinstance(value, Mapping):
        for v in value.values():
            out |= fact_tokens(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            out |= fact_tokens(v)
    return out


def unmatched_numbers(text: str, facts: Any) -> list[str]:
    """The number tokens of `text` that the facts do not give (empty when all are given)."""
    known = fact_tokens(facts) | set(FIXED_NUMBERS)
    return [t for t in tokens(text) if t not in known]


def phrases(facts: Any) -> list[str]:
    """The ready-made phrases of the facts (`PHRASE_KEYS`), longest first."""
    found: list[str] = []
    if isinstance(facts, Mapping):
        for k, v in facts.items():
            if k in PHRASE_KEYS and isinstance(v, str):
                found.append(v)
            else:
                found += phrases(v)
    elif isinstance(facts, (list, tuple)):
        for v in facts:
            found += phrases(v)
    return sorted(set(found), key=len, reverse=True)


def wording_problems(text: str, decision: Mapping, facts: Mapping | None = None) -> list[str]:
    """The wording rules the text breaks (empty when none). `facts`: the Analyst's facts, for its phrases."""
    lower = " ".join(text.lower().split())
    problems = [f"forbidden: {p}" for p in FORBIDDEN if p in lower]
    problems += [f"forbidden: {m.group(0).lower()}" for m in ALWAYS_FORBIDDEN.finditer(text)]
    outcome = (decision.get("outcome_wording") or "").lower()
    if not outcome or outcome not in lower:
        problems.append("outcome wording missing")
    verdict = (decision.get("verdict_wording") or "").lower()
    if decision.get("verdict"):
        if verdict not in lower:
            problems.append("verdict wording missing")
    elif NO_VERDICT_FORBIDDEN.search(text):
        problems.append("a verdict is stated where there is none")
    rest = text
    found = phrases(facts or {})
    for phrase in found:
        rest = rest.replace(phrase, " ")
    # A p-value's display string anywhere outside its phrase counts as a p-value outside it.
    p_tokens = {t for phrase in found if phrase.startswith("p ") for t in tokens(phrase)}
    for sentence in filter(None, (x.strip() for x in _SENTENCE.split(rest))):
        if _P_VALUE.search(sentence) or p_tokens & set(tokens(sentence)):
            problems.append("a p-value outside its ready-made phrase")
        if _FIGURE_WORDS.search(sentence) and tokens(sentence):
            problems.append("paper figures outside their ready-made phrase")
        if _EFFECTIVE.search(sentence) and _INDEPENDENT.search(sentence):
            problems.append("the effective number described as independent")
    return problems
