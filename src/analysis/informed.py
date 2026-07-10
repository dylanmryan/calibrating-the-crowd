"""Who makes prices informative — are large trades the smart ones?

Classic microstructure question applied to a prediction market. Per fill we
observe size, price, and the aggressor (taker_side). Two measures per trade,
signed by the taker's direction (+ yes-buyer, - no-buyer):

  markout to CLOSE      s * (p_close  - p_trade)   did the price move the
                                                   taker's way by game start?
  markout to SETTLEMENT s * (outcome - p_trade)    was the taker right?

Informed trading predicts both rise with trade size. Complements late_flow.py
("the final-day flow carries information") by asking WHO carries it. Game-level
version: does size-weighted large-trade imbalance predict the outcome beyond
the closing book line, while small-trade imbalance does not?
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def lo(p):
    p = np.clip(np.asarray(p, float), 0.01, 0.99)
    return np.log(p / (1 - p))


def clustered_mean(x, groups):
    mu = x.mean()
    g = pd.DataFrame({"x": x - mu, "c": groups}).groupby("c")["x"].sum()
    se = np.sqrt((g ** 2).sum()) / len(x)
    return mu, se


def main():
    t = pd.read_csv("data/processed/kalshi_trades_24h.csv")
    t = t.dropna(subset=["yes_price", "count", "taker_side", "kalshi_p1", "outcome"])
    t = t[t.taker_side.isin(["yes", "no"])]
    t["p_trade"] = t.yes_price.astype(float)   # collector stores dollars (0-1)
    t["s"] = np.where(t.taker_side == "yes", 1.0, -1.0)
    t["mk_close"] = t.s * (t.kalshi_p1 - t.p_trade)
    t["home_won"] = (t.outcome == 1).astype(float)
    t["mk_settle"] = t.s * (t.home_won - t.p_trade)
    print(f"trades: {len(t):,} across {t.game_id.nunique():,} games "
          f"({dict(t.groupby('league').game_id.nunique())})", flush=True)
    print(f"size: median={t['count'].median():.0f} p90={t['count'].quantile(.9):.0f} "
          f"p99={t['count'].quantile(.99):.0f} contracts", flush=True)

    print("\n=== markout by trade-size quintile (game-clustered SEs) ===", flush=True)
    t["bucket"] = pd.qcut(t["count"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    print(f"  {'size Q':>7} {'n':>8} {'avg size':>9} {'markout->close':>15} {'z':>6} "
          f"{'markout->settle':>16} {'z':>6}", flush=True)
    for b, g in t.groupby("bucket", observed=True):
        mc, sec = clustered_mean(g.mk_close.values, g.game_id.values)
        ms, ses = clustered_mean(g.mk_settle.values, g.game_id.values)
        print(f"  {b:>7} {len(g):>8,} {g['count'].mean():>9.0f} "
              f"{mc*100:>+14.2f}pt {mc/sec:>+6.1f} {ms*100:>+15.2f}pt {ms/ses:>+6.1f}", flush=True)
    print("  (Kalshi taker fee ~1.75pt at evens: takers need markout > fee to profit)", flush=True)

    # game-level: large vs small signed imbalance
    print("\n=== game level: does LARGE-trade imbalance predict outcomes beyond the book? ===", flush=True)
    thresh = t.groupby("league")["count"].transform(lambda x: x.quantile(0.75))
    t["big"] = t["count"] >= thresh
    def imb(g):
        v = g["s"] * g["count"]
        tot = g["count"].sum()
        return v.sum() / tot if tot else np.nan
    gm = (t.groupby(["game_id", "big"]).apply(imb, include_groups=False)
            .unstack().rename(columns={False: "imb_small", True: "imb_big"}))
    meta = t.groupby("game_id").agg(book_p1=("book_p1", "first"),
                                    home_won=("home_won", "first"),
                                    start_utc=("start_utc", "first"))
    d = gm.join(meta).dropna(subset=["book_p1", "imb_big", "imb_small"])
    dates = pd.to_datetime(d.start_utc, utc=True, format="ISO8601").dt.date.values
    X = sm.add_constant(np.column_stack([lo(d.book_p1), d.imb_big, d.imb_small]))
    r = sm.Logit(d.home_won.values.astype(int), X).fit(
        disp=0, cov_type="cluster", cov_kwds={"groups": dates})
    for k, nm in enumerate(["book", "imbalance LARGE", "imbalance small"], start=1):
        print(f"  {nm:16} weight={r.params[k]:+.3f}  z={r.tvalues[k]:+.2f}  p={r.pvalues[k]:.3f}", flush=True)
    print(f"  (n={len(d):,} games; imbalance = size-weighted net taker direction, top-quartile", flush=True)
    print(f"   sizes vs rest. Informed trading => LARGE significant, small not.)", flush=True)


if __name__ == "__main__":
    main()
