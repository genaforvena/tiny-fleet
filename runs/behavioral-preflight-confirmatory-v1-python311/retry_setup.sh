#!/usr/bin/env bash
set -euo pipefail

IMAGE='python@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1'
REPO='/home/mesh-home/tiny-fleet'
OUT="$REPO/runs/behavioral-preflight-confirmatory-v1-python311"
docker run --rm --platform linux/amd64 \
  --volume "$REPO/runs/drift-confirmatory-v1/snapshots:/source:ro" \
  --volume "$OUT:/study" \
  --workdir /study \
  "$IMAGE" bash /study/retry_setup_inner.sh >"$OUT/docker/retry-setup.log" 2>&1
