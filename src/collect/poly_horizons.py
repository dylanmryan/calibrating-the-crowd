"""Polymarket multi-horizon price paths (T-24h -> start), one free CLOB call/game.

Mirrors kalshi_horizons: home-token minute-level prices-history over the final
24h, sampled at the same 7 horizons. Feeds the horizon-resolved three-way
equivalence ("when does the dead heat form?").
"""
from __future__ import annotations

import os
import time

import pandas as pd
import requests

_session = requests.Session()
C = "https://clob.polymarket.com"
OUT = "data/processed/poly_horizons.csv"
HORIZONS_MIN = [1440, 720, 360, 180, 60, 15, 0]


def path_prices(token: str, start_epoch: int) -> dict | None:
    r = _session.get(f"{C}/prices-history", params={
        "market": token, "startTs": start_epoch - 24 * 3600 - 600,
        "endTs": start_epoch, "fidelity": 1}, timeout=30)
    if r.status_code != 200:
        return None
    h = [p for p in r.json().get("history", []) if p["t"] <= start_epoch]
    if not h:
        return None
    out = {"n_points": len(h)}
    for hm in HORIZONS_MIN:
        cut = start_epoch - hm * 60
        past = [p for p in h if p["t"] <= cut]
        out[f"q_h{hm}"] = float(past[-1]["p"]) if past else None
    return out


def build(map_path="data/processed/poly_token_map_full.csv", out=OUT):
    mp = pd.read_csv(map_path)
    done = set(pd.read_csv(out)["game_id"]) if os.path.exists(out) else set()
    todo = mp[~mp.game_id.isin(done)]
    print(f"fetching poly paths for {len(todo):,} games ({len(done)} done)", flush=True)
    rows, n = [], 0
    for r in todo.itertuples(index=False):
        p = path_prices(r.token_home, int(pd.Timestamp(r.start_utc).timestamp()))
        n += 1
        if p:
            rows.append({"game_id": r.game_id, "league": r.league,
                         "start_utc": r.start_utc, **p})
        if len(rows) >= 200:
            _flush(out, rows); rows = []
            print(f"  ...{n}", flush=True)
        time.sleep(0.12)
    _flush(out, rows)
    print(f"done: {n} fetched", flush=True)


def _flush(path, rows):
    if not rows:
        return
    df = pd.DataFrame(rows)
    if os.path.exists(path):
        df = pd.concat([pd.read_csv(path), df], ignore_index=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    build()
