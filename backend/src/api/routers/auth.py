from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.db import get_session
from ...services.users_service import UserService
from ..schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    MeResponse
)
from ...core.auth import get_current_user
from ...models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_session)):
    """Create a new user with selected role (simple|admin)."""
    
    svc = UserService(db)
    try:
        u = await svc.register(payload.employee_id, payload.password, payload.role)
    except ValueError as e:
        # 409 for duplicate or invalid role
        msg = str(e)
        status = 409 if "already" in msg else 422
        raise HTTPException(status_code=status, detail=msg)
    now = datetime.now(timezone.utc).isoformat()
    return {"user_id": str(u.id), "employee_id": u.employee_id, "role": u.role, "created_at": now}

@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_session)):
    """Authenticate user and return access token."""

    svc = UserService(db)
    try:
        _u, token, ttl = await svc.authenticate(payload.employee_id, payload.password)
    except PermissionError:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return {"access_token": token, "token_type": "Bearer", "expires_in": ttl}

@router.get("/me", response_model=MeResponse)
async def me(user: User = Depends(get_current_user)):
    """Return current user's profile derived from JWT."""

    return {"user_id": str(user.id), "employee_id": user.employee_id, "role": user.role}
