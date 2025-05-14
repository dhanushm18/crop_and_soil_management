# Soil Health Assessment Tool

A machine learning-based web application for assessing soil health, determining fertility levels, and recommending suitable crops based on soil parameters.

## Features

- **Soil Fertility Level Classification**: Categorizes soil as High, Medium, or Low fertility
- **Soil Quality Score Prediction**: Provides a numerical score (0-100) indicating overall soil health
- **Crop Suitability Recommendation**: Suggests crops that would grow well in the given soil conditions
- **User-Friendly Interface**: Easy-to-use web interface for inputting soil parameters
- **Sample Soil Profiles**: Pre-defined soil profiles for quick testing

## Technologies Used

- **Backend**: Python, Flask
- **Machine Learning**: Scikit-learn, Pandas, NumPy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Data Visualization**: Matplotlib, Seaborn (for model development)

## Installation and Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/soil-health-assessment.git
   cd soil-health-assessment
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Generate the dataset and train the models (optional):
   ```
   python data/soil_data.py
   jupyter notebook notebooks/soil_health_model.ipynb
   ```

5. Run the application:
   ```
   python app.py
   ```

6. Open your web browser and navigate to `http://127.0.0.1:5000/`

## Input Parameters

The tool requires the following soil parameters:

- **Nitrogen (N)**: 0-100 ppm
- **Phosphorus (P)**: 0-100 ppm
- **Potassium (K)**: 0-100 ppm
- **pH**: 4.0-8.5
- **Electrical Conductivity (EC)**: 0-4 dS/m
- **Moisture Content**: 0-100%
- **Organic Matter**: 0-10%

## Project Structure

```
soil-health-assessment/
├── app.py                  # Flask application
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── data/
│   ├── soil_data.py        # Data generation script
│   └── soil_dataset.csv    # Generated dataset
├── models/
│   ├── soil_health_model.py # Model implementation
│   ├── fertility_model.pkl  # Trained fertility model
│   ├── quality_model.pkl    # Trained quality score model
│   ├── scaler.pkl           # Feature scaler
│   └── label_encoder.pkl    # Label encoder
├── notebooks/
│   └── soil_health_model.ipynb # Model development notebook
├── static/
│   ├── css/
│   │   └── style.css       # Custom styles
│   └── js/
│       └── script.js       # Frontend JavaScript
└── templates/
    ├── index.html          # Main page
    └── about.html          # About page
```

## How It Works

1. **Data Collection**: The user inputs soil parameters through the web interface.
2. **Data Processing**: The input data is processed and scaled.
3. **Prediction**: The machine learning models predict the soil fertility level and quality score.
4. **Crop Recommendation**: Based on the soil parameters, suitable crops are recommended.
5. **Results Display**: The results are displayed in an easy-to-understand format.

## Future Improvements

- Integration with soil sensors for automatic data collection
- More detailed crop recommendations with planting guidelines
- Soil improvement recommendations based on the assessment
- Historical data tracking for monitoring soil health over time
- Mobile application for field use

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This project was created as a demonstration of machine learning applications in agriculture.
- The soil parameter thresholds and crop suitability rules are based on general agricultural guidelines.
