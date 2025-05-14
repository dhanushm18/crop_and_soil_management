from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import os
import random
from datetime import datetime

app = Flask(__name__)

# Sample crop data
crops = [
    {
        "id": 1,
        "name": "Rice",
        "cost_per_acre": 25000,
        "yield_per_acre": 2000,  # kg
        "price_per_kg": 20,
        "growing_period": 120,  # days
        "water_requirement": "High",
        "labor_requirement": "Medium",
        "suitable_season": "Kharif",
        "soil_type": "Clay",
        "fertilizer_requirement": "High",
        "pest_resistance": "Medium"
    },
    {
        "id": 2,
        "name": "Wheat",
        "cost_per_acre": 20000,
        "yield_per_acre": 1800,  # kg
        "price_per_kg": 25,
        "growing_period": 150,  # days
        "water_requirement": "Medium",
        "labor_requirement": "Low",
        "suitable_season": "Rabi",
        "soil_type": "Loamy",
        "fertilizer_requirement": "Medium",
        "pest_resistance": "Medium"
    },
    {
        "id": 3,
        "name": "Cotton",
        "cost_per_acre": 35000,
        "yield_per_acre": 800,  # kg
        "price_per_kg": 60,
        "growing_period": 180,  # days
        "water_requirement": "Medium",
        "labor_requirement": "High",
        "suitable_season": "Kharif",
        "soil_type": "Black",
        "fertilizer_requirement": "High",
        "pest_resistance": "Low"
    },
    {
        "id": 4,
        "name": "Sugarcane",
        "cost_per_acre": 40000,
        "yield_per_acre": 40000,  # kg
        "price_per_kg": 3,
        "growing_period": 360,  # days
        "water_requirement": "High",
        "labor_requirement": "High",
        "suitable_season": "Year-round",
        "soil_type": "Loamy",
        "fertilizer_requirement": "High",
        "pest_resistance": "Medium"
    },
    {
        "id": 5,
        "name": "Maize",
        "cost_per_acre": 18000,
        "yield_per_acre": 2500,  # kg
        "price_per_kg": 15,
        "growing_period": 100,  # days
        "water_requirement": "Medium",
        "labor_requirement": "Medium",
        "suitable_season": "Kharif/Rabi",
        "soil_type": "Sandy Loam",
        "fertilizer_requirement": "Medium",
        "pest_resistance": "Medium"
    },
    {
        "id": 6,
        "name": "Soybean",
        "cost_per_acre": 22000,
        "yield_per_acre": 1500,  # kg
        "price_per_kg": 35,
        "growing_period": 110,  # days
        "water_requirement": "Medium",
        "labor_requirement": "Low",
        "suitable_season": "Kharif",
        "soil_type": "Loamy",
        "fertilizer_requirement": "Low",
        "pest_resistance": "High"
    },
    {
        "id": 7,
        "name": "Potato",
        "cost_per_acre": 45000,
        "yield_per_acre": 20000,  # kg
        "price_per_kg": 10,
        "growing_period": 90,  # days
        "water_requirement": "Medium",
        "labor_requirement": "High",
        "suitable_season": "Rabi",
        "soil_type": "Sandy Loam",
        "fertilizer_requirement": "High",
        "pest_resistance": "Low"
    },
    {
        "id": 8,
        "name": "Tomato",
        "cost_per_acre": 50000,
        "yield_per_acre": 25000,  # kg
        "price_per_kg": 15,
        "growing_period": 120,  # days
        "water_requirement": "High",
        "labor_requirement": "High",
        "suitable_season": "Year-round",
        "soil_type": "Loamy",
        "fertilizer_requirement": "High",
        "pest_resistance": "Low"
    },
    {
        "id": 9,
        "name": "Groundnut",
        "cost_per_acre": 28000,
        "yield_per_acre": 1200,  # kg
        "price_per_kg": 45,
        "growing_period": 130,  # days
        "water_requirement": "Low",
        "labor_requirement": "Medium",
        "suitable_season": "Kharif",
        "soil_type": "Sandy Loam",
        "fertilizer_requirement": "Medium",
        "pest_resistance": "Medium"
    },
    {
        "id": 10,
        "name": "Mustard",
        "cost_per_acre": 15000,
        "yield_per_acre": 1000,  # kg
        "price_per_kg": 40,
        "growing_period": 120,  # days
        "water_requirement": "Low",
        "labor_requirement": "Low",
        "suitable_season": "Rabi",
        "soil_type": "Loamy",
        "fertilizer_requirement": "Low",
        "pest_resistance": "Medium"
    }
]

