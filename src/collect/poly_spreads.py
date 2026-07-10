"""Polymarket actual quoted spreads from OddPool archived order books.

Completes the 3-venue cost table: we have the books' overround (~4.2%) and
Kalshi's quoted bid/ask spread (~1.0%), but Polymarket's moneyline prices came
from CLOB last-trade history, which carries no book. OddPool archived Polymarket
order-book snapshots (since ~Mar 2026) keyed by gamma conditionId + token.

Two stages, resumable:
  harvest  — free gamma calls: map joint-set games (start >= APRIL) to their
             moneyline conditionId + home-outcome token -> data/processed/poly_token_map.csv
  fetch    — 1 OddPool request/game (free tier ~25s throttle): archived book
             just before official start -> data/processed/poly_spreads.csv

Budget note: free tier is 1K req/month shared with validate_recon; default cap
150 games, stratified by league.
"""
from __future__ import annotations

import datetime as dt
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from src.collect.polymarket_hist import G, LEAGUE_TO_POLY, _as_list, _sports, _session

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env", override=True)
H = {"X-API-Key": (os.getenv("ODDSPOOL_API_KEY") or "").strip()}
B = "https://api.oddpool.com"
SINCE = "2026-04-01"          # inside OddPool's archive window, post-fee era
MAP_OUT = "data/processed/poly_token_map.csv"
OUT = "data/processed/poly_spreads.csv"


def _ml_market(event: dict):
    """Moneyline market of a game event -> (outcomes, tokens, conditionId, gameStart)."""
    for m in event.get("markets", []):
        q = (m.get("question") or "").lower()
        if any(w in q for w in ("spread", "total", "over/under", "o/u")):
            continue
        oc = _as_list(m.get("outcomes"))
        if not oc or len(oc) != 2 or {str(o).lower() for o in oc} == {"yes", "no"}:
            continue
        toks = _as_list(m.get("clobTokenIds"))
        cid = m.get("conditionId")
        gst = m.get("gameStartTime") or event.get("startDate")
        if toks and len(toks) == 2 and cid and gst:
            return oc, toks, cid, gst
    return None


def harvest(out=MAP_OUT, since=SINCE):
    """Map clean joint-set games since `since` to conditionId + home token (gamma, free)."""
    m = pd.read_csv("data/processed/games_master.csv")
    m = m[m["poly_p1"].notna() & m["outcome"].notna() & ~m["outcome_disagree"].fillna(False)]
    m = m[m["start_utc"] >= since].copy()
    m["gdate"] = pd.to_datetime(m["start_utc"], utc=True, format="ISO8601").dt.date
    print(f"games to map: {len(m):,} across {sorted(m.league.unique())}", flush=True)

    def hit(pn, team):
        t = str(team).lower()
        return pn in t or t.endswith(pn)

    sports = _sports()
    rows = []
    for lg in sorted(m.league.unique()):
        sid = (sports.get(LEAGUE_TO_POLY.get(lg, "")) or {}).get("series")
        if not sid:
            continue
        sub = m[m.league == lg]
        found = 0
        for offset in range(0, 4000, 100):
            r = _session.get(f"{G}/events", params={
                "series_id": sid, "closed": "true", "limit": 100, "offset": offset,
                "order": "startDate", "ascending": "false"}, timeout=30)
            evs = r.json() if r.status_code == 200 else None
            if not isinstance(evs, list) or not evs:
                break
            for e in evs:
                ml = _ml_market(e) if isinstance(e, dict) else None
                if not ml:
                    continue
                oc, toks, cid, gst = ml
                g = dt.datetime.fromisoformat(gst.replace("Z", "+00:00"))
                cands = []
                for dd in (g.date(), g.date() - dt.timedelta(days=1), g.date() + dt.timedelta(days=1)):
                    for e2 in sub[sub.gdate == dd].itertuples(index=False):
                        n0, n1 = oc[0].lower(), oc[1].lower()
                        if hit(n0, e2.team1) and hit(n1, e2.team2):
                            cands.append((e2, 0))
                        elif hit(n0, e2.team2) and hit(n1, e2.team1):
                            cands.append((e2, 1))
                if not cands:
                    continue
                best, hidx = min(cands, key=lambda c: abs(
                    (pd.Timestamp(c[0].start_utc) - pd.Timestamp(g)).total_seconds()))
                rows.append({"game_id": best.game_id, "league": lg, "start_utc": best.start_utc,
                             "condition_id": cid, "token_home": toks[hidx],
                             "k_spread1": best.k_spread1})
                found += 1
            # events are newest-first; stop paging once older than our window
            last = evs[-1].get("startDate") if isinstance(evs[-1], dict) else None
            if last and last < since:
                break
            if len(evs) < 100:
                break
        print(f"  {lg}: mapped {found}", flush=True)
    df = pd.DataFrame(rows).drop_duplicates(subset=["game_id"])
    df.to_csv(out, index=False)
    print(f"saved {len(df):,} token mappings -> {out}", flush=True)


