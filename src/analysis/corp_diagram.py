"""CORP reliability diagrams (Dimitriadis-Gneiting-Jordan 2021) with consistency bands.

Isotonic (PAV) recalibration replaces binned reliability curves — no binning
choices, optimal in-sample recalibration — with pointwise consistency bands
resampled under the null of perfect calibration (y* ~ Bernoulli(p), refit PAV,
5-95% envelope). A curve inside its band = calibration indistinguishable from
perfect at that probability level. MCB/DSC annotated per source (x1000).
"""
from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.isotonic import IsotonicRegression

from src.analysis.three_way import SRC, COLOR, load
from src.analysis.compare import stacked
from src.analysis.referee import corp

B = 200
GRID = np.linspace(0.01, 0.99, 99)
RNG = np.random.default_rng(7)


def band(p, b=B):
    """5-95% envelope of the isotonic fit under perfect calibration."""
    fits = np.empty((b, len(GRID)))
    for i in range(b):
        ystar = RNG.random(len(p)) < p
        iso = IsotonicRegression(out_of_bounds="clip").fit(p, ystar.astype(float))
        fits[i] = iso.predict(GRID)
    return np.quantile(fits, 0.05, axis=0), np.quantile(fits, 0.95, axis=0)


def main():
    d = load()
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.6), sharey=True)
    for ax, (name, (c1, c2)) in zip(axes, SRC.items()):
        p, y = stacked(d, c1, c2)
        iso = IsotonicRegression(out_of_bounds="clip").fit(p, y.astype(float))
        lo, hi = band(p)
        m = corp(p, y)
        inside = float(np.mean((iso.predict(GRID) >= lo) & (iso.predict(GRID) <= hi)))
        print(f"{name:11} MCB={m['MCB']*1000:.2f}  DSC={m['DSC']*1000:.1f}  "
              f"CORP curve inside 90% consistency band: {inside:.0%} of [0.01,0.99]", flush=True)
        ax.fill_between(GRID, lo, hi, color="0.85", label="90% consistency band")
        ax.plot([0, 1], [0, 1], "--", color="0.5", lw=1)
        ax.plot(GRID, iso.predict(GRID), color=COLOR[name], lw=2, label="CORP (isotonic)")
        ax.hist(p, bins=40, weights=np.full_like(p, 0.08 / len(p) * 40),
                bottom=-0.002, color=COLOR[name], alpha=0.35)
        ax.set(title=f"{name}  (MCB {m['MCB']*1000:.1f}, DSC {m['DSC']*1000:.1f} ×10³)",
               xlabel="forecast probability", xlim=(0, 1), ylim=(-0.01, 1))
    axes[0].set_ylabel("conditional event frequency")
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle(f"CORP reliability, both sides stacked (n={2*len(d):,} forecasts)")
    fig.tight_layout()
    fig.savefig("results/corp_reliability.png", dpi=130)
    print("saved results/corp_reliability.png", flush=True)


if __name__ == "__main__":
    main()
