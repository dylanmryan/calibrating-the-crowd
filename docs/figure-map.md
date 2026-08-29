# Figure program — mapping to the report's argument

Nine figures, built by `src/analysis/report_visuals.py`, output to
`results/report/` as PNG (220 dpi) and PDF (vector, for the document).
Every statistic is quoted from the 2026-08-23 suite logs with provenance
declared in the module; only F2's reliability curve is recomputed, and it
is checked against `plain_calibration.log`.

| Fig | Section it serves | The one thing it establishes |
|---|---|---|
| F0 | §1 opener | One game, every venue: 28 books, the Polymarket path, and the Kalshi tape land 0.5pt apart (built 2026-08-28 from data/exhibits) |
| F1 | S4 — the orthogonality claim | Price quality and participant cost are two independent axes |
| F2 | S6 — the dead heat | Priced probability tracks realized frequency, identically, at three institutions |
| F3 | S6 — formal equivalence | The venues are equivalent inside the band where a difference could reach anyone — and where they stop resolving |
| F4 | S6 — price formation | No venue leads another at 30, 15, 10 or 5 minutes |
| F5 | S5 — the industry's strongest claim, tested | The markets do aggregate information a public-statistics floor does not contain — and they aggregate the same information |
| F6 | S6→S7 — the discipline boundary | What fails is the kind of market, not the kind of institution |
| F7 | S7 — the bridge | Per-position cost × turnover: calibration disciplines the price, not the participant |
| F8 | S4 — the participant criterion | The flow is shaped like consumption, not like hedging |
| F9 | S1/S3 — institutional distinction | Institutional design leaves a visible fingerprint on prices even where accuracy is identical |
| F10 | S6 — how the equivalence forms | The dead heat is built during the final day, not assumed at the close |
| F11 | S1/S5 — what an exchange offers | There is a side of the market a bookmaker cannot let you take |
| F12 | S5 — the peer-to-peer claim | Two-sided size at this scale is professional market-making, not peer supply |
| F13 | S4 — the operational criteria | Six criteria say forecasting instrument; the seventh is the one a participant feels |
| F14 | S1/S7 — the cost mechanism | For this clientele depth never binds; the spread and the fee are the whole story |

## Alternatives (picked 2026-08-28: the primary of every pair is in; all
five alternates go to the appendix gallery. Reasoning per pair below —
the trade-off column decided each one in the primary's favor for a
first-time reader who must be able to trust the honesty of the display.)

| Alternative | Replaces | Trade-off |
|---|---|---|
| F1alt stat tiles | F1 two panels | Faster to read, better as a section opener; loses the visual proof that the venues coincide |
| F2alt deviation | F2 reliability curve | Shows that every deviation is shared, at 10x magnification; loses the intuitive 45-degree line |
| F3alt simple forest | F3 anchor ladder | Cleaner for a first-time reader; drops the honest report of where equivalence stops resolving |
| F6alt price curves | F6 three rows | Shows the whole price range; noisier, and the sparse futures buckets invite over-reading |
| F7alt two rates | F7 single rate | Brackets the result by both measured cost rates; busier, and needs the CI caveat read |

## Design decisions

- Categorical palette is the validated three-slot set (blue #2a78d6 Kalshi,
  orange #eb6834 Polymarket, aqua #1baf7a sportsbook). It clears the
  all-pairs CVD and normal-vision floors in light mode. Aqua sits below 3:1
  on the light surface, so every series carries a direct label rather than
  relying on colour alone.
- Colour follows the entity everywhere: Kalshi is blue in all nine figures.
- The Elo benchmark (F5) is deliberately muted grey, not a fourth
  categorical hue — it is a floor, not a peer.
- Red is reserved for a status meaning throughout: a claim that does not
  resolve (F3), a counterfactual (F4), a threshold (F7, F8).
- No dual axes anywhere; F1 and F6 use two panels rather than two scales.

## Deliberately not illustrated

- **The retractions.** Eight claims retracted or downgraded, four on
  2026-08-23. This belongs in prose in Methods or Limitations; a figure
  would dramatise it.
- **The MDE table.** CFB, WNBA and NFL cannot detect the effect at issue.
  It is a table, not a chart — every null needs its MDE in the same
  sentence, which a figure cannot enforce.
- **The World Cup 3-way case study.** D6 fixed it as descriptive at n=9;
  any chart would invite inferential reading.
- **The affiliated-dealer material.** D8 reduced it to a paragraph plus an
  appendix; a figure would re-inflate a scope cut already taken.
- **The WNBA totals rejection.** Resolved 2026-08-29 as a false alarm
  (dissolved at n=290; sign-flipped on the registered holdout). Nothing to
  illustrate — a fortiori.

## Caveats carried in the figures themselves

- F6 states in its own footnote that the books' sub-10c return rises from
  \$0.34 to \$0.52 under Shin de-vig. This matters: `murphy.py` established
  that tail-sensitive claims must use Shin, and the sub-10c longshot return
  is a tail-sensitive claim. Under the project's own rule, "Kalshi \$0.33
  and the books \$0.34, statistically identical" holds under multiplicative
  de-vig only. The 3-12 month bucket is unaffected (\$0.39 vs \$0.38).
- F3 shows where the equivalence fails (the two Polymarket pairs at the
  mid-price anchor) rather than reporting only the pre-stated margin.
- F7 labels the cadence grid as a scenario, not a measurement.
