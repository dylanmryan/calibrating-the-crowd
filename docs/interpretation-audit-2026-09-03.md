# Interpretation audit — where a view, expectation, or assumption may have steered the work
*Written 2026-09-03, after the defensibility audit closed all sixteen of its items.
That audit asked whether each CHOICE was defensible. This one asks a different and
harder question: **did we only ever look where we expected to find something, and are
the claims stated at the strength the evidence supports?** Method: take each headline
claim, construct the strongest rival explanation a hostile reader would offer, and
check whether the project ever names it. Where a check was cheap I ran it.*

---

## Verdict

**The measurement is sound and the dead heat survives everything.** Two more cuts run
for this audit came back clean (news-conditional accuracy, league-equal weighting), and
nothing below disturbs §5A.

What this audit finds is different in kind: **one interpretive claim is stated at more
strength than the design can carry**, three scope exclusions are undeclared, and one
piece of the project's own evidence has a rival explanation it does not name. None of
these is a defect in the analysis. All of them are places where the paper currently
asks the reader to accept an interpretation the data underdetermines — which, in a
paper whose credibility rests on exactly the opposite habit, is the expensive kind of
mistake.

Ordered by how much I would want them fixed before submission.

---

## 1. The mechanism claim outruns the design *(the important one)*

**What the paper says.** Contribution 1, README and draft §3: *"Nobody leads. No venue
predicts another at 30, 15, 10, or 5-minute resolution. Price discovery is maker-driven
and parallel, not transmitted."*

**The problem.** "Parallel, not transmitted" is a causal claim about how prices form. The
evidence for it is a null: no venue predicts another at any clock resolution. But a
market maker quoting Kalshi continuously off the book's no-vig line would produce
*exactly that null* — no lead at any resolution, because there is no lag to detect. The
lead–lag design cannot separate parallel independent discovery from continuous
mirroring. It rules out **slow** transmission, which is a real and worthwhile result,
and the paper reports it as ruling out transmission altogether.

**What the data actually show.** Regressing each exchange's log-odds on the book's:

| exchange | R² on the book | idiosyncratic share | does that residual predict the outcome? |
|---|---|---|---|
| Kalshi | 0.9946 | 0.54% | coef +1.28, z=+2.11, **p=0.035** |
| Polymarket | 0.9865 | 1.35% | coef +0.38, z=+1.13, **p=0.259** |

So **Polymarket is not statistically separable from a de-vigged transform of the book
consensus** — the part of its price the book does not explain carries no detectable
information. Kalshi's residual does carry information, but that is the *encompassing*
result: p=0.035, flagged FRAGILE, and it has printed 0.004 / 0.048 / 0.044 / 0.054 /
0.021 across five vintages. The entire case for exchange price independence in
benchmarked markets rests on that one wobbling coefficient.

**This does not mean the exchanges copy the book.** Two genuinely independent, genuinely
accurate forecasters of the same games would also be ~0.99 correlated, because the games
differ enormously in difficulty and both track the truth. High correlation is not
evidence of copying. The point is the reverse: **the correlation is uninformative in
both directions, so the mechanism is underdetermined, and the paper should say so
instead of picking the flattering reading.**

**What genuinely supports independence** — and should be promoted to carry this claim,
because it is much stronger than the lead–lag null:

- **`niche_gradient`.** Un-benchmarked game markets, where no professional line exists to
  copy, are calibrated (excess ECE 0.00, slope 0.98, and 0.997 at the 1h staleness cut).
  Exchanges demonstrably do not *need* a book to price well.
- The fragile encompassing increment, quoted as fragile.

Note what the niche result does *not* establish: that exchanges ignore the book **where
one exists**. And the paper's own thesis — repetition and fast resolution produce
calibration, not the presence of a benchmark — is entirely compatible with exchanges
leaning on the book wherever it is available. These two readings are not in tension;
only the "not transmitted" phrasing forces a choice the evidence has not made.

