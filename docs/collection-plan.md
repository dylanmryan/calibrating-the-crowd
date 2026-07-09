# Data Collection Plan — Calibrating the Crowd

**Goal:** a per-game dataset comparing prediction-market prices (Kalshi, Polymarket) and
sportsbook lines against actual outcomes, plus a live time-series to study lead–lag
"influence" between sportsbooks and prediction markets.

## Target output schema (one row per game)

`data/processed/games_master.parquet`

| column | meaning |
|---|---|
| `sport`, `league` | e.g. Baseball / MLB |
| `game_id` | canonical id (ESPN event id) |
| `date`, `start_utc` | official start time (ESPN) — the price-sampling reference |
| `team1`, `team2` | home, away (canonical names) |
| `kalshi_p1`, `kalshi_p2` | pre-game implied prob per side (book-mid, normalized to sum 1) |
| `poly_p1`, `poly_p2` | pre-game implied prob per side (Polymarket) |
| `book_p1`, `book_p2` | de-vigged sportsbook moneyline prob per side |
| `outcome` | which side actually won (1=team1, 2=team2) |
| `kalshi_spread1/2`, `kalshi_stale1/2` | quality flags (bid/ask width, minutes to start) |
| `poly_*`, `book_*` quality | same, per source |
| `price_source` | `book-mid` (post-cutoff/live) or `trade-recon` (pre-cutoff) |

De-vig / normalization: every source's two complementary prices are normalized to sum to 1
(removes spread/vig) so calibration is apples-to-apples. Raw prices retained too.

---

## Part A — Historical backfill (one-time)

### A1. Outcomes + schedule  ✅ built
- `src/collect/kalshi.py` → 13,468 settled games, 7 leagues, `won` per side.
- `src/collect/espn.py` → official start times + final scores (cross-check).
- `src/match/kalshi_espn.py` → 99.3% match on 6 major leagues (auto-learned team-code aliases).

### A2. Kalshi historical prices
- **Post-cutoff (~last 60 days):** book-mid `(yes_bid+yes_ask)/2` from 1-min candlesticks. ✅ built (`kalshi_prices.py`).
- **Pre-cutoff (older):** candlesticks are empty, BUT `/historical/trades?ticker=X&max_ts=<start>`
  retains fills. Reconstruct effective bid/ask from `taker_side` (yes-buy=ask, yes-sell=bid) →
  book-mid, even historically. Fallbacks: VWAP over last 2h → last trade. Record staleness.
  **To build:** `src/collect/kalshi_hist_prices.py`.
- Coverage varies by liquidity (MLB/WNBA deep; thin college games sparse) — flag & filter.

### A3. Polymarket historical prices  ← workstream
- Global platform (on-chain, matches existing keys/notebook). Steps:
  1. Discover sports game markets (gamma `/events` or CLOB; the naive tag filter failed —
     needs the sports/series structure or the `dr-manhattan` unified MCP).
  2. Match markets → games (team + date, reuse alias approach).
  3. Price at start: CLOB `/prices-history` is coarse (~12h) for resolved markets → prefer
     on-chain trades / a paid archive for fine granularity.
- **Decision pending:** evaluate paid unified vendor (PredictionData.io — also bundles
  sportsbook; or FinFeedAPI) vs. in-house on-chain reconstruction. Free PMXT archive is
  hourly + shallow, useful only as a recent-months complement.

### A4. Sportsbook historical
- The Odds API `/historical` (paid, 10× credits) OR a unified vendor (PredictionData.io).
- De-vig moneylines (multiplicative; later Shin/power for robustness).

### A5. Merge → `games_master.parquet` on `game_id`.

---

## Part B — Live collection (START NOW — perishable) 

Captures a **time-series** of prices from all sources over each game's pre-game window,
so we can study **influence / lead–lag** (does the sportsbook move first and the
prediction market follow, or vice versa?). This data cannot be recovered later.

### Store: `data/live/snapshots.parquet` (append-only)
Row per (snapshot time × game × source): `snapshot_utc, league, game_id, start_utc,
minutes_to_start, source, p1, p2, spread1, spread2, raw`.

### Sources per snapshot
- **Kalshi:** open markets `/markets?series_ticker=...&status=open` → current `yes_bid/ask` per side. ✅
- **Sportsbook:** Odds API `/sports/{sport}/odds?markets=h2h` → de-vigged moneyline. ✅
  (Free tier = 500 req/mo; 1 call returns all games for a league. Budget: snapshot at a
  fixed schedule that covers the pre-game window — see cadence — or pay for higher volume.)
- **Polymarket:** plug in once A3 discovery is solved.

### Cadence (influence analysis needs resolution near tip-off)
Snapshot each game at ~T-12h, T-6h, T-3h, T-1h, T-30m, T-15m, T-5m. Implemented as a job
run every 15 min that only records a source when a game is inside the pre-game window,
keeping Odds API calls within budget (≈1 call/league/run, throttled).

### Leagues in season now (2026-07): **MLB, WNBA** (+ soccer/tennis later). NFL/NBA/NHL/CFB/CBB resume in fall.

### Scheduling
Run `python -m src.collect.live_snapshot` every 15 min via cron / scheduled task.
Outcomes backfilled from ESPN finals after games complete.

---

## Analysis (downstream, already prototyped)
- Calibration (reliability, Brier, slope, ECE) per source & league — `src/analysis/`.
- Favorite–longshot (logistic), spread-curve consistency (alternate lines).
- Diebold–Mariano source comparison; time-horizon calibration (open vs close).
- **Influence:** lead–lag / Granger-style tests on the live time-series across sources.
