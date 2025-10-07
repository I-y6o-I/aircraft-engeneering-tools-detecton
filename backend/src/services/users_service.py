from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.user import User
from ..core.security import hash_password, verify_password, create_access_token

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