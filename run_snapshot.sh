#!/bin/zsh
# Live snapshot runner — intended to be called by cron/launchd every ~15 min.
# Appends a multi-source price snapshot to data/live/snapshots.csv and logs output.
# Resolves its own location so the checkout can live anywhere.
ROOT="${0:A:h}"
cd "$ROOT" || exit 1
mkdir -p logs
"$ROOT/.venv/bin/python" -m src.collect.live_snapshot \
  >> logs/snapshot.log 2>&1
