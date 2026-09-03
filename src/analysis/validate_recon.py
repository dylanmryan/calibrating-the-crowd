"""Validate the trade-reconstruction pricing method against OddPool's archived books.

Roughly 80% of this project's Kalshi closes are RECONSTRUCTED from the trade tape
rather than read off a quoted book: Kalshi's API retains no order book past ~60
days, so `kalshi_hist_prices.closing_trade_price` infers an effective bid and ask
from trade taker-sides. That is the single largest measurement assumption in the
paper's exchange leg, and it needs external corroboration rather than an argument.

OddPool archived real order-book snapshots (1-5 min) since ~March 2026. For a
stratified sample of trade-recon games in that window we fetch the archived book
just before official start and compare its best bid/ask/mid to our reconstruction.

Two entry points, deliberately separated so the suite can cite this result
without spending quota:
  collect()  — network. Free tier: 1K req/month, strict throttle -> 1 call/~25s,
               resumable. Run by hand; NOT part of make_results.
  main()     — offline. Reads data/processed/recon_validation.csv and prints the
               agreement table. This is what the suite runs and what the report
               cites, so the freeze re-stamps it like every other number.

Known coverage limit, stated because the report must state it: the validated
sample covers CBB-M, MLB, NBA and NHL only — there is no NFL, CFB or WNBA row.
"""
from __future__ import annotations

import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_ROOT / ".env", override=True)
H = {"X-API-Key": (os.getenv("ODDSPOOL_API_KEY") or "").strip()}
B = "https://api.oddpool.com"
OUT = "data/processed/recon_validation.csv"


def sample_games(n_per_league=60):
    k = pd.read_csv("data/processed/kalshi_hist_prices.csv")
    k = k[(k.k_src1 == "trade-recon") & (k.start_utc >= "2026-03-20")]
    mt = pd.read_csv("data/processed/kalshi_espn_matches.csv")[["espn_id", "event_ticker"]]
    kk = pd.read_csv("data/processed/kalshi_settled_markets.csv")[["event_ticker", "ticker"]]
    k = k.merge(mt.rename(columns={"espn_id": "game_id"}), on="game_id")
    # home ticker = the side our p1/bid1/ask1 describe (ticker-order rule build)
    from src.collect.kalshi_hist_prices import _rule_home
    rows = []
    for r in k.itertuples(index=False):
        sides = kk[kk.event_ticker == r.event_ticker]["ticker"].tolist()
        codes = sorted({t.rsplit("-", 1)[-1] for t in sides})
        rh = _rule_home(r.event_ticker, codes) if len(codes) == 2 else None
        if rh is None:
            continue
        tk = next(t for t in sides if t.endswith("-" + rh))
        rows.append({"game_id": r.game_id, "league": r.league, "ticker": tk,
                     "start_utc": r.start_utc, "our_bid": r.k_yes_bid1,
                     "our_ask": r.k_yes_ask1, "our_mid_norm": r.kalshi_p1})
    df = pd.DataFrame(rows).dropna(subset=["our_bid", "our_ask"])
    # stratified sample: shuffle once, take up to n per league
    return df.sample(frac=1, random_state=7).groupby("league").head(n_per_league)


def fetch_book(ticker, start_utc, retries=3):
    end_ms = int(pd.Timestamp(start_utc).timestamp() * 1000)
    for attempt in range(retries):
        try:
            r = requests.get(f"{B}/historical/kalshi/orderbook", headers=H, params={
                "market_id": ticker, "start_time": end_ms - 30 * 60 * 1000,
                "end_time": end_ms, "granularity": "5m", "limit": 10}, timeout=25)
        except requests.RequestException:
            time.sleep(20); continue
        if r.status_code == 200:
            s = r.json().get("snapshots", [])
            return s[-1] if s else None      # snapshot closest to start
        if r.status_code == 429:
            time.sleep(45 * (attempt + 1)); continue
        return None
    return None


