"""Is the MLB margin mispricing tradeable? (exploitability facet, contract level)

The autopsy showed Kalshi over-prices "win by 3+" (margin 3/4 cells) by ~2.5pts each
while under-pricing 1-2-run finishes by +8pts. Strategy: BUY NO on the >2.5 rung
(betting the game finishes close or the side loses), executed at the real NO ask
(1 - yes_bid), Kalshi taker fee included, settled on actual contract outcomes.

Thesis link: the moneyline market was unbeatable (efficient). If this derivative-
contract edge survives costs, crowd wisdom fails precisely where crowd attention
thins — and the over-priced "decisive win" contracts are a behavioral (lottery-like)
gambling fingerprint inside an otherwise efficient market.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FEE = lambda p: 0.07 * p * (1 - p)


def backtest(sub: pd.DataFrame, label: str, rng) -> None:
    sub = sub.dropna(subset=["yes_bid"])
    if len(sub) < 30:
        print(f"  {label:30} n={len(sub)} (too few)", flush=True)
        return
    p_no = 1 - sub["yes_bid"]
    cost = p_no + FEE(p_no)
    pnl = (1 - sub["won"]) - cost            # NO pays $1 when the YES side lost
    roi = pnl.sum() / cost.sum()
    idx = rng.integers(0, len(sub), (2000, len(sub)))
    r = pnl.values[idx].sum(1) / cost.values[idx].sum(1)
    lo, hi = np.percentile(r, [2.5, 97.5])
    verdict = "PROFITABLE" if lo > 0 else ("losing" if hi < 0 else "~0")
    print(f"  {label:30} n={len(sub):5,}  ROI={roi:+.2%}  95%CI=({lo:+.1%},{hi:+.1%})  {verdict}", flush=True)


def main():
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    mlb = sp[(sp.league == "MLB") & sp.won.notna()].copy()
    rng = np.random.default_rng(3)

    print("=== SELL 'MLB win by 3+' (buy NO on the rung), real quotes + fees ===", flush=True)
    for thr in (2.5, 3.5, 4.5):
        backtest(mlb[mlb.threshold == thr], f"NO on >{thr} (all)", rng)
    print("\nby price source (>2.5 rung):", flush=True)
    for src, g in mlb[mlb.threshold == 2.5].groupby("src"):
        backtest(g, f"NO on >2.5 [{src}]", rng)
    print("\ncontrol — BUY YES on >2.5 (the over-priced side; should lose):", flush=True)
    sub = mlb[mlb.threshold == 2.5].dropna(subset=["yes_ask"])
    cost = sub["yes_ask"] + FEE(sub["yes_ask"])
    pnl = sub["won"] - cost
    print(f"  n={len(sub):,}  ROI={pnl.sum()/cost.sum():+.2%}", flush=True)


if __name__ == "__main__":
    main()
