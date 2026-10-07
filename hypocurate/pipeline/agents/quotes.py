"""The checks on a Curator proposal (owner, 2026-10-06, Q2; changed after the step 8a review, owner
2026-10-07; register 'curator_quote_checks').

`check(field, value, quote, documents)` applies them in this order and returns the first refusal code:
1. **The value** is allowed for the field (`value_problem`): a vocabulary value, a microstructure of
   vocabulary tokens joined by '+', or for the test temperature a finite number of °C (never JSON
   null, never a boolean or a string).
2. **The quote's length**, after collapsing runs of whitespace: `QUOTE_MIN_CHARS` to `QUOTE_MAX_CHARS`.
3. **The quote occurs in the source's sealed documentation** (`locate`): runs of whitespace are
   collapsed to one space on both sides and the quote is trimmed; nothing else is changed (no case
   folding, no punctuation or LaTeX normalization). The occurrence must begin and end at a word
   boundary of the document (it does not start or stop inside a word). Code finds the document and
   the line; the model's own claim about where it found the quote is not used.
4. **The quote holds a listed term for the value** (`term_for`), as a whole word, after collapsing
   whitespace and setting aside `EXCLUDED_PHRASES` ("tensile" in "ultimate tensile strength" alone is
   not a test type). Terms are case-insensitive except `CASE_SENSITIVE_TERMS` (B2, L12). A
   microstructure joined by '+' needs every part. A test temperature is a complete signed number
   (sign and decimals included, so 25 never matches -25, 25.5 or 125; never part of a larger number
   such as "1,025" or "1 025"; never an end of a range such as "20 - 25", "20–25", "20 to 25" or
   "20 °C to 25 °C") equal to the value and followed by a Celsius unit in a form found in the frozen
   documents: "°C" (after spaces or LaTeX "~"), or LaTeX "\\SI{<number>}{\\degreeCelsius}".
5. **For a test condition** (test type, temperature band, test temperature) the quote also holds a
   testing word (`TESTING_WORDS`, whole words): a processing sentence such as "cold rolled at room
   temperature" is refused.

Safe refusals, recorded in the register: a statement under 30 characters, a temperature given in
kelvin or in a Celsius form not found in the documents (such as "$^\\circ$C"), a range such as
"20-25 °C", and LaTeX forms of a term (such as "L1$_2$"). Each leaves the field unassigned.

The database applies the same checks when a passed proposal is stored (migration 0005, with its own
copy of the lists, tested equal to these). None of them shows that the sentence supports the value:
that is for the person who accepts or rejects the proposal, with the quote shown beside it.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping

from hypocurate.access.vocabulary import CURATION_TARGETS, MICROSTRUCTURE_TOKENS

QUOTE_MIN_CHARS, QUOTE_MAX_CHARS = 30, 600  # after collapsing whitespace; the database's bounds (0005)
_SPACE = re.compile(r"\s+")
WORD_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_")  # ASCII, as the database
_W = "A-Za-z0-9_"


def _spellings(first: str) -> tuple[str, ...]:
    """'face' -> face-centred cubic, face centered cubic, face-centered-cubic, ... (with or without hyphens)."""
    return tuple(f"{first}{a}cent{b}{c}cubic" for a in ("-", " ") for b in ("red", "ered") for c in (" ", "-"))


# The listed terms per field and value (register 'curator_quote_checks'; changing it is a register change).
TERMS: Mapping[str, Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "test_type": MappingProxyType({"tension": ("tensile", "tension"), "compression": ("compressive", "compression")}),
    "phase_class": MappingProxyType({"FCC": ("FCC",) + _spellings("face"), "BCC": ("BCC",) + _spellings("body")}),
    "test_temperature_band": MappingProxyType({
        "room temperature": ("room temperature", "room-temperature", "ambient temperature"),
        "elevated": ("elevated temperature", "high temperature", "high-temperature"),
        "cryogenic": ("cryogenic", "liquid nitrogen", "liquid helium", "77 K")}),
    "microstructure": MappingProxyType({token: (token,) for token in ("FCC", "BCC", "B2", "HCP", "L12", "Laves")}),
})
CASE_SENSITIVE_TERMS = frozenset({"B2", "L12"})
EXCLUDED_PHRASES = ("ultimate tensile strength", "ultimate tensile strengths")
# Owner, 2026-10-07: "deformed" and "strained" removed after the re-check (they often describe processing).
TESTING_WORDS = ("test", "tests", "tested", "testing", "loaded", "loading", "strain rate")
TESTING_FIELDS = frozenset({"test_type", "test_temperature_band", "test_temperature"})
TEMPERATURE_RANGE = (-273.15, 3000.0)  # °C, the value check of a test temperature

_SIGNS = "\\-+\u2212\u2013"  # hyphen-minus (escaped for a character class), plus, minus sign, en dash
_DASHES = "\\-\u2212\u2013"
# A number: no leading zero before another digit, so no part of "1 025" or "1,025" is read as 25.
_NUMBER = rf"[{_SIGNS}]?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?"
# Not the tail of a larger number: not after "<digit>," (owner, 2026-10-07, after the re-check).
_NOT_AFTER = r"(?<![0-9],)"
# Not the end of a range: the text before the number (or before "\SI") does not end in a number, with
# or without its unit, then a dash or "to" ("20 - 25", "20–25", "20 to 25", "20 °C to 25 °C").
_RANGE_LEFT = re.compile(rf"[0-9](?:[ ~]*\u00b0C|\}}\{{\\degreeCelsius\}})? ?(?:[Tt]o|[{_DASHES}]+) ?$")
# Not the start of a range: the unit is not followed by a dash or "to" and another number.
_NOT_BEFORE = rf"(?! ?(?:[{_DASHES}]|[Tt]o ) ?[{_SIGNS}]?(?:[0-9]|\\SI))"
_PLAIN = re.compile(rf"(?<![{_W}.{_SIGNS}]){_NOT_AFTER}({_NUMBER})(?![.,]?[0-9])[ ~]*\u00b0C{_NOT_BEFORE}")
_LATEX = re.compile(rf"{_NOT_AFTER}\\SI\{{({_NUMBER})\}}\{{\\degreeCelsius\}}{_NOT_BEFORE}")


def collapse(text: str) -> str:
    return _SPACE.sub(" ", text).strip()


@dataclass(frozen=True)
class Located:
    document: str
    line: int  # 1-based, where the quote begins in the original document


@dataclass(frozen=True)
class Checked:
    code: str | None              # None: passed
    located: Located | None = None
    term: str | None = None


def _bounded(text: str, start: int, end: int) -> bool:
    inside_at_start = start > 0 and text[start - 1] in WORD_CHARS and text[start] in WORD_CHARS
    inside_at_end = end < len(text) and text[end - 1] in WORD_CHARS and text[end] in WORD_CHARS
    return not inside_at_start and not inside_at_end


def locate(quote: str, documents: Mapping[str, str]) -> Located | None:
    """Where the collapsed quote first occurs at word boundaries, searching documents in path order;
    None if nowhere."""
    wanted = collapse(quote)
    if not wanted:
        return None
    for path in sorted(documents):
        original = documents[path]
        collapsed, origin = [], []  # collapsed text, and for each of its characters the original index
        in_space = False
        for i, ch in enumerate(original):
            if ch.isspace():
                if not in_space and collapsed:
                    collapsed.append(" ")
                    origin.append(i)
                in_space = True
            else:
                collapsed.append(ch)
                origin.append(i)
                in_space = False
        text = "".join(collapsed)
        at = text.find(wanted)
        while at >= 0:
            if _bounded(text, at, at + len(wanted)):
                return Located(path, original.count("\n", 0, origin[at]) + 1)
            at = text.find(wanted, at + 1)
    return None


def _prepared(quote: str) -> str:
    text = collapse(quote)
    for phrase in EXCLUDED_PHRASES:
        text = re.sub(rf"(?<![{_W}]){re.escape(phrase)}(?![{_W}])", " ", text, flags=re.IGNORECASE)
    return text


def _occurs(term: str, text: str) -> bool:
    flags = 0 if term in CASE_SENSITIVE_TERMS else re.IGNORECASE
    return re.search(rf"(?<![{_W}]){re.escape(term)}(?![{_W}])", text, flags) is not None


def _as_decimal(written: str) -> Decimal:
    return Decimal(written.translate(str.maketrans({"\u2212": "-", "\u2013": "-"})))


def term_for(field: str, value, quote: str) -> str | None:
    """The listed term the quote holds for this value, or None (see the module docstring)."""
    text = _prepared(quote)
    if field == "test_temperature":
        if value_problem(field, value):
            return None
        wanted = Decimal(str(value))
        for match in sorted([*_PLAIN.finditer(text), *_LATEX.finditer(text)], key=lambda m: m.start()):
            if _RANGE_LEFT.search(text, 0, match.start()):
                continue
            if _as_decimal(match.group(1)) == wanted:
                return match.group(1)
        return None
    if field == "microstructure" and isinstance(value, str):
        parts = value.split("+")
        terms = [next((t for t in TERMS["microstructure"].get(p, ()) if _occurs(t, text)), None) for p in parts]
        return terms[0] if parts and all(terms) else None  # every part checked; the first stored (it occurs)
    for term in TERMS.get(field, {}).get(value, ()) if isinstance(value, str) else ():
        if _occurs(term, text):
            return term
    return None


def testing_word(quote: str) -> str | None:
    text = collapse(quote)
    return next((w for w in TESTING_WORDS if _occurs(w, text)), None)


def value_problem(field: str, value: Any) -> str | None:
    if field == "test_temperature":
        ok = (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
              and TEMPERATURE_RANGE[0] <= value <= TEMPERATURE_RANGE[1])
        return None if ok else "value_not_allowed"
    if field == "microstructure":
        ok = isinstance(value, str) and value != "" and all(t in MICROSTRUCTURE_TOKENS for t in value.split("+"))
        return None if ok else "value_not_allowed"
    target = CURATION_TARGETS.get(field)
    ok = target is not None and isinstance(value, str) and value in target["vocabulary"]
    return None if ok else "value_not_allowed"


def check(field: str, value: Any, quote: str, documents: Mapping[str, str]) -> Checked:
    """Every check, in order (see the module docstring)."""
    code = value_problem(field, value)
    if code:
        return Checked(code)
    collapsed = collapse(quote) if isinstance(quote, str) else ""
    if len(collapsed) < QUOTE_MIN_CHARS:
        return Checked("quote_too_short")
    if len(collapsed) > QUOTE_MAX_CHARS:
        return Checked("quote_too_long")
    located = locate(quote, documents)
    if located is None:
        return Checked("quote_not_found")
    term = term_for(field, value, quote)
    if term is None:
        return Checked("term_missing", located)
    if field in TESTING_FIELDS and testing_word(quote) is None:
        return Checked("testing_word_missing", located, term)
    return Checked(None, located, term)
