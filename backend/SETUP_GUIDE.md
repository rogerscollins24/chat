# Backend Setup & Run Guide

## Prerequisites
- Python 3.8+
- PostgreSQL (or SQLite for development)
- Virtual Environment

## Installation & Setup

### 1. Create and Activate Virtual Environment
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic python-dotenv
```

### 3. Configure Environment Variables
```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your database configuration
# Example for local PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/leadpulse_db
```

### 4. Database Setup (PostgreSQL)

#### Option A: Using PostgreSQL
```sql
-- Create database
CREATE DATABASE leadpulse_db;

-- Create user (if not exists)
CREATE USER leadpulse_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE leadpulse_db TO leadpulse_user;
```

Then update your `.env`:
```
DATABASE_URL=postgresql://leadpulse_user:your_secure_password@localhost:5432/leadpulse_db
```

#### Option B: Using SQLite (Development)
For quick development testing, use SQLite:
```
DATABASE_URL=sqlite:///./leadpulse.db
```

Note: Modify `main.py` line 34:
```python
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
```

## Running the Backend

### Development Mode (with auto-reload)
```bash
# Make sure venv is activated
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing the API

### Health Check
```bash
curl http://localhost:8000/health
```

### Interactive API Documentation
Visit: http://localhost:8000/docs

### Create a Session
```bash
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "user_name": "John Doe",
    "ad_source": "google_ads",
    "user_avatar": "https://example.com/avatar.jpg",
    "metadata": {
      "ip": "192.168.1.1",
      "location": "New York",
      "browser": "Chrome",
      "ad_id": "ad_456"
    }
  }'
```

### Send a Message
```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "sender_id": "user123",
    "sender_role": "USER",
    "text": "Hello, I need help",
    "is_internal": false
  }'
```

### Get All Sessions
```bash
curl http://localhost:8000/api/sessions
```

### Get Session Messages
```bash
curl http://localhost:8000/api/sessions/1/messages
```

### Update Session Status
```bash
curl -X PATCH http://localhost:8000/api/sessions/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "RESOLVED"
  }'
```

## WebSocket Connection

Connect to WebSocket for real-time updates:
```
ws://localhost:8000/ws/{session_id}
```

### Example JavaScript:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/1');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

// Send message through WebSocket
ws.send(JSON.stringify({
  type: 'message',
  sender_id: 'user123',
  sender_role: 'USER',
  text: 'Hello from WebSocket'
}));
```

## Database Schema

### Sessions Table
- `id` (Primary Key)
- `user_id` (String, Unique)
- `user_name` (String)
- `user_avatar` (String, Optional)
- `ad_source` (String)
- `status` (Enum: OPEN/RESOLVED)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### Messages Table
- `id` (Primary Key)
- `session_id` (Foreign Key)
- `sender_id` (String)
- `sender_role` (Enum: USER/AGENT)
- `text` (Text)
- `is_internal` (Boolean)
- `timestamp` (DateTime)

### LeadMetadata Table
- `id` (Primary Key)
- `session_id` (Foreign Key, Unique)
- `ip` (String, Optional)
- `location` (String, Optional)
- `browser` (String, Optional)
- `ad_id` (String, Optional)

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql://user:password@localhost/dbname |
| ENVIRONMENT | Deployment environment | development \| production |
| LOG_LEVEL | Logging level | INFO \| DEBUG |

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running
- Verify DATABASE_URL in .env
- Check username and password

### Port Already in Use
```bash
# Use a different port
uvicorn main:app --reload --port 8001
```

### Virtual Environment Issues
```bash
# Deactivate and reactivate
deactivate
source venv/bin/activate
```

## Security Notes

⚠️ **Before Production:**
1. Set strong DATABASE_URL password
2. Use JWT authentication middleware
3. Implement CORS restrictions (specify allowed origins)
4. Enable HTTPS/WSS for production
5. Add rate limiting
6. Validate and sanitize all inputs
7. Use environment variables for secrets
8. Enable database backup strategy

## Next Steps

1. Set up PostgreSQL database
2. Configure `.env` file with database URL
3. Run `uvicorn main:app --reload`
4. Test API endpoints via /docs
5. Integrate frontend with API endpoints
