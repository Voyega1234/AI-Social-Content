import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Load environment variables
load_dotenv()

def check_table_structure():
    """Check the structure of the social_media_content table."""
    try:
        # Get database connection string from environment variables
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            print("Error: DATABASE_URL environment variable not found.")
            return False
        
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        
        # Get inspector
        inspector = inspect(engine)
        
        # Check if table exists
        if 'social_media_content' in inspector.get_table_names():
            print("Table 'social_media_content' exists.")
            
            # Get columns
            columns = inspector.get_columns('social_media_content')
            print("\nColumns:")
            for column in columns:
                print(f"  - {column['name']} ({column['type']})")
        else:
            print("Table 'social_media_content' does not exist.")
            
            # List all tables
            print("\nAvailable tables:")
            for table_name in inspector.get_table_names():
                print(f"  - {table_name}")
        
        # Try to execute a simple query
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM social_media_content LIMIT 1"))
            row = result.fetchone()
            if row:
                print("\nSample row:")
                for key, value in row._mapping.items():
                    print(f"  - {key}: {value}")
            else:
                print("\nNo data in the table.")
        
        return True
    
    except Exception as e:
        print(f"Error checking table structure: {e}")
        return False

if __name__ == "__main__":
    print("Checking table structure...")
    check_table_structure()
    print("Check complete.") 