"""Polymarket historical pricing -> one row per matched game (home/away closing probs + outcome).

For each resolved game event (per sport series), take the moneyline market's two
outcome tokens, read each token's CLOB price-history at/before the official ESPN start
(fidelity=1), normalize to sum 1, and read the winner from the resolved outcomePrices.
Games are matched to the ESPN registry by full team name + date.
"""
from __future__ import annotations

import os
import json
import datetime as dt
import pandas as pd
import requests

from src.match.kalshi_espn import espn_games

G = "https://gamma-api.polymarket.com"
C = "https://clob.polymarket.com"
_session = requests.Session()

LEAGUE_TO_POLY = {"MLB": "mlb", "WNBA": "wnba", "NBA": "nba", "NFL": "nfl",
                  "NHL": "nhl", "CBB-M": "ncaab", "CFB": "cfb"}


def _as_list(x):
    return json.loads(x) if isinstance(x, str) else x


def _sports():
    return {s["sport"]: s for s in _session.get(f"{G}/sports", timeout=30).json()}


def poly_price_at(token: str, start_epoch: int, window_h: int = 8) -> dict | None:
    r = _session.get(f"{C}/prices-history", params={
        "market": token, "startTs": start_epoch - window_h * 3600,
        "endTs": start_epoch, "fidelity": 1}, timeout=30)
    if r.status_code != 200:
        return None
    h = [p for p in r.json().get("history", []) if p["t"] <= start_epoch]
    if not h:
        return None
    last = h[-1]  # history is ascending in t
    return {"price": float(last["p"]), "staleness_min": round((start_epoch - last["t"]) / 60, 1)}


def _moneyline(event: dict):
    """Return (outcomes, clobTokenIds, final_prices, gameStartTime) for the moneyline market."""
    for m in event.get("markets", []):
        q = (m.get("question") or "").lower()
        if any(w in q for w in ("spread", "total", "over/under", "o/u")):
            continue
        oc = _as_list(m.get("outcomes"))
        if not oc or len(oc) != 2 or {str(o).lower() for o in oc} == {"yes", "no"}:
            continue
        toks = _as_list(m.get("clobTokenIds"))
        fin = _as_list(m.get("outcomePrices"))
        gst = m.get("gameStartTime") or event.get("startDate")
        if toks and len(toks) == 2 and gst:
            return oc, toks, fin, gst
    return None


def build(out="data/processed/polymarket_hist_prices.csv", leagues=None,
          max_events=4000, flush_every=50) -> None:
    esp = espn_games()
    esp = esp.assign(gdate=pd.to_datetime(esp["start_utc"], utc=True, format="ISO8601").dt.date)
    # index ESPN games by (league, date) -> games; Polymarket names may be nicknames
    # ("Lakers") vs ESPN full names ("Los Angeles Lakers"), so match by substring.
    from collections import defaultdict
    gidx: dict = defaultdict(list)
    for e in esp.itertuples(index=False):
        gidx[(e.league, e.gdate)].append(e)

    def _match(lg, names, gstart):
        """Return (game, {poly_name: 'home'|'away'}) or (None, None).

        gstart is the Polymarket game datetime (UTC). Among team+date candidates
        (doubleheaders), pick the ESPN game closest in start time.
        """
        n0, n1 = names[0].lower(), names[1].lower()
        if n0 == n1:
            return None, None  # degenerate market (identical outcome names)
        def hit(pn, team):
            t = team.lower()
            return pn in t or t.endswith(pn)
        gdate = gstart.date()
        cands = []
        for dd in (gdate, gdate - dt.timedelta(days=1), gdate + dt.timedelta(days=1)):
            for e in gidx.get((lg, dd), []):
                if hit(n0, e.home_team) and hit(n1, e.away_team):
                    cands.append((e, {names[0]: "home", names[1]: "away"}))
                elif hit(n0, e.away_team) and hit(n1, e.home_team):
                    cands.append((e, {names[0]: "away", names[1]: "home"}))
        if not cands:
            return None, None
        if len(cands) == 1:
            return cands[0]
        gs = pd.Timestamp(gstart)
        return min(cands, key=lambda c: abs((pd.Timestamp(c[0].start_utc) - gs).total_seconds()))

    sports = _sports()
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    rows = []
    for lg in (leagues or LEAGUE_TO_POLY):
        sport = LEAGUE_TO_POLY.get(lg)
        s = sports.get(sport)
        if not s:
            print(f"  {lg}: no Polymarket sport '{sport}'", flush=True)
            continue
        sid = s.get("series")
        matched = seen = 0
        for offset in range(0, max_events, 100):
            r = _session.get(f"{G}/events", params={
                "series_id": sid, "closed": "true", "limit": 100, "offset": offset,
                "order": "startDate", "ascending": "false"}, timeout=30)
            evs = r.json() if r.status_code == 200 else None
            if not isinstance(evs, list) or not evs:
                break
            for e in evs:
                if not isinstance(e, dict):
                    continue
                ml = _moneyline(e)
                if not ml:
                    continue
                oc, toks, fin, gst = ml
                seen += 1
                g = dt.datetime.fromisoformat(gst.replace("Z", "+00:00"))
                game, side = _match(lg, oc, g)
                if not game or game.espn_id in done or set(side.values()) != {"home", "away"}:
                    continue
                start_epoch = int(pd.Timestamp(game.start_utc).timestamp())
                tok = dict(zip(oc, toks))          # poly name -> token
                home_name = next(n for n, s in side.items() if s == "home")
                away_name = next(n for n, s in side.items() if s == "away")
                ph = poly_price_at(tok.get(home_name), start_epoch)
                pa = poly_price_at(tok.get(away_name), start_epoch)
                if not ph or not pa:
                    continue
                tot = ph["price"] + pa["price"]
                if tot <= 0:
                    continue
                winner = oc[0] if fin and float(fin[0]) > float(fin[1]) else (oc[1] if fin else None)
                rows.append({
                    "game_id": game.espn_id, "league": lg, "start_utc": game.start_utc,
                    "team1": game.home_team, "team2": game.away_team,
                    "poly_p1": round(ph["price"] / tot, 4), "poly_p2": round(pa["price"] / tot, 4),
                    # raw price per side (un-normalized); prices-history gives no bid/ask book
                    "poly_raw1": round(ph["price"], 4), "poly_raw2": round(pa["price"], 4),
                    "poly_stale1": ph["staleness_min"], "poly_stale2": pa["staleness_min"],
                    "poly_outcome": 1 if side.get(winner) == "home" else (2 if side.get(winner) == "away" else None),
                })
                matched += 1
                done.add(game.espn_id)
                if len(rows) >= flush_every:
                    _append(out, rows); rows = []
            if len(evs) < 100:
                break
        print(f"  {lg}: moneyline events seen={seen}, matched+priced={matched}", flush=True)
    if rows:
        _append(out, rows)
    print("done", flush=True)


def _append(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(rows)
    if os.path.exists(path):
        df = pd.concat([pd.read_csv(path), df], ignore_index=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    import sys
    build(leagues=sys.argv[1:] or None)
