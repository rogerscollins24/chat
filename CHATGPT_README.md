# LeadPulse Chat System - Complete Architecture Guide for ChatGPT

## 🎯 Application Overview

**LeadPulse Chat System** is a production-ready, multi-tenant lead management and real-time chat platform designed for businesses to engage with potential leads through ads and manage conversations with internal support agents.

**Core Purpose**: Enable two-way communication between leads/clients (who click ads) and internal support agents, with complete message persistence, real-time WebSocket notifications, and referral-based lead assignment.

---

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT APPLICATIONS                      │
├─────────────────────────────────────────────────────────────┤
│  Lead/Client Interface (Public)  │  Agent Dashboard (Admin)  │
│  URL: http://localhost:5173/     │  URL: http://localhost:5173/admin  │
└──────────────────┬───────────────────────────────┬──────────┘
                   │                               │
              HTTP / WebSocket                 HTTP / WebSocket
           (REST API + Real-time)           (REST API + Real-time)
                   │                               │
        ┌──────────▼───────────────────────────────▼──────────┐
        │          FASTAPI BACKEND SERVER                     │
        │      http://localhost:8000                          │
        │  (REST API + WebSocket Connections)                │
        └──────────┬───────────────────────────────┬──────────┘
                   │                               │
           [Agent Authentication]          [Message Handling]
           [Lead Assignment]                [Database Persistence]
           [Message Routing]                [Real-time Notifications]
                   │                               │
        ┌──────────▼───────────────────────────────▼──────────┐
        │    DATABASE (SQLite Dev / PostgreSQL Prod)          │
        │  - Sessions (conversations)                         │
        │  - Messages (all messages saved)                    │
        │  - Agents (authentication, referral codes)          │
        │  - LeadMetadata (tracking, attribution)             │
        │  - MessageTemplates (predefined responses)          │
        └─────────────────────────────────────────────────────┘
