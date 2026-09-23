"""Was the book handicapped by a stale price? The paper's timing caveat, measured.

The design has always carried an asymmetry, conceded in `docs/findings.md` under
Caveats & scope and never quantified:

    "Book lines sampled up to 60 min before start (credit-batching);
     prediction-market prices at start. Any late-news asymmetry slightly
     FAVORS the markets."

That is the most exploitable sentence in the paper. It hands a referee the reply
"the exchanges only tie the books because the book prices are up to an hour
stale," and the answer to date has been a hand-wave in the direction of "slightly."

It does not have to be. Both per-book tapes carry each bookmaker's own
`last_update`, so the age of the quote that built the consensus is known per
game — and the collection cadence makes that age strongly BIMODAL (about half
the games priced within ~5 minutes of start, a third more than half an hour
out). The split is an artifact of credit-batching, not of anything about the
games, which is what makes it usable: it is a natural experiment in how stale
the benchmark was, and the paper's headline can simply be re-run inside each arm.

S1 establishes the split and checks that the timestamps belong to the price the
paper actually uses. S2 re-runs the dead heat inside each arm, against the US
consensus and against Pinnacle, with MDEs, plus a direct test of whether the
differential moves with freshness at all. S3 asks the one PER-BOOK timing
question a closing cross-section can answer. S4 states what none of it settles.

Reporting rule followed throughout: this module is not here to make the caveat
go away. If the staleness penalty is real it gets reported at its size and sign;
the claim being tested is only whether the headline equivalence survives at
MATCHED freshness, which is a narrower and more defensible statement than the
one the caveat currently concedes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.analysis.compare import brier
from src.analysis.rigor import cluster_dm, DELTA_PRESTATED
from src.analysis.power import KMDE

US = "data/processed/sportsbook_us_books.csv"
SHARP = "data/processed/sportsbook_sharp_prices.csv"
FRESH, STALE = 10.0, 30.0        # minutes before start; the gap between the modes


def _age(df):
    return ((pd.to_datetime(df.start_utc, utc=True, format="ISO8601")
             - pd.to_datetime(df.book_ts, utc=True, format="ISO8601"))
            .dt.total_seconds() / 60)


def load():
    """Master joint set + per-game book quote age + Pinnacle's own price/age."""
    m = pd.read_csv("data/processed/games_master.csv", low_memory=False)
    m = m[m.kalshi_p1.notna() & m.poly_p1.notna() & m.book_p1.notna()
          & m.outcome.notna() & ~m.outcome_disagree.fillna(False)].copy()
    m["y"] = (m.outcome == 1).astype(float)
    m["date"] = pd.to_datetime(m.start_utc, utc=True, format="ISO8601").dt.date

    u = pd.read_csv(US)
    u["age"], u["devig"] = _age(u), u.raw_p1 / (u.raw_p1 + u.raw_p2)
    g = u.groupby("game_id")
    us = g.agg(book_age=("age", "median"), age_spread=("age", lambda x: x.max() - x.min()),
               nbooks=("devig", "size"), reb=("devig", "mean")).reset_index()

    s = pd.read_csv(SHARP)
    s["age"], s["devig"] = _age(s), s.raw_p1 / (s.raw_p1 + s.raw_p2)
    pin = (s[s.book == "pinnacle"].drop_duplicates("game_id", keep="last")
           [["game_id", "devig", "age"]].rename(columns={"devig": "pinnacle",
                                                         "age": "pin_age"}))
    return m.merge(us, on="game_id", how="left").merge(pin, on="game_id", how="left"), u


