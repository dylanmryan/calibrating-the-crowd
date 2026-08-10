# Calibrating the Crowd — Findings Summary
*Dylan Ryan · BPF Undergraduate Research Grant · updated 2026-07-10*

**Research question:** are sports prediction markets genuine forecasting instruments,
or another form of gambling?

**Answer so far: forecasting instruments, on every facet tested.** A US-regulated
exchange (Kalshi), an offshore crypto market (Polymarket), and professional
sportsbooks converge on statistically *equivalent*, well-calibrated, internally
coherent, unexploitable probability forecasts. The one facet where they differ is
cost: prediction markets charge participants ~1% versus the books' ~4.2%.

---

## Data

| Component | Size | Source |
|---|---|---|
| Game registry (schedule, start times, outcomes) | 9,482 games, 7 leagues | ESPN scoreboard API |
| Kalshi moneyline closing prices | 9,186 games | order-book mid at official start (candlesticks); trade-reconstructed bid/ask pre-cutoff |
| Polymarket closing prices | 5,563 games | CLOB 1-min price history at official start |
| Sportsbook consensus closing lines | 5,151 games | The Odds API historical (≈10.5 books/game, de-vigged) |
| **All-three joint set (clean)** | **5,328 games** | NBA/NHL/MLB/CFB/NFL/WNBA, May 2025 – Jul 2026 (franchise re-collection 2026-07-31) |
| Alternate-spread ladders | 28,940 contracts, 4,042 games | Kalshi spread series |
| Book alternate spread lines | 107,100 points, 2,480 MLB/NBA games | The Odds API historical (per-event, de-vigged pairs) |
| Polymarket archived order books | 93 games (spread sample) | OddPool archive |
| Multi-horizon price paths | Kalshi ~8,000 + Polymarket 5,410 games × 7 horizons | trade history / CLOB minute paths |
| Book T−24h "opening" consensus | 3,461 games | The Odds API historical |
| Live 3-source time series + World Cup 3-way | every 15 min | VPS collector (lead–lag, in progress) |

Outcome integrity: ESPN finals cross-checked against both platforms' settlements
(99.6% / 98.7% agreement); flagged games excluded. Venue/side assignment via the
ticker-order rule (validated 99.6% vs ESPN).

**Data-quality gate (2026-07-29).** A 48-check automated audit now runs as
the *first* module of the results suite — a failure blocks the whole
regeneration. Checks: key uniqueness, price ranges, bid ≤ ask, two-sided
sums, master-vs-ESPN outcome consistency, referential integrity,
resumable-collector duplicate hazards, and file hygiene. Its first run caught
and fixed: **39 cross-harvest duplicate game rows** in the Kalshi price file
and 22 in the horizons file (older-era rows superseded by the current side
rule; keep-newest now enforced inside the collectors so it cannot recur),
plus two stale iCloud "keep both" file copies. After cleaning, all checks
pass and every headline conclusion is unchanged (shifts confined to the 4th
decimal; pooled TOST intervals tightened to ±0.46e-3).
(`src/analysis/data_audit.py`, first entry in `src/make_results.py`)

**Review fixes applied (2026-07-30).** Following the full code review
(`docs/code-review-findings.md`): 1:1 match enforcement dropped 117
ambiguous doubleheader/series pairings and purged their possibly-wrong
prices (three-way clean set 5,053 → 5,046; kalshi-disagree flags fell
179 → 161, confirming some "disagreements" were the wrong siblings);
the FDR inventory was regenerated from live logs; the MLB run-line 45.0%
claim and NBA-encompassing sub-claim were retracted; tie-consistent PIT
and push handling corrected the distributional comparisons; lead–lag
shifts now run on full calendar grids; the horizon collector's page cap
was raised (deep re-fill in progress); book team-name matching was
normalized, and the dropped franchise games re-collected (2026-07-31:
closing leg 353 calls + targeted T-24h top-up 268 calls, ~5.7K credits
total, user-approved; Clippers 79/82, Canadiens 99/100, Blues 82/84 now
priced). **Final data configuration: three-way clean n=5,328, Briers
0.2196/0.2199/0.2196, all equivalences hold; four-way n=2,639.** The
franchise restoration is itself a selection check passed: adding ~280
previously-missing games moved the Briers by ~1e-3 uniformly and no
conclusion changed.

**Deep coherence audit (2026-07-29).** A second gate checks that the data is
*true*, not just well-formed, by cross-examination: no look-ahead (every
closing quote timestamped before its game's start, all files); cross-source
disagreement as a misattachment detector (median gaps 0.5–0.6pt; the 13
gross-disagreement games are *genuine stale quotes* — 11 are Aug–Sep 2025
CFB where brand-new Polymarket listings still sat near issuance while Kalshi
and the books agreed with each other — not matching errors); clock
verification (found and fixed the one real defect: 47 Polymarket-US games
whose tape anchor was the settlement time rather than kickoff — excluded via
a look-ahead guard in `four_way`, conclusions unchanged); side-flip
signatures (home-win rates sane in every league; price–outcome correlation
positive in every source × league; identical-quote and exact-0.5 pairs all
book-confirmed as genuine coin flips); zombie-data scans (16.7% of minute
series are *resting books* with full observation counts, a market state, not
missing data); and a fork check — two independent pipelines pricing the same
quantity agree (horizons-at-start vs closing prices: median gap 0.5pt). Both
gates: **72 checks, 0 warnings, 0 failures.**
(`src/analysis/deep_audit.py`)

**Which Polymarket:** all Polymarket data is the **Global** platform (the
on-chain Polygon CLOB behind gamma-api/clob.polymarket.com; USDC-collateralized;
US persons officially excluded since the 2022 CFTC settlement) — *not* the
separately regulated Polymarket US entity launched later (too little history to
study). This matters twice: (1) the three-way design is genuinely
institutionally diverse — a CFTC-regulated exchange, an *offshore crypto*
market, and licensed US sportsbooks; (2) the participant pools barely overlap
(US bettors on Kalshi/books, non-US on Polymarket Global), so **three
regulatory regimes and three largely distinct crowds converge on statistically
identical prices** — the equivalence is not one population trading in three
venues. The 2026-03-30 sports fee studied in the natural experiment is the
Global platform's. **Update 2026-07-28: Polymarket US is now also studied, as
a fourth leg — see "The fourth cell" below.**

## The fourth cell: Polymarket US (2026-07-28)

Polymarket US — the same brand operating as a CFTC-regulated designated
contract market with a *legally disjoint, US-only* participant pool —
publishes a complete public execution tape (daily time-and-sales CSVs from
platform launch 2025-10-29). Closing prices = last trade at or before the
ESPN start (trade-recon methodology; staleness/fill-count quality flags),
markets mapped by slug team codes + date, priced side identified from the
catalog's long-side team and **validated against realized outcomes (97.9%
agreement on extreme closes)** — the same audit discipline as the Kalshi
ticker-order rule.

