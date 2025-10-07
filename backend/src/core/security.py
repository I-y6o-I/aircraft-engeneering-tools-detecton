from __future__ import annotations
from datetime import datetime, timezone
import jwt
from passlib.context import CryptContext
from .settings import settings, jwt_exp_delta

# Configure passlib with bcrypt
pwd_ctx = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

def hash_password(raw: str) -> str:
    """Hash password with bcrypt."""
    return pwd_ctx.hash(raw)

def verify_password(raw: str, hashed: str) -> bool:
    """Verify raw password against bcrypt hash."""

    return pwd_ctx.verify(raw, hashed)

def create_access_token(sub: str, role: str) -> tuple[str, int]:
    """Create signed JWT with subject (user id) and role."""

    now = datetime.now(timezone.utc)
    exp = now + jwt_exp_delta()
    payload = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    ttl = int(exp.timestamp() - now.timestamp())
    return token, ttl

def decode_access_token(token: str) -> dict:
    """Decode and validate JWT; raises if invalid/expired."""

    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])