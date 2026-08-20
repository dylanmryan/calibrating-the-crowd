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

Movement C is the pivotal regrouping. The MLB walk-off failure (5.5) and the
one-shot outright failure (5.9) are currently 12 pages apart, but they are the
same finding at two scales: **discipline is a property of the market's
repetition structure, not of the institution.** Walk-offs are a within-game
rule that breaks the mapping; one-shot outrights are a market type with no
repetition to break. Put them adjacent and the paper has a thesis instead of
two anomalies.

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
| 5C. Where the surface cracks | 1,400 | Fig 5, Fig 6 | Table 4 |
| 5D. What it costs, and who is on the other side | 1,300 | Fig 7, Fig 8 | Table 5 |
| 6. Institutional synthesis | 700 | — | — |
| 7. Limitations | 600 | — | — |
| 8. Reproducibility and data | 250 | — | — |
| **Total** | **~10,870** | **8 + Fig 9 in 5D** | **5** |

### Main figures (9 of 29). Everything else → Appendix B gallery.
| # | File | Carries |
|---|---|---|
| 1 | `plain_calibration.png` | The hook: teams priced at X% win X% of the time, all venues |
| 2 | `equivalence_forest.png` | Formal equivalence — every pairwise ΔBrier CI inside the margin |
| 3 | `horizon_calibration.png` | When the equivalence forms (T-24h → close) |
| 4 | `five_min.png` | How it forms: no leader survives the resolution ladder |
| 5 | `margin_pit.png` | The crack: MLB margin PIT rejects |
| 6 | `totals.png` | The diagnosis: same games, totals PIT passes |
| 7 | `oneshot_returns.png` | The boundary: one-shot returns collapse everywhere |
| 8 | `niche_gradient.png` | The active ingredient: repetition, not benchmark |
| 9 | `horizon_translation.png` | The participant's units: bankroll decay by cadence |

Deliberately demoted to appendix (each is good, none is load-bearing for the
spine): `four_way`, `three_way_calibration`, `corp_reliability`, `murphy`,
`spread_coherence`, `profitability`, `model_benchmark`, `book_moves`,
`minute_lead_lag`, `retail_fingerprint`, `fee_liquidity`, `tick_pricing`,
`immediacy`, `liquidity_footprint`, `why_sports`, `kalshi_nuance`,
`hierarchical_calibration`, `horizon_cross`, `margin_distribution`,
`kalshi_vs_polymarket`, `reliability_kalshi`, `book_moves`.
Their numbers still appear in prose and tables — only the plots move.

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
- **¶3 Master and joint set.** 9,778 games / 7 leagues; three-way clean
  n=5,327. Explain the attrition from master to joint set explicitly — a
  reader will ask, and answering pre-emptively buys credibility.
- **¶4 External validation.** Trade-recon vs archived books 99% within 1pt;
  Poly CLOB vs archived books median error 0.00pt.
- **¶5 Audit-gate architecture.** 73 checks, suite halts on failure.
- **¶6 The side-assignment lesson.** Short here, full treatment Appendix A.
  Two independent catches of stale-print traps in resolved-market histories.
  This is a genuine methods contribution and should be signposted, not buried.
- **¶7 Availability.** `analysis_core.csv`, DATA_DICTIONARY.md, data_tour.ipynb,
  one-command regeneration.

### §4 Methods (900 w, Table 2)

- **¶1 Scoring.** Brier and log score; Murphy decomposition; CORP; Murphy
  diagrams with sup-t bands.
- **¶2 De-vigging.** Multiplicative default, Shin for tail-sensitive claims,
  with the tail artifact documented rather than hidden.
- **¶3 Inference.** Date-clustered Diebold-Mariano; TOST at δ=1.0e-3 Brier
  (≈0.5pt/game) with the justification for that margin; interval-randomized
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
  that no participant can arbitrate [four_way]. This is the cleanest mechanism
  demonstration in the paper: agreement without arbitrage means shared
  information.
- **¶5 Stability.** Equivalence holds within every adequately powered quarter
  [time_stability]. Note the one wobble and its direction.
- **¶6–7 The gambling scorecard (Table 3 companion).** Calibration, no FLB,
  equal resolution, coherent ladders (97.3% monotone, 0.1% arb), no behavioral
  fingerprints, all edge strategies ≤0, cross-venue self-consistency. Two
  paragraphs, not a bare list.
- **¶8 Equally good — and equally better than public statistics.** Walk-forward
  Elo beaten by ~13.3e-3 (z≈7.4) while the venues differ by ≤0.5e-3
  [model_benchmark]. Closes the movement: the equivalence is at a high level,
  not a low one.

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
  [book_moves]. Parallel processing of the same information, not transmission.

