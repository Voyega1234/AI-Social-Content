import streamlit as st
import pandas as pd
import os
import json
import datetime
import time
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from google import genai
from google.genai import types
import qa_manager  # Import our new qa_manager module

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get a database connection."""
    try:
        # Get database connection string from environment variables
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

def get_gemini_client():
    """Get a Gemini client."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("Error: GEMINI_API_KEY environment variable not found.")
            return None
        
        # Initialize Gemini client with the correct approach from the documentation
        client = genai.Client(api_key=api_key)
        return client
    
    except Exception as e:
        st.error(f"Error initializing Gemini client: {str(e)}")
        return None

def save_insights_to_db(business_id, insights_data):
    """Save business context analysis to the database."""
    try:
        engine = get_db_connection()
        if not engine:
            return False, "Failed to connect to database"
        
        # Convert UUID to string if it's a UUID object
        if hasattr(business_id, 'hex'):
            business_id = str(business_id)
        
        # Create a connection
        with engine.connect() as conn:
            # Use a transaction context manager
            with conn.begin():
                # Check if business_context_analysis table exists, create if not
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS business_context_analysis (
                        insight_id SERIAL PRIMARY KEY,
                        business_id UUID NOT NULL,
                        insight_data JSONB NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                    )
                """))
                
                # Insert the insights data
                conn.execute(
                    text("""
                        INSERT INTO business_context_analysis (business_id, insight_data, created_at)
                        VALUES (:business_id, :insight_data, :created_at)
                    """),
                    {
                        "business_id": business_id,
                        "insight_data": json.dumps(insights_data),
                        "created_at": datetime.datetime.now()
                    }
                )
            
        return True, "Business context analysis saved to database successfully"
    
    except Exception as e:
        return False, f"Error saving business context analysis to database: {str(e)}"

def get_saved_insights(business_id):
    """Get saved business context analysis from the database."""
    try:
        engine = get_db_connection()
        if not engine:
            return []
        
        # Convert UUID to string if it's a UUID object
        if hasattr(business_id, 'hex'):
            business_id = str(business_id)
        
        # Create a connection
        with engine.connect() as conn:
            # First, check if the business_context_analysis table exists and create it if it doesn't
            with conn.begin():  # Use a transaction context manager
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS business_context_analysis (
                        insight_id SERIAL PRIMARY KEY,
                        business_id UUID NOT NULL,
                        insight_data JSONB NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                    )
                """))
            
            # Query the insights data
            result = conn.execute(
                text("""
                    SELECT insight_id, insight_data, created_at
                    FROM business_context_analysis
                    WHERE business_id = :business_id
                    ORDER BY created_at DESC
                """),
                {"business_id": business_id}
            )
            
            # Fetch all results
            insights = []
            for row in result:
                insight_data = row[1]
                # Check if insight_data is a string and needs to be parsed
                if isinstance(insight_data, str):
                    try:
                        insight_data = json.loads(insight_data)
                    except json.JSONDecodeError:
                        # If it's not valid JSON, keep it as is
                        pass
                
                insights.append({
                    "insight_id": row[0],
                    "insight_data": insight_data,
                    "created_at": row[2]
                })
            
        return insights
    
    except Exception as e:
        st.error(f"Error retrieving business context analysis from database: {str(e)}")
        return []

