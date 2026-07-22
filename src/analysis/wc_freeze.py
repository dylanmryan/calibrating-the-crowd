"""World Cup wrap-up: backfill regulation-90 outcomes and freeze the 3-way case study.

The live WC snapshotter priced Kalshi's "Reg Time" 3-way markets and the books'
regulation-time h2h, so the matching outcome is the score at 90 minutes. ESPN's
status distinguishes FT (decided in regulation) from AET / FT-Pens (level at 90
by construction -> regulation outcome is a draw); no period scores needed.

Outputs data/processed/wc_3way_snapshots.csv (snapshots + outcomes, frozen) and
prints the per-game closing-price table plus 3-way Brier / log score per source.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import requests

SNAP = "data/live/vps_mirror/wc_snapshots.csv"
OUT = "data/processed/wc_3way_snapshots.csv"
_session = requests.Session()

# ESPN soccer status -> did the match go past 90'?
REG_DECIDED = {"STATUS_FULL_TIME"}
PAST_90 = {"STATUS_FINAL_AET", "STATUS_FINAL_PEN"}


def regulation_outcomes(games: pd.DataFrame) -> pd.DataFrame:
    """One row per game: final score, status, and the regulation-90 outcome."""
    dates = sorted({pd.to_datetime(s, utc=True).strftime("%Y%m%d") for s in games.start_utc})
    events = {}
    for d in dates:
        r = _session.get(
            "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard",
            params={"dates": d, "limit": 400}, timeout=30)
        r.raise_for_status()
        for e in r.json().get("events", []):
            events[e["id"]] = e
    rows = []
    for g in games.itertuples(index=False):
        e = events.get(str(g.game_id))
        if e is None:
            print(f"  WARNING: no ESPN event for {g.game_id} {g.home} v {g.away}")
            continue
        comp = e["competitions"][0]
        side = {c["homeAway"]: c for c in comp["competitors"]}
        status = e["status"]["type"]["name"]
        hs, as_ = int(side["home"]["score"]), int(side["away"]["score"])
        if status in PAST_90:
            reg = "draw"
        elif status in REG_DECIDED:
            reg = "draw" if hs == as_ else ("home" if hs > as_ else "away")
        else:
            print(f"  WARNING: unexpected status {status} for {g.game_id}; skipping")
            continue
        rows.append({"game_id": g.game_id, "home_score": hs, "away_score": as_,
                     "status": status, "reg_outcome": reg})
    return pd.DataFrame(rows)


def main():
    snap = pd.read_csv(SNAP)
    games = snap[["game_id", "start_utc", "home", "away"]].drop_duplicates("game_id")
    oc = regulation_outcomes(games)
    df = snap.merge(oc, on="game_id", how="left")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"frozen {len(df)} snapshot rows, {oc.shape[0]} games with outcomes -> {OUT}")
    print(f"regulation outcomes: {oc.reg_outcome.value_counts().to_dict()}\n")

    # closing price = last pre-kickoff snapshot per (game, source)
    pre = df[df.minutes_to_start > 0].sort_values("snapshot_utc")
    close = pre.groupby(["game_id", "source"]).tail(1).copy()
    y = pd.get_dummies(close.reg_outcome)[["home", "draw", "away"]].to_numpy(float)
    p = close[["p_home", "p_draw", "p_away"]].to_numpy(float)
    close["brier3"] = ((p - y) ** 2).sum(axis=1)
    close["logscore"] = np.log(np.clip((p * y).sum(axis=1), 1e-6, None))
    close["p_realized"] = (p * y).sum(axis=1)

    show = close.merge(games[["game_id", "home", "away"]], on="game_id")[
        ["home_x", "away_x", "source", "minutes_to_start", "p_home", "p_draw", "p_away",
         "reg_outcome", "p_realized", "brier3"]].rename(columns={"home_x": "home", "away_x": "away"})
    print(show.sort_values(["home", "source"]).to_string(index=False))

    agg = close.groupby("source").agg(
        games=("brier3", "size"), brier3=("brier3", "mean"),
        logscore=("logscore", "mean"), p_realized=("p_realized", "mean"),
        mins_before=("minutes_to_start", "mean"))
    print("\nclosing-snapshot scores (3-way Brier, lower = better):")
    print(agg.round(4).to_string())


if __name__ == "__main__":
    main()
