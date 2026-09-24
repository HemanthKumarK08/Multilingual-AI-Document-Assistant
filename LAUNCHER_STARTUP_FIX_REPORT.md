# LAUNCHER STARTUP FIX REPORT

## 1. Root Cause
The `run_project.command` (and `start_project.sh`) launcher previously had a hardcoded 15-second readiness polling timeout (`for i in {1..30}; do sleep 0.5; done`). 

During application startup, FastAPI's `lifespan` pre-warms the `intfloat/multilingual-e5-small` embedding model, ChromaDB persistent collections, and the in-memory BM25 index. This thorough pre-warming takes approximately 13.8–20.0 seconds on cold start. 

Because the polling loop timed out at 15 seconds, it exited the readiness loop before the server completed initialization, skipped the `open "http://localhost:8000/"` command, and then blocked on `wait $SERVER_PID`. As a result, Uvicorn started successfully in the background, but the default web browser was never triggered.

---

## 2. Files Changed
1. `run_project.command`:
   - Increased readiness polling window to 60 seconds (`MAX_WAIT_SECONDS=60` with 1-second interval).
   - Added premature crash detection (`kill -0 "$SERVER_PID"`).
   - Ensured browser opens to `http://localhost:8000/` exactly once after HTTP 200 is confirmed on `/health`.
   - Cleaned up signal trapping (`SIGINT`, `SIGTERM`) to ensure single, non-recursive exit handling on Ctrl+C.
2. `start_project.sh`:
   - Aligned with identical 60s readiness polling, premature crash check, and auto-browser opening.
3. `start_project.command`:
   - Added symlink pointing to `run_project.command` with full executable permissions.

---

## 3. Exact Launcher Lifecycle
```
User executes ./run_project.command
   │
   ▼
1. Detect Python 3.11 environment (.venv / Homebrew / System)
   │
   ▼
2. Setup / Verify Virtual Environment (.venv)
   │
   ▼
3. Check Backend Dependencies & Verify Frontend Bundle (dist/index.html)
   │
   ▼
4. Verify Configuration (.env)
   │
   ▼
5. Check Port 8000 Availability (terminate any stale PIDs cleanly)
   │
   ▼
6. Launch Uvicorn in Background & Capture SERVER_PID
   │
   ▼
7. FastAPI Lifespan Execution:
   ├─ SQLite Schema Verification
   ├─ SentenceTransformer Embedding Pre-warming (intfloat/multilingual-e5-small)
   ├─ ChromaDB Vector Store Pre-warming
   └─ In-Memory BM25 Lexical Index Pre-warming
   │
   ▼
8. Readiness Polling (up to 60s, polling http://127.0.0.1:8000/health)
   │
   ▼
9. Health Check Returns HTTP 200 OK
   │
   ▼
10. Automatically Open Default Web Browser to http://localhost:8000/
   │
   ▼
11. Stream Server Logs and Wait on SERVER_PID until Ctrl+C or stop_project
```

---

## 4. Health Readiness Mechanism
- Polls `http://127.0.0.1:8000/health` with `curl -s -f`.
- Checks process liveness with `kill -0 "$SERVER_PID"` on each iteration.
- Emits progress logs every 5 seconds (`Initializing services (X s / 60s)...`).
- Triggers browser launch only upon receiving a validated HTTP 200 status.

---

## 5. Browser Auto-Open Behavior
- Opens the user-facing application shell at `http://localhost:8000/`.
- Does NOT open `/docs` (Swagger UI remains accessible manually at `http://localhost:8000/docs`).
- Exactly ONE browser window/tab is launched per launcher start via macOS `open "http://localhost:8000/"`.

---

## 6. Process / PID Handling
- PID is captured immediately upon launch (`SERVER_PID=$!`).
- Clean shutdown handler on `SIGINT` / `SIGTERM` sends `SIGTERM` (`kill -15`), waits for clean process termination, and cleans up.
- Port 8000 stale process killer checks only port 8000 and matching Uvicorn process IDs, avoiding killing unrelated system processes.

---

## 7. Ctrl+C Verification
- Pressing `Ctrl+C` sends `SIGINT` to the launcher.
- Trap handler catches `SIGINT`, gracefully stops Uvicorn (`kill -15`), waits for database connections to close, and exits cleanly.

---

## 8. Stop Project Verification
- Running `./stop_project.command` identifies active processes on port 8000 and matching `uvicorn.*app\.main:app` processes.
- Gracefully terminates workers, verifies port 8000 is clean, and exits with confirmation.

---

## 9. Clean-Start Result
- **Launcher Execution**: `[6/6] Starting Multilingual AI Document Assistant...`
- **Embedding Pre-warming**: ~13.8–20.0s (completed in background).
- **Health Check**: Passed (`GET /health HTTP/1.1 200 OK`).
- **Browser**: Opened `http://localhost:8000/` automatically.
- **Frontend SPA**: Loaded `index.html`, `index-DATCFs8M.js`, `index-aW8p9gB7.css`, and analytics health metrics.

---

## 10. RAG Smoke Test
- **Query**: `"in which website credit guarantee scheme can be applied"`
- **Response**: `"Applications are made through eligible MLIs (Banks/NBFCs). The document provides https://www.cgtmse.in for detailed guidelines [Source 1]."`
- **Citation**: Page 10 of `b9b4423d_MSMESchemebooklet2025-26.pdf`
- **Total Latency**: 50.85 ms (Zero cold-start delay).

---

## 11. Regression Results
- **Total Tests**: **506**
- **Passed**: **500**
- **Skipped**: **6**
- **Failed**: **0**
- **Frontend Build**: `✓ built in 1.67s` (`dist/index.html` 1.03 kB)

---

## 12. Remaining Warnings
1. `resource_tracker: "There appear to be 1 leaked semaphore objects"`:
   - **Investigation**: Originates from PySpark's underlying Java/Python IPC multiprocessing process upon batch analytics execution shutdown. It is harmless runtime cleanup behavior from PySpark and does not leak memory or block backend operations.
2. `python-multipart` deprecation notice from Starlette:
   - Standard Starlette library warning; harmless and non-breaking.
