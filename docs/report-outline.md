# Report outline — Calibrating the Crowd
*Drafting outline (2026-08-06; numbers re-verified against the 2026-08-29
freeze, the 2026-09-03 re-stamp at 61, the 2026-09-16 re-stamp at 63 and the
2026-09-23 re-stamp at 65 modules, 0 failures throughout). Provenance in
brackets. Figures referenced by filename exist in `results/`. Sections 7 and 8
were revised 2026-09-03 following the interpretation audit — see
`docs/interpretation-audit-2026-09-03.md`.*

**Working title:** Calibrating the Crowd: Prediction Markets and Sportsbooks
as Rival Forecasters of the Same Games

**Thesis in three sentences.** On five thousand identical games, a
CFTC-regulated exchange, an offshore crypto market, a second US-regulated
exchange, and the professional sportsbook complex — including Pinnacle and
every major US retail brand — produced formally equivalent forecasts, priced
in parallel with no leader at any time resolution. The institutions differ
not in accuracy but in design: what participation costs, who supplies the
liquidity, and how precision and existence of prices follow the
market-maker complex. The boundary of this discipline is not the
institution but the market type: one-shot, long-horizon outrights are badly
priced by everyone — exchanges and books alike — while repeated,
fast-resolving markets are clean even without a benchmark, deep liquidity,
or a big platform.

---

## 1. Introduction
- Hook: the same ~5,300 games were priced simultaneously by four
  institutionally distinct mechanisms. Did the crowd match the professionals?
- The framing rule (locked): gambling venue vs forecasting institution —
  never trading exploitability.
