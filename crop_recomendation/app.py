from flask import Flask, request, render_template, jsonify
import numpy as np
import joblib

app = Flask(__name__)

# Load the model
model = joblib.load('crop_recommender_rf.joblib')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get input values from form
        nitrogen = float(request.form['N'])
        phosphorus = float(request.form['P'])
        potassium = float(request.form['K'])
        temperature = float(request.form['temperature'])
        humidity = float(request.form['humidity'])
        ph = float(request.form['ph'])
        rainfall = float(request.form['rainfall'])

        # Create input array for prediction
        input_data = np.array([[nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall]])

        # Make prediction
        prediction = model.predict(input_data)[0]

        # Format prediction text
        prediction_text = f"The recommended crop for your soil and climate conditions is: {prediction.upper()}"

        return render_template('index.html', prediction_text=prediction_text, show_prediction=True)
    except Exception as e:
        return render_template('index.html', prediction_text=f"Error: {str(e)}", show_prediction=True)

@app.route('/api/predict', methods=['POST'])
def api_predict():
    try:
        # Get JSON data
        data = request.get_json()

        # Extract values
        nitrogen = float(data.get('N', data.get('nitrogen', 0)))
        phosphorus = float(data.get('P', data.get('phosphorus', 0)))
        potassium = float(data.get('K', data.get('potassium', 0)))
        temperature = float(data.get('temperature', 0))
        humidity = float(data.get('humidity', 0))
        ph = float(data.get('ph', 0))
        rainfall = float(data.get('rainfall', 0))

        # Create input array for prediction
        input_data = np.array([[nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall]])

        # Make prediction
        prediction = model.predict(input_data)[0]

        return jsonify({
            'status': 'success',
            'prediction': prediction,
            'input': {
                'N': nitrogen,
                'P': phosphorus,
                'K': potassium,
                'temperature': temperature,
                'humidity': humidity,
                'ph': ph,
                'rainfall': rainfall
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    print("Starting Flask app...")
    print("Model loaded successfully")
    print("Running on http://127.0.0.1:5000")
    app.run(debug=True)