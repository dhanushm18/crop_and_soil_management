"""
Configuration settings for the Weather-Aware Crop and Soil Management application.
"""

# OpenWeatherMap API key
API_KEY = "b1b15e88fa797225412429c1c50c122a1"

# OpenWeatherMap API base URL
BASE_URL = "https://api.openweathermap.org/data/2.5"

# Default location (can be overridden by user input)
DEFAULT_LOCATION = {
    "city": "Bangalore",
    "country": "IN"
}

# Units for weather data (metric, imperial, standard)
UNITS = "metric"

# Flask app settings
DEBUG = True
SECRET_KEY = "your-secret-key-here"
