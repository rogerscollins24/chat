# Overflow Management Implementation - Complete

## Overview
Implemented **Option C: Manual Super-Admin Reassignment** for handling agents exceeding 50 leads in 24 hours. Super admins can now view overloaded agents and manually reassign their recent sessions to other agents with audit logging.

## Features Implemented

### 1. Backend Endpoints (Python/FastAPI)

#### GET `/api/admin/agents/overflow`
- **Purpose**: Retrieve all agents with their 24-hour session counts
- **Query Logic**: 
  - Counts OPEN sessions created in the last 24 hours per agent
  - Flags agents with 50+ leads as "is_overflowed: true"
  - Sorts by session count (highest first)
- **Response**:
  ```json
  {
    "agents": [
      {
        "id": 1,
        "name": "John Agent",
        "email": "john@example.com",
        "role": "AGENT",
        "session_count_24h": 52,
        "is_overflowed": true
      }
    ],
    "overflow_threshold": 50
  }
  ```
- **Security**: Super-admin only (guarded by `super_admin_guard` dependency)

#### POST `/api/admin/reassign-sessions`
- **Purpose**: Bulk reassign open sessions from overloaded agent to target agent
- **Logic**:
  - Only reassigns OPEN sessions created in last 24 hours
  - Prevents reassigning to same agent
  - Verifies both agents exist
  - Commits all reassignments in single transaction
  - Notifies target agent via WebSocket if connected
  - Logs audit trail with super-admin email
- **Request Body**:
  ```json
  {
    "from_agent_id": 1,
    "to_agent_id": 2
  }
  ```
- **Response**:
  ```json
  {
    "status": "ok",
    "reassigned_count": 12,
    "from_agent": "John Agent",
    "to_agent": "Jane Agent"
  }
  ```
- **Security**: Super-admin only

### 2. Frontend API Functions (TypeScript)

#### `getOverflowAgents()`
- Fetches agents with their 24-hour session counts
- Returns `{ agents: OverflowAgent[]; overflow_threshold: 50 }`
- Type-safe interface: `OverflowAgent`

#### `reassignSessions(fromAgentId, toAgentId)`
- Posts reassignment request to backend
- Handles error responses with detailed messages
- Returns reassignment result with count

### 3. Super Admin Dashboard UI Updates

#### New Components
1. **Overflow Alert Panel** (Top of main content)
   - Shows all agents with `is_overflowed: true`
   - Displays session count in orange for visibility
   - "Reassign Overflow" button for each overloaded agent
   - Shows "No agents in overflow" when all are healthy

2. **Reassignment Modal**
   - Triggered when user clicks "Reassign Overflow"
   - Displays dropdown of available target agents (excludes source agent)
   - Shows current session count for each target agent
   - Confirmation warning: "All open sessions from the last 24 hours will be reassigned"
   - "Confirm Reassign" and "Cancel" buttons
   - Shows loading state during reassignment

#### State Management
- `overflowAgents`: Array of agents with 24h counts
- `reassignModal`: Modal state with from_agent info
- `selectedTargetAgent`: Target agent ID for reassignment
- `reassigning`: Loading flag during operation

#### Data Flow
1. Load button triggers `loadData()` which fetches 3 datasets in parallel:
   - Agents list
   - Sessions list
   - Overflow agents (with 24h counts)
2. Overflow agents filtered to show only `is_overflowed: true`
3. On reassignment: modal collects input → `handleReassignBulk()` → API call → reload data

## Technical Details

### Database Query Optimization
```python
# SQLAlchemy query counts sessions in last 24 hours
agents_with_counts = db.query(
    Agent.id,
    Agent.name,
    Agent.email,
    Agent.role,
    func.count(Session.id).label('session_count_24h')
).outerjoin(Session, Agent.id == Session.assigned_agent_id).filter(
    (Session.created_at >= yesterday) | (Session.created_at == None)
).group_by(Agent.id, Agent.name, Agent.email, Agent.role).all()
```
- Uses LEFT JOIN to include agents with 0 sessions
- Filters sessions by timestamp to last 24 hours
- Groups by agent to get count