**Recommended wording change.** From *"discovery is parallel, not transmitted"* to
something like: *no venue leads another at any resolution the data can see, so if the
exchange price is a fast function of the book it is a same-step one; and where no book
exists at all, exchange prices are calibrated anyway.* That is weaker, it is what the
design supports, and it costs the paper nothing — the dead heat and the boundary thesis
are untouched.

---

## 2. The law-of-one-price evidence has an unnamed rival explanation

**What the paper says** (`findings.md:120`): Polymarket US and Polymarket Global agree to
a median 0.50pt *"because both pools process the same public information, not because
anyone arbitrages the two books: the strongest version yet of the shared-information
mechanism."*

**The rival it does not name.** Legal segregation stops *participants* from trading both
pools. It does not stop **one operator from running both books**, or the same
market-making firms from quoting both venues off one model. Polymarket US and Polymarket
Global are the same company. Shared quoting infrastructure produces identical prices
across segregated pools with no arbitrage and no independent information processing
whatsoever — it is a third mechanism, and for this particular pair it is arguably the
*leading* one.

The argument as written eliminates arbitrage and then treats shared information as the
only survivor. That is a false dichotomy, and it lands on the sentence the paper calls
its strongest version of the mechanism.

**What to do.** This is not fixable with data — maker identity is not in any public tape,
which is itself worth saying. The fix is to name the third mechanism and scope the claim:
segregated pools rule out *participant* arbitrage, not common quoting. The Kalshi-vs-
Polymarket comparison is the more informative one here precisely because they are
unaffiliated firms, and it should carry the weight this sentence currently gives to
US-vs-Global.

---

## 3. Three scope exclusions that are never declared anywhere

Greped `findings.md`, `report-outline.md`, `drafting-plan.md`, README and the draft:

| excluded | mentions in the entire project |
|---|---|
| parlays / same-game parlays | **0** |
| player props | **0** |
| in-play / live betting | **0** (the readiness audit says "make sure §7 says so in one clause" — §7 does not) |

Each is a legitimate scope decision. The problem is that none is *stated*, and the first
two bear directly on the paper's framing.

**Parlays are the sharpest.** The paper's question is whether a prediction market is a
gambling venue or a forecasting institution, and it answers by comparing the **pre-game
moneyline** — the sportsbook's most efficient, lowest-hold, most heavily arbitraged
product. It is close to the book's loss-leader. The industry's actual economics, and the
product most implicated in the harm literature, is the parlay, where hold runs several
times the moneyline's and no exchange analogue exists. A reader entitled to be difficult
will say: *you compared the one product where books look most like forecasters, then
generalized to the institution.*

That does not invalidate anything — comparing like with like requires a product both
venues list, and the moneyline is that product. But it needs one honest paragraph, and
the paper is stronger for volunteering it than for being caught by it. The same
paragraph covers props and in-play.

---

## 4. The headline sample is a different league mix, and this is unreported

Requiring all three venues does not just shrink the sample, it re-weights it:

| league | share of Kalshi-priced clean set | share of the headline three-way set |
|---|---|---|
| CBB-M | 10.2% | **0.0%** |
| MLB | 41.2% | 23.3% |
| NHL | 15.4% | 26.0% |
| NBA | 14.3% | 24.1% |

College basketball vanishes entirely; baseball nearly halves. `referee.py` §1 tests
joint-vs-wide for the Kalshi–Polymarket comparison, which is the right instinct, but it
does not characterize the composition shift or ask whether the pooled result is a
weighting artifact.

**I checked. It is not:**

| weighting | Kalshi | Polymarket | Sportsbook |
|---|---|---|---|
| natural (n-weighted, as reported) | 0.2196 | 0.2198 | 0.2196 |
| league-equal (each league counts once) | 0.2145 | 0.2147 | 0.2144 |

Same ordering, same spacing, same verdict. Worth a two-line table in §5A and a sentence
in Data noting what the three-way requirement removes.