- **The dead heat extends to a fourth institution.** On the 2,639
  quality-filtered games where all four sources price the same event
  (MLB/NBA/NHL/NFL/WNBA, Nov 2025–Jul 2026; 47 games with endDate-fallback
  time anchors excluded by the deep audit's look-ahead guard): Brier
  0.2305 / 0.2306 / 0.2306 / 0.2308 (K / P-Global / book / P-US). Polymarket
  US is formally TOST-equivalent to *each* of the other three at δ=0.001
  (δ_min 0.56–0.64e-3; all clustered DM n.s., p ≥ 0.27) — despite its closes
  being last-trade prices, a noisier measure than the others' book-mids.
- **Law of one price across legally segregated pools:** |US − Global| median
  0.50pt, mean 0.77pt, >5pt in only 0.4% of games — barely wider than the
  Kalshi-vs-Global benchmark (median 0.40pt), even though no participant may
  legally trade both Polymarkets. Prices agree because both pools process the
  same public information, not because anyone arbitrages the two books: the
  strongest version yet of the shared-information mechanism.
- Caveats: ~2% of extreme-close side checks disagree (isolated
  postponement/stale cases, visible as scatter outliers); 23% of tape symbols
  didn't match ESPN (code aliases + coverage); CBB (4,387 US markets) awaits
  our own CBB expansion; one partial season, MLB-heavy.
  (`src/collect/polyus.py`, `src/analysis/four_way.py`,
  `results/four_way.png`)

## The thesis in one table (Table 1 of the report)

Of all teams priced at X%, how many actually won — same games, all three
institutions (n=5,328 games / 10,656 priced teams; `plain_calibration`):

| priced | Kalshi won | Polymarket won | Sportsbook won |
|---|---|---|---|
| 10% | 8.9% | 8.8% | 7.3% |
| 20% | 22.6% | 22.7% | 22.6% |
| 30% | 30.7% | 31.2% | 29.1% |
| 40% | 43.3% | 43.2% | 44.1% |
| 50% | 50.0% | 50.2% | 50.0% |
| 60% | 56.8% | 56.4% | 55.9% |
| 70% | 69.2% | 68.9% | 70.9% |
| 80% | 77.1% | 77.4% | 77.4% |
| 90% | 91.1% | 91.2% | 92.7% |

A $1 stake at any price level returns ≈$1.00 gross at every institution —
the fees/vig are the whole house edge. Even the small deviations are
*shared* (the mild 40/60 compression appears identically at the books):
prediction markets behave like sportsbooks at every price level, and the
formal machinery below (slopes, ECE, CORP, Murphy, TOST) exists to prove
this table is not luck. (`results/plain_calibration.png`)

## Headline: a statistical dead heat (n = 5,328, final data configuration 2026-07-31)

| | Kalshi | Polymarket | Sportsbook |
|---|---|---|---|
| Brier | 0.2196 | 0.2199 | 0.2196 |
| ECE | 0.0106 | 0.0092 | 0.0048 |
| Calibration slope (95% CI incl. 1) | 0.98 | 0.98 | 1.03 |
| Resolution (×1000) | 31.9 | 31.7 | 31.6 |

- No pairwise Diebold–Mariano difference is significant; with **date-clustered SEs**
  (383 clusters): p = 0.15 / 0.26 / 0.54.
- **TOST equivalence:** every pairwise ΔBrier 90% CI lies within ±0.00052 → the three
  sources are formally *equivalent* at margin δ = 0.001 Brier (≈0.5% per-game
  probability error).
- **Per-league TOST (2026-07-21):** equivalence at δ=0.001 also holds formally
  *within each* of the three big leagues — all 9 pairwise CIs in MLB/NBA/NHL
  (n≥1,206 each) sit inside ±0.84e-3. CFB/WNBA/NFL show no detectable
  differences but are underpowered for the formal claim (δ_min 0.94–2.6e-3) —
  report as "consistent, not established." **Sharpness is equal too**: mean
  p(1−p) within 0.002 pooled (exchanges fractionally *sharper* than the book
  consensus in every league) — equally informative, not just equally
  calibrated; calibration alone could be gamed by hedging to the base rate,
  identical sharpness + identical Brier cannot. (`src/analysis/league_tost.py`)
- **Power, so the nulls can be read (2026-08-10, `src/analysis/power.py`).**
  Minimum detectable effect at α=.05 / 80% power, computed from the same
  date-clustered SE the DM tests use, against the δ=1e-3 margin:
  - **Pooled the equivalence is genuinely powered**: MDE 0.36–0.51e-3 across
    the three pairs, i.e. roughly a third to half the margin we declare
    equivalence at. A true gap of 0.4e-3 — a forecaster mispricing every game
    by about 2pt in a fixed direction — would have been caught.
  - **MLB, NBA and NHL are individually powered** (worst-pair MDE 0.58 / 0.95 /
    0.64e-3). Their per-league nulls carry information.
  - **CFB (2.74e-3) and WNBA (2.47e-3) are not, and NFL (1.57e-3) is not
    either.** They would need ~7.5×, ~6× and ~2.5× their current games to
    reach MDE=δ. Their nulls are *consistent with* equivalence and cannot
    establish it — the report says so wherever they appear.
  Note δ_min (league_tost) and MDE answer different questions: δ_min is how
  wide the realized CI happened to be, MDE is how wide it would need to be to
  catch a true effect. A subgroup can read "EQUIV" on a lucky near-zero point
  estimate while still being underpowered — which is exactly why both are
  reported.
- Robust to de-vig method (Shin vs multiplicative: book Brier 0.2181→0.2182,
  conclusions unchanged).
- Figure: `results/three_way_calibration.png`.

## The gambling scorecard

| Facet | Gambling would predict | Found |
|---|---|---|
| Calibration | biased prices | well-calibrated, all sources, full 0–1 range |
| Favorite–longshot bias | longshots overpriced | none — all slope CIs include 1; ladder longshots if anything *under*priced |
| Information content | none | resolution equal to professional books |
| Internal coherence | incoherent ladders | 97.3% perfectly monotone; executable arbitrage in 0.10% (0.05% live-book) |
| Distributional accuracy | wrong shapes | PIT uniform in NBA (p=.33), NHL (p=.23), WNBA (p=.42); **MLB rejects (p<.001)** |
| Exploitability | beatable | no strategy clears costs; divergence-chasing loses 38% |
| House edge | high take | Kalshi ~1.0% vs sportsbook ~4.2% overround |

Supporting figures: `spread_coherence.png`, `margin_pit.png`, `profitability.png`,
`kalshi_nuance.png`.

## Why sports? The platform pathologies vanish where a benchmark exists (2026-07-24)

Bürgi–Deng–Whelan ("Makers and Takers: The Economics of the Kalshi Prediction
Market," Jan 2026) document, on transaction data covering *all* Kalshi
categories 2021–Apr 2025 (sports launched too late to be in their sample): a
strong favorite–longshot bias (sub-10c contracts lose >60% of stake), average
contract ROI ≈ **−20%**, and makers out-earning takers. Replicating their
analyses on our sports data:

- **The FLB cliff is absent in sports.** Hold-to-settlement return by price
  bucket: moneylines at mid **−0.45%** overall (se 0.11, game-clustered,
  n=17,821 sides); at ask + taker fee −4.6%; spread ladders at ask + fee
  −5.8% — every bucket from 10c up sits in the 0 to −8% cost band, versus
  their −20% platform average. The single BDW-like point (sub-10c moneylines,
  −70%) is confined to **trade-recon prices on thin college longshots**
  (570 of 571 sides are reconstruction-sourced, 85% CBB/CFB; one-sided
  longshot prints overstate reconstructed mids). Live order books quote almost
  no sub-10c moneylines, and the live-book-heavy ladder tail shows no cliff
  (−8% ± 36, n.s.) — consistent with the earlier ladder-tail finding that
  longshots are, if anything, slightly *under*priced.
- **Makers > takers replicates qualitatively:** realized ROI on the final-24h
  fill sample (709K fills, 512 games): takers −5.0% gross / −7.7% net of fee,
  makers +5.6% (individually n.s. with game clustering; the maker−taker wedge
  is the structural spread+fee). Caveat: home-side tickers only, and takers
  are 94% yes-side — the sample is mostly home-backers' market orders.
- **Reading:** BDW's platform-wide pathologies are absent precisely in the
  corner of Kalshi that has (a) a professional pricing benchmark ecosystem
  (the books) and (b) thousands of rapidly resolving, repeated, statistically
  tractable events. Sports is what a prediction market looks like when that
  discipline is available — the sharpest mechanism evidence yet for the
  institutional thesis, and it turns the paper's benchmark design into an
  explanation, not just a comparison.
  (`src/analysis/why_sports.py`, `results/why_sports.png`)

## Notable nuances

1. **MLB margin distributions are miscalibrated** (PIT KS=0.072, p<0.001, unbiased in
   location) — and the mechanism is now partly identified. Baseball's ending rules
   concentrate finals at a margin of exactly 1: extra-inning games (8.6% of games,
   ghost-runner era) end within one run **70%** of the time (home wins in extras:
   88% by exactly 1) vs 25% in regulation. In the run-line "win by 1–2" cell the
   market implies 14.6% in extras games that empirically hit 44.5% (+29.9pts,
   z=8.9); extras account for ~24% of the cell's total +8.4pt under-pricing, with
   a broad +6.4pt under-pricing of small margins remaining even in regulation.
   Notably the market prices the home/away walk-off *asymmetry* in the right
   direction (implied 17.3% home vs 11.6% away) — the level is wrong, not the
   shape's direction. (`src/analysis/mlb_extras.py`)
   **Cross-source verdict: the blind spot is Kalshi-specific.** On the same games
   and rungs, the books' alternate run lines price the cell almost perfectly
   (implied 22.6% vs empirical 23.0%, gap +0.4pts, z=0.5; robust to requiring
   ≥3 books), while Kalshi misses by +8.4pts (z=10). This is the first clean
   Kalshi-vs-books divergence found anywhere in the project — and it lives in
   the thin derivative ladders, not the liquid moneylines. Same pattern in tail
   calibration on 20,363 identical contracts: book ECE 0.0069 vs Kalshi 0.0195
   (Brier 0.1764 vs 0.1785). NBA ladders show no such gap (±1–2pts).
   (`src/analysis/ladder_vs_books.py`, sportsbook alternate spreads for 2,480
   MLB/NBA ladder games)
   Two completions of this story: **(a) the books' full margin distributions
   pass the same PIT that rejects Kalshi's** (tie-consistent PIT, corrected
   2026-07-30: book MLB KS p=0.084, NBA p=0.165 vs Kalshi MLB p<0.001 — the
   earlier p=0.46 for MLB was inflated by strict-inequality tie handling on
   integer lines; the pass is now marginal but the contrast with Kalshi's
   decisive rejection stands) (`src/analysis/book_pit.py`); **(b) the mispricing is
   unexploitable**: selling the over-priced "win by 3+" contracts at the bid,
   fees included, loses 2.9–4.5% (date-clustered z −2.3 to −4.6; robust to
   live-book-only quotes) — the bias is harbored inside Kalshi's transaction-
   cost band exactly as books harbor biases inside their vig, which is *why* it
   persists (`src/analysis/ladder_cost.py`).
2. **Forecast encompassing — a whisper that faded as the sample grew
   (downgraded 2026-07-30).** On the Jul-10 master, Kalshi's price appeared to
   carry information beyond the book (LR p=0.004) and beyond Polymarket
   (p=0.013), concentrated in the NBA (p=0.006). The code review caught that
   these numbers were stale: **on the current, larger and cleaner master the
   whisper is borderline at best — Kalshi-beyond-book clustered p=0.054
   (drops under BH at q=0.05), Kalshi-beyond-Polymarket clustered p=0.044
   (fragile), and the NBA-concentration sub-claim is retracted outright
   (p=0.145).** What survives: neither the book nor Polymarket adds
   information beyond Kalshi at any sample size, and the increment — if real
   — is economically negligible (DM accuracy gain n.s.; liquid-game Briers
   identical to 4 decimals). Treat as suggestive only; the honest headline is
   *mutual encompassing*, not a crowd edge. Policy note: we now cite the
   date-clustered p (the conservative choice) rather than the LR p
   everywhere in this family. (`src/analysis/encompassing.py`)
   **The whisper is carried by late order flow.** Decomposing Kalshi's close
   into a 24h-out level plus the final-day movement (trade-path panel, n=3,314
   games with ≥10 trades): the flow term predicts outcomes beyond the closing
   book line (clustered z=3.43, p=0.001 after the horizon re-fill), and model-free, final-24h moves of ≥3pts point
   toward the eventual winner 57.9% of the time (n=978). The effect again
   concentrates where book quotes are freshest — not a staleness artifact.
   What traders do on the exchange in the last day is genuinely informative.
   (`src/analysis/late_flow.py`)
   **…but the carrier is quote revision, not aggressive flow.** On 710,176
   per-fill trades (516 games, all 7 leagues): markout-to-close is a flat
   −0.3 to −0.4pt across every trade-size quintile (3-contract lots to
   1,100-contract blocks) — no size class beats the close, all pay the spread —
   and game-level taker imbalance (large or small) predicts nothing beyond the
   book line (p=0.80/0.48). Prices move informatively while aggressive flow
   carries no signal ⇒ price discovery is **maker-driven**: the informed side
   is the passive side re-pricing its quotes. Coheres with the cost structure
   (makers trade ~free; takers pay ~spread+fee for immediacy and gain no edge).
   (`src/collect/kalshi_trades.py`, `src/analysis/informed.py`)
3. **Lead–lag (two-week VPS panel, 210 games, 10.2k complete 15-min steps,
   2026-07-21):** 15-min changes stay nearly uncorrelated contemporaneously
   (r=0.03–0.09). The first-pass "book momentum" was an artifact of the 3-day
   sample — it vanishes with data (own-lag z=−0.3); books are simply stickier
   (>0.4pt move in 4.4% of steps vs ~8–10% on the exchanges). Cross-venue
   Granger terms are statistically real but economically tiny: the exchanges
   predict each other, while nothing significantly predicts
   the book's next move (z≤+1.2) — yet every
   coefficient is ~0.03, i.e. ~3% of a move transmits one step ahead. Event
   study on big moves (|d|≥2pts; n=65–123 events per source): the other
   venues' signed response concentrates at offset 0 (+0.35–0.74pt within the
   same 15-min step), ≈0 before, ≤0.2pt after — **big repricings are
   simultaneous at 15-min resolution; no venue front-runs another**. Coheres
   with the T−24h horizon result (books fractionally ahead, gap closed by
   start) and with maker-driven discovery on public news.
   **Panel refresh 2026-08-10 (528 games, 23.9k complete steps):** the
   cross-venue terms partly dissolved as the sample grew — only P→K survives
   (+0.031, z=+4.4); **the book→Poly term this section previously reported is
   now −0.004 (z=−0.1) and is retired**, and the FDR entry has been rewritten
   accordingly. Nothing predicts the book (all |z|≤0.9). The event-study
   picture is unchanged and sharper: every venue's response to every other
   concentrates at offset 0 (n=122–328 events).
   (`src/analysis/lead_lag.py`)
   **Book-line-move event study (refreshed 2026-08-10, 528-game panel):**
   around the 70 book-consensus jumps of ≥2pts (mean 4.1pts), the exchanges'
   anticipation-direction share is 34% for Kalshi (sign-test p=0.012, now
   significant — it was 37%, p=0.076, on the 347-game panel) and 23% for
   Polymarket (p<0.001): **both significantly below chance — before a book
   move the exchanges are, if anything, drifting the other way.** The
   same-step/no-chase shape is unchanged. Original pass (2026-07-31,
   347-game panel) for reference: around the
   54 book-consensus jumps of ≥2pts (mean 4.6pts), the exchanges' *total*
   response over ±1h is only ~1pt (Kalshi +1.03, Poly +0.69) — ~80% of a big
   book move is never echoed by the exchanges at all. What is echoed arrives
   almost entirely in the same 15-min step (Kalshi +0.80, Poly +0.82 at
   offset 0), with slight reversal after (−0.2 to −0.35) and **no systematic
   anticipation**: the share of events where an exchange had already drifted
   the book's way is 37% for Kalshi (p=0.076) and 21% for Polymarket
   (p<0.001) — significantly *below* chance for Poly. The mirror study is
   symmetric: around Kalshi jumps ≥2pts the book's total response is +1.15pt
   (70% same-step, +0.57 follow-through). Reading: big single-venue moves are
   mostly venue-specific (book-panel composition and flow management on the
   consensus side; idiosyncratic exchange flow on the other) — the *shared*
   news component is small and repriced everywhere within one step. The
   exchanges neither foresee nor chase the books' line moves; they filter
   them. Caveat: consensus jumps can partly reflect which books happen to be
   quoting (composition), which the muted exchange response is itself
   evidence of. (`src/analysis/book_moves.py`, `results/book_moves.png`)
   **Minute-level completion (2026-07-24; 563 post-cutoff games, 202K 1-min
   changes, final 6h, exchanges only):** at 60× finer resolution the
   simultaneity resolves into a **symmetric few-minute echo** — each
   exchange's last 5 minutes predict the other's next move with nearly
   identical strength (sum-coef +0.092/+0.096, z=+7.1/+7.7; bidirectional),
   the cross-correlogram hump lives within ±2 minutes (corr 0.030 at +1
   vs 0.021 at −1), and in the 23 joint ≥1.5pt repricing episodes the venues
   cross half their move in the *same minute* (median lead 0.0; Kalshi-first
   39%, ties 17%; sign-test p=1.0; a 2026-07-30 sign-convention fix corrected
   the direction labels — the symmetric-null conclusion is unchanged).
   Interpretation caveat (2026-08-01): part of the few-minute echo may be
   *print timing* rather than information diffusion (thin markets record the
   common move when they next trade — nonsynchronous-trading bias). This
   cannot manufacture the null: stale prints create symmetric echo, while a
   true leader would still show asymmetric cross-prediction — and the
   symmetry (0.092 vs 0.096) is the finding. Measured biases run *against*
   the books (live feed verified fresh — median quote age 0.6 min — but
   consensus-composition noise attenuates measured book leadership), so
   "books lead slightly, exchanges never lead" is if anything understated.
   **No leader–follower relay at any resolution
   measured.** Scheduled-news check: MLB intensity shows no discrete
   lineup-window burst (T−4h→T−1.5h flat ≈0.007pt/min at both venues;
   per-game release-time variation may smear one) — repricing ramps into the
   final 75 minutes instead, in lockstep; the 5pm-ET injury-report hour
   (NBA/WNBA, n=78) is suggestive only. (`src/collect/minute_paths.py`,
   `src/analysis/minute_lead_lag.py`, `results/minute_lead_lag.png`)
   **The last open cell is now closed (2026-08-10, `src/analysis/five_min.py`,
   `results/five_min.png`).** The VPS cron moved to */5 on 2026-07-31, so
   book-vs-exchange can finally be read below a quarter of an hour: 181 games,
   19,272 five-minute steps with all three venues.
   (a) *Resolution ladder* — the same battery on the same games at 5/10/15/30
   min. A genuine lead is a fixed wall-clock delay and must sharpen as the grid
   approaches it; none does (every cross-lag correlation sits in +0.006…+0.059
   with no monotone pattern), and nothing predicts the book at any grid. **The
   no-leader result is not a resolution artifact.**
   (b) What the finer clock *does* reveal is a small one-step book→exchange
   coefficient invisible at 15 min: Kalshi +0.047 (z=+2.4), Polymarket +0.164
   (z=+4.5), game-clustered. Three cuts identify it as drift alignment rather
   than news transmission: it is **exactly zero in the final two hours before
   start** (K +0.006 z=+0.1; P −0.008 z=−0.1) — the window where information
   actually arrives and where every headline horizon result lives; it lives in
   sub-half-point book moves, not news-sized ones (the ≥0.5pt cut has only 192
   steps — the consensus is that sticky); and for Polymarket it is as strong
   from a quote frozen for 30 minutes (+0.176) as from an active one (+0.138),
   which is catch-up, not response. Kalshi, by contrast, only responds when its
   quote is already awake (+0.089 vs +0.001) — a real if tiny repricing.
   (c) *Event study on the fine clock.* A 2pt book move essentially never lands
   in one 5-min step, so events are defined on the book's rolling 15-min change
   and responses read at 5-min resolution (n=19 — suggestive, not a claim):
   the exchanges are already moving **during** the book's window, and 31–38% of
   their (small) total arrives in the following half hour. The 15-min study's
   "same step" was not hiding a lag.
