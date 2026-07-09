"""Inference hardening for the three-way dead heat.

1. Cluster-robust DM tests (cluster by date: same-day games share news/conditions).
2. TOST equivalence: turn "not significant" into "statistically equivalent within ±δ".
   We report the 90% CI of each pairwise Brier difference — equivalence holds at any
   margin δ wider than that CI.
3. De-vig robustness: recompute book probabilities with Shin's model (which accounts
   for insider/informed betting) instead of multiplicative normalization; re-test.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.three_way import load, SRC


def cluster_dm(pA, pB, y, clusters):
    """DM on squared-error differential with cluster-robust (by date) SE."""
    d = ((np.asarray(pA) - y) ** 2 - (np.asarray(pB) - y) ** 2)
    n = len(d)
    dbar = d.mean()
    g = pd.DataFrame({"d": d - dbar, "c": clusters}).groupby("c")["d"].sum()
    se = np.sqrt((g ** 2).sum()) / n
    z = dbar / se
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    ci90 = (dbar - 1.645 * se, dbar + 1.645 * se)
    return dbar, se, z, p, ci90


def shin_two_way(pi1, pi2):
    """Shin (1993) fair probabilities for a 2-outcome market from raw implied probs."""
    PI = pi1 + pi2
    lo, hi = 0.0, 0.4
    for _ in range(60):  # bisection on insider fraction z
        z = (lo + hi) / 2
        p1 = (np.sqrt(z * z + 4 * (1 - z) * pi1 * pi1 / PI) - z) / (2 * (1 - z))
        p2 = (np.sqrt(z * z + 4 * (1 - z) * pi2 * pi2 / PI) - z) / (2 * (1 - z))
        if p1 + p2 > 1:
            lo = z
        else:
            hi = z
    s = p1 + p2
    return p1 / s, p2 / s


def main():
    d = load()
    y = d["home_won"].values
    dates = pd.to_datetime(d["start_utc"], utc=True, format="ISO8601").dt.date.values
    n_days = len(set(dates))
    print(f"clean all-three games: {len(d):,} across {n_days} dates (clusters)\n", flush=True)

    print("=== cluster-robust (by date) pairwise DM + 90% CI of Brier difference ===", flush=True)
    names = list(SRC)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            dbar, se, z, p, ci = cluster_dm(d[SRC[a][0]], d[SRC[b][0]], y, dates)
            print(f"  {a} - {b}: ΔBrier={dbar*1000:+.3f}e-3  clustSE={se*1000:.3f}e-3  "
                  f"z={z:+.2f} p={p:.3f}  90%CI=({ci[0]*1000:+.3f},{ci[1]*1000:+.3f})e-3", flush=True)
    print("  -> equivalence (TOST) holds at margin δ iff the 90% CI lies inside ±δ.", flush=True)
    print("     For scale: δ=1.0e-3 Brier ≈ a 0.5% probability error on every game.", flush=True)

    print("\n=== de-vig robustness: multiplicative vs Shin (book fair probs) ===", flush=True)
    sb = pd.read_csv("data/processed/sportsbook_hist_prices.csv")[["game_id", "book_raw1", "book_raw2"]]
    m = d.merge(sb, on="game_id", how="inner").dropna(subset=["book_raw1", "book_raw2"])
    yy = m["home_won"].values
    dd = pd.to_datetime(m["start_utc"], utc=True, format="ISO8601").dt.date.values
    shin = np.array([shin_two_way(a, b) for a, b in zip(m.book_raw1, m.book_raw2)])
    m["book_shin1"] = shin[:, 0]
    from src.analysis.compare import brier
    print(f"  book Brier multiplicative={brier(m.book_p1, yy):.4f}  Shin={brier(m.book_shin1, yy):.4f}", flush=True)
    print(f"  mean |shift| in book prob: {np.abs(m.book_shin1-m.book_p1).mean()*100:.3f} pts", flush=True)
    for a in ("Kalshi", "Polymarket"):
        dbar, se, z, p, ci = cluster_dm(m[SRC[a][0]], m["book_shin1"], yy, dd)
        print(f"  {a} - Book(Shin): ΔBrier={dbar*1000:+.3f}e-3  z={z:+.2f} p={p:.3f}", flush=True)


if __name__ == "__main__":
    main()
