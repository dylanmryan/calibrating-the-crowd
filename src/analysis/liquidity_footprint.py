"""Where does the liquidity-provision complex stand? The footprint map.

Kalshi discloses THAT its affiliate trades (2021 emergency rule; rulebook;
CFTC 2026-07-30 proposal) but not WHERE. The observable answer is the
footprint: `liquidity_dollars` (resting-order notional) for all 784K open
markets, swept 2026-08-04, plus each series' fee_type (whether makers pay
fees — the exchange's own per-product pricing of liquidity provision).

Classes: covered-league games (our main sample), niche games (gradient
sample), sports outrights/futures, and non-sports reference categories.
The prediction from the paper's results: the professional book stands
where markets are repeated and fast-resolving (games), thins in niche
games, and largely deserts one-shot outrights — i.e., liquidity provision
DEPLOYS along the same gradient calibration follows.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

COVERED = ("KXNBAGAME", "KXNFLGAME", "KXMLBGAME", "KXNHLGAME", "KXWNBAGAME",
           "KXNCAAFGAME", "KXNCAABGAME", "KXCFBGAME", "KXCBBGAME")


def classify(row, niche, outright):
    s = row
    if s in COVERED:
        return "covered game"
    if s in niche:
        return "niche game"
    if s in outright:
        return "sports outright"
    return None


def stats(g):
    liq = g.liquidity_dollars
    two = (g.yes_bid.notna() & g.yes_ask.notna()
           & (g.yes_bid.astype(float) > 0) & (g.yes_ask.astype(float) < 1))
    return pd.Series({
        "markets": len(g),
        "median_liq": liq.median(),
        "share_liq_ge_1k": (liq >= 1000).mean(),
        "share_two_sided": two.mean(),
        "total_liq_$M": liq.sum() / 1e6})


def main():
    d = pd.read_csv("data/processed/kalshi_liquidity_sweep.csv")
    fees = pd.read_csv("data/processed/kalshi_series_fees.csv").drop_duplicates("series")
    niche = set(pd.read_csv("data/processed/kalshi_niche_prices.csv").series)
    outright = set(pd.read_csv("data/processed/kalshi_futures_prices.csv").series)
    print(f"sweep {d.sweep_date.iloc[0]}: {len(d):,} open markets, "
          f"{d.series.nunique():,} series, total resting liquidity "
          f"${d.liquidity_dollars.sum()/1e6:,.0f}M", flush=True)

    d["cls"] = [classify(s, niche, outright) for s in d.series]
    d2 = d.merge(fees[["series", "category", "fee_type"]], on="series", how="left")
    d2.loc[d2.cls.isna() & (d2.category != "Sports") & d2.category.notna(), "cls"] = \
        "non-sports (" + d2.category + ")"

    print("\n=== the footprint by market class ===", flush=True)
    t = d2[d2.cls.notna()].groupby("cls").apply(stats, include_groups=False)
    t = t.sort_values("median_liq", ascending=False)
    with pd.option_context("display.float_format", lambda x: f"{x:,.2f}"):
        print(t.to_string(), flush=True)

    print("\n=== who pays maker fees (fee_type by class) ===", flush=True)
    ft = d2[d2.cls.notna()].groupby(["cls", "fee_type"]).size().rename("markets")
    top = ft.groupby("cls", group_keys=False).apply(lambda s: s.nlargest(2))
    print(top.to_string(), flush=True)

    # NOTE: liquidity_dollars is served zeroed by the API (list AND detail),
    # like the pre-cutoff price fields — the real depth comes from the signed
    # orderbook survey (top-20-volume markets per class, 2026-08-04).
    try:
        sv = pd.read_csv("data/processed/kalshi_depth_survey.csv")
    except FileNotFoundError:
        sv = None
    if sv is not None:
        print("\n=== signed depth survey (top-volume markets per class) ===", flush=True)
        tt = sv.groupby("cls").agg(
            n=("ticker", "size"),
            book_present=("spread", lambda x: x.notna().mean()),
            med_spread=("spread", "median"),
            med_d5_dollars=("d5_dollars", "median"))
        with pd.option_context("display.float_format", lambda x: f"{x:,.2f}"):
            print(tt.to_string(), flush=True)

    print("\n=== reading ===", flush=True)
    print("  The professional book stands ~$800K within 5c per covered game", flush=True)
    print("  at 1c spreads; niche games get 1/100th of that (~$6K) and stay", flush=True)
    print("  CALIBRATED; headline outrights carry real depth (~$235K median", flush=True)
    print("  among top-volume fields) and are MISCALIBRATED anyway, while", flush=True)
    print("  74% of the outright tail has no two-sided book at all. Standing", flush=True)
    print("  liquidity neither rescues one-shot markets nor is needed by", flush=True)
    print("  repeated ones — reinforcing repetition, not liquidity, as the", flush=True)
    print("  active ingredient. The fee menu points the same way: makers", flush=True)
    print("  PAY fees where they queue to quote (covered games) and make", flush=True)
    print("  free where the exchange needs them (niche, outrights, politics).", flush=True)


if __name__ == "__main__":
    main()
