"""PIT of the BOOKS' implied margin distributions — the symmetric test.

We rejected Kalshi's MLB margin distributions (PIT KS p<0.001) and traced the
shape error to the walk-off/extras spike. The books priced that cell correctly.
Symmetric question: is the books' whole implied margin DISTRIBUTION correct?
Same interval-randomized PIT machinery (margin_dist.pit), rungs from the books'
de-vigged alternate spread lines, F(0) from the de-vigged moneyline.

Prediction: MLB books pass (or reject far more mildly) where Kalshi rejects.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.margin_dist import implied_cdf, pit
from src.analysis.ladder_convention import BOOK


def main():
    ab = pd.read_csv("data/processed/sportsbook_alt_spreads.csv")
    esp = pd.read_csv("data/processed/espn_games.csv")[
        ["espn_id", "home_score", "away_score"]].rename(columns={"espn_id": "game_id"})
    ml = pd.read_csv("data/processed/games_master.csv")[
        ["game_id", "book_p1", "outcome_disagree"]]
    ab = ab.merge(esp, on="game_id").merge(ml, on="game_id", how="left")
    ab = ab[ab.home_score.notna() & ~ab.outcome_disagree.fillna(False)]

    rng = np.random.default_rng(11)
    us, lgs = [], []
    for (gid, lg), g in ab.groupby(["game_id", "league"]):
        margin = int(g.iloc[0].home_score - g.iloc[0].away_score)
        # home rung t: P(M > t) = prob_home at point -t ; away rung t: 1 - prob_home at +t
        home = {-p.point: p.prob_home for p in g[g.point < 0].itertuples(index=False)}
        away = {p.point: 1 - p.prob_home for p in g[g.point > 0].itertuples(index=False)}
        if not home or not away:
            continue
        pml = g.iloc[0].book_p1
        pml = float(pml) if pml == pml else None
        u = pit(implied_cdf(home, away, pml, BOOK), margin, rng)
        if u is not None:
            us.append(u); lgs.append(lg)

    us, lgs = np.asarray(us), pd.Series(lgs)
    print(f"book ladders PIT-able: {len(us):,} games", flush=True)
    for l in sorted(lgs.unique()):
        uu = us[lgs.values == l]
        k = stats.kstest(uu, "uniform")
        print(f"  BOOK {l:4} n={len(uu):5,}  KS={k.statistic:.4f} p={k.pvalue:.3f} mean={uu.mean():.3f}", flush=True)
    print("  (Kalshi benchmark, same test: see margin_dist.log — quoting it here", flush=True)
    print("   went stale once already. Post ladder-convention fix Kalshi's MLB PIT", flush=True)
    print("   passes while the books' rejects, but the book ladder is far denser", flush=True)
    print("   and includes push lines, so it is the better-powered test.)", flush=True)


if __name__ == "__main__":
    main()