4. **The price of immediacy (2026-08-10, `src/analysis/immediacy.py`,
   `results/immediacy.png`; 66,996 book snapshots, 274 games since the
   2026-07-25 depth deployment).** Every cost number elsewhere in this document
   is a *touch* number. The depth captures give a two-anchor execution curve
   (size at the touch, size resting within 5¢) and answer what capacity sits
   behind the quote.
   - **Immediacy is free at the size the market is actually traded in.** Median
     cost is half the tick — 0.50¢, ≈0.9% of notional — for orders up to 10,000
     units on both venues. The median customer order from the fills tape (30
     contracts, ~$16 at stake) sits **inside the touch in 89% of Kalshi
     snapshots and 95% of Polymarket's**. For the customer this project
     measures, depth is never the binding cost; the spread and the fee are.
     This is the missing justification for treating the −4.2% taker figure as
     the whole retail story.
   - **Capacity, not price, is what runs out.** Cost stays near the half-spread
     as size grows, but the share of books that can absorb the order collapses:
     Kalshi fills a 10,000-unit order inside 5¢ in 61% of snapshots, 50,000 in
     44%, 200,000 in 36%; Polymarket 96% / 67% / 21%. Polymarket's cost also
     rises where Kalshi's does not (0.86¢ at 50K, 1.64¢ at 200K).
   - **The venues invert as the game approaches.** A day out Polymarket is far
     deeper (median 107.7K units within 5¢ vs Kalshi's 17.9K); inside 30
     minutes Kalshi is five times deeper than Polymarket (377K vs 76K). The
     raw cross-bucket table overstates this — the late buckets contain a more
     liquid mix of games — so the ramp is measured **within game**: Kalshi
     late/early depth ratio 2.29× (deeper late in 87% of 235 games),
     Polymarket 1.58× (62% of 233). Both thicken; Kalshi's professional
     complex ramps roughly twice as hard, which is the microstructure
     counterpart of the liquidity-footprint and maker-structure results.
   - **Touch asymmetry replicates the two-layer book.** A ≤10-unit order is the
     best quote on some side in 22.4% of Kalshi snapshots but only 1.9% of
     Polymarket's; Kalshi's touch imbalance (0.21) departs from its 5¢-band
     imbalance (0.27) while Polymarket's are both ≈0.5. Kalshi wears a
     retail-sized surface over a professional layer; Polymarket's touch is
     itself professional-sized.
5. **Cost asymmetry — 3-venue table now complete**: sportsbook overround ~4.2%
   everywhere; Kalshi bid/ask overround ~1.0%; and Polymarket's archived books
   (OddPool, n=93 games, all four in-season leagues) show a median quoted spread
   of exactly 1.00pt — equal to Kalshi's on the same games. Both exchanges are
   ~4× tighter than the books at the quote. All-in for a market-order taker
   (spread + fees): Polymarket ~1.25–1.75% < Kalshi ≈ books ~4.2%; makers trade
   ~free on both exchanges, a path books don't offer. Bonus validation: the
   archived Polymarket book mids match our CLOB-derived closing prices with
   median error 0.00pts — both prediction-market price pipelines are now
   independently confirmed against external archives.
6. **The ordinary gambler's ROI** on Kalshi: −3 to −4.5% across strategies
   (everything/favorites/longshots/home) ≈ transaction costs. Efficient market, not
   a beatable casino — and also not a rigged one.
7. **Thin markets are noisier**: Kalshi calibration error rises sharply with quoted
   spread (ECE 0.013 tight → 0.11 wide; reliability 0.25 → 18.1 ×1000; reruns
   2026-07-10 and 2026-07-21 on the re-harvested master), but thin markets do not
   drive any headline result: on liquid
   games only (spread ≤ 1¢, n=4,374) all three sources have Brier 0.2186 and every
   pairwise clustered DM is n.s. (p ≥ 0.45). This formally retires the pre-side-fix
   "Kalshi lags even on liquid games (p=0.004)" result — it was contamination.

## Who bears the Polymarket sports fee? (liquidity incidence, 2026-07-24)

The fee natural experiment's accuracy half was null (DiD p=0.74). The economic
half, on NBA/NHL games priced by both exchanges (Feb 2–May 25, within-game
volume pairing):

- **Incidence fell on taker volume, not on the price of liquidity.** The
  within-game ratio log(Poly volume) − log(Kalshi volume) fell **−0.53
  log-pts (−41%, date-clustered z=−3.6)** between the complete-coverage
  windows (Feb vs Apr–May); mid-Feb placebo split is null (z=+1.3). The
  event-time path shows a *trend break at the fee date*: flat through
  February, sustained decline from Mar 30 onward. Levels (descriptive):
  Kalshi final-24h notional +51% into the playoffs, Poly −10% on the same
  games.
- **The quoted touch never moved**: archived order books (OddPool) show the
  Polymarket spread at T−30m pinned at the 1¢ minimum tick both eras (pre-fee
  median 1.0pt n=30, post 1.0pt n=21, Mann–Whitney p=0.43; July's
  independent 93-game measurement also 1.0pt). The +25% maker rebate
  plausibly held quoting steady — and at one tick the spread had no room to
  narrow.
- **Reading:** fees moved *quantity*, not price quality (fee_experiment) or
  the *price of liquidity* — the marginal taker left, the makers stayed.
  Coheres with maker-driven price discovery.
- Caveats, stated plainly: gamma strips volume from most archived March
  markets (coverage 100% Feb, 7–57% Mar, 100% post), so March is excluded
  and the windows straddle the playoff transition; Kalshi's secular growth
  cannot be fully separated from fee-driven migration, though the flat
  February pre-trend and the break's timing both point at the fee.
  (`src/collect/fee_volumes.py`, `src/analysis/fee_liquidity.py`,
  `results/fee_liquidity.png`)

## Decimal pricing: the tick, not the trader, sets the price of liquidity (2026-07-25)

Tick regimes probed from the live APIs: **Kalshi sports markets are
`linear_cent` — a uniform 1¢ tick over the entire [0,1] range, ladders
included; Polymarket runs dynamic ticks** (0.01 mid-range,
`orderPriceMinTickSize` = 0.001 on extreme-priced markets, sub-cent quotes
observed live). Measured on our stored quotes:

- **The touch is the tick.** 97% of Kalshi live-book moneyline quotes
  (n=2,784 sides) and 96% of stored Polymarket books (n=144) sit at *exactly*
  one tick. The quoted spread in the liquid range is a censored bound, not an
  equilibrium choice — which retro-sharpens two earlier results: the fee
  experiment's "spread unchanged" is a statement about a binding floor (the
  free margins were volume, −41%, and depth), and cross-venue "median spread
  1.0pt on both" partly reflects shared tick design rather than equally
  aggressive quoting.
