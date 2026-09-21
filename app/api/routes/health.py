"""
Health & Diagnostic Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.db.session import get_db
from app.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def get_health(db: AsyncSession = Depends(get_db)):
    """System health check verifying database and engine configurations."""
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy ({str(e)})"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        app_name=settings.APP_NAME,
        version="0.1.0",
        environment=settings.APP_ENV,
        database_status=db_status,
        vector_store_configured=bool(settings.VECTOR_STORE_PATH),
        llm_primary_provider=settings.LLM_PRIMARY_PROVIDER,
    )
