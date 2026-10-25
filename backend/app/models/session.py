import enum
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class CompressionMode(str, enum.Enum):
    COMPRESS = "compress"
    SUMMARIZE = "summarize"
    OFF = "off"


class CompressionSession(Base):
    __tablename__ = "compression_sessions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_name = Column(String(255), nullable=False)
    mode = Column(SQLEnum(CompressionMode), nullable=False, default=CompressionMode.COMPRESS)
    provider = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=True)

    total_requests = Column(Integer, nullable=False, default=0)
    eligible_requests = Column(Integer, nullable=False, default=0)
    tokens_before = Column(Integer, nullable=False, default=0)
    tokens_after = Column(Integer, nullable=False, default=0)
    tokens_saved = Column(Integer, nullable=False, default=0)
    savings_ratio = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="sessions")
    requests = relationship("CompressionRequest", back_populates="session", cascade="all, delete-orphan")

    @property
    def savings_ratio_float(self) -> float:
        return self.savings_ratio / 10000.0

    @savings_ratio_float.setter
    def savings_ratio_float(self, value: float) -> None:
        self.savings_ratio = int(value * 10000)