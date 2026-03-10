from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
import httpx
import re
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session as DBSession
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from models import Base, Session, Message, LeadMetadata, SessionStatus, SenderRole, Agent, AgentRole, MessageTemplate
from schemas import (
    SessionCreate, SessionResponse, SessionUpdate,
    MessageCreate, MessageResponse,
    LeadMetadataCreate, AgentCreate, AgentLogin, AgentResponse, TokenResponse,
    AgentUpdate, AgentResetPassword, AgentReferralRotate,
    MessageTemplateCreate, MessageTemplateResponse
)
from auth import (
    get_password_hash, verify_password, create_access_token, 
    generate_referral_code, get_current_agent, security
)
from typing import List, Optional
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://adconnect_user:adconnect_secure_password_123@localhost:5432/adconnect_db"
)

# Add SQLite-specific connection args if using SQLite
connect_args = {}
if "sqlite" in DATABASE_URL.lower():
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables (with error handling for permission issues)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"Could not auto-create tables (this is OK if they exist): {e}")

# FastAPI app
app = FastAPI(
    title="LeadPulse Chat System API",
    description="Backend API for LeadPulse chat system",
    version="1.0.0"
)

# CORS middleware - whitelist specific origins for production
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT"],
    allow_headers=["Content-Type", "Authorization"],
)

# Startup event to ensure tables exist
@app.on_event("startup")
async def startup_event():
    """Ensure all tables exist on startup"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables verified/created")
    except Exception as e:
        logger.warning(f"⚠️  Warning creating tables on startup: {e}")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def super_admin_guard(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: DBSession = Depends(get_db)
):
    agent = await get_current_agent(credentials, db)
    if agent.role != AgentRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin privileges required")
    return agent


# Helper functions for device info and geolocation
def extract_device_info(user_agent: str) -> dict:
    """Extract browser, OS, and device type from User-Agent string"""
    user_agent = user_agent.lower() if user_agent else ""
    
    # Detect browser
    browser = "Unknown"
    if "chrome" in user_agent and "edg" not in user_agent:
        match = re.search(r"chrome/([0-9.]+)", user_agent)
        browser = f"Chrome {match.group(1)}" if match else "Chrome"
    elif "safari" in user_agent and "chrome" not in user_agent:
        match = re.search(r"version/([0-9.]+)", user_agent)
        browser = f"Safari {match.group(1)}" if match else "Safari"
    elif "firefox" in user_agent:
        match = re.search(r"firefox/([0-9.]+)", user_agent)
        browser = f"Firefox {match.group(1)}" if match else "Firefox"
    elif "edg" in user_agent:
        match = re.search(r"edg/([0-9.]+)", user_agent)
        browser = f"Edge {match.group(1)}" if match else "Edge"
    elif "opera" in user_agent or "opr" in user_agent:
        browser = "Opera"
    
    # Detect OS
    os_info = "Unknown"
    if "windows" in user_agent:
        match = re.search(r"windows nt ([0-9.]+)", user_agent)
        os_info = f"Windows {match.group(1)}" if match else "Windows"
    elif "macintosh" in user_agent or "mac os x" in user_agent:
        match = re.search(r"mac os x ([0-9_]+)", user_agent)
        if match:
            version = match.group(1).replace("_", ".")
            os_info = f"macOS {version}"
        else:
            os_info = "macOS"
    elif "iphone" in user_agent:
        match = re.search(r"iphone os ([0-9_]+)", user_agent)
        os_info = f"iOS {match.group(1).replace('_', '.')}" if match else "iOS"
    elif "ipad" in user_agent:
        match = re.search(r"os ([0-9_]+)", user_agent)
        os_info = f"iPadOS {match.group(1).replace('_', '.')}" if match else "iPadOS"
    elif "android" in user_agent:
        match = re.search(r"android ([0-9.]+)", user_agent)
        os_info = f"Android {match.group(1)}" if match else "Android"
    elif "linux" in user_agent:
        os_info = "Linux"
    
    # Detect device type
    device_type = "Desktop"
    if any(m in user_agent for m in ["mobile", "iphone", "ipod", "android", "blackberry", "windows phone"]):
        device_type = "Mobile"
    elif any(m in user_agent for m in ["ipad", "tablet"]):
        device_type = "Tablet"
    
    return {
        "browser": browser,
        "os": os_info,
        "device_type": device_type
    }


def get_client_ip(request: Request) -> str:
    """Extract real client IP from request, considering proxies"""
    # Check for proxied IP first (for Render and other deployments)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()
    
    # Check for other common proxy headers
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # Use direct connection IP
    return request.client.host if request.client else "Unknown"


async def get_geolocation_from_ip(ip_address: str) -> dict:
    """Lookup city and country from IP address using ip-api.com"""
    if not ip_address or ip_address == "Unknown":
        return {"city": "Unknown", "country": "Unknown"}
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://ip-api.com/json/{ip_address}")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    return {
                        "city": data.get("city", "Unknown"),
                        "country": data.get("country", "Unknown"),
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon")
                    }
    except Exception as e:
        logger.warning(f"Failed to lookup geolocation for IP {ip_address}: {e}")
    
    return {"city": "Unknown", "country": "Unknown"}

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}  # session_id -> list of websockets
        self.agent_connections: dict = {}   # agent_id -> websocket

    async def connect(self, session_id: int, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, session_id: int, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].remove(websocket)

    def connect_agent(self, agent_id: int, websocket: WebSocket):
        self.agent_connections[agent_id] = websocket

    def disconnect_agent(self, agent_id: int):
        if agent_id in self.agent_connections:
            del self.agent_connections[agent_id]

    async def broadcast(self, session_id: int, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")

    async def notify_agent(self, agent_id: int, message: dict):
        """Send notification to a specific agent's WebSocket connection."""
        if agent_id in self.agent_connections:
            try:
                await self.agent_connections[agent_id].send_json(message)
            except Exception as e:
                logger.error(f"Error notifying agent {agent_id}: {e}")

