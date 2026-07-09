"""Multi-horizon calibration: does the market sharpen as the game approaches?

Forecasting-tool signature: Brier/ECE improve monotonically toward tip-off as
information (lineups, injuries, weather, money) arrives. Gambling-noise signature:
flat or erratic accuracy. Home-side Kalshi price at each horizon vs actual outcome.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.compare import brier, ece
from src.analysis.decomposition import murphy

HORIZONS_MIN = [24 * 60, 12 * 60, 6 * 60, 3 * 60, 60, 15, 0]
LABEL = {1440: "24h", 720: "12h", 360: "6h", 180: "3h", 60: "1h", 15: "15m", 0: "start"}


def main(path="data/processed/kalshi_horizons.csv"):
    d = pd.read_csv(path)
    print(f"games: {len(d):,} | median trades/game: {int(d.n_trades.median())} "
          f"| median lookback: {d.earliest_min.median()/60:.1f}h", flush=True)

    # constant-sample comparison: only games priced at EVERY horizon
    cols = [f"p_h{h}" for h in HORIZONS_MIN]
    full = d.dropna(subset=cols)
    print(f"games with a price at ALL horizons (constant sample): {len(full):,}\n", flush=True)

    print(f"{'horizon':>8} {'n(all)':>7} {'Brier':>8} {'ECE':>8} {'resol':>7}   [constant sample: Brier]", flush=True)
    rows = []
    for h in HORIZONS_MIN:
        c = f"p_h{h}"
        sub = d.dropna(subset=[c])
        y, p = sub["home_won"].values, sub[c].values
        m = murphy(p, y)
        bc = brier(full[c], full["home_won"].values)
        rows.append({"h": h, "n": len(sub), "brier": m["brier"], "ece": ece(p, y),
                     "res": m["resolution"], "brier_const": bc})
        print(f"{LABEL[h]:>8} {len(sub):>7,} {m['brier']:>8.4f} {ece(p,y):>8.4f} "
              f"{m['resolution']*1000:>7.1f}   {bc:.4f}", flush=True)
    t = pd.DataFrame(rows)

    # how much do prices move in the final day?
    mv = (full["p_h0"] - full["p_h1440"]).abs()
    print(f"\nmean |Δprice| from 24h -> start: {mv.mean()*100:.1f} pts "
          f"(median {mv.median()*100:.1f}); moves >5pts: {(mv>0.05).mean():.1%} of games", flush=True)

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    x = np.arange(len(HORIZONS_MIN))
    ax.plot(x, t["brier_const"], "o-", color="tab:blue", label=f"Brier (constant sample, n={len(full):,})")
    ax2 = ax.twinx()
    ece_const = [ece(full[f"p_h{h}"].values, full["home_won"].values) for h in HORIZONS_MIN]
    ax2.plot(x, ece_const, "s--", color="tab:red", alpha=0.7, label="ECE")
    ax.set_xticks(x, [LABEL[h] for h in HORIZONS_MIN])
    ax.set(xlabel="time before official start", ylabel="Brier (lower = more accurate)",
           title="Does the market sharpen toward tip-off? (Kalshi, home side)")
    ax2.set_ylabel("ECE (calibration error)", color="tab:red")
    lines = ax.get_lines() + ax2.get_lines()
    ax.legend(lines, [l.get_label() for l in lines], loc="upper right")
    fig.tight_layout(); fig.savefig("results/horizon_calibration.png", dpi=130)
    print("saved results/horizon_calibration.png", flush=True)


if __name__ == "__main__":
    main()
