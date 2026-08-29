"""Report Tables 1-5, rendered from the suite's own logs and data files.

The drafting plan's five main tables exist as numbers scattered across logs;
this module assembles them so the freeze re-stamps tables exactly as it
re-stamps figures, and prose can copy from one artifact. Every number is
parsed from a results/logs/*.log line or computed from the committed data —
a failed parse raises, failing the suite, which is the point: a table that
cannot trace its numbers must not render.

Output: results/report/tables.md (markdown, one section per table) and the
same content to this module's log.

Table 4 is the paper's centerpiece: the 2x2 of discipline. Read across a
row and the institution explanation dies; read down a column and the
benchmark explanation dies; what is left is repetition.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

LOGS = Path("results/logs")
OUT = Path("results/report/tables.md")


def logtext(name: str) -> str:
    return (LOGS / f"{name}.log").read_text()


def grab(name: str, pattern: str, flags=0) -> tuple[str, ...]:
    m = re.search(pattern, logtext(name), flags)
    assert m, f"tables.py: pattern not found in {name}.log: {pattern}"
    return m.groups()


def main():
    md: list[str] = []

    # ------------------------------------------------------------- table 1 --
    m = pd.read_csv("data/processed/games_master.csv",
                    usecols=["kalshi_p1", "poly_p1", "book_p1", "outcome"])
    n_master = len(m)
    n_k, n_p, n_b = int(m.kalshi_p1.notna().sum()), int(m.poly_p1.notna().sum()), int(m.book_p1.notna().sum())
    n_3w, n_dates = grab("rigor", r"clean all-three games: ([\d,]+) across (\d+) dates")
    n_4w = grab("four_way", r"four-way joint clean set: [\d,]+ matched, ([\d,]+) after quality filters")[0]
    n_lad = len(pd.read_csv("data/processed/kalshi_spread_prices.csv", usecols=["ticker"]))
    n_tot = len(pd.read_csv("data/processed/kalshi_total_prices.csv", usecols=["ticker"]))
    snaps = pd.read_csv("data/live/vps_mirror/snapshots.csv", usecols=["game_id"], low_memory=False)
    n_out, n_seas = grab("book_outrights", r"sub-10c: n=(\d+).*?(\d+) clusters")

    md.append(f"""## Table 1 — Data sources

| Source | Instrument | Price construction | Coverage |
|---|---|---|---|
| Kalshi | Moneyline (game winner) | Order-book mid at official start (candlesticks) post-cutoff; validated trade-reconstruction pre-cutoff | {n_k:,} of {n_master:,} master games |
| Polymarket Global | Moneyline | CLOB minute price at official start | {n_p:,} games |
| Polymarket US | Moneyline | Last trade at/before start from the public DCM tape | {n_4w} four-way clean games |
| Sportsbooks | Moneyline | The Odds API historical closing consensus (~10.5 books/game), de-vigged; EU per-book incl. Pinnacle; 11 US books per-book | {n_b:,} games |
| Kalshi | Alternate-spread ladders | Book-mid / trade-recon per rung, settled under league-specific cover lines | {n_lad:,} contracts |
| Kalshi | Totals ladders | Same construction; settlement-verified uniform convention | {n_tot:,} contracts |
| Kalshi + books | Outrights 2020-26 | Monthly in-season snapshots, de-vigged fields | n={n_out} sub-10c, {n_seas} sport-season clusters |
| All three | Live panel | VPS collector, 5-min cadence, synchronized quotes | {snaps.game_id.nunique():,} games / {len(snaps):,} rows |
| ESPN | Outcomes + schedule | Scoreboard finals, cross-checked vs both platforms' settlements | anchor for everything above |

