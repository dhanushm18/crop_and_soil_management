"""
Weather-Aware Crop and Soil Management Application

A Flask application that provides crop recommendations and soil management
advice based on weather conditions from the OpenWeatherMap API.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import weather_service
import crop_service
import soil_service
from config import DEFAULT_LOCATION

app = Flask(__name__)
app.config.from_pyfile('config.py')

@app.route('/')
def index():
    """Home page route."""
    return render_template('index.html')

@app.route('/weather', methods=['GET', 'POST'])
def weather():
    """Weather information route."""
    if request.method == 'POST':
        city = request.form.get('city', DEFAULT_LOCATION['city'])
        country = request.form.get('country', DEFAULT_LOCATION['country'])
    else:
        city = request.args.get('city', DEFAULT_LOCATION['city'])
        country = request.args.get('country', DEFAULT_LOCATION['country'])
    
    # Get current weather and forecast
    current_weather = weather_service.get_current_weather(city, country)
    forecast = weather_service.get_processed_forecast(city, country)
    
    if not current_weather:
        error_message = "Unable to fetch weather data. Please check the location and try again."
        return render_template('weather.html', error=error_message)
    
    # Format date for display
    current_date = datetime.now().strftime('%A, %B %d, %Y')
    
    return render_template(
        'weather.html',
        current_weather=current_weather,
        forecast=forecast,
        current_date=current_date,
        city=city,
        country=country
    )

@app.route('/crops', methods=['GET', 'POST'])
def crops():
    """Crop recommendations route."""
    if request.method == 'POST':
        city = request.form.get('city', DEFAULT_LOCATION['city'])
        country = request.form.get('country', DEFAULT_LOCATION['country'])
    else:
        city = request.args.get('city', DEFAULT_LOCATION['city'])
        country = request.args.get('country', DEFAULT_LOCATION['country'])
    
    # Get current weather and forecast
    current_weather = weather_service.get_current_weather(city, country)
    forecast = weather_service.get_processed_forecast(city, country)
    
    if not current_weather or not forecast:
        error_message = "Unable to fetch weather data. Please check the location and try again."
        return render_template('crops.html', error=error_message)
    
    # Get crop recommendations
    crop_recommendations = crop_service.get_crop_recommendations(current_weather, forecast)
    
    return render_template(
        'crops.html',
        crop_recommendations=crop_recommendations,
        city=city,
        country=country
    )

@app.route('/soil', methods=['GET', 'POST'])
def soil():
    """Soil management route."""
    if request.method == 'POST':
        city = request.form.get('city', DEFAULT_LOCATION['city'])
        country = request.form.get('country', DEFAULT_LOCATION['country'])
    else:
        city = request.args.get('city', DEFAULT_LOCATION['city'])
        country = request.args.get('country', DEFAULT_LOCATION['country'])
    
    # Get current weather and forecast
    current_weather = weather_service.get_current_weather(city, country)
    forecast = weather_service.get_processed_forecast(city, country)
    
    if not current_weather or not forecast:
        error_message = "Unable to fetch weather data. Please check the location and try again."
        return render_template('soil.html', error=error_message)
    
    # Get soil management recommendations
    soil_recommendations = soil_service.get_soil_recommendations(current_weather, forecast)
    
    return render_template(
        'soil.html',
        soil_recommendations=soil_recommendations,
        city=city,
        country=country
    )

if __name__ == '__main__':
    app.run(debug=True)
