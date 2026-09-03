# Defensibility audit — arbitrary choices, unexplored paths, and what to do about them
*Written 2026-09-03, before the final report is drafted. Method: read the decision
record (D1–D8, readiness audit, registered claims, code-review findings), then sweep
the pipeline for choices that were **made but never justified, never varied, and
never reported** — the class of decision a referee converts into "how do you know
this isn't an artifact of that?" Where a check was cheap I ran it, on the frozen
data, and the result is quoted below. Those runs are **scratch, not suite** — every
one that stays has to become a module so the freeze stamps it, per the project's own
no-hand-carried-numbers rule.*

---

## Verdict

The **decision record is unusually good** — better than most published work. D1–D8
justify the choices that were consciously faced, and the readiness audit's "considered
and deliberately not added" list is the right instinct. Nothing below overturns a
finding. But the record covers the decisions you *noticed you were making*. The gap is
the layer underneath: **parameters that got picked once, early, and never revisited**,
and **conditioning dimensions the pooled result could be hiding**.

Three things are genuinely load-bearing and currently undefended:

1. **The book consensus construction** (mean-of-vigged-probs, then de-vig once) is the
   paper's benchmark and is asserted nowhere. Tested below: it doesn't matter.
2. **80% of Kalshi closes are trade-reconstructed, not observed quotes** — a fact the
   public draft currently contradicts in print, and which no headline robustness cut
   conditions on. Tested below: it doesn't matter, and there is an external validation
   of the method sitting outside the suite and uncited.
3. **ECE is reported as a headline number and is strongly bin-dependent** — the
   cross-venue *ranking* on ECE flips with bin count. Nothing in the paper ranks on
   ECE, but the README table invites the reader to.

Everything I tested held. That is the point: the work is defensible, and right now it
isn't *shown* to be. Most of what follows converts an unstated assumption into a
reported row.

---

## Part A — Arbitrary choices that are undocumented and untested

### A1. Book consensus aggregation *(highest value; genuinely undefended)*

`src/collect/sportsbook_hist.py:_consensus` averages **raw (vigged) implied
probabilities across books, then de-vigs the average once.** Three other constructions
are equally standard, and the choice is recorded nowhere — not in D1–D8, not in the
data dictionary, not in the outline.

Ran on the 4,655 games with per-book detail (`sportsbook_us_books.csv`):

| construction | book Brier | K–B clustered z | p | \|CI\|max |
|---|---|---|---|---|
| headline `book_p1` | 0.2197 | +0.07 | 0.942 | 0.24e-3 |
| mean-then-devig | 0.2197 | +0.26 | 0.798 | 0.26e-3 |
| devig-then-mean | 0.2197 | +0.26 | 0.796 | 0.26e-3 |
| devig-then-median | 0.2197 | +0.22 | 0.828 | 0.26e-3 |
| best-price (line-shopped) | 0.2198 | −0.61 | 0.539 | 0.31e-3 |

Mean absolute divergence from the headline: 0.016pt (devig-then-mean), 0.15pt (median),
0.37pt (best-price). **Equivalence at δ=1e-3 holds under all four**, including the
line-shopped construction that gives the books their best possible case. This is a
one-paragraph robustness row that closes the single most obvious attack on the
benchmark, and it currently doesn't exist.

Also unstated: `regions="us"` — the consensus is US books only (Pinnacle and Betfair
enter separately via `sportsbook_sharp`). Say so once.

### A2. Kalshi price construction is two different instruments, mixed

`price_side()` returns a **1-minute candle book-mid** where Kalshi's 60-day window
still holds the book, and a **trade-reconstructed bid/ask** otherwise. On the frozen
three-way set that is **4,263 trade-recon vs 1,070 book-mid — 80% reconstructed.**
No analysis splits on `k_src`. Ran it:

| construction | n | K | P | B | K–B z | p | \|CI\|max |
|---|---|---|---|---|---|---|---|
| trade-recon | 4,263 | 0.2145 | 0.2148 | 0.2146 | −1.31 | 0.191 | 0.38e-3 |
| book-mid | 1,070 | 0.2400 | 0.2396 | 0.2393 | +1.70 | 0.090 | 1.25e-3 |

