"""Fee incidence on liquidity: who absorbed Polymarket's 2026-03-30 sports fee?

The accuracy half was null (fee_experiment: price quality unmoved). This is
the economic half, on NBA/NHL games priced by both exchanges Feb 2 - May 25:

  volume — within-game log volume ratio  Δ_i = log(poly_vol) − log(k_notional),
    compared across the fee date with league controls and date-clustered SEs.
    Pairing within games nets out game quality and league mix. COVERAGE
    CONSTRAINT: gamma archives most March markets with volume stripped
    (coverage 100% in Feb, 7-57% across March, 100% post), so the MAIN spec
    uses only the complete-coverage windows — February vs April-May — and the
    March stretch is excluded; the placebo splits February in half. Residual
    caveat: the windows sit either side of the playoff transition, and any
    venue-specific playoff attention shift loads onto the estimate.
  spreads — OddPool archived order books: quoted spread at T-30m, pre-fee
    (Mar 21-29, the archive's earliest coverage) vs post-fee (Apr 1-14).
    Taker fee + maker rebate could widen (taker flow leaves) or narrow
    (rebate subsidizes quoting) the touch.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FEE_DATE = pd.Timestamp("2026-03-30", tz="UTC")
PLACEBO = pd.Timestamp("2026-03-02", tz="UTC")


def did(d, boundary, label):
    d = d.copy()
    d["post"] = (d.t >= boundary).astype(float)
    X = sm.add_constant(np.column_stack([d.post.values,
                                         (d.league == "NHL").astype(float).values]))
    r = sm.OLS(d.delta.values, X).fit(cov_type="cluster",
                                      cov_kwds={"groups": d.date.values})
    print(f"  {label:28} post = {r.params[1]:+.3f} log-pts "
          f"({(np.exp(r.params[1])-1)*100:+.1f}%)  z={r.tvalues[1]:+.2f}  "
          f"p={r.pvalues[1]:.3f}  n={len(d):,}", flush=True)
    return r.params[1], r.bse[1]


def main():
    d = pd.read_csv("data/processed/fee_volumes.csv")
    d = d[(d.poly_vol > 0) & (d.k_notional > 0)].copy()
    d["t"] = pd.to_datetime(d.start_utc, utc=True, format="ISO8601")
    d["date"] = d.t.dt.date
    d["delta"] = np.log(d.poly_vol) - np.log(d.k_notional)
    pre, post = d[d.t < FEE_DATE], d[d.t >= FEE_DATE]
    print(f"games with both volumes: {len(d):,} "
          f"({len(pre)} pre-fee, {len(post)} post-fee; "
          f"{d.league.value_counts().to_dict()})", flush=True)
    print(f"median per-game volume: Poly ${d.poly_vol.median():,.0f} | "
          f"Kalshi final-24h notional ${d.k_notional.median():,.0f} "
          f"(units differ; only the ratio's CHANGE is used)", flush=True)

    print("\n=== within-game volume-ratio comparison (Δ = log poly − log kalshi) ===", flush=True)
    feb = d[d.t < pd.Timestamp("2026-03-02", tz="UTC")]
    clean = pd.concat([feb, d[d.t >= pd.Timestamp("2026-04-01", tz="UTC")]])
    b, se = did(clean, FEE_DATE, "MAIN: Feb vs Apr-May (full coverage)")
    did(feb, pd.Timestamp("2026-02-16", tz="UTC"), "placebo mid-Feb split")
    did(d, FEE_DATE, "full sample (March coverage-biased)")

    print("\n=== levels (descriptive; playoff ramp NOT controlled) ===", flush=True)
    for col, lab in [("poly_vol", "Polymarket"), ("k_notional", "Kalshi 24h")]:
        lp = np.log(d[col])
        print(f"  {lab:11} mean log volume pre {lp[d.t < FEE_DATE].mean():.2f} "
              f"-> post {lp[d.t >= FEE_DATE].mean():.2f} "
              f"({(np.exp(lp[d.t >= FEE_DATE].mean() - lp[d.t < FEE_DATE].mean())-1)*100:+.0f}%)",
              flush=True)

    # event-time: biweekly mean of the ratio
    d["bi"] = d.t.dt.to_period("W").dt.start_time
    ev = d.groupby("bi").agg(delta=("delta", "mean"), n=("delta", "size")).reset_index()

    # spreads leg (may still be collecting — degrade gracefully)
    spr = None
    if os.path.exists("data/processed/fee_spreads.csv"):
        spr = pd.read_csv("data/processed/fee_spreads.csv").drop_duplicates("game_id")
        print("\n=== quoted spread at T-30m (OddPool archived books) ===", flush=True)
        for era, g in spr.groupby("era"):
            print(f"  {era:4} n={len(g):3}  median spread {g.poly_spread.median()*100:.1f}pts  "
                  f"mean {g.poly_spread.mean()*100:.2f}pts", flush=True)
        if spr.era.nunique() == 2:
            a = spr[spr.era == "pre"].poly_spread
            bpost = spr[spr.era == "post"].poly_spread
            u, p = stats.mannwhitneyu(a, bpost, alternative="two-sided")
            print(f"  Mann-Whitney pre vs post: p={p:.3f}", flush=True)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axes[0]
    ax.errorbar(ev.bi, ev.delta, yerr=1.96 * d.groupby("bi").delta.sem().values,
                fmt="o-", ms=4, capsize=2, color="tab:purple")
    ax.axvline(FEE_DATE.tz_localize(None), color="tab:red", ls="--", lw=1.2, label="fee introduced")
    ax.axhline(d[d.t < FEE_DATE].delta.mean(), color="0.6", ls=":", lw=1)
    ax.set(ylabel="log(Poly vol) − log(Kalshi vol), weekly mean",
           title=f"Relative volume around the fee (DiD {b:+.2f}±{1.96*se:.2f} log-pts)")
    ax.legend(fontsize=8)
    ax.tick_params(axis="x", rotation=45)

    ax = axes[1]
    if spr is not None and spr.era.nunique() == 2:
        for i, era in enumerate(["pre", "post"]):
            g = spr[spr.era == era]
            ax.scatter(np.full(len(g), i) + np.linspace(-0.12, 0.12, len(g)),
                       g.poly_spread * 100, s=14, alpha=0.6,
                       color="tab:green" if era == "pre" else "tab:red")
            ax.hlines(g.poly_spread.median() * 100, i - 0.2, i + 0.2, color="0.2", lw=2)
        ax.set_xticks([0, 1], ["pre-fee\n(Mar 21–29)", "post-fee\n(Apr 1–14)"])
        ax.set(ylabel="quoted spread at T-30m (pts)",
               title="Polymarket touch around the fee")
    fig.suptitle("Who bears the Polymarket sports fee?")
    fig.tight_layout()
    fig.savefig("results/fee_liquidity.png", dpi=130)
    print("\nsaved results/fee_liquidity.png", flush=True)


if __name__ == "__main__":
    main()
