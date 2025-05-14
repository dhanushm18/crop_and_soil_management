import pandas as pd
import numpy as np
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score

print("Loading soil dataset...")
# Check if dataset exists, if not generate it
if not os.path.exists('data/soil_dataset.csv'):
    print("Dataset not found. Generating synthetic data...")
    from data.soil_data import save_data
    df = save_data()
else:
    df = pd.read_csv('data/soil_dataset.csv')

print(f"Dataset loaded with {len(df)} samples.")

# Encode the fertility level
le = LabelEncoder()
df['fertility_level_encoded'] = le.fit_transform(df['fertility_level'])
fertility_classes = le.classes_
print(f"Fertility level classes: {fertility_classes}")

# Extract features and targets
features = ['nitrogen', 'phosphorus', 'potassium', 'ph', 'ec', 'moisture', 'organic_matter']
X = df[features]

# Target for fertility level classification
y_fertility = df['fertility_level_encoded']

# Target for quality score regression
y_quality = df['quality_score']

# Split the data into training and testing sets
X_train, X_test, y_fertility_train, y_fertility_test, y_quality_train, y_quality_test = train_test_split(
    X, y_fertility, y_quality, test_size=0.2, random_state=42
)

# Scale the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("Training fertility level classification model...")
# Train a Random Forest classifier for fertility level
rf_fertility = RandomForestClassifier(n_estimators=100, random_state=42)
rf_fertility.fit(X_train_scaled, y_fertility_train)

# Make predictions
y_fertility_pred = rf_fertility.predict(X_test_scaled)

# Evaluate the model
fertility_accuracy = accuracy_score(y_fertility_test, y_fertility_pred)
print(f"Fertility Level Classification Accuracy: {fertility_accuracy:.4f}")

print("\nTraining soil quality score prediction model...")
# Train a Random Forest regressor for quality score
rf_quality = RandomForestRegressor(n_estimators=100, random_state=42)
rf_quality.fit(X_train_scaled, y_quality_train)

# Make predictions
y_quality_pred = rf_quality.predict(X_test_scaled)

# Evaluate the model
quality_mse = mean_squared_error(y_quality_test, y_quality_pred)
quality_rmse = np.sqrt(quality_mse)
quality_r2 = r2_score(y_quality_test, y_quality_pred)

print(f"Quality Score Prediction MSE: {quality_mse:.4f}")
print(f"Quality Score Prediction RMSE: {quality_rmse:.4f}")
print(f"Quality Score Prediction R²: {quality_r2:.4f}")

# Create models directory if it doesn't exist
os.makedirs('models', exist_ok=True)

print("\nSaving models...")
# Save the models
with open('models/fertility_model.pkl', 'wb') as f:
    pickle.dump(rf_fertility, f)

with open('models/quality_model.pkl', 'wb') as f:
    pickle.dump(rf_quality, f)

# Save the scaler
with open('models/scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)

# Save the label encoder
with open('models/label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)

print("Models saved successfully!")

# Test the models with sample inputs
from models.soil_health_model import SoilHealthModel

print("\nTesting the saved models...")
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
