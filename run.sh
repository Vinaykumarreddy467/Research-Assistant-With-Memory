#!/usr/bin/env bash
# ==============================================================================
# Research Assistant with Memory - Local Launch Script (Linux / macOS)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PID_DIR="$SCRIPT_DIR/.pids"
mkdir -p "$PID_DIR"

# Color helpers
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================${NC}"
echo -e "${BLUE}   Starting Research Assistant with Memory Services   ${NC}"
echo -e "${BLUE}=====================================================${NC}"

# Check for .env file
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    echo -e "${YELLOW}[!] No .env file found. Creating .env from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}[!] Please add your GEMINI_API_KEY or GROQ_API_KEY into .env if needed.${NC}"
  fi
fi

# 1. Backend (FastAPI) Setup and Launch
echo -e "\n${GREEN}[1/3] Starting FastAPI Backend (Port 8000)...${NC}"
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment for backend..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

# Run FastAPI backend in background and record PID
uvicorn main:app --host 0.0.0.0 --port 8000 --reload > "$SCRIPT_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > "$PID_DIR/backend.pid"
deactivate
echo -e "${GREEN}✓ Backend running at http://localhost:8000 (PID: $BACKEND_PID)${NC}"

# 2. Frontend (React + Vite) Setup and Launch
echo -e "\n${GREEN}[2/3] Starting React + Vite Frontend (Port 5173)...${NC}"
cd "$SCRIPT_DIR/frontend"

if [ ! -d "node_modules" ]; then
  echo "Installing Node dependencies for frontend..."
  npm install
fi

npm run dev > "$SCRIPT_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$PID_DIR/frontend.pid"
echo -e "${GREEN}✓ React UI running at http://localhost:5173 (PID: $FRONTEND_PID)${NC}"

# 3. Streamlit Frontend Setup and Launch
echo -e "\n${GREEN}[3/3] Starting Streamlit Frontend (Port 8501)...${NC}"
cd "$SCRIPT_DIR/streamlit"

if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment for Streamlit..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

streamlit run app.py --server.port 8501 --server.headless true > "$SCRIPT_DIR/streamlit.log" 2>&1 &
STREAMLIT_PID=$!
echo $STREAMLIT_PID > "$PID_DIR/streamlit.pid"
deactivate
echo -e "${GREEN}✓ Streamlit UI running at http://localhost:8501 (PID: $STREAMLIT_PID)${NC}"

cd "$SCRIPT_DIR"

echo -e "\n${BLUE}=====================================================${NC}"
echo -e "${GREEN}All services are up and running!${NC}"
echo -e "  - React Web UI:      ${BLUE}http://localhost:5173${NC}"
echo -e "  - Streamlit UI:      ${BLUE}http://localhost:8501${NC}"
echo -e "  - FastAPI API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e ""
echo -e "To view live logs:    tail -f backend.log frontend.log streamlit.log"
echo -e "To stop all services: ./stop.sh"
echo -e "${BLUE}=====================================================${NC}"
