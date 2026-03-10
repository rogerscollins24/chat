#!/usr/bin/env python3
"""
Super Admin Creation Script for Render Deployment
This script adds or verifies a super admin user in the database.
Usage: python create_super_admin.py [email] [password] [name]
"""

import os
import sys
import secrets
import string
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Agent, AgentRole
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_referral_code() -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(8))

def create_super_admin(email=None, password=None, name=None):
    """Create a super admin user in the database"""
    
    # Default credentials for initial setup (can be overridden via args/env)
    email = email or os.getenv("SUPER_ADMIN_EMAIL") or "admin@leadpulse.com"
    password = password or os.getenv("SUPER_ADMIN_PASSWORD") or "Admin123456"
    name = name or os.getenv("SUPER_ADMIN_NAME") or "Super Admin"
    
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ Error: DATABASE_URL environment variable not set")
            return 1
        
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print(f"Connecting to database...")
        print(f"Creating/verifying super admin: {email}")
        
        # Check if configured admin already exists
        existing = db.query(Agent).filter(Agent.email == email).first()
        if existing:
            changed = False
            existing_role = getattr(existing, "role", None)
            existing_role_value = getattr(existing_role, "value", existing_role)
            if existing_role_value != AgentRole.SUPER_ADMIN.value:
                setattr(existing, "role", AgentRole.SUPER_ADMIN)
                changed = True
            existing_password_hash = getattr(existing, "password_hash", None)
            if not existing_password_hash:
                setattr(existing, "password_hash", get_password_hash(password))
                changed = True
            if changed:
                db.commit()
            print(f"✅ Super admin already exists:")
            print(f"   Email: {existing.email}")
            print(f"   Name: {existing.name}")
            print(f"   Referral Code: {existing.referral_code}")
            print(f"   Role: {existing.role}")
            if changed:
                print("   Updated existing account to ensure SUPER_ADMIN access")
            db.close()
            return 0
        
        # Create new super admin
        super_admin = Agent(
            email=email,
            password_hash=get_password_hash(password),
            name=name,
            referral_code=generate_referral_code(),
            is_default_pool=False,
            role=AgentRole.SUPER_ADMIN
        )
        db.add(super_admin)
        db.commit()
        
        print(f"✅ Super admin created successfully!")
        print(f"   Email: {super_admin.email}")
        print(f"   Name: {super_admin.name}")
        print(f"   Referral Code: {super_admin.referral_code}")
        print(f"   Role: {super_admin.role}")
        print(f"\n⚠️  Login credentials (change password after first login):")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        print(f"\n   Access super admin dashboard at: /admin/super-admin")
        
        db.close()
        return 0
        
    except Exception as e:
        print(f"❌ Error creating super admin: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else None
    password = sys.argv[2] if len(sys.argv) > 2 else None
    name = sys.argv[3] if len(sys.argv) > 3 else None
    
    exit_code = create_super_admin(email, password, name)
    sys.exit(exit_code)
