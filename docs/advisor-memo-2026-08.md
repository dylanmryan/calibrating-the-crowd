To: Prof. Kuyper
From: Dylan Ryan
Date: August 1, 2026
Subject: Calibrating the Crowd: progress, methodology, and questions for direction

Hi Professor,

Here is a full update on the project. The data collection and analysis are
done, the answer to the research question came out clearer than I expected,
and I am about two weeks ahead of the schedule in the proposal. What
remains is writing the report and preparing the repository to go public. I
organized this update around the questions the project ended up answering,
since each one builds on the last. I have also tried to explain not just
what I did but why I did it that way, since most of the methodology
choices came out of problems I ran into. At the end is a list of questions
where I need your direction.

THE SETUP, AND WHY I BUILT IT THIS WAY

The question is whether sports prediction markets (Kalshi, Polymarket) are
real forecasting instruments or just another way to gamble. The difficulty
in answering that directly is that nobody knows the true probability that
a given team wins tonight, so prices cannot be graded against truth. My
way around it was to grade them against sportsbooks on the exact same
games. Books are a professional industry that has priced these games for
decades. If the crowd's prices behave like theirs, that is the best
available evidence that they are real forecasts. So I built a dataset
where every game has a closing price from Kalshi, from Polymarket, and
from a sportsbook consensus, plus the actual outcome. After cleaning,
that is 5,328 games across six leagues.

A few decisions shaped everything downstream:

- Everything is anchored to ESPN. Each market labels games its own way,
  and Kalshi's timestamps turn out to mark the end of the game rather
  than the start, so I use ESPN's official start time as the moment I
  sample every price and ESPN's final score as the outcome. One clock and
  one referee for all sources. I also cross-check outcomes against both
  markets' own settlements and drop the roughly 2% of games where
  anything disagrees, because a single wrong outcome contaminates every
  analysis it touches.
- Sportsbook odds are padded. Both teams are often priced as if they were
  52% likely, and the extra is the vig. I rescale each source's two
  prices to sum to 100% so I am comparing honest probabilities. Since
  there is more than one way to remove vig, I re-ran everything under two
  alternative methods, and the conclusions do not move.
- Kalshi deletes price data about 60 days after a market closes. For
  older games I rebuilt prices from trade records, which is possible
  because each trade shows which side initiated it, so the bid and ask
  can be reconstructed. I did not trust the reconstruction until I
  checked it against an independent archive of old order books. 99% of
  the reconstructed prices were within one cent.

QUESTION 1: DO THEY PRICE GAMES THE WAY SPORTSBOOKS DO?

Yes, and the simplest evidence is one table. Take every team priced at X%
to win and ask how often those teams actually won:

    priced   Kalshi   Polymarket   Sportsbook
    10%      8.9%     8.8%         7.3%
    20%      22.6%    22.7%        22.6%
    30%      30.7%    31.2%        29.1%
    40%      43.3%    43.2%        44.1%
    50%      50.0%    50.2%        50.0%
    60%      56.8%    56.4%        55.9%
    70%      69.2%    68.9%        70.9%
    80%      77.1%    77.4%        77.4%
    90%      91.1%    91.2%        92.7%

Teams priced 40% win about 43% of the time at all three institutions.
Teams priced 90% win about 91-93% at all three. A dollar staked at any
price level returns about a dollar before fees, everywhere. Even the
small imperfections are shared. The slight flattening around 40/60 shows
up identically at the books, which says it is a feature of the games and
not of any venue.

The formal version scores everyone with Brier scores (the average squared
error of the stated probability, which penalizes confident wrongness) and
gets 0.2196, 0.2199, and 0.2196. Two methodology points here are the ones
I most want your opinion on:

- Games played on the same day are not independent. They share weather,
  news, and correlated outcomes, so every significance test clusters
  standard errors by date. This is not decoration. Clustering properly
  eliminated a borderline difference between Kalshi and Polymarket that
  looked real under naive standard errors.
- "No significant difference" felt like a weak headline, since it could
  just reflect low power. I flipped it into an equivalence test (TOST).
  Instead of failing to reject that the sources differ, I show
  affirmatively that any difference is smaller than 0.001 in Brier score,
  which is about half a percentage point of probability per game and
  smaller than anyone's fees. That holds pooled and within each big
  league separately. I chose the 0.001 margin because it sits below any
  economically meaningful edge, but it is a judgment call and I would
  like your read on it.

