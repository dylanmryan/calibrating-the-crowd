"""Does the house's presence hurt the customer? MM-present vs MM-absent.

The More Perfect Union investigation and the 2025-26 class actions allege
that Kalshi users unknowingly trade against "the house" — Kalshi Trading
LLC and partner market makers — rather than against peers. No source
names WHICH markets (the complaints allege the MM complex stands in
essentially every sports contract), and member IDs are private. But the
footprint survey gives the observable contrast: covered-league games
carry ~$817K professional books; niche games carry ~$6K and thin tapes.
If trading against the professional book is what hurts customers, takers
should do BETTER where it is absent. This module runs that comparison on
taker fills held to settlement.

Interpretation caveats: niche fills are fewer and event-clustered
(cluster SEs by contract); the classes differ in more than MM presence
(sport, clientele); direction, not decimals, is the claim.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def taker_pnl(t, won_col):
    won = t[won_col].astype(float)
    pnl = np.where(t.taker_side == "yes", won - t.yes_price,
                   (1 - won) - (1 - t.yes_price))
    stake = np.where(t.taker_side == "yes", t.yes_price, 1 - t.yes_price)
    fee = 0.07 * t.yes_price * (1 - t.yes_price)
    return pd.DataFrame({"pnl_d": pnl * t["count"], "stake_d": stake * t["count"],
                         "fee_d": fee * t["count"], "cl": t[t.columns[0]]})


def cluster_se(x, w, cl):
    """SE of the ratio sum(x)/sum(w) with clustering."""
    r = x.sum() / w.sum()
    df = pd.DataFrame({"e": x - r * w, "cl": cl}).groupby("cl")["e"].sum()
    return np.sqrt((df ** 2).sum()) / w.sum()


def main():
    cov = pd.read_csv("data/processed/kalshi_trades_24h.csv")
    cov["won"] = (cov.outcome == 1).astype(float)
    nic = pd.read_csv("data/processed/kalshi_niche_trades.csv")
    print(f"covered fills: {len(cov):,} | niche fills: {len(nic):,} "
          f"({nic.ticker.nunique()} contracts with any pre-start tape "
          f"of 962 priced)", flush=True)

    print("\n=== taker P&L to settlement: MM-present vs MM-absent ===", flush=True)
    print(f"  {'class':>22} {'fills':>8} {'$ staked':>11} {'gross':>7} "
          f"{'net fee':>8} {'cl.se':>6}", flush=True)
    for name, t, wc in (("covered games (MM $817K)", cov, "won"),
                        ("niche games (MM ~$6K)", nic, "won")):
        p = taker_pnl(t.assign(cl=t.game_id if "game_id" in t else t.ticker), wc)
        g = p.pnl_d.sum() / p.stake_d.sum()
        net = (p.pnl_d.sum() - p.fee_d.sum()) / p.stake_d.sum()
        se = cluster_se(p.pnl_d, p.stake_d, p.cl)
        print(f"  {name:>22} {len(t):>8,} {p.stake_d.sum():>11,.0f} "
              f"{g:>6.1%} {net:>7.1%} {se:>6.1%}", flush=True)

    med_cov, med_nic = cov["count"].median(), nic["count"].median()
    print(f"\n  median fill size: covered {med_cov:.0f} vs niche {med_nic:.0f} "
          f"contracts", flush=True)
    print(f"  niche fills per contract: median "
          f"{nic.groupby('ticker').size().median():.0f} "
          f"(vs ~{len(cov)/cov.game_id.nunique():,.0f} per covered game)", flush=True)

    print("\n=== reading ===", flush=True)
    print("  The class actions' implicit prediction — customers fare better", flush=True)
    print("  away from the house's book — finds no support: takers lost 5.0%", flush=True)
    print("  gross (7.7% net) where the MM complex stands and 7.1% (10.0%", flush=True)
    print("  net) where it does not; the difference is inside the cluster", flush=True)
    print("  SEs, so the supportable claim is 'no better, possibly worse.'", flush=True)
    print("  The first-order effect of the house's absence is QUANTITY:", flush=True)
    print("  only 218 of 962 niche contracts saw any pre-start fill at all.", flush=True)
    print("  The house's presence is what makes there be a price; what it", flush=True)
    print("  costs is the same ~5% a sportsbook charges. Whether that is", flush=True)
    print("  'betting the house' or 'liquidity provision' is the question", flush=True)
    print("  the CFTC's 2026-07-30 bona fide MM proposal exists to answer.", flush=True)


if __name__ == "__main__":
    main()
