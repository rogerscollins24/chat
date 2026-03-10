from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class SessionStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class SenderRole(str, Enum):
    USER = "USER"
    AGENT = "AGENT"


class LeadMetadataCreate(BaseModel):
    ip: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    browser: Optional[str] = None
    device: Optional[str] = None
    ad_id: Optional[str] = None
    agent_referral_code: Optional[str] = None


class LeadMetadataResponse(LeadMetadataCreate):
    id: int
    session_id: int

    class Config:
        from_attributes = True


# Agent Schemas
class AgentCreate(BaseModel):
    email: EmailStr  # Validates email format automatically
    password: str = Field(..., min_length=8, max_length=128)  # Require 8+ chars
    name: str = Field(..., min_length=1, max_length=255)
    is_default_pool: bool = False
    role: Optional[str] = "AGENT"
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password has uppercase, lowercase, and number"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class AgentUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    password: Optional[str] = None
    is_default_pool: Optional[bool] = None
    role: Optional[str] = None


class AgentLogin(BaseModel):
    email: str
    password: str


class AgentResponse(BaseModel):
    id: int
    email: str
    name: str
    referral_code: str
    is_default_pool: bool
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    agent: AgentResponse


class AgentResetPassword(BaseModel):
    new_password: str


class AgentReferralRotate(BaseModel):
    referral_code: Optional[str] = None


class SessionCreate(BaseModel):
    user_id: str
    user_name: str
    user_avatar: Optional[str] = None
    ad_source: str
    referral_code: Optional[str] = None
    lead_metadata: Optional[LeadMetadataCreate] = None


class SessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None


class MessageCreate(BaseModel):
    session_id: int
    sender_id: str = Field(..., min_length=1, max_length=255)
    sender_role: SenderRole
    text: str = Field(..., min_length=1, max_length=5000)  # Limit message size to prevent DoS
    is_internal: bool = False


class MessageResponse(MessageCreate):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: int
    user_id: str
    user_name: str
    user_avatar: Optional[str]
    ad_source: str
    assigned_agent_id: Optional[int]
    status: SessionStatus
    has_auto_welcome_sent: bool = False
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []
    lead_metadata: Optional[LeadMetadataResponse] = None

    class Config:
        from_attributes = True


class MessageTemplateCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)  # Limit template size


class MessageTemplateResponse(BaseModel):
    id: int
    text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
