"""Inference hardening for the three-way dead heat.

1. Cluster-robust DM tests (cluster by date: same-day games share news/conditions).
2. TOST equivalence: turn "not significant" into "statistically equivalent within ±δ".
   We report the 90% CI of each pairwise Brier difference — equivalence holds at any
   margin δ wider than that CI — and translate every margin onto the probability
   scale, because ΔBrier = ε² for a systematic offset ε and the two are easy to
   confuse (an earlier note in this file glossed δ=1e-3 as 0.5pt; it is 3.16pt).
   Margins are anchored economically: an edge below (taker cost × price) cannot be
   monetised, so that is the smallest difference worth calling real.
   See docs/methodology-decisions.md D2.
3. De-vig robustness: recompute book probabilities with Shin's model (which accounts
   for insider/informed betting) instead of multiplicative normalization; re-test.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.three_way import load, SRC


# All-in retail taker cost as a share of notional [immediacy.log; Kalshi's taker
# path ≈ the books' 4.1% vig]. Anchors the equivalence margin: an edge smaller
# than (cost × price) cannot be monetised by anyone actually paying that cost.
TAKER_COST = 0.042

# Pre-stated TOST margin, fixed 2026-07-21 before the comparisons that rest on
# it. It does not move — see docs/methodology-decisions.md D2.
DELTA_PRESTATED = 1.0e-3

ANCHOR_PRICES = (0.25, 0.50, 0.75)


def eps_pt(delta):
    """Systematic probability offset, in percentage points, that a Brier margin
    δ tolerates. For a forecast displaced from the truth by ε, the Brier excess
    is exactly ε², so the offset a margin admits is √δ."""
    return np.sqrt(delta) * 100


def anchored_margin(price, cost=TAKER_COST):
    """Brier margin below which an edge is unmonetisable at this contract price.
    Cost is a share of notional and notional is the contract price, so breakeven
    edge is cost × price; converting to the Brier scale squares it."""
    return (cost * price) ** 2


def equivalence_report(pairs):
    """Margin ladder on the probability scale, then each pair's TOST verdict."""
    print("\n=== equivalence margins, translated to the probability scale ===", flush=True)
    print("  ΔBrier = ε² for a systematic offset ε, so a margin δ admits √δ:", flush=True)
    ladder = [anchored_margin(p) for p in ANCHOR_PRICES] + [DELTA_PRESTATED]
    print("    " + "   ".join(f"δ={dl*1000:.2f}e-3 -> {eps_pt(dl):.2f}pt" for dl in ladder), flush=True)

    print(f"\n  Economic anchor: an edge below (taker cost × price) cannot be monetised.", flush=True)
    print(f"  All-in taker cost {TAKER_COST*100:.1f}% of notional [immediacy.log].", flush=True)
    for pr in ANCHOR_PRICES:
        dl = anchored_margin(pr)
        print(f"    price {pr:.2f} -> breakeven edge {TAKER_COST*pr*100:.2f}pt "
              f"-> δ={dl*1000:.3f}e-3", flush=True)
    print(f"  The pre-stated δ={DELTA_PRESTATED*1000:.1f}e-3 coincides with the anchor at "
          f"favourite prices (p≈0.75);\n  it was fixed before these comparisons and is "
          f"not re-chosen here.", flush=True)

    margins = [(f"p={pr:.2f}", anchored_margin(pr)) for pr in ANCHOR_PRICES]
    margins.append(("pre-stated", DELTA_PRESTATED))

    print("\n=== TOST verdicts: equivalent at δ iff the 90% CI lies inside ±δ ===", flush=True)
    head = f"  {'pair':<26}{'|CI|max':>11}{'':3}" + "".join(f"{lab:>12}" for lab, _ in margins)
    print(head, flush=True)
    print("  " + "-" * (len(head) - 2), flush=True)
    for name, bound in pairs:
        cells = "".join(f"{'yes' if bound < dl else 'NO':>12}" for _, dl in margins)
        print(f"  {name:<26}{bound*1000:>8.3f}e-3{'':3}{cells}", flush=True)
    print("\n  A 'NO' at the tighter anchors reports the measurement's power, not a", flush=True)
    print("  difference between venues: it means the comparison stops resolving below", flush=True)
    print("  an edge only a zero-cost participant could ever act on.", flush=True)


