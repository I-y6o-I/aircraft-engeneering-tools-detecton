from __future__ import annotations
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Enum
from ..core.db import Base

class User(Base):
    __tablename__ = "users"
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(Enum("simple", "admin", name="user_role"), default="simple")