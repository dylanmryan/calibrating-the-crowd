# Advisor meeting prep — 2026-07-26

*Send `docs/findings.md` + `docs/advisor-checkpoint.md` ahead tonight so the
meeting spends time on decisions, not recap.*

## 0. The elevator answer (say this first)

"The proposal asked whether sports prediction markets are calibrated the way
sportsbooks are. The answer is stronger than yes: a regulated exchange, an
offshore crypto market, and the Vegas consensus produce *formally equivalent*
forecasts — TOST-equivalent within δ=0.001 Brier, pooled and within every
big league, under every proper scoring function, at every horizon in the
final day. All three beat a public-statistics Elo floor by ~14×10⁻³ Brier
(z≈7), i.e. they're equally good and equally better than public information.
And the platform pathologies documented on the rest of Kalshi — favorite–
longshot bias, −20% returns — vanish in sports, the one asset class with a
professional benchmark and rapid repeated resolution. Measurement is done;
I'm two weeks ahead of the roadmap and starting the report."

## 1. Show, in this order (have results/ open)

| # | Figure | The sentence it carries |
|---|---|---|
| 1 | `corp_reliability.png` | All three sources inside perfect-calibration bands (bin-free). |
| 2 | `murphy.png` | No proper scoring function separates them (sup-t, uniform bands). |
| 3 | `horizon_cross.png` | Both exchanges sharpen in lockstep; dead heat holds along the whole final day. |
| 4 | `model_benchmark.png` | The markets' shared premium over public statistics (the gray bar). |
| 5 | `why_sports.png` | BDW's −20%/FLB cliff collapses to the cost band in sports. |
| 6 | `minute_lead_lag.png` | No leader at any resolution; symmetric few-minute echo. |
| 7 | `fee_liquidity.png` | Fee incidence: volume −41% trend break, touch pinned at 1¢. |
| 8 | `margin_pit.png` + `spread_coherence.png` | Distributional layer: coherent ladders; MLB's one crack (books price it, Kalshi doesn't, unexploitable). |

Live demo if wanted: `python -m src.make_results` — 35 analyses, ~4 min,
zero failures, every report number regenerated from raw processed data.

## 2. Numbers to know cold

- **Headline set:** n=5,044 (frozen) / 5,053 on re-harvested master; 6 leagues,
  May 2025–Jul 2026. Brier K/P/B = 0.2180/0.2182/0.2181; clustered DM all
  n.s. (p=.15/.26/.54); TOST: every pairwise 90% CI within ±0.52e-3 (margin
  δ=1e-3). Per-league TOST formal in MLB/NBA/NHL (δ_min ≤ 0.84e-3);
  CFB/WNBA/NFL consistent-but-underpowered → hierarchical Bayes: every
  league×source HDI covers (0,1), σ_β≈0.10.
- **Sharpness:** equal (mean p(1−p) within 0.002; exchanges fractionally sharper).
- **Model leg:** walk-forward Elo Brier 0.2348 vs 0.2209–0.2210; ΔBrier
  ≈14e-3, z≈7.4 vs all three; book fully encompasses model (z=0.6); Kalshi
  adds beyond model+book (z=2.7). Premium largest CFB (+56e-3), smallest NHL/MLB.
