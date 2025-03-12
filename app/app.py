import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
from google import genai
from sqlalchemy import create_engine, text
import psycopg2
import warnings
import uuid
from datetime import date

# Suppress SQLAlchemy warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Set page configuration
st.set_page_config(
    page_title="AI Content Generator & Analytics",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set theme to light and customize colors with clean, minimal UI
st.markdown("""
<style>
    /* Set light theme colors */
    :root {
        --background-color: #ffffff;
        --secondary-background-color: #f8f9fa;
        --primary-color: #4285F4;
        --accent-color: #34A853;
        --text-color: #202124;
        --widget-background-color: #ffffff;
        --widget-border-color: #e0e0e0;
    }
    
    /* Main container styling */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: 100%;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #202124 !important;
        font-weight: 500 !important;
        margin-bottom: 0.75rem !important;
    }
    
    h1 {
        color: #4285F4 !important;
        font-size: 2rem !important;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 1.5rem !important;
    }
    
    /* Style for text areas and input boxes */
    .stTextArea, .stTextInput {
        background-color: #ffffff !important;
        color: #202124 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 4px !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextArea:focus, .stTextInput:focus {
        border-color: #4285F4 !important;
        box-shadow: 0 1px 2px rgba(66, 133, 244, 0.1) !important;
    }
    
    /* Style for selectbox */
    .stSelectbox {
        border-radius: 4px !important;
    }
    
    .stSelectbox > div > div {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 4px !important;
        color: #202124 !important;
    }
    
    /* Style for expanders */
    .streamlit-expanderHeader {
        background-color: #f8f9fa !important;
        color: #202124 !important;
        border-radius: 4px !important;
        padding: 0.75rem !important;
        font-weight: 500 !important;
        border-left: 2px solid #4285F4 !important;
        transition: all 0.2s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #f1f3f4 !important;
    }
    
    /* Style for the content inside expanders */
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 0 0 4px 4px !important;
        padding: 1rem !important;
        margin-top: -4px !important;
        box-shadow: none !important;
    }
    
    /* Style for metrics */
    .stMetric {
        background-color: #f8f9fa !important;
        border-radius: 4px !important;
        padding: 0.75rem !important;
        border: 1px solid #e0e0e0 !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
    }
    
    .stMetric:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    }
    
    .stMetric label {
        color: #5f6368 !important;
        font-weight: 500 !important;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 600 !important;
        color: #4285F4 !important;
    }
    
    .stMetric [data-testid="stMetricDelta"] {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }
    
    /* Style for dataframes */
    .stDataFrame {
        background-color: #ffffff !important;
        border-radius: 4px !important;
        box-shadow: none !important;
        padding: 0.25rem !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    .stDataFrame [data-testid="stTable"] {
        border-radius: 4px !important;
    }
    
    .stDataFrame th {
        background-color: #f8f9fa !important;
        color: #5f6368 !important;
        font-weight: 500 !important;
    }
    
    .stDataFrame td {
        background-color: #ffffff !important;
        color: #202124 !important;
    }
    
    /* Style for tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #f8f9fa !important;
        border-radius: 4px 4px 0 0 !important;
        padding: 0.25rem 0.25rem 0 0.25rem !important;
        gap: 0.25rem !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #5f6368 !important;
        border-radius: 4px 4px 0 0 !important;
        padding: 0.5rem 0.75rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4285F4 !important;
        color: #ffffff !important;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 0 0 4px 4px !important;
        padding: 1rem !important;
    }
    
    /* Style for buttons */
    .stButton > button {
        background-color: #4285F4 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
        text-transform: none !important;
        letter-spacing: normal !important;
    }
    
    .stButton > button:hover {
        background-color: #3b78e7 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Style for sidebar */
    .css-1d391kg, .css-1wrcr25 {
        background-color: #f8f9fa !important;
    }
    
    /* Style for sliders */
    .stSlider [data-baseweb="slider"] {
        margin-top: 0.75rem !important;
        margin-bottom: 0.75rem !important;
    }
    
    .stSlider [data-baseweb="slider"] [data-testid="stThumbValue"] {
        background-color: #4285F4 !important;
        color: white !important;
        font-weight: 500 !important;
    }
    
    /* Style for radio buttons */
    .stRadio [data-testid="stRadio"] > div {
        gap: 0.25rem !important;
    }
    
    .stRadio [data-testid="stRadio"] label {
        background-color: #f8f9fa !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 4px !important;
        padding: 0.25rem 0.75rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stRadio [data-testid="stRadio"] label:hover {
        background-color: #f1f3f4 !important;
    }
    
    /* Style for checkboxes */
    .stCheckbox [data-testid="stCheckbox"] > div {
        background-color: #f8f9fa !important;
        border-radius: 4px !important;
        padding: 0.25rem !important;
    }
    
    /* Style for dividers */
    hr {
        border-color: #e0e0e0 !important;
        margin: 1.5rem 0 !important;
    }
    
    /* Style for tooltips */
    .stTooltipIcon {
        color: #4285F4 !important;
    }
    
    /* Style for warnings and errors */
    .stAlert {
        border-radius: 4px !important;
        padding: 0.75rem !important;
        margin: 0.75rem 0 !important;
        border-left: 2px solid !important;
    }
    
    .stAlert[data-baseweb="notification"] {
        background-color: #f8f9fa !important;
    }
    
    /* Success message */
    .stAlert[kind="success"] {
        border-left-color: #34A853 !important;
    }
    
    /* Info message */
    .stAlert[kind="info"] {
        border-left-color: #4285F4 !important;
    }
    
    /* Warning message */
    .stAlert[kind="warning"] {
        border-left-color: #FBBC05 !important;
    }
    
    /* Error message */
    .stAlert[kind="error"] {
        border-left-color: #EA4335 !important;
    }
    
    /* Animation for generated content */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .generated-content {
        animation: fadeIn 0.3s ease-out forwards;
    }
</style>
""", unsafe_allow_html=True)

# Add a custom header with logo and title
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 1.5rem; padding-bottom: 0.75rem; border-bottom: 1px solid #e0e0e0;">
    <div style="font-size: 2.5rem; margin-right: 0.75rem; color: #4285F4;">✨</div>
    <div>
        <h1 style="margin: 0; padding: 0; color: #4285F4; font-size: 1.75rem; font-weight: 500;">AI Content Generator & Analytics</h1>
        <p style="color: #5f6368; margin: 0; padding: 0; font-size: 0.9rem;">Create engaging social media content with AI assistance</p>
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
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <div style="font-size: 2.5rem; margin-bottom: 0.75rem; color: #4285F4;">✨</div>
        <h2 style="margin: 0; padding: 0; color: #4285F4; font-size: 1.5rem; font-weight: 500;">AI Content Generator</h2>
        <p style="color: #5f6368; margin: 0; padding: 0; font-size: 0.9rem;">Powered by Gemini AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("## Navigation")
    page = st.sidebar.radio(
        "Select a page",
        ["Content Generator", "Data Analytics"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info("""
    This application uses AI to generate social media content and analyze engagement metrics.
    
    - **Content Generator**: Create new content with AI
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

# Main app
def main():
    """Run the main app."""
    # Navigation
    page = sidebar_navigation()
    
    # Display the selected page
    if page == "Content Generator":
        content_generator_page()
    else:
        data_analytics_page()
    
    # Add footer
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding-top: 0.75rem; border-top: 1px solid #e0e0e0;">
        <p style="color: #5f6368; font-size: 0.8rem;">
            AI Content Generator & Analytics | Powered by Gemini AI | © 2025
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 