def fetch_book(condition_id, token, start_utc, retries=3):
    end_ms = int(pd.Timestamp(start_utc).timestamp() * 1000)
    for attempt in range(retries):
        try:
            r = requests.get(f"{B}/historical/polymarket/orderbook", headers=H, params={
                "market_id": condition_id, "asset_id": token,
                "start_time": end_ms - 30 * 60 * 1000, "end_time": end_ms,
                "granularity": "5m", "limit": 10}, timeout=25)
        except requests.RequestException:
            time.sleep(20); continue
        if r.status_code == 200:
            s = r.json().get("snapshots", [])
            return s[-1] if s else None
        if r.status_code == 429:
            time.sleep(45 * (attempt + 1)); continue
        return None
    return None


def fetch(cap=150, per_league=40):
    mp = pd.read_csv(MAP_OUT)
    done = set(pd.read_csv(OUT)["game_id"]) if os.path.exists(OUT) else set()
    todo = (mp[~mp.game_id.isin(done)]
            .sample(frac=1, random_state=7).groupby("league").head(per_league)
            .head(max(0, cap - len(done))))
    print(f"fetching {len(todo)} archived books ({len(done)} done)", flush=True)
    rows, n = [], 0
    for r in todo.itertuples(index=False):
        snap = fetch_book(r.condition_id, r.token_home, r.start_utc)
        n += 1
        if snap and snap.get("best_bid") is not None and snap.get("best_ask") is not None:
            bid, ask = float(snap["best_bid"]), float(snap["best_ask"])
            rows.append({"game_id": r.game_id, "league": r.league,
                         "poly_bid": bid, "poly_ask": ask, "poly_spread": round(ask - bid, 4),
                         "k_spread1": r.k_spread1,
                         "snap_gap_min": round((pd.Timestamp(r.start_utc).timestamp()
                                                - snap["timestamp"] / 1000) / 60, 1)})
        if len(rows) >= 10:
            _append(rows); rows = []
            print(f"  ...{n}", flush=True)
        time.sleep(25)
    if rows:
        _append(rows)
    print(f"done: {n} fetched", flush=True)
    report()


def _append(rows):
    df = pd.DataFrame(rows)
    if os.path.exists(OUT):
        df = pd.concat([pd.read_csv(OUT), df], ignore_index=True)
    df.to_csv(OUT, index=False)


def report():
    d = pd.read_csv(OUT).dropna(subset=["poly_spread"])
    if not len(d):
        print("no rows", flush=True)
        return
    print(f"\n=== Polymarket pre-game quoted spread (archived books, n={len(d)}) ===", flush=True)
    print(f"spread: median {d.poly_spread.median()*100:.2f}pts  mean {d.poly_spread.mean()*100:.2f}  "
          f"p90 {d.poly_spread.quantile(.9)*100:.2f}", flush=True)
    both = d.dropna(subset=["k_spread1"])
    if len(both):
        print(f"same-game Kalshi spread: median {both.k_spread1.median()*100:.2f}pts "
              f"(paired, n={len(both)})", flush=True)
    print(d.groupby("league")["poly_spread"].agg(["median", "mean", "count"]).round(4).to_string(), flush=True)


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("harvest", "all") and not os.path.exists(MAP_OUT):
        harvest()
    if cmd in ("fetch", "all"):
        fetch(cap=int(sys.argv[2]) if len(sys.argv) > 2 else 150)
    if cmd == "report":
        report()
