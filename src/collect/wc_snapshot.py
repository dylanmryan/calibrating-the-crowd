"""Live World Cup 3-way snapshotter: Kalshi + sportsbook (home / draw / away).

Soccer matches are 3-way, so this is separate from the binary live_snapshot. It
reuses the signed Kalshi order-book helper and Odds API pattern, but stores three
normalized probabilities per source. Matched to ESPN WC games by country name.
Outcome resolution (regulation vs. penalties) is deferred — prices are the
perishable part. Polymarket omitted for now (no clean WC match-winner market).
"""
from __future__ import annotations

import os
import datetime as dt
import pandas as pd

from src.collect.live_snapshot import _best_book, BASE_K, ODDS, _session
from src.collect.espn import fetch_day

KEY = os.getenv("ODDS_API_KEY")
KSERIES = "KXWCGAME"
ODDS_SPORT = "soccer_fifa_world_cup"
WIN_BEFORE_H, WIN_AFTER_H = 14, 2

# ESPN vs Kalshi/Odds country-name reconciliations (grown from observed misses)
ALIASES = {"USA": "United States", "Korea Republic": "South Korea",
           "IR Iran": "Iran", "Czechia": "Czech Republic"}


def _canon(name):
    return ALIASES.get(str(name).strip(), str(name).strip())


def kalshi_open() -> dict:
    """event_ticker -> {team_name_or_'Draw': ticker} for the 3 open sides per match."""
    out, cursor = {}, None
    while True:
        p = {"series_ticker": KSERIES, "status": "open", "limit": 1000}
        if cursor:
            p["cursor"] = cursor
        r = _session.get(f"{BASE_K}/markets", params=p, timeout=30)
        if r.status_code != 200:
            break
        d = r.json()
        for m in d.get("markets", []):
            ev, tk = m.get("event_ticker"), m.get("ticker", "")
            code = tk.rsplit("-", 1)[-1]
            # Kalshi labels sides "Reg Time: Spain" (regulation-time 3-way) -> strip the prefix
            raw = (m.get("yes_sub_title") or "").replace("Reg Time:", "").strip()
            name = "Draw" if code == "TIE" else _canon(raw)
            if ev and tk and name:
                out.setdefault(ev, {})[name] = tk
        cursor = d.get("cursor")
        if not cursor or not d.get("markets"):
            break
    return out


def kalshi_price(kmk, home, away):
    """Match the event by team-name set, read each side's signed book, normalize across 3."""
    want = {home, away}
    for ev, sides in kmk.items():
        teams = {n for n in sides if n != "Draw"}
        if teams == want and "Draw" in sides and len(sides) == 3:
            mids = {}
            for n, tk in sides.items():
                b = _best_book(tk)
                if not b:
                    break
                mids[n] = (b[0] + b[1]) / 2
            if len(mids) != 3:
                return None
            s = sum(mids.values())
            if s <= 0:
                return None
            return {"p_home": round(mids[home] / s, 4), "p_away": round(mids[away] / s, 4),
                    "p_draw": round(mids["Draw"] / s, 4)}
    return None


def odds_events():
    r = _session.get(f"{ODDS}/sports/{ODDS_SPORT}/odds", params={
        "apiKey": KEY, "regions": "us", "markets": "h2h", "oddsFormat": "decimal"}, timeout=30)
    return r.json() if r.status_code == 200 else []


def book_price(events, home, away):
    """Match by unordered team set (home/away is arbitrary at neutral sites), de-vig 3 outcomes."""
    want = {home, away}
    for e in events:
        if {_canon(e.get("home_team")), _canon(e.get("away_team"))} == want:
            hs = aw = dr = n = 0.0
            for bk in e.get("bookmakers", []):
                mk = next((m for m in bk.get("markets", []) if m["key"] == "h2h"), None)
                if not mk:
                    continue
                px = {_canon(o["name"]) if o["name"] != "Draw" else "Draw": o["price"]
                      for o in mk["outcomes"]}
                if home in px and away in px and "Draw" in px and min(px[home], px[away], px["Draw"]) > 0:
                    hs += 1 / px[home]; aw += 1 / px[away]; dr += 1 / px["Draw"]; n += 1
            if n:
                s = hs + aw + dr
                return {"p_home": round(hs / s, 4), "p_away": round(aw / s, 4),
                        "p_draw": round(dr / s, 4), "n_books": int(n)}
    return None


def snapshot(out="data/live/wc_snapshots.csv") -> pd.DataFrame:
    now = dt.datetime.now(dt.timezone.utc)
    today = now.strftime("%Y%m%d")
    tomorrow = (now + dt.timedelta(days=1)).strftime("%Y%m%d")
    games = fetch_day("WC", today) + fetch_day("WC", tomorrow)
    kmk = kalshi_open()
    odds = odds_events()

    rows = []
    for g in games:
        start = pd.to_datetime(g["start_utc"], utc=True)
        mins = (start - now).total_seconds() / 60
        if not (-WIN_AFTER_H * 60 <= mins <= WIN_BEFORE_H * 60):
            continue
        home, away = _canon(g["home_team"]), _canon(g["away_team"])
        base = {"snapshot_utc": now.isoformat(), "game_id": g["espn_id"], "start_utc": g["start_utc"],
                "minutes_to_start": round(mins, 1), "home": home, "away": away}
        kp = kalshi_price(kmk, home, away)
        if kp:
            rows.append({**base, "source": "kalshi", **kp})
        bp = book_price(odds, home, away)
        if bp:
            rows.append({**base, "source": "sportsbook", **bp})
    df = pd.DataFrame(rows)
    if not df.empty:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if os.path.exists(out):
            df = pd.concat([pd.read_csv(out), df], ignore_index=True)
        df.to_csv(out, index=False)
    return df


if __name__ == "__main__":
    df = snapshot()
    if df.empty:
        print("no World Cup matches in the pre-game window right now")
    else:
        latest = df[df["snapshot_utc"] == df["snapshot_utc"].max()]
        print(f"WC snapshot rows: {len(latest)}")
        show = latest.pivot_table(index=["home", "away", "minutes_to_start"], columns="source",
                                  values=["p_home", "p_draw", "p_away"], aggfunc="first")
        print(show.to_string())