I also stress-tested the calibration result in several ways: binning-free
calibration curves so the answer does not depend on how bins are drawn,
Murphy diagrams that check every reasonable scoring rule at once, and a
Bayesian hierarchical model that partial-pools the small leagues so I can
say something honest about them instead of "not enough data." The result
is that every league in every source is consistent with perfect
calibration.

QUESTION 2: ARE THEY ACTUALLY INFORMED, OR JUST UNBIASED?

This matters because calibration alone is cheap. A forecaster can be
perfectly calibrated by hedging everything toward the base rate. So I
built a deliberately simple fourth forecaster as a floor: an Elo rating
model that only knows win/loss records, run strictly walk-forward so that
every prediction uses only games that had already happened. Even the
home-field adjustment is estimated only from past games. All three
markets beat the model by the same wide margin: model Brier 0.2348
against roughly 0.2210 for every market, with z around 7. The gap between
the markets and the model is about thirty times the gap between any two
markets. The model itself turns out to be well calibrated, just not
sharp. That is the point. Calibration is easy, information is hard, and
all three institutions carry the same large amount of it beyond public
statistics.

The one genuine flaw I found anywhere: Kalshi's thin MLB win-by-X-runs
markets underprice narrow wins by about 8 points. The books price the
same outcomes correctly, so the blind spot is Kalshi-specific. The part I
find most interesting is that trading the mistake loses money after fees.
The bias survives because transaction costs protect it, the same way
books carry small biases inside their vig. That pattern repeats
throughout the project.

QUESTION 3: DO PRICES FORM THE SAME WAY? DOES ANYONE LEAD?

I collected price paths at multiple horizons, from a day out down to game
time, and ran a live collector on a cloud server that snapshots all three
sources every 15 minutes (recently increased to every 5). The picture:
the books hold a small but real accuracy lead a full day out (p = 0.02),
both exchanges sharpen along nearly identical curves, and the gap is gone
by game time. From there I kept zooming in, first with 15-minute data and
then with 1-minute data built from exchange candlesticks, and no venue
leads at any resolution. When one venue's price jumps, the others move
within the same observation window or not at all. I also ran an event
study specifically around large sportsbook line moves, to test whether
the exchanges either anticipate them or copy them. Neither happens. About
80% of a large book line move is never echoed by the exchanges at all,
and the exchanges show no drift in the right direction beforehand. One
caveat I want to state plainly: at the 1-minute level, part of the
apparent two-to-three-minute response time could just be thin markets
recording a move whenever they next trade, rather than slow learning.
That cannot fake the main conclusion, since stale prints produce
symmetric patterns and symmetry is the finding, but I will not oversell
the speed interpretation.

QUESTION 4: WHAT IS ACTUALLY DIFFERENT?

Cost and market design, not accuracy. A market-order bettor pays about
4.2% all-in on Kalshi, statistically the same as the books' 4.1% vig.
The patient limit-order path costs nearly nothing, which books do not
offer. Polymarket adding fees mid-sample was a useful natural experiment:
accuracy did not move at all, but relative trading volume dropped about
40%. The casual money left, the market-makers stayed, and the quoted
spread never moved. On that last point I found something I did not
expect. Between 96% and 97% of all quotes sit at exactly the exchanges'
one-cent minimum tick, so the spread is not really chosen by anyone. It
is pinned at the legal floor. That also means cheap contracts are
structurally expensive to trade, since a one-cent spread is 20% of a
five-cent contract, and that is part of what shelters the MLB bias
described above.

QUESTION 5: WHY DOES SPORTS WORK SO WELL?

