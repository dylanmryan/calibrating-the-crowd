"""Book-line-move event study: do the exchanges anticipate, mirror, or chase?

For every sportsbook consensus move of >= thresh in one 15-min step, align all
three sources' signed changes in a +-4-step (+-1h) window and decompose each
exchange's TOTAL adjustment into:
    pre  (offsets -4..-1)  — anticipation: the exchange moved before the book
    at   (offset 0)        — same-step repricing (shared news)
    post (offsets +1..+4)  — following: the exchange chased the book's line
Plus the anticipation FREQUENCY (share of events where the exchange's net
pre-window move already pointed the way the book was about to move; 50% =
coin flip), a size split, and the mirror study (book response to exchange
moves — is the book's stickiness following-with-a-lag or independence?).
Events are non-overlapping (a window's steps can't seed another event).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.lead_lag import panel, SRCS

W = 4               # +-4 steps of 15 min = +-1h
THRESH = 0.02


def windows(d, event_src, thresh=THRESH, w=W):
    """Signed change matrices around non-overlapping big moves of event_src."""
    out = {s: [] for s in SRCS}
    sizes, mts = [], []
    for gid, g in d.groupby("game_id"):
        g = g.sort_values("t").reset_index(drop=True)
        ev = g.index[g[event_src].abs() >= thresh].tolist()
        last = -10 * max(w, 1)
        for i in ev:
            if i - last <= w or i - w < 0 or i + w >= len(g):
                continue
            last = i
            sgn = np.sign(g.loc[i, event_src])
            for s in SRCS:
                out[s].append(sgn * g.loc[i - w:i + w, s].to_numpy(float))
            sizes.append(abs(g.loc[i, event_src]))
            mts.append(gid)
    return {s: np.array(v) for s, v in out.items()}, np.array(sizes)


def decompose(mat, w=W):
    """(pre, at, post) mean signed response and the anticipation share."""
    pre = np.nansum(mat[:, :w], axis=1)
    at = mat[:, w]
    post = np.nansum(mat[:, w + 1:], axis=1)
    total = pre + at + post
    ok = ~np.isnan(total)
    antic = pre[ok] > 0
    return (np.nanmean(pre), np.nanmean(at), np.nanmean(post),
            np.nanmean(total), antic.mean(), int(ok.sum()))


def report(label, mats, sizes, w=W):
    print(f"\n=== events: {label} (n={len(sizes)}, mean size "
          f"{sizes.mean()*100:.1f}pts) ===", flush=True)
    print(f"  {'responder':12} {'pre(-1h)':>9} {'at':>7} {'post(+1h)':>10} "
          f"{'total':>7} {'antic%':>7}", flush=True)
    res = {}
    for s in SRCS:
        pre, at, post, tot, antic, n = decompose(mats[s], w)
        res[s] = (pre, at, post, tot, antic)
        print(f"  {s:12} {pre*100:>+8.2f} {at*100:>+6.2f} {post*100:>+9.2f} "
              f"{tot*100:>+6.2f} {antic:>6.0%}", flush=True)
    return res


def main():
    d = panel()
    print(f"panel: {d.game_id.nunique()} games", flush=True)

    mats, sizes = windows(d, "sportsbook")
    res = report("BOOK moves >=2pts — do exchanges anticipate or chase?", mats, sizes)
    for s in ("kalshi", "polymarket"):
        pre, at, post, tot, antic = res[s]
        n = len(sizes)
        p_sign = stats.binomtest(int(round(antic * n)), n).pvalue if n else 1.0
        print(f"  {s}: {pre/tot:.0%} of its total adjustment happens BEFORE the "
              f"book's move, {at/tot:.0%} same-step, {post/tot:.0%} after "
              f"(anticipation-direction share {antic:.0%}, sign-test p={p_sign:.3f})", flush=True)

    big = sizes >= 0.03
    if big.sum() >= 15:
        report("BOOK moves >=3pts", {s: m[big] for s, m in mats.items()}, sizes[big])

    kmats, ksizes = windows(d, "kalshi")
    kres = report("KALSHI moves >=2pts — does the book follow?", kmats, ksizes)
    pre, at, post, tot, _ = kres["sportsbook"]
    print(f"  book: {at/tot:.0%} of its (small) response is same-step; "
          f"post-window follow-through {post*100:+.2f}pts", flush=True)

    # figure: cumulative paths + decomposition bars
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4))
    x = np.arange(-W, W + 1) * 15
    for s, c in zip(SRCS, ("tab:blue", "tab:orange", "tab:green")):
        axes[0].plot(x, np.nancumsum(np.nanmean(mats[s], axis=0)) * 100, "o-",
                     ms=3, color=c, label=s)
    axes[0].axvline(0, color="0.4", ls="--", lw=1)
    axes[0].set(xlabel="minutes from book move", ylabel="cumulative signed move (pts)",
                title=f"Around book moves ≥2pts (n={len(sizes)})")
    axes[0].legend(fontsize=8)

    labels = ["pre (−1h)", "at", "post (+1h)"]
    xx = np.arange(3)
    for i, s in enumerate(("kalshi", "polymarket")):
        vals = [res[s][j] * 100 for j in range(3)]
        axes[1].bar(xx + (i - 0.5) * 0.35, vals, 0.35,
                    label=s, color=["tab:blue", "tab:orange"][i], alpha=0.85)
    axes[1].set_xticks(xx, labels)
    axes[1].set(ylabel="mean signed response (pts)",
                title="Exchange adjustment split around book moves")
    axes[1].legend(fontsize=8)

    for s, c in zip(SRCS, ("tab:blue", "tab:orange", "tab:green")):
        axes[2].plot(x, np.nancumsum(np.nanmean(kmats[s], axis=0)) * 100, "o-",
                     ms=3, color=c, label=s)
    axes[2].axvline(0, color="0.4", ls="--", lw=1)
    axes[2].set(xlabel="minutes from Kalshi move", title=f"Around Kalshi moves ≥2pts (n={len(ksizes)})")
    axes[2].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("results/book_moves.png", dpi=130)
    print("\nsaved results/book_moves.png", flush=True)


if __name__ == "__main__":
    main()
