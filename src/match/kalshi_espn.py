"""Match Kalshi games to ESPN games on league + date + team-code pair.

Each Kalshi event has two side markets whose ticker suffixes are the two team
tricodes (e.g. ...BOSPHI-BOS and ...-PHI) -> a clean unordered code pair, no
fuzzy name matching. ESPN gives team abbreviations. Codes don't always agree
across sources (e.g. NBA Spurs SAS vs SA), so we reconcile via a per-league alias
map, built up by inspecting the misses this script reports.
"""
from __future__ import annotations

import pandas as pd

# Kalshi-code -> ESPN-abbr reconciliations, per league. Seeded empty; grown from misses.
ALIASES: dict[str, dict[str, str]] = {
    "NBA": {}, "NFL": {}, "MLB": {}, "NHL": {}, "WNBA": {}, "CFB": {}, "CBB-M": {},
}


def kalshi_games(path="data/processed/kalshi_settled_markets.csv") -> pd.DataFrame:
    """Collapse per-side rows into one row per game with the unordered team-code pair."""
    df = pd.read_csv(path)
    df["code"] = df["ticker"].str.rsplit("-", n=1).str[-1]  # side tricode
    df["date"] = pd.to_datetime(df["date"]).dt.date
    rows = []
    for ev, g in df.groupby("event_ticker"):
        if g["code"].nunique() != 2:
            continue  # skip malformed events
        codes = tuple(sorted(g["code"].unique()))
        win = g.loc[g["won"] == 1, "code"]
        gdate, kstart = _ticker_parts(ev)
        rows.append({
            "event_ticker": ev,
            "league": g["league"].iloc[0],
            # authoritative game date from the ticker (close_time conflates series games)
            "date": gdate if gdate is not None else g["date"].iloc[0],
            "codes": codes,
            "winner_code": win.iloc[0] if len(win) else None,
            "k_start": kstart,  # approx UTC start (for doubleheader time disambiguation)
        })
    return pd.DataFrame(rows)


def _ticker_parts(ev: str):
    """Parse a Kalshi ticker into (ET game date, approx UTC datetime).

    e.g. KXMLBGAME-26MAY011420AZCHC -> date 2026-05-01, 14:20 ET +4h UTC. The ET date
    is the authoritative game date (close_time conflates consecutive series games).
    Time is present mainly on newer MLB tickers; noon ET is used as a proxy otherwise.
    """
    import re
    import datetime as _dt
    m = re.match(r"KX[A-Z0-9]+GAME-(\d{2}[A-Z]{3}\d{2})(\d{4})?", ev or "")
    if not m:
        return None, None
    date_s, time_s = m.groups()
    try:
        d = _dt.datetime.strptime(date_s.title(), "%y%b%d")
    except ValueError:
        return None, None
    game_date = d.date()
    hh, mm = (int(time_s[:2]) % 24, int(time_s[2:])) if time_s else (12, 0)  # noon proxy
    start_utc = pd.Timestamp(d.replace(hour=hh, minute=mm) + _dt.timedelta(hours=4), tz="UTC")
    return game_date, start_utc


def espn_games(path="data/processed/espn_games.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["start_utc"] = pd.to_datetime(df["start_utc"], utc=True, format="ISO8601")
    df["date"] = df["start_utc"].dt.date
    df["codes"] = df.apply(lambda r: tuple(sorted([str(r["home_abbr"]), str(r["away_abbr"])])), axis=1)
    return df


def _norm(codes: tuple, league: str) -> frozenset:
    amap = ALIASES.get(league, {})
    return frozenset(amap.get(c, c) for c in codes)


def learn_aliases(kal: pd.DataFrame, esp: pd.DataFrame, min_support: int = 2) -> None:
    """Infer Kalshi-code -> ESPN-abbr mappings from games that share date + one code.

    If a Kalshi pair {A,B} and an ESPN pair {A,X} fall on the same date, then B and
    X are the same team, so B->X is a candidate alias. We accept a mapping only when
    it's the consistent majority (>= min_support votes, no ties) for that code.
    """
    from collections import Counter, defaultdict

    esp_by_day: dict = {}
    for r in esp.itertuples(index=False):
        esp_by_day.setdefault((r.league, r.date), []).append(set(r.codes))

    votes: dict = defaultdict(Counter)  # (league, kalshi_code) -> Counter(espn_code)
    for g in kal.itertuples(index=False):
        kcodes = set(g.codes)
        for delta in (0, -1, 1):
            for ecodes in esp_by_day.get((g.league, g.date + pd.Timedelta(days=delta)), []):
                shared = kcodes & ecodes
                if len(shared) == 1:  # exactly one code agrees -> the leftovers are aliases
                    (kc,), (ec,) = kcodes - ecodes, ecodes - kcodes
                    if kc != ec:
                        votes[(g.league, kc)][ec] += 1

    for (league, kc), ctr in votes.items():
        (best, n), = ctr.most_common(1)
        others = [c for c in ctr.values() if c == n]
        if n >= min_support and len(others) == 1:  # clear majority, no tie
            ALIASES.setdefault(league, {})[kc] = best


def match(kal: pd.DataFrame, esp: pd.DataFrame) -> pd.DataFrame:
    # index ESPN by (league, canonical code-set) -> list of (date, row)
    idx: dict = {}
    for r in esp.itertuples(index=False):
        key = (r.league, _norm(r.codes, r.league))
        idx.setdefault(key, []).append(r)

    out = []
    for g in kal.itertuples(index=False):
        key = (g.league, _norm(g.codes, g.league))
        cand = [c for c in idx.get(key, []) if abs((c.date - g.date).days) <= 1]
        if len(cand) <= 1:
            hit = cand[0] if cand else None
        else:  # doubleheader: pick the ESPN game closest in start time to the ticker time
            ks = getattr(g, "k_start", None)
            hit = (min(cand, key=lambda c: abs((c.start_utc - ks).total_seconds()))
                   if ks is not None else cand[0])
        out.append({
            "event_ticker": g.event_ticker, "league": g.league, "date": g.date,
            "codes": g.codes, "matched": hit is not None,
            "espn_id": hit.espn_id if hit else None,
            "start_utc": hit.start_utc if hit else None,
            "espn_winner_abbr": (hit.home_abbr if hit.winner == "home" else hit.away_abbr) if hit else None,
        })
    return pd.DataFrame(out)


if __name__ == "__main__":
    kal, esp = kalshi_games(), espn_games()
    m0 = match(kal, esp)
    print(f"before aliases: {m0['matched'].mean():.1%}", flush=True)
    learn_aliases(kal, esp)
    print(f"learned aliases: " + ", ".join(f"{lg}:{len(a)}" for lg, a in ALIASES.items() if a), flush=True)
    m = match(kal, esp)
    rate = m.groupby("league")["matched"].agg(["mean", "sum", "size"])
    rate.columns = ["match_rate", "matched", "total"]
    print(rate.sort_values("match_rate").to_string(), flush=True)
    print(f"\nOVERALL: {m['matched'].mean():.1%}  ({m['matched'].sum():,}/{len(m):,})", flush=True)

    # show sample misses per league with their codes to grow the alias map
    print("\n--- sample unmatched (Kalshi codes) ---", flush=True)
    miss = m[~m.matched]
    for lg, g in miss.groupby("league"):
        ex = [c for c in g["codes"].head(6)]
        print(f"  {lg:6} misses={len(g):5} e.g. {ex}", flush=True)

    m.to_csv("data/processed/kalshi_espn_matches.csv", index=False)
    print(f"\nsaved matches -> data/processed/kalshi_espn_matches.csv", flush=True)
