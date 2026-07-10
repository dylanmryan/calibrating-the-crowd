"""Per-fill Kalshi trade harvest (final 24h before start) for a game sample.

Feeds the informed-trading test: per trade we get size (count), price, and
taker_side — enough to ask whether large trades are the informed ones. Free,
unauthenticated endpoint; ~2-4 requests per game.
"""
from __future__ import annotations

import os
import time
import pandas as pd
import requests

from src.collect.kalshi_prices import BASE
from src.collect.kalshi_hist_prices import _rule_home

OUT = "data/processed/kalshi_trades_24h.csv"
_session = requests.Session()


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def sample_games(n_per_league=80):
    m = pd.read_csv("data/processed/games_master.csv")
    m = m[m.kalshi_p1.notna() & m.outcome.notna() & ~m.outcome_disagree.fillna(False)]
    mt = pd.read_csv("data/processed/kalshi_espn_matches.csv")[["espn_id", "event_ticker"]]
    kk = pd.read_csv("data/processed/kalshi_settled_markets.csv")[["event_ticker", "ticker"]]
    m = m.merge(mt.rename(columns={"espn_id": "game_id"}), on="game_id")
    rows = []
    for r in m.itertuples(index=False):
        sides = kk[kk.event_ticker == r.event_ticker]["ticker"].tolist()
        codes = sorted({t.rsplit("-", 1)[-1] for t in sides})
        rh = _rule_home(r.event_ticker, codes) if len(codes) == 2 else None
        if rh is None:
            continue
        tk = next((t for t in sides if t.endswith("-" + rh)), None)
        if tk:
            rows.append({"game_id": r.game_id, "league": r.league, "ticker": tk,
                         "start_utc": r.start_utc, "outcome": r.outcome,
                         "book_p1": r.book_p1, "kalshi_p1": r.kalshi_p1})
    df = pd.DataFrame(rows)
    return df.sample(frac=1, random_state=7).groupby("league").head(n_per_league)


def fetch_trades(ticker: str, start_utc: str, window_h: int = 24) -> list[dict]:
    """/historical/trades covers all eras (live /markets/trades only ~60 days).
    Pages newest-first from max_ts; stops once past the window's lower edge."""
    end = int(pd.Timestamp(start_utc).timestamp())
    lo_ts = end - window_h * 3600
    lo_iso = pd.Timestamp(lo_ts, unit="s", tz="UTC").strftime("%Y-%m-%dT%H:%M:%S")
    out, cursor = [], None
    for _ in range(20):
        params = {"ticker": ticker, "limit": 1000, "max_ts": end}
        if cursor:
            params["cursor"] = cursor
        r = _session.get(f"{BASE}/historical/trades", params=params, timeout=25)
        if r.status_code != 200:
            time.sleep(1.0)
            continue
        j = r.json()
        page = j.get("trades", [])
        out.extend(t for t in page if (t.get("created_time") or "") >= lo_iso)
        cursor = j.get("cursor")
        if not cursor or (page and (page[-1].get("created_time") or "") < lo_iso):
            break
        time.sleep(0.15)
    return out


def build(out=OUT, n_per_league=80):
    todo = sample_games(n_per_league)
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    todo = todo[~todo.game_id.isin(done)]
    print(f"harvesting trades for {len(todo)} games ({len(done)} done)", flush=True)
    rows, n = [], 0
    for g in todo.itertuples(index=False):
        for t in fetch_trades(g.ticker, g.start_utc):
            rows.append({"game_id": g.game_id, "league": g.league,
                         "start_utc": g.start_utc, "outcome": g.outcome,
                         "book_p1": g.book_p1, "kalshi_p1": g.kalshi_p1,
                         "created_time": t.get("created_time"),
                         # API v2 fields: yes_price_dollars (string $), count_fp (string contracts)
                         "yes_price": _f(t.get("yes_price_dollars")) or _f(t.get("yes_price")),
                         "count": _f(t.get("count_fp")) or _f(t.get("count")),
                         "taker_side": t.get("taker_side")})
        n += 1
        if n % 50 == 0:
            _flush(out, rows); rows = []
            print(f"  ...{n} games", flush=True)
        time.sleep(0.15)
    _flush(out, rows)
    print(f"done: {n} games", flush=True)


def _flush(path, rows):
    if not rows:
        return
    df = pd.DataFrame(rows)
    if os.path.exists(path):
        df = pd.concat([pd.read_csv(path), df], ignore_index=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    build()
