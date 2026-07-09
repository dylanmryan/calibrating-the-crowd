"""Three-way calibration: Kalshi vs Polymarket vs sportsbook on the same games.

The core thesis test: do prediction markets match, beat, or lag the professional
books? On games where all three price the same event (resolved, no disagreement):
  - Brier per source; pairwise Diebold-Mariano tests (who is significantly better?)
  - Calibration slope + ECE per source
  - Reliability overlay (three curves)
  - Per-league Brier table
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.compare import brier, cal_slope, ece, stacked, reliability

SRC = {"Kalshi": ("kalshi_p1", "kalshi_p2"),
       "Polymarket": ("poly_p1", "poly_p2"),
       "Sportsbook": ("book_p1", "book_p2")}
COLOR = {"Kalshi": "tab:blue", "Polymarket": "tab:orange", "Sportsbook": "tab:green"}


def load(path="data/processed/games_master.csv"):
    m = pd.read_csv(path)
    m = m[m["outcome"].notna() & ~m["outcome_disagree"].fillna(False)]
    m = m[m["kalshi_p1"].notna() & m["poly_p1"].notna() & m["book_p1"].notna()].copy()
    m["home_won"] = (m["outcome"] == 1).astype(int)
    return m


def dm(pA, pB, y):
    """Diebold-Mariano: <0 means A better (lower loss). Returns (stat, pvalue)."""
    d = ((pA - y) ** 2 - (pB - y) ** 2).values
    stat = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    return stat, 2 * (1 - stats.norm.cdf(abs(stat)))


def main():
    d = load()
    y = d["home_won"].values
    print(f"all-three games (clean): {len(d):,}\n", flush=True)

    print("=== per-source metrics (home-team framing for Brier) ===", flush=True)
    for name, (c1, c2) in SRC.items():
        p, yy = stacked(d, c1, c2)
        print(f"  {name:11} Brier={brier(d[c1], y):.4f}  slope={cal_slope(p, yy):.3f}  ECE={ece(p, yy):.4f}", flush=True)

    print("\n=== pairwise Diebold-Mariano (who forecasts better?) ===", flush=True)
    names = list(SRC)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            s, pv = dm(d[SRC[a][0]], d[SRC[b][0]], y)
            better = a if s < 0 else b
            sig = "significant" if pv < 0.05 else "n.s."
            print(f"  {a} vs {b}: DM={s:+.2f} (p={pv:.3f}) -> {better} better ({sig})", flush=True)

    print("\n=== per league: Brier by source ===", flush=True)
    print(f"  {'league':7}{'n':>6}  {'Kalshi':>8}{'Poly':>8}{'Book':>8}   best", flush=True)
    for lg, g in d.groupby("league"):
        yy = g["home_won"].values
        b = {n: brier(g[c[0]], yy) for n, c in SRC.items()}
        best = min(b, key=b.get)
        print(f"  {lg:7}{len(g):>6}  {b['Kalshi']:>8.4f}{b['Polymarket']:>8.4f}{b['Sportsbook']:>8.4f}   {best}", flush=True)

    # reliability overlay
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfect")
    for name, (c1, c2) in SRC.items():
        p, yy = stacked(d, c1, c2)
        t = reliability(p, yy)
        ax.plot(t.pred, t.obs, "o-", color=COLOR[name], ms=4, label=f"{name} (Brier={brier(p, yy):.3f})")
    ax.set(xlabel="Predicted probability", ylabel="Observed win frequency",
           title=f"Kalshi vs Polymarket vs Sportsbook (n={len(d):,})", xlim=(0, 1), ylim=(0, 1))
    ax.set_aspect("equal"); ax.legend(loc="upper left")
    fig.tight_layout(); fig.savefig("results/three_way_calibration.png", dpi=130)
    print("\nsaved results/three_way_calibration.png", flush=True)


if __name__ == "__main__":
    main()