- **The tick tax.** Kalshi ladder rungs hug the 1¢ floor at every price
  level (68–78% at-tick), so the *relative* spread rises mechanically as
  price falls: 2.6% of price mid-range → 15.4% at 5–10¢ → 28.6% at 1–5¢
  (floor: 25%). In Polymarket's 0.001 regime the same floor is ~1–2.5% —
  a tenfold difference in the structural cost of tail trading, set by
  exchange design. Stored Poly moneyline quotes are almost entirely on the
  cent grid (off-grid 0.7% — a 2026-07-30 fix corrected an earlier 14.6%
  figure caused by a float-modulo bug), consistent with the 0.001 regime
  applying only at price extremes.
- **Implication for the cost-band thesis:** the band that shelters Kalshi's
  MLB tail bias is partly *tick-made* — a finer tail tick (Polymarket-style
  tiering) would compress it and, by the paper's own logic, force tail
  prices closer to true probabilities. A concrete institutional-design
  recommendation for the synthesis.
  (`src/analysis/tick_pricing.py`, `results/tick_pricing.png`)

## The market premium over public statistics (model leg, 2026-07-24)

A deliberately naive fourth forecaster — walk-forward Elo per league built
from ESPN win/loss results only (K=20, expanding-window home advantage,
season-gap regression, burn-in thresholds; no look-ahead anywhere) —
evaluated on the same clean three-way games (n=4,627):

