"""Multiple-testing control across the paper's positive claims.

The project runs many hypothesis tests; a referee will ask which discoveries
survive false-discovery-rate control. Inventory below = every POSITIVE claim
(an effect asserted to exist) with its p-value AS OF THE 2026-07-30 suite run
(the code-review found the previous inventory carried stale Jul-10 values —
several claims weakened as the sample grew and was cleaned). Policy adopted
with the refresh: cite the DATE-CLUSTERED p wherever a clustered and an LR/MLE
version both exist (the conservative choice), and every entry names the
results/logs file that generates it, so drift is checkable by grep.

Nulls/equivalences are not discoveries and are controlled by their own TOST
margins; listed separately. Benjamini-Hochberg at q = 0.05 and 0.10.

RETIRED CLAIMS (kept here as the honest record):
  - "Book consensus momentum z=17.5" (2026-07-21): 3-day small-sample
    artifact; matured panel own-lag z=-0.3.
  - "NBA carries the encompassing increment" (2026-07-30): p=0.006 on Jul-10
    data, p=0.145 on the current master — RETRACTED.
  - "Wide-set Kalshi beats Poly" and "log-score Kalshi beats book"
    (2026-07-30): the two long-flagged fragiles dissolved to p=0.142 / 0.326
    as the sample grew — no longer claims at any threshold.
  - "Kalshi sharpens 24h->start p=3e-4" (2026-07-30): no module in the
    current suite computes this statistic (descriptive table only); removed
    pending a proper constant-sample DM if wanted.
"""
from __future__ import annotations

# (claim, p-value, provenance: results/logs file, 2026-07-30 run)
DISCOVERIES = [
    ("MLB ladder under-prices 1-2-run margins (z=+10.05)",       1e-10,  "ladder_vs_books.log"),
    ("Extras end within 1 run 70% vs 25% (cell z~8.9)",          1e-10,  "mlb_extras.log"),
    ("Markets beat walk-forward Elo floor (z=+7.3..+7.4)",       1e-10,  "model_benchmark.log"),
    ("Minute-scale bidirectional K<->P predictability (z~7)",    1e-10,  "minute_lead_lag.log"),
    ("Ladder-cost: selling the bias LOSES money (z=-4.6)",       1e-5,   "ladder_cost.log"),
    ("Poly relative volume -41% at fee date (z=-3.6)",           3e-4,   "fee_liquidity.log"),
    ("MLB PIT rejects for Kalshi (KS p<0.001)",                  1e-3,   "margin_dist.log"),
    ("Books beat Kalshi ladders as DISTRIBUTIONS (RPS z=+5.36)",  1e-7,   "multi_outcome.log (MLB z=+5.4, NBA z=+2.3, NHL z=+0.05 TIE — edge is MLB-concentrated)"),
    ("Sports FUTURES longshots overpriced ($0.33/$1, pooled)",    6e-3,   "futures_calibration.log [modest n]"),
    ("BOOKS' outright longshots overpriced ($0.34/$1, 0-3mo)",    1e-5,   "book_outrights.log [cluster-t, 20 sport-seasons 2020-26 playoff-densified, se 0.08; = Kalshi's $0.33]"),
    ("Cross-venue 15-min predictability, P->K only (z=+4.4)",     1e-5,  "lead_lag.log [REVISED 2026-08-10 on the 528-game panel: the book->P term this claim used to include is now z=-0.1 and is retired; only the exchange-to-exchange term survives]"),
    ("Book consensus predicts exchanges' next 5-min move (P z=+4.5)", 1e-5, "five_min.log [effect is ZERO in the final 2h (z=+0.1/-0.1), lives in sub-0.5pt book moves, and for Poly is as strong from a 30-min-frozen quote — read as drift alignment away from game time, NOT news transmission]"),
    ("Late flow predicts beyond closing book (clustered z=3.43)", 1e-3,  "late_flow.log"),
    ("Books lead Kalshi at T-24h (clustered DM, z=+1.86)",       6.3e-2, "horizon_equivalence.log [softened on completed 84%-coverage T-24h sample; was z=+2.32 p=0.020]"),
    ("Murphy sup-t: Kalshi edge vs Shin-book, low thresholds",   3.7e-2, "murphy.log (sup-adjusted)"),
    ("Kalshi encompasses Polymarket at close (clustered z)",     4.4e-2, "encompassing.log [FRAGILE]"),
    ("Kalshi encompasses book at close (clustered z)",           5.4e-2, "encompassing.log [FRAGILE]"),
]

