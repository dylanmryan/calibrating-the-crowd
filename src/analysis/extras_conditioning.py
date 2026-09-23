"""Is the extra-innings 1-2 run cell mispriced, or is the test conditioning on the future?

`mlb_extras.py` splits ladder contracts on `extras` — a state realized DURING the
game — and compares the pre-game implied probability against the frequency inside
each slice. The market cannot observe that state when it quotes. Conditioning a
calibration test on an outcome-correlated variable OUTSIDE the forecaster's
information set breaks the calibration identity mechanically, in both directions,
whether or not anything is mispriced. A +20.22pt extras slice, a -2.76pt
regulation slice and a null aggregate (-0.82pt, z=-1.23) is the signature of
exactly that, not of a rule the market missed.

Four sections, in the order a referee would demand them:

  S1. PLACEBO. Run the published split on forecasters that CANNOT be mispricing
      the ghost-runner rule: a constant quoting the unconditional base rate, and
      the best achievable forecast built from pre-game information only. If they
      show the same gap, the statistic has no power to detect mispricing and the
      published number is measuring the extras/margin dependence instead.

  S2. IS THERE ANYTHING TO PRICE? How predictable are extra innings before the
      first pitch, from the market's own pre-game surface — matchup closeness
      and the implied scoring environment? If extras are near-unpredictable, no
      forecaster could have priced them differently and the claim is empty.

  S3. THE REAL TEST. Calibration with respect to PRE-GAME information only. For
      any Z inside the forecaster's information set, calibration asserts
      E[realized - implied | Z] = 0. Take Z = an ex-ante estimate of extras
      propensity, cross-fitted so no game is scored by a model that saw it. A
      significant coefficient of EITHER sign is mispricing the market could
      have avoided; zero is not. It lands NEGATIVE (see S4), so the published
      sign does not survive either.

  S4. The same cut by quintile of ex-ante extras propensity — the picture S3
      summarises, and the one an editor will ask to see.

The cell is built by mlb_extras' own construction (cover-3 rung, league
convention via ladder_convention) so every number here is comparable line for
line with the published ones.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.analysis.ladder_convention import cover_line
from src.analysis.mlb_extras import load_games
from src.collect.kalshi_hist_prices import _rule_home


# ------------------------------------------------------------------ data ---
def cell_rows(g):
    """Per-side 'win by 1-2' rows: implied, realized, extras flag, covariates.

    Mirrors mlb_extras.ladder_decomposition exactly — same cover-3 rung, same
    moneyline leg — so the slices below reproduce the published table.
    """
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    sp = sp[sp.league == "MLB"]
    ml = pd.read_csv("data/processed/games_master.csv")[["game_id", "kalshi_p1"]]
    mlmap = ml.dropna(subset=["kalshi_p1"]).set_index("game_id")["kalshi_p1"].to_dict()
    info = g.set_index("game_id")[["margin", "extras", "date"]]

    rows = []
    for gid, grp in sp.groupby("game_id"):
        if gid not in info.index or gid not in mlmap:
            continue
        ev = grp["event_ticker"].iloc[0]
        codes = sorted(set(grp["team"]))
        rh = _rule_home(ev, codes) if len(codes) == 2 else None
        if rh is None:
            continue
        pml = float(mlmap[gid])
        margin = int(info.loc[gid, "margin"])
        extras = bool(info.loc[gid, "extras"])
        gdate = info.loc[gid, "date"]
        for side, sgn in (("home", +1), ("away", -1)):
            rungs = {r.threshold: r.prob for r in
                     grp[(grp.team == rh) == (side == "home")].itertuples(index=False)
                     if r.prob == r.prob}
            bc = {cover_line("MLB", t): p for t, p in rungs.items()}
            if 3 not in bc:
                continue
            pwin = pml if sgn == 1 else 1 - pml
            smg = sgn * margin
            rows.append({"game_id": gid, "date": gdate, "side": side,
                         "extras": extras, "p_home": pml,
                         "imp": pwin - bc[3], "emp": float(smg in (1, 2))})
    return pd.DataFrame(rows)


def implied_median_total():
    """Implied median total runs per game: where P(total > t) crosses 0.5.

    The scoring environment the market itself priced. Low-total games have more
    tied-after-nine endings, so this is the natural ex-ante handle on extras.
    """
    t = pd.read_csv("data/processed/kalshi_total_prices.csv", low_memory=False)
    t = t[(t.league == "MLB") & t.prob.notna()]
    out = {}
    for gid, g in t.groupby("game_id"):
        g = g.sort_values("threshold")
        th, pr = g.threshold.values, g.prob.values
        if len(th) < 2 or pr[0] < 0.5 or pr[-1] > 0.5:
            out[gid] = float(th[int(np.argmin(np.abs(pr - 0.5)))])
            continue
        i = int(np.argmax(pr <= 0.5))
        x0, x1, y0, y1 = th[i - 1], th[i], pr[i - 1], pr[i]
        out[gid] = float(x0 + (y0 - 0.5) * (x1 - x0) / (y0 - y1)) if y0 != y1 else float(x0)
    return pd.Series(out, name="med_total")


# --------------------------------------------------------------- helpers ---
def crossfit_logit(X, y, folds=5, seed=7):
    """Out-of-fold predicted probabilities: no row is scored by a model that saw it."""
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(y))
    pred = np.full(len(y), np.nan)
    for k in range(folds):
        te = idx[k::folds]
        tr = np.setdiff1d(idx, te)
        try:
            m = sm.Logit(y[tr], sm.add_constant(X[tr], has_constant="add")).fit(disp=0)
            pred[te] = m.predict(sm.add_constant(X[te], has_constant="add"))
        except Exception:
            continue
    return pred


def auc(y, s):
    ok = ~np.isnan(s)
    y, s = np.asarray(y)[ok], np.asarray(s)[ok]
    n1, n0 = y.sum(), len(y) - y.sum()
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = pd.Series(s).rank().values
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def gap(d, pcol):
    """Published statistic: empirical minus implied, on a slice."""
    return 100 * (d.emp.mean() - d[pcol].mean())


def main():
    g = load_games()
    d = cell_rows(g)
    mt = implied_median_total()
    d["med_total"] = d.game_id.map(mt)
    d["closeness"] = (d.p_home - 0.5).abs()
    d = d.dropna(subset=["imp", "emp", "med_total", "closeness"]).reset_index(drop=True)
    print(f"MLB 'win by 1-2' sides with a cover-3 rung, a moneyline and a totals "
          f"ladder: {len(d):,} ({d.game_id.nunique():,} games, "
          f"{d.extras.mean():.1%} extras)", flush=True)
    print(f"  reproduces the published cell: all {gap(d,'imp'):+.2f}pt | "
          f"regulation {gap(d[~d.extras],'imp'):+.2f}pt | "
          f"extras {gap(d[d.extras],'imp'):+.2f}pt", flush=True)

    # ---- S1 placebo ----------------------------------------------------
    print("\n=== 1. PLACEBO: run the published split on forecasters that CANNOT "
          "be missing the rule ===", flush=True)
    d["const"] = d.emp.mean()
    Xpre = d[["imp", "closeness", "med_total"]].values
    d["best_pre"] = crossfit_logit(Xpre, d.emp.values)
    d2 = d.dropna(subset=["best_pre"])
    print(f"  {'forecaster':>44}{'extras gap':>12}{'regulation gap':>16}", flush=True)
    for name, col, src in (
            ("the market (published)", "imp", d),
            ("a constant at the unconditional base rate", "const", d),
            ("best achievable forecast, PRE-GAME info only", "best_pre", d2)):
        print(f"  {name:>44}{gap(src[src.extras], col):>+11.2f}pt"
              f"{gap(src[~src.extras], col):>+15.2f}pt", flush=True)
    print("\n  READ: a constant cannot misprice a rule, and a forecast fitted on "
          "pre-game\n  information cannot use a state realized after the first pitch. "
          "Both show the\n  published effect. The statistic does not measure mispricing.",
          flush=True)
    raw = 100 * (d[d.extras].emp.mean() - d.emp.mean())
    print(f"\n  For scale: P(win by 1-2 | extras) - P(win by 1-2) = {raw:+.2f}pt. "
          f"That is the\n  extras/margin dependence alone, and it is the whole of the "
          f"published gap.", flush=True)

    # ---- S2 predictability ---------------------------------------------
    print("\n=== 2. WAS THERE ANYTHING TO PRICE? extras predictability before the "
          "first pitch ===", flush=True)
    gm = d.groupby("game_id").agg(extras=("extras", "first"),
                                  closeness=("closeness", "first"),
                                  med_total=("med_total", "first")).reset_index()
    Z = gm[["closeness", "med_total"]].values
    gm["zhat"] = crossfit_logit(Z, gm.extras.values.astype(float))
    a = auc(gm.extras.values.astype(float), gm.zhat.values)
    print(f"  games {len(gm):,}, extras rate {gm.extras.mean():.1%}", flush=True)
    print(f"  cross-fitted AUC of P(extras | matchup closeness, implied total): "
          f"{a:.3f}  (0.5 = coin flip)", flush=True)
    q = gm.dropna(subset=["zhat"]).copy()
    q["bucket"] = pd.qcut(q.zhat, 5, labels=["Q1 least", "Q2", "Q3", "Q4", "Q5 most"])
    tab = q.groupby("bucket", observed=True).agg(games=("extras", "size"),
                                                 extras_rate=("extras", "mean"),
                                                 mean_zhat=("zhat", "mean"))
    print(f"  {'ex-ante extras propensity':>26}{'games':>8}{'predicted':>11}{'actual':>9}",
          flush=True)
    for k, r in tab.iterrows():
        print(f"  {str(k):>26}{int(r.games):>8,}{r.mean_zhat:>10.1%}{r.extras_rate:>9.1%}",
              flush=True)

    # ---- S3 the real test -----------------------------------------------
    print("\n=== 3. THE REAL TEST: is the pricing error predictable from PRE-GAME "
          "information? ===", flush=True)
    d = d.merge(q[["game_id", "zhat"]], on="game_id", how="left")
    s = d.dropna(subset=["zhat"]).copy()
    s["err"] = s.emp - s.imp
    print("  calibration asserts E[realized - implied | Z] = 0 for any Z the market "
          "could see.", flush=True)
    print(f"  {'Z':>40}{'coef':>12}{'z':>8}{'p':>9}", flush=True)
    for label, cols in (("ex-ante extras propensity", ["zhat"]),
                        ("matchup closeness", ["closeness"]),
                        ("implied median total", ["med_total"]),
                        ("all three jointly", ["zhat", "closeness", "med_total"])):
        X = sm.add_constant(s[cols].values, has_constant="add")
        r = sm.OLS(s.err.values, X).fit(cov_type="cluster",
                                        cov_kwds={"groups": s.date.values})
        for j, c in enumerate(cols, start=1):
            nm = f"{label} [{c}]" if len(cols) > 1 else label
            print(f"  {nm:>40}{r.params[j]:>+12.4f}{r.tvalues[j]:>+8.2f}"
                  f"{r.pvalues[j]:>9.3f}", flush=True)

    # the headline Z under every error structure, so the replacement claim below
    # does not rest on one clustering choice.
    X = sm.add_constant(s[["zhat"]].values, has_constant="add")
    print("\n  the headline Z (ex-ante extras propensity) under every error structure:",
          flush=True)
    for lab, kw in (("date-clustered (house convention)",
                     dict(cov_type="cluster", cov_kwds={"groups": s.date.values})),
                    ("game-clustered", dict(cov_type="cluster",
                                            cov_kwds={"groups": s.game_id.values})),
                    ("iid", {})):
        rr = sm.OLS(s.err.values, X).fit(**kw)
        print(f"  {lab:>40}{rr.params[1]:>+12.4f}{rr.tvalues[1]:>+8.2f}"
              f"{rr.pvalues[1]:>9.3f}", flush=True)

    # does the market's own price already move with extras propensity?
    X = sm.add_constant(s[["zhat"]].values, has_constant="add")
    rimp = sm.OLS(s.imp.values, X).fit(cov_type="cluster",
                                       cov_kwds={"groups": s.game_id.values})
    print(f"\n  and does the PRICE itself move with ex-ante extras propensity? "
          f"coef={rimp.params[1]:+.4f} (z={rimp.tvalues[1]:+.2f}, p={rimp.pvalues[1]:.3f})",
          flush=True)

    # ---- S4 quintile picture ---------------------------------------------
    print("\n=== 4. THE SAME CUT, BY EX-ANTE EXTRAS PROPENSITY ===", flush=True)
    s["bucket"] = pd.qcut(s.zhat, 5, labels=["Q1 least", "Q2", "Q3", "Q4", "Q5 most"])
    print(f"  {'ex-ante extras propensity':>26}{'sides':>8}{'implied':>10}"
          f"{'realized':>10}{'gap':>10}", flush=True)
    for k, sub in s.groupby("bucket", observed=True):
        print(f"  {str(k):>26}{len(sub):>8,}{sub.imp.mean():>10.4f}"
              f"{sub.emp.mean():>10.4f}{gap(sub,'imp'):>+9.2f}pt", flush=True)
    print("\n  READ: if the market had missed the ghost-runner rule, the gap would "
          "grow with\n  ex-ante extras propensity — the games a forecaster could have "
          "seen coming. It does\n  the OPPOSITE: the column falls monotonically and "
          "S3's coefficient is negative at\n  z=-3.0 date-clustered (p=0.003; -2.9 "
          "game-clustered, -2.4 iid). So the published\n  SIGN does not survive the "
          "correction either. On pre-game information the market\n  slightly "
          "OVER-prices the narrow-margin cell in extras-prone games — a ~4pt swing\n  "
          "across the whole propensity range. Small, robust, and opposite to the "
          "retracted\n  claim. Report it as a sign reversal, not as a null.", flush=True)


if __name__ == "__main__":
    main()