```

---

## 📁 Frontend Structure (React + TypeScript + Vite)

### Root Level Files
- **`App.tsx`** (1287 lines) - Main application component with routing, state management
- **`index.tsx`** - React entry point
- **`index.html`** - HTML template
- **`types.ts`** - TypeScript type definitions for all interfaces
- **`constants.tsx`** - Application constants, initial data, AD sources
- **`vite.config.ts`** - Vite build configuration
- **`tsconfig.json`** - TypeScript configuration
- **`package.json`** - Node dependencies (React, React Router, WebSocket)

### `/components` Directory
- **`SuperAdminDashboard.tsx`** - Super admin dashboard for managing all agents
- **`Icons.tsx`** - Reusable SVG icon components (SendIcon, etc.)

### `/src/services` Directory
- **`api.ts`** - API client for all backend communication (REST endpoints)



### Frontend Routes
```
/                    → Lead/Client Chat Interface
/admin               → Agent Dashboard (requires authentication)
/admin/super-admin   → Super Admin Dashboard
```

### Key Frontend Features
1. **Lead/Client Interface**
   - Allows leads to chat with agents
   - Tracks ad source, browser, location
   - Real-time message display

2. **Agent Dashboard**
   - Agent login/authentication
   - List of active chat sessions
   - Real-time message notifications
   - Send/receive messages
   - Mark sessions as resolved/archived
   - Internal notes (visible only to agents)

3. **Super Admin Dashboard**
   - Manage all agents
   - Create/edit/delete agents
   - View agent performance metrics
   - Assign referral codes

---

## 🔧 Backend Structure (FastAPI + SQLAlchemy + PostgreSQL)

### Backend Entry Point
- **`main.py`** (954 lines) - FastAPI app setup, routes, WebSocket management

### Core Backend Files

#### **`auth.py`**
- Password hashing (bcrypt, 12 rounds)
- JWT token creation (7-day expiration)
- Token validation and verification
- Referral code generation (8-character alphanumeric)

#### **`models.py`**
- SQLAlchemy ORM models:
  - `Agent` - Agent/user accounts with emails, passwords, roles
  - `Session` - Chat sessions between leads and agents
  - `Message` - Individual messages in sessions
  - `LeadMetadata` - Tracking data (browser, location, adId, campaign, IP)
  - `MessageTemplate` - Pre-made response templates
  - `SessionStatus`, `SenderRole`, `AgentRole` - Enums

#### **`schemas.py`**
- Pydantic schemas for request/response validation:
  - AgentCreate, AgentLogin, AgentResponse, TokenResponse
  - SessionCreate, SessionResponse, SessionUpdate
  - MessageCreate, MessageResponse
  - LeadMetadataCreate
  - MessageTemplateCreate, MessageTemplateResponse

#### **`requirements.txt`**
- Dependencies:
  - fastapi, uvicorn (web framework)
  - sqlalchemy (ORM)
  - psycopg2-binary (PostgreSQL driver)
  - python-dotenv (environment variables)
  - pydantic (validation)
  - pyjwt, passlib (authentication)
  - python-multipart (form handling)
  - python-jose (JWT handling)
  - bcrypt (password hashing)

#### **Database Setup Files**
- **`migrate_to_postgres.py`** - Migration script from SQLite to PostgreSQL
- **`test_postgresql_backend.py`** - Tests for PostgreSQL backend
- **`create_templates_table.py`** - Creates message templates table

#### **Configuration**
- **`.env.example`** - Template for environment variables
- **`.env.postgres`** - PostgreSQL-specific configuration

### Backend Routes & API Endpoints

#### **Agent Management**
```
POST   /api/agents/register          - Create new agent account
POST   /api/agents/login             - Agent login (returns JWT token)
GET    /api/agents/{agent_id}        - Get agent details
PUT    /api/agents/{agent_id}        - Update agent profile
POST   /api/agents/reset-password    - Reset agent password
POST   /api/agents/rotate-referral   - Generate new referral code
GET    /api/agents                   - List all agents (super admin)
DELETE /api/agents/{agent_id}        - Delete agent (super admin)
```

#### **Session Management**
```
POST   /api/sessions                 - Create new chat session
GET    /api/sessions                 - Get all sessions for agent
GET    /api/sessions/{session_id}    - Get specific session
PUT    /api/sessions/{session_id}    - Update session (status, etc.)
DELETE /api/sessions/{session_id}    - Archive session
```

#### **Messages**
```
POST   /api/messages                 - Send message
GET    /api/sessions/{session_id}/messages - Get session messages
GET    /api/messages/search          - Search messages
DELETE /api/messages/{message_id}    - Delete message
```

#### **Message Templates**
```
POST   /api/templates                - Create template
GET    /api/templates                - List all templates
PUT    /api/templates/{template_id}  - Update template
DELETE /api/templates/{template_id}  - Delete template
```

#### **WebSocket**
```
WebSocket /ws/{session_id}/{agent_id}  - Real-time message connection
```

#### **Utilities**
```
GET    /api/health                   - Health check
GET    /docs                         - Swagger API documentation
GET    /docs/openapi.json            - OpenAPI schema
```

---

## 💾 Database Schema

### Tables & Relationships

#### **agents**
```sql
id (PK) | email (UNIQUE) | name | password_hash | referral_code | 
is_default_pool | role | created_at | updated_at
```
- **Purpose**: Store agent credentials and authentication
- **Key Field**: `referral_code` - Unique code leads use to assign to agent

#### **sessions**
```sql
id (PK) | lead_id | lead_name | lead_avatar_url | assigned_agent_id (FK) | 
status | created_at | updated_at | is_offline_notified
```
- **Purpose**: Track individual chat conversations
- **Status Values**: OPEN, RESOLVED, ARCHIVED
- **agent_id**: Foreign key to agents table

#### **messages**
```sql
id (PK) | session_id (FK) | sender_id | sender_role | text | 
timestamp | delivery_status | is_internal | created_at
```
- **Purpose**: Store all messages with complete history
- **sender_role**: 'USER' or 'AGENT'
- **is_internal**: For private agent notes only
- **delivery_status**: 'sent', 'delivered', 'read'

#### **lead_metadata**
```sql
id (PK) | session_id (FK) | browser | location | ip | 
ad_id | campaign | agent_referral_code | city | device | created_at
```
- **Purpose**: Track lead source, device, location for analytics
- **Fields**: Used for attribution and reporting

#### **message_templates**
```sql
id (PK) | agent_id (FK) | name | content | category | 
is_active | created_at | updated_at
```
- **Purpose**: Store pre-made response templates for agents
- **Use Case**: Quick replies for common questions

---

## 🔐 Authentication & Security

### Agent Authentication Flow
```
1. Agent registers with email/password → AUTO-GENERATED REFERRAL CODE
2. Agent password hashed with bcrypt (12 rounds)
3. Agent logs in with email/password → JWT token created (7-day expiration)
4. Token sent in Authorization header for all requests
5. Token verified by get_current_agent() middleware
```

### Lead Assignment
```
1. Lead clicks ad with referral code in URL
2. Lead metadata stored with referral_code
3. System finds agent with matching referral_code
4. If no match, assign to default pool agent
5. All messages routed to assigned agent
```

### Security Features
- Password hashing with bcrypt (industry standard)
- JWT tokens with expiration
- CORS enabled for specific origins
- HTTP Bearer token authentication
- SQL injection protection via SQLAlchemy ORM

---

## 🔄 Real-Time Communication

### WebSocket Flow
```
1. Agent connects: WebSocket /ws/{session_id}/{agent_id}
2. Client sends message via REST API
3. Backend detects new message, broadcasts via WebSocket
4. Connected agents receive real-time notification
5. Message persisted to database immediately
6. If WebSocket unavailable, fall back to polling (REST)
```

### Message Persistence
**Key Feature: ALL MESSAGES SAVED TO DATABASE IMMEDIATELY**
```
1. Message received from client/agent
2. Message inserted into messages table
3. Response sent to sender immediately
4. WebSocket notification to connected recipients
5. Message visible on all tabs/devices via database query
6. No message loss, complete history preserved
```

---

## 🚀 Running the Application

### Prerequisites
- **Frontend**: Node.js 18+ (npm available)
- **Backend**: Python 3.9+ (pip available)
- **Database**: PostgreSQL 12+ running on localhost:5432

### Starting Backend
```bash
cd backend

