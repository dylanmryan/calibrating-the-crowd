"""Referee-proofing battery: the attack surfaces a skeptical reviewer would probe.

1. SELECTION: do conclusions depend on the all-three joint set? Re-test
   Kalshi-vs-Polymarket on the wider both-priced set, and Kalshi calibration on
   ALL its priced games (incl. leagues Polymarket never listed).
2. DEPENDENCE: stacked both-sides calibration doubles n with p2 = 1-p1. Redo
   slope/ECE on the home side only.
3. SCORING RULE: Brier is one rule. Log score (tail-sensitive) as robustness,
   with date-clustered pairwise DM.
4. CORP decomposition (Dimitriadis-Gneiting-Jordan 2021): isotonic (PAV)
   reliability instead of arbitrary bins — Brier = MCB (miscalibration)
   - DSC (discrimination) + UNC, with no binning choices to dispute.
5. ECE's bin dependence, made explicit. ECE is the calibration number readers
   recognise, and it is an artifact of its bin count: the LEVEL roughly triples
   from 5 to 20 bins and the cross-venue RANKING is not stable either. Nothing
   in this project ranks venues on ECE — that is what MCB (§4) and the Brier
   differentials are for — but ECE appears in summary tables, so the sweep and
   the binomial noise floor are printed here and the reading rule is stated:
   quote ECE as a level against its floor, never as a comparison.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.compare import brier, cal_slope, ece, stacked
from src.analysis.rigor import cluster_dm
from src.analysis.power import KMDE
from src.analysis.three_way import SRC, load


def pav(p, y):
    """Pool-adjacent-violators: isotonic fit of y on sorted p (CORP recalibration)."""
    order = np.argsort(p, kind="stable")
    yy = y[order].astype(float)
    val, wt = list(yy), [1.0] * len(yy)
    i = 0
    vals, wts = [], []
    for v in yy:
        vals.append(v); wts.append(1.0)
        while len(vals) > 1 and vals[-2] > vals[-1] - 1e-12:
            w = wts[-1] + wts[-2]
            m = (vals[-1] * wts[-1] + vals[-2] * wts[-2]) / w
            vals = vals[:-2] + [m]; wts = wts[:-2] + [w]
    fit = np.repeat(vals, [int(w) for w in wts])
    out = np.empty_like(fit)
    out[order] = fit
    return out


def corp(p, y):
    p, y = np.asarray(p, float), np.asarray(y, float)
    c = pav(p, y)
    s = brier(p, y)
    s_c = brier(c, y)
    s_r = brier(np.full_like(y, y.mean()), y)
    return {"brier": s, "MCB": s - s_c, "DSC": s_r - s_c, "UNC": s_r}


def ece_noise_floor(d, c1, c2, sims=400, seed=17):
    """Mean ECE a PERFECTLY calibrated forecaster of these prices would show from
    binning noise alone. Games are simulated once and both sides stacked, so the
    floor inherits the same mirrored-side dependence the observed ECE has.

    Same construction as oos_verification.ece_noise_floor, which applies it to
    the holdout; the frozen sample needs it for the identical reason.
    """
    rng = np.random.default_rng(seed)
    p1 = d[c1].values
    es = []
    for _ in range(sims):
        y = (rng.random(len(p1)) < p1).astype(float)
        p = np.concatenate([p1, d[c2].values])
        yy = np.concatenate([y, 1 - y])
        es.append(ece(p, yy))
    return float(np.mean(es))


def ece_binning(d3):
    print("\n=== 5. ECE is a bin artifact; MCB is not ===", flush=True)
    print(f"  {'nbins':>7}" + "".join(f"{s:>12}" for s in SRC) +
          "   best on ECE", flush=True)
    for nb in (5, 8, 10, 12, 15, 20, 25):
        vals = {}
        for name, (c1, c2) in SRC.items():
            p_, y_ = stacked(d3, c1, c2)
            vals[name] = ece(p_, y_, nbins=nb)
        best = min(vals, key=vals.get)
        print(f"  {nb:>7}" + "".join(f"{vals[s]:>12.4f}" for s in SRC) +
              f"   {best}", flush=True)
    print("\n  The level roughly triples from 5 to 20 bins and the 'best' venue changes", flush=True)
    print("  with the bin count. That is the bins moving, not the venues.", flush=True)

    print("\n  ECE at the reported 10 bins, against its binomial noise floor:", flush=True)
    print(f"  {'source':11}{'ECE':>9}{'noise floor':>14}{'ratio':>8}", flush=True)
    for name, (c1, c2) in SRC.items():
        p_, y_ = stacked(d3, c1, c2)
        e = ece(p_, y_)
        f = ece_noise_floor(d3, c1, c2)
        print(f"  {name:11}{e:>9.4f}{f:>14.4f}{e/f:>8.2f}x", flush=True)
    print("\n  READING RULE: report ECE as a LEVEL against this floor, never as a", flush=True)
    print("  ranking. The miscalibration statistic that carries a comparison is MCB", flush=True)
    print("  (section 4), which is isotonic and has no bin count to choose.", flush=True)


def main():
    # ---------- 1. selection ----------
    m = pd.read_csv("data/processed/games_master.csv")
    m = m[m["outcome"].notna() & ~m["outcome_disagree"].fillna(False)].copy()
    m["home_won"] = (m["outcome"] == 1).astype(int)
    both = m[m.kalshi_p1.notna() & m.poly_p1.notna()]
    d3 = load()
    print("=== 1. selection: does the joint-set filter drive anything? ===", flush=True)
    for label, g in (("both-priced (wide)", both), ("all-three (paper set)", d3)):
        y = g["home_won"].values
        dt = pd.to_datetime(g["start_utc"], utc=True, format="ISO8601").dt.date.values
        dbar, se, z, p, _ = cluster_dm(g["kalshi_p1"], g["poly_p1"], y, dt)
        print(f"  {label:22} n={len(g):5,}  Brier K={brier(g.kalshi_p1,y):.4f} "
              f"P={brier(g.poly_p1,y):.4f}  DM z={z:+.2f} p={p:.3f}", flush=True)
    kal = m[m.kalshi_p1.notna()]
    for label, g in (("Kalshi, all priced", kal), ("Kalshi, joint set", d3)):
        p_, y_ = stacked(g, "kalshi_p1", "kalshi_p2")
        print(f"  {label:22} n={len(g):5,}  slope={cal_slope(p_,y_):.3f}  ECE={ece(p_,y_):.4f}", flush=True)

    # ---------- 2. home-side-only ----------
    print("\n=== 2. home-side-only calibration (no stacked-sides dependence) ===", flush=True)
    y3 = d3["home_won"].values
    for name, (c1, c2) in SRC.items():
        p_, y_ = stacked(d3, c1, c2)
        print(f"  {name:11} stacked slope={cal_slope(p_,y_):.3f} ECE={ece(p_,y_):.4f}   "
              f"home-only slope={cal_slope(d3[c1].values, y3):.3f} "
              f"ECE={ece(d3[c1].values, y3):.4f}", flush=True)

    # ---------- 3. log score ----------
    print("\n=== 3. log-score robustness (date-clustered pairwise DM) ===", flush=True)
    dt3 = pd.to_datetime(d3["start_utc"], utc=True, format="ISO8601").dt.date.values
    ll = {}
    for name, (c1, _) in SRC.items():
        p_ = np.clip(d3[c1].values, 1e-4, 1 - 1e-4)
        ll[name] = -(y3 * np.log(p_) + (1 - y3) * np.log(1 - p_))
        print(f"  {name:11} mean log loss = {ll[name].mean():.4f}", flush=True)
    names = list(SRC)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            dd = ll[a] - ll[b]
            g = pd.DataFrame({"d": dd - dd.mean(), "c": dt3}).groupby("c")["d"].sum()
            se = np.sqrt((g ** 2).sum()) / len(dd)
            z = dd.mean() / se
            print(f"  {a} - {b}: z={z:+.2f} p={2*(1-stats.norm.cdf(abs(z))):.3f}", flush=True)

    # ---------- 4b. season-segment split ----------
    print("\n=== 4b. regular season vs postseason (ESPN season_type) ===", flush=True)
    esp = pd.read_csv("data/processed/espn_games.csv")
    if "season_type" not in esp.columns or esp["season_type"].isna().all():
        print("  SKIPPED: espn_games.csv carries no season_type — "
              "re-run src.collect.espn (collector stores it since 2026-08-28)", flush=True)
    else:
        st = esp.rename(columns={"espn_id": "game_id"})[["game_id", "season_type"]]
        g3 = d3.merge(st, on="game_id", how="left")
        for label, seg in (("regular season", g3[g3.season_type == 2]),
                           ("postseason", g3[g3.season_type == 3])):
            if len(seg) < 150:
                print(f"  {label}: n={len(seg)} — too small to read", flush=True)
                continue
            y_ = seg["home_won"].values
            dts = seg["start_utc"].astype(str).str[:10].values
            briers = "  ".join(f"{n[0]}={brier(seg[c[0]], y_):.4f}" for n, c in SRC.items())
            worst_z, worst_ci, mde = 0.0, 0.0, 0.0
            for a, b in (("kalshi_p1", "poly_p1"), ("kalshi_p1", "book_p1"),
                         ("poly_p1", "book_p1")):
                dbar, se, z, pv, (lo, hi) = cluster_dm(seg[a], seg[b], y_, dts)
                worst_z = max(worst_z, abs(z))
                worst_ci = max(worst_ci, abs(lo), abs(hi))
                mde = max(mde, KMDE * se)
            eq = "EQUIV@1e-3" if worst_ci <= 1e-3 else "(not resolved)"
            print(f"  {label:15} n={len(seg):5,}  {briers}  worst|z|={worst_z:.2f}  "
                  f"delta_min={worst_ci*1000:.2f}e-3 {eq}  MDE={mde*1000:.2f}e-3", flush=True)
        print("  (robustness: the dead heat is not a playoff-attention artifact;", flush=True)
        print("   the postseason cell is the smaller one — quote its MDE)", flush=True)

    # ---------- 4. CORP ----------
    print("\n=== 4. CORP (isotonic) decomposition, no binning choices ===", flush=True)
    print(f"  {'source':11} {'Brier':>8} {'MCB(cal)':>10} {'DSC(disc)':>10} {'UNC':>8}", flush=True)
    for name, (c1, c2) in SRC.items():
        p_, y_ = stacked(d3, c1, c2)
        r = corp(p_, y_)
        print(f"  {name:11} {r['brier']:>8.4f} {r['MCB']*1000:>9.2f}e-3 "
              f"{r['DSC']*1000:>9.1f}e-3 {r['UNC']:>8.4f}", flush=True)
    print("  MCB is the project's reported miscalibration statistic: isotonic, so it", flush=True)
    print("  has no bin count to dispute. Section 5 shows why that matters.", flush=True)

    # ---------- 5. ECE bin dependence ----------
    ece_binning(d3)


if __name__ == "__main__":
    main()
