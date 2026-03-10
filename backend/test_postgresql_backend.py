#!/usr/bin/env python3
"""
PostgreSQL Backend Test Suite
Tests the FastAPI backend with PostgreSQL integration
"""

import requests
import json
import time
import sys

# API Configuration
API_URL = "http://localhost:8001"
TIMEOUT = 5

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️  {text}{RESET}")

def test_api_health():
    """Test if API is responding"""
    print_header("TEST 1: API Health Check")
    try:
        response = requests.get(f"{API_URL}/docs", timeout=TIMEOUT)
        if response.status_code == 200:
            print_success("API is running and responding")
            return True
        else:
            print_error(f"API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {API_URL}")
        print_info("Make sure backend is running: uvicorn main:app --port 8001")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_get_agents():
    """Test getting agents from PostgreSQL"""
    print_header("TEST 2: Get Agents from PostgreSQL")
    try:
        response = requests.get(f"{API_URL}/api/agents", timeout=TIMEOUT)
        if response.status_code == 200:
            agents = response.json()
            print_success(f"Retrieved {len(agents)} agents")
            for agent in agents:
                print_info(f"  - {agent.get('name')} ({agent.get('email')})")
            return True
        else:
            print_error(f"Failed to get agents: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_agent_login():
    """Test agent login"""
    print_header("TEST 3: Agent Login")
    try:
        # Use credentials for agent created in migration
        credentials = {
            "email": "john@leadpulse.com",
            "password": "password123"
        }
        response = requests.post(
            f"{API_URL}/api/agents/login",
            json=credentials,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print_success(f"Agent login successful")
            print_info(f"Token received: {token[:20]}...")
            return token
        else:
            print_error(f"Login failed: {response.status_code}")
            print_info(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None

def test_get_sessions(token):
    """Test getting sessions with authentication"""
    print_header("TEST 4: Get Sessions")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_URL}/api/sessions",
            headers=headers,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            sessions = response.json()
            print_success(f"Retrieved {len(sessions)} sessions")
            for session in sessions:
                print_info(f"  - Session {session.get('id')}: User {session.get('user_name')} (Status: {session.get('status')})")
            return True
        else:
            print_error(f"Failed to get sessions: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_create_session(token):
    """Test creating a new session"""
    print_header("TEST 5: Create New Session")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        session_data = {
            "user_id": f"test_user_{int(time.time())}",
            "user_name": "Test User",
            "user_avatar": "https://via.placeholder.com/150",
            "ad_source": "google"
        }
        response = requests.post(
            f"{API_URL}/api/sessions",
            json=session_data,
            headers=headers,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            session = response.json()
            session_id = session.get("id")
            print_success(f"Session created with ID: {session_id}")
            print_info(f"  - User: {session.get('user_name')}")
            print_info(f"  - Status: {session.get('status')}")
            return session_id
        else:
            print_error(f"Failed to create session: {response.status_code}")
            print_info(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None

def test_send_message(session_id, token):
    """Test sending a message"""
    print_header("TEST 6: Send Message to Session")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        message_data = {
            "session_id": session_id,
            "sender_id": "test_sender",
            "sender_role": "USER",
            "text": "Hello, this is a test message from PostgreSQL!",
            "is_internal": False
        }
        response = requests.post(
            f"{API_URL}/api/messages",
            json=message_data,
            headers=headers,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            message = response.json()
            print_success(f"Message sent with ID: {message.get('id')}")
            print_info(f"  - Text: {message.get('text')}")
            print_info(f"  - Sender: {message.get('sender_role')}")
            print_info(f"  - Timestamp: {message.get('timestamp')}")
            return True
        else:
            print_error(f"Failed to send message: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_get_messages(session_id, token):
    """Test retrieving messages from a session"""
    print_header("TEST 7: Get Messages from Session")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_URL}/api/sessions/{session_id}/messages",
            headers=headers,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            messages = response.json()
            print_success(f"Retrieved {len(messages)} messages")
            for msg in messages:
                print_info(f"  - {msg.get('sender_role')}: {msg.get('text')[:50]}...")
            return True
        else:
            print_error(f"Failed to get messages: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print_header("PostgreSQL Backend Integration Tests")
    
    test_results = []
    
    # Test 1: API Health
    if not test_api_health():
        print_error("Cannot continue - backend is not running")
        return False
    test_results.append(True)
    
    # Test 2: Get Agents
    test_results.append(test_get_agents())
    
    # Test 3: Agent Login
    token = test_agent_login()
    test_results.append(token is not None)
    
    if token:
        # Test 4: Get Sessions
        test_results.append(test_get_sessions(token))
        
        # Test 5: Create Session
        session_id = test_create_session(token)
        test_results.append(session_id is not None)
        
        if session_id:
            # Test 6: Send Message
            test_results.append(test_send_message(session_id, token))
            
            # Test 7: Get Messages
            test_results.append(test_get_messages(session_id, token))
    
    # Summary
    print_header("Test Summary")
    passed = sum(test_results)
    total = len(test_results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print_info(f"Tests Passed: {passed}/{total} ({percentage:.0f}%)")
    
    if passed == total:
        print_success("All tests passed! PostgreSQL integration is working correctly.")
        return True
    else:
        print_warning(f"{total - passed} test(s) failed. Check the output above.")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
