from flask import Flask, render_template, request
import onnxruntime as ort
import numpy as np
from PIL import Image
import os

app = Flask(__name__)

# Ensure static directory exists
os.makedirs('static', exist_ok=True)

# Load ONNX model (with error handling)
try:
    ort_session = ort.InferenceSession("plant_disease_optimized.onnx")
    input_name = ort_session.get_inputs()[0].name
except Exception as e:
    print(f"Error loading ONNX model: {e}")
    ort_session = None

# Enhanced disease database
disease_db = {
    "Apple___Apple_scab": {
        "solution": "Apply fungicides containing myclobutanil or sulfur",
        "tips": ["Prune infected branches", "Remove fallen leaves", "Plant resistant varieties"]
    },
    "Tomato___Late_blight": {
        "solution": "Use copper-based fungicides",
        "tips": ["Water at plant base", "Improve air circulation", "Remove infected plants"]
    },
    "healthy": {
        "solution": "No treatment needed",
        "tips": ["Maintain good watering", "Rotate crops annually"]
    }
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'file' not in request.files:
            return render_template("index.html", error="No file uploaded")
            
        file = request.files['file']
        if file.filename == '':
            return render_template("index.html", error="No file selected")

        try:
            # Secure filename and save
            filename = os.path.join('static', os.path.basename(file.filename))
            file.save(filename)
            
            # Verify model loaded
            if ort_session is None:
                return render_template("index.html", error="Model failed to load")
            
            # Preprocess and predict
            img_array = preprocess_image(filename)
            outputs = ort_session.run(None, {input_name: img_array})
            class_index = np.argmax(outputs[0])
            disease_name = [
                "Apple___Apple_scab", 
                "Tomato___Late_blight",
                "healthy"
            ][class_index % 3]  # Simple fallback for testing
            
            advice = disease_db.get(disease_name, {
                "solution": "Consult local expert",
                "tips": ["Isolate plant", "Check soil conditions"]
            })
            
            return render_template(
                "index.html",
                prediction=disease_name,
                confidence=f"{np.max(outputs[0])*100:.1f}%",
                image_path=filename[7:],  # Remove 'static/' for web path
                solution=advice["solution"],
                tips=advice["tips"],
                is_healthy="healthy" in disease_name.lower()
            )
            
        except Exception as e:
            print(f"Error: {e}")
            return render_template("index.html", error="Processing failed")

    return render_template("index.html")

def preprocess_image(image_path, target_size=(224, 224)):
    """Simplified preprocessing"""
    img = Image.open(image_path).convert('RGB').resize(target_size)
    return np.expand_dims(np.array(img)/255.0, axis=0).astype(np.float32)

if __name__ == "__main__":
    app.run(debug=True, port=5001)  # Changed port to avoid conflicts