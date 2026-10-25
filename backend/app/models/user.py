import enum
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class UserRole(str, enum.Enum):
    OPERATOR = "operator"
    ANALYST = "analyst"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    keycloak_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    roles = Column(String(500), nullable=False, default="operator")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    sessions = relationship("CompressionSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    def get_roles(self) -> list[UserRole]:
        return [UserRole(r.strip()) for r in self.roles.split(",") if r.strip()]

    def set_roles(self, roles: list[UserRole]) -> None:
        self.roles = ",".join([r.value for r in roles])

    def has_role(self, role: UserRole) -> bool:
        return role in self.get_roles()