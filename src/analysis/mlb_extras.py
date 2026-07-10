"""MLB margin-of-1 mechanism: walk-offs and extra innings.

The run-line autopsy found Kalshi under-prices 1-2-run margins by ~8pts and the
PIT test rejects MLB's implied margin distribution (location-unbiased, wrong
shape). Two rules of baseball predict exactly this shape error:

  1. Walk-off endings — the home team stops playing the moment it leads in its
     final at-bat, truncating would-be bigger wins to small margins. Prediction:
     the margin=1 spike is a HOME-win phenomenon.
  2. Extra innings — since 2020 each extra half-inning starts with a placed
     ghost runner; combined with the walk-off rule, extras overwhelmingly end
     by exactly one run. Prediction: P(margin=1 | extras) >> P(margin=1 | 9inn).

If the ladder's under-pricing of the 1-2 cell concentrates in these game states,
the miscalibration has a *cause*: the market prices a smooth margin distribution
and misses the spike created by baseball's ending rules.

Needs data/processed/mlb_innings.csv (src/collect/mlb_innings.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.collect.kalshi_hist_prices import _rule_home


def load_games():
    esp = pd.read_csv("data/processed/espn_games.csv")
    esp = esp[(esp.league == "MLB") & (esp.status == "STATUS_FINAL")].copy()
    inn = pd.read_csv("data/processed/mlb_innings.csv")[["game_id", "innings"]]
    g = esp.rename(columns={"espn_id": "game_id"}).merge(inn, on="game_id", how="inner")
    g = g[g.innings >= 9]  # drop rain-shortened
    g["margin"] = g.home_score - g.away_score
    g = g[g.margin != 0]
    g["extras"] = g.innings > 9
    g["home_win"] = g.margin > 0
    return g


def descriptive(g):
    print(f"=== MLB endings, n={len(g):,} finals ({g.extras.mean():.1%} extras) ===", flush=True)
    print(f"{'game state':>22} {'n':>6} {'P(|margin|=1)':>14} {'P(|margin|<=2)':>15}", flush=True)
    cuts = [("all games", g),
            ("regulation (9 inn)", g[~g.extras]),
            ("extra innings", g[g.extras]),
            ("home wins", g[g.home_win]),
            ("away wins", g[~g.home_win]),
            ("home wins, extras", g[g.home_win & g.extras]),
            ("away wins, extras", g[~g.home_win & g.extras])]
    for name, s in cuts:
        m1 = (s.margin.abs() == 1).mean()
        m12 = (s.margin.abs() <= 2).mean()
        print(f"{name:>22} {len(s):>6,} {m1:>14.3f} {m12:>15.3f}", flush=True)


def ladder_decomposition(g):
    """Re-derive the autopsy's 'margin 1-2' cell, tagged by side and extras."""
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    sp = sp[sp.league == "MLB"]
    ml = pd.read_csv("data/processed/games_master.csv")[["game_id", "kalshi_p1"]]
    info = g.set_index("game_id")[["margin", "extras"]]

    rows = []
    for gid, grp in sp.groupby("game_id"):
        if gid not in info.index:
            continue
        ev = grp["event_ticker"].iloc[0]
        codes = sorted(set(grp["team"]))
        rh = _rule_home(ev, codes) if len(codes) == 2 else None
        mlr = ml[ml.game_id == gid]
        if rh is None or not len(mlr) or mlr.iloc[0].kalshi_p1 != mlr.iloc[0].kalshi_p1:
            continue
        pml = float(mlr.iloc[0].kalshi_p1)
        margin, extras = int(info.loc[gid, "margin"]), bool(info.loc[gid, "extras"])
        for side, sgn in (("home", +1), ("away", -1)):
            rungs = {r.threshold: r.prob for r in
                     grp[(grp.team == rh) == (side == "home")].itertuples(index=False)
                     if r.prob == r.prob}
            if 2.5 not in rungs:
                continue
            pwin = pml if sgn == 1 else 1 - pml
            sm = sgn * margin
            rows.append({"side": side, "extras": extras,
                         "imp": pwin - rungs[2.5], "emp": float(sm in (1, 2))})
    d = pd.DataFrame(rows)

    print(f"\n=== ladder 'win by 1-2' cell: implied vs empirical (n={len(d):,} sides) ===", flush=True)
    print(f"{'slice':>18} {'n':>6} {'implied':>9} {'empirical':>10} {'gap(pts)':>9} {'z':>6}", flush=True)
    slices = [("all", d), ("home side", d[d.side == "home"]), ("away side", d[d.side == "away"]),
              ("regulation", d[~d.extras]), ("extras", d[d.extras])]
    for name, s in slices:
        if not len(s):
            continue
        gap = s.emp.mean() - s.imp.mean()
        se = np.sqrt(s.emp.var() / len(s) + s.imp.var() / len(s))
        print(f"{name:>18} {len(s):>6,} {s.imp.mean():>9.4f} {s.emp.mean():>10.4f} "
              f"{gap*100:>+9.2f} {gap/se:>+6.2f}", flush=True)

    # How much of the total gap do extras explain? Counterfactual: give
    # extra-inning games the regulation empirical rate.
    emp_all, imp_all = d.emp.mean(), d.imp.mean()
    emp_reg = d[~d.extras].emp.mean()
    share_x = d.extras.mean()
    emp_cf = (1 - share_x) * emp_reg + share_x * emp_reg
    explained = (emp_all - emp_cf) / (emp_all - imp_all)
    print(f"\n  gap = {(emp_all-imp_all)*100:+.2f}pts; counterfactual (extras priced like "
          f"regulation) removes {(emp_all-emp_cf)*100:.2f}pts -> extras explain "
          f"{explained:.0%} of the under-pricing", flush=True)
    hs, as_ = d[d.side == "home"], d[d.side == "away"]
    print(f"  home-side gap {(hs.emp.mean()-hs.imp.mean())*100:+.2f}pts vs away-side "
          f"{(as_.emp.mean()-as_.imp.mean())*100:+.2f}pts (walk-off asymmetry)", flush=True)


if __name__ == "__main__":
    g = load_games()
    descriptive(g)
    ladder_decomposition(g)
