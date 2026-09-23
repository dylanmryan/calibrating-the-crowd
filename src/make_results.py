"""Regenerate every report number and figure from the clean master in one run.

    .venv/bin/python -m src.make_results          # full suite (~minutes)
    .venv/bin/python -m src.make_results three_way rigor   # subset

Runs each canonical analysis module as a subprocess (one failure doesn't kill
the suite), tees stdout to results/logs/<module>.log, and writes
results/MANIFEST.md with per-module status, timing, and the figure inventory.
The report must cite these logs/figures only — no hand-carried numbers.

Excluded on purpose: collectors (network/API cost), wc_freeze (case study
frozen 2026-07-21; re-running re-fetches ESPN). validate_recon RUNS here — its
network path is `validate_recon.collect()`, invoked by hand and never by the
suite; the module's main() is the offline report over the already-fetched
comparison file.
"""
from __future__ import annotations

import subprocess
import sys
import time
from datetime import date
from pathlib import Path

# dependency-safe order; all read local processed data only
MODULES = [
    "data_audit", "deep_audit",   # the gates: a FAIL here fails the whole suite
    "validate_recon",             # offline: trade-recon vs archived books (80% of the Kalshi leg)
    "plain_calibration", "three_way", "rigor", "league_tost", "four_way", "decomposition", "nuance", "corp_diagram", "murphy",
    "coherence", "margin_dist", "book_pit", "totals", "ladder_vs_books", "ladder_cost", "multi_outcome",
    "mlb_autopsy", "mlb_extras", "extras_conditioning", "profitability", "behavioral", "why_sports", "time_stability", "futures_calibration", "retail_fingerprint", "niche_gradient", "book_outrights", "sharp_books", "us_books", "maker_structure", "liquidity_footprint", "mm_involvement", "market_functioning",
    "model_benchmark", "encompassing",
    "late_flow", "informed", "horizon", "horizon_equivalence", "horizon_cross",
    "close_efficiency", "layer2", "one_price",
    "fee_experiment", "fee_liquidity", "tick_pricing", "referee", "power", "robustness_cuts", "horizon_translation", "lead_lag", "book_moves", "book_panel", "book_freshness", "minute_lead_lag", "five_min", "immediacy",
    "oos_verification",           # registered holdout scorecard (docs/registered-claims.md)
    # Log-CONSUMERS last. multiple_testing re-derives every claim's p-value from
    # the logs above, so running it mid-suite (where it sat until 2026-09-16)
    # silently read the PREVIOUS run's logs for the ~20 modules scheduled after
    # it — lead_lag, five_min, book_moves, book_panel, ladder_cost and the rest.
    # It converged across repeated runs and so never failed, but "the inventory
    # reads its own logs" is only true if those logs are this run's.
    "multiple_testing",
    "tables",                     # report Tables 1-5 rendered from the logs above
    # candidate figures for the two instrument legs. In the suite so they cannot
    # drift from the logs while the report decides whether to adopt them; they
    # write C1-C4 and touch nothing the frozen F-set owns.
    "report_visuals_instrument",
    "hierarchical_calibration",   # PyMC; ~90s, the suite's slowest module
]


def main():
    todo = sys.argv[1:] or MODULES
    unknown = set(todo) - set(MODULES)
    if unknown:
        sys.exit(f"unknown module(s): {', '.join(sorted(unknown))}")
    logdir = Path("results/logs")
    logdir.mkdir(parents=True, exist_ok=True)
    rows, t00 = [], time.time()
    for m in todo:
        t0 = time.time()
        log = logdir / f"{m}.log"
        with open(log, "w") as f:
            rc = subprocess.run([sys.executable, "-m", f"src.analysis.{m}"],
                                stdout=f, stderr=subprocess.STDOUT).returncode
        dt = time.time() - t0
        rows.append((m, rc, dt))
        print(f"{'OK ' if rc == 0 else 'FAIL'} {m:20} {dt:6.1f}s -> {log}", flush=True)
        if rc != 0 and m in ("data_audit", "deep_audit"):
            print(f"GATE FAILED ({m}) — halting the suite; nothing regenerated past this point", flush=True)
            break

    figs = sorted(p.name for p in Path("results").glob("*.png"))
    fails = [m for m, rc, _ in rows if rc]
    if todo != MODULES:  # subset runs must not clobber the full-suite manifest
        print(f"\nsubset run ({len(fails)} failures); manifest untouched", flush=True)
        sys.exit(1 if fails else 0)
    with open("results/MANIFEST.md", "w") as f:
        f.write(f"# Results manifest — regenerated {date.today()}\n\n"
                f"Suite: {len(rows)} modules, {time.time()-t00:.0f}s total, "
                f"{len(fails)} failed{': ' + ', '.join(fails) if fails else ''}.\n\n"
                f"| module | status | seconds | log |\n|---|---|---|---|\n")
        for m, rc, dt in rows:
            f.write(f"| {m} | {'ok' if rc == 0 else f'FAIL({rc})'} | {dt:.1f} | logs/{m}.log |\n")
        f.write("\n## Figures\n\n" + "".join(f"- {g}\n" for g in figs))
    print(f"\nmanifest -> results/MANIFEST.md ({len(fails)} failures)", flush=True)
    sys.exit(1 if fails else 0)


if __name__ == 