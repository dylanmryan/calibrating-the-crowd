"""Head-to-head calibration: Kalshi vs Polymarket on the same games.

On the joint set (both platforms priced, resolved outcome, no settlement disagreement):
  - Brier score each, paired Diebold-Mariano test (are they significantly different?)
  - Calibration slope + ECE each
  - Per-sport Brier comparison
  - Reliability diagram overlay
  - Divergence analysis: when the two prices disagree, which is closer to the outcome?
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path="data/processed/games_master.csv") -> pd.DataFrame:
    m = pd.read_csv(path)
    m = m[m["outcome"].notna() & ~m["outcome_disagree"].fillna(False)]
    both = m[m["kalshi_p1"].notna() & m["poly_p1"].notna()].copy()
    both["home_won"] = (both["outcome"] == 1).astype(int)
    return both


def brier(p, y):
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def cal_slope(p, y):
    p = np.clip(np.asarray(p, float), 0.01, 0.99)
    X = sm.add_constant(np.log(p / (1 - p)))
    r = sm.Logit(np.asarray(y), X).fit(disp=0)
    return r.params[1]


def ece(p, y, nbins=10):
    p, y = np.asarray(p, float), np.asarray(y, float)
    edges = np.linspace(0, 1, nbins + 1)
    b = np.clip(np.digitize(p, edges) - 1, 0, nbins - 1)
    e = 0.0
    for k in range(nbins):
        m = b == k
        if m.any():
            e += m.mean() * abs(y[m].mean() - p[m].mean())
    return float(e)


def stacked(d, col1, col2):
    """Both sides -> full 0-1 range: (home prob, home_won) + (away prob, away_won)."""
    p = np.concatenate([d[col1].values, d[col2].values])
    y = np.concatenate([d["home_won"].values, 1 - d["home_won"].values])
    return p, y


def reliability(p, y, nbins=12):
    edges = np.linspace(0, 1, nbins + 1)
    df = pd.DataFrame({"p": p, "y": y})
    df["b"] = pd.cut(df["p"], edges, include_lowest=True)
    g = df.groupby("b", observed=True).agg(pred=("p", "mean"), obs=("y", "mean"), n=("y", "size")).dropna()
    return g


def main():
    d = load()
    y = d["home_won"].values
    print(f"joint clean games: {len(d):,}\n", flush=True)

    # --- paired Brier + Diebold-Mariano ---
    lk = (d["kalshi_p1"] - y) ** 2
    lp = (d["poly_p1"] - y) ** 2
    dd = (lk - lp).values
    dm = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd)))
    pval = 2 * (1 - stats.norm.cdf(abs(dm)))
    print("=== overall (home-team framing) ===", flush=True)
    print(f"Brier  Kalshi={brier(d.kalshi_p1, y):.4f}   Polymarket={brier(d.poly_p1, y):.4f}", flush=True)
    print(f"Diebold-Mariano stat={dm:+.2f} (p={pval:.3f})  "
          f"{'Kalshi better' if dm < 0 else 'Polymarket better'} "
          f"{'(significant)' if pval < 0.05 else '(not significant)'}", flush=True)

    # --- calibration on stacked both-sides ---
    for name, c1, c2 in [("Kalshi", "kalshi_p1", "kalshi_p2"), ("Polymarket", "poly_p1", "poly_p2")]:
        p, yy = stacked(d, c1, c2)
        print(f"{name:11} slope={cal_slope(p, yy):.3f}  ECE={ece(p, yy):.4f}  "
              f"Brier={brier(p, yy):.4f}", flush=True)

    # --- per sport ---
    print("\n=== per league: Brier (lower=better) ===", flush=True)
    for lg, g in d.groupby("league"):
        yy = g["home_won"].values
        bk, bp = brier(g.kalshi_p1, yy), brier(g.poly_p1, yy)
        win = "Kalshi" if bk < bp else "Poly"
        print(f"  {lg:6} n={len(g):5}  Kalshi={bk:.4f}  Poly={bp:.4f}  -> {win}", flush=True)

    # --- divergence: when prices disagree, who's closer? ---
    d["gap"] = (d["kalshi_p1"] - d["poly_p1"]).abs()
    div = d[d["gap"] > 0.05]
    k_closer = (np.abs(div.kalshi_p1 - div.home_won) < np.abs(div.poly_p1 - div.home_won)).mean()
    print(f"\n=== divergence (|Kalshi-Poly| > 5pts): {len(div)} games ===", flush=True)
    print(f"correlation of the two prices (all games): {d.kalshi_p1.corr(d.poly_p1):.4f}", flush=True)
    print(f"when they diverge, Kalshi closer to outcome: {k_closer:.1%} of the time", flush=True)

    # --- reliability overlay ---
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfect")
    for name, c1, c2, col in [("Kalshi", "kalshi_p1", "kalshi_p2", "tab:blue"),
                              ("Polymarket", "poly_p1", "poly_p2", "tab:orange")]:
        p, yy = stacked(d, c1, c2)
        t = reliability(p, yy)
        ax.plot(t.pred, t.obs, "o-", color=col, ms=4, label=f"{name} (Brier={brier(p, yy):.3f})")
    ax.set(xlabel="Predicted probability", ylabel="Observed win frequency",
           title=f"Kalshi vs Polymarket calibration (n={len(d):,} games)",
           xlim=(0, 1), ylim=(0, 1))
    ax.set_aspect("equal"); ax.legend(loc="upper left")
    fig.tight_layout(); fig.savefig("results/kalshi_vs_polymarket.png", dpi=130)
    print("\nsaved results/kalshi_vs_polymarket.png", flush=True)


if __name__ == "__main__":
    main()
