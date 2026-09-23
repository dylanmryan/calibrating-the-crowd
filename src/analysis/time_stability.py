"""Self-correction over time: a casino's edge is static, an instrument learns.

Two tests on existing data:
  1. Sub-period stability — the pooled dead heat could in principle hide
     regimes (one venue better early, worse late, averaging out). Split the
     sample into calendar quarters and run the full pairwise clustered-DM +
     TOST machinery inside each; the instrument hypothesis predicts the
     equivalence holds in EVERY period independently.
  2. The bias half-life — track the MLB win-by-1-2 cell gap (implied vs
     empirical) by era. CORRECTED 2026-08-28: the series this section
     previously tracked (+7.4 to +11.2pt, "not self-correcting") was the
     ladder-convention artifact retracted on 2026-08-23, not the market —
     an artifact naturally persists across eras. Under the settlement-
     verified convention (ladder_convention.cover_line) the aggregate cell
     is near-unbiased in every era. A second blind-spot claim stood here --
     the EXTRA-INNINGS cell (~+20pt, shared with the books) -- and it was
     RETRACTED 2026-09-23: splitting on `extras`, a state realized during the
     game, breaks the calibration identity mechanically, and a constant
     forecaster scores +21.19pt on the same split (extras_conditioning.py).
     No blind spot survives here, and the era-level extras figures are
     withdrawn with the parent claim rather than being reported as too rare
     to read.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.compare import brier
from src.analysis.rigor import cluster_dm
from src.analysis.three_way import SRC, load
from src.collect.kalshi_hist_prices import _rule_home
from src.analysis.ladder_convention import cover_line


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
    """The corrected 1-2-run cell by era; construction mirrors mlb_extras."""
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    sp = sp[sp.league == "MLB"]
    esp = pd.read_csv("data/processed/espn_games.csv")
    esp = esp[(esp.league == "MLB") & (esp.status == "STATUS_FINAL")].copy()
    esp = esp.rename(columns={"espn_id": "game_id"})
    inn = pd.read_csv("data/processed/mlb_innings.csv")[["game_id", "innings"]]
    esp = esp.merge(inn, on="game_id", how="inner")
    esp = esp[esp.innings >= 9]  # drop rain-shortened, as mlb_extras does
    esp["margin"] = esp.home_score - esp.away_score
    esp = esp[esp.margin != 0]
    info = esp.set_index("game_id")[["margin", "innings"]]
    ml = pd.read_csv("data/processed/games_master.csv")[["game_id", "kalshi_p1"]]
    sp = sp.merge(ml, on="game_id", how="left")
    sp["start"] = pd.to_datetime(sp.start_utc, utc=True, format="ISO8601")

    rows = []
    for gid, grp in sp.groupby("game_id"):
        if gid not in info.index:
            continue
        ev = grp["event_ticker"].iloc[0]
        codes = sorted(set(grp["team"]))
        rh = _rule_home(ev, codes) if len(codes) == 2 else None
        pml = grp["kalshi_p1"].iloc[0]
        if rh is None or pml != pml:
            continue
        margin = int(info.loc[gid, "margin"])
        extras = bool(info.loc[gid, "innings"] > 9)
        start = grp["start"].iloc[0]
        for side, sgn in (("home", +1), ("away", -1)):
            rungs = {r.threshold: r.prob for r in
                     grp[(grp.team == rh) == (side == "home")].itertuples(index=False)
                     if r.prob == r.prob}
            # index by cover line: "win by 1-2" is P(>=1) - P(>=3); for MLB the
            # cover-3 rung is threshold 3.5 (integer-line convention)
            bc = {cover_line("MLB", t): p for t, p in rungs.items()}
            if 3 not in bc:
                continue
            pwin = float(pml) if sgn == 1 else 1 - float(pml)
            sm = sgn * margin
            rows.append({"start": start, "extras": extras,
                         "imp": pwin - bc[3], "emp": float(sm in (1, 2))})
    d = pd.DataFrame(rows)

    print("\n=== 2. the corrected 1-2-run cell over time (self-correction test) ===", flush=True)
    print(f"  {'era':>14} {'sides':>7} {'implied':>8} {'empirical':>10} {'gap':>7} {'z':>6}"
          f"  | {'extras n':>8} {'extras gap':>10} {'z':>6}", flush=True)
    eras = [("2025 season", "2025-01-01", "2025-12-01"),
            ("2026 1st half", "2026-03-01", "2026-06-01"),
            ("2026 2nd half", "2026-06-01", "2026-09-01")]
    for label, a, b in eras:
        s = d[(d.start >= a) & (d.start < b)]
        if len(s) < 50:
            continue
        gap = s.emp.mean() - s.imp.mean()
        se = np.sqrt(s.emp.var(ddof=1) / len(s) + s.imp.var(ddof=1) / len(s))
        x = s[s.extras]
        if len(x) >= 10:
            gx = x.emp.mean() - x.imp.mean()
            sex = np.sqrt(x.emp.var(ddof=1) / len(x) + x.imp.var(ddof=1) / len(x))
            xtra = f"  | {len(x):>8,} {gx*100:>+9.1f}p {gx/sex:>+6.1f}"
        else:
            xtra = f"  | {len(x):>8,} {'--':>10} {'--':>6}"
        print(f"  {label:>14} {len(s):>7,} {s.imp.mean()*100:>7.1f}% {s.emp.mean()*100:>9.1f}% "
              f"{gap*100:>+6.1f}p {gap/se:>+6.1f}{xtra}", flush=True)
    print("  (the +7.4/+11.2pt series previously printed here was the ladder-", flush=True)
    print("   convention artifact, retracted 2026-08-23. Corrected, the aggregate", flush=True)
    print("   cell is near-unbiased in every era. The extras blind spot once", flush=True)
    print("   reported here was RETRACTED 2026-09-23 as a conditioning artifact", flush=True)
    print("   (extras_conditioning.py); its era-level figures are withdrawn too.)", flush=True)


def main():
    subperiod_stability()
    bias_half_life()


if __name__ == "__main__":
    main()
