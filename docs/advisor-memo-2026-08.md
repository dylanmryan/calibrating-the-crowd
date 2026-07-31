To: Prof. Kuyper
From: Dylan Ryan
Date: August 1, 2026
Subject: Calibrating the Crowd — where the project stands, how I did it, and what I need from you

Hi Professor,

Here's a full update on the project. The short version: the data work and
analysis are done, the answer to the research question is clearer than I
expected it to be, and I'm about two weeks ahead of the schedule we set in
the proposal. What's left is writing the report and getting the repo ready
to go public. I've organized this around the questions the project ended up
answering, since each one builds on the last — and I've tried to explain not
just what I did but why I did it that way, since a lot of the methodology
choices came from problems I ran into. At the end there's a list of
questions where I could really use your direction.

THE SETUP, AND WHY I BUILT IT THIS WAY

The question is whether sports prediction markets (Kalshi, Polymarket) are
real forecasting instruments or just another way to gamble. The problem
with answering that directly is that nobody knows the "true" probability
the Yankees win tonight, so you can't grade prices against truth. My way
around it: grade them against sportsbooks, on the exact same games. Books
are a professional industry that's priced these games for decades — if the
crowd's prices behave like theirs, that's the best evidence available that
they're real forecasts. So I built a dataset where every game has a closing
price from Kalshi, from Polymarket, and from a sportsbook consensus, plus
the actual outcome. After all the cleaning that's 5,328 games across six
leagues.

A few decisions that shaped everything downstream:

- Everything is anchored to ESPN. Each market labels games its own way and
  Kalshi's timestamps are actually the game's END time (found that out the
  hard way), so I use ESPN's official start time as the moment I sample
  every price, and ESPN's final score as the outcome — one clock and one
  referee for all sources. I also cross-check outcomes against both
  markets' own settlements and throw out the ~2% of games where anything
  disagrees, because one wrong outcome poisons every analysis it touches.
- Sportsbook odds are padded (both teams priced like they're 52% likely —
  the extra is the vig). I rescale each source's two prices to sum to 100%
  so I'm comparing honest probabilities. Since there's more than one way
  to remove vig, I re-ran everything under two alternative methods; the
  conclusions don't move.
- Kalshi deletes price data ~60 days after a market closes. For older
  games I rebuilt prices from trade records (each trade says which side
  initiated it, so you can reconstruct the bid and ask). I didn't trust
  the reconstruction until I checked it against an independent archive of
  old order books — 99% of my reconstructed prices were within a cent.

QUESTION 1: DO THEY PRICE GAMES LIKE SPORTSBOOKS DO?

Yes, and the cleanest way to see it is the table I keep coming back to.
Take every team priced at X% to win and ask how often they actually won:

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

Teams priced 40% win about 43% of the time — at all three places. Teams
priced 90% win about 91-93% — at all three places. A dollar bet at any
price level returns about a dollar before fees, everywhere. Even the small
imperfections are shared (that little 40/60 flattening shows up identically
at the books), which tells you they're features of the games, not of any
venue.

The formal version: I score everyone with Brier scores (average squared
error of the probability — it punishes being confidently wrong) and get
0.2196 / 0.2199 / 0.2196. Two methodology points here that I'd flag as the
ones I most want your opinion on:

- Games played on the same day aren't independent — they share weather,
  news, correlated outcomes. So every significance test I run clusters by
  date. This isn't decoration: doing it properly killed a borderline
  "difference" between Kalshi and Polymarket that looked real with naive
  standard errors.
- "We found no significant difference" felt like a weak headline — maybe I
  just didn't have power. So I flipped it into an equivalence test (TOST):
  instead of failing to reject "they're different," I affirmatively show
  that any difference is smaller than 0.001 in Brier, which is about half
  a percent of probability per game — smaller than anyone's fees. That
  holds pooled and within each big league separately. I picked the 0.001
  margin because it's below any economically meaningful edge, but the
  choice is a judgment call and I'd like your read on it.

