from flask import Flask, render_template, request, jsonify
from models.soil_health_model import SoilHealthModel

app = Flask(__name__)
model = SoilHealthModel()

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    """Handle prediction requests."""
    try:
        # Get input data from the form
        nitrogen = float(request.form.get('nitrogen', 0))
        phosphorus = float(request.form.get('phosphorus', 0))
        potassium = float(request.form.get('potassium', 0))
        ph = float(request.form.get('ph', 0))
        ec = float(request.form.get('ec', 0))
        moisture = float(request.form.get('moisture', 0))
        organic_matter = float(request.form.get('organic_matter', 0))
        
        # Make prediction
        result = model.predict(nitrogen, phosphorus, potassium, ph, ec, moisture, organic_matter)
        
        # Return the result
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/about')
def about():
    """Render the about page."""
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