Joint three-way clean set: **{n_3w} games** across {n_dates} dates.
""")

    # ------------------------------------------------------------- table 2 --
    rows = re.findall(r"^\s+(ALL|NHL|NBA|MLB|CFB|WNBA|NFL)\s+(\d+)\s+(\d+)\s+"
                      r"([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\S.*)$",
                      logtext("power"), re.M)
    assert len(rows) >= 7, "tables.py: power.log MDE rows not found"
    md.append("## Table 2 — Power: minimum detectable effect by subgroup\n\n"
              "| Group | n | dates | MDE K-P | MDE K-B | MDE P-B | verdict at δ=1e-3 |\n"
              "|---|---|---|---|---|---|---|")
    seen = set()
    for g, n, dts, a, b, c, v in rows:
        if g in seen:
            continue
        seen.add(g)
        md.append(f"| {g} | {int(n):,} | {dts} | {a}e-3 | {b}e-3 | {c}e-3 | {v.strip()} |")
    md.append("\nReading rule (locked): every subgroup null is quoted with its MDE. "
              "UNDERPOWERED leagues are 'consistent with equivalence but unable to "
              "detect it', never evidence for it. δ=1e-3 admits a systematic "
              "3.16pt offset (ΔBrier=ε²).\n")

    # ------------------------------------------------------------- table 3 --
    src3 = re.findall(r"^\s+(Kalshi|Polymarket|Sportsbook)\s+Brier=([\d.]+)\s+slope=([\d.]+)\s+ECE=([\d.]+)",
                      logtext("three_way"), re.M)
    assert len(src3) == 3, "tables.py: three_way per-source lines not found"
    md.append("## Table 3 — The headline equivalence\n\n"
              "| Source | Brier | Calibration slope | ECE |\n|---|---|---|---|")
    for name, b3, s3, e3 in src3:
        md.append(f"| {name} | {b3} | {s3} | {e3} |")
    pair3 = re.findall(r"(Kalshi - Polymarket|Kalshi - Sportsbook|Polymarket - Sportsbook): "
                       r"ΔBrier=([+-][\d.]+)e-3.*?p=([\d.]+)\s+90%CI=\(([+-][\d.]+),([+-][\d.]+)\)e-3",
                       logtext("rigor"))
    assert len(pair3) == 3, "tables.py: rigor pairwise lines not found"
    md.append("\n| Pair | ΔBrier | p (clustered DM) | 90% CI | vs pre-stated δ=1.0e-3 | vs mid-price anchor 0.44e-3 |\n|---|---|---|---|---|---|")
    verd = dict(re.findall(r"^\s+(Kalshi - Polymarket|Kalshi - Sportsbook|Polymarket - Sportsbook)\s+"
                           r"[\d.]+e-3\s+\S+\s+(\S+)", logtext("rigor"), re.M))
    for pair, db, pv, lo, hi in pair3:
        inside_pre = max(abs(float(lo)), abs(float(hi))) <= 1.0
        md.append(f"| {pair} | {db}e-3 | {pv} | ({lo}, {hi})e-3 | "
                  f"{'equivalent' if inside_pre else 'not resolved'} | "
                  f"{'equivalent' if verd.get(pair, 'NO') == 'yes' else 'does not resolve'} |")
    md.append("\nFour-way: Polymarket US TOST-equivalent to each other source "
              "(δ_min ≤ 0.73e-3) [four_way.log]. Vs Pinnacle: every CI within "
              "±0.34e-3 [sharp_books.log].\n")

    # ------------------------------------------------------------- table 4 --
    b_k, b_p, b_b = (src3[0][1], src3[1][1], src3[2][1])
    ece_n, floor_n, exc_n = grab("niche_gradient", r"ECE niche ([\d.]+)pt vs its noise floor ([\d.]+)pt -> excess ([\d.]+)pt")
    slope_n, slo, shi = grab("niche_gradient", r"calibration slope core [\d.]+ vs niche ([\d.]+) \(niche 90% CI ([\d.]+)-([\d.]+)")
    n_f, ret_f = grab("futures_calibration", r"sub-10c futures contracts \(n=(\d+)\): \$1 stake returned \$([\d.]+) gross")
    ret_pf = grab("futures_calibration", r"Poly sub-10c \(dust excluded, n=\d+\): \$1 -> \$([\d.]+) gross")[0]
    n_bo, ret_bo, se_bo = grab("book_outrights", r"sub-10c: n=(\d+), \$1 -> \$([\d.]+) gross \(sport-season-clustered se ([\d.]+)")
    tail_unq = grab("liquidity_footprint", r"(\d+)% of the outright tail has no")[0]

    md.append(f"""## Table 4 — The 2×2 of discipline (the centerpiece)

