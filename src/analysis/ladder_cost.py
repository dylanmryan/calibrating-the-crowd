"""Does the MLB ladder mispricing survive transaction costs?

The referee's question about the Kalshi-specific +8.4pt under-pricing of 1-2-run
margins: if the books price it correctly, why hasn't it been traded away? This is
an EFFICIENCY test, not a strategy: a bias that clears executable costs is a
genuine inefficiency (bounded arbitrage / thin books); one inside the cost band
is "harbored" the way books harbor biases inside their vig.

Trade construction: the mispricing implies Kalshi's P(win by >2.5) is too HIGH,
so the natural position is SELL YES at the bid on threshold-2.5 contracts
(equivalently backing "loses or wins by 1-2"). Costs: cross the spread (sell at
bid, value at mid) + Kalshi taker fee 0.07*P*(1-P) at execution price P.
Per contract shorted at bid b:  profit = b*1{no} - (1-b)*1{yes} - fee,
ROI on collateral (1-b). NBA is the control (no cell bias found there).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def roi_table(sp, label):
    print(f"\n  --- {label} ---", flush=True)
    print(f"  {'threshold':>10} {'n':>7} {'sell-YES ROI':>13} {'z(date-clust)':>14}", flush=True)
    for t, g in sp.groupby("threshold"):
        if len(g) < 200 or t > 4.5:
            continue
        b = g.yes_bid.values
        fee = 0.07 * b * (1 - b)
        won_yes = g.won.values.astype(float)
        profit = b * (1 - won_yes) - (1 - b) * won_yes - fee
        roi = profit / (1 - b)
        # date-clustered SE of the mean ROI
        cl = pd.DataFrame({"r": roi, "c": g.date.values}).groupby("c")["r"]
        means, sizes = cl.mean(), cl.size()
        mu = roi.mean()
        se = np.sqrt(((sizes * (means - mu)) ** 2).sum()) / len(roi)
        print(f"  {t:>10} {len(g):>7,} {mu*100:>+12.2f}% {mu/se:>+14.2f}", flush=True)


def main():
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    sp = sp.dropna(subset=["yes_bid", "yes_ask", "won"])
    sp = sp[(sp.yes_bid > 0) & (sp.yes_ask < 1) & (sp.yes_ask > sp.yes_bid - 1e-9)]
    sp["date"] = pd.to_datetime(sp["start_utc"], utc=True, format="ISO8601").dt.date
    print(f"contracts with executable quotes: {len(sp):,}", flush=True)

    for lg in ("MLB", "NBA"):
        roi_table(sp[sp.league == lg], f"{lg} — all quote sources")
    # live-book-only robustness: reconstructed quotes may flatter or damn the trade
    for lg in ("MLB",):
        roi_table(sp[(sp.league == lg) & (sp.src == "book-mid")], f"{lg} — live book quotes only")

    print("\n  interpretation: positive & significant => real inefficiency persists net of", flush=True)
    print("  costs (thin-market bounded arbitrage); negative/zero => bias harbored inside", flush=True)
    print("  the cost band, exactly as books harbor biases inside their vig.", flush=True)


if __name__ == "__main__":
    main()
