import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, JSON, ForeignKey, Enum as SAEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import enum


class LeadSource(str, enum.Enum):
    manual_entry = "manual_entry"
    csv_upload = "csv_upload"
    linkedin_import = "linkedin_import"
    api_import = "api_import"
    referral = "referral"


class LeadStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    engaged = "engaged"
    warm = "warm"
    hot = "hot"
    qualified = "qualified"
    handed_off = "handed_off"
    converted = "converted"
    lost = "lost"
    do_not_contact = "do_not_contact"


class CompanySize(str, enum.Enum):
    xs = "1-10"
    sm = "11-50"
    md = "51-200"
    lg = "201-500"
    xl = "501-1000"
    xxl = "1001-5000"
    enterprise = "5000+"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    company_size: Mapped[Optional[str]] = mapped_column(
        SAEnum(CompanySize, name="company_size_enum", create_constraint=True),
        nullable=True,
    )
    location_city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location_country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(
        SAEnum(LeadSource, name="lead_source_enum", create_constraint=True),
        default=LeadSource.manual_entry,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(LeadStatus, name="lead_status_enum", create_constraint=True),
        default=LeadStatus.new,
        nullable=False,
        index=True,
    )
    lead_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    assigned_to: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    assigned_agent_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("ai_agents.id"), nullable=True
    )
    tags: Mapped[list] = mapped_column(JSON, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_contacted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_action_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    handoff_at: Mapped[Optional[datetime]] = mapped_column(
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
    assigned_user = relationship("User", back_populates="leads", foreign_keys=[assigned_to])
    assigned_agent = relationship("AIAgent", back_populates="leads", foreign_keys=[assigned_agent_id])
    interactions = relationship("Interaction", back_populates="lead", order_by="Interaction.created_at.desc()")
    enrollments = relationship("LeadCampaignEnrollment", back_populates="lead")
    score_history = relationship("LeadScoreHistory", back_populates="lead", order_by="LeadScoreHistory.created_at.desc()")
    handoffs = relationship("Handoff", back_populates="lead")

    __table_args__ = (
        Index("ix_leads_status_score", "status", "lead_score"),
        Index("ix_leads_next_action", "next_action_at"),
    )
