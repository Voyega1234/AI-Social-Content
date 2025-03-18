# AI Social Content Generator - Code Structure

This document explains the new object-oriented structure of the AI Social Content Generator application.

## Directory Structure

```
app/
├── __init__.py                # Package initialization
├── main.py                    # Entry point with the main() function
├── app.py                     # Legacy monolithic application (for reference)
├── utils/                     # Utility functions
│   ├── __init__.py            # Package initialization
│   ├── database.py            # Database connection functions
│   ├── ui.py                  # UI helper functions (CSS, navigation)
│   └── validators.py          # Validation functions (color validation, etc.)
├── services/                  # External service integrations
│   ├── __init__.py            # Package initialization
│   ├── gemini_service.py      # Gemini API integration
│   └── ideogram_service.py    # Ideogram API integration
├── pages/                     # Application pages
│   ├── __init__.py            # Package initialization with BasePage class
│   ├── content_generator.py   # Content Generator page
│   ├── image_creator.py       # Image Creator page
│   ├── data_analytics.py      # Data Analytics page
│   └── client_info.py         # Client Information page
└── static/                    # Static assets
    └── css/                   # CSS stylesheets
```

## Key Classes and Their Responsibilities

### Utils

- **DatabaseManager**: Handles database connections and query execution
- **ColorValidator**: Validates and formats color values

### Services

- **GeminiService**: Manages interactions with the Gemini API
- **IdeogramService**: Manages interactions with the Ideogram API

### Pages

- **BasePage**: Abstract base class for all pages
- **ContentGeneratorPage**: Handles the Content Generator page functionality
- **ImageCreatorPage**: Handles the Image Creator page functionality
- **DataAnalyticsPage**: Handles the Data Analytics page functionality
- **ClientInformationPage**: Handles the Client Information page functionality

## How to Run

You can run the application using:

```bash
streamlit run app/main.py
```

## Legacy Support

For backward compatibility, the application includes legacy functions that map to the new OOP structure. This allows existing code to continue working without modification.

## Migrating from Legacy to OOP

To migrate from the legacy monolithic structure to the new OOP structure:

1. Import the appropriate class from the new structure
2. Create an instance of the class
3. Call the appropriate method on the instance

Example:

```python
# Legacy code
from app import get_db_connection
connection = get_db_connection()

# New OOP code
from utils.database import DatabaseManager
connection = DatabaseManager.get_connection()
``` 