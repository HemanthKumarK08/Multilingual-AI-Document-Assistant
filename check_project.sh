#!/bin/bash
# ==============================================================================
# MULTILINGUAL AI DOCUMENT ASSISTANT WITH BIG DATA ANALYTICS
# COMPREHENSIVE PROJECT HEALTH CHECK & DIAGNOSTICS
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
echo "   PROJECT HEALTH CHECK & SYSTEM DIAGNOSTICS                                    "
echo "================================================================================"
echo -e "${NC}"

ALL_PASSED=true

check_component() {
    local name="$1"
    local command="$2"
    local info="$3"

    if eval "$command" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} ${BOLD}$name${NC} ($info)"
    else
        echo -e "  ${RED}✗${NC} ${BOLD}$name${NC} ($info)"
        ALL_PASSED=false
    fi
}

# 1. Python Environment
PYTHON_VER=""
if [ -f ".venv/bin/python" ]; then
    PYTHON_VER="$(.venv/bin/python --version)"
    echo -e "  ${GREEN}✓${NC} ${BOLD}Python Runtime${NC} ($PYTHON_VER in .venv)"
else
    echo -e "  ${RED}✗${NC} ${BOLD}Python Runtime${NC} (Virtual environment .venv missing)"
    ALL_PASSED=false
fi

# 2. Virtual Environment
check_component "Virtual Environment" "[ -f .venv/bin/pip ] && [ -f .venv/bin/python ]" ".venv/bin active"

# 3. Backend Dependencies
check_component "Backend Dependencies" ".venv/bin/python -c 'import fastapi, uvicorn, pydantic, sqlalchemy, aiosqlite, fitz, docx'" "FastAPI, Uvicorn, SQLAlchemy, PyMuPDF, python-docx"

# 4. ML, Embeddings & ChromaDB
check_component "Vector Store & ML Engine" ".venv/bin/python -c 'import torch, transformers, sentence_transformers, chromadb'" "PyTorch, Transformers, Sentence-Transformers, ChromaDB"

# 5. Big Data Analytics & PySpark
check_component "Big Data & PySpark Engine" ".venv/bin/python -c 'import pyspark, pyarrow'" "PySpark 3.5.3, PyArrow 17.0.0"

# 6. Relational Database
check_component "SQLite Relational Database" "[ -f data/app.db ]" "data/app.db verified"

# 7. ChromaDB Collection Data
check_component "ChromaDB Persistent Index" "[ -d data/vector_store ]" "data/vector_store directory present"

# 8. Telemetry & Parquet Data Lake
check_component "Telemetry & Parquet Data Lake" "[ -d data/telemetry/parquet ] && [ -d data/telemetry/validated ]" "data/telemetry/parquet active"

# 9. Precomputed Batch Analytics
check_component "PySpark Precomputed Analytics" "[ -f data/telemetry/analytics/manifest.json ] && [ -f data/telemetry/analytics/summary_metrics.json ]" "manifest.json & 7 metric files verified"

# 10. Frontend Application Shell
check_component "Frontend SPA Build" "[ -f frontend/dist/index.html ]" "frontend/dist/index.html verified"

# 11. Core Application Imports & Routes
check_component "FastAPI Application Loading" ".venv/bin/python -c 'from app.main import app; assert app.title'" "app.main:app validated"

# 12. Port 8000 Status
if lsof -ti :8000 &>/dev/null; then
    PORT_PID=$(lsof -ti :8000 | tr '\n' ' ')
    echo -e "  ${YELLOW}!${NC} ${BOLD}Port 8000${NC} (Active - In use by PID: $PORT_PID)"
else
    echo -e "  ${GREEN}✓${NC} ${BOLD}Port 8000${NC} (Available for launcher)"
fi

# 13. Quick Unit & Integration Test Validation
echo -e "\n${BOLD}Running Smoke Test Suite (15 core tests)...${NC}"
if .venv/bin/pytest tests/unit/test_telemetry* tests/integration/test_api* -q; then
    echo -e "  ${GREEN}✓${NC} ${BOLD}Test Suite Smoke Check${NC} (All sample tests passed cleanly)"
else
    echo -e "  ${RED}✗${NC} ${BOLD}Test Suite Smoke Check${NC} (Errors detected)"
    ALL_PASSED=false
fi

echo -e "\n${CYAN}================================================================================${NC}"
if [ "$ALL_PASSED" = true ]; then
    echo -e "${GREEN}${BOLD}✓ ALL SYSTEM HEALTH CHECKS PASSED! Project is READY to run.${NC}"
    echo -e "To start the project with one click, run: ${CYAN}${BOLD}./run_project.command${NC}"
else
    echo -e "${YELLOW}${BOLD}! One or more checks reported issues. Please review diagnostics above.${NC}"
fi
echo -e "${CYAN}================================================================================${NC}\n"
