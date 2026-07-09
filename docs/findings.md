# Calibrating the Crowd — Findings Summary
*Dylan Ryan · BPF Undergraduate Research Grant · updated 2026-07-09*

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
| Multi-horizon price paths | ~9,000 games × 7 horizons | Kalshi trade history (in progress) |
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

## Notable nuances

1. **MLB margin distributions are miscalibrated** (PIT KS=0.072, p<0.001, unbiased in
   location) — plausibly the margin-of-exactly-1 spike created by walk-off rules,
   under-priced in run lines. The one distributional crack found; worth a section.
2. **Cost asymmetry**: sportsbook overround ~4.2% everywhere; Kalshi bid/ask
   overround ~1.0% (caveat: Kalshi charges trading fees on top; books are all-in).
3. **The ordinary gambler's ROI** on Kalshi: −3 to −4.5% across strategies
   (everything/favorites/longshots/home) ≈ transaction costs. Efficient market, not
   a beatable casino — and also not a rigged one.
4. **Thin markets are noisier**: Kalshi calibration error rises sharply with quoted
   spread (ECE 0.014 tight → 0.10 wide), but thin markets do not drive any headline
   result.

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

- **Multi-horizon calibration** (T−24h → start, from Kalshi trade paths): does the
  market sharpen as the event approaches? (Page & Clemen replication.)
- **Lead–lag price discovery**: 15-min three-source time series accumulating on an
  always-on VPS (plus World Cup 3-way home/draw/away).
- Advisor input pending on: HAC/cluster choices, multiple-testing policy,
  equivalence-margin convention, 3-way calibration methodology.

## Caveats & scope

- Sports moneylines only (spreads analyzed within Kalshi; cross-source spread curves
  not yet built). Deep history limited by Kalshi's ~60-day price retention (trade
  reconstruction used beyond it) and Polymarket's structured-sports era (mid-2025→).
- Book lines sampled up to 60 min before start (credit-batching); prediction-market
  prices at start. Any late-news asymmetry slightly *favors* the markets.
- CBB largely excluded (ESPN coverage gap; no Polymarket CBB markets).
- Kalshi trading fees are not included in the overround comparison (spread only).
