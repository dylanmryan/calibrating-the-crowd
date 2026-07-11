"""Are CLOSING prices fully efficient with respect to the day's own movement?

Sharpening (open->close accuracy gains) says prices move toward truth. A
stricter question: once you know the close, is the PATH redundant? If the
open->close move still predicts outcomes conditional on the close, the close
underreacts to its own news (the classic line-move anomaly: bet the direction
the line moved). Test per source:
    logit(home_won) ~ logit(close) + [logit(close) - logit(open)]
A significant move term = closing price not fully efficient.

Second panel: T-24h encompassing. At the close, Kalshi adds a whisper beyond
the books (encompassing.py). Does it already exist a DAY out, or is the
exchange's contribution built during the final day along with the catch-up?
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from src.analysis.horizon_equivalence import load


def lo(p):
    p = np.clip(np.asarray(p, float), 0.01, 0.99)
    return np.log(p / (1 - p))


def move_test(d, open_c, close_c, label, dates):
    y = d.home_won.values.astype(int)
    X = sm.add_constant(np.column_stack([lo(d[close_c]), lo(d[close_c]) - lo(d[open_c])]))
    r = sm.Logit(y, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": dates})
    rr = sm.Logit(y, X[:, :2]).fit(disp=0)
    p_lr = 1 - stats.chi2.cdf(2 * (sm.Logit(y, X).fit(disp=0).llf - rr.llf), df=1)
    print(f"  {label:11} close={r.params[1]:+.3f}  move={r.params[2]:+.3f} "
          f"(z={r.tvalues[2]:+.2f}, p={r.pvalues[2]:.3f}, LR p={p_lr:.3f})", flush=True)


def main():
    d = load()
    dates = pd.to_datetime(d.start_utc, utc=True, format="ISO8601").dt.date.values
    print(f"constant sample: {len(d):,} games\n", flush=True)

    print("=== does the day's move predict beyond the close? (underreaction test) ===", flush=True)
    move_test(d, "book24_p1", "book_p1", "Book", dates)
    move_test(d, "p_h1440", "p_h0", "Kalshi", dates)
    move_test(d, "q_h1440", "q_h0", "Polymarket", dates)
    print("  (move term ~0 = close fully absorbs the day's news; >0 = underreaction)", flush=True)

    print("\n=== T-24h encompassing: does Kalshi add information a day out? ===", flush=True)
    y = d.home_won.values.astype(int)
    for pair, cols in [("book24 + Kalshi24", ["book24_p1", "p_h1440"]),
                       ("book24 + Poly24", ["book24_p1", "q_h1440"]),
                       ("close: book + Kalshi (same sample)", ["book_p1", "p_h0"])]:
        X = sm.add_constant(np.column_stack([lo(d[c]) for c in cols]))
        r = sm.Logit(y, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": dates})
        full = sm.Logit(y, X).fit(disp=0)
        rr = sm.Logit(y, X[:, :2]).fit(disp=0)   # drop the 2nd source
        p_lr = 1 - stats.chi2.cdf(2 * (full.llf - rr.llf), df=1)
        print(f"  {pair:36} 2nd-source weight={r.params[2]:+.3f} "
              f"(z={r.tvalues[2]:+.2f}, p={r.pvalues[2]:.3f}, LR excl p={p_lr:.3f})", flush=True)


if __name__ == "__main__":
    main()
