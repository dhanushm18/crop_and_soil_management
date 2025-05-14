import os
import numpy as np
import joblib
import pickle
import onnxruntime as ort
from PIL import Image
from io import BytesIO
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import random
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# Load environment variables
load_dotenv()
# Print environment variables for debugging
print(f"Environment variables loaded. GEMINI_API_KEY exists: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agriculture.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Ensure static directory exists for plant disease images
os.makedirs('static/uploads', exist_ok=True)

# ===== Load Models =====

# Load crop recommendation model
try:
    crop_model = joblib.load('models/crop_recommender_rf.joblib')
    print("Crop recommendation model loaded successfully")
except Exception as e:
    print(f"Error loading crop recommendation model: {e}")
    crop_model = None

# Load fertilizer recommendation model
try:
    fertilizer_model = pickle.load(open('models/xgb_pipeline.pkl', 'rb'))
    print("Fertilizer recommendation model loaded successfully")
except Exception as e:
    print(f"Error loading fertilizer recommendation model: {e}")
    fertilizer_model = None

# Load plant disease detection model
try:
    # Use absolute path for the model file
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "plant_disease_optimized.onnx")
    ort_session = ort.InferenceSession(model_path)
    input_name = ort_session.get_inputs()[0].name
    print(f"Plant disease detection model loaded successfully from {model_path}")
except Exception as e:
    print(f"Error loading plant disease detection model: {e}")
    ort_session = None

# Configure the Gemini API for chatbot
try:
    # Use environment variable or fallback to the API key from the original project
    api_key = os.getenv("GEMINI_API_KEY")

    # Check if API key is available
    if not api_key:
        print("WARNING: GEMINI_API_KEY not found in environment variables. Using fallback key.")
        api_key = "AIzaSyApClWYweivPNmL4r2dT_6EwnmrZ1QzLqM"

    print(f"Using Gemini API key: {api_key[:5]}...{api_key[-5:]}")

    # Configure the Gemini API
    genai.configure(api_key=api_key)

    # Test the API key with a simple request
    try:
        # Use a simpler model for testing
        test_model = genai.GenerativeModel("gemini-1.5-flash")
        test_response = test_model.generate_content("Hello")
        print("API key test successful")
        print(f"Test response: {test_response.text}")
    except Exception as test_error:
        print(f"API key test failed: {test_error}")
        raise Exception(f"Invalid API key or API access error: {test_error}")

    # Set up the model with simpler configuration
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 1024,
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    # Use a simpler model that's less likely to have issues
    print("Initializing chatbot model with gemini-1.5-flash...")
    chatbot_model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",  # Use flash instead of pro for better reliability
        generation_config=generation_config,
        safety_settings=safety_settings
    )

    # Initialize a simple chat session without complex history
    print("Starting chat session...")
    chat = chatbot_model.start_chat(
        history=[
            {
                "role": "user",
                "parts": ["You are an agriculture expert chatbot."]
            },
            {
                "role": "model",
                "parts": ["I'm your agriculture expert assistant. How can I help you today?"]
            }
        ]
    )

    # Test the chat session
    print("Testing chat session...")
    test_chat_response = chat.send_message("Hello, can you help with farming?")
    print(f"Chat test successful. Response: {test_chat_response.text[:100]}...")

    print("Chatbot model initialized successfully")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error initializing chatbot model: {e}")
    chatbot_model = None
    chat = None

# ===== Database Models =====

class Farm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    size = db.Column(db.Float)  # in acres/hectares
    soil_records = db.relationship('SoilRecord', backref='farm', lazy=True)
    harvests = db.relationship('Harvest', backref='farm', lazy=True)

class SoilComponent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    unit = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)

    def __repr__(self):
        return f'<SoilComponent {self.name}>'

class SoilRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text)
    values = db.relationship('SoilValue', backref='soil_record', lazy=True, cascade="all, delete-orphan")

class SoilValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    soil_record_id = db.Column(db.Integer, db.ForeignKey('soil_record.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('soil_component.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    component = db.relationship('SoilComponent')

class Crop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    nitrogen_depletion = db.Column(db.Float)  # Amount of nitrogen depleted per hectare
    phosphorus_depletion = db.Column(db.Float)  # Amount of phosphorus depleted per hectare
    potassium_depletion = db.Column(db.Float)  # Amount of potassium depleted per hectare
    harvests = db.relationship('Harvest', backref='crop', lazy=True)

class Harvest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    crop_id = db.Column(db.Integer, db.ForeignKey('crop.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    area = db.Column(db.Float)  # Area harvested in hectares
    yield_amount = db.Column(db.Float)  # Yield in kg or tons
    notes = db.Column(db.Text)

# ===== Helper Functions =====

def create_initial_data():
    """Create initial sample data for the application with a comprehensive soil and harvest history"""

    # Create soil components if they don't exist
    if not SoilComponent.query.first():
        components = [
            {'name': 'Nitrogen (N)', 'unit': 'mg/kg', 'description': 'Essential for leaf growth and protein formation'},
            {'name': 'Phosphorus (P)', 'unit': 'mg/kg', 'description': 'Important for root development and energy transfer'},
            {'name': 'Potassium (K)', 'unit': 'mg/kg', 'description': 'Helps overall plant health and disease resistance'},
            {'name': 'pH', 'unit': 'pH', 'description': 'Soil acidity/alkalinity affecting nutrient availability'},
            {'name': 'Organic Matter', 'unit': '%', 'description': 'Decomposed plant/animal material improving soil structure'},
            {'name': 'Moisture', 'unit': '%', 'description': 'Water content in soil affecting nutrient uptake'}
        ]
        for comp in components:
            db.session.add(SoilComponent(**comp))
        db.session.commit()

    # Create crops if they don't exist
    if not Crop.query.first():
        crops = [
            {'name': 'Wheat', 'nitrogen_depletion': 120, 'phosphorus_depletion': 30, 'potassium_depletion': 30},
            {'name': 'Rice', 'nitrogen_depletion': 100, 'phosphorus_depletion': 25, 'potassium_depletion': 25},
            {'name': 'Corn', 'nitrogen_depletion': 150, 'phosphorus_depletion': 35, 'potassium_depletion': 40},
            {'name': 'Soybeans', 'nitrogen_depletion': 80, 'phosphorus_depletion': 20, 'potassium_depletion': 35},
            {'name': 'Cotton', 'nitrogen_depletion': 110, 'phosphorus_depletion': 40, 'potassium_depletion': 50}
        ]
        for crop in crops:
            db.session.add(Crop(**crop))
        db.session.commit()

    # Create a default farm if none exists
    farm = Farm.query.first()
    if not farm:
        farm = Farm(name="Green Valley Farm", location="Karnataka, India", size=120.5)
        db.session.add(farm)
        db.session.commit()
        farm_id = farm.id
    else:
        farm_id = farm.id

    # Clear existing data if requested
    SoilRecord.query.delete()
    Harvest.query.delete()
    db.session.commit()

    # Get component IDs
    nitrogen = SoilComponent.query.filter_by(name='Nitrogen (N)').first()
    phosphorus = SoilComponent.query.filter_by(name='Phosphorus (P)').first()
    potassium = SoilComponent.query.filter_by(name='Potassium (K)').first()
    ph = SoilComponent.query.filter_by(name='pH').first()
    organic_matter = SoilComponent.query.filter_by(name='Organic Matter').first()
    moisture = SoilComponent.query.filter_by(name='Moisture').first()

    # Get crop IDs
    wheat = Crop.query.filter_by(name='Wheat').first()
    rice = Crop.query.filter_by(name='Rice').first()
    corn = Crop.query.filter_by(name='Corn').first()

    # Create a comprehensive timeline of soil records and harvests
    # Starting with high nutrient levels
    soil_records_data = [
        # Initial soil test - January
        {
            'date': datetime(2023, 1, 15),
            'notes': "Initial soil test before planting season",
            'values': [
                {'component_id': nitrogen.id, 'value': 85.0},
                {'component_id': phosphorus.id, 'value': 42.0},
                {'component_id': potassium.id, 'value': 180.0},
                {'component_id': ph.id, 'value': 6.8},
                {'component_id': organic_matter.id, 'value': 4.2},
                {'component_id': moisture.id, 'value': 45.0}
            ]
        },

        # After wheat planting - February
        {
            'date': datetime(2023, 2, 20),
            'notes': "Post-planting soil test for wheat crop",
            'values': [
                {'component_id': nitrogen.id, 'value': 78.0},
                {'component_id': phosphorus.id, 'value': 38.0},
                {'component_id': potassium.id, 'value': 175.0},
                {'component_id': ph.id, 'value': 6.7},
                {'component_id': organic_matter.id, 'value': 4.1},
                {'component_id': moisture.id, 'value': 48.0}
            ]
        },

        # Mid-season wheat - April
        {
            'date': datetime(2023, 4, 10),
            'notes': "Mid-season soil test for wheat crop",
            'values': [
                {'component_id': nitrogen.id, 'value': 65.0},
                {'component_id': phosphorus.id, 'value': 32.0},
                {'component_id': potassium.id, 'value': 160.0},
                {'component_id': ph.id, 'value': 6.6},
                {'component_id': organic_matter.id, 'value': 4.0},
                {'component_id': moisture.id, 'value': 42.0}
            ]
        },

        # After wheat harvest - June
        {
            'date': datetime(2023, 6, 5),
            'notes': "Post-harvest soil test after wheat",
            'values': [
                {'component_id': nitrogen.id, 'value': 45.0},  # Significant depletion after harvest
                {'component_id': phosphorus.id, 'value': 25.0},
                {'component_id': potassium.id, 'value': 145.0},
                {'component_id': ph.id, 'value': 6.5},
                {'component_id': organic_matter.id, 'value': 3.8},
                {'component_id': moisture.id, 'value': 40.0}
            ]
        },

        # After fertilization - June
        {
            'date': datetime(2023, 6, 20),
            'notes': "Post-fertilization soil test before rice planting",
            'values': [
                {'component_id': nitrogen.id, 'value': 90.0},  # Increased after fertilization
                {'component_id': phosphorus.id, 'value': 45.0},
                {'component_id': potassium.id, 'value': 185.0},
                {'component_id': ph.id, 'value': 6.6},
                {'component_id': organic_matter.id, 'value': 4.0},
                {'component_id': moisture.id, 'value': 50.0}
            ]
        },

        # Mid-season rice - August
        {
            'date': datetime(2023, 8, 15),
            'notes': "Mid-season soil test for rice crop",
            'values': [
                {'component_id': nitrogen.id, 'value': 75.0},
                {'component_id': phosphorus.id, 'value': 38.0},
                {'component_id': potassium.id, 'value': 170.0},
                {'component_id': ph.id, 'value': 6.4},
                {'component_id': organic_matter.id, 'value': 3.9},
                {'component_id': moisture.id, 'value': 55.0}
            ]
        },

        # After rice harvest - October
        {
            'date': datetime(2023, 10, 10),
            'notes': "Post-harvest soil test after rice",
            'values': [
                {'component_id': nitrogen.id, 'value': 50.0},  # Depleted after rice harvest
                {'component_id': phosphorus.id, 'value': 28.0},
                {'component_id': potassium.id, 'value': 150.0},
                {'component_id': ph.id, 'value': 6.3},
                {'component_id': organic_matter.id, 'value': 3.7},
                {'component_id': moisture.id, 'value': 45.0}
            ]
        },

        # After fertilization - October
        {
            'date': datetime(2023, 10, 25),
            'notes': "Post-fertilization soil test before corn planting",
            'values': [
                {'component_id': nitrogen.id, 'value': 95.0},  # Increased after heavy fertilization for corn
                {'component_id': phosphorus.id, 'value': 48.0},
                {'component_id': potassium.id, 'value': 190.0},
                {'component_id': ph.id, 'value': 6.5},
                {'component_id': organic_matter.id, 'value': 4.1},
                {'component_id': moisture.id, 'value': 48.0}
            ]
        },

        # Mid-season corn - December
        {
            'date': datetime(2023, 12, 15),
            'notes': "Mid-season soil test for corn crop",
            'values': [
                {'component_id': nitrogen.id, 'value': 70.0},
                {'component_id': phosphorus.id, 'value': 40.0},
                {'component_id': potassium.id, 'value': 170.0},
                {'component_id': ph.id, 'value': 6.4},
                {'component_id': organic_matter.id, 'value': 4.0},
                {'component_id': moisture.id, 'value': 42.0}
            ]
        },

        # After corn harvest - February
        {
            'date': datetime(2024, 2, 10),
            'notes': "Post-harvest soil test after corn",
            'values': [
                {'component_id': nitrogen.id, 'value': 40.0},  # Significant depletion after corn harvest
                {'component_id': phosphorus.id, 'value': 25.0},
                {'component_id': potassium.id, 'value': 140.0},
                {'component_id': ph.id, 'value': 6.2},
                {'component_id': organic_matter.id, 'value': 3.6},
                {'component_id': moisture.id, 'value': 40.0}
            ]
        },

        # After fertilization - March
        {
            'date': datetime(2024, 3, 1),
            'notes': "Post-fertilization soil test for new season",
            'values': [
                {'component_id': nitrogen.id, 'value': 85.0},  # Replenished for new season
                {'component_id': phosphorus.id, 'value': 42.0},
                {'component_id': potassium.id, 'value': 180.0},
                {'component_id': ph.id, 'value': 6.5},
                {'component_id': organic_matter.id, 'value': 4.0},
                {'component_id': moisture.id, 'value': 45.0}
            ]
        },

        # Current soil test - April
        {
            'date': datetime(2024, 4, 15),
            'notes': "Current soil test",
            'values': [
                {'component_id': nitrogen.id, 'value': 80.0},
                {'component_id': phosphorus.id, 'value': 40.0},
                {'component_id': potassium.id, 'value': 175.0},
                {'component_id': ph.id, 'value': 6.6},
                {'component_id': organic_matter.id, 'value': 4.1},
                {'component_id': moisture.id, 'value': 47.0}
            ]
        }
    ]

    # Create soil records
    for record_data in soil_records_data:
        record = SoilRecord(
            farm_id=farm_id,
            date=record_data['date'],
            notes=record_data['notes']
        )
        db.session.add(record)
        db.session.flush()  # Get the record ID

        for value_data in record_data['values']:
            value = SoilValue(
                soil_record_id=record.id,
                component_id=value_data['component_id'],
                value=value_data['value']
            )
            db.session.add(value)

    db.session.commit()

    # Create harvest records
    harvests_data = [
        {
            'crop': wheat,
            'date': datetime(2023, 5, 30),
            'area': 40.0,
            'yield_amount': 6000.0,
            'notes': "Wheat harvest - Good yield despite slightly dry conditions"
        },
        {
            'crop': rice,
            'date': datetime(2023, 10, 5),
            'area': 35.0,
            'yield_amount': 7500.0,
            'notes': "Rice harvest - Excellent yield with good rainfall"
        },
        {
            'crop': corn,
            'date': datetime(2024, 2, 5),
            'area': 45.0,
            'yield_amount': 9000.0,
            'notes': "Corn harvest - High yield with intensive fertilization"
        }
    ]

    for harvest_data in harvests_data:
        harvest = Harvest(
            farm_id=farm_id,
            crop_id=harvest_data['crop'].id,
            date=harvest_data['date'],
            area=harvest_data['area'],
            yield_amount=harvest_data['yield_amount'],
            notes=harvest_data['notes']
        )
        db.session.add(harvest)

    db.session.commit()

    print(f"Created sample data with {len(soil_records_data)} soil records and {len(harvests_data)} harvests")

def generate_components_line_chart(soil_records):
    """
    Generate an advanced visualization of soil components over time with harvest impact.
    This function creates a multi-panel chart showing:
    1. Main panel: Nutrient levels over time with harvest events
    2. Depletion panel: Calculated nutrient depletion after each harvest
    3. Nutrient balance panel: Relative balance of N, P, K over time
    """
    if not soil_records or len(soil_records) < 2:
        return None

    try:
        # Get the farm ID from the first soil record
        farm_id = soil_records[0].farm_id

        # Get all harvests for this farm, ordered by date
        harvests = Harvest.query.filter_by(farm_id=farm_id).order_by(Harvest.date.asc()).all()

        # Extract dates and component values from soil records
        soil_dates = [record.date for record in soil_records]

        # Get all components
        components = SoilComponent.query.all()
        component_data = {}
        component_ids = {}  # To store component IDs for later use

        # Extract values for each component
        for component in components:
            values = []
            for record in soil_records:
                value_obj = next((v for v in record.values if v.component_id == component.id), None)
                if value_obj:
                    values.append(value_obj.value)
                else:
                    values.append(None)

            # Only include components that have at least one value
            if any(v is not None for v in values):
                component_data[component.name] = values
                component_ids[component.name] = component.id

        if not component_data:
            return None

        # Filter to only include N, P, K for the main visualization
        npk_components = ['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)']
        npk_data = {k: v for k, v in component_data.items() if k in npk_components}

        if not npk_data:
            # If no NPK data, use whatever components we have
            npk_data = component_data

        # Create a figure with multiple subplots
        fig = plt.figure(figsize=(14, 10))

        # Define a custom color palette
        colors = {
            'Nitrogen (N)': '#3498db',  # Blue
            'Phosphorus (P)': '#e74c3c',  # Red
            'Potassium (K)': '#2ecc71',  # Green
            'pH': '#9b59b6',  # Purple
            'Organic Matter': '#f39c12',  # Orange
            'Moisture': '#1abc9c'  # Teal
        }

        # Default colors for any other components
        default_colors = ['#34495e', '#7f8c8d', '#95a5a6', '#bdc3c7']

        # Create the main plot (nutrient levels over time)
        ax1 = plt.subplot2grid((3, 1), (0, 0), rowspan=2)

        # Plot soil component values with custom styling
        for i, (component_name, values) in enumerate(npk_data.items()):
            # Filter out None values for plotting
            valid_indices = [i for i, v in enumerate(values) if v is not None]
            valid_dates = [soil_dates[i] for i in valid_indices]
            valid_values = [values[i] for i in valid_indices]

            if valid_dates and valid_values:
                color = colors.get(component_name, default_colors[i % len(default_colors)])
                ax1.plot(valid_dates, valid_values, marker='o', linestyle='-',
                         label=component_name, linewidth=3, color=color,
                         markerfacecolor='white', markeredgewidth=2, markersize=8)

        # Set y-axis limits with some padding
        y_min, y_max = ax1.get_ylim()
        ax1.set_ylim(max(0, y_min * 0.9), y_max * 1.1)

        # Process harvests and calculate depletion
        harvest_depletions = []

        if harvests:
            for harvest in harvests:
                crop = Crop.query.get(harvest.crop_id)
                if crop and soil_dates[0] <= harvest.date <= soil_dates[-1]:
                    # Add a vertical span to highlight harvest period
                    ax1.axvspan(harvest.date - datetime.timedelta(days=2),
                               harvest.date + datetime.timedelta(days=2),
                               alpha=0.2, color='#e74c3c', zorder=0)

                    # Add harvest marker
                    ax1.scatter([harvest.date], [y_max * 0.95], marker='▼', s=120,
                               color='#e74c3c', zorder=10, label=f'{crop.name} Harvest' if len(harvest_depletions) == 0 else "")

                    # Add annotation for the harvest
                    ax1.annotate(f'{crop.name}',
                                xy=(harvest.date, y_max * 0.95),
                                xytext=(harvest.date, y_max * 0.85),
                                ha='center', va='top',
                                fontsize=10, fontweight='bold',
                                bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#e74c3c', alpha=0.9))

                    # Calculate nutrient depletion
                    if harvest.area:
                        # Find the nearest soil record before the harvest
                        prev_record = None
                        for record in soil_records:
                            if record.date < harvest.date:
                                prev_record = record

                        # Find the nearest soil record after the harvest
                        next_record = None
                        for record in reversed(soil_records):
                            if record.date > harvest.date:
                                next_record = record

                        # If we have both records, calculate the depletion
                        if prev_record and next_record:
                            depletion_data = {
                                'date': harvest.date,
                                'crop': crop.name,
                                'area': harvest.area,
                                'nutrients': {}
                            }

                            # For each nutrient (N, P, K), calculate the depletion
                            for nutrient, depletion_attr in [
                                ('Nitrogen (N)', 'nitrogen_depletion'),
                                ('Phosphorus (P)', 'phosphorus_depletion'),
                                ('Potassium (K)', 'potassium_depletion')
                            ]:
                                if nutrient in component_data:
                                    # Get the component ID
                                    component_id = component_ids.get(nutrient)
                                    if component_id:
                                        # Get values before and after harvest
                                        prev_value = next((v.value for v in prev_record.values if v.component_id == component_id), None)
                                        next_value = next((v.value for v in next_record.values if v.component_id == component_id), None)

                                        if prev_value is not None and next_value is not None:
                                            # Calculate expected depletion based on crop and area
                                            expected_depletion = getattr(crop, depletion_attr, 0) * harvest.area / 100
                                            actual_depletion = prev_value - next_value

                                            depletion_data['nutrients'][nutrient] = {
                                                'expected': expected_depletion,
                                                'actual': actual_depletion,
                                                'prev_value': prev_value,
                                                'next_value': next_value,
                                                'color': colors.get(nutrient)
                                            }

                                            # Add a visual indicator of the depletion on the main chart
                                            color = colors.get(nutrient)
                                            ax1.plot([prev_record.date, next_record.date],
                                                    [prev_value, next_value],
                                                    'o--', color=color, alpha=0.7, linewidth=2)

                                            # Add arrow showing the depletion
                                            mid_point = prev_record.date + (next_record.date - prev_record.date) / 2
                                            ax1.annotate('',
                                                        xy=(mid_point, next_value),
                                                        xytext=(mid_point, prev_value),
                                                        arrowprops=dict(arrowstyle='<->', color=color, lw=2, alpha=0.7))

                            harvest_depletions.append(depletion_data)

        # Customize the main plot
        ax1.set_title('Soil Nutrient Levels Over Time', fontsize=16, fontweight='bold', pad=15)
        ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Nutrient Level (mg/kg)', fontsize=12, fontweight='bold')
        ax1.grid(True, linestyle='--', alpha=0.7)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        # Format x-axis to show dates nicely
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %d, %Y'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')

        # Add legend with custom styling
        legend = ax1.legend(loc='upper left', fontsize=10, frameon=True,
                           facecolor='white', edgecolor='#dddddd')

        # Create the depletion visualization (bottom panel)
        ax2 = plt.subplot2grid((3, 1), (2, 0), rowspan=1)

        if harvest_depletions:
            # Set up bar positions
            bar_width = 0.25
            index = np.arange(len(harvest_depletions))

            # Plot bars for each nutrient depletion
            for i, nutrient in enumerate(['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)']):
                expected_values = []
                actual_values = []

                for depletion in harvest_depletions:
                    if nutrient in depletion['nutrients']:
                        expected_values.append(depletion['nutrients'][nutrient]['expected'])
                        actual_values.append(depletion['nutrients'][nutrient]['actual'])
                    else:
                        expected_values.append(0)
                        actual_values.append(0)

                # Plot expected depletion (solid bars)
                color = colors.get(nutrient)
                ax2.bar(index + i*bar_width, expected_values, bar_width,
                       label=f'{nutrient} (Expected)', color=color, alpha=0.7)

                # Plot actual depletion (hatched bars)
                ax2.bar(index + i*bar_width, actual_values, bar_width,
                       label=f'{nutrient} (Actual)', color=color, alpha=0.4,
                       hatch='///', edgecolor=color)

            # Set x-ticks to show harvest dates and crops
            ax2.set_xticks(index + bar_width)
            ax2.set_xticklabels([f"{d['crop']}\n{d['date'].strftime('%b %d')}" for d in harvest_depletions])

            # Customize the depletion plot
            ax2.set_title('Nutrient Depletion After Harvests', fontsize=14, fontweight='bold', pad=15)
            ax2.set_ylabel('Depletion (mg/kg)', fontsize=12, fontweight='bold')
            ax2.grid(True, axis='y', linestyle='--', alpha=0.7)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)

            # Add legend with custom styling
            legend2 = ax2.legend(loc='upper right', fontsize=9, frameon=True,
                               facecolor='white', edgecolor='#dddddd', ncol=3)
        else:
            # If no harvest data, show a message
            ax2.text(0.5, 0.5, 'No harvest data available to calculate nutrient depletion',
                    ha='center', va='center', fontsize=12,
                    bbox=dict(boxstyle='round,pad=0.5', fc='#f8f9fa', ec='#dddddd'))
            ax2.set_xticks([])
            ax2.set_yticks([])
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['bottom'].set_visible(False)
            ax2.spines['left'].set_visible(False)

        # Add a subtle background color to the entire figure
        fig.patch.set_facecolor('#f8f9fa')

        # Add a title for the entire figure
        fig.suptitle('Soil Health Visualization with Harvest Impact Analysis',
                    fontsize=18, fontweight='bold', y=0.98)

        # Add explanatory text at the bottom
        if harvest_depletions:
            fig.text(0.5, 0.01,
                    'This visualization shows how nutrient levels change over time and the impact of harvests.\n'
                    'The top panel shows nutrient levels with harvest events marked by red triangles.\n'
                    'The bottom panel compares expected vs. actual nutrient depletion after each harvest.',
                    ha='center', va='bottom', fontsize=10, style='italic')

        plt.tight_layout()
        plt.subplots_adjust(top=0.92, bottom=0.1, hspace=0.3)

        # Save plot to a BytesIO object
        buf = BytesIO()
        plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
        buf.seek(0)

        # Convert to base64 for embedding in HTML
        img_data = base64.b64encode(buf.getbuffer()).decode('ascii')
        plt.close()

        return img_data

    except Exception as e:
        print(f"Error generating chart: {e}")
        import traceback
        traceback.print_exc()
        plt.close()  # Make sure to close any open figures
        return None

def preprocess_image(image_path, target_size=(224, 224)):
    """Simplified preprocessing for plant disease detection"""
    img = Image.open(image_path).convert('RGB').resize(target_size)
    return np.expand_dims(np.array(img)/255.0, axis=0).astype(np.float32)

# Function to predict crop yield based on conditions
def predict_yield(crop_name, soil_type, water_level, fertilizer_level, season):
    """
    Predict crop yield based on growing conditions.
    This is a simplified model for demonstration purposes.
    In a real application, this would use a trained ML model.
    """
    # Base yields from our crop data
    base_yields = {
        'rice': 2500,
        'wheat': 1800,
        'maize': 3000,
        'cotton': 1200,
        'sugarcane': 40000,
        'potato': 15000,
        'tomato': 20000,
        'soybean': 1500
    }

    # Get base yield for the crop (case-insensitive)
    crop_key = crop_name.lower()
    base_yield = base_yields.get(crop_key, 2000)  # Default to 2000 if crop not found

    # Apply modifiers based on conditions
    # Soil type modifier
    soil_modifiers = {
        'clay': {'rice': 1.1, 'wheat': 0.9, 'maize': 0.95, 'cotton': 0.9, 'sugarcane': 1.05, 'potato': 0.8, 'tomato': 0.85, 'soybean': 0.9},
        'loamy': {'rice': 1.0, 'wheat': 1.1, 'maize': 1.1, 'cotton': 1.05, 'sugarcane': 1.0, 'potato': 1.1, 'tomato': 1.1, 'soybean': 1.05},
        'sandy': {'rice': 0.8, 'wheat': 0.85, 'maize': 0.9, 'cotton': 0.95, 'sugarcane': 0.85, 'potato': 0.9, 'tomato': 0.9, 'soybean': 0.95},
        'black': {'rice': 0.95, 'wheat': 1.05, 'maize': 1.0, 'cotton': 1.15, 'sugarcane': 1.0, 'potato': 1.0, 'tomato': 1.0, 'soybean': 1.1},
        'red': {'rice': 0.9, 'wheat': 0.95, 'maize': 0.95, 'cotton': 1.0, 'sugarcane': 0.9, 'potato': 0.95, 'tomato': 0.95, 'soybean': 1.0},
        'sandy loam': {'rice': 0.85, 'wheat': 1.0, 'maize': 1.05, 'cotton': 1.0, 'sugarcane': 0.9, 'potato': 1.05, 'tomato': 1.0, 'soybean': 1.0}
    }

    # Water level modifier
    water_modifiers = {
        'low': {'rice': 0.7, 'wheat': 0.8, 'maize': 0.85, 'cotton': 0.9, 'sugarcane': 0.7, 'potato': 0.8, 'tomato': 0.75, 'soybean': 0.9},
        'medium': {'rice': 0.9, 'wheat': 1.0, 'maize': 1.0, 'cotton': 1.0, 'sugarcane': 0.9, 'potato': 1.0, 'tomato': 1.0, 'soybean': 1.0},
        'high': {'rice': 1.2, 'wheat': 1.05, 'maize': 1.1, 'cotton': 1.05, 'sugarcane': 1.2, 'potato': 1.1, 'tomato': 1.15, 'soybean': 1.05}
    }

    # Fertilizer level modifier
    fertilizer_modifiers = {
        'low': {'rice': 0.8, 'wheat': 0.85, 'maize': 0.85, 'cotton': 0.9, 'sugarcane': 0.8, 'potato': 0.8, 'tomato': 0.8, 'soybean': 0.9},
        'medium': {'rice': 1.0, 'wheat': 1.0, 'maize': 1.0, 'cotton': 1.0, 'sugarcane': 1.0, 'potato': 1.0, 'tomato': 1.0, 'soybean': 1.0},
        'high': {'rice': 1.25, 'wheat': 1.2, 'maize': 1.2, 'cotton': 1.15, 'sugarcane': 1.25, 'potato': 1.25, 'tomato': 1.3, 'soybean': 1.15}
    }

    # Season modifier
    season_modifiers = {
        'kharif': {'rice': 1.1, 'wheat': 0.8, 'maize': 1.1, 'cotton': 1.1, 'sugarcane': 1.0, 'potato': 0.9, 'tomato': 1.0, 'soybean': 1.1},
        'rabi': {'rice': 0.9, 'wheat': 1.2, 'maize': 0.95, 'cotton': 0.8, 'sugarcane': 1.0, 'potato': 1.1, 'tomato': 1.0, 'soybean': 0.9},
        'zaid': {'rice': 1.0, 'wheat': 0.9, 'maize': 1.0, 'cotton': 0.9, 'sugarcane': 1.0, 'potato': 1.0, 'tomato': 1.05, 'soybean': 1.0},
        'year-round': {'rice': 1.0, 'wheat': 1.0, 'maize': 1.0, 'cotton': 1.0, 'sugarcane': 1.1, 'potato': 1.0, 'tomato': 1.1, 'soybean': 1.0}
    }

    # Apply modifiers
    soil_modifier = soil_modifiers.get(soil_type.lower(), {}).get(crop_key, 1.0)
    water_modifier = water_modifiers.get(water_level.lower(), {}).get(crop_key, 1.0)
    fertilizer_modifier = fertilizer_modifiers.get(fertilizer_level.lower(), {}).get(crop_key, 1.0)
    season_modifier = season_modifiers.get(season.lower(), {}).get(crop_key, 1.0)

    # Calculate predicted yield
    predicted_yield = base_yield * soil_modifier * water_modifier * fertilizer_modifier * season_modifier

    # Add some randomness to make it more realistic (±5%)
    import random
    randomness = random.uniform(0.95, 1.05)
    predicted_yield *= randomness

    # Round to nearest whole number
    return round(predicted_yield)

# ===== Routes =====

@app.route('/')
def index():
    return render_template('index.html')

# ----- Crop Recommendation Routes -----

@app.route('/crop-recommendation')
def crop_recommendation():
    return render_template('crop_recommendation.html')

@app.route('/crop-recommendation/predict', methods=['POST'])
def crop_predict():
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
        prediction = crop_model.predict(input_data)[0]

        # Format prediction text
        prediction_text = f"The recommended crop for your soil and climate conditions is: {prediction.upper()}"

        return render_template('crop_recommendation.html', prediction=prediction_text, input_data={
            'N': nitrogen,
            'P': phosphorus,
            'K': potassium,
            'temperature': temperature,
            'humidity': humidity,
            'ph': ph,
            'rainfall': rainfall
        })
    except Exception as e:
        return render_template('crop_recommendation.html', error=f"Error making prediction: {str(e)}")

@app.route('/api/crop-recommendation/predict', methods=['POST'])
def api_crop_predict():
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
        prediction = crop_model.predict(input_data)[0]

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

# ----- Fertilizer Recommendation Routes -----

@app.route('/fertilizer-recommendation')
def fertilizer_recommendation():
    # Mapping dictionaries
    soil_type_mapping = {0: 'Black', 1: 'Clayey', 2: 'Loamy', 3: 'Red', 4: 'Sandy'}
    crop_type_mapping = {0: 'Barley', 1: 'Cotton', 2: 'Ground Nuts', 3: 'Maize',
                        4: 'Millets', 5: 'Oil seeds', 6: 'Paddy', 7: 'Pulses',
                        8: 'Sugarcane', 9: 'Tobacco', 10: 'Wheat'}

    return render_template('fertilizer_recommendation.html',
                          soil_types=list(soil_type_mapping.values()),
                          crop_types=list(crop_type_mapping.values()))

@app.route('/fertilizer-recommendation/predict', methods=['POST'])
def fertilizer_predict():
    # Mapping dictionaries
    soil_type_mapping = {0: 'Black', 1: 'Clayey', 2: 'Loamy', 3: 'Red', 4: 'Sandy'}
    soil_type_reverse = {v: k for k, v in soil_type_mapping.items()}

    crop_type_mapping = {0: 'Barley', 1: 'Cotton', 2: 'Ground Nuts', 3: 'Maize',
                        4: 'Millets', 5: 'Oil seeds', 6: 'Paddy', 7: 'Pulses',
                        8: 'Sugarcane', 9: 'Tobacco', 10: 'Wheat'}
    crop_type_reverse = {v: k for k, v in crop_type_mapping.items()}

    fertilizer_mapping = {0: '10-26-26', 1: '14-35-14', 2: '17-17-17', 3: '20-20',
                         4: '28-28', 5: 'DAP', 6: 'Urea'}

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
        prediction = fertilizer_model.predict(input_data)[0]
        fertilizer = fertilizer_mapping[prediction]

        return render_template('fertilizer_result.html',
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
        return render_template('fertilizer_recommendation.html',
                              error=f"Error making prediction: {str(e)}",
                              soil_types=list(soil_type_mapping.values()),
                              crop_types=list(crop_type_mapping.values()))

# ----- Plant Disease Detection Routes -----

@app.route('/plant-disease')
def plant_disease():
    return render_template('plant_disease.html')

@app.route('/plant-disease/predict', methods=['POST'])
def plant_disease_predict():
    """
    Process plant disease detection from uploaded image using the ONNX model.
    """
    # Complete disease database with all classes from the model
    disease_db = {
        "Apple___Apple_scab": {
            "solution": "Apply fungicides containing myclobutanil or sulfur. Begin applications at bud break and continue at 7-10 day intervals during wet spring weather.",
            "tips": [
                "Prune infected branches during dormant season",
                "Remove and destroy fallen leaves to reduce fungal spores",
                "Plant resistant apple varieties like Liberty, Enterprise, or Williams Pride",
                "Ensure good air circulation by proper tree spacing and pruning",
                "Apply protective fungicides before rain events"
            ]
        },
        "Apple___Black_rot": {
            "solution": "Apply fungicides containing captan or thiophanate-methyl. Prune out infected branches and remove mummified fruits.",
            "tips": [
                "Remove all mummified fruits from the tree and ground",
                "Prune out cankers and dead wood during dormant season",
                "Maintain good sanitation in the orchard",
                "Apply fungicides during the growing season",
                "Ensure proper spacing for air circulation"
            ]
        },
        "Apple___Cedar_apple_rust": {
            "solution": "Apply fungicides containing mancozeb or myclobutanil. Remove nearby cedar trees if possible.",
            "tips": [
                "Remove nearby juniper or cedar trees (alternate hosts)",
                "Apply protective fungicides in spring before infection",
                "Plant resistant apple varieties",
                "Maintain good air circulation",
                "Remove infected leaves and fruit"
            ]
        },
        "Apple___healthy": {
            "solution": "Continue good orchard management practices to maintain tree health.",
            "tips": [
                "Maintain regular pruning schedule",
                "Apply balanced fertilization based on soil tests",
                "Monitor for early signs of pests or disease",
                "Ensure adequate irrigation during dry periods",
                "Practice good sanitation in the orchard"
            ]
        },
        "Tomato___Late_blight": {
            "solution": "Apply copper-based fungicides or approved fungicides containing chlorothalonil, mancozeb, or maneb. Begin applications before disease appears when conditions favor disease development.",
            "tips": [
                "Water at the base of plants to keep foliage dry",
                "Improve air circulation by proper plant spacing and staking",
                "Remove and destroy infected plants immediately",
                "Rotate crops - don't plant tomatoes or potatoes in the same location for 3-4 years",
                "Use resistant varieties when available",
                "Mulch around plants to prevent soil splash onto leaves"
            ]
        },
        "Tomato___Early_blight": {
            "solution": "Apply fungicides containing chlorothalonil, mancozeb, or copper. Remove and destroy infected leaves.",
            "tips": [
                "Remove lower infected leaves promptly",
                "Mulch around plants to prevent soil splash",
                "Provide adequate spacing for air circulation",
                "Rotate crops - avoid planting tomatoes in the same location for 3 years",
                "Water at the base of plants to keep foliage dry"
            ]
        },
        "Tomato___healthy": {
            "solution": "Continue good gardening practices to maintain plant health.",
            "tips": [
                "Maintain consistent watering schedule",
                "Provide support for growing plants",
                "Apply balanced fertilizer according to soil test results",
                "Monitor regularly for early signs of pests or disease",
                "Maintain proper spacing for good air circulation"
            ]
        }
    }

    # Check if file was uploaded
    if 'file' not in request.files:
        return render_template("plant_disease.html", error="No file was uploaded. Please select an image file.")

    file = request.files['file']

    # Check if filename is empty
    if file.filename == '':
        return render_template("plant_disease.html", error="No file was selected. Please choose an image file.")

    # Check if the file is an allowed image type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return render_template("plant_disease.html", error="Invalid file type. Please upload a PNG, JPG, JPEG, or GIF image.")

    try:
        # Create a secure filename with UUID to prevent conflicts
        import uuid
        file_extension = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{str(uuid.uuid4())}{file_extension}"

        # Ensure the uploads directory exists
        upload_dir = os.path.join('static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # Full path to save the file
        filepath = os.path.join(upload_dir, unique_filename)

        # Save the file
        file.save(filepath)
        print(f"Successfully saved image to {filepath}")

        # Verify the file was saved correctly
        if not os.path.exists(filepath):
            raise Exception("Failed to save the uploaded file")

        # Define the disease classes mapping
        disease_classes = {
            0: 'Apple___Apple_scab', 1: 'Apple___Black_rot', 2: 'Apple___Cedar_apple_rust',
            3: 'Apple___healthy', 4: 'Blueberry___healthy',
            5: 'Cherry_(including_sour)___Powdery_mildew', 6: 'Cherry_(including_sour)___healthy',
            7: 'Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot', 8: 'Corn_(maize)___Common_rust_',
            9: 'Corn_(maize)___Northern_Leaf_Blight', 10: 'Corn_(maize)___healthy',
            11: 'Grape___Black_rot', 12: 'Grape___Esca_(Black_Measles)',
            13: 'Grape___Leaf_blight_(Isariopsis_Leaf_Spot)', 14: 'Grape___healthy',
            15: 'Orange___Haunglongbing_(Citrus_greening)', 16: 'Peach___Bacterial_spot',
            17: 'Peach___healthy', 18: 'Pepper,_bell___Bacterial_spot', 19: 'Pepper,_bell___healthy',
            20: 'Potato___Early_blight', 21: 'Potato___Late_blight', 22: 'Potato___healthy',
            23: 'Raspberry___healthy', 24: 'Soybean___healthy', 25: 'Squash___Powdery_mildew',
            26: 'Strawberry___Leaf_scorch', 27: 'Strawberry___healthy', 28: 'Tomato___Bacterial_spot',
            29: 'Tomato___Early_blight', 30: 'Tomato___Late_blight', 31: 'Tomato___Leaf_Mold',
            32: 'Tomato___Septoria_leaf_spot', 33: 'Tomato___Spider_mites Two-spotted_spider_mite',
            34: 'Tomato___Target_Spot', 35: 'Tomato___Tomato_Yellow_Leaf_Curl_Virus',
            36: 'Tomato___Tomato_mosaic_virus', 37: 'Tomato___healthy'
        }

        # Check if the ONNX model is loaded
        if ort_session is None:
            raise Exception("Plant disease detection model is not available")

        # Process the image for prediction
        from PIL import Image
        import numpy as np

        # Load and preprocess the image
        img = Image.open(filepath)
        img = img.resize((224, 224))  # Resize to model input size
        img_array = np.array(img).astype(np.float32)

        # Normalize the image (0-255 to 0-1)
        img_array = img_array / 255.0

        # Add batch dimension and ensure correct channel order (RGB)
        img_array = np.expand_dims(img_array, axis=0)

        # Make prediction using the ONNX model
        outputs = ort_session.run(None, {input_name: img_array})

        # Get the predicted class
        prediction = outputs[0]
        class_idx = np.argmax(prediction[0])
        confidence = prediction[0][class_idx]

        # Get the disease name
        disease_name = disease_classes[class_idx]

        print(f"Predicted disease: {disease_name} with confidence {confidence*100:.1f}%")

        # Get advice for the predicted disease
        advice = disease_db.get(disease_name, {
            "solution": "Consult a local agricultural expert for proper diagnosis and treatment recommendations.",
            "tips": [
                "Isolate the affected plant to prevent potential spread",
                "Check soil conditions and adjust if necessary",
                "Monitor other plants for similar symptoms",
                "Take multiple clear photos of symptoms for expert consultation"
            ]
        })

        # Use the URL path that will work in the template
        image_url = f"/static/uploads/{unique_filename}"

        # Return the results
        return render_template(
            "plant_disease.html",
            prediction=disease_name.replace("___", " - "),  # Format the disease name for display
            confidence=f"{confidence*100:.1f}%",
            image_path=image_url,
            solution=advice["solution"],
            tips=advice["tips"],
            is_healthy="healthy" in disease_name.lower()
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in plant disease prediction: {str(e)}")

        # Provide a user-friendly error message
        error_message = "An error occurred while processing your image. Please try again with a different image."
        if "image file is truncated" in str(e).lower():
            error_message = "The uploaded image appears to be corrupted. Please try a different image."
        elif "cannot identify image file" in str(e).lower():
            error_message = "The file could not be processed as an image. Please upload a valid image file."

        return render_template("plant_disease.html", error=error_message)

# ----- Chatbot Routes -----

@app.route('/chatbot')
def chatbot():
    """
    Render the chatbot page with client-side implementation.
    This is a standalone implementation that doesn't rely on external APIs.
    """
    return render_template('chatbot.html')

@app.route('/chatbot/ask', methods=['POST'])
def chatbot_ask():
    """
    API endpoint to handle chatbot requests.
    """
    global chat, chatbot_model  # Use global to access the chat and model variables

    try:
        # Get message from request
        user_message = request.json.get('message', '')
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Check if chat is initialized
        if chat is None:
            # Try to initialize the chat if it's None
            try:
                print("Chat is None, trying to initialize it...")

                # Set up the model with simpler configuration
                generation_config = {
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }

                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]

                # Create a new model instance
                chatbot_model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )

                # Create a new chat session
                chat = chatbot_model.start_chat(history=[])
                print("Chat initialized successfully")
            except Exception as init_error:
                error_message = 'Sorry, the chatbot service is currently unavailable. The Gemini API may not be properly configured.'
                print(f"Failed to initialize chat: {str(init_error)}")
                return jsonify({
                    'response': error_message,
                    'error_details': str(init_error),
                    'debug': True
                }), 500

        # Send the user's message to the Gemini model
        try:
            # Debug information
            print(f"Sending message to Gemini API: '{user_message[:50]}...' (truncated)")

            # Send the message
            response = chat.send_message(user_message)
            print(f"Received response from Gemini API: '{response.text[:50]}...' (truncated)")

            return jsonify({'response': response.text})
        except Exception as chat_error:
            error_details = str(chat_error)
            print(f"Gemini API error: {error_details}")
            traceback.print_exc()

            # Try to recreate the chat session if there was an error
            try:
                print("Trying to recreate chat session after error...")
                chat = chatbot_model.start_chat(history=[])
                print("Chat session recreated")

                # Try again with the new session
                response = chat.send_message(user_message)
                print(f"Second attempt successful: '{response.text[:50]}...' (truncated)")
                return jsonify({'response': response.text})
            except Exception as retry_error:
                print(f"Failed to recreate chat session: {str(retry_error)}")

                # Check for common API errors
                if "API key not valid" in error_details or "invalid API key" in error_details.lower():
                    error_message = "Sorry, there's an issue with the API key configuration. Please check your Gemini API key."
                elif "quota exceeded" in error_details.lower() or "rate limit" in error_details.lower():
                    error_message = "Sorry, the API quota has been exceeded. Please try again later."
                elif "blocked" in error_details.lower() or "safety" in error_details.lower():
                    error_message = "Sorry, your request was blocked by safety filters. Please try a different question."
                else:
                    error_message = f"Sorry, I encountered an error: {error_details}"

                # Return the actual error for debugging
                return jsonify({
                    'response': error_message,
                    'error_details': error_details,
                    'debug': True
                }), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in chatbot API: {str(e)}")
        return jsonify({
            'response': f"Sorry, I encountered an error: {str(e)}",
            'error_details': str(e),
            'debug': True
        }), 500

# Dashboard functionality has been removed
# All dashboard routes and functionality have been removed from the application

# ----- Weather-Aware Farming Routes -----

@app.route('/weather-aware')
def weather_aware():
    """Route for weather-aware farming recommendations"""
    return render_template('weather_aware.html')

# ----- Soil Health Analysis Routes -----

@app.route('/soil-health')
def soil_health():
    """Route for soil health analysis"""
    return render_template('soil_health.html')

@app.route('/soil-health/analyze', methods=['POST'])
def soil_health_analyze():
    """Analyze soil health based on input parameters"""
    try:
        # Get input values from form
        nitrogen = float(request.form['nitrogen'])
        phosphorus = float(request.form['phosphorus'])
        potassium = float(request.form['potassium'])
        ph = float(request.form['ph'])
        ec = float(request.form['ec'])
        moisture = float(request.form['moisture'])
        organic_matter = float(request.form['organic_matter'])

        # Validate input ranges
        if not (0 <= nitrogen <= 100):
            return render_template('soil_health.html', error="Nitrogen should be between 0 and 100 ppm")
        if not (0 <= phosphorus <= 100):
            return render_template('soil_health.html', error="Phosphorus should be between 0 and 100 ppm")
        if not (0 <= potassium <= 100):
            return render_template('soil_health.html', error="Potassium should be between 0 and 100 ppm")
        if not (4.0 <= ph <= 8.5):
            return render_template('soil_health.html', error="pH should be between 4.0 and 8.5")
        if not (0 <= ec <= 4):
            return render_template('soil_health.html', error="EC should be between 0 and 4 dS/m")
        if not (0 <= moisture <= 100):
            return render_template('soil_health.html', error="Moisture should be between 0 and 100%")
        if not (0 <= organic_matter <= 10):
            return render_template('soil_health.html', error="Organic matter should be between 0 and 10%")

        # Calculate soil health parameters
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
            fertility_class = 'success'
        elif quality_score >= 40:
            fertility_level = 'Medium'
            fertility_class = 'warning'
        else:
            fertility_level = 'Low'
            fertility_class = 'danger'

        # Determine suitable crops
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

        # Generate soil health recommendations
        recommendations = []

        # Nitrogen recommendations
        if nitrogen < 30:
            recommendations.append("Low nitrogen levels. Apply nitrogen-rich fertilizers like urea or ammonium sulfate. Consider planting legumes as cover crops to fix nitrogen.")
        elif nitrogen > 80:
            recommendations.append("High nitrogen levels. Reduce nitrogen fertilizer application. Plant nitrogen-demanding crops like corn or leafy greens.")

        # Phosphorus recommendations
        if phosphorus < 30:
            recommendations.append("Low phosphorus levels. Apply phosphate fertilizers or bone meal. Maintain soil pH between 6.0-7.0 for optimal phosphorus availability.")
        elif phosphorus > 80:
            recommendations.append("High phosphorus levels. Avoid phosphorus fertilizers. Monitor water runoff to prevent phosphorus pollution.")

        # Potassium recommendations
        if potassium < 30:
            recommendations.append("Low potassium levels. Apply potassium-rich fertilizers like potassium chloride or sulfate of potash.")
        elif potassium > 80:
            recommendations.append("High potassium levels. Reduce potassium fertilizer application.")

        # pH recommendations
        if ph < 5.5:
            recommendations.append("Acidic soil. Apply agricultural lime to raise pH. Avoid acid-forming fertilizers.")
        elif ph > 7.5:
            recommendations.append("Alkaline soil. Apply sulfur or acidifying fertilizers to lower pH. Choose acid-tolerant crops.")

        # EC recommendations
        if ec > 2.5:
            recommendations.append("High salt content. Improve drainage and leach salts with irrigation. Add organic matter to buffer salt effects.")

        # Moisture recommendations
        if moisture < 30:
            recommendations.append("Low moisture content. Improve irrigation practices. Add organic matter to improve water retention.")
        elif moisture > 70:
            recommendations.append("High moisture content. Improve drainage. Consider raised beds or drainage tiles.")

        # Organic matter recommendations
        if organic_matter < 2:
            recommendations.append("Low organic matter. Add compost, manure, or plant cover crops. Minimize tillage to preserve soil structure.")

        # Generate soil health card data
        soil_health_data = {
            'nitrogen': nitrogen,
            'phosphorus': phosphorus,
            'potassium': potassium,
            'ph': ph,
            'ec': ec,
            'moisture': moisture,
            'organic_matter': organic_matter,
            'quality_score': round(quality_score, 1),
            'fertility_level': fertility_level,
            'fertility_class': fertility_class,
            'suitable_crops': suitable_crops,
            'recommendations': recommendations
        }

        return render_template('soil_health.html', result=soil_health_data)

    except Exception as e:
        return render_template('soil_health.html', error=f"Error analyzing soil health: {str(e)}")

# ----- Comparison Dashboard Routes -----

# Function to predict yield based on input parameters
def predict_yield(crop_name, soil_type, water_level, fertilizer_level, season):
    """
    Predict crop yield based on input parameters
    """
    import random

    # Sample crop data for comparison
    crops = [
        {
            "id": 1,
            "name": "Rice",
            "cost_per_acre": 25000,
            "yield_per_acre": 2500,
            "price_per_kg": 20,
            "growing_period": 120,
            "water_requirement": "High",
            "labor_requirement": "High",
            "suitable_season": "Kharif",
            "description": "Rice is a staple food crop grown in paddy fields. It requires standing water for most of its growing period."
        },
        {
            "id": 2,
            "name": "Wheat",
            "cost_per_acre": 18000,
            "yield_per_acre": 1800,
            "price_per_kg": 25,
            "growing_period": 140,
            "water_requirement": "Medium",
            "labor_requirement": "Medium",
            "suitable_season": "Rabi",
            "description": "Wheat is a major cereal grain cultivated worldwide. It's a cool-season crop that requires moderate water."
        },
        {
            "id": 3,
            "name": "Maize (Corn)",
            "cost_per_acre": 20000,
            "yield_per_acre": 3000,
            "price_per_kg": 18,
            "growing_period": 100,
            "water_requirement": "Medium",
            "labor_requirement": "Medium",
            "suitable_season": "Kharif, Rabi",
            "description": "Maize is a versatile crop used for both human consumption and animal feed. It adapts to various growing conditions."
        },
        {
            "id": 4,
            "name": "Cotton",
            "cost_per_acre": 35000,
            "yield_per_acre": 1200,
            "price_per_kg": 60,
            "growing_period": 180,
            "water_requirement": "Medium",
            "labor_requirement": "High",
            "suitable_season": "Kharif",
            "description": "Cotton is a major cash crop grown for its fiber. It requires a long, frost-free period and moderate water."
        },
        {
            "id": 5,
            "name": "Sugarcane",
            "cost_per_acre": 40000,
            "yield_per_acre": 40000,
            "price_per_kg": 3,
            "growing_period": 365,
            "water_requirement": "High",
            "labor_requirement": "High",
            "suitable_season": "Year-round",
            "description": "Sugarcane is a perennial grass cultivated for its sweet juice. It requires high water and labor inputs."
        },
        {
            "id": 6,
            "name": "Potato",
            "cost_per_acre": 30000,
            "yield_per_acre": 15000,
            "price_per_kg": 10,
            "growing_period": 90,
            "water_requirement": "Medium",
            "labor_requirement": "Medium",
            "suitable_season": "Rabi",
            "description": "Potato is a root vegetable and a cool-season crop. It's highly productive and versatile in cooking."
        },
        {
            "id": 7,
            "name": "Tomato",
            "cost_per_acre": 45000,
            "yield_per_acre": 20000,
            "price_per_kg": 15,
            "growing_period": 90,
            "water_requirement": "Medium",
            "labor_requirement": "High",
            "suitable_season": "Year-round",
            "description": "Tomato is a high-value vegetable crop. It requires good management but can provide excellent returns."
        },
        {
            "id": 8,
            "name": "Soybean",
            "cost_per_acre": 15000,
            "yield_per_acre": 1500,
            "price_per_kg": 40,
            "growing_period": 100,
            "water_requirement": "Low",
            "labor_requirement": "Low",
            "suitable_season": "Kharif",
            "description": "Soybean is a legume crop that fixes nitrogen in the soil. It's drought-tolerant and requires less labor."
        }
    ]

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

@app.route('/comparison_dashboard')
def comparison_dashboard():
    """Route for crop comparison dashboard"""
    # Pass translation function to the template
    # Sample crop data for comparison
    crops = [
        {
            "id": 1,
            "name": "Rice",
            "cost_per_acre": 25000,
            "yield_per_acre": 2500,
            "price_per_kg": 20,
            "growing_period": 120,
            "water_requirement": "High",
            "labor_requirement": "High",
            "suitable_season": "Kharif",
            "description": "Rice is a staple food crop grown in paddy fields. It requires standing water for most of its growing period."
        },
        {
            "id": 2,
            "name": "Wheat",
            "cost_per_acre": 18000,
            "yield_per_acre": 1800,
            "price_per_kg": 25,
            "growing_period": 140,
            "water_requirement": "Medium",
            "labor_requirement": "Medium",
            "suitable_season": "Rabi",
            "description": "Wheat is a major cereal grain cultivated worldwide. It's a cool-season crop that requires moderate water."
        },
        {
            "id": 3,
            "name": "Maize (Corn)",
            "cost_per_acre": 20000,
            "yield_per_acre": 3000,
            "price_per_kg": 18,
            "growing_period": 100,
            "water_requirement": "Medium",
            "labor_requirement": "Medium",
            "suitable_season": "Kharif, Rabi",
            "description": "Maize is a versatile crop used for both human consumption and animal feed. It adapts to various growing conditions."
        },
        {
            "id": 4,
            "name": "Cotton",
            "cost_per_acre": 35000,
            "yield_per_acre": 1200,
            "price_per_kg": 60,
            "growing_period": 180,
            "water_requirement": "Medium",
            "labor_requirement": "High",
            "suitable_season": "Kharif",
            "description": "Cotton is a major cash crop grown for its fiber. It requires a long, frost-free period and moderate water."
        },
        {
            "id": 5,
            "name": "Sugarcane",
            "cost_per_acre": 40000,
            "yield_per_acre": 40000,
            "price_per_kg": 3,
            "growing_period": 365,
            "water_requirement": "High",
            "labor_requirement": "High",
            "suitable_season": "Year-round",
            "description": "Sugarcane is a perennial grass cultivated for its sweet juice. It requires high water and labor inputs."
        },
        {
            "id": 6,
            "name": "Potato",
            "cost_per_acre": 30000,
            "yield_per_acre": 15000,
            "price_per_kg": 10,
            "growing_period": 90,
            "water_requirement": "Medium",
            "labor_requirement": "Medium",
            "suitable_season": "Rabi",
            "description": "Potato is a root vegetable and a cool-season crop. It's highly productive and versatile in cooking."
        },
        {
            "id": 7,
            "name": "Tomato",
            "cost_per_acre": 45000,
            "yield_per_acre": 20000,
            "price_per_kg": 15,
            "growing_period": 90,
            "water_requirement": "Medium",
            "labor_requirement": "High",
            "suitable_season": "Year-round",
            "description": "Tomato is a high-value vegetable crop. It requires good management but can provide excellent returns."
        },
        {
            "id": 8,
            "name": "Soybean",
            "cost_per_acre": 15000,
            "yield_per_acre": 1500,
            "price_per_kg": 40,
            "growing_period": 100,
            "water_requirement": "Low",
            "labor_requirement": "Low",
            "suitable_season": "Kharif",
            "description": "Soybean is a legume crop that fixes nitrogen in the soil. It's drought-tolerant and requires less labor."
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

    # Get prediction result if available
    prediction_result = None
    if request.args.get('predict') == 'true':
        crop_name = request.args.get('crop_name')
        soil_type = request.args.get('soil_type')
        water_level = request.args.get('water_level')
        fertilizer_level = request.args.get('fertilizer_level')
        season = request.args.get('season')

        if crop_name and soil_type and water_level and fertilizer_level and season:
            # Get base crop data
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
                    "roi": predicted_roi,
                    "base_yield": base_crop["yield_per_acre"],
                    "price_per_kg": price_per_kg,
                    "cost_per_acre": cost_per_acre
                }

    return render_template('comparison_dashboard.html', crops=crops, prediction_result=prediction_result)

@app.route('/comparison_dashboard/predict', methods=['POST'])
def predict_crop_yield():
    """API endpoint for crop yield prediction"""
    try:
        # Get form data
        crop_name = request.form.get('crop_name')
        soil_type = request.form.get('soil_type')
        water_level = request.form.get('water_level')
        fertilizer_level = request.form.get('fertilizer_level')
        season = request.form.get('season')

        # Redirect to comparison dashboard with prediction parameters
        return redirect(url_for('comparison_dashboard',
                               predict='true',
                               crop_name=crop_name,
                               soil_type=soil_type,
                               water_level=water_level,
                               fertilizer_level=fertilizer_level,
                               season=season))
    except Exception as e:
        # Handle errors
        return render_template('comparison_dashboard.html', error=str(e))

@app.route('/weather-aware/forecast', methods=['POST'])
def weather_forecast():
    """Get weather forecast and farming recommendations based on location"""
    try:
        location = request.form['location']
        crop_type = request.form['crop_type']

        # Here you would typically call your weather API and get forecast data
        # For demonstration, we'll use mock data
        weather_data = {
            'location': location,
            'forecast': [
                {
                    'date': (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'),
                    'condition': random.choice(['Sunny', 'Partly Cloudy', 'Cloudy', 'Light Rain', 'Heavy Rain']),
                    'temperature': round(random.uniform(20, 35), 1),
                    'humidity': round(random.uniform(40, 90), 1),
                    'wind_speed': round(random.uniform(5, 25), 1),
                    'precipitation': round(random.uniform(0, 30), 1)
                } for i in range(7)
            ]
        }

        # Generate farming recommendations based on weather forecast
        recommendations = generate_weather_recommendations(weather_data, crop_type)

        return render_template('weather_forecast.html',
                              weather_data=weather_data,
                              recommendations=recommendations,
                              crop_type=crop_type)
    except Exception as e:
        return render_template('weather_aware.html', error=f"Error getting weather forecast: {str(e)}")

def generate_weather_recommendations(weather_data, crop_type):
    """Generate farming recommendations based on weather forecast and crop type"""
    recommendations = []

    # Check for heavy rain in the forecast
    heavy_rain_days = [day for day in weather_data['forecast'] if day['condition'] == 'Heavy Rain']
    if heavy_rain_days:
        recommendations.append({
            'type': 'warning',
            'title': 'Heavy Rain Alert',
            'description': f"Heavy rain expected on {', '.join([day['date'] for day in heavy_rain_days])}. Consider these actions:",
            'actions': [
                'Ensure proper drainage in your fields',
                'Delay fertilizer application to prevent runoff',
                'Check crop supports to prevent damage',
                'Consider protective covering for sensitive crops'
            ]
        })

    # Check for dry conditions
    dry_days = [day for day in weather_data['forecast'] if day['condition'] in ['Sunny', 'Partly Cloudy'] and day['humidity'] < 50]
    if len(dry_days) >= 3:
        recommendations.append({
            'type': 'info',
            'title': 'Dry Spell Expected',
            'description': 'Extended dry conditions forecasted. Optimize your irrigation:',
            'actions': [
                'Increase irrigation frequency',
                'Water during early morning or evening to reduce evaporation',
                'Consider mulching to retain soil moisture',
                'Monitor plants for signs of water stress'
            ]
        })

    # Crop-specific recommendations
    if crop_type == 'Rice':
        if any(day['temperature'] > 32 for day in weather_data['forecast']):
            recommendations.append({
                'type': 'warning',
                'title': 'High Temperature Alert for Rice',
                'description': 'Temperatures above optimal range for rice detected:',
                'actions': [
                    'Maintain adequate water levels to cool the crop',
                    'Consider additional irrigation during hottest parts of the day',
                    'Monitor for heat stress symptoms',
                    'Ensure proper nutrient management to strengthen plants'
                ]
            })
    elif crop_type == 'Wheat':
        if any(day['temperature'] < 15 for day in weather_data['forecast']):
            recommendations.append({
                'type': 'info',
                'title': 'Cool Weather Advisory for Wheat',
                'description': 'Temperatures below optimal range for wheat development:',
                'actions': [
                    'Monitor for frost damage if temperatures drop further',
                    'Delay irrigation during coldest days',
                    'Consider foliar nutrient application to support growth',
                    'Watch for signs of slowed development'
                ]
            })
    elif crop_type == 'Cotton':
        high_humidity_days = [day for day in weather_data['forecast'] if day['humidity'] > 80]
        if high_humidity_days:
            recommendations.append({
                'type': 'warning',
                'title': 'Disease Risk Alert for Cotton',
                'description': 'High humidity increases risk of fungal diseases:',
                'actions': [
                    'Monitor for early signs of boll rot or leaf spot',
                    'Consider preventative fungicide application',
                    'Ensure adequate spacing for air circulation',
                    'Avoid overhead irrigation during this period'
                ]
            })

    # Add general farming schedule recommendation
    recommendations.append({
        'type': 'success',
        'title': 'Optimal Farming Schedule',
        'description': 'Based on the 7-day forecast, here\'s your optimal farming schedule:',
        'actions': [
            f"Best days for planting: {', '.join([day['date'] for day in weather_data['forecast'] if 'Rain' not in day['condition']][:2])}",
            f"Best days for fertilizer application: {', '.join([day['date'] for day in weather_data['forecast'] if day['precipitation'] < 5 and day['wind_speed'] < 15][:2])}",
            f"Best days for pesticide application: {', '.join([day['date'] for day in weather_data['forecast'] if day['precipitation'] < 2 and day['wind_speed'] < 10][:2])}",
            f"Best days for harvesting: {', '.join([day['date'] for day in weather_data['forecast'] if day['condition'] == 'Sunny' and day['humidity'] < 70][:2])}"
        ]
    })

    return recommendations

# Initialize the app
def initialize_database():
    with app.app_context():
        # Create database tables
        db.create_all()
        print("Database tables created")

        # Create initial data
        create_initial_data()
        print("Initial data created")

        # Verify database content
        farm_count = Farm.query.count()
        soil_record_count = SoilRecord.query.count()
        harvest_count = Harvest.query.count()
        print(f"Database contains: {farm_count} farms, {soil_record_count} soil records, {harvest_count} harvests")

# Initialize database when the app starts
initialize_database()

if __name__ == '__main__':
    print("Starting integrated agriculture application...")
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
