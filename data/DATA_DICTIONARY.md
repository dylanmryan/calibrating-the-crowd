# Data Dictionary — Calibrating the Crowd

Every dataset in `data/processed/`, what it contains, where it came from, and
what to watch out for. All prices are probabilities in [0,1] unless noted.
Team orientation: `team1`/`home`/`p1` is the home side throughout; outcomes are
`1` = home won, `2` = away won. All timestamps UTC unless suffixed otherwise.

**Start here: `analysis_core.csv`** — one row per game, every venue joined,
clean column names. The starter notebook (`notebooks/data_tour.ipynb`) loads it
and reproduces the headline results.

## Core game-level tables

### analysis_core.csv (~9.4K games, built from the tables below)
One row per ESPN game. Columns:
- `game_id` — ESPN event id (the join key across every table)
- `league` — MLB / NBA / NFL / NHL / WNBA / CFB / CBB-M
- `start_utc`, `home_team`, `away_team`
- `home_won` — 1.0/0.0 from ESPN finals (NaN = not yet resolved)
- `clean_set` — True = passes outcome cross-checks; use this filter for
  calibration work (the paper's n=5,328 three-way set is `clean_set` plus
  non-null Kalshi/Polymarket/book probs)
- `kalshi_home_prob` — Kalshi price at official start (book-mid post-cutoff,
  last-trade reconstruction pre-cutoff; validated vs archived books, 99%
  within 1pt)
- `polymarket_home_prob` — Polymarket CLOB price at start
- `book_home_prob_devig` — mean de-vigged (multiplicative) home probability
  across ~10 US books at the closing hour; `book_home_prob_raw` /
  `book_away_prob_raw` keep the vigged versions (they sum to >1; the
  overround); `book_count` = books in the consensus
- `book_home_prob_t24h` — same consensus 24h before start (84% coverage; the
  missing games are mostly ones books don't list a day ahead)
- `pinnacle_home_prob`, `betfair_home_prob` — de-vigged closing quotes from
  the EU snapshot (Pinnacle = the sharp book; Betfair = the incumbent
  betting exchange)

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
  2026-07-25; book odds at 5-min cadence since 2026-07-31.
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
