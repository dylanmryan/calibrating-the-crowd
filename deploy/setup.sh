#!/usr/bin/env bash
# One-shot setup for the live collector on a fresh Ubuntu cloud box.
# Run from the project root ON THE BOX:  bash deploy/setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "==> project root: $ROOT"

echo "==> installing system packages"
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip

echo "==> creating venv + installing the collector's dependencies"
python3 -m venv .venv
./.venv/bin/pip install --quiet --upgrade pip
# only what the LIVE collector needs (not the heavy analysis stack)
./.venv/bin/pip install --quiet pandas requests python-dotenv cryptography

echo "==> preflight checks"
[ -f .env ] || { echo "ERROR: .env is missing — scp it to the box first"; exit 1; }
KEY="$(grep -E '^KALSHI_PRIVATE_KEY_PATH' .env | cut -d= -f2 | tr -d ' ')"
[ -n "$KEY" ] && [ -f "$KEY" ] || { echo "ERROR: Kalshi key not found at '$KEY' — scp pem/ to the box"; exit 1; }
for f in data/processed/kalshi_settled_markets.csv data/processed/espn_games.csv; do
  [ -f "$f" ] || { echo "ERROR: $f missing — needed for team-alias matching; copy it over"; exit 1; }
done
echo "    secrets + alias data present."

echo "==> writing box runner + cron (every 15 min)"
cat > run_snapshot.sh <<EOF
#!/usr/bin/env bash
cd "$ROOT" || exit 1
mkdir -p logs
"$ROOT/.venv/bin/python" -m src.collect.live_snapshot >> logs/snapshot.log 2>&1
EOF
chmod +x run_snapshot.sh
( crontab -l 2>/dev/null | grep -v run_snapshot.sh; echo "*/15 * * * * $ROOT/run_snapshot.sh" ) | crontab -

echo "==> test snapshot (should print a table of games)"
./.venv/bin/python -m src.collect.live_snapshot | head -8 || true

echo
echo "==> DONE. cron is live:"; crontab -l | grep run_snapshot.sh
echo "    tail the log with:  tail -f $ROOT/logs/snapshot.log"