- Contributions:
  1. First same-game three-way (then four-way) calibration with a books
     benchmark, formal equivalence (TOST), not just "no significant difference."
  2. The benchmark upgraded to the sharp price itself (Pinnacle) and to
     book-by-book US retail.
  3. Distributional layer: margins, ladders, PIT, RPS — a near-dead-heat
     here too after the 2026-08-23 ladder-convention correction: a small
     NBA-carried book edge (+0.49e-3 pooled RPS), and — after the 2026-09-23
     conditioning correction — **no shared blind spot at all**. The
     "extra-innings margins, missed by ~20pt at both institutions" claim that
     stood here is RETRACTED: the split conditions on a state realized during
     the game, and a constant forecaster reproduces it (+21.19pt vs the
     market's +20.22pt) [extras_conditioning.log §1].
  4. Horizon-resolved: when the equivalence forms; minute-scale price
     formation; maker-driven discovery.
  5. Institutional accounting: costs, fees, ticks, taker P&L, the affiliated
     dealer, and where the liquidity complex deploys.
  6. The discipline boundary: a futures/outrights 2x2 plus a no-benchmark
     niche tier that isolates repetition as the active ingredient.
  7. Methods lessons: three independent pipeline catches — the
     side-assignment audit, stale-print traps in resolved-market histories,
     and the league-specific ladder settlement conventions — each converted
     into a permanent audit gate.

## 2. Literature (updated)
- Page & Clemen 2013 (sharpening toward event date) — replicated comparatively.
- Snowberg & Wolfers 2010 (FLB as misperception) — no FLB in game markets,
  any source; FLB alive in outrights at every institution.
- Levitt 2004 (books shade toward bettor biases) — tested per book on two
  continents: dead (30+ books, deviations sub-1pt, sign mostly opposite).
- Burgi, Deng & Whelan: platform-wide pathologies (replicated as our sports
  null) + "Makers and Takers" 2026 (makers > takers) — our taker P&L and
  maker-structure legs are the institutional mechanism for their result.
- Clinton & Huang 2026 (cross-platform); Woodland & Woodland 1994 (MLB
  run-line context); practitioner run-line literature.
- Regulatory: CFTC bona fide MM proposal (2026-07-30), the MPU investigation
  and 2025-26 class actions — §5.7 speaks directly to the live policy question.

### 2.1 The demand side: who is using these, and as what (new, Aug 2026)
The public debate is conducted almost entirely in the language of CATEGORIES —
every participant asserts whether this is investing or gambling, and none of
them measures. This paper is the measurement. Sources, all 2026:
- **Betterment 2026 Retail Investor Survey** ("The Guidance Gap"; n=1,000 US
  retail investors, fielded Mar 27-Apr 3 2026 via Sago, four generations, all
  holding at least one qualifying investment; full report at
  betterment.com/retail-report): **52% of Gen Z investors redirected money
  earmarked for investing into sports betting in the past year**; **26% treat
  sports betting as a deliberate part of a long-term financial strategy**
  (vs 14% millennials, 6% Gen X, 1% boomers); among those who feel financially
  behind, 32% of Gen Z and 24% of millennials are in or considering prediction
  markets or sports betting, ~80% of them believing high-risk speculative
  products beat traditional ones. CEO Sarah Levy: "When a prediction market or
  sportsbook starts to feel like a retirement strategy, we have a problem."
  CAVEAT to state in text: Betterment is a robo-advisor and has a commercial
  interest in this finding; the measure is self-reported.
- **Schwab** (Rick Wurster, CEO): "We'll leave the sports gambling... to the
  gambling houses — the FanDuels, the DraftKings and the Robinhoods," while
  distinguishing sports event contracts from economic-indicator ones. A second
  institution performing the same categorization, in the opposite direction.
- **Northwestern Mutual 2026**: 32% of Gen Z have invested in or are
  considering sports betting / prediction markets, vs 24% of millennials.
- **Scale**: Robinhood processed >16bn event contracts through June 2026
  ($156m Q2-2026 revenue, ~10x YoY); reporting puts **~95% of prediction-market
  volume in sports**. This retires "sports scope" as a limitation and makes it
  the main case: sports is not a corner of this industry, it is the industry.

USE: this section supplies the stakes, and the paper supplies the missing
measurement. Levy and Wurster both treat "prediction market" and "sportsbook"
as one category; §5.1-§5.6 show that conflation is RIGHT about cost and
clientele and WRONG about information. And Betterment's finding is about
HORIZON — people using these for long-term wealth — which is exactly the axis
§5.9 shows the discipline breaking on.

## 3. Data and pipeline
- Sources table: Kalshi (book-mid post-cutoff / validated trade-recon
  pre-cutoff), Polymarket Global (CLOB), Polymarket US (DCM tape),
  sportsbooks (Odds API: US consensus, EU per-book incl. Pinnacle/Betfair,
  US per-book (86% of joint set), T-24h, alt-spreads, outrights 2020-26), ESPN
  anchor. Master 10,118 games / 7 leagues; three-way clean n=5,333 (frozen).
- External validation: trade-recon vs archived books 99% within 1pt; Poly
  CLOB vs archived books median error 0.00pt.
- Audit-gate architecture (79 checks -- 55 in data_audit.log + 24 in
  deep_audit.log; suite halts on failure) [corrected 2026-09-15: the
  "73 checks" figure matches neither log nor their sum] + the
  side-assignment lesson (own subsection).
- **Quote timing is recorded, and it matters** (added 2026-09-16). Both per-book
  tapes carry each bookmaker's own `last_update`, so the age of every book quote
  at kickoff is known. Credit-batching made that age bimodal — 56% of games
  priced within ~5 min of start, 31% more than 30 min out, almost nothing
  between — which §5.1 uses as a natural experiment on the design's one timing
  asymmetry. Say here that the split is the collector's cadence, not a property
  of the games, because that is what licenses reading it causally.
- **The live panel's book leg is a cross-book MEAN**, built at ingest with the
  members discarded (`collect/live_snapshot.py:book_price`). Every *timing*
  result therefore describes a consensus series, not any bookmaker. Flag it here
  once; §5.4 measures what it costs and §7 states what it forecloses.
- Data availability: `analysis_core.csv` (committed), DATA_DICTIONARY.md,
  data_tour.ipynb, one-command regeneration.

## 4. Methods
- Scoring: Brier + log score; Murphy decomposition; CORP; Murphy diagrams
  with sup-t bands. De-vig: multiplicative default, Shin for tail-sensitive
  claims (tail artifact documented).
- Inference: date-clustered DM; TOST at δ=1.0e-3 Brier (admits a systematic 3.16pt offset; ΔBrier=ε²), reported against the cost-anchored ladder δ=0.11/0.44/0.99e-3 at prices 0.25/0.50/0.75;
  interval-randomized tie-consistent PIT; exact binomials for tail buckets;
  cluster bootstrap for niche ECE/slope; BH-FDR two-family policy.
- **Instrument checks on the benchmark** (added 2026-09-16, both in §5 with
  their logs). (a) *Freshness arms*: re-run the headline DM/TOST inside the
  bimodal quote-age split, plus a fresh-dummy interaction on the squared-error
  differential that tests directly whether the differential moves with
  staleness. (b) *Constant-membership panel*: re-detect the book-move events on
  steps where the consensus kept the same number of books, with eligibility
  applied at detection rather than as a post-hoc subset, so non-overlap pruning
  runs over a population a detector actually produces. Both report MDEs.
- Power: MDE table for every subgroup equivalence [power.log]. Pooled MDE
  0.36-0.51e-3 vs delta=1e-3 (powered); MLB/NBA/NHL individually powered
  (0.58/0.95/0.64e-3); CFB 2.74, WNBA 2.47, NFL 1.57 are NOT — reported as
  consistent-but-unable-to-detect, with the n multiple each would need
  (7.5x / 6.1x / 2.5x). Stated reading rule: quote MDE beside every subgroup
  null.

## 5. Results

### 5.1 The headline: a formal dead heat, at every level of scrutiny
**Fig 1: `plain_calibration.png`** (teams priced at X% win X% of the time,
1% resolution). **Fig 2: `equivalence_forest.png`** (all pairwise dBrier
with 90% CIs inside ±1e-3). **Table 1**: plain calibration deciles.
- Briers 0.2196 / 0.2199 / 0.2196 (K/P/B), slopes 0.96-1.01, ECE
  0.009-0.014 [three_way.log]. All clustered DM n.s.; TOST-equivalent,
  CIs within ±0.53e-3 [rigor.log].
- Four-way: Polymarket US equivalent to each (δ_min ≤ 0.74e-3); law of one
  price across legally segregated pools, median gap 0.50pt [four_way.log].
  Reads as arbitrage-elimination only — US and Global are one operator, so the
  pair cannot separate shared information from shared quoting. The
  unaffiliated-firm version (Kalshi vs Polymarket, median 0.40pt) carries the
  mechanism claim.
- Vs Pinnacle: all CIs within ±0.34e-3 [sharp_books.log]. Vs each of 11 US
  books: dead heat book-by-book, all n.s. [us_books.log].
- **At matched freshness** (new 2026-09-16, [book_freshness.log]). The design's
  one timing asymmetry — book quotes up to an hour old, exchange prices at T-0 —
  is measured rather than conceded. Collection cadence made quote age bimodal
  (56% of games under 10 min, 31% over 30, almost nothing between), so the
  headline re-runs inside each arm. **Against Pinnacle quoted <10 min from start
  the gap is −0.004e-3 (z=−0.02, n=2,992, MDE 0.49e-3) — an exact tie at full
  power.** All twelve arm-by-arm rows are TOST-equivalent; the one underpowered
  cell is labelled. The staleness shift itself is +0.33..+0.41e-3 — the sign the
  caveat predicted — at z=0.14–1.30, i.e. directionally right and too small to
  detect. Say it that way; do not declare the caveat dead.
- **Exchanges price off current information** (same log): splitting each game's
  books at their own median timestamp, both exchanges sit closer to the fresher
  half (Kalshi −0.021pt t=−3.7; Poly −0.030pt t=−5.0, n=4,642). Proximity, NOT
  precedence — an exchange that leads with books catching up looks identical —
  and worth 6–9% of the fresh-stale price gap. It is the only per-book timing
  statement the banked data supports; see §7 for why lead-lag is not among them.
- Time stability: equivalence holds within every adequate quarter
  [time_stability.log].
- **Registered out-of-sample verification (2026-08-28/29)**: claims fixed in
  docs/registered-claims.md before the holdout was pulled; on 264 fresh
  games the exchange dead heat verified at full registered power
  (|ΔBrier|=0.04e-3, p=.879, MDE 0.81e-3 < δ), calibration slopes cover 1,
  the extras blind spot appeared to replicate (+19.6pt vs +20.2pt frozen) —
  **R6 withdrawn 2026-09-23 as a vacuous test: a constant forecaster would have
  confirmed it too, so it could not fail** (third annotation,
  registered-claims.md) — structural
  cost matched (−4.6% vs −4.5%), and the WNBA totals tilt failed to
  replicate (treated as noise). The three-way legs were not evaluable — the
  live feed's book leg stopped 2026-08-07 on credit exhaustion — and are
  reported as such [oos_verification.log].

### 5.2 The gambling scorecard (table)
Calibration ✓, no FLB (slopes ≈1) ✓, equal resolution ✓, coherent ladders
(98.0% monotone, 0.07% executable arb [corrected 2026-09-15: was
"97.3% monotone, 0.1% arb"; coherence.log gives 98.0% and 0.07%]) ✓, no behavioral fingerprints ✓, unexploitable
(all edge strategies ≤0) ✓, self-consistent across venues ✓.
Figs: `spread_coherence.png`, `profitability.png`.

### 5.3 When the equivalence forms
- T-24h: Poly-book already tied; Kalshi marginally behind (ΔBrier +0.517e-3,
  date-clustered z=+1.80, p=0.072 on the completed 84% sample, n=3,906)
  [corrected 2026-09-15: this line carried z=+1.86, p=.063 — the
  pre-2026-09-03 asserted value that the multiple_testing drift report lists
  as superseded ("was 0.063 / now 0.072"); horizon_equivalence.log gives
  ΔBrier=+0.517e-3 z=+1.80 p=0.072]. Drops at BH q=.05 and survives only at
  q=.10 [multiple_testing.log] — report as suggestive, not as a finding.
- Lockstep sharpening 24h→start (both exchanges, and the books:
  close-vs-24h p=.035 [corrected 2026-09-15: was p=.040;
  horizon_equivalence.log gives ΔBrier=−0.999e-3 z=−2.11 p=0.035]);
  convergence of cross-venue gaps 1.3pt→0.9pt (|K−Book| 1.27→1.04,
  |P−Book| 1.12→0.84, |K−P| 1.28→0.89).
- Day's move uninformative beyond close (close efficiency all n.s.).
Fig: `horizon_calibration.png`.

### 5.4 How prices form
- No venue leads at 15-min; the two EXCHANGES do not lead each other at 1-min
  (symmetric few-minute echo, z≈7 both directions; big repricings simultaneous)
  [minute_lead_lag.log]. Say "the exchanges" in the 1-min sentence: the minute
  panel is `k_mid`/`p_price` only, so the book's finest clock is 5 minutes.
- **Resolution ladder (5/10/15/30 min, same games): no cross-lag correlation
  sharpens as the clock sharpens, and nothing predicts the book at any grid —
  the no-leader result is not an artifact of a coarse clock** [five_min.log].
  The fine clock does surface a small book→exchange coefficient (K +0.047
  z=2.4, P +0.164 z=4.5) that is ZERO in the final 2h, lives in sub-0.5pt book
  moves, and for Poly is as strong from a 30-min-frozen quote: drift alignment
  away from game time, not news transmission. Reported with its cuts.
- Markouts flat across size; taker imbalance predicts nothing → discovery
  is maker-driven, information enters via quote revision [informed].
- Book-move event study: exchanges neither anticipate nor follow with a lag.
  On the refreshed 528-game panel the anticipation-direction share is 34%
  Kalshi (p=0.012) and 23% Polymarket (p<0.001), both significantly BELOW
  chance, and the sign is stable from a 1pt to a 3pt event cut
  [book_moves.log]. State the conclusion at the strength it supports: no
  transmission on any clock the panel resolves. It does NOT establish
  independent processing — a same-step function of the book would look
  identical here (see §7, mechanism).
- **Is the benchmark a clean instrument for timing?** (new 2026-09-16,
  [book_panel.log]). Every result above reads a cross-book MEAN, so the obvious
  attack is that averaging manufactured the null. Report the audit, not a
  reassurance: membership changes on 2.2% of 15-min steps but carries 54% of
  the consensus series' squared variation, and the ≥2pt event population is 7.4×
  enriched in it. Re-detecting events on a constant-membership panel moves the
  anticipation shares AWAY from chance (Kalshi 34%→26%, Poly 23%→21%) — the
  contamination was diluting the finding, so the published numbers understate.
  Both shares now sit in the FDR family and survive BH at q=0.05.
- **What cleaning the panel reveals** (report this; it is the one thing the
  pooled panel hid). On the constant-membership panel a book→Polymarket
  coefficient appears in the final 2h: +0.070 (z=+2.6, p=0.008; date-clustered
  p=0.012) against −0.004 in the pooled panel. Kalshi's term is +0.063 (z=+1.7,
  n.s.). Three cuts identify it as a resting quote catching up, not news: it
  lives in RESTING quotes (z=+5.5) not awake ones (z=+1.2), in sub-0.5pt drift
  not news-sized moves, and it does NOT sharpen at the 5-min clock (−0.008,
  z=−0.1) — the opposite of a fixed wall-clock lag's signature. Same diagnosis
  `five_min` reached for >2h, now reached independently inside 2h.
