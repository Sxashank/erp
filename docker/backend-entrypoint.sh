#!/usr/bin/env sh
set -eu

wait_for_tcp_url() {
  url="$1"
  label="$2"

  python - "$url" "$label" <<'PY'
import socket
import sys
import time
from urllib.parse import urlparse

url = sys.argv[1]
label = sys.argv[2]
parsed = urlparse(url)
host = parsed.hostname
port = parsed.port

if not host:
    raise SystemExit(f"{label}: missing host in URL")

if port is None:
    if parsed.scheme.startswith("postgresql"):
        port = 5432
    elif parsed.scheme.startswith("redis"):
        port = 6379
    else:
        raise SystemExit(f"{label}: missing port in URL")

deadline = time.time() + 90
last_error = None
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=3):
            print(f"{label} is reachable at {host}:{port}")
            raise SystemExit(0)
    except OSError as exc:
        last_error = exc
        time.sleep(2)

raise SystemExit(f"Timed out waiting for {label} at {host}:{port}: {last_error}")
PY
}

if [ -n "${DATABASE_URL:-}" ]; then
  wait_for_tcp_url "$DATABASE_URL" "database"
fi

if [ -n "${REDIS_URL:-}" ]; then
  wait_for_tcp_url "$REDIS_URL" "redis"
fi

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
  echo "Running Alembic migrations..."
  alembic upgrade head
fi

if [ "${RUN_SEED_DATA:-false}" = "true" ]; then
  echo "Running idempotent master seed data..."
  python scripts/seed_data.py
fi

exec "$@"
