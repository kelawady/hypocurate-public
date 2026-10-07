"""How numbers are shown (step 8b; owner, 2026-10-07: rounding and phrasing are done by code, never by the Analyst;
register 'display_precision'). The one named place for display precision.

From the register: k, its standard error and t to 0.1, and a p-value to two significant figures
('reference_test_tolerance', 'reference_numbers'); counts exact. From the approved sensitivity numbers
('reference_numbers'): the effective number of papers to two decimals and the largest share as a percentage to one
decimal. Drafted by Claude Code for the owner's review: every other share or rate (calibration, detection, power,
their intervals) as a percentage to one decimal; temperatures, scatter and shift to at most one decimal; the
threshold α as given; any other number to three significant figures.

`display(facts)` turns every float of the Analyst's facts into its display string; integers (counts) stay as they
are. `p_phrase` and `figures_phrase` are the ready-made phrases the Analyst must use whole (the wording check
refuses a p-value or the paper figures anywhere else).
"""
from __future__ import annotations

import math
from typing import Any, Callable, Mapping

P_DESCRIPTION = "approximate, nominal, one-sided"


def one_decimal(v: float) -> str:
    return f"{v:.1f}"


def two_decimals(v: float) -> str:
    return f"{v:.2f}"


def significant(v: float, n: int) -> str:
    """`n` significant figures; scientific notation below 0.001 without exponent padding (2.5e-7)."""
    if v == 0:
        return "0"
    if abs(v) < 1e-3:
        mantissa, exponent = f"{v:.{n - 1}e}".split("e")
        return f"{mantissa}e{int(exponent)}"
    digits = max(n - 1 - math.floor(math.log10(abs(v))), 0)
    return f"{v:.{digits}f}"


def p_value(v: float) -> str:
    return significant(v, 2)


def percent(v: float) -> str:
    return f"{v * 100:.1f}%"


def at_most_one_decimal(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))


def as_given(v: float) -> str:
    return f"{v:g}"


def fallback(v: float) -> str:
    return significant(v, 3)


# Key -> how its value is shown. A list value (an interval) is shown element by element.
RULES: Mapping[str, Callable[[float], str]] = {
    "estimate": one_decimal, "std_error": one_decimal, "t": one_decimal,
    "p_value": p_value,
    "effective_papers": two_decimals,
    "largest_paper_share": percent, "share": percent, "ci_low": percent, "ci_high": percent,
    "detection": percent, "detection_ci": percent, "false_positive": percent, "false_positive_ci": percent,
    "estimated_power": percent, "estimated_power_estimated_noise": percent,
    "scatter": at_most_one_decimal, "shift": at_most_one_decimal, "min": at_most_one_decimal,
    "max": at_most_one_decimal,
    "alpha": as_given,
}


def _show(key: str | None, value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        if value.is_integer() and key not in RULES:
            return int(value)
        return RULES.get(key, fallback)(value)
    if isinstance(value, int):
        return value
    if isinstance(value, Mapping):
        return {k: _show(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [_show(key, v) for v in value]
    return value


def display(facts: Mapping) -> dict:
    """The facts with every float as its display string (integers unchanged)."""
    return _show(None, facts)


def p_phrase(p: float) -> str:
    """The ready-made phrase for a p-value: the value and its fixed description."""
    return f"p ≈ {p_value(p)} ({P_DESCRIPTION})"


def figures_phrase(informative: int, effective: float, largest_share: float, df: int) -> str:
    """The ready-made phrase for the four paper figures, always together (register 'p_value_reporting')."""
    return (f"{informative} informative papers, an effective number of papers of {two_decimals(effective)}, "
            f"a largest share of {percent(largest_share)} and {df} degrees of freedom")
