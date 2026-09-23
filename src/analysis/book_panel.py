"""Is the book consensus a clean instrument for lead-lag? (composition audit)

Every dynamic result in this paper reads one series for "the sportsbook": a
cross-book MEAN built at ingest by `collect/live_snapshot.py:book_price`, which
averages each bookmaker's implied probabilities and stores only the average and
`n_books`. Per-book live quotes were never banked. That construction is fine for
ACCURACY — the static leg unpacks it per book (`sharp_books`, `us_books`,
`robustness_cuts` S3, all four consensus rules) — but it is not obviously fine
for TIMING, and the timing leg is where contribution 1 lives.

Three ways averaging can manufacture the no-leader null, all pushing the same
direction (toward zero, which is the paper's headline):

  1. SMEARING. Books update asynchronously. A move started by one book enters
     the consensus as a ramp across several steps instead of the one-step jump
     a cross-lag regression is built to detect. Classical measurement error in
     the regressor => attenuation.
  2. COMPOSITION. `n_books` is not constant within a game. When a book joins or
     drops out, the consensus changes because its MEMBERSHIP changed, not
     because anyone repriced. That is noise injected directly into the variable
     whose timing is under test.
  3. EVENT CONTAMINATION. `book_moves.py` defines its event population as a
     consensus jump >= 2pts in one step. A membership change produces exactly
     such a jump, so the events are enriched in artifacts relative to base rate.

This module measures (2) and (3) rather than conceding them in prose, and
re-runs the event study on a constant-membership panel. It does NOT measure (1):
smearing is not separately identified without per-book series, so it stays a
stated direction of bias, not a number — and since it attenuates, it can only
make the nulls below look stronger than they are, never weaker. What this module
also cannot do is ask whether Pinnacle leads the field, for the same missing
data. S5 states that limit precisely instead of leaving it implied.

Caveat carried in the output: `n_books` equality is a LOWER BOUND on churn. One
book leaving as another joins keeps the count constant, so the "clean" panel
still contains some membership turnover. Every contamination number here is
therefore conservative in the direction of understating the problem.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from src.analysis.lead_lag import panel, SRCS
from src.analysis.book_moves import windows, decompose, W, THRESH

SNAP = "data/live/vps_mirror/snapshots.csv"
ERA5 = "2026-07-31"          # cron switched */15 -> */5


def meta(freq="15min", since=None, path=SNAP):
    """Book-side metadata per (game, step): consensus breadth and clock."""
    s = pd.read_csv(path, low_memory=False)
    s = s[(s.minutes_to_start > 0) & (s.source == "sportsbook")]
    s["t"] = pd.to_datetime(s.snapshot_utc, utc=True, format="ISO8601").dt.floor(freq)
    if since is not None:
        s = s[s.t >= pd.Timestamp(since, tz="UTC")]
    return (s.groupby(["game_id", "t"])
            .agg(n_books=("n_books", "last"), mts=("minutes_to_start", "last"),
                 p1=("p1", "last")).reset_index())


def attach(d, freq="15min", since=None):
    """Merge membership metadata onto a lead_lag panel and flag clean steps.

    same_panel — the consensus had the same number of books as one step earlier.
    NaN breadth (no book print on that step) counts as NOT clean: unverifiable
    is treated as contaminated, so the clean subsample is conservative.
    """
    g = d.sort_values(["game_id", "t"]).merge(meta(freq, since), on=["game_id", "t"],
                                              how="left")
    g["n_books_lag"] = g.groupby("game_id")["n_books"].shift(1)
    g["same_panel"] = (g.n_books == g.n_books_lag).fillna(False)
    return g


def census(freq="15min", since=None):
    """S1. How much does the book panel's membership actually move?"""
    print(f"\n=== 1. CONSENSUS MEMBERSHIP CENSUS ({freq} clock) ===", flush=True)
    m = meta(freq, since).sort_values(["game_id", "t"])
    g = m.groupby("game_id")
    m["dn"], m["dp"] = g.n_books.diff(), g.p1.diff()
    print(f"  book-side steps {len(m):,} over {m.game_id.nunique():,} games | "
          f"n_books median {m.n_books.median():.0f}, min {m.n_books.min():.0f}, "
          f"max {m.n_books.max():.0f}", flush=True)
    rng = g.n_books.agg(lambda x: x.max() - x.min())
    print(f"  within-game breadth range: mean {rng.mean():.2f}, median {rng.median():.0f} | "
          f"games with ANY change {(rng > 0).mean():.1%}, with >=3 {(rng >= 3).mean():.1%}",
          flush=True)

    st = m[m.dn.notna() & m.dp.notna()]
    chg, same = st[st.dn != 0], st[st.dn == 0]
    print(f"\n  steps with a membership change: {(st.dn != 0).mean():.1%} "
          f"({len(chg):,} of {len(st):,})", flush=True)
    print(f"  mean |consensus move| when membership CHANGED : {chg.dp.abs().mean()*100:>5.2f} pts", flush=True)
    print(f"  mean |consensus move| when membership CONSTANT: {same.dp.abs().mean()*100:>5.2f} pts", flush=True)
    if same.dp.abs().mean() > 0:
        print(f"  ratio: {chg.dp.abs().mean()/same.dp.abs().mean():.1f}x", flush=True)
    # exact share of total squared variation, not a mean-centred variance
    # decomposition: the changes are near-zero-mean, but "sum of squares" needs
    # no such assumption and is what the sentence in the paper claims.
    share = (chg.dp ** 2).sum() / (st.dp ** 2).sum()
    print(f"  share of the consensus-change series' total squared variation carried by "
          f"those\n  {(st.dn != 0).mean():.1%} of steps: {share:.1%}", flush=True)

    print("\n  churn by time-to-start (the headline horizon results live inside 2h):", flush=True)
    b = st.assign(bucket=pd.cut(st.mts, [0, 60, 120, 240, 480, np.inf],
                                labels=["0-60m", "1-2h", "2-4h", "4-8h", ">8h"]))
    tab = b.groupby("bucket", observed=True).agg(
        steps=("dn", "size"), churn=("dn", lambda x: (x != 0).mean()))
    print(f"  {'window':>8}{'steps':>9}{'churn':>9}", flush=True)
    for k, r in tab.iterrows():
        print(f"  {k:>8}{int(r.steps):>9,}{r.churn:>9.2%}", flush=True)
    up, dn = int((st.dn > 0).sum()), int((st.dn < 0).sum())
    nxt = st.assign(dn_next=st.groupby("game_id").dn.shift(-1))
    drops = nxt[nxt.dn < 0]
    rev = (drops.dn_next > 0).mean() if len(drops) else float("nan")
    print(f"\n  direction: {up:,} joins vs {dn:,} exits — books posting lines as the game "
          f"approaches;\n  {rev:.0%} of exits reverse on the very next step (feed flicker, "
          f"not a book\n  withdrawing a line).", flush=True)
    return tab


