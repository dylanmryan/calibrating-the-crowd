# Roadmap — Remaining Work & Improvements
*Written 2026-07-10 (end of week 2 of 8; project ends ~Aug 24)*

## Where the project stands vs. the proposal

| Proposal commitment | Status |
|---|---|
| Layer 1: moneyline calibration, PM vs sportsbooks | ✅ **Done, definitive** — n=5,044 three-way dead heat; TOST-equivalent; clustered DM; de-vig-robust |
| De-vig methods (multiplicative / Shin / power) | ✅ Done, all three, conclusions invariant |
| Reliability diagrams, Brier + decomposition | ✅ Done (equal resolution; reliability differences tiny) |
| Favorite–longshot bias (logistic slopes) | ✅ Done — none anywhere; ladder longshots slightly *under*priced |
| Diebold–Mariano cross-source tests | ✅ Done + hardened (date-clustered SEs, equivalence testing) |
| Layer 3: alternate-spread probability curves | ◑ Done *within Kalshi* (28,940 contracts: 97.3% monotone, 0.1% arb, PIT; MLB rejects) — **cross-source curve comparison not built** |
| Layer 2: standard point spreads vs books | ❌ Not started (books' spread/alt lines never collected) |
| Time-horizon calibration (Page & Clemen) | ✅ Done for Kalshi (monotone sharpening 24h→start, constant-sample) — books/Poly horizons not done |
| Opening vs closing line movement | ◑ Partially covered by horizons; no true "opening line" analysis |
| Public reproducible GitHub repo | ◑ Repo exists but **private**; data + results gitignored; no repro packaging |
| Final research report | ❌ Not started (docs/findings.md is the seed) |

Beyond the proposal, the project also delivered: behavioral-fingerprint battery (all
null), realized-cost institutional analysis (taker ≈ book vig; maker ≈ free), the
side-assignment audit (a methods contribution in itself), trade-recon validation vs
OddPool archived books (99% within 1pt), and a live 3-source lead–lag collector +
World Cup 3-way (running on the VPS, verified alive 2026-07-10).

## Remaining work, by week

### Week 3 (Jul 13–20) — close the open measurement loops
1. **Polymarket spread measurement via OddPool** (~770 requests left this month):
   harvest token ids from gamma, sample archived Poly books → completes the
   3-venue taker-cost table (Kalshi ~4.2% ≈ books ~4.1% vs Poly ~1–1.75%?).
2. **Rerun decomposition + liquidity analyses on the clean dataset** — the memory'd
   numbers (reliability ordering, thin-market DM) predate the side-fix and are
   flagged superseded. Everything cited in the report must come from clean data.
3. **MLB run-line shape follow-up**: the +8.2pt under-pricing of 1–2-run margins is
   the paper's one crack. Do a cost-aware backtest (sell "win by 3+" at the bid,
   fees in) purely to establish whether the mispricing survives transaction costs —
   framed as "bias harbored inside the cost band, like books harbor biases inside
   vig," not as a trading strategy.
4. **World Cup wrap-up**: WC ends ~Jul 19. After the final, backfill outcomes
   (regulation-90 rule) and freeze wc_snapshots as a small 3-way calibration case.
5. **Decide on Layer 2 (book spread lines)**: get an Odds API credit estimate for
   historical `alternate_spreads` on a sample (dry-run cost first, confirm before
   spending). If affordable → cross-source margin curves (the proposal's most novel
   layer). If not → scope the report to "cross-source moneylines + within-Kalshi
   distributions" and say why.

### Weeks 4–5 (Jul 21–Aug 3) — the two remaining analyses
6. **Lead–lag price discovery** on the live 15-min series (by then ~4 weeks of
   MLB/WNBA + WC). Cross-correlation of price *changes* at 15-min lags,
   Granger tests, and an event-window look at big moves: who moves first,
   Kalshi, Polymarket, or the books? This is the "do markets import the books'
   information?" mechanism question the crowd-size null already hints at.
7. **Cross-source horizons**: extend the sharpening analysis — Polymarket
   `/prices-history` paths at the same 7 horizons for the joint set, so the
   Page–Clemen replication is comparative, not Kalshi-only.
8. **Advisor checkpoint** (send findings.md + specific questions): multiple-testing
   policy across the many DM/PIT tests, equivalence-margin convention (δ=0.001
   Brier), interval-randomized PIT validity, lead–lag methodology choice.

### Weeks 6–7 (Aug 4–17) — write the report
9. Draft the full report from docs/findings.md skeleton: intro/lit review
   (position against Page & Clemen 2013; Snowberg & Wolfers 2010; Clinton &
   Huang 2026 — our three-way design answers their cross-platform question with
   a books benchmark), data & pipeline (incl. the side-assignment audit as a
   methods lesson), results (headline equivalence → scorecard → nuances), the
   institutional synthesis ("sportsbook at the retail-taker surface, forecasting
   instrument in aggregate"), limitations.
10. Regenerate every figure/table from a single `make results`-style script on the
    clean master — no hand-carried numbers.

### Week 8 (Aug 18–24) — reproducibility + release
11. Public-repo prep: purge/rotate secrets, write README + data-availability note,
    pin the environment, decide what processed data can ship (Kalshi/Poly prices
    are re-derivable from free APIs; book lines may need "code + instructions"
    instead of raw data), archive the release (tag or Zenodo DOI for the report).
12. Retire/hand off the VPS collector; final rsync of live data.

## Standing chores (throughout)
- **Kalshi re-harvest cadence**: prices become unretrievable past the rolling
  ~60-day cutoff — run the historical harvesters every ~2 weeks so the season stays
  priced (last full run Jul 9; next ~Jul 21).
- rsync VPS `data/live/` weekly; verify cron after any reboot.
- Keep committing atomically (analysis / fix / finding per commit) and pushing.

## Improvement ideas (worth doing if time allows, in rough priority)
1. **CORP reliability diagrams** (isotonic, Dimitriadis–Gneiting–Jordan 2021) with
   consistency bands — strictly better than binned diagrams and reviewers like them.
2. **Log-score robustness** alongside Brier (tail-sensitive; cheap to add).
3. **Per-league equivalence table** (TOST by league) — turns "winners alternate in
   the 4th decimal" into a formal statement.
4. **CBB coverage** via ESPN `groups=50` — adds a big low-liquidity league for the
   thin-market story (Kalshi-vs-book only; no Poly CBB).
5. **Residual doubleheader cleanup** (24 flagged games; live-collector DH ambiguity)
   — small, but makes the audit section airtight.
6. **Season/format robustness**: re-check headline within playoffs vs regular
   season, and pre- vs post-Polymarket-fee era (2026-03-30 boundary).
7. **Sharpness comparison** (mean p(1−p) / resolution already ~equal — present it
   explicitly as "equally informative, not just equally calibrated").
8. **Kalshi academic data request** — free official granular history would firm up
   pre-cutoff trade-recon prices for the public release.

## Known risks
- **API budgets**: OddPool ~770 req/mo free; Odds API credits for any Layer-2
  backfill are paid — always dry-run cost + confirm before spending.
- **Kalshi 60-day price decay** — the standing re-harvest chore is load-bearing.
- **Lead–lag sample**: only MLB/WNBA in season; if 15-min granularity proves too
  coarse for clean lead–lag, fall back to event-window case studies around news.
