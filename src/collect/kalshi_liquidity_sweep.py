"""Point-in-time sweep of the whole exchange's resting liquidity.

Which markets does the liquidity-provision complex (affiliate + Market
Maker Agreement firms + incentive-program participants) actually stand
in? Member IDs are private, but the FOOTPRINT is public: every market
object carries `liquidity_dollars` (notional value of resting orders),
and every series carries `fee_type` / `fee_multiplier` (who pays makers'
fees, set by the exchange per product). One unsigned paginated sweep of
all open markets = the liquidity landscape of the exchange on this date,
joinable to our market classes (covered games / niche games / outrights).

Output: data/processed/kalshi_liquidity_sweep.csv (one row per open
market) + kalshi_series_fees.csv (one row per series). Point-in-time:
stamped with the sweep date, not meant to be resumed or merged.
"""
from __future__ import annotations

import time

import pandas as pd
import requests

B = "https://api.elections.kalshi.com/trade-api/v2"
OUT = "data/processed/kalshi_liquidity_sweep.csv"
FEES = "data/processed/kalshi_series_fees.csv"
_session = requests.Session()


def sweep_markets(sweep_date: str):
    rows, cursor, pages = [], None, 0
    while True:
        params = {"status": "open", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        r = _session.get(f"{B}/markets", params=params, timeout=30)
        if r.status_code != 200:
            time.sleep(2)
            continue
        j = r.json()
        for m in j.get("markets", []):
            ev = m.get("event_ticker") or ""
            rows.append({
                "sweep_date": sweep_date,
                "series": ev.split("-")[0] if "-" in ev else ev,
                "event_ticker": ev, "ticker": m.get("ticker"),
                "liquidity_dollars": float(m.get("liquidity_dollars") or 0),
                "volume_fp": float(m.get("volume_fp") or 0),
                "open_interest_fp": float(m.get("open_interest_fp") or 0),
                "yes_bid": m.get("yes_bid_dollars"), "yes_ask": m.get("yes_ask_dollars"),
                "close_time": m.get("close_time")})
        pages += 1
        cursor = j.get("cursor")
        if pages % 10 == 0:
            print(f"  {pages} pages, {len(rows):,} markets", flush=True)
        if not cursor:
            break
        time.sleep(0.15)
    return pd.DataFrame(rows)


def sweep_series():
    rows = []
    for cat in ("Sports", "Politics", "Economics", "Financials", "Climate and Weather",
                "Entertainment", "Science and Technology", "World", "Crypto"):
        try:
            r = _session.get(f"{B}/series", params={"category": cat}, timeout=30)
            for s in (r.json().get("series", []) if r.status_code == 200 else []):
                rows.append({"series": s.get("ticker"), "category": cat,
                             "fee_type": s.get("fee_type"),
                             "fee_multiplier": s.get("fee_multiplier"),
                             "title": s.get("title")})
        except requests.RequestException:
            pass
        time.sleep(0.3)
    return pd.DataFrame(rows)


def build(sweep_date: str):
    mk = sweep_markets(sweep_date)
    mk.to_csv(OUT, index=False)
    print(f"markets: {len(mk):,} open across {mk.series.nunique():,} series -> {OUT}",
          flush=True)
    sf = sweep_series()
    sf.to_csv(FEES, index=False)
    print(f"series fee schedule: {len(sf):,} series -> {FEES}", flush=True)


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "unknown")
