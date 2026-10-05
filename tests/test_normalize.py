"""Step 4 fix, review finding 5: composition parsing never returns a non-finite value.

Before the fix, large coefficients gave NaN or infinity marked as converted (labels such
as "FeinfNi0"). The calculation now scales by the largest amount first, and refuses
amounts or ratios it cannot represent."""
import math

import pytest

from hypocurate.sources.normalize import formula_to_atomic_percent, percent_columns_to_atomic_percent

HUGE = "9" * 308  # about 1e308: finite, but two of them overflow a plain sum


def test_a_coefficient_too_large_to_represent_is_refused():
    composition, reason = formula_to_atomic_percent(f"Fe{'9' * 400} Ni1")
    assert composition is None and "too large to represent" in reason


def test_large_finite_coefficients_are_normalized_without_overflow():
    composition, reason = formula_to_atomic_percent(f"Fe{HUGE} Ni{HUGE}")
    assert reason is None
    assert composition == {"Fe": pytest.approx(50.0), "Ni": pytest.approx(50.0)}
    composition, reason = formula_to_atomic_percent(f"Fe{HUGE} Ni{HUGE} Co{HUGE} Cr{HUGE}")
    assert reason is None and all(math.isfinite(v) for v in composition.values())


def test_a_ratio_too_extreme_to_represent_is_refused():
    composition, reason = formula_to_atomic_percent(f"Fe0.{'0' * 330}1 Ni{HUGE}")
    assert composition is None and "too small to represent" in reason
    composition, reason = formula_to_atomic_percent(f"Fe0.{'0' * 300}1 Ni{HUGE}")
    assert composition is None and "too extreme to represent" in reason


def test_every_converted_composition_is_finite_and_sums_to_100():
    for formula in ("Fe1 Ni1", "Al0.25 Co1 Fe1 Ni1", f"Fe{HUGE} Ni1", "Fe1 Ni0.000001"):
        composition, reason = formula_to_atomic_percent(formula)
        assert reason is None, formula
        assert all(math.isfinite(v) and v > 0 for v in composition.values())
        assert math.fsum(composition.values()) == pytest.approx(100.0)


def test_non_finite_percentages_are_refused():
    for bad in (math.inf, -math.inf, math.nan):
        composition, reason = percent_columns_to_atomic_percent({"Fe": 50.0, "Ni": bad})
        assert composition is None and "not a finite number for Ni" in reason
