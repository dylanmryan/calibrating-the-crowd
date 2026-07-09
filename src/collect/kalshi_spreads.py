"""Kalshi alternate-spread ladders -> per-threshold pre-game prices (free, Kalshi only).

Each spread event (e.g. KXNBASPREAD-26MAY07LALOKC) holds many threshold contracts
("LAL wins by over 4.5?"), independently priced. We price every threshold at the
official start (book-mid via 1-min candles, trade-recon fallback) to reconstruct
each game's implied probability curve over margin of victory.

Start times come from the existing Kalshi<->ESPN match table: a spread event's
ticker suffix (date+teams[, time]) equals its moneyline sibling's suffix, so we
join through the corresponding KX<LG>GAME event.
"""
from __future__ import annotations

import os
import re
import pandas as pd

from src.collect.kalshi_prices import closing_book_price
from src.collect.kalshi_hist_prices import closing_trade_price
from src.collect.kalshi import fetch_settled_markets  # paginated live+historical

SPREAD_TO_GAME = {
    "KXNBASPREAD": ("NBA", "KXNBAGAME"),
    "KXWNBASPREAD": ("WNBA", "KXWNBAGAME"),
    "KXMLBSPREAD": ("MLB", "KXMLBGAME"),
    "KXNHLSPREAD": ("NHL", "KXNHLGAME"),
}


def _suffix(event_ticker: str) -> str:
    return event_ticker.split("-", 1)[1] if "-" in event_ticker else ""


def _parse_side(ticker: str):
    """KXNBASPREAD-26MAY07LALOKC-LAL4 -> (team='LAL', threshold=4.5)."""
    m = re.match(r".+-([A-Z]+)(\d+)$", ticker)
    if not m:
        return None, None
    return m.group(1), int(m.group(2)) + 0.5


def build(out="data/processed/kalshi_spread_prices.csv", flush_every=300) -> None:
    matches = pd.read_csv("data/processed/kalshi_espn_matches.csv")
    matches = matches[matches.matched & matches.start_utc.notna()]
    # game-event suffix -> (espn_id, start_utc)
    lookup = {}
    for r in matches.itertuples(index=False):
        lookup[_suffix(r.event_ticker)] = (r.espn_id, r.start_utc)

    done = set()
    if os.path.exists(out):
        done = set(pd.read_csv(out)["ticker"])

    rows, n_priced = [], 0
    for sseries, (lg, gseries) in SPREAD_TO_GAME.items():
        mk = fetch_settled_markets(sseries)
        mk = [m for m in mk if m.get("ticker") not in done]
        print(f"{sseries}: {len(mk)} unpriced settled markets", flush=True)
        for m in mk:
            ev, tk = m.get("event_ticker", ""), m.get("ticker", "")
            hit = lookup.get(_suffix(ev))
            if not hit:
                continue
            espn_id, start_utc = hit
            team, thr = _parse_side(tk)
            if team is None:
                continue
            px = closing_book_price(tk, sseries, start_utc)
            src = "book-mid"
            if not px:
                px = closing_trade_price(tk, start_utc)
                src = "trade-recon" if px else None
            if not px:
                continue
            won = 1 if m.get("result") == "yes" else 0
            rows.append({"league": lg, "event_ticker": ev, "ticker": tk,
                         "game_id": espn_id, "start_utc": start_utc,
                         "team": team, "threshold": thr,
                         "prob": px["mid"],
                         "yes_bid": px.get("yes_bid"), "yes_ask": px.get("yes_ask"),
                         "spread_w": px.get("spread"), "stale_min": px.get("staleness_min"),
                         "src": src, "won": won})
            n_priced += 1
            if len(rows) >= flush_every:
                _append(out, rows); rows = []
                print(f"  ...{n_priced} priced", flush=True)
    if rows:
        _append(out, rows)
    print(f"done: {n_priced} threshold contracts priced -> {out}", flush=True)


def _append(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(rows)
    if os.path.exists(path):
        df = pd.concat([pd.read_csv(path), df], ignore_index=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    build()
