import numpy as np
import pickle
import os

class SoilHealthModel:
    """
    A model for predicting soil health parameters:
    - Fertility level (High/Medium/Low)
    - Soil quality score (0-100)
    - Suitable crops
    """
    
    def __init__(self):
        """Initialize the model by loading the trained models."""
        model_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Check if models exist, if not, use dummy models
        if (os.path.exists(os.path.join(model_dir, 'fertility_model.pkl')) and
            os.path.exists(os.path.join(model_dir, 'quality_model.pkl')) and
            os.path.exists(os.path.join(model_dir, 'scaler.pkl')) and
            os.path.exists(os.path.join(model_dir, 'label_encoder.pkl'))):
            
            # Load the trained models
            with open(os.path.join(model_dir, 'fertility_model.pkl'), 'rb') as f:
                self.fertility_model = pickle.load(f)
            
            with open(os.path.join(model_dir, 'quality_model.pkl'), 'rb') as f:
                self.quality_model = pickle.load(f)
            
            with open(os.path.join(model_dir, 'scaler.pkl'), 'rb') as f:
                self.scaler = pickle.load(f)
            
            with open(os.path.join(model_dir, 'label_encoder.pkl'), 'rb') as f:
                self.label_encoder = pickle.load(f)
            
            self.using_dummy = False
        else:
            # Use dummy models
            print("Trained models not found. Using dummy prediction logic.")
            self.using_dummy = True
    
    def predict(self, nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter):
        """
        Predict soil health parameters based on input soil data.
        
        Args:
            nitrogen (float): Nitrogen content in ppm (0-100)
            phosphorus (float): Phosphorus content in ppm (0-100)
            potassium (float): Potassium content in ppm (0-100)
            ph (float): pH value (4.0-8.5)
            ec (float): Electrical Conductivity in dS/m (0-4)
            moisture (float): Moisture content in % (0-100)
            organic_matter (float): Organic Matter content in % (0-10)
            
        Returns:
            dict: A dictionary containing fertility level, quality score, and suitable crops
        """
        if self.using_dummy:
            return self._dummy_predict(nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter)
        
        # Prepare input data
        input_data = np.array([[nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter]])
        
        # Scale the input data
        input_scaled = self.scaler.transform(input_data)
        
        # Predict fertility level
        fertility_pred = self.fertility_model.predict(input_scaled)[0]
        fertility_level = self.label_encoder.inverse_transform([fertility_pred])[0]
        
        # Predict quality score
        quality_score = self.quality_model.predict(input_scaled)[0]
        
        # Predict suitable crops
        suitable_crops = self._predict_suitable_crops(nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter)
        
        return {
            'fertility_level': fertility_level,
            'quality_score': round(quality_score, 1),
            'suitable_crops': suitable_crops
        }
    
    def _dummy_predict(self, nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter):
        """
        Make dummy predictions when trained models are not available.
        This uses simplified rules based on domain knowledge.
        """
        # Calculate a simple quality score (0-100)
        # This is a simplified model - in reality, the relationship would be more complex
        
        # Normalize values to 0-1 range
        n_norm = nitrogen / 100
        p_norm = phosphorus / 100
        k_norm = potassium / 100
        
        # pH is optimal around 6.5 for most crops
        ph_score = 1 - 0.2 * abs(ph - 6.5)
        
        # EC is better when lower (less salt)
        ec_norm = max(0, 1 - (ec / 4))
        
        # Moisture is optimal around 50-60%
        moisture_norm = 1 - 0.02 * abs(moisture - 55)
        
        # Organic matter is better when higher
        om_norm = min(1, organic_matter / 8)
        
        # Calculate weighted quality score
        quality_score = (
            0.2 * n_norm + 
            0.2 * p_norm + 
            0.2 * k_norm + 
            0.15 * ph_score + 
            0.1 * ec_norm + 
            0.1 * moisture_norm + 
            0.05 * om_norm
        ) * 100
        
        # Determine fertility level based on quality score
        if quality_score >= 70:
            fertility_level = 'High'
        elif quality_score >= 40:
            fertility_level = 'Medium'
        else:
            fertility_level = 'Low'
        
        # Predict suitable crops
        suitable_crops = self._predict_suitable_crops(nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter)
        
        return {
            'fertility_level': fertility_level,
            'quality_score': round(quality_score, 1),
            'suitable_crops': suitable_crops
        }
    
    def _predict_suitable_crops(self, nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter):
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


# For testing
if __name__ == "__main__":
    model = SoilHealthModel()
    
    # Test with sample inputs
    test_cases = [
        # High fertility soil
        {'nitrogen': 80, 'phosphorus': 75, 'potassium': 85, 'ph': 6.5, 'ec': 1.2, 'moisture': 60, 'organic_matter': 7.5},
        # Medium fertility soil
        {'nitrogen': 45, 'phosphorus': 40, 'potassium': 50, 'ph': 7.0, 'ec': 2.0, 'moisture': 45, 'organic_matter': 4.0},
        # Low fertility soil
        {'nitrogen': 15, 'phosphorus': 10, 'potassium': 20, 'ph': 5.0, 'ec': 3.5, 'moisture': 30, 'organic_matter': 1.5}
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\nTest Case {i+1}:")
        print(f"Input: {case}")
        result = model.predict(
            case['nitrogen'], case['phosphorus'], case['potassium'], 
            case['ph'], case['ec'], case['moisture'], case['organic_matter']
        )
        print(f"Predicted Fertility Level: {result['fertility_level']}")
        print(f"Predicted Quality Score: {result['quality_score']}")
        print(f"Suitable Crops: {', '.join(result['suitable_crops'])}")