manager = ConnectionManager()

# ==================== HELPER FUNCTIONS ====================

async def send_auto_welcome_message(
    db: DBSession, 
    session: Session, 
    manager: ConnectionManager,
    ref_code: Optional[str] = None
):
    """Send automatic welcome message for ad referral sessions.
    
    Args:
        db: Database session
        session: Session object to send welcome message to
        manager: ConnectionManager for WebSocket broadcasts
        ref_code: The referral code used (for logging)
    """
    try:
        # The exact welcome message content as specified
        welcome_text = """Thank you for reaching out to us! 👋

To assist you more effectively, could you kindly share the following details;
• Full name
• Location (city/country)
• Phone number

This will help us provide more accurate guidance."""
        
        # Create the welcome message as an AGENT message
        welcome_message = Message(
            session_id=session.id,
            sender_id=f"agent-{session.assigned_agent_id}",
            sender_role=SenderRole.AGENT,
            text=welcome_text,
            is_internal=False
        )
        db.add(welcome_message)
        
        # Mark that auto welcome has been sent
        session.has_auto_welcome_sent = True
        
        # Commit to database
        db.commit()
        db.refresh(welcome_message)
        
        logger.info(f"✅ Auto welcome message sent for session {session.id} from referral code '{ref_code}'")
        
        # Broadcast to client via WebSocket
        await manager.broadcast(session.id, {
            "type": "message",
            "data": {
                "id": welcome_message.id,
                "session_id": welcome_message.session_id,
                "sender_id": welcome_message.sender_id,
                "sender_role": welcome_message.sender_role,
                "text": welcome_message.text,
                "is_internal": welcome_message.is_internal,
                "timestamp": welcome_message.timestamp.isoformat()
            }
        })
        
        # Notify the assigned agent
        if session.assigned_agent_id:
            await manager.notify_agent(session.assigned_agent_id, {
                "type": "message",
                "data": {
                    "id": welcome_message.id,
                    "session_id": welcome_message.session_id,
                    "sender_id": welcome_message.sender_id,
                    "sender_role": welcome_message.sender_role,
                    "text": welcome_message.text,
                    "is_internal": welcome_message.is_internal,
                    "timestamp": welcome_message.timestamp.isoformat()
                }
            })
            logger.debug(f"Notified agent {session.assigned_agent_id} about auto welcome message")
        
    except Exception as e:
        logger.error(f"❌ Error sending auto welcome message for session {session.id}: {e}")
        db.rollback()
        # Don't raise - we don't want to fail session creation if welcome message fails

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    return {
        "message": "LeadPulse Chat System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health/db")