### Audit Logging
- Backend logs every reassignment with format:
  ```
  Super admin john@example.com reassigned 12 sessions from agent agent1@example.com (1) to agent agent2@example.com (2)
  ```
- Includes: admin email, count, source agent info, target agent info

### WebSocket Notification
- When reassignment completes, target agent receives notification:
  ```json
  {
    "type": "sessions_reassigned",
    "data": {
      "reassigned_count": 12,
      "from_agent": "John Agent",
      "admin": "Super Admin Name"
    }
  }
  ```

## Security Considerations

1. **Super-Admin Guard**: All overflow endpoints require `super_admin_guard` dependency
   - Validates JWT token
   - Checks `agent.role == AgentRole.SUPER_ADMIN`
   - Rejects non-super-admin requests with 403 Forbidden

2. **Validation**:
   - Both agent IDs must exist (404 if not)
   - Cannot reassign to same agent
   - Only OPEN sessions affected

3. **Transaction Safety**:
   - All session updates in single `db.commit()`
   - Rollback on error with `db.rollback()`
   - No partial reassignments

## Testing Checklist

- [ ] **GET /api/admin/agents/overflow**
  - [ ] Returns all agents sorted by session count (descending)
  - [ ] Correctly counts 24h sessions
  - [ ] Flags agents with 50+ as overflowed
  - [ ] Returns 403 for non-super-admin

- [ ] **POST /api/admin/reassign-sessions**
  - [ ] Successfully reassigns sessions from agent A to B
  - [ ] Only affects OPEN sessions in last 24h
  - [ ] Rejects reassignment to same agent
  - [ ] Returns correct reassignment count
  - [ ] Logs audit trail
  - [ ] Sends WebSocket notification to target agent

- [ ] **Super Admin Dashboard UI**
  - [ ] Overflow panel shows only overflowed agents
  - [ ] Modal opens on "Reassign Overflow" click
  - [ ] Target agent dropdown excludes source agent
  - [ ] Confirmation succeeds and reloads data
  - [ ] Modal closes after successful reassignment
  - [ ] Error messages display on failure

## Example Usage Flow

1. Super admin logs into dashboard
2. Dashboard loads agents and shows overflow panel
3. Super admin sees "John Agent (52 sessions) - OVERFLOWED"
4. Super admin clicks "Reassign Overflow" button
5. Modal opens with dropdown of available agents
6. Super admin selects "Jane Agent" (currently 30 sessions)
7. Super admin clicks "Confirm Reassign"
8. Backend reassigns 52 sessions from John to Jane in last 24h window
9. Backend logs: "Super admin admin@example.com reassigned 52 sessions..."
10. Modal closes, dashboard reloads
11. Overflow panel now shows Jane Agent (82 sessions) as overflowed
12. John Agent no longer in overflow list (0 sessions in last 24h)

## Files Modified

1. **`backend/main.py`** (955 lines)
   - Added `GET /api/admin/agents/overflow` endpoint (lines 828-866)
   - Added `POST /api/admin/reassign-sessions` endpoint (lines 869-940)

2. **`src/services/api.ts`** (720 lines)
   - Added `OverflowAgent` interface (line 496-502)
   - Added `getOverflowAgents()` function (line 504-511)
   - Added `reassignSessions()` function (line 513-525)

3. **`components/SuperAdminDashboard.tsx`** (295 lines)
   - Updated imports to include new API functions
   - Added state for overflow management
   - Updated `loadData()` to fetch overflow agents
   - Added `handleReassignBulk()` function
   - Added overflow panel UI with alert styling
   - Added reassignment modal with target agent selector
   - Maintains existing agents and sessions panels

## Next Steps (Optional)

1. **Automatic Load Balancing**: Add background job to auto-distribute excess sessions
2. **Reassignment History**: Track all reassignments with timestamps and outcomes
3. **Agent Notifications**: Frontend alerts when agent is about to receive many reassigned sessions
4. **Custom Threshold**: Allow super-admin to configure overflow threshold (currently hardcoded at 50)
5. **Bulk Actions**: Allow reassigning from multiple agents at once
