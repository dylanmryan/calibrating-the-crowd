"""Kalshi total-runs/points ladders -> per-threshold pre-game prices (free, Kalshi only).

A third market layer, alongside moneylines and spreads. Each totals event (e.g.
KXMLBTOTAL-26AUG102210KCLAD) holds independently priced "Over X.5 runs scored"
contracts, and the API supplies the threshold directly as `floor_strike` with
`strike_type='greater'` — no ticker parsing, unlike the spread ladders.

Why this layer earns its collection: the project's one unexplained anomaly is
that Kalshi under-prices small MLB victory margins and fails the margin PIT
where the books pass, with walk-off/extra-inning compression as the proposed
mechanism. Totals are a different statistic over the SAME run-scoring process,
and extras push totals UP rather than compressing margins down. If the implied
totals distribution is well calibrated while margins are not, the defect is the
walk-off truncation rule specifically; if both fail, Kalshi mismodels baseball's
scoring tail generally.

Start times and game ids come from the existing Kalshi<->ESPN match table: a
totals event's ticker suffix (date+time+away+home) equals its moneyline
sibling's, so we join through the corresponding KX<LG>GAME event. Markets whose
suffix is not in the match table are skipped BEFORE any pricing call.
"""
from __future__ import annotations

import os
import pandas as pd

from src.collect.kalshi_prices import closing_book_price
from src.collect.kalshi_hist_prices import closing_trade_price
from src.collect.kalshi import fetch_settled_markets

TOTAL_TO_GAME = {
    "KXMLBTOTAL": ("MLB", "KXMLBGAME"),
    "KXNBATOTAL": ("NBA", "KXNBAGAME"),
    "KXNHLTOTAL": ("NHL", "KXNHLGAME"),
    "KXWNBATOTAL": ("WNBA", "KXWNBAGAME"),
}


def _suffix(event_ticker: str) -> str:
    return event_ticker.split("-", 1)[1] if "-" in event_ticker else ""


def _price_one(job):
    """One contract -> priced row (or None). Pure per-ticker work, thread-safe."""
    lg, tseries, ev, tk, espn_id, start_utc, thr, result = job
    px = closing_book_price(tk, tseries, start_utc)
    src = "book-mid"
    if not px:
        px = closing_trade_price(tk, start_utc)
        src = "trade-recon" if px else None
    if not px:
        return None
    return {"league": lg, "event_ticker": ev, "ticker": tk,
            "game_id": espn_id, "start_utc": start_utc,
            "threshold": thr,
            "prob": px["mid"],
            "yes_bid": px.get("yes_bid"), "yes_ask": px.get("yes_ask"),
            "spread_w": px.get("spread"), "stale_min": px.get("staleness_min"),
            "src": src,
            "won": 1 if result == "yes" else 0}


def build(out="data/processed/kalshi_total_prices.csv", workers=12,
          max_contracts=40_000) -> None:
    from concurrent.futures import ThreadPoolExecutor

    matches = pd.read_csv("data/processed/kalshi_espn_matches.csv")
    matches = matches[matches.matched & matches.start_utc.notna()]
    lookup = {}
    for r in matches.itertuples(index=False):
        lookup[_suffix(r.event_ticker)] = (r.espn_id, r.start_utc)

    done = set()
    if os.path.exists(out):
        done = set(pd.read_csv(out)["ticker"])

    work = []
    for tseries, (lg, _gseries) in TOTAL_TO_GAME.items():
        mk = fetch_settled_markets(tseries)
        mk = [m for m in mk if m.get("ticker") not in done]
        n_join = 0
        for m in mk:
            hit = lookup.get(_suffix(m.get("event_ticker", "")))
            # strike_type 'greater' => contract pays if total > floor_strike
            if (not hit or m.get("floor_strike") is None
                    or m.get("strike_type") not in (None, "greater")):
                continue
            n_join += 1
            work.append((lg, tseries, m.get("event_ticker", ""), m.get("ticker", ""),
                         hit[0], hit[1], float(m["floor_strike"]), m.get("result")))
        print(f"{tseries}: {len(mk)} unpriced settled markets, "
              f"{n_join} join a matched game", flush=True)

    work = work[:max_contracts]
    print(f"contracts to price: {len(work):,} ({len(done):,} already done)", flush=True)
    rows, n_priced = [], 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, row in enumerate(ex.map(_price_one, work), 1):
            if row is not None:
                rows.append(row); n_priced += 1
            if len(rows) >= 500:
                _append(out, rows); rows = []
            if i % 2000 == 0:
                print(f"  {i:,}/{len(work):,} ({n_priced:,} priced)", flush=True)
    if rows:
        _append(out, rows)
    print(f"done: {n_priced:,} threshold contracts priced -> {out}", flush=True)


def _append(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(rows)
    if os.path.exists(path):
        df = pd.concat([pd.read_csv(path), df], ignore_index=True)
    # cross-harvest dedupe, newest wins (the data_audit lesson)
    df = df.drop_duplicates(subset=["ticker"], keep="last")
    df.to_csv(path, index=False)


if __name__ == "__main__":
    build()
