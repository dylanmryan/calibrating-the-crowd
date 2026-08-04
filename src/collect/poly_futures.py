"""Polymarket sports futures: cross-platform check of the futures pathology.

The Kalshi futures leg found longshot overpricing and both-tail
overconfidence in winner-take-all outright fields. Is that Kalshi-specific
or exchange-general? Same design here: resolved multi-outcome championship
/ conference / award fields on Polymarket, each outcome priced at T-7d and
T-30d before the event's close, winner from final outcomePrices.

Discovery: gamma public-search over a fixed query list (championships,
conferences, majors, awards across US sports + soccer), keeping closed
events with >= 5 outcome markets and exactly one YES resolution.
Prices: CLOB /prices-history (coarse ~12h granularity for resolved
markets — immaterial at 7/30-day horizons). Output:
data/processed/poly_futures_prices.csv
"""
from __future__ import annotations

import json
import os
import time

import pandas as pd
import requests

G = "https://gamma-api.polymarket.com"
C = "https://clob.polymarket.com"
OUT = "data/processed/poly_futures_prices.csv"
_session = requests.Session()

QUERIES = [
    "NBA Champion", "NBA Eastern Conference", "NBA Western Conference", "NBA MVP",
    "World Series", "AL Pennant", "NL Pennant", "MLB MVP",
    "Super Bowl Champion", "AFC Champion", "NFC Champion", "NFL MVP", "Heisman",
    "Stanley Cup", "College Football Champion", "March Madness Champion",
    "Premier League Winner", "Champions League Winner", "La Liga Winner",
    "Ballon d'Or", "Formula 1 Champion", "Masters Winner", "Wimbledon Champion",
]


def _events():
    seen, evs = set(), []
    for q in QUERIES:
        try:
            r = _session.get(f"{G}/public-search",
                             params={"q": q, "limit_per_type": 12}, timeout=20)
            found = r.json().get("events", []) if r.status_code == 200 else []
        except requests.RequestException:
            continue
        for e in found:
            if e.get("closed") and e.get("slug") not in seen \
                    and len(e.get("markets") or []) >= 5:
                seen.add(e["slug"])
                evs.append(e)
        time.sleep(0.3)
    return evs


def _history(token: str):
    """Full price path for a token (windowed queries reject long ranges;
    interval=max returns everything at ~12h fidelity)."""
    try:
        r = _session.get(f"{C}/prices-history",
                         params={"market": token, "interval": "max", "fidelity": 720},
                         timeout=25)
        return r.json().get("history", []) if r.status_code == 200 else []
    except requests.RequestException:
        return []


def build(out=OUT, workers=8):
    from concurrent.futures import ThreadPoolExecutor
    done = set(pd.read_csv(out)["token"].astype(str)) if os.path.exists(out) else set()
    work = []
    for e in _events():
        ms = e.get("markets") or []
        wins, items = 0, []
        close = e.get("closedTime") or e.get("endDate")
        if not close:
            continue
        for m in ms:
            try:
                prices = json.loads(m.get("outcomePrices") or "[]")
                tokens = json.loads(m.get("clobTokenIds") or "[]")
            except json.JSONDecodeError:
                continue
            if len(prices) != 2 or len(tokens) != 2:
                continue
            won = 1 if float(prices[0]) > 0.5 else 0
            wins += won
            items.append({"event_slug": e["slug"], "event_title": e.get("title"),
                          "close_time": close, "n_outcomes": len(ms),
                          "title": m.get("question"), "token": str(tokens[0]),
                          "won": won})
        if wins == 1:                     # winner-take-all fields only
            work.extend(i for i in items if i["token"] not in done)
    print(f"poly futures contracts to price: {len(work):,} in "
          f"{len({w['event_slug'] for w in work})} fields", flush=True)

    # anchor each field at its DECISION moment, not the event's closedTime
    # (events often close weeks after the title is decided, which would put
    # T-7d in the post-decision regime). Decision = first time the winner's
    # path prints >= 0.99. Prints older than MAX_STALE_D days at the target
    # are dropped: with ~12h candle fidelity any active market has a recent
    # print, so this kills the stale-peak artifact (faded contenders whose
    # last trade was at their high).
    MAX_STALE_D = 3
    decision = {}
    for slug in {w["event_slug"] for w in work}:
        wtok = next((w["token"] for w in work if w["event_slug"] == slug and w["won"]), None)
        if wtok:
            h = _history(wtok)
            hit = next((x["t"] for x in h if x["p"] >= 0.99), None)
            if hit:
                decision[slug] = hit
    print(f"decision anchors found for {len(decision)} fields", flush=True)
    work = [w for w in work if w["event_slug"] in decision]

    def price_one(item):
        dt = decision[item["event_slug"]]
        h = _history(item["token"])
        row = dict(item)
        row["decision_ts"] = dt
        any_p = False
        for hd in (7, 30):
            ts = dt - hd * 86400
            pts = [x for x in h if x["t"] <= ts]
            if pts and (ts - pts[-1]["t"]) <= MAX_STALE_D * 86400:
                row[f"p_{hd}d"] = pts[-1]["p"]
                any_p = True
            else:
                row[f"p_{hd}d"] = None
        return row if any_p else None

    rows, priced = [], 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, row in enumerate(ex.map(price_one, work), 1):
            if row is not None:
                rows.append(row)
                priced += 1
            if len(rows) >= 100:
                pd.DataFrame(rows).to_csv(out, mode="a",
                                          header=not os.path.exists(out), index=False)
                rows = []
            if i % 200 == 0:
                print(f"  {i}/{len(work)} ({priced} priced)", flush=True)
    if rows:
        pd.DataFrame(rows).to_csv(out, mode="a", header=not os.path.exists(out), index=False)
    print(f"done: {priced} priced -> {out}", flush=True)


if __name__ == "__main__":
    build()
