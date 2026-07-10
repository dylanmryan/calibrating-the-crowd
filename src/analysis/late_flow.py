"""What carries Kalshi's information whisper — the level or the late flow?

Encompassing found a small Kalshi increment beyond the book (LR p=0.004, NBA-
driven). Mechanism question: if it reflects informed order flow migrating to the
exchange, the information should live in Kalshi's LATE PRICE MOVEMENT (what
traders did in the final hours), not in its stale level a day out.

Test: decompose the closing log-odds into level + flow,
    logit(home_won) ~ logit(book) + logit(K_24h) + [logit(K_0) - logit(K_24h)]
with date-clustered SEs. A significant Δ coefficient given the book and the
24h level means the final-day flow itself predicts outcomes beyond the closing
book consensus. Run pooled and NBA-only (where the whisper concentrates).
Requires kalshi_horizons.csv (home-side trade paths at 7 horizons).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


def lo(p):
    return np.log(np.clip(np.asarray(p, float), 0.01, 0.99) /
                  (1 - np.clip(np.asarray(p, float), 0.01, 0.99)))


def run(d, label):
    dates = pd.to_datetime(d["start_utc"], utc=True, format="ISO8601").dt.date.values
    y = d["home_won"].values.astype(int)
    X = sm.add_constant(np.column_stack([
        lo(d.book_p1), lo(d.p_h1440), lo(d.p_h0) - lo(d.p_h1440)]))
    r = sm.Logit(y, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": dates})
    names = ["book", "K 24h level", "K flow 24h->0"]
    print(f"\n  --- {label} (n={len(d):,}) ---", flush=True)
    for k, nm in enumerate(names, start=1):
        # LR exclusion (plain MLE)
        keep = [i for i in range(1, 4) if i != k]
        rr = sm.Logit(y, X[:, [0] + keep]).fit(disp=0)
        full = sm.Logit(y, X).fit(disp=0)
        p_lr = 1 - stats.chi2.cdf(2 * (full.llf - rr.llf), df=1)
        print(f"    {nm:14} weight={r.params[k]:+.3f}  clustered z={r.tvalues[k]:+.2f} "
              f"p={r.pvalues[k]:.3f}   LR excl. p={p_lr:.3f}", flush=True)


def main():
    h = pd.read_csv("data/processed/kalshi_horizons.csv")
    m = pd.read_csv("data/processed/games_master.csv")[
        ["game_id", "book_p1", "outcome", "outcome_disagree"]]
    d = h.merge(m, on="game_id")
    d = d[d.outcome.notna() & ~d.outcome_disagree.fillna(False) & d.book_p1.notna()]
    d = d.dropna(subset=["p_h1440", "p_h0"])
    d = d[d.n_trades >= 10]          # need a real trade path, not one stale print
    d["home_won"] = (d.outcome == 1).astype(int)
    print(f"games with 24h price path + book line: {len(d):,}", flush=True)
    print(f"mean |flow| 24h->start: {np.abs(d.p_h0 - d.p_h1440).mean()*100:.2f}pts", flush=True)

    run(d, "pooled, all leagues")
    run(d[d.league == "NBA"], "NBA only (whisper league)")
    run(d[d.league != "NBA"], "all except NBA")

    # model-free complement: when the last-day flow is large, does it point at truth?
    d["flow"] = d.p_h0 - d.p_h1440
    big = d[d.flow.abs() >= 0.03]
    toward = ((big.flow > 0) == (big.home_won == 1)).mean()
    print(f"\n  games with |flow| >= 3pts: n={len(big):,}; flow points toward the "
          f"eventual winner {toward:.1%} of the time "
          f"(coin flip = the flow is noise)", flush=True)


if __name__ == "__main__":
    main()
