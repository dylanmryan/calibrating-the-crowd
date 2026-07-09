"""Kalshi collector: settled game-outcome markets across major leagues.

Market-data reads need no auth. Kalshi splits data into a live tier and a
historical tier at a rolling boundary (/historical/cutoff); this module queries
BOTH endpoints and merges by ticker so nothing is missed as the boundary moves.

Inventory step only: produces one row per market SIDE with its settlement
outcome. Pre-game implied probabilities are added later from candlesticks
(see fetch_close_price), since the bulk market objects only carry end-state prices.
"""
from __future__ import annotations

import time
import pandas as pd
import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"

# Game-outcome series (which team wins) per major league.
LEAGUE_SERIES = {
    "NBA":   "KXNBAGAME",
    "NFL":   "KXNFLGAME",
    "MLB":   "KXMLBGAME",
    "NHL":   "KXNHLGAME",
    "WNBA":  "KXWNBAGAME",
    "CFB":   "KXNCAAFGAME",
    "CBB-M": "KXNCAAMBGAME",
}

_session = requests.Session()


def get(path: str, params: dict | None = None, retries: int = 3) -> dict:
    """GET with light retry/backoff on transient errors and rate limits."""
    for attempt in range(retries):
        r = _session.get(f"{BASE}{path}", params=params, timeout=45)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503):
            time.sleep(1.5 * (attempt + 1))
            continue
        r.raise_for_status()
    r.raise_for_status()
    return {}


def fetch_cutoff() -> str:
    """The current live/historical boundary (market_settled_ts)."""
    return get("/historical/cutoff").get("market_settled_ts", "")


def _paginate(endpoint: str, series_ticker: str, cap: int) -> list[dict]:
    out: list[dict] = []
    cursor = None
    while len(out) < cap:
        params = {"series_ticker": series_ticker, "limit": 1000, "status": "settled"}
        if cursor:
            params["cursor"] = cursor
        data = get(f"/{endpoint}", params)
        markets = data.get("markets", [])
        out.extend(markets)
        cursor = data.get("cursor")
        if not cursor or not markets:
            break
    return out


def fetch_settled_markets(series_ticker: str, cap: int = 40000) -> list[dict]:
    """All settled markets for a series, merging historical + live tiers by ticker."""
    merged = {m["ticker"]: m for m in _paginate("historical/markets", series_ticker, cap)}
    merged.update({m["ticker"]: m for m in _paginate("markets", series_ticker, cap)})
    return list(merged.values())


def market_to_row(m: dict, league: str) -> dict | None:
    """One market SIDE -> tidy row. Outcome from `result` (yes/no); None if unresolved."""
    result = m.get("result")
    if result not in ("yes", "no"):
        return None  # skip voided/pushed/unsettled
    return {
        "league": league,
        "event_ticker": m.get("event_ticker"),
        "ticker": m.get("ticker"),
        "team": m.get("yes_sub_title"),      # the YES side's team
        "title": m.get("title"),
        "won": 1 if result == "yes" else 0,  # did this side win
        "occurrence_datetime": m.get("occurrence_datetime"),  # game start (None pre-cutoff)
        "close_time": m.get("close_time"),   # market close (~game end)
        "series_ticker": m.get("ticker", "").split("-")[0],
    }


def collect(leagues: list[str] | None = None) -> pd.DataFrame:
    """Inventory settled game markets across leagues -> per-side DataFrame with outcomes."""
    leagues = leagues or list(LEAGUE_SERIES)
    cutoff = fetch_cutoff()
    print(f"live/historical cutoff: {cutoff}", flush=True)
    rows: list[dict] = []
    for lg in leagues:
        st = LEAGUE_SERIES[lg]
        markets = fetch_settled_markets(st)
        kept = [r for m in markets if (r := market_to_row(m, lg))]
        rows.extend(kept)
        print(f"  {lg:6} {st:16} markets={len(markets):6}  resolved sides={len(kept):6}", flush=True)
    df = pd.DataFrame(rows)
    # derive a game date from close_time (UTC date; refined later against game start).
    # format="ISO8601" handles both Kalshi timestamp variants (with/without fractional
    # seconds); the default parser in pandas 3.0 is strict and NaTs the odd one out.
    df["date"] = pd.to_datetime(df["close_time"], utc=True, format="ISO8601").dt.date
    return df


if __name__ == "__main__":
    df = collect()
    out = "data/processed/kalshi_settled_markets.csv"
    df.to_csv(out, index=False)
    print(f"\nsaved {len(df):,} rows -> {out}", flush=True)
    print(f"unique games (event_ticker): {df['event_ticker'].nunique():,}", flush=True)
    print(df.groupby("league").agg(sides=("ticker", "size"),
                                    games=("event_ticker", "nunique"),
                                    win_rate=("won", "mean")).to_string(), flush=True)
