"""
Service for soil management recommendations based on weather conditions.
"""

# Dictionary of soil management practices based on weather conditions
SOIL_MANAGEMENT = {
    "irrigation": {
        "conditions": {
            "low_rainfall": True,
            "high_temp": True
        },
        "description": "Regular irrigation is needed to maintain soil moisture.",
        "practices": [
            "Drip irrigation to conserve water",
            "Early morning or evening watering to reduce evaporation",
            "Monitor soil moisture levels regularly"
        ]
    },
    "drainage": {
        "conditions": {
            "high_rainfall": True
        },
        "description": "Proper drainage is essential to prevent waterlogging.",
        "practices": [
            "Create drainage channels to remove excess water",
            "Raise beds for better drainage in heavy rainfall areas",
            "Add organic matter to improve soil structure and drainage"
        ]
    },
    "mulching": {
        "conditions": {
            "high_temp": True,
            "moderate_rainfall": True
        },
        "description": "Mulching helps conserve soil moisture and suppress weeds.",
        "practices": [
            "Apply organic mulch (straw, leaves, compost) around plants",
            "Maintain 2-4 inches of mulch depth",
            "Keep mulch away from direct contact with plant stems"
        ]
    },
    "cover_cropping": {
        "conditions": {
            "erosion_risk": True
        },
        "description": "Cover crops protect soil from erosion and add organic matter.",
        "practices": [
            "Plant cover crops during fallow periods",
            "Choose cover crops appropriate for the season",
            "Incorporate cover crops into soil before planting main crops"
        ]
    },
    "soil_testing": {
        "conditions": {
            "always": True
        },
        "description": "Regular soil testing helps monitor soil health and nutrient levels.",
        "practices": [
            "Test soil pH and nutrient levels annually",
            "Adjust fertilization based on soil test results",
            "Monitor soil organic matter content"
        ]
    },
    "organic_matter": {
        "conditions": {
            "poor_soil": True
        },
        "description": "Adding organic matter improves soil structure, fertility, and water retention.",
        "practices": [
            "Apply compost or well-rotted manure",
            "Incorporate crop residues into soil",
            "Use green manures to add organic matter"
        ]
    },
    "erosion_control": {
        "conditions": {
            "high_rainfall": True,
            "sloped_land": True
        },
        "description": "Erosion control measures prevent soil loss during heavy rainfall.",
        "practices": [
            "Contour plowing on sloped land",
            "Install erosion control barriers",
            "Maintain vegetative cover on vulnerable areas"
        ]
    },
    "conservation_tillage": {
        "conditions": {
            "erosion_risk": True,
            "dry_conditions": True
        },
        "description": "Reduced tillage helps conserve soil moisture and prevent erosion.",
        "practices": [
            "Practice no-till or minimum tillage",
            "Leave crop residues on soil surface",
            "Use appropriate equipment for conservation tillage"
        ]
    }
}

def get_soil_recommendations(weather_data, forecast_data):
    """
    Get soil management recommendations based on current weather and forecast.
    
    Args:
        weather_data (dict): Current weather data
        forecast_data (list): Forecast data for upcoming days
        
    Returns:
        list: Recommended soil management practices
    """
    if not weather_data or not forecast_data:
        return []
    
    # Extract relevant weather parameters
    current_temp = weather_data['main']['temp']
    
    # Calculate average forecast values
    avg_temp = sum(day['temp_max'] for day in forecast_data) / len(forecast_data)
    avg_rain_chance = sum(day['rain_chance'] for day in forecast_data) / len(forecast_data)
    max_wind = max(day['wind_speed'] for day in forecast_data)
    
    # Determine weather conditions
    conditions = {
        "high_temp": avg_temp > 30,
        "low_temp": avg_temp < 15,
        "high_rainfall": avg_rain_chance > 60,
        "moderate_rainfall": 30 <= avg_rain_chance <= 60,
        "low_rainfall": avg_rain_chance < 30,
        "erosion_risk": avg_rain_chance > 50 or max_wind > 20,
        "dry_conditions": avg_rain_chance < 30 and avg_temp > 25,
        "sloped_land": True,  # Assuming sloped land by default
        "poor_soil": True,    # Assuming soil needs improvement by default
        "always": True
    }
    
    # Get recommended practices
    recommendations = []
    
    for practice_name, practice_info in SOIL_MANAGEMENT.items():
        # Check if all required conditions are met
        if all(conditions.get(condition, False) == value for condition, value in practice_info["conditions"].items()):
            recommendations.append({
                "name": practice_name.replace("_", " ").title(),
                "description": practice_info["description"],
                "practices": practice_info["practices"]
            })
    
    return recommendations
