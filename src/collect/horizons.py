"""Multi-horizon Kalshi prices: the home side's last-trade price at T-24h ... T-0.

One /historical/trades call per game (home ticker, max_ts=start, up to 1000 fills)
gives the pre-game price path; we sample it at fixed horizons. Tests whether the
market SHARPENS as the event approaches — the signature of genuine information
aggregation (Page & Clemen 2013), vs. static/noisy gambling odds.
"""
from __future__ import annotations

import os
import time
import datetime as dt
import pandas as pd
import requests

from src.collect.kalshi_prices import BASE
from src.collect.kalshi_hist_prices import _rule_home

HORIZONS_MIN = [24 * 60, 12 * 60, 6 * 60, 3 * 60, 60, 15, 0]
_session = requests.Session()


def _trades(ticker: str, max_ts: int, retries: int = 3) -> list:
    out, cursor = [], None
    for _page in range(2):  # up to 2000 fills reaches ~24h back for most games
        p = {"ticker": ticker, "max_ts": max_ts, "limit": 1000}
        if cursor:
            p["cursor"] = cursor
        for attempt in range(retries):
            try:
                r = _session.get(f"{BASE}/historical/trades", params=p, timeout=30)
                break
            except requests.RequestException:
                time.sleep(3.0 * (attempt + 1))
        else:
            return out
        if r.status_code != 200:
            return out
        d = r.json()
        tr = d.get("trades", [])
        out += tr
        cursor = d.get("cursor")
        if not cursor or not tr:
            break
    return out


def home_ticker_map() -> pd.DataFrame:
    """game_id -> home-side Kalshi ticker via the validated ticker-order rule."""
    mt = pd.read_csv("data/processed/kalshi_espn_matches.csv")
    mt = mt[mt.matched & mt.start_utc.notna()]
    kk = pd.read_csv("data/processed/kalshi_settled_markets.csv")
    kk["code"] = kk["ticker"].str.rsplit("-", n=1).str[-1]
    rows = []
    for ev, g in kk.groupby("event_ticker"):
        codes = sorted(set(g["code"]))
        if len(codes) != 2:
            continue
        rh = _rule_home(ev, codes)
        if rh is None:
            continue
        rows.append({"event_ticker": ev,
                     "home_tk": g[g["code"] == rh]["ticker"].iloc[0]})
    return mt.merge(pd.DataFrame(rows), on="event_ticker")[
        ["espn_id", "league", "start_utc", "home_tk"]].rename(columns={"espn_id": "game_id"})


def build(out="data/processed/kalshi_horizons.csv", flush_every=200) -> None:
    m = pd.read_csv("data/processed/games_master.csv")
    m = m[m["outcome"].notna() & ~m["outcome_disagree"].fillna(False) & m["kalshi_p1"].notna()]
    tk = home_ticker_map()
    todo = m[["game_id", "outcome"]].merge(tk, on="game_id")
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    todo = todo[~todo["game_id"].isin(done)]
    print(f"sampling horizons for {len(todo)} games ({len(done)} done)", flush=True)

    rows, n = [], 0
    for r in todo.itertuples(index=False):
        start = int(pd.Timestamp(r.start_utc).timestamp())
        tr = _trades(r.home_tk, start)
        if not tr:
            continue
        # ascending time series of (epoch, yes_price)
        ser = sorted((int(pd.Timestamp(t["created_time"]).timestamp()),
                      float(t["yes_price_dollars"])) for t in tr)
        row = {"game_id": r.game_id, "league": r.league, "start_utc": r.start_utc,
               "home_won": int(r.outcome == 1), "n_trades": len(ser),
               "earliest_min": round((start - ser[0][0]) / 60)}
        for hmin in HORIZONS_MIN:
            cut = start - hmin * 60
            past = [p for ts, p in ser if ts <= cut]
            row[f"p_h{hmin}"] = past[-1] if past else None
        rows.append(row)
        n += 1
        if len(rows) >= flush_every:
            _append(out, rows); rows = []
            print(f"  ...{n}", flush=True)
    if rows:
        _append(out, rows)
    print(f"done: {n} games -> {out}", flush=True)


def _append(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(rows)
    if os.path.exists(path):
        df = pd.concat([pd.read_csv(path), df], ignore_index=True)
    # audit gate: later harvests supersede older rows for the same game
    df = df.drop_duplicates("game_id", keep="last")
    df.to_csv(path, index=False)


if __name__ == "__main__":
    build()
