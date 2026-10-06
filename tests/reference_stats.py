"""The independent reference implementation of the statistics (test side only; step 7).

PRD 13.3, software correctness: the package's coefficient, uncertainty and p-value must match an
independent implementation within numerical tolerance. This one uses statsmodels (a test-only
dependency, not in the deployed image) with explicit dummy variables, as the reference scripts in
`docs/reference/` do: OLS of the outcome on k × d^-1/2 plus one intercept per alloy, statsmodels'
cluster-robust covariance grouped by paper (its default small-sample correction), and a one-sided
p-value against t with (groups - 1) degrees of freedom. It shares no code with
`hypocurate.pipeline.statistics` or `calibration`: the model's alloy rule (two or more distinct
grain sizes) and the sorting are reimplemented here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats


def frame(rows) -> pd.DataFrame:
    """rows: (alloy, group, grain size in µm, outcome). Only alloys with two or more distinct grain sizes."""
    f = pd.DataFrame(list(rows), columns=["alloy", "group", "d", "y"])
    sizes = f.groupby("alloy")["d"].nunique()
    f = f[f["alloy"].isin(sizes[sizes >= 2].index)].copy()
    f["x"] = f["d"] ** -0.5
    return f.reset_index(drop=True)


def fit(rows) -> dict:
    """k, its cluster-robust standard error and the one-sided p-value; counts."""
    f = frame(rows)
    n, alloys, groups = len(f), f["alloy"].nunique(), f["group"].nunique()
    out = {"n": n, "alloys": alloys, "groups": groups, "resid_df": n - alloys - 1}
    if alloys == 0:
        return {**out, "k": None, "se": None, "p": None}
    formula = "y ~ x + C(alloy)" if alloys > 1 else "y ~ x"
    if n - alloys - 1 < 1 or groups < 2:
        return {**out, "k": float(smf.ols(formula, f).fit().params["x"]), "se": None, "p": None}
    m = smf.ols(formula, f).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(f["group"])[0]})
    k, se = float(m.params["x"]), float(m.bse["x"])
    return {**out, "k": k, "se": se, "p": float(stats.t.sf(k / se, groups - 1))}


def henderson_iii(rows) -> dict:
    """Method III by statsmodels' OLS fits and an explicit projection (numpy pinv)."""
    f = frame(rows)
    reduced = smf.ols("y ~ x + C(alloy)", f).fit()
    full = smf.ols("y ~ x + C(alloy) + C(group)", f).fit()
    rss_r, rss_f = float(reduced.ssr), float(full.ssr)
    rank_r, rank_f = int(np.linalg.matrix_rank(reduced.model.exog)), int(np.linalg.matrix_rank(full.model.exog))
    x = reduced.model.exog
    projection = x @ np.linalg.pinv(x)
    z = pd.get_dummies(f["group"]).to_numpy(dtype=float)
    residual = z - projection @ z
    trace = float(np.trace(residual.T @ residual))
    n = len(f)
    scatter_sq = rss_f / (n - rank_f)
    return {"rss_reduced": rss_r, "rss_full": rss_f, "rank_reduced": rank_r, "rank_full": rank_f, "trace": trace,
            "scatter_squared": scatter_sq,
            "shift_squared_untruncated": (rss_r - rss_f - (rank_f - rank_r) * scatter_sq) / trace}


def significant_count(x, alloy, group, outcomes, alpha) -> int:
    """The locked test on each row of `outcomes`, one statsmodels fit per row (explicit dummies)."""
    alloy, group = np.asarray(alloy), np.asarray(group)
    dummies = pd.get_dummies(alloy).to_numpy(dtype=float)
    exog = np.column_stack([x, dummies])  # k first, then one intercept per alloy (no constant)
    g = len(set(group.tolist()))
    hits = 0
    for y in outcomes:
        m = sm.OLS(y, exog).fit(cov_type="cluster", cov_kwds={"groups": group})
        hits += stats.t.sf(m.params[0] / m.bse[0], g - 1) < alpha
    return int(hits)
