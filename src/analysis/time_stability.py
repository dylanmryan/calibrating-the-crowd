"""Self-correction over time: a casino's edge is static, an instrument learns.

Two tests on existing data:
  1. Sub-period stability — the pooled dead heat could in principle hide
     regimes (one venue better early, worse late, averaging out). Split the
     sample into calendar quarters and run the full pairwise clustered-DM +
     TOST machinery inside each; the instrument hypothesis predicts the
     equivalence holds in EVERY period independently.
  2. The bias half-life — the one real crack (Kalshi's MLB ladder
     underpricing narrow wins) should SHRINK as the platform matures if
     markets self-correct. Track the win-by-1-2 cell gap (implied vs
     empirical) by era: 2025 season vs 2026 season halves.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.compare import brier
from src.analysis.rigor import cluster_dm
from src.analysis.three_way import SRC, load
from src.collect.kalshi_hist_prices import _rule_home


def subperiod_stability():
    d = load()
    d["date"] = d.start_utc.astype(str).str[:10]
    d["q"] = pd.to_datetime(d.start_utc, utc=True, format="ISO8601").dt.to_period("Q").astype(str)
    y_all = d.home_won.values
    print("=== 1. does the dead heat hold in every sub-period? ===", flush=True)
    print(f"  {'quarter':>7} {'n':>6} {'K':>7} {'P':>7} {'B':>7} "
          f"{'worst pair z':>13} {'delta_min':>10}", flush=True)
    for q, g in sorted(d.groupby("q")):
        if len(g) < 200:
            continue
        y = g.home_won.values
        briers = [brier(g[c1].values, y) for _, (c1, _) in SRC.items()]
        worst_z, worst_dmin = 0.0, 0.0
        pairs = [("kalshi_p1", "poly_p1"), ("kalshi_p1", "book_p1"), ("poly_p1", "book_p1")]
        for a, b in pairs:
            dbar, se, z, p, (lo, hi) = cluster_dm(g[a].values, g[b].values, y, g.date.values)
            worst_z = max(worst_z, abs(z))
            worst_dmin = max(worst_dmin, max(abs(lo), abs(hi)))
        eq = "EQUIV@1e-3" if worst_dmin <= 1e-3 else f"(power-limited)"
        print(f"  {q:>7} {len(g):>6,} {briers[0]:>7.4f} {briers[1]:>7.4f} {briers[2]:>7.4f} "
              f"{worst_z:>13.2f} {worst_dmin*1000:>9.2f}e-3 {eq}", flush=True)
    print("  (worst pair z < 1.96 in a period = no detectable difference there;", flush=True)
    print("   delta_min = smallest TOST margin all three pairs meet in that period)", flush=True)


def bias_half_life():
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    esp = pd.read_csv("data/processed/espn_games.csv")[
        ["espn_id", "home_score", "away_score"]].rename(columns={"espn_id": "game_id"})
    mlb = sp[sp.league == "MLB"].merge(esp, on="game_id")
    mlb = mlb[mlb.home_score.notna()].copy()
    mlb["start"] = pd.to_datetime(mlb.start_utc, utc=True, format="ISO8601")

    print("\n=== 2. is the MLB narrow-margin bias shrinking? (self-correction test) ===", flush=True)
    print(f"  {'era':>14} {'sides':>7} {'implied':>8} {'empirical':>10} {'gap':>7} {'z':>6}", flush=True)
    # win-by-1-2 cell per side: P(0 < M_side <= 2.5) from that side's ladder
    # cell = P(win) - P(win by 3+): use rungs 2.5 (P(M>2.5)) and the side winning
    eras = [("2025 season", "2025-01-01", "2025-12-01"),
            ("2026 1st half", "2026-03-01", "2026-06-01"),
            ("2026 2nd half", "2026-06-01", "2026-09-01")]
    for label, a, b in eras:
        g = mlb[(mlb.start >= a) & (mlb.start < b)]
        rows = []
        for (gid, ev), gg in g.groupby(["game_id", "event_ticker"]):
            codes = sorted(set(gg.team))
            rh = _rule_home(ev, codes) if len(codes) == 2 else None
            if rh is None:
                continue
            hs, as_ = gg.home_score.iloc[0], gg.away_score.iloc[0]
            for side_code, won_by in ((rh, hs - as_), ([c for c in codes if c != rh][0], as_ - hs)):
                s = gg[gg.team == side_code]
                r25 = s[s.threshold == 2.5]
                if len(r25) != 1:
                    continue
                # implied P(win by 1-2) needs P(win): approximate with ladder
                # complement pair: P(M > -0.5)... use moneyline-free version:
                # cell implied = P(M > 0.5)-ish unavailable -> use the matched
                # construction from ladder_vs_books: P(win by 1-2) =
                # P(win) - P(M > 2.5); P(win) from 0.5 rung if quoted else skip
                r05 = s[s.threshold == 0.5]
                if len(r05) == 1:
                    imp = float(r05.prob.iloc[0]) - float(r25.prob.iloc[0])
                else:
                    continue
                rows.append({"imp": imp, "emp": 1.0 if won_by in (1, 2) else 0.0})
        if len(rows) < 50:
            # fall back: use all sides with 2.5 rung + realized, implied via
            # P(win)-P(win by 3+) where P(win) comes from the master moneyline
            ml = pd.read_csv("data/processed/games_master.csv")[
                ["game_id", "kalshi_p1", "kalshi_p2"]]
            rows = []
            for (gid, ev), gg in g.groupby(["game_id", "event_ticker"]):
                codes = sorted(set(gg.team))
                rh = _rule_home(ev, codes) if len(codes) == 2 else None
                if rh is None:
                    continue
                mlrow = ml[ml.game_id == gid]
                if not len(mlrow) or mlrow.kalshi_p1.isna().iloc[0]:
                    continue
                hs, as_ = gg.home_score.iloc[0], gg.away_score.iloc[0]
                pwin = {rh: float(mlrow.kalshi_p1.iloc[0])}
                other = [c for c in codes if c != rh][0]
                pwin[other] = float(mlrow.kalshi_p2.iloc[0])
                for side_code, won_by in ((rh, hs - as_), (other, as_ - hs)):
                    s = gg[(gg.team == side_code) & (gg.threshold == 2.5)]
                    if len(s) != 1:
                        continue
                    imp = pwin[side_code] - float(s.prob.iloc[0])
                    rows.append({"imp": imp, "emp": 1.0 if won_by in (1, 2) else 0.0})
        if not rows:
            continue
        r = pd.DataFrame(rows)
        gap = (r.emp.mean() - r.imp.mean())
        se = np.sqrt(r.emp.var(ddof=1) / len(r))
        print(f"  {label:>14} {len(r):>7,} {r.imp.mean()*100:>7.1f}% {r.emp.mean()*100:>9.1f}% "
              f"{gap*100:>+6.1f}p {gap/se:>+6.1f}", flush=True)
    print("  (a shrinking gap across eras = the market learning its own blind", flush=True)
    print("   spot; a static gap = the cost-band shelter holding it in place)", flush=True)


def main():
    subperiod_stability()
    bias_half_life()


if __name__ == "__main__":
    main()
