import streamlit as st
import pandas as pd
import datetime
from sqlalchemy import create_engine, text
from typing import List, Dict, Tuple, Optional, Any, Union

def get_db_connection():
    """Get a database connection using SQLAlchemy."""
    try:
        # Get database connection string from environment variables
        import os
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            st.error("Error: DATABASE_URL environment variable not found.")
            return None
        
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        return engine
    
    except Exception as e:
        st.error(f"Error connecting to database: {str(e)}")
        return None

def get_all_questions() -> pd.DataFrame:
    """
    Retrieve all questions from the database.
    
    Returns:
        pd.DataFrame: DataFrame containing all questions
    """
    try:
        engine = get_db_connection()
        if not engine:
            return pd.DataFrame()
        
        query = """
        SELECT DISTINCT question_id, question_text, is_default, display_order, 
               created_at, updated_at
        FROM questions
        ORDER BY display_order, question_id
        """
        
        # Use raw_connection with pandas
        connection = engine.raw_connection()
        questions_df = pd.read_sql_query(query, connection)
        connection.close()
        
        # Ensure no duplicates
        questions_df = questions_df.drop_duplicates(subset=['question_id'])
        
        return questions_df
    
    except Exception as e:
        st.error(f"Error retrieving questions: {str(e)}")
        return pd.DataFrame()

def get_default_questions() -> pd.DataFrame:
    """
    Retrieve all default questions from the database.
    
    Returns:
        pd.DataFrame: DataFrame containing default questions
    """
    try:
        engine = get_db_connection()
        if not engine:
            return pd.DataFrame()
        
        query = """
        SELECT question_id, question_text, is_default, display_order, 
               created_at, updated_at
        FROM questions
        WHERE is_default = TRUE
        ORDER BY display_order, question_id
        """
        
        # Use the engine directly with pandas
        questions_df = pd.read_sql_query(query, engine)
        return questions_df
    
    except Exception as e:
        st.error(f"Error retrieving default questions: {str(e)}")
        return pd.DataFrame()

