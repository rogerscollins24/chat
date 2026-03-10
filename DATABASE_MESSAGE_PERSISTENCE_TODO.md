# Database Message Persistence Implementation - TODO List

**Objective**: Save all messages to database so agents can see them across different webpages/tabs

**Status**: 🔵 Planning Phase

---

## Phase 1: Backend Database Model Updates

### Step 1.1: Verify Message Model Exists
- [ ] Open `backend/models.py`
- [ ] Check if `Message` class exists with fields: `id`, `session_id`, `content`, `sender_id`, `sender_type`, `timestamp`
- [ ] If missing, add Message model with proper SQLAlchemy mappings
- [ ] Verify Message has ForeignKey relationship to Session

**Expected Result**: Message table structure ready in database

---

## Phase 2: Backend API Endpoints

### Step 2.1: Add Message Save Endpoint
- [ ] Open `backend/main.py`
- [ ] Add `MessageCreate` Pydantic schema for request validation
- [ ] Add `MessageResponse` Pydantic schema for response
- [ ] Create `POST /api/messages` endpoint:
  - Accepts: `session_id`, `content`, `sender_id`, `sender_type`
  - Saves to database
  - Returns saved message with timestamp
  - Notifies connected agent via WebSocket

**Expected Result**: Messages can be posted and persisted to database

### Step 2.2: Add Message Retrieval Endpoints
- [ ] Add `GET /api/sessions/{session_id}/messages` endpoint:
  - Filters messages by session_id
  - Returns all messages for that session sorted by timestamp
  - Includes authentication check

**Expected Result**: Can fetch messages for specific session from database

### Step 2.3: Update Sessions Endpoint
- [ ] Modify `GET /api/sessions` to include messages array:
  - Each session returns list of messages from database
  - Messages ordered by timestamp (oldest first)
  - Include all message fields (id, content, sender_id, sender_type, timestamp)

**Expected Result**: Sessions endpoint returns complete message history

---

## Phase 3: Database Migration

### Step 3.1: Create Database Schema
- [ ] Delete old database file: `rm backend/leadpulse.db`
- [ ] Restart backend server to auto-create tables
- [ ] Verify `messages` table created with correct columns

**Expected Result**: Fresh database with messages table ready

---

## Phase 4: Frontend API Service Updates

### Step 4.1: Add Message API Functions
- [ ] Open `src/services/api.ts`
- [ ] Add `saveMessage()` function:
  - POST to `/api/messages`
  - Parameters: `sessionId`, `content`, `senderId`, `senderType`
  - Returns saved message object
  - Includes auth token in headers

- [ ] Add `getSessionMessages()` function:
  - GET from `/api/sessions/{sessionId}/messages`
  - Returns array of messages
  - Includes auth token in headers

**Expected Result**: Frontend has functions to save/retrieve messages

---

## Phase 5: Frontend UI Component Updates

### Step 5.1: Update App.tsx - Load Sessions with Messages
- [ ] Open `App.tsx`
- [ ] In the session loading effect:
  - Fetch `/api/sessions` endpoint
  - Store complete sessions WITH message arrays in state
  - No separate message fetch needed (messages included in response)

**Expected Result**: Sessions load with all messages from database

### Step 5.2: Update Message Send Handler
- [ ] Find message input component (where agents type messages)
- [ ] On send button click:
  - Call `api.saveMessage()` with all required fields
  - Wait for database response
  - Add returned message to UI
  - Update session messages array

**Expected Result**: Agent messages saved to database when sent

### Step 5.3: Remove localStorage Sync (Optional Cleanup)
- [ ] Consider removing localStorage sync code if using database
- [ ] Or keep as fallback for real-time updates
- [ ] Decision: **Keep it** for instant UI updates while database processes

**Expected Result**: Clean code without conflicting sync mechanisms

---

## Phase 6: Frontend - Client Side Message Handling

### Step 6.1: Update Client Chat Component
- [ ] Find where client sends messages (chat input on client portal)
- [ ] On send:
  - Call API endpoint to save message
  - Message saved with `sender_type: 'client'`
  - Wait for 201 response before clearing input

**Expected Result**: Client messages also persisted to database

---

## Phase 7: Testing

