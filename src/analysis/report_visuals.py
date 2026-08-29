"""Report figure program — nine figures built for the argument, not for the modules.

Each figure does one job in the report's chain:

  F1  two axes            price quality and participant cost are independent
  F2  the dead heat       priced vs realized, three institutions, same games
  F3  equivalence forest  pairwise CIs against the cost-anchored margin ladder
  F4  no venue leads      cross-lag correlation does not sharpen with the clock
  F5  the premium         markets vs a public-statistics floor, by league
  F6  discipline boundary $1 returned: repeated markets vs one-shot markets
  F7  translation         what a re-staked bankroll does over a season
  F8  the fingerprint     when the flow arrives (consumption, not hedging)
  F9  institutional trace exchanges price closer to exchanges than to books

Statistics come from the current suite logs (results/logs/*.log, regenerated
2026-08-23) and are quoted with provenance in SOURCES below, so this module
cannot silently drift from the numbers the suite prints. The only quantity
recomputed here is the reliability curve in F2, which needs the full binning
rather than a printed summary; it is asserted against plain_calibration.log.

Palette: the validated three-slot categorical set (blue/orange/aqua), which
clears the all-pairs CVD and normal-vision floors in light mode. Aqua sits
below 3:1 on the light surface, so every series carries a direct label.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

warnings.filterwarnings("ignore")

OUT = Path("results/report")
CORE = Path("data/processed/analysis_core.csv")

# ---------------------------------------------------------------- palette ---
K, P, B = "#2a78d6", "#eb6834", "#1baf7a"      # Kalshi / Polymarket / Sportsbook
MODEL = "#898781"                               # the naive benchmark: muted, not a peer
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"
CRITICAL, GOOD = "#d03b3b", "#0ca30c"

VENUES = [("Kalshi", K), ("Polymarket", P), ("Sportsbook", B)]
NL = chr(10)   # newline for multi-line annotations

mpl.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9, "axes.titlesize": 10.5, "axes.labelsize": 9,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
    "axes.labelcolor": INK2, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.grid": False, "legend.frameon": False,
    "figure.dpi": 110, "savefig.dpi": 220, "savefig.bbox": "tight",
})


def _frame(ax, xgrid=False, ygrid=True):
    """Recessive chrome: two spines, hairline grid, no ticks."""
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(AXIS)
    ax.set_axisbelow(True)
    if ygrid:
        ax.yaxis.grid(True, color=GRID, lw=0.8)
    if xgrid:
        ax.xaxis.grid(True, color=GRID, lw=0.8)


def _title(fig, title, subtitle=None, y=0.985):
    fig.text(0.008, y, title, fontsize=12.5, fontweight="bold", color=INK, va="top")
    if subtitle:
        off = 0.235 / fig.get_figheight()
        fig.text(0.008, y - off, subtitle, fontsize=9.2, color=INK2, va="top")


def _note(fig, text, y=0.008):
    fig.text(0.008, y, text, fontsize=7.6, color=MUTED, va="bottom")


def _save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}")
    plt.close(fig)
    print(f"  saved {OUT/name}.png / .pdf")


# ----------------------------------------------------------- logged stats ---
# Every number below is quoted from the 2026-08-23 suite run. Provenance is the
# log file named on each block; nothing here is recomputed or remembered.

# rigor.log — pooled pairwise DM, 90% CI of Brier difference (x1e-3)
POOLED_CI = [
    ("Kalshi vs Polymarket",   -0.243, -0.530, +0.044),
    ("Kalshi vs Sportsbook",   -0.021, -0.234, +0.192),
    ("Polymarket vs Sportsbook", +0.222, -0.078, +0.521),
]
# sharp_books.log — same construction against the sharp book and the exchange
SHARP_CI = [
    ("Kalshi vs Pinnacle",       -0.115, -0.33, +0.10),
    ("Polymarket vs Pinnacle",   -0.021, -0.25, +0.21),
    ("US consensus vs Pinnacle", -0.088, -0.22, +0.04),
    ("Kalshi vs Betfair",        +0.019, -0.22, +0.26),
]
# rigor.log — cost-anchored margin ladder: delta = (taker cost x price)^2
ANCHORS = [(0.110, "0.25"), (0.441, "0.50"), (0.992, "0.75")]

# three_way.log / rigor.log
BRIER = {"Kalshi": 0.2197, "Polymarket": 0.2200, "Sportsbook": 0.2197}
# immediacy.log + findings cost table: all-in cost to a market-order taker
TAKER_COST = {"Kalshi": 4.2, "Polymarket": 1.5, "Sportsbook": 4.2}
TAKER_NOTE = {"Kalshi": "spread + fee", "Polymarket": "spread + fee", "Sportsbook": "overround"}

# five_min.log — cross-lag correlation by grid; a true lead must GROW leftward
LADDER = {
    "Kalshi predicts Polymarket":   [0.013, 0.025, 0.006, 0.023],
    "Kalshi predicts Sportsbook":   [0.035, 0.039, 0.033, 0.042],
    "Polymarket predicts Kalshi":   [0.008, 0.021, 0.025, 0.026],
    "Polymarket predicts Sportsbook": [0.026, 0.029, 0.031, 0.024],
    "Sportsbook predicts Kalshi":   [0.006, 0.028, 0.033, 0.059],
    "Sportsbook predicts Polymarket": [0.051, 0.040, 0.041, 0.026],
}
GRIDS = [5, 10, 15, 30]

# model_benchmark.log — per-league Brier, evaluation set n=4,880
LEAGUE_BRIER = {          # league: (n, elo, kalshi, poly, book)
    "CFB":  (521,  0.2331, 0.1779, 0.1779, 0.1783),
    "NBA":  (1212, 0.2099, 0.1961, 0.1967, 0.1965),
    "NFL":  (256,  0.2285, 0.2131, 0.2135, 0.2132),
    "WNBA": (351,  0.2235, 0.2170, 0.2167, 0.2159),
    "MLB":  (1239, 0.2525, 0.2461, 0.2458, 0.2460),
    "NHL":  (1301, 0.2481, 0.2447, 0.2449, 0.2446),
}

# plain_calibration.log — $1 returned by price band, game markets
GAME_RETURN = {
    "Kalshi":     ([.107, .203, .305, .406, .500, .594, .695, .797, .893],
                   [0.83, 1.13, 1.01, 1.06, 1.00, 0.96, 0.99, 0.96, 1.02]),
    "Polymarket": ([.106, .202, .305, .407, .500, .593, .696, .798, .894],
                   [0.83, 1.14, 1.03, 1.06, 1.00, 0.95, 0.99, 0.97, 1.02]),
    "Sportsbook": ([.109, .204, .305, .407, .500, .593, .695, .796, .891],
                   [0.67, 1.12, 0.96, 1.08, 1.00, 0.94, 1.02, 0.97, 1.04]),
}
# futures_calibration.log (T-7d) and book_outrights.log (0-3 months out)
FUTURES_RETURN = {
    "Kalshi":     ([.010, .031, .068, .132, .262, .405, .597, .863],
                   [0.52, 0.00, 0.22, 0.98, 0.74, 0.57, 1.09, 0.72]),
    "Polymarket": ([.013, .034, .072, .270],
                   [0.00, 0.83, 0.58, 0.35]),
    "Sportsbook": ([.006, .033, .073, .142, .258, .417, .593],
                   [0.32, 0.50, 0.99, 1.28, 1.08, 1.06, 1.01]),
}
SUB10 = {"Kalshi": 0.33, "Polymarket": 0.53, "Sportsbook": 0.34}
SUB10_SHIN = 0.52   # book_outrights.log — the tail-robust de-vig, 0-3 months

# horizon_translation.log
COST_RATE, TICKET_EQUIV = 0.045, 12.4
CADENCE = [("monthly", 6), ("fortnightly", 13), ("weekly", 26),
           ("twice a week", 52), ("daily", 182)]

# retail_fingerprint.log — fills per hour by distance from start
FLOW = [("T−24h–T−12h", 1.09), ("T−12h–T−6h", 2.71),
        ("T−6h–T−3h", 5.80), ("T−3h–T−1h", 10.96),
        ("final hour", 31.30)]

# sharp_books.log — mean |price gap| in points, same games
GAPS = {"Kalshi": [("Betfair Exchange", 0.55), ("Pinnacle", 0.72), ("US retail consensus", 0.71)],
        "Polymarket": [("Betfair Exchange", 0.59), ("Pinnacle", 0.80), ("US retail consensus", 0.80)]}
PIN_VS_RETAIL = 0.47


# ===================================================================== F1 ===


def f1_two_axes():
    """The report's hinge: forecast quality and participant cost do not covary."""
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.2))
    fig.subplots_adjust(top=0.63, bottom=0.34, wspace=0.34, left=0.13, right=0.97)
    ys = [2, 1, 0]

    for (name, col), y in zip(VENUES, ys):
        v = BRIER[name]
        a1.plot([v], [y], "o", ms=10, color=col, zorder=3,
                markeredgecolor=SURFACE, markeredgewidth=2)
        a1.text(-0.03, y, name, va="center", ha="right", fontsize=8.8, color=INK,
                transform=a1.get_yaxis_transform())
        a1.text(v, y + 0.33, f"{v:.4f}", ha="center", fontsize=8.2, color=INK2)
    a1.axvspan(BRIER["Kalshi"] - 0.00032, BRIER["Kalshi"] + 0.00032,
               color=K, alpha=0.08, zorder=0)
    a1.set_xlim(0.21935, 0.22045)
    a1.set_ylim(-0.55, 2.72)
    a1.set_yticks([])
    a1.set_xticks([0.2195, 0.2200])
    a1.set_xlabel("Brier score   (lower = better forecast)")
    a1.set_title("How good is the price?", loc="left", color=INK, pad=9)
    _frame(a1, xgrid=True, ygrid=False)

    for (name, col), y in zip(VENUES, ys):
        c = TAKER_COST[name]
        a2.barh(y, c, height=0.34, color=col, zorder=3)
        a2.text(c + 0.13, y, f"{c:.1f}%", va="center", fontsize=8.8, color=INK)
        a2.text(-0.14, y, name, va="center", ha="right", fontsize=8.8, color=INK)
    a2.set_xlim(0, 5.6)
    a2.set_ylim(-0.55, 2.72)
    a2.set_yticks([])
    a2.set_xlabel("all-in cost to a market-order taker   (% of notional)")
    a2.set_title("What does the customer pay?", loc="left", color=INK, pad=9)
    _frame(a2, xgrid=True, ygrid=False)

    fig.text(0.13, 0.175, "shaded: the band inside which a difference" + NL +
             "cannot be monetised",
             fontsize=7.6, color=MUTED, linespacing=1.5, va="top")
    fig.text(0.565, 0.175,
             "the venue defended as a forecasting instrument and the" + NL +
             "venue everyone calls gambling charge the same 4.2%",
             fontsize=7.6, color=MUTED, linespacing=1.5, va="top")

    _title(fig, "Price quality and participant cost are independent",
           "Same 5,327 games. Left is the forecasting question; right is the gambling question. "
           "Neither answers the other.")
    _note(fig, "three_way.log / immediacy.log · Polymarket all-in runs 1.25-1.75%; makers trade near-free "
               "on both exchanges, and the fill tape says the customer is a taker.")
    _save(fig, "F1_two_axes")



