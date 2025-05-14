# Agriculture Hub

An all-in-one web application for agriculture that combines crop recommendation, fertilizer recommendation, plant disease detection, an agriculture chatbot, and a soil quality dashboard.

## Features

- **Crop Recommendation**: Get personalized crop recommendations based on soil composition and climate conditions
- **Fertilizer Recommendation**: Find the optimal fertilizer for your crops based on soil nutrient levels and crop type
- **Plant Disease Detection**: Identify plant diseases from images and get treatment recommendations
- **Agriculture Chatbot**: Get instant answers to farming questions from an AI-powered agriculture expert
- **Soil Quality Dashboard**: Track and monitor soil health over time with detailed analytics and visualizations

## Setup and Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Ensure the model files are in the `models` directory:
   - `crop_recommender_rf.joblib` (Crop recommendation model)
   - `xgb_pipeline.pkl` (Fertilizer recommendation model)
   - `plant_disease_optimized.onnx` (Plant disease detection model)
6. Create a `.env` file with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
7. Run the application:
   ```
   python app.py
   ```
8. Open your browser and navigate to `http://localhost:5000`

## Project Structure

- `app.py`: Main Flask application
- `models/`: Directory containing ML models
- `static/`: Static files (CSS, JS, images)
- `templates/`: HTML templates
- `requirements.txt`: Required Python packages
- `.env`: Environment variables (API keys)

## Technologies Used

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Machine Learning**: scikit-learn, XGBoost, ONNX Runtime
- **AI**: Google Gemini API
- **Data Visualization**: Matplotlib
- **Database**: SQLite

## API Endpoints

- `/api/crop-recommendation/predict`: Crop recommendation API
- `/api/fertilizer-recommendation/predict`: Fertilizer recommendation API
- `/api/plant-disease/predict`: Plant disease detection API
- `/api/chatbot/ask`: Chatbot API

## License

MIT

## Acknowledgements

This project combines and integrates several individual projects:
- Crop Recommendation System
- Fertilizer Recommendation System
- Plant Disease Detection
- Agriculture Chatbot
- Soil Quality Dashboard