async def health_db():
    """Database health check endpoint for Render/browser verification."""
    required_tables = ["agents", "sessions", "messages", "lead_metadata", "message_templates"]

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        missing_tables = [table for table in required_tables if table not in existing_tables]

        session_columns = [column["name"] for column in inspector.get_columns("sessions")]
        has_auto_welcome_sent_column = "has_auto_welcome_sent" in session_columns

        health_ok = len(missing_tables) == 0 and has_auto_welcome_sent_column

        return {
            "status": "ok" if health_ok else "degraded",
            "database_connected": True,
            "required_tables": required_tables,
            "existing_tables": existing_tables,
            "missing_tables": missing_tables,
            "checks": {
                "sessions_has_auto_welcome_sent": has_auto_welcome_sent_column
            }
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "database_connected": False,
                "error": str(e)
            }
        )

# ==================== AGENT ENDPOINTS ====================

@app.post("/api/agents/register", response_model=AgentResponse)
async def register_agent(agent_data: AgentCreate, db: DBSession = Depends(get_db)):
    """Register a new agent with auto-generated referral code."""
    try:
        # Check if email already exists
        existing_agent = db.query(Agent).filter(Agent.email == agent_data.email).first()
        if existing_agent:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # If this is set as default pool, unset any existing default
        if agent_data.is_default_pool:
            db.query(Agent).filter(Agent.is_default_pool == True).update({"is_default_pool": False})
        
        # Generate unique referral code
        referral_code = generate_referral_code()
        while db.query(Agent).filter(Agent.referral_code == referral_code).first():
            referral_code = generate_referral_code()
        
        # Create new agent
        db_agent = Agent(
            email=agent_data.email,
            password_hash=get_password_hash(agent_data.password),
            name=agent_data.name,
            referral_code=referral_code,
            is_default_pool=agent_data.is_default_pool,
            role=AgentRole.AGENT
        )
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        
        logger.info(f"New agent registered: {agent_data.email} with referral code: {referral_code}")
        return db_agent
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering agent: {e}")
        raise HTTPException(status_code=500, detail="Failed to register agent")


@app.post("/api/agents/login", response_model=TokenResponse)
async def login_agent(login_data: AgentLogin, db: DBSession = Depends(get_db)):
    """Authenticate an agent and return JWT token."""
    try:
        # Find agent by email
        agent = db.query(Agent).filter(Agent.email == login_data.email).first()
        if not agent or not verify_password(login_data.password, agent.password_hash):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )
        
        # Invalidate old sessions by setting last_active_token_issued_at to now
        agent.last_active_token_issued_at = datetime.utcnow()  # Store as naive UTC datetime for DB compatibility
        db.commit()
        
        # Create access token with new issued timestamp
        access_token = create_access_token(data={"agent_id": agent.id, "email": agent.email, "role": agent.role.value})
        
        logger.info(f"Agent logged in: {agent.email}")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            agent=AgentResponse.model_validate(agent)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.get("/api/agents", response_model=List[AgentResponse])
async def get_all_agents(db: DBSession = Depends(get_db), current_agent=Depends(super_admin_guard)):
    """Get list of all agents (super-admin only)."""
    try:
        agents = db.query(Agent).all()
        return agents
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch agents")

@app.get("/api/agents/me", response_model=AgentResponse)
async def get_current_agent_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: DBSession = Depends(get_db)
):
    """Get current authenticated agent's profile."""
    current_agent = await get_current_agent(credentials, db)
    return current_agent


# ==================== SUPER ADMIN AGENT MANAGEMENT ====================