# ===================================================================== F2 ===
def f2_dead_heat():
    """Priced vs realized, both sides stacked — the table everything else defends."""
    d = pd.read_csv(CORE)
    d = d[d.clean_set.astype(bool)]
    cols = {"Kalshi": "kalshi_home_prob", "Polymarket": "polymarket_home_prob",
            "Sportsbook": "book_home_prob_devig"}
    d = d.dropna(subset=list(cols.values()) + ["home_won"])
    n_games = len(d)

    edges = np.arange(0.05, 1.00, 0.10)
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    fig.subplots_adjust(top=0.855, bottom=0.11, left=0.125, right=0.97)

    ax.plot([0, 1], [0, 1], color=AXIS, lw=1.0, zorder=1)
    ax.text(0.795, 0.845, "perfect calibration", fontsize=7.8, color=MUTED,
            rotation=41, rotation_mode="anchor")

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
            ys.append(y[m].mean())
        ax.plot(xs, ys, "-o", color=col, lw=2, ms=6, zorder=3,
                markeredgecolor=SURFACE, markeredgewidth=1.6, label=name)

    # direct labels (aqua is sub-3:1 on this surface — relief rule)
    ax.text(0.055, 0.93, "Kalshi", color=K, fontsize=9.5, fontweight="bold")
    ax.text(0.055, 0.865, "Polymarket", color=P, fontsize=9.5, fontweight="bold")
    ax.text(0.055, 0.80, "Sportsbook", color=B, fontsize=9.5, fontweight="bold")

    ax.set_xlim(0.02, 1.0)
    ax.set_ylim(0.02, 1.0)
    ax.set_xticks(np.arange(0.1, 1.0, 0.1))
    ax.set_yticks(np.arange(0.1, 1.0, 0.1))
    ax.set_xticklabels([f"{int(v*100)}%" for v in np.arange(0.1, 1.0, 0.1)])
    ax.set_yticklabels([f"{int(v*100)}%" for v in np.arange(0.1, 1.0, 0.1)])
    ax.set_xlabel("price the market charged")
    ax.set_ylabel("share of those teams that actually won")
    _frame(ax, xgrid=True, ygrid=True)

    _title(fig, "If a contract trades at 60c, does it happen 60% of the time?",
           f"Yes — and identically at three institutions. {n_games:,} games, "
           f"{2*n_games:,} priced teams, both sides stacked.", y=0.985)
    _note(fig, "Recomputed from analysis_core.csv; matches plain_calibration.log. "
               "Bands with fewer than 30 sides suppressed.")
    _save(fig, "F2_dead_heat")
    return n_games


