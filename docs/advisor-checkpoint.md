# Advisor checkpoint — methodology questions (drafted 2026-07-21)

*Send with `docs/findings.md` attached. Status in one paragraph, then the
specific questions where a ruling changes what goes in the report.*

## Status

The proposal's Layer 1 is done and definitive: on 5,044 games priced by
Kalshi, Polymarket, and a de-vigged sportsbook consensus, all three are a
statistical dead heat (Brier ≈ 0.2185; every pairwise clustered DM n.s.;
TOST-equivalent within δ=0.001), with no favorite–longshot bias anywhere and
equal resolution. The horizon work shows the equivalence is *built during the
final day* (books hold a small real lead at T−24h, p=0.029, closed by start;
both exchanges sharpen in lockstep and are indistinguishable at every one of 7
horizons). Within-Kalshi distributional work (28,940 ladder contracts) found
one clean divergence: MLB small-margin under-pricing in Kalshi's thin ladders
that the books price correctly — and it is unexploitable net of fees, which we
frame institutionally: exchanges harbor biases inside their transaction-cost
band exactly as books harbor biases inside vig. Lead–lag on the live 15-min
panel finds no venue leads at that resolution; big repricings are simultaneous.
Remaining: report drafting and reproducibility packaging.

## Questions

1. **Multiple-testing policy.** We run Benjamini–Hochberg (q=0.05) over the
   paper's 13 *positive* claims (11 survive; the two fragile p≈0.05 results
   drop and re-enter at q=0.10), while nulls/equivalence claims are inventoried
   separately under TOST with pre-stated margins — on the logic that
   equivalences are not "discoveries." Is this two-family separation
   defensible, or would you put every test into one FDR family?

2. **Equivalence margin convention.** TOST margin is δ=0.001 Brier (~0.5% of
   the 0.2185 level; smaller than the fee wedge a trader would need). Is there
   a convention you'd prefer — e.g., a margin tied to the resolution component,
   or to an economically meaningful accuracy edge?

3. **Interval-randomized PIT.** Margin-distribution tests use PIT randomized
   within the discrete margin cells. Is that acceptable, or should we present a
   discrete/nonrandomized PIT variant alongside it?

4. **Cluster choice for DM tests.** All DM/regression inference clusters by
   date (same-day games share weather/news/lineup shocks). Games also nest in
   leagues; should we show two-way (date × league) as robustness, or is
   date-only standard here?

5. **Lead–lag methodology.** With a 15-min grid, irregular game windows, and a
   consensus (averaged) book line, we use game-clustered predictive regressions
   plus an event study around ≥2pt moves, rather than formal VAR/Hasbrouck
   information shares. Is that the right level of formality, or is an
   information-share decomposition worth the assumptions?

6. **3-way calibration (World Cup case study, n=9).** We report multiclass
   Brier descriptively. For ordered outcomes (home/draw/away), would you
   insist on RPS instead/alongside?

7. **Framing check.** The institutional synthesis we plan for the report:
   "sportsbook-like at the retail-taker surface (taker costs ≈ vig, no
   exploitable edge), forecasting instrument in aggregate (calibration equal to
   books, biases confined to cost bands)." Any objection to that as the
   organizing thesis?
