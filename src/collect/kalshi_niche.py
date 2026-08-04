"""Niche-sport game markets: the benchmark-intensity gradient sample.

The mechanism claim (benchmarked, repeated, fast-resolving markets are
disciplined) is confounded in the games-vs-futures contrast: futures differ
in repetition AND horizon AND benchmark salience at once. Niche game
markets — table tennis, T20 cricket, esports, minor-league soccer, tennis
challengers — are fast-resolving repeated games WITHOUT a mainstream
sportsbook consensus behind them, isolating the benchmark dimension.

Pre-game timestamps, two tiers:
  A (clean): the event ticker embeds the scheduled start (…26JUL291100… =
     ET clock time; verified close_time lands one plausible match-duration
     later, 0 negative durations in probes). Price = last trade strictly
     before the embedded start — the exact main-sample methodology.
  B (robustness): no embedded time (tennis, minor soccer, rugby). Price at
     close_time − D with conservative sport durations (soccer regulation
     markets settle ~2h after kickoff; D=2.5h is safely pre-game). Tier B
     is secondary; headline numbers use Tier A.

Skipped: UFC (card position unknowable), NASCAR/F1 (multi-outcome futures-
like, covered by the futures leg). Output: data/processed/kalshi_niche_prices.csv
"""
from __future__ import annotations

import os
import re
import time

import pandas as pd
import requests

B = "https://api.elections.kalshi.com/trade-api/v2"
OUT = "data/processed/kalshi_niche_prices.csv"
INV = "data/processed/kalshi_series_inventory.csv"
_session = requests.Session()

COVERED = {"KXNBAGAME", "KXNFLGAME", "KXMLBGAME", "KXNHLGAME", "KXWNBAGAME",
           "KXNCAAFGAME", "KXNCAABGAME", "KXWCGAME", "KXCFBGAME", "KXCBBGAME"}
SKIP_PAT = re.compile(r"UFC|NASCAR|F1|GOLF|BOXING")
# sport class -> tier-B fallback duration (hours before close_time); None = tier A only
CLASSES = [
    ("TABLETENNIS", "tabletennis", 1.5),
    ("T20|CRICKET", "cricket", 4.5),
    ("ATP|WTA|ITF|CHALLENGER|TENNISMATCH", "tennis", 4.0),
    ("DOTA2|VALORANT|OWGAME|CODGAME|R6GAME|LOLGAME|CSGO|CS2|ESPORT|STARCRAFT", "esports", 3.0),
    ("RUGBY", "rugby", 2.5),
    ("NBL|BASKETBALL", "hoops-minor", 2.5),
    ("HOCKEY", "hockey-minor", 3.0),
    ("BASEBALL", "baseball-minor", 3.5),
    ("GAME", "soccer-minor", 2.5),   # residual …GAME series are minor-league soccer
    ("MATCH", "other", 3.0),
]
TICK_TIME = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})(\d{4})?")


def _class_of(ticker: str):
    for pat, name, dur in CLASSES:
        if re.search(pat, ticker):
            return name, dur
    return None, None


def _start_ts(event_ticker: str, close_time: str, fallback_h: float):
    g = TICK_TIME.search(event_ticker)
    if g and g.group(4):
        ts = pd.Timestamp(f"20{g.group(1)}-{g.group(2)}-{g.group(3)} "
                          f"{g.group(4)[:2]}:{g.group(4)[2:]}", tz="US/Eastern")
        return ts.tz_convert("UTC"), "A"
    return pd.Timestamp(close_time) - pd.Timedelta(hours=fallback_h), "B"


def _get(path, params, tries=4):
    for i in range(tries):
        try:
            r = _session.get(f"{B}{path}", params=params, timeout=25)
            if r.status_code == 200:
                return r.json()
            time.sleep(1.0 + i)
        except requests.RequestException:
            time.sleep(1.5 + i)
    return {}


def last_trade_before(ticker: str, ts: int):
    """Last trade strictly before ts -> (price, trade_time) or (None, None)."""
    j = _get("/historical/trades", {"ticker": ticker, "limit": 1, "max_ts": ts})
    tr = j.get("trades", [])
    if not tr:
        return None, None
    p = tr[0].get("yes_price_dollars") or tr[0].get("yes_price")
    try:
        p = float(p)
    except (TypeError, ValueError):
        return None, None
    return (p / 100 if p > 1 else p), tr[0].get("created_time")


def _worklist(max_per_series=400):
    inv = pd.read_csv(INV)
    g = inv[inv.ticker.str.contains("GAME|MATCH", na=False) & (inv.n_settled > 0)
            & ~inv.ticker.isin(COVERED) & ~inv.ticker.str.contains(SKIP_PAT, na=False)]
    done = set(pd.read_csv(OUT)["ticker"]) if os.path.exists(OUT) else set()
    work = []
    for st in g.ticker:
        cls, dur = _class_of(st)
        if cls is None:
            continue
        cursor, fetched = None, 0
        while fetched < max_per_series:
            params = {"series_ticker": st, "status": "settled", "limit": 200}
            if cursor:
                params["cursor"] = cursor
            j = _get("/markets", params)
            ms = j.get("markets", [])
            if not ms:
                break
            for m in ms:
                if m.get("result") not in ("yes", "no") or m["ticker"] in done:
                    continue
                start, tier, = _start_ts(m["event_ticker"], m["close_time"], dur)
                work.append({"series": st, "sport_class": cls, "tier": tier,
                             "event_ticker": m["event_ticker"], "ticker": m["ticker"],
                             "title": m.get("title"), "start_utc": str(start),
                             "close_time": m["close_time"],
                             "won": 1 if m["result"] == "yes" else 0})
            fetched += len(ms)
            cursor = j.get("cursor")
            if not cursor:
                break
            time.sleep(0.35)
        time.sleep(0.35)
    return work


def _price_one(item):
    ts = int(pd.Timestamp(item["start_utc"]).timestamp())
    p, tts = last_trade_before(item["ticker"], ts)
    if p is None:
        return None
    stale = (pd.Timestamp(item["start_utc"]) - pd.Timestamp(tts)).total_seconds() / 60
    return {**item, "p_start": p, "trade_ts": tts, "staleness_min": round(stale, 1)}


def build(out=OUT, workers=12):
    from concurrent.futures import ThreadPoolExecutor
    work = _worklist()
    print(f"niche contracts to price: {len(work):,} across "
          f"{len({w['series'] for w in work})} series", flush=True)
    rows, priced = [], 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, row in enumerate(ex.map(_price_one, work), 1):
            if row is not None:
                rows.append(row)
                priced += 1
            if len(rows) >= 200:
                pd.DataFrame(rows).to_csv(out, mode="a",
                                          header=not os.path.exists(out), index=False)
                rows = []
            if i % 1000 == 0:
                print(f"  {i}/{len(work)} ({priced} priced)", flush=True)
    if rows:
        pd.DataFrame(rows).to_csv(out, mode="a", header=not os.path.exists(out), index=False)
    print(f"done: {priced} priced -> {out}", flush=True)


if __name__ == "__main__":
    build()
