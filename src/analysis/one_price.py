"""Law of one price ACROSS venues: can you arb Kalshi against Polymarket?

Within-Kalshi ladders are already arbitrage-free (0.1%). The cross-venue
version is the market-integration question: same contract (home team wins),
two order books on two exchanges — do the books ever cross?

Executable crossing (per $1 contract, home YES token on both venues):
  route A: buy Kalshi at ask, sell Polymarket at bid  -> profit = poly_bid - kalshi_ask
  route B: buy Polymarket at ask, sell Kalshi at bid  -> profit = kalshi_bid - poly_ask
Taker fees: Kalshi 0.07*p(1-p) per side; Polymarket 0.03*p(1-p) (post 2026-03-30).

Data: OddPool archived Polymarket books (~start, median gap 0.1 min) matched to
Kalshi bid/ask at official start (kalshi_hist_prices raw quotes). Timing gap
minutes at most — noted as a caveat, biases TOWARD finding spurious crossings.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def main():
    ps = pd.read_csv("data/processed/poly_spreads.csv").dropna(subset=["poly_bid", "poly_ask"])
    k = pd.read_csv("data/processed/kalshi_hist_prices.csv")[
        ["game_id", "league", "k_yes_bid1", "k_yes_ask1", "k_src1"]]
    d = ps.merge(k, on="game_id", suffixes=("", "_k")).dropna(
        subset=["k_yes_bid1", "k_yes_ask1"])
    print(f"games with both venues' executable books: {len(d):,} "
          f"({dict(d.groupby('league').size())})", flush=True)

    mid_k = (d.k_yes_bid1 + d.k_yes_ask1) / 2
    mid_p = (d.poly_bid + d.poly_ask) / 2
    print(f"mid-price gap |Kalshi-Poly|: median={np.abs(mid_k-mid_p).median()*100:.2f}pts  "
          f"mean={np.abs(mid_k-mid_p).mean()*100:.2f}pts  max={np.abs(mid_k-mid_p).max()*100:.2f}pts", flush=True)

    fee_k = 0.07 * mid_k * (1 - mid_k)
    fee_p = 0.03 * mid_p * (1 - mid_p)
    a = d.poly_bid - d.k_yes_ask1          # buy Kalshi, sell Poly
    b = d.k_yes_bid1 - d.poly_ask          # buy Poly, sell Kalshi
    gross = np.maximum(a, b)
    net = np.maximum(a - fee_k - fee_p, b - fee_k - fee_p)
    print(f"\nbest-route GROSS crossing: positive in {(gross > 0).mean():.1%} of games "
          f"(median {gross.median()*100:+.2f}pts)", flush=True)
    print(f"best-route NET-of-fees:    positive in {(net > 0).mean():.1%} of games "
          f"(median {net.median()*100:+.2f}pts)", flush=True)
    pos = d[net > 0]
    if len(pos):
        print(f"  net-positive cases: {len(pos)} "
              f"(max {net.max()*100:.2f}pts) — inspect for timing-gap artifacts:", flush=True)
        for r, nv in zip(pos.itertuples(index=False), net[net > 0]):
            print(f"    {r.league} {r.game_id}: K {r.k_yes_bid1:.2f}/{r.k_yes_ask1:.2f} "
                  f"({r.k_src1}) vs P {r.poly_bid:.2f}/{r.poly_ask:.2f}  net={nv*100:+.2f}pts", flush=True)
    print("\n  ~0% net crossings = the two exchanges are one integrated market at the", flush=True)
    print("  quote level: the law of one price holds across venues, not just within.", flush=True)


if __name__ == "__main__":
    main()
