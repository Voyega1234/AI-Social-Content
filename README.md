# AI Social Content Generator

A comprehensive application for generating social media content, creating AI images, analyzing client information, and visualizing data analytics using Streamlit and AI services.

## Features

- **Content Generator**: Create social media content for various platforms using AI
- **Image Creator**: Generate images using Ideogram API with various prompts and styles
- **Client Information**: Analyze client information and generate audience insights
- **Data Analytics**: Visualize social media performance metrics and gain insights

## Directory Structure

```
app/
├── data/               # Database and data files
├── pages/              # Page classes for the application
│   ├── client_info.py  # Client information page
│   ├── content_generator.py  # Content generator page
│   ├── data_analytics.py  # Data analytics page
│   ├── image_creator.py  # Image creator page
├── services/           # API service integrations
│   ├── gemini_service.py  # Google Gemini API service
│   ├── ideogram_service.py  # Ideogram API service
├── static/             # Static files (CSS, images)
│   ├── logo.png        # Application logo
│   ├── style.css       # CSS styles
├── utils/              # Utility functions
│   ├── database.py     # Database manager
│   ├── ui.py           # UI utility functions
│   ├── validators.py   # Input validation functions
├── main.py             # Main application entry point
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-social-content.git
cd ai-social-content
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
GEMINI_API_KEY=your_gemini_api_key
IDEOGRAM_API_KEY=your_ideogram_api_key
```

## Usage

1. Run the application:
```bash
streamlit run app/main.py
```

2. Open your browser and navigate to `http://localhost:8501`

3. Use the sidebar to navigate between different pages:
   - Content Generator
   - Image Creator
   - Client Information
   - Data Analytics

## API Keys

This application requires API keys for the following services:

- **Google Gemini API**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Ideogram API**: Get your API key from [Ideogram](https://ideogram.ai/api)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 