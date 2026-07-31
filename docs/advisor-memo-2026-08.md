MEMO

To: Prof. Arend Kuyper
From: Dylan Ryan
Date: August 1, 2026
Re: Calibrating the Crowd — progress, findings, and questions for direction

---

1. SUMMARY

The project asks whether sports prediction markets are genuine forecasting
instruments or another form of gambling, using sportsbooks as the
professional benchmark. Measurement is complete: on 5,328 games priced by
Kalshi, Polymarket, and a de-vigged sportsbook consensus, the three (and a
fourth leg, Polymarket's separate US exchange) produce statistically
equivalent forecasts, formally so, at every price level, in every league,
under every proper scoring rule. Where they differ is cost and mechanism,
not accuracy. I am roughly two weeks ahead of the original schedule; what
remains is the written report and public release. Below I organize
everything around the five questions the project ended up answering, then
the process, the problems I found and fixed, and the specific decisions I
need from you.

2. THE RESEARCH QUESTIONS AND WHAT I FOUND

Question 1 — Do prediction markets price games the way sportsbooks do?
Yes, and the plainest evidence is one table. Of all teams priced at X% to
win (both sides of every game, closing prices, same games at all three
institutions):

    priced   Kalshi won   Polymarket won   Sportsbook won
    10%      8.9%         8.8%             7.3%
    20%      22.6%        22.7%            22.6%
    30%      30.7%        31.2%            29.1%
    40%      43.3%        43.2%            44.1%
    50%      50.0%        50.2%            50.0%
    60%      56.8%        56.4%            55.9%
    70%      69.2%        68.9%            70.9%
    80%      77.1%        77.4%            77.4%
    90%      91.1%        91.2%            92.7%

A dollar staked at any price returns about a dollar gross, everywhere; the
fee is the entire house edge. Even the small deviations (a mild flattening
around 40/60) appear identically at the books — they are properties of the
games, not of any venue. Formally: Brier scores 0.2196 / 0.2199 / 0.2196;
no pairwise difference is significant with date-clustered errors; and by
equivalence testing (TOST) every pairwise difference is bounded within
±0.001 Brier — pooled, and separately within MLB, NBA, and NHL. No
favorite–longshot bias anywhere. This holds under every proper scoring
rule simultaneously (Murphy diagrams with a sup-t test).

Question 2 — Do they know as much as the books, or are they just unbiased?
They know as much. Against a deliberately naive fourth forecaster (a
walk-forward Elo model built only from win/loss records, no look-ahead),
all three markets are better by the same wide margin: model Brier 0.2348
vs ~0.2210 for every market (z ≈ 7.4). The markets differ from each other
by less than a thirtieth of that gap. Notably the naive model is itself
well-calibrated — it is just not sharp. Calibration is cheap; information
is the product, and all three institutions carry the same large amount.
The one real crack: Kalshi's thin MLB margin ladders underprice narrow
wins by ~8 points (the books price the same cell correctly), and the
mispricing is unexploitable after fees — a bias sheltered inside
transaction costs exactly the way books shelter biases inside vig.

Question 3 — Do prices form the same way, and does anyone lead?
The books hold a small, real accuracy lead a full day out (p = 0.020);
both exchanges then sharpen along statistically identical paths and the
gap is gone by game time. At 15-minute and 1-minute resolution no venue
leads: big repricings land within the same observation step everywhere,
cross-venue predictability is symmetric and economically trivial, and an
event study around large book line moves shows the exchanges neither
anticipate them (significantly less often than chance, for Polymarket)
nor chase them — about 80% of a big book move is never echoed at all,
consistent with most line moves being book-specific rather than news.
Trade-level evidence says prices move through market-makers revising
quotes on public information, not through informed bettors.

Question 4 — What actually differs?
Cost and market design. A market-order bettor pays ~4.2% all-in on Kalshi,
statistically the same as the books' ~4.1% vig; the patient limit-order
path costs nearly nothing, which books do not offer. When Polymarket
introduced fees mid-sample, accuracy did not move; casual volume left
(−41% relative) while the quoted spread never budged — it is pinned at
the exchanges' 1-cent minimum tick 96-97% of the time, so the "price of
liquidity" is set by exchange design rather than dealer choice. That tick
also makes Kalshi's low-priced tail contracts structurally expensive
(a 1-cent floor is 20%+ of a 5-cent contract), which is partly what
shelters the MLB bias above.

Question 5 — Why does sports work so well?
A January 2026 paper (Bürgi, Deng & Whelan) found the rest of Kalshi —
politics, weather, culture — has a strong favorite–longshot bias and −20%
average returns. Replicating their analyses on sports: the pathologies
vanish; losses equal fees. And Polymarket's two legally separated
exchanges (offshore Global and the CFTC-regulated US entity, whose
customers cannot arbitrage each other) agree to a median half a cent on
the same games. Together these point at a mechanism: sports is the corner
of the prediction-market world with a professional benchmark and
thousands of fast-resolving repeated events. Markets forecast well where
something disciplines them.

How the parts fit: Q1 establishes the equivalence; Q2 shows it is
equivalence of information, not shared blandness; Q3 shows the prices are
produced the same way, in parallel, with no one copying anyone; Q4
isolates what actually distinguishes the institutions; Q5 explains why
this asset class behaves so well. The thesis in one line: at the retail
surface a prediction market functions like a sportsbook; in aggregate it
is a forecasting instrument; and the benchmark that lets us measure this
is plausibly also the discipline that causes it.

3. PROCESS AND RELIABILITY

All data comes from free public APIs except the sportsbook lines (The
Odds API, purchased in planned batches). Prices are sampled at ESPN's
official start times; outcomes are cross-checked against both platforms'
settlements. Older Kalshi prices are reconstructed from trade records — a
method validated against an independent order-book archive (99% within
one cent). Every number regenerates from one command: a 40-module suite
that begins with two automated audit gates (73 checks — uniqueness,
ranges, no look-ahead, cross-source coherence, side-flip signatures) that
block regeneration if anything fails. Positive claims are inventoried
with per-claim provenance and controlled with Benjamini–Hochberg (12 of
13 survive q = 0.05); equivalence claims are stated via TOST margins,
separately.

4. ISSUES FOUND AND FIXED

The project's checks caught its own errors several times; in every case
the headline conclusions survived, and twice they strengthened.

- A side-assignment bug (prices attached to the wrong team) was exposed
  by impossible backtest profits, fixed structurally via Kalshi's ticker
  convention, and validated at 99.6%.
- A full code review found the claims inventory carrying stale p-values:
  an "exchanges add information beyond the books" result weakened from
  p = 0.004 to ~0.05 as the sample grew, and its NBA sub-claim failed
  outright. Both are downgraded/retracted in the findings.
- The reported MLB run-line bias (home sides covering 45%) turned out to
  be an artifact of scoring pushes as losses; corrected, the main lines
  are calibrated. Retracted.
- Team-name matching had silently dropped three franchises (Clippers,
  Canadiens, Blues) from the sportsbook data; fixed and re-collected.
  Restoring ~280 team-correlated missing games moved Briers ~0.001
  uniformly and changed nothing — an accidental selection test, passed.
- A pagination cap had dropped the most liquid games from the day-ahead
  sample; re-collected at depth, the books' T−24h lead strengthened
  (p = 0.029 → 0.020). Fixing our own selection bias made the result
  stronger, which is what one hopes real results do.

5. QUESTIONS FOR YOU

Methodology rulings that gate the final write-up:
1. Multiple testing: is the two-family policy defensible — BH-FDR over
   positive discoveries, TOST margins for equivalences, kept separate?
2. Equivalence margin: is δ = 0.001 Brier (≈0.5% probability error per
   game, below any fee) a reasonable convention, or would you anchor it
   differently?
3. Inference: date-clustered errors everywhere; worth adding two-way
   (date × league) as robustness?
4. The PIT tests use interval randomization for discrete margins — is
   that sufficient, or should a discrete variant be shown alongside?
5. Lead–lag: are predictive regressions plus event studies the right
   formality, or would you want Hasbrouck-style information shares?

Direction for the remaining month:
6. What should the deliverable be — grant report only, or shaped for a
   venue (Journal of Prediction Markets, IJF, an arXiv preprint)? This
   decides length and voice; I can have a full draft to you within days
   of knowing.
7. When could you turn around comments on a first draft? Two review
   cycles fit before the Aug 24 end if the first starts by ~Aug 8.
8. Public release: any concerns with making the repository public
   (secrets rotated) and with the data-sharing plan — exchange prices
   are re-derivable from free APIs; book lines shipped as code +
   instructions rather than raw data?
9. Is the strongest framing the equivalence itself, or the Question-5
   mechanism story (benchmark discipline), as the paper's lead?
10. The fall extension (college basketball, football season, the
    accumulating 5-minute panel and depth data) runs past the grant.
    Is a follow-on study something you would want to supervise?

6. NEXT STEPS

Report drafting begins now against the finished results; the live
collector keeps accumulating the finer 5-minute panel for one remaining
open cell (whether book-vs-exchange simultaneity holds below 15 minutes);
public-release preparation is scheduled for the final week. Everything
in this memo regenerates from the repository with one command.
