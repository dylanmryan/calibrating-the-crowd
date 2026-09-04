# Report-readiness audit — is every significant analysis in, and what remains
*Written 2026-08-28, before drafting begins. Method: enumerate the full space
of insights and comparisons a report on this question should contain, check
each against the repo (57-module suite, 2026-08-23 run; docs; figure program),
and plan whatever is missing. Verdict first, then the coverage matrix, then
the gap plan.*

---

> **Status, 2026-09-04.** This document is the record as written on 2026-08-28
> and is left unedited. **Every ANALYTICAL gap it identified has been closed:**
> Gap 1 (retraction reconciliation) in 6bbd3dc, Gap 2 (registered out-of-sample
> verification) in f915794/aec245a, Gap 3 (tables, figure program, exhibits) in
> 97b9c00, Gap 4 (playoff split, shared-deviation stat) in 97b9c00, Gap 5's
> number freeze in dc40fe6.
>
> **Gap 5's release checklist is the one thing still open**, and it is
> deliberately open because it is Dylan's call, not a task: the repo is
> untagged, has no DOI, and is still private. What HAS been done is the part
> that gates the decision — a secrets audit over the full git history
> (2026-09-04): no `.env`, `pem/`, `.key` or `config.yaml` was ever committed,
> and no literal API key or private-key block appears in the content of any
> commit on any branch. **The repository can be made public without a history
> rewrite.** Remaining, all one-liners once the call is made: `git tag`, a
> Zenodo DOI if wanted, and flipping visibility. Two further audits followed — `defensibility-audit-2026-09-03.md`
> (arbitrary choices, all 16 items closed) and `interpretation-audit-2026-09-03.md`
> (claim strength and unexamined rival explanations). References below to
> "out-of-sample verification planned ~Aug 22" describe the state on 2026-08-28;
> it was registered, run, and reported.

## Verdict

**Analytical coverage is essentially complete.** Of the ~45 distinct
insights/comparisons enumerated below, the suite already contains all but a
handful, usually at a depth beyond what a referee would demand (formal
equivalence with an economically anchored margin, MDE-disciplined nulls,
two-family FDR, four clock resolutions, a retraction record). The remaining
risk to the report is **not missing analysis breadth**. It is three things:

1. **Consistency.** The 2026-08-23 ladder-convention retraction rewrote the
   paper's §5C story, and four load-bearing documents still carry the
   retracted version — including the outline's "single source of truth"
   numbers table and the public README.
2. **Verification.** The one significant *promised* analysis that does not
   exist is the registered out-of-sample verification (outline open item 2,
   limitations §7 "out-of-sample verification planned ~Aug 22"). Data to run
   it now exists and is partly free.
3. **Assembly.** Several report artifacts are designed but not built
   (Table 4, the tables generally), and the new figure program is built but
   uncommitted and not reconciled with the drafting plan.

Nothing here contradicts a settled methodology decision (D1–D8 all stand).

---

## Coverage matrix

Status: ✅ done and current · ⚠ done but documentation stale · ❌ missing.

### A. Is the price accurate? (forecasting-instrument test)

| Insight / comparison | Status | Where |
|---|---|---|
| Plain calibration (priced X% → wins X%), all venues | ✅ | plain_calibration |
| Proper scores + Murphy decomposition + CORP + Murphy diagrams | ✅ | three_way, decomposition, corp_diagram, murphy |
| Formal equivalence (TOST), cost-anchored margin ladder | ✅ | rigor (fixed 339d19e) |
| Sharpness/resolution equality (not just calibration) | ✅ | league_tost |
| Favorite–longshot bias | ✅ | three_way, ladders, why_sports |
| Per-league splits + power (MDE) + hierarchical pooling | ✅ | league_tost, power, hierarchical_calibration |
| Robustness battery (log score, home-side, selection, de-vig, binning, staleness) | ✅ | referee, murphy |
| Temporal stability (quarterly) | ✅ | time_stability |
| **Playoffs vs regular season split** | ❌ | roadmap improvement #6, never built |
| **Registered out-of-sample verification on fresh games** | ❌ | promised (outline item 2, §7), no module exists |
| Distributional layer: margin PIT, RPS, book comparison | ⚠ | multi_outcome, book_pit, margin_dist — current in code/logs, stale in docs (see Gap 1) |
| Totals layer (third market layer, mechanism test) | ⚠ | totals — same staleness |
| Multi-outcome 3-way (World Cup) | ✅ | wc_freeze, multi_outcome (descriptive, appendix per D6) |
| Coherence: ladder monotonicity, arbitrage, cross-venue one price | ✅ | coherence, one_price |
| vs public-statistics floor (walk-forward Elo) | ✅ | model_benchmark |
| Information content: encompassing, late flow | ✅ | encompassing, late_flow (honestly downgraded) |

