# Report outline — Calibrating the Crowd
*Drafting outline (2026-08-06), for review before prose. Every number below
was re-verified against the 2026-08-06 clean-run logs (53 modules, 0
failures); provenance in brackets. Figures referenced by filename exist in
`results/`.*

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
  3. Distributional layer: margins, ladders, PIT, RPS — where the books keep
     a real edge and why.
  4. Horizon-resolved: when the equivalence forms; minute-scale price
     formation; maker-driven discovery.
  5. Institutional accounting: costs, fees, ticks, taker P&L, the affiliated
     dealer, and where the liquidity complex deploys.
  6. The discipline boundary: a futures/outrights 2x2 plus a no-benchmark
     niche tier that isolates repetition as the active ingredient.
  7. Methods lessons: the side-assignment audit; stale-print traps in
     resolved-market histories (two independent catches).

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
  anchor. Master 9,419 games / 7 leagues; three-way clean n=5,328.
- External validation: trade-recon vs archived books 99% within 1pt; Poly
  CLOB vs archived books median error 0.00pt.
- Audit-gate architecture (73 checks, suite halts on failure) + the
  side-assignment lesson (own subsection).
- Data availability: `analysis_core.csv` (committed), DATA_DICTIONARY.md,
  data_tour.ipynb, one-command regeneration.

## 4. Methods
- Scoring: Brier + log score; Murphy decomposition; CORP; Murphy diagrams
  with sup-t bands. De-vig: multiplicative default, Shin for tail-sensitive
  claims (tail artifact documented).
- Inference: date-clustered DM; TOST at δ=1.0e-3 Brier (≈0.5pt/game);
  interval-randomized tie-consistent PIT; exact binomials for tail buckets;
  cluster bootstrap for niche ECE/slope; BH-FDR two-family policy.
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
- Vs Pinnacle: all CIs within ±0.34e-3 [sharp_books.log]. Vs each of 11 US
  books: dead heat book-by-book, all n.s. [us_books.log].
- Time stability: equivalence holds within every adequate quarter
  [time_stability.log].

### 5.2 The gambling scorecard (table)
Calibration ✓, no FLB (slopes ≈1) ✓, equal resolution ✓, coherent ladders
(97.3% monotone, 0.1% arb) ✓, no behavioral fingerprints ✓, unexploitable
(all edge strategies ≤0) ✓, self-consistent across venues ✓.
Figs: `spread_coherence.png`, `profitability.png`.

### 5.3 When the equivalence forms
- T-24h: Poly-book already tied; Kalshi marginally behind (z=+1.86, p=.063
  — softened from p=.020 on the completed 84% sample; drops at BH q=.05;
  report as suggestive) [horizon_equivalence.log].
- Lockstep sharpening 24h→start (both exchanges, and the books:
  close-vs-24h p=.040); convergence of cross-venue gaps 1.3pt→0.9pt.
- Day's move uninformative beyond close (close efficiency all n.s.).
Fig: `horizon_calibration.png`.

### 5.4 How prices form
- No venue leads at 15-min or 1-min; symmetric few-minute echo (z≈7 both
  directions); big repricings simultaneous [minute_lead_lag.log].
- **Resolution ladder (5/10/15/30 min, same games): no cross-lag correlation
  sharpens as the clock sharpens, and nothing predicts the book at any grid —
  the no-leader result is not an artifact of a coarse clock** [five_min.log].
  The fine clock does surface a small book→exchange coefficient (K +0.047
  z=2.4, P +0.164 z=4.5) that is ZERO in the final 2h, lives in sub-0.5pt book
  moves, and for Poly is as strong from a 30-min-frozen quote: drift alignment
  away from game time, not news transmission. Reported with its cuts.
- Markouts flat across size; taker imbalance predicts nothing → discovery
  is maker-driven, information enters via quote revision [informed].
- Book-move event study: exchanges neither anticipate nor follow with a lag
  — parallel processing of the same information. On the refreshed 528-game
  panel the anticipation-direction share is 34% Kalshi (p=0.012) and 23%
  Polymarket (p<0.001), both significantly BELOW chance [book_moves.log].
Figs: `minute_lead_lag.png`, `five_min.png`.

### 5.5 Where the surfaces crack: distributions
- RPS head-to-head on shared rungs (n=3,690): books better, but LOCALIZED —
  MLB +3.9e-3 (z=+5.4), NBA +1.1e-3 (z=+2.3), NHL exact tie (z=+0.05)
  [multi_outcome.log]. The edge lives where the margin process is
  pathological (walk-off/extras spike).
- MLB 1-2-run cell: Kalshi +8.5pt vs books +0.4pt (z=+10); extras mechanism
  ~24% of it; unexploitable net of costs (selling it loses 2.9-4.5%) —
  biases harbored inside cost bands, exactly like books inside vig.
- PIT: books pass where Kalshi fails (MLB); NHL book ladders fail where
  Kalshi passes (sparse-rung caveat, noted not claimed) [book_pit.log].
- **The mechanism, isolated by a third market layer** [totals.log]: totals run
  over the same scoring process but extras push totals UP instead of
  truncating margins, and no stop-the-game rule applies. On 1,244 IDENTICAL
  MLB games the totals PIT PASSES (KS=0.017, p=0.84) where the margin PIT
  REJECTS (KS=0.073, p=2.9e-6) — with 11 rungs vs 3-5, i.e. the passing test
  is the better-powered one. Totals contract calibration ECE 0.0046, no
  right-tail bias (all |z|<=1.01).
  **Kalshi does not mismodel baseball; it mismodels the rule that stops the
  game.** Kalshi-only layer (no book benchmark — budget spent).
  Full four-league sample (36,552 contracts / 4,260 games): totals PIT passes
  in MLB (p=.90), NBA (p=.86) and NHL (p=.25) and REJECTS only in WNBA
  (p=.0076, n=234, mild upward tilt, mean u .536) — reported as an open
  observation, not a claim. Coherence splits by price source: live-book
  ladders are 99.3-100% monotone in every league, trade-reconstructed ones
  86.9-95.6% — the violations are reconstruction noise, same as the spread
  ladders.
