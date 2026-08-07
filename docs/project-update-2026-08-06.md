# Project update, week of Aug 4

Quick update on what happened since the last memo. Short version: the
evidence side of the project is now finished, the main conclusion got
sharper (and one part of it changed), and I spent the last of the data
budget banking everything we will need after the API subscription ends.
Writing is next.

## The big change: what actually disciplines these markets

Going into the week, the story was that sports prediction markets are
accurate because a sportsbook benchmark exists alongside repeated,
fast-resolving games. Those two ingredients were tangled together, so I
spent the week separating them, and the answer surprised me.

First I tested markets with no benchmark at all. Kalshi lists game
markets for things like table tennis, T20 cricket, esports, and
Bolivian league soccer, where there is no meaningful US sportsbook line.
I priced about a thousand of these settled contracts the same way as the
main sample. They are calibrated: no detectable miscalibration once you
account for the sample size, slope 0.98, and the three-way soccer prices
still sum to about 1.02. No benchmark needed.

Then I tested the books themselves on one-shot markets. I pulled
championship futures odds from 27 books, monthly, for every big-4 season
back to 2020-21 (20 completed seasons total). Longshots priced under 10
cents at the books returned about 34 cents on the dollar, basically
identical to Kalshi's 33 cents on its own futures. Polymarket's futures
show the same direction. So the failure is not an exchange problem, and
the success is not a benchmark or liquidity effect (the big futures
markets have deep books and misprice anyway). The revised one-liner for
the paper: repeated, fast-resolving markets price well at every
institution, one-shot long-horizon markets price badly at every
institution, and the institutions mainly differ in what they charge.

## The dead heat passed its two hardest tests

The accuracy comparison had been against an average of US retail books.
I re-collected the whole closing sample from the EU region, which
includes Pinnacle (the "sharp" book academics treat as the true price)
and kept every book separately this time. Results: the exchanges are
statistically equivalent to Pinnacle itself, and equivalent to each of
11 US books one at a time, including DraftKings and FanDuel. Also ran
the classic Levitt test (do retail books shade lines to exploit bettor
biases) on 30+ books across two continents: deviations from Pinnacle are
under one point everywhere and mostly the wrong sign for shading. That
idea appears to be dead in modern data.

## The "betting against the house" question

You may have seen the More Perfect Union video or the lawsuits claiming
Kalshi users unknowingly bet against Kalshi's own trading affiliate. I
dug into this properly. Nobody publishes which markets the affiliate is
in, so I measured what is observable: covered-league games have about
$800K of standing liquidity per market at 1 cent spreads, niche games
have about $6K, and most outright markets have no two-sided book at all.
Takers lose about 5 percent of stake either way (7 percent where the
professional book is absent, statistically the same), so the data does
not support the idea that the house's presence hurts customers. What the
house's presence actually determines is whether a market exists at all
and how precise it is. This section of the report now speaks directly to
the CFTC rule proposal from July 30 about affiliated market makers,
which is nice timing.

## Data and budget housekeeping

The API subscription ends September 1 and we are not renewing. I spent
the remaining credits deliberately: finished the day-ahead lines (84
percent coverage), the per-book EU and US records, extended the futures
snapshots back to 2020, and grabbed four case-study games in full detail
for the report (the NBA Finals clincher, the Super Bowl, the biggest
game in our trade tape, and a 10-inning walk-off that illustrates the
one real Kalshi weakness we found). About 11K credits remain, which is
exactly what the live collector needs through the end of the project.
Everything is backed up in three places and every analysis runs from
stored files, so nothing depends on the subscription after it lapses.

For your hands-on request: the repo now has a documented core dataset
(analysis_core.csv, one row per game with every venue's price), a data
dictionary explaining every file, and a starter notebook that reproduces
the headline table from scratch. Clone the repo and open
notebooks/data_tour.ipynb and you should be able to poke at everything.

## Where the numbers stand

Five thousand three hundred twenty-eight games priced by all three main
sources. Brier scores 0.2196, 0.2199, 0.2196. Every pairwise comparison
formally equivalent, including against Pinnacle. Books keep one real
edge, margin-of-victory distributions, and even that turns out to be
concentrated in baseball (the NHL comparison is an exact tie). Sixteen
positive findings survive multiple-testing control at the strict level
for thirteen of them, and the two that weakened as data grew are
reported as suggestive rather than quietly kept.

## Next steps

The report outline is done, with every number tied to a regenerated log
file, and two new summary figures (the equivalence forest plot and the
one-shot-markets chart). I start prose this week in grant-report form
unless you would rather see a different format. Mid-August: the 5-minute
line-movement study once that data matures, then a small out-of-sample
check where I verify the headline claims on late-August games that were
not part of any analysis. Last week of the project is packaging the
repo for public release.

Questions for you, whenever convenient: the venue question from the last
memo (grant report vs arXiv writeup) still gates how I frame the
introduction, and if you want to try the notebook and anything is
confusing, that feedback would directly improve the data release.