- **The markets beat the public-statistics floor decisively — and
  identically.** Model Brier 0.2348 vs 0.2209/0.2210/0.2210: ΔBrier ≈ +14e-3
  against every source (date-clustered z ≈ +7.4, p<0.0001). The three market
  institutions differ from each other by ≤0.5e-3 (n.s.; TOST-equivalent) —
  they sit ~28× closer to one another than to the model. One line: **equally
  good, and equally better than public statistics.**
- **The naive model is calibrated but not sharp** (slope 0.976, CI incl. 1;
  ECE 0.033). Calibration is cheap; the markets' value-add is discrimination.
- **Per-league premium tracks where information lives**: largest in CFB
  (+56e-3 — 1.3 seasons of won-lost records cannot learn hundreds of college
  teams; the markets import rich priors), smallest in NHL (+4.4e-3) and MLB
  (+6.7e-3), the low-resolution sports.
- **Encompassing**: the book fully encompasses the model (model weight z=+0.6
  given the book — public W/L records retain *nothing*); Kalshi still adds
  beyond model+book (z=+2.7). The information hierarchy: public statistics ⊂
  books ⊂ books + exchange late flow.
- Robust to K∈{10, 32} (model Brier 0.2352–0.2369; conclusions unchanged).
  (`src/analysis/model_benchmark.py`, `results/model_benchmark.png`)

## When does the dead heat form? (open vs close, n=2,901 constant sample; horizon re-fill 2026-07-30)

At **T−24h** the books hold a small, statistically real accuracy lead over
Kalshi (ΔBrier +0.69e-3, date-clustered z=+2.32, p=0.020 after the 2026-07-30
horizon re-fill restored the most-liquid games the old 2-page fill cap had
dropped — the claim *strengthened* with the selection fixed); Polymarket sits
between (n.s. vs both). By **game start** all three are identical on the same
games (0.2125 / 0.2123 / 0.2124). Both exchanges sharpen monotonically through
the final day; cross-source price gaps contract (|K−book| 1.26→1.10pts,
|P−book| 0.97→0.89, |K−P| 1.08→0.88); the books themselves also move (mean
1.76pts, Brier improvement −0.66e-3, n.s.). Reading: **the equivalence is
built during the final day** — the exchanges start slightly behind the
professionals and close the gap by start, while their own late flow contributes
genuine information (see the encompassing/late-flow nuance). Caveats: single
test at p=0.03; constant sample skews toward early-listed, actively-traded
games (NHL/CFB-heavy); book T−24h listing coverage 63%.
Data: `sportsbook_open_prices.csv` (T−24h consensus, 3,461 games, ~24.5K
credits), `poly_horizons.csv` (CLOB minute-paths, 5,410 games).
(`src/analysis/horizon_equivalence.py`)

Two completions (2026-07-11, same constant sample): **(a) all three closes are
efficient** — the day's own move predicts nothing given the close (book move
term p=0.99(!), Kalshi p=0.35, Poly p=0.52): no line-move anomaly anywhere;
**(b) the Kalshi whisper does not exist at T−24h** (weight −0.22, p=0.68 — a
day out the books fully encompass both exchanges). The exchange's incremental
information is *created during the final day*, the same window in which it
closes the accuracy gap. (`src/analysis/close_efficiency.py`)

**Comparative sharpening (2026-07-21; re-filled 2026-07-30, n=2,901).** The
full 7-horizon Brier curves on the joint constant sample make the Page–Clemen replication comparative:
both exchanges sharpen essentially monotonically (Kalshi 0.2138→0.2125,
Polymarket 0.2134→0.2123) and are statistically indistinguishable at every
horizon (all date-clustered |z| ≤ 1.8; smallest p=0.077 at 12h, favoring Poly)
— **the dead heat holds along the whole final-day path**, not just at the
close. Mean |24h→start| move is 2.0pts on both venues; book reference on the
same games 0.2130 (T−24h) → 0.2124 (close).
(`src/analysis/horizon_cross.py`, `results/horizon_cross.png`)

## The affiliated dealer inside the exchange (2026-08-04)

Kalshi's own affiliate, Kalshi Trading, has traded on KalshiEX since June
2021 — posting passive orders and aggressing — with the exchange's CEO
and COO on both boards. A CFTC rule proposal issued 2026-07-30 would
formalize the arrangement for roughly eight such affiliated market makers
across prediction markets (Kalshi Trading; SIG's stake in Rothera on
Polymarket; CME/FanDuel; DraftKings): affiliates may make markets but
must be "bona fide" — continuous two-sided quotes, no directional
positions beyond what quoting requires, and fills subordinated to
unaffiliated traders at every price level.

This matters for the thesis in both directions. It SOFTENS the cleanest
institutional line — part of the "peer-to-peer" book is structurally the
house — and our depth captures show what that book looks like
(`src/analysis/maker_structure.py`, 4,533 snapshots, 93 games): a
two-layer structure where the touch is thin and asymmetric (a
<=10-contract retail order is the best quote on one side in 20% of
snapshots) while ~20K contracts per side stand within 5c — 11x the
touch, twice as balanced, ~2M contracts standing across ~90 games at
once. Standing two-sided size at that scale is professional market
making, not organic peer supply. Takers surrender ~5% of stake to
settlement and this quoting layer collects it: dealer-like revenue
inside a peer-to-peer shell. But it also SUPPORTS the distinction: the
bona fide restrictions are precisely what a bookmaker is NOT subject to
— the affiliate may not take a directional view against its customers,
where taking that view is a sportsbook's entire business model. The
honest statement: the exchange-vs-house line is not about who supplies
liquidity (professionals do, in both institutions, affiliate included);
it is about whether the liquidity supplier is permitted a directional
book. Public trade data carries no member IDs, so Kalshi Trading's own
share of the quoting layer cannot be measured from outside — a stated
limitation, and the one place the paper must rely on the documentary
record (KalshiEX rulebook; CFTC proposal of 2026-07-30) rather than
measurement.

## The books Americans use: per-book US record (2026-08-05)

The credit endgame banked the per-book US closing record before the
subscription lapses (`src/collect/sportsbook_us_books.py`, 4,664 games
= 86% of the joint set, 11 books, ~23.9K credits; seeded-shuffle bucket
order, floor-stopped at the live-feed reserve). Three closures (`src/analysis/us_books.py`):

1. **No Levitt shading at the US retail books either.** Deviation from
   Pinnacle on home favorites: DraftKings -0.08pt, FanDuel -0.15pt,
   BetMGM -0.13pt; all 11 books between -0.22 and -0.01pt — magnitudes
   near zero and the SIGN is opposite to bias-exploitation. With the EU
   table, shading is now dead at 30+ books on two continents including
   every major US brand.
2. **The dead heat holds book by book.** Every individual US book ties
   Kalshi on clustered DM (|z| <= 1.9, all n.s.; book Briers 0.2195 to
   0.2239). The equivalence was never an averaging artifact.
3. **Dispersion**: median cross-book range 2.0pt; Kalshi prices inside
   the US-book envelope in 70% of games.

## How markets FUNCTION with and without the complex (2026-08-05)

Same niche-league matches (Brasileiro, Eliteserien, NRL), three
institutions, measured head-to-head (`src/analysis/market_functioning.py`;
book leg `src/collect/niche_books.py`, ~2.8K credits, EU/Pinnacle):

| | books | Polymarket | Kalshi |
|---|---|---|---|
| presence (287 settled matches) | 55-85% quoted, 16-23 books/match (name-match lower bound) | 55-68% listed, **$203K median volume** | prices form on 14% |
| price vs book consensus | — | 1.5pt | **4.2pt** (covered leagues: 0.7pt) |
| cost of functioning | 7.1% vig (vs ~4% covered) | taker fee ~1% | 1c spread where quoted |

