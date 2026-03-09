from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InteractionCreate(BaseModel):
    lead_id: str
    campaign_id: Optional[str] = None
    campaign_step_id: Optional[str] = None
    agent_id: Optional[str] = None
    type: str
    channel: str
    direction: str
    subject: Optional[str] = None
    body: str
    metadata_json: dict = {}
    sentiment: Optional[str] = None
    intent: Optional[str] = None
    ai_analysis: Optional[dict] = None


class InteractionResponse(BaseModel):
    id: str
    lead_id: str
    campaign_id: Optional[str]
    campaign_step_id: Optional[str]
    agent_id: Optional[str]
    type: str
    channel: str
    direction: str
    subject: Optional[str]
    body: str
    metadata_json: dict
    sentiment: Optional[str]
    intent: Optional[str]
    ai_analysis: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}
