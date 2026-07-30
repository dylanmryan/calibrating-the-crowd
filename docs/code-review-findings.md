# Full code & methodology review — verified findings (2026-07-30)

Three parallel reviewers over collectors/core-stats/microstructure; every
Tier-1/2 claim re-verified against code and current data before inclusion.
Ordered by impact on published claims. Status: OPEN unless noted.

## Tier 1 — changes published claims (fix before the report)

1. **FDR inventory is stale; the encompassing family weakened as data grew.**
   `multiple_testing.py` hard-codes p-values from the Jul-10 era. Current
   regenerated logs: Kalshi-beyond-book LR p=0.048 (clustered 0.054) vs
   hard-coded 0.004; Kalshi-beyond-Poly 0.040 vs 0.013; NBA-concentration
   p=0.145 vs 0.006 (**dead — retract**); Murphy sup-t 0.037 vs 0.012;
   wide-set K>P 0.142 vs 0.048; log-score 0.326 vs 0.051. One inventory
   claim ("sharpens 24h→start p=3e-4") has **no generating code** in the
   current suite. Fix: regenerate the inventory from live logs (make
   multiple_testing read the logs or recompute), downgrade the whisper to
   fragile in findings, retract the NBA sub-claim, re-run BH.
2. **minute_lead_lag first-passage sign inverted.** `halves` stores
   minutes-to-start (decreasing in time), so `p − k > 0` means POLY crossed
   first; the stat, print, and histogram label all say Kalshi. Verified
   synthetically. Current conclusion (symmetric null, median 0.0) survives;
   every directional label is backwards. Fix sign + labels.
3. **tick_pricing off-grid share wrong: 14.6% → 0.69%.** Float-modulo bug
   (`x*100 % 1` fires on 0.29). findings.md cites 14.6%. Fix formula
   (`abs(x*100−round(x*100))>1e-6`), correct findings (also *strengthens*
   the "moneylines are on-grid" narrative).
4. **book_pit vs margin_dist not apples-to-apples.** Strict inequalities in
   the PIT give tied outcomes (margin == integer book line; impossible on
   Kalshi's half-integer rungs) overlapping intervals → biased toward
   uniformity → toward "books pass". The books-pass/Kalshi-fails contrast
   needs a tie-consistent PIT before it's citable.
5. **layer2 counts pushes as losses.** 34% of book alt-spread points are
   integers; `cover=(margin>-point)` scores pushes as no-cover while the
   de-vigged prob is push-conditional. The −1.5 run-line headline is
   half-integer (push-free, safe); the calibration table isn't. Fix: drop
   pushes or use push-conditional outcomes.

## Tier 2 — real coverage/selection issues (referee-relevant)

6. **Book leg silently drops whole franchises.** Substring team matching
   misses "LA Clippers" (0/83 joint games priced), "Montréal Canadiens"
   (0/100, accent), "St. Louis Blues" (0/84, period), plus CFB names —
   ~290 joint games of *team-correlated* missingness in the three-way
   sample; also hits T-24h and alt-spread legs. Fix: normalized alias map;
   re-collect those teams' book lines if credits allow (~300 games).
7. **117 duplicate Kalshi→ESPN matches** (DH/CBB); 84 Kalshi-priced dup
   games sit in the clean master (7 in the three-way set) possibly carrying
   the sibling game's prices; 3,090 dup rows in trades. Fix: enforce 1:1 in
   the matcher (drop both on ambiguity), audit-gate it.
8. **Horizon collector caps at 2 pages of fills** → 15% of games (the most
   liquid!) missing T-24h prices — a concrete liquidity-composition
   mechanism inside the sharpening analyses' constant-sample caveat.
   Fix: raise page cap on next harvest; note in findings meanwhile.
9. **fee_volumes records fetch failures as volume 0** (false zeros poison
   the DiD); resume marks them done. Fix: distinguish None/0, re-fetch.
10. **polyus collector still emits endDate-anchored closes** (analysis
    guards downstream — collector should anchor to ESPN start or emit the
    flag itself); done-file written after append (crash → dup rows; add
    dedupe on read); multi-row-per-slug semantics documented but implicit.
11. **Trade-recon unbounded look-back**: one side of a reconstructed book
    can be days stale while staleness reports the newest fill; add a time
    floor or a max-side-age flag on next harvest.
12. **live_snapshot doubleheader first-match ambiguity** (known limitation;
    now with mechanism); nearest-start selection would fix.
13. **lead_lag 15-min shifts run on row-dropped frames** (~4% of steps span
    gaps); minute version's glitch filter also row-drops (0.6%). Fix: mask
    to NaN instead of dropping rows; re-run (expect negligible shifts).

## Tier 3 — statistical hygiene (mostly conservative or tiny)

14. `slope_ci` on stacked mirrored sides → SEs ~√2 narrow (no-FLB
    conclusion safe — wider CI still contains 1 — but report home-side CIs).
15. `nuance.py` per-bin binomtests double-count sides (anti-conservative
    stars near 0.5).
16. CORP consistency band resamples mirrored sides independently → band too
    wide near 0.5 (overstates center support modestly).
17. `cluster_dm`: CR0, no G/(G−1), z not t(G−1) — ~1-2% CI effect at
    per-league G≈83; negligible pooled.
18. Encompassing family cites LR p over (larger) clustered p — the
    anti-conservative choice exactly where those claims now sit (0.048 vs
    0.054). Cite clustered.
19. MLB cell z-stats (z≈9-10) ignore pairing/covariance — direction
    conservative, conclusions hold.
20. four_way: 2 dup game_ids survive into the joint set (double-weighted);
    side-validation print runs pre-guard (inflated by mechanical closes);
    dead `and False` fallback clause. Enforce uniqueness, reorder, delete.
21. make_results "gates" don't halt the suite — later modules still run on
    bad data; only the exit code fails. Stop after gate failure.
22. deep_audit: corr check's trailing unconditional PASS + break skips
    remaining leagues; four-way anchor check is tautological (re-applies
    the filter it asserts). Rework both.
23. Minor: murphy global p can print 0.000 (use (r+1)/(B+1)); coherence
    bracket check is an upper bound + dead loop + bare except; profitability
    bootstrap resamples sides iid; wc_freeze would poison scores if a game
    lacked an outcome (none currently do); fee_liquidity "Feb" includes
    Mar 1 and "biweekly" is weekly (labels only).

## Verified clean (checked explicitly, no error found)

DM sign conventions and TOST CI-inclusion logic everywhere; Rademacher
sup-t bootstrap; Shin bisection; Elo walk-forward (no look-ahead, correct
update order, tz-safe chronological sort); all de-vig math; Kalshi
candle/trade and Poly prices-history look-ahead exclusion; polyus tape
UTC consistency and cross-file window summing; hierarchical model
(non-centered, R-hat, HDI, index alignment); why_sports return/fee/maker
algebra and cluster_mean_se; ladder_cost economics; fee DiD spec and its
3e-4 entry; three_way.load() outcome-blind filters; minute panel ordering,
ffill, and lag conventions (other than the sign in #2).

## Impact assessment

Untouched by every finding: the four-way dead heat, TOST equivalences,
per-league/hierarchical calibration, model-benchmark gap, BDW replication,
fee volume incidence, lead-lag symmetric-null, law of one price, tick
pinning (the 97%/96% at-tick numbers are unaffected; only the off-grid
share changes). Casualties: the encompassing "whisper" downgrades to
fragile/borderline; its NBA sub-claim retracts; the book-PIT contrast and
layer2 calibration table need reruns before citation; ~290 games of book
coverage and 84 dup-match games need repair for the final numbers.
