#!/usr/bin/env python3
"""Create the message_templates table if it doesn't exist."""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://adconnect_user:adconnect_secure_password_123@localhost:5432/adconnect_db"
)

# Parse connection string
try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message_templates (
            id SERIAL NOT NULL PRIMARY KEY,
            text TEXT NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✓ message_templates table created successfully (or already existed)")
except Exception as e:
    print(f"✗ Error creating table: {e}")
    exit(1)
