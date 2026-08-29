# Registered claims — out-of-sample verification protocol
*Committed 2026-08-28, BEFORE the holdout data was pulled. This is the claim
registration the outline promised (open item 2) and the limitations section
references as "informal pre-registration." It fixes the claims, the samples,
the statistics, and the pass criteria; `src/analysis/oos_verification.py`
then evaluates exactly this list, once, and the result is reported whichever
way it comes out.*

## Honesty statement, first

The holdout events (games of 2026-08-12 through 2026-08-28) have already
been played. Registration here is relative to **data access**, not event
time: nothing starting on or after 2026-08-12 has been collected locally,
analyzed, or looked at anywhere in this project. The evidence base was
frozen by circumstance on 2026-08-11 (final master build; totals and spread
collection completed the same day) and the local VPS mirror was last synced
2026-08-10 16:12 ET. The VPS cron has been collecting panel snapshots
autonomously since; that file has not been pulled or read. The claims below
were fixed from the 2026-08-23 suite logs — which contain no post-cutoff
game — before any holdout row existed on this machine.

No new paid data: the sportsbook leg of the holdout comes exclusively from
the already-running VPS live feed (its credit reserve funds it). No
historical Odds API calls are made.

## Samples

| id | definition |
|---|---|
| H-EX | Rebuilt-master rows with official start ≥ 2026-08-12 00:00 UTC, settled by pull time, both exchange closes present, passing the exact `three_way.load()` clean-set quality filters (spread, staleness, source flags) |
| H-3W | VPS panel games with start ≥ cutoff and all three sources quoted in the final pre-start snapshot; outcomes from refreshed ESPN finals |
| H-LAD | Kalshi MLB spread-ladder sides for games with start ≥ cutoff (fresh collection), scored under `ladder_convention.cover_line()` |
| H-TOT | Kalshi WNBA totals ladders for games with start ≥ cutoff (fresh collection) |

Expected scale: roughly 250–400 games in H-EX/H-3W (17 days of MLB + WNBA +
CFB week 0/1), ~30–60 extras-relevant sides in H-LAD, ~50–90 ladders in
H-TOT. **Every null below is therefore quoted with its MDE, per the house
reading rule; the deliverable is directional consistency, not re-derivation
of the formal equivalence at full power.** H-EX/H-3W date clusters number
only ~17; cluster-robust inference at that count is itself noisy and is
flagged wherever quoted.

## Registered claims

| id | claim (from the frozen record) | statistic on holdout | registered prediction | consistency criterion |
|---|---|---|---|---|
| R1 | Three-way dead heat | pairwise ΔBrier, date-clustered DM, on H-3W (exchange closes per master convention; book at final panel snapshot) | all three pairwise gaps small and n.s. | every \|ΔBrier\| point estimate < δ=1.0e-3; no pair rejects at α=.05; MDE quoted |
| R2 | Exchange dead heat | Kalshi-vs-Polymarket ΔBrier on H-EX | gap small and n.s. | \|ΔBrier\| < 1.0e-3; DM n.s.; MDE quoted |
| R3 | Calibration | logistic slope + ECE per venue (exchanges on H-EX; book on H-3W) | slopes ≈ 1, ECE at noise floor | every slope 95% CI includes 1; ECE within 2× the binomial noise floor for that n |
| R4 | No favorite–longshot bias | mean realized-minus-priced in price buckets <30c and >70c, stacked sides (H-EX) | no systematic longshot overpricing | neither tail bucket shows a deficit \|z\| ≥ 2 in the FLB direction |
| R5 | Synchronized-clock robustness | R1 re-scored with ALL THREE legs from the same final snapshot (H-3W) | dead heat unchanged when the 60-min consensus-timing caveat is removed | same criterion as R1; gap between mixed-clock and same-clock ΔBriers < 0.5e-3 |
| R6 | Shared extras blind spot (direction) | extras vs regulation win-by-1–2 cell gap on H-LAD | extras gap positive (frozen estimate ≈ +20pt); aggregate cell small | extras-cell gap > 0; aggregate \|gap\| < extras gap; CI quoted (will be wide) |
| R7 | WNBA totals tilt (the open observation's real-time test) | PIT mean u on H-TOT | u > 0.5 (frozen estimate 0.536: market slow to re-price a rising scoring environment) | report u with CI; either outcome upgrades the open observation (confirmed direction, or noise) |
| R8 | Structural taker cost | half-spread + taker fee over notional on fresh Kalshi panel quotes | ≈ −4.5% per position | within ±1.0pt of −4.5% |

## Registered as NOT testable in this holdout, and why

- Books-vs-Kalshi ladder RPS and the books' extras cell: no book
  alternate-spread data post-2026-08-11 (Odds API budget spent; the live
  feed carries moneylines only).
- Encompassing / late-flow / maker-driven discovery: requires re-collecting
  the per-fill trade panel; out of scope for the freeze window.
- Outright returns: no outright fields resolve inside a 17-day August
  window.
- Fee incidence, tick design, immediacy inversion: structural results
  already measured on their own full samples; the freeze rider refresh
  (five_min, immediacy, lead_lag on the extended panel) updates them but is
  not a registered holdout test because the panel windows overlap the
  development sample.

## Evaluation protocol

1. Pull the holdout (VPS rsync; free Kalshi/ESPN/Polymarket refresh chain;
   spreads + totals incremental collection), rebuild the master, re-run the
   audit gates.
2. Run `oos_verification.py` once. It prints the R1–R8 scorecard with every
   statistic, criterion, and MDE, and writes `results/oos_scorecard.png`.
3. The scorecard enters the report as §5A's closing paragraph (per
   drafting-plan open item 3) and one abstract sentence, whichever way it
   reads. A deviation is a finding, not a problem to fix: it gets reported
   with the same prominence as a confirmation.
4. No statistic in this file may be changed after the pull. Any additional
   exploratory cut run on holdout data must be labeled exploratory in the
   log and cannot join this scorecard.