- **Horizons:** books lead at T−24h (ΔBrier +0.73e-3, z=2.18, p=.029), gap
  closed by start; whisper absent at T−24h, created in final day; closes are
  efficient (day's move predicts nothing, book p=0.99).
- **Microstructure:** 15-min panel (210 games) — event study simultaneous;
  1-min panel (563 games, 202K changes) — bidirectional predictability
  z≈7 both ways, coef ~0.09; episodes half-cross same minute; no lineup-window
  burst (intensity ramps into final 75 min). Maker-driven discovery (markouts
  flat in size; taker imbalance uninformative).
- **Why sports (BDW contrast):** their all-Kalshi avg ROI ≈ −20%, sub-10c
  lose >60%; our sports moneylines @mid −0.45% (se 0.11), @ask+fee −4.6%,
  ladders −5.8%; sub-10c "cliff" = trade-recon artifact (570/571 recon,
  college longshots). Makers +5.6% vs takers −7.7% (qualitative match).
- **Costs:** taker all-in: Kalshi ≈ −4.2% ≈ books −4.1%; Poly ~1–1.75%;
  makers ~free. MLB ladder cell +8.4pts (z=10), Kalshi-specific (books
  +0.4pts), unexploitable (selling loses 2.9–4.5% net) — bias inside the
  cost band, like books inside vig. Run-line 45.0% home cover = documented
  structural feature (walk-off compression).
- **Fee experiment:** accuracy DiD null (p=.74); volume ratio −41% trend
  break at fee date (z=−3.6, placebo-clean windows); spread pinned at 1¢
  tick both eras (pre n=30 / post n=21, MW p=.43).
- **Nulls (own them):** behavioral fingerprints all null; no FLB anywhere;
  ensemble adds nothing; crowd-size doesn't scale accuracy.
- **Discipline:** 17 positive claims, BH-FDR 15/17 at q=0.05 (only the two
  pre-flagged p≈0.05 fragiles drop); equivalences inventoried separately.
- **Validation story (tell it as a strength):** impossible backtest profits →
  side-assignment audit → ticker-order rule (99.6% validated) → one marginal
  result reversed; trade-recon independently validated vs archived books
  (99% within 1pt); Poly pipeline validated twice (CLOB vs archive, 0.00 median).

**Which Polymarket (know this cold):** the GLOBAL on-chain platform, not the
newer regulated Polymarket US entity (insufficient history). Strengthens the
design: three regulatory regimes (CFTC exchange / offshore crypto / state-
licensed books) AND three largely non-overlapping participant pools (US
bettors on Kalshi+books; non-US on Poly Global) converge on identical prices —
the equivalence is not one crowd in three venues. The fee experiment is the
Global platform's 2026-03-30 sports fee. Possible ask: is a Polymarket-US
side comparison worth adding, or future work? (Recommend: future work.)

## 3. Limitations to volunteer before he asks

Consensus book line (not one book's risk book); trade-recon staleness in the
pre-cutoff era; constant-sample composition in horizon analyses; small-league
power (now posterior statements, not shrugs); fee analysis: March gamma
coverage gap + playoff-transition windows; single season, US sports, moneyline-
centric; WC 3-way n=9 descriptive; Murphy K-vs-Shin p=0.012 flicker —
reported, FDR-controlled, not oversold; 15-min→1-min panels are exchanges-only
(books have no minute feed).

## 4. Decisions to get from him (the checkpoint seven)

1. **Multiple testing:** two-family policy (FDR for discoveries, TOST for
   equivalences) — acceptable, or one family?
2. **TOST margin:** δ=0.001 Brier — convention he prefers?
3. **Interval-randomized PIT** — fine, or add a discrete variant?
4. **Clustering:** date-only vs two-way (date × league) robustness?
5. **Lead–lag formality:** predictive regressions + event study enough, or
   Hasbrouck information shares?
6. **WC 3-way scoring:** multiclass Brier only, or RPS alongside?
7. **Framing sign-off:** "sportsbook at the retail-taker surface, forecasting
   instrument in aggregate" as the organizing thesis.

## 5. Meeting-logistics asks (beyond the checkpoint)

8. **Report target:** grant final report only, or shape for a venue (Journal
   of Prediction Markets? IJF? arXiv preprint?) — changes length and voice.
9. **Draft schedule:** first full draft can be ready ~Aug 1–3; when can he
   turn comments around? (Two review cycles fit before Aug 24 if the first
   starts by Aug 8.)
10. **Public release:** OK to make the repo public after secret rotation?
    Any concern with shipping processed *book* lines (Odds API terms) vs
    "code + instructions"? Zenodo DOI vs arXiv for archiving?
11. **The one crack worth a paper?** MLB ladder blind spot + cost-band
    persistence — worth spinning into a standalone note later?
12. **Fall continuation:** CFB/CBB season + accumulated depth series (price-
    of-immediacy curve) extend naturally past Aug 24 — appetite for a
    follow-on (independent study / co-authored extension)?
13. **Kalshi academic data request** — worth sending under his name for
    granular history pre-cutoff?

## 6. Status vs plan (if he asks about timeline)

End of week 4 of 8. Everything through week 5 done; six unplanned extensions
delivered (BDW replication, Murphy, model leg, minute lead–lag, hierarchical
Bayes, fee incidence). Weeks 5–7: write (skeleton done, all numbers
regenerable one-command). Week 8: public-repo packaging + secret rotation.
Standing: Kalshi re-harvest ~Aug 4, weekly VPS rsync, final lead–lag +
first immediacy curve mid-Aug. Dropped/deferred honestly: CBB (season starts
after the grant window — future work), residual DH cleanup (24 games,
optional polish).
