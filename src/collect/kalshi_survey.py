"""Survey Kalshi settled game-outcome markets across major leagues.

Discovery-only: reports how many settled markets each major league has and over
what date range, combining the live and historical tiers (which are split by the
rolling /historical/cutoff boundary). No auth needed for market-data reads.
"""
import sys
import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"

# Game-outcome series (moneyline-style: which team wins) per major league.
SERIES = {
    "NBA":   "KXNBAGAME",
    "NFL":   "KXNFLGAME",
    "MLB":   "KXMLBGAME",
    "NHL":   "KXNHLGAME",
    "WNBA":  "KXWNBAGAME",
    "CFB":   "KXNCAAFGAME",
    "CBB-M": "KXNCAAMBGAME",
}


def pull(endpoint, series_ticker, cap):
    """Paginate settled markets for one series from one endpoint (live/historical)."""
    url = f"{BASE}/{endpoint}"
    out, cursor = [], None
    while len(out) < cap:
        params = {"series_ticker": series_ticker, "limit": 1000, "status": "settled"}
        if cursor:
            params["cursor"] = cursor
        r = requests.get(url, params=params, timeout=45)
        if r.status_code != 200:
            print(f"    [{endpoint}] HTTP {r.status_code}: {r.text[:120]}", flush=True)
            break
        data = r.json()
        markets = data.get("markets", [])
        out.extend(markets)
        cursor = data.get("cursor")
        if not cursor or not markets:
            break
    return out


def survey(cap=30000):
    cut = requests.get(f"{BASE}/historical/cutoff", timeout=30).json()
    print(f"historical cutoff (market_settled_ts): {cut.get('market_settled_ts')}\n", flush=True)
    print(f"{'SPORT':7} {'hist':>7} {'live':>6} {'TOTAL':>7} | date span (close_time)", flush=True)
    print("-" * 72, flush=True)

    rows = {}
    for label, st in SERIES.items():
        hist = pull("historical/markets", st, cap)
        live = pull("markets", st, cap)
        merged = {m.get("ticker"): m for m in hist}
        merged.update({m.get("ticker"): m for m in live})
        markets = list(merged.values())
        dates = sorted(m.get("close_time", "")[:10] for m in markets if m.get("close_time"))
        span = f"{dates[0]} -> {dates[-1]}" if dates else "no dates"
        print(f"{label:7} {len(hist):>7} {len(live):>6} {len(markets):>7} | {span}", flush=True)
        rows[label] = {"hist": len(hist), "live": len(live), "total": len(markets), "span": span}
    return rows


if __name__ == "__main__":
    survey()
