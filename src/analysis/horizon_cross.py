"""Comparative multi-horizon calibration: Kalshi vs Polymarket sharpening curves.

Completes the Page-Clemen replication comparatively: both exchanges' home-side
price paths sampled at the same 7 horizons (T-24h -> start) on a joint constant
sample (a price at EVERY horizon on BOTH venues), with the book consensus as
reference points at the ends (T-24h collector; closing line from the master).
Per horizon: Brier each, and the K-P Brier differential with date-clustered DM.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.compare import brier, ece
from src.analysis.rigor import cluster_dm
from src.analysis.horizon import HORIZONS_MIN, LABEL
from src.analysis.horizon_equivalence import load


def main():
    d = load()
    cols = [f"p_h{h}" for h in HORIZONS_MIN] + [f"q_h{h}" for h in HORIZONS_MIN]
    d = d.dropna(subset=cols).copy()
    d["date"] = d.start_utc.astype(str).str[:10]
    y = d.home_won.values
    print(f"joint constant sample (all 7 horizons on BOTH exchanges): {len(d):,} games")
    print(d.league.value_counts().to_string(), "\n")

    print(f"{'horizon':>8} {'K Brier':>9} {'P Brier':>9} {'K ECE':>7} {'P ECE':>7} "
          f"{'dBrier K-P':>11} {'z':>6} {'p':>6}")
    kb, pb = [], []
    for h in HORIZONS_MIN:
        pk, pq = d[f"p_h{h}"].values, d[f"q_h{h}"].values
        dbar, se, z, p, _ = cluster_dm(pk, pq, y, d.date.values)
        kb.append(brier(pk, y)); pb.append(brier(pq, y))
        print(f"{LABEL[h]:>8} {kb[-1]:>9.4f} {pb[-1]:>9.4f} {ece(pk, y):>7.4f} "
              f"{ece(pq, y):>7.4f} {dbar*1000:>+10.2f}e-3 {z:>+6.2f} {p:>6.3f}")

    b24 = brier(d.book24_p1.values, y)
    b0 = brier(d.book_p1.values, y)
    print(f"\nbook reference (same games): T-24h Brier {b24:.4f}, close {b0:.4f}")
    mvk = (d.p_h0 - d.p_h1440).abs().mean() * 100
    mvp = (d.q_h0 - d.q_h1440).abs().mean() * 100
    print(f"mean |move| 24h->start: Kalshi {mvk:.1f}pts, Polymarket {mvp:.1f}pts")

    x = np.arange(len(HORIZONS_MIN))
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    ax.plot(x, kb, "o-", color="tab:green", label=f"Kalshi (n={len(d):,})")
    ax.plot(x, pb, "s-", color="tab:purple", label="Polymarket")
    ax.scatter([0, x[-1]], [b24, b0], marker="D", s=70, color="tab:orange",
               zorder=5, label="book consensus (T-24h / close)")
    ax.set_xticks(x, [LABEL[h] for h in HORIZONS_MIN])
    ax.set(xlabel="time before official start", ylabel="Brier (lower = more accurate)",
           title="Both exchanges sharpen toward start (joint constant sample)")
    ax.legend()
    fig.tight_layout(); fig.savefig("results/horizon_cross.png", dpi=130)
    print("saved results/horizon_cross.png")


if __name__ == "__main__":
    main()
