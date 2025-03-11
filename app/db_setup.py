import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, MetaData, Table, Date, UUID, text
from sqlalchemy.sql import func
import psycopg2
import warnings

# Suppress SQLAlchemy warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Load environment variables
load_dotenv()

def check_table_exists():
    """Check if the social_media_content table already exists."""
    try:
        # Get database connection string from environment variables
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            print("Error: DATABASE_URL environment variable not found.")
            return False
        
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        
        # Check if table exists
        with engine.connect() as conn:
            result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'social_media_content'
            )
            """))
            exists = result.scalar()
            
            if exists:
                print("Table 'social_media_content' already exists.")
                return True
            else:
                print("Table 'social_media_content' does not exist.")
                return False
    
    except Exception as e:
        print(f"Error checking if table exists: {e}")
        return False

def create_tables():
    """Create database tables if they don't exist."""
    try:
        # Get database connection string from environment variables
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            print("Error: DATABASE_URL environment variable not found.")
            return False
        
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        
        # Create metadata object
        metadata = MetaData()
        
        # Define social_media_content table based on the existing structure
        social_media_content = Table(
            'social_media_content',
            metadata,
            Column('business_id', UUID, primary_key=True),
            Column('content_type', String(5), nullable=False),
            Column('platform', String(9), nullable=False),
            Column('url', Text),
            Column('full_content', Text, nullable=False),
            Column('scraped_date', Date),
            Column('likes_count', Integer, default=0),
            Column('views_count', Integer, default=0),
            Column('comments_count', Integer, default=0),
            Column('shares_count', Integer, default=0),
            Column('saves_count', Integer, default=0),
            Column('hashtags', Text),
            Column('created_at', DateTime, server_default=func.now()),
            Column('updated_at', DateTime, onupdate=func.now())
        )
        
        # Create tables in the database
        metadata.create_all(engine)
        
        print("Database tables created successfully.")
        return True
    
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False

def seed_sample_data():
    """Seed the database with sample data."""
    try:
        # Get database connection string from environment variables
        connection_string = os.getenv("DATABASE_URL")
        if not connection_string:
            print("Error: DATABASE_URL environment variable not found.")
            return False
        
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        
        # Sample data
        sample_data = [
            {
                "business_id": "c1fc6192-979c-4b70-a064-7d3c7ae15903",
                "content_type": "video",
                "platform": "TikTok",
                "url": "https://www.tiktok.com/example1",
                "full_content": "Check out our new product launch! #NewProduct #Exciting",
                "scraped_date": "2025-03-11",
                "likes_count": 120,
                "views_count": 1500,
                "comments_count": 25,
                "shares_count": 10,
                "saves_count": 5,
                "hashtags": "NewProduct,Exciting"
            },
            {
                "business_id": "d2fc6192-979c-4b70-a064-7d3c7ae15904",
                "content_type": "image",
                "platform": "Instagram",
                "url": "https://www.instagram.com/example2",
                "full_content": "Beautiful sunset at our office today! #WorkLife #Sunset",
                "scraped_date": "2025-03-11",
                "likes_count": 250,
                "views_count": 0,
                "comments_count": 15,
                "shares_count": 5,
                "saves_count": 20,
                "hashtags": "WorkLife,Sunset"
            },
            {
                "business_id": "e3fc6192-979c-4b70-a064-7d3c7ae15905",
                "content_type": "text",
                "platform": "Twitter",
                "url": "https://www.twitter.com/example3",
                "full_content": "Excited to announce our new partnership with @PartnerCompany! #Partnership #Growth",
                "scraped_date": "2025-03-11",
                "likes_count": 75,
                "views_count": 1000,
                "comments_count": 8,
                "shares_count": 30,
                "saves_count": 0,
                "hashtags": "Partnership,Growth"
            }
        ]
        
        # Insert sample data using SQLAlchemy
        with engine.connect() as conn:
            for data in sample_data:
                conn.execute(
                    text("""
                    INSERT INTO social_media_content 
                    (business_id, content_type, platform, url, full_content, scraped_date,
                     likes_count, views_count, comments_count, shares_count, saves_count, hashtags) 
                    VALUES (:business_id, :content_type, :platform, :url, :full_content, :scraped_date,
                     :likes_count, :views_count, :comments_count, :shares_count, :saves_count, :hashtags)
                    ON CONFLICT (business_id) DO NOTHING
                    """),
                    {
                        "business_id": data["business_id"],
                        "content_type": data["content_type"],
                        "platform": data["platform"],
                        "url": data["url"],
                        "full_content": data["full_content"],
                        "scraped_date": data["scraped_date"],
                        "likes_count": data["likes_count"],
                        "views_count": data["views_count"],
                        "comments_count": data["comments_count"],
                        "shares_count": data["shares_count"],
                        "saves_count": data["saves_count"],
                        "hashtags": data["hashtags"]
                    }
                )
            conn.commit()
        
        print("Sample data seeded successfully.")
        return True
    
    except Exception as e:
        print(f"Error seeding sample data: {e}")
        return False

if __name__ == "__main__":
    print("Setting up database...")
    if not check_table_exists():
        if create_tables():
            seed_sample_data()
    print("Database setup complete.") 