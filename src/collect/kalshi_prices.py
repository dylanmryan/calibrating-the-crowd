"""Pull each Kalshi market's pre-game implied probability from the order book.

For a market and an official start time, we read the candlestick series and take
the LAST candle at or before start, using the bid/ask midpoint
(yes_bid + yes_ask)/2 as the implied probability -- the resting order book, not
trades. We also return the bid/ask spread (liquidity/quality signal) and how stale
the quote is (gap from the candle to start), so thin or stale markets can be flagged.
"""
from __future__ import annotations

import time
import datetime as dt
import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"
_session = requests.Session()


def fetch_cutoff() -> str:
    """Current live/historical price boundary (market_settled_ts)."""
    r = _session.get(f"{BASE}/historical/cutoff", timeout=30)
    return r.json().get("market_settled_ts", "")


def _candles(ticker: str, series: str, start_ts: int, end_ts: int, interval: int):
    """Try the live series path, then the historical path; return candle list or []."""
    for url in (f"{BASE}/series/{series}/markets/{ticker}/candlesticks",
                f"{BASE}/historical/markets/{ticker}/candlesticks"):
        for attempt in range(3):
            try:
                r = _session.get(url, params={"start_ts": start_ts, "end_ts": end_ts,
                                              "period_interval": interval}, timeout=30)
            except requests.RequestException:  # dropped connection / DNS blip -> back off, retry
                time.sleep(3.0 * (attempt + 1))
                continue
            if r.status_code == 200:
                cs = r.json().get("candlesticks", [])
                if cs:
                    return cs
                break  # 200 but empty -> try next path
            if r.status_code in (429, 500, 502, 503):
                time.sleep(1.0 * (attempt + 1))
            else:
                break
    return []


def _dollars(node):
    v = (node or {}).get("close_dollars")
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def closing_book_price(ticker: str, series: str, start_utc: str,
                       lookback_hours: int = 6) -> dict | None:
    """Order-book implied probability at/just before official start.

    Returns dict(mid, yes_bid, yes_ask, spread, quote_utc, staleness_min) or None
    if no book exists in the window.
    """
    start = dt.datetime.fromisoformat(str(start_utc).replace("Z", "+00:00"))
    end_ts = int(start.timestamp())
    start_ts = end_ts - lookback_hours * 3600
    # 1-min candles are dense post-cutoff; fall back to 60-min for older historical markets.
    cs = _candles(ticker, series, start_ts, end_ts, interval=1)
    if not cs:
        cs = _candles(ticker, series, end_ts - max(lookback_hours, 72) * 3600, end_ts, interval=60)
    # keep candles at or before start that actually have a two-sided book
    usable = []
    for c in cs:
        if c.get("end_period_ts", 1 << 62) > end_ts:
            continue
        yb, ya = _dollars(c.get("yes_bid")), _dollars(c.get("yes_ask"))
        if yb is not None and ya is not None and ya >= yb:
            usable.append((c["end_period_ts"], yb, ya))
    if not usable:
        return None
    ts, yb, ya = max(usable, key=lambda x: x[0])  # last book before start
    return {
        "mid": round((yb + ya) / 2, 4),
        "yes_bid": yb, "yes_ask": ya,
        "spread": round(ya - yb, 4),
        "quote_utc": dt.datetime.fromtimestamp(ts, dt.timezone.utc).isoformat(),
        "staleness_min": round((end_ts - ts) / 60, 1),
    }


def build_price_dataset(out: str = "data/processed/kalshi_prices.csv",
                        window_days: int = 64) -> None:
    """Pull BOTH sides' pre-game book prices for every matched game in the price window.

    Two sides per game -> two (implied_prob, won) points spanning the full 0-1 range,
    which is what a favorite-longshot / calibration analysis needs. We only attempt
    games settled within Kalshi's rolling price window (older ones have no book data).
    """
    import datetime as _dt
    import pandas as pd
    cutoff = fetch_cutoff()
    cut_dt = _dt.datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
    print(f"cutoff={cutoff}; pulling BOTH sides for matched games since ~cutoff", flush=True)

    m = pd.read_csv("data/processed/kalshi_espn_matches.csv")
    m = m[m.matched & m.start_utc.notna()].copy()
    m["start"] = pd.to_datetime(m["start_utc"], utc=True, format="ISO8601")
    # keep only games in the priceable window (small buffer before cutoff)
    m = m[m["start"] >= (cut_dt - _dt.timedelta(days=2))]
    kal = pd.read_csv("data/processed/kalshi_settled_markets.csv")

    rows, n_games = [], 0
    for lg, g in m.sort_values("start").groupby("league"):
        games = hits = 0
        for r in g.itertuples(index=False):
            games += 1
            for side in kal[kal.event_ticker == r.event_ticker].itertuples(index=False):
                px = closing_book_price(side.ticker, side.series_ticker, r.start_utc)
                if px:
                    hits += 1
                    rows.append({"league": lg, "event_ticker": r.event_ticker,
                                 "ticker": side.ticker, "start_utc": r.start_utc,
                                 "implied_prob": px["mid"], "spread": px["spread"],
                                 "staleness_min": px["staleness_min"], "won": int(side.won)})
        n_games += games
        print(f"  {lg:6} games={games:5} priced-sides={hits:5}", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    print(f"\nsaved {len(df):,} priced sides from {n_games:,} games -> {out}", flush=True)


if __name__ == "__main__":
    build_price_dataset()
