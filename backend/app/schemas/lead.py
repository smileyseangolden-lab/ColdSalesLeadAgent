from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class LeadCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_name: str = Field(min_length=1, max_length=255)
    job_title: str = Field(min_length=1, max_length=255)
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    source: str = "manual_entry"
    tags: list[str] = []
    custom_fields: dict = {}
    notes: Optional[str] = None
    assigned_to: Optional[str] = None

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not re.match(r"https?://(www\.)?linkedin\.com/", v):
            raise ValueError("Invalid LinkedIn URL format")
        return v


class LeadUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    status: Optional[str] = None
    lead_score: Optional[int] = Field(None, ge=0, le=100)
    assigned_to: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    tags: Optional[list[str]] = None
    custom_fields: Optional[dict] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    full_name: str
    email: str
    phone: Optional[str]
    linkedin_url: Optional[str]
    company_name: str
    job_title: str
    industry: Optional[str]
    company_size: Optional[str]
    location_city: Optional[str]
    location_state: Optional[str]
    location_country: Optional[str]
    source: str
    status: str
    lead_score: int
    assigned_to: Optional[str]
    assigned_agent_id: Optional[str]
    tags: list
    custom_fields: dict
    notes: Optional[str]
    last_contacted_at: Optional[datetime]
    next_action_at: Optional[datetime]
    handoff_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadBulkCreate(BaseModel):
    leads: list[LeadCreate]
    tags: list[str] = []
    source: str = "csv_upload"


class LeadFilter(BaseModel):
    status: Optional[str] = None
    score_min: Optional[int] = None
    score_max: Optional[int] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    assigned_to: Optional[str] = None
    tags: Optional[list[str]] = None
    source: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 50
    sort_by: str = "created_at"
    sort_order: str = "desc"


class LeadListResponse(BaseModel):
    leads: list[LeadResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
