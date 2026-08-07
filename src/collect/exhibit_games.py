"""Case-study exhibits: a few games captured in full cross-venue detail.

The report's aggregate claims deserve concrete openings — named games where
the reader can watch 20+ books, two exchanges, and the tape converge. Four
exhibits (chosen for story value and data coverage):

  1. 401859967  NBA Finals Game 5 (SAS-NYK, 2026-06-13): the title clincher.
  2. 401772988  Super Bowl LX (SEA-NE, 2026-02-08): the biggest single event.
  3. 401772937  BUF-MIA TNF (2025-09-18): the tape's highest-notional game
     ($4.5M in our 24h window) — the "ordinary marquee game."
  4. 401814965  PIT-WSH (2026-04-16): 10-inning 1-run walk-off with full
     ladder + tape coverage — the MLB blind-spot exhibit.

Per game: per-book h2h odds (us+eu regions) at seven horizons (T-72h to
start), close-time spreads/totals per book, full Kalshi trade tape, and
Polymarket price paths. Odds API cost ~160 credits/game (~650 total, the
tail of the budget). Everything lands in data/exhibits/.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env", override=True)
BASE = "https://api.the-odds-api.com/v4"
KEY = os.getenv("ODDS_API_KEY")
KB = "https://api.elections.kalshi.com/trade-api/v2"
OUT = "data/exhibits"
_session = requests.Session()

GAMES = [
    dict(game_id=401859967, league="NBA", sport="basketball_nba",
         start="2026-06-14T00:30:00Z", home="San Antonio Spurs",
         away="New York Knicks", tag="nba_finals_g5"),
    dict(game_id=401772988, league="NFL", sport="americanfootball_nfl",
         start="2026-02-08T23:30:00Z", home="New England Patriots",
         away="Seattle Seahawks", tag="super_bowl_lx"),
    dict(game_id=401772937, league="NFL", sport="americanfootball_nfl",
         start="2025-09-19T00:15:00Z", home="Buffalo Bills",
         away="Miami Dolphins", tag="buf_mia_tnf"),
    dict(game_id=401814965, league="MLB", sport="baseball_mlb",
         start="2026-04-16T16:35:00Z", home="Pittsburgh Pirates",
         away="Washington Nationals", tag="pit_wsh_walkoff"),
]
HORIZONS_H = (72, 24, 12, 6, 3, 1, 0)


def _norm(s):
    return str(s).lower().strip()


KALSHI_EVENT_OVERRIDE = {401859967: "KXNBAGAME-26JUN13NYKSAS"}
POLY_SLUG_OVERRIDE = {401772988: "nfl-sea-ne-2026-02-08",
                      401859967: "nba-nyk-sas-2026-06-13",
                      401772937: "nfl-mia-buf-2025-09-18",
                      401814965: "mlb-wsh-pit-2026-04-16"}


def books_leg(g):
    out_f = f"{OUT}/{g['tag']}_books.csv"
    if os.path.exists(out_f):
        prev = pd.read_csv(out_f)
        if len(prev) > 50:
            print("   (books already collected, skipping)", flush=True)
            return prev
    rows = []
    start = pd.Timestamp(g["start"])
    ev_id = None
    for h in HORIZONS_H:
        ts = (start - pd.Timedelta(hours=h)).floor("60min" if h == 0 else "1min")
        r = _session.get(f"{BASE}/historical/sports/{g['sport']}/odds", params={
            "apiKey": KEY, "regions": "us,eu", "markets": "h2h",
            "oddsFormat": "decimal", "date": ts.strftime("%Y-%m-%dT%H:%M:%SZ")},
            timeout=30)
        snap = r.json().get("data", []) if r.status_code == 200 else []
        for sg in snap:
            if _norm(sg.get("home_team")) != _norm(g["home"]) or \
               _norm(sg.get("away_team")) != _norm(g["away"]):
                continue
            ev_id = sg.get("id") or ev_id
            for bk in sg.get("bookmakers", []):
                mk = next((x for x in bk.get("markets", []) if x["key"] == "h2h"), None)
                if not mk:
                    continue
                px = {o["name"]: o["price"] for o in mk["outcomes"]}
                if g["home"] in px and g["away"] in px:
                    rows.append({"horizon_h": h, "snap_utc": str(ts), "book": bk["key"],
                                 "market": "h2h", "home_decimal": px[g["home"]],
                                 "away_decimal": px[g["away"]],
                                 "point": None, "book_ts": mk.get("last_update")})
        time.sleep(0.2)
    # close-time spreads + totals per book
    if ev_id:
        ts = start.floor("60min")
        r = _session.get(f"{BASE}/historical/sports/{g['sport']}/events/{ev_id}/odds",
                         params={"apiKey": KEY, "regions": "us", "date":
                                 ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                 "markets": "spreads,totals", "oddsFormat": "decimal"},
                         timeout=30)
        data = (r.json() or {}).get("data") if r.status_code == 200 else None
        for bk in (data or {}).get("bookmakers", []):
            for mk in bk.get("markets", []):
                for o in mk.get("outcomes", []):
                    rows.append({"horizon_h": 0, "snap_utc": str(ts), "book": bk["key"],
                                 "market": mk["key"], "home_decimal": None,
                                 "away_decimal": None, "point": o.get("point"),
                                 "book_ts": f"{o.get('name')}@{o.get('price')}"})
    return pd.DataFrame(rows)


def kalshi_leg(g):
    mt = pd.read_csv("data/processed/kalshi_espn_matches.csv")
    kk = pd.read_csv("data/processed/kalshi_settled_markets.csv")
    ev = mt[mt.espn_id == g["game_id"]].event_ticker
    evt = KALSHI_EVENT_OVERRIDE.get(g["game_id"],
                                    ev.iloc[0] if len(ev) else None)
    if evt is None:
        return pd.DataFrame()
    tks = kk[kk.event_ticker == evt].ticker.tolist()
    if not tks:   # settled-markets file may predate the game; ask the API
        rr = _session.get(f"{KB}/markets", params={"event_ticker": evt,
                                                   "limit": 10}, timeout=20)
        tks = [m["ticker"] for m in (rr.json().get("markets", [])
                                     if rr.status_code == 200 else [])]
    rows = []
    for tk in tks:
        end = int(pd.Timestamp(g["start"]).timestamp()) + 6 * 3600
        cursor = None
        # recent (post-cutoff) games live on /markets/trades; older ones on
        # /historical/trades — probe historical first, fall back to live
        probe = _session.get(f"{KB}/historical/trades",
                             params={"ticker": tk, "limit": 1, "max_ts": end},
                             timeout=20)
        endpoint = ("/historical/trades"
                    if probe.status_code == 200 and probe.json().get("trades")
                    else "/markets/trades")
        for _ in range(25):
            params = {"ticker": tk, "limit": 1000, "max_ts": end}
            if cursor:
                params["cursor"] = cursor
            rr = _session.get(f"{KB}{endpoint}", params=params, timeout=25)
            j = rr.json() if rr.status_code == 200 else {}
            tr = j.get("trades", [])
            for t in tr:
                rows.append({"ticker": tk, "created_time": t["created_time"],
                             "yes_price": float(t.get("yes_price_dollars") or 0)
                             or float(t.get("yes_price", 0)) / 100,
                             "count": float(t.get("count_fp") or t.get("count") or 0),
                             "taker_side": t.get("taker_side")})
            cursor = j.get("cursor")
            if not tr or not cursor:
                break
            time.sleep(0.1)
    return pd.DataFrame(rows)


def poly_leg(g):
    toks = []
    if g["game_id"] in POLY_SLUG_OVERRIDE:
        ev = _session.get("https://gamma-api.polymarket.com/events",
                          params={"slug": POLY_SLUG_OVERRIDE[g["game_id"]]},
                          timeout=20).json()
        for m in (ev[0].get("markets", []) if ev else []):
            ids = json.loads(m.get("clobTokenIds") or "[]")
            if ids:
                toks.append((m.get("question", "?")[:40], str(ids[0])))
    rows = []
    for side, tok in toks:
        for fid in (60, 180, 720):
            try:
                rr = _session.get("https://clob.polymarket.com/prices-history",
                                  params={"market": tok, "interval": "max",
                                          "fidelity": fid}, timeout=30)
                h = rr.json().get("history", []) if rr.status_code == 200 else []
            except requests.RequestException:
                h = []
            if h:
                rows += [{"side": side, "fidelity_min": fid, "ts": x["t"],
                          "p": x["p"]} for x in h]
                break
            time.sleep(0.2)
    return pd.DataFrame(rows)


def build():
    os.makedirs(OUT, exist_ok=True)
    manifest = []
    for g in GAMES:
        print(f"== {g['tag']} ==", flush=True)
        b = books_leg(g)
        b.to_csv(f"{OUT}/{g['tag']}_books.csv", index=False)
        k = kalshi_leg(g)
        k.to_csv(f"{OUT}/{g['tag']}_kalshi_trades.csv", index=False)
        p = poly_leg(g)
        p.to_csv(f"{OUT}/{g['tag']}_poly_path.csv", index=False)
        manifest.append({**{k2: v for k2, v in g.items()},
                         "book_rows": len(b), "books": b.book.nunique() if len(b) else 0,
                         "kalshi_fills": len(k), "poly_points": len(p)})
        print(f"   books rows={len(b)} | kalshi fills={len(k):,} | poly pts={len(p)}",
              flush=True)
    pd.DataFrame(manifest).to_csv(f"{OUT}/exhibits_manifest.csv", index=False)
    print("manifest written", flush=True)


if __name__ == "__main__":
    build()
