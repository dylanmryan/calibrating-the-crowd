# Sports prediction markets are forecasting instruments. For most participants they cost what gambling costs.

*Dylan Ryan · Northwestern University · September 2026*

---

## 1. The question

I got interested in sports betting and the statistics underneath it, and separately in prediction markets. They are different things that overlap on one small set of contracts: sports games. The same event gets sold two completely different ways. A sportsbook takes your bet. A prediction market invites you to trade on sports, which is the language of skill.

I expected the prices to be correlated, since arbitrage should pull a sportsbook's odds toward the exchange's. That is not the interesting part. Sports is the right place to ask the real question, because sports betting is recently legalized, heavily marketed, and unambiguously regulated as gambling, with the safeguards that come with that. Prediction markets list the same contracts without the same label.

So the question I spent a year on is whether trading sports on an exchange is a different activity from betting on sports, or the same activity with better vocabulary. I wanted to know if the data could settle it.

## 2. What I looked at

The same 5,333 games, priced through four institutionally different mechanisms: a CFTC-regulated exchange, an offshore crypto order book, a second US-regulated exchange, and the professional sportsbook complex, including Pinnacle and eleven major US retail books.

Every price is anchored to the moment the game started, and nothing after it is ever used. That anchoring is the part that matters, and it is worth being precise about how each price is built, because they are not built the same way. A collector has run continuously since summer pulling all four venues on a fixed schedule, and where that panel covers a game the quote is a live snapshot. For the historical sample it is different: the sportsbook leg is an archived pre-game snapshot, and about 80% of the exchange leg is reconstructed from the trade tape, because the exchange keeps no order book older than sixty days. So I checked the reconstruction against a third party's archived order books rather than assume it: it recovers the real quote exactly in 95% of cases and lands within one cent in 99%. And the headline result is the same on games priced either way.

Most of the work was making them comparable. They name teams differently, disagree about what day a late game belongs to, and quote probabilities that are not comparable at all until the house margin is stripped out. A data quality gate runs 73 checks before any analysis and halts the suite on failure rather than producing plausible output from bad input.

## 3. What I found

A dead heat. Brier scores of 0.2196, 0.2199 and 0.2196. When these venues say 62%, it happens about 62% of the time, and they are wrong in the same places by the same amounts.

This is not "we failed to find a difference." I set the margin for what counts as the same before running anything and tested for equivalence directly, and every pairwise interval landed inside it. The tie holds against Pinnacle specifically, book by book across US retail, and across legally segregated pools that no participant can arbitrage between. That last one surprised me: the arbitrage explanation I walked in with cannot be the reason, because the tie survives where arbitrage is impossible.

Nobody leads, either. No venue predicts another at thirty, fifteen, ten or five minute resolution, so nothing is flowing from one venue to the rest on any clock I can measure. I want to be careful about what that does and does not prove. A market maker quoting the exchange continuously off the sportsbook's line would also produce no lead, because there would be no lag to find — and in fact almost all of an exchange price is explained by the book, which is what you would expect either from copying or from two accurate forecasters watching the same games. The measurement cannot separate those. What can: the exchanges price obscure markets with no professional line to copy just as well as the ones that have one. They do not need the book. Whether they lean on it where it exists is a question this data cannot answer, and I would rather say that than pretend otherwise.

None of this is because the bar is low. I built a deliberately naive fourth forecaster, a walk-forward Elo model off nothing but past wins and losses, and every venue beat it decisively. The three institutions sit about 28 times closer to each other than any of them sits to the model. They are equally good, and equally better than public statistics.

I checked hard that I was not manufacturing the tie. The audit gate caught 39 duplicate rows early on, I fixed the collectors and reran, and nothing moved past the fourth decimal. Ten claims have been retracted or downgraded as the sample grew, and that record is kept in the code rather than quietly dropped. Then I committed my claims in writing and pulled a fresh holdout I had never looked at. The dead heat replicated at full registered power.

> **[F2: dead heat, reliability curve]**
> *Caption: Priced probability tracks realized frequency, identically, at three institutions.*

> **[F4: no leader]**
> *Caption: No venue predicts another at thirty, fifteen, ten or five minutes. If one follows another, it does so within the same step.*

## 4. Why accuracy is not profit

