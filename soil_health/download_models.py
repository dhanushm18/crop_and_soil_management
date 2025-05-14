import os
import shutil
import zipfile

def create_models_zip():
    """Create a zip file containing the trained models."""
    # Check if models exist
    model_files = [
        'models/fertility_model.pkl',
        'models/quality_model.pkl',
        'models/scaler.pkl',
        'models/label_encoder.pkl'
    ]
    
    missing_files = [f for f in model_files if not os.path.exists(f)]
    if missing_files:
        print(f"Error: The following model files are missing: {missing_files}")
        print("Please run train_models.py first to generate the models.")
        return False
    
    # Create a zip file
    with zipfile.ZipFile('soil_health_models.zip', 'w') as zipf:
        for file in model_files:
            zipf.write(file)
    
    print(f"Models have been zipped to soil_health_models.zip")
    print("You can download this file and extract it to use the trained models.")
    return True

if __name__ == "__main__":
    create_models_zip()
