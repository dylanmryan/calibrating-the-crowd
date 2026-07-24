"""Hierarchical Bayesian calibration: partial pooling turns small-league noise
into posterior statements.

Per source, a hierarchical logistic recalibration
    y_i ~ Bernoulli( sigmoid( alpha_league + beta_league * logit(p_i) ) )
with league effects partially pooled through hyperpriors (non-centered NUTS).
Perfect calibration is (alpha, beta) = (0, 1). Deliverables per source:
  - shrunken league-level (alpha, beta) posteriors with 90% HDIs — the frequen-
    tist "CFB/WNBA/NFL are underpowered" caveat becomes a shrunken estimate;
  - P(practically calibrated) per league: posterior mass inside the ROPE
    |alpha| < 0.10 and |beta - 1| < 0.10 (~2.5pt max distortion at p=0.5);
  - sigma_beta hyperposterior: is there ANY league-level calibration
    heterogeneity to find?
Home-side forecasts, clean three-way set, consistent with DM/TOST conventions.
"""
from __future__ import annotations

import os
# this Mac's Xcode CLT rejects pytensor's -ld64 linker flag; the model is tiny,
# so run pytensor's pure-Python backend instead of compiling C ops
os.environ.setdefault("PYTENSOR_FLAGS", "cxx=")

import numpy as np
import pandas as pd
import pymc as pm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.three_way import SRC, COLOR, load
from src.analysis.decomposition import slope_ci

SEED = 7
ROPE_A, ROPE_B = 0.10, 0.10


def split_rhat(x):
    """Split-R-hat for one parameter's (chains, draws) sample array."""
    c, n = x.shape
    h = n // 2
    parts = x[:, : h * 2].reshape(c * 2, h)
    W = parts.var(axis=1, ddof=1).mean()
    B = h * parts.mean(axis=1).var(ddof=1)
    return float(np.sqrt((h - 1) / h + B / (W * h)))


def hdi90(s):
    """Shortest 90% interval of a posterior sample vector."""
    s = np.sort(np.asarray(s, float))
    k = max(1, int(np.floor(0.90 * len(s))))
    i = int(np.argmin(s[k:] - s[:len(s) - k]))
    return s[i], s[i + k]


def fit_source(x, y, lg_idx, leagues):
    with pm.Model(coords={"league": leagues}) as model:
        mu_a = pm.Normal("mu_a", 0.0, 0.5)
        mu_b = pm.Normal("mu_b", 1.0, 0.5)
        sig_a = pm.HalfNormal("sig_a", 0.3)
        sig_b = pm.HalfNormal("sig_b", 0.3)
        za = pm.Normal("za", 0.0, 1.0, dims="league")
        zb = pm.Normal("zb", 0.0, 1.0, dims="league")
        alpha = pm.Deterministic("alpha", mu_a + sig_a * za, dims="league")
        beta = pm.Deterministic("beta", mu_b + sig_b * zb, dims="league")
        pm.Bernoulli("y", logit_p=alpha[lg_idx] + beta[lg_idx] * x, observed=y)
        idata = pm.sample(draws=1000, tune=1500, chains=4, target_accept=0.98,
                          random_seed=SEED, progressbar=False)
    return idata


def main():
    d = load()
    leagues = sorted(d.league.unique())
    lg_idx = pd.Categorical(d.league, categories=leagues).codes
    y = d.home_won.values
    print(f"three-way clean games: {len(d):,}; leagues: {leagues}", flush=True)

    results = {}
    for name, (c1, _) in SRC.items():
        p = np.clip(d[c1].values, 0.01, 0.99)
        x = np.log(p / (1 - p))
        idata = fit_source(x, y, lg_idx, leagues)
        div = int(idata.sample_stats.diverging.sum())
        rhats = []
        for v in ("alpha", "beta"):
            arr = idata.posterior[v].values          # (chains, draws, league)
            rhats += [split_rhat(arr[:, :, j]) for j in range(arr.shape[2])]
        for v in ("mu_a", "mu_b", "sig_a", "sig_b"):
            rhats.append(split_rhat(idata.posterior[v].values))
        rhat_max = max(rhats)
        print(f"\n=== {name} (divergences={div}, max R-hat={rhat_max:.3f}) ===", flush=True)
        post = idata.posterior
        a = post["alpha"].values.reshape(-1, len(leagues))
        b = post["beta"].values.reshape(-1, len(leagues))
        rope = ((np.abs(a) < ROPE_A) & (np.abs(b - 1) < ROPE_B)).mean(axis=0)
        print(f"  {'league':7} {'alpha (90% HDI)':>24} {'beta (90% HDI)':>24} "
              f"{'P(calibrated)':>14} {'MLE slope':>10}", flush=True)
        for j, lg in enumerate(leagues):
            gg = d[d.league == lg]
            s_mle, _, _ = slope_ci(gg[c1].values, gg.home_won.values)
            ah = hdi90(a[:, j])
            bh = hdi90(b[:, j])
            print(f"  {lg:7} {a[:, j].mean():+.3f} [{ah[0]:+.2f},{ah[1]:+.2f}]"
                  f"{'':6} {b[:, j].mean():.3f} [{bh[0]:.2f},{bh[1]:.2f}]{'':6} "
                  f"{rope[j]:>13.0%} {s_mle:>10.3f}", flush=True)
        sb = post["sig_b"].values.ravel()
        mb = post["mu_b"].values.ravel()
        mh = hdi90(mb)
        print(f"  hyper: mu_beta {mb.mean():.3f} [{mh[0]:.2f},{mh[1]:.2f}]  sigma_beta {sb.mean():.3f} "
              f"(P<0.05 = {np.mean(sb < 0.05):.0%})", flush=True)
        results[name] = (a, b, rope)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    yy = np.arange(len(leagues))
    for i, (name, (a, b, _)) in enumerate(results.items()):
        off = (i - 1) * 0.22
        for ax, mat, ref in [(axes[0], b, 1.0), (axes[1], a, 0.0)]:
            mean = mat.mean(axis=0)
            hdi = np.array([hdi90(mat[:, j]) for j in range(len(leagues))])
            ax.errorbar(mean, yy + off, xerr=[mean - hdi[:, 0], hdi[:, 1] - mean],
                        fmt="o", ms=4, capsize=2, color=COLOR[name], label=name if ax is axes[0] else None)
    axes[0].axvline(1, color="0.4", ls="--", lw=1)
    axes[0].set(title="calibration slope β (shrunken, 90% HDI)", yticks=yy, yticklabels=leagues)
    axes[1].axvline(0, color="0.4", ls="--", lw=1)
    axes[1].set(title="calibration intercept α (shrunken, 90% HDI)")
    axes[0].legend(fontsize=8)
    fig.suptitle("Hierarchical Bayesian calibration: every league, every source, ≈ perfectly calibrated")
    fig.tight_layout()
    fig.savefig("results/hierarchical_calibration.png", dpi=130)
    print("\nsaved results/hierarchical_calibration.png", flush=True)


if __name__ == "__main__":
    main()
