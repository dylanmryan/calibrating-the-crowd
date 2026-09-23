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

THRESH is the one number that defines the event population, so it is swept
rather than asserted (see threshold_sweep). The sweep RE-DETECTS events at each
threshold rather than sub-setting the 2pt events: because detection enforces
non-overlap, a lower threshold does not merely add events, it changes which
ones survive the pruning — so a post-hoc subset would not answer the question.
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


def windows(d, event_src, thresh=THRESH, w=W, eligible=None):
    """Signed change matrices around non-overlapping big moves of event_src.

    eligible — optional boolean column in `d`. When given, only steps where it
    is True can SEED an event. The filter is applied at detection, before the
    non-overlap pruning, not as a post-hoc subset of the unfiltered events:
    pruning enforces non-overlap over whatever population is detected, so
    dropping events afterwards would leave a population no detector produces
    (the same reason `threshold_sweep` re-detects at each cut). Used by
    `book_panel.py` to re-run the study on steps where the book consensus kept
    a constant membership.
    """
    out = {s: [] for s in SRCS}
    sizes, mts = [], []
    for gid, g in d.groupby("game_id"):
        g = g.sort_values("t").reset_index(drop=True)
        hit = g[event_src].abs() >= thresh
        if eligible is not None:
            hit &= g[eligible].fillna(False).astype(bool)
        ev = g.index[hit].tolist()
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


def threshold_sweep(d, event_src="sportsbook", ths=(0.01, 0.015, 0.02, 0.03)):
    """Is the conclusion a property of the market or of THRESH?

    Reports, per threshold, each exchange's anticipation share (the share of
    events where its net pre-window move already pointed the way the book was
    about to go; 50% = coin flip) with a sign-test, plus the event count. The
    summary is derived from the rows, not asserted, because this runs on two
    different clocks with very different event counts.
    """
    print(f"\n=== threshold sensitivity: events re-detected at each cut "
          f"({event_src} moves) ===", flush=True)
    print(f"  {'thresh':>7}{'events':>8}{'mean size':>11}   " +
          "".join(f"{s + ' antic% (p)':>22}" for s in ("kalshi", "polymarket")), flush=True)
    rows = []
    for t in ths:
        mats, sizes = windows(d, event_src, thresh=t)
        n = len(sizes)
        if n < 15:
            print(f"  {t*100:>6.1f}p{n:>8}   (too few events to read)", flush=True)
            continue
        cells, shares, ps = "", [], []
        for s in ("kalshi", "polymarket"):
            *_, antic, nok = decompose(mats[s])
            pv = stats.binomtest(int(round(antic * nok)), nok).pvalue if nok else 1.0
            shares.append(antic); ps.append(pv)
            cells += f"{antic:>13.0%} (p={pv:.3f})".rjust(22)
        mark = "  <- module default" if abs(t - THRESH) < 1e-9 else ""
        print(f"  {t*100:>6.1f}p{n:>8}{sizes.mean()*100:>10.1f}p   {cells}{mark}",
              flush=True)
        rows.append((t, n, shares, ps))

    if not rows:
        print("  no threshold on this clock yields a readable event count.", flush=True)
        return rows
    below = all(sh < 0.5 for _, _, shares, _ in rows for sh in shares)
    sig = [t for t, _, _, ps in rows if all(pv < 0.05 for pv in ps)]
    lo = min(min(shares) for _, _, shares, _ in rows)
    hi = max(max(shares) for _, _, shares, _ in rows)
    print(f"  Read: across {len(rows)} readable cut(s) the anticipation share spans "
          f"{lo:.0%}-{hi:.0%}", flush=True)
    if below:
        print("  — BELOW 50% throughout, i.e. the exchanges had if anything drifted the", flush=True)
        print("  wrong way before a book jump. There is no anticipation to find at any", flush=True)
        print("  cut, so the null is a property of the data rather than of where the", flush=True)
        print("  event boundary was drawn.", flush=True)
    else:
        print("  — the sign is NOT stable across cuts; read the rows, not a summary.", flush=True)
    if sig:
        print(f"  Significantly below chance for both exchanges at: "
              f"{', '.join(f'{t*100:.1f}pt' for t in sig)}.", flush=True)
    return rows


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

    threshold_sweep(d)

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
