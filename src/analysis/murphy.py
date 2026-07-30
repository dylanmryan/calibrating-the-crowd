"""Murphy diagrams: the dead heat holds under EVERY proper scoring function.

Ehm-Gneiting-Jordan-Krueger (2016, JRSS-B): every consistent scoring function
for probability forecasts is a mixture of elementary scores
    S_theta(p, y) = theta*1{p>theta, y=0} + (1-theta)*1{p<=theta, y=1},
so if source A's mean elementary score is <= B's at every threshold theta, A
dominates B under all proper scores simultaneously (Brier, log, spherical, any
cost-ratio decision rule). We plot the three Murphy curves and each pairwise
difference with pointwise 95% date-clustered bands: bands covering zero
everywhere = no scoring function any user could hold changes the ranking.
Home-side forecasts, consistent with the DM/TOST convention.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.three_way import SRC, COLOR, load

# theta on cent-grid MIDPOINTS: exchange prices sit on a 1c grid, and thresholds
# equal to those mass points make 1{p>theta} flip whole masses between adjacent
# thetas (a tie-handling artifact the continuous book consensus doesn't share).
THETA = np.arange(0.005, 1.0, 0.01)


def elementary(p, y):
    """(n, len(THETA)) matrix of elementary scores."""
    p = np.asarray(p, float)[:, None]
    y = np.asarray(y, float)[:, None]
    t = THETA[None, :]
    return t * (p > t) * (1 - y) + (1 - t) * (p <= t) * y


def cluster_band(d, dates, B=999, seed=7):
    """Pointwise mean, cluster-robust SE, and the sup-t uniform critical value.

    Multiplier (Rademacher) bootstrap over date-cluster score sums gives the
    95% quantile of sup_theta |t(theta)| -> a uniform band and a global
    p-value for "some proper scoring function separates the pair".
    """
    n = d.shape[0]
    mu = d.mean(axis=0)
    g = pd.DataFrame(d - mu).groupby(pd.Series(dates)).sum().values  # (C, t)
    se = np.sqrt((g ** 2).sum(axis=0)) / n
    rng = np.random.default_rng(seed)
    eps = rng.choice([-1.0, 1.0], size=(B, g.shape[0]))
    ok = se > 0  # extreme thresholds no forecast pair straddles: diff identically 0
    sups = np.abs(eps @ g[:, ok] / n / se[ok]).max(axis=1)
    t_obs = np.abs(mu[ok] / se[ok]).max()
    crit = np.quantile(sups, 0.95)
    p_glob = float((1 + (sups >= t_obs).sum()) / (len(sups) + 1))
    return mu, se, crit, t_obs, p_glob


def main():
    from src.analysis.rigor import shin_two_way
    d = load()
    d["date"] = d.start_utc.astype(str).str[:10]
    sb = pd.read_csv("data/processed/sportsbook_hist_prices.csv")[
        ["game_id", "book_raw1", "book_raw2"]]
    d = d.merge(sb, on="game_id", how="inner").dropna(subset=["book_raw1", "book_raw2"])
    shin = np.array([shin_two_way(a, b) for a, b in zip(d.book_raw1, d.book_raw2)])
    d["book_shin1"] = shin[:, 0]
    y = d.home_won.values
    print(f"three-way clean games: {len(d):,} (book = Shin de-vig; see artifact note)", flush=True)

    cols = {"Kalshi": "kalshi_p1", "Polymarket": "poly_p1", "Sportsbook": "book_shin1"}
    S = {name: elementary(d[c].values, y) for name, c in cols.items()}
    for name, s in S.items():
        print(f"  {name:11} mean elementary score integral x2 = {2*np.trapezoid(s.mean(0), THETA):.4f} "
              f"(Brier check)", flush=True)

    # the de-vig artifact demonstration: multiplicative book tails lose to both
    # exchanges at extreme thresholds; Shin (which corrects longshot shading)
    # removes it — a difference Brier cannot see (0.2183 vs 0.2184).
    print("\n  de-vig artifact check (sup-t global p vs each book variant):", flush=True)
    S_mult = elementary(d.book_p1.values, y)
    for a in ("Kalshi", "Polymarket"):
        _, _, _, t_m, p_m = cluster_band(S[a] - S_mult, d.date.values)
        _, _, _, t_s, p_s = cluster_band(S[a] - S["Sportsbook"], d.date.values)
        print(f"    {a:11} vs mult book: sup-t={t_m:.2f} p={p_m:.3f}  |  "
              f"vs Shin book: sup-t={t_s:.2f} p={p_s:.3f}", flush=True)

    pairs = [("Kalshi", "Polymarket"), ("Kalshi", "Sportsbook"), ("Polymarket", "Sportsbook")]
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7), sharex=True,
                             gridspec_kw={"height_ratios": [1.2, 1]})
    for ax in axes[0]:
        for name, s in S.items():
            ax.plot(THETA, s.mean(0) * 1000, color=COLOR[name], lw=1.6, label=name)
    axes[0, 0].set_ylabel("mean elementary score (×10³)")
    axes[0, 0].legend(fontsize=8)
    for j, (a, b) in enumerate(pairs):
        axes[0, j].set_title(f"{a} vs {b}", fontsize=10)
        mu, se, crit, t_obs, p_glob = cluster_band(S[a] - S[b], d.date.values)
        frac_in = float(np.mean(np.abs(mu) <= 1.96 * se))
        print(f"  {a} - {b}: max |diff| = {np.abs(mu).max()*1000:.3f}e-3 | pointwise "
              f"band covers 0 at {frac_in:.0%} of thresholds | sup-t = {t_obs:.2f} vs "
              f"crit {crit:.2f} -> global p = {p_glob:.3f}", flush=True)
        ax = axes[1, j]
        ax.fill_between(THETA, (mu - 1.96 * se) * 1000, (mu + 1.96 * se) * 1000,
                        color="0.8", label="95% pointwise (date-clustered)")
        ax.plot(THETA, (mu - crit * se) * 1000, ls="--", color="0.55", lw=0.9,
                label="95% uniform (sup-t)")
        ax.plot(THETA, (mu + crit * se) * 1000, ls="--", color="0.55", lw=0.9)
        ax.plot(THETA, mu * 1000, color="tab:red", lw=1.2)
        ax.axhline(0, color="0.3", lw=0.8)
        ax.set(xlabel="threshold θ (decision cost ratio)",
               title=f"global p = {p_glob:.2f}")
        if j == 0:
            ax.set_ylabel("score difference (×10³)")
            ax.legend(fontsize=7)
    fig.suptitle("Murphy diagrams: no proper scoring function separates the three sources")
    fig.tight_layout()
    fig.savefig("results/murphy.png", dpi=130)
    print("saved results/murphy.png", flush=True)


if __name__ == "__main__":
    main()
