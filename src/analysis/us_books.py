"""The books Americans use: per-book US closing quotes (half-sample).

The EU leg answered the sharp-book question; this answers the referee's
US question — do DraftKings, FanDuel, BetMGM shade their lines the way
the Levitt tradition says retail books do? Random half of the joint set's
closing buckets (seeded shuffle; unbiased subsample), per-book quotes
kept. Also: each US book's own accuracy, cross-book dispersion, and
whether the exchanges price inside the US-book envelope.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.rigor import cluster_dm


def main():
    u = pd.read_csv("data/processed/sportsbook_us_books.csv")
    u = u.drop_duplicates(["game_id", "book"], keep="last")
    u["devig1"] = u.raw_p1 / (u.raw_p1 + u.raw_p2)
    s = pd.read_csv("data/processed/sportsbook_sharp_prices.csv")
    s = s[s.book == "pinnacle"].drop_duplicates("game_id", keep="last")
    s["pinnacle"] = s.raw_p1 / (s.raw_p1 + s.raw_p2)
    m = pd.read_csv("data/processed/games_master.csv", low_memory=False)
    m = m[m.outcome.notna() & ~m.outcome_disagree.fillna(False)]
    w = u.pivot_table(index="game_id", columns="book", values="devig1")
    d = m.merge(w, on="game_id").merge(s[["game_id", "pinnacle"]], on="game_id", how="left")
    d["y"] = (d.outcome == 1).astype(float)
    d["date"] = pd.to_datetime(d.start_utc, utc=True, format="ISO8601").dt.date
    books = [c for c in w.columns if d[c].notna().sum() > 800]
    print(f"US per-book sample: {d.game_id.nunique():,} games | books kept: "
          f"{len(books)} | pinnacle joined: {d.pinnacle.notna().sum():,}", flush=True)

    # 1) Levitt shading vs the sharp line, US retail books
    p = d[d.pinnacle.notna()]
    fav = p[p.pinnacle > 0.5]
    print("\n=== US retail deviation from Pinnacle (pts) ===", flush=True)
    print(f"  {'book':>16} {'all':>7} {'home favs':>10} {'n':>6}", flush=True)
    devs = sorted(((bk, (p[bk] - p.pinnacle).mean() * 100,
                    (fav[bk] - fav.pinnacle).mean() * 100, p[bk].notna().sum())
                   for bk in books), key=lambda t: t[2])
    for bk, dv, dvf, n in devs:
        print(f"  {bk:>16} {dv:>+7.2f} {dvf:>+10.2f} {n:>6,}", flush=True)

    # 2) each book's own accuracy vs the exchanges (same games)
    print("\n=== book-level Brier vs exchanges (clustered DM vs Kalshi) ===", flush=True)
    for bk in sorted(books, key=lambda b: ((d[b] - d.y) ** 2).mean()):
        g = d[d[bk].notna() & d.kalshi_p1.notna()]
        dbar, se, z, pv, _ = cluster_dm(g[bk].to_numpy(), g.kalshi_p1.to_numpy(),
                                        g.y.to_numpy(), g.date.to_numpy())
        print(f"  {bk:>16}: Brier {((g[bk]-g.y)**2).mean():.4f} "
              f"(vs Kalshi dBrier {dbar*1e3:+.2f}e-3, z={z:+.2f}, p={pv:.3f})", flush=True)

    # 3) dispersion and the envelope
    dev = d[books]
    spread = dev.max(axis=1) - dev.min(axis=1)
    inside = ((d.kalshi_p1 >= dev.min(axis=1)) & (d.kalshi_p1 <= dev.max(axis=1))).mean()
    print(f"\n=== dispersion ===", flush=True)
    print(f"  cross-book range (max-min devig prob): median "
          f"{spread.median()*100:.1f}pt", flush=True)
    print(f"  Kalshi's price inside the US-book envelope: {inside:.0%} of games",
          flush=True)


if __name__ == "__main__":
    main()