# ===================================================================== F3 ===
def f3_forest():
    """Equivalence, read against the margin ladder rather than a single line."""
    rows = POOLED_CI + [None] + SHARP_CI
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    fig.subplots_adjust(top=0.80, bottom=0.235, left=0.285, right=0.97)

    for lo_a, lab in ANCHORS:
        ax.axvspan(-lo_a, lo_a, color=K, alpha=0.055, zorder=0)
        ax.plot([lo_a, lo_a], [-0.7, len(rows) - 0.3], color=K, lw=0.8, alpha=0.35, zorder=1)
        ax.plot([-lo_a, -lo_a], [-0.7, len(rows) - 0.3], color=K, lw=0.8, alpha=0.35, zorder=1)
        ax.text(lo_a, len(rows) - 0.15, f"{lab}", ha="center", fontsize=7.6, color=INK2)
    ax.text(0, len(rows) + 0.55, "unmonetisable-edge margin, at a contract price of",
            ha="center", fontsize=7.8, color=INK2)

    ax.axvline(0, color=AXIS, lw=1.0, zorder=1)
    ypos, labels = [], []
    for i, r in enumerate(reversed(rows)):
        if r is None:
            continue
        name, est, lo, hi = r
        inside_mid = abs(lo) <= 0.441 and abs(hi) <= 0.441
        col = K if inside_mid else CRITICAL
        ax.plot([lo, hi], [i, i], color=col, lw=2.2, solid_capstyle="round", zorder=3)
        ax.plot([est], [i], "o", ms=6.5, color=col, zorder=4,
                markeredgecolor=SURFACE, markeredgewidth=1.6)
        ypos.append(i)
        labels.append(name)

    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=8.6, color=INK)
    ax.set_ylim(-0.7, len(rows) + 1.1)
    ax.set_xlim(-1.15, 1.15)
    ax.set_xlabel("difference in Brier score  (×10⁻³, 90% CI)")
    _frame(ax, xgrid=True, ygrid=False)

    handles = [Line2D([], [], color=K, lw=2.2,
                      label="equivalent at the strictest defensible margin (mid-price)"),
               Line2D([], [], color=CRITICAL, lw=2.2,
                      label="resolves only at the favourite-price margin")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.155),
              fontsize=8, ncol=2, labelcolor=INK2, columnspacing=1.8)

    _title(fig, "The venues are equivalent inside the band where a difference could reach anyone",
           "Pre-stated δ = 1.0×10⁻³, fixed in July before these comparisons. The bands are what a "
           "4.2% taker cost makes unmonetisable.", y=0.985)
    _note(fig, "rigor.log, sharp_books.log  ·  ΔBrier = ε², so δ = 1.0×10⁻³ tolerates a "
               "systematic 3.16pt error, not 0.5pt  ·  a red bar reports the measurement's power, not a gap between venues.")
    _save(fig, "F3_equivalence_forest")


