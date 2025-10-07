from __future__ import annotations
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user import User
from ..core.security import hash_password, verify_password, create_access_token, decode_access_token
from ..core.db import get_session

VALID_ROLES = {"simple", "admin"}

class UserService:
    """User service responsible for registration and authentication logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, employee_id: str, password: str, role: str = "simple") -> User:
        """Register a new user with given role (simple|admin)."""

        if role not in VALID_ROLES:
            raise ValueError("invalid role")
        exists = (await self.db.execute(select(User).where(User.employee_id == employee_id))).scalar_one_or_none()
        if exists:
            raise ValueError("employee_id already registered")
        u = User(employee_id=employee_id, password_hash=hash_password(password), role=role)
        self.db.add(u)
        await self.db.commit()
        await self.db.refresh(u)
        return u

    async def authenticate(self, employee_id: str, password: str) -> tuple[User, str, int]:
        """Authenticate by employee_id and password; return user and signed JWT."""
        
        u = (await self.db.execute(select(User).where(User.employee_id == employee_id))).scalar_one_or_none()
        if not u or not verify_password(password, u.password_hash):
            raise PermissionError("invalid credentials")
        token, ttl = create_access_token(str(u.id), u.role)
        return u, token, ttl


# FastAPI security scheme for Bearer token
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_session)
) -> User:
    """FastAPI dependency to get current user from JWT token."""
    
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        # Fetch user from database
        user = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return user
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )