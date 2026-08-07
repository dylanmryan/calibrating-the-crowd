# Project update, week of Aug 4

- Added more sportsbooks to the comparison. The benchmark used to be an
  average of about 10 US books. I collected individual closing lines from
  30+ books, including Pinnacle (the sharp book) and DraftKings, FanDuel,
  and BetMGM. The result holds against every one of them individually:
  the prediction markets are statistically equivalent to each book, and
  no book shades its lines away from the sharp price by more than a
  fraction of a point.

- Finished the last analyses. The evidence phase is complete: 53
  automated analyses, all passing data-quality checks, plus four example
  games captured in full detail (Super Bowl, NBA Finals clincher, and
  two others) to use as illustrations in the report.

- New finding, and it changes the story. Kalshi's markets for sports with
  no real sportsbook coverage (table tennis, esports, minor league
  soccer) are still well calibrated, while championship futures are badly
  priced everywhere, including at the books (longshots return about $0.33
  per $1 at Kalshi and $0.34 at the books). So what keeps prices honest
  is repetition and fast resolution, not the benchmark and not the type
  of institution.

- Looked into the markets Kalshi Trading is involved in (the affiliate
  from the lawsuits and the More Perfect Union video). No public data
  identifies its specific markets, so I measured its observable
  footprint: covered games carry about $800K of standing liquidity per
  market, niche games about $6K, and most futures have no real book.
  Customers lose the same roughly 5 percent either way, so the affiliate's
  presence mainly determines whether a market exists at all, not whether
  users get worse prices.

Also: the odds API budget is fully spent and everything is banked and
backed up, so nothing depends on the subscription after it ends Sept 1.
The repo has a cleaned dataset, data dictionary, and starter notebook
(notebooks/data_tour.ipynb) if you want to explore the data yourself.

Three quick questions before I start writing:

1. Format: grant report, or written more like a paper we could put on
   arXiv later?
2. Is the central framing OK: "functions like a sportsbook for the retail
   bettor, works as a forecasting instrument in aggregate"?
3. Do you want to see the outline (about 3 pages) first, or should I just
   send a full draft?