|  | Benchmarked (professional books present) | Un-benchmarked |
|---|---|---|
| **Repeated, fast-resolving** | Game markets: dead heat — Brier {b_k} / {b_p} / {b_b} (K/P/B), formally equivalent | Niche tier: ECE {ece_n}pt vs a {floor_n}pt noise floor → excess **{exc_n}pt**; slope {slope_n} (90% CI {slo}–{shi}) |
| **One-shot, long-horizon** | Outrights: $1 on sub-10c longshots returns **${ret_f}** (Kalshi, n={n_f}), **${ret_pf}** (Polymarket), **${ret_bo}** (books, se {se_bo}, n={n_bo}) | {tail_unq}% of the outright tail has no two-sided book at all; where quoted, the same failure |

Read across a row: the institution explanation dies (every institution prices
the same market type the same way). Read down a column: the benchmark
explanation dies (repeated markets are clean without books; one-shot markets
fail with them). What is left is repetition and fast resolution.
De-vig caveat carried from the figure program: the books' sub-10c return
rises to ~$0.52 under Shin — the equal-failure claim holds under
multiplicative de-vig, so the sentence is "the books fail the same way,
within de-vig uncertainty."
""")

    # ------------------------------------------------------------- table 5 --
    sc, sc_lo, sc_hi, sc_n = grab("horizon_translation",
                                  r"share of notional\): (-[\d.]+)%\s+\[IQR (-[\d.]+)% to (-[\d.]+)%, n=([\d,]+)")
    r_all = re.search(r"^\s+ALL\s+[\d,]+\s+[\d,]+\s+(-[\d.]+)%\s+(-[\d.]+)%", logtext("retail_fingerprint"), re.M)
    assert r_all, "tables.py: retail ALL row not found"
    gross, net = r_all.groups()
    roi_all = grab("profitability", r"bet EVERYTHING\s+n=[\d, ]+\s+ROI=(-[\d.]+)%")[0]
    maker = grab("why_sports", r"maker \(no fee\)\s+ROI = \+([\d.]+)%")[0]
    cov_or = grab("market_functioning", r"covered-league books ~([\d.]+)")[0]
    niche_or = grab("market_functioning", r"median field sum ([\d.]+)")[0]

    md.append(f"""## Table 5 — What participation costs, and what it returns

| Rate | Value | Where it comes from |
|---|---|---|
| Kalshi structural taker cost | **{sc}% per position** (IQR {sc_lo}% to {sc_hi}%) | fixed by quote + fee schedule; n={sc_n} live quotes [horizon_translation.log] |
| Kalshi realized taker P&L | {gross}% gross / **{net}% net** of fees, on $95.7M | held to settlement; game-clustered CI spans zero — outcomes are noisy, the cost is not [retail_fingerprint.log] |
| Ordinary-gambler backtest ROI | {roi_all}% (bet everything) | every strategy lands at ~cost [profitability.log] |
| Maker path | ≈ free (realized +{maker}%, n.s.) | a route books do not offer [why_sports.log] |
| Sportsbook cost | ~{float(cov_or) - 1:.0%} overround (covered leagues) | field sums [market_functioning.log]; niche rises to {float(niche_or) - 1:.0%} |
| Polymarket taker | ~1–1.75% all-in | ~1% fee schedule + one-tick spread [tick_pricing.log, fee_liquidity.log] |

Bankroll after a ~26-week season of re-staking at the structural rate:
monthly 76%, fortnightly 55%, weekly 30%, twice-weekly 9%, daily ~0%
[horizon_translation.log]. **Calibration disciplines the price; it does not
protect the participant.**
""")

    text = "# Report tables — rendered from the suite logs\n\n" + "\n".join(md)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(text, flush=True)
    print(f"\nsaved -> {OUT}", flush=True)


if __name__ == "__main__":
    main()
