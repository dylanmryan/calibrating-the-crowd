#!/bin/bash
# Pull live data from VPS into a STAGING MIRROR only — never overwrite merged files.
cd "$(dirname "$0")"
rsync -az -e "ssh -i pem/ssh-key-2026-07-06.key" ubuntu@129.80.69.136:~/research/data/live/ data/live/vps_mirror/
echo "mirrored to data/live/vps_mirror/ ($(wc -l < data/live/vps_mirror/snapshots.csv) snapshot rows)"