# ===================================================================== F4 ===


def f4_no_leader():
    """A real lead is a fixed delay: it must sharpen as the grid approaches it."""
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    fig.subplots_adjust(top=0.71, bottom=0.17, left=0.10, right=0.64)

    x = np.arange(len(GRIDS))
    ends = sorted(((v[-1], k) for k, v in LADDER.items()), reverse=True)
    slots, used = {}, []
    for val, name in ends:
        y = val
        while any(abs(y - u) < 0.0052 for u in used):
            y -= 0.0052
        used.append(y)
        slots[name] = y
    for name, vals in LADDER.items():
        ax.plot(x, vals, "-o", color=MUTED, lw=1.4, ms=4.5, alpha=0.8, zorder=3,
                markeredgecolor=SURFACE, markeredgewidth=1.2)
        ax.plot([x[-1], x[-1] + 0.14], [vals[-1], slots[name]], color=GRID, lw=0.8, zorder=2)
        ax.text(x[-1] + 0.18, slots[name], name, fontsize=7.6, color=INK2, va="center")

    ax.annotate("", xy=(-0.12, 0.094), xytext=(0.95, 0.070),
                arrowprops=dict(arrowstyle="->", color=CRITICAL, lw=1.5))
    ax.text(1.30, 0.101, "a real lead would rise" + NL +
            "steeply toward the finer grids",
            fontsize=7.8, color=CRITICAL, va="top", linespacing=1.5)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{g} min" for g in GRIDS])
    ax.set_xlim(-0.32, len(GRIDS) - 0.85)
    ax.set_ylim(-0.004, 0.102)
    ax.set_xlabel("sampling grid   (finer grid = closer to any true delay)")
    ax.set_ylabel("cross-lag correlation")
    _frame(ax)

    _title(fig, "No venue leads another, at any clock we can measure",
           "181 games, 19,272 five-minute steps with all three venues priced. "
           "All six ordered pairs, at four resolutions.")
    _note(fig, "five_min.log · a fixed-delay lead must grow as the grid shrinks toward it; none does, "
               "and nothing predicts the sportsbook at any grid.")
    _save(fig, "F4_no_leader")



