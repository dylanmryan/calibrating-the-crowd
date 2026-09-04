# Drafting plan — Calibrating the Crowd
*Created 2026-08-20. Turns `report-outline.md` (evidence catalogue) into a
paragraph-level writing spec. Numbers are NOT re-verified here — the locked
table in `report-outline.md:354` remains the single source of truth, and
nothing in this file supersedes it. Freeze has not run; every number cited in
prose gets re-stamped at freeze.*

---

## 0. Two decisions this plan makes (reject either and the rest still holds)

**Decision A — Structure §5 as four movements, not eleven subsections.**
The outline's §5.1–5.11 is the order the evidence was *collected*, not the
order it should be *read*. Eleven peer-level results sections is a catalogue;
a reader cannot hold the arc. This plan regroups them into four movements with
an argumentative spine:

| Movement | Question it answers | Absorbs |
|---|---|---|
| A. The dead heat | Are they equally good? | 5.1, 5.2, 5.8 |
| B. How the equivalence is produced | Why are they equally good? | 5.3, 5.4 |
| C. Where the surface cracks | Where does it stop being true? | 5.5, 5.9 |
| D. What it costs, and who is on the other side | What does it mean for a user? | 5.6, 5.7, 5.11 |

Nothing is dropped. §5.10 (World Cup 3-way, n=9, descriptive) moves to
Appendix F — at n=9 it cannot carry a numbered results section, and it
interrupts C→D at exactly the wrong moment.

Movement C is the pivotal regrouping — rebuilt 2026-08-28 after the
ladder-convention retraction (b7a2428). The shared extra-innings blind spot
(5.5: the 1-2-run cell missed by ~+20pt at BOTH venues) and the one-shot
outright failure (5.9) are the same finding at two scales: **discipline is a
property of the market's repetition structure, not of the institution.**
Extras are a rare state inside a repeated market (8.6% of games — thin
feedback); one-shot outrights are a market type with no repetition at all;
both are mispriced everywhere, by the same amount at every institution. Put
them adjacent and the paper has a thesis instead of two anomalies — and the
retraction strengthened it: the one finding that looked Kalshi-specific
turned out to be institution-independent once the settlement convention was
read correctly.

**Decision B — Target ~11,000 words main text, ~9 main figures, 5 main tables.**
Format-agnostic: this is a paper that reads as a grant report with a cover
page, or as an arXiv preprint unchanged. Writing to the tighter of the two
targets costs nothing and removes the advisor question from the critical path.

---

## 1. Front matter

**Title (keep):** Calibrating the Crowd: Prediction Markets and Sportsbooks as
Rival Forecasters of the Same Games

**Subtitle candidate, if a subtitle is wanted:** *Calibration disciplines the
price, not the participant.* This is the paper's most quotable line and its
actual contribution. Recommend holding it for the §5 Movement D punchline and
the abstract's last sentence rather than the title — used twice it lands, used
three times it wears.

**Abstract (~220 words, WRITE LAST).** Six sentences, one job each:
1. Setup: same games, four institutionally distinct pricing mechanisms.
2. Design: n games, leagues, window, books benchmark including the sharp price.
3. Headline: formal equivalence (TOST), not merely absence of significance.
4. Mechanism: no venue leads at any resolution; maker-driven discovery.
5. Boundary: fails identically at every institution where repetition is absent.
6. Institutional finding: equivalent prices, unchanged participant cost.

**Keywords:** prediction markets; forecast calibration; sports betting;
market microstructure; equivalence testing.

**JEL:** G14 (information and market efficiency), G41 (behavioral finance),
D84 (expectations), L83 (sports/gambling).

---

## 2. Word and figure budget

| Section | Words | Figures | Tables |
|---|---|---|---|
| Abstract | 220 | — | — |
| 1. Introduction | 1,100 | Fig 1 | — |
| 2. Background and related work | 1,400 | — | — |
| 3. Data and pipeline | 900 | — | Table 1 |
| 4. Methods | 900 | — | Table 2 |
| 5A. The dead heat | 1,200 | Fig 2 | Table 3 |
| 5B. How the equivalence is produced | 900 | Fig 3, Fig 4 | — |
| 5C. Where the surface cracks | 1,400 | Fig 6 | Table 4 |
| 5D. What it costs, and who is on the other side | 1,300 | Fig 7, Fig 8 | Table 5 |
| 6. Institutional synthesis | 700 | — | — |
| 7. Limitations | 600 | — | — |
| 8. Reproducibility and data | 250 | — | — |
| **Total** | **~10,870** | **8 + Fig 9 in 5D** | **5** |

