"""Fee-incidence collection: per-game volumes and archived spreads around the
Polymarket sports-fee introduction (2026-03-30).

Three legs, all resumable:
  volumes — (a) Polymarket per-game USD volume from gamma (closed=true unlocks
            settled markets; batched condition_ids, free); (b) Kalshi final-24h
            trade volume from /historical/trades (retained pre-cutoff; the bulk
            market objects null out volume past the 60-day window). Home-side
            ticker for Kalshi vs whole-market for Poly: levels aren't
            comparable, but the within-game LOG RATIO is — the DiD uses only
            its pre/post change. NBA+NHL both-priced games Feb 2 - May 25.
  spreads — OddPool archived Polymarket books (coverage starts 2026-03-20):
            quoted spread at T-30m for a pre-fee (Mar 21-29) vs post-fee
            (Apr 1-14) sample. ~25s/request free-tier throttle.

Usage: python -m src.collect.fee_volumes [volumes|spreads]
"""
from __future__ import annotations

import os
import sys
import time

import pandas as pd
import requests

from src.collect.kalshi_hist_prices import _rule_home
from src.collect.kalshi_trades import fetch_trades
from src.collect.poly_spreads import fetch_book

VOL_OUT = "data/processed/fee_volumes.csv"
SPR_OUT = "data/processed/fee_spreads.csv"
G = "https://gamma-api.polymarket.com"
WIN = ("2026-02-02", "2026-05-25")
FEE_DATE = "2026-03-30"
_session = requests.Session()


def sample():
    m = pd.read_csv("data/processed/games_master.csv")
    m = m[m.outcome.notna() & ~m.outcome_disagree.fillna(False)
          & m.kalshi_p1.notna() & m.poly_p1.notna()
          & m.league.isin(["NBA", "NHL"])].copy()
    m = m[(m.start_utc >= WIN[0]) & (m.start_utc < WIN[1])]
    tok = pd.read_csv("data/processed/poly_token_map_full.csv")[
        ["game_id", "condition_id", "token_home"]]
    mt = pd.read_csv("data/processed/kalshi_espn_matches.csv")[["espn_id", "event_ticker"]]
    kk = pd.read_csv("data/processed/kalshi_settled_markets.csv")[["event_ticker", "ticker"]]
    m = (m.merge(tok, on="game_id")
          .merge(mt.rename(columns={"espn_id": "game_id"}), on="game_id"))
    rows = []
    for r in m.itertuples(index=False):
        sides = kk[kk.event_ticker == r.event_ticker]["ticker"].tolist()
        codes = sorted({t.rsplit("-", 1)[-1] for t in sides})
        rh = _rule_home(r.event_ticker, codes) if len(codes) == 2 else None
        tk = next((t for t in sides if rh and t.endswith("-" + rh)), None)
        if tk:
            rows.append({"game_id": r.game_id, "league": r.league,
                         "start_utc": r.start_utc, "ticker": tk,
                         "condition_id": r.condition_id, "token_home": r.token_home})
    return pd.DataFrame(rows)


def poly_volumes(cids):
    out = {}
    for i in range(0, len(cids), 20):
        batch = cids[i:i + 20]
        # gamma wants repeated condition_ids params, not a comma-joined string
        r = _session.get(f"{G}/markets", params={"condition_ids": batch,
                                                 "closed": "true", "limit": 100}, timeout=30)
        if r.status_code == 200:
            for mk in r.json():
                out[mk.get("conditionId")] = mk.get("volumeNum")
        time.sleep(0.3)
    return out


def volumes(out=VOL_OUT):
    g = sample()
    print(f"{len(g)} NBA/NHL both-priced games in {WIN[0]}..{WIN[1]}", flush=True)
    pv = poly_volumes(list(g.condition_id))
    print(f"gamma volumes: {sum(v is not None for v in pv.values())}/{len(g)}", flush=True)
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    todo = g[~g.game_id.isin(done)]
    buf, n = [], 0
    for r in todo.itertuples(index=False):
        fills = fetch_trades(r.ticker, r.start_utc, window_h=24)
        n += 1
        kc = sum(float(t.get("count_fp") or t.get("count") or 0) for t in fills)
        kn = sum(float(t.get("count_fp") or t.get("count") or 0)
                 * float(t.get("yes_price_dollars") or 0) for t in fills)
        buf.append({"game_id": r.game_id, "league": r.league, "start_utc": r.start_utc,
                    "poly_vol": pv.get(r.condition_id),
                    "k_fills": len(fills), "k_contracts": kc, "k_notional": round(kn, 2)})
        if len(buf) >= 25:
            df = pd.DataFrame(buf)
            df.to_csv(out, mode="a", header=not os.path.exists(out), index=False)
            buf = []
            print(f"  {n}/{len(todo)} kalshi trade volumes", flush=True)
        time.sleep(0.15)
    if buf:
        pd.DataFrame(buf).to_csv(out, mode="a", header=not os.path.exists(out), index=False)
    print(f"done -> {out}", flush=True)


def spreads(out=SPR_OUT, per_era=30):
    g = sample()
    eras = {"pre": ("2026-03-21", "2026-03-30"), "post": ("2026-04-01", "2026-04-15")}
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    for era, (a, b) in eras.items():
        pick = (g[(g.start_utc >= a) & (g.start_utc < b) & ~g.game_id.isin(done)]
                .sample(frac=1, random_state=7).groupby("league").head(per_era // 2 + 3)
                .head(per_era))
        print(f"{era}: fetching {len(pick)} archived books", flush=True)
        for r in pick.itertuples(index=False):
            snap = fetch_book(r.condition_id, r.token_home,
                              (pd.Timestamp(r.start_utc) - pd.Timedelta("30min")).isoformat())
            if snap and snap.get("best_bid") is not None and snap.get("best_ask") is not None:
                row = {"game_id": r.game_id, "league": r.league, "start_utc": r.start_utc,
                       "era": era, "poly_bid": float(snap["best_bid"]),
                       "poly_ask": float(snap["best_ask"]),
                       "poly_spread": round(float(snap["best_ask"]) - float(snap["best_bid"]), 4)}
                pd.DataFrame([row]).to_csv(out, mode="a",
                                           header=not os.path.exists(out), index=False)
            time.sleep(25)
    print(f"done -> {out}", flush=True)


if __name__ == "__main__":
    leg = sys.argv[1] if len(sys.argv) > 1 else "volumes"
    {"volumes": volumes, "spreads": spreads}[leg]()
