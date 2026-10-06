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


def informative_groups(rows, relative_zero=1e-10) -> set:
    """Test-side: groups with a record whose transformed grain size differs from its alloy's average
    by more than relative_zero × the largest transformed grain size (alloys with two or more grain sizes)."""
    f = frame(rows)
    if f.empty:
        return set()
    contrast = (f["x"] - f.groupby("alloy")["x"].transform("mean")).abs()
    return set(f.loc[contrast > relative_zero * f["x"].abs().max(), "group"])


def fit_informative(rows, count: str = "informative") -> dict:
    """The owner's rule (2026-10-06, as corrected after the re-check), computed in 60-digit decimal
    arithmetic (Python's `decimal`). It independently checks the implementation's covariance; it does not
    remove every floating-point effect (its inputs, the transformed grain sizes, come from ordinary
    floating-point code, the informative-paper classification is the floating-point `informative_groups`,
    and the tail probability uses SciPy), and it does not validate the statistical method itself (the
    chosen correction and degrees of freedom). The computation:
    within-alloy centring, k = Σ x̃ỹ / Σ x̃², residuals e = ỹ - k x̃, the clustered variance summing
    **every** paper's score (no filtering), the factor G/(G-1) × (N-1)/(N-K) and a one-sided t test
    with G - 1 degrees of freedom, where G is the informative papers (`count="informative"`) or every
    paper (`count="all"`, the earlier definition). It shares no code with the package."""
    from decimal import Decimal, localcontext
    f = frame(rows)
    groups_inf = informative_groups(rows)
    with localcontext() as ctx:
        ctx.prec = 60
        x = [Decimal(v) for v in f["x"]]
        y = [Decimal(v) for v in f["y"]]
        alloys, groups = list(f["alloy"]), list(f["group"])
        mean_x, mean_y = {}, {}
        for a in set(alloys):
            idx = [i for i, b in enumerate(alloys) if b == a]
            mean_x[a] = sum(x[i] for i in idx) / len(idx)
            mean_y[a] = sum(y[i] for i in idx) / len(idx)
        xt = [x[i] - mean_x[alloys[i]] for i in range(len(x))]
        yt = [y[i] - mean_y[alloys[i]] for i in range(len(y))]
        sxx = sum(v * v for v in xt)
        k = sum(a * b for a, b in zip(xt, yt)) / sxx
        e = [yt[i] - k * xt[i] for i in range(len(x))]
        scores = {}
        for i, g in enumerate(groups):
            scores[g] = scores.get(g, Decimal(0)) + xt[i] * e[i]
        n, k_params = len(x), len(set(alloys)) + 1
        g_count = len(groups_inf) if count == "informative" else len(set(groups))
        factor = (Decimal(g_count) / (g_count - 1)) * (Decimal(n - 1) / (n - k_params))
        variance = sum(s * s for s in scores.values()) / (sxx * sxx) * factor
        se = float(variance.sqrt())
    return {"k": float(k), "se": se, "p": float(stats.t.sf(float(k) / se, g_count - 1)), "df": g_count - 1,
            "groups_informative": len(groups_inf), "groups": len(set(groups))}


def effective_papers(rows) -> tuple:
    """Test-side: (Σ I_g)² / Σ I_g² and max I_g / Σ I_g, I_g a paper's sum of squared within-alloy
    deviations of the transformed grain size."""
    f = frame(rows)
    dev = f["x"] - f.groupby("alloy")["x"].transform("mean")
    info = (dev ** 2).groupby(f["group"]).sum()
    return float(info.sum() ** 2 / (info ** 2).sum()), float(info.max() / info.sum())
