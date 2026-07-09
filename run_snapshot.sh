#!/bin/zsh
# Live snapshot runner — intended to be called by cron/launchd every ~15 min.
# Appends a multi-source price snapshot to data/live/snapshots.csv and logs output.
cd "/Users/dylanryan/Desktop/Summer Research" || exit 1
mkdir -p logs
/Users/dylanryan/Desktop/Summer\ Research/.venv/bin/python -m src.collect.live_snapshot \
  >> logs/snapshot.log 2>&1
