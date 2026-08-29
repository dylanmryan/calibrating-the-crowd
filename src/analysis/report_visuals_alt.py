"""Additional and alternative report figures.

Five figures that fill gaps in the main program, and five alternatives to
figures that already exist, so the choice between framings is yours rather
than mine.

  NEW
  F10  when the equivalence forms   Brier along the final day, all three venues
  F11  maker and taker              the structural difference a book cannot offer
  F12  who is on the other side     the two-layer order book
  F13  the gambling scorecard       seven criteria, and the one that matches
  F14  immediacy                    cost and capacity against order size

  ALTERNATIVES
  F1alt   headline as stat tiles          (vs F1's two panels)
  F2alt   deviation from perfect          (vs F2's 45-degree reliability curve)
  F3alt   pooled pairs, single margin     (vs F3's full anchor ladder)
  F6alt   the whole price curve           (vs F6's three-row summary)
  F7alt   re-staked and fixed-stake       (vs F7's re-staked only)

Same provenance rule as report_visuals: every statistic is quoted from the
2026-08-23 suite logs, named at each block.
"""
from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from src.analysis.report_visuals import (
    AXIS, B, CRITICAL, GAME_RETURN, GRID, INK, INK2, K, MODEL, MUTED, NL, P,
    SURFACE, VENUES, COST_RATE, FUTURES_RETURN, POOLED_CI, SUB10, SUB10_SHIN,
    TICKET_EQUIV, _frame, _note, _save, _title,
)

# ----------------------------------------------------------- logged stats ---
# horizon_cross.log — 7-horizon constant sample, n=3,906 on both exchanges (2026-08-29 freeze)
HORIZONS = ["24h", "12h", "6h", "3h", "1h", "15m", "start"]
HZ = {"Kalshi":     [0.2210, 0.2203, 0.2200, 0.2198, 0.2197, 0.2194, 0.2195],
      "Polymarket": [0.2206, 0.2204, 0.2200, 0.2198, 0.2197, 0.2197, 0.2196]}
HZ_BOOK = {0: 0.2204, 6: 0.2194}          # book reference: two observations only

# why_sports.log section B — per-fill realized ROI, final-24h sample
ROI = [("Taker, gross", -4.99, K), ("Taker, net of fee", -7.73, K),
       ("Maker, no fee", +5.64, P)]
ROI_SE = 7.0                               # game-clustered; the wedge is structural
STRUCTURAL = -4.6                          # horizon_translation.log

# maker_structure.log / immediacy.log — the two-layer book (Kalshi, home side)
LAYERS = {"at the touch": (1135, 2243), "resting within 5c": (15148, 27566)}
TOUCH_RETAIL = {"Kalshi": 22.4, "Polymarket": 1.9}   # % of snapshots

# immediacy.log — median cost and fill share by order size
SIZES = [10, 100, 1000, 10000, 50000, 200000]
COST = {"Kalshi": [0.50, 0.50, 0.50, 0.50, 0.50, 0.55],
        "Polymarket": [0.50, 0.50, 0.50, 0.51, 0.86, 1.64]}
FILL = {"Kalshi": [99, 98, 92, 61, 44, 36],
        "Polymarket": [100, 100, 100, 96, 67, 21]}
MEDIAN_ORDER = 30

# The operational criteria, post-2026-08-23 correction.
SCORECARD = [
    ("Calibration", "prices systematically biased",
     "well calibrated at every venue (ECE 0.009-0.014)", False),
    ("Favourite-longshot bias", "longshots systematically overpriced",
     "none: every calibration-slope CI includes 1", False),
    ("Information content", "no forecasting value",
     "beats a public-statistics floor by 13e-3 (z~7.3)", False),
    ("Internal coherence", "ladders contradict themselves",
     "99.7% monotone on live books; executable arbitrage 0.10%", False),
    ("Distributional accuracy", "the shape of outcomes is wrong",
     "margin PIT passes in every league; totals in 3 of 4", False),
    ("Exploitability", "a profitable strategy exists",
     "no strategy clears costs; edge-chasing loses more", False),
    ("What the house takes", "a large, unavoidable take",
     "4.2% all-in for a taker - the same as a sportsbook", True),
]