Three lessons. (1) **Presence follows the complex/clientele, not the
sport**: Polymarket's Brazilian user base gives it six-figure volume on
matches where Kalshi's book never prints — the two exchanges chose
different tails, so "exchanges can't do niche" is false; THIS exchange's
complex didn't deploy here. (2) **Precision follows the professional
book**: Kalshi's thin-tail prints sit 4.2pt from consensus, six times
the covered-league 0.7pt, while its pooled calibration there is still
unbiased (slope 0.98, gradient leg) — repetition keeps prices right on
average, the liquidity complex compresses the noise around them. (3)
**The books' price of functioning everywhere is vig**: their niche
overround is 7.2% vs ~4% on covered leagues. Combined with the
mm_involvement result, the decomposition of market quality is now:
repetition → unbiasedness; MM complex → existence and precision;
institution type → what you pay for it.

## "Betting against the house": testing the MPU/class-action claim (2026-08-04)

The More Perfect Union investigation and the 2025-26 class actions
(nationwide Nov 2025; KY/IL/OH and others, funded by Veridis Management
under Statute-of-Anne recovery theories) allege that Kalshi customers
unknowingly wager against "the house" — Kalshi Trading LLC and partner
market makers like Susquehanna — rather than against peers. None of the
sources names WHICH markets; the complaints allege the MM complex stands
in essentially every sports contract, and member IDs are private, so
"affiliate vs no affiliate" is unobservable. What IS observable is the
footprint contrast (professional book present vs absent), and the
lawsuits imply a testable prediction: customers should fare better away
from the house's book.

They do not (`src/analysis/mm_involvement.py`, 43,080 niche fills
collected for the test): takers held to settlement lost **5.0% gross /
7.7% net where the MM complex stands ($95.7M staked) and 7.1% / 10.0%
where it does not ($1.8M)** — the difference is inside the cluster SEs,
so the supportable claim is "no better, possibly worse." The first-order
effect of the house's absence is quantity: only 218 of 962 niche
contracts saw a single pre-start fill. Literature anchor: Burgi, Deng &
Whelan's follow-up ("Makers and Takers," Jan 2026) finds makers earn
more than takers platform-wide — consistent with our maker-driven price
formation and taker-pays results. The paper's framing: the house's
presence is what makes there be a price at all; what it costs is the
same ~5% a sportsbook charges; whether that is "betting the house" or
"liquidity provision" is precisely the question the CFTC's bona fide MM
proposal exists to answer.

## The footprint: where the liquidity complex actually stands (2026-08-04)

Kalshi discloses THAT its affiliate trades (Sept 2021 emergency rule
filing; rulebook; the CFTC 2026-07-30 proposal) but publishes no
market-level roster — and its Liquidity Incentive Program filing (Aug
2025, effective through Sept 2026, i.e. spanning our sample) shows a
second channel: per-second-snapshot rewards for resting orders near the
touch, open to everyone EXCEPT the affiliate and formal Market Maker
Agreement firms, who are paid under separate private agreements. So the
WHO is unobservable; the WHERE is not. A full-exchange sweep (784,617
open markets, 2026-08-04; `src/collect/kalshi_liquidity_sweep.py`) plus
a signed orderbook survey of the top-volume markets per class
(`src/analysis/liquidity_footprint.py`):

- **Covered-league games**: 100% two-sided, 1c spreads, median ~$817K
  standing within 5c per market.
- **Niche games**: 90-99% two-sided but at 1/100th the size (~$6K) —
  and, per the gradient leg, calibrated anyway.
- **Sports outrights**: headline fields carry real depth (~$235K median
  among top-volume) yet are miscalibrated ($0.33/$1 longshots); 74% of
  the outright tail has no two-sided book at all.
- **The fee menu prices the same gradient**: covered games are
  `quadratic_with_maker_fees` (makers PAY — supply is abundant), while
  niche games, outrights, and politics are `quadratic` (makers free —
  supply needs coaxing). The exchange's own price list tells you where
  liquidity provision is inframarginal.

This closes a confounder: the futures pathology is not a thin-book
artifact (the big outright fields have deep books and fail anyway), and
niche calibration is not a deep-book product (those books are tiny). The
liquidity complex deploys where flow is; calibration follows repetition.
API note: `liquidity_dollars` is served zeroed everywhere (list and
detail) — depth requires the signed orderbook endpoint.

## Against the sharp book itself: the dead heat's strongest test (2026-08-04)

The paper's benchmark had been a US retail consensus with per-book quotes
discarded. An EU-region re-collection of the full joint set's closing
buckets (`src/collect/sportsbook_sharp.py`, 24 books per game kept,
n=5,294 with Pinnacle) upgrades the comparison three ways
(`src/analysis/sharp_books.py`, `logs/sharp_books.log`):

**1. Equivalence survives Pinnacle.** Against the academic-standard sharp
book specifically: Kalshi ΔBrier −0.12e-3 (z=−0.93), Polymarket −0.03e-3,
US retail consensus −0.08e-3 — every pairwise 90% CI inside ±0.34e-3,
formally equivalent at the paper's δ=1e-3. The dead heat is not an
artifact of averaging soft books; the exchanges match the sharpest price
in the market.

**2. Exchanges are a family.** Mean |price gap|: Kalshi sits 0.55pt from
Betfair Exchange but 0.71-0.72pt from Pinnacle and US retail; Polymarket
0.59 vs 0.80. The three peer-to-peer mechanisms (Kalshi, Polymarket,
Betfair) cluster with each other more tightly than with any bookmaker —
institutional design leaves a visible fingerprint on prices even when
accuracy is identical. Betfair's Brier ties everyone on its subsample
(n=3,728).

**3. No economically meaningful Levitt shading.** Per-book deviation from
Pinnacle on home favorites spans −0.49pt (Nordic books) to +0.88pt
(tipico_de) — directionally a hint of favorite-shading at some retail
books, but sub-1pt everywhere, an order of magnitude below classic
line-shading claims. The modern retail book prices off the sharp line,
not off its customers' biases; its revenue lives in the vig, same as the
exchange's fee schedule.

## The mechanism, isolated: repetition disciplines, benchmarks don't (2026-08-04)

Two free legs and one purchased leg completed the futures 2x2 and revised
the mechanism story. The earlier framing — "benchmarked, repeated markets
are disciplined" — bundled three ingredients (benchmark presence,
repetition, fast resolution). Today's evidence separates them:

**1. Niche game markets are clean without any benchmark**
(`src/analysis/niche_gradient.py`, `logs/niche_gradient.log`). 962
settled Kalshi game contracts from 44 un-benchmarked series (minor-league
soccer, T20 cricket, esports, table tennis; prices = last trade before
scheduled start, staleness <= 6h; Tier A uses ticker-embedded start times,
the exact main-sample methodology). ECE 2.43pt sits BELOW the 3.26pt a
perfectly calibrated sample of this size would show from binning noise
alone — zero detectable excess miscalibration. Slope 0.980 (event-
clustered 90% CI 0.84–1.15), no bucket rejects, and 128 three-way soccer
field sums have median 1.020 — exchange-grade vig in the Bolivian Primera
Division. The benchmark's real effect is on *quantity*, not quality: only
~17% of enumerated niche contracts ever traded pre-start (vs near-total
pricing in covered leagues). Without books, there are fewer prices; the
prices that form are good ones.

**2. The books' own outrights fail the same way the exchanges' do**
(`src/collect/sportsbook_outrights.py`, `src/analysis/book_outrights.py`).
Monthly in-season snapshots, 12 resolved sport-seasons (NBA/NFL/MLB/NHL,
2023-24 through 2025-26), 20 books including Pinnacle. De-vigged consensus
sub-10c longshots returned **$0.34 per $1** at 0-3 months out
(sport-season-clustered se 0.08, n=1,614, 20 seasons 2020-26 with
playoff-month densification) and $0.39 at 3-12 months — statistically
identical to Kalshi's $0.33. Shin-robust. Meanwhile the books
charge outright overrounds of 1.20 (Pinnacle) to 1.27 vs Kalshi's
1.03-1.06. An apparent 10-20c "value pocket" (+9pt) is not claimable:
with 12 champions total, whichever bucket happens to hold the eventual
winners pops mechanically. (Betfair Exchange's displayed outright sums of
~2.3 are stale thin asks on dust longshots, a liquidity fact, not vig.)

**3. Polymarket outrights replicate the direction**
(`src/collect/poly_futures.py`). With decision-moment anchoring (first
winner print >= 0.99, because event closedTime can postdate the title by
weeks) and a 3-day print-freshness cap: 22 fully-priced fields, sub-10c
$0.53/$1 (se 0.37), all-futures $0.59, field sums median 1.017.
Underpowered alone; consistent cross-platform. A methods note worth
keeping: without the freshness cap, stale peak prices of faded contenders
manufacture fake pathology (field sums 1.21, a -36pt bucket) — the same
trap the Kalshi staleness re-check guards against (fresh sub-10c prints
there: 0 winners in 114, $0.00/$1 — the pathology is not a staleness
artifact).

