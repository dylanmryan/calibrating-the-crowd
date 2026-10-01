# Calibrating the Crowd

**Prediction markets and sportsbooks as rival forecasters of the same games.**

Undergraduate research project, BPF Undergraduate Research Grant, Department of
Statistics and Data Science, Northwestern University. Summer 2026.
Student: Dylan Ryan · Faculty mentor: Prof. Arend Kuyper.

---

## The question

If a contract trades at 60c, does that outcome happen about 60% of the time?
Prediction markets are defended as forecasting instruments and dismissed as
gambling dressed up as analysis. Sports are the cleanest place to adjudicate
that: outcomes are definitive, frequent, and — uniquely — already priced by a
professional industry that has been doing it for decades.

This project prices the **same games** through four institutionally distinct
mechanisms and asks whether they differ.

## The finding

On 5,333 games priced by all sources, a CFTC-regulated exchange (Kalshi), an
offshore crypto CLOB (Polymarket Global), a second US-regulated exchange
(Polymarket US), and the professional sportsbook complex — including Pinnacle
and eleven major US retail books — are a **statistical dead heat**.

| source | Brier | calibration slope | MCB (miscalibration) |
|---|---|---|---|
| Kalshi | 0.2196 | 0.964 | 1.31e-3 |
| Polymarket | 0.2198 | 0.961 | 1.33e-3 |
| Sportsbook consensus | 0.2196 | 1.008 | 1.45e-3 |

*Miscalibration is reported as CORP's **MCB** (isotonic, `referee.py` §4), not as
ECE. ECE is the number readers recognise, and it is an artifact of its bin count:
on this sample the level roughly triples between 5 and 20 bins and the venue that
looks best changes with it (`referee.py` §5). ECE at the conventional 10 bins is
0.009–0.013 across the three, against a binomial noise floor of 0.0095–0.0098 for
a sample this size — i.e. all three sit essentially at the floor. Quote ECE as a
level against that floor; never rank venues on it.*

Not merely "no significant difference" — formally equivalent under two
one-sided tests, with every pairwise 90% CI inside the pre-stated margin. The
equivalence holds against Pinnacle specifically, book-by-book across US retail,
within every adequately powered quarter, across every favourite-strength band,
at every news intensity, and across legally segregated pools that no
participant can arbitrage.

It also holds at **matched freshness**, which is the version that answers the
obvious objection. Book prices in this data are up to an hour old while exchange
prices are taken at kickoff, so a reader is entitled to ask whether the books
were simply handicapped by a stale quote. The collection cadence happens to
answer it: quote age is bimodal, and against Pinnacle quoted **within 10 minutes
of start** the gap is −0.004e-3 (z=−0.02, n=2,992) against a minimum detectable
effect of 0.49e-3 — an exact tie, at full power. The staleness penalty is
directionally real on all four legs (+0.06 to +0.41e-3, the sign the objection
predicts; +0.33 and +0.41e-3 on the two Kalshi legs, +0.06 and +0.27e-3 on the
Polymarket legs) and too small to detect at any n this project has.

Three things follow, and they are the actual contribution:

1. **Nobody leads, and nobody needs a benchmark.** No venue predicts another
   at 30, 15, 10 or 5-minute resolution, and the two exchanges do not predict
   each other at 1 minute — so if one venue's price is a function of another's,
   it is a same-step function, not a lag. (Corrected 2026-09-16: this line
   previously claimed 1-minute coverage for all three venues. The 1-minute
   panel is `k_mid` and `p_price` only — the book has no minute-level series,
   so 5 minutes is the finest clock on which it is measured at all.) The design
   cannot distinguish parallel discovery from continuous same-step mirroring,
   and the paper says so rather than picking the flattering reading: 99.5% of
   Kalshi's log-odds variation and 98.7% of Polymarket's is explained by the
   book consensus, and only Kalshi's residual carries detectable information
   (p=0.035, fragile). What *does* separate the venues from the book is that
   they price un-benchmarked niche markets — where no professional line exists
   to follow — just as well (excess ECE 0.00, slope 0.98).

   One limit of this leg is structural and worth stating next to the claim:
   "the sportsbook" in every *timing* result is a cross-book mean, because the
   live collector averaged the field at ingest. So "does Pinnacle lead the
   retail field?" is not identified by anything this project banked, at any
   resolution. `book_panel.py` bounds what that costs — membership churn is
   2.2% of steps but carries 54% of the consensus series' squared variation, and the
   ≥2pt event population is 7.4× enriched in it — and then re-runs the study on
   a constant-membership panel. The nulls survive: the exchanges' anticipation
   share moves *away* from chance when the artifacts are removed (Kalshi
   34%→26%, Polymarket 23%→21%), so the no-leader result is not an averaging
   artifact. The *accuracy* leg never had this problem — it is unpacked against
   Pinnacle and book-by-book below.