Figs: `minute_lead_lag.png`, `five_min.png`.

### 5.5 Where the surfaces crack: distributions
*(rewritten 2026-08-28, post ladder-convention correction b7a2428)*
- **The correction, stated as a result.** Kalshi settles MLB/WNBA spread
  rungs on integer lines ("wins by t-0.5 or more") vs NBA/NHL half-point
  lines ("wins by more than t"); the analysis had applied one rule
  everywhere, shifting MLB's implied margin CDF by a full run. Verified
  against Kalshi's own settlement field (99.87% league-specific vs 97.80%
  single-rule, n=25,146 contracts); enforced by
  `ladder_convention.cover_line()` + a per-league data_audit gate. Four
  claims retracted in place [multiple_testing.py header].
- **Post-correction surface: near-dead-heat on shapes too.** Every league's
  Kalshi margin PIT passes (pooled KS=0.0093 p=0.812; MLB KS=0.0282 p=0.087,
  n=1,962) [margin_dist.log] [corrected 2026-09-15: this prose carried
  pooled KS=0.011 p=0.718 / MLB p=0.104 — the hand-maintained values from
  the multiple_testing.py NULLS registry, not margin_dist.log; the locked
  table below was already right]. RPS head-to-head on shared rungs
  (n=3,670 [corrected 2026-09-15: was n=3,673]): books
  better by +0.48e-3 (z=+2.41) pooled [corrected 2026-09-15: was +0.49e-3,
  z=+2.44], carried by NBA (+1.14e-3, z=+2.27,
  its convention was always right); MLB n.s. (+0.33e-3, z=+1.29); NHL exact
  tie [multi_outcome.log]. Ladder price agreement corr 0.9887; tail ECE on
  identical contracts 0.0078 (K) vs 0.0072 (B) [ladder_vs_books.log]
  [corrected 2026-09-15: the book figure was 0.0073; the log prints
  Book ECE=0.0072]. The
  books' own denser ladders (pushes excluded) fail the PIT in MLB (p=0.000)
  and NHL (p=.032 [corrected 2026-09-15: was p=.024; book_pit.log gives
  KS=0.0402 p=0.032]) where Kalshi's sparser ones pass — test density/power,
  not book inferiority [book_pit.log].
