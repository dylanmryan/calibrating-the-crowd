"""Natural experiment: did Polymarket's fee introduction change price quality?

Polymarket sports were FEE-FREE until 2026-03-30, then a taker fee (peak 0.75%
at 50/50) switched on mid-sample. Institutional-design question: do fees degrade
(or improve, via discouraging noise trading) the forecast quality of an exchange?

Design: within-era paired accuracy vs the sportsbook benchmark (which had no
regime change), then a difference-in-differences on the per-game Brier
differential d_i = e_poly - e_book regressed on a post dummy (date-clustered).
Kalshi (fee schedule unchanged) runs as a placebo: its differential vs the book
should NOT move at the boundary. League composition shifts across eras (seasons),
so league fixed effects are included in the DiD.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.analysis.compare import brier, ece, cal_slope, stacked
from src.analysis.three_way import load

FEE_DATE = "2026-03-30"


def did(d, src_col, label):
    """Regress per-game squared-error differential (src - book) on post dummy."""
    y = d["home_won"].values
    e_src = (d[src_col] - y) ** 2
    e_book = (d["book_p1"] - y) ** 2
    dd = (e_src - e_book).values
    X = pd.get_dummies(d["league"], drop_first=True, dtype=float)
    X.insert(0, "post", (d["start_utc"] >= FEE_DATE).astype(float).values)
    X = sm.add_constant(X)
    dates = pd.to_datetime(d["start_utc"], utc=True, format="ISO8601").dt.date.values
    r = sm.OLS(dd, X).fit(cov_type="cluster", cov_kwds={"groups": dates})
    print(f"  {label:22} post coeff={r.params['post']*1000:+.3f}e-3 Brier  "
          f"z={r.tvalues['post']:+.2f}  p={r.pvalues['post']:.3f}", flush=True)


def main():
    d = load()
    d["post"] = d["start_utc"] >= FEE_DATE
    print(f"clean all-three games: {len(d):,}  "
          f"pre-fee {len(d[~d.post]):,} / post-fee {len(d[d.post]):,}", flush=True)
    print("league mix:", flush=True)
    print(pd.crosstab(d.league, d.post).to_string(), flush=True)

    print("\n=== per-era Polymarket quality (vs book on the same games) ===", flush=True)
    print(f"  {'era':10} {'n':>6} {'Poly Brier':>11} {'Book Brier':>11} {'Poly ECE':>9} {'Poly slope':>11}", flush=True)
    for post, g in d.groupby("post"):
        y = g["home_won"].values
        p, yy = stacked(g, "poly_p1", "poly_p2")
        print(f"  {'post-fee' if post else 'pre-fee':10} {len(g):>6,} "
              f"{brier(g.poly_p1, y):>11.4f} {brier(g.book_p1, y):>11.4f} "
              f"{ece(p, yy):>9.4f} {cal_slope(p, yy):>11.3f}", flush=True)

    print("\n=== difference-in-differences on per-game Brier differential ===", flush=True)
    did(d, "poly_p1", "Polymarket - book")
    did(d, "kalshi_p1", "Kalshi - book (placebo)")
    print("  (positive post coeff = source worsened vs book after the fee date)", flush=True)


if __name__ == "__main__":
    main()
