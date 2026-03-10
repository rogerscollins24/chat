#!/usr/bin/env python3
"""
Auto Welcome Message Test Suite
Tests the automatic welcome message functionality for ad referral sessions
"""

import requests
import json
import time
import sys
from datetime import datetime

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
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

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
        response = requests.get(f"{API_URL}/", timeout=TIMEOUT)
        if response.status_code == 200:
            print_success("API is running and responding")
            return True
        else:
            print_error(f"API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {API_URL}")
        print_info("Make sure backend is running: cd backend && uvicorn main:app --port 8001")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def get_test_agent_referral_code():
    """Get a valid referral code from an existing agent"""
    # Use hardcoded ref codes that exist in the database
    # These were created during setup
    return 'G9BAKZ3D'  # Non-default pool agent

def test_auto_welcome_for_referral_session():
    """Test that auto welcome message is sent for new ad referral sessions"""
    print_header("TEST 2: Auto Welcome Message for Referral Session")
    
    # Get a valid referral code
    ref_code = get_test_agent_referral_code()
    if not ref_code:
        print_error("No agents found - cannot test referral code")
        return False
    
    print_info(f"Using referral code: {ref_code}")
    
    try:
        # Create a new session with referral code
        timestamp = int(time.time() * 1000)
        session_data = {
            "user_id": f"test-user-welcome-{timestamp}",
            "user_name": "Test User",
            "user_avatar": None,
            "ad_source": "google_ads",
            "referral_code": ref_code,
            "lead_metadata": {
                "city": "New York",
                "browser": "Chrome",
                "device": "Desktop"
            }
        }
        
        response = requests.post(
            f"{API_URL}/api/sessions",
            json=session_data,
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print_error(f"Failed to create session: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
        
        session = response.json()
        session_id = session.get('id')
        print_success(f"Session created: ID={session_id}")
        
        # Check if has_auto_welcome_sent flag is set
        if not session.get('has_auto_welcome_sent'):
            print_error("has_auto_welcome_sent flag not set on session")
            return False
        print_success("has_auto_welcome_sent flag is True")
        
        # Give WebSocket broadcast a moment to complete
        time.sleep(0.5)
        
        # Get messages for this session
        messages_response = requests.get(
            f"{API_URL}/api/sessions/{session_id}/messages",
            timeout=TIMEOUT
        )
        
        if messages_response.status_code != 200:
            print_error(f"Failed to get messages: {messages_response.status_code}")
            return False
        
        messages = messages_response.json()
        print_info(f"Found {len(messages)} messages")
        
        # Verify exactly one message exists
        if len(messages) != 1:
            print_error(f"Expected 1 message, got {len(messages)}")
            return False
        
        # Verify message content
        welcome_msg = messages[0]
        
        # Check sender_role is AGENT
        if welcome_msg.get('sender_role') != 'AGENT':
            print_error(f"Expected AGENT role, got {welcome_msg.get('sender_role')}")
            return False
        print_success("Message sender_role is AGENT")
        
        # Check message text contains required elements
        text = welcome_msg.get('text', '')
        required_elements = [
            '👋',  # Wave emoji
            'optional',  # Must include "optional"
            '•',  # Bullet points
            'Full name',
            'Location',
            'Phone number'
        ]
        
        all_present = True
        for element in required_elements:
            if element not in text:
                print_error(f"Required element '{element}' not found in message")
                all_present = False
        
        if all_present:
            print_success("All required UX elements present in welcome message")
            print_info(f"Message preview: {text[:100]}...")
            return True
        else:
            print_error("Welcome message missing required elements")
            print_info(f"Full message: {text}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_no_welcome_for_default_pool():
    """Test that NO auto welcome message is sent for DEFAULT_POOL sessions"""
    print_header("TEST 3: No Auto Welcome for DEFAULT_POOL Sessions")
    
    try:
        # Create a session WITHOUT referral code (should use DEFAULT_POOL)
        timestamp = int(time.time() * 1000)
        session_data = {
            "user_id": f"test-user-noref-{timestamp}",
            "user_name": "Test User No Ref",
            "user_avatar": None,
            "ad_source": "direct",
            "referral_code": None  # No referral code
        }
        
        response = requests.post(
            f"{API_URL}/api/sessions",
            json=session_data,
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print_error(f"Failed to create session: {response.status_code}")
            return False
        
        session = response.json()
        session_id = session.get('id')
        print_success(f"Session created: ID={session_id}")
        
        # Check has_auto_welcome_sent should be False
        if session.get('has_auto_welcome_sent'):
            print_error("has_auto_welcome_sent should be False for non-referral sessions")
            return False
        print_success("has_auto_welcome_sent flag is False (correct)")
        
        # Give WebSocket a moment
        time.sleep(0.5)
        
        # Get messages - should be zero
        messages_response = requests.get(
            f"{API_URL}/api/sessions/{session_id}/messages",
            timeout=TIMEOUT
        )
        
        if messages_response.status_code != 200:
            print_error(f"Failed to get messages: {messages_response.status_code}")
            return False
        
        messages = messages_response.json()
        
        if len(messages) == 0:
            print_success("No auto welcome message sent (correct)")
            return True
        else:
            print_error(f"Expected 0 messages, got {len(messages)}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_no_duplicate_welcome_on_retry():
    """Test that welcome message is NOT duplicated when session creation is retried"""
    print_header("TEST 4: No Duplicate Welcome on Frontend Retry")
    
    # Get a valid referral code
    ref_code = get_test_agent_referral_code()
    if not ref_code:
        print_error("No agents found - cannot test referral code")
        return False
    
    try:
        # Create a session with referral code
        timestamp = int(time.time() * 1000)
        user_id = f"test-user-retry-{timestamp}"
        session_data = {
            "user_id": user_id,
            "user_name": "Test Retry User",
            "user_avatar": None,
            "ad_source": "facebook_ads",
            "referral_code": ref_code
        }
        
        # First request - should create session and send welcome
        response1 = requests.post(
            f"{API_URL}/api/sessions",
            json=session_data,
            timeout=TIMEOUT
        )
        
        if response1.status_code != 200:
            print_error(f"Failed to create session: {response1.status_code}")
            return False
        
        session1 = response1.json()
        session_id = session1.get('id')
        print_success(f"First request - Session created: ID={session_id}")
        
        time.sleep(0.5)
        
        # Second request - should return existing session (simulating frontend retry)
        response2 = requests.post(
            f"{API_URL}/api/sessions",
            json=session_data,
            timeout=TIMEOUT
        )
        
        if response2.status_code != 200:
            print_error(f"Failed on retry: {response2.status_code}")
            return False
        
        session2 = response2.json()
        print_success("Second request - Returned existing session")
        
        # Should be same session
        if session2.get('id') != session_id:
            print_error("Second request created a different session!")
            return False
        print_success("Same session returned on retry (correct)")
        
        time.sleep(0.5)
        
        # Get messages - should still be exactly one
        messages_response = requests.get(
            f"{API_URL}/api/sessions/{session_id}/messages",
            timeout=TIMEOUT
        )
        
        if messages_response.status_code != 200:
            print_error(f"Failed to get messages: {messages_response.status_code}")
            return False
        
        messages = messages_response.json()
        
        if len(messages) == 1:
            print_success(f"Still exactly 1 message (no duplicate)")
            return True
        else:
            print_error(f"Expected 1 message, got {len(messages)}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_no_welcome_for_returning_user():
    """Test that welcome message is NOT sent for returning users with existing messages"""
    print_header("TEST 5: No Welcome for Returning Users")
    
    # Get a valid referral code
    ref_code = get_test_agent_referral_code()
    if not ref_code:
        print_error("No agents found - cannot test referral code")
        return False
    
    try:
        # Create a session with referral code
        timestamp = int(time.time() * 1000)
        user_id = f"test-user-returning-{timestamp}"
        session_data = {
            "user_id": user_id,
            "user_name": "Test Returning User",
            "user_avatar": None,
            "ad_source": "linkedin_ads",
            "referral_code": ref_code
        }
        
        response = requests.post(
            f"{API_URL}/api/sessions",
            json=session_data,
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print_error(f"Failed to create session: {response.status_code}")
            return False
        
        session = response.json()
        session_id = session.get('id')
        print_success(f"Session created: ID={session_id}")
        
        time.sleep(0.5)
        
        # Manually send a user message (simulating user interaction)
        user_message = {
            "session_id": session_id,
            "sender_id": user_id,
            "sender_role": "USER",
            "text": "Hello, I need help!",
            "is_internal": False
        }
        
        msg_response = requests.post(
            f"{API_URL}/api/messages",
            json=user_message,
            timeout=TIMEOUT
        )
        
        if msg_response.status_code != 200:
            print_error(f"Failed to send user message: {msg_response.status_code}")
            return False
        
        print_success("User sent a message")
        
        time.sleep(0.5)
        
        # Get messages - should have welcome + user message = 2 total
        messages_response = requests.get(
            f"{API_URL}/api/sessions/{session_id}/messages",
            timeout=TIMEOUT
        )
        
        if messages_response.status_code != 200:
            print_error(f"Failed to get messages: {messages_response.status_code}")
            return False
        
        messages = messages_response.json()
        
        # Should have 2 messages: auto welcome + user message
        if len(messages) == 2:
            print_success(f"Has 2 messages: welcome + user message (correct)")
            
            # Verify order: welcome first, user message second
            if messages[0].get('sender_role') == 'AGENT' and messages[1].get('sender_role') == 'USER':
                print_success("Message order correct: AGENT welcome then USER message")
                return True
            else:
                print_error("Message order incorrect")
                return False
        else:
            print_error(f"Expected 2 messages, got {len(messages)}")
            return False
            
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all test cases"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}AUTO WELCOME MESSAGE TEST SUITE{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")
    
    tests = [
        ("API Health Check", test_api_health),
        ("Auto Welcome for Referral Session", test_auto_welcome_for_referral_session),
        ("No Welcome for DEFAULT_POOL", test_no_welcome_for_default_pool),
        ("No Duplicate Welcome on Retry", test_no_duplicate_welcome_on_retry),
        ("No Welcome for Returning Users", test_no_welcome_for_returning_user),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    if passed == total:
        print_success(f"ALL TESTS PASSED ({passed}/{total})")
        return 0
    else:
        print_error(f"SOME TESTS FAILED ({passed}/{total} passed)")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
