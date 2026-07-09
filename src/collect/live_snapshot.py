"""Live multi-source price snapshotter (Kalshi book + sportsbook moneyline).

Run on a schedule (e.g. every 15 min). For each in-season game inside its pre-game
window, it records the CURRENT price from each source as one append-only row, building
the time-series needed for sportsbook-vs-prediction-market lead-lag ("influence") analysis.

team1 = home, team2 = away (consistent across sources). Prices are per-side implied
probabilities, normalized so the pair sums to 1 (de-vig / spread-removed). Polymarket
plugs in later (its game-market discovery is a separate workstream).
"""
from __future__ import annotations

import os
import time
import base64
import datetime as dt
from pathlib import Path
import pandas as pd
import requests
from dotenv import load_dotenv
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from src.collect.espn import fetch_day
from src.collect import polymarket
from src.match.kalshi_espn import kalshi_games, espn_games, learn_aliases, ALIASES

# Resolve paths relative to the project root so this runs on any machine (Mac or cloud box).
_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env")

KHOST = "https://api.elections.kalshi.com"
BASE_K = f"{KHOST}/trade-api/v2"
ODDS = "https://api.the-odds-api.com/v4"
_session = requests.Session()

# Kalshi live order book requires a signed request (the public endpoint returns empty).
_KEY_ID = os.getenv("KALSHI_API_KEY_ID")
_KEYPATH = os.getenv("KALSHI_PRIVATE_KEY_PATH", "")
if _KEYPATH and not os.path.isabs(_KEYPATH):
    _KEYPATH = str(_ROOT / _KEYPATH)  # relative key path -> resolve against project root
with open(_KEYPATH, "rb") as _f:
    _KEY = serialization.load_pem_private_key(_f.read(), password=None)


