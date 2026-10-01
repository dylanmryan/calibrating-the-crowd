# Data Dictionary — Calibrating the Crowd

Every dataset in `data/processed/`, what it contains, where it came from, and
what to watch out for. All prices are probabilities in [0,1] unless noted.
Team orientation: `team1`/`home`/`p1` is the home side throughout; outcomes are
`1` = home won, `2` = away won. All timestamps UTC unless suffixed otherwise.

**Which of these are in this repository.** Eleven. Every free-API table is here:
`kalshi_hist_prices.csv`, `kalshi_settled_markets.csv`, `kalshi_espn_matches.csv`,
`polymarket_hist_prices.csv`, `polyus_prices.csv`, `polyus_catalog.csv` and
`espn_games.csv`, plus the derived `analysis_core.csv` and `recon_validation.csv`.
Also here: `games_master.csv`, the merged table with audit flags that
`three_way.load()` reads, and `analysis_four_way.csv` (below).

So all three prediction markets — Kalshi, Polymarket Global and Polymarket US —
ship with their prices, and the three-way and four-way sets can both be rebuilt
from this repository alone.

The per-bookmaker sportsbook tapes are here as well — `sportsbook_hist_prices.csv`,
`sportsbook_open_prices.csv`, `sportsbook_us_books.csv`, `sportsbook_sharp_prices.csv`,
`sportsbook_outrights.csv`, `sportsbook_alt_spreads.csv` — so the book leg can be
rebuilt from the feed rather than taken from the consensus. They came from The Odds
API on a paid plan; re-users should check that provider's terms.

