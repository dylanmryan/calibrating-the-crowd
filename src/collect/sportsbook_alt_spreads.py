"""Historical sportsbook ALTERNATE spread lines for MLB + NBA ladder games.

Completes the proposal's layer 3 cross-source: Kalshi's alternate-spread ladders
(threshold contracts at 2.5/3.5/4.5...) vs the books' alternate spread lines at
the same margins — do the books also under-price 1-2-run MLB margins, or is the
walk-off blind spot Kalshi-specific?

Cost model (paid credits, user-approved ~27K on 2026-07-10):
  - /historical/.../events        1 credit per (league, 30-min start bucket)
  - /historical/.../events/{id}/odds?markets=alternate_spreads  10 credits/game
Targets: clean-master games that have a Kalshi ladder (~2,560). Resumable; hard
stop when x-requests-remaining drops below CREDIT_FLOOR.
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
KEY = os.getenv("ODDS_API_KEY")
BASE = "https://api.the-odds-api.com/v4"
OUT = "data/processed/sportsbook_alt_spreads.csv"
CREDIT_FLOOR = 12_000     # live-feed reserve through the Aug 24 project end
_session = requests.Session()
_remaining = [None]


def _get(url, params, retries=3):
    for attempt in range(retries):
        r = _session.get(url, params={"apiKey": KEY, **params}, timeout=30)
        rem = r.headers.get("x-requests-remaining")
        if rem is not None:
            _remaining[0] = float(rem)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503):
            time.sleep(1.5 * (attempt + 1))
        else:
            return None
    return None


def targets():
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    m = pd.read_csv("data/processed/games_master.csv")
    m = m[m.outcome.notna() & ~m.outcome_disagree.fillna(False)]
    m = m[m.league.isin(("MLB", "NBA", "NHL")) & m.game_id.isin(sp.game_id)].copy()
    m["start"] = pd.to_datetime(m["start_utc"], utc=True, format="ISO8601")
    m["bucket"] = m["start"].dt.floor("30min")
    return m


def _consensus_alt(game_obj, home, away):
    """alternate_spreads -> rows of (side, point, prob_raw, prob devig, n_books)."""
    from collections import defaultdict
    pair = defaultdict(list)    # (home_point) -> list of (imp_home, imp_away) per book
    for bk in game_obj.get("bookmakers", []):
        mk = next((m for m in bk.get("markets", []) if m["key"] == "alternate_spreads"), None)
        if not mk:
            continue
        px = {}
        for o in mk["outcomes"]:
            if o.get("point") is None or not o.get("price") or o["price"] <= 1:
                continue
            px[(o["name"], float(o["point"]))] = 1.0 / float(o["price"])
        for (name, pt), imp_h in list(px.items()):
            if name != home:
                continue
            imp_a = px.get((away, -pt))
            if imp_a:
                pair[pt].append((imp_h, imp_a))
    rows = []
    for pt, obs in pair.items():
        ph = [h / (h + a) for h, a in obs]
        rh = [h for h, _ in obs]
        rows.append({"point": pt, "prob_home": sum(ph) / len(ph),
                     "raw_home": sum(rh) / len(rh), "n_books": len(obs)})
    return rows


def build(out=OUT, flush_every=100, max_games=None):
    m = targets()
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    m = m[~m.game_id.isin(done)]
    if max_games:
        m = m.head(max_games)
    print(f"target games: {len(m):,} ({len(done)} done)  credit floor {CREDIT_FLOOR:,}", flush=True)
    rows, odds_calls = [], 0
    for (lg, bucket), grp in m.groupby(["league", "bucket"]):
        if _remaining[0] is not None and _remaining[0] < CREDIT_FLOOR:
            print(f"CREDIT FLOOR reached ({_remaining[0]:,.0f} remaining) — stopping", flush=True)
            break
        iso = bucket.strftime("%Y-%m-%dT%H:%M:%SZ")
        ev = _get(f"{BASE}/historical/sports/{SPORT[lg]}/events", {"date": iso})
        events = (ev or {}).get("data", [])
        for g in grp.itertuples(index=False):
            home, away = str(g.team1).lower(), str(g.team2).lower()
            best = None
            for sg in events:
                ct = pd.Timestamp(sg.get("commence_time"))
                if abs((ct - g.start).total_seconds()) > 3 * 3600:
                    continue
                if _match_hit(home, sg.get("home_team", "")) and _match_hit(away, sg.get("away_team", "")):
                    best = sg
                    break
            if not best:
                continue
            od = _get(f"{BASE}/historical/sports/{SPORT[lg]}/events/{best['id']}/odds",
                      {"date": iso, "regions": "us", "markets": "alternate_spreads",
                       "oddsFormat": "decimal"})
            odds_calls += 1
            data = (od or {}).get("data")
            if not data:
                continue
            for r in _consensus_alt(data, best["home_team"], best["away_team"]):
                rows.append({"game_id": g.game_id, "league": lg, "start_utc": g.start_utc,
                             "team1": g.team1, "team2": g.team2, **{k: round(v, 4) if isinstance(v, float) else v
                                                                     for k, v in r.items()}})
        if len(rows) >= flush_every:
            _append(out, rows); rows = []
            print(f"  ...{odds_calls} odds calls, remaining credits ~{_remaining[0]:,.0f}", flush=True)
    if rows:
        _append(out, rows)
    print(f"done: {odds_calls} odds calls, remaining credits ~{_remaining[0]:,.0f}", flush=True)


def _append(path, rows):
    df = pd.DataFrame(rows)
    if os.path.exists(path):
        df = pd.concat([pd.read_csv(path), df], ignore_index=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    import sys
    build(max_games=int(sys.argv[1]) if len(sys.argv) > 1 else None)