def contamination(d, ths=(0.01, 0.015, 0.02, 0.03, 0.05)):
    """S2. Is the event population enriched in membership artifacts?"""
    print("\n=== 2. EVENT-POPULATION CONTAMINATION ===", flush=True)
    st = d[d.sportsbook.notna() & d.n_books_lag.notna()]
    base = 1 - st.same_panel.mean()
    print(f"  base rate of membership change across all {len(st):,} book steps: "
          f"{base:.1%}", flush=True)
    print(f"  {'threshold':>10}{'events':>9}{'contaminated':>14}{'enrichment':>12}", flush=True)
    for t in ths:
        e = st[st.sportsbook.abs() >= t]
        if not len(e):
            continue
        c = 1 - e.same_panel.mean()
        mark = "   <- book_moves default" if abs(t - THRESH) < 1e-9 else ""
        print(f"  {t*100:>9.1f}p{len(e):>9,}{c:>13.1%}{c/base if base else np.nan:>11.1f}x"
              f"{mark}", flush=True)
    print("\n  READ: a membership change is a jump-shaped event, so the bigger the cut the", flush=True)
    print("  larger the artifact share. This is a property of the INSTRUMENT, not of the", flush=True)
    print("  market, and it is why S3 re-detects the events on a constant panel.", flush=True)


