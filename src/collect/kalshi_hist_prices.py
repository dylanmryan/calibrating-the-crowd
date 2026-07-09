"""Unified Kalshi historical pricing -> one row per game with home/away closing probs.

Per side, at the official ESPN start time:
  - book-mid   : 1-min candlestick (yes_bid+yes_ask)/2   [recent, post-cutoff]
  - trade-recon: /historical/trades + max_ts, effective bid/ask from taker_side  [older]
The two sides are normalized to sum to 1. Resumable: skips games already priced.
"""
from __future__ import annotations

import os
import datetime as dt
import pandas as pd
import requests

from src.collect.kalshi_prices import closing_book_price, BASE
from src.match.kalshi_espn import kalshi_games, espn_games, learn_aliases, ALIASES

_session = requests.Session()


def _norm(code: str, league: str) -> str:
    return ALIASES.get(league, {}).get(code, code)


def _rule_home(event_ticker: str, codes) -> str | None:
    """Home code from ticker order: the event pair suffix ends with the home code."""
    import re
    m = re.match(r"KX[A-Z0-9]+-(?:\d{2}[A-Z]{3}\d{2})(?:\d{4})?([A-Z]+)$", event_ticker)
    if not m:
        return None
    ends = [c for c in codes if m.group(1).endswith(c)]
    return ends[0] if len(ends) == 1 else None


def closing_trade_price(ticker: str, start_utc: str, lookback: int = 300) -> dict | None:
    """Reconstruct the closing book-mid from trades at/before official start."""
    import time
    start = dt.datetime.fromisoformat(str(start_utc).replace("Z", "+00:00"))
    end = int(start.timestamp())
    r = None
    for attempt in range(3):
        try:
            r = _session.get(f"{BASE}/historical/trades",
                             params={"ticker": ticker, "max_ts": end, "limit": lookback}, timeout=30)
            break
        except requests.RequestException:  # dropped connection -> back off, retry
            time.sleep(3.0 * (attempt + 1))
    if r is None or r.status_code != 200:
        return None
    tr = r.json().get("trades", [])
    if not tr:
        return None
    tr.sort(key=lambda t: t["created_time"], reverse=True)  # newest first

    def px(t):
        return float(t["yes_price_dollars"])
    last = px(tr[0])
    newest_ts = pd.to_datetime(tr[0]["created_time"]).timestamp()
    ask = next((px(t) for t in tr if t.get("taker_side") == "yes"), None)  # yes-buy hits ask
    bid = next((px(t) for t in tr if t.get("taker_side") == "no"), None)   # yes-sell hits bid
    if bid is not None and ask is not None and ask >= bid:
        mid, spread = (bid + ask) / 2, ask - bid
    else:
        mid, spread, bid, ask = last, None, None, None
    return {"mid": round(mid, 4), "yes_bid": bid, "yes_ask": ask,
            "spread": round(spread, 4) if spread is not None else None,
            "staleness_min": round((end - newest_ts) / 60, 1), "source": "trade-recon"}


def price_side(ticker: str, series: str, start_utc: str) -> dict | None:
    b = closing_book_price(ticker, series, start_utc)
    if b:
        return {"mid": b["mid"], "yes_bid": b["yes_bid"], "yes_ask": b["yes_ask"],
                "spread": b["spread"], "staleness_min": b["staleness_min"], "source": "book-mid"}
    return closing_trade_price(ticker, start_utc)


def build(out="data/processed/kalshi_hist_prices.csv", limit: int | None = None,
          flush_every: int = 100) -> None:
    m = pd.read_csv("data/processed/kalshi_espn_matches.csv")
    m = m[m.matched & m.start_utc.notna()].copy()
    esp = espn_games().set_index("espn_id")
    kal = pd.read_csv("data/processed/kalshi_settled_markets.csv")
    kal["code"] = kal["ticker"].str.rsplit("-", n=1).str[-1]
    learn_aliases(kalshi_games(), espn_games())

    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    todo = m[~m["espn_id"].isin(done)]
    if limit:
        todo = todo.head(limit)
    print(f"pricing {len(todo)} games ({len(done)} already done)", flush=True)

    rows, n = [], 0
    for r in todo.itertuples(index=False):
        if r.espn_id not in esp.index:
            continue
        e = esp.loc[r.espn_id]
        sides = list(kal[kal.event_ticker == r.event_ticker].itertuples(index=False))
        codes = sorted({s.code for s in sides})
        if len(codes) != 2:
            continue
        # side assignment by TICKER ORDER (event pair ends with the home code) —
        # validated at 99.6% vs ESPN; immune to the alias collisions that produced
        # same-ticker/flipped pricing. Alias mapping is only a fallback.
        rh = _rule_home(r.event_ticker, codes)
        if rh is not None:
            hside = next(s for s in sides if s.code == rh)
            aside = next(s for s in sides if s.code != rh)
        else:
            home, away = _norm(str(e.home_abbr), r.league), _norm(str(e.away_abbr), r.league)
            byteam = {_norm(s.code, r.league): s for s in sides}
            if home == away or home not in byteam or away not in byteam:
                continue
            hside, aside = byteam[home], byteam[away]
        ph = price_side(hside.ticker, hside.series_ticker, r.start_utc)
        pa = price_side(aside.ticker, aside.series_ticker, r.start_utc)
        n += 1
        if not ph or not pa:
            continue
        s = ph["mid"] + pa["mid"]
        if s <= 0:
            continue
        rows.append({
            "game_id": r.espn_id, "league": r.league, "date": r.date, "start_utc": r.start_utc,
            "team1": e.home_team, "team2": e.away_team,
            "kalshi_p1": round(ph["mid"] / s, 4), "kalshi_p2": round(pa["mid"] / s, 4),
            # raw quotes per side (un-normalized); no_bid=1-yes_ask, no_ask=1-yes_bid
            "k_yes_bid1": ph["yes_bid"], "k_yes_ask1": ph["yes_ask"],
            "k_yes_bid2": pa["yes_bid"], "k_yes_ask2": pa["yes_ask"],
            "k_src1": ph["source"], "k_src2": pa["source"],
            "k_spread1": ph["spread"], "k_spread2": pa["spread"],
            "k_stale1": ph["staleness_min"], "k_stale2": pa["staleness_min"],
        })
        if len(rows) >= flush_every:
            _append(out, rows); rows = []
            print(f"  ...{n} processed, flushed", flush=True)
    if rows:
        _append(out, rows)
    print(f"done: processed {n} games", flush=True)


def _append(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(rows)
    if os.path.exists(path):
        df = pd.concat([pd.read_csv(path), df], ignore_index=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    import sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    build(limit=lim)
