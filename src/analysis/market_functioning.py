"""How markets FUNCTION with and without the liquidity complex, by venue.

The involvement question, asked properly: not just what takers lose, but
whether a market exists, how early, at what cost, and how far its prices
sit from everyone else's — measured on the same matches across Kalshi,
Polymarket, and the books, in the tier where Kalshi's professional book
is thin (Brasileiro, Eliteserien, NRL) versus the covered-league
baseline where it stands ($817K books, 0.7-0.8pt gaps, dead-heat
accuracy).

Inputs: niche_book_odds.csv (EU books at start, Pinnacle-anchored),
niche_unpriced_book_check.csv (book presence where Kalshi never priced),
niche_poly_check.csv (Poly presence/volume/price on the same matches),
kalshi_niche_prices.csv. Small-n by construction; the claims are
presence rates and median gaps, not significance tests.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def main():
    bk = pd.read_csv("data/processed/niche_book_odds.csv")
    un = pd.read_csv("data/processed/niche_unpriced_book_check.csv")
    pl = pd.read_csv("data/processed/niche_poly_check.csv")
    ni = pd.read_csv("data/processed/kalshi_niche_prices.csv").drop_duplicates("ticker")

    # 1) PRESENCE on the same matches (priced sample + unpriced sample)
    print("=== does a pre-game price exist? (same niche-league matches) ===", flush=True)
    bk_p = bk[bk.book.notna()].groupby("event_ticker").book.nunique()
    print(f"  Kalshi-priced matches (n=40): books quoted {len(bk_p)}/40 "
          f"(median {bk_p.median():.0f} books/match); Polymarket listed "
          f"{pl[pl.kalshi_priced].poly_listed.mean():.0%}", flush=True)
    print(f"  Kalshi-UNpriced matches (n=60): books quoted "
          f"{un.book_listed.mean():.0%} | Polymarket listed "
          f"{pl[~pl.kalshi_priced].poly_listed.mean():.0%} with median "
          f"${pl[~pl.kalshi_priced].poly_vol.median():,.0f} volume/match", flush=True)
    print("  (name-matching misses make book/Poly presence LOWER bounds;", flush=True)
    print("   Kalshi presence is exact — its own settled markets)", flush=True)

    # 2) PRICE AGREEMENT where venues coexist
    b = bk[bk.book.notna()].copy()
    S = b.raw_h + b.raw_a + b.raw_d.fillna(0)
    b["devig_h"] = b.raw_h / S
    cons = b.groupby("event_ticker").agg(book_h=("devig_h", "mean"),
                                         home_is_t1=("home_is_t1", "first"),
                                         n_books=("book", "nunique")).reset_index()
    # Kalshi t1-win price per event
    k1 = ni.merge(cons[["event_ticker"]], on="event_ticker")
    k1 = k1[~k1.title.str.contains("Tie|Draw", na=False)]
    k1 = k1.sort_values("ticker").groupby("event_ticker").first().reset_index()
    m = cons.merge(k1[["event_ticker", "p_start", "title"]], on="event_ticker")
    m["book_t1"] = np.where(m.home_is_t1, m.book_h, np.nan)   # t1==home only (clean orientation)
    m = m[m.book_t1.notna()]
    m = m.merge(pl[["event_ticker", "poly_p1"]], on="event_ticker", how="left")
    gaps_kb = (m.p_start - m.book_t1).abs() * 100
    print(f"\n=== price agreement, t1-win prob (n={len(m)} matches) ===", flush=True)
    print(f"  |Kalshi - book consensus|: median {gaps_kb.median():.1f}pt "
          f"(covered-league benchmark: 0.7pt)", flush=True)
    both = m[m.poly_p1.notna()]
    if len(both) >= 5:
        print(f"  |Poly - book|: median {(both.poly_p1 - both.book_t1).abs().median()*100:.1f}pt"
              f" | |Kalshi - Poly|: median {(both.p_start - both.poly_p1).abs().median()*100:.1f}pt"
              f" (n={len(both)}; Poly prices are coarse candles, up to hours old)", flush=True)

    # 3) the books' price of functioning: niche vig vs covered-league vig
    over = (b.groupby(["event_ticker", "book"])[["raw_h", "raw_a", "raw_d"]]
              .first().sum(axis=1))
    print(f"\n=== the books' niche overround ===", flush=True)
    print(f"  median field sum {over.median():.3f} (covered-league books ~1.04; "
          f"books charge more to function where flow is thin)", flush=True)

    print("\n=== reading ===", flush=True)
    print("  Same matches, three institutions. Books quote ~80-100% of them", flush=True)
    print(f"  at ~{(over.median()-1)*100:.0f}% vig (vs ~4% in covered leagues). Polymarket", flush=True)
    print("  carries six-figure volume (its Brazilian clientele) and prices", flush=True)
    print("  1.5pt from the book line. Kalshi's book mostly never prints,", flush=True)
    print("  and when it does the print sits 4.2pt from consensus — six", flush=True)
    print("  times the covered-league 0.7pt. Put next to the gradient leg", flush=True)
    print("  (niche prices UNBIASED on average, slope 0.98), the split is", flush=True)
    print("  clean: repetition keeps prices right on average; the liquidity", flush=True)
    print("  complex is what compresses the noise around them. The MM", flush=True)
    print("  complex decides WHETHER a market functions and how PRECISE it", flush=True)
    print("  is; repetition decides whether it is BIASED. Each venue", flush=True)
    print("  functions exactly where its complex or clientele deploys.", flush=True)


if __name__ == "__main__":
    main()
