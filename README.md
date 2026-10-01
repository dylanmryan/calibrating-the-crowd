# Calibrating the Crowd

**Sports prediction markets and sportsbooks as forecasters of the same games.**

Undergraduate research project, Department of Statistics and Data Science,
Northwestern University. Summer 2026.
Student: Dylan Ryan · Faculty mentor: Prof. Arend Kuyper.

## Research report

The [research report](https://docs.google.com/document/d/1PrgOKQpmin81d3iuxW_3kNqTtV87xXD5v0Rlzd8noe4)
is the authoritative account of the findings and their limitations. Earlier
writeups in `docs/` are historical working notes and may contain superseded
claims. This README summarizes the report; it does not establish that faculty
review or independent validation has been completed.

## Question and primary finding

Do sports prediction markets forecast pre-game winners as accurately as
professional sportsbooks? The primary comparison matches **5,333 games across
six leagues and 386 dates**, from May 2025 through July 2026, with usable prices
from **Kalshi, Polymarket Global, and an equally weighted consensus of eleven
US-region sportsbooks**.

| Source | Brier score | Home-side calibration slope |
|---|---:|---:|
| Kalshi | 0.2196 | 0.956 |
| Polymarket Global | 0.2198 | 0.954 |
| Sportsbook consensus | 0.2196 | 1.002 |

Lower Brier scores indicate smaller average prediction errors. For every
pairwise comparison, the date-clustered 90% confidence interval for the Brier
difference lies entirely within **±0.001**. This establishes equivalent average
closing accuracy at that tolerance. The margin is an **internal analytical
tolerance**, not an externally timestamped preregistration or a validated
threshold of economic significance. It is not generally convertible into a
systematic probability offset.

The result holds with Pinnacle as the benchmark and with sportsbook quotes
restricted to those within ten minutes of the recorded start. Equivalence is
not established in every league or calendar-quarter subgroup. Calibration-slope
intervals include one; this does not establish perfect calibration. Inference
uses one home-side observation per game, rather than treating complementary
sides as independent outcomes.

## Supplementary findings

- **Polymarket US:** a separate four-way comparison of **2,631 games**, with
  Brier scores 0.2303 / 0.2305 / 0.2304 / 0.2307 for Kalshi / Global /
  sportsbooks / US. US comparisons meet the same equivalence tolerance on
  this sample. These scores cannot be ranked against the headline scores
  because the games differ.
- **Reserved sample:** 264 games across 17 dates gave similar average accuracy
  for the two exchanges. The plan was written after the games were played but
  before the reserved data were accessed locally. This is a held-out
  comparison, not a prospective preregistered replication or a formal
  equivalence test. Sportsbook data were unavailable.
- **Timing:** forecasts become closer over the final day. Some specifications
  detect lagged predictability, and the minute-level exchange panel detects
  it in both directions. No consistent directional leader emerges. Rapid
  transmission and common information cannot be distinguished from
  independent forecasting; the live sportsbook series is an aggregate.
- **Other markets:** margin-of-victory, niche-sport, and championship results
  are exploratory. Championship payout ratios are descriptive probability
  proxies, not achievable returns. Differences in sample, horizon, and metric
  prevent identifying repetition or frequent resolution as a cause.
- **Validation:** an apparent extra-innings anomaly was withdrawn after a
  placebo reproduced the gap created by conditioning on a future game state.
  The supplementary Elo baseline has a result-availability timing limitation.
  The encompassing analysis is not used to support the conclusions.

Similar average forecast accuracy does not imply identical prices, independent
participants, or profitable trading. The report does not claim that separate
venues cannot be arbitraged, infer participant bankroll paths from aggregate
trade records, or treat hypothetical fee scenarios as realized customer returns.

## Status

The research report has been drafted and is undergoing final review. Saved
collection and analysis outputs are available for inspection. Their presence
does not mean that every exploratory analysis is a confirmed result.

## Reproducing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.make_results          # regenerates every figure and log
```

The suite is audit-gated: 79 data-quality checks run first and the suite halts
on failure rather than producing plausible output from bad input. (55 in
`results/logs/data_audit.log` + 24 in `results/logs/deep_audit.log`. Corrected
2026-09-15: this line read "73 checks", a figure that matches neither log nor
their sum.)

**What that command needs, stated plainly.** The suite reads the full
`data/processed/` set, but some microstructure and live files are not committed here (see *Data
availability* below) — so `make_results` runs for someone holding the banked
inputs, not for a fresh clone.

**So the frozen run's logs are committed instead.** All 65 are in
[`results/logs/`](results/logs/), stamped 2026-09-23, one per module, alongside
[`results/MANIFEST.md`](results/MANIFEST.md) (per-module runtime and status) and
the rendered tables in `results/report/`. The saved logs provide the reported numerical outputs; the research report
specifies which analyses support its conclusions. That is the intended route for a reader who wants to audit rather
than re-execute.

For a fresh clone, the readable entry point is
[`notebooks/data_tour.ipynb`](notebooks/data_tour.ipynb) — it ships its rendered
outputs, so the headline can be read straight off GitHub without executing
anything. Re-executing it needs one file beyond `analysis_core.csv` — the 70MB
trade tape `kalshi_trades_24h.csv`, which is held back for its size, not its
contents.

## Data availability — read this before judging reproducibility

**Exchange data is committed.** Kalshi and Polymarket are public APIs with no
authentication and no cost, so there is nothing to withhold: the price tables
for all three markets are here, not merely re-derivable from the collectors in
`src/collect/`. That includes
[`kalshi_hist_prices.csv`](data/processed/kalshi_hist_prices.csv),
[`polymarket_hist_prices.csv`](data/processed/polymarket_hist_prices.csv), and
[`polyus_prices.csv`](data/processed/polyus_prices.csv) with its catalogue —
the Polymarket US leg that `four_way.py` reads, which `analysis_core.csv` has
no column for — plus the ESPN registry and Kalshi settlement tables the joins
need.

**Sportsbook data is here too.** Historical odds came from The Odds API under a
paid plan — the proposal anticipated free sources, historical coverage turned out
to be paid, and the grant funded it. The per-bookmaker tapes are published
anyway: `sportsbook_hist_prices.csv` and `sportsbook_open_prices.csv` (the
closing and T-24h consensus), `sportsbook_us_books.csv` (11 US retail books),
`sportsbook_sharp_prices.csv` (28 books incl. Pinnacle and Betfair),
`sportsbook_outrights.csv` and `sportsbook_alt_spreads.csv` — 338,952 rows.
Anyone re-using them should check The Odds API's own terms, which govern that
data regardless of its appearing here. Consequences, stated plainly:
- What *is* committed is [`data/processed/analysis_core.csv`](data/processed/analysis_core.csv)
  — one de-vigged row per game, sufficient to reproduce the headline
  calibration results. It is the **three-way** table: Kalshi, Polymarket Global
  and the book consensus. 5,333 of its 10,118 rows carry all three; the rest
  carry one or two and exist for the niche-market and coverage analyses. It is
  sorted by date, so the first 603 rows — 2025-04-15 to 2025-05-22, before
  Polymarket and book collection began — are Kalshi-only and look empty on a
  first read. `DATA_DICTIONARY.md` tabulates exactly which venue is missing
  where, and why.
- The book *consensus* is published too — in `analysis_core.csv` and in
  [`games_master.csv`](data/processed/games_master.csv), the merged table with
  audit flags that `three_way.load()` reads.
- A third party still cannot independently *re-collect* the book leg without
  their own subscription, and the project's own access lapses September 2026.
- Not every table the suite reads is here. The headline three-way and four-way
  results rebuild from this repository; a handful of microstructure and live
  tables (the liquidity sweep, the 24h trade tape, the VPS snapshots) are too
  large for a git repository and remain banked locally.

**The four-way set is a file too.**
[`analysis_four_way.csv`](data/processed/analysis_four_way.csv) — 2,631 games
priced by all four venues, no missing values, rebuilt from the tables here and
reproducing `four_way.py`'s frozen log exactly (Brier 0.2303 / 0.2305 / 0.2304 /
0.2307). It is derived rather than frozen; `analysis_core.csv` remains the
artifact the suite ran on.

Every field is documented in [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md).
Four games are included in cross-venue detail under `data/exhibits/` (NBA
Finals G5, Super Bowl LX, a Thursday-night NFL game, and a walk-off) — 27-32
books at seven horizons, Kalshi tapes, and Polymarket paths, with per-game
coverage counts in `exhibits_manifest.csv`. Super Bowl LX has books and
Polymarket but no Kalshi tape: its game market is not locatable through the
public API, so that file is present and empty rather than quietly absent.

## Layout

```
src/collect/     API collectors (Kalshi, Polymarket Global + US, Odds API, ESPN)
src/normalize/   venue-specific price construction
src/match/       cross-venue game matching
src/analysis/    65 suite modules, one concern each (+8 standalone, not suite-gated)
src/make_results.py   regenerates everything
results/         figures, frozen logs/ (65, one per module), MANIFEST, report/ tables
docs/            findings log, methodology decisions, registered claims, figure map
notebooks/       data tour
```

## Methods

Brier scores; calibration plots and home-side calibration regressions;
multiplicative de-vigging with sensitivity checks; date-clustered comparisons
of predictive loss; two one-sided equivalence tests at ±0.001; a weekly block
bootstrap; and Benjamini–Hochberg adjustments for a documented family of 20
selected claims. Additional exploratory procedures are described in the report
and source modules.

Methodological working notes are kept in
[`docs/methodology-decisions.md`](docs/methodology-decisions.md). Where those
notes and the report differ, the report governs the interpretation of findings.

## License and use

Code is released under the [MIT License](LICENSE) for inspection and reproduction.
The repository also contains sportsbook-derived tables from The Odds API.
The code license does not confer rights to third-party data; consult the data
provider's terms before reuse. Independently recollecting the sportsbook inputs
requires access to the provider.

This is a forecast-evaluation research project, not a betting system.