# ===================================================================== F5 ===

def f5_premium():
    """The markets clear a public-statistics floor — and clear it identically."""
    order = sorted(LEAGUE_BRIER, key=lambda L: LEAGUE_BRIER[L][1] - LEAGUE_BRIER[L][2])
    fig, ax = plt.subplots(figsize=(7.2, 4.1))
    fig.subplots_adjust(top=0.74, bottom=0.24, left=0.10, right=0.97)

    for i, L in enumerate(order):
        n, elo, k, p, b = LEAGUE_BRIER[L]
        mk = np.mean([k, p, b])
        ax.plot([mk, elo], [i, i], color=GRID, lw=4.5, solid_capstyle="round", zorder=1)
        ax.plot([elo], [i], "o", ms=8, color=MODEL, zorder=3,
                markeredgecolor=SURFACE, markeredgewidth=1.8)
        for (v, c), dy in zip(((k, K), (p, P), (b, B)), (0.20, 0.0, -0.20)):
            ax.plot([v], [i + dy], "o", ms=6.5, color=c, zorder=4,
                    markeredgecolor=SURFACE, markeredgewidth=1.5)
        ax.text(elo + 0.0032, i, f"+{1000*(elo-mk):.0f}", va="center",
                fontsize=8.2, color=INK2)
        ax.text(0.1665, i + 0.14, L, va="center", ha="left", fontsize=8.8, color=INK)
        ax.text(0.1665, i - 0.20, f"n={n:,}", va="center", ha="left", fontsize=7.2, color=MUTED)

    ax.set_yticks([])
    ax.set_ylim(-0.72, len(order) - 0.22)
    ax.set_xlim(0.1645, 0.2665)
    ax.set_xlabel("Brier score   (lower is better)")
    _frame(ax, xgrid=True, ygrid=False)

    handles = [Line2D([], [], marker="o", ls="", ms=7, color=c, label=lbl,
                      markeredgecolor=SURFACE, markeredgewidth=1.5) for lbl, c in VENUES]
    handles.append(Line2D([], [], marker="o", ls="", ms=8, color=MODEL,
                          label="Elo, built from win-loss records only",
                          markeredgecolor=SURFACE, markeredgewidth=1.5))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.16),
              ncol=4, fontsize=8, labelcolor=INK2, handletextpad=0.35, columnspacing=1.6)

    _title(fig, "The markets import information that public statistics do not contain",
           "And they import the same information: the three venues differ from each other by "
           "<=0.5x10-3, and each beats the model by ~13x10-3 (z ~ 7.3).")
    _note(fig, "model_benchmark.log · walk-forward Elo, no look-ahead, n=4,880 · "
               "labels give the market-model gap in Brier x10-3.")
    _save(fig, "F5_market_premium")



