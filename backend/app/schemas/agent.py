from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    type: str
    config: dict = {}
    persona: str = ""
    system_prompt: str = ""


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    config: Optional[dict] = None
    persona: Optional[str] = None
    system_prompt: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    type: str
    status: str
    config: dict
    persona: str
    system_prompt: str
    stats: dict
    last_active_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