@app.post("/api/admin/agents", response_model=AgentResponse)
async def create_agent_admin(agent_data: AgentCreate, db: DBSession = Depends(get_db), current_agent=Depends(super_admin_guard)):
    """Super admin: create an agent (or super admin)."""
    try:
        existing_agent = db.query(Agent).filter(Agent.email == agent_data.email).first()
        if existing_agent:
            raise HTTPException(status_code=400, detail="Email already registered")

        if agent_data.is_default_pool:
            db.query(Agent).filter(Agent.is_default_pool == True).update({"is_default_pool": False})

        if agent_data.role:
            try:
                role = AgentRole[agent_data.role.upper()]
            except KeyError:
                raise HTTPException(status_code=400, detail="Invalid role. Use AGENT or SUPER_ADMIN")
        else:
            role = AgentRole.AGENT
        referral_code = generate_referral_code()
        while db.query(Agent).filter(Agent.referral_code == referral_code).first():
            referral_code = generate_referral_code()

        db_agent = Agent(
            email=agent_data.email,
            password_hash=get_password_hash(agent_data.password),
            name=agent_data.name,
            referral_code=referral_code,
            is_default_pool=agent_data.is_default_pool,
            role=role,
        )
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        logger.info(f"New agent created: {agent_data.email} with role: {role.value}")
        return db_agent
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error creating agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating agent: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")


