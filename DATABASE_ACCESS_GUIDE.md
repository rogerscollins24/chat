# 📊 Database Access & Management Guide

## Your Database is Ready!

**Database Name:** `leadpulse_db`
**User:** `leadpulse_user`
**Password:** `leadpulse_password`
**Host:** `localhost`
**Port:** `5432`

---

## ✅ Running Backend Server

Your FastAPI backend is currently running on:
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

To start/stop the server:
```bash
cd backend
/Users/admin/adconnect-chat-hub/backend/venv/bin/python -m uvicorn main:app --reload
```

---

## 🗄️ View Database - Method 1: psql CLI (Recommended for quick checks)

### Connect to database
```bash
psql -U leadpulse_user -d leadpulse_db -h localhost
```

### List all tables
```sql
\dt
```

### View Sessions table
```sql
SELECT * FROM sessions;
```

### View Messages table
```sql
SELECT * FROM messages;
```

### View Metadata table
```sql
SELECT * FROM lead_metadata;
```

### View table structure
```sql
\d sessions
\d messages
\d lead_metadata
```

### Count rows in each table
```sql
SELECT COUNT(*) as session_count FROM sessions;
SELECT COUNT(*) as message_count FROM messages;
SELECT COUNT(*) as metadata_count FROM lead_metadata;
```

### Exit psql
```sql
\q
```

---

## 🗄️ View Database - Method 2: pgAdmin (GUI - Install if you want)

pgAdmin is a web-based PostgreSQL management tool.

### Install pgAdmin (optional)
```bash
brew install pgadmin4
```

Then access it at: http://localhost:5050

### Quick Connection in pgAdmin:
1. Create new server
2. **Name:** LeadPulse
3. **Host:** localhost
4. **Port:** 5432
5. **Database:** leadpulse_db
6. **Username:** leadpulse_user
7. **Password:** leadpulse_password

---

## 🗄️ View Database - Method 3: DBeaver (Desktop App)

DBeaver is a powerful database IDE.

### Download
https://dbeaver.io/download/

### Connection Settings:
- **Database:** PostgreSQL
- **Server Host:** localhost
- **Port:** 5432
- **Database:** leadpulse_db
- **Username:** leadpulse_user
- **Password:** leadpulse_password

---

## 🗄️ View Database - Method 4: VS Code Extension

### Install Extension
Search for "PostgreSQL" in VS Code extensions, install "PostgreSQL" by Chris Kolkman

### Add Connection
1. Open Command Palette (Cmd+Shift+P)
2. Type "PostgreSQL: Add Connection"
3. Configure with credentials above

---

## 📊 Database Schema

### Sessions Table
```sql
CREATE TABLE sessions (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR UNIQUE NOT NULL,
  user_name VARCHAR NOT NULL,
  user_avatar VARCHAR,
  ad_source VARCHAR NOT NULL,
  status sessionstatus DEFAULT 'OPEN',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Messages Table
```sql
CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  session_id INTEGER REFERENCES sessions(id),
  sender_id VARCHAR NOT NULL,
  sender_role senderrole NOT NULL,
  text TEXT NOT NULL,
  is_internal BOOLEAN DEFAULT FALSE,
  timestamp TIMESTAMP DEFAULT NOW()
);
```

### LeadMetadata Table
```sql
CREATE TABLE lead_metadata (
  id SERIAL PRIMARY KEY,
  session_id INTEGER UNIQUE REFERENCES sessions(id),
  ip VARCHAR,
  location VARCHAR,
  browser VARCHAR,
  ad_id VARCHAR
);
```

---

## 🧪 Test the API

### 1. Open Interactive Docs
```
http://localhost:8000/docs
```

### 2. Create a Session (in terminal)
```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "user_name": "John Doe",
    "ad_source": "google_ads",
    "lead_metadata": {
      "ip": "192.168.1.1",
      "location": "New York",
      "browser": "Chrome",
      "ad_id": "ad_456"
    }
  }'
```

### 3. Send a Message
```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "sender_id": "user123",
    "sender_role": "USER",
    "text": "Hello, I need help!"
  }'
```

### 4. Get All Sessions
```bash
curl http://localhost:8000/api/sessions | jq .
```

### 5. Get Session Details
```bash
curl http://localhost:8000/api/sessions/1 | jq .
```

---

## 🔍 Quick Database Inspection

### Check database connection
```bash
psql -U leadpulse_user -d leadpulse_db -c "SELECT 1;"
```

### List all databases
```bash
psql -U leadpulse_user -c "\l"
```

### Check table stats
```bash
psql -U leadpulse_user -d leadpulse_db << 'EOF'
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
EOF
```

---

## ⚡ Useful psql Commands

| Command | Purpose |
|---------|---------|
| `\l` | List all databases |
| `\c dbname` | Connect to database |
| `\dt` | List tables |
| `\d tablename` | Describe table |
| `\du` | List users/roles |
| `\dp` | List permissions |
| `\q` | Quit |
| `SELECT * FROM table LIMIT 10;` | View first 10 rows |

---

## 🛠️ Reset Database (if needed)

Drop and recreate:
```bash
psql postgres << 'EOF'
DROP DATABASE IF EXISTS leadpulse_db;
CREATE DATABASE leadpulse_db OWNER leadpulse_user;

\c leadpulse_db

GRANT CONNECT ON DATABASE leadpulse_db TO leadpulse_user;
GRANT USAGE ON SCHEMA public TO leadpulse_user;
GRANT CREATE ON SCHEMA public TO leadpulse_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO leadpulse_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO leadpulse_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO leadpulse_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TYPES TO leadpulse_user;
EOF
```

Then restart the backend server to recreate tables.

---

## 📝 Example Query to Check Data

```bash
psql -U leadpulse_user -d leadpulse_db << 'EOF'
-- Count records
SELECT 'sessions' as table_name, COUNT(*) as row_count FROM sessions
UNION
SELECT 'messages', COUNT(*) FROM messages
UNION
SELECT 'lead_metadata', COUNT(*) FROM lead_metadata;

-- View sessions with related data
SELECT 
  s.id,
  s.user_name,
  s.ad_source,
  s.status,
  COUNT(m.id) as message_count
FROM sessions s
LEFT JOIN messages m ON s.id = m.session_id
GROUP BY s.id, s.user_name, s.ad_source, s.status;
EOF
```

---

## 🎯 Next Steps

1. ✅ Database is set up and ready
2. ✅ Backend server is running on `http://localhost:8000`
3. ⏭️ Test API endpoints at `http://localhost:8000/docs`
4. ⏭️ View data using one of the methods above
5. ⏭️ Create test sessions and messages via the API
6. ⏭️ Integrate frontend with the API

Happy coding! 🚀
