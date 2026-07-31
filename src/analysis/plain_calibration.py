"""The thesis as one table: teams priced X% win X% of the time — everywhere.

For every price level (10-point bands centered on 10%..90%), on the same
5,3xx games priced by all three sources: how many teams were priced there,
how often they actually won, the gap in points with a Wilson 95% CI, and the
plainest possible economics — what $1 staked at that price returned gross
(win_rate / price; 1.00 = perfectly fair, before fees/vig).

Both sides of every game count (a 40% team and its 60% opponent are separate
rows in separate bands). Footnote: in the 50% band both sides of one game can
land together, so that row's effective sample is slightly smaller than n.
This is the reader-facing version of Layer 1 — the formal machinery (slopes,
ECE, CORP, TOST) proves what this table shows.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.three_way import SRC, COLOR, load
from src.analysis.compare import stacked

CENTERS = np.arange(0.10, 0.91, 0.10)
HALF = 0.05


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    hw = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return mid - hw, mid + hw


def table(p, y):
    rows = []
    for c in CENTERS:
        m = (p >= c - HALF) & (p < c + HALF)
        n = int(m.sum())
        if n == 0:
            continue
        obs = y[m].mean()
        said = p[m].mean()
        lo, hi = wilson(y[m].sum(), n)
        rows.append({"band": f"{c*100:.0f}%", "n": n, "said": said, "obs": obs,
                     "gap_pts": (obs - said) * 100, "ci_lo": lo, "ci_hi": hi,
                     "dollar": obs / said})
    return pd.DataFrame(rows)


def main():
    d = load()
    print(f"same {len(d):,} games, all three sources; both sides = "
          f"{2*len(d):,} priced teams\n", flush=True)

    tabs = {}
    for name, (c1, c2) in SRC.items():
        p, y = stacked(d, c1, c2)
        t = table(np.asarray(p), np.asarray(y))
        tabs[name] = t
        print(f"=== {name}: teams priced X% — how often did they win? ===", flush=True)
        print(f"  {'priced':>7} {'teams':>7} {'avg price':>10} {'won':>7} "
              f"{'gap':>7} {'95% CI':>15} {'$1 returned':>12}", flush=True)
        for r in t.itertuples(index=False):
            star = " " if r.ci_lo <= r.said <= r.ci_hi else "*"
            print(f"  {r.band:>7} {r.n:>7,} {r.said*100:>9.1f}% {r.obs*100:>6.1f}% "
                  f"{r.gap_pts:>+6.1f}p {r.ci_lo*100:>6.1f}-{r.ci_hi*100:<5.1f}% "
                  f"${r.dollar:>10.2f}{star}", flush=True)
        n_out = sum(1 for r in t.itertuples() if not (r.ci_lo <= r.said <= r.ci_hi))
        print(f"  bands where the stated price falls outside the 95% CI: "
              f"{n_out}/{len(t)}\n", flush=True)

    print("=== side by side: % of teams that won, by stated price ===", flush=True)
    print(f"  {'priced':>7} " + "".join(f"{s:>12}" for s in SRC) + f" {'(n range)':>14}", flush=True)
    for i, c in enumerate(CENTERS):
        band = f"{c*100:.0f}%"
        vals, ns = [], []
        for s in SRC:
            row = tabs[s][tabs[s].band == band]
            vals.append(f"{row.obs.iloc[0]*100:>11.1f}%" if len(row) else f"{'—':>12}")
            ns.append(int(row.n.iloc[0]) if len(row) else 0)
        print(f"  {band:>7} " + "".join(vals) + f"  {min(ns):>6,}-{max(ns):,}", flush=True)
    print("\n  (50% band note: both sides of a near-coin-flip game can land in the", flush=True)
    print("   same band, so its effective sample is slightly below n.)", flush=True)

    fig, ax = plt.subplots(figsize=(8.5, 6))
    for name in SRC:
        t = tabs[name]
        ax.errorbar(t.said * 100, t.obs * 100,
                    yerr=[(t.obs - t.ci_lo) * 100, (t.ci_hi - t.obs) * 100],
                    fmt="o-", ms=5, capsize=3, color=COLOR[name], label=name)
    ax.plot([0, 100], [0, 100], "--", color="0.4", lw=1, label="perfect (said = won)")
    ax.set(xlabel="stated price (implied win probability, %)",
           ylabel="share of teams that actually won (%)",
           title=f"Teams priced X% win X% of the time — at all three institutions\n"
                 f"(same {len(d):,} games; {2*len(d):,} priced teams)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig("results/plain_calibration.png", dpi=130)
    print("\nsaved results/plain_calibration.png", flush=True)


if __name__ == "__main__":
    main()
