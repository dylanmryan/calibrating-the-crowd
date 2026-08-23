"""Cross-source margin curves: Kalshi alternate-spread ladders vs the books'
alternate spread lines on the same games (MLB + NBA).

Mapping: both sources are reduced to a COVER LINE -- the smallest signed
margin, for the contract's own side, that wins it -- and joined on that.
Joining on the raw threshold instead silently pairs different events in MLB,
where Kalshi quotes integer run lines ("wins by 2+") against the books'
half-point lines ("wins by more than 2.5"). That one-rung offset, not the
market, produced the +8.4pt MLB cell. See src/analysis/ladder_convention.py.

Questions:
  1. Do the curves agree point-by-point? (level + correlation by league/threshold)
  2. Tail calibration of the BOOK ladders (Brier/ECE vs realized margins) —
     benchmark for Kalshi's 0.186 / 0.008.
  3. THE test: the MLB 'win by 1-2' cell, computed from the cover=3 rung on
     both sides so the same event is priced. Historically reported as a
     Kalshi-specific +8.4pt under-pricing; that was the join bug.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.compare import brier, ece
from src.collect.kalshi_hist_prices import _rule_home
from src.analysis.ladder_convention import cover_line, book_cover_line, is_push_line


def _kalshi_ladder():
    """(game_id, side, threshold, k_prob) with side resolved via ticker-order rule."""
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    sp = sp[sp.league.isin(("MLB", "NBA", "NHL"))]
    rows = []
    for gid, g in sp.groupby("game_id"):
        ev = g["event_ticker"].iloc[0]
        codes = sorted(set(g["team"]))
        rh = _rule_home(ev, codes) if len(codes) == 2 else None
        if rh is None:
            continue
        for r in g.itertuples(index=False):
            if r.prob != r.prob:
                continue
            rows.append({"game_id": gid, "league": r.league,
                         "side": "home" if r.team == rh else "away",
                         "threshold": float(r.threshold),
                         "cover": cover_line(r.league, r.threshold),
                         "k_prob": float(r.prob)})
    return pd.DataFrame(rows)


def _book_ladder():
    """Book P(side wins by > t) from alternate_spreads consensus."""
    ab = pd.read_csv("data/processed/sportsbook_alt_spreads.csv")
    home = ab[ab.point < 0].assign(side="home", threshold=lambda d: -d.point,
                                   b_prob=lambda d: d.prob_home)
    away = ab[ab.point > 0].assign(side="away", threshold=lambda d: d.point,
                                   b_prob=lambda d: 1 - d.prob_home)
    out = pd.concat([home, away])
    # whole-number lines can push; they are not the same event as any Kalshi
    # rung and must not be joined to one
    out = out[~is_push_line(out.threshold)].copy()
    out["cover"] = book_cover_line(out.threshold)
    return out[["game_id", "league", "side", "threshold", "cover", "b_prob", "n_books"]]


def _margins():
    esp = pd.read_csv("data/processed/espn_games.csv")
    esp = esp[esp.status == "STATUS_FINAL"].rename(columns={"espn_id": "game_id"})
    esp["margin"] = esp.home_score - esp.away_score
    return esp.set_index("game_id")["margin"]


def main():
    k, b = _kalshi_ladder(), _book_ladder()
    mg = _margins()
    d = k.merge(b, on=["game_id", "league", "side", "cover"], how="inner",
                suffixes=("_k", "_b"))
    d = d[d.game_id.isin(mg.index)].copy()
    d["margin"] = d.game_id.map(mg)
    d["sm"] = np.where(d.side == "home", d.margin, -d.margin)
    d["won"] = (d.sm >= d.cover).astype(float)
    print(f"matched ladder contracts: {len(d):,} "
          f"({d.game_id.nunique():,} games; MLB {len(d[d.league=='MLB']):,} / NBA {len(d[d.league=='NBA']):,})", flush=True)

    print("\n=== level agreement: Kalshi vs book ladder prices ===", flush=True)
    print(f"  corr={d.k_prob.corr(d.b_prob):.4f}   mean(K-B)={100*(d.k_prob-d.b_prob).mean():+.2f}pts   "
          f"|K-B| median={100*(d.k_prob-d.b_prob).abs().median():.2f}pts", flush=True)
    d["band"] = pd.cut(d.b_prob, [0, .1, .25, .5, .75, .9, 1.0])
    print(d.groupby(["league", "band"], observed=True)
           .apply(lambda g: pd.Series({"n": len(g), "mean_K_minus_B": round(100*(g.k_prob-g.b_prob).mean(), 2)}),
                  include_groups=False).to_string(), flush=True)

    print("\n=== tail calibration on identical contracts ===", flush=True)
    for name, col in (("Kalshi", "k_prob"), ("Book", "b_prob")):
        print(f"  {name:7} Brier={brier(d[col], d.won):.4f}  ECE={ece(d[col].values, d.won.values):.4f}", flush=True)

    # --- THE cell test: MLB win-by-1-2, book version ------------------------
    print("\n=== MLB 'win by 1-2' cell: Kalshi vs book (same games, same rungs) ===", flush=True)
    m = pd.read_csv("data/processed/games_master.csv")[["game_id", "kalshi_p1", "book_p1"]]
    mlb = d[(d.league == "MLB") & (d.cover == 3)].merge(m, on="game_id")
    inn = pd.read_csv("data/processed/mlb_innings.csv")[["game_id", "innings"]]
    mlb = mlb.merge(inn, on="game_id", how="left")
    mlb["extras"] = mlb.innings > 9
    rows = []
    for r in mlb.itertuples(index=False):
        for src, pml, plad in (("Kalshi", r.kalshi_p1, r.k_prob), ("Book", r.book_p1, r.b_prob)):
            if pml != pml:
                continue
            pwin = pml if r.side == "home" else 1 - pml
            rows.append({"src": src, "extras": bool(r.extras),
                         "imp": pwin - plad, "emp": float(r.sm in (1, 2))})
    c = pd.DataFrame(rows)
    print(f"  {'source':>8} {'n':>6} {'implied':>9} {'empirical':>10} {'gap(pts)':>9} {'z':>6}", flush=True)
    for src, g in c.groupby("src"):
        gap = g.emp.mean() - g.imp.mean()
        se = np.sqrt(g.emp.var() / len(g) + g.imp.var() / len(g))
        print(f"  {src:>8} {len(g):>6,} {g.imp.mean():>9.4f} {g.emp.mean():>10.4f} "
              f"{gap*100:>+9.2f} {gap/se:>+6.2f}", flush=True)
    for src, g in c.groupby("src"):
        reg, ext = g[~g.extras], g[g.extras]
        print(f"  {src}: regulation gap {100*(reg.emp.mean()-reg.imp.mean()):+.2f}pts (n={len(reg)}), "
              f"extras gap {100*(ext.emp.mean()-ext.imp.mean()):+.2f}pts (n={len(ext)})", flush=True)
    print("  (matching gaps => baseball-wide blind spot; book~0 => Kalshi-specific)", flush=True)


if __name__ == "__main__":
    main()
