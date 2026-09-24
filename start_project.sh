#!/bin/bash
# ==============================================================================
# MULTILINGUAL AI DOCUMENT ASSISTANT WITH BIG DATA ANALYTICS
# ONE-CLICK PROJECT LAUNCHER (macOS)
# ==============================================================================

set -e

# Change directory to the project root directory where this script is located
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Terminal Colors
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
echo "================================================================================"
echo "   MULTILINGUAL AI DOCUMENT ASSISTANT WITH BIG DATA ANALYTICS                   "
echo "   One-Click Launcher & Service Manager                                         "
echo "================================================================================"
echo -e "${NC}"
echo -e "Project Root: ${BOLD}${PROJECT_ROOT}${NC}"

# 1. Detect Python 3.11
echo -e "\n${BOLD}[1/6] Checking Python Environment...${NC}"
PYTHON_BIN=""
if [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
    echo -e "  ${GREEN}✓${NC} Existing virtual environment detected: $("$PYTHON_BIN" --version)"
elif command -v /opt/homebrew/opt/python@3.11/bin/python3.11 &>/dev/null; then
    PYTHON_BIN="/opt/homebrew/opt/python@3.11/bin/python3.11"
    echo -e "  ${GREEN}✓${NC} Found Homebrew Python 3.11: $PYTHON_BIN"
elif command -v python3.11 &>/dev/null; then
    PYTHON_BIN="$(command -v python3.11)"
    echo -e "  ${GREEN}✓${NC} Found system python3.11: $PYTHON_BIN"
elif command -v python3 &>/dev/null; then
    PYTHON_BIN="$(command -v python3)"
    echo -e "  ${YELLOW}!${NC} Using default python3: $("$PYTHON_BIN" --version)"
else
    echo -e "  ${RED}✗ Error: Python 3 is not installed or not found on PATH.${NC}"
    exit 1
fi

# 2. Setup / Verify Virtual Environment
echo -e "\n${BOLD}[2/6] Verifying Virtual Environment (.venv)...${NC}"
if [ ! -d "$PROJECT_ROOT/.venv" ] || [ ! -f "$PROJECT_ROOT/.venv/bin/pip" ]; then
    echo -e "  ${YELLOW}!${NC} Creating fresh .venv using $PYTHON_BIN..."
    "$PYTHON_BIN" -m venv "$PROJECT_ROOT/.venv"
    echo -e "  ${GREEN}✓${NC} .venv created successfully."
fi

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
VENV_PIP="$PROJECT_ROOT/.venv/bin/pip"

# 3. Check / Install Dependencies & Build Frontend
echo -e "\n${BOLD}[3/6] Checking Project Dependencies & Frontend Build...${NC}"
if ! "$VENV_PYTHON" -c "import fastapi, uvicorn, pydantic, chromadb, pyspark, pyarrow" &>/dev/null; then
    echo -e "  ${YELLOW}!${NC} Installing missing dependencies into .venv (this may take a moment)..."
    "$VENV_PIP" install -r "$PROJECT_ROOT/requirements.txt"
    echo -e "  ${GREEN}✓${NC} Dependencies installed."
else
    echo -e "  ${GREEN}✓${NC} All core backend and analytics dependencies verified."
fi

if [ ! -d "$PROJECT_ROOT/frontend/dist" ] && command -v npm &>/dev/null; then
    echo -e "  ${YELLOW}!${NC} Building frontend application shell (Vite)..."
    npm --prefix "$PROJECT_ROOT/frontend" run build
    echo -e "  ${GREEN}✓${NC} Frontend build complete."
elif [ -d "$PROJECT_ROOT/frontend/dist" ]; then
    echo -e "  ${GREEN}✓${NC} Frontend build verified and current."
fi

# 4. Check Environment Variables (.env)
echo -e "\n${BOLD}[4/6] Verifying Configuration (.env)...${NC}"
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo -e "  ${GREEN}✓${NC} Created .env from .env.example with safe local defaults."
    else
        echo -e "  ${YELLOW}!${NC} Warning: .env not found. Running with default configurations."
    fi
else
    echo -e "  ${GREEN}✓${NC} Configuration .env found."
fi

# 5. Check Port Availability & Clean Stale Processes
echo -e "\n${BOLD}[5/6] Checking Port 8000...${NC}"
PORT_PIDS=$(lsof -ti :8000 2>/dev/null || true)
if [ -n "$PORT_PIDS" ]; then
    echo -e "  ${YELLOW}!${NC} Port 8000 is currently occupied by PID(s): $PORT_PIDS"
    echo -e "  ${YELLOW}!${NC} Terminating stale process(es) to allow clean startup..."
    for p in $PORT_PIDS; do
        kill -15 "$p" 2>/dev/null || true
    done
    sleep 1
    STILL_ALIVE=$(lsof -ti :8000 2>/dev/null || true)
    if [ -n "$STILL_ALIVE" ]; then
        for p in $STILL_ALIVE; do
            kill -9 "$p" 2>/dev/null || true
        done
        sleep 0.5
    fi
    echo -e "  ${GREEN}✓${NC} Port 8000 cleared."
else
    echo -e "  ${GREEN}✓${NC} Port 8000 is free."
fi

# Configure PySpark environment
if [ -d "/opt/homebrew/opt/openjdk@17" ]; then
    export JAVA_HOME="/opt/homebrew/opt/openjdk@17"
fi

# 6. Start Application Server
echo -e "\n${BOLD}[6/6] Starting Multilingual AI Document Assistant...${NC}"

# Cleanup handler on exit or Ctrl+C
cleanup() {
    trap - SIGINT SIGTERM EXIT
    echo -e "\n\n${YELLOW}================================================================================${NC}"
    echo -e "${YELLOW} Stopping Application Services cleanly...${NC}"
    if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
        kill -15 "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    echo -e "${GREEN} Application stopped cleanly. Goodbye!${NC}"
    echo -e "${YELLOW}================================================================================${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Launch Uvicorn in background
"$VENV_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

echo -e "  ${CYAN}Starting backend on PID $SERVER_PID...${NC}"
echo -e "  ${YELLOW}Waiting for application readiness (pre-warming embedding models & indexes)...${NC}"

# Poll readiness with realistic prewarming timeout (up to 60 seconds)
SERVER_READY=false
MAX_WAIT_SECONDS=60
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT_SECONDS ]; do
    # Check if backend process crashed prematurely
    if ! kill -0 "$SERVER_PID" 2>/dev/null; then
        echo -e "\n${RED}✗ Backend server process (PID $SERVER_PID) terminated unexpectedly.${NC}"
        SERVER_READY=false
        break
    fi

    if curl -s -f http://127.0.0.1:8000/health >/dev/null 2>&1; then
        SERVER_READY=true
        break
    fi

    sleep 1
    ELAPSED=$((ELAPSED + 1))
    if [ $((ELAPSED % 5)) -eq 0 ]; then
        echo -e "  ${YELLOW}Initializing services (${ELAPSED}s / ${MAX_WAIT_SECONDS}s)...${NC}"
    fi
done

if [ "$SERVER_READY" = true ]; then
    echo -e "\n${GREEN}${BOLD}================================================================================${NC}"
    echo -e "${GREEN}${BOLD} ✓ APPLICATION STARTED SUCCESSFULLY & HEALTH CHECK PASSED!                     ${NC}"
    echo -e "${GREEN}${BOLD}================================================================================${NC}"
    echo -e "  • User Application Shell (SPA)  : ${CYAN}${BOLD}http://localhost:8000/${NC}"
    echo -e "  • Interactive API Documentation : ${CYAN}http://localhost:8000/docs${NC}"
    echo -e "  • Health Check Status Endpoint  : ${CYAN}http://localhost:8000/health${NC}"
    echo -e "  • Analytics Health Endpoint     : ${CYAN}http://localhost:8000/api/v1/analytics/health${NC}"
    echo -e "  • Analytics Summary KPIs        : ${CYAN}http://localhost:8000/api/v1/analytics/summary${NC}"
    echo -e "  • Grounded QA Endpoint          : ${CYAN}POST http://localhost:8000/api/v1/qa/query${NC}"
    echo -e "\n${BOLD}Opening user-facing application in default web browser: http://localhost:8000/${NC}"
    
    # Automatically open default web browser to the root SPA
    if command -v open &>/dev/null; then
        open "http://localhost:8000/"
    fi

    echo -e "\n${BOLD}Server is running and streaming logs below. Press [Ctrl+C] to stop anytime.${NC}\n"
else
    echo -e "\n${RED}✗ Backend server failed to respond on http://127.0.0.1:8000/health within ${MAX_WAIT_SECONDS} seconds.${NC}"
    cleanup
    exit 1
fi

# Keep launcher alive and wait on server process
wait $SERVER_PID
