"""Four-way calibration: Polymarket US joins Kalshi, Polymarket Global, books.

The fourth institutional cell — the same brand as Polymarket Global operating
as a CFTC-regulated US exchange with a legally disjoint (US-only) participant
pool. Closing prices come from the public execution tape (last trade at or
before the ESPN start; trade-recon methodology, like our pre-cutoff Kalshi
prices), so quality filters mirror that era: staleness and fill-count flags.

Steps:
  1. Aggregate tape rows (a game's final-24h window can span two daily files;
     the close is the latest pre-start trade across files, volumes summed).
  2. Match slugs to master game_ids: league + date (±1 day for UTC) + the
     unordered team-code pair vs ESPN abbreviations; unmatched codes fall
     back to the catalog's long-team full names.
  3. Validate the side convention empirically before use (the tape prices the
     catalog's long=true side): settled games' closes must converge to the
     long side's realized outcome.
  4. Analysis on the joint clean set: four-way Brier/DM/TOST on identical
     games, per-league table, and the law-of-one-price test between the two
     Polymarkets — same brand, segregated pools.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.compare import brier
from src.analysis.rigor import cluster_dm
from src.analysis.three_way import load

STALE_MAX_MIN = 120
FILLS_MIN = 5
LEAGUES = {"NBA", "NHL", "MLB", "WNBA", "NFL", "CFB"}


def build_prices():
    p = pd.read_csv("data/processed/polyus_prices.csv")
    p["close_ts"] = pd.to_datetime(p.close_ts, utc=True, format="ISO8601")
    agg = (p.sort_values("close_ts").groupby("slug")
           .agg(close_price=("close_price", "last"), close_ts=("close_ts", "last"),
                stale_min=("stale_min", "last"), fills_24h=("fills_24h", "sum"),
                vol_24h=("vol_24h", "sum")).reset_index())
    cat = pd.read_csv("data/processed/polyus_catalog.csv")
    d = agg.merge(cat[["slug", "league", "game_start", "long_desc", "long_team"]], on="slug")
    d = d[d.league.isin(LEAGUES)].copy()
    parts = d.slug.str.split("-")
    d["code1"] = parts.str[2].str.upper()
    d["code2"] = parts.str[3].str.upper()
    d["date"] = pd.to_datetime(d.game_start, utc=True, format="ISO8601").dt.date
    return d


def match_games(d):
    espn = pd.read_csv("data/processed/espn_games.csv")
    espn = espn[espn.winner.isin(["home", "away"])].copy()
    espn["lg"] = espn.league.replace({"CBB-M": "CBB"})
    espn["date"] = pd.to_datetime(espn.start_utc, utc=True, format="ISO8601").dt.date
    idx = {}
    for r in espn.itertuples(index=False):
        key = (r.lg, frozenset((str(r.home_abbr).upper(), str(r.away_abbr).upper())))
        for delta in (-1, 0, 1):
            idx.setdefault((key[0], key[1], r.date + pd.Timedelta(days=delta).to_pytimedelta()), []).append(r)
    rows = []
    for r in d.itertuples(index=False):
        cands = idx.get((r.league, frozenset((r.code1, r.code2)), r.date), [])
        if len(cands) == 1:
            e = cands[0]
        elif len(cands) > 1:   # doubleheaders: nearest start time
            e = min(cands, key=lambda x: abs(pd.Timestamp(x.start_utc)
                                             - pd.Timestamp(r.game_start)))
        else:
            continue
        home_names = f"{e.home_team}"
        long_is_home = (str(r.long_team) in home_names or str(r.long_desc) in home_names
                        or str(r.code2) == str(e.home_abbr).upper() and False)
        # primary rule: match long team NAME to ESPN home/away names
        if str(r.long_team) and str(r.long_team) != "nan":
            if str(r.long_team) == str(e.home_team):
                long_is_home = True
            elif str(r.long_team) == str(e.away_team):
                long_is_home = False
            elif str(r.long_desc) in str(e.home_team):
                long_is_home = True
            elif str(r.long_desc) in str(e.away_team):
                long_is_home = False
            else:
                continue   # can't identify the priced side -> drop
        espn_start = pd.Timestamp(e.start_utc)
        rows.append({"game_id": e.espn_id, "league": r.league,
                     "pus_p1": r.close_price if long_is_home else 1 - r.close_price,
                     "pus_long_won": (e.winner == "home") == long_is_home,
                     "stale_min": r.stale_min, "fills_24h": r.fills_24h,
                     "vol_24h": r.vol_24h, "close_price": r.close_price,
                     # anchor integrity: the tape close was computed against the
                     # catalog's game_start, which falls back to endDate (post-
                     # game!) when gameStartTime is missing — those closes can
                     # contain in-game trades. Measure both defects explicitly.
                     "anchor_delta_min": abs((pd.Timestamp(r.game_start) - espn_start)
                                             .total_seconds()) / 60,
                     "eff_stale_min": (espn_start - r.close_ts).total_seconds() / 60})
    return pd.DataFrame(rows)


def main():
    d = build_prices()
    print(f"tape closes in major leagues: {len(d):,}", flush=True)
    m = match_games(d)
    print(f"matched to ESPN games: {len(m):,} ({m.league.value_counts().to_dict()})", flush=True)

    # ---- side-convention validation (like the ticker-order rule audit) ----
    extreme = m[(m.close_price > 0.9) | (m.close_price < 0.1)]
    if len(extreme):
        ok = ((extreme.close_price > 0.9) == extreme.pus_long_won).mean()
        print(f"side validation on extreme closes (n={len(extreme)}): "
              f"{ok:.1%} agree with realized outcome", flush=True)

    # ---- join the three-way clean set ----
    # look-ahead guard (deep audit 2026-07-29): drop games whose tape anchor was
    # the endDate fallback (start mismatch > 30min vs ESPN) and any close that
    # postdates the ESPN start
    bad_anchor = (m.anchor_delta_min > 30) | (m.eff_stale_min < 0)
    print(f"anchor integrity: excluding {bad_anchor.sum()} of {len(m)} matched games "
          f"(endDate-fallback anchors / post-start closes)", flush=True)
    m = m[~bad_anchor]

    t = load()
    t["date"] = t.start_utc.astype(str).str[:10]
    j = t.merge(m[["game_id", "pus_p1", "stale_min", "fills_24h"]], on="game_id")
    jq = j[(j.stale_min <= STALE_MAX_MIN) & (j.fills_24h >= FILLS_MIN)].copy()
    y = jq.home_won.values
    print(f"\nfour-way joint clean set: {len(j):,} matched, {len(jq):,} after quality "
          f"filters (stale<={STALE_MAX_MIN}min, fills>={FILLS_MIN})", flush=True)
    print(jq.league.value_counts().to_string(), flush=True)

    cols = {"Kalshi": "kalshi_p1", "Poly-Global": "poly_p1",
            "Sportsbook": "book_p1", "Poly-US": "pus_p1"}
    print(f"\n=== four-way Brier (same games) ===", flush=True)
    for name, c in cols.items():
        print(f"  {name:11} {brier(jq[c].values, y):.4f}", flush=True)
    print(f"\n=== Poly-US vs each (clustered DM; dbar>0 => US worse; TOST d_min) ===", flush=True)
    for name, c in cols.items():
        if c == "pus_p1":
            continue
        dbar, se, z, p, (lo, hi) = cluster_dm(jq.pus_p1.values, jq[c].values, y, jq.date.values)
        dmin = max(abs(lo), abs(hi))
        print(f"  vs {name:11} dBrier={dbar*1000:+.2f}e-3  z={z:+.2f}  p={p:.3f}  "
              f"delta_min={dmin*1000:.2f}e-3 {'EQUIV@1e-3' if dmin <= 1e-3 else ''}", flush=True)

    # ---- law of one price: the two Polymarkets ----
    gap_us = (jq.pus_p1 - jq.poly_p1).abs()
    gap_kp = (jq.kalshi_p1 - jq.poly_p1).abs()
    print(f"\n=== law of one price: Poly-US vs Poly-Global (segregated pools) ===", flush=True)
    print(f"  |US - Global|: median {gap_us.median()*100:.2f}pt, mean {gap_us.mean()*100:.2f}pt, "
          f">5pt in {(gap_us > 0.05).mean():.1%}", flush=True)
    print(f"  benchmark |K - Global|: median {gap_kp.median()*100:.2f}pt, mean {gap_kp.mean()*100:.2f}pt, "
          f">5pt in {(gap_kp > 0.05).mean():.1%}", flush=True)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    axes[0].scatter(jq.poly_p1, jq.pus_p1, s=5, alpha=0.35, color="tab:purple")
    axes[0].plot([0, 1], [0, 1], "--", color="0.4", lw=1)
    axes[0].set(xlabel="Polymarket Global (home prob)", ylabel="Polymarket US (home prob)",
                title=f"Same brand, segregated pools (n={len(jq):,})")
    leagues = [lg for lg, _ in sorted(jq.groupby("league"), key=lambda t: -len(t[1]))]
    x = np.arange(len(leagues))
    w = 0.2
    for i, (name, c) in enumerate(cols.items()):
        vals = [brier(jq[jq.league == lg][c].values, jq[jq.league == lg].home_won.values)
                for lg in leagues]
        axes[1].bar(x + (i - 1.5) * w, vals, w, label=name)
    axes[1].set_xticks(x, leagues)
    axes[1].set(ylabel="Brier", title="Four-way Brier by league")
    axes[1].legend(fontsize=8)
    fig.suptitle("Polymarket US: the fourth institutional cell")
    fig.tight_layout()
    fig.savefig("results/four_way.png", dpi=130)
    print("\nsaved results/four_way.png", flush=True)


if __name__ == "__main__":
    main()
