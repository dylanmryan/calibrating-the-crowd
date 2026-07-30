"""Sportsbook consensus lines at T-24h ("opening" side of the proposal's
open-vs-close commitment).

Same machinery as the closing-line run (sportsbook_hist), but the snapshot is
taken 24 hours before each game's official start. Enables the horizon-resolved
equivalence question: is the exchange already equivalent to the books a day
out, or does the dead heat only form by start?

Cost: ~10 credits per (league, 30-min bucket) snapshot call, ~23K total for the
joint set (user-approved 2026-07-10). Hard stop below CREDIT_FLOOR. Some games
won't be listed a day ahead (notably MLB pitcher-dependent lines) — recorded
as misses, which is itself data.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.collect.sportsbook_hist import SPORT, _consensus, _match_hit, _snapshot, _append

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env", override=True)
OUT = "data/processed/sportsbook_open_prices.csv"
CREDIT_FLOOR = 7_500   # lowered 2026-07-31 for the user-approved T-24h franchise top-up
OFFSET_H = 24


def build(out=OUT, bucket_min=30, flush_every=200, game_ids=None):
    import requests
    m = pd.read_csv("data/processed/games_master.csv")
    m = m[m["kalshi_p1"].notna() & m["poly_p1"].notna()].copy()
    m["start"] = pd.to_datetime(m["start_utc"], utc=True, format="ISO8601")
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    m = m[~m["game_id"].isin(done)]
    if game_ids is not None:   # targeted top-up (e.g. match-fix re-collection)
        m = m[m["game_id"].isin(set(game_ids))]
    m["bucket"] = (m["start"] - pd.Timedelta(hours=OFFSET_H)).dt.floor(f"{bucket_min}min")
    print(f"target games: {len(m):,} ({len(done)} done)", flush=True)

    key = os.getenv("ODDS_API_KEY")
    rows, calls, remaining = [], 0, None
    for (lg, bucket), grp in m.groupby(["league", "bucket"]):
        sk = SPORT.get(lg)
        if not sk:
            continue
        if remaining is not None and remaining < CREDIT_FLOOR:
            print(f"CREDIT FLOOR reached ({remaining:,.0f}) — stopping", flush=True)
            break
        snap = _snapshot(sk, bucket.strftime("%Y-%m-%dT%H:%M:%SZ"))
        calls += 1
        # read remaining credits cheaply every ~50 calls
        if calls % 50 == 0:
            r = requests.get("https://api.the-odds-api.com/v4/sports",
                             params={"apiKey": key}, timeout=20)
            remaining = float(r.headers.get("x-requests-remaining") or 0)
        for g in grp.itertuples(index=False):
            home, away = str(g.team1).lower(), str(g.team2).lower()
            best = None
            for sg in snap:
                ct = pd.Timestamp(sg.get("commence_time"))
                if abs((ct - g.start).total_seconds()) > 3 * 3600:
                    continue
                if _match_hit(home, sg.get("home_team", "")) and _match_hit(away, sg.get("away_team", "")):
                    best = sg
                    break
            if not best:
                continue
            c = _consensus(best, best["home_team"], best["away_team"])
            if c:
                rows.append({"game_id": g.game_id, "league": lg, "start_utc": g.start_utc,
                             "team1": g.team1, "team2": g.team2,
                             **{k.replace("book_", "book24_"): v for k, v in c.items()}})
        if len(rows) >= flush_every:
            _append(out, rows); rows = []
            print(f"  ...{calls} calls (~{calls*10} credits), remaining ~{remaining}", flush=True)
    if rows:
        _append(out, rows)
    print(f"done: {calls} calls (~{calls*10} credits)", flush=True)


if __name__ == "__main__":
    build()
