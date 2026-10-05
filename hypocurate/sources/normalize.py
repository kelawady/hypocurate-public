"""Unit and alloy-name normalizers shared by the adapters (PRD Sections 6.1 and 10).

Each function converts and reports. It never rescales, rounds away or corrects a value
silently: anything it cannot convert comes back as a `not_convertible` (or
`not_reported`) `Value` with the reason, and the adapter keeps the text as reported.
Physical plausibility (for example a negative grain size) is not judged here: that is
the job of the code checks under the locked plan (step 6).
"""
from __future__ import annotations

import math
import re

from hypocurate.sources.record import Value

# The 118 element symbols, to catch a formula that parses but names no element.
ELEMENTS = frozenset("""
H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge
As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm
Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U
Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og
""".split())

_FORMULA = re.compile(r"(?:\s*[A-Z][a-z]?\s*(?:\d+(?:\.\d*)?|\.\d+)?)+\s*")
_TERM = re.compile(r"([A-Z][a-z]?)\s*(\d+(?:\.\d*)?|\.\d+)?")

# Sum of percentage columns accepted as 100 (floating-point representation only).
PERCENT_SUM_TOLERANCE = 1e-6


def number(text: str, unit: str | None, blank_reason: str = "blank in the source") -> Value:
    """A number as reported, in the unit the source states. Blank → not reported;
    anything that is not a finite decimal number → not convertible, with the reason."""
    t = text.strip()
    if t == "":
        return Value(None, unit, "not_reported", blank_reason)
    try:
        x = float(t)
    except ValueError:
        return Value(None, unit, "not_convertible", f"not a number: {text!r}")
    if not math.isfinite(x):
        return Value(None, unit, "not_convertible", f"not a finite number: {text!r}")
    return Value(x, unit, "converted")


def formula_to_atomic_percent(formula: str) -> tuple[dict[str, float] | None, str | None]:
    """A formula string ("Al0.25 Co1 Fe1 Ni1", "CoCrFeMnNi") → atomic percent per element,
    full precision. A missing amount means 1. Returns (composition, None) or (None, reason)."""
    if formula.strip() == "":
        return None, "blank in the source"
    if not _FORMULA.fullmatch(formula):
        return None, f"formula does not parse: {formula!r}"
    amounts: dict[str, float] = {}
    for symbol, amount in _TERM.findall(formula):
        if symbol not in ELEMENTS:
            return None, f"unknown element symbol {symbol!r} in {formula!r}"
        a = float(amount) if amount else 1.0
        if not math.isfinite(a):
            return None, f"amount {amount!r} of {symbol} is too large to represent in {formula!r}"
        if a <= 0:
            if any(c in "123456789" for c in amount):
                return None, f"amount {amount!r} of {symbol} is too small to represent in {formula!r}"
            return None, f"amount {amount!r} of {symbol} is not positive in {formula!r}"
        amounts[symbol] = amounts.get(symbol, 0.0) + a
    # Numerically safe (step 4 review, finding 5): scale by the largest amount first, so
    # neither the sum nor 100 * a overflows; refuse a ratio too extreme to represent.
    largest = max(amounts.values())
    if not math.isfinite(largest):
        return None, f"amounts in {formula!r} are too large to represent"
    scaled = {e: a / largest for e, a in amounts.items()}
    if any(s == 0.0 for s in scaled.values()):
        return None, f"the ratio of amounts in {formula!r} is too extreme to represent"
    total = math.fsum(scaled.values())
    composition = {e: 100.0 * s / total for e, s in scaled.items()}
    if not all(math.isfinite(v) and v > 0 for v in composition.values()):
        return None, f"the composition of {formula!r} is not a finite positive number for every element"
    return composition, None


def percent_columns_to_atomic_percent(columns: dict[str, float | None]
                                      ) -> tuple[dict[str, float] | None, str | None]:
    """Columns of atomic percentages, one per element → atomic percent per element.
    Elements at 0 are absent from the alloy. A blank column, a negative value, a value
    above 100 or a sum other than 100 is reported, never rescaled."""
    for symbol in columns:
        if symbol not in ELEMENTS:
            return None, f"unknown element symbol {symbol!r}"
    blank = [e for e, v in columns.items() if v is None]
    if blank:
        return None, f"blank percentage for {', '.join(blank)}"
    infinite = [e for e, v in columns.items() if not math.isfinite(v)]
    if infinite:
        return None, f"percentage not a finite number for {', '.join(infinite)}"
    negative = [e for e, v in columns.items() if v < 0]
    if negative:
        return None, f"negative percentage for {', '.join(negative)}"
    # Re-check item 5: finite but huge values overflowed the sum and aborted the file.
    # A percentage above 100 is refused before summing; the overflow is caught as well.
    above = [e for e, v in columns.items() if v > 100.0 + PERCENT_SUM_TOLERANCE]
    if above:
        return None, f"percentage above 100 for {', '.join(above)}"
    try:
        total = math.fsum(columns.values())
    except OverflowError:
        return None, "the percentages are too large to sum"
    if not math.isfinite(total) or abs(total - 100.0) > PERCENT_SUM_TOLERANCE:
        return None, f"percentages sum to {total:g}, not 100"
    return {e: float(v) for e, v in columns.items() if v > 0}, None


def alloy_label(composition: dict[str, float]) -> str:
    """An alloy name **for display only**: elements in alphabetical order, each with its
    atomic percent rounded to 0.1 (the reference script's naming,
    `docs/reference/worked_example.py`).

    Equal labels do not mean the same alloy: Fe50.01Ni49.99 and Fe50.04Ni49.96 both read
    `Fe50Ni50` (step 4 review, finding 2). The record carries the full-precision
    composition; when two compositions count as the same alloy is a plan and
    domain-profile setting, defined in step 6 with a tolerance the owner approves."""
    return "".join(f"{e}{round(v, 1):g}" for e, v in sorted(composition.items()))


# The same-alloy rule (register entry 'same_alloy_rule', owner 2026-10-05): each element's
# atomic percent rounded to this many decimals; two compositions are the same alloy when
# their rounded compositions are identical. Used by the gap report's condition summaries
# (step 5); the plan setting that applies it to analysis comes in step 6.
SAME_ALLOY_DECIMALS = 1


def same_alloy_key(composition: dict[str, float]) -> str:
    """The same-alloy rule's key for a full-precision composition: elements in
    alphabetical order, each with its rounded atomic percent. Equal keys mean the same
    alloy under the rule; unlike `alloy_label`, the key is the rule itself."""
    return " ".join(f"{e} {round(v, SAME_ALLOY_DECIMALS):.{SAME_ALLOY_DECIMALS}f}"
                    for e, v in sorted(composition.items()))


_DOI_WRAPPER = re.compile(r"(?:https?://(?:dx\.)?doi\.org/|doi:)\s*", re.IGNORECASE)
_ASCII_UPPER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def doi_group_key(doi: str) -> str | None:
    """The grouping key of a paper from its DOI as reported (step 4 review, finding 1).

    Conservative normalization, so that formatting differences do not split one paper:
    surrounding whitespace is trimmed; one `https://doi.org/`, `http://dx.doi.org/` or
    `doi:` wrapper is removed (case-insensitive); ASCII letters A–Z are case-folded, as DOI
    equivalence prescribes. Nothing else changes (no Unicode normalization). The DOI as
    reported is kept unchanged in the record. Returns None if nothing is left."""
    key = doi.strip()
    match = _DOI_WRAPPER.match(key)
    if match:
        key = key[match.end():]
    key = key.strip().translate(_ASCII_UPPER)
    return f"doi:{key}" if key else None
