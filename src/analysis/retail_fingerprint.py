"""Retail fingerprint: does the order flow look like consumption or analysis?

The pricing side of the paper says prices are instrument-grade and
maker-driven, with taker flow uninformative. This asks what the taker flow
IS, from 710K fills (512 games): when people trade (relative to the game,
and by wall clock when far from any game), and in what sizes (tiny round
lots being the classic retail habit). The institutional synthesis expects a
sportsbook-like clientele at the surface: entertainment-shaped flow whose
price impact is filtered by makers — betting-shop customers, exchange-grade
prices. No new significance claims; this is descriptive institutional
evidence, cross-checked against the existing markout result (no size class
has edge).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    t = pd.read_csv("data/processed/kalshi_trades_24h.csv")
    t["ts"] = pd.to_datetime(t.created_time, utc=True, format="ISO8601")
    t["start"] = pd.to_datetime(t.start_utc, utc=True, format="ISO8601")
    t["hrs_to"] = (t.start - t.ts).dt.total_seconds() / 3600
    t["notional"] = t["count"] * t.yes_price
    t = t[t.hrs_to.between(0, 24)]
    print(f"fills: {len(t):,} | games: {t.game_id.nunique()} | "
          f"contracts: {t['count'].sum():,.0f}", flush=True)

    # 1. when: concentration into game time
    last3 = t[t.hrs_to <= 3]
    print(f"\n=== timing: consumption clusters at the event ===", flush=True)
    print(f"  final 3h of 24: {len(last3)/len(t):.0%} of fills, "
          f"{last3.notional.sum()/t.notional.sum():.0%} of notional "
          f"(uniform would be 12.5%)", flush=True)
    for lo, hi in ((0, 1), (1, 3), (3, 6), (6, 12), (12, 24)):
        m = t[(t.hrs_to > lo) & (t.hrs_to <= hi)]
        rate = len(m) / (hi - lo)
        print(f"  T-{hi}h..T-{lo}h: {len(m)/len(t):>5.1%} of fills "
              f"({rate/len(t)*100:.2f}%/hour)", flush=True)

    # 2. wall clock, far from game time (T-24..T-12): leisure hours?
    far = t[t.hrs_to > 12].copy()
    far["et_hour"] = (far.ts.dt.tz_convert("US/Eastern")).dt.hour
    evening = far.et_hour.between(19, 23).mean()
    work = far.et_hour.between(9, 17).mean()
    print(f"\n=== wall clock for fills FAR from any game (T-24..T-12h) ===", flush=True)
    print(f"  evening ET (7pm-midnight): {evening:.0%} of far fills "
          f"(5/24 hours = 21% if uniform)", flush=True)
    print(f"  working hours ET (9am-5pm): {work:.0%} (8/24 = 33% if uniform)", flush=True)

    # 3. lot sizes: the retail habit
    print(f"\n=== lot sizes ===", flush=True)
    c = t["count"]
    tiny = (c <= 10).mean()
    round_lot = c.isin([1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000]).mean()
    big_share = t.loc[c >= 500, "count"].sum() / c.sum()
    print(f"  fills of <=10 contracts: {tiny:.0%} of all fills "
          f"(but only {t.loc[c <= 10, 'count'].sum()/c.sum():.0%} of volume)", flush=True)
    print(f"  round-number lots: {round_lot:.0%} of fills", flush=True)
    print(f"  fills of >=500 contracts: {(c >= 500).mean():.1%} of fills, "
          f"{big_share:.0%} of volume", flush=True)
    med_fill = c.median()
    med_dollar = t.notional.median()
    print(f"  median fill: {med_fill:.0f} contracts ≈ ${med_dollar:.0f} at stake", flush=True)

    print(f"\n  reading: flow is event-clustered, evening-tilted, and tiny —", flush=True)
    print(f"  a betting-shop clientele — while the markout analysis shows no", flush=True)
    print(f"  size class beats the close: consumption pays, makers price.", flush=True)

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2))
    axes[0].hist(t.hrs_to, bins=48, color="tab:blue", alpha=0.8)
    axes[0].invert_xaxis()
    axes[0].set(xlabel="hours before game start", ylabel="fills",
                title="Trading clusters at the event")
    axes[1].hist(far.et_hour, bins=range(25), color="tab:orange", alpha=0.8)
    axes[1].set(xlabel="hour of day (ET), fills >12h from any game",
                title="...and in the evening otherwise")
    sizes = c.clip(upper=1000)
    axes[2].hist(sizes, bins=np.geomspace(1, 1000, 40), color="tab:green", alpha=0.8)
    axes[2].set(xscale="log", xlabel="fill size (contracts, log)",
                title=f"...in tiny lots (median {med_fill:.0f})")
    fig.suptitle("The retail fingerprint: who the market is for (710K fills)")
    fig.tight_layout()
    fig.savefig("results/retail_fingerprint.png", dpi=130)
    print("\nsaved results/retail_fingerprint.png", flush=True)


if __name__ == "__main__":
    main()