2. **The discipline has a boundary, and it is not the institution.** One-shot,
   long-horizon outrights are badly priced *everywhere* — Kalshi returns $0.33
   per $1 on sub-10c longshots, the books $0.34. Meanwhile un-benchmarked niche
   game markets are clean (excess ECE 0.00). What produces calibration is
   repetition and fast resolution, not regulation, liquidity, or the presence
   of a professional benchmark.
3. **Calibration disciplines the price; it does not protect the participant.**
   Structural taker cost is −4.6% per position. A weekly bettor keeps about
   30% of bankroll across a season. Twelve well-priced game bets cost the
   same as one badly-priced futures ticket.

**No anomaly survives, and the last candidate died of a bad test.** Until
2026-09-23 this section reported one: extra-inning baseball, where the
win-by-1-2 cell looked under-priced by about 20 points at Kalshi and at the
books alike. It was the project's third-longest-lived claim and it is
**retracted**, not because the number was wrong but because the statistic was.
Extra innings are realized *during* the game. Splitting a calibration test on a
state the forecaster could not observe breaks the calibration identity
mechanically, so the split returns the extras/margin dependence no matter whose
prices you feed it — a **constant at the unconditional base rate scores
+21.19pt on the same split**, and a pre-game-information-only forecast
+21.23pt, against the market's +20.22pt (`extras_conditioning.py` §1). A
constant cannot misprice the ghost-runner rule. The whole published gap was the
dependence, and extras are barely foreseeable anyway (cross-fitted AUC 0.540).

Tested the way calibration actually requires — is the pricing error predictable
from information the market *had*? — the cell comes back with the **opposite**
sign: a small over-pricing in extras-prone games (coef −1.1495, z=−3.00
date-clustered; ~4pt across the whole propensity range). That is reported as a
post-hoc finding at exactly that strength, not as a blind spot.

This is the project's fourth self-caught error and the second on this same cell:
an earlier, larger version ("Kalshi misprices small MLB margins") fell on
2026-08-23 to a league-specific settlement convention. The boundary thesis does
not depend on it — outrights and un-benchmarked niche games carry that argument,
and neither conditions on a realized state.

## Status

Evidence collection and analysis are **complete and frozen** (2026-08-29
freeze run; re-stamped 2026-09-03 at 61 modules with a robustness battery
added, 2026-09-16 at 63 with the book-consensus panel audit and the
quote-freshness leg, and **2026-09-23 at 65** with the conditioning audit that
retracted the extra-innings claim — every prior number reproducing unchanged
across all four stamps; 0 failures, audit-gated; every figure and table
regenerates from the frozen logs). A **registered
out-of-sample verification** — claims committed in `docs/registered-claims.md` before the
holdout was pulled — confirmed the exchange dead heat at full registered
power on fresh games (|ΔBrier| 0.04e-3 against an MDE of 0.81e-3),
and the structural cost, and resolved the one open observation (WNBA totals) as
a false alarm. Its extra-innings leg (R6) is **withdrawn**: as annotated in
`docs/registered-claims.md`, that claim was registered around a statistic a
constant forecaster would also have confirmed, so it could not fail and its
confirmation carries no information. The written report is **in progress**. This repository is the
reproducibility artifact promised in the grant proposal.

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
`data/processed/` set, and only two of those files are committed here (see *Data
availability* below) — so `make_results` runs for someone holding the banked
inputs, not for a fresh clone.

**So the frozen run's logs are committed instead.** All 65 are in
[`results/logs/`](results/logs/), stamped 2026-09-23, one per module, alongside
[`results/MANIFEST.md`](results/MANIFEST.md) (per-module runtime and status) and
the rendered tables in `results/report/`. Every number in the README and the
report can be checked against them without re-running anything and without the
book data. That is the intended route for a reader who wants to audit rather
than re-execute.

For a fresh clone, the readable entry point is
[`notebooks/data_tour.ipynb`](notebooks/data_tour.ipynb) — it ships its rendered
outputs, so the headline can be read straight off GitHub without executing
anything. Re-executing it needs one file beyond `analysis_core.csv`
(`kalshi_trades_24h.csv`, the trade tape) that carries de-vigged book prices and
is therefore not redistributed.

## Data availability — read this before judging reproducibility

**Exchange data is fully re-derivable.** Kalshi and Polymarket are public APIs
with no authentication and no cost. Anyone can rebuild that half from scratch
with the collectors in `src/collect/`.

**Sportsbook data is not.** Historical odds came from The Odds API under a paid
plan. The proposal anticipated free sources; historical coverage turned out to
be paid, and the grant funded it. Consequences, stated plainly:

- Raw book odds are **not redistributed** here.
- What *is* committed is [`data/processed/analysis_core.csv`](data/processed/analysis_core.csv)
  — one de-vigged row per game, all venues, sufficient to reproduce the
  headline calibration results.
- A third party cannot independently re-collect the book leg without their own
  subscription, and the project's own access lapses September 2026. Book data
  is banked locally and backed up.

