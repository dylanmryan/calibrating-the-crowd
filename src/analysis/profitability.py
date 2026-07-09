"""Economic significance: can Kalshi's measured mispricing actually be traded?

Strategy: treat the sportsbook's de-vigged consensus as fair value. Whenever a
Kalshi contract's ASK is below fair value minus fees (positive expected value),
buy it. Execution is honest: real ask prices (stored raw quotes), Kalshi's actual
trading fee (0.07 * P * (1-P)), realized game outcomes.

Baselines show the ordinary gambler's experience: bet every favorite / every
longshot / everything -> expected loss ~ half-spread + fee.

If no strategy clears costs, the market is efficient within transaction costs:
participants pay a usage cost, but there is no exploitable inefficiency —
the sharpest operational answer to "is this gambling?".
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FEE = lambda p: 0.07 * p * (1 - p)  # Kalshi taker fee per contract (dollars)


def load():
    m = pd.read_csv("data/processed/games_master.csv")
    m = m[m["outcome"].notna() & ~m["outcome_disagree"].fillna(False)]
    m = m[m["book_p1"].notna() & m["kalshi_p1"].notna()]
    k = pd.read_csv("data/processed/kalshi_hist_prices.csv")[
        ["game_id", "k_yes_bid1", "k_yes_ask1", "k_yes_bid2", "k_yes_ask2"]]
    d = m.merge(k, on="game_id", how="left")
    rows = []
    for r in d.itertuples(index=False):
        for side, ask, bid, fair, won in (
                (1, r.k_yes_ask1, r.k_yes_bid1, r.book_p1, int(r.outcome == 1)),
                (2, r.k_yes_ask2, r.k_yes_bid2, r.book_p2, int(r.outcome == 2))):
            rows.append({"game_id": r.game_id, "league": r.league, "side": side,
                         "ask": ask, "bid": bid, "fair": fair, "won": won,
                         "is_fav": fair > 0.5, "is_home": side == 1})
    return pd.DataFrame(rows)


def roi(bets: pd.DataFrame):
    """Per-contract: pay ask+fee, receive 1 if won. Returns (roi, total_bets)."""
    cost = bets["ask"] + FEE(bets["ask"])
    pnl = bets["won"] - cost
    return float(pnl.sum() / cost.sum()), len(bets)


def boot_ci(bets, n=2000, seed=7):
    rng = np.random.default_rng(seed)
    cost = (bets["ask"] + FEE(bets["ask"])).values
    pnl = (bets["won"] - cost).values
    idx = rng.integers(0, len(bets), (n, len(bets)))
    r = pnl[idx].sum(1) / cost[idx].sum(1)
    return np.percentile(r, [2.5, 97.5])


def main():
    d = load().dropna(subset=["ask", "bid"])
    d = d[(d["ask"] > 0) & (d["ask"] < 1)]
    print(f"tradeable contract-sides with real quotes: {len(d):,} "
          f"({d.game_id.nunique():,} games)\n", flush=True)

    print("=== baselines: the ordinary gambler on Kalshi ===", flush=True)
    for name, sub in [("bet EVERYTHING", d), ("bet favorites", d[d.is_fav]),
                      ("bet longshots", d[~d.is_fav]), ("bet home teams", d[d.is_home])]:
        r, n = roi(sub)
        print(f"  {name:16} n={n:6,}  ROI={r:+.2%}", flush=True)

    print("\n=== edge strategy: buy Kalshi when ask < book fair value - fee ===", flush=True)
    d["edge"] = d["fair"] - (d["ask"] + FEE(d["ask"]))
    print(f"  {'min edge':>9} {'n bets':>7} {'gross ROI':>10}  95% CI", flush=True)
    results = []
    for thr in (0.00, 0.01, 0.02, 0.03, 0.05):
        sub = d[d["edge"] > thr]
        if len(sub) < 20:
            print(f"  {thr:>9.0%} {len(sub):>7,}   (too few)", flush=True)
            continue
        r, n = roi(sub)
        lo, hi = boot_ci(sub)
        results.append((thr, r, lo, hi, n))
        sig = "PROFITABLE" if lo > 0 else ("losing" if hi < 0 else "≈ zero")
        print(f"  {thr:>9.0%} {n:>7,} {r:>+10.2%}  ({lo:+.1%},{hi:+.1%})  {sig}", flush=True)

    print("\n=== mechanism: which direction does Kalshi err vs the book? ===", flush=True)
    d["kalshi_mid"] = (d["ask"] + d["bid"]) / 2
    d["dev"] = d["kalshi_mid"] - d["fair"]  # + = Kalshi prices side ABOVE book fair
    div = d[d["dev"].abs() > 0.02]
    print(f"  contracts where Kalshi deviates >2pts from book: {len(div):,} ({len(div)/len(d):.1%})", flush=True)
    for name, sub in [("favorites", d[d.is_fav]), ("longshots", d[~d.is_fav]),
                      ("home sides", d[d.is_home]), ("away sides", d[~d.is_home])]:
        print(f"  mean deviation on {name:10}: {sub.dev.mean()*100:+.2f} pts "
              f"(Kalshi {'richer' if sub.dev.mean()>0 else 'cheaper'})", flush=True)
    print("\n  by league (mean deviation on favorites, pts):", flush=True)
    for lg, g in d[d.is_fav].groupby("league"):
        print(f"    {lg:6} {g.dev.mean()*100:+.2f}", flush=True)

    if results:
        fig, ax = plt.subplots(figsize=(8, 5))
        thrs = [x[0] for x in results]
        ax.axhline(0, color="k", lw=1)
        ax.errorbar(thrs, [x[1] for x in results],
                    yerr=[[x[1] - x[2] for x in results], [x[3] - x[1] for x in results]],
                    fmt="o-", color="tab:red", capsize=4, label="edge strategy ROI (95% CI)")
        base, _ = roi(d)
        ax.axhline(base, color="0.5", ls=":", label=f"bet-everything baseline ({base:+.1%})")
        ax.set(xlabel="minimum edge required (book fair − Kalshi ask − fee)",
               ylabel="realized ROI per $ staked",
               title="Can the Kalshi–book gap be traded profitably?")
        ax.legend()
        fig.tight_layout(); fig.savefig("results/profitability.png", dpi=130)
        print("\nsaved results/profitability.png", flush=True)


if __name__ == "__main__":
    main()
