# Project update, week of Aug 4

What got done this week:

- Finished the last analyses. The data collection and evidence phase of the
  project is now complete (53 automated analyses, all passing checks).
- Main new finding: I separated what actually keeps these markets accurate.
  Markets with no sportsbook benchmark (table tennis, esports, minor league
  soccer on Kalshi) are still well calibrated, while championship futures
  are badly priced everywhere, including at the books themselves (longshots
  return about $0.33 per $1 at both Kalshi and the books). So repetition
  and fast resolution are what discipline prices, not the institution.
- Hardened the headline result: the exchanges are statistically equivalent
  to Pinnacle (the sharp book) and to DraftKings, FanDuel, and 9 other US
  books individually, not just to an average.
- Looked into the "users are betting against the house" claim from the
  lawsuits and the More Perfect Union video: no public data says which
  markets Kalshi's affiliate trades in, but customers do no better where
  the professional market makers are absent, there is mostly just no
  market there at all.
- Spent the rest of the data budget banking everything we need before the
  odds API expires Sept 1 (day-ahead lines, per-book records, futures back
  to 2020, four fully detailed example games for the report). Everything
  is backed up and reproducible without the subscription.
- For hands-on access: the repo now has a cleaned one-row-per-game dataset
  (analysis_core.csv), a data dictionary, and a starter notebook
  (notebooks/data_tour.ipynb) that reproduces the main table.
- Report outline is done, with every number tied to a generated log file.
  Prose starts now.

Three quick questions before I commit to the write-up:

1. Format: grant report, or written more like a paper we could put on
   arXiv later?
2. Is the central framing OK with you: "functions like a sportsbook for
   the retail bettor, works as a forecasting instrument in aggregate"?
3. Do you want to see the outline (about 3 pages) before I write, or
   should I just send you a full draft?
