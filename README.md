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
within every adequately powered quarter, and across legally segregated pools
that no participant can arbitrage.

Three things follow, and they are the actual contribution:

1. **Nobody leads.** No venue predicts another at 30, 15, 10, or 5-minute
   resolution. Price discovery is maker-driven and parallel, not transmitted.
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

One genuine anomaly survives every correction: extra-inning baseball games.
Extras end within one run 70% of the time (the ghost-runner rule), and the
win-by-1-2 cell is under-priced in that state by about 20 points — by Kalshi
and by the sportsbooks, by the same amount. An earlier, larger version of this
anomaly ("Kalshi misprices small MLB margins") was retracted on 2026-08-23
when a league-specific settlement convention surfaced in the ladder data; what
remains after the fix is smaller, shared by every institution, and a cleaner
instance of the paper's thesis: rare, slow-feedback states are mispriced
everywhere, exactly like one-shot outrights.

## Status

Evidence collection and analysis are **complete and frozen** (2026-08-29
freeze run; re-stamped 2026-09-03 at 61 modules with a robustness battery
added, every prior number reproducing unchanged; 0 failures, audit-gated;
every figure and table regenerates from the frozen logs). A **registered
out-of-sample verification** — claims committed in `docs/registered-claims.md` before the
holdout was pulled — confirmed the exchange dead heat at full registered
power on fresh games (|ΔBrier| 0.04e-3 against an MDE of 0.81e-3),
replicated the extra-innings blind spot (+19.6pt vs +20.2pt frozen) and the
structural cost, and resolved the one open observation (WNBA totals) as a
false alarm. The written report is **in progress**. This repository is the
reproducibility artifact promised in the grant proposal.

## Reproducing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m src.make_results          # regenerates every figure and log
```

The suite is audit-gated: 73 data-quality checks run first and the suite halts
on failure rather than producing plausible output from bad input.

Start here instead if you just want to see the headline reproduce from a clean
load: [`notebooks/data_tour.ipynb`](notebooks/data_tour.ipynb).

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
src/analysis/    61 analysis modules, one concern each
src/make_results.py   regenerates everything
results/         figures + MANIFEST (per-module runtime and status)
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
are labelled suggestive and do not become claims. Ten claims have been
**retracted, downgraded, or resolved as false alarms in place** as the sample
grew or the pipeline was audited — four on 2026-08-23, when a league-specific
settlement convention turned out to be generating the project's one "venue
defect," and one on 2026-08-29, when the WNBA totals rejection dissolved on
the frozen sample and flipped sign on the registered holdout. The full record
is kept at the top of `src/analysis/multiple_testing.py` rather than quietly
dropped.

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

## License and use

Research code, released for inspection and reproduction. Not investment advice,
not a betting system, and deliberately not framed as one — the project's
question is whether these venues forecast well, never whether they can be beaten.
