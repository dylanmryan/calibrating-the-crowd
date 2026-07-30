"""Distributional calibration of spread-ladder implied margin distributions (PIT).

Each game's ladder implies a CDF over the final margin M = home - away:
  home rung t:  F(t)  = 1 - P(home wins by > t)
  away rung t:  F(-t) = P(away wins by > t)
  moneyline:    F(0)  = 1 - P(home wins)          (no ties in these leagues)
Margins are integers and rungs sit at half-integers, so P(M <= m) = F(m + 0.5)
exactly. Randomized PIT: u = F(m-.5) + V*(F(m+.5)-F(m-.5)), V~U(0,1).
If the implied distributions are correct, u ~ Uniform(0,1)  (KS test).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def implied_cdf(home_rungs: dict, away_rungs: dict, p_home_win: float | None):
    """Grid {x: F(x)} at half-integers (and 0 from the moneyline), isotonic-clipped."""
    pts = {}
    for t, p in away_rungs.items():
        pts[-t] = p                      # F(-t) = P(M < -t)
    if p_home_win is not None:
        pts[0.0] = 1 - p_home_win
    for t, p in home_rungs.items():
        pts[t] = 1 - p                   # F(t) = 1 - P(M > t)
    xs = sorted(pts)
    fs = np.maximum.accumulate([pts[x] for x in xs])   # enforce monotone CDF
    return dict(zip(xs, np.clip(fs, 0, 1)))


def pit(cdf: dict, m: int, rng) -> float | None:
    """Interval-randomized PIT: u ~ U(F(a), F(b)) where (a, b) is the tightest grid
    interval containing m (tails -> 0/1). Valid under the null for ANY grid: the
    interval's null probability equals its F-mass, so u is unconditionally uniform.
    Crucially, no game is dropped — dropping unbracketed margins selects on the
    outcome and fakes rejection in short-ladder leagues."""
    if not cdf:
        return None
    lo = max((f for x, f in cdf.items() if x < m), default=0.0)
    # x >= m (not x > m): when the margin TIES a grid threshold (possible for
    # the books' integer lines, impossible for Kalshi's half-integer rungs),
    # the interval must be the atom's own (F(m-), F(m)] — the strict version
    # spanned two cells and smoothed u toward uniform exactly for the books
    hi = min((f for x, f in cdf.items() if x >= m), default=1.0)
    if hi < lo:
        return None
    return lo + rng.uniform() * (hi - lo)


def main():
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    esp = pd.read_csv("data/processed/espn_games.csv")[
        ["espn_id", "home_score", "away_score", "home_abbr"]].rename(columns={"espn_id": "game_id"})
    ml = pd.read_csv("data/processed/games_master.csv")[
        ["game_id", "kalshi_p1", "outcome_disagree"]]
    from src.collect.kalshi_hist_prices import _rule_home

    rng = np.random.default_rng(11)
    us, leagues = [], []
    for (gid, lg), g in sp.groupby(["game_id", "league"]):
        row = esp[esp.game_id == gid]
        if len(row) != 1 or row.iloc[0].home_score != row.iloc[0].home_score:
            continue
        mlrow = ml[ml.game_id == gid]
        if len(mlrow) and bool(mlrow.iloc[0].outcome_disagree):
            continue
        margin = int(row.iloc[0].home_score - row.iloc[0].away_score)
        ev = g["event_ticker"].iloc[0]
        codes = sorted(set(g["team"]))
        if len(codes) != 2:
            continue
        rh = _rule_home(ev, codes)
        if rh is None:
            continue
        home = {r.threshold: r.prob for r in g[g.team == rh].itertuples(index=False)
                if r.prob == r.prob}
        away = {r.threshold: r.prob for r in g[g.team != rh].itertuples(index=False)
                if r.prob == r.prob}
        if len(home) < 1 or len(away) < 1:
            continue
        pml = float(mlrow.iloc[0].kalshi_p1) if len(mlrow) else None
        if pml is not None and pml != pml:
            pml = None
        u = pit(implied_cdf(home, away, pml), margin, rng)
        if u is not None:
            us.append(u); leagues.append(lg)

    us = np.asarray(us)
    print(f"games with ladder bracketing the realized margin: {len(us):,}", flush=True)
    ks = stats.kstest(us, "uniform")
    print(f"PIT uniformity (all): KS={ks.statistic:.4f}  p={ks.pvalue:.3f}  "
          f"mean={us.mean():.3f} (0.5=unbiased)", flush=True)
    lg = pd.Series(leagues)
    for l in sorted(set(leagues)):
        uu = us[lg.values == l]
        k = stats.kstest(uu, "uniform")
        print(f"  {l:5} n={len(uu):5,}  KS={k.statistic:.4f} p={k.pvalue:.3f} mean={uu.mean():.3f}", flush=True)

    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.hist(us, bins=20, density=True, color="tab:purple", alpha=0.75, edgecolor="white")
    ax.axhline(1, color="k", ls="--", lw=1, label="perfect (uniform)")
    ax.set(xlabel="PIT value of realized margin under implied CDF", ylabel="density",
           title=f"Are the implied margin distributions correct? (n={len(us):,}, KS p={ks.pvalue:.3f})")
    ax.legend()
    fig.tight_layout(); fig.savefig("results/margin_pit.png", dpi=130)
    print("saved results/margin_pit.png", flush=True)


if __name__ == "__main__":
    main()
