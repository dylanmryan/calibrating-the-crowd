"""Spread-ladder threshold conventions, which differ by league.

Getting this wrong does not produce an error; it silently shifts an entire
implied margin distribution by one unit, which reads downstream as a market
mispricing. It did: the +8.4pt "MLB under-prices 1-2 run margins" result was
this bug, not the market.

Kalshi settles a spread contract at threshold t as:

  NBA, NHL   (half-point spreads)     side wins by MORE THAN t   ->  sm >  t
  MLB, WNBA  (integer run/goal lines) side wins by t-0.5 OR MORE ->  sm >= t-0.5

Verified against Kalshi's own settlement field (`result`, collected by
src/collect/kalshi_spreads.py) on 25,146 contracts joined to ESPN finals:

  league-specific rule   99.87%   (MLB 99.58 / NBA 100.00 / NHL 99.98 / WNBA 100.00)
  single `sm > t` rule   97.80%   (error concentrated in MLB: 7.22% of its rows,
                                   at thresholds 2.5/3.5/4.5 -- exactly the rungs
                                   the distributional claims are built on)

Everything downstream should go through cover_line(): the smallest signed
margin, for the contract's OWN side, that wins the contract. That single
number makes the two conventions interchangeable, and it is also the natural
key for joining to the books' alternate-spread lines.

The totals ladder (kalshi_total_prices.csv) was checked the same way and is
uniform -- `total > t` reproduces settlement 99.76% overall and 99.5-100% in
every league -- so totals need no adjustment.
"""
from __future__ import annotations

import numpy as np

# Leagues whose spread markets are quoted on integer run/goal lines, where a
# threshold of t means "wins by t-0.5 or more" rather than "wins by more than t".
INTEGER_LINE_LEAGUES = frozenset({"MLB", "WNBA"})

# Sentinel for sportsbook ladders. Books quote the line itself in every sport,
# so they always follow the "wins by more than t" branch; passing this instead
# of a real league name makes that explicit at the call site.
BOOK = "__book__"


def cover_line(league: str, threshold: float) -> float:
    """Smallest signed margin (contract's own side) that wins this contract.

    Margins are integers, so "wins by more than t" for half-integer t is the
    same event as "wins by t+0.5 or more"; expressing both conventions as a
    minimum winning margin removes the difference.
    """
    t = float(threshold)
    return t - 0.5 if league in INTEGER_LINE_LEAGUES else t + 0.5


def book_cover_line(threshold: float) -> float:
    """Same quantity for a book alternate-spread line.

    Books quote the line itself: a side at -t covers iff it wins by more than
    t, so the smallest winning integer margin is floor(t) + 1. That reduces to
    t + 0.5 on the half-point lines and stays correct on the integer lines,
    where t itself is a push rather than a win.

    Integer lines are fine for placing a CDF point but must NOT be joined to
    Kalshi rungs: "wins by more than 3, push at 3" is not the event "wins by
    4 or more", even though both have the same smallest winning margin. Use
    is_push_line() to drop them before any join.

    Accepts a scalar or an array/Series.
    """
    return np.floor(threshold) + 1


def is_push_line(threshold) -> bool:
    """True for a whole-number book line, where the margin can land on the line."""
    return np.asarray(threshold) % 1 == 0


def resolves(league: str, signed_margin: float, threshold: float) -> bool:
    """Did this contract settle YES, given the side's signed margin?"""
    return float(signed_margin) >= cover_line(league, threshold)


def cdf_x_home(league: str, threshold: float) -> float:
    """x at which a HOME-side contract pins F(x) = 1 - p, for F over M = home - away.

    P(contract) = P(M >= cover) = 1 - F(cover - 1).
    """
    return cover_line(league, threshold) - 1.0


def cdf_x_away(league: str, threshold: float) -> float:
    """x at which an AWAY-side contract pins F(x) = p, for F over M = home - away.

    P(contract) = P(-M >= cover) = P(M <= -cover) = F(-cover).
    """
    return -cover_line(league, threshold)


def _self_test() -> None:
    """Re-derive the conventions from settlement data. Run as a module."""
    import numpy as np
    import pandas as pd

    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    esp = pd.read_csv("data/processed/espn_games.csv")
    sp["game_id"] = pd.to_numeric(sp.game_id, errors="coerce")
    esp["espn_id"] = pd.to_numeric(esp.espn_id, errors="coerce")
    m = sp.merge(esp[["espn_id", "home_abbr", "away_abbr", "home_score", "away_score"]],
                 left_on="game_id", right_on="espn_id", how="inner")
    m = m[(m.team == m.home_abbr) | (m.team == m.away_abbr)].copy()
    m["sm"] = np.where(m.team == m.home_abbr,
                       m.home_score - m.away_score, m.away_score - m.home_score)

    rule = [resolves(lg, sm, t) for lg, sm, t in zip(m.league, m.sm, m.threshold)]
    agree = (np.asarray(rule).astype(int) == m.won.values).mean()
    naive = ((m.sm > m.threshold).astype(int) == m.won).mean()
    print(f"contracts checked: {len(m):,}")
    print(f"  league-specific cover_line() : {100*agree:.2f}%")
    print(f"  single 'sm > threshold' rule : {100*naive:.2f}%")
    for lg, g in m.groupby("league"):
        r = np.asarray([resolves(lg, sm, t) for sm, t in zip(g.sm, g.threshold)]).astype(int)
        print(f"    {lg:5s} n={len(g):6,}  {100*(r == g.won.values).mean():6.2f}%")
    assert agree > 0.995, f"convention self-test failed at {agree:.4f}"
    print("  self-test PASSED")


if __name__ == "__main__":
    _self_test()