def census(d, u):
    print("\n=== 1. QUOTE-AGE CENSUS: the split is the collector's, not the games' ===",
          flush=True)
    a = d.book_age.dropna()
    qs = {f"p{p}": a.quantile(p / 100) for p in (5, 25, 50, 75, 95)}
    print(f"  per-game median book quote age, minutes before start (n={len(a):,} games):",
          flush=True)
    print("    " + "  ".join(f"{k}={v:.1f}" for k, v in qs.items()), flush=True)
    print(f"    <{FRESH:.0f} min: {(a < FRESH).sum():,} games ({(a < FRESH).mean():.0%})"
          f"   |   >{STALE:.0f} min: {(a > STALE).sum():,} games ({(a > STALE).mean():.0%})"
          f"   |   between: {((a >= FRESH) & (a <= STALE)).sum():,}", flush=True)
    print("  Bimodal, with almost nothing in between — the signature of a batched", flush=True)
    print("  collector, not of a property of the games. That is what makes it usable.", flush=True)

    print(f"\n  Within-game spread (freshest vs stalest book): median "
          f"{d.age_spread.median():.1f} min, p90 {d.age_spread.quantile(.9):.1f} min.",
          flush=True)
    per = u.groupby("book").age.mean()
    print(f"  Per-book mean age spans {per.min():.1f}-{per.max():.1f} min across "
          f"{u.book.nunique()} books: the field is\n  near-synchronous within a game; "
          f"the variation that matters is BETWEEN games.", flush=True)

    # the timestamps live in a different file from book_p1 — show they are the
    # same quotes rather than assuming it
    j = d[d.reb.notna()]
    gap = (j.reb - j.book_p1).abs() * 100
    print(f"\n  Timestamp provenance: `book_p1` is built in sportsbook_hist, the "
          f"timestamps in\n  sportsbook_us_books. Rebuilding the consensus from the "
          f"timestamped file reproduces\n  `book_p1` to a median {gap.median():.3f}pt "
          f"(mean {gap.mean():.3f}, p95 {gap.quantile(.95):.3f}, corr "
          f"{j.reb.corr(j.book_p1):.5f}) on\n  {len(j):,} games — the same quotes, so the "
          f"ages below are the headline price's.", flush=True)


def _row(label, sub, a, b):
    db, se, z, p, ci = cluster_dm(sub[a], sub[b], sub.y, sub.date)
    bound, m = max(abs(ci[0]), abs(ci[1])), KMDE * se
    print(f"  {label:<34}{len(sub):>7,}{brier(sub[a], sub.y):>9.4f}{brier(sub[b], sub.y):>9.4f}"
          f"{db*1000:>+11.3f}e-3{z:>7.2f}{p:>8.3f}{bound*1000:>8.3f}e-3"
          f"{('yes' if bound < DELTA_PRESTATED else 'NO'):>6}{m*1000:>8.3f}e-3"
          f"{('' if m <= DELTA_PRESTATED else '  UNDERPOWERED')}", flush=True)
    return db, se


def interaction(d, a, b, agecol, label):
    """Does the differential MOVE with freshness? The caveat's actual claim."""
    s = d[d[agecol].notna() & ((d[agecol] < FRESH) | (d[agecol] > STALE))].copy()
    s["dsq"] = (s[a] - s.y) ** 2 - (s[b] - s.y) ** 2
    s["fresh"] = (s[agecol] < FRESH).astype(float)
    r = sm.OLS(s.dsq.values, sm.add_constant(s[["fresh"]].values)).fit(
        cov_type="cluster", cov_kwds={"groups": s.date.values})
    print(f"  {label:<40}{r.params[1]*1000:>+10.3f}e-3{r.tvalues[1]:>8.2f}"
          f"{r.pvalues[1]:>9.3f}{len(s):>9,}", flush=True)


def deadheat(d):
    print("\n=== 2. THE CAVEAT, MEASURED: the dead heat inside each freshness arm ===",
          flush=True)
    print(f"  {'comparison':<34}{'n':>7}{'BrierA':>9}{'BrierB':>9}{'dBrier(A-B)':>14}"
          f"{'z':>7}{'p':>8}{'|CI|max':>11}{'TOST':>6}{'MDE':>11}", flush=True)
    for a, an in (("kalshi_p1", "Kalshi"), ("poly_p1", "Poly")):
        for b, bn, agecol in (("book_p1", "US consensus", "book_age"),
                              ("pinnacle", "PINNACLE", "pin_age")):
            sub = d[d[b].notna() & d[agecol].notna()]
            print(f"  --- {an} vs {bn} " + "-" * 34, flush=True)
            _row(f"{an} v {bn}: all", sub, a, b)
            _row(f"{an} v {bn}: quote <{FRESH:.0f} min", sub[sub[agecol] < FRESH], a, b)
            _row(f"{an} v {bn}: quote >{STALE:.0f} min", sub[sub[agecol] > STALE], a, b)

    print("\n  Do NOT read the Brier LEVELS across arms: the fresh arm sits at 0.216 and", flush=True)
    print("  the stale arm at 0.219-0.221 because the batches caught different leagues", flush=True)
    print("  and different game difficulty, not because anyone forecasts better when the", flush=True)
    print("  book is fresh. Every differential above is computed WITHIN an arm on the", flush=True)
    print("  same games, so composition cancels there and only there.", flush=True)

    print("\n  Does the differential MOVE with freshness? (coefficient on a fresh dummy,",
          flush=True)
    print("   date-clustered.) Signs: dBrier(exchange - book) is NEGATIVE when the",
          flush=True)
    print("   exchange is the better forecast, so an exchange edge that shrinks once",
          flush=True)
    print("   the book is quoted fresh appears as a POSITIVE shift. That positive shift",
          flush=True)
    print("   is exactly what the staleness caveat predicts; its absence, or a negative",
          flush=True)
    print("   shift, would mean the handicap was imagined.", flush=True)
    print(f"  {'differential':<40}{'fresh shift':>14}{'z':>8}{'p':>9}{'n':>9}", flush=True)
    for a, an in (("kalshi_p1", "Kalshi"), ("poly_p1", "Poly")):
        interaction(d[d.book_p1.notna()], a, "book_p1", "book_age",
                    f"({an} - US consensus) when book is fresh")
        interaction(d[d.pinnacle.notna()], a, "pinnacle", "pin_age",
                    f"({an} - Pinnacle) when Pinnacle is fresh")
    print("\n  READ: report the shift at its size and sign. The question this module", flush=True)
    print("  settles is narrower than 'the caveat was wrong' — it is whether the", flush=True)
    print("  equivalence survives at MATCHED freshness, which is the arm where the", flush=True)
    print("  book is not handicapped at all. A caveat that is directionally right but", flush=True)
    print("  small and insignificant should be reported that way, not declared dead.", flush=True)


