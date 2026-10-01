# Methodology decisions
*Settled 2026-08-20. These close the seven questions raised at the
2026-07-21 advisor checkpoint and the four listed as pending in
`findings.md`. Decided in-house; each records the reasoning so a reader can
disagree with the choice rather than guess at it. This file is the source for
report §4.*

---

## D1. Multiple-testing policy — two families, kept separate

**Decision.** Benjamini–Hochberg at q=0.05 over the inventory of *positive*
claims only (the `DISCOVERIES` list in `src/analysis/multiple_testing.py`).
Equivalence and null results are not entered into that family; they are
disciplined by a pre-stated TOST margin (D2) and by the MDE table. Report
q=0.05 as headline, q=0.10 alongside.

**Reasoning.** FDR controls the expected share of false rejections among
rejected nulls. An equivalence claim rejects a null of *non*-equivalence — a
different null, in the opposite direction, with the error of concern being a
false claim of sameness. Pooling the two families would apply a correction
designed for one error rate to a claim exposed to the other, and would make
equivalence claims *harder* to assert as the count of unrelated discoveries
grows, which is incoherent. The right discipline for the equivalence family is
power, and that is what the MDE table supplies.

**What makes this honest rather than convenient:** the discovery family is
fixed by an inventory that also carries its retired claims. Four results have
been retracted in place as the sample grew (`multiple_testing.py` header). A
family that only ever gains members is a family being gamed; this one has lost
four.

**Reading rule for the report.** Every null gets its MDE quoted in the same
sentence. Every discovery gets its BH status quoted at first mention.

---

## D2. Equivalence margin — pre-stated δ=1.0e-3, reported against a cost-anchored ladder

**This decision changes what the paper says. Read the correction first.**

### Correction to an existing scale statement

`rigor.py:63` and the report outline both gloss δ=1.0e-3 Brier as
"≈ 0.5 percentage points per game." **That is wrong by a factor of six.**

For a forecast displaced from the truth by ε, the Brier excess is exactly ε².
Verified numerically on 2M simulated games:

| systematic offset ε | induced ΔBrier |
|---|---|
| 0.50 pt | 0.024e-3 |
| 1.00 pt | 0.099e-3 |
| 2.10 pt | 0.438e-3 |
| 3.16 pt | 0.993e-3 |

Inverted: **δ=1.0e-3 tolerates a systematic 3.16pt error, not 0.5pt.** The
observed CI half-widths correspond to 2.30pt (pooled, ±0.53e-3) and 1.84pt
(vs Pinnacle, ±0.34e-3). The "0.5%" in the original note was 0.5% *of the
0.2185 Brier level*, which is a relative statement about the score and not a
statement about probabilities. Both places must be corrected before drafting.

### The decision

**Primary margin stays δ = 1.0e-3.** It was pre-stated in July, before the
comparisons that now rest on it, and moving a margin after seeing results is
the exact failure the pre-registration section warns about. It does not move.

**But it is now reported against an economic anchor, not asserted.** The
economically meaningful threshold is the edge a participant cannot monetize.
At an all-in retail taker cost of 4.2% of notional, breakeven edge is
`cost × price`, so the margin is price-dependent:

| contract price | breakeven edge | equivalent δ |
|---|---|---|
| 0.25 | 1.05 pt | 0.11e-3 |
| 0.50 | 2.10 pt | 0.44e-3 |
| 0.75 | 3.15 pt | 0.99e-3 |

The pre-stated δ=1.0e-3 turns out to be the unmonetizable-edge margin
evaluated at favorite prices. That coincidence is worth stating plainly as a
coincidence — it justifies the margin retrospectively, it did not choose it.

**Report the ladder, including where it fails.** Against δ=0.44e-3 (the
mid-price anchor, the strictest defensible reading):

- vs Pinnacle, ±0.34e-3 → **equivalent**
- pooled three-way, ±0.53e-3 → **not equivalent at the mid-price anchor**

This is a better result than a single pass, and the paper should say so
directly: *the venues are indistinguishable within the band where a difference
could reach anyone, and against the sharpest single book they are
indistinguishable within a band a third narrower still.* At a margin tight
enough to matter only to a zero-cost participant who does not exist, the
pooled comparison stops resolving — and that is a statement about the
measurement's power, not about the venues.

**Implementation.** `rigor.py` prints the 90% CIs already; add the ε-scale
column and the three anchor rows. Small change, and it must land before any §5A
prose is written.

---

## D3. PIT for discrete predictive distributions — randomized primary, nonrandomized alongside

**Decision.** Interval-randomized PIT remains primary. Add the nonrandomized
(mean) PIT of Czado, Gneiting & Held as a robustness panel in the appendix.
Lean the headline distributional argument on the totals layer, not the margin
layer.

