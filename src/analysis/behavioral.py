"""Behavioral gambling fingerprints + the crowd-size mechanism.

If prediction-market prices carry FAN MONEY (gambling behavior), we expect:
  1. Home bias — home sides systematically over-priced.
  2. Popular-franchise premium — big-fanbase teams over-priced (price > outcome rate).
  3. Weekend/primetime degradation — recreational money worsens calibration.
Testing each per source (Kalshi / Polymarket / book): a bias present only in the
prediction markets is retail-crowd-specific; present everywhere = sports-wide.

Crowd-size mechanism: does accuracy require a crowd? Kalshi accuracy vs the book
benchmark as a function of the game's trade count (from the horizons collection).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.compare import ece
from src.analysis.three_way import load, SRC

POPULAR = {  # big-fanbase franchises (valuation/attendance leaders)
    "New York Yankees", "Los Angeles Dodgers", "Boston Red Sox", "Chicago Cubs",
    "Atlanta Braves", "Los Angeles Lakers", "Golden State Warriors", "Boston Celtics",
    "New York Knicks", "Chicago Bulls", "Dallas Cowboys", "Green Bay Packers",
    "Pittsburgh Steelers", "Philadelphia Eagles", "Kansas City Chiefs",
    "San Francisco 49ers", "Toronto Maple Leafs", "New York Rangers",
    "Boston Bruins", "Montreal Canadiens", "Chicago Blackhawks",
    "Indiana Fever", "New York Liberty", "Las Vegas Aces",
}


def _sided(d):
    """One row per contract-side: pred per source, won, side metadata."""
    rows = []
    for r in d.itertuples(index=False):
        start = pd.Timestamp(r.start_utc)
        wk = start.tz_convert("US/Eastern") if start.tzinfo else start
        weekend = wk.weekday() >= 4  # Fri/Sat/Sun
        for side, team, won in ((1, r.team1, r.outcome == 1), (2, r.team2, r.outcome == 2)):
            rows.append({"team": team, "won": int(won), "is_home": side == 1,
                         "popular": team in POPULAR, "weekend": weekend,
                         "kalshi": getattr(r, f"kalshi_p{side}"),
                         "poly": getattr(r, f"poly_p{side}"),
                         "book": getattr(r, f"book_p{side}")})
    return pd.DataFrame(rows)


def bias_test(g, col):
    """Mean (price - outcome): >0 = over-priced. Returns (bias, z)."""
    x = (g[col] - g["won"]).dropna()
    return x.mean(), x.mean() / (x.std() / np.sqrt(len(x)))


def main():
    d = load()
    s = _sided(d)
    print(f"contract-sides: {len(s):,}\n", flush=True)

    print("=== 1. home bias (price - outcome on home sides; >0 = over-priced) ===", flush=True)
    for name, col in [("Kalshi", "kalshi"), ("Polymarket", "poly"), ("Sportsbook", "book")]:
        b, z = bias_test(s[s.is_home], col)
        print(f"  {name:11} bias={b*100:+.2f} pts  z={z:+.2f}", flush=True)

    print("\n=== 2. popular-franchise premium ===", flush=True)
    pop, rest = s[s.popular], s[~s.popular]
    print(f"  popular-team sides: {len(pop):,}", flush=True)
    for name, col in [("Kalshi", "kalshi"), ("Polymarket", "poly"), ("Sportsbook", "book")]:
        bp, zp = bias_test(pop, col)
        br, _ = bias_test(rest, col)
        print(f"  {name:11} popular={bp*100:+.2f} pts (z={zp:+.2f})   others={br*100:+.2f}", flush=True)

    print("\n=== 3. weekend/primetime vs weekday calibration (ECE) ===", flush=True)
    for name, col in [("Kalshi", "kalshi"), ("Polymarket", "poly"), ("Sportsbook", "book")]:
        we = s[s.weekend].dropna(subset=[col]); wd = s[~s.weekend].dropna(subset=[col])
        print(f"  {name:11} weekend ECE={ece(we[col].values, we.won.values):.4f} (n={len(we):,})"
              f"   weekday ECE={ece(wd[col].values, wd.won.values):.4f} (n={len(wd):,})", flush=True)

    print("\n=== 4. crowd size: Kalshi accuracy vs trade count ===", flush=True)
    h = pd.read_csv("data/processed/kalshi_horizons.csv")[["game_id", "n_trades"]]
    m = d.merge(h, on="game_id").dropna(subset=["n_trades"])
    m["bucket"] = pd.qcut(m["n_trades"], 4, labels=["Q1 thin", "Q2", "Q3", "Q4 deep"])
    print(f"  {'bucket':>8} {'n':>6} {'median trades':>14} {'|K-book| gap':>13} {'Kalshi ECE':>11}", flush=True)
    for b, g in m.groupby("bucket", observed=True):
        gap = (g.kalshi_p1 - g.book_p1).abs().mean()
        p = np.concatenate([g.kalshi_p1, g.kalshi_p2]); yy = np.concatenate([g.outcome == 1, g.outcome == 2]).astype(float)
        print(f"  {str(b):>8} {len(g):>6,} {int(g.n_trades.median()):>14,} {gap*100:>12.2f}p {ece(p, yy):>11.4f}", flush=True)


if __name__ == "__main__":
    main()