# ==================================================================== F10 ===
def f10_formation():
    """The equivalence is built during the final day, not assumed at the close."""
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    fig.subplots_adjust(top=0.74, bottom=0.155, left=0.115, right=0.80)

    x = np.arange(len(HORIZONS))
    for name, col in (("Kalshi", K), ("Polymarket", P)):
        ax.plot(x, HZ[name], "-o", color=col, lw=2, ms=5.5, zorder=3,
                markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.text(x[-1] + 0.13, HZ[name][-1] + (-0.00007 if name == "Kalshi" else 0.00007),
                name, color=col, fontsize=8.8, fontweight="bold", va="center")

    bx, by = list(HZ_BOOK), list(HZ_BOOK.values())
    ax.plot(bx, by, color=B, lw=1.6, alpha=0.55, zorder=2)
    ax.plot(bx, by, "o", color=B, ms=7, zorder=4,
            markeredgecolor=SURFACE, markeredgewidth=1.6)
    ax.text(x[-1] + 0.13, by[-1] - 0.00016, "Sportsbook", color=B, fontsize=8.8,
            fontweight="bold", va="center")
    ax.text(x[-1] + 0.13, by[-1] - 0.00030, "(observed at two points only)",
            color=MUTED, fontsize=7.2, va="center")

    ax.annotate("", xy=(0, 0.22112), xytext=(0, 0.22056),
                arrowprops=dict(arrowstyle="<->", color=MUTED, lw=1.0))
    ax.text(0.16, 0.22084, "a day out, the books are\nfractionally ahead",
            fontsize=7.8, color=INK2, va="center", linespacing=1.5)
    ax.text(x[-1] - 0.05, 0.22032, "by the first pitch,\nnothing separates them",
            fontsize=7.8, color=INK2, ha="right", va="center", linespacing=1.5)

    ax.set_xticks(x)
    ax.set_xticklabels(["T-" + h if h != "start" else "start" for h in HORIZONS])
    ax.set_xlim(-0.3, len(HORIZONS) - 0.55)
    ax.set_ylim(0.21930, 0.22140)
    ax.set_xlabel("time before the first pitch or tip-off")
    ax.set_ylabel("Brier score   (lower is better)")
    _frame(ax)

    _title(fig, "The dead heat is built during the final day",
           "Constant sample of 3,905 games priced at all seven horizons on both exchanges. "
           "Both exchanges sharpen monotonically and are indistinguishable at every horizon.")
    _note(fig, "horizon_cross.log, horizon_equivalence.log · the T-24h book lead is z=+1.86, p=0.063 - "
               "it does NOT survive BH at q=0.05, and is reported as suggestive.")
    _save(fig, "F10_when_equivalence_forms")


# ==================================================================== F11 ===
def f11_maker_taker():
    """The institutional difference that survives: you may be the maker."""
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    fig.subplots_adjust(top=0.70, bottom=0.24, left=0.26, right=0.97)

    ax.axvline(0, color=AXIS, lw=1.0, zorder=2)
    for i, (label, val, col) in enumerate(ROI):
        y = 2 - i
        ax.barh(y, val, height=0.42, color=col, zorder=3)
        ax.text(val + (0.35 if val > 0 else -0.35), y, f"{val:+.1f}%",
                va="center", ha="left" if val > 0 else "right",
                fontsize=8.8, color=INK)
        ax.text(-0.55 if val < 0 else -0.55, y, label, va="center", ha="right",
                fontsize=8.8, color=INK, transform=ax.get_yaxis_transform())

    ax.axvline(STRUCTURAL, color=CRITICAL, lw=1.3, zorder=4)
    ax.text(STRUCTURAL - 0.4, -0.62, "structural taker cost, -4.6%" + NL +
            "(half-spread + fee, fixed before any ball is thrown)",
            fontsize=7.7, color=CRITICAL, ha="right", va="center", linespacing=1.5)

    ax.set_yticks([])
    ax.set_ylim(-0.95, 2.6)
    ax.set_xlim(-11, 9)
    ax.set_xlabel("realized return on stake, held to settlement   (%)")
    _frame(ax, xgrid=True, ygrid=False)

    _title(fig, "The exchange offers a side of the market a sportsbook cannot",
           "709,126 fills across 509 games. Takers pay for immediacy and gain no edge; makers are "
           "paid for supplying it. At a bookmaker only one of these roles exists.")
    _note(fig, "why_sports.log · CAUTION: each realized figure is individually n.s. with game clustering "
               "(se ~7pp over 509 games). What is measured precisely is the WEDGE - spread plus fee - not "
               "a profit opportunity. Read the red line, not the bars.")
    _save(fig, "F11_maker_taker")


# ==================================================================== F12 ===
def f12_two_layer():
    """Who stands behind the quote: the peer-to-peer claim, measured."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.8, 3.6),
                                 gridspec_kw={"width_ratios": [1.35, 1]})
    fig.subplots_adjust(top=0.68, bottom=0.30, wspace=0.42, left=0.155, right=0.97)

    ys = [1, 0]
    for i, (label, (bid, ask)) in enumerate(LAYERS.items()):
        y = ys[i]
        a1.barh(y + 0.11, bid, height=0.20, color=K, zorder=3)
        a1.barh(y - 0.11, ask, height=0.20, color=K, alpha=0.55, zorder=3)
        a1.text(ask + 700, y - 0.11, f"{ask:,} ask", va="center", fontsize=7.8, color=INK2)
        a1.text(bid + 700, y + 0.11, f"{bid:,} bid", va="center", fontsize=7.8, color=INK2)
        a1.text(-0.03, y, label, va="center", ha="right", fontsize=8.6, color=INK,
                transform=a1.get_yaxis_transform())
    fig.text(0.36, 0.055, "the standing size sits BEHIND the best price:" + NL +
             "8x the touch, and twice as balanced",
             fontsize=7.6, color=INK2, ha="center", linespacing=1.5, va="bottom")
    a1.set_yticks([])
    a1.set_ylim(-0.55, 1.5)
    a1.set_xlim(0, 34000)
    a1.set_xticks([0, 10000, 20000, 30000])
    a1.set_xticklabels(["0", "10k", "20k", "30k"])
    a1.set_xlabel("median resting contracts, one side")
    a1.set_title("The book has two layers", loc="left", color=INK, pad=9)
    _frame(a1, xgrid=True, ygrid=False)

    for i, (name, col) in enumerate((("Kalshi", K), ("Polymarket", P))):
        a2.bar(i, TOUCH_RETAIL[name], width=0.42, color=col, zorder=3)
        a2.text(i, TOUCH_RETAIL[name] + 0.9, f"{TOUCH_RETAIL[name]:.1f}%",
                ha="center", fontsize=8.8, color=INK)
    a2.set_xticks([0, 1])
    a2.set_xticklabels(["Kalshi", "Polymarket"], fontsize=8.6, color=INK)
    a2.set_xlim(-0.6, 1.6)
    a2.set_ylim(0, 28)
    a2.set_ylabel("share of snapshots")
    a2.set_title("How often is a retail-sized" + NL + "order the best quote?",
                 loc="left", color=INK, pad=9, fontsize=9.6)
    fig.text(0.755, 0.055, "Kalshi wears a retail surface over a professional" + NL +
             "layer; Polymarket's touch is itself professional-sized",
             fontsize=7.6, color=INK2, ha="center", linespacing=1.5, va="bottom")
    _frame(a2)

    _title(fig, "Who is actually on the other side",
           "85,453 depth snapshots over 564 games. Two-sided size at this scale is professional "
           "market-making, not organic peer supply.")
    _note(fig, "maker_structure.log, immediacy.log · public trade data carries no member IDs, so the "
               "exchange affiliate's own share of this layer cannot be measured from outside - a stated "
               "limitation, and the one place the report relies on the documentary record.")
    _save(fig, "F12_two_layer_book")


# ==================================================================== F13 ===
def f13_scorecard():
    """The operational criteria, and the single facet that matches a sportsbook."""
    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    fig.subplots_adjust(top=0.76, bottom=0.06, left=0.005, right=0.995)
    ax.axis("off")

    n = len(SCORECARD)
    ax.text(0.005, 1.02, "CRITERION", fontsize=7.6, color=MUTED, fontweight="bold")
    ax.text(0.28, 1.02, "IF THIS WERE A GAMBLING PRODUCT", fontsize=7.6,
            color=MUTED, fontweight="bold")
    ax.text(0.60, 1.02, "WHAT THE DATA SHOW", fontsize=7.6, color=MUTED, fontweight="bold")
    ax.plot([0.005, 0.995], [0.995, 0.995], color=AXIS, lw=0.9)

    for i, (crit, predicted, found, matches) in enumerate(SCORECARD):
        y = 0.93 - i * 0.132
        if matches:
            ax.add_patch(plt.Rectangle((0.0, y - 0.052), 1.0, 0.108,
                                       color=CRITICAL, alpha=0.07, lw=0))
        ax.text(0.005, y, crit, fontsize=8.8, color=INK, va="center",
                fontweight="bold" if matches else "normal")
        ax.text(0.28, y, predicted, fontsize=8.2, color=MUTED, va="center")
        ax.text(0.60, y, found, fontsize=8.2,
                color=CRITICAL if matches else INK2, va="center")
        ax.plot([0.245, 0.265], [y, y], color=AXIS, lw=0.8)
        ax.plot([0.565, 0.585], [y, y], color=AXIS, lw=0.8)

    ax.set_xlim(0, 1)
    ax.set_ylim(0.03, 1.06)

    _title(fig, "Six criteria say forecasting instrument. The seventh reaches the customer.",
           "The facets are the market-efficiency literature's, not ours. Only the last one - what the "
           "house takes - matches what a sportsbook does, and it is the only one a participant feels.")
    _note(fig, "three_way.log, decomposition.log, model_benchmark.log, coherence.log, margin_dist.log, "
               "totals.log, profitability.log, immediacy.log · distributional row reflects the "
               "2026-08-23 ladder-convention correction.", y=0.012)
    _save(fig, "F13_scorecard")


# ==================================================================== F14 ===
def f14_immediacy():
    """Depth is never the binding cost for the customer this project measures."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.8, 3.6))
    fig.subplots_adjust(top=0.70, bottom=0.24, wspace=0.30, left=0.085, right=0.97)

    x = np.arange(len(SIZES))
    for ax, data, ylab, title, ylim in (
        (a1, COST, "median cost to cross   (cents)", "What it costs", (0, 1.85)),
        (a2, FILL, "share of order books   (%)", "How often it fits", (0, 108)),
    ):
        for name, col in (("Kalshi", K), ("Polymarket", P)):
            ax.plot(x, data[name], "-o", color=col, lw=2, ms=5.5, zorder=3,
                    markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.set_xticks(x)
        ax.set_xticklabels(["10", "100", "1k", "10k", "50k", "200k"])
        ax.set_xlim(-0.3, len(SIZES) - 0.7)
        ax.set_ylim(*ylim)
        ax.set_xlabel("order size (units)")
        ax.set_ylabel(ylab)
        ax.set_title(title, loc="left", color=INK, pad=9)
        ax.axvspan(-0.3, 0.42, color=INK, alpha=0.045, zorder=0)
        _frame(ax)

    a1.text(0.06, 1.62, "where the median" + NL + "customer trades" + NL + "(30 units)",
            fontsize=7.6, color=INK2, linespacing=1.5, va="top")
    a1.text(2.55, 0.95, "Polymarket", color=P, fontsize=8.6, fontweight="bold")
    a1.text(3.15, 0.30, "Kalshi", color=K, fontsize=8.6, fontweight="bold")
    a2.text(0.55, 30, "capacity, not price," + NL + "is what runs out",
            fontsize=7.8, color=INK2, linespacing=1.5)

    _title(fig, "For the customer this project measures, depth is never the binding cost",
           "162,615 order-book snapshots over 564 games. The median fill is 30 contracts, about 16 dollars "
           "at stake - it sits inside the touch in 89% of Kalshi snapshots and 95% of Polymarket's.")
    _note(fig, "immediacy.log · the spread and the fee are the whole retail cost story; the capacity "
               "limit binds on institutional-sized orders, which the fill tape shows are not what "
               "this clientele sends.")
    _save(fig, "F14_immediacy")


# ================================================================= F1 alt ===
def f1alt_tiles():
    """The headline as three numbers rather than two panels."""
    fig = plt.figure(figsize=(7.8, 2.9))
    _title(fig, "Same games, three institutions, two questions",
           "5,333 games priced by a CFTC-regulated exchange, an offshore crypto exchange, and the "
           "professional sportsbook complex.")
    tiles = [
        ("0.2196", "Brier score, all three venues", "within 0.0002 of each other", K),
        ("4.2%", "all-in cost to a taker", "Kalshi and the sportsbooks alike", CRITICAL),
        ("13e-3", "how far all three beat", "a public-statistics floor (z~7.3)", B),
    ]
    for i, (big, label, sub, col) in enumerate(tiles):
        x = 0.02 + i * 0.335
        fig.text(x, 0.545, big, fontsize=34, fontweight="bold", color=col, va="top")
        fig.text(x, 0.245, label, fontsize=9.4, color=INK, va="top")
        fig.text(x, 0.155, sub, fontsize=8.2, color=MUTED, va="top")
        if i:
            fig.lines.append(Line2D([x - 0.025, x - 0.025], [0.10, 0.60],
                                    transform=fig.transFigure, color=GRID, lw=1))
    _note(fig, "three_way.log, immediacy.log, model_benchmark.log · the first two numbers are the "
               "report's whole argument: the forecast is excellent and the customer's cost is a "
               "sportsbook's.")
    _save(fig, "F1alt_stat_tiles")


# ================================================================= F2 alt ===
def f2alt_deviation():
    """The same data as a residual: what the 45-degree line hides."""
    from src.analysis.report_visuals import CORE
    import pandas as pd

    d = pd.read_csv(CORE)
    d = d[d.clean_set.astype(bool)]
    cols = {"Kalshi": "kalshi_home_prob", "Polymarket": "polymarket_home_prob",
            "Sportsbook": "book_home_prob_devig"}
    d = d.dropna(subset=list(cols.values()) + ["home_won"])
    edges = np.arange(0.05, 1.00, 0.10)

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    fig.subplots_adjust(top=0.74, bottom=0.155, left=0.10, right=0.97)
    ax.axhline(0, color=AXIS, lw=1.1, zorder=2)

    for name, col in VENUES:
        p = np.concatenate([d[cols[name]].values, 1 - d[cols[name]].values])
        y = np.concatenate([d.home_won.values, 1 - d.home_won.values])
        idx = np.digitize(p, edges)
        xs, ys = [], []
        for b in range(1, len(edges)):
            m = idx == b
            if m.sum() < 30:
                continue
            xs.append(p[m].mean())
            ys.append(100 * (y[m].mean() - p[m].mean()))
        ax.plot(xs, ys, "-o", color=col, lw=2, ms=5.5, zorder=3,
                markeredgecolor=SURFACE, markeredgewidth=1.5)
        dy = {"Kalshi": -0.30, "Polymarket": -0.95, "Sportsbook": 0.35}[name]
        ax.text(xs[-1] + 0.012, ys[-1] + dy, name, color=col, fontsize=8.6,
                fontweight="bold", va="center")

    ax.text(1.015, -2.05, "the mild compression around even money" + NL +
            "is SHARED: the sportsbooks show it too," + NL +
            "so it is a property of the games, not" + NL + "of any one institution",
            fontsize=7.8, color=INK2, linespacing=1.55, va="top", ha="right")
    ax.set_xlim(0.04, 1.06)
    ax.set_ylim(-4.6, 4.6)
    ax.set_xticks(np.arange(0.1, 1.0, 0.1))
    ax.set_xticklabels([f"{int(v*100)}%" for v in np.arange(0.1, 1.0, 0.1)])
    ax.set_xlabel("price the market charged")
    ax.set_ylabel("realized minus priced   (percentage points)")
    _frame(ax)

    _title(fig, "The same result at higher magnification: every deviation is shared",
           "Realized win rate minus the price charged. A gambling product would show a systematic "
           "tilt against the customer; there is none, at any price level, at any venue.")
    _note(fig, "recomputed from analysis_core.csv, matching plain_calibration.log · the sportsbook's "
               "10% and 90% bands deviate most (-3.7pt and +3.7pt), the exchanges' least.")
    _save(fig, "F2alt_deviation")


# ================================================================= F3 alt ===
def f3alt_simple():
    """The forest without the anchor ladder, for a first-time reader."""
    fig, ax = plt.subplots(figsize=(7.0, 3.0))
    fig.subplots_adjust(top=0.66, bottom=0.24, left=0.28, right=0.97)

    ax.axvspan(-1, 1, color=K, alpha=0.08, zorder=0)
    ax.axvline(0, color=AXIS, lw=1.0, zorder=1)
    for i, (name, est, lo, hi) in enumerate(reversed(POOLED_CI)):
        ax.plot([lo, hi], [i, i], color=K, lw=2.6, solid_capstyle="round", zorder=3)
        ax.plot([est], [i], "o", ms=7, color=K, zorder=4,
                markeredgecolor=SURFACE, markeredgewidth=1.8)
        ax.text(-0.03, i, name, va="center", ha="right", fontsize=8.8, color=INK,
                transform=ax.get_yaxis_transform())
    ax.text(1.0, 2.62, "the pre-stated" + NL + "equivalence margin",
            fontsize=7.8, color=INK2, ha="center", linespacing=1.4)

    ax.set_yticks([])
    ax.set_ylim(-0.6, 3.05)
    ax.set_xlim(-1.35, 1.35)
    ax.set_xlabel("difference in Brier score   (x10-3, 90% CI)")
    _frame(ax, xgrid=True, ygrid=False)

    _title(fig, "Every pairwise difference sits inside the pre-stated margin",
           "Not merely 'no significant difference' - formally equivalent, against a margin fixed in "
           "July before these comparisons were run.")
    _note(fig, "rigor.log · the margin tolerates a systematic 3.16pt pricing error; every interval "
               "here is narrower than half of it.")
    _save(fig, "F3alt_simple_forest")


# ================================================================= F6 alt ===
def f6alt_curves():
    """The boundary shown across the whole price range rather than summarised."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.8, 3.9), sharey=True)
    fig.subplots_adjust(top=0.68, bottom=0.20, wspace=0.07, left=0.09, right=0.97)

    for ax, data, title in (
        (a1, GAME_RETURN, "Repeated markets: single games"),
        (a2, FUTURES_RETURN, "One-shot markets: championships, awards, win totals"),
    ):
        ax.axhline(1.0, color=AXIS, lw=1.1, zorder=2)
        for name, col in VENUES:
            if name not in data:
                continue
            xs, ys = data[name]
            ax.plot(xs, ys, "-o", color=col, lw=1.9, ms=5, zorder=3,
                    markeredgecolor=SURFACE, markeredgewidth=1.4)
        ax.set_xlim(-0.03, 0.95)
        ax.set_ylim(-0.08, 1.45)
        ax.set_xticks([0, 0.25, 0.5, 0.75])
        ax.set_xticklabels(["0c", "25c", "50c", "75c"])
        ax.set_xlabel("price of the contract")
        ax.set_title(title, loc="left", color=INK, pad=9, fontsize=9.6)
        _frame(ax)

    a1.set_ylabel("what one dollar staked returned")
    a1.set_yticks([0, 0.5, 1.0])
    a1.set_yticklabels(["nothing", "half", "fair"])
    for name, col, dy in (("Kalshi", K, 0.30), ("Polymarket", P, 0.18), ("Sportsbook", B, 0.06)):
        a1.text(0.42, dy, name, color=col, fontsize=8.6, fontweight="bold")
    a2.text(0.30, 0.10, "every venue's" + NL + "long-shot tail" + NL + "collapses here",
            fontsize=7.8, color=INK2, linespacing=1.5)

    _title(fig, "What fails is the kind of market, not the kind of institution",
           "The same three institutions, across the full price range. On the left they track fair at "
           "every level; on the right all three break, and they break together.")
    _note(fig, "plain_calibration.log, futures_calibration.log, book_outrights.log · sparse futures "
               "buckets are joined for legibility, not because the price scale is continuous · "
               "the books' sub-10c point moves from 0.34 to 0.52 dollars under Shin de-vig.")
    _save(fig, "F6alt_price_curves")


# ================================================================= F7 alt ===
def f7alt_two_readings():
    """The same arithmetic at both measured cost rates: structural and realized."""
    n = np.arange(0, 121)
    struct = (1 - COST_RATE) ** n
    realized = (1 - 0.0777) ** n          # horizon_translation.log realized column

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    fig.subplots_adjust(top=0.72, bottom=0.155, left=0.095, right=0.97)

    ax.fill_between(n, realized, struct, color=K, alpha=0.09, zorder=1)
    ax.plot(n, struct, color=K, lw=2.2, zorder=3)
    ax.plot(n, realized, color=P, lw=2.2, zorder=3)
    ax.text(52, 0.335, "at the structural cost, -4.6% a position",
            color=K, fontsize=8.4, fontweight="bold")
    ax.text(30, 0.205, "at the realized taker loss, -7.7%",
            color=P, fontsize=8.4, fontweight="bold")

    ax.axvline(TICKET_EQUIV, color=CRITICAL, lw=1.3, zorder=2)
    ax.text(TICKET_EQUIV + 2.2, 0.955,
            f"{TICKET_EQUIV} positions at the structural rate" + NL +
            "= one futures ticket held from a week out",
            fontsize=7.9, color=CRITICAL, va="top", linespacing=1.5)

    for series, col in ((struct, K), (realized, P)):
        ax.plot([26], [series[26]], "o", ms=6.5, color=col, zorder=4,
                markeredgecolor=SURFACE, markeredgewidth=1.6)
    ax.annotate("one bet a week for a season" + NL + "leaves 30% to 12%",
                xy=(26, realized[26]), xytext=(30, 0.62), fontsize=8,
                color=INK2, linespacing=1.5,
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.9))

    ax.set_xlim(-3, 120)
    ax.set_ylim(0, 1.04)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("settled positions over one ~26-week season")
    ax.set_ylabel("bankroll remaining")
    _frame(ax)

    _title(fig, "The same arithmetic, bracketed by both measured cost rates",
           "A weekly bettor keeps between 30% and 12% of a bankroll across one season. Which end "
           "you land on depends on the cost measure, not on whether the prices were any good.")
    _note(fig, "horizon_translation.log · the STRUCTURAL rate is the anchor: it is fixed by the quote "
               "and the fee schedule. The realized rate agrees but its game-clustered 90% CI runs "
               "-19.5% to +2.9% over 513 games - outcomes are noisy, the cost is not.")
    _save(fig, "F7alt_two_rates")



def main():
    print("building additional + alternative figures -> results/report/")
    f10_formation(); f11_maker_taker(); f12_two_layer(); f13_scorecard(); f14_immediacy()
    f1alt_tiles(); f2alt_deviation(); f3alt_simple(); f6alt_curves(); f7alt_two_readings()
    print("done.")


if __name__ == "__main__":
    main()
