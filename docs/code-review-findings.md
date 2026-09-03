# Full code & methodology review — verified findings (2026-07-30)

Three parallel reviewers over collectors/core-stats/microstructure; every
Tier-1/2 claim re-verified against code and current data before inclusion.
Ordered by impact on published claims.

**The findings below are the record as written on 2026-07-30 and are left
unedited. Current status is the table immediately following, re-verified against
the code on 2026-09-03 — do not read the body as a list of open defects.**

## Status as of 2026-09-03

Every Tier-1 finding is fixed. A second pass on 2026-09-03 closed four more
(15, 23b, 23c, and the re-drift of 1) and formally declared a fifth (17). What
remains open is bounded in size, conservative in direction, or in a collector
that has since been retired — a limitation to state, not a bug to fix.

| # | finding | status | note |
|---|---|---|---|
| 1 | stale FDR inventory | **FIXED** 43bfb88, hardened 2026-09-03 | regenerated from live logs; clustered-p policy adopted; NBA sub-claim retracted. It then re-drifted, as a hand-maintained list will: `multiple_testing` now re-derives every p from the frozen logs at run time and prints a drift report. That refresh retracted the Murphy sup-t claim (0.037 → 0.129) and strengthened both encompassing claims |
| 2 | minute first-passage sign inverted | **FIXED** bed8579 | labels corrected; symmetric-null conclusion was always intact |
| 3 | tick off-grid float-modulo bug | **FIXED** bed8579 | 14.6% → 0.7%; strengthens the on-grid narrative |
| 4 | book_pit not tie-consistent | **FIXED** 70a5893 | tie-consistent PIT; book MLB pass weakens to p=0.084, contrast stands |
| 5 | layer2 counts pushes as losses | **FIXED** 70a5893 | pushes excluded; the MLB 45.0% run-line claim was **retracted** as a scoring artifact |
| 6 | book leg drops whole franchises | **FIXED** 490fa7f | accent/punctuation-insensitive alias map in `sportsbook_hist._norm_name`; franchises re-collected |
| 7 | 117 duplicate Kalshi→ESPN matches | **FIXED** 490fa7f | 1:1 enforced, ambiguous pairs purged, audit-gated |
| 8 | horizon collector 2-page fill cap | **FIXED** 490fa7f | cap raised 8×; constant sample 2,137 → 2,901 |
| 9 | fee_volumes records failures as 0 | **OPEN (collector retired)** | the Polymarket side now distinguishes `None`; the Kalshi side still sums an empty fill list to 0 and the resume file marks it done. Collector is retired — state as a limitation on the DiD's precision, do not re-collect |
| 10 | polyus endDate-anchored closes | **OPEN (guarded downstream)** | `game_start = gameStartTime or endDate` still in the collector; the look-ahead guard is in the analysis layer (443520e fixed 47 affected games). Retired collector — limitation |
| 11 | trade-recon unbounded look-back | **OPEN, now bounded empirically** | no time floor on the reconstructed side, and `staleness_min` reports the newest fill. `validate_recon` (now in the suite) bounds the damage: 94.9%/96.9% exact bid/ask, median mid error 0.00pt, n=98 |
| 12 | live_snapshot doubleheader ambiguity | **OPEN (collector retired)** | no nearest-start selection; known limitation with a named mechanism |
| 13 | lead_lag shifts on row-dropped frames | **FIXED** bed8579 | masks to NaN on a full calendar grid; shifts negligible as predicted |
| 14 | slope_ci on stacked mirrored sides | **FIXED** 490fa7f | `referee` §2 reports home-side-only slope and ECE alongside the stacked version |
| 15 | nuance per-bin binomtests double-count sides | **FIXED** 2026-09-03 | the binomial now runs on the halved effective sample, since a game contributes two deterministically mirrored sides. No star changes state on the frozen data (there were none), so this is a guard against a future false flag |
| 16 | CORP band resamples mirrored sides independently | **OPEN, conservative direction** | `corp_diagram.band` draws `y* ~ Bern(p)` over the stacked vector, so the null band is too WIDE near 50c — it overstates support for the centre rather than manufacturing a rejection |
| 17 | cluster_dm uses CR0, z not t(G−1) | **DECLARED, quantified** | `rigor.cluster_levels` (2026-09-03) prints the corrected estimator at six clustering levels: the G/(G−1) correction moves the SE <1% at G=386 and ~3% at G=15, and changes no verdict. Left uncorrected in the headline `cluster_dm` deliberately — re-basing every number in a frozen, pre-registered suite for a sub-1% effect trades a real risk of transcription error for no inferential gain. The corrected version is printed alongside so a reader can use either |
| 18 | encompassing cites LR p over clustered p | **FIXED** 43bfb88 | clustered-p policy adopted across the inventory |
| 19 | MLB cell z-stats ignore pairing | **OPEN, conservative direction** | ignoring the positive covariance between paired venue estimates inflates the variance, so the reported z is a lower bound on significance |
| 20 | four_way dup ids / pre-guard print / dead clause | **FIXED** 490fa7f | uniqueness enforced, print reordered, dead clause deleted |
| 21 | gates don't halt the suite | **FIXED** 490fa7f | `make_results` breaks on a gate failure |
| 22 | deep_audit tautological / short-circuiting checks | **FIXED** 490fa7f | both reworked |
| 23a | murphy global p can print 0.000 | **FIXED** 490fa7f | `(1+r)/(B+1)` floor |
| 23b | coherence bracket check is an upper bound | **FIXED** 2026-09-03 | the log now prints the consistency rate as "an UPPER bound" and states why (only the ±1.5 rung is tested against the moneyline) |
| 23c | profitability bootstrap resamples bets iid | **FIXED** 2026-09-03 | now a game-level cluster bootstrap. The review's predicted direction was backwards: a game's two sides are perfectly anti-correlated (exactly one pays), so pairing *removes* variance — the clustered CI on the full sample is [−4.4%, −4.1%] against iid's [−6.0%, −2.6%]. Correct either way, and it sharpens the cost result rather than softening it |
| 23d | wc_freeze would poison scores on a missing outcome | **OPEN, latent** | no game currently lacks an outcome; the case study is frozen and descriptive (D6) |
| 23e | fee_liquidity label errors | **OPEN, labels only** | "Feb" window includes Mar 1; "biweekly" is weekly. Numbers are correct |

---

## The findings as written, 2026-07-30 (unedited)

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
