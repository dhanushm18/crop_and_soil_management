import joblib
import numpy as np

# Load the model
model = joblib.load('crop_recommender_rf.joblib')

# Print model information
print("Model type:", type(model))
print("Model parameters:", model.get_params())

# Check if the model has feature names
if hasattr(model, 'feature_names_in_'):
    print("Feature names:", model.feature_names_in_)

# Check if the model has classes (for classification)
if hasattr(model, 'classes_'):
    print("Classes (crops):", model.classes_)

# Test prediction with sample data
# N, P, K, temperature, humidity, ph, rainfall
sample_data = np.array([[83, 45, 60, 28, 70, 7.0, 150]])
prediction = model.predict(sample_data)
print("Prediction for sample data:", prediction)

# Get feature importances if available
if hasattr(model, 'feature_importances_'):
    print("Feature importances:", model.feature_importances_)