- **RETRACTED 2026-09-23 — there is no surviving crack.** This bullet asserted
  a SHARED blind spot: extra-inning games under-pricing the 1-2-run cell by
  +20.2pt on Kalshi (z=+7.46, n=339) and +22.0pt at the books (+21.99pt,
  n=208), with regulation running the other way (-3.1pt K / -1.6pt B) so each
  aggregate cell cancelled. **Every one of those numbers reproduces and none of
  them identifies mispricing.** `extras` is realized DURING the game;
  conditioning a calibration test on an outcome-correlated state outside the
  forecaster's information set breaks the calibration identity mechanically, in
  both directions, whether or not anything is mispriced. The placebo is decisive
  [extras_conditioning.log §1]: a **constant at the unconditional base rate
  scores +21.19pt** on the same split and a pre-game-information-only forecast
  +21.23pt, against the market's +20.22pt. P(win by 1-2 | extras) − P(win by
  1-2) = +21.19pt *is* the published gap. Extras are near-unforeseeable ex ante
  besides (cross-fitted AUC 0.540, §2).
  The correct test — E[realized − implied | Z] = 0 for Z in the market's
  information set, Z = cross-fitted ex-ante extras propensity — reverses the
  sign [§3-§4]: coef −1.1495, **z=−3.00 date-clustered** (−2.89 game-clustered,
  −2.41 iid), a small OVER-pricing of the cell in extras-prone games, ~4pt
  across the propensity range. Post-hoc, flagged as such in the FDR inventory,
  and to be written at that strength only.
  **Consequence for the movement:** the shared-blind-spot column loses its
  within-game member and now holds only the WC draws and the 40/60 compression.
  §5.9's boundary argument is unaffected — outrights and un-benchmarked niche
  games never conditioned on a realized state — but §5C can no longer claim a
  within-game miniature of it, and the drafting beat built on that parallel has
  to go. This is the project's fourth self-caught error and the SECOND on this
  same cell (cf. the 2026-08-23 ladder-convention retraction).
