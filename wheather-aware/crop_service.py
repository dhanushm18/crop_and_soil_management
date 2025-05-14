"""
Service for crop recommendations based on weather conditions.
"""

# Dictionary of crops with their optimal growing conditions
CROP_DATA = {
    "rice": {
        "temp_min": 20,
        "temp_max": 35,
        "humidity_min": 60,
        "humidity_max": 90,
        "rainfall_needed": "high",
        "season": ["summer", "monsoon"],
        "description": "Rice is a staple food crop that thrives in warm, humid conditions with plenty of water."
    },
    "wheat": {
        "temp_min": 15,
        "temp_max": 25,
        "humidity_min": 40,
        "humidity_max": 70,
        "rainfall_needed": "moderate",
        "season": ["winter", "spring"],
        "description": "Wheat is a cereal grain that grows best in cool, dry conditions with moderate rainfall."
    },
    "maize": {
        "temp_min": 18,
        "temp_max": 32,
        "humidity_min": 50,
        "humidity_max": 80,
        "rainfall_needed": "moderate",
        "season": ["summer", "monsoon"],
        "description": "Maize (corn) is a versatile crop that requires warm temperatures and moderate rainfall."
    },
    "cotton": {
        "temp_min": 20,
        "temp_max": 35,
        "humidity_min": 40,
        "humidity_max": 70,
        "rainfall_needed": "moderate",
        "season": ["summer", "monsoon"],
        "description": "Cotton is a fiber crop that grows well in warm, sunny conditions with moderate humidity."
    },
    "sugarcane": {
        "temp_min": 20,
        "temp_max": 38,
        "humidity_min": 60,
        "humidity_max": 85,
        "rainfall_needed": "high",
        "season": ["summer", "monsoon"],
        "description": "Sugarcane is a tropical crop that requires high temperatures, humidity, and rainfall."
    },
    "tomato": {
        "temp_min": 18,
        "temp_max": 30,
        "humidity_min": 50,
        "humidity_max": 70,
        "rainfall_needed": "moderate",
        "season": ["spring", "summer"],
        "description": "Tomatoes are a popular vegetable crop that grows best in warm, sunny conditions with moderate humidity."
    },
    "potato": {
        "temp_min": 15,
        "temp_max": 25,
        "humidity_min": 60,
        "humidity_max": 80,
        "rainfall_needed": "moderate",
        "season": ["winter", "spring"],
        "description": "Potatoes are a root vegetable that prefers cool temperatures and moderate rainfall."
    },
    "onion": {
        "temp_min": 13,
        "temp_max": 28,
        "humidity_min": 50,
        "humidity_max": 70,
        "rainfall_needed": "low",
        "season": ["winter", "spring"],
        "description": "Onions are a bulb vegetable that grows well in cool to moderate temperatures with low to moderate rainfall."
    }
}

def get_season(month):
    """
    Determine the current season based on the month.
    
    Args:
        month (int): Month number (1-12)
        
    Returns:
        str: Season name
    """
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:  # 9, 10, 11
        return "monsoon"

def get_rainfall_category(rain_chance):
    """
    Categorize rainfall based on the chance of rain.
    
    Args:
        rain_chance (int): Percentage chance of rain
        
    Returns:
        str: Rainfall category (low, moderate, high)
    """
    if rain_chance < 30:
        return "low"
    elif rain_chance < 60:
        return "moderate"
    else:
        return "high"

def get_crop_recommendations(weather_data, forecast_data):
    """
    Get crop recommendations based on current weather and forecast.
    
    Args:
        weather_data (dict): Current weather data
        forecast_data (list): Forecast data for upcoming days
        
    Returns:
        dict: Recommended crops with scores and reasons
    """
    if not weather_data or not forecast_data:
        return {}
    
    # Extract relevant weather parameters
    current_temp = weather_data['main']['temp']
    current_humidity = weather_data['main']['humidity']
    
    # Calculate average forecast values
    avg_temp = sum(day['temp_max'] for day in forecast_data) / len(forecast_data)
    avg_humidity = sum(day['humidity'] for day in forecast_data) / len(forecast_data)
    avg_rain_chance = sum(day['rain_chance'] for day in forecast_data) / len(forecast_data)
    
    # Determine rainfall category
    rainfall = get_rainfall_category(avg_rain_chance)
    
    # Determine current season (using the month from the first forecast day)
    import datetime
    current_month = datetime.datetime.now().month
    current_season = get_season(current_month)
    
    # Score each crop based on weather conditions
    crop_scores = {}
    
    for crop_name, crop_info in CROP_DATA.items():
        score = 0
        reasons = []
        
        # Check temperature suitability
        if crop_info['temp_min'] <= avg_temp <= crop_info['temp_max']:
            score += 30
            reasons.append(f"Temperature ({avg_temp:.1f}°C) is optimal")
        elif abs(avg_temp - (crop_info['temp_min'] + crop_info['temp_max']) / 2) < 5:
            score += 15
            reasons.append(f"Temperature ({avg_temp:.1f}°C) is acceptable")
        else:
            reasons.append(f"Temperature ({avg_temp:.1f}°C) is not ideal")
        
        # Check humidity suitability
        if crop_info['humidity_min'] <= avg_humidity <= crop_info['humidity_max']:
            score += 25
            reasons.append(f"Humidity ({avg_humidity:.1f}%) is optimal")
        elif abs(avg_humidity - (crop_info['humidity_min'] + crop_info['humidity_max']) / 2) < 10:
            score += 10
            reasons.append(f"Humidity ({avg_humidity:.1f}%) is acceptable")
        else:
            reasons.append(f"Humidity ({avg_humidity:.1f}%) is not ideal")
        
        # Check rainfall suitability
        if crop_info['rainfall_needed'] == rainfall:
            score += 25
            reasons.append(f"Expected rainfall is optimal")
        elif (crop_info['rainfall_needed'] == "moderate" and rainfall in ["low", "high"]) or \
             (crop_info['rainfall_needed'] in ["low", "high"] and rainfall == "moderate"):
            score += 10
            reasons.append(f"Expected rainfall is acceptable")
        else:
            reasons.append(f"Expected rainfall is not ideal")
        
        # Check season suitability
        if current_season in crop_info['season']:
            score += 20
            reasons.append(f"Current season ({current_season}) is suitable")
        else:
            reasons.append(f"Current season ({current_season}) is not ideal")
        
        crop_scores[crop_name] = {
            "score": score,
            "reasons": reasons,
            "description": crop_info["description"]
        }
    
    # Sort crops by score (descending)
    sorted_crops = {k: v for k, v in sorted(crop_scores.items(), key=lambda item: item[1]["score"], reverse=True)}
    
    return sorted_crops