I also stress-tested the calibration result every way I could think of:
binning-free calibration curves (so the answer doesn't depend on how I
drew the bins), Murphy diagrams (which check every reasonable scoring rule
at once, so nobody can say "you'd get a different winner under a different
metric"), and a Bayesian hierarchical model that partial-pools the small
leagues so I can say something honest about them instead of "not enough
data" (answer: every league in every source is consistent with perfect
calibration).

QUESTION 2: ARE THEY ACTUALLY SMART, OR JUST UNBIASED?

This one matters because being calibrated is cheap — you can be perfectly
calibrated by hedging everything toward the base rate. So I built a
deliberately dumb fourth forecaster as a floor: an Elo rating model that
only knows win/loss records, strictly walk-forward (at every prediction it
only uses games that already happened — no peeking, and even the home-field
adjustment is estimated only from past games). All three markets beat it by
the same wide margin: model Brier 0.2348 vs about 0.2210 for everyone
(z around 7). The gap between the markets and the model is roughly 30 times
the gap between any two markets. And the model itself turns out to be
well-calibrated — just not sharp. That's the point: calibration is easy,
knowing things is hard, and all three institutions know the same large
amount beyond public statistics.

The one genuine flaw I found anywhere: Kalshi's thin MLB "win by X runs"
markets underprice narrow wins by about 8 points. The books price the same
thing correctly, so it's Kalshi-specific. But here's the part I think is
actually interesting: trading the mistake loses money after fees. The bias
survives because transaction costs protect it — the same way books carry
small biases inside their vig. That became a running theme.

QUESTION 3: DO PRICES FORM THE SAME WAY? DOES ANYONE LEAD?

I collected price paths at multiple horizons (a day out down to game time)
and ran a live collector on a cloud server that snapshots all three sources
every 15 minutes (now every 5). The picture: books hold a small, real
accuracy lead a full day out (p = 0.02), both exchanges sharpen along
basically identical curves, and the gap is gone by game time. From there I
kept zooming in — 15-minute data, then 1-minute data I built from exchange
candlesticks — and nobody leads at any resolution. When one venue's price
jumps, the others move within the same observation window or not at all. I
also ran an event study specifically around big sportsbook line moves,
because I wondered if the exchanges either see them coming or copy them.
Neither: about 80% of a big book line move is never echoed by the exchanges
at all, and the exchanges show no drift in the right direction beforehand.
One caveat I want to be upfront about: at the 1-minute level, part of the
"response takes a couple minutes" pattern could just be thin markets
recording a move whenever they next trade, not actual slow learning. That
can't fake the main conclusion (stale prints look symmetric, and symmetry
is the finding — a real leader would look asymmetric), but I'm not going to
oversell the speed interpretation.

QUESTION 4: SO WHAT'S ACTUALLY DIFFERENT?

Cost and design, not accuracy. A market-order bettor pays about 4.2% all-in
on Kalshi — statistically the same as the books' 4.1% vig. (The patient
limit-order path is nearly free, which books don't offer.) Polymarket
adding fees mid-sample was a lucky natural experiment: accuracy didn't
move at all, but relative trading volume dropped about 40% — the casual
money left, the market-makers stayed, and the quoted spread never budged.
On that last point I found something I didn't expect: 96-97% of all quotes
sit at exactly the exchanges' 1-cent minimum tick, so the spread isn't
really chosen by anyone — it's pinned at the legal floor. That also means
cheap contracts are structurally expensive to trade (a 1-cent spread is
20% of a 5-cent contract), which is part of what shelters that MLB bias.

QUESTION 5: WHY DOES SPORTS WORK SO WELL?

A paper from January (Bürgi, Deng & Whelan) studied all of Kalshi —
politics, weather, entertainment — and found ugly stuff: longshots losing
60%+ of their money, average returns around −20%. I re-ran their exact
analyses on my sports data and the pathologies just aren't there; losses
equal fees and nothing more. Also, Polymarket runs two legally separate
exchanges (the offshore one and a new CFTC-regulated US one) whose
customers can't trade on each other's platform — and their prices agree to
a median of half a cent on the same games. Nobody can arbitrage those two
books, so the agreement has to come from both crowds processing the same
public information. My best explanation for all of it: sports is the one
corner of prediction markets with a professional benchmark and thousands
of fast-resolving repeated events. Markets seem to forecast well where
something disciplines them. Honestly I think this might be the most
interesting sentence in the project.