---

## 5. A cut that should exist and did not: accuracy conditional on news

If forecasting skill differs anywhere, it differs when there is something to forecast.
Nothing in the suite conditions on information arrival. Using the T−24h→close book move
as a news proxy (n=4,552 games with a T−24h price):

| news bucket | n | mean move | K | P | B | worst \|z\| | δ_min | MDE |
|---|---|---|---|---|---|---|---|---|
| quiet | 2,277 | 0.6pt | 0.2112 | 0.2115 | 0.2109 | 1.66 | 1.14e-3 | 1.01e-3 |
| some | 1,364 | 2.1pt | 0.2290 | 0.2292 | 0.2291 | 1.03 | 0.61e-3 | 0.80e-3 |
| busy | 683 | 4.0pt | 0.2292 | 0.2294 | 0.2292 | 0.68 | 0.79e-3 | 1.03e-3 |
| news (top 5%) | 228 | 8.9pt | 0.2426 | 0.2428 | 0.2432 | 0.76 | 1.95e-3 | 2.43e-3 |

Nothing rejects at any news intensity; the top bucket is underpowered and says so. This
is the theoretically best hiding place for a venue difference, and it is empty. It
belongs in `robustness_cuts.py` as a fifth cut — it is a stronger result than several
that are already in the paper.

---

## 6. The direction of the corrections — checked, and it defends you

A reader who notices that every correction moved the paper toward its own thesis would be
right to ask whether the pipeline has a thumb on the scale. It does not, and the record
shows it, but the paper never says so:

- Corrections that **removed a "Kalshi has a defect" claim** (strengthen the dead heat):
  the four ladder-convention retractions, the WNBA totals false alarm.
