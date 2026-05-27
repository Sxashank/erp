#!/usr/bin/env bash
# SMFC ERP — one-shot dev runner.
#
# - Starts the project services in detached background sessions.
# - `start` is idempotent: if the managed stack is already healthy, it does not kill it.
# - `restart` is the explicit stop-then-start path.
# - Leaves unrelated processes alone (other vite/uvicorn on different ports).
# - Probes Postgres + Redis via Docker (host pg_isready / redis-cli not required).
# - Starts backend (uvicorn) + frontend (vite) detached, both logged to /tmp.
# - Prints PIDs and tail-commands so the operator can stop them later.
#
# Usage:
#   ./dev.sh          # start everything (idempotent)
#   ./dev.sh stop     # stop everything
#   ./dev.sh restart  # stop then start
#   ./dev.sh status   # show what's listening
#   ./dev.sh logs     # tail both logs

set -u

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-5176}"
BACKEND_LOG="/tmp/erp_backend.log"
FRONTEND_LOG="/tmp/erp_frontend.log"
BACKEND_PID_FILE="/tmp/erp_backend.pid"
FRONTEND_PID_FILE="/tmp/erp_frontend.pid"

PG_CONTAINER="${PG_CONTAINER:-docker-jaiho-postgresql-1}"
REDIS_CONTAINER="${REDIS_CONTAINER:-redis}"

c_green() { printf "\033[32m%s\033[0m\n" "$*"; }
c_red()   { printf "\033[31m%s\033[0m\n" "$*"; }
c_amber() { printf "\033[33m%s\033[0m\n" "$*"; }
info()    { printf "==> %s\n" "$*"; }

