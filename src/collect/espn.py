"""ESPN scoreboard collector: official start times, teams, and final scores.

ESPN's public scoreboard API uses one consistent shape across sports, giving us
three things per game: the official start time (UTC) used as the price-sampling
reference, team names/abbreviations for matching to Kalshi, and final scores for
an independent outcome cross-check against Kalshi's settlements.

We only query dates where our Kalshi data has games, to avoid ~440 blind days.
"""
from __future__ import annotations

import time
import pandas as pd
import requests

# Map our league labels -> ESPN sport/league path.
LEAGUE_PATH = {
    "NBA":   "basketball/nba",
    "NFL":   "football/nfl",
    "MLB":   "baseball/mlb",
    "NHL":   "hockey/nhl",
    "WNBA":  "basketball/wnba",
    "CFB":   "football/college-football",
    "CBB-M": "basketball/mens-college-basketball",
    "WC":    "soccer/fifa.world",
}

_session = requests.Session()


def fetch_day(league: str, yyyymmdd: str, retries: int = 3) -> list[dict]:
    """All games for one league on one date -> tidy rows."""
    url = f"https://site.api.espn.com/apis/site/v2/sports/{LEAGUE_PATH[league]}/scoreboard"
    for attempt in range(retries):
        r = _session.get(url, params={"dates": yyyymmdd, "limit": 400}, timeout=30)
        if r.status_code == 200:
            break
        time.sleep(1.0 * (attempt + 1))
    else:
        return []
    rows = []
    for e in r.json().get("events", []):
        comp = e["competitions"][0]
        by_side = {c["homeAway"]: c for c in comp["competitors"]}
        home, away = by_side.get("home"), by_side.get("away")
        if not (home and away):
            continue
        hs = _to_int(home.get("score"))
        as_ = _to_int(away.get("score"))
        winner = None
        if hs is not None and as_ is not None and hs != as_:
            winner = "home" if hs > as_ else "away"
        rows.append({
            "league": league,
            "espn_id": e.get("id"),
            "start_utc": e.get("date"),          # official start, UTC
            "date": yyyymmdd,
            "home_team": home["team"]["displayName"],
            "away_team": away["team"]["displayName"],
            "home_abbr": home["team"].get("abbreviation"),
            "away_abbr": away["team"].get("abbreviation"),
            "home_score": hs,
            "away_score": as_,
            "winner": winner,
            "status": e["status"]["type"]["name"],
            # 1=preseason, 2=regular season, 3=postseason (ESPN convention)
            "season_type": (e.get("season") or {}).get("type"),
        })
    return rows


def _to_int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def collect(kalshi_csv: str = "data/processed/kalshi_settled_markets.csv") -> pd.DataFrame:
    """Pull ESPN games for every (league, date) present in the Kalshi dataset."""
    k = pd.read_csv(kalshi_csv)
    # ISO8601 handles both Kalshi timestamp variants (with/without fractional seconds).
    k["date"] = pd.to_datetime(k["close_time"], utc=True, format="ISO8601").dt.date
    k = k.dropna(subset=["date"])
    # Kalshi close_time is UTC and often the day AFTER a US evening game; query the
    # close date and the day before to be safe against the tip-off/close date shift.
    pairs = set()
    for lg, d in k[["league", "date"]].drop_duplicates().itertuples(index=False):
        for delta in (0, -1):
            day = (pd.Timestamp(d) + pd.Timedelta(days=delta)).strftime("%Y%m%d")
            pairs.add((lg, day))

    rows, done = [], 0
    total = len(pairs)
    for lg, day in sorted(pairs):
        rows.extend(fetch_day(lg, day))
        done += 1
        if done % 200 == 0:
            print(f"  {done}/{total} day-queries done, {len(rows)} games so far", flush=True)
    df = pd.DataFrame(rows).drop_duplicates(subset=["espn_id"])
    return df


if __name__ == "__main__":
    df = collect()
    out = "data/processed/espn_games.csv"
    df.to_csv(out, index=False)
    print(f"\nsaved {len(df):,} ESPN games -> {out}", flush=True)
    print(df.groupby("league").agg(games=("espn_id", "size"),
                                    finals=("status", lambda s: (s == "STATUS_FINAL").sum())).to_string(), flush=True)
