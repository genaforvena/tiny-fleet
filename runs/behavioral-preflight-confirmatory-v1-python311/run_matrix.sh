#!/usr/bin/env bash
set -euo pipefail

IMAGE='python@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1'
REPO='/home/mesh-home/tiny-fleet'
OUT="$REPO/runs/behavioral-preflight-confirmatory-v1-python311"
mkdir -p "$OUT/docker"

for snapshot in httpx-old httpx-new attrs-old attrs-new pytest-old pytest-new; do
  archive="$REPO/runs/drift-confirmatory-v1/snapshots/$snapshot.tar"
  printf 'Running %s\n' "$snapshot"
  docker run --rm --platform linux/amd64 \
    --volume "$REPO/runs/drift-confirmatory-v1/snapshots:/source:ro" \
    --volume "$OUT:/study" \
    --env SNAPSHOT="$snapshot" \
    --workdir /study \
    "$IMAGE" bash /study/run_one.sh >"$OUT/docker/$snapshot.log" 2>&1
done

python3 "$OUT/summarize.py"