kill_port() {
    local port="$1"
    local pids
    pids=$(lsof -ti ":$port" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        for pid in $pids; do
            echo "    killing PID $pid on :$port"
            kill -9 "$pid" 2>/dev/null || true
        done
        sleep 1
    fi
}

pid_is_running() {
    local pid="$1"
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

read_pid_file() {
    local pidfile="$1"
    if [ -f "$pidfile" ]; then
        tr -d '[:space:]' < "$pidfile"
    fi
}

cleanup_pid_file() {
    local pidfile="$1"
    local pid
    pid=$(read_pid_file "$pidfile")
    if [ -n "$pid" ] && ! pid_is_running "$pid"; then
        rm -f "$pidfile"
    fi
}

kill_pid_file() {
    local pidfile="$1"
    local label="$2"
    local pid
    pid=$(read_pid_file "$pidfile")
    if [ -z "$pid" ]; then
        return 0
    fi

    if pid_is_running "$pid"; then
        echo "    stopping $label PID $pid"
        kill "$pid" 2>/dev/null || true
        sleep 1
        if pid_is_running "$pid"; then
            echo "    force killing $label PID $pid"
            kill -9 "$pid" 2>/dev/null || true
        fi
    fi
    rm -f "$pidfile"
}

port_in_use() {
    lsof -ti ":$1" >/dev/null 2>&1
}

http_status() {
    local url="$1"
    curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000"
}

spawn_detached() {
    local workdir="$1" log_file="$2" pid_file="$3"
    shift 3

    python3 - "$workdir" "$log_file" "$pid_file" "$@" <<'PY'
import os
import subprocess
import sys

workdir, log_file, pid_file, *cmd = sys.argv[1:]

with open(log_file, "ab", buffering=0) as log_handle, open(os.devnull, "rb") as devnull:
    proc = subprocess.Popen(
        cmd,
        cwd=workdir,
        stdin=devnull,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )

with open(pid_file, "w", encoding="utf-8") as handle:
    handle.write(str(proc.pid))

print(proc.pid)
PY
}

check_docker_service() {
    local container="$1" probe="$2" label="$3"
    if docker exec "$container" sh -c "$probe" >/dev/null 2>&1; then
        c_green "    $label is ready ($container)."
        return 0
    fi
    c_red "    $label is not reachable in container '$container'."
    return 1
}

cmd_stop() {
    info "Stopping project processes on :$BACKEND_PORT and :$FRONTEND_PORT..."
    kill_pid_file "$BACKEND_PID_FILE" "backend"
    kill_pid_file "$FRONTEND_PID_FILE" "frontend"
    kill_port "$BACKEND_PORT"
    kill_port "$FRONTEND_PORT"
    sleep 1
    if lsof -i ":$BACKEND_PORT" -i ":$FRONTEND_PORT" 2>/dev/null | grep -q LISTEN; then
        c_amber "    Some ports are still in use:"
        lsof -i ":$BACKEND_PORT" -i ":$FRONTEND_PORT" 2>/dev/null | grep LISTEN
    else
        c_green "    All project ports clear."
    fi
}

cmd_status() {
    info "Listeners on project ports:"
    lsof -i ":$BACKEND_PORT" -i ":$FRONTEND_PORT" 2>/dev/null | grep LISTEN || echo "    (none)"
    echo ""
    info "Health probes:"
    local b f
    b=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$BACKEND_PORT/docs" || echo "000")
    f=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$FRONTEND_PORT/" || echo "000")
    echo "    backend  http://localhost:$BACKEND_PORT/docs : HTTP $b"
    echo "    frontend http://localhost:$FRONTEND_PORT/    : HTTP $f"
}

cmd_logs() {
    echo "--- backend  ($BACKEND_LOG) ---"
    tail -n 5 "$BACKEND_LOG" 2>/dev/null || echo "  (no log)"
    echo ""
    echo "--- frontend ($FRONTEND_LOG) ---"
    tail -n 5 "$FRONTEND_LOG" 2>/dev/null || echo "  (no log)"
    echo ""
    echo "Tail live with:"
    echo "  tail -f $BACKEND_LOG"
    echo "  tail -f $FRONTEND_LOG"
}

cmd_start() {
    cleanup_pid_file "$BACKEND_PID_FILE"
    cleanup_pid_file "$FRONTEND_PID_FILE"

    local backend_http frontend_http
    backend_http=$(http_status "http://localhost:$BACKEND_PORT/docs")
    frontend_http=$(http_status "http://localhost:$FRONTEND_PORT/")
    if [ "$backend_http" = "200" ] && [ "$frontend_http" = "200" ]; then
        c_green "    Backend and frontend are already running."
        cmd_status
        return 0
    fi

    # ── 2. Docker infra check ─────────────────────────────────────────
    info "Checking Postgres + Redis (Docker)..."
    if ! check_docker_service "$PG_CONTAINER" "pg_isready -U postgres" "Postgres"; then
        c_red "Aborting — bring up postgres first:"
        echo "    docker start $PG_CONTAINER"
        exit 1
    fi
    if ! check_docker_service "$REDIS_CONTAINER" "redis-cli ping" "Redis"; then
        c_red "Aborting — bring up redis first:"
        echo "    docker start $REDIS_CONTAINER"
        exit 1
    fi

    # ── 3. Python venv ────────────────────────────────────────────────
    if [ ! -d "$BACKEND_DIR/.venv" ]; then
        info "Creating Python virtual environment..."
        python3 -m venv "$BACKEND_DIR/.venv"
    fi

    # ── 4. .env ───────────────────────────────────────────────────────
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        info "Seeding backend/.env from .env.example..."
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    fi

    # ── 5. Clear Python bytecode cache (avoid stale-module surprises) ─
    find "$BACKEND_DIR/app" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true

    # ── 6. Start backend (detached) ───────────────────────────────────
    if [ "$backend_http" != "200" ]; then
        if port_in_use "$BACKEND_PORT"; then
            c_red "    Backend port :$BACKEND_PORT is already in use by another process."
            c_red "    Run ./dev.sh restart if you want this script to replace it."
            exit 1
        fi
        info "Starting backend on :$BACKEND_PORT (logs → $BACKEND_LOG)..."
        : > "$BACKEND_LOG"
        spawn_detached \
            "$BACKEND_DIR" \
            "$BACKEND_LOG" \
            "$BACKEND_PID_FILE" \
            bash -lc "source .venv/bin/activate && exec uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --log-level info" \
            >/dev/null
    else
        c_green "    Backend already healthy on :$BACKEND_PORT."
    fi

    # ── 7. Start frontend (detached) ──────────────────────────────────
    if [ "$frontend_http" != "200" ]; then
        if port_in_use "$FRONTEND_PORT"; then
            c_red "    Frontend port :$FRONTEND_PORT is already in use by another process."
            c_red "    Run ./dev.sh restart if you want this script to replace it."
            exit 1
        fi
        info "Starting frontend on :$FRONTEND_PORT (logs → $FRONTEND_LOG)..."
        : > "$FRONTEND_LOG"
        spawn_detached \
            "$PROJECT_DIR" \
            "$FRONTEND_LOG" \
            "$FRONTEND_PID_FILE" \
            bash -lc "exec pnpm dev -- --host localhost --port $FRONTEND_PORT" \
            >/dev/null
    else
        c_green "    Frontend already healthy on :$FRONTEND_PORT."
    fi

    # ── 8. Wait + health check ────────────────────────────────────────
    info "Waiting for boot..."
    local attempt=0 b="000" f="000"
    while [ $attempt -lt 20 ]; do
        sleep 1
        b=$(http_status "http://localhost:$BACKEND_PORT/docs")
        f=$(http_status "http://localhost:$FRONTEND_PORT/")
        if [ "$b" = "200" ] && [ "$f" = "200" ]; then
            break
        fi
        attempt=$((attempt + 1))
    done

    echo ""
    c_green "============================================"
    if [ "$b" = "200" ]; then
        c_green "  Backend  : http://localhost:$BACKEND_PORT  (PID $(read_pid_file "$BACKEND_PID_FILE"))"
        c_green "  API docs : http://localhost:$BACKEND_PORT/docs"
    else
        c_red   "  Backend  : http://localhost:$BACKEND_PORT  → HTTP $b   (check $BACKEND_LOG)"
    fi
    if [ "$f" = "200" ]; then
        c_green "  Frontend : http://localhost:$FRONTEND_PORT  (PID $(read_pid_file "$FRONTEND_PID_FILE"))"
    else
        c_red   "  Frontend : http://localhost:$FRONTEND_PORT  → HTTP $f   (check $FRONTEND_LOG)"
    fi
    c_green "============================================"
    echo ""
    echo "  Stop with:   ./dev.sh stop"
    echo "  Restart:     ./dev.sh restart"
    echo "  Tail logs:   tail -f $BACKEND_LOG $FRONTEND_LOG"
}

case "${1:-start}" in
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    restart) cmd_stop; cmd_start ;;
    status)  cmd_status ;;
    logs)    cmd_logs ;;
    *)
        echo "usage: $0 {start|stop|restart|status|logs}"
        exit 2
        ;;
esac