I built a scorecard for the original question and ran every facet gambling would predict. Biased prices: none, all four are calibrated across the full range. Favorite-longshot bias: none, every slope interval includes one. No information content: false, resolution matches the professional books. Incoherent ladders: 97.3% are perfectly monotone, and executable arbitrage exists in 0.10% of them. Beatable: no strategy I tried clears costs, and chasing cross-venue divergence loses 38%.

Six facets say forecasting instrument. The seventh is the one a participant actually feels, and it is cost.

Here is where the marketing and the mechanism separate, and not the way I expected. At the quote, the exchanges look far cheaper: about 1.0% against the books' 4.2% overround. But quoted spread is not what a retail customer pays. Once you add the taker fee, all-in cost for a market order on the regulated US exchange is about 4.2%, which is the sportsbook number. The offshore venue is genuinely cheaper at 1.25 to 1.75%. Structural taker cost across the sample is −4.6% per position, and the ordinary participant's realized return on the regulated exchange runs −3 to −4.5%, which is transaction costs and nothing else. An efficient market, not a beatable casino, and not a rigged one either.

Cost compounds. One position a week across a season leaves a weekly participant with roughly 30% of the bankroll, before anyone has been right or wrong about a single game.

> **[F7: cost times turnover]**
> *Caption: Calibration disciplines the price. It does not protect the participant.*

There is one real structural difference, and it is not the one the marketing sells. On an exchange you can post a quote instead of taking one, and makers trade close to free. Across 709,126 fills the takers came out around 5% behind and the makers ahead, and while those individual returns are too noisy to lean on, the wedge between the two roles is measured precisely and it is exactly the spread plus the fee. A bookmaker cannot offer you that side, because it is their side. So the honest distinction is not that trading sports is more skillful than betting on sports. It is that an exchange will let you be the house, and almost nobody takes it up.

## 5. What this means if you run a market

**The discipline boundary is not the institution.** One-shot, long-horizon outrights are badly priced everywhere: about 33 cents back per dollar on deep longshots at the exchange, 34 at the books. Meanwhile obscure game markets with no professional benchmark at all are clean. What produces calibration is repetition and fast resolution, not regulation, liquidity, or having a professional to copy.

**Check what your split is conditioning on.** The one anomaly I thought had survived every correction was extra-inning baseball: because of the runner-on-second rule extra innings end within a single run about 70% of the time, and the contract paying on a narrow margin looked underpriced in that state by roughly 20 points — at the exchange and at the books alike. **I retracted it on 2026-09-23, and the way it died is more useful than the finding ever was.** Whether a game goes to extra innings is settled *during* the game. Splitting a calibration test on something the forecaster could not know breaks the arithmetic of calibration by itself, so the test returns the same answer no matter whose prices go in: a constant that always quotes the base rate scores +21.2 points on that split, against the market's +20.2. A constant cannot misprice the runner-on-second rule. Asked properly — is the error predictable from what the market knew before the first pitch? — the sign flips, to a small *over*-pricing in the games most likely to go long. So: no venue defect, no shared blind spot, and one methodological rule worth more than the anomaly. Before you believe a conditional calibration result, including your own, run it on a constant first. If the constant shows the same effect, the test has no power and the number means nothing.

**Cost is the competitive variable, and it is the one you set.** Everyone here is accurate and nobody is meaningfully more accurate, so accuracy is not a differentiator. If a market-order customer pays the same all-in as they would at a sportsbook, the distinction the product is marketed on is not one the data can see. What is real is the maker side, and it is the part hardest to explain and least advertised. If you want the forecasting-instrument framing to mean something to the person using it, that is the thing to build toward.

---

*Code, data pipeline, and the full analysis: [repo link]. Advised by Prof. Arend Kuyper; supported by a Northwestern BPF Undergraduate Research Grant.*

<!-- ==================================================================
PRODUCTION NOTES — DELETE EVERYTHING BELOW BEFORE POSTING
===================================================================

WHAT CHANGED AFTER READING THE ACTUAL REPO, AND WHY

