"""Per-league equivalence (TOST) + sharpness: formalizing the dead heat's breadth.

Turns "per-league winners alternate in the 4th decimal" into a formal statement:
for every league and source pair, the date-clustered 90% CI of the Brier
differential gives delta_min = the smallest TOST margin at which the pair is
formally equivalent (equivalent at delta=1e-3 iff the CI sits inside +-1e-3).
Sharpness (mean p(1-p), lower = sharper) presents "equally informative, not just
equally calibrated" explicitly — calibration can be gamed by hedging to the base
rate; identical sharpness + identical Brier cannot.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.three_way import SRC, load
from src.analysis.compare import brier
from src.analysis.rigor import cluster_dm
from src.analysis.decomposition import murphy

DELTA = 1e-3
PAIRS = [("Kalshi", "Polymarket"), ("Kalshi", "Sportsbook"), ("Polymarket", "Sportsbook")]


def tost_row(d, a, b):
    y = d.home_won.values
    pa, pb = d[SRC[a][0]].values, d[SRC[b][0]].values
    dbar, se, z, p, (lo, hi) = cluster_dm(pa, pb, y, d.date.values)
    dmin = max(abs(lo), abs(hi))
    return dbar, lo, hi, dmin, ("EQUIV" if dmin <= DELTA else "wide-CI")


def main():
    d = load()
    d["date"] = d.start_utc.astype(str).str[:10]
    print(f"three-way clean games: {len(d):,}\n")

    print(f"=== per-league TOST (home-side Brier differential ×1000, 90% CI, δ=1.0e-3) ===")
    print(f"{'league':>7} {'n':>6}  {'pair':22} {'ΔBrier':>8} {'90% CI':>18} {'δ_min':>7}  verdict")
    for lg, g in [("ALL", d)] + sorted(d.groupby("league"), key=lambda t: -len(t[1])):
        for a, b in PAIRS:
            dbar, lo, hi, dmin, verdict = tost_row(g, a, b)
            print(f"{lg:>7} {len(g):>6}  {a[:4]+' vs '+b:22} {dbar*1000:>+8.2f} "
                  f"[{lo*1000:>+6.2f},{hi*1000:>+6.2f}]    {dmin*1000:>5.2f}  {verdict}")
        print()

    print("=== sharpness: mean p(1-p), lower = sharper (home side) ===")
    print(f"{'league':>7} {'n':>6}" + "".join(f" {s:>11}" for s in SRC) + "   spread(max-min)")
    for lg, g in [("ALL", d)] + sorted(d.groupby("league"), key=lambda t: -len(t[1])):
        sh = {s: (g[c1] * (1 - g[c1])).mean() for s, (c1, _) in SRC.items()}
        vals = "".join(f" {sh[s]:>11.4f}" for s in SRC)
        print(f"{lg:>7} {len(g):>6}{vals}   {max(sh.values())-min(sh.values()):.4f}")

    print("\n=== resolution (×1000, higher = more informative; same-game comparison) ===")
    y = d.home_won.values
    for s, (c1, _) in SRC.items():
        m = murphy(d[c1].values, y)
        print(f"  {s:11} resolution={m['resolution']*1000:6.1f}  brier={brier(d[c1].values, y):.4f}")


if __name__ == "__main__":
    main()