def _signed_get(path: str, params: dict | None = None):
    ts = str(int(time.time() * 1000))
    sig = _KEY.sign((ts + "GET" + path).encode(),
                    padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                                salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    h = {"KALSHI-ACCESS-KEY": _KEY_ID, "KALSHI-ACCESS-TIMESTAMP": ts,
         "KALSHI-ACCESS-SIGNATURE": base64.b64encode(sig).decode()}
    return _session.get(KHOST + path, headers=h, params=params, timeout=30)


def _best_book(ticker: str):
    """Signed orderbook -> (yes_bid, yes_ask) in dollars, or None if one-sided/empty."""
    r = _signed_get(f"/trade-api/v2/markets/{ticker}/orderbook")
    if r.status_code != 200:
        return None
    ob = r.json().get("orderbook_fp") or r.json().get("orderbook") or {}
    yes = ob.get("yes_dollars") or ob.get("yes") or []
    no = ob.get("no_dollars") or ob.get("no") or []
    if not yes or not no:
        return None
    yes_bid = max(float(p) for p, _ in yes)          # best (highest) YES bid
    no_bid = max(float(p) for p, _ in no)            # best NO bid -> YES ask = 1 - no_bid
    yes_ask = 1 - no_bid
    return (yes_bid, yes_ask) if yes_ask >= yes_bid else None

# in-season leagues -> (Kalshi series, Odds API sport key, Polymarket sport)
LEAGUES = {
    "MLB":  ("KXMLBGAME", "baseball_mlb", "mlb"),
    "WNBA": ("KXWNBAGAME", "basketball_wnba", "wnba"),
}
# pre-game window: record a game from 14h before to 1h after official start
WIN_BEFORE_H, WIN_AFTER_H = 14, 1


def _norm(code: str, league: str) -> str:
    return ALIASES.get(league, {}).get(code, code)


def _implied_pair(a: float, b: float) -> tuple[float, float]:
    """Normalize two positive numbers to sum to 1."""
    s = a + b
    return (round(a / s, 4), round(b / s, 4)) if s > 0 else (None, None)


def kalshi_open(series: str) -> dict:
    """event_ticker -> {code: ticker} for currently open markets."""
    out: dict = {}
    cursor = None
    while True:
        p = {"series_ticker": series, "status": "open", "limit": 1000}
        if cursor:
            p["cursor"] = cursor
        r = _session.get(f"{BASE_K}/markets", params=p, timeout=30)
        if r.status_code != 200:
            break
        d = r.json()
        for m in d.get("markets", []):
            ev, tk = m.get("event_ticker"), m.get("ticker", "")
            if ev and tk:
                out.setdefault(ev, {})[tk.rsplit("-", 1)[-1]] = tk
        cursor = d.get("cursor")
        if not cursor or not d.get("markets"):
            break
    return out


def kalshi_price(kmarkets: dict, league: str, home_abbr: str, away_abbr: str):
    """Find the matching open Kalshi event, read each side's signed book, return mids + spreads."""
    want = {_norm(home_abbr, league), _norm(away_abbr, league)}
    for ev, sides in kmarkets.items():
        codes = {_norm(c, league) for c in sides}
        if codes == want and len(sides) == 2:
            byteam = {_norm(c, league): tk for c, tk in sides.items()}
            hbook = _best_book(byteam[_norm(home_abbr, league)])
            abook = _best_book(byteam[_norm(away_abbr, league)])
            if not hbook or not abook:
                return None  # book not yet populated (fills near game time)
            hmid = (hbook[0] + hbook[1]) / 2
            amid = (abook[0] + abook[1]) / 2
            p1, p2 = _implied_pair(hmid, amid)
            return {"p1": p1, "p2": p2, "spread1": round(hbook[1] - hbook[0], 4),
                    "spread2": round(abook[1] - abook[0], 4), "raw_home_mid": round(hmid, 4)}
    return None


def odds_h2h(sport: str) -> list:
    key = os.getenv("ODDS_API_KEY")
    r = _session.get(f"{ODDS}/sports/{sport}/odds",
                     params={"apiKey": key, "regions": "us", "markets": "h2h",
                             "oddsFormat": "decimal"}, timeout=30)
    return r.json() if r.status_code == 200 else []


def book_price(odds_events: list, home: str, away: str):
    """Match by team names; average books, de-vig to implied probs (home, away)."""
    for e in odds_events:
        if e.get("home_team") == home and e.get("away_team") == away:
            hs, as_, n = 0.0, 0.0, 0
            for bk in e.get("bookmakers", []):
                mk = next((m for m in bk.get("markets", []) if m["key"] == "h2h"), None)
                if not mk:
                    continue
                px = {o["name"]: o["price"] for o in mk["outcomes"]}
                if home in px and away in px:
                    hs += 1 / px[home]; as_ += 1 / px[away]; n += 1
            if n:
                p1, p2 = _implied_pair(hs / n, as_ / n)
                return {"p1": p1, "p2": p2, "n_books": n}
    return None


def snapshot(out="data/live/snapshots.csv") -> pd.DataFrame:
    # keep aliases current (learned from the historical match data)
    learn_aliases(kalshi_games(), espn_games())
    now = dt.datetime.now(dt.timezone.utc)
    today = now.strftime("%Y%m%d")
    tomorrow = (now + dt.timedelta(days=1)).strftime("%Y%m%d")

    rows = []
    for lg, (series, sport, poly_sport) in LEAGUES.items():
        games = fetch_day(lg, today) + fetch_day(lg, tomorrow)
        kmk = kalshi_open(series)
        odds = odds_h2h(sport)
        poly = polymarket.game_prices(poly_sport)
        for g in games:
            start = pd.to_datetime(g["start_utc"], utc=True)
            mins = (start - now).total_seconds() / 60
            if not (-WIN_AFTER_H * 60 <= mins <= WIN_BEFORE_H * 60):
                continue  # outside pre-game window
            base = {"snapshot_utc": now.isoformat(), "league": lg, "game_id": g["espn_id"],
                    "start_utc": g["start_utc"], "minutes_to_start": round(mins, 1),
                    "team1": g["home_team"], "team2": g["away_team"]}
            kp = kalshi_price(kmk, lg, g["home_abbr"], g["away_abbr"])
            if kp:
                rows.append({**base, "source": "kalshi", **kp})
            bp = book_price(odds, g["home_team"], g["away_team"])
            if bp:
                rows.append({**base, "source": "sportsbook", **bp})
            pp = polymarket.price_for(poly, g["home_team"], g["away_team"])
            if pp:
                rows.append({**base, "source": "polymarket", **pp})
    df = pd.DataFrame(rows)
    if not df.empty:
        path = out
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            df = pd.concat([pd.read_csv(path), df], ignore_index=True)
        df.to_csv(path, index=False)
    return df


def backfill_outcomes(snap="data/live/snapshots.csv", out="data/live/outcomes.csv") -> int:
    """Record final results for games we've snapshotted that have since finished (ESPN)."""
    if not os.path.exists(snap):
        return 0
    games = (pd.read_csv(snap)[["game_id", "league", "start_utc", "team1", "team2"]]
             .drop_duplicates("game_id"))
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    now = dt.datetime.now(dt.timezone.utc)
    games = games[~games["game_id"].isin(done)].copy()
    games["start"] = pd.to_datetime(games["start_utc"], utc=True)
    games = games[games["start"] < now - dt.timedelta(hours=2)]  # likely finished
    if games.empty:
        return 0
    rows = []
    for (lg, date), grp in games.groupby(["league", games["start"].dt.strftime("%Y%m%d")]):
        # ESPN ids are strings; game_id read from CSV is an int -> compare as str.
        # Also query the prior day: late games roll into the next UTC date.
        prev = (dt.datetime.strptime(date, "%Y%m%d") - dt.timedelta(days=1)).strftime("%Y%m%d")
        espn = {str(e["espn_id"]): e for d_ in (date, prev) for e in fetch_day(lg, d_)}
        for r in grp.itertuples(index=False):
            e = espn.get(str(r.game_id))
            if e and e["status"] == "STATUS_FINAL" and e["winner"]:
                rows.append({"game_id": r.game_id, "league": lg, "team1": r.team1,
                             "team2": r.team2, "home_score": e["home_score"],
                             "away_score": e["away_score"],
                             "outcome": 1 if e["winner"] == "home" else 2})
    if rows:
        df = pd.DataFrame(rows)
        if os.path.exists(out):
            df = pd.concat([pd.read_csv(out), df], ignore_index=True)
        df.to_csv(out, index=False)
    return len(rows)


if __name__ == "__main__":
    n = backfill_outcomes()
    if n:
        print(f"recorded outcomes for {n} finished game(s)")
    df = snapshot()
    if df.empty:
        print("no games in pre-game window right now")
    else:
        latest = df[df["snapshot_utc"] == df["snapshot_utc"].max()]
        print(f"snapshot rows this run: {len(latest)}")
        piv = latest.pivot_table(index=["league", "team1", "team2", "minutes_to_start"],
                                 columns="source", values=["p1", "p2"], aggfunc="first")
        print(piv.to_string())