**The revised mechanism, one sentence:** repeated, fast-resolving markets
price well at every institution and even without a benchmark; one-shot,
long-horizon markets price badly at every institution — exchanges and
sportsbooks alike — and the institutions differ only in what they charge
for it (exchange vig 1.03 vs book vig 1.2+). Discipline comes from
repetition and feedback, not from institutional design or the presence of
a sportsbook consensus.

## The retail fingerprint: who the market is for (2026-08-03)

Descriptive institutional evidence from the 710K-fill sample
(`src/analysis/retail_fingerprint.py`, `results/retail_fingerprint.png`):
the taker flow looks exactly like a betting shop's clientele. **53% of
fills (60% of notional) arrive in the final 3 hours** before the game
(uniform would be 12.5%), running 31%/hour in the last hour versus
1.1%/hour overnight. Fills placed far from any game (T−24h..T−12h)
concentrate in evening leisure hours — 41% between 7pm and midnight ET
(2× uniform) versus 10% during working hours (a third of uniform). The
**median fill is 30 contracts, about $14 at stake**; 28% of fills are ≤10
contracts yet carry only 1% of volume, while the 7.6% of fills ≥500
contracts carry 78% of it — and the markout analysis shows even those
large fills do not beat the close. Held to settlement (added 2026-08-04),
taker flow surrendered **5.0% of stake gross, 7.7% net of taker fees, on
$95.7M staked** — essentially a sportsbook hold — and no size class
escaped (gross -3.7% to -6.1%; >500-contract fills -4.9%). The pattern is
uniform across all seven leagues (final-3h share 46-57%, median fills
21-34 contracts). The synthesis in one line: **consumption pays, makers
price** — a sportsbook-shaped crowd at the surface, exchange-grade prices
in aggregate.

## Futures and outrights: the pathologies return (2026-08-03)

The within-sports control for the benchmark-discipline mechanism: settled
multi-outcome winner-take-all fields (champions, seeds, award and win-total
fields — 635 priceable contracts in 89 fields from 34 series; prices =
last trade at T−7d/T−30d, trade-recon; calibration on fully-priced fields
so no field's winner can be missing). (`src/collect/kalshi_futures.py`,
`src/analysis/futures_calibration.py`)

- **Longshot futures are badly overpriced — the BDW pattern, inside
  sports.** Sub-10¢ contracts returned **$0.33 per $1 staked** gross
  (n=344; ~9 winners expected at stated prices, 2 observed; pooled exact
  p≈0.006). Compare BDW's all-Kalshi ~$0.40 and our game markets' ~$1.00.
- **Overall**: $1 staked across all futures contracts returned $0.55
  (T−7d) / $0.75 (T−30d) gross, versus ≈$1.00 in game markets.
- **The shape is overconfidence, not classic FLB**: *both* tails
  underperform (sub-10¢ longshots return $0.00–0.52; 75–99¢ favorites won
  62.5% vs 86.3% priced, exact p=0.003) while the middle is roughly fair
  (10–20¢ pays $0.98; 50–75¢ pays $1.09). Futures prices are too extreme
  in both directions.
- **Yet the *vig* is exchange-like**: fully-priced fields sum to a median
  1.03 (T−7d) / 1.06 (T−30d) — nothing like the books' 1.2–1.6 futures
  overrounds. The inversion is striking: on futures, the exchange offers
  book-beating *cost* with badly miscalibrated *prices*, while on games it
  offers both. Cost discipline survives without a benchmark; calibration
  does not.
- Caveats, plainly: 89 fields is modest; field types are heterogeneous
  (championships, exact-win-totals, seeds, awards); thin futures trade
  sparsely so T−7d "prices" can be stale prints; only ~11% of enumerated
  contracts ever traded near the horizons (the priceable universe *is*
  the liquid tail).
- **Mechanism reading**: the same platform, the same sports, the same
  participants — but remove rapid repetition and the sharp benchmark, and
  the calibration pathologies reappear. It is not "sports" that is clean;
  it is benchmarked, fast-resolving, repeated markets.

## Self-correction over time (2026-08-02)

Two tests of whether the market behaves like a static house edge or a
learning instrument (`src/analysis/time_stability.py`):

- **The dead heat holds in every sub-period independently.** Quarterly
  splits: 2025Q4 and 2026Q2 are each formally TOST-equivalent on their own
  (δ_min ≤ 0.84e-3); 2025Q3 is consistent but power-limited (n=465). The
  one detectable wobble — 2026Q1, where **Kalshi beat the books** for a
  quarter (ΔBrier −0.68e-3, z=−3.09, one of 12 quarter-pair tests) —
  favors the *exchange* and vanished the next quarter. No sub-period shows
  the exchanges behind.
- **The MLB blind spot is NOT self-correcting — as the cost-band thesis
  predicts.** The win-by-1-2 underpricing persisted through 2026 at
  +7.5pts (H1, z=+7.6) and +11.2pts (H2, z=+7.3), with implied
  probabilities static near 14% while reality sat at 22–25%. Where fees
  and the 1¢ tick shelter a bias from arbitrage, no correction pressure
  exists and none is observed — the sheltering mechanism demonstrated in
  real time, not just cross-sectionally. (2025 ladders were too sparse to
  measure, n=65 sides.)

## Beyond binary: 3-way outcomes and full margin distributions (2026-08-02)

Extending the comparison past win/lose markets (`src/analysis/multi_outcome.py`):

- **World Cup 3-way, outcome level (n=8 pre-kickoff games, descriptive).**
  The knockout sample ran hot on draws and aways (home teams priced ~46%
  won 25%; draws priced ~28% happened 37.5%) — but *identically at both
  venues* (RPS 0.2157 vs 0.2149), and across all 888 snapshot rows the two
  venues priced the **draw** — the outcome with no fans — within 0.3pt of
  each other, tighter than the teams. Small-sample surprise, shared priors.
- **Margin distributions scored head-to-head (the "by how much" question).**
  Each game's spread ladder implies a full probability distribution over
  victory margins; scoring Kalshi's and the books' distributions with the
  ranked probability score on each game's *shared* rungs (n=3,690 games
  after the NHL extension, 2026-08-04): **the books' distributional edge
  is real but LOCALIZED** — MLB ΔRPS +3.9e-3 (z=+5.4, the known
  small-margin blind spot), NBA +1.1e-3 (z=+2.3), and NHL an exact tie
  (+0.01e-3, z=+0.05); pooled z=+5.36. The edge concentrates precisely in
  the sport whose margin process is strangest (baseball's walk-off/extras
  spike), not as a general books-are-better-at-shapes rule. A curiosity
  for the report's caveats: on NHL the BOOKS' ladder-implied margins fail
  the PIT (KS p<0.001) while Kalshi's pass (p=0.23) — but NHL ladders
  carry only 2-3 rungs, where shape inference is weakest, so this is
  noted, not claimed. Refined thesis sentence: *dead heat on who wins; on
  by-how-much, the professionals keep an edge only where the margin
  distribution itself is pathological.*
- **The picture** (`results/margin_distribution.png`): aggregated implied
  margin distributions vs realized outcomes. MLB books track reality
  within 2.3pts total variation; Kalshi misallocates ~18pts (blowouts
  over-priced, 1–2-run games under-priced). NBA: the two sources'
  implied curves are visually identical.
- **Next (inventoried): outrights/futures.** Kalshi lists 3,068 sports
  series including settled multi-outcome championship markets — the classic
  home of favorite–longshot bias and the sharpest place to extend the BDW
  contrast. Polymarket US `tec-` tournament markets are already in the
  downloaded tape.

## Layer 2, market integration, and FDR control (2026-07-11)

- **Layer 2 (the standard spread) — corrected 2026-07-30.** Main line
  identified per game as the alternate point with de-vigged cover probability
  nearest ½ (mean |p−½| = 2.2pts). The code review caught that **pushes
  (margins landing exactly on integer lines) were being scored as losses**;
  with the 152 pushes excluded, the main-line calibration is clean in *both*
  leagues: MLB empirical cover 50.4% vs 49.9% predicted (n=1,137, ECE
  0.009); NBA 52.1% vs 50.0% (n=1,191, ECE 0.020, n.s.). **The previously
  reported "MLB home sides cover only 45.0% vs 49.9%" was substantially a
  push-scoring artifact and is retracted.** The practitioner literature on
  the historical home-favorite run-line bias (and Woodland & Woodland 1994)
  remains relevant background, but our sample shows no main-line
  miscalibration once pushes are handled — if anything a cleaner null.
  Kalshi ≈ book at matched main-line rungs (mean diff −0.07pts).
  (`src/analysis/layer2.py`)
