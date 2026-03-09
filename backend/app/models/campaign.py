import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, JSON, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


class CampaignType(str, enum.Enum):
    email_sequence = "email_sequence"
    linkedin_sequence = "linkedin_sequence"
    multi_channel = "multi_channel"


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    completed = "completed"
    archived = "archived"


class StepChannel(str, enum.Enum):
    email = "email"
    linkedin_message = "linkedin_message"
    linkedin_connection_request = "linkedin_connection_request"
    linkedin_comment = "linkedin_comment"
    phone_reminder = "phone_reminder"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(
        SAEnum(CampaignType, name="campaign_type_enum", create_constraint=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(CampaignStatus, name="campaign_status_enum", create_constraint=True),
        default=CampaignStatus.draft,
        nullable=False,
    )
    target_criteria: Mapped[dict] = mapped_column(JSON, default=dict)
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    settings: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "sending_schedule": {"days": ["mon", "tue", "wed", "thu", "fri"]},
            "timezone": "America/New_York",
            "daily_send_limit": 50,
            "min_wait_minutes": 60,
        },
    )
    stats_cache: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "total_enrolled": 0,
            "emails_sent": 0,
            "opens": 0,
            "clicks": 0,
            "replies": 0,
            "handoffs": 0,
        },
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    creator = relationship("User", back_populates="campaigns")
    steps = relationship(
        "CampaignStep", back_populates="campaign", order_by="CampaignStep.step_number"
    )
    enrollments = relationship("LeadCampaignEnrollment", back_populates="campaign")


class CampaignStep(Base):
    __tablename__ = "campaign_steps"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    campaign_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    channel: Mapped[str] = mapped_column(
        SAEnum(StepChannel, name="step_channel_enum", create_constraint=True),
        nullable=False,
    )
    delay_days: Mapped[int] = mapped_column(Integer, default=0)
    delay_hours: Mapped[int] = mapped_column(Integer, default=0)
    subject_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body_template: Mapped[str] = mapped_column(Text, nullable=False)
    ai_personalization_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_personalization_instructions: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    condition: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    variant_group: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    variant_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    campaign = relationship("Campaign", back_populates="steps")
