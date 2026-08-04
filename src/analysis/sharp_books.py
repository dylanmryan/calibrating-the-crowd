"""Which book is the benchmark? Pinnacle, Betfair, and the retail field.

The paper's "sportsbook" has been a de-vigged US retail consensus. This
leg asks three sharper questions on the same games (EU closing snapshots,
per-book quotes retained):
  1. Whose line do the exchanges actually sit on — the sharp book
     (Pinnacle), the incumbent exchange (Betfair), or retail?
  2. Does the accuracy dead heat survive against the SHARP price
     specifically (the strongest version of the benchmark)?
  3. Levitt shading: do individual retail books systematically deviate
     from Pinnacle in the direction bettor-bias exploitation predicts?

Timing: EU snapshots use the same closing bucket (start floored to the
hour) as the US consensus run, so book-vs-book comparisons are clean;
exchange prices are at start, the same known timing caveat as the
headline three-way.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.rigor import cluster_dm


def main():
    s = pd.read_csv("data/processed/sportsbook_sharp_prices.csv")
    s = s.drop_duplicates(["game_id", "book"], keep="last")
    s["devig1"] = s.raw_p1 / (s.raw_p1 + s.raw_p2)
    m = pd.read_csv("data/processed/games_master.csv", low_memory=False)
    m = m[m.kalshi_p1.notna() & m.poly_p1.notna() & m.book_p1.notna()
          & m.outcome.notna() & ~m.outcome_disagree.fillna(False)]
    w = s.pivot_table(index="game_id", columns="book", values="devig1")
    d = m.merge(w, on="game_id", how="inner")
    d["date"] = pd.to_datetime(d.start_utc, utc=True, format="ISO8601").dt.date
    d["y"] = (d.outcome == 1).astype(float)
    print(f"joint games with EU books: {len(d):,} | pinnacle: "
          f"{d.pinnacle.notna().sum():,} | betfair_ex_eu: "
          f"{d.betfair_ex_eu.notna().sum():,}", flush=True)

    # 1) proximity: whose line do the exchanges sit on?
    p = d[d.pinnacle.notna()].copy()
    print("\n=== mean |price gap| to each reference (pts, same games) ===", flush=True)
    refs = {"pinnacle (sharp)": p.pinnacle, "US retail consensus": p.book_p1}
    if p.betfair_ex_eu.notna().sum() > 500:
        refs["betfair exchange"] = p.betfair_ex_eu
    for src_name, src in (("Kalshi", p.kalshi_p1), ("Polymarket", p.poly_p1)):
        row = "  ".join(f"{rn}: {(src - rv).abs().mean()*100:.2f}"
                        for rn, rv in refs.items() if rv.notna().sum() > 500)
        print(f"  {src_name:>10} -> {row}", flush=True)
    print(f"  [scale: |pinnacle - US retail| = "
          f"{(p.pinnacle - p.book_p1).abs().mean()*100:.2f}pts]", flush=True)

    # 2) accuracy against the sharp price
    print("\n=== Brier vs the sharp book (clustered DM by date) ===", flush=True)
    subs = {"Pinnacle": "pinnacle", "Betfair exch": "betfair_ex_eu"}
    for nm, col in subs.items():
        g = d[d[col].notna()]
        if len(g) < 500:
            continue
        bs = {"Kalshi": g.kalshi_p1, "Poly": g.poly_p1, "US consensus": g.book_p1,
              nm: g[col]}
        line = " | ".join(f"{k} {((v - g.y)**2).mean():.4f}" for k, v in bs.items())
        print(f"  n={len(g):,}: {line}", flush=True)
        for k in ("Kalshi", "Poly", "US consensus"):
            dbar, se, z, pv, ci90 = cluster_dm(bs[k].to_numpy(), g[col].to_numpy(),
                                               g.y.to_numpy(), g.date.to_numpy())
            print(f"    {k} vs {nm}: dBrier={dbar*1e3:+.3f}e-3 z={z:+.2f} p={pv:.3f} "
                  f"90%CI=({ci90[0]*1e3:+.2f},{ci90[1]*1e3:+.2f})e-3", flush=True)

    # 3) Levitt shading: signed deviation from Pinnacle on home favorites
    print("\n=== retail deviation from the sharp line (Levitt shading test) ===", flush=True)
    fav = p[p.pinnacle > 0.5]     # home favorites: public money side
    books = [c for c in w.columns if c not in ("pinnacle",)
             and p[c].notna().sum() > 1500]
    devs = []
    for bk in books:
        dv = (p[bk] - p.pinnacle).mean() * 100
        dvf = (fav[bk] - fav.pinnacle).mean() * 100
        devs.append((bk, dv, dvf, p[bk].notna().sum()))
    devs.sort(key=lambda t: t[2])
    print(f"  {'book':>16} {'all (pts)':>10} {'home favs':>10} {'n':>6}", flush=True)
    for bk, dv, dvf, n in devs:
        print(f"  {bk:>16} {dv:>+10.2f} {dvf:>+10.2f} {n:>6,}", flush=True)
    print("  [shading toward favorites/public sides would show retail books "
          "systematically ABOVE pinnacle on home favorites]", flush=True)


if __name__ == "__main__":
    main()
