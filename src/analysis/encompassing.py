"""Forecast encompassing: equally accurate is not the same as redundant.

The dead heat (equal Brier, TOST-equivalent) says the three sources are equally
GOOD. It does not say whether any of them carries information the others lack —
two forecasters can tie on accuracy while each knows something the other doesn't
(combining them would then help), or one can be a pure copy of the other.

The formal test (Chong & Hendry 1986 adapted to probabilities): combine forecasts
on the log-odds scale and fit
    home_won ~ logit(p_A) + logit(p_B)      [+ logit(p_C)]
with date-cluster-robust SEs. Source A "encompasses" B if B's coefficient is zero
given A — B adds no information beyond A. Weights that both matter mean the
forecasts are complementary and an ensemble should beat either (our ensemble test
already found no Brier gain, p=0.25 — this is the formal, more powerful version).

Caveat printed with results: the prices are correlated at r~0.99, so individual
coefficients are unstable by construction; the reported tests are of INCREMENTAL
information (each coefficient given the others), which is exactly the question.

Also included: liquidity-controlled cluster-robust DM on tight-spread games only.
The pre-side-fix data showed "Kalshi lags the book even on liquid games
(p=0.004)"; that claim was never re-tested after the repair — done here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from src.analysis.compare import brier
from src.analysis.rigor import cluster_dm
from src.analysis.three_way import SRC, load

LOGIT_CLIP = 0.01


def lo(p):
    p = np.clip(np.asarray(p, float), LOGIT_CLIP, 1 - LOGIT_CLIP)
    return np.log(p / (1 - p))


def encompass(d, cols, dates, label):
    """Logit of home_won on the log-odds of each source in `cols` (+ intercept),
    date-clustered SEs. Prints weight, z, p per source and the LR test of each
    source's exclusion (does dropping it lose information?)."""
    y = d["home_won"].values
    X = sm.add_constant(np.column_stack([lo(d[c]) for c in cols]))
    r = sm.Logit(y, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": dates})
    full_llf = r.llf
    print(f"\n  --- {label} (n={len(d):,}) ---", flush=True)
    for k, c in enumerate(cols, start=1):
        # LR test: refit without source k (plain MLE llf comparison)
        keep = [i for i in range(1, len(cols) + 1) if i != k]
        Xr = X[:, [0] + keep]
        rr = sm.Logit(y, Xr).fit(disp=0)
        lr = 2 * (full_llf - rr.llf)
        p_lr = 1 - stats.chi2.cdf(lr, df=1)
        name = c.replace("_p1", "")
        print(f"    {name:8} weight={r.params[k]:+.3f}  clustered z={r.tvalues[k]:+.2f} "
              f"p={r.pvalues[k]:.3f}   LR excl. p={p_lr:.3f}", flush=True)
    return r


def main():
    d = load()
    y = d["home_won"].values
    dates = pd.to_datetime(d["start_utc"], utc=True, format="ISO8601").dt.date.values
    print(f"clean all-three games: {len(d):,} ({len(set(dates))} date clusters)", flush=True)
    print(f"price correlations: K-book={d.kalshi_p1.corr(d.book_p1):.4f}  "
          f"P-book={d.poly_p1.corr(d.book_p1):.4f}  K-P={d.kalshi_p1.corr(d.poly_p1):.4f}", flush=True)

    print("\n=== pairwise encompassing (does the 2nd source add info beyond the 1st?) ===", flush=True)
    encompass(d, ["book_p1", "kalshi_p1"], dates, "book + Kalshi")
    encompass(d, ["book_p1", "poly_p1"], dates, "book + Polymarket")
    encompass(d, ["kalshi_p1", "poly_p1"], dates, "Kalshi + Polymarket")

    print("\n=== all three ===", flush=True)
    encompass(d, ["book_p1", "kalshi_p1", "poly_p1"], dates, "book + Kalshi + Polymarket")
    print("\n  (weights sum >1 is fine — log-odds combination; the question is each", flush=True)
    print("   source's INCREMENTAL p-value, not the raw weight. r~0.99 collinearity", flush=True)
    print("   makes single weights unstable; LR exclusion tests are the verdict.)", flush=True)

    # --- who's right when they disagree? (model-free complement) ---
    print("\n=== divergent games: who is closer to the outcome? ===", flush=True)
    for a, b in [("kalshi_p1", "book_p1"), ("poly_p1", "book_p1"), ("kalshi_p1", "poly_p1")]:
        gap = (d[a] - d[b]).abs()
        div = d[gap > 0.03]
        if not len(div):
            continue
        a_closer = (np.abs(div[a] - div.home_won) < np.abs(div[b] - div.home_won)).mean()
        an, bn = a.replace("_p1", ""), b.replace("_p1", "")
        print(f"  |{an}-{bn}|>3pts: n={len(div):4}  {an} closer {a_closer:.1%} of the time", flush=True)

    # --- timing-artifact check ---------------------------------------------
    # Book quotes come from Odds API snapshots at start floored to 30 min
    # (sportsbook_hist.build, bucket_min=30), so book staleness = minutes past
    # the half-hour, 0-29. Kalshi is priced AT start. If Kalshi's incremental
    # information is just fresher news (lineups/scratches in the gap), it should
    # concentrate in stale-book games and vanish where the book quote is fresh.
    print("\n=== timing check: encompassing by book-quote staleness ===", flush=True)
    start = pd.to_datetime(d["start_utc"], utc=True, format="ISO8601")
    d = d.assign(stale_min=(start - start.dt.floor("30min")).dt.total_seconds() / 60)
    for label, sub in [("fresh (<10 min)", d[d.stale_min < 10]),
                       ("stale (>=10 min)", d[d.stale_min >= 10])]:
        sd = pd.to_datetime(sub["start_utc"], utc=True, format="ISO8601").dt.date.values
        encompass(sub, ["book_p1", "kalshi_p1"], sd, f"book + Kalshi, book {label}")
        dbar, se, z, p, _ = cluster_dm(sub["kalshi_p1"], sub["book_p1"], sub["home_won"].values, sd)
        print(f"    DM Kalshi-book: ΔBrier={dbar*1000:+.3f}e-3  z={z:+.2f} p={p:.3f}", flush=True)

    # --- per-league sign consistency (book + Kalshi) ---
    print("\n=== per-league: Kalshi increment beyond the book ===", flush=True)
    print(f"  {'league':7}{'n':>6}  {'K weight':>9}{'z':>7}{'p':>7}", flush=True)
    for lg, g in d.groupby("league"):
        gd = pd.to_datetime(g["start_utc"], utc=True, format="ISO8601").dt.date.values
        X = sm.add_constant(np.column_stack([lo(g["book_p1"]), lo(g["kalshi_p1"])]))
        try:
            r = sm.Logit(g["home_won"].values, X).fit(
                disp=0, cov_type="cluster", cov_kwds={"groups": gd})
            print(f"  {lg:7}{len(g):>6}  {r.params[2]:>+9.3f}{r.tvalues[2]:>7.2f}{r.pvalues[2]:>7.3f}", flush=True)
        except Exception as e:
            print(f"  {lg:7}{len(g):>6}  (fit failed: {e})", flush=True)

    # --- liquidity-controlled DM, clean data (retires the pre-fix p=0.004 claim) ---
    print("\n=== liquidity-controlled cluster-robust DM (tight Kalshi spread <=0.01) ===", flush=True)
    liq = d[d["k_spread1"] <= 0.01].copy()
    ld = pd.to_datetime(liq["start_utc"], utc=True, format="ISO8601").dt.date.values
    yy = liq["home_won"].values
    print(f"  liquid games: {len(liq):,}", flush=True)
    names = list(SRC)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            dbar, se, z, p, ci = cluster_dm(liq[SRC[a][0]], liq[SRC[b][0]], yy, ld)
            print(f"  {a} - {b}: ΔBrier={dbar*1000:+.3f}e-3  z={z:+.2f} p={p:.3f}", flush=True)
    for name, (c1, _) in SRC.items():
        print(f"  {name:11} liquid Brier={brier(liq[c1], yy):.4f}", flush=True)


if __name__ == "__main__":
    main()