- **Totals layer, retargeted** [totals.log]: totals settle uniformly
  (verified — no convention adjustment), and now serve as the dense
  companion surface: PIT passes MLB (KS=0.0202 p=0.396, n=1,969), NBA
  (KS=0.0180 p=0.793, n=1,284), NHL (KS=0.0300 p=0.218, n=1,222), WNBA
  (KS=0.0619 p=0.207, n=290) [corrected 2026-09-15: this line read
  "MLB (p=.90), NBA (p=.86), NHL (p=.25)" — a PRE-FREEZE vintage carried in
  the multiple_testing.py NULLS string, which pairs p=0.90 with n=1,466 MLB
  ladders; the freeze grew that sample to 1,969, the same growth documented
  for WNBA (234->290). All four leagues still pass; the p-values are ordinary
  rather than resounding];
  contract ECE 0.0046 (MLB), no right-tail bias (all |z|<=1.01). The
  totals-pass/margins-reject contrast this layer was collected to test is
  retracted — both layers pass, which upgrades the conclusion: the whole
  run-scoring process is priced correctly [corrected 2026-09-23: this read
  "priced correctly outside the extras cell"; after the conditioning
  retraction there is no excepted cell — on pre-game information the extras
  cell is not under-priced either]. WNBA
  totals: RESOLVED as a false alarm, twice over. The 2026-08-11 rejection
  (p=.0076, n=234) DISSOLVED as the frozen sample grew (KS 0.062, p=0.21,
  n=290) and FLIPPED SIGN on the registered holdout (mean u 0.404, z=−2.3,
  n=47) [totals.log, oos_verification.log]. Retired from the FDR inventory
  with the retraction record; report it as the machinery working. Coherence splits by price source: live-book
  totals ladders 99.5-100% monotone in every league (MLB 99.5%, NBA/NHL/WNBA
  100.0%) vs trade-recon 86.1-96.0% [totals.log] [corrected 2026-09-15: was
  "99.3-100%" and "raw 86.9-95.6%", neither of which appears in totals.log;
  99.3% is WNBA's ALL-source row]; violations are reconstruction noise.
- **Self-correction, corrected** [time_stability.log §2, migrated
  2026-08-28]: the previously reported "+7.5 to +11.2pt non-correcting
  bias" was the artifact persisting (an artifact cannot self-correct).
  Corrected, the aggregate cell is near-unbiased in every era. The era-split
  extras figures that stood here (+18.3pt / +26.4pt, n=156/56 sides) are
  withdrawn with the parent claim on 2026-09-23 — they are the same
  conditioned-on-the-future statistic cut finer, so they measure the
  extras/margin dependence within each half, not a bias that failed to
  self-correct.
Figs: `margin_distribution.png`, `margin_pit.png`, `totals.png` now show
agreement/passes — appendix gallery; §5C's main-text figure load is the
discipline boundary (F6). The extras cell was to be "carried in prose"; after
the 2026-09-23 retraction the prose it needs is the retraction itself plus the
sign-reversed pre-game result, and the placebo table (extras_conditioning §1)
is the natural small exhibit if §5C wants one.

### 5.6 What participation costs, and who pays
- Cost table: taker all-in Kalshi ≈ -4.2% ≈ books' vig -4.1%; maker path
  ≈ free (a route books do not offer); Poly takers ~1-1.75%.
- Realized taker P&L to settlement: -5.0% gross / -7.7% net on $95.7M; every
  size class loses; retail fingerprint (53% of fills in final 3h, evening
  leisure concentration, median stake $14) [retail_fingerprint.log].
- Fee natural experiment: accuracy invariant; incidence on volume (-41%)
  with the touch pinned at 1c [fee_liquidity.log]. Tick design: the touch
  IS the tick; Kalshi's uniform 1c makes tails ~10x costlier than Poly's
  0.001 regime [tick_pricing.log].
- **The price of immediacy** [immediacy.log]: the touch numbers above are the
  whole retail story, and here is why — a 30-unit order (the tape's median)
  sits inside the touch in 89% (K) / 95% (P) of book snapshots, and median
  cost stays at half the tick (0.50c, ~0.9% of notional) up to 10,000 units.
  What runs out is capacity, not price: fill-inside-5c drops to 61/44/36% (K)
  and 96/67/21% (P) at 10K/50K/200K units. The venues invert into the event —
  Poly is deeper a day out, Kalshi ~5x deeper inside 30 min; measured
  within-game the ramp is 2.29x (K) vs 1.58x (P). Touch asymmetry replicates
  the two-layer book (a <=10-unit order is the best quote 22.4% of the time on
  Kalshi vs 1.9% on Poly).
Figs: `retail_fingerprint.png`, `fee_liquidity.png`, `tick_pricing.png`,
`immediacy.png`.

### 5.7 Who supplies the market (the affiliated-dealer question)
- Documentary: Kalshi Trading on the exchange since 2021; CFTC bona fide MM
  proposal (2026-07-30); incentive program excludes affiliate + MM firms
  (separate agreements). No public market-level roster; member IDs private.
- The two-layer book: retail-sized touch (20% of snapshots ≤10 contracts on
  a side) over ~20K contracts/side within 5c across ~90 games — professional
  structure [maker_structure.log].
- The footprint: games $817K/5c at 1c spreads; niche $6K; 74% of the
  outright tail unquoted; the fee menu prices the same gradient (makers PAY
  on covered games, free where supply needs coaxing) [liquidity_footprint.log].
- The class-action prediction tested: takers do NO BETTER where the house's
  book is absent (-5.0%/-7.7% vs -7.1%/-10.0%, n.s.) — the house's absence
  mostly means no market [mm_involvement.log].
- Market functioning on shared niche matches (287): books 55-85% present at
  7.1% vig; Polymarket $203K/match (its clientele) at 1.5pt from the book
  line; Kalshi prices 14% of its own listings at 4.2pt — vs 0.7pt where its
  complex stands [market_functioning.log].
- Synthesis: the MM complex governs whether a market exists and how precise
  it is; it does not worsen what takers pay; the exchange/house line is
  about whether the liquidity supplier may hold a directional book.

### 5.8 The market premium over public statistics
- Walk-forward Elo: markets beat it by ~13.3e-3 Brier (z≈7.4) while
  differing from each other by ≤0.5e-3 [model_benchmark.log]. "Equally
  good, and equally better than public statistics."
Fig: `model_benchmark.png`.

### 5.9 The boundary of discipline: repetition, not institution
**Lead this section with the horizon collision (see §2.1).** A quarter of Gen Z
investors report treating sports betting as part of a long-term financial
strategy. The market type a "strategy" horizon implies is precisely the one
this section shows failing at every institution: one-shot, long-horizon
outrights return $0.33/$1 (Kalshi) and $0.34/$1 (the books) on sub-10c
longshots, while the repeated, fast-resolving game markets return ~$1.00 at
mid. The discipline documented in this paper does not extend to the horizon on
which people say they are using these products. That is the single most
policy-relevant sentence the data supports.
**Fig 3: `oneshot_returns.png`** (sub-10c $1 returns: ladders $1.22 vs
outrights $0.33 / $0.53 / $0.34). **Fig 4: `niche_gradient.png`**.
- BDW's platform pathologies vanish in game markets (moneylines at mid
  -0.45%) [why_sports.log].
- They return in one-shot outrights AT EVERY INSTITUTION: Kalshi $0.33
  (fresh prints: 0 winners in 114, $0.00), Polymarket $0.53, the BOOKS
  $0.34 at 0-3 months (se 0.08, n=1,614, 20 sport-seasons 2020-26
  playoff-densified, Shin-robust — statistically identical to the exchange)
  [futures_calibration.log, book_outrights.log]. Both-tail overconfidence
  on the exchange (75c+ favorites won 62.5% vs 86.3% priced); book
  overrounds 1.20-1.27 vs exchange 1.03.
- And they DON'T appear in un-benchmarked repeated games: niche tier excess
  ECE 0.00 vs noise floor, slope 0.98 (CI 0.84-1.15), field sums 1.02
  [niche_gradient.log]. The benchmark is not load-bearing; repetition and
  fast resolution are. Liquidity isn't either: deep outright books
  misprice, tiny niche books don't (5.7's footprint closes the confounder).
- Precision vs bias decomposition: repetition → unbiased; MM complex →
  existence + precision (0.7pt vs 4.2pt from consensus).

### 5.10 Case study: the World Cup 3-way (descriptive, n=9 matches) and the
draw priced within 0.3pt across venues.

