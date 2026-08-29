"""Registered out-of-sample verification of the paper's core claims.

The protocol is docs/registered-claims.md (committed f915794, 2026-08-28,
BEFORE the holdout was pulled). It fixes eight claims R1-R8, their samples,
statistics, and consistency criteria; this module evaluates exactly that
list, once, and reports the scorecard whichever way it comes out. Nothing
here may drift from the registered file; any extra cut is labeled
exploratory and does not join the scorecard.

Holdout: games with official start >= 2026-08-12 00:00 UTC — the day after
the final pre-freeze master build. No such game was collected locally or
analyzed anywhere in the project before registration. The sportsbook leg
comes only from the VPS live feed (no historical Odds API calls).

Power expectation, registered in advance: at ~250-400 games the formal
equivalence margin is out of reach (pooled-master MDE 0.36-0.51e-3 scales
by ~sqrt(n) to ~2e-3 here), so every null is quoted with its MDE and the
deliverable is directional consistency, not re-derivation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.compare import brier, ece, stacked
from src.analysis.rigor import cluster_dm
from src.analysis.power import KMDE
from src.analysis.ladder_convention import cover_line
from src.analysis.margin_dist import pit
from src.analysis.totals import implied_cdf, TOTALS, MIN_RUNGS
from src.collect.kalshi_hist_prices import _rule_home

CUTOFF = "2026-08-12"          # registered before the pull; do not move
SNAPS = "data/live/vps_mirror/snapshots.csv"
MAX_STALE_MIN = 120            # a "final pre-start quote" must be this fresh

scorecard: list[dict] = []


def record(rid, claim, stat, verdict):
    scorecard.append({"id": rid, "claim": claim, "stat": stat, "verdict": verdict})
    print(f"  [{rid}] {verdict}: {stat}", flush=True)


def slope_ci(p, y, groups):
    """Logistic recalibration slope with cluster-robust 95% CI."""
    p = np.clip(np.asarray(p, float), 0.01, 0.99)
    X = sm.add_constant(np.log(p / (1 - p)))
    r = sm.Logit(np.asarray(y), X).fit(disp=0, cov_type="cluster",
                                       cov_kwds={"groups": np.asarray(groups)})
    b, se = r.params[1], r.bse[1]
    return b, b - 1.96 * se, b + 1.96 * se


def ece_noise_floor(d, c1, c2, sims=400, seed=17):
    """Mean ECE a PERFECTLY calibrated forecaster of these prices would show
    from binning noise alone (game-level outcome sim, then both-sides stack)."""
    rng = np.random.default_rng(seed)
    p1 = d[c1].values
    es = []
    for _ in range(sims):
        y = (rng.random(len(p1)) < p1).astype(float)
        p = np.concatenate([p1, d[c2].values])
        yy = np.concatenate([y, 1 - y])
        es.append(ece(p, yy))
    return float(np.mean(es))


# ---------------------------------------------------------------- samples ---

def load_hex():
    m = pd.read_csv("data/processed/games_master.csv")
    m = m[m["outcome"].notna() & ~m["outcome_disagree"].fillna(False)]
    m = m[m["kalshi_p1"].notna() & m["poly_p1"].notna()].copy()
    m["start"] = pd.to_datetime(m.start_utc, utc=True, format="mixed")
    m = m[m.start >= pd.Timestamp(CUTOFF, tz="UTC")]
    m["home_won"] = (m["outcome"] == 1).astype(int)
    m["date"] = m.start_utc.astype(str).str[:10]
    return m


def load_h3w():
    d = pd.read_csv(SNAPS, low_memory=False)
    d = d[d.minutes_to_start > 0].copy()
    d["snap"] = pd.to_datetime(d.snapshot_utc, utc=True, format="ISO8601")
    d["start"] = pd.to_datetime(d.start_utc, utc=True, format="mixed")
    d = d[d.start >= pd.Timestamp(CUTOFF, tz="UTC")]
    d = d[d.minutes_to_start <= MAX_STALE_MIN]
    last = (d.sort_values("snap").groupby(["game_id", "source"]).tail(1))
    legs = {}
    for src_name in ("kalshi", "polymarket", "sportsbook"):
        s = last[last.source == src_name][["game_id", "league", "start_utc", "p1"]]
        legs[src_name] = s.rename(columns={"p1": f"{src_name}_p1"})
    j = legs["kalshi"].merge(legs["polymarket"][["game_id", "polymarket_p1"]], on="game_id")
    j = j.merge(legs["sportsbook"][["game_id", "sportsbook_p1"]], on="game_id")
    esp = pd.read_csv("data/processed/espn_games.csv")
    esp = esp[esp.status == "STATUS_FINAL"][["espn_id", "home_score", "away_score"]]
    esp = esp.rename(columns={"espn_id": "game_id"})
    j = j.merge(esp, on="game_id", how="inner")
    j = j[j.home_score != j.away_score]
    j["home_won"] = (j.home_score > j.away_score).astype(int)
    j["date"] = j.start_utc.astype(str).str[:10]
    # mixed-clock legs: exchange closes per the master convention where
    # available (the headline's own construction), panel quote as fallback
    m = pd.read_csv("data/processed/games_master.csv")[["game_id", "kalshi_p1", "poly_p1"]]
    j = j.merge(m, on="game_id", how="left", suffixes=("", "_master"))
    j["kmix"] = j["kalshi_p1_master"].fillna(j["kalshi_p1"])
    j["pmix"] = j["poly_p1"].fillna(j["polymarket_p1"])
    return j


def r1_r5(j):
    print(f"\n=== R1/R5. three-way dead heat on the panel holdout "
          f"(n={len(j):,} games, {j.date.nunique()} date clusters — "
          f"cluster count is low; flagged per registration) ===", flush=True)
    kk = j.kmix.values
    pp = j.pmix.values
    bb = j.sportsbook_p1.values
    y = j.home_won.values
    for name, arr in (("Kalshi", kk), ("Polymarket", pp), ("Sportsbook", bb)):
        print(f"  {name:11} Brier={brier(arr, y):.4f}", flush=True)
    pairs = [("K-P", kk, pp), ("K-B", kk, bb), ("P-B", pp, bb)]
    worst_gap, worst_rej, mdes = 0.0, False, []
    for lab, a, b in pairs:
        dbar, se, z, p, _ = cluster_dm(a, b, y, j.date.values)
        mde = KMDE * se
        mdes.append(mde)
        worst_gap = max(worst_gap, abs(dbar))
        worst_rej = worst_rej or (p < 0.05)
        print(f"  {lab}: dBrier={dbar*1000:+.2f}e-3  z={z:+.2f}  p={p:.3f}  "
              f"MDE={mde*1000:.2f}e-3", flush=True)
    ok = (worst_gap < 1e-3) and not worst_rej
    record("R1", "three-way dead heat (panel holdout)",
           f"max |dBrier| {worst_gap*1000:.2f}e-3, all DM {'n.s.' if not worst_rej else 'REJECTS'}, "
           f"MDE {min(mdes)*1000:.2f}-{max(mdes)*1000:.2f}e-3",
           "CONSISTENT" if ok else "DEVIATES")

    # R5: all three legs from the same final snapshot (kalshi/poly panel quotes)
    ks = j.kalshi_p1.values
    ps = j.polymarket_p1.values
    shift = 0.0
    for (lab, a0, b0), (a1, b1) in zip(pairs, [(ks, ps), (ks, bb), (ps, bb)]):
        d0, *_ = cluster_dm(a0, b0, y, j.date.values)
        d1, *_ = cluster_dm(a1, b1, y, j.date.values)
        shift = max(shift, abs(d1 - d0))
    d_sync = [cluster_dm(a, b, y, j.date.values) for a, b in [(ks, ps), (ks, bb), (ps, bb)]]
    rej = any(t[3] < 0.05 for t in d_sync)
    gap = max(abs(t[0]) for t in d_sync)
    print(f"\n  R5 same-clock rescore: max |dBrier|={gap*1000:.2f}e-3, "
          f"max shift vs mixed-clock={shift*1000:.2f}e-3", flush=True)
    ok5 = (gap < 1e-3) and not rej and (shift < 0.5e-3)
    record("R5", "synchronized-clock robustness",
           f"max |dBrier| {gap*1000:.2f}e-3 same-clock; shift vs mixed {shift*1000:.2f}e-3",
           "CONSISTENT" if ok5 else "DEVIATES")


def r2_r3_r4(h):
    print(f"\n=== R2. exchange dead heat on the master holdout "
          f"(n={len(h):,} games, {h.date.nunique()} date clusters) ===", flush=True)
    y = h.home_won.values
    for name, c in (("Kalshi", "kalshi_p1"), ("Polymarket", "poly_p1")):
        print(f"  {name:11} Brier={brier(h[c].values, y):.4f}", flush=True)
    dbar, se, z, p, _ = cluster_dm(h.kalshi_p1.values, h.poly_p1.values, y, h.date.values)
    mde = KMDE * se
    print(f"  K-P: dBrier={dbar*1000:+.2f}e-3  z={z:+.2f}  p={p:.3f}  MDE={mde*1000:.2f}e-3", flush=True)
    ok = (abs(dbar) < 1e-3) and (p >= 0.05)
    record("R2", "exchange dead heat (master holdout)",
           f"|dBrier| {abs(dbar)*1000:.2f}e-3, DM p={p:.3f}, MDE {mde*1000:.2f}e-3",
           "CONSISTENT" if ok else "DEVIATES")

    print(f"\n=== R3. calibration on the holdout ===", flush=True)
    ok3, det = True, []
    for name, (c1, c2) in (("Kalshi", ("kalshi_p1", "kalshi_p2")),
                           ("Polymarket", ("poly_p1", "poly_p2"))):
        ps_, yy = stacked(h, c1, c2)
        g = np.concatenate([h.game_id.values, h.game_id.values])
        b, lo, hi = slope_ci(ps_, yy, g)
        e = ece(ps_, yy)
        floor = ece_noise_floor(h, c1, c2)
        cov = lo <= 1 <= hi
        near = e <= 2 * floor
        ok3 = ok3 and cov and near
        det.append(f"{name} slope {b:.2f} [{lo:.2f},{hi:.2f}] ECE {e:.3f} (floor {floor:.3f})")
        print(f"  {name:11} slope={b:.3f} [{lo:.2f},{hi:.2f}] {'covers 1' if cov else 'MISSES 1'}  "
              f"ECE={e:.4f} vs noise floor {floor:.4f} {'ok' if near else 'EXCESS'}", flush=True)
    record("R3", "holdout calibration (slopes~1, ECE at floor)", "; ".join(det),
           "CONSISTENT" if ok3 else "DEVIATES")

    print(f"\n=== R4. favorite-longshot bias on the holdout (stacked sides) ===", flush=True)
    p4, y4 = stacked(h, "kalshi_p1", "kalshi_p2")
    ok4, det4 = True, []
    for lab, m in (("<30c", p4 < 0.30), (">70c", p4 > 0.70)):
        n = int(m.sum())
        if n < 30:
            det4.append(f"{lab}: n={n} too thin")
            print(f"  {lab}: n={n} — too thin to read", flush=True)
            continue
        gap = y4[m].mean() - p4[m].mean()
        se4 = np.sqrt(y4[m].var(ddof=1) / n)
        z4 = gap / se4
        flb = (lab == "<30c" and z4 <= -2) or (lab == ">70c" and z4 >= 2)
        ok4 = ok4 and not flb
        det4.append(f"{lab}: gap {gap*100:+.1f}pt z={z4:+.1f} (n={n})")
        print(f"  {lab}: realized-priced {gap*100:+.1f}pt  z={z4:+.1f}  n={n}", flush=True)
    record("R4", "no favorite-longshot bias", "; ".join(det4),
           "CONSISTENT" if ok4 else "DEVIATES")


def r6_extras():
    print(f"\n=== R6. shared extras blind spot, direction (fresh MLB ladders) ===", flush=True)
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    sp = sp[sp.league == "MLB"].copy()
    sp["start"] = pd.to_datetime(sp.start_utc, utc=True, format="mixed")
    sp = sp[sp.start >= pd.Timestamp(CUTOFF, tz="UTC")]
    esp = pd.read_csv("data/processed/espn_games.csv")
    esp = esp[(esp.league == "MLB") & (esp.status == "STATUS_FINAL")].copy()
    esp = esp.rename(columns={"espn_id": "game_id"})
    inn = pd.read_csv("data/processed/mlb_innings.csv")[["game_id", "innings"]]
    esp = esp.merge(inn, on="game_id", how="inner")
    esp = esp[esp.innings >= 9]
    esp["margin"] = esp.home_score - esp.away_score
    esp = esp[esp.margin != 0]
    info = esp.set_index("game_id")[["margin", "innings"]]
    ml = pd.read_csv("data/processed/games_master.csv")[["game_id", "kalshi_p1"]]
    sp = sp.merge(ml, on="game_id", how="left")

    rows = []
    for gid, grp in sp.groupby("game_id"):
        if gid not in info.index:
            continue
        ev = grp["event_ticker"].iloc[0]
        codes = sorted(set(grp["team"]))
        rh = _rule_home(ev, codes) if len(codes) == 2 else None
        pml = grp["kalshi_p1"].iloc[0]
        if rh is None or pml != pml:
            continue
        margin = int(info.loc[gid, "margin"])
        extras = bool(info.loc[gid, "innings"] > 9)
        for side, sgn in (("home", +1), ("away", -1)):
            rungs = {r.threshold: r.prob for r in
                     grp[(grp.team == rh) == (side == "home")].itertuples(index=False)
                     if r.prob == r.prob}
            bc = {cover_line("MLB", t): p for t, p in rungs.items()}
            if 3 not in bc:
                continue
            pwin = float(pml) if sgn == 1 else 1 - float(pml)
            sm_ = sgn * margin
            rows.append({"extras": extras, "imp": pwin - bc[3], "emp": float(sm_ in (1, 2))})
    d = pd.DataFrame(rows)
    if len(d) < 20:
        record("R6", "extras cell direction", f"only {len(d)} sides — cannot read", "UNDERPOWERED")
        return
    ext, reg = d[d.extras], d[~d.extras]
    def cell(s):
        gap = s.emp.mean() - s.imp.mean()
        se6 = np.sqrt(s.emp.var(ddof=1) / len(s) + s.imp.var(ddof=1) / len(s)) if len(s) > 5 else np.nan
        return gap, se6
    g_all, _ = cell(d)
    print(f"  all sides n={len(d)}: gap {g_all*100:+.1f}pt", flush=True)
    det = f"aggregate {g_all*100:+.1f}pt (n={len(d)})"
    if len(ext) >= 10:
        g_ext, se_ext = cell(ext)
        ci = 1.645 * se_ext * 100
        print(f"  extras n={len(ext)}: gap {g_ext*100:+.1f}pt (90% CI ±{ci:.1f}pt)  "
              f"[frozen estimate +20.2pt]", flush=True)
        print(f"  regulation n={len(reg)}: gap {cell(reg)[0]*100:+.1f}pt", flush=True)
        ok = (g_ext > 0) and (abs(g_all) < g_ext)
        det = f"extras {g_ext*100:+.1f}pt ±{ci:.0f} (n={len(ext)}); " + det
        record("R6", "extras cell direction (predicted +)", det,
               "CONSISTENT" if ok else "DEVIATES")
    else:
        record("R6", "extras cell direction",
               f"only {len(ext)} extras sides in window; " + det, "UNDERPOWERED")


def r7_wnba_totals():
    print(f"\n=== R7. WNBA totals tilt — the open observation's real-time test ===", flush=True)
    t = pd.read_csv(TOTALS)
    t = t[t.league == "WNBA"].copy()
    t["start"] = pd.to_datetime(t.start_utc, utc=True, format="mixed")
    t = t[t.start >= pd.Timestamp(CUTOFF, tz="UTC")]
    esp = (pd.read_csv("data/processed/espn_games.csv")[["espn_id", "home_score", "away_score"]]
           .rename(columns={"espn_id": "game_id"}))
    t = t.merge(esp, on="game_id", how="inner")
    t = t[t.home_score.notna() & t.away_score.notna()]
    t["total"] = (t.home_score + t.away_score).astype(int)
    t = t[t.prob.between(0.0, 1.0)]
    rng = np.random.default_rng(17)
    us = []
    for gid, gg in t.groupby("game_id"):
        rungs = {r.threshold: r.prob for r in gg.itertuples(index=False) if r.prob == r.prob}
        if len(rungs) < MIN_RUNGS:
            continue
        u = pit(implied_cdf(rungs), int(gg.total.iloc[0]), rng)
        if u is not None:
            us.append(u)
    if len(us) < 25:
        record("R7", "WNBA totals tilt (predicted u>0.5)",
               f"only {len(us)} fresh ladders — cannot read", "UNDERPOWERED")
        return
    us = np.array(us)
    se7 = (1 / 12 / len(us)) ** 0.5
    z7 = (us.mean() - 0.5) / se7
    ks = stats.kstest(us, "uniform")
    print(f"  n={len(us)} ladders: mean u={us.mean():.3f} (z={z7:+.1f} vs 0.5)  "
          f"KS p={ks.pvalue:.3f}  [frozen estimate mean u 0.536]", flush=True)
    verdict = ("CONSISTENT" if us.mean() > 0.5 else "DEVIATES") if abs(z7) >= 1 else "NOISE"
    record("R7", "WNBA totals tilt (predicted u>0.5)",
           f"mean u {us.mean():.3f}, z {z7:+.1f}, n={len(us)}", verdict)


def r8_cost():
    print(f"\n=== R8. structural taker cost on fresh quotes ===", flush=True)
    d = pd.read_csv(SNAPS, low_memory=False)
    d["snap"] = pd.to_datetime(d.snapshot_utc, utc=True, format="ISO8601")
    d = d[(d.source == "kalshi") & (d.minutes_to_start > 0)]
    d = d[d.snap >= pd.Timestamp(CUTOFF, tz="UTC")]
    d = d.dropna(subset=["spread1", "p1"])
    d = d[(d.spread1 >= 0) & d.p1.between(0.02, 0.98)]
    half = d.spread1 / 2
    fee = 0.07 * d.p1 * (1 - d.p1)
    cost = (half + fee) / d.p1
    med = -cost.median()
    print(f"  n={len(d):,} fresh quotes: median {med*100:.1f}% per position "
          f"(IQR {-cost.quantile(.75)*100:.1f} to {-cost.quantile(.25)*100:.1f})  "
          f"[frozen: -4.5%, criterion ±1.0pt]", flush=True)
    ok = abs(med - (-0.045)) <= 0.010
    record("R8", "structural taker cost -4.5% ±1pt",
           f"median {med*100:.1f}%/position (n={len(d):,})",
           "CONSISTENT" if ok else "DEVIATES")


def figure():
    fig, ax = plt.subplots(figsize=(10, 0.55 * len(scorecard) + 1.6))
    ax.axis("off")
    ax.set_title("Registered out-of-sample scorecard — claims fixed before the holdout was pulled\n"
                 f"(docs/registered-claims.md; holdout = games starting on/after {CUTOFF})",
                 fontsize=10, loc="left")
    colors = {"CONSISTENT": "#0ca30c", "DEVIATES": "#d03b3b",
              "UNDERPOWERED": "#898781", "NOISE": "#898781"}
    for i, row in enumerate(scorecard):
        yy = 1 - (i + 1) / (len(scorecard) + 1)
        ax.text(0.00, yy, row["id"], fontsize=9, weight="bold", transform=ax.transAxes)
        ax.text(0.05, yy, row["claim"], fontsize=9, transform=ax.transAxes)
        ax.text(0.42, yy, row["stat"], fontsize=8, color="#52514e", transform=ax.transAxes)
        ax.text(0.92, yy, row["verdict"], fontsize=9, weight="bold",
                color=colors.get(row["verdict"], "#0b0b0b"), transform=ax.transAxes)
    fig.tight_layout()
    fig.savefig("results/oos_scorecard.png", dpi=160)
    print("\nsaved results/oos_scorecard.png", flush=True)


def main():
    print(f"registered protocol: docs/registered-claims.md (commit f915794); "
          f"cutoff {CUTOFF}; evaluated once on the freeze pull", flush=True)
    j = load_h3w()
    r1_r5(j)
    h = load_hex()
    r2_r3_r4(h)
    r6_extras()
    r7_wnba_totals()
    r8_cost()
    print("\n=== SCORECARD ===", flush=True)
    for row in scorecard:
        print(f"  {row['id']:3} {row['verdict']:12} {row['claim']}", flush=True)
    figure()


if __name__ == "__main__":
    main()
