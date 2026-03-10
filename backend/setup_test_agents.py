#!/usr/bin/env python3
"""Setup test agents for testing"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Agent, AgentRole
from auth import get_password_hash, generate_referral_code
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://adconnect_user:adconnect_secure_password_123@localhost:5432/adconnect_db')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # Check if agents exist
    agents = db.query(Agent).all()
    print(f'ℹ️  Found {len(agents)} agents in database')
    
    # Create test agents if none exist
    if len(agents) == 0:
        test_agent = Agent(
            email='test@agent.com',
            password_hash=get_password_hash('Test1234'),
            name='Test Agent',
            referral_code='TEST123',
            is_default_pool=False,
            role=AgentRole.AGENT
        )
        db.add(test_agent)
        
        default_agent = Agent(
            email='default@agent.com',
            password_hash=get_password_hash('Default1234'),
            name='Default Pool Agent',
            referral_code='DEFAULT',
            is_default_pool=True,
            role=AgentRole.AGENT
        )
        db.add(default_agent)
        
        db.commit()
        print('✅ Created test agents:')
        print('  - Test Agent (test@agent.com) - Code: TEST123')
        print('  - Default Pool Agent (default@agent.com) - Code: DEFAULT (default pool)')
    else:
        print('Existing agents:')
        for agent in agents:
            print(f'  - {agent.name} ({agent.email}) - Code: {agent.referral_code} - Default: {agent.is_default_pool}')
finally:
    db.close()
