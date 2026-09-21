#!/bin/bash
# ==============================================================================
# MULTILINGUAL AI DOCUMENT ASSISTANT WITH BIG DATA ANALYTICS
# STOP PROJECT SCRIPT (macOS)
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Terminal Colors
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "================================================================================"
echo "   STOPPING MULTILINGUAL AI DOCUMENT ASSISTANT                                  "
echo "================================================================================"
echo -e "${NC}"

STOPPED_ANY=false

# 1. Check Port 8000
PIDS=$(lsof -ti :8000 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo -e "Terminating process(es) on port 8000 (PIDs: $PIDS)..."
    for pid in $PIDS; do
        kill -15 "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
    done
    STOPPED_ANY=true
fi

# 2. Check for any leftover uvicorn processes matching app.main:app
UVICORN_PIDS=$(pgrep -f "uvicorn.*app\.main:app" 2>/dev/null || true)
if [ -n "$UVICORN_PIDS" ]; then
    echo -e "Terminating uvicorn workers (PIDs: $UVICORN_PIDS)..."
    for pid in $UVICORN_PIDS; do
        kill -15 "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
    done
    STOPPED_ANY=true
fi

sleep 1

# Verify port 8000 is clean
RECHECK=$(lsof -ti :8000 2>/dev/null || true)
if [ -z "$RECHECK" ]; then
    echo -e "\n${GREEN}${BOLD}✓ All application services have been stopped cleanly.${NC}"
    echo -e "${GREEN}✓ Port 8000 is now free. Project databases and data remain preserved.${NC}\n"
else
    echo -e "\n${YELLOW}! Force killing remaining processes on port 8000 (PIDs: $RECHECK)...${NC}"
    kill -9 $RECHECK 2>/dev/null || true
    echo -e "${GREEN}✓ Port 8000 cleared.${NC}\n"
fi
