from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CampaignStepCreate(BaseModel):
    step_number: int = Field(ge=1)
    channel: str
    delay_days: int = Field(default=0, ge=0)
    delay_hours: int = Field(default=0, ge=0)
    subject_template: Optional[str] = None
    body_template: str = Field(min_length=1)
    ai_personalization_enabled: bool = True
    ai_personalization_instructions: Optional[str] = None
    condition: Optional[dict] = None
    variant_group: Optional[str] = None
    variant_label: Optional[str] = None


class CampaignStepUpdate(BaseModel):
    step_number: Optional[int] = None
    channel: Optional[str] = None
    delay_days: Optional[int] = None
    delay_hours: Optional[int] = None
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    ai_personalization_enabled: Optional[bool] = None
    ai_personalization_instructions: Optional[str] = None
    condition: Optional[dict] = None


class CampaignStepResponse(BaseModel):
    id: str
    campaign_id: str
    step_number: int
    channel: str
    delay_days: int
    delay_hours: int
    subject_template: Optional[str]
    body_template: str
    ai_personalization_enabled: bool
    ai_personalization_instructions: Optional[str]
    condition: Optional[dict]
    variant_group: Optional[str]
    variant_label: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    type: str
    target_criteria: dict = {}
    settings: dict = {}
    steps: list[CampaignStepCreate] = []


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    target_criteria: Optional[dict] = None
    settings: Optional[dict] = None


class CampaignResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    type: str
    status: str
    target_criteria: dict
    created_by: str
    settings: dict
    stats_cache: dict
    steps: list[CampaignStepResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