### §5C Where the surface cracks (1,400 w, Fig 5, Fig 6, Table 4)

*The pivotal movement. Two failures, one mechanism.*

- **¶1 Transition.** Everything so far is about the price of a binary outcome.
  Push on the full distribution and on market type, and the equivalence stops
  holding in two places that turn out to be the same place.
- **¶2 The distributional edge is real but localized.** RPS on shared rungs
  (n=3,690): books better — MLB +3.9e-3 (z=+5.4), NBA +1.1e-3 (z=+2.3), NHL
  an exact tie (z=+0.05) [multi_outcome]. The edge lives exactly where the
  margin process is pathological.
- **¶3 The MLB cell.** Kalshi +8.5pt vs books +0.4pt on 1–2-run margins
  (z=+10); extras mechanism ~24% of it [ladder_vs_books].
- **¶4 And it is sheltered, not exploitable.** Selling it loses 2.9–4.5% net
  of costs. The bias is harbored inside a cost band — institutionally
  identical to how a book harbors bias inside vig. This sentence is where the
  framing rule earns its keep.
- **¶5 PIT (Fig 5).** Books pass where Kalshi fails (MLB); NHL book ladders
  fail where Kalshi passes, with the sparse-rung caveat noted and not claimed
  [book_pit].
- **¶6–7 The diagnosis via a third market layer (Fig 6). Two paragraphs.**
  ¶6: the design. Totals run over the same scoring process, but extras push
  totals UP instead of truncating margins, and no stop-the-game rule applies.
  Same 1,244 MLB games. ¶7: the result. Totals PIT passes (KS=0.017, p=0.84)
  where the margin PIT rejects (KS=0.073, p=2.9e-6) — with 11 rungs vs 3–5,
  so the passing test is the better-powered one. **Kalshi does not mismodel
  baseball; it mismodels the rule that stops the game.**
- **¶8 Scope and the open observation.** Four-league sample (36,552 contracts /
  4,260 games): totals PIT passes in MLB (p=.90), NBA (p=.86), NHL (p=.25),
  rejects only in WNBA (p=.0076, n=234, mild upward tilt, mean u .536).
  Reported as an open observation. Coherence splits by price source —
  live-book ladders 99.3–100% monotone, trade-reconstructed 86.9–95.6% — so
  the violations are reconstruction noise, not market incoherence.
  Kalshi-only layer: no book benchmark, budget spent. Say so.
- **¶9 The scale-up (transition to the boundary).** A rule that breaks the
  mapping inside a game is a small version of a market type that has no
  repetition to learn from at all.
- **¶10 Pathologies vanish where repetition exists.** BDW's platform-wide
  pathologies are absent in game markets — moneylines at mid, −0.45%
  [why_sports].
- **¶11 They return in one-shot outrights, at EVERY institution (Fig 7).**
  Kalshi $0.33 (fresh prints: 0 winners in 114), Polymarket $0.53, and the
  BOOKS $0.34 at 0–3 months (se 0.08, n=1,614, 20 sport-seasons 2020–26,
  playoff-densified, Shin-robust) — statistically identical to the exchange
  [futures_calibration, book_outrights]. Both-tail overconfidence: 75c+
  favorites won 62.5% against 86.3% priced. Book overrounds 1.20–1.27 vs
  exchange 1.03: the exchange charges less and is wrong in the same places.
- **¶12 The benchmark is not the active ingredient (Fig 8).** Un-benchmarked
  repeated niche games are clean: excess ECE 0.00 against the noise floor,
  slope 0.98 (CI 0.84–1.15), field sums 1.02 [niche_gradient].
- **¶13 Nor is liquidity.** Deep outright books misprice; tiny niche books do
  not. The footprint result closes the confounder [liquidity_footprint].
- **¶14 Table 4, read both ways.** Across rows the institution explanation
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
2. **Number freeze** — deferred by request. Every number in the draft carries
   its bracketed log until freeze re-stamps it. Do not strip provenance
   brackets before freeze.
3. **Out-of-sample verification (~Aug 22)** — if it runs, it becomes ¶9 of
   §5A and a sentence in the abstract. If it does not, nothing else changes.
   Drafted so its absence leaves no hole.
4. **Table 4 needs rendering** — the 2×2 does not exist as an artifact yet.
   Numbers are all in `niche_gradient`, `futures_calibration`,
   `book_outrights`, `liquidity_footprint`.
5. **WNBA totals rejection** — one sentence in §5C ¶8, one clause in §7 ¶4.
   No further analysis.
