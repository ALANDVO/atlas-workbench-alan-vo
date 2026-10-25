from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base
from app.models.session import CompressionMode


class CompressionRequest(Base):
    __tablename__ = "compression_requests"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PG_UUID(as_uuid=True), ForeignKey("compression_sessions.id"), nullable=False, index=True)
    provider = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    mode = Column(SQLEnum(CompressionMode), nullable=False)

    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    compressed_tokens = Column(Integer, nullable=False, default=0)
    recovered_tokens = Column(Integer, nullable=False, default=0)
    savings = Column(Integer, nullable=False, default=0)
    mcp_recovery_used = Column(Boolean, nullable=False, default=False)
    duration_ms = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="completed")
    error_message = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("CompressionSession", back_populates="requests")