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
        if a <= 0:
            return None, f"amount {amount!r} of {symbol} is not positive in {formula!r}"
        amounts[symbol] = amounts.get(symbol, 0.0) + a
    total = sum(amounts.values())
    return {e: 100.0 * a / total for e, a in amounts.items()}, None


def percent_columns_to_atomic_percent(columns: dict[str, float | None]
                                      ) -> tuple[dict[str, float] | None, str | None]:
    """Columns of atomic percentages, one per element → atomic percent per element.
    Elements at 0 are absent from the alloy. A blank column, a negative value or a sum
    other than 100 is reported, never rescaled."""
    for symbol in columns:
        if symbol not in ELEMENTS:
            return None, f"unknown element symbol {symbol!r}"
    blank = [e for e, v in columns.items() if v is None]
    if blank:
        return None, f"blank percentage for {', '.join(blank)}"
    negative = [e for e, v in columns.items() if v < 0]
    if negative:
        return None, f"negative percentage for {', '.join(negative)}"
    total = sum(columns.values())
    if abs(total - 100.0) > PERCENT_SUM_TOLERANCE:
        return None, f"percentages sum to {total:g}, not 100"
    return {e: float(v) for e, v in columns.items() if v > 0}, None


def alloy_label(composition: dict[str, float]) -> str:
    """The canonical alloy name: elements in alphabetical order, each with its atomic
    percent rounded to 0.1 (the reference script's naming, `docs/reference/worked_example.py`).
    The full-precision composition is kept beside it in the record."""
    return "".join(f"{e}{round(v, 1):g}" for e, v in sorted(composition.items()))