### B. Which institutions, compared how?

| Comparison | Status | Where |
|---|---|---|
| Kalshi vs Polymarket Global vs book consensus (three-way) | ✅ | three_way, rigor |
| vs Pinnacle specifically (sharp benchmark) | ✅ | sharp_books |
| Book-by-book, 11 US retail books | ✅ | us_books |
| Fourth leg: Polymarket US; law of one price across segregated pools | ✅ | four_way |
| Betfair; exchange-family price clustering | ✅ | sharp_books |
| Levitt shading, per book, two continents | ✅ | sharp_books, us_books |
| Everyone vs naive public-stats model | ✅ | model_benchmark |

### C. How do prices form?

| Insight | Status | Where |
|---|---|---|
| Horizon calibration T−24h → close; comparative sharpening | ✅ | horizon_equivalence, horizon_cross |
| Lead–lag at 30/15/10/5-min + 1-min; resolution ladder | ✅ | lead_lag, minute_lead_lag, five_min |
| Book-move and exchange-move event studies (both directions) | ✅ | book_moves, lead_lag |
| Close efficiency (day's move uninformative beyond close) | ✅ | close_efficiency |
| Maker-driven discovery (markouts, taker imbalance) | ✅ | informed |

### D. What does participation cost, and who is on the other side?

| Insight | Status | Where |
|---|---|---|
| Cost accounting: vig vs spread+fee, all venues, maker path | ✅ | profitability, cost table |
| Realized taker P&L to settlement | ✅ | retail_fingerprint |
| Retail fingerprint (timing, stake size, leisure concentration) | ✅ | retail_fingerprint |
| Fee natural experiment: accuracy + incidence | ✅ | fee_experiment, fee_liquidity |
| Tick design and the tail tax | ✅ | tick_pricing |
| Price of immediacy; depth; venue inversion into the event | ✅ | immediacy |
| Two-layer book / maker structure | ✅ | maker_structure |
| Affiliated dealer: documentary + MM-involvement test + functioning | ✅ | mm_involvement, market_functioning (scoped per D8) |
| Liquidity footprint across market classes | ✅ | liquidity_footprint |
| Horizon-matched translation (bankroll by cadence) | ✅ | horizon_translation |

### E. Where does the discipline stop? (mechanism)

| Insight | Status | Where |
|---|---|---|
| Outrights fail at every institution (K/P/books) | ✅ | futures_calibration, book_outrights |
| Un-benchmarked niche games are clean | ✅ | niche_gradient |
| BDW platform pathologies vanish in sports | ✅ | why_sports |
| Repetition-vs-benchmark-vs-liquidity decomposition | ✅ | niche_gradient + liquidity_footprint + market_functioning |
| **Table 4 (the 2×2 of discipline) as a rendered artifact** | ❌ | numbers exist; table does not (drafting-plan open item 4) |

### F. Rigor and deliverable infrastructure

| Item | Status | Where |
|---|---|---|
| FDR two-family policy; retraction record | ✅ | multiple_testing (17 claims, 15 keep) |
| Audit gates (73 checks + settlement-convention gate) | ✅ | data_audit, deep_audit |
| Figure program for the report | ⚠ | F1–F14 built in results/report/, **uncommitted**; drafting plan still references the old 9-of-29 selection |
| Locked-numbers table (single source of truth) | ⚠ | report-outline.md — **contains retracted numbers** |
| Number freeze | ❌ | deferred; blocked on final panel rsync + re-harvest |
| Public-release checklist (secrets, tag/DOI, repo visibility) | ❌ | README written for public; release steps not executed |
| Report prose | ❌ | the point of all this |

---

## The gaps, prioritized

### Gap 1 (blocking) — reconcile every document with the 2026-08-23 retraction

The ladder-convention fix (commit b7a2428) retracted the paper's former
centerpiece anomaly: MLB "win by 1–2" cell +8.4pt (z=+10) → −1.1pt (n.s.);
MLB margin PIT now **passes** (p=0.104); the totals-pass/margins-reject
contrast is gone (both pass); the pooled RPS edge shrinks to +0.49e-3
(z=+2.44) and is **carried by NBA**. What survives, better founded:
**extra-inning MLB games under-price the 1–2-run cell by +20.15pt on Kalshi
(z=+5.94) and +21.99pt at the books — the same miss at both institutions**,
a baseball-wide blind spot in a rare state (8.6% of games), cancelled in
aggregate by regulation running the other way (−3.07pt).

Documents still asserting the retracted version:

| Document | Stale content |
|---|---|
| `docs/report-outline.md` | §5.5 whole subsection; locked table rows "RPS MLB z=+5.4", "MLB cell K +8.5pt vs B +0.4pt (z=+10)", "Totals vs margins PIT pass/reject"; §1 contribution 3; thesis paragraph's implicit reliance |
| `docs/drafting-plan.md` | §5C ¶2–¶8 (the pivotal movement is built on the retracted contrast); Fig 5/6 assignments (`margin_pit.png` as "the crack" — it now shows a pass); §4 ¶3 still glosses δ as "≈0.5pt/game" (contradicts D2's 3.16pt correction); Movement C summary in §0 |
| `docs/findings.md` | Nuance 1 (the full old MLB story, including "Kalshi does not mismodel baseball; it mismodels the rule that stops the game") |
| `README.md` | "One genuine anomaly" paragraph states the retracted totals-vs-margins diagnosis (committed Aug 20, three days before the retraction) |
| `docs/advisor-email-2026-08-14.md` | Third bullet states the retracted finding. Marked "not sent" — **do not send as-is** |

**The re-architected §5C** (spec for the drafting-plan rewrite; verify every
number against the 2026-08-23 logs when editing, hand-carry nothing):

1. Transition unchanged (binary price → full distribution → market type).
2. Distributional surface is *mostly* clean too: every league's margin PIT
   passes (pooled p=0.718, MLB p=0.104); books' localized RPS edge is now
   small and an **NBA** story (+1.14e-3, z=+2.27; MLB n.s.; NHL tie).
3. The one crack that survives is **shared**: the extras 1–2-run cell,
   missed by ~+20pt at *both* institutions. This is a within-game microcosm
   of the paper's boundary thesis — a rare, slow-feedback state goes
   mispriced *everywhere*, exactly like one-shot outrights — and it joins
   the WC draws and the 40/60 compression in the shared-blind-spot motif.
   The retraction strengthened the thesis: the last "Kalshi-specific defect"
   became another institution-independent failure of repetition.
4. Totals layer re-purposed: no longer the walk-off diagnosis, now evidence
   that the same scoring process is priced correctly in its dense, repeated
   dimension (11-rung totals, ECE 0.0046) — plus the WNBA open observation
   (one sentence, per drafting-plan open item 5).
5. Methods lesson upgraded: the ladder-convention catch is the project's
   **third** independent pipeline catch (side-assignment, stale prints,
   settlement conventions), each found by the same discipline — impossible
   results treated as pipeline alarms, settlement data as ground truth,
   then a permanent audit gate. §3's "two independent catches" line and
   Appendix A's scope need the update. This is a genuine contribution;
   drafting should present it as one.
6. Boundary material (outrights, niche, Table 4) unchanged.
7. Figure decision for §5C: `margin_pit.png`/`totals.png` no longer carry a
   contrast; move to appendix gallery. The extras cell is a prose+table
   point (or one small panel if wanted); F6 (discipline boundary) carries
   the movement's figure load.

Also sweep for the D2 scale correction ("≈0.5pt" gloss) everywhere it
survives, and re-verify §1/§2/§6 forward references after the rewrite.

### Gap 2 (the missing significant analysis) — registered out-of-sample verification

The outline promises it; the limitations section leans on it ("informal
pre-registration (freeze + out-of-sample verification planned ~Aug 22)");
no module exists. This is the single highest-value addition available: it
converts "we froze our claims" from an assertion into a result, and it is
the standard referee response to a paper with this many tests.

Design (new module `oos_verification.py` + registration doc):

1. **Register first.** Write `docs/registered-claims.md` *before* touching
   new data: the holdout-testable claims with predicted direction/magnitude
   — three-way dead heat (|ΔBrier| within the pre-stated margin), slopes ≈1,
   no FLB, no venue leads on new panel steps, extras-cell sign (+, both
   venues), structural taker cost ≈ −4.5%. Date it, commit it, then collect.
2. **Holdout data, no new spend.** The VPS panel has been collecting all
   three venues at 5-min cadence since the local mirror was last synced
   (2026-08-10) — roughly +300 games by now at ~18/day. Final rsync gives a
   post-registration three-way sample with **synchronized T−0 book quotes**,
   which simultaneously retires the report's consensus-timing caveat on the
   holdout (a two-birds design: fresh games *and* a same-clock robustness
   check). Kalshi/Polymarket full-universe refresh for the wider
   exchange-only holdout is free API work; the 60-day Kalshi window
   comfortably covers August.
3. **Evaluate against the registered list only.** Report each with its MDE
   per the house reading rule — at n≈300 the equivalence test will be
   underpowered for the formal margin, and the report should say exactly
   that: the holdout is a consistency check on direction and magnitude, not
   a re-derivation. The exchange-only holdout (larger n) carries more power.
4. Optional cell, user's call: WNBA totals tilt on fresh games — the open
   observation made a real-time prediction (market slow to re-price a rising
   scoring environment); the holdout can score it. Drafting-plan open item 5
   said "no further analysis," so include only if wanted; it would be the
   cleanest possible handling of an open observation.
5. **Book-leg top-up is optional and gated.** The panel supplies the book
   quotes for panel games at no credit cost. A historical closing-bucket
   top-up for non-panel August games would widen the three-way holdout but
   costs Odds API credits against the 11.8K live-feed reserve — if desired,
   dry-run the credit cost first and confirm before spending (standing
   rule). Default: don't.
6. Reruns that ride along free: the five_min event study roughly doubles
   past its n=19; the fine-clock panel and immediacy analyses refresh.

Outcome either way is reportable: confirmation becomes §5A's closing
paragraph and an abstract sentence (drafting-plan open item 3 already
reserves the slot); a deviation becomes an honest result in a paper that has
already retracted four claims in public.

### Gap 3 — report artifacts that are designed but not built

1. **Table 4, the 2×2 of discipline** — the paper's centerpiece table.
   Numbers all exist (niche_gradient, futures_calibration, book_outrights,
   liquidity_footprint). Build it as a small module (or a `tables.py`
   emitting Markdown/LaTeX for Tables 1–5 from logs) so freeze re-stamps it
   like everything else — consistent with the no-hand-carried-numbers rule.
2. **Tables 1, 2, 3, 5** — same treatment: data-sources table, MDE table
   with the reading rule, headline equivalence table, cost accounting table.
3. **Figure-program reconciliation and commit.** `report_visuals.py`,
   `report_visuals_alt.py`, `docs/figure-map.md`, and `results/report/`
   (F1–F14 + alternatives) are all untracked. Commit them; then update the
   drafting plan's per-section figure references from the old
   `results/*.png` selection to the F-numbers, and make the five
   pick-one-of-each-pair choices (F1 vs stat tiles, F2 vs deviation, F3 vs
   simple forest, F6 vs price curves, F7 vs two rates) so drafting has one
   authoritative figure list. The F6 Shin footnote (books' sub-10c return
   $0.34→$0.52 under Shin) must appear in §5C prose, not just the figure —
   the equal-failure claim is multiplicative-de-vig-only and the text has to
   own that.
4. **Case-study exhibits: use or cut, explicitly.** Four games sit in
   `data/exhibits/` in full cross-venue detail (27–32 books × 7 horizons,
   134K fills) and nothing in the analysis or figure program touches them.
   §1 ¶1 wants exactly this ("one game, four prices, within a point") — a
   half-day option is a small §1 exhibit (one game's four price paths into
   the close, e.g. Super Bowl LX). If cut, add them to figure-map's
   "deliberately not illustrated" list so the decision is recorded.

### Gap 4 — cheap, referee-anticipating robustness (secondary)

1. **Playoffs vs regular season.** The one roadmap robustness idea never
   built. One referee.py addition: headline Briers + pairwise DM/TOST split
   by season segment. Quarterly stability nearly covers it; this closes it.
2. **Shared-deviation statistic (optional).** F2alt shows the venues'
   calibration deviations are shared at 10× magnification; one number
   (e.g., cross-venue R² of binned deviations, or per-game error
   correlation) would let prose cite the motif that now also carries the
   extras cell and the WC draws. Small addition to plain_calibration.
3. **data_tour.ipynb re-execution** post-retraction (text greps clean;
   re-run to confirm outputs, since it's the public on-ramp).

### Gap 5 — freeze and release (mechanical, sequenced last)

1. Final VPS rsync + collector retirement (mirror stale since Aug 10).
2. One last Kalshi re-harvest before the 60-day window advances.
3. **Number freeze**: full suite + report_visuals on final data; regenerate
   the outline's locked table *from logs* (it currently mixes three vintages
   and two retracted rows); stamp figures/tables.
4. Release checklist: secrets audit incl. git history scan (`.env`, `pem/`
   are ignored — verify nothing leaked historically), pin requirements,
   repo-public decision + tag or Zenodo DOI, README status line update.

---

## Considered and deliberately not added

So the audit is visibly exhaustive rather than selective — each of these was
weighed and rejected, most with reasoning already on record:

- **Hasbrouck information shares / VECM** — rejected with reasons (D5).
- **Two-way clustering** — rejected, 7 league clusters (D4).
- **CBB expansion** — scoped out (ESPN gap, no Poly leg); limitation.
- **Book totals benchmark** — budget spent; documented limitation.
- **Demographic identification** — impossible from public tape; limitation ¶1.
- **In-play/live pricing** — out of scope by design (pre-start prices); make
  sure §7 says so in one clause.
- **More conditional-calibration cuts** (rest days, weather, travel) — the
  Elo floor already bounds public-information content; diminishing returns.
- **Divergence-conditional accuracy** ("when venues disagree, who's right?")
  — already answered twice: encompassing (neither adds beyond the other) and
  the divergence-chasing backtest (loses 38%).
- **Further WNBA totals analysis** — held to one sentence per open item 5,
  unless the OOS cell above is wanted.
- **Kalshi academic data request** — moot at this stage of the project.

---

## Execution plan

Order matters: registration before data, reconciliation before prose,
freeze last. Rough effort in parentheses.

**Phase 1 — Truth reconciliation (blocks everything; ~half day)**
1. Regenerate the locked-numbers table in `report-outline.md` from the
   2026-08-23 logs; rewrite outline §5.5 + contribution 3 to the
   post-retraction story (Gap 1 spec).
2. Rewrite drafting-plan §5C beats + §0 Movement C summary + §4 ¶3 δ gloss +
   figure assignments; update findings.md nuance 1; fix the README anomaly
   paragraph; annotate the advisor-email draft as superseded.
3. Commit the figure program (report_visuals*.py, figure-map.md,
   results/report/).

**Phase 2 — Registration + holdout (the significant addition; ~1 day)**
4. Write and commit `docs/registered-claims.md` (before any new data).
5. Final VPS rsync; Kalshi + Polymarket refresh (free). No Odds API spend
   without a dry-run estimate and explicit approval.
6. Build `oos_verification.py` (+ suite entry): registered-claims scorecard
   on the holdout, MDEs quoted, synchronized-clock robustness noted;
   five_min/immediacy refresh rides along.

**Phase 3 — Artifacts (~half day)**
7. `tables.py` (or equivalent): Tables 1–5 from logs, Table 4 first.
8. Exhibit decision: build the §1 opener panel from `data/exhibits/`, or
   record the cut in figure-map.
9. Playoff/regular-season split in referee.py; optional shared-deviation
   stat; re-execute data_tour.ipynb.

**Phase 4 — Freeze, then draft (~half day + the writing)**
10. Collector retirement + final suite run + freeze stamp; regenerate
    MANIFEST and locked table; verify 0 failures.
11. Release checklist (secrets/history audit, pins, tag/DOI, visibility) —
    repo-public moment is the user's call.
12. Draft per the (revised) drafting plan, §5C first.

**Decisions reserved for Dylan** (flagged, not assumed): optional Odds API
top-up for the non-panel holdout (default no); WNBA OOS cell in or out;
exhibits used or cut; the five figure-pair picks; repo-public timing.
