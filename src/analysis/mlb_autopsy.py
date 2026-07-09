"""MLB margin autopsy + ensemble information test.

Part 1 — why does MLB fail the distributional PIT? Compare the ladder-implied
probability of each exact margin against its empirical frequency. Baseball's
walk-off rule creates a spike at margin=1 (home team stops playing once ahead);
if run lines under-price that spike, the miscalibration is localized and explainable.

Part 2 — ensemble test: average the three sources' probabilities. If they carry
the same information (equal resolution), the ensemble should NOT beat the best
single source; genuine private information would make the combination win.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.compare import brier
from src.analysis.three_way import load, dm
from src.collect.kalshi_hist_prices import _rule_home


def mlb_margins():
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    sp = sp[sp.league == "MLB"]
    esp = pd.read_csv("data/processed/espn_games.csv")[
        ["espn_id", "home_score", "away_score"]].rename(columns={"espn_id": "game_id"})
    ml = pd.read_csv("data/processed/games_master.csv")[["game_id", "kalshi_p1"]]

    rows = []
    for gid, g in sp.groupby("game_id"):
        e = esp[esp.game_id == gid]
        if len(e) != 1 or e.iloc[0].home_score != e.iloc[0].home_score:
            continue
        ev = g["event_ticker"].iloc[0]
        codes = sorted(set(g["team"]))
        rh = _rule_home(ev, codes) if len(codes) == 2 else None
        if rh is None:
            continue
        margin = int(e.iloc[0].home_score - e.iloc[0].away_score)
        home = {r.threshold: r.prob for r in g[g.team == rh].itertuples(index=False) if r.prob == r.prob}
        away = {r.threshold: r.prob for r in g[g.team != rh].itertuples(index=False) if r.prob == r.prob}
        mlr = ml[ml.game_id == gid]
        pml = float(mlr.iloc[0].kalshi_p1) if len(mlr) and mlr.iloc[0].kalshi_p1 == mlr.iloc[0].kalshi_p1 else None
        if pml is None:
            continue
        # per side, decompose the win probability into margin cells using the
        # dense rungs (2.5/3.5/4.5): implied P(win by 1-2) = P(win) - P(by>2.5), etc.
        for side_rungs, sgn in ((home, +1), (away, -1)):
            pwin = pml if sgn == 1 else 1 - pml
            sm = sgn * margin
            if 2.5 in side_rungs:
                rows.append({"cell": "margin 1-2", "imp": pwin - side_rungs[2.5],
                             "emp": float(sm in (1, 2))})
            if 2.5 in side_rungs and 3.5 in side_rungs:
                rows.append({"cell": "margin 3", "imp": side_rungs[2.5] - side_rungs[3.5],
                             "emp": float(sm == 3)})
            if 3.5 in side_rungs and 4.5 in side_rungs:
                rows.append({"cell": "margin 4", "imp": side_rungs[3.5] - side_rungs[4.5],
                             "emp": float(sm == 4)})
    d = pd.DataFrame(rows)
    print(f"=== MLB margin autopsy ({d.game if hasattr(d,'game') else len(d):,} cell-observations) ===", flush=True)
    print(f"{'cell':>11} {'n':>6} {'implied':>9} {'empirical':>10} {'gap(pts)':>9} {'z':>6}", flush=True)
    for cell, g in d.groupby("cell"):
        se = g.emp.std() / np.sqrt(len(g))
        z = (g.emp.mean() - g.imp.mean()) / np.sqrt(se**2 + (g.imp.std()/np.sqrt(len(g)))**2)
        print(f"{cell:>11} {len(g):>6,} {g.imp.mean():>9.4f} {g.emp.mean():>10.4f} "
              f"{(g.emp.mean()-g.imp.mean())*100:>+9.2f} {z:>+6.2f}", flush=True)
    print("  (positive gap = market UNDER-prices that margin cell)", flush=True)


def ensemble():
    d = load()
    y = d["home_won"].values
    d["ens"] = d[["kalshi_p1", "poly_p1", "book_p1"]].mean(axis=1)
    print(f"\n=== ensemble information test (n={len(d):,}) ===", flush=True)
    briers = {}
    for name, col in [("Kalshi", "kalshi_p1"), ("Polymarket", "poly_p1"),
                      ("Sportsbook", "book_p1"), ("ENSEMBLE(mean)", "ens")]:
        briers[name] = brier(d[col], y)
        print(f"  {name:15} Brier={briers[name]:.4f}", flush=True)
    best_single = min(("kalshi_p1", "poly_p1", "book_p1"), key=lambda c: brier(d[c], y))
    s, p = dm(d["ens"], d[best_single], y)
    print(f"  ensemble vs best single ({best_single}): DM={s:+.2f} p={p:.3f} "
          f"-> {'ensemble ADDS information' if (s<0 and p<0.05) else 'no significant gain (shared information)'}", flush=True)
    # disagreement-conditional: does the ensemble help most when sources disagree?
    d["spread3"] = d[["kalshi_p1", "poly_p1", "book_p1"]].max(axis=1) - d[["kalshi_p1", "poly_p1", "book_p1"]].min(axis=1)
    hi = d[d.spread3 > d.spread3.quantile(0.9)]
    s2, p2 = dm(hi["ens"], hi[best_single], hi["home_won"].values)
    print(f"  top-decile disagreement games (n={len(hi)}): ensemble vs best single "
          f"DM={s2:+.2f} p={p2:.3f}", flush=True)


if __name__ == "__main__":
    mlb_margins()
    ensemble()
