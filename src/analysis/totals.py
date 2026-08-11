"""Totals ladders: is the MLB blind spot about margins, or about baseball?

The project's one unexplained anomaly is distributional and one-sided: Kalshi
under-prices small MLB victory margins (+8.5pt on the 1-2-run cell, z=+10),
fails the margin PIT where the books pass, and loses the RPS head-to-head in
MLB but not NHL. The proposed mechanism is walk-off/extra-inning compression —
the rule that ends a game the moment the home team leads truncates the margin
distribution in a way the ladder does not model.

That mechanism makes a sharp, falsifiable prediction about a DIFFERENT market
layer. Total runs is another statistic over the same run-scoring process, but
extras push totals UP rather than compressing margins toward zero, and no
truncation rule applies. So:

  totals calibrated + margins not  -> the defect is the walk-off truncation
                                      rule specifically. The market models
                                      baseball's scoring fine; it mishandles
                                      the rule that stops the game.
  both fail                        -> Kalshi mismodels the run-scoring tail
                                      generally, and the walk-off story is at
                                      best partial.

Same machinery as the margin work: implied CDF from the "Over X.5" ladder,
interval-randomized PIT (never dropping unbracketed games — that selects on the
outcome), coherence checks, and a tail-calibration table. NBA/NHL totals serve
as controls: their scoring processes have no equivalent truncation rule, so
they should pass whatever MLB does.

Kalshi-only by design: the Odds API budget is spent, so there is no book
benchmark for this layer. The comparison that matters here is Kalshi-vs-reality
and totals-vs-margins on the SAME games, both of which are internal.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.margin_dist import pit

TOTALS = "data/processed/kalshi_total_prices.csv"
MIN_RUNGS = 3


def load():
    t = pd.read_csv(TOTALS)
    esp = (pd.read_csv("data/processed/espn_games.csv")
           [["espn_id", "home_score", "away_score"]]
           .rename(columns={"espn_id": "game_id"}))
    ml = pd.read_csv("data/processed/games_master.csv")[["game_id", "outcome_disagree"]]
    t = t.merge(esp, on="game_id", how="left").merge(ml, on="game_id", how="left")
    t = t[t.home_score.notna() & t.away_score.notna()]
    t = t[~t.outcome_disagree.fillna(False).astype(bool)]
    t["total"] = (t.home_score + t.away_score).astype(int)
    t = t[t.prob.between(0.0, 1.0)]
    return t


def implied_cdf(rungs: dict) -> dict:
    """{threshold: P(total > t)} -> {t: F(t)=P(total <= t)}, isotonic-clipped."""
    xs = sorted(rungs)
    fs = np.maximum.accumulate([1 - rungs[x] for x in xs])
    return dict(zip(xs, np.clip(fs, 0, 1)))


def coherence(t):
    print("=== 1. COHERENCE: is each ladder a valid survival function? ===", flush=True)
    print(f"  {'league':>7} {'ladders':>8} {'monotone':>10} {'adj viol':>10} "
          f"{'exec arb':>9} {'med rungs':>10}", flush=True)
    for lg, g in sorted(t.groupby("league"), key=lambda x: -len(x[1])):
        mono = viol = arb = 0
        n = 0
        rungs = []
        for gid, gg in g.groupby("game_id"):
            gg = gg.sort_values("threshold")
            if len(gg) < MIN_RUNGS:
                continue
            n += 1
            rungs.append(len(gg))
            p = gg.prob.to_numpy()
            d = np.diff(p)
            mono += int((d <= 1e-9).all())
            viol += int((d > 1e-9).sum())
            # executable: a higher threshold's BID above a lower threshold's ASK
            b, a = gg.yes_bid.to_numpy(), gg.yes_ask.to_numpy()
            if np.isfinite(b).all() and np.isfinite(a).all():
                arb += int(any(b[j] > a[i] + 1e-9
                               for i in range(len(gg)) for j in range(i + 1, len(gg))))
        if not n:
            continue
        tot_adj = sum(r - 1 for r in rungs)
        print(f"  {lg:>7} {n:>8,} {mono/n:>9.1%} {viol/max(tot_adj,1):>9.2%} "
              f"{arb/n:>8.2%} {int(np.median(rungs)):>10}", flush=True)
    print("  (monotone = P(total>t) never rises with t; exec arb = a crossing a", flush=True)
    print("   taker could actually lift, using stored bid/ask)", flush=True)


def calibration(t):
    print("\n=== 2. CONTRACT-LEVEL CALIBRATION (every threshold contract) ===", flush=True)
    print(f"  {'league':>7} {'n':>7} {'Brier':>8} {'ECE':>7}   reliability by implied bucket",
          flush=True)
    for lg, g in sorted(t.groupby("league"), key=lambda x: -len(x[1])):
        p, y = g.prob.to_numpy(), g.won.to_numpy()
        br = np.mean((p - y) ** 2)
        edges = np.array([0, .1, .25, .5, .75, .9, 1.001])
        idx = np.digitize(p, edges) - 1
        ece, cells = 0.0, []
        for k in range(len(edges) - 1):
            m = idx == k
            if m.sum() < 25:
                continue
            ece += m.mean() * abs(p[m].mean() - y[m].mean())
            cells.append(f"[{edges[k]:.2f},{edges[k+1]:.2f}) "
                         f"{p[m].mean():.3f}->{y[m].mean():.3f}(n={m.sum():,})")
        print(f"  {lg:>7} {len(g):>7,} {br:>8.4f} {ece:>7.4f}   " +
              ("  ".join(cells) if cells else "-"), flush=True)


def pit_test(t, label_extra=""):
    print(f"\n=== 3. DISTRIBUTIONAL CALIBRATION — PIT of realized totals{label_extra} ===",
          flush=True)
    print("  totals are integers and rungs sit at half-integers, so the tightest", flush=True)
    print("  bracketing interval is exact; no game is dropped for being unbracketed", flush=True)
    rng = np.random.default_rng(17)
    out = {}
    print(f"  {'league':>7} {'games':>7} {'KS':>7} {'p':>9} {'mean u':>8} "
          f"{'(0.5=unbiased)':>16}", flush=True)
    for lg, g in sorted(t.groupby("league"), key=lambda x: -len(x[1])):
        us = []
        for gid, gg in g.groupby("game_id"):
            rungs = {r.threshold: r.prob for r in gg.itertuples(index=False)
                     if r.prob == r.prob}
            if len(rungs) < MIN_RUNGS:
                continue
            u = pit(implied_cdf(rungs), int(gg.total.iloc[0]), rng)
            if u is not None:
                us.append(u)
        if len(us) < 60:
            print(f"  {lg:>7} {len(us):>7} {'-':>7} {'-':>9}   too few ladders", flush=True)
            continue
        us = np.array(us)
        ks = stats.kstest(us, "uniform")
        verdict = "REJECTS" if ks.pvalue < 0.05 else "passes"
        print(f"  {lg:>7} {len(us):>7,} {ks.statistic:>7.4f} {ks.pvalue:>9.2e} "
              f"{us.mean():>8.3f}   {verdict}", flush=True)
        out[lg] = us
    return out


def head_to_head(t):
    """The decisive contrast: totals vs margins on the SAME MLB games."""
    print("\n=== 4. THE MECHANISM TEST: totals vs margins, same games ===", flush=True)
    try:
        sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    except FileNotFoundError:
        print("  spread ladders unavailable — skipped", flush=True)
        return
    mlb_t = t[t.league == "MLB"]
    shared = set(mlb_t.game_id) & set(sp[sp.league == "MLB"].game_id)
    print(f"  MLB games with BOTH a totals ladder and a spread ladder: {len(shared):,}",
          flush=True)
    if len(shared) < 60:
        print("  too few shared games for the paired contrast", flush=True)
        return
    sub = mlb_t[mlb_t.game_id.isin(shared)]
    rng = np.random.default_rng(23)
    us = []
    for gid, gg in sub.groupby("game_id"):
        rungs = {r.threshold: r.prob for r in gg.itertuples(index=False)
                 if r.prob == r.prob}
        if len(rungs) < MIN_RUNGS:
            continue
        u = pit(implied_cdf(rungs), int(gg.total.iloc[0]), rng)
        if u is not None:
            us.append(u)
    us = np.array(us)
    ks = stats.kstest(us, "uniform")
    print(f"  totals PIT on those games: n={len(us):,}, KS={ks.statistic:.4f}, "
          f"p={ks.pvalue:.2e}, mean u={us.mean():.3f}", flush=True)
    print("  compare margin_dist.log for the MARGIN PIT on the same league", flush=True)
    print("  (MLB margins: KS=0.072, p<0.001 — rejects, mean u 0.496 = unbiased", flush=True)
    print("   location, wrong shape).", flush=True)


def extras(t):
    """Does the implied totals distribution carry the extra-innings right tail?"""
    print("\n=== 5. THE EXTRAS CHANNEL ===", flush=True)
    try:
        inn = pd.read_csv("data/processed/mlb_innings.csv")
    except FileNotFoundError:
        print("  mlb_innings.csv unavailable — skipped", flush=True)
        return
    col = next((c for c in ("innings", "n_innings", "final_inning") if c in inn.columns), None)
    if col is None or "game_id" not in inn.columns:
        print(f"  no innings column found in {list(inn.columns)[:8]} — skipped", flush=True)
        return
    g = (t[t.league == "MLB"].merge(inn[["game_id", col]], on="game_id", how="inner")
         .rename(columns={col: "innings"}))
    if g.empty:
        print("  no overlap between totals ladders and the innings file", flush=True)
        return
    g["extras"] = g.innings > 9
    per_game = g.groupby("game_id").agg(total=("total", "first"),
                                        extras=("extras", "first"))
    rate = per_game.extras.mean()
    print(f"  MLB totals games with innings data: {len(per_game):,}; "
          f"{rate:.1%} went to extras", flush=True)
    print(f"  mean total runs — regulation {per_game[~per_game.extras].total.mean():.2f} "
          f"vs extras {per_game[per_game.extras].total.mean():.2f}", flush=True)
    print("\n  right-tail calibration (the region extras feed):", flush=True)
    print(f"  {'threshold':>10} {'n':>7} {'implied P(over)':>16} {'realized':>10} "
          f"{'gap (pts)':>10} {'z':>7}", flush=True)
    for thr in sorted(g.threshold.unique()):
        gg = g[g.threshold == thr]
        if len(gg) < 80:
            continue
        p, y = gg.prob.mean(), gg.won.mean()
        se = np.sqrt(max(p * (1 - p), 1e-9) / len(gg))
        z = (y - p) / se
        print(f"  {thr:>10.1f} {len(gg):>7,} {p:>16.3f} {y:>10.3f} "
              f"{(y-p)*100:>+10.1f} {z:>+7.2f}", flush=True)
    print("  (a systematically NEGATIVE gap at high thresholds = the implied", flush=True)
    print("   right tail is too thin, i.e. the extras/blowout mass is missing)", flush=True)


def figure(us_by_league, t):
    have = [lg for lg in ("MLB", "NBA", "NHL", "WNBA") if lg in us_by_league]
    if not have:
        return
    fig, axes = plt.subplots(1, len(have) + 1, figsize=(3.4 * (len(have) + 1), 3.6))
    for ax, lg in zip(axes, have):
        u = us_by_league[lg]
        ax.hist(u, bins=20, range=(0, 1), color="tab:blue", alpha=.8,
                edgecolor="white")
        ax.axhline(len(u) / 20, color="0.35", ls="--", lw=1)
        ks = stats.kstest(u, "uniform")
        ax.set(title=f"{lg} totals PIT\nKS={ks.statistic:.3f}, p={ks.pvalue:.3g}",
               xlabel="PIT u", ylabel="games" if lg == have[0] else "")
    ax = axes[-1]
    mlb = t[t.league == "MLB"]
    if len(mlb):
        by = mlb.groupby("threshold").agg(p=("prob", "mean"), y=("won", "mean"),
                                          n=("won", "size"))
        by = by[by.n >= 80]
        ax.plot(by.index, by.p, "o-", ms=3, label="implied P(over)")
        ax.plot(by.index, by.y, "s-", ms=3, label="realized")
        ax.set(xlabel="total-runs threshold", ylabel="P(over)",
               title="MLB totals ladder vs reality")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("results/totals.png", dpi=130)
    print("\nsaved results/totals.png", flush=True)


def main():
    t = load()
    print(f"totals ladder contracts: {len(t):,} over {t.game_id.nunique():,} games; "
          f"leagues {t.league.value_counts().to_dict()}", flush=True)
    print(f"price source: {t.src.value_counts(normalize=True).round(3).to_dict()}",
          flush=True)
    coherence(t)
    calibration(t)
    us = pit_test(t)
    head_to_head(t)
    extras(t)
    figure(us, t)


if __name__ == "__main__":
    main()
