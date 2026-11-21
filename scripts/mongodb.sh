#!/usr/bin/env bash
# Local MongoDB without Docker or sudo (spec/10-local-development.md).
# Installs the official MongoDB Community server into ~/.local/share/tsg-mongodb
# and runs it as a single-node replica set bound to 127.0.0.1.
#
# Usage: scripts/mongodb.sh install | start | stop | status
set -euo pipefail

MONGO_VERSION="${MONGO_VERSION:-8.0.12}"
MONGO_HOME="${MONGO_HOME:-$HOME/.local/share/tsg-mongodb}"
MONGO_BIN="$MONGO_HOME/mongodb-$MONGO_VERSION/bin/mongod"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$REPO_ROOT/.localdata/mongo"
LOG_FILE="$REPO_ROOT/.localdata/mongod.log"
PID_FILE="$REPO_ROOT/.localdata/mongod.pid"
PORT="${MONGO_PORT:-27017}"

install() {
  if [[ -x "$MONGO_BIN" ]]; then
    echo "MongoDB $MONGO_VERSION already installed at $MONGO_BIN"
    return
  fi
  local archive="mongodb-linux-x86_64-ubuntu2404-$MONGO_VERSION"
  mkdir -p "$MONGO_HOME"
  echo "Downloading MongoDB $MONGO_VERSION from fastdl.mongodb.org ..."
  curl -fsSL "https://fastdl.mongodb.org/linux/$archive.tgz" -o "$MONGO_HOME/$archive.tgz"
  tar -xzf "$MONGO_HOME/$archive.tgz" -C "$MONGO_HOME"
  mv "$MONGO_HOME/$archive" "$MONGO_HOME/mongodb-$MONGO_VERSION"
  rm "$MONGO_HOME/$archive.tgz"
  "$MONGO_BIN" --version | head -1
}

is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

start() {
  [[ -x "$MONGO_BIN" ]] || install
  if is_running; then
    echo "MongoDB already running (pid $(cat "$PID_FILE"))"
    return
  fi
  mkdir -p "$DATA_DIR"
  "$MONGO_BIN" --dbpath "$DATA_DIR" --port "$PORT" --bind_ip 127.0.0.1 \
    --replSet rs0 --wiredTigerCacheSizeGB 0.25 \
    --logpath "$LOG_FILE" --logappend --pidfilepath "$PID_FILE" --fork >/dev/null
  # Initialise the single-node replica set on first start (needed for change streams).
  uv --directory "$REPO_ROOT/backend" run python -I - "$PORT" <<'PY'
import sys, time
from pymongo import MongoClient
from pymongo.errors import OperationFailure

port = int(sys.argv[1])
client = MongoClient(f"mongodb://127.0.0.1:{port}/?directConnection=true", serverSelectionTimeoutMS=10000)
try:
    client.admin.command("replSetInitiate", {"_id": "rs0", "members": [{"_id": 0, "host": f"127.0.0.1:{port}"}]})
except OperationFailure as exc:
    if exc.code != 23:  # AlreadyInitialized
        raise
for _ in range(30):
    if client.admin.command("hello").get("isWritablePrimary"):
        break
    time.sleep(0.5)
print(f"MongoDB ready on 127.0.0.1:{port} (replica set rs0)")
PY
}

stop() {
  if ! is_running; then
    rm -f "$PID_FILE"
    echo "MongoDB not running"
    return
  fi
  local pid
  pid="$(cat "$PID_FILE")"
  # SIGTERM triggers a clean shutdown (flushes data, releases the lock file).
  kill "$pid"
  for _ in $(seq 30); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.5
  done
  if kill -0 "$pid" 2>/dev/null; then
    echo "MongoDB did not stop in 15s; forcing" >&2
    kill -9 "$pid"
  fi
  rm -f "$PID_FILE"
  echo "MongoDB stopped"
}

status() {
  if is_running; then echo "running (pid $(cat "$PID_FILE"))"; else echo "stopped"; fi
}

case "${1:-}" in
  install) install ;;
  start) start ;;
  stop) stop ;;
  status) status ;;
  *) echo "usage: $0 install|start|stop|status" >&2; exit 2 ;;
esac
