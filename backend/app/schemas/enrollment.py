from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EnrollmentCreate(BaseModel):
    lead_id: str
    campaign_id: str


class EnrollmentResponse(BaseModel):
    id: str
    lead_id: str
    campaign_id: str
    current_step: int
    status: str
    enrolled_at: datetime
    last_step_executed_at: Optional[datetime]
    next_step_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