Figs: `margin_distribution.png`, `margin_pit.png`, `totals.png`.

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
Sports scope (but see §2.1: ~95% of prediction-market volume is sports, so this
is the main case rather than a narrow one); consensus timing (60-min buckets vs exchange T-0 — documented
direction); Kalshi 60-day decay (harvest protocol); trade-recon staleness
(caps + robustness); small-league power (MDE table); niche name-matching
lower bounds; Poly resolved-market candle coarseness; US per-book covers 86% of the joint set
(floor-stopped); outright inference = 20 season-clusters; 15-min panel
era-limited; informal pre-registration (freeze + out-of-sample verification
planned ~Aug 22).

## 8. Reproducibility and data
One-command regeneration (53 modules, audit-gated); committed core table +
dictionary + tour notebook; free-API re-derivability for exchange data;
book data banked (subscription lapses Sept 2026); VPS backups.

## Appendices
A. Side-assignment audit. B. Robustness battery (log score, home-side,
CORP, selection, de-vig variants, staleness). C. FDR table: 16 discovery
claims, 13 survive BH q=.05 (encompassing whisper + books-lead-24h drop;
reported as suggestive). D. Equivalence/null register (17 entries).
E. Data dictionary.

---

## Numbers locked for the draft (single source of truth)
| Claim | Number | Log |
|---|---|---|
| Three-way Briers | 0.2196 / 0.2199 / 0.2196 (n=5,328) | three_way |
| TOST pooled | all CIs within ±0.53e-3 | rigor |
| vs Pinnacle | CIs within ±0.34e-3 (n=5,294) | sharp_books |
| US book-by-book | 11 books, 4,664 games, all n.s. | us_books |
| Four-way | δ_min ≤ 0.74e-3 | four_way |
| Elo premium | +13.3e-3, z≈7.4 | model_benchmark |
| RPS | MLB z=+5.4, NBA z=+2.3, NHL z=+0.05 | multi_outcome |
| MLB cell | K +8.5pt vs B +0.4pt (z=+10) | ladder_vs_books |
| Taker P&L | -5.0% gross / -7.7% net, $95.7M | retail_fingerprint |
| Outright longshots | K $0.33 / P $0.53 / B $0.34 (se .08, 20 seasons) | futures_calibration, book_outrights |
| Niche gradient | excess ECE 0.00, slope 0.98 | niche_gradient |
| Footprint | $817K vs $6K vs $235K per market | liquidity_footprint |
| Functioning | 0.7pt vs 4.2pt from consensus; books 7.1% niche vig | market_functioning |
| Shading | 30+ books, sub-1pt, sign opposite | sharp_books, us_books |
| Fee incidence | volume -41%, touch pinned | fee_liquidity |
| FDR | 16 claims, 13 keep at q=.05 | multiple_testing |

## Open items before the final draft
1. Advisor: venue (grant report vs arXiv) and turnaround — memo pending.
2. Claim registration + out-of-sample verification on late-Aug data (~Aug 22).
3. ~~5-min book event study + price-of-immediacy curve~~ — DONE 2026-08-10
   (five_min.py, immediacy.py; §5.4 and §5.6 above).
4. ~~MDE table~~ — DONE 2026-08-10 (power.py; §4 above).
5. Number freeze: final suite run stamps every figure/table. One last VPS
   panel refresh first — the fine-clock event study is at n=19 and the panel
   adds ~18 games/day.
6. Kalshi price re-harvest ~Aug 18 (60-day cutoff) before the freeze.

## Numbers added 2026-08-10 (append to the locked table at freeze)
| Claim | Number | Log |
|---|---|---|
| Resolution ladder | no lead sharpens 30->5 min; nothing predicts the book | five_min |
| 5-min book->exchange | K +0.047 (z=2.4) / P +0.164 (z=4.5); ZERO in final 2h | five_min |
| Immediacy at retail size | 0.50c (~0.9% notional); inside touch 89%/95% | immediacy |
| Capacity at 200K units | fills inside 5c in 36% (K) / 21% (P) of books | immediacy |
| Within-game depth ramp | 2.29x (K) vs 1.58x (P) | immediacy |
| Pooled MDE | 0.36-0.51e-3 vs delta=1e-3 | power |
| Underpowered leagues | CFB 2.74, WNBA 2.47, NFL 1.57 (e-3) | power |
| FDR | 17 claims, 15 keep at q=.05 | multiple_testing |
| Totals vs margins PIT (same 1,244 MLB games) | totals p=0.84 pass / margins p=2.9e-6 reject | totals |
| Totals contract calibration (MLB) | Brier 0.1780, ECE 0.0046, n=15,124 | totals |
| Re-harvested master (2026-08-11) | 9,778 games; three-way clean n=5,327 | build_master, three_way |
| Structural taker cost | -4.5%/position (IQR -5.4 to -4.0, n=47,766 quotes) | horizon_translation |
| Bankroll left, weekly re-stake, one season | 30% | horizon_translation |
| Game bets equal to one futures ticket | 12.4 | horizon_translation |