@app.patch("/api/admin/agents/{agent_id}", response_model=AgentResponse)
async def update_agent_admin(agent_id: int, updates: AgentUpdate, db: DBSession = Depends(get_db), current_agent=Depends(super_admin_guard)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if updates.email is not None:
        agent.email = updates.email
    if updates.name is not None:
        agent.name = updates.name
    if updates.is_default_pool is not None:
        if updates.is_default_pool:
            db.query(Agent).filter(Agent.is_default_pool == True).update({"is_default_pool": False})
        agent.is_default_pool = updates.is_default_pool
    if updates.role is not None:
        try:
            agent.role = AgentRole[updates.role]
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid role")
    if updates.password:
        agent.password_hash = get_password_hash(updates.password)

    db.commit()
    db.refresh(agent)
    return agent


@app.post("/api/admin/agents/{agent_id}/reset_password")
async def reset_agent_password(agent_id: int, payload: AgentResetPassword, db: DBSession = Depends(get_db), current_agent=Depends(super_admin_guard)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "ok"}


@app.post("/api/admin/agents/{agent_id}/referral", response_model=AgentResponse)
async def rotate_referral(agent_id: int, _: AgentReferralRotate, db: DBSession = Depends(get_db), current_agent=Depends(super_admin_guard)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    referral_code = generate_referral_code()
    while db.query(Agent).filter(Agent.referral_code == referral_code).first():
        referral_code = generate_referral_code()
    agent.referral_code = referral_code
    db.commit()
    db.refresh(agent)
    return agent


@app.delete("/api/admin/agents/{agent_id}")
async def delete_agent(agent_id: int, db: DBSession = Depends(get_db), current_agent=Depends(super_admin_guard)):
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()
    return {"status": "deleted"}


# ==================== SESSION ENDPOINTS ====================

# POST /api/sessions - Create a new session
@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate, 
    request: Request,
    db: DBSession = Depends(get_db)
):
    """Create a new chat session when a user clicks an ad."""
    try:
        # Extract device info and IP from request
        user_agent = request.headers.get("user-agent", "")
        client_ip = get_client_ip(request)
        device_info = extract_device_info(user_agent)
        
        # Get geolocation from IP
        geolocation = await get_geolocation_from_ip(client_ip)
        
        # Check if session already exists for this user_id
        existing_session = db.query(Session).filter(
            Session.user_id == session_data.user_id
        ).first()
        
        if existing_session:
            return existing_session

        # Determine agent assignment
        assigned_agent_id = None
        referral_code_used = session_data.referral_code
        
        if session_data.referral_code:
            # Look up agent by referral code
            agent = db.query(Agent).filter(Agent.referral_code == session_data.referral_code).first()
            if agent:
                assigned_agent_id = agent.id
                logger.info(f"Session assigned to agent {agent.name} via referral code {session_data.referral_code}")
            else:
                logger.warning(f"Invalid referral code: {session_data.referral_code}")
                referral_code_used = None
        
        # If no referral code or invalid, assign to default pool agent
        if assigned_agent_id is None:
            default_agent = db.query(Agent).filter(Agent.is_default_pool == True).first()
            if default_agent:
                assigned_agent_id = default_agent.id
                referral_code_used = "DEFAULT_POOL"
                logger.info(f"Session assigned to default pool agent: {default_agent.name}")
            else:
                logger.warning("No default pool agent configured, session will be unassigned")

        # Create new session
        db_session = Session(
            user_id=session_data.user_id,
            user_name=session_data.user_name,
            user_avatar=session_data.user_avatar,
            ad_source=session_data.ad_source,
            assigned_agent_id=assigned_agent_id,
            status=SessionStatus.OPEN
        )
        db.add(db_session)
        db.flush()

        # Add metadata with automatically extracted device info and geolocation
        metadata = LeadMetadata(
            session_id=db_session.id,
            ip=client_ip,
            location=f"{geolocation.get('city', 'Unknown')}, {geolocation.get('country', 'Unknown')}",
            city=geolocation.get('city'),
            browser=device_info.get('browser'),
            device=f"{device_info.get('device_type')} - {device_info.get('os')}",
            ad_id=session_data.lead_metadata.ad_id if session_data.lead_metadata else None,
            agent_referral_code=referral_code_used
        )
        db.add(metadata)

        db.commit()
        db.refresh(db_session)
        
        # Send automatic welcome message for ad referral sessions
        # Only if: (1) ref_code exists and is not DEFAULT_POOL, (2) no messages yet, (3) not already sent
        if referral_code_used and referral_code_used != "DEFAULT_POOL" and not db_session.has_auto_welcome_sent:
            # Check if session has zero messages
            message_count = db.query(Message).filter(Message.session_id == db_session.id).count()
            if message_count == 0:
                logger.info(f"Sending auto welcome message for new ad referral session {db_session.id}")
                await send_auto_welcome_message(db, db_session, manager, referral_code_used)
            else:
                logger.debug(f"Skipping auto welcome - session {db_session.id} already has {message_count} messages")
        else:
            if not referral_code_used:
                logger.debug(f"Skipping auto welcome - no referral code for session {db_session.id}")
            elif referral_code_used == "DEFAULT_POOL":
                logger.debug(f"Skipping auto welcome - DEFAULT_POOL session {db_session.id}")
            elif db_session.has_auto_welcome_sent:
                logger.debug(f"Skipping auto welcome - already sent for session {db_session.id}")
        
        return db_session

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")

# GET /api/sessions - List all sessions (filtered by agent or all)
@app.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions(
    status: Optional[str] = None,
    include_all: bool = False,
    skip: int = 0,
    limit: int = 100,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: DBSession = Depends(get_db)
):
    """List sessions. If authenticated, returns agent's assigned sessions. Use include_all=true for all sessions."""
    try:
        current_agent = None
        if credentials:
            try:
                current_agent = await get_current_agent(credentials, db)
            except HTTPException:
                # If authentication fails, continue without agent filter
                pass
        
        query = db.query(Session)
        
        # Filter by agent if authenticated and not requesting all
        if current_agent and not include_all:
            query = query.filter(Session.assigned_agent_id == current_agent.id)
            logger.info(f"Listing sessions for agent: {current_agent.email}")
        elif include_all:
            # Only super admins can request include_all
            if not current_agent or current_agent.role != AgentRole.SUPER_ADMIN:
                raise HTTPException(status_code=403, detail="Super admin privileges required")
            logger.info("Listing all sessions (admin view)")
        else:
            logger.info("Listing all sessions (no authentication)")
        
        # Filter by status if provided
        if status:
            try:
                status_enum = SessionStatus[status.upper()]
                query = query.filter(Session.status == status_enum)
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        sessions = query.order_by(Session.updated_at.desc()).offset(skip).limit(limit).all()
        return sessions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to list sessions")

@app.get("/api/templates", response_model=List[MessageTemplateResponse])
async def list_message_templates(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: DBSession = Depends(get_db)
):
    """List reusable templates for authenticated agents."""
    await get_current_agent(credentials, db)
    try:
        templates = db.query(MessageTemplate).order_by(MessageTemplate.created_at.desc()).all()
        return templates
    except Exception as e:
        logger.warning(f"Could not fetch templates: {e}")
        return []  # Return empty list if table doesn't exist

@app.post("/api/templates", response_model=MessageTemplateResponse)
async def create_message_template(
    payload: MessageTemplateCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: DBSession = Depends(get_db)
):
    """Save a reusable template (shared across agents)."""
    await get_current_agent(credentials, db)
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Template text cannot be empty")
    try:
        total = db.query(MessageTemplate).count()
        if total >= 5:
            raise HTTPException(status_code=400, detail="Maximum of 5 templates reached")
        template = MessageTemplate(text=text)
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Could not save template: {e}")
        raise HTTPException(status_code=500, detail="Templates are currently unavailable")

@app.delete("/api/templates/{template_id}")
async def delete_message_template(
    template_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: DBSession = Depends(get_db)
):
    """Delete a saved template."""
    await get_current_agent(credentials, db)
    try:
        template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        db.delete(template)
        db.commit()
        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Could not delete template: {e}")
        raise HTTPException(status_code=500, detail="Templates are currently unavailable")

# GET /api/sessions/{id} - Get a specific session
@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: int, db: DBSession = Depends(get_db)):
    """Retrieve a specific chat session with all messages."""
    db_session = db.query(Session).filter(Session.id == session_id).first()
    
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return db_session