# Calculate profit for each crop
for crop in crops:
    revenue = crop["yield_per_acre"] * crop["price_per_kg"]
    profit = revenue - crop["cost_per_acre"]
    roi = (profit / crop["cost_per_acre"]) * 100

    crop["revenue"] = revenue
    crop["profit"] = profit
    crop["roi"] = roi

@app.route('/')
def index():
    return render_template('index.html', crops=crops)

@app.route('/api/crops')
def get_crops():
    return jsonify(crops)

@app.route('/api/compare')
def compare_crops():
    selected_crops = request.args.getlist('crop_ids')
    selected_crops = [int(crop_id) for crop_id in selected_crops]

    filtered_crops = [crop for crop in crops if crop["id"] in selected_crops]

    return jsonify(filtered_crops)

@app.route('/crop/<int:crop_id>')
def crop_detail(crop_id):
    crop = next((c for c in crops if c["id"] == crop_id), None)
    if crop:
        return render_template('crop_detail.html', crop=crop)
    return "Crop not found", 404

# Function to generate "predicted" yield based on input parameters
def predict_yield(crop_name, soil_type, water_level, fertilizer_level, season):
    # Get base yield from our crop data
    base_crop = next((c for c in crops if c["name"].lower() == crop_name.lower()), None)

    if not base_crop:
        # Default base yield if crop not found
        base_yield = 2000
    else:
        base_yield = base_crop["yield_per_acre"]

    # Apply "adjustments" based on parameters (dummy ML prediction)
    # Soil type factor
    soil_factors = {
        "clay": 1.0,
        "loamy": 1.2,
        "sandy": 0.8,
        "black": 1.1,
        "red": 0.9,
        "sandy loam": 1.05
    }
    soil_factor = soil_factors.get(soil_type.lower(), 1.0)

    # Water level factor
    water_factors = {
        "low": 0.7,
        "medium": 1.0,
        "high": 1.3
    }
    water_factor = water_factors.get(water_level.lower(), 1.0)

    # Fertilizer level factor
    fertilizer_factors = {
        "low": 0.8,
        "medium": 1.0,
        "high": 1.25
    }
    fertilizer_factor = fertilizer_factors.get(fertilizer_level.lower(), 1.0)

    # Season suitability factor
    season_factor = 1.0
    if base_crop:
        if season.lower() in base_crop["suitable_season"].lower():
            season_factor = 1.2
        else:
            season_factor = 0.7

    # Add some randomness to simulate "prediction uncertainty"
    random_factor = random.uniform(0.9, 1.1)

    # Calculate predicted yield
    predicted_yield = base_yield * soil_factor * water_factor * fertilizer_factor * season_factor * random_factor

    return round(predicted_yield)

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    soil_types = ["Clay", "Loamy", "Sandy", "Black", "Red", "Sandy Loam"]
    water_levels = ["Low", "Medium", "High"]
    fertilizer_levels = ["Low", "Medium", "High"]
    seasons = ["Kharif", "Rabi", "Summer", "Winter", "Year-round"]

    prediction_result = None

    if request.method == 'POST':
        crop_name = request.form.get('crop_name')
        soil_type = request.form.get('soil_type')
        water_level = request.form.get('water_level')
        fertilizer_level = request.form.get('fertilizer_level')
        season = request.form.get('season')

        # Get the base crop data
        base_crop = next((c for c in crops if c["name"].lower() == crop_name.lower()), None)

        if base_crop:
            # Generate predicted yield
            predicted_yield = predict_yield(crop_name, soil_type, water_level, fertilizer_level, season)

            # Calculate predicted revenue and profit
            price_per_kg = base_crop["price_per_kg"]
            cost_per_acre = base_crop["cost_per_acre"]

            predicted_revenue = predicted_yield * price_per_kg
            predicted_profit = predicted_revenue - cost_per_acre
            predicted_roi = (predicted_profit / cost_per_acre) * 100

            prediction_result = {
                "crop_name": crop_name,
                "soil_type": soil_type,
                "water_level": water_level,
                "fertilizer_level": fertilizer_level,
                "season": season,
                "yield_per_acre": predicted_yield,
                "revenue": predicted_revenue,
                "profit": predicted_profit,
                "roi": predicted_roi
            }

    return render_template('predict.html',
                          crops=crops,
                          soil_types=soil_types,
                          water_levels=water_levels,
                          fertilizer_levels=fertilizer_levels,
                          seasons=seasons,
                          prediction_result=prediction_result)

if __name__ == '__main__':
    app.run(debug=True)