- **Law of one price across venues.** On 92 games with executable books on
  both exchanges (OddPool archive × Kalshi quotes): median mid-price gap
  1.00pt; buy-one-sell-other crosses gross in 7.6% of games and **net of both
  venues' fees in ≤1%** — and the largest "crossing" traced to a rare
  wrong-game match (a playoff-series next-game market), not real money. The
  two exchanges are one integrated market at the quote level.
  (`src/analysis/one_price.py`) A follow-up audit showed same-pair-within-48h
  games (series; the wrong-game risk set) have *smaller* Poly-book gaps than
  average (0.57 vs 0.95pts; 1 outlier >5pts in 1,465) — series matching is
  sound; 13 of 5,061 games (0.26%) show >5pt Poly-book divergence overall.
- **Multiple testing (inventory regenerated 2026-07-30).** The code review
  found the inventory carried stale Jul-10 p-values; it now holds current
  values with per-claim log provenance, citing clustered p's wherever both
  exist. Benjamini–Hochberg over the **13** current positive claims:
  **12 of 13 survive q=0.05**; only the Kalshi-encompasses-book whisper
  (clustered p=0.054) drops, re-entering at q=0.10. Retired outright as the
  sample grew: the NBA-encompassing sub-claim (p=0.006→0.145), the two
  long-flagged fragiles (wide-set K>P 0.048→0.142; log-score 0.051→0.326),
  and one unsourced claim ("sharpens 24h→start") removed pending a proper
  test. Every load-bearing discovery survives FDR control.
  Nulls/equivalences are inventoried separately (they are not discoveries and
  carry their own TOST margins). (`src/analysis/multiple_testing.py`)

## World Cup 3-way case study (frozen 2026-07-21)

The live 3-way collector (Kalshi "Reg Time" markets vs de-vigged book h2h) ran
from the round of 16 through the final: 9 knockout games, 1,002 snapshots.
Outcomes backfilled by the regulation-90 rule (AET/pens ⇒ level at 90 ⇒ draw):
4 draws, 3 away wins, 2 home wins. On the last pre-kickoff snapshot (8 games;
the collector went live mid-match for the ninth) the two sources are
near-identical: mean 3-way Brier 0.677 (Kalshi) vs 0.673 (book); mean price on
the realized outcome 0.356 vs 0.358 (~0.1pt apart). Both were badly surprised
by the *same* games — a 4-draw knockout stretch including an AET final and
France–England 4–6 (France 0.55 to win in 90). Chalk-heavy priors, but shared
ones: **the binary-market equivalence replicates in a 3-outcome setting** —
descriptive only at n=9.
Frozen: `data/processed/wc_3way_snapshots.csv` (`src/analysis/wc_freeze.py`)

## Robustness (referee-proofing, 2026-07-10)

- **Scoring rule**: log score reproduces the dead heat (all pairwise clustered
  DM n.s.; the one borderline, K-vs-book p=0.051, *favors Kalshi*).
- **Stacked-sides dependence**: home-side-only calibration ≈ stacked (slopes
  0.97–1.02, ECE shifts <0.003) — the both-sides convention does no work.
- **Scoring-function family (Murphy diagrams, 2026-07-24):** elementary-score
  curves (Ehm–Gneiting–Jordan–Krueger 2016) across all decision thresholds θ,
  with date-clustered pointwise and sup-t *uniform* bands (cluster multiplier
  bootstrap). Kalshi vs Polymarket: globally null (sup-t p=0.29) — no proper
  scoring function separates the exchanges. Versus the **Shin**-de-vigged
  book: Polymarket p=0.28; Kalshi p=0.037 on the current master (was 0.012 on
  Jul-10 data — softened as the sample grew), a marginal low-threshold
  (θ≈0.04–0.14) edge *favoring Kalshi* — in the FDR inventory (still keeps at
  q=0.05; treat with the usual fragile-flicker caution). **Method finding:
  de-vig choice is invisible to Brier (0.2183 vs 0.2184) but decisive at
  extreme thresholds** — against the multiplicative-de-vig book, both
  exchanges spuriously "dominate" both tails (sup-t ≈ 5.5, p<0.001), because
  multiplicative de-vig under-corrects the books' longshot shading and
  flattens tail probabilities; Shin removes the effect entirely. Tail-
  sensitive claims must use Shin. (`src/analysis/murphy.py`,
  `results/murphy.png`)
- **Hierarchical Bayesian calibration (PyMC, 2026-07-24):** partial-pooling
  logistic recalibration — league-level (α, β) under non-centered
  hyperpriors; NUTS, 0 divergences, all R-hat ≤ 1.005. **Every league ×
  source 90% HDI covers (α, β) = (0, 1)** — no credible miscalibration
  anywhere. Shrinkage does what the frequentist caveat couldn't: WNBA
  Kalshi's noisy MLE slope 0.795 becomes a posterior 0.898 [0.75, 1.04];
  the MLB MLE slopes of 0.73–0.76 — shared by *all three* sources, hence an
  outcome-side quirk, not a venue defect — shrink to 0.91–0.94. The
  league-heterogeneity hyperparameter σ_β ≈ 0.10 with μ_β compatible with 1
  in every source: nothing league-level to find. The "CFB/WNBA/NFL
  underpowered" caveat is now a posterior statement instead of a shrug.
  (`src/analysis/hierarchical_calibration.py`,
  `results/hierarchical_calibration.png`)
- **Binning**: CORP (isotonic, bin-free) miscalibration is 1.2–1.4e-3 for all
  three sources and *reverses* the binned ordering (Kalshi lowest) — reliability
  differences between sources are within method noise; discrimination (33e-3)
  is identical. Bin-based "book is best calibrated" should not be over-read.
  CORP reliability *diagrams* with resampled 90% consistency bands
  (2026-07-21): every source's isotonic curve sits inside its
  perfect-calibration band over 83–89% of [0.01,0.99] — exactly the coverage
  perfect calibration predicts. Report-grade replacement for the binned
  diagrams. (`src/analysis/corp_diagram.py`, `results/corp_reliability.png`)
- **Selection**: Kalshi calibration on ALL its priced games (n=9,003, incl.
  leagues Polymarket never listed) is intact (slope 1.014, ECE 0.018). On the
  wider both-priced set the K-vs-P DM flickers to p=0.048 in *Kalshi's* favor —
  the K–P ordering is fragile around the 5% line in either direction; the
  equivalence-with-books conclusion is unaffected.
- **Fee natural experiment**: Polymarket's sports taker fee switched on
  2026-03-30 mid-sample. Difference-in-differences on the per-game Brier
  differential vs the book (league FE, date-clustered): post-fee coefficient
  +0.23e-3, p=0.74 (Kalshi placebo also null); post-fee Polymarket ECE 0.004,
  slope 0.994. **Introducing fees did not measurably degrade price quality** —
  forecast accuracy is invariant to the fee regime, consistent with prices
  tracking information rather than microstructure.
  (`src/analysis/referee.py`, `src/analysis/fee_experiment.py`)

## Data-quality audit (methods note)

A profitability backtest surfaced "impossible" profits (e.g. a 9¢ ask on a 91%
book favorite). Direct API verification showed the *market* was right and our
pipeline had mis-assigned sides in ~350 games (team-code alias collisions; 2.7%
same-ticker contamination). Fix: side assignment by the Kalshi ticker-order rule
(event pair suffix ends with the home code; 99.6% validated), plus venue-mismatch
exclusions. **The pre-fix data showed "Kalshi significantly lags the books"
(p=0.004); the clean data shows equivalence.** Lesson: an impossible backtest
profit is a data-quality alarm, and market-vs-market cross-checks catch errors
single-source studies cannot.

## In progress

- **Lead–lag price discovery** — *complete as of 2026-08-10*. The panel now
  runs to 528 games; the 15-min pass was refreshed (one cross-venue term
  retired), the sub-15-min cell was closed on the 5-min cadence (nuance 3c),
  and the depth captures produced the price-of-immediacy curve (nuance 4).
  The World Cup 3-way leg ended with the final and is frozen (see case study).
  The panel keeps growing ~18 games/day; one final refresh before the number
  freeze will roughly double the n=19 fine-clock event study.
- Advisor input pending on: HAC/cluster choices, multiple-testing policy,
  equivalence-margin convention, 3-way calibration methodology.

## Caveats & scope

- Cross-source margin curves cover MLB + NBA (Kalshi ladders vs book alternate
  lines); other leagues remain within-Kalshi only. Deep history limited by Kalshi's ~60-day price retention (trade
  reconstruction used beyond it) and Polymarket's structured-sports era (mid-2025→).
- Book lines sampled up to 60 min before start (credit-batching); prediction-market
  prices at start. Any late-news asymmetry slightly *favors* the markets.
- CBB largely excluded (ESPN coverage gap; no Polymarket CBB markets).
- Kalshi trading fees are not included in the overround comparison (spread only).
