#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; SCRIPT="$1"; shift || true
scp -q "$DIR/ss_api.py" "$SCRIPT" juan@2.29.41.159:/tmp/
ssh -o BatchMode=yes juan@2.29.41.159 "cd /home/juan/superset-stack && set -a && . ./.env && set +a && docker cp /tmp/ss_api.py superset-stack-superset-1:/tmp/ss_api.py && docker cp /tmp/$(basename "$SCRIPT") superset-stack-superset-1:/tmp/script.py && docker exec -e SUPERSET_ADMIN_USER -e SUPERSET_ADMIN_PASSWORD -w /tmp superset-stack-superset-1 python /tmp/script.py $*"
