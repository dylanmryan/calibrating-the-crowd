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
  - LADDER-CONVENTION CORRECTION (2026-08-20). MLB/WNBA spread rungs settle at
    "wins by t-0.5 or more"; NBA/NHL at "wins by more than t". The analysis
    layer applied the NBA rule everywhere, shifting MLB's implied margin CDF by
    a full run. Four claims below were that bug, not the market. Verified
    against Kalshi's own settlement field; guarded now by a data_audit gate and
    by src/analysis/ladder_convention.py.
      * "MLB ladder under-prices 1-2-run margins z=+10.05" -> +8.40pts becomes
        -1.10pts (z=-1.31). RETRACTED.
      * "MLB PIT rejects for Kalshi, KS p<0.001" -> KS 0.0709 becomes 0.0343,
        p=0.104. RETRACTED; every league's margin PIT now passes.
      * "Books beat Kalshi ladders as DISTRIBUTIONS, RPS z=+5.36" -> the MLB
        term was the artifact (+3.96e-3 z=+5.42 becomes +0.33e-3 z=+1.29).
        REVISED, not retracted: a smaller pooled edge survives (+0.49e-3,
        z=+2.44) and it is now carried by NBA (+1.14e-3, z=+2.27), whose
        convention was correct all along.
      * "Totals pass where margins reject" (the walk-off mechanism story) ->
        both layers now pass on the same 1,244 games (totals p=0.84, margins
        p=0.10). The CONTRAST is retracted; the totals result itself stands.
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
  - "WNBA totals PIT rejects, KS=0.108 p=.0076" (retired 2026-08-29, twice
    over): the freeze collection grew the sample 234->290 ladders and the
    rejection DISSOLVED in place (KS 0.062, p=0.207, mean u 0.509); and on
    the registered post-2026-08-12 holdout the tilt FLIPPED SIGN (mean u
    0.404, z=-2.3, n=47; oos_verification.log). A false alarm from the
    smallest league, caught by exactly the machinery built to catch it.
"""
from __future__ import annotations

# (claim, p-value, provenance: results/logs file, 2026-07-30 run)
DISCOVERIES = [
    ("MLB extra-inning 1-2-run cell under-priced, BOTH venues (K z=+5.94)", 1e-8,
     "mlb_extras.log, ladder_vs_books.log [K +20.15pts / books +21.99pts on the "
     "same games -- baseball-wide, NOT Kalshi-specific. Replaces the retracted "
     "Kalshi-only +8.4pt claim; regulation runs the other way at -3.07pts]"),
    ("Extras end within 1 run 70% vs 25% (cell z~8.9)",          1e-10,  "mlb_extras.log"),
    ("Markets beat walk-forward Elo floor (z=+7.3..+7.4)",       1e-10,  "model_benchmark.log"),
    ("Minute-scale bidirectional K<->P predictability (z~7)",    1e-10,  "minute_lead_lag.log"),
    ("Ladder-cost: selling MLB ladder rungs LOSES money (z=-4.6)", 1e-5,
     "ladder_cost.log [unchanged — uses each contract's own settlement — but it "
     "no longer tests a Kalshi-specific bias, since that bias was the artifact]"),
    ("Poly relative volume -41% at fee date (z=-3.6)",           3e-4,   "fee_liquidity.log"),

    ("Books beat Kalshi ladders as DISTRIBUTIONS (RPS z=+2.44)",  1.5e-2,
     "multi_outcome.log [post-convention-fix: MLB z=+1.29 n.s., NBA z=+2.27, "
     "NHL z=+0.05 TIE — the edge is now NBA-carried and much smaller]"),
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
    ("Kalshi margin PIT, all leagues (convention-corrected)", "pooled p=0.718; MLB p=0.104 — the pre-fix MLB rejection was the ladder-convention artifact. The BOOKS' far denser ladders show small deviations of their own (MLB p<.001, NHL p=.024, KS 0.04-0.07) — density/power, not superiority; see book_pit.log"),
    ("Kalshi TOTALS PIT, MLB", "KS=0.015 p=0.90 PASSES (n=1,466 ladders). The margin layer now ALSO passes post convention fix — the totals-pass/margins-reject contrast is retracted; both layers of the run process are priced correctly outside the extras cell"),
    ("Kalshi TOTALS PIT, NBA/NHL controls", "p=0.86 / 0.25 — pass on full samples (n=1,284 / 1,211)"),
    ("Kalshi totals right-tail bias (MLB)", "no threshold off by more than 2.8pt, all |z|<=1.01"),
    ("Totals ladder coherence, live-book only", "99.3-100% monotone every league; raw 86.9-95.6% is trade-reconstruction noise"),
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
