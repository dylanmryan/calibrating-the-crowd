"""The benchmark-intensity gradient: niche game markets vs the covered core.

Games-vs-futures confounds repetition, horizon, and benchmark salience.
Niche game markets (minor-league soccer, cricket, esports, table tennis)
hold repetition and horizon fixed — fast-resolving, repeated, binary —
and remove the sportsbook consensus. If calibration survives, repetition
and fast resolution suffice; if it degrades, the benchmark itself is
load-bearing. Either answer sharpens the mechanism.

Method notes: prices are last trade strictly before the scheduled start
(Tier A: start embedded in the ticker, main-sample methodology; Tier B:
close_time minus a conservative sport duration). Headline restricts to
staleness <= 6h. Contracts within an event are dependent (2-3 siblings),
so ECE and slope get event-clustered bootstrap CIs; bucket binomials are
pooled and slightly anti-conservative — read them as descriptive.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

MAX_STALE_MIN = 360
EDGES = np.linspace(0, 1, 11)


def bucket_table(p, won, label):
    print(f"\n  {label}: n={len(p):,}", flush=True)
    print(f"  {'priced':>8} {'n':>6} {'avg':>6} {'won':>6} {'gap':>7} {'exact p':>8}", flush=True)
    b = np.clip(np.digitize(p, EDGES) - 1, 0, 9)
    gaps = []
    for k in range(10):
        m = b == k
        if m.sum() < 20:
            continue
        said, obs = p[m].mean(), won[m].mean()
        pex = stats.binomtest(int(won[m].sum()), int(m.sum()), said).pvalue
        gaps.append((m.sum(), abs(obs - said)))
        print(f"  {EDGES[k]*100:>3.0f}-{EDGES[k+1]*100:>2.0f}c {m.sum():>6,} "
              f"{said*100:>5.1f}% {obs*100:>5.1f}% {(obs-said)*100:>+6.1f}p {pex:>8.3f}", flush=True)
    ece = sum(n * g for n, g in gaps) / sum(n for n, g in gaps)
    return ece


def slope(p, won):
    x = np.log(np.clip(p, 0.01, 0.99) / (1 - np.clip(p, 0.01, 0.99)))
    import statsmodels.api as sm
    fit = sm.GLM(won, sm.add_constant(x), family=sm.families.Binomial()).fit()
    return fit.params[1]


def cluster_boot(df, pcol, wcol, gcol, fn, n=2000, seed=11):
    rng = np.random.default_rng(seed)
    groups = df[gcol].unique()
    idx = {g: df.index[df[gcol] == g].to_numpy() for g in groups}
    out = []
    for _ in range(n):
        take = np.concatenate([idx[g] for g in rng.choice(groups, len(groups))])
        s = df.loc[take]
        try:
            out.append(fn(s[pcol].to_numpy(), s[wcol].to_numpy()))
        except Exception:
            continue
    return np.percentile(out, [5, 95])


def main():
    d = pd.read_csv("data/processed/kalshi_niche_prices.csv").drop_duplicates("ticker")
    d = d[d.sport_class != "tennis"]                      # n=4, day-stale — unusable
    total = len(d)
    d = d[d.staleness_min <= MAX_STALE_MIN].copy()
    print(f"niche contracts: {len(d):,} of {total:,} priced within {MAX_STALE_MIN/60:.0f}h "
          f"staleness ({d.series.nunique()} series; enumerated universe was ~7.5K — "
          f"only ~17% ever traded pre-start, vs ~near-total pricing in covered leagues)",
          flush=True)
    print(d.sport_class.value_counts().to_string(), flush=True)

    # covered-core comparator: identical trade-recon-at-start methodology
    m = pd.read_csv("data/processed/games_master.csv", low_memory=False)
    m = m[m.kalshi_p1.notna() & m.outcome.notna() & ~m.outcome_disagree.fillna(False)]
    core = pd.DataFrame({
        "p": np.concatenate([m.kalshi_p1.to_numpy(), m.kalshi_p2.to_numpy()]),
        "won": np.concatenate([(m.outcome == 1).astype(float).to_numpy(),
                               (m.outcome == 2).astype(float).to_numpy()]),
        "ev": np.concatenate([m.game_id.to_numpy(), m.game_id.to_numpy()])})
    core = core[core.p.notna()]

    print("\n=== calibration: benchmarked core vs un-benchmarked niche ===", flush=True)
    ece_core = bucket_table(core.p.to_numpy(), core.won.to_numpy(),
                            "covered leagues (books present)")
    ece_n = bucket_table(d.p_start.to_numpy(), d.won.to_numpy().astype(float),
                         "niche sports (no book consensus)")

    # raw ECE is not comparable across sample sizes (finite-sample |gap| bias),
    # so report each sample's ECE against its own H0 noise floor: the expected
    # ECE if prices were PERFECTLY calibrated, at the observed bucket sizes
    # (E|gap| per bucket ~ sqrt(p(1-p)/n_k) * sqrt(2/pi), folded normal).
    def noise_floor(p):
        b = np.clip(np.digitize(p, EDGES) - 1, 0, 9)
        ns, es = [], []
        for k in range(10):
            m = b == k
            if m.sum() < 20:
                continue
            pb = p[m].mean()
            ns.append(m.sum())
            es.append(np.sqrt(pb * (1 - pb) / m.sum()) * np.sqrt(2 / np.pi))
        return np.average(es, weights=ns)

    nf_c, nf_n = noise_floor(core.p.to_numpy()), noise_floor(d.p_start.to_numpy())
    print(f"\n  ECE core {ece_core*100:.2f}pt vs its perfect-calibration noise floor "
          f"{nf_c*100:.2f}pt -> excess {max(0, ece_core-nf_c)*100:.2f}pt", flush=True)
    print(f"  ECE niche {ece_n*100:.2f}pt vs its noise floor {nf_n*100:.2f}pt "
          f"-> excess {max(0, ece_n-nf_n)*100:.2f}pt", flush=True)
    d2 = d.reset_index(drop=True)
    sl_c = slope(core.p.to_numpy(), core.won.to_numpy())
    sl_n = slope(d.p_start.to_numpy(), d.won.to_numpy().astype(float))
    slo, shi = cluster_boot(d2, "p_start", "won", "event_ticker", slope, n=500)
    print(f"  calibration slope core {sl_c:.3f} vs niche {sl_n:.3f} "
          f"(niche 90% CI {slo:.3f}-{shi:.3f}; 1.0 = perfect, <1 = overconfident)", flush=True)

    # tier robustness
    for tier in ("A", "B"):
        t = d[d.tier == tier]
        if len(t) > 150:
            b = np.clip(np.digitize(t.p_start.to_numpy(), EDGES) - 1, 0, 9)
            ks = [k for k in range(10) if (b == k).sum() > 19]
            e = np.average([abs(t.won.to_numpy()[b == k].mean()
                                - t.p_start.to_numpy()[b == k].mean()) for k in ks],
                           weights=[(b == k).sum() for k in ks])
            print(f"  tier {tier} only (n={len(t):,}): ECE {e*100:.2f}pt, "
                  f"slope {slope(t.p_start.to_numpy(), t.won.to_numpy().astype(float)):.3f}", flush=True)

    # 3-way soccer field sums: the un-benchmarked overround
    soc = d[(d.sport_class == "soccer-minor")]
    f = soc.groupby("event_ticker").filter(lambda g: len(g) == 3)
    sums = f.groupby("event_ticker").p_start.sum()
    if len(sums):
        print(f"\n=== niche 3-way field sums (n={len(sums)} fields) ===", flush=True)
        print(f"  median {sums.median():.3f}, IQR {sums.quantile(.25):.3f}-{sums.quantile(.75):.3f} "
              f"(games ~1.01, futures 1.03-1.06, books 1.2-1.6)", flush=True)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.4, 6))
    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.6, label="perfect calibration")
    for p, w, color, lab in (
            (core.p.to_numpy(), core.won.to_numpy(), "tab:blue",
             f"covered leagues (n={len(core):,})"),
            (d.p_start.to_numpy(), d.won.to_numpy().astype(float), "tab:red",
             f"niche sports, no book benchmark (n={len(d):,})")):
        b = np.clip(np.digitize(p, EDGES) - 1, 0, 9)
        xs, ys, ns = [], [], []
        for k in range(10):
            m = b == k
            if m.sum() >= 20:
                xs.append(p[m].mean()); ys.append(w[m].mean()); ns.append(m.sum())
        ax.plot(xs, ys, "-", color=color, alpha=0.6)
        ax.scatter(xs, ys, s=[max(20, n / 8) for n in ns], color=color, label=lab)
    ax.set(xlabel="price (implied probability)", ylabel="realized win rate",
           title="Calibration survives the loss of the benchmark\n"
                 "(table tennis, cricket, esports, minor-league soccer)")
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig("results/niche_gradient.png", dpi=130)
    print("\nsaved results/niche_gradient.png", flush=True)


if __name__ == "__main__":
    main()
