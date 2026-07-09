"""Spread-ladder coherence: do independently-priced contracts form rational curves?

Gambling-like pricing would produce incoherent ladders; model-based forecasting
produces monotone, arbitrage-free probability curves. Tests per (game, team) ladder:

  1. Monotonicity: P(win by >t) must be non-increasing in t. Count/size violations (mids).
  2. Executable arbitrage: sell the higher threshold at its BID, buy the lower at its
     ASK -> riskless profit iff bid(t_hi) > ask(t_lo). Uses real quotes, not mids.
  3. Moneyline bracket: P(by >1.5) <= P(win) <= 1 - P(opp by >1.5) (cross-market coherence).
  4. Tail calibration: every threshold contract is a binary forecast with an outcome ->
     reliability at extreme probabilities the moneyline set never reaches.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.compare import brier, ece, reliability

TICK = 0.011  # one cent + epsilon: violations larger than a tick are economically real


def ladders(df):
    for (ev, team), g in df.groupby(["event_ticker", "team"]):
        g = g.sort_values("threshold")
        if len(g) >= 3:
            yield ev, team, g


def main(path="data/processed/kalshi_spread_prices.csv"):
    df = pd.read_csv(path)
    print(f"threshold contracts priced: {len(df):,} | games: {df.game_id.nunique():,} "
          f"| ladders(>=3 rungs): {sum(1 for _ in ladders(df)):,}", flush=True)
    print(f"source mix: {df.src.value_counts().to_dict()}", flush=True)

    # --- 1&2: monotonicity + executable arbitrage per ladder ---
    stats = []
    for ev, team, g in ladders(df):
        p = g["prob"].values
        diffs = np.diff(p)  # should be <= 0
        viol = diffs > TICK
        n_arb = 0
        bid, ask = g["yes_bid"].values, g["yes_ask"].values
        if not (np.isnan(bid).all() or np.isnan(ask).all()):
            for i in range(len(g) - 1):  # adjacent rungs
                if not (np.isnan(bid[i + 1]) or np.isnan(ask[i])) and bid[i + 1] - ask[i] > 1e-9:
                    n_arb += 1
        stats.append({"league": g.league.iloc[0], "rungs": len(g),
                      "n_viol": int(viol.sum()), "max_viol": float(diffs.max()),
                      "n_arb": n_arb, "src": g.src.mode()[0]})
    s = pd.DataFrame(stats)
    print("\n=== ladder coherence ===", flush=True)
    print(f"ladders analyzed: {len(s):,}  (median rungs {int(s.rungs.median())})", flush=True)
    print(f"perfectly monotone (mids, tick-tolerance): {(s.n_viol==0).mean():.1%}", flush=True)
    print(f"adjacent-pair violation rate: {s.n_viol.sum()/ (s.rungs-1).sum():.2%} of all rungs", flush=True)
    print(f"ladders w/ EXECUTABLE arbitrage (bid/ask crossing): {(s.n_arb>0).mean():.2%}", flush=True)
    print("\nby source (book-mid = live order book; trade-recon = reconstructed):", flush=True)
    for src, g in s.groupby("src"):
        print(f"  {src:11} ladders={len(g):6} monotone={(g.n_viol==0).mean():6.1%} "
              f"arb-ladders={(g.n_arb>0).mean():6.2%}", flush=True)
    print("\nby league:", flush=True)
    for lg, g in s.groupby("league"):
        print(f"  {lg:5} ladders={len(g):6} monotone={(g.n_viol==0).mean():6.1%} "
              f"arb={(g.n_arb>0).mean():6.2%}", flush=True)

    # --- 3: moneyline bracket ---
    try:
        ml = pd.read_csv("data/processed/kalshi_hist_prices.csv")[["game_id", "kalshi_p1", "kalshi_p2"]]
        master = pd.read_csv("data/processed/games_master.csv")[["game_id", "team1", "team2"]]
        ml = ml.merge(master, on="game_id")
        lo = df[df.threshold == 1.5].groupby(["game_id", "team"])["prob"].first().reset_index()
        checks = ok = 0
        for gid, g in lo.groupby("game_id"):
            row = ml[ml.game_id == gid]
            if len(row) != 1 or len(g) != 2:
                continue
            r = row.iloc[0]
            p15 = dict(zip(g.team, g.prob))
            t1, t2 = list(p15)
            for a, b, pwin in ((t1, t2, None),):
                pass
            # bracket per team: P(by>1.5) <= P(win); with two sides also P(win) <= 1 - P(opp by>1.5)
            probs = sorted(p15.values())
            pw = sorted([r.kalshi_p1, r.kalshi_p2])
            checks += 1
            if probs[0] <= pw[0] + TICK and probs[1] <= pw[1] + TICK and \
               pw[0] <= 1 - probs[1] + TICK and pw[1] <= 1 - probs[0] + TICK:
                ok += 1
        if checks:
            print(f"\n=== moneyline bracket consistency ===", flush=True)
            print(f"games checked: {checks:,}  consistent: {ok/checks:.1%}", flush=True)
    except FileNotFoundError:
        pass

    # --- 4: tail calibration on all threshold contracts ---
    print("\n=== threshold-contract calibration (extreme probabilities) ===", flush=True)
    print(f"Brier={brier(df.prob, df.won):.4f}  ECE={ece(df.prob.values, df.won.values):.4f}  n={len(df):,}", flush=True)
    t = reliability(df.prob.values, df.won.values, nbins=20)
    lowp = df[df.prob <= 0.10]
    print(f"longshot rungs (p<=0.10): n={len(lowp):,} mean_pred={lowp.prob.mean():.4f} "
          f"obs={lowp.won.mean():.4f}", flush=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))
    ax1.plot([0, 1], [0, 1], "k--", lw=1)
    ax1.scatter(t.pred, t.obs, s=np.sqrt(t.n) * 3, color="tab:purple", alpha=0.8)
    ax1.set(xlabel="Predicted P(win by > t)", ylabel="Observed frequency",
            title=f"Spread-contract calibration (n={len(df):,})", xlim=(0, 1), ylim=(0, 1))
    ax1.set_aspect("equal")
    ax2.hist(s.n_viol, bins=range(0, int(s.n_viol.max()) + 2), color="tab:red", alpha=0.7)
    ax2.set(xlabel="monotonicity violations per ladder", ylabel="ladders",
            title=f"Coherence ({(s.n_viol==0).mean():.0%} perfectly monotone)")
    fig.tight_layout(); fig.savefig("results/spread_coherence.png", dpi=130)
    print("saved results/spread_coherence.png", flush=True)


if __name__ == "__main__":
    main()
