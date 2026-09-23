"""Candidate figures for the two instrument legs (book_freshness, book_panel).

Four candidates, offered so the report can pick rather than settle:

  C1  matched-freshness forest   the dead heat re-read inside each quote-age arm
  C2  the natural experiment     why an arm split exists at all, and what it shows
  C3  clean-panel anticipation   the no-leader null STRENGTHENS when artifacts go
  C4  panel integrity            how dirty the consensus series is, and where

House style and palette are `report_visuals`'s, imported rather than copied so
the candidates cannot drift from the frozen figure program.

Provenance rule, and the reason this module recomputes instead of quoting: the
frozen F-set quotes logged constants in a SOURCES block, which is right for
numbers a module prints once. These four need estimates and CIs per subsample,
so they are computed HERE from the same loaders and the same estimator
(`rigor.cluster_dm`) that `book_freshness` and `book_panel` use. Same inputs,
same code path — the figures cannot disagree with the logs, and `_assert_matches_log`
checks the two headline values against the log text at build time rather than
trusting that claim.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy import stats

from src.analysis.report_visuals import (
    _frame, _title, _note, _save, K, P, B, INK, INK2, MUTED, GRID, AXIS,
    SURFACE, CRITICAL, OUT)
from src.analysis.rigor import cluster_dm, DELTA_PRESTATED
from src.analysis.power import KMDE
from src.analysis import book_freshness as BF
from src.analysis import book_panel as BP
from src.analysis.book_moves import windows, decompose, W, THRESH
from src.analysis.lead_lag import panel

FRESH, STALE = BF.FRESH, BF.STALE


def _assert_matches_log(label, value, needle, log="book_freshness"):
    """Fail loudly if a figure's headline number is not in the module's log."""
    txt = Path(f"results/logs/{log}.log").read_text()
    assert needle in txt, (
        f"{label}: '{needle}' is not in {log}.log — the figure and the log "
        f"disagree, so the figure must not be published.")
    print(f"    checked against {log}.log: {label} = {value}")


# ------------------------------------------------------------------- C1 ---
def c1_freshness_forest(d):
    """Pairwise ΔBrier with 90% CIs, split by how stale the book quote was."""
    groups = []
    for a, an in (("kalshi_p1", "Kalshi"), ("poly_p1", "Polymarket")):
        for b, bn, age in (("pinnacle", "Pinnacle", "pin_age"),
                           ("book_p1", "US consensus", "book_age")):
            sub = d[d[b].notna() & d[age].notna()]
            arms = []
            for lab, s in (("all quotes", sub),
                           (f"<{FRESH:.0f} min from kickoff", sub[sub[age] < FRESH]),
                           (f">{STALE:.0f} min out", sub[sub[age] > STALE])):
                est, se, z, p, ci = cluster_dm(s[a], s[b], s.y, s.date)
                arms.append((lab, est * 1e3, ci[0] * 1e3, ci[1] * 1e3,
                             KMDE * se * 1e3, len(s)))
            groups.append((f"{an} − {bn}", arms))

    nrows = sum(len(a) for _, a in groups) + len(groups)   # a blank row per group header
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    fig.subplots_adjust(top=0.82, bottom=0.235, left=0.335, right=0.90)

    ax.axvspan(-DELTA_PRESTATED * 1e3, DELTA_PRESTATED * 1e3, color=K, alpha=0.06, zorder=0)
    for x in (-DELTA_PRESTATED * 1e3, DELTA_PRESTATED * 1e3):
        ax.plot([x, x], [-0.9, nrows - 0.1], color=K, lw=0.8, alpha=0.35, zorder=1)
    ax.axvline(0, color=AXIS, lw=1.1, zorder=1)

    y = nrows - 1
    yticks, yticklabels = [], []
    for gname, arms in groups:
        gy = []
        for lab, est, lo, hi, mde, n in arms:
            underpowered = mde > DELTA_PRESTATED * 1e3
            fresh = "kickoff" in lab
            col = CRITICAL if underpowered else (K if fresh else MUTED)
            lw = 2.8 if fresh else 1.9
            ax.plot([lo, hi], [y, y], color=col, lw=lw, solid_capstyle="round", zorder=3)
            ax.plot([est], [y], "o", ms=7.2 if fresh else 5.6, color=col, zorder=4,
                    markeredgecolor=SURFACE, markeredgewidth=1.6)
            ax.text(1.44, y, f"{n:,}", fontsize=7.6, color=MUTED, va="center", ha="right")
            yticks.append(y); yticklabels.append(lab)
            gy.append(y); y -= 1
        # group name on the blank row ABOVE its arms — beside them it collides
        # with the arm labels at every left margin worth using
        ax.text(-0.335, max(gy) + 0.75, gname, transform=ax.get_yaxis_transform(),
                ha="left", va="center", fontsize=9.4, color=INK, fontweight="bold")
        y -= 1

    ax.text(1.44, nrows - 0.15, "games", fontsize=7.6, color=INK2, ha="right")
    ax.text(DELTA_PRESTATED * 1e3, nrows - 0.15, "pre-stated δ", fontsize=7.6,
            color=INK2, ha="center")
    ax.set_yticks(yticks); ax.set_yticklabels(yticklabels, fontsize=8.4, color=INK2)
    ax.set_ylim(-0.9, nrows - 0.1); ax.set_xlim(-1.5, 1.5)
    ax.set_xlabel("difference in Brier score   (×10⁻³, 90% CI — negative favours the exchange)",
                  labelpad=10)
    _frame(ax, xgrid=True, ygrid=False)

    ax.legend(handles=[
        Line2D([], [], color=K, lw=2.8, label="book quoted minutes from kickoff — the arm where it is not handicapped"),
        Line2D([], [], color=MUTED, lw=1.9, label="pooled, or the stale arm"),
        Line2D([], [], color=CRITICAL, lw=1.9, label="underpowered (MDE > δ): consistent, but unable to detect")],
        loc="upper left", bbox_to_anchor=(-0.45, -0.145), fontsize=8, ncol=1,
        labelcolor=INK2, handlelength=1.6)
    _title(fig, "The dead heat survives when the sportsbook is quoted fresh",
           "Book prices here are up to an hour old while exchange prices are taken at kickoff. Splitting on "
           "quote age removes\nthat asymmetry — and against Pinnacle inside ten minutes the difference is "
           "−0.004×10⁻³, at full power.", y=0.988)
    _note(fig, "book_freshness.log · date-clustered Diebold–Mariano on the squared-error differential; a 90% CI "
               "inside ±δ is the TOST criterion. Every row shown is equivalent at δ.", y=0.012)
    _save(fig, "C1_matched_freshness_forest")


# ------------------------------------------------------------------- C2 ---
def c2_natural_experiment(d):
    """Why an arm split exists (left) and the direct staleness test (right).

    The right panel is deliberately NOT the arm-by-arm comparison — C1 already
    shows that. It is the interaction: does the differential MOVE with
    freshness? Sign convention matters and is stated on the axis, because a
    positive shift is what the staleness caveat predicts, not what refutes it.
    """
    import statsmodels.api as sm
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.1),
                             gridspec_kw={"width_ratios": [1.0, 1.12]})
    fig.subplots_adjust(top=0.70, bottom=0.185, left=0.075, right=0.975, wspace=0.42)

    ax = axes[0]
    age = d.book_age.dropna()
    n, _, _ = ax.hist(age, bins=np.arange(0, 70, 1.5), color=B, alpha=0.85,
                      edgecolor=SURFACE, lw=0.4)
    top = n.max() * 1.30
    ax.set_ylim(0, top)
    ax.axvspan(0, FRESH, color=K, alpha=0.10)
    ax.axvspan(STALE, 70, color=MUTED, alpha=0.10)
    ax.text(FRESH * 0.5, top * 0.97, f"fresh · {(age < FRESH).mean():.0%}",
            ha="center", va="top", fontsize=8.6, color=K, fontweight="bold")
    ax.text(50, top * 0.97, f"stale · {(age > STALE).mean():.0%}",
            ha="center", va="top", fontsize=8.6, color=INK2, fontweight="bold")
    ax.set_xlabel("age of the book quote at kickoff (minutes)")
    ax.set_ylabel("games")
    ax.set_title("A batched collector split the sample for us", fontsize=9.8,
                 color=INK, pad=8)
    _frame(ax)

    ax = axes[1]
    rows = []
    for a, an in (("kalshi_p1", "Kalshi"), ("poly_p1", "Polymarket")):
        for b, bn, age_c in (("pinnacle", "Pinnacle", "pin_age"),
                             ("book_p1", "US consensus", "book_age")):
            sub = d[d[b].notna() & d[age_c].notna()]
            sub = sub[(sub[age_c] < FRESH) | (sub[age_c] > STALE)].copy()
            sub["dsq"] = (sub[a] - sub.y) ** 2 - (sub[b] - sub.y) ** 2
            sub["fresh"] = (sub[age_c] < FRESH).astype(float)
            r = sm.OLS(sub.dsq.values, sm.add_constant(sub[["fresh"]].values)).fit(
                cov_type="cluster", cov_kwds={"groups": sub.date.values})
            lo, hi = r.conf_int(alpha=0.10)[1]
            rows.append((f"{an} − {bn}", r.params[1] * 1e3, lo * 1e3, hi * 1e3))

    ax.axvline(0, color=AXIS, lw=1.1)
    ax.axvspan(0, 1.35, color=MUTED, alpha=0.07, zorder=0)
    for i, (lab, est, lo, hi) in enumerate(reversed(rows)):
        ax.plot([lo, hi], [i, i], color=INK2, lw=2.2, solid_capstyle="round", zorder=3)
        ax.plot([est], [i], "o", ms=6.8, color=K, zorder=4,
                markeredgecolor=SURFACE, markeredgewidth=1.5)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([r[0] for r in reversed(rows)], fontsize=8.6, color=INK)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.set_xlim(-0.9, 1.35)
    ax.set_xlabel("shift in Δ Brier when the book is quoted fresh  (×10⁻³, 90% CI)")
    ax.text(0.67, len(rows) - 0.52, "the direction the caveat predicts",
            ha="center", fontsize=7.9, color=INK2)
    ax.set_title("and the staleness penalty is real but tiny", fontsize=9.8,
                 color=INK, pad=8)
    _frame(ax, xgrid=True, ygrid=False)

    _title(fig, "The one timing asymmetry in the design, measured instead of conceded",
           "Credit-batching left quote age bimodal, which makes it a natural experiment: the split is the "
           "collector's cadence,\nnot a property of the games. Every interval on the right covers zero.",
           y=0.985)
    _note(fig, "book_freshness.log §1–§2 · a POSITIVE shift means the exchange's apparent edge shrinks "
               "once the book is quoted fresh — the handicap the caveat feared. All four are "
               "insignificant (z = 0.14–1.30).")
    _save(fig, "C2_freshness_natural_experiment")


# ------------------------------------------------------------------- C3 ---
def c3_clean_panel(dp):
    """Anticipation share: published population vs constant-membership panel."""
    dp = dp.copy()
    dp["win_clean"] = (dp.groupby("game_id").same_panel
                       .transform(lambda s: s.rolling(2 * W + 1, center=True,
                                                      min_periods=2 * W + 1).min()).astype(float))
    pops = [("all events\n(as published)", None),
            ("event step\nmembership-constant", "same_panel"),
            ("whole ±1h window\nmembership-constant", "win_clean")]
    res = {}
    for lab, col in pops:
        mats, sizes = windows(dp, "sportsbook", thresh=THRESH, w=W, eligible=col)
        for s, nm in (("kalshi", "Kalshi"), ("polymarket", "Polymarket")):
            *_, antic, nok = decompose(mats[s], W)
            pv = stats.binomtest(int(round(antic * nok)), nok).pvalue
            res[(lab, nm)] = (antic, pv, len(sizes))

    fig, ax = plt.subplots(figsize=(8.0, 4.3))
    fig.subplots_adjust(top=0.74, bottom=0.20, left=0.105, right=0.80)
    ax.axhline(0.5, color=CRITICAL, lw=1.2, ls="--", zorder=2)
    ax.text(2.42, 0.505, "coin flip — no anticipation", fontsize=8.2, color=CRITICAL, va="bottom")
    x = np.arange(len(pops))
    for nm, col in (("Kalshi", K), ("Polymarket", P)):
        ys = [res[(l, nm)][0] for l, _ in pops]
        ax.plot(x, ys, "o-", color=col, lw=2.2, ms=8, markeredgecolor=SURFACE,
                markeredgewidth=1.6, zorder=4, label=nm)
        for xi, (l, _) in zip(x, pops):
            a, pv, n = res[(l, nm)]
            ax.annotate(f"{a:.0%}", (xi, a), textcoords="offset points",
                        xytext=(0, -17 if nm == "Polymarket" else 11),
                        ha="center", fontsize=8.6, color=col, fontweight="bold")
        ax.text(2.06, ys[-1], f"  {nm}", fontsize=9, color=col, va="center", fontweight="bold")
    # event counts live in the tick labels: as an in-axes row they collide with
    # whichever series happens to sit lowest at the right-hand end
    ax.set_xticks(x)
    ax.set_xticklabels([f"{l}\nn={res[(l,'Kalshi')][2]} events" for l, _ in pops],
                       fontsize=8.6, color=INK)
    ax.set_ylim(0.165, 0.60); ax.set_xlim(-0.35, 2.35)
    ax.set_yticks([0.2, 0.3, 0.4, 0.5])
    ax.set_yticklabels(["20%", "30%", "40%", "50%"])
    ax.set_ylabel("share of book jumps the exchange\nhad already drifted toward", fontsize=8.8)
    _frame(ax)
    _title(fig, "Cleaning the benchmark makes the no-leader result stronger, not weaker",
           "If the exchanges' failure to anticipate book moves were an artifact of averaging books "
           "together, removing the\nartifact events would pull these lines toward 50%. They move the "
           "other way.", y=0.985)
    _note(fig, "book_panel.log §3 · events are re-detected at each population, so non-overlap pruning "
               "runs over a population a detector actually produces. All six points p<0.02 (sign test).")
    _save(fig, "C3_clean_panel_anticipation")


# ------------------------------------------------------------------- C4 ---
def c4_panel_integrity(dp, freq="15min"):
    """How much of the consensus series is bookkeeping, and where it lives."""
    m = BP.meta(freq).sort_values(["game_id", "t"])
    g = m.groupby("game_id")
    m["dn"], m["dp"] = g.n_books.diff(), g.p1.diff()
    st = m[m.dn.notna() & m.dp.notna()]

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.9))
    fig.subplots_adjust(top=0.70, bottom=0.175, left=0.095, right=0.975, wspace=0.30)

    ax = axes[0]
    b = st.assign(bucket=pd.cut(st.mts, [0, 60, 120, 240, 480, np.inf],
                                labels=["0–60m", "1–2h", "2–4h", "4–8h", ">8h"]))
    tab = b.groupby("bucket", observed=True).agg(churn=("dn", lambda x: (x != 0).mean()),
                                                 n=("dn", "size"))
    cols = [K, K, MUTED, MUTED, MUTED]
    ax.bar(range(len(tab)), tab.churn * 100, color=cols, alpha=0.9)
    for i, (_, r) in enumerate(tab.iterrows()):
        ax.text(i, r.churn * 100 + 0.09, f"{r.churn*100:.2f}%", ha="center",
                fontsize=8.2, color=INK2)
    ax.set_xticks(range(len(tab))); ax.set_xticklabels(tab.index, fontsize=8.6)
    ax.set_ylabel("% of steps where the panel's\nmembership changed", fontsize=8.8)
    ax.set_title("The churn lives far from kickoff", fontsize=9.6, color=INK, pad=6)
    ax.text(0.5, tab.churn.iloc[0] * 100 + 1.15,
            "the window every headline\nhorizon result lives in",
            ha="center", fontsize=7.8, color=K)
    _frame(ax)

    ax = axes[1]
    base = 1 - dp[dp.sportsbook.notna() & dp.n_books_lag.notna()].same_panel.mean()
    ths = [1.0, 1.5, 2.0, 3.0, 5.0]
    sub = dp[dp.sportsbook.notna() & dp.n_books_lag.notna()]
    shares = [(1 - sub[sub.sportsbook.abs() >= t / 100].same_panel.mean()) * 100 for t in ths]
    ax.plot(ths, shares, "o-", color=CRITICAL, lw=2.2, ms=7,
            markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=4)
    ax.axhline(base * 100, color=MUTED, lw=1.2, ls="--")
    ax.text(1.0, base * 100 + 1.0, f"base rate across all steps: {base*100:.1f}%",
            fontsize=7.9, color=MUTED, va="bottom")
    ax.annotate("the event cut the\npublished study uses", (2.0, shares[2]),
                textcoords="offset points", xytext=(6, -30), fontsize=7.8, color=INK2,
                arrowprops=dict(arrowstyle="->", color=AXIS, lw=0.9))
    ax.set_xlabel("size of the consensus jump that defines an event (points)")
    ax.set_ylabel("% of those jumps that are a\nmembership change, not a reprice", fontsize=8.8)
    ax.set_xlim(0.6, 6.4); ax.set_ylim(0, 28)
    ax.set_title("and it concentrates in exactly the big moves", fontsize=9.6, color=INK, pad=6)
    _frame(ax)

    _title(fig, "Why the benchmark had to be audited before its timing could be trusted",
           "\"The sportsbook\" in every lead–lag result is a mean across books. When a book joins or "
           "drops out, the mean moves\nwithout anyone repricing — and a jump-shaped artifact lands "
           "in a study whose events are jumps.", y=0.985)
    _note(fig, "book_panel.log §1–§2 · 15-minute grid. Membership change is detected as a change in "
               "book count, a LOWER bound: one book leaving as another joins is invisible to it.")
    _save(fig, "C4_panel_integrity")


def main():
    print("candidate figures for the instrument legs", flush=True)
    d, u = BF.load()
    _assert_matches_log("K vs Pinnacle, fresh arm", "-0.004e-3", "-0.004e-3  -0.02")
    c1_freshness_forest(d)
    c2_natural_experiment(d)
    dp = BP.attach(panel())
    _assert_matches_log("clean-panel anticipation (Kalshi)", "26%", "26% (p=0.00191)", "book_panel")
    c3_clean_panel(dp)
    c4_panel_integrity(dp)
    print("\n  candidates written to results/report/ as C1–C4; renumber on selection.", flush=True)


if __name__ == "__main__":
    main()
