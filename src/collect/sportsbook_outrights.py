"""Sportsbook championship-winner (outright) odds: the books' own futures.

The futures leg shows exchange outrights are miscalibrated where game
markets are clean. The open question: are the BOOKS any better on the same
kind of market? If books also misprice outrights, the pathology is about
long-horizon one-shot markets generally, not exchange design. Also
measures the books' outright overrounds directly (literature says 1.2-1.6;
exchanges run 1.03) — per book, Pinnacle included via the EU region.

Monthly in-season snapshots across three resolved seasons per sport
(2023-24 .. 2025-26; MLB 2023-2025), us+eu regions, ~20 credits/snapshot,
~1.9K total (within the 2026-08-04 envelope). Champions are resolved in
the analysis step, not here. Output: data/processed/sportsbook_outrights.csv
(one row per snapshot-book-team).
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env", override=True)
BASE = "https://api.the-odds-api.com/v4"
KEY = os.getenv("ODDS_API_KEY")
OUT = "data/processed/sportsbook_outrights.csv"
_session = requests.Session()

SEASONS = {
    "basketball_nba_championship_winner":
        [f"{y}-{m:02d}" for y in (2020, 2021, 2022, 2023, 2024, 2025) for m in (10, 11, 12)] +
        [f"{y}-{m:02d}" for y in (2021, 2022, 2023, 2024, 2025, 2026) for m in (1, 2, 3, 4, 5, 6)] +
        ["2021-07"],
    "americanfootball_nfl_super_bowl_winner":
        [f"{y}-{m:02d}" for y in (2020, 2021, 2022, 2023, 2024, 2025) for m in (9, 10, 11, 12)] +
        [f"{y}-{m:02d}" for y in (2021, 2022, 2023, 2024, 2025, 2026) for m in (1, 2)],
    "baseball_mlb_world_series_winner":
        [f"{y}-{m:02d}" for y in (2021, 2022, 2023, 2024, 2025) for m in (4, 5, 6, 7, 8, 9, 10)] +
        ["2020-08", "2020-09", "2020-10"],
    "icehockey_nhl_championship_winner":
        [f"{y}-{m:02d}" for y in (2020, 2021, 2022, 2023, 2024, 2025) for m in (10, 11, 12)] +
        [f"{y}-{m:02d}" for y in (2021, 2022, 2023, 2024, 2025, 2026) for m in (1, 2, 3, 4, 5, 6)] +
        ["2021-07"],
}


def build(out=OUT):
    done = set()
    if os.path.exists(out):
        prev = pd.read_csv(out)
        done = set(zip(prev.sport, prev.snap))
    rows, calls = [], 0
    for sk, months in SEASONS.items():
        for ym in months:
            if (sk, ym) in done:
                continue
            date = f"{ym}-01T12:00:00Z"
            r = _session.get(f"{BASE}/historical/sports/{sk}/odds", params={
                "apiKey": KEY, "regions": "us,eu", "markets": "outrights",
                "oddsFormat": "decimal", "date": date}, timeout=30)
            calls += 1
            if r.status_code != 200:
                time.sleep(1)
                continue
            for g in r.json().get("data", []):
                for bk in g.get("bookmakers", []):
                    mk = next((m for m in bk.get("markets", [])
                               if m["key"] == "outrights"), None)
                    if not mk:
                        continue
                    for o in mk.get("outcomes", []):
                        if o.get("price", 0) > 1:
                            rows.append({"sport": sk, "snap": ym, "book": bk["key"],
                                         "team": o["name"], "raw_p": 1 / o["price"]})
            if calls % 20 == 0:
                print(f"  {calls} snapshots (~{calls*20} credits)", flush=True)
    if rows:
        pd.DataFrame(rows).to_csv(out, mode="a", header=not os.path.exists(out),
                                  index=False)
    print(f"done: {calls} snapshot calls (~{calls*20} credits) -> {out}", flush=True)


if __name__ == "__main__":
    build()