### Step 7.1: Test Message Persistence
- [ ] Start backend server: `cd backend && python main.py`
- [ ] Start frontend server: `npm run dev`
- [ ] Login as agent (john@leadpulse.com / password123)
- [ ] Send test message from agent side
- [ ] Verify message appears in UI
- [ ] Refresh page
- [ ] **VERIFY**: Message still visible (loaded from database)

**Expected Result**: ✅ Messages persist across page refreshes

### Step 7.2: Test Multi-Tab Sync via Database
- [ ] Open 2 tabs of agent dashboard (both logged in)
- [ ] Tab 1: Send message
- [ ] Tab 1: Verify message appears
- [ ] Tab 2: Refresh page OR wait 30 seconds
- [ ] **VERIFY**: Tab 2 shows message from database

**Expected Result**: ✅ Messages visible across multiple tabs via database

### Step 7.3: Test Client to Agent Flow
- [ ] Create new session by visiting: `http://localhost:5173/?ref_code=NX42DDF3`
- [ ] Send message as client
- [ ] Check database that message saved: `SELECT * FROM messages;`
- [ ] Login as agent
- [ ] **VERIFY**: Client message appears in agent dashboard

**Expected Result**: ✅ Client messages persisted and visible to agent

### Step 7.4: Test Multiple Sessions
- [ ] Create 3 different chat sessions
- [ ] Send 2-3 messages in each session
- [ ] Verify each session shows correct messages
- [ ] Cross-session messages don't leak

**Expected Result**: ✅ Message filtering by session_id works correctly

---

## Phase 8: Verification & Cleanup

### Step 8.1: Database Verification
- [ ] Open database viewer (SQLite browser or `sqlite3 leadpulse.db`)
- [ ] Query: `SELECT * FROM messages;`
- [ ] Verify:
  - All sent messages present
  - Correct session_id foreign keys
  - Timestamps accurate
  - Content preserved exactly

**Expected Result**: ✅ All messages in database are correct

### Step 8.2: API Response Verification
- [ ] Test endpoint with curl:
  ```bash
  curl -X GET "http://localhost:8000/api/sessions" \
    -H 'Authorization: Bearer <token>' | jq '.[0].messages'
  ```
- [ ] Verify messages array returned
- [ ] Verify all required fields present

**Expected Result**: ✅ API returns complete message data

### Step 8.3: Performance Check
- [ ] Measure message send latency (should be < 500ms)
- [ ] Measure session load time with 20+ messages (should be < 1 second)
- [ ] Check no console errors

**Expected Result**: ✅ Performance acceptable

---

## Phase 9: Documentation Updates

### Step 9.1: Update IMPLEMENTATION_DOCUMENTATION.md
- [ ] Add section: "Message Persistence"
- [ ] Document database schema changes
- [ ] Document new API endpoints
- [ ] Update architecture diagram if needed

**Expected Result**: ✅ Documentation reflects new implementation

---

## Final Checklist

### Before Marking Complete
- [ ] All messages persist to database ✅
- [ ] Messages load from database on page refresh ✅
- [ ] Multi-tab sync works via database ✅
- [ ] Client messages visible to agent ✅
- [ ] Agent messages visible to client ✅
- [ ] No errors in browser console ✅
- [ ] No errors in backend logs ✅
- [ ] Database integrity verified ✅
- [ ] Documentation updated ✅

---

## Rollback Plan (If Issues Arise)

If problems occur:
1. Stop both servers
2. Delete database: `rm backend/leadpulse.db`
3. Revert API changes in `backend/main.py`
4. Revert UI changes in `App.tsx`
5. Restart servers
6. Test with previous implementation

---

## Estimated Time

- **Backend changes**: 15-20 minutes
- **Frontend changes**: 20-25 minutes
- **Testing**: 15-20 minutes
- **Documentation**: 10 minutes
- **Total**: ~60-75 minutes

---

## Implementation Order

Execute in this sequence:
1. ✅ Phase 1: Model verification
2. ✅ Phase 2: Backend endpoints
3. ✅ Phase 3: Database migration
4. ✅ Phase 4: API service functions
5. ✅ Phase 5: App.tsx updates
6. ✅ Phase 6: Client component updates
7. ✅ Phase 7: Testing all scenarios
8. ✅ Phase 8: Verification
9. ✅ Phase 9: Documentation

---

**Created**: January 31, 2026  
**Priority**: High - Critical for multi-tab message sync  
**Owner**: Development Team