**Reasoning.** Randomized PIT is the standard construction for discrete
predictive distributions and is uniform under correct specification, which is
what the test needs. Its weakness is real and specific: with 3–5 ladder rungs
the randomization supplies a large share of the variation, so a reader is
entitled to ask how much of a pass is the model and how much is the noise.
That objection is answered structurally rather than by argument — the totals
layer runs 11 rungs on the same 1,244 games, so the *passing* test is the one
least dependent on randomization while the *rejecting* test is the sparse one.
A rejection that survives on sparse rungs and a pass that holds on dense rungs
point the same way, and neither can be an artifact of the same mechanism.

---

## D4. Clustering — date only, with the reason for refusing two-way stated

**Decision.** All DM tests and predictive regressions cluster by date. No
two-way date × league. League enters as a subgroup split (`league_tost`), not
as a clustering dimension.

**Reasoning.** Date is the dominant shared shock: same-day games share news
cycles, weather systems, national broadcast slates, and the same population of
attention. That is the dependence the standard errors need to absorb.

Two-way clustering is declined for a concrete reason, not a stylistic one:
**there are seven leagues.** Cluster-robust variance estimation is consistent
in the number of clusters, and seven is far below any usable threshold —
conventional guidance wants 30–50, and at seven the estimated variance is
itself so noisy that the "robustness" check would be less reliable than the
result it is checking. Reporting it would import false precision. The paper
says this in one sentence rather than omitting the check silently.

Heterogeneity across leagues is a real question and is addressed the right way:
by estimating within each league and reporting the MDE, which is already done.

**Demonstration added 2026-09-03.** The above is an argument for date and
against two-way; it did not show that the answer is insensitive to the level,
which is the question a referee actually asks. `rigor.cluster_levels` now
re-estimates all three headline differentials at six levels — iid, league ×
date, date, week, month, and home team — with the G/(G−1) finite-sample
correction and a t(G−1) reference. No level crosses α=.05 on any pair, and the
widest 90% bound anywhere is ~0.52e-3, roughly half δ. Team clustering gives
*smaller* SEs than date, so there is no per-team shock the headline spec is
missing. This also settles review item 17 (CR0, z rather than t): the
correction moves the SE by under 1% at G=386 and about 3% at G=15, and changes
no verdict.

---

## D5. Lead–lag formality — predictive regressions and event study, not Hasbrouck

**Decision.** Keep game-clustered predictive regressions plus the ≥2pt event
study and the 5/10/15/30-minute resolution ladder. Do not compute Hasbrouck
information shares or a VECM.

**Reasoning.** Information shares require synchronous, continuously traded,
cointegrated prices for the *same* instrument on a common clock, sharing one
efficient price. Four of those conditions fail here. The book series is a
*consensus average across books*, which is not a tradeable price and has no
well-defined innovation. Trading windows are irregular and league-specific.
Tick regimes differ by three orders of magnitude (1c vs 0.001), so the
microstructure noise the decomposition attributes to venues is partly a
design constant. And under asynchronous updating, Hasbrouck bounds are known
to widen until they contain nearly everything — the method would run, print
numbers, and mean little.

The design actually used is stronger for the question asked. A null that
holds identically at four clock resolutions on the same games is harder to
explain away than a point estimate from a model whose assumptions the data
violates. The one surviving coefficient is reported with its three cuts
(zero in the final two hours; confined to sub-0.5pt book moves; as strong from
a frozen quote) rather than promoted.

---

## D6. Ordered multi-outcome scoring — RPS primary, multiclass Brier alongside

**Decision.** For ordered outcomes (margins, ladders), the ranked probability
score is primary and multiclass Brier is reported alongside; this is already
the practice in `multi_outcome.py` and is now the stated convention. For the
unordered 3-way (home/draw/away) the two coincide in interpretation and both
are reported. The World Cup case study (n=9) is **descriptive only** — no
test, no p-value, no inferential language — and moves to an appendix.

**Reasoning.** RPS penalizes distance in the outcome ordering, which is the
whole content of a margin claim: being wrong by five runs should cost more
than being wrong by one, and Brier is indifferent between them. Where the
paper's distributional finding lives — the MLB small-margin cell — the
ordering *is* the finding, so the scoring rule has to see it. At n=9 no
scoring rule rescues inference, and presenting one invites the reader to
treat nine matches as evidence.

---

## D7. Framing — unchanged

**Decision.** Keep the locked framing: gambling venue vs forecasting
institution, never trading exploitability. Exploitability appears only as an
institutional diagnostic — biases sheltered inside a cost band, as books
shelter theirs inside vig.

**Reasoning.** It survived every result, including the ones that did not go
the way the framing anticipated, and it is the only framing under which the
MLB anomaly and the outright failure are the same finding rather than two
embarrassments.

---

## D8. Scope cuts (not in the original checkpoint; decided now)

Two sections are reduced because they carry risk the research question does
not require.

**Affiliated dealer (§5.7) → one paragraph plus an appendix.** The material is
sound but it reads an active CFTC proceeding and live class actions, and its
central test is an underpowered null (−5.0%/−7.7% vs −7.1%/−10.0%, n.s.)
being read as a statement about conduct. Keep the finding, state it as what it
is — the house's absence mostly means no market, and takers do no better
without it — and stop. Do not adjudicate the litigation.

