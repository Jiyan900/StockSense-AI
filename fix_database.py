import os
import sys
from sqlalchemy import text
from database import engine, init_db

def check_tables():
    """Check if required tables exist in the database"""
    try:
        # Try to connect to the database
        with engine.connect() as conn:
            # Check for stocks table
            result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'stocks')"))
            stocks_exists = result.scalar()
            
            # If stocks table doesn't exist, initialize the database
            if not stocks_exists:
                print("Initializing database tables...")
                init_db()
                print("Database tables created successfully!")
                return True
            else:
                print("Database tables already exist.")
                return True
    
    except Exception as e:
        print(f"Error checking database tables: {e}")
        return False

if __name__ == "__main__":
    check_tables()