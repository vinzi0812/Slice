#!/usr/bin/env python3
"""
Database initialization script for Supabase.
Run this once to create all tables in your Supabase database.
"""

from app.db.database import engine, Base

def create_tables():
    """Create all tables in the database"""
    print("Creating tables in Supabase database...")
    Base.metadata.create_all(bind=engine)
    print("✅ All tables created successfully!")

if __name__ == "__main__":
    create_tables()