Every field is documented in [`data/DATA_DICTIONARY.md`](data/DATA_DICTIONARY.md).
Four games are included in full cross-venue detail under `data/exhibits/`
(NBA Finals G5, Super Bowl LX, a Thursday-night NFL game, and a walk-off).

## Layout

```
src/collect/     API collectors (Kalshi, Polymarket Global + US, Odds API, ESPN)
src/normalize/   venue-specific price construction
src/match/       cross-venue game matching
src/analysis/    65 suite modules, one concern each (+8 standalone, not suite-gated)
src/make_results.py   regenerates everything
results/         figures, frozen logs/ (65, one per module), MANIFEST, report/ tables
docs/            findings log, report outline, drafting plan, methodology decisions
notebooks/       data tour
```

## Methods

Brier and log score with Murphy decomposition and CORP; multiplicative de-vig
with Shin as robustness; date-clustered Diebold–Mariano; TOST equivalence
against a pre-stated margin; interval-randomized PIT for discrete predictive
distributions; ranked probability score for ordered outcomes; Benjamini–Hochberg
FDR over positive claims with equivalence claims held in a separate family and
disciplined by a minimum-detectable-effect table.

Each of those choices, including the ones declined and why, is written up in
[`docs/methodology-decisions.md`](docs/methodology-decisions.md).

## Reading the results honestly

Underpowered subgroups are reported with their MDE, not as evidence of sameness
(CFB, WNBA, and NFL cannot detect the effect size at issue). Suggestive results
are labelled suggestive and do not become claims. Eleven claims have been
**retracted, downgraded, or resolved as false alarms in place** as the sample
grew or the pipeline was audited — four on 2026-08-23, when a league-specific
settlement convention turned out to be generating the project's one "venue
defect"; one on 2026-08-29, when the WNBA totals rejection dissolved on the
frozen sample and flipped sign on the registered holdout; and one on
2026-09-03, when the FDR inventory was rebuilt to re-derive its p-values from
the logs instead of carrying them, and a Murphy sup-t claim it had been
carrying at p=0.037 turned out to read 0.129 on the frozen data. The full
record is kept at the top of `src/analysis/multiple_testing.py` rather than
quietly dropped.

Those corrections did not all run one way, which is the question a reader
should ask. Four removed a claim that Kalshi had a *defect*; four removed a
claim that Kalshi was *better*. What is true of nearly all of them is that they
moved toward the null — which is what you would see if the null were true, and
also what you would see from a pipeline whose cleaning shrinks extreme
estimates. The registered out-of-sample verification exists to separate those
two readings, and it replicated the dead heat on games collected after the
claims were fixed.

The headline is also reported against the choices that produced it, because a
result stated once is weaker than the same result stated five ways.
`robustness_cuts.py` re-runs the three-way equivalence by favourite strength
(a difference confined to heavy favourites would not show in a pooled Brier),
by which of two instruments produced the Kalshi price (~80% of closes are
reconstructed from the trade tape, and `validate_recon.py` checks that
reconstruction against a third party's archived order books), under four
book-consensus constructions including a line-shopped one, and with the 1.5%
of games where settlements disagree put back in. `rigor.py` re-estimates every
differential at six clustering levels. Nothing moves: the verdict is the same
in every cut, and each null carries its MDE.

`book_freshness.py` (added 2026-09-16) reads a field that had sat unused in both
per-book tapes — each bookmaker's own `last_update` — and turns the design's one
timing asymmetry from a stated caveat into a measurement, re-running the headline
inside each arm of a bimodal quote-age split. It also carries the only per-book
*timing* result the banked data supports: both exchanges price closer to the
books that updated most recently (Kalshi −0.021pt, Polymarket −0.030pt), which is
proximity rather than precedence and is reported as such.

`book_panel.py` (added 2026-09-16) does the same job for the benchmark's fitness
as a *timing* instrument rather than as a forecast — the one attack the
robustness battery had not answered. It measures how much of the consensus
series is membership churn rather than repricing, re-detects the book-move
events on a constant-membership panel, and states plainly which question the
banked data cannot answer at all. Its one new positive finding is reported as
such: cleaning the panel reveals a book→Polymarket coefficient in the final two
hours (+0.070, z=+2.6) that the pooled panel hides — and three identification
cuts in the same log read it as a resting quote catching up to a drifting
consensus, not news transmission.

## License and use

Released under the [MIT License](LICENSE) for inspection and reproduction.

Note on data: the committed derived files (`data/processed/analysis_core.csv`,
`data/processed/recon_validation.csv`) are included so the headline results can be
verified. Raw sportsbook odds are **not** redistributed here — see *Data
availability* above. Anyone rebuilding the book leg needs their own Odds API
subscription.

Not investment advice, not a betting system, and deliberately not framed as one —
the project's question is whether these venues forecast well, never whether they
can be beaten.
