# Authentication utilities for JWT and password hashing
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session as DBSession
import logging
import os
import secrets
import string
import warnings

# Suppress passlib bcrypt warnings
warnings.filterwarnings("ignore", category=UserWarning, module="passlib")

# Password hashing with bcrypt config for compatibility
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    logger = logging.getLogger(__name__)
    if os.getenv("ENVIRONMENT") == "production":
        SECRET_KEY = secrets.token_urlsafe(48)
        logger.error("❌ JWT_SECRET missing in production. Using ephemeral fallback secret; set JWT_SECRET immediately.")
    else:
        SECRET_KEY = "dev-secret-key-not-for-production-change-me"
        logger.warning("⚠️  Using development JWT_SECRET - set JWT_SECRET env var in production!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    issued_at = datetime.now(timezone.utc)
    if expires_delta:
        expire = issued_at + expires_delta
    else:
        expire = issued_at + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": issued_at.timestamp()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_referral_code() -> str:
    """Generate a unique 8-character alphanumeric referral code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))


async def get_current_agent(
    credentials: Optional[HTTPAuthorizationCredentials],
    db: DBSession
):
    """Dependency to get the current authenticated agent from JWT token."""
    from models import Agent  # Import here to avoid circular dependency
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    
    agent_id: int = payload.get("agent_id")
    if agent_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if this token is still the active one (single session enforcement)
    if agent.last_active_token_issued_at:
        token_issued_at_timestamp = payload.get("iat")
        if token_issued_at_timestamp:
            # Create aware datetime from token timestamp
            token_issued_at = datetime.fromtimestamp(token_issued_at_timestamp, tz=timezone.utc)
            # Strip timezone info to match naive datetimes stored in database
            token_issued_at = token_issued_at.replace(tzinfo=None)
            if token_issued_at < agent.last_active_token_issued_at:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired - you logged in from another device",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    
    return agent


async def require_super_admin(
    agent = Depends(get_current_agent),
):
    """Ensure the current agent is a super admin."""
    from models import AgentRole

    if agent.role != AgentRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return agent