def client_information_page():
    """Display the client information page."""
    # Check if insights were just saved
    if 'insights_saved' in st.session_state and st.session_state.insights_saved:
        st.success("Business context analysis saved to database successfully!")
        # Clear the flag
        st.session_state.insights_saved = False
    
    st.title("🧠 Business Context Analysis")
    
    st.markdown("""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="margin-top: 0;">Business Context Analysis Generator</h3>
        <p>This tool analyzes your social media data to provide detailed insights about your business context.</p>
        <p>The AI will answer questions about demographics, psychographics, behavioral patterns, and market positioning based on your social media content.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get database engine
    engine = get_db_connection()
    if engine:
        try:
            # Get list of businesses with names
            business_query = """
            SELECT DISTINCT b.business_id, b.business_name 
            FROM social_media_content s
            JOIN businesses b ON s.business_id = b.business_id
            """
            
            # Use the engine's raw_connection method with pandas
            try:
                connection = engine.raw_connection()
                businesses_df = pd.read_sql_query(business_query, connection)
                connection.close()
            except Exception as e:
                st.warning(f"Error with join query: {str(e)}")
                # Fallback query if the join fails
                business_query = """
                SELECT DISTINCT business_id 
                FROM social_media_content
                """
                connection = engine.raw_connection()
                businesses_df = pd.read_sql_query(business_query, connection)
                connection.close()
            
            if not businesses_df.empty:
                # Create a selection for business
                if 'business_name' in businesses_df.columns:
                    # If we have business names, use them for display
                    business_options = businesses_df.set_index('business_id')['business_name'].to_dict()
                    
                    # Store the current selected business in session state for comparison
                    if 'previous_selected_business' not in st.session_state:
                        st.session_state.previous_selected_business = None
                    
                    selected_business = st.selectbox(
                        "Select a business to analyze:",
                        options=list(business_options.keys()),
                        format_func=lambda x: business_options.get(x, x),
                        index=0,
                        key="business_selector"
                    )
                    
                    # Check if business selection has changed
                    if st.session_state.previous_selected_business is not None and st.session_state.previous_selected_business != selected_business:
                        # Clear analysis-related session state variables when business changes
                        keys_to_clear = [
                            'business_context_analysis_json', 
                            'edited_insights',
                            'viewing_saved_insights',
                            'selected_insight_id',
                            'excluded_questions',
                            'editing_answer'
                        ]
                        for key in keys_to_clear:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        # Update the previous selected business
                        st.session_state.previous_selected_business = selected_business
                        st.rerun()
                    
                    # Update the previous selected business
                    st.session_state.previous_selected_business = selected_business
                else:
                    # Fallback to just showing business IDs
                    selected_business = st.selectbox(
                        "Select a business to analyze:",
                        businesses_df['business_id'].tolist(),
                        index=0,
                        key="business_selector"
                    )
                
                # Get social media data for the selected business
                social_media_query = f"""
                SELECT * FROM social_media_content
                WHERE business_id = '{selected_business}'
                """
                connection = engine.raw_connection()
                social_media_df = pd.read_sql_query(social_media_query, connection)
                connection.close()
                
                if not social_media_df.empty:
                    st.success(f"Found {len(social_media_df)} social media posts for analysis.")
                    
                    # Display a sample of the data
                    with st.expander("View social media data sample"):
                        st.dataframe(social_media_df[['platform', 'content_type', 'full_content', 'likes_count', 'comments_count', 'shares_count', 'hashtags']].head())
                    
                    # Get questions from the database
                    questions_df = qa_manager.get_all_questions()
                    
                    # Remove any duplicate questions
                    questions_df = questions_df.drop_duplicates(subset=['question_id'])
                    
                    # Store questions in session state to prevent duplicate rendering
                    if 'questions_df' not in st.session_state:
                        st.session_state.questions_df = questions_df
                    else:
                        # Only update if there are changes
                        if len(questions_df) != len(st.session_state.questions_df):
                            st.session_state.questions_df = questions_df
                    
                    # If no questions in the database, initialize with default questions
                    if questions_df.empty:
                        st.info("No questions found in the database. Initializing with default questions...")
                        default_questions = [
                            "What is likely their age range, life stage, and family status?",
                            "Would income level matter for this product or service?",
                            "Do they have a specific occupation and would it influence their purchasing behavior?",
                            "What are their personal values, life priorities, or causes they care about?",
                            "What is their lifestyle like, and how does it shape their needs?",
                            "What specific problems, frustrations, or unmet needs are they experiencing?",
                            "What deeply held beliefs drive their decisions?",
                            "Who are the Key Opinion Leaders or influencers they are likely to respect and follow?",
                            "What do they hope to achieve?",
                            "What struggles do they face that your product/service might solve?",
                            "What complementary fields or interests overlap with this niche?",
                            "How else might they solve the same problem your product addresses?",
                            "Is there an evolving trend that's rapidly changing the niche landscape?",
                            "Are purchases triggered by life stages or seasonal events?"
                        ]
                        
                        # Add default questions to the database
                        for i, question in enumerate(default_questions):
                            success, message, _ = qa_manager.add_question(
                                question_text=question,
                                is_default=True,
                                display_order=i+1
                            )
                            if not success:
                                st.warning(f"Failed to add default question: {message}")
                        
                        # Refresh questions from the database
                        questions_df = qa_manager.get_all_questions()
                    
                    # Display each question in its own box with option to edit/delete
                    st.subheader("Questions we'll answer about your target audience")
                    
                    # Add explanation about Skip functionality
                    st.info("""
                    Use the **Skip** button to exclude questions from being sent to Gemini for analysis.
                    Skipped questions will remain in your database but won't be included in the analysis.
                    You can include them again at any time by clicking the **Include** button.
                    """)
                    
                    # Add new question - using a button and container instead of an expander
                    if 'show_add_question' not in st.session_state:
                        st.session_state.show_add_question = False
                        
                    if st.button("➕ Add a custom question"):
                        st.session_state.show_add_question = not st.session_state.show_add_question
                        
                    if st.session_state.show_add_question:
                        with st.container():
                            new_question = st.text_area("Enter your custom question:", placeholder="e.g., What social media platforms are most effective for reaching this audience?")
                            
                            # Show which category the question will be added to
                            if new_question:
                                category = find_topic_for_question(new_question)
                                st.info(f"This question will be added to the '{category}' category.")
                            
                            if st.button("Submit Question"):
                                if new_question:
                                    success, message, question_id = qa_manager.add_question(
                                        question_text=new_question,
                                        is_default=False
                                    )
                                    if success:
                                        st.success(f"Question added successfully to the '{category}' category!")
                                        # Force expander for this category to be open on refresh
                                        category_key = f"expander_{category.replace(' ', '_').lower()}"
                                        st.session_state[category_key] = True
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to add question: {message}")
                                else:
                                    st.warning("Please enter a question before submitting.")
                    
                    # Get answers for this business
                    answers_df = qa_manager.get_answers_for_business(selected_business)
                    
                    # Create a dictionary of question_id -> answer_text for easy lookup
                    answers_dict = {}
                    if not answers_df.empty:
                        answers_dict = answers_df.set_index('question_id')['answer_text'].to_dict()
                    
                    # Initialize excluded questions in session state if not already there
                    if 'excluded_questions' not in st.session_state:
                        st.session_state.excluded_questions = set()
                    
                    # Group questions by topic
                    # Define topic groups
                    topic_groups = {
                        "Demographics and Background": [
                            "What is likely their age range, life stage, and family status?",
                            "Would income level matter for this product or service?",
                            "Do they have a specific occupation and would it influence their purchasing behavior?"
                        ],
                        "Values and Lifestyle": [
                            "What are their personal values, life priorities, or causes they care about?",
                            "What is their lifestyle like, and how does it shape their needs?",
                            "What deeply held beliefs drive their decisions?"
                        ],
                        "Needs and Challenges": [
                            "What specific problems, frustrations, or unmet needs are they experiencing?",
                            "What struggles do they face that your product/service might solve?",
                            "How else might they solve the same problem your product addresses?"
                        ],
                        "Goals and Influences": [
                            "Who are the Key Opinion Leaders or influencers they are likely to respect and follow?",
                            "What do they hope to achieve?",
                            "What complementary fields or interests overlap with this niche?"
                        ],
                        "Market Trends": [
                            "Is there an evolving trend that's rapidly changing the niche landscape?",
                            "Are purchases triggered by life stages or seasonal events?"
                        ]
                    }
                    
                    # Function to find the topic for a question
                    def find_topic_for_question(question_text):
                        for topic, questions in topic_groups.items():
                            if any(q.lower() in question_text.lower() or question_text.lower() in q.lower() for q in questions):
                                return topic
                        return "Other Questions"
                    
                    # Group questions by topic
                    questions_by_topic = {}
                    # Initialize "Other Questions" category to ensure it exists even if empty
                    questions_by_topic["Other Questions"] = []
                    
                    for _, row in st.session_state.questions_df.iterrows():
                        question_id = row['question_id']
                        question_text = row['question_text']
                        topic = find_topic_for_question(question_text)
                        
                        if topic not in questions_by_topic:
                            questions_by_topic[topic] = []
                        
                        questions_by_topic[topic].append({
                            'question_id': question_id,
                            'question_text': question_text
                        })
                    
                    # Display questions grouped by topic (all collapsed by default)
                    for topic, questions in questions_by_topic.items():
                        # Skip empty categories
                        if not questions:
                            continue
                            
                        # Create a unique key for this topic's expander
                        topic_key = f"expander_{topic.replace(' ', '_').lower()}"
                        
                        # Initialize the expander state in session state if it doesn't exist
                        if topic_key not in st.session_state:
                            st.session_state[topic_key] = False  # Default to collapsed
                        
                        # Set expanded=False to hide by default, unless programmatically set to True
                        with st.expander(f"📋 {topic}", expanded=st.session_state[topic_key]):
                            # Reset the state after rendering if it was temporarily set to True
                            if st.session_state[topic_key] == True:
                                st.session_state[topic_key] = False
                                
                            for question in questions:
                                question_id = question['question_id']
                                question_text = question['question_text']
                                
                                # Check if this question is excluded
                                is_excluded = question_id in st.session_state.excluded_questions
                                
                                # Create a container with custom styling for the question
                                st.markdown(f"""
                                <div style="background-color: #f8f9fa; border-left: 4px solid #4CAF50; padding: 10px; margin-bottom: 10px; border-radius: 5px;">
                                    <strong style="font-size: 1.05rem;">{question_text}</strong>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Create columns for the question content and skip button
                                col1, col2 = st.columns([5, 1])
                                
                                with col1:
                                    # Add visual indicator if question is excluded
                                    if is_excluded:
                                        st.markdown("""
                                        <p style="color: #888888; font-style: italic; font-size: 0.8em; margin-top: -5px;">
                                            This question will be skipped during analysis
                                        </p>
                                        """, unsafe_allow_html=True)
                                    
                                    # If there's an answer for this question, display it
                                    if question_id in answers_dict:
                                        st.markdown("### Answer:")
                                        st.markdown(answers_dict[question_id])
                                    else:
                                        st.markdown("*No answer available yet.*")
                                
                                with col2:
                                    # Create a container for buttons
                                    button_container = st.container()
                                    
                                    # Toggle button text based on current state
                                    skip_text = "✓ Include" if is_excluded else "⏭️ Skip"
                                    skip_key = f"include_{question_id}" if is_excluded else f"skip_{question_id}"
                                    
                                    # Skip/Include button with different styling based on state
                                    button_type = "primary" if not is_excluded else "secondary"
                                    
                                    # Skip/Include button
                                    if button_container.button(skip_text, key=skip_key, type=button_type):
                                        if is_excluded:
                                            # Remove from excluded list
                                            st.session_state.excluded_questions.remove(question_id)
                                        else:
                                            # Add to excluded list
                                            st.session_state.excluded_questions.add(question_id)
                                        st.rerun()
                                
                                # Add a separator between questions
                                st.markdown("<hr style='margin: 15px 0; border: 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
                    
                    # Edit answer modal
                    if 'editing_answer' in st.session_state:
                        with st.form(key="edit_answer_form"):
                            question_id = st.session_state.editing_answer
                            question_text = st.session_state.questions_df[st.session_state.questions_df['question_id'] == question_id]['question_text'].iloc[0]
                            st.subheader(f"Edit Answer for: {question_text}")
                            edited_answer = st.text_area("Edit your answer:", value=st.session_state.edited_answer, height=200)
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Save Changes"):
                                    success, message = qa_manager.save_answer(
                                        business_id=selected_business,
                                        question_id=question_id,
                                        answer_text=edited_answer,
                                        generated_by="User",
                                        is_edited=True
                                    )
                                    if success:
                                        del st.session_state.editing_answer
                                        del st.session_state.edited_answer
                                        st.success("Answer updated!")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to update answer: {message}")
                            with col2:
                                if st.form_submit_button("Cancel"):
                                    del st.session_state.editing_answer
                                    del st.session_state.edited_answer
                                    st.rerun()
                    
                    # Check for saved insights
                    saved_insights = get_saved_insights(selected_business)
                    if saved_insights and len(saved_insights) > 0:
                        st.info(f"Found {len(saved_insights)} saved business context analysis for this business.")
                        if st.button("View Saved Insights"):
                            st.session_state.viewing_saved_insights = True
                    
                    # View saved insights
                    if 'viewing_saved_insights' in st.session_state and st.session_state.viewing_saved_insights:
                        st.subheader("Saved Business Context Analysis")
                        
                        # Create a list of insight dates for the selectbox
                        insight_dates = [insight['created_at'].strftime('%Y-%m-%d %H:%M') for insight in saved_insights]
                        
                        # Add a selectbox to choose which insight to view
                        selected_insight_index = st.selectbox(
                            "Select an insight to view:",
                            range(len(insight_dates)),
                            format_func=lambda i: f"Insight from {insight_dates[i]}"
                        )
                        
                        # Get the selected insight
                        selected_insight = saved_insights[selected_insight_index]
                        
                        # Display the summary
                        summary_text = selected_insight['insight_data']['summary']
                        summary_parts = summary_text.split("\n\n")
                        
                        if len(summary_parts) >= 2:
                            # If summary is properly formatted in paragraphs
                            business_description = summary_parts[0]
                            audience_info = summary_parts[1]
                            
                            st.markdown(f"""
                            <div style="background-color: #e6f3ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                <h4 style="margin-top: 0;">Business Summary</h4>
                                <h5 style="color: #1e3a8a; margin-top: 10px;">🏢 Business Description</h5>
                                <p style="font-weight: 500;">{business_description}</p>
                                <h5 style="color: #1e3a8a; margin-top: 15px;">👥 Target Audience</h5>
                                <p>{audience_info}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Fallback if not in paragraphs
                            st.markdown(f"""
                            <div style="background-color: #e6f3ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                <h4 style="margin-top: 0;">Summary</h4>
                                <p>{summary_text}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Display each question and answer
                        st.subheader("Detailed Analysis")
                        for item in selected_insight['insight_data']['business_context_analysis']:
                            with st.expander(item['question']):
                                st.markdown(item['answer'])
                        
                        if st.button("Hide Saved Insights"):
                            st.session_state.viewing_saved_insights = False
                            st.rerun()
                    
                    # Button to generate insights
                    if st.button("🔍 Analyze Target Audience", use_container_width=True, type="primary"):
                        with st.spinner("Analyzing social media data to understand your target audience..."):
                            # Prepare data for Gemini - handle None values
                            # Replace None values with empty strings before joining
                            social_media_df['full_content'] = social_media_df['full_content'].fillna("")
                            content_text = "\n".join([str(text) for text in social_media_df['full_content'].tolist()])
                            
                            # Handle None values in hashtags
                            social_media_df['hashtags'] = social_media_df['hashtags'].fillna("")
                            hashtags = ", ".join([tag for tags in social_media_df['hashtags'] for tag in str(tags).split(',') if tag])
                            
                            # Handle None values in platform and content_type
                            social_media_df['platform'] = social_media_df['platform'].fillna("")
                            social_media_df['content_type'] = social_media_df['content_type'].fillna("")
                            platforms = ", ".join([p for p in social_media_df['platform'].unique() if p])
                            content_types = ", ".join([ct for ct in social_media_df['content_type'].unique() if ct])
                            
                            # Calculate engagement metrics - ensure numeric columns are treated as such
                            social_media_df['likes_count'] = pd.to_numeric(social_media_df['likes_count'], errors='coerce').fillna(0)
                            social_media_df['comments_count'] = pd.to_numeric(social_media_df['comments_count'], errors='coerce').fillna(0)
                            social_media_df['shares_count'] = pd.to_numeric(social_media_df['shares_count'], errors='coerce').fillna(0)
                            avg_likes = social_media_df['likes_count'].mean()
                            avg_comments = social_media_df['comments_count'].mean()
                            avg_shares = social_media_df['shares_count'].mean()
                            
                            # Define the JSON schema for structured output
                            response_schema = {
                                "type": "OBJECT",
                                "properties": {
                                    "business_context_analysis": {
                                        "type": "ARRAY",
                                        "items": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "question": {"type": "STRING"},
                                                "answer": {"type": "STRING"},
                                                "question_id": {"type": "INTEGER"}
                                            },
                                            "required": ["question", "answer", "question_id"]
                                        }
                                    },
                                    "summary": {"type": "STRING"}
                                },
                                "required": ["business_context_analysis", "summary"]
                            }
                            
                            # Create a list of questions with IDs for the prompt, excluding skipped questions
                            if 'excluded_questions' in st.session_state:
                                # Filter out excluded questions
                                filtered_questions_df = questions_df[~questions_df['question_id'].isin(st.session_state.excluded_questions)]
                                questions_with_ids = filtered_questions_df[['question_id', 'question_text']].to_dict('records')
                                
                                # Show how many questions were excluded
                                excluded_count = len(st.session_state.excluded_questions)
                                if excluded_count > 0:
                                    st.info(f"{excluded_count} question(s) will be skipped during analysis.")
                            else:
                                # Use all questions if no exclusions are set
                                questions_with_ids = questions_df[['question_id', 'question_text']].to_dict('records')
                            
                            # Create prompt for Gemini
                            prompt = f"""
                            You are an expert social media analyst and market researcher. Analyze the following social media data to provide detailed insights about the business and its target audience.
                            
                            SOCIAL MEDIA DATA:
                            - Content: {content_text}
                            - Hashtags: {hashtags}
                            - Platforms: {platforms}
                            - Content Types: {content_types}
                            - Average Likes: {avg_likes}
                            - Average Comments: {avg_comments}
                            - Average Shares: {avg_shares}
                            
                            Based on this data, please answer the following questions about the target audience:
                            {json.dumps(questions_with_ids)}
                            
                            IMPORTANT INSTRUCTIONS:
                            1. Only provide insights that are directly supported by the data provided.
                            2. DO NOT make up or invent information that isn't evident in the data.
                            3. If there isn't enough information to answer a question confidently, acknowledge the limitations and provide the best analysis based ONLY on what's available.
                            4. Be specific about what you can observe from the data and avoid speculative claims.
                            5. When discussing demographics or psychographics, only mention patterns that are clearly indicated in the content or engagement metrics.
                            6. In the summary, your HIGHEST PRIORITY should be thoroughly describing the business itself - what they do, their services, products, style, mood, tone, and brand identity. This business description must come first and be comprehensive.
                            7. Only after providing a detailed business description should you then discuss the target audience information.
                            
                            Format your response as a JSON object with an array of question-answer pairs (including question_id) and a summary.
                            The summary should be structured in two clear paragraphs:
                            1. First paragraph: Describe what the business does as a company, including detailed information about their products, services, key offerings, brand style, mood, tone, and unique value proposition.
                            2. Second paragraph: Describe the target audience and how the business addresses their needs.
                            
                            CRITICAL: The business description in the first paragraph MUST be comprehensive and should be given priority. Include specific details about their products, services, brand identity, and overall business focus before moving on to audience information.
                            
                            Be specific and provide actionable insights, but only based on the actual data provided.
                            """
                            
                            try:
                                # Get Gemini client
                                client = get_gemini_client()
                                
                                if client:
                                    # Configure the model using the correct syntax
                                    generation_config = types.GenerateContentConfig(
                                        temperature=0.1,
                                        top_p=0.95,
                                        top_k=40,
                                        max_output_tokens=8192,
                                        response_mime_type="application/json",
                                        response_schema=response_schema
                                    )
                                    
                                    # Generate content using the correct syntax
                                    response = client.models.generate_content(
                                        model="gemini-2.0-flash",
                                        contents=[prompt],
                                        config=generation_config
                                    )
                                    
                                    # Parse the JSON response
                                    business_context_analysis_json = json.loads(response.text)
                                    
                                    # Store in session state for editing
                                    st.session_state.business_context_analysis_json = business_context_analysis_json
                                    st.session_state.edited_insights = business_context_analysis_json.copy()
                                    
                                    # Save answers to the database
                                    answers_to_save = []
                                    for insight in business_context_analysis_json['business_context_analysis']:
                                        answers_to_save.append({
                                            "question_id": insight['question_id'],
                                            "answer_text": insight['answer'],
                                            "generated_by": "Gemini AI",
                                            "is_edited": False
                                        })
                                    
                                    success, message = qa_manager.save_multiple_answers(
                                        business_id=selected_business,
                                        answers=answers_to_save
                                    )
                                    
                                    if not success:
                                        st.warning(f"Some answers could not be saved to the database: {message}")
                                    
                                    # Display the insights
                                    st.subheader("📊 Business Context Analysis")
                                    st.info("The AI has analyzed your social media data and generated the following insights. You can edit any answer by clicking the edit button.")
                                    
                                    # Display summary with edit option
                                    summary_text = business_context_analysis_json['summary']
                                    summary_parts = summary_text.split("\n\n")
                                    
                                    if len(summary_parts) >= 2:
                                        # If summary is properly formatted in paragraphs
                                        business_description = summary_parts[0]
                                        audience_info = summary_parts[1]
                                        
                                        st.markdown(f"""
                                        <div style="background-color: #e6f3ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                            <h4 style="margin-top: 0;">Business Summary</h4>
                                            <h5 style="color: #1e3a8a; margin-top: 10px;">🏢 Business Description</h5>
                                            <p style="font-weight: 500;">{business_description}</p>
                                            <h5 style="color: #1e3a8a; margin-top: 15px;">👥 Target Audience</h5>
                                            <p>{audience_info}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    else:
                                        # Fallback if not in paragraphs
                                        st.markdown(f"""
                                        <div style="background-color: #e6f3ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                            <h4 style="margin-top: 0;">Summary</h4>
                                            <p>{summary_text}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    if st.button("✏️ Edit Summary"):
                                        st.session_state.editing_summary = True
                                    
                                    # Edit summary if requested
                                    if 'editing_summary' in st.session_state and st.session_state.editing_summary:
                                        with st.form(key="edit_summary_form"):
                                            st.subheader("Edit Summary")
                                            edited_summary = st.text_area("Edit the summary:", value=st.session_state.edited_insights['summary'], height=200)
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                if st.form_submit_button("Save Changes"):
                                                    st.session_state.edited_insights['summary'] = edited_summary
                                                    del st.session_state.editing_summary
                                                    st.success("Summary updated!")
                                                    st.rerun()
                                            with col2:
                                                if st.form_submit_button("Cancel"):
                                                    del st.session_state.editing_summary
                                                    st.rerun()
                                    
                                    # Display each question and answer in its own card with edit option
                                    for i, insight in enumerate(business_context_analysis_json['business_context_analysis']):
                                        with st.expander(insight['question']):
                                            st.markdown(insight['answer'])
                                            if st.button("✏️ Edit Answer", key=f"edit_answer_{i}"):
                                                st.session_state.editing_answer = insight['question_id']
                                                st.session_state.edited_answer = insight['answer']
                                                st.rerun()
                                    
                                    # Save to database button
                                    if st.button("💾 Save Insights to Database", use_container_width=True):
                                        success, message = save_insights_to_db(
                                            selected_business, 
                                            st.session_state.edited_insights if 'edited_insights' in st.session_state else business_context_analysis_json
                                        )
                                        if success:
                                            st.success(message)
                                            # Set a flag in session state to indicate successful save
                                            st.session_state.insights_saved = True
                                            # Add a small delay to ensure the success message is shown
                                            time.sleep(0.5)
                                            # Refresh the page
                                            st.rerun()
                                        else:
                                            st.error(message)
                                    
                                    # Option to download as JSON
                                    st.download_button(
                                        "📄 Download as JSON",
                                        data=json.dumps(st.session_state.edited_insights if 'edited_insights' in st.session_state else business_context_analysis_json, indent=2),
                                        file_name="business_context_analysis.json",
                                        mime="application/json",
                                        use_container_width=True
                                    )
                                else:
                                    st.error("Could not initialize Gemini client. Please check your API key.")
                                    
                            except Exception as e:
                                st.error(f"Error generating insights: {str(e)}")
                    
                    # If insights were previously generated, display them
                    elif 'business_context_analysis_json' in st.session_state and 'viewing_saved_insights' not in st.session_state:
                        st.subheader("📊 Previously Generated Business Context Analysis")
                        
                        # Use edited insights if available
                        insights_to_display = st.session_state.edited_insights if 'edited_insights' in st.session_state else st.session_state.business_context_analysis_json
                        
                        # Display summary with edit option
                        summary_text = insights_to_display['summary']
                        summary_parts = summary_text.split("\n\n")
                        
                        if len(summary_parts) >= 2:
                            # If summary is properly formatted in paragraphs
                            business_description = summary_parts[0]
                            audience_info = summary_parts[1]
                            
                            st.markdown(f"""
                            <div style="background-color: #e6f3ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                <h4 style="margin-top: 0;">Business Summary</h4>
                                <h5 style="color: #1e3a8a; margin-top: 10px;">🏢 Business Description</h5>
                                <p style="font-weight: 500;">{business_description}</p>
                                <h5 style="color: #1e3a8a; margin-top: 15px;">👥 Target Audience</h5>
                                <p>{audience_info}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Fallback if not in paragraphs
                            st.markdown(f"""
                            <div style="background-color: #e6f3ff; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                                <h4 style="margin-top: 0;">Summary</h4>
                                <p>{summary_text}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if st.button("✏️ Edit Summary", key="edit_summary_previous"):
                            st.session_state.editing_summary = True
                        
                        # Edit summary if requested
                        if 'editing_summary' in st.session_state and st.session_state.editing_summary:
                            with st.form(key="edit_summary_form_previous"):
                                st.subheader("Edit Summary")
                                edited_summary = st.text_area("Edit the summary:", value=insights_to_display['summary'], height=200)
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("Save Changes"):
                                        if 'edited_insights' not in st.session_state:
                                            st.session_state.edited_insights = insights_to_display.copy()
                                        st.session_state.edited_insights['summary'] = edited_summary
                                        del st.session_state.editing_summary
                                        st.success("Summary updated!")
                                        st.rerun()
                                with col2:
                                    if st.form_submit_button("Cancel"):
                                        del st.session_state.editing_summary
                                        st.rerun()
                        
                        # Display each question and answer in its own card with edit option
                        for i, insight in enumerate(insights_to_display['business_context_analysis']):
                            with st.expander(insight['question']):
                                st.markdown(insight['answer'])
                                if st.button("✏️ Edit Answer", key=f"edit_answer_previous_{i}"):
                                    st.session_state.editing_answer = insight.get('question_id', i)
                                    st.session_state.edited_answer = insight['answer']
                                    st.rerun()
                        
                        # Save to database button
                        if st.button("💾 Save Insights to Database", use_container_width=True, key="save_db_previous"):
                            success, message = save_insights_to_db(
                                selected_business, 
                                st.session_state.edited_insights if 'edited_insights' in st.session_state else insights_to_display
                            )
                            if success:
                                st.success(message)
                                # Set a flag in session state to indicate successful save
                                st.session_state.insights_saved = True
                                # Add a small delay to ensure the success message is shown
                                time.sleep(0.5)
                                # Refresh the page
                                st.rerun()
                            else:
                                st.error(message)
                        
                        # Option to download as JSON
                        st.download_button(
                            "📄 Download as JSON",
                            data=json.dumps(insights_to_display, indent=2),
                            file_name="business_context_analysis.json",
                            mime="application/json",
                            use_container_width=True
                        )
                else:
                    st.warning("No social media data found for the selected business.")
            else:
                st.warning("No businesses found in the database.")
                
        except Exception as e:
            st.error(f"Error querying database: {str(e)}")
    else:
        st.error("Could not connect to the database. Please check your connection settings.") 