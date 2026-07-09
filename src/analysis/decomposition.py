"""Deeper three-way analysis: Brier decomposition, favorite-longshot, liquidity heterogeneity.

Murphy decomposition:  Brier = Reliability - Resolution + Uncertainty
  - Reliability (calibration): lower is better  -> are the probabilities right?
  - Resolution (discrimination): higher is better -> do they separate winners from losers?
  - Uncertainty: base-rate variance, identical across sources on the same games.
This separates "well-calibrated" from "informative" — a source can be one without the other.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.analysis.compare import brier, stacked, ece
from src.analysis.three_way import SRC, load


def murphy(p, y, nbins=10):
    p, y = np.asarray(p, float), np.asarray(y, float)
    ybar, N = y.mean(), len(y)
    edges = np.linspace(0, 1, nbins + 1)
    b = np.clip(np.digitize(p, edges) - 1, 0, nbins - 1)
    rel = res = 0.0
    for k in range(nbins):
        m = b == k
        nk = int(m.sum())
        if nk == 0:
            continue
        rel += nk * (p[m].mean() - y[m].mean()) ** 2
        res += nk * (y[m].mean() - ybar) ** 2
    rel, res = rel / N, res / N
    return {"brier": brier(p, y), "reliability": rel, "resolution": res,
            "uncertainty": ybar * (1 - ybar), "skill": res - rel}


def slope_ci(p, y):
    """Logistic recalibration slope + 95% CI. slope<1 (CI excludes 1) => favorite-longshot."""
    p = np.clip(np.asarray(p, float), 0.01, 0.99)
    X = sm.add_constant(np.log(p / (1 - p)))
    r = sm.Logit(np.asarray(y), X).fit(disp=0)
    lo, hi = r.conf_int()[1]
    return r.params[1], lo, hi


def main():
    d = load()
    print(f"three-way clean games: {len(d):,}\n", flush=True)

    print("=== Brier decomposition (both-sides, ×1000 for readability) ===", flush=True)
    print(f"  uncertainty (same for all) = {murphy(*stacked(d,'kalshi_p1','kalshi_p2'))['uncertainty']*1000:.1f}", flush=True)
    print(f"  {'source':11}{'Brier':>8}{'Reliab(cal)':>12}{'Resol(disc)':>12}{'Skill':>8}", flush=True)
    for name, (c1, c2) in SRC.items():
        m = murphy(*stacked(d, c1, c2))
        print(f"  {name:11}{m['brier']*1000:>8.1f}{m['reliability']*1000:>12.2f}"
              f"{m['resolution']*1000:>12.1f}{m['skill']*1000:>8.1f}", flush=True)
    print("  (lower Reliability = better calibrated; higher Resolution = more informative)", flush=True)

    print("\n=== favorite-longshot: calibration slope (95% CI) ===", flush=True)
    for name, (c1, c2) in SRC.items():
        s, lo, hi = slope_ci(*stacked(d, c1, c2))
        flag = "FAV-LONGSHOT (slope<1)" if hi < 1 else ("overconfident-ish" if s < 1 else "ok")
        print(f"  {name:11} slope={s:.3f} ({lo:.2f},{hi:.2f})  {flag}", flush=True)

    print("\n=== resolution by sport (discrimination; higher=better) ===", flush=True)
    print(f"  {'league':7}{'n':>6}  {'Kalshi':>8}{'Poly':>8}{'Book':>8}", flush=True)
    for lg, g in d.groupby("league"):
        r = {name: murphy(*stacked(g, c[0], c[1]))["resolution"] * 1000 for name, c in SRC.items()}
        print(f"  {lg:7}{len(g):>6}  {r['Kalshi']:>8.1f}{r['Polymarket']:>8.1f}{r['Sportsbook']:>8.1f}", flush=True)

    print("\n=== Kalshi calibration by liquidity (spread tertiles) ===", flush=True)
    g = d.dropna(subset=["k_spread1"]).copy()
    if len(g):
        g["liq"] = pd.qcut(g["k_spread1"], [0, .5, .9, 1.0], labels=["tight", "mid", "wide"], duplicates="drop")
        for lv, sub in g.groupby("liq", observed=True):
            p, y = stacked(sub, "kalshi_p1", "kalshi_p2")
            print(f"  spread {str(lv):5} n={len(sub):5}  Kalshi ECE={ece(p,y):.4f}  "
                  f"reliability={murphy(p,y)['reliability']*1000:.2f}", flush=True)


if __name__ == "__main__":
    main()
