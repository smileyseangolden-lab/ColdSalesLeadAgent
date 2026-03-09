import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


class InteractionType(str, enum.Enum):
    email_sent = "email_sent"
    email_received = "email_received"
    email_opened = "email_opened"
    email_clicked = "email_clicked"
    email_bounced = "email_bounced"
    linkedin_sent = "linkedin_sent"
    linkedin_received = "linkedin_received"
    linkedin_connection_sent = "linkedin_connection_sent"
    linkedin_connection_accepted = "linkedin_connection_accepted"
    phone_call = "phone_call"
    meeting_scheduled = "meeting_scheduled"
    note_added = "note_added"
    status_change = "status_change"
    score_change = "score_change"
    handoff = "handoff"


class InteractionChannel(str, enum.Enum):
    email = "email"
    linkedin = "linkedin"
    phone = "phone"
    internal = "internal"


class InteractionDirection(str, enum.Enum):
    outbound = "outbound"
    inbound = "inbound"
    internal = "internal"


class Sentiment(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    unknown = "unknown"


class Intent(str, enum.Enum):
    interested = "interested"
    not_interested = "not_interested"
    question = "question"
    objection = "objection"
    meeting_request = "meeting_request"
    unsubscribe = "unsubscribe"
    out_of_office = "out_of_office"
    auto_reply = "auto_reply"
    referral = "referral"
    spam = "spam"
    unknown = "unknown"


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    lead_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("campaigns.id"), nullable=True
    )
    campaign_step_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("campaign_steps.id"), nullable=True
    )
    agent_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("ai_agents.id"), nullable=True
    )
    type: Mapped[str] = mapped_column(
        SAEnum(InteractionType, name="interaction_type_enum", create_constraint=True),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(
        SAEnum(InteractionChannel, name="interaction_channel_enum", create_constraint=True),
        nullable=False,
    )
    direction: Mapped[str] = mapped_column(
        SAEnum(InteractionDirection, name="interaction_direction_enum", create_constraint=True),
        nullable=False,
    )
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    sentiment: Mapped[Optional[str]] = mapped_column(
        SAEnum(Sentiment, name="sentiment_enum", create_constraint=True),
        nullable=True,
    )
    intent: Mapped[Optional[str]] = mapped_column(
        SAEnum(Intent, name="intent_enum", create_constraint=True),
        nullable=True,
    )
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    lead = relationship("Lead", back_populates="interactions")

    __table_args__ = (
        Index("ix_interactions_lead_created", "lead_id", "created_at"),
        Index("ix_interactions_type", "type"),
    )
