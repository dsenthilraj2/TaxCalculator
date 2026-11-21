#!/usr/bin/env bash
# One command to run the whole local demo: MongoDB + API + UI.
#
#   scripts/demo.sh start     start everything (installs/seeds on first run)
#   scripts/demo.sh stop      stop everything, including MongoDB
#   scripts/demo.sh restart   stop, then start
#   scripts/demo.sh status    show what is running
#   scripts/demo.sh logs      follow the API and UI logs
#   scripts/demo.sh seed      (re)load demo products and sample calculations
#
# Each service runs in its own process group, so `stop` also ends child processes
# (uvicorn's reloader, Vite's esbuild). Logs: .localdata/logs/
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="$REPO_ROOT/.localdata/run"
LOG_DIR="$REPO_ROOT/.localdata/logs"
API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-5173}"
API_URL="http://127.0.0.1:$API_PORT"
WEB_URL="http://127.0.0.1:$WEB_PORT"

mkdir -p "$RUN_DIR" "$LOG_DIR"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok() { printf '\033[1;32m ✓\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m !\033[0m %s\n' "$*"; }

is_running() {
  local pid_file="$RUN_DIR/$1.pid"
  [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null
}

port_busy() {
  (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null
}

wait_for() {
  local name="$1" url="$2" seconds="${3:-60}"
  for _ in $(seq "$seconds"); do
    if curl -fsS -o /dev/null "$url" 2>/dev/null; then
      ok "$name ready at $url"
      return 0
    fi
    sleep 1
  done
  warn "$name did not become ready in ${seconds}s. See $LOG_DIR/$name.log"
  return 1
}

start_service() {
  local name="$1" port="$2"
  shift 2
  if is_running "$name"; then
    ok "$name already running (pid $(cat "$RUN_DIR/$name.pid"))"
    return
  fi
  if port_busy "$port"; then
    warn "Port $port is already in use by another process; not starting $name."
    return 1
  fi
  # setsid: new process group whose id is the leader's pid, so stop can end the whole group.
  setsid nohup "$@" >"$LOG_DIR/$name.log" 2>&1 < /dev/null &
  echo $! >"$RUN_DIR/$name.pid"
}

stop_service() {
  local name="$1"
  local pid_file="$RUN_DIR/$name.pid"
  if ! is_running "$name"; then
    rm -f "$pid_file"
    ok "$name not running"
    return
  fi
  local pid
  pid="$(cat "$pid_file")"
  kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
  for _ in $(seq 10); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 1
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -KILL -- "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
  fi
  rm -f "$pid_file"
  ok "$name stopped"
}

ensure_dependencies() {
  if [[ ! -d "$REPO_ROOT/backend/.venv" ]]; then
    say "Installing backend dependencies (first run)"
    uv --directory "$REPO_ROOT/backend" sync
  fi
  if [[ ! -d "$REPO_ROOT/web/portal/node_modules" ]]; then
    say "Installing UI dependencies (first run)"
    (cd "$REPO_ROOT/web/portal" && npm ci)
  fi
  if [[ ! -f "$REPO_ROOT/backend/.env.local" ]]; then
    cp "$REPO_ROOT/.env.example" "$REPO_ROOT/backend/.env.local"
  fi
}

seed() {
  say "Loading demo data"
  uv --directory "$REPO_ROOT/backend" run tsg-seed
  touch "$RUN_DIR/seeded"
}

start() {
  ensure_dependencies

  say "Starting MongoDB"
  "$REPO_ROOT/scripts/mongodb.sh" start

  if [[ ! -f "$RUN_DIR/seeded" ]]; then
    seed
  fi

  say "Starting API on port $API_PORT"
  start_service api "$API_PORT" env TSG_PORT="$API_PORT" \
    uv --directory "$REPO_ROOT/backend" run tsg-api
  wait_for api "$API_URL/health/ready"

  say "Starting UI on port $WEB_PORT"
  start_service web "$WEB_PORT" env TSG_API_URL="$API_URL" \
    npm --prefix "$REPO_ROOT/web/portal" run dev -- --port "$WEB_PORT" --strictPort
  wait_for web "$WEB_URL"

  echo
  ok "Demo is running"
  echo "    UI:        $WEB_URL"
  echo "    API docs:  $API_URL/docs"
  echo "    Logs:      $LOG_DIR"
  echo "    Stop:      scripts/demo.sh stop"
}

stop() {
  say "Stopping demo"
  stop_service web
  stop_service api
  "$REPO_ROOT/scripts/mongodb.sh" stop
}

status() {
  for name in api web; do
    if is_running "$name"; then
      ok "$name running (pid $(cat "$RUN_DIR/$name.pid"))"
    else
      warn "$name stopped"
    fi
  done
  printf ' • mongodb %s\n' "$("$REPO_ROOT/scripts/mongodb.sh" status)"
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status) status ;;
  logs) tail -n 50 -F "$LOG_DIR/api.log" "$LOG_DIR/web.log" ;;
  seed) "$REPO_ROOT/scripts/mongodb.sh" start; seed ;;
  *) echo "usage: $0 start|stop|restart|status|logs|seed" >&2; exit 2 ;;
esac
