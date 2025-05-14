import os
import pickle
import numpy as np
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Load the model
MODEL_PATH = 'xgb_pipeline.pkl'
model = pickle.load(open(MODEL_PATH, 'rb'))

# Mapping dictionaries
soil_type_mapping = {0: 'Black', 1: 'Clayey', 2: 'Loamy', 3: 'Red', 4: 'Sandy'}
soil_type_reverse = {v: k for k, v in soil_type_mapping.items()}

crop_type_mapping = {0: 'Barley', 1: 'Cotton', 2: 'Ground Nuts', 3: 'Maize', 
                    4: 'Millets', 5: 'Oil seeds', 6: 'Paddy', 7: 'Pulses', 
                    8: 'Sugarcane', 9: 'Tobacco', 10: 'Wheat'}
crop_type_reverse = {v: k for k, v in crop_type_mapping.items()}

fertilizer_mapping = {0: '10-26-26', 1: '14-35-14', 2: '17-17-17', 3: '20-20', 
                     4: '28-28', 5: 'DAP', 6: 'Urea'}

@app.route('/')
def home():
    return render_template('index.html', 
                          soil_types=list(soil_type_mapping.values()),
                          crop_types=list(crop_type_mapping.values()))

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get form data
        n_content = float(request.form['n_content'])
        p_content = float(request.form['p_content'])
        k_content = float(request.form['k_content'])
        temperature = float(request.form['temperature'])
        humidity = float(request.form['humidity'])
        moisture = float(request.form['moisture'])
        soil_type = request.form['soil_type']
        crop_type = request.form['crop_type']
        
        # Convert soil and crop types to numerical values
        soil_type_num = soil_type_reverse[soil_type]
        crop_type_num = crop_type_reverse[crop_type]
        
        # Create input array for prediction
        input_data = np.array([[n_content, p_content, k_content, temperature, 
                               humidity, moisture, soil_type_num, crop_type_num]])
        
        # Make prediction
        prediction = model.predict(input_data)[0]
        fertilizer = fertilizer_mapping[prediction]
        
        return render_template('result.html', 
                              fertilizer=fertilizer,
                              n_content=n_content,
                              p_content=p_content,
                              k_content=k_content,
                              temperature=temperature,
                              humidity=humidity,
                              moisture=moisture,
                              soil_type=soil_type,
                              crop_type=crop_type)
    
    except Exception as e:
        return render_template('index.html', 
                              error=f"Error making prediction: {str(e)}",
                              soil_types=list(soil_type_mapping.values()),
                              crop_types=list(crop_type_mapping.values()))

if __name__ == '__main__':
    app.run(debug=True)
