"""Repair Kalshi side-assignment artifacts found via the profitability backtest.

Root cause: kalshi_hist_prices assigned home/away via team-code aliases; rare alias
collisions flipped sides, and home-and-home rematches sometimes matched the wrong
night's ESPN game. Fix uses the validated ticker-order rule (event pair ENDS with
the home code, 99.6% ESPN agreement, 100% in NFL/NHL/CFB/WNBA):

  1. swap p1/p2 (and raw-quote columns) where old alias assignment != ticker rule
  2. flag venue-disagree events (rule vs ESPN home) -> excluded via master flag

No API calls needed. Writes data/processed/venue_flags.csv and rewrites
kalshi_hist_prices.csv in place.
"""
from __future__ import annotations

import re
import pandas as pd

from src.match.kalshi_espn import kalshi_games, espn_games, learn_aliases, ALIASES

SWAP = [("kalshi_p1", "kalshi_p2"), ("k_yes_bid1", "k_yes_bid2"), ("k_yes_ask1", "k_yes_ask2"),
        ("k_src1", "k_src2"), ("k_spread1", "k_spread2"), ("k_stale1", "k_stale2")]


def rule_home(ev: str, codes) -> str | None:
    m = re.match(r"KX[A-Z0-9]+-(?:\d{2}[A-Z]{3}\d{2})(?:\d{4})?([A-Z]+)$", ev)
    if not m:
        return None
    ends = [c for c in codes if m.group(1).endswith(c)]
    return ends[0] if len(ends) == 1 else None


def main():
    learn_aliases(kalshi_games(), espn_games())

    def norm(c, lg):
        return ALIASES.get(lg, {}).get(str(c), str(c))

    esp = pd.read_csv("data/processed/espn_games.csv")[["espn_id", "home_abbr", "away_abbr"]]
    mt = pd.read_csv("data/processed/kalshi_espn_matches.csv")
    mm = mt[mt.matched].merge(esp, on="espn_id")
    kk = pd.read_csv("data/processed/kalshi_settled_markets.csv")
    kk["code"] = kk.ticker.str.rsplit("-", n=1).str[-1]
    scodes = kk.groupby("event_ticker")["code"].apply(lambda s: tuple(sorted(set(s)))).rename("sc")
    mm = mm.merge(scodes, on="event_ticker")

    swap_ids, flag_ids = set(), set()
    for r in mm.itertuples(index=False):
        rh = rule_home(r.event_ticker, r.sc)
        if rh is None:
            continue
        nrh, nh = norm(rh, r.league), norm(str(r.home_abbr), r.league)
        if nrh != nh:
            flag_ids.add(r.espn_id)          # venue disagreement -> wrong-game risk
            continue
        # old build logic: p1 got the code whose alias-normalization equals ESPN home
        old_p1 = next((c for c in r.sc if norm(c, r.league) == nh), None)
        if old_p1 is not None and old_p1 != rh:
            swap_ids.add(r.espn_id)          # alias collision -> flipped sides

    print(f"venue-disagree (exclude): {len(flag_ids)} games", flush=True)
    print(f"side-swap (repair): {len(swap_ids)} games", flush=True)

    pd.DataFrame({"game_id": sorted(flag_ids)}).to_csv("data/processed/venue_flags.csv", index=False)

    k = pd.read_csv("data/processed/kalshi_hist_prices.csv")
    m = k["game_id"].isin(swap_ids)
    for a, b in SWAP:
        if a in k.columns and b in k.columns:
            k.loc[m, [a, b]] = k.loc[m, [b, a]].values
    k.to_csv("data/processed/kalshi_hist_prices.csv", index=False)
    print(f"swapped {int(m.sum())} rows in kalshi_hist_prices.csv", flush=True)


if __name__ == "__main__":
    main()