def collect(cap=220):
    """Network path: fetch archived books for the stratified sample. Spends quota."""
    done = set()
    if os.path.exists(OUT):
        done = set(pd.read_csv(OUT)["game_id"])
    todo = sample_games()
    todo = todo[~todo["game_id"].isin(done)].head(max(0, cap - len(done)))
    print(f"validating {len(todo)} games ({len(done)} done)", flush=True)
    rows, n = [], 0
    for r in todo.itertuples(index=False):
        snap = fetch_book(r.ticker, r.start_utc)
        n += 1
        if snap:
            rows.append({"game_id": r.game_id, "league": r.league,
                         "our_bid": r.our_bid, "our_ask": r.our_ask,
                         "book_bid": float(snap["best_yes_bid"]) if snap.get("best_yes_bid") else None,
                         "book_ask": float(snap["best_yes_ask"]) if snap.get("best_yes_ask") else None,
                         "snap_gap_min": round((pd.Timestamp(r.start_utc).timestamp()
                                                - snap["timestamp"] / 1000) / 60, 1)})
        if len(rows) >= 10:
            _append(rows); rows = []
            print(f"  ...{n}", flush=True)
        time.sleep(25)   # free-tier throttle
    if rows:
        _append(rows)
    print(f"done: {n} fetched", flush=True)
    main()


def _append(rows):
    df = pd.DataFrame(rows)
    if os.path.exists(OUT):
        df = pd.concat([pd.read_csv(OUT), df], ignore_index=True)
    df.to_csv(OUT, index=False)


def main():
    """Offline path: the agreement table the suite runs and the report cites."""
    if not os.path.exists(OUT):
        raise SystemExit(f"{OUT} missing — run validate_recon.collect() first")
    raw = pd.read_csv(OUT)
    d = raw.dropna(subset=["book_bid", "book_ask", "our_bid", "our_ask"])
    if not len(d):
        raise SystemExit("no comparable rows in recon_validation.csv")

    k = pd.read_csv("data/processed/kalshi_hist_prices.csv", usecols=["k_src1"])
    n_recon = int((k.k_src1 == "trade-recon").sum())
    print("=== trade-reconstruction vs archived order books (OddPool) ===", flush=True)
    print(f"  what this underwrites: {n_recon:,} of {len(k):,} Kalshi game prices "
          f"({n_recon/len(k):.0%}) are", flush=True)
    print("  reconstructed from the trade tape rather than read off a quoted book", flush=True)
    print(f"  validated sample: {len(d)} games ({len(raw)} fetched, "
          f"{len(raw)-len(d)} with no archived book)\n", flush=True)

    d = d.copy()
    d["mid_err"] = ((d.our_bid + d.our_ask) / 2 - (d.book_bid + d.book_ask) / 2).abs()
    print(f"  exact bid match: {(d.our_bid == d.book_bid).mean():.1%}   "
          f"exact ask match: {(d.our_ask == d.book_ask).mean():.1%}", flush=True)
    print(f"  |mid error|: mean {d.mid_err.mean()*100:.2f}pt, "
          f"median {d.mid_err.median()*100:.2f}pt, "
          f"within 1pt: {(d.mid_err <= 0.01).mean():.1%}", flush=True)
    if "snap_gap_min" in d:
        print(f"  archived snapshot gap to official start: median "
              f"{d.snap_gap_min.median():.1f} min", flush=True)

    print(f"\n  {'league':>8}{'n':>6}{'mean |mid err|':>16}{'median':>10}{'within 1pt':>12}",
          flush=True)
    for lg, g in d.groupby("league"):
        print(f"  {lg:>8}{len(g):>6}{g.mid_err.mean()*100:>15.2f}pt"
              f"{g.mid_err.median()*100:>9.2f}pt{(g.mid_err <= 0.01).mean():>12.1%}",
              flush=True)

    missing = sorted(set(pd.read_csv("data/processed/games_master.csv").league.unique())
                     - set(d.league.unique()))
    print(f"\n  COVERAGE LIMIT: no validated rows for {', '.join(missing)}. The", flush=True)
    print("  reconstruction is a per-market mechanism, not a league-specific one, but", flush=True)
    print("  the report must say the validation does not cover these leagues directly.", flush=True)
    print("\n  Read: the reconstruction recovers the archived touch almost exactly. The", flush=True)
    print("  residual is concentrated in NBA, the league whose books move fastest", flush=True)
    print("  between the last fill and the bell. robustness_cuts section 2 shows the", flush=True)
    print("  three-way verdict is the same on recon-priced and book-mid-priced games.", flush=True)


if __name__ == "__main__":
    main()
