"""
Main FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.landing_page import get_landing_page_html
from app.core.logging import setup_logging, logger
from app.db.session import init_db, close_db
from app.api.routes import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifespan context."""
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} in [{settings.APP_ENV}] mode...")

    # Initialize SQLite database schema
    await init_db()
    logger.info("Database tables verified/initialized.")

    # Pre-warm existing SentenceTransformerEmbeddingProvider, vector store, and lexical index
    try:
        import time
        t0 = time.perf_counter()
        from app.api.routes.qa import _rag_coordinator
        logger.info("Pre-warming embedding model, ChromaDB collection, and BM25 index...")
        if _rag_coordinator and _rag_coordinator.retrieval_coordinator:
            rc = _rag_coordinator.retrieval_coordinator
            if rc.dense_retriever:
                rc.dense_retriever.embedding_provider.embed_query("warmup query")
            if rc.lexical_retriever:
                _ = rc.lexical_retriever.index
        warmup_ms = (time.perf_counter() - t0) * 1000.0
        logger.info(f"Embedding model, ChromaDB collection, and BM25 index pre-warmed in {warmup_ms:.2f}ms.")
    except Exception as e:
        logger.warning(f"Pre-warming encountered an issue (non-fatal): {e}")

    yield

    # Clean shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Database connections closed.")

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Multilingual AI Document Assistant with Big Data Analytics",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router under /api/v1 and root
app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router, prefix="")

# Frontend dist paths
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"

if FRONTEND_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS)), name="frontend_assets")

def serve_frontend_or_landing():
    if FRONTEND_INDEX.exists():
        return FileResponse(
            str(FRONTEND_INDEX),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0",
            }
        )
    return HTMLResponse(content=get_landing_page_html())

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    User-facing application entry page.
    Returns modern application SPA shell for browser navigation,
    with content negotiation fallback to JSON for programmatic API clients.
    """
    accept = request.headers.get("accept", "")
    if "text/html" not in accept and ("application/json" in accept or accept == "*/*" or request.query_params.get("format") == "json"):
        return JSONResponse({
            "app_name": settings.APP_NAME,
            "version": "0.1.0",
            "status": "online",
            "environment": settings.APP_ENV,
            "docs_url": "/docs",
            "health_url": "/health"
        })
    return serve_frontend_or_landing()

# SPA Client-side Route handlers to allow direct browser navigation / deep links
@app.get("/documents", response_class=HTMLResponse)
async def frontend_documents(request: Request):
    return serve_frontend_or_landing()

@app.get("/ask", response_class=HTMLResponse)
async def frontend_ask(request: Request):
    return serve_frontend_or_landing()

@app.get("/analytics", response_class=HTMLResponse)
async def frontend_analytics(request: Request):
    return serve_frontend_or_landing()

@app.get("/settings", response_class=HTMLResponse)
async def frontend_settings(request: Request):
    return serve_frontend_or_landing()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG
    )
