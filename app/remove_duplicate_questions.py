import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a database connection."""
    try:
        # Get database connection string from environment variables
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            print("Error: DATABASE_URL environment variable not found.")
            return None
        
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        return engine
    
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return None

def remove_duplicate_questions():
    """
    Remove duplicate questions from the database.
    This function keeps the question with the lowest question_id for each unique question_text.
    """
    try:
        engine = get_db_connection()
        if not engine:
            print("Failed to connect to database")
            return False
        
        # Use raw connection
        connection = engine.raw_connection()
        cursor = connection.cursor()
        
        # Find duplicate questions
        cursor.execute("""
            WITH duplicates AS (
                SELECT 
                    question_id,
                    question_text,
                    ROW_NUMBER() OVER (PARTITION BY LOWER(question_text) ORDER BY question_id) as row_num
                FROM questions
            )
            SELECT question_id, question_text
            FROM duplicates
            WHERE row_num > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            print("No duplicate questions found.")
            cursor.close()
            connection.close()
            return True
        
        print(f"Found {len(duplicates)} duplicate questions.")
        
        # Get the IDs of duplicate questions to delete
        duplicate_ids = [row[0] for row in duplicates]
        
        # Format the list for SQL IN clause
        ids_str = ','.join(str(id) for id in duplicate_ids)
        
        # First delete answers associated with the duplicate questions
        cursor.execute(f"""
            DELETE FROM answers
            WHERE question_id IN ({ids_str})
        """)
        
        # Then delete the duplicate questions
        cursor.execute(f"""
            DELETE FROM questions
            WHERE question_id IN ({ids_str})
        """)
        
        # Commit the transaction
        connection.commit()
        
        print(f"Successfully removed {len(duplicate_ids)} duplicate questions.")
        
        # Close the connection
        cursor.close()
        connection.close()
        
        return True
    
    except Exception as e:
        print(f"Error removing duplicate questions: {str(e)}")
        return False

if __name__ == "__main__":
    print("Starting duplicate question removal process...")
    success = remove_duplicate_questions()
    if success:
        print("Process completed successfully.")
    else:
        print("Process failed.") 