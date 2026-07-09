"""Polymarket (Global) game-market fetcher via the public gamma API — no MCP, no auth.

Discovery path: GET /sports gives each sport a `series` id; GET /events?series_id=<id>
returns that league's game events, each carrying full team-name outcomes and current
prices. We keep the moneyline market (two team-name outcomes, not spread/total) and
return current implied probabilities keyed by the unordered team-name pair, so the live
collector can match them to ESPN games by name (same as the sportsbook side).
"""
from __future__ import annotations

import json
import datetime as dt
import requests

G = "https://gamma-api.polymarket.com"
_session = requests.Session()
_SPORTS: dict = {}


def _sports() -> dict:
    global _SPORTS
    if not _SPORTS:
        _SPORTS = {s["sport"]: s for s in _session.get(f"{G}/sports", timeout=30).json()}
    return _SPORTS


def _as_list(x):
    return json.loads(x) if isinstance(x, str) else x


def game_prices(sport: str, window_h: float = 30, max_events: int = 600) -> list[dict]:
    """Current moneyline prices for a sport's games near now.

    Returns list of {teams: frozenset(names), price: {name: prob}, start: gameStartTime}.
    """
    s = _sports().get(sport)
    if not s:
        return []
    sid = s.get("series")
    now = dt.datetime.now(dt.timezone.utc)
    out, offset = [], 0
    while offset < max_events:
        evs = _session.get(f"{G}/events", params={
            "series_id": sid, "closed": "false", "limit": 100, "offset": offset,
            "order": "startDate", "ascending": "false"}, timeout=30).json()
        if not evs:
            break
        for e in evs:
            for m in e.get("markets", []):
                q = (m.get("question") or "").lower()
                if any(w in q for w in ("spread", "total", "over/under", "o/u")):
                    continue  # keep the moneyline only
                oc, pr = _as_list(m.get("outcomes")), _as_list(m.get("outcomePrices"))
                gst = m.get("gameStartTime") or e.get("startDate")
                if not (oc and pr and len(oc) == 2 and len(pr) == 2 and gst):
                    continue
                if {str(o).strip().lower() for o in oc} == {"yes", "no"}:
                    continue  # skip Yes/No prop markets; want team-name moneyline
                try:
                    g = dt.datetime.fromisoformat(gst.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if -3 <= (g - now).total_seconds() / 3600 <= window_h:
                    out.append({"teams": frozenset(oc),
                                "price": {oc[0]: float(pr[0]), oc[1]: float(pr[1])},
                                "start": gst})
                break
        offset += 100
        if len(evs) < 100:
            break
    return out


def price_for(games: list[dict], home: str, away: str):
    """Normalized (p_home, p_away) for the matching game, or None."""
    want = frozenset((home, away))
    for g in games:
        if g["teams"] == want:
            ph, pa = g["price"].get(home), g["price"].get(away)
            if ph is not None and pa is not None and (ph + pa) > 0:
                s = ph + pa
                return {"p1": round(ph / s, 4), "p2": round(pa / s, 4),
                        "raw1": ph, "raw2": pa}
    return None


if __name__ == "__main__":
    for sport in ("mlb", "wnba"):
        g = game_prices(sport)
        print(f"{sport}: {len(g)} current game markets")
        for x in g[:4]:
            print("  ", sorted(x["teams"]), x["price"], x["start"])
