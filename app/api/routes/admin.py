"""
Administrator Authentication & Management Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import User
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.schemas import LoginRequest, TokenResponse

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def admin_login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticates administrator credentials and returns an HMAC session token."""
    stmt = select(User).where(User.username == req.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash) or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid administrator username or password."
        )

    token = create_access_token(
        subject=user.username,
        role=user.role,
        expires_minutes=settings.ADMIN_TOKEN_EXPIRY_MINUTES
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ADMIN_TOKEN_EXPIRY_MINUTES,
        role=user.role
    )
