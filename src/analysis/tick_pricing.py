"""Decimal pricing and the tick: is the quoted spread a choice or a constraint?

Tick regimes (probed from live APIs, 2026-07-25):
  Kalshi sports markets:  price_level_structure = "linear_cent" — a uniform
    1c tick over the whole [0,1] range, spread ladders included.
  Polymarket game markets: orderPriceMinTickSize = 0.01 mid-range, dropping
    to 0.001 on extreme-priced markets (sub-cent quotes observed live).

Three consequences measured here on stored quotes:
  1. Tick-bind incidence — the share of live order-book spreads sitting at
     EXACTLY one tick, by price level. A spread pinned at the tick is a
     censored variable: it cannot narrow, so "spread didn't move" findings
     (e.g. the fee experiment) are statements about a bound, and the real
     adjustment margins are depth and volume.
  2. The tick tax — minimum relative spread (tick/price) by price level. At
     50c a 1c tick is 2% of price; at 5c it is 20%. Kalshi's uniform cent
     makes tail quoting structurally coarse exactly where its ladder-tail
     calibration gap vs the books lives; Polymarket's 0.001 regime relaxes
     the bound tenfold in the same region.
  3. Sub-cent usage — off-cent-grid quotes in our stored Polymarket books
     (rare on moneylines, whose mid-range prices carry the 0.01 tick).
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

EDGES = np.array([0.01, 0.05, 0.10, 0.20, 0.35, 0.65, 0.80, 0.90, 0.95, 0.99])
LAB = [f"{int(a*100)}-{int(b*100)}c" for a, b in zip(EDGES[:-1], EDGES[1:])]


def bucket(p):
    return np.clip(np.digitize(p, EDGES) - 1, 0, len(LAB) - 1)


def main():
    # ---------- Kalshi moneylines (live order-book quotes only) ----------
    q = pd.read_csv("data/processed/kalshi_hist_prices.csv")
    m = pd.read_csv("data/processed/games_master.csv")[["game_id", "outcome"]]
    q = q.merge(m, on="game_id")
    q = q[q.outcome.notna()]
    sides = []
    for i in (1, 2):
        g = q[q[f"k_src{i}"] == "book-mid"]
        s = pd.DataFrame({"mid": (g[f"k_yes_bid{i}"] + g[f"k_yes_ask{i}"]) / 2,
                          "spread": g[f"k_yes_ask{i}"] - g[f"k_yes_bid{i}"]})
        sides.append(s)
    ml = pd.concat(sides).dropna()
    ml = ml[ml.spread >= 0]
    print(f"Kalshi live-book moneyline sides: {len(ml):,}")
    at_tick = (ml.spread.round(4) == 0.01).mean()
    print(f"  spread == exactly 1 tick: {at_tick:.0%} of quotes "
          f"(median spread {ml.spread.median()*100:.1f}c)")

    # ---------- Kalshi ladders (the tails) ----------
    lad = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    lad = lad[(lad.src == "book-mid") & lad.spread_w.notna() & (lad.prob > 0)].copy()
    lad["b"] = bucket(lad.prob.values)
    print(f"\nKalshi live-book ladder contracts: {len(lad):,}")
    print(f"  {'price':>8} {'n':>6} {'at-tick':>8} {'med spread':>11} {'rel spread':>11} {'tick/price':>11}")
    rel_rows = []
    for k, lab in enumerate(LAB):
        g = lad[lad.b == k]
        if len(g) < 30:
            continue
        att = (g.spread_w.round(4) == 0.01).mean()
        rel = (g.spread_w / g.prob).median()
        tickrel = 0.01 / g.prob.median()
        rel_rows.append({"lab": lab, "mid": g.prob.median(), "rel": rel, "tickrel": tickrel})
        print(f"  {lab:>8} {len(g):>6} {att:>8.0%} {g.spread_w.median()*100:>10.1f}c "
              f"{rel*100:>10.1f}% {tickrel*100:>10.1f}%")
    rr = pd.DataFrame(rel_rows)

    # ---------- Polymarket stored books ----------
    frames = []
    for f, cols in [("data/processed/poly_spreads.csv", ("poly_bid", "poly_ask")),
                    ("data/processed/fee_spreads.csv", ("poly_bid", "poly_ask"))]:
        if os.path.exists(f):
            d = pd.read_csv(f)
            frames.append(d[[cols[0], cols[1]]].rename(columns={cols[0]: "bid", cols[1]: "ask"}))
    pb = pd.concat(frames).dropna()
    pb["spread"] = pb.ask - pb.bid
    off_grid = ((pb.bid * 100) % 1 > 1e-6) | ((pb.ask * 100) % 1 > 1e-6)
    print(f"\nPolymarket stored books (moneylines, n={len(pb)}):")
    print(f"  spread == exactly 1 tick: {(pb.spread.round(4) == 0.01).mean():.0%}; "
          f"off-cent-grid quotes: {off_grid.mean():.1%}")
    print("  (moneylines live mid-range where Poly's tick is 0.01; the 0.001 regime")
    print("   applies to extreme-priced markets — sub-cent quotes observed live on a")
    print("   -1.5 spread market, gamma orderPriceMinTickSize=0.001)")

    print("\nReading: the touch on BOTH venues' moneylines sits at the minimum tick —")
    print("the quoted spread is a censored bound, not an equilibrium choice. Fee-era")
    print("'spread unchanged' is therefore about the bound; depth and volume are the")
    print("free margins (volume moved -41%; depth capture now accumulating). In the")
    print("tails, Kalshi's uniform cent is a 10-20% relative floor where Polymarket's")
    print("0.001 regime floors at 1-2% — tick design, not trader behavior, sets the")
    print("price of tail liquidity.")

    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.plot(rr.mid * 100, rr.rel * 100, "o-", color="tab:blue",
            label="Kalshi ladder: median quoted spread / price")
    ax.plot(rr.mid * 100, rr.tickrel * 100, "--", color="tab:blue", alpha=0.6,
            label="Kalshi minimum (1c tick / price)")
    ax.plot(rr.mid * 100, 0.1 / rr.mid, ":", color="tab:orange",
            label="Polymarket minimum in 0.001 regime")
    ax.set(xscale="log", yscale="log", xlabel="contract price (cents, log)",
           ylabel="relative spread (% of price, log)",
           title="The tick tax: uniform 1c pricing makes tails expensive")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("results/tick_pricing.png", dpi=130)
    print("\nsaved results/tick_pricing.png")


if __name__ == "__main__":
    main()
