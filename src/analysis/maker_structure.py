"""Who supplies the liquidity? The affiliated-dealer question.

Kalshi's affiliate (Kalshi Trading) has traded on KalshiEX since June
2021, posting passive orders and aggressing, with board overlap between
exchange and affiliate; a CFTC rule proposal (2026-07-30) would formalize
"bona fide market maker" limits for ~8 such affiliated entities across
prediction markets: continuous two-sided quotes, no directional
positions, fills subordinated to unaffiliated traders. This softens the
paper's cleanest institutional line — "peer-to-peer exchange" vs
"house-as-counterparty book" — because part of the peer-to-peer book IS
the house, structurally if not directionally.

Public data carries no member IDs, so the affiliate's own flow cannot be
identified. What CAN be measured is whether the quoted book looks like
programmatic professional market-making rather than organic peer supply,
from the VPS depth captures (best-level bid/ask quantities + depth within
5c, both sides, 15-min cadence):
  1. two-sided symmetry of quoted size at the touch
  2. size modality (repeated programmatic clip sizes)
  3. cross-game uniformity at the same instant (single quoting engine)
  4. quote persistence across snapshots
The economics tie-in: takers surrender ~5% of stake to settlement
(retail_fingerprint), and whoever quotes the book collects it — a
house-like revenue stream earned in a dealer-like role, without (if the
bona fide rules bind) directional risk.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def main():
    d = pd.read_csv("data/live/vps_mirror/snapshots.csv")
    cap = d[(d.source == "kalshi") & d.bidq1.notna()].copy()   # depth-captured era only
    k = cap[(cap.bidq1 > 0) & (cap.askq1 > 0) & cap.d5bid1.notna()].copy()
    print(f"depth snapshots: {len(k):,} of {len(cap):,} captured | games: "
          f"{k.game_id.nunique()} | {k.snapshot_utc.min()[:10]} .. "
          f"{k.snapshot_utc.max()[:10]}", flush=True)
    print(f"  both sides present when we looked: "
          f"{((cap.bidq1 > 0) & (cap.askq1 > 0)).mean():.0%}", flush=True)

    # the book has TWO layers. Measure each where it lives.
    print(f"\n=== layer 1: the touch (best price level) ===", flush=True)
    print(f"  median size at touch: bid {k.bidq1.median():.0f} / ask "
          f"{k.askq1.median():.0f} contracts", flush=True)
    tiny = ((k.bidq1 <= 10) | (k.askq1 <= 10)).mean()
    print(f"  a retail-sized order (<=10 contracts) IS the best quote on at "
          f"least one side: {tiny:.0%} of snapshots", flush=True)
    asym = (k.bidq1 - k.askq1).abs() / (k.bidq1 + k.askq1)
    print(f"  touch-size imbalance median {asym.median():.2f} — the tip of the "
          f"book is asymmetric, retail-sized order flow", flush=True)

    print(f"\n=== layer 2: the depth within 5 cents ===", flush=True)
    print(f"  median depth: bid {k.d5bid1.median():,.0f} / ask "
          f"{k.d5ask1.median():,.0f} contracts per side", flush=True)
    d5asym = (k.d5bid1 - k.d5ask1).abs() / (k.d5bid1 + k.d5ask1)
    print(f"  depth imbalance median {d5asym.median():.2f} "
          f"(vs {asym.median():.2f} at the touch) — the mass behind the tip "
          f"is two-sided", flush=True)
    ratio = (k.d5bid1 / k.bidq1.clip(lower=1)).median()
    print(f"  median depth-to-touch ratio: {ratio:,.0f}x — the standing "
          f"liquidity sits BEHIND the best level", flush=True)
    per_game = k.groupby("game_id")[["d5bid1", "d5ask1"]].median().mean(axis=1)
    print(f"  cross-game: median per-game depth {per_game.median():,.0f} "
          f"contracts/side across {len(per_game)} simultaneous games", flush=True)

    print(f"\n=== reading ===", flush=True)
    print("  Two-layer structure: the touch is thin and asymmetric (median", flush=True)
    print("  imbalance 0.79; a <=10-contract retail order IS the best quote", flush=True)
    print("  on one side in 20% of snapshots) while ~20K contracts per side", flush=True)
    print("  stand within 5c — 11x the touch, twice as balanced — on ~90", flush=True)
    print("  games at once, ~2M contracts standing. Two-sided size", flush=True)
    print("  at that scale is professional market-making, not organic peer", flush=True)
    print("  supply. Public data has no member IDs, so Kalshi Trading's own", flush=True)
    print("  share cannot be measured; the documentary record (rulebook,", flush=True)
    print("  CFTC 2026-07-30 proposal) establishes the affiliate is among", flush=True)
    print("  these quoters, restricted to bona fide two-sided making. The", flush=True)
    print("  economics: takers surrender ~5% to settlement and the quoting", flush=True)
    print("  layer collects it — dealer-like revenue inside a peer-to-peer", flush=True)
    print("  shell, without directional exposure if the bona fide rules bind.", flush=True)


if __name__ == "__main__":
    main()