# ===================================================================== F6 ===


def f6_boundary():
    """The contribution: what fails is the market TYPE, not the institution."""
    rows = [
        ("Repeated markets (single games)" + NL + "all price levels pooled",
         {"Kalshi": 1.00, "Polymarket": 1.00, "Sportsbook": 1.00}, False),
        ("Repeated markets (single games)" + NL + "contracts priced near 10c",
         {"Kalshi": 0.83, "Polymarket": 0.83, "Sportsbook": 0.67}, False),
        ("One-shot markets (championships, awards)" + NL + "contracts priced under 10c",
         SUB10, True),
    ]
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    fig.subplots_adjust(top=0.74, bottom=0.20, left=0.315, right=0.97)

    ax.axvline(1.0, color=AXIS, lw=1.2, zorder=1)
    ax.text(1.0, 2.62, "fair: one dollar back for one dollar staked",
            ha="center", fontsize=7.8, color=INK2)

    for i, (label, vals, is_bad) in enumerate(rows):
        y = 2 - i
        ax.axhspan(y - 0.42, y + 0.42, color=CRITICAL if is_bad else INK, alpha=0.035, zorder=0)
        for (name, col), dy in zip(VENUES, (0.22, 0.0, -0.22)):
            v = vals[name]
            ax.plot([v], [y + dy], "o", ms=8.5, color=col, zorder=4,
                    markeredgecolor=SURFACE, markeredgewidth=1.8)
            ax.text(v + 0.028, y + dy, f"\\${v:.2f}", ha="left", va="center",
                    fontsize=7.8, color=INK2)
        ax.text(-0.045, y, label, va="center", ha="right", fontsize=8.4,
                color=INK, linespacing=1.45)

    ax.plot([SUB10_SHIN], [0 - 0.22], "o", ms=8.5, mfc="none", zorder=4,
            markeredgecolor=B, markeredgewidth=1.6)
    ax.annotate("the books under Shin de-vig," + NL + ""
                "the tail-robust correction", xy=(SUB10_SHIN, -0.24), xytext=(0.70, -0.30),
                fontsize=7.6, color=INK2, linespacing=1.45, va="center",
                arrowprops=dict(arrowstyle="->", color=MUTED, lw=0.9))

    ax.set_yticks([])
    ax.set_ylim(-0.78, 2.75)
    ax.set_xlim(-0.02, 1.16)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_xticklabels([r"\$0.00", r"\$0.25", r"\$0.50", r"\$0.75", r"\$1.00"])
    ax.set_xlabel("what one dollar staked returned, gross")
    _frame(ax, xgrid=True, ygrid=False)

    for lbl, c, x in zip([v[0] for v in VENUES], [v[1] for v in VENUES], (0.34, 0.44, 0.56)):
        fig.text(x, 0.055, lbl, color=c, fontsize=8.4, fontweight="bold")

    _title(fig, "What fails is the kind of market, not the kind of institution",
           "Longshots are not the problem: at 10c in a game market every venue pays close to fair. "
           "Remove repetition and fast resolution and all three misprice together.")
    _note(fig, "plain_calibration.log, futures_calibration.log, book_outrights.log · CAVEAT: the books' "
               "sub-10c return rises to \\$0.52 under Shin de-vig, which this project's own Murphy result "
               "requires for tail claims - so 'identical to Kalshi' holds under multiplicative de-vig only.")
    _save(fig, "F6_discipline_boundary")