NULLS = [
    ("Three-way closing DM (all pairs)", "n.s. + TOST equivalent at ±1e-3"),
    ("Four-way: Poly-US vs each source", "n.s. + TOST equivalent at ±1e-3"),
    ("Fee natural experiment DiD on accuracy", "p=0.74 (placebo p=0.39)"),
    ("Taker-size markout gradient", "flat across quintiles"),
    ("Taker imbalance beyond book", "p=0.80/0.48"),
    ("Closing-price efficiency (move beyond close)", "p=0.99/0.35/0.52"),
    ("Behavioral fingerprints (home bias, franchise, weekend)", "all n.s."),
    ("FLB: all slope CIs include 1 (home-side)", "-"),
    ("Layer-2 main-line calibration (push-corrected)", "MLB 50.4% vs 49.9%; NBA n.s. — 45.0% claim retracted"),
    ("Book PIT MLB/NBA (tie-consistent)", "p=0.084/0.165 (marginal pass vs Kalshi p<0.001)"),
    ("Kalshi TOTALS PIT, MLB", "KS=0.017 p=0.84 PASSES on the same 1,244 games where the MARGIN PIT rejects (p=2.9e-6) — and with more rungs, so better powered; isolates the defect to the margin, not the run process"),
    ("Kalshi totals right-tail bias (MLB)", "no threshold off by more than 2.8pt, all |z|<=1.01"),
    ("T-24h encompassing (K beyond book a day out)", "p=0.68"),
    ("Minute-scale first-passage leads", "median 0.0, sign-test p=1.0"),
    ("Resolution ladder 30->5 min: any venue leads", "no cross-lag corr sharpens as the clock sharpens; nothing predicts the book at any grid"),
    ("Book->exchange lead in the final 2h (5-min clock)", "K +0.006 (z=+0.1), P -0.008 (z=-0.1)"),
    ("Niche-sport games (no benchmark): excess ECE", "0.00pt vs noise floor; slope CI 0.84-1.15"),
    ("Exchanges vs PINNACLE at close (n=5,294)", "all n.s.; 90% CIs within ±0.34e-3 (TOST-equiv)"),
    ("Levitt shading vs sharp line (24 EU books)", "sub-1pt deviations, both signs"),
    ("Levitt shading, US retail (DK/FD/MGM +8, n=2.6K)", "-0.22..-0.01pt on home favs: none"),
    ("Book-by-book Brier vs Kalshi (11 US books)", "all n.s.; dead heat holds per book"),
    ("Poly outrights alone (22 fields)", "direction matches Kalshi, underpowered"),
]


def bh(items, q):
    m = len(items)
    ranked = sorted(items, key=lambda t: t[1])
    keep = 0
    for i, (_, p, _) in enumerate(ranked, start=1):
        if p <= i / m * q:
            keep = i
    return ranked, keep


def main():
    for q in (0.05, 0.10):
        ranked, keep = bh(DISCOVERIES, q)
        print(f"=== Benjamini-Hochberg, q={q} ({len(DISCOVERIES)} positive claims, "
              f"values as of the 2026-08-10 refresh, clustered p where "
              f"available) ===", flush=True)
        for i, (name, p, src) in enumerate(ranked, start=1):
            mark = "KEEP" if i <= keep else "drop"
            print(f"  [{mark}] p={p:<8.2g} {name}  ({src})", flush=True)
        print(flush=True)
    print("=== nulls / equivalence claims (not FDR-controlled discoveries) ===", flush=True)
    for name, note in NULLS:
        print(f"  - {name}: {note}", flush=True)
    print("\n(retired claims documented in the module docstring)", flush=True)


if __name__ == "__main__":
    main()
