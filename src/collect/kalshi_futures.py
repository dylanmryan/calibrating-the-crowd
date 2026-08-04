"""Settled multi-outcome futures on Kalshi: prices at fixed horizons.

From the series inventory, take every settled event with >= 3 outcome
contracts and exactly one YES settlement (a winner-take-all field: champion,
division winner, award, seed). Price each contract by its last trade at or
before T-7d and T-30d ahead of the event's close, via /historical/trades
with max_ts (the same trade-recon machinery validated on game markets).
This is the sample where favorite-longshot bias classically lives, and the
direct bridge to Burgi-Deng-Whelan's platform-wide pathology numbers.

Resumable by ticker. Output: data/processed/kalshi_futures_prices.csv.
"""
from __future__ import annotations

import os
import time

import pandas as pd
import requests

B = "https://api.elections.kalshi.com/trade-api/v2"
OUT = "data/processed/kalshi_futures_prices.csv"
INV = "data/processed/kalshi_series_inventory.csv"
HORIZONS_D = (7, 30)
_session = requests.Session()


def last_trade_before(ticker: str, ts: int):
    for attempt in range(3):
        try:
            r = _session.get(f"{B}/historical/trades",
                             params={"ticker": ticker, "limit": 1, "max_ts": ts}, timeout=20)
        except requests.RequestException:
            time.sleep(2.0)
            continue
        if r.status_code == 200:
            tr = r.json().get("trades", [])
            if tr:
                p = tr[0].get("yes_price_dollars") or tr[0].get("yes_price")
                try:
                    p = float(p)
                    return p / 100 if p > 1 else p
                except (TypeError, ValueError):
                    return None
            return None
        time.sleep(1.5)
    return None


def build(out=OUT, min_outcomes=3, max_contracts=4000):
    inv = pd.read_csv(INV)
    picks = inv[(inv.max_outcomes >= min_outcomes) & (inv.n_settled >= min_outcomes)]
    print(f"series with multi-outcome settled events: {len(picks)}", flush=True)
    done = set(pd.read_csv(out)["ticker"]) if os.path.exists(out) else set()
    rows, priced = [], 0
    for sr in picks.itertuples(index=False):
        try:
            r = _session.get(f"{B}/markets", params={"series_ticker": sr.ticker,
                                                     "status": "settled", "limit": 200}, timeout=25)
            ms = r.json().get("markets", []) if r.status_code == 200 else []
        except requests.RequestException:
            continue
        evs = {}
        for m in ms:
            evs.setdefault(m.get("event_ticker"), []).append(m)
        for ev, mlist in evs.items():
            if len(mlist) < min_outcomes:
                continue
            results = [m.get("result") for m in mlist]
            if results.count("yes") != 1:
                continue          # not winner-take-all (or voided) -> skip
            close = max(pd.Timestamp(m.get("close_time")) for m in mlist)
            for m in mlist:
                tk = m.get("ticker")
                if tk in done:
                    continue
                row = {"series": sr.ticker, "event_ticker": ev, "ticker": tk,
                       "title": m.get("title") or m.get("yes_sub_title"),
                       "close_time": str(close), "n_outcomes": len(mlist),
                       "won": 1 if m.get("result") == "yes" else 0}
                any_price = False
                for hd in HORIZONS_D:
                    ts = int((close - pd.Timedelta(days=hd)).timestamp())
                    p = last_trade_before(tk, ts)
                    row[f"p_{hd}d"] = p
                    any_price = any_price or (p is not None)
                    time.sleep(0.08)
                if any_price:
                    rows.append(row)
                    priced += 1
                if len(rows) >= 50:
                    pd.DataFrame(rows).to_csv(out, mode="a",
                                              header=not os.path.exists(out), index=False)
                    rows = []
                if priced >= max_contracts:
                    break
            if priced >= max_contracts:
                break
        if priced >= max_contracts:
            break
    if rows:
        pd.DataFrame(rows).to_csv(out, mode="a", header=not os.path.exists(out), index=False)
    print(f"done: {priced} contracts priced -> {out}", flush=True)


if __name__ == "__main__":
    build()
