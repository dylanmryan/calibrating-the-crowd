"""Build data/processed/analysis_core.csv — the one committed, human-readable table.

This is the file an advisor or referee opens first, and the one the tour notebook
and report_figures.py read: one row per game, every venue's home-side probability
side by side, plus the flag that reproduces the headline sample.

It had been assembled by hand, which meant it silently went stale the moment the
master was rebuilt (it still held 9,419 rows after the 2026-08-11 re-harvest
produced 9,778). Having it as a script makes it regenerable alongside everything
else, and keeps the committed dataset honest.

Columns, deliberately plain-language rather than pipeline-internal:
  game_id, league, start_utc, home_team, away_team
  kalshi_home_prob, polymarket_home_prob   — exchange closes at official start
  book_home_prob_devig                     — consensus close, multiplicative de-vig
  book_home_prob_raw / book_away_prob_raw  — the vigged quotes they came from
  book_count                               — books in the consensus
  book_home_prob_t24h                      — consensus 24h before start
  pinnacle_home_prob / betfair_home_prob   — the sharp benchmarks (de-vigged)
  home_won                                 — 1/0 outcome
  clean_set                                — resolved and no cross-source outcome
                                             disagreement; the three-way headline
                                             is this flag AND all three prices
"""
from __future__ import annotations

import pandas as pd

OUT = "data/processed/analysis_core.csv"
SHARP = {"pinnacle": "pinnacle_home_prob", "betfair_ex_eu": "betfair_home_prob"}


def _devig(p1, p2):
    """Multiplicative de-vig, the project default for headline book probs."""
    tot = p1 + p2
    return p1 / tot.where(tot > 0)


def build(out=OUT) -> pd.DataFrame:
    m = pd.read_csv("data/processed/games_master.csv")
    core = pd.DataFrame({
        "game_id": m.game_id,
        "league": m.league,
        "start_utc": m.start_utc,
        "home_team": m.team1,
        "away_team": m.team2,
        "kalshi_home_prob": m.kalshi_p1,
        "polymarket_home_prob": m.poly_p1,
        "book_home_prob_devig": m.book_p1,
        "book_count": m.book_n_books,
        "home_won": m.outcome.map({1: 1, 2: 0}),
        # resolved AND no source disagrees with ESPN on who won
        "clean_set": m.outcome.notna() & ~m.outcome_disagree.fillna(False).astype(bool),
    })

    bk = pd.read_csv("data/processed/sportsbook_hist_prices.csv")[
        ["game_id", "book_raw1", "book_raw2"]].rename(
        columns={"book_raw1": "book_home_prob_raw", "book_raw2": "book_away_prob_raw"})
    core = core.merge(bk.drop_duplicates("game_id"), on="game_id", how="left")

    op = pd.read_csv("data/processed/sportsbook_open_prices.csv")[
        ["game_id", "book24_p1"]].rename(columns={"book24_p1": "book_home_prob_t24h"})
    core = core.merge(op.drop_duplicates("game_id"), on="game_id", how="left")

    sh = pd.read_csv("data/processed/sportsbook_sharp_prices.csv")
    for book, col in SHARP.items():
        b = sh[sh.book == book].drop_duplicates("game_id")
        b = b.assign(**{col: _devig(b.raw_p1, b.raw_p2)})[["game_id", col]]
        core = core.merge(b, on="game_id", how="left")

    core = core.sort_values(["start_utc", "game_id"]).reset_index(drop=True)
    core.to_csv(out, index=False)

    three = core.clean_set & core[["kalshi_home_prob", "polymarket_home_prob",
                                   "book_home_prob_devig"]].notna().all(axis=1)
    print(f"wrote {out}: {len(core):,} games", flush=True)
    print(f"  clean_set                 {int(core.clean_set.sum()):,}", flush=True)
    print(f"  three-way headline sample {int(three.sum()):,}", flush=True)
    for c in ("kalshi_home_prob", "polymarket_home_prob", "book_home_prob_devig",
              "book_home_prob_t24h", "pinnacle_home_prob", "betfair_home_prob"):
        print(f"  {c:26} {int(core[c].notna().sum()):,}", flush=True)
    return core


if __name__ == "__main__":
    build()
