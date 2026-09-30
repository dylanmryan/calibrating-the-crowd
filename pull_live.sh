#!/bin/bash
# Pull live data from VPS into a STAGING MIRROR only — never overwrite merged files.
# Host details come from .env (VPS_HOST, VPS_USER, VPS_KEY) so they are not
# committed to a public repository.
set -euo pipefail
cd "$(dirname "$0")"

[ -f .env ] && { set -a; . ./.env; set +a; }

: "${VPS_HOST:?set VPS_HOST in .env (collector box hostname or IP)}"
: "${VPS_USER:?set VPS_USER in .env (ssh login user on the collector box)}"
: "${VPS_KEY:?set VPS_KEY in .env (path to the ssh private key, e.g. pem/your-key.key)}"

rsync -az -e "ssh -i $VPS_KEY" "$VPS_USER@$VPS_HOST:~/research/data/live/" data/live/vps_mirror/
echo "mirrored to data/live/vps_mirror/ ($(wc -l < data/live/vps_mirror/snapshots.csv) snapshot rows)"
