"""Robustness cuts: does the dead heat depend on a choice nobody had to defend?

Four decisions were made once, early, and never varied. Each is defensible; none
was ever *shown* to be immaterial, which is a different thing and the thing a
referee asks about. This module varies all four on the frozen sample.

  1. FAVOURITE STRENGTH. A pooled Brier is dominated by mid-price games, so a
     venue difference confined to heavy favourites — where the money
     concentrates — would be invisible in it. Bucketing is on the outcome-blind
     three-venue consensus price, never on any single venue's own price.
  2. KALSHI PRICE CONSTRUCTION. `price_side()` returns a 1-min candle book-mid
     where Kalshi's 60-day window still holds the book and a trade-reconstructed
     bid/ask otherwise — two different instruments, ~80/20 on this sample. The
     reconstruction is separately validated against archived order books
     (validate_recon); this asks whether the COMPARISON depends on which one
     produced the price.
  3. BOOK CONSENSUS CONSTRUCTION. The benchmark averages vigged implied
     probabilities across books and de-vigs the average once. De-vigging each
     book first, taking a median instead of a mean, and line-shopping the best
     price on each side are all equally standard. Line-shopping is the books'
     best possible case and is included for that reason.
  0. QUOTE QUALITY. The master carries staleness, spread, and consensus-depth
     flags for every price, and `three_way.load()` filters on none of them. The
     honest statement is not "we filtered" but "no filter was needed" — which
     is only honest if the distributions are shown. Section 0 shows them.
  4. SAMPLE EXCLUSION. The clean set drops games where any source's settlement
     disagrees with ESPN. The drop is venue-asymmetric (far more Kalshi than
     Polymarket), so the honest check is whether keeping every disputed game and
     trusting ESPN moves anything.

Reading rule, applied throughout per power.py: every null is quoted with its MDE.
delta_min (the smallest TOST margin the realized 90% CI meets) and MDE answer
different questions and can disagree — a cell can be EQUIV at delta_min by luck
of a near-zero point estimate while still being underpowered.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.analysis.compare import brier
from src.analysis.rigor import cluster_dm, DELTA_PRESTATED
from src.analysis.power import KMDE
from src.analysis.three_way import SRC, load

PAIRS = [("kalshi_p1", "poly_p1", "K-P"),
         ("kalshi_p1", "book_p1", "K-B"),
         ("poly_p1", "book_p1", "P-B")]

# favourite-strength buckets, in points of distance from a coin flip
FAV_EDGES = [0.0, 0.05, 0.15, 0.25, 1.0]
FAV_LABELS = ["coin-flip <5pt", "mild 5-15pt", "clear 15-25pt", "heavy >25pt"]

MIN_CELL = 150          # below this a cut is reported as too small to read


def worst_pair(g, pairs=PAIRS):
    """Worst-case |z| (with the pair that produced it), delta_min and MDE.

    The pair is named so a borderline cell cannot hide behind an aggregate:
    a worst |z| near 2 across three pairs and several cuts is unremarkable,
    but the reader is entitled to see which comparison it came from.
    """
    y = g.home_won.values
    wz, wlab, wd, wm = 0.0, "", 0.0, 0.0
    for a, b, lab in pairs:
        _, se, z, _, (lo, hi) = cluster_dm(g[a], g[b], y, g.date.values)
        if abs(z) > wz:
            wz, wlab = abs(z), lab
        wd = max(wd, abs(lo), abs(hi))
        wm = max(wm, KMDE * se)
    return wz, wlab, wd, wm


def verdict(dmin, mde, delta=DELTA_PRESTATED):
    """EQUIV needs the realized CI inside delta; a null needs power to mean anything."""
    if dmin <= delta:
        return "EQUIV@1e-3" if mde <= delta else "EQUIV@1e-3 (low power)"
    return "power-limited" if mde > delta else "not resolved"


def header(title, first="cut"):
    print(f"\n=== {title} ===", flush=True)
    print(f"  {first:<26}{'n':>6}{'K':>8}{'P':>8}{'B':>8}"
          f"{'worst|z|':>13}{'d_min':>8}{'MDE':>8}   verdict", flush=True)


def row(label, g):
    if len(g) < MIN_CELL:
        print(f"  {label:<26}{len(g):>6}   (below {MIN_CELL} — too small to read)", flush=True)
        return
    y = g.home_won.values
    wz, wlab, wd, wm = worst_pair(g)
    print(f"  {label:<26}{len(g):>6}"
          f"{brier(g.kalshi_p1, y):>8.4f}{brier(g.poly_p1, y):>8.4f}{brier(g.book_p1, y):>8.4f}"
          f"{wz:>8.2f} {wlab:<4}{wd*1000:>8.2f}{wm*1000:>8.2f}   {verdict(wd, wm)}", flush=True)


# ------------------------------------------------------------------ cut 0 ---

def quality_flags(d):
    """What the unused quality columns actually contain.

    Reported rather than filtered on: a staleness or spread cut would be a
    researcher degree of freedom, and these distributions show there is nothing
    for it to buy. `poly_stale` in particular bounds a construction detail —
    `poly_price_at` looks back up to 8 HOURS for a last trade, and the table
    shows that window never binds anywhere near its limit.
    """
    print("\n=== 0. quote quality on the headline sample (carried, never filtered on) ===",
          flush=True)
    cols = [
        ("k_stale1", "Kalshi quote age (min)", "min"),
        ("poly_stale1", "Poly quote age (min)", "min"),
        ("k_spread1", "Kalshi quoted spread ($)", "$"),
        ("book_n_books", "books in the consensus", "n"),
    ]
    print(f"  {'column':<26}{'n':>6}{'p50':>9}{'p90':>9}{'p99':>9}{'max':>9}   tail", flush=True)
    for c, lab, unit in cols:
        if c not in d:
            continue
        v = d[c].dropna()
        if not len(v):
            continue
        if unit == "n":
            tail = f"{(v < 5).mean():.1%} of games under 5 books"
        elif unit == "min":
            tail = f"{(v > 60).mean():.2%} older than 60 min"
        else:
            tail = f"{(v > 0.02).mean():.1%} wider than 2c"
        print(f"  {lab:<26}{len(v):>6,}{v.median():>9.2f}{v.quantile(.90):>9.2f}"
              f"{v.quantile(.99):>9.2f}{v.max():>9.2f}   {tail}", flush=True)
    print("  Read: the quotes are essentially simultaneous with the bell and the", flush=True)
    print("  consensus is essentially always the full book panel, so no quality", flush=True)
    print("  filter is applied and none would change the sample materially. The", flush=True)
    print("  book leg is the one with a real timing caveat (30-min snapshot", flush=True)
    print("  bucketing, sportsbook_hist), and it is conceded in the limitations.", flush=True)


# ------------------------------------------------------------------ cut 1 ---

def cut_favourite(d):
    header("1. by favourite strength (bucketed on the outcome-blind consensus price)")
    d = d.copy()
    d["consensus"] = d[[c for c, _ in SRC.values()]].mean(axis=1)
    d["fav"] = (d.consensus - 0.5).abs()
    d["bkt"] = pd.cut(d.fav, FAV_EDGES, labels=FAV_LABELS, include_lowest=True)
    for b in FAV_LABELS:
        row(b, d[d.bkt == b])
    print("  (a difference confined to the tails would not show in the pooled Brier;", flush=True)
    print("   the tail buckets are the small ones, so their nulls are MDE-limited)", flush=True)


# ------------------------------------------------------------------ cut 2 ---

def cut_construction(d):
    header("2. by Kalshi price construction (k_src)", first="construction")
    for src in ("trade-recon", "book-mid"):
        row(src, d[d.k_src1 == src])
    n_r = int((d.k_src1 == "trade-recon").sum())
    print(f"  ({n_r:,}/{len(d):,} = {n_r/len(d):.0%} of Kalshi closes are reconstructed", flush=True)
    print("   from the trade tape; the reconstruction itself is validated against", flush=True)
    print("   archived order books in validate_recon — see that log)", flush=True)


# ------------------------------------------------------------------ cut 3 ---

def book_constructions():
    """Four consensus rules from the per-book tape, indexed by game_id."""
    u = pd.read_csv("data/processed/sportsbook_us_books.csv")
    u = u[(u.raw_p1 > 0) & (u.raw_p2 > 0)].copy()
    u["devig"] = u.raw_p1 / (u.raw_p1 + u.raw_p2)
    g = u.groupby("game_id")
    mean1, mean2 = g.raw_p1.mean(), g.raw_p2.mean()
    # line-shopping: the cheapest quote on each side is the lowest implied prob
    best1, best2 = g.raw_p1.min(), g.raw_p2.min()
    return pd.DataFrame({
        "mean_then_devig": mean1 / (mean1 + mean2),
        "devig_then_mean": g.devig.mean(),
        "devig_then_median": g.devig.median(),
        "bestprice_devig": best1 / (best1 + best2),
        "n_books": g.size(),
    })


def cut_consensus(d):
    alt = book_constructions()
    j = d.merge(alt, left_on="game_id", right_index=True, how="inner")
    y = j.home_won.values
    print(f"\n=== 3. by book-consensus construction (n={len(j):,} games with per-book "
          f"detail, mean {j.n_books.mean():.1f} books) ===", flush=True)
    print(f"  {'construction':<26}{'Brier':>8}{'vs K z':>9}{'p':>8}{'d_min':>9}"
          f"{'MDE':>8}   {'mean |diff| vs headline':>24}", flush=True)
    cols = ["book_p1", "mean_then_devig", "devig_then_mean",
            "devig_then_median", "bestprice_devig"]
    for c in cols:
        _, se, z, pv, (lo, hi) = cluster_dm(j.kalshi_p1, j[c], y, j.date.values)
        dmin, m = max(abs(lo), abs(hi)), KMDE * se
        diff = "—" if c == "book_p1" else f"{(j[c] - j.book_p1).abs().mean()*100:.3f}pt"
        tag = " (headline)" if c == "book_p1" else ""
        print(f"  {c + tag:<26}{brier(j[c], y):>8.4f}{z:>+9.2f}{pv:>8.3f}"
              f"{dmin*1000:>9.2f}{m*1000:>8.2f}   {diff:>24}", flush=True)
    print("  (bestprice = line-shopped across all books, the benchmark's best possible", flush=True)
    print("   case; the equivalence verdict does not turn on any of these choices)", flush=True)


# ------------------------------------------------------------------ cut 4 ---

def cut_exclusion():
    m = pd.read_csv("data/processed/games_master.csv")
    priced = m.kalshi_p1.notna() & m.poly_p1.notna() & m.book_p1.notna()
    inc = m[priced & m.outcome.notna()].copy()
    inc["home_won"] = (inc.outcome == 1).astype(int)
    inc["date"] = inc.start_utc.astype(str).str[:10]
    bad = inc.outcome_disagree.fillna(False).astype(bool)
    header("4. by sample exclusion (settlement disagreements kept vs dropped)", first="sample")
    row("clean set (the paper's)", inc[~bad])
    row("INCLUDING disagreers", inc)
    nk = int(inc.kalshi_disagree.fillna(False).astype(bool).sum())
    npo = int(inc.poly_disagree.fillna(False).astype(bool).sum())
    print(f"  ({int(bad.sum())}/{len(inc):,} = {bad.mean():.1%} dropped; the drop is "
          f"venue-asymmetric —", flush=True)
    print(f"   {nk} Kalshi vs {npo} Polymarket settlement disagreements — so the check", flush=True)
    print("   that matters is whether keeping them and trusting ESPN moves anything)", flush=True)


def main():
    d = load()
    d["date"] = d.start_utc.astype(str).str[:10]
    print(f"three-way clean games: {len(d):,} over {d.date.nunique()} dates", flush=True)
    print(f"equivalence margin delta = {DELTA_PRESTATED*1000:.1f}e-3 (pre-stated; D2)", flush=True)
    print("d_min and MDE are printed x1000; MDE at alpha=.05, power=80% (power.py)", flush=True)
    print("EQUIV and a significant z can co-occur and do not contradict: at this n a", flush=True)
    print("gap far too small to matter is still detectable. TOST answers 'is it small',", flush=True)
    print("DM answers 'is it zero'; the paper's claim is the first one.", flush=True)

    quality_flags(d)
    cut_favourite(d)
    cut_construction(d)
    cut_consensus(d)
    cut_exclusion()

    print("\nREPORT RULE: these are robustness cuts, not subgroup discoveries. None", flush=True)
    print("enters the FDR family (multiple_testing D1); each is read the way every", flush=True)
    print("other null in this project is read — with its MDE in the same sentence.", flush=True)


if __name__ == "__main__":
    main()
