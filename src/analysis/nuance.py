"""Nuanced calibration analysis of Kalshi pre-game prices vs outcomes.

Beyond the basic reliability diagram, this reports:
  - Calibration slope/intercept (logistic recalibration) -> over/under-confidence
  - Expected & maximum calibration error (ECE / MCE)
  - Per-bin observed vs predicted with Wilson CIs and binomial significance
  - Favorite-longshot signature (residual vs predicted)
  - Irregularities: does calibration degrade with wider spreads (thin books) or stale quotes?
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / d
    return (c - h, c + h)


def reliability_table(df, nbins=20):
    edges = np.linspace(0, 1, nbins + 1)
    d = df.copy()
    d["bin"] = pd.cut(d["implied_prob"], edges, include_lowest=True)
    rows = []
    for b, g in d.groupby("bin", observed=True):
        n, k = len(g), int(g["won"].sum())
        lo, hi = wilson(k, n)
        pred = g["implied_prob"].mean()
        # Binomial two-sided p: is the observed win rate != predicted? The rows
        # here are contract-SIDES, and a game contributes two deterministically
        # mirrored ones, so n overstates the independent information and the
        # naive p is anti-conservative (2026-07-30 review, item 15). Halve the
        # effective sample before testing; the Wilson CI above is left on the
        # full n and is therefore the tighter of the two displays.
        n_eff = max(int(round(n / 2)), 1)
        k_eff = int(round(k / 2))
        pval = (stats.binomtest(min(k_eff, n_eff), n_eff,
                                min(max(pred, 1e-9), 1 - 1e-9)).pvalue if n else np.nan)
        rows.append({"bin": str(b), "pred": pred, "obs": k / n, "n": n,
                     "ci_lo": lo, "ci_hi": hi, "resid": k / n - pred, "p_value": pval})
    return pd.DataFrame(rows)


def calibration_fit(df):
    """Logistic recalibration: won ~ logit(pred). slope=1,intercept=0 => perfectly calibrated."""
    p = df["implied_prob"].clip(0.01, 0.99)
    X = sm.add_constant(np.log(p / (1 - p)))
    res = sm.Logit(df["won"].values, np.asarray(X)).fit(disp=0)
    ci = res.conf_int()
    return {"intercept": res.params[0], "slope": res.params[1],
            "slope_ci": (ci[1][0], ci[1][1]), "n": len(df)}


def ece_mce(tbl):
    w = tbl["n"] / tbl["n"].sum()
    ece = float((w * tbl["resid"].abs()).sum())
    mce = float(tbl["resid"].abs().max())
    return ece, mce


def report(df):
    print(f"\n=== OVERALL (n={len(df):,} contract-sides) ===", flush=True)
    fit = calibration_fit(df)
    print(f"calibration slope={fit['slope']:.3f} (95% CI {fit['slope_ci'][0]:.2f},{fit['slope_ci'][1]:.2f}), "
          f"intercept={fit['intercept']:.3f}", flush=True)
    print(f"  slope<1 => overconfident/favorite-longshot; =1 => calibrated", flush=True)
    print(f"calibration-in-the-large: mean_pred={df['implied_prob'].mean():.4f} "
          f"vs mean_obs={df['won'].mean():.4f}", flush=True)
    tbl = reliability_table(df)
    ece, mce = ece_mce(tbl)
    print(f"ECE={ece:.4f}  MCE={mce:.4f}", flush=True)
    print("\nper-bin (flagged * = obs differs from pred at p<0.05):", flush=True)
    for r in tbl.itertuples(index=False):
        flag = "*" if (r.p_value is not None and r.p_value < 0.05) else " "
        print(f"  {r.bin:14} pred={r.pred:.3f} obs={r.obs:.3f} [{r.ci_lo:.2f},{r.ci_hi:.2f}] "
              f"n={r.n:4} resid={r.resid:+.3f} {flag}", flush=True)

    print("\n=== per league ===", flush=True)
    for lg, g in df.groupby("league"):
        if len(g) < 30:
            print(f"  {lg:6} n={len(g):4} (too few)", flush=True); continue
        f = calibration_fit(g)
        e, _ = ece_mce(reliability_table(g, nbins=10))
        print(f"  {lg:6} n={len(g):5} slope={f['slope']:.2f} "
              f"cal-in-large={g['implied_prob'].mean()-g['won'].mean():+.3f} ECE={e:.3f}", flush=True)

    print("\n=== irregularities ===", flush=True)
    # liquidity: does calibration worsen in wider-spread (thinner) books?
    df2 = df.copy()
    med = df2["spread"].median()
    df2["liq"] = np.where(df2["spread"] <= med, f"tight(<={med:.2f})", f"wide(>{med:.2f})")
    for lv, g in df2.groupby("liq"):
        e, _ = ece_mce(reliability_table(g, nbins=10))
        print(f"  spread {lv:14} n={len(g):5} ECE={e:.3f} mean_spread={g['spread'].mean():.3f} "
              f"cal-in-large={g['implied_prob'].mean()-g['won'].mean():+.3f}", flush=True)
    # staleness: quotes far from tip-off
    df2["fresh"] = np.where(df2["staleness_min"] <= 5, "<=5min", ">5min")
    for lv, g in df2.groupby("fresh"):
        e, _ = ece_mce(reliability_table(g, nbins=10))
        print(f"  quote {lv:7} n={len(g):5} ECE={e:.3f}", flush=True)
    return tbl, fit


def plots(df, tbl):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))
    ax1.plot([0, 1], [0, 1], "k--", lw=1)
    ax1.errorbar(tbl["pred"], tbl["obs"],
                 yerr=[tbl["obs"] - tbl["ci_lo"], tbl["ci_hi"] - tbl["obs"]],
                 fmt="o", ms=4, color="tab:blue", ecolor="0.7", capsize=2)
    ax1.set(xlabel="Predicted (Kalshi book mid)", ylabel="Observed win freq",
            title=f"Reliability (n={len(df):,})", xlim=(0, 1), ylim=(0, 1))
    ax1.set_aspect("equal")

    ax2.axhline(0, color="k", lw=1)
    ax2.scatter(tbl["pred"], tbl["resid"], s=tbl["n"] / tbl["n"].max() * 300 + 15, color="tab:red", alpha=0.6)
    ax2.set(xlabel="Predicted probability", ylabel="Observed - Predicted",
            title="Favorite-longshot signature", xlim=(0, 1))
    fig.tight_layout()
    fig.savefig("results/kalshi_nuance.png", dpi=130)
    print("\nsaved results/kalshi_nuance.png", flush=True)


if __name__ == "__main__":
    df = pd.read_csv("data/processed/kalshi_prices.csv")
    df = df[(df["implied_prob"] > 0) & (df["implied_prob"] < 1)]
    tbl, fit = report(df)
    plots(df, tbl)
