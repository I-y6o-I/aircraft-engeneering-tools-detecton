from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Text, JSON, ForeignKey
from ..core.db import Base

class Session(Base):
    __tablename__ = "sessions"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    
    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Session metadata
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    threshold_used: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Session data snapshots (JSON fields)
    handout_predict: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    handout_final: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    handover_predict: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    handover_final: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Images (base64 encoded)
    handout_image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    handover_image: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Hash for integrity checking
    hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)