def tracks_freshest(d, u):
    """S3. The one per-book TIMING question a closing cross-section can answer."""
    print("\n=== 3. DO THE EXCHANGES SIT ON THE BOOKS THAT JUST UPDATED? ===", flush=True)
    rows = []
    for gid, g in u.groupby("game_id"):
        if len(g) < 4:
            continue
        med = g.age.median()
        f, s = g[g.age <= med], g[g.age > med]
        if not len(f) or not len(s):
            continue
        rows.append({"game_id": gid, "fresh": f.devig.mean(), "stale": s.devig.mean(),
                     "lag_min": s.age.mean() - f.age.mean()})
    f = pd.DataFrame(rows).merge(d[["game_id", "kalshi_p1", "poly_p1"]], on="game_id")
    disagree = ((f.fresh - f.stale).abs() * 100).mean()
    print(f"  Splitting each game's books at their own median timestamp: the fresher "
          f"half and\n  the staler half disagree by {disagree:.3f}pt on average "
          f"({f.lag_min.mean():.1f} min apart, n={len(f):,} games).", flush=True)
    print(f"\n  mean |exchange - fresh half| MINUS |exchange - stale half|, in points", flush=True)
    print(f"  (negative = the exchange sits closer to the books that updated most recently)",
          flush=True)
    print(f"  {'exchange':>12}{'gap':>12}{'t':>8}{'share of the fresh-stale gap':>32}", flush=True)
    for c, nm in (("kalshi_p1", "Kalshi"), ("poly_p1", "Polymarket")):
        dd = ((f[c] - f.fresh).abs() - (f[c] - f.stale).abs()) * 100
        t = dd.mean() / (dd.std() / np.sqrt(len(dd)))
        print(f"  {nm:>12}{dd.mean():>+11.3f}p{t:>8.1f}{abs(dd.mean())/disagree:>31.0%}",
              flush=True)
    print("\n  READ: both exchanges sit closer to the books that just updated, which says", flush=True)
    print("  they are priced off current information rather than off a stale field. It", flush=True)
    print("  does NOT say which moved first: an exchange that LEADS and books that catch", flush=True)
    print("  up produce the same cross-section. The effect is also small in level terms.", flush=True)


def scope():
    print("\n=== 4. WHAT THIS DOES AND DOES NOT SETTLE ===", flush=True)
    print("  SETTLES: whether the book was handicapped by a stale quote, which is the", flush=True)
    print("  paper's stated timing caveat. The headline can be read inside the arm where", flush=True)
    print("  the benchmark is quoted minutes from start, at full power.", flush=True)
    print("\n  DOES NOT SETTLE: lead-lag between books. Every price here is one closing", flush=True)
    print("  cross-section per game, so there is no series in which one book could lead", flush=True)
    print("  another. That question needs per-book time series the collector did not", flush=True)
    print("  write until 2026-09-16; see book_panel.py S5 and the limitation in the", flush=True)
    print("  report outline. S3 above is the closest a cross-section gets, and it is a", flush=True)
    print("  statement about proximity, not about precedence.", flush=True)


def main():
    d, u = load()
    print(f"BOOK QUOTE FRESHNESS — the timing caveat, measured "
          f"({d.game_id.nunique():,} joint games)", flush=True)
    census(d, u)
    deadheat(d)
    tracks_freshest(d, u)
    scope()


if __name__ == "__main__":
    main()
