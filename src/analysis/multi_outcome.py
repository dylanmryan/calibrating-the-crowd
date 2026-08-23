"""Beyond binary: 3-way soccer and full margin distributions as forecasts.

Part A - World Cup 3-way (frozen case study, descriptive at n=8 pre-kickoff
games): outcome-level calibration by outcome TYPE (home/draw/away), draw
pricing specifically (the outcome with no fans), ranked probability scores
per source (the proper score for ordered outcomes), and how tightly the two
sources tracked each other across the full snapshot paths.

Part B - margin distributions head-to-head: each game's spread ladder implies
a full distribution over victory margins. Kalshi's ladder and the books' alt
lines are scored as DISTRIBUTIONS with the ranked probability score on the
per-game SHARED threshold grid (fair comparison: same cut points), then the
per-game RPS differential gets the usual date-clustered DM treatment. This
extends the dead-heat question from "who wins" to "by how much".

Part C - inventory probe for the outright/futures leg: settled multi-outcome
championship markets on Kalshi (where favorite-longshot bias classically
lives, and where Burgi-Deng-Whelan's platform pathologies were worst).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import requests
from scipy import stats

from src.analysis.margin_dist import implied_cdf
from src.analysis.ladder_convention import BOOK
from src.analysis.rigor import cluster_dm
from src.collect.kalshi_hist_prices import _rule_home

OUTCOMES = ["home", "draw", "away"]


def wc_part():
    d = pd.read_csv("data/processed/wc_3way_snapshots.csv")
    pre = d[d.minutes_to_start > 0].sort_values("snapshot_utc")
    close = pre.groupby(["game_id", "source"]).tail(1)
    close = close[close.reg_outcome.notna()]
    n_games = close.game_id.nunique()
    print(f"=== A. World Cup 3-way (n={n_games} pre-kickoff games; descriptive) ===", flush=True)

    print(f"\n  outcome-type calibration (mean priced vs realized share):", flush=True)
    print(f"  {'outcome':>8} {'realized':>9} {'Kalshi':>8} {'book':>8}", flush=True)
    for oc in OUTCOMES:
        real = (close[close.source == "kalshi"].reg_outcome == oc).mean()
        row = [close[close.source == s][f"p_{oc}"].mean() for s in ("kalshi", "sportsbook")]
        print(f"  {oc:>8} {real:>8.1%} {row[0]:>7.1%} {row[1]:>7.1%}", flush=True)

    print(f"\n  ranked probability score (ordered home>draw>away; lower better):", flush=True)
    for s in ("kalshi", "sportsbook"):
        g = close[close.source == s]
        cum_f = np.cumsum(g[["p_home", "p_draw", "p_away"]].to_numpy(float), axis=1)
        oc_idx = g.reg_outcome.map({"home": 0, "draw": 1, "away": 2}).to_numpy()
        cum_o = (np.arange(3)[None, :] >= oc_idx[:, None]).astype(float)
        rps = ((cum_f - cum_o) ** 2)[:, :2].sum(axis=1) / 2
        print(f"    {s:11} RPS = {rps.mean():.4f}", flush=True)

    # how tightly did the sources track across the whole path?
    piv = pre.pivot_table(index=["game_id", "snapshot_utc"], columns="source",
                          values=["p_home", "p_draw", "p_away"])
    gaps = {}
    for oc in OUTCOMES:
        col = f"p_{oc}"
        both = piv[col].dropna()
        gaps[oc] = (both["kalshi"] - both["sportsbook"]).abs().mean() * 100
    print(f"\n  mean |Kalshi - book| across all {len(pre):,} snapshot rows: "
          + ", ".join(f"{oc} {v:.1f}pt" for oc, v in gaps.items()), flush=True)
    print("  (the draw is priced as tightly across venues as the teams are)", flush=True)


def margin_rps(return_cdfs=False):
    sp = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    ab = pd.read_csv("data/processed/sportsbook_alt_spreads.csv")
    esp = pd.read_csv("data/processed/espn_games.csv")[
        ["espn_id", "home_score", "away_score"]].rename(columns={"espn_id": "game_id"})
    ml = pd.read_csv("data/processed/games_master.csv")[
        ["game_id", "kalshi_p1", "book_p1", "outcome_disagree", "start_utc", "league"]]
    ml = ml[~ml.outcome_disagree.fillna(False)]

    # Kalshi per-game CDF
    kcdf = {}
    for gid, g in sp.groupby("game_id"):
        codes = sorted(set(g.team))
        rh = _rule_home(g.event_ticker.iloc[0], codes) if len(codes) == 2 else None
        if rh is None:
            continue
        home = {r.threshold: r.prob for r in g[g.team == rh].itertuples(index=False)}
        away = {r.threshold: r.prob for r in g[g.team != rh].itertuples(index=False)}
        row = ml[ml.game_id == gid]
        pml = float(row.kalshi_p1.iloc[0]) if len(row) and row.kalshi_p1.notna().iloc[0] else None
        if home and away:
            kcdf[gid] = implied_cdf(home, away, pml, g.league.iloc[0])

    # book per-game CDF (alt lines: point<0 = home laying, prob_home = P(cover))
    bcdf = {}
    for gid, g in ab.groupby("game_id"):
        home = {-r.point: r.prob_home for r in g[g.point < 0].itertuples(index=False)}
        away = {r.point: 1 - r.prob_home for r in g[g.point > 0].itertuples(index=False)}
        row = ml[ml.game_id == gid]
        pml = float(row.book_p1.iloc[0]) if len(row) and row.book_p1.notna().iloc[0] else None
        if home and away:
            bcdf[gid] = implied_cdf(home, away, pml, BOOK)

    both = sorted((set(kcdf) & set(bcdf)))
    esp_m = esp.set_index("game_id")
    ml_m = ml.set_index("game_id")
    rows = []
    for gid in both:
        if gid not in esp_m.index or gid not in ml_m.index:
            continue
        er = esp_m.loc[gid]
        if isinstance(er, pd.DataFrame) or er.home_score != er.home_score:
            continue
        m = er.home_score - er.away_score
        shared = sorted(set(kcdf[gid]) & set(bcdf[gid]))
        if len(shared) < 3:
            continue
        rk = np.mean([(kcdf[gid][x] - (m <= x)) ** 2 for x in shared])
        rb = np.mean([(bcdf[gid][x] - (m <= x)) ** 2 for x in shared])
        mr = ml_m.loc[gid]
        rows.append({"game_id": gid, "league": mr.league,
                     "date": str(mr.start_utc)[:10], "rps_k": rk, "rps_b": rb,
                     "n_shared": len(shared)})
    r = pd.DataFrame(rows)
    print(f"\n=== B. margin DISTRIBUTIONS head-to-head (RPS on shared rungs) ===", flush=True)
    print(f"  games with both ladders: {len(r):,} "
          f"(median shared thresholds {int(r.n_shared.median())})", flush=True)
    for lg, g in list(r.groupby("league")) + [("ALL", r)]:
        # per-game RPS differential with date-clustered SE
        diff = g.rps_k - g.rps_b
        dbar = diff.mean()
        cent = pd.DataFrame({"d": (diff - dbar).values, "c": g.date.values}).groupby("c")["d"].sum()
        se = np.sqrt((cent ** 2).sum()) / len(g)
        z = dbar / se if se > 0 else np.nan
        print(f"  {lg:5} n={len(g):5}  RPS Kalshi={g.rps_k.mean():.4f}  "
              f"book={g.rps_b.mean():.4f}  diff={dbar*1000:+.2f}e-3  z={z:+.2f}"
              f"  ({'book better' if dbar > 0 else 'Kalshi better'})", flush=True)
    print("  (dead heat on WHO wins; this asks BY HOW MUCH. After the ladder-", flush=True)
    print("   convention fix the MLB gap is n.s.; what survives is a small NBA", flush=True)
    print("   edge to the books -- see src/analysis/ladder_convention.py)", flush=True)
    if return_cdfs:
        return kcdf, bcdf, esp_m, ml_m


def eval_cdf(cdf, x):
    """Step CDF evaluated at x (exact grid hit required -> None otherwise)."""
    return cdf.get(x)


def distribution_figure(kcdf, bcdf, esp_m, ml_m):
    """The margin-of-victory probability graph the ladders construct, vs reality."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # grids chosen from the thresholds BOTH sources actually quote
    # CDF x-positions (cover-based), chosen to cut the SAME six cells as before:
    #   MLB home rungs 2.5/3.5/4.5 -> x 1/2/3 ; away -> x -2/-3/-4
    #   NBA home rungs 2.5/5.5     -> x 2/5   ; away -> x -3/-6
    grids = {"MLB": [-4.0, -3.0, 0.0, 2.0, 3.0],
             "NBA": [-6.0, -3.0, 0.0, 2.0, 5.0]}
    labels = {"MLB": ["away 4+", "away 3", "away 1-2", "home 1-2", "home 3", "home 4+"],
              "NBA": ["away 6+", "away 3-5", "away 1-2", "home 1-2", "home 3-5", "home 6+"]}
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2))
    print("\n=== B2. the margin-of-victory probability graph vs reality ===", flush=True)
    for ax, lg in zip(axes, ("MLB", "NBA")):
        thr = grids[lg]
        gids = [g for g in (set(kcdf) & set(bcdf))
                if g in esp_m.index and g in ml_m.index
                and ml_m.loc[g].league == lg
                and all(t in kcdf[g] and t in bcdf[g] for t in thr)]
        if not gids:
            continue
        cells = list(zip([-np.inf] + thr, thr + [np.inf]))
        imp_k = np.zeros(len(cells)); imp_b = np.zeros(len(cells)); real = np.zeros(len(cells))
        for g in gids:
            m = esp_m.loc[g].home_score - esp_m.loc[g].away_score
            Fk = lambda x: 0.0 if x == -np.inf else (1.0 if x == np.inf else kcdf[g][x])
            Fb = lambda x: 0.0 if x == -np.inf else (1.0 if x == np.inf else bcdf[g][x])
            for i, (lo, hi) in enumerate(cells):
                imp_k[i] += Fk(hi) - Fk(lo)
                imp_b[i] += Fb(hi) - Fb(lo)
                real[i] += (lo < m <= hi) if hi != np.inf else (m > lo)
        n = len(gids)
        imp_k /= n; imp_b /= n; real /= n
        x = np.arange(len(cells))
        ax.bar(x, real * 100, color="0.82", label="actual outcomes")
        ax.plot(x, imp_k * 100, "o-", color="tab:blue", label="Kalshi ladder implies")
        ax.plot(x, imp_b * 100, "s-", color="tab:green", label="books' lines imply")
        ax.set_xticks(x, labels[lg], rotation=45, fontsize=8)
        ax.set(ylabel="probability / share of games (%)",
               title=f"{lg} margin of victory (n={n:,} games)")
        ax.legend(fontsize=8)
        gap_k = np.abs(imp_k - real).sum() / 2 * 100
        gap_b = np.abs(imp_b - real).sum() / 2 * 100
        print(f"  {lg}: n={n:,} | total variation distance to reality: "
              f"Kalshi {gap_k:.1f}pts, books {gap_b:.1f}pts", flush=True)
    fig.suptitle("What the spread ladders say the final margin will be — and what it was")
    fig.tight_layout()
    fig.savefig("results/margin_distribution.png", dpi=140)
    print("  saved results/margin_distribution.png", flush=True)


