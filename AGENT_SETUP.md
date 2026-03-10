# Agent Authentication & Referral Code System - Setup Guide

## Overview

The system now supports:
- ✅ Agent authentication with JWT tokens
- ✅ Agent login page for `/admin` route
- ✅ Referral code system linking clients to specific agents
- ✅ Default pool agent for clients without referral codes
- ✅ Agent-specific session filtering

## Quick Start

### 1. Create a Default Pool Agent

First, create a default agent to handle clients without referral codes:

```bash
curl -X POST http://localhost:8000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "pool@leadpulse.com",
    "password": "pool123",
    "name": "Pool Agent",
    "is_default_pool": true
  }'
```

**Response:** You'll get a response with the agent details including their unique `referral_code`.

### 2. Create Additional Agents

Create regular agents with unique referral codes:

```bash
curl -X POST http://localhost:8000/api/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@leadpulse.com",
    "password": "secure123",
    "name": "John Smith",
    "is_default_pool": false
  }'
```

**Important:** Save the `referral_code` from the response - agents will share this with clients!

### 3. Login to Agent Portal

1. Navigate to: `http://localhost:5173/#/admin`
2. Use the credentials from agent registration:
   - Email: `pool@leadpulse.com`
   - Password: `pool123`

3. After login, you'll see:
   - Your referral code in the navigation bar
   - Only sessions assigned to you
   - Real-time chat interface

### 4. Test Referral Code System

#### Client with Referral Code:
```
http://localhost:5173/?ref_code=ABC12XYZ
```
Where `ABC12XYZ` is an agent's referral code. This client will be assigned ONLY to that agent.

#### Client without Referral Code:
```
http://localhost:5173/
```
This client will be automatically assigned to the default pool agent.

## API Endpoints

### Agent Endpoints

#### Register Agent
```http
POST /api/agents/register
Content-Type: application/json

{
  "email": "agent@example.com",
  "password": "password123",
  "name": "Agent Name",
  "is_default_pool": false
}
```

#### Login Agent
```http
POST /api/agents/login
Content-Type: application/json

{
  "email": "agent@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbG...",
  "token_type": "bearer",
  "agent": {
    "id": 1,
    "email": "agent@example.com",
    "name": "Agent Name",
    "referral_code": "ABC12XYZ",
    "is_default_pool": false,
    "created_at": "2026-01-30T..."
  }
}
```

#### Get Current Agent
```http
GET /api/agents/me
Authorization: Bearer <access_token>
```

### Session Endpoints (Updated)

#### List Sessions (Agent-Filtered)
```http
GET /api/sessions
Authorization: Bearer <access_token>
```

Returns only sessions assigned to the authenticated agent.

To get all sessions (admin view):
```http
GET /api/sessions?include_all=true
Authorization: Bearer <access_token>
```

#### Create Session with Referral Code
```http
POST /api/sessions
Content-Type: application/json

{
  "user_id": "unique-user-id",
  "user_name": "Client Name",
  "ad_source": "Facebook Ads",
  "referral_code": "ABC12XYZ",
  "lead_metadata": {
    "ip": "192.168.1.1",
    "browser": "Chrome",
    "ad_id": "fb-campaign-123"
  }
}
```

## URL Parameters for Client Links

### With Referral Code (Specific Agent):
```
/?ref_code=ABC12XYZ&ref=Facebook%20Ads&ad_id=campaign-001
```

### Without Referral Code (Default Pool):
```
/?ref=Google%20Search&ad_id=google-123
```

## How It Works

### 1. Client Arrives with Referral Code
```
User clicks: http://yoursite.com/?ref_code=ABC12XYZ
    ↓
Frontend extracts ref_code from URL
    ↓
Calls: POST /api/sessions with referral_code
    ↓
Backend looks up agent by referral_code
    ↓
Session.assigned_agent_id = agent.id
    ↓
Only that agent can see this session
```

### 2. Client Arrives WITHOUT Referral Code
```
User clicks: http://yoursite.com/
    ↓
Frontend calls: POST /api/sessions (no referral_code)
    ↓
Backend queries: SELECT * FROM agents WHERE is_default_pool = true
    ↓
Session.assigned_agent_id = default_agent.id
    ↓
Default pool agent sees this session
```

### 3. Agent Login & Session Filtering
```
Agent logs in at /admin
    ↓
Receives JWT token with agent_id
    ↓
Frontend calls: GET /api/sessions (with Authorization header)
    ↓
Backend filters: WHERE assigned_agent_id = current_agent.id
    ↓
Agent sees only their assigned sessions
```

## Database Schema

### New Tables & Columns

#### `agents` table:
```sql
id                  INTEGER PRIMARY KEY
email               VARCHAR UNIQUE
password_hash       VARCHAR
name                VARCHAR
referral_code       VARCHAR UNIQUE (8-char alphanumeric)
is_default_pool     BOOLEAN (only one can be true)
created_at          TIMESTAMP
```

#### `sessions` table (updated):
```sql
assigned_agent_id   INTEGER FOREIGN KEY → agents.id
```

#### `lead_metadata` table (updated):
```sql
agent_referral_code VARCHAR (stores the code used)
```

## Frontend Changes

### New Components
- **AgentLogin**: Login form at `/admin` route
- Logout button in navigation when authenticated
- Referral code display in agent nav

### New State Management
- `currentAgent`: Stores logged-in agent data
- `isAuthenticated`: Boolean flag for auth status
- Token stored in localStorage: `agent_token`

### Updated API Calls
- `createSession()` now accepts `referral_code` parameter
- `listSessions()` automatically includes JWT token if available
- All agent API functions: `loginAgent()`, `registerAgent()`, `getCurrentAgent()`

## Security Notes

1. **JWT Secret Key**: Change `JWT_SECRET_KEY` in `.env`:
   ```bash
   JWT_SECRET_KEY=your-super-secure-random-key-here
   ```

2. **Token Expiration**: Currently set to 7 days. Adjust in `backend/auth.py`:
   ```python
   ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
   ```

3. **Password Requirements**: Consider adding validation for stronger passwords

4. **HTTPS**: In production, ensure all API calls use HTTPS

## Testing Checklist

- [ ] Create default pool agent via API
- [ ] Create regular agent via API
- [ ] Login to `/admin` with agent credentials
- [ ] See agent name and referral code in nav
- [ ] Create client session WITHOUT ref_code → assigned to default agent
- [ ] Create client session WITH ref_code → assigned to specific agent
- [ ] Verify agent only sees their assigned sessions
- [ ] Test logout functionality
- [ ] Test token persistence (refresh page while logged in)

## Troubleshooting

### "Agent not found" error
- Ensure you created at least one agent via registration endpoint
- Check database: `SELECT * FROM agents;`

### Sessions not filtered by agent
- Verify JWT token is being sent: Check Network tab → Headers → Authorization
- Check backend logs for authentication errors

### No default agent found
- Ensure one agent has `is_default_pool = true`
- Run: `curl http://localhost:8000/api/agents/register` with `"is_default_pool": true`

### Token expired
- Login again - tokens expire after 7 days
- Or adjust `ACCESS_TOKEN_EXPIRE_MINUTES` in `backend/auth.py`

## Next Steps

1. **Admin Panel**: Add ability to view all agents and reassign sessions
2. **Agent Analytics**: Track sessions per agent, conversion rates
3. **Referral Links Generator**: UI for agents to generate tracking URLs
4. **Commission Tracking**: Link sessions to agent commissions
5. **Multi-tenant Support**: Separate agent organizations/teams
