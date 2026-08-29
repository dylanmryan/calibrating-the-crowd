"""Power: what gap could we have SEEN, and where does "consistent" mean nothing?

Every equivalence statement in this project is only as strong as its power. The
per-league table reports some leagues as "consistent but underpowered"; this
module replaces that shrug with a number. For each subgroup and source pair it
reports the minimum detectable effect

    MDE = (z_{1-a/2} + z_{1-b}) x SE_clustered(dBrier),      a=.05, b=.20

using the SAME date-clustered standard error the Diebold-Mariano tests use, and
compares it against the equivalence margin delta=1e-3 that the report adopts.

Reading rule, stated once so the report can point at it:
  MDE <= delta   -> the subgroup could have detected a gap the size we care
                    about. "No difference" is informative here.
  MDE >  delta   -> the subgroup could NOT. A null is uninformative and must be
                    reported as underpowered, never as evidence of equivalence.
Also reported: the n each subgroup would need to bring MDE down to delta, which
is the honest answer to "why not just add more leagues".

The interval-based delta_min in league_tost and the MDE here answer different
questions and can disagree: delta_min asks how wide the realized CI is (it
depends on where the point estimate landed), MDE asks how wide it would have to
be to catch a true effect. A subgroup can be "EQUIV at delta_min<1e-3" by luck
of a near-zero point estimate while still being underpowered.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.three_way import SRC, load
from src.analysis.rigor import cluster_dm

DELTA = 1e-3
ALPHA, BETA = 0.05, 0.20
PAIRS = [("Kalshi", "Polymarket"), ("Kalshi", "Sportsbook"), ("Polymarket", "Sportsbook")]
KMDE = stats.norm.ppf(1 - ALPHA / 2) + stats.norm.ppf(1 - BETA)   # ~2.802


def mde(d, a, b):
    """(clustered SE, MDE, n needed for MDE=DELTA) for one subgroup and pair."""
    y = d.home_won.values
    pa, pb = d[SRC[a][0]].values, d[SRC[b][0]].values
    _, se, _, _, _ = cluster_dm(pa, pb, y, d.date.values)
    m = KMDE * se
    # SE scales as 1/sqrt(n) at fixed cluster structure
    n_need = len(d) * (m / DELTA) ** 2 if m > 0 else np.nan
    return se, m, n_need


def table(d, groups, label):
    print(f"\n=== MDE by {label} (Brier differential x1000; "
          f"alpha={ALPHA}, power={1-BETA:.0%}) ===", flush=True)
    print(f"{'group':>10} {'n':>6} {'dates':>6}  " +
          "  ".join(f"{a[:4]+'-'+b[:4]:>14}" for a, b in PAIRS) +
          "   verdict at delta=1e-3", flush=True)
    for name, g in groups:
        if len(g) < 30:
            print(f"{name:>10} {len(g):>6} {'-':>6}   (too few games)", flush=True)
            continue
        cells, worst = [], 0.0
        for a, b in PAIRS:
            se, m, n_need = mde(g, a, b)
            worst = max(worst, m)
            cells.append(f"{m*1000:>14.2f}")
        verdict = ("powered" if worst <= DELTA else
                   "UNDERPOWERED" if worst > 2 * DELTA else "marginal")
        print(f"{name:>10} {len(g):>6} {g.date.nunique():>6}  " +
              "  ".join(cells) + f"   {verdict}", flush=True)


def main():
    d = load()
    d["date"] = d.start_utc.astype(str).str[:10]
    print(f"three-way clean games: {len(d):,} over {d.date.nunique()} dates", flush=True)
    print(f"equivalence margin delta = {DELTA*1000:.1f}e-3 Brier "
          f"(admits a systematic 3.16pt offset; dBrier=eps^2 — see D2)", flush=True)

    table(d, [("ALL", d)], "the pooled sample")
    table(d, sorted(d.groupby("league"), key=lambda t: -len(t[1])), "league")

    print("\n=== how much data would each league need? ===", flush=True)
    print("  (n implied by SE ~ 1/sqrt(n) at the observed cluster structure; a", flush=True)
    print("   multiple below 1.0x means the league is ALREADY powered)", flush=True)
    print(f"{'league':>10} {'n now':>7} {'worst MDE':>10} {'n for MDE=1e-3':>15} "
          f"{'multiple':>9}", flush=True)
    for lg, g in sorted(d.groupby("league"), key=lambda t: -len(t[1])):
        if len(g) < 30:
            continue
        worst_m, worst_need = 0.0, 0.0
        for a, b in PAIRS:
            se, m, n_need = mde(g, a, b)
            if m > worst_m:
                worst_m, worst_need = m, n_need
        flag = "" if worst_m <= DELTA else "   <-- null is uninformative"
        print(f"{lg:>10} {len(g):>7,} {worst_m*1000:>10.2f} {worst_need:>15,.0f} "
              f"{worst_need/len(g):>8.1f}x{flag}", flush=True)

    print("\n=== what the pooled sample CAN rule out ===", flush=True)
    for a, b in PAIRS:
        se, m, _ = mde(d, a, b)
        # translate a Brier gap into the per-game probability error it implies
        pts = np.sqrt(m) * 100
        print(f"  {a} vs {b}: any true gap larger than {m*1000:.2f}e-3 Brier would "
              f"have been detected with {1-BETA:.0%} probability", flush=True)
        print(f"    = a forecaster mispricing every game by {pts:.1f}pt in a fixed "
              f"direction (a constant bias eps raises Brier by eps^2)", flush=True)

    print("\nREPORT RULE: quote MDE alongside every subgroup null. Leagues flagged", flush=True)
    print("UNDERPOWERED above must be described as 'consistent with equivalence but", flush=True)
    print("unable to detect it', never as evidence for it.", flush=True)


if __name__ == "__main__":
    main()
