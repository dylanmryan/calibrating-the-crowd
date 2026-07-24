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
| **All-three joint set (clean)** | **5,044 games** | NBA/NHL/MLB/CFB/NFL/WNBA, May 2025 – Jul 2026 |
| Alternate-spread ladders | 28,940 contracts, 4,042 games | Kalshi spread series |
| Book alternate spread lines | 107,100 points, 2,480 MLB/NBA games | The Odds API historical (per-event, de-vigged pairs) |
| Polymarket archived order books | 93 games (spread sample) | OddPool archive |
| Multi-horizon price paths | Kalshi ~8,000 + Polymarket 5,410 games × 7 horizons | trade history / CLOB minute paths |
| Book T−24h "opening" consensus | 3,461 games | The Odds API historical |
| Live 3-source time series + World Cup 3-way | every 15 min | VPS collector (lead–lag, in progress) |

Outcome integrity: ESPN finals cross-checked against both platforms' settlements
(99.6% / 98.7% agreement); flagged games excluded. Venue/side assignment via the
ticker-order rule (validated 99.6% vs ESPN).

## Headline: a statistical dead heat (n = 5,044)

| | Kalshi | Polymarket | Sportsbook |
|---|---|---|---|
| Brier | 0.2180 | 0.2182 | 0.2181 |
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
   pass the same PIT that rejects Kalshi's** (book MLB KS p=0.46, NBA p=0.17 vs
   Kalshi MLB p<0.001) — the books' curves are distributionally correct, not
   just right in one cell (`src/analysis/book_pit.py`); **(b) the mispricing is
   unexploitable**: selling the over-priced "win by 3+" contracts at the bid,
   fees included, loses 2.9–4.5% (date-clustered z −2.3 to −4.6; robust to
   live-book-only quotes) — the bias is harbored inside Kalshi's transaction-
   cost band exactly as books harbor biases inside their vig, which is *why* it
   persists (`src/analysis/ladder_cost.py`).
2. **Forecast encompassing — equally accurate ≠ redundant.** In log-odds
   combination regressions (date-clustered SEs), Kalshi's price carries a small
   information increment *beyond* the book (LR exclusion p=0.004) and beyond
   Polymarket (p=0.013); neither the book nor Polymarket adds information beyond
   Kalshi. The increment is sign-consistent across all six leagues, statistically
   driven by the NBA (p=0.006) — the most heavily traded league, consistent with
   informed marginal traders — and is **not** a quote-timing artifact: it
   concentrates in games where the book quote is freshest (<10 min old, p=0.003)
   and vanishes where it is stale. Economically it is negligible: the DM accuracy
   gain is n.s. and liquid-game Briers are identical to 4 decimals. Precisely:
   the crowd re-prices the books' information without loss and adds a detectable
   whisper of its own. (`src/analysis/encompassing.py`)
   **The whisper is carried by late order flow.** Decomposing Kalshi's close
   into a 24h-out level plus the final-day movement (trade-path panel, n=3,314
   games with ≥10 trades): the flow term predicts outcomes beyond the closing
   book line (LR p=0.001), and model-free, final-24h moves of ≥3pts point
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
   predict each other (K→P z=+3.3, P→K z=+3.0) and book→Poly (z=+2.9), while
   nothing significantly predicts the book's next move (z≤+1.4) — yet every
   coefficient is ~0.03, i.e. ~3% of a move transmits one step ahead. Event
   study on big moves (|d|≥2pts; n=65–123 events per source): the other
   venues' signed response concentrates at offset 0 (+0.35–0.74pt within the
   same 15-min step), ≈0 before, ≤0.2pt after — **big repricings are
   simultaneous at 15-min resolution; no venue front-runs another**. Coheres
   with the T−24h horizon result (books fractionally ahead, gap closed by
   start) and with maker-driven discovery on public news.
   (`src/analysis/lead_lag.py`)
4. **Cost asymmetry — 3-venue table now complete**: sportsbook overround ~4.2%
   everywhere; Kalshi bid/ask overround ~1.0%; and Polymarket's archived books
   (OddPool, n=93 games, all four in-season leagues) show a median quoted spread
   of exactly 1.00pt — equal to Kalshi's on the same games. Both exchanges are
   ~4× tighter than the books at the quote. All-in for a market-order taker
   (spread + fees): Polymarket ~1.25–1.75% < Kalshi ≈ books ~4.2%; makers trade
   ~free on both exchanges, a path books don't offer. Bonus validation: the
   archived Polymarket book mids match our CLOB-derived closing prices with
   median error 0.00pts — both prediction-market price pipelines are now
   independently confirmed against external archives.
