# AI Social Content Generator

A powerful AI-powered tool for creating engaging social media content, generating professional images, and analyzing performance metrics.

![AI Social Content Generator](https://img.shields.io/badge/AI-Social%20Content%20Generator-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-FF4B4B)
![Python](https://img.shields.io/badge/Python-3.9+-blue)

## 🌟 Features

### 📝 Content Generator
- Create engaging social media posts for multiple platforms
- Customize content based on business type and target audience
- Generate variations of content with different tones and styles
- Save and export content for later use

### 🎨 Image Creator
- Generate professional AI images for social media
- Create cohesive storyboards with multiple related images
- Customize images with specific color palettes
- Upload reference images to guide the AI generation
- Support for various aspect ratios and image styles

### 📊 Data Analytics
- Track social media performance metrics
- Analyze engagement patterns across platforms
- Visualize data with interactive charts and graphs
- Generate insights and recommendations

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- PostgreSQL database (for analytics features)
- Gemini API key (for content generation)
- Ideogram API key (for image generation)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/yourusername/AI-Social-Content.git
   cd AI-Social-Content
   ```

2. Create and activate a virtual environment (recommended)
   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory with the following variables:
   ```
   GEMINI_API_KEY=your_gemini_api_key
   IDEOGRAM_API_KEY=your_ideogram_api_key
   DATABASE_URL=postgresql://username:password@localhost:5432/database_name
   ```

### Database Setup

1. Create a PostgreSQL database
2. Run the database setup script
   ```bash
   python app/db_setup.py
   ```
3. Verify the database tables were created correctly
   ```bash
   python app/check_table.py
   ```

## 🖥️ Running the Application

Start the Streamlit application:

```bash
streamlit run app/app.py
```

The application will be available at http://localhost:8501 in your web browser.

## 🧩 Application Structure

```
AI-Social-Content/
├── app/                      # Main application directory
│   ├── app.py                # Main Streamlit application
│   ├── __init__.py           # Package initialization
│   ├── db_setup.py           # Database setup script
│   ├── check_table.py        # Database verification script
│   └── static/               # Static assets
│       └── css/              # CSS stylesheets
├── .env                      # Environment variables (not tracked in git)
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## 🛠️ Technologies Used

- **Streamlit**: Web application framework
- **Gemini AI**: Content generation
- **Ideogram API**: Image generation
- **PostgreSQL**: Database for analytics
- **Pandas & Plotly**: Data processing and visualization
- **SQLAlchemy**: Database ORM

## 🔍 Key Features Explained

### Color Palette Management
The application allows users to define custom color palettes for image generation. These colors are passed to the Ideogram API to ensure brand consistency across generated images.

### Storyboard Generation
Create a series of 4 related images that tell a cohesive visual story, perfect for marketing campaigns or product launches. The AI ensures consistent styling and color usage across all images.

### Reference Image Analysis
Upload reference images to guide the AI in generating similar styles or incorporating specific elements from your existing brand assets.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [Streamlit](https://streamlit.io/) for the amazing web app framework
- [Gemini AI](https://ai.google.dev/) for the powerful content generation capabilities
- [Ideogram](https://ideogram.ai/) for the image generation API 