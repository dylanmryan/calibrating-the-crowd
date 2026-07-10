"""When does the dead heat form? Horizon-resolved three-way equivalence.

The closing three-way is a statistical tie. Two readings: (a) the venues
aggregate information independently and all arrive at the truth, or (b) the
exchanges import the books' work and converge onto it by start. They separate
at T-24h: under (a) the sources are already equivalent a day out; under (b)
the books lead early and the gap closes.

Inputs: kalshi_horizons (last-trade path), poly_horizons (CLOB path),
sportsbook_open_prices (T-24h consensus), games_master (close + outcome).
Constant sample throughout (varying-n horizon columns are composition-biased).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.compare import brier
from src.analysis.rigor import cluster_dm

H = [1440, 720, 360, 180, 60, 15, 0]


def load():
    k = pd.read_csv("data/processed/kalshi_horizons.csv")
    q = pd.read_csv("data/processed/poly_horizons.csv")
    o = pd.read_csv("data/processed/sportsbook_open_prices.csv")[["game_id", "book24_p1"]]
    m = pd.read_csv("data/processed/games_master.csv")[
        ["game_id", "league", "start_utc", "book_p1", "outcome", "outcome_disagree"]]
    d = (k.drop(columns=["league", "start_utc"]).merge(q.drop(columns=["league", "start_utc"]), on="game_id")
           .merge(o, on="game_id").merge(m, on="game_id"))
    d = d[d.outcome.notna() & ~d.outcome_disagree.fillna(False) & (d.n_trades >= 10)]
    d = d.dropna(subset=["p_h1440", "p_h0", "q_h1440", "q_h0", "book24_p1", "book_p1"])
    d["home_won"] = (d.outcome == 1).astype(int)
    return d


def main():
    d = load()
    y = d.home_won.values
    dates = pd.to_datetime(d.start_utc, utc=True, format="ISO8601").dt.date.values
    print(f"constant sample (all sources at 24h AND close): {len(d):,} games", flush=True)
    print(dict(d.league.value_counts()), flush=True)

    print("\n=== T-24h three-way (a full day before start) ===", flush=True)
    srcs24 = {"Kalshi 24h": "p_h1440", "Poly 24h": "q_h1440", "Book 24h": "book24_p1"}
    for n_, c in srcs24.items():
        print(f"  {n_:11} Brier={brier(d[c], y):.4f}", flush=True)
    names = list(srcs24)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            db, se, z, p, ci = cluster_dm(d[srcs24[a]], d[srcs24[b]], y, dates)
            print(f"  {a} - {b}: ΔBrier={db*1000:+.3f}e-3  z={z:+.2f} p={p:.3f}  "
                  f"90%CI=({ci[0]*1000:+.2f},{ci[1]*1000:+.2f})e-3", flush=True)

    print("\n=== closing three-way (same constant sample) ===", flush=True)
    srcs0 = {"Kalshi 0h": "p_h0", "Poly 0h": "q_h0", "Book close": "book_p1"}
    for n_, c in srcs0.items():
        print(f"  {n_:11} Brier={brier(d[c], y):.4f}", flush=True)

    print("\n=== convergence: mean |gap| between sources, 24h vs close ===", flush=True)
    pairs = [("Kalshi", "Book", "p_h1440", "book24_p1", "p_h0", "book_p1"),
             ("Poly", "Book", "q_h1440", "book24_p1", "q_h0", "book_p1"),
             ("Kalshi", "Poly", "p_h1440", "q_h1440", "p_h0", "q_h0")]
    for a, b, a24, b24, a0, b0 in pairs:
        g24 = (d[a24] - d[b24]).abs().mean()
        g0 = (d[a0] - d[b0]).abs().mean()
        print(f"  |{a}-{b}|: 24h={g24*100:.2f}pts -> close={g0*100:.2f}pts", flush=True)

    print("\n=== do the books sharpen too? (open-vs-close, Page-Clemen for books) ===", flush=True)
    db, se, z, p, _ = cluster_dm(d.book_p1, d.book24_p1, y, dates)
    print(f"  book close vs book 24h: ΔBrier={db*1000:+.3f}e-3  z={z:+.2f} p={p:.3f}", flush=True)
    print(f"  mean |book move| 24h->close: {(d.book_p1-d.book24_p1).abs().mean()*100:.2f}pts", flush=True)

    print("\n=== Brier by horizon (constant sample; Kalshi & Poly paths) ===", flush=True)
    print(f"  {'horizon':>9} {'Kalshi':>8} {'Poly':>8}", flush=True)
    sub = d.dropna(subset=[f"p_h{h}" for h in H] + [f"q_h{h}" for h in H])
    yy = sub.home_won.values
    for h in H:
        print(f"  T-{h:>4}min {brier(sub[f'p_h{h}'], yy):>8.4f} {brier(sub[f'q_h{h}'], yy):>8.4f}", flush=True)
    print(f"  (n={len(sub):,} with complete paths on both exchanges)", flush=True)


if __name__ == "__main__":
    main()