# ==================== SUPER ADMIN SESSION OVERSIGHT ====================


@app.get("/api/admin/sessions", response_model=List[SessionResponse])
async def admin_list_sessions(
    status: Optional[str] = None,
    agent_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 200,
    db: DBSession = Depends(get_db),
    current_agent=Depends(super_admin_guard)
):
    query = db.query(Session)
    if status:
        try:
            status_enum = SessionStatus[status.upper()]
            query = query.filter(Session.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid status")
    if agent_id is not None:
        query = query.filter(Session.assigned_agent_id == agent_id)
    sessions = query.order_by(Session.updated_at.desc()).offset(skip).limit(limit).all()
    return sessions


@app.patch("/api/admin/sessions/{session_id}/assign", response_model=SessionResponse)
async def admin_reassign_session(
    session_id: int,
    payload: dict,
    db: DBSession = Depends(get_db),
    current_agent=Depends(super_admin_guard)
):
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    new_agent_id = payload.get("agent_id")
    if new_agent_id is not None:
        agent = db.query(Agent).filter(Agent.id == new_agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        db_session.assigned_agent_id = agent.id

    db.commit()
    db.refresh(db_session)
    return db_session


@app.get("/api/admin/export/sessions")
async def export_sessions(
    status: Optional[str] = None,
    agent_id: Optional[int] = None,
    db: DBSession = Depends(get_db),
    current_agent=Depends(super_admin_guard)
):
    query = db.query(Session)
    if status:
        try:
            status_enum = SessionStatus[status.upper()]
            query = query.filter(Session.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid status")
    if agent_id is not None:
        query = query.filter(Session.assigned_agent_id == agent_id)
    sessions = query.order_by(Session.updated_at.desc()).all()
    # Return JSON export for now
    return {"exported": len(sessions), "sessions": sessions}

# GET /api/sessions/{id}/messages - Fetch chat history
@app.get("/api/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: int,
    skip: int = 0,
    limit: int = 100,
    db: DBSession = Depends(get_db)
):
    """Retrieve all messages for a specific session."""
    # Verify session exists
    db_session = db.query(Session).filter(Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).offset(skip).limit(limit).all()
    
    return messages

# POST /api/messages - Send a message (requires authentication or valid session)
@app.post("/api/messages", response_model=MessageResponse)
async def create_message(
    message_data: MessageCreate,
    db: DBSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Send a message - agents must authenticate, users need valid session."""
    try:
        # If JWT token provided, verify it's a valid agent
        if credentials:
            try:
                agent = await get_current_agent(credentials, db)
                # Agent authenticated - verify they own this session or are super admin
                db_session = db.query(Session).filter(
                    Session.id == message_data.session_id
                ).first()
                if not db_session:
                    raise HTTPException(status_code=404, detail="Session not found")
                if db_session.assigned_agent_id != agent.id and agent.role != 'SUPER_ADMIN':
                    raise HTTPException(status_code=403, detail="Not authorized to message this session")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Token verification failed: {e}")
                raise HTTPException(status_code=401, detail="Invalid token")
        else:
            # User sending message - verify session exists
            db_session = db.query(Session).filter(
                Session.id == message_data.session_id
            ).first()
        
        # Verify session exists
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Create new message
        db_message = Message(
            session_id=message_data.session_id,
            sender_id=message_data.sender_id,
            sender_role=message_data.sender_role,
            text=message_data.text,
            is_internal=message_data.is_internal
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        # Get the session with assigned agent
        session = db.query(Session).filter(Session.id == message_data.session_id).first()
        logger.info(f"Message created: id={db_message.id}, session_id={message_data.session_id}, sender_role={message_data.sender_role}, text={db_message.text}")
        
        if session:
            logger.info(f"Session found: id={session.id}, assigned_agent_id={session.assigned_agent_id}")
        
        # Broadcast message via WebSocket to all clients in session
        await manager.broadcast(message_data.session_id, {
            "type": "message",
            "data": {
                "id": db_message.id,
                "session_id": db_message.session_id,
                "sender_id": db_message.sender_id,
                "sender_role": db_message.sender_role,
                "text": db_message.text,
                "is_internal": db_message.is_internal,
                "timestamp": db_message.timestamp.isoformat()
            }
        })
        
        # Also notify the assigned agent regardless of who sent the message
        if session and session.assigned_agent_id:
            await manager.notify_agent(session.assigned_agent_id, {
                "type": "message",
                "data": {
                    "id": db_message.id,
                    "session_id": db_message.session_id,
                    "sender_id": db_message.sender_id,
                    "sender_role": db_message.sender_role,
                    "text": db_message.text,
                    "is_internal": db_message.is_internal,
                    "timestamp": db_message.timestamp.isoformat()
                }
            })
        
        return db_message

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

# PATCH /api/sessions/{id} - Update session status
@app.patch("/api/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    session_update: SessionUpdate,
    db: DBSession = Depends(get_db)
):
    """Update session status or other fields."""
    try:
        db_session = db.query(Session).filter(Session.id == session_id).first()
        
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update fields if provided
        if session_update.status is not None:
            db_session.status = session_update.status
        if session_update.user_name is not None:
            db_session.user_name = session_update.user_name
        if session_update.user_avatar is not None:
            db_session.user_avatar = session_update.user_avatar
        
        db.commit()
        db.refresh(db_session)
        
        # Broadcast session update via WebSocket
        await manager.broadcast(session_id, {
            "type": "session_update",
            "data": {
                "id": db_session.id,
                "status": db_session.status,
                "updated_at": db_session.updated_at.isoformat()
            }
        })
        
        return db_session

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to update session")

# ==================== WebSocket ENDPOINT ====================

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(session_id: int, websocket: WebSocket):
    """WebSocket endpoint for real-time chat updates."""
    try:
        await manager.connect(session_id, websocket)
        logger.info(f"WebSocket connected for session {session_id}")
        
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                # Handle incoming message
                message = MessageCreate(
                    session_id=session_id,
                    sender_id=data.get("sender_id"),
                    sender_role=data.get("sender_role"),
                    text=data.get("text"),
                    is_internal=data.get("is_internal", False)
                )
                # You could save to DB here if needed
                await manager.broadcast(session_id, {
                    "type": "message",
                    "data": data
                })
            
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id, websocket)

# Agent WebSocket endpoint for real-time updates (requires JWT token)
@app.websocket("/api/ws")
async def agent_websocket(websocket: WebSocket):
    """WebSocket endpoint for agents to receive real-time updates - JWT authenticated."""
    # Get authorization token from query param (WebSocket standard)
    query_params = websocket.scope.get("query_string", b"").decode()
    token = None
    
    # Extract token from query string: ?token=<jwt>
    if "token=" in query_params:
        token = query_params.split("token=")[1].split("&")[0]
    
    if not token:
        await websocket.close(code=4001, reason="Unauthorized - token required")
        logger.warning("WebSocket connection rejected: No token provided")
        return
    
    # Verify token before accepting connection
    db = SessionLocal()
    agent = None
    try:
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        agent = await get_current_agent(credentials, db)
        if not agent:
            await websocket.close(code=4001, reason="Unauthorized - invalid token")
            logger.warning("WebSocket connection rejected: Invalid token")
            return
    except Exception as e:
        logger.error(f"WebSocket auth failed: {e}")
        try:
            await websocket.close(code=4001, reason="Unauthorized")
        except:
            pass
        return
    finally:
        db.close()
    
    # Accept connection after verification
    await websocket.accept()
    agent_id = agent.id
    
    try:
        logger.info(f"✓ Agent {agent_id} ({agent.email}) WebSocket authenticated")
        
        # Listen for messages from the agent
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "subscribe":
                # Agent is subscribing to session updates (already verified)
                manager.connect_agent(agent_id, websocket)
                logger.info(f"✓ Agent {agent_id} subscribed to WebSocket updates")
            
    except WebSocketDisconnect:
        if agent_id:
            manager.disconnect_agent(agent_id)
            logger.info(f"Agent {agent_id} WebSocket disconnected")
    except Exception as e:
        if agent_id:
            manager.disconnect_agent(agent_id)
        logger.error(f"Agent WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

# ==================== OVERFLOW MANAGEMENT ====================

@app.get("/api/admin/agents/overflow")
async def get_overflow_agents(
    db: DBSession = Depends(get_db),
    current_agent=Depends(super_admin_guard)
):
    """Get agents with 50+ sessions in last 24 hours (overflow status)."""
    try:
        from sqlalchemy import func
        from datetime import timedelta
        
        # Get current time and 24 hours ago
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(hours=24)
        
        # Query agents with session count in last 24 hours
        agents_with_counts = db.query(
            Agent.id,
            Agent.name,
            Agent.email,
            Agent.role,
            func.count(Session.id).label('session_count_24h')
        ).outerjoin(Session, Agent.id == Session.assigned_agent_id).filter(
            (Session.created_at >= yesterday) | (Session.created_at == None)
        ).group_by(Agent.id, Agent.name, Agent.email, Agent.role).all()
        
        result = []
        for agent_id, name, email, role, count in agents_with_counts:
            overflow_status = count >= 50 if count else False
            result.append({
                "id": agent_id,
                "name": name,
                "email": email,
                "role": role,
                "session_count_24h": count or 0,
                "is_overflowed": overflow_status
            })
        
        return {
            "agents": sorted(result, key=lambda x: x['session_count_24h'], reverse=True),
            "overflow_threshold": 50
        }
        
    except Exception as e:
        logger.error(f"Error getting overflow agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get overflow agents")


@app.post("/api/admin/reassign-sessions")
async def reassign_sessions(
    payload: dict,
    db: DBSession = Depends(get_db),
    current_agent=Depends(super_admin_guard)
):
    """Reassign open sessions from one agent to another (last 24 hours)."""
    try:
        from_agent_id = payload.get("from_agent_id")
        to_agent_id = payload.get("to_agent_id")
        
        if not from_agent_id or not to_agent_id:
            raise HTTPException(status_code=400, detail="from_agent_id and to_agent_id required")
        
        if from_agent_id == to_agent_id:
            raise HTTPException(status_code=400, detail="Cannot reassign to same agent")
        
        # Verify both agents exist
        from_agent = db.query(Agent).filter(Agent.id == from_agent_id).first()
        to_agent = db.query(Agent).filter(Agent.id == to_agent_id).first()
        
        if not from_agent or not to_agent:
            raise HTTPException(status_code=404, detail="One or both agents not found")
        
        # Get sessions from last 24 hours with OPEN status
        from datetime import timedelta
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        
        sessions_to_reassign = db.query(Session).filter(
            Session.assigned_agent_id == from_agent_id,
            Session.status == SessionStatus.OPEN,
            Session.created_at >= yesterday
        ).all()
        
        count = 0
        for session in sessions_to_reassign:
            session.assigned_agent_id = to_agent_id
            count += 1
        
        db.commit()
        
        # Log the reassignment action
        logger.info(f"Super admin {current_agent.email} reassigned {count} sessions from agent {from_agent.email} ({from_agent_id}) to agent {to_agent.email} ({to_agent_id})")
        
        # Notify the new agent via WebSocket if connected
        await manager.notify_agent(to_agent_id, {
            "type": "sessions_reassigned",
            "data": {
                "reassigned_count": count,
                "from_agent": from_agent.name,
                "admin": current_agent.name
            }
        })
        
        return {
            "status": "ok",
            "reassigned_count": count,
            "from_agent": from_agent.name,
            "to_agent": to_agent.name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error reassigning sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to reassign sessions")

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