What is **not** here is the microstructure and live tail: the Kalshi liquidity sweep
(137MB, past GitHub's file limit), the 24h trade tape, the minute paths and the VPS
snapshot mirror. Those drive the liquidity, immediacy and live-capture modules, not
the headline. See *Data availability* in the README.

### analysis_four_way.csv (2,631 games)
The four-way set, as a file: one row per game priced by **all four** venues, so
the fourth institutional cell is readable without re-running the join. Columns
`kalshi_p1`, `poly_p1`, `pus_p1`, `book_p1` (home-side probabilities),
`book_count`, `home_won`, and the two PolyUS quality fields `stale_min` /
`fills_24h`. No column has a missing value.

This is **derived, not frozen**. `analysis_core.csv` is the artifact the suite
ran on and is unchanged. This file was rebuilt on 2026-09-30 from published
tables only, reusing `four_way.py`'s own `build_prices()` and `match_games()`,
and it reproduces that module's frozen log exactly: 2,794 games matched, 2,631
after the quality filters (stale <= 120min, fills >= 5), with Brier 0.2303
Kalshi / 0.2305 Poly-Global / 0.2304 Sportsbook / 0.2307 Poly-US. Regenerate it
with `python -m src.analysis.four_way` or rebuild it from the tables here.

**Start here: `analysis_core.csv`** — one row per game, every venue joined,
clean column names. The starter notebook (`notebooks/data_tour.ipynb`) loads it
and reproduces the headline results.

## Core game-level tables

### analysis_core.csv (10,118 games, built from the tables below)
One row per ESPN game. Columns:
- `game_id` — ESPN event id (the join key across every table)
- `league` — MLB / NBA / NFL / NHL / WNBA / CFB / CBB-M
- `start_utc`, `home_team`, `away_team`
- `home_won` — 1.0/0.0 from ESPN finals (NaN = not yet resolved)
- `clean_set` — True = passes outcome cross-checks; use this filter for
  calibration work (the paper's n=5,333 three-way set is `clean_set` plus
  non-null Kalshi/Polymarket/book probs, plus a resolved outcome)
- `kalshi_home_prob` — Kalshi price at official start (book-mid post-cutoff,
  last-trade reconstruction pre-cutoff; validated vs archived books, 99%
  within 1pt)
- `polymarket_home_prob` — Polymarket CLOB price at start
- `book_home_prob_devig` — mean de-vigged (multiplicative) home probability
  across ~10 US books at the closing hour; `book_home_prob_raw` /
  `book_away_prob_raw` keep the vigged versions (they sum to >1; the
  overround); `book_count` = books in the consensus
- `book_home_prob_t24h` — same consensus 24h before start (85% of book-priced
  games; the
  missing games are mostly ones books don't list a day ahead)
- `pinnacle_home_prob`, `betfair_home_prob` — de-vigged closing quotes from
  the EU snapshot (Pinnacle = the sharp book; Betfair = the incumbent
  betting exchange)

#### Coverage: why a venue's price is blank

A blank is a price that does not exist, not one that was dropped. Verified
2026-09-30: of the 4,681 games with no book price and the 3,702 with no
Polymarket price, **zero** have a price sitting unused in the upstream tables.
Overall presence is Kalshi 99.5%, Polymarket 63.4%, book consensus 53.7%, and
the three gaps have three different causes:

| cause | where it shows |
|---|---|
| The Odds API budget was exhausted before the sample ended | book coverage falls 99.8% (2026-06) to 4.5% (2026-07) to 0% (2026-08) |
| CBB-M was collected from Kalshi only | all 1,018 men's college basketball games have Kalshi and nothing else |
| Historical backfill reached further on some venues than others | 2025-04 to 2025-09 runs 0-38% on both Polymarket and book |

None of this touches the headline. The three-way set takes only games priced
everywhere, so every result is computed on 5,333 complete rows; the wider file
is kept because the Kalshi-only and two-venue rows carry the niche-market and
coverage analyses.

### games_master.csv
The underlying merged table (Kalshi + Polymarket + ESPN + book consensus)
with matching metadata and audit flags (`outcome_disagree`, `venue_disagree`).
Prefer `analysis_core.csv` unless you need the flags.

### espn_games.csv / kalshi_espn_matches.csv / kalshi_settled_markets.csv
ESPN schedule+finals (incl. `home_score`/`away_score` for margins); the
Kalshi-ticker-to-ESPN match table; all settled Kalshi game markets.

## Sportsbook tables (The Odds API; subscription ends Sept 2026 — these
files are the permanent record)

- `sportsbook_hist_prices.csv` — closing consensus per game (US region,
  60-min buckets at official start).
- `sportsbook_open_prices.csv` — T-24h consensus (`book24_p1/p2`).
- `sportsbook_sharp_prices.csv` — **per-book** EU closing quotes, one row
  per game-book (24 books incl. `pinnacle`, `betfair_ex_eu`, `matchbook`);
  `raw_p1/raw_p2` are vigged implied probs — de-vig with p1/(p1+p2).
- `sportsbook_us_books.csv` — the same shape for 11 US retail brands
  (DraftKings, FanDuel, BetMGM, …), 4,729 games.
- **`book_ts` in both per-book files is that bookmaker's own `last_update`,
  not the collection time**, so the age of each quote at kickoff is
  recoverable. It went unread until 2026-09-16 and is now load-bearing:
  `src/analysis/book_freshness.py` uses it to re-run the headline inside a
  bimodal quote-age split, which converts the project's timing caveat from a
  concession into a measurement. It is a CLOSING cross-section — ~8-12
  distinct stamps per game, near-synchronous within a game — so it bounds how
  stale the benchmark was, and cannot support lead-lag between books.
- `sportsbook_alt_spreads.csv` — de-vigged alternate-spread ladders
  (MLB/NBA/NHL), one row per game-line-side, `n_books` per point.
- `sportsbook_outrights.csv` — monthly championship-winner odds snapshots,
  per book-team, 12 sport-seasons 2023-26 (`snap` = YYYY-MM). Vigged; field
  sums are the outright overround (1.20-1.27).
- `niche_book_odds.csv` / `niche_unpriced_book_check.csv` — EU book odds and
  presence checks for the niche-league sample (Brasileiro, Eliteserien, NRL).

## Kalshi microstructure and breadth

- `kalshi_hist_prices.csv` — raw per-side quotes behind the game prices.
- `kalshi_spread_prices.csv` — 28.9K alternate-spread threshold contracts
  (the ladders; join to games via `game_id`).
- `kalshi_trades_24h.csv` — 710K public fills in the final 24h for 513
  games (`taker_side`, `count`, `yes_price`; home ticker only).
- `kalshi_niche_prices.csv` / `kalshi_niche_trades.csv` — the niche-sport
  sample: 1.3K contracts priced at scheduled start (tier A = ticker-embedded
  start; staleness recorded) + 43K fills.
- `kalshi_futures_prices.csv` — 635 outright contracts in 89 settled
  winner-take-all fields, priced at T-7d/T-30d before close.
- `kalshi_horizons.csv` — home-side price paths at 7 horizons (24h → 0).
- `kalshi_liquidity_sweep.csv` — point-in-time sweep of ALL 784K open
  markets (2026-08-04): series, volume, open interest, touch quotes. NOTE:
  the API's `liquidity_dollars` field is served zeroed — ignore it.
- `kalshi_series_fees.csv` — per-series fee schedule (`fee_type`:
  `quadratic_with_maker_fees` = makers pay, `quadratic` = makers free).
- `kalshi_depth_survey.csv` — signed order-book depth (contracts within 5c)
  for top-volume markets per class (2026-08-04).
- `kalshi_series_inventory.csv` — all 3.1K sports series with settled counts.

## Polymarket

- `polymarket_hist_prices.csv` — CLOB game prices at start.
- `poly_horizons.csv` — minute-path horizons (T-24h → 0).
- `poly_spreads.csv` / `poly_token_map*.csv` — measured quoted spreads
  (via OddPool archive) and CLOB token id maps.
- `poly_futures_prices.csv` — outright fields priced at decision-time
  minus 7/30d (decision = first winner print >= 0.99; 3-day freshness cap.
  Without that cap, stale peak prices fake pathology — see findings).
- `niche_poly_check.csv` — Poly presence/volume/prices on niche matches.
- `polyus_catalog.csv` / `polyus_prices.csv` — Polymarket US (the fourth
  venue): market catalog and execution-tape prices.

## Live capture (VPS, 15-min cadence; `data/live/vps_mirror/`)

- `snapshots.csv` — Kalshi/Polymarket/book aligned quotes per upcoming game,
  with Kalshi touch sizes and depth-within-5c (`bidq1..d5ask2`) since
  2026-07-25; book odds at 5-min cadence since 2026-07-31. The `sportsbook`
  rows carry a **cross-book MEAN** (`p1`/`p2`, with `n_books` = how many books
  it averaged), not any individual book's quote. Every lead–lag result in the
  project reads this series; `src/analysis/book_panel.py` audits what the
  averaging costs and which questions it forecloses.
- `book_quotes.csv` — **per-book** live quotes, one row per (snapshot, game,
  book): `book`, `book_update` (that bookmaker's own last-update stamp, so
  quote age is recoverable), `raw1`/`raw2` (vigged implied probabilities).
  Added 2026-09-16 from the same Odds API response `snapshots.csv` already
  paid for, at zero marginal credit cost, after the panel audit found that
  per-book *timing* was unrecoverable from anything banked. Written to its own
  file so `snapshots.csv` keeps the exact schema the frozen analysis reads.
  **Empty until collection resumes** — it does not cover the frozen panel, and
  no result in the current report uses it.
- `wc_snapshots.csv` — World Cup 3-way (home/draw/away) paths.
- `outcomes.csv` — ESPN finals backfill.

## Provenance and caveats in one paragraph

Kalshi prices older than ~60 days are reconstructed from the trade tape
(`/historical/trades` with `max_ts`) because Kalshi's candles/books are
erased past a rolling cutoff; the reconstruction was validated against an
independent order-book archive (median error 0.00pt, 99% within 1pt).
Book consensus is a de-vigged mean across books at a 60-min snapshot
bucket, so exchange prices (measured AT start) have a slight timing
advantage — documented, and unchanged by robustness checks. Polymarket
resolved-market histories only serve ~12h candles (fine at day-scale
horizons, coarse at T-0). Audit gates (`src/analysis/data_audit.py`,
`deep_audit.py`) run before every suite regeneration; `results/MANIFEST.md`
records the last clean run.

## Case-study exhibits (`data/exhibits/`)

Four named games captured in full cross-venue detail for the report's
narrative openings (see `exhibits_manifest.csv` for coverage counts):
- `nba_finals_g5_*` — 2026 NBA Finals Game 5 (SAS-NYK, the Knicks'
  clincher): 32 books at 7 horizons (T-72h..start), 50K Kalshi fills,
  Polymarket path.
- `super_bowl_lx_*` — Super Bowl LX (SEA 29-13 NE): 27 books, full
  Polymarket paths for all three game markets. Kalshi tape unavailable
  (the SB game market is not locatable via the public API).
- `buf_mia_tnf_*` — the tape's highest-notional regular game ($4.5M in
  24h): 28 books, 50K fills.
- `pit_wsh_walkoff_*` — 10-inning 1-run walk-off (the MLB blind-spot
  exhibit): 31 books incl. close-time spreads/totals, 34K fills.
Notes: `*_books.csv` horizons are snapshots at T-72/24/12/6/3/1/0h
(decimal odds, us+eu regions); Kalshi tapes are the newest <=50K fills
through start+6h (post-cutoff games served by the live trades endpoint,
older ones by the historical endpoint); Polymarket paths for
long-resolved markets are coarse (12h candles) — day-scale only.
