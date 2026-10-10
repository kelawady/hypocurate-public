"""Checks of an agent's prose against the run record (step 8b; owner, Q8; register 'analyst_text_checks').

Owner, 2026-10-07 (after the live set): rounding and phrasing are done by code. The Analyst's facts carry every
number as its display string (`pipeline.display`) and a ready-made phrase for each p-value and for each set of
paper figures; the Analyst quotes numbers exactly as given and never rounds.

**Placeholders** (owner, 2026-10-07, after the live checks): the Analyst writes no digits; it refers to each
number, phrase and wording by its fact's name in braces, and code renders the finished text (`render`). Before
rendering: every name must be one of the facts given, no digit may appear outside a placeholder, and
{outcome_wording} (and {verdict_wording} when there is a verdict) must be used (`placeholder_problems`, counts
only). The rules below then run on the finished text.

**Number check** (written for reuse by the Commentator, step 12; PRD 5.9): every number in the text must be, as a
token, one of the numbers the facts give (their display strings, counts and the numbers in the given text such as
the claim), apart from a few numbers of the method's own wording (`FIXED_NUMBERS`: validity checks 1 and 2, the 95%
interval, the model's exponent -1/2). Thousands separators are ignored. It checks numerical consistency only: it
does not check what the text says about the numbers.

**Wording check** (CLAUDE.md, rule 13): the text must contain code's outcome wording verbatim (so it always says
"in the sources searched"), and code's verdict wording verbatim when there is a verdict; it must not contain any
phrase of `FORBIDDEN` or `ALWAYS_FORBIDDEN` (no causal language, never "confirms the claim", even with a verdict),
and with no verdict it must not state one (`NO_VERDICT_FORBIDDEN`); a sentence naming the effective number must not
call it "independent". (Owner, 2026-10-07: the two word-based rules on p-values and paper figures were removed. With
placeholders, a p-value and the paper figures exist only inside their phrase names, which no other name exposes
(tested); with a verdict, the pooled result's two phrases are required placeholders.)
"""
from __future__ import annotations

import re
from typing import Any, Iterable, Mapping

FIXED_NUMBERS = ("1", "2", "95", "95%", "0.5", "-0.5")
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


def wording_problems(text: str, decision: Mapping, facts: Mapping | None = None) -> list[str]:
    """The wording rules the text breaks (empty when none). `facts`: the Analyst's facts, for its phrases."""
    lower = " ".join(text.lower().split())
    problems = [f"forbidden: {p}" for p in FORBIDDEN if p in lower]
    problems += [f"forbidden: {' '.join(m.group(0).lower().split())}" for m in ALWAYS_FORBIDDEN.finditer(text)]
    outcome = (decision.get("outcome_wording") or "").lower()
    if not outcome or outcome not in lower:
        problems.append("outcome wording missing")
    verdict = (decision.get("verdict_wording") or "").lower()
    if decision.get("verdict"):
        if verdict not in lower:
            problems.append("verdict wording missing")
    elif NO_VERDICT_FORBIDDEN.search(text):
        problems.append("a verdict is stated where there is none")
    for sentence in filter(None, (x.strip() for x in _SENTENCE.split(text))):
        if _EFFECTIVE.search(sentence) and _INDEPENDENT.search(sentence):
            problems.append("the effective number described as independent")
    return problems


# --- Placeholders (owner, 2026-10-07): the Analyst writes {name}; code writes the numbers -----------------------

PLACEHOLDER = re.compile(r"\{([^{}\n]{1,80})\}")
REQUIRED = ("outcome_wording",)  # and 'verdict_wording' whenever the facts give one
# Owner, 2026-10-07: with a verdict, the pooled result's p-value phrase and paper-figures phrase must be used too.
REQUIRED_WITH_VERDICT = ("pooled_p_phrase", "pooled_figures_phrase")


def placeholder_problems(template: str, names: Mapping[str, str]) -> dict[str, int]:
    """Counts only, never text: names not among the facts, digits outside a placeholder, required placeholders
    missing."""
    used = PLACEHOLDER.findall(template)
    rest = PLACEHOLDER.sub(" ", template)
    required = list(REQUIRED) + (["verdict_wording"] if "verdict_wording" in names else [])
    phrases_required = [r for r in REQUIRED_WITH_VERDICT if "verdict_wording" in names and r in names]
    return {"unknown_names": sum(1 for u in used if u not in names),
            "digits_outside_placeholders": len(re.findall(r"\d", rest)),
            "required_missing": sum(1 for r in required if r not in used),
            "result_phrases_missing": sum(1 for r in phrases_required if r not in used)}


# Owner, 2026-10-10 (live run A on Render: "Because of the the estimate is positive, ..."): the names whose values are
# complete sentences built by code. Each must stand as a sentence of its own in the Analyst's text: after the start of
# the text, a sentence's end (. ! ?), the start of a line or a list marker, and followed by the end of the text, a line
# break, or a new sentence (a capital letter). The Analyst's instruction names exactly these.
SENTENCE_NAMES = ("model_sentence", "scope_source", "direction_sentence", "minimums_sentence", "calibration_summary",
                  "group_definition")
_LIST_MARKER = re.compile(r"(?:^|\n)[ \t]*[-*•][ \t]*$")


def sentence_reason(name: str) -> str:
    return "{" + name + "} is a whole sentence: place it as a sentence of its own"


def placement_problems(template: str, names: Mapping[str, str]) -> list[str]:
    """The whole-sentence names placed inside another sentence, each once, as reasons in code's words (never text).
    Judged on the finished text around each placeholder, so a sentence name next to another reads as it will be
    shown. Names not among the facts are left to `placeholder_problems`."""
    problems: list[str] = []
    for m in PLACEHOLDER.finditer(template):
        name = m.group(1)
        if name not in SENTENCE_NAMES or name not in names:
            continue
        before = render(template[:m.start()], names) if all(
            u in names for u in PLACEHOLDER.findall(template[:m.start()])) else template[:m.start()]
        after = render(template[m.end():], names) if all(
            u in names for u in PLACEHOLDER.findall(template[m.end():])) else template[m.end():]
        head = before.rstrip(" \t")
        starts = not head or head[-1] in ".!?\n" or bool(_LIST_MARKER.search(head))
        rest = after.lstrip(" \t")
        ends = (not after or after[0] in " \t\n") and (not rest or rest[0] == "\n" or rest[0].isupper())
        if not (starts and ends):
            reason = sentence_reason(name)
            if reason not in problems:
                problems.append(reason)
    return problems


def missing_required(template: str, names: Mapping[str, str]) -> tuple[list[str], list[str]]:
    """The required names the template does not use (our names only): the wordings, then the result phrases."""
    used = set(PLACEHOLDER.findall(template))
    required = list(REQUIRED) + (["verdict_wording"] if "verdict_wording" in names else [])
    phrases = [r for r in REQUIRED_WITH_VERDICT if "verdict_wording" in names and r in names]
    return [r for r in required if r not in used], [r for r in phrases if r not in used]


def render(template: str, names: Mapping[str, str]) -> str:
    """The finished text: each {name} replaced by its display string or ready-made phrase."""
    return PLACEHOLDER.sub(lambda m: names[m.group(1)], template)
