# AI Content Generator & Analytics

A Streamlit web application that uses AI to generate social media content ideas and captions, and provides analytics on your content data.

## Features

- **AI Content Generation**: Generate social media content ideas, captions, hashtags, and campaign ideas using OpenAI's GPT models.
- **Content Database**: Store generated content in a PostgreSQL database for future reference.
- **Data Analytics**: Visualize and analyze your content data with interactive charts and tables.

## Prerequisites

- Python 3.8+
- PostgreSQL database
- OpenAI API key

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd ai_content_generator
   ```

2. Set up a virtual environment using UV:
   ```
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file with your database and OpenAI API credentials.

5. Set up the database:
   ```
   python app/db_setup.py
   ```

## Usage

1. Start the Streamlit application:
   ```
   streamlit run app/app.py
   ```

2. Open your web browser and navigate to the URL displayed in the terminal (usually http://localhost:8501).

3. Use the sidebar to navigate between the Content Generator and Data Analytics pages.

## Content Generator

1. Select the social media platform, content type, industry, and tone.
2. Add any additional context or keywords.
3. Click "Generate Content" to create AI-generated content.
4. Save the generated content to the database if desired.

## Data Analytics

View analytics about your stored content, including:
- Content distribution by platform
- Content distribution by type
- Content distribution by industry
- Recent content entries

## Database Schema

The application uses a PostgreSQL database with the following schema:

```sql
CREATE TABLE social_media_content (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    tone VARCHAR(50),
    content TEXT NOT NULL,
    additional_context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

## License

[MIT License](LICENSE) 