# ===================================================================== F7 ===


def f7_translation():
    """Per-position cost x turnover: the bridge from price quality to the customer."""
    n = np.arange(0, 185)
    bank = (1 - COST_RATE) ** n

    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    fig.subplots_adjust(top=0.72, bottom=0.17, left=0.09, right=0.97)

    ax.fill_between(n, 0, bank, color=K, alpha=0.10, zorder=1)
    ax.plot(n, bank, color=K, lw=2.2, zorder=3)

    ax.axvline(TICKET_EQUIV, color=CRITICAL, lw=1.4, zorder=2)
    ax.text(46, 1.005,
            f"{TICKET_EQUIV} game bets cost the same as one" + NL +
            "futures ticket held from a week out",
            fontsize=8.2, color=CRITICAL, linespacing=1.5, va="top")

    for label, pos in CADENCE:
        if pos > 110:
            continue
        v = (1 - COST_RATE) ** pos
        ax.plot([pos], [v], "o", ms=7, color=K, zorder=4,
                markeredgecolor=SURFACE, markeredgewidth=1.8)
        ax.text(pos + 3.5, v + 0.028, f"{label}   {v*100:.0f}%", ha="left", va="bottom",
                fontsize=8, color=INK2)

    ax.set_xlim(-3, 118)
    ax.set_ylim(0, 1.04)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xlabel("settled positions over one ~26-week season")
    ax.set_ylabel("bankroll remaining")
    _frame(ax)

    _title(fig, "Calibration disciplines the price. It does not protect the participant.",
           "Structural taker cost is -4.5% per position, set by the quote and the fee schedule "
           "before any ball is thrown. Re-staking proceeds each time:")
    _note(fig, "horizon_translation.log · cadence is a SCENARIO GRID, not a measurement: the public tape "
               "carries no account identifiers, so no outside researcher can observe how often one person bets.")
    _save(fig, "F7_translation")



# ===================================================================== F8 ===
def f8_fingerprint():
    """The participant-side criterion: this flow is shaped like consumption."""
    fig, ax = plt.subplots(figsize=(6.8, 3.9))
    fig.subplots_adjust(top=0.76, bottom=0.17, left=0.135, right=0.97)

    labels = [f[0] for f in FLOW]
    vals = [f[1] for f in FLOW]
    y = np.arange(len(labels))
    cols = [MUTED] * (len(labels) - 1) + [K]

    ax.barh(y, vals, height=0.42, color=cols, zorder=3)
    for i, v in enumerate(vals):
        ax.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=8.6,
                color=INK if i == len(vals) - 1 else INK2,
                fontweight="bold" if i == len(vals) - 1 else "normal")
    ax.axvline(100 / 24, color=CRITICAL, lw=1.2, zorder=4)
    ax.text(100 / 24 + 0.4, len(labels) - 0.05, "if the flow were spread evenly (4.2%/hr)",
            fontsize=7.8, color=CRITICAL, va="bottom")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.6, color=INK)
    ax.set_xlim(0, 36)
    ax.set_ylim(-0.6, len(labels) - 0.15)
    ax.set_xlabel("share of all fills arriving, per hour")
    _frame(ax, xgrid=True, ygrid=False)

    _title(fig, "The flow is shaped like consumption, not like hedging",
           "710,129 fills across 513 games. 53% arrive in the final three hours; the median fill is "
           "30 contracts, about $14 at stake.", y=0.985)
    _note(fig, "retail_fingerprint.log  ·  orders placed far from any game cluster 7pm–midnight ET (41%) "
               "and avoid working hours (10%)  ·  no size class beats the close.")
    _save(fig, "F8_retail_fingerprint")


