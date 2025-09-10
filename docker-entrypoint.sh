#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Waiting for database availability..."
python - <<'PY'
import os, sys, time
from urllib.parse import urlparse
import psycopg2

url = os.environ.get('DATABASE_URL')
if not url:
    print('[entrypoint] DATABASE_URL not set; skipping DB wait')
    sys.exit(0)

for i in range(60):
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print('[entrypoint] Database is reachable')
        break
    except Exception as e:
        if i % 5 == 0:
            print(f"[entrypoint] Waiting for DB... ({e})")
        time.sleep(2)
else:
    print('[entrypoint] ERROR: database not reachable after timeout', file=sys.stderr)
    sys.exit(1)
PY

echo "[entrypoint] Running migrations (flask db upgrade)"
flask db upgrade

echo "[entrypoint] Starting: $*"
exec "$@"
