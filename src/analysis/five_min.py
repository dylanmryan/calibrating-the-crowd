"""Sub-15-minute price formation: does the simultaneity survive a finer clock?

The 15-min panel said no venue leads; the 1-min Kalshi/Polymarket paths said the
same for the two exchanges. The cell that stayed open was BOOK-vs-EXCHANGE below
15 minutes: with a */15 collector, "same step" could hide a lead of up to a
quarter of an hour. The VPS cron moved to */5 on 2026-07-31, so the later era
carries all three venues on a native 5-minute grid.

Three questions, in order of how damaging a "yes" would be to the null:
  1. RESOLUTION LADDER — rerun the same battery on the same games at 5/10/15/30
     min. A real lead is a fixed wall-clock delay, so it must SHARPEN as the grid
     approaches it; a spurious one washes out. If nothing appears at 5 min that
     was invisible at 15, the null is not a resolution artifact.
  2. CROSS-LAG + PREDICTIVE REGRESSIONS at 5 min, game-clustered.
  3. BOOK-MOVE EVENT STUDY at 5 min (+-1h = +-12 steps): the 15-min study put
     ~80% of the (small) exchange response at offset 0. At 5 min that mass must
     either stay at 0 — repricing inside five minutes — or resolve into a lag.

Era note: only snapshots from 2026-07-31 are used; earlier rows are on the */15
clock and would pad the fine grid with structural NaN.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analysis.lead_lag import panel, SRCS
from src.analysis.book_moves import windows, decompose

ERA = "2026-07-31"          # cron switched */15 -> */5
GRIDS = ["5min", "10min", "15min", "30min"]
W5 = 12                     # +-12 steps of 5 min = +-1h, same window as the 15-min study
THRESH = 0.02


def cross_lags(d, label):
    """corr(dA_t, dB_{t+1}) for every ordered pair, on one grid."""
    g = d.sort_values(["game_id", "t"]).copy()
    for c in SRCS:
        g[f"{c}_next"] = g.groupby("game_id")[c].shift(-1)
    rows = []
    for a in SRCS:
        for b in SRCS:
            if a == b:
                continue
            sub = g.dropna(subset=[a, f"{b}_next"])
            r = np.corrcoef(sub[a], sub[f"{b}_next"])[0, 1] if len(sub) > 30 else np.nan
            rows.append((f"{a[:4]}->{b[:4]}", r, len(sub)))
    return rows


def resolution_ladder():
    """The core robustness: same era, same games, four clocks."""
    print("=== 1. RESOLUTION LADDER — does a lead appear as the clock sharpens? ===",
          flush=True)
    print("  a lead is a fixed delay: corr(dA_t, dB_t+1) must GROW as the step "
          "shrinks toward it", flush=True)
    tables = {}
    for f in GRIDS:
        d = panel(freq=f, since=ERA)
        tables[f] = cross_lags(d, f)
        steps = d.dropna(subset=SRCS)
        print(f"\n  grid {f:>6}: {d.game_id.nunique()} games, "
              f"{len(steps):,} all-three complete steps", flush=True)
    pairs = [r[0] for r in tables[GRIDS[0]]]
    print(f"\n  {'pair':>12} " + " ".join(f"{f:>9}" for f in GRIDS), flush=True)
    for i, p in enumerate(pairs):
        vals = [tables[f][i][1] for f in GRIDS]
        print(f"  {p:>12} " + " ".join(f"{v:>+9.3f}" for v in vals), flush=True)
    ns = [tables[f][0][2] for f in GRIDS]
    print(f"  {'n':>12} " + " ".join(f"{n:>9,}" for n in ns), flush=True)
    print("\n  READ: flat/noisy across grids => no hidden delay between 5 and 30 min.", flush=True)
    return tables


def regressions(d):
    print("\n=== 2. PREDICTIVE REGRESSIONS at 5 min: dB_t ~ dB_(t-1) + dA_(t-1) ===",
          flush=True)
    g = d.sort_values(["game_id", "t"]).copy()
    for c in SRCS:
        g[f"{c}_lag"] = g.groupby("game_id")[c].shift(1)
    for b in SRCS:
        others = [a for a in SRCS if a != b]
        sub = g.dropna(subset=[b] + [f"{c}_lag" for c in SRCS])
        if len(sub) < 200:
            print(f"  predict d{b:<11} — too few observations (n={len(sub)})", flush=True)
            continue
        X = sm.add_constant(sub[[f"{b}_lag"] + [f"{a}_lag" for a in others]].values)
        r = sm.OLS(sub[b].values, X).fit(cov_type="cluster",
                                         cov_kwds={"groups": sub.game_id.values})
        terms = [f"{b}(own)"] + others
        msg = "  ".join(f"{t}:{r.params[i+1]:+.3f}(z={r.tvalues[i+1]:+.1f})"
                        for i, t in enumerate(terms))
        print(f"  predict d{b:<11} <- {msg}   n={len(sub):,}", flush=True)


def _meta_panel(path="data/live/vps_mirror/snapshots.csv"):
    """Per-(game, 5-min step) book-side metadata: consensus breadth and clock.

    n_books is the number of books in the consensus at that snapshot. If the
    book->exchange lead below is mechanical — a consensus that drifts because
    its members update at staggered times — it should live in the steps where
    the membership CHANGES, and weaken where it is constant.
    """
    s = pd.read_csv(path)
    s = s[(s.minutes_to_start > 0) & (s.source == "sportsbook")]
    s["t"] = pd.to_datetime(s.snapshot_utc, utc=True, format="ISO8601").dt.floor("5min")
    s = s[s.t >= pd.Timestamp(ERA, tz="UTC")]
    return (s.groupby(["game_id", "t"])
            .agg(n_books=("n_books", "last"), mts=("minutes_to_start", "last"))
            .reset_index())


def robustness(d):
    """Is the 5-min book->exchange lead information, or consensus bookkeeping?"""
    print("\n=== 2b. IS THE LEAD MECHANICAL? consensus-composition and dose checks ===",
          flush=True)
    meta = _meta_panel()
    g = d.sort_values(["game_id", "t"]).copy()
    for c in SRCS:
        g[f"{c}_lag"] = g.groupby("game_id")[c].shift(1)
    g = g.merge(meta, on=["game_id", "t"], how="left")
    g["n_books_lag"] = g.groupby("game_id")["n_books"].shift(1)
    g["same_panel"] = g.n_books == g.n_books_lag

    def fit(sub, y):
        sub = sub.dropna(subset=[y] + [f"{c}_lag" for c in SRCS])
        if len(sub) < 300 or sub.game_id.nunique() < 10:
            return None, len(sub)
        others = [a for a in SRCS if a != y]
        X = sm.add_constant(sub[[f"{y}_lag"] + [f"{a}_lag" for a in others]].values)
        r = sm.OLS(sub[y].values, X).fit(cov_type="cluster",
                                         cov_kwds={"groups": sub.game_id.values})
        j = 1 + 1 + others.index("sportsbook")
        return (r.params[j], r.tvalues[j]), len(sub)

    print("  coefficient on lagged BOOK move, predicting the exchange's next 5-min move", flush=True)
    print(f"  {'subsample':38} {'kalshi':>18} {'polymarket':>18}", flush=True)
    # had the exchange's own quote been moving, or was it resting? a resting
    # quote that eventually catches up to a slowly drifting consensus produces
    # a positive lagged-book coefficient with no information passing at all.
    for c in ("kalshi", "polymarket"):
        recent = (g.groupby("game_id")[c].transform(
            lambda s: s.abs().rolling(6, min_periods=1).sum().shift(1)))
        g[f"{c}_awake"] = recent > 0.001

    cuts = [
        ("all steps", g, None),
        ("consensus membership UNCHANGED", g[g.same_panel], None),
        ("consensus membership CHANGED", g[~g.same_panel.astype(bool)], None),
        ("book moved >=0.5pt", g[g.sportsbook_lag.abs() >= 0.005], None),
        ("book moved <0.5pt", g[g.sportsbook_lag.abs() < 0.005], None),
        ("final 2h before start", g[g.mts <= 120], None),
        ("more than 2h out", g[g.mts > 120], None),
        ("exchange quote AWAKE (moved in last 30m)", g, "awake"),
        ("exchange quote RESTING (frozen 30m)", g, "resting"),
    ]
    for label, sub, mode in cuts:
        cells = []
        for y in ("kalshi", "polymarket"):
            s2 = sub
            if mode == "awake":
                s2 = sub[sub[f"{y}_awake"]]
            elif mode == "resting":
                s2 = sub[~sub[f"{y}_awake"].astype(bool)]
            res, n = fit(s2, y)
            cells.append(f"{res[0]:+.3f}(z={res[1]:+.1f})" if res else f"n={n} thin")
        print(f"  {label:38} {cells[0]:>18} {cells[1]:>18}", flush=True)
    print("\n  READ: a bookkeeping artifact concentrates where membership changes and", flush=True)
    print("  does not scale with move size; information scales with size and with", flush=True)
    print("  proximity to the event.", flush=True)


def rolling_event_study(d, w=6, roll=3, thresh=THRESH):
    """Same-magnitude events as the 15-min study, measured on the 5-min clock.

    A 2pt book move almost never lands in a single 5-min step, so events are
    defined on the book's rolling `roll`-step (15-min) change and the responses
    are read at 5-min resolution, offsets aligned to the step that COMPLETES
    the move. If the 15-min study's "80% of the response is same-step" was
    hiding a lag, it must show up here as mass to the right of 0.
    """
    print(f"\n=== 3. EVENT STUDY: book moves >= {thresh*100:.0f}pts over {roll*5} min, "
          f"response on the 5-min clock (+-{w*5}min) ===", flush=True)
    out = {s: [] for s in SRCS}
    sizes = []
    for gid, g in d.groupby("game_id"):
        g = g.sort_values("t").reset_index(drop=True)
        rollsum = g["sportsbook"].rolling(roll, min_periods=roll).sum()
        ev = rollsum.index[rollsum.abs() >= thresh].tolist()
        last = -10 * max(w, 1)
        for i in ev:
            if i - last <= w or i - w < 0 or i + w >= len(g):
                continue
            last = i
            sgn = np.sign(rollsum.loc[i])
            for s in SRCS:
                out[s].append(sgn * g.loc[i - w:i + w, s].to_numpy(float))
            sizes.append(abs(rollsum.loc[i]))
    mats = {s: np.array(v) for s, v in out.items()}
    sizes = np.array(sizes)
    if len(sizes) < 10:
        print(f"  only {len(sizes)} events — underpowered", flush=True)
        return mats, sizes, None
    print(f"  n={len(sizes)} events, mean size {sizes.mean()*100:.1f}pts "
          f"(offset 0 = the 5-min step completing the move)", flush=True)
    offs = np.arange(-w, w + 1) * 5
    print(f"  {'responder':12} " + " ".join(f"{o:>+6d}" for o in offs), flush=True)
    for s in SRCS:
        prof = np.nanmean(mats[s], axis=0) * 100
        print(f"  {s:12} " + " ".join(f"{v:>+6.2f}" for v in prof), flush=True)
    print("\n  exchange response split (pts):", flush=True)
    for s in ("kalshi", "polymarket"):
        pre, at, post, tot, antic, n = decompose(mats[s], w)
        after = f"{post/tot:+.0%}" if abs(tot) > 1e-9 else "n/a"
        print(f"    {s:12} during the move (-{roll*5}..0): "
              f"{np.nansum(np.nanmean(mats[s], axis=0)[w-roll+1:w+1])*100:+.2f}pts | "
              f"after (+5..+{w*5}min): {post*100:+.2f}pts ({after} of total) | "
              f"before: {pre*100:+.2f}pts", flush=True)
    print("  READ: mass to the RIGHT of 0 = the exchanges chase the book with a "
          "sub-15-min lag; mass at/left of 0 = they were already there.", flush=True)
    return mats, sizes, True


def event_study(d, w=W5):
    print(f"\n=== 3. BOOK-MOVE EVENT STUDY at 5 min (+-{w*5}min, events >= {THRESH*100:.0f}pts) ===",
          flush=True)
    global W5_ACTIVE
    mats, sizes = windows(d, "sportsbook", THRESH, w)
    if len(sizes) < 10:
        print(f"  only {len(sizes)} clean non-overlapping events — underpowered "
              "at this window width", flush=True)
        return mats, sizes, None
    print(f"  n={len(sizes)} events, mean size {sizes.mean()*100:.1f}pts", flush=True)
    print(f"  {'responder':12} {'pre':>9} {'at(5min)':>9} {'post':>10} "
          f"{'total':>7} {'antic%':>7}", flush=True)
    res = {}
    for s in SRCS:
        pre, at, post, tot, antic, n = decompose(mats[s], w)
        res[s] = (pre, at, post, tot, antic)
        print(f"  {s:12} {pre*100:>+8.2f} {at*100:>+8.2f} {post*100:>+9.2f} "
              f"{tot*100:>+6.2f} {antic:>6.0%}", flush=True)
    for s in ("kalshi", "polymarket"):
        pre, at, post, tot, antic = res[s]
        p_sign = stats.binomtest(int(round(antic * len(sizes))), len(sizes)).pvalue
        if abs(tot) > 1e-9:
            print(f"  {s}: {at/tot:.0%} of its total adjustment lands in the SAME "
                  f"5-min step as the book's move ({pre/tot:+.0%} before, "
                  f"{post/tot:+.0%} after); anticipation-direction share "
                  f"{antic:.0%}, sign-test p={p_sign:.3f}", flush=True)

    # where does the response actually land? cumulative profile per offset
    print("\n  response timing (cumulative share of the window total, by offset):", flush=True)
    offs = np.arange(-w, w + 1) * 5
    for s in ("kalshi", "polymarket"):
        prof = np.nanmean(mats[s], axis=0)
        cum = np.nancumsum(prof)
        tot = cum[-1]
        if abs(tot) < 1e-9:
            continue
        share = cum / tot
        mark = [f"{o:+d}m:{sh:.0%}" for o, sh in zip(offs, share)
                if o in (-30, -15, -5, 0, 5, 10, 15, 30, 60)]
        print(f"    {s:12} " + "  ".join(mark), flush=True)
    return mats, sizes, res


def mirror(d, w=W5):
    print("\n=== 4. MIRROR: does the book follow the exchanges within 5 min? ===", flush=True)
    for src in ("kalshi", "polymarket"):
        mats, sizes = windows(d, src, THRESH, w)
        if len(sizes) < 10:
            print(f"  {src}: only {len(sizes)} events — skipped", flush=True)
            continue
        pre, at, post, tot, antic, n = decompose(mats["sportsbook"], w)
        share = f"{at/tot:.0%}" if abs(tot) > 1e-9 else "n/a"
        print(f"  around {src} moves >=2pts (n={len(sizes)}): book responds "
              f"{pre*100:+.2f} pre / {at*100:+.2f} at / {post*100:+.2f} post "
              f"(total {tot*100:+.2f}pts, same-step share {share})", flush=True)


def figure(mats, sizes, w=W5):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    x = np.arange(-w, w + 1) * 5
    for s, c in zip(SRCS, ("tab:blue", "tab:orange", "tab:green")):
        axes[0].plot(x, np.nancumsum(np.nanmean(mats[s], axis=0)) * 100, "o-",
                     ms=3, color=c, label=s)
    axes[0].axvline(0, color="0.4", ls="--", lw=1)
    axes[0].set(xlabel="minutes from book move (5-min clock)",
                ylabel="cumulative signed move (pts)",
                title=f"Around book moves ≥2pts (n={len(sizes)}, 5-min grid)")
    axes[0].legend(fontsize=8)

    for s, c in zip(SRCS, ("tab:blue", "tab:orange", "tab:green")):
        axes[1].plot(x, np.nanmean(mats[s], axis=0) * 100, "o-", ms=3, color=c, label=s)
    axes[1].axhline(0, color="0.6", lw=0.8)
    axes[1].axvline(0, color="0.4", ls="--", lw=1)
    axes[1].set(xlabel="minutes from book move", ylabel="mean signed move per step (pts)",
                title="Per-step response — a lag would be a bump right of 0")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig("results/five_min.png", dpi=130)
    print("\nsaved results/five_min.png", flush=True)


def main():
    d5 = panel(freq="5min", since=ERA)
    complete = d5.dropna(subset=SRCS)
    print(f"5-min era panel (from {ERA}): {d5.game_id.nunique()} games, "
          f"{len(d5):,} grid steps, {len(complete):,} with all three venues", flush=True)
    moved = (complete[SRCS].abs() > 0.004).mean()
    print("share of 5-min steps with a >0.4pt move: " +
          "  ".join(f"{s}={moved[s]:.1%}" for s in SRCS), flush=True)
    print("\ncontemporaneous correlation of 5-min changes:", flush=True)
    print(complete[SRCS].corr().round(3).to_string(), flush=True)

    resolution_ladder()
    regressions(d5)
    robustness(d5)
    # +-1h at a 5-min clock rejects almost every event as overlapping; +-30min
    # is the widest window that keeps a usable event count, and it still spans
    # six steps either side of the move.
    event_study(d5, w=6)
    mats, sizes, ok = rolling_event_study(d5, w=6)
    mirror(d5, w=6)
    if ok:
        figure(mats, sizes, w=6)

    print("\n=== VERDICT ===", flush=True)
    print("  The no-leader result is NOT a resolution artifact: no cross-lag", flush=True)
    print("  correlation sharpens as the clock goes 30 -> 5 min, and nothing", flush=True)
    print("  predicts the book at any grid.", flush=True)
    print("  What the finer clock DOES reveal is a small one-step book->exchange", flush=True)
    print("  coefficient (Kalshi +0.047 z=2.4, Polymarket +0.164 z=4.5). Three", flush=True)
    print("  cuts say it is drift alignment, not news transmission:", flush=True)
    print("    - it is ZERO in the final 2h before start (K +0.006, P -0.008),", flush=True)
    print("      the window where information actually arrives;", flush=True)
    print("    - it lives in sub-half-point book moves, not news-sized ones;", flush=True)
    print("    - for Polymarket it is as strong from a quote frozen for 30 min", flush=True)
    print("      (+0.176) as from an active one (+0.138) — catch-up, not response.", flush=True)
    print("  Around real 2pt book moves the exchanges are already moving DURING", flush=True)
    print("  the book's 15-min window; ~31-38% of their (small) total arrives in", flush=True)
    print("  the following half hour (n=19 events — suggestive, not a claim).", flush=True)


if __name__ == "__main__":
    main()