def clean_event_study(d, thresh=THRESH, w=W):
    """S3. The event study that the contamination above calls into question."""
    print(f"\n=== 3. BOOK-MOVE EVENT STUDY, CLEAN vs CONTAMINATED PANEL "
          f"(>= {thresh*100:.0f}pt) ===", flush=True)
    d = d.copy()
    d["win_clean"] = (d.groupby("game_id").same_panel
                      .transform(lambda s: s.rolling(2 * w + 1, center=True,
                                                     min_periods=2 * w + 1).min())
                      .astype("float"))
    cuts = [("all events (published)", None),
            ("event step membership-constant", "same_panel"),
            ("whole +-1h window constant", "win_clean")]
    print(f"  {'population':>32}{'events':>8}{'size':>7}"
          f"{'kalshi antic% (p)':>22}{'poly antic% (p)':>22}", flush=True)
    res = {}
    for label, col in cuts:
        mats, sizes = windows(d, "sportsbook", thresh=thresh, w=w, eligible=col)
        if len(sizes) < 10:
            print(f"  {label:>32}{len(sizes):>8}   too few events to read", flush=True)
            continue
        cells = ""
        for s in ("kalshi", "polymarket"):
            *_, antic, nok = decompose(mats[s], w)
            pv = stats.binomtest(int(round(antic * nok)), nok).pvalue if nok else 1.0
            cells += f"{antic:>11.0%} (p={pv:.3g})".rjust(22)
            res[(label, s)] = (antic, pv, nok)
        print(f"  {label:>32}{len(sizes):>8}{sizes.mean()*100:>6.1f}p{cells}", flush=True)

    print(f"\n  response decomposition on the CLEAN population (pts, signed by the "
          f"book's move):", flush=True)
    mats, sizes = windows(d, "sportsbook", thresh=thresh, w=w, eligible="same_panel")
    print(f"  {'responder':>12}{'pre(-1h)':>10}{'at':>8}{'post(+1h)':>11}{'total':>8}", flush=True)
    for s in SRCS:
        pre, at, post, tot, _antic, _n = decompose(mats[s], w)
        print(f"  {s:>12}{pre*100:>+9.2f}{at*100:>+7.2f}{post*100:>+10.2f}{tot*100:>+7.2f}",
              flush=True)
    print("\n  READ: if the published anticipation shares were an averaging artifact they", flush=True)
    print("  must move toward 50% once the artifact events are gone. The rows above are", flush=True)
    print("  the test; the comparison is stated in findings.md, not asserted here.", flush=True)
    return res