A paper from January (Bürgi, Deng and Whelan) studied all of Kalshi,
including politics, weather, and entertainment, and found serious
problems: longshots losing over 60% of their money and average returns
around -20%. I re-ran their analyses on my sports data and the
pathologies are simply not there. Losses equal fees and nothing more. In
addition, Polymarket runs two legally separate exchanges, the offshore
platform and a new CFTC-regulated US entity, whose customers cannot trade
on each other's books. Their prices agree to a median of half a cent on
the same games. Since nobody can arbitrage between them, the agreement
has to come from both crowds processing the same public information. My
best explanation for all of this is that sports is the one corner of
prediction markets with a professional benchmark and thousands of
fast-resolving repeated events. Markets appear to forecast well where
something disciplines them. I think this may be the most interesting
claim in the project.

THINGS THAT WENT WRONG, AND WHAT I DID ABOUT THEM

I want to be direct about these because catching them changed how I work.

- Early on, a backtest showed impossible profits of about +90%. Real
  markets do not leave that on the table, so I assumed my pipeline was
  broken, and it was. Team codes were colliding and attaching the wrong
  team's price to some games. The durable fix came from noticing that
  Kalshi's ticker format encodes the home team. I validated that rule at
  99.6% against ESPN and rebuilt side assignment on it. My rule since
  then: impossible results mean bugs.
- A full code review near the end caught real problems. My claims
  inventory had stale p-values. A result I liked, that the crowd adds
  information beyond the books, had weakened from p = 0.004 to about 0.05
  as the data grew, and its NBA sub-claim had failed entirely (p = 0.145).
  I downgraded the first and retracted the second. Separately, a reported
  MLB run-line bias turned out to come from scoring pushes as losses.
  With pushes handled correctly the lines are calibrated, and I retracted
  that claim as well.
- Two data-collection biases: my team-name matching silently dropped
  entire franchises from the sportsbook data (the accent in Montréal, the
  period in St. Louis, "LA Clippers" versus "Los Angeles Clippers"), and
  a pagination cap was dropping the most liquid games from the day-ahead
  sample. I fixed both and re-collected. Fixing them made the results
  stronger rather than weaker. The books' day-ahead lead became more
  significant, and restoring about 280 missing games moved all three
  Brier scores identically and changed no conclusion.
- Because of all this I built two automated audit gates, 73 checks in
  total covering duplicates, impossible values, timestamps that would
  leak future information, and cross-source sanity. They run before
  anything else, and if a check fails, no results regenerate. I also keep
  an explicit inventory of every positive claim under false-discovery
  control (Benjamini-Hochberg; 12 of 13 current claims survive at
  q = 0.05), with equivalence claims tracked separately under their TOST
  margins. My reasoning is that proving an effect exists and proving two
  things are the same are different kinds of statements and should not
  share one correction. That separation is a judgment call I would like
  you to check.

WHAT I NEED FROM YOU

Methodology calls that gate the final write-up:
1. Is the two-family testing setup defensible, with FDR for discoveries
   and TOST margins for equivalences kept separate? Or would you put
   everything into one family?
2. Is 0.001 Brier a defensible equivalence margin, or would you anchor it
   to something else?
3. I cluster by date everywhere. Is two-way clustering (date by league)
   worth adding as a robustness check?
4. For discrete margins (win by N), my distribution tests use randomized
   PIT. Is that sufficient, or should a discrete version be shown
   alongside?
5. For lead-lag, I used predictive regressions plus event studies rather
   than formal information-share decompositions. Is that enough, or would
   you want the Hasbrouck-style machinery?

Direction:
6. What should the deliverable be: the grant report only, or something
   shaped for a venue (Journal of Prediction Markets, IJF, arXiv)? This
   changes how I write it, and I can have a full draft to you within days
   of knowing.
7. When could you realistically turn around comments on a draft? Two
   rounds fit before August 24 if the first starts by about August 8.
8. Any concerns with making the repository public (secrets rotated) and
   with the data plan? Exchange prices are re-derivable from free APIs,
   and book lines would ship as code plus instructions rather than raw
   data.
9. Which framing should lead the paper: the equivalence result itself, or
   the Question 5 argument that benchmarks discipline markets?
10. The fall naturally extends this work (college basketball, football
    season, the finer 5-minute data now accumulating). Is a follow-on
    study something you would be open to supervising?

Everything above regenerates from the repository with one command, and the
findings document contains the full detail behind any number here. I would
especially appreciate answers on 6 and 7, since the writing schedule
depends on them.

Thanks,
Dylan