def futures_probe():
    print(f"\n=== C. settled multi-outcome futures on Kalshi (inventory probe) ===", flush=True)
    s = requests.Session()
    B = "https://api.elections.kalshi.com/trade-api/v2"
    candidates = ["KXNBACHAMP", "KXNBAFINALS", "KXWSERIES", "KXMLBCHAMP", "KXSB",
                  "KXNHLCUP", "KXSTANLEY", "KXMARMADW", "KXMARMAD", "KXWCUP",
                  "KXNBAEAST", "KXMLBALCS", "KXWNBACHAMP", "KXEPL"]
    for series in candidates:
        try:
            r = s.get(f"{B}/markets", params={"series_ticker": series,
                                              "status": "settled", "limit": 200}, timeout=15)
            ms = r.json().get("markets", []) if r.status_code == 200 else []
            if ms:
                evs = {}
                for m in ms:
                    evs.setdefault(m.get("event_ticker"), 0)
                    evs[m["event_ticker"]] += 1
                sizes = sorted(evs.values(), reverse=True)
                print(f"  {series:14} settled markets={len(ms):4}  events={len(evs):3}  "
                      f"outcomes/event (top): {sizes[:3]}", flush=True)
        except requests.RequestException:
            continue
    print("  (any event with >2 outcomes is a true multi-outcome market —", flush=True)
    print("   candidate sample for the outright favorite-longshot test)", flush=True)


def main():
    wc_part()
    out = margin_rps(return_cdfs=True)
    if out:
        distribution_figure(*out)
    futures_probe()


if __name__ == "__main__":
    main()
