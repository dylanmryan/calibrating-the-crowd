"""Layer 2 of the proposal: the STANDARD point spread, priced near 50/50.

The main line is the books' chosen threshold that splits the margin
distribution in half — we identify it per game as the alternate point whose
de-vigged cover probability is closest to 0.5. Questions: (1) is P(cover)
calibrated in the tight 40-60% band where every game lives? (2) does Kalshi's
ladder agree with the books at the main line?
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.compare import brier, ece
from src.analysis.ladder_vs_books import _book_ladder, _kalshi_ladder, _margins


def main():
    ab = pd.read_csv("data/processed/sportsbook_alt_spreads.csv")
    mg = _margins()
    ab = ab[ab.game_id.isin(mg.index) & (ab.n_books >= 2)].copy()
    # main line = home point with cover prob closest to 1/2
    ab["dist"] = (ab.prob_home - 0.5).abs()
    main_line = ab.loc[ab.groupby("game_id")["dist"].idxmin()].copy()
    main_line["margin"] = main_line.game_id.map(mg)
    # pushes (margin lands exactly on an integer line) are refunds, and the
    # de-vigged two-way prob is push-conditional — exclude them, don't score
    # them as losses
    pushes = (main_line.margin == -main_line.point).sum()
    main_line = main_line[main_line.margin != -main_line.point]
    print(f"pushes excluded: {pushes}", flush=True)
    main_line["cover"] = (main_line.margin > -main_line.point).astype(float)
    print(f"main lines: {len(main_line):,} games "
          f"({dict(main_line.groupby('league').size())})", flush=True)
    print(f"mean |main line prob - 0.5| = {main_line.dist.mean()*100:.2f}pts", flush=True)

    print("\n=== book P(cover) calibration at the main line ===", flush=True)
    for lg, g in list(main_line.groupby("league")) + [("ALL", main_line)]:
        p, y = g.prob_home.values, g.cover.values
        print(f"  {lg:4} n={len(g):5,}  mean pred={p.mean():.4f}  empirical cover={y.mean():.4f}  "
              f"Brier={brier(p, y):.4f}  ECE={ece(p, y):.4f}", flush=True)
    print("  (a fair coin forecaster scores Brier 0.2500 here — spreads live at 50/50)", flush=True)

    # Kalshi at the same threshold
    k = _kalshi_ladder()
    kk = k.set_index(["game_id", "side", "threshold"])["k_prob"]
    rows = []
    for r in main_line.itertuples(index=False):
        if r.point < 0:
            key = (r.game_id, "home", -r.point)
            kp = kk.get(key)
            kp = kp if kp is None or np.isscalar(kp) else None
        else:
            key = (r.game_id, "away", r.point)
            kp = kk.get(key)
            kp = (1 - kp) if kp is not None and np.isscalar(kp) else None
        if kp is not None and kp == kp:
            rows.append({"league": r.league, "b": r.prob_home, "k": float(kp), "cover": r.cover})
    d = pd.DataFrame(rows)
    print(f"\n=== Kalshi vs book at the main line (matched rungs, n={len(d):,}) ===", flush=True)
    print(f"  corr={d.b.corr(d.k):.3f}  mean(K-B)={100*(d.k-d.b).mean():+.2f}pts", flush=True)
    for src, col in (("Book", "b"), ("Kalshi", "k")):
        print(f"  {src:6} Brier={brier(d[col], d.cover):.4f}  ECE={ece(d[col].values, d.cover.values):.4f}", flush=True)
    for lg, g in d.groupby("league"):
        print(f"    {lg}: n={len(g):,}  mean(K-B)={100*(g.k-g.b).mean():+.2f}pts  "
              f"Brier K={brier(g.k, g.cover):.4f} B={brier(g.b, g.cover):.4f}", flush=True)


if __name__ == "__main__":
    main()
