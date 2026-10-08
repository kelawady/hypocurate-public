"""How numbers are shown (step 8b; owner, 2026-10-07: rounding and phrasing are done by code, never by the Analyst;
register 'display_precision'). The one named place for display precision.

From the register: k, its standard error and t to 0.1, and a p-value to two significant figures
('reference_test_tolerance', 'reference_numbers'); counts exact. From the approved sensitivity numbers
('reference_numbers'): the effective number of papers to two decimals and the largest share as a percentage to one
decimal. Drafted by Claude Code for the owner's review: every other share or rate (calibration, detection, power,
their intervals) as a percentage to one decimal; temperatures, scatter and shift to at most one decimal; the
threshold α as given; any other number to three significant figures.

Every number shown is formatted here, with its unit where it has one (fix round 1: the earlier `display(facts)`, which
gave numbers without units, is deleted). `p_phrase`, `figures_phrase` and `interval_phrase` are ready-made phrases; `coefficient`, `stress` and
`temperature` carry their units (owner, 2026-10-07); `nominal_level` gives the threshold as a percentage.
"""
from __future__ import annotations

import math

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


# Owner, 2026-10-07 (after reading a live explanation): units on every estimate, standard error, scatter, shift and
# temperature; one form for rates and the threshold (percentages); each simulation interval says what it is.
COEFFICIENT_UNIT = "MPa·µm^0.5"
INTERVAL_NOTE = "a 95% simulation interval covering simulation uncertainty only"


def coefficient(v: float) -> str:
    """An estimate or standard error of k, with its unit."""
    return f"{one_decimal(v)} {COEFFICIENT_UNIT}"


def stress(v: float) -> str:
    return f"{at_most_one_decimal(v)} MPa"


def temperature(v: float) -> str:
    return f"{at_most_one_decimal(v)} °C"


def nominal_level(alpha: float) -> str:
    """The threshold in the same form as the shares it is compared with."""
    return percent(alpha)


def interval_phrase(low: float, high: float) -> str:
    return f"{percent(low)} to {percent(high)}, {INTERVAL_NOTE}"


def p_phrase(p: float) -> str:
    """The ready-made phrase for a p-value: its fixed description and the value, with no brackets, so that it reads
    the same inside parentheses (fix round 1, owner's wording fix)."""
    return f"an {P_DESCRIPTION} p ≈ {p_value(p)}"


def figures_phrase(informative: int, effective: float, largest_share: float, df: int) -> str:
    """The ready-made phrase for the four paper figures, always together (register 'p_value_reporting')."""
    return (f"{informative} informative groups, an effective number of groups of {two_decimals(effective)}, "
            f"a largest share of {percent(largest_share)} and {df} degrees of freedom")
