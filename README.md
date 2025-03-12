# AI Social Content Generator

A comprehensive tool for generating social media content, analyzing performance metrics, and creating AI-powered images.

## Features

- **Content Generator**: Create engaging social media content for various platforms
- **Image Creator**: Generate stunning images using AI
- **Data Analytics**: Analyze social media performance metrics

## Project Structure

The project follows a modular structure:

```
AI-Social-Content/
├── app/
│   ├── __init__.py
│   ├── app.py
│   ├── main.py
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── utils/
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── ideogram.py
│   │   ├── ui/
│   │   │   └── __init__.py
│   │   ├── image_creator/
│   │   │   ├── __init__.py
│   │   │   └── display.py
│   │   ├── content_generator/
│   │   │   └── __init__.py
│   │   └── data_analytics/
│   │       └── __init__.py
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory with the following variables:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   IDEOGRAM_API_KEY=your_ideogram_api_key
   DATABASE_URL=your_database_connection_string
   ```

## Running the Application

You can run the application using either of the following commands:

```bash
streamlit run app/main.py
```

or

```bash
streamlit run app/app.py
```

## Troubleshooting

If you encounter import errors, make sure:
1. The `app` directory has an `__init__.py` file
2. You're using relative imports within modules
3. You're running the application from the project root directory

## Dependencies

- streamlit
- pandas
- plotly
- sqlalchemy
- google-generativeai
- requests
- pillow
- python-dotenv 