# Create & activate virtual environment
python -m venv venv
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run backend
python main.py
# Listens on http://localhost:8000
```

### Starting Frontend
```bash
npm install
npm run dev
# Listens on http://localhost:5173
```

### File Integrity
```bash
npm run build  # Production build
npm run preview # Preview build
```

---

## 📊 Data Flow Examples

### Example 1: Lead Sends Message
```
1. Lead types message in chat UI
2. Frontend calls: POST /api/messages
3. Backend:
   - Creates Message record in database
   - Updates Session.updated_at
   - Broadcasts via WebSocket to assigned agent
   - Returns success response
4. Frontend:
   - Updates local message state
   - Displays "message sent"
   - Sets message.status = 'sent'
5. Agent (if connected):
   - Receives WebSocket notification
   - Loads message from database if needed
   - Displays new message in real-time
```

### Example 2: Agent Responds
```
1. Agent types response in dashboard
2. Frontend calls: POST /api/messages (with agent auth token)
3. Backend:
   - Creates Message record (sender_role = 'AGENT')
   - Broadcasts via WebSocket to lead session
4. Lead (if viewing chat):
   - Receives WebSocket notification
   - Message displays in real-time
5. Agent (all tabs/devices):
   - Message visible immediately
   - Persisted to database
```

### Example 3: Multi-Tab Sync
```
1. Agent opens dashboard in Tab A
   - Loads sessions from /api/sessions
   - Establishes WebSocket connection
2. Agent opens dashboard in Tab B
   - Loads same sessions independently from database
   - Establishes separate WebSocket connection
3. Lead sends message
   - Message saved to database
   - WebSocket broadcast received by both tabs
   - Both tabs display message in real-time
   - Perfect sync across all tabs
