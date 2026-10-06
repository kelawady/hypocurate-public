"""The two checks on a Curator proposal (owner, 2026-10-06, Q2; register 'curator_quote_checks').

1. **The quote occurs in the source's sealed documentation.** Runs of whitespace (spaces, tabs,
   line breaks) are collapsed to one space on both sides, and the quote is trimmed; nothing else is
   changed (no case folding, no punctuation or LaTeX normalization). Code finds the document and the
   line where the quote begins; the model's own claim about where it found the quote is not used.
   The database checks the same occurrence again when the proposal is stored (migration 0005).
2. **The quote contains a listed term for the proposed value** (`TERMS`, case-insensitive), a first
   filter against a quote unrelated to the value. A paraphrase without a listed term is refused,
   which leaves the field unassigned: the safe direction. For the test temperature (a number), the
   term is the number as written in the quote. A microstructure joined by '+' needs every part.

Neither check shows that the sentence supports the value: that is for the person who accepts or
rejects the proposal, with the quote shown beside it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

QUOTE_MIN_CHARS, QUOTE_MAX_CHARS = 30, 1500  # after collapsing whitespace; the database's bounds (0005)
_SPACE = re.compile(r"\s+")

# The listed terms per field and value (register 'curator_quote_checks'; changing it is a register change).
TERMS: Mapping[str, Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "test_type": MappingProxyType({"tension": ("tensile", "tension"), "compression": ("compressive", "compression")}),
    "phase_class": MappingProxyType({"FCC": ("FCC", "face-centred cubic", "face-centered cubic"),
                                     "BCC": ("BCC", "body-centred cubic", "body-centered cubic")}),
    "test_temperature_band": MappingProxyType({
        "room temperature": ("room temperature", "room-temperature", "ambient temperature"),
        "elevated": ("elevated temperature", "high temperature", "high-temperature"),
        "cryogenic": ("cryogenic", "liquid nitrogen", "77 K")}),
    "microstructure": MappingProxyType({token: (token,) for token in ("FCC", "BCC", "B2", "HCP", "L12", "Laves")}),
})


def collapse(text: str) -> str:
    return _SPACE.sub(" ", text).strip()


@dataclass(frozen=True)
class Located:
    document: str
    line: int  # 1-based, where the quote begins in the original document


def locate(quote: str, documents: Mapping[str, str]) -> Located | None:
    """Where the collapsed quote first occurs, searching documents in path order; None if nowhere."""
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
        at = "".join(collapsed).find(wanted)
        if at >= 0:
            return Located(path, original.count("\n", 0, origin[at]) + 1)
    return None


def term_for(field: str, value, quote: str) -> str | None:
    """The listed term the quote contains for this value, or None (see the module docstring)."""
    lowered = quote.lower()
    if field == "test_temperature":
        written = _number_text(value)
        return written if written is not None and re.search(rf"(?<![\d.]){re.escape(written)}(?![\d])", quote) else None
    if field == "microstructure" and isinstance(value, str):
        parts = value.split("+")
        terms = [next((t for t in TERMS["microstructure"].get(p, ()) if t.lower() in lowered), None) for p in parts]
        return terms[0] if parts and all(terms) else None  # every part checked; the first stored (it occurs)
    for term in TERMS.get(field, {}).get(value, ()):
        if term.lower() in lowered:
            return term
    return None


def _number_text(value) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return str(int(value)) if float(value).is_integer() else repr(float(value))
