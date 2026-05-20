from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from database import Base

# Many-to-many: users <-> roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id"), primary_key=True),
    Column("role_id", String, ForeignKey("roles.id"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)          # admin, analyst, auditor, client
    description = Column(String, nullable=True)
    permissions = Column(String, nullable=False)                # comma-separated: "upload,edit,delete"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", secondary=user_roles, back_populates="roles")


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    documents = relationship("Document", back_populates="uploader")

    @property
    def permissions(self) -> list[str]:
        """Collect all permissions from all assigned roles."""
        perms = set()
        for role in self.roles:
            for p in role.permissions.split(","):
                perms.add(p.strip())
        return list(perms)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions or "all" in self.permissions
