"""Joint 1-minute price paths, final 6h before start: Kalshi mid + Polymarket CLOB.

Kalshi 1-min candlesticks exist only inside the rolling ~60-day historical
window, so the joint minute-level sample is games since the cutoff (2026-05-25:
MLB/WNBA season + NBA/NHL finals tails). One candlestick call + one free CLOB
prices-history call (fidelity=1) per game, home side both venues. Long output:
one row per (game, minute-to-start) with the last observation in that minute;
gaps left for the analysis layer to fill. Resumable by game_id.
"""
from __future__ import annotations

import os
import time

import pandas as pd
import requests

from src.collect.kalshi import LEAGUE_SERIES
from src.collect.kalshi_prices import _candles, _dollars
from src.collect.kalshi_hist_prices import _rule_home

OUT = "data/processed/minute_paths.csv"
WINDOW_MIN = 360
CUTOFF = "2026-05-26"
C = "https://clob.polymarket.com"
_session = requests.Session()


def sample():
    m = pd.read_csv("data/processed/games_master.csv")
    m = m[m.outcome.notna() & ~m.outcome_disagree.fillna(False)
          & m.kalshi_p1.notna() & m.poly_p1.notna()].copy()
    m = m[pd.to_datetime(m.start_utc, utc=True, format="ISO8601")
          >= pd.Timestamp(CUTOFF, tz="UTC")]
    tok = pd.read_csv("data/processed/poly_token_map_full.csv")[["game_id", "token_home"]]
    mt = pd.read_csv("data/processed/kalshi_espn_matches.csv")[["espn_id", "event_ticker"]]
    kk = pd.read_csv("data/processed/kalshi_settled_markets.csv")[["event_ticker", "ticker"]]
    m = (m.merge(tok, on="game_id").merge(
        mt.rename(columns={"espn_id": "game_id"}), on="game_id"))
    rows = []
    for r in m.itertuples(index=False):
        sides = kk[kk.event_ticker == r.event_ticker]["ticker"].tolist()
        codes = sorted({t.rsplit("-", 1)[-1] for t in sides})
        rh = _rule_home(r.event_ticker, codes) if len(codes) == 2 else None
        tk = next((t for t in sides if rh and t.endswith("-" + rh)), None)
        if tk:
            rows.append({"game_id": r.game_id, "league": r.league, "start_utc": r.start_utc,
                         "ticker": tk, "token": r.token_home})
    return pd.DataFrame(rows)


def kalshi_minutes(ticker, league, start_ts):
    cs = _candles(ticker, LEAGUE_SERIES[league], start_ts - WINDOW_MIN * 60, start_ts, interval=1)
    out = {}
    for c in cs:
        ts = c.get("end_period_ts", 0)
        if not (start_ts - WINDOW_MIN * 60 <= ts <= start_ts):
            continue
        yb, ya = _dollars(c.get("yes_bid")), _dollars(c.get("yes_ask"))
        if yb is not None and ya is not None and ya >= yb > 0:
            out[(start_ts - ts) // 60] = round((yb + ya) / 2, 4)
    return out


def poly_minutes(token, start_ts):
    r = _session.get(f"{C}/prices-history", params={
        "market": token, "startTs": start_ts - WINDOW_MIN * 60 - 60,
        "endTs": start_ts, "fidelity": 1}, timeout=30)
    if r.status_code != 200:
        return {}
    out = {}
    for p in r.json().get("history", []):
        if start_ts - WINDOW_MIN * 60 <= p["t"] <= start_ts:
            out[(start_ts - p["t"]) // 60] = float(p["p"])
    return out


def build(out=OUT):
    g = sample()
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    todo = g[~g.game_id.isin(done)]
    print(f"{len(g)} eligible games, {len(todo)} to fetch", flush=True)
    buf, n_ok = [], 0
    for i, r in enumerate(todo.itertuples(index=False), 1):
        start_ts = int(pd.Timestamp(r.start_utc).timestamp())
        km = kalshi_minutes(r.ticker, r.league, start_ts)
        pm = poly_minutes(r.token, start_ts)
        if km and pm:
            n_ok += 1
            for mts in sorted(set(km) | set(pm)):
                buf.append({"game_id": r.game_id, "league": r.league,
                            "start_utc": r.start_utc, "mts": int(mts),
                            "k_mid": km.get(mts), "p_price": pm.get(mts)})
        if buf and (i % 25 == 0 or i == len(todo)):
            df = pd.DataFrame(buf)
            hdr = not os.path.exists(out)
            df.to_csv(out, mode="a", header=hdr, index=False)
            buf = []
            print(f"  {i}/{len(todo)} games ({n_ok} with both series)", flush=True)
        time.sleep(0.15)
    print(f"done: {n_ok} joint games -> {out}", flush=True)


if __name__ == "__main__":
    build()
