from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class EmailAccountCreate(BaseModel):
    email_address: EmailStr
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    daily_send_limit: int = Field(default=50, ge=1, le=500)
    warmup_enabled: bool = False
    warmup_daily_increment: int = Field(default=2, ge=1, le=20)
    signature_html: Optional[str] = None


class EmailAccountUpdate(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    daily_send_limit: Optional[int] = None
    warmup_enabled: Optional[bool] = None
    warmup_daily_increment: Optional[int] = None
    signature_html: Optional[str] = None
    is_active: Optional[bool] = None


class EmailAccountResponse(BaseModel):
    id: str
    user_id: str
    email_address: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    imap_host: Optional[str]
    imap_port: Optional[int]
    daily_send_limit: int
    sends_today: int
    warmup_enabled: bool
    warmup_daily_increment: int
    signature_html: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
