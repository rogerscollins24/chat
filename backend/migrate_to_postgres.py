#!/usr/bin/env python3
"""
Migration script to set up PostgreSQL database with all tables
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base, Agent, Session, Message, LeadMetadata
from auth import get_password_hash, generate_referral_code
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://adconnect_user:adconnect_secure_password_123@localhost:5432/adconnect_db"
)

def migrate():
    """Create all tables and seed initial data"""
    
    print("🔄 Connecting to PostgreSQL...")
    engine = create_engine(DATABASE_URL)
    
    # Test connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()
            print(f"✅ Connected to PostgreSQL: {version[0][:50]}...")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return
    
    print("📦 Creating all tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return
    
    # Create session for seeding data
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if agents already exist
        existing_agents = db.query(Agent).count()
        if existing_agents > 0:
            print(f"⏭️  Skipping seed data - {existing_agents} agents already exist")
            return
        
        # Seed initial agents
        print("👤 Creating default agents...")
        
        john_code = generate_referral_code()
        john = Agent(
            email="john@leadpulse.com",
            password_hash=get_password_hash("password123"),
            name="John Smith",
            referral_code=john_code,
            is_default_pool=False,
            created_at=datetime.utcnow()
        )
        db.add(john)
        
        pool_code = generate_referral_code()
        pool_agent = Agent(
            email="pool@leadpulse.com",
            password_hash=get_password_hash("password123"),
            name="Pool Agent",
            referral_code=pool_code,
            is_default_pool=True,
            created_at=datetime.utcnow()
        )
        db.add(pool_agent)
        
        db.commit()
        print(f"✅ Agents created!")
        print(f"   - John Smith (referral code: {john_code})")
        print(f"   - Pool Agent (referral code: {pool_code})")
        
        # Create sample session
        print("💬 Creating sample session...")
        session = Session(
            user_id="test-user-1",
            user_name="Test Client",
            ad_source="test_migration",
            assigned_agent_id=john.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(session)
        db.commit()
        print(f"✅ Sample session created (ID: {session.id})")
        
        # Add sample metadata
        metadata = LeadMetadata(
            session_id=session.id,
            agent_referral_code=john_code,
            browser="Chrome"
        )
        db.add(metadata)
        db.commit()
        print(f"✅ Session metadata created")
        
        # Add sample messages
        print("💬 Adding sample messages...")
        messages = [
            Message(
                session_id=session.id,
                sender_id="test-user-1",
                sender_role="USER",
                text="Hello, I need help with my order",
                is_internal=False,
                timestamp=datetime.utcnow()
            ),
            Message(
                session_id=session.id,
                sender_id="john",
                sender_role="AGENT",
                text="Hi! I'm happy to help. What can I assist you with?",
                is_internal=False,
                timestamp=datetime.utcnow()
            )
        ]
        db.add_all(messages)
        db.commit()
        print(f"✅ Sample messages added ({len(messages)} messages)")
        
        # Show summary
        agent_count = db.query(Agent).count()
        session_count = db.query(Session).count()
        message_count = db.query(Message).count()
        
        print("\n✨ PostgreSQL migration completed successfully!")
        print("\n📊 Database Summary:")
        print(f"   - Agents: {agent_count}")
        print(f"   - Sessions: {session_count}")
        print(f"   - Messages: {message_count}")
        
    except Exception as e:
        print(f"❌ Error during migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
