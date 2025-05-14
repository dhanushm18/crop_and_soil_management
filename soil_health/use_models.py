import pickle
import numpy as np
import os

def load_models(models_dir='models'):
    """Load the trained models from the specified directory."""
    try:
        # Load the fertility model
        with open(os.path.join(models_dir, 'fertility_model.pkl'), 'rb') as f:
            fertility_model = pickle.load(f)
        
        # Load the quality model
        with open(os.path.join(models_dir, 'quality_model.pkl'), 'rb') as f:
            quality_model = pickle.load(f)
        
        # Load the scaler
        with open(os.path.join(models_dir, 'scaler.pkl'), 'rb') as f:
            scaler = pickle.load(f)
        
        # Load the label encoder
        with open(os.path.join(models_dir, 'label_encoder.pkl'), 'rb') as f:
            label_encoder = pickle.load(f)
        
        return fertility_model, quality_model, scaler, label_encoder
    except Exception as e:
        print(f"Error loading models: {e}")
        return None, None, None, None

def predict_soil_health(nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter, models_dir='models'):
    """Predict soil health parameters based on input soil data."""
    # Load models
    fertility_model, quality_model, scaler, label_encoder = load_models(models_dir)
    
    if fertility_model is None:
        print("Models could not be loaded. Please make sure the model files exist.")
        return None
    
    # Prepare input data
    input_data = np.array([[nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter]])
    
    # Scale the input data
    input_scaled = scaler.transform(input_data)
    
    # Predict fertility level
    fertility_pred = fertility_model.predict(input_scaled)[0]
    fertility_level = label_encoder.inverse_transform([fertility_pred])[0]
    
    # Predict quality score
    quality_score = quality_model.predict(input_scaled)[0]
    
    # Predict suitable crops
    suitable_crops = predict_suitable_crops(nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter)
    
    return {
        'fertility_level': fertility_level,
        'quality_score': round(quality_score, 1),
        'suitable_crops': suitable_crops
    }

def predict_suitable_crops(nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter):
    """Predict suitable crops based on soil parameters."""
    suitable_crops = []
    
    # Rice
    if 5.0 <= ph <= 7.5 and moisture > 60:
        suitable_crops.append('Rice')
    
    # Wheat
    if 6.0 <= ph <= 7.5 and nitrogen > 40:
        suitable_crops.append('Wheat')
    
    # Corn
    if 5.5 <= ph <= 7.5 and potassium > 50:
        suitable_crops.append('Corn')
    
    # Soybeans
    if 6.0 <= ph <= 7.0 and phosphorus > 40:
        suitable_crops.append('Soybeans')
    
    # Cotton
    if 5.5 <= ph <= 8.0 and ec < 3:
        suitable_crops.append('Cotton')
    
    # Tomatoes
    if 5.5 <= ph <= 7.5 and organic_matter > 3:
        suitable_crops.append('Tomatoes')
    
    # Potatoes
    if 4.8 <= ph <= 6.5 and moisture > 40:
        suitable_crops.append('Potatoes')
    
    # Carrots
    if 5.5 <= ph <= 7.0 and phosphorus > 30:
        suitable_crops.append('Carrots')
    
    # Lettuce
    if 6.0 <= ph <= 7.0 and nitrogen > 30:
        suitable_crops.append('Lettuce')
    
    # Spinach
    if 6.0 <= ph <= 7.5 and nitrogen > 50:
        suitable_crops.append('Spinach')
    
    return suitable_crops

if __name__ == "__main__":
    # Test with sample inputs
    test_cases = [
        # High fertility soil
        {'nitrogen': 80, 'phosphorus': 75, 'potassium': 85, 'ph': 6.5, 'ec': 1.2, 'moisture': 60, 'organic_matter': 7.5},
        # Medium fertility soil
        {'nitrogen': 45, 'phosphorus': 40, 'potassium': 50, 'ph': 7.0, 'ec': 2.0, 'moisture': 45, 'organic_matter': 4.0},
        # Low fertility soil
        {'nitrogen': 15, 'phosphorus': 10, 'potassium': 20, 'ph': 5.0, 'ec': 3.5, 'moisture': 30, 'organic_matter': 1.5}
    ]
    
    print("Testing soil health prediction with trained models:")
    for i, case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        print(f"Input: {case}")
        result = predict_soil_health(
            case['nitrogen'], case['phosphorus'], case['potassium'], 
            case['ph'], case['ec'], case['moisture'], case['organic_matter']
        )
        if result:
            print(f"Predicted Fertility Level: {result['fertility_level']}")
            print(f"Predicted Quality Score: {result['quality_score']}")
            print(f"Suitable Crops: {', '.join(result['suitable_crops'])}")
    
    print("\nTo use these models in your own application:")
    print("1. Download the soil_health_models.zip file")
    print("2. Extract the contents to a 'models' directory in your project")
    print("3. Import and use the functions from this script to make predictions")
