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

## 3. Data and pipeline
- Sources table: Kalshi (book-mid post-cutoff / validated trade-recon
  pre-cutoff), Polymarket Global (CLOB), Polymarket US (DCM tape),
  sportsbooks (Odds API: US consensus, EU per-book incl. Pinnacle/Betfair,
  US per-book half-sample, T-24h, alt-spreads, outrights 2020-26), ESPN
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
- Power: MDE table for subgroup equivalences (to add; NFL n=278, WNBA n=412
  are consistent-but-underpowered).

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
- Markouts flat across size; taker imbalance predicts nothing → discovery
  is maker-driven, information enters via quote revision [informed].
- Book-move event study: exchanges neither anticipate nor follow with a lag
  — parallel processing of the same information [book_moves.log].
Fig: `minute_lead_lag.png`.

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
Figs: `margin_distribution.png`, `margin_pit.png`.

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
Figs: `retail_fingerprint.png`, `fee_liquidity.png`, `tick_pricing.png`.

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
Sports scope; consensus timing (60-min buckets vs exchange T-0 — documented
direction); Kalshi 60-day decay (harvest protocol); trade-recon staleness
(caps + robustness); small-league power (MDE table); niche name-matching
lower bounds; Poly resolved-market candle coarseness; US per-book is a
seeded half-sample; outright inference = 20 season-clusters; 15-min panel
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
| US book-by-book | 11 books, all n.s. | us_books |
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
3. 5-min book event study + price-of-immediacy curve (~Aug 14).
4. MDE table (fold into §4/Appendix B).
5. Number freeze: final suite run stamps every figure/table.
