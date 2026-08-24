#!/usr/bin/env bash
# ==============================================================================
# Research Assistant with Memory - Stop Script (Linux / macOS)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/.pids"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=====================================================${NC}"
echo -e "${YELLOW}   Stopping Research Assistant Services...           ${NC}"
echo -e "${BLUE}=====================================================${NC}"

stop_process() {
  local name=$1
  local pid_file="$PID_DIR/$2"

  if [ -f "$pid_file" ]; then
    local pid=$(cat "$pid_file")
    if kill -0 "$pid" 2>/dev/null; then
      echo -e "Stopping $name (PID: $pid)..."
      kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
      echo -e "${GREEN}✓ $name stopped.${NC}"
    else
      echo -e "${YELLOW}- $name was not running (stale PID $pid).${NC}"
    fi
    rm -f "$pid_file"
  else
    echo -e "${YELLOW}- No PID file found for $name.${NC}"
  fi
}

# Stop by recorded PIDs
stop_process "FastAPI Backend" "backend.pid"
stop_process "React Frontend" "frontend.pid"
stop_process "Streamlit Frontend" "streamlit.pid"

# Fallback: clean up any lingering processes on ports 8000, 5173, 8501
echo -e "\nChecking for lingering processes on standard ports..."
for port in 8000 5173 8501; do
  if command -v lsof >/dev/null 2>&1; then
    PID=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$PID" ]; then
      echo "Killing remaining process on port $port (PID: $PID)..."
      kill -9 $PID 2>/dev/null || true
    fi
  elif command -v fuser >/dev/null 2>&1; then
    fuser -k ${port}/tcp >/dev/null 2>&1 || true
  fi
done

echo -e "\n${GREEN}All services have been safely stopped.${NC}"
echo -e "${BLUE}=====================================================${NC}"
