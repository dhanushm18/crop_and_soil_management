from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64
import numpy as np

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agriculture.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Create database models

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
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    soil_data = db.relationship('SoilData', backref='record', lazy=True, cascade="all, delete-orphan")
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<SoilRecord {self.date}>'

class SoilData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    soil_record_id = db.Column(db.Integer, db.ForeignKey('soil_record.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('soil_component.id'), nullable=False)
    value = db.Column(db.Float, nullable=False)
    component = db.relationship('SoilComponent')

    def __repr__(self):
        return f'<SoilData {self.component.name}: {self.value}>'

class Crop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    depletion_rates = db.relationship('DepletionRate', backref='crop', lazy=True)

    def __repr__(self):
        return f'<Crop {self.name}>'

class DepletionRate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    crop_id = db.Column(db.Integer, db.ForeignKey('crop.id'), nullable=False)
    component_id = db.Column(db.Integer, db.ForeignKey('soil_component.id'), nullable=False)
    rate = db.Column(db.Float, nullable=False)  # Amount depleted per harvest
    component = db.relationship('SoilComponent')

    def __repr__(self):
        return f'<DepletionRate {self.crop.name} - {self.component.name}: {self.rate}>'

class Harvest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    farm_id = db.Column(db.Integer, db.ForeignKey('farm.id'), nullable=False)
    crop_id = db.Column(db.Integer, db.ForeignKey('crop.id'), nullable=False)
    crop = db.relationship('Crop')
    yield_amount = db.Column(db.Float)  # in kg or other units
    notes = db.Column(db.Text)

    def __repr__(self):
        return f'<Harvest {self.crop.name} on {self.date}>'

# Create initial data
def create_initial_data():
    # Create common soil components if not exists
    components = [
        {'name': 'Nitrogen (N)', 'unit': 'ppm', 'description': 'Essential for leaf growth'},
        {'name': 'Phosphorus (P)', 'unit': 'ppm', 'description': 'Important for root development'},
        {'name': 'Potassium (K)', 'unit': 'ppm', 'description': 'Helps overall plant health'},
        {'name': 'Calcium (Ca)', 'unit': 'ppm', 'description': 'Strengthens cell walls'},
        {'name': 'Magnesium (Mg)', 'unit': 'ppm', 'description': 'Essential for photosynthesis'},
        {'name': 'Sulfur (S)', 'unit': 'ppm', 'description': 'Helps protein formation'},
        {'name': 'Organic Matter', 'unit': '%', 'description': 'Improves soil structure and fertility'},
        {'name': 'pH', 'unit': 'pH', 'description': 'Affects nutrient availability'}
    ]

    for comp in components:
        if not SoilComponent.query.filter_by(name=comp['name']).first():
            component = SoilComponent(name=comp['name'], unit=comp['unit'], description=comp['description'])
            db.session.add(component)

    # Create common crops if not exists
    crops = ['Corn', 'Wheat', 'Soybeans', 'Rice', 'Cotton', 'Potatoes', 'Tomatoes']
    for crop_name in crops:
        if not Crop.query.filter_by(name=crop_name).first():
            crop = Crop(name=crop_name)
            db.session.add(crop)

    db.session.commit()

    # Add depletion rates for crops
    if not DepletionRate.query.first():
        # Get all crops and components
        all_crops = Crop.query.all()
        components = SoilComponent.query.all()

        # Sample depletion rates (these would be based on research in a real app)
        for crop in all_crops:
            for component in components:
                if component.name != 'pH':  # pH doesn't deplete in the same way
                    # Different crops deplete soil components at different rates
                    if crop.name == 'Corn':
                        rate = 15.0 if component.name == 'Nitrogen (N)' else 5.0
                    elif crop.name == 'Wheat':
                        rate = 10.0 if component.name == 'Phosphorus (P)' else 4.0
                    elif crop.name == 'Soybeans':
                        rate = 8.0 if component.name == 'Potassium (K)' else 3.0
                    else:
                        rate = 5.0  # Default depletion rate

                    depletion = DepletionRate(crop_id=crop.id, component_id=component.id, rate=rate)
                    db.session.add(depletion)

        db.session.commit()

    # Create a default farm if none exists
    if not Farm.query.first():
        farm = Farm(name="Demo Farm", location="Sample Location", size=100.0)
        db.session.add(farm)
        db.session.commit()

# Routes
@app.route('/')
def index():
    # Get the first farm (or create one if none exists)
    farm = Farm.query.first()
    if not farm:
        farm = Farm(name="Demo Farm", location="Sample Location", size=100.0)
        db.session.add(farm)
        db.session.commit()

    return redirect(url_for('dashboard', farm_id=farm.id))

@app.route('/dashboard/<int:farm_id>')
def dashboard(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    soil_records = SoilRecord.query.filter_by(farm_id=farm_id).order_by(SoilRecord.date.asc()).all()
    harvests = Harvest.query.filter_by(farm_id=farm_id).order_by(Harvest.date.desc()).all()

    # Generate line charts for soil components over time
    components_chart = generate_components_line_chart(soil_records)

    return render_template('dashboard.html', farm=farm, soil_records=soil_records,
                           harvests=harvests, components_chart=components_chart)

@app.route('/farms/new', methods=['GET', 'POST'])
def new_farm():
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get('location')
        size = request.form.get('size')

        farm = Farm(name=name, location=location, size=size)
        db.session.add(farm)
        db.session.commit()

        flash('Farm added successfully!')
        return redirect(url_for('dashboard', farm_id=farm.id))

    return render_template('farm_form.html')

@app.route('/farms/<int:farm_id>')
def farm_detail(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    soil_records = SoilRecord.query.filter_by(farm_id=farm_id).order_by(SoilRecord.date.desc()).all()
    harvests = Harvest.query.filter_by(farm_id=farm_id).order_by(Harvest.date.desc()).all()

    return render_template('farm_detail.html', farm=farm, soil_records=soil_records, harvests=harvests)

@app.route('/farms/<int:farm_id>/soil/new', methods=['GET', 'POST'])
def new_soil_record(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    components = SoilComponent.query.all()

    if request.method == 'POST':
        notes = request.form.get('notes')

        soil_record = SoilRecord(farm_id=farm_id, notes=notes)
        db.session.add(soil_record)
        db.session.flush()  # Get the ID without committing

        # Add soil data for each component
        for component in components:
            value = request.form.get(f'component_{component.id}')
            if value:
                soil_data = SoilData(
                    soil_record_id=soil_record.id,
                    component_id=component.id,
                    value=float(value)
                )
                db.session.add(soil_data)

        db.session.commit()
        flash('Soil record added successfully!')
        return redirect(url_for('dashboard', farm_id=farm_id))

    return render_template('soil_form.html', farm=farm, components=components)

@app.route('/farms/<int:farm_id>/harvest/new', methods=['GET', 'POST'])
def new_harvest(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    crops = Crop.query.all()

    if request.method == 'POST':
        crop_id = request.form.get('crop_id')
        yield_amount = request.form.get('yield_amount')
        notes = request.form.get('notes')

        harvest = Harvest(
            farm_id=farm_id,
            crop_id=crop_id,
            yield_amount=float(yield_amount) if yield_amount else None,
            notes=notes
        )
        db.session.add(harvest)

        # Get the latest soil record for this farm
        latest_soil_record = SoilRecord.query.filter_by(farm_id=farm_id).order_by(SoilRecord.date.desc()).first()

        if latest_soil_record:
            # Create a new soil record with depleted values
            new_record = SoilRecord(farm_id=farm_id, notes=f"Auto-generated after {Crop.query.get(crop_id).name} harvest")
            db.session.add(new_record)
            db.session.flush()  # Get the ID without committing

            # Get depletion rates for the crop
            crop = Crop.query.get(crop_id)
            depletion_rates = {dr.component_id: dr.rate for dr in crop.depletion_rates}

            # Apply depletion to each soil component
            for soil_data in latest_soil_record.soil_data:
                component_id = soil_data.component_id
                original_value = soil_data.value

                # Calculate new value after depletion
                depletion = depletion_rates.get(component_id, 0)
                new_value = max(0, original_value - depletion)  # Ensure value doesn't go below 0

                # Add new soil data with depleted value
                new_soil_data = SoilData(
                    soil_record_id=new_record.id,
                    component_id=component_id,
                    value=new_value
                )
                db.session.add(new_soil_data)

        db.session.commit()
        flash('Harvest recorded successfully! Soil components have been updated.')
        return redirect(url_for('dashboard', farm_id=farm_id))

    return render_template('harvest_form.html', farm=farm, crops=crops)

@app.route('/soil_history/<int:farm_id>')
def soil_history(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    soil_records = SoilRecord.query.filter_by(farm_id=farm_id).order_by(SoilRecord.date.asc()).all()

    # Generate line charts for soil components over time
    components_chart = generate_components_line_chart(soil_records)

    return render_template('soil_history.html', farm=farm, soil_records=soil_records, components_chart=components_chart)

@app.route('/components')
def components():
    soil_components = SoilComponent.query.all()
    return render_template('components.html', components=soil_components)

@app.route('/crops')
def crops():
    all_crops = Crop.query.all()
    return render_template('crops.html', crops=all_crops)

@app.route('/crops/<int:crop_id>')
def crop_detail(crop_id):
    crop = Crop.query.get_or_404(crop_id)
    depletion_rates = DepletionRate.query.filter_by(crop_id=crop_id).all()
    return render_template('crop_detail.html', crop=crop, depletion_rates=depletion_rates)

# Helper function to generate soil component bar chart
def generate_soil_chart(soil_record):
    plt.figure(figsize=(10, 6))

    components = []
    values = []

    for data in soil_record.soil_data:
        components.append(data.component.name)
        values.append(data.value)

    plt.bar(components, values)
    plt.xlabel('Soil Components')
    plt.ylabel('Value')
    plt.title(f'Soil Composition on {soil_record.date.strftime("%Y-%m-%d")}')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # Save plot to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Convert to base64 for embedding in HTML
    img_data = base64.b64encode(buf.getbuffer()).decode('ascii')
    plt.close()

    return img_data

# Helper function to generate line chart for soil components over time
def generate_components_line_chart(soil_records):
    if not soil_records:
        return None

    # Get all unique components from the records
    component_data = {}
    dates = []

    # Collect data for each component over time
    for record in soil_records:
        dates.append(record.date)
        for data in record.soil_data:
            component_name = data.component.name
            if component_name not in component_data:
                component_data[component_name] = {
                    'values': [],
                    'dates': [],
                    'unit': data.component.unit
                }
            component_data[component_name]['values'].append(data.value)
            component_data[component_name]['dates'].append(record.date)

    # Create a single figure for all components
    plt.figure(figsize=(12, 8))

    # Define a colormap for different components
    colors = plt.cm.tab10.colors

    # Plot each component on the same graph with different colors
    for i, (component_name, data) in enumerate(component_data.items()):
        color = colors[i % len(colors)]
        plt.plot(data['dates'], data['values'], 'o-',
                 linewidth=2, markersize=8,
                 label=f'{component_name} ({data["unit"]})',
                 color=color)

    plt.title('Soil Components Over Time', fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Value', fontsize=12)
    plt.grid(True)
    plt.legend(loc='best', fontsize=10)

    # Format x-axis to show dates nicely
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()

    # Save plot to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)

    # Convert to base64 for embedding in HTML
    img_data = base64.b64encode(buf.getbuffer()).decode('ascii')
    plt.close()

    return img_data

# Initialize the app
with app.app_context():
    db.create_all()
    create_initial_data()

if __name__ == '__main__':
    app.run(debug=True)
