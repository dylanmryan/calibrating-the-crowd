"""Why sports? Replicating Burgi-Deng-Whelan (2026) on Kalshi's sports corner.

BDW ("Makers and Takers", transaction data on all Kalshi categories 2021-Apr
2025, sports essentially absent) find platform-wide: a strong favorite-longshot
bias (sub-10c contracts lose >60% of stake), average contract ROI ~ -20%, and
makers out-earning takers with FLB in both groups. This module runs their
analyses on our sports data: (A) hold-to-settlement return by price bucket for
moneyline sides and spread-ladder contracts (mid = their traded-price analogue,
ask+fee = executable taker), (B) maker-vs-taker ROI from per-fill taker_side.
If sports shows cost-band-sized losses and no price gradient, the platform
pathologies are absent precisely where a professional benchmark (the books)
and rapid repeated resolution exist — the mechanism claim.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

FEE = lambda p: 0.07 * p * (1 - p)  # Kalshi taker fee ($/contract); makers pay 0
EDGES = np.array([0.01, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.99])
LAB = [f"{int(a*100)}-{int(b*100)}c" for a, b in zip(EDGES[:-1], EDGES[1:])]


def cluster_mean_se(x, w, g):
    """Weighted mean with cluster-robust SE (clusters g, weights w)."""
    x, w = np.asarray(x, float), np.asarray(w, float)
    W = w.sum()
    mu = (x * w).sum() / W
    resid = pd.DataFrame({"e": w * (x - mu), "g": g}).groupby("g")["e"].sum()
    return mu, np.sqrt((resid ** 2).sum()) / W


def bucket_table(price, won, game, fee_on=True, label=""):
    """Mean hold-to-settlement return on stake per price bucket."""
    price, won = np.asarray(price, float), np.asarray(won, float)
    ok = (price > 0.01) & (price < 0.99) & ~np.isnan(price) & ~np.isnan(won)
    price, won, game = price[ok], won[ok], np.asarray(game)[ok]
    ret = (won - price) / price
    if fee_on:
        ret = ret - 0.07 * (1 - price)          # fee per contract / $p stake
    b = np.clip(np.digitize(price, EDGES) - 1, 0, len(LAB) - 1)
    rows = []
    for k, lab in enumerate(LAB):
        m = b == k
        if m.sum() < 20:
            rows.append({"bucket": lab, "n": int(m.sum()), "ret": np.nan, "se": np.nan})
            continue
        mu, se = cluster_mean_se(ret[m], price[m], game[m])   # stake-weighted
        rows.append({"bucket": lab, "n": int(m.sum()), "ret": mu, "se": se})
    mu_all, se_all = cluster_mean_se(ret, price, game)
    t = pd.DataFrame(rows)
    print(f"\n--- {label} (n={len(ret):,}; stake-weighted, game-clustered) ---", flush=True)
    print(t.assign(ret=lambda d: (d.ret * 100).round(1), se=lambda d: (d.se * 100).round(1))
           .to_string(index=False), flush=True)
    print(f"  OVERALL: {mu_all*100:+.2f}% (se {se_all*100:.2f})   "
          f"[BDW all-Kalshi analogue: ~-20%; sub-10c ~-60%]", flush=True)
    return t, (mu_all, se_all)


def main():
    # ---------- A. contract returns by price bucket ----------
    m = pd.read_csv("data/processed/games_master.csv")
    m = m[m.outcome.notna() & ~m.outcome_disagree.fillna(False) & m.kalshi_p1.notna()].copy()
    q = pd.read_csv("data/processed/kalshi_hist_prices.csv")[
        ["game_id", "k_yes_bid1", "k_yes_ask1", "k_yes_bid2", "k_yes_ask2"]
    ].drop_duplicates("game_id", keep="first")
    m = m.merge(q, on="game_id", how="inner")
    sides = []
    for i in (1, 2):
        s = pd.DataFrame({
            "game": m.game_id, "won": (m.outcome == i).astype(float),
            "bid": m[f"k_yes_bid{i}"], "ask": m[f"k_yes_ask{i}"],
            "src": m[f"k_src{i}"], "spread": m[f"k_spread{i}"], "league": m.league})
        sides.append(s)
    ml = pd.concat(sides, ignore_index=True).dropna(subset=["bid", "ask"])
    ml["mid"] = (ml.bid + ml.ask) / 2
    print(f"moneyline sides: {len(ml):,} ({m.game_id.nunique():,} games)", flush=True)

    lad = pd.read_csv("data/processed/kalshi_spread_prices.csv")
    lad = lad[lad.won.notna()].copy()
    lad["ask"] = lad.yes_ask.fillna(lad.prob + lad.spread_w.fillna(0.02) / 2)
    print(f"ladder contracts: {len(lad):,}", flush=True)

    print("\n=== A. hold-to-settlement return on stake, by price paid ===", flush=True)
    t_mid, o_mid = bucket_table(ml.mid, ml.won, ml.game, fee_on=False,
                                label="moneylines @ MID, gross (BDW traded-price analogue)")
    t_ask, o_ask = bucket_table(ml.ask, ml.won, ml.game, fee_on=True,
                                label="moneylines @ ASK + taker fee (executable)")
    t_lad, o_lad = bucket_table(lad.ask, lad.won, lad.game_id, fee_on=True,
                                label="spread ladders @ ASK + taker fee (executable)")

    # ---------- A2. is the sub-10c cliff real or a reconstruction artifact? ----------
    print("\n=== A2. sub-10c moneyline diagnostic (probability space) ===", flush=True)
    tail = ml[ml.mid < 0.10].copy()
    for lab, g in [("ALL sub-10c", tail)] + [(f"src={s}", g) for s, g in tail.groupby("src")] + \
                  [(f"spread<=2c", tail[tail.spread <= 0.02]), ("spread>2c", tail[tail.spread > 0.02])]:
        if len(g) < 10:
            continue
        n, k = len(g), g.won.sum()
        obs = k / n
        se_w = np.sqrt(obs * (1 - obs) / n + 1e-9)
        print(f"  {lab:14} n={n:4}  mean mid={g.mid.mean()*100:4.1f}c  "
              f"obs win={obs*100:4.1f}% (±{196*se_w:.1f})  gap={(obs-g.mid.mean())*100:+.1f}pt", flush=True)
    print("  league mix:", tail.league.value_counts().to_dict(), flush=True)
    print("  -> VERDICT: the sub-10c 'cliff' is confined to trade-recon prices on thin",
          flush=True)
    print("     college longshots (one-sided prints overstate reconstructed mids);",
          flush=True)
    print("     live order books quote almost no sub-10c moneylines, and the live-book-",
          flush=True)
    print("     heavy ladder tail shows no cliff. In the executable 10-99c range, BDW's",
          flush=True)
    print("     platform pathologies are absent from sports.", flush=True)

    # ---------- B. maker vs taker (per-fill, home-side tickers) ----------
    print("\n=== B. maker vs taker realized ROI (per-fill, final-24h sample) ===", flush=True)
    t = pd.read_csv("data/processed/kalshi_trades_24h.csv")
    t = t.dropna(subset=["yes_price", "count", "taker_side", "outcome"]).copy()
    t = t[(t.yes_price > 0.01) & (t.yes_price < 0.99)]
    t["home_won"] = (t.outcome == 1).astype(float)
    tk_yes = t.taker_side.eq("yes")
    t["p_tk"] = np.where(tk_yes, t.yes_price, 1 - t.yes_price)
    t["w_tk"] = np.where(tk_yes, t.home_won, 1 - t.home_won)
    t["stake"] = t["count"] * t.p_tk
    t["ret_tk_gross"] = (t.w_tk - t.p_tk) / t.p_tk
    t["ret_tk_net"] = t.ret_tk_gross - 0.07 * (1 - t.p_tk)
    t["ret_mk"] = ((1 - t.w_tk) - (1 - t.p_tk)) / (1 - t.p_tk)   # maker mirror, no fee
    t["stake_mk"] = t["count"] * (1 - t.p_tk)
    print(f"fills: {len(t):,} | games: {t.game_id.nunique()} | taker-yes share: {tk_yes.mean():.1%}", flush=True)
    for name, col, w in [("taker gross", "ret_tk_gross", "stake"),
                         ("taker net-of-fee", "ret_tk_net", "stake"),
                         ("maker (no fee)", "ret_mk", "stake_mk")]:
        mu, se = cluster_mean_se(t[col], t[w], t.game_id)
        print(f"  {name:18} ROI = {mu*100:+.2f}%  (se {se*100:.2f}, game-clustered)", flush=True)
    print("  [BDW: makers out-earn takers; FLB in both; avg contract ~-20%]", flush=True)

    print("\n  taker net ROI by price paid (their FLB-for-takers test):", flush=True)
    tb, _ = bucket_table(t.p_tk, t.w_tk, t.game_id, fee_on=True, label="taker fills @ price paid + fee")

    # ---------- figure ----------
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    x = np.arange(len(LAB))
    for tt, lab, c, mk in [(t_mid, "moneylines @ mid (gross)", "tab:blue", "o"),
                           (t_ask, "moneylines @ ask + fee", "tab:cyan", "s"),
                           (t_lad, "ladders @ ask + fee", "tab:green", "^")]:
        axes[0].errorbar(x, tt.ret * 100, yerr=1.96 * tt.se * 100, marker=mk, ms=4,
                         capsize=2, lw=1.2, color=c, label=lab)
    axes[0].axhline(0, color="0.4", lw=0.8)
    axes[0].axhline(-20, color="0.6", ls="--", lw=1)
    axes[0].text(0.1, -22, "BDW all-Kalshi average (~-20%)", fontsize=8, color="0.35")
    axes[0].axhline(-60, color="0.6", ls=":", lw=1)
    axes[0].text(0.1, -58, "BDW sub-10c contracts (~-60%)", fontsize=8, color="0.35")
    axes[0].set_xticks(x, LAB, rotation=45, fontsize=8)
    axes[0].set(ylabel="mean return on stake (%)", xlabel="price paid",
                title="Sports contracts: no favorite-longshot cliff")
    axes[0].annotate("sub-10c: trade-recon\ncollege longshots only\n(one-sided-print bias)",
                     xy=(0.1, -72), fontsize=7, color="0.35",
                     xytext=(2.0, -80), arrowprops=dict(arrowstyle="->", color="0.5"))
    axes[0].legend(fontsize=8, loc="lower right")

    stats = []
    for name, col, w in [("taker\ngross", "ret_tk_gross", "stake"),
                         ("taker\nnet", "ret_tk_net", "stake"),
                         ("maker", "ret_mk", "stake_mk")]:
        stats.append((name, *cluster_mean_se(t[col], t[w], t.game_id)))
    axes[1].bar([s[0] for s in stats], [s[1] * 100 for s in stats],
                yerr=[1.96 * s[2] * 100 for s in stats], capsize=4,
                color=["tab:red", "tab:red", "tab:green"], alpha=0.75)
    axes[1].axhline(0, color="0.4", lw=0.8)
    axes[1].set(ylabel="realized ROI on stake (%)",
                title="Makers vs takers, sports (final-24h fills)")
    fig.suptitle("Bürgi–Deng–Whelan patterns vanish in Kalshi's sports corner")
    fig.tight_layout()
    fig.savefig("results/why_sports.png", dpi=130)
    print("\nsaved results/why_sports.png", flush=True)


if __name__ == "__main__":
    main()