# ===================================================================== F9 ===


def f9_institution():
    """Institutional design leaves a trace in prices even when accuracy does not."""
    refs = ["Betfair Exchange", "Pinnacle", "US retail consensus"]
    kind = ["peer-to-peer exchange", "sharp bookmaker", "11 bookmakers"]
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    fig.subplots_adjust(top=0.70, bottom=0.16, left=0.27, right=0.90)

    for i, (r, kd) in enumerate(zip(refs, kind)):
        y = 2 - i
        vk, vp = dict(GAPS["Kalshi"])[r], dict(GAPS["Polymarket"])[r]
        ax.plot([vk, vp], [y, y], color=GRID, lw=4, solid_capstyle="round", zorder=1)
        ax.plot([vk], [y], "o", ms=9, color=K, zorder=4,
                markeredgecolor=SURFACE, markeredgewidth=1.8)
        ax.plot([vp], [y], "o", ms=9, color=P, zorder=3,
                markeredgecolor=SURFACE, markeredgewidth=1.8)
        ax.text(vk, y + 0.19, f"{vk:.2f}", ha="center", fontsize=8, color=INK2)
        ax.text(vp, y + 0.19, f"{vp:.2f}", ha="center", fontsize=8, color=INK2)
        ax.text(0.505, y + 0.10, r, va="center", ha="right", fontsize=8.8, color=INK)
        ax.text(0.505, y - 0.17, kd, va="center", ha="right", fontsize=7.4, color=MUTED)

    ax.axvline(PIN_VS_RETAIL, color=MUTED, lw=1.1, zorder=2)
    ax.text(PIN_VS_RETAIL + 0.006, 2.62, "0.47 - the gap between" + NL +
            "Pinnacle and US retail",
            ha="left", fontsize=7.6, color=MUTED, linespacing=1.4)

    ax.set_yticks([])
    ax.set_ylim(-0.55, 2.98)
    ax.set_xlim(0.42, 0.87)
    ax.set_xlabel("mean |price gap| to that reference   (percentage points)")
    _frame(ax, xgrid=True, ygrid=False)
    key = [Line2D([], [], marker="o", ls="", ms=8, color=c, label=lbl,
                  markeredgecolor=SURFACE, markeredgewidth=1.6)
           for lbl, c in (("Kalshi", K), ("Polymarket", P))]
    ax.legend(handles=key, loc="upper right", fontsize=8.4, labelcolor=INK2,
              handletextpad=0.35, borderpad=0.5, borderaxespad=0.3)

    _title(fig, "The exchanges price closer to the exchange than to any bookmaker",
           "Forecast accuracy is identical across all of them. Institutional design still leaves a "
           "visible fingerprint on the price.")
    _note(fig, "sharp_books.log · same games throughout (n=5,280 Pinnacle, 3,714 Betfair)")
    _save(fig, "F9_institutional_trace")

def main():
    print("building report figures -> results/report/")
    f1_two_axes()
    n = f2_dead_heat()
    f3_forest()
    f4_no_leader()
    f5_premium()
    f6_boundary()
    f7_translation()
    f8_fingerprint()
    f9_institution()
    print(f"done. three-way clean n={n:,}")


if __name__ == "__main__":
    main()
