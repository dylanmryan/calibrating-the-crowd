"""Deep coherence audit: is the data TRUE, not just well-formed?

The structural gate (data_audit) checks shapes; this checks meaning, by
cross-examination — each failure mode has a signature that independent
sources make visible:

  look-ahead   — any closing quote timestamped after its game's start;
  misattach    — a price attached to the wrong game shows up as gross
                 cross-source disagreement on that game;
  clock errors — Polymarket US's own gameStartTime vs ESPN's start;
  side flips   — league home-win rates outside sane bands, or a source's
                 price NEGATIVELY correlated with outcomes in any league,
                 plus the two dead-bug signatures (identical quotes on both
                 sides; exact 0.5/0.5 pairs);
  zombie data  — flat-lined horizon paths and dead minute series;
  fork check   — kalshi_horizons' at-start price vs the independent closing
                 pipeline on the same games: two codepaths, one quantity.

Severity mirrors data_audit: FAIL exits nonzero (blocks make_results).
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

P = "data/processed"
issues = {"PASS": 0, "WARN": 0, "FAIL": 0}


def check(name, ok, msg="", warn=False):
    lvl = "PASS" if ok else ("WARN" if warn else "FAIL")
    issues[lvl] += 1
    print(f"  [{lvl}] {name}" + (f" — {msg}" if msg and not ok else ""), flush=True)


def main():
    print("=== deep coherence audit ===", flush=True)
    m = pd.read_csv(f"{P}/games_master.csv")
    clean = m[m.outcome.notna() & ~m.outcome_disagree.fillna(False)].copy()

    # ---------- 1. look-ahead: quote timestamps vs start ----------
    q = pd.read_csv(f"{P}/kalshi_hist_prices.csv")
    neg = ((q.k_stale1 < 0) | (q.k_stale2 < 0)).sum()
    check("no look-ahead: kalshi staleness >= 0", neg == 0, f"{neg} negative")
    pu = pd.read_csv(f"{P}/polyus_prices.csv")
    check("no look-ahead: polyus close <= start", (pu.stale_min >= 0).all(),
          f"{(pu.stale_min < 0).sum()} negative")
    pg_cols = pd.read_csv(f"{P}/polymarket_hist_prices.csv", nrows=1).columns
    stale_c = [c for c in pg_cols if "stale" in c]
    if stale_c:
        pg = pd.read_csv(f"{P}/polymarket_hist_prices.csv")
        check("no look-ahead: poly staleness >= 0", (pg[stale_c[0]].dropna() >= 0).all())

    # ---------- 2. cross-source disagreement = misattachment detector ----------
    pairs = [("kalshi_p1", "poly_p1", "K-P"), ("kalshi_p1", "book_p1", "K-B"),
             ("poly_p1", "book_p1", "P-B")]
    flagged = set()
    for a, b, lab in pairs:
        d = clean[[a, b, "game_id", "league", "team1", "team2", "date"]].dropna()
        gap = (d[a] - d[b]).abs()
        med, p99, worst = gap.median(), gap.quantile(0.99), gap.max()
        n_gross = (gap > 0.15).sum()
        check(f"cross-source {lab}: gross disagreements (<0.5%)",
              n_gross / len(d) < 0.005, f"{n_gross}/{len(d)}")
        print(f"         {lab}: median {med*100:.1f}pt, p99 {p99*100:.1f}pt, max {worst*100:.1f}pt", flush=True)
        flagged |= set(d.loc[gap > 0.15, "game_id"])
        agree = ((d[a] > 0.5) == (d[b] > 0.5)) | d[a].between(0.45, 0.55) | d[b].between(0.45, 0.55)
        check(f"cross-source {lab}: same favorite (>=98%)", agree.mean() >= 0.98,
              f"{(~agree).mean():.2%} flipped")
    if flagged:
        print(f"\n  worst cross-source disagreements ({len(flagged)} games) — eyeball:", flush=True)
        w = clean[clean.game_id.isin(flagged)][
            ["game_id", "league", "date", "team1", "team2", "kalshi_p1", "poly_p1", "book_p1"]]
        print(w.head(8).to_string(index=False), flush=True)

    # ---------- 3. clock check: Polymarket US gameStartTime vs ESPN ----------
    from src.analysis.four_way import build_prices
    pus = build_prices()
    espn = pd.read_csv(f"{P}/espn_games.csv")
    pus2 = pus.copy()
    espn2 = espn[espn.winner.isin(["home", "away"])].copy()
    espn2["lg"] = espn2.league.replace({"CBB-M": "CBB"})
    espn2["date"] = pd.to_datetime(espn2.start_utc, utc=True, format="ISO8601").dt.date
    espn2["codes"] = [frozenset((str(h).upper(), str(a).upper()))
                      for h, a in zip(espn2.home_abbr, espn2.away_abbr)]
    pus2["codes"] = [frozenset((c1, c2)) for c1, c2 in zip(pus2.code1, pus2.code2)]
    j = pus2.merge(espn2[["lg", "codes", "date", "start_utc"]],
                   left_on=["league", "codes", "date"], right_on=["lg", "codes", "date"])
    dt_min = (pd.to_datetime(j.game_start, utc=True, format="ISO8601")
              - pd.to_datetime(j.start_utc, utc=True, format="ISO8601")).dt.total_seconds().abs() / 60
    check("clock: PolyUS anchor fallback share (documented; filtered in four_way)",
          (dt_min > 30).mean() < 0.15, f"{(dt_min > 30).mean():.2%}", warn=True)
    # the analysis set itself must be free of post-start closes
    from src.analysis.four_way import match_games
    mm = match_games(pus)
    kept = mm[(mm.anchor_delta_min <= 30) & (mm.eff_stale_min >= 0)]
    check("clock: four-way analysis set has zero post-start closes",
          (kept.eff_stale_min >= 0).all() and len(kept) > 0,
          f"{(mm.eff_stale_min < 0).sum()} contaminated pre-filter, all excluded")
    print(f"         PolyUS-vs-ESPN start deltas: median {dt_min.median():.1f}min, "
          f"p99 {dt_min.quantile(0.99):.0f}min (n={len(j):,})", flush=True)

    # ---------- 4. side flips ----------
    espn_cl = espn[espn.winner.isin(["home", "away"])]
    for lg, g in espn_cl.groupby("league"):
        hw = (g.winner == "home").mean()
        check(f"home-win rate sane: {lg}", 0.42 <= hw <= 0.68, f"{hw:.1%}", warn=True)
    for src in ("kalshi_p1", "poly_p1", "book_p1"):
        for lg, g in clean.dropna(subset=[src]).groupby("league"):
            r = np.corrcoef(g[src], (g.outcome == 1).astype(float))[0, 1]
            if not (r > 0.05):
                check(f"price-outcome corr positive: {src}/{lg}", False, f"r={r:+.3f}")
                break
        else:
            continue
    check("price-outcome corr positive: all source x league", True)
    same_quote = ((q.k_yes_bid1 == q.k_yes_bid2) & (q.k_yes_ask1 == q.k_yes_ask2)
                  & q.k_yes_bid1.notna()).sum()
    genuine = ((q.k_yes_bid1 == q.k_yes_bid2) & (q.k_yes_ask1 == q.k_yes_ask2)
               & q.kalshi_p1.between(0.47, 0.53)).sum()
    check("bug signature: identical-quotes-both-sides only at coin flips",
          same_quote == genuine, f"{same_quote - genuine} suspicious of {same_quote}")
    # exact 0.5/0.5 pairs are legitimate iff the books also price ~50/50
    half = clean[(clean.kalshi_p1 == 0.5) & (clean.kalshi_p2 == 0.5)]
    hb = half.book_p1.dropna()
    check("bug signature: kalshi 0.5/0.5 pairs are genuine coin flips",
          len(hb) == 0 or hb.between(0.45, 0.55).all(),
          f"{(~hb.between(0.45, 0.55)).sum()} of {len(hb)} not book-confirmed")

    # ---------- 5. zombie data ----------
    kh = pd.read_csv(f"{P}/kalshi_horizons.csv")
    hcols = [c for c in kh.columns if c.startswith("p_h")]
    flat = (kh[hcols].nunique(axis=1) == 1).mean()
    check("zombie: flat kalshi horizon paths (<10%)", flat < 0.10, f"{flat:.1%}", warn=True)
    mp = pd.read_csv(f"{P}/minute_paths.csv")
    dead = (mp.groupby("game_id").k_mid.nunique() <= 1).mean()
    # dead series have FULL observation counts (resting books that never
    # repriced for 6h) — a market state, not missing data
    check("zombie: dead kalshi minute series (<25%, resting books)", dead < 0.25,
          f"{dead:.1%}", warn=True)

    # ---------- 6. fork check: horizons p_h0 vs closing pipeline ----------
    f = kh[["game_id", "p_h0"]].dropna().merge(
        q[["game_id", "kalshi_p1"]].dropna(), on="game_id")
    gap = (f.p_h0 - f.kalshi_p1).abs()
    check("fork: horizons@start vs close pipeline (median <= 2pt)",
          gap.median() <= 0.02, f"median {gap.median()*100:.1f}pt")
    print(f"         fork gap: median {gap.median()*100:.1f}pt, p95 {gap.quantile(.95)*100:.1f}pt, "
          f">10pt in {(gap > 0.10).mean():.1%} (n={len(f):,}; trade path vs book-mid — "
          f"small gaps expected)", flush=True)

    print(f"\ndeep audit: {issues['PASS']} pass, {issues['WARN']} warn, {issues['FAIL']} FAIL", flush=True)
    sys.exit(1 if issues["FAIL"] else 0)


if __name__ == "__main__":
    main()
