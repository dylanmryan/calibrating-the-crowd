"""Per-book US closing quotes, random half-sample: the DK/FanDuel record.

The closing US collection stored only the consensus; the per-book EU leg
answered the sharp-book questions but not the one a US-institution paper
gets asked: do DraftKings/FanDuel/BetMGM — the books Americans actually
use — shade their lines? A random half of the joint set's closing buckets
(seeded shuffle, so any early stop is still an unbiased sample) banks the
per-book US record before the subscription lapses (Sept 2026).

~10 credits per (league, hour) bucket, ~13.4K for the half. Floor 12K.
Output: data/processed/sportsbook_us_books.csv (one row per game-book).
"""
from __future__ import annotations

import os
import random
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
OUT = "data/processed/sportsbook_us_books.csv"
CREDIT_FLOOR = 12000
_session = requests.Session()


def _snapshot_us(sport_key: str, iso_ts: str) -> list:
    for attempt in range(3):
        r = _session.get(f"{BASE}/historical/sports/{sport_key}/odds", params={
            "apiKey": KEY, "regions": "us", "markets": "h2h",
            "oddsFormat": "decimal", "date": iso_ts}, timeout=30)
        if r.status_code == 200:
            return r.json().get("data", [])
        if r.status_code in (429, 500, 502, 503):
            time.sleep(1.5 * (attempt + 1))
        else:
            return []
    return []


def build(out=OUT, half=True, flush_every=400):
    m = pd.read_csv("data/processed/games_master.csv", low_memory=False)
    m = m[m["kalshi_p1"].notna() & m["poly_p1"].notna()].copy()
    m["start"] = pd.to_datetime(m["start_utc"], utc=True, format="ISO8601")
    m["bucket"] = m["start"].dt.floor("60min")
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    m = m[~m["game_id"].isin(done)]
    groups = list(m.groupby(["league", "bucket"]))
    random.Random(17).shuffle(groups)
    if half:
        groups = groups[: (len(groups) + 1) // 2]
    print(f"buckets this run: {len(groups):,} (~{len(groups)*10:,} credits) | "
          f"games in scope: {sum(len(g) for _, g in groups):,}", flush=True)

    rows, calls, remaining = [], 0, None
    for (lg, bucket), grp in groups:
        sk = SPORT.get(lg)
        if not sk:
            continue
        if remaining is not None and remaining < CREDIT_FLOOR:
            print(f"CREDIT FLOOR reached ({remaining:,.0f}) — stopping", flush=True)
            break
        snap = _snapshot_us(sk, bucket.strftime("%Y-%m-%dT%H:%M:%SZ"))
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
            pd.DataFrame(rows).to_csv(out, mode="a",
                                      header=not os.path.exists(out), index=False)
            rows = []
            print(f"  ...{calls} calls (~{calls*10} credits), remaining ~{remaining}",
                  flush=True)
    if rows:
        pd.DataFrame(rows).to_csv(out, mode="a", header=not os.path.exists(out), index=False)
    print(f"done: {calls} calls (~{calls*10} credits)", flush=True)


if __name__ == "__main__":
    build()
