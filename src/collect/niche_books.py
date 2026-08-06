"""Sportsbook odds for the NICHE-league sample: the functioning benchmark.

For the settled niche matches where mainstream books DO make markets
(Brasileiro, Argentina Primera, Eliteserien, NRL, international T20),
snapshot the EU-region historical odds at each match's start hour. This
turns the MM-involvement question into a functioning comparison: on the
same matches, do the books quote (presence), at what implied vig, and
how far are Kalshi's thin-book prices from the de-vigged consensus —
versus the 0.7pt gap on covered leagues where the MM complex stands?

~10 credits per (league, start-hour) bucket, ~2.5K total. EU region so
Pinnacle anchors the consensus. Team matching: names parsed from Kalshi
market titles ("Will X win the X vs Y game?"), accent-normalized
substring match against the book feed's home/away.
Output: data/processed/niche_book_odds.csv (one row per match-book).
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from src.collect.sportsbook_hist import _norm_name

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env", override=True)
BASE = "https://api.the-odds-api.com/v4"
KEY = os.getenv("ODDS_API_KEY")
OUT = "data/processed/niche_book_odds.csv"
_session = requests.Session()

SPORT = {"KXBRASILEIROGAME": "soccer_brazil_campeonato",
         "KXARGPREMDIVGAME": "soccer_argentina_primera_division",
         "KXELITESERIENGAME": "soccer_norway_eliteserien",
         "KXRUGBYNRLMATCH": "rugbyleague_nrl",
         "KXT20MATCH": "cricket_international_t20"}
TITLE = re.compile(r"^(.+?) vs\.? (.+?)(?::| Winner| Tie| Draw|\?)", re.I)


def matches():
    """All settled matches in the covered niche leagues: the priced sample
    plus everything else Kalshi settled (enumerated live), so the book leg
    covers matches Kalshi's own book never priced."""
    from src.collect.kalshi_niche import _get, _start_ts
    n = pd.read_csv("data/processed/kalshi_niche_prices.csv").drop_duplicates("ticker")
    n = n[n.series.isin(SPORT)]
    rows = {}
    for r in n.itertuples(index=False):
        g = TITLE.search(str(r.title) or "")
        if g:
            rows.setdefault(r.event_ticker, {
                "series": r.series, "event_ticker": r.event_ticker,
                "start_utc": r.start_utc, "t1": g.group(1), "t2": g.group(2)})
    for sr in SPORT:
        j = _get("/markets", {"series_ticker": sr, "status": "settled", "limit": 200})
        for m in j.get("markets", []):
            if m["event_ticker"] in rows or m.get("result") not in ("yes", "no"):
                continue
            g = TITLE.search(str(m.get("title") or ""))
            if not g:
                continue
            start, _ = _start_ts(m["event_ticker"], m["close_time"], 2.5)
            rows[m["event_ticker"]] = {
                "series": sr, "event_ticker": m["event_ticker"],
                "start_utc": str(start), "t1": g.group(1), "t2": g.group(2)}
        time.sleep(0.35)
    return pd.DataFrame(rows.values())


def build(out=OUT):
    m = matches()
    m["start"] = pd.to_datetime(m.start_utc, utc=True, format="ISO8601")
    m["bucket"] = m.start.dt.floor("60min")
    done = set(pd.read_csv(out)["event_ticker"]) if os.path.exists(out) else set()
    m = m[~m.event_ticker.isin(done)]
    print(f"niche matches to price: {len(m):,} | buckets: "
          f"{m.groupby(['series', 'bucket']).ngroups:,}", flush=True)
    rows, calls = [], 0
    for (sr, bucket), grp in m.groupby(["series", "bucket"]):
        r = _session.get(f"{BASE}/historical/sports/{SPORT[sr]}/odds", params={
            "apiKey": KEY, "regions": "eu", "markets": "h2h",
            "oddsFormat": "decimal", "date": bucket.strftime("%Y-%m-%dT%H:%M:%SZ")},
            timeout=30)
        calls += 1
        snap = r.json().get("data", []) if r.status_code == 200 else []
        for g in grp.itertuples(index=False):
            n1, n2 = _norm_name(g.t1), _norm_name(g.t2)
            best = None
            for sg in snap:
                h, a = _norm_name(sg.get("home_team", "")), _norm_name(sg.get("away_team", ""))
                if abs((pd.Timestamp(sg.get("commence_time")) - g.start).total_seconds()) > 4 * 3600:
                    continue
                if (n1 in h or h in n1 or n1 in a or a in n1) and \
                        (n2 in h or h in n2 or n2 in a or a in n2):
                    best = sg
                    break
            if not best:
                rows.append({"event_ticker": g.event_ticker, "series": sr,
                             "start_utc": g.start_utc, "book": None})
                continue
            home_is_t1 = n1 in _norm_name(best["home_team"]) or _norm_name(best["home_team"]) in n1
            for bk in best.get("bookmakers", []):
                mk = next((x for x in bk.get("markets", []) if x["key"] == "h2h"), None)
                if not mk:
                    continue
                px = {o["name"]: o["price"] for o in mk["outcomes"]}
                h = px.get(best["home_team"])
                a = px.get(best["away_team"])
                dr = px.get("Draw")
                if not h or not a:
                    continue
                rows.append({"event_ticker": g.event_ticker, "series": sr,
                             "start_utc": g.start_utc, "book": bk["key"],
                             "home_is_t1": home_is_t1,
                             "raw_h": 1 / h, "raw_a": 1 / a,
                             "raw_d": (1 / dr) if dr else None})
        time.sleep(0.1)
        if calls % 40 == 0:
            print(f"  {calls} calls (~{calls*10} credits)", flush=True)
    pd.DataFrame(rows).to_csv(out, mode="a", header=not os.path.exists(out), index=False)
    print(f"done: {calls} calls (~{calls*10} credits) -> {out}", flush=True)


if __name__ == "__main__":
    build()