def regressions(d, label="15-min"):
    """S4. The predictive regressions with membership held constant.

    Cleaning the instrument is only half the job. If a book->exchange
    coefficient APPEARS once the composition noise is gone, it still has to be
    identified: an exchange quote that has been resting for half an hour and
    then steps toward a consensus that drifted while it slept produces a
    positive lagged-book coefficient with no information passing at all. The
    two mechanism cuts are `five_min.robustness`'s and are reused unchanged so
    the two clocks are read the same way: real news transmission concentrates
    in AWAKE quotes and SCALES with the size of the book's move; catch-up
    bookkeeping does the opposite.
    """
    print(f"\n=== 4. PREDICTIVE REGRESSIONS, MEMBERSHIP HELD CONSTANT ({label}) ===",
          flush=True)
    g = d.sort_values(["game_id", "t"]).copy()
    for c in SRCS:
        g[f"{c}_lag"] = g.groupby("game_id")[c].shift(1)
    g["date"] = pd.to_datetime(g.t, utc=True).dt.date
    for c in ("kalshi", "polymarket"):
        g[f"{c}_awake"] = g.groupby("game_id")[c].transform(
            lambda s: s.abs().rolling(2, min_periods=1).sum().shift(1)) > 0.001

    def fit(sub, y, cl="game_id"):
        sub = sub.dropna(subset=[y] + [f"{c}_lag" for c in SRCS] + [cl])
        if len(sub) < 200 or sub[cl].nunique() < 10:
            return None, len(sub)
        others = [a for a in SRCS if a != y]
        X = sm.add_constant(sub[[f"{y}_lag"] + [f"{a}_lag" for a in others]].values)
        r = sm.OLS(sub[y].values, X).fit(cov_type="cluster",
                                         cov_kwds={"groups": sub[cl].values})
        j = 2 + others.index("sportsbook")
        return (r.params[j], r.tvalues[j], r.pvalues[j]), len(sub)

    def row(lab, sub, cl="game_id", awake=None):
        cells, n = "", 0
        for y in ("kalshi", "polymarket"):
            s2 = sub if awake is None else (sub[sub[f"{y}_awake"]] if awake
                                            else sub[~sub[f"{y}_awake"].astype(bool)])
            r, n = fit(s2, y, cl)
            cells += (f"{r[0]:+.3f}(z={r[1]:+.1f},p={r[2]:.3f})" if r
                      else f"n={n} thin").rjust(26)
        print(f"  {lab:>36}{cells}", flush=True)

    print("  coefficient on the lagged BOOK move, predicting the exchange's next move",
          flush=True)
    print(f"  {'subsample':>36}{'kalshi':>26}{'polymarket':>26}", flush=True)
    base = g[g.same_panel & (g.mts <= 120)]
    row("all steps", g)
    row("membership CONSTANT", g[g.same_panel])
    row("membership CONSTANT, final 2h", base)
    row("membership CONSTANT, >2h out", g[g.same_panel & (g.mts > 120)])
    print(f"  {'':>36}{'--- final 2h, identified ---':>52}", flush=True)
    row("  same, date-clustered", base, cl="date")
    row("  exchange quote AWAKE (moved <30m)", base, awake=True)
    row("  exchange quote RESTING (frozen 30m)", base, awake=False)
    row("  book move >=0.5pt (news-sized)", base[base.sportsbook_lag.abs() >= 0.005])
    row("  book move <0.5pt (drift)", base[base.sportsbook_lag.abs() < 0.005])

    sub = base.dropna(subset=["sportsbook"] + [f"{c}_lag" for c in SRCS])
    if len(sub) > 200:
        X = sm.add_constant(sub[[f"{c}_lag" for c in ("sportsbook", "kalshi",
                                                      "polymarket")]].values)
        r = sm.OLS(sub.sportsbook.values, X).fit(
            cov_type="cluster", cov_kwds={"groups": sub.game_id.values})
        mirror = "  ".join(f"{nm}:{r.params[i+1]:+.3f}(z={r.tvalues[i+1]:+.1f})"
                           for i, nm in enumerate(["book(own)", "kalshi", "polymarket"]))
        print(f"\n  mirror, same window — predict the BOOK: {mirror}  n={len(sub):,}",
              flush=True)

    print("\n  READ: smearing and composition both attenuate, so a coefficient that only", flush=True)
    print("  APPEARS after cleaning is the case to take seriously. Identify it before", flush=True)
    print("  reporting it as transmission: news concentrates in awake quotes and scales", flush=True)
    print("  with move size. A coefficient that lives in RESTING quotes and in sub-0.5pt", flush=True)
    print("  drift is a stale quote stepping toward a consensus that moved without it.", flush=True)


