from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HandoffCreate(BaseModel):
    lead_id: str
    from_agent_id: str
    to_user_id: str
    reason: str
    lead_score_at_handoff: int
    context_summary: str


class HandoffUpdate(BaseModel):
    status: Optional[str] = None
    outcome_notes: Optional[str] = None


class HandoffResponse(BaseModel):
    id: str
    lead_id: str
    from_agent_id: str
    to_user_id: str
    reason: str
    lead_score_at_handoff: int
    context_summary: str
    status: str
    accepted_at: Optional[datetime]
    completed_at: Optional[datetime]
    outcome_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
