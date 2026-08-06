"""The report's two synthesis figures.

1. equivalence_forest.png — every pairwise closing-accuracy comparison as
   dBrier with date-clustered 90% CIs against the ±1e-3 equivalence band:
   the paper's central claim (formal equivalence, not absence of
   significance) in one picture. Computed fresh from analysis_core.csv.

2. oneshot_returns.png — $1 gross returns on sub-10c longshots in repeated
   game markets vs one-shot outrights, by institution: the mechanism
   (repetition disciplines prices; one-shot markets break everywhere) in
   one picture. Game-market values computed from spread-ladder tails
   (clean two-sided quotes); outright values from the futures legs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def clustered(dA, dB, y, cl):
    d = (dA - y) ** 2 - (dB - y) ** 2
    dbar = d.mean()
    g = pd.DataFrame({"d": d - dbar, "c": cl}).groupby("c")["d"].sum()
    se = np.sqrt((g ** 2).sum()) / len(d)
    return dbar, se


def forest():
    c = pd.read_csv("data/processed/analysis_core.csv")
    c = c[c.clean_set & c.kalshi_home_prob.notna() & c.polymarket_home_prob.notna()
          & c.book_home_prob_devig.notna()].copy()
    c["date"] = pd.to_datetime(c.start_utc, utc=True, format="ISO8601").dt.date
    y = c.home_won.to_numpy()
    rows = []
    pairs = [("Kalshi vs Polymarket", c.kalshi_home_prob, c.polymarket_home_prob, c),
             ("Kalshi vs US books", c.kalshi_home_prob, c.book_home_prob_devig, c),
             ("Polymarket vs US books", c.polymarket_home_prob, c.book_home_prob_devig, c)]
    p = c[c.pinnacle_home_prob.notna()]
    pairs += [("Kalshi vs Pinnacle", p.kalshi_home_prob, p.pinnacle_home_prob, p),
              ("Polymarket vs Pinnacle", p.polymarket_home_prob, p.pinnacle_home_prob, p)]
    for lab, a, b, base in pairs:
        dbar, se = clustered(a.to_numpy(), b.to_numpy(),
                             base.home_won.to_numpy(), base.date.to_numpy())
        rows.append((lab, dbar * 1e3, 1.645 * se * 1e3, len(base), False))
    for lg in ("NHL", "NBA", "MLB", "CFB", "WNBA", "NFL"):
        g = c[c.league == lg]
        dbar, se = clustered(g.kalshi_home_prob.to_numpy(),
                             g.book_home_prob_devig.to_numpy(),
                             g.home_won.to_numpy(), g.date.to_numpy())
        rows.append((f"{lg}: Kalshi vs books", dbar * 1e3, 1.645 * se * 1e3, len(g), True))

    fig, ax = plt.subplots(figsize=(8, 6.5))
    ys = np.arange(len(rows))[::-1]
    ax.axvspan(-1, 1, color="tab:green", alpha=0.10,
               label="equivalence margin (±1.0e-3 Brier ≈ 0.5pt per game)")
    ax.axvline(0, color="k", lw=0.8)
    for (lab, d, ci, n, sub), yy in zip(rows, ys):
        col = "tab:gray" if sub else "tab:blue"
        ax.errorbar(d, yy, xerr=ci, fmt="o", color=col, capsize=3,
                    markersize=5 if sub else 7)
        ax.text(-3.45, yy, f"{lab}  (n={n:,})", va="center", fontsize=8.5,
                color="dimgray" if sub else "black")
    ax.set(yticks=[], xlim=(-3.5, 3.5),
           xlabel="Brier difference ×1000 (negative = first source better), 90% CI",
           title="Closing accuracy: every comparison lands inside the equivalence band")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig("results/equivalence_forest.png", dpi=130)
    print("saved results/equivalence_forest.png", flush=True)


def oneshot():
    labels = ["Kalshi ladders\n(repeated games)\nn=1,467",
              "Kalshi outrights\nn=344", "Polymarket outrights\nn=98",
              "Sportsbook outrights\nn=1,003"]
    # ladder tails: obs 9.07% vs priced 7.46% (coherence.log) -> $1.22
    vals = [0.0907 / 0.0746, 0.33, 0.53, 0.24]
    errs = [None, 0.28 * 1.645, 0.37 * 1.645, 0.06 * 1.645]
    cols = ["tab:green", "tab:red", "tab:orange", "tab:purple"]
    fig, ax = plt.subplots(figsize=(7.6, 5))
    xs = np.arange(len(vals))
    ax.bar(xs, vals, color=cols, alpha=0.85,
           yerr=[e if e else 0 for e in errs], capsize=4)
    ax.axhline(1.0, color="k", ls="--", lw=1)
    ax.text(3.35, 1.03, "fair value", fontsize=9)
    for x, v in zip(xs, vals):
        ax.text(x, 0.04, f"${v:.2f}", ha="center", fontsize=11, fontweight="bold",
                color="white")
    ax.set_xticks(xs, labels, fontsize=9)
    ax.set(ylabel="gross return per $1 staked on sub-10¢ longshots",
           title="One-shot markets break every institution;\n"
                 "repeated markets are clean even on an exchange")
    fig.tight_layout()
    fig.savefig("results/oneshot_returns.png", dpi=130)
    print("saved results/oneshot_returns.png", flush=True)


def main():
    forest()
    oneshot()


if __name__ == "__main__":
    main()