1. THE +8.4pt KALSHI RUN-LINE MISPRICING IS GONE.
   You retracted it on 2026-08-23 when the league-specific settlement
   convention surfaced in the ladder data. My earlier draft had it as the
   centrepiece of section 4. Replaced with what actually survived: the
   extra-innings blind spot, ~20pts, SHARED by Kalshi and the books equally,
   replicated on the registered holdout at +19.6pt vs +20.2pt frozen.
   This is a much better story for your thesis anyway, because a shared blind
   spot supports "the boundary is the market type, not the institution."
   [SUPERSEDED 2026-09-23: the replacement was itself retracted. The extras
   split conditions on a state realized during the game, and a constant
   forecaster scores +21.19pt on it. The holdout "replication" (R6) is
   withdrawn as a test that could not fail. There is no shared blind spot; the
   boundary argument rests on outrights and niche games. See the retraction
   block in docs/findings.md.]

2. THE COST STORY WAS BACKWARDS AND I HAD BUILT A CHART OF IT.
   The CV tab line "~1% exchanges vs ~4.2% sportsbooks" is the QUOTED
   overround. All-in for a market-order taker it is: Polymarket 1.25-1.75%,
   Kalshi ~4.2%, books ~4.2%. The regulated US exchange costs a taker the
   same as a sportsbook. My chart3_cost.png claimed a 77% vs 33% split and is
   WRONG. Do not use it. Deleted from the draft; use F7 instead.
   This correction makes your argument stronger, not weaker.

3. FOUR VENUES, NOT THREE. Kalshi, Polymarket Global, Polymarket US, and the
   book complex. The three-way clean set is what the Brier table is on.

4. THE ARBITRAGE POINT IN SECTION 1 NOW PAYS OFF. You expected correlation
   from arbitrage; the data shows the tie holds across legally segregated
   pools nobody can arbitrage, and that no venue leads at any horizon. That
   is a genuinely interesting result and section 3 now says so.

FIGURES — ALL ALREADY BUILT, results/report/ at 220dpi PNG + vector PDF
   F2_dead_heat            -> section 3
   F4_no_leader            -> section 3
   F7_translation          -> section 4
   F6_discipline_boundary  -> optional, section 5 opener
   F13_scorecard           -> strong alternative opener for section 4
   Do not rebuild anything. Your figure program already uses the same
   palette I would have picked (Kalshi blue #2a78d6, Polymarket orange
   #eb6834, sportsbook aqua #1baf7a) and already carries the honest caveats.

LENGTH
Runs ~1,240 words against Liz's ~770. Sections 3 and 4 carry the overage and
both earned it. If you need to cut, the Elo paragraph in section 3 and the
scorecard list in section 4 compress fastest without losing an argument.

NUMBERS TO RECONCILE BEFORE POSTING
- Game count: README says 5,333 priced by all sources; findings.md says
  "final data configuration: three-way clean n=5,328". I used 5,333. Pick one
  and make README, findings.md, the write-up and your LinkedIn bullets agree.
- Section 5 longshot line: "$0.33 vs $0.34" holds under MULTIPLICATIVE de-vig
  only. Under Shin the books rise to $0.52, and your own murphy.py rule says
  tail-sensitive claims must use Shin. F6 carries this caveat in its footnote.
  Either add the caveat in text or soften to "both are poor" without the
  near-identical numbers. Do not post the tight version unqualified.

SEPARATELY — REFLECTION QUESTION 4 NEEDS FIXING
I told you earlier to answer "I cluster on game." That is wrong for the
headline tests. The repo uses DATE-clustered Diebold-Mariano and date-clustered
logit for the encompassing and four-way comparisons. Game clustering appears in
the return analyses where one game contributes multiple sides; futures
calibration clusters by event; outrights cluster by sport-season. The correct
answer is that the clustering unit follows what repeats: date for the headline
forecast comparisons, because games on the same slate share news and weather.
Rewrite that answer before you send it to Liz.

ADDED ON REVIEW (second pass over the repo)
- Title now matches the question section 1 asks.
- F5 added to section 3. Without it the piece reads as "everyone is the same,"
  and omits that all four beat a naive Elo floor decisively. Leaving that out
  made the work look like a null result when it is not.
- The maker/taker asymmetry added to the end of section 4. This was the
  biggest gap: it is the one genuine structural difference between an
  exchange and a bookmaker, it directly answers the question in section 1,
  and F11 already illustrates it. Consider adding F11 next to that paragraph.
- Section 5 now closes on the maker side rather than trailing off on
  operator advice.

STILL OUTSTANDING
- Liz wants you to read the Palantir written application questions before
  drafting further. Paste them and I will map them to these sections.
- Courtesy heads-up to Kuyper that you are posting.
-->
