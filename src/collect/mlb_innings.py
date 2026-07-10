"""Fetch innings played per MLB game (ESPN scoreboard `status.period`).

The scoreboard events we already collect carry the final period count — for MLB
that is innings (9 = regulation, >9 = extras) — but espn.py never stored it.
Extras matter for the margin-distribution work: walk-off endings and the placed
ghost runner concentrate extra-inning finals at a margin of exactly 1, the cell
the run-line autopsy found under-priced. One free scoreboard call per MLB date.
"""
from __future__ import annotations

import time
import pandas as pd

from src.collect.espn import LEAGUE_PATH, _session

OUT = "data/processed/mlb_innings.csv"


def fetch_day_periods(yyyymmdd: str, retries: int = 3) -> list[dict]:
    url = f"https://site.api.espn.com/apis/site/v2/sports/{LEAGUE_PATH['MLB']}/scoreboard"
    for attempt in range(retries):
        r = _session.get(url, params={"dates": yyyymmdd, "limit": 400}, timeout=30)
        if r.status_code == 200:
            break
        time.sleep(1.0 * (attempt + 1))
    else:
        return []
    rows = []
    for e in r.json().get("events", []):
        st = e.get("status", {})
        if st.get("type", {}).get("name") != "STATUS_FINAL":
            continue
        rows.append({"game_id": int(e["id"]), "date": yyyymmdd,
                     "innings": int(st.get("period") or 0)})
    return rows


def build(out: str = OUT) -> None:
    esp = pd.read_csv("data/processed/espn_games.csv")
    days = sorted(esp[(esp.league == "MLB") & (esp.status == "STATUS_FINAL")]["date"]
                  .astype(int).astype(str).unique())
    rows = []
    for i, day in enumerate(days, 1):
        rows.extend(fetch_day_periods(day))
        if i % 50 == 0:
            print(f"  {i}/{len(days)} dates, {len(rows)} games", flush=True)
    df = pd.DataFrame(rows).drop_duplicates(subset=["game_id"])
    df.to_csv(out, index=False)
    print(f"saved {len(df):,} MLB games with innings -> {out}", flush=True)
    print(df.innings.value_counts().sort_index().to_string(), flush=True)


if __name__ == "__main__":
    build()