def add_question(question_text: str, is_default: bool = False, display_order: int = None) -> Tuple[bool, str, int]:
    """
    Add a new question to the database.
    
    Args:
        question_text (str): The text of the question
        is_default (bool, optional): Whether this is a default question. Defaults to False.
        display_order (int, optional): The display order of the question. Defaults to None.
    
    Returns:
        Tuple[bool, str, int]: Success status, message, and new question ID
    """
    try:
        engine = get_db_connection()
        if not engine:
            return False, "Failed to connect to database", -1
        
        # Check if a question with the same text already exists
        connection = engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT question_id FROM questions 
            WHERE LOWER(question_text) = LOWER(%s)
            """,
            (question_text,)
        )
        existing_question = cursor.fetchone()
        
        if existing_question:
            cursor.close()
            connection.close()
            return False, "Question with this text already exists in the database", existing_question[0]
        
        # If display_order is not provided, get the max display_order and add 1
        if display_order is None:
            cursor.execute("SELECT COALESCE(MAX(display_order), 0) FROM questions")
            max_order = cursor.fetchone()[0]
            display_order = max_order + 1
        
        # Insert the new question
        cursor.execute(
            """
            INSERT INTO questions (question_text, is_default, display_order, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING question_id
            """,
            (
                question_text,
                is_default,
                display_order,
                datetime.datetime.now(),
                datetime.datetime.now()
            )
        )
        
        # Get the new question ID
        question_id = cursor.fetchone()[0]
        
        # Commit the transaction
        connection.commit()
        cursor.close()
        connection.close()
            
        return True, "Question added successfully", question_id
    
    except Exception as e:
        return False, f"Error adding question: {str(e)}", -1

def update_question(question_id: int, question_text: str = None, is_default: bool = None, 
                   display_order: int = None) -> Tuple[bool, str]:
    """
    Update an existing question in the database.
    
    Args:
        question_id (int): The ID of the question to update
        question_text (str, optional): The new text of the question. Defaults to None.
        is_default (bool, optional): Whether this is a default question. Defaults to None.
        display_order (int, optional): The display order of the question. Defaults to None.
    
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        engine = get_db_connection()
        if not engine:
            return False, "Failed to connect to database"
        
        # Build the SET clause dynamically based on which parameters are provided
        set_clauses = []
        params = {"question_id": question_id, "updated_at": datetime.datetime.now()}
        
        if question_text is not None:
            set_clauses.append("question_text = :question_text")
            params["question_text"] = question_text
        
        if is_default is not None:
            set_clauses.append("is_default = :is_default")
            params["is_default"] = is_default
        
        if display_order is not None:
            set_clauses.append("display_order = :display_order")
            params["display_order"] = display_order
        
        # Add the updated_at timestamp
        set_clauses.append("updated_at = :updated_at")
        
        # If no parameters were provided, return early
        if len(set_clauses) <= 1:  # Only updated_at
            return False, "No updates provided"
        
        # Build the SQL query
        query = f"""
            UPDATE questions
            SET {", ".join(set_clauses)}
            WHERE question_id = :question_id
        """
        
        # Execute the update
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            conn.commit()
            
            # Check if any rows were affected
            if result.rowcount == 0:
                return False, f"Question with ID {question_id} not found"
            
        return True, "Question updated successfully"
    
    except Exception as e:
        return False, f"Error updating question: {str(e)}"

def delete_question(question_id: int) -> Tuple[bool, str]:
    """
    Delete a question from the database.
    
    Args:
        question_id (int): The ID of the question to delete
    
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        engine = get_db_connection()
        if not engine:
            return False, "Failed to connect to database"
        
        # Use raw_connection instead of connect
        connection = engine.raw_connection()
        cursor = connection.cursor()
        
        # Delete the question
        cursor.execute("DELETE FROM questions WHERE question_id = %s", (question_id,))
        
        # Check if any rows were affected
        rows_affected = cursor.rowcount
        
        # Commit the transaction
        connection.commit()
        cursor.close()
        connection.close()
        
        if rows_affected == 0:
            return False, f"Question with ID {question_id} not found"
            
        return True, "Question deleted successfully"
    
    except Exception as e:
        return False, f"Error deleting question: {str(e)}"

def get_answers_for_business(business_id: str) -> pd.DataFrame:
    """
    Retrieve all answers for a specific business.
    
    Args:
        business_id (str): The ID of the business
    
    Returns:
        pd.DataFrame: DataFrame containing all answers for the business
    """
    try:
        engine = get_db_connection()
        if not engine:
            return pd.DataFrame()
        
        query = """
        SELECT a.answer_id, a.question_id, a.business_id, a.answer_text, 
               a.generated_by, a.is_edited, a.created_at, a.updated_at,
               q.question_text
        FROM answers a
        JOIN questions q ON a.question_id = q.question_id
        WHERE a.business_id = %s
        ORDER BY q.display_order, q.question_id
        """
        
        # Use raw_connection with pandas
        connection = engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute(query, (business_id,))
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        cursor.close()
        connection.close()
        
        # Create DataFrame from the results
        answers_df = pd.DataFrame(data, columns=columns)
        return answers_df
    
    except Exception as e:
        st.error(f"Error retrieving answers: {str(e)}")
        return pd.DataFrame()

def save_answer(business_id: str, question_id: int, answer_text: str, 
               generated_by: str = "AI", is_edited: bool = False) -> Tuple[bool, str]:
    """
    Save an answer to the database. If an answer already exists for this business and question,
    it will be updated.
    
    Args:
        business_id (str): The ID of the business
        question_id (int): The ID of the question
        answer_text (str): The text of the answer
        generated_by (str, optional): Who/what generated the answer. Defaults to "AI".
        is_edited (bool, optional): Whether the answer has been edited. Defaults to False.
    
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        engine = get_db_connection()
        if not engine:
            return False, "Failed to connect to database"
        
        # Check if an answer already exists for this business and question
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT answer_id FROM answers 
                    WHERE business_id = :business_id AND question_id = :question_id
                """),
                {"business_id": business_id, "question_id": question_id}
            )
            existing_answer = result.fetchone()
            
            if existing_answer:
                # Update the existing answer
                conn.execute(
                    text("""
                        UPDATE answers
                        SET answer_text = :answer_text, generated_by = :generated_by, 
                            is_edited = :is_edited, updated_at = :updated_at
                        WHERE answer_id = :answer_id
                    """),
                    {
                        "answer_id": existing_answer[0],
                        "answer_text": answer_text,
                        "generated_by": generated_by,
                        "is_edited": is_edited,
                        "updated_at": datetime.datetime.now()
                    }
                )
                message = "Answer updated successfully"
            else:
                # Insert a new answer
                conn.execute(
                    text("""
                        INSERT INTO answers (question_id, business_id, answer_text, 
                                           generated_by, is_edited, created_at, updated_at)
                        VALUES (:question_id, :business_id, :answer_text, 
                               :generated_by, :is_edited, :created_at, :updated_at)
                    """),
                    {
                        "question_id": question_id,
                        "business_id": business_id,
                        "answer_text": answer_text,
                        "generated_by": generated_by,
                        "is_edited": is_edited,
                        "created_at": datetime.datetime.now(),
                        "updated_at": datetime.datetime.now()
                    }
                )
                message = "Answer saved successfully"
            
            # Commit the transaction
            conn.commit()
            
        return True, message
    
    except Exception as e:
        return False, f"Error saving answer: {str(e)}"

def save_multiple_answers(business_id: str, answers: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Save multiple answers for a business in a single transaction.
    
    Args:
        business_id (str): The ID of the business
        answers (List[Dict[str, Any]]): List of answer dictionaries, each containing:
            - question_id: The ID of the question
            - answer_text: The text of the answer
            - generated_by (optional): Who/what generated the answer
            - is_edited (optional): Whether the answer has been edited
    
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        engine = get_db_connection()
        if not engine:
            return False, "Failed to connect to database"
        
        # Start a transaction
        with engine.begin() as conn:
            for answer in answers:
                question_id = answer["question_id"]
                answer_text = answer["answer_text"]
                generated_by = answer.get("generated_by", "AI")
                is_edited = answer.get("is_edited", False)
                
                # Check if an answer already exists
                result = conn.execute(
                    text("""
                        SELECT answer_id FROM answers 
                        WHERE business_id = :business_id AND question_id = :question_id
                    """),
                    {"business_id": business_id, "question_id": question_id}
                )
                existing_answer = result.fetchone()
                
                if existing_answer:
                    # Update the existing answer
                    conn.execute(
                        text("""
                            UPDATE answers
                            SET answer_text = :answer_text, generated_by = :generated_by, 
                                is_edited = :is_edited, updated_at = :updated_at
                            WHERE answer_id = :answer_id
                        """),
                        {
                            "answer_id": existing_answer[0],
                            "answer_text": answer_text,
                            "generated_by": generated_by,
                            "is_edited": is_edited,
                            "updated_at": datetime.datetime.now()
                        }
                    )
                else:
                    # Insert a new answer
                    conn.execute(
                        text("""
                            INSERT INTO answers (question_id, business_id, answer_text, 
                                               generated_by, is_edited, created_at, updated_at)
                            VALUES (:question_id, :business_id, :answer_text, 
                                   :generated_by, :is_edited, :created_at, :updated_at)
                        """),
                        {
                            "question_id": question_id,
                            "business_id": business_id,
                            "answer_text": answer_text,
                            "generated_by": generated_by,
                            "is_edited": is_edited,
                            "created_at": datetime.datetime.now(),
                            "updated_at": datetime.datetime.now()
                        }
                    )
        
        return True, f"Successfully saved {len(answers)} answers"
    
    except Exception as e:
        return False, f"Error saving answers: {str(e)}"

def delete_answer(answer_id: int) -> Tuple[bool, str]:
    """
    Delete an answer from the database.
    
    Args:
        answer_id (int): The ID of the answer to delete
    
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        engine = get_db_connection()
        if not engine:
            return False, "Failed to connect to database"
        
        # Delete the answer
        with engine.connect() as conn:
            result = conn.execute(
                text("DELETE FROM answers WHERE answer_id = :answer_id"),
                {"answer_id": answer_id}
            )
            conn.commit()
            
            # Check if any rows were affected
            if result.rowcount == 0:
                return False, f"Answer with ID {answer_id} not found"
            
        return True, "Answer deleted successfully"
    
    except Exception as e:
        return False, f"Error deleting answer: {str(e)}"

def create_analysis_session(business_id: str, session_name: str = None, 
                           summary_text: str = None) -> Tuple[bool, str, int]:
    """
    Create a new analysis session for a business.
    
    Args:
        business_id (str): The ID of the business
        session_name (str, optional): Name for the session. Defaults to None.
        summary_text (str, optional): Summary text for the session. Defaults to None.
    
    Returns:
        Tuple[bool, str, int]: Success status, message, and new session ID
    """
    try:
        engine = get_db_connection()
        if not engine:
            return False, "Failed to connect to database", -1
        
        # If session_name is not provided, use a timestamp
        if session_name is None:
            session_name = f"Analysis {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Insert the new session
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO analysis_sessions (business_id, session_name, summary_text, created_at, updated_at)
                    VALUES (:business_id, :session_name, :summary_text, :created_at, :updated_at)
                    RETURNING session_id
                """),
                {
                    "business_id": business_id,
                    "session_name": session_name,
                    "summary_text": summary_text,
                    "created_at": datetime.datetime.now(),
                    "updated_at": datetime.datetime.now()
                }
            )
            
            # Get the new session ID
            session_id = result.scalar()
            
            # Commit the transaction
            conn.commit()
            
        return True, "Analysis session created successfully", session_id
    
    except Exception as e:
        return False, f"Error creating analysis session: {str(e)}", -1

def add_answers_to_session(session_id: int, answer_ids: List[int]) -> Tuple[bool, str]:
    """
    Add answers to an analysis session.
    
    Args:
        session_id (int): The ID of the session
        answer_ids (List[int]): List of answer IDs to add to the session
    
    Returns:
        Tuple[bool, str]: Success status and message
    """
    try:
        engine = get_db_connection()
        if not engine:
            return False, "Failed to connect to database"
        
        # Start a transaction
        with engine.begin() as conn:
            for answer_id in answer_ids:
                # Check if the answer is already in the session
                result = conn.execute(
                    text("""
                        SELECT 1 FROM session_answers 
                        WHERE session_id = :session_id AND answer_id = :answer_id
                    """),
                    {"session_id": session_id, "answer_id": answer_id}
                )
                
                if not result.fetchone():
                    # Add the answer to the session
                    conn.execute(
                        text("""
                            INSERT INTO session_answers (session_id, answer_id, created_at)
                            VALUES (:session_id, :answer_id, :created_at)
                        """),
                        {
                            "session_id": session_id,
                            "answer_id": answer_id,
                            "created_at": datetime.datetime.now()
                        }
                    )
        
        return True, f"Successfully added {len(answer_ids)} answers to the session"
    
    except Exception as e:
        return False, f"Error adding answers to session: {str(e)}"

def get_analysis_sessions(business_id: str) -> pd.DataFrame:
    """
    Retrieve all analysis sessions for a business.
    
    Args:
        business_id (str): The ID of the business
    
    Returns:
        pd.DataFrame: DataFrame containing all analysis sessions for the business
    """
    try:
        engine = get_db_connection()
        if not engine:
            return pd.DataFrame()
        
        query = """
        SELECT session_id, business_id, session_name, summary_text, created_at, updated_at
        FROM analysis_sessions
        WHERE business_id = :business_id
        ORDER BY created_at DESC
        """
        
        # Use the engine directly with pandas
        sessions_df = pd.read_sql_query(query, engine, params={"business_id": business_id})
        return sessions_df
    
    except Exception as e:
        st.error(f"Error retrieving analysis sessions: {str(e)}")
        return pd.DataFrame()

def get_session_answers(session_id: int) -> pd.DataFrame:
    """
    Retrieve all answers for a specific analysis session.
    
    Args:
        session_id (int): The ID of the session
    
    Returns:
        pd.DataFrame: DataFrame containing all answers for the session
    """
    try:
        engine = get_db_connection()
        if not engine:
            return pd.DataFrame()
        
        query = """
        SELECT a.answer_id, a.question_id, a.business_id, a.answer_text, 
               a.generated_by, a.is_edited, a.created_at, a.updated_at,
               q.question_text
        FROM session_answers sa
        JOIN answers a ON sa.answer_id = a.answer_id
        JOIN questions q ON a.question_id = q.question_id
        WHERE sa.session_id = :session_id
        ORDER BY q.display_order, q.question_id
        """
        
        # Use the engine directly with pandas
        answers_df = pd.read_sql_query(query, engine, params={"session_id": session_id})
        return answers_df
    
    except Exception as e:
        st.error(f"Error retrieving session answers: {str(e)}")
        return pd.DataFrame() 