- Corrections that **removed a "Kalshi is better" claim** (weaken the exchange's case):
  the NBA encompassing sub-claim, wide-set K>P, log-score K>book, and — new on
  2026-09-03 — the Murphy sup-t edge.

**The corrections ran both ways, and roughly evenly.** That is a real defense of the
process and it should be one sentence in §3 or §7, because reconstructing it from the
`multiple_testing.py` header is work no reader will do.

One caveat to state alongside it: every correction moved *toward the null*. That is what
you would see if the null were true, and also what you would see from a pipeline whose
cleaning systematically shrinks extreme estimates. The out-of-sample verification is the
answer to that worry — say so explicitly at that point rather than leaving the two facts
in different sections.

---

## 7. The dead heat is under-sold by its own framing

The comparison is currently anchored to the Brier *level* (0.2196), which is dominated by
irreducible uncertainty. The CORP decomposition gives the honest scale:

- UNC 0.2500 — irreducible
- DSC 31.7e-3 — the skill any venue actually has
- MCB ~1.3e-3 — miscalibration
- pairwise differences ~0.2e-3

So the venues' skill differs by **under 1% of the skill any of them has**, and their
miscalibration differs by less than that. Stated against resolution rather than against
the Brier level, the dead heat is a considerably stronger claim than the paper currently
makes — and it is the framing that survives the obvious "0.2196 vs 0.2198 is a tiny
number, but so is everything here" objection.

---

## Considered and found clean *(so this audit is visibly not selective)*

- **Is the dead heat a de-vig artifact?** No — Shin robustness in `rigor`, and four
  consensus constructions in `robustness_cuts` §3.
- **Is it a favourite/longshot-range artifact?** No — `robustness_cuts` §1.
- **A league artifact?** No — `league_tost`, and the equal-weighting check above.
- **A time-period artifact?** No — `time_stability`, `referee` §4b.
- **A measurement-mode artifact?** No — `robustness_cuts` §2, `validate_recon`.
- **A clustering/normality artifact?** No — `rigor.cluster_levels`, `rigor.block_bootstrap`.
- **A news-intensity artifact?** No — §5 above.
- **Selection into the joint set?** Tested (`referee` §1) and re-tested here.
- **Publication bias inside the project?** The DISCOVERIES family is fixed by an
  inventory that has *lost* members, now re-derives from logs, and fails the suite if a
  claim cannot find its evidence. This is better handled than in most published work.

---

## To do — ALL NINE DONE 2026-09-03

Suite 61/0 after the changes; every addition is additive to the frozen logs.

**Before drafting §5A and §6 — these change what the paper says**

1. ✅ **Contribution 1 rewritten** in the README and the public draft, and the
   "parallel processing / not transmission" phrasing removed from `report-outline.md`
   §5.4 and `drafting-plan.md` §5B (grep is clean). The claim now reads: no
   transmission at any resolution the panel resolves — which the event study does
   support — with the independence weight moved onto `niche_gradient`. The evidence
   is a new **`encompassing.separability`** section printing R² on the book, the
   idiosyncratic share, and whether that share predicts outcomes, with the caveat
   stated in both directions (a high R² is not evidence of copying; a fragile
   increment on a 0.5% residual is not evidence of independence).
2. ✅ **Law of one price rescoped** in `findings.md` (with the correction marked in
   place, not silently), `report-outline.md` §5.1 and `drafting-plan.md` §5A ¶4. It
   now reads as arbitrage-elimination only; shared quoting infrastructure is named as
   the third mechanism; Kalshi-vs-Polymarket (unaffiliated firms, median 0.40pt)
   carries the shared-information claim.
3. ✅ **Product-scope paragraph** added to `report-outline.md` §7, leading the
   limitations rather than buried in the clause list: moneyline only, no parlays, no
   props, no in-play, with the two-way consequence stated — the moneyline is the
   book's most efficient product, and it is not where the money or the concern
   sits.

**Cheap, and each strengthens a claim**

4. ✅ **`robustness_cuts` §5, news arrival.** Buckets on |close − T−24h| of the book
   consensus (outcome-blind, measured on the leg no pairwise test singles out).
   Nothing rejects at any intensity; quiet and top-5% are power-limited and say so.
5. ✅ **`robustness_cuts` §6, league composition.** Prints the full shift (CBB-M
   10.2%→0.0%, MLB 41.2%→23.3%, NHL 15.4%→26.0%) and the pooled Brier under both
   weightings: natural 0.2196/0.2198/0.2196, league-equal 0.2145/0.2147/0.2144. Same
   ordering, same spacing. Also summarised in the §7 clause list.
6. ✅ **`rigor.scale_against_skill`.** Prints Brier / UNC / DSC / MCB per venue and
   the ratio that matters: mean discrimination 31.7e-3 against a widest pairwise 90%
   bound of 0.52e-3 — **the venues differ by at most 1.6% of the skill any of them
   has.** That is the framing that survives "0.2196 vs 0.2198 is a small number among
   small numbers".
7. ✅ **Correction-direction paragraph** in `report-outline.md` §7 and in the README's
   honesty section: four retractions removed a "Kalshi has a defect" claim, four
   removed a "Kalshi is better" claim. The caveat that nearly all moved toward the
   null is stated, with the registered OOS verification named as what separates "the
   null is true" from "our cleaning shrinks extremes".

**Housekeeping in the outline**

8. ✅ **Vintage housekeeping.** Outline header and §8 now say 61 modules and cite the
   2026-08-29 freeze plus the 2026-09-03 re-stamp; the pre-registration clause reads
   as discharged with its scorecard result rather than as planned.
   `report-readiness-audit.md` gains a status banner recording that all five of its
   gaps were closed, so it stops reading as an open list.

**Genuinely unavailable, and worth saying once**

9. ✅ **The missing datum is named** in the §7 mechanism paragraph and in the
   `encompassing.separability` log: maker identity is not in any public tape, so
   whether the same firms quote both exchanges cannot be settled from outside, and
   doing so would need venue cooperation.
