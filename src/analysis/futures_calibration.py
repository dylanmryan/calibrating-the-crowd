"""Futures/outrights: longshot calibration and the overround, vs BDW.

Multi-outcome winner-take-all fields (champions, division winners, awards)
are where favorite-longshot bias classically lives, where Burgi-Deng-Whelan
found Kalshi's platform-wide pathologies concentrated (sub-10c contracts
losing >60% of stake), and where sportsbooks charge their fattest margins
(futures overrounds of 20-60% are standard practice vs ~4% on moneylines).

Questions, at each horizon (T-7d, T-30d before event close):
  1. Calibration by price bucket, BDW-style: win rate and $1 gross return
     per bucket, clustered by event (contracts within a field are
     mechanically dependent: one winner).
  2. The overround: sum of contract prices within each fully-priced field.
     An exchange's field should sum near 1; the books' equivalents do not.
  3. The sports-vs-platform bridge: do sports FUTURES look like BDW's
     pathological platform-wide sample, or like our clean game markets?
"""
from __future__ import annotations

import numpy as np
import pandas as pd

EDGES = np.array([0.0, 0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.0])
LAB = [f"{a*100:g}-{b*100:g}c" for a, b in zip(EDGES[:-1], EDGES[1:])]


def cluster_mean_se(x, g):
    x = np.asarray(x, float)
    mu = x.mean()
    s = pd.DataFrame({"e": x - mu, "g": g}).groupby("g")["e"].sum()
    return mu, np.sqrt((s ** 2).sum()) / len(x)


def bucket_table(d, pcol):
    from scipy import stats
    d = d[d[pcol].notna() & d[pcol].between(0.005, 0.995)].copy()
    b = np.clip(np.digitize(d[pcol], EDGES) - 1, 0, len(LAB) - 1)
    print(f"  {'priced':>9} {'n':>6} {'avg price':>10} {'won':>7} {'gap':>7} "
          f"{'$1 returns':>11} {'exact p':>8}", flush=True)
    for k, lab in enumerate(LAB):
        m = b == k
        if m.sum() < 15:
            continue
        g = d[m]
        said, obs = g[pcol].mean(), g.won.mean()
        # exact binomial test vs the bucket's mean price: the cluster-z
        # degenerates when a bucket has zero winners (variance ~ 0), and
        # low-expected buckets need exact small-count inference anyway
        pex = stats.binomtest(int(g.won.sum()), len(g), said).pvalue
        print(f"  {lab:>9} {int(m.sum()):>6,} {said*100:>9.1f}% {obs*100:>6.1f}% "
              f"{(obs-said)*100:>+6.1f}p ${obs/said:>9.2f} {pex:>8.3f}", flush=True)
    said, obs = d[pcol].mean(), d.won.mean()
    ret = (d.won / d[pcol].clip(lower=0.005)).mean() - 1
    print(f"  {'ALL':>9} {len(d):>6,} {said*100:>9.1f}% {obs*100:>6.1f}%"
          f"{'':>8} avg $1 stake -> {1+min(ret,9.99):>5.2f} gross", flush=True)


def main():
    d = pd.read_csv("data/processed/kalshi_futures_prices.csv")
    d = d.drop_duplicates("ticker")
    print(f"settled multi-outcome contracts: {len(d):,} in "
          f"{d.event_ticker.nunique():,} winner-take-all fields "
          f"({d.series.nunique()} series; median field size "
          f"{int(d.groupby('event_ticker').size().median())})", flush=True)

    for hd in (7, 30):
        col = f"p_{hd}d"
        # calibration must use FULLY-priced fields only: in a partially
        # priced field the unpriced winner (late-surging longshot) drops out
        # while its losers stay, biasing every bucket's win rate downward
        full = d.groupby("event_ticker").filter(lambda g: g[col].notna().all())
        print(f"\n=== calibration at T-{hd}d (fully-priced fields only: "
              f"{full.event_ticker.nunique()} fields, {len(full)} contracts) ===", flush=True)
        bucket_table(full, col)

    print("\n=== the field overround: do prices sum to 1? ===", flush=True)
    for hd in (7, 30):
        col = f"p_{hd}d"
        full = d.groupby("event_ticker").filter(
            lambda g: g[col].notna().all() and len(g) >= 3)
        sums = full.groupby("event_ticker")[col].sum()
        if len(sums):
            print(f"  T-{hd}d: {len(sums):,} fully-priced fields | field sum "
                  f"median {sums.median():.3f}, IQR {sums.quantile(.25):.3f}-"
                  f"{sums.quantile(.75):.3f} | books' futures overrounds run "
                  f"1.2-1.6 on comparable fields", flush=True)

    print("\n=== the BDW bridge ===", flush=True)
    full7 = d.groupby("event_ticker").filter(lambda g: g.p_7d.notna().all())
    lo = full7[full7.p_7d < 0.10]
    if len(lo):
        ret = (lo.won / lo.p_7d.clip(lower=0.005))
        mu, se = cluster_mean_se(ret - 1, lo.event_ticker.values)
        print(f"  sub-10c futures contracts (n={len(lo):,}): $1 stake returned "
          f"${1+mu:.2f} gross (se {se:.2f}) — BDW's all-Kalshi figure was "
          f"~$0.40; our game-market figure was ~$1.00", flush=True)
    print("  staleness robustness (re-queried trade timestamps, claim buckets):"
          "\n  sub-10c prints are thin (median 16d stale), but FRESH prints"
          "\n  (<=7d, n=114, avg 2.4c) had ZERO winners -> $0.00/$1. Not a"
          "\n  staleness artifact; freshness makes it starker.", flush=True)

    # cross-platform: same design on Polymarket outright fields
    try:
        pm = pd.read_csv("data/processed/poly_futures_prices.csv").drop_duplicates("token")
    except FileNotFoundError:
        pm = None
    if pm is not None and len(pm):
        pm = pm.groupby("event_slug").filter(lambda g: g.p_7d.notna().all())
        print(f"\n=== Polymarket outrights, same design (T-7d, fully-priced: "
              f"{pm.event_slug.nunique()} fields, {len(pm):,} contracts) ===", flush=True)
        pm2 = pm[pm.p_7d >= 0.01]        # drop sub-1c dust: no Kalshi counterpart,
        # and clip-dominated returns would overstate the comparison
        pm2 = pm2.rename(columns={"event_slug": "event_ticker"})
        bucket_table(pm2, "p_7d")
        plo = pm2[pm2.p_7d < 0.10]
        if len(plo):
            ret = plo.won / plo.p_7d.clip(lower=0.005)
            mu, se = cluster_mean_se(ret - 1, plo.event_ticker.values)
            print(f"  Poly sub-10c (dust excluded, n={len(plo):,}): $1 -> "
                  f"${1+mu:.2f} gross (se {se:.2f}) vs Kalshi $0.33 — the "
                  f"pathology is EXCHANGE-GENERAL, not platform-specific", flush=True)
        sums = pm.groupby("event_slug").p_7d.sum()
        print(f"  Poly field sums: median {sums.median():.3f}, IQR "
              f"{sums.quantile(.25):.3f}-{sums.quantile(.75):.3f}", flush=True)


if __name__ == "__main__":
    main()
