"""Minute-level lead-lag + scheduled-news event study (Kalshi vs Polymarket).

Does the 15-min "simultaneous repricing" verdict survive 60x finer resolution?
Four instruments on the joint 1-min panel (final 6h, post-cutoff games):
  1. cross-correlograms of 1-min (and 5-min) changes at +-10 lags;
  2. predictive regressions: dP_t ~ own lags + dK_(t-1..t-5), game-clustered,
     testing the SUM of cross-lag coefficients (and the mirror);
  3. repricing-intensity curves vs minutes-to-start — MLB lineup postings
     (~2-4h pre-game) are scheduled public information: do both venues' bursts
     coincide, or does one venue's intensity peak earlier?
  4. first-passage timing inside joint repricing episodes (both venues move
     >=1.5pts same sign in 15 min): which venue crosses HALF of its episode
     move first? Median lead in minutes, sign-test.
Plus a wall-clock panel around 5:00pm ET (NBA/WNBA injury-report hour) on the
basketball subsample — suggestive only (n small, WNBA policy timing varies).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

MAXGAP_FFILL = 20      # minutes; beyond this a quiet stretch stays NaN
GLITCH = 0.10
NLAG = 5


def panel(path="data/processed/minute_paths.csv"):
    d = pd.read_csv(path)
    frames = []
    for gid, g in d.groupby("game_id"):
        g = g.set_index("mts").reindex(range(0, 361)).sort_index(ascending=False)
        for c in ("k_mid", "p_price"):
            g[c] = g[c].ffill(limit=MAXGAP_FFILL)
        g["dk"] = g.k_mid.diff()
        g["dp"] = g.p_price.diff()
        g = g[(g.dk.abs() <= GLITCH) | g.dk.isna()]
        g = g[(g.dp.abs() <= GLITCH) | g.dp.isna()]
        g["game_id"] = gid
        g["league"] = d[d.game_id == gid].league.iloc[0]
        g["start_utc"] = d[d.game_id == gid].start_utc.iloc[0]
        frames.append(g.reset_index())
    return pd.concat(frames, ignore_index=True)


def xcorr(d, agg=1):
    g = d.dropna(subset=["dk", "dp"]).copy()
    if agg > 1:
        g["bin"] = g.mts // agg
        g = (g.groupby(["game_id", "bin"]).agg(dk=("dk", "sum"), dp=("dp", "sum"),
                                               league=("league", "first")).reset_index()
             .sort_values(["game_id", "bin"], ascending=[True, False]))
    lags = range(-10 // agg or -1, 10 // agg + 1 or 2)
    rows = []
    for k in lags:
        a = g.groupby("game_id")["dk"].shift(k)   # k>0: K's PAST move vs P now
        sub = pd.DataFrame({"a": a, "b": g["dp"]}).dropna()
        rows.append({"lag": k, "corr": np.corrcoef(sub.a, sub.b)[0, 1], "n": len(sub)})
    return pd.DataFrame(rows)


def predictive(d, y_col, x_col):
    g = d.sort_values(["game_id", "mts"], ascending=[True, False]).copy()
    cols = []
    for l in range(1, NLAG + 1):
        for c in (y_col, x_col):
            g[f"{c}_l{l}"] = g.groupby("game_id")[c].shift(l)
            cols.append(f"{c}_l{l}")
    g = g.dropna(subset=[y_col] + cols)
    X = sm.add_constant(g[cols].values)
    r = sm.OLS(g[y_col].values, X).fit(cov_type="cluster",
                                       cov_kwds={"groups": g.game_id.values})
    idx = [1 + i for i, c in enumerate(cols) if c.startswith(x_col)]
    contrast = np.zeros(len(r.params)); contrast[idx] = 1
    t = r.t_test(contrast)
    return np.asarray(t.effect).item(), np.asarray(t.tvalue).item(), len(g)


def episodes(d, thresh=0.015):
    """First-passage half-crossing lead inside joint 15-min repricing episodes."""
    leads = []
    for gid, g in d.groupby("game_id"):
        g = g.sort_values("mts", ascending=False).reset_index(drop=True)
        k15 = g.dk.rolling(15).sum()
        p15 = g.dp.rolling(15).sum()
        trig = (k15.abs() >= thresh) & (p15.abs() >= thresh) & (np.sign(k15) == np.sign(p15))
        i = 0
        while i < len(g):
            if not trig.iloc[i]:
                i += 1
                continue
            w = g.iloc[max(0, i - 15): min(len(g), i + 16)]
            halves = {}
            for c in ("k_mid", "p_price"):
                s = w[c].dropna()
                if len(s) < 10:
                    break
                total = s.iloc[-1] - s.iloc[0]
                if abs(total) < 0.01:
                    break
                cum = (s - s.iloc[0]) / total
                cross = cum[cum >= 0.5]
                if cross.empty:
                    break
                halves[c] = w.loc[cross.index[0], "mts"]
            if len(halves) == 2:
                leads.append(halves["p_price"] - halves["k_mid"])  # >0: K crossed EARLIER
            i += 30
    return np.array(leads, float)


def main():
    d = panel()
    n_games = d.game_id.nunique()
    print(f"joint 1-min panel: {n_games} games, "
          f"{d.dropna(subset=['dk','dp']).shape[0]:,} complete minute-changes", flush=True)
    print(d.groupby('league').game_id.nunique().to_dict(), flush=True)

    print("\n=== cross-correlograms (positive lag = Kalshi's past move vs Poly's now) ===", flush=True)
    x1 = xcorr(d, 1)
    print("  1-min:", "  ".join(f"{r.lag:+d}:{r.corr:+.3f}" for r in x1.itertuples()), flush=True)
    x5 = xcorr(d, 5)
    print("  5-min:", "  ".join(f"{int(r.lag)*5:+d}m:{r.corr:+.3f}" for r in x5.itertuples()), flush=True)

    print("\n=== predictive regressions: sum of 5 cross-lags (game-clustered) ===", flush=True)
    for lab, yc, xc in [("dPoly <- Kalshi lags", "dp", "dk"), ("dKalshi <- Poly lags", "dk", "dp")]:
        eff, tv, n = predictive(d, yc, xc)
        print(f"  {lab:22} sum-coef={eff:+.3f}  z={tv:+.2f}  n={n:,}", flush=True)

    print("\n=== joint repricing episodes: who crosses half its move first? ===", flush=True)
    ld = episodes(d)
    if len(ld):
        k_first = (ld > 0).mean()
        from scipy import stats as st
        nz = ld[ld != 0]
        p_sign = st.binomtest(int((nz > 0).sum()), len(nz)).pvalue if len(nz) else 1.0
        print(f"  episodes: {len(ld)} | median lead {np.median(ld):+.1f} min | "
              f"Kalshi-first {k_first:.0%}, ties {(ld==0).mean():.0%} | sign-test p={p_sign:.3f}", flush=True)

    mlb = d[d.league == "MLB"]
    inten = (mlb.assign(b=(mlb.mts // 15) * 15)
             .groupby("b")[["dk", "dp"]].apply(lambda g: g.abs().mean() * 100))
    print("\n=== MLB repricing intensity (mean |1-min move|, pts) — lineup window T-4h..T-1.5h ===", flush=True)
    print(inten.rename(columns={"dk": "kalshi", "dp": "poly"}).round(3).to_string(), flush=True)

    bb = d[d.league.isin(["NBA", "WNBA"])].copy()
    bb["clock_et"] = (pd.to_datetime(bb.start_utc, utc=True, format="ISO8601")
                      - pd.to_timedelta(bb.mts, unit="m")).dt.tz_convert("US/Eastern")
    bb["m5"] = (bb.clock_et.dt.hour * 60 + bb.clock_et.dt.minute) - 17 * 60
    ev = bb[(bb.m5 >= -60) & (bb.m5 <= 90)].copy()
    ev["b"] = (ev.m5 // 10) * 10

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.5))
    ax = axes[0, 0]
    ax.bar(x1.lag - 0.2, x1["corr"], 0.4, color="tab:blue", label="corr(dK_{t-k}, dP_t)")
    ax.axhline(0, color="0.4", lw=0.8)
    ax.set(xlabel="lag k (min; +k = Kalshi earlier)", ylabel="correlation",
           title=f"1-min cross-correlogram ({n_games} games)")
    ax.legend(fontsize=8)

    ax = axes[0, 1]
    ax.plot(-inten.index, inten.dk, "o-", ms=3, color="tab:blue", label="Kalshi")
    ax.plot(-inten.index, inten.dp, "s-", ms=3, color="tab:orange", label="Polymarket")
    ax.axvspan(-240, -90, color="tab:green", alpha=0.10, label="lineup window")
    ax.set(xlabel="minutes to start", ylabel="mean |1-min move| (pts)",
           title="MLB repricing intensity: scheduled-news window")
    ax.legend(fontsize=8)

    ax = axes[1, 0]
    if len(ld):
        ax.hist(np.clip(ld, -15, 15), bins=np.arange(-15.5, 16.5), color="tab:purple", alpha=0.8)
        ax.axvline(0, color="0.3", lw=1)
        ax.axvline(np.median(ld), color="tab:red", ls="--", lw=1.2,
                   label=f"median {np.median(ld):+.1f} min")
    ax.set(xlabel="half-move lead (min; >0 = Kalshi first)", ylabel="episodes",
           title="Joint repricing episodes: first-passage timing")
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    for c, col, lab in [("dk", "tab:blue", "Kalshi"), ("dp", "tab:orange", "Polymarket")]:
        prof = ev.groupby("b")[c].apply(lambda s: s.abs().mean() * 100)
        ax.plot(prof.index, prof.values, "o-", ms=3, color=col, label=lab)
    ax.axvline(0, color="0.35", ls="--", lw=1)
    ax.text(2, ax.get_ylim()[1] * 0.92, "5:00pm ET", fontsize=8, color="0.35")
    ax.set(xlabel="minutes from 5:00pm ET", ylabel="mean |1-min move| (pts)",
           title=f"NBA/WNBA injury-report hour (n={ev.game_id.nunique()} games, suggestive)")
    ax.legend(fontsize=8)

    fig.suptitle("Minute-level price discovery: Kalshi vs Polymarket")
    fig.tight_layout()
    fig.savefig("results/minute_lead_lag.png", dpi=130)
    print("\nsaved results/minute_lead_lag.png", flush=True)


if __name__ == "__main__":
    main()