def cluster_dm(pA, pB, y, clusters):
    """DM on squared-error differential with cluster-robust (by date) SE."""
    d = ((np.asarray(pA) - y) ** 2 - (np.asarray(pB) - y) ** 2)
    n = len(d)
    dbar = d.mean()
    g = pd.DataFrame({"d": d - dbar, "c": clusters}).groupby("c")["d"].sum()
    se = np.sqrt((g ** 2).sum()) / n
    z = dbar / se
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    ci90 = (dbar - 1.645 * se, dbar + 1.645 * se)
    return dbar, se, z, p, ci90


def shin_two_way(pi1, pi2):
    """Shin (1993) fair probabilities for a 2-outcome market from raw implied probs."""
    PI = pi1 + pi2
    lo, hi = 0.0, 0.4
    for _ in range(60):  # bisection on insider fraction z
        z = (lo + hi) / 2
        p1 = (np.sqrt(z * z + 4 * (1 - z) * pi1 * pi1 / PI) - z) / (2 * (1 - z))
        p2 = (np.sqrt(z * z + 4 * (1 - z) * pi2 * pi2 / PI) - z) / (2 * (1 - z))
        if p1 + p2 > 1:
            lo = z
        else:
            hi = z
    s = p1 + p2
    return p1 / s, p2 / s


def main():
    d = load()
    y = d["home_won"].values
    dates = pd.to_datetime(d["start_utc"], utc=True, format="ISO8601").dt.date.values
    n_days = len(set(dates))
    print(f"clean all-three games: {len(d):,} across {n_days} dates (clusters)\n", flush=True)

    print("=== cluster-robust (by date) pairwise DM + 90% CI of Brier difference ===", flush=True)
    names = list(SRC)
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            dbar, se, z, p, ci = cluster_dm(d[SRC[a][0]], d[SRC[b][0]], y, dates)
            bound = max(abs(ci[0]), abs(ci[1]))
            pairs.append((f"{a} - {b}", bound))
            print(f"  {a} - {b}: ΔBrier={dbar*1000:+.3f}e-3  clustSE={se*1000:.3f}e-3  "
                  f"z={z:+.2f} p={p:.3f}  90%CI=({ci[0]*1000:+.3f},{ci[1]*1000:+.3f})e-3  "
                  f"|CI|max={bound*1000:.3f}e-3 = {eps_pt(bound):.2f}pt", flush=True)

    equivalence_report(pairs)

    print("\n=== de-vig robustness: multiplicative vs Shin (book fair probs) ===", flush=True)
    sb = pd.read_csv("data/processed/sportsbook_hist_prices.csv")[["game_id", "book_raw1", "book_raw2"]]
    m = d.merge(sb, on="game_id", how="inner").dropna(subset=["book_raw1", "book_raw2"])
    yy = m["home_won"].values
    dd = pd.to_datetime(m["start_utc"], utc=True, format="ISO8601").dt.date.values
    shin = np.array([shin_two_way(a, b) for a, b in zip(m.book_raw1, m.book_raw2)])
    m["book_shin1"] = shin[:, 0]
    from src.analysis.compare import brier
    print(f"  book Brier multiplicative={brier(m.book_p1, yy):.4f}  Shin={brier(m.book_shin1, yy):.4f}", flush=True)
    print(f"  mean |shift| in book prob: {np.abs(m.book_shin1-m.book_p1).mean()*100:.3f} pts", flush=True)
    for a in ("Kalshi", "Polymarket"):
        dbar, se, z, p, ci = cluster_dm(m[SRC[a][0]], m["book_shin1"], yy, dd)
        print(f"  {a} - Book(Shin): ΔBrier={dbar*1000:+.3f}e-3  z={z:+.2f} p={p:.3f}", flush=True)


if __name__ == "__main__":
    main()