### 5.11 Horizon-matched translation: the answer to the demand-side surveys
**Fig: `horizon_translation.png`** [horizon_translation.log]. §2.1's respondents
describe a HORIZON (long-term wealth); this paper measures per-position returns.
The bridge is one line: per-position rate x re-stake frequency.
- Rates, recomputed not quoted. STRUCTURAL taker cost -4.5% per position
  (half-spread + fee over notional, n=47,766 live quotes, IQR -5.4 to -4.0) —
  this is the anchor because it is fixed by the quote and fee schedule before
  any ball is thrown. REALIZED taker P&L -5.0% gross / -7.7% net agrees, but
  its game-clustered 90% CI (-19.5% to +2.9%) spans zero: outcomes are noisy,
  the cost is not. The two agreeing to within a couple of points IS the finding.
- Cadence is a SCENARIO GRID, explicitly not a measurement — the public tape has
  no account identifiers, so no outsider can observe per-person frequency.
- Bankroll left after a 26-week season, re-staking: monthly 76%, fortnightly
  55%, weekly 30%, twice-weekly 9%, daily ~0%.
- **The horizon-matched line**: one futures ticket held from a week out returns
  -43.7% ($0.56/$1, matching futures_calibration). Reaching the same place
  through the well-priced game markets takes 12.4 positions — so ~12 game bets
  equals buying the one product this paper shows is badly priced at EVERY
  institution, and a weekly bettor gets there 48% of the way through a season.
- **What it adds beyond the calibration results**: every accuracy result in the
  paper is about the PRICE, and none of it reaches the customer. A market that
  is TOST-equivalent to Pinnacle, coherent and arbitrage-free still returns
  close to nothing to a taker at any cadence a "financial plan" implies.
  **Calibration disciplines the price; it does not protect the participant.**
  That is the institutional finding in the units the surveys use.
- Framing discipline: descriptive comparison of measured returns, no
  recommendation; the equity yardstick is a fixed textbook constant, not an
  estimate from this project.

## 6. Institutional synthesis
For a market-order retail bettor, the exchange's sports section functions
as a sportsbook: same prices, same realized cost, same sheltered biases,
sportsbook-shaped clientele, and a professional dealer complex on the other
side. In aggregate it is a forecasting instrument: formally equivalent to
the sharpest professional prices, coherent, maker-disciplined, and honest
about its own uncertainty. The difference that survives every test is
design, not accuracy — who may hold a directional book, what the tick and
fee schedule charge for the tails, and where the liquidity complex chooses
to stand. Discipline comes from repetition and feedback; nothing about
"prediction markets" or "sportsbooks" as institutions manufactures it.

## 7. Limitations
**No demographic data.** The Betterment/Northwestern Mutual framing in §2.1 is
motivation, NOT identification: Kalshi's public fill tape carries no age,
location, or account attributes, so this paper cannot and does not claim its
traders are Gen Z. What it can say is what the product costs and returns to
whoever is using it, and what the usage pattern looks like (median $14 stake,
53% of fills in the final 3h, evening-leisure concentration) — consumption-
shaped, whoever is doing it. Any generational claim would need account-level
data no outside researcher has.
**Product scope: the pre-game moneyline only.** This is the largest scope
decision in the paper and it deserves its own paragraph rather than a clause.
Every comparison here is a straight pre-game win/loss price. No parlays, no
same-game parlays, no player props, no in-play or live pricing. The
justification is real — a like-for-like comparison needs a contract both
institutions list, and the moneyline is that contract — but the consequence
cuts two ways and the paper should own both. The moneyline is the
sportsbook's most efficient, lowest-hold, most heavily arbitraged product,
close to a loss-leader; the industry's economics, and the products most
implicated in the harm literature, are parlays and props, where hold runs
several times higher and no exchange analogue exists. So this design compares
the venues where the book looks *most* like a forecaster, and it says nothing
about the products where most of the money and most of the concern actually
sit. A reader is entitled to note that "the exchange forecasts as well as the
sportsbook" is established on one product line and not on the institution's
whole book of business. In-play pricing — arguably where the gambling/
forecasting distinction is sharpest — is excluded by design, since every price
here is anchored at the official start and nothing after it is used.

**The benchmark is a cross-book mean, and for TIMING that is a real limit.**
Every accuracy comparison in this paper is unpacked per book — against Pinnacle
specifically (n=5,284) and book-by-book across 11 US retail brands, with the
equivalence holding in each. Every *timing* comparison is not, and cannot be:
the live collector averaged the field at ingest and kept no per-book quotes, so
"the sportsbook" in every lead–lag result is a consensus series. Two
consequences, and the paper should state both rather than the reassuring one.
(1) **A question this design cannot answer at all.** Whether the sharp book
leads the retail field, and whether an exchange sits on Pinnacle's line or the
field's, is not identified by anything banked here, at any resolution. The
per-book tapes that exist are closing cross-sections (~8–12 timestamps per
game), not series. (2) **A question it can answer, and does.** Whether the
averaging manufactured the no-leader null is testable on the banked panel and
was tested (`book_panel.py`): membership churn is 2.2% of 15-min steps but
carries 54% of the consensus series' variance and enriches the ≥2pt event
population 7.4×, yet re-detecting the events on a constant-membership panel
moves the anticipation shares *away* from chance rather than toward it. The
nulls are not an averaging artifact. What the cleaning does reveal is a small
book→Polymarket coefficient in the final 2h (+0.070, z=+2.6) invisible in the
pooled panel, which three cuts identify as a resting quote catching up to a
drifting consensus rather than news transmission — it lives in frozen quotes
and sub-half-point drift, and it does not sharpen at the finer clock. The
collector now retains per-book quotes (`data/live/book_quotes.csv`, zero
marginal credit cost, same API response), so the first question is answerable
by a future panel but not by this one.

**Mechanism is underdetermined, and no outside researcher can fix it.** The
lead–lag nulls rule out slow transmission between venues, not transmission:
a maker quoting one venue continuously off another's line produces no lead at
any resolution. 99.5% of Kalshi's log-odds variation and 98.7% of
Polymarket's is explained by the book consensus, and only Kalshi's residual
carries detectable information (p=0.035, fragile). That does not show copying
— two independent accurate forecasters of the same games would also be ~0.99
correlated — but it does mean this design cannot separate the two readings in
benchmarked markets. What it can show is that exchanges price *un*-benchmarked
niche markets just as well, so they do not require a professional line. The
missing datum is maker identity: whether the same firms quote both exchanges
is not in any public tape, and settling it would need venue cooperation.

