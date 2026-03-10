#!/usr/bin/env python3
"""
Pre-deployment database initialization script
Ensures all tables exist before the app starts
Run via: preDeployCommand in render.yaml
"""

import os
from sqlalchemy import create_engine
from models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize database tables"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            logger.warning("⚠️  DATABASE_URL not set, skipping pre-deploy init")
            return 0
        
        logger.info(f"Initializing database...")
        engine = create_engine(database_url, echo=False)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database initialized successfully")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = init_db()
    sys.exit(exit_code)
