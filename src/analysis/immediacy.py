"""The price of immediacy: what does it cost to trade size, and at what size
does the exchange stop being free?

Every cost number in this project so far has been a TOUCH number — the quoted
spread plus the fee, i.e. what a one-contract taker pays. That is the right
number for the median customer (the fills tape puts the median order at 30
contracts, about $14 at stake) but it says nothing about the market's capacity.
The VPS collector has recorded order-book depth on both exchanges every snapshot
since 2026-07-25: size at the touch and size resting within 5c on each side.
That is enough for a two-anchor execution curve.

Cost model for demanding Q units immediately (buying the home side):
  Q <= touch size          -> you pay the half-spread, nothing more
  touch < Q <= depth(5c)   -> the remainder fills into the 5c band; assume the
                              resting size is uniform across the band, so those
                              units average 2.5c x (fraction of the band eaten)
                              above the touch
  Q > depth(5c)            -> beyond what the capture measures; reported as
                              censored rather than extrapolated
Units are $1-payout contracts on Kalshi and $1-payout shares on Polymarket, so
notional and cost percentages are directly comparable.

Reported as cents versus the mid, and as a percentage of notional, so it lines
up with the -4.2% taker figure and the -7.7% realized taker P&L.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DEPTH_ERA = "2026-07-25"        # depth capture deployed
BAND = 0.05                     # the captured depth band, in dollars
SIZES = [10, 100, 1_000, 10_000, 50_000, 200_000]
RETAIL = 30                     # median fill size from the trades tape


def load(path="data/live/vps_mirror/snapshots.csv"):
    d = pd.read_csv(path)
    d["ts"] = pd.to_datetime(d.snapshot_utc, utc=True, format="ISO8601")
    d = d[(d.ts >= pd.Timestamp(DEPTH_ERA, tz="UTC")) & (d.minutes_to_start > 0)]
    d = d[d.source.isin(["kalshi", "polymarket"])]
    d = d.dropna(subset=["askq1", "d5ask1", "spread1"])
    # a book that is crossed or has no size is not a quote
    d = d[(d.askq1 > 0) & (d.d5ask1 >= d.askq1) & (d.spread1 >= 0)]
    return d


def cost_cents(q, touch, depth, spread):
    """Average cost per unit versus the mid, in cents, for an immediate size q.

    NaN where q exceeds the measured 5c band (censored, not extrapolated).
    """
    half = spread / 2 * 100
    extra = np.where(
        q <= touch, 0.0,
        np.where(q <= depth,
                 # units beyond the touch average halfway into the eaten band
                 (q - touch) / np.maximum(q, 1) *
                 (BAND * 100) * ((q - touch) / np.maximum(depth - touch, 1e-9)) / 2,
                 np.nan))
    return half + extra


def curve(d, label_col=None):
    rows = []
    for venue, g in d.groupby("source"):
        for q in SIZES:
            c = cost_cents(q, g.askq1.to_numpy(), g.d5ask1.to_numpy(),
                           g.spread1.to_numpy())
            feasible = np.isfinite(c)
            med = np.nanmedian(c) if feasible.any() else np.nan
            # cost as a share of notional: a unit costs about `price` dollars
            px = g.p1.to_numpy()
            pct = np.nanmedian(c / 100 / np.clip(px, 0.02, 0.98)) * 100
            rows.append({"venue": venue, "size": q,
                         "feasible%": feasible.mean() * 100,
                         "cost_cents": med, "cost_pct_notional": pct})
    return pd.DataFrame(rows)


def main():
    d = load()
    print(f"depth panel from {DEPTH_ERA}: {len(d):,} book snapshots, "
          f"{d.game_id.nunique()} games, leagues "
          f"{d.league.value_counts().to_dict()}", flush=True)

    print("\n=== 1. WHAT STANDS THERE (median resting size, home side) ===", flush=True)
    print(f"  {'venue':12} {'touch bid':>11} {'touch ask':>11} {'within 5c bid':>14} "
          f"{'within 5c ask':>14} {'spread':>8}", flush=True)
    for venue, g in d.groupby("source"):
        print(f"  {venue:12} {g.bidq1.median():>11,.0f} {g.askq1.median():>11,.0f} "
              f"{g.d5bid1.median():>14,.0f} {g.d5ask1.median():>14,.0f} "
              f"{g.spread1.median()*100:>7.1f}c", flush=True)
    print("  (Kalshi units are $1 contracts, Polymarket units are $1 shares)", flush=True)

    print("\n=== 2. THE IMMEDIACY CURVE (median cost vs mid, home side) ===", flush=True)
    c = curve(d)
    print(f"  {'size (units)':>13} " +
          " ".join(f"{v:>26}" for v in sorted(d.source.unique())), flush=True)
    for q in SIZES:
        cells = []
        for venue in sorted(d.source.unique()):
            r = c[(c.venue == venue) & (c["size"] == q)].iloc[0]
            if not np.isfinite(r.cost_cents):
                cells.append(f"{'beyond 5c band':>26}")
            else:
                cells.append(f"{r.cost_cents:>8.2f}c ({r.cost_pct_notional:>4.1f}% "
                             f"| {r['feasible%']:>3.0f}% fill)")
        print(f"  {q:>13,} " + " ".join(cells), flush=True)
    print("\n  'fill' = share of snapshots where the whole order fits inside the", flush=True)
    print("  measured 5c band; cost is the median over those snapshots.", flush=True)

    print("\n=== 3. WHERE THE MEDIAN CUSTOMER SITS ===", flush=True)
    for venue, g in d.groupby("source"):
        inside = (g.askq1 >= RETAIL).mean()
        c30 = np.nanmedian(cost_cents(RETAIL, g.askq1.to_numpy(), g.d5ask1.to_numpy(),
                                      g.spread1.to_numpy()))
        px = np.nanmedian(g.p1)
        print(f"  {venue:12} a {RETAIL}-unit order (the median fill, ~${RETAIL*px:.0f} "
              f"at stake) sits inside the touch in {inside:.1%} of snapshots; "
              f"median cost {c30:.2f}c = {c30/100/px*100:.1f}% of notional", flush=True)
    print("  => for the customer the market is measured in, depth is not the", flush=True)
    print("     binding cost. The spread and the fee are.", flush=True)

    print("\n=== 4. DOES THE BOOK THICKEN INTO THE EVENT? ===", flush=True)
    d = d.copy()
    d["bucket"] = pd.cut(d.minutes_to_start, [0, 30, 120, 360, 1440, 1e9],
                         labels=["<30m", "30m-2h", "2-6h", "6-24h", ">24h"])
    piv = d.pivot_table(index="bucket", columns="source", values="d5ask1",
                        aggfunc="median", observed=True)
    n = d.pivot_table(index="bucket", columns="source", values="d5ask1",
                      aggfunc="size", observed=True)
    print("  median size resting within 5c of the ask (CROSS-GAME — the late", flush=True)
    print("  buckets contain a different, more liquid mix of games; use the", flush=True)
    print("  within-game ratio below for the ramp, not this table):", flush=True)
    print(f"  {'window':>10} " + " ".join(f"{v:>16}" for v in piv.columns), flush=True)
    for b in piv.index:
        print(f"  {str(b):>10} " +
              " ".join(f"{piv.loc[b, v]:>10,.0f} (n={n.loc[b, v]:,})"
                       if pd.notna(piv.loc[b, v]) else f"{'-':>16}"
                       for v in piv.columns), flush=True)

    # the cross-bucket table mixes games; do it WITHIN game so the ramp cannot
    # be a composition effect (late-observed games being the liquid ones)
    print("\n  within-game check (same games, late window / early window):", flush=True)
    for venue, g in d.groupby("source"):
        early = (g[g.minutes_to_start.between(360, 1440)]
                 .groupby("game_id").d5ask1.median())
        late = (g[g.minutes_to_start <= 120].groupby("game_id").d5ask1.median())
        both = pd.concat([early.rename("early"), late.rename("late")],
                         axis=1).dropna()
        if len(both) < 10:
            print(f"    {venue:12} only {len(both)} games in both windows", flush=True)
            continue
        ratio = (both.late / both.early)
        rose = (ratio > 1).mean()
        print(f"    {venue:12} n={len(both)} games: median late/early depth ratio "
              f"{ratio.median():.2f}x, deeper late in {rose:.0%} of games", flush=True)

    print("\n=== 5. TOUCH ASYMMETRY (who is the best quote?) ===", flush=True)
    for venue, g in d.groupby("source"):
        tiny = ((g.bidq1 <= 10) | (g.askq1 <= 10)).mean()
        imb = (g.bidq1 / (g.bidq1 + g.askq1)).median()
        deep_imb = (g.d5bid1 / (g.d5bid1 + g.d5ask1)).median()
        print(f"  {venue:12} a <=10-unit order is the best quote on some side in "
              f"{tiny:.1%} of snapshots; touch imbalance {imb:.2f} vs "
              f"5c-band imbalance {deep_imb:.2f}", flush=True)
    print("  (touch thin + band balanced = a retail-sized surface over a "
          "professional layer)", flush=True)

    # figure
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.3))
    qs = np.unique(np.round(np.logspace(0.7, 5.6, 40)).astype(int))
    for venue, col in zip(sorted(d.source.unique()), ("tab:blue", "tab:orange")):
        g = d[d.source == venue]
        med, feas = [], []
        for q in qs:
            cc = cost_cents(q, g.askq1.to_numpy(), g.d5ask1.to_numpy(),
                            g.spread1.to_numpy())
            med.append(np.nanmedian(cc))
            feas.append(np.isfinite(cc).mean() * 100)
        axes[0].plot(qs, med, color=col, label=venue)
        axes[1].plot(qs, feas, color=col, label=venue)
    axes[0].axvline(RETAIL, color="0.4", ls="--", lw=1)
    axes[0].annotate("median customer order", (RETAIL, 0.6), fontsize=7,
                     rotation=90, va="bottom", ha="right", color="0.3")
    axes[0].set(xscale="log", xlabel="order size ($1-payout units)",
                ylabel="cost vs mid (cents per unit)",
                title="The price of immediacy")
    axes[0].legend(fontsize=8)
    axes[1].axvline(RETAIL, color="0.4", ls="--", lw=1)
    axes[1].set(xscale="log", xlabel="order size ($1-payout units)",
                ylabel="% of snapshots filling inside 5c",
                title="Capacity: share of books that absorb the order")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("results/immediacy.png", dpi=130)
    print("\nsaved results/immediacy.png", flush=True)


if __name__ == "__main__":
    main()