**No demographic data** — see above.

Sports scope (but see §2.1: ~95% of prediction-market volume is sports, so this
is the main case rather than a narrow one); consensus timing (60-min buckets vs
exchange T-0 — **measured, not just documented, as of 2026-09-16**: quote age is
bimodal, and against Pinnacle quoted <10 min from start ΔBrier is −0.004e-3 at
MDE 0.49e-3, an exact tie at full power; the staleness shift is +0.33..+0.41e-3,
the sign the caveat predicted, and not significant — book_freshness.log); **the three-venue requirement re-weights the sample** (CBB-M falls
from 10.2% of the Kalshi-priced clean set to 0% of the headline set, MLB from
41% to 23%; the pooled dead heat is unchanged under league-equal weighting —
robustness_cuts §6); Kalshi 60-day decay (harvest protocol); trade-recon
staleness (caps, plus external validation against archived order books —
validate_recon); small-league power (MDE table); niche name-matching
lower bounds; Poly resolved-market candle coarseness; US per-book covers 86% of the joint set
(floor-stopped); outright inference = 20 season-clusters; 15-min panel
era-limited; informal pre-registration, discharged — claims were registered in
`docs/registered-claims.md` before the holdout was pulled and the scorecard is
reported whichever way it read (R2 confirmed at full registered power; R7
deviated and the open observation was retired as noise).

**On the direction of our own corrections.** Eleven claims have been retracted,
downgraded, or resolved as false alarms. A reader is right to ask whether they
all conveniently moved toward the paper's thesis. They did not: four removed a
*"Kalshi has a defect"* claim (the ladder-convention set, the WNBA totals false
alarm) and four removed a *"Kalshi is better"* claim (the NBA encompassing
sub-claim, wide-set K>P, log-score K>book, and the Murphy sup-t edge). The
corrections ran both ways and roughly evenly. What is true of nearly all of
them is that they moved *toward the null* — which is what one would see if the
null were true, and also what one would see from a pipeline whose cleaning
shrinks extreme estimates. The registered out-of-sample verification is the
answer to that second reading: the dead heat replicated on games collected
after the claims were fixed, at full registered power.

## 8. Reproducibility and data
One-command regeneration (65 modules, audit-gated); committed core table +
dictionary + tour notebook; free-API re-derivability for exchange data;
book data banked (subscription lapses Sept 2026); VPS backups.

## Appendices
A. Side-assignment audit. B. Robustness battery (log score, home-side,
CORP, selection, de-vig variants, quote quality) **plus the 2026-09-03 cuts:
favourite strength, Kalshi price construction, four book-consensus
constructions, exclusion sensitivity, six clustering levels, ECE bin
sensitivity, logit-clip sensitivity**. C. FDR table: 15 discovery claims,
13 survive BH q=.05 (books-lead-24h and the Murphy sup-t edge drop; the
latter retracted), 14 at q=.10; p-values re-derived from the logs at run
time and the retraction record stays in the module header. One claim
(futures pooled longshot p) is held out of the family as unsourced.
D. Equivalence/null register (17 entries). E. Data dictionary.

---

## Numbers locked at the freeze — 2026-08-29 (single source of truth)
*Regenerated from the freeze suite (2026-08-29, 59 modules); re-stamped 2026-09-03
at 61 and 2026-09-16 at 63, 0 failures throughout, every prior number reproducing
unchanged (results/MANIFEST.md).
Every §5 prose number must be read from this table or the named log; the
2026-08-06/08-10 tables this replaces are superseded in full.*

> **Reconciliation note — 2026-09-15.** This table was audited line-by-line
> against `results/logs/`. It held up everywhere it was checked except the FDR
> row (corrected above). The §5 **prose**, however, did not: §5.2 and §5.3
> carried margin-PIT, RPS, extras-z, tail-ECE, book-PIT and T−24h figures that
> disagree with the named logs, in every case matching the hand-maintained
> strings in `multiple_testing.py`'s docstring and `NULLS` list rather than the
> logs those sections cite. Those are corrected in place and marked. The rule
> this table states — *read from this table or the named log* — was the thing
> that had lapsed, not the table. Where the two still disagree, the log wins:
> this table is a transcription, and `results/logs/` is the source of truth.

