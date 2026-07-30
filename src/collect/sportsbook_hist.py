"""Historical sportsbook closing lines -> consensus de-vigged probability per game.

For each game we query The Odds API historical snapshot nearest its official start,
average the moneyline across all books, and de-vig (normalize the pair to sum 1).
Games are bucketed by (sport, start rounded to `bucket_min`) so one paid call
(10 credits) covers every game starting together. Matched to our games by team name
+ commence-time proximity (which also separates doubleheaders).
"""
from __future__ import annotations

import os
import time
import datetime as dt
from pathlib import Path
import pandas as pd
import requests
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env", override=True)
KEY = os.getenv("ODDS_API_KEY")
BASE = "https://api.the-odds-api.com/v4"
_session = requests.Session()

SPORT = {"MLB": "baseball_mlb", "WNBA": "basketball_wnba", "NBA": "basketball_nba",
         "NFL": "americanfootball_nfl", "NHL": "icehockey_nhl",
         "CFB": "americanfootball_ncaaf", "CBB-M": "basketball_ncaab"}


def _snapshot(sport_key: str, iso_ts: str) -> list:
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


def _norm_name(s):
    """Accent/punctuation-insensitive team-name key (review 2026-07-30: raw
    substring matching silently dropped whole franchises — Montréal's accent,
    St. Louis's period, 'LA Clippers' vs 'Los Angeles Clippers')."""
    import unicodedata
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace(".", "").replace("'", "")
    for a, b in (("la clippers", "los angeles clippers"),
                 ("st louis", "saint louis"), ("st. louis", "saint louis")):
        s = s.replace(a, b)
    return s.strip()


def _match_hit(pn, team):
    t = _norm_name(team)
    pn = _norm_name(pn)
    return pn in t or t.endswith(pn)


def _consensus(game_obj, home, away):
    """Average implied prob across books, de-vig (normalize pair to 1)."""
    hs = aw = n = 0.0
    for bk in game_obj.get("bookmakers", []):
        mk = next((m for m in bk.get("markets", []) if m["key"] == "h2h"), None)
        if not mk:
            continue
        px = {o["name"]: o["price"] for o in mk["outcomes"]}
        if home in px and away in px and px[home] > 0 and px[away] > 0:
            hs += 1 / px[home]; aw += 1 / px[away]; n += 1
    if not n:
        return None
    ph, pa = hs / n, aw / n
    s = ph + pa
    return {"book_p1": round(ph / s, 4), "book_p2": round(pa / s, 4),
            "book_raw1": round(ph, 4), "book_raw2": round(pa, 4), "book_n_books": int(n)}


def build(out="data/processed/sportsbook_hist_prices.csv", leagues=None,
          bucket_min=30, flush_every=200, joint_only=True) -> None:
    m = pd.read_csv("data/processed/games_master.csv")
    m["start"] = pd.to_datetime(m["start_utc"], utc=True, format="ISO8601")
    if joint_only:  # only games priced by BOTH markets (the three-way target) — saves credits
        m = m[m["kalshi_p1"].notna() & m["poly_p1"].notna()]
    if leagues:
        m = m[m["league"].isin(leagues)]
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    m = m[~m["game_id"].isin(done)]

    # bucket by (sport, start rounded to bucket_min) -> one API call each
    m["bucket"] = m["start"].dt.floor(f"{bucket_min}min")
    rows, calls = [], 0
    for (lg, bucket), grp in m.groupby(["league", "bucket"]):
        sk = SPORT.get(lg)
        if not sk:
            continue
        snap = _snapshot(sk, bucket.strftime("%Y-%m-%dT%H:%M:%SZ"))
        calls += 1
        # index snapshot games for matching
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
                             "team1": g.team1, "team2": g.team2, **c})
        if len(rows) >= flush_every:
            _append(out, rows); rows = []
            print(f"  ...{calls} calls, flushed (~{calls*10} credits)", flush=True)
    if rows:
        _append(out, rows)
    print(f"done: {calls} API calls (~{calls*10} credits)", flush=True)


def _append(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(rows)
    if os.path.exists(path):
        df = pd.concat([pd.read_csv(path), df], ignore_index=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    import sys
    build(leagues=sys.argv[1:] or None)
