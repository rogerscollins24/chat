from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

Base = declarative_base()


class SessionStatus(str, enum.Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class SenderRole(str, enum.Enum):
    USER = "USER"
    AGENT = "AGENT"


class AgentRole(str, enum.Enum):
    AGENT = "AGENT"
    SUPER_ADMIN = "SUPER_ADMIN"


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    referral_code = Column(String, unique=True, index=True, nullable=False)
    is_default_pool = Column(Boolean, default=False, index=True)
    # Use non-native enums to avoid CREATE TYPE privileges in Postgres
    role = Column(Enum(AgentRole, native_enum=False), default=AgentRole.AGENT, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_active_token_issued_at = Column(DateTime, nullable=True, default=None)

    # Relationships
    sessions = relationship("Session", back_populates="agent")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    user_name = Column(String)
    user_avatar = Column(String, nullable=True)
    ad_source = Column(String)
    assigned_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)
    status = Column(Enum(SessionStatus, native_enum=False), default=SessionStatus.OPEN)
    has_auto_welcome_sent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    agent = relationship("Agent", back_populates="sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    lead_metadata = relationship("LeadMetadata", back_populates="session", uselist=False, cascade="all, delete-orphan")


class MessageTemplate(Base):
    __tablename__ = "message_templates"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    sender_id = Column(String)
    sender_role = Column(Enum(SenderRole, native_enum=False))
    text = Column(Text)
    is_internal = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("Session", back_populates="messages")


class LeadMetadata(Base):
    __tablename__ = "lead_metadata"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), unique=True, index=True)
    ip = Column(String, nullable=True)
    location = Column(String, nullable=True)
    city = Column(String, nullable=True)
    browser = Column(String, nullable=True)
    device = Column(String, nullable=True)
    ad_id = Column(String, nullable=True)
    agent_referral_code = Column(String, nullable=True)

    # Relationships
    session = relationship("Session", back_populates="lead_metadata")