### Main figures — the report figure program (results/report/, built by
`src/analysis/report_visuals.py`; see docs/figure-map.md for design notes).
This supersedes the old 9-of-29 selection from results/*.png — those plots
remain as the appendix gallery's raw layer.

| Slot | File | Section | Carries |
|---|---|---|---|
| Fig 1 | `F2_dead_heat` | §1 hook | Teams priced at X% win X% of the time, all venues |
| Fig 2 | `F3_equivalence_forest` | §5A | Every pairwise ΔBrier CI against the cost-anchored margin ladder |
| Fig 3 | `F5_market_premium` | §5A | Markets beat the public-statistics floor — identically |
| Fig 4 | `F10_when_equivalence_forms` | §5B | T-24h → close: lockstep sharpening, no separation |
| Fig 5 | `F4_no_leader` | §5B | No cross-lag correlation sharpens with the clock |
| Fig 6 | `F6_discipline_boundary` | §5C | Repeated vs one-shot: what fails is the market type |
| Fig 7 | `F8_retail_fingerprint` | §5D | The flow is shaped like consumption |
| Fig 8 | `F7_translation` | §5D | Bankroll decay by cadence: price vs participant |
| Fig 9 | `F1_two_axes` | §6 | Price quality and participant cost are independent |

§1 opener (BUILT 2026-08-28): `F0_one_game` — one game, every venue; the
BUF-MIA exhibit's three-day book/Polymarket record plus the final-30-minute
Kalshi tape, closing 0.5pt apart.

**Pair picks (decided 2026-08-28; alternates go to the appendix gallery):**
F1 over F1alt (the venue-coincidence proof beats stat tiles); F2 over F2alt
(the 45° hook; F2alt's 10x deviation view is the appendix companion to the
shared-deviation statistic); F3 over F3alt (D2 requires reporting where the
margin ladder stops resolving); F6 over F6alt (sparse futures buckets invite
over-reading); F7 over F7alt (the structural rate is the anchor; the
two-rate bracket is appendix nuance).

Appendix gallery: F9_institutional_trace, F11_maker_taker,
F12_two_layer_book, F13_scorecard, F14_immediacy, the five alternates, and
the full results/*.png suite layer (their numbers still appear in prose and
tables — only the plots sit in the appendix).

### Main tables
- **Table 1** Data sources: venue, instrument, price construction, coverage, n.
- **Table 2** Power/MDE by subgroup, with the stated reading rule.
- **Table 3** Headline equivalence: Brier, slope, ECE, pairwise Δ with TOST CIs.
- **Table 4** The 2×2 of discipline: {repeated, one-shot} × {benchmarked, not}.
- **Table 5** Cost accounting: structural taker cost, realized P&L, book vig.

**Table 4 is a new object and the paper's centerpiece.** It does not exist yet
as a rendered table; the numbers all do. Cells:

|  | Benchmarked (books present) | Un-benchmarked (niche) |
|---|---|---|
| **Repeated, fast-resolving** | Game markets: dead heat, ECE ~0.01 | Niche tier: excess ECE 0.00, slope 0.98 |
| **One-shot, long-horizon** | Outrights: K $0.33 / B $0.34 per $1 | 74% of the outright tail unquoted |

Reading the table across rows kills the "institution" explanation; reading it
down columns kills the "benchmark" explanation. What is left is repetition.

---

## 3. Voice and register rules (carry over from the memo work)

1. **Framing rule, locked:** gambling venue vs forecasting institution. Never
   trading exploitability. Exploitability appears only as an institutional
   diagnostic — biases sheltered inside cost bands, exactly as books shelter
   theirs inside vig.
2. **No hand-carried numbers.** Every figure in prose traces to a log in
   `results/logs/`. Bracketed provenance in the drafting pass, stripped at
   final formatting.
3. **Nulls are quoted with their MDE.** Every subgroup null gets its minimum
   detectable effect in the same sentence. Non-negotiable — it is the
   difference between "equivalent" and "underpowered."
4. **Suggestive stays suggestive.** The Kalshi T-24h lag (p=.063, drops at
   BH q=.05) and the WNBA totals rejection (n=234) are reported as
   observations, never as claims. Same for the 5-min book→exchange
   coefficient, which is reported with its cuts.
5. Register: declarative, no em-dash pileups, no conversational fillers. The
   Aug memo revision (`c85c5d0`) set the target; match it.
6. Present tense for what the market does, past tense for what was measured.

---

## 4. Paragraph-level spec

Beats are numbered. Each is one paragraph unless marked. Drafting a section
means writing its beats in order and nothing else.

### §1 Introduction (1,100 w, Fig 1)

- **¶1 Hook.** ~5,300 games, priced simultaneously by four mechanisms that
  share no clearing, no regulator, and in two cases no legal access to each
  other's customers. Concrete opener: one game, four prices, within a point.
- **¶2 Why it is a real question.** Prediction markets are argued about
  categorically — "investing" or "gambling" — by every participant and
  measured by none. Name the two institutions doing the categorizing
  (Betterment, Schwab, opposite directions) in one clause; the full treatment
  is §2.
- **¶3 Why sports, and why that is not a limitation.** ~95% of
  prediction-market volume is sports; >16bn Robinhood event contracts through
  June 2026. Sports is not a corner of this industry, it is the industry.
- **¶4 What the design adds over prior cross-platform work.** Same games, a
  professional benchmark including the sharp price, and equivalence testing
  rather than failure-to-reject.
- **¶5 Fig 1 walkthrough.** The headline picture, described in one paragraph
  so a reader who stops here still leaves with the finding.
- **¶6–7 Contributions, seven items,** compressed from the outline's list into
  two paragraphs of prose rather than a bulleted list. Prose reads as
  confidence; bullets read as a CV.
- **¶8 Roadmap.** Four movements, named. One sentence each.

### §2 Background and related work (1,400 w)

- **¶1 Calibration and horizon.** Page & Clemen 2013 — sharpening toward the
  event date. This paper replicates it comparatively: both exchanges and the
  books sharpen in lockstep.
- **¶2 Favorite–longshot bias.** Snowberg & Wolfers 2010 as misperception.
  Finding: no FLB in game markets at any source; FLB fully alive in outrights
  at every institution. Flag forward to Movement C — this is the paper's
  cleanest engagement with an established result.
- **¶3 Do books shade?** Levitt 2004. Tested per-book on two continents:
  30+ books, deviations sub-1pt, sign mostly opposite. Report as a
  non-replication in the modern market, stated carefully — the 2004 setting
  was a tournament, not a modern liquid book.
- **¶4 Platform pathologies.** Bürgi, Deng & Whelan, including "Makers and
  Takers" 2026. Their platform-wide pathologies are replicated here as a
  sports null; our taker P&L and maker-structure results supply the
  institutional mechanism for their makers > takers finding.
- **¶5 Cross-platform and context.** Clinton & Huang 2026; Woodland &
  Woodland 1994 for the MLB run-line baseline; practitioner run-line
  literature on walk-off compression.
- **¶6 Regulatory.** CFTC bona fide MM proposal (2026-07-30), the MPU
  investigation, the 2025–26 class actions. One paragraph, factual, no
  advocacy. Flag that Movement D tests a prediction these actions make.
- **¶7–9 The demand side (three paragraphs, the outline's §2.1).**
  ¶7: Betterment 2026 — 52% of Gen Z redirected investing money to sports
  betting; 26% treat it as long-term strategy. State the survey design (n=1,000,
  Sago, Mar 27–Apr 3) and the commercial-interest caveat in the same breath as
  the number, not in a footnote.
  ¶8: Schwab in the opposite direction; Northwestern Mutual 2026 corroborating
  the magnitude. Two institutions performing the same categorization with
  opposite signs and no measurement between them.
  ¶9: **The hinge paragraph.** Levy and Wurster both treat "prediction market"
  and "sportsbook" as one category. This paper shows that conflation is RIGHT
  about cost and clientele and WRONG about information. And the surveys'
  finding is about *horizon* — which is exactly the axis Movement C shows the
  discipline breaking on. This paragraph is the reason the paper is not just a
  calibration exercise; give it the room.

### §3 Data and pipeline (900 w, Table 1)

- **¶1 The four price sources** and how each price is constructed
  (Kalshi book-mid post-cutoff / validated trade-recon pre-cutoff; Polymarket
  Global CLOB; Polymarket US DCM tape; Odds API consensus and per-book).
- **¶2 The books benchmark is not one thing.** US consensus, EU per-book
  including Pinnacle and Betfair, US per-book at 86% of the joint set, T-24h,
  alt-spreads, outrights 2020–26. Say plainly which claims rest on which.
- **¶3 Master and joint set.** 10,118 games / 7 leagues; three-way clean
  n=5,333 (frozen 2026-08-29). Explain the attrition from master to joint set explicitly — a
  reader will ask, and answering pre-emptively buys credibility.
- **¶4 External validation.** Trade-recon vs archived books 99% within 1pt;
  Poly CLOB vs archived books median error 0.00pt.
- **¶5 Audit-gate architecture.** 73 checks, suite halts on failure.
- **¶6 The pipeline lessons.** Short here, full treatment Appendix A. Three
  independent catches, one discipline: the side-assignment audit, stale-print
  traps in resolved-market histories, and the league-specific ladder
  settlement conventions (2026-08-23) — impossible results treated as
  pipeline alarms, settlement data as ground truth, each catch converted into
  a permanent audit gate. A genuine methods contribution; signpost it.
- **¶7 Availability.** `analysis_core.csv`, DATA_DICTIONARY.md, data_tour.ipynb,
  one-command regeneration.

### §4 Methods (900 w, Table 2)

- **¶1 Scoring.** Brier and log score; Murphy decomposition; CORP; Murphy
  diagrams with sup-t bands.
- **¶2 De-vigging.** Multiplicative default, Shin for tail-sensitive claims,
  with the tail artifact documented rather than hidden.
- **¶3 Inference.** Date-clustered Diebold-Mariano; TOST at δ=1.0e-3 Brier —
  which admits a systematic 3.16pt offset (ΔBrier = ε², per D2), not the
  0.5pt an earlier gloss claimed — read against the cost-anchored ladder
  δ=0.11/0.44/0.99e-3 at prices 0.25/0.50/0.75; interval-randomized
  tie-consistent PIT; exact binomials for tail buckets; cluster bootstrap for
  niche ECE/slope.
- **¶4 Multiplicity.** BH-FDR two-family policy, stated before any result is
  shown so it does not look chosen after the fact.
- **¶5 Power, and the reading rule (Table 2).** Pooled MDE 0.36–0.51e-3
  against δ=1e-3. MLB/NBA/NHL individually powered. CFB (2.74), WNBA (2.47),
  NFL (1.57) are not, with the n-multiple each would need. State the rule:
  quote the MDE beside every subgroup null.
- **¶6 Pre-registration honesty.** Informal: freeze plus planned out-of-sample
  verification. Say exactly what was decided before seeing data and what was
  not. An honest paragraph here is worth more than a claim of rigor.

### §5A The dead heat (1,200 w, Fig 2, Table 3)

- **¶1 The headline.** Briers 0.2196 / 0.2199 / 0.2196 (K/P/B), slopes
  0.96–1.01, ECE 0.009–0.014 [three_way].
- **¶2 Equivalence, not absence of evidence.** All clustered DM n.s.; TOST
  CIs within ±0.53e-3 [rigor]. Explain in one sentence why this distinction
  is the design's contribution.
- **¶3 The benchmark upgraded to the sharp price.** Vs Pinnacle, CIs within
  ±0.34e-3 [sharp_books]. Vs each of 11 US retail books, dead heat
  book-by-book [us_books].
- **¶4 The fourth leg and the law of one price.** Polymarket US equivalent to
  each, δ_min ≤ 0.74e-3; median gap 0.50pt across legally segregated pools
  that no participant can arbitrate [four_way]. **Scope this claim carefully —
  the earlier draft over-read it.** Segregation binds traders, not operators:
  US and Global are one company, so the pair cannot distinguish shared
  information from shared quoting infrastructure, and maker identity is not in
  any public tape. Agreement without arbitrage rules out the arbitrage
  mechanism and nothing more. The version that carries weight is **Kalshi vs
  Polymarket** — unaffiliated firms, different technology, different regulatory
  regimes — agreeing to a median 0.40pt. Lead with that pair and use US-vs-
  Global as the arbitrage-elimination step only.
- **¶5 Stability.** Equivalence holds within every adequately powered quarter
  [time_stability]. Note the one wobble and its direction.
- **¶6–7 The gambling scorecard (Table 3 companion).** Calibration, no FLB,
  equal resolution, coherent ladders (97.3% monotone, 0.1% arb), no behavioral
  fingerprints, all edge strategies ≤0, cross-venue self-consistency. Two
  paragraphs, not a bare list.
- **¶8 Equally good — and equally better than public statistics.** Walk-forward
  Elo beaten by ~13.3e-3 (z≈7.4) while the venues differ by ≤0.5e-3
  [model_benchmark].
- **¶9 The registered holdout (closes the movement).** Claims were frozen in
  docs/registered-claims.md before any post-2026-08-11 game was pulled; on
  264 fresh games the exchange dead heat verified at full registered power
  (|ΔBrier| 0.04e-3, p=.879, MDE 0.81e-3 against δ=1e-3), slopes cover 1,
  the extras cell replicated (+19.6pt vs +20.2pt), the structural cost
  matched (−4.6%), and one open observation (WNBA totals tilt) flipped sign
  and is retired as noise. The three-way legs could not be evaluated — the
  live book feed had stopped 2026-08-07 when its credit reserve ran out —
  and the scorecard says so rather than re-scoping [oos_verification]. One
  abstract sentence comes from this paragraph.

### §5B How the equivalence is produced (900 w, Fig 3, Fig 4)

- **¶1 When it forms.** T-24h: Poly–book already tied; Kalshi marginally
  behind (z=+1.86, p=.063, drops at BH q=.05 — suggestive only)
  [horizon_equivalence].
- **¶2 Lockstep sharpening.** 24h→start at both exchanges and the books
  (close-vs-24h p=.040); cross-venue gaps converge 1.3pt→0.9pt. The day's move
  is uninformative beyond the close.
- **¶3 No leader, at any clock.** 15-min and 1-min: symmetric few-minute echo
  (z≈7 both directions), big repricings simultaneous [minute_lead_lag].
- **¶4 The resolution ladder (Fig 4).** 5/10/15/30 min on the same games: no
  cross-lag correlation sharpens as the clock sharpens, and nothing predicts
  the book at any grid. The no-leader result is not a coarse-clock artifact
  [five_min].
- **¶5 The one coefficient that survives, reported with its cuts.** Book→
  exchange K +0.047 (z=2.4) / P +0.164 (z=4.5), ZERO in the final 2h, living
  in sub-0.5pt book moves, and for Poly as strong from a 30-min-frozen quote.
  Read as drift alignment away from game time, not news transmission.
- **¶6 Where information actually enters.** Markouts flat across size; taker
  imbalance predicts nothing; discovery is maker-driven via quote revision
  [informed]. Book-move event study: anticipation-direction share 34% Kalshi
  (p=0.012) and 23% Polymarket (p<0.001), both significantly *below* chance
  [book_moves], sign stable from a 1pt to a 3pt event cut. Write this as "no
  transmission at any resolution the panel resolves", NOT as "parallel
  processing" — the latter is a mechanism claim the event study cannot make,
  since a same-step function of the book produces the same picture. The
  independence evidence lives in niche_gradient (calibrated where no book
  exists) and, weakly, in the encompassing residual.

### §5C Where the surface cracks (1,400 w, Fig 6, Table 4)

*The pivotal movement, rebuilt 2026-08-28 post-retraction. One mechanism at
two scales — and the last "venue defect" died on inspection.*

- **¶1 Transition.** Everything so far is about the price of a binary
  outcome. Push on the full distribution and on market type, and what breaks
  is the same thing at two scales — and it breaks at every institution at
  once.
- **¶2 The correction, stated as a result.** Kalshi settles MLB/WNBA spread
  rungs on integer lines ("wins by t-0.5 or more"), NBA/NHL on half-point
  lines ("wins by more than t"); one rule applied everywhere shifted MLB's
  implied CDF by a full run. Caught against Kalshi's own settlement field
  (99.87% vs 97.80% on 25,146 contracts), gated in data_audit, four claims
  retracted in place [multiple_testing]. Present it as a result, not a
  confession — this paragraph buys the reader's trust for everything after
  it, and it is the §3 pipeline-lessons arc completing.
- **¶3 The corrected surface: near-dead-heat on shapes too.** Every league's
  margin PIT passes (pooled p=0.718; MLB p=0.104) [margin_dist]. RPS on
  shared rungs: books +0.49e-3 (z=+2.44), carried by NBA (+1.14e-3, z=+2.27);
  MLB n.s.; NHL exact tie [multi_outcome]. The books' denser ladders fail
  their own PITs (MLB p<.001, NHL p=.024) where Kalshi's sparse ones pass —
  density and power, not superiority [book_pit]. One clause on tail ECE
  0.0078 vs 0.0073 on identical contracts [ladder_vs_books].
- **¶4 The crack that survives is shared.** Extras (8.6% of finals; 70% end
  within one run under the ghost-runner rule): the 1-2-run cell is
  under-priced +20.2pt on Kalshi (z=+5.94) and +22.0pt at the books, same
  games, same rungs [mlb_extras, ladder_vs_books]. Regulation runs the other
  way, so each venue's aggregate cell is a cancellation (K -1.1pt, B +0.4pt,
  both n.s.) — the bias was never visible in the aggregate, and never absent
  from the state.
- **¶5 Why that matters.** A rare, slow-feedback state inside a repeated
  market is the within-game miniature of the boundary this movement ends on:
  repetition disciplines what it samples often; what it samples rarely stays
  wrong — at every institution. The shared-blind-spot column now holds the
  extras cell, the WC draws, and the 40/60 compression. And it is sheltered:
  selling any rung loses money net of costs [ladder_cost] — biases harbored
  inside cost bands, exactly as books harbor theirs inside vig. The framing
  rule earns its keep here.
- **¶6 The totals layer, retargeted.** Totals settle uniformly (verified);
  PIT passes MLB/NBA/NHL, contract ECE 0.0046, no right-tail bias [totals].
  Collected to test the walk-off contrast; the contrast is retracted, and
  what the layer shows instead is stronger: the entire run-scoring process
  is priced correctly in every densely-sampled dimension. WNBA rejection:
  one sentence — resolved as a false alarm twice over: dissolved in the
  frozen sample (p=0.21 at n=290) and sign-flipped on the registered holdout
  (u 0.404, z=−2.3, n=47) [totals, oos_verification].
- **¶7 Self-correction, corrected.** The "+7.5 to +11.2pt non-correcting
  bias" was the artifact persisting; the corrected aggregate cell is
  near-unbiased in every era, and the extras cell recurs in both 2026
  halves (+18.3/+26.4pt, n=156/56) — no self-correction claim either way at
  these n [time_stability].
- **¶8 The scale-up (transition to the boundary).** A state a market rarely
  samples is a small version of a market type with no repetition to learn
  from at all.
- **¶9 Pathologies vanish where repetition exists.** BDW's platform-wide
  pathologies are absent in game markets — moneylines at mid, -0.45%
  [why_sports].
- **¶10 They return in one-shot outrights, at EVERY institution (Fig 6).**
  Kalshi $0.33 (fresh prints: 0 winners in 114), Polymarket $0.53, and the
  BOOKS $0.34 at 0-3 months (se 0.08, n=1,614, 20 sport-seasons 2020-26,
  playoff-densified) — statistically identical to the exchange
  [futures_calibration, book_outrights]. Both-tail overconfidence: 75c+
  favorites won 62.5% against 86.3% priced. Book overrounds 1.20-1.27 vs
  exchange 1.03: the exchange charges less and is wrong in the same places.
  State the de-vig caveat in prose, not just the figure footnote: the books'
  sub-10c return rises to $0.52 under Shin, and murphy.py's own rule says
  tail-sensitive claims must use Shin — so "statistically identical" holds
  under multiplicative de-vig, and the honest sentence is "the books fail
  the same way, within de-vig uncertainty," not "identically."
- **¶11 The benchmark is not the active ingredient.** Un-benchmarked
  repeated niche games are clean: excess ECE 0.00 against the noise floor,
  slope 0.98 (CI 0.84-1.15), field sums 1.02 [niche_gradient].
- **¶12 Nor is liquidity.** Deep outright books misprice; tiny niche books
  do not. The footprint result closes the confounder [liquidity_footprint].
- **¶13 Table 4, read both ways.** Across rows the institution explanation
  dies; down columns the benchmark explanation dies. Repetition and fast
  resolution are what is left. Precision vs bias decomposition: repetition
  produces unbiasedness; the MM complex produces existence and precision
  (0.7pt vs 4.2pt from consensus).

### §5D What it costs, and who is on the other side (1,300 w, Fig 9, Table 5)

- **¶1 Transition.** Every result so far is a property of the price. None of
  it is a property of what the user receives.
- **¶2 The cost table (Table 5).** Taker all-in Kalshi ≈ −4.2% ≈ books' vig
  −4.1%; maker path ≈ free, a route books do not offer; Poly takers ~1–1.75%.
- **¶3 Realized, not just quoted.** Taker P&L to settlement −5.0% gross /
  −7.7% net on $95.7M; every size class loses [retail_fingerprint].
- **¶4 Who this is.** 53% of fills in the final 3h, evening-leisure
  concentration, median stake $14. Consumption-shaped. State the identification
  limit here, not only in §7: no account attributes exist in the tape.
- **¶5 What the microstructure charges.** Fee natural experiment: accuracy
  invariant, incidence on volume (−41%) with the touch pinned at 1c
  [fee_liquidity]. Tick design: the touch IS the tick; Kalshi's uniform 1c
  makes tails ~10x costlier than Poly's 0.001 regime [tick_pricing].
- **¶6 The price of immediacy.** A 30-unit order sits inside the touch in
  89% (K) / 95% (P) of snapshots; median cost half the tick (0.50c, ~0.9% of
  notional) up to 10,000 units. What runs out is capacity, not price
  [immediacy]. Venues invert into the event: Poly deeper a day out, Kalshi
  ~5x deeper inside 30 min.
- **¶7–9 The affiliated dealer (three paragraphs).**
  ¶7: documentary record — Kalshi Trading on the exchange since 2021, the CFTC
  bona fide MM proposal, incentive program exclusions, no public roster.
  ¶8: the two-layer book — retail-sized touch over ~20K contracts/side within
  5c across ~90 games [maker_structure]; the footprint gradient (games
  $817K/5c, niche $6K, 74% of the outright tail unquoted) and a fee menu that
  prices that same gradient.
  ¶9: the class-action prediction, tested. Takers do NO BETTER where the
  house's book is absent (−5.0%/−7.7% vs −7.1%/−10.0%, n.s.) [mm_involvement].
  The house's absence mostly means no market. Market functioning on 287 shared
  niche matches supports the same reading. Synthesis: the MM complex governs
  whether a market exists and how precise it is; it does not worsen what takers
  pay. The exchange/house question is about whether the liquidity supplier may
  hold a directional book — a governance question, not an accuracy one.
- **¶10–12 Horizon-matched translation (Fig 9, three paragraphs).**
  ¶10: the bridge. §2's respondents describe a horizon; this paper measures
  per-position returns; the link is rate × re-stake frequency. Structural taker
  cost −4.5% per position (n=47,766 quotes, IQR −5.4 to −4.0) is the anchor
  because it is fixed by the quote and fee schedule before a ball is thrown.
  Realized −5.0%/−7.7% agrees, but its game-clustered 90% CI (−19.5% to +2.9%)
  spans zero. **The two agreeing to within a couple of points is the finding;
  outcomes are noisy, the cost is not.**
  ¶11: cadence is a scenario grid, explicitly not a measurement — the public
  tape has no account identifiers. Bankroll after a 26-week season: monthly
  76%, fortnightly 55%, weekly 30%, twice-weekly 9%, daily ~0%.
  ¶12: the horizon-matched line. One futures ticket held from a week out
  returns −43.7% ($0.56/$1). Reaching the same place through the well-priced
  game markets takes 12.4 positions — ~12 game bets equals buying the one
  product this paper shows is badly priced at every institution, and a weekly
  bettor gets 48% of the way there in a season. Close on: **calibration
  disciplines the price; it does not protect the participant.**
  Framing discipline: descriptive comparison only, no recommendation; the
  equity yardstick is a fixed textbook constant, not an estimate from this
  project.

### §6 Institutional synthesis (700 w)

- **¶1 For the market-order retail user,** the exchange's sports section
  functions as a sportsbook: same prices, same realized cost, same sheltered
  biases, sportsbook-shaped clientele, professional dealer on the other side.
- **¶2 In aggregate it is a forecasting instrument:** formally equivalent to
  the sharpest professional prices, coherent, maker-disciplined, honest about
  its own uncertainty, and better than public statistics.
- **¶3 Both are true, and that is the answer to the categorization debate.**
  The conflation Levy and Wurster perform is right about cost and clientele
  and wrong about information. Neither institution's label does any work.
- **¶4 What actually differs is design:** who may hold a directional book,
  what the tick and fee schedule charge for the tails, where the liquidity
  complex chooses to stand.
- **¶5 Where discipline comes from.** Repetition and feedback. Nothing about
  "prediction markets" or "sportsbooks" as institutions manufactures it — and
  the horizon on which people report using these products is the one where it
  is absent.
- **¶6 Policy reading, stated once and carefully.** The regulatory debate is
  about venue category; the evidence says category is the wrong axis. One
  paragraph, no advocacy, no recommendation.

### §7 Limitations (600 w)

- **¶1 No demographic data.** Longest limitation, first position. The §2
  framing is motivation, not identification. The tape carries no age,
  location, or account attributes; no generational claim is made or possible.
  What can be said: what the product costs and returns to whoever is using it,
  and that the usage pattern is consumption-shaped.
- **¶2 Data-construction limits.** Consensus timing (60-min buckets vs
  exchange T-0, with the direction documented and favoring the markets);
  Kalshi 60-day decay and the harvest protocol; trade-recon staleness with
  caps and robustness; Poly resolved-market candle coarseness.
- **¶3 Coverage limits.** US per-book at 86% of the joint set (floor-stopped);
  CBB largely excluded; niche name-matching gives lower bounds; cross-source
  margin curves cover MLB and NBA only; totals layer is Kalshi-only.
- **¶4 Inference limits.** Small-league power (point back to Table 2);
  outright inference rests on 20 season-clusters; 15-min panel is era-limited;
  pre-registration is informal.

### §8 Reproducibility and data (250 w)

One-command regeneration, audit-gated suite, committed core table, dictionary,
tour notebook, free-API re-derivability for exchange data, book data banked
before the subscription lapses Sept 2026, backups. Repository URL.

### Appendices
A. Side-assignment audit. B. Full figure gallery (the 20 demoted figures).
C. Robustness battery: log score, home-side, CORP, selection, de-vig variants,
staleness. D. FDR table. E. Equivalence/null register. F. World Cup 3-way
case study (n=9, descriptive). G. Data dictionary.

---

## 5. Drafting order (not document order)

Write outward from the strongest material. The spine gets written while
energy is highest; the framing gets written once the spine is fixed and can
be described accurately.

1. **§5C** — the pivotal movement, hardest argument, most original. If this
   paragraph plan survives contact with drafting, the paper works.
2. **§5A** — mostly transcription from locked numbers. Fast.
3. **§5D** — second-hardest; three sub-arcs to keep separate.
4. **§5B** — short, mechanical.
5. **§6** — writes itself once 5A–5D exist.
6. **§3, §4** — reference sections, low creative load, good recovery work.
7. **§2** — needs the results fixed so the forward-references are accurate.
8. **§7, §8** — mechanical.
9. **§1** — last but one. An introduction written before the paper describes
   the paper the author intended, not the one that exists.
10. **Abstract** — last.

---

## 6. Open items that affect prose (not blocking)

1. **Venue/format** — advisor email pending. Decision B makes this
   non-blocking; the manuscript works either way.
2. ~~**Number freeze**~~ — RUN 2026-08-29 (dc40fe6) and re-stamped 2026-09-03
   at 61 modules. Provenance brackets can now be resolved against
   `results/logs/`; keep them in the draft until the final read-through.
3. ~~**Out-of-sample verification**~~ — REGISTERED 2026-08-28 and EXECUTED
   2026-08-29. It becomes ¶9 of §5A and an abstract sentence, as planned: R2
   confirmed the exchange dead heat at full registered power (|ΔBrier|
   0.04e-3 vs MDE 0.81e-3), R6 and R8 replicated, R7 deviated and retired the
   WNBA observation as noise, R1/R5 not evaluable (the live feed's book leg
   had stopped). Report the deviation with the same prominence as the
   confirmations.
4. ~~**Table 4 needs rendering**~~ — BUILT. `tables.py` emits Tables 1–5 to
   `results/report/tables.md` from the logs, re-stamped by every freeze run,
   so no number is hand-carried.
5. ~~**WNBA totals rejection**~~ — RESOLVED as a false alarm twice over
   (dissolved on the frozen sample, flipped sign on the registered holdout).
   It is now an example of the machinery working, not an open observation:
   one sentence in §5C, and it belongs in the §7 corrections paragraph.
6. **NEW (2026-09-03 interpretation audit)** — three claims were restated at
   the strength the design supports. §5B must not say "parallel processing"
   or "not transmitted"; §5A ¶4's law-of-one-price is arbitrage-elimination
   only; §7 leads with the product-scope paragraph. See
   `docs/interpretation-audit-2026-09-03.md`.
