import streamlit as st
import pandas as pd
import plotly.express as px
import os
import requests
import json
import base64
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from google import genai
from sqlalchemy import create_engine, text
import psycopg2
import warnings
import uuid
from datetime import date
import io

# Suppress SQLAlchemy warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Set page configuration
st.set_page_config(
    page_title="AI Content Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load external CSS file
def load_css(css_file):
    with open(css_file, 'r') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Load the CSS
css_path = os.path.join(os.path.dirname(__file__), 'static/css/style.css')
load_css(css_path)

# Add a custom header with logo and title
st.markdown("""
<div class="app-header">
    <div class="app-logo">✨</div>
    <div>
        <h1 class="app-title">AI Content Generator</h1>
        <p class="app-subtitle">Create engaging social media content with AI assistance</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Load environment variables
load_dotenv()

# Database connection
def get_db_connection():
    """Create a connection to the PostgreSQL database."""
    try:
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            st.error("Database connection string not found. Please check your .env file.")
            return None
        
        # Create engine
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

# Gemini AI API setup
def get_gemini_client():
    """Initialize and return a Gemini AI client."""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("Gemini API key not found. Please check your .env file.")
            return None
        
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        st.error(f"Error initializing Gemini client: {e}")
        return None

# Sidebar navigation
def sidebar_navigation():
    """Display the sidebar navigation."""
    st.sidebar.markdown("""
    <div class="sidebar-header">
        <div class="sidebar-logo">✨</div>
        <h2 class="sidebar-title">AI Content Generator</h2>
        <p class="sidebar-subtitle">Powered by Gemini AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("## Navigation")
    page = st.sidebar.radio(
        "Select a page",
        ["Content Generator", "Image Creator", "Data Analytics"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info("""
    This application uses AI to generate social media content and analyze engagement metrics.
    
    - **Content Generator**: Create new content with AI
    - **Image Creator**: Generate creative image concepts
    - **Data Analytics**: Analyze your social media performance
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Tips for Best Results")
    st.sidebar.success("""
    **For better AI-generated content:**
    
    1. Select a business with existing content
    2. Choose a specific product or service
    3. Provide detailed descriptions
    4. Select appropriate style, mood, and tone
    5. Increase reference content items for better learning
    """)
    
    return page

# Content Generator Page
def content_generator_page():
    """Display the content generator page."""
    st.markdown('<div class="generated-content">', unsafe_allow_html=True)
    st.title("AI Content Generator")
    st.write("Generate social media content ideas and captions using AI.")
    
    # Add a quick guide
    with st.expander("📚 How to Use This Tool", expanded=False):
        st.markdown("""
        ### Quick Guide to Generating Great Content
        
        1. **Select a Business**: Choose from existing businesses or enter a new one
        2. **Choose Platform**: Select the social media platform for your content
        3. **Select Product**: Choose a product or service to feature
        4. **Set Style Parameters**: Adjust style, mood, and tone to match your brand
        5. **Generate Content**: Click the button to create AI-powered content
        6. **Review & Edit**: The AI generates multiple options you can review and modify
        
        **Pro Tips:**
        - Provide detailed product descriptions for more targeted content
        - Use the reference content section to understand what works for your brand
        - Try different style combinations for variety in your content
        """)
    
    # Get database connection for fetching business names and reference content
    engine = get_db_connection()
    if not engine:
        st.error("Unable to connect to database. Some features may be limited.")
        businesses = []
        reference_content = pd.DataFrame()
        business_details = {}
    else:
        try:
            # Get a raw connection from the engine for pandas
            connection = engine.raw_connection()
            
            # Fetch business names from database
            business_query = """
            SELECT business_id, business_name 
            FROM businesses 
            ORDER BY business_name
            """
            businesses_df = pd.read_sql_query(business_query, connection)
            businesses = businesses_df.to_dict('records') if not businesses_df.empty else []
            
            # Close the connection when done
            connection.close()
        except Exception as e:
            st.warning(f"Could not fetch business data: {e}")
            businesses = []
            reference_content = pd.DataFrame()
            business_details = {}
    
    # Input fields
    col1, col2 = st.columns(2)
    
    with col1:
        # Business selection
        if businesses:
            business_options = [{"label": b["business_name"], "value": b["business_id"]} for b in businesses]
            selected_business = st.selectbox(
                "Select Business",
                options=[b["value"] for b in business_options],
                format_func=lambda x: next((b["label"] for b in business_options if b["value"] == x), x)
            )
            selected_business_name = next((b["label"] for b in business_options if b["value"] == selected_business), "")
        else:
            selected_business = st.text_input("Business ID")
            selected_business_name = st.text_input("Business Name")
        
        platform = st.selectbox(
            "Select Platform",
            ["Instagram", "TikTok", "Facebook", "Twitter", "LinkedIn"]
        )
        
        content_type = st.selectbox(
            "Content Type",
            ["video", "image", "text", "reel", "post"]
        )
        
        # Language selection with Thai as default
        language = st.selectbox(
            "Output Language",
            ["Thai", "English", "Mixed Thai-English"],
            index=0  # Default to Thai
        )
    
    with col2:
        # Replace Style/Mood/Tone dropdowns with a single text input for content preferences
        st.markdown("### Content Preferences (Optional)")
        content_preferences = st.text_area(
            "Describe your preferred style, mood, or tone",
            placeholder="e.g., 'Professional and friendly', 'Casual and humorous', or leave blank to match your brand's existing style",
            help="Describe how you want your content to sound. If left blank, we'll generate content that matches your brand's existing style."
        )
        
        # Add a note about multiple variations
        st.info("We'll generate 3 different content variations for you to choose from.")
    
    # Product selection section
    with st.expander("Product Information", expanded=False):
        # Initialize session state for products if it doesn't exist
        if 'products' not in st.session_state or st.session_state.get('current_business') != selected_business:
            st.session_state.products = []
            st.session_state.current_business = selected_business
            
            # Extract products from database
            if engine and selected_business:
                try:
                    # Get a raw connection from the engine for pandas
                    connection = engine.raw_connection()
                    
                    # Try to fetch products from a products table if it exists
                    try:
                        products_query = f"""
                        SELECT product_name, product_description
                        FROM products
                        WHERE business_id = '{selected_business}'
                        ORDER BY product_name
                        """
                        products_df = pd.read_sql_query(products_query, connection)
                        if not products_df.empty:
                            st.session_state.products = products_df.to_dict('records')
                    except Exception:
                        # If products table doesn't exist, try to extract product mentions from content
                        product_extraction_query = f"""
                        SELECT DISTINCT full_content, created_at
                        FROM social_media_content
                        WHERE business_id = '{selected_business}'
                        ORDER BY created_at DESC
                        LIMIT 20
                        """
                        content_df = pd.read_sql_query(product_extraction_query, connection)
                        
                        # Close the connection when done
                        connection.close()
                        
                        if not content_df.empty:
                            # Use AI to extract product mentions from content
                            all_content = "\n\n".join(content_df['full_content'].tolist())
                            
                            # Only attempt extraction if we have a Gemini client
                            client = get_gemini_client()
                            if client:
                                try:
                                    extraction_prompt = f"""
                                    Extract a list of products or services mentioned in the following social media content for {selected_business_name}.
                                    Only extract actual products or services, not general topics.
                                    Format the response as a simple list of product/service names, one per line.
                                    
                                    Content:
                                    {all_content}
                                    """
                                    
                                    extraction_response = client.models.generate_content(
                                        model="gemini-2.0-flash",
                                        contents=extraction_prompt
                                    )
                                    
                                    # Parse the response into a list of products
                                    extracted_products = [
                                        line.strip() for line in extraction_response.text.split('\n') 
                                        if line.strip() and not line.strip().startswith('-')
                                    ]
                                    
                                    # Convert to the same format as if from database
                                    st.session_state.products = [{"product_name": p, "product_description": ""} for p in extracted_products]
                                except Exception as e:
                                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                                        st.warning("""
                                        Gemini AI Service Temporarily Unavailable for product extraction.
                                        The AI service is currently experiencing high demand or maintenance.
                                        You can still manually enter product names.
                                        """)
                                    else:
                                        st.warning(f"Could not extract products using AI: {e}")
                except Exception as e:
                    st.warning(f"Could not fetch products: {e}")
        
        # Use the products from session state
        products = st.session_state.products
        
        # Product selection
        product_options = [""] + [p["product_name"] for p in products]
        
        # Initialize session state for selected product if it doesn't exist
        if 'selected_product' not in st.session_state:
            st.session_state.selected_product = ""
        
        # Use proper label for the selectbox
        selected_product = st.selectbox(
            "Select Product (optional)",
            options=product_options,
            index=product_options.index(st.session_state.selected_product) if st.session_state.selected_product in product_options else 0,
            help="Select a product to focus the content on, or leave blank to let the AI decide based on popular products",
            key="product_selectbox"
        )
        
        # Update the session state when selection changes
        st.session_state.selected_product = selected_product
        
        # Custom product input
        if 'custom_product' not in st.session_state:
            st.session_state.custom_product = ""
        
        # Use proper label for the input
        custom_product = st.text_input(
            "Or enter a custom product/service",
            value=st.session_state.custom_product,
            help="If your product isn't in the list, enter it here",
            key="custom_product_input"
        )
        
        # Update the session state
        st.session_state.custom_product = custom_product
        
        # Product description
        if 'product_description' not in st.session_state:
            st.session_state.product_description = ""
        
        # Use proper label for the text area
        if selected_product and selected_product in [p["product_name"] for p in products]:
            product_desc = next((p["product_description"] for p in products if p["product_name"] == selected_product), "")
            product_description = st.text_area(
                "Product Description (optional)",
                value=product_desc if not st.session_state.product_description else st.session_state.product_description,
                help="Provide details about the product to help the AI generate better content",
                key="product_description_area"
            )
        else:
            product_description = st.text_area(
                "Product Description (optional)",
                value=st.session_state.product_description,
                help="Provide details about the product to help the AI generate better content",
                key="product_description_area"
            )
        
        # Update the session state
        st.session_state.product_description = product_description
        
        # Use proper label for the hashtags input
        hashtags_input = st.text_area(
            "Hashtags (comma separated)",
            key="hashtags_input"
        )
        
        # Use proper label for the additional context input
        additional_context = st.text_area(
            "Additional Context for Content",
            key="additional_context_input"
        )
    
    # Fetch business details for AI learning
    business_details = {}
    if engine and selected_business:
        try:
            # Get a raw connection from the engine for pandas
            connection = engine.raw_connection()
            
            # Fetch business details - removing industries table join
            business_details_query = f"""
            SELECT *
            FROM businesses
            WHERE business_id = '{selected_business}'
            """
            
            business_details_df = pd.read_sql_query(business_details_query, connection)
            
            if not business_details_df.empty:
                business_details = business_details_df.iloc[0].to_dict()
                
                # Fetch additional business metrics if available
                metrics_query = f"""
                SELECT 
                    platform,
                    COUNT(*) as content_count,
                    AVG(likes_count) as avg_likes,
                    AVG(comments_count) as avg_comments,
                    AVG(shares_count) as avg_shares
                FROM social_media_content
                WHERE business_id = '{selected_business}'
                GROUP BY platform
                """
                
                metrics_df = pd.read_sql_query(metrics_query, connection)
                if not metrics_df.empty:
                    business_details['metrics'] = metrics_df.to_dict('records')
                
                # Fetch most common hashtags
                hashtags_query = f"""
                SELECT 
                    hashtags,
                    COUNT(*) as frequency
                FROM social_media_content
                WHERE business_id = '{selected_business}' AND hashtags IS NOT NULL AND hashtags != ''
                GROUP BY hashtags
                ORDER BY frequency DESC
                LIMIT 5
                """
                
                hashtags_df = pd.read_sql_query(hashtags_query, connection)
                if not hashtags_df.empty:
                    business_details['common_hashtags'] = hashtags_df.to_dict('records')
            
            # Close the connection when done
            connection.close()
        except Exception as e:
            st.warning(f"Could not fetch business details: {e}")
            business_details = {}
    
    # Display business details for learning
    if business_details:
        with st.expander("Business Details for AI Learning", expanded=False):
            st.subheader(f"About {selected_business_name}")
            
            # Display basic business info
            if 'business_description' in business_details and business_details['business_description']:
                st.markdown("**Business Description:**")
                st.write(business_details['business_description'])
            
            # Display metrics if available
            if 'metrics' in business_details:
                st.markdown("**Content Performance Metrics:**")
                metrics_df = pd.DataFrame(business_details['metrics'])
                st.dataframe(metrics_df)
            
            # Display common hashtags
            if 'common_hashtags' in business_details:
                st.markdown("**Commonly Used Hashtags:**")
                hashtags_list = [h['hashtags'] for h in business_details['common_hashtags']]
                st.write(", ".join(hashtags_list))
    
    # Add a control for the number of reference content items
    st.sidebar.subheader("AI Learning Settings")
    reference_count = st.sidebar.slider(
        "Number of Reference Content Items",
        min_value=1,
        max_value=20,
        value=10,
        help="Control how many content items the AI will learn from. More items may improve quality but increase processing time."
    )
    
    # Split the reference count between business-specific and general content
    business_specific_count = reference_count // 2
    general_count = reference_count - business_specific_count
    
    # Fetch reference content based on selected business
    reference_content = pd.DataFrame()
    if engine and selected_business:
        try:
            # Get a raw connection from the engine for pandas
            connection = engine.raw_connection()
            
            # Fetch popular content for reference filtered by business
            # Get more items than needed to account for filtering
            fetch_multiplier = 2  # Get 2x the items to ensure we have enough after filtering
            
            popular_content_query = f"""
            SELECT business_id, platform, content_type, full_content, hashtags, 
                   likes_count, comments_count, shares_count, saves_count, views_count,
                   (likes_count + views_count + comments_count + shares_count + saves_count) as engagement_score,
                   created_at
            FROM social_media_content
            WHERE business_id = '{selected_business}'
            AND full_content IS NOT NULL AND full_content != ''
            ORDER BY likes_count DESC
            LIMIT {business_specific_count * fetch_multiplier}
            """
            business_content = pd.read_sql_query(popular_content_query, connection)
            
            # Also get some generally popular content
            general_content_query = f"""
            SELECT business_id, platform, content_type, full_content, hashtags, 
                   likes_count, comments_count, shares_count, saves_count, views_count,
                   (likes_count + views_count + comments_count + shares_count + saves_count) as engagement_score,
                   created_at
            FROM social_media_content
            WHERE business_id != '{selected_business}'
            AND full_content IS NOT NULL AND full_content != ''
            ORDER BY likes_count DESC
            LIMIT {general_count * fetch_multiplier}
            """
            general_content = pd.read_sql_query(general_content_query, connection)
            
            # Combine and deduplicate
            reference_content = pd.concat([business_content, general_content]).drop_duplicates()
            
            # Close the connection when done
            connection.close()
        except Exception as e:
            st.warning(f"Could not fetch reference content: {e}")
            reference_content = pd.DataFrame()
    
    # Reference content section
    if not reference_content.empty:
        # Filter out content with empty content
        reference_content = reference_content[reference_content['full_content'].notna() & (reference_content['full_content'] != '')]
        
        # Sort by likes if available
        if 'likes_count' in reference_content.columns:
            reference_content = reference_content.sort_values(by='likes_count', ascending=False)
        
        # Ensure we have exactly the requested number of items
        business_specific = reference_content[reference_content['business_id'] == selected_business].head(business_specific_count)
        general_popular = reference_content[reference_content['business_id'] != selected_business].head(general_count)
        
        # If we don't have enough business-specific content, get more general content
        if len(business_specific) < business_specific_count:
            additional_general_count = business_specific_count - len(business_specific)
            general_popular = reference_content[reference_content['business_id'] != selected_business].head(general_count + additional_general_count)
        
        # If we don't have enough general content, get more business-specific content
        if len(general_popular) < general_count:
            additional_business_count = general_count - len(general_popular)
            business_specific = reference_content[reference_content['business_id'] == selected_business].head(business_specific_count + additional_business_count)
        
        # Combine the filtered content
        reference_content = pd.concat([business_specific, general_popular])
        
        if not reference_content.empty:
            with st.expander(f"AI Learning & Reference Content ({len(reference_content)} items)", expanded=False):
                st.markdown("""
                ### How AI Uses This Content
                
                The AI analyzes these high-performing content examples to:
                - Learn the brand's voice and style
                - Understand what content generates engagement
                - Identify successful content patterns
                - Incorporate effective hashtags and keywords
                
                This helps generate more relevant and engaging content for your business.
                """)
                
                # Add tabs for business-specific and general content
                tab1, tab2 = st.tabs(["Business-Specific Content", "General Popular Content"])
                
                # Business-specific content
                with tab1:
                    business_specific = reference_content[reference_content['business_id'] == selected_business]
                    if not business_specific.empty:
                        for idx, row in business_specific.iterrows():
                            # Skip empty content (should be already filtered, but just in case)
                            if pd.isna(row['full_content']) or row['full_content'] == '':
                                continue
                                
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"**Platform:** {row['platform']} | **Type:** {row['content_type']}")
                                st.text_area("Content", value=row['full_content'], height=100, key=f"ref_business_{row['business_id']}_{idx}")
                                
                                # Display hashtags with better extraction
                                if 'hashtags' in row and row['hashtags']:
                                    st.markdown(f"**Hashtags:** {row['hashtags']}")
                                else:
                                    # Try to extract hashtags from content
                                    content_hashtags = [word.strip() for word in row['full_content'].split() if word.strip().startswith('#')]
                                    if content_hashtags:
                                        hashtag_str = ', '.join(content_hashtags)
                                        st.markdown(f"**Extracted Hashtags:** {hashtag_str}")
                            
                            with col2:
                                # Just display likes for simplicity
                                # Try different ways to access likes
                                if 'likes_count' in row:
                                    likes = row['likes_count']
                                    if pd.notna(likes) and likes != '':
                                        likes = int(likes)
                                    else:
                                        likes = 0
                                else:
                                    # Try alternative column names
                                    for col in ['likes', 'like_count', 'like_counts']:
                                        if col in row and pd.notna(row[col]) and row[col] != '':
                                            likes = int(row[col])
                                            break
                                    else:
                                        likes = 0
                                
                                st.metric("Likes", likes)
                            
                            st.markdown("---")
                    else:
                        st.info("No business-specific content available for reference.")
                
                # General popular content
                with tab2:
                    general_content = reference_content[reference_content['business_id'] != selected_business]
                    if not general_content.empty:
                        for idx, row in general_content.iterrows():
                            # Skip empty content (should be already filtered, but just in case)
                            if pd.isna(row['full_content']) or row['full_content'] == '':
                                continue
                                
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"**Platform:** {row['platform']} | **Type:** {row['content_type']}")
                                st.text_area("Content", value=row['full_content'], height=100, key=f"ref_general_{row['business_id']}_{idx}")
                                
                                # Display hashtags with better extraction
                                if 'hashtags' in row and row['hashtags']:
                                    st.markdown(f"**Hashtags:** {row['hashtags']}")
                                else:
                                    # Try to extract hashtags from content
                                    content_hashtags = [word.strip() for word in row['full_content'].split() if word.strip().startswith('#')]
                                    if content_hashtags:
                                        hashtag_str = ', '.join(content_hashtags)
                                        st.markdown(f"**Extracted Hashtags:** {hashtag_str}")
                            
                            with col2:
                                # Just display likes for simplicity
                                # Try different ways to access likes
                                if 'likes_count' in row:
                                    likes = row['likes_count']
                                    if pd.notna(likes) and likes != '':
                                        likes = int(likes)
                                    else:
                                        likes = 0
                                else:
                                    # Try alternative column names
                                    for col in ['likes', 'like_count', 'like_counts']:
                                        if col in row and pd.notna(row[col]) and row[col] != '':
                                            likes = int(row[col])
                                            break
                                    else:
                                        likes = 0
                                
                                st.metric("Likes", likes)
                            
                            st.markdown("---")
                    else:
                        st.info("No general popular content available for reference.")
                
                # Add a section explaining how this content influences the AI
                st.markdown("""
                ### How This Influences Generated Content
                
                When you click "Generate Content", the AI will:
                1. Analyze these examples for patterns
                2. Consider your selected platform, style, mood, and tone
                3. Incorporate business context and hashtags
                4. Create new content that follows successful patterns while being unique
                
                The more high-quality reference content available, the better the AI's output will be.
                """)
        else:
            st.warning("No non-empty reference content available.")
    
    # Generate button
    if st.button("Generate Content"):
        if not selected_business:
            st.warning("Please select or enter a Business.")
            return
        
        client = get_gemini_client()
        if not client:
            return
        
        with st.spinner("Generating content..."):
            try:
                # Prepare business context from details
                business_context = ""
                if business_details:
                    business_context = f"""
                    Business Name: {selected_business_name}
                    """
                    
                    if 'business_description' in business_details and business_details['business_description']:
                        business_context += f"""
                        Business Description: {business_details['business_description']}
                        """
                    
                    if 'common_hashtags' in business_details:
                        hashtags_list = [h['hashtags'] for h in business_details['common_hashtags']]
                        business_context += f"""
                        Commonly Used Hashtags: {', '.join(hashtags_list)}
                        """
                
                # Prepare product context
                product_context = ""
                final_product = selected_product if selected_product else custom_product
                
                if final_product:
                    product_context = f"""
                    Product/Service: {final_product}
                    """
                    
                    if product_description:
                        product_context += f"""
                        Product Description: {product_description}
                        """
                else:
                    # If no product specified, instruct AI to reference popular products
                    product_context = """
                    No specific product selected. Please reference popular products or services from the business 
                    based on the reference content or business information.
                    """
                
                # Get reference content if available
                reference_text = ""
                if not reference_content.empty:
                    # Filter for business-specific content first
                    business_specific = reference_content[reference_content['business_id'] == selected_business]
                    
                    # Prepare reference text from all available content
                    reference_text = "Reference from popular content:\n\n"
                    
                    # Add business-specific content first (more relevant)
                    if not business_specific.empty:
                        reference_text += "Business-specific content:\n"
                        for i, row in business_specific.head(3).iterrows():  # Limit to top 3 for prompt size
                            reference_text += f"""
                            Platform: {row['platform']}
                            Content Type: {row['content_type']}
                            Content: {row['full_content']}
                            Hashtags: {row['hashtags'] if pd.notna(row['hashtags']) else ''}
                            ---
                            """
                    
                    # Add general popular content
                    general_content = reference_content[reference_content['business_id'] != selected_business]
                    if not general_content.empty:
                        reference_text += "\nGeneral popular content:\n"
                        for i, row in general_content.head(2).iterrows():  # Limit to top 2 for prompt size
                            reference_text += f"""
                            Platform: {row['platform']}
                            Content Type: {row['content_type']}
                            Content: {row['full_content']}
                            Hashtags: {row['hashtags'] if pd.notna(row['hashtags']) else ''}
                            ---
                            """
                    
                    # Add instruction for AI
                    reference_text += """
                    Learn from these examples to create content that matches the style and tone,
                    but create something unique and original.
                    """
                
                # Prepare style/mood/tone context
                style_context = ""
                if content_preferences:
                    style_context = f"Content Preferences: {content_preferences}"
                else:
                    style_context = "Content Preferences: Match the brand's existing style and tone"
                
                # Language instruction
                language_instruction = ""
                if language == "Thai":
                    language_instruction = "Generate the content in Thai language only."
                elif language == "English":
                    language_instruction = "Generate the content in English language only."
                elif language == "Mixed Thai-English":
                    language_instruction = "Generate the content in a mix of Thai and English languages, with Thai being the primary language."
                
                # Prepare base prompt
                base_prompt = f"""
                {language_instruction}
                
                Generate social media content for {platform} as a {content_type}.
                {style_context}
                
                Business Information:
                {business_context}
                
                {product_context}
                
                Additional context: {additional_context}
                
                Include relevant hashtags based on: {hashtags_input}
                
                Make the content engaging and optimized for the platform.
                
                {reference_text}
                """
                
                # Create 3 different variations with different styles
                variation_prompts = [
                    base_prompt + "\nCreate content that is professional and informative.",
                    base_prompt + "\nCreate content that is casual and friendly.",
                    base_prompt + "\nCreate content that is creative and engaging."
                ]
                
                # Call Gemini API for each variation
                try:
                    generated_contents = []
                    extracted_hashtags_list = []
                    
                    for i, prompt in enumerate(variation_prompts):
                        with st.spinner(f"Generating variation {i+1}..."):
                            response = client.models.generate_content(
                                model="gemini-2.0-flash",
                                contents=prompt
                            )
                            
                            # Store generated content
                            generated_content = response.text
                            generated_contents.append(generated_content)
                            
                            # Extract hashtags if present
                            variation_hashtags = hashtags_input
                            if not variation_hashtags and "#" in generated_content:
                                # Try to extract hashtags from the generated content
                                potential_hashtags = [word.strip() for word in generated_content.split() if word.startswith("#")]
                                if potential_hashtags:
                                    variation_hashtags = ",".join([tag.replace("#", "") for tag in potential_hashtags])
                            
                            extracted_hashtags_list.append(variation_hashtags)
                    
                    # Display content with tabs for each variation
                    st.subheader("Generated Content Variations:")
                    
                    # Create tabs for each variation
                    tabs = st.tabs([f"Variation {i+1}" for i in range(len(generated_contents))])
                    
                    # Display content in each tab
                    for i, tab in enumerate(tabs):
                        with tab:
                            st.markdown(f"**Style: {'Professional & Informative' if i == 0 else 'Casual & Friendly' if i == 1 else 'Creative & Engaging'}**")
                            st.write(generated_contents[i])
                            
                            # Display extracted hashtags if any
                            if extracted_hashtags_list[i]:
                                st.markdown("**Extracted Hashtags:**")
                                st.write(extracted_hashtags_list[i])
                    
                    # Display note about read-only mode
                    st.info("This application is in read-only mode. Content cannot be saved to the database.")
                
                except Exception as e:
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        st.error("""
                        ### Gemini AI Service Temporarily Unavailable
                        
                        The AI service is currently experiencing high demand or maintenance. Please try again in a few minutes.
                        
                        **Alternative options:**
                        - Try refreshing the page
                        - Try a different browser
                        - Check your internet connection
                        - Try again later when the service load may be lower
                        
                        Technical details: {e}
                        """)
                    else:
                        st.error(f"Error calling AI service: {e}")
                
            except Exception as e:
                st.error(f"Error preparing content generation: {e}")

# Data Analytics Page
def data_analytics_page():
    """Display the data analytics page."""
    st.markdown('<div class="generated-content">', unsafe_allow_html=True)
    st.title("Social Media Content Analytics")
    st.write("Analyze and visualize your social media content data.")
    
    # Add a quick guide
    with st.expander("📊 How to Use Analytics", expanded=False):
        st.markdown("""
        ### Quick Guide to Analytics
        
        1. **Select a Business**: Choose the business to analyze
        2. **Filter by Platform**: Narrow down results by social media platform
        3. **Review Metrics**: Examine engagement metrics across platforms
        4. **Analyze Content Types**: See which content formats perform best
        5. **Explore Top Content**: Study your most successful posts
        6. **Identify Trends**: Look for patterns in hashtag usage and engagement
        
        **Pro Tips:**
        - Compare metrics across different platforms to optimize your strategy
        - Use the top content examples as inspiration for new posts
        - Pay attention to which hashtags drive the most engagement
        """)
    
    # Get database connection
    engine = get_db_connection()
    if not engine:
        return
    
    # Business selection
    try:
        # Get a raw connection from the engine for pandas
        connection = engine.raw_connection()
        
        # Fetch business names from database
        business_query = """
        SELECT business_id, business_name 
        FROM businesses 
        ORDER BY business_name
        """
        businesses_df = pd.read_sql_query(business_query, connection)
        
        # Close the connection
        connection.close()
        
        if not businesses_df.empty:
            business_options = [{"label": b["business_name"], "value": b["business_id"]} for b in businesses_df.to_dict('records')]
            selected_business = st.selectbox(
                "Select Business",
                options=[b["value"] for b in business_options],
                format_func=lambda x: next((b["label"] for b in business_options if b["value"] == x), x)
            )
            selected_business_name = next((b["label"] for b in business_options if b["value"] == selected_business), "")
        else:
            st.warning("No businesses found in the database.")
            return
    except Exception as e:
        st.error(f"Error fetching businesses: {e}")
        return
    
    # Platform filter
    st.subheader("Filter Data")
    platforms = ["All", "Instagram", "TikTok", "Facebook", "Twitter", "LinkedIn"]
    selected_platform = st.selectbox("Platform", platforms)
    
    # Apply filters
    platform_filter = "" if selected_platform == "All" else f"AND platform = '{selected_platform}'"
    
    try:
        # Get a raw connection from the engine for pandas
        connection = engine.raw_connection()
        
        # Fetch content data with filters
        content_query = f"""
        SELECT business_id, platform, content_type, full_content, hashtags, 
               COALESCE(likes_count, 0) as likes_count, 
               COALESCE(comments_count, 0) as comments_count, 
               COALESCE(shares_count, 0) as shares_count, 
               COALESCE(saves_count, 0) as saves_count, 
               COALESCE(views_count, 0) as views_count,
               url, created_at
        FROM social_media_content
        WHERE business_id = '{selected_business}'
        {platform_filter}
        ORDER BY created_at DESC
        """
        content_df = pd.read_sql_query(content_query, connection)
        
        # Get max engagement values for reference
        max_engagement_query = f"""
        SELECT 
            MAX(likes_count) as max_likes,
            MAX(comments_count) as max_comments,
            MAX(shares_count) as max_shares,
            MAX(saves_count) as max_saves,
            MAX(views_count) as max_views
        FROM social_media_content
        WHERE business_id = '{selected_business}'
        {platform_filter}
        """
        max_engagement_df = pd.read_sql_query(max_engagement_query, connection)
        
        # Get engagement metrics by platform - using simple aggregations
        platform_metrics_query = f"""
        SELECT 
            platform, 
            COUNT(*) as post_count,
            SUM(COALESCE(likes_count, 0)) as total_likes,
            SUM(COALESCE(comments_count, 0)) as total_comments,
            SUM(COALESCE(shares_count, 0)) as total_shares,
            SUM(COALESCE(saves_count, 0)) as total_saves,
            SUM(COALESCE(views_count, 0)) as total_views,
            MAX(COALESCE(likes_count, 0)) as max_likes,
            MAX(COALESCE(comments_count, 0)) as max_comments,
            MAX(COALESCE(shares_count, 0)) as max_shares,
            MAX(COALESCE(saves_count, 0)) as max_saves,
            MAX(COALESCE(views_count, 0)) as max_views
        FROM social_media_content
        WHERE business_id = '{selected_business}'
        {platform_filter}
        GROUP BY platform
        """
        platform_metrics_df = pd.read_sql_query(platform_metrics_query, connection)
        
        # Calculate averages in Python for more control
        if not platform_metrics_df.empty:
            for metric in ['likes', 'comments', 'shares', 'saves', 'views']:
                platform_metrics_df[f'avg_{metric}'] = (
                    platform_metrics_df[f'total_{metric}'] / 
                    platform_metrics_df['post_count']
                ).round().astype(int)
        
        # Get content type distribution
        content_type_query = f"""
        SELECT content_type, COUNT(*) as count
        FROM social_media_content
        WHERE business_id = '{selected_business}'
        {platform_filter}
        GROUP BY content_type
        """
        content_type_df = pd.read_sql_query(content_type_query, connection)
        
        # Get all hashtags for processing individual words
        hashtag_query = f"""
        SELECT hashtags
        FROM social_media_content
        WHERE business_id = '{selected_business}'
        {platform_filter}
        AND hashtags IS NOT NULL AND hashtags != ''
        """
        hashtag_df = pd.read_sql_query(hashtag_query, connection)
        
        # Get all content for calculating engagement score in Python
        all_content_query = f"""
        SELECT business_id, platform, content_type, full_content, hashtags, 
               COALESCE(likes_count, 0) as likes_count, 
               COALESCE(comments_count, 0) as comments_count, 
               COALESCE(shares_count, 0) as shares_count, 
               COALESCE(saves_count, 0) as saves_count, 
               COALESCE(views_count, 0) as views_count,
               url, created_at
        FROM social_media_content
        WHERE business_id = '{selected_business}'
        {platform_filter}
        """
        all_content_df = pd.read_sql_query(all_content_query, connection)
        
        # Close the connection when done
        connection.close()
        
        # Calculate engagement score in Python for consistency
        if not all_content_df.empty:
            # Define the engagement score formula
            all_content_df['engagement_score'] = (
                all_content_df['likes_count'] + 
                all_content_df['comments_count'] * 2 + 
                all_content_df['shares_count'] * 3 + 
                all_content_df['saves_count'] * 2
            )
            
            # Get top 5 by engagement score
            popular_content_df = all_content_df.sort_values('engagement_score', ascending=False).head(5)
        else:
            popular_content_df = pd.DataFrame()
        
        # Process hashtags to extract individual words
        hashtag_words = []
        if not hashtag_df.empty:
            for _, row in hashtag_df.iterrows():
                if pd.notna(row['hashtags']) and row['hashtags']:
                    # Split by commas and then clean each hashtag
                    tags = row['hashtags'].split(',')
                    for tag in tags:
                        clean_tag = tag.strip().lower()
                        if clean_tag and not clean_tag.startswith('#'):
                            clean_tag = '#' + clean_tag
                        if clean_tag:
                            hashtag_words.append(clean_tag)
            
            # Count occurrences of each hashtag
            if hashtag_words:
                hashtag_counts = pd.Series(hashtag_words).value_counts().reset_index()
                hashtag_counts.columns = ['hashtag', 'count']
                hashtag_counts = hashtag_counts.head(10)  # Get top 10
            else:
                hashtag_counts = pd.DataFrame(columns=['hashtag', 'count'])
        else:
            hashtag_counts = pd.DataFrame(columns=['hashtag', 'count'])
        
        # Display analytics
        st.subheader(f"Analytics for {selected_business_name}")
        
        # Calculate metrics directly from the dataframe for accuracy
        total_posts = len(content_df)
        total_likes = content_df['likes_count'].sum()
        total_comments = content_df['comments_count'].sum()
        total_shares = content_df['shares_count'].sum()
        total_views = content_df['views_count'].sum()
        
        avg_likes = int(total_likes / total_posts) if total_posts > 0 else 0
        avg_comments = int(total_comments / total_posts) if total_posts > 0 else 0
        avg_shares = int(total_shares / total_posts) if total_posts > 0 else 0
        avg_views = int(total_views / total_posts) if total_posts > 0 else 0
        
        max_likes = content_df['likes_count'].max() if not content_df.empty else 0
        max_comments = content_df['comments_count'].max() if not content_df.empty else 0
        max_shares = content_df['shares_count'].max() if not content_df.empty else 0
        max_views = content_df['views_count'].max() if not content_df.empty else 0
        
        # Summary metrics
        st.markdown("### Summary Metrics")
        metric_cols = st.columns(5)
        with metric_cols[0]:
            st.metric("Total Posts", total_posts)
        with metric_cols[1]:
            st.metric("Avg. Likes", avg_likes, f"Max: {max_likes}")
        with metric_cols[2]:
            st.metric("Avg. Comments", avg_comments, f"Max: {max_comments}")
        with metric_cols[3]:
            st.metric("Avg. Shares", avg_shares, f"Max: {max_shares}")
        with metric_cols[4]:
            st.metric("Avg. Views", avg_views, f"Max: {max_views}")
        
        # Detailed metrics
        with st.expander("Detailed Metrics"):
            st.markdown("#### Total Engagement")
            st.markdown(f"Total Likes: {total_likes}")
            st.markdown(f"Total Comments: {total_comments}")
            st.markdown(f"Total Shares: {total_shares}")
            st.markdown(f"Total Views: {total_views}")
            
            st.markdown("#### Maximum Values")
            st.markdown(f"Max Likes: {max_likes}")
            st.markdown(f"Max Comments: {max_comments}")
            st.markdown(f"Max Shares: {max_shares}")
            st.markdown(f"Max Views: {max_views}")
            
            # Show raw data
            st.markdown("#### Raw Engagement Data")
            st.dataframe(content_df[['platform', 'likes_count', 'comments_count', 'shares_count', 'views_count']].sort_values('likes_count', ascending=False).head(10))
        
        # Platform metrics
        if not platform_metrics_df.empty:
            st.markdown("### Performance by Platform")
            
            fig1 = px.bar(
                platform_metrics_df, 
                x='platform', 
                y=['avg_likes', 'avg_comments', 'avg_shares', 'avg_saves'],
                barmode='group',
                title="Average Engagement by Platform"
            )
            st.plotly_chart(fig1)
            
            # Show platform metrics table
            with st.expander("Platform Metrics Details"):
                st.dataframe(platform_metrics_df[['platform', 'post_count', 'avg_likes', 'avg_comments', 'avg_shares', 'max_likes', 'max_comments', 'max_shares']])
        
        # Content type distribution
        if not content_type_df.empty:
            st.markdown("### Content Type Distribution")
            fig2 = px.pie(
                content_type_df, 
                values='count', 
                names='content_type',
                title="Content Types"
            )
            st.plotly_chart(fig2)
        
        # Top hashtags - individual words
        if not hashtag_counts.empty:
            st.markdown("### Top Hashtags")
            fig3 = px.bar(
                hashtag_counts, 
                x='hashtag', 
                y='count',
                title="Most Used Hashtags"
            )
            st.plotly_chart(fig3)
        
        # Top 5 most popular content - use the same platform filter as main filter
        if not popular_content_df.empty:
            st.markdown("### Top 5 Most Popular Content")
            
            # Display content with URL link only (no preview)
            for idx, row in popular_content_df.iterrows():
                # Calculate engagement components for verification
                likes = int(row['likes_count'])
                comments = int(row['comments_count'])
                shares = int(row['shares_count'])
                saves = int(row['saves_count'])
                
                # Calculate engagement score for display
                engagement_score = likes + (comments * 2) + (shares * 3) + (saves * 2)
                
                with st.expander(f"#{idx+1} - {row['platform']} - {row['content_type']} - Engagement Score: {engagement_score}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Content:**")
                        st.text_area("", value=row['full_content'], height=100, key=f"content_{idx}")
                        
                        if pd.notna(row['hashtags']) and row['hashtags']:
                            st.markdown(f"**Hashtags:** {row['hashtags']}")
                        
                        # Simple URL link without preview
                        if pd.notna(row['url']) and row['url']:
                            st.markdown(f"**URL:** [View Original Content]({row['url']})")
                    
                    with col2:
                        # Display engagement metrics
                        st.markdown("**Engagement:**")
                        st.metric("Likes", likes)
                        st.metric("Comments", comments)
                        st.metric("Shares", shares)
                        st.metric("Saves", saves)
                        
                        # Engagement score calculation is now hidden
                        # st.markdown("**Engagement Score Calculation:**")
                        # st.markdown(f"Likes: {likes}")
                        # st.markdown(f"Comments × 2: {comments} × 2 = {comments * 2}")
                        # st.markdown(f"Shares × 3: {shares} × 3 = {shares * 3}")
                        # st.markdown(f"Saves × 2: {saves} × 2 = {saves * 2}")
                        st.markdown(f"**Total Engagement Score: {engagement_score}**")
        else:
            st.info("No content found with the selected filters.")
    
    except Exception as e:
        st.error(f"Error fetching analytics data: {e}")
        import traceback
        st.error(traceback.format_exc())

# Image Creator Page
def image_creator_page():
    """Display the image creator page."""
    st.markdown('<div class="generated-content">', unsafe_allow_html=True)
    st.title("AI Image Concept Generator")
    st.write("Generate creative image concepts and create images using AI.")
    
    # Add a quick guide
    with st.expander("🎨 How to Use This Tool", expanded=False):
        st.markdown("""
        ### Quick Guide to Generating Image Concepts
        
        1. **Select a Business**: Choose from existing businesses or enter a new one
        2. **Choose Platform**: Select the social media platform for your image
        3. **Describe Your Idea**: Provide a brief description of what you're looking for
        4. **Generate Concept**: Click the button to create AI-powered image concepts
        5. **Create Image**: Use the generated prompt to create an actual image with Ideogram
        6. **Download & Use**: Download the generated images for your social media content
        
        **Pro Tips:**
        - Be specific about the mood, style, and elements you want in your image
        - Try different aspect ratios for different platforms (1:1 for Instagram, 16:9 for Twitter)
        - Use negative prompts to avoid unwanted elements in your images
        - Upload reference images to help the AI understand your visual style better
        """)
    
    # Get database connection for fetching business names
    engine = get_db_connection()
    if not engine:
        st.error("Unable to connect to database. Some features may be limited.")
        businesses = []
    else:
        try:
            # Get a raw connection from the engine for pandas
            connection = engine.raw_connection()
            
            # Fetch business names from database
            business_query = """
            SELECT business_id, business_name 
            FROM businesses 
            ORDER BY business_name
            """
            businesses_df = pd.read_sql_query(business_query, connection)
            businesses = businesses_df.to_dict('records') if not businesses_df.empty else []
            
            # Close the connection when done
            connection.close()
        except Exception as e:
            st.warning(f"Could not fetch business data: {e}")
            businesses = []
    
    # Create tabs for concept generation and image generation
    concept_tab, image_tab, storyboard_tab = st.tabs(["Generate Concept", "Create Image", "Create Storyboard"])
    
    with concept_tab:
        # Input fields
        col1, col2 = st.columns(2)
        
        with col1:
            # Business selection
            if businesses:
                business_options = [{"label": b["business_name"], "value": b["business_id"]} for b in businesses]
                selected_business = st.selectbox(
                    "Select Business",
                    options=[b["value"] for b in business_options],
                    format_func=lambda x: next((b["label"] for b in business_options if b["value"] == x), x)
                )
                selected_business_name = next((b["label"] for b in business_options if b["value"] == selected_business), "")
            else:
                selected_business = st.text_input("Business ID")
                selected_business_name = st.text_input("Business Name")
            
            platform = st.selectbox(
                "Select Platform",
                ["Instagram", "TikTok", "Facebook", "Twitter", "LinkedIn"]
            )
            
            image_purpose = st.selectbox(
                "Image Purpose",
                ["Product Showcase", "Brand Awareness", "Promotion", "Educational", "Lifestyle", "User Generated Content"]
            )
            
            # Multiple reference image upload
            st.markdown("### Reference Images (Optional)")
            st.write("Upload up to 5 reference images to help guide the AI. The system will analyze these images and incorporate their elements into your generated image.")
            
            # Initialize reference images in session state if not already there
            if 'reference_images' not in st.session_state:
                st.session_state.reference_images = []
                st.session_state.reference_descriptions = []
            
            # Create 5 file uploaders for reference images
            uploaded_images = []
            for i in range(5):
                uploaded_file = st.file_uploader(
                    f"Reference Image {i+1}",
                    type=["jpg", "jpeg", "png"],
                    key=f"ref_img_{i}"
                )
                if uploaded_file is not None:
                    uploaded_images.append(uploaded_file)
            
            # Display uploaded images in a grid
            if uploaded_images:
                st.write(f"{len(uploaded_images)} reference images uploaded")
                cols = st.columns(min(len(uploaded_images), 3))
                for i, img in enumerate(uploaded_images):
                    with cols[i % 3]:
                        st.image(img, caption=f"Reference {i+1}", width=150)
            
            # Button to analyze all images
            if uploaded_images and st.button("Analyze All Reference Images"):
                with st.spinner("Analyzing reference images... This may take a moment."):
                    # Clear previous descriptions
                    st.session_state.reference_images = []
                    st.session_state.reference_descriptions = []
                    
                    # Process each image
                    for i, img in enumerate(uploaded_images):
                        description_response = describe_image_with_ideogram(img)
                        
                        if description_response and "descriptions" in description_response:
                            # Store the image and description in session state
                            description_text = description_response["descriptions"][0]["text"]
                            st.session_state.reference_images.append(img)
                            st.session_state.reference_descriptions.append(description_text)
                            
                            # Display the description
                            st.markdown(f"### Reference Image {i+1} Description")
                            st.markdown(f"""
                            <div style="background-color: #f0f7ff; padding: 15px; border-radius: 5px; border-left: 5px solid #4285F4;">
                                <p style="font-family: monospace; margin: 0;">{description_text}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error(f"Failed to analyze Reference Image {i+1}. Please try again or use a different image.")
                    
                    if st.session_state.reference_descriptions:
                        st.success(f"Successfully analyzed {len(st.session_state.reference_descriptions)} reference images! These descriptions will be incorporated into your prompt.")
                    else:
                        st.error("Failed to analyze any reference images. Please try again with different images.")
        
        with col2:
            # Image concept description
            st.markdown("### Image Concept")
            image_concept = st.text_area(
                "Describe your image idea",
                placeholder="e.g., 'A minimalist product shot of our coffee mug with morning sunlight', or 'A lifestyle image showing our skincare routine in action'",
                help="Be as specific as possible about what you want to see in the image."
            )
            
            # Visual style preferences
            visual_style = st.text_area(
                "Visual Style Preferences (Optional)",
                placeholder="e.g., 'Bright and airy with pastel colors', 'Dark and moody with high contrast', or 'Minimalist with lots of white space'",
                help="Describe the visual style, colors, lighting, and mood you want for your image."
            )
            
            # Display reference image description if available
            if 'reference_image_description' in st.session_state:
                st.markdown("### Reference Image Description")
                st.markdown(f"""
                <div style="background-color: #f0f7ff; padding: 15px; border-radius: 5px; border-left: 5px solid #4285F4;">
                    <p style="font-family: monospace; margin: 0;">{st.session_state.reference_image_description}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Generate button
        if st.button("Generate Image Concept"):
            if not selected_business:
                st.warning("Please select or enter a Business.")
                return
            
            if not image_concept:
                st.warning("Please describe your image concept.")
                return
            
            client = get_gemini_client()
            if not client:
                return
            
            with st.spinner("Generating image concept..."):
                try:
                    # Prepare prompt for Gemini
                    reference_description = ""
                    if 'reference_image_description' in st.session_state:
                        reference_description = f"""
                        Reference Image Description: {st.session_state.reference_image_description}
                        
                        Please incorporate elements from this reference image description into your creative brief.
                        """
                    
                    # Update to handle multiple reference images
                    reference_description = ""
                    if 'reference_descriptions' in st.session_state and st.session_state.reference_descriptions:
                        reference_description = "Reference Image Descriptions:\n\n"
                        for i, desc in enumerate(st.session_state.reference_descriptions):
                            reference_description += f"Reference Image {i+1}: {desc}\n\n"
                        
                        reference_description += """
                        CRITICAL: You MUST faithfully reproduce the EXACT visual elements from these reference images.
                        Be extremely specific about objects, colors, styles, and layouts mentioned in the descriptions.
                        The final image MUST contain these elements exactly as they appear in the reference images.
                        """
                    else:
                        # Enhanced prompt for when no reference images are provided
                        reference_description = """
                        IMPORTANT: Since no reference images were provided, create a highly detailed and professional design with:
                        - Precise descriptions of visual elements (specific colors, objects, layouts)
                        - Professional composition and lighting
                        - Clear text placement and hierarchy
                        - Brand-appropriate styling
                        - Realistic and high-quality visual elements
                        """
                    
                    prompt = f"""
                    Create a detailed creative brief for a professional creative design to be used on {platform} for {selected_business_name}.
                    
                    Purpose: {image_purpose}
                    
                    Basic concept: {image_concept}
                    
                    Visual style preferences: {visual_style if visual_style else "Not specified"}
                    
                    {reference_description}
                    
                    Please structure your response with the following sections:
                    
                    1. Creative Ideation: Overall concept and creative direction
                    2. Content Pillars: Key themes and messages to convey
                    3. Mood and Tone: Emotional response and atmosphere
                    4. Concept Details: Specific visual elements, composition, and technical aspects
                    5. Headline: A catchy title for the image (25 characters or less)
                    6. Sub-Headline: Supporting text (50 characters or less)
                    7. Ideogram Prompt: A detailed prompt that could be used with AI image generators (150-200 characters). The image MUST include the business name "{selected_business_name}" and its logo prominently displayed in a professional manner suitable for social media posting.
                    8. Negative Prompt: Elements to avoid in the image generation (optional)
                    
                    Make it specific, detailed, and aligned with the brand's identity.
                    """
                    
                    # Enhanced prompt that includes text and professional design elements
                    prompt = f"""
                    Create a detailed creative brief for a professional business image to be used on {platform} for {selected_business_name}.
                    
                    Purpose: {image_purpose}
                    
                    Basic concept: {image_concept}
                    
                    Visual style preferences: {visual_style if visual_style else "Not specified"}
                    
                    {reference_description}
                    
                    Please structure your response with the following sections:
                    
                    1. Creative Ideation: Overall concept and creative direction
                    2. Content Pillars: Key themes and messages to convey
                    3. Mood and Tone: Emotional response and atmosphere
                    4. Concept Details: Specific visual elements, composition, and technical aspects, including:
                       - Layout recommendations (rule of thirds, centered, etc.)
                       - Color scheme suggestions (specific colors that work well for this brand)
                       - Typography style (font types that would work well)
                    5. Text Elements:
                       - Headline: A catchy title for the image (25 characters or less)
                       - Sub-Headline: Supporting text (50 characters or less)
                       - Call to Action: Brief text to encourage engagement (if applicable)
                       - Text Placement: Where text should appear in the image
                    6. Professional Design Elements:
                       - Logo placement suggestions
                       - UI/UX considerations (if for digital use)
                       - White space utilization
                       - Visual hierarchy recommendations
                    7. Ideogram Prompt: A detailed prompt that includes all text elements and design specifications (200-250 characters)
                       - Be sure to include TEXT: elements in the prompt to specify exact text that should appear in the image
                       - Include specific design instructions like "professional layout," "corporate style," etc.
                       - CRITICAL: When using elements from reference images, use EXACT descriptions like "EXACT SAME black table as in reference image" to ensure faithful reproduction
                    9. Negative Prompt: Elements to avoid in the image generation (optional)
                    
                    Make it specific, detailed, professional, and aligned with the brand's identity. The final image should look like it was professionally designed with integrated text elements.
                    """
                    
                    # Enhanced prompt that includes text and professional design elements with stronger emphasis on reference images
                    prompt = f"""
                    Create a detailed creative brief for a professional business image to be used on {platform} for {selected_business_name}.
                    
                    Purpose: {image_purpose}
                    
                    Basic concept: {image_concept}
                    
                    Visual style preferences: {visual_style if visual_style else "Not specified"}
                    
                    {reference_description}
                    
                    Please structure your response with the following sections:
                    
                    1. Creative Ideation: Overall concept and creative direction
                    2. Content Pillars: Key themes and messages to convey
                    3. Mood and Tone: Emotional response and atmosphere
                    4. Reference Elements: 
                       - Specific objects, colors, layouts, and design elements from the reference images that MUST be included
                       - How these elements will be incorporated faithfully into the final image
                    5. Concept Details: Specific visual elements, composition, and technical aspects, including:
                       - Layout recommendations (rule of thirds, centered, etc.)
                       - Color scheme suggestions (specific colors that work well for this brand)
                       - Typography style (font types that would work well)
                    6. Text Elements:
                       - Headline: A catchy title for the image (25 characters or less)
                       - Sub-Headline: Supporting text (50 characters or less)
                       - Call to Action: Brief text to encourage engagement (if applicable)
                       - Text Placement: Where text should appear in the image
                    7. Professional Design Elements:
                       - Logo placement suggestions
                       - UI/UX considerations (if for digital use)
                       - White space utilization
                       - Visual hierarchy recommendations
                    8. Ideogram Prompt: A detailed prompt that includes all text elements and design specifications (200-250 characters)
                       - Be sure to include TEXT: elements in the prompt to specify exact text that should appear in the image
                       - Include specific design instructions like "professional layout," "corporate style," etc.
                       - CRITICAL: When using elements from reference images, use EXACT descriptions like "EXACT SAME black table as in reference image" to ensure faithful reproduction
                    9. Negative Prompt: Elements to avoid in the image generation (optional)
                    
                    Make it specific, detailed, professional, and aligned with the brand's identity. The final image should look like it was professionally designed with integrated text elements and should faithfully reproduce key elements from the reference images.
                    """
                    
                    # Enhanced prompt for when no reference images are provided
                    if not ('reference_descriptions' in st.session_state and st.session_state.reference_descriptions):
                        reference_description = """
                        IMPORTANT: Since no reference images were provided, create a highly detailed and professional design with:
                        - Precise descriptions of visual elements (specific colors, objects, layouts)
                        - Professional composition and lighting
                        - Clear text placement and hierarchy
                        - Brand-appropriate styling
                        - Realistic and high-quality visual elements
                        """
                    
                    # Call Gemini API
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )
                    
                    # Store the response in session state for use in the image tab
                    st.session_state.concept_response = response.text
                    
                    # Display the response in a nicely formatted way
                    st.subheader("Generated Image Concept")
                    
                    # Parse the response to extract sections
                    concept_text = response.text
                    
                    # Display in tabs with updated names to better reflect the new content structure
                    tabs = st.tabs(["Complete Brief", "Creative Ideation", "Content & Mood", "Design Details", "Text & Prompts"])
                    
                    with tabs[0]:
                        st.markdown(concept_text)
                        
                    with tabs[1]:
                        # Extract Creative Ideation section
                        if "Creative Ideation:" in concept_text or "1. Creative Ideation:" in concept_text:
                            creative_section = concept_text.split("1. Creative Ideation:")[1].split("2. Content Pillars:")[0] if "1. Creative Ideation:" in concept_text else concept_text.split("Creative Ideation:")[1].split("Content Pillars:")[0]
                            st.markdown("### Creative Ideation")
                            st.markdown(creative_section)
                        else:
                            st.info("Creative ideation section not found in the generated content.")
                    
                    with tabs[2]:
                        # Extract Content Pillars and Mood sections
                        st.markdown("### Content Pillars")
                        if "Content Pillars:" in concept_text or "2. Content Pillars:" in concept_text:
                            content_section = concept_text.split("2. Content Pillars:")[1].split("3. Mood and Tone:")[0] if "2. Content Pillars:" in concept_text else concept_text.split("Content Pillars:")[1].split("Mood and Tone:")[0]
                            st.markdown(content_section)
                        else:
                            st.info("Content pillars section not found in the generated content.")
                        
                        st.markdown("### Mood and Tone")
                        if "Mood and Tone:" in concept_text or "3. Mood and Tone:" in concept_text:
                            mood_section = concept_text.split("3. Mood and Tone:")[1].split("4. Concept Details:")[0] if "3. Mood and Tone:" in concept_text else concept_text.split("Mood and Tone:")[1].split("Concept Details:")[0]
                            st.markdown(mood_section)
                        else:
                            st.info("Mood and tone section not found in the generated content.")
                    
                    with tabs[3]:
                        # Extract Concept Details
                        st.markdown("### Concept Details")
                        if "Concept Details:" in concept_text or "4. Concept Details:" in concept_text:
                            details_section = concept_text.split("4. Concept Details:")[1].split("5. Headline:")[0] if "4. Concept Details:" in concept_text else concept_text.split("Concept Details:")[1].split("Text Elements:")[0]
                            st.markdown(details_section)
                        else:
                            st.info("Concept details section not found in the generated content.")
                            
                        # Extract Professional Design Elements if available
                        st.markdown("### Professional Design Elements")
                        if "Professional Design Elements:" in concept_text or "6. Professional Design Elements:" in concept_text:
                            design_section = concept_text.split("6. Professional Design Elements:")[1].split("7. Ideogram Prompt:")[0] if "6. Professional Design Elements:" in concept_text else concept_text.split("Professional Design Elements:")[1].split("Ideogram Prompt:")[0]
                            st.markdown(design_section)
                        else:
                            st.info("Professional design elements section not found in the generated content.")

                    with tabs[3]:
                        # Extract Reference Elements if available (new format)
                        if "Reference Elements:" in concept_text or "4. Reference Elements:" in concept_text:
                            st.markdown("### Reference Elements")
                            reference_elements_section = concept_text.split("4. Reference Elements:")[1].split("5. Concept Details:")[0] if "4. Reference Elements:" in concept_text else concept_text.split("Reference Elements:")[1].split("Concept Details:")[0]
                            st.markdown(reference_elements_section)
                            
                            # Display reference images alongside their elements
                            if 'reference_images' in st.session_state and st.session_state.reference_images:
                                st.markdown("### Reference Images")
                                ref_cols = st.columns(min(len(st.session_state.reference_images), 3))
                                for i, img in enumerate(st.session_state.reference_images):
                                    with ref_cols[i % 3]:
                                        st.image(img, caption=f"Reference {i+1}", width=150)
                        
                        # Extract Concept Details (handles both old and new format)
                        st.markdown("### Concept Details")
                        if "5. Concept Details:" in concept_text:  # New format (with Reference Elements)
                            details_section = concept_text.split("5. Concept Details:")[1].split("6. Text Elements:")[0]
                            st.markdown(details_section)
                        elif "4. Concept Details:" in concept_text:  # Old format (without Reference Elements)
                            details_section = concept_text.split("4. Concept Details:")[1].split("5. Text Elements:")[0] if "5. Text Elements:" in concept_text else concept_text.split("4. Concept Details:")[1].split("5. Headline:")[0]
                            st.markdown(details_section)
                        elif "Concept Details:" in concept_text:  # Generic fallback
                            if "Text Elements:" in concept_text:
                                details_section = concept_text.split("Concept Details:")[1].split("Text Elements:")[0]
                            else:
                                details_section = concept_text.split("Concept Details:")[1].split("Headline:")[0]
                            st.markdown(details_section)
                        else:
                            st.info("Concept details section not found in the generated content.")
                            
                        # Extract Professional Design Elements if available (handles both old and new format)
                        st.markdown("### Professional Design Elements")
                        if "7. Professional Design Elements:" in concept_text:  # New format
                            design_section = concept_text.split("7. Professional Design Elements:")[1].split("8. Ideogram Prompt:")[0]
                            st.markdown(design_section)
                        elif "6. Professional Design Elements:" in concept_text:  # Old format
                            design_section = concept_text.split("6. Professional Design Elements:")[1].split("7. Ideogram Prompt:")[0]
                            st.markdown(design_section)
                        elif "Professional Design Elements:" in concept_text:  # Generic fallback
                            design_section = concept_text.split("Professional Design Elements:")[1].split("Ideogram Prompt:")[0]
                            st.markdown(design_section)
                        else:
                            st.info("Professional design elements section not found in the generated content.")
                    
                    with tabs[4]:
                        # Extract Text Elements
                        st.markdown("### Text Elements")
                        if "Text Elements:" in concept_text or "5. Text Elements:" in concept_text:
                            text_elements_section = concept_text.split("5. Text Elements:")[1].split("6. Professional Design Elements:")[0] if "5. Text Elements:" in concept_text else concept_text.split("Text Elements:")[1].split("Professional Design Elements:")[0]
                            st.markdown(text_elements_section)
                        else:
                            # Extract Headlines using the old format for backward compatibility
                            if "Headline:" in concept_text or "5. Headline:" in concept_text:
                                headline_section = concept_text.split("5. Headline:")[1].split("6. Sub-Headline:")[0] if "5. Headline:" in concept_text else concept_text.split("Headline:")[1].split("Sub-Headline:")[0]
                                st.markdown(f"**Headline:** {headline_section.strip()}")
                            else:
                                st.info("Headline not found in the generated content.")
                            
                            if "Sub-Headline:" in concept_text or "6. Sub-Headline:" in concept_text:
                                subheadline_section = concept_text.split("6. Sub-Headline:")[1].split("7. Ideogram Prompt:")[0] if "6. Sub-Headline:" in concept_text else concept_text.split("Sub-Headline:")[1].split("Ideogram Prompt:")[0]
                                st.markdown(f"**Sub-Headline:** {subheadline_section.strip()}")
                            else:
                                st.info("Sub-headline not found in the generated content.")
                        
                        st.markdown("### AI Image Generator Prompt")
                        if "Ideogram Prompt:" in concept_text or "7. Ideogram Prompt:" in concept_text:
                            if "7. Ideogram Prompt:" in concept_text:
                                if "8. Negative Prompt:" in concept_text:
                                    prompt_section = concept_text.split("7. Ideogram Prompt:")[1].split("8. Negative Prompt:")[0]
                                else:
                                    prompt_section = concept_text.split("7. Ideogram Prompt:")[1]
                            else:
                                if "Negative Prompt:" in concept_text:
                                    prompt_section = concept_text.split("Ideogram Prompt:")[1].split("Negative Prompt:")[0]
                                else:
                                    prompt_section = concept_text.split("Ideogram Prompt:")[1]
                            
                            # Store the prompt in session state for use in the image tab
                            st.session_state.ideogram_prompt = prompt_section.strip()
                            
                            # Display the prompt in a highlighted box
                            st.markdown(f"""
                            <div style="background-color: #f0f7ff; padding: 15px; border-radius: 5px; border-left: 5px solid #4285F4;">
                                <p style="font-family: monospace; margin: 0;">{prompt_section.strip()}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("Ideogram prompt not found in the generated content.")
                        
                        # Extract negative prompt if available
                        st.markdown("### Negative Prompt (Elements to Avoid)")
                        if "Negative Prompt:" in concept_text or "8. Negative Prompt:" in concept_text:
                            negative_section = concept_text.split("8. Negative Prompt:")[1] if "8. Negative Prompt:" in concept_text else concept_text.split("Negative Prompt:")[1]
                            
                            # Store the negative prompt in session state for use in the image tab
                            st.session_state.negative_prompt = negative_section.strip()
                            
                            st.markdown(f"""
                            <div style="background-color: #fff0f0; padding: 15px; border-radius: 5px; border-left: 5px solid #EA4335;">
                                <p style="font-family: monospace; margin: 0;">{negative_section.strip()}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.session_state.negative_prompt = None
                            st.info("No negative prompt found in the generated content.")
                        
                        # Add a note about switching to the image tab
                        st.success("""
                        **Concept generated successfully!** 
                        
                        Switch to the "Create Image" tab to generate an actual image using this concept.
                        """)
                        
                except Exception as e:
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        st.error("""
                        ### Gemini AI Service Temporarily Unavailable
                        
                        The AI service is currently experiencing high demand or maintenance. Please try again in a few minutes.
                        
                        **Alternative options:**
                        - Try refreshing the page
                        - Try a different browser
                        - Check your internet connection
                        - Try again later when the service load may be lower
                        
                        Technical details: {e}
                        """)
                    else:
                        st.error(f"Error calling AI service: {e}")
    
    with image_tab:
        st.subheader("Create Image with Ideogram")
        
        # Add a helpful guide at the top
        with st.expander("📝 How to Use This Image Generator", expanded=False):
            st.markdown("""
            ### Understanding the Image Generation Process
            
            1. **Prompt**: This is the text description that tells the AI what to create. Be specific about what you want to see in the image.
            
            2. **Negative Prompt**: This tells the AI what NOT to include in your image (e.g., "blurry images, distorted faces").
            
            3. **Image Style**: Choose a predefined style like "Realistic" or "Anime" to influence the overall look.
            
            4. **Aspect Ratio**: Select the shape of your image (square, landscape, portrait, etc.).
            
            5. **Generate Button**: Click this when you're ready to create your image.
            
            **Tips for Better Results:**
            - Be specific and detailed in your prompt
            - Use negative prompts to avoid unwanted elements
            - Try different styles if you're not happy with the results
            """)
        
        # Check if we have a prompt from the concept tab
        if 'ideogram_prompt' in st.session_state:
            # Create a visually distinct card for the prompt section
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e0e0e0;">
            """, unsafe_allow_html=True)
            
            # Display the prompt from the concept tab with a clearer heading
            st.markdown("""
            <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 1.2rem;">📋 Generated Prompt</h3>
            <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">This is the AI-generated description that will be used to create your image:</p>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #e0e0e0; margin-bottom: 15px;">
                <p style="font-family: monospace; margin: 0; white-space: pre-wrap;">{st.session_state.ideogram_prompt}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Allow editing the prompt with clearer instructions
            st.markdown("""
            <h4 style="margin-bottom: 5px; font-size: 1rem;">✏️ Edit Prompt (if needed)</h4>
            <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">You can modify the text below to change what appears in your image:</p>
            """, unsafe_allow_html=True)
            
            edited_prompt = st.text_area(
                "",
                value=st.session_state.ideogram_prompt,
                height=100,
                key="edit_prompt_input",
                help="This is an editable text area. Make changes to the prompt here if you want to customize the image generation."
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Create a visually distinct card for the negative prompt section
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e0e0e0;">
            """, unsafe_allow_html=True)
            
            # Display negative prompt if available with clearer heading
            if 'negative_prompt' in st.session_state and st.session_state.negative_prompt:
                st.markdown("""
                <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 1.2rem;">🚫 Negative Prompt</h3>
                <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">These elements will be avoided in your generated image:</p>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #e0e0e0; margin-bottom: 15px;">
                    <p style="font-family: monospace; margin: 0; white-space: pre-wrap;">{st.session_state.negative_prompt}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Allow editing the negative prompt with clearer instructions
                st.markdown("""
                <h4 style="margin-bottom: 5px; font-size: 1rem;">✏️ Edit Negative Prompt (if needed)</h4>
                <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">You can modify what elements should be avoided in your image:</p>
                """, unsafe_allow_html=True)
                
                edited_negative_prompt = st.text_area(
                    "",
                    value=st.session_state.negative_prompt,
                    height=100,
                    key="edit_negative_prompt_input",
                    help="This is an editable text area. Add things you DON'T want to see in your image."
                )
            else:
                st.markdown("""
                <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 1.2rem;">🚫 Negative Prompt (Optional)</h3>
                <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">Specify elements you want to avoid in your image:</p>
                """, unsafe_allow_html=True)
                
                edited_negative_prompt = st.text_area(
                    "",
                    placeholder="Example: blurry images, distorted faces, text, watermarks, unrealistic proportions",
                    height=100,
                    key="negative_prompt_input",
                    help="This is an editable text area. Add things you DON'T want to see in your image."
                )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Create a visually distinct card for the image settings
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e0e0e0;">
            <h3 style="margin-top: 0; margin-bottom: 15px; font-size: 1.2rem;">⚙️ Image Settings</h3>
            """, unsafe_allow_html=True)
            
            # Image style and aspect ratio options
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <p style="margin-bottom: 5px; font-size: 0.9rem; color: #666;">Choose model and style options:</p>
                """, unsafe_allow_html=True)
                
                # Add model selection
                model_options = {
                    "V_2_TURBO": "V_2_TURBO (Balanced speed and quality)",
                    "V_1_TURBO": "V_1_TURBO (Fastest generation)"
                }
                selected_model = st.selectbox(
                    "Model",
                    list(model_options.keys()),
                    format_func=lambda x: model_options[x],
                    index=0,
                    help="V_2_TURBO offers balanced speed and quality. V_1_TURBO is faster but may have lower quality."
                )
                
                # Get style options
                style_options = get_ideogram_styles()
                
                # Style is always None since we don't have V_2A anymore
                style = None
                # No need to show style selection UI
            
            with col2:
                st.markdown("""
                <p style="margin-bottom: 5px; font-size: 0.9rem; color: #666;">Choose the shape/dimensions of your image:</p>
                """, unsafe_allow_html=True)
                
                aspect_ratio_options = get_ideogram_aspect_ratios()
                aspect_ratio_selected = st.selectbox(
                    "Aspect Ratio",
                    list(aspect_ratio_options.keys()),
                    index=0,
                    help="Select the shape of your image. Square (1:1) is good for social media posts. Landscape (16:9) is good for wide images."
                )
                aspect_ratio = aspect_ratio_options[aspect_ratio_selected]
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Number of images is fixed to 1 (hidden from user)
            num_images = 1
            
            # Generate image button with more prominence
            st.markdown("""
            <div style="text-align: center; margin: 30px 0;">
            """, unsafe_allow_html=True)
            
            if st.button("🖼️ Generate Image", use_container_width=True, key="generate_button"):
                with st.spinner("Creating your image with AI... This may take a moment."):
                    # Call Ideogram API
                    response = generate_image_with_ideogram(
                        prompt=edited_prompt,
                        style=style,
                        aspect_ratio=aspect_ratio,
                        negative_prompt=edited_negative_prompt if edited_negative_prompt else None,
                        num_images=num_images,
                        model=selected_model
                    )
                    
                    if response:
                        st.success("✅ Image generated successfully!")
                        
                        # Store the response in session state
                        st.session_state.ideogram_response = response
                        
                        # Display the generated images
                        display_ideogram_images(response)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
        else:
            # If no prompt is available, show a clearer message with options
            st.info("""
            ### No prompt available yet
            
            You need to create a prompt before generating an image. You can:
            
            1. **Go to the "Generate Concept" tab** first to create an image concept automatically
            2. **OR** enter a prompt manually below
            3. **OR** upload a reference image to analyze
            """)
            
            # Create a visually distinct card for manual prompt entry
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e0e0e0;">
            <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 1.2rem;">✏️ Enter a Prompt Manually</h3>
            <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">Describe what you want to see in your image:</p>
            """, unsafe_allow_html=True)
            
            # Allow manual prompt entry if no concept is available
            manual_prompt = st.text_area(
                "",
                placeholder="Example: A serene landscape with mountains and a lake at sunset, with warm golden light, reflections in the water, and small birds flying in the distance",
                height=120,
                help="This is where you describe what you want in your image. Be detailed and specific for best results."
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if manual_prompt:
                # Display reference image description if available from the image tab
                if 'image_tab_reference_description' in st.session_state:
                    st.markdown("""
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e0e0e0;">
                    <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 1.2rem;">🖼️ Reference Image Description</h3>
                    <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">Description of your uploaded reference image:</p>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""
                    <div style="background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #e0e0e0;">
                        <p style="font-family: monospace; margin: 0; white-space: pre-wrap;">{st.session_state.image_tab_reference_description}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add checkbox to include reference image description in the prompt
                    include_reference = st.checkbox(
                        "Include reference image description in the prompt", 
                        value=True,
                        help="Check this to combine your prompt with the reference image description"
                    )
                    
                    if include_reference:
                        # Combine the prompt with the reference description
                        combined_prompt = f"{manual_prompt}. Reference: {st.session_state.image_tab_reference_description}"
                        
                        st.markdown("""
                        <h4 style="margin-top: 15px; margin-bottom: 10px; font-size: 1rem;">Combined Prompt</h4>
                        <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">This is what will be sent to the AI:</p>
                        """, unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div style="background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #e0e0e0;">
                            <p style="font-family: monospace; margin: 0; white-space: pre-wrap;">{combined_prompt}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # Create a visually distinct card for the negative prompt
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e0e0e0;">
                <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 1.2rem;">🚫 Negative Prompt (Optional)</h3>
                <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">Specify elements you want to avoid in your image:</p>
                """, unsafe_allow_html=True)
                
                # Negative prompt
                manual_negative_prompt = st.text_area(
                    "",
                    placeholder="Example: blurry, distorted faces, text, watermarks, unrealistic proportions",
                    height=100,
                    help="List things you DON'T want to see in your image"
                )
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Create a visually distinct card for the image settings
                st.markdown("""
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e0e0e0;">
                <h3 style="margin-top: 0; margin-bottom: 15px; font-size: 1.2rem;">⚙️ Image Settings</h3>
                """, unsafe_allow_html=True)
                
                # Image style and aspect ratio options
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    <p style="margin-bottom: 5px; font-size: 0.9rem; color: #666;">Choose model and style options:</p>
                    """, unsafe_allow_html=True)
                    
                    # Add model selection
                    model_options = {
                        "V_2_TURBO": "V_2_TURBO (Balanced speed and quality)",
                        "V_1_TURBO": "V_1_TURBO (Fastest generation)"
                    }
                    selected_model = st.selectbox(
                        "Model",
                        list(model_options.keys()),
                        format_func=lambda x: model_options[x],
                        index=0,
                        help="V_2_TURBO offers balanced speed and quality. V_1_TURBO is faster but may have lower quality."
                    )
                    
                    # Get style options
                    style_options = get_ideogram_styles()
                    
                    # Style is always None since we don't have V_2A anymore
                    style = None
                    # No need to show style selection UI
                
                with col2:
                    st.markdown("""
                    <p style="margin-bottom: 5px; font-size: 0.9rem; color: #666;">Choose the shape/dimensions of your image:</p>
                    """, unsafe_allow_html=True)
                    
                    aspect_ratio_options = get_ideogram_aspect_ratios()
                    aspect_ratio_selected = st.selectbox(
                        "Aspect Ratio",
                        list(aspect_ratio_options.keys()),
                        index=0,
                        help="Select the shape of your image. Square (1:1) is good for social media posts. Landscape (16:9) is good for wide images."
                    )
                    aspect_ratio = aspect_ratio_options[aspect_ratio_selected]
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Number of images is fixed to 1 (hidden from user)
                num_images = 1
                
                # Generate image button with more prominence
                st.markdown("""
                <div style="text-align: center; margin: 30px 0;">
                """, unsafe_allow_html=True)
                
                if st.button("🖼️ Generate Image", use_container_width=True, key="generate_manual_button"):
                    with st.spinner("Creating your image with AI... This may take a moment."):
                        # Determine which prompt to use
                        final_prompt = combined_prompt if include_reference and 'image_tab_reference_description' in st.session_state else manual_prompt
                        
                        # Call Ideogram API
                        response = generate_image_with_ideogram(
                            prompt=final_prompt,
                            style=style,
                            aspect_ratio=aspect_ratio,
                            negative_prompt=manual_negative_prompt if manual_negative_prompt else None,
                            num_images=num_images,
                            model=selected_model
                        )
                        
                        if response:
                            st.success("✅ Image generated successfully!")
                            
                            # Store the response in session state
                            st.session_state.ideogram_response = response
                            
                            # Display the generated images
                            display_ideogram_images(response)
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    with storyboard_tab:
        st.subheader("Create a Storyboard with Related Images")
        
        # Add a helpful guide at the top
        with st.expander("📚 How to Use the Storyboard Generator", expanded=False):
            st.markdown("""
            ### Creating a Visual Storyboard
            
            1. **Start with a Concept**: First use the "Generate Concept" tab to create your main storyboard idea
            2. **Enter Your Storyboard Prompt**: Describe the overall theme or narrative you want to visualize
            3. **Generate Storyboard**: The AI will create 4 coordinated image prompts based on your main concept
            4. **View Your Storyboard**: See all 4 resulting images in a 2×2 grid format
            
            **Tips for Better Results:**
            - Be specific about the narrative or sequence you want to portray
            - Mention if you want a specific style to be consistent across all images
            - For best results, describe a scene, story, or process that can be broken into logical parts
            """)
        
        # Check if we have a prompt from the concept tab
        if 'ideogram_prompt' in st.session_state:
            # Create a visually distinct card for the prompt section
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e0e0e0;">
            """, unsafe_allow_html=True)
            
            # Display the prompt from the concept tab with a clearer heading
            st.markdown("""
            <h3 style="margin-top: 0; margin-bottom: 10px; font-size: 1.2rem;">📋 Main Storyboard Concept</h3>
            <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">This is the main concept that will be used to create your storyboard:</p>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #e0e0e0; margin-bottom: 15px;">
                <p style="font-family: monospace; margin: 0; white-space: pre-wrap;">{st.session_state.ideogram_prompt}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Allow editing the main storyboard concept
            st.markdown("""
            <h4 style="margin-bottom: 5px; font-size: 1rem;">✏️ Edit Main Concept (if needed)</h4>
            <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">You can modify the text below to change your storyboard concept:</p>
            """, unsafe_allow_html=True)
            
            storyboard_concept = st.text_area(
                "",
                value=st.session_state.ideogram_prompt,
                height=100,
                key="storyboard_concept_input",
                help="This is the main concept for your storyboard. Make changes here if you want to customize it."
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Create a visually distinct card for the storyboard settings
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e0e0e0;">
            <h3 style="margin-top: 0; margin-bottom: 15px; font-size: 1.2rem;">⚙️ Storyboard Settings</h3>
            """, unsafe_allow_html=True)
            
            # Storyboard style and aspect ratio options
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <p style="margin-bottom: 5px; font-size: 0.9rem; color: #666;">Choose model and style options:</p>
                """, unsafe_allow_html=True)
                
                # Add model selection
                model_options = {
                    "V_2_TURBO": "V_2_TURBO (Balanced speed and quality)",
                    "V_1_TURBO": "V_1_TURBO (Fastest generation)"
                }
                selected_model = st.selectbox(
                    "Model",
                    list(model_options.keys()),
                    format_func=lambda x: model_options[x],
                    index=0,
                    key="storyboard_model",
                    help="V_2_TURBO offers balanced speed and quality. V_1_TURBO is faster but may have lower quality."
                )
                
                # Get style options
                style_options = get_ideogram_styles()
                
                # Style is always None since we don't have V_2A anymore
                style = None
                # No need to show style selection UI
            
            with col2:
                st.markdown("""
                <p style="margin-bottom: 5px; font-size: 0.9rem; color: #666;">Choose the shape/dimensions for all storyboard images:</p>
                """, unsafe_allow_html=True)
                
                aspect_ratio_options = get_ideogram_aspect_ratios()
                aspect_ratio_selected = st.selectbox(
                    "Aspect Ratio",
                    list(aspect_ratio_options.keys()),
                    index=0,
                    key="storyboard_aspect_ratio",
                    help="Select the shape for all your storyboard images. Square (1:1) works best for storyboards."
                )
                aspect_ratio = aspect_ratio_options[aspect_ratio_selected]
            
            # Negative prompt for storyboard
            st.markdown("""
            <h4 style="margin-top: 15px; margin-bottom: 5px; font-size: 1rem;">🚫 Negative Prompt (Optional)</h4>
            <p style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">Specify elements you want to avoid in all storyboard images:</p>
            """, unsafe_allow_html=True)
            
            if 'negative_prompt' in st.session_state and st.session_state.negative_prompt:
                storyboard_negative_prompt = st.text_area(
                    "",
                    value=st.session_state.negative_prompt,
                    height=80,
                    key="storyboard_negative_prompt",
                    help="This will apply to all images in your storyboard."
                )
            else:
                storyboard_negative_prompt = st.text_area(
                    "",
                    placeholder="Example: blurry images, distorted faces, text, watermarks, unrealistic proportions",
                    height=80,
                    key="storyboard_negative_prompt",
                    help="This will apply to all images in your storyboard."
                )
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Generate storyboard button
            st.markdown("""
            <div style="text-align: center; margin: 30px 0;">
            """, unsafe_allow_html=True)
            
            if st.button("🎬 Generate Storyboard", use_container_width=True, key="generate_storyboard_button"):
                with st.spinner("Creating your storyboard with AI... This may take a moment."):
                    # Get Gemini client for generating the storyboard prompts
                    client = get_gemini_client()
                    if not client:
                        st.error("Unable to initialize Gemini client. Please try again later.")
                    else:
                        try:
                            # Prepare prompt for Gemini to generate 4 coordinated image prompts
                            prompt = f"""
                            Based on this main concept: "{storyboard_concept}"
                            
                            Create 4 coordinated image prompts that tell a cohesive visual story for professional business use. Each image should include text elements and professional design details.
                            
                            The 4 prompts should:
                            1. Follow the same visual style and aesthetic for brand consistency
                            2. Each include specific text elements (like headlines, taglines, or calls to action)
                            3. Incorporate professional design elements (like logo placement, branded colors, or UI mockups)
                            4. Work together as a cohesive marketing campaign or product story
                            5. Be detailed enough to create professional-looking business content
                            6. CRITICAL: Use EXACTLY the same color palette and visual theme across all 4 images
                            7. Maintain consistent lighting, mood, and stylistic elements throughout the series
                            
                            For each prompt, include:
                            - The main visual scene or composition
                            - Specific text to include in the image (headlines, taglines, etc.)
                            - Design elements (layout suggestions, color schemes, etc.)
                            - Professional context (how it would be used in business)
                            
                            Format your response as a JSON array with 4 detailed prompts, like this:
                            ["Professional business image with modern office setting. TEXT: 'Innovation Starts Here' in bold sans-serif font at top. Clean layout with blue and white color scheme, showing team collaboration.", "Prompt 2", "Prompt 3", "Prompt 4"]
                            
                            Do not include any explanations or additional text - ONLY return the JSON array.
                            """

                            # Enhanced prompt that incorporates reference images for storyboard generation
                            reference_elements = ""
                            has_references = False
                            
                            if 'reference_descriptions' in st.session_state and st.session_state.reference_descriptions:
                                has_references = True
                                reference_elements = "Reference Image Descriptions:\n\n"
                                for i, desc in enumerate(st.session_state.reference_descriptions):
                                    reference_elements += f"Reference Image {i+1}: {desc}\n\n"
                                
                                reference_elements += """
                                IMPORTANT: When using elements from reference images, you MUST reproduce them EXACTLY as they appear.
                                Not every image needs to use reference elements, but when you do use them:
                                
                                1. Be EXTREMELY specific about what you're incorporating
                                2. Use exact wording like "EXACT SAME black long plate table as in Reference Image X" 
                                3. Mention the specific reference image number
                                
                                Create 4 DIFFERENT but RELATED images that work together as a cohesive advertising campaign.
                                Each image should have its own unique focus while maintaining brand consistency across all panels.
                                """
                            else:
                                # Enhanced instructions for when no reference images are provided
                                reference_elements = """
                                IMPORTANT: Since no reference images were provided, create highly detailed and professional designs with:
                                
                                1. Precise descriptions of visual elements (specific colors, objects, layouts)
                                2. Professional composition and lighting details
                                3. Clear text placement and hierarchy
                                4. Brand-appropriate styling
                                5. Realistic and high-quality visual elements
                                6. CRITICAL: Use EXACTLY the same color palette across all 4 images (specify exact colors like "deep navy blue #1a2b3c" and "warm gold #d4af37")
                                7. Maintain consistent font styles, lighting mood, and visual theme throughout all panels
                                
                                Create 4 DIFFERENT but RELATED images that work together as a cohesive advertising campaign.
                                Each image should have its own unique focus while maintaining brand consistency across all panels.
                                """
                            
                            # Base prompt that's always included
                            prompt = f"""
                            Based on this main concept: "{storyboard_concept}"
                            
                            {reference_elements}
                            
                            Create 4 coordinated image prompts that tell a cohesive visual story for professional business use. Each image should include text elements and professional design details.
                            
                            The 4 prompts should:
                            1. Follow the same visual style and aesthetic for brand consistency
                            2. Each include specific text elements (like headlines, taglines, or calls to action)
                            3. Incorporate professional design elements (like logo placement, branded colors, or UI mockups)
                            4. Work together as a cohesive marketing campaign or product story
                            5. Be detailed enough to create professional-looking business content
                            6. CRITICAL: Use EXACTLY the same color palette and visual theme across all 4 images
                            7. Maintain consistent lighting, mood, and stylistic elements throughout the series
                            """
                            
                            # Add reference-specific instructions if references exist
                            if has_references:
                                prompt += """
                            6. FAITHFULLY REPRODUCE specific elements from the reference images in your prompts
                            
                            For each prompt, include:
                            - The main visual scene or composition
                            - Specific text to include in the image (headlines, taglines, etc.)
                            - Design elements (layout suggestions, color schemes, etc.)
                            - Professional context (how it would be used in business)
                            - SPECIFIC references to elements from reference images ONLY when used (not every panel needs reference elements)
                            
                            Example of a 4-panel storyboard with selective reference use:
                            
                            Panel 1: "Professional restaurant interior with black long plate table exactly as shown in Reference Image 2. Warm amber lighting, deep blue and gold color scheme. Customers enjoying meal. TEXT: 'Begin Your Culinary Journey', top center in gold serif font. Professional layout, elegant style."
                            
                            Panel 2: "Close-up of signature dish with steam rising. Same deep blue background and amber lighting as Panel 1. Rich gold accents, artistic plating. No reference image elements needed here. TEXT: 'Crafted With Passion', bottom right in matching gold serif font. Luxury food photography style."
                            
                            Panel 3: "Chef in white uniform using cooking technique with exact same flame pattern as Reference Image 4. Maintaining the deep blue and gold color scheme with amber lighting. TEXT: 'Mastery In Motion', centered in gold serif font. Dynamic composition, action shot."
                            
                            Panel 4: "Exterior night shot of restaurant with glowing signage. Deep blue night sky with gold and amber lighting elements matching previous panels. No reference elements needed. TEXT: 'Visit Us Tonight', bottom center with restaurant address in gold serif font. Elegant nighttime photography."
                            """
                            else:
                                prompt += """
                            For each prompt, include:
                            - The main visual scene or composition
                            - Specific text to include in the image (headlines, taglines, etc.)
                            - Design elements (layout suggestions, color schemes, etc.)
                            - Professional context (how it would be used in business)
                            """
                            
                            # Add the final formatting instructions
                            prompt += """
                            Format your response as a JSON array with 4 detailed prompts, like this:
                            ["Prompt 1", "Prompt 2", "Prompt 3", "Prompt 4"]
                            
                            Do not include any explanations or additional text - ONLY return the JSON array.
                            """

                            # Call Gemini API
                            response = client.models.generate_content(
                                model="gemini-2.0-flash",
                                contents=prompt
                            )
                            
                            # Parse the response to extract the 4 prompts
                            try:
                                # Extract the JSON array from the response
                                import json
                                import re
                                
                                # Clean the response text to extract just the JSON array
                                response_text = response.text.strip()
                                # Find anything that looks like a JSON array
                                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                                
                                if json_match:
                                    json_str = json_match.group(0)
                                    storyboard_prompts = json.loads(json_str)
                                else:
                                    # Fallback: try to parse the entire response as JSON
                                    storyboard_prompts = json.loads(response_text)
                                
                                # Ensure we have exactly 4 prompts
                                if not isinstance(storyboard_prompts, list) or len(storyboard_prompts) != 4:
                                    raise ValueError("Did not receive exactly 4 prompts")
                                
                                # Store the prompts in session state
                                st.session_state.storyboard_prompts = storyboard_prompts
                                
                                # Display the 4 prompts
                                st.subheader("Generated Storyboard Prompts")
                                
                                # Create a 2x2 grid to display the prompts
                                prompt_cols1 = st.columns(2)
                                prompt_cols2 = st.columns(2)
                                
                                with prompt_cols1[0]:
                                    st.markdown("### Panel 1")
                                    st.markdown(f"""
                                    <div style="background-color: #f0f7ff; padding: 15px; border-radius: 5px; border-left: 5px solid #4285F4;">
                                        <p style="font-family: monospace; margin: 0;">{storyboard_prompts[0]}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with prompt_cols1[1]:
                                    st.markdown("### Panel 2")
                                    st.markdown(f"""
                                    <div style="background-color: #f0f7ff; padding: 15px; border-radius: 5px; border-left: 5px solid #4285F4;">
                                        <p style="font-family: monospace; margin: 0;">{storyboard_prompts[1]}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with prompt_cols2[0]:
                                    st.markdown("### Panel 3")
                                    st.markdown(f"""
                                    <div style="background-color: #f0f7ff; padding: 15px; border-radius: 5px; border-left: 5px solid #4285F4;">
                                        <p style="font-family: monospace; margin: 0;">{storyboard_prompts[2]}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with prompt_cols2[1]:
                                    st.markdown("### Panel 4")
                                    st.markdown(f"""
                                    <div style="background-color: #f0f7ff; padding: 15px; border-radius: 5px; border-left: 5px solid #4285F4;">
                                        <p style="font-family: monospace; margin: 0;">{storyboard_prompts[3]}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # Generate the 4 images
                                st.subheader("Generating Storyboard Images...")
                                
                                # Create a progress bar
                                progress_bar = st.progress(0)
                                
                                # Store the generated image URLs
                                storyboard_images = []
                                
                                # Generate each image
                                for i, prompt in enumerate(storyboard_prompts):
                                    with st.spinner(f"Generating image {i+1} of 4..."):
                                        # Update progress
                                        progress_bar.progress((i) / 4)
                                        
                                        # Generate the image
                                        response = generate_image_with_ideogram(
                                            prompt=prompt,
                                            style=style,
                                            aspect_ratio=aspect_ratio,
                                            negative_prompt=storyboard_negative_prompt if storyboard_negative_prompt else None,
                                            num_images=1,
                                            model=selected_model
                                        )
                                        
                                        if response and "data" in response and len(response["data"]) > 0:
                                            # Extract the image URL
                                            if "url" in response["data"][0]:
                                                storyboard_images.append(response["data"][0]["url"])
                                            elif "image_url" in response["data"][0]:
                                                storyboard_images.append(response["data"][0]["image_url"])
                                        else:
                                            st.error(f"Failed to generate image {i+1}. Please try again.")
                                    
                                    # Update progress
                                    progress_bar.progress((i + 1) / 4)
                                
                                # Complete the progress bar
                                progress_bar.progress(1.0)
                                
                                # Store the storyboard images in session state
                                if len(storyboard_images) == 4:
                                    st.session_state.storyboard_images = storyboard_images
                                    
                                    # Display the storyboard
                                    st.subheader("Your Storyboard")
                                    
                                    # Create a 2x2 grid to display the images
                                    image_cols1 = st.columns(2)
                                    image_cols2 = st.columns(2)
                                    
                                    with image_cols1[0]:
                                        st.markdown("### Panel 1")
                                        st.image(storyboard_images[0], use_column_width=True)
                                        st.markdown(f"**Prompt:** {storyboard_prompts[0]}")
                                        st.markdown(
                                            f"""
                                            <div style="text-align: center;">
                                                <a href="{storyboard_images[0]}" download="storyboard_panel1.jpg" 
                                                style="display: inline-block; padding: 8px 16px; background-color: #4CAF50; color: white; 
                                                text-decoration: none; border-radius: 5px; font-size: 0.8rem;">
                                                Download Image
                                                </a>
                                            </div>
                                            """, 
                                            unsafe_allow_html=True
                                        )
                                    
                                    with image_cols1[1]:
                                        st.markdown("### Panel 2")
                                        st.image(storyboard_images[1], use_column_width=True)
                                        st.markdown(f"**Prompt:** {storyboard_prompts[1]}")
                                        st.markdown(
                                            f"""
                                            <div style="text-align: center;">
                                                <a href="{storyboard_images[1]}" download="storyboard_panel2.jpg" 
                                                style="display: inline-block; padding: 8px 16px; background-color: #4CAF50; color: white; 
                                                text-decoration: none; border-radius: 5px; font-size: 0.8rem;">
                                                Download Image
                                                </a>
                                            </div>
                                            """, 
                                            unsafe_allow_html=True
                                        )
                                    
                                    with image_cols2[0]:
                                        st.markdown("### Panel 3")
                                        st.image(storyboard_images[2], use_column_width=True)
                                        st.markdown(f"**Prompt:** {storyboard_prompts[2]}")
                                        st.markdown(
                                            f"""
                                            <div style="text-align: center;">
                                                <a href="{storyboard_images[2]}" download="storyboard_panel3.jpg" 
                                                style="display: inline-block; padding: 8px 16px; background-color: #4CAF50; color: white; 
                                                text-decoration: none; border-radius: 5px; font-size: 0.8rem;">
                                                Download Image
                                                </a>
                                            </div>
                                            """, 
                                            unsafe_allow_html=True
                                        )
                                    
                                    with image_cols2[1]:
                                        st.markdown("### Panel 4")
                                        st.image(storyboard_images[3], use_column_width=True)
                                        st.markdown(f"**Prompt:** {storyboard_prompts[3]}")
                                        st.markdown(
                                            f"""
                                            <div style="text-align: center;">
                                                <a href="{storyboard_images[3]}" download="storyboard_panel4.jpg" 
                                                style="display: inline-block; padding: 8px 16px; background-color: #4CAF50; color: white; 
                                                text-decoration: none; border-radius: 5px; font-size: 0.8rem;">
                                                Download Image
                                                </a>
                                            </div>
                                            """, 
                                            unsafe_allow_html=True
                                        )
                                    
                                    # Add a download all button
                                    st.markdown(
                                        f"""
                                        <div style="text-align: center; margin-top: 30px;">
                                            <p>Download all images individually using the buttons above each panel.</p>
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                    )
                                    
                                    st.success("✅ Storyboard generated successfully!")
                                else:
                                    st.error("Failed to generate all storyboard images. Please try again.")
                            
                            except Exception as e:
                                st.error(f"Error processing storyboard prompts: {e}")
                                st.error("Please try again with a different concept or settings.")
                        
                        except Exception as e:
                            if "503" in str(e) or "UNAVAILABLE" in str(e):
                                st.error("""
                                ### Gemini AI Service Temporarily Unavailable
                                
                                The AI service is currently experiencing high demand or maintenance. Please try again in a few minutes.
                                
                                **Alternative options:**
                                - Try refreshing the page
                                - Try a different browser
                                - Check your internet connection
                                - Try again later when the service load may be lower
                                
                                Technical details: {e}
                                """)
                            else:
                                st.error(f"Error calling AI service: {e}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        else:
            # If no prompt is available, show a message with instructions
            st.info("""
            ### No concept available yet
            
            You need to create a concept before generating a storyboard. Please:
            
            1. Go to the "Generate Concept" tab first to create an image concept
            2. Then come back to this tab to create your storyboard
            
            A good storyboard starts with a clear concept!
            """)

# Ideogram API integration
def get_ideogram_client():
    """Initialize and return an Ideogram API client."""
    # Store API key in session state if not already there
    if 'ideogram_api_key' not in st.session_state:
        st.session_state.ideogram_api_key = "QwpPhBkcx1I6RZVbJB7pjC_6DtgJQsjgZzG1AXs8WuesB4RnuqLieyQ5k_b22Z_iLGUlyStjdec0guOynPwuGA"
    
    return st.session_state.ideogram_api_key

def generate_image_with_ideogram(prompt, style=None, aspect_ratio="1:1", negative_prompt=None, num_images=1, model="V_2_TURBO"):
    """Generate an image using the Ideogram API.
    
    Args:
        prompt (str): The text prompt for image generation
        style (str, optional): Style parameter is ignored as V_2A is no longer available
        aspect_ratio (str, optional): Aspect ratio of the image (1:1, 16:9, etc.)
        negative_prompt (str, optional): Things to avoid in the image
        num_images (int, optional): Number of images to generate (1-4)
        model (str, optional): Model to use for generation (V_1_TURBO or V_2_TURBO)
        
    Returns:
        dict: Response from Ideogram API containing image URLs and other metadata
    """
    api_key = get_ideogram_client()
    if not api_key:
        st.error("Ideogram API key not found.")
        return None
    
    # Ideogram API endpoint - updated to correct endpoint
    url = "https://api.ideogram.ai/generate"
    
    # Prepare headers - updated to use Api-Key instead of Authorization
    headers = {
        "Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Convert aspect ratio format from "W:H" to "ASPECT_W_H"
    if ":" in aspect_ratio:
        width, height = aspect_ratio.split(":")
        aspect_ratio = f"ASPECT_{width}_{height}"
    
    # Ensure num_images is within valid range (1-4)
    num_images = max(1, min(4, num_images))
    
    # Prepare payload with the correct structure
    payload = {
        "image_request": {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "model": model,
            "num_images": num_images,
            "magic_prompt_option": "AUTO"  # Always use AUTO for magic prompt
        }
    }
    
    # Add negative prompt if provided
    if negative_prompt:
        payload["image_request"]["negative_prompt"] = negative_prompt
    
    try:
        # Make API request
        response = requests.post(url, headers=headers, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error calling Ideogram API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error calling Ideogram API: {e}")
        return None

def display_ideogram_images(response):
    """Display images generated by Ideogram API.
    
    Args:
        response (dict): Response from Ideogram API
    """
    import io
    from PIL import Image
    import requests
    import base64
    
    if not response or "data" not in response:
        st.error("No images found in the response.")
        return
    
    # Extract image URLs from response
    image_urls = []
    for image_data in response["data"]:
        # Check for the 'url' field in the response (Ideogram API format)
        if "url" in image_data:
            image_urls.append(image_data["url"])
        # Fallback to 'image_url' field if present (for backward compatibility)
        elif "image_url" in image_data:
            image_urls.append(image_data["image_url"])
    
    # Check if we have any images to display
    if not image_urls:
        st.warning("No images were generated. Please try again with a different prompt or settings.")
        return
    
    # Initialize session state for slideshow if not already there
    if "generated_images" not in st.session_state:
        st.session_state.generated_images = image_urls
    else:
        # Update the images if they're different from what's already stored
        if st.session_state.generated_images != image_urls:
            st.session_state.generated_images = image_urls
            # Reset the index when new images are loaded
            st.session_state.current_image_index = 0
    
    # Initialize current image index if not already there
    if "current_image_index" not in st.session_state:
        st.session_state.current_image_index = 0
    
    # Display number of images generated
    num_images = len(image_urls)
    st.markdown(f"### {num_images} {'Image' if num_images == 1 else 'Images'} Generated")
    
    # Function to resize image while preserving aspect ratio
    def resize_image_for_preview(image_url, max_width=600):
        try:
            # Download the image
            response = requests.get(image_url)
            img = Image.open(io.BytesIO(response.content))
            
            # Calculate new dimensions while preserving aspect ratio
            width, height = img.size
            if width > max_width:
                ratio = max_width / width
                new_width = max_width
                new_height = int(height * ratio)
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert the resized image to bytes for display
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
        except Exception as e:
            st.warning(f"Could not resize image: {e}")
            return image_url
    
    # Create a slideshow if there are multiple images
    if num_images > 1:
        # Ensure index is within bounds
        if st.session_state.current_image_index >= num_images:
            st.session_state.current_image_index = 0
        
        # Create columns for navigation
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            # Previous button
            if st.button("← Previous", key="prev_button"):
                st.session_state.current_image_index = (st.session_state.current_image_index - 1) % num_images
        
        with col2:
            # Display current image number
            current_idx = st.session_state.current_image_index + 1
            st.markdown(f"<h4 style='text-align: center;'>Image {current_idx} of {num_images}</h4>", unsafe_allow_html=True)
        
        with col3:
            # Next button
            if st.button("Next →", key="next_button"):
                st.session_state.current_image_index = (st.session_state.current_image_index + 1) % num_images
        
        # Get the current image URL
        current_url = image_urls[st.session_state.current_image_index]
        
        # Get resized image for preview
        resized_image_data = resize_image_for_preview(current_url)
        
        # Display the resized image
        st.markdown(f"""
        <div style="display: flex; justify-content: center; margin: 0 auto;">
            <img src="{resized_image_data}" style="max-width: 100%;">
        </div>
        """, unsafe_allow_html=True)
        
        # Add download button for the current image (original quality)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <a href="{current_url}" download="ideogram_image_{st.session_state.current_image_index+1}.jpg" 
                       style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; 
                       text-decoration: none; border-radius: 5px; font-weight: bold;">
                       Download Original Quality Image
                    </a>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        # Add a thumbnail gallery for quick navigation
        st.markdown("### All Generated Images")
        
        # Create a grid of thumbnails
        thumbnail_cols = st.columns(min(4, num_images))
        
        for i, url in enumerate(image_urls):
            with thumbnail_cols[i % min(4, num_images)]:
                # Add a border to the current image in the gallery
                border_style = "border: 3px solid #4CAF50;" if i == st.session_state.current_image_index else ""
                
                # Get resized thumbnail
                thumbnail_data = resize_image_for_preview(url, max_width=150)
                
                # Display the thumbnail
                st.markdown(
                    f"""
                    <div style="text-align: center; margin-bottom: 10px; {border_style}">
                        <img src="{thumbnail_data}" style="width: 100%; max-width: 150px;">
                        <p style="margin-top: 5px;">Image {i+1}</p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                # Add a button to select this image
                if st.button(f"View {i+1}", key=f"thumb_{i}"):
                    st.session_state.current_image_index = i
    else:
        # Display single image with reduced size
        current_url = image_urls[0]
        
        # Get resized image for preview
        resized_image_data = resize_image_for_preview(current_url)
        
        # Display the resized image
        st.markdown(f"""
        <div style="display: flex; justify-content: center; margin: 0 auto;">
            <img src="{resized_image_data}" style="max-width: 100%;">
        </div>
        """, unsafe_allow_html=True)
        
        # Add download button for the single image (original quality)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                f"""
                <div style="text-align: center;">
                    <a href="{current_url}" download="ideogram_image.jpg" 
                       style="display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; 
                       text-decoration: none; border-radius: 5px; font-weight: bold;">
                       Download Original Quality Image
                    </a>
                </div>
                """, 
                unsafe_allow_html=True
            )

def get_ideogram_aspect_ratios():
    """Get available aspect ratios for Ideogram API.
    
    Returns:
        dict: Dictionary mapping display names to API values
    """
    return {
        "Square (1:1)": "ASPECT_1_1",
        "Landscape (16:9)": "ASPECT_16_9",
        "Portrait (9:16)": "ASPECT_9_16",
        "Standard (4:3)": "ASPECT_4_3",
        "Portrait (3:4)": "ASPECT_3_4",
        "Landscape (3:2)": "ASPECT_3_2",
        "Portrait (2:3)": "ASPECT_2_3",
        "Widescreen (16:10)": "ASPECT_16_10",
        "Tall (10:16)": "ASPECT_10_16",
        "Panorama (3:1)": "ASPECT_3_1",
        "Vertical Panorama (1:3)": "ASPECT_1_3"
    }

def get_ideogram_styles():
    """Get available styles for Ideogram API.
    
    Returns:
        dict: Dictionary mapping display names to API values
    """
    return {
        "Auto": "AUTO",
        "General": "GENERAL",
        "Realistic": "REALISTIC",
        "Design": "DESIGN",
        "3D Render": "RENDER_3D",
        "Anime": "ANIME"
    }

def describe_image_with_ideogram(image_file):
    """Analyze an image using the Ideogram Describe API.
    
    Args:
        image_file: The uploaded image file
        
    Returns:
        dict: Response from Ideogram Describe API containing image description
    """
    api_key = get_ideogram_client()
    if not api_key:
        st.error("Ideogram API key not found.")
        return None
    
    # Ideogram Describe API endpoint
    url = "https://api.ideogram.ai/describe"
    
    # Prepare headers
    headers = {
        "Api-Key": api_key
    }
    
    try:
        # Create a multipart form with the image file
        # The API expects the field to be named "image_file" not "image"
        files = {
            "image_file": (image_file.name, image_file.getvalue(), "image/jpeg")
        }
        
        # Make API request
        response = requests.post(url, headers=headers, files=files)
        
        # Check if request was successful
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error calling Ideogram Describe API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error calling Ideogram Describe API: {e}")
        return None

# Main app
def main():
    """Run the main app."""
    # Navigation
    page = sidebar_navigation()
    
    # Display the selected page
    if page == "Content Generator":
        content_generator_page()
    elif page == "Image Creator":
        image_creator_page()
    else:
        data_analytics_page()
    
    # Add footer
    st.markdown("""
    <div class="app-footer">
        <p class="footer-text">
            AI Content Generator & Analytics | Powered by Gemini AI | © 2025
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 