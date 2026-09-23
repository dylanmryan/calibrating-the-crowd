> Sports prediction markets are forecasting instruments. For most participants they cost what gambling costs.

@ Dylan Ryan · Northwestern University · September 2026

## 1. The question

I got interested in sports betting and the statistics underneath it, and separately in prediction markets. They are different things that happen to overlap on one small set of contracts: sports games.

A prediction market is an exchange where you buy and sell contracts that pay a dollar if something happens and nothing if it does not. The price is a probability. A contract trading at 60 cents is the market saying 60%.

The same game gets sold two completely different ways. A sportsbook takes your bet. A prediction market invites you to trade on sports, which is the language of skill. I wanted to know whether that difference is real or whether it is marketing.

I expected the prices to be correlated, since arbitrage should pull a sportsbook's odds toward the exchange's. That is not the interesting part. Sports is the right place to ask, because sports betting is recently legalized, heavily marketed, and unambiguously regulated as gambling, with the safeguards that come with that. Prediction markets list the same contracts without the same label.

So the question I spent a year on is whether trading sports on an exchange is a different activity from betting on sports, or the same activity with better vocabulary.

## 2. What I looked at

The same 5,333 games, priced three ways: a US-regulated exchange, an offshore crypto exchange, and the professional sportsbook complex, which here means Pinnacle plus eleven major US retail books. A second US-regulated exchange lists a smaller overlapping set of 2,639 of those games, and it ties as well.

Every price is a snapshot taken while the market was still open, not a closing line reconstructed afterward. That matters more than it sounds. A line rebuilt after the fact has already absorbed whatever everyone was about to find out, so it looks smarter than anything a person could actually have bet into.

Most of the work was making them comparable, and none of it was interesting. The sources name teams differently. They disagree about which calendar day a late game belongs to. And sportsbook odds are not probabilities at all until you take the house margin out, because a book quotes both sides so they sum to more than 100% and keeps the excess. Strip that out and you have something you can hold next to an exchange price. A data quality gate runs 73 checks before any analysis and halts the whole thing if one fails, rather than letting bad input produce plausible output.

## 3. What I found

A dead heat.

The standard way to score a forecaster is the Brier score, which is the average squared distance between what you predicted and what happened. Lower is better. The three came in at 0.2196, 0.2199 and 0.2196.

They are also calibrated, which is a different property and the one that matters more here. Calibrated means that when a venue says 62%, the thing happens about 62% of the time. All of them do this across the whole range, and they miss in the same places by the same amounts.

Now, "I could not find a difference" is a weak claim, and it is usually what you get when the sample is too small to see one. So I did it the other way around. Before running anything I wrote down how close two venues would have to be for me to call them the same, then tested whether they fell inside that band. Every pairwise comparison did. The tie holds against Pinnacle specifically, book by book across US retail, and across legally separated pools that no participant can trade between. That last one surprised me, because the arbitrage story I walked in with cannot explain a tie that survives where arbitrage is impossible.

Nobody leads, either. If one venue were doing the real pricing and the rest were copying, you would see it predict them at short horizons. It does not, at thirty, fifteen, ten or five minutes. They price in parallel.

None of this is because the bar is low. I built a deliberately dumb fourth forecaster, a rating system fed nothing but past wins and losses, and every venue beat it comfortably. The gap between the venues is about a thirtieth of the gap between any of them and the dumb model. They are close to each other because they are all good, not because none of them is trying.

I spent a lot of the year checking that I was not manufacturing the result. The audit gate caught 39 duplicate rows early on, so I fixed the collectors, reran everything, and nothing moved past the fourth decimal. Ten claims have been retracted or downgraded as the sample grew, and that record lives in the code instead of quietly disappearing. At the end I wrote my claims down, then pulled a batch of fresh games I had never looked at and checked them against it. The dead heat held.

[[F2]]

[[F4]]

## 4. What actually disciplines a market

The comparison tells you which venue is better. The more useful question is what makes any of them good, and the answer turns out not to be the institution.

These venues differ in nearly everything that gets written about them. One is regulated as a derivatives exchange and one as gambling. One matches you against other participants and one against the house. None of that showed up in the accuracy, so I went looking for what does.

The clean test is markets with no professional benchmark to copy. If an exchange is really just importing sportsbook prices, then contracts nobody else prices should be bad. I settled 962 contracts across 44 series that no major book covers: minor-league soccer, T20 cricket, esports, table tennis. They are calibrated. The miscalibration I measured sits below what a perfectly calibrated sample of that size would show from binning noise alone, and the three-way soccer fields carry exchange-grade margins in the Bolivian Primera Division. Having a benchmark changes how many prices form, not how good they are. Only about 17% of those niche contracts ever traded before the start. Where books exist almost everything gets priced; where they do not, less gets priced, and what does is fine.

Then the opposite test. Season-long bets, the ones placed in September and settled in June, are priced badly. A dollar on a deep longshot returned 33 cents at the exchange and 34 at the books, across twelve resolved seasons and twenty books including Pinnacle. Polymarket runs the same direction. This is not a thin-market problem, because the big championship fields carry real depth and fail anyway.

So the line is not between institutions. It is between kinds of market. Repetition and fast feedback produce good prices everywhere, including where there is nobody to copy. One-shot, long-horizon markets produce bad prices everywhere.

[[F6]]

Where the institutions do differ is price and access. Outright margins run about 1.03 to 1.06 at the exchange against 1.20 to 1.27 at the books, so both sell you the same badly priced product at very different markups. And an exchange will let you post a quote instead of taking one, which a bookmaker cannot do, because that is their side of the transaction. Across 709,126 fills the participants who took prices came out behind and the ones who posted them came out ahead. Those individual returns are noisy, but the wedge between the two roles is measured precisely and it is exactly the spread plus the fee.

[[F11]]

## 5. What this means if you run one

**Your own fee schedule already knows this.** Kalshi charges makers on covered game markets and lets them trade free on niche games and outrights. That is the same gradient I spent a year measuring, priced by the exchange itself: where flow is abundant, liquidity provision is inframarginal and can be taxed, and where it is scarce it has to be coaxed. If you want to know which of your markets are structurally healthy, read your own price list before you read your calibration report.

**Check what your split is conditioning on.** The one anomaly I thought had survived every correction was extra-inning baseball: because of the runner-on-second rule extra innings end within a single run about 70% of the time, and the contract paying on a narrow margin looked underpriced in that state by roughly 20 points — at the exchange and at the books alike. **I retracted it on 2026-09-23, and the way it died is more useful than the finding ever was.** Whether a game goes to extra innings is settled *during* the game. Splitting a calibration test on something the forecaster could not know breaks the arithmetic of calibration by itself, so the test returns the same answer no matter whose prices go in: a constant that always quotes the base rate scores +21.2 points on that split, against the market's +20.2. A constant cannot misprice the runner-on-second rule. Asked properly — is the error predictable from what the market knew before the first pitch? — the sign flips, to a small *over*-pricing in the games most likely to go long. So: no venue defect, no shared blind spot, and one methodological rule worth more than the anomaly. Before you believe a conditional calibration result, including your own, run it on a constant first. If the constant shows the same effect, the test has no power 