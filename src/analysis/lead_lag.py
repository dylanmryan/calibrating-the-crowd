"""Lead-lag price discovery on the live 15-minute three-source panel.

Who moves first when pre-game news arrives — the exchange (Kalshi), the crypto
market (Polymarket), or the books? Method-validation first pass on the VPS
panel (accumulating since 2026-07-07); rerun as data grows.

Design: snapshots to a 15-min grid per game, price CHANGES per source per step,
then for each ordered pair (A, B):
    corr(dA_t, dB_{t+1})   -- A's move now predicts B's next move => A leads
and a pooled predictive regression dB_t ~ dB_{t-1} + dA_{t-1} (game-clustered),
which asks whether A's last move helps predict B's next beyond B's own momentum.
Pre-game observations only; glitch filter |d| > 20pts.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

SRCS = ["kalshi", "polymarket", "sportsbook"]


def panel(path="data/live/vps_mirror/snapshots.csv"):
    s = pd.read_csv(path)
    s = s[s.minutes_to_start > 0]
    s["t"] = pd.to_datetime(s.snapshot_utc, utc=True, format="ISO8601").dt.floor("15min")
    w = (s.pivot_table(index=["game_id", "t"], columns="source", values="p1", aggfunc="last")
         .reset_index().sort_values(["game_id", "t"]))
    frames = []
    for gid, g in w.groupby("game_id"):
        g = g.set_index("t").resample("15min").asfreq()
        d = g[SRCS].diff()
        d = d[(d.abs() <= 0.2)]
        d["game_id"] = gid
        frames.append(d.reset_index())
    return pd.concat(frames, ignore_index=True).dropna(subset=SRCS, how="all")


def event_windows(g, thresh=0.02, offsets=range(-2, 3)):
    """Event study around big one-step moves (|dA| >= thresh).

    For each source A's big moves, align every other source's changes at
    offsets -2..+2 steps, SIGNED by the direction of A's move. Response
    concentrated at +1 => A leads B on news; response at <=0 => B moved
    first or simultaneously (A wasn't the discoverer).
    """
    g = g.sort_values(["game_id", "t"]).copy()
    for c in SRCS:
        for k in offsets:
            g[f"{c}@{k}"] = g.groupby("game_id")[c].shift(-k)
    print(f"\n=== event windows: big moves (|d| >= {thresh*100:.0f}pts), signed response in pts ===", flush=True)
    print(f"  {'event source':>12} {'n':>5} | " +
          " ".join(f"{'B@'+str(k):>8}" for k in offsets) + "   (per other source B)", flush=True)
    for a in SRCS:
        ev = g[g[a].abs() >= thresh]
        sgn = np.sign(ev[a])
        for b in SRCS:
            if b == a:
                continue
            resp = [(sgn * ev[f"{b}@{k}"]).mean() * 100 for k in offsets]
            n = ev[f"{b}@1"].notna().sum()
            print(f"  {a:>12} {len(ev):>5} | " +
                  " ".join(f"{r:>+8.2f}" for r in resp) + f"   B={b}", flush=True)


def main():
    d = panel()
    have_all = d.dropna(subset=SRCS)
    print(f"15-min change observations: {len(d):,} rows, {d.game_id.nunique()} games; "
          f"all-three complete steps: {len(have_all):,}", flush=True)
    moved = (have_all[SRCS].abs() > 0.004).mean()
    print(f"share of steps with a >0.4pt move: " +
          "  ".join(f"{s}={moved[s]:.1%}" for s in SRCS), flush=True)

    print("\n=== contemporaneous correlation of 15-min changes ===", flush=True)
    print(have_all[SRCS].corr().round(3).to_string(), flush=True)

    print("\n=== cross-lag correlations: corr(dA_t, dB_t+1) — A leads B if positive ===", flush=True)
    g = have_all.sort_values(["game_id", "t"]).copy()
    for c in SRCS:
        g[f"{c}_next"] = g.groupby("game_id")[c].shift(-1)
    print(f"  {'A -> B':28} {'corr':>7} {'n':>7}", flush=True)
    for a in SRCS:
        for b in SRCS:
            if a == b:
                continue
            sub = g.dropna(subset=[a, f"{b}_next"])
            r = np.corrcoef(sub[a], sub[f"{b}_next"])[0, 1]
            print(f"  {a:>11} leads {b:<11} {r:>+7.3f} {len(sub):>7,}", flush=True)

    print("\n=== predictive regressions: dB_t ~ dB_(t-1) + dA_(t-1), game-clustered ===", flush=True)
    for b in SRCS:
        others = [a for a in SRCS if a != b]
        sub = g.copy()
        for c in SRCS:
            sub[f"{c}_lag"] = sub.groupby("game_id")[c].shift(1)
        sub = sub.dropna(subset=[b] + [f"{c}_lag" for c in SRCS])
        X = sm.add_constant(sub[[f"{b}_lag"] + [f"{a}_lag" for a in others]].values)
        r = sm.OLS(sub[b].values, X).fit(cov_type="cluster",
                                         cov_kwds={"groups": sub.game_id.values})
        terms = [f"{b}(own)"] + others
        msg = "  ".join(f"{t}:{r.params[i+1]:+.3f}(z={r.tvalues[i+1]:+.1f})"
                        for i, t in enumerate(terms))
        print(f"  predict d{b:<11} <- {msg}   n={len(sub):,}", flush=True)
    print("\n  (positive z on a cross term = that source's last move predicts this", flush=True)
    print("   source's next move: information flows from it. Early-sample caveat.)", flush=True)

    event_windows(g)


if __name__ == "__main__":
    main()
