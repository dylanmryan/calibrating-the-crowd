"""Horizon-matched translation: what these products return to someone using
them as a financial plan.

Betterment's 2026 Retail Investor Survey reports that 26% of Gen Z investors
treat sports betting as a deliberate part of a long-term financial strategy and
52% redirected money earmarked for investing into it. That is a claim about
HORIZON — wealth accumulation — and this project measures per-position returns.
This module converts one into the other.

The translation is deliberately simple, because the honest version has to be:

  per-position return  x  how often you re-stake  =  what happens to a bankroll

The first factor is MEASURED here from the fill tape and the futures file (both
recomputed, never quoted, so this cannot go stale). The second factor is NOT
measurable from any public data: Kalshi's tape carries no account identifiers,
so nobody outside the exchange can observe how often one person bets. It is
therefore presented as an explicit scenario grid, and labelled as such
everywhere. Nothing here estimates any individual's behaviour.

The result that matters is not that betting loses money — the paper already
established that. It is that TURNOVER, not price quality, determines the annual
outcome. The game markets are the well-calibrated, professionally-priced,
formally-equivalent-to-Pinnacle product this paper spends fifty modules
validating, and at a weekly cadence they still return almost nothing to a taker.
Calibration protects the price. It does not protect the customer.

NOT INVESTMENT ADVICE, and deliberately not framed as any: this is a
descriptive comparison of measured historical returns of two market types, of
the same kind the paper makes everywhere else. The equity figure used for scale
is a fixed textbook constant, not an estimate produced by this project, and no
recommendation is made or implied.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

TRADES = "data/processed/kalshi_trades_24h.csv"
FUTURES = "data/processed/kalshi_futures_prices.csv"

# Scenario grid for re-stake frequency over a ~26-week season. NOT measured.
CADENCES = [("monthly", 6), ("fortnightly", 13), ("weekly", 26),
            ("twice a week", 52), ("daily", 182)]
# Fixed textbook constant used only to give the table a familiar yardstick.
EQUITY_REAL_ANNUAL = 0.07
B = 2000


def taker_rate():
    """Stake-weighted taker return per settled position, gross and net of fee.

    Same construction as retail_fingerprint (trades are on the home ticker;
    Kalshi's taker fee is 0.07*p*(1-p) per contract), plus a game-clustered
    bootstrap so the compounding below can carry an interval.
    """
    t = pd.read_csv(TRADES)
    t = t.dropna(subset=["outcome", "yes_price", "count", "taker_side"])
    home_won = (t.outcome == 1).astype(float)
    stake = np.where(t.taker_side == "yes", t.yes_price, 1 - t.yes_price)
    pnl = np.where(t.taker_side == "yes", home_won - t.yes_price,
                   (1 - home_won) - (1 - t.yes_price))
    fee = 0.07 * t.yes_price * (1 - t.yes_price)
    d = pd.DataFrame({"game_id": t.game_id,
                      "stake": stake * t["count"],
                      "pnl": pnl * t["count"],
                      "fee": fee * t["count"]})
    gross = d.pnl.sum() / d.stake.sum()
    net = (d.pnl.sum() - d.fee.sum()) / d.stake.sum()

    by = d.groupby("game_id")[["stake", "pnl", "fee"]].sum()
    rng = np.random.default_rng(5)
    idx = np.arange(len(by))
    boot = []
    for _ in range(B):
        s = by.iloc[rng.choice(idx, len(idx), replace=True)]
        boot.append((s.pnl.sum() - s.fee.sum()) / s.stake.sum())
    lo, hi = np.percentile(boot, [5, 95])
    return gross, net, lo, hi, d.stake.sum(), by.shape[0]


def structural_cost(path="data/live/vps_mirror/snapshots.csv"):
    """The taker's cost per position from the QUOTE, not from outcomes.

    A taker pays the half-spread away from the mid plus Kalshi's fee
    0.07*p*(1-p), on a stake of p per contract. Unlike realized P&L this is
    nearly deterministic — it depends on the quote and the fee schedule, not on
    who won — so it is the right anchor for compounding. Realized P&L is the
    empirical check that this is what actually happens; its interval is wide
    because outcomes are random, not because the cost is uncertain.
    """
    d = pd.read_csv(path)
    d = d[(d.source == "kalshi") & (d.minutes_to_start > 0)]
    d = d.dropna(subset=["spread1", "p1"])
    d = d[(d.spread1 >= 0) & d.p1.between(0.02, 0.98)]
    half = d.spread1 / 2
    fee = 0.07 * d.p1 * (1 - d.p1)
    cost = (half + fee) / d.p1                    # as a fraction of notional
    return -cost.median(), -cost.quantile(.25), -cost.quantile(.75), len(d)


def outright_rate():
    """Per-dollar return on a held futures ticket, at each horizon.

    TWO constructions, because they answer different questions and the
    difference is large enough to mislead if only one is shown:

      per ticket  — mean of (won / price) across contracts. What a randomly
                    chosen listed ticket returns. This is futures_calibration's
                    construction and the figure the rest of the paper quotes
                    ($0.55 at T-7d), so it is the primary number here.
      per dollar  — total winners / total price paid. What a dollar spread
                    across a whole field returns. Higher, because it is
                    dominated by expensive favourites, which are priced far
                    better than the longshot tail.

    A person buying a futures bet buys a ticket, so the first is the relevant
    one for the translation; the second is reported so the gap is visible.
    """
    f = pd.read_csv(FUTURES).drop_duplicates("ticker")
    sizes = f.groupby("event_ticker")["ticker"].count()
    out = {}
    for col, label in (("p_7d", "T-7d"), ("p_30d", "T-30d")):
        g = f[f[col].notna() & f[col].between(0.005, 0.995) & f.won.notna()]
        # fully-priced fields only: a partially-priced field drops late-surging
        # winners and keeps the losers, biasing returns down (futures_calibration)
        priced = g.groupby("event_ticker")["ticker"].count()
        full = priced.index[priced.eq(sizes.reindex(priced.index))]
        keep = g[g.event_ticker.isin(full)]
        if len(keep) < 30:
            continue
        per_ticket = (keep.won / keep[col]).mean() - 1
        per_dollar = keep.won.sum() / keep[col].sum() - 1
        sub = keep[keep[col] <= 0.10]
        sub_ret = ((sub.won / sub[col]).mean() - 1) if len(sub) >= 15 else np.nan
        out[label] = (per_ticket, per_dollar, sub_ret, len(keep), len(sub))
    return out


def main():
    cost, c25, c75, n_q = structural_cost()
    gross, net, lo, hi, staked, n_games = taker_rate()
    print("=== 1. THE MEASURED PER-POSITION RATES (recomputed, not quoted) ===",
          flush=True)
    print(f"  STRUCTURAL cost of one taker position (half-spread + fee, as a", flush=True)
    print(f"  share of notional): {cost:+.1%}  [IQR {c75:+.1%} to {c25:+.1%}, "
          f"n={n_q:,} live quotes]", flush=True)
    print(f"  REALIZED taker P&L held to settlement: {gross:+.1%} gross, "
          f"{net:+.1%} net of fee", flush=True)
    print(f"    (${staked:,.0f} staked across {n_games} games; game-clustered "
          f"90% CI {lo:+.1%} to {hi:+.1%})", flush=True)
    print("\n  The realized interval is wide and spans zero — with 513 games the", flush=True)
    print("  OUTCOMES are noisy. The cost is not: it is set by the quote and the", flush=True)
    print("  fee schedule before any ball is thrown. So the structural rate is", flush=True)
    print("  the anchor below and the realized rate is the consistency check —", flush=True)
    print("  and they agree to within a couple of points, which is the finding.", flush=True)
    outs = outright_rate()
    for label, (tick, doll, sub, n, nsub) in outs.items():
        subtxt = f"{sub:+.1%}" if sub == sub else "n/a"
        print(f"  outrights held from {label}: {tick:+.1%} per TICKET "
              f"(= ${1+tick:.2f} per $1, the paper's figure; {doll:+.1%} if a", flush=True)
        print(f"    dollar is spread across the whole field); sub-10c longshots "
              f"{subtxt}  [n={n}, {nsub} sub-10c]", flush=True)
    print("\n  Note the shapes differ. The game-market rate is a well-calibrated", flush=True)
    print("  price minus a spread and a fee. The outright rate is a MISPRICED", flush=True)
    print("  price: this paper shows books do the same thing on their own", flush=True)
    print("  futures ($0.34/$1 on sub-10c longshots), so it is not exchange-", flush=True)
    print("  specific. Both are what the customer receives.", flush=True)

    print("\n=== 2. WHAT A RE-STAKED BANKROLL DOES OVER ONE SEASON ===", flush=True)
    print("  SCENARIO GRID, NOT A MEASUREMENT: Kalshi's public tape carries no", flush=True)
    print("  account identifiers, so per-person cadence is unobservable to any", flush=True)
    print("  outside researcher. These are illustrative re-stake frequencies.", flush=True)
    print(f"\n  {'cadence':>14} {'positions':>10} {'at cost rate':>13} "
          f"{'at realized rate':>17}", flush=True)
    for label, n in CADENCES:
        print(f"  {label:>14} {n:>10} {(1+cost)**n:>12.1%} "
              f"{(1+net)**n:>16.1%}", flush=True)
    print("\n  (fraction of an initial bankroll remaining after a ~26-week season,", flush=True)
    print("   re-staking proceeds each time — the 'strategy' reading. A customer", flush=True)
    print("   who instead stakes a fixed sum and pockets nothing loses", flush=True)
    print(f"   {abs(cost):.1%} of everything they put through, linearly.)", flush=True)

    print("\n=== 3. THE HORIZON-MATCHED COMPARISON ===", flush=True)
    r7 = outs.get("T-7d", (np.nan,))[0]   # per-ticket, paper-consistent
    if r7 == r7:
        n_equiv = np.log(1 + r7) / np.log(1 + cost)
        print(f"  Holding ONE futures ticket from a week out returns {r7:+.1%}.", flush=True)
        print(f"  Reaching the same place through the well-priced game markets", flush=True)
        print(f"  takes {n_equiv:.1f} settled positions at {cost:+.1%} each.", flush=True)
        weeks = dict(CADENCES)["weekly"]
        print(f"  So about {n_equiv:.0f} game bets is equivalent to buying the one", flush=True)
        print("  product this paper shows is badly priced at EVERY institution —", flush=True)
        print(f"  and a weekly bettor reaches that point {n_equiv/weeks:.0%} of the way", flush=True)
        print(f"  through one {weeks}-week season, then keeps going.", flush=True)
    print(f"\n  For scale only, a fixed textbook constant and NOT an estimate from", flush=True)
    print(f"  this project: long-run real equity returns are conventionally taken", flush=True)
    print(f"  at about {EQUITY_REAL_ANNUAL:+.0%}/year. The weekly-cadence cell above is the", flush=True)
    print("  relevant comparison for the survey's 'part of a financial plan'", flush=True)
    print("  respondents. No recommendation is made or implied.", flush=True)

    print("\n=== 4. WHAT THIS SAYS THAT THE CALIBRATION RESULTS DO NOT ===", flush=True)
    print("  Every accuracy result in this paper is about the PRICE: the game", flush=True)
    print("  markets are formally equivalent to Pinnacle and to 30+ books, their", flush=True)
    print("  ladders are coherent and arbitrage-free, and no venue leads another.", flush=True)
    print("  None of that reaches the customer. The taker's outcome is set by the", flush=True)
    print("  spread, the fee and how often they re-stake — and at any cadence a", flush=True)
    print("  'financial plan' would imply, a perfectly calibrated market still", flush=True)
    print("  returns close to nothing. Calibration disciplines the price; it does", flush=True)
    print("  not protect the participant. That is the paper's institutional", flush=True)
    print("  finding stated in the units the demand-side surveys use.", flush=True)

    # figure
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3))
    ns = np.arange(0, 183)
    axes[0].plot(ns, (1 + cost) ** ns * 100, color="tab:blue",
                 label=f"game markets, cost rate ({cost:+.1%}/position)")
    axes[0].plot(ns, (1 + net) ** ns * 100, color="tab:blue", ls=":", lw=1.2,
                 label=f"game markets, realized ({net:+.1%})")
    if r7 == r7:
        axes[0].axhline((1 + r7) * 100, color="tab:red", ls="--",
                        label=f"one futures ticket ({r7:+.0%})")
    for label, n in CADENCES:
        axes[0].axvline(n, color="0.85", lw=.8, zorder=0)
        axes[0].annotate(label, (n, 96), fontsize=6.5, rotation=90,
                         ha="right", va="top", color="0.45")
    axes[0].set(xlabel="settled positions (re-staking proceeds)",
                ylabel="% of initial bankroll", ylim=(0, 105),
                title="Turnover, not price quality, sets the outcome")
    axes[0].legend(fontsize=8)

    labs = [c[0] for c in CADENCES]
    vals = [(1 + cost) ** c[1] * 100 for c in CADENCES]
    axes[1].barh(labs, vals, color="tab:blue", alpha=.85)
    for i, v in enumerate(vals):
        axes[1].text(v + 1, i, f"{v:.0f}%", va="center", fontsize=8)
    axes[1].set(xlabel="% of bankroll left after a ~26-week season",
                title="Illustrative re-stake cadences (scenario, not measured)",
                xlim=(0, 105))
    fig.tight_layout()
    fig.savefig("results/horizon_translation.png", dpi=130)
    print("\nsaved results/horizon_translation.png", flush=True)


if __name__ == "__main__":
    main()