**Demand-side surveys (§2.1) → two sentences of motivation.** Betterment is
self-reported and commercially interested, and the project has no demographic
data connecting it to its own sample; the limitations section already concedes
this. The horizon-translation result does not need the survey: −4.5% per
position, 30% of bankroll after a season of weekly re-staking, and 12.4 game
bets equalling one badly-priced futures ticket are self-contained. Keep the
surveys as the reason anyone should care, not as a premise anything rests on.

---

## D9. Sportsbook consensus — equal-weight mean of vigged probabilities, de-vigged once
*Added 2026-09-03. This was a decision made in code in July and never written
down; it is recorded here because the consensus is the paper's benchmark and an
undocumented benchmark is not a benchmark.*

**Decision.** `sportsbook_hist._consensus` averages each book's raw implied
probability across the US book panel, then normalizes the resulting pair to sum
to 1. Equal weights, no book excluded, no trimming. Pinnacle and Betfair are
NOT in this consensus — they enter separately as sharp benchmarks
(`sportsbook_sharp`), so "the books" in the headline means the US retail
complex, and the sharp comparison is a distinct test.

**Reasoning.** Averaging before de-vigging keeps one de-vig operation on one
well-conditioned pair, rather than compounding a per-book normalization across
a panel whose books quote at different overrounds. Equal weighting is the
neutral choice absent a defensible weighting variable: stake data is not
public, and weighting by a book's own overround would build a sharpness
judgement into the benchmark the paper is testing against.

**Why this is now a reported robustness rather than an assertion.** Three
alternatives — de-vig each book then average, de-vig then take the median, and
line-shop the best price on each side — are run in `robustness_cuts.py` §3.
All four give a book Brier of 0.2197-0.2198 and leave the equivalence verdict
inside δ=1e-3, including the line-shopped construction, which is the benchmark's
best possible case. Mean absolute divergence from the headline is 0.016pt for
devig-then-mean, 0.15pt for the median, 0.37pt for line-shopping. The choice
was defensible and, as it turns out, immaterial; the paper says both.

---

## D10. Kalshi closing price — book-mid where the book survives, trade reconstruction where it does not
*Added 2026-09-03, same reason as D9: made in code, never written down, and it
is the largest measurement assumption in the exchange leg.*

**Decision.** `kalshi_hist_prices.price_side` returns the 1-minute candle
book-mid at official start where Kalshi's API still holds the book (a ~60-day
window), and otherwise reconstructs an effective bid and ask from the trade
tape's taker sides. On the frozen three-way sample that is **4,263 games
reconstructed to 1,070 book-mid — 80/20.** Both are anchored to the official
ESPN start and neither uses anything after it.

**Reasoning.** The alternative to reconstruction is not a better price, it is
no price: Kalshi retains no order book past the window, so a book-mid-only
sample would discard 80% of the games and would be selected on recency, which
is the one dimension along which this market is plausibly changing. A
reconstructed touch that is verifiably close to the real touch is a better
instrument than a sample four-fifths smaller and selected on the wrong axis.

**Why this is now evidence rather than an argument.** Two checks, both in the
suite as of 2026-09-03:

1. `validate_recon.py` compares the reconstruction against a third party's
   archived order-book snapshots (OddPool) for a stratified sample of 98 games:
   **94.9% exact bid match, 96.9% exact ask, median mid error 0.00pt, 99%
   within 1pt.** NBA is the residual (mean 1.67pt, n=24), the league whose
   books move fastest between the last fill and the bell. The validation covers
   CBB-M, MLB, NBA and NHL only — no NFL, CFB or WNBA rows — and says so.
2. `robustness_cuts.py` §2 splits the headline equivalence on the construction.
   Neither subsample rejects; the trade-recon sample is formally equivalent at
   δ=1e-3 and the smaller book-mid sample is power-limited with its MDE quoted.

**Known residual, declared not fixed.** `closing_trade_price` puts no age floor
on either reconstructed side, and `staleness_min` reports the age of the
*newest* fill, so a quote whose bid side is older than its ask side reports as
fresh (2026-07-30 review, item 11). The collector is retired, so this is a
limitation rather than a bug to fix, and check 1 is what bounds it.

---

## Changes required in code before drafting

| File | Change | Blocking |
|---|---|---|
| `src/analysis/rigor.py:63` | Replace the "≈0.5pt/game" gloss; print ε=√δ scale and the three cost-anchored margins | Yes — §5A |
| report outline (working doc) | Same correction wherever δ is glossed | Yes — §5A |
| `src/analysis/margin_dist.py` | Add nonrandomized (mean) PIT panel | No — appendix |
| `src/analysis/multiple_testing.py` | **Done 2026-09-03**: the inventory now re-derives every p from the frozen logs at run time instead of carrying them. It had drifted again since the July regeneration — the Murphy sup-t claim is retracted (0.037 → 0.129) and both encompassing claims strengthened | — |
