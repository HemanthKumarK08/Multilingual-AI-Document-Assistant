"""
API Router Aggregator
Combines health, documents, QA, analytics, and admin routes.
"""

from fastapi import APIRouter
from app.api.routes import health, documents, qa, analytics, admin

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(qa.router, prefix="/qa", tags=["Question Answering"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
