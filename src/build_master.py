"""Merge Kalshi + Polymarket historical prices + ESPN outcomes -> games_master.csv.

Produces the target per-game schema:
  sport, league, game_id, date, start_utc, team1(home), team2(away),
  kalshi_p1/p2, poly_p1/p2, outcome (1=home won, 2=away won), + quality/source flags.
Cross-checks each platform's implied winner against the ESPN result and flags disagreements.
"""
from __future__ import annotations

import pandas as pd
from src.match.kalshi_espn import espn_games

SPORT = {"MLB": "Baseball", "NBA": "Basketball", "WNBA": "Basketball",
         "CBB-M": "Basketball", "NFL": "Football", "CFB": "Football", "NHL": "Hockey"}


def build(out="data/processed/games_master.csv") -> pd.DataFrame:
    esp = espn_games()
    base = pd.DataFrame({
        "game_id": esp["espn_id"], "league": esp["league"],
        "date": pd.to_datetime(esp["start_utc"], utc=True, format="ISO8601").dt.date,
        "start_utc": esp["start_utc"], "team1": esp["home_team"], "team2": esp["away_team"],
        "outcome": esp["winner"].map({"home": 1, "away": 2}),
    })
    base["sport"] = base["league"].map(SPORT)

    kal = _load("data/processed/kalshi_hist_prices.csv",
                ["game_id", "kalshi_p1", "kalshi_p2", "k_src1", "k_src2",
                 "k_spread1", "k_spread2", "k_stale1", "k_stale2"])
    poly = _load("data/processed/polymarket_hist_prices.csv",
                 ["game_id", "poly_p1", "poly_p2", "poly_stale1", "poly_stale2", "poly_outcome"])
    book = _load("data/processed/sportsbook_hist_prices.csv",
                 ["game_id", "book_p1", "book_p2", "book_n_books"])

    m = (base.merge(kal, on="game_id", how="left")
             .merge(poly, on="game_id", how="left")
             .merge(book, on="game_id", how="left"))
    m = m.merge(_kalshi_outcome(esp), on="game_id", how="left")

    # keep games priced by at least one source
    m = m[m["kalshi_p1"].notna() | m["poly_p1"].notna() | m["book_p1"].notna()].copy()

    # data-integrity: cross-check ESPN outcome against each platform's settlement.
    # kalshi_disagree flags series-day mismatches (price on wrong game of a series).
    m["poly_disagree"] = (m["poly_outcome"].notna() & (m["poly_outcome"] != m["outcome"]))
    m["kalshi_disagree"] = (m["k_outcome"].notna() & (m["k_outcome"] != m["outcome"]))
    # venue flags: ticker-order home != ESPN home -> wrong-night match risk (repair_sides.py)
    try:
        vf = set(pd.read_csv("data/processed/venue_flags.csv")["game_id"])
    except FileNotFoundError:
        vf = set()
    m["venue_disagree"] = m["game_id"].isin(vf)
    m["outcome_disagree"] = m["poly_disagree"] | m["kalshi_disagree"] | m["venue_disagree"]

    cols = ["sport", "league", "game_id", "date", "start_utc", "team1", "team2",
            "kalshi_p1", "kalshi_p2", "poly_p1", "poly_p2", "book_p1", "book_p2", "outcome",
            "k_src1", "k_src2", "k_spread1", "k_spread2", "k_stale1", "k_stale2",
            "poly_stale1", "poly_stale2", "book_n_books",
            "poly_disagree", "kalshi_disagree", "outcome_disagree"]
    m = m[[c for c in cols if c in m.columns]]
    m.to_csv(out, index=False)

    both = m["kalshi_p1"].notna() & m["poly_p1"].notna()
    three = both & m["book_p1"].notna()
    print(f"master rows: {len(m):,}  (kalshi={m['kalshi_p1'].notna().sum():,}, "
          f"poly={m['poly_p1'].notna().sum():,}, book={m['book_p1'].notna().sum():,}, "
          f"K+P={both.sum():,}, all-three={three.sum():,})", flush=True)
    print(f"unresolved (null outcome, excludable): {m['outcome'].isna().sum()}", flush=True)
    print("\nby league (both platforms):", flush=True)
    print(m[both].groupby("league").size().to_string(), flush=True)
    print(f"\noutcome cross-check flags: poly-disagree={int(m.poly_disagree.sum())}, "
          f"kalshi-disagree={int(m.kalshi_disagree.sum())}, "
          f"any={int(m.outcome_disagree.sum())} ({m.outcome_disagree.mean():.1%})", flush=True)
    clean = m[m["outcome"].notna() & ~m["outcome_disagree"]]
    print(f"clean rows (resolved + no disagreement): {len(clean):,}", flush=True)
    return m


def _kalshi_outcome(esp):
    """Kalshi's own settlement winner per game_id (home=1/away=2), for cross-checking ESPN."""
    from src.match.kalshi_espn import kalshi_games, learn_aliases, ALIASES
    learn_aliases(kalshi_games(), esp)

    def norm(c, lg):
        return ALIASES.get(lg, {}).get(str(c), str(c))
    k = pd.read_csv("data/processed/kalshi_settled_markets.csv")
    k["code"] = k["ticker"].str.rsplit("-", n=1).str[-1]
    win = (k[k["won"] == 1].groupby("event_ticker")
           .agg(code=("code", "first"), league=("league", "first")).reset_index())
    mt = pd.read_csv("data/processed/kalshi_espn_matches.csv")[["event_ticker", "espn_id"]]
    win = win.merge(mt, on="event_ticker").merge(
        esp[["espn_id", "home_abbr", "away_abbr"]], on="espn_id")
    win["k_outcome"] = win.apply(
        lambda r: 1 if norm(r.code, r.league) == norm(r.home_abbr, r.league) else 2, axis=1)
    return (win.groupby("espn_id")["k_outcome"].first().reset_index()
            .rename(columns={"espn_id": "game_id"}))


def _load(path, cols):
    try:
        # residual doubleheader collisions can map two markets to one game_id;
        # keep the first so the merge stays 1 row per game
        return pd.read_csv(path)[cols].drop_duplicates("game_id", keep="first")
    except FileNotFoundError:
        return pd.DataFrame(columns=cols)


if __name__ == "__main__":
    build()