THINGS THAT WENT WRONG (AND WHAT I DID ABOUT THEM)

I want to be straightforward about these because catching them changed how
I work.

- Early on a backtest showed impossible profits (+90% returns). Real
  markets don't do that, so I assumed my pipeline was broken — it was. Team
  codes were colliding and attaching the wrong team's price to some games.
  The durable fix came from noticing Kalshi's own ticker format encodes the
  home team; I validated that rule at 99.6% against ESPN and rebuilt side
  assignment on it. Since then my rule is: impossible results mean bugs.
- I ran a full code review near the end and it caught real stuff. My
  claims list had stale p-values — a result I liked ("the crowd adds
  information beyond the books") had weakened from p = 0.004 to about 0.05
  as the data grew, and its NBA sub-claim had died completely (p = 0.145).
  I downgraded one and retracted the other. Also, a reported MLB run-line
  bias turned out to be me scoring pushes as losses — with pushes handled
  right, the lines are calibrated and I retracted the claim.
- Two data-collection biases: my team-name matching silently dropped
  entire franchises (Montréal's accent, St. Louis's period, "LA Clippers")
  from the sportsbook data, and a pagination cap was dropping the most
  liquid games from the day-ahead sample. I fixed both and re-collected.
  Encouragingly, fixing them made the results stronger, not weaker — the
  books' day-ahead lead got more significant, and restoring ~280 missing
  games moved all three Brier scores identically and changed nothing.
- Because of all this I built two automated audit gates (73 checks —
  duplicates, impossible values, timestamps that would leak future
  information, cross-source sanity) that run before anything else; if a
  check fails, no results regenerate. And I keep an explicit inventory of
  every positive claim with false-discovery control (Benjamini–Hochberg;
  12 of 13 current claims survive at q = 0.05), with equivalence claims
  tracked separately under their TOST margins — my reasoning is that "we
  proved X exists" and "we proved X and Y are the same" are different
  kinds of statements and shouldn't share one correction. That separation
  is a judgment call I'd like you to check.

WHAT I NEED FROM YOU

Methodology calls (these gate the final write-up):
1. Is the two-family testing setup okay — FDR for discoveries, TOST for
   equivalences, kept separate? Or would you put everything in one family?
2. Is δ = 0.001 Brier a defensible equivalence margin, or would you anchor
   it to something else?
3. I cluster by date everywhere. Worth adding two-way (date × league)
   clustering as a robustness check?
4. For discrete margins (win-by-N), my distribution tests use randomized
   PIT. Fine, or show a discrete version alongside?
5. For lead–lag, I used predictive regressions plus event studies rather
   than formal information-share decompositions. Enough, or do you want
   the Hasbrouck-style machinery?

Direction:
6. What should the deliverable be — just the grant report, or shaped for
   a venue (Journal of Prediction Markets? IJF? arXiv)? This changes how
   I write it, and I can have a full draft to you within days of knowing.
7. When could you realistically turn around comments on a draft? Two
   rounds fit before Aug 24 if the first starts by about Aug 8.
8. Any concerns with making the repo public (secrets rotated) and the
   data plan — exchange prices are re-derivable from free APIs, book
   lines shipped as "code + instructions" rather than raw data?
9. Which framing should lead the paper: the equivalence result itself, or
   the Question-5 story about benchmarks disciplining markets?
10. The fall naturally extends this (college basketball, football season,
    the finer 5-minute data now accumulating). Is a follow-on something
    you'd be open to supervising?

Everything above regenerates from the repository with one command, and the
findings document has the full detail behind any number here. Looking
forward to your thoughts — especially on 6 and 7, since the writing
schedule hangs on them.

Thanks,
Dylan
