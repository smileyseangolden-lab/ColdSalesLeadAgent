import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Text, DateTime, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


class AgentType(str, enum.Enum):
    outbound_email = "outbound_email"
    outbound_linkedin = "outbound_linkedin"
    reply_handler = "reply_handler"
    lead_scorer = "lead_scorer"
    research_agent = "research_agent"


class AgentStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    error = "error"
    disabled = "disabled"


class AIAgent(Base):
    __tablename__ = "ai_agents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        SAEnum(AgentType, name="agent_type_enum", create_constraint=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(AgentStatus, name="agent_status_enum", create_constraint=True),
        default=AgentStatus.active,
        nullable=False,
    )
    config: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "tone": "professional",
            "persona_name": "Sales Development Representative",
            "rate_limit_per_hour": 20,
            "working_hours_start": 8,
            "working_hours_end": 18,
            "working_days": ["mon", "tue", "wed", "thu", "fri"],
            "timezone": "America/New_York",
        },
    )
    persona: Mapped[str] = mapped_column(
        Text,
        default="You are a knowledgeable sales development representative. You are helpful, consultative, and focus on understanding the prospect's challenges before pitching solutions.",
    )
    system_prompt: Mapped[str] = mapped_column(
        Text,
        default="You are an AI sales development representative. Your goal is to engage prospects in meaningful conversations, understand their needs, and help them discover how our solutions can address their challenges.",
    )
    stats: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "messages_sent_today": 0,
            "messages_sent_week": 0,
            "total_messages": 0,
            "response_rate": 0.0,
            "errors_today": 0,
        },
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
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
    leads = relationship("Lead", back_populates="assigned_agent", foreign_keys="Lead.assigned_agent_id")
    handoffs = relationship("Handoff", back_populates="from_agent", foreign_keys="Handoff.from_agent_id")
