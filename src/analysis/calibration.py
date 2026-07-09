"""Calibration analysis: bin predicted probabilities vs observed win rates.

Produces a reliability diagram (observed frequency vs predicted probability) and
Brier scores, overall and per league. Well-calibrated => points hug the diagonal.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BINS = np.linspace(0, 1, 11)  # 10 fixed-width bins


def reliability_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per-bin mean predicted prob, observed win rate, and count."""
    d = df.copy()
    d["bin"] = pd.cut(d["implied_prob"], BINS, include_lowest=True)
    g = d.groupby("bin", observed=True).agg(
        pred=("implied_prob", "mean"),
        obs=("won", "mean"),
        n=("won", "size"),
    ).dropna()
    return g.reset_index()


def brier(df: pd.DataFrame) -> float:
    return float(np.mean((df["implied_prob"] - df["won"]) ** 2))


def plot(df: pd.DataFrame, out: str = "results/reliability_kalshi.png") -> None:
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfect calibration")

    tbl = reliability_table(df)
    ax.plot(tbl["pred"], tbl["obs"], "-", color="0.4", lw=1, zorder=1)
    ax.scatter(tbl["pred"], tbl["obs"], s=tbl["n"] / tbl["n"].max() * 400 + 20,
               color="tab:blue", alpha=0.7, zorder=2,
               label=f"all leagues (Brier={brier(df):.3f}, n={len(df):,})")

    ax.set_xlabel("Predicted probability (Kalshi closing book mid)")
    ax.set_ylabel("Observed win frequency")
    ax.set_title("Kalshi calibration — pre-game moneyline (all sports)")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("equal")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    print(f"saved {out}", flush=True)


if __name__ == "__main__":
    df = pd.read_csv("data/processed/kalshi_prices.csv")
    # drop pathological quotes: no book, or absurd spreads (thin/stale markets)
    df = df[(df["implied_prob"] > 0) & (df["implied_prob"] < 1)]
    print(f"priced games: {len(df):,}", flush=True)
    print(f"overall Brier: {brier(df):.4f}", flush=True)
    print("\nreliability table (all sports):", flush=True)
    print(reliability_table(df).to_string(index=False), flush=True)
    print("\nper-league Brier:", flush=True)
    for lg, g in df.groupby("league"):
        print(f"  {lg:6} n={len(g):5}  Brier={brier(g):.4f}  mean_spread={g['spread'].mean():.3f}", flush=True)
    plot(df)
