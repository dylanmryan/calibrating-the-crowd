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

---

## Post-pull annotation (2026-08-29 — nothing above this line was edited)

The pull revealed one sample failure the registration did not anticipate:
the VPS live feed's **sportsbook leg stopped on 2026-08-07 15:35 UTC** (the
Odds API live-feed credit reserve exhausted; the exchange legs ran to
2026-08-28 unaffected). H-3W therefore contains zero synchronized book
quotes, and **R1 and R5 are reported as NOT EVALUABLE** — not re-scoped.
A paid historical top-up (~313 post-cutoff games ≈ 3–3.5K credits, IF the
plan still has them — the local key now returns 401) could still build the
three-way holdout; per the protocol and the standing budget rule that is a
decision for Dylan, not something this run performs. A labeled EXPLORATORY
same-clock K-vs-P comparison (n=252, ΔBrier +2.2e-3, p=0.45) appears in the
log and is not on the scorecard.

Scorecard as evaluated (oos_verification.log, 2026-08-29):

| id | verdict | result |
|---|---|---|
| R1 | NOT EVALUABLE | no post-cutoff synchronized book quotes exist |
| R2 | **CONSISTENT** | \|ΔBrier\| 0.04e-3, p=0.879, **MDE 0.81e-3 — powered at the pre-stated δ** (n=264) |
| R3 | **CONSISTENT** | slopes 1.41/1.43 with CIs covering 1; ECE 0.021–0.022 vs noise floor 0.042 |
| R4 | UNDERPOWERED | 26 sides per tail bucket — too thin to read |
| R5 | NOT EVALUABLE | same sample failure as R1 |
| R6 | **CONSISTENT** | extras cell +19.6pt (90% CI ±14.3, n=34) vs frozen +20.2pt; aggregate +0.1pt |
| R7 | **DEVIATES** | mean u 0.404 (z=−2.3, n=47) — the tilt **flipped sign** vs the frozen 0.536; the open observation does not replicate and is treated as sampling noise, which is precisely what this test existed to determine |
| R8 | **CONSISTENT** | −4.6% per position (n=44,525 fresh quotes) vs frozen −4.5% |

## Second annotation (2026-09-03) — a description error in the sample table

Nothing above the post-pull line has been edited, including this correction's
subject. The H-EX row describes the sample as "passing the exact
`three_way.load()` clean-set quality filters (spread, staleness, source
flags)." **Those filters do not exist.** `three_way.load()` filters on exactly
two things — a resolved outcome and no cross-source settlement disagreement —
and requires the prices to be present; it has never conditioned on spread,
staleness, or source.

The analysis is unaffected: `oos_verification.load_hex()` mirrors what
`load()` actually does, so the holdout sample was built the way the frozen
sample was, which is what the registration was for. Only the *description* was
wrong, and it is corrected here rather than above because a pre-registration
document that gets edited after the pull is not a pre-registration document.

The substantive question underneath it — whether those unused flags hide
anything — is now answered rather than assumed: `robustness_cuts.py` §0 prints
their distributions on the headline sample (Kalshi quote age median 0.1 min,
Polymarket 0.9 min, 11 books in the consensus for 99.6% of games), and §1-§4
re-run the equivalence under the cuts a filter would have imposed.

## Third annotation (2026-09-23) — R6 was a vacuous test, and is withdrawn

Nothing above the post-pull line has been edited, R6 included. R6 registered
the extras blind spot's *direction* ("extras gap positive, frozen estimate
≈ +20pt") and the holdout scored it **CONSISTENT** (+19.6pt, 90% CI ±14.3,
n=34). That verdict should be read as **no evidence at all**, and the reason is
a flaw in the registration rather than in the holdout.

`extras` is realized DURING the game. Conditioning a calibration test on an
outcome-correlated state outside the forecaster's information set breaks the
calibration identity mechanically, so the split returns the extras/margin
dependence whichever forecaster you feed it. `src/analysis/extras_conditioning.py`
demonstrates this directly: a **constant at the unconditional base rate**
scores +21.19pt on the same split, and a pre-game-information-only forecast
+21.23pt, against the market's +20.22pt. A constant cannot misprice the
ghost-runner rule.

So R6 predicted a positive gap that a constant would also have produced. It was
guaranteed to confirm before any data was pulled, which makes it the one thing a
pre-registration is supposed to exclude: a test that cannot fail. Its
confirmation adds nothing, and is withdrawn as evidence for the blind-spot
claim. The claim itself is retracted in `multiple_testing.py`'s retired-claims
record.

This is a lesson about the registration, not the holdout. R1–R5 and R7–R8 were
all falsifiable — R7 in fact **deviated** and was reported as a deviation. The
gap in the procedure was that R6's *statistic* was never checked against a
placebo before being registered, only its direction and magnitude. Any future
registration of a conditional-calibration claim should state the information set
the conditioning variable belongs to, and should be run against a constant
forecaster first.

The replacement test — E[realized − implied | Z] = 0 for Z inside the market's
information set, Z = a cross-fitted ex-ante extras propensity — is **not**
registered and is not scored here. It is a post-hoc finding from auditing R6,
flagged as such in the FDR inventory, and it runs the *opposite* way (coef
−1.1495, z=−3.00 date-clustered: a small over-pricing of the cell in
extras-prone games). It is reported at that strength and no higher.
