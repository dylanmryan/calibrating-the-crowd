"""Model-benchmark leg: how much of market accuracy is just public statistics?

A deliberately naive fourth forecaster — walk-forward Elo per league built from
ESPN win/loss results only (K=20; home advantage estimated on an expanding
window; ratings regressed 1/3 to the mean across season gaps; no look-ahead
anywhere) — evaluated on the same clean three-way games. The gap between this
floor and the markets measures the information the market ecosystem adds
beyond public won-lost records; encompassing asks whether the model retains
ANY increment once the book is known (it shouldn't). MLB is expected to be the
weakest fit (win/loss Elo ignores starting pitchers) — that is itself
informative about where market information lives.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.compare import brier, ece
from src.analysis.three_way import SRC, load
from src.analysis.rigor import cluster_dm
from src.analysis.decomposition import slope_ci

K_ELO = 20.0
SEASON_GAP_DAYS = 60
REGRESS = 1 / 3           # shrink toward 1500 across a season gap
BURN = {"MLB": 10, "NBA": 10, "NHL": 10, "WNBA": 8, "NFL": 4, "CFB": 4, "CBB-M": 4}


def elo_forecasts(espn, k=K_ELO):
    """One walk-forward pass per league -> model prob of a home win per game."""
    out = []
    for lg, g in espn.groupby("league"):
        g = g.sort_values("start_utc")
        rating, played, last = {}, {}, {}
        hw, hn = 55.0, 100.0                      # Beta(55,45) prior on home-win rate
        for r in g.itertuples(index=False):
            h, a = r.home_team, r.away_team
            t = pd.Timestamp(r.start_utc)
            for team in (h, a):
                rating.setdefault(team, 1500.0)
                played.setdefault(team, 0)
                if team in last and (t - last[team]).days > SEASON_GAP_DAYS:
                    rating[team] = 1500.0 + (1 - REGRESS) * (rating[team] - 1500.0)
            H = 400 * np.log10(hw / (hn - hw) )   # expanding-window home edge
            e = 1 / (1 + 10 ** (-((rating[h] - rating[a] + H) / 400)))
            if min(played[h], played[a]) >= BURN.get(lg, 10):
                out.append({"game_id": r.espn_id, "model_p1": e})
            y = 1.0 if r.winner == "home" else 0.0
            rating[h] += k * (y - e)
            rating[a] -= k * (y - e)
            played[h] += 1; played[a] += 1
            last[h] = last[a] = t
            hw += y; hn += 1
    return pd.DataFrame(out)


def logodds(p):
    p = np.clip(np.asarray(p, float), 0.01, 0.99)
    return np.log(p / (1 - p))


def main():
    espn = pd.read_csv("data/processed/espn_games.csv")
    espn = espn[espn.winner.isin(["home", "away"]) & espn.start_utc.notna()].copy()
    print(f"ESPN training games: {len(espn):,} across {espn.league.nunique()} leagues", flush=True)

    model = elo_forecasts(espn)
    d = load().merge(model, on="game_id", how="inner")
    d["date"] = d.start_utc.astype(str).str[:10]
    y = d.home_won.values
    print(f"evaluation set (three-way clean ∩ model burn-in): {len(d):,} games", flush=True)

    for kk in (10.0, 32.0):   # K-factor robustness, same evaluation games
        alt = load().merge(elo_forecasts(espn, k=kk), on="game_id", how="inner")
        print(f"  robustness K={kk:.0f}: model Brier {brier(alt.model_p1, (alt.outcome==1).astype(int)):.4f} "
              f"(n={len(alt):,})", flush=True)

    print("\n=== the information hierarchy (same games) ===", flush=True)
    cols = {"Elo model": "model_p1", **{k: v[0] for k, v in SRC.items()}}
    print(f"  {'source':11} {'Brier':>8} {'ECE':>8} {'slope':>7}", flush=True)
    for name, c in cols.items():
        s, lo, hi = slope_ci(d[c].values, y)
        print(f"  {name:11} {brier(d[c].values, y):>8.4f} {ece(d[c].values, y):>8.4f} "
              f"{s:>7.3f} ({lo:.2f},{hi:.2f})", flush=True)

    print("\n=== clustered DM: model vs each market (dbar>0 => model worse) ===", flush=True)
    for name, (c1, _) in SRC.items():
        dbar, se, z, p, _ = cluster_dm(d.model_p1.values, d[c1].values, y, d.date.values)
        print(f"  model vs {name:11} dBrier={dbar*1000:+.2f}e-3  z={z:+.2f}  p={p:.4f}", flush=True)

    print("\n=== per-league Brier (model | K / P / B) ===", flush=True)
    for lg, g in sorted(d.groupby("league"), key=lambda t: -len(t[1])):
        yy = g.home_won.values
        row = " / ".join(f"{brier(g[c[0]].values, yy):.4f}" for c in SRC.values())
        print(f"  {lg:6} n={len(g):5}  model {brier(g.model_p1.values, yy):.4f}  | {row}", flush=True)

    print("\n=== encompassing: does anything survive the book? (log-odds logits, date-clustered) ===", flush=True)
    for lab, X_cols in [("book | model", ["book_p1", "model_p1"]),
                        ("model | book", ["model_p1", "book_p1"]),
                        ("kalshi | model+book", ["kalshi_p1", "model_p1", "book_p1"])]:
        X = sm.add_constant(np.column_stack([logodds(d[c]) for c in X_cols]))
        r = sm.Logit(y, X).fit(disp=0, cov_type="cluster",
                               cov_kwds={"groups": d.date.values})
        terms = "  ".join(f"{c.split('_')[0]}:{r.params[i+1]:+.2f}(z={r.tvalues[i+1]:+.1f})"
                          for i, c in enumerate(X_cols))
        print(f"  {lab:22} {terms}", flush=True)

    fig, ax = plt.subplots(figsize=(8.5, 5))
    leagues = [lg for lg, _ in sorted(d.groupby("league"), key=lambda t: -len(t[1]))]
    x = np.arange(len(leagues))
    w = 0.2
    series = [("Elo model", "model_p1", "0.55"), ("Kalshi", "kalshi_p1", "tab:blue"),
              ("Polymarket", "poly_p1", "tab:orange"), ("Sportsbook", "book_p1", "tab:green")]
    for i, (name, c, color) in enumerate(series):
        vals = [brier(d[d.league == lg][c].values, d[d.league == lg].home_won.values)
                for lg in leagues]
        ax.bar(x + (i - 1.5) * w, vals, w, label=name, color=color)
    ax.set_xticks(x, leagues)
    ax.set(ylabel="Brier (lower = better)",
           title="Public-statistics floor vs the markets (walk-forward Elo)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig("results/model_benchmark.png", dpi=130)
    print("\nsaved results/model_benchmark.png", flush=True)


if __name__ == "__main__":
    main()
