import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Enum as SAEnum, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    sales_rep = "sales_rep"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        SAEnum(UserRole, name="user_role", create_constraint=True),
        default=UserRole.sales_rep,
        nullable=False,
    )
    team: Mapped[str] = mapped_column(String(100), nullable=True)
    notification_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    leads = relationship("Lead", back_populates="assigned_user", foreign_keys="Lead.assigned_to")
    campaigns = relationship("Campaign", back_populates="creator")
    email_accounts = relationship("EmailAccount", back_populates="user")
    handoffs = relationship("Handoff", back_populates="to_user", foreign_keys="Handoff.to_user_id")
