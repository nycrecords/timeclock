#!/usr/bin/env bash
set -euo pipefail

# Function to handle errors
error_exit() {
    echo "[entrypoint] ERROR: $1" >&2
    exit 1
}

echo "[entrypoint] Starting TimeClock application..."
echo "[entrypoint] Environment: FLASK_ENV=${FLASK_ENV:-production}"
echo "[entrypoint] Database URL configured: ${DATABASE_URL:+yes}"

# Check if DATABASE_URL is set
if [ -z "${DATABASE_URL:-}" ]; then
    error_exit "DATABASE_URL environment variable is not set"
fi

echo "[entrypoint] Waiting for database availability..."
python - <<'PY'
import os, sys, time
from urllib.parse import urlparse
import psycopg2

url = os.environ.get('DATABASE_URL')
if not url:
    print('[entrypoint] ERROR: DATABASE_URL not set', file=sys.stderr)
    sys.exit(1)

max_attempts = 30
for i in range(max_attempts):
    try:
        conn = psycopg2.connect(url)
        conn.close()
        print(f'[entrypoint] Database is reachable (attempt {i+1}/{max_attempts})')
        break
    except Exception as e:
        if i % 5 == 0:
            print(f"[entrypoint] Waiting for DB... attempt {i+1}/{max_attempts} ({str(e)[:100]})")
        if i == max_attempts - 1:
            print(f'[entrypoint] ERROR: database not reachable after {max_attempts} attempts', file=sys.stderr)
            sys.exit(1)
        time.sleep(2)
PY

# Check exit code from Python script
if [ $? -ne 0 ]; then
    error_exit "Failed to connect to database"
fi

echo "[entrypoint] Running migrations (flask db upgrade)"
if ! flask db upgrade; then
    error_exit "Database migration failed"
fi

# Verify the app can import without errors
echo "[entrypoint] Verifying application can start..."
python -c "from timeclock import app; print('[entrypoint] App imported successfully')" || error_exit "Failed to import application"

echo "[entrypoint] Starting: $*"
if [ $# -eq 0 ]; then
    echo "[entrypoint] WARNING: No command provided, using default"
    exec gunicorn -w 2 -b 0.0.0.0:5000 --timeout 120 --log-level info timeclock:app
else
    exec "$@"
fi
