"""
Service for interacting with the OpenWeatherMap API.
"""

import requests
from config import API_KEY, BASE_URL, UNITS

def get_current_weather(city, country=None):
    """
    Get current weather data for a specific location.
    
    Args:
        city (str): City name
        country (str, optional): Country code (e.g., 'US', 'IN')
        
    Returns:
        dict: Weather data or None if request failed
    """
    location = city
    if country:
        location = f"{city},{country}"
        
    params = {
        'q': location,
        'appid': API_KEY,
        'units': UNITS
    }
    
    try:
        response = requests.get(f"{BASE_URL}/weather", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching current weather: {e}")
        return None

def get_weather_forecast(city, country=None, days=5):
    """
    Get weather forecast for a specific location.
    
    Args:
        city (str): City name
        country (str, optional): Country code (e.g., 'US', 'IN')
        days (int, optional): Number of days for forecast (max 5)
        
    Returns:
        dict: Forecast data or None if request failed
    """
    location = city
    if country:
        location = f"{city},{country}"
        
    params = {
        'q': location,
        'appid': API_KEY,
        'units': UNITS,
        'cnt': days * 8  # API returns data in 3-hour intervals (8 per day)
    }
    
    try:
        response = requests.get(f"{BASE_URL}/forecast", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather forecast: {e}")
        return None

def get_processed_forecast(city, country=None):
    """
    Get processed forecast data organized by day.
    
    Args:
        city (str): City name
        country (str, optional): Country code
        
    Returns:
        list: List of daily forecast data
    """
    forecast_data = get_weather_forecast(city, country)
    if not forecast_data or 'list' not in forecast_data:
        return []
    
    # Process the forecast data to organize by day
    daily_forecasts = {}
    for item in forecast_data['list']:
        # Extract date (without time)
        date = item['dt_txt'].split(' ')[0]
        
        if date not in daily_forecasts:
            daily_forecasts[date] = {
                'date': date,
                'temp_min': float('inf'),
                'temp_max': float('-inf'),
                'humidity': 0,
                'weather_conditions': [],
                'wind_speed': 0,
                'rain_chance': 0,
                'samples': 0
            }
        
        # Update min/max temperature
        daily_forecasts[date]['temp_min'] = min(daily_forecasts[date]['temp_min'], item['main']['temp_min'])
        daily_forecasts[date]['temp_max'] = max(daily_forecasts[date]['temp_max'], item['main']['temp_max'])
        
        # Accumulate values for averaging later
        daily_forecasts[date]['humidity'] += item['main']['humidity']
        daily_forecasts[date]['wind_speed'] += item['wind']['speed']
        
        # Track weather conditions
        weather_condition = item['weather'][0]['main']
        if weather_condition not in daily_forecasts[date]['weather_conditions']:
            daily_forecasts[date]['weather_conditions'].append(weather_condition)
        
        # Check for rain probability
        if 'rain' in item or 'Rain' in weather_condition:
            daily_forecasts[date]['rain_chance'] += 1
        
        daily_forecasts[date]['samples'] += 1
    
    # Calculate averages
    for date, data in daily_forecasts.items():
        samples = data['samples']
        data['humidity'] = round(data['humidity'] / samples)
        data['wind_speed'] = round(data['wind_speed'] / samples, 1)
        data['rain_chance'] = round((data['rain_chance'] / samples) * 100)
    
    # Convert to list and sort by date
    return sorted(daily_forecasts.values(), key=lambda x: x['date'])