5. **The ordinary gambler's ROI** on Kalshi: −3 to −4.5% across strategies
   (everything/favorites/longshots/home) ≈ transaction costs. Efficient market, not
   a beatable casino — and also not a rigged one.
6. **Thin markets are noisier**: Kalshi calibration error rises sharply with quoted
   spread (ECE 0.013 tight → 0.11 wide; reliability 0.25 → 18.1 ×1000; reruns
   2026-07-10 and 2026-07-21 on the re-harvested master), but thin markets do not
   drive any headline result: on liquid
   games only (spread ≤ 1¢, n=4,374) all three sources have Brier 0.2186 and every
   pairwise clustered DM is n.s. (p ≥ 0.45). This formally retires the pre-side-fix
   "Kalshi lags even on liquid games (p=0.004)" result — it was contamination.

## When does the dead heat form? (open vs close, n=2,139 constant sample)

At **T−24h** the books hold a small, statistically real accuracy lead over
Kalshi (ΔBrier +0.73e-3, date-clustered z=2.18, p=0.029); Polymarket sits
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

**Comparative sharpening (2026-07-21).** The full 7-horizon Brier curves on the
joint constant sample (n=2,137) make the Page–Clemen replication comparative:
both exchanges sharpen essentially monotonically (Kalshi 0.2138→0.2125,
Polymarket 0.2134→0.2123) and are statistically indistinguishable at every
horizon (all date-clustered |z| ≤ 1.8; smallest p=0.077 at 12h, favoring Poly)
— **the dead heat holds along the whole final-day path**, not just at the
close. Mean |24h→start| move is 2.0pts on both venues; book reference on the
same games 0.2130 (T−24h) → 0.2124 (close).
(`src/analysis/horizon_cross.py`, `results/horizon_cross.png`)

## Layer 2, market integration, and FDR control (2026-07-11)

- **Layer 2 (the standard spread).** Main line identified per game as the
  alternate point with de-vigged cover probability nearest ½ (mean |p−½| =
  2.2pts). NBA is calibrated (empirical cover 51.4% vs 50.0% predicted, ECE
  0.014). **MLB home sides cover the run line only 45.0% vs 49.9% implied**
  (n=1,274, z≈−3.5, ECE 0.049) — directionally consistent with the walk-off
  compression of home margins (home teams ahead stop batting; −1.5 fails on
  1-run wins). Literature check (2026-07-21): this matches the long-documented
  home-favorite run-line bias — large-sample public analyses put historical
  home −1.5 cover near 45% with the same walk-off mechanism (~28–29% of MLB
  games end by exactly one run), and Woodland & Woodland (1994) established
  MLB moneylines as efficient-within-costs with a *reverse* favorite–longshot
  bias. So: a known structural feature the books carry inside their vig (our
  cost-band thesis), not a pipeline artifact — but post-hoc on a single rung
  here, so cite as corroborated context, not a new discovery. Kalshi ≈ book
  at matched main-line rungs (mean diff −0.07pts; mostly NBA — MLB ladders
  rarely quote 1.5). (`src/analysis/layer2.py`)
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
- **Multiple testing.** Benjamini–Hochberg over the paper's 14 positive
  claims (Murphy sup-t added 2026-07-24): **12 of 14 survive q=0.05** — only
  the two results already flagged as fragile (wide-set K>P at p=0.048;
  log-score K>book at p=0.051) drop, and they re-enter at q=0.10. Every
  load-bearing discovery survives FDR control.
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
  book: Polymarket p=0.28; Kalshi p=0.012, a marginal low-threshold
  (θ≈0.04–0.14) edge *favoring Kalshi* — added to the FDR inventory (survives
  q=0.05; treat with the usual fragile-flicker caution). **Method finding:
  de-vig choice is invisible to Brier (0.2183 vs 0.2184) but decisive at
  extreme thresholds** — against the multiplicative-de-vig book, both
  exchanges spuriously "dominate" both tails (sup-t ≈ 5.5, p<0.001), because
  multiplicative de-vig under-corrects the books' longshot shading and
  flattens tail probabilities; Shin removes the effect entirely. Tail-
  sensitive claims must use Shin. (`src/analysis/murphy.py`,
  `results/murphy.png`)
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

- **Lead–lag price discovery**: two-week pass analyzed (nuance 3); the series
  keeps accumulating on the VPS — rerun near season end for power. The World
  Cup 3-way leg ended with the final and is frozen (see case study).
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
