#!/bin/bash
# SMFC ERP - Development Startup Script
# Assumes PostgreSQL and Redis are already running (external Docker containers)

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT=5176
PIDS=()

cleanup() {
    echo ""
    echo "Shutting down services..."
    for pid in "${PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done
    wait 2>/dev/null
    echo "All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# ── 1. Check external services ──
echo "==> Checking PostgreSQL..."
pg_isready -h localhost -p 5432 > /dev/null 2>&1 || { echo "ERROR: PostgreSQL is not running on port 5432"; exit 1; }
echo "    PostgreSQL is ready."

echo "==> Checking Redis..."
redis-cli -h localhost -p 6379 ping > /dev/null 2>&1 || { echo "ERROR: Redis is not running on port 6379"; exit 1; }
echo "    Redis is ready."

# ── 2. Setup Python virtual environment ──
if [ ! -d "$BACKEND_DIR/.venv" ]; then
    echo "==> Creating Python virtual environment..."
    python3 -m venv "$BACKEND_DIR/.venv"
fi

echo "==> Installing Python dependencies..."
source "$BACKEND_DIR/.venv/bin/activate"
pip install -q -r "$BACKEND_DIR/requirements.txt"
pip install -q apscheduler python-dateutil pycryptodome

# ── 3. Create .env if missing ──
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "==> Creating backend .env from .env.example..."
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

# ── 4. Install frontend dependencies ──
if [ ! -d "$PROJECT_DIR/node_modules" ]; then
    echo "==> Installing frontend dependencies..."
    cd "$PROJECT_DIR" && pnpm install
fi

# ── 5. Start backend ──
echo "==> Starting backend on port $BACKEND_PORT..."
cd "$BACKEND_DIR"
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload &
PIDS+=($!)

# ── 6. Start frontend ──
echo "==> Starting frontend on port $FRONTEND_PORT..."
cd "$PROJECT_DIR"
pnpm dev &
PIDS+=($!)

echo ""
echo "============================================"
echo "  SMFC ERP is running!"
echo "  Frontend : http://localhost:$FRONTEND_PORT"
echo "  Backend  : http://localhost:$BACKEND_PORT"
echo "  API Docs : http://localhost:$BACKEND_PORT/docs"
echo "============================================"
echo "  Press Ctrl+C to stop all services"
echo ""

wait