def unanswerable():
    """S5. The question this data cannot answer, stated as a limit."""
    print("\n=== 5. WHAT THIS PANEL CANNOT ANSWER ===", flush=True)
    s = pd.read_csv(SNAP, low_memory=False)
    b = s[s.source == "sportsbook"]
    print(f"  live book rows: {len(b):,}; per-book quotes retained: 0 "
          f"(`book_price()` averages at ingest and keeps only the mean and n_books).",
          flush=True)
    for f, name in (("data/processed/sportsbook_sharp_prices.csv", "EU/sharp"),
                    ("data/processed/sportsbook_us_books.csv", "US retail")):
        try:
            q = pd.read_csv(f)
            ts = q.groupby("game_id").book_ts.nunique()
            print(f"  {name} per-book tape: {len(q):,} quotes, {q.book.nunique()} books, "
                  f"{q.game_id.nunique():,} games — but {ts.mean():.2f} distinct timestamps "
                  f"per game:\n    a CLOSING CROSS-SECTION, not a time series.", flush=True)
        except FileNotFoundError:
            pass
    # The per-book tape has many distinct timestamps per game, so it is worth
    # asking how much they actually spread: if the field quotes within a couple
    # of minutes of itself, the SMEARING channel (asynchronous updates turning
    # one book's move into a multi-step ramp in the mean) is small wherever
    # that holds, which is as close as banked data gets to bounding it.
    try:
        q = pd.read_csv("data/processed/sportsbook_us_books.csv")
        q["age"] = ((pd.to_datetime(q.start_utc, utc=True, format="ISO8601")
                     - pd.to_datetime(q.book_ts, utc=True, format="ISO8601"))
                    .dt.total_seconds() / 60)
        sp = q.groupby("game_id").age.agg(lambda x: x.max() - x.min())
        per = q.groupby("book").age.mean()
        print(f"\n  ONE thing the closing cross-section DOES bound: how staggered the "
              f"field is.\n  Within-game spread between the freshest and stalest book: "
              f"median {sp.median():.1f} min, p90 {sp.quantile(.9):.1f} min; only "
              f"{(sp > 5).mean():.1%} of games\n  exceed 5 minutes, and per-book mean "
              f"age spans just {per.min():.1f}-{per.max():.1f} min across "
              f"{q.book.nunique()} books.\n  At the close the US field is near-synchronous, "
              f"so smearing is small THERE. It says\n  nothing about the wide pre-game "
              f"window, where the census above shows the churn\n  actually lives.",
              flush=True)
    except FileNotFoundError:
        pass

    print("\n  Consequence, stated plainly: 'does Pinnacle lead Kalshi, and does the", flush=True)
    print("  retail field follow Pinnacle?' is NOT identified by any data this project", flush=True)
    print("  banked, at any resolution. The no-leader result is a result about the", flush=True)
    print("  CONSENSUS, and S1-S4 are what can be said about that instrument's fitness.", flush=True)
    print("  Answering the per-book question needs one row per bookmaker per snapshot —", flush=True)
    print("  the same Odds API call already made, without the averaging step, so the", flush=True)
    print("  marginal credit cost is zero but the panel must be collected forward.", flush=True)


def main():
    print("BOOK-CONSENSUS PANEL AUDIT — is the benchmark a clean instrument for timing?",
          flush=True)
    census()
    d15 = attach(panel())
    print(f"\n15-min panel: {d15.game_id.nunique():,} games, {len(d15):,} grid steps",
          flush=True)
    contamination(d15)
    clean_event_study(d15)
    regressions(d15, "15-min")

    d5 = attach(panel(freq="5min", since=ERA5), freq="5min", since=ERA5)
    print(f"\n--- 5-minute era ({ERA5}+): {d5.game_id.nunique():,} games, "
          f"{len(d5):,} grid steps ---", flush=True)
    contamination(d5, ths=(0.01, 0.02, 0.03))
    regressions(d5, "5-min")

    unanswerable()
    print("\n  NOTE: n_books equality is a LOWER BOUND on membership churn — one book", flush=True)
    print("  leaving as another joins is invisible to it. Every contamination figure", flush=True)
    print("  above understates, and every 'clean' subsample still holds some turnover.",
          flush=True)


if __name__ == "__main__":
    main()
