"""Per-book EU closing lines: the sharp book and the other exchanges.

The paper's "sportsbook" benchmark is a de-vigged US retail consensus
(per-book quotes were not retained). This leg re-snapshots the joint set's
closing buckets in the EU region and KEEPS EVERY BOOK, which buys three
things at once:
  1. Pinnacle — the academic-standard sharp book (low margin, winners
     welcome). Do the exchanges track the sharp line tighter than the
     retail consensus?
  2. betfair_ex_eu / matchbook — actual betting exchanges. A same-game
     comparison of Kalshi/Polymarket against the incumbent exchange design.
  3. Per-book dispersion — which individual books sit closest to the
     exchanges, and the Levitt line-shading test book by book.

Same bucket-and-match machinery as the closing run (60-min buckets at
official start). ~10 credits per (league, hour) bucket, ~26.8K total
(within the 2026-08-04 approved envelope). Resumable by game_id.
Output: data/processed/sportsbook_sharp_prices.csv (one row per game-book).
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from src.collect.sportsbook_hist import SPORT, _match_hit

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env", override=True)
BASE = "https://api.the-odds-api.com/v4"
KEY = os.getenv("ODDS_API_KEY")
OUT = "data/processed/sportsbook_sharp_prices.csv"
CREDIT_FLOOR = 12000   # live-feed reserve through Aug 24
_session = requests.Session()


def _snapshot_eu(sport_key: str, iso_ts: str) -> list:
    for attempt in range(3):
        r = _session.get(f"{BASE}/historical/sports/{sport_key}/odds", params={
            "apiKey": KEY, "regions": "eu", "markets": "h2h",
            "oddsFormat": "decimal", "date": iso_ts}, timeout=30)
        if r.status_code == 200:
            return r.json().get("data", [])
        if r.status_code in (429, 500, 502, 503):
            time.sleep(1.5 * (attempt + 1))
        else:
            return []
    return []


def _append(out, rows):
    pd.DataFrame(rows).to_csv(out, mode="a", header=not os.path.exists(out), index=False)


def build(out=OUT, flush_every=400):
    m = pd.read_csv("data/processed/games_master.csv", low_memory=False)
    m = m[m["kalshi_p1"].notna() & m["poly_p1"].notna()].copy()
    m["start"] = pd.to_datetime(m["start_utc"], utc=True, format="ISO8601")
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    m = m[~m["game_id"].isin(done)]
    m["bucket"] = m["start"].dt.floor("60min")
    print(f"target games: {len(m):,} ({len(done)} done) | "
          f"buckets: {m.groupby(['league', 'bucket']).ngroups:,}", flush=True)

    rows, calls, remaining = [], 0, None
    for (lg, bucket), grp in m.groupby(["league", "bucket"]):
        sk = SPORT.get(lg)
        if not sk:
            continue
        if remaining is not None and remaining < CREDIT_FLOOR:
            print(f"CREDIT FLOOR reached ({remaining:,.0f}) — stopping", flush=True)
            break
        snap = _snapshot_eu(sk, bucket.strftime("%Y-%m-%dT%H:%M:%SZ"))
        calls += 1
        if calls % 50 == 0:
            r = _session.get(f"{BASE}/sports", params={"apiKey": KEY}, timeout=20)
            remaining = float(r.headers.get("x-requests-remaining") or 0)
        for g in grp.itertuples(index=False):
            home, away = str(g.team1).lower(), str(g.team2).lower()
            best = None
            for sg in snap:
                ct = pd.Timestamp(sg.get("commence_time"))
                if abs((ct - g.start).total_seconds()) > 3 * 3600:
                    continue
                if _match_hit(home, sg.get("home_team", "")) and \
                        _match_hit(away, sg.get("away_team", "")):
                    best = sg
                    break
            if not best:
                continue
            for bk in best.get("bookmakers", []):
                mk = next((x for x in bk.get("markets", []) if x["key"] == "h2h"), None)
                if not mk:
                    continue
                px = {o["name"]: o["price"] for o in mk["outcomes"]}
                h, a = px.get(best["home_team"]), px.get(best["away_team"])
                if not h or not a or h <= 1 or a <= 1:
                    continue
                rows.append({"game_id": g.game_id, "league": lg,
                             "start_utc": g.start_utc, "team1": g.team1,
                             "team2": g.team2, "book": bk["key"],
                             "raw_p1": 1 / h, "raw_p2": 1 / a,
                             "book_ts": mk.get("last_update")})
        if len(rows) >= flush_every:
            _append(out, rows)
            rows = []
            print(f"  ...{calls} calls (~{calls*10} credits), remaining ~{remaining}", flush=True)
    if rows:
        _append(out, rows)
    print(f"done: {calls} calls (~{calls*10} credits)", flush=True)


if __name__ == "__main__":
    build()
