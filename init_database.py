import os
import sys
from database import init_db
from db_operations import create_default_watchlist

def main():
    """Initialize the database and create default data"""
    print("Initializing database...")
    
    # Check if database URL is set
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set.")
        sys.exit(1)
    
    # Initialize database tables
    init_db()
    print("Database tables created successfully!")
    
    # Create default watchlist
    watchlist = create_default_watchlist()
    if watchlist:
        print(f"Default watchlist '{watchlist.name}' created successfully!")
    else:
        print("Error creating default watchlist.")
    
    print("Database initialization completed.")

if __name__ == "__main__":
    main()