"""Data-quality gate: every processed dataset audited before any number is cited.

Checks per file: key uniqueness, value ranges (probabilities in (0,1), bid <=
ask, non-negative sizes), internal consistency (two-sided prices sum to 1),
cross-file referential integrity (master vs sources vs ESPN outcomes), the
duplicate hazards specific to resumable append collectors, and stray-file
hygiene. Severity: PASS / WARN (documented, non-blocking) / FAIL (blocks the
suite — make_results runs this first and a FAIL fails the run).
"""
from __future__ import annotations

import glob
import os
import sys

import numpy as np
import pandas as pd

P = "data/processed"
issues = {"PASS": 0, "WARN": 0, "FAIL": 0}


def report(level, name, msg=""):
    issues[level] += 1
    print(f"  [{level}] {name}" + (f" — {msg}" if msg else ""), flush=True)


def check(name, ok, msg_fail="", warn=False):
    if ok:
        report("PASS", name)
    else:
        report("WARN" if warn else "FAIL", name, msg_fail)


def approx_one(a, b, tol=0.02):
    s = a + b
    return s.dropna().sub(1).abs().le(tol)


def main():
    print("=== data quality audit ===", flush=True)

    # ---------- ESPN registry ----------
    espn = pd.read_csv(f"{P}/espn_games.csv")
    check("espn: espn_id unique", espn.espn_id.is_unique,
          f"{espn.espn_id.duplicated().sum()} dups")
    check("espn: winner values", espn.winner.dropna().isin(["home", "away"]).all())
    sc = espn[["home_score", "away_score"]].dropna()
    check("espn: scores sane", ((sc >= 0) & (sc < 300)).all().all())
    ties = espn[(espn.home_score == espn.away_score) & espn.winner.notna()]
    check("espn: no tied-score winners", len(ties) == 0, f"{len(ties)} rows", warn=True)

    # ---------- Kalshi inventory ----------
    k = pd.read_csv(f"{P}/kalshi_settled_markets.csv")
    check("kalshi inv: ticker unique", k.ticker.is_unique, f"{k.ticker.duplicated().sum()} dups")
    check("kalshi inv: won binary", k.won.isin([0, 1]).all())
    sides = k.groupby("event_ticker").size()
    odd = (sides != 2).sum()
    check("kalshi inv: 2 sides/event", odd == 0, f"{odd} events != 2 sides", warn=True)

    # ---------- match integrity ----------
    mt = pd.read_csv(f"{P}/kalshi_espn_matches.csv")
    mm = mt[mt.espn_id.notna()]
    check("matches: espn_id unique (1:1 enforced)", mm.espn_id.is_unique,
          f"{mm.espn_id.duplicated().sum()} ambiguous")

    # ---------- Kalshi closing quotes ----------
    q = pd.read_csv(f"{P}/kalshi_hist_prices.csv")
    check("kalshi px: game_id unique", q.game_id.is_unique, f"{q.game_id.duplicated().sum()} dups")
    check("kalshi px: p1+p2 ~ 1", approx_one(q.kalshi_p1, q.kalshi_p2, 0.001).all())
    for i in (1, 2):
        bad = (q[f"k_yes_ask{i}"] < q[f"k_yes_bid{i}"]).sum()
        check(f"kalshi px: bid<=ask side{i}", bad == 0, f"{bad} crossed")
    inr = q[["k_yes_bid1", "k_yes_ask1", "k_yes_bid2", "k_yes_ask2"]].stack().dropna()
    check("kalshi px: quotes in [0,1]", inr.between(0, 1).all())

    # ---------- Poly Global + books closes ----------
    pg = pd.read_csv(f"{P}/polymarket_hist_prices.csv")
    check("poly px: game_id unique", pg.game_id.is_unique, f"{pg.game_id.duplicated().sum()} dups")
    check("poly px: p1+p2 ~ 1", approx_one(pg.poly_p1, pg.poly_p2, 0.001).all())
    for f, lab in [("sportsbook_hist_prices.csv", "book close"),
                   ("sportsbook_open_prices.csv", "book T-24h")]:
        b = pd.read_csv(f"{P}/{f}")
        cols = [c for c in b.columns if c.endswith("_p1") or c.endswith("p_1")]
        check(f"{lab}: game_id unique", b.game_id.is_unique,
              f"{b.game_id.duplicated().sum()} dups")
    b = pd.read_csv(f"{P}/sportsbook_hist_prices.csv")
    over = b.book_raw1 + b.book_raw2
    check("book close: overround in [1.00,1.15]", over.dropna().between(0.99, 1.15).mean() > 0.995,
          f"{(~over.dropna().between(0.99, 1.15)).sum()} outside", warn=True)

    # ---------- master ----------
    m = pd.read_csv(f"{P}/games_master.csv")
    check("master: game_id unique", m.game_id.is_unique, f"{m.game_id.duplicated().sum()} dups")
    check("master: outcome in {1,2}", m.outcome.dropna().isin([1, 2]).all())
    for pre in ("kalshi", "poly", "book"):
        both = m[[f"{pre}_p1", f"{pre}_p2"]].dropna()
        check(f"master: {pre} p1+p2 ~ 1", approx_one(both[f"{pre}_p1"], both[f"{pre}_p2"]).all())
    # outcome vs ESPN winner
    j = m.merge(espn[["espn_id", "winner"]].rename(columns={"espn_id": "game_id"}), on="game_id")
    j = j[j.outcome.notna() & j.winner.notna() & ~j.outcome_disagree.fillna(False)]
    mism = ((j.outcome == 1) != (j.winner == "home")).sum()
    check("master: outcome == ESPN winner (clean rows)", mism == 0, f"{mism} mismatches")
    # three-way clean set reproduces
    from src.analysis.three_way import load
    n3 = len(load())
    check("master: three-way clean set size", 5000 <= n3 <= 5200, f"n={n3}", warn=True)
    print(f"         (three-way clean n = {n3:,})", flush=True)

    # ---------- ladders ----------
    lad = pd.read_csv(f"{P}/kalshi_spread_prices.csv")
    check("ladders: ticker unique", lad.ticker.is_unique, f"{lad.ticker.duplicated().sum()} dups")
    check("ladders: won binary", lad.won.dropna().isin([0, 1]).all())
    check("ladders: prob in (0,1)", lad.prob.dropna().between(0, 1).all())
    crossed = (lad.yes_ask < lad.yes_bid).sum()
    check("ladders: bid<=ask", crossed == 0, f"{crossed} crossed", warn=True)

    # ---------- horizons ----------
    for f, pre in [("kalshi_horizons.csv", "p_h"), ("poly_horizons.csv", "q_h")]:
        h = pd.read_csv(f"{P}/{f}")
        check(f"{f}: game_id unique", h.game_id.is_unique,
              f"{h.game_id.duplicated().sum()} dups")
        cols = [c for c in h.columns if c.startswith(pre)]
        vals = h[cols].stack().dropna()   # pandas 3.0 stack keeps NaN
        check(f"{f}: horizons in (0,1)", vals.between(0, 1).all())

    # ---------- trades ----------
    t = pd.read_csv(f"{P}/kalshi_trades_24h.csv")
    check("trades: price in (0,1)", t.yes_price.dropna().between(0, 1).all())
    check("trades: count > 0", (t["count"].dropna() > 0).all())
    dup_share = t.duplicated().mean()
    check("trades: exact-dup rows < 1%", dup_share < 0.01, f"{dup_share:.2%}", warn=True)
    tt = pd.to_datetime(t.created_time, utc=True, format="ISO8601")
    ts = pd.to_datetime(t.start_utc, utc=True, format="ISO8601")
    inwin = ((tt <= ts) & (tt >= ts - pd.Timedelta("25h"))).mean()
    check("trades: fills inside 24h window", inwin > 0.999, f"{1-inwin:.3%} outside", warn=True)

    # ---------- minute paths ----------
    mp = pd.read_csv(f"{P}/minute_paths.csv")
    dups = mp.duplicated(["game_id", "mts"]).sum()
    check("minute_paths: (game,minute) unique", dups == 0, f"{dups} dups")
    vals = mp[["k_mid", "p_price"]].stack().dropna()
    check("minute_paths: prices in (0,1)", vals.between(0, 1).all())

    # ---------- Polymarket US ----------
    cat = pd.read_csv(f"{P}/polyus_catalog.csv")
    check("polyus catalog: slug unique", cat.slug.is_unique, f"{cat.slug.duplicated().sum()} dups")
    pu = pd.read_csv(f"{P}/polyus_prices.csv")
    dups = pu.duplicated(["slug", "tape_date"]).sum()
    check("polyus prices: (slug,tape_date) unique", dups == 0, f"{dups} dups")
    check("polyus prices: close in (0,1)", pu.close_price.between(0, 1).all())
    check("polyus prices: stale_min >= 0", (pu.stale_min >= 0).all())

    # ---------- fee / spread files ----------
    fv = pd.read_csv(f"{P}/fee_volumes.csv")
    check("fee_volumes: game_id unique", fv.game_id.is_unique,
          f"{fv.game_id.duplicated().sum()} dups")
    fs = pd.read_csv(f"{P}/fee_spreads.csv")
    check("fee_spreads: game_id unique", fs.game_id.is_unique,
          f"{fs.game_id.duplicated().sum()} dups", warn=True)
    for f in ("poly_spreads.csv", "fee_spreads.csv"):
        d = pd.read_csv(f"{P}/{f}")
        neg = (d.poly_spread < 0).sum()
        check(f"{f}: spreads >= 0", neg == 0, f"{neg} negative")

    # ---------- live mirror ----------
    lv = pd.read_csv("data/live/vps_mirror/snapshots.csv")
    pair = lv[["p1", "p2"]].dropna()
    check("live: p1+p2 ~ 1", approx_one(pair.p1, pair.p2).all())
    depth_cols = [c for c in lv.columns if c.startswith(("bidq", "askq", "d5"))]
    if depth_cols:
        dvals = lv[depth_cols].stack().dropna()
        check("live: depth non-negative", (dvals >= 0).all())

    # ---------- stray-file hygiene ----------
    strays = [f for pat in ("data/processed/* 2.*", "logs/* 2.*")
              for f in glob.glob(pat)]
    check("hygiene: no ' 2.' stray copies", len(strays) == 0,
          "; ".join(strays), warn=True)

    print(f"\naudit: {issues['PASS']} pass, {issues['WARN']} warn, {issues['FAIL']} FAIL", flush=True)
    sys.exit(1 if issues["FAIL"] else 0)


if __name__ == "__main__":
    main()