Neither rejects; the trade-recon subsample is formally equivalent at δ=1e-3, the
book-mid subsample is power-limited (quote the MDE, don't call it equivalent). Clean
result, needs reporting.

**Two consequences beyond the robustness row:**

- **`docs/public-writeup-draft-2026-09-03.md` §2 says "Every price is a live snapshot
  taken while the market was open, not a closing line reconstructed later."** That is
  false for 80% of the Kalshi leg and for the whole book leg (Odds API historical
  snapshots). It is the kind of sentence that, if caught by a reader, costs more
  credibility than the underlying issue warrants. Rewrite it to say what is actually
  true and *why it is still sound*: no look-ahead anywhere (verified in the code
  review), prices anchored at official start, and the reconstruction externally
  validated (next bullet).
- **`src/analysis/validate_recon.py` externally validates the reconstruction against
  archived OddPool order books and its result is cited nowhere.** n=98: exact bid match
  94.9%, exact ask 96.9%, median mid error 0.00pt, 99% within 1pt (NBA is the outlier
  league at 1.67pt mean, n=24). This is the evidentiary basis for 80% of the Kalshi
  sample and it lives outside the suite (excluded for network cost) in an untracked
  CSV. Split it into a network `collect()` and an offline `report()`, put `report()` in
  `MODULES` so the freeze stamps it, and commit `recon_validation.csv` (it contains no
  paid book data — it is free-tier OddPool plus Kalshi, so the redistribution
  constraint in the README does not apply).
- Coverage gap worth one clause: the validation sample is CBB-M / MLB / NBA / NHL only.
  No NFL, CFB, or WNBA row.

### A3. Trade-recon has no time floor on the reconstructed side

`closing_trade_price()` takes the most recent 300 trades and picks the newest
`taker_side=="yes"` as the ask and newest `taker_side=="no"` as the bid — **with no
age limit on either.** `staleness_min` reports the age of the *newest* fill, so a
book whose bid side is days old still reports as fresh. This was Tier-2 item 11 of the
2026-07-30 review and is still open in code. A2's validation empirically bounds the
damage (median error 0.00pt), which is the honest defence — but the defence has to be
*stated*, because the staleness column does not carry it.

### A4. Quality flags are collected and never used

`k_stale1/2`, `k_spread1/2`, `poly_stale1/2`, `book_n_books` are carried all the way
into `games_master.csv` and then touched only by the audit gates, `decomposition`'s
spread tercile, and `encompassing`'s liquidity restriction. **`three_way.load()`
filters on nothing but outcome resolution and price presence.**

The good news, measured on the frozen set:

- `k_stale1`: median 0.1 min, 99.9% under 60 min.
- `poly_stale1`: median 0.9 min, **max 8.1 min** — the 8-hour `window_h` lookback in
  `poly_price_at` never actually binds.
- `book_n_books`: median 11, 99.6% of games have ≥5 books.

So the honest statement is not "we filtered" but "**no filter was needed, and here are
the distributions**." One table in Methods. It costs nothing and it pre-empts the
question. Related: **`docs/registered-claims.md` describes H-EX as passing "the exact
`three_way.load()` clean-set quality filters (spread, staleness, source flags)."**
Those filters do not exist. `load_hex()` correctly mirrors what `load()` actually does,
so the *analysis* is right and only the *description* is wrong — but that sentence sits
in the pre-registration document, which is the last place you want an inaccurate
description of the sample definition. Annotate it below the post-pull line.

### A5. ECE's bin count is arbitrary and the venue ranking is not bin-stable

`compare.ece(nbins=10)`, `compare.reliability(nbins=12)`, `nuance.reliability_table(nbins=20)`
— three different bin counts in one codebase. Swept on the frozen stacked sides:

| nbins | Kalshi | Poly | Book |
|---|---|---|---|
| 5 | 0.0058 | 0.0050 | 0.0062 |
| 10 | 0.0129 | 0.0128 | **0.0087** |
| 12 | 0.0123 | 0.0121 | **0.0155** |
| 20 | 0.0191 | 0.0198 | **0.0267** |

The level roughly triples from 5 to 20 bins, and **the book goes from best to worst
between 10 and 12 bins.** The paper never ranks on ECE — CORP/MCB is the binning-free
measure and it is already in `referee` — but the README's headline table puts ECE
0.009–0.014 next to the Briers, which is exactly the invitation to rank.

Fix, in order of value: (i) make **CORP MCB the reported miscalibration statistic**
and demote ECE to a descriptive level; (ii) wherever ECE appears, quote it **against a
noise floor** — `oos_verification.ece_noise_floor()` already does this correctly for
the holdout and should be run on the frozen sample too, where it is currently absent;
(iii) state the bin count in the caption and add the sweep to the appendix; (iv)
standardise the three bin counts or document why they differ.

### A6. The logit clip at [0.01, 0.99]

`cal_slope` and every log-odds transform clip probabilities to 1–99c. The frozen
sample's price range is 2.5c–98.5c, so the clip **binds on real observations** — and
it binds precisely in the tails, which is where the favourite–longshot claim lives.
Clipping compresses the tails toward the centre, which biases the estimated slope
*toward 1*, i.e. toward the paper's own no-FLB conclusion. The bias is certainly tiny
at this sample's tail density, but the direction is unfavourable and the check is two
lines: re-report slopes at clip 0.005 and 0.001 and confirm the CIs still cover 1.

### A7. Untested threshold constants

Each of these was picked once and never varied. Most are conventional and I would not
spend time on them — listed so the record shows they were weighed:

| constant | file | status |
|---|---|---|
| `THRESH = 0.02` (≥2pt book move) | `book_moves`, `five_min` | **worth a sweep** — it defines the event study's population; a size split exists but not a threshold sweep |
| `K_ELO = 20`, `REGRESS = 1/3`, `BURN` | `model_benchmark` | K is swept (10/32) ✅; `REGRESS` and `BURN` are not, and the Elo floor is a headline comparison |
| `GLITCH = 0.10`, `MAXGAP_FFILL = 20`, `NLAG = 5` | `minute_lead_lag` | conventional; the null is symmetric and robust across four clocks — declare, don't sweep |
| `TICK = 0.011` | `coherence` | fine (one cent + epsilon), state it |
| `STALE_MAX_MIN = 120`, `FILLS_MIN = 5` | `four_way` | fine, state them |
| `MAX_STALE_MIN = 360` | `niche_gradient` | 6h is loose for a calibration sample; worth one sensitivity line |
| `TAKER_COST = 0.042` | `rigor` | anchors the whole D2 margin ladder — sourced to `immediacy.log`, good, but the ladder should show ±1pt on the cost |
| `EQUITY_REAL_ANNUAL = 0.07` | `horizon_translation` | an economic assumption in a headline number; state it in the caption |
| `bucket_min = 30`, 3-hour match window | `sportsbook_hist` | the source of the "consensus timing" caveat — already conceded |

---

## Part B — Conditioning dimensions the pooled result could be hiding

### B1. Clustering: the choice does not matter, and you can now say so

Your instinct was right that this needs an answer. D4 justifies date clustering and
correctly refuses two-way date × league (7 leagues). What D4 does not do is show that
the choice is immaterial. Ran the headline three pairs at five clustering levels:

| pair | iid | league×date (G=859) | **date (G=386)** | week (G=59) | month (G=15) |
|---|---|---|---|---|---|
| K–B | 0.125e-3 | 0.127e-3 | **0.130e-3** | 0.156e-3 | 0.156e-3 |
| K–P | 0.139e-3 | 0.168e-3 | **0.170e-3** | 0.173e-3 | 0.155e-3 |
| P–B | 0.151e-3 | 0.182e-3 | **0.182e-3** | 0.160e-3 | 0.149e-3 |

(clustered SEs, with the G/(G−1) finite-sample correction applied.) No p-value crosses
0.05 at any level. Date clustering is **more conservative than week or month** for two
of the three pairs and within 20% for the third — i.e. the more conservative choice was
already made. **Team clustering** (home team, G=271) gives *smaller* SEs than date on
all three pairs, so there is no team-level dependence date clustering is missing.

This also settles open code-review item 17: applying G/(G−1) moves the SE by <1% at
G=386 and ~3% at G=15. Demonstrated rather than asserted, and it costs one table.

**The clustering dimension you have not tried and might want:** none, as a variance
estimator. But a **week-level block bootstrap** of the Brier differential would be a
distribution-free companion to the normal-approximation TOST, and at 59 weekly blocks
it is well-conditioned. Optional, half a day.

### B2. Favourite strength — your example, and it is a real gap

Nothing anywhere runs DM/TOST **by price level.** A pooled Brier is dominated by
mid-price games; a venue difference confined to heavy favourites would be invisible in
it, and that is exactly where a referee will look, because that is where the money
concentrates. Ran it, bucketing on the outcome-blind three-venue consensus price:

| bucket | n | K | P | B | worst \|z\| | δ_min | MDE |
|---|---|---|---|---|---|---|---|
| coin-flip (<5pt from 50c) | 1,396 | 0.2487 | 0.2489 | 0.2487 | 0.62 | 0.78e-3 | 0.97e-3 |
| mild (5–15pt) | 2,075 | 0.2456 | 0.2455 | 0.2457 | 0.51 | 0.47e-3 | 0.61e-3 |
| clear (15–25pt) | 885 | 0.2094 | 0.2097 | 0.2091 | 1.67 | 1.21e-3 | 1.02e-3 |
| heavy (>25pt) | 977 | 0.1319 | 0.1327 | 0.1321 | 1.24 | 1.88e-3 | 1.90e-3 |

Nothing rejects anywhere; **formal equivalence at δ=1e-3 in the two largest buckets**,
power-limited in the two tail buckets with the MDE quoted — exactly the house reading
rule. This should be a table in §5A. It is the single best addition available for the
effort, and it is *the* answer to "your dead heat could be hiding a difference in the
tails."

### B3. Sample-exclusion sensitivity

The clean set drops 79 of 5,412 all-three games (1.5%) on `outcome_disagree`, and the
drop is **venue-asymmetric**: 72 Kalshi vs 7 Polymarket. A referee will ask whether a
filter that removes 10× more of one venue's games is selecting on that venue's errors.
Answer, measured:

| set | n | K | P | B | worst \|CI\| |
|---|---|---|---|---|---|
| paper set (clean) | 5,333 | 0.2196 | 0.2198 | 0.2196 | 0.52e-3 |
| including all disagreers | 5,412 | 0.2200 | 0.2203 | 0.2200 | 0.56e-3 |

Every conclusion survives keeping them and trusting ESPN. One row, and the asymmetry
becomes a footnote instead of a vulnerability. (`referee.py` §1 does the *selection*
version of this — joint vs wide set — but not the *exclusion* version.)

### B4. Conditioning cuts that exist for one venue but not for the comparison

`nuance.py` cuts Kalshi calibration by spread (median split) and staleness (≤5 min),
and `decomposition.py` cuts by spread tercile — **but only Kalshi's own calibration,
never the three-way equivalence.** Given A4's distributions the answer will be "no
change," which is exactly why it is worth one line.

### B5. Dimensions checked and genuinely not worth building

So the audit is exhaustive rather than selective:

- **Two-way date × league** — declined for cause in D4 (7 clusters), and B1 now shows
  the variance estimator is insensitive anyway. Keep the refusal, cite B1 alongside it.
- **Home/away asymmetry** — `referee` §2 already reports home-side-only slope and ECE
  against the stacked version.
- **Playoffs vs regular season** — built (`referee` §4b, commit 97b9c00). ✅
- **Time / quarter stability** — `time_stability`. ✅
- **Day-of-week, primetime, national broadcast** — plausible shared shocks, but they
  are *within* the date cluster the SEs already absorb, and there is no mechanism story
  that predicts a venue *difference* there. Skip; record the skip.
- **Rest days, weather, travel** — declined in the readiness audit; the Elo floor
  already bounds public-information content. Keep declined.
- **Divergence-conditional accuracy** — answered twice (encompassing, divergence
  backtest). Keep declined.
- **Book-count conditioning** — 99.6% of games have ≥5 books; no variation to exploit.
  Report the distribution (A4) instead of the cut.

---

## Part C — Documentation defects that cost more than they should

These are cheap and they matter disproportionately, because a reader who catches one
starts discounting the rest.

1. **`docs/code-review-findings.md` header still reads "Status: OPEN unless noted"**
   and lists 23 findings, 5 of them Tier-1 "changes published claims." The git history
   shows most were fixed (43bfb88, bed8579, 70a5893, 490fa7f). As it stands, an advisor
   or referee opening this file sees 23 live defects in a frozen project. **Add a
   per-item status column** (FIXED + commit / OPEN + why it is acceptable). This is the
   highest ratio of credibility-recovered to effort in the whole audit.
2. **`docs/figure-map.md:5`** says statistics are quoted from the **2026-08-23** logs;
   `report_visuals.py:16,100` says **2026-08-29 freeze**. The figures are right, the map
   is stale. Same file says "Nine figures" and then lists F0–F14.
3. **`docs/registered-claims.md`** H-EX row describes filters that do not exist (A4).
   Annotate below the post-pull line — never edit above it.
4. **`src/analysis/multiple_testing.py`** hard-codes p-values "as of the 2026-07-30
   suite run" with individual entries hand-patched to later vintages. This is the exact
   failure mode Tier-1 item 1 caught the first time, rebuilding itself. Either have the
   module **grep each cited log for its p-value**, or add a `data_audit` gate that does
   and fails the suite on drift. Given the retraction record is one of the paper's
   genuine contributions, the inventory that carries it should not be hand-maintained.
5. **README** quotes ECE 0.009–0.014 with no bin count and no noise floor (A5).

---

## Part D — Code-review items that appear still open

Spot-checked against current code. None threaten a conclusion; all should have a stated
status per C1.

| # | item | status | disposition |
|---|---|---|---|
| 11 | trade-recon unbounded look-back | **open** | defend via A2's validation, or add a max-side-age flag |
| 15 | `nuance` per-bin binomtests double-count mirrored sides | **open** | anti-conservative stars near 50c; drop the stars or halve n |
| 16 | CORP band resamples mirrored sides independently | **open** | band too wide near 50c → *overstates* support; declare direction |
| 17 | `cluster_dm` uses CR0, z not t(G−1) | **open** | **quantified in B1: <1% at G=386.** Add the correction (3 lines) or cite B1 |
| 19 | MLB cell z-stats ignore pairing/covariance | **open** | direction is conservative; state it |
| 23 | `profitability` bootstrap resamples bets iid | **open** | should be game- or date-clustered; likely narrows CIs spuriously |
| 23 | `coherence` bracket check is an upper bound | **open** | fine, but the 0.10% arbitrage figure should say "≤" |
| 23 | `fee_liquidity` label errors ("Feb" includes Mar 1; "biweekly" is weekly) | **open** | labels only — fix or annotate |
| 9/10/12 | `fee_volumes` false zeros; `polyus` endDate anchor; `live_snapshot` DH ambiguity | **open** | collector-side; analysis guards downstream. Record as known limitations — collectors are retired, so these are documentation items now, not fixes |

---

## Concrete to-do list

Ordered by *credibility bought per hour*. Items 1–6 are the ones I would not draft
without.

**Tier 1 — DONE 2026-09-03.** Suite re-stamped at 61 modules, 0 failures. The
2026-08-29 frozen logs reproduced *bit-identically* except for a wall-clock
string in the PyMC log; the only content changes are additive (`rigor`,
`referee`) plus two new modules. Every cut below came back clean.

*(original scoping: do before writing §5A, ~one day)*

1. ✅ **Fix the public draft's "live snapshot" sentence** (A2). Replaced with an
   accurate account of the three constructions, the 80/20 split, and the external
   validation — which reads as a strength rather than a caveat.
2. ✅ **Status-annotate `code-review-findings.md`** (C1). Re-verified all 23 against
   current code: every Tier-1 finding fixed; 9 remain open, each bounded,
   direction-conservative, or in a retired collector. Body left unedited as the
   historical record; status table added on top.
3. ✅ **New module `robustness_cuts.py`**, in `MODULES`, carrying four tables:
   - equivalence by **favourite-strength bucket** with MDEs (B2) ← the important one
   - equivalence by **Kalshi price-construction mode** (`k_src`) with MDEs (A2)
   - equivalence under **four book-consensus constructions** incl. line-shopped (A1)
   - **exclusion sensitivity**: clean set vs including all 79 disagreers (B3)
   All four pass. Every cell prints its worst-|z| *with the pair that produced it*,
   its δ_min and its MDE, and the module states that EQUIV and a significant z can
   co-occur without contradiction (TOST asks "is it small", DM asks "is it zero").
4. ✅ **Clustering-robustness table** (B1) in `rigor.cluster_levels`: six levels with
   the G/(G−1) correction and t(G−1). No level crosses α=.05 on any pair and the
   widest 90% bound anywhere is ~0.52e-3, half the pre-stated δ. D4 is now a
   demonstration, and open review item 17 is quantified rather than asserted.
5. ✅ **Trade-recon validation is now reportable** (A2): `validate_recon.collect()` is
   the network path (by hand), `main()` the offline report, which is in `MODULES`.
   It states what it underwrites (8,024/10,069 = 80% of Kalshi prices), the
   agreement (94.9%/96.9% exact bid/ask, median mid error 0.00pt, 99% within 1pt),
   and its own coverage limit (no CFB, NFL or WNBA rows). `recon_validation.csv` is
   un-ignored and ready to commit — it carries no paid book data.
6. ✅ **ECE discipline** (A5): `referee.py` §5 prints the bin sweep (5–25) and the
   binomial noise floor on the frozen sample. All three venues sit at 0.89–1.35× the
   floor — i.e. at it. MCB is now the README's reported miscalibration column
   (K 1.31 / P 1.33 / B 1.45 e-3) with ECE demoted to a footnoted level, and §4 says
   in the log that MCB is the statistic that carries a comparison. *Also corrected
   while there: the README had Polymarket's Brier as 0.2199; the log says 0.2198.*

**Tier 2 — DONE 2026-09-03.** All six. One of them turned out to be neither
cheap nor cosmetic: rebuilding the FDR inventory to read its own logs **changed
which claims survive BH** (item 10).

*(original scoping: cheap, half a day)*

7. ✅ **Quality-flag distribution table** — `robustness_cuts.py` §0. Kalshi quote
   age median 0.1 min, Polymarket 0.9 min (max 8.1, so `poly_price_at`'s 8-hour
   look-back never binds anywhere near its limit), 11 books in the consensus for
   99.6% of games. No filter was needed; now it is shown rather than asserted.
8. ✅ **Doc-vintage defects.** figure-map now reads 2026-08-29 freeze and
   "Fifteen figures (F0–F14)"; `registered-claims.md` carries a second annotation
   *below* the post-pull line correcting the H-EX filter description (the analysis
   was always right — `load_hex()` mirrors what `load()` actually does — only the
   description was wrong); the README ECE line was done in Tier 1.
9. ✅ **Logit-clip sensitivity** — `decomposition.py`. **My audit was wrong here:**
   A6 asserted the 1c/99c guard "binds on real observations." It binds on exactly
   one observation out of 5,333 (Polymarket's 99.2c home price); Kalshi and the
   books clip nothing. The module now prints each venue's price extremes, the
   clipped count, and slopes at three clips — identical to three decimals, every
   CI covering 1.
10. ✅ **`multiple_testing` now re-derives every p from the frozen logs** — each
    claim names a log, a regex, and whether the capture is a p or a z; a pattern
    that stops matching raises and fails the suite; a drift report prints against
    the previously asserted values. **This changed the paper's claim set:**
    - **Murphy sup-t vs the Shin book: 0.037 → 0.129. RETRACTED.** It survives at
      no threshold, and it was always the claim most exposed to the de-vig choice.
    - **Both encompassing terms strengthened and now survive BH at q=0.05**
      (K-beyond-book 0.054→0.033, K-beyond-Poly 0.044→0.021). The FRAGILE flag
      stays: this family has printed 0.004 / 0.048 / 0.044 / 0.054 / 0.021 across
      five vintages, which is a result at the data's resolution limit, not a
      stable effect.
    - **The futures pooled longshot p (6e-3) has no generating line** in
      `futures_calibration.log` and is now held OUT of the BH family, on the
      precedent set for "sharpens 24h→start". The effect is still reported
      descriptively; the p-value is what lacked a source.
    - Net: **15 claims in the family, 13 survive q=0.05, 14 at q=0.10.**
    Propagated to `findings.md` (two passages), `report-outline.md` appendix C,
    and the README retraction count (ten → eleven).
11. ✅ **D9 (book consensus construction) and D10 (Kalshi price construction)**
    added to `methodology-decisions.md`, each with its reasoning, its robustness
    evidence, and — for D10 — its declared residual (the unbounded trade-recon
    look-back, review item 11). D4 also gains a cross-reference to the new
    clustering demonstration.
12. ✅ **Tier-3 items closed or declared.** 15 fixed (binomial now on the halved
    effective sample; no star changes state on the frozen data, so it is a guard
    against a future false flag). 23b fixed (the coherence rate prints as an upper
    bound and says why). 23c fixed — and **the review's predicted direction was
    backwards**: a game's two sides are perfectly anti-correlated, so the game-level
    cluster bootstrap *narrows* the interval ([−4.4%,−4.1%] vs iid's
    [−6.0%,−2.6%]); correct either way, and it sharpens the cost result. 17
    **declared, not applied**: re-basing every number in a frozen pre-registered
    suite for a sub-1% effect trades transcription risk for no inferential gain,
    so the corrected estimator is printed alongside in `rigor.cluster_levels` and
    a reader may use either.

**Tier 3 — DONE 2026-09-03.** All four. Two of them turned up something the
default cut was hiding (items 13 and 16).

*(original scoping: optional, maximum armour, one day)*

13. ✅ **Threshold sweep** — `book_moves.threshold_sweep`, called from both clocks.
    It RE-DETECTS events at each cut rather than sub-setting the 2pt events, which
    matters because detection enforces non-overlap. On the 15-min clock the
    anticipation share runs 23–42% across a 3× range of cuts — below chance
    throughout, significantly so at 1.0/1.5/2.0pt — so "no anticipation" is a
    property of the data, not of the cut. **The 5-min clock is the find:** its
    event study reports n=7 and gives up at the 2pt default, but a 1pt cut yields
    55 events and reproduces the below-chance result independently (27%/17%,
    p<0.001). The 2pt default is kept for comparability with the 15-min study
    rather than tuned per clock, and the log now says so.
14. ✅ **Week-block bootstrap** — `rigor.block_bootstrap`, 59 weekly blocks ×
    4,000 resamples. Analytic vs bootstrap 90% intervals: K–P (−0.51,+0.05) vs
    (−0.52,+0.05); K–B (−0.22,+0.20) vs (−0.25,+0.25); P–B (−0.08,+0.52) vs
    (−0.03,+0.49), all e-3. Same EQUIV verdict on all three, so the headline
    survives dropping both the normality assumption and the cluster-SE formula.
15. ✅ **Elo hyperparameter grid** — `model_benchmark`. Ten settings across K,
    `REGRESS` and `BURN`. `BURN` changes the evaluation set, so each row's gap is
    computed against the best market Brier *on that row's own games*; comparing
    raw Briers across rows would not be a comparison. Narrowest gap anywhere is
    7.5e-3 (burn=20), and that row narrows only by dropping early-season games —
    where a cold Elo is worst and the market's edge is largest — so it is a
    smaller question, not a better model. The floor never comes within reach.
16. ✅ **Niche staleness sweep** at 1h / 3h / 6h / 24h. Excess ECE is 0.00pt at
    every cut and the slope stays near 1 — and the **1h cut is the cleanest**
    (slope 0.997), so the un-benchmarked-markets-are-calibrated result is not
    bought by the loose 6h window; if anything the loose window costs a little.
    The default stays at 6h because the tighter cuts are thinner samples with
    higher noise floors, and the log now states that trade-off.

**Explicitly decline and record in the readiness audit's "considered and not added"
list** (so the exhaustiveness is visible): two-way date×league clustering (D4, now
reinforced by B1), day-of-week / primetime cuts (B5), book-count conditioning (B5),
and the remaining collector-side items 9/10/12 (collectors retired — limitations, not
fixes).

---

## One framing note for the report

Every check in Tier 1 came back clean. That is worth saying out loud in §4 rather than
burying in an appendix, because it is a *result*: the dead heat is invariant to the
book-consensus construction, to which of two instruments produced the Kalshi price, to
favourite strength, to the clustering level, and to whether the 1.5% of disputed games
are kept or dropped. A finding that survives five independent ways of trying to break
it is a much stronger claim than a finding reported once — and this project has already
earned the right to say so, having broken four of its own claims when they didn't
survive.
