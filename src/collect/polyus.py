"""Polymarket US (the CFTC-regulated DCM): catalog + closing prices from the
public execution tape.

Two data paths, chosen after probing the API surface:
  catalog — authenticated GET /v1/markets (ED25519-signed headers; the .env
            key/secret pair). One row per sports moneyline: slug, teams, the
            LONG side (the instrument the tape prices), gameStartTime.
  tape    — the public Time & Sales daily CSVs (Time, Symbol, Price, Size;
            manifest at polymarketexchange.com/files/time-and-sales/manifest.json,
            complete from platform launch 2025-10-29). Files are streamed one
            at a time and discarded; we keep per game only the last trade at
            or before the ESPN official start (closing price, trade-recon
            style), plus final-24h fills/volume and staleness. No auth.

Side convention: the tape prices ONE instrument per market — the marketSide
with long=true (observed = the first team code in the slug). The analysis
layer validates this against ESPN outcomes before use, exactly as the Kalshi
ticker-order rule was validated.

Usage: python -m src.collect.polyus catalog | tape
"""
from __future__ import annotations

import io
import os
import sys
import time
import base64

import pandas as pd
import requests
from dotenv import load_dotenv
from cryptography.hazmat.primitives.asymmetric import ed25519

load_dotenv(".env", override=True)
API = "https://api.polymarket.us"
TAPE = "https://www.polymarketexchange.com/files/time-and-sales"
CAT_OUT = "data/processed/polyus_catalog.csv"
PRICE_OUT = "data/processed/polyus_prices.csv"
DONE = "data/processed/polyus_tape_done.txt"
_session = requests.Session()

_KEY = (os.getenv("POLYMARKET_API_KEY") or "").strip().strip("'\"")
_SEC = (os.getenv("POLYMARKET_API_SECRET") or "").strip().strip("'\"")


def _hdr(method, path):
    pk = ed25519.Ed25519PrivateKey.from_private_bytes(base64.b64decode(_SEC)[:32])
    ts = str(int(time.time() * 1000))
    sig = base64.b64encode(pk.sign(f"{ts}{method}{path}".encode())).decode()
    return {"X-PM-Access-Key": _KEY, "X-PM-Timestamp": ts, "X-PM-Signature": sig}


def catalog(out=CAT_OUT):
    rows, offset = [], 0
    while True:
        r = _session.get(f"{API}/v1/markets", headers=_hdr("GET", "/v1/markets"),
                         params={"limit": 200, "offset": offset}, timeout=30)
        ms = r.json().get("markets", []) if r.status_code == 200 else []
        if not ms:
            break
        for m in ms:
            slug = m.get("slug") or ""
            if not slug.startswith("aec-"):        # moneylines only (asc-=spread, tec-=futures)
                continue
            long_side = next((s for s in m.get("marketSides", []) if s.get("long")), {})
            team = (long_side.get("team") or {})
            rows.append({
                "market_id": m.get("id"), "slug": slug,
                "league": slug.split("-")[1].upper(),
                "question": m.get("question"),
                "game_start": m.get("gameStartTime") or m.get("endDate"),
                "long_desc": long_side.get("description"),
                "long_team": team.get("name"),
                "closed": m.get("closed"),
                "outcomes": str(m.get("outcomes"))})
        offset += 200
        if offset % 2000 == 0:
            print(f"  {offset} markets scanned, {len(rows)} moneylines", flush=True)
        time.sleep(0.1)
    df = pd.DataFrame(rows)
    df.to_csv(out, index=False)
    print(f"catalog: {len(df):,} moneyline markets -> {out}", flush=True)
    print(df.league.value_counts().to_string(), flush=True)


def tape(out=PRICE_OUT):
    cat = pd.read_csv(CAT_OUT)
    cat["start"] = pd.to_datetime(cat.game_start, utc=True, format="ISO8601")
    by_symbol = cat.set_index("slug")["start"].to_dict()
    man = _session.get(f"{TAPE}/manifest.json", timeout=30).json()
    files = sorted(f["filename"] for f in (man if isinstance(man, list) else man.get("files", [])))
    done = set(open(DONE).read().split()) if os.path.exists(DONE) else set()
    todo = [f for f in files if f not in done]
    print(f"tape: {len(todo)}/{len(files)} daily files to process", flush=True)
    for i, fn in enumerate(todo, 1):
        try:
            r = _session.get(f"{TAPE}/{fn}", timeout=180)
            r.raise_for_status()
            t = pd.read_csv(io.BytesIO(r.content))
        except Exception as e:
            print(f"  {fn}: FAILED {type(e).__name__} — will retry next run", flush=True)
            continue
        t.columns = [c.strip().lower().replace(" ", "_") for c in t.columns]
        tcol = next(c for c in t.columns if "time" in c)
        pcol = next(c for c in t.columns if "price" in c)
        qcol = next(c for c in t.columns if "quantity" in c or "size" in c)
        scol = next(c for c in t.columns if "symbol" in c)
        t = t[t[scol].isin(by_symbol)]
        rows = []
        if len(t):
            t["ts"] = pd.to_datetime(t[tcol], utc=True, format="mixed")
            for sym, g in t.groupby(scol):
                start = by_symbol[sym]
                pre = g[g.ts <= start]
                w24 = pre[pre.ts >= start - pd.Timedelta("24h")]
                if pre.empty:
                    continue
                last = pre.sort_values("ts").iloc[-1]
                rows.append({
                    "slug": sym, "tape_date": fn[:8],
                    "close_price": float(last[pcol]),
                    "close_ts": last.ts.isoformat(),
                    "stale_min": round((start - last.ts).total_seconds() / 60, 1),
                    "fills_24h": len(w24),
                    "vol_24h": float(w24[qcol].sum())})
        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(out, mode="a", header=not os.path.exists(out), index=False)
        with open(DONE, "a") as f:
            f.write(fn + "\n")
        if i % 20 == 0 or i == len(todo):
            print(f"  {i}/{len(todo)} files ({fn}, {len(rows)} game closes)", flush=True)
    print(f"done -> {out}", flush=True)


if __name__ == "__main__":
    {"catalog": catalog, "tape": tape}[sys.argv[1] if len(sys.argv) > 1 else "catalog"]()
