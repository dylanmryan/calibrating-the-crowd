"""Books' own championship futures: calibration and overround.

Completes the futures 2x2. Exchange games clean, exchange futures
pathological, niche exchange games clean — so is the pathology about
long-horizon one-shot markets, or about exchanges? The books' outright
odds on the SAME competitions answer it: if books also misprice
outrights, long-horizon one-shot structure is the problem for everyone
and "books as the disciplined benchmark" has a boundary too.

Data: monthly in-season snapshots (us+eu books, Pinnacle + Betfair
exchange included), three resolved seasons per big-4 sport. Champions
resolved from Kalshi settlements + ESPN (SB LX: Seattle). Implied probs
de-vigged multiplicatively within each book's full field; consensus =
cross-book mean. Season-champion outcomes cluster by sport-season (12
clusters) — exact binomials are pooled and descriptive, the cross-season
repetition is the replication.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

CHAMPS = {
    ("basketball_nba_championship_winner", 2021): ("Milwaukee Bucks", "2021-07-20"),
    ("basketball_nba_championship_winner", 2022): ("Golden State Warriors", "2022-06-16"),
    ("basketball_nba_championship_winner", 2023): ("Denver Nuggets", "2023-06-12"),
    ("americanfootball_nfl_super_bowl_winner", 2021): ("Tampa Bay Buccaneers", "2021-02-07"),
    ("americanfootball_nfl_super_bowl_winner", 2022): ("Los Angeles Rams", "2022-02-13"),
    ("americanfootball_nfl_super_bowl_winner", 2023): ("Kansas City Chiefs", "2023-02-12"),
    ("baseball_mlb_world_series_winner", 2020): ("Los Angeles Dodgers", "2020-10-27"),
    ("baseball_mlb_world_series_winner", 2021): ("Atlanta Braves", "2021-11-02"),
    ("baseball_mlb_world_series_winner", 2022): ("Houston Astros", "2022-11-05"),
    ("icehockey_nhl_championship_winner", 2021): ("Tampa Bay Lightning", "2021-07-07"),
    ("icehockey_nhl_championship_winner", 2022): ("Colorado Avalanche", "2022-06-26"),
    ("icehockey_nhl_championship_winner", 2023): ("Vegas Golden Knights", "2023-06-13"),
    ("basketball_nba_championship_winner", 2024): ("Boston Celtics", "2024-06-17"),
    ("basketball_nba_championship_winner", 2025): ("Oklahoma City Thunder", "2025-06-22"),
    ("basketball_nba_championship_winner", 2026): ("New York Knicks", "2026-06-19"),
    ("americanfootball_nfl_super_bowl_winner", 2024): ("Kansas City Chiefs", "2024-02-11"),
    ("americanfootball_nfl_super_bowl_winner", 2025): ("Philadelphia Eagles", "2025-02-09"),
    ("americanfootball_nfl_super_bowl_winner", 2026): ("Seattle Seahawks", "2026-02-08"),
    ("baseball_mlb_world_series_winner", 2023): ("Texas Rangers", "2023-11-01"),
    ("baseball_mlb_world_series_winner", 2024): ("Los Angeles Dodgers", "2024-10-30"),
    ("baseball_mlb_world_series_winner", 2025): ("Los Angeles Dodgers", "2025-11-01"),
    ("icehockey_nhl_championship_winner", 2024): ("Florida Panthers", "2024-06-24"),
    ("icehockey_nhl_championship_winner", 2025): ("Florida Panthers", "2025-06-17"),
    ("icehockey_nhl_championship_winner", 2026): ("Carolina Hurricanes", "2026-06-19"),
}
EDGES = np.array([0.0, 0.02, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.0])
LAB = [f"{a*100:g}-{b*100:g}c" for a, b in zip(EDGES[:-1], EDGES[1:])]


def season_of(sport, snap):
    y, m = int(snap[:4]), int(snap[5:7])
    if "mlb" in sport:
        return y
    # August boundary: the COVID-delayed 2021 NBA/NHL finals ran into July,
    # which still belongs to the 2020-21 season
    return y + 1 if m >= 8 else y


def main():
    d = pd.read_csv("data/processed/sportsbook_outrights.csv")
    d["season"] = [season_of(s, sn) for s, sn in zip(d.sport, d.snap)]
    d = d[[(s, se) in CHAMPS for s, se in zip(d.sport, d.season)]].copy()
    d["champ"] = [CHAMPS[(s, se)][0] for s, se in zip(d.sport, d.season)]
    d["won"] = (d.team == d.champ).astype(int)
    dec = pd.to_datetime(pd.Series([CHAMPS[(s, se)][1] for s, se in
                                    zip(d.sport, d.season)], index=d.index))
    snap_dt = pd.to_datetime(np.where(d.snap.str.len() == 7, d.snap + "-01", d.snap))
    d["months_out"] = ((dec - snap_dt).dt.days / 30.4).round(1)
    d = d[d.months_out > 0]

    # full fields only: books quoting partial contender lists would
    # understate sums and distort de-vig
    nmax = d.groupby(["sport", "snap"]).team.nunique().rename("n_field")
    d = d.join(nmax, on=["sport", "snap"])
    bk_n = d.groupby(["sport", "snap", "book"]).team.nunique().rename("n_bk")
    d = d.join(bk_n, on=["sport", "snap", "book"])
    d = d[d.n_bk >= 0.9 * d.n_field]

    print(f"snapshot-book-team rows: {len(d):,} | sport-seasons: "
          f"{d.groupby(['sport','season']).ngroups} | books: {d.book.nunique()}", flush=True)

    # 1) the overround, by book
    sums = d.groupby(["sport", "snap", "book"]).raw_p.sum().rename("oversum").reset_index()
    print("\n=== outright field overrounds by book (median across snapshots) ===", flush=True)
    med = sums.groupby("book").oversum.agg(["median", "count"])
    med = med[med["count"] >= 10].sort_values("median")
    for bk, r in med.iterrows():
        tag = " <- sharp" if bk == "pinnacle" else (
              " <- exchange" if bk in ("betfair_ex_eu", "matchbook") else "")
        print(f"  {bk:>16}: {r['median']:.2f}  (n={int(r['count'])}){tag}", flush=True)
    print(f"  [Kalshi outright fields: 1.03-1.06; game markets ~1.01-1.04]", flush=True)

    # 2) calibration of the de-vigged cross-book consensus.
    # multiplicative de-vig on 1.2+ overrounds under-corrects longshots
    # (they carry most of the margin), so tail claims get a Shin check.
    d["devig"] = d.raw_p / d.groupby(["sport", "snap", "book"]).raw_p.transform("sum")

    def shin(g):
        raw = g.raw_p.to_numpy()
        S = raw.sum()
        lo_z, hi_z = 0.0, 0.4
        for _ in range(50):
            z = (lo_z + hi_z) / 2
            p = (np.sqrt(z * z + 4 * (1 - z) * raw * raw / S) - z) / (2 * (1 - z))
            if p.sum() > 1:
                lo_z = z
            else:
                hi_z = z
        return pd.Series(p / p.sum(), index=g.index)

    d["shin"] = d.groupby(["sport", "snap", "book"], group_keys=False).apply(
        shin, include_groups=False)
    cons = (d.groupby(["sport", "season", "snap", "team"])
              .agg(p=("devig", "mean"), p_shin=("shin", "mean"), won=("won", "first"),
                   months_out=("months_out", "first")).reset_index())
    print(f"\n=== book consensus outright calibration "
          f"({len(cons):,} team-snapshots) ===", flush=True)
    for lo, hi, lab in ((0, 3, "0-3 months out (vs exchange T-7/30d)"),
                        (3, 12, "3-12 months out")):
        c = cons[(cons.months_out > lo) & (cons.months_out <= hi)]
        print(f"\n  {lab}: n={len(c):,}", flush=True)
        print(f"  {'priced':>8} {'n':>5} {'avg':>6} {'won':>6} {'gap':>7} "
              f"{'$1 ret':>7} {'exact p':>8}", flush=True)
        b = np.clip(np.digitize(c.p, EDGES) - 1, 0, len(LAB) - 1)
        for k, lab2 in enumerate(LAB):
            m = b == k
            if m.sum() < 10:
                continue
            g = c[m]
            said, obs = g.p.mean(), g.won.mean()
            pex = stats.binomtest(int(g.won.sum()), len(g), said).pvalue
            print(f"  {lab2:>8} {len(g):>5} {said*100:>5.1f}% {obs*100:>5.1f}% "
                  f"{(obs-said)*100:>+6.1f}p ${obs/said:>6.2f} {pex:>8.3f}", flush=True)
        lo10 = c[c.p < 0.10]
        if len(lo10):
            ret = lo10.won / lo10.p.clip(lower=0.005)
            cl = lo10.sport + lo10.season.astype(str) if "season" in lo10 else None
            mu = ret.mean()
            e = (ret - mu).groupby(cl).sum() if cl is not None else None
            se = np.sqrt((e ** 2).sum()) / len(ret) if e is not None else float("nan")
            print(f"  sub-10c: n={len(lo10)}, $1 -> ${mu:.2f} gross "
                  f"(sport-season-clustered se {se:.2f}, {e.shape[0]} clusters) "
                  f"[exchanges: Kalshi $0.33, Poly ~$0.53]", flush=True)
            los = c[c.p_shin < 0.10]
            rs = los.won / los.p_shin.clip(lower=0.005)
            print(f"  sub-10c under SHIN de-vig: n={len(los)}, $1 -> "
                  f"${rs.mean():.2f} gross (tail-robust check)", flush=True)
            mid = c[(c.p_shin >= 0.10) & (c.p_shin < 0.20)]
            if len(mid) > 20:
                print(f"  10-20c under SHIN: n={len(mid)}, priced {mid.p_shin.mean()*100:.1f}% "
                      f"won {mid.won.mean()*100:.1f}% (is the +9pt 'value pocket' "
                      f"a de-vig artifact?)", flush=True)


if __name__ == "__main__":
    main()