```

---

## 🎨 UI Components Breakdown

### Lead Interface Components
- **Message Input Form** - Text input with send button
- **Message Bubble** - Styled message display with timestamps
- **Session List** - All active and archived conversations
- **Typing Indicator** - Shows when agent is typing
- **Status Badges** - OPEN, RESOLVED, ARCHIVED indicators

### Agent Interface Components
- **Session Card** - Compact session preview in list
- **Message Viewer** - Full message history from database
- **Agent Actions** - Mark resolved, archive, send internal notes
- **Referral Code Display** - Shows agent's unique code for leads
- **Notification Panel** - Real-time alerts for new messages

### Super Admin Components
- **Agent Management Table** - CRUD operations for agents
- **Referral Code Manager** - View and rotate referral codes
- **Activity Dashboard** - Analytics and metrics
- **Role Manager** - Assign admin/agent roles

---

## 🔍 Key Technical Decisions

### Why This Architecture?
1. **React + TypeScript** - Type safety, component reusability, large ecosystem
2. **FastAPI** - Fast async Python, built-in WebSocket support, auto API docs
3. **SQLAlchemy** - Database agnostic ORM, easy migrations
4. **PostgreSQL** - Reliable, scalable, production-ready
5. **JWT Tokens** - Stateless authentication, mobile/API friendly
6. **WebSocket** - Real-time low-latency communication
7. **Message Persistence** - Complete audit trail, legal compliance

### Why Database-Backed Messages?
- **No Message Loss** - All messages saved immediately to database
- **History Available On Demand** - Load past conversations anytime
- **Multi-Device Sync** - Same data across all tabs and devices
- **Audit Trail** - Complete record for compliance
- **Scalability** - Database handles thousands of messages

---

## 🛠️ Common Development Tasks

### Adding a New Agent Endpoint
1. Define Pydantic schema in `schemas.py`
2. Add SQLAlchemy model in `models.py` (if needed)
3. Create route handler in `main.py`
4. Call from frontend via `api.ts`

### Adding a New Chat Feature
1. Update `types.ts` with new TypeScript interfaces
2. Update database schema in `models.py`
3. Update API endpoints in `main.py`
4. Update frontend components in `App.tsx` or `/components`
5. Test with both lead and agent interfaces

### Debugging Message Issues
1. Check database: `SELECT * FROM messages WHERE session_id = ?`
2. Check WebSocket connections in browser DevTools
3. Check backend logs for errors
4. Verify JWT token expiration
5. Test REST API directly: `curl http://localhost:8000/docs`

---

## 📝 Environment Configuration

### Required `.env` Variables
```
DATABASE_URL=postgresql://user:password@localhost:5432/adconnect_db
JWT_SECRET=your-super-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Database Connection Strings
```
SQLite (dev):  sqlite:///./leadpulse.db
PostgreSQL:    postgresql://user:pass@host:5432/dbname
Fallback:      Uses PostgreSQL by default in main.py
```

---

## ✅ Quality Assurance

### Testing Checklist
- [ ] Agent can register and login
- [ ] Lead can send message without login
- [ ] Messages persist after page refresh
- [ ] Real-time WebSocket delivery works
- [ ] Referral code assignment works
- [ ] Default pool agent fallback works
- [ ] Multi-tab synchronization works
- [ ] Message search/history retrieval works
- [ ] Internal agent notes don't leak to leads
- [ ] JWT token expiration works
- [ ] Session status transitions work (OPEN → RESOLVED → ARCHIVED)

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **OpenAPI Schema**: http://localhost:8000/docs/openapi.json
- **Database Docs**: See `models.py` for table definitions
- **Type Definitions**: See `types.ts` for frontend interfaces
- **Constants**: See `constants.tsx` for initial data

---

## 🎯 Use This Guide With ChatGPT

When asking ChatGPT to help with this project, include this context:
```
[Paste this README into ChatGPT]

Now you understand the complete architecture. You can:
1. Help debug specific issues
2. Write new features following this architecture
3. Optimize performance
4. Add new API endpoints
5. Refactor components
6. Create migration scripts
7. Build new dashboards
```

Example prompt for ChatGPT:
> "Using the LeadPulse Chat System architecture, how would I add a feature to notify agents of idle sessions?"

This provides ChatGPT with the full context needed for accurate, architecture-aware suggestions.
