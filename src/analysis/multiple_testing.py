"""Multiple-testing control across the paper's positive claims.

The project runs many hypothesis tests; a referee will ask which discoveries
survive false-discovery-rate control. Inventory below = every POSITIVE claim
(an effect asserted to exist) with its primary p-value as reported in
docs/findings.md. Nulls/equivalences are not discoveries and are controlled by
their own TOST margins, so they are listed separately for transparency.

Benjamini-Hochberg at q = 0.05 and 0.10.
"""
from __future__ import annotations

# (claim, p-value, source analysis)
DISCOVERIES = [
    ("MLB ladder under-prices 1-2-run margins (z=10)",        1e-10, "mlb_autopsy/ladder_vs_books"),
    ("Extras end within 1 run 70% vs 25% (z=8.9 cell gap)",   1e-10, "mlb_extras"),
    ("MLB PIT rejects for Kalshi (KS)",                       1e-3,  "margin_dist"),
    ("Ladder-cost: selling the bias LOSES money (z=-4.6)",    1e-5,  "ladder_cost"),
    ("Kalshi sharpens 24h->start (DM)",                       3e-4,  "horizon"),
    ("Late flow predicts beyond closing book (LR)",           1e-3,  "late_flow"),
    ("Kalshi encompasses book at close (LR)",                 4e-3,  "encompassing"),
    ("NBA carries the encompassing increment",                6e-3,  "encompassing"),
    ("Kalshi encompasses Polymarket at close (LR)",           1.3e-2, "encompassing"),
    ("Books lead Kalshi at T-24h (clustered DM)",             2.9e-2, "horizon_equivalence"),
    ("Murphy sup-t: Kalshi edge vs Shin-book, low thresholds", 1.2e-2, "murphy (sup-adjusted, favors Kalshi)"),
    ("Markets beat walk-forward Elo floor (DM z=7.4, all 3)",  1e-10, "model_benchmark"),
    ("Minute-scale bidirectional K<->P predictability (z~7)",  1e-10, "minute_lead_lag"),
    # 2026-07-21: replaced "book momentum z=17.5" — retired as a 3-day
    # small-sample artifact (matured panel own-lag z=-0.3). Matured claim:
    ("Cross-venue 15-min predictability K<->P, book->P (z~3)", 1.0e-3, "lead_lag (matured panel)"),
    ("Wide-set Kalshi beats Poly (DM)",                       4.8e-2, "referee (flagged fragile)"),
    ("Log-score Kalshi beats book (DM)",                      5.1e-2, "referee (flagged fragile)"),
]

NULLS = [
    ("Three-way closing DM (all pairs)", "p=0.15/0.26/0.54 + TOST equivalent at ±1e-3"),
    ("Fee natural experiment DiD", "p=0.74 (placebo p=0.39)"),
    ("Taker-size markout gradient", "flat across quintiles"),
    ("Taker imbalance beyond book", "p=0.80/0.48"),
    ("Closing-price efficiency (move beyond close)", "p=0.99/0.35/0.52"),
    ("Behavioral fingerprints (home bias, franchise, weekend)", "all n.s."),
    ("FLB: all slope CIs include 1", "-"),
    ("Book PIT MLB/NBA", "p=0.46/0.17 (pass)"),
    ("T-24h encompassing (K beyond book a day out)", "p=0.68"),
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
        print(f"=== Benjamini-Hochberg, q={q} ({len(DISCOVERIES)} positive claims) ===", flush=True)
        for i, (name, p, src) in enumerate(ranked, start=1):
            mark = "KEEP" if i <= keep else "drop"
            print(f"  [{mark}] p={p:<8.2g} {name}  ({src})", flush=True)
        print(flush=True)
    print("=== nulls / equivalence claims (not FDR-controlled discoveries) ===", flush=True)
    for name, note in NULLS:
        print(f"  - {name}: {note}", flush=True)


if __name__ == "__main__":
    main()