| Claim | Number | Log |
|---|---|---|
| Three-way Briers | 0.2196 / 0.2198 / 0.2196 (n=5,333) | three_way |
| TOST pooled | all 90% CIs within ±0.52e-3; K-B ±0.22e-3 passes the mid-price anchor | rigor |
| vs Pinnacle | all CIs within ±0.33e-3 (n=5,284) | sharp_books |
| US book-by-book | 11 books, 4,655 games, all n.s. | us_books |
| Four-way | δ_min ≤ 0.74e-3; US-Global median gap 0.50pt | four_way |
| Elo premium | +13.1e-3, z≈+7.3 (n=4,887) | model_benchmark |
| Shared deviations | calibration-deviation corr K-P +0.99, K-B +0.93, P-B +0.91 | plain_calibration |
| Season split | regular season EQUIV@1e-3 (δ_min 0.51e-3, n=5,094); postseason consistent, MDE 3.23e-3 (n=228) | referee §4b |
| RPS post convention fix | pooled +0.48e-3 (z=+2.41), NBA-carried +1.14e-3 (z=+2.27); MLB n.s. | multi_outcome |
| Extras 1-2-run cell | **RETRACTED 2026-09-23** — figures reproduce (K +20.2pt z=+7.5 n=339; books +22.0pt; aggregates n.s.) but the split conditions on a state realized mid-game: a constant scores +21.19pt. Replacement, pre-game Z: coef −1.1495, z=−3.00 date-clustered (small OVER-pricing) | extras_conditioning, mlb_extras |
| Margin + totals PIT | margins pooled p=0.81 (MLB p=0.087, n=1,962); totals pass ALL FOUR leagues (WNBA p=0.21, n=290) | margin_dist, totals |
| Taker P&L | -5.0% gross / -7.7% net on $95.7M (game-clustered CI spans zero) | retail_fingerprint |
| Outright longshots | K $0.33 / P $0.53 / B $0.34 (se .08, 20 seasons; books $0.52 under Shin) | futures_calibration, book_outrights |
| Niche gradient | excess ECE 0.00 vs noise floor, slope 0.98 | niche_gradient |
| Footprint | $817K vs $6K vs $235K per market; 74% of outright tail unquoted | liquidity_footprint |
| Functioning | 0.7pt vs 4.2pt from consensus; books ~7% niche vig vs ~4% covered | market_functioning |
| Shading | 30+ books, sub-1pt, sign mostly opposite | sharp_books, us_books |
| Fee incidence | volume -41% at the fee date, touch pinned at 1c | fee_liquidity |
| Resolution ladder | no lead sharpens 30→5 min; nothing predicts the book at any grid | five_min |
| 5-min book→exchange | K +0.047 (z=+2.4) / P +0.164 (z=+4.5); ZERO in final 2h | five_min |
| Immediacy at retail size | 30-unit order inside the touch 92.4% (K) / 95.0% (P); median cost 0.50c ≈ 1% of notional to 10K units | immediacy |
| Capacity at 200K units | fills inside 5c: 38% (K) / 22% (P) | immediacy |
| Within-game depth ramp | 2.14x (K) vs 1.58x (P) | immediacy |
| Pooled MDE | 0.36-0.51e-3 vs δ=1e-3 (powered) | power |
| Underpowered leagues | CFB 2.74, WNBA 2.45, NFL 1.57 (e-3), with n-multiples needed | power |
| FDR | **19 claims, 17 keep at q=.05, 18 at q=.10** (Murphy sup-t drops at both); WNBA totals claim retired | multiple_testing | <!-- updated 2026-09-16: family grew 15->19. book_panel added the two anticipation-share claims (never registered before) and the cleaned-panel book->Poly term; book_freshness added the fresh-book proximity term. All four KEEP at q=.05. --> <!-- corrected 2026-09-15: row read "16 claims, 13 keep at q=.05 (all 16 at q=.10)"; multiple_testing.log prints a 15-claim family, 13 KEEP at q=0.05 and 14 KEEP at q=0.10 -->
| Structural taker cost | -4.6%/position (IQR -5.5 to -4.0, n=95,654 quotes) | horizon_translation |
| Bankroll, weekly re-stake, one season | 29.5% | horizon_translation |
| Game bets equal to one futures ticket | 12.2 | horizon_translation |
| Master | 10,118 games / 7 leagues; three-way clean n=5,333 | build_master, three_way |
| Registered holdout | R2 dead heat \|ΔB\|=0.04e-3 at MDE 0.81e-3 (POWERED); cost -4.6%; WNBA tilt sign-flipped; R1/R5 not evaluable (book feed ended 08-07); **R6 extras +19.6pt WITHDRAWN 2026-09-23 as vacuous** | oos_verification, registered-claims.md |
| Quote-age split | bimodal: 56% of games <10 min, 31% >30 min, 618 between (n=4,655) | book_freshness |
| Dead heat at MATCHED freshness | K vs Pinnacle quoted <10 min: −0.004e-3 (z=−0.02, n=2,992, MDE 0.49e-3); all 12 arm rows TOST-equiv, one cell flagged underpowered | book_freshness |
| Staleness shift | +0.06..+0.41e-3 (z=0.14–1.30), the sign the caveat predicts, n.s. | book_freshness |
| Exchanges vs freshest books | K −0.021pt (t=−3.7), P −0.030pt (t=−5.0), n=4,642; 6–9% of the fresh-stale gap. Proximity, not precedence | book_freshness |
| Book-panel churn | membership changes on 2.2% of 15-min steps but carries 54.3% of the consensus series' squared variation; ≥2pt events 7.4× enriched | book_panel |
| No-leader nulls, clean panel | anticipation share moves AWAY from chance: K 34%→26%, P 23%→21% (whole ±1h window constant, n=43) | book_panel |
| Cleaned-panel book→Poly, final 2h | +0.070 (z=+2.6, p=0.008); resting-quote catch-up, not transmission (RESTING z=+5.5 vs AWAKE z=+1.2; absent at 5-min) | book_panel |

## Open items before the final draft
1. Advisor: venue (grant report vs arXiv) and turnaround — memo pending.
   Non-blocking per drafting-plan Decision B.
2. ~~Claim registration + out-of-sample verification~~ — EXECUTED 2026-08-28
   (docs/registered-claims.md committed before the holdout was collected;
   oos_verification.py; §5A closing paragraph slot per drafting plan).
3. ~~5-min book event study + price-of-immediacy curve~~ — DONE 2026-08-10
   (five_min.py, immediacy.py; §5.4 and §5.6 above).
4. ~~MDE table~~ — DONE 2026-08-10 (power.py; §4 above).
5. ~~Number freeze~~ — RUN 2026-08-28 after the final VPS panel refresh and
   re-harvest; MANIFEST + logs stamp every figure/table.
6. ~~Kalshi price re-harvest~~ — RUN 2026-08-28 with the freeze.
7. ~~Benchmark-instrument audit~~ — DONE 2026-09-16 (`book_panel.py`,
   `book_freshness.py`; suite re-stamped at 63 modules, 0 failures, every prior
   number reproducing). Closes the two questions a referee reaches for first:
   whether pooling books manufactured the no-leader null (it did not — cleaning
   moves the anticipation shares *away* from chance) and whether a stale book
   quote manufactured the dead heat (it did not — an exact tie against Pinnacle
   inside 10 minutes, at full power). Slots written into §3, §4, §5.1, §5.4, §7
   and the locked-numbers table. The one question that remains genuinely
   unanswerable — does the sharp book lead the retail field — is stated as a
   limitation, and the collector now banks per-book quotes so a future panel
   could